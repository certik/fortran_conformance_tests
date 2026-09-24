"""Batch296 BIND(C), CONTIGUOUS and DIMENSION fixture packet checks."""
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import generate_attributes_8_5_5_8_5_8_1_fixtures as generated
import run_tests as runner
from execution_validation import validate_case_trace
from suite_data import Registry


class AttributeBatch296FixturesTests(unittest.TestCase):
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
            "C820_valid__attributes_bind_variable_interop": ("C820", set(generated.BIND_VAR_FACETS), True),
            "C821_valid__attributes_bind_common_interop": ("C821", set(generated.BIND_COMMON_FACETS), True),
            "R814_valid__attributes_dimension_grammar": ("R814", set(generated.DIM_R814_FACETS), False),
            "S8_5_8_1_001_valid__attributes_dimension_assumed_rank": ("S8.5.8.1-001", set(generated.DIM_EFFECT_FACETS), False),
            "S8_5_7_003_valid__attributes_contiguous_assumed_rank": ("S8.5.7-003", set(generated.CONTIG_FACETS), False),
        }
        for name, (rule, facets, has_c) in expected.items():
            case = self.cases[name]
            self.assertEqual(case.rule, rule)
            self.assertEqual(set(case.meta.facets), facets)
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(bool([s for s in case.fixture.build if s.language == "c"]), has_c)
            self.assertEqual(self.members[name]["cohort"], "runtime-effect")

    def test_generated_files_catalogues_and_views_are_exact(self):
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        generated.generate(check=True)
        self.assertEqual(generated.synced_catalogues({
            "8.5.5": self.registry.catalogues["8.5.5"],
            "8.5.7": self.registry.catalogues["8.5.7"],
            "8.5.8.1": self.registry.catalogues["8.5.8.1"],
        }), {
            "8.5.5": self.registry.catalogues["8.5.5"],
            "8.5.7": self.registry.catalogues["8.5.7"],
            "8.5.8.1": self.registry.catalogues["8.5.8.1"],
        })
        self.assertEqual(generated.render_bind_view(self.registry.catalogues["8.5.5"]), (ROOT / generated.BIND_VIEW).read_text())
        self.assertEqual(generated.render_contig_view(self.registry.catalogues["8.5.7"]), (ROOT / generated.CONTIG_VIEW).read_text())
        self.assertEqual(generated.render_dim_view(self.registry.catalogues["8.5.8.1"]), (ROOT / generated.DIM_VIEW).read_text())

    def test_sources_use_direct_inquiries_and_no_forbidden_layout_or_byte_oracles(self):
        for spec in self.specs.values():
            source = spec["source"].lower()
            self.assertNotRegex(source, r"\b(?:loc|c_loc|transfer|storage_size|equivalence|cpu_time)\b")
            self.assertLessEqual(max(map(len, spec["source"].splitlines())), 132)
        self.assertIn("rank(x)", self.specs["S8_5_8_1_001_valid__attributes_dimension_assumed_rank"]["source"])
        self.assertIn("shape(x", self.specs["S8_5_8_1_001_valid__attributes_dimension_assumed_rank"]["source"])
        self.assertIn("is_contiguous(x)", self.specs["S8_5_7_003_valid__attributes_contiguous_assumed_rank"]["source"])
        self.assertIn("extern int attr_bind_scalar", self.specs["C820_valid__attributes_bind_variable_interop"]["c_source"])
        self.assertIn("extern struct attr_pair attr_bind_common", self.specs["C821_valid__attributes_bind_common_interop"]["c_source"])

    def test_every_claimed_facet_has_a_distinct_feature_mutation(self):
        for spec in self.specs.values():
            mutations = generated.mutation_sources(spec)
            self.assertGreaterEqual(len(mutations), len(spec["facets"]))
            base = {"source.f90": spec["source"].encode("ascii")}
            if "c_source" in spec:
                base["companion.c"] = spec["c_source"].encode("ascii")
            for name, files in mutations.items():
                self.assertTrue(any(files[k] != base[k] for k in files), name)
                if "companion.c" in files and files["companion.c"] != base.get("companion.c"):
                    self.assertIn(b"shadow", files["companion.c"])
                self.assertIn(b" OK'", files["source.f90"])

    def staged(self, case, fault=None):
        compiler = runner.Compiler("synthetic", "gfortran", "f2023", "synthetic")
        spec = self.specs[case.name]
        expected_stdout = generated.COMPLETIONS[spec["variant"]]
        def transport(command, cwd, timeout, stdin=None):
            phase = "compile" if "-c" in command else "link" if "-o" in command else "run"
            if phase != "run" and fault == phase:
                return runner.ProcessResult(1, "synthetic failure", False, "", "synthetic failure")
            if phase != "run":
                Path(command[command.index("-o") + 1]).write_bytes(b"object")
                return runner.ProcessResult(0, "", False, "", "")
            stdout = expected_stdout if fault != "stdout" else expected_stdout.replace(" OK", " BAD")
            stderr = "" if fault != "stderr" else "extra\n"
            return runner.ProcessResult(0 if fault != "run" else 1, stdout + stderr, False, stdout, stderr)
        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, cc="cc", timeout=5)
        validate_case_trace(self.members[case.name], asdict(check), dict(compiler.configuration(), version="synthetic"), ROOT, dict(command="cc", version="synthetic"), False)
        return check

    def test_runner_contract_requires_successful_compile_link_run_and_exact_output(self):
        for case in self.cases.values():
            self.assertEqual(self.staged(case).outcome, "pass")
            for fault in ("compile", "link", "run", "stdout", "stderr"):
                self.assertEqual(self.staged(case, fault).outcome, "fail")


if __name__ == "__main__":
    unittest.main()
