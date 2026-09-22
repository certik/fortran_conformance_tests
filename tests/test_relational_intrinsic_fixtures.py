"""Runtime fixtures for Fortran 2023 relational intrinsic operation interpretation."""

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
import generate_relational_intrinsic_fixtures as generated


class RelationalIntrinsicFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_eleven_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 22)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(generated.VARIANTS[self.specs[case.name]["variant"]],
                             (case.rule, tuple(case.meta.facets)))
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
                        replace(case, meta=replace(case.meta, facets=case.meta.facets + case.meta.facets[:1]))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_pin_operands_lengths_and_nonduplicating_oracles(self):
        anchors = {
            "default_logical_result": [
                "! rule: S10.1.5.5.1-001\n! covers: two-operand-comparison\n",
                "left = -3", "right = 2", "observed = left < right",
                "false_control = right < left", "if (false_control) then"],
            "lt_symbolic_pair": [
                "! rule: S10.1.5.5.1-002\n! covers: lt-symbolic-pair\n",
                "less_left = -4", "equal_left = 5", "greater_left = 8",
                "dotted_less = less_left .LT. less_right", "symbolic_less = less_left < less_right",
                "dotted_equal = equal_left .LT. equal_right", "symbolic_greater = greater_left < greater_right"],
            "le_symbolic_pair": [
                "! covers: le-symbolic-pair\n", "dotted_less = less_left .LE. less_right",
                "symbolic_less = less_left <= less_right", "dotted_equal = equal_left .LE. equal_right",
                "symbolic_greater = greater_left <= greater_right"],
            "gt_symbolic_pair": [
                "! covers: gt-symbolic-pair\n", "dotted_less = less_left .GT. less_right",
                "symbolic_equal = equal_left > equal_right", "dotted_greater = greater_left .GT. greater_right",
                "symbolic_greater = greater_left > greater_right"],
            "ge_symbolic_pair": [
                "! covers: ge-symbolic-pair\n", "dotted_less = less_left .GE. less_right",
                "symbolic_equal = equal_left >= equal_right", "dotted_greater = greater_left .GE. greater_right",
                "symbolic_greater = greater_left >= greater_right"],
            "eq_symbolic_pair": [
                "! covers: eq-symbolic-pair\n", "less_left = -4", "equal_left = 5", "greater_left = 8",
                "dotted_less = less_left .EQ. less_right", "symbolic_less = less_left == less_right",
                "dotted_equal = equal_left .EQ. equal_right"],
            "ne_symbolic_pair": [
                "! covers: ne-symbolic-pair\n", "less_left = -4", "equal_left = 5", "greater_left = 8",
                "dotted_less = less_left .NE. less_right", "symbolic_less = less_left /= less_right",
                "dotted_equal = equal_left .NE. equal_right"],
            "same_length_character_equality": [
                "! covers: same-length-character-equality\n", "character(len=2) :: left, same, different",
                "left = 'M5'", "same = 'M5'", "different = 'M6'",
                "select case (len(different))", "equal_result = left == same"],
            "right_blank_padding_equality": [
                "! covers: right-blank-padding-equality\n! covers: all-characters-equal\n",
                "character(len=1) :: short", "character(len=2) :: padded",
                "short = 'A'", "padded = 'A '", "Padding extends short to 'A '"],
            "right_blank_padding_inequality": [
                "! covers: right-blank-padding-inequality\n", "character(len=4) :: long",
                "long = 'A  B'", "Padding extends short to 'A   '", "unequal_result = short /= long"],
            "zero_length_equality": [
                "! covers: zero-length-equality\n", "character(len=0) :: left, right",
                "left = ''", "right = ''", "equal_result = left == right", "unequal_result = left /= right"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            variant = spec["variant"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn(f"case ({len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\b(max|min|merge|transfer|loc|c_loc|trim|index|repeat)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(llt|lle|lgt|lge|achar|iachar|selected_char_kind)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(real|complex|cmplx|coarray|sync\s+all)\b")
            if variant.startswith(("lt_", "le_", "gt_", "ge_", "eq_", "ne_")):
                self.assertIn(".neqv.", source.lower())
                for row in generated.ROW_ORDER:
                    self.assertIn(f"dotted_{row}", source)
                    self.assertIn(f"symbolic_{row}", source)
            if "character" in variant or "padding" in variant or "zero_length" in variant:
                self.assertRegex(source, r"(?i)\blen\s*\(")
            for needle in anchors[variant]:
                self.assertIn(needle, source)
            for facet in spec["facets"]:
                mutated_header = source.replace("! covers: " + facet, "! covers: foreign", 1)
                self.assertNotEqual(mutated_header, source)
                self.assertNotIn("! covers: " + facet + "\n", mutated_header)

    def test_guard_probe_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 169)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 94)
        wrong_operator = [
            probe for spec in self.specs.values() for probe in spec["probes"]
            if probe["mutation"] == "wrong-operator-substitution"]
        self.assertEqual(len(wrong_operator), 60)
        self.assertEqual({
            (probe["expected"], probe["replacement"]) for probe in wrong_operator
        }, {
            (generated.PAIR_OPERATORS[operator + "_symbolic_pair"][spelling],
             generated.PAIR_OPERATORS[alternative + "_symbolic_pair"][spelling])
            for operator in generated.OPERATOR_ORDER
            for alternative in generated.OPERATOR_ORDER
            if alternative != operator
            for spelling in ("dotted", "symbolic")
        })
        saw_reverse = False
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
                saw_reverse = saw_reverse or probe["mutation"] == "reverse-operand-mutation"
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
        self.assertTrue(saw_reverse)

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
        self.assertEqual(vectors, 789)

    def test_each_operator_row_set_distinguishes_all_alternatives(self):
        self.assertEqual(len(generated.DISCRIMINATION_ROWS), 30)
        for operator in generated.OPERATOR_ORDER:
            row_truths = [generated.TRUTH_TABLE[operator][row] for row in generated.ROW_ORDER]
            for alternative in generated.OPERATOR_ORDER:
                if alternative == operator:
                    continue
                row = generated.DISCRIMINATION_ROWS[(operator, alternative)]
                self.assertIn(row, generated.ROW_ORDER)
                self.assertNotEqual(generated.TRUTH_TABLE[operator][row],
                                    generated.TRUTH_TABLE[alternative][row])
                self.assertNotEqual(row_truths,
                                    [generated.TRUTH_TABLE[alternative][row] for row in generated.ROW_ORDER])

    def test_catalogue_sync_removes_only_selected_runtime_facets_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, remaining in generated.REMAINING_PENDING.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
            for facet in generated.FACETS_BY_RULE[rule]:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
        self.assertIn(generated.GENERAL_ORACLE_PREFIX, by_rule[generated.RULE_GENERAL]["oracle"])
        self.assertIn(generated.PAIR_ORACLE_PREFIX, by_rule[generated.RULE_PAIRS]["oracle"])
        self.assertIn(generated.CHAR_ORACLE_PREFIX, by_rule[generated.RULE_CHAR_EQUALITY]["oracle"])
        self.assertIn(generated.GENERAL_LIMIT_PREFIX, by_rule[generated.RULE_GENERAL]["oracle_limitation"])
        self.assertIn(generated.PAIR_LIMIT_PREFIX, by_rule[generated.RULE_PAIRS]["oracle_limitation"])
        self.assertIn(generated.CHAR_LIMIT_PREFIX, by_rule[generated.RULE_CHAR_EQUALITY]["oracle_limitation"])
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Eleven complete run/effect/f2023 programs", view)
        self.assertIn("S10.1.5.5.1-003 through -008", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
