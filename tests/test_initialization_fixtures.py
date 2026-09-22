"""Runtime fixtures for Fortran 2023 initialization."""

import copy
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
import generate_initialization_fixtures as generated


class InitializationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_ten_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 20)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
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

    def test_sources_pin_headers_sentinels_bounds_and_character_lengths(self):
        anchors = {
            "scalar_integer_logical": ["integer :: i = -31417", "logical :: flag = .true.",
                                       "if (i /= -31417)", "if (.not. flag)"],
            "integer_kind_conversion": ["selected_int_kind(18)", "wide = -31417",
                                        "narrow = wide_source", "if (narrow /= 2719)"],
            "character_length_conversion": ["character(len=2) :: trunc = 'Zq7R'",
                                            "character(len=5) :: padded = 'Bx'", "if (len(trunc) /= 2)",
                                            "if (trunc(1:2) /= 'Zq')", "if (len(padded) /= 5)",
                                            "if (padded(3:3) /= ' ')", "if (padded(5:5) /= ' ')",],
            "scalar_array_expansion": ["integer :: a(-3:-1) = -24681", "integer :: b(5:6,-2:0) = 13579",
                                       "if (lbound(a,1) /= -3)", "if (ubound(b,2) /= 0)",
                                       "if (b(6,0) /= 13579)"],
            "array_values": ["integer :: v(4:6) = [2,3,5]", "if (lbound(v,1) /= 4)",
                             "if (v(4) /= 2)", "if (v(6) /= 5)"],
            "derived_explicit_override": ["integer :: component = -111", "type(sample) :: obj = sample(2719)",
                                          "if (obj%component /= 2719)"],
            "saved_scalar_target": ["target_value = -22231", "integer, pointer :: p => target_value",
                                    "associated(p, target_value)", "target_value = -22230",
                                    "if (p /= -22230)"],
            "subprogram_retention": ["integer :: kept = -31417", "call visit(first)", "call visit(second)",
                                     "if (first /= -31417)", "if (second /= -31416)"],
            "block_retention": ["block", "integer :: kept = -27182", "kept = -27181",
                                "if (first /= -27182)", "if (second /= -27181)"],
            "data_part_retention": ["integer :: a(-2:-1)", "data a(-2) /-12345/",
                                    "if (lbound(a,1) /= -2)", "a(-1) = 2468",
                                    "if (first_a /= -12345)", "if (second_b /= 2468)"],
        }
        forbidden_declaration_initializers = (
            r"(?im)^\s*(integer|real|logical|character|type\()\b[^\n]*(=\s*(0(\.0)?|\.false\.|''|\"\"))",
            r"(?im)^\s*data\b[^\n]*/\s*(0|\.false\.|''|\"\")\s*/",
        )
        for spec in self.specs.values():
            source = spec["source"]
            variant = spec["variant"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertGreaterEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^\s+error stop$", source)),
                             len([g for g in spec["guards"] if g["kind"] == "guard"]))
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            for pattern in forbidden_declaration_initializers:
                self.assertNotRegex(source, pattern)
            for sentinel in spec["sentinels"]:
                self.assertNotIn(sentinel.lower(), {"0", "0.0", ".false.", "''", '""', "' '"})
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|coarray|sync\s+all)\b")
            for needle in anchors[variant]:
                self.assertIn(needle, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 63)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 18)
        self.assertEqual(sum(len(spec["initializer_removals"]) for spec in self.specs.values()), 14)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            hashes = set()
            for probe in spec["probes"] + spec["input_mutations"] + spec["initializer_removals"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.mutated_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                if probe in spec["initializer_removals"]:
                    self.assertNotIn(probe["expected"].encode("ascii"), mutant)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, (spec["probes"] + spec["input_mutations"])[0])

    def test_initialization_removal_is_planned_for_every_fixture(self):
        for spec in self.specs.values():
            removals = spec["initializer_removals"]
            self.assertTrue(removals, spec["variant"])
            if spec["variant"] == "data_part_retention":
                self.assertEqual([row["expected"] for row in removals], ["    data a(-2) /-12345/\n"])
            elif spec["variant"] == "saved_scalar_target":
                self.assertEqual([row["expected"] for row in removals], [" => target_value"])
            else:
                self.assertTrue(any(" = " in row["expected"] for row in removals), spec["variant"])
            self.assertRegex(spec["ignored_initialization"].lower(), r"reject|fail")

    def test_catalogue_sync_removes_only_selected_pending_entries_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            self.assertEqual(set(by_rule[rule].get("pending", {})), generated.REMAINING_PENDING[rule])
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Ten complete run/effect/f2023 programs", view)
        self.assertIn("no fixture expects 0, 0.0, .FALSE. or a blank string", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
