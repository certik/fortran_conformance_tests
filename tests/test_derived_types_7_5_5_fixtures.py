"""Additional 7.5.5 type-bound procedure fixture packet checks."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_derived_types_7_5_5_fixtures as generated
import generate_type_bound_fixtures as type_bound


class DerivedTypes755FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def test_exact_owned_runtime_cases_and_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 3)
        self.assertEqual(len(self.files), 6)
        covered = {}
        for name, case in self.cases.items():
            with self.subTest(case=name):
                covered.setdefault(case.rule, set()).update(case.meta.facets)
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.outcome, "success")
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.meta.evidence, "effect")
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
                self.assertEqual(case.fixture.files, ["source.f90"])
                self.assertEqual(len(case.fixture.build), 1)
                self.assertEqual(case.fixture.link["objects"], ["source.o"])
                validate_case_requirement(case, self.registry.requirements[case.rule],
                                          case.rule in self.registry.numbered)
        self.assertEqual(covered, {rule: set(facets) for rule, facets in generated.SELECTED.items()})

    def test_generated_bytes_and_sources_are_bounded(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/derived_types_755_"))
                if path.suffix == ".f90":
                    text = raw.decode("ascii")
                    self.assertTrue(text.endswith("\n"))
                    self.assertLessEqual(max(map(len, text.splitlines())), 132)

    def test_catalogue_sync_removes_only_selected_pending_facets(self):
        synced = generated.synced_catalogue(self.catalogue)
        self.assertEqual(synced, self.catalogue)
        by_rule = {row["id"]: row for row in self.catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            row = by_rule[rule]
            with self.subTest(rule=rule):
                for facet in facets:
                    self.assertNotIn(facet, row["pending"])
                self.assertIn(generated.ORACLE_PREFIX + rule + ": ", row["oracle"])
                self.assertIn(generated.LIMIT_PREFIX + rule + ": ", row["oracle_limitation"])
        self.assertEqual(sum(len(row["pending"]) for row in self.catalogue["requirements"]), 58)
        view = (ROOT / "doc/fortran_2023_7_5_5.md").read_text()
        self.assertIn("**3 are directly represented by the `derived_types_755_` companion packet**", view)
        self.assertIn("**58 remain PENDING**", view)

    def test_no_overlap_with_existing_type_bound_packet(self):
        _, existing, _ = type_bound.build_corpus(ROOT)
        existing_facets = {}
        for spec in existing.values():
            existing_facets.setdefault(spec["rule"], set()).update(spec["facets"])
        for rule, facets in generated.SELECTED.items():
            self.assertTrue(set(facets).isdisjoint(existing_facets.get(rule, set())), rule)
        self.assertFalse(set(self.cases) & set(existing))

    def test_mutation_matrix_is_feature_bound_and_nonempty(self):
        total = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["mutations"]), 1, spec["id"])
            for mutation in spec["mutations"]:
                with self.subTest(case=spec["id"], mutation=mutation["id"]):
                    total += 1
                    mutated = generated.apply_mutation(spec, mutation).encode("ascii")
                    self.assertNotEqual(mutated, raw)
                    for replacement in mutation["replacements"]:
                        start, end = replacement["span"]
                        self.assertEqual(raw[start:end].decode("ascii"), replacement["expected"])
                        self.assertNotEqual(replacement["expected"], replacement["replacement"])
                    self.assertTrue(mutation["derivation"].strip())
        self.assertEqual(total, 4)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
