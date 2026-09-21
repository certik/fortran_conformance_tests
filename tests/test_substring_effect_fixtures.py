"""Runtime fixtures for Fortran 2023 substring effects."""

import copy
from dataclasses import replace
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_substring_effect_fixtures as generated


class SubstringEffectFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_eight_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 16)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         set(generated.FACETS))
        for excluded in ("in-range-nonzero", "both-endpoints", "character-variable-parent"):
            self.assertNotIn(excluded, {facet for case in self.cases.values() for facet in case.meta.facets})
        for case in self.cases.values():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             (generated.RULE, "valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(len(case.meta.facets), 1)
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
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence="positive-control")),
                                          self.registry.requirements[generated.RULE])

    def test_sources_use_actual_substrings_and_independent_oracles(self):
        expected = {
            "contiguous_portion": ["c='abcdef'", "if (c(2:5) /= 'bcde')", "c(3:4)='XY'",
                                   "if (c(2:5) /= 'bXYe')"],
            "first_expression_start": ["seed=1", "f=seed+2", "if (c(f:5) /= 'cde')",
                                       "f=f-1", "if (c(f:5) /= 'bcde')"],
            "second_expression_end": ["seed=2", "l=seed+2", "if (c(2:l) /= 'bcd')",
                                      "l=l+1", "if (c(2:l) /= 'bcde')"],
            "inclusive_character_selection": ["if (c(2:2) /= 'b')", "if (len(c(2:2)) /= 1)"],
            "default_start_one": ["if (c(:3) /= 'abc')", "if (c(:3) /= c(1:3))"],
            "default_end_parent_length": ["if (c(4:) /= 'def')", "if (len(c(4:)) /= 3)",
                                          "if (c(4:) /= c(4:6))", "c(6:6)='Z'",
                                          "if (c(4:) /= 'deZ')"],
            "length_formula": ["if (len(c(2:4)) /= 3)", "if (c(2:4) /= 'bcd')",
                               "if (len(c(4:4)) /= 1)", "if (c(4:4) /= 'd')",
                               "if (len(c(4:3)) /= 0)", "if (c(4:3) /= '')"],
            "zero_length_when_start_exceeds_end": ["if (len(c(4:3)) /= 0)", "if (c(4:3) /= '')",
                                                   "if (c /= 'abcdef')", "if (c(3:4) /= 'cd')"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertEqual(source.count("    error stop\n"), len(spec["guards"]) - 1)
            self.assertEqual(source.count("checks=checks+1"), len(spec["observations"]))
            self.assertIn(f"if (checks /= {len(spec['observations'])})", source)
            self.assertNotRegex(source, r"(?i)\b(index|scan|trim|adjustl)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(coarray|sync\s+all|error\s+stop\s+[0-9])\b")
            if spec["variant"] not in {"inclusive_character_selection", "default_end_parent_length",
                                       "length_formula", "zero_length_when_start_exceeds_end"}:
                self.assertNotRegex(source, r"(?i)\blen\s*\(")
            for needle in expected[spec["variant"]]:
                self.assertIn(needle, source)

    def test_guard_probe_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 40)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 42)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual(len(spec["guards"]), len(spec["observations"]) + 2)
            hashes = set()
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            for probe in spec["omissions"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                if probe["id"] == "omit-completion":
                    self.assertNotIn(spec["completion"].strip().encode(), mutant)
                    self.assertEqual((probe["kind"], probe["failure_stdout"]), ("output", ""))
                else:
                    self.assertIn(spec["completion"].strip().encode(), mutant)
                    if probe["id"].startswith("omit-observation") or probe["id"] == "omit-all-observations":
                        self.assertEqual(probe["guard_id"], "check-total")
            changed = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(changed, spec["probes"][0])

    def probe_check(self, spec, probe=None):
        raw = spec["source"].encode("ascii") if probe is None else generated.wrong_oracle_source(spec, probe)
        if probe is None:
            stdout, stderr, code, outcome = spec["completion"], "", 0, "pass"
        elif probe["kind"] == "output":
            stdout = "" if probe["mutation"] == "completion-statement-omission" else probe["replacement"] + "\n"
            stderr, code, outcome = "", 0, "fail"
        else:
            stdout, stderr, code, outcome = probe["failure_stdout"], "ERROR STOP\n", 2, "fail"
        trace = [dict(phase=phase, returncode=0, timed_out=False, stdout="", stderr="")
                 for phase in ("compile", "link", "run")]
        trace[-1].update(returncode=code, stdout=stdout, stderr=stderr)
        return dict(outcome=outcome, phase="run", trace=trace, input_hashes={"source.f90": generated.sha(raw)})

    def test_each_planned_failure_requires_current_complete_parent(self):
        vectors = 0
        for spec in self.specs.values():
            parent = self.probe_check(spec)
            for probe in spec["probes"] + spec["omissions"]:
                verdict = generated.probe_verdict(spec, probe, parent, self.probe_check(spec, probe),
                                                  parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                bad_parent = copy.deepcopy(parent)
                bad_parent["input_hashes"]["source.f90"] = "0" * 64
                blocked = generated.probe_verdict(spec, probe, bad_parent, self.probe_check(spec, probe),
                                                  parent_binding_current=True)
                self.assertFalse(blocked["qualified"])
                untested = generated.probe_verdict(spec, probe, parent, None, parent_binding_current=True)
                self.assertEqual((untested["status"], untested["qualified"]), ("UNTESTED", False))
                vectors += 3
        self.assertEqual(vectors, 246)

    def test_catalogue_sync_removes_only_s9_4_1_001_pending_entries_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        owner = next(row for row in catalogue["requirements"] if row["id"] == generated.RULE)
        self.assertEqual(owner.get("pending", {}), {})
        for facet in generated.FACETS:
            self.assertNotIn(facet, owner.get("pending", {}))
        for other in ("R908", "R909", "R910", "C908", "S9.4.1-002"):
            row = next(item for item in catalogue["requirements"] if item["id"] == other)
            self.assertTrue(row.get("pending"))
        self.assertIn(generated.ORACLE_PREFIX, owner["oracle"])
        self.assertIn(generated.LIMIT_PREFIX, owner["oracle_limitation"])
        self.assertNotIn("This is a source-only catalogue packet", owner["oracle_limitation"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("R908, R909, R910, C908 and\nS9.4.1-002 remain pending", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
