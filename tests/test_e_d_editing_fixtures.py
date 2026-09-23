"""Runtime fixture checks for Fortran 2023 E and D editing."""

import json
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement
import generate_e_d_editing_fixtures as generated


class EDEditingFixturesTests(unittest.TestCase):
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
        self.assertEqual(len(owned_facets), 19)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, owned_facets)
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            expected_evidence = "positive-control" if spec["rule"] == "S13.7.2.3.3-006" else "effect"
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", expected_evidence, "f2023"))
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
            expected_cohort = "positive-control" if expected_evidence == "positive-control" else "runtime-effect"
            self.assertEqual(self.members[case.name]["cohort"], expected_cohort)
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])), requirement)

    def test_sources_pin_portable_fields_and_latitudes(self):
        anchors = {
            "field_width": ["value = 0.5", "write(field,'(SS,2P,E10.3E2)') value", "call expect_text(field, ' 50.00E-02'"],
            "fractional_digits": ["write(field,'(SS,1P,E9.2E2)') value", "call expect_text(field, ' 1.00E+00'"],
            "exponent_digit_count": ["write(field,'(SS,2P,E11.3E3)') value", "call expect_text(field, ' 50.00E-002'"],
            "e_no_input_effect": ["field = '1E+1'", "with_e = -99.0", "without_e = -88.0", "read(field,'(E4.0E2)') with_e", "read(field,'(E4.0)') without_e"],
            "input_same_as_f": ["field = '15'", "e_value = -99.0", "d_value = -88.0", "read(field,'(E2.1)') e_value", "read(field,'(D2.1)') d_value"],
            "ieee_output_same_as_f": ["ieee_value(0.0, ieee_positive_inf)", "ieee_value(0.0, ieee_quiet_nan)", "write(e_field,'(SS,E4.1)') value", "write(d_field,'(SS,D4.1)') value", "write(f_field,'(SS,F4.1)') value", "write(e_nan,'(SS,E5.1)') nan_value", "call expect_text(e_nan, '  NaN'"],
            "finite_normalized_form": ["write(field,'(SS,E10.3E2)') value", "call expect_text(field(3:10), '.100E+01'"],
            "finite_decimal_symbol": ["write(field,'(SS,E10.3E2)') value", "call expect_text(field(3:3), '.'"],
            "finite_d_digits": ["call expect_text(field(4:6), '100'"],
            "finite_exp_from_table": ["call expect_text(field(7:10), 'E+01'"],
            "table_e_w_d_abs_le_99": ["write(field,'(SS,E10.3)') value", "call expect_either(field(7:10), 'E+01', '+001'"],
            "table_e_w_d_abs_100_to_999": ["write(field,'(SS,101P,E110.101)') value", "call expect_text(field(1:55),", "call expect_text(field(56:110),", "call expect_text(field(107:110), '-100'"],
            "table_e_w_d_ee_positive": ["write(field,'(SS,2P,E10.3E2)') value", "call expect_text(field, ' 50.00E-02'"],
            "table_e0_or_e0_d": ["write(field,'(SS,1P,E0.3E0)') value", "call expect_text(field, '1.000E+0'"],
            "table_d_w_d_abs_le_99": ["write(field,'(SS,1P,D10.3)') value", "call expect_one_of(field(7:10), 'D+00', 'E+00', '+000'"],
            "table_d_w_d_abs_100_to_999": ["write(field,'(SS,101P,D110.101)') value", "call expect_text(field(1:55),", "call expect_text(field(56:110),", "call expect_text(field(107:110), '-100'"],
            "zero_exponent_plus": ["call expect_text(field(7:7), '+'"],
            "scale_negative_to_zero": ["write(field,'(SS,-1P,E10.3E2)') value", "call expect_text(field(3:10), '.010E+02'"],
            "scale_positive": ["write(field,'(SS,1P,E10.3E2)') value", "call expect_text(field, ' 1.000E+00'"],
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
            if "write(field," in source or "write(e_field," in source or "write(d_field," in source or "write(f_field," in source:
                self.assertIn("#", source)
            self.assertNotRegex(source, r"(?i)\b(trim|adjustl|adjustr|transfer|merge|pack|unpack)\s*\(")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)
            for line in source.splitlines():
                if line.strip().startswith("write(") and not line.strip().startswith("write(*"):
                    self.assertIn("SS,", line, line)
            if spec["variant"].startswith("finite_") or spec["variant"] == "scale_negative_to_zero":
                self.assertNotIn("' 0.", source)
                self.assertNotIn("'0.", source)

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
                sign_modes += probe["mutation"] == "sign-mode-substitution"
                sentinel_inits += probe["category"] == "sentinel-init"
                case_has_oracle = case_has_oracle or probe["category"] == "oracle"
                if probe["mutation"] == "descriptor-substitution":
                    self.assertIn("discriminant", probe)
                    descriptor_pairs.append((spec["variant"], probe["expected"], probe["replacement"]))
                    case_has_descriptor = True
                if probe["category"] == "sentinel-init":
                    self.assertIn("discriminant", probe)
                    sentinel_expected.append((spec["variant"], probe["mutation"], probe["expected"], probe["replacement"]))
            self.assertTrue(case_has_oracle, spec["variant"])
            self.assertTrue(case_has_descriptor, spec["variant"])
        self.assertEqual(total_probes, 195)
        self.assertEqual(reverse, len(self.specs))
        self.assertEqual(inputs, 19)
        self.assertGreaterEqual(oracles, len(self.specs))
        self.assertEqual(sign_modes, 11)
        self.assertEqual(sentinel_inits, 12)
        required_pairs = {
            ("field_width", "E10.3E2", "ES10.3E2"),
            ("field_width", "E10.3E2", "EN10.3E2"),
            ("fractional_digits", "E9.2E2", "E9.1E2"),
            ("e_no_input_effect", "E4.0E2", "E4.1E2"),
            ("input_same_as_f", "D2.1", "D2.0"),
            ("ieee_output_same_as_f", "D4.1", "D2.1"),
            ("finite_normalized_form", "E10.3E2", "F10.3"),
            ("table_e_w_d_abs_100_to_999", "101P", "100P"),
            ("table_e_w_d_abs_100_to_999", "E110.101", "E109.101"),
            ("table_d_w_d_abs_100_to_999", "D110.101", "D110.100"),
            ("table_d_w_d_abs_le_99", "D10.3", "F10.3"),
            ("zero_exponent_plus", "E0.3E0", "F0.3"),
            ("scale_negative_to_zero", "-1P", "0P"),
        }
        self.assertLessEqual(required_pairs, set(descriptor_pairs))
        self.assertIn(("e_no_input_effect", "sentinel-initialization-expected", "  with_e = -99.0\n", "  with_e = 10.0\n"), sentinel_expected)
        self.assertIn(("input_same_as_f", "sentinel-initialization-zero", "  d_value = -88.0\n", "  d_value = 0.0\n"), sentinel_expected)
        for old, new in {(old, new) for _, old, new in descriptor_pairs}:
            self.assertNotEqual(old[0], "D" if new.startswith("E") else "")
        for spec in self.specs.values():
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
