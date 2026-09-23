"""DATA statement fixture packet structure, catalogue binding and mutations."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement
import generate_data_statement_fixtures as generated


class DataStatementFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_fixture_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 13)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 24)
        self.assertEqual(generated.coverage(self.specs),
                         {rule: set(facets) for rule, facets in generated.SELECTED.items()})
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule], case.rule in self.registry.numbered)

    def test_sources_use_nondefault_data_values_and_portable_character_guards(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertTrue(source.endswith("\n"))
            self.assertIn("  implicit none\n", source)
            self.assertIn("data ", source.lower())
            self.assertNotIn(";", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 100)
            self.assertIn(spec["completion"].strip(), source)
            self.assertNotRegex(source, r"(?im)data .* /\s*0\s*/")
        s004 = self.specs["S8_6_7_004_valid__data_statement_runtime_effects"]["source"]
        self.assertLess(s004.index("if (len(padded) /= 4)"), s004.index("if (padded /= 'AB  ')"))
        self.assertLess(s004.index("if (len(cut) /= 2)"), s004.index("if (cut /= 'WX')"))
        self.assertLess(s004.index("if (radix(boz_value) /= 2)"), s004.index("if (boz_value /= 53)"))
        s848 = self.specs["R848_valid__data_statement_constants"]["source"]
        self.assertLess(s848.index("if (len(scalar_character) /= 2)"),
                        s848.index("if (scalar_character /= 'AB')"))
        self.assertIn("if (associated(null_pointer))", s848)
        self.assertIn("if (.not. associated(target_pointer, target_value))", s848)
        vector = self.specs["S8_6_7_004_valid__data_statement_vector_section_order"]["source"]
        self.assertIn("data a([4,1,3]) /41, 11, 31/", vector)
        negative = self.specs["S8_6_7_004_valid__data_statement_negative_step_order"]["source"]
        self.assertLess(negative.index("if (a(3) /= 31)"), negative.index("if (a(1) /= 11)"))

    def test_mutations_bind_complete_parent_and_change_data_features(self):
        total = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["mutations"]), 2)
            for mutation in spec["mutations"]:
                total += 1
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                changed = generated.wrong_oracle_source(spec, mutation)
                self.assertNotEqual(changed, raw)
                self.assertIn(b"DATA STATEMENT", changed)
                self.assertTrue(
                    "data" in mutation["expected"].lower()
                    or "*" in mutation["expected"]
                    or "/" in mutation["expected"]
                    or "parameter" in mutation["expected"].lower()
                    or "'" in mutation["expected"]
                    or "null" in mutation["expected"].lower()
                    or "target_value" in mutation["expected"].lower())
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(dict(spec, source=spec["source"] + "\n"), spec["mutations"][0])
        self.assertEqual(total, 40)

    def test_catalogue_sync_removes_only_selected_facets_and_preserves_foreign_data(self):
        original = self.registry.catalogues[generated.SECTION]
        updated = generated.synced_catalogue(original, self.specs)
        self.assertEqual(original, self.registry.catalogues[generated.SECTION])
        for requirement in updated["requirements"]:
            selected = set(generated.SELECTED.get(requirement["id"], ()))
            self.assertFalse(selected & set(requirement.get("pending", {})))
            if selected:
                self.assertIn("DATA statement fixture family:", requirement["oracle"])
                self.assertIn("DATA statement fixture family boundaries:", requirement["oracle_limitation"])
        old_s004 = next(r for r in original["requirements"] if r["id"] == "S8.6.7-004")
        new_s004 = next(r for r in updated["requirements"] if r["id"] == "S8.6.7-004")
        for facet in ("scalar-position-order", "whole-array-element-order", "initialization-not-execution"):
            self.assertNotIn(facet, old_s004["pending"])
            self.assertNotIn(facet, new_s004["pending"])
        for facet in set(old_s004["pending"]) - set(generated.SELECTED["S8.6.7-004"]):
            self.assertIn(facet, new_s004["pending"])

    def test_view_rendering_and_check_mode_are_idempotent(self):
        catalogue = generated.synced_catalogue(self.registry.catalogues[generated.SECTION], self.specs)
        view = generated.render_view(catalogue, self.specs)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("<!-- BEGIN DATA POSITION EFFECTS -->", view)
        for requirement in catalogue["requirements"]:
            self.assertIn(render_requirement(requirement), view)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        perturbed = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        next(r for r in perturbed["requirements"] if r["id"] == "R840")["pending"]["foreign"] = "synthetic"
        synced = generated.synced_catalogue(perturbed, self.specs)
        self.assertIn("foreign", next(r for r in synced["requirements"] if r["id"] == "R840")["pending"])


if __name__ == "__main__":
    unittest.main()
