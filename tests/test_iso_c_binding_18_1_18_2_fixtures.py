"""ISO_C_BINDING 18.1/18.2 fixture packet structure and non-vacuity metadata."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry

sys.path.insert(0, str(ROOT / "tools"))
import generate_iso_c_binding_18_1_18_2_fixtures as generated


class IsoCBinding18182FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        fixture_paths = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in fixture_paths}

    def test_generator_is_byte_identical_and_collects_owned_cases(self):
        self.assertEqual(len(self.specs), 21)
        self.assertEqual(set(self.cases), {spec["id"] for spec in self.specs.values()})
        self.assertEqual(sum(path.name == "fixture.json" for path in self.files), 21)
        for path, raw in self.files.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_bytes(), raw, path)

    def test_each_manifest_is_valid_runtime_fixture_with_exact_stdout(self):
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            manifest = json.loads((case.fixture.root / "fixture.json").read_text())
            self.assertEqual(manifest, spec["manifest"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertEqual(case.fixture.expectation.stderr, [""])
            self.assertEqual(len(case.fixture.expectation.stdout), 1)
            self.assertTrue(case.fixture.expectation.stdout[0].endswith(" OK\n"))
            if any(name.endswith(".c") for name in spec["files"]):
                self.assertTrue(any(step.language == "c" for step in case.fixture.build))

    def test_owned_facets_are_exactly_direct_authored_and_unclaimed_facets_remain_pending(self):
        owned = {}
        for spec in self.specs.values():
            owned.setdefault(spec["rule"], set()).update(spec["facets"])
        for rule, facets in owned.items():
            req = self.registry.requirements[rule]
            self.assertTrue(facets <= set(req["facets"]))
            self.assertFalse(facets & set(req["pending"]), rule)
            self.assertIn(generated.ORACLE_PREFIX[rule], req["oracle"])
            self.assertIn(generated.LIMIT_PREFIX[rule], req["oracle_limitation"])
        self.assertIn("descriptor-dummy-interoperation", self.registry.requirements["S18.1-005"]["pending"])
        self.assertIn("interoperable-enumerations-correspond-to-c-types", self.registry.requirements["S18.1-004"]["pending"])
        self.assertIn("iso-c-binding-procedures-accessible", self.registry.requirements["S18.2.1-001"]["pending"])
        self.assertIn("optional-integer-kind-minus-one-branch", self.registry.requirements["S18.2.2-004"]["pending"])
        self.assertIn("real-kind-minus-four-other-branch", self.registry.requirements["S18.2.2-006"]["pending"])
        self.assertIn("c-associated-result-default-logical-scalar", self.registry.requirements["S18.2.3.2-004"]["pending"])

    def test_c_long_double_profile_guards_every_long_double_fixture(self):
        profile = ROOT / "tests/profiles/c_long_double_positive.f90"
        text = profile.read_text()
        self.assertIn("use, intrinsic :: iso_c_binding, only: c_long_double", text)
        self.assertIn("if (c_long_double < 0) stop 77", text)
        self.assertNotRegex(text.lower(), r"\breal\s*\(")
        profiled = {spec["variant"] for spec in self.specs.values()
                    if spec["manifest"].get("profiles") == ["c-long-double-positive"]}
        self.assertEqual(profiled, {
            "representation_roundtrip",
            "real_valid_branch",
            "complex_kind_equalities",
        })
        for spec in self.specs.values():
            expected = ["c-long-double-positive"] if spec["variant"] in profiled else []
            self.assertEqual(self.cases[spec["id"]].meta.profiles, expected)

    def test_every_claimed_facet_has_feature_mutation_and_mutations_are_structural(self):
        for spec in self.specs.values():
            claimed = set(spec["facets"])
            mutated = {facet for mutation in spec["mutations"] for facet in mutation["facets"]}
            self.assertEqual(mutated, claimed, spec["id"])
            seen_ids = set()
            for mutation in spec["mutations"]:
                self.assertNotIn(mutation["id"], seen_ids)
                seen_ids.add(mutation["id"])
                self.assertTrue(mutation["replacements"], mutation["id"])
                mutated_files = generated.apply_mutation(spec["files"], mutation)
                self.assertNotEqual(mutated_files, spec["files"], mutation["id"])
                self.assertEqual(set(mutated_files), set(spec["files"]))
                for old, new in mutation["replacements"]:
                    self.assertNotEqual(old, new)
                    self.assertTrue(any(new in text for text in mutated_files.values()))

    def test_catalogue_views_are_synchronized_for_touched_sections(self):
        catalogues = generated.synced_catalogues(ROOT)
        for section, rel in generated.CATALOGUES.items():
            catalogue = catalogues[rel]
            view = ROOT / catalogue["render"]["path"]
            self.assertEqual(view.read_text(), generated.render_view(section, catalogue, ROOT))


if __name__ == "__main__":
    unittest.main()
