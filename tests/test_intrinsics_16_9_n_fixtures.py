"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.109-16.9.113."""

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
import generate_intrinsics_16_9_n_fixtures as generated


class Intrinsics169NFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        expected = {generated.identifier(spec["variant"], spec["rule"]) for spec in self.specs.values()}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.files), 34)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 37)
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
            "index_positions_and_kinds": ["kind(index('AB', 'B', kind=ik))", "kind(index('AB', 'B'))"],
            "int_numeric_and_boz": ["kind(int(17, kind=ik))", "kind(int(17))"],
            "ior_bit_model": ["kind(ior(5_ik, 3_ik))", "kind(ior(z'01', 3_ik))"],
            "iparity_characteristics": ["kind(iparity(wide))", "shape(iparity(a))", "shape(iparity(a, dim=1))"],
            "ishft_kind_and_bits": ["kind(ishft(wide, 1))"],
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
            self.assertNotRegex(source, r"(?i)\bcoarray|sync\s+all|ieee_set_flag|ieee_get_flag\b")
            self.assertNotIn("selected_int_kind(18)", source)
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_feature_mutations_bind_complete_parent_sources_and_facets(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 37)
        by_facet = {}
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual({m["facet"] for m in spec["mutations"]}, set(spec["facets"]))
            hashes = set()
            for mutation in spec["mutations"]:
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
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
        for section, catalogue_path in generated.CATALOGUES.items():
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
            for rule, pending in generated.REMAINING_PENDING.items():
                if rule in by_rule:
                    self.assertEqual(set(by_rule[rule].get("pending", {})), set(pending))
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("Unnumbered argument restrictions", view)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
