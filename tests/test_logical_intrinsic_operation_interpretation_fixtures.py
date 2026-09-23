"""Runtime fixtures for Fortran 2023 logical intrinsic operation interpretation."""

import json
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_logical_intrinsic_operation_interpretation_fixtures as generated


class LogicalIntrinsicOperationInterpretationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_six_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 12)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual(sum(len(case.meta.facets) for case in self.cases.values()), 21)
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.rule, tuple(case.meta.facets)),
                             (spec["rule"], tuple(generated.VARIANTS[spec["variant"]][1])))
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
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
                        replace(case, meta=replace(case.meta, facets=case.meta.facets + ["foreign"])),
                        replace(case, meta=replace(case.meta, facets=case.meta.facets + case.meta.facets[:1]))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_assert_direct_logical_expressions_and_nonzero_sentinel(self):
        anchors = {
            "context_type": [
                "checks=17", "if (.false. .or. .true.) then",
                "call require_false(.true. .eqv. .false., 'LIO:context_type:logical-dummy-eqv')",
                "call require_true(.not. .false., 'LIO:context_type:logical-dummy-not')",
                "logical, intent(in) :: value", "if (checks /= 20)"],
            "not_truth_table": [
                "checks=17", "if (.not. .true.) then", "LIO:not_truth_table:not-true-is-false",
                "if (.not. .false.) then", "LIO:not_truth_table:not-false-is-true", "if (checks /= 19)"],
            "and_truth_table": [
                "if (.true. .and. .true.) then", "if (.true. .and. .false.) then",
                "if (.false. .and. .true.) then", "if (.false. .and. .false.) then", "if (checks /= 21)"],
            "or_truth_table": [
                "if (.true. .or. .true.) then", "if (.true. .or. .false.) then",
                "if (.false. .or. .true.) then", "if (.false. .or. .false.) then", "if (checks /= 21)"],
            "eqv_truth_table": [
                "if (.true. .eqv. .true.) then", "if (.true. .eqv. .false.) then",
                "if (.false. .eqv. .true.) then", "if (.false. .eqv. .false.) then", "if (checks /= 21)"],
            "neqv_truth_table": [
                "if (.true. .neqv. .true.) then", "if (.true. .neqv. .false.) then",
                "if (.false. .neqv. .true.) then", "if (.false. .neqv. .false.) then", "if (checks /= 21)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn("checks=17", source)
            self.assertNotIn("checks=0", source)
            self.assertNotRegex(source, r"(?i)=\s*\.false\.\s*$")
            self.assertNotRegex(source, r"(?i)\b(result_tt|result_tf|result_ft|result_ff|observed)\b")
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|merge|iand|ior|ieor|selected_logical_kind)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|real|complex)\b")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 33)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 21)
        self.assertEqual(sum(len(spec["operator_mutations"]) for spec in self.specs.values()), 12)
        self.assertEqual(sum(len(spec["sentinel_mutations"]) for spec in self.specs.values()), 6)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 33)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["guards"]), len(spec["observations"]) + 2)
            hashes = set()
            for probe in spec["probes"] + spec["sentinel_mutations"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.mutated_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for mutation in spec["input_mutations"]:
                mutant = generated.mutated_source(spec, mutation)
                expected = raw
                for site in sorted(mutation["sites"], key=lambda item: item["span"][0], reverse=True):
                    start, end = site["span"]
                    self.assertEqual(raw[start:end].decode("ascii"), site["expected"])
                    expected = expected[:start] + site["replacement"].encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for mutation in spec["operator_mutations"]:
                self.assertEqual(len(mutation["spans"]), 4)
                mutant = generated.mutated_source(spec, mutation)
                expected = raw
                for start, end in sorted(mutation["spans"], reverse=True):
                    self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                    expected = expected[:start] + mutation["replacement"].encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for mutation in spec["omissions"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                if mutation["id"] == "omit-completion":
                    self.assertNotIn(spec["completion"].strip().encode(), mutant)
                    self.assertEqual((mutation["kind"], mutation["failure_stdout"]), ("output", ""))
                else:
                    self.assertIn(spec["completion"].strip().encode(), mutant)
                    self.assertEqual(mutation["guard_id"], "check-total")
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["probes"][0])

    def test_truth_tables_and_discrimination_rows_are_complete(self):
        expected = {
            ".and.": {"TT": True, "TF": False, "FT": False, "FF": False},
            ".or.": {"TT": True, "TF": True, "FT": True, "FF": False},
            ".eqv.": {"TT": True, "TF": False, "FT": False, "FF": True},
            ".neqv.": {"TT": False, "TF": True, "FT": True, "FF": False},
        }
        by_variant = {spec["variant"]: spec for spec in self.specs.values()}
        self.assertEqual([(g["id"], g["expected_truth"]) for g in by_variant["not_truth_table"]["observations"]],
                         [("not-true-is-false", False), ("not-false-is-true", True)])
        self.assertEqual(generated.BINARY_TRUTH_TABLES, expected)
        self.assertEqual(generated.DISCRIMINATION_ROWS[".and."][".eqv."], "FF")
        self.assertEqual(generated.DISCRIMINATION_ROWS[".or."][".neqv."], "TT")
        for variant, operator in generated.BINARY_VARIANT_OPERATORS.items():
            spec = by_variant[variant]
            self.assertEqual([guard["id"].split("-")[-1].upper() for guard in spec["observations"]],
                             ["TT", "TF", "FT", "FF"])
            self.assertEqual({row: guard["expected_truth"]
                              for row, guard in zip(("TT", "TF", "FT", "FF"), spec["observations"])},
                             expected[operator])
            self.assertEqual({mutation["replacement"] for mutation in spec["operator_mutations"]},
                             set(expected) - {operator})
            for alternative, row in generated.DISCRIMINATION_ROWS[operator].items():
                self.assertNotEqual(expected[operator][row], expected[alternative][row])
                self.assertIn(row, ["TT", "TF", "FT", "FF"])

    def test_catalogue_sync_removes_only_selected_pending_entries_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, remaining in generated.REMAINING_PENDING.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
            for facet in generated.FACETS_BY_RULE[rule]:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Six complete run/effect/f2023 programs cover 21 pending facets", view)
        self.assertIn("Only operand-type-delegation remains pending", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
