"""Compile-only inventory, interaction countermodels, minimal repairs and causal guards."""
import copy
import itertools
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_type_specifier_fixtures as generated
import generate_derived_parameter_fixtures as parameters

CONTROLS = {
    "R754": "bare_nonparameterized bare_defaulted positional keywords mixed",
    "R755": "keyword_repair",
    "C795": "local_type_repair public_provider_repair",
    "C796": "nonparameterized_repair",
    "C797": "required_keywords_repair required_mixed_repair",
    "C798": "keyword_then_positional_repair positional_keyword_positional_repair",
    "C799": "keyword_repair",
    "C7100": "associate_guard dummy_allocation local_explicit_length_repair",
}
NEGATIVES = {
    "R754": "empty_list missing_separator",
    "R755": "arrow empty_keyword empty_value",
    "C795": "ordinary_object private_type",
    "C796": "nonparameterized_list",
    "C797": "missing_kind missing_length duplicate_keyword positional_keyword_duplicate",
    "C798": "keyword_then_positional positional_keyword_positional",
    "C799": "unknown_keyword component_keyword",
    "C7100": "local_assumed_length",
}
WRONG_CAUSES = {
    "R754": [
        "Argument list of procedure 'record' must not be empty",
        "Missing comma in the actual argument list of 'record'",
        "Expected ')' in a type declaration",
        "Type parameter 'k' of 'record' must be a constant expression"],
    "R755": [
        "Expected '=' after actual argument keyword 'n'",
        "Pointer component initialization 'n' requires '=>'",
        "Expected a value in the expression",
        "Type parameter keyword 'other' uses '=' rather than '=>'",
        "Missing type parameter keyword in derived type specifier 'different'"],
    "C795": [
        "Object 'scalar_name' has no explicit type",
        "PRIVATE component 'hidden' is inaccessible in this scope",
        "Procedure 'hidden' has not been declared",
        "Derived type 'different' is not declared",
        "Derived type 'hidden' has an incompatible KIND parameter",
        "Derived type `different` is not defined",
        "'scalar_name' is an abstract derived type"],
    "C796": [
        "Derived type 'record' requires a value for type parameter 'k'",
        "Derived type 'other' has no type parameters",
        "Procedure 'record' has no formal parameters",
        "Kind parameter of 'record' is invalid",
        "Type 'different' is not parameterized and so the type parameter spec list at (1) may not appear"],
    "C797": [
        "Type parameter 'n' must be a constant expression",
        "Keyword argument 'n' was supplied twice to procedure 'record'",
        "Type parameter specification without a keyword follows one with a keyword",
        "The type parameter spec list contains too many parameter expressions",
        "Type parameter 'other' was already specified",
        "Component 'n' was declared more than once",
        "Multiple values given for argument 'n'",
        "Multiple values given for type parameter 'other'",
        "Type parameter 'k' lacks a constant value"],
    "C798": [
        "Type parameter 'a' was already specified",
        "No value was provided for type parameter 'n'",
        "A positional actual argument may not follow a keyword argument",
        "Missing keyword name in actual argument list",
        "A component value must have a keyword after a component keyword",
        "Positional argument after keyword argument in procedure 'record'",
        "Positional argument after keyword argument in parameterized derived type 'different'"],
    "C799": [
        "Keyword argument 'nn' is not in the procedure interface",
        "Structure constructor component keyword 'payload' was repeated",
        "Type parameter inquiry of 'payload' is not allowed",
        "Unknown type parameter keyword 'nn' for derived type 'different'",
        "Type parameter keyword 'other' is not a parameter of derived type 'record'",
        "'nn' is not the name of a component for derived type 'record'",
        "'payload' is not the name of a parameter for derived type 'different'"],
    "C7100": [
        "Assumed-length CHARACTER variable 'value' must be a dummy argument",
        "KIND parameter 'n' must be a constant expression",
        "The deferred LEN parameter of an unallocated object cannot be inquired about",
        "Assumed-type TYPE(*) is not allowed in this context",
        "The derived parameter 'n' at (1) does not have a default value",
        "The object 'different' at (1) with ASSUMED type parameters must be a dummy or a SELECT TYPE selector"],
}
UNCORROBORATED_NATIVE = {
    "R754": ["Token '::' is unexpected here", "Token 'n' (of type 'identifier') is unexpected here",
             "F2023 R755: The empty type specification at (1) is not allowed",
             "Syntax error in argument list at (1)", "expected ')'"],
    "R755": ["Token '=>' is unexpected here", "Token '=' is unexpected here", "Token ')' is unexpected here",
             "Syntax error in argument list at (1)", "expected ')'"],
    "C796": ["Too many type parameters given for derived type 'record'"],
    "C797": ["Keyword 'n' at (1) has already appeared in the current argument list"],
    "C798": ["Missing keyword name in actual argument list at (1)", "Type parameter value must have a name"],
    "C7100": ["An assumed (*) type parameter may be used only for a (non-statement function) dummy argument, "
              "associate name, character named constant, or external function result"],
}


class TypeSpecifierFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if "/fixtures/type_specifier_" in case.path}
        cls.catalogue = cls.registry.catalogues["7.5.9"]

    def name(self, rule, variant, invalid=False):
        return generated.identifier(rule, variant, invalid)

    def source(self, rule, variant, invalid=False, file="source.f90"):
        return (self.cases[self.name(rule, variant, invalid)].fixture.root / file).read_text()

    def judge(self, name, message, family="lfortran", code=1, line=None, file=None,
              severity=None, echo=False, timed_out=False, without_exclusions=False, trailer=""):
        predicate = self.cases[name].fixture.expectation.diagnostic
        if without_exclusions:
            predicate = dict(predicate, excludes_any=[])
        line = predicate["line"] if line is None else line
        file = predicate["file"] if file is None else file
        point = f"{line}-{line}:1-100" if family == "lfortran" else f"{line}:1"
        severity = severity or ("semantic error" if family == "lfortran" else "error")
        output = f"{file}:{point}: {severity}: {'unrelated failure' if echo else message}\n"
        if echo:
            output += "  1 | " + message + "\n"
        output += trailer
        return runner.judge_diagnostic(
            runner.ProcessResult(code, output, timed_out=timed_out),
            runner.Compiler(family, family, "f23" if family == "lfortran" else
                            "f2018" if family == "flang" else "f2023"),
            self.cases[name].rule, predicate).outcome

    def test_exact_case_ids_compile_phases_roles_and_no_runtime_or_policy(self):
        expected = {self.name(rule, variant): "valid"
                    for rule, variants in CONTROLS.items() for variant in variants.split()}
        expected.update({self.name(rule, variant, True): "invalid"
                         for rule, variants in NEGATIVES.items() for variant in variants.split()})
        self.assertEqual(len(expected), 34)
        self.assertEqual(set(self.specs), set(expected))
        self.assertEqual(set(self.cases), set(expected))
        self.assertEqual(len(self.repairs), 17)
        self.assertEqual(set(NEGATIVES), set(generated.ELIGIBLE))
        for name, kind in expected.items():
            case = self.cases[name]
            manifest = json.loads(Path(case.path).read_text())
            with self.subTest(case=name):
                self.assertEqual(case.kind, kind)
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.meta.evidence, "effect" if kind == "invalid" else "positive-control")
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertFalse(case.meta.profiles)
                self.assertFalse(case.meta.coarray)
                self.assertEqual(case.meta.images, 1)
                self.assertIsNone(case.fixture.link)
                self.assertNotIn("run", manifest)
                self.assertNotIn("requires", manifest)
                self.assertNotIn("oracle_profile", manifest)
                self.assertFalse(case.rule.startswith("S"))
                self.assertEqual(manifest["expect"]["outcome"], "diagnose" if kind == "invalid" else "success")

    def test_exact_scoped_generated_inputs(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("type_specifier_*/*") if p.is_file()}
        self.assertEqual(set(self.outputs), actual)
        self.assertEqual(len(actual), 70)
        for path, raw in self.outputs.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            self.assertTrue(raw.endswith(b"\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_all_negatives_have_exact_same_primary_source_minimal_repairs(self):
        self.assertEqual(set(self.repairs), {name for name, case in self.cases.items() if case.kind == "invalid"})
        for name, repair in self.repairs.items():
            bad_case, good_case = self.cases[name], self.cases[repair["control"]]
            bad = {f: (bad_case.fixture.root / f).read_text() for f in bad_case.fixture.files}
            good = {f: (good_case.fixture.root / f).read_text() for f in good_case.fixture.files}
            with self.subTest(case=name):
                self.assertEqual(bad.keys(), good.keys())
                self.assertEqual([f for f in bad if bad[f] != good[f]], [repair["file"]])
                self.assertEqual(bad[repair["file"]].count(repair["wrong"]), 1)
                self.assertEqual(bad[repair["file"]].replace(repair["wrong"], repair["repaired"], 1), good[repair["file"]])
                self.assertEqual(bad_case.rule, good_case.rule)
                self.assertEqual(good_case.kind, "valid")
                self.assertEqual(good_case.meta.evidence, "positive-control")
                predicate = bad_case.fixture.expectation.diagnostic
                self.assertEqual((predicate["file"], predicate["line"]), (repair["anchor_file"], repair["line"]))
                self.assertTrue(bad[repair["anchor_file"]].splitlines()[repair["line"]-1].startswith("type("))
        keyword_control = self.name("R755", "keyword_repair")
        self.assertEqual(sum(r["control"] == keyword_control for r in self.repairs.values()), 3)
        required_control = self.name("C797", "required_keywords_repair")
        self.assertEqual(sum(r["control"] == required_control for r in self.repairs.values()), 3)
        self.assertEqual(self.specs[self.name("C7100", "dummy_allocation")]["facets"],
                         ["dummy-declaration", "dummy-allocation"])

    def test_source_scenarios_match_actual_typedefs_and_specifier_roles(self):
        for name, spec in self.specs.items():
            plan = spec["plan"]
            case = self.cases[name]
            inputs = {f: (case.fixture.root / f).read_text() for f in case.fixture.files}
            text = "\n".join(inputs.values())
            with self.subTest(case=name):
                self.assertIn(generated.specifier(plan), text)
                expected = [] if spec["kind"] == "valid" else [case.rule]
                self.assertEqual(generated.model(plan)["issues"], expected)
                if expected:
                    self.assertIsNone(generated.model(plan)["mapping"])
                for formal in plan["formals"]:
                    declaration = f"integer, {formal['category']} :: {formal['name']}"
                    if formal["default"] is not None:
                        declaration += "=" + str(formal["default"])
                    self.assertIn(declaration + "\n", text)
                self.assertNotRegex(text, r"(?i)\binteger\s*\(\s*(?:k|a|b|c|d)\s*\)")
                self.assertNotRegex(text, r"(?i)\b(?:real|logical|complex)\s*\(")
                self.assertNotRegex(text, r"(?im)^\s*program\b")
                self.assertNotRegex(text, r"(?im)^value\s*=\s*record")
                if case.kind == "invalid":
                    self.assertNotIn("allocate(", text)
                    self.assertNotRegex(text, r"(?im)^\s*(?:\w+\s+)?function\b")

    def test_empty_list_and_missing_separator_do_not_depend_on_other_failures(self):
        empty = self.specs[self.name("R754", "empty_list", True)]["plan"]
        self.assertTrue(empty["formals"])
        self.assertTrue(all(f["default"] is not None for f in empty["formals"]))
        self.assertEqual(generated.model(empty), {"issues": ["R754"], "mapping": None})
        nonpdt = self.specs[self.name("C796", "nonparameterized_list", True)]["plan"]
        self.assertFalse(nonpdt["formals"])
        self.assertEqual(nonpdt["entries"], [generated.entry(None, 3)])
        self.assertEqual(generated.model(nonpdt)["issues"], ["C796"])
        text = self.source("R754", "missing_separator", True)
        self.assertIn("record(k=(5) n=11)", text)
        self.assertNotIn("record(5 11)", text)
        for variant in ("arrow", "empty_keyword", "empty_value"):
            plan = self.specs[self.name("R755", variant, True)]["plan"]
            self.assertTrue(all(f["default"] is not None for f in plan["formals"]))
            self.assertEqual(generated.model(plan)["issues"], ["R755"])

    def test_C795_type_category_and_private_provider_are_isolated(self):
        text = self.source("C795", "ordinary_object", True)
        self.assertIn("integer :: scalar_name\n", text)
        self.assertIn("type(scalar_name) :: value", text)
        self.assertNotRegex(text, r"(?i)type\s*\(\s*(?:integer|real|logical|complex|character|enum|enumeration)\s*\)")
        for category in ("intrinsic", "enum", "enumeration"):
            with self.assertRaisesRegex(ValueError, "R703 alternatives"):
                generated.model(generated.scenario(listed=False, symbol_kind=category))
        bad = self.cases[self.name("C795", "private_type", True)]
        good = self.cases[self.name("C795", "public_provider_repair")]
        self.assertEqual([s.id for s in bad.fixture.build], ["provider", "client"])
        self.assertEqual(bad.fixture.build[1].depends_on, ["provider"])
        self.assertEqual(bad.fixture.expectation.step, "client")
        self.assertEqual((bad.fixture.root / "client.f90").read_bytes(), (good.fixture.root / "client.f90").read_bytes())
        self.assertIn("use specifier_provider\n", (bad.fixture.root / "client.f90").read_text())
        self.assertNotIn("only", (bad.fixture.root / "client.f90").read_text().lower())
        self.assertEqual((bad.fixture.root / "provider.f90").read_text().replace("type, private", "type, public"),
                         (good.fixture.root / "provider.f90").read_text())

    def test_C797_duplicates_are_not_argument_count_or_order_counterexamples(self):
        for variant, formal in (("duplicate_keyword", "n"), ("positional_keyword_duplicate", "k")):
            plan = self.specs[self.name("C797", variant, True)]["plan"]
            self.assertEqual(len(plan["formals"]), 3)
            self.assertEqual(len(plan["entries"]), 3)
            self.assertTrue(all(e["keyword"] is None or e["keyword"] in {"k", "n", "pad"} for e in plan["entries"]))
            self.assertEqual(generated.model(plan)["issues"], ["C797"])
            self.assertIsNone(generated.model(plan)["mapping"])
            keys = [e["keyword"] if e["keyword"] is not None else "k" for e in plan["entries"]]
            self.assertEqual(keys.count(formal), 2)
        for variant in ("missing_kind", "missing_length"):
            plan = self.specs[self.name("C797", variant, True)]["plan"]
            self.assertTrue(all(e["keyword"] is not None for e in plan["entries"]))
        for variant in ("required_keywords_repair", "required_mixed_repair"):
            plan = self.specs[self.name("C797", variant)]["plan"]
            self.assertEqual(generated.model(plan)["mapping"], {"k": 7, "n": 3, "pad": 5})

    def test_C798_exhaustive_order_masks_and_only_valid_repair_mappings(self):
        for count, accepted in ((3, 4), (4, 5)):
            formals = [generated.formal(chr(97+i), "kind", i+1) for i in range(count)]
            good_count = 0
            for mask in itertools.product((False, True), repeat=count):
                values = [generated.entry(chr(97+i) if named else None, 11+i) for i, named in enumerate(mask)]
                result = generated.model(generated.scenario(formals, values))
                independently_valid = not any(mask[i] and not mask[j] for i in range(count) for j in range(i+1, count))
                self.assertEqual(result["issues"], [] if independently_valid else ["C798"])
                self.assertEqual(result["mapping"] is not None, independently_valid)
                good_count += independently_valid
            self.assertEqual(good_count, accepted)
        expected = {
            "keyword_then_positional": {"a": 11, "b": 2, "c": 31},
            "positional_keyword_positional": {"a": 11, "b": 22, "c": 3, "d": 44},
        }
        for variant, mapping in expected.items():
            bad = self.specs[self.name("C798", variant, True)]["plan"]
            good = self.specs[self.name("C798", variant + "_repair")]["plan"]
            self.assertTrue(all(f["category"] == "kind" and f["default"] is not None for f in bad["formals"]))
            self.assertIsNone(generated.model(bad)["mapping"])
            self.assertEqual(generated.model(good)["mapping"], mapping)

    def test_keyword_membership_and_scalar_integer_value_countermodels(self):
        for variant, keyword in (("unknown_keyword", "nn"), ("component_keyword", "payload")):
            plan = self.specs[self.name("C799", variant, True)]["plan"]
            self.assertTrue(all(f["default"] is not None for f in plan["formals"]))
            self.assertEqual(plan["entries"], [generated.entry(keyword, 3)])
            self.assertEqual(generated.model(plan)["issues"], ["C799"])
            self.assertIn("integer :: payload", self.source("C799", variant, True))
        positive = self.specs[self.name("R755", "keyword_repair")]["plan"]
        for invalid in (1.5, True, [3, 4]):
            plan = copy.deepcopy(positive)
            plan["entries"][0]["value"] = invalid
            self.assertIn("R701", generated.model(plan)["issues"])
        kind = generated.scenario([generated.formal("k", "kind")], [generated.entry("k", "*")], context="dummy")
        self.assertEqual(generated.model(kind)["issues"], ["C701"])

    def allocation_from_source(self, source):
        declarations = re.findall(
            r"(?m)^type\(record\(k=(\d+),n=(\*|:|\d+)\)\), allocatable(?:, intent\(inout\))? :: (item|actual)$", source)
        self.assertEqual(len(declarations), 2)
        settings = {}
        for kind, length, name in declarations:
            settings[name] = dict(type="record", polymorphic=False, rank=0, kinds={"k": int(kind)},
                                  deferred=["n"] if length == ":" else [], allocatable=True,
                                  lengths={"n": int(length) if length.isdigit() else length})
        allocation = re.search(r"(?m)^allocate\(record\(k=(\d+),n=(\*|:|\d+)\) :: item,stat=status\)$", source)
        self.assertIsNotNone(allocation)
        values = {"k": int(allocation[1]), "n": int(allocation[2]) if allocation[2].isdigit() else allocation[2]}
        objects = [dict(name="item", dummy=True, assumed=["n"] if settings["item"]["lengths"]["n"] == "*" else [])]
        return settings["item"], settings["actual"], values, objects

    def test_C7100_actual_source_has_complete_declaration_guard_and_allocation_premises(self):
        source = self.source("C7100", "dummy_allocation")
        dummy, actual, values, objects = self.allocation_from_source(source)
        plan = self.specs[self.name("C7100", "dummy_allocation")]["plan"]
        self.assertEqual(dummy, plan["dummy"])
        self.assertEqual(actual, plan["actual"])
        self.assertEqual(values, {"k": 7, "n": "*"})
        self.assertEqual(objects, [dict(name="item", dummy=True, assumed=["n"])])
        self.assertEqual(generated.allocation_model(dummy, actual, values, objects), [])
        self.assertIn("if (.not.allocated(item)) then\nallocate(", source)
        self.assertIn("if (status/=0) error stop 1\nend if\nitem%payload=0", source)
        self.assertNotRegex(source.lower(), r"\b(?:source|mold)\s*=")
        self.assertNotRegex(source, r"\b(?:item|actual)%n\b")
        self.assertIn("subroutine allocate_dummy(item)", source)
        self.assertIn("call allocate_dummy(actual)", source)
        guard = self.source("C7100", "associate_guard")
        self.assertIn("class(record(k=7,n=*)), intent(in) :: item", guard)
        self.assertIn("select type(view=>item)\ntype is(record(k=7,n=*))", guard)
        self.assertEqual(guard.count("type is("), 1)
        self.assertNotRegex(guard.lower(), r"\b(?:optional|pointer|allocatable|abstract|sequence|bind)\b")
        self.assertNotRegex(guard.lower(), r"(?m)^associate\s*\(")
        self.assertIn("type(record(k=7,n=5)) :: actual\nactual%payload=0\ncall select_record(actual)", guard)
        bad = self.source("C7100", "local_assumed_length", True)
        self.assertIn("subroutine local_context()\ntype(record(k=7,n=*)) :: value", bad)
        self.assertNotRegex(bad.lower(), r"\b(?:function|allocate|parameter)\b")

    def test_C7100_deferred_set_and_C939_iff_countermodels(self):
        source = self.source("C7100", "dummy_allocation")
        dummy, actual, values, objects = self.allocation_from_source(source)
        for key, changed, expected in [
            ("type", "other", "15.5.2.6p2"), ("polymorphic", True, "15.5.2.6p2"),
            ("rank", 1, "15.5.2.6p3"), ("kinds", {"k": 9}, "15.5.2.6p3"),
            ("deferred", ["n"], "15.5.2.6p4"), ("allocatable", False, "15.5.2.7p2"),
        ]:
            altered = dict(actual, **{key: changed})
            self.assertIn(expected, generated.allocation_model(dummy, altered, values, objects))
        for dummy_object, assumed, star in itertools.product((False, True), repeat=3):
            objs = [dict(name="item", dummy=dummy_object, assumed=["n"] if assumed else [])]
            vals = {"k": 7, "n": "*" if star else 5}
            valid_iff = star == (dummy_object and assumed)
            self.assertEqual("C939" not in generated.allocation_model(dummy, actual, vals, objs), valid_iff)
        self.assertIn("C940", generated.allocation_model(dummy, actual, {"k": 9, "n": "*"}, objects))
        self.assertIn("C701", generated.allocation_model(dummy, actual, {"k": "*", "n": "*"}, objects))
        self.assertEqual(generated.allocation_model(dummy, actual, values, []), ["R929"])
        deferred_source = source.replace("record(k=7,n=5)", "record(k=7,n=:)")
        self.assertIn("15.5.2.6p4", generated.allocation_model(*self.allocation_from_source(deferred_source)))
        explicit_allocation = source.replace("allocate(record(k=7,n=*)", "allocate(record(k=7,n=5)")
        self.assertIn("C939", generated.allocation_model(*self.allocation_from_source(explicit_allocation)))

    def test_every_contract_is_a_finite_role_property_route_and_not_fatal_policy(self):
        routes = generated.diagnostic_routes()
        self.assertEqual(set(self.repairs), {self.name(rule, variant, True) for rule, variant in routes})
        for (rule, variant), messages in routes.items():
            name = self.name(rule, variant, True)
            predicate = self.cases[name].fixture.expectation.diagnostic
            self.assertEqual(predicate["contains_any"], messages)
            self.assertEqual(len(messages), len(set(messages)))
            for message in messages:
                self.assertTrue(any(role in message.lower() for role in
                                    ("derived type", "type parameter", "derived parameter")))
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        self.assertEqual(self.judge(name, message, family, code), "pass",
                                         (name, family, code, message))

    def test_wrong_roles_properties_and_generic_recovery_reject_without_blacklists(self):
        self.assertEqual(set(WRONG_CAUSES), set(NEGATIVES))
        for name in self.repairs:
            for message in WRONG_CAUSES[self.cases[name].rule]:
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        with self.subTest(case=name, family=family, message=message, code=code):
                            self.assertEqual(self.judge(name, message, family, code, without_exclusions=True), "fail")

    def test_location_file_and_source_echo_cannot_supply_a_cause(self):
        for name in self.repairs:
            predicate = self.cases[name].fixture.expectation.diagnostic
            message = predicate["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                self.assertEqual(self.judge(name, message, family, line=predicate["line"]+1), "fail")
                self.assertEqual(self.judge(name, message, family, file="wrong.f90"), "fail")
                self.assertEqual(self.judge(name, message, family, echo=True), "fail")

    def test_unqualified_native_recovery_or_broader_contexts_remain_uncorroborated(self):
        for name in self.repairs:
            for message in UNCORROBORATED_NATIVE.get(self.cases[name].rule, []):
                for family in ("lfortran", "gfortran", "flang"):
                    self.assertEqual(self.judge(name, message, family, without_exclusions=True), "fail",
                                     (name, family, message))

    def test_internal_verifier_resource_unsupported_and_timeout_guards(self):
        for name in self.repairs:
            predicate = self.cases[name].fixture.expectation.diagnostic
            message = predicate["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                self.assertEqual(self.judge(name, message, family, timed_out=True), "fail")
                self.assertEqual(self.judge(name, message, family, code=-11), "fail")
                for suffix in (" not implemented", " unsupported", " ASR verify pass error",
                               " internal compiler error", " out of memory"):
                    self.assertEqual(self.judge(name, message + suffix, family), "fail")
                internal = f"{predicate['file']}:{predicate['line']}:1: error: Internal: no symbol found for 'value'\n"
                self.assertEqual(self.judge(name, message, family, trailer=internal), "fail")

    def test_nonfatal_warnings_need_exact_explicit_family_allowances(self):
        for name in self.repairs:
            predicate = self.cases[name].fixture.expectation.diagnostic
            allowances = predicate.get("allow_nonfatal", [])
            for family in ("lfortran", "gfortran", "flang"):
                message = predicate["contains_any"][0]
                allowed = any(a["compiler"] == family and a["severity"] == "warning" and
                              message in a.get("equals_any", []) for a in allowances)
                self.assertEqual(self.judge(name, message, family, code=0, severity="warning"),
                                 "pass" if allowed else "fail")
            for allowance in allowances:
                self.assertEqual(set(allowance), {"compiler", "severity", "equals_any"})
                for message in allowance["equals_any"]:
                    self.assertIn(message, predicate["contains_any"])
                    self.assertEqual(self.judge(name, message, allowance["compiler"], code=0,
                                                severity=allowance["severity"]), "pass")

    def test_all_original_facets_pending_gates_and_both_phase_neutral_views(self):
        self.assertEqual(len(self.catalogue["requirements"]), 11)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 59)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 31)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"] if r["id"].startswith("S")), 15)
        for requirement in self.catalogue["requirements"]:
            covered = set(generated.ELIGIBLE.get(requirement["id"], []))
            self.assertEqual(set(requirement["pending"]), set(requirement["facets"]) - covered)
            self.assertEqual(requirement["diagnostic_obligation"], "not-required" if requirement["id"].startswith("S") else "required")
        self.assertEqual(generated.synced_catalogue(self.catalogue, self.specs), self.catalogue)
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs, self.repairs))
        registry = Registry(ROOT)
        registry.catalogues = {"7.5.9": self.catalogue}
        registry.render()
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split("## Reproduction and remaining gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 31)
        for requirement in self.catalogue["requirements"]:
            for facet, plan in requirement["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed.update(review_state="reviewed", review_rationale="Synthetic in-memory regression, not an approval.")
        registry = Registry(ROOT)
        registry.catalogues["7.5.9"] = reviewed
        reviewed["review_fingerprint"] = registry.catalogue_fingerprint("7.5.9")
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs, self.repairs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs, self.repairs))

    def test_registration_does_not_change_original_case_fingerprints_or_write_their_inputs(self):
        old = Registry(ROOT)
        local_rules = {r["id"] for r in old.catalogues["7.5.9"]["requirements"]}
        del old.catalogues["7.5.9"]
        del old.accounting["7.5.9"]
        old.index["catalogues"].remove(generated.CATALOGUE)
        for rule in local_rules:
            del old.requirements[rule]
            del old.requirement_sections[rule]
        existing = [c for c in self.all_cases if c.rule not in local_rules]
        self.assertGreaterEqual(len(existing), 1849)
        for case in existing:
            self.assertEqual(case.fingerprint(self.registry), case.fingerprint(old), case.name)
            paths = ({case.fixture.root / file for file in case.fixture.files} | {Path(case.path)}
                     if case.fixture else {Path(case.path)})
            self.assertFalse(paths & set(self.outputs), case.name)

    def test_shared_parameter_corpus_remains_byte_exact(self):
        corpus = parameters.build_corpus()
        self.assertEqual((len(corpus.cases), len(corpus.files)), (66, 105))
        self.assertFalse(set(corpus.files) & set(self.outputs))
        for path, content in corpus.files.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
