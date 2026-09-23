"""Runtime fixtures for Fortran 2023 structure component effects."""

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
import generate_structure_component_fixtures as generated


class StructureComponentFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_twelve_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 24)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for _, facet in generated.VARIANTS.values()})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
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

    def test_sources_pin_rank_shape_bounds_values_and_no_layout_oracles(self):
        anchors = {
            "array_component": ["integer :: avec(-5:-3)", "if (any(shape(obj%avec) /= [3]))",
                                "if (any(lbound(obj%avec) /= [-5]))", "if (any(ubound(obj%avec) /= [-3]))"],
            "bare_part_name_rank": ["! covers: bare-part-name-rank", "obj%avec = [911, 919, 929]",
                                    "if (any(obj%avec /= [911, 919, 929]))"],
            "triplet_rank_contribution": ["! covers: triplet-rank-contribution", "obj%grid(-4:-3,7)",
                                           "if (any(shape(obj%grid(-4:-3,7)) /= [2]))"],
            "vector_subscript_rank_contribution": ["! covers: vector-subscript-rank-contribution",
                                                    "picks = [-2, -4]", "obj%grid(picks,8)",
                                                    "if (any(obj%grid(picks,8) /= [284, 484]))"],
            "rank_from_nonzero_part_ref": ["! covers: rank-from-nonzero-part-ref", "x(2:6:2)%alpha",
                                           "if (any(shape(x(2:6:2)%alpha) /= [3]))",
                                           "if (any(x(2:6:2)%alpha /= [311, 317, 331]))"],
            "rank_zero_when_no_nonzero_part_ref": ["! covers: rank-zero-when-no-nonzero-part-ref",
                                                   "if (obj%alpha + 17 /= 690)"],
            "base_object_leftmost": ["left_obj%inner%alpha = 971", "right_obj%inner%alpha = 1091",
                                     "if (left_obj%inner%alpha /= 971)"],
            "type_from_rightmost": ["if (obj%alpha + 37 /= 1268)", "if (len(obj%text) /= 5)",
                                    "if (obj%text /= 'ABCDE')"],
            "type_parameters_from_rightmost": ["character(len=5) :: text", "character(len=7) :: longer_text",
                                               "if (len(obj%text) /= 5)", "if (len(obj%longer_text) /= 7)"],
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
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|common|coarray|sync\s+all)\b")
            self.assertNotIn("x%avec", source)
            self.assertNotIn("x%bvec", source)
            self.assertIn("if (x(2)%alpha /=", source)
            self.assertIn("x(3)%alpha =", source)
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)
            if "text" in source:
                self.assertRegex(source, r"len\([^)]*%[a-z_]*text\)")
                for literal in re.findall(r"'([^']*)'", source):
                    if literal.startswith(("SC:", "STRUCTURE COMPONENT")):
                        continue
                    self.assertNotEqual(literal, "")
                    self.assertNotRegex(literal, r"\s$|^\s")

    def test_catalogue_pending_and_boundaries(self):
        catalogue = json.loads((ROOT / generated.CATALOGUE).read_text())
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            self.assertFalse(set(facets) & set(by_rule[rule]["pending"]))
            self.assertEqual(set(by_rule[rule]["pending"]), generated.REMAINING_PENDING[rule])
            self.assertIn(generated.ORACLE_PREFIX[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIX[rule], by_rule[rule]["oracle_limitation"])
        self.assertIn("multiple-section-subscript-rank-contribution", by_rule["S9.4.2-002"]["pending"])
        self.assertIn("x%a", by_rule["S9.4.2-003"]["oracle_limitation"])

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 116)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 87)
        self.assertEqual(sum(len(spec["feature_mutations"]) for spec in self.specs.values()), 52)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 116)
        self.assertEqual(sum(len(spec["reverse_mutations"]) for spec in self.specs.values()), 12)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            hashes = set()
            categories = {m["category"] for m in spec["feature_mutations"]}
            self.assertIn("component-reference", categories)
            self.assertIn("parent-subscript", categories)
            self.assertIn("component-value-swap", categories)
            for probe in generated.all_failing_mutations(spec):
                if "span" in probe:
                    start, end = probe["span"]
                    self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                    mutant = generated.mutated_source(spec, probe)
                    self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                else:
                    mutant = generated.mutated_source(spec, probe)
                    self.assertNotEqual(mutant, raw)
                    for span, replacement in zip(probe["spans"], probe["replacements"]):
                        start, end = span
                        self.assertEqual(raw[start:end].decode("ascii"), replacement["expected"])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for reverse in spec["reverse_mutations"]:
                mutant = generated.mutated_source(spec, reverse)
                self.assertNotEqual(mutant, raw)
                self.assertIn(b"STRUCTURE COMPONENT", mutant)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["probes"][0])

    def probe_check(self, spec, probe=None):
        raw = spec["source"].encode("ascii") if probe is None else generated.mutated_source(spec, probe)
        if probe is None or probe.get("kind") == "reverse":
            stdout, stderr, code, outcome = spec["completion"], "", 0, "pass"
        elif probe["kind"] == "output":
            stdout = "" if probe["mutation"] == "completion-statement-omission" else probe["replacement"] + "\n"
            stderr, code, outcome = "", 0, "fail"
        else:
            stdout, stderr, code, outcome = probe.get("failure_stdout", ""), "ERROR STOP\n", 2, "fail"
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
        self.assertEqual(vectors, 696)


if __name__ == "__main__":
    unittest.main()
