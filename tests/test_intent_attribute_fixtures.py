"""INTENT attribute fixture packet coverage and non-vacuity checks."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_intent_attribute_fixtures as generated

EXPECTED = {
    "C846_valid__intent_attribute_c846_assignment_control": ("C846", ["assignment-and-loop-contexts"], "positive-control"),
    "C846_invalid__intent_attribute_c846_assignment_to_in": ("C846", ["assignment-and-loop-contexts"], "effect"),
    "C846_valid__intent_attribute_c846_do_variable_control": ("C846", ["assignment-and-loop-contexts"], "positive-control"),
    "C846_invalid__intent_attribute_c846_do_variable_to_in": ("C846", ["assignment-and-loop-contexts"], "effect"),
    "S8_5_10_002_valid__intent_attribute_pointer_dummy_target": (
        "S8.5.10-002", ["target-definition-controls"], "positive-control"),
    "S8_5_10_004_valid__intent_attribute_out_scalar_define": ("S8.5.10-004", ["definable-variable-controls"], "positive-control"),
    "S8_5_10_003_valid__intent_attribute_out_default_initialized": (
        "S8.5.10-003", ["default-initialized-exception-source", "redefinition-before-use"], "context-only"),
    "S8_5_10_003_valid__intent_attribute_out_allocatable_deallocated": (
        "S8.5.10-003", ["allocatable-entry-deallocation"], "context-only"),
    "S8_5_10_003_valid__intent_attribute_out_plain_entry": ("S8.5.10-003", ["plain-entry-context"], "context-only"),
    "S8_5_10_008_valid__intent_attribute_inout_definable_actual": (
        "S8.5.10-008", ["definable-actual-controls", "nonmodifying-inout-source", "partial-definition-and-retention"], "positive-control"),
    "S8_5_10_011_valid__intent_attribute_pointer_component_target": (
        "S8.5.10-011", ["pointer-subobject-target-boundary"], "positive-control"),
}


class IntentAttributeFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def source(self, case_id):
        return (self.cases[case_id].fixture.root / "source.f90").read_text()

    def test_exact_owned_cases_and_selected_facet_bindings(self):
        self.assertEqual(set(self.specs), set(EXPECTED))
        self.assertEqual(set(self.cases), set(EXPECTED))
        self.assertEqual(len(self.files), 22)
        unique = {(rule, facet) for rule, facets in generated.SELECTED.items() for facet in facets}
        covered = {(case.rule, facet) for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(unique, covered)
        for case_id, (rule, facets, evidence) in EXPECTED.items():
            case = self.cases[case_id]
            self.assertEqual(case.rule, rule)
            self.assertEqual(case.meta.facets, facets)
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.evidence, evidence)
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            validate_case_requirement(case, self.registry.requirements[rule])
            if case.kind == "invalid":
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("compile", "diagnose"))
                self.assertIsNone(case.fixture.link)
            else:
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("run", "success"))
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.fixture.expectation.stdout, [self.specs[case_id]["completion"]])

    def test_generated_files_are_deterministic_ascii_and_prefix_isolated(self):
        actual = {p for p in (ROOT / "tests" / "fixtures").glob(generated.PREFIX + "*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            self.assertTrue(raw.endswith(b"\n"))
            if path.name == "source.f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)
        self.assertEqual(generated.build_corpus()[0], self.files)

    def test_negative_has_one_property_control_and_focused_diagnostic(self):
        invalid = self.specs["C846_invalid__intent_attribute_c846_assignment_to_in"]
        control = self.specs[invalid["control_id"]]
        repaired = invalid["source"].replace("integer, intent(in) :: x", "integer, intent(inout) :: x")
        repaired = repaired.replace("INTENT ATTRIBUTE C846 ASSIGNMENT INVALID OK",
                                    "INTENT ATTRIBUTE C846 ASSIGNMENT CONTROL OK")
        self.assertEqual(repaired, control["source"])
        self.assertEqual(invalid["diagnostic"]["file"], "source.f90")
        self.assertEqual(invalid["diagnostic"]["line"], invalid["diagnostic"]["end_line"])
        self.assertEqual(invalid["diagnostic"]["contains_any"], ["intent(in)", "INTENT(IN)"])
        for banned in ("not implemented", "internal error", "traceback", "segmentation"):
            self.assertIn(banned, invalid["diagnostic"]["excludes_any"])
        do_invalid = self.specs["C846_invalid__intent_attribute_c846_do_variable_to_in"]
        do_control = self.specs[do_invalid["control_id"]]
        repaired_do = do_invalid["source"].replace("  do i = 1, 3", "  do j = 1, 3")
        repaired_do = repaired_do.replace("INTENT ATTRIBUTE C846 DO VARIABLE INVALID OK",
                                          "INTENT ATTRIBUTE C846 DO VARIABLE CONTROL OK")
        self.assertEqual(repaired_do, do_control["source"])
        self.assertEqual(do_invalid["diagnostic"]["line"],
                         generated.locate_line(do_invalid["source"], "do i = 1, 3"))

    def test_out_fixtures_never_read_undefined_parts_and_use_nondefault_sentinels(self):
        default_src = self.source("S8_5_10_003_valid__intent_attribute_out_default_initialized")
        self.assertIn("integer :: stamp = 41", default_src)
        self.assertIn("actual%stamp = 17", default_src)
        self.assertIn("actual%payload = 19", default_src)
        self.assertLess(default_src.index("if (x%stamp /= 41)"), default_src.index("x%payload = 23"))
        self.assertNotIn("x%payload /=", default_src)
        alloc_src = self.source("S8_5_10_003_valid__intent_attribute_out_allocatable_deallocated")
        self.assertIn("allocate(actual(5))", alloc_src)
        self.assertIn("if (allocated(x)) error stop 4", alloc_src)
        self.assertLess(alloc_src.index("if (allocated(x))"), alloc_src.index("allocate(x(2))"))
        self.assertIn("if (any(actual /= [31,37]))", alloc_src)
        scalar_src = self.source("S8_5_10_004_valid__intent_attribute_out_scalar_define")
        self.assertIn("actual = 29", scalar_src)
        self.assertLess(scalar_src.index("call define_out"), scalar_src.index("if (actual /= 47)"))

    def test_inout_and_pointer_component_sources_reach_the_rules(self):
        direct = self.source("S8_5_10_002_valid__intent_attribute_pointer_dummy_target")
        self.assertIn("integer, pointer, intent(in) :: p", direct)
        self.assertIn("actual => target", direct)
        self.assertIn("p = 13", direct)
        self.assertIn("if (target /= 13)", direct)
        inout = self.source("S8_5_10_008_valid__intent_attribute_inout_definable_actual")
        self.assertIn("integer, intent(inout) :: x", inout)
        self.assertIn("if (x /= 61) error stop 3", inout)
        self.assertIn("x = 73", inout)
        pointer = self.source("S8_5_10_011_valid__intent_attribute_pointer_component_target")
        self.assertIn("type(pointer_box), intent(in) :: x", pointer)
        self.assertIn("actual%p => target", pointer)
        self.assertIn("x%p = 90", pointer)
        self.assertIn("if (.not. associated(actual%p, target))", pointer)
        self.assertIn("if (associated(actual%p, other))", pointer)

    def test_mutation_matrix_is_feature_level_and_conforming_runtime(self):
        mutations = [(spec["id"], mutation) for spec in self.specs.values() if spec["kind"] == "valid"
                     for mutation in spec["mutations"]]
        self.assertEqual(len(mutations), 19)
        self.assertFalse([spec["id"] for spec in self.specs.values()
                          if spec["kind"] == "valid" and not spec["mutations"]])
        ids = {mutation["id"] for _, mutation in mutations}
        self.assertTrue({"remove-out-intent", "change-default-initializer", "remove-target-definition",
                         "remove-inout-write", "remove-assignment", "change-pointer-target-definition",
                         "remove-do-marker-increment"} <= ids)
        for case_id, mutation in mutations:
            original = self.specs[case_id]["source"]
            self.assertNotEqual(mutation["source"], original)
            self.assertIn("program p", mutation["source"])
            self.assertNotIn("intent(in) :: x\n  x = 5", mutation["source"])
        self.assertTrue(callable(generated.check_mutations))
        self.assertIn("S8_5_10_002_valid__intent_attribute_pointer_dummy_target",
                      generated.KNOWN_PARENT_FAILURES["lfortran"])

    def test_catalogue_sync_removes_only_selected_pending_facets_and_renders_summary(self):
        synced = generated.synced_catalogue(self.catalogue)
        self.assertEqual(synced, self.catalogue)
        by_rule = {row["id"]: row for row in self.catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            pending = set(by_rule[rule].get("pending", {}))
            self.assertFalse(set(facets) & pending)
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        view = generated.render_view(self.catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Eleven generated fixtures discharge eleven selected 8.5.10 facets", view)
        self.assertIn("No fixture reads an undefined OUT value", view)
        self.assertIn("finalization-relations", by_rule["S8.5.10-003"].get("pending", {}))

    def test_generator_check_mode_is_read_only(self):
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)


if __name__ == "__main__":
    unittest.main()
