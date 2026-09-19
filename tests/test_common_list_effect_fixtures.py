"""COMMON sequence observations, protected seeds and bounded full-parent sensitivity."""

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
import generate_common_list_effect_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


def subprogram(source, name):
    start = source.index("subroutine " + name + "(")
    end = source.index("end subroutine " + name + "\n", start) + len("end subroutine " + name + "\n")
    return source[start:end]


class CommonListEffectFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {p for p in cls.files if p.name == "fixture.json"}
        cls.cases = {c.name: c for c in cls.all_cases if Path(c.path) in manifests}
        cls.members = {r["id"]: r for r in cls.registry.execution._members(list(cls.cases.values()))}
        cls.transport_vectors = cls.probe_verdict_vectors = cls.generator_state_vectors = 0

    def test_exact_four_complete_f2023_effect_manifests(self):
        self.assertEqual(set(self.cases), {generated.identifier(v) for v in
                                          ("named_single", "named_multiple", "blank", "interleaved")})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        self.assertEqual(len(self.files), 8)
        self.assertEqual({f for c in self.cases.values() for f in c.meta.facets}, set(generated.FACETS))
        for case in self.cases.values():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             ("S8.10.2.1-001", "valid", "effect", "f2023"))
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

    def test_actual_common_lists_and_matching_saved_views(self):
        expected_statements = {
            "named_single": ["  common /packet/ a, b /packet/ c, d"],
            "named_multiple": ["  common /packet/ a, b", "  common /packet/ c, d"],
            "blank": ["  common a, b", "  common // c, d"],
            "interleaved": ["  common /left_block/ a", "  common /right_block/ x",
                            "  common /left_block/ b", "  common /right_block/ y"],
        }
        for spec in self.specs.values():
            variant, source = spec["variant"], spec["source"]
            main = source[:source.index("\nsubroutine seed_common(")]
            self.assertNotRegex(main, r"(?im)^[ \t]*(common|save)\b")
            writer = subprogram(source, "write_common")
            self.assertEqual(re.findall(r"(?m)^  common[^\n]+", writer), expected_statements[variant])
            for name in ("seed_common", "write_common", "read_common"):
                body = subprogram(source, name)
                self.assertIn("integer, intent(inout) :: entries, ", body)
                self.assertNotRegex(body, r"(?im)^[ \t]*common[^\n]*\b(entries|writes|checks)\b")
                if variant == "blank":
                    self.assertNotRegex(body, r"(?im)^[ \t]*save\b")
                    if name != "write_common":
                        self.assertEqual(len(re.findall(r"(?m)^  common // ", body)), 1)
                elif variant == "interleaved":
                    self.assertEqual(body.count("  save /left_block/\n"), 1)
                    self.assertEqual(body.count("  save /right_block/\n"), 1)
                    if name != "write_common":
                        self.assertEqual(len(re.findall(r"(?m)^  common /left_block/ ", body)), 1)
                        self.assertEqual(len(re.findall(r"(?m)^  common /right_block/ ", body)), 1)
                else:
                    self.assertEqual(body.count("  save /packet/\n"), 1)
                    if name != "write_common":
                        self.assertEqual(len(re.findall(r"(?m)^  common /packet/ ", body)), 1)
            if variant == "interleaved":
                self.assertIn("integer :: seed_left(2), seed_right(2)", subprogram(source, "seed_common"))
                self.assertIn("integer :: left_view(2), right_view(2)", subprogram(source, "read_common"))
            else:
                self.assertIn("integer :: seed_values(4)", subprogram(source, "seed_common"))
                self.assertIn("integer :: view(4)", subprogram(source, "read_common"))

    def test_separate_seed_and_caller_guards_precede_all_payload_observation(self):
        expected_counts = dict(seed_entries=1, seed_writes=4, seed_returns=1, writer_entries=1,
                               writer_writes=4, writer_returns=1, reader_entries=1,
                               reader_checks=4, reader_returns=1, caller_checks=9)
        for spec in self.specs.values():
            source = spec["source"]
            main = source[:source.index("\nsubroutine seed_common(")]
            self.assertEqual(spec["expected_counts"], expected_counts)
            for name in expected_counts:
                self.assertEqual(main.count(f"  {name}=0\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^  call ", main)), 3)
            self.assertEqual(main.count("  call seed_common(seed_entries, seed_writes)\n"), 1)
            self.assertLess(main.index("call seed_common"), main.index("call write_common"))
            self.assertLess(main.index("if (seed_writes /= 4)"), main.index("call write_common"))
            self.assertLess(main.index("if (writer_entries /= 1)"), main.index("call read_common"))
            self.assertLess(main.index("if (writer_writes /= 4)"), main.index("call read_common"))
            self.assertLess(main.index("if (writer_returns /= 1)"), main.index("call read_common"))
            self.assertEqual(main.count("caller_checks=caller_checks+1"), 9)
            self.assertIn("if (caller_checks /= 9)", main)
            for stage in ("seed", "writer", "reader"):
                self.assertEqual(main.count(f"  {stage}_returns={stage}_returns+1\n"), 1)
            seed = subprogram(source, "seed_common")
            self.assertEqual(seed.count("entries=entries+1"), 1)
            self.assertEqual(seed.count("writes=writes+1"), 4)
            expressions = (["seed_left(1)", "seed_left(2)", "seed_right(1)", "seed_right(2)"]
                           if spec["variant"] == "interleaved" else [f"seed_values({i})" for i in range(1, 5)])
            for expression, value in zip(expressions, (-101, -102, -103, -104)):
                self.assertIn(f"  {expression}={value}\n", seed)
            for body in ("write_common", "read_common"):
                self.assertNotIn("-101", subprogram(source, body))
                self.assertNotIn("seed_values", subprogram(source, body))

    def test_reader_coordinates_are_independent_distinct_literal_oracles(self):
        for spec in self.specs.values():
            reader = subprogram(spec["source"], "read_common")
            expected = ([("left_view(1)", "11"), ("left_view(2)", "22"),
                         ("right_view(1)", "33"), ("right_view(2)", "44")]
                        if spec["variant"] == "interleaved" else
                        [("view(1)", "11"), ("view(2)", "22"), ("view(3)", "33"), ("view(4)", "44")])
            self.assertEqual([(g["expression"], g["expected"]) for g in spec["observations"]], expected)
            for expression, value in expected:
                self.assertIn(f"  if ({expression} /= {value}) then\n", reader)
            self.assertEqual(reader.count("checks=checks+1"), 4)
            self.assertEqual(reader.count("  entries=entries+1\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^  if ", reader)), 4)
            self.assertNotRegex(reader, r"(?im)^[ \t]*(view|left_view|right_view)\([^\n]*\)\s*=")
            self.assertNotRegex(reader, r"(?i)\b(sum|all|product|reshape|transfer)\s*\(")
            writer = subprogram(spec["source"], "write_common")
            values = ({"a": 11, "b": 22, "x": 33, "y": 44} if spec["variant"] == "interleaved"
                      else {"a": 11, "b": 22, "c": 33, "d": 44})
            for name, value in values.items():
                self.assertEqual(writer.count(f"  {name}={value}\n"), 1)
            self.assertEqual(writer.count("writes=writes+1"), 4)

    def test_complete_programs_have_only_ordinary_defined_integer_contexts(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertNotIn(";", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^subroutine ", source)), 3)
            self.assertEqual(source.count("  implicit none\n"), 4)
            self.assertEqual(source.count("  return\n"), 3)
            self.assertNotRegex(source, r"(?im)^[ \t]*(contains|module|data|equivalence|type|real|logical|character)\b")
            self.assertNotRegex(source, r"(?i)\b(pointer|allocatable|optional|target|bind|volatile|"
                                       r"asynchronous|allocate|deallocate|coarray|parameter)\b")
            self.assertNotRegex(source, r"(?im)^[ \t]*integer[^\n]*::[^\n]*=")
            self.assertNotRegex(source, r"(?im)^[ \t]*do\b")
            self.assertTrue(source.endswith("end subroutine read_common\n"))

    def test_all_wrong_value_order_block_and_completion_spans_bind_complete_sources(self):
        self.assertEqual(sum(len(s["probes"]) for s in self.specs.values()), 65)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(len(spec["guards"]), 15)
            self.assertEqual(spec["source"].count("    error stop\n"), 14)
            self.assertEqual(len(spec["probes"]), 17 if spec["variant"] == "interleaved" else 16)
            hashes = set()
            for probe in spec["probes"]:
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertEqual(mutant.count(b"\n"), raw.count(b"\n"))
                for first, last in spec["protected_spans"]:
                    self.assertIn(raw[first:last], mutant)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
            order = next(p for p in spec["probes"] if p["id"] == "wrong-position-order")
            self.assertEqual((order["expected"], order["replacement"]), ("11", "22"))
            if spec["variant"] == "interleaved":
                block = next(p for p in spec["probes"] if p["id"] == "wrong-block-value")
                self.assertEqual((block["expected"], block["replacement"]), ("11", "33"))
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(dict(spec, source=spec["source"] + "\n"), spec["probes"][0])

    def test_all_omissions_preserve_seed_and_reach_exact_guards_or_external_completion(self):
        self.assertEqual(sum(len(s["omissions"]) for s in self.specs.values()), 104)
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(len(spec["omissions"]), 26)
            hashes = {generated.sha(generated.wrong_oracle_source(spec, p)) for p in spec["probes"]}
            for probe in spec["omissions"]:
                start, end = probe["span"]
                mutant = generated.wrong_oracle_source(spec, probe)
                self.assertEqual(mutant, raw[:start] + raw[end:])
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                for first, last in spec["protected_spans"]:
                    self.assertIn(raw[first:last], mutant)
                self.assertEqual(re.findall(rb"(?m)^  (?:common|save)[^\n]+", raw),
                                 re.findall(rb"(?m)^  (?:common|save)[^\n]+", mutant))
                if probe["id"] == "omit-completion":
                    self.assertNotIn(spec["completion"].strip().encode(), mutant)
                    self.assertEqual((probe["kind"], probe["failure_stdout"]), ("output", ""))
                    continue
                self.assertIn(spec["completion"].strip().encode(), mutant)
                if probe["id"].startswith("omit-write-"):
                    operation = next(r for r in spec["writer_operations"] if r["span"] == probe["span"])
                    self.assertEqual(probe["guard_id"], operation["observation"])
                    self.assertEqual(subprogram(mutant.decode(), "write_common").count("writes=writes+1"), 4)
                elif probe["id"].startswith("omit-reader-check-") or probe["id"] == "omit-all-reader-checks":
                    self.assertEqual(probe["guard_id"], "reader-checks")
                elif probe["id"].startswith("omit-caller-check-"):
                    self.assertEqual(probe["guard_id"], "caller-check-total")
                else:
                    expected = {
                        "omit-writer-call": "writer-entries", "omit-reader-call": "reader-entries",
                        "noop-writer-body": "writer-entries", "noop-reader-body": "reader-entries",
                        "omit-all-writes": "writer-writes", "omit-writer-return-count": "writer-returns",
                        "omit-reader-return-count": "reader-returns",
                    }
                    self.assertEqual(probe["guard_id"], expected[probe["id"]])
                self.assertEqual(probe["failure_stdout"], f"CLE:{spec['variant']}:{probe['guard_id']}\n")
            for span in spec["protected_spans"]:
                forbidden = dict(span=span, expected=spec["source"][span[0]:span[1]], replacement="")
                with self.assertRaisesRegex(ValueError, "protected seed"):
                    generated.wrong_oracle_source(spec, forbidden)

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
                    code, stdout, stderr = 1, "CLE:wrong-guard\n", "ERROR STOP\n"
                elif fault == "crash":
                    code = -11
                elif fault == "timeout":
                    timed_out = True
            elif fault == phase + "-internal":
                stderr = "ASR verify pass error\n"
            elif phase == "compile" and fault == "obsolescent-warning":
                stderr = "Warning: Obsolescent feature: COMMON block\n"
            if phase != "run" and code == 0 and fault != "missing-" + phase + "-artifact":
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact, not native evidence")
            return runner.ProcessResult(code, stdout + stderr, timed_out, stdout, stderr,
                                        stdout.encode(), stderr.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual([r["phase"] for r in check.trace], phases)
        self.assertEqual(check.input_hashes, {"source.f90": generated.sha(source)})
        type(self).transport_vectors += 1
        return check, phases

    def test_staging_needs_complete_runtime_and_exact_external_completion(self):
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
        if probe is None:
            stdout, code = spec["completion"], 0
        elif probe["kind"] == "output":
            stdout = "" if probe["mutation"] == "completion-statement-omission" else probe["replacement"] + "\n"
            code = 0
        else:
            stdout, code = probe["failure_stdout"], 2
        trace = [dict(phase=phase, returncode=0, timed_out=False, stdout="", stderr="")
                 for phase in ("compile", "link", "run")]
        trace[-1].update(returncode=code, stdout=stdout, stderr="" if code == 0 else "ERROR STOP\n")
        return dict(outcome="pass" if probe is None else "fail", phase="run", trace=trace,
                    input_hashes={"source.f90": generated.sha(raw)})

    def test_each_planned_intended_failure_and_absent_completion_requires_the_whole_parent(self):
        for spec in self.specs.values():
            for probe in spec["probes"] + spec["omissions"]:
                parent, observed = self.probe_check(spec), self.probe_check(spec, probe)
                verdict = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("sensitive", True))
                if probe["kind"] == "output":
                    self.assertEqual(observed["trace"][-1]["returncode"], 0)
                type(self).probe_verdict_vectors += 1

    def test_failed_stale_preempted_or_incomplete_parents_and_probes_never_qualify(self):
        for spec in self.specs.values():
            selected = [spec["probes"][0], next(p for p in spec["probes"] if p["kind"] == "output"),
                        next(p for p in spec["omissions"] if p["id"] == "omit-completion")]
            for probe in selected:
                for fault in ("parent-stale", "parent-failed", "parent-not-run", "parent-no-trace",
                              "parent-wrong-input", "probe-compile-blocked", "probe-link-blocked",
                              "probe-wrong-input", "wrong-guard", "extra-output", "compile-internal",
                              "resource-failure", "crash", "timeout", "probe-passed", "probe-untested"):
                    parent, observed, current = self.probe_check(spec), self.probe_check(spec, probe), True
                    if fault == "parent-stale":
                        current = False
                    elif fault == "parent-failed":
                        parent["outcome"] = "fail"
                    elif fault == "parent-not-run":
                        parent["phase"] = "compile"
                    elif fault == "parent-no-trace":
                        parent["trace"] = []
                    elif fault == "parent-wrong-input":
                        parent["input_hashes"]["source.f90"] = "0" * 64
                    elif fault == "probe-compile-blocked":
                        observed.update(phase="compile", trace=observed["trace"][:1])
                    elif fault == "probe-link-blocked":
                        observed.update(phase="link", trace=observed["trace"][:2])
                    elif fault == "probe-wrong-input":
                        observed["input_hashes"]["source.f90"] = "0" * 64
                    elif fault == "wrong-guard":
                        observed["trace"][-1]["stdout"] = "CLE:wrong-guard\n"
                    elif fault == "extra-output":
                        observed["trace"][-1]["stdout"] += "EXTRA\n"
                    elif fault == "compile-internal":
                        observed["trace"][0]["stderr"] = "ASR verify pass error\n"
                    elif fault == "resource-failure":
                        observed["trace"][-1]["stderr"] = "out of memory\n"
                    elif fault == "crash":
                        observed["trace"][-1]["returncode"] = -11
                    elif fault == "timeout":
                        observed["trace"][-1]["timed_out"] = True
                    elif fault == "probe-passed":
                        observed["outcome"] = "pass"
                    else:
                        observed = None
                    verdict = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=current)
                    self.assertFalse(verdict["qualified"])
                    if observed is None:
                        self.assertEqual(verdict["status"], "UNTESTED")
                    type(self).probe_verdict_vectors += 1
                parent, observed = self.probe_check(spec), self.probe_check(spec, probe)
                parent["outcome"] = "fail"
                for value in (parent, observed):
                    value["trace"][-1].update(returncode=1, stdout="CLE:earlier-parent-guard\n", stderr="ERROR STOP\n")
                verdict = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=True)
                self.assertEqual((verdict["status"], verdict["qualified"]), ("parent-preempted", False))
                type(self).probe_verdict_vectors += 1

    def test_input_output_role_and_owner_drift_stale_complete_case_bindings(self):
        for original, mutation in itertools.product(self.cases.values(), ("source", "output", "role", "requirement")):
            registry = Registry(ROOT)
            fingerprint = original.fingerprint(registry)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest = root / "fixture.json"
                manifest.write_bytes(original.fixture.path.read_bytes())
                source = root / "source.f90"
                source.write_bytes((original.fixture.root / "source.f90").read_bytes())

                def current_cases(*args, **kwargs):
                    fixture = runner.load_fixture(manifest, runner.PROFILES)
                    changed = replace(original, path=str(manifest), fixture=fixture, meta=fixture.meta)
                    return [changed if c.name == original.name else c for c in self.all_cases]

                with patch.object(runner, "Registry", return_value=registry), \
                        patch.object(runner, "collect_cases", side_effect=current_cases):
                    self.assertEqual(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}), [])
                    data = json.loads(manifest.read_text())
                    if mutation == "source":
                        source.write_bytes(source.read_bytes() + b"\n")
                    elif mutation == "output":
                        data["expect"]["stdout"] += "EXTRA\n"
                    elif mutation == "role":
                        data["evidence"] = "positive-control"
                    else:
                        registry.requirements[generated.RULE]["oracle_limitation"] += " Different source gate."
                    write_json(manifest, data)
                    self.assertTrue(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}))

    def test_catalogue_sync_changes_only_four_pending_entries_and_two_stale_sentences(self):
        original = self.registry.catalogues[generated.SECTION]
        for mask, review in itertools.product(range(16), ("draft", "reviewed", "stale")):
            data = copy.deepcopy(original)
            owner = next(r for r in data["requirements"] if r["id"] == generated.RULE)
            owner["pending"] = {f: "Selected exact future plan." for i, f in enumerate(generated.FACETS)
                                if mask & (1 << i)}
            owner["oracle"] += "\n\nForeign exact oracle paragraph."
            owner["oracle_limitation"] += "\n\nForeign exact limitation paragraph."
            for ordinal, row in enumerate(data["requirements"]):
                if row["id"] != generated.RULE:
                    row["pending"] = {f: "Unselected exact plan: " + f for i, f in enumerate(row["facets"])
                                      if (i + ordinal + mask) % 3}
            data.update(review_state="draft" if review == "draft" else "reviewed",
                        review_fingerprint=("0" if review == "stale" else "1") * 64,
                        review_rationale="Synthetic lifecycle state; never a disk review.")
            expected, before = copy.deepcopy(data), copy.deepcopy(data)
            expected_owner = next(r for r in expected["requirements"] if r["id"] == generated.RULE)
            expected_owner["pending"] = {}
            for field, stale, current, _anchors in generated.STALE_SENTENCES:
                self.assertNotIn(stale, expected_owner[field])
                self.assertEqual(expected_owner[field].count(current), 1)
            actual = generated.synced_catalogue(data)
            self.assertEqual(data, before)
            self.assertEqual(actual, expected)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            stale_data = copy.deepcopy(data)
            stale_owner = next(r for r in stale_data["requirements"] if r["id"] == generated.RULE)
            for field, stale, current, _anchors in generated.STALE_SENTENCES:
                stale_owner[field] = stale_owner[field].replace(current, stale)
                self.assertIn(stale, stale_owner[field])
            self.assertEqual(generated.synced_catalogue(stale_data), expected)
            view = generated.render_view(actual)
            self.assertTrue(all(render_requirement(r) in view for r in actual["requirements"]))
            self.assertIn('Registry.catalogue_review_state("8.10.2.1")', view)
            self.assertIn("replaces the two\ninherited sentences that said no program or mutation existed", view)
            self.assertNotIn("inherited historical source-plan/oracle", view)
            actual_owner = next(r for r in actual["requirements"] if r["id"] == generated.RULE)
            for _, stale, _, _anchors in generated.STALE_SENTENCES:
                self.assertNotIn(stale, render_requirement(actual_owner))
            self.assertIn("Foreign exact oracle paragraph.", actual_owner["oracle"])
            self.assertIn("Foreign exact limitation paragraph.", actual_owner["oracle_limitation"])
            type(self).generator_state_vectors += 1
        self.assertEqual(self.generator_state_vectors, 48)

    def test_generator_rejects_missing_definitions_weakened_roles_and_duplicate_summary(self):
        for mutation in ("missing-owner", "duplicate-owner", "missing-facet", "positive-control", "category"):
            data = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(r for r in data["requirements"] if r["id"] == generated.RULE)
            if mutation == "missing-owner":
                data["requirements"].remove(owner)
            elif mutation == "duplicate-owner":
                data["requirements"].append(copy.deepcopy(owner))
            elif mutation == "missing-facet":
                owner["facets"].pop()
            elif mutation == "positive-control":
                owner["positive_control_facets"] = [generated.FACETS[0]]
            else:
                owner["category"] = "syntax"
            before = copy.deepcopy(data)
            with self.assertRaisesRegex(ValueError, "selected COMMON"):
                generated.synced_catalogue(data)
            self.assertEqual(data, before)
        with self.assertRaisesRegex(ValueError, "unknown COMMON"):
            generated.program("unowned")
        for field, stale, current, anchors in generated.STALE_SENTENCES:
            for mutation in ("mixed", "duplicate-current", "duplicate-stale", "removed", "reworded",
                             "stale-plus-reworded", "stale-plus-current", "anchor-only"):
                data = copy.deepcopy(self.registry.catalogues[generated.SECTION])
                owner = next(r for r in data["requirements"] if r["id"] == generated.RULE)
                reworded = current.replace("every other", "no other")
                self.assertNotEqual(reworded, current)
                self.assertTrue(all(anchor in reworded for anchor in anchors))
                if mutation == "mixed":
                    owner[field] += " " + stale
                elif mutation == "duplicate-current":
                    owner[field] += " " + current
                elif mutation == "duplicate-stale":
                    owner[field] = owner[field].replace(current, stale + " " + stale)
                elif mutation == "removed":
                    owner[field] = owner[field].replace(current, "")
                elif mutation == "reworded":
                    owner[field] = owner[field].replace(current, reworded)
                elif mutation == "stale-plus-reworded":
                    owner[field] = owner[field].replace(current, stale + " " + reworded)
                elif mutation == "stale-plus-current":
                    owner[field] = owner[field].replace(current, stale + " " + current)
                else:
                    owner[field] = owner[field].replace(current, anchors[0])
                before = copy.deepcopy(data)
                with self.assertRaisesRegex(ValueError, "inherited COMMON " + field):
                    generated.synced_catalogue(data)
                self.assertEqual(data, before)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = root / generated.VIEW
            view.parent.mkdir(parents=True)
            view.write_text((ROOT / generated.VIEW).read_text().replace(
                generated.SUMMARY_BEGIN, generated.SUMMARY_BEGIN + "\n" + generated.SUMMARY_BEGIN))
            with self.assertRaisesRegex(ValueError, "summary boundaries"):
                generated.render_view(self.registry.catalogues[generated.SECTION], root)

    def test_generation_is_deterministic_idempotent_and_check_mode_is_read_only(self):
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
            view.write_text("Foreign exact narrative.\n\n" + view.read_text())
            foreign = root / "tests/fixtures/common_foreign/source.f90"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("Foreign unchanged bytes.\n")
            generated.generate(root, sync_catalogue=True)
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not invoke compilers")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
            self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}, before)
            self.assertEqual(view.read_text().count("Foreign exact narrative."), 1)
            source = root / "tests/fixtures/common_list_effect_named_single/source.f90"
            source.write_bytes(source.read_bytes() + b"\n")
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(ValueError, "stale COMMON list family"):
                generated.generate(root, check=True)
            self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
