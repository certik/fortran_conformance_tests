"""Ordinary-array C834 source roles, exact repairs and finite reporting evidence."""
import copy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_validation import validate_case_trace
from suite_data import Registry, render_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_c834_array_shape_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))
EXPECTED_CAUSES = {
    "pointer_scalar": [
        "Pointer array 'a' must have a deferred shape or assumed rank",
        "Array pointer 'a' at (1) must have a deferred shape or assumed rank",
        "Array pointer 'a' must have deferred shape or assumed rank",
    ],
    "pointer_vector": [
        "Array pointer 'a' at (1) must have a deferred shape or assumed rank",
        "Array pointer 'a' must have deferred shape or assumed rank",
    ],
    "allocatable_scalar": [
        "Allocatable array 'a' must have a deferred shape or assumed rank",
        "Allocatable array 'a' at (1) must have a deferred shape or assumed rank",
        "Allocatable array 'a' must have deferred shape or assumed rank",
    ],
    "allocatable_vector": [
        "Allocatable array 'a' at (1) must have a deferred shape or assumed rank",
        "Allocatable array 'a' must have deferred shape or assumed rank",
    ],
}
SCALAR_ONLY_REPORTS = (
    "Expecting a scalar integer or parameter annotated integer variable ",
    "Must be a scalar value, but is a rank-1 array",
)


class C834ArrayShapeFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if case.rule == "C834"}
        cls.files, cls.specs = generated.build_corpus()
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}
        cls.negatives = [cls.cases[generated.identifier(name, True)] for name in EXPECTED_CAUSES]

    def test_exact_eight_IDs_three_facets_and_compile_only_roles(self):
        identifiers = {
            "C834_" + kind + "__array_shape_" + attribute + "_" + form + suffix
            for attribute in ("pointer", "allocatable") for form in ("scalar", "vector")
            for kind, suffix in (("invalid", ""), ("valid", "_control"))
        }
        self.assertEqual(set(self.cases), identifiers)
        self.assertEqual(set(self.specs), identifiers)
        self.assertEqual(len(self.cases), 8)
        self.assertEqual(len(self.negatives), 4)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {"pointer-deferred-list", "allocatable-deferred-list", "explicit-bound-exclusion"})
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.rule, case.meta.standard, case.meta.oracle_basis), ("C834", "f2023", "standard"))
            self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
            self.assertEqual(case.meta.facets, ["explicit-bound-exclusion"] if case.kind == "invalid" else
                             [spec["attribute"] + "-deferred-list", "explicit-bound-exclusion"])
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertIsNone(case.fixture.link)
            self.assertEqual(self.members[case.name]["cohort"],
                             "diagnostic-only" if case.kind == "invalid" else "positive-control")

    def test_complete_local_source_has_only_the_selected_array_declaration(self):
        for case in self.cases.values():
            spec = self.specs[case.name]
            raw = (case.fixture.root / "source.f90").read_bytes()
            expected = (
                "subroutine array_shape_context()\n"
                "  implicit none\n"
                f"  integer, {spec['attribute']} :: a({spec['array_spec']})\n"
                "end subroutine array_shape_context\n"
            )
            self.assertEqual(raw.decode("ascii"), expected)
            self.assertEqual(len(raw.splitlines()), 4)
            self.assertEqual(raw.count(b"::"), 1)
            for token in (b"save", b"=", b"call", b"allocate(", b"associated(", b"size(", b"shape(",
                          b"rank(", b"intent", b"target", b"data ", b"type ", b"bind(", b"common"):
                self.assertNotIn(token, raw)
            self.assertEqual(spec["rank"], 1)
            if case.kind == "invalid" and spec["bound_form"] == "vector":
                self.assertIn(b"a([2])", raw)
                self.assertNotIn(b":: ]", raw)

    def test_each_repair_changes_only_the_same_rank_array_spec(self):
        for case in self.negatives:
            spec = self.specs[case.name]
            control = self.cases[generated.identifier(spec["variant"] + "_control", False)]
            raw = (case.fixture.root / "source.f90").read_bytes()
            fixed = (control.fixture.root / "source.f90").read_bytes()
            start, end = spec["repair"]["byte_span_zero_based_half_open"]
            expected = b"[2]" if spec["bound_form"] == "vector" else b"2"
            self.assertEqual(raw[start:end], expected)
            self.assertEqual(raw[:start] + b":" + raw[end:], fixed)
            self.assertEqual(raw.splitlines()[:2], fixed.splitlines()[:2])
            self.assertEqual(raw.splitlines()[3:], fixed.splitlines()[3:])
            self.assertEqual(raw.count(b"\n"), fixed.count(b"\n"))
            self.assertEqual(spec["repair"]["negative_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(spec["repair"]["control_sha256"], hashlib.sha256(fixed).hexdigest())
            self.assertEqual(control.meta.facets, [spec["attribute"] + "-deferred-list", "explicit-bound-exclusion"])

    def test_exact_case_specific_calibrated_causes_have_no_warning_or_vector_error_fallback(self):
        for case in self.negatives:
            spec = self.specs[case.name]
            diagnostic = case.fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]), ("source.f90", 3, 3))
            self.assertEqual(diagnostic["equals_any"], EXPECTED_CAUSES[spec["variant"]])
            self.assertNotIn("contains_any", diagnostic)
            self.assertNotIn("additional_spans", diagnostic)
            self.assertFalse(diagnostic.get("allow_nonfatal"))
            for message in SCALAR_ONLY_REPORTS:
                self.assertNotIn(message.strip(), diagnostic["equals_any"])

    def staged(self, case, family, message=None, status=1, codes=False, filename=None,
               first=3, last=3, severity="error", silent=False, echo_only=False,
               timed_out=False, tail="", has_code=True, object_exists=False):
        compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport, not observation")
        raw = (case.fixture.root / "source.f90").read_bytes()
        if message is None:
            message = case.fixture.expectation.diagnostic["equals_any"][0] if case.kind == "invalid" else ""
        calls = []

        def transport(command, cwd, timeout, stdin=None):
            source = Path(command[command.index("-c") + 1])
            workspace = Path(cwd).resolve()
            self.assertEqual(source, workspace / "source.f90")
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(timeout, 5)
            self.assertIsNone(stdin)
            origin = filename or str(source)
            label = " [C834]" if has_code else ""
            body = "unrelated expression" if echo_only else message
            text = (f"{origin}:{first}-{last}:1-80: semantic {severity}{label}: {body}\n"
                    if family == "lfortran" else f"{origin}:{first}:1: {severity}: {body}\n")
            if echo_only:
                text += f"    3 | ! {message}\n      | 1\n"
            text = ("" if silent else text) + tail
            if object_exists:
                Path(command[command.index("-o") + 1]).write_bytes(b"synthetic object, not native")
            calls.append(command)
            return runner.ProcessResult(status, text, timed_out, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5, codes=codes)
        self.assertEqual((len(calls), len(check.trace), check.phase), (1, 1, "compile"))
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertFalse(validate_case_trace(
            self.members[case.name], asdict(check), dict(compiler.configuration(), version=compiler.version),
            ROOT, None, False))
        return check

    def test_180_genuine_full_cause_vectors_allow_ordinary_statuses_and_codes(self):
        rows = []
        for case in self.negatives:
            for cause in case.fixture.expectation.diagnostic["equals_any"]:
                for family, mode in FAMILIES:
                    for status in (0, 1, 2):
                        for codes in (False, True):
                            with self.subTest(id=case.name, cause=cause, family=family, status=status, codes=codes):
                                check = self.staged(case, family, cause, status=status, codes=codes)
                                self.assertEqual(check.outcome, "pass")
                                self.assertEqual(check.note, "diagnoses without rejection" if status == 0 else "rejects")
                            rows.append((case.name, cause, family, mode, status, codes))
        self.assertEqual(len(rows), 180)
        self.assertEqual(len(set(rows)), 180)

    def test_720_quoted_and_unrelated_envelopes_do_not_borrow_the_full_cause(self):
        count = 0
        for case in self.negatives:
            for cause in case.fixture.expectation.diagnostic["equals_any"]:
                for family, _ in FAMILIES:
                    for status in (0, 1, 2):
                        for codes in (False, True):
                            for message in ('Example: "' + cause + '"', 'Unknown symbol "' + cause + '"',
                                            "Unrelated failure: " + cause, cause + " quoted as an example"):
                                with self.subTest(id=case.name, family=family, status=status, codes=codes, message=message):
                                    self.assertEqual(self.staged(
                                        case, family, message, status=status, codes=codes).outcome, "fail")
                                count += 1
        self.assertEqual(count, 720)

    def test_scalar_only_vector_diagnostics_are_not_C834_causes(self):
        for case in self.negatives:
            for family, _ in FAMILIES:
                for status in (0, 1, 2):
                    for message in SCALAR_ONLY_REPORTS:
                        with self.subTest(id=case.name, family=family, status=status, message=message):
                            self.assertEqual(self.staged(case, family, message, status=status).outcome, "fail")
                    for prefix in ("Not yet implemented: ", "Not implemented: ", "Unimplemented: ", "Unsupported: ",
                                   "Internal: ", "Invalid kind: ", "Verifier: "):
                        self.assertEqual(self.staged(
                            case, family, prefix + case.fixture.expectation.diagnostic["equals_any"][0],
                            status=status).outcome, "fail")

    def test_genuine_cause_and_unqualified_secondary_scalar_complaint_remain_distinct(self):
        for case in self.negatives:
            if self.specs[case.name]["bound_form"] != "vector":
                continue
            cause = case.fixture.expectation.diagnostic["equals_any"][-1]
            tail = "\nsource.f90:3:25: error: Must be a scalar value, but is a rank-1 array\n"
            for status in (0, 1, 2):
                self.assertEqual(self.staged(case, "flang", cause, status=status, tail=tail).outcome, "pass")
                self.assertEqual(self.staged(case, "flang", SCALAR_ONLY_REPORTS[1], status=status).outcome, "fail")

    def test_720_wrong_origin_line_token_and_nonfatal_vectors_fail(self):
        count = 0
        for case in self.negatives:
            cause = case.fixture.expectation.diagnostic["equals_any"][0]
            for family, _ in FAMILIES:
                for status in (0, 1, 2):
                    for codes in (False, True):
                        variants = (
                            dict(filename="/foreign/source.f90"), dict(filename="unrelated/source.f90"),
                            dict(filename="../source.f90"), dict(first=2, last=2), dict(first=4, last=4),
                            dict(message=cause.replace("'a'", "'other'")), dict(severity="warning"),
                            dict(severity="portability"), dict(echo_only=True), dict(silent=True),
                        )
                        for variant in variants:
                            with self.subTest(id=case.name, family=family, status=status, codes=codes, variant=variant):
                                self.assertEqual(self.staged(
                                    case, family, status=status, codes=codes, **variant).outcome, "fail")
                            count += 1
        self.assertEqual(count, 720)

    def test_recovery_ranges_native_failures_and_code_flag_never_supply_credit(self):
        for case in self.negatives:
            for first, last in ((2, 3), (3, 4), (1, 4), (4, 3), (0, 3)):
                self.assertEqual(self.staged(case, "lfortran", first=first, last=last).outcome, "fail")
            for family, _ in FAMILIES:
                for status in (-6, -11, 128, 134, 139):
                    self.assertEqual(self.staged(case, family, status=status).outcome, "fail")
                self.assertEqual(self.staged(case, family, timed_out=True).outcome, "fail")
                for tail in ("\n/foreign/source.f90:1:1: error: Internal: failure\n",
                             "\nASR verify pass error\n", "\nLLVM ERROR: failure\n", "\nout of memory\n"):
                    self.assertEqual(self.staged(case, family, tail=tail).outcome, "fail")
                for codes in (False, True):
                    expected = "fail" if family == "lfortran" and codes else "pass"
                    self.assertEqual(self.staged(case, family, codes=codes, has_code=False).outcome, expected)

    def test_controls_require_objects_and_never_run(self):
        count = 0
        for case in self.cases.values():
            if case.kind != "valid":
                continue
            for family, _ in FAMILIES:
                for exists in (False, True):
                    check = self.staged(case, family, status=0, silent=True, object_exists=exists)
                    self.assertEqual(check.outcome, "pass" if exists else "fail")
                    count += 1
        self.assertEqual(count, 24)

    def test_only_selected_C834_facets_are_represented_and_foreign_plans_are_preserved(self):
        requirement = self.registry.requirements["C834"]
        self.assertEqual(set(requirement["pending"]), {
            "rank-clause-alternative", "scalar-assumed-rank-boundary", "component-grammar-source"})
        catalogue = self.registry.catalogues["8.5.8.4"]
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        for change in ("actual", "one-foreign", "all-foreign", "unselected-owner-facet"):
            candidate = copy.deepcopy(catalogue)
            foreign = [item for item in candidate["requirements"] if item["id"] != "C834"]
            if change == "one-foreign":
                foreign[0]["pending"].pop(next(iter(foreign[0]["pending"])))
            elif change == "all-foreign":
                for item in foreign:
                    item["pending"] = {}
            elif change == "unselected-owner-facet":
                next(item for item in candidate["requirements"] if item["id"] == "C834")["pending"].pop(
                    "rank-clause-alternative")
            before = copy.deepcopy(candidate)
            self.assertEqual(generated.synced_catalogue(candidate), before)
            self.assertEqual(candidate, before)
            text = generated.render_view(candidate)
            self.assertIn(f"have {sum(len(item['pending']) for item in foreign)} pending facets", text)
            for item in candidate["requirements"]:
                self.assertIn(render_requirement(item), text)
        self.assertEqual(generated.render_view(catalogue), (ROOT / generated.VIEW).read_text())

    def test_renewable_source_reviews_and_foreign_blockers_retain_the_whole_population(self):
        registry = Registry(ROOT)
        catalogue = registry.catalogues["8.5.8.4"]
        disk = (copy.deepcopy(registry.reviews), copy.deepcopy(registry.evidence.data),
                copy.deepcopy(registry.source_uses.data), copy.deepcopy(registry.execution.data))
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(catalogue)
            registry.catalogues["8.5.8.4"] = candidate
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "Synthetic in-memory lifecycle, not a written review."
            candidate["review_fingerprint"] = (
                "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.5.8.4"))
            self.assertEqual(registry.catalogue_review_state("8.5.8.4"), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertIn(f"**Source review: {state}.**", generated.render_view(candidate))
        for case in self.cases.values():
            registry.reviews[case.review_key] = dict(
                state="source-reviewed", fingerprint=case.fingerprint(registry), sources=["C834"],
                rationale="Synthetic owner-only source review, never written.")
        foreign = next(case for case in self.all_cases if case.name not in self.cases)
        registry.reviews[foreign.review_key] = dict(
            registry.reviews[foreign.review_key], state="unreviewed", rationale="Explicit foreign blocker retained.")
        for item in registry.execution.report(self.all_cases, include_members=False):
            record = registry.execution.aggregates[item["id"]]
            record["review"] = dict(record["review"], state="source-reviewed",
                                    fingerprint=item["review"]["fingerprint"], rationale="Synthetic exact snapshot.")
        for item in registry.execution.report(self.all_cases, include_members=False):
            self.assertEqual(item["member_count"], len(self.all_cases))
            self.assertEqual(set(item["member_ids"]), {case.name for case in self.all_cases})
            self.assertEqual(item["state"], "stale")
            self.assertTrue(any(foreign.name in reason for reason in item["blockers"]))
        fresh = Registry(ROOT)
        self.assertEqual((fresh.reviews, fresh.evidence.data, fresh.source_uses.data, fresh.execution.data), disk)

    def test_real_source_cause_and_origin_mutations_invalidate_selected_snapshot(self):
        original = self.negatives[0]
        fingerprint = original.fingerprint(self.registry)
        for mutation in ("source", "cause", "origin", "line"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                path = directory / "fixture.json"
                path.write_bytes(original.fixture.path.read_bytes())
                source = directory / "source.f90"
                source.write_bytes((original.fixture.root / "source.f90").read_bytes())

                def collected(*args, **kwargs):
                    fixture = runner.load_fixture(path, runner.PROFILES)
                    updated = replace(original, path=str(path), fixture=fixture, meta=fixture.meta)
                    return [updated if case.name == original.name else case for case in self.all_cases]

                cloned = next(case for case in collected() if case.name == original.name)
                self.assertEqual(cloned.fingerprint(self.registry), fingerprint)
                data = json.loads(path.read_bytes())
                diagnostic = data["expect"]["diagnostic"]
                if mutation == "source":
                    source.write_bytes(source.read_bytes() + b"\n")
                elif mutation == "cause":
                    diagnostic["equals_any"][0] += " changed"
                elif mutation == "origin":
                    diagnostic["file"] = "other.f90"
                else:
                    diagnostic["line"] = diagnostic["end_line"] = 2
                path.write_text(json.dumps(data, indent=2) + "\n")
                with patch.object(runner, "Registry", return_value=self.registry), \
                        patch.object(runner, "collect_cases", side_effect=collected):
                    self.assertTrue(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}))

    def test_generator_is_byte_idempotent_and_owns_exactly_sixteen_files(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("c834_array_shape_*/*") if path.is_file()}
        self.assertEqual(len(actual), 16)
        self.assertEqual(actual, set(self.files))
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")


if __name__ == "__main__":
    unittest.main()
