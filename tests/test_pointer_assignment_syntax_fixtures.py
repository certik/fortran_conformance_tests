"""Pointer-assignment statement syntax fixture metadata."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_pointer_assignment_syntax_fixtures as generated


class PointerAssignmentSyntaxFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_cases_and_twenty_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 46)
        selected = {(rule, facet) for rule, facets in generated.SELECTED.items() for facet in facets}
        covered = {(case.rule, facet) for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, selected)
        self.assertEqual(len(covered), 20)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertTrue(name.startswith(generated.PREFIX))
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.build[0].source, "source.f90")
            self.assertEqual(case.fixture.build[0].language, "fortran")
            self.assertEqual(case.fixture.build[0].form, "free")
            if spec["kind"] == "invalid":
                self.assertEqual((case.kind, case.meta.evidence), ("invalid", "effect"))
                self.assertEqual(self.members[name]["cohort"], "diagnostic-only")
                self.assertIsNone(case.fixture.link)
                expect = case.fixture.expectation
                self.assertEqual((expect.phase, expect.step, expect.outcome), ("compile", "source", "diagnose"))
                self.assertEqual(expect.diagnostic["file"], "source.f90")
                self.assertEqual(expect.diagnostic["line"], spec["diagnostic_line"])
                self.assertEqual(expect.diagnostic["end_line"], spec["diagnostic_line"])
                self.assertEqual(expect.diagnostic["contains_any"], spec["contains_any"])
                for bad in ("not implemented", "internal error", "asr", "syntax error"):
                    self.assertIn(bad, expect.diagnostic["excludes_any"])
            elif spec["phase"] == "run":
                self.assertEqual((case.kind, case.meta.evidence), ("valid", "positive-control"))
                self.assertEqual(self.members[name]["cohort"], "positive-control")
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                expect = case.fixture.expectation
                self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
                self.assertEqual(expect.stdout, [spec["stdout"]])
                self.assertEqual(expect.stderr, [""])
            else:
                self.assertEqual((case.kind, case.meta.evidence), ("valid", "positive-control"))
                self.assertEqual(self.members[name]["cohort"], "positive-control")
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("compile", "success"))
            validate_case_requirement(case, self.registry.requirements[case.rule])

    def test_runtime_sources_use_nondefault_bounds_and_two_way_aliasing(self):
        runtime = [spec for spec in self.specs.values() if spec["phase"] == "run"]
        self.assertEqual(len(runtime), 5)
        for spec in runtime:
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertNotRegex(source.lower(), r"\b(transfer|loc|c_loc|equivalence|common)\s*\(")
            if spec["variant"] == "bounds_spec":
                self.assertIn("p(-4:,6:) => t", source)
                self.assertIn("lbound(p) /= [-4,6]", source)
                self.assertIn("ubound(p) /= [-2,7]", source)
                self.assertIn("shape(p) /= [3,2]", source)
                self.assertLess(source.index("p(-4,6) = 741"), source.index("t(2,10) /= 741"))
                self.assertLess(source.index("t(3,11) = 852"), source.index("p(-3,7) /= 852"))
                self.assertIn("other(2,10) /= -700", source)
            elif spec["variant"] == "remap":
                self.assertIn("p(-1:0,4:6) => v", source)
                self.assertIn("lbound(p) /= [-1,4]", source)
                self.assertIn("ubound(p) /= [0,6]", source)
                self.assertIn("shape(p) /= [2,3]", source)
                self.assertLess(source.index("p(0,6) = 961"), source.index("v(2) /= 961"))
                self.assertLess(source.index("v(-1) = 862"), source.index("p(-1,5) /= 862"))
                self.assertIn("alt(2) /= -900", source)
            elif spec["variant"] == "procedure":
                self.assertIn("procedure(op), pointer :: pp", source)
                self.assertIn("pp => double_it", source)
                self.assertIn("pp(21) /= 42", source)

    def test_invalids_have_one_property_controls(self):
        for spec in self.specs.values():
            if spec["kind"] != "invalid":
                continue
            control = self.specs[spec["control"]]
            self.assertEqual(control["kind"], "valid")
            self.assertEqual(control["rule"], spec["rule"])
            source = spec["source"]
            repair = spec["repair"]
            self.assertIn(repair["expected"], source)
            repaired = source.replace(repair["expected"], repair["replacement"], 1)
            if spec["id"].endswith("C1018_too_few_bounds_specs"):
                self.assertIn("p(-4:,6:) => t", repaired)
                self.assertIn("integer, pointer :: p(:,:)", repaired)
            elif spec["id"].endswith("C1018_too_many_bounds_specs"):
                self.assertIn("p(-4:) => t", repaired)
                self.assertIn("integer, pointer :: p(:)", repaired)
            elif spec["id"].endswith("C1019_too_few_bounds_remappings"):
                self.assertIn("p(-1:0,4:6) => v", repaired)
                self.assertIn("integer, pointer :: p(:,:)", repaired)
            elif spec["id"].endswith("C1019_too_many_bounds_remappings"):
                self.assertIn("p(-1:4) => v", repaired)
                self.assertIn("integer, pointer :: p(:)", repaired)
            else:
                self.assertEqual(repaired, control["source"])

    def test_mutation_spans_bind_complete_parent_and_feature_mutations_are_load_bearing(self):
        runtime = [spec for spec in self.specs.values() if spec["phase"] == "run"]
        self.assertEqual(sum(len(generated.all_mutations(spec)) for spec in runtime), 32)
        feature_ids = {mutation["id"] for spec in runtime for mutation in generated.all_mutations(spec)
                       if mutation["kind"] == "feature"}
        self.assertTrue({"remove-bounds-spec-list", "change-remap-shape",
                         "shift-remap-lower-bound", "swap-target"} <= feature_ids)
        self.assertNotIn("remove-remap-list", feature_ids)
        for spec in runtime:
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertTrue(any(mutation["kind"] == "feature" for mutation in generated.all_mutations(spec)))
            for mutation in generated.all_mutations(spec):
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                if mutation["id"] == "shift-remap-lower-bound":
                    self.assertIn(b"p(0:1,4:6) => v", mutant)
                    self.assertNotIn(b"p => v", mutant)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, generated.all_mutations(spec)[0])

    def test_catalogue_sync_removes_only_selected_facets_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Twenty selected facets of 10.2.2.2", view)
        self.assertIn("remain pending", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
