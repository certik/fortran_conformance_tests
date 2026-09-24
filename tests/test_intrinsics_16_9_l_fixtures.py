"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.96-16.9.100."""

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
import generate_intrinsics_16_9_l_fixtures as generated


class Intrinsics169LFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.specs), 19)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 39)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images), ("f2023", "standard", 1))
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])

    def test_sources_are_bounded_and_use_direct_intrinsic_inquiries(self):
        anchors = {
            "huge_result_characteristics": ["size(shape(huge(wide)))", "kind(huge(wide))"],
            "huge_integer_model": ["integer_huge_model(0)", "huge(0_ik) == model_wide"],
            "huge_real_model": ["exponent(huge(0.0))", "fraction(huge(x))"],
            "hypot_result_characteristics": ["kind(hypot(x, y)) == kind(x)"],
            "iachar_result_characteristics": ["type_code(iachar('A'))", "kind(iachar('A', kind=ik))"],
            "iachar_ascii_positions": ["iachar(' ') == 32", "iachar('X') == 88"],
            "iall_result_characteristics": ["kind(iall(wide))", "shape(iall(a2, dim=1))"],
            "iall_full_reduction": ["btest(iall([14, 13, 11]), 3)", "btest(not(0), bit_size(0)-1)"],
            "iand_truth_table": ["got = iand(left, right)", ".not. btest(got, 2)"],
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
            self.assertNotRegex(source, r"(?i)transfer\s*\(|storage_size\s*\(|loc\s*\(|c_loc\s*\(")
            self.assertNotRegex(source, r"(?i)\bhypot\s*\([^)]*\)\s*==\s*[0-9]")
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_feature_mutations_bind_complete_parent_sources_and_facets(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 39)
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
                by_facet.setdefault((spec["rule"], mutation["facet"]), set()).add(mutation["id"])
                expected = raw
                for start, end, old, new in reversed(mutation["spans"]):
                    self.assertEqual(raw[start:end].decode("ascii"), old)
                    expected = expected[:start] + new.encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
        selected_facets = {(rule, facet) for rule, (_, facets) in generated.SELECTED.items() for facet in facets}
        self.assertEqual(set(by_facet), selected_facets)

    def test_catalogues_remove_selected_facets_and_preserve_known_pending(self):
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
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue, ROOT)
            self.assertIn(generated.SUMMARY_BEGIN, view)
        pending = self.registry.requirements
        self.assertEqual(set(pending["S16.9.96-005"].get("pending", {})),
                         {"HUGE-enumeration-last-enumerator", "HUGE-enumeration-singleton-last-enumerator"})
        self.assertEqual(set(pending["S16.9.97-003"].get("pending", {})),
                         {"HYPOT-euclidean-distance-processor-dependent-approximation"})
        self.assertEqual(set(pending["S16.9.97-004"].get("pending", {})),
                         {"HYPOT-without-undue-overflow-underflow"})
        self.assertEqual(set(pending["S16.9.98-004"].get("pending", {})),
                         {"IACHAR-non-ASCII-result-processor-dependent"})
        self.assertEqual(set(pending["S16.9.100-001"].get("pending", {})),
                         {"IAND-integer-kinds-match", "IAND-not-both-boz"})

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
