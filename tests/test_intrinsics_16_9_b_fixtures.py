"""Runtime fixture metadata for Fortran 2023 intrinsics 16.9.11-16.9.17."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement
from dataclasses import replace

sys.path.insert(0, str(ROOT / "tools"))
import generate_intrinsics_16_9_b_fixtures as generated


class Intrinsics169BFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_owned_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(case) for case in generated.CASES})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 2 * len(generated.CASES))
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             ("valid", self.specs[case.name]["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                              case.fixture.expectation.exit_code), ("run", "success", 0))
            self.assertEqual(case.fixture.expectation.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            expected_cohort = "positive-control" if case.meta.evidence == "positive-control" else "runtime-effect"
            self.assertEqual(self.members[case.name]["cohort"], expected_cohort)
            self.assertEqual(generated.FACETS_BY_RULE[case.rule], case.meta.facets)
            wrong_evidence = "effect" if case.meta.evidence == "positive-control" else "positive-control"
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence=wrong_evidence)),
                                          self.registry.requirements[case.rule])

    def test_sources_pin_exact_or_bounded_oracles(self):
        anchors = {
            "aint_arguments": ["observed = aint(2.5)", "aint(high, kind=kind(0.0))"],
            "aint_result_kind": ["kind(aint(high, kind=kind(0.0)))", "kind(aint(high))"],
            "aint_truncation_values": ["below_one = aint(0.5)", "positive = aint(2.5)", "negative = aint(-2.5)"],
            "all_arguments": ["reduced = all(mask, dim=1)", "reduced = all(mask, dim=2)"],
            "all_result_characteristics": ["kind(all(vector))", "scalar_result = all(vector, dim=1)"],
            "all_result_values": ["all(empty)", "all(has_false)", "reduced = all(mask2, dim=1)"],
            "allocated_arguments": ["allocate(array(2))", "allocated(scalar)"],
            "allocated_result_characteristics": ["kind(allocated(array))", "status = allocated(array)"],
            "allocated_result_values": ["allocate(array(4))", "scalar_status = allocated(scalar)"],
            "anint_arguments": ["observed = anint(2.25)", "anint(high, kind=kind(0.0))"],
            "anint_result_kind": ["kind(anint(high, kind=kind(0.0)))", "kind(anint(high))"],
            "anint_nearest_values": ["near_pos = anint(2.25)", "tie_pos = anint(2.5)", "tie_neg = anint(-2.5)"],
            "any_or_reduction": ["observed = any(mask)", ".or."],
            "any_transformational_class": ["scalar_result = any(mask)", "reduced = any(mask, dim=1)"],
            "any_arguments": ["reduced = any(mask, dim=1)", "reduced = any(mask, dim=2)"],
            "any_result_characteristics": ["kind(any(vector))", "scalar_result = any(vector, dim=1)"],
            "any_result_values": ["any(empty)", "any(all_false)", "reduced = any(mask2, dim=1)"],
            "asin_operation": ["values = asin(inputs)", "values < -2.0", "values > 2.0"],
            "asin_elemental_class": ["values = asin(inputs)", "shape(values)", "values(1) >= 0.0"],
            "asin_arguments": ["real_values = asin([-1.0, 0.0, 1.0])", "z_value = asin(z)"],
            "asin_result_characteristics": ["kind(asin(high_inputs(1)))", "size(asin(high_inputs))", "kind(asin(z))"],
            "asin_real_range": ["values = asin(inputs)", "values < -2.0", "values > 2.0"],
            "asin_complex_range": ["z_value = asin(z)", "part = real(z_value)"],
            "asind_operation": ["values = asind(inputs)", "values < -90.0", "values > 90.0"],
            "asind_elemental_class": ["values = asind(inputs)", "shape(values)", "values(1) >= 0.0"],
            "asind_arguments": ["values = asind([-1.0, 0.0, 1.0])"],
            "asind_result_characteristics": ["kind(asind(high_inputs(1)))", "size(asind(high_inputs))"],
            "asind_degree_range": ["values = asind(inputs)", "values < -90.0", "values > 90.0"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(source.count("checks=checks+1"), spec["checks"])
            self.assertIn(f"case ({spec['checks']})", source)
            self.assertNotRegex(source, r"(?i)\b(random_number|system_clock|transfer|loc|c_loc|epsilon|spacing)\s*\(")
            if spec["section"] in {"16.9.16", "16.9.17"}:
                self.assertNotRegex(source, r"/=?\s*[0-9]+\.[0-9]{3,}")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()),
                         sum(len(spec["facets"]) + 2 for spec in self.specs.values()))
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["feature_mutations"]), len(spec["facets"]))
            self.assertEqual({mutation["facet"] for mutation in spec["feature_mutations"]},
                             set(spec["facets"]))
            self.assertEqual(len(spec["oracle_mutations"]), 1)
            hashes = set()
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["mutations"][0])

    def test_catalogues_sync_and_restores_unclaimed_facets_pending(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.FACETS_BY_RULE.items():
                if not rule.startswith("S" + section):
                    continue
                for facet in facets:
                    self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            for rule, remaining in generated.REMAINING_PENDING.items():
                if rule in by_rule:
                    self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
            for rule, row in by_rule.items():
                if rule not in generated.FACETS_BY_RULE:
                    self.assertNotIn(f"{rule} {generated.TOPIC} runtime fixture: ", row.get("oracle", ""))
                    self.assertNotIn(f"{rule} {generated.TOPIC} fixture boundaries: ",
                                     row.get("oracle_limitation", ""))
            synced = generated.synced_catalogue(section, catalogue)
            self.assertEqual(synced, catalogue)
            view = generated.render_view(section, synced)
            self.assertIn(f"<!-- BEGIN INTRINSICS 16.9.B FIXTURES {section} -->", view)
            self.assertIn("executable fixture observations", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
