"""Regression checks for Clause 12.3 positioning/storage and 12.4 internal-file fixtures."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_io_positioning_internal_12_3_12_4_fixtures as generated


class IoPositioningInternalFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}

    def test_owned_fixture_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len({spec["variant"] for spec in self.specs.values()}), 12)
        self.assertEqual(len(self.specs), 12)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 21)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images), ("f2023", "standard", 1))
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])

    def test_generated_files_are_byte_exact_and_hygienic(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob(generated.TOPIC + "_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            text = raw.decode("ascii")
            self.assertTrue(text.endswith("\n"))
            self.assertNotRegex(text.lower(), r"/tmp|/var/tmp|iomsg")
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, text.splitlines())), 132)
                self.assertIn("call finish(", text)
                self.assertEqual(len(re.findall(r"(?m)^program ", text)), 1)
                self.assertEqual(len(re.findall(r"(?m)^end program ", text)), 1)
                if "open(newunit" in text:
                    self.assertIn("status='delete'", text)
                if "read(" in text.lower() and "read(u" in text.lower():
                    self.assertRegex(text, r"call check_(?:int|char)\('pre-")

    def test_catalogues_are_synchronized_for_selected_facets(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        for section, rel in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(section, catalogue, self.specs), catalogue)
            for req in catalogue["requirements"]:
                expected_pending = set(req["facets"]) - covered.get(req["id"], set())
                self.assertEqual(set(req.get("pending", {})), expected_pending, req["id"])
                if covered.get(req["id"]):
                    self.assertIn("I/O positioning/internal runtime fixtures:", req["oracle"])
                    self.assertIn("I/O positioning/internal fixture boundaries:", req["oracle_limitation"])
            view = generated.render_view(section, catalogue, self.specs)
            self.assertEqual((ROOT / generated.VIEWS[section]).read_text(), view)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("Deferred-length allocatable internal WRITE facets remain pending", view)

    def test_mutation_spans_bind_parent_sources(self):
        self.assertEqual(len({spec["source_sha256"] for spec in self.specs.values()}), len(self.specs))
        total = 0
        for spec in self.specs.values():
            source = spec["source"]
            raw = source.encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["mutations"]), 3)
            categories = {mutation["category"] for mutation in spec["mutations"]}
            self.assertIn("feature", categories)
            for mutation in spec["mutations"]:
                total += 1
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutated = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutated, raw)
                self.assertIn(b"program fixture_", mutated)
        self.assertEqual(total, 118)

    def test_generation_check_mode_is_read_only(self):
        generated.check_files(self.files, self.specs)
        before = {path: path.read_bytes() for path in self.files}
        generated.sync_files(self.files, self.specs)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
