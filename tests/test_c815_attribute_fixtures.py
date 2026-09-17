"""Exact cross-statement repairs, causal contracts and legitimate administrative transitions."""
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from case_contracts import apply_case_contracts
from execution_commands import case_plan
from execution_validation import validate_case_trace
import run_tests as runner
from suite_data import Registry, SuiteError, case_review_bindings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_c815_attribute_fixtures as generated

FACETS = {"allocatable-stmt": "repeat-allocatable", "dimension-stmt": "repeat-dimension",
          "intent-stmt": "repeat-intent", "save-stmt": "repeat-save", "access-stmt": "repeat-public"}
MARKERS = {"allocatable-stmt": 7, "dimension-stmt": 13, "intent-stmt": 19, "save-stmt": 24, "access-stmt": 30}
FIRST = {
    "allocatable-stmt": "    integer, allocatable :: b(:)\n",
    "dimension-stmt": "    integer, dimension(3) :: a\n",
    "intent-stmt": "    integer, intent(in) :: x\n",
    "save-stmt": "    integer, save :: n = 0\n",
    "access-stmt": "    integer, public :: m = 1\n",
}
SECOND = {
    "allocatable-stmt": "    allocatable :: b   ! {error C815 allocatable-stmt}\n",
    "dimension-stmt": "    dimension :: a(3)   ! {error C815 dimension-stmt}\n",
    "intent-stmt": "    intent(in) :: x   ! {error C815 intent-stmt}\n",
    "save-stmt": "    save :: n   ! {error C815 save-stmt}\n",
    "access-stmt": "    public :: m   ! {error C815 access-stmt}\n",
}
GNU_MESSAGES = {
    "allocatable-stmt": "Duplicate ALLOCATABLE attribute specified at (1)",
    "dimension-stmt": "Duplicate DIMENSION attribute specified at (1)",
    "intent-stmt": "INTENT (IN) conflicts with INTENT(IN) at (1)",
    "save-stmt": "Legacy Extension: Duplicate SAVE attribute specified at (1)",
    "access-stmt": "ACCESS specification at (1) was already specified",
}


def diagnostic_output(family, line, message, severity="error", filename="C815_invalid.f90"):
    if family == "lfortran":
        return f"{filename}:{line}-{line}:5-40: semantic {severity}: {message}\n"
    return f"{filename}:{line}:5:\n{severity}: {message}\n"


class C815AttributeFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.pairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.by_name = {case.name: case for case in cls.all_cases}
        cls.negative = {label: cls.by_name["C815_invalid:" + label] for label in FACETS}
        cls.controls = {label: cls.by_name[generated.control_id(label)] for label in FACETS}
        cls.sidecar = json.loads((ROOT / generated.SIDECAR).read_text())

    def test_exact_eleven_cases_and_individual_facet_roles(self):
        names = set(self.negative_case_ids()) | {case.name for case in self.controls.values()} | {"C815_valid"}
        self.assertEqual({case.name for case in runner.select_cases(self.all_cases, sorted(names))}, names)
        self.assertEqual({case.name for case in runner.select_cases(self.all_cases, ["C815"])}, names)
        self.assertEqual(len(names), 11)
        for label, case in self.controls.items():
            self.assertEqual((case.rule, case.kind, case.meta.evidence, case.meta.standard), ("C815", "valid", "positive-control", "f2023"))
            self.assertEqual(case.meta.facets, [FACETS[label]])
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.outcome), ("compile", "success"))
            self.assertIsNone(case.fixture.link)
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)

    def negative_case_ids(self):
        return ["C815_invalid:" + label for label in FACETS]

    def test_original_container_and_valid_complete_body_are_pinned(self):
        invalid = (ROOT / generated.INVALID).read_bytes()
        self.assertEqual(hashlib.sha256(invalid).hexdigest(), "1a75480da64388dfd60a50c2170dd4147c8709d2252a07793afcd005aa9b849c")
        self.assertEqual(runner.metadata(str(ROOT / generated.INVALID), "C815").facets, [])
        valid = (ROOT / generated.VALID).read_bytes()
        self.assertTrue(valid.startswith(b"! covers: mixed-single-specification\n"))
        body = valid[len(b"! covers: mixed-single-specification\n"):]
        self.assertEqual(hashlib.sha256(body).hexdigest(), "1eeac48954c88e528408bb1aa2b9be38dd1326b496d0e8f5d7f5b9dfb5d3bd57")
        for fragment in (
            b"integer :: m = 1\n    public :: m\n", b"integer, private :: p = 2\n",
            b"get_p = p\n", b"allocatable :: b_alloc(:)\n    integer :: b_alloc\n",
            b"dimension :: b(2)\n", b"if (m /= 1 .or. get_p() /= 2) error stop\n",
            b"if (size(a) /= 3 .or. size(b) /= 2 .or. size(b_alloc) /= 2) error stop\n",
        ):
            self.assertIn(fragment, body)
        case = self.by_name["C815_valid"]
        self.assertEqual(case.meta.facets, ["mixed-single-specification"])
        self.assertEqual((case.meta.standard, case.meta.evidence, case.review_key), ("", "effect", "C815_valid"))
        self.assertEqual(case_plan(case)["expectation"]["phase"], "run")
        self.assertIsNone(case.fixture)

    def test_each_repair_deletes_only_statement_syntax_preserving_comments_and_padding(self):
        actual = {item[2]: item for item in runner.isolated_cases(str(ROOT / generated.INVALID), "C815")}
        self.assertEqual(set(actual), set(FACETS))
        expected_spans = {"access-stmt": [102, 113], "allocatable-stmt": [295, 311],
                          "dimension-stmt": [95, 112], "intent-stmt": [97, 112], "save-stmt": [98, 107]}
        for label, pair in self.pairs.items():
            raw = actual[label][-1].encode()
            repaired = (self.controls[label].fixture.root / "source.f90").read_bytes()
            start, end = pair["repair"]["byte_span_zero_based_half_open"]
            syntax = SECOND[label].split("!", 1)[0].strip()
            self.assertEqual([start, end], expected_spans[label])
            self.assertEqual(raw[start:end], syntax.encode())
            self.assertEqual(repaired, raw[:start] + raw[end:])
            self.assertEqual(len(raw.splitlines()), 31)
            self.assertEqual(len(repaired.splitlines()), 31)
            before, after = raw.splitlines(keepends=True), repaired.splitlines(keepends=True)
            self.assertEqual(before[MARKERS[label] - 2].decode(), FIRST[label])
            self.assertEqual(after[MARKERS[label] - 2].decode(), FIRST[label])
            self.assertEqual([i + 1 for i, values in enumerate(zip(before, after)) if values[0] != values[1]], [MARKERS[label]])
            self.assertEqual(after[MARKERS[label] - 1], SECOND[label].replace(syntax, "", 1).encode())
            self.assertTrue(after[MARKERS[label] - 1].startswith(b"    "))
            self.assertTrue(after[MARKERS[label] - 1].endswith(b"\n"))
            self.assertEqual(pair["negative_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(pair["repaired_sha256"], hashlib.sha256(repaired).hexdigest())
            self.assertIn(("{error C815 " + label + "}").encode(), repaired)
            self.assertEqual(pair["repair"]["statement_line"], MARKERS[label])
            self.assertTrue(pair["repair"]["comment_and_newline_preserved"])
            self.assertEqual(self.controls[label].fixture.expectation.outcome, "success")

    def test_repairs_preserve_type_shape_initializers_and_all_body_operations(self):
        required = {
            "allocatable-stmt": ["subroutine c815_allocatable_stmt()", "integer, allocatable :: b(:)", "allocate(b(2))"],
            "dimension-stmt": ["subroutine c815_dimension_stmt()", "integer, dimension(3) :: a", "a = 1"],
            "intent-stmt": ["subroutine c815_intent_stmt(x)", "integer, intent(in) :: x"],
            "save-stmt": ["subroutine c815_save_twice()", "integer, save :: n = 0", "n = n + 1"],
            "access-stmt": ["module c815_public_twice", "integer, public :: m = 1"],
        }
        for label, fragments in required.items():
            text = self.pairs[label]["repaired_source"]
            self.assertIn("implicit none", text)
            self.assertIn("end module" if label == "access-stmt" else "end subroutine", text)
            for fragment in fragments:
                self.assertIn(fragment, text)
            self.assertNotIn("real, allocatable", text)
            self.assertNotIn("intent(out)", text)
            self.assertNotIn("intent(inout)", text)
            self.assertNotIn("rank(", text)
        saved = self.pairs["save-stmt"]["repaired_source"]
        self.assertEqual(saved.count("integer, save :: n = 0"), 1)
        self.assertNotRegex(saved, r"(?m)^\s*save :: n")
        self.assertNotIn("x =", self.pairs["intent-stmt"]["repaired_source"])

    def test_per_case_diagnose_span_and_metadata_migration(self):
        self.assertEqual(set(self.sidecar), {"schema_version", "cases"})
        self.assertEqual(set(self.sidecar["cases"]), set(FACETS))
        groups, _ = case_review_bindings(self.all_cases, self.registry)
        self.assertNotIn("C815_invalid", groups)
        for label, case in self.negative.items():
            self.assertEqual(case.meta.facets, [FACETS[label]])
            self.assertEqual(case.review_key, case.name)
            self.assertEqual(set(groups[case.name]), {case.name})
            self.assertEqual(case.contract["outcome"], "diagnose")
            self.assertEqual(case.contract["diagnostic"]["file"], "C815_invalid.f90")
            self.assertEqual(case.contract["diagnostic"]["line"], MARKERS[label] - 1)
            self.assertEqual(case.contract["diagnostic"]["end_line"], MARKERS[label])
            self.assertEqual(case.isolated[-1], self.pairs[label]["negative_source"])
            self.assertEqual({k: v for k, v in asdict(case.meta).items() if k != "facets"}, {
                "evidence": "effect", "coarray": False, "profiles": [], "images": 1, "standard": "",
                "reference_warnings": [], "oracle_basis": "standard", "oracle_profile": ""})
            self.assertEqual(case_plan(case)["expectation"]["outcome"], "diagnose")

    def judge(self, label, family, text, code=1, timeout=False):
        compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023" if family == "gfortran" else "f2018")
        return runner.judge_diagnostic(runner.ProcessResult(code, text, timeout), compiler, "C815",
                                       self.negative[label].contract["diagnostic"])

    def test_calibrated_reporting_accepts_ordinary_zero_and_nonzero_without_rule_codes(self):
        for label, message in GNU_MESSAGES.items():
            for line in (MARKERS[label] - 1, MARKERS[label]):
                for code in (0, 1, 2):
                    result = self.judge(label, "gfortran", diagnostic_output("gfortran", line, message), code)
                    self.assertEqual(result.outcome, "pass")
                    self.assertEqual(result.note, "diagnoses without rejection" if code == 0 else "rejects")
        for family, label, message in (
            ("lfortran", "dimension-stmt", "Duplicate DIMENSION attribute specified"),
            ("flang", "allocatable-stmt", "ALLOCATABLE attribute was already specified on 'b'"),
            ("flang", "dimension-stmt", "The dimensions of 'a' have already been declared"),
            ("flang", "intent-stmt", "INTENT_IN attribute was already specified on 'x'"),
        ):
            self.assertEqual(self.judge(label, family, diagnostic_output(family, MARKERS[label], message), 0).outcome, "pass")

    def test_actual_public_and_save_warnings_are_raw_reports_not_credited_by_this_schema(self):
        for label, message in (
            ("access-stmt", "The accessibility of 'm' has already been specified as PUBLIC [-Wredundant-attribute]"),
            ("save-stmt", "SAVE attribute was already specified on 'n' [-Wredundant-attribute]"),
        ):
            text = diagnostic_output("flang", MARKERS[label], message, "warning")
            self.assertEqual(list(runner.reference_messages(text, "C815_invalid.f90")),
                             [(MARKERS[label], "warning", message)])
            for code in (0, 1):
                self.assertEqual(self.judge(label, "flang", text, code).outcome, "fail")
            self.assertNotIn("allow_nonfatal", self.sidecar["cases"][label]["diagnostic"])

    def test_wrong_attribute_subject_payload_implicit_confirmation_and_recovery_are_not_causes(self):
        bad = {
            "allocatable-stmt": ["Duplicate POINTER attribute specified", "ALLOCATABLE", "ALLOCATABLE attribute was already specified on 'other'"],
            "dimension-stmt": ["Invalid array specification", "DIMENSION", "The dimensions of 'other' have already been declared"],
            "intent-stmt": ["INTENT (OUT) conflicts with INTENT(IN)", "INTENT (INOUT) conflicts with INTENT(INOUT)", "INTENT_IN attribute was already specified on 'other'"],
            "save-stmt": ["Implicit SAVE confirmed by explicit specification", "SAVE", "SAVE attribute was already specified on 'other'"],
            "access-stmt": ["Default PUBLIC confirmed", "PUBLIC", "The accessibility of 'other' has already been specified as PUBLIC"],
        }
        for label, messages in bad.items():
            for family in ("lfortran", "gfortran", "flang"):
                for message in messages + ["syntax error", "expected statement", "missing interface", "has no implicit type"]:
                    self.assertEqual(self.judge(label, family, diagnostic_output(family, MARKERS[label], message)).outcome, "fail")

    def test_only_the_first_second_relation_span_and_real_diagnostic_can_match(self):
        for label, message in GNU_MESSAGES.items():
            for line in (1, MARKERS[label] - 2, MARKERS[label] + 1, 31):
                self.assertEqual(self.judge(label, "gfortran", diagnostic_output("gfortran", line, message)).outcome, "fail")
            self.assertEqual(self.judge(label, "gfortran", diagnostic_output("gfortran", MARKERS[label], message, filename="other.f90")).outcome, "fail")
            echo = f"C815_invalid.f90:{MARKERS[label]}:5:\n {MARKERS[label]} | ! {message}\n      | 1\nError: syntax error\n"
            self.assertEqual(self.judge(label, "gfortran", echo).outcome, "fail")
            self.assertEqual(self.judge(label, "lfortran", "! " + message).outcome, "fail")

    def test_native_failure_and_unsupported_envelopes_never_corroborate_repetition(self):
        for label, message in GNU_MESSAGES.items():
            for family in ("lfortran", "gfortran", "flang"):
                good = diagnostic_output(family, MARKERS[label], message)
                for prefix in ("Unsupported facility: ", "Not implemented: ", "Recovery: "):
                    self.assertEqual(self.judge(label, family, diagnostic_output(family, MARKERS[label], prefix + message)).outcome, "fail")
                for tail in ("error: Internal: verifier failed\n", "internal compiler error: failure\n",
                             "ASR verify pass error\n", "out of memory\n"):
                    self.assertEqual(self.judge(label, family, good + tail).outcome, "fail")
                for code in (-11, 139):
                    self.assertEqual(self.judge(label, family, good, code).outcome, "fail")
                self.assertEqual(self.judge(label, family, good, 0, True).outcome, "fail")

    def test_exact_540_prefix_vectors_stage_all_roles_endpoints_modes_and_statuses(self):
        prefixes = ("", "Not implemented: ", "Unsupported facility: ", "Not yet implemented: ", "Unimplemented: ", "Internal: ")
        members = {member["id"]: member for member in self.registry.execution._members(list(self.negative.values()))}
        vectors = []
        for label, case in self.negative.items():
            source = case.isolated[-1].encode()
            self.assertEqual(len(source.splitlines()), 31)
            diagnostic = case.contract["diagnostic"]
            message = diagnostic["contains_any"][0]
            for family, mode in (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018")):
                compiler = runner.Compiler(family, family, mode, "mocked transport")
                identity = dict(compiler.configuration(), version=compiler.version)
                for line in (diagnostic["line"], diagnostic["end_line"]):
                    for code in (0, 1, 2):
                        for prefix in prefixes:
                            with self.subTest(case=case.name, family=family, mode=mode, line=line, code=code, prefix=prefix):
                                captured = []

                                def transport(command, cwd, timeout, stdin=None):
                                    staged = Path(command[-1])
                                    self.assertEqual(staged.name, "C815_invalid.f90")
                                    self.assertEqual(staged.parent.resolve(), Path(cwd).resolve())
                                    self.assertEqual(staged.read_bytes(), source)
                                    self.assertEqual(timeout, 5)
                                    self.assertIsNone(stdin)
                                    if family == "lfortran":
                                        text = f"{staged}:{line}-{line}:5-40: semantic error: {prefix}{message}\n"
                                    else:
                                        text = f"{staged}:{line}:5: error: {prefix}{message}\n"
                                    captured.append(text)
                                    return runner.ProcessResult(code, text, False, "", text, b"", text.encode())

                                with patch.object(runner, "run", side_effect=transport):
                                    checked = runner.execute_case(case, compiler, timeout=5)
                                self.assertEqual(len(captured), 1)
                                self.assertEqual(checked.phase, "compile")
                                self.assertEqual(len(checked.trace), 1)
                                self.assertEqual(checked.input_hashes, {"C815_invalid.f90": hashlib.sha256(source).hexdigest()})
                                self.assertFalse(validate_case_trace(
                                    members[case.name], asdict(checked), identity, ROOT, None, False))
                                self.assertEqual(checked.outcome, "fail" if prefix else "pass")
                                vectors.append((case.name, family, mode, line, code, prefix))
        self.assertEqual(len(vectors), 540)
        self.assertEqual(len(set(vectors)), 540)

    def temporary_cases(self, directory, data):
        source = directory / "C815_invalid.f90"
        source.write_bytes((ROOT / generated.INVALID).read_bytes())
        source.with_suffix(".cases.json").write_text(json.dumps(data))
        cases = [runner.SuiteCase("C815_invalid:" + item[2], "C815", "invalid", str(source),
                                  runner.metadata(str(source), "C815"), "C815_invalid", isolated=item)
                 for item in runner.isolated_cases(str(source), "C815")]
        apply_case_contracts(cases, runner.PROFILES, directory)
        return cases

    def test_sidecar_schema_is_exact_and_no_warning_or_standard_extension_is_injected(self):
        mutations = [
            lambda data: data["cases"].pop("save-stmt"),
            lambda data: data["cases"].update(extra=data["cases"]["save-stmt"]),
            lambda data: data["cases"]["save-stmt"].update(outcome="reject"),
            lambda data: data["cases"]["save-stmt"].update(standard="f2023"),
            lambda data: data["cases"]["save-stmt"]["diagnostic"].update(line=25),
            lambda data: data["cases"]["save-stmt"]["diagnostic"].update(file="other.f90"),
            lambda data: data["cases"]["save-stmt"]["diagnostic"].update(allow_nonfatal=[]),
        ]
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            for mutate in mutations:
                data = copy.deepcopy(self.sidecar)
                mutate(data)
                with self.assertRaises(SuiteError):
                    self.temporary_cases(directory, data)
            current = self.temporary_cases(directory, self.sidecar)
            self.assertEqual({case.review_key for case in current}, set(self.negative_case_ids()))

    def test_valid_review_key_can_be_stale_or_legitimately_current_without_affecting_generation(self):
        registry = Registry(ROOT)
        cases = runner.collect_cases(ROOT / "tests", registry)
        valid = next(case for case in cases if case.name == "C815_valid")
        fingerprint = valid.fingerprint(registry)
        reviews_before = copy.deepcopy(registry.reviews)
        files_before, pairs_before = generated.build_corpus()
        for saved, expected in (("0" * 64, "stale"), (fingerprint, "source-reviewed")):
            record = dict(state="source-reviewed", fingerprint=saved, sources=["C815"],
                          rationale="In-memory legitimate administrative-state regression; no repository adjudication written.")
            registry._review_record("C815_valid", record)
            registry.reviews["C815_valid"] = record
            review = registry.review("C815_valid", fingerprint, ["C815_valid"])
            self.assertEqual(review.state, expected)
            self.assertEqual(valid.review_key, "C815_valid")
            self.assertEqual(generated.build_corpus(), (files_before, pairs_before))
            self.assertEqual(registry.reviews.get("C815_invalid"), reviews_before.get("C815_invalid"))
        self.assertEqual(Registry(ROOT).reviews, reviews_before)

    def test_real_parsed_source_states_draft_reviewed_stale_preserve_neutral_generation(self):
        registry = Registry(ROOT)
        templates = {section: (ROOT / path).read_text() for section, path in (
            ("8.5.1", generated.VIEW), ("8.5.2", generated.ACCESS_VIEW))}
        originals = {section: copy.deepcopy(registry.catalogues[section]) for section in templates}
        for section, original in originals.items():
            original_render = generated.render_view(templates[section], original, self.pairs if section == "8.5.1" else None)
            for state in ("draft", "reviewed", "stale"):
                candidate = copy.deepcopy(original)
                candidate["review_state"] = "draft" if state == "draft" else "reviewed"
                candidate["review_rationale"] = "In-memory source-administration regression, not an approval."
                registry.catalogues[section] = candidate
                candidate["review_fingerprint"] = "0" * 64 if state == "stale" else registry.catalogue_fingerprint(section)
                self.assertEqual(registry.catalogue_review_state(section), state)
                if section == "8.5.1":
                    updated = generated.synced_catalogue(candidate)
                    self.assertEqual(updated, candidate)
                else:
                    updated = candidate
                self.assertEqual(generated.render_view(templates[section], updated, self.pairs if section == "8.5.1" else None),
                                 original_render)
            registry.catalogues[section] = original

    def test_exact_files_native_render_and_six_of_fiftyfive_facet_partition(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("c815_attribute_*/*") if path.is_file()}
        self.assertEqual(actual, {path for path in self.files if "/fixtures/" in str(path)})
        self.assertEqual(len(actual), 10)
        self.assertEqual(len(self.files), 12)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        first, second = self.registry.catalogues["8.5.1"], self.registry.catalogues["8.5.2"]
        self.assertEqual((len(first["requirements"]), len(second["requirements"])), (2, 5))
        self.assertEqual(sum(len(r["facets"]) for c in (first, second) for r in c["requirements"]), 55)
        self.assertEqual(sum(len(r["pending"]) for c in (first, second) for r in c["requirements"]), 49)
        for catalogue in (first, second):
            for requirement in catalogue["requirements"]:
                selected = set(generated.FACETS) if requirement["id"] == "C815" else set()
                self.assertEqual(set(requirement["pending"]), set(requirement["facets"]) - selected)
        self.assertEqual(generated.synced_catalogue(first), first)
        self.assertEqual(generated.render_view((ROOT / generated.VIEW).read_text(), first, self.pairs), (ROOT / generated.VIEW).read_text())
        self.assertEqual(generated.render_view((ROOT / generated.ACCESS_VIEW).read_text(), second), (ROOT / generated.ACCESS_VIEW).read_text())
        native = Registry(ROOT)
        native.catalogues = {section: native.catalogues[section] for section in ("8.5.1", "8.5.2")}
        native.render()


if __name__ == "__main__":
    unittest.main()
