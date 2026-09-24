"""Runtime fixture metadata for Fortran 2023 12.1-12.3.2 I/O records/files."""

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
import generate_io_records_files_fixtures as generated


class IORecordsFilesFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_owned_fixture_manifests_bind_selected_facets(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.files), 2 * len(self.specs))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        selected = {rule: set(facets) for rule, facets in generated.RULE_FACETS.items()}
        covered = {}
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.kind, "valid")
            expected_evidence = "positive-control" if case.rule in generated.POSITIVE_CONTROL_RULES else "effect"
            self.assertEqual(case.meta.evidence, expected_evidence)
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images), ("f2023", "standard", 1))
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["completion"]])
            self.assertEqual(expect.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])
            covered.setdefault(case.rule, set()).update(case.meta.facets)
        self.assertEqual(covered, selected)

    def test_sources_are_hygienic_and_contain_load_bearing_io_patterns(self):
        anchors = {
            "internal_formatted_transfer": ["record = '#####'", "write(record,'(I3,1X,A)'", "read(record,'(I3,1X,A)'", "call expect_char(record, '137 Q'"],
            "external_formatted_records": ["status='scratch'", "write(u,'()'", "rewind(u", "call expect_char(ch, ' ', 'read-empty')"],
            "unformatted_value_and_empty_records": ["form='unformatted'", "write(u, iostat=ios)", "read(u, iostat=ios)", "call expect_logical(flag, .false."],
            "endfile_explicit_and_implicit": ["endfile(u", "iostat_end", "open(unit=u, file=name_open_b", "status='delete'"],
            "named_file_create_delete_inquire": ["inquire(file=name, exist=exists)", "status='new'", "status='delete'", "call expect_logical(exists, .false., 'exists-after-delete')"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn("  implicit none\n", source)
            self.assertNotIn("/tmp", source)
            self.assertNotRegex(source, r"(?i)\bpos\s*=")
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            if "expect_char" in source:
                self.assertIn("if (len(value) /= len(expected))", source)
            if spec["variant"] == "named_file_create_delete_inquire":
                self.assertIn("call cleanup_name(name)", source)
            if spec["variant"] == "endfile_explicit_and_implicit":
                self.assertIn("call cleanup_name(name_close)", source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()),
                         sum(len(generated.source_specs()[name]["mutations"]) for name in self.specs))
        categories = {m["category"] for spec in self.specs.values() for m in spec["mutations"]}
        for category in {"feature-removal", "sentinel-init-remove", "sentinel-init-expected",
                         "oracle", "completion"}:
            self.assertIn(category, categories)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["mutations"]), 7)
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)

    def test_permanent_facet_assertion_feature_mutant_table_is_complete(self):
        expected = {(rule, facet) for rule, facets in generated.RULE_FACETS.items() for facet in facets}
        self.assertEqual(set(generated.FACET_ASSERTION_MUTANTS), expected)
        feature_categories = {
            "feature-removal", "feature-substitution", "format-substitution", "open-status",
            "output-list", "record-data", "file-name",
        }
        by_variant = {}
        for spec in self.specs.values():
            by_variant.setdefault(spec["variant"], set()).update(
                mutation["id"] for mutation in spec["mutations"] if mutation["category"] in feature_categories
            )
        for key, rows in generated.FACET_ASSERTION_MUTANTS.items():
            if isinstance(rows, dict):
                rows = [rows]
            self.assertGreaterEqual(len(rows), 1, key)
            for row in rows:
                self.assertIn(row["variant"], by_variant, key)
                self.assertIn(row["feature_mutant"], by_variant[row["variant"]], key)
                self.assertRegex(row["assertion"], r"^[a-z0-9-]+$")

    def test_catalogues_are_synchronized_for_selected_facets_only(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            synced = generated.synced_catalogue(section, catalogue)
            self.assertEqual(synced, catalogue)
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.RULE_FACETS.items():
                if rule not in by_rule:
                    continue
                row = by_rule[rule]
                for facet in facets:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIX[rule], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIX[rule], row["oracle_limitation"])
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("I/O records and files runtime observations", view)
            self.assertIn("assert byte sizes", view)

    def test_generation_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
