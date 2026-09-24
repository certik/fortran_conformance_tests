"""Generated runtime fixtures for Fortran 2023 intrinsic procedures 16.9.67-16.9.70."""

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
import generate_intrinsics_16_9_g_fixtures as generated


class Intrinsics169GFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.profile_files = generated.profile_files()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        expected = {generated.identifier(spec["rule"], spec["variant"]) for spec in generated.source_specs().values()}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.files), 42)
        self.assertEqual(len(self.profile_files), 12)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 30)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 51)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
        expected_profiles = {
            "date_and_time_subroutine_call": ["date-and-time-date-available"],
            "date_and_time_date_digits": ["date-and-time-date-available"],
            "date_and_time_time_digits": ["date-and-time-time-available"],
            "date_and_time_zone_digits": ["date-and-time-zone-available"],
            "date_and_time_values_ranges": [
                "date-and-time-values-1-available", "date-and-time-values-2-available",
                "date-and-time-values-3-available", "date-and-time-values-4-available",
                "date-and-time-values-5-available",
                "date-and-time-values-6-available", "date-and-time-values-7-available",
                "date-and-time-values-8-available", "date-and-time-zone-available"],
        }
        for spec in self.specs.values():
            if spec["variant"].startswith("date_and_time_"):
                self.assertEqual(spec["profiles"], expected_profiles[spec["variant"]])

    def test_sources_use_only_portable_or_profiled_oracles(self):
        anchors = {
            "cshift_rank_two_sections": ["shift=-1, dim=2", "shift=[-1, 1, 0]", "expected(2,:) = [5, 6, 4]"],
            "cshift_result_characteristics": ["len(cshift(words, 1))", "shape(cshift(rect, 1, dim=2))"],
            "date_and_time_time_digits": ["time_value(7:7) == '.'", "second <= 60", "millis <= 999"],
            "date_and_time_values_ranges": ["date_values(1) /= -huge(date_values(1))", "time_values(8) <= 999", "zone_values(4) == zone_minutes"],
            "dble_result_values": ["dble(z) == -4.0d0", "transfer(real(z'0000000000000001', kind(0.0d0))"],
            "dble_result_kind": ["kind(dble(1)) == kind(0.0d0)", "kind(dble(input)) == kind(0.0d0)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertNotRegex(source, r"(?i)sync\s+all|coarray")
            self.assertNotRegex(source, r"(?i)\bread\s*\(")
            self.assertNotRegex(source, r"(?i)\bint64\b")
            if spec["section"] in {"16.9.67", "16.9.69"}:
                self.assertTrue(spec["profiles"])
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_mutation_spans_and_feature_count(self):
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            features = [m for m in spec["mutations"] if m["kind"] == "feature"]
            self.assertEqual(len(features), len(spec["facets"]))
            seen = set()
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutate_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                digest = generated.sha(mutant)
                self.assertNotIn(digest, seen)
                seen.add(digest)

    def test_catalogues_remove_only_generated_facets_and_views_refresh(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            expected = generated.sync_catalogue(section, catalogue, self.specs)
            self.assertEqual(expected, catalogue)
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN.format(section=section), view)
            self.assertIn("available branch", view)
            for spec in self.specs.values():
                if spec["section"] != section:
                    continue
                row = self.registry.requirements[spec["rule"]]
                for facet in spec["facets"]:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(f"{spec['rule']} {generated.TOPIC} runtime fixture: ", row["oracle"])

    def test_known_remaining_pending_boundaries(self):
        expected_pending = {
            "S16.9.67-001": {"cpu-time-processor-time-description"},
            "S16.9.67-005": {"cpu-time-unavailable-assigns-negative", "cpu-time-available-assigns-processor-time-approximation"},
            "S16.9.67-006": {"cpu-time-negative-value-processor-dependent", "cpu-time-approximation-processor-dependent", "cpu-time-image-vs-program-time-out-of-scope"},
            "S16.9.68-006": {"cshift-rank-one-lbound-sensitive-indexing"},
            "S16.9.69-001": {"date-and-time-description"},
            "S16.9.69-003": {"date-argument-default-character-scalar", "date-intent-out"},
            "S16.9.69-005": {"time-argument-default-character-scalar", "time-intent-out"},
            "S16.9.69-007": {"zone-argument-default-character-scalar", "zone-intent-out"},
            "S16.9.69-009": {"values-rank-one-integer-range-size", "values-intent-out"},
            "S16.9.69-011": {"date-time-availability-may-vary-by-image", "date-time-multi-image-sharing-processor-dependent"},
        }
        for rule, pending in expected_pending.items():
            self.assertEqual(set(self.registry.requirements[rule].get("pending", {})), pending)
        for rule in ["S16.9.70-001", "S16.9.70-002", "S16.9.70-003", "S16.9.70-004", "S16.9.70-005"]:
            self.assertEqual(self.registry.requirements[rule].get("pending", {}), {})

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        for path, raw in {**self.files, **self.profile_files}.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        for path, raw in {**self.files, **self.profile_files}.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
