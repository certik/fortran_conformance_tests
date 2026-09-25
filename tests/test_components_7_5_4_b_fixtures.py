"""Runtime fixture metadata for component declarations and defaults in 7.5.4."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry

sys.path.insert(0, str(ROOT / "tools"))
import generate_components_7_5_4_b_fixtures as generated


class Components754BFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_runtime_fixture_set(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 14)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 19)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 19)
        for name, case in self.cases.items():
            with self.subTest(case=name):
                spec = self.specs[name]
                self.assertEqual(case.rule, spec["rule"])
                self.assertEqual(case.meta.facets, spec["facets"])
                self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
                self.assertFalse(case.meta.coarray)
                self.assertEqual(case.meta.images, 1)
                self.assertEqual(case.meta.profiles, [])
                self.assertEqual(case.fixture.files, ["source.f90"])
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.outcome, "success")
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])

    def test_generated_bytes_match_and_sources_are_bounded(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith(
                    ("tests/fixtures/components_7_5_4_b_",)))
                raw.decode("ascii")
                if path.suffix == ".f90":
                    self.assertLessEqual(max(map(len, raw.splitlines()), default=0), 132)
                    lowered = raw.decode("ascii").lower()
                    self.assertNotIn("codimension", lowered)
                    self.assertNotIn("transfer(", lowered)
                    self.assertNotIn("c_loc", lowered)

    def test_mutation_spans_are_feature_level_and_bound_to_parent(self):
        seen_facets = []
        for spec in self.specs.values():
            raw = spec["source"]
            self.assertEqual(generated.sha(raw.encode("ascii")), spec["source_sha256"])
            for mutation in spec["mutations"]:
                with self.subTest(case=spec["id"], mutation=mutation["id"]):
                    self.assertIn(mutation["facet"], spec["facets"])
                    self.assertEqual(raw.count(mutation["expected"]), 1)
                    mutant = generated.mutated_source(spec, mutation)
                    self.assertNotEqual(mutant, raw)
                    self.assertIn(mutation["replacement"], mutant)
                    self.assertNotIn("delete the final PASS", mutation["assertion"])
                    self.assertNotEqual(mutation["expected"], mutation["replacement"])
                    seen_facets.append((spec["rule"], mutation["facet"]))
        self.assertEqual(set(seen_facets), {
            (spec["rule"], facet) for spec in self.specs.values() for facet in spec["facets"]
        })
        c769 = self.specs["C769_valid__components_7_5_4_b_target_compatibility_constraint"]
        self.assertEqual(c769["mutations"][0]["expected"], "alias => target")
        self.assertEqual(c769["mutations"][0]["replacement"], "alias => other")
        self.assertNotIn("target = 31", c769["mutations"][0]["expected"])
        self.assertEqual(generated.CONFIRMED_LFORTRAN_DEFECT_VARIANTS, {
            "initialization_alternatives", "initial_target_designator",
            "nested_initial_target", "target_compatibility_constraint",
        })
        self.assertEqual(generated.CONFIRMED_LFORTRAN_DEFECT_MUTATIONS, {
            "type_object_classification-pointer-and-allocatable-recursion-boundary",
        })

    def test_catalogue_sync_and_pending_partition(self):
        covered = {}
        for case in self.all_cases:
            covered.setdefault(case.rule, set()).update(case.meta.facets)
        linked = self.registry.evidence.validate_cases(self.all_cases)
        for section, relative in generated.CATALOGUES.items():
            with self.subTest(section=section):
                catalogue = self.registry.catalogues[section]
                self.assertEqual(generated.synced_catalogue(section, catalogue), catalogue)
                self.assertIn(generated.SUMMARY_BEGIN, (ROOT / generated.VIEWS[section]).read_text())
                for requirement in catalogue["requirements"]:
                    rule = requirement["id"]
                    self.assertEqual(set(requirement["pending"]),
                                     set(requirement["facets"]) - covered.get(rule, set())
                                     - set(linked.get(rule, {})))
                for rule, facets in generated.FACETS_BY_RULE.items():
                    owner = next((row for row in catalogue["requirements"] if row["id"] == rule), None)
                    if owner is not None:
                        for facet in facets:
                            self.assertNotIn(facet, owner.get("pending", {}))
                        self.assertIn(generated.ORACLE_PREFIX[section], owner["oracle"])
                        self.assertIn(generated.LIMIT_PREFIX[section], owner["oracle_limitation"])

    def test_check_mode_is_read_only(self):
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
