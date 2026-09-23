"""Runtime fixture metadata for Fortran 2023 deallocation effects."""

import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_deallocation_fixtures as generated


class DeallocationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_eleven_owned_f2023_fixtures_are_collected(self):
        self.assertEqual(set(self.cases), {generated.identifier(name) for name in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 22)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, {facet for meta in generated.VARIANTS.values() for facet in meta["facets"]})
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.coarray or case.meta.profiles or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language,
                              case.fixture.build[0].form), ("source.f90", "fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["completion"]])
            self.assertEqual(expect.stderr, [""])

    def test_sources_keep_reviewed_before_after_pairings_and_forbidden_oracles_out(self):
        required = {
            "dealloc_allocated_control": ["x(-9:-7)", "deallocate(x, stat=stat)", "allocated(x)"],
            "dealloc_unallocated_error": ["x(-3:-1)", "deallocate(x, stat=stat)", "stat <= 0"],
            "dealloc_function_result_retains": ["allocate(r(-5:-3))", "got = make_result()"],
            "dealloc_procedure_local_auto": ["integer, allocatable :: scratch(:)", "call visit(1)",
                                             "call visit(2)"],
            "dealloc_saved_local_control": ["integer, allocatable, save :: retained(:)",
                                            "deallocate(retained, stat=stat)"],
            "dealloc_block_local_auto": ["block", "integer, allocatable :: local(:)", "end block"],
            "dealloc_intent_out_actual": ["intent(out) :: x(:)", "allocated(x)",
                                          "allocate(x(8:10), stat=stat)"],
            "dealloc_intent_out_subobject": ["type(holder), intent(out) :: h", "allocated(h%part)",
                                             "allocate(h%part(3:5), stat=stat)"],
            "dealloc_intrinsic_assignment_subobject": ["lhs = rhs", "allocated(lhs%part)",
                                                       "allocated(rhs%part)"],
            "dealloc_derived_subobject": ["type(owner), allocatable :: item",
                                          "deallocate(item, stat=stat)", "expect_log([3, 367, 373, 379])"],
            "dealloc_automatic_same_effect": ["deallocate(explicit)", "call automatic_visit(1)",
                                              "call automatic_visit(2)"],
        }
        nonzero_payloads = ("37", "67", "97", "107", "139", "157", "191", "229", "271", "293", "367")
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertIn("! rule: ", source)
            self.assertIn("! covers: ", source)
            self.assertRegex(source, r"(?i)\ballocated\s*\(")
            self.assertRegex(source, r"(?i)\blbound\s*\(|\bubound\s*\(")
            self.assertNotRegex(source, r"(?i)\b(associated|transfer|loc|c_loc)\s*\(")
            self.assertNotRegex(source, r"(?i)errmsg\s*=")
            self.assertTrue(any(payload in source for payload in nonzero_payloads))
            for needle in required[spec["variant"]]:
                self.assertIn(needle, source)

    def test_mutation_metadata_binds_parent_and_includes_required_feature_mutations(self):
        counts = generated.mutation_counts(self.specs)
        self.assertEqual(counts, dict(cases=11, facets=11, failing_mutations=45,
                                      feature_mutations=12, reverse_controls=11))
        feature_ids = {
            mutation["id"]
            for spec in self.specs.values()
            for mutation in spec["feature_mutations"]
        }
        self.assertIn("remove-explicit-deallocate", feature_ids)
        self.assertIn("make-automatic-local-saved", feature_ids)
        self.assertIn("remove-intrinsic-assignment", feature_ids)
        self.assertIn("intent-out-to-inout", feature_ids)
        self.assertIn("remove-save-attribute", feature_ids)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            for mutation in generated.failing_mutations(spec):
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
            for mutation in spec["reverse_mutations"]:
                mutant = generated.mutated_source(spec, mutation).decode("ascii")
                for replacement in mutation["replacements"]:
                    self.assertIn(replacement["replacement"], mutant)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["feature_mutations"][0])

    def test_catalogue_counts_and_pending_facets_match_bound_fixtures(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for spec in self.specs.values():
            pending = by_rule[spec["rule"]].get("pending", {})
            for facet in spec["facets"]:
                self.assertNotIn(facet, pending)
        report = self.registry.audit(self.all_cases)
        # Assert this packet's own contribution, never suite-wide totals.
        # Global counts drift whenever any other packet integrates: a sibling
        # fixture packet moves authored_facets and the case count, and a SOURCE
        # packet moves declared_facets. None of them encode anything about
        # deallocation. Scope every assertion to this section instead.
        self.assertEqual(len(self.specs), 11)
        bound = {facet for spec in self.specs.values() for facet in spec["facets"]}
        self.assertEqual(len(bound), 11)
        section_facets = sum(len(row["facets"]) for row in catalogue["requirements"])
        section_pending = sum(len(row.get("pending", {})) for row in catalogue["requirements"])
        self.assertEqual(section_facets - section_pending, 11)
        self.assertIn("declared_facets", report)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        specs = generated.generate(ROOT, check=True)
        self.assertEqual(set(specs), set(self.specs))
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        self.assertEqual(
            generated.summary_line(True, specs),
            "Checked 11 deallocation cases, 11 facets, 45 failing mutations "
            "(12 feature-level) and 11 reverse controls.")


if __name__ == "__main__":
    unittest.main()
