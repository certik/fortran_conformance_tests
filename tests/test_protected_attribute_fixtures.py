"""Fixture packet tests for Fortran 2023 8.5.15 PROTECTED attribute."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, render_requirement, validate_case_requirement

import generate_protected_attribute_fixtures as generated


class ProtectedAttributeFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_owned_cases_and_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 27)
        self.assertEqual(len(self.files), 54)
        self.assertEqual(sum(len(v) for v in generated.SELECTED.values()), 19)
        covered = {}
        for case in self.cases.values():
            covered.setdefault(case.rule, set()).update(case.meta.facets)
            validate_case_requirement(case, self.registry.requirements[case.rule])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual((case.fixture.build[0].source, case.fixture.build[0].language, case.fixture.build[0].form),
                             ("source.f90", "fortran", "free"))
        self.assertEqual(covered, {rule: set(facets) for rule, facets in generated.SELECTED.items()})

    def test_valid_and_invalid_fixture_contracts(self):
        for name, spec in self.specs.items():
            case = self.cases[name]
            if spec["kind"] == "valid":
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome),
                                 ("run", "success"))
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
                self.assertEqual(case.fixture.expectation.stderr, [""])
                expected_cohort = "runtime-effect" if spec["evidence"] == "effect" else "positive-control"
                self.assertEqual(self.members[name]["cohort"], expected_cohort)
            else:
                self.assertEqual(case.kind, "invalid")
                self.assertEqual(case.fixture.link, None)
                self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step,
                                  case.fixture.expectation.outcome), ("compile", "source", "diagnose"))
                diagnostic = case.fixture.expectation.diagnostic
                self.assertEqual(diagnostic["file"], "source.f90")
                self.assertEqual(diagnostic["line"], diagnostic["end_line"])
                self.assertEqual(diagnostic["excludes_any"], list(generated.EXCLUSIONS))
                self.assertEqual(self.members[name]["cohort"], "diagnostic-only")

    def test_negatives_have_one_property_repairs(self):
        for spec in self.specs.values():
            if spec["kind"] != "invalid":
                continue
            control = self.specs[spec["control_id"]]
            self.assertEqual(spec["repair"]["control_id"], control["id"])
            self.assertEqual(spec["repair"]["control_sha256"], control["source_sha256"])
            if spec["rule"] in {"C856", "C859", "C860"}:
                self.assertEqual(spec["source"].replace(", protected", "", 1), control["source"])
            elif spec["rule"] == "C857":
                repaired = spec["source"].replace("integer, parameter, protected :: c = 5",
                                                  "integer, protected :: c = 5", 1)
                self.assertEqual(repaired, control["source"])
            else:
                self.fail(f"unexpected invalid rule {spec['rule']}")

    def test_sources_are_ascii_and_oracles_use_nondefault_values(self):
        required = {
            "S8_5_15_001_valid__protected_attribute_module_setter_control": [
                "integer, protected :: x = -11", "call set_x(17)", "x /= 29",
            ],
            "S8_5_15_002_valid__protected_attribute_target_definition_control": [
                "integer, target :: storage = -9", "data_ptr = 23", "storage /= 23",
            ],
            "C859_valid__protected_attribute_readonly_use": [
                "use protected_attribute_readonly_m, only: x, y => z", "observed /= 54", "intent(in)",
            ],
            "C860_valid__protected_attribute_pointer_query_control": [
                "associated(data_ptr, store)", "associated(proc)", "proc(21) /= 42",
            ],
        }
        for name, spec in self.specs.items():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec["kind"] == "valid":
                self.assertIn("write(*,'(a)')", source)
                self.assertNotRegex(source, r"(?i)\b(error stop 0| = 0\n|observed\s*=\s*0)\b")
        for name, needles in required.items():
            source = self.specs[name]["source"]
            for needle in needles:
                self.assertIn(needle, source)

    def test_mutation_definitions_are_load_bearing_and_conforming(self):
        total = sum(len(spec["mutations"]) for spec in self.specs.values())
        self.assertEqual(total, 17)
        mutated = 0
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            for mutation in spec["mutations"]:
                self.assertTrue(mutation.get("conforming"))
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                text = spec["source"]
                for expected, replacement in mutation["replacements"]:
                    self.assertEqual(text.count(expected), 1)
                    text = text.replace(expected, replacement, 1)
                self.assertEqual(text.encode("ascii"), mutant)
                mutated += 1
        self.assertEqual(mutated, total)

    def test_catalogue_sync_removes_only_selected_pending_facets_and_renders_summary(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("Twenty-seven fixtures cover nineteen selected facets", view)
        for row in synced["requirements"]:
            self.assertIn(render_requirement(row), view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)


if __name__ == "__main__":
    unittest.main()
