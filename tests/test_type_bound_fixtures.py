"""Finite inventory, source premises and diagnostic guards for type-bound bindings."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_type_bound_fixtures as generated
import generate_derived_parameter_fixtures as parameters


PAIRS = {
    "R746": "late_private duplicate_private",
    "R747": "private_list public_statement",
    "C772": "main_private procedure_private submodule_private",
    "R749": "attribute_colons empty_concrete empty_interface",
    "R750": "target_call", "C773": "target_colons",
    "C774": "implicit_external internal_target inaccessible_target",
    "C775": "duplicate_list duplicate_statement",
    "R751": "missing_arrow missing_member",
    "C776": "explicit_access implicit_access",
    "C777": "procedure_member generic_member component_member",
    "C778": "repeated_member duplicate_member inherited_repeat",
    "C779": "operator_nopass assignment_nopass read_formatted read_unformatted write_formatted write_unformatted",
    "R752": "empty_pass pointer_attribute",
    "C783": "duplicate_public duplicate_private duplicate_deferred duplicate_non_overridable duplicate_nopass duplicate_pass duplicate_pass_name",
    "C784": "no_arguments integer_argument", "C785": "missing_pass_name",
    "C786": "bare_conflict named_conflict", "C787": "incompatible_attributes",
    "C788": "missing_deferred missing_interface", "C789": "redefer_concrete",
    "C790": "nonoverridable_override",
    "S7.5.5-007": "explicit_private_client default_private_client private_other_module private_generic private_inherited",
}
ADMISSIONS = {
    "R746": "private_only", "C772": "module_private",
    "R749": "colon declaration_list interface_list", "R750": "explicit_target",
    "C774": "module_target renamed_target external_target", "C775": "target_aliases",
    "R751": "named_generic public_generic", "C776": "access_agreement access_scopes",
    "C777": "local_member forward_member inherited_member", "C778": "distinct_generics",
    "C779": "named_nopass", "C784": "typed_nopass nonfirst_pass", "C785": "first_pass",
    "C786": "separate_choices", "C787": "separate_bindings", "C789": "deferred_override",
    "C790": "inherited_nonoverridable distinct_binding", "S7.5.5-007": "private_descendant",
}
RUNS = {
    "S7.5.5-001": "same_name renamed_target",
    "S7.5.5-003": "concrete_interface deferred_interface",
    "S7.5.5-004": "generic_union forward_generic_union",
    "S7.5.5-005": "public_over_private",
    "S7.5.5-006": "private_type public_generic",
}


class TypeBoundFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in all_cases if "/fixtures/type_bound_" in c.path}
        cls.catalogue = cls.registry.catalogues["7.5.5"]

    def inputs(self, name):
        c = self.cases[name]
        return {f: (c.fixture.root / f).read_bytes() for f in c.fixture.files}

    def source(self, rule, variant, invalid=False):
        return b"\n".join(self.inputs(generated.identifier(rule, variant, invalid)).values()).decode()

    def judge(self, name, message, family="lfortran", code=1, line=None, file=None,
              timed_out=False, echo=False, without_exclusions=False):
        case = self.cases[name]
        predicate = case.fixture.expectation.diagnostic
        if without_exclusions:
            predicate = dict(predicate, excludes_any=[])
        line = predicate["line"] if line is None else line
        file = predicate["file"] if file is None else file
        point = f"{line}-{line}:1-100" if family == "lfortran" else f"{line}:1"
        severity = "semantic error" if family == "lfortran" else "error"
        output = f"{file}:{point}: {severity}: {'unrelated failure' if echo else message}\n"
        if echo:
            output += "  1 | " + message + "\n"
        return runner.judge_diagnostic(
            runner.ProcessResult(code, output, timed_out=timed_out),
            runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023"),
            case.rule, predicate).outcome

    def test_exact_case_ids_and_phase_census(self):
        expected = {}
        for rule, variants in PAIRS.items():
            for variant in variants.split():
                expected[generated.identifier(rule, variant, True)] = ("invalid", "compile", "effect")
                expected[generated.identifier(rule, variant + "_repair")] = ("valid", "compile", "positive-control")
        for phase, groups in [("compile", ADMISSIONS), ("run", RUNS)]:
            for rule, variants in groups.items():
                for variant in variants.split():
                    expected[generated.identifier(rule, variant)] = (
                        "valid", phase, "effect" if phase == "run" else "positive-control")
        self.assertEqual(len(expected), 151)
        self.assertEqual(set(self.cases), set(expected))
        self.assertEqual(set(self.specs), set(expected))
        self.assertEqual(len(self.repairs), 57)
        for name, (kind, phase, evidence) in expected.items():
            c = self.cases[name]
            with self.subTest(case=name):
                self.assertEqual((c.kind, c.fixture.expectation.phase, c.meta.evidence),
                                 (kind, phase, evidence))
                self.assertEqual(c.meta.standard, "f2023")
                self.assertEqual(c.meta.oracle_basis, "standard")
                self.assertFalse(c.meta.profiles)
                self.assertFalse(c.meta.coarray)
                self.assertEqual(c.meta.images, 1)
        self.assertEqual(sum(c.kind == "invalid" for c in self.cases.values()), 57)
        self.assertEqual(sum(c.fixture.expectation.phase == "run" for c in self.cases.values()), 9)

    def test_exact_generated_bytes_and_owned_prefix(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("type_bound_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.outputs))
        self.assertEqual(len(actual), 327)
        for path, content in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), content)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/type_bound_"))
                if path.suffix == ".f90":
                    content.decode("ascii")
                    self.assertTrue(content.endswith(b"\n"))
                    self.assertLessEqual(max(map(len, content.splitlines())), 132)

    def test_every_negative_has_one_source_minimal_conforming_repair(self):
        self.assertEqual(set(self.repairs), {n for n, c in self.cases.items() if c.kind == "invalid"})
        for name, repair in self.repairs.items():
            bad, good = self.inputs(name), self.inputs(repair["control"])
            with self.subTest(case=name):
                self.assertEqual(set(bad), set(good))
                self.assertEqual([p for p in bad if bad[p] != good[p]], [repair["file"]])
                wrong, fixed = repair["wrong"].encode(), repair["repaired"].encode()
                self.assertEqual(bad[repair["file"]].count(wrong), 1)
                self.assertEqual(bad[repair["file"]].replace(wrong, fixed, 1), good[repair["file"]])
                self.assertEqual(self.cases[name].fixture.expectation.outcome, "diagnose")
                self.assertEqual(self.cases[repair["control"]].fixture.expectation.outcome, "success")
                self.assertEqual(self.cases[repair["control"]].meta.evidence, "positive-control")
                manifest = json.loads(Path(self.cases[name].path).read_text())
                self.assertEqual(manifest["expect"]["step"], Path(repair["anchor_file"]).stem)
                for index, step in enumerate(manifest["build"]):
                    self.assertEqual(step["depends_on"], [s["id"] for s in manifest["build"][:index]])

    def test_exact_eligible_coverage_and_pending_graphs(self):
        coverage = {}
        for spec in self.specs.values():
            coverage.setdefault(spec["rule"], set()).update(spec["facets"])
        self.assertEqual(coverage, {k: set(v.split()) for k, v in generated.ELIGIBLE.items()})
        self.assertEqual(sum(map(len, coverage.values())), 90)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 156)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 66)
        for r in self.catalogue["requirements"]:
            self.assertEqual(set(r["pending"]), set(r["facets"]) - coverage.get(r["id"], set()))
        for rule in ["R748", "C780", "C781", "C782", "S7.5.5-002"]:
            self.assertNotIn(rule, coverage)
        self.assertIn("access-alternative-identity-source-question", self.registry.requirements["C783"]["pending"])
        self.assertIn("default-private-binding", self.registry.requirements["S7.5.5-005"]["pending"])
        self.assertIn("explicit-private-over-public", self.registry.requirements["S7.5.5-005"]["pending"])
        self.assertIn("public-type-public-object", self.registry.requirements["S7.5.5-006"]["pending"])
        self.assertIn("defining-module-control", self.registry.requirements["S7.5.5-007"]["pending"])

    def test_canonical_json_and_both_markdown_views_are_current(self):
        self.assertEqual(self.catalogue, generated.synced_catalogue(self.catalogue, self.specs))
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs))
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split("## Reproduction and gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 66)
        for r in self.catalogue["requirements"]:
            for facet, plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** — {plan}", appendix)
        admin = {k: v for k, v in self.catalogue.items() if k.startswith("review_")}
        synced = generated.synced_catalogue(self.catalogue, self.specs)
        self.assertEqual({k: v for k, v in synced.items() if k.startswith("review_")}, admin)
        self.assertIn(f"Catalogue source review: {generated.catalogue_review_status(self.catalogue)}.", view)
        self.assertEqual(self.registry.requirements["S7.5.5-007"]["diagnostic_obligation"], "required")

    def test_administrative_review_transitions_do_not_rewrite_requirement_material(self):
        neutral = generated.synced_catalogue(self.catalogue, self.specs)
        reviewed = json.loads(json.dumps(neutral))
        reviewed["review_state"] = "reviewed"
        reviewed["review_rationale"] = "Synthetic in-memory administrative preservation test, not an approval."
        registry = Registry(ROOT)
        registry.catalogues["7.5.5"] = reviewed
        reviewed["review_fingerprint"] = registry.catalogue_fingerprint("7.5.5")
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertEqual(generated.catalogue_review_status(reviewed), "reviewed")
        self.assertEqual(reviewed["requirements"], neutral["requirements"])
        view = generated.render_view(reviewed, self.specs)
        self.assertIn("Catalogue source review: reviewed.", view)
        self.assertNotIn("unreviewed fixtures", view)
        self.assertNotIn("remains the next integration gate", view)
        self.assertNotIn("still require independent fixture review", view)
        stale = json.loads(json.dumps(reviewed))
        stale["review_fingerprint"] = "0" * 64
        self.assertEqual(generated.synced_catalogue(stale, self.specs), stale)
        self.assertIn("Catalogue source review: stale.", generated.render_view(stale, self.specs))

    def test_all_57_contracts_use_only_the_finite_role_property_routes(self):
        routes = generated.diagnostic_routes()
        self.assertEqual({generated.identifier(r, v, True) for r, v in routes}, set(self.repairs))
        for (rule, variant), route in routes.items():
            name = generated.identifier(rule, variant, True)
            predicate = self.cases[name].fixture.expectation.diagnostic
            with self.subTest(case=name):
                self.assertEqual(predicate["contains_any"], route["messages"])
                self.assertEqual(predicate.get("allow_nonfatal", []), route.get("nonfatal", []))
                self.assertEqual(len(route["messages"]), len(set(route["messages"])))

    def test_coordinator_tbfr001_probes_and_semantic_companions(self):
        probes = [
            ("R749", "attribute_colons", "Dummy argument declaration expected '::'"),
            ("R749", "empty_concrete", "Expected binding name for generic interface 'unrelated'"),
            ("R751", "missing_arrow", "Pointer assignment to unrelated object expected '=>'"),
            ("C773", "target_colons", "An IMPORT statement requires a double colon"),
            ("C773", "target_colons", "A type parameter declaration must appear with '::'"),
            ("C784", "no_arguments", "Generic procedure 'unrelated' must have at least one argument"),
            ("C786", "bare_conflict", "The generic interface cannot distinguish procedures with PASS and NOPASS"),
            ("C786", "named_conflict", "The generic interface cannot distinguish procedures with NOPASS and PASS"),
            ("C787", "incompatible_attributes", "The generic interface cannot distinguish procedures with DEFERRED and NON_OVERRIDABLE"),
            ("C788", "missing_deferred", "The length parameter of character component 'text' must be DEFERRED"),
            ("R749", "attribute_colons", "Type parameter declaration expected '::' after KIND"),
            ("R749", "empty_interface", "Expected binding name for generic interface 'different'"),
            ("R751", "missing_arrow", "An unrelated data pointer initializer expected '=>'"),
            ("R751", "missing_member", "Expected specific binding name for generic interface 'unrelated'"),
            ("C773", "target_colons", "A component initialization requires a double colon"),
            ("C784", "no_arguments", "External procedure 'different' must have at least one argument"),
            ("C786", "bare_conflict", "Generic resolution treats PASS and NOPASS argument lists differently"),
            ("C787", "incompatible_attributes", "A generic interface compares NON_OVERRIDABLE and DEFERRED bindings"),
            ("C788", "missing_deferred", "Allocatable CHARACTER result 'text' must be DEFERRED"),
        ]
        for rule, variant, message in probes:
            name = generated.identifier(rule, variant, True)
            for family in ["lfortran", "gfortran", "flang"]:
                for code in [0, 1]:
                    with self.subTest(case=name, family=family, code=code, message=message):
                        self.assertEqual(self.judge(name, message, family, code,
                                                    without_exclusions=True), "fail")

    def test_wrong_roles_and_properties_for_every_negative_family(self):
        wrong = {
            "R746": ["Component PRIVATE must precede data component declarations",
                     "Binding 'act' cannot override a PRIVATE parent procedure"],
            "R747": ["Component 'act' is PRIVATE and cannot be accessed from the client",
                     "PUBLIC binding 'act' has the wrong result type"],
            "C772": ["A PRIVATE component of 'record' is inaccessible by USE association",
                     "Type-bound binding 'act' cannot change a public parent's accessibility"],
            "R749": ["Expected binding name for generic interface 'unrelated'",
                     "A dummy procedure declaration expected '::'"],
            "R750": ["Procedure pointer target 'impl' has an incompatible interface",
                     "Token '(' is unexpected here in an unrelated array reference"],
            "C773": ["An IMPORT statement requires a double colon",
                     "A data component declaration must appear with '::'"],
            "C774": ["'different' must be a module procedure or an external procedure with an explicit interface",
                     "Actual argument 'work' has the wrong type for a generic procedure"],
            "C775": ["Type parameter 'act' was declared twice",
                     "There is already a procedure with binding name 'different' for the derived type 'record'"],
            "R751": ["Pointer assignment to 'unrelated' expected '=>'",
                     "Expected a binding name in the external generic interface 'different'"],
            "C776": ["Component 'g' has incompatible type parameters",
                     "Binding 'g' has matching accessibility but different dummy names"],
            "C777": ["Generic interface 'g' has duplicate declarations of procedure 'impl'",
                     "Binding name 'different' not found in this derived type"],
            "C778": ["Binding name 'specific' was already specified for generic 'different'",
                     "'int_case' already defined as specific binding for the generic 'different'"],
            "C779": ["Generic distinguishability compares a NOPASS operator and a PASS operator",
                     "Defined input/output procedure 'different' may not have NOPASS attribute"],
            "R752": ["Token ')' is unexpected in an array bounds declaration",
                     "Procedure pointer component 'act' requires POINTER"],
            "C783": ["Procedure pointer component 'act' specifies NOPASS more than once",
                     "Data component 'payload' specifies its PRIVATE access twice"],
            "C784": ["Generic procedure 'unrelated' must have at least one argument",
                     "Non-polymorphic passed-object dummy argument of 'impl' at (1)"],
            "C785": ["Passed-object dummy argument slef has the wrong rank",
                     "Procedure 'different' with PASS(slef) at (1) has no argument 'slef'"],
            "C786": ["Generic resolution cannot distinguish NOPASS and PASS procedures",
                     "An interface compares PASS and NOPASS attributes for generic resolution"],
            "C787": ["Generic interface cannot distinguish NON_OVERRIDABLE and DEFERRED procedures",
                     "DEFERRED procedure 'act' is used in a non-ABSTRACT type"],
            "C788": ["The length parameter of character component 'text' must be DEFERRED",
                     "Type 'record' is not ABSTRACT but has a DEFERRED binding"],
            "C789": ["DEFERRED binding 'act' requires an ABSTRACT containing type",
                     "Binding 'act' overrides a parent with different dummy argument names"],
            "C790": ["NON_OVERRIDABLE binding 'act' has the wrong result type",
                     "Override of PURE 'act' must be PURE"],
            "S7.5.5-007": ["'unrelated' of 'record' is PRIVATE at (1)",
                          "PRIVATE name 'secret' is accessible only within module 'different_provider'"],
        }
        self.assertEqual(set(wrong), set(PAIRS))
        for name in self.repairs:
            for message in wrong[self.cases[name].rule]:
                for family in ["lfortran", "gfortran", "flang"]:
                    with self.subTest(case=name, family=family, message=message):
                        self.assertEqual(self.judge(name, message, family,
                                                    without_exclusions=True), "fail")

    def test_full_role_messages_can_report_without_fatal_exit(self):
        for name in self.repairs:
            predicate = self.cases[name].fixture.expectation.diagnostic
            for message in predicate["contains_any"]:
                self.assertNotIn(message.lower(), {"type", "kind", "expected", "private", "attribute", "binding"})
                for family in ["lfortran", "gfortran", "flang"]:
                    for code in [0, 1]:
                        with self.subTest(case=name, message=message, family=family, code=code):
                            self.assertEqual(self.judge(name, message, family, code), "pass")

    def test_generic_wrong_causes_crashes_locations_and_echo_are_rejected(self):
        wrong = [
            "expected type", "Expected END TYPE statement", "syntax error",
            "Unexpected end of file", "Unknown type 'record'", "Duplicate attribute",
            "Binding 'unrelated' is PRIVATE", "Generic 'unrelated' is ambiguous",
            "Procedure 'unrelated' has the wrong number of arguments",
            "Function implementation is not implemented", "internal compiler error",
        ]
        for name in self.repairs:
            case = self.cases[name]
            p = case.fixture.expectation.diagnostic
            correct = p["contains_any"][0]
            for family in ["lfortran", "gfortran", "flang"]:
                with self.subTest(case=name, family=family):
                    for message in wrong:
                        self.assertEqual(self.judge(name, message, family), "fail")
                    self.assertEqual(self.judge(name, correct, family, file="unrelated.f90"), "fail")
                    self.assertEqual(self.judge(name, correct, family, line=p.get("end_line", p["line"]) + 1), "fail")
                    self.assertEqual(self.judge(name, correct, family, timed_out=True), "fail")
                    self.assertEqual(self.judge(name, correct, family, code=-11), "fail")
                    self.assertEqual(self.judge(name, correct, family, echo=True), "fail")
                    self.assertEqual(self.judge(name, correct + ": not implemented", family), "fail")
                    self.assertEqual(self.judge(name, correct + ": ASR verifier failure", family), "fail")

    def test_binding_roles_do_not_cross_credit_components_or_opposite_iff_direction(self):
        cases = {
            generated.identifier("C783", "duplicate_nopass", True):
                "Component 'act' has a Duplicate NOPASS attribute",
            generated.identifier("C786", "bare_conflict", True):
                "Procedure pointer component has PASS and NOPASS",
            generated.identifier("C788", "missing_deferred", True):
                "Interface must be specified for DEFERRED binding",
            generated.identifier("C790", "nonoverridable_override", True):
                "A pure procedure must not be overridden by an impure procedure",
            generated.identifier("S7.5.5-007", "explicit_private_client", True):
                "Component 'secret' of 'record' is PRIVATE",
            generated.identifier("R752", "empty_pass", True):
                "Expected '::' after binding-attributes at (1)",
            generated.identifier("C779", "assignment_nopass", True):
                "Type-bound operator at (1) cannot be NOPASS",
            generated.identifier("C784", "integer_argument", True):
                "Non-polymorphic passed-object dummy argument of 'impl' at (1)",
            generated.identifier("C777", "generic_member", True):
                "h doesn't exist inside record type",
            generated.identifier("S7.5.5-007", "private_other_module", True):
                "Syntax error in VALUE statement at (1)",
        }
        for name, message in cases.items():
            for family in ["lfortran", "gfortran", "flang"]:
                self.assertEqual(self.judge(name, message, family), "fail")

    def test_qualified_nonfatal_reports_and_internal_failure_boundary(self):
        expected = {
            generated.identifier("C773", "target_colons", True): "portability",
            **{generated.identifier("C783", "duplicate_" + v, True): "warning"
               for v in ["public", "private", "deferred", "non_overridable", "nopass", "pass"]},
        }
        actual = {name for name in self.repairs
                  if self.cases[name].fixture.expectation.diagnostic.get("allow_nonfatal")}
        self.assertEqual(actual, set(expected))
        for name, severity in expected.items():
            case = self.cases[name]
            d = case.fixture.expectation.diagnostic
            allowance = d["allow_nonfatal"][0]
            self.assertEqual(allowance["compiler"], "flang")
            self.assertEqual(allowance["severity"], severity)
            message = allowance["equals_any"][0]
            for family in ["flang", "gfortran"]:
                output = f"{d['file']}:{d['line']}:1: {severity}: {message}\n"
                result = runner.judge_diagnostic(
                    runner.ProcessResult(0, output), runner.Compiler(family, family, "f2018"),
                    case.rule, d)
                self.assertEqual(result.outcome, "pass" if family == "flang" else "fail")
        case = self.cases[generated.identifier("C783", "duplicate_pass_name", True)]
        d = case.fixture.expectation.diagnostic
        self.assertNotIn("allow_nonfatal", d)
        output = (f"{d['file']}:{d['line']}:1: warning: "
                  "Attribute 'PASS' cannot be used more than once [-Wredundant-attribute]\n"
                  f"{d['file']}:{d['line']}:29: error: Internal: no symbol found for 'self'\n")
        self.assertEqual(runner.judge_diagnostic(
            runner.ProcessResult(1, output), runner.Compiler("flang", "flang", "f2018"),
            case.rule, d).outcome, "fail")

    def test_actual_c783_warning_allowances_cannot_hide_native_internal_errors(self):
        names = {
            generated.identifier("C783", "duplicate_" + variant, True)
            for variant in ["public", "private", "deferred", "non_overridable", "nopass", "pass"]
        }
        actual = {
            name for name in self.repairs
            if self.cases[name].rule == "C783"
            and self.cases[name].fixture.expectation.diagnostic.get("allow_nonfatal")
        }
        self.assertEqual(actual, names)
        compiler = runner.Compiler("flang", "flang", "f2018")
        for name in sorted(names):
            fixture = self.cases[name].fixture
            diagnostic = fixture.expectation.diagnostic
            allowance = diagnostic["allow_nonfatal"][0]
            self.assertEqual((allowance["compiler"], allowance["severity"]), ("flang", "warning"))
            message = allowance["equals_any"][0]
            warning = f"{diagnostic['file']}:{diagnostic['line']}:1: warning: {message}\n"
            for status in [0, 1]:
                with self.subTest(case=name, status=status, ordinary_warning=True):
                    with patch.object(runner, "run", return_value=runner.ProcessResult(status, warning)):
                        ordinary = runner.check_fixture(fixture, compiler)
                    self.assertEqual(ordinary.outcome, "pass")
                for origin in [
                    f"{diagnostic['file']}:{diagnostic['line']}:29: ",
                    "other.inc:8:1: ",
                    "",
                ]:
                    internal = origin + "error: Internal: no symbol found for 'self'\n"
                    for output in [warning + internal, internal + warning]:
                        with self.subTest(case=name, status=status, origin=origin, output=output):
                            with patch.object(runner, "run", return_value=runner.ProcessResult(status, output)):
                                failure = runner.check_fixture(fixture, compiler)
                            self.assertEqual(failure.outcome, "fail")
                            self.assertEqual(failure.phase, "compile")
                            self.assertIn("compiler internal error", failure.note)
                            self.assertEqual(failure.output, output)

    def test_abstract_deferred_repairs_retain_the_other_required_premises(self):
        good = self.source("C787", "incompatible_attributes_repair")
        self.assertIn("type, abstract :: record", good)
        self.assertIn("procedure(iface), deferred, nopass :: act", good)
        self.assertNotIn("non_overridable", good)
        good = self.source("C789", "redefer_concrete_repair")
        self.assertIn("type, abstract, extends(record) :: child\ncontains\nend type child", good)
        self.assertNotIn("procedure(child_iface), deferred :: act", good)
        good = self.source("C788", "missing_deferred_repair")
        self.assertIn("procedure(iface), deferred, nopass :: act", good)
        good = self.source("C788", "missing_interface_repair")
        self.assertIn("type, abstract :: record", good)
        self.assertIn("procedure, nopass :: impl", good)

    def test_nameless_generic_pairs_have_valid_interfaces_and_only_remove_nopass(self):
        for name, repair in self.repairs.items():
            if self.cases[name].rule != "C779":
                continue
            with self.subTest(case=name):
                self.assertEqual(repair["repaired"], repair["wrong"].replace(", nopass", ""))
                content = b"\n".join(self.inputs(name).values()).decode()
                self.assertIn("class(record), intent(", content)
                self.assertNotIn("value ::", content)
                self.assertNotIn("optional", content)
                if "io_impl" in content:
                    self.assertIn("integer, intent(out) :: iostat", content)
                    self.assertIn("character(*), intent(inout) :: iomsg", content)
                    self.assertIn("iostat = 0", content)
                    self.assertNotIn("write(unit", content)
                    self.assertNotIn("read(unit", content)
                    formatted = "unformatted" not in name
                    self.assertEqual("v_list(:)" in content, formatted)
                    self.assertEqual("iotype" in content, formatted)
                    intent = "inout" if "_read_" in name else "in"
                    self.assertIn(f"class(record), intent({intent}) :: dtv", content)

    def test_c784_missing_defining_type_is_not_repaired_by_adding_a_typed_witness(self):
        negative = self.source("C784", "integer_argument", invalid=True)
        control = self.source("C784", "integer_argument_repair")
        for source in (negative, control):
            self.assertIn("subroutine impl(number)\ninteger, intent(in) :: number", source)
            self.assertNotIn("class(record)", source)
        self.assertIn("procedure :: impl", negative)
        self.assertIn("procedure, nopass :: impl", control)
        self.assertIn("necessarily also fails C765", self.registry.requirements["C784"]["oracle"])

    def test_runtime_setup_is_named_and_expectations_are_independent(self):
        same = self.source("S7.5.5-001", "same_name")
        for snippet in ["call prepare_first(a)", "call prepare_second(b)", "item%payload = 17",
                        "item%payload = 29", "observed /= 17", "observed /= 59"]:
            self.assertIn(snippet, same)
        for variant in ["generic_union", "forward_generic_union"]:
            body = self.source("S7.5.5-004", variant)
            for expected in [11, 22, 13, 24]:
                self.assertIn(f"observed /= {expected}", body)
            self.assertIn("call prepare(item,payload=5)", body)
            self.assertIn("call prepare(item,payload=7)", body)
        deferred = self.source("S7.5.5-003", "deferred_interface")
        self.assertIn("class(base), intent(in) :: item", deferred)
        self.assertIn("type(record) :: item", deferred)
        self.assertNotIn("type(base) ::", deferred)
        self.assertNotIn("item%base", deferred)
        for name, c in self.cases.items():
            if c.fixture.expectation.phase == "run":
                body = b"\n".join(self.inputs(name).values()).decode().lower()
                for forbidden in ["associated(", "allocated(", "transfer(", "sizeof(", "same_type_as(", "final ::"]:
                    self.assertNotIn(forbidden, body)

    def test_private_client_repairs_and_existing_control_ownership(self):
        explicit = self.repairs[generated.identifier("S7.5.5-007", "explicit_private_client", True)]
        default = self.repairs[generated.identifier("S7.5.5-007", "default_private_client", True)]
        self.assertEqual((explicit["wrong"], explicit["repaired"]),
                         ("procedure, private :: secret", "procedure, public :: secret"))
        self.assertEqual((default["wrong"], default["repaired"]), ("private\n", ""))
        for repair in [explicit, default]:
            self.assertEqual((repair["file"], repair["anchor_file"]), ("provider.f90", "client.f90"))
        desc = self.source("S7.5.5-007", "private_descendant")
        self.assertIn("module subroutine inspect()", desc)
        self.assertIn("submodule(tbp_provider)", desc)
        self.assertNotIn("type(base) ::", desc)
        self.assertEqual(len([x for x in self.cases.values() if x.rule == "S7.5.5-005"]), 1)
        self.assertEqual(len([x for x in self.cases.values() if x.rule == "S7.5.5-006"]), 2)

    def test_shared_parameter_corpus_remains_exact(self):
        corpus = parameters.build_corpus()
        self.assertEqual(len(corpus.cases), 66)
        self.assertEqual(len(corpus.files), 105)
        self.assertFalse(set(corpus.files) & set(self.outputs))
        for path, content in corpus.files.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
