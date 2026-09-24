"""Tests for generated Clause 16.9.59-16.9.66 intrinsic fixtures."""

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
import generate_intrinsics_16_9_f_fixtures as generated


class Intrinsics169FFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_generated_case_inventory_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 16)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 27)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 27)
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

    def test_sources_use_direct_inquiries_and_exact_oracles(self):
        required = {
            "command_argument_count_no_args": ["kind(command_argument_count())"],
            "command_argument_count_no_args_value": ["observed = command_argument_count()", "command_name_control = command_argument_count()"],
            "conjg_characteristics": ["conjg(scalar_z)", "conjg(vector_z)", "shape(conjg(vector_z))"],
            "cos_characteristics": ["cos(real_x)", "cos(complex_x)", "shape(cos(real_x))"],
            "cosd_characteristics": ["cosd(x)", "shape(cosd(x))"],
            "cosh_characteristics": ["cosh(real_x)", "cosh(complex_x)", "shape(cosh(complex_x))"],
            "cospi_elemental": ["size(cospi(x))", "shape(cospi(x))"],
            "cospi_argument": ["kind(cospi(x))"],
            "cospi_characteristics": ["kind(cospi(scalar_x))", "shape(cospi(vector_x))"],
            "count_characteristics": ["kind(count(mask1, kind=IK))", "kind(count(mask1))", "size(shape(count(mask1)))", "size(count(mask2, dim=1))"],
            "count_values": ["count(empty)", "count(companion) == 2", "count(mask2, dim=2) == [2, 1]"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count(spec["completion"].rstrip()), 1)
            self.assertEqual(generated.sha(source.encode("ascii")), spec["source_sha256"])
            self.assertNotRegex(source.lower(), r"transfer\s*\(|loc\s*\(|c_loc\s*\(")
            if spec["section"] in {"16.9.61", "16.9.62", "16.9.63", "16.9.65"}:
                self.assertNotIn("0.54030231", source)
                self.assertNotIn("1.5430806", source)
                self.assertNotIn("== 1.0d0", source)
                self.assertNotIn("== cmplx(1.0d0, 0.0d0", source)
            for token in required.get(spec["variant"], []):
                self.assertIn(token, source)

    def test_mutations_are_facet_specific_and_bind_parent_sources(self):
        hashes = set()
        for spec in self.specs.values():
            self.assertEqual({mutation["facet"] for mutation in spec["mutations"]}, set(spec["facets"]))
            raw = spec["source"].encode("ascii")
            for mutation in spec["mutations"]:
                self.assertEqual(mutation["kind"], "feature")
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutate_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                self.assertEqual(generated.sha(mutant), mutation["source_sha256"])
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
                    self.assertEqual(missing, set(requirement.get("pending", {})), requirement["id"])

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
