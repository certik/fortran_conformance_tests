"""Batch314 explicit-shape and assumed-shape array fixture metadata."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry

sys.path.insert(0, str(ROOT / "tools"))
import generate_array_shapes_8_5_8_2_8_5_8_3_fixtures as generated


class ArrayShapes858FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_cases_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 11)
        self.assertEqual(len(self.files), 22)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["stdout"]])
            self.assertEqual(expect.stderr, [""])

    def test_sources_are_direct_shape_bound_observers(self):
        required = {
            "explicit_r815_scalar_forms": ["integer :: upper_only(4)", "integer :: explicit_lower(-2:1)", "integer :: multi(2,0:2)", "rank(multi)"],
            "explicit_r816_lower_bound": ["integer :: a(-2:1)", "lbound(a) /= [-2]"],
            "explicit_r817_upper_bound": ["integer :: positive(3)", "integer :: zero(0:0)", "integer :: negative(-3:-1)"],
            "explicit_c831_contexts": ["integer :: module_a(module_n)", "integer :: main_a(main_n)", "integer :: local(n)", "integer :: b(n)"],
            "explicit_s001_list_rank": ["integer :: module_rank_two(2,3)", "integer :: main_rank_two(2,3)", "integer :: zero_extent(0,3)"],
            "assumed_r820_scalar_specs": ["integer, intent(in) :: x(:)", "integer, intent(in) :: x(-3:)"],
            "assumed_s001_list_rank": ["integer, intent(in) :: x(:,:)", "rank(x) /= 2"],
            "assumed_s002_scalar_lowers": ["integer, intent(in) :: x(:,:)", "integer, intent(in) :: x(0:,-3:)", "integer, intent(in) :: x(0:,:)"],
            "assumed_empty_inquiry": ["integer :: empty(5:3,-2:1)", "integer, intent(in) :: x(5:,-2:)", "lbound(x) /= [1,-2]", "ubound(x) /= [0,1]"],
            "assumed_s003_extent_relation": ["actual(-2:0,4:5)", "v(1:5:2)", "integer, intent(in) :: x(-5:,7:)", "x /= [11,13,15]"],
            "assumed_empty_extent": ["integer :: empty(5:3,-2:1)", "shape(x) /= [0,4]", "size(x) /= 0"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertTrue(source.endswith("\n"))
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertNotRegex(source, r"(?i)\b(?:allocatable|pointer|target|save|data|common|equivalence|transfer|c_loc|loc)\b")
            self.assertNotRegex(source, r"(?i)\b(?:reshape|spread|pack|merge)\s*\(")
            for needle in required[spec["slug"]]:
                self.assertIn(needle, source)
            if "empty" in spec["slug"]:
                self.assertNotRegex(source, r"empty\([^)]*\)\s*(?:=|/=)")
                self.assertNotIn("count(empty", source)

    def test_feature_mutations_are_bound_to_sources_and_facets(self):
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual({m["facet"] for m in spec["mutations"]}, set(spec["facets"]))
            for mutation in spec["mutations"]:
                changed = generated.mutated_source(spec, mutation)
                self.assertNotEqual(changed, raw)
                for rep in mutation["replacements"]:
                    start, end = rep["span"]
                    self.assertEqual(raw[start:end].decode("ascii"), rep["expected"])
                    self.assertIn(rep["replacement"].encode("ascii"), changed)
            broken = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "parent source"):
                generated.mutated_source(broken, spec["mutations"][0])

    def test_catalogues_remove_only_selected_pending_facets_and_preserve_other_owners(self):
        explicit = self.registry.catalogues[generated.EXPLICIT_SECTION]
        assumed = self.registry.catalogues[generated.ASSUMED_SECTION]
        self.assertEqual(generated.sync_catalogue(explicit, generated.EXPLICIT_SECTION), explicit)
        self.assertEqual(generated.sync_catalogue(assumed, generated.ASSUMED_SECTION), assumed)
        for section, catalogue in ((generated.EXPLICIT_SECTION, explicit), (generated.ASSUMED_SECTION, assumed)):
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.SELECTED[section].items():
                row = by_rule[rule]
                for facet in facets:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], row["oracle_limitation"])
        self.assertEqual(set({row["id"] for row in explicit["requirements"] if row["pending"]}),
                         {"R815", "R816", "R817", "R818", "R819", "C831", "C832", "C833", "S8.5.8.2-001", "S8.5.8.2-003", "S8.5.8.2-004", "S8.5.8.2-005"})
        self.assertEqual(set({row["id"] for row in assumed["requirements"] if row["pending"]}),
                         {"R820", "R821", "S8.5.8.3-001", "S8.5.8.3-002", "S8.5.8.3-003"})
        self.assertEqual(set(next(row for row in explicit["requirements"] if row["id"] == "S8.5.8.2-005")["pending"]), {"vector-bound-capture"})
        self.assertEqual(set(next(row for row in explicit["requirements"] if row["id"] == "S8.5.8.2-004")["pending"]), {"inquiry-normalization-source"})

    def test_rendered_views_and_check_mode_are_deterministic(self):
        self.assertEqual(generated.render_view(generated.EXPLICIT_SECTION, self.registry.catalogues[generated.EXPLICIT_SECTION]),
                         (ROOT / generated.EXPLICIT_VIEW).read_text())
        self.assertEqual(generated.render_view(generated.ASSUMED_SECTION, self.registry.catalogues[generated.ASSUMED_SECTION]),
                         (ROOT / generated.ASSUMED_VIEW).read_text())
        actual = {path for path in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
