"""Scoping and name-association fixture packet checks for Fortran 2023 19.3.5-19.5.1.2."""

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
import generate_scoping_19_3_19_5_fixtures as generated


class Scoping193195FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_owned_cases_and_facets(self):
        self.assertEqual(set(self.cases), {spec["id"] for spec in self.specs.values()})
        self.assertEqual(len(self.cases), 18)
        self.assertEqual(len(self.files), 36)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
            cohort = "positive-control" if spec["evidence"] == "positive-control" else "runtime-effect"
            self.assertEqual(self.members[case.name]["cohort"], cohort)

    def test_sources_have_distinct_sentinels_and_scoping_features(self):
        all_sources = []
        for spec in self.specs.values():
            source = spec["source"]
            all_sources.append(source)
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertIn("checks = checks + 1", source)
            self.assertIn("write(*,'(a)') '" + spec["stdout"].strip() + "'", source)
            self.assertRegex(source, r"-\d{2,4}")
        joined = "\n".join(all_sources).lower()
        for needle in ("associate", "select rank", "select type", "block", "do concurrent", "forall", "data ("):
            self.assertIn(needle, joined)
        self.assertNotRegex(joined, r"\b(real|complex|random_number|system_clock|c_loc|loc)\b")

    def test_mutations_are_feature_level_and_nonidentical(self):
        total = 0
        for spec in self.specs.values():
            hashes = set()
            for plan in spec["mutations"]:
                mutant = generated.mutate_source(spec, plan)
                self.assertNotEqual(mutant, spec["source"])
                self.assertEqual(generated.sha(mutant.encode("ascii")), plan["mutant_sha256"])
                self.assertIn(spec["stdout"].strip(), mutant)
                for repl in plan["replacements"]:
                    self.assertEqual(spec["source"].count(repl["expected"]), 1)
                    self.assertNotEqual(repl["expected"], repl["replacement"])
                self.assertNotIn(plan["mutant_sha256"], hashes)
                hashes.add(plan["mutant_sha256"])
                total += 1
        self.assertEqual(total, 48)

    def test_catalogues_synced_and_rendered(self):
        for section, rel in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.FACETS_BY_RULE.items():
                if generated.section_for_rule(rule) != section:
                    continue
                self.assertEqual(set(by_rule[rule].get("pending", {})), generated.EXPECTED_REMAINING[rule])
                for facet in facets:
                    self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            self.assertEqual(generated.synced_catalogue(section, catalogue), catalogue)
            view = generated.rendered_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("Scoping/name-association fixture observations", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)

    def test_identity_sabotage_is_reported_by_matrix_logic(self):
        spec = next(iter(self.specs.values()))
        plan = json.loads(json.dumps(spec["mutations"][0]))
        plan["replacements"][0]["replacement"] = plan["replacements"][0]["expected"]
        self.assertEqual(generated.mutate_source(spec, plan, allow_identical=True), spec["source"])
        with self.assertRaises(ValueError):
            generated.mutate_source(spec, plan)


if __name__ == "__main__":
    unittest.main()
