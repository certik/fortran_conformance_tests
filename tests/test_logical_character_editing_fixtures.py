"""Runtime fixture checks for Fortran 2023 logical and character editing."""

import json
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_logical_character_editing_fixtures as generated


class LogicalCharacterEditingFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_owned_runtime_manifests_are_discoverable(self):
        expected_ids = {generated.identifier(case["variant"]) for case in generated.CASES}
        self.assertEqual(set(self.cases), expected_ids)
        self.assertEqual(set(self.specs), expected_ids)
        self.assertEqual(len(self.files), 2 * len(generated.CASES))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        owned_facets = {facet for case in generated.CASES for facet in generated.all_facets(case)}
        self.assertEqual(len(owned_facets), 17)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, owned_facets)
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.files, ["source.f90"])
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                              case.fixture.expectation.exit_code), ("run", "success", 0))
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            expected_cohort = "positive-control" if spec["evidence"] == "positive-control" else "runtime-effect"
            self.assertEqual(self.members[case.name]["cohort"], expected_cohort)
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])), requirement)

    def test_sources_pin_exact_fields_lengths_and_guards(self):
        anchors = {
            "l_logical_output": ["write(field,'(L2)') value", "call expect_text(field, ' T'"],
            "g_logical_output": ["field = '##'", "write(field,'(G0)') value", "call expect_text(field, 'F '"],
            "l_output_fields": ["write(true_field,'(L3)') true_value", "call expect_text(true_field, '  T'",
                                "write(false_field,'(L2)') false_value", "call expect_text(false_field, ' F'"],
            "l_true_forms_and_trailing": ["field = ' .Txx'", "call mark_logical('true-trailing', value, guard, .false.)",
                                           "call expect_pre_logical(value, .false., guard", "read(field,'(L5)') value",
                                           "call expect_logical(value, .true."],
            "l_false_standard_input": ["field = '   F'", "record = field // boundary_field",
                                       "call mark_logical('false-standard', value, guard, .true.)",
                                       "call mark_logical('false-boundary', boundary_value, boundary_guard, .false.)",
                                       "read(record,'(L4,L1)', iostat=ios) value, boundary_value",
                                       "call expect_int(ios, 0", "call expect_logical(value, .false.",
                                       "call expect_logical(boundary_value, .true."],
            "l_lowercase_t": ["field = ' t'", "read(field,'(L2)') value", "call expect_logical(value, .true."],
            "l_lowercase_f": ["field = '.f'", "record = field // boundary_field",
                              "call mark_logical('lower-f-boundary', boundary_value, boundary_guard, .false.)",
                              "read(record,'(L2,L1)', iostat=ios) value, boundary_value",
                              "call expect_int(ios, 0", "call expect_logical(value, .false.",
                              "call expect_logical(boundary_value, .true."],
            "a_character_item": ["write(field,'(A2)') value", "call expect_text(field, 'xy'"],
            "g_character_output": ["write(field,'(G0)') value", "call expect_text(field, 'xy'"],
            "a_explicit_width_output": ["write(field,'(A4)') value", "call expect_text(field, '  xy'"],
            "a_omitted_width_output": ["write(field,'(A)') value", "call expect_text(field, 'xy'"],
            "a_input_wide_rightmost": ["field = 'abcd'", "call mark_text('wide-rightmost', value, guard, '??')",
                                       "read(field,'(A4)') value", "call expect_text(value, 'cd'"],
            "a_input_short_left_justified": ["field = 'xy'", "call mark_text('short-left', value, guard, '????')",
                                             "read(field,'(A2)') value", "call expect_text(value, 'xy  '"],
            "a_output_wide_left_padded": ["write(field,'(A4)') value", "call expect_text(field, '  xy'"],
            "a_output_narrow_leftmost": ["value = 'wxyz'", "write(field,'(A2)') value",
                                         "call expect_text(field, 'wx'"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertIn("if (len(observed) /= len(expected)) then", source)
            self.assertIn("checks = checks + 1", source)
            self.assertNotRegex(source, r"(?i)\b(trim|adjustl|adjustr|repeat|transfer|merge|pack|unpack)\s*\(")
            self.assertNotIn("L0", source)
            self.assertNotIn("A0", source)
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)
            if spec["variant"].startswith(("l_", "a_input")) and "read(" in source:
                self.assertIn("guard = 0", source)
                self.assertRegex(source, r"call expect_pre_(logical|text)")
            if "call expect_text(field" in source or "call expect_text(true_field" in source:
                self.assertIn("#", source)

    def test_mutation_plans_bind_complete_parent_sources(self):
        total_probes = 0
        reverse = 0
        inputs = 0
        oracles = 0
        descriptor_pairs = []
        sentinel_inits = []
        pre_guards = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            mutated_hashes = set()
            case_has_input = False
            case_has_oracle = False
            case_has_descriptor = False
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                digest = generated.sha(mutant)
                self.assertNotIn(digest, mutated_hashes)
                mutated_hashes.add(digest)
                total_probes += 1
                reverse += probe["mutation"] == "reverse-total-sentinel"
                inputs += probe["category"] == "input"
                oracles += probe["category"] == "oracle"
                pre_guards += probe["mutation"] == "pre-read-guard"
                case_has_input = case_has_input or probe["category"] == "input"
                case_has_oracle = case_has_oracle or probe["category"] == "oracle"
                if probe["mutation"] == "descriptor-substitution":
                    self.assertIn("discriminant", probe)
                    descriptor_pairs.append((spec["variant"], probe["expected"], probe["replacement"]))
                    case_has_descriptor = True
                if probe["category"] == "sentinel-init":
                    self.assertIn("discriminant", probe)
                    sentinel_inits.append((spec["variant"], probe["mutation"], probe["expected"], probe["replacement"]))
            self.assertTrue(case_has_input, spec["variant"])
            self.assertTrue(case_has_oracle, spec["variant"])
            self.assertTrue(case_has_descriptor, spec["variant"])
        self.assertEqual(reverse, len(self.specs))
        self.assertGreaterEqual(total_probes, 80)
        self.assertGreaterEqual(inputs, len(self.specs))
        self.assertGreaterEqual(oracles, len(self.specs))
        self.assertEqual(pre_guards, 8)
        self.assertEqual(len(sentinel_inits), 18)
        self.assertIn(("l_true_forms_and_trailing", "sentinel-initialization-expected",
                       "  call mark_logical('true-trailing', value, guard, .false.)\n",
                       "  call mark_logical('true-trailing', value, guard, .true.)\n"), sentinel_inits)
        self.assertIn(("l_false_standard_input", "sentinel-initialization-expected",
                       "  call mark_logical('false-standard', value, guard, .true.)\n",
                       "  call mark_logical('false-standard', value, guard, .false.)\n"), sentinel_inits)
        self.assertIn(("l_false_standard_input", "sentinel-initialization-expected",
                       "  call mark_logical('false-boundary', boundary_value, boundary_guard, .false.)\n",
                       "  call mark_logical('false-boundary', boundary_value, boundary_guard, .true.)\n"), sentinel_inits)
        self.assertIn(("a_input_wide_rightmost", "sentinel-initialization-blank",
                       "  call mark_text('wide-rightmost', value, guard, '??')\n",
                       "  call mark_text('wide-rightmost', value, guard, '  ')\n"), sentinel_inits)
        self.assertIn(("a_input_short_left_justified", "sentinel-initialization-expected",
                       "  call mark_text('short-left', value, guard, '????')\n",
                       "  call mark_text('short-left', value, guard, 'xy  ')\n"), sentinel_inits)
        for expected in [
            ("l_logical_output", "L2", "L1"),
            ("l_output_fields", "L3", "L2"), ("l_output_fields", "L2", "L1"),
            ("l_true_forms_and_trailing", "L5", "L2"), ("l_false_standard_input", "L4", "L3"),
            ("l_lowercase_t", "L2", "L1"), ("l_lowercase_f", "L2", "L1"),
            ("g_logical_output", "G0", "L2"), ("a_character_item", "A2", "A1"),
            ("a_explicit_width_output", "A4", "A3"),
            ("a_omitted_width_output", "A", "A1"), ("a_input_wide_rightmost", "A4", "A3"),
            ("a_input_short_left_justified", "A2", "A1"), ("a_output_narrow_leftmost", "A2", "A1"),
            ("a_output_wide_left_padded", "A4", "A3"), ("g_character_output", "G0", "A1"),
        ]:
            self.assertIn(expected, descriptor_pairs)
        for spec in self.specs.values():
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
