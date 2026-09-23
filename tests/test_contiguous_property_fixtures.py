"""Runtime fixtures for standard-required CONTIGUOUS property inquiries."""
import copy
from dataclasses import asdict
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from execution_validation import validate_case_trace
from suite_data import Registry, render_requirement
import generate_contiguous_property_fixtures as generated

FAMILIES = (("gfortran", "f2023"), ("lfortran", "f23"))


class ContiguousPropertyFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if case.name in cls.specs}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_ten_cases_are_discovered_as_runtime_effects_for_selected_facets_only(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 10)
        by_rule = {generated.RULE_TRUE: set(generated.TRUE_FACETS), generated.RULE_FALSE: set(generated.FALSE_FACETS)}
        seen = {generated.RULE_TRUE: set(), generated.RULE_FALSE: set()}
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             (spec["rule"], "valid", "effect", "f2023"))
            self.assertEqual(case.meta.facets, [spec["facet"]])
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            seen[case.rule].add(spec["facet"])
        self.assertEqual(seen, by_rule)

    def test_sources_use_only_is_contiguous_bounds_shape_and_nonzero_literal_payloads(self):
        for spec in self.specs.values():
            source = spec["source"]
            self.assertNotRegex(source.lower(), r"\b(?:transfer|loc|c_loc|storage_size|equivalence|common|cpu_time)\b")
            self.assertNotIn(":: x(..)", source)
            self.assertNotIn("0) error stop 'CP:payload", source)
            self.assertNotRegex(source, r"=\s*0\s*(?:!|\n)")
            self.assertRegex(source, r"\bis_contiguous\(")
            self.assertRegex(source, r"\blbound\(|\bubound\(")
            self.assertRegex(source, r"\bshape\(")
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
        false_sources = "\n".join(self.specs[name]["source"] for name in self.specs
                                  if self.specs[name]["rule"] == generated.RULE_FALSE)
        self.assertGreaterEqual(false_sources.count(".false."), 2)
        self.assertGreaterEqual(false_sources.count(".true."), 2)

    def test_hand_derived_values_bounds_and_shapes_are_embedded_in_expected_literals(self):
        expected = {
            "attributed_pointer": {"-2", "2", "4", "6", "5", "3", "1493"},
            "whole_nonpointer": {"-2", "2", "4", "6", "5", "3", "0", "1614"},
            "assumed_shape": {"-2", "2", "4", "6", "5", "3", "1507"},
            "allocated_array": {"-3", "1", "7", "9", "5", "3", "0", "4", "6", "1786", "365"},
            "associated_pointer": {"-2", "2", "4", "6", "5", "3", "1614"},
            "gap_free_section": {"1", "5", "178", "222"},
            "full_leading_dimensions": {"1", "5", "2", "1514"},
            "full_character_substring": {"1", "3", "4"},
            "ordinary_gapped_section": {"1", "4", "5", "167", "233"},
            "multidimensional_interleaving": {"1", "2", "3", "1507", "1614"},
        }
        for spec in self.specs.values():
            literals = {guard["expected"] for guard in spec["guards"] if guard["expected"] not in (".true.", ".false.")}
            self.assertTrue(expected[spec["variant"]] <= literals, spec["variant"])

    def test_every_fixture_file_and_catalogue_rendering_is_exact_and_deterministic(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("contiguous_property_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        self.assertEqual(generated.synced_catalogue(self.registry.catalogues["8.5.7"]),
                         self.registry.catalogues["8.5.7"])
        self.assertEqual(generated.render_view(self.registry.catalogues["8.5.7"]),
                         (ROOT / generated.VIEW).read_text())
        check = subprocess.run([sys.executable, str(ROOT / "tools/generate_contiguous_property_fixtures.py"), "--check"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_only_selected_pending_facets_are_removed_and_review_state_is_not_asserted(self):
        catalogue = self.registry.catalogues["8.5.7"]
        for rule, facets in generated.FACETS_BY_RULE.items():
            requirement = self.registry.requirements[rule]
            self.assertTrue(set(facets) <= set(requirement["facets"]))
            self.assertTrue(set(facets).isdisjoint(requirement["pending"]))
        candidate = copy.deepcopy(catalogue)
        for row in candidate["requirements"]:
            if row["id"] not in generated.FACETS_BY_RULE:
                row["pending"] = {}
        before = copy.deepcopy(candidate)
        self.assertEqual(generated.synced_catalogue(candidate), before)
        text = generated.render_view(catalogue)
        self.assertIn("Source review:", text)
        self.assertNotIn("review_state ==", text)
        for row in catalogue["requirements"]:
            self.assertIn(render_requirement(row), text)

    def staged(self, case, family, mode, source_bytes=None, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic transport")
        raw = source_bytes if source_bytes is not None else (case.fixture.root / "source.f90").read_bytes()
        phases = []
        def transport(command, cwd, timeout, stdin=None):
            self.assertIsNone(stdin)
            workspace = Path(cwd).resolve()
            if (workspace / "source.f90").exists():
                self.assertEqual((workspace / "source.f90").read_bytes(), raw)
            phase = "compile" if "-c" in command else "link" if "-o" in command else "run"
            phases.append(phase)
            code, stdout, stderr, timed_out = 0, "", "", False
            if fault == phase + "-failure":
                code, stderr = 1, "synthetic failure"
            elif phase == "run":
                stdout = self.specs[case.name]["completion"]
                if fault == "wrong-output":
                    stdout = stdout.replace(" OK ", " BAD ")
                elif fault == "stderr":
                    stderr = "extra\n"
                elif fault == "timeout":
                    timed_out = True
            if phase != "run" and code == 0:
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact")
            return runner.ProcessResult(code, stdout + stderr, timed_out, stdout, stderr, stdout.encode(), stderr.encode())
        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        return check, phases

    def test_runner_executes_compile_link_run_and_rejects_native_failures_or_wrong_output(self):
        for case in self.cases.values():
            for family, mode in FAMILIES:
                with self.subTest(case=case.name, family=family, fault="none"):
                    check, phases = self.staged(case, family, mode)
                    self.assertEqual((check.outcome, check.phase), ("pass", "run"))
                    self.assertEqual(phases, ["compile", "link", "run"])
                for fault in ("compile-failure", "link-failure", "wrong-output", "stderr", "timeout"):
                    with self.subTest(case=case.name, family=family, fault=fault):
                        check, _ = self.staged(case, family, mode, fault=fault)
                        self.assertEqual(check.outcome, "fail")

    def test_feature_and_wrong_oracle_mutations_are_bound_to_complete_sources(self):
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            mutated = generated.feature_mutation_source(spec)
            start, end = spec["feature_span"]
            self.assertTrue(any(raw[start:end].decode("ascii") == guard["expression"] for guard in spec["guards"]))
            self.assertIn(spec["feature_replacement"].encode("ascii"), mutated)
            self.assertNotEqual(mutated, raw)
            self.assertEqual(raw.count(b"\n"), mutated.count(b"\n"))
            self.assertIn(spec["completion"].strip().encode("ascii"), mutated)
            for guard in spec["guards"]:
                changed = generated.wrong_oracle_source(spec, guard)
                g0, g1 = guard["span"]
                self.assertEqual(raw[g0:g1].decode("ascii"), guard["expected"])
                self.assertEqual(changed, raw[:g0] + guard["replacement"].encode("ascii") + raw[g1:])
                self.assertNotEqual(changed, raw)
                if guard["expected"] == ".false.":
                    self.assertEqual(guard["replacement"], ".true.")


if __name__ == "__main__":
    unittest.main()
