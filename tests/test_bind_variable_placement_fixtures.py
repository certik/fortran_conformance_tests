"""C819 complete contexts, minimal repairs, causal staging and independent adjudications."""
import copy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_validation import validate_case_trace
from fixture_support import load_fixture
from suite_data import Registry, render_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_bind_variable_placement_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))
FACETS = {
    "main_local": "main-local",
    "external_local": "external-procedure-local",
    "contained_local": "contained-procedure-local",
}
GNU_CAUSE = ("Variable 'bound_value' at (1) cannot be BIND(C) because it is neither a COMMON block "
             "nor declared at the module level scope")
FLANG_CAUSE = "A variable with BIND(C) attribute may only appear in the specification part of a module"
PREFIXES = ("", "Internal: ", "Not yet implemented: ", "Unimplemented: ", "Unsupported: ",
            "Internal error: ", "Verifier error: ")


class BindVariablePlacementFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases
                     if "/fixtures/bind_variable_placement_" in case.path}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def case(self, variant, negative=False):
        return self.cases[generated.identifier(variant, negative)]

    def test_exact_seven_compile_cases_three_negatives_four_positive_controls(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 7)
        self.assertEqual(sum(case.kind == "invalid" for case in self.cases.values()), 3)
        for case in self.cases.values():
            self.assertEqual(case.rule, "C819")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if case.kind == "invalid" else "success")
            self.assertIsNone(case.fixture.link)
        for variant, facet in FACETS.items():
            self.assertEqual(self.case(variant, True).meta.facets, [facet])
            self.assertEqual(self.case(variant + "_control").meta.facets, [facet])
        self.assertEqual(self.case("module_admission").meta.facets, ["module-admission"])
        self.assertEqual({case.name for case in self.all_cases if case.rule == "C819"}, set(self.cases))

    def test_complete_contexts_prior_intrinsic_kind_and_single_ordinary_scalar(self):
        sources = {
            "main_local": (
                "program main_local\n  use, intrinsic :: iso_c_binding, only: c_int\n  implicit none\n"
                "  integer(c_int), bind(c) :: bound_value\n  bound_value=1_c_int\nend program main_local\n"),
            "external_local": (
                "subroutine external_local()\n  use, intrinsic :: iso_c_binding, only: c_int\n  implicit none\n"
                "  integer(c_int), bind(c) :: bound_value\n  bound_value=1_c_int\nend subroutine external_local\n"),
            "contained_local": (
                "module placement_host\n  implicit none\ncontains\n  subroutine contained_local()\n"
                "    use, intrinsic :: iso_c_binding, only: c_int\n    implicit none\n"
                "    integer(c_int), bind(c) :: bound_value\n    bound_value=1_c_int\n"
                "  end subroutine contained_local\nend module placement_host\n"),
        }
        for variant, source in sources.items():
            self.assertEqual(self.specs[generated.identifier(variant, True)]["source"], source)
            self.assertEqual(source.count("bind(c)"), 1)
            self.assertEqual(source.count(":: bound_value"), 1)
            self.assertEqual(source.count("="), 1)
            for forbidden in ("parameter", "pointer", "allocatable", "dimension", "common", "intent",
                              "result(", "name=", "save", "interface", "call ", "["):
                self.assertNotIn(forbidden, source)
            self.assertLess(source.index("use, intrinsic"), source.index("integer(c_int)"))
            declaration_line = 7 if variant == "contained_local" else 4
            diagnostic = self.case(variant, True).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                             ("source.f90", declaration_line, declaration_line))
            self.assertIn("integer(c_int), bind(c) :: bound_value", source.splitlines()[declaration_line - 1])

    def test_module_admission_is_a_module_specification_not_a_C_or_retention_observer(self):
        source = self.specs[generated.identifier("module_admission")]["source"]
        self.assertEqual(source,
                         "module module_admission\n  use, intrinsic :: iso_c_binding, only: c_int\n"
                         "  implicit none\n  integer(c_int), bind(c) :: bound_value\nend module module_admission\n")
        self.assertNotIn("contains", source)
        self.assertNotIn("=", source)
        self.assertNotIn("save", source)
        self.assertNotIn("call", source)
        self.assertNotIn("source.f90", source)

    def test_exact_three_repairs_delete_only_BIND_C_and_its_separator(self):
        for variant in FACETS:
            negative = self.specs[generated.identifier(variant, True)]
            control = self.specs[negative["repair"]["control_id"]]
            raw, fixed = negative["source"].encode(), control["source"].encode()
            repair = negative["repair"]
            start = raw.index(b", bind(c)")
            end = start + len(b", bind(c)")
            self.assertEqual(repair["byte_span_zero_based_half_open"], [start, end])
            self.assertEqual(fixed, raw[:start] + raw[end:])
            self.assertEqual(len(raw) - len(fixed), 9)
            self.assertEqual(raw.count(b"\n"), fixed.count(b"\n"))
            self.assertEqual(raw.count(b"bound_value"), fixed.count(b"bound_value"))
            self.assertEqual(repair["negative_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(repair["control_sha256"], hashlib.sha256(fixed).hexdigest())
            line = repair["line"]
            self.assertEqual(raw.splitlines()[:line - 1], fixed.splitlines()[:line - 1])
            self.assertEqual(raw.splitlines()[line:], fixed.splitlines()[line:])
            self.assertEqual(fixed.splitlines()[line - 1],
                             raw.splitlines()[line - 1].replace(b", bind(c)", b""))
            self.assertIn(b"bound_value=1_c_int\n", fixed)
            if variant == "contained_local":
                self.assertTrue(fixed.startswith(b"module placement_host\n"))
                self.assertTrue(fixed.endswith(b"end module placement_host\n"))

    def staged(self, case, family, message=None, code=1, line=None, end_line=None, filename=None,
               severity="error", timed_out=False, echo_only=False, silent=False, tail="", fixture=None):
        fixture = fixture or case.fixture
        compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "mocked process transport only")
        identity = dict(compiler.configuration(), version=compiler.version)
        raw = (fixture.root / "source.f90").read_bytes()
        target = fixture.expectation.diagnostic.get("line", 4)
        first = target if line is None else line
        last = first if end_line is None else end_line
        cause = message if message is not None else (FLANG_CAUSE if family == "flang" else GNU_CAUSE)
        calls = []

        def transport(command, cwd, timeout, stdin=None):
            self.assertEqual(timeout, 5)
            self.assertIsNone(stdin)
            source = Path(command[command.index("-c") + 1])
            workspace = Path(cwd).resolve()
            self.assertEqual(source.parent, workspace)
            self.assertEqual(source.name, "source.f90")
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(command[0], family)
            source_line = raw.decode().splitlines()[target - 1]
            column = source_line.index("bound_value") + 1
            report_file = filename or str(source)
            reported = "syntax error" if echo_only else cause
            if family == "lfortran":
                text = f"{report_file}:{first}-{last}:1-80: semantic {severity}: {reported}\n"
            elif family == "gfortran":
                text = (f"{report_file}:{first}:{column}:\n\n {first:4} | {source_line}\n"
                        f"      | {' ' * (column - 1)}1\n{severity.capitalize()}: {reported}\n")
            else:
                text = (f"error: Semantic errors in {source}\n"
                        f"{report_file}:{first}:{column}: {severity}: {reported}\n"
                        f"  {source_line}\n  {' ' * (column - 1)}^^^^^^^^^^^\n")
            if echo_only:
                text += f" {first:4} | ! {cause}\n      | 1\n"
            text += tail
            if silent:
                text = ""
            calls.append(dict(command=command, workspace=str(workspace)))
            return runner.ProcessResult(code, text, timed_out, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(fixture, compiler, timeout=5)
        self.assertEqual(len(calls), 1)
        self.assertEqual(check.phase, "compile")
        self.assertEqual(len(check.trace), 1)
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(check.execution_context["workspace"], calls[0]["workspace"])
        self.assertEqual(check.execution_context["compiler_resources"], {})
        self.assertEqual((check.trace[0]["phase"], check.trace[0]["step"]), ("compile", "source"))
        self.assertFalse(validate_case_trace(self.members[case.name], asdict(check), identity, ROOT, None, False))
        return check

    def test_189_causal_and_wrapped_vectors_use_real_staging_all_families_modes_and_statuses(self):
        vectors = []
        for variant in FACETS:
            case = self.case(variant, True)
            for family, mode in FAMILIES:
                cause = FLANG_CAUSE if family == "flang" else GNU_CAUSE
                for code in (0, 1, 2):
                    for prefix in PREFIXES:
                        with self.subTest(case=case.name, family=family, mode=mode, code=code, prefix=prefix):
                            check = self.staged(case, family, prefix + cause, code=code)
                            self.assertEqual(check.outcome, "fail" if prefix else "pass")
                            if not prefix:
                                self.assertEqual(check.note, "diagnoses without rejection" if code == 0 else "rejects")
                            vectors.append((case.name, family, mode, code, prefix))
        self.assertEqual(len(vectors), 189)
        self.assertEqual(len(set(vectors)), 189)

    def test_wrong_location_subject_role_and_cause_are_not_corroboration(self):
        wrong_causes = (
            "BIND(C)", "module", "BIND(C) module",
            GNU_CAUSE.replace("'bound_value'", "'other_value'"),
            GNU_CAUSE.replace("BIND(C)", "SAVE"),
            FLANG_CAUSE.replace("BIND(C)", "ALLOCATABLE"),
            "A procedure name cannot appear in a type declaration with BIND(C)",
            "Dummy argument 'bound_value' must be interoperable",
            "Function result 'bound_value' has an unsupported kind",
            "The KIND argument of INTEGER is invalid",
            "Cannot read module iso_c_binding", "Missing explicit interface",
            "Syntax error in the BIND language-binding-spec", "Invalid initialization",
            "Duplicate BIND(C) attribute on variable 'bound_value'",
        )
        for variant in FACETS:
            case = self.case(variant, True)
            target = case.fixture.expectation.diagnostic["line"]
            for family, _ in FAMILIES:
                for line in (0, 1, target - 1, target + 1):
                    self.assertEqual(self.staged(case, family, line=line).outcome, "fail")
                self.assertEqual(self.staged(case, family, filename="different.f90").outcome, "fail")
                self.assertEqual(self.staged(case, family, echo_only=True).outcome, "fail")
                for message in wrong_causes:
                    with self.subTest(case=case.name, family=family, message=message):
                        self.assertEqual(self.staged(case, family, message).outcome, "fail")
                cause = FLANG_CAUSE if family == "flang" else GNU_CAUSE
                for prefix in ("Not implemented: ", "Not supported: ", "Recovery: ", "ASR: ", "Wrong kind: ",
                               "Dummy argument: ", "Function result: ", "Initializer: "):
                    self.assertEqual(self.staged(case, family, prefix + cause).outcome, "fail")
            for first, last in ((target - 1, target), (target, target + 1), (target + 1, target)):
                self.assertEqual(self.staged(case, "lfortran", line=first, end_line=last).outcome, "fail")

    def test_silent_acceptance_or_rejection_cannot_replace_a_located_report(self):
        for variant in FACETS:
            case = self.case(variant, True)
            for family, _ in FAMILIES:
                for code in (0, 1, 2):
                    self.assertEqual(self.staged(case, family, code=code, silent=True).outcome, "fail")

    def test_abnormal_statuses_timeouts_resources_ASR_and_native_failures_never_count(self):
        for variant in FACETS:
            case = self.case(variant, True)
            for family, _ in FAMILIES:
                for code in (-6, -11, 128, 134, 139):
                    self.assertEqual(self.staged(case, family, code=code).outcome, "fail")
                self.assertEqual(self.staged(case, family, code=0, timed_out=True).outcome, "fail")
                for tail in ("\ninternal compiler error: failure\n", "\nASR verify pass error\n",
                             "\nout of memory\n", "\nLLVM ERROR: failure\n", "\nerror: Internal: failure\n"):
                    self.assertEqual(self.staged(case, family, tail=tail).outcome, "fail")

    def test_nonfatal_requires_an_exact_family_cause_and_is_not_a_current_native_allowance(self):
        for variant in FACETS:
            case = self.case(variant, True)
            self.assertNotIn("allow_nonfatal", case.fixture.expectation.diagnostic)
            for family, _ in FAMILIES:
                message = FLANG_CAUSE if family == "flang" else GNU_CAUSE
                for code in (0, 1, 2):
                    self.assertEqual(self.staged(case, family, message, code=code, severity="warning").outcome, "fail")
                diagnostic = copy.deepcopy(case.fixture.expectation.diagnostic)
                diagnostic["allow_nonfatal"] = [dict(compiler=family, severity="warning", equals_any=[message])]
                fixture = replace(case.fixture, expectation=replace(case.fixture.expectation, diagnostic=diagnostic))
                for code in (0, 1, 2):
                    self.assertEqual(self.staged(case, family, message, code=code, severity="warning", fixture=fixture).outcome, "pass")
                for other in (message + " for a different reason", "Not yet implemented: " + message,
                              "Unimplemented: " + message, "Internal: " + message):
                    self.assertEqual(self.staged(case, family, other, code=0, severity="warning", fixture=fixture).outcome, "fail")
                mismatched = copy.deepcopy(diagnostic)
                mismatched["allow_nonfatal"][0]["compiler"] = "flang" if family != "flang" else "gfortran"
                other_fixture = replace(case.fixture, expectation=replace(case.fixture.expectation, diagnostic=mismatched))
                self.assertEqual(self.staged(case, family, message, code=0, severity="warning", fixture=other_fixture).outcome, "fail")
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "source.f90").write_bytes((case.fixture.root / "source.f90").read_bytes())
                    data = copy.deepcopy(self.specs[case.name]["manifest"])
                    data["expect"]["diagnostic"] = diagnostic
                    (root / "fixture.json").write_text(json.dumps(data))
                    self.assertEqual(load_fixture(root / "fixture.json", runner.PROFILES).expectation.diagnostic, diagnostic)

    def test_each_positive_stages_exact_source_and_compiles_only(self):
        for case in self.cases.values():
            if case.kind != "valid":
                continue
            for family, mode in FAMILIES:
                with self.subTest(case=case.name, family=family, mode=mode):
                    compiler = runner.Compiler(family, family, mode, "mocked positive process transport")
                    raw = (case.fixture.root / "source.f90").read_bytes()
                    calls = []

                    def transport(command, cwd, timeout, stdin=None):
                        source = Path(command[command.index("-c") + 1])
                        self.assertEqual(source.parent, Path(cwd).resolve())
                        self.assertEqual(source.name, "source.f90")
                        self.assertEqual(source.read_bytes(), raw)
                        self.assertEqual(timeout, 5)
                        self.assertIsNone(stdin)
                        Path(command[command.index("-o") + 1]).write_bytes(b"mock object")
                        calls.append(command)
                        return runner.ProcessResult(0, "", False, "", "", b"", b"")

                    with patch.object(runner, "run", side_effect=transport):
                        check = runner.check_fixture(case.fixture, compiler, timeout=5)
                    self.assertEqual((check.outcome, check.phase, len(calls)), ("pass", "compile", 1))
                    self.assertFalse(validate_case_trace(
                        self.members[case.name], asdict(check), dict(compiler.configuration(), version=compiler.version),
                        ROOT, None, False))

    def test_only_C819_selected_facets_and_authorized_requirement_fields_change(self):
        catalogue = self.registry.catalogues["8.5.5"]
        c819 = next(row for row in catalogue["requirements"] if row["id"] == "C819")
        self.assertEqual(set(c819["pending"]), {
            "submodule-local", "common-placement-source-use", "interface-result-dummy-source-use"})
        self.assertEqual(set(c819["facets"]) - set(c819["pending"]), set(generated.FACETS))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        for unrelated_pending in ("actual", "none"):
            candidate = copy.deepcopy(catalogue)
            if unrelated_pending == "none":
                for row in candidate["requirements"]:
                    if row["id"] != "C819":
                        row["pending"] = {}
            expected = copy.deepcopy(candidate)
            result = generated.synced_catalogue(candidate)
            self.assertEqual(result, expected)
            self.assertEqual(candidate, expected)
            text = generated.render_view(result)
            for row in result["requirements"]:
                self.assertIn(render_requirement(row), text)
            others = sum(len(row["pending"]) for row in result["requirements"] if row["id"] != "C819")
            self.assertIn(f"have {others} pending facets ({len(c819['pending']) + others} total in 8.5.5)", text)
        native = Registry(ROOT)
        native.catalogues = {"8.5.5": catalogue}
        native.render()
        self.assertEqual(generated.render_view(catalogue), (ROOT / generated.VIEW).read_text())

    def test_generation_preserves_renewable_source_case_inventory_and_other_owner_states(self):
        registry = Registry(ROOT)
        original = copy.deepcopy(registry.catalogues["8.5.5"])
        files_before = generated.build_corpus()[0]
        records_before = copy.deepcopy(registry.reviews)
        source_use_before = copy.deepcopy(registry.source_uses.data)
        links_before = copy.deepcopy(registry.evidence.links)
        aggregates_before = copy.deepcopy(registry.execution.aggregates)
        foreign_catalogues = {section: copy.deepcopy(catalogue) for section, catalogue in registry.catalogues.items()
                              if section != "8.5.5"}
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original)
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory source lifecycle check; never written as approval."
            registry.catalogues["8.5.5"] = candidate
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.5.5")
            self.assertEqual(registry.catalogue_review_state("8.5.5"), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertIn(f"**Source review: {state}.**", generated.render_view(candidate))
        candidate["review_fingerprint"] = registry.catalogue_fingerprint("8.5.5")
        for case in self.cases.values():
            fingerprint = case.fingerprint(registry)
            record = dict(state="source-reviewed", fingerprint=fingerprint, sources=["C819"],
                          rationale="In-memory fixture adjudication check; no disk approval.")
            registry._review_record(case.name, record)
            registry.reviews[case.name] = record
            self.assertEqual(registry.review(case.name, fingerprint, [case.name]).state, "source-reviewed")
            registry.reviews[case.name] = dict(record, fingerprint="0" * 64)
            self.assertEqual(registry.review(case.name, fingerprint, [case.name]).state, "stale")
            registry.reviews[case.name] = record
        cases = runner.collect_cases(ROOT / "tests", registry)
        for report in registry.execution.report(cases, include_members=False):
            aggregate = registry.execution.aggregates[report["id"]]
            record = copy.deepcopy(aggregate["review"])
            record.update(state="source-reviewed", fingerprint=report["review"]["fingerprint"],
                          rationale="In-memory inventory lifecycle check; no disk renewal.")
            aggregate["review"] = record
            registry.execution._validate(aggregate)
        for report in registry.execution.report(cases, include_members=False):
            self.assertEqual(report["state"], "stale" if report["blockers"] else "current")
        self.assertEqual(generated.build_corpus()[0], files_before)
        fresh = Registry(ROOT)
        self.assertEqual(fresh.reviews, records_before)
        self.assertEqual(fresh.source_uses.data, source_use_before)
        self.assertEqual(fresh.evidence.links, links_before)
        self.assertEqual(fresh.execution.aggregates, aggregates_before)
        self.assertEqual({section: catalogue for section, catalogue in fresh.catalogues.items()
                          if section != "8.5.5"}, foreign_catalogues)

    def test_exact_fourteen_files_and_generator_idempotence(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("bind_variable_placement_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 14)
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")


if __name__ == "__main__":
    unittest.main()
