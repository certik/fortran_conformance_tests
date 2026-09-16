"""Exact compile-only FINAL corpus, source-premise and causal-contract checks."""
import copy
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_final_statement_fixtures as generated


ADMISSIONS = {
    "R753": "with_double_colon without_double_colon multiple_names",
    "C791": "module_scalar module_array separate_module assumed_rank elemental",
    "C792": "one_specification",
    "C793": "different_ranks different_kind_values",
    "C794": "sole_assumed_rank different_kind_family",
}
NEGATIVES = {
    "R753": "missing_name_bare missing_name_colons missing_list_separator",
    "C791": ("nonmodule_procedure zero_dummies two_dummies optional_dummy coarray_dummy "
             "pointer_dummy allocatable_dummy polymorphic_dummy different_derived_type "
             "length_n length_m intent_out_dummy value_dummy"),
    "C792": "duplicate_list duplicate_statements case_equivalent",
    "C793": "same_kind_rank full_kind_tuple elemental_scalar_conflict",
    "C794": "plus_scalar plus_vector plus_elemental",
}
PENDING = {
    "R753": {"qualified-name-and-binding-part-use-graph"},
    "C791": {"dummy-kind-and-interface-use-graph"},
    "C792": {"identity-and-same-type-use-graph"},
    "C793": {"signature-consumer-use-graph"},
    "C794": {"assumed-rank-context-graph"},
    "S7.5.6.1-001": {
        "own-final-type-classification", "plain-component-recursion", "pointer-recursion-boundary",
        "allocatable-recursion-boundary", "nonpointer-entity-classification", "pointer-result-and-target-use-graph",
    },
}


def case_id(rule, variant, invalid=False):
    return rule + ("_invalid__" if invalid else "_valid__") + variant


class FinalStatementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if "/fixtures/final_statement_" in case.path}
        cls.negatives = {name: case for name, case in cls.cases.items() if case.kind == "invalid"}

    def inputs(self, name):
        fixture = self.cases[name].fixture
        return {file: (fixture.root / file).read_bytes() for file in fixture.files}

    def source(self, name):
        return b"\n".join(self.inputs(name).values())

    def judge(self, case, message, family="lfortran", code=1, line=None, filename=None,
              end_line=None, suffix="", timeout=False, echo=False):
        diagnostic = case.fixture.expectation.diagnostic
        line = diagnostic["line"] if line is None else line
        filename = filename or diagnostic["file"]
        location = (f"{filename}:{line}-{line if end_line is None else end_line}:1-90: semantic error: "
                    if family == "lfortran" else f"{filename}:{line}:1: error: ")
        output = location + ("unrelated error" if echo else message) + "\n"
        if echo:
            output += "  1 | " + message + "\n"
        result = runner.ProcessResult(code, output + suffix, timed_out=timeout)
        compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023")
        return runner.judge_diagnostic(result, compiler, case.rule, diagnostic).outcome

    def test_exact_case_ids_and_compile_only_metadata(self):
        expected = {case_id(rule, variant) for rule, variants in ADMISSIONS.items()
                    for variant in variants.split()}
        for rule, variants in NEGATIVES.items():
            for variant in variants.split():
                expected.add(case_id(rule, variant, True))
                expected.add(case_id(rule, variant + "_repair"))
        expected.add("C793_valid__full_kind_tuple_first_repair")
        self.assertEqual(len(expected), 64)
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.negatives), 25)
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.profiles, [])
                self.assertEqual(case.meta.images, 1)
                self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
                manifest = json.loads(Path(case.path).read_text())
                self.assertNotIn("link", manifest)
                self.assertNotIn("run", manifest)
                self.assertNotIn("exit_code", manifest["expect"])
                self.assertEqual(case.meta.coarray, name in {
                    "C791_invalid__coarray_dummy", "C791_valid__coarray_dummy_repair"})

    def test_all_generated_bytes_and_paths_are_exact(self):
        self.assertEqual(len(self.outputs), 129)
        actual = {p for p in (ROOT / "tests/fixtures").glob("final_statement_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.outputs))
        for path, raw in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/final_statement_"))
                raw.decode("ascii")
                self.assertTrue(raw.endswith(b"\n"))
                if path.suffix == ".f90":
                    self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_all_negative_controls_change_one_unique_span(self):
        self.assertEqual(set(self.repairs), set(self.negatives))
        self.assertEqual(sum(map(len, self.repairs.values())), 26)
        for name, relations in self.repairs.items():
            bad = self.inputs(name)
            for repair in relations:
                good = self.inputs(repair["control"])
                with self.subTest(case=name, control=repair["control"]):
                    file = repair["file"]
                    wrong, fixed = repair["wrong"].encode(), repair["repaired"].encode()
                    self.assertEqual(set(bad), set(good))
                    self.assertEqual([p for p in bad if bad[p] != good[p]], [file])
                    self.assertEqual(bad[file].count(wrong), 1)
                    self.assertEqual(bad[file].replace(wrong, fixed, 1), good[file])
                    self.assertEqual(self.cases[name].meta.coarray,
                                     self.cases[repair["control"]].meta.coarray)

    def test_empty_bodies_do_not_claim_finalization_execution(self):
        for name in self.cases:
            raw = self.source(name).lower()
            with self.subTest(case=name):
                self.assertNotRegex(raw, rb"(?m)^\s*(program|call|print|read|write|allocate|deallocate|"
                                    rb"nullify|if|do|select|stop|error\s+stop)\b")
                self.assertNotIn(b"is_finalizable", raw)
                self.assertNotIn(b"num_images", raw)
                self.assertNotIn(b"save", raw)
                self.assertRegex(raw, rb"(?m)^final(?:\s|$)")
                self.assertNotIn(b"abstract", raw)
                self.assertNotIn(b"bind(c)", raw)
                self.assertNotRegex(raw, rb"(?m)^\s*integer\s*\([^)]*\)")
                self.assertNotRegex(raw, rb"::[^\n]*=")

    def test_count_repairs_do_not_create_illegal_local_declarations(self):
        bad = self.source("C791_invalid__zero_dummies")
        good = self.source("C791_valid__zero_dummies_repair")
        self.assertIn(b"subroutine finish()\nend subroutine finish", bad)
        self.assertNotIn(b"type(record)", bad)
        self.assertIn(b"subroutine finish(self)\ntype(record), intent(inout) :: self", good)
        bad = self.source("C791_invalid__two_dummies")
        good = self.source("C791_valid__two_dummies_repair")
        self.assertEqual(bad.replace(b"finish(self, spare)", b"finish(self)"), good)
        self.assertIn(b"integer :: spare", bad)
        self.assertNotRegex(good, rb"integer\s*,[^\n]*::\s*spare")

    def test_nonmodule_pair_has_complete_prior_type_interface_and_definitions(self):
        bad = self.source("C791_invalid__nonmodule_procedure")
        good = self.source("C791_valid__nonmodule_procedure_repair")
        self.assertEqual(bad.replace(b"final :: finish_external", b"final :: finish_module"), good)
        self.assertLess(bad.index(b"end type record"), bad.index(b"interface\n"))
        self.assertIn(b"subroutine finish_external(self)\nimport :: record\n"
                      b"type(record), intent(inout) :: self", bad)
        self.assertIn(b"contains\nsubroutine finish_module(self)", bad)
        self.assertIn(b"end module final_defs\nsubroutine finish_external(self)\n"
                      b"use final_defs, only: record", bad)
        self.assertNotIn(b"use ", bad.split(b"end module final_defs")[0])

    def test_separate_module_control_builds_parent_then_submodule(self):
        case = self.cases["C791_valid__separate_module"]
        self.assertEqual([step.source for step in case.fixture.build], ["C791.f90", "implementation.f90"])
        sources = self.inputs(case.name)
        self.assertIn(b"module subroutine finish(self)", sources["C791.f90"])
        self.assertNotIn(b"import", sources["C791.f90"])
        self.assertIn(b"submodule(final_defs) implementation", sources["implementation.f90"])
        self.assertIn(b"module procedure finish", sources["implementation.f90"])

    def test_independent_attribute_and_length_premises(self):
        coarray = self.source("C791_invalid__coarray_dummy")
        self.assertIn(b"type(record), intent(inout) :: self[*]", coarray)
        self.assertNotIn(b"save", coarray)
        self.assertNotIn(b"allocatable", coarray)
        value = self.source("C791_invalid__value_dummy")
        self.assertIn(b"type(record), value, intent(in) :: self", value)
        for word in (b"intent(out)", b"intent(inout)", b"pointer", b"allocatable"):
            self.assertNotIn(word, value)
        for parameter, selector in (("n", b"record(2,*)"), ("m", b"record(*,3)")):
            raw = self.source("C791_invalid__length_" + parameter)
            self.assertIn(b"integer, len :: n,m", raw)
            self.assertIn(b"type(" + selector + b"), intent(inout) :: self", raw)
            self.assertEqual(raw.count(b"final :: finish\n"), 1)
            self.assertNotIn(b"integer, kind", raw)
        for name, case in self.cases.items():
            if case.kind == "valid":
                self.assertNotIn(b"class(record)", self.source(name))

    def test_duplicate_statement_repair_removes_the_whole_statement(self):
        bad = self.source("C792_invalid__duplicate_statements")
        good = self.source("C792_valid__duplicate_statements_repair")
        self.assertEqual(bad.count(b"final :: finish"), 2)
        self.assertEqual(good.count(b"final :: finish"), 1)
        self.assertNotRegex(good, rb"(?m)^\s*final\s*(?:::\s*)?$")
        self.assertEqual(bad.replace(b"final :: finish ! repeated occurrence\n", b""), good)

    def test_kind_tuple_and_elemental_signature_repairs_preserve_other_properties(self):
        bad = self.source("C793_invalid__full_kind_tuple")
        first = self.source("C793_valid__full_kind_tuple_first_repair")
        second = self.source("C793_valid__full_kind_tuple_repair")
        self.assertIn(b"integer, kind :: k1,k2", bad)
        self.assertIn(b"type(record(2,2,*)), intent(inout) :: second", first)
        self.assertIn(b"type(record(1,3,*)), intent(inout) :: second", second)
        for raw in (bad, first, second):
            self.assertIn(b"type(record(1,2,*)), intent(inout) :: first", raw)
            self.assertNotRegex(raw, rb"integer\s*\([^)]*\)")
        bad = self.source("C793_invalid__elemental_scalar_conflict")
        good = self.source("C793_valid__elemental_scalar_conflict_repair")
        self.assertEqual(bad.replace(b":: ordinary\n", b":: ordinary(:)\n"), good)
        self.assertIn(b"impure elemental subroutine finish_elemental(element)\n"
                      b"type(record), intent(inout) :: element\n", good)

    def test_assumed_rank_exclusivity_is_not_runtime_precedence(self):
        for variant in ("plus_scalar", "plus_vector", "plus_elemental"):
            bad = self.source("C794_invalid__" + variant)
            good = self.source("C794_valid__" + variant + "_repair")
            with self.subTest(variant=variant):
                self.assertIn(b"type(record), intent(inout) :: any_rank(..)", bad)
                self.assertEqual(bad.replace(b"final :: finish_fixed\n", b""), good)
                self.assertIn(b"subroutine finish_fixed(fixed)", good)
                self.assertNotRegex(good, rb"(?m)^\s*final\s*(?:::\s*)?$")
        for name in self.cases:
            raw = self.source(name).lower()
            for match in re.finditer(rb"(?m)^(.*)subroutine (\w+)\((\w+)\)\n([^\n]*)", raw):
                if b"elemental" in match.group(1):
                    self.assertIn(b"impure elemental", match.group(1))
                    self.assertIn(b"intent(inout)", match.group(4))
                    self.assertNotIn(match.group(3) + b"(", match.group(4))

    def test_precise_prospective_routes_do_not_imply_native_observations(self):
        for name, case in self.negatives.items():
            for message in case.fixture.expectation.diagnostic["contains_any"]:
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        with self.subTest(case=name, message=message, family=family, code=code):
                            self.assertEqual(self.judge(case, message, family, code), "pass")

    def test_unsupported_wrappers_fail_without_losing_unwrapped_causes(self):
        positives = wrappers = 0
        for name, case in self.negatives.items():
            message = case.fixture.expectation.diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    self.assertEqual(self.judge(case, message, family, code), "pass")
                    positives += 1
                    for prefix in ("Unsupported: ", "This feature is unsupported by this compiler: "):
                        with self.subTest(case=name, family=family, code=code, prefix=prefix):
                            self.assertEqual(self.judge(case, prefix + message, family, code), "fail")
                            wrappers += 1
        self.assertEqual(positives, 150)
        self.assertEqual(wrappers, 300)

    def test_wrong_subject_property_and_generic_recovery_do_not_count(self):
        common = ["expected type", "expected function", "Expected END TYPE statement",
                  "A type parameter must be constant", "Type 'record' is not found",
                  "Cannot open module file 'final_defs.mod'", "Ambiguous interfaces",
                  "Final subroutine 'unrelated' must have exactly one dummy argument"]
        special = {
            "C791_invalid__nonmodule_procedure": ["Final subroutine 'finish_module' must be a module procedure"],
            "C791_invalid__optional_dummy": ["Dummy argument 'self' of final subroutine 'finish' must not be POINTER"],
            "C791_invalid__polymorphic_dummy": ["Passed-object dummy 'self' must be polymorphic"],
            "C791_invalid__length_n": ["Length parameter 'm' of final dummy 'self' in 'finish' must be assumed"],
            "C791_invalid__length_m": ["Length parameter 'n' of final dummy 'self' in 'finish' must be assumed"],
            "C791_invalid__value_dummy": ["VALUE dummy argument cannot have INTENT(INOUT)"],
            "C792_invalid__duplicate_list": ["Final subroutines 'first' and 'second' have the same rank"],
            "C793_invalid__same_kind_rank": ["Final subroutine 'finish_first' is already specified for type 'record'"],
            "C793_invalid__elemental_scalar_conflict": ["Elemental dummy 'element' must be scalar"],
            "C794_invalid__plus_vector": ["Final subroutines 'finish_any' and 'finish_fixed' have the same rank"],
        }
        for name, case in self.negatives.items():
            diagnostic = case.fixture.expectation.diagnostic
            for line in range(diagnostic["line"], diagnostic.get("end_line", diagnostic["line"]) + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        for message in common + special.get(name, []):
                            with self.subTest(case=name, line=line, family=family, code=code, message=message):
                                self.assertEqual(self.judge(case, message, family, code, line=line), "fail")

    def test_wrong_files_echo_internal_verifier_resource_and_timeout_fail(self):
        for name, case in self.negatives.items():
            diagnostic = case.fixture.expectation.diagnostic
            message = diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    for kwargs in (
                        {"filename": "other.f90"}, {"line": diagnostic["line"] - 1},
                        {"line": diagnostic.get("end_line", diagnostic["line"]) + 1}, {"echo": True},
                        {"timeout": True}, {"suffix": "ASR verify pass error\n"},
                        {"suffix": "LLVM ERROR: invalid IR\n"}, {"suffix": "error: out of memory\n"},
                        {"suffix": "error: Internal: no symbol found for 'self'\n"},
                    ):
                        with self.subTest(case=name, family=family, code=code, kwargs=kwargs):
                            self.assertEqual(self.judge(case, message, family, code, **kwargs), "fail")
                for code in (-11, 139):
                    self.assertEqual(self.judge(case, message, family, code), "fail")
            self.assertEqual(self.judge(case, message,
                                       end_line=diagnostic.get("end_line", diagnostic["line"]) + 1), "fail")

    def test_native_routes_do_not_credit_recovery_or_other_signature_properties(self):
        examples = {
            "C791_invalid__polymorphic_dummy": [
                "Argument of FINAL procedure at (1) must be of type 'record'"],
            "C791_invalid__length_n": [
                "FINAL subroutine 'finish' of derived type 'record' must have a dummy argument with an assumed LEN type parameter 'm=*'",
                "Argument of FINAL procedure at (1) must be of type 'record'"],
            "C791_invalid__length_m": [
                "FINAL subroutine 'finish' of derived type 'record' must have a dummy argument with an assumed LEN type parameter 'n=*'"],
            "C791_invalid__two_dummies": [
                "Final procedure 'finish' of 'record' must take exactly one argument, not 0"],
            "C791_invalid__zero_dummies": [
                "Final procedure 'finish' of 'record' must take exactly one argument, not 2"],
            "C792_invalid__duplicate_list": [
                "FINAL procedure 'finish' at (1) is not a SUBROUTINE"],
            "C792_invalid__case_equivalent": [
                "FINAL procedure 'finish' at (1) is not a SUBROUTINE"],
            "C793_invalid__full_kind_tuple": [
                "FINAL procedure 'finish_second' declared at (1) has the same rank (0) as 'finish_first'"],
            "C793_invalid__same_kind_rank": [
                "FINAL procedure at (1) with assumed rank argument must be the only finalizer with the same kind/type"],
            "C794_invalid__plus_scalar": [
                "FINAL subroutines 'finish_fixed' and 'finish_any' of derived type 'record' cannot be distinguished by rank or KIND type parameter value"],
            "C794_invalid__plus_vector": [
                "FINAL subroutines 'finish_fixed' and 'finish_any' of derived type 'record' cannot be distinguished by rank or KIND type parameter value"],
            "C794_invalid__plus_elemental": [
                "FINAL subroutines 'finish_fixed' and 'finish_any' of derived type 'record' cannot be distinguished by rank or KIND type parameter value"],
        }
        for name, messages in examples.items():
            case = self.negatives[name]
            diagnostic = case.fixture.expectation.diagnostic
            for line in range(diagnostic["line"], diagnostic.get("end_line", diagnostic["line"]) + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        for message in messages:
                            with self.subTest(case=name, line=line, family=family, code=code, message=message):
                                self.assertEqual(self.judge(case, message, family, code, line=line), "fail")

    def test_verifier_signature_reports_are_not_final_language_diagnostics(self):
        for variant, count in (("zero_dummies", 0), ("two_dummies", 2)):
            case = self.negatives["C791_invalid__" + variant]
            diagnostic = case.fixture.expectation.diagnostic
            for code in (0, 1):
                output = (f"{diagnostic['file']}:{diagnostic['line']}-{diagnostic['line']}:1-90: "
                          "ASR verify pass error [asr.verify.struct.final_procedure_signature]: "
                          f"Final procedure 'finish' of 'record' must take exactly one argument, not {count}\n")
                result = runner.judge_diagnostic(
                    runner.ProcessResult(code, output), runner.Compiler("lfortran", "lfortran", "f23"),
                    case.rule, diagnostic)
                self.assertEqual(result.outcome, "fail")
                self.assertIn("ASR verification", result.note)

    def test_all_pending_plans_and_administrative_fields_survive_rendering(self):
        catalogue = self.registry.catalogues["7.5.6.1"]
        self.assertEqual(sum(len(req["facets"]) for req in catalogue["requirements"]), 48)
        self.assertEqual({req["id"]: set(req["pending"]) for req in catalogue["requirements"]}, PENDING)
        self.assertFalse(any(spec["rule"].startswith("S") for spec in self.specs.values()))
        appendix = generated.pending_appendix(catalogue)
        for requirement in catalogue["requirements"]:
            for facet, plan in requirement["pending"].items():
                self.assertIn(f"* **`{facet}`**: {plan}\n", appendix)
        self.assertTrue((ROOT / generated.VIEW).read_text().find(appendix) >= 0)
        example = copy.deepcopy(catalogue)
        example.update(review_state="reviewed", review_fingerprint="0" * 64,
                       review_rationale="synthetic administrative-state preservation check")
        updated = generated.synced_catalogue(example, self.specs)
        for key in ("review_state", "review_fingerprint", "review_rationale"):
            self.assertEqual(updated[key], example[key])
        self.assertEqual(generated.catalogue_review_status(updated), "stale")
        self.assertIn("Catalogue source review: stale", generated.render_view(updated, self.specs))
        self.assertIn("15.9.1", next(q for q in catalogue["requirements"] if q["id"] == "C793")["dependencies"])


if __name__ == "__main__":
    unittest.main()
