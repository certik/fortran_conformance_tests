"""Generated fixtures for Fortran 2023 expressions 10.1.1 through 10.1.2.4."""

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
import generate_expressions_10_1_1_10_1_2_4_fixtures as generated


class Expressions1011Through10124FixtureTests(unittest.TestCase):
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
        self.assertEqual(len(self.files), 56)
        self.assertEqual(sum(spec["kind"] == "valid" for spec in self.specs.values()), 16)
        self.assertEqual(sum(spec["kind"] == "invalid" for spec in self.specs.values()), 12)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 62)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 50)
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
                self.assertEqual(self.members[name]["cohort"], "runtime-effect" if spec["evidence"] == "effect" else "positive-control")
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
            "semantics_representation": ["object_value = 17", "computed_value = 2 + 5", "array_value = [3,5]"],
            "value_characteristics": ["kind(40+2)", "len('ab'//'cde')", "rank(21+1)", "shape([8,13])"],
            "overall_forms": ["interface operator(.combine.)", "array_result = a + b", "3 .combine. 4"],
            "overall_categories": [".u. 5", "2**3", "'ab'//'cd'", "9 > 4", ".true. .and. .true."],
            "primary_core_forms": ["constructed = pair(7,11)", "make_value(4)", "(.true. ? 31 : 41)"],
            "conditional_selection": ["x = 10 * (.true. ? branch(1,2) : branch(9,3))", "calls = calls + 1"],
            "level1_precedence": ["x = .u. 2 * 3", "x = .u.(1+2)", "x = 6 * 2"],
            "c1005_controls": ["interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)"],
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
                self.assertNotIn(generated.sha(mutated.encode("ascii")), mutated_hashes)
                mutated_hashes.add(generated.sha(mutated.encode("ascii")))
                for old, new in mutation["replacements"]:
                    self.assertIn(new, mutated)
                    self.assertIn(old, spec["source"])

    def test_catalogues_have_only_selected_pending_removed_and_views_render(self):
        for section, rel in generated.CATALOGUES.items():
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
            rendered = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, rendered)
            self.assertIn("Batch291 expression fixtures", rendered)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
