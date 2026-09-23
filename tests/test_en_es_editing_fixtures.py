"""Runtime fixture checks for Fortran 2023 EN and ES editing."""

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
import generate_en_es_editing_fixtures as generated


class EnEsEditingFixturesTests(unittest.TestCase):
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

    def test_sources_pin_exact_fields_lengths_and_modes(self):
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
            self.assertIn("value = " + spec["input_value"], source)
            self.assertIn("'" + spec["expected"] + "'", source)
            self.assertIn("#", source)
            self.assertIn("SS,", source)
            self.assertNotIn("write(field,'(S,", source)
            self.assertNotIn("write(field,'(SP,", source)
            self.assertNotRegex(source, r"(?i)\b(trim|adjustl|adjustr|transfer|merge|pack|unpack)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(complex|double\s+precision|coarray|sync\s+all)\b")
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)
            if "scale_factor" in spec["variant"]:
                self.assertIn("write(scaled,'(" + spec["descriptor"] + ")') value", source)
                self.assertIn("write(control,'(SS,0P," + spec["descriptor"].split(",")[-1] + ")') value", source)
            else:
                self.assertIn("write(field,'(" + spec["descriptor"] + ")') value", source)

    def test_discrimination_table_is_load_bearing(self):
        table = {
            ("EN12.3E2", "0.5"): (" 500.000E-03", "   5.000E-01", "+00"),
            ("EN12.3E2", "0.125"): (" 125.000E-03", "   1.250E-01", "+00"),
            ("EN12.3E2", "100.0"): (" 100.000E+00", "   1.000E+02", "+03"),
            ("EN11.2E2", "100.0"): (" 100.00E+00", "   1.00E+02", "+03"),
        }
        for spec in self.specs.values():
            bare = spec["descriptor"].split(",")[-1]
            key = (bare, spec["input_value"])
            if bare.startswith("ES"):
                key = ("EN" + bare[2:], spec["input_value"])
            self.assertIn(key, table, spec["variant"])
            en_expected, es_expected, e_exponent = table[key]
            if bare.startswith("EN"):
                self.assertEqual(spec["expected"], en_expected)
                other = es_expected
            else:
                self.assertEqual(spec["expected"], es_expected)
                other = en_expected
            self.assertNotEqual(spec["expected"], other)
            self.assertNotIn(e_exponent, spec["expected"][-4:])

    def test_mutation_plans_bind_complete_parent_sources(self):
        total_probes = 0
        reverse = 0
        inputs = 0
        oracles = 0
        descriptor_pairs = []
        sign_modes = 0
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
        self.assertEqual(reverse, len(self.specs))
        self.assertEqual(inputs, len(self.specs))
        self.assertGreaterEqual(oracles, len(self.specs))
        self.assertGreaterEqual(sign_modes, len(self.specs))
        self.assertEqual(total_probes, 184)
        required_pairs = {
            ("EN12.3E2", "ES12.3E2"), ("EN12.3E2", "E12.3E2"),
            ("ES12.3E2", "EN12.3E2"), ("ES12.3E2", "E12.3E2"),
            ("EN11.2E2", "ES11.2E2"), ("ES11.2E2", "EN11.2E2"),
            ("EN12.3E2", "EN11.3E2"), ("ES12.3E2", "ES11.3E2"),
            ("EN12.3E2", "EN12.2E2"), ("ES12.3E2", "ES12.2E2"),
            ("EN12.3E2", "EN12.3E1"), ("ES12.3E2", "ES12.3E1"),
        }
        observed_pairs = {(old, new) for _, old, new in descriptor_pairs}
        self.assertLessEqual(required_pairs, observed_pairs)
        for spec in self.specs.values():
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def test_generator_check_is_byte_identical(self):
        generated.generate(ROOT, check=True, sync_catalogues=False)


if __name__ == "__main__":
    unittest.main()
