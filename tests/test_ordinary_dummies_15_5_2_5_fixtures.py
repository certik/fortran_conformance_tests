"""Generated fixture tests for Fortran 2023 ordinary dummy variables 15.5.2.5."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_ordinary_dummies_15_5_2_5_fixtures as generated


class OrdinaryDummies15525FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_owned_cases_and_requirement_roles(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 28)
        unique_facets = {(spec["rule"], facet) for spec in self.specs.values() for facet in spec["facets"]}
        self.assertEqual(len(unique_facets), 22)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 16)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            validate_case_requirement(case, self.registry.requirements[case.rule], numbered=case.rule.startswith("C"))
            if case.kind == "valid":
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertIn(case.meta.evidence, {"effect", "positive-control"})
                if not case.rule.startswith("C"):
                    self.assertGreaterEqual(len(spec["mutations"]), 1)
            else:
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("compile", "diagnose"))
                self.assertIn("call bad(", spec["source"].splitlines()[case.fixture.expectation.diagnostic["line"] - 1])
            with self.assertRaises(SuiteError):
                bad = case.__class__(case.name, case.rule, case.kind, case.path,
                                     case.meta.__class__(case.meta.facets + ["foreign"], case.meta.evidence),
                                     case.review_key, case.fixture)
                validate_case_requirement(bad, self.registry.requirements[case.rule], numbered=case.rule.startswith("C"))

    def test_sources_are_self_checking_and_bounded(self):
        required = {
            "ordinary_scope": ["call observe_scope(31, out)", "call expect_equal(out, 31"],
            "scalar_character_leftmost": ["character(len=3), intent(inout) :: x", "call expect_char5(char_actual, 'XYZDE'"],
            "array_character_leftmost": ["character(len=1), intent(inout) :: x(4)", "call expect_char4(seq_seen, 'ABCD'"],
            "target_return": ["module_q => x", "associated(module_q, target_value)"],
            "assumed_rank_scalar_exception": ["select rank (x)", "call assumed_rank_observe(53"],
            "assumed_rank_lower": ["integer :: actual(-2:-1,4:6)", "call expect_vector2(lower_seen, [1,1]"],
            "intent_out_default_component": ["integer :: keep = 17", "intent(out) :: x"],
            "c1548_async_invalid": ["call bad(a(3:1:-2))", "integer, asynchronous :: x(2)"],
            "c1549_async_invalid": ["integer, pointer, asynchronous :: p(:)", "call bad(p)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertNotIn("/tmp", source.lower())
            body_lines = [line for line in source.splitlines() if not line.startswith("! covers: ")]
            self.assertLessEqual(max(map(len, body_lines)), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            if spec["kind"] == "valid":
                self.assertIn("write(*,'(a)') '" + spec["completion"].strip() + "'", source)
                self.assertRegex(source, r"call expect_equal\(checks, \d+, 'check count'\)") if "checks" in source else None
            for needle in required.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_mutations_are_feature_specific_and_bound(self):
        seen = {}
        for spec in self.specs.values():
            self.assertEqual(generated.sha(spec["source"].encode("ascii")), spec["source_sha256"])
            digests = {spec["source_sha256"]}
            for mutation in spec["mutations"]:
                self.assertEqual(mutation["kind"], "feature")
                self.assertIn(mutation["facet"], spec["facets"])
                seen[(spec["rule"], mutation["facet"])] = seen.get((spec["rule"], mutation["facet"]), 0) + 1
                mutant = generated.mutate_source(spec, mutation)
                self.assertNotEqual(mutant, spec["source"])
                digest = generated.sha(mutant.encode("ascii"))
                self.assertEqual(digest, mutation["mutant_sha256"])
                self.assertNotIn(digest, digests)
                digests.add(digest)
                for repl in mutation["replacements"]:
                    self.assertEqual(spec["source"].count(repl["expected"]), 1)
                    self.assertNotEqual(repl["expected"], repl["replacement"])
        self.assertEqual(len(seen), 16)
        self.assertTrue(all(count == 1 for count in seen.values()))

    def test_catalogues_and_views_are_synced(self):
        for section, rel in generated.CATALOGUES.items():
            catalogue = json.loads((ROOT / rel).read_text())
            expected = generated.synced_catalogue(section, catalogue, self.specs)
            self.assertEqual(expected, catalogue)
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for spec in self.specs.values():
                row = by_rule[spec["rule"]]
                for facet in spec["facets"]:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[spec["rule"]], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[spec["rule"]], row["oracle_limitation"])
            view = generated.rendered_view(section, catalogue, ROOT)
            self.assertEqual((ROOT / generated.VIEWS[section]).read_text(), view)
        self.registry.render(write=False)

    def test_generation_check_is_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
