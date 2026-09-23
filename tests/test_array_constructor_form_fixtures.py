"""Array constructor form, positive controls and focused diagnostics."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_array_constructor_form_fixtures as generated
import generate_array_constructor_value_fixtures as value_generated

EXPECTED = {
    "R777_valid__array_constructor_form_delimiter_forms": ("R777", ["slash-parenthesis-admission", "square-bracket-admission"]),
    "R778_valid__array_constructor_form_typed_empty_integer_control": ("R778", ["typed-empty-integer"]),
    "R778_invalid__array_constructor_form_untyped_empty_list": ("R778", ["untyped-empty-list"]),
    "R778_valid__array_constructor_form_typed_nonempty_and_derived": ("R778", ["typed-nonempty"]),
    "C7122_valid__array_constructor_form_same_derived_type": ("C7122", ["same-derived-type-admission"]),
    "C7120_valid__array_constructor_form_untyped_same_type_rank_control": ("C7120", ["same-type-kind-different-ranks"]),
    "R778_valid__array_constructor_form_untyped_nonempty": ("R778", ["untyped-nonempty"]),
    "R781_valid__array_constructor_form_scalar_and_array_values": ("R781", ["scalar-expression-admission", "array-expression-admission"]),
    "C7120_invalid__array_constructor_form_different_intrinsic_type": ("C7120", ["different-intrinsic-type"]),
    "R781_valid__array_constructor_form_implied_do_value": ("R781", ["implied-do-admission"]),
    "R782_valid__array_constructor_form_implied_do_forms": ("R782", ["single-body-value", "multiple-body-values", "nested-form"]),
    "R783_valid__array_constructor_form_inferred_and_runtime_controls": ("R783", ["inferred-integer-variable", "runtime-bound-and-step-expressions"]),
    "C7128_valid__array_constructor_form_distinct_nested_variables": ("C7128", ["distinct-nested-variables"]),
    "S7_8_002_valid__array_constructor_form_equal_character_lengths": ("S7.8-002", ["runtime-equal-length-controls"]),
    "S7_8_007_valid__array_constructor_form_constant_zero_trip_character": ("S7.8-007", ["constant-length-zero-trip-control"]),
}


class ArrayConstructorFormFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        paths = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in paths}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def source(self, case_id):
        return (self.cases[case_id].fixture.root / "source.f90").read_text()

    def test_exact_case_and_facet_partition(self):
        self.assertEqual(set(self.specs), set(EXPECTED))
        self.assertEqual(set(self.cases), set(EXPECTED))
        self.assertEqual(len(self.specs), 15)
        self.assertEqual(sum(len(s["facets"]) for s in self.specs.values()), 20)
        for case_id, (rule, facets) in EXPECTED.items():
            spec = self.specs[case_id]
            case = self.cases[case_id]
            self.assertEqual(spec["rule"], rule)
            self.assertEqual(spec["facets"], facets)
            self.assertEqual(case.rule, rule)
            self.assertEqual(case.meta.facets, facets)
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            validate_case_requirement(case, self.registry.requirements[rule])
            if case.kind == "valid":
                self.assertEqual(case.meta.evidence, "positive-control")
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.exit_code, 0)
            else:
                self.assertEqual(case.meta.evidence, "effect")
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")

    def test_generated_files_are_exact_and_isolated_to_prefix(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 30)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            self.assertTrue(raw.endswith(b"\n"))
            if path.name == "source.f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_batch130_value_facets_are_not_rebound_or_recreated(self):
        overlap = set()
        for rule, facets in generated.SELECTED.items():
            overlap |= {(rule, facet) for facet in facets} & {(r, f) for r, fs in value_generated.ELIGIBLE.items() for f in fs}
        self.assertFalse(overlap)
        self.assertFalse(set(value_generated.build_corpus()[0]) & set(self.files))
        for case_id in self.specs:
            self.assertNotIn("array_constructor_value_", case_id)

    def test_constructed_sources_reach_the_selected_forms(self):
        src = self.source("R777_valid__array_constructor_form_delimiter_forms")
        self.assertIn("associate(slash => (/11,13/))", src)
        self.assertIn("associate(square => [11,13])", src)
        self.assertLess(src.index("slash(1) /= 11"), src.index("square(1) /= 11"))
        src = self.source("R778_valid__array_constructor_form_typed_empty_integer_control")
        self.assertIn("n = size([integer ::])", src)
        self.assertIn("if (n /= 0) error stop 1", src)
        self.assertIn("sum([integer ::])", src)
        src = self.source("R778_valid__array_constructor_form_typed_nonempty_and_derived")
        self.assertIn("[integer :: 17,19,23]", src)
        self.assertIn("type rec", src)
        self.assertIn("[rec :: left,right]", src)
        self.assertIn("records(2)%marker /= 37", src)
        src = self.source("C7120_valid__array_constructor_form_untyped_same_type_rank_control")
        self.assertIn("associate(values => [7,vec,matrix,31])", src)
        self.assertIn("matrix(2,1) = 19", src)
        self.assertIn("values(8) /= 31", src)
        src = self.source("R782_valid__array_constructor_form_implied_do_forms")
        self.assertIn("[(i,10*i,i=1,2)]", src)
        self.assertIn("[((10*i+j,j=1,2),i=1,2)]", src)
        self.assertIn("[(i,i=lower,upper,stride)]", src)
        self.assertNotIn("integer :: i=", src)

    def test_character_and_zero_size_oracles_are_nonvacuous(self):
        src = self.source("S7_8_002_valid__array_constructor_form_equal_character_lengths")
        self.assertIn("character(len=2) :: left, right", src)
        self.assertLess(src.index("len(equal) /= 2"), src.index("equal(1) /= 'AB'"))
        self.assertIn("size(zero_constant) /= 0", src)
        self.assertIn("len(zero_constant) /= 2", src)
        self.assertIn("[character(len=3) :: ('AB',i=1,0)]", src)
        self.assertIn("len(zero_typed) /= 3", src)
        self.assertNotIn("a  ", src)

    def test_invalids_have_one_property_controls_and_focused_diagnostics(self):
        empty = self.specs["R778_invalid__array_constructor_form_untyped_empty_list"]
        control = self.specs[empty["control_id"]]
        self.assertEqual(empty["control_rule"], "R778")
        self.assertEqual(empty["control_facets"], ["typed-empty-integer"])
        self.assertEqual(empty["source"].replace("[]", "[integer ::]"), control["source"])
        self.assertEqual(empty["diagnostic"]["contains_any"], ["empty array constructor"])
        diff = self.specs["C7120_invalid__array_constructor_form_different_intrinsic_type"]
        diff_control = self.specs[diff["control_id"]]
        self.assertEqual(diff["source"].replace("[7,vec,2.0,31]", "[7,vec,matrix,31]"), diff_control["source"])
        self.assertEqual(diff["diagnostic"]["contains_any"], ["array constructor"])
        for spec in (empty, diff):
            self.assertEqual(spec["diagnostic"]["file"], "source.f90")
            self.assertEqual(spec["diagnostic"]["line"], spec["diagnostic"]["end_line"])
            for banned in ("not implemented", "internal error", "traceback", "unknown exception"):
                self.assertIn(banned, spec["diagnostic"]["excludes_any"])

    def test_mutation_matrix_targets_features_not_only_expected_values(self):
        mutations = [(spec["id"], m) for spec in self.specs.values() for m in spec.get("mutations", [])]
        self.assertEqual(len(mutations), 28)
        self.assertFalse([spec["id"] for spec in self.specs.values()
                          if spec["kind"] == "valid" and not spec["mutations"]])
        seen = set()
        for case_id, mutation in mutations:
            original = self.specs[case_id]["source"]
            mutated = mutation["source"]
            self.assertNotEqual(mutated, original)
            self.assertIn(mutation["replacement"], mutated)
            self.assertNotIn((case_id, mutation["id"]), seen)
            seen.add((case_id, mutation["id"]))
        ids = {m["id"] for _, m in mutations}
        self.assertTrue({"slash-swap", "square-swap", "change-type-spec-length", "drop-character-ac-value", "swap-nested-order", "drop-array-ac-value"} <= ids)
        self.assertTrue(callable(generated.check_mutations))

    def test_catalogue_bindings_preserve_foreign_pending_and_admin_state(self):
        updated = generated.synced_catalogue(self.catalogue, self.specs)
        self.assertEqual(updated, self.catalogue)
        for rule, facets in generated.SELECTED.items():
            req = next(r for r in self.catalogue["requirements"] if r["id"] == rule)
            self.assertFalse(set(facets) & set(req["pending"]))
            self.assertIn(generated.ORACLE_PREFIX, req["oracle"])
            self.assertIn(generated.LIMIT_PREFIX, req["oracle_limitation"])
        for rule, facets in value_generated.ELIGIBLE.items():
            req = next(r for r in self.catalogue["requirements"] if r["id"] == rule)
            self.assertFalse(set(facets) & set(req["pending"]))
        admin = {k: v for k, v in self.catalogue.items() if k.startswith("review_")}
        self.assertEqual({k: v for k, v in updated.items() if k.startswith("review_")}, admin)


if __name__ == "__main__":
    unittest.main()
