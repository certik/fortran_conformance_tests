"""Regression checks for the Clause 12.3 access/position fixture packet."""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_io_access_position_12_3_fixtures as generated


class IoAccessPositionFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in all_cases if f"/fixtures/{generated.TOPIC}_" in case.path}

    def test_exact_owned_fixture_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.specs), 21)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 38)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, "effect")
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
                lower = text.lower()
                self.assertTrue("status='scratch'" in lower or "status='replace'" in lower)
                self.assertIn("status='delete'", lower)
                self.assertNotRegex(lower, r"/tmp|/var/tmp|iomsg")

    def test_scoped_catalogue_pending_matches_authored_coverage(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        for section, rel in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            for req in catalogue["requirements"]:
                expected_pending = set(req["facets"]) - covered.get(req["id"], set())
                self.assertEqual(set(req["pending"]), expected_pending, req["id"])
                if covered.get(req["id"]):
                    self.assertIn("Access-position fixture implementation:", req["oracle"])

    def test_sources_have_expected_guard_counts_and_portable_iostat_policy(self):
        for name, spec in self.specs.items():
            source = (ROOT / spec["source_path"]).read_text()
            checks = len(re.findall(r"\bcall check_(?:int|char|true)\(", source))
            self.assertEqual(checks, spec["checks"], name)
            self.assertIn(f"call finish_checks({spec['checks']})", source)
            self.assertNotRegex(source, r"check_int\([^\n]*ios,[^\n]*(?:-[0-9]|[1-9][0-9])\)")
            self.assertNotIn("iostat_eor", source.lower())

    def test_mutants_are_unique_conforming_feature_changes(self):
        all_mutants = []
        for name, spec in self.specs.items():
            source = (ROOT / spec["source_path"]).read_text()
            self.assertGreaterEqual(len(spec["mutants"]), len(spec["facets"]))
            seen = set()
            for mutant in spec["mutants"]:
                self.assertNotIn(mutant["id"], seen)
                seen.add(mutant["id"])
                self.assertEqual(source.count(mutant["old"]), 1, (name, mutant["id"]))
                changed = source.replace(mutant["old"], mutant["new"], 1)
                self.assertNotEqual(changed, source, (name, mutant["id"]))
                self.assertIn("program p", changed)
                all_mutants.append((name, mutant["id"]))
        self.assertGreaterEqual(len(all_mutants), 38)


if __name__ == "__main__":
    unittest.main()
