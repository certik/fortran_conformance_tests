"""Runtime fixture metadata for Fortran 2023 list-directed input."""

import json
from pathlib import Path
import re
import sys
import unittest
from dataclasses import replace

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_list_directed_input_fixtures as generated


class ListDirectedInputFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_eighteen_owned_f2023_internal_read_fixtures(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 36)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual(sum(len(case.meta.facets) for case in self.cases.values()), 18)
        for case in self.cases.values():
            expected_evidence = self.specs[case.name]["evidence"]
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", expected_evidence, "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(generated.VARIANTS[self.specs[case.name]["variant"]],
                             (case.rule, case.meta.facets[0]))
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expect.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"],
                             "positive-control" if expected_evidence == "positive-control" else "runtime-effect")
            bad_evidence = "effect" if expected_evidence == "positive-control" else "positive-control"
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence=bad_evidence)),
                                          self.registry.requirements[case.rule])

    def test_sources_pin_records_sentinels_len_and_no_output_or_files(self):
        anchors = {
            "record_end_as_blank": ["recs = [character(len=1) :: \"1\", \"2\"]", "read(recs,*) a, b", "if (a /= 1)", "if (b /= 2)"],
            "multiple_blanks_collapse": ["rec = \"1   2\"", "read(rec,*) a, b", "if (a /= 1)", "if (b /= 2)"],
            "character_constants_preserve_blanks": ["rec = \"'A  B'\"", "if (len(text) /= 4)", "if (text /= 'A  B')"],
            "repeat_constant": ["rec = \"11,3*7,29\"", "read(rec,*) x", "if (x(5) /= 29)"],
            "repeat_null": ["x=[101,202,303]", "rec = \"2*\"", "read(rec,*) x(1), x(2)", "if (x(2) /= 202)"],
            "comma_separator": ["rec = \"1, 2\"", "read(rec,*) a, b", "if (a /= 1)", "if (b /= 2)"],
            "edit_compatible_forms": ["rec_i = \"42\"", "rec_l = \".TRUE.\"", "if (n /= 42)", "if (flag .neqv. .true.)"],
            "blanks_not_zeros": ["rec = \"1 2\"", "if (a /= 1)", "if (b /= 2)"],
            "repeat_undelimited_character": ["rec = \"2*ab\"", "if (len(words(1)) /= 2)", "if (words(1) /= 'ab')"],
            "repeat_literal_otherwise": ["rec = \"5,2*7,19\"", "if (x(1) /= 5)", "if (x(4) /= 19)"],
            "character_delimited_sequence": ["rec = \"'A,B/;'\"", "if (len(text) /= 5)", "if (text /= 'A,B/;')"],
            "character_blank_padding": ["rec = \"'AB'\"", "if (len(text) /= 4)", "if (text /= 'AB  ')"] ,
            "repeat_null_form": ["x=907", "rec = \"1*\"", "if (x /= 907)"],
            "empty_between_separators": ["x=[111,222,333]", "rec = \"10,,30\"", "if (x(2) /= 222)"],
            "leading_empty_first_record": ["x=707", "y=808", "rec = \",9\"", "if (x /= 707)", "if (y /= 9)"],
            "null_preserves_value": ["x=717", "y=818", "rec = \",44\"", "if (x /= 717)", "if (y /= 44)"],
            "slash_terminates": ["x=-701", "y=-802", "rec = \"1 / 99\"", "if (y /= -802)"],
            "slash_null_supplies_remaining": ["x=[501,602,703]", "rec = \"1 /\"", "if (x(2) /= 602)", "if (x(3) /= 703)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn("read(", source)
            self.assertNotRegex(source, r"(?i)\b(open|close|write\s*\([^*]|rewind|backspace|endfile|unit\s*=|newunit\s*=|scratch)\b")
            self.assertNotRegex(source, r"(?i)\b(real|complex|selected_real_kind|c_loc|loc|transfer)\b")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|error\s+stop\s+[0-9])\b")
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            for sentinel in spec["sentinels"]:
                self.assertNotIn("=0", sentinel.replace(" ", ""))
                self.assertNotIn(",0", sentinel.replace(" ", ""))
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
            if spec["variant"] in {
                "character_constants_preserve_blanks",
                "repeat_undelimited_character",
                "character_delimited_sequence",
                "character_blank_padding",
            }:
                self.assertRegex(source, r"len\(")

    def test_mutation_spans_cover_oracles_inputs_features_read_counts_and_reverse_sentinels(self):
        self.assertEqual(sum(len(generated.all_mutations(spec)) for spec in self.specs.values()), 208)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 20)
        self.assertEqual(sum(len(spec["feature_mutations"]) for spec in self.specs.values()), 27)
        self.assertEqual(sum(len(spec["reverse_mutations"]) for spec in self.specs.values()), 5)
        categories = {m["category"] for spec in self.specs.values() for m in spec["input_mutations"] + spec["feature_mutations"]}
        for required in ("repeat-count", "repeat-null-count", "slash-deletion", "null-removal", "value-order", "read-list-cardinality"):
            self.assertIn(required, categories)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertGreaterEqual(len(spec["input_mutations"]), 1)
            self.assertEqual(len(spec["read_lists"]), spec["source"].count("read("))
            for mutation in generated.all_mutations(spec):
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, generated.all_mutations(spec)[0])
        reverse_variants = {spec["variant"] for spec in self.specs.values() if spec["reverse_mutations"]}
        self.assertEqual(reverse_variants, {"repeat_null", "repeat_null_form", "empty_between_separators",
                                            "null_preserves_value", "slash_null_supplies_remaining"})
        for spec in self.specs.values():
            for mutation in spec["reverse_mutations"]:
                reverse = generated.mutated_source(spec, mutation).decode("ascii")
                self.assertRegex(reverse, r"/= 0")
                self.assertNotEqual(reverse, spec["source"])

    def test_catalogue_sync_removes_only_selected_pending_facets_and_renders_summary(self):
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, remaining in generated.REMAINING_PENDING.items():
                if rule not in by_rule:
                    continue
                self.assertEqual(set(by_rule[rule].get("pending", {})), remaining)
                for facet in generated.FACETS_BY_RULE.get(rule, []):
                    self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                    self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
                    self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
            synced = generated.synced_catalogue(section, catalogue)
            self.assertEqual(synced, catalogue)
            view = generated.render_view(section, synced)
            self.assertIn(generated.SUMMARY_BEGIN, view)
            self.assertIn("Eighteen complete internal READ fixtures", view)
            self.assertIn("make no claim about list-directed output form", view)
        self.assertIn("real-decimal-field", self.registry.requirements["S13.10.3.1-004"]["pending"])
        self.assertIn("slash-ignores-rest", self.registry.requirements["S13.10.3.2-003"]["pending"])

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
