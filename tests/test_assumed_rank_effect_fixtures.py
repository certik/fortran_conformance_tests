"""Real assumed-rank inputs, full-parent oracle mutations and independent lifecycle state."""
import copy
from dataclasses import asdict, replace
import hashlib
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
import generate_assumed_rank_effect_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class AssumedRankEffectFixturesTests(unittest.TestCase):
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

    def test_two_exact_primary_run_effect_cases_and_no_extra_coverage(self):
        self.assertEqual(set(self.cases), {
            "S8_5_8_7_001_valid__assumed_rank_effect_ordinary",
            "S8_5_8_7_001_valid__assumed_rank_effect_zero_size",
        })
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual({case.meta.facets[0] for case in self.cases.values()}, set(generated.FACETS))
        for case in self.cases.values():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard),
                             ("S8.5.8.7-001", "valid", "effect", "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(len(case.meta.facets), 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expectation = case.fixture.expectation
            self.assertEqual((expectation.phase, expectation.outcome, expectation.exit_code), ("run", "success", 0))
            self.assertEqual(expectation.stdout, [self.specs[case.name]["completion"]])
            self.assertEqual(expectation.stderr, [""])
            self.assertEqual(self.members[case.name]["cohort"], "runtime-effect")
            wrong = replace(case, meta=replace(case.meta, evidence="positive-control"))
            with self.assertRaises(SuiteError):
                validate_case_requirement(wrong, self.registry.requirements[generated.RULE])

    def test_original_rank_and_argument_rules_bind_real_internal_observers(self):
        expected = {
            "ordinary": [("scalar", "0", "1"), ("vector", "1", "2"), ("matrix", "2", "3")],
            "zero_size": [("a", "1", "1"), ("b", "2", "2")],
        }
        for spec in self.specs.values():
            source = spec["source"]
            main, observer = source.split("contains\n", 1)
            self.assertTrue(observer.startswith("  subroutine observe(x, expected_rank, expected_visit)\n"))
            self.assertIn("    implicit none\n    integer, intent(in) :: x(..)\n", observer)
            self.assertIn("    integer, intent(in) :: expected_rank, expected_visit\n", observer)
            self.assertIn("    observed_rank=rank(x)\n", observer)
            self.assertEqual(source.count("rank(x)"), 1)
            self.assertNotRegex(main, r"\brank\s*\(")
            self.assertEqual(re.findall(r"call observe\((\w+), (\d), (\d)\)", main), expected[spec["variant"]])
            self.assertNotRegex(observer, r"\bx\s*\((?!\.\.)")
            self.assertTrue(source.endswith(f"end program assumed_rank_{spec['variant']}_effect\n"))
            self.assertLess(source.index("observed_rank=rank(x)"), source.index("if (observed_rank /= expected_rank)"))
            self.assertLess(source.index("if (observed_rank /= expected_rank)"), source.index("select case (observed_rank)"))

    def test_nonempty_actuals_are_defined_and_empty_named_arrays_keep_their_dimensions(self):
        ordinary = self.specs[generated.identifier("ordinary")]["source"].split("contains\n", 1)[0]
        self.assertIn("  integer :: scalar, vector(3), matrix(2,3)\n", ordinary)
        for assignment in ("scalar=11", "vector=12", "matrix=13"):
            self.assertLess(ordinary.index(assignment), ordinary.index("call observe("))
        empty = self.specs[generated.identifier("zero_size")]["source"]
        self.assertIn("  integer :: a(0), b(0,3)\n", empty)
        self.assertIn("  call observe(a, 1, 1)\n", empty)
        self.assertIn("  call observe(b, 2, 2)\n", empty)
        self.assertNotRegex(empty, r"(?m)^\s*[ab]\s*=")
        self.assertEqual(re.findall(r"\ba\s*\(", empty), ["a("])
        self.assertEqual(re.findall(r"\bb\s*\(", empty), ["b("])

    def test_no_unsupported_role_state_inquiry_or_storage_shortcut_in_the_programs(self):
        for spec in self.specs.values():
            source = spec["source"]
            self.assertNotRegex(source, r"(?i)\b(pointer|allocatable|optional|value|target|contiguous|asynchronous|"
                                       r"volatile|coarray|bind|class|type|save|allocate|common|equivalence)\b")
            self.assertNotRegex(source, r"(?i)\b(size|shape|lbound|ubound|present|associated|allocated|"
                                       r"storage_size|transfer|reshape|kind|loc|c_loc|c_sizeof)\s*\(")
            self.assertNotIn("select rank", source.lower())
            self.assertNotIn("rank([", source.lower())
            self.assertNotRegex(source, r"(?m)^\s*integer[^\n]*::[^\n]*=")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            source.encode("ascii")

    def test_actual_categories_visits_normal_returns_and_all_guard_totals_are_consumed(self):
        for variant, calls, categories, checks in (("ordinary", 3, (0, 1, 2), 6), ("zero_size", 2, (1, 2), 5)):
            spec = self.specs[generated.identifier(variant)]
            source = spec["source"]
            guards = {guard["id"]: guard for guard in spec["guards"]}
            for name, expected in (("total-visits", calls), ("normal-returns", calls),
                                   ("observer-checks", 2 * calls), ("caller-checks", checks)):
                self.assertEqual(guards[name]["expected"], str(expected))
            for rank in categories:
                self.assertEqual(guards[f"category-{rank}"]["expected"], "1")
                self.assertIn(f"    case ({rank})\n", source)
            self.assertEqual(source.count("returns=returns+1"), calls)
            self.assertEqual(source.count("visits=visits+1"), 1)
            self.assertEqual(source.count("observer_checks=observer_checks+1"), 2)
            self.assertEqual(source.count("main_checks=main_checks+1"), checks)
            for name in ("visits", "returns", "observer_checks", "main_checks", "rank_one_visits", "rank_two_visits"):
                self.assertLess(source.index(f"  {name}=0\n"), source.index("  call observe("))
            if variant == "ordinary":
                self.assertLess(source.index("  scalar_visits=0\n"), source.index("  call observe("))
            self.assertLess(source.index("ARE:" + variant + ":caller-checks"), source.index(spec["completion"].strip()))

    def test_every_guard_activation_and_output_has_a_single_exact_whole_parent_mutation(self):
        for variant, guards, probes, activations in (("ordinary", 10, 14, (1, 2, 3)),
                                                    ("zero_size", 9, 11, (1, 2))):
            spec = self.specs[generated.identifier(variant)]
            raw = spec["source"].encode("ascii")
            self.assertEqual((len(spec["guards"]), len(spec["probes"])), (guards, probes))
            self.assertEqual(len({probe["id"] for probe in spec["probes"]}), probes)
            guard_map = {guard["id"]: guard for guard in spec["guards"]}
            self.assertEqual(spec["source"].count("  error stop\n"), guards - 1)
            for guard in spec["guards"]:
                actual = {probe["activation"] for probe in spec["probes"] if probe["guard_id"] == guard["id"]}
                self.assertEqual(actual, set(guard["activations"]))
            for name in ("observer-rank", "observer-visit"):
                self.assertEqual(guard_map[name]["activations"], list(activations))
            for probe in spec["probes"]:
                changed = generated.wrong_oracle_source(spec, probe)
                start, end = probe["span"]
                self.assertEqual(raw[start:end].decode("ascii"), probe["expected"])
                self.assertEqual(changed, raw[:start] + probe["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(raw, changed)
                self.assertEqual(changed.count(b"\n"), raw.count(b"\n"))
                self.assertIn(b"integer, intent(in) :: x(..)", changed)
                self.assertIn(b"observed_rank=rank(x)", changed)
                self.assertEqual(changed.count(b"call observe("), len(activations))
                self.assertIn(b"end subroutine observe\n", changed)
                if probe["activation"] is not None:
                    matches = list(re.finditer(r"call observe\((\w+), (\d), (\d)\)", spec["source"]))
                    call = matches[probe["activation"] - 1]
                    group = 2 if probe["category"] == "rank" else 3
                    self.assertEqual(tuple(probe["span"]), call.span(group))
                    self.assertEqual(int(probe["replacement"]), int(call.group(group)) + 1)
                    self.assertEqual(probe["failure_stdout"],
                                     f"ARE:{variant}:{probe['guard_id']}:activation={probe['activation']}\n")
                elif probe["kind"] == "guard":
                    self.assertEqual(int(probe["replacement"]), int(probe["expected"]) + 1)
            changed_parent = dict(spec, source=spec["source"] + "\n")
            with self.assertRaisesRegex(ValueError, "complete parent input"):
                generated.wrong_oracle_source(changed_parent, spec["probes"][0])

    def staged(self, case, family, mode, fault=None):
        compiler = runner.Compiler(family, family, mode, "synthetic transport, not compiler evidence")
        raw = (case.fixture.root / "source.f90").read_bytes()
        phases = []

        def transport(command, cwd, timeout, stdin=None):
            workspace = Path(cwd).resolve()
            self.assertEqual((timeout, stdin), (5, None))
            self.assertEqual((workspace / "source.f90").read_bytes(), raw)
            phase = "compile" if "-c" in command else "link" if "-o" in command else "run"
            phases.append(phase)
            if phase == "compile":
                self.assertEqual(Path(command[command.index("-c") + 1]), workspace / "source.f90")
            elif phase == "run":
                self.assertEqual(command, [str(workspace / "program")])
            status, stdout, stderr, timed_out = 0, "", "", False
            if fault == phase + "-failure":
                status, stderr = 1, "synthetic failed process"
            elif phase == "run":
                stdout = self.specs[case.name]["completion"]
                if fault == "no-op":
                    stdout = ""
                elif fault == "wrong-output":
                    stdout = stdout.replace(" OK", " BAD")
                elif fault == "extra-output":
                    stdout += "extra\n"
                elif fault == "stderr":
                    stderr = "extra\n"
                elif fault == "guard":
                    status, stdout, stderr = 1, "ARE:wrong-rank\n", "ERROR STOP\n"
                elif fault == "crash":
                    status = -11
                elif fault == "timeout":
                    timed_out = True
            elif fault == phase + "-internal":
                stderr = "ASR verify pass error\n"
            if phase != "run" and status == 0 and fault != "missing-" + phase + "-artifact":
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic artifact")
            return runner.ProcessResult(status, stdout + stderr, timed_out, stdout, stderr, stdout.encode(), stderr.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5)
        ran = validate_case_trace(self.members[case.name], asdict(check),
                                  dict(compiler.configuration(), version=compiler.version), ROOT, None, False)
        self.assertEqual(ran, "run" in phases)
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertEqual([step["phase"] for step in check.trace], phases)
        type(self).transport_vectors += 1
        return check, phases

    def test_real_staging_requires_ordered_compile_link_run_and_exact_completion(self):
        for case, (family, mode) in itertools.product(self.cases.values(), FAMILIES):
            check, phases = self.staged(case, family, mode)
            self.assertEqual((check.outcome, check.phase), ("pass", "run"))
            self.assertEqual(phases, ["compile", "link", "run"])
            self.assertEqual(qualifying_reference(case, dict(outcome=check.outcome, phase=check.phase, standard=mode)),
                             mode == "f2023")
            for fault in ("no-op", "wrong-output", "extra-output", "stderr", "guard", "crash", "timeout",
                          "compile-failure", "link-failure", "run-failure", "compile-internal",
                          "link-internal", "missing-compile-artifact", "missing-link-artifact"):
                with self.subTest(case=case.name, family=family, fault=fault):
                    check, phases = self.staged(case, family, mode, fault)
                    self.assertEqual(check.outcome, "fail")
                    if fault.startswith(("compile-", "link-", "missing-")):
                        self.assertNotIn("run", phases)

    def synthetic_probe_check(self, spec, probe=None):
        stdout = spec["completion"] if probe is None else (
            probe["replacement"] + "\n" if probe["kind"] == "output" else probe["failure_stdout"])
        status = 0 if probe is None or probe["kind"] == "output" else 2
        trace = [dict(phase=phase, returncode=0, timed_out=False, stdout="", stderr="") for phase in ("compile", "link", "run")]
        trace[-1].update(returncode=status, stdout=stdout, stderr="" if status == 0 else "ERROR STOP\n")
        raw = spec["source"].encode() if probe is None else generated.wrong_oracle_source(spec, probe)
        return dict(outcome="pass" if probe is None else "fail", phase="run", trace=trace,
                    input_hashes={"source.f90": hashlib.sha256(raw).hexdigest()})

    def test_sensitivity_needs_current_passing_full_parent_and_the_exact_intended_failure(self):
        for spec in self.specs.values():
            parent = self.synthetic_probe_check(spec)
            for probe in spec["probes"]:
                observed = self.synthetic_probe_check(spec, probe)
                good = generated.probe_verdict(spec, probe, parent, observed, parent_binding_current=True)
                self.assertTrue(good["qualified"])
                self.assertEqual(good["status"], "sensitive")
                type(self).probe_verdict_vectors += 1
                failed_parent, preempted = copy.deepcopy(parent), copy.deepcopy(observed)
                failed_parent["outcome"] = "fail"
                for check in (failed_parent, preempted):
                    check["trace"][-1].update(returncode=1, stdout="ARE:earlier-parent-guard\n", stderr="ERROR STOP\n")
                result = generated.probe_verdict(spec, probe, failed_parent, preempted, parent_binding_current=True)
                self.assertEqual(result["status"], "parent-preempted")
                self.assertTrue(result["parent_preempted"])
                self.assertFalse(result["qualified"])
                type(self).probe_verdict_vectors += 1
                for fault in ("parent-stale", "parent-failed", "parent-not-run", "parent-no-trace", "parent-wrong-input",
                              "probe-compile-blocked", "probe-link-blocked", "probe-wrong-input", "wrong-guard",
                              "wrong-activation", "compile-internal", "resource-failure", "crash", "timeout",
                              "probe-passed", "probe-untested"):
                    original, changed, current = copy.deepcopy(parent), copy.deepcopy(observed), True
                    if fault == "parent-stale":
                        current = False
                    elif fault == "parent-failed":
                        original["outcome"] = "fail"
                    elif fault == "parent-not-run":
                        original["phase"] = "compile"
                    elif fault == "parent-no-trace":
                        original["trace"] = []
                    elif fault == "parent-wrong-input":
                        original["input_hashes"]["source.f90"] = "0" * 64
                    elif fault == "probe-compile-blocked":
                        changed.update(phase="compile", trace=changed["trace"][:1])
                    elif fault == "probe-link-blocked":
                        changed.update(phase="link", trace=changed["trace"][:2])
                    elif fault == "probe-wrong-input":
                        changed["input_hashes"]["source.f90"] = "0" * 64
                    elif fault == "wrong-guard":
                        changed["trace"][-1]["stdout"] = "ARE:unrelated-guard\n"
                    elif fault == "wrong-activation":
                        changed["trace"][-1]["stdout"] += "activation=other\n"
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
                    result = generated.probe_verdict(spec, probe, original, changed, parent_binding_current=current)
                    with self.subTest(probe=probe["id"], variant=spec["variant"], fault=fault):
                        self.assertFalse(result["qualified"])
                        if changed is None:
                            self.assertEqual(result["status"], "UNTESTED")
                    type(self).probe_verdict_vectors += 1

    def test_source_output_role_and_requirement_mutations_stale_native_snapshots(self):
        for original, mutation in itertools.product(self.cases.values(), ("source", "output", "role", "requirement")):
            registry = Registry(ROOT)
            fingerprint = original.fingerprint(registry)
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                path = directory / "fixture.json"
                path.write_bytes(original.fixture.path.read_bytes())
                source = directory / "source.f90"
                source.write_bytes((original.fixture.root / "source.f90").read_bytes())

                def current_cases(*args, **kwargs):
                    fixture = runner.load_fixture(path, runner.PROFILES)
                    changed = replace(original, path=str(path), fixture=fixture, meta=fixture.meta)
                    return [changed if case.name == original.name else case for case in self.all_cases]

                with patch.object(runner, "Registry", return_value=registry), \
                        patch.object(runner, "collect_cases", side_effect=current_cases):
                    self.assertEqual(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}), [])
                    manifest = json.loads(path.read_text())
                    if mutation == "source":
                        source.write_bytes(source.read_bytes() + b"\n")
                    elif mutation == "output":
                        manifest["expect"]["stdout"] += "extra\n"
                    elif mutation == "role":
                        manifest["evidence"] = "positive-control"
                    else:
                        registry.requirements[generated.RULE]["oracle_limitation"] += " Changed source gate."
                    write_json(path, manifest)
                    self.assertTrue(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}))

    def test_every_unselected_owner_subset_and_foreign_pending_control_review_state_is_preserved(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        unselected = sorted(set(self.registry.requirements[generated.RULE]["facets"]) - set(generated.FACETS))
        for selected_mask, foreign_mask, foreign_state, review_state in itertools.product(
                range(4), range(1 << len(unselected)), ("all", "partial", "none"), ("draft", "reviewed", "stale")):
            candidate = copy.deepcopy(catalogue)
            owner = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
            for bit, facet in enumerate(generated.FACETS):
                if selected_mask & (1 << bit):
                    owner["pending"][facet] = "Selected independently revised plan."
            for bit, facet in enumerate(unselected):
                if foreign_mask & (1 << bit):
                    owner["pending"][facet] = "Foreign exact plan for " + facet
                else:
                    owner["pending"].pop(facet, None)
            owner["positive_control_facets"] = [unselected[0]]
            owner["oracle"] += "\n\nForeign oracle paragraph."
            owner["oracle_limitation"] += "\n\nForeign limitation paragraph."
            for row in candidate["requirements"]:
                if row["id"] != generated.RULE:
                    row["pending"] = {facet: "Foreign plan for " + facet for facet in row["facets"]}
                    if foreign_state == "partial":
                        row["pending"].pop(row["facets"][0])
                    elif foreign_state == "none":
                        row["pending"] = {}
            candidate["review_state"] = "draft" if review_state == "draft" else "reviewed"
            candidate["review_fingerprint"] = "0" * 64 if review_state == "stale" else "1" * 64
            candidate["review_rationale"] = "Synthetic raw state, never a disk approval."
            untouched = copy.deepcopy(candidate)
            expected = copy.deepcopy(candidate)
            for row in expected["requirements"]:
                if row["id"] == generated.RULE:
                    for facet in generated.FACETS:
                        row["pending"].pop(facet, None)
            actual = generated.synced_catalogue(candidate)
            self.assertEqual(actual, expected)
            self.assertEqual(candidate, untouched)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            text = generated.render_view(actual)
            for row in actual["requirements"]:
                self.assertIn(render_requirement(row), text)
            self.assertNotIn("Every implementation facet remains pending", text)
            self.assertNotIn("other four", text)
            self.assertNotIn("**Source review: reviewed.**", text)
            type(self).generator_state_vectors += 1

    def test_selected_definitions_are_required_but_no_fixed_pending_census_is_required(self):
        for facet in generated.FACETS:
            candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
            owner["facets"].remove(facet)
            before = copy.deepcopy(candidate)
            with self.assertRaisesRegex(ValueError, "selected S8.5.8.7-001 facet definitions changed"):
                generated.synced_catalogue(candidate)
            self.assertEqual(candidate, before)
        candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        for row in candidate["requirements"]:
            row["pending"] = {}
        self.assertEqual(generated.synced_catalogue(candidate), candidate)

    def test_real_source_review_lifecycle_and_full_foreign_inventory_blockers_are_not_renewed(self):
        registry = Registry(ROOT)
        disk = copy.deepcopy((registry.catalogues, registry.reviews, registry.evidence.data,
                              registry.source_uses.data, registry.execution.data))
        original = copy.deepcopy(registry.catalogues[generated.SECTION])
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original)
            registry.catalogues[generated.SECTION] = candidate
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory source state, never an actual approval."
            candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint(generated.SECTION)
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
        before = registry.execution.snapshot(self.all_cases)
        foreign = next(case for case in self.all_cases if case.name not in self.cases and case.review_key in registry.reviews)
        registry.reviews[foreign.review_key] = dict(
            registry.reviews[foreign.review_key], state="unreviewed", rationale="Retained independent foreign blocker.")
        for case in self.cases.values():
            registry.reviews[case.review_key] = dict(
                state="source-reviewed", fingerprint=case.fingerprint(registry), sources=["8.5.8.7#p1"],
                rationale="In-memory owner-only state, not written review.")
        for report in registry.execution.report(self.all_cases, include_members=False):
            registry.execution.aggregates[report["id"]]["review"].update(
                state="source-reviewed", fingerprint=report["review"]["fingerprint"],
                rationale="Synthetic matching raw receipt retaining blockers.")
        for report in registry.execution.report(self.all_cases):
            self.assertEqual(report["member_count"], len(self.all_cases))
            self.assertEqual({row["id"] for row in report["members"]}, {case.name for case in self.all_cases})
            self.assertEqual(report["state"], "stale")
            self.assertIn(foreign.name + ": fixture review is unreviewed", report["blockers"])
        with patch.object(runner, "Registry", return_value=registry), \
                patch.object(runner, "collect_cases", return_value=self.all_cases):
            self.assertTrue(runner.confirm_snapshot([], [], {}, execution_snapshot=before))
        fresh = Registry(ROOT)
        self.assertEqual((fresh.catalogues, fresh.reviews, fresh.evidence.data, fresh.source_uses.data, fresh.execution.data), disk)

    def test_standalone_generation_keeps_foreign_family_cases_and_is_byte_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in catalogue["requirements"] if row["id"] == generated.RULE)
            foreign_facet = next(facet for facet in owner["facets"] if facet not in generated.FACETS)
            owner["pending"].pop(foreign_facet, None)
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            write_json(root / generated.CATALOGUE, catalogue)
            generated.generate(root, sync_catalogue=True)
            foreign = root / "tests/fixtures/assumed_rank_effect_foreign_owner"
            foreign.mkdir()
            parent = self.specs[generated.identifier("ordinary")]
            manifest = copy.deepcopy(parent["manifest"])
            manifest.update(id="S8_5_8_7_001_valid__foreign_owner", facets=[foreign_facet])
            write_json(foreign / "fixture.json", manifest)
            (foreign / "source.f90").write_text(parent["source"])
            write_json(root / "source.json", dict(
                self.registry.standard, sections={generated.SECTION: self.registry.sections[generated.SECTION]}))
            (root / "rules.txt").write_text("R827 test inventory\nC839 test inventory\nC840 test inventory\nC841 test inventory\n")
            write_json(root / "reviews.json", dict(schema_version=1, fixtures={}))
            write_json(root / "index.json", dict(
                schema_version=1, standard=self.registry.standard, source_inventory="source.json",
                rule_inventory="rules.txt", reviews="reviews.json", catalogues=[generated.CATALOGUE]))
            registry = Registry(root, "index.json")
            cases = runner.collect_cases(root / "tests", registry)
            self.assertEqual({case.name for case in cases}, set(self.cases) | {manifest["id"]})
            self.assertTrue(all(row["review"]["state"] == "unreviewed" for row in registry.execution._members(cases)))
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not execute a compiler")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
                registry.render()
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)

    def test_only_owned_oracle_paragraphs_are_upserted_and_raw_source_records_are_retained(self):
        catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        owner = next(row for row in catalogue["requirements"] if row["id"] == generated.RULE)
        owner["oracle"] = "Foreign first.\n\n" + generated.ORACLE_PREFIX + "old.\n\nForeign last."
        owner["oracle_limitation"] = "Foreign limit."
        changed = generated.synced_catalogue(catalogue)
        updated = next(row for row in changed["requirements"] if row["id"] == generated.RULE)
        self.assertEqual(updated["oracle"], "Foreign first.\n\n" + generated.ORACLE + "\n\nForeign last.")
        self.assertEqual(updated["oracle_limitation"], "Foreign limit.\n\n" + generated.LIMITATION)
        for key in ("review_state", "review_rationale", "review_fingerprint", "subunits", "accounting"):
            self.assertEqual(changed[key], catalogue[key])
        owner["oracle"] += "\n\n" + generated.ORACLE_PREFIX + "duplicate."
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            generated.synced_catalogue(catalogue)

    def test_exact_four_fixture_files_and_check_only_native_rendering(self):
        self.assertEqual(len(self.files), 4)
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        registry = Registry(ROOT)
        registry.catalogues = {generated.SECTION: registry.catalogues[generated.SECTION]}
        registry.render()


if __name__ == "__main__":
    unittest.main()
