"""Fixture checks for Fortran 2023 data objects clauses 9.1-9.3."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_data_objects_9_1_9_3_fixtures as generated


class DataObjects913FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_owned_cases_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 20)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            if spec["kind"] == "valid":
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.meta.evidence, spec["evidence"])
                self.assertEqual(case.fixture.link, {"driver": "fortran", "objects": ["source.o"], "output": "program"})
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
            else:
                self.assertNotEqual(case.kind, "valid")
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")

    def test_sources_are_bounded_and_reach_claimed_constructs(self):
        required = {
            "designator_forms": ["scalar_value", "arr(2)", "arr(1:3:2)", "z%im", "person%age", "text(2:4)"],
            "variable_alternatives": ["x = 11", "ip() = 23"],
            "variable_boundary_control": ["x = 7", "len_value = len(c)"],
            "c901_named_constant_control": ["integer :: k = 1", "k = 2"],
            "c902_data_pointer_controls": ["p_admit() = 31", "p_nonptr_repair() = 41", "p_proc_repair() = 51"],
            "variable_identity": ["x = 41", "ip() = 42", "selected_ptr() = 52"],
            "defined_references": ["x = 51", "p => t", "write(buffer, '(i2)') 73"],
            "variable_name_token_control": ["namelist /grp_one/ x", "namelist /grp_two/ z"],
            "c903_ordinary_variable_name": ["namelist /grp/ ordinary", "read(input, nml=grp"],
            "char_variable_designator": ["write(buffer, '(a)') 'ok'"],
            "character_type_admission": ["write(buffer, '(a)') 'abc'"],
            "int_variable_stat": ["allocate(a, stat=s)", "allocate(b, stat=stat_ptr())"],
            "integer_type_admission": ["allocate(a, stat=stat_value)"],
            "constant_references": ["literal_total = 1 + 2", "integer, parameter :: k = 81", "parameter (stmt_param = 5)", "arr(2)", "letters(2:3)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertNotIn("/tmp", source.lower())
            body_lines = [line for line in source.splitlines() if not line.startswith('! covers: ')]
            self.assertLessEqual(max(map(len, body_lines)), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("! standard: f2023\n", source)
            if spec["kind"] == "valid":
                self.assertIn("  implicit none\n", source)
                self.assertIn("write(*,'(a)') '" + spec["completion"].strip() + "'", source)
                self.assertRegex(source, r"call expect_int\(checks, \d+, 'check count before completion'\)")
                for token in required[spec["variant"]]:
                    self.assertIn(token, source)

    def test_mutations_are_facet_specific_feature_changes(self):
        by_facet = {}
        for spec in self.specs.values():
            self.assertEqual(generated.sha(spec["source"].encode("ascii")), spec["source_sha256"])
            if spec["kind"] != "valid":
                self.assertEqual(spec["mutations"], [])
                continue
            self.assertEqual(len(spec["mutations"]), len(spec["facets"]))
            hashes = {spec["source_sha256"]}
            for mutation in spec["mutations"]:
                self.assertEqual(mutation["kind"], "feature")
                self.assertIn(mutation["facet"], spec["facets"])
                by_facet[(spec["rule"], mutation["facet"])] = by_facet.get((spec["rule"], mutation["facet"]), 0) + 1
                mutant = generated.mutate_source(spec, mutation)
                digest = generated.sha(mutant.encode("ascii"))
                self.assertEqual(digest, mutation["mutant_sha256"])
                self.assertNotIn(digest, hashes)
                hashes.add(digest)
                self.assertIn(spec["completion"].strip(), mutant)
                for repl in mutation["replacements"]:
                    self.assertEqual(spec["source"].count(repl["expected"]), 1)
                    self.assertNotEqual(repl["expected"], repl["replacement"])
        expected = {(rule, facet) for rule, facets in generated.COVERED.items() for facet in facets}
        self.assertTrue(expected <= set(by_facet))
        self.assertTrue(all(count >= 1 for count in by_facet.values()))

    def test_catalogues_synced_pending_and_rendered(self):
        for section, rel in generated.CATALOGUES.items():
            catalogue = json.loads((ROOT / rel).read_text())
            expected = generated.synced_catalogue(section, catalogue, self.specs)
            self.assertEqual(catalogue, expected)
            for row in catalogue["requirements"]:
                for facet in generated.COVERED.get(row["id"], set()):
                    self.assertNotIn(facet, row.get("pending", {}))
                if row["id"] in generated.COVERED:
                    self.assertIn(generated.ORACLE_PREFIX[row["id"]], row["oracle"])
                    self.assertIn(generated.LIMIT_PREFIX[row["id"]], row["oracle_limitation"])
            self.assertEqual((ROOT / generated.VIEWS[section]).read_text(), generated.rendered_view(section, catalogue, ROOT))
        self.registry.render(write=False)

    def test_generation_is_deterministic_and_identity_sabotage_rejected(self):
        generated.generate(ROOT, check=True)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        spec = next(spec for spec in self.specs.values() if spec["mutations"])
        mutation = json.loads(json.dumps(spec["mutations"][0]))
        mutation["replacements"][0]["replacement"] = mutation["replacements"][0]["expected"]
        self.assertEqual(generated.mutate_source(spec, mutation, allow_identical=True), spec["source"])
        with self.assertRaises(ValueError):
            generated.mutate_source(spec, mutation)


if __name__ == "__main__":
    unittest.main()
