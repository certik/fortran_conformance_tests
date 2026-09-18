"""Complete DATA subjects, reached observations and safe full-program mutations."""
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
import generate_data_position_effect_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class DataPositionEffectFixturesTests(unittest.TestCase):
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

    def test_exact_three_owned_f2023_runtime_effect_cases(self):
        self.assertEqual(set(self.cases), {generated.identifier(v) for v in ("scalar", "array", "nonexecution")})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 6)
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

    def test_scalar_and_array_oracles_observe_actual_independently_initialized_subjects(self):
        scalar = self.specs[generated.identifier("scalar")]
        self.assertIn("  integer :: i, j, k, checks\n  data i,j,k /11,22,33/\n", scalar["source"])
        self.assertEqual([(g["expression"], g["expected"]) for g in scalar["observations"]],
                         [("i", "11"), ("j", "22"), ("k", "33")])
        self.assertEqual(scalar["source"].count("checks=checks+1"), 3)
        self.assertIn("if (checks /= 3)", scalar["source"])
        self.assertNotRegex(scalar["source"], r"(?im)^\s*[ijk]\s*=")
        array = self.specs[generated.identifier("array")]
        self.assertIn("  integer :: a(2,3), checks\n  data a /11,21,12,22,13,23/\n", array["source"])
        expected = [("a(1,1)", "11"), ("a(2,1)", "21"), ("a(1,2)", "12"),
                    ("a(2,2)", "22"), ("a(1,3)", "13"), ("a(2,3)", "23")]
        self.assertEqual([(g["expression"], g["expected"]) for g in array["observations"]], expected)
        self.assertEqual([1 + (i - 1) + 2 * (j - 1) for i, j in ((1, 1), (2, 1), (1, 2),
                                                                  (2, 2), (1, 3), (2, 3))],
                         [1, 2, 3, 4, 5, 6])
        self.assertEqual(array["source"].count("checks=checks+1"), 6)
        self.assertIn("if (checks /= 6)", array["source"])
        self.assertNotRegex(array["source"], r"(?im)^\s*a(?:\([^\n]*\))?\s*=")
        for spec in (scalar, array):
            self.assertNotRegex(spec["source"], r"(?i)\b(reshape|sum|product|all|transfer)\s*\(")
            self.assertNotIn("contains", spec["source"])
            self.assertNotIn("[", spec["source"])

    def test_nonexecution_reads_explicit_local_before_return_and_physical_data_statement(self):
        spec = self.specs[generated.identifier("nonexecution")]
        main, body = spec["source"].split("contains\n", 1)
        self.assertIn("  observed=-1\n", main)
        self.assertEqual(main.count("observed=read_kept()"), 1)
        self.assertIn("  returns=returns+1\n", main)
        self.assertTrue(body.startswith(
            "  integer function read_kept() result(value)\n    implicit none\n    integer :: kept\n"))
        self.assertNotIn("kept", main.replace("read_kept", "function"))
        self.assertLess(body.index("integer :: kept"), body.index("if (kept /= 7)"))
        self.assertLess(body.index("if (kept /= 7)"), body.index("value=kept"))
        self.assertLess(body.index("value=kept"), body.index("    return\n"))
        self.assertIn("    return\n    data kept /7/\n    after_data=after_data+1\n", body)
        self.assertNotRegex(body, r"(?im)^\s*kept\s*=")
        self.assertNotIn("data value", body)
        self.assertNotIn("data read_kept", body)
        guards = {g["id"]: g for g in spec["guards"]}
        expected = {"function-entries": 1, "before-return-events": 1, "normal-returns": 1,
                    "body-checks": 1, "returned-value": 7, "after-data-events": 0, "check-total": 6}
        for name, value in expected.items():
            self.assertEqual(guards[name]["expected"], str(value))
        self.assertEqual(main.count("checks=checks+1"), 6)
        self.assertEqual(body.count("body_checks=body_checks+1"), 1)
        self.assertNotRegex(spec["source"], r"(?im)^\s*integer[^\n]*::[^\n]*=")

    def test_all_complete_sources_are_small_ordinary_defined_integer_contexts(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertNotIn(";", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertNotRegex(source, r"(?im)^\s*(module|common|equivalence|type|character|real|logical)\b")
            self.assertNotRegex(source, r"(?i)\b(pointer|allocatable|optional|target|volatile|"
                                       r"asynchronous|bind|allocate|deallocate|coarray|parameter)\b")
            self.assertEqual(len(re.findall(r"(?im)^[ \t]*data ", source)), 1)
            self.assertTrue(source.endswith("end program data_position_" + spec["variant"] + "_effect\n"))

    def test_every_guard_and_completion_mutation_preserves_the_data_initialization(self):
        self.assertEqual(sum(len(spec["probes"]) for spec in self.specs.values()), 22)
        for spec in self.specs.values():
            raw = spec["source"].encode()
            data = re.findall(rb"(?im)^[ \t]*data [^\n]+", raw)
            self.assertEqual([p["id"] for p in spec["probes"]], [g["id"] for g in spec["guards"]])
            self.assertEqual(len(re.findall(r"(?m)^\s*error stop$", spec["source"])), len(spec["guards"]) - 1)
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode(), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode() + raw[end:])
                self.assertNotEqual(mutant, raw)
                self.assertEqual(mutant.count(b"\n"), raw.count(b"\n"))
                self.assertEqual(re.findall(rb"(?im)^[ \t]*data [^\n]+", mutant), data)
                if probe["kind"] == "guard":
                    self.assertEqual(int(probe["replacement"]), int(probe["expected"]) + 1)
                    self.assertEqual(probe["failure_stdout"], probe["failure_token"] + "\n")
                else:
                    self.assertEqual(probe["replacement"] + "\n", spec["completion"].replace(" OK", " BAD"))
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(dict(spec, source=spec["source"] + "\n"), spec["probes"][0])

    def test_omissions_keep_defined_subjects_results_and_reach_specific_lifecycle_guards(self):
        self.assertEqual(sum(len(spec["omissions"]) for spec in self.specs.values()), 21)
        for spec in self.specs.values():
            raw = spec["source"].encode()
            data = re.findall(rb"(?im)^[ \t]*data [^\n]+", raw)
            for probe in spec["omissions"]:
                start, end = probe["span"]
                self.assertEqual(probe["expected"].encode(), raw[start:end])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode() + raw[end:])
                self.assertEqual(re.findall(rb"(?im)^[ \t]*data [^\n]+", mutant), data)
                self.assertIn(spec["completion"].rstrip("\n").encode(), mutant)
                if probe["id"] == "defined-noop-function":
                    body = mutant.decode().split("contains\n", 1)[1]
                    self.assertIn("    integer :: kept\n    value=-1\n    return\n    data kept /7/\n", body)
                    self.assertNotIn("value=kept", body)
                    self.assertEqual(probe["failure_stdout"], "DPE:nonexecution:function-entries\n")
                elif probe["id"] == "omit-function-call":
                    self.assertNotIn(b"observed=read_kept()", mutant)
                    self.assertIn(b"observed=-1", mutant)
                    self.assertEqual(probe["failure_stdout"], "DPE:nonexecution:function-entries\n")
                elif probe["id"] == "omit-explicit-return":
                    self.assertNotIn(b"    return\n", mutant)
                    self.assertIn(b"value=kept", mutant)
                    self.assertIn(b"data kept /7/\n    after_data=after_data+1", mutant)
                    self.assertEqual(probe["failure_stdout"], "DPE:nonexecution:after-data-events\n")
                elif probe["id"] == "omit-local-observation":
                    self.assertEqual(probe["failure_stdout"], "DPE:nonexecution:body-checks\n")
                else:
                    self.assertEqual(probe["failure_stdout"], f"DPE:{spec['variant']}:check-total\n")

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
            code, stdout, stderr, timed_out = 0, "", "", False
            if fault == phase + "-failure":
                code, stderr = 1, "synthetic process failed"
            elif phase == "run":
                self.assertEqual(command, [str(workspace / "program")])
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
                    code, stdout, stderr = 1, "DPE:wrong-guard\n", "ERROR STOP\n"
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timed_out = True
            elif fault == phase + "-internal":
                stderr = "ASR verify pass error\n"
            elif phase == "compile" and fault == "obsolescent-warning":
                stderr = "Warning: Obsolescent feature: DATA statement after executable statement\n"
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

    def test_staging_requires_complete_parent_and_does_not_turn_obsolescence_into_invalidity(self):
        for case, (family, mode) in itertools.product(self.cases.values(), FAMILIES):
            for fault in (None, "obsolescent-warning"):
                parent, phases = self.staged(case, family, mode, fault)
                self.assertEqual((parent.outcome, parent.phase, phases), ("pass", "run", ["compile", "link", "run"]))
                self.assertEqual(qualifying_reference(case, dict(outcome="pass", phase="run", standard=mode)),
                                 mode == "f2023")
            for fault in ("no-op", "wrong-output", "extra-output", "stderr", "guard", "crash", "timeout",
                          "compile-failure", "link-failure", "run-failure", "compile-internal", "link-internal",
                          "missing-compile-artifact", "missing-link-artifact"):
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

    def test_sensitivity_requires_current_complete_parent_and_intended_guard_not_native_failure(self):
        for spec in self.specs.values():
            for probe in spec["probes"] + spec["omissions"]:
                parent, observed = self.probe_check(spec), self.probe_check(spec, probe)
                verdict = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                type(self).probe_verdict_vectors += 1
                failed, preempted = copy.deepcopy(parent), copy.deepcopy(observed)
                failed["outcome"] = "fail"
                for check in (failed, preempted):
                    check["trace"][-1].update(returncode=1, stdout="DPE:earlier-parent-guard\n", stderr="ERROR STOP\n")
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
                        changed["trace"][-1]["stdout"] = "DPE:wrong-guard\n"
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
                    self.assertFalse(generated.probe_verdict(
                        spec, probe, good, changed, parent_binding_current=current)["qualified"])
                    type(self).probe_verdict_vectors += 1

    def test_source_output_role_and_complete_requirement_changes_stale_case_snapshots(self):
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
                        registry.requirements[generated.RULE]["oracle_limitation"] += " Changed source gate."
                    write_json(manifest, data)
                    self.assertTrue(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}))

    def test_unselected_facets_foreign_requirements_controls_and_raw_review_lifecycle_survive(self):
        original = self.registry.catalogues[generated.SECTION]
        unselected = sorted(set(self.registry.requirements[generated.RULE]["facets"]) - set(generated.FACETS))
        self.assertEqual(len(unselected), 18)
        patterns = [set(), set(unselected)] + [{facet} for facet in unselected]
        for selected_mask, pending, foreign_state, review_state in itertools.product(
                range(8), patterns, ("all", "partial", "none"), ("draft", "reviewed", "stale")):
            data = copy.deepcopy(original)
            owner = next(row for row in data["requirements"] if row["id"] == generated.RULE)
            for bit, facet in enumerate(generated.FACETS):
                if selected_mask & (1 << bit):
                    owner["pending"][facet] = "Selected independently revised plan."
            for facet in unselected:
                if facet in pending:
                    owner["pending"][facet] = "Foreign exact plan: " + facet
                else:
                    owner["pending"].pop(facet, None)
            owner["positive_control_facets"] = [unselected[0]]
            owner["oracle"] += "\n\nForeign exact oracle paragraph."
            owner["oracle_limitation"] += "\n\nForeign exact limitation paragraph."
            for row in data["requirements"]:
                if row["id"] != generated.RULE:
                    row["pending"] = {facet: "Foreign pending: " + facet for facet in row["facets"]}
                    if foreign_state == "partial":
                        row["pending"].pop(row["facets"][0])
                    elif foreign_state == "none":
                        row["pending"] = {}
            data.update(review_state="draft" if review_state == "draft" else "reviewed",
                        review_fingerprint=("0" if review_state == "stale" else "1") * 64,
                        review_rationale="Synthetic raw lifecycle state, never a disk review.")
            before, expected = copy.deepcopy(data), copy.deepcopy(data)
            for row in expected["requirements"]:
                if row["id"] == generated.RULE:
                    for facet in generated.FACETS:
                        row["pending"].pop(facet, None)
            actual = generated.synced_catalogue(data)
            self.assertEqual(data, before)
            self.assertEqual(actual, expected)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            view = generated.render_view(actual)
            self.assertTrue(all(render_requirement(row) in view for row in actual["requirements"]))
            self.assertNotIn("All 185 facets remain PENDING", view)
            self.assertIn('Registry.catalogue_review_state("8.6.7")', view)
            type(self).generator_state_vectors += 1
        self.assertEqual(self.generator_state_vectors, 1440)

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
                with self.assertRaisesRegex(ValueError, "selected DATA position"):
                    generated.synced_catalogue(data)
                self.assertEqual(data, before)
        data = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        owner = next(row for row in data["requirements"] if row["id"] == generated.RULE)
        owner["oracle"] += "\n\n" + generated.ORACLE_PREFIX + "duplicate."
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            generated.synced_catalogue(data)
        with self.assertRaisesRegex(ValueError, "unknown DATA"):
            generated.program("unowned")

    def test_generation_is_idempotent_preserves_foreign_data_and_check_mode_never_writes(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        self.registry.render()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            view = root / generated.VIEW
            view.write_text(view.read_text().replace(
                "## Bounded contexts, phases and reporting", "Foreign exact narrative.\n\n## Bounded contexts, phases and reporting"))
            foreign = root / "tests/fixtures/data_position_foreign/source.f90"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("Foreign unchanged bytes.\n")
            generated.generate(root, sync_catalogue=True)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not invoke native compilers")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)
            self.assertEqual(view.read_text().count("Foreign exact narrative."), 1)
            source = root / "tests/fixtures/data_position_effect_scalar/source.f90"
            source.write_bytes(source.read_bytes() + b"\n")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, "stale DATA position family"):
                generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
