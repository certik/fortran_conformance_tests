"""Runtime fixture metadata for Fortran 2023 ALLOCATE execution effects."""

import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_allocate_execution_fixtures as generated


class AllocateExecutionFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_ten_owned_f2023_effect_fixtures(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 20)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, set().union(*map(set, generated.FACETS_BY_RULE.values())))
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expect.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence="positive-control")),
                                          self.registry.requirements[case.rule])

    def test_sources_assert_bounds_shape_size_values_and_avoid_forbidden_oracles(self):
        required = {
            "explicit_bounds": ["allocate(a(3:5)", "lbound(a,1) /= 3", "ubound(a,1) /= 5", "size(a) /= 3"],
            "default_lower": ["allocate(a(4)", "allocate(b(-2:1))", "lbound(a,1) /= 1"],
            "bound_capture": ["lo = 2", "hi = 4", "allocate(a(lo:hi)", "lo = -5", "hi = 9"],
            "zero_extent": ["allocate(a(5:3)", "size(a) /= 0", "reached /= 917"],
            "source_shape_bounds": ["allocate(s(-3:-1,5:8))", "allocate(a, source=s", "lbound(a) /= [-3,5]"],
            "source_same_rank_vector": ["allocate(a(-4:-2), source=[11,22,33]", "a(-4) /= 11"],
            "source_scalar_broadcast": ["allocate(a(-2:2), source=7", "size(a) /= 5", "a(2) /= 7"],
            "source_rank_two_array": ["integer :: s(2:4,7:8)", "allocate(a(2:4,7:8), source=s"],
            "source_evaluated_once": ["allocate(a, source=produce()", "counter /= 1", "produce=79"],
            "mold_undefined_value": ["allocate(mold(-6:-4,2:5))", "allocate(a, mold=mold", "a(-6,2)=612"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            variant = spec["variant"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("allocated(", source)
            if variant == "zero_extent":
                self.assertIn("size(a) /= 0", source)
            elif variant == "source_evaluated_once":
                self.assertIn("counter /= 1", source)
                self.assertIn("a /= 79", source)
            else:
                self.assertRegex(source, r"lbound\(")
                self.assertRegex(source, r"ubound\(|size\(")
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|common)\s*\(")
            self.assertNotRegex(source, r"(?i)errmsg\s*=")
            if variant == "zero_extent":
                self.assertNotRegex(source, r"a\([^)]*\)\s*(?:=|/=)")
            for needle in required[variant]:
                self.assertIn(needle, source)
            self.assertNotIn("source=0", source.lower())

    def test_mutation_spans_bind_complete_parent_and_include_feature_level(self):
        self.assertEqual(sum(len(generated.all_mutations(spec)) for spec in self.specs.values()), 273)
        self.assertEqual(sum(len(spec["feature_mutations"]) for spec in self.specs.values()), 11)
        self.assertEqual(sum(len(spec["reverse_mutations"]) for spec in self.specs.values()), 1)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["feature_mutations"]), 1)
            self.assertGreaterEqual(len(spec["input_mutations"]), 1)
            for mutation in generated.all_mutations(spec):
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, generated.all_mutations(spec)[0])
        reverse_specs = [spec for spec in self.specs.values() if spec["reverse_mutations"]]
        self.assertEqual([spec["variant"] for spec in reverse_specs], ["source_scalar_broadcast"])
        reverse = generated.mutated_source(reverse_specs[0], reverse_specs[0]["reverse_mutations"][0]).decode("ascii")
        self.assertIn("source=8", reverse)
        self.assertEqual(reverse.count("/= 8"), 5)
        self.assertNotIn("source=7", reverse)

    def test_catalogue_sync_removes_only_selected_pending_facets_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        for rule, remaining in generated.REMAINING_PENDING.items():
            if rule in by_rule:
                self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Ten complete run/effect/f2023 fixtures cover thirteen selected facets", view)
        self.assertIn("remain pending with their original plans", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
