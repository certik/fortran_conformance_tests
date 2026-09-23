"""Fixture metadata for Fortran 2023 type-declaration statements in 8.2."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_type_declaration_fixtures as generated


class TypeDeclarationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_cases_and_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 17)
        self.assertEqual(len(self.files), 34)
        selected = {rule: set(facets) for rule, facets in generated.SELECTED.items()}
        covered = {}
        for case in self.cases.values():
            covered.setdefault(case.rule, set()).update(case.meta.facets)
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            validate_case_requirement(case, self.registry.requirements[case.rule], case.rule in self.registry.numbered)
        self.assertEqual(covered, selected)

    def test_invalid_cases_are_line_anchored_diagnostics_with_controls(self):
        controls = {
            "C804_invalid__type_declaration_c804_noncharacter_star_length":
                "C804_valid__type_declaration_c804_character_star_length_control",
            "C806_invalid__type_declaration_c806_initializer_without_colons":
                "C806_valid__type_declaration_c806_initializer_with_colons_control",
            "C807_invalid__type_declaration_c807_missing_initializer":
                "C807_valid__type_declaration_c807_all_initialized_control",
            "C808_invalid__type_declaration_c808_allocatable_initializer":
                "C808_valid__type_declaration_c808_allocatable_no_initializer_control",
        }
        self.assertEqual({name for name, case in self.cases.items() if case.kind == "invalid"}, set(controls))
        for invalid_id, control_id in controls.items():
            invalid = self.cases[invalid_id]
            control = self.cases[control_id]
            self.assertEqual(invalid.fixture.expectation.outcome, "diagnose")
            self.assertEqual(control.fixture.expectation.outcome, "success")
            self.assertEqual(control.fixture.expectation.phase, "run" if control.fixture.link else "compile")
            self.assertEqual(invalid.rule, control.rule)
            self.assertTrue(set(invalid.meta.facets) & set(control.meta.facets)
                            or invalid.rule == "C804" or invalid.rule == "C807")
            diagnostic = invalid.fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                             ("source.f90", self.specs[invalid_id].get("line"), self.specs[invalid_id].get("line")))
            self.assertEqual(diagnostic["contains_any"], self.specs[invalid_id]["messages"])
            self.assertEqual(diagnostic["excludes_any"], generated.EXCLUSIONS)

    def test_runtime_sources_have_len_before_character_equality_and_feature_mutations(self):
        runtime = [spec for spec in self.specs.values() if spec["manifest"]["expect"]["phase"] == "run"]
        self.assertEqual(len(runtime), 13)
        mutation_count = sum(len(generated.all_mutations(spec)) for spec in runtime)
        self.assertEqual(mutation_count, 28)
        for spec in runtime:
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertIn("print '(a)'", source)
            self.assertEqual(spec["manifest"]["expect"]["stdout"], spec["completion"])
            for mutation in generated.all_mutations(spec):
                start, end = mutation["span"]
                raw = source.encode("ascii")
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                self.assertNotEqual(generated.mutated_source(spec, mutation), raw)
        for spec in runtime:
            if "character" in spec["stem"] or "length" in spec["stem"] or "initializer_values" in spec["stem"]:
                self.assertLess(source_order(spec["source"], "len("), source_order(spec["source"], " /= '"))
        s004 = self.specs["S8_2_004_valid__type_declaration_s004_initializer_values"]
        self.assertIn("remove_logical_initializer", {row["id"] for row in generated.all_mutations(s004)})
        self.assertIn("change_logical_initializer", {row["id"] for row in generated.all_mutations(s004)})

    def test_catalogue_sync_removes_only_selected_pending_facets(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertIn("nonconstant-initializer", by_rule["R805"].get("pending", {}))
        self.assertIn("C1012", by_rule["R805"]["pending"]["nonconstant-initializer"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


def source_order(source, needle):
    index = source.find(needle)
    return 10**9 if index < 0 else index


if __name__ == "__main__":
    unittest.main()
