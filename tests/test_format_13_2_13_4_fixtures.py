"""Runtime fixture metadata for FORMAT specifications and format control (13.2-13.4)."""

import json
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_format_13_2_13_4_fixtures as generated


class Format132134FixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_owned_manifests_are_discoverable_and_bound(self):
        expected_ids = {generated.identifier(row["variant"]) for row in generated.CASES}
        self.assertEqual(set(self.cases), expected_ids)
        self.assertEqual(set(self.specs), expected_ids)
        self.assertEqual(len(self.files), 2 * len(generated.CASES))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        owned_facets = {facet for row in generated.CASES for facet in row["facets"]}
        self.assertEqual(len(owned_facets), len(generated.CASES))
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, owned_facets)
        for name, spec in self.specs.items():
            case = self.cases[name]
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.fixture.files, ["source.f90"])
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome,
                              case.fixture.expectation.exit_code), ("run", "success", 0))
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])),
                                          self.registry.requirements[case.rule])

    def test_sources_pin_sentinels_lengths_and_key_format_features(self):
        anchors = {
            "format_stmt_keyword_spec": ["100 format(SS,I3)", "write(buf,100) 7", "if (buf /= '  7')"],
            "empty_parenthesized_format": ["write(buf,'()')", "if (buf /= ' ')"] ,
            "rank_one_character_array_concat": ["fmt = [character(len=4) :: '(SS', ',I3)']", "write(buf,fmt) 7"],
            "array_element_order_concat": ["fmt = [character(len=4) :: '(SS', ',I1', ',I1', ')   ']", "if (buf /= '25 ')"] ,
            "asterisk_parenthesized_list": ["write(buf,'(SS,*(I1,:,\";\"))') 4,5,6", "if (buf /= '4;5;6')"],
            "complex_item_two_real_descriptors": ["z = cmplx(2.5, -3.5)", "write(buf,'(SS,F5.1,F5.1)') z", "if (buf /= '  2.5 -3.5')"],
            "colon_without_following_item_terminates": ["write(buf,'(SS,I1,:,\",\",I1)') 4", "if (buf /= '4 ')"] ,
            "unlimited_reversion_modes_unchanged": ["write(buf,'(SP,*(I2))') 7,8", "if (buf /= '+7+8')"],
            "nested_group_reversion_target": ["write(rec,'(SS,\"H\",(I1,\",\"))') 1,2,3", "if (observed /= 'H1,2, 3, ')"] ,
            "no_preceding_parenthesis_fallback": ["write(rec,'(SS,\"H\",I1)') 1,2,3", "if (observed /= 'H1H2H3')"],
            "repeat_reused_on_reversion": ["write(rec,'(SS,\"H\",2(I1))') 1,2,3,4,5,6", "if (observed /= 'H1234 56 ')"] ,
            "complete_reversion_modes_unchanged": ["write(rec,'(SP,(I2))') 7,8", "if (observed /= '+7+8')"],
            "reversion_positions_like_slash": ["write(rec,'(SS,I1)') 1,2,3", "if (observed /= '123')"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertIn("#", source)
            self.assertIn("if (len(", source)
            self.assertIn("checks = checks + 1", source)
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\b(trim|adjustl|adjustr|dt\s*\(|iomsg|iostat)\b")
            for line in source.splitlines():
                fmt = ""
                if "format(" in line.lower():
                    fmt = line[line.lower().index("format("):]
                elif "write(" in line.lower() and "'" in line:
                    parts = line.split("'")
                    fmt = parts[1] if len(parts) > 2 else ""
                if re.search(r"(?i)\b[IF]\d", fmt):
                    self.assertRegex(fmt, r"(?i)\bS[SP]\b", line)
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)
            for needle in anchors.get(spec["variant"], []):
                self.assertIn(needle, source)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["feature_mutations"]) for spec in self.specs.values()), len(self.specs))
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertTrue(spec["feature_mutations"], spec["variant"])
            self.assertGreaterEqual(len(spec["omissions"]), 2, spec["variant"])
            hashes = set()
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                digest = generated.sha(mutant)
                self.assertNotIn(digest, hashes)
                hashes.add(digest)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent"):
                generated.mutated_source(changed, spec["mutations"][0])

    def test_catalogues_remove_only_selected_pending_facets_and_render_views(self):
        by_section = {}
        for row in generated.CASES:
            by_section.setdefault(row["section"], set()).update(row["facets"])
        for section, rel in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, selected in generated.SELECTED_BY_RULE.items():
                if rule not in by_rule:
                    continue
                requirement = by_rule[rule]
                self.assertFalse(set(requirement.get("pending", {})) & selected)
                self.assertEqual(set(requirement.get("pending", {})), set(requirement["facets"]) - selected)
                self.assertIn(generated.ORACLE_PREFIX[rule], requirement["oracle"])
                self.assertIn(generated.LIMIT_PREFIX[rule], requirement["oracle_limitation"])
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn(f"runtime observations for {section}", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
