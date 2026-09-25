"""Procedure-reference fixtures for Fortran 2023 15.5.1."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_procedure_reference_15_5_1_fixtures as generated


class ProcedureReference1551FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_cases_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 30)
        self.assertEqual(len([s for s in self.specs.values() if s["kind"] == "invalid"]), 10)
        self.assertEqual(len([s for s in self.specs.values() if s.get("evidence") == "positive-control"]), 10)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(len(covered), 29)
        for case in self.cases.values():
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            validate_case_requirement(case, self.registry.requirements[case.rule], case.rule[0] in "RC")

    def test_runtime_cases_have_feature_mutations_and_exact_stdout(self):
        runtime = [spec for spec in self.specs.values() if spec["id"] in {case["id"] for case in generated.RUNTIME_CASES}]
        self.assertEqual(len(runtime), 10)
        for spec in runtime:
            case = self.cases[spec["id"]]
            self.assertEqual((case.kind, case.meta.evidence), ("valid", "effect"))
            self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            self.assertGreaterEqual(len(spec["mutations"]), len(spec["facets"]))
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            mutated = set()
            for mutation in spec["mutations"]:
                self.assertIn(mutation["facet"], spec["facets"])
                self.assertEqual(raw.count(mutation["expected"].encode("ascii")), 1)
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                mutated.add(generated.sha(mutant))
            self.assertEqual(len(mutated), len(spec["mutations"]))
            self.assertIn("checks = checks + 1", spec["source"])
            self.assertNotIn("real ::", spec["source"].lower())

    def test_diagnostic_cases_are_line_anchored_with_run_controls(self):
        invalids = [spec for spec in self.specs.values() if spec["kind"] == "invalid"]
        controls = {spec.get("controls"): spec for spec in self.specs.values() if spec.get("controls")}
        self.assertEqual(set(controls), {spec["id"] for spec in invalids})
        for spec in invalids:
            case = self.cases[spec["id"]]
            self.assertEqual((case.kind, case.meta.evidence), ("invalid", "effect"))
            diag = case.fixture.expectation.diagnostic
            self.assertEqual((diag["file"], diag["line"], diag["end_line"]), ("source.f90", spec["line"], spec["line"]))
            self.assertIn("excludes_any", diag)
            self.assertNotIn("contains_any", diag)
            self.assertNotIn("equals_any", diag)
            self.assertTrue(any("Internal Compiler Error" in item for item in diag["excludes_any"]))
            control = self.cases[controls[spec["id"]]["id"]]
            self.assertEqual((control.kind, control.meta.evidence), ("valid", "positive-control"))
            self.assertEqual(control.fixture.expectation.phase, "run")
            self.assertEqual(control.fixture.expectation.stdout, [controls[spec["id"]]["stdout"]])

    def test_catalogue_sync_removes_only_owned_pending_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_id = {row["id"]: row for row in catalogue["requirements"]}
        for spec in self.specs.values():
            for facet in spec["facets"]:
                self.assertNotIn(facet, by_id[spec["rule"]].get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIX, by_id[spec["rule"]]["oracle"])
                self.assertIn(generated.LIMIT_PREFIX, by_id[spec["rule"]]["oracle_limitation"])
        for facet in ("no-polymorphic-subobject-of-coindexed-object",
                      "call-designator-is-subroutine",
                      "procedure-name-generic-or-procedure",
                      "actual-arg-conditional",
                      "conditional-consequents-same-rank"):
            owners = [row for row in catalogue["requirements"] if facet in row["facets"]]
            self.assertEqual(len(owners), 1)
            self.assertIn(facet, owners[0].get("pending", {}))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("diagnostic negatives", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
