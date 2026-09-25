"""Additional 7.6.1 ENUM,BIND(C) diagnostic fixtures and controls."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry, validate_case_requirement

import generate_enum_type_7_6_1_b_fixtures as generated


class EnumType761BDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def test_exact_case_metadata_and_requirement_roles(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.specs), 20)
        self.assertEqual(sum(1 for spec in self.specs.values() if spec["kind"] == "invalid"), 10)
        self.assertEqual(sum(len(facets) for facets in generated.SELECTED.values()), 10)
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
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertIsNone(case.fixture.link)
            if spec["kind"] == "invalid":
                self.assertEqual(case.fixture.expectation.outcome, "diagnose")
                diagnostic = case.fixture.expectation.diagnostic
                self.assertEqual(diagnostic["file"], "source.f90")
                self.assertLessEqual(diagnostic["line"], diagnostic["end_line"])
                self.assertNotIn("contains_any", diagnostic)
                for needle in ("internal compiler error", "internal error", "not implemented"):
                    self.assertIn(needle, diagnostic["excludes_any"])
            else:
                self.assertEqual(case.fixture.expectation.outcome, "success")

    def test_generated_files_are_exact_and_prefix_isolated(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob(generated.PREFIX + "*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 40)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            self.assertTrue(raw.endswith(b"\n"))
            if path.name == "source.f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)
        generated.generate(ROOT, check=True)
        self.assertEqual(generated.build_corpus()[0], self.files)

    def test_controls_are_one_property_repairs_of_invalid_sources(self):
        for spec in self.specs.values():
            if spec["kind"] != "invalid":
                continue
            control = self.specs[spec["control_id"]]
            self.assertEqual(spec["source"].replace(spec["repair_from"], spec["repair_to"], 1),
                             control["source"])
            self.assertNotIn(spec["repair_from"], control["source"])
            self.assertIn(spec["repair_to"], control["source"])
            self.assertEqual(control["facets"], spec["facets"])
            manifest = json.loads(Path(self.cases[spec["id"]].path).read_text())
            self.assertLessEqual(manifest["expect"]["diagnostic"]["line"],
                                 manifest["expect"]["diagnostic"]["end_line"])

    def test_sources_are_unnamed_enum_bind_c_not_named_or_enumeration_type(self):
        for spec in self.specs.values():
            source = spec["source"].lower()
            self.assertIn("enum", source)
            self.assertNotIn("enumeration type", source)
            self.assertNotRegex(source, r"(?im)^\\s*enum\\s*,\\s*bind\\s*\\(\\s*c\\s*\\)\\s*::")
            self.assertNotRegex(source, r"(?im)^\s*type\s*\(")
            self.assertNotRegex(source, r"(?i)\\b(?:iso_c_binding|c_int|transfer|storage_size|kind)\\b")
            if spec["kind"] == "valid":
                self.assertIn("enum, bind(c)", source)

    def test_catalogue_sync_and_pending_partition(self):
        synced = generated.synced_catalogue(self.catalogue)
        self.assertEqual(synced, self.catalogue)
        by_rule = {row["id"]: row for row in self.catalogue["requirements"]}
        for rule, facets in generated.SELECTED.items():
            self.assertFalse(set(facets) & set(by_rule[rule].get("pending", {})))
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertIn("named-bind-c", by_rule["R760"]["pending"])
        self.assertIn("named-specifier-admission", by_rule["R764"]["pending"])
        self.assertIn("integer-value-roundtrip", by_rule["S7.6.1-002"]["pending"])
        self.assertEqual(sum(len(row["pending"]) for row in self.catalogue["requirements"]), 35)

    def test_view_mentions_additional_diagnostics_and_reference_gate(self):
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue))
        self.assertIn("enum_type_7_6_1_b_` diagnostics add ten", view)
        self.assertIn("rejects named enum-type syntax", view)
        self.assertIn("**29 of64 facets**; **35 remain pending**.", view)
        appendix = view.split("## Complete finite pending plans\n", 1)[1]
        self.assertEqual(appendix.count("* **`"), 35)

    def test_no_hidden_runtime_or_value_oracle_in_compile_packet(self):
        for spec in self.specs.values():
            self.assertEqual(spec["phase"], "compile")
            self.assertNotRegex(spec["source"], r"(?im)^\\s*(if|print|write|error stop)\\b")
            self.assertNotIn("check", spec["source"].lower())


if __name__ == "__main__":
    unittest.main()
