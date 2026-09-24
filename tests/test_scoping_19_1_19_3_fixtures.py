"""Runtime fixture checks for Fortran 2023 scoping rules 19.1-19.3.4."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_scoping_19_1_19_3_fixtures as generated


class Scoping191193FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.CASES})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertIsInstance(json.loads(json.dumps(self.specs)), dict)
        self.assertEqual(len(self.files), 2 * len(generated.CASES))
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            spec = self.specs[case.name]
            expected_evidence = generated.CASES[spec["variant"]].get("evidence", "effect")
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", expected_evidence, "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["completion"]])
            self.assertEqual(expect.stderr, [""])
            self.assertEqual(generated.CASES[spec["variant"]]["facets"], case.meta.facets)
            validate_case_requirement(case, self.registry.requirements[case.rule])
            with self.assertRaises(SuiteError):
                validate_case_requirement(case.__class__(case.name, case.rule, case.kind, case.path,
                                                          case.meta.__class__(case.meta.facets + ["foreign"],
                                                                              case.meta.evidence),
                                                          case.review_key, case.fixture),
                                          self.registry.requirements[case.rule])

    def test_sources_have_load_bearing_sentinels_and_headers(self):
        needles = {
            "host_rename_shadow": ["host_seen = token", "integer :: token\n    token = 73", "call expect_equal(token, 41"],
            "construct_statement_entities": ["associate (i => construct_source)", "implied_values = [(i, i = 1, 3)]", "call expect_equal(i, 99"],
            "association_rename": ["local_name => source_name", "source_name = 99", "host_seen = token"],
            "common_block_homonym": ["common /blk/ cb_member", "ordinary = blk + 1", "call expect_equal(cb_member, 29"],
            "function_results": ["scope_result = 42 + n", "answer = scope_recur(n - 1) + 10"],
            "components": ["type :: type_one", "selected = obj%tag", "built = type_one(tag=44)", "tag = 99"],
            "argument_keywords": ["first_proc(other=7, item=3)", "second_proc(other=8, item=4)"],
            "type_parameters": ["type :: box(k)", "integer(kind=k) :: value", "type(box(k=default_k)) :: b", "b%k"],
            "binding_reference": ["procedure :: calc => calc_impl", "obj%calc()", "calc = 99"],
            "generic_binding_operator": ["generic :: operator(+) => add_box", "combined = left + right"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertNotIn("/tmp", source.lower())
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("! standard: f2023\n", source)
            self.assertEqual(source.count("  implicit none\n") >= 1, True)
            self.assertIn("write(*,'(a)') '" + spec["completion"].strip() + "'", source)
            self.assertRegex(source, r"call expect_equal\(.+check count before completion")
            self.assertNotRegex(source, r"(?i)\b(real|complex|coarray|sync\s+all|c_loc|transfer)\b")
            for needle in needles.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_mutation_definitions_change_complete_parent_sources(self):
        total = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["mutations"]), 2)
            self.assertTrue(any(m["kind"] == "feature" for m in spec["mutations"]))
            hashes = {spec["source_sha256"]}
            for mutation in spec["mutations"]:
                total += 1
                for old, new in mutation["replacements"]:
                    self.assertEqual(spec["source"].count(old), 1, (spec["variant"], mutation["id"], old))
                    self.assertNotEqual(old, new)
                mutant = generated.mutated_source(spec, mutation)
                digest = generated.sha(mutant)
                self.assertNotIn(digest, hashes)
                hashes.add(digest)
                self.assertNotIn(spec["completion"].replace("OK", "BAD").encode(), mutant)
        self.assertGreaterEqual(total, 45)

    def test_catalogues_remove_only_selected_pending_entries_and_render(self):
        for rel in sorted(set(generated.CATALOGUES.values())):
            catalogue = json.loads((ROOT / rel).read_text())
            expected = generated.synced_catalogue(rel, catalogue)
            self.assertEqual(expected, catalogue)
        for rule, facets in generated.FACETS_BY_RULE.items():
            section_path = generated.catalogue_path_for_rule(rule)
            catalogue = json.loads((ROOT / section_path).read_text())
            req = {row["id"]: row for row in catalogue["requirements"]}[rule]
            for facet in facets:
                self.assertNotIn(facet, req.get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], req["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], req["oracle_limitation"])
        self.registry.render(write=False)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
