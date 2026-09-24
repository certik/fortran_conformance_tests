"""Runtime fixture checks for Fortran 2023 pointer association rules 19.5.2."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_pointer_association_19_5_2_fixtures as generated


class PointerAssociation1952FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_owned_cases_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 11)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 33)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 33)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])
            with self.assertRaises(SuiteError):
                bad = case.__class__(
                    case.name,
                    case.rule,
                    case.kind,
                    case.path,
                    case.meta.__class__(case.meta.facets + ["foreign"], case.meta.evidence),
                    case.review_key,
                    case.fixture,
                )
                validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_are_bounded_and_reach_pointer_events(self):
        required_tokens = {
            "reference_general": ["reader => read_target", "writer => write_target", "writer = 77"],
            "status_over_time": ["p => first_target", "p => second_target", "nullify(p)"],
            "target_characteristics": ["lbound(p_array, 1)", "len(p_text)", "select type (p_poly)"],
            "initialization_status": ["dis => null()", "assoc => associated_target", "nullify(changing)"],
            "definition_status": ["reader => defined_target", "writer => definable_target", "writer = 789"],
            "associated_allocate_assignment": ["allocate(p_alloc)", "p_from_pointer => source_pointer", "p_allocatable => alloc_target"],
            "associated_source_dummy": ["allocate(dst, source=src)", "integer, pointer, intent(in) :: dummy"],
            "associated_default_components": ["intent(out) :: box", "type(box_local) :: local", "allocate(box_alloc :: allocated_box)"],
            "disassociated_direct": ["nullify(p_nullify)", "deallocate(p_dealloc)", "p_assignment => q_null"],
            "disassociated_source_default": ["allocate(dst, source=src)", "type(box_local) :: local", "allocate(box_alloc :: allocated_box)"],
            "name_association_propagates": ["call change_dummy(actual)", "dummy => target"],
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
            self.assertIn("! standard: f2023\n", source)
            self.assertIn("  implicit none\n", source)
            self.assertIn("write(*,'(a)') '" + spec["completion"].strip() + "'", source)
            self.assertRegex(source, r"call expect_equal\(checks, \d+, 'check count before completion'\)")
            self.assertNotRegex(source.lower(), r"\b(real|complex|random_number|system_clock|c_loc|loc)\b")
            for token in required_tokens[spec["variant"]]:
                self.assertIn(token, source)

    def test_mutations_are_facet_specific_feature_changes(self):
        by_facet = {}
        for spec in self.specs.values():
            self.assertEqual(generated.sha(spec["source"].encode("ascii")), spec["source_sha256"])
            hashes = {spec["source_sha256"]}
            self.assertEqual(len(spec["mutations"]), len(spec["facets"]))
            for mutation in spec["mutations"]:
                self.assertEqual(mutation["kind"], "feature")
                self.assertIn(mutation["facet"], spec["facets"])
                by_facet.setdefault((spec["rule"], mutation["facet"]), 0)
                by_facet[(spec["rule"], mutation["facet"])] += 1
                mutant = generated.mutate_source(spec, mutation)
                self.assertNotEqual(mutant, spec["source"])
                digest = generated.sha(mutant.encode("ascii"))
                self.assertEqual(digest, mutation["mutant_sha256"])
                self.assertNotIn(digest, hashes)
                hashes.add(digest)
                self.assertIn(spec["completion"].strip(), mutant)
                for repl in mutation["replacements"]:
                    self.assertEqual(spec["source"].count(repl["expected"]), 1)
                    self.assertNotEqual(repl["expected"], repl["replacement"])
        expected = {
            (rule, facet)
            for rule, facets in generated.FACETS_BY_RULE.items()
            for facet in facets
        }
        self.assertEqual(set(by_facet), expected)
        self.assertTrue(all(count == 1 for count in by_facet.values()))

    def test_catalogues_synced_pending_and_rendered(self):
        for section, rel in generated.CATALOGUES.items():
            catalogue = json.loads((ROOT / rel).read_text())
            expected = generated.synced_catalogue(section, catalogue, self.specs)
            self.assertEqual(expected, catalogue)
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.FACETS_BY_RULE.items():
                if not rule.startswith("S" + section + "-"):
                    continue
                self.assertEqual(set(by_rule[rule].get("pending", {})), generated.EXPECTED_REMAINING[rule])
                for facet in facets:
                    self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            view = generated.rendered_view(section, catalogue, ROOT)
            self.assertEqual((ROOT / generated.VIEWS[section]).read_text(), view)
        self.registry.render(write=False)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)

    def test_identity_sabotage_is_rejected(self):
        spec = next(iter(self.specs.values()))
        plan = json.loads(json.dumps(spec["mutations"][0]))
        plan["replacements"][0]["replacement"] = plan["replacements"][0]["expected"]
        self.assertEqual(generated.mutate_source(spec, plan, allow_identical=True), spec["source"])
        with self.assertRaises(ValueError):
            generated.mutate_source(spec, plan)


if __name__ == "__main__":
    unittest.main()
