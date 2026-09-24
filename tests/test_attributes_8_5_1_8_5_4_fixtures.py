"""Regression checks for the 8.5.1/8.5.2 attribute fixture packet."""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_attributes_8_5_1_8_5_4_fixtures as generated


class Attributes851854FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in all_cases if f"/fixtures/{generated.TOPIC}_" in case.path}

    def test_exact_owned_fixture_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.specs), 6)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 16)
        expectations = {
            "C816": "effect",
            "R807": "positive-control",
            "C817": "positive-control",
            "S8.5.2-001": "effect",
            "S8.5.2-002": "effect",
            "S8.5.2-003": "positive-control",
        }
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, expectations[case.rule])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)

    def test_generated_files_are_byte_exact_ascii_and_hygienic(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob(generated.TOPIC + "_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            text = raw.decode("ascii")
            self.assertTrue(text.endswith("\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, text.splitlines())), 132)
                self.assertNotRegex(text.lower(), r"/tmp|/var/tmp|iomsg|sleep")

    def test_scoped_catalogue_pending_matches_owned_coverage(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        for section in ("8.5.1", "8.5.2"):
            catalogue = self.registry.catalogues[section]
            for req in catalogue["requirements"]:
                if req["id"] not in covered:
                    continue
                expected_pending = set(req["facets"]) - covered.get(req["id"], set())
                self.assertEqual(set(req["pending"]), expected_pending, req["id"])
                if covered.get(req["id"]):
                    self.assertIn(generated.MARKER, req["oracle"])
                    self.assertIn(generated.MARKER, req["oracle_limitation"])

    def test_each_facet_has_distinct_assertion_and_feature_mutant(self):
        for name, spec in self.specs.items():
            source = (ROOT / spec["source_path"]).read_text()
            checks = set(re.findall(r"call check_(?:int|true)\('([^']+)'", source))
            self.assertEqual(len(checks), spec["checks"], name)
            self.assertIn(f"call finish_checks({spec['checks']})", source)
            by_facet = {facet: [] for facet in spec["facets"]}
            for mutant in spec["mutants"]:
                self.assertIn(mutant["facet"], by_facet, name)
                self.assertIn(mutant["assertion"], checks, (name, mutant["id"]))
                changed = source
                for change in mutant.get("changes", [{"old": mutant.get("old"), "new": mutant.get("new")}]):
                    self.assertEqual(changed.count(change["old"]), 1, (name, mutant["id"]))
                    changed = changed.replace(change["old"], change["new"], 1)
                self.assertNotEqual(changed, source, (name, mutant["id"]))
                self.assertIn("program p", changed)
                self.assertNotIn("CHECK_COUNT', 0", changed)
                by_facet[mutant["facet"]].append(mutant["assertion"])
            for facet, assertions in by_facet.items():
                self.assertTrue(assertions, (name, facet))
            representative = {facet: assertions[0] for facet, assertions in by_facet.items()}
            self.assertEqual(len(set(representative.values())), len(representative), name)

    def test_result_shape_inquiries_stay_direct_on_function_expressions(self):
        source = (ROOT / self.specs[f"{generated.TOPIC}_c816_function_results"]["source_path"]).read_text()
        self.assertIn("all(shape(fixed_result()) == [2,3])", source)
        self.assertIn("all(shape(sized_result(4)) == [4])", source)
        self.assertNotRegex(source, r"shape\s*=|shp\s*=")


if __name__ == "__main__":
    unittest.main()
