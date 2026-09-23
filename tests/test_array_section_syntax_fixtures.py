"""Regression tests for the 9.5.3.1 array element/section syntax fixture packet."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry

sys.path.insert(0, str(ROOT / "tools"))
import generate_array_section_syntax_fixtures as generated

EXPECTED = {
    "array_element_data_ref": ("R917", ["data-ref-array-element-form"], 1),
    "element_part_ref_rules": ("C924", ["all-part-refs-rank-zero", "last-part-ref-has-subscript-list"], 1),
    "data_ref_and_substring_sections": ("R918", ["data-ref-section-form", "data-ref-with-substring-range-form"], 2),
    "final_section_nonzero_rank": ("C925", ["exactly-one-nonzero-rank-part-ref", "final-section-subscript-list-nonzero-rank"], 1),
    "character_substring_section": ("C926", ["character-data-ref-with-substring-range"], 1),
    "section_subscript_alternatives": ("R921", ["subscript-alternative", "subscript-triplet-alternative", "vector-subscript-alternative"], 3),
    "subscript_triplet_forms": ("R922", ["lower-and-upper-triplet", "omitted-first-subscript", "omitted-second-subscript", "explicit-stride"], 4),
    "scalar_stride_expressions": ("R924", ["literal-scalar-int-stride", "variable-scalar-int-stride"], 2),
    "vector_subscript_int_expr": ("R925", ["int-expr-vector-subscript-form"], 1),
    "rank_one_integer_vector": ("C929", ["integer-rank-one-array-expression"], 1),
    "substring_elementwise": ("S9.5.3.1-001", ["substring-range-applies-to-each-section-element"], 1),
}


class ArraySectionSyntaxFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if "/fixtures/array_section_syntax_" in case.path}
        cls.catalogue = cls.registry.catalogues["9.5.3.1"]

    def name(self, variant):
        rule = EXPECTED[variant][0]
        return generated.identifier(rule, variant)

    def spec(self, variant):
        return self.specs[self.name(variant)]

    def source(self, variant):
        return (self.cases[self.name(variant)].fixture.root / "source.f90").read_text()

    def test_packet_cases_and_manifest_contracts(self):
        expected_names = {self.name(variant) for variant in EXPECTED}
        self.assertEqual(set(self.specs), expected_names)
        self.assertEqual(set(self.cases), expected_names)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 20)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 26)
        for variant, (rule, facets, check_count) in EXPECTED.items():
            name = self.name(variant)
            spec, case = self.specs[name], self.cases[name]
            self.assertEqual(spec["rule"], rule)
            self.assertEqual(spec["facets"], facets)
            self.assertEqual(spec["expected_checks"], check_count)
            self.assertEqual(case.rule, rule)
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.facets, facets)
            self.assertEqual(case.meta.evidence, "effect" if rule.startswith("S") else "positive-control")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertEqual(case.fixture.expectation.stdout, [generated.stdout_for(variant)])

    def test_exact_generated_files_and_source_hygiene(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("array_section_syntax_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_bytes(), raw)
            text = raw.decode("ascii")
            self.assertTrue(text.endswith("\n"))
            if path.name == "source.f90":
                self.assertLessEqual(max(map(len, text.splitlines())), 132)
                self.assertNotIn("@", text)
                self.assertNotIn(":0", text)
                self.assertNotRegex(text.lower(), r"\b(?:real|complex|pointer|allocatable|coarray|codimension)\b")

    def test_catalogue_pending_removed_only_for_selected_facets(self):
        by_rule = {row["id"]: row for row in self.catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            pending = by_rule[rule].get("pending", {})
            for facet in facets:
                self.assertNotIn(facet, pending)
            self.assertIn("Array-section syntax fixture oracle:", by_rule[rule]["oracle"])
            self.assertIn("Array-section syntax fixture boundaries:", by_rule[rule]["oracle_limitation"])
        self.assertIn("at-token-present", by_rule["R920"].get("pending", {}))
        self.assertIn("nonfinal-part-ref-nonzero-rank", by_rule["C925"].get("pending", {}))
        self.assertIn("assumed-size-last-dimension-upper-omitted-rejected", by_rule["C930"].get("pending", {}))

    def test_feature_mutations_are_bound_and_conforming_intent(self):
        for spec in self.specs.values():
            source = spec["source"]
            self.assertTrue(any("remove" in mutation["id"] or "replace-vector" in mutation["id"]
                                for mutation in spec["mutations"]), spec["id"])
            for mutation in spec["mutations"]:
                self.assertEqual(source.count(mutation["expected"]), 1, mutation)
                mutated = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutated, source)
                self.assertNotIn("@", mutated)
                self.assertNotIn(":0", mutated)
                self.assertIn(mutation["replacement"], mutated)
        self.assertIn("a(3:-1:-2)", generated.mutated_source(
            self.spec("final_section_nonzero_rank"), self.spec("final_section_nonzero_rank")["mutations"][1]))
        self.assertIn("m(:,0)", generated.mutated_source(
            self.spec("section_subscript_alternatives"), self.spec("section_subscript_alternatives")["mutations"][0]))

    def test_sources_reach_the_intended_syntax_forms(self):
        self.assertIn("box%c(k)", self.source("array_element_data_ref"))
        self.assertIn("box%child%c(j)", self.source("element_part_ref_rules"))
        self.assertIn("words(:)(2:4)", self.source("data_ref_and_substring_sections"))
        self.assertIn("a(-1:3:2)", self.source("final_section_nonzero_rank"))
        self.assertIn("m(0,:)", self.source("section_subscript_alternatives"))
        self.assertIn("a([3,-2,1])", self.source("section_subscript_alternatives"))
        self.assertIn("a(:1)", self.source("subscript_triplet_forms"))
        self.assertIn("a(1:)", self.source("subscript_triplet_forms"))
        self.assertIn("a(2:-2:step)", self.source("scalar_stride_expressions"))
        self.assertIn("a(idx)", self.source("vector_subscript_int_expr"))
        self.assertIn("len(actual) /= expected_len", self.source("substring_elementwise"))


if __name__ == "__main__":
    unittest.main()
