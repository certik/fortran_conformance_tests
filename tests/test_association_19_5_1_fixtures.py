"""Runtime fixture checks for Fortran 2023 association rules 19.5.1.3-19.5.1.6."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_association_19_5_1_fixtures as generated


class Association1951FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifests(self):
        self.assertEqual(set(self.cases), {case["id"] for case in generated.CASES.values()})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), sum(len(case["files"]) + 1 for case in generated.CASES.values()))
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(generated.CASES[spec["variant"]]["facets"], case.meta.facets)
            self.assertEqual(set(case.fixture.files), set(spec["files"]))
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])
            with self.assertRaises(SuiteError):
                validate_case_requirement(case.__class__(case.name, case.rule, case.kind, case.path,
                                                          case.meta.__class__(case.meta.facets + ["foreign"],
                                                                              case.meta.evidence),
                                                          case.review_key, case.fixture),
                                          self.registry.requirements[case.rule])

    def test_sources_have_sentinels_headers_and_c_companion(self):
        required_needles = {
            "use_persistence": ["alias => shared", "later_seen = alias", "shared = 501"],
            "host_core": ["type(box) :: local_box", "integer :: arr(p)", "q => t"],
            "host_hiding_global": ["use association_provider_x, only: x", "use m, only: value"],
            "external_global_hide": ["integer, external :: x", "observed = x()"],
            "local_object": ["integer :: x", "x = 302"],
            "local_type_param": ["type :: box(x)", "integer, len :: x = 304"],
            "local_intrinsic": ["intrinsic :: abs", "integer :: abs, x, observed, checks"],
            "local_generic": ["interface x", "local_x = 318 + n"],
            "local_proc_pointer": ["procedure(intfun), pointer :: x", "x => local_target"],
            "linkage_bind_module": ["bind(c, name=\"assoc_link_value\")", "extern int assoc_link_value;"],
            "value_selectors": ["associate (a => x + 1)", "associate (a => arr(idx))"],
            "construct_lifetime": ["associate (a => x)", "a = 99"],
        }
        for spec in self.specs.values():
            for name, source in spec["files"].items():
                source.encode("ascii")
                self.assertNotIn("\r", source)
                self.assertNotIn("/tmp", source.lower())
                self.assertLessEqual(max(map(len, source.splitlines())), 132)
                if name.endswith(".f90"):
                    self.assertEqual(source.count("! rule: "), 1)
                    self.assertIn("! standard: f2023\n", source)
                    self.assertIn("write(*,'(a)') '" + spec["completion"].strip() + "'", source)
                    self.assertRegex(source, r"call expect_equal\(.+check count before completion")
                    self.assertNotRegex(source.lower(), r"sync\s+all|coarray")
            combined = "\n".join(spec["files"].values())
            for needle in required_needles.get(spec["variant"], []):
                self.assertIn(needle, combined)

    def test_mutation_definitions_change_complete_parent_sources(self):
        total = 0
        feature_facets = set()
        for spec in self.specs.values():
            for name, source in spec["files"].items():
                self.assertEqual(generated.sha(source.encode("ascii")), spec["files_sha256"][name])
            self.assertGreaterEqual(len(spec["mutations"]), 1)
            self.assertTrue(any(m["kind"] == "feature" for m in spec["mutations"]))
            parent_hashes = {name: {digest} for name, digest in spec["files_sha256"].items()}
            for mutation in spec["mutations"]:
                total += 1
                self.assertEqual(mutation["kind"], "feature")
                self.assertTrue(mutation.get("facets"))
                feature_facets.update(mutation["facets"])
                target = mutation.get("file", "source.f90")
                parent = spec["files"][target]
                for old, new in mutation["replacements"]:
                    self.assertEqual(parent.count(old), 1, (spec["variant"], mutation["id"], old))
                    self.assertNotEqual(old, new)
                mutant = generated.mutated_files(spec, mutation)
                digest = generated.sha(mutant[target].encode("ascii"))
                self.assertNotIn(digest, parent_hashes[target])
                parent_hashes[target].add(digest)
                self.assertNotIn(spec["completion"].replace("OK", "BAD"), mutant[target])
        self.assertEqual(feature_facets, {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        table_facets = set(generated.FACET_ASSERTION_MUTATION_TABLE)
        self.assertEqual(table_facets, feature_facets)
        mutant_facets = {(facet, mutation["id"]) for spec in self.specs.values()
                         for mutation in spec["mutations"] for facet in mutation["facets"]}
        for facet, rows in generated.FACET_ASSERTION_MUTATION_TABLE.items():
            self.assertTrue(rows)
            seen_ids = set()
            for assertion, mutation_id in rows:
                self.assertIsInstance(assertion, str)
                self.assertIsInstance(mutation_id, str)
                self.assertNotIn(mutation_id, seen_ids, facet)
                seen_ids.add(mutation_id)
                self.assertIn((facet, mutation_id), mutant_facets)
        self.assertGreaterEqual(total, 42)

    def test_catalogues_remove_only_selected_pending_entries_and_render(self):
        for rel in sorted(set(generated.CATALOGUES.values())):
            catalogue = json.loads((ROOT / rel).read_text())
            self.assertEqual(generated.synced_catalogue(rel, catalogue), catalogue)
        for rule, facets in generated.FACETS_BY_RULE.items():
            catalogue = json.loads((ROOT / generated.catalogue_path_for_rule(rule)).read_text())
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
