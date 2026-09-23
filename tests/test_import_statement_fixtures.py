"""Fixture packet tests for Fortran 2023 8.8 IMPORT statements."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement

import generate_import_statement_fixtures as generated


class ImportStatementFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_cases_and_twenty_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 15)
        self.assertEqual(len(self.files), 30)
        self.assertEqual(sum(len(v) for v in generated.SELECTED.values()), 20)
        covered = {}
        for case in self.cases.values():
            covered.setdefault(case.rule, set()).update(case.meta.facets)
            validate_case_requirement(case, self.registry.requirements[case.rule])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
        self.assertEqual(covered, {rule: set(facets) for rule, facets in generated.SELECTED.items()})

    def test_runtime_fixtures_have_run_oracles_and_controls_have_positive_role(self):
        for name, spec in self.specs.items():
            case = self.cases[name]
            if spec["phase"] == "run":
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("run", "success"))
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                expected_cohort = "positive-control" if spec["evidence"] == "positive-control" else "runtime-effect"
                self.assertEqual(self.members[name]["cohort"], expected_cohort)
            else:
                self.assertEqual(case.kind, "invalid")
                self.assertEqual(case.fixture.link, None)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "diagnose"))
                self.assertEqual(self.members[name]["cohort"], "diagnostic-only")

    def test_c8100_negatives_are_one_import_deletion_from_running_controls(self):
        for key in ("main", "external", "module", "block_data"):
            invalid = self.specs[generated.ident(key + "_invalid")]
            control = self.specs[generated.ident(key + "_control")]
            self.assertEqual(invalid["repair"]["control_id"], control["id"])
            self.assertEqual(invalid["repair"]["control_sha256"], generated.sha(control["source"].encode("ascii")))
            self.assertEqual(invalid["source"].replace("  import\n", "", 1), control["source"])
            diagnostic = self.cases[invalid["id"]].fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                             ("source.f90", 2, 2))
            self.assertEqual(diagnostic["contains_any"], generated.C8100_CAUSES[key])
            self.assertEqual(diagnostic["excludes_any"], list(generated.EXCLUSIONS))

    def test_sources_are_ascii_runtime_observations_with_no_default_equivalent_oracles(self):
        required = {
            "import_statement_forms": [
                "import host_a", "import :: host_b, host_c", "import, only: host_a",
                "import, none", "import, all", "if (observed /= 12)", "if (host_c /= 6)",
            ],
            "import_statement_only": ["import, only: hx", "import, only: hy", "integer :: hz", "hz /= 100"],
            "import_statement_none": ["import, none", "integer :: hz", "hz /= 100"],
            "import_statement_all": ["import, all", "hz /= 7"],
            "import_statement_bare": ["    import\n", "hz /= 6"],
            "import_statement_interface": [
                "import :: box, rk, slot_count", "slot_count_alt = 1",
                "type(box), intent(in) :: item(slot_count)", "observed /= 42_rk",
            ],
        }
        for name, needles in required.items():
            source = self.specs[name]["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertIn("write(*,'(a)')", source)
            for needle in needles:
                self.assertIn(needle, source)
            self.assertNotRegex(source, r"(?i)\b(error stop 0|observed\s*=\s*0|hz\s*=\s*0)\b")

    def test_mutation_definitions_bind_parent_source_and_include_compensated_features(self):
        total = sum(len(generated.all_mutations(spec)) for spec in self.specs.values())
        self.assertEqual(total, 17)
        conforming_features = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            for mutation in generated.all_mutations(spec):
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                text = spec["source"]
                for expected, replacement in mutation["replacements"]:
                    self.assertEqual(text.count(expected), 1)
                    text = text.replace(expected, replacement)
                self.assertEqual(text.encode("ascii"), mutant)
                if mutation in spec.get("feature_mutations", []):
                    if mutation.get("conforming"):
                        conforming_features += 1
                    else:
                        self.fail(f"runtime feature mutation must be conforming: {spec['id']} {mutation['id']}")
        self.assertEqual(conforming_features, 7)

    def test_catalogue_sync_removes_only_selected_pending_facets_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Fifteen fixtures cover twenty selected facets", view)
        for row in synced["requirements"]:
            self.assertIn(render_requirement(row), view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)


if __name__ == "__main__":
    unittest.main()
