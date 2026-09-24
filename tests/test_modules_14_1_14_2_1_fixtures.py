"""Tests for generated Clause 14.1 and 14.2.1 fixtures."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_modules_14_1_14_2_1_fixtures as generated


class Modules1411421FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_generated_case_set_and_manifest_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 25)
        self.assertEqual(sum(1 for case in self.cases.values() if case.kind == "invalid"), 11)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 50)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.coarray or case.meta.profiles or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            validate_case_requirement(case, self.registry.requirements[case.rule],
                                      case.rule in self.registry.numbered)
            if case.kind == "valid" and not spec.get("compile_only"):
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                                  case.fixture.expectation.exit_code), ("run", "success", 0))
                self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
            elif case.kind == "valid":
                self.assertEqual(self.members[case.name]["cohort"], "positive-control")
                self.assertEqual(case.meta.evidence, "positive-control")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "success"))
            else:
                self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "diagnose"))
                diag = case.fixture.expectation.diagnostic
                self.assertEqual((diag["file"], diag["line"], diag["end_line"]),
                                 ("source.f90", spec["line"], spec["end_line"]))
                self.assertEqual(diag["contains_any"], spec["messages"])
                for banned in generated.EXCLUSIONS:
                    self.assertIn(banned, diag["excludes_any"])
                self.assertIn(spec["control"], self.cases)

    def test_diagnostic_controls_are_one_property(self):
        pairs = [
            ("R1402_valid__program_statement_name_control", "R1402_invalid__program_statement_missing_name",
             "program r1402_missing_name_control", "program"),
            ("R1404_valid__module_missing_end_control", "R1404_invalid__module_missing_end",
             "end module r1404_missing_end_m", "end program r1404_missing_end_m"),
            ("R1405_valid__module_statement_name_control", "R1405_invalid__module_statement_missing_name",
             "module r1405_missing_name_m", "module"),
            ("C1402_valid__end_module_name_mismatch_control", "C1402_invalid__end_module_name_mismatch",
             "end module c1402_name_m", "end module c1402_other_m"),
            ("C1403_valid__stmt_function_control", "C1403_invalid__stmt_function_in_module_spec",
             "  integer :: i, f\n", "  integer :: i, f\n  f(i) = i + 1\n"),
            ("C1403_valid__entry_control", "C1403_invalid__entry_in_module_spec",
             "  implicit none\n", "  implicit none\n  entry alternate()\n"),
            ("C1403_valid__format_control", "C1403_invalid__format_in_module_spec",
             "  implicit none\n", "  implicit none\n  100 format(I0)\n"),
        ]
        for control, invalid, old, new in pairs:
            with self.subTest(invalid=invalid):
                control_source = self.specs[control]["source"]
                invalid_source = self.specs[invalid]["source"]
                self.assertEqual(control_source.count(old), 1)
                self.assertEqual(control_source.replace(old, new, 1), invalid_source)
        r1407 = self.specs["R1407_valid__module_subprogram_without_contains_control"]["source"]
        self.assertEqual(r1407.replace("contains\n", "", 1),
                         self.specs["R1407_invalid__module_subprogram_without_contains"]["source"])
        r1408 = self.specs["R1408_valid__invalid_module_subprogram_control"]["source"]
        self.assertEqual(r1408.replace("subroutine invalid_inside_module", "block data invalid_inside_module", 1)
                              .replace("end subroutine invalid_inside_module",
                                       "end block data invalid_inside_module", 1),
                         self.specs["R1408_invalid__block_data_as_module_subprogram"]["source"])

    def test_sources_exercise_external_and_intrinsic_resolution(self):
        external = self.specs["S14_2_1_005_valid__external_implicit_interface_declarations"]["source"]
        self.assertIn("integer :: abs\n  external :: abs", external)
        self.assertIn("character(len=5) :: ext_word\n  external :: ext_word", external)
        self.assertIn("external_value = abs(-1)", external)
        self.assertIn("external_word_len = len(ext_word())", external)
        intrinsic = self.specs["S14_2_1_006_valid__intrinsic_attribute"]["source"]
        self.assertIn("intrinsic :: abs", intrinsic)
        self.assertIn("via_attribute = abs(-7)", intrinsic)
        intrinsic_use = self.specs["S14_2_1_006_valid__intrinsic_use"]["source"]
        self.assertIn("! intrinsic-use-anchor", intrinsic_use)
        self.assertIn("via_use = abs(-7)", intrinsic_use)

    def test_runtime_mutation_matrix_is_feature_based_and_complete(self):
        runtime = [spec for spec in self.specs.values()
                   if spec["kind"] == "valid" and not spec.get("compile_only")]
        self.assertEqual(len(runtime), 3)
        total = 0
        for spec in runtime:
            self.assertTrue(spec["mutations"])
            for label, old, new in spec["mutations"]:
                self.assertNotEqual(old, new, label)
                self.assertEqual(spec["source"].count(old), 1, label)
                mutant = spec["source"].replace(old, new)
                self.assertNotEqual(generated.sha(mutant.encode("ascii")), spec["source_sha256"])
                self.assertIn("error stop", mutant.lower())
                self.assertIn("print '(a)'", mutant)
                total += 1
        self.assertEqual(total, 7)

    def test_catalogues_remove_generated_facets_and_keep_pending_remainders(self):
        main = self.registry.catalogues[generated.SECTION_MAIN]
        module = self.registry.catalogues[generated.SECTION_MODULE]
        for rule, facets in generated.MAIN_FACETS.items():
            owner = next(row for row in main["requirements"] if row["id"] == rule)
            for facet in facets:
                self.assertNotIn(facet, owner.get("pending", {}))
        for rule, facets in generated.MODULE_FACETS.items():
            owner = next(row for row in module["requirements"] if row["id"] == rule)
            for facet in facets:
                self.assertNotIn(facet, owner.get("pending", {}))
        for rule, facet in [
            ("S14.1-001", "main-program-unit-classification"),
            ("R1402", "program-stmt-with-name"),
            ("S14.2.1-001", "module-contains-declarations-specifications-definitions"),
            ("S14.2.1-002", "public-module-identifiers-use-accessible"),
            ("S14.2.1-003", "nonintrinsic-module-program-unit-defined"),
            ("R1404", "module-program-unit-form"),
            ("R1405", "module-stmt-with-name"),
            ("R1407", "module-subprogram-part-with-contains"),
            ("R1407", "contains-without-module-subprograms"),
            ("R1408", "module-function-subprogram"),
            ("R1408", "module-subroutine-subprogram"),
            ("C1402", "end-module-name-identical"),
        ]:
            catalogue = main if rule.startswith("S14.1") or rule in {"R1402", "R1403"} else module
            self.assertIn(facet, next(row for row in catalogue["requirements"] if row["id"] == rule)["pending"])

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
