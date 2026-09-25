"""Fixture metadata for Fortran 2023 12.10.1/12.10.2.1 INQUIRE tests."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement
import generate_io_inquire_12_10_1_fixtures as generated


class IOInquireFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in all_cases if Path(case.path) in manifests}

    def test_owned_manifest_set_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.files), 2 * len(self.specs))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        covered = {}
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.kind, spec["kind"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images),
                             ("f2023", "standard", 1))
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            validate_case_requirement(case, self.registry.requirements[case.rule],
                                      numbered=case.rule.startswith(("C", "R")))
            covered.setdefault(case.rule, set()).update(case.meta.facets)
        direct = set(generated.DIRECT_RUNTIME_RULES) | {item["rule"] for item in generated.INVALID_CASES} | {
            rule for rule, _facets, _source in generated.CONTROLS.values()
        }
        for rule in direct:
            self.assertEqual(covered[rule], set(generated.RULE_FACETS[rule]), rule)
        for rule in generated.LINKED_RUNTIME_RULES:
            self.assertNotIn(rule, covered)

    def test_sources_are_hygienic_and_guard_inquiry_targets(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertNotRegex(source.lower(), r"/tmp|/var/tmp")
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            if spec["variant"] in {"forms_timing", "syntax_forms", "specifier_assignments"}:
                self.assertIn("sentinel-probe:", source)
                self.assertIn("call expect_", source)
                self.assertIn("inquire(", source.lower())
            if spec["variant"] in {"forms_timing", "specifier_assignments"}:
                self.assertIn("subroutine cleanup_name", source)
            if spec["kind"] == "invalid":
                self.assertIn("control", spec)
                self.assertEqual(spec["evidence"], "effect")

    def test_mutation_spans_are_bound_to_parent_sources(self):
        unique = {}
        for spec in self.specs.values():
            if spec.get("mutations"):
                unique.setdefault((spec["variant"], spec["source_sha256"]), spec)
        self.assertEqual({variant for variant, _sha in unique},
                         {"forms_timing", "syntax_forms", "specifier_assignments"})
        categories = {m["category"] for spec in unique.values() for m in spec["mutations"]}
        self.assertIn("feature", categories)
        self.assertIn("sentinel-init-remove", categories)
        self.assertIn("sentinel-init-expected", categories)
        self.assertIn("sentinel-init-default", categories)
        for spec in unique.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["mutations"]), 5)
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)

    def test_catalogues_and_views_are_synchronized(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            self.assertEqual(generated.synced_catalogue(section, catalogue), catalogue)
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.RULE_FACETS.items():
                if generated.RULE_SECTION[rule] != section:
                    continue
                row = by_rule[rule]
                for facet in facets:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIX[rule], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIX[rule], row["oracle_limitation"])
            view = generated.render_view(section, catalogue, ROOT)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("INQUIRE general/specifier-list fixtures", view)
        evidence = json.loads((ROOT / generated.EVIDENCE_LINKS_PATH).read_text())
        self.assertEqual(generated.synced_evidence_links(ROOT, self.registry.catalogues), evidence)
        owned = [link for link in evidence["links"] if link["id"].endswith(".io-inquire-12-10-1")]
        self.assertEqual(len(owned), sum(len(generated.RULE_FACETS[rule]) for rule in generated.LINKED_RUNTIME_RULES))

    def test_generation_check_mode_is_read_only(self):
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
