"""Tests for generated Clause 16.9.22-16.9.27 intrinsic fixtures."""

import json
from pathlib import Path
import sys
import unittest
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_intrinsics_16_9_d_fixtures as generated


class Intrinsics169DFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_generated_case_inventory_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 15)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 18)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 19)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])), requirement)

    def test_sources_are_bounded_and_source_derived(self):
        required_tokens = {
            "atan2_values": ["pos_value = atan2(y_pos, x_neg)", "zero_value == y_zero"],
            "atand_values": ["observed = atand(y, x)", "reference = atan2d(y, x)"],
            "atanh_complex_range": ["x = cmplx(0.0_RK, 2.0_RK, kind=RK)", "y = atanh(x)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertIn("  implicit none\n", source)
            self.assertEqual(source.count(spec["completion"].rstrip()), 1)
            self.assertEqual(generated.sha(source.encode("ascii")), spec["source_sha256"])
            self.assertNotRegex(source.lower(), r"transfer\s*\(|loc\s*\(|c_loc\s*\(")
            for token in required_tokens.get(spec["variant"], []):
                self.assertIn(token, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        hashes = set()
        for spec in self.specs.values():
            self.assertGreaterEqual(len(spec["mutations"]), len(spec["facets"]))
            raw = spec["source"].encode("ascii")
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutate_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertEqual(generated.sha(mutant), mutation["source_sha256"])
                self.assertNotEqual(mutant, raw)
                hashes.add(mutation["source_sha256"])
        self.assertEqual(len(hashes), sum(len(spec["mutations"]) for spec in self.specs.values()))

    def test_catalogue_pending_matches_uncovered_target_facets(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        for section, rel in generated.CATALOGUES.items():
            data = json.loads((ROOT / rel).read_text())
            for requirement in data["requirements"]:
                if requirement["id"].startswith("S" + section + "-"):
                    missing = set(requirement["facets"]) - covered.get(requirement["id"], set())
                    self.assertEqual(missing, set(requirement["pending"]), requirement["id"])


if __name__ == "__main__":
    unittest.main()
