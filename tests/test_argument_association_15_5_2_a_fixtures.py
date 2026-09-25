"""Generated fixtures for Fortran 2023 argument association 15.5.2 batch A."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_argument_association_15_5_2_a_fixtures as generated


class ArgumentAssociation1552AFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_owned_cases_and_requirement_roles(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 29)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 41)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 40)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            validate_case_requirement(case, self.registry.requirements[case.rule], numbered=case.rule.startswith("C"))
            if case.kind == "valid":
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertIn(case.meta.evidence, {"effect", "positive-control"})
            else:
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("compile", "diagnose"))
                self.assertEqual(case.fixture.expectation.diagnostic["line"], 11)
            with self.assertRaises(SuiteError):
                bad = case.__class__(case.name, case.rule, case.kind, case.path,
                                     case.meta.__class__(case.meta.facets + ["foreign"], case.meta.evidence),
                                     case.review_key, case.fixture)
                validate_case_requirement(bad, self.registry.requirements[case.rule], numbered=case.rule.startswith("C"))

    def test_sources_are_self_checking_and_bounded(self):
        required = {
            "correspondence": ["call record_pair(b=17, a=11", "call record_pair(23, 29", "call reduced%set(41)"],
            "passed_object": ["call type_bound%set(47)", "proc_ptr%pp => set_box", "call proc_ptr%pp(43)"],
            "conditional_order": ["(.true. ? 101 : 202)", "(.false. ? 11 : 33)"],
            "conditional_actual": ["variable_actual = 57", "(.true. ? variable_actual : 58)"],
            "argument_association_p1": ["p => target_value", "inquiry = associated(p)"],
            "argument_association_value": ["integer, value :: x", "x = 29", "caller_value = 17"],
            "alloc_pointer_rank": ["lbound(x, 1)", "ubound(x, 1)", "value = x(0)"],
            "alloc_dummy_intent_out": ["intent(out) :: x(:)", "was_alloc = allocated(x)", "allocate(x(1:1))"],
            "pointer_dummy_target": ["associated(q, module_target_scalar)", "call ptr_target_in(module_target_scalar"],
            "c1550_control": ["pointer, contiguous :: p(:)", "call accept_contiguous(p)"],
            "c1550_noncontiguous": ["integer, pointer :: p(:)", "call accept_contiguous(p)"],
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
            if spec["kind"] == "valid":
                self.assertIn("write(*,'(a)') '" + spec["completion"].strip() + "'", source)
                self.assertRegex(source, r"call expect_equal\(checks, \d+, 'check count'\)")
            for needle in required.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_mutations_are_feature_specific_and_bound(self):
        seen = {}
        for spec in self.specs.values():
            self.assertEqual(generated.sha(spec["source"].encode("ascii")), spec["source_sha256"])
            digests = {spec["source_sha256"]}
            for mutation in spec["mutations"]:
                self.assertEqual(mutation["kind"], "feature")
                self.assertIn(mutation["facet"], spec["facets"])
                seen[(spec["rule"], mutation["facet"])] = seen.get((spec["rule"], mutation["facet"]), 0) + 1
                mutant = generated.mutate_source(spec, mutation)
                self.assertNotEqual(mutant, spec["source"])
                digest = generated.sha(mutant.encode("ascii"))
                self.assertEqual(digest, mutation["mutant_sha256"])
                self.assertNotIn(digest, digests)
                digests.add(digest)
                for repl in mutation["replacements"]:
                    self.assertEqual(spec["source"].count(repl["expected"]), 1)
                    self.assertNotEqual(repl["expected"], repl["replacement"])
        self.assertEqual(len(seen), 40)
        self.assertTrue(all(count == 1 for count in seen.values()))

    def test_catalogues_and_views_are_synced(self):
        for section, rel in generated.CATALOGUES.items():
            catalogue = json.loads((ROOT / rel).read_text())
            expected = generated.synced_catalogue(section, catalogue, self.specs)
            self.assertEqual(expected, catalogue)
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for spec in self.specs.values():
                if not spec["rule"].startswith("S" + section + "-") and not (section == "15.5.2.8" and spec["rule"] == "C1550"):
                    continue
                row = by_rule[spec["rule"]]
                for facet in spec["facets"]:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[spec["rule"]], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[spec["rule"]], row["oracle_limitation"])
            view = generated.rendered_view(section, catalogue, ROOT)
            self.assertEqual((ROOT / generated.VIEWS[section]).read_text(), view)
        self.registry.render(write=False)

    def test_generation_check_is_read_only(self):
        self.assertEqual(generated.build_corpus(ROOT)[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
