"""Runtime and diagnostic fixtures for Fortran 2023 USE association in 14.2.2."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry
import generate_use_association_14_2_2_fixtures as generated


class UseAssociation1422FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.valid_specs = generated.source_specs()
        cls.diag_specs = generated.diagnostic_specs()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        expected = {generated.identifier(v) for v in generated.CASES} | {
            generated.diagnostic_identifier(v) for v in generated.DIAGNOSTIC_CASES}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 2 * (len(generated.CASES) + len(generated.DIAGNOSTIC_CASES)))
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            if case.name in self.diag_specs:
                self.assertEqual((case.kind, case.meta.evidence), ("invalid", "effect"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("compile", "diagnose"))
                self.assertEqual(case.fixture.expectation.diagnostic["line"], spec["line"])
                self.assertIn("not implemented", case.fixture.expectation.diagnostic["excludes_any"])
            elif case.rule.startswith(("R", "C")) or case.rule in {"S14.2.2-001", "S14.2.2-009", "S14.2.2-010"}:
                self.assertEqual((case.kind, case.meta.evidence), ("valid", "positive-control"))
            else:
                self.assertEqual((case.kind, case.meta.evidence), ("valid", "effect"))
            if case.name in self.valid_specs:
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])

    def test_sources_are_ascii_self_checking_and_scoped(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("implicit none\n", source)
        for spec in self.valid_specs.values():
            self.assertIn("write(*,'(a)')", spec["source"])
            self.assertIn(spec["completion"].rstrip("\n"), spec["source"])
        for spec in self.diag_specs.values():
            self.assertNotIn("write(*,'(a)')", spec["source"])

    def test_mutation_replacements_bind_complete_parent_sources(self):
        self.assertGreaterEqual(sum(len(s["mutations"]) for s in self.valid_specs.values()),
                                sum(len(f) for f in generated.FACETS_BY_RULE.values()))
        for spec in self.valid_specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            seen = set()
            self.assertGreaterEqual(len(spec["mutations"]), 1)
            for mutation in spec["mutations"]:
                self.assertEqual(mutation["kind"], "feature")
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), seen)
                seen.add(generated.sha(mutant))
                for old, _ in mutation["replacements"]:
                    self.assertIn(old.encode("ascii"), raw)

    def test_catalogue_sync_removes_only_claimed_pending_facets(self):
        catalogue = self.registry.catalogues["14.2.2"]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.ALL_COVERED_FACETS_BY_RULE.items():
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)

    def test_facet_assertion_mutation_table_is_complete(self):
        expected = {facet for facets in generated.ALL_COVERED_FACETS_BY_RULE.values() for facet in facets}
        self.assertEqual(set(generated.FACET_ASSERTION_MUTATION_TABLE), expected)
        for facet, row in generated.FACET_ASSERTION_MUTATION_TABLE.items():
            self.assertIn(row["case"], self.specs)
            self.assertTrue(row["assertion"])
            self.assertTrue(row["feature_mutant"])

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
