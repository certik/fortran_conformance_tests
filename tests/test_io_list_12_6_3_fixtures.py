"""Runtime and diagnostic fixtures for Fortran 2023 12.6.3 I/O lists."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_io_list_12_6_3_fixtures as generated


class IoList1263FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_generated_fixture_set_and_manifest_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), len(self.specs))
        self.assertEqual(len(self.files), 2 * len(self.specs))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        runtime = [s for s in self.specs.values() if s["kind"] == "valid" and s.get("completion")]
        invalid = [s for s in self.specs.values() if s["kind"] == "invalid"]
        controls = [s for s in self.specs.values() if s["kind"] == "valid" and not s.get("completion")]
        self.assertEqual((len(invalid), len(controls)), (3, 3))
        self.assertGreaterEqual(len(runtime), 20)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual((case.rule, case.meta.standard, case.meta.oracle_basis),
                             (spec["rule"], "f2023", "standard"))
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.build[0].source, "source.f90")
            self.assertEqual(case.fixture.build[0].form, "free")
            validate_case_requirement(case, self.registry.requirements[case.rule])
            if spec["kind"] == "invalid":
                self.assertEqual(case.kind, "invalid")
                self.assertEqual(case.meta.evidence, "effect")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(self.members[name]["cohort"], "diagnostic-only")
                self.assertIn("excludes_any", case.fixture.expectation.diagnostic)
            elif spec.get("completion"):
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.link["driver"], "fortran")
                self.assertIn(self.members[name]["cohort"], {"runtime-effect", "positive-control"})
            else:
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.meta.evidence, "positive-control")
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.fixture.expectation.outcome, "success")
                self.assertIsNone(case.fixture.link)

    def test_sources_contain_required_io_list_observations_and_hygiene(self):
        anchors = {
            "basic_input_output": ["if (x /= -777)", "read(rec,*) x", "write(out,'(SS,I2)') x + 5"],
            "input_implied_do": ["read(rec,*) (a(i), i = 1, 3)", "if (any(a /= [1, 2, 3]))"],
            "implied_do_increment": ["j = lo + 1, hi, stride", "if (any(a /= [-1, 8, -3, 9, -5]))"],
            "output_implied_do": ["write(out,'(SS,3I2)') (a(i) + 1, i = 1, 3)", "if (out /= ' 3 5 7')"],
            "pointer_io": ["p => target", "read(rec,*) p", "write(out,'(SS,I2)') p"],
            "allocatable_io": ["allocate(x)", "if (.not. allocated(x))", "read(rec,*) x"],
            "read_n_then_slice": ["read(rec,*) n, a(1:n)", "if (n /= 3)"],
            "array_element_order_input": ["read(rec,*) a", "reshape(a, [4]) /= [1, 2, 3, 4]"],
            "derived_formatted_components": ["read(rec,'(I1,1X,A2)') item", "write(out,'(SS,I2,A2)') item"],
            "derived_array_reapplied": ["write(out,'(SS,3I1)') item"],
            "zero_effective_items": ["allocate(empty(0))", "i = 1, 0", "z(:0)"],
            "ordinary_procedure_pointer_result_control": ["procedure(f), pointer :: p", "write(out,'(SS,I2)') p()"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec.get("completion"):
                self.assertIn("implicit none", source)
                self.assertIn("checks =", source)
                self.assertIn(spec["completion"].strip(), source)
                self.assertNotRegex(source.lower(), r"\b(open|close|unit\s*=|newunit\s*=|scratch|coarray|sync\s+all)\b")
                if "read(" in source:
                    self.assertRegex(source, r"pre-read sentinel")
                for needle in anchors.get(spec["variant"], []):
                    self.assertIn(needle, source)
            if "character" in source and spec.get("completion"):
                self.assertNotIn("==", source)
        self.assertIn("read(rec,*) 1", self.specs[generated.identifier("R1216", "input_nonvariable", "invalid")]["source"])
        self.assertIn("read(rec,*) a", self.specs[generated.identifier("C1233", "assumed_size_input", "invalid")]["source"])
        self.assertIn("a(i) + 1", self.specs[generated.identifier("C1234", "input_implied_do_expression", "invalid")]["source"])

    def test_mutation_spans_bind_features_sentinels_and_oracles(self):
        runtime = [s for s in self.specs.values() if s["kind"] == "valid" and s.get("completion")]
        self.assertEqual(sum(len(generated.all_runtime_mutations(s)) for s in runtime), 119)
        self.assertEqual(sum(len(s["feature_mutations"]) for s in runtime), 55)
        self.assertEqual(sum(len(s["sentinel_mutations"]) for s in runtime), 33)
        self.assertEqual(sum(len(s["oracle_mutations"]) for s in runtime), 31)
        categories = {m["category"] for s in runtime for m in generated.all_runtime_mutations(s)}
        for required in {"input-sentinel", "array-element-order", "zero-sized-array",
                         "zero-count-implied-do", "zero-length-character", "derived-output-expansion"}:
            self.assertIn(required, categories)
        for spec in runtime:
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["feature_mutations"]), 2)
            if "read(" in spec["source"]:
                self.assertGreaterEqual(len(spec["sentinel_mutations"]), 3)
            for mutation in generated.all_runtime_mutations(spec):
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
        changed = dict(runtime[0], source=runtime[0]["source"] + "\n")
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            generated.mutated_source(changed, generated.all_runtime_mutations(runtime[0])[0])

    def test_catalogue_sync_removes_only_selected_pending_facets_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        for rule, facets in generated.SELECTED.items():
            owner = self.registry.requirements[rule]
            self.assertTrue(facets <= set(owner["facets"]))
            for facet in facets:
                self.assertNotIn(facet, owner.get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIX, owner["oracle"])
            self.assertIn(generated.LIMIT_PREFIX, owner["oracle_limitation"])
        self.assertIn("procedure-pointer-output-expression-rejected",
                      self.registry.requirements["C1235"].get("pending", {}))
        self.assertIn("formatted-derived-components-accessible",
                      self.registry.requirements["S12.6.3-017"].get("pending", {}))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("reads n before", view)
        self.assertIn("Every runtime input target", view)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
