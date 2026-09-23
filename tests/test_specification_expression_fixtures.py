"""Specification-expression fixtures, catalogue binding and feature mutations."""
import copy
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement
import generate_specification_expression_fixtures as generated

EXPECTED_RULE_FACETS = generated.SELECTED
EXPECTED_CASES = {
    "p1_contexts": ("S10.1.11-001", {"constant-expression-default", "subprogram-specification-part-exception"}, "positive-control"),
    "r1029_scalar": ("R1029", {"scalar-int-expression-form"}, "positive-control"),
    "c1011_intrinsic_dummy": ("C1011", {"intrinsic-operation", "constant-primary", "dummy-designator-primary", "parenthesized-restricted-expression"}, "positive-control"),
    "c1011_common": ("C1011", {"common-designator-primary"}, "positive-control"),
    "c1011_host_use": ("C1011", {"host-use-designator-primary"}, "positive-control"),
    "c1011_inquiries": ("C1011", {"specification-inquiry-restricted-argument", "specification-inquiry-variable-argument"}, "positive-control"),
    "c1011_constant_inquiry": ("C1011", {"constant-specification-inquiry-primary"}, "positive-control"),
    "c1011_standard_intrinsic": ("C1011", {"standard-intrinsic-primary"}, "positive-control"),
    "c1011_spec_function": ("C1011", {"specification-function-primary"}, "positive-control"),
    "c1011_subscripts_typeparams": ("C1011", {"restricted-subscripts-and-type-params"}, "positive-control"),
    "p3_intrinsic_inquiry": ("S10.1.11-002", {"intrinsic-inquiry-excluding-present"}, "effect"),
    "p4_spec_function": ("S10.1.11-003", {"pure-function", "nonstandard-intrinsic", "no-dummy-procedure-argument"}, "effect"),
    "p6_association_typing": ("S10.1.11-005", {"host-use-associated-typing"}, "positive-control"),
}


class SpecificationExpressionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_thirteen_owned_cases_and_twenty_facets(self):
        self.assertEqual(set(self.specs), {generated.identifier(name) for name in EXPECTED_CASES})
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.files), 26)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 20)
        covered = {}
        for variant, (rule, facets, evidence) in EXPECTED_CASES.items():
            name = generated.identifier(variant)
            case = self.cases[name]
            self.assertEqual(case.rule, rule)
            self.assertEqual(set(case.meta.facets), facets)
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", evidence, "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertFalse(case.meta.reference_warnings)
            validate_case_requirement(case, self.registry.requirements[rule], numbered=(rule == "R1029"))
            covered.setdefault(rule, set()).update(facets)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual((case.fixture.build[0].language, case.fixture.build[0].form), ("fortran", "free"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                              case.fixture.expectation.exit_code), ("run", "success", 0))
            self.assertEqual(case.fixture.expectation.stdout, [self.specs[name]["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
        self.assertEqual(covered, {rule: set(facets) for rule, facets in EXPECTED_RULE_FACETS.items()})

    def test_sources_are_distinguished_runtime_observations_not_duplicate_diagnostics(self):
        for name, spec in self.specs.items():
            source = spec["source"]
            source.encode("ascii")
            self.assertTrue(source.endswith("\n"))
            self.assertEqual(source.count(spec["completion"].rstrip("\n")), 1)
            self.assertIn("write(*,'(a)')", source)
            self.assertNotIn("present(", source.lower())
            self.assertNotRegex(source.lower(), r"\b(optional|intent\s*\(\s*out\s*\)|allocatable|pointer|coarray)\b")
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if "observe(" in source:
                self.assertGreaterEqual(source.count("call observe("), 2, msg=name)
        common = self.specs[generated.identifier("c1011_common")]["source"].lower()
        self.assertEqual(common.count("common /specblk/ n_common"), 2)
        subscript = self.specs[generated.identifier("c1011_subscripts_typeparams")]["source"]
        self.assertIn("character(len=n) :: word", subscript)
        self.assertIn("table(n-1)+len(text(1:n))", subscript)

    def test_every_fixture_has_remove_feature_and_load_bearing_mutants(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 26)
        for spec in self.specs.values():
            self.assertEqual(len(spec["mutations"]), 2)
            self.assertTrue(spec["mutations"][0]["id"].startswith("remove-"))
            for mutation in spec["mutations"]:
                mutant = mutation["source"]
                self.assertNotEqual(mutant, spec["source"])
                self.assertIn(spec["completion"].rstrip("\n"), mutant)
                self.assertEqual(mutant.count("\n"), spec["source"].count("\n"))
                for old, new in mutation["replacements"]:
                    self.assertIn(new, mutant)
                    self.assertNotIn(old, mutant)
                self.assertTrue(any("integer :: a(1)" in new or "character(len=1)" in new or "integer :: a(n)" in new
                                    for _, new in mutation["replacements"])
                                or mutation["id"].startswith(("changed-", "sibling-")))

    def test_synced_catalogue_removes_only_selected_pending_facets_and_renders(self):
        original = self.registry.catalogues[generated.SECTION]
        updated = generated.synced_catalogue(original)
        self.assertEqual(generated.synced_catalogue(updated), updated)
        for rule, facets in EXPECTED_RULE_FACETS.items():
            before = next(row for row in original["requirements"] if row["id"] == rule)
            after = next(row for row in updated["requirements"] if row["id"] == rule)
            self.assertFalse(set(facets) & set(after["pending"]))
            self.assertEqual(set(before["pending"]) - set(facets), set(after["pending"]))
            self.assertIn(generated.ORACLE_PREFIXES[rule], after["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], after["oracle_limitation"])
        for row in updated["requirements"]:
            if row["id"] not in EXPECTED_RULE_FACETS:
                before = next(item for item in original["requirements"] if item["id"] == row["id"])
                self.assertEqual(row, before)
        rendered = generated.render_view(updated)
        for row in updated["requirements"]:
            self.assertIn(render_requirement(row), rendered)
        self.assertEqual(rendered, (ROOT / generated.VIEW).read_text())

    def test_generation_check_mode_is_byte_identical(self):
        generated.generate(ROOT, check=True)
        for path, raw in self.files.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_bytes(), raw)
        actual = {path for path in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))

    def test_mutation_checker_uses_project_local_workspace_and_compiler_standards(self):
        self.assertFalse((ROOT / generated.BUILD_ROOT).exists())
        gnu = generated.compiler_command("/tool/gfortran", "f2023", Path("source.f90"), Path("program"))
        lfortran = generated.compiler_command("/tool/lfortran", "f23", Path("source.f90"), Path("program"))
        self.assertEqual(gnu[:2], ["/tool/gfortran", "-std=f2023"])
        self.assertEqual(lfortran[:2], ["/tool/lfortran", "--std=f23"])
        for spec in self.specs.values():
            for mutation in spec["mutations"]:
                self.assertNotIn("/tmp", mutation["source"])

    def test_mutation_check_compiles_in_per_case_cwd_and_preserves_git_status(self):
        spec = dict(variant="unit", source="program p\nend program p\n", completion="OK\n",
                    mutations=[dict(id="remove-feature", source="program p\nerror stop\nend program p\n")])
        compile_cwds, status_snapshots = [], []

        def fake_run(command, **kwargs):
            if command[:3] == ["git", "--no-pager", "status"]:
                self.assertEqual(Path(kwargs["cwd"]), ROOT)
                status_snapshots.append(kwargs["cwd"])
                return SimpleNamespace(returncode=0, stdout=" M tools/example.py\n", stderr="")
            if command[0] == "/tool/gfortran":
                self.assertEqual(command[1:4], ["-std=f2023", "source.f90", "-o"])
                compile_cwds.append(Path(kwargs["cwd"]).relative_to(ROOT).as_posix())
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            cwd = Path(kwargs["cwd"]).relative_to(ROOT).as_posix()
            return SimpleNamespace(returncode=0 if cwd.endswith("/parent") else 1,
                                   stdout="OK\n" if cwd.endswith("/parent") else "guard\n", stderr="")

        with patch.object(generated, "source_specs", return_value={"unit": spec}), \
                patch.object(generated.subprocess, "run", side_effect=fake_run):
            self.assertEqual(generated.mutation_check(ROOT, "/tool/gfortran", "f2023"), 1)
        self.assertEqual(len(status_snapshots), 2)
        self.assertEqual(compile_cwds, [
            f"{generated.BUILD_ROOT}/gfortran_f2023/unit/parent",
            f"{generated.BUILD_ROOT}/gfortran_f2023/unit/remove-feature",
        ])
        self.assertFalse((ROOT / generated.BUILD_ROOT).exists())

    def test_catalogue_update_preserves_raw_review_lifecycle(self):
        registry = Registry(ROOT)
        original = copy.deepcopy(registry.catalogues[generated.SECTION])
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original)
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory lifecycle only."
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint(generated.SECTION)
            registry.catalogues[generated.SECTION] = candidate
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            synced = generated.synced_catalogue(candidate)
            registry.catalogues[generated.SECTION] = synced
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)


if __name__ == "__main__":
    unittest.main()
