"""Unnamed 7.6.1 ENUM syntax, constant consumers and R762 diagnostics."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement

import generate_enum_type_fixtures as generated
import generate_enum_value_fixtures as enum_value


class EnumTypeFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def test_exact_case_metadata_and_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.specs), 9)
        direct = {(rule, facet) for rule, facets in generated.SELECTED.items() for facet in facets}
        self.assertEqual(len(direct), 12)
        for spec in self.specs.values():
            case = self.cases[spec["id"]]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray)
            validate_case_requirement(case, self.registry.requirements[case.rule])
            if spec["kind"] == "invalid":
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("compile", "diagnose"))
                self.assertIsNone(case.fixture.link)
            elif spec["phase"] == "compile":
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("compile", "success"))
                self.assertIsNone(case.fixture.link)
            else:
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("run", "success"))
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])

    def test_generated_files_are_exact_ascii_and_prefix_isolated(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if path.is_file()
                  if not any(path.parent.name.startswith(prefix) for prefix in generated.EXTERNAL_PREFIXES)}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 18)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            self.assertTrue(raw.endswith(b"\n"))
            if path.name == "source.f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)
        generated.generate(ROOT, check=True)
        self.assertEqual(generated.build_corpus()[0], self.files)

    def test_sources_are_distinct_unnamed_7_6_1_enum_programs(self):
        run_specs = [spec for spec in self.specs.values() if spec["phase"] == "run"]
        self.assertEqual(len({spec["source_sha256"] for spec in run_specs}), len(run_specs))
        for spec in self.specs.values():
            source = spec["source"]
            self.assertIn("enum, bind(c)\n", source)
            self.assertNotIn("enumeration type", source.lower())
            self.assertNotRegex(source, r"(?i)enum,\s*bind\(c\)\s*::")
            self.assertNotRegex(source, r"(?im)^\s*type\s*\(")
            self.assertNotRegex(source, r"(?i)\b(?:c_int|selected_int_kind|transfer|storage_size|huge)\b")
        self.assertNotIn("previous_enum", json.dumps(self.specs))

    def test_r762_negative_has_one_property_control_and_ice_exclusions(self):
        invalid = self.specs[generated.invalid_id("R762", "nonconstant_initializer")]
        control = self.specs[invalid["control_id"]]
        self.assertEqual(invalid["rule"], "R762")
        self.assertEqual(invalid["facets"], ["constant-initializer"])
        self.assertEqual(invalid["source"].replace("integer :: seed = 4",
                                                   "integer, parameter :: seed = 4"),
                         control["source"])
        diagnostic = self.cases[invalid["id"]].fixture.expectation.diagnostic
        self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                         ("source.f90", 5, 5))
        self.assertEqual(diagnostic["contains_any"], [generated.DIAGNOSTIC_CAUSE])
        for needle in ("internal compiler error", "internal error", "AssertFailed", "traceback"):
            self.assertIn(needle, diagnostic["excludes_any"])

    def test_mutation_matrix_is_honest_and_source_specific(self):
        run_specs = [spec for spec in self.specs.values() if spec["phase"] == "run"]
        self.assertEqual(sum(len(spec["mutations"]) for spec in run_specs), 64)
        self.assertTrue(all(spec["feature_mutations"] for spec in run_specs))
        seen = set()
        for spec in run_specs:
            for mutation in spec["mutations"]:
                self.assertNotIn((spec["source_sha256"], mutation["id"]), seen)
                seen.add((spec["source_sha256"], mutation["id"]))
                if "span" in mutation:
                    start, end = mutation["span"]
                    self.assertEqual(spec["source"][start:end], mutation["expected"])
                    self.assertNotEqual(generated.wrong_source(spec, mutation).decode("ascii"), spec["source"])
        self.assertIn("remove-prior-constant-initializer",
                      {m["id"] for m in self.specs[generated.valid_id("R762", "constant_initializers")]
                       ["feature_mutations"]})

    def test_catalogue_sync_and_shared_pending_union_invariant(self):
        synced = generated.synced_catalogue(self.catalogue)
        self.assertEqual(synced, self.catalogue)
        by_rule = {row["id"]: row for row in self.catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            self.assertFalse(set(facets) & set(by_rule[rule].get("pending", {})))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertNotIn("constant-initializer", by_rule["R762"]["pending"])
        self.assertIn("constant-and-name-consumer-graph", by_rule["R762"]["pending"])
        broken = copy.deepcopy(self.catalogue)
        next(row for row in broken["requirements"] if row["id"] == "R760")["pending"].pop("named-bind-c")
        with self.assertRaisesRegex(ValueError, "shared pending partition mismatch"):
            generated.synced_catalogue(broken)
        with self.assertRaisesRegex(ValueError, "shared pending partition mismatch"):
            enum_value.synced_catalogue(broken, enum_value.build_corpus()[1])

    def test_view_renders_shared_generated_region_and_own_summary(self):
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue))
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("one compile-control/diagnostic pair checks the R762 nonconstant", view)
        self.assertIn("**Seven run fixtures, eleven compile controls and eleven diagnostic fixtures** represent **29 of64 facets**; "
                      "**35 remain pending**.", view)
        self.assertEqual(view.count("<!-- BEGIN GENERATED 7.6.1 -->"), 1)
        self.assertEqual(view.count("<!-- END GENERATED 7.6.1 -->"), 1)


if __name__ == "__main__":
    unittest.main()
