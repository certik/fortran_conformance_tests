"""Scalar explicit-shape bounds, range and zero-extent runtime fixture metadata."""
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
import generate_explicit_shape_fixtures as generated


class ExplicitShapeFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def test_exact_three_owned_f2023_effect_fixtures_and_eight_facets(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 6)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, set().union(*map(set, generated.FACETS_BY_RULE.values())))
        self.assertEqual(sum(len(case.meta.facets) for case in self.cases.values()), 8)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             (spec["rule"], "valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["completion"]])
            self.assertEqual(expect.stderr, [""])

    def test_sources_observe_declared_arrays_without_descriptor_proxies_or_empty_element_access(self):
        required = {
            "scalar_bounds": [
                "integer :: upper_only(4)", "integer :: explicit2d(-2:0,4:5)",
                "integer :: mixed(2,-1:1)", "lbound(upper_only) /= [1]",
                "lbound(explicit2d) /= [-2,4]", "lbound(mixed) /= [1,-1]",
                "count(upper_only == 41) /= 4", "count(explicit2d == 52) /= 6",
                "count(mixed == 63) /= 6"],
            "range_bounds": [
                "integer :: positive_range(2:4)", "integer :: negative_range(-2:0)",
                "integer :: zero_singleton(0:0)", "positive_range(lbound(positive_range,1))",
                "negative_range(ubound(negative_range,1))", "zero_singleton(lbound(zero_singleton,1)) /= 85"],
            "empty_ranges": [
                "integer :: empty1(5:3)", "integer :: empty2(5:3,-2:1)",
                "lbound(empty1) /= [1]", "ubound(empty1) /= [0]",
                "shape(empty2) /= [0,4]", "size(empty2) /= 0", "reached /= 917"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertTrue(source.endswith("\n"))
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertNotRegex(source, r"(?i)\b(?:allocatable|pointer|target|save|data|common|equivalence|transfer|loc|c_loc)\b")
            self.assertNotRegex(source, r"(?i)\b(?:reshape|pack|merge|spread)\s*\(")
            self.assertNotRegex(source, r"(?i)\bubound\s*\([^)]*,\s*kind")
            self.assertNotRegex(source, r"(?i)\b(?:module|contains|subroutine|function|interface|block)\b")
            for needle in required[spec["variant"]]:
                self.assertIn(needle, source)
            if spec["variant"] == "empty_ranges":
                self.assertNotRegex(source, r"empty[12]\([^)]*\)\s*(?:=|/=)")
                self.assertNotIn("count(empty", source)
            else:
                self.assertRegex(source, r"=\d[0-9]\n")

    def test_mutation_bindings_cover_guards_inputs_omissions_and_features(self):
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["feature_mutations"]), 2)
            self.assertGreaterEqual(len(spec["input_mutations"]), 1)
            self.assertEqual(len(spec["observations"]), spec["expected_counts"]["checks"])
            self.assertEqual(len(spec["omissions"]), len(spec["observations"]) + 1)
            for mutation in generated.all_mutations(spec):
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, generated.all_mutations(spec)[0])
        feature_ids = {row["id"] for spec in self.specs.values() for row in spec["feature_mutations"]}
        self.assertIn("feature-upper-only-to-nonunit-lower", feature_ids)
        self.assertIn("feature-remove-explicit-lowers", feature_ids)
        self.assertIn("feature-empty-one-dimensional-to-singleton", feature_ids)

    def test_catalogue_sync_removes_only_owned_pending_facets_and_renders_summary(self):
        by_rule = {row["id"]: row for row in self.catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), generated.REMAINING_PENDING[rule])
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertEqual(generated.synced_catalogue(self.catalogue), self.catalogue)
        rendered = generated.render_view(self.catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, rendered)
        self.assertIn("Three complete run/effect/f2023 fixtures cover eight selected scalar-list facets", rendered)
        self.assertIn("S8.5.8.2-002 is fully represented here", rendered)
        self.assertIn("`inquiry-normalization-source` pending", rendered)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("explicit_shape_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")


if __name__ == "__main__":
    unittest.main()
