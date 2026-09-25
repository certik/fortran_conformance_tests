"""Batch319 attribute statement fixture packet checks."""
from dataclasses import asdict
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import generate_attribute_statements_8_6_a_fixtures as generated
import run_tests as runner
from execution_validation import validate_case_trace
from suite_data import Registry


class AttributeStatements86AFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if case.name in cls.specs}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_five_cases_are_discovered_with_owned_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        expected = {
            f"{generated.TOPIC}_accessibility_resolution": ("R831", {"generic-name-branch", "operator-generic-branch", "assignment-generic-branch"}, "effect", "run", "success", "runtime-effect"),
            f"{generated.TOPIC}_optional_presence": ("R853", {"presence-and-interface-source"}, "effect", "run", "success", "runtime-effect"),
            f"{generated.TOPIC}_parameter_definitions": ("S8.6.11-004", {"simple-derived-values"}, "effect", "run", "success", "runtime-effect"),
            f"{generated.TOPIC}_c873_duplicate_omitted_private": ("C873", {"one-no-list-default"}, "effect", "compile", "diagnose", "diagnostic-only"),
            f"{generated.TOPIC}_c873_single_omitted_private_control": ("C873", {"one-no-list-default"}, "positive-control", "compile", "success", "positive-control"),
        }
        for name, (rule, facets, evidence, phase, outcome, cohort) in expected.items():
            case = self.cases[name]
            self.assertEqual(case.rule, rule)
            self.assertEqual(set(case.meta.facets), facets)
            self.assertEqual(case.meta.evidence, evidence)
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), (phase, outcome))
            if phase == "run":
                self.assertEqual(case.fixture.expectation.stdout, ["ATTRIBUTE STATEMENTS 8.6.A OK\n"])
            self.assertEqual(self.members[name]["cohort"], cohort)

    def test_generated_files_catalogues_and_views_are_exact(self):
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        generated.check_files(ROOT)
        for section, rel in generated.CATALOGUES.items():
            current = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(section, current, self.specs), current)
            self.assertEqual(generated.render_view(section, current), (ROOT / generated.VIEWS[section]).read_text())

    def test_sources_use_direct_inquiries_and_no_forbidden_layout_oracles(self):
        for spec in self.specs.values():
            source = spec["source"].lower()
            self.assertNotRegex(source, r"\b(?:loc|c_loc|transfer|storage_size|equivalence|cpu_time)\b")
            self.assertLessEqual(max(map(len, spec["source"].splitlines())), 132)
        self.assertIn("present(with_colon)", self.specs[f"{generated.TOPIC}_optional_presence"]["source"])
        self.assertIn("shape(vector)", self.specs[f"{generated.TOPIC}_parameter_definitions"]["source"])
        self.assertIn("interface operator(+)", self.specs[f"{generated.TOPIC}_accessibility_resolution"]["source"])
        self.assertIn("private\nprivate", self.specs[f"{generated.TOPIC}_c873_duplicate_omitted_private"]["source"])

    def test_each_claimed_facet_has_a_mutation(self):
        for spec in self.specs.values():
            if spec.get("phase") == "compile":
                continue
            claimed = {facet for rules in spec["sections"].values() for facets in rules.values() for facet in facets}
            mutants = [m for m in spec["mutants"] if m["facet"] in claimed]
            self.assertEqual({m["facet"] for m in mutants}, claimed)
            for mutant in mutants:
                mutated = spec["source"]
                for change in mutant["changes"]:
                    self.assertEqual(mutated.count(change["old"]), 1, mutant["id"])
                    mutated = mutated.replace(change["old"], change["new"], 1)
                self.assertNotEqual(mutated, spec["source"])
                self.assertIn("ATTRIBUTE STATEMENTS 8.6.A OK", mutated)

    def test_c873_negative_has_one_property_compile_control(self):
        invalid = self.specs[f"{generated.TOPIC}_c873_duplicate_omitted_private"]
        control = self.specs[f"{generated.TOPIC}_c873_single_omitted_private_control"]
        self.assertEqual(invalid["source"].replace("private\n", "", 1), control["source"].replace("a861_c873_control", "a861_c873_invalid"))
        case = self.cases[invalid["id"]]
        self.assertEqual(case.fixture.expectation.diagnostic["line"], 4)
        self.assertEqual(case.fixture.expectation.diagnostic["end_line"], 4)
        self.assertIn("internal error", case.fixture.expectation.diagnostic["excludes_any"])

    def staged(self, case, fault=None):
        compiler = runner.Compiler("synthetic", "gfortran", "f2023", "synthetic")
        spec = self.specs[case.name]
        phases = []
        def transport(command, cwd, timeout, stdin=None):
            phase = "compile" if "-c" in command else "link" if "-o" in command else "run"
            phases.append(phase)
            if phase != "run" and fault == phase:
                return runner.ProcessResult(1, "synthetic failure", False, "", "synthetic failure")
            if phase != "run":
                Path(command[command.index("-o") + 1]).write_bytes(b"object")
                return runner.ProcessResult(0, "", False, "", "")
            stdout = "ATTRIBUTE STATEMENTS 8.6.A OK\n" if fault != "stdout" else "ATTRIBUTE STATEMENTS 8.6.A BAD\n"
            stderr = "" if fault != "stderr" else "extra\n"
            return runner.ProcessResult(0 if fault != "run" else 1, stdout + stderr, False, stdout, stderr)
        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        validate_case_trace(self.members[case.name], asdict(check), dict(compiler.configuration(), version="synthetic"), ROOT, None, False)
        return check, phases

    def test_runner_contract_requires_compile_link_run_and_exact_output(self):
        for case in self.cases.values():
            if case.fixture.expectation.phase != "run":
                continue
            check, phases = self.staged(case)
            self.assertEqual((check.outcome, phases), ("pass", ["compile", "link", "run"]))
            for fault in ("compile", "link", "run", "stdout", "stderr"):
                self.assertEqual(self.staged(case, fault)[0].outcome, "fail")


if __name__ == "__main__":
    unittest.main()
