"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.101-16.9.106."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_intrinsics_16_9_m_fixtures as generated


class Intrinsics169MFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        expected = {generated.identifier(spec["variant"], spec["rule"]) for spec in self.specs.values()}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.files), 38)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 30)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images), ("f2023", "standard", 1))
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.profiles, spec.get("profiles", []))
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])

    def test_sources_are_bounded_and_use_direct_result_inquiries(self):
        anchors = {
            "iany_result_kind": ["kind(iany(wide))"],
            "iany_scalar_result": ["size(shape(iany([1, 2, 4])))"],
            "iany_dim_shape": ["shape(iany(grid, dim=1))"],
            "ibclr_kind": ["kind(ibclr(7_ik, 1))"],
            "ibclr_bits": ["btest(r, z - 1)"],
            "ibits_kind": ["kind(ibits(7_ik, 1, 2))"],
            "ibits_bits": ["ibits(ibset(0, z - 1), z - 1, 1) == 1"],
            "ibset_kind": ["kind(ibset(7_ik, 1))"],
            "ibset_bits": ["btest(r, z - 1)"],
            "ichar_kinds": ["kind(ichar('A', kind=ik))", "kind(ichar('A'))"],
            "ieor_kind": ["kind(ieor(z'01', 3_ik))"],
            "ieor_boz": ["left = ieor(z'0F', 10_ik)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn(f"if (checks /= {len(spec['facets'])})", source)
            self.assertNotRegex(source.lower(), r"transfer\s*\(|loc\s*\(|c_loc\s*\(|coarray|sync\s+all")
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_feature_mutations_bind_complete_parent_sources_and_facets(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 30)
        by_facet = {}
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual({m["facet"] for m in spec["mutations"]}, set(spec["facets"]))
            for mutation in spec["mutations"]:
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                self.assertEqual(mutation["kind"], "source")
                self.assertEqual(mutation["category"], "feature")
                by_facet.setdefault((spec["rule"], mutation["facet"]), set()).add(mutation["id"])
                expected = raw
                for start, end, old, new in reversed(mutation["spans"]):
                    self.assertEqual(raw[start:end].decode("ascii"), old)
                    expected = expected[:start] + new.encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
        selected_facets = {(rule, facet) for rule, (_, facets) in generated.SELECTED.items() for facet in facets}
        self.assertEqual(set(by_facet), selected_facets)

    def test_catalogues_remove_only_selected_facets_and_regenerate_views(self):
        for section in generated.CATALOGUES:
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, (_, facets) in generated.SELECTED.items():
                if rule not in by_rule:
                    continue
                row = by_rule[rule]
                for facet in facets:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], row["oracle_limitation"])
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("processor-dependent native character positions remain pending", view)
        for rule, pending in generated.REMAINING_PENDING.items():
            self.assertEqual(set(self.registry.requirements[rule].get("pending", {})), set(pending))

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
