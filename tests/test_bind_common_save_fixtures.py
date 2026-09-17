"""Complete bound-COMMON lifetimes, exact confirmations, runtime oracles and role boundaries."""
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
import generate_bind_common_save_fixtures as generated
import generate_bind_variable_placement_fixtures as placement

EXPECTED_GUARDS = [
    ("writer-first", "writer_visits", 1), ("reader-first", "reader_visits", 1),
    ("left-first", "left_observed", 11), ("right-first", "right_observed", 13), ("cycle-first", "cycles", 1),
    ("writer-second", "writer_visits", 2), ("reader-second", "reader_visits", 2),
    ("left-second", "left_observed", 17), ("right-second", "right_observed", 19), ("cycle-second", "cycles", 2),
    ("check-total", "checks", 10),
]
FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class BindCommonSaveFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if case.name in cls.specs}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_two_complete_run_cases_keep_effect_and_control_roles(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 2)
        for variant, facet, role in (("retention", "named-common-retention", "effect"),
                                     ("confirmation", "explicit-save-confirmation", "positive-control")):
            case = self.cases[generated.identifier(variant)]
            self.assertEqual((case.rule, case.kind, case.meta.facets, case.meta.evidence),
                             ("S8.5.5-002", "valid", [facet], role))
            self.assertEqual(case.meta.standard, "f2023")
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
            self.assertEqual(expected.stdout, ["BIND COMMON SAVE OK\n"])
            self.assertEqual(expected.stderr, [""])
            self.assertFalse(self.members[case.name]["c_companion_required"])
            self.assertFalse(self.members[case.name]["binding_header_required"])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect" if role == "effect" else "positive-control")

    def test_complete_external_interfaces_match_without_declaring_common_storage(self):
        for spec in self.specs.values():
            source = spec["source"]
            main, procedures = source.split("end program bind_common_retention\n", 1)
            self.assertTrue(main.startswith("program bind_common_retention\n"))
            self.assertNotRegex(main, r"(?im)^\s*(common|bind\s*\(|save\b|module\b)")
            self.assertNotIn("contains", source)
            interface = main.split("  interface\n", 1)[1].split("  end interface\n", 1)[0]
            for procedure, intent in (("store_pair", "in"), ("load_pair", "out")):
                declaration = [
                    f"subroutine {procedure}(left_value, right_value, visits)",
                    "use, intrinsic :: iso_c_binding, only: c_int", "implicit none",
                    f"integer(c_int), intent({intent}) :: left_value, right_value",
                    "integer(c_int), intent(inout) :: visits",
                ]
                body = interface.split(f"    subroutine {procedure}", 1)[1]
                body = f"subroutine {procedure}" + body.split(f"    end subroutine {procedure}", 1)[0]
                self.assertEqual([line.strip() for line in body.splitlines()], declaration)
                actual = procedures.split(f"subroutine {procedure}", 1)[1]
                actual = f"subroutine {procedure}" + actual
                self.assertEqual([line.strip() for line in actual.splitlines()[:5]], declaration)
            self.assertEqual(len(re.findall(r"(?m)^subroutine ", procedures)), 2)
            self.assertEqual(len(re.findall(r"(?m)^end subroutine ", procedures)), 2)

    def test_only_writer_and_reader_declare_two_interoperable_members_and_one_binding(self):
        for spec in self.specs.values():
            procedures = spec["source"].split("end program bind_common_retention\n", 1)[1]
            for name in ("store_pair", "load_pair"):
                body = procedures.split(f"subroutine {name}(", 1)[1].split(f"end subroutine {name}", 1)[0]
                self.assertEqual(body.count("  integer(c_int) :: first, second\n"), 1)
                self.assertEqual(body.count("  common /saved_pair/ first, second\n"), 1)
                self.assertEqual(body.count("  bind(c) :: /saved_pair/\n"), 1)
                self.assertNotRegex(body, r"(?im)^\s*(data\b|equivalence\b|module\b|block\b)")
                self.assertNotRegex(body, r"(?i)pointer|allocatable|parameter|coarray|target|dimension")
                self.assertNotRegex(body, r"::[^\n]*=")
                self.assertNotRegex(body, r"(?im)^\s*save\s+(first|second|visits)\b")
                self.assertNotRegex(body, r"integer\(c_int\),\s*bind")
            self.assertEqual(spec["source"].count("common /saved_pair/"), 2)
            self.assertEqual(spec["source"].count("bind(c) :: /saved_pair/"), 2)
            self.assertNotIn("name=", spec["source"])
            self.assertNotRegex(spec["source"], r"(?i)integer\s*\(\s*\d")

    def test_confirmation_inserts_only_two_block_SAVE_statements_and_nothing_else(self):
        effect = self.specs[generated.identifier("retention")]
        control = self.specs[generated.identifier("confirmation")]
        raw, fixed = effect["source"].encode(), control["source"].encode()
        self.assertNotRegex(effect["source"], r"(?im)^\s*save\b")
        self.assertEqual(control["source"].count("  save /saved_pair/\n"), 2)
        self.assertEqual(fixed.replace(b"  save /saved_pair/\n", b""), raw)
        self.assertEqual(len(fixed) - len(raw), 2 * len(b"  save /saved_pair/\n"))
        reconstructed = raw
        for insertion in reversed(control["confirmation_insertions"]):
            offset = insertion["original_byte_offset"]
            self.assertTrue(raw[:offset].endswith(b"  bind(c) :: /saved_pair/\n"))
            reconstructed = reconstructed[:offset] + insertion["inserted"].encode() + reconstructed[offset:]
            start, end = insertion["control_byte_span"]
            self.assertEqual(fixed[start:end], b"  save /saved_pair/\n")
        self.assertEqual(reconstructed, fixed)
        self.assertEqual({row["scope"] for row in control["confirmation_insertions"]}, {"store_pair", "load_pair"})
        self.assertEqual(raw.split(b"end program bind_common_retention")[0],
                         fixed.split(b"end program bind_common_retention")[0])

    def test_every_common_read_follows_writer_definition_and_complete_return(self):
        for spec in self.specs.values():
            main, external = spec["source"].split("end program bind_common_retention\n", 1)
            writer = external.split("subroutine store_pair(", 1)[1].split("end subroutine store_pair", 1)[0]
            reader = external.split("subroutine load_pair(", 1)[1].split("end subroutine load_pair", 1)[0]
            self.assertTrue(writer.endswith("  first=left_value\n  second=right_value\n  visits=visits+1_c_int\n"))
            self.assertTrue(reader.endswith("  left_value=first\n  right_value=second\n  visits=visits+1_c_int\n"))
            self.assertNotIn("call ", writer)
            self.assertNotIn("call ", reader)
            calls = re.findall(r"(?m)^\s*call (.+)$", main)
            self.assertEqual(calls, ["store_pair(left_input, right_input, writer_visits)",
                                     "load_pair(left_observed, right_observed, reader_visits)"] * 2)
            first, second = main.split("  left_input=11_c_int\n", 1)[1].split("  left_input=17_c_int\n")
            for part, right, label in ((first, 13, "first"), (second, 19, "second")):
                self.assertTrue(part.startswith(f"  right_input={right}_c_int\n  call store_pair"))
                self.assertLess(part.index("call store_pair"), part.index(f"BCS:writer-{label}"))
                self.assertLess(part.index(f"BCS:writer-{label}"), part.index("call load_pair"))
                self.assertLess(part.index("call load_pair"), part.index(f"BCS:reader-{label}"))
                self.assertLess(part.index(f"BCS:reader-{label}"), part.index(f"BCS:left-{label}"))

    def test_independent_literal_value_visit_cycle_and_check_observers_are_all_consumed(self):
        for spec in self.specs.values():
            main = spec["source"].split("end program bind_common_retention", 1)[0]
            expected = [(expression, str(value), "BCS:" + label) for label, expression, value in EXPECTED_GUARDS]
            self.assertEqual(re.findall(r"if \((\w+) /= (\d+)_c_int\) error stop '([^']+)'", main), expected)
            self.assertEqual(main.count("  checks=checks+1_c_int\n"), 10)
            self.assertEqual(main.count("  cycles=cycles+1_c_int\n"), 2)
            for counter in ("writer_visits", "reader_visits", "checks", "cycles"):
                self.assertIn(f"  {counter}=0_c_int\n", main)
                self.assertLess(main.index(f"  {counter}=0_c_int"), main.index("  call store_pair"))
            self.assertNotRegex(main, r"::[^\n]*=")
            self.assertTrue(main.endswith("  if (checks /= 10_c_int) error stop 'BCS:check-total'\n"
                                          "  write(*,'(a)') 'BIND COMMON SAVE OK'\n"))

    def test_every_wrong_oracle_probe_keeps_the_complete_program_and_one_exact_span(self):
        for spec in self.specs.values():
            self.assertEqual(len(spec["guards"]), 12)
            self.assertEqual([(row["id"], row["expression"], row["expected"]) for row in spec["guards"][:-1]],
                             EXPECTED_GUARDS)
            spans = []
            for guard in spec["guards"]:
                raw = spec["source"].encode()
                changed = generated.wrong_oracle_source(spec, guard)
                start, end = guard["span"]
                self.assertEqual(raw[start:end].decode(), guard["literal"])
                self.assertEqual(changed[:start], raw[:start])
                self.assertEqual(changed[start + len(guard["replacement"]):], raw[end:])
                self.assertEqual(changed.count(b"\n"), raw.count(b"\n"))
                self.assertEqual(changed.count(b"subroutine "), raw.count(b"subroutine "))
                self.assertEqual(changed.count(b"  common /saved_pair/"), 2)
                self.assertNotEqual(changed, raw)
                spans.append((start, end))
                if guard["kind"] == "guard":
                    self.assertEqual(guard["replacement"], f"{guard['expected'] + 1}_c_int")
                    self.assertIn(guard["failure_token"].encode(), changed)
                    self.assertIn(b"write(*,'(a)') 'BIND COMMON SAVE OK'", changed)
            self.assertEqual(len(set(spans)), 12)
            for (_, end), (start, _) in zip(spans, spans[1:]):
                self.assertLess(end, start)

    def staged(self, case, family, mode, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic process transport only")
        raw = (case.fixture.root / "source.f90").read_bytes()
        calls = []

        def transport(command, cwd, timeout, stdin=None):
            self.assertEqual(timeout, 5)
            self.assertIsNone(stdin)
            workspace = Path(cwd).resolve()
            self.assertEqual((workspace / "source.f90").read_bytes(), raw)
            if "-c" in command:
                phase = "compile"
                self.assertEqual(Path(command[command.index("-c") + 1]), workspace / "source.f90")
            elif "-o" in command:
                phase = "link"
            else:
                phase = "run"
                self.assertEqual(command[-1], str(workspace / "program"))
            calls.append(phase)
            code, out, err, timeout_flag = 0, "", "", False
            if fault == phase + "-failure":
                code, err = 1, "synthetic " + phase + " failure"
            elif phase == "run":
                out = "BIND COMMON SAVE OK\n"
                if fault == "early-success":
                    out = ""
                elif fault == "wrong-output":
                    out = "BIND COMMON SAVE BAD\n"
                elif fault == "extra-output":
                    out += "unrequested\n"
                elif fault == "stderr":
                    err = "unrequested\n"
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timeout_flag = True
            if phase != "run" and not code:
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact")
            return runner.ProcessResult(code, out + err, timeout_flag, out, err, out.encode(), err.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        identity = dict(compiler.configuration(), version=compiler.version)
        ran = validate_case_trace(self.members[case.name], asdict(check), identity, ROOT, None, False)
        self.assertEqual(ran, "run" in calls)
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertEqual([step["phase"] for step in check.trace], calls)
        self.assertEqual(check.execution_context["compiler_resources"], {})
        return check, calls

    def test_real_staging_and_ordered_compile_link_run_traces_for_both_roles(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                with self.subTest(case=case.name, family=family):
                    check, calls = self.staged(case, family, mode)
                    self.assertEqual((check.outcome, check.phase), ("pass", "run"))
                    self.assertEqual(calls, ["compile", "link", "run"])

    def test_early_success_wrong_completion_and_native_failures_never_satisfy_the_oracle(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                for fault in ("early-success", "wrong-output", "extra-output", "stderr", "run-failure",
                              "crash", "timeout", "compile-failure", "link-failure"):
                    with self.subTest(case=case.name, family=family, fault=fault):
                        check, calls = self.staged(case, family, mode, fault)
                        self.assertEqual(check.outcome, "fail")
                        if fault in ("compile-failure", "link-failure"):
                            self.assertNotIn("run", calls)
                            self.assertNotEqual(check.phase, "run")

    def test_owned_facets_control_opt_in_and_all_foreign_requirements_remain_separate(self):
        catalogue = self.registry.catalogues["8.5.5"]
        requirement = self.registry.requirements[generated.RULE]
        self.assertEqual(requirement["positive_control_facets"], ["explicit-save-confirmation"])
        self.assertEqual(set(requirement["pending"]),
                         {"member-save-source-use", "consistent-common-labels", "module-variable-save-distinction"})
        self.assertEqual(set(requirement["facets"]) - set(requirement["pending"]), set(generated.FACETS))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        self.assertEqual(placement.synced_catalogue(catalogue), catalogue)
        for other_pending in ("actual", "none"):
            candidate = copy.deepcopy(catalogue)
            for row in candidate["requirements"]:
                if row["id"] != generated.RULE and other_pending == "none":
                    row["pending"] = {}
            expected = copy.deepcopy(candidate)
            self.assertEqual(generated.synced_catalogue(candidate), expected)
            text = generated.render_view(candidate)
            for row in candidate["requirements"]:
                self.assertIn(render_requirement(row), text)
            self.assertEqual(candidate, expected)
        for path, raw in placement.build_corpus()[0].items():
            self.assertEqual(path.read_bytes(), raw)

    def test_shared_render_is_composable_and_keeps_the_C819_managed_view(self):
        catalogue = self.registry.catalogues["8.5.5"]
        view = generated.render_view(catalogue)
        self.assertEqual(view, (ROOT / generated.VIEW).read_text())
        self.assertEqual(placement.render_view(catalogue), view)
        for marker in ("<!-- BEGIN GENERATED 8.5.5 -->", "<!-- END GENERATED 8.5.5 -->",
                       "<!-- BEGIN BIND COMMON SAVE -->", "<!-- END BIND COMMON SAVE -->"):
            self.assertEqual(view.count(marker), 1)
        native = Registry(ROOT)
        native.catalogues = {"8.5.5": catalogue}
        native.render()

    def test_source_case_and_inventory_lifecycles_do_not_rewrite_other_owners(self):
        registry = Registry(ROOT)
        original_catalogues = copy.deepcopy(registry.catalogues)
        original_reviews = copy.deepcopy(registry.reviews)
        original_links = copy.deepcopy(registry.evidence.links)
        original_source_uses = copy.deepcopy(registry.source_uses.data)
        original_inventory = copy.deepcopy(registry.execution.data)
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original_catalogues["8.5.5"])
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory source lifecycle only."
            registry.catalogues["8.5.5"] = candidate
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.5.5")
            self.assertEqual(registry.catalogue_review_state("8.5.5"), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertIn(f"**Source review: {state}.**", generated.render_view(candidate))
        for case in self.cases.values():
            fingerprint = case.fingerprint(registry)
            record = dict(state="source-reviewed", fingerprint=fingerprint, sources=["8.5.5#p3"],
                          rationale="In-memory independent fixture state, never disk approval.")
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
                rationale="In-memory inventory binding only; actual blockers preserved.")
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

    def test_exact_four_fixture_files_remain_byte_identical_on_regeneration(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("bind_common_save_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 4)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        self.assertEqual(generated.build_corpus()[0], self.files)


if __name__ == "__main__":
    unittest.main()
