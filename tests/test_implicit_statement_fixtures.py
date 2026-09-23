"""Fixture metadata for Fortran 2023 8.7 IMPLICIT statements."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import generate_implicit_statement_fixtures as generated
import run_tests as runner
from suite_data import Registry, validate_case_requirement


class ImplicitStatementFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_cases_and_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 14)
        self.assertEqual(len(self.files), 28)
        covered = {}
        for case in self.cases.values():
            covered.setdefault(case.rule, set()).update(case.meta.facets)
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            validate_case_requirement(case, self.registry.requirements[case.rule],
                                      case.rule in self.registry.numbered)
        self.assertEqual(covered, {rule: set(facets) for rule, facets in generated.SELECTED.items()})

    def test_runtime_sources_use_generic_resolution_and_feature_mutations(self):
        runtime = [spec for spec in self.specs.values() if spec["manifest"]["expect"]["phase"] == "run"]
        self.assertEqual(len(runtime), 6)
        self.assertEqual(sum(len(spec["mutations"]) for spec in runtime), 12)
        for spec in runtime:
            source = spec["source"]
            self.assertEqual(generated.sha(source.encode("ascii")), spec["source_sha256"])
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertIn("interface classify", source)
            self.assertIn("procedure classify_integer", source)
            self.assertIn("procedure classify_real", source)
            self.assertIn("classify(", source)
            self.assertNotRegex(source, r"(?i)\bkind\s*\(|selected_|transfer|storage_size|same_type_as")
            self.assertEqual(spec["manifest"]["expect"]["stdout"], spec["completion"])
            for item in spec["mutations"]:
                start, end = item["span"]
                raw = source.encode("ascii")
                self.assertEqual(raw[start:end].decode("ascii"), item["expected"])
                mutant = generated.apply_mutation(spec, item)
                self.assertNotEqual(mutant, raw)
                self.assertIn(item["replacement"].encode("ascii"), mutant)
        default = self.specs["S8_7_002_valid__implicit_statement_default_integer_real_generic"]
        self.assertEqual({row["id"] for row in default["mutations"]},
                         {"change_integer_name_to_default_real", "change_real_name_to_default_integer"})
        for spec in runtime:
            if spec is not default:
                self.assertTrue(any(row["id"].startswith("remove_") for row in spec["mutations"]))

    def test_invalid_cases_are_numbered_line_anchored_diagnostics_with_controls(self):
        invalid = {name: case for name, case in self.cases.items() if case.kind == "invalid"}
        self.assertEqual(set(invalid), {
            "C897_invalid__implicit_statement_plain_none_plus_map",
            "C899_invalid__implicit_statement_missing_external_attribute_subroutine",
        })
        c897 = invalid["C897_invalid__implicit_statement_plain_none_plus_map"].fixture.expectation.diagnostic
        self.assertEqual((c897["file"], c897["line"], c897["end_line"]), ("source.f90", 2, 2))
        self.assertEqual(c897["additional_spans"], [{"line": 3}])
        self.assertEqual(c897["contains_any"], ["No other implicit statement", "following an IMPLICIT NONE"])
        c899 = invalid["C899_invalid__implicit_statement_missing_external_attribute_subroutine"].fixture.expectation.diagnostic
        self.assertEqual((c899["file"], c899["line"], c899["end_line"]), ("source.f90", 3, 3))
        self.assertEqual(c899["contains_any"], ["explicitly declared"])
        for diagnostic in (c897, c899):
            self.assertEqual(diagnostic["excludes_any"], generated.EXCLUSIONS)
        for control in (
            "C897_valid__implicit_statement_plain_none_no_other_map_control",
            "C899_valid__implicit_statement_explicit_external_subroutine_control",
        ):
            self.assertEqual(self.cases[control].meta.evidence, "positive-control")
            self.assertEqual(self.cases[control].fixture.expectation.outcome, "success")

    def test_compile_controls_pin_none_forms_and_external_only_branch(self):
        anchors = {
            "R866_valid__implicit_statement_empty_parentheses_none_control": "implicit none()",
            "R866_valid__implicit_statement_type_only_none_control": "implicit none(type)",
            "R869_valid__implicit_statement_type_keyword_control": "implicit none(type)",
            "C897_valid__implicit_statement_external_only_coexistence_control": "implicit none(external)",
            "C899_valid__implicit_statement_explicit_external_subroutine_control": "external ping",
        }
        for name, needle in anchors.items():
            case = self.cases[name]
            source = (case.fixture.root / "source.f90").read_text()
            self.assertIn(needle, source.lower())
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertEqual(case.fixture.expectation.outcome, "success")

    def test_catalogue_sync_removes_only_selected_pending_facets(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertIn("character-length-and-kind", by_rule["R867"].get("pending", {}))
        self.assertIn("NONE-before-PARAMETER", by_rule["C895"].get("pending", {}))
        self.assertIn("repeated-TYPE", by_rule["C896"].get("pending", {}))
        self.assertIn("descending-range-exclusion", by_rule["C898"].get("pending", {}))
        self.assertIn("duplicate-single-letter", by_rule["S8.7-001"].get("pending", {}))
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        view = generated.render_view(catalogue)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Fourteen complete fixtures", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
