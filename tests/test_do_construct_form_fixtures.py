"""DO construct form fixture packet checks for Fortran 2023 11.1.7.2."""

import copy
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_do_construct_form_fixtures as generated


class DoConstructFormFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_twenty_owned_cases_and_facets(self):
        self.assertEqual(set(self.cases), {spec["id"] for spec in self.specs.values()})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 40)
        self.assertEqual(sum(len(v) for v in generated.FACETS_BY_RULE.values()), 20)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             (spec["kind"], spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(generated.FACETS_BY_RULE[case.rule].count(spec["facets"][0]), 1)
            header = spec["source"].splitlines()[:2]
            self.assertEqual(header, [f"! rule: {case.rule}", f"! covers: {case.meta.facets[0]}"])
            self.assertEqual(header, [f"! rule: {spec['manifest']['rule']}",
                                      f"! covers: {spec['manifest']['facets'][0]}"])
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            if case.kind == "valid":
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                                  case.fixture.expectation.exit_code), ("run", "success", 0))
                self.assertEqual(case.fixture.expectation.stdout, [spec["stdout"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                self.assertEqual(self.members[case.name]["cohort"], "positive-control")
            else:
                self.assertIsNone(case.fixture.link)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "diagnose"))
                self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only")
                diagnostic = case.fixture.expectation.diagnostic
                self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                                 ("source.f90", spec["diagnostic_line"], spec["diagnostic_line"]))
                self.assertEqual(diagnostic["contains_any"], spec["messages"])
                for exclusion in generated.EXCLUSIONS:
                    self.assertIn(exclusion, diagnostic["excludes_any"])

    def test_sources_are_complete_ascii_and_reach_only_selected_rules(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertNotIn("C1121", source)
            self.assertNotIn("R1123", source)
            if spec["kind"] == "valid":
                self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
                self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
                self.assertIn("trace = -777", source)
                self.assertIn("write(*,'(a)') '" + spec["stdout"].strip() + "'", source)
                self.assertIn("error stop", source)
        for variant in ("label_statement", "unnamed_label", "label_with_loop_control", "continue_end"):
            source = self.specs[generated.identifier(variant)]["source"]
            self.assertIn("after_label_count = after_label_count + 1", source)
            self.assertIn("after_label_count /= 1", source)
        for variant in ("nonlabel_without_loop_control",):
            source = self.specs[generated.identifier(variant)]["source"]
            self.assertIn("if (n == 3) exit", source)
            self.assertNotRegex(source, r"do i =")
        for variant in ("concurrent_header_without_type", "concurrent_header_with_type",
                        "concurrent_default_step", "concurrent_explicit_step",
                        "concurrent_step_expression", "single_locality", "default_none"):
            source = self.specs[generated.identifier(variant)]["source"]
            self.assertIn("do concurrent", source)
            self.assertNotIn("print *", source.lower())
            self.assertNotRegex(source, r"(?i)\b(coarray|sync|image_index|num_images)\b")

    def test_invalid_repairs_are_one_property_and_match_their_controls(self):
        for variant in ("named_missing_end_name", "unnamed_end_name"):
            spec = self.specs[generated.identifier(variant)]
            control = self.specs[spec["control_id"]]
            repair = spec["repair"]
            self.assertEqual(spec["source"].splitlines()[repair["line"] - 1].strip(), repair["expected"])
            repaired_lines = spec["source"].replace(repair["expected"], repair["replacement"], 1).splitlines()
            control_lines = control["source"].splitlines()
            repaired_lines[:2] = control_lines[:2]
            self.assertEqual("\n".join(repaired_lines) + "\n", control["source"])
            self.assertNotEqual(spec["source"], control["source"])
            diff_lines = {line for line, (a, b) in enumerate(zip(spec["source"].splitlines(),
                                                                 control["source"].splitlines()), 1)
                          if a != b}
            self.assertLessEqual(diff_lines, {1, 2, repair["line"]})
            self.assertIn(2, diff_lines)
            self.assertIn(repair["line"], diff_lines)
            self.assertEqual(len(spec["source"].splitlines()), len(control_lines))

    def test_feature_mutations_are_load_bearing_and_not_oracle_only(self):
        total = 0
        for spec in self.specs.values():
            for mutation in spec.get("mutations", []):
                mutant = generated.mutate_source(spec, mutation)
                self.assertNotEqual(mutant, spec["source"])
                self.assertEqual(generated.sha(mutant.encode("ascii")), mutation["mutant_sha256"])
                self.assertIn(mutation["replacement"], mutant)
                self.assertNotIn(mutation["expected"], mutant)
                self.assertNotIn(spec["stdout"].strip() + " BAD", mutant)
                self.assertIn(spec["stdout"].strip(), mutant)
                self.assertTrue(any(token in mutation["id"] for token in
                                    ("bound", "upper", "label", "name", "step", "threshold", "type", "locality")))
                total += 1
        self.assertEqual(total, 18)

    def test_catalogue_sync_removes_only_selected_pending_facets_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertIn("concurrent-header-with-mask", by_rule["R1125"].get("pending", {}))
        self.assertIn("end-do-name-mismatch-rejected", by_rule["C1135"].get("pending", {}))
        self.assertNotIn("R1123", by_rule)
        self.assertNotIn("C1121", by_rule)
        unresolved = {row["unit"]: row["disposition"] for row in catalogue["accounting"]}
        self.assertEqual(unresolved["R1123"], "unresolved")
        self.assertEqual(unresolved["C1121"], "unresolved")
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Twenty facets are discharged", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)

    def test_case_requirement_validation_rejects_bad_facets(self):
        for case in self.cases.values():
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement, numbered=case.rule[0] in "RC")
            bad = copy.copy(case)
            bad.meta = copy.copy(case.meta)
            bad.meta.facets = ["foreign-facet"]
            with self.assertRaises(SuiteError):
                validate_case_requirement(bad, requirement, numbered=case.rule[0] in "RC")


if __name__ == "__main__":
    unittest.main()
