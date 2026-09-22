"""Runtime fixtures for exact integer division and character concatenation."""

import copy
from dataclasses import replace
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_exact_arithmetic_fixtures as generated


class ExactArithmeticFixturesTests(unittest.TestCase):
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
                         set(generated.INT_FACETS) | {facet for facets in generated.CHAR_FACETS_BY_RULE.values()
                                                      for facet in facets})
        for case in self.cases.values():
            expected_evidence = "positive-control" if case.rule == generated.CHAR_RULE_TYPE else "effect"
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", expected_evidence, "f2023"))
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
            self.assertEqual(self.members[case.name]["cohort"],
                             "positive-control" if case.rule == generated.CHAR_RULE_TYPE else "runtime-effect")
            wrong_evidence = "effect" if case.rule == generated.CHAR_RULE_TYPE else "positive-control"
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence=wrong_evidence)),
                                          self.registry.requirements[case.rule])
            for bad in (replace(case, meta=replace(case.meta, facets=[])),
                        replace(case, meta=replace(case.meta, facets=[case.meta.facets[0], "foreign"])),
                        replace(case, meta=replace(case.meta, facets=case.meta.facets * 2))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_pin_headers_literals_and_nonduplicating_oracles(self):
        anchors = {
            "positive_truncates_toward_zero": [
                "! rule: S10.1.5.2.2-001\n! covers: positive-truncates-toward-zero\n",
                "result = 8 / 3", "quotient 2.666", "if (result /= 2)"],
            "negative_dividend_truncates_toward_zero": [
                "! covers: negative-dividend-truncates-toward-zero\n",
                "result = (-8) / 3", "Flooring division would give -3", "if (result /= -2)"],
            "negative_divisor_truncates_toward_zero": [
                "! covers: negative-divisor-truncates-toward-zero\n",
                "result = 8 / (-3)", "Flooring division would give -3", "if (result /= -2)"],
            "exact_integer_division": [
                "! covers: exact-integer-division\n", "result = 8 / 4", "quotient exactly 2", "if (result /= 2)"],
            "default_character_same_kind": [
                "! rule: S10.1.5.3.1-001\n! covers: default-character-same-kind\n",
                "left = 'AX'", "right = 'b7q'", "if (kind(left // right) /= kind(left))",
                "if (len(left // right) /= 5)", "if (left // right /= 'AXb7q')"],
            "character_result_type": [
                "! covers: character-result-type\n", "character(len=5) :: result", "result = left // right",
                "if (result /= 'R4s9T')", "if (len(result) /= 5)", "if (kind(result) /= kind(left))"],
            "right_append_value": [
                "! rule: S10.1.5.3.1-002\n! covers: right-append-value\n",
                "left = 'AB'", "right = 'q7Z'", "swapped order would be 'q7ZAB'",
                "if (len(left // right) /= 5)", "if (left // right /= 'ABq7Z')"],
            "result_length_sum": [
                "! covers: result-length-sum\n", "left = 'mN'", "right = 'p8R'",
                "LEN(left // right) must be 2+3=5", "if (len(left // right) /= 5)",
                "if (left // right /= 'mNp8R')"],
            "zero_length_left": [
                "! covers: zero-length-left\n", "character(len=0) :: left", "right = 'R9q'",
                "length 0+3=3", "if (len(left // right) /= 3)", "if (left // right /= 'R9q')"],
            "zero_length_right": [
                "! covers: zero-length-right\n", "character(len=0) :: right", "left = 'L0xP'",
                "length 4+0=4", "if (len(left // right) /= 4)", "if (left // right /= 'L0xP')"],
            "left_grouped_concatenation_value": [
                "! rule: S10.1.5.3.1-003\n! covers: left-grouped-concatenation-value\n",
                "('A' // 'bc') // 'D3e'", "if (len((first // second) // third) /= 6)",
                "if ((first // second) // third /= 'AbcD3e')"],
            "right_grouped_concatenation_value": [
                "! covers: right-grouped-concatenation-value\n", "'A' // ('bc' // 'D3e')",
                "if (len(first // (second // third)) /= 6)", "if (first // (second // third) /= 'AbcD3e')"],
            "nested_parentheses_value": [
                "! covers: nested-parentheses-value\n", "Nested parentheses do not change the final value",
                "if (len((((first)) // ((second) // ((third))))) /= 6)",
                "if ((((first)) // ((second) // ((third)))) /= 'uV2wx9')"],
        }
        for spec in self.specs.values():
            source = spec["source"]
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
            self.assertNotRegex(source, r"(?i)\b(mod|modulo|floor|ceiling|int|nint|real|aimag|cmplx)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(trim|index|repeat|transfer)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|selected_char_kind)\b")
            if spec["rule"] in {generated.CHAR_RULE_VALUE, generated.CHAR_RULE_PARENS}:
                self.assertRegex(source, r"(?i)\blen\s*\(")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            mutated = source.replace("! covers: " + spec["facets"][0], "! covers: foreign", 1)
            self.assertNotEqual(mutated, source)
            self.assertNotIn("! covers: " + spec["facets"][0] + "\n", mutated)

    def test_guard_probe_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 53)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 49)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["guards"]), len(spec["observations"]) + 2)
            hashes = set()
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for probe in spec["omissions"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
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
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def probe_check(self, spec, probe=None):
        raw = spec["source"].encode("ascii") if probe is None else generated.wrong_oracle_source(spec, probe)
        if probe is None:
            stdout, stderr, code, outcome = spec["completion"], "", 0, "pass"
        elif probe["kind"] == "output":
            stdout = "" if probe["mutation"] == "completion-statement-omission" else probe["replacement"] + "\n"
            stderr, code, outcome = "", 0, "fail"
        else:
            stdout, stderr, code, outcome = probe["failure_stdout"], "ERROR STOP\n", 2, "fail"
        trace = [dict(phase=phase, returncode=0, timed_out=False, stdout="", stderr="")
                 for phase in ("compile", "link", "run")]
        trace[-1].update(returncode=code, stdout=stdout, stderr=stderr)
        return dict(outcome=outcome, phase="run", trace=trace, input_hashes={"source.f90": generated.sha(raw)})

    def test_each_planned_failure_requires_current_complete_parent(self):
        vectors = 0
        for spec in self.specs.values():
            parent = self.probe_check(spec)
            for probe in spec["probes"] + spec["omissions"]:
                verdict = generated.probe_verdict(spec, probe, parent, self.probe_check(spec, probe),
                                                  parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                bad_parent = copy.deepcopy(parent)
                bad_parent["input_hashes"]["source.f90"] = "0" * 64
                blocked = generated.probe_verdict(spec, probe, bad_parent, self.probe_check(spec, probe),
                                                  parent_binding_current=True)
                self.assertFalse(blocked["qualified"])
                untested = generated.probe_verdict(spec, probe, parent, None, parent_binding_current=True)
                self.assertEqual((untested["status"], untested["qualified"]), ("UNTESTED", False))
                vectors += 3
        self.assertEqual(vectors, 306)

    def test_catalogue_sync_removes_selected_pending_entries_and_regenerates_views(self):
        int_catalogue = self.registry.catalogues[generated.INT_SECTION]
        int_owner = next(row for row in int_catalogue["requirements"] if row["id"] == generated.INT_RULE)
        self.assertEqual(int_owner.get("pending", {}), {})
        for facet in generated.INT_FACETS:
            self.assertNotIn(facet, int_owner.get("pending", {}))
        self.assertIn(generated.INT_ORACLE_PREFIX, int_owner["oracle"])
        self.assertIn(generated.INT_LIMIT_PREFIX, int_owner["oracle_limitation"])
        self.assertEqual(generated.synced_integer_catalogue(int_catalogue), int_catalogue)
        self.assertIn(generated.INT_SUMMARY_BEGIN, generated.render_view(
            int_catalogue, generated.INT_SECTION, generated.INT_VIEW, ROOT, character=False))

        char_catalogue = self.registry.catalogues[generated.CHAR_SECTION]
        by_rule = {row["id"]: row for row in char_catalogue["requirements"]}
        self.assertEqual(set(by_rule[generated.CHAR_RULE_TYPE].get("pending", {})),
                         {"nondefault-same-kind-profile", "different-kind-boundary"})
        self.assertEqual(by_rule[generated.CHAR_RULE_VALUE].get("pending", {}), {})
        self.assertEqual(by_rule[generated.CHAR_RULE_PARENS].get("pending", {}), {})
        for rule, facets in generated.CHAR_FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
        self.assertIn(generated.CHAR_TYPE_ORACLE_PREFIX, by_rule[generated.CHAR_RULE_TYPE]["oracle"])
        self.assertIn(generated.CHAR_VALUE_ORACLE_PREFIX, by_rule[generated.CHAR_RULE_VALUE]["oracle"])
        self.assertIn(generated.CHAR_PARENS_ORACLE_PREFIX, by_rule[generated.CHAR_RULE_PARENS]["oracle"])
        self.assertEqual(generated.synced_character_catalogue(char_catalogue), char_catalogue)
        char_view = generated.render_view(char_catalogue, generated.CHAR_SECTION, generated.CHAR_VIEW, ROOT, character=True)
        self.assertIn(generated.CHAR_SUMMARY_BEGIN, char_view)
        self.assertIn("`nondefault-same-kind-profile` and `different-kind-boundary` remain pending", char_view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
