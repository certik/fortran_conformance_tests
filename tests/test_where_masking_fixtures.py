"""Runtime fixtures for Fortran 2023 WHERE masking semantics."""

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
import generate_where_masking_fixtures as generated


class WhereMaskingFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 44)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 22)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for _, facet, _ in generated.VARIANTS.values()})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(generated.VARIANTS[spec["variant"]],
                             (case.rule, case.meta.facets[0], spec["scenario"]))
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["completion"]])
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

    def test_sources_pin_headers_masks_bounds_and_literal_oracles(self):
        anchors = {
            "where_stmt_nonunit": [
                "integer :: actual(-2:3), rhs(-2:3)", "mask(-2)=.true.",
                "mask(3)=.false.", "where (mask) actual = rhs",
                "Expected final actual(-2:3) = [501,-901,503,-899,505,-897].",
                "if (actual(-1) /= -901)", "if (actual(2) /= 505)"],
            "where_construct_simple": [
                "Construct control mask true at 1, 3 and 6.", "where (mask)", "actual = rhs",
                "Expected final actual(1:6) = [101,-702,103,-704,-705,106].",
                "if (actual(4) /= -704)"],
            "where_construct_elsewhere": [
                "first_mask=[T,F,F,T,F,T], second_mask=[T,T,F,T,F,F].",
                "elsewhere (second_mask)", "Expected final actual(1:6) = [101,202,303,104,305,106].",
                "if (actual(2) /= 202)", "if (actual(5) /= 305)"],
            "nested_construct_simple": [
                "where (outer_mask)", "where (inner_mask)", "elsewhere", "end where",
                "Expected final actual(1:6) = [101,202,-803,-804,205,106].",
                "Statement-like nesting would not give positions 2 and 5"],
            "nested_construct_restore": [
                "actual = actual + 1000", "Expected final actual(1:6) = [1101,1202,303,304,1205,1106].",
                "If inner pending leaked outward", "if (actual(3) /= 303)"],
            "nested_stmt_simple": [
                "where (inner_mask) actual = then_values", "Expected final actual(1:6) = [101,-802,-803,-804,-805,106].",
                "outer-false position 3 has inner true but stays sentinel"],
            "nested_stmt_pending": [
                "where (inner_mask) actual = then_values", "elsewhere", "actual = outer_else_values",
                "Expected final actual(1:6) = [101,-802,303,304,-805,106].",
                "positions 2 and 5 would be assigned by the outer ELSEWHERE"],
            "nested_stmt_restore": [
                "actual = actual + 1000", "Expected final actual(1:6) = [1101,198,-803,-804,195,1106].",
                "restored outer control mask"]
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn(f"! rule: {spec['rule']}\n! covers: {spec['facets'][0]}\n", source)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn("Sentinels are distinct from every value any WHERE branch can assign.", source)
            self.assertIn("Expected values below are hand-written scalar literals", source)
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\b(merge|pack|count|unpack|all|any)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(real|complex)\b")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|error\s+stop\s+[0-9])\b")
            for needle in anchors[spec["scenario"]]:
                self.assertIn(needle, source)

    def test_guard_probe_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 176)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 176)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["observations"]), 6)
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
        self.assertEqual(vectors, 1056)

    def test_catalogue_sync_removes_only_selected_runtime_facets_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), generated.REMAINING_PENDING[rule])
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIX[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIX[rule], by_rule[rule]["oracle_limitation"])
        untouched = {
            "S10.2.3.2-002": {"where-stmt-mask-single-snapshot", "where-construct-mask-single-snapshot", "masked-elsewhere-mask-single-snapshot"},
            "S10.2.3.2-009": {"nonelemental-rhs-array-result-selected", "nonelemental-mask-result-source-control", "nonelemental-argument-unmasked-source-control"},
            "S10.2.3.2-010": {"elemental-operation-selected-elements", "elemental-function-selected-elements", "elemental-mask-expression-selected-elements"},
            "S10.2.3.2-011": {"rhs-array-constructor-values-selected", "mask-array-constructor-controls-branches"},
            "S10.2.3.2-013": {"where-stmt-mask-value-stable", "where-construct-mask-value-stable", "elsewhere-mask-value-stable"},
            "S10.2.3.2-014": {"mask-function-affects-rhs-entity-control", "mask-function-affects-variable-entity-source-control"},
        }
        for rule, pending in untouched.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), pending)
        form_catalogue = self.registry.catalogues[generated.FORM_SECTION]
        self.assertEqual(sum(len(row.get("pending", {})) for row in form_catalogue["requirements"]), 34)
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Twenty-two complete run/effect/f2023 programs", view)
        self.assertIn("At-most-once mask evaluation", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
