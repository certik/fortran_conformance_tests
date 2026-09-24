"""Metadata checks for generated Fortran 2023 procedure fixtures, 15.1-15.3.2.2."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_procedures_15_1_15_3_fixtures as generated


class Procedures151153FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_fixture_inventory_and_runtime_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), len(generated.CASES))
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 30)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["completion"]])
            self.assertEqual(expect.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])

    def test_sources_are_self_checking_ascii_and_rule_scoped(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("implicit none", source.lower())
            self.assertIn("error stop", source.lower())
            self.assertIn("print '(a)'", source)
            self.assertIn(spec["completion"].strip(), source)
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|common)\s*\(")
            self.assertNotRegex(source, r"(?i)iomsg\s*=")
            self.assertNotRegex(source, r"(?i)real\s*::\s*sentinel")

    def test_mutations_bind_complete_parent_and_feature_level_spans(self):
        total = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertTrue(any(item["kind"] == "feature" for item in generated.all_mutations(spec)))
            for mutation in generated.all_mutations(spec):
                total += 1
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertGreaterEqual(mutation["line"], 1)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, generated.all_mutations(spec)[0])
        self.assertEqual(total, 46)

    def test_catalogues_are_synced_and_rendered_for_discharged_facets(self):
        for section, catalogue_path in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            rendered = generated.render_view(catalogue, ROOT)
            if rendered is not None:
                self.assertEqual((ROOT / catalogue["render"]["path"]).read_text(), rendered)
        for rule, facets in generated.FACETS_BY_RULE.items():
            requirement = self.registry.requirements[rule]
            for facet in facets:
                self.assertNotIn(facet, requirement.get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], requirement["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], requirement["oracle_limitation"])
        checked_rules = set(generated.FACETS_BY_RULE) | set(generated.RESTORED_PENDING)
        still_pending = {
            facet for rule in checked_rules
            for facet in self.registry.requirements[rule].get("pending", {})
        }
        self.assertEqual(still_pending, {
            "non-fortran-means-defines-external-procedure",
            "intrinsic-module-specific-procedure-is-module-procedure",
            "internal-procedure-name-not-global",
            "procedure-kind-characteristic",
            "procedure-pure-characteristic",
            "procedure-simple-characteristic",
            "procedure-elemental-characteristic",
            "procedure-bind-characteristic",
            "procedure-dummy-arguments-characteristics",
            "procedure-function-result-characteristics",
            "dummy-data-object-characteristic",
            "dummy-procedure-characteristic",
            "dummy-asterisk-alternate-return-characteristic",
            "dummy-data-declared-type-characteristic",
            "dummy-data-type-parameters-characteristic",
            "dummy-data-shape-characteristic",
            "dummy-data-corank-codimensions-characteristic",
            "dummy-data-intent-characteristic",
            "dummy-data-optional-characteristic",
            "dummy-data-allocatable-characteristic",
            "dummy-data-asynchronous-contiguous-value-volatile-characteristics",
            "dummy-data-polymorphic-characteristic",
            "dummy-data-pointer-target-characteristics",
            "dummy-data-nonconstant-parameter-bound-dependence-characteristic",
            "dummy-data-assumed-or-deferred-properties-characteristic",
        })

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
