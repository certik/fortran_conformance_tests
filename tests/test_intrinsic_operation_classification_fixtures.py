"""Runtime fixtures for Fortran 2023 intrinsic operation classification."""

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
import generate_intrinsic_operation_classification_fixtures as generated


class IntrinsicOperationClassificationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_thirteen_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 26)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(generated.VARIANTS[self.specs[case.name]["variant"]],
                             (case.rule, case.meta.facets[0]))
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expect.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence="positive-control")),
                                          self.registry.requirements[case.rule])
            for bad in (replace(case, meta=replace(case.meta, facets=[])),
                        replace(case, meta=replace(case.meta, facets=[case.meta.facets[0], "foreign"])),
                        replace(case, meta=replace(case.meta, facets=case.meta.facets * 2))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_pin_headers_literals_and_classification_boundaries(self):
        anchors = {
            "unary_plus_integer": [
                "! rule: S10.1.5.1-001\n! covers: unary-plus-integer\n",
                "left = -19", "result = + left", "if (result /= -19)"],
            "numeric_add_op": ["! covers: numeric-add-op\n", "left = 14", "right = -5", "result = left + right", "if (result /= 9)"],
            "numeric_subtract_op": ["! covers: numeric-subtract-op\n", "result = left - right", "if (result /= 19)"],
            "numeric_multiply_op": ["! covers: numeric-multiply-op\n", "left = -6", "right = 7", "result = left * right", "if (result /= -42)"],
            "numeric_divide_op": ["! covers: numeric-divide-op\n", "left = 17", "right = 5", "if (left / right /= 3)"],
            "numeric_power_op": ["! covers: numeric-power-op\n", "left = 2", "right = 5", "result = left ** right", "if (result /= 32)"],
            "default_character_concat": [
                "! rule: S10.1.5.1-004\n! covers: default-character-concat\n",
                "left = 'Q3'", "right = 'z9X'", "if (kind(left // right) /= kind(left))",
                "if (len(left // right) /= 5)", "if (left // right /= 'Q3z9X')"],
            "character_result_length_value": [
                "! covers: character-result-length-value\n", "character(len=5) :: result", "left = 'Lm'",
                "right = 'h5K'", "result = left // right", "if (len(result) /= 5)", "if (result /= 'Lmh5K')"],
            "logical_not": [
                "! rule: S10.1.5.1-005\n! covers: logical-not\n", "false_value = .false.",
                "true_value = .true.", "result_false = .not. false_value",
                "result_true = .not. true_value", "if (result_true) then"],
            "logical_and": [
                "! covers: logical-and\n", "t = .true.", "f = .false.", "result_tt = t .and. t",
                "result_tf = t .and. f", "result_ft = f .and. t", "result_ff = f .and. f",
                "if (checks /= 4)"],
            "logical_or": [
                "! covers: logical-or\n", "result_tt = t .or. t", "result_tf = t .or. f",
                "result_ft = f .or. t", "result_ff = f .or. f", "if (checks /= 4)"],
            "logical_eqv": [
                "! covers: logical-eqv\n", "result_tt = t .eqv. t", "result_tf = t .eqv. f",
                "result_ft = f .eqv. t", "result_ff = f .eqv. f", "if (checks /= 4)"],
            "logical_neqv": [
                "! covers: logical-neqv\n", "result_tt = t .neqv. t", "result_tf = t .neqv. f",
                "result_ft = f .neqv. t", "result_ff = f .neqv. f", "if (checks /= 4)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            variant = spec["variant"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertIn("Runtime consequence only", source)
            self.assertNotRegex(source, r"(?i)\b(real|complex)\s*(::|\()|\b(selected_char_kind|transfer|loc|c_loc|trim|index|repeat)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|call\s+)\b")
            if variant.startswith("logical_"):
                self.assertNotRegex(source, r"(?i)(\.eq\.|\.ne\.)")
            for needle in anchors[variant]:
                self.assertIn(needle, source)
            mutated_header = source.replace("! covers: " + spec["facets"][0], "! covers: foreign", 1)
            self.assertNotEqual(mutated_header, source)
            self.assertNotIn("! covers: " + spec["facets"][0] + "\n", mutated_header)

    def test_guard_input_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 55)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 25)
        self.assertEqual(sum(len(spec["operator_mutations"]) for spec in self.specs.values()), 12)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 49)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["guards"]), len(spec["observations"]) + 2)
            hashes = set()
            for probe in spec["probes"] + spec["input_mutations"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.mutated_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for probe in spec["operator_mutations"]:
                self.assertEqual(len(probe["spans"]), 4)
                mutant = generated.mutated_source(spec, probe)
                expected = raw
                for start, end in reversed(probe["spans"]):
                    self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                    expected = expected[:start] + probe["replacement"].encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for probe in spec["omissions"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.mutated_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                if probe["id"] == "omit-completion":
                    self.assertNotIn(spec["completion"].strip().encode(), mutant)
                    self.assertEqual((probe["kind"], probe["failure_stdout"]), ("output", ""))
                else:
                    self.assertIn(spec["completion"].strip().encode(), mutant)
                    self.assertEqual(probe["guard_id"], "check-total")
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["probes"][0])

    def test_logical_truth_tables_and_operator_swap_plans_are_discriminating(self):
        tables = {
            ".and.": {(True, True): True, (True, False): False, (False, True): False, (False, False): False},
            ".or.": {(True, True): True, (True, False): True, (False, True): True, (False, False): False},
            ".eqv.": {(True, True): True, (True, False): False, (False, True): False, (False, False): True},
            ".neqv.": {(True, True): False, (True, False): True, (False, True): True, (False, False): False},
        }
        by_variant = {spec["variant"]: spec for spec in self.specs.values()}
        self.assertEqual(
            [(guard["id"], guard["expected_truth"]) for guard in by_variant["logical_not"]["observations"]],
            [("not-false-is-true", True), ("not-true-is-false", False)])
        for variant, operator in generated.BINARY_LOGICAL_OPERATORS.items():
            spec = by_variant[variant]
            observed = {
                (True, True): spec["observations"][0]["expected_truth"],
                (True, False): spec["observations"][1]["expected_truth"],
                (False, True): spec["observations"][2]["expected_truth"],
                (False, False): spec["observations"][3]["expected_truth"],
            }
            self.assertEqual(observed, tables[operator])
            self.assertEqual({row for row, value in observed.items() if value != tables[".and."][row]},
                             set() if operator == ".and." else
                             {row for row in tables[operator] if tables[operator][row] != tables[".and."][row]})
            alternatives = [item for item in tables if item != operator]
            self.assertEqual({mutation["replacement"] for mutation in spec["operator_mutations"]}, set(alternatives))
            for alternative in alternatives:
                distinguishing_rows = [row for row in observed if observed[row] != tables[alternative][row]]
                self.assertTrue(distinguishing_rows, (operator, alternative))

    def test_catalogue_sync_removes_only_selected_pending_entries_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, remaining in generated.REMAINING_PENDING.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Binary result-type combinations, arrays, relation families", view)
        self.assertIn("not the classification label itself", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
