"""Runtime fixtures for Fortran 2023 structure constructors."""

import json
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_structure_constructor_effect_fixtures as generated


class StructureConstructorEffectFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_fifteen_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 30)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for _, facet in generated.VARIANTS.values()})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(generated.VARIANTS[self.specs[case.name]["variant"]],
                             (case.rule, case.meta.facets[0]))
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expect.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence="positive-control")),
                                          self.registry.requirements[case.rule])

    def test_sources_pin_component_identity_defaults_and_feature_anchors(self):
        anchors = {
            "array_component_scalar": ["integer :: values(3)", "source(1)=11", "source(2)=13", "source(3)=17",
                                       "call observe(record(101, 103, values=source))", "obj%values(3) /= 17"],
            "keyword_order": ["integer :: left", "integer :: right", "right=13, left=11",
                              "obj%left /= 11", "obj%right /= 13"],
            "numeric_conversion": ["real :: source", "source=4.0", "value=source", "obj%value /= 4"],
            "scalar_array": ["integer :: values(-1:1)", "scalar=17", "values=scalar",
                             "lbound(obj%values,1) /= -1", "obj%values(0) /= 17"],
            "conforming_array": ["integer :: source(3)", "source(2)=13", "values=source",
                                 "obj%values(-1) /= 11", "obj%values(1) /= 17"],
            "omitted_defaults": ["integer :: left = 11", "integer :: right = 13", "record(101, 103)",
                                 "right=29", "obj%right /= 29"],
            "omitted_allocatables": ["integer, allocatable :: scalar", "integer, allocatable :: vector(:)",
                                     ".not. allocated(obj%scalar)", ".not. allocated(obj%vector)"],
            "live_data_target": ["integer, pointer :: p", "integer, target :: datum", "datum=17",
                                 "associated(obj%p, datum)", "obj%p /= 17"],
            "pointer_source_bounds": ["integer, pointer :: p(:)", "source(5:7) => target",
                                      "lbound(obj%p,1) /= 5", "obj%p(7) /= 17"],
            "known_disassociated_pointer": ["source => null()", ".not. associated(obj%p)"],
            "contextual_mold_null": ["p=null()", "q=null(mold=mold)", ".not. associated(obj%p)",
                                     ".not. associated(obj%q)"],
            "no_mold_null_allocatable": ["scalar=null(), vector=null()", ".not. allocated(obj%scalar)",
                                         ".not. allocated(obj%vector)"],
            "typed_mold_null_allocatable": ["vector=null(mold=mold)", ".not. allocated(obj%vector)"],
            "allocated_char_source": ["allocate(character(len=3) :: source)", "source='QRS'",
                                      "allocated(obj%text)", "len(obj%text) /= 3", "obj%text /= 'QRS'"],
            "ordinary_char_source": ["character(len=3) :: source", "source='LMN'", "allocated(obj%text)",
                                     "len(obj%text) /= 3", "obj%text /= 'LMN'"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            variant = spec["variant"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn("integer :: lead\n    integer :: swapped\n    integer :: stamp = -9051", source)
            self.assertIn("record(101, 103", source)
            self.assertIn("obj%lead /= 101", source)
            self.assertIn("obj%swapped /= 103", source)
            self.assertIn("obj%stamp /= -9051", source)
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|common|coarray|sync\s+all)\b")
            for sentinel in spec["sentinels"]:
                self.assertNotIn(sentinel.lower(), {"0", "0.0", ".false.", "''", '""', "' '"})
            for needle in anchors[variant]:
                self.assertIn(needle, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["oracle_mutations"]) for spec in self.specs.values()), 117)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 18)
        self.assertEqual(sum(len(spec["feature_mutations"]) for spec in self.specs.values()), 45)
        self.assertEqual(sum(len(spec["reverse_mutations"]) for spec in self.specs.values()), 15)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            hashes = set()
            for mutation in (spec["oracle_mutations"] + spec["input_mutations"]
                             + spec["feature_mutations"] + spec["reverse_mutations"]):
                for edit in mutation["edits"]:
                    start, end = edit["span"]
                    self.assertEqual(raw[start:end].decode("ascii"), edit["expected"])
                mutant = generated.mutated_source(spec, mutation)
                if mutation["group"] != "reverse":
                    self.assertNotIn(generated.sha(mutant), hashes)
                    hashes.add(generated.sha(mutant))
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["oracle_mutations"][0])

    def test_feature_level_mutations_are_mandatory_for_every_fixture(self):
        for spec in self.specs.values():
            feature_names = {row["mutation"] for row in spec["feature_mutations"]}
            self.assertEqual(feature_names, {"default-initialization-change", "component-definition-reorder",
                                             "component-value-swap"})
            self.assertEqual(len(spec["reverse_mutations"]), 1)
            reverse = spec["reverse_mutations"][0]
            self.assertEqual(reverse["mutation"], "default-initialization-reverse")
            self.assertEqual([edit["replacement"] for edit in reverse["edits"]],
                             ["integer :: stamp = -9052", "-9052"])

    def test_catalogue_sync_removes_only_selected_pending_entries_and_regenerates_view(self):
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
        self.assertIn("Fifteen complete run/effect/f2023 programs", view)
        self.assertIn("Character cases assert LEN explicitly", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
