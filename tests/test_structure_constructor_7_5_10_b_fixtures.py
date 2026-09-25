"""Batch317 structure-constructor fixtures for Fortran 2023 7.5.10."""

import copy
import json
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_structure_constructor_7_5_10_b_fixtures as generated


class StructureConstructor7510BFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifests_roles_and_requirements(self):
        expected = {generated.runtime_id(variant) for variant in generated.RUNTIME_CASES}
        expected |= {generated.compile_id("binding_keyword", True), generated.compile_id("binding_keyword", False)}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.files), 20)
        runtime = {name: spec for name, spec in self.specs.items() if spec.get("mutations")}
        self.assertEqual(len(runtime), 8)
        for name, case in self.cases.items():
            spec = self.specs[name]
            with self.subTest(case=name):
                self.assertEqual(case.rule, spec["rule"])
                self.assertEqual(case.meta.facets, spec["facets"])
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertEqual(case.meta.images, 1)
                self.assertFalse(case.meta.profiles or case.meta.coarray)
                self.assertEqual(case.fixture.files, ["source.f90"])
                if spec.get("invalid"):
                    self.assertEqual((case.kind, case.meta.evidence), ("invalid", "effect"))
                    self.assertEqual(case.fixture.expectation.phase, "compile")
                    self.assertEqual(case.fixture.expectation.outcome, "diagnose")
                    self.assertIn("line", case.fixture.expectation.diagnostic)
                elif name.endswith("binding_keyword_repair"):
                    self.assertEqual((case.kind, case.meta.evidence), ("valid", "positive-control"))
                    self.assertEqual(case.fixture.expectation.phase, "compile")
                    with self.assertRaises(SuiteError):
                        validate_case_requirement(replace(case, meta=replace(case.meta, evidence="effect")),
                                                  self.registry.requirements[case.rule])
                else:
                    self.assertEqual((case.kind, case.meta.evidence), ("valid", "effect"))
                    self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                                      case.fixture.expectation.exit_code), ("run", "success", 0))
                    self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])

    def test_sources_pin_distinct_assertions_and_feature_mutations(self):
        anchors = {
            "pdt_kind_parameter": ["packet(k=kind(0.0))(payload=4.0)", "kind(x%payload) /= kind(0.0)",
                                   "x%payload /= 4.0"],
            "ordinary_character_defined_assignment": ["len(x%wide) /= 5", "x%wide /= 'AB   '",
                                                       "x%narrow /= 'WX'", "calls /= 0"],
            "private_omissions": ["default_box(tag=29)", "x%hidden /= 17", "allocated(x%store)"],
            "pointer_default_private_omission": ["record(tag=29)", "associated(x%p)", "x%hidden /= 17"],
            "procedure_pointer_target": ["holder(worker)", "associated(x%action)", "x%action(3) /= 8"],
            "allocatable_same_rank_sources": ["from_alloc=source", "from_ordinary=ordinary",
                                               "x%from_alloc(-1) /= 13", "x%from_ordinary(-1) /= 23"],
            "allocatable_source_matrix": ["from_alloc=source", "from_ordinary=ordinary", "scalar=scalar_source",
                                           "x%scalar /= 4"],
            "generic_precedence": ["generic_value = record(11)", "keyword_value = record(payload=11)",
                                    "fallback_value = token(21)", "generic_value%payload /= 29"],
            "binding_keyword": ["procedure :: get"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            if spec.get("invalid"):
                self.assertIn("value = gadget(payload=11, get=19)", source)
            elif spec["variant"] == "binding_keyword":
                self.assertIn("value = gadget(payload=11)", source)
            if spec.get("mutations"):
                facets = {m["facet"] for m in spec["mutations"]}
                self.assertEqual(facets, set(spec["facets"]))
                self.assertGreaterEqual(len(spec["mutations"]), len(spec["facets"]))

    def test_mutation_spans_bind_complete_parent_sources(self):
        total = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            hashes = set()
            for mut in spec.get("mutations", []):
                total += 1
                self.assertEqual(mut["group"], "feature")
                for edit in mut["edits"]:
                    start, end = edit["span"]
                    self.assertEqual(raw[start:end].decode("ascii"), edit["expected"])
                mutant = generated.mutated_source(spec, mut)
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            if spec.get("mutations"):
                changed = dict(spec, source=spec["source"] + "\n")
                with self.assertRaisesRegex(ValueError, "complete parent"):
                    generated.mutated_source(changed, spec["mutations"][0])
        self.assertEqual(total, 17)

    def test_catalogue_sync_and_view_are_union_owned(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("54 of98 facets are represented; 44 remain pending", view)
        self.assertIn("## Complete finite pending plans", view)
        self.assertEqual(view.split("## Complete finite pending plans\n", 1)[1].count("* **`"), 44)
        corrupted = copy.deepcopy(catalogue)
        by_rule = {row["id"]: row for row in corrupted["requirements"]}
        by_rule["R756"]["pending"].pop("required-parentheses")
        with self.assertRaisesRegex(ValueError, "pending partition mismatch: R756"):
            generated.synced_catalogue(corrupted)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        reviewed = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        reviewed["review_state"] = "reviewed"
        self.assertEqual(generated.synced_catalogue(reviewed), reviewed)


if __name__ == "__main__":
    unittest.main()
