"""Runtime fixtures for Fortran 2023 10.1.4 evaluation of operations."""

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
import generate_evaluation_operations_fixtures as generated


class EvaluationOperationsFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_fourteen_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 28)
        self.assertEqual(sum(len(case.meta.facets) for case in self.cases.values()), 14)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for _, facet in generated.VARIANTS.values()})
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(generated.VARIANTS[spec["variant"]], (case.rule, case.meta.facets[0]))
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

    def test_sources_pin_headers_integer_oracles_and_nonvacuity_anchors(self):
        anchors = {
            "unary_intrinsic_operand_value": ["x = -7", "y = 4", "r1 = -x", "r2 = -y", "if (r2 /= -4)"],
            "binary_intrinsic_both_operand_values": ["left = 19", "right = 6", "forward = left - right", "if (reverse /= -13)"],
            "array_intrinsic_element_values": ["a = [8,-3,15]", "b = [2,5,-4]", "[6,-8,19]", "sum(result)"],
            "implied_do_initial_expression": ["integer :: i", "i=1+1, 4", "[2,3,4]"],
            "implied_do_terminal_expression": ["i=1, 2+2", "[1,2,3,4]"],
            "implied_do_stride_expression": ["i=1, 5, 1+1", "[1,3,5]"],
            "nested_implied_do_controls": ["integer :: i, j", "i=2-1, 3, 1+1", "j=1+2, 4+1, 1+1", "[13,33,15,35]"],
            "scalar_left_array_right": ["a = [1,4,7]", "result = 10 - a", "[9,6,3]"],
            "array_left_scalar_right": ["a = [1,4,7]", "result = a - 10", "[-9,-6,-3]"],
            "same_shape_array_operands": ["a = [1,2,3]", "b = [10,20,30]", "[11,22,33]"],
            "corresponding_element_pairing": ["a = [1,100,7]", "b = [10,1,-5]", "[-9,99,12]"],
            "intrinsic_unary_array_values": ["a = [1,-2,3]", "result = -a", "[-1,2,-3]"],
            "unary_result_same_shape": ["a(2,-1) = -11", "a(3,1) = -32", "shape(-a)", "[2,3]"],
            "pure_elemental_function_array_values": ["pure elemental integer function bump", "bump = x + 3", "[1,3,8]"],
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
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|common|pointer|target|allocatable|coarray)\b")
            self.assertNotRegex(source, r"(?i)\b(real|complex)\b")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            mutated = source.replace("! covers: " + spec["facets"][0], "! covers: foreign", 1)
            self.assertNotEqual(mutated, source)
            self.assertNotIn("! covers: " + spec["facets"][0] + "\n", mutated)

    def test_guard_input_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 58)
        self.assertEqual(sum(len(spec["input_probes"]) for spec in self.specs.values()), 21)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 58)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["guards"]), len(spec["observations"]) + 2)
            hashes = set()
            for probe in spec["probes"] + spec["input_probes"]:
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
            stdout, stderr, code, outcome = probe.get("failure_stdout") or "EOP:mutated\n", "ERROR STOP\n", 2, "fail"
        trace = [dict(phase=phase, returncode=0, timed_out=False, stdout="", stderr="")
                 for phase in ("compile", "link", "run")]
        trace[-1].update(returncode=code, stdout=stdout, stderr=stderr)
        return dict(outcome=outcome, phase="run", trace=trace, input_hashes={"source.f90": generated.sha(raw)})

    def test_each_planned_failure_requires_current_complete_parent(self):
        vectors = 0
        for spec in self.specs.values():
            parent = self.probe_check(spec)
            for probe in spec["probes"] + spec["input_probes"] + spec["omissions"]:
                verdict = self.local_verdict(spec, probe, parent, self.probe_check(spec, probe), True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                bad_parent = copy.deepcopy(parent)
                bad_parent["input_hashes"]["source.f90"] = "0" * 64
                blocked = self.local_verdict(spec, probe, bad_parent, self.probe_check(spec, probe), True)
                self.assertFalse(blocked["qualified"])
                untested = self.local_verdict(spec, probe, parent, None, True)
                self.assertEqual((untested["status"], untested["qualified"]), ("UNTESTED", False))
                vectors += 3
        self.assertEqual(vectors, 411)

    def local_verdict(self, spec, probe, parent, observed, parent_binding_current):
        parent_passed = (parent_binding_current and parent.get("outcome") == "pass"
                         and parent.get("input_hashes") == {"source.f90": spec["source_sha256"]}
                         and parent["trace"][-1]["stdout"] == spec["completion"]
                         and parent["trace"][-1]["stderr"] == "" and parent["trace"][-1]["returncode"] == 0)
        if observed is None:
            return dict(status="UNTESTED", qualified=False, parent_passed=bool(parent_passed), intended_failure=False)
        intended = (observed.get("outcome") == "fail"
                    and observed.get("input_hashes") == {"source.f90": generated.sha(generated.wrong_oracle_source(spec, probe))})
        return dict(status="sensitive" if parent_passed and intended else "not-sensitive",
                    qualified=bool(parent_passed and intended), parent_passed=bool(parent_passed),
                    intended_failure=bool(intended))

    def test_catalogue_sync_removes_only_selected_facets_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), generated.REMAINING_PENDING[rule])
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertIn("pure-element-order-latitude", by_rule["S10.1.4-005"].get("pending", {}))
        self.assertIn("condition-order-without-side-effects", by_rule["S10.1.4-006"].get("pending", {}))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("pure-element-order-latitude` facet remains pending/unimplemented", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
