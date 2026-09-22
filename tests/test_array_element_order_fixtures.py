"""Runtime fixtures for Fortran 2023 array element order."""

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
import generate_array_element_order_fixtures as generated


class ArrayElementOrderFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_six_owned_f2023_runtime_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in generated.VARIANTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 12)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for _, facet in generated.VARIANTS.values()})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
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
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, evidence="positive-control")),
                                          self.registry.requirements[case.rule])
            for bad in (replace(case, meta=replace(case.meta, facets=[])),
                        replace(case, meta=replace(case.meta, facets=[case.meta.facets[0], "foreign"])),
                        replace(case, meta=replace(case.meta, facets=case.meta.facets * 2))):
                with self.assertRaises(SuiteError):
                    validate_case_requirement(bad, self.registry.requirements[case.rule])

    def test_sources_pin_headers_bounds_literals_and_hand_arithmetic(self):
        anchors = {
            "sequence_rank_two": [
                "! rule: S9.5.3.3-001\n! covers: array-elements-form-sequence\n",
                "integer :: a(2:4,-1:2)", "2049", "4052",
                "rank 2 sequence: j1=2,j2=-1,d1=3",
                "if (a(3,1) /= 3051)", "if (checks /= 12)"],
            "position_rank_two": [
                "! rule: S9.5.3.3-001\n! covers: position-determined-by-subscript-order-value\n",
                "integer :: a(5:7,20:23)", "rank 2 positions: j1=5,j2=20,d1=3",
                "(6,21) position 5", "(5,22) position 7", "if (a(5,22) /= 5072)"],
            "rank_one": [
                "! rule: S9.5.3.3-002\n! covers: rank-one-order-value\n",
                "integer :: a(3:7)", "rank 1: j1=3, s1=5 gives position 1+(5-3)=3",
                "if (a(5) /= 105)", "if (a(3) /= 103)", "if (a(7) /= 107)"],
            "rank_two": [
                "! rule: S9.5.3.3-002\n! covers: rank-two-order-value\n",
                "integer :: a(-2:1,4:6)", "rank 2 formula: j1=-2,j2=4,d1=4",
                "(0,5) position 7", "if (a(0,5) /= 55)"],
            "rank_three": [
                "! rule: S9.5.3.3-002\n! covers: rank-three-order-value\n",
                "integer :: a(-2:0,4:5,7:10)", "rank 3: j=(-2,4,7), d1=3, d2=2",
                "(-1,5,9) position 17", "if (a(-1,5,9) /= 90509)"],
            "rank_fifteen": [
                "! rule: S9.5.3.3-002\n! covers: rank-fifteen-pattern\n",
                "character(len=40) :: a(3:4,-2:-1,5:6, &",
                "rank 15: d1=d2=d3=d15=2 and d4..d14=1",
                "has Table 9.1 position 16", "(-4-(-5))*8 = 16",
                "if (a(4,-1,6,8,9,10,11,12,13,14, &",
                "'4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-4'"]
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
            self.assertRegex(source, r"(?im)^  data a / &")
            self.assertNotRegex(source, r"(?i)\b(reshape|pack|transfer|loc|c_loc|shape|size|lbound|ubound)\s*\(")
            self.assertNotRegex(source, r"(?i)\b(equivalence|common|pointer|target|allocatable|associate|coarray)\b")
            for needle in anchors[variant]:
                self.assertIn(needle, source)
            mutated = source.replace("! covers: " + spec["facets"][0], "! covers: foreign", 1)
            self.assertNotEqual(mutated, source)
            self.assertNotIn("! covers: " + spec["facets"][0] + "\n", mutated)

    def test_guard_probe_and_omission_spans_bind_complete_parent_sources(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 39)
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 39)
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
        self.assertEqual(vectors, 234)

    def test_catalogue_sync_removes_only_runtime_facets_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        self.assertEqual(set(by_rule["S9.5.3.3-001"].get("pending", {})), {"table9-1-is-formula-source"})
        self.assertEqual(set(by_rule["S9.5.3.3-002"].get("pending", {})), {"table-layout-ambiguity-recorded"})
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
        self.assertIn(generated.ORACLE_PREFIX_001, by_rule["S9.5.3.3-001"]["oracle"])
        self.assertIn(generated.ORACLE_PREFIX_002, by_rule["S9.5.3.3-002"]["oracle"])
        self.assertIn(generated.LIMIT_PREFIX_001, by_rule["S9.5.3.3-001"]["oracle_limitation"])
        self.assertIn(generated.LIMIT_PREFIX_002, by_rule["S9.5.3.3-002"]["oracle_limitation"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("`table9-1-is-formula-source` and `table-layout-ambiguity-recorded` remain pending", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
