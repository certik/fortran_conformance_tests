"""Input, semantic-premise and cause regressions for derived definitions."""
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_derived_definition_fixtures as generated


RUN_VARIANTS = {
    "R726": "parameters components binding",
    "R727": "bare colons",
    "R728": "public private extends",
    "C737": "prior_parent renamed_parent host_parent",
    "C738": "concrete_override",
    "C743": "private_roles",
    "R730": "unnamed named",
    "C744": "case_equivalent",
    "S7.5.2.2-001": ("public_public public_private private_public private_private "
                     "component_private binding_private"),
    "S7.5.2.2-002": "module_constructor descendant_constructor",
    "R731": "sequence_statement",
    "C745": "data_types component_kinds",
    "S7.5.2.3-001": "numeric_order nested_order character_order zero_member",
    "S7.5.2.4-001": "local host use_alias parameters",
    "S7.5.2.4-002": ("ordinary_distinct sequence_match bind_match same_name_aliases "
                     "different_names_same_alias component_order component_name component_kind "
                     "component_rank component_attributes sequence_vs_ordinary bind_vs_ordinary "
                     "sequence_vs_bind"),
}
COMPILE_VARIANTS = {
    "R726": "empty empty_binding_part",
    "R728": "abstract bind_c",
    "C734": "subjects",
    "C737": "abstract_parent",
    "C739": "ordinary",
    "C741": "ancestor_presence",
    "C742": "event_parent lock_parent notify_parent event_to_lock lock_to_notify notify_to_event",
    "R729": "private private_sequence sequence_private",
}
PAIR_VARIANTS = {
    "R726": "late_parameter late_component_private component_after_contains",
    "R727": "missing_colons empty_parameter_list",
    "R728": "bind_name parameterized_parent",
    "C734": "integer real complex character logical doubleprecision",
    "C735": "abstract public private bind extends",
    "C736": "kind_name length_name",
    "C737": "nontype_parent forward_parent sequence_parent bind_parent c_ptr c_funptr",
    "C738": "local_deferred inherited_deferred private_inherited",
    "C739": "sequence bind",
    "C740": "child_sequence",
    "C741": "direct nested",
    "C742": "event lock notify",
    "C743": "private sequence",
    "C744": "end_name",
    "C745": ("empty ordinary_component enum_component enumeration_component "
             "kind_parameter length_parameter empty_contains specific_binding"),
    "C1409": "private_derived_name",
    "C1514": "sequence_definition_identity",
}


def identifier(rule, variant, invalid=False):
    return (rule.replace(".", "_").replace("-", "_")
            + ("_invalid__" if invalid else "_valid__") + variant)


class DerivedDefinitionCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in all_cases if (
            case.rule in {*(f"R{i}" for i in range(726, 732)), *(f"C{i}" for i in range(734, 746))}
            or case.rule.startswith(("S7.5.1-", "S7.5.2."))
            or "/fixtures/derived_definition_" in case.path)}
        cls.negatives = {name: case for name, case in cls.cases.items() if case.kind == "invalid"}

    def inputs(self, case):
        if isinstance(case, str):
            case = self.cases[case]
        if case.fixture:
            return {name: (case.fixture.root / name).read_bytes() for name in case.fixture.files}
        return {Path(case.path).name: Path(case.path).read_bytes()}

    def source(self, name, filename=None):
        inputs = self.inputs(name)
        return inputs[filename] if filename else b"\n".join(inputs.values())

    def judge(self, case, message, family="lfortran", code=1, line=None, filename=None,
              end_line=None, suffix="", timed_out=False, echo=False):
        diagnostic = case.fixture.expectation.diagnostic
        line = diagnostic["line"] if line is None else line
        filename = filename or diagnostic["file"]
        if family == "lfortran":
            output = (f"{filename}:{line}-{line if end_line is None else end_line}:1-90: "
                      f"semantic error: {'unrelated failure' if echo else message}\n")
        else:
            output = f"{filename}:{line}:1: error: {'unrelated failure' if echo else message}\n"
        if echo:
            output += "  1 | " + message + "\n"
        output += suffix
        return runner.judge_diagnostic(
            runner.ProcessResult(code, output, timed_out=timed_out),
            runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023"),
            case.rule, diagnostic).outcome

    def test_exact_case_inventory_and_phases(self):
        expected = {}
        for phase, groups in (("run", RUN_VARIANTS), ("compile", COMPILE_VARIANTS)):
            for rule, variants in groups.items():
                for variant in variants.split():
                    expected[identifier(rule, variant)] = phase
        for rule, variants in PAIR_VARIANTS.items():
            for variant in variants.split():
                expected[identifier(rule, variant, True)] = "compile"
                control = ("C1514_valid__sequence_component_name_repair" if rule == "C1514"
                           else identifier(rule, variant + "_repair"))
                expected[control] = "run" if rule == "C1409" else "compile"
        self.assertEqual(len(expected), 165)
        self.assertEqual(set(self.cases), set(expected))
        self.assertEqual(set(self.specs), set(expected))
        self.assertEqual(len(self.negatives), 50)
        self.assertEqual(sum(phase == "run" for phase in expected.values()), 49)
        for name, phase in expected.items():
            case = self.cases[name]
            with self.subTest(case=name):
                actual = case.fixture.expectation.phase if case.fixture else "run"
                self.assertEqual(actual, phase)
                self.assertEqual(self.specs[name]["phase"], phase)
                self.assertEqual(case.meta.standard, "f2023")
                self.assertFalse(case.meta.profiles)
                self.assertEqual(case.meta.coarray, self.specs[name]["coarray"])
        self.assertEqual(sum(case.meta.coarray for case in self.cases.values()), 17)

    def test_generated_files_are_exact_and_confined_to_their_owned_prefixes(self):
        for path, content in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), content)
                relative = path.relative_to(ROOT).as_posix()
                self.assertTrue(relative.startswith(("tests/clause07/", "tests/fixtures/derived_definition_")))
                if path.suffix == ".f90":
                    content.decode("ascii")
                    self.assertTrue(content.endswith(b"\n"))
                    self.assertLessEqual(max(map(len, content.splitlines())), 132)
        paths = {path for path in (ROOT / "tests/fixtures").glob("derived_definition_*/*") if path.is_file()}
        self.assertEqual(paths, {path for path in self.outputs if "/fixtures/" in str(path)})

    def test_every_negative_has_one_exact_minimal_source_transformation(self):
        self.assertEqual(set(self.repairs), set(self.negatives))
        for name, repair in self.repairs.items():
            bad = self.inputs(name)
            good = self.inputs(repair["control"])
            file = repair["file"]
            with self.subTest(case=name):
                self.assertEqual(set(bad), set(good))
                self.assertEqual([p for p in bad if bad[p] != good[p]], [file])
                wrong, replacement = repair["wrong"].encode(), repair["repaired"].encode()
                self.assertEqual(bad[file].count(wrong), 1)
                self.assertEqual(bad[file].replace(wrong, replacement, 1), good[file])
                for other in set(bad) - {file}:
                    self.assertEqual(bad[other], good[other])
                self.assertEqual(self.cases[name].meta.coarray, self.cases[repair["control"]].meta.coarray)
        for name in ("R726_invalid__late_parameter", "R726_invalid__late_component_private",
                     "R726_invalid__component_after_contains"):
            repair = self.repairs[name]
            self.assertEqual(sorted(line.strip() for line in repair["wrong"].splitlines()),
                             sorted(line.strip() for line in repair["repaired"].splitlines()))
        self.assertEqual(self.repairs["C1409_invalid__private_derived_name"]["file"], "provider.f90")
        self.assertEqual(self.repairs["C1514_invalid__sequence_definition_identity"]["file"], "types_b.f90")

    def test_prospective_cause_routes_and_nonfatal_reporting_are_separate_from_observations(self):
        for name, case in self.negatives.items():
            for message in case.fixture.expectation.diagnostic["contains_any"]:
                self.assertTrue(message.strip())
                self.assertNotIn(message.strip().lower(),
                                 {"type", "kind", "constant", "attribute", "ambiguity",
                                  "function", "expected"})
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        with self.subTest(case=name, family=family, code=code, message=message):
                            self.assertEqual(self.judge(case, message, family, code), "pass")

    def test_generic_wrong_causes_never_satisfy_the_contract(self):
        messages = [
            "expected type", "expected attribute", "expected constant expression",
            "Unknown type 'record'", "Duplicate attribute", "Ambiguous interfaces",
            "The generic 'identify' is ambiguous", "Component 'payload' is PRIVATE",
            "Function 'answer' is not implemented", "Invalid character in name",
            "Unexpected end of file", "Expected END TYPE statement",
            "Only Integer literals or expressions which reduce to constant Integer are accepted as kind parameters",
        ]
        for name, case in self.negatives.items():
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    for message in messages:
                        with self.subTest(case=name, family=family, code=code, message=message):
                            self.assertEqual(self.judge(case, message, family, code), "fail")

    def test_type_component_binding_and_parent_subjects_do_not_cross_credit(self):
        pairs = {
            "C735_invalid__private": ["Component 'payload' has duplicate PRIVATE attributes",
                                      "Binding 'answer' has duplicate PRIVATE attributes"],
            "C736_invalid__kind_name": ["Component 'k' is duplicated in derived type 'record'",
                                        "Type parameter value 'k' must be constant"],
            "C738_invalid__inherited_deferred": [
                "Derived-type 'parent' declared at (1) must be ABSTRACT because 'action' is DEFERRED and not overridden",
                "Non-ABSTRACT type 'parent' inherits deferred binding 'action'"],
            "C738_invalid__private_inherited": [
                "Derived-type 'parent' declared at (1) must be ABSTRACT because 'action' is DEFERRED and not overridden",
                "PRIVATE binding 'action' is not accessible in child_module"],
            "C740_invalid__child_sequence": [
                "Parent type 'parent' is not extensible", "Component 'parent' is not a SEQUENCE type"],
            "C741_invalid__direct": [
                "Coarray 'added' must have the ALLOCATABLE attribute",
                "Type 'co_parent' lacks a coarray potential subobject component"],
            "C742_invalid__event": [
                "Named variable 'added' of EVENT_TYPE must be a coarray",
                "The parent lacks a coarray potential subobject component"],
            "C743_invalid__private": [
                "Duplicate PRIVATE attribute in a derived-type-stmt",
                "Duplicate PRIVATE statement in the type-bound procedure part"],
            "C744_invalid__end_name": ["Parent type 'other' is not defined"],
            "C745_invalid__empty_contains": [
                "SEQUENCE type 'record' must have at least one component",
                "Binding 'answer' lacks a passed-object argument"],
            "C1409_invalid__private_derived_name": [
                "Component 'payload' is private in type 'hidden_record'",
                "Module 'provider' is not found"],
            "C1514_invalid__sequence_definition_identity": [
                "Ambiguous interfaces in generic interface 'identify' for 'left_tag' at (1) and 'other_tag' at (2)",
                "Ambiguous interfaces in generic interface 'other' for 'left_tag' at (1) and 'right_tag' at (2)"],
        }
        for name, messages in pairs.items():
            case = self.negatives[name]
            diagnostic = case.fixture.expectation.diagnostic
            for line in range(diagnostic["line"], diagnostic.get("end_line", diagnostic["line"]) + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        for message in messages:
                            with self.subTest(case=name, family=family, line=line, code=code, message=message):
                                self.assertEqual(self.judge(case, message, family, code, line=line), "fail")

    def test_location_implementation_crash_and_verifier_failures_override_words(self):
        for name, case in self.negatives.items():
            diagnostic = case.fixture.expectation.diagnostic
            message = diagnostic["contains_any"][0]
            for kwargs in (
                {"filename": "other.f90"},
                {"line": diagnostic["line"] - 1},
                {"end_line": diagnostic.get("end_line", diagnostic["line"]) + 1},
                {"echo": True},
                {"suffix": "ASR verify pass error\n"},
                {"suffix": "LLVM ERROR: invalid IR\n"},
                {"suffix": "error: out of memory\n"},
                {"code": -11}, {"code": 139}, {"timed_out": True},
            ):
                with self.subTest(case=name, kwargs=kwargs):
                    self.assertEqual(self.judge(case, message, **kwargs), "fail")
            for prefix in ("Not yet implemented: ", "Unsupported feature: ", "Obsolescent feature: "):
                with self.subTest(case=name, prefix=prefix):
                    self.assertEqual(self.judge(case, prefix + message), "fail")

    def test_observed_nonfatal_routes_are_exact_and_family_specific(self):
        count = 0
        for case in self.negatives.values():
            diagnostic = case.fixture.expectation.diagnostic
            for permission in diagnostic.get("allow_nonfatal", []):
                self.assertEqual(permission["compiler"], "flang")
                self.assertEqual(permission["severity"], "warning")
                self.assertEqual(set(permission), {"compiler", "severity", "equals_any"})
                count += 1
                for message in permission["equals_any"]:
                    output = f"{diagnostic['file']}:{diagnostic['line']}:1: warning: {message}\n"
                    for code in (0, 1):
                        for family in ("flang", "gfortran"):
                            check = runner.judge_diagnostic(
                                runner.ProcessResult(code, output),
                                runner.Compiler(family, family, "f2018" if family == "flang" else "f2023"),
                                case.rule, diagnostic)
                            self.assertEqual(check.outcome, "pass" if family == "flang" else "fail")
                    for changed in ("Obsolescent feature: " + message, "Not yet implemented: " + message):
                        output = f"{diagnostic['file']}:{diagnostic['line']}:1: warning: {changed}\n"
                        check = runner.judge_diagnostic(
                            runner.ProcessResult(0, output), runner.Compiler("flang", "flang", "f2018"),
                            case.rule, diagnostic)
                        self.assertEqual(check.outcome, "fail")
        self.assertEqual(count, 7)

    def test_new_observed_routes_do_not_expand_to_wrong_subjects(self):
        examples = {
            "C735_invalid__bind": "Variable 'record': Duplicate BIND attribute specified at (1)",
            "C735_invalid__private": "Component 'payload': Attribute 'PRIVATE' cannot be used more than once [-Wredundant-attribute]",
            "C736_invalid__kind_name": "Dummy argument: Duplicate name 'k' in parameter list at (1)",
            "C736_invalid__length_name": "Type parameter, component, or procedure binding 'n' already defined in this type",
            "C737_invalid__nontype_parent": "Symbol 'selector' at (1) has not been previously defined",
            "C740_invalid__child_sequence": "Component parent of SEQUENCE type declared at (1) does not have the SEQUENCE attribute",
            "C742_invalid__event": "Noncoarray component added at (1) of type EVENT_TYPE or with subcomponent of type EVENT_TYPE must have a codimension or be a subcomponent of a coarray. (Variables of type child may not have a codimension as already a coarray subcomponent exists)",
            "C742_invalid__lock": "Noncoarray component added at (1) of type LOCK_TYPE or with subcomponent of type LOCK_TYPE must have a codimension or be a subcomponent of a coarray. (Variables of type child may not have a codimension as already a coarray subcomponent exists)",
            "C742_invalid__notify": "Type 'child' has an EVENT_TYPE or LOCK_TYPE component, so the type at the base of its type extension chain ('parent') must either have an EVENT_TYPE or LOCK_TYPE component, or be EVENT_TYPE or LOCK_TYPE",
            "C743_invalid__private": "PRIVATE should not appear more than once in derived type bindings [-Wredundant-attribute]",
            "C745_invalid__kind_parameter": "SEQUENCE statement at (1) must precede structure components",
            "C745_invalid__length_parameter": "SEQUENCE statement at (1) must precede structure components",
            "R726_invalid__component_after_contains": "expected 'PROCEDURE'",
            "R727_invalid__empty_parameter_list": "expected end of statement",
            "R727_invalid__missing_colons": "expected '::'",
        }
        for name, message in examples.items():
            case = self.negatives[name]
            diagnostic = case.fixture.expectation.diagnostic
            for line in range(diagnostic["line"], diagnostic.get("end_line", diagnostic["line"]) + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        with self.subTest(case=name, family=family, code=code, line=line):
                            self.assertEqual(self.judge(case, message, family, code, line=line), "fail")

    def test_empty_binding_part_and_procedure_components_are_not_conflated(self):
        empty = self.source("R726_valid__empty_binding_part").lower()
        self.assertIn(b"contains\nend type", empty)
        bad = self.source("C745_invalid__empty_contains").lower()
        self.assertIn(b"integer :: payload", bad)
        self.assertIn(b"contains\nend type", bad)
        procedure = self.source("C745_valid__component_kinds").lower()
        definition = procedure.split(b"type :: record", 1)[1].split(b"end type", 1)[0]
        self.assertNotIn(b"contains", definition)
        self.assertIn(b"procedure(answer_interface), pointer, nopass", definition)
        self.assertIn(b"integer, pointer", definition)
        self.assertIn(b"integer, allocatable", definition)
        self.assertLess(procedure.index(b"value%answer =>"), procedure.index(b"value%answer()"))

    def test_coarray_and_special_type_cases_have_independent_type_only_premises(self):
        for name, case in self.cases.items():
            if case.rule not in ("C741", "C742"):
                continue
            raw = self.source(name).lower()
            with self.subTest(case=name):
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertTrue(case.meta.coarray)
                self.assertNotRegex(raw, rb"\b(?:event\s+post|event\s+wait|notify\s+wait|lock\s*\(|unlock\s*\()")
                self.assertNotIn(b"program p", raw)
        for variant, typename in (("event", "event_type"), ("lock", "lock_type"), ("notify", "notify_type")):
            bad = self.source("C742_invalid__" + variant).decode()
            parent = bad.split("type :: parent", 1)[1].split("end type", 1)[0]
            self.assertIn("integer, allocatable :: co[:]", parent)
            self.assertNotIn("type(" + typename + ")", parent)
            good = self.source("C742_valid__" + variant + "_repair").decode()
            parent = good.split("type :: parent", 1)[1].split("end type", 1)[0]
            self.assertIn("integer, allocatable :: co[:]", parent)
            self.assertIn("type(" + typename + ") :: seed", parent)
        nested = self.source("C741_invalid__nested").lower()
        self.assertIn(b"type(leaf) :: added", nested)
        self.assertNotIn(b"type(leaf), pointer", nested)
        self.assertNotIn(b"type(leaf), allocatable", nested)

    def test_typed_sequence_storage_is_not_representation_punning(self):
        for variant in ("numeric_order", "nested_order", "character_order", "zero_member"):
            raw = self.source("S7_5_2_3_001_valid__" + variant).lower()
            specification = raw.split(b"equivalence(value,flat)", 1)[0]
            with self.subTest(variant=variant):
                self.assertIn(b"sequence", specification)
                self.assertNotRegex(specification, rb"\b(?:pointer|allocatable|target|bind)\b")
                self.assertNotRegex(specification, rb"::[^\n]*=")
                self.assertNotIn(b"use ", specification)
                self.assertNotRegex(raw, rb"\b(?:real|logical|complex|transfer|storage_size|c_sizeof|loc)\b")
                self.assertNotRegex(raw, rb"equivalence\([^)]*\(\s*[^:)]*:")
        numeric = self.source("S7_5_2_3_001_valid__numeric_order")
        self.assertIn(b"integer :: flat(2)", numeric)
        self.assertIn(b"flat(1) /= 11 .or. flat(2) /= 13", numeric)
        nested = self.source("S7_5_2_3_001_valid__nested_order")
        self.assertIn(b"integer :: flat(3)", nested)
        self.assertIn(b"any(flat /= [11,13,17])", nested)
        zero = self.source("S7_5_2_3_001_valid__zero_member")
        self.assertIn(b"character(0) :: empty", zero)
        self.assertIn(b"character(3) :: flat", zero)
        self.assertIn(b"flat(1:1)", zero)
        self.assertIn(b"flat(2:3)", zero)
        self.assertNotIn(b"flat(1:0)", zero)

    def test_accessibility_and_descendant_paths_are_actual_source_contexts(self):
        for variant in ("private_public", "private_private"):
            main = self.source("S7_5_2_2_001_valid__" + variant, "main.f90").lower()
            self.assertNotIn(b"type(record)", main)
            self.assertNotIn(b"only: record", main)
            self.assertIn(b"call initialize()", main)
        pp = self.source("S7_5_2_2_001_valid__component_private", "provider.f90").lower()
        header, binding = pp.split(b"type, public :: record", 1)[1].split(b"end type", 1)[0].split(b"contains")
        self.assertIn(b"private", header)
        self.assertNotIn(b"private", binding)
        bp = self.source("S7_5_2_2_001_valid__binding_private", "provider.f90").lower()
        header, binding = bp.split(b"type, public :: record", 1)[1].split(b"end type", 1)[0].split(b"contains")
        self.assertNotIn(b"private", header)
        self.assertIn(b"private", binding)
        descendant = self.cases["S7_5_2_2_002_valid__descendant_constructor"].fixture
        self.assertEqual([s.source for s in descendant.build], ["root.f90", "first.f90", "second.f90", "main.f90"])
        self.assertIn(b"module subroutine inspect", self.source(descendant.name, "root.f90"))
        self.assertIn(b"submodule(root:first)", self.source(descendant.name, "second.f90"))
        self.assertIn(b"hidden_record(17)", self.source(descendant.name, "second.f90"))

    def test_identity_has_no_nonextensible_inquiry_or_private_sequence_shortcut(self):
        inquiry_cases = set()
        for name, case in self.cases.items():
            raw = self.source(name).lower()
            if b"same_type_as" in raw:
                inquiry_cases.add(name)
                self.assertNotIn(b"sequence", raw)
                self.assertNotIn(b"bind(c)", raw)
            self.assertNotRegex(raw, rb"\b(?:transfer|storage_size|c_sizeof|sizeof|offsetof)\s*\(")
            self.assertNotIn("private-component-interpretation", case.meta.facets)
            self.assertNotIn("companion-member-order", case.meta.facets)
        self.assertEqual(inquiry_cases, {
            "S7_5_2_4_001_valid__local", "S7_5_2_4_001_valid__use_alias",
            "S7_5_2_4_001_valid__parameters", "S7_5_2_4_002_valid__ordinary_distinct",
        })
        pdt = self.source("S7_5_2_4_001_valid__parameters").lower()
        self.assertIn(b"type(record(1,2))", pdt)
        self.assertIn(b"type(record(2,3))", pdt)
        self.assertIn(b"integer :: payload(n)", pdt)
        self.assertNotIn(b"integer(k)", pdt)
        for variant in ("component_rank", "component_attributes", "sequence_vs_bind",
                        "different_names_same_alias"):
            dispatch = self.source("S7_5_2_4_002_valid__" + variant, "dispatch.f90").lower()
            self.assertEqual(dispatch.count(b"type(record), intent(in) :: value"), 2)
            self.assertNotIn(b"optional", dispatch)
            self.assertNotIn(b":: value(", dispatch)

    def test_canonical_pairs_do_not_claim_local_linkage_or_reuse_old_cases(self):
        for name in ("C1409_invalid__private_derived_name", "C1409_valid__private_derived_name_repair",
                     "C1514_invalid__sequence_definition_identity", "C1514_valid__sequence_component_name_repair"):
            case = self.cases[name]
            self.assertEqual(case.meta.facets, [])
            self.assertIn("/fixtures/derived_definition_", case.path)
        bad = self.inputs("C1514_invalid__sequence_definition_identity")
        good = self.inputs("C1514_valid__sequence_component_name_repair")
        self.assertEqual(bad["dispatch.f90"], good["dispatch.f90"])
        self.assertEqual(bad["types_b.f90"].replace(b"integer :: payload", b"integer :: renamed_payload"),
                         good["types_b.f90"])
        self.assertNotIn(b"value%payload", bad["dispatch.f90"])
        self.assertEqual(self.cases["C1409_valid__private_derived_name_repair"].fixture.expectation.phase, "run")

    def test_direct_coverage_partition_is_independent_of_administrative_review_state(self):
        coverage = {}
        for case in self.cases.values():
            coverage.setdefault(case.rule, set()).update(case.meta.facets)
        for section in ("7.5.1", "7.5.2.1", "7.5.2.2", "7.5.2.3", "7.5.2.4"):
            for requirement in self.registry.catalogues[section]["requirements"]:
                self.assertEqual(set(requirement["pending"]),
                                 set(requirement["facets"]) - coverage.get(requirement["id"], set()))


if __name__ == "__main__":
    unittest.main()
