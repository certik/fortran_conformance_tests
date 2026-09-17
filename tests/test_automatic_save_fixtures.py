"""C814 source validity, exact repairs, real staging and renewable administrative states."""
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
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_automatic_save_fixtures as generated
import generate_type_parameter_entry_fixtures as entry

NEGATIVE_FACETS = {
    "character_selector": "character-selector-save",
    "character_entity": "character-entity-length-save",
    "explicit_bound": "explicit-bound-save",
}
DECLARATIONS = {
    "character_selector": "character(len=n), save :: text",
    "character_entity": "character, save :: text*(n)",
    "explicit_bound": "integer, save :: a(n)",
}
MESSAGES = {
    "character_selector": "Automatic object 'text' at (1) cannot have the SAVE attribute",
    "character_entity": "Automatic object 'text' at (1) cannot have the SAVE attribute",
    "explicit_bound": "Automatic object 'a' at (1) cannot have the SAVE attribute",
}


class AutomaticSaveFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if "/fixtures/automatic_save_" in case.path}

    def case(self, variant, negative=False):
        return self.cases[generated.identifier(variant, negative)]

    def test_exact_ten_compile_cases_three_negatives_seven_positive_controls(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 10)
        self.assertEqual(sum(case.kind == "invalid" for case in self.cases.values()), 3)
        self.assertEqual(sum(case.kind == "valid" for case in self.cases.values()), 7)
        for case in self.cases.values():
            self.assertEqual(case.rule, "C814")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertEqual(case.fixture.expectation.step, "source")
            self.assertIsNone(case.fixture.link)
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if case.kind == "invalid" else "success")
        for variant, facet in NEGATIVE_FACETS.items():
            self.assertEqual(self.case(variant, True).meta.facets, [facet])
            self.assertEqual(self.case(variant + "_control").meta.facets, [facet])
        for variant in ("parameter_constant", "len_constant", "size_constant"):
            self.assertEqual(self.case(variant).meta.facets, ["constant-specification-admission"])
        self.assertEqual(self.case("bare_save").meta.facets, ["bare-save-admission"])

    def test_negative_context_is_complete_pretyped_nonoptional_IN_and_an_automatic_local(self):
        for variant, declaration in DECLARATIONS.items():
            spec = self.specs[generated.identifier(variant, True)]
            body = "a=1" if variant == "explicit_bound" else "text='x'"
            expected = (f"subroutine {variant}(n)\nimplicit none\ninteger, intent(in) :: n\n"
                        f"{declaration}\n{body}\nend subroutine {variant}\n")
            self.assertEqual(spec["source"], expected)
            self.assertTrue(spec["automatic"])
            self.assertNotIn("pointer", expected)
            self.assertNotIn("allocatable", expected)
            self.assertNotIn("optional", expected)
            self.assertNotIn("intent(out)", expected)
            self.assertNotIn(":: n=", expected)
            self.assertNotIn(":: text=", expected)
            self.assertNotIn(":: a(n)=", expected)
            diagnostic = self.case(variant, True).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]), ("source.f90", 4, 4))

    def test_three_repairs_are_exact_SAVE_comma_deletions_not_entity_or_scope_substitutes(self):
        for variant in NEGATIVE_FACETS:
            negative = self.specs[generated.identifier(variant, True)]
            control = self.specs[negative["repair"]["control_id"]]
            raw, fixed = negative["source"].encode(), control["source"].encode()
            start, end = negative["repair"]["byte_span_zero_based_half_open"]
            self.assertEqual(raw[start:end], b", save")
            self.assertEqual(fixed, raw[:start] + raw[end:])
            self.assertEqual(len(raw) - len(fixed), 6)
            self.assertEqual(raw.splitlines()[:3], fixed.splitlines()[:3])
            self.assertEqual(raw.splitlines()[4:], fixed.splitlines()[4:])
            self.assertIn("integer, intent(in) :: n\n", control["source"])
            self.assertTrue(control["automatic"])
            self.assertEqual(control["source"].splitlines()[3], DECLARATIONS[variant].replace(", save", ""))
            self.assertNotIn("save", control["source"].splitlines()[3])

    def test_constant_parameter_is_not_given_SAVE_and_remains_a_prior_constant(self):
        source = self.specs[generated.identifier("parameter_constant")]["source"]
        self.assertEqual(source, "subroutine parameter_constant()\nimplicit none\ninteger, parameter :: extent=3\n"
                                "integer, save :: a(extent)\na=1\nend subroutine parameter_constant\n")
        self.assertLess(source.index("parameter :: extent=3"), source.index("save :: a(extent)"))
        self.assertNotIn("parameter, save", source)

    def test_LEN_and_SIZE_inquire_on_prior_declared_properties_not_payload(self):
        expected = {
            "len_constant": ("character(len=3) :: basis", "character(len=len(basis)), save :: text", "text='abc'"),
            "size_constant": ("integer :: basis(3)", "integer, save :: a(size(basis))", "a=1"),
        }
        for variant, (prior, target, body) in expected.items():
            source = self.specs[generated.identifier(variant)]["source"]
            self.assertEqual(source, f"subroutine {variant}()\nimplicit none\n{prior}\n{target}\n{body}\nend subroutine {variant}\n")
            self.assertLess(source.index(prior), source.index(target))
            self.assertEqual(source.count("basis"), 2)
            self.assertNotIn("basis=", source)
            self.assertFalse(self.specs[generated.identifier(variant)]["automatic"])
            self.assertNotIn("pointer", source)
            self.assertNotIn("allocatable", source)

    def test_bare_SAVE_filters_allowed_items_in_a_procedure_not_a_BLOCK(self):
        source = self.specs[generated.identifier("bare_save")]["source"]
        self.assertEqual(source, "subroutine bare_save(n)\nimplicit none\ninteger, intent(in) :: n\n"
                                "character(len=n) :: text\nsave\ntext='x'\nend subroutine bare_save\n")
        self.assertEqual(source.splitlines().count("save"), 1)
        self.assertNotIn(", save", source)
        self.assertNotIn("save ::", source)
        self.assertNotIn("block", source)
        self.assertTrue(self.specs[generated.identifier("bare_save")]["automatic"])

    def staged_diagnostic(self, variant, message, code=1, line=4, filename=None, severity="error", timeout=False, allow=None):
        fixture = self.case(variant, True).fixture
        if allow is not None:
            diagnostic = copy.deepcopy(fixture.expectation.diagnostic)
            diagnostic["allow_nonfatal"] = allow
            fixture = replace(fixture, expectation=replace(fixture.expectation, diagnostic=diagnostic))
        compiler = runner.Compiler("mock-gfortran", "gfortran", "f2023", "synthetic transport")
        calls = []

        def transport(command, cwd, limit, stdin=None):
            self.assertEqual(limit, 5)
            staged = Path(command[command.index("-c") + 1])
            self.assertEqual(staged.parent, Path(cwd).resolve())
            self.assertEqual(staged.name, "source.f90")
            self.assertEqual(staged.read_bytes(), (fixture.root / "source.f90").read_bytes())
            self.assertIn("-std=f2023", command)
            text = f"{filename or staged}:{line}:1: {severity}: {message}\n"
            calls.append((str(staged), text))
            return runner.ProcessResult(code, text, timeout, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(fixture, compiler, timeout=5)
        self.assertEqual(len(calls), 1)
        self.assertEqual(check.phase, "compile")
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256((fixture.root / "source.f90").read_bytes()).hexdigest()})
        self.assertEqual(check.trace[0]["phase"], "compile")
        self.assertEqual(check.execution_context["workspace"], str(Path(calls[0][0]).parent))
        return check

    def test_real_staging_allows_ordinary_zero_nonzero_causal_reports_without_codes(self):
        for variant, message in MESSAGES.items():
            for code in (0, 1, 2):
                check = self.staged_diagnostic(variant, message, code)
                self.assertEqual(check.outcome, "pass")
                self.assertEqual(check.note, "diagnoses without rejection" if code == 0 else "rejects")

    def test_source_span_subject_attribute_and_body_error_exclusions_with_mocked_transport(self):
        for variant, message in MESSAGES.items():
            for line in (1, 3, 5, 6):
                self.assertEqual(self.staged_diagnostic(variant, message, line=line).outcome, "fail")
            self.assertEqual(self.staged_diagnostic(variant, message, filename="wrong.f90").outcome, "fail")
            wrong = [
                "SAVE", "nonconstant expression", "Automatic object 'wrong' at (1) cannot have the SAVE attribute",
                "Dummy argument 'n' cannot have SAVE", "Function result cannot have SAVE", "Malformed character suffix",
                "Initialization of an automatic object is not permitted", "Missing explicit interface",
                "A SAVE statement in BLOCK must have a list", "Unknown SAVE syntax",
            ]
            for text in wrong:
                self.assertEqual(self.staged_diagnostic(variant, text).outcome, "fail")
            for prefix in ("Not yet implemented: ", "Unimplemented: ", "Unsupported: ", "Recovery: "):
                self.assertEqual(self.staged_diagnostic(variant, prefix + message).outcome, "fail")

    def test_manifest_nonfatal_whitelist_path_is_specific_and_only_mocked(self):
        for variant, message in MESSAGES.items():
            self.assertEqual(self.staged_diagnostic(variant, message, code=0, severity="warning").outcome, "fail")
            allowed = [dict(compiler="gfortran", severity="warning", equals_any=[message])]
            self.assertEqual(self.staged_diagnostic(variant, message, code=0, severity="warning", allow=allowed).outcome, "pass")
            self.assertEqual(self.staged_diagnostic(variant, message + " different cause", code=0, severity="warning", allow=allowed).outcome, "fail")
            mismatch = [dict(compiler="flang", severity="warning", equals_any=[message])]
            self.assertEqual(self.staged_diagnostic(variant, message, code=0, severity="warning", allow=mismatch).outcome, "fail")
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture = self.case(variant, True).fixture
                (root / "source.f90").write_bytes((fixture.root / "source.f90").read_bytes())
                data = copy.deepcopy(self.specs[fixture.name]["manifest"])
                data["expect"]["diagnostic"]["allow_nonfatal"] = allowed
                (root / "fixture.json").write_text(json.dumps(data))
                self.assertEqual(load_fixture(root / "fixture.json", runner.PROFILES).expectation.diagnostic["allow_nonfatal"], allowed)

    def test_native_failures_and_echo_do_not_override_the_selected_cause(self):
        for variant, message in MESSAGES.items():
            for code in (-6, -11, 139):
                self.assertEqual(self.staged_diagnostic(variant, message, code=code).outcome, "fail")
            self.assertEqual(self.staged_diagnostic(variant, message, code=0, timeout=True).outcome, "fail")
            for text in (
                message + "\nerror: Internal: verifier failure",
                message + "\ninternal compiler error: failure",
                message + "\nASR verify pass error",
                message + "\nout of memory",
            ):
                self.assertEqual(self.staged_diagnostic(variant, text).outcome, "fail")
            source_echo = f"syntax error\n 4 | ! {message}\n   | 1"
            self.assertEqual(self.staged_diagnostic(variant, source_echo).outcome, "fail")

    def test_exact_189_native_family_prefix_vectors_use_real_staging_and_traces(self):
        prefixes = ("", "Internal: ", "Not yet implemented: ", "Unimplemented: ", "Unsupported: ",
                    "Internal error: ", "Verifier error: ")
        members = {member["id"]: member for member in self.registry.execution._members(list(self.cases.values()))}
        vectors = []
        for variant, message in MESSAGES.items():
            case = self.case(variant, True)
            source = (case.fixture.root / "source.f90").read_bytes()
            for family, standard in (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018")):
                compiler = runner.Compiler(family, family, standard, "mocked process transport")
                identity = dict(compiler.configuration(), version=compiler.version)
                for code in (0, 1, 2):
                    for prefix in prefixes:
                        with self.subTest(case=case.name, family=family, standard=standard, code=code, prefix=prefix):
                            captured = []

                            def transport(command, cwd, timeout, stdin=None):
                                staged = Path(command[command.index("-c") + 1])
                                self.assertEqual(staged.parent, Path(cwd).resolve())
                                self.assertEqual(staged.name, "source.f90")
                                self.assertEqual(staged.read_bytes(), source)
                                self.assertEqual(timeout, 5)
                                self.assertIsNone(stdin)
                                if family == "lfortran":
                                    text = f"{staged}:4-4:1-60: semantic error: {prefix}{message}\n"
                                else:
                                    text = f"{staged}:4:1: error: {prefix}{message}\n"
                                captured.append(text)
                                return runner.ProcessResult(code, text, False, "", text, b"", text.encode())

                            with patch.object(runner, "run", side_effect=transport):
                                check = runner.check_fixture(case.fixture, compiler, timeout=5)
                            self.assertEqual(len(captured), 1)
                            self.assertEqual(check.phase, "compile")
                            self.assertEqual(len(check.trace), 1)
                            self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(source).hexdigest()})
                            self.assertFalse(validate_case_trace(
                                members[case.name], asdict(check), identity, ROOT, None, False))
                            self.assertEqual(check.outcome, "fail" if prefix else "pass")
                            vectors.append((case.name, family, standard, code, prefix))
        self.assertEqual(len(vectors), 189)
        self.assertEqual(len(set(vectors)), 189)

    def test_all_positive_controls_use_real_staging_and_only_compile_with_mocked_process(self):
        for case in self.cases.values():
            if case.kind != "valid":
                continue
            calls = []

            def transport(command, cwd, timeout, stdin=None):
                staged = Path(command[command.index("-c") + 1])
                self.assertEqual(staged.read_bytes(), (case.fixture.root / "source.f90").read_bytes())
                Path(command[command.index("-o") + 1]).write_bytes(b"mock object")
                calls.append(command)
                return runner.ProcessResult(0, "", False, "", "", b"", b"")

            with patch.object(runner, "run", side_effect=transport):
                check = runner.check_fixture(case.fixture, runner.Compiler("mock", "gfortran", "f2023"), timeout=5)
            self.assertEqual((check.outcome, check.phase, len(calls)), ("pass", "compile", 1))

    def test_case_source_and_inventory_adjudication_are_independent_of_generation(self):
        registry = Registry(ROOT)
        cases = runner.collect_cases(ROOT / "tests", registry)
        targets = [case for case in cases if case.name in self.specs]
        files_before = generated.build_corpus()[0]
        original_reviews = copy.deepcopy(registry.reviews)
        for case in targets:
            fingerprint = case.fingerprint(registry)
            record = dict(state="source-reviewed", fingerprint=fingerprint, sources=["C814"],
                          rationale="In-memory current case adjudication regression; no disk approval.")
            registry._review_record(case.name, record)
            registry.reviews[case.name] = record
            self.assertEqual(registry.review(case.name, fingerprint, [case.name]).state, "source-reviewed")
            stale = dict(record, fingerprint="0" * 64)
            registry.reviews[case.name] = stale
            self.assertEqual(registry.review(case.name, fingerprint, [case.name]).state, "stale")
            registry.reviews[case.name] = record
        catalogue = copy.deepcopy(registry.catalogues["8.3"])
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(catalogue)
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory source state regression; no disk approval."
            registry.catalogues["8.3"] = candidate
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.3")
            self.assertEqual(registry.catalogue_review_state("8.3"), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertIn(f"**Source review: {state}.**", generated.render_view(candidate))
        registry.catalogues["8.3"] = candidate
        candidate["review_fingerprint"] = registry.catalogue_fingerprint("8.3")
        report = registry.execution.report(cases)
        for item in report:
            aggregate = registry.execution.aggregates[item["id"]]
            record = copy.deepcopy(aggregate["review"])
            record.update(fingerprint=item["review"]["fingerprint"], state="source-reviewed",
                          rationale="In-memory current inventory regression; no disk approval.")
            aggregate["review"] = record
            registry.execution._validate(aggregate)
        self.assertTrue(all(item["state"] == "current" for item in registry.execution.report(cases)))
        self.assertEqual(generated.build_corpus()[0], files_before)
        self.assertEqual(Registry(ROOT).reviews, original_reviews)

    def test_shared_entry_requirement_generator_and_native_view_remain_consistent(self):
        catalogue = self.registry.catalogues["8.3"]
        c814 = next(item for item in catalogue["requirements"] if item["id"] == "C814")
        existing = next(item for item in catalogue["requirements"] if item["id"] == "S8.3-001")
        existing_before = copy.deepcopy(existing)
        initialization_before = copy.deepcopy(self.registry.catalogues["8.4"])
        initialization_path = ROOT / "doc/catalogues/initialization_8_4.json"
        initialization_bytes = initialization_path.read_bytes()
        self.assertEqual(set(c814["pending"]), {"pdt-length-save", "fixed-length-allocatable-save",
                                                "fixed-length-pointer-save", "inquiry-dependent-bound-save"})
        self.assertEqual(set(c814["facets"]) - set(c814["pending"]), set(generated.FACETS))
        updated = generated.synced_catalogue(catalogue)
        self.assertEqual(updated, catalogue)
        self.assertEqual(next(item for item in updated["requirements"] if item["id"] == "S8.3-001"), existing_before)
        entry_files, entry_specs = entry.build_corpus()
        for path, raw in entry_files.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(generated.render_view(catalogue), entry.render_view(catalogue, entry_specs))
        self.assertEqual(generated.render_view(catalogue), (ROOT / generated.VIEW).read_text())
        for unrelated_pending in (existing_before["pending"], {}):
            with self.subTest(unrelated_entry_pending=sorted(unrelated_pending)):
                candidate = copy.deepcopy(catalogue)
                unrelated = next(item for item in candidate["requirements"] if item["id"] == "S8.3-001")
                unrelated["pending"] = copy.deepcopy(unrelated_pending)
                preserved = copy.deepcopy(unrelated)
                result = generated.synced_catalogue(candidate)
                self.assertEqual(next(item for item in result["requirements"] if item["id"] == "C814"), c814)
                self.assertEqual(next(item for item in result["requirements"] if item["id"] == "S8.3-001"), preserved)
                self.assertEqual(generated.render_view(result), entry.render_view(result, entry_specs))
        native = Registry(ROOT)
        native.catalogues = {"8.3": catalogue}
        native.render()
        self.assertEqual(self.registry.catalogues["8.4"], initialization_before)
        self.assertEqual(Registry(ROOT).catalogues["8.4"], initialization_before)
        self.assertEqual(initialization_path.read_bytes(), initialization_bytes)

    def test_exact_twenty_fixture_files_and_source_plan_partition(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("automatic_save_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 20)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        self.assertEqual({spec["facet"] for spec in self.specs.values()}, set(generated.FACETS))
        self.assertEqual(sum(spec["facet"] == "constant-specification-admission" for spec in self.specs.values()), 3)
        self.assertEqual(sum(spec["facet"] == "bare-save-admission" for spec in self.specs.values()), 1)


if __name__ == "__main__":
    unittest.main()
