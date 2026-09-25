"""Array constructor 7.8.b fixture packet checks."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_array_constructors_7_8_b_fixtures as generated

EXPECTED = {
    "R778_valid__array_constructors_7_8_b_typed_empty_other_categories": ("R778", ["typed-empty-other-categories"]),
    "S7_8_002_valid__array_constructors_7_8_b_explicit_character_length_boundaries": ("S7.8-002", ["zero-size-and-explicit-spec-boundaries"]),
    "C7121_valid__array_constructors_7_8_b_intrinsic_type_admissions": ("C7121", ["intrinsic-type-admissions"]),
    "C7124_valid__array_constructors_7_8_b_limited_value_admissions": ("C7124", ["limited-value-admissions"]),
    "C7125_valid__array_constructors_7_8_b_concrete_child_admission": ("C7125", ["concrete-child-admission"]),
    "C7128_valid__array_constructors_7_8_b_disjoint_reuse_admission": ("C7128", ["disjoint-reuse-admission"]),
    "R784_valid__array_constructors_7_8_b_bare_scalar_integer_name": ("R784", ["bare-scalar-integer-name"]),
    "R784_valid__array_constructors_7_8_b_literal_control_repair": ("R784", ["bare-scalar-integer-name"]),
    "R782_valid__array_constructors_7_8_b_implied_do_syntax_control": ("R782", ["single-body-value"]),
    "R782_invalid__array_constructors_7_8_b_missing_control_separator": ("R782", ["missing-control-separator"]),
    "R782_invalid__array_constructors_7_8_b_missing_body_list": ("R782", ["missing-body-list"]),
    "R784_invalid__array_constructors_7_8_b_literal_control_variable": ("R784", ["literal-is-not-control-variable"]),
}


class ArrayConstructors78BFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        paths = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in paths}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def source(self, case_id):
        return (self.cases[case_id].fixture.root / "source.f90").read_text()

    def test_exact_case_facet_partition_and_metadata(self):
        self.assertEqual(set(self.specs), set(EXPECTED))
        self.assertEqual(set(self.cases), set(EXPECTED))
        self.assertEqual(len(self.specs), 12)
        selected = {(rule, facet) for rule, facets in generated.SELECTED.items() for facet in facets}
        represented = {(spec["rule"], facet) for spec in self.specs.values() for facet in spec["facets"]}
        self.assertEqual(selected, represented & selected)
        self.assertEqual(len(selected), 10)
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

    def test_generated_files_are_exact_and_isolated(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 24)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            self.assertTrue(raw.endswith(b"\n"))
            if path.name == "source.f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_sources_reach_the_selected_constructor_features(self):
        src = self.source("R778_valid__array_constructors_7_8_b_typed_empty_other_categories")
        self.assertIn("[character(len=3) ::]", src)
        self.assertIn("if (len(chars) /= 3) error stop 2", src)
        self.assertIn("if (size([rec ::]) /= 0) error stop 3", src)
        src = self.source("S7_8_002_valid__array_constructors_7_8_b_explicit_character_length_boundaries")
        self.assertIn("[character(len=3) ::]", src)
        self.assertIn("[character(len=3) :: 'ab','abcd']", src)
        self.assertLess(src.index("len(values) /= 3"), src.index("values(1) /= 'ab '"))
        self.assertIn("values(2) /= 'abc'", src)
        src = self.source("C7121_valid__array_constructors_7_8_b_intrinsic_type_admissions")
        for needle in (
            "[integer :: 1, 2.0, (3.0,0.0)]", "[real :: 1, 2.0, (3.0,0.0)]",
            "[complex :: 1, 2.0, (3.0,-4.0)]", "[logical :: .true., .false.]",
            "[character(len=2) :: 'A','BC']", "len(chars) /= 2"):
            self.assertIn(needle, src)
        src = self.source("C7124_valid__array_constructors_7_8_b_limited_value_admissions")
        self.assertIn("class(base), intent(in) :: x", src)
        self.assertIn("[base :: local, x]", src)
        self.assertIn("[integer :: 5, 7]", src)
        src = self.source("C7125_valid__array_constructors_7_8_b_concrete_child_admission")
        self.assertIn("type, abstract :: base", src)
        self.assertIn("type, extends(base) :: child", src)
        self.assertIn("[left, right]", src)
        src = self.source("C7128_valid__array_constructors_7_8_b_disjoint_reuse_admission")
        self.assertIn("[(i,i=1,2),(i,i=3,4)]", src)
        self.assertIn("if (i /= 99) error stop 6", src)
        src = self.source("R784_valid__array_constructors_7_8_b_bare_scalar_integer_name")
        self.assertIn("[(i,i=2,4)]", src)
        self.assertIn("if (i /= 77) error stop 5", src)

    def test_invalids_have_real_one_property_controls_and_line_diagnostics(self):
        for case_id in (
            "R782_invalid__array_constructors_7_8_b_missing_control_separator",
            "R782_invalid__array_constructors_7_8_b_missing_body_list",
            "R784_invalid__array_constructors_7_8_b_literal_control_variable",
        ):
            spec = self.specs[case_id]
            control = self.specs[spec["control_id"]]
            repaired = spec["source"].replace(spec["repair"]["original"], spec["repair"]["replacement"])
            self.assertEqual(repaired, control["source"])
            self.assertEqual(spec["diagnostic"]["file"], "source.f90")
            self.assertEqual(spec["diagnostic"]["line"], spec["diagnostic"]["end_line"])
            self.assertIn(spec["repair"]["anchor"], spec["source"].splitlines()[spec["diagnostic"]["line"] - 1])
            for banned in ("not implemented", "internal error", "assert", "asr", "traceback"):
                self.assertIn(banned, spec["diagnostic"]["excludes_any"])

    def test_mutation_matrix_is_feature_specific_and_runtime_checked(self):
        mutations = [(case_id, m) for case_id, spec in self.specs.items() for m in spec.get("mutations", [])]
        self.assertEqual(len(mutations), 21)
        self.assertFalse([spec["id"] for spec in self.specs.values() if spec["kind"] == "valid" and not spec["mutations"]])
        ids = {m["id"] for _, m in mutations}
        self.assertTrue({
            "reverse-integer-values", "change-real-converted-value", "reverse-complex-values",
            "swap-logical-values", "swap-character-values", "swap-limited-class-values",
            "swap-concrete-child-values", "change-second-disjoint-bounds", "change-bare-terminal-bound",
            "change-literal-control-body", "change-control-body-value",
            "change-empty-character-length", "make-derived-empty-nonempty",
            "change-explicit-value-length", "swap-explicit-character-values",
        } <= ids)
        for case_id, mutation in mutations:
            self.assertNotEqual(mutation["source"], self.specs[case_id]["source"])
        self.assertTrue(callable(generated.check_mutations))

    def test_catalogue_bindings_are_owned_and_preserve_admin(self):
        updated = generated.synced_catalogue(self.catalogue, self.specs)
        self.assertEqual(updated, self.catalogue)
        for rule, facets in generated.SELECTED.items():
            req = next(r for r in self.catalogue["requirements"] if r["id"] == rule)
            self.assertFalse(set(facets) & set(req["pending"]))
            self.assertIn(generated.ORACLE_PREFIX, req["oracle"])
            self.assertIn(generated.LIMIT_PREFIX, req["oracle_limitation"])
        admin = {k: v for k, v in self.catalogue.items() if k.startswith("review_")}
        self.assertEqual({k: v for k, v in updated.items() if k.startswith("review_")}, admin)
        self.assertEqual((ROOT / generated.VIEW).read_text(), generated.render_view(self.catalogue))


if __name__ == "__main__":
    unittest.main()
