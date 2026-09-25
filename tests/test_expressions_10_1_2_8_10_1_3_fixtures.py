"""Generated fixtures for Fortran 2023 expressions 10.1.2.8 through 10.1.3."""

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
import generate_expressions_10_1_2_8_10_1_3_fixtures as generated


class Expressions10128Through1013FixtureTests(unittest.TestCase):
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
        self.assertEqual(len(self.files), 80)
        self.assertEqual(sum(spec["kind"] == "valid" for spec in self.specs.values()), 29)
        self.assertEqual(sum(spec["kind"] == "invalid" for spec in self.specs.values()), 11)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 75)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 64)
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
            "level5_logical_layers": [".not. false_a()", "true_a() .or. false_a() .eqv. false_b()", "true_a() .and. true_b() .and. false_a()"],
            "general_defined_binary_forms": ["1 + 2 .join. 3 * 4", "1 .join. 2 .join. 3", ".union.", ".aaaaaaaa"],
            "operator_precedence_table": ["x = -2**2", "ok = a // b == c", "r = .neg. a * b", "x = 2 * 3 .starstar. 4", "r = a // b // c", "r = a .or. b .or. c"],
            "r1023_missing_level5_rhs": ["x = 1 .join."],
            "r1016_defined_and_grouping": ["operator(.and.)", "r = a .and. b .and. c"],
            "r1018_defined_equiv_grouping": ["operator(.eqv.)", "r = a .eqv. b .eqv. c"],
            "c1006_sixty_four_letters": ["interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)"],
            "c1006_logical_true_spelling": ["interface operator(.true.)"],
            "c1006_logical_false_spelling": ["interface operator(.false.)"],
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

    def test_every_selected_facet_has_feature_mutation_and_invalids_have_repairs(self):
        selected = {(rule, facet) for rule, facets in generated.SELECTED.items() for facet in facets}
        mutated = set()
        for spec in self.specs.values():
            if spec["kind"] == "invalid":
                self.assertTrue(spec["repair"])
                diagnostic = spec["manifest"]["expect"]["diagnostic"]
                self.assertEqual((diagnostic["file"], diagnostic["line"]), ("source.f90", spec["line"]))
                self.assertEqual(diagnostic["contains_any"], spec["messages"])
                self.assertIn("internal compiler error", diagnostic["excludes_any"])
                continue
            self.assertEqual({mutation["facet"] for mutation in spec["mutations"]}, set(spec["facets"]))
            hashes = set()
            for mutation in spec["mutations"]:
                mutated.add((spec["rule"], mutation["facet"]))
                self.assertNotEqual(mutation["source"], spec["source"])
                digest = generated.sha(mutation["source"].encode("ascii"))
                self.assertNotIn(digest, hashes)
                hashes.add(digest)
                for old, new in mutation["replacements"]:
                    self.assertIn(old, spec["source"])
                    self.assertIn(new, mutation["source"])
        self.assertEqual(selected, mutated)

    def test_each_diagnostic_negative_has_a_compiled_control(self):
        controls = {
            "r1015_double_not": "r1015_double_not_control",
            "r1016_missing_and_rhs": "r1016_missing_and_rhs_control",
            "r1017_missing_or_rhs": "r1017_missing_or_rhs_control",
            "r1018_missing_equiv_rhs": "r1018_missing_equiv_rhs_control",
            "r1023_missing_level5_rhs": "r1023_missing_level5_rhs_control",
            "r1024_missing_leading_dot": "r1024_missing_leading_dot_control",
            "r1024_missing_trailing_dot": "r1024_missing_trailing_dot_control",
            "r1024_digit_in_name": "r1024_digit_in_name_control",
            "c1006_sixty_four_letters": "c1006_sixty_four_letters_control",
            "c1006_logical_true_spelling": "c1006_logical_true_spelling_control",
            "c1006_logical_false_spelling": "c1006_logical_false_spelling_control",
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
            self.assertIn("Batch304 expression fixtures", rendered)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
