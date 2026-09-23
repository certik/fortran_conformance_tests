"""Runtime fixture checks for Fortran 2023 input/output rounding modes."""

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
import generate_rounding_mode_fixtures as generated


class RoundingModeFixturesTests(unittest.TestCase):
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
        self.assertEqual(len(owned_facets), 17)
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

    def test_sources_pin_exact_fields_and_rounding_modes(self):
        anchors = {
            "open_specifier_up": ["open_value = -1.25", "round='UP'", "write(unit,'(SS,F5.1)') open_value",
                                  "open_field = '#####'", "read(unit,'(a)') open_field",
                                  "call expect_text(open_field, ' -1.2'"],
            "data_transfer_specifier_down": ["transfer_value = 1.25", "transfer_field = '#####'",
                                  "write(transfer_field,'(SS,F5.1)',round='DOWN') transfer_value",
                                  "call expect_text(transfer_field, '  1.2'"],
            "edit_descriptor_specifier_zero": ["descriptor_value = 1.25", "descriptor_field = '#####'",
                                  "write(descriptor_field,'(SS,RZ,F5.1)') descriptor_value",
                                  "call expect_text(descriptor_field, '  1.2'"],
            "decimal_internal_directions": ["input_field = '1.25'", "input_value = -99.0",
                                            "read(input_field,'(F4.2)') input_value",
                                            "call expect_real(input_value, 1.25",
                                            "output_value = 1.125", "output_field = '#####'",
                                            "write(output_field,'(SS,F5.3)') output_value",
                                            "call expect_text(output_field, '1.125'"],
            "required_rounding_modes": ["tie_positive = 1.25", "tie_negative = -1.25",
                                        "nearest_value = 1.125", "write(up_field,'(SS,RU,F5.1)') tie_positive",
                                        "call expect_text(up_field, '  1.3'",
                                        "write(down_field,'(SS,RD,F5.1)') tie_positive",
                                        "call expect_text(down_field, '  1.2'",
                                        "write(zero_field,'(SS,RZ,F5.1)') tie_negative",
                                        "call expect_text(zero_field, ' -1.2'",
                                        "write(nearest_field,'(SS,RN,F5.1)') nearest_value",
                                        "call expect_text(nearest_field, '  1.1'",
                                        "write(compatible_field,'(SS,RC,F5.1)') tie_negative",
                                        "call expect_text(compatible_field, ' -1.3'"],
            "edit_descriptors_required_modes": ["write(up_field,'(SS,RU,F5.1)') tie_positive",
                                                "write(down_field,'(SS,RD,F5.1)') tie_positive",
                                                "write(zero_field,'(SS,RZ,F5.1)') tie_negative",
                                                "write(nearest_field,'(SS,RN,F5.1)') nearest_value",
                                                "write(compatible_field,'(SS,RC,F5.1)') tie_negative"],
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
                stripped = line.strip()
                if stripped.startswith("write(") and not stripped.startswith("write(*") and ",'(" in stripped and "F" in stripped:
                    self.assertIn("SS,", stripped, stripped)
            if "call expect_text" in source:
                self.assertIn("#", source)
            self.assertNotRegex(source, r"F[0-9]+\.[01].*0\.[0-9]")

    def test_mutation_plans_bind_complete_parent_sources(self):
        total_probes = 0
        reverse = 0
        inputs = 0
        oracles = 0
        sentinels = 0
        descriptors = []
        round_modes = []
        sentinel_expected = []
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            mutated_hashes = set()
            case_has_input = False
            case_has_oracle = False
            case_has_feature = False
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
                sentinels += probe["category"] == "sentinel-init"
                case_has_input = case_has_input or probe["category"] == "input"
                case_has_oracle = case_has_oracle or probe["category"] == "oracle"
                if probe["mutation"] == "descriptor-substitution":
                    self.assertIn("discriminant", probe)
                    descriptors.append((spec["variant"], probe["expected"], probe["replacement"]))
                    case_has_feature = True
                if probe["mutation"] == "round-mode-substitution":
                    self.assertIn("discriminant", probe)
                    round_modes.append((spec["variant"], probe["expected"], probe["replacement"]))
                    case_has_feature = True
                if probe["category"] == "sentinel-init":
                    self.assertIn("discriminant", probe)
                    sentinel_expected.append((spec["variant"], probe["mutation"], probe["expected"], probe["replacement"]))
            self.assertTrue(case_has_input, spec["variant"])
            self.assertTrue(case_has_oracle, spec["variant"])
            self.assertTrue(case_has_feature, spec["variant"])
        self.assertEqual(reverse, len(self.specs))
        self.assertGreaterEqual(total_probes, 40)
        self.assertGreaterEqual(inputs, len(self.specs))
        self.assertGreaterEqual(oracles, len(self.specs))
        self.assertEqual(sentinels, 6)
        self.assertIn(("open_specifier_up", "UP", "DOWN"), round_modes)
        self.assertIn(("data_transfer_specifier_down", "DOWN", "UP"), round_modes)
        self.assertIn(("edit_descriptor_specifier_zero", "RZ", "RU"), descriptors)
        self.assertIn(("decimal_internal_directions", "F4.2", "F3.2"), descriptors)
        self.assertIn(("required_rounding_modes", "RN", "RU"), descriptors)
        self.assertIn(("required_rounding_modes", "RC", "RU"), descriptors)
        self.assertIn(("edit_descriptors_required_modes", "RZ", "RD"), descriptors)
        self.assertIn(("decimal_internal_directions", "sentinel-initialization-expected",
                       "  input_value = -99.0\n", "  input_value = 1.25\n"), sentinel_expected)
        self.assertIn(("open_specifier_up", "sentinel-initialization-expected",
                       "  open_field = '#####'\n", "  open_field = ' -1.2'\n"), sentinel_expected)
        self.assertIn(("decimal_internal_directions", "sentinel-initialization-remove",
                       "  input_value = -99.0\n", ""), sentinel_expected)
        for spec in self.specs.values():
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
