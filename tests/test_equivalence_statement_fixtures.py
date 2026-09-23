"""Finite EQUIVALENCE storage-association fixture packet checks."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, render_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_equivalence_statement_fixtures as generated


class EquivalenceStatementFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        fixture_paths = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in fixture_paths}

    def test_exact_packet_scope_and_manifest_contract(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.specs), 11)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 17)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 30)
        self.assertEqual(len(self.files), 22)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)

    def test_generated_files_are_byte_exact_ascii_and_bounded(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("equivalence_statement_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            text = raw.decode("ascii")
            self.assertTrue(text.endswith("\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, text.splitlines())), 132)
                self.assertIn("module equivalence_statement_checks", text)
                self.assertIn("call finish_checks(", text)
                self.assertNotRegex(text.lower(), r"\b(?:transfer|storage_size|c_loc|equivalence\s*::)\b")
                self.assertNotIn("case_count", text.lower())

    def test_each_fixture_has_defined_prestate_and_conforming_feature_mutants(self):
        for spec in self.specs.values():
            source = spec["source"]
            self.assertEqual(source.count("call finish_checks("), 1)
            self.assertIn(f"call finish_checks({spec['expected_check_count']})", source)
            self.assertTrue(any(m["kind"] == "remove-equivalence" for m in spec["mutations"]))
            self.assertRegex(source, r"call check_(?:integer|character|logical)\('[^']+-pre")
            for line in spec["equivalences"]:
                self.assertEqual(source.count(line), 1)
            for mutation in spec["mutations"]:
                mutant = spec["mutation_sources"][mutation["id"]]
                self.assertNotEqual(mutant, source)
                mutant.encode("ascii")
                self.assertIn("call finish_checks(", mutant)
                if mutation["kind"] == "remove-equivalence":
                    for line in spec["equivalences"]:
                        self.assertNotIn(line, mutant)
                else:
                    self.assertIn(mutation["replacement"], mutant)
                    self.assertNotIn(mutation["expected"], mutant)

    def test_catalogue_pending_entries_match_direct_case_coverage(self):
        catalogue = json.loads((ROOT / generated.CATALOGUE).read_text())
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        selected = generated.selected_facets()
        for row in catalogue["requirements"]:
            if row["id"] in selected:
                self.assertFalse(selected[row["id"]] & set(row["pending"]))
                self.assertIn(generated.ORACLE_PREFIX, row["oracle"])
                self.assertIn(generated.LIMIT_PREFIX, row["oracle_limitation"])
        rendered = generated.render_view(catalogue, ROOT)
        self.assertEqual((ROOT / generated.VIEW).read_text(), rendered)
        for row in catalogue["requirements"]:
            self.assertIn(render_requirement(row), rendered)


if __name__ == "__main__":
    unittest.main()
