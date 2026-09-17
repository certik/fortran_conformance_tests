"""Actual local-array capture, defined-state windows and complete-program oracle regressions."""
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
import generate_explicit_bound_capture_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))
ARRAY_CATEGORIES = {"lower", "upper", "size", "shape", "values"}


class ExplicitBoundCaptureFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if case.name in cls.specs}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_two_effect_programs_cover_only_the_six_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 2)
        self.assertEqual({case.name for case in self.all_cases if case.rule == generated.RULE}, set(self.cases))
        self.assertEqual(set().union(*(set(case.meta.facets) for case in self.cases.values())), set(generated.FACETS))
        for case in self.cases.values():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             ("S8.5.8.2-005", "valid", "effect", "f2023"))
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].language, case.fixture.build[0].form), ("fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expected = case.fixture.expectation
            self.assertEqual((expected.phase, expected.outcome, expected.exit_code), ("run", "success", 0))
            self.assertEqual(expected.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expected.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            self.assertFalse(self.members[case.name]["c_companion_required"])

    def test_procedure_array_is_a_pretyped_nonoptional_INOUT_bound_local(self):
        source = self.specs[generated.identifier("procedure")]["source"]
        main, procedures = source.split("contains\n", 1)
        self.assertNotIn("integer :: a", main)
        self.assertIn("  n=3\n  call capture(n, 1, 3, 6, 101, entries, changes, undefined_events, checks)\n", main)
        self.assertIn("  n=1\n  call capture(n, 2, 1, 4, 102, entries, changes, undefined_events, checks)\n", main)
        self.assertEqual(main.count("call capture("), 2)
        declaration = (
            "    integer, intent(inout) :: n, entries, changes, undefined_events, checks\n"
            "    integer, intent(in) :: visit, upper_expected, extent_expected, value_expected\n"
            "    integer :: a(-2:n)\n"
            "    a=100+visit\n")
        self.assertIn(declaration, procedures)
        self.assertLess(procedures.index("a=100+visit"), procedures.index("lbound(a,1)"))
        self.assertEqual(procedures.count("integer :: a("), 1)
        self.assertNotIn("optional", procedures)
        for counter in ("entries", "changes", "undefined_events", "checks", "returns", "main_checks"):
            self.assertLess(main.index(f"  {counter}=0\n"), main.index("  call capture("))

    def test_controlled_undefinition_does_not_read_or_define_the_bound_source(self):
        source = self.specs[generated.identifier("procedure")]["source"]
        helper = source.split("  subroutine make_undefined(value, event_count)\n", 1)[1].split(
            "  end subroutine make_undefined\n", 1)[0]
        self.assertEqual(helper,
                         "    integer, intent(out) :: value\n"
                         "    integer, intent(inout) :: event_count\n"
                         "    event_count=event_count+1\n")
        window = source.split("    call make_undefined(n, undefined_events)\n", 1)[1].split("    n=upper_expected\n", 1)[0]
        self.assertNotRegex(window, r"\bn\b")
        self.assertIn("lbound(a,1)", window)
        self.assertIn("ubound(a,1)", window)
        self.assertIn("shape(a)", window)
        self.assertIn("size(a)", window)
        self.assertIn("any(a /= value_expected)", window)
        self.assertIn("if (undefined_events /= visit)", window)
        self.assertIn("    n=upper_expected\n    if (n /= upper_expected)", source)
        self.assertLess(source.index("    n=upper_expected"), source.index("  end subroutine capture"))

    def test_three_procedure_snapshots_use_whole_arrays_and_independent_scalar_expectations(self):
        spec = self.specs[generated.identifier("procedure")]
        for phase in ("initial", "redefined", "undefined-source"):
            prefix = "procedure-" + phase + "-"
            guards = {row["category"]: row for row in spec["guards"] if row["id"].startswith(prefix)}
            self.assertEqual(set(guards), ARRAY_CATEGORIES)
            expected = {
                "lower": ("lbound(a,1)", "-2"),
                "upper": ("ubound(a,1)", "upper_expected"),
                "size": ("size(a)", "extent_expected"),
                "shape": ("shape(a)", "extent_expected"),
                "values": ("a", "value_expected"),
            }
            for category, (expression, value) in expected.items():
                self.assertEqual((guards[category]["expression"], guards[category]["expected"]), (expression, value))
                self.assertNotRegex(guards[category]["expected"], r"\bn\b|lbound|ubound|shape|size")
        self.assertIn("    n=0\n    changes=changes+1\n", spec["source"])
        self.assertLess(spec["source"].index("    n=0"), spec["source"].index("EBC:procedure-redefined-lower"))
        self.assertEqual(sum(row["counter"] == "checks" for row in spec["guards"]), 20)
        self.assertEqual(sum(row["counter"] == "main_checks" for row in spec["guards"]), 12)
        self.assertEqual(len([row for row in spec["guards"] if row["kind"] == "guard"]), 33)

    def test_fresh_BLOCK_activations_have_literal_entry_expectations_and_real_local_arrays(self):
        source = self.specs[generated.identifier("blocks")]["source"]
        prefix = source.split("    outer_activation: block\n", 1)[0]
        self.assertNotRegex(prefix, r"integer[^!\n]*::[^\n]*\(")
        self.assertIn("  do visit=1,2\n", prefix)
        self.assertEqual(source.count("    outer_activation: block\n"), 1)
        self.assertEqual(source.count("      inner_activation: block\n"), 1)
        self.assertIn("      integer :: outer(-2:n)\n      outer=200+visit\n", source)
        self.assertIn("        integer :: inner(1:n)\n        inner=300+visit\n", source)
        branch1, branch2 = prefix.split("    if (visit == 1) then\n", 1)[1].split("    else\n")
        expected = [
            ("n", 3, 1), ("outer_upper", 3, 1), ("outer_extent", 6, 4), ("outer_value", 201, 202),
            ("inner_bound", 5, 2), ("inner_upper", 5, 2), ("inner_extent", 5, 2), ("inner_value", 301, 302),
        ]
        for name, first, second in expected:
            self.assertIn(f"      {name}={first}\n", branch1)
            self.assertIn(f"      {name}={second}\n", branch2)
        for counter in ("outer_entries", "inner_entries", "inner_exits", "outer_exits", "events", "checks"):
            self.assertLess(prefix.index(f"  {counter}=0\n"), prefix.index("  do visit=1,2"))
        self.assertLess(source.index("      n=inner_bound"), source.index("      inner_activation: block"))
        self.assertLess(source.index("        inner=300+visit"), source.index("        n=9"))

    def test_nested_array_observers_never_escape_their_lifetimes(self):
        source = self.specs[generated.identifier("blocks")]["source"]
        before_inner, after_inner = source.split("      end block inner_activation\n", 1)
        inside_inner = before_inner.split("      inner_activation: block\n", 1)[1]
        self.assertIn("lbound(inner,1)", inside_inner)
        self.assertIn("lbound(outer,1)", inside_inner)
        self.assertIn("EBC:outer-after-inner-change-values", inside_inner)
        self.assertNotRegex(after_inner, r"(?:lbound|ubound|shape|size|any)\(inner\b")
        self.assertIn("EBC:outer-after-inner-exit-values", after_inner)
        after_outer = after_inner.split("    end block outer_activation\n", 1)[1]
        self.assertNotRegex(after_outer, r"(?:lbound|ubound|shape|size|any)\((?:inner|outer)\b")
        self.assertIn("inner_exits=inner_exits+1", after_inner)
        self.assertIn("outer_exits=outer_exits+1", after_outer)
        spec = self.specs[generated.identifier("blocks")]
        self.assertEqual(sum(row["counter"] == "checks" for row in spec["guards"]), 48)
        self.assertEqual(len([row for row in spec["guards"] if row["kind"] == "guard"]), 55)
        self.assertEqual(sum(row["category"] in ARRAY_CATEGORIES for row in spec["guards"]), 35)
        finals = {row["expression"]: row["expected"] for row in spec["guards"] if row["id"].startswith("block-total-")}
        self.assertEqual(finals, dict(outer_entries="2", inner_entries="2", inner_exits="2", outer_exits="2",
                                     events="12", checks="96"))

    def test_sources_have_no_storage_lifetime_mask_or_unrelated_descriptor_facility(self):
        for spec in self.specs.values():
            source = spec["source"]
            self.assertNotRegex(source, r"(?i)\b(?:save|data|allocate|allocatable|pointer|target|coarray|common|equivalence|module|codimension|bind)\b")
            self.assertNotRegex(source, r"(?im)^\s*integer[^!\n]*::[^\n]*=")
            self.assertNotRegex(source, r"(?i)\b(?:rank|kind|len|reshape|transfer)\s*\(")
            self.assertNotRegex(source, r"integer\s*\(")
            self.assertNotIn("a(:)", source)
            self.assertNotIn("outer(:)", source)
            self.assertNotIn("inner(:)", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)

    def test_every_guard_and_each_dynamic_activation_has_a_complete_one_span_probe(self):
        for variant, expected in (("procedure", 54), ("blocks", 105)):
            spec = self.specs[generated.identifier(variant)]
            self.assertEqual(len(spec["probes"]), expected)
            self.assertEqual(len({row["id"] for row in spec["probes"]}), expected)
            for guard in spec["guards"]:
                probes = [row for row in spec["probes"] if row["span"] == guard["span"]]
                self.assertEqual(len(probes), 2 if guard["repeat"] else 1)
                for probe in probes:
                    raw = spec["source"].encode()
                    start, end = probe["span"]
                    changed = generated.wrong_oracle_source(spec, probe)
                    self.assertEqual(raw[start:end].decode(), probe["expected"])
                    self.assertEqual(changed, raw[:start] + probe["replacement"].encode() + raw[end:])
                    self.assertEqual(changed.count(b"\n"), raw.count(b"\n"))
                    self.assertEqual(changed.count(b"integer :: "), raw.count(b"integer :: "))
                    self.assertNotEqual(changed, raw)
                    if probe["activation"]:
                        visit = probe["repeat"]
                        delta = f"2-{visit}" if probe["activation"] == 1 else f"{visit}-1"
                        self.assertEqual(probe["replacement"], f"({guard['expected']} + ({delta}))")
                        self.assertEqual([2 - entry if probe["activation"] == 1 else entry - 1 for entry in (1, 2)],
                                         [int(entry == probe["activation"]) for entry in (1, 2)])
                        self.assertIn(f"write(*,'(a,i1)') '{probe['activation_output_prefix']}', {visit}", spec["source"])
                    if probe["kind"] == "guard":
                        self.assertIn(probe["failure_token"].encode(), changed)
                        self.assertIn(spec["completion"].strip().encode(), changed)
            self.assertEqual(sum(row["kind"] == "output" for row in spec["probes"]), 1)

    def staged(self, case, family, mode, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic process transport")
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
                self.assertEqual(Path(command[command.index("-c") + 1]), workspace / "source.f90")
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
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timed_out = True
            if phase != "run" and code == 0:
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact")
            return runner.ProcessResult(code, stdout + stderr, timed_out, stdout, stderr,
                                        stdout.encode(), stderr.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertEqual([row["phase"] for row in check.trace], phases)
        self.assertEqual(check.execution_context["compiler_resources"], {})
        return check, phases

    def test_actual_staging_and_ordered_traces_use_each_complete_program(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                with self.subTest(case=case.name, family=family):
                    check, phases = self.staged(case, family, mode)
                    self.assertEqual((check.outcome, check.phase), ("pass", "run"))
                    self.assertEqual(phases, ["compile", "link", "run"])

    def test_no_op_wrong_completion_and_build_crash_timeout_failures_are_not_effects(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                for fault in ("early-success", "wrong-output", "extra-output", "stderr", "run-failure",
                              "compile-failure", "link-failure", "crash", "timeout"):
                    with self.subTest(case=case.name, family=family, fault=fault):
                        check, phases = self.staged(case, family, mode, fault)
                        self.assertEqual(check.outcome, "fail")
                        if fault in ("compile-failure", "link-failure"):
                            self.assertNotIn("run", phases)

    def test_only_S5_metadata_changes_and_vector_capture_stays_pending(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        requirement = self.registry.requirements[generated.RULE]
        self.assertEqual(set(requirement["pending"]), {"vector-bound-capture"})
        self.assertNotIn("positive_control_facets", requirement)
        self.assertEqual(set(requirement["facets"]) - set(requirement["pending"]), set(generated.FACETS))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        for state in ("actual", "no-foreign-pending"):
            candidate = copy.deepcopy(catalogue)
            if state == "no-foreign-pending":
                for row in candidate["requirements"]:
                    if row["id"] != generated.RULE:
                        row["pending"] = {}
            expected = copy.deepcopy(candidate)
            self.assertEqual(generated.synced_catalogue(candidate), expected)
            self.assertEqual(candidate, expected)
            rendered = generated.render_view(candidate)
            for row in candidate["requirements"]:
                self.assertIn(render_requirement(row), rendered)
            other = sum(len(row["pending"]) for row in candidate["requirements"] if row["id"] != generated.RULE)
            self.assertIn(f"and {other} other local facets remain PENDING", rendered)

    def test_rendered_source_review_case_and_inventory_states_remain_independent(self):
        registry = Registry(ROOT)
        original_catalogues = copy.deepcopy(registry.catalogues)
        original_reviews = copy.deepcopy(registry.reviews)
        original_links = copy.deepcopy(registry.evidence.links)
        original_source_uses = copy.deepcopy(registry.source_uses.data)
        original_inventory = copy.deepcopy(registry.execution.data)
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original_catalogues[generated.SECTION])
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory source lifecycle, no disk approval."
            registry.catalogues[generated.SECTION] = candidate
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint(generated.SECTION)
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertIn(f"**Source review: {state}.**", generated.render_view(candidate))
        for case in self.cases.values():
            fingerprint = case.fingerprint(registry)
            record = dict(state="source-reviewed", fingerprint=fingerprint, sources=["8.5.8.2#p5"],
                          rationale="In-memory independent fixture review, never disk approval.")
            registry._review_record(case.name, record)
            registry.reviews[case.name] = record
            self.assertTrue(registry.review(case.name, fingerprint, [case.name]).approved)
            registry.reviews[case.name] = dict(record, fingerprint="0" * 64)
            self.assertEqual(registry.review(case.name, fingerprint, [case.name]).state, "stale")
        cases = runner.collect_cases(ROOT / "tests", registry)
        before = {row["id"]: row for row in registry.execution.report(cases, include_members=False)}
        for name, row in before.items():
            registry.execution.aggregates[name]["review"].update(
                state="source-reviewed", fingerprint=row["review"]["fingerprint"],
                rationale="In-memory whole-universe binding with actual blockers preserved.")
        for row in registry.execution.report(cases, include_members=False):
            self.assertEqual(row["state"], "stale" if before[row["id"]]["blockers"] else "current")
            self.assertEqual(row["blockers"], before[row["id"]]["blockers"])
        fresh = Registry(ROOT)
        self.assertEqual(fresh.catalogues, original_catalogues)
        self.assertEqual(fresh.reviews, original_reviews)
        self.assertEqual(fresh.evidence.links, original_links)
        self.assertEqual(fresh.source_uses.data, original_source_uses)
        self.assertEqual(fresh.execution.data, original_inventory)
        self.assertEqual(generated.build_corpus()[0], self.files)

    def test_exact_four_fixture_files_and_native_definition_rendering(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("explicit_bound_capture_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 4)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        self.assertEqual(generated.render_view(self.registry.catalogues[generated.SECTION]), (ROOT / generated.VIEW).read_text())
        native = Registry(ROOT)
        native.catalogues = {generated.SECTION: native.catalogues[generated.SECTION]}
        native.render()


if __name__ == "__main__":
    unittest.main()
