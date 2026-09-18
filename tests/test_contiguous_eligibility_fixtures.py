"""C830 entity categories, exact repairs, causal reports and renewable evidence."""
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
import generate_contiguous_eligibility_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))
GNU_CAUSE = (
    "'subject' at (1) has the CONTIGUOUS attribute but is not an array pointer "
    "or an assumed-shape or assumed-rank array"
)
FLANG_CAUSE = (
    "CONTIGUOUS entity 'subject' should be an array pointer, assumed-shape, "
    "or assumed-rank [-Wredundant-contiguous]"
)
PREFIXES = ("", "Internal: ", "Not yet implemented: ", "Unimplemented: ", "Unsupported: ",
            "Internal error: ", "Verifier error: ")
POINT_NEGATIVES = ("ordinary_scalar", "scalar_pointer", "explicit_shape", "allocatable_fixed_rank")


class ContiguousEligibilityFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases
                     if "/fixtures/contiguous_eligibility_" in case.path}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}
        cls.point_negatives = [cls.cases[generated.identifier(variant, True)] for variant in POINT_NEGATIVES]

    def case(self, variant, negative=False):
        return self.cases[generated.identifier(variant, negative)]

    def test_exact_fourteen_cases_eight_facets_and_compile_only_roles(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 14)
        self.assertEqual(sum(case.kind == "invalid" for case in self.cases.values()), 5)
        self.assertEqual(len(self.point_negatives), 4)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, {
            "ordinary-scalar-excluded", "scalar-pointer-excluded", "explicit-shape-excluded",
            "allocatable-fixed-rank-excluded", "array-pointer-admission",
            "assumed-shape-admission", "assumed-rank-admission", "assumed-size-excluded",
        })
        for case in self.cases.values():
            self.assertEqual((case.rule, case.meta.standard, case.meta.oracle_basis), ("C830", "f2023", "standard"))
            self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertFalse(case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if case.kind == "invalid" else "success")
            self.assertIsNone(case.fixture.link)
            self.assertEqual(self.members[case.name]["cohort"],
                             "diagnostic-only" if case.kind == "invalid" else "positive-control")

    def test_four_actual_invalid_categories_have_no_unrelated_context_defect(self):
        declarations = {
            "ordinary_scalar": "integer, contiguous :: subject",
            "scalar_pointer": "integer, pointer, contiguous :: subject",
            "explicit_shape": "integer, contiguous :: subject(2)",
            "allocatable_fixed_rank": "integer, allocatable, contiguous :: subject(:)",
        }
        for variant, declaration in declarations.items():
            source = self.specs[generated.identifier(variant, True)]["source"]
            self.assertEqual(source, "program declaration_context\n  implicit none\n  " + declaration
                             + "\nend program declaration_context\n")
            self.assertEqual(source.count("subject"), 1)
            self.assertEqual(source.count("contiguous"), 1)
            self.assertNotIn("=", source)
            for token in ("call", "save", "data ", "common", "bind(", "kind", "target", "type ", "["):
                self.assertNotIn(token, source)
            diagnostic = self.case(variant, True).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                             ("source.f90", 3, 3))

    def test_four_repairs_preserve_every_byte_except_the_attribute_separator(self):
        for variant in ("ordinary_scalar", "scalar_pointer", "explicit_shape", "allocatable_fixed_rank"):
            negative = self.specs[generated.identifier(variant, True)]
            control = self.specs[negative["repair"]["control_id"]]
            raw, fixed = negative["source"].encode(), control["source"].encode()
            start, end = negative["repair"]["byte_span_zero_based_half_open"]
            self.assertEqual(raw[start:end], b", contiguous")
            self.assertEqual(end - start, 12)
            self.assertEqual(fixed, raw[:start] + raw[end:])
            self.assertEqual(raw.count(b"\n"), fixed.count(b"\n"))
            self.assertEqual(raw.splitlines()[:2], fixed.splitlines()[:2])
            self.assertEqual(raw.splitlines()[3:], fixed.splitlines()[3:])
            self.assertEqual(negative["repair"]["negative_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(negative["repair"]["control_sha256"], hashlib.sha256(fixed).hexdigest())
            self.assertEqual(negative["facet"], control["facet"])

    def test_admissions_use_actual_array_pointer_and_explicit_interface_dummy_categories(self):
        declarations = {
            "array_pointer": "integer, pointer, contiguous :: subject(:)",
            "assumed_shape": "integer, contiguous :: subject(:)",
            "assumed_rank": "integer, contiguous :: subject(..)",
            "allocatable_assumed_rank": "integer, allocatable, contiguous :: subject(..)",
        }
        for variant, declaration in declarations.items():
            source = self.specs[generated.identifier(variant)]["source"]
            if variant == "array_pointer":
                expected = f"program declaration_context\n  implicit none\n  {declaration}\nend program declaration_context\n"
            else:
                expected = (
                    "module eligibility_scope\n  implicit none\ncontains\n"
                    "  subroutine declaration_context(subject)\n    implicit none\n"
                    f"    {declaration}\n"
                    "  end subroutine declaration_context\nend module eligibility_scope\n"
                )
            self.assertEqual(source, expected)
            for token in ("call", "allocate(", "associated(", "is_contiguous(", "=", "print", "save", "intent"):
                self.assertNotIn(token, source)

    def staged(self, case, family, message=None, code=1, line=None, end_line=None, filename=None,
               severity=None, timed_out=False, echo_only=False, silent=False, tail="", codes=False):
        compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport, not observation")
        identity = dict(compiler.configuration(), version=compiler.version)
        fixture = case.fixture
        raw = (fixture.root / "source.f90").read_bytes()
        target = fixture.expectation.diagnostic["line"]
        first, last = (target if line is None else line), end_line
        last = first if last is None else last
        cause = message if message is not None else (FLANG_CAUSE if family == "flang" else GNU_CAUSE)
        level = severity or ("portability" if family == "flang" else "error")
        calls = []

        def transport(command, cwd, timeout, stdin=None):
            source = Path(command[command.index("-c") + 1])
            workspace = Path(cwd).resolve()
            self.assertEqual((source.parent, source.name), (workspace, "source.f90"))
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(command[0], family)
            self.assertEqual(timeout, 5)
            self.assertIsNone(stdin)
            lines = raw.decode().splitlines()
            source_line = lines[first - 1] if 1 <= first <= len(lines) else lines[target - 1]
            column = max(1, source_line.find("subject") + 1)
            location = filename or str(source)
            reported = "syntax error" if echo_only else cause
            if family == "lfortran":
                text = f"{location}:{first}-{last}:1-80: semantic {level} [C830]: {reported}\n"
            elif family == "gfortran":
                text = (f"{location}:{first}:{column}:\n\n {first:4} | {source_line}\n"
                        f"      | {' ' * (column - 1)}1\n{level.capitalize()}: {reported}\n")
            else:
                text = (f"{location}:{first}:{column}: {level}: {reported}\n"
                        f"  {source_line}\n  {' ' * (column - 1)}^^^^^^^\n")
            if echo_only:
                text += f" {first:4} | ! {cause}\n      | 1\n"
            text = "" if silent else text + tail
            calls.append(dict(command=command, workspace=str(workspace)))
            return runner.ProcessResult(code, text, timed_out, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(fixture, compiler, timeout=5, codes=codes)
        self.assertEqual((len(calls), check.phase, len(check.trace)), (1, "compile", 1))
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(check.execution_context["workspace"], calls[0]["workspace"])
        self.assertEqual(check.execution_context["compiler_resources"], {})
        self.assertFalse(validate_case_trace(self.members[case.name], asdict(check), identity, ROOT, None, False))
        return check

    def test_504_exact_causal_and_wrapped_vectors_use_actual_staging(self):
        vectors = []
        for case in self.point_negatives:
            for family, mode in FAMILIES:
                cause = FLANG_CAUSE if family == "flang" else GNU_CAUSE
                for code in (0, 1, 2):
                    for prefix in PREFIXES:
                        for codes in (False, True):
                            with self.subTest(case=case.name, family=family, code=code, prefix=prefix, codes=codes):
                                check = self.staged(case, family, prefix + cause, code=code, codes=codes)
                                self.assertEqual(check.outcome, "fail" if prefix else "pass")
                                if not prefix:
                                    self.assertEqual(check.note, "diagnoses without rejection" if code == 0 else "rejects")
                                vectors.append((case.name, family, mode, code, prefix, codes))
        self.assertEqual(len(vectors), 504)
        self.assertEqual(len(set(vectors)), 504)

    def test_wrong_location_subject_cause_and_source_echo_never_qualify(self):
        wrong = (
            "CONTIGUOUS", "array pointer assumed-shape assumed-rank", "Unrelated shape mismatch",
            GNU_CAUSE.replace("'subject'", "'other'"), FLANG_CAUSE.replace("'subject'", "'other'"),
            GNU_CAUSE.replace("CONTIGUOUS", "VOLATILE"), "Invalid kind in declaration",
            "Missing explicit interface for assumed-shape dummy", "Cannot read module eligibility_scope",
            "Duplicate CONTIGUOUS attribute", "Unknown type of subject", "Invalid initialization",
        )
        for case in self.point_negatives:
            for family, _ in FAMILIES:
                for line in (0, 1, 2, 4):
                    self.assertEqual(self.staged(case, family, line=line).outcome, "fail")
                self.assertEqual(self.staged(case, family, filename="other.f90").outcome, "fail")
                self.assertEqual(self.staged(case, family, echo_only=True).outcome, "fail")
                for message in wrong:
                    self.assertEqual(self.staged(case, family, message).outcome, "fail")
            for first, last in ((2, 3), (3, 4), (4, 3)):
                self.assertEqual(self.staged(case, "lfortran", line=first, end_line=last).outcome, "fail")

    def test_only_exact_flang_portability_is_allowed_without_error_severity(self):
        expected = [{"compiler": "flang", "severity": "portability", "equals_any": [FLANG_CAUSE]}]
        for case in self.cases.values():
            if case.kind != "invalid":
                continue
            self.assertEqual(case.fixture.expectation.diagnostic["allow_nonfatal"], expected)
            for family, _ in FAMILIES:
                for severity in ("warning", "portability"):
                    for code in (0, 1, 2):
                        check = self.staged(case, family, FLANG_CAUSE, severity=severity, code=code)
                        self.assertEqual(check.outcome, "pass" if (family, severity) == ("flang", "portability") else "fail")
            for message in (FLANG_CAUSE + " extra text", "Example: " + FLANG_CAUSE,
                            FLANG_CAUSE.removesuffix(" [-Wredundant-contiguous]")):
                self.assertEqual(self.staged(case, "flang", message).outcome, "fail")

    def test_exact_cause_selectors_preserve_the_reviewed_messages_without_substring_fallback(self):
        for case in self.cases.values():
            if case.kind != "invalid":
                continue
            diagnostic = case.fixture.expectation.diagnostic
            self.assertEqual(diagnostic["equals_any"], [GNU_CAUSE, FLANG_CAUSE])
            self.assertNotIn("contains_any", diagnostic)
            target = 6 if case == self.case("assumed_size", True) else 3
            self.assertEqual((diagnostic["line"], diagnostic["end_line"]), (target, target))
            self.assertEqual(diagnostic.get("additional_spans", []), [dict(line=4)] if target == 6 else [])
            self.assertEqual(diagnostic["allow_nonfatal"], [
                {"compiler": "flang", "severity": "portability", "equals_any": [FLANG_CAUSE]}])

    def test_216_quoted_outer_errors_cannot_borrow_a_matching_inner_cause(self):
        checked = 0
        for case in self.point_negatives:
            for family, _ in FAMILIES:
                cause = FLANG_CAUSE if family == "flang" else GNU_CAUSE
                for status in (0, 1, 2):
                    for codes in (False, True):
                        for outer in ("Example", "Unknown symbol", "Unrelated expression"):
                            message = outer + ': "' + cause + '"'
                            with self.subTest(case=case.name, family=family, status=status, codes=codes, outer=outer):
                                self.assertEqual(self.staged(
                                    case, family, message, code=status, codes=codes, severity="error").outcome, "fail")
                            checked += 1
        self.assertEqual(checked, 216)

    def test_144_foreign_origins_fail_and_216_genuine_origins_retain_cause_credit(self):
        foreign, genuine = 0, 0
        for case in self.point_negatives:
            for family, _ in FAMILIES:
                for status in (0, 1, 2):
                    for codes in (False, True):
                        for origin in ("/different/translation-unit/source.f90", "unrelated/source.f90"):
                            with self.subTest(case=case.name, family=family, status=status, codes=codes, origin=origin):
                                self.assertEqual(self.staged(
                                    case, family, filename=origin, code=status, codes=codes).outcome, "fail")
                            foreign += 1
                        for origin in (None, "source.f90", "./source.f90"):
                            with self.subTest(case=case.name, family=family, status=status, codes=codes, origin=origin):
                                self.assertEqual(self.staged(
                                    case, family, filename=origin, code=status, codes=codes).outcome, "pass")
                            genuine += 1
        self.assertEqual((foreign, genuine), (144, 216))

    def test_silence_abnormal_termination_and_native_failures_never_qualify(self):
        for case in self.cases.values():
            if case.kind != "invalid":
                continue
            for family, _ in FAMILIES:
                for code in (0, 1, 2):
                    self.assertEqual(self.staged(case, family, code=code, silent=True).outcome, "fail")
                for code in (-6, -11, 128, 134, 139):
                    self.assertEqual(self.staged(case, family, code=code).outcome, "fail")
                self.assertEqual(self.staged(case, family, code=0, timed_out=True).outcome, "fail")
                for tail in ("\ninternal compiler error: failure\n", "\nASR verify pass error\n",
                             "\nout of memory\n", "\nLLVM ERROR: failure\n", "\nerror: Internal: failure\n"):
                    self.assertEqual(self.staged(case, family, tail=tail).outcome, "fail")

    def test_each_positive_compiles_exact_bytes_without_running_an_observer(self):
        for case in self.cases.values():
            if case.kind != "valid":
                continue
            for family, mode in FAMILIES:
                compiler = runner.Compiler(family, family, mode, "synthetic positive transport")
                raw = (case.fixture.root / "source.f90").read_bytes()
                calls = []

                def transport(command, cwd, timeout, stdin=None):
                    source = Path(command[command.index("-c") + 1])
                    self.assertEqual((source.parent, source.name), (Path(cwd).resolve(), "source.f90"))
                    self.assertEqual(source.read_bytes(), raw)
                    self.assertEqual(timeout, 5)
                    self.assertIsNone(stdin)
                    Path(command[command.index("-o") + 1]).write_bytes(b"synthetic object")
                    calls.append(command)
                    return runner.ProcessResult(0, "", False, "", "", b"", b"")

                with patch.object(runner, "run", side_effect=transport):
                    check = runner.check_fixture(case.fixture, compiler, timeout=5)
                self.assertEqual((check.outcome, check.phase, len(calls)), ("pass", "compile", 1))
                self.assertFalse(validate_case_trace(
                    self.members[case.name], asdict(check), dict(compiler.configuration(), version=compiler.version),
                    ROOT, None, False))

    def test_assumed_size_preserves_original_source_repair_and_disjoint_subject_anchors(self):
        requirement = self.registry.requirements["C830"]
        self.assertNotIn("assumed-size-excluded", requirement["pending"])
        negative = self.case("assumed_size", True)
        control = self.case("assumed_size_control")
        raw = (negative.fixture.root / "source.f90").read_bytes()
        repaired = (control.fixture.root / "source.f90").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "648a3dce6d21264c0be051dec9cf0730140a321214a7075b472d50d8a5369a28")
        self.assertEqual(hashlib.sha256(repaired).hexdigest(),
                         "edcc0562d3ccec81328730fb6abc6e50a90e683c238cf2d055e666b2e300de45")
        self.assertEqual(raw[121:133], b", contiguous")
        self.assertEqual(repaired, raw[:121] + raw[133:])
        self.assertEqual((len(raw.splitlines()), len(repaired.splitlines())), (8, 8))
        self.assertEqual(raw.splitlines()[3].strip(), b"subroutine declaration_context(subject)")
        self.assertEqual(raw.splitlines()[5].strip(), b"integer, contiguous :: subject(*)")
        self.assertEqual(raw.splitlines()[4].strip(), b"implicit none")
        diagnostic = negative.fixture.expectation.diagnostic
        self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                         ("source.f90", 6, 6))
        self.assertEqual(diagnostic["additional_spans"], [dict(line=4)])
        self.assertEqual(diagnostic["equals_any"], [GNU_CAUSE, FLANG_CAUSE])
        self.assertEqual(diagnostic["excludes_any"], self.point_negatives[0].fixture.expectation.diagnostic["excludes_any"])
        self.assertEqual(diagnostic["allow_nonfatal"], self.point_negatives[0].fixture.expectation.diagnostic["allow_nonfatal"])
        for spec in self.specs.values():
            self.assertNotIn(";", spec["source"])
            if spec["kind"] == "invalid" and spec["variant"] != "assumed_size":
                self.assertEqual(spec["manifest"]["expect"]["diagnostic"]["line"], 3)
                self.assertEqual(spec["manifest"]["expect"]["diagnostic"]["end_line"], 3)
                self.assertNotIn("additional_spans", spec["manifest"]["expect"]["diagnostic"])

    def test_assumed_size_120_anchor_gap_and_cross_range_vectors(self):
        case = self.case("assumed_size", True)
        checked = 0
        for family, _ in FAMILIES:
            ranges = [(line, line) for line in (3, 4, 5, 6, 7)]
            if family == "lfortran":
                ranges += [(4, 6), (3, 4), (4, 5), (5, 6), (6, 7)]
            for status in (0, 1, 2):
                for codes in (False, True):
                    for first, last in ranges:
                        with self.subTest(family=family, status=status, codes=codes, first=first, last=last):
                            check = self.staged(case, family, code=status, codes=codes, line=first, end_line=last)
                            self.assertEqual(check.outcome, "pass" if first == last and first in (4, 6) else "fail")
                        checked += 1
        self.assertEqual(checked, 120)

    def test_assumed_size_both_anchors_keep_all_cause_origin_and_failure_gates(self):
        case = self.case("assumed_size", True)
        checked = 0
        for family, _ in FAMILIES:
            cause = FLANG_CAUSE if family == "flang" else GNU_CAUSE
            for line in (4, 6):
                for status in (0, 1, 2):
                    for codes in (False, True):
                        variants = [
                            dict(message='Example: "' + cause + '"', severity="error"),
                            dict(message='Unknown symbol "' + cause + '"', severity="error"),
                            dict(message=cause.replace("'subject'", "'other'")),
                            dict(filename="/foreign/source.f90"),
                            dict(filename="../source.f90"),
                            dict(filename="unrelated/source.f90"),
                            dict(severity="warning"),
                            dict(echo_only=True),
                            dict(silent=True),
                            dict(timed_out=True),
                            dict(tail="\n/foreign/source.f90:1:1: error: Internal: failed\n"),
                            dict(tail="\nASR verify pass error\n"),
                            dict(tail="\nout of memory\n"),
                        ]
                        variants += [dict(message=prefix + cause, severity="error") for prefix in PREFIXES[1:]]
                        for variant in variants:
                            with self.subTest(family=family, line=line, status=status, codes=codes, variant=variant):
                                self.assertEqual(self.staged(
                                    case, family, code=status, codes=codes, line=line, **variant).outcome, "fail")
                            checked += 1
                for status in (-6, -11, 128, 134, 139):
                    with self.subTest(family=family, line=line, abnormal_status=status):
                        self.assertEqual(self.staged(case, family, code=status, line=line).outcome, "fail")
                    checked += 1
        self.assertEqual(checked, 714)

    def test_assumed_size_schema_and_mutations_invalidate_the_real_contract_snapshot(self):
        original = self.case("assumed_size", True)
        fingerprint = original.fingerprint(self.registry)
        raw_manifest = original.fixture.path.read_bytes()
        raw_source = (original.fixture.root / "source.f90").read_bytes()
        for mutation in ("span", "gap", "cause", "origin", "source"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                path = directory / "fixture.json"
                path.write_bytes(raw_manifest)
                (directory / "source.f90").write_bytes(raw_source)

                def current_cases(*args, **kwargs):
                    fixture = runner.load_fixture(path, runner.PROFILES)
                    changed = replace(original, path=str(path), fixture=fixture, meta=fixture.meta)
                    return [changed if case.name == original.name else case for case in self.all_cases]

                cloned = next(case for case in current_cases() if case.name == original.name)
                self.assertEqual(cloned.fingerprint(self.registry), fingerprint)
                data = json.loads(raw_manifest)
                diagnostic = data["expect"]["diagnostic"]
                if mutation == "span":
                    diagnostic.pop("additional_spans")
                elif mutation == "gap":
                    diagnostic["additional_spans"] = [dict(line=5)]
                elif mutation == "cause":
                    diagnostic["equals_any"][0] += " changed"
                elif mutation == "origin":
                    diagnostic["file"] = "other.f90"
                else:
                    (directory / "source.f90").write_bytes(raw_source + b"\n")
                path.write_text(json.dumps(data, indent=2) + "\n")
                if mutation != "origin":
                    changed = next(case for case in current_cases() if case.name == original.name)
                    self.assertNotEqual(changed.fingerprint(self.registry), fingerprint)
                with patch.object(runner, "Registry", return_value=self.registry), \
                        patch.object(runner, "collect_cases", side_effect=current_cases):
                    errors = runner.confirm_snapshot([], [original], {original.review_key: fingerprint})
                self.assertTrue(errors)

    def test_generator_preserves_other_requirements_facets_and_administrative_records(self):
        catalogue = self.registry.catalogues["8.5.7"]
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        for pending_state in ("actual", "one-foreign-facet-cleared", "none"):
            candidate = copy.deepcopy(catalogue)
            foreign = [row for row in candidate["requirements"] if row["id"] != "C830"]
            if pending_state == "one-foreign-facet-cleared":
                foreign[0]["pending"].pop(next(iter(foreign[0]["pending"])))
            if pending_state == "none":
                for requirement in foreign:
                    requirement["pending"] = {}
            expected = copy.deepcopy(candidate)
            self.assertEqual(generated.synced_catalogue(candidate), expected)
            self.assertEqual(candidate, expected)
            text = generated.render_view(candidate)
            for row in candidate["requirements"]:
                self.assertIn(render_requirement(row), text)
            other = sum(len(row["pending"]) for row in candidate["requirements"] if row["id"] != "C830")
            self.assertIn(f"have {other} pending facets", text)
        self.assertEqual(generated.render_view(catalogue), (ROOT / generated.VIEW).read_text())
        registry = Registry(ROOT)
        registry.catalogues = {"8.5.7": catalogue}
        registry.render()

    def test_renewable_lifecycle_preserves_the_full_foreign_inventory_and_blockers(self):
        registry = Registry(ROOT)
        before = copy.deepcopy(registry.catalogues["8.5.7"])
        disk = (copy.deepcopy(registry.reviews), copy.deepcopy(registry.evidence.links),
                copy.deepcopy(registry.source_uses.data), copy.deepcopy(registry.execution.aggregates))
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(before)
            registry.catalogues["8.5.7"] = candidate
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory lifecycle, not written approval."
            candidate["review_fingerprint"] = (
                "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.5.7"))
            self.assertEqual(registry.catalogue_review_state("8.5.7"), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertIn(f"**Source review: {state}.**", generated.render_view(candidate))
        for case in self.cases.values():
            registry.reviews[case.name] = dict(
                state="source-reviewed", fingerprint=case.fingerprint(registry), sources=["C830"],
                rationale="In-memory owner-only fixture review, not written approval.")
        cases = runner.collect_cases(ROOT / "tests", registry)
        foreign = next(case for case in cases if case.name not in self.cases)
        registry.reviews[foreign.review_key] = dict(
            registry.reviews[foreign.review_key], state="unreviewed",
            rationale="Explicit foreign blocker, never discarded or written to disk.")
        members = registry.execution._members(cases)
        self.assertEqual({row["id"] for row in members}, {case.name for case in self.all_cases})
        self.assertEqual(next(row for row in members if row["id"] == foreign.name)["review"]["state"], "unreviewed")
        for report in registry.execution.report(cases, include_members=False):
            aggregate = registry.execution.aggregates[report["id"]]
            aggregate["review"] = dict(
                aggregate["review"], state="source-reviewed", fingerprint=report["review"]["fingerprint"],
                rationale="In-memory exact inventory review retaining all foreign blockers.")
            registry.execution._validate(aggregate)
        for report in registry.execution.report(cases, include_members=False):
            self.assertTrue(report["blockers"])
            self.assertEqual(report["state"], "stale")
            self.assertEqual(report["member_count"], len(self.all_cases))
        fresh = Registry(ROOT)
        self.assertEqual((fresh.reviews, fresh.evidence.links, fresh.source_uses.data, fresh.execution.aggregates), disk)

    def test_exact_generated_files_and_byte_stable_reexecution(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("contiguous_eligibility_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 28)
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")


if __name__ == "__main__":
    unittest.main()
