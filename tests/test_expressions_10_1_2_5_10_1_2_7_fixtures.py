"""Generated fixtures for Fortran 2023 expressions 10.1.2.5 through 10.1.2.7."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_expressions_10_1_2_5_10_1_2_7_fixtures as generated


class Expressions10125Through10127FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_fixture_set_and_manifest_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.files), 50)
        self.assertEqual(sum(spec["kind"] == "valid" for spec in self.specs.values()), 19)
        self.assertEqual(sum(spec["kind"] == "invalid" for spec in self.specs.values()), 6)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 60)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 54)
        self.assertEqual(json.loads(json.dumps({k: v["manifest"] for k, v in self.specs.items()})),
                         {k: v["manifest"] for k, v in self.specs.items()})
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            validate_case_requirement(case, self.registry.requirements[case.rule], case.rule[0] in "RC")
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.build[0].source, "source.f90")
            if spec["kind"] == "valid":
                self.assertIn(self.members[name]["cohort"], {"runtime-effect", "positive-control"})
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.outcome, "success")
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            else:
                self.assertEqual(self.members[name]["cohort"], "diagnostic-only")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("compile", "diagnose"))

    def test_sources_are_bounded_ascii_and_pin_key_constructs(self):
        anchors = {
            "level2_numeric_layers": ["x = 2**3**2", "x = 24/3*2", "x = 10-3-2", "x = -2**2"],
            "r1008_power_token": ["x = 2**3", "x = 2*3"],
            "level3_concat_layers": ["len('ab'//'cd')", "left_one = a // b // c", "operator(.cat.)", "out%value = 10*lhs%value + rhs%value"],
            "r1011_concat_forms": ["left_two = d // e // f", "joined_s = 'ab'//'cd'"],
            "r1012_concat_token": ["len('ab'//'cd')", "joined_s = 'ab'//'cd'"],
            "level4_relational_layers": ["len('A')", "'A' .EQ. 'A '", "'B' == 'B '", "ok = 3 >= 3"],
            "r1014_relop_tokens": ["4 .NE. 5", "4 .LE. 4", "6 /= 7", "2 <= 2"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec["kind"] == "valid":
                self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
                self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
                self.assertIn("  implicit none\n", source)
                self.assertIn("write(*,'(a)')", source)
            if spec["variant"] in anchors:
                for needle in anchors[spec["variant"]]:
                    self.assertIn(needle, source)
            self.assertEqual(generated.sha(source.encode("ascii")), spec["source_sha256"])

    def test_every_valid_facet_has_distinct_feature_mutation_and_invalids_have_repairs(self):
        for spec in self.specs.values():
            if spec["kind"] == "invalid":
                self.assertTrue(spec["repair"])
                self.assertIn(spec["source"].splitlines()[spec["line"] - 1].strip().split()[0],
                              spec["source"].splitlines()[spec["line"] - 1])
                diagnostic = spec["manifest"]["expect"]["diagnostic"]
                self.assertEqual((diagnostic["file"], diagnostic["line"]), ("source.f90", spec["line"]))
                self.assertEqual(diagnostic["contains_any"], spec["messages"])
                self.assertIn("internal compiler error", diagnostic["excludes_any"])
                continue
            by_facet = {mutation["facet"] for mutation in spec["mutations"]}
            self.assertEqual(by_facet, set(spec["facets"]))
            mutated_hashes = set()
            for mutation in spec["mutations"]:
                mutated = mutation["source"]
                self.assertNotEqual(mutated, spec["source"])
                digest = generated.sha(mutated.encode("ascii"))
                self.assertNotIn(digest, mutated_hashes)
                mutated_hashes.add(digest)
                for old, new in mutation["replacements"]:
                    self.assertIn(old, spec["source"])
                    self.assertIn(new, mutated)

    def test_each_diagnostic_negative_has_a_compiled_control(self):
        controls = {
            "r1005_missing_power_rhs": "r1005_missing_power_rhs_control",
            "r1006_missing_mult_rhs": "r1006_missing_mult_rhs_control",
            "r1007_missing_add_rhs": "r1007_missing_add_rhs_control",
            "r1011_missing_concat_rhs": "r1011_missing_concat_rhs_control",
            "r1013_relation_chain": "r1013_relation_chain_control",
            "r1013_missing_relation_rhs": "r1013_missing_relation_rhs_control",
        }
        by_variant = {spec["variant"]: spec for spec in self.specs.values()}
        for negative, control in controls.items():
            self.assertEqual(by_variant[negative]["kind"], "invalid")
            self.assertEqual(by_variant[control]["kind"], "valid")
            self.assertEqual(by_variant[negative]["rule"], by_variant[control]["rule"])
            self.assertEqual(by_variant[negative]["facets"], by_variant[control]["facets"])
            self.assertEqual(len(by_variant[control]["mutations"]), 1)

    def test_catalogues_have_selected_pending_removed_and_views_render(self):
        for section in generated.CATALOGUES:
            catalogue = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.SELECTED.items():
                if rule not in by_rule:
                    continue
                for facet in facets:
                    if facet in by_rule[rule]["facets"]:
                        self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIX, by_rule[rule]["oracle"])
                self.assertIn(generated.LIMIT_PREFIX, by_rule[rule]["oracle_limitation"])
            for rule, notes in generated.PENDING_NOTES.items():
                if rule in by_rule:
                    for facet, note in notes.items():
                        self.assertEqual(by_rule[rule].get("pending", {}).get(facet), note)
            rendered = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, rendered)
            self.assertIn("Batch295 expression fixtures", rendered)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
