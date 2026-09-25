"""Additional executable fixtures for Fortran 2023 11.1 BLOCK and ASSOCIATE rules."""
import json
from pathlib import Path
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_associate_blocks_11_1_fixtures as generated


class AssociateBlocks111FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_fixture_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 29)
        self.assertEqual(len(self.files), 58)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, set().union(*map(set, generated.FACETS_BY_RULE.values())))
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 42)
        invalids = {name for name, spec in self.specs.items() if spec["kind"] == "invalid"}
        self.assertEqual(len(invalids), 5)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual((case.rule, case.kind, case.meta.standard), (spec["rule"], spec["kind"], "f2023"))
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            if case.kind == "valid":
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                bad = "positive-control" if case.meta.evidence == "effect" else "effect"
                if case.rule.startswith("S"):
                    with self.assertRaises(SuiteError):
                        validate_case_requirement(replace(case, meta=replace(case.meta, evidence=bad)),
                                                  self.registry.requirements[case.rule])
            else:
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")
                self.assertEqual(case.fixture.expectation.diagnostic["line"], spec["line"])
                self.assertEqual(case.fixture.expectation.diagnostic["end_line"], spec["line"])
                self.assertIn("internal compiler error", case.fixture.expectation.diagnostic["excludes_any"])

    def test_source_anchors_and_line_hygiene(self):
        anchors = {
            "block_completion_causes": ["goto 40", "returner(return_value)", "if (i == 2) cycle", "if (i == 4) exit"],
            "selector_evaluation_before_block": ["associate (value => bump())", "counter=counter+1", "inside=counter"],
            "contiguity": ["is_contiguous(whole)", "base(1:6:2)", ".not. is_contiguous(stride)"],
            "polymorphic_selector": ["class(base), allocatable :: obj", "select type (alias)", "seen_extra=alias%extra"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("  implicit none\n", source)
            self.assertEqual(source.count("program "), 2 if "end program" in source else 1)
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)
            if spec["kind"] == "invalid":
                self.assertNotIn("write(*", source)
            else:
                self.assertIn(spec["completion"].rstrip("\n"), source)

    def test_feature_mutations_are_unique_complete_parent_changes(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 37)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            if spec["kind"] == "valid":
                self.assertGreaterEqual(len(spec["mutations"]), 1)
            seen = set()
            for mutation in spec["mutations"]:
                self.assertIn(mutation["facet"], spec["facets"])
                self.assertEqual(spec["source"].count(mutation["expected"]), 1)
                mutant = generated.mutant_source(spec, mutation).encode("ascii")
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), seen)
                seen.add(generated.sha(mutant))

    def test_catalogues_render_with_only_selected_pending_removed(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, remaining in generated.REMAINING_PENDING.items():
                if rule in by_rule:
                    self.assertEqual(set(by_rule[rule].get("pending", {})), set(remaining))
            for rule, facets in generated.FACETS_BY_RULE.items():
                if rule in by_rule:
                    for facet in facets:
                        self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                    self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
                    self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            self.assertEqual(generated.synced_catalogue(section, catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn(generated.SUMMARY_END, view)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
