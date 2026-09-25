"""Batch320 fixture-packet checks for Fortran 2023 8.6.12-8.6.17 attribute statements."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import generate_attribute_statements_8_6_b_fixtures as generated
import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement


class AttributeStatements86BFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_cases_and_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 23)
        self.assertEqual(len(self.files), 46)
        covered = {}
        for case in self.cases.values():
            covered.setdefault(case.rule, set()).update(case.meta.facets)
            validate_case_requirement(case, self.registry.requirements[case.rule])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
        expected = {}
        for section in generated.SELECTED.values():
            for rule, facets in section.items():
                expected.setdefault(rule, set()).update(facets)
        self.assertEqual(covered, expected)

    def test_valid_and_invalid_manifest_contracts(self):
        for name, spec in self.specs.items():
            case = self.cases[name]
            if spec["kind"] == "valid":
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("run", "success"))
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                self.assertIn(self.members[name]["cohort"], {"runtime-effect", "positive-control"})
            else:
                self.assertEqual(case.kind, "invalid")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "diagnose"))
                diagnostic = case.fixture.expectation.diagnostic
                self.assertEqual(diagnostic["file"], "source.f90")
                self.assertEqual(diagnostic["line"], diagnostic["end_line"])
                self.assertEqual(diagnostic["excludes_any"], list(generated.EXCLUSIONS))
                self.assertEqual(self.members[name]["cohort"], "diagnostic-only")

    def test_sources_are_ascii_portable_and_statement_specific(self):
        required = {
            "R857_valid__attribute_statements_8_6_b_pointer_rank_two_deferred_shape": ["pointer :: p(:,:)", "rank(p) /= 2"],
            "R858_valid__attribute_statements_8_6_b_protected_declarator_control": ["protected :: a", "a(1) = v"],
            "R863_valid__attribute_statements_8_6_b_target_inline_array_shape": ["target :: values(3), matrix(0:1,2)", "rank(matrix)"],
            "R864_valid__attribute_statements_8_6_b_value_copy_double_colon": ["value :: x, y", "if (a /= 3)"],
            "R865_invalid__attribute_statements_8_6_b_volatile_designator": ["volatile :: a(1)"],
        }
        for name, spec in self.specs.items():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec["kind"] == "valid":
                self.assertIn("write(*,'(a)')", source)
                self.assertNotRegex(source, r"(?i)\b(error stop 0| = 0\n)\b")
        for name, needles in required.items():
            source = self.specs[name]["source"]
            for needle in needles:
                self.assertIn(needle, source)

    def test_diagnostic_repairs_are_one_property_controls(self):
        repairs = {
            "R858_invalid__attribute_statements_8_6_b_protected_missing_list": ("protected ::", "protected :: x"),
            "R858_invalid__attribute_statements_8_6_b_protected_declarator_suffix": ("protected :: a(:)", "protected :: a"),
            "C893_invalid__attribute_statements_8_6_b_save_bare_and_listed": ("  save :: x\n", ""),
            "R864_invalid__attribute_statements_8_6_b_value_missing_list": ("    value", "    value x"),
            "R864_invalid__attribute_statements_8_6_b_value_single_colon": ("    value : x", "    value :: x"),
            "R864_invalid__attribute_statements_8_6_b_value_missing_comma": ("    value :: x y", "    value :: x, y"),
            "R865_invalid__attribute_statements_8_6_b_volatile_missing_list": ("  volatile", "  volatile x"),
            "R865_invalid__attribute_statements_8_6_b_volatile_single_colon": ("  volatile : x", "  volatile :: x"),
            "R865_invalid__attribute_statements_8_6_b_volatile_missing_comma": ("  volatile :: x y", "  volatile :: x, y"),
            "R865_invalid__attribute_statements_8_6_b_volatile_designator": ("volatile :: a(1)", "volatile :: a"),
        }
        for name, (bad, good) in repairs.items():
            spec = self.specs[name]
            control = self.specs[spec["repair"]["control_id"]]
            repaired = spec["source"].replace(bad, good, 1)
            self.assertEqual(repaired, control["source"])
            self.assertEqual(spec["repair"]["control_sha256"], control["source_sha256"])

    def test_mutation_definitions_are_load_bearing_and_conforming(self):
        total = sum(len(spec["mutations"]) for spec in self.specs.values() if spec["kind"] == "valid")
        self.assertEqual(total, 14)
        for spec in self.specs.values():
            self.assertEqual(generated.sha(spec["source"].encode("ascii")), spec["source_sha256"])
            for mutation in spec["mutations"]:
                self.assertTrue(mutation.get("conforming"))
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, spec["source"].encode("ascii"))
                text = spec["source"]
                for expected, replacement in mutation["replacements"]:
                    self.assertEqual(text.count(expected), 1)
                    text = text.replace(expected, replacement, 1)
                self.assertEqual(text.encode("ascii"), mutant)

    def test_catalogues_and_views_are_synchronised(self):
        for section, path in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.SELECTED[section].items():
                row = by_rule[rule]
                for facet in facets:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIX[rule], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIX[rule], row["oracle_limitation"])
            synced = generated.synced_catalogue(section, catalogue)
            self.assertEqual(synced, catalogue)
            view = generated.render_view(section, synced)
            self.assertIn(generated.SUMMARY_BEGIN[section], view)
            self.assertIn(generated.SUMMARY_END[section], view)
            for row in synced["requirements"]:
                self.assertIn(render_requirement(row), view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)


if __name__ == "__main__":
    unittest.main()
