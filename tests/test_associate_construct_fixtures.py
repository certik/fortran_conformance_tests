"""Runtime fixtures for Fortran 2023 ASSOCIATE construct effects."""

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
import generate_associate_construct_fixtures as generated


class AssociateConstructFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_ten_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 20)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            expected_evidence = self.specs[case.name]["evidence"]
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
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect" if expected_evidence == "effect" else expected_evidence)
            bad_evidence = "effect" if case.meta.evidence == "positive-control" else "positive-control"
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence=bad_evidence)),
                                          self.registry.requirements[case.rule])
            for bad in (replace(case, meta=replace(case.meta, facets=[])),
                        replace(case, meta=replace(case.meta, facets=[case.meta.facets[0], "foreign"])),
                        replace(case, meta=replace(case.meta, facets=case.meta.facets * 2))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_pin_headers_selectors_associate_names_and_nonvacuity(self):
        anchors = {
            "expression_selector_value": [
                "! rule: S11.1.3.2-001\n! covers: expression-selector-value-before-block\n",
                "associate (value => seed + 17)", "seed=-900", "if (value /= 40)",
                "if (seed /= -900)"],
            "subscript_expression_capture": [
                "! rule: S11.1.3.2-001\n! covers: variable-designator-subexpressions-before-block\n",
                "integer :: a(1:4)", "idx=2", "associate (cell => a(idx))", "idx=4",
                "cell=77", "if (a(2) /= 77)", "if (a(4) /= 44)"],
            "expression_associate_read": [
                "! rule: S11.1.3.2-002\n! covers: associate-name-reads-expression-value\n",
                "associate (expr_value => left*10 + right)", "left=-1", "right=-2",
                "if (expr_value /= 125)"],
            "variable_selector_define": [
                "! rule: S11.1.3.2-002\n! covers: associate-name-defines-variable-selector\n",
                "target=314", "associate (alias => target)", "alias=271", "if (target /= 271)"],
            "outer_homonym_scope": [
                "! rule: S11.1.3.2-002\n! covers: associate-name-not-outside-block-source\n",
                "item=707", "target=101", "associate (item => target)", "item=303",
                "if (item /= 707)", "if (target /= 303)"],
            "character_length_parameter": [
                "! rule: S11.1.3.2-003\n! covers: character-length-type-parameter\n",
                "character(len=9) :: parent", "associate (slice => parent(3:8))",
                "if (len(slice) /= 6)", "if (len(parent) /= 9)"],
            "rank_shape": [
                "! rule: S11.1.3.3-001\n! covers: same-rank-as-selector\n",
                "integer :: grid(-2:4,7:12)", "associate (tile => grid(-1:3:2,8:12:4))",
                "dims=shape(tile)", "if (dims(1) /= 3)", "if (dims(2) /= 2)"],
            "lower_bound_lbound": [
                "! rule: S11.1.3.3-001\n! covers: nondefault-lower-bound\n",
                "integer :: base(-5:5)", "associate (whole => base)", "whole_lower=lbound(whole,1)",
                "associate (sec => base(-3:3:2))", "section_lower=lbound(sec,1)",
                "if (whole_lower /= -5)", "if (section_lower /= 1)"],
            "upper_bound_extent": [
                "! rule: S11.1.3.3-001\n! covers: upper-bound-from-extent\n",
                "integer :: base(10:21)", "associate (vec => base(12:20:3))",
                "lo=lbound(vec,1)", "hi=ubound(vec,1)", "extent=size(vec)",
                "if (lo /= 1)", "if (extent /= 3)", "if (hi /= 3)"],
            "definable_selector_assignment": [
                "! rule: S11.1.3.3-005\n! covers: definable-selector-assignment-control\n",
                "integer :: store(5:9)", "associate (vec => store(6:8))", "vec=[601,602,603]",
                "if (store(6) /= 601)", "if (store(7) /= 602)", "if (store(8) /= 603)",
                "if (store(5) /= 50)"],
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
            self.assertNotRegex(source, r"(?i)\b(real|complex|procedure|call|selected_int_kind|c_loc|loc|transfer)\b")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|error\s+stop\s+[0-9])\b")
            if variant == "character_length_parameter":
                self.assertIn("if (len(slice) /= 6)", source)
                self.assertNotRegex(source, r"slice\s*/=")
            for needle in anchors[variant]:
                self.assertIn(needle, source)
            mutated_header = source.replace("! covers: " + spec["facets"][0], "! covers: foreign", 1)
            self.assertNotEqual(mutated_header, source)
            self.assertNotIn("! covers: " + spec["facets"][0] + "\n", mutated_header)

    def test_guard_probe_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 44)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 43)
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
                    if probe["id"].startswith("omit-observation") or probe["id"] == "omit-all-observations":
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
        self.assertEqual(vectors, 261)

    def test_catalogue_sync_removes_only_selected_runtime_facets_and_regenerates_views(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, remaining in generated.REMAINING_PENDING.items():
                if rule not in by_rule:
                    continue
                self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
                for facet in generated.FACETS_BY_RULE.get(rule, []):
                    self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                    self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
                    self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            synced = generated.synced_catalogue(section, catalogue)
            self.assertEqual(synced, catalogue)
            view = generated.render_view(section, synced)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn(generated.SUMMARY_END, view)
        self.assertNotIn("block-executes-after-selector-evaluation",
                         self.registry.requirements["S11.1.3.2-001"].get("pending", {}))
        self.assertIn("outside-end-associate-branch-rejected",
                      self.registry.requirements["S11.1.3.2-005"]["pending"])
        self.assertIn("nondefinable-selector-definition-rejected",
                      self.registry.requirements["S11.1.3.3-005"]["pending"])

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
