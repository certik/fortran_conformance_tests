"""Runtime fixture checks for Fortran 2023 F editing."""

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
import generate_f_editing_fixtures as generated


class FEditingFixturesTests(unittest.TestCase):
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
        owned_facets = {facet for case in generated.CASES for facet in case["facets"]}
        self.assertEqual(len(owned_facets), 25)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, owned_facets)
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
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
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])), requirement)

    def test_sources_pin_exact_fields_lengths_and_sign_modes(self):
        anchors = {
            "field_width_fixed_selected": ["fixed = '#####'", "write(fixed,'(SS,F5.1)') negative_value", "call expect_text(fixed, ' -3.0'", "selected = '###'", "write(selected,'(SS,F0.1)') positive_value", "call expect_text(selected, '3.0'"],
            "fractional_digits": ["value = 1.25", "field = '#####'", "write(field,'(SS,F5.2)') value", "call expect_text(field, ' 1.25'"],
            "lowercase_real_exponent": ["field = '1e1'", "value = -99.0", "read(field,'(F3.0)') value", "call expect_real(value, 10.0"],
            "lowercase_ieee_exceptional_input": ["field = 'inf'", "value = -99.0", "read(field,'(F3.0)') value", "ieee_value(0.0, ieee_positive_inf)"],
            "input_ieee_form": ["field = 'INF'", "value = -99.0", "read(field,'(F3.0)') value", "ieee_value(0.0, ieee_positive_inf)"],
            "input_mantissa_decimal": ["field = '1.5'", "value = -99.0", "read(field,'(F3.0)') value", "call expect_real(value, 1.5"],
            "input_omitted_decimal_d": ["field = '15'", "value = -99.0", "read(field,'(F2.1)') value", "call expect_real(value, 1.5"],
            "input_e_exponent": ["field = '1E+1'", "value = -99.0", "read(field,'(F4.0)') value", "call expect_real(value, 10.0"],
            "input_d_exponent": ["field = '1D+1'", "value = -99.0", "read(field,'(F4.0)') value", "call expect_real(value, 10.0"],
            "d_exponent_same_as_e": ["e_field = '1E+1'", "d_field = '1D+1'", "e_value = -99.0", "d_value = -88.0", "call expect_true(d_value == e_value"],
            "ieee_infinity_input_syntax": ["field = ' INF '", "value = -99.0", "read(field,'(F5.0)') value", "ieee_value(0.0, ieee_positive_inf)"],
            "ieee_nan_input_syntax": ["field = 'NAN()'", "value = -99.0", "read(field,'(F5.0)') value", "call expect_true(ieee_is_nan(value)"],
            "nan_empty_payload_quiet": ["field = 'NAN()'", "value = -99.0", "read(field,'(F5.0)') value", "call expect_true(ieee_class(value) == ieee_quiet_nan"],
            "infinity_output_wide": ["field = '#########'", "write(field,'(SS,F9.1)') value", "call expect_text(field, ' Infinity'"],
            "infinity_output_narrow": ["inf_field = '####'", "write(inf_field,'(SS,F4.1)') value", "call expect_text(inf_field, ' Inf'", "star_field = '##'", "write(star_field,'(SS,F2.1)') value", "call expect_text(star_field, '**'"],
            "nan_output_forced_widths": ["right_field = '#####'", "write(right_field,'(SS,F5.1)') value", "call expect_text(right_field, '  NaN'", "nan_field = '###'", "write(nan_field,'(SS,F0.1)') value", "call expect_text(nan_field, 'NaN'", "star_field = '##'", "write(star_field,'(SS,F2.1)') value", "call expect_text(star_field, '**'"],
            "finite_output_sign": ["value = -3.0", "write(field,'(SS,F5.1)') value", "call expect_text(field, ' -3.0'"],
            "finite_output_decimal_fraction": ["value = 1.25", "write(field,'(SS,F5.2)') value", "call expect_text(field, ' 1.25'"],
            "finite_output_leading_zero": ["value = 0.25", "field = '###'", "write(field,'(SS,RZ,F3.0)') value", "call expect_text(field, ' 0.'"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertIn("if (len(observed) /= len(expected)) then", source)
            self.assertIn("if (observed /= expected) then", source)
            self.assertIn("checks = checks + 1", source)
            self.assertNotRegex(source, r"(?i)\b(trim|adjustl|adjustr|repeat|transfer|merge|pack|unpack)\s*\(")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)
            for line in source.splitlines():
                if line.strip().startswith("write(") and not line.strip().startswith("write(*") and ",'(" in line and "F" in line:
                    self.assertIn("SS,", line, line)
            if "call expect_text" in source:
                self.assertIn("#", source)

    def test_mutation_plans_bind_complete_parent_sources(self):
        total_probes = 0
        reverse = 0
        inputs = 0
        oracles = 0
        sign_modes = 0
        sentinel_inits = 0
        descriptor_pairs = []
        sentinel_expected = []
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
                sentinel_inits += probe["category"] == "sentinel-init"
                sign_modes += probe["mutation"] == "sign-mode-substitution"
                case_has_input = case_has_input or probe["category"] == "input"
                case_has_oracle = case_has_oracle or probe["category"] == "oracle"
                if probe["mutation"] == "descriptor-substitution":
                    self.assertIn("discriminant", probe)
                    descriptor_pairs.append((spec["variant"], probe["expected"], probe["replacement"]))
                    case_has_descriptor = True
                if probe["category"] == "sentinel-init":
                    self.assertIn("discriminant", probe)
                    sentinel_expected.append((spec["variant"], probe["mutation"], probe["expected"], probe["replacement"]))
            self.assertTrue(case_has_input, spec["variant"])
            self.assertTrue(case_has_oracle, spec["variant"])
            self.assertTrue(case_has_descriptor, spec["variant"])
        self.assertGreaterEqual(total_probes, 80)
        self.assertEqual(reverse, len(self.specs))
        self.assertGreaterEqual(inputs, len(self.specs))
        self.assertGreaterEqual(oracles, len(self.specs))
        self.assertEqual(sign_modes, 6)
        self.assertEqual(sentinel_inits, 36)
        self.assertIn(("lowercase_ieee_exceptional_input", "sentinel-initialization-expected",
                       "  value = -99.0\n", "  value = ieee_value(0.0, ieee_positive_inf)\n"),
                      sentinel_expected)
        self.assertIn(("nan_empty_payload_quiet", "sentinel-initialization-expected",
                       "  value = -99.0\n", "  value = ieee_value(0.0, ieee_quiet_nan)\n"),
                      sentinel_expected)
        self.assertIn(("d_exponent_same_as_e", "sentinel-initialization-zero",
                       "  d_value = -88.0\n", "  d_value = 0.0\n"),
                      sentinel_expected)
        self.assertIn(("input_e_exponent", "sentinel-initialization-remove",
                       "  value = -99.0\n", ""),
                      sentinel_expected)
        self.assertIn(("field_width_fixed_selected", "F0.1", "F4.1"), descriptor_pairs)
        self.assertIn(("fractional_digits", "F5.2", "E12.4"), descriptor_pairs)
        self.assertIn(("infinity_output_wide", "F9.1", "F4.1"), descriptor_pairs)
        self.assertIn(("infinity_output_narrow", "F4.1", "F3.1"), descriptor_pairs)
        self.assertIn(("nan_empty_payload_quiet", "F5.0", "F2.0"), descriptor_pairs)
        self.assertIn(("nan_output_forced_widths", "F5.1", "F4.1"), descriptor_pairs)
        self.assertIn(("nan_output_forced_widths", "F0.1", "F4.1"), descriptor_pairs)
        self.assertIn(("finite_output_leading_zero", "F3.0", "F2.0"), descriptor_pairs)
        for spec in self.specs.values():
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
