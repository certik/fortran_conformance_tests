"""Runtime fixture checks for Fortran 2023 IEEE 17.4-17.9 fixtures."""

import json
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_ieee_17_4_17_9_fixtures as generated


class Ieee174179FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_owned_manifests_are_discoverable_and_bound(self):
        expected_ids = {generated.identifier(case["variant"]) for case in generated.CASES}
        self.assertEqual(set(self.cases), expected_ids)
        self.assertEqual(set(self.specs), expected_ids)
        self.assertEqual(len([path for path in self.files if path.name == "fixture.json"]), len(generated.CASES))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertIn(case.fixture.expectation.stdout[0], spec["stdout_options"])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])), requirement)

    def test_sources_are_ieee_arithmetic_only_and_guarded(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            lowered = source.lower()
            self.assertIn("use, intrinsic :: ieee_arithmetic", lowered)
            self.assertNotIn("use, intrinsic :: ieee_exceptions", lowered)
            self.assertNotIn("use, intrinsic :: ieee_features", lowered)
            self.assertNotIn("unsupported ok", lowered)
            if "rounding" in spec["variant"]:
                self.assertIn("ieee_support_rounding", lowered)
            if "underflow" in spec["variant"] or "subnormal" in spec["variant"]:
                self.assertIn("ieee_support", lowered)
            if "tiny(" in lowered or "epsilon(" in lowered:
                self.assertIn("volatile", lowered)

    def test_mutation_plans_bind_complete_parent_sources(self):
        total = 0
        covered = set()
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual({probe["facet"] for probe in spec["probes"]}, set(spec["facets"]), spec["variant"])
            mutated_hashes = set()
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.mutated_source(spec, probe)
                self.assertNotEqual(mutant, raw)
                digest = generated.sha(mutant)
                self.assertNotIn(digest, mutated_hashes)
                mutated_hashes.add(digest)
                covered.add(probe["facet"])
                total += 1
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.mutated_source(changed, spec["probes"][0])
        self.assertEqual(total, len(generated.FEATURE_MUTATION_TABLE))
        self.assertEqual({row[0] for row in generated.FEATURE_MUTATION_TABLE}, covered)
        for _, assertion, mutation in generated.FEATURE_MUTATION_TABLE:
            self.assertTrue(assertion)
            self.assertTrue(mutation)

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
