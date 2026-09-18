"""Strided actuals, actual dummy inquiries, rank refinement and complete runtime observation."""
import copy
from dataclasses import asdict
import hashlib
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_validation import validate_case_trace
from suite_data import Registry, render_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_contiguous_dummy_effect_fixtures as generated
import generate_contiguous_eligibility_fixtures as eligibility

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class ContiguousDummyEffectFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name:case for case in cls.all_cases if case.name in cls.specs}
        cls.members = {row["id"]:row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_two_full_effect_cases_have_only_the_two_selected_primary_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 2)
        self.assertEqual({case.meta.facets[0] for case in self.cases.values()}, set(generated.FACETS))
        for case in self.cases.values():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             ("S8.5.7-001", "valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].language, case.fixture.build[0].form), ("fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expected = case.fixture.expectation
            self.assertEqual((expected.phase, expected.outcome, expected.exit_code), ("run", "success", 0))
            self.assertEqual(expected.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expected.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")

    def test_defined_integer_actuals_nonvector_triplets_and_complete_internal_interfaces(self):
        for spec in self.specs.values():
            main, procedure = spec["source"].split("contains\n", 1)
            self.assertIn("  integer :: a(4)\n", main)
            self.assertIn("  a=[11,12,13,14]\n", main)
            self.assertEqual(main.count("call update_section(a(1:4:2),"), 1)
            self.assertLess(main.index("  a=[11,12,13,14]"), main.index("  if (a(1)"))
            self.assertLess(main.index("  if (a(4)"), main.index("  call update_section"))
            self.assertTrue(procedure.startswith("  subroutine update_section(x, entries, updates, exits, checks"))
            self.assertIn("    implicit none\n", procedure)
            self.assertIn("  end subroutine update_section\n", procedure)
            self.assertTrue(spec["source"].endswith(f"end program contiguous_{spec['variant']}_effect\n"))
            self.assertNotRegex(procedure, r"\ba\s*\(")
            self.assertNotIn("a([", spec["source"])
            for counter in ("entries", "updates", "exits", "checks", "main_checks"):
                self.assertLess(main.index(f"  {counter}=0\n"), main.index("  call update_section"))

    def test_dummy_inquiries_are_direct_and_their_literal_expectations_are_independent(self):
        for spec in self.specs.values():
            by_id = {guard["id"]:guard for guard in spec["guards"]}
            self.assertEqual((by_id["dummy-contiguity"]["expression"], by_id["dummy-contiguity"]["expected"]),
                             ("is_contiguous(x)", ".true."))
            self.assertEqual((by_id["dummy-rank"]["expression"], by_id["dummy-rank"]["expected"]), ("rank(x)", "1"))
            self.assertEqual((by_id["dummy-size"]["expression"], by_id["dummy-size"]["expected"]), ("size(x)", "2"))
            self.assertEqual(spec["source"].count("is_contiguous("), 1)
            self.assertEqual(spec["source"].count("rank(x)"), 1)
            self.assertNotIn("rank([", spec["source"])
            self.assertNotIn("is_contiguous(a", spec["source"])
            self.assertNotIn("is_contiguous(r", spec["source"])
            self.assertLess(spec["source"].index("size(x)"), spec["source"].index("CDE:dummy-initial-1"))

    def test_assumed_shape_payload_is_the_actual_dummy_with_no_observer_temporary(self):
        source = self.specs[generated.identifier("assumed_shape")]["source"]
        self.assertIn("    integer, contiguous, intent(inout) :: x(:)\n", source)
        self.assertNotIn("select rank", source)
        self.assertNotIn("branches", source)
        self.assertIn("    x(1)=x(1)+10\n    updates=updates+1\n", source)
        self.assertIn("    x(2)=x(2)+10\n    updates=updates+1\n", source)
        self.assertEqual(len(re.findall(r"(?m)^\s*integer[^\n]*::[^\n]*\(", source)), 2)

    def test_assumed_rank_payload_is_confined_to_rank_one_association_and_default_fails(self):
        source = self.specs[generated.identifier("assumed_rank")]["source"]
        self.assertIn("    integer, contiguous, intent(inout) :: x(..)\n", source)
        before, ranked = source.split("    select rank (r => x)\n", 1)
        branch, after = ranked.split("    rank default\n", 1)
        self.assertTrue(branch.startswith("    rank (1)\n      branches=branches+1\n"))
        self.assertTrue(after.startswith("      error stop 'CDE:unexpected-rank'\n    end select\n"))
        self.assertIn("      r(1)=r(1)+10\n", branch)
        self.assertIn("      r(2)=r(2)+10\n", branch)
        self.assertNotRegex(before, r"\br\([12]\)")
        self.assertNotRegex(after, r"\br\([12]\)")
        self.assertNotRegex(source, r"\bx\([12]\)")
        self.assertNotRegex(source, r"integer[^\n]*::[^\n]*\br\(")
        self.assertNotIn("return", after.split("    end select\n")[0].lower())
        self.assertEqual(before.count("is_contiguous(x)"), 1)
        self.assertEqual(before.count("rank(x)"), 1)
        self.assertEqual(before.count("size(x)"), 1)

    def test_selected_and_untouched_values_plus_entry_update_return_and_check_counts_are_consumed(self):
        for spec in self.specs.values():
            guards = {guard["id"]:guard for guard in spec["guards"]}
            for i, value in enumerate((11,12,13,14), 1):
                self.assertEqual(guards[f"caller-initial-{i}"]["expected"], str(value))
            for i, value in enumerate((21,12,23,14), 1):
                self.assertEqual((guards[f"caller-returned-{i}"]["expression"],
                                  guards[f"caller-returned-{i}"]["expected"]), (f"a({i})", str(value)))
            for i, before, after in ((1,11,21), (2,13,23)):
                self.assertEqual(guards[f"dummy-initial-{i}"]["expected"], str(before))
                self.assertEqual(guards[f"dummy-updated-{i}"]["expected"], str(after))
            for label, expected in (("dummy-entry","1"), ("dummy-update-total","2"), ("dummy-completed","1")):
                self.assertEqual(guards[label]["expected"], expected)
            source = spec["source"]
            self.assertEqual(source.count("entries=entries+1"), 1)
            self.assertEqual(source.count("updates=updates+1"), 2)
            self.assertEqual(source.count("exits=exits+1"), 1)
            self.assertEqual(sum(row["counter"] == "checks" for row in spec["guards"]), spec["procedure_checks"])
            self.assertEqual(sum(row["counter"] == "main_checks" for row in spec["guards"]), spec["main_checks"])
            self.assertEqual(guards["caller-procedure-checks"]["expected"], str(spec["procedure_checks"]))
            self.assertEqual(guards["caller-check-total"]["expected"], str(spec["main_checks"]))
            self.assertLess(source.index("CDE:dummy-update-total"), source.index("exits=exits+1"))

    def test_no_disallowed_argument_attribute_alias_or_storage_mechanism_claim_in_sources(self):
        for spec in self.specs.values():
            source = spec["source"]
            self.assertNotRegex(source, r"(?i)\b(?:asynchronous|volatile|coarray|pointer|allocatable|target|optional|value|common|equivalence|allocate|bind)\b")
            self.assertNotRegex(source, r"(?im)^\s*integer[^\n]*::[^\n]*=")
            self.assertNotRegex(source, r"integer\s*\(")
            self.assertNotRegex(source, r"(?i)c_loc|c_sizeof|storage_size|loc\(")
            self.assertLessEqual(max(map(len, source.splitlines())), 132)

    def test_every_assertion_and_completion_has_one_source_exact_full_program_probe(self):
        for variant, count in (("assumed_shape",24), ("assumed_rank",26)):
            spec = self.specs[generated.identifier(variant)]
            self.assertEqual(len(spec["guards"]), count)
            self.assertEqual(len({row["id"] for row in spec["guards"]}), count)
            for guard in spec["guards"]:
                raw = spec["source"].encode()
                changed = generated.wrong_oracle_source(spec, guard)
                start, end = guard["span"]
                self.assertEqual(raw[start:end].decode(), guard["expected"])
                self.assertEqual(changed, raw[:start] + guard["replacement"].encode() + raw[end:])
                self.assertEqual(raw.count(b"\n"), changed.count(b"\n"))
                self.assertIn(b"call update_section(a(1:4:2)", changed)
                self.assertIn(b"subroutine update_section", changed)
                self.assertNotEqual(changed, raw)
                if guard["kind"] == "guard":
                    self.assertIn(guard["failure_token"].encode(), changed)
                    self.assertIn(spec["completion"].strip().encode(), changed)
            contiguity = next(row for row in spec["guards"] if row["id"] == "dummy-contiguity")
            self.assertEqual((contiguity["expected"], contiguity["replacement"]), (".true.", ".false."))

    def staged(self, case, family, mode, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic process transport only")
        raw = (case.fixture.root / "source.f90").read_bytes()
        phases = []
        def transport(command, cwd, timeout, stdin=None):
            self.assertEqual(timeout, 5)
            self.assertIsNone(stdin)
            workspace = Path(cwd).resolve()
            self.assertEqual((workspace / "source.f90").read_bytes(), raw)
            phase = "compile" if "-c" in command else "link" if "-o" in command else "run"
            phases.append(phase)
            if phase == "compile":
                self.assertEqual(Path(command[command.index("-c")+1]), workspace / "source.f90")
            if phase == "run":
                self.assertEqual(command[-1], str(workspace / "program"))
            code, stdout, stderr, timed_out = 0, "", "", False
            if fault == phase + "-failure":
                code, stderr = 1, "synthetic failure"
            elif phase == "run":
                stdout = self.specs[case.name]["completion"]
                if fault == "early-success":
                    stdout = ""
                elif fault == "wrong-output":
                    stdout = stdout.replace(" OK", " BAD")
                elif fault == "extra-output":
                    stdout += "extra\n"
                elif fault == "stderr":
                    stderr = "extra\n"
                elif fault == "unexpected-rank":
                    code, stdout, stderr = 1, "", "ERROR STOP CDE:unexpected-rank\n"
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timed_out = True
            if phase != "run" and code == 0:
                Path(command[command.index("-o")+1]).write_bytes(b"synthetic artifact")
            return runner.ProcessResult(code, stdout+stderr, timed_out, stdout, stderr, stdout.encode(), stderr.encode())
        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual(check.input_hashes, {"source.f90":hashlib.sha256(raw).hexdigest()})
        self.assertEqual([row["phase"] for row in check.trace], phases)
        self.assertEqual(check.execution_context["compiler_resources"], {})
        return check, phases

    def test_real_staging_and_ordered_complete_compile_link_run_traces(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                with self.subTest(case=case.name, family=family):
                    check, phases = self.staged(case, family, mode)
                    self.assertEqual((check.outcome,check.phase),("pass","run"))
                    self.assertEqual(phases,["compile","link","run"])

    def test_noop_wrong_values_output_default_rank_and_native_failures_cannot_pass(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                for fault in ("early-success","wrong-output","extra-output","stderr","unexpected-rank",
                              "compile-failure","link-failure","run-failure","crash","timeout"):
                    with self.subTest(case=case.name, family=family, fault=fault):
                        check, phases = self.staged(case, family, mode, fault)
                        self.assertEqual(check.outcome,"fail")
                        if fault in ("compile-failure","link-failure"):
                            self.assertNotIn("run",phases)

    def test_only_selected_S1_metadata_changes_and_all_other_plans_remain(self):
        catalogue = self.registry.catalogues["8.5.7"]
        requirement = self.registry.requirements[generated.RULE]
        self.assertTrue(set(generated.FACETS) <= set(requirement["facets"]))
        self.assertTrue(set(generated.FACETS).isdisjoint(requirement["pending"]))
        self.assertTrue(set(generated.FACETS).isdisjoint(requirement.get("positive_control_facets", [])))
        self.assertEqual(generated.synced_catalogue(catalogue),catalogue)
        self.assertEqual(eligibility.synced_catalogue(catalogue),catalogue)
        for state in ("actual","no-foreign-pending"):
            candidate = copy.deepcopy(catalogue)
            if state == "no-foreign-pending":
                for row in candidate["requirements"]:
                    if row["id"] != generated.RULE:
                        row["pending"] = {}
            preserved = copy.deepcopy(candidate)
            self.assertEqual(generated.synced_catalogue(candidate),preserved)
            self.assertEqual(candidate,preserved)
            rendered = generated.render_view(candidate)
            for row in candidate["requirements"]:
                self.assertIn(render_requirement(row),rendered)
        for path,raw in eligibility.build_corpus()[0].items():
            self.assertEqual(path.read_bytes(),raw)

    def test_every_unselected_S1_pending_subset_and_review_record_are_preserved(self):
        catalogue = self.registry.catalogues["8.5.7"]
        requirement = self.registry.requirements[generated.RULE]
        unselected = sorted(set(requirement["facets"]) - set(generated.FACETS))
        for mask in range(1 << len(unselected)):
            with self.subTest(mask=mask):
                candidate = copy.deepcopy(catalogue)
                selected = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
                for index, facet in enumerate(unselected):
                    if mask & (1 << index):
                        selected["pending"].pop(facet, None)
                selected["positive_control_facets"] = ["contiguous-actual-control"]
                candidate["review_rationale"] = "In-memory lifecycle record; never written as approval."
                candidate["review_fingerprint"] = "1" * 64
                before = copy.deepcopy(candidate)
                updated = generated.synced_catalogue(candidate)
                self.assertEqual(updated, before)
                self.assertEqual(candidate, before)
                text = generated.render_view(updated)
                self.assertIn(f"{len(selected['pending'])} other {generated.RULE} facets remain PENDING.", text)
                self.assertNotIn("The other three S8.5.7-001 facets remain pending", text)
                self.assertNotIn("current assumed-size gate", text)
                for row in updated["requirements"]:
                    self.assertIn(render_requirement(row), text)

    def test_selected_facets_must_exist_before_the_generator_changes_any_state(self):
        catalogue = self.registry.catalogues["8.5.7"]
        for facet in generated.FACETS:
            with self.subTest(facet=facet):
                candidate = copy.deepcopy(catalogue)
                selected = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
                selected["facets"].remove(facet)
                before = copy.deepcopy(candidate)
                with self.assertRaisesRegex(ValueError, "selected S8.5.7-001 facet definitions changed"):
                    generated.synced_catalogue(candidate)
                self.assertEqual(candidate, before)

    def test_shared_renderer_and_adjudication_lifecycles_are_composable_and_independent(self):
        registry = Registry(ROOT)
        original_catalogues = copy.deepcopy(registry.catalogues)
        original_reviews = copy.deepcopy(registry.reviews)
        original_links = copy.deepcopy(registry.evidence.links)
        original_uses = copy.deepcopy(registry.source_uses.data)
        original_inventory = copy.deepcopy(registry.execution.data)
        catalogue = registry.catalogues["8.5.7"]
        self.assertEqual(generated.render_view(catalogue),eligibility.render_view(catalogue))
        self.assertEqual(generated.render_view(catalogue),(ROOT / generated.VIEW).read_text())
        for state in ("draft","reviewed","stale"):
            candidate = copy.deepcopy(catalogue)
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory source lifecycle; no disk approval."
            registry.catalogues["8.5.7"] = candidate
            candidate["review_fingerprint"] = "0"*64 if state == "stale" else registry.catalogue_fingerprint("8.5.7")
            self.assertEqual(registry.catalogue_review_state("8.5.7"),state)
            self.assertEqual(generated.synced_catalogue(candidate),candidate)
            self.assertIn(f"**Source review: {state}.**",generated.render_view(candidate))
        for case in self.cases.values():
            fingerprint = case.fingerprint(registry)
            record = dict(state="source-reviewed",fingerprint=fingerprint,sources=["8.5.7#p1"],
                          rationale="In-memory independent case state, not actual approval.")
            registry._review_record(case.name,record)
            registry.reviews[case.name] = record
            self.assertTrue(registry.review(case.name,fingerprint,[case.name]).approved)
            registry.reviews[case.name] = dict(record,fingerprint="0"*64)
            self.assertEqual(registry.review(case.name,fingerprint,[case.name]).state,"stale")
        cases = runner.collect_cases(ROOT / "tests",registry)
        before = {row["id"]:row for row in registry.execution.report(cases,include_members=False)}
        for name,row in before.items():
            registry.execution.aggregates[name]["review"].update(
                state="source-reviewed",fingerprint=row["review"]["fingerprint"],
                rationale="In-memory whole-inventory binding with actual blockers retained.")
        for row in registry.execution.report(cases,include_members=False):
            self.assertEqual(row["state"],"stale" if before[row["id"]]["blockers"] else "current")
            self.assertEqual(row["blockers"],before[row["id"]]["blockers"])
        fresh = Registry(ROOT)
        self.assertEqual(fresh.catalogues,original_catalogues)
        self.assertEqual(fresh.reviews,original_reviews)
        self.assertEqual(fresh.evidence.links,original_links)
        self.assertEqual(fresh.source_uses.data,original_uses)
        self.assertEqual(fresh.execution.data,original_inventory)
        self.assertEqual(generated.build_corpus()[0],self.files)

    def test_four_fixture_files_are_exact_and_native_definition_rendering_is_current(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("contiguous_dummy_effect_*/*") if path.is_file()}
        self.assertEqual(actual,set(self.files))
        self.assertEqual(len(actual),4)
        for path,raw in self.files.items():
            self.assertEqual(path.read_bytes(),raw)
            raw.decode("ascii")
        registry = Registry(ROOT)
        registry.catalogues = {"8.5.7":registry.catalogues["8.5.7"]}
        registry.render()


if __name__ == "__main__":
    unittest.main()
