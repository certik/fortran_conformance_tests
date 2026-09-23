"""ALLOCATE statement form fixtures, diagnostics, one-property controls, and catalogue sync."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry
import generate_allocate_statement_fixtures as generated


class AllocateStatementFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_cases_and_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 44)
        self.assertEqual(len(self.cases), 22)
        covered = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertEqual(covered, generated.SELECTED_FACETS)
        invalid = [case for case in self.cases.values() if case.kind == "invalid"]
        controls = [case for case in self.cases.values() if case.meta.evidence == "positive-control"]
        self.assertEqual(len(invalid), 6)
        self.assertEqual(len(controls), 6)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
            self.assertEqual(self.members[case.name]["cohort"],
                             "diagnostic-only" if case.kind == "invalid"
                             else "positive-control" if case.meta.evidence == "positive-control"
                             else "runtime-effect")

    def test_runtime_positive_sources_have_portable_oracles_and_feature_mutations(self):
        required = {
            "creation": ["allocate(x)", "allocated(x)", "allocate(ptr)", "associated(ptr)", "x /= 17", "ptr /= 23"],
            "r929_forms": ["allocate(x)", "allocate(character(len=5) :: c)", "len(c) /= 5", "c /= 'abcde'"],
            "r930_options": ["source=source_value", "stat=s", "errmsg=msg", "allocated(x)", "x /= 37",
                             "s /= 0", "msg /= 'UNCHANGED'"],
            "r931_errmsg": ["source=source_value", "stat=s", "errmsg=msg", "allocated(x)", "x /= 37",
                            "len(msg) /= 9"],
            "r933_scalar": ["allocate(x)", "allocated(x)", "x /= 41"],
            "r934_variable": ["allocate(x)", "allocated(x)", "x /= 41"],
            "c936_targets": ["allocate(x)", "allocated(x)", "allocate(ptr)", "associated(ptr)"],
            "c937_deferred": ["allocate(character(len=5) :: c)", "len(c) /= 5", "c /= 'vwxyz'"],
            "c944_scalar_no_shape": ["allocate(x)", "allocated(x)", "x /= 41"],
            "c949_type_no_source": ["allocate(character(len=5) :: c)", "len(c) /= 5", "c /= 'vwxyz'"],
        }
        for spec in self.specs.values():
            if spec["kind"] != "valid" or spec["evidence"] != "effect":
                continue
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertIn("checks=0", source)
            self.assertIn(spec["completion"].rstrip("\n"), source)
            self.assertGreaterEqual(len(spec["mutations"]), 1)
            for needle in required[spec["variant"]]:
                self.assertIn(needle, source)
            self.assertNotRegex(source, r"(?i)\b(transfer|loc|c_loc|equivalence|common)\s*\(")
            if "errmsg=msg" in source:
                self.assertIn("msg='UNCHANGED'", source)
                self.assertIn("len(msg) /= 9", source)
                self.assertIn("msg /= 'UNCHANGED'", source)

    def test_diagnostics_are_line_anchored_and_controls_are_one_property_repairs(self):
        for name, spec in self.specs.items():
            manifest = spec["manifest"]
            if spec["kind"] == "invalid":
                expect = manifest["expect"]
                self.assertEqual((expect["phase"], expect["step"], expect["outcome"]),
                                 ("compile", "source", "diagnose"))
                diag = expect["diagnostic"]
                self.assertEqual((diag["file"], diag["line"], diag["end_line"]),
                                 ("source.f90", spec["diagnostic_line"], spec["diagnostic_line"]))
                self.assertEqual(diag["contains_any"], spec["messages"])
                for text in ("not implemented", "unsupported", "internal error", "asr", "verifier"):
                    self.assertIn(text, [value.lower() for value in diag["excludes_any"]])
                self.assertNotIn("equals_any", diag)
                self.assertNotIn("allow_nonfatal", diag)
            elif spec["evidence"] == "positive-control":
                self.assertEqual(manifest["expect"], dict(phase="compile", step="source", outcome="success"))
        for variant in generated.DIAGNOSTICS:
            bad = self.specs[generated.case_id(generated.DIAGNOSTICS[variant]["rule"], "invalid", variant)]
            good = self.specs[bad["repair"]["control_id"]]
            bad_lines = bad["source"].splitlines()
            good_lines = good["source"].splitlines()
            self.assertEqual(len(bad_lines), len(good_lines))
            changed = [i + 1 for i, (left, right) in enumerate(zip(bad_lines, good_lines)) if left != right]
            self.assertEqual(changed, [bad["diagnostic_line"] if variant != "c936_ordinary_variable" else 3])
            self.assertEqual(bad["repair"]["control_sha256"], generated.sha(good["source"].encode("ascii")))

    def test_mutation_spans_bind_complete_parent(self):
        mutation_count = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            for mutation in generated.all_mutations(spec):
                mutation_count += 1
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                self.assertEqual(generated.mutated_source(spec, mutation),
                                 raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutation["expected"], mutation["replacement"])
        self.assertEqual(mutation_count, 21)

    def test_catalogue_sync_removes_only_selected_facets_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        untouched_pending = {
            "R930": {"mold-option", "unknown-option-rejected"},
            "C943": {"shape-spec-list-for-array", "upper-bounds-expr-for-array", "same-rank-source-alternative"},
            "C936": {"ordinary-variable-rejected"} - {"ordinary-variable-rejected"},
        }
        self.assertEqual({"mold-option", "unknown-option-rejected"}, set(by_rule["R930"].get("pending", {})))
        for facet in ("shape-spec-list-for-array", "upper-bounds-expr-for-array", "same-rank-source-alternative"):
            self.assertIn(facet, by_rule["C943"].get("pending", {}))
        self.assertIn("scalar-shape-spec-rejected", by_rule["C944"].get("pending", {}))
        self.assertIn("violates both C944", by_rule["C944"]["pending"]["scalar-shape-spec-rejected"])
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Six required diagnostic negatives", view)
        self.assertIn("every such negative also violates numbered C946", view)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
