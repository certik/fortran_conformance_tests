"""Complete SAVE parents, every oracle activation, and independently managed source state."""
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
import generate_save_local_effect_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class SaveLocalEffectFixturesTests(unittest.TestCase):
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

    def test_exact_two_owned_run_effect_cases_and_no_other_facet_credit(self):
        self.assertEqual(set(self.cases), {
            "S8_5_16_001_valid__save_local_effect_return",
            "S8_5_16_001_valid__save_local_effect_recursive",
        })
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 4)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, set(generated.FACETS))
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

    def test_actual_saved_local_without_declaration_initialization_or_confounding_entities(self):
        for spec in self.specs.values():
            source = spec["source"]
            main, body = source.split("contains\n", 1)
            self.assertEqual(body.count("    integer, save :: kept\n"), 1)
            self.assertNotRegex(source, r"(?im)^\s*integer[^\n]*::[^\n]*=")
            self.assertNotRegex(source, r"(?im)^\s*(data|module|block|common|equivalence|type|character)\b")
            self.assertNotRegex(source, r"(?i)\b(pointer|allocatable|optional|value|target|contiguous|"
                                       r"asynchronous|volatile|bind|allocate|deallocate|thread|coarray)\b")
            self.assertNotIn("[", source)
            self.assertNotIn("\r", source)
            self.assertNotIn(";", source)
            source.encode("ascii")
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertNotIn("kept", main)
            self.assertNotRegex(source, r"(?im)^\s*call [^\n]*\bkept\b")
            self.assertIn("    integer :: activation\n", body)
            self.assertIn("    entries=entries+1\n    activation=entries\n", body)
            self.assertLess(body.index("kept=11"), body.index("if (kept"))
            self.assertTrue(source.endswith("end program save_local_" + spec["variant"] + "_effect\n"))

    def test_return_parent_has_three_actual_returns_and_independent_literal_snapshots(self):
        spec = self.specs[generated.identifier("return")]
        source = spec["source"]
        main, body = source.split("contains\n", 1)
        self.assertTrue(body.startswith("  subroutine visit(phase, expected_phase, expected_entry,"))
        self.assertIn("    integer, intent(out) :: snapshot\n", body)
        self.assertIn("    integer, intent(inout) :: entries, exits, checks\n", body)
        self.assertEqual(re.findall(r"call visit\((\d), (\d), (\d),", main),
                         [("1", "1", "1"), ("2", "2", "2"), ("3", "3", "3")])
        self.assertEqual(body.count("      return\n"), 3)
        self.assertEqual(main.count("  returns=returns+1\n"), 3)
        self.assertEqual(body.count("      snapshot=kept\n      exits=exits+1\n      return\n"), 3)
        self.assertIn("    end if\n    exits=exits+1\n  end subroutine visit\n", body)
        first, rest = body.split("    else if (phase == 2) then\n")
        second, third = rest.split("    else\n")
        self.assertIn("kept=11", first)
        self.assertLess(second.index("if (kept /= 11)"), second.index("kept=17"))
        self.assertIn("if (kept /= 17)", third)
        self.assertNotRegex(third, r"(?m)^\s*kept=")
        guards = {row["id"]: row for row in spec["guards"]}
        for phase, value, checks in ((1, 11, 3), (2, 17, 7), (3, 17, 11)):
            for field in ("entries", "exits", "returns"):
                self.assertEqual(guards[f"after-{phase}-{field}"]["expected"], str(phase))
            self.assertEqual(guards[f"after-{phase}-snapshot"]["expected"], str(value))
            self.assertEqual(guards[f"after-{phase}-local-checks"]["expected"], str(checks))
            self.assertIn(f"  snapshot=-{phase}\n  call visit({phase},", main)
        self.assertEqual(main.count("main_checks=main_checks+1"), 15)
        self.assertEqual(guards["main-check-total"]["expected"], "15")

    def test_recursive_parent_observes_same_saved_entity_with_outer_instance_still_active(self):
        spec = self.specs[generated.identifier("recursive")]
        main, body = spec["source"].split("contains\n", 1)
        self.assertTrue(body.startswith("  recursive subroutine share("))
        self.assertEqual(re.findall(r"call share\((\d), (\d), (\d),", spec["source"]),
                         [("0", "0", "1"), ("1", "1", "2")])
        outer, inner = body.split("    else\n")
        self.assertLess(outer.index("kept=11"), outer.index("call share(1, 1, 2"))
        self.assertLess(outer.index("call share(1, 1, 2"), outer.index("if (kept /= 17)"))
        self.assertIn("      child_returns=child_returns+1\n", outer)
        self.assertIn("      before_snapshot=kept\n", outer)
        self.assertIn("      after_snapshot=kept\n", outer)
        self.assertLess(inner.index("if (kept /= 11)"), inner.index("kept=17"))
        self.assertIn("      inner_snapshot=kept\n      kept=17\n", inner)
        self.assertIn("      return\n", inner)
        self.assertEqual(body.count("      return\n"), 2)
        self.assertIn("    end if\n    exits=exits+1\n  end subroutine share\n", body)
        self.assertNotIn("call share", inner)
        self.assertIn("    integer, intent(inout) :: before_snapshot, inner_snapshot, after_snapshot\n", body)
        self.assertNotIn("intent(out)", body)
        guards = {row["id"]: row for row in spec["guards"]}
        expected = {"caller-entries": 2, "caller-exits": 2, "caller-child-returns": 1,
                    "caller-outer-returns": 1, "caller-before-snapshot": 11, "caller-inner-snapshot": 11,
                    "caller-after-snapshot": 17, "caller-local-checks": 12, "main-check-total": 8}
        for name, literal in expected.items():
            self.assertEqual(guards[name]["expected"], str(literal))
        self.assertEqual(main.count("main_checks=main_checks+1"), 8)
        self.assertEqual(guards["outer-shared"]["expression"], "kept")
        self.assertEqual(guards["outer-shared"]["activation"], 1)
        self.assertEqual(guards["inner-shared"]["expression"], "kept")
        self.assertEqual(guards["inner-shared"]["activation"], 2)

    def test_every_guard_and_dynamic_activation_has_one_span_whole_program_probe(self):
        for variant, guard_count, probe_count, activations in (
                ("return", 24, 28, (1, 2, 3)), ("recursive", 20, 22, (1, 2))):
            spec = self.specs[generated.identifier(variant)]
            raw = spec["source"].encode("ascii")
            self.assertEqual((len(spec["guards"]), len(spec["probes"])), (guard_count, probe_count))
            self.assertEqual(len({row["id"] for row in spec["probes"]}), probe_count)
            self.assertEqual(len(re.findall(r"(?m)^\s*error stop$", spec["source"])), guard_count - 1)
            self.assertEqual(len(re.findall(r"(?m)^\s*if \(.*/= .*?\) then$", spec["source"])), guard_count - 1)
            for guard in spec["guards"]:
                probes = [row for row in spec["probes"] if row["guard_id"] == guard["id"]]
                self.assertEqual({row["activation"] for row in probes}, set(guard["activations"]))
                if guard["call_site"]:
                    self.assertEqual(guard["activations"], list(activations))
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode(), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode() + raw[end:])
                self.assertNotEqual(mutant, raw)
                self.assertEqual(mutant.count(b"\n"), raw.count(b"\n"))
                self.assertIn(b"integer, save :: kept\n", mutant)
                self.assertEqual(mutant.count(b"kept=11"), raw.count(b"kept=11"))
                self.assertEqual(mutant.count(b"kept=17"), raw.count(b"kept=17"))
                self.assertEqual(mutant.count(b"      return\n"), raw.count(b"      return\n"))
                if probe["kind"] == "guard":
                    self.assertEqual(int(probe["replacement"]), int(probe["expected"]) + 1)
                    suffix = "" if probe["activation"] is None else f":activation={probe['activation']}"
                    self.assertEqual(probe["failure_stdout"], probe["failure_token"] + suffix + "\n")
                else:
                    self.assertEqual(probe["replacement"] + "\n", spec["completion"].replace(" OK", " BAD"))
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(dict(spec, source=spec["source"] + "\n"), spec["probes"][0])

    def staged(self, case, family, mode, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic transport, not compiler calibration")
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
            code, stdout, stderr, timeout_flag = 0, "", "", False
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
                    code, stdout, stderr = 1, "SLE:wrong-guard\n", "ERROR STOP\n"
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timeout_flag = True
            elif fault == phase + "-internal":
                stderr = "ASR verify pass error\n"
            if phase != "run" and code == 0 and fault != "missing-" + phase + "-artifact":
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact, not native evidence")
            return runner.ProcessResult(code, stdout + stderr, timeout_flag, stdout, stderr, stdout.encode(), stderr.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual([row["phase"] for row in check.trace], phases)
        self.assertEqual(check.input_hashes, {"source.f90": generated.sha(source)})
        type(self).transport_vectors += 1
        return check, phases

    def test_real_staging_requires_compile_link_run_artifacts_and_exact_parent_completion(self):
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

    def test_sensitivity_requires_current_passing_complete_parent_and_exact_guard_activation(self):
        for spec in self.specs.values():
            for probe in spec["probes"]:
                parent, observed = self.probe_check(spec), self.probe_check(spec, probe)
                verdict = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                type(self).probe_verdict_vectors += 1
                failed, preempted = copy.deepcopy(parent), copy.deepcopy(observed)
                failed["outcome"] = "fail"
                for check in (failed, preempted):
                    check["trace"][-1].update(returncode=1, stdout="SLE:earlier-parent-guard\n", stderr="ERROR STOP\n")
                verdict = generated.probe_verdict(spec, probe, failed, preempted, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("parent-preempted", False))
                type(self).probe_verdict_vectors += 1
                for fault in ("parent-stale", "parent-failed", "parent-not-run", "parent-no-trace", "parent-wrong-input",
                              "probe-compile-blocked", "probe-link-blocked", "probe-wrong-input", "wrong-guard",
                              "wrong-activation", "compile-internal", "resource-failure", "crash", "timeout",
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
                        changed["trace"][-1]["stdout"] = "SLE:wrong-guard\n"
                    elif fault == "wrong-activation":
                        changed["trace"][-1]["stdout"] += "activation=wrong\n"
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

    def test_source_output_role_and_full_requirement_changes_stale_snapshots(self):
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

    def test_every_unselected_pending_subset_and_foreign_control_review_state_is_preserved(self):
        original = self.registry.catalogues[generated.SECTION]
        unselected = sorted(set(self.registry.requirements[generated.RULE]["facets"]) - set(generated.FACETS))
        expected_vectors = 4 * (1 << len(unselected)) * 3 * 3
        for selected_mask, mask, foreign_state, review_state in itertools.product(
                range(4), range(1 << len(unselected)), ("all", "partial", "none"), ("draft", "reviewed", "stale")):
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
            if unselected:
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
            self.assertNotIn("All 32 new facets are PENDING", view)
            self.assertNotIn("12 requirements and 90 pending facets", view)
            self.assertIn('Registry.catalogue_review_state("8.5.16")', view)
            type(self).generator_state_vectors += 1
        self.assertEqual(self.generator_state_vectors, expected_vectors)

    def test_selected_definitions_and_unique_owned_paragraphs_are_required_without_mutation(self):
        for facet in generated.FACETS:
            data = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in data["requirements"] if row["id"] == generated.RULE)
            owner["facets"].remove(facet)
            before = copy.deepcopy(data)
            with self.assertRaisesRegex(ValueError, "selected saved-local effect definitions"):
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

    def test_source_lifecycle_and_full_unselected_case_blockers_are_not_renewed(self):
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
                state="source-reviewed", fingerprint=case.fingerprint(registry), sources=["8.5.16#p1"],
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

    def test_standalone_generation_validates_owned_rules_and_keeps_foreign_cases_and_narrative(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in catalogue["requirements"] if row["id"] == generated.RULE)
            foreign_facet = next(facet for facet in owner["facets"] if facet not in generated.FACETS)
            owner["pending"].pop(foreign_facet, None)
            owner["positive_control_facets"] = [foreign_facet]
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            write_json(root / generated.CATALOGUE, catalogue)
            view = root / generated.VIEW
            view.write_text(view.read_text().replace(
                "## Source and decomposition\n", "## Source and decomposition\n\nForeign exact narrative.\n"))
            generated.generate(root, sync_catalogue=True)
            foreign = root / "tests/fixtures/save_local_effect_foreign"
            foreign.mkdir()
            parent = self.specs[generated.identifier("return")]
            manifest = copy.deepcopy(parent["manifest"])
            manifest.update(id="S8_5_16_001_valid__foreign_save_owner", facets=[foreign_facet], evidence="positive-control")
            write_json(foreign / "fixture.json", manifest)
            (foreign / "source.f90").write_text(parent["source"])
            write_json(root / "reviews.json", dict(schema_version=1, fixtures={}))
            fixtures = [runner.load_fixture(path, runner.PROFILES) for path in root.rglob("fixture.json")]
            self.assertEqual({fixture.name for fixture in fixtures}, set(self.cases) | {manifest["id"]})
            for fixture in fixtures:
                case = runner.SuiteCase(fixture.name, fixture.rule, fixture.kind, str(fixture.path),
                                        fixture.meta, fixture.name, fixture=fixture)
                validate_case_requirement(case, owner)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not invoke a compiler")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)
            self.assertEqual(view.read_text().count("Foreign exact narrative."), 1)
            self.assertTrue(all(render_requirement(row) in view.read_text() for row in catalogue["requirements"]))

    def test_generated_sources_manifests_and_view_are_exact_and_check_mode_never_writes(self):
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
            generated.generate(root, sync_catalogue=True)
            source = root / "tests/fixtures/save_local_effect_return/source.f90"
            source.write_bytes(source.read_bytes() + b"\n")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, "stale saved-local effect family"):
                generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
