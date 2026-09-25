"""Generated BLOCK and branch fixture packet invariants."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, render_requirement
import generate_block_branch_11_1_4_11_2_fixtures as generated


class BlockBranchFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_case_set_and_manifest_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 29)
        self.assertEqual(len(self.files), 58)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.build[0].form, "free")
            if spec["kind"] == "valid":
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.outcome, "success")
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                self.assertTrue(spec["mutations"], name)
            else:
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")
                diagnostic = case.fixture.expectation.diagnostic
                self.assertEqual(diagnostic["file"], "source.f90")
                self.assertGreaterEqual(diagnostic["line"], 1)
                self.assertLessEqual(diagnostic["line"], diagnostic["end_line"])
                self.assertEqual(diagnostic["excludes_any"], list(generated.EXCLUSIONS))
                self.assertIn(spec["control_id"], self.specs)

    def test_selected_facets_are_bound_and_only_unselected_facets_remain_pending(self):
        for rule, facets in generated.SELECTED.items():
            requirement = self.registry.requirements[rule]
            self.assertTrue(set(facets).isdisjoint(requirement.get("pending", {})))
            self.assertTrue(set(facets) <= set(requirement["facets"]))
            self.assertIn(generated.ORACLE_PREFIX[rule], requirement["oracle"])
            self.assertIn(generated.LIMIT_PREFIX[rule], requirement["oracle_limitation"])
        for section, rel in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(section, catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            self.assertEqual(view, (ROOT / generated.VIEWS[section]).read_text())
            for row in catalogue["requirements"]:
                self.assertIn(render_requirement(row), view)

    def test_feature_mutations_are_nonidentical_ascii_complete_programs(self):
        seen = 0
        for spec in self.specs.values():
            if spec["kind"] != "valid":
                continue
            original = spec["source"]
            for mutation in spec["mutations"]:
                self.assertIn(mutation["facet"], spec["facets"])
                self.assertNotEqual(mutation["source"], original)
                self.assertEqual(mutation["source"].count("\n"), original.count("\n"))
                mutation["source"].encode("ascii")
                self.assertIn("program ", mutation["source"])
                self.assertIn("end program", mutation["source"])
                seen += 1
        self.assertEqual(seen, 25)

    def test_generated_files_are_byte_identical_and_check_mode_is_read_only(self):
        for path, raw in self.files.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
