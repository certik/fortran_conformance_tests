"""Tests for generated Clause 16.9.88-16.9.91 intrinsic fixtures."""

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
import generate_intrinsics_16_9_j_fixtures as generated


class Intrinsics169JFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_generated_case_inventory_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), len(generated.CASES))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])),
                                          self.registry.requirements[case.rule])

    def test_sources_are_exact_or_characteristic_only(self):
        required_tokens = {
            "findloc_result_kind": ["kind(findloc([2, 4], 4))", "kind(findloc([2, 4], 4, kind=ik))"],
            "findloc_no_dim_shape": ["size(shape(findloc(vector, 6)))", "size(findloc(grid, 2))"],
            "findloc_dim_shape": ["size(shape(findloc(vector, 6, dim=1)))", "shape(findloc(grid, 2, dim=1))"],
            "findloc_case_i_values": ["allocate(empty(0))", "findloc(misses, 6)"],
            "findloc_case_ii_mask": ["mask=select_last", "mask=no_match_mask", "false_mask = .false."],
            "findloc_back_order": ["back=.false.", "back=.true.", "reshape([9, 1, 9, 1, 1, 9]"],
            "floor_result_kind": ["kind(floor(3.75))", "kind(floor(3.75, kind=ik))"],
            "floor_exact_values": ["floor(3.75)", "floor(-3.25)", "floor(-3.0)"],
            "fraction_finite_model": ["radix(one)", "fraction(radix_power)"],
            "fraction_ieee_specials": ["ieee_is_nan(nan_result)", "ieee_is_nan(inf_result)"],
            "gamma_elemental": ["shape(gamma(values))", "[1.0, 1.5, -0.5]"],
            "gamma_result_kind": ["kind(gamma(high))", "kind(high)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertIn("  implicit none\n", source)
            self.assertEqual(source.count("checks=checks+1"), spec["checks"])
            self.assertEqual(generated.sha(source.encode("ascii")), spec["source_sha256"])
            self.assertNotRegex(source.lower(), r"transfer\s*\(|c_loc\s*\(|random_number\s*\(")
            if spec["section"] == "16.9.91":
                self.assertNotRegex(source, r"gamma\([^)]*\)\s*[=/]=")
            for token in required_tokens.get(spec["variant"], []):
                self.assertIn(token, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        hashes = set()
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(len(spec["feature_mutations"]), len(spec["facets"]))
            self.assertEqual({mutation["facet"] for mutation in spec["feature_mutations"]}, set(spec["facets"]))
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                hashes.add(generated.sha(mutant))
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["mutations"][0])
        self.assertEqual(len(hashes), sum(len(spec["mutations"]) for spec in self.specs.values()))

    def test_catalogues_sync_and_pending_matches_uncovered_facets(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        for section, rel in generated.CATALOGUES.items():
            data = json.loads((ROOT / rel).read_text())
            synced = generated.synced_catalogue(section, data, self.specs)
            self.assertEqual(synced, data)
            view = generated.render_view(section, synced, ROOT)
            self.assertIn(f"<!-- BEGIN INTRINSICS 16.9.J FIXTURES {section} -->", view)
            for requirement in data["requirements"]:
                if requirement["id"].startswith("S" + section + "-"):
                    missing = set(requirement["facets"]) - covered.get(requirement["id"], set())
                    self.assertEqual(missing, set(requirement.get("pending", {})), requirement["id"])
                    if requirement["id"] in generated.FACETS_BY_RULE:
                        self.assertIn(f"{requirement['id']} {generated.TOPIC} runtime fixture: ",
                                      requirement.get("oracle", ""))
                        self.assertIn(f"{requirement['id']} {generated.TOPIC} fixture boundaries: ",
                                      requirement.get("oracle_limitation", ""))

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
