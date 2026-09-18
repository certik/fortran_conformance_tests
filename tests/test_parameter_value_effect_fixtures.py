"""Actual PARAMETER subjects, independent literals and complete-parent sensitivity."""
import copy
from dataclasses import asdict, replace
import itertools
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from evidence_links import qualifying_reference
from execution_validation import validate_case_trace
from suite_data import Registry, SuiteError, render_requirement, validate_case_requirement, write_json


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_parameter_value_effect_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))
COUNTS = {"integer": 3, "logical": 2, "character_padding": 6,
          "character_truncation": 6, "array": 2, "scalar_array": 4}


class ParameterValueEffectFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}
        cls.transport_vectors = 0
        cls.probe_verdict_vectors = 0
        cls.generator_state_vectors = 0

    def test_exact_six_owned_f2023_runtime_effect_cases(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in COUNTS})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 12)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         set(generated.FACETS))
        for case in self.cases.values():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             (generated.RULE, "valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertFalse(case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
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

    def test_integer_and_logical_subjects_use_independent_values_not_initializer_or_representation_oracles(self):
        dependencies = self.registry.requirements[generated.RULE]["dependencies"]
        self.assertIn("16.9.122p3-p5", dependencies)
        self.assertIn("16.9.145p2-p5", dependencies)
        integer = self.specs[generated.identifier("integer")]
        source = integer["source"]
        self.assertIn("  integer :: first, second, remainder\n", source)
        self.assertIn("  parameter (first=3, second=7, remainder=mod(28,3))\n", source)
        self.assertEqual(source.count("mod("), 1)
        self.assertEqual([(row["expression"], row["expected"]) for row in integer["observations"]],
                         [("first", "3"), ("second", "7"), ("remainder", "1")])
        logical = self.specs[generated.identifier("logical")]
        self.assertIn("  logical :: yes, no\n  parameter (yes=.true., no=.false.)\n", logical["source"])
        self.assertEqual([(row["expression"], row["operator"], row["expected"])
                          for row in logical["observations"]],
                         [("yes", ".neqv.", ".true."), ("no", ".neqv.", ".false.")])
        self.assertEqual([row["replacement"] for row in logical["observations"]], [".false.", ".true."])
        self.assertNotRegex(logical["source"], r"(?i)\b(transfer|btest|iachar|int|kind)\s*\(")

    def test_character_oracles_include_lengths_positions_and_actual_assumed_length_constant(self):
        for variant, length, value in (("character_padding", 4, "AB  "), ("character_truncation", 2, "AB")):
            spec = self.specs[generated.identifier(variant)]
            self.assertIn(f"  character(len={length}) :: word\n", spec["source"])
            guards = {row["id"]: row for row in spec["observations"]}
            self.assertEqual((guards["length"]["expression"], guards["length"]["expected"]),
                             ("len(word)", str(length)))
            self.assertEqual((guards["whole-word"]["expression"], guards["whole-word"]["expected"]),
                             ("word", repr(value)))
            for index, character in enumerate(value, 1):
                self.assertEqual((guards[f"position-{index}"]["expression"],
                                  guards[f"position-{index}"]["expected"]),
                                 (f"word({index}:{index})", repr(character)))
            if variant == "character_padding":
                self.assertIn("  parameter (word='AB')\n", spec["source"])
                self.assertEqual(guards["position-3"]["expected"], "' '")
                self.assertEqual(guards["position-4"]["expected"], "' '")
            else:
                self.assertIn("  character(len=*) :: full_word\n", spec["source"])
                self.assertIn("  parameter (word='ABCDE', full_word='CDE')\n", spec["source"])
                self.assertEqual((guards["assumed-length"]["expression"], guards["assumed-length"]["expected"]),
                                 ("len(full_word)", "3"))
                self.assertEqual((guards["assumed-value"]["expression"], guards["assumed-value"]["expected"]),
                                 ("full_word", "'CDE'"))
            self.assertNotRegex(spec["source"], r"(?i)\b(transfer|iachar|achar|storage_size|kind)\s*\(")

    def test_explicit_arrays_observe_every_actual_element_with_literal_oracles(self):
        vector = self.specs[generated.identifier("array")]
        self.assertIn("  integer :: values(2)\n  parameter (values=[3,7])\n", vector["source"])
        self.assertEqual([(row["expression"], row["expected"]) for row in vector["observations"]],
                         [("values(1)", "3"), ("values(2)", "7")])
        matrix = self.specs[generated.identifier("scalar_array")]
        self.assertIn("  integer :: values(2,2)\n  parameter (values=5)\n", matrix["source"])
        self.assertEqual([(row["expression"], row["expected"]) for row in matrix["observations"]],
                         [("values(1,1)", "5"), ("values(2,1)", "5"),
                          ("values(1,2)", "5"), ("values(2,2)", "5")])
        for spec in (vector, matrix):
            body = spec["source"].split("contains\n", 1)[1]
            self.assertNotIn("[", body)
            self.assertNotRegex(body, r"(?i)\b(sum|product|all|reshape|rank|shape|size|lbound|ubound)\s*\(")
            self.assertNotRegex(spec["source"], r"(?im)^\s*values(?:\([^\n]*\))?\s*=")

    def test_complete_parent_counts_one_observer_all_checks_and_normal_completion(self):
        for spec in self.specs.values():
            source = spec["source"]
            main, body = source.split("contains\n", 1)
            self.assertEqual(main.count("  call observe\n"), 1)
            self.assertEqual(main.count("  returns=returns+1\n"), 1)
            self.assertTrue(body.startswith("  subroutine observe\n    implicit none\n    visits=visits+1\n"))
            self.assertEqual(body.count("observed_checks=observed_checks+1"), COUNTS[spec["variant"]])
            self.assertEqual(spec["observed_checks"], COUNTS[spec["variant"]])
            self.assertEqual(main.count("main_checks=main_checks+1"), 3)
            self.assertIn(f"if (observed_checks /= {COUNTS[spec['variant']]}) then", main)
            self.assertIn("if (main_checks /= 3) then", main)
            self.assertLess(main.index("if (visits /= 1)"), main.index("if (observed_checks /="))
            self.assertLess(main.index("if (observed_checks /="), main.index(spec["completion"].rstrip("\n")))
            self.assertNotRegex(source, r"(?im)^\s*(module|data|type|block|common|equivalence)\b")
            self.assertNotRegex(source, r"(?i)\b(pointer|allocatable|optional|target|volatile|"
                                       r"asynchronous|bind|allocate|deallocate|coarray)\b")
            self.assertNotIn("\r", source)
            self.assertNotIn(";", source)
            source.encode("ascii")
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertTrue(source.endswith("end program parameter_value_" + spec["variant"] + "_effect\n"))

    def test_every_guard_and_completion_has_one_exact_full_source_literal_mutation(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 53)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(len(spec["guards"]), COUNTS[spec["variant"]] + 5)
            self.assertEqual([row["id"] for row in spec["probes"]], [row["id"] for row in spec["guards"]])
            self.assertEqual(len(re.findall(r"(?m)^\s*error stop$", spec["source"])), len(spec["guards"]) - 1)
            declarations = raw.split(b"  visits=0\n", 1)[0]
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode(), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode() + raw[end:])
                self.assertNotEqual(mutant, raw)
                self.assertEqual(mutant.count(b"\n"), raw.count(b"\n"))
                self.assertTrue(mutant.startswith(declarations))
                self.assertEqual(mutant.count(b"call observe"), 1)
                if probe["kind"] == "guard":
                    self.assertEqual(probe["failure_stdout"], probe["failure_token"] + "\n")
                else:
                    self.assertEqual(probe["replacement"] + "\n", spec["completion"].replace(" OK", " BAD"))
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(dict(spec, source=spec["source"] + "\n"), spec["probes"][0])

    def test_omissions_remove_call_body_or_observation_with_count_and_bind_expected_caller_guard(self):
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 35)
        for spec in self.specs.values():
            raw = spec["source"].encode()
            plans = {row["id"]: row for row in spec["omissions"]}
            self.assertEqual(set(plans), {"omit-observer-call", "empty-observer-body"}
                             | {"omit-observation-" + row["id"] for row in spec["observations"]})
            for probe in plans.values():
                start, end = probe["span"]
                self.assertEqual(probe["expected"].encode(), raw[start:end])
                self.assertEqual(probe["replacement"], "")
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + raw[end:])
                self.assertEqual(mutant.split(b"  visits=0\n", 1)[0], raw.split(b"  visits=0\n", 1)[0])
                self.assertIn(spec["completion"].rstrip("\n").encode(), mutant)
                if probe["id"] == "omit-observer-call":
                    self.assertNotIn(b"call observe", mutant)
                elif probe["id"] == "empty-observer-body":
                    self.assertIn(b"subroutine observe\n    implicit none\n  end subroutine observe", mutant)
                else:
                    self.assertIn("observed_checks=observed_checks+1", probe["expected"])
                    self.assertEqual(mutant.count(b"observed_checks=observed_checks+1"),
                                     COUNTS[spec["variant"]] - 1)
                guard = "observed-checks" if probe["id"].startswith("omit-observation-") else "observer-visits"
                self.assertEqual(probe["failure_stdout"], f"PVE:{spec['variant']}:{guard}\n")

    def staged(self, case, family, mode, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic transport, not native calibration")
        source = (case.fixture.root / "source.f90").read_bytes()
        phases = []

        def transport(command, cwd, timeout, stdin=None):
            workspace = Path(cwd).resolve()
            self.assertEqual((timeout, stdin), (5, None))
            self.assertEqual((workspace / "source.f90").read_bytes(), source)
            phase = "compile" if "-c" in command else "link" if "-o" in command else "run"
            phases.append(phase)
            if phase == "compile":
                self.assertEqual(Path(command[command.index("-c") + 1]), workspace / "source.f90")
            if phase == "run":
                self.assertEqual(command, [str(workspace / "program")])
            code, stdout, stderr, timed_out = 0, "", "", False
            if fault == phase + "-failure":
                code, stderr = 1, "synthetic process failed"
            elif phase == "run":
                stdout = self.specs[case.name]["completion"]
                if fault == "no-op":
                    stdout = ""
                elif fault == "wrong-output":
                    stdout = stdout.replace(" OK", " BAD")
                elif fault == "extra-output":
                    stdout += "EXTRA\n"
                elif fault == "stderr":
                    stderr = "unexpected\n"
                elif fault == "guard":
                    code, stdout, stderr = 1, "PVE:wrong-guard\n", "ERROR STOP\n"
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timed_out = True
            elif fault == phase + "-internal":
                stderr = "ASR verify pass error\n"
            if phase != "run" and code == 0 and fault != "missing-" + phase + "-artifact":
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact, not native evidence")
            return runner.ProcessResult(code, stdout + stderr, timed_out, stdout, stderr,
                                        stdout.encode(), stderr.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual([row["phase"] for row in check.trace], phases)
        self.assertEqual(check.input_hashes, {"source.f90": generated.sha(source)})
        type(self).transport_vectors += 1
        return check, phases

    def test_real_staging_requires_compile_link_run_artifacts_and_exact_completion(self):
        for case, (family, mode) in itertools.product(self.cases.values(), FAMILIES):
            parent, phases = self.staged(case, family, mode)
            self.assertEqual((parent.outcome, parent.phase, phases), ("pass", "run", ["compile", "link", "run"]))
            self.assertEqual(qualifying_reference(case, dict(outcome="pass", phase="run", standard=mode)),
                             mode == "f2023")
            for fault in ("no-op", "wrong-output", "extra-output", "stderr", "guard", "crash", "timeout",
                          "compile-failure", "link-failure", "run-failure", "compile-internal", "link-internal",
                          "missing-compile-artifact", "missing-link-artifact"):
                with self.subTest(case=case.name, family=family, fault=fault):
                    check, phases = self.staged(case, family, mode, fault)
                    self.assertEqual(check.outcome, "fail")
                    if fault.startswith(("compile-", "link-", "missing-")):
                        self.assertNotIn("run", phases)

    def probe_check(self, spec, probe=None):
        raw = spec["source"].encode() if probe is None else generated.wrong_oracle_source(spec, probe)
        stdout = spec["completion"] if probe is None else (
            probe["replacement"] + "\n" if probe["kind"] == "output" else probe["failure_stdout"])
        code = 0 if probe is None or probe["kind"] == "output" else 2
        trace = [dict(phase=phase, returncode=0, timed_out=False, stdout="", stderr="")
                 for phase in ("compile", "link", "run")]
        trace[-1].update(returncode=code, stdout=stdout, stderr="" if code == 0 else "ERROR STOP\n")
        return dict(outcome="pass" if probe is None else "fail", phase="run", trace=trace,
                    input_hashes={"source.f90": generated.sha(raw)})

    def test_sensitivity_requires_current_complete_passing_parent_and_intended_failure(self):
        for spec in self.specs.values():
            for probe in spec["probes"] + spec["omissions"]:
                parent, observed = self.probe_check(spec), self.probe_check(spec, probe)
                verdict = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                type(self).probe_verdict_vectors += 1
                failed, preempted = copy.deepcopy(parent), copy.deepcopy(observed)
                failed["outcome"] = "fail"
                for check in (failed, preempted):
                    check["trace"][-1].update(returncode=1, stdout="PVE:earlier-parent-guard\n", stderr="ERROR STOP\n")
                verdict = generated.probe_verdict(spec, probe, failed, preempted, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("parent-preempted", False))
                type(self).probe_verdict_vectors += 1
                for fault in ("parent-stale", "parent-failed", "parent-not-run", "parent-no-trace", "parent-wrong-input",
                              "probe-compile-blocked", "probe-link-blocked", "probe-wrong-input", "wrong-guard",
                              "extra-output", "compile-internal", "resource-failure", "crash", "timeout",
                              "probe-passed", "probe-untested"):
                    good, changed, current = copy.deepcopy(parent), copy.deepcopy(observed), True
                    if fault == "parent-stale":
                        current = False
                    elif fault == "parent-failed":
                        good["outcome"] = "fail"
                    elif fault == "parent-not-run":
                        good["phase"] = "compile"
                    elif fault == "parent-no-trace":
                        good["trace"] = []
                    elif fault == "parent-wrong-input":
                        good["input_hashes"]["source.f90"] = "0" * 64
                    elif fault == "probe-compile-blocked":
                        changed.update(phase="compile", trace=changed["trace"][:1])
                    elif fault == "probe-link-blocked":
                        changed.update(phase="link", trace=changed["trace"][:2])
                    elif fault == "probe-wrong-input":
                        changed["input_hashes"]["source.f90"] = "0" * 64
                    elif fault == "wrong-guard":
                        changed["trace"][-1]["stdout"] = "PVE:wrong-guard\n"
                    elif fault == "extra-output":
                        changed["trace"][-1]["stdout"] += "EXTRA\n"
                    elif fault == "compile-internal":
                        changed["trace"][0]["stderr"] = "ASR verify pass error\n"
                    elif fault == "resource-failure":
                        changed["trace"][-1]["stderr"] = "out of memory\n"
                    elif fault == "crash":
                        changed["trace"][-1]["returncode"] = -11
                    elif fault == "timeout":
                        changed["trace"][-1]["timed_out"] = True
                    elif fault == "probe-passed":
                        changed["outcome"] = "pass"
                    else:
                        changed = None
                    with self.subTest(case=spec["id"], probe=probe["id"], fault=fault):
                        verdict = generated.probe_verdict(spec, probe, good, changed, parent_binding_current=current)
                        self.assertFalse(verdict["qualified"])
                        if changed is None:
                            self.assertEqual(verdict["status"], "UNTESTED")
                    type(self).probe_verdict_vectors += 1

    def test_source_output_role_and_complete_requirement_changes_stale_snapshots(self):
        for original, mutation in itertools.product(self.cases.values(), ("source", "output", "role", "requirement")):
            registry = Registry(ROOT)
            fingerprint = original.fingerprint(registry)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest = root / "fixture.json"
                manifest.write_bytes(original.fixture.path.read_bytes())
                (root / "source.f90").write_bytes((original.fixture.root / "source.f90").read_bytes())

                def current_cases(*args, **kwargs):
                    fixture = runner.load_fixture(manifest, runner.PROFILES)
                    changed = replace(original, path=str(manifest), fixture=fixture, meta=fixture.meta)
                    return [changed if case.name == original.name else case for case in self.all_cases]

                with patch.object(runner, "Registry", return_value=registry), \
                        patch.object(runner, "collect_cases", side_effect=current_cases):
                    self.assertEqual(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}), [])
                    data = json.loads(manifest.read_text())
                    if mutation == "source":
                        (root / "source.f90").write_bytes((root / "source.f90").read_bytes() + b"\n")
                    elif mutation == "output":
                        data["expect"]["stdout"] += "EXTRA\n"
                    elif mutation == "role":
                        data["evidence"] = "positive-control"
                    else:
                        registry.requirements[generated.RULE]["oracle_limitation"] += " Changed current source gate."
                    write_json(manifest, data)
                    self.assertTrue(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}))

    def test_unselected_pending_control_and_raw_review_states_are_not_overwritten(self):
        original = self.registry.catalogues[generated.SECTION]
        unselected = sorted(set(self.registry.requirements[generated.RULE]["facets"]) - set(generated.FACETS))
        self.assertEqual(set(unselected), {"simple-derived-values", "numeric-kind-and-BOZ-oracle-gates"})
        for selected_mask, mask, foreign_state, review_state in itertools.product(
                range(64), range(4), ("all", "partial", "none"), ("draft", "reviewed", "stale")):
            data = copy.deepcopy(original)
            owner = next(row for row in data["requirements"] if row["id"] == generated.RULE)
            for bit, facet in enumerate(generated.FACETS):
                if selected_mask & (1 << bit):
                    owner["pending"][facet] = "Selected independently revised plan."
            for bit, facet in enumerate(unselected):
                if mask & (1 << bit):
                    owner["pending"][facet] = "Foreign exact plan: " + facet
                else:
                    owner["pending"].pop(facet, None)
            owner["positive_control_facets"] = [unselected[0]]
            owner["oracle"] += "\n\nForeign exact oracle paragraph."
            owner["oracle_limitation"] += "\n\nForeign exact limitation paragraph."
            for row in data["requirements"]:
                if row["id"] == generated.RULE:
                    continue
                row["pending"] = {facet: "Foreign pending: " + facet for facet in row["facets"]}
                if foreign_state == "partial":
                    row["pending"].pop(row["facets"][0])
                elif foreign_state == "none":
                    row["pending"] = {}
            data.update(review_state="draft" if review_state == "draft" else "reviewed",
                        review_fingerprint=("0" if review_state == "stale" else "1") * 64,
                        review_rationale="Synthetic raw lifecycle state, never a disk review.")
            before, expected = copy.deepcopy(data), copy.deepcopy(data)
            target = next(row for row in expected["requirements"] if row["id"] == generated.RULE)
            for facet in generated.FACETS:
                target["pending"].pop(facet, None)
            actual = generated.synced_catalogue(data)
            self.assertEqual(data, before)
            self.assertEqual(actual, expected)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            view = generated.render_view(actual)
            self.assertTrue(all(render_requirement(row) in view for row in actual["requirements"]))
            self.assertNotIn("No cases are implemented here.", view)
            self.assertIn('Registry.catalogue_review_state("8.6.11")', view)
            type(self).generator_state_vectors += 1
        self.assertEqual(self.generator_state_vectors, 2304)

    def test_selected_definitions_roles_and_unique_owned_paragraphs_are_required(self):
        for facet in generated.FACETS:
            for mutation in ("missing", "control"):
                data = copy.deepcopy(self.registry.catalogues[generated.SECTION])
                owner = next(row for row in data["requirements"] if row["id"] == generated.RULE)
                if mutation == "missing":
                    owner["facets"].remove(facet)
                else:
                    owner["positive_control_facets"] = [facet]
                before = copy.deepcopy(data)
                with self.assertRaisesRegex(ValueError, "selected PARAMETER value"):
                    generated.synced_catalogue(data)
                self.assertEqual(data, before)
        data = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        owner = next(row for row in data["requirements"] if row["id"] == generated.RULE)
        owner["oracle"] = "Foreign first.\n\n" + generated.ORACLE_PREFIX + "old.\n\nForeign last."
        owner["oracle_limitation"] = "Foreign limit."
        target = next(row for row in generated.synced_catalogue(data)["requirements"] if row["id"] == generated.RULE)
        self.assertEqual(target["oracle"], "Foreign first.\n\n" + generated.ORACLE + "\n\nForeign last.")
        self.assertEqual(target["oracle_limitation"], "Foreign limit.\n\n" + generated.LIMITATION)
        owner["oracle"] += "\n\n" + generated.ORACLE_PREFIX + "duplicate."
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            generated.synced_catalogue(data)
        with self.assertRaisesRegex(ValueError, "unknown PARAMETER"):
            generated.identifier("unowned")
        with self.assertRaisesRegex(ValueError, "unknown PARAMETER"):
            generated.program("unowned")

    def test_raw_source_lifecycle_and_foreign_inventory_blockers_are_not_renewed(self):
        registry = Registry(ROOT)
        disk = copy.deepcopy((registry.catalogues, registry.reviews, registry.evidence.data,
                              registry.source_uses.data, registry.execution.data))
        original = copy.deepcopy(registry.catalogues[generated.SECTION])
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original)
            registry.catalogues[generated.SECTION] = candidate
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory lifecycle only."
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint(generated.SECTION)
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
        before = registry.execution.snapshot(self.all_cases)
        foreign = next(case for case in self.all_cases if case.name not in self.cases and case.review_key in registry.reviews)
        registry.reviews[foreign.review_key] = dict(
            registry.reviews[foreign.review_key], state="unreviewed", rationale="Synthetic independent foreign blocker.")
        for case in self.cases.values():
            registry.reviews[case.review_key] = dict(
                state="source-reviewed", fingerprint=case.fingerprint(registry), sources=["8.6.11#p4"],
                rationale="Synthetic owner-only state, not an actual approval.")
        for report in registry.execution.report(self.all_cases, include_members=False):
            registry.execution.aggregates[report["id"]]["review"].update(
                state="source-reviewed", fingerprint=report["review"]["fingerprint"],
                rationale="Synthetic matching receipt does not erase blockers.")
        for report in registry.execution.report(self.all_cases):
            self.assertEqual({row["id"] for row in report["members"]}, {case.name for case in self.all_cases})
            self.assertEqual(report["member_count"], len(self.all_cases))
            self.assertEqual(report["state"], "stale")
            self.assertIn(foreign.name + ": fixture review is unreviewed", report["blockers"])
        with patch.object(runner, "Registry", return_value=registry), \
                patch.object(runner, "collect_cases", return_value=self.all_cases):
            self.assertTrue(runner.confirm_snapshot([], [], {}, execution_snapshot=before))
        fresh = Registry(ROOT)
        self.assertEqual((fresh.catalogues, fresh.reviews, fresh.evidence.data, fresh.source_uses.data,
                          fresh.execution.data), disk)

    def test_generation_preserves_foreign_narrative_and_check_mode_never_writes(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        self.assertEqual(generated.render_view(self.registry.catalogues[generated.SECTION]),
                         (ROOT / generated.VIEW).read_text())
        self.registry.render()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            catalogue = json.loads((root / generated.CATALOGUE).read_text())
            owner = next(row for row in catalogue["requirements"] if row["id"] == generated.RULE)
            owner["pending"].pop("simple-derived-values")
            owner["positive_control_facets"] = ["simple-derived-values"]
            write_json(root / generated.CATALOGUE, catalogue)
            view = root / generated.VIEW
            view.write_text(view.read_text().replace(
                "The canonical record is", "Foreign exact narrative.\n\nThe canonical record is"))
            foreign = root / "tests/fixtures/parameter_value_foreign/source.f90"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("Unrelated bytes, not a selected Fortran case.\n")
            generated.generate(root, sync_catalogue=True)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not invoke a compiler")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)
            self.assertEqual(view.read_text().count("Foreign exact narrative."), 1)
            source = root / "tests/fixtures/parameter_value_effect_integer/source.f90"
            source.write_bytes(source.read_bytes() + b"\n")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, "stale PARAMETER value family"):
                generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
