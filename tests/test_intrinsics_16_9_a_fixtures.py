"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.2-16.9.10."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry


sys.path.insert(0, str(ROOT / "tools"))
import generate_intrinsics_16_9_a_fixtures as generated


class Intrinsics169AFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        expected = {generated.identifier(variant) for variant in generated.VARIANTS}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.files), 56)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 38)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images), ("f2023", "standard", 1))
            self.assertFalse(case.meta.coarray or case.meta.profiles or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])

    def test_sources_are_bounded_and_avoid_transcendental_exactness(self):
        required_anchors = {
            "abs_integer_real_values": ["neg_i = -7", "neg_r = -2.0", "abs(neg_i)", "abs(neg_r)"],
            "achar_ascii_mapping": ["achar(88)", "achar(48)", "achar(65)", "achar(122)"],
            "acos_result_ranges": ["rr >= 0.0_rk .and. rr <= 4.0_rk", "real(rz) >= 0.0_rk"],
            "acosd_result_range": ["y >= 0.0_rk .and. y <= 180.0_rk"],
            "acosh_complex_ranges": ["real(r) >= 0.0_rk", "aimag(r) >= -4.0_rk .and. aimag(r) <= 4.0_rk"],
            "acospi_result_range": ["y >= 0.0_rk .and. y <= 1.0_rk"],
            "adjustl_blank_movement": ["s = '  AB#'", "adjustl(s)", "verify(r, ' ')", "r(4:5) /= '  '"],
            "adjustr_blank_movement": ["s = 'AB#  '", "adjustr(s)", "verify(r, ' ', back=.true.)", "r(1:2) /= '  '"],
            "aimag_imaginary_component": ["z = cmplx(2.0_rk, -3.0_rk", "aimag(z)", "-3.0_rk"],
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
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\bcoarray|sync\s+all|ieee_set_flag|ieee_get_flag\b")
            if spec["variant"].startswith(("acos", "acosh")):
                self.assertNotRegex(source, r"(?i)(acos|acosd|acosh|acospi)\s*\([^\n]*\)\s*==")
                self.assertNotRegex(source, r"(?i)==\s*(acos|acosd|acosh|acospi)\s*\(")
            for needle in required_anchors.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        total = sum(len(spec["mutations"]) for spec in self.specs.values())
        self.assertEqual(total, 244)
        feature_mutations = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["observations"]), 1)
            hashes = set()
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.wrong_oracle_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                feature_mutations += mutation["kind"] == "source"
        self.assertEqual(feature_mutations, 48)

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
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("Processor-dependent approximations", view)

    def test_known_remaining_pending_boundaries(self):
        expected_pending = {
            "S16.9.2-004": {"abs-complex-magnitude-processor-dependent-approximation"},
            "S16.9.2-005": {"abs-complex-magnitude-avoids-undue-overflow-underflow"},
            "S16.9.3-001": {"achar-kind-argument-scalar-integer-constant"},
            "S16.9.3-002": {
                "achar-result-kind-from-kind-argument",
                "achar-result-default-character-kind-when-kind-absent"},
            "S16.9.3-004": {"achar-outside-representable-range-processor-dependent"},
            "S16.9.4-003": {"acos-processor-dependent-approximation"},
            "S16.9.5-003": {"acosd-processor-dependent-approximation"},
            "S16.9.6-003": {"acosh-processor-dependent-approximation"},
            "S16.9.7-003": {"acospi-processor-dependent-approximation"},
            "S16.9.8-004": {"result-same-kind"},
            "S16.9.9-004": {"result-same-kind"},
        }
        for rule, pending in expected_pending.items():
            row = self.registry.requirements[rule]
            self.assertEqual(set(row.get("pending", {})), pending)
        self.assertEqual(set(self.registry.requirements["S16.9.1-001"].get("pending", {})),
                         {"subroutine-argument-assigned-value-representable", "function-result-value-representable"})
        self.assertEqual(set(self.registry.requirements["S16.9.1-002"].get("pending", {})),
                         {"deferred-length-character-argument-reallocation", "deferred-length-character-argument-value"})
        self.assertEqual(set(self.registry.requirements["S16.9.1-003"].get("pending", {})),
                         {"ieee-infinity-result-signals-overflow-or-divide-by-zero",
                          "ieee-nan-result-signals-invalid-when-supported",
                          "ieee-flags-unchanged-without-infinity-or-nan"})

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
