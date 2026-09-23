"""Runtime fixture metadata for Fortran 2023 control edit descriptors."""

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
import generate_control_edit_descriptor_fixtures as generated


class ControlEditDescriptorFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_sixteen_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 32)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(generated.VARIANTS[self.specs[case.name]["variant"]]["rule"], case.rule)
            self.assertEqual(generated.VARIANTS[self.specs[case.name]["variant"]]["facets"], case.meta.facets)
            self.assertEqual(case.fixture.files, ["source.f90"])
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expect.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence="positive-control")),
                                          self.registry.requirements[case.rule])
            for bad in (replace(case, meta=replace(case.meta, facets=[])),
                        replace(case, meta=replace(case.meta, facets=[case.meta.facets[0], "foreign"])),
                        replace(case, meta=replace(case.meta, facets=case.meta.facets * 2))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_pin_exact_expected_fields_and_sentinel_prefill(self):
        anchors = {
            "position_t3_writes_later_blank_fill": ["write(buf,'(T3,\"Z\")')", "if (buf /= '  Z')"],
            "position_t1_subsequent_replacement": ["write(buf,'(\"AB\",T1,\"C\")')", "if (buf /= 'CB')"],
            "t_forward_from_current": ["write(buf,'(\"A\",T3,\"B\")')", "if (buf /= 'A B')"],
            "tl_backward_two_positions": ["write(buf,'(\"ABC\",TL2,\"Z\")')", "if (buf /= 'AZC')"],
            "tr_forward_two_positions": ["write(buf,'(\"A\",TR2,\"B\")')", "if (buf /= 'A  B')"],
            "x_forward_two_positions": ["write(buf,'(\"A\",2X,\"B\")')", "if (buf /= 'A  B')"],
            "slash_explicit_repeat": ["rec = '#'", "write(rec,'(\"A\",2/,\"B\")')", "observed = rec(1) // rec(2) // rec(3)", "if (observed /= 'A B')"],
            "colon_terminates_without_item": ["write(buf,'(I1,:,\",\",I1)') 4", "if (buf /= '4')"],
            "colon_no_effect_with_item": ["write(buf,'(I1,:,\",\",I1)') 4,5", "if (buf /= '4,5')"],
            "ss_suppresses_optional_plus": ["write(buf,'(SS,I2)') 7", "if (buf /= ' 7')"],
            "sp_prints_optional_plus": ["write(buf,'(SP,I2)') 7", "if (buf /= '+7')"],
            "bn_nonleading_blank_null": ["input = '1 2'", "read(input,'(BN,I3)') observed", "if (observed /= 12)"],
            "bz_nonleading_blank_zero": ["input = '1 2'", "read(input,'(BZ,I3)') observed", "if (observed /= 102)"],
            "dc_outputs_comma_decimal": ["write(buf,'(DC,F3.1)') 1.5", "if (buf /= '1,5')"],
            "dp_outputs_point_decimal": ["write(buf,'(DP,F3.1)') 1.5", "if (buf /= '1.5')"],
            "string_descriptor_includes_blank": ["write(buf,'(\"A B\")')", "if (buf /= 'A B')"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            variant = spec["variant"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), 1)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            if "read(input" not in source:
                self.assertIn("#", source)
            if ":: buf" in source and "observed = rec" not in source:
                self.assertRegex(source, r"if \(len\(buf\) /= \d+\)")
            for needle in anchors[variant]:
                self.assertIn(needle, source)
            mutated_header = source.replace("! covers: " + spec["facets"][0], "! covers: foreign", 1)
            self.assertNotEqual(mutated_header, source)
            self.assertNotIn("! covers: " + spec["facets"][0] + "\n", mutated_header)

    def test_mutation_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 61)
        self.assertEqual(sum(len(spec["input_mutations"]) for spec in self.specs.values()), 16)
        self.assertEqual(sum(len(spec["descriptor_mutations"]) for spec in self.specs.values()), 16)
        self.assertEqual(sum(1 for spec in self.specs.values() for m in spec["descriptor_mutations"]
                             if m["category"] == "descriptor-substitution"), 9)
        self.assertEqual(sum(1 for spec in self.specs.values() for m in spec["descriptor_mutations"]
                             if m["category"] == "descriptor-omission"), 7)
        self.assertEqual(sum(len(spec["reverse_mutations"]) for spec in self.specs.values()), 1)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 45)
        saw_reverse = False
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["guards"]), len(spec["observations"]) + 2)
            hashes = set()
            for mutation in spec["probes"] + spec["input_mutations"] + spec["descriptor_mutations"] + spec["omissions"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutated_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                if mutation in spec["descriptor_mutations"]:
                    self.assertIn(mutation["category"], {"descriptor-substitution", "descriptor-omission"})
            for mutation in spec["reverse_mutations"]:
                saw_reverse = True
                mutant = generated.mutated_source(spec, mutation)
                expected = raw
                for repl in sorted(mutation["replacements"], key=lambda item: item["span"][0], reverse=True):
                    start, end = repl["span"]
                    self.assertEqual(raw[start:end].decode("ascii"), repl["expected"])
                    expected = expected[:start] + repl["replacement"].encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
                self.assertEqual((mutation["category"], mutation["intended"]), ("sentinel-load-bearing", "pass"))
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.mutated_source(changed, spec["probes"][0])
        self.assertTrue(saw_reverse)

    def test_descriptor_substitution_matrix_and_mode_pairs_are_permanent(self):
        substitutions = {(m["expected"], m["replacement"]) for spec in self.specs.values()
                         for m in spec["descriptor_mutations"] if m["category"] == "descriptor-substitution"}
        self.assertTrue({("T3", "T4"), ("TL2", "TR2"), ("SP", "SS"),
                         ("DC", "DP"), ("BN", "BZ")} <= substitutions)
        self.assertTrue({("SS", "SP"), ("DP", "DC"), ("BZ", "BN")} <= substitutions)
        self.assertFalse({("LZS", "LZP"), ("LZP", "LZS")} & substitutions)
        by_variant = {spec["variant"]: spec for spec in self.specs.values()}
        self.assertEqual(by_variant["ss_suppresses_optional_plus"]["expected"], " 7")
        self.assertEqual(by_variant["sp_prints_optional_plus"]["expected"], "+7")
        self.assertEqual(by_variant["bn_nonleading_blank_null"]["expected"], 12)
        self.assertEqual(by_variant["bz_nonleading_blank_zero"]["expected"], 102)
        self.assertEqual(by_variant["dc_outputs_comma_decimal"]["expected"], "1,5")
        self.assertEqual(by_variant["dp_outputs_point_decimal"]["expected"], "1.5")
        self.assertGreaterEqual(sum(1 for spec in self.specs.values()
                                    for m in spec["descriptor_mutations"]
                                    if m["category"] == "descriptor-omission"), 1)

    def test_catalogue_sync_removes_only_selected_pending_entries_and_regenerates_views(self):
        for section, rel in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, facets in generated.FACETS_BY_RULE.items():
                if not rule.startswith("S" + section):
                    continue
                for facet in facets:
                    self.assertNotIn(facet, by_rule[rule].get("pending", {}))
                if rule in generated.REMAINING_PENDING:
                    self.assertEqual(set(by_rule[rule].get("pending", {})), generated.REMAINING_PENDING[rule])
                self.assertIn(generated.ORACLE_PREFIX[rule], by_rule[rule]["oracle"])
                self.assertIn(generated.LIMIT_PREFIX[rule], by_rule[rule]["oracle_limitation"])
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            if any(case["section"] == section for case in generated.CASES):
                self.assertIn(generated.SUMMARY_BEGIN, view)
                self.assertIn("Internal output cases pre-fill", view)
            else:
                self.assertNotIn(generated.SUMMARY_BEGIN, view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
