"""Regression checks for the Clause 12.6.2.1 I/O control-list fixture packet."""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_io_control_list_12_6_2_1_fixtures as generated


class IoControlListFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in all_cases if f"/fixtures/{generated.TOPIC}_" in case.path}

    def test_exact_owned_fixture_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertGreaterEqual(len(self.specs), 100)
        covered = {(spec["rule"], facet) for spec in self.specs.values() for facet in spec["facets"]}
        self.assertGreaterEqual(len(covered), 70)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            if spec["kind"] == "valid":
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.exit_code, 0)
            else:
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")
                self.assertIn("control", spec)

    def test_generated_files_are_byte_exact_ascii_and_hygienic(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob(generated.TOPIC + "_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            text = raw.decode("ascii")
            self.assertTrue(text.endswith("\n"))
            self.assertNotRegex(text.lower(), r"/tmp|/var/tmp")
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, text.splitlines()), default=0), 132)
                self.assertNotRegex(text.lower(), r"iomsg\s*(?:==|/=)")

    def test_scoped_catalogue_pending_matches_authored_coverage(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        catalogue = self.registry.catalogues["12.6.2.1"]
        for req in catalogue["requirements"]:
            expected_pending = set(req["facets"]) - covered.get(req["id"], set())
            self.assertEqual(set(req["pending"]), expected_pending, req["id"])
            if covered.get(req["id"]):
                self.assertIn("I/O control-list fixture implementation:", req["oracle"])

    def test_runtime_mutants_are_unique_feature_changes(self):
        total_feature = 0
        for name, spec in self.specs.items():
            if spec["kind"] != "valid" or spec["evidence"] != "effect":
                continue
            source = (ROOT / spec["source_path"]).read_text()
            checks = len(re.findall(r"\bcall check_(?:int|char|true|nonzero)\(", source))
            self.assertEqual(checks, spec["checks"], name)
            self.assertIn(f"call finish_checks({spec['checks']})", source)
            feature = [m for m in spec["mutants"] if m["category"] == "feature"]
            self.assertGreaterEqual(len(feature), len(spec["facets"]), name)
            read_targets = re.findall(r"(?im)^\s*read\s*\(.*\)\s+[A-Za-z]\w*\s*$", source)
            sentinel = [m for m in spec["mutants"] if m["category"] == "sentinel"]
            self.assertEqual(len(sentinel), 3 * len(read_targets), name)
            for line in read_targets:
                target = line.split()[-1]
                self.assertRegex(source, rf"call check_int\('pre-read-[0-9]+-{target}', {target}, -7[0-9]{{3}}\)")
            seen = set()
            for mutant in spec["mutants"]:
                self.assertNotIn(mutant["id"], seen)
                seen.add(mutant["id"])
                self.assertEqual(source.count(mutant["old"]), 1, (name, mutant["id"]))
                self.assertNotEqual(source.replace(mutant["old"], mutant["new"], 1), source)
            total_feature += len(feature)
        self.assertGreaterEqual(total_feature, 10)

    def test_diagnostics_are_line_anchored_and_have_controls(self):
        valid_names = {name for name, spec in self.specs.items() if spec["kind"] == "valid"}
        for name, spec in self.specs.items():
            if spec["kind"] != "invalid":
                continue
            self.assertIn(spec["control"], valid_names, name)
            fixture = self.cases[name].fixture.expectation.diagnostic
            self.assertEqual(fixture["file"], "source.f90")
            self.assertGreaterEqual(fixture["line"], 1)
            self.assertFalse(fixture.get("contains_any"))
            self.assertIn("internal compiler error", fixture.get("excludes_any", []))


if __name__ == "__main__":
    unittest.main()
