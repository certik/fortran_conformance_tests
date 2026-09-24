"""Tests for generated Clause 14 submodule and block data fixtures."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_submodule_block_data_fixtures as generated


class SubmoduleBlockDataFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_generated_case_set_and_manifest_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 23)
        self.assertEqual(sum(1 for case in self.cases.values() if case.kind == "invalid"), 8)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 46)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.coarray or case.meta.profiles or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            validate_case_requirement(case, self.registry.requirements[case.rule],
                                      case.rule in self.registry.numbered)
            if case.kind == "valid" and not spec.get("compile_only"):
                self.assertEqual(self.members[case.name]["cohort"],
                                 "runtime-effect" if case.meta.evidence == "effect" else "positive-control")
                self.assertIn(case.meta.evidence, {"effect", "positive-control"})
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                                  case.fixture.expectation.exit_code), ("run", "success", 0))
                self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
            elif case.kind == "valid":
                self.assertEqual(self.members[case.name]["cohort"], "positive-control")
                self.assertEqual(case.meta.evidence, "positive-control")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "success"))
            else:
                self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only")
                self.assertEqual(case.meta.evidence, "effect")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "diagnose"))
                diag = case.fixture.expectation.diagnostic
                self.assertEqual((diag["file"], diag["line"], diag["end_line"]),
                                 ("source.f90", spec["line"], spec["end_line"]))
                self.assertEqual(diag["contains_any"], spec["messages"])
                for banned in generated.EXCLUSIONS:
                    self.assertIn(banned, diag["excludes_any"])
                self.assertIn(spec["control"], self.cases)

    def test_submodule_sources_exercise_host_tree_and_diagnostics(self):
        tree = self.specs["S14_2_3_004_valid__submodule_host_association"]["source"]
        for needle in [
            "module host_assoc_m", "integer, parameter :: module_base = 17",
            "submodule (host_assoc_m) host_parent", "integer, parameter :: parent_base = 30",
            "submodule (host_assoc_m:host_parent) host_child",
            "value = module_base + 5", "if (parent_host_value() /= 41)",
        ]:
            self.assertIn(needle, tree)
        pairs = self.specs["S14_2_3_002_valid__submodule_relationships"]["source"]
        self.assertEqual(pairs.count("submodule (relation_left_m) impl"), 1)
        self.assertEqual(pairs.count("submodule (relation_right_m) impl"), 1)
        self.assertIn("submodule (relation_root_m:relation_parent) relation_child", pairs)
        self.assertIn("if (left_value() /= 14)", pairs)
        self.assertIn("if (right_value() /= 23)", pairs)
        invalid_statement = self.specs["R1417_invalid__submodule_statement_missing_parens"]["source"]
        self.assertIn("submodule statement_control_m statement_control_sm", invalid_statement)
        self.assertNotIn("submodule (statement_control_m) statement_control_sm", invalid_statement)
        self.assertIn("100 format(I0)\ncontains", self.specs[
            "C1411_invalid__submodule_format_in_specification_part"]["source"])
        self.assertIn("end submodule other", self.specs["C1413_invalid__submodule_end_name_mismatch"]["source"])

    def test_block_data_sources_observe_named_common_initialization(self):
        values = self.specs["S14_3_001_valid__block_data_initial_values"]["source"]
        for needle in [
            "common /initial_blk/ a, b", "data a /17/", "data b /23/",
            "if (a /= 17)", "if (b /= 23)",
        ]:
            self.assertIn(needle, values)
        self.assertIn("block data\n", self.specs[
            "C1414_invalid__block_data_end_name_without_start_name"]["source"])
        self.assertIn("end block data other", self.specs[
            "C1414_invalid__block_data_end_name_mismatch"]["source"])
        self.assertIn("integer, allocatable :: a", self.specs[
            "C1416_invalid__block_data_allocatable_type_decl"]["source"])
        self.assertIn("external :: f", self.specs[
            "C1415_invalid__block_data_external_statement"]["source"])

    def test_runtime_mutation_matrix_is_feature_based_and_complete(self):
        runtime = [spec for spec in self.specs.values()
                   if spec["kind"] == "valid" and not spec.get("compile_only")]
        self.assertEqual(len(runtime), 9)
        total = 0
        for spec in runtime:
            self.assertTrue(spec["mutations"])
            for label, old, new in spec["mutations"]:
                self.assertNotEqual(old, new, label)
                self.assertEqual(spec["source"].count(old), 1, label)
                mutant = spec["source"].replace(old, new)
                self.assertNotEqual(generated.sha(mutant.encode("ascii")), spec["source_sha256"])
                self.assertIn("error stop", mutant.lower())
                self.assertIn("print '(a)'", mutant)
                total += 1
        self.assertEqual(total, 16)

    def test_catalogues_remove_only_generated_facets_and_keep_pending_remainders(self):
        sub = self.registry.catalogues[generated.SECTION_SUBMODULE]
        block = self.registry.catalogues[generated.SECTION_BLOCK_DATA]
        for rule, facets in generated.SUBMODULE_FACETS.items():
            owner = next(row for row in sub["requirements"] if row["id"] == rule)
            for facet in facets:
                self.assertNotIn(facet, owner.get("pending", {}))
            self.assertIn(generated.SUBMODULE_ORACLE_PREFIX, owner["oracle"])
            self.assertIn(generated.SUBMODULE_LIMIT_PREFIX, owner["oracle_limitation"])
        self.assertIn("entry-stmt-forbidden-in-submodule-spec",
                      next(row for row in sub["requirements"] if row["id"] == "C1411")["pending"])
        self.assertIn("parent-submodule-is-descendant",
                      next(row for row in sub["requirements"] if row["id"] == "C1412")["pending"])
        for rule, facets in generated.BLOCK_DATA_FACETS.items():
            owner = next(row for row in block["requirements"] if row["id"] == rule)
            for facet in facets:
                self.assertNotIn(facet, owner.get("pending", {}))
            self.assertIn(generated.BLOCK_DATA_ORACLE_PREFIX, owner["oracle"])
            self.assertIn(generated.BLOCK_DATA_LIMIT_PREFIX, owner["oracle_limitation"])
        self.assertIn("listed-block-data-specification-statements",
                      next(row for row in block["requirements"] if row["id"] == "C1415")["pending"])
        self.assertIn("bind-attribute-forbidden-in-block-data-type-decl",
                      next(row for row in block["requirements"] if row["id"] == "C1416")["pending"])
        self.assertIn("named-common-block-single-block-data-owner",
                      next(row for row in block["requirements"] if row["id"] == "S14.3-005")["pending"])
        self.assertIn("single-unnamed-block-data-program-unit",
                      next(row for row in block["requirements"] if row["id"] == "S14.3-006")["pending"])
        self.assertIn("bare-end-submodule-form",
                      next(row for row in sub["requirements"] if row["id"] == "R1419")["pending"])
        self.assertIn("bare-end-block-data-form",
                      next(row for row in block["requirements"] if row["id"] == "R1422")["pending"])

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
