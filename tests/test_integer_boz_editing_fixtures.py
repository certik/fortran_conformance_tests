"""Runtime fixture checks for Fortran 2023 integer and BOZ editing."""

import json
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_integer_boz_editing_fixtures as generated


class IntegerBozEditingFixturesTests(unittest.TestCase):
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
        self.assertEqual(len(owned_facets), 18)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, owned_facets)
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
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

    def test_sources_pin_exact_fields_and_lengths(self):
        anchors = {
            "i_width_fixed_selected": ["write(fixed,'(SS,I5)') value", "call expect_text(fixed, '   42'", "write(selected,'(SS,I0)') value", "call expect_text(selected, '42'"],
            "i_input_m_ignored": ["field_m = '7'", "read(field_m,'(I1.1)') got_m", "read(field_plain,'(I1)') got_plain"],
            "i_input_signed_digit": ["field_negative = '-42'", "field_positive = ' 42'", "call expect_int(got_negative, -42"],
            "i_output_leading_blanks": ["write(field,'(SS,I5)') value", "call expect_text(field, '   42'"],
            "i_output_negative_minus": ["value = -42", "write(field,'(I5)') value", "call expect_text(field, '  -42'"],
            "i_output_no_leading_zero": ["value = 7", "call expect_text(field, '    7'"],
            "i_output_minimum_m_digits": ["write(field,'(SS,I5.4)') value", "call expect_text(field, ' 0042'"],
            "i_output_leading_zeros_to_m": ["write(field,'(SS,I3.2)') value", "call expect_text(field, ' 07'"],
            "boz_width_fixed_selected": ["write(fixed,'(B5)') value", "call expect_text(fixed, '  101'", "write(selected,'(B0)') value"],
            "boz_input_m_ignored": ["field_m = '101'", "read(field_m,'(B3.3)') got_m", "read(field_plain,'(B3)') got_plain"],
            "b_input_binary_digits": ["read(field,'(B3)') got", "call expect_int(got, 5"],
            "o_input_octal_digits": ["read(field,'(O2)') got", "call expect_int(got, 8"],
            "z_input_hex_digits": ["field = '0A'", "read(field,'(Z2)') got", "call expect_int(got, 10"],
            "z_input_lowercase_equivalence": ["field = '0a'", "read(field,'(Z2)') got", "call expect_int(got, 10"],
            "b_output_no_leading_zero_bits": ["write(field,'(B5)') value", "call expect_text(field, '  101'"],
            "o_output_no_leading_zero_bits": ["write(field,'(O4)') value", "call expect_text(field, '  10'"],
            "z_output_no_leading_zero_bits": ["write(field,'(Z3)') value", "call expect_text(field, '  A'"],
            "boz_output_minimum_m_digits": ["write(b_field,'(B4.4)') b_value", "call expect_text(b_field, '0101'", "write(o_field,'(O4.4)') o_value", "call expect_text(o_field, '0010'", "write(z_field,'(Z4.4)') z_value", "call expect_text(z_field, '000A'"],
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
            self.assertNotRegex(source, r"(?i)\b(real|complex|enum|enumeration|coarray|sync\s+all)\b")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)

    def test_mutation_plans_bind_complete_parent_sources(self):
        total_probes = 0
        reverse = 0
        inputs = 0
        oracles = 0
        descriptor_pairs = []
        sign_modes = 0
        hashes_by_case = {}
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            mutated_hashes = set()
            case_has_input = False
            case_has_oracle = False
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
                case_has_input = case_has_input or probe["category"] == "input"
                case_has_oracle = case_has_oracle or probe["category"] == "oracle"
                if probe["mutation"] == "descriptor-substitution":
                    descriptor_pairs.append((spec["variant"], probe["expected"], probe["replacement"]))
            self.assertTrue(case_has_input, spec["variant"])
            self.assertTrue(case_has_oracle, spec["variant"])
            hashes_by_case[spec["variant"]] = mutated_hashes
        self.assertGreaterEqual(total_probes, 60)
        self.assertEqual(reverse, len(self.specs))
        self.assertGreaterEqual(inputs, len(self.specs))
        self.assertGreaterEqual(oracles, len(self.specs))
        self.assertGreaterEqual(sign_modes, 5)
        self.assertIn(("i_width_fixed_selected", "I5", "I6"), descriptor_pairs)
        self.assertIn(("i_width_fixed_selected", "I5", "I5.4"), descriptor_pairs)
        boz_matrix = {(old, new) for variant, old, new in descriptor_pairs if variant == "boz_output_minimum_m_digits"}
        self.assertEqual(boz_matrix, {
            ("B4.4", "O4.4"), ("B4.4", "Z4.4"),
            ("O4.4", "B4.4"), ("O4.4", "Z4.4"),
            ("Z4.4", "B4.4"), ("Z4.4", "O4.4"),
        })
        for spec in self.specs.values():
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
