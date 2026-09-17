import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, case_review_bindings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_declaration_name_source_uses as generator


class DeclarationNameSourceUseTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry(ROOT)
        self.inventory = self.registry.source_uses.inventories[generator.INVENTORY_ID]

    def report(self):
        return next(row for row in self.registry.source_uses.report()
                    if row["id"] == generator.INVENTORY_ID)

    def test_generated_registry_is_current_without_requiring_an_approval_state(self):
        generator.check_generated(self.registry)
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools/generate_declaration_name_source_uses.py"), "--check"],
            cwd=ROOT, text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_complete_finite_denominator_and_no_completion_credit(self):
        report = self.report()
        self.assertEqual((report["source_unit_count"], report["base_source_unit_count"],
                          report["fine_source_unit_count"]), (127, 25, 102))
        self.assertEqual(report["disposition_counts"],
                         {"mapped": 30, "not-applicable": 97, "pending": 0, "missing": 0})
        self.assertEqual(report["occurrence_record_count"], 31)
        self.assertTrue(report["classified_scope"])
        self.assertEqual(report["coverage_credit"], "none")
        self.assertEqual(report["facet_completion"], "pending")
        self.assertEqual(report["new_executions"], 0)
        self.assertEqual(report["universal_conformance"], "not-established")

    def test_exact_assumed_and_explicit_definition_resolutions(self):
        counts = {"target": 0, "explicit-override": 0}
        for entry in self.inventory["entries"]:
            for item in entry["occurrences"]:
                counts[item["resolution"]] += 1
                expected = ("target", "4.1.3#R402") if item["term"] == "function-name" else (
                    "explicit-override", "8.2#R804")
                self.assertEqual((item["resolution"], item["definition"]), expected)
                self.assertIn("6.2.2#R603", item["dependencies"])
                self.assertIn("6.2.2#C601", item["dependencies"])
        self.assertEqual(counts, {"target": 9, "explicit-override": 22})

    def test_fine_records_reuse_seven_parent_occurrences(self):
        physical = set()
        for entry in self.inventory["entries"]:
            parent = self.registry.source_material(entry["source"])["parent"]
            for item in entry["occurrences"]:
                physical.add((parent, item["term"], item["ordinal"]))
        self.assertEqual(len(physical), 7)
        self.assertEqual(sum(term == "function-name" for _, term, _ in physical), 2)
        rows = {entry["source"]: entry for entry in self.inventory["entries"]}
        self.assertIn("defining production head", rows["8.2#R804"]["occurrences"][0]["rationale"])
        self.assertEqual(rows["8.2#R803.function-character-length"]["occurrences"][0]["term"],
                         "function-name")
        self.assertEqual(rows["8.2#R803.suffix-order"]["occurrences"][0]["term"], "object-name")

    def test_prose_specifiers_examples_and_anchor_names_are_not_fake_occurrences(self):
        rows = {entry["source"]: entry for entry in self.inventory["entries"]}
        for anchor in ("8.2#C802", "8.2#C802.no-name-outside-premise", "8.2#C803",
                       "8.2#R806", "8.2#p3", "8.2#note-unnumbered", "8.2#note-unnumbered.2"):
            with self.subTest(anchor=anchor):
                self.assertEqual(rows[anchor]["disposition"], "not-applicable")
                self.assertEqual(rows[anchor]["occurrences"], [])

    def test_wrong_alias_resolution_cannot_pass_generator_check(self):
        row = next(entry for entry in self.inventory["entries"] if entry["source"] == "8.2#R804")
        row["occurrences"][0].update(resolution="target", definition="4.1.3#R402")
        with self.assertRaisesRegex(SuiteError, "stale declaration-name"):
            generator.check_generated(self.registry)

    def test_new_fine_units_require_review_instead_of_automatic_exclusion(self):
        self.registry.catalogues["8.2"]["subunits"]["R803"].append("R803.unreviewed")
        with self.assertRaisesRegex(SuiteError, "fine source census changed"):
            generator.build_inventory(self.registry)

    def test_source_hash_or_base_denominator_change_requires_review(self):
        self.registry.sections["8.2"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(SuiteError, "original source census changed"):
            generator.build_inventory(self.registry)
        self.registry.sections["8.2"]["sha256"] = generator.SECTION_SHA256
        self.registry.sections["8.2"]["units"]["p99"] = copy.deepcopy(
            self.registry.sections["8.2"]["units"]["p1"])
        with self.assertRaisesRegex(SuiteError, "original source census changed"):
            generator.build_inventory(self.registry)

    def test_different_document_cannot_reuse_the_classification(self):
        self.registry.standard["sha256"] = "0" * 64
        with self.assertRaisesRegex(SuiteError, "requires the pinned"):
            generator.build_inventory(self.registry)

    def test_deleted_entries_remain_in_the_denominator_as_missing(self):
        self.inventory["entries"].pop()
        report = self.report()
        self.assertEqual(report["source_unit_count"], 127)
        self.assertEqual(report["disposition_counts"]["missing"], 1)
        self.assertFalse(report["classified_scope"])
        with self.assertRaisesRegex(SuiteError, "stale declaration-name"):
            generator.check_generated(self.registry)

    def test_generation_preserves_draft_current_and_stale_review_records(self):
        original_record = copy.deepcopy(self.inventory.get("review"))
        self.inventory.pop("review", None)
        generator.check_generated(self.registry)
        self.assertEqual(self.report()["state"], "draft")
        report = self.report()
        sources = self.registry.source_uses._sources(
            self.inventory, self.registry.source_uses._universe(self.inventory))
        self.inventory["review"] = dict(state="source-reviewed", rationale="In-memory lifecycle probe.",
                                        fingerprint=report["review"]["fingerprint"], sources=sources)
        self.assertEqual(self.report()["state"], "current")
        generator.check_generated(self.registry)
        self.inventory["review"]["fingerprint"] = "0" * 64
        self.inventory["review"]["rationale"] = "Retained stale history."
        self.assertEqual(self.report()["state"], "stale")
        generated = generator.generated_registry(self.registry)
        row = next(item for item in generated["inventories"] if item["id"] == generator.INVENTORY_ID)
        self.assertEqual(row["review"], self.inventory["review"])
        generator.check_generated(self.registry)
        if original_record is not None:
            self.inventory["review"] = original_record

    def test_source_prerequisite_state_does_not_break_generation(self):
        self.registry.catalogues["8.2"]["review_state"] = "draft"
        self.assertIn("8.2: catalogue source review is draft", self.report()["blockers"])
        generator.check_generated(self.registry)

    def test_generation_preserves_unrelated_inventory_and_case_bindings(self):
        before_data = copy.deepcopy(self.registry.source_uses.data)
        before_reviews = copy.deepcopy(self.registry.reviews)
        cases = runner.collect_cases(ROOT / "tests", self.registry)
        before_bindings = case_review_bindings(cases, self.registry)
        other = dict(
            id="synthetic-unrelated", target=dict(requirement="R401", facet="assumed-list-census",
                                                  source_units=["4.1.3#R401"]),
            basis=["8.2#R803"], sections=["8.2"], coverage_credit="none",
            claim="In-memory preservation probe.", limitation="No approval or completeness.",
            entries=[])
        self.registry.source_uses.data["inventories"].append(other)
        generated = generator.generated_registry(self.registry)
        self.assertEqual(generated["inventories"][-1], other)
        self.assertEqual(self.registry.source_uses.data["inventories"][:-1], before_data["inventories"])
        self.assertEqual(self.registry.reviews, before_reviews)
        self.assertEqual(case_review_bindings(cases, self.registry), before_bindings)

    def test_wrong_pdf_fails_before_any_authoring_dependency_is_needed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong.pdf"
            path.write_bytes(b"not the pinned document")
            with self.assertRaisesRegex(SuiteError, "PDF checksum differs"):
                generator.verify_pdf(self.registry, path)


if __name__ == "__main__":
    unittest.main()
