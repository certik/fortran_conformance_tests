"""Generated POINTER/SAVE 8.5.14/8.5.16 fixtures and owned catalogue state."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_pointer_save_8_5_14_8_5_16_fixtures as generated


class PointerSaveFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}

    def test_exact_generated_cases_and_manifest_contracts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 17)
        self.assertEqual(len(self.files), 34)
        invalid = {name for name, spec in self.specs.items() if spec.get("invalid")}
        self.assertEqual(len(invalid), 6)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].id, case.fixture.build[0].source), ("source", "source.f90"))
            validate_case_requirement(case, self.registry.requirements[case.rule])
            if spec.get("invalid"):
                self.assertEqual((case.kind, case.meta.evidence), ("invalid", "effect"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("compile", "diagnose"))
                self.assertEqual(case.fixture.expectation.diagnostic["line"], spec["line"])
                self.assertNotIn("equals_any", case.fixture.expectation.diagnostic)
                self.assertIn("asr", case.fixture.expectation.diagnostic["excludes_any"])
            else:
                self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("run", "success"))

    def test_runtime_feature_mutations_are_unique_conforming_text_substitutions(self):
        mutation_count = 0
        facets = set()
        for spec in self.specs.values():
            source = spec["source"]
            for mutation in spec.get("mutations", []):
                mutation_count += 1
                facets.add(mutation["facet"])
                self.assertIn(mutation["facet"], spec["facets"])
                self.assertEqual(source.count(mutation["old"]), 1, mutation["id"])
                mutant = generated.apply_mutation(source, mutation)
                self.assertNotEqual(mutant, source)
                self.assertIn("error stop", mutant)
        self.assertEqual(mutation_count, 17)
        runtime_facets = {facet for spec in self.specs.values() if spec.get("mutations") for facet in spec["facets"]}
        self.assertEqual(facets, runtime_facets)

    def test_every_claimed_facet_has_feature_mutation_or_negative_control_pair(self):
        control_keys = {spec.get("control") for spec in self.specs.values() if spec.get("invalid")}
        available_controls = {spec["key"] for spec in self.specs.values() if not spec.get("invalid")}
        mutation_pairs = {(spec["rule"], mutation["facet"])
                          for spec in self.specs.values() for mutation in spec.get("mutations", [])}
        negative_pairs = {(spec["rule"], facet)
                          for spec in self.specs.values() if spec.get("invalid")
                          for facet in spec["facets"]}
        self.assertTrue(control_keys <= available_controls)
        for spec in self.specs.values():
            if spec.get("invalid"):
                continue
            for facet in spec["facets"]:
                pair = (spec["rule"], facet)
                self.assertTrue(pair in mutation_pairs or pair in negative_pairs,
                                f"{spec['id']}:{facet} lacks a feature mutation or negative/control pair")
        selected = {(rule, facet) for rules in generated.selected_by_section().values()
                    for rule, facets in rules.items() for facet in facets}
        self.assertTrue(selected <= (mutation_pairs | negative_pairs))

    def test_generator_updates_only_selected_pending_facets_and_owned_paragraphs(self):
        selected = generated.selected_by_section()
        for section, rel in generated.CATALOGUES.items():
            disk = self.registry.catalogues[section]
            updated = generated.synced_catalogue(section, disk)
            self.assertEqual(updated, disk)
            for rule, facets in selected[section].items():
                row = next(item for item in disk["requirements"] if item["id"] == rule)
                self.assertTrue(facets <= set(row["facets"]))
                self.assertFalse(facets & set(row.get("pending", {})))
                self.assertIn(generated.ORACLES[(section, rule)], row["oracle"])
                self.assertIn(generated.LIMITATIONS[(section, rule)], row["oracle_limitation"])
            clone = copy.deepcopy(disk)
            for rule, facets in selected[section].items():
                row = next(item for item in clone["requirements"] if item["id"] == rule)
                for facet in facets:
                    row.setdefault("pending", {})[facet] = "synthetic selected pending"
            synced = generated.synced_catalogue(section, clone)
            for rule, facets in selected[section].items():
                row = next(item for item in synced["requirements"] if item["id"] == rule)
                self.assertFalse(facets & set(row.get("pending", {})))

    def test_generated_files_catalogues_and_views_are_exact(self):
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        for section, rel in generated.CATALOGUES.items():
            catalogue = json.loads((ROOT / rel).read_text())
            view = generated.render_view(section, catalogue, ROOT)
            self.assertEqual((ROOT / generated.VIEWS[section]).read_text(), view)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            for row in catalogue["requirements"]:
                self.assertIn(render_requirement(row), view)

    def test_sources_stay_within_packet_scope_and_no_foreign_tooling_changes(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("/tmp", source)
            self.assertNotIn("coarray", source.lower())
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec["rule"].startswith("S8.5.14"):
                self.assertIn("pointer", source.lower())
            if spec["rule"].startswith("S8.5.16") or spec["rule"] in {"C861", "C862"}:
                self.assertRegex(source.lower(), r"\bsave\b|common")


if __name__ == "__main__":
    unittest.main()
