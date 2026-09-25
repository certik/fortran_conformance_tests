"""Fixture packet tests for Fortran 2023 interface blocks, 15.4.3.1-15.4.3.2."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement

import generate_interface_block_15_4_3_2_fixtures as generated


class InterfaceBlock15432FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}

    def test_exact_owned_cases_and_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 42)
        self.assertEqual(len(self.files), 84)
        self.assertEqual(sum(len(v) for v in generated.SELECTED.values()), 35)
        runtime_feature_facets = set()
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            validate_case_requirement(case, self.registry.requirements[case.rule])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            for mutation in spec.get("feature_mutations", []):
                runtime_feature_facets.add(mutation["facet"])
        for rule in generated.RUNTIME_RULES:
            for facet in generated.SELECTED.get(rule, []):
                if rule != "S15.4.3.2-004" or facet != "specific-interface-block-definition":
                    self.assertIn(facet, runtime_feature_facets)

    def test_runtime_and_diagnostic_contracts(self):
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            if spec["kind"] == "valid":
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                expect = case.fixture.expectation
                self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
                self.assertEqual(expect.stdout, [spec["completion"]])
                self.assertEqual(expect.stderr, [""])
            else:
                self.assertEqual(case.kind, "invalid")
                self.assertIsNone(case.fixture.link)
                expect = case.fixture.expectation
                self.assertEqual((expect.phase, expect.step, expect.outcome), ("compile", "source", "diagnose"))
                self.assertEqual(expect.diagnostic["file"], "source.f90")
                self.assertEqual(expect.diagnostic["line"], spec["diagnostic"]["line"])
                self.assertEqual(expect.diagnostic["end_line"], spec["diagnostic"]["end_line"])
                self.assertEqual(expect.diagnostic["excludes_any"], list(generated.EXCLUSIONS))
                self.assertNotIn("contains_any", expect.diagnostic)
                self.assertNotIn("equals_any", expect.diagnostic)
                control = self.specs[spec["repair"]["control_id"]]
                self.assertEqual(spec["repair"]["control_sha256"], control["source_sha256"])
                self.assertEqual(control["kind"], "valid")
                if spec["variant"] == "r1505_subroutine_end":
                    repaired = spec["source"].replace("    end function ext_sub_body",
                                                      "    end subroutine ext_sub_body", 1)
                    self.assertEqual(repaired, control["source"])

    def test_sources_are_ascii_self_checking_and_not_argument_association_claims(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec["kind"] == "valid":
                self.assertIn("implicit none", source.lower())
                self.assertIn("print '(a)'", source)
                self.assertIn(spec["completion"].strip(), source)
                self.assertNotIn("iomsg", source.lower())
                self.assertNotRegex(source.lower(), r"call\s+\w+\s*\(\s*\w+\s*=")

    def test_mutation_definitions_bind_parent_and_are_feature_specific(self):
        total = sum(len(generated.all_mutations(spec)) for spec in self.specs.values())
        self.assertEqual(total, 20)
        feature_count = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            seen_feature_facets = set()
            for mutation in generated.all_mutations(spec):
                text = spec["source"]
                for expected, replacement in mutation["replacements"]:
                    self.assertEqual(text.count(expected), 1)
                    text = text.replace(expected, replacement)
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, text.encode("ascii"))
                self.assertNotEqual(mutant, raw)
                if mutation in spec.get("feature_mutations", []):
                    self.assertTrue(mutation.get("conforming"))
                    self.assertNotIn(mutation["facet"], seen_feature_facets)
                    seen_feature_facets.add(mutation["facet"])
                    feature_count += 1
        self.assertEqual(feature_count, 12)

    def test_catalogues_are_synced_and_rendered_for_selected_facets(self):
        for section, path in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            rendered = generated.render_view(section, catalogue, ROOT)
            self.assertEqual((ROOT / catalogue["render"]["path"]).read_text(), rendered)
            rules = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.SELECTED.items():
                if rule not in rules:
                    continue
                for facet in facets:
                    self.assertNotIn(facet, rules[rule].get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], rules[rule]["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], rules[rule]["oracle_limitation"])
            for row in catalogue["requirements"]:
                self.assertIn(render_requirement(row), rendered)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)


if __name__ == "__main__":
    unittest.main()
