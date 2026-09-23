"""Exact legacy inputs, one-attribute repairs, per-case contracts and conservative causality."""
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
import run_tests as runner
from suite_data import Registry, SuiteError, case_review_bindings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_c801_declaration_fixtures as generated

FACETS = {
    "access-spec": "duplicate-public", "allocatable": "duplicate-allocatable",
    "dimension": "duplicate-dimension", "intent": "duplicate-intent-in", "parameter": "duplicate-parameter",
}
ATTRIBUTES = {"access-spec": "public", "allocatable": "allocatable", "dimension": "dimension(3)",
              "intent": "intent(in)", "parameter": "parameter"}
MARKERS = {"access-spec": 23, "allocatable": 5, "dimension": 10, "intent": 15, "parameter": 19}
REPAIRED_STATEMENTS = {
    "access-spec": "    integer, public :: m = 1   ! {error C801 access-spec}",
    "allocatable": "    real, allocatable :: b(:)   ! {error C801 allocatable}",
    "dimension": "    integer, dimension(3) :: a   ! {error C801 dimension}",
    "intent": "    integer, intent(in) :: x   ! {error C801 intent}",
    "parameter": "    integer, parameter :: n = 1   ! {error C801 parameter}",
}
GNU_CAUSES = {
    "access-spec": "Duplicate PUBLIC attribute at (1)",
    "allocatable": "Duplicate ALLOCATABLE attribute at (1)",
    "dimension": "Duplicate DIMENSION attribute at (1)",
    "intent": "Duplicate INTENT (IN) attribute at (1)",
    "parameter": "Duplicate PARAMETER attribute at (1)",
}
FLANG_CAUSES = {
    "access-spec": "Attribute 'PUBLIC' cannot be used more than once [-Wredundant-attribute]",
    "allocatable": "Attribute 'ALLOCATABLE' cannot be used more than once [-Wredundant-attribute]",
    "dimension": "Attribute 'DIMENSION' cannot be used more than once",
    "intent": "Attribute 'INTENT(IN)' cannot be used more than once [-Wredundant-attribute]",
    "parameter": "Attribute 'PARAMETER' cannot be used more than once [-Wredundant-attribute]",
}


def output(family, line, message, severity="error", filename="C801_invalid.f90"):
    if family == "lfortran":
        return f"{filename}:{line}-{line}:5-40: semantic {severity}: {message}\n"
    return f"{filename}:{line}:5:\n{severity}: {message}\n"


class C801DeclarationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.pairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.by_name = {case.name: case for case in cls.all_cases}
        cls.sidecar = json.loads((ROOT / generated.SIDECAR).read_text())
        cls.catalogue = cls.registry.catalogues["8.2"]
        cls.negative = {label: cls.by_name["C801_invalid:" + label] for label in FACETS}
        cls.controls = {label: cls.by_name[generated.control_id(label)] for label in FACETS}

    def test_exact_eleven_case_partition_and_five_new_compile_controls(self):
        expected = {"C801_invalid:" + label for label in FACETS} | {
            generated.control_id(label) for label in FACETS} | {"C801_valid"}
        selected = runner.select_cases(self.all_cases, sorted(expected))
        self.assertEqual({case.name for case in selected}, expected)
        self.assertEqual({case.name for case in runner.select_cases(self.all_cases, ["C801"])}, expected)
        self.assertEqual(len(selected), 11)
        for label, case in self.controls.items():
            self.assertEqual(case.rule, "C801")
            self.assertEqual(case.meta.facets, [FACETS[label]])
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, "positive-control")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.step, "source")
            self.assertIsNone(case.fixture.link)
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)

    def test_retained_container_and_valid_body_are_byte_pinned(self):
        invalid = (ROOT / generated.INVALID).read_bytes()
        self.assertEqual(hashlib.sha256(invalid).hexdigest(),
                         "d603976ab70bebc2cda0f9557d2f9531fb0c9119af5106293093afd563639136")
        self.assertEqual(runner.metadata(str(ROOT / generated.INVALID), "C801").facets, [])
        valid = (ROOT / generated.VALID).read_bytes()
        self.assertTrue(valid.startswith(b"! covers: distinct-attributes-admission\n"))
        body = valid[len(b"! covers: distinct-attributes-admission\n"):]
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "eb5a32b631c396b98a5463bb0ca6709d252837c2cee886a374c501b913fd897e")
        self.assertIn(b"integer, dimension(3), parameter :: a = [1, 2, 3]", body)
        self.assertIn(b"real, allocatable, dimension(:) :: b\n", body)
        self.assertIn(b"allocate(b(2))\n    b = 1.0\n", body)
        self.assertIn(b"if (size(a) /= 3) error stop\n", body)
        self.assertIn(b"if (size(b) /= 2) error stop\n", body)
        case = self.by_name["C801_valid"]
        self.assertEqual(case.review_key, "C801_valid")
        self.assertEqual(case.meta.facets, ["distinct-attributes-admission"])
        self.assertEqual(case.meta.evidence, "effect")
        self.assertEqual(case.meta.standard, "")
        self.assertEqual(case_plan(case)["expectation"], {"phase": "run", "step": "run", "outcome": "success"})
        self.assertFalse(case.fixture)

    def test_repairs_delete_exactly_one_repeated_attribute_and_comma(self):
        original = {item[2]: item for item in runner.isolated_cases(str(ROOT / generated.INVALID), "C801")}
        self.assertEqual(set(original), set(FACETS))
        for label, case in self.controls.items():
            raw = original[label][-1].encode()
            repaired = (case.fixture.root / "source.f90").read_bytes()
            pair = self.pairs[label]
            start, end = pair["repair"]["byte_span_zero_based_half_open"]
            self.assertEqual(raw[start:end], (", " + ATTRIBUTES[label]).encode())
            self.assertEqual(repaired, raw[:start] + raw[end:])
            self.assertEqual(len(raw) - len(repaired), len(", " + ATTRIBUTES[label]))
            before, after = raw.splitlines(keepends=True), repaired.splitlines(keepends=True)
            self.assertEqual(len(before), 24)
            self.assertEqual(len(after), 24)
            self.assertEqual([n + 1 for n, (a, b) in enumerate(zip(before, after)) if a != b], [MARKERS[label]])
            self.assertEqual(after[MARKERS[label] - 1].decode().rstrip("\n"), REPAIRED_STATEMENTS[label])
            self.assertEqual(pair["negative_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(pair["repair_sha256"], hashlib.sha256(repaired).hexdigest())
            self.assertIn(("{error C801 " + label + "}").encode(), repaired)
            self.assertEqual(pair["isolated_bounds"], list(original[label][3]))

    def test_complete_eligibility_and_body_statements_survive_every_repair(self):
        required = {
            "access-spec": ("module c801_public\n", "integer, public :: m = 1", "end module\n"),
            "allocatable": ("subroutine c801_allocatable()\n", "real, allocatable :: b(:)", "allocate(b(2))", "end subroutine\n"),
            "dimension": ("subroutine c801_dimension()\n", "integer, dimension(3) :: a", "    a = 1\n", "end subroutine\n"),
            "intent": ("subroutine c801_intent(x)\n", "integer, intent(in) :: x", "end subroutine\n"),
            "parameter": ("subroutine c801_parameter()\n", "integer, parameter :: n = 1", "end subroutine\n"),
        }
        for label, fragments in required.items():
            source = self.pairs[label]["repair_source"]
            for fragment in fragments:
                self.assertIn(fragment, source)
            self.assertIn("    implicit none\n", source)
            self.assertNotIn("intent(out)", source)
            self.assertNotIn("intent(inout)", source)
            self.assertNotIn("rank(", source)
            self.assertNotIn("bind(c", source)
            self.assertNotIn("private", source)
        self.assertNotIn("x =", self.pairs["intent"]["repair_source"])
        self.assertNotIn("integer, allocatable", self.pairs["allocatable"]["repair_source"])

    def test_each_negative_has_only_its_own_facet_and_marker_contract(self):
        self.assertEqual(set(self.sidecar), {"schema_version", "cases"})
        self.assertEqual(self.sidecar["schema_version"], 1)
        self.assertEqual(set(self.sidecar["cases"]), set(FACETS))
        for label, case in self.negative.items():
            contract = self.sidecar["cases"][label]
            self.assertEqual(set(contract), {"facets", "outcome", "diagnostic"})
            self.assertEqual(contract["facets"], [FACETS[label]])
            self.assertEqual(case.meta.facets, [FACETS[label]])
            self.assertEqual(contract["outcome"], "diagnose")
            self.assertEqual(case.review_key, case.name)
            self.assertEqual(case.contract["outcome"], "diagnose")
            self.assertEqual(case.contract["diagnostic"]["file"], "C801_invalid.f90")
            self.assertEqual(case.contract["diagnostic"]["line"], MARKERS[label])
            self.assertEqual(case.contract["diagnostic"]["end_line"], MARKERS[label])
            self.assertEqual(case.isolated[0], MARKERS[label])
            self.assertEqual(case.isolated[-1], self.pairs[label]["negative_source"])
            self.assertEqual(case_plan(case)["expectation"], {"phase": "compile", "step": "source", "outcome": "diagnose"})
            self.assertEqual({k: v for k, v in asdict(case.meta).items() if k != "facets"}, {
                "evidence": "effect", "coarray": False, "profiles": [], "images": 1, "standard": "",
                "reference_warnings": [], "oracle_basis": "standard", "oracle_profile": ""})

    def test_invalid_group_is_retired_and_valid_key_supports_explicit_renewal(self):
        groups, fingerprints = case_review_bindings(self.all_cases, self.registry)
        self.assertNotIn("C801_invalid", groups)
        self.assertIn("C801_invalid", self.registry.reviews)
        self.assertIn("C801_valid", self.registry.reviews)
        self.assertEqual(self.registry.reviews["C801_invalid"]["fingerprint"],
                         "580531ed9f0c853d63de08a23bde539cfdc33e3086ee8affc1cd367fc4b7a8bf")
        self.assertEqual(len({case.fingerprint(self.registry) for case in self.negative.values()}), 5)
        for case in self.negative.values():
            self.assertEqual(set(groups[case.name]), {case.name})
            self.assertNotEqual(fingerprints[case.name], self.registry.reviews["C801_invalid"]["fingerprint"])
        valid = self.by_name["C801_valid"]
        old_valid_fingerprint = "14079b901ad0ee3a3ea93cf6c4e8ca99593a74e85672405d413a44acd9799796"
        current_fingerprint = valid.fingerprint(self.registry)
        self.assertNotEqual(current_fingerprint, old_valid_fingerprint)
        self.assertEqual(groups["C801_valid"], ["C801_valid"])
        original = copy.deepcopy(self.registry.reviews["C801_valid"])
        try:
            for fingerprint, expected_state in ((old_valid_fingerprint, "stale"),
                                                (current_fingerprint, "source-reviewed")):
                record = dict(state="source-reviewed", rationale="Synthetic in-memory valid-key transition.",
                              sources=["C801"], fingerprint=fingerprint)
                self.registry._review_record("C801_valid", record)
                self.registry.reviews["C801_valid"] = record
                review = self.registry.review("C801_valid", current_fingerprint, groups["C801_valid"])
                self.assertEqual(review.state, expected_state)
        finally:
            self.registry.reviews["C801_valid"] = original

    def test_valid_key_renewal_does_not_break_retired_group_history_checks(self):
        original = copy.deepcopy(self.registry.reviews["C801_valid"])
        valid = self.by_name["C801_valid"]
        try:
            self.registry.reviews["C801_valid"] = dict(
                state="source-reviewed", rationale="Synthetic in-memory current valid-case review.",
                sources=["C801"], fingerprint=valid.fingerprint(self.registry))
            self.test_invalid_group_is_retired_and_valid_key_supports_explicit_renewal()
        finally:
            self.registry.reviews["C801_valid"] = original

    def test_source_view_and_requirement_text_do_not_freeze_adjudication_state(self):
        text = (ROOT / generated.VIEW).read_text()
        for state in ("draft", "reviewed", "stale"):
            with self.subTest(state=state):
                catalogue = generated.synced_catalogue(copy.deepcopy(self.catalogue))
                catalogue["review_state"] = "draft" if state == "draft" else "reviewed"
                catalogue["review_rationale"] = "Synthetic in-memory source state, not an approval."
                registry = Registry(ROOT)
                registry.catalogues["8.2"] = catalogue
                catalogue["review_fingerprint"] = (
                    "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.2"))
                self.assertEqual(registry.catalogue_review_state("8.2"), state)
                rendered = generated.render_view(text, catalogue, self.pairs)
                self.assertNotIn("**DRAFT, UNAPPROVED C801 INTEGRATION.**", rendered)
                self.assertNotIn("The new source records remain draft", rendered)
                self.assertNotIn("Six facets are represented without approval", rendered)
                self.assertIn("C801_valid", rendered)
                self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
                self.assertEqual(generated.render_view(rendered, catalogue, self.pairs), rendered)

    def judge(self, label, family, text, returncode=1, timed_out=False):
        compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023" if family == "gfortran" else "f2018")
        return runner.judge_diagnostic(
            runner.ProcessResult(returncode, text, timed_out), compiler, "C801",
            self.negative[label].contract["diagnostic"])

    def test_actual_specific_error_causes_allow_zero_or_ordinary_nonzero_status_without_codes(self):
        for label, message in GNU_CAUSES.items():
            for status in (0, 1, 2):
                check = self.judge(label, "gfortran", output("gfortran", MARKERS[label], message), status)
                self.assertEqual(check.outcome, "pass")
                self.assertEqual(check.note, "diagnoses without rejection" if status == 0 else "rejects")
        for family, message in (
            ("lfortran", "Dimensions specified twice"),
            ("flang", "Attribute 'DIMENSION' cannot be used more than once"),
        ):
            for status in (0, 1):
                self.assertEqual(self.judge("dimension", family, output(family, 10, message), status).outcome, "pass")

    def test_observed_warnings_remain_explicit_noncredit_in_the_existing_sidecar_schema(self):
        for label, message in FLANG_CAUSES.items():
            if label == "dimension":
                continue
            for status in (0, 1):
                text = output("flang", MARKERS[label], message, "warning")
                parsed = list(runner.reference_messages(text, "C801_invalid.f90"))
                self.assertEqual(parsed, [(MARKERS[label], "warning", message)])
                self.assertEqual(self.judge(label, "flang", text, status).outcome, "fail")
            self.assertNotIn("allow_nonfatal", self.sidecar["cases"][label]["diagnostic"])

    def test_wrong_attribute_payload_subject_recovery_and_bare_keywords_do_not_match(self):
        wrong = {
            "access-spec": ["Duplicate PRIVATE attribute", "PUBLIC", "Invalid PUBLIC specification"],
            "allocatable": ["Duplicate POINTER attribute", "ALLOCATABLE", "Allocate-object is neither a data pointer nor an allocatable variable"],
            "dimension": ["Duplicate PARAMETER attribute", "DIMENSION", "Invalid array specification", "Symbol 'a' has no IMPLICIT type"],
            "intent": ["Duplicate INTENT (OUT) attribute", "Duplicate INTENT (INOUT) attribute", "INTENT(IN)", "Dummy argument is not definable"],
            "parameter": ["Duplicate TARGET attribute", "PARAMETER", "Missing initializer for parameter n"],
        }
        for label, messages in wrong.items():
            for family in ("lfortran", "gfortran", "flang"):
                for message in messages + ["syntax error", "expected declaration", "unexpected END", "symbol already declared"]:
                    self.assertEqual(self.judge(label, family, output(family, MARKERS[label], message)).outcome, "fail")

    def test_exact_original_location_and_real_diagnostic_not_echo_are_required(self):
        for label, message in GNU_CAUSES.items():
            line = MARKERS[label]
            for wrong_line in (1, line - 1, line + 1, 24):
                self.assertEqual(self.judge(label, "gfortran", output("gfortran", wrong_line, message)).outcome, "fail")
            self.assertEqual(self.judge(label, "gfortran", output("gfortran", line, message, filename="wrong.f90")).outcome, "fail")
            echo = f"C801_invalid.f90:{line}:5:\n {line} | ! {message}\n      | 1\nError: syntax error\n"
            self.assertEqual(self.judge(label, "gfortran", echo).outcome, "fail")
            self.assertEqual(self.judge(label, "lfortran", f"! {message}\n").outcome, "fail")
        allocation_recovery = output("gfortran", 6, "Allocate-object at (1) is neither a data pointer nor an allocatable variable")
        self.assertEqual(self.judge("allocatable", "gfortran", allocation_recovery).outcome, "fail")
        genuine = output("gfortran", 5, GNU_CAUSES["allocatable"]) + allocation_recovery
        self.assertEqual(self.judge("allocatable", "gfortran", genuine).outcome, "pass")

    def test_unsupported_internal_verifier_resource_timeout_and_signal_are_not_corroboration(self):
        for label, message in GNU_CAUSES.items():
            for family in ("lfortran", "gfortran", "flang"):
                good = output(family, MARKERS[label], message)
                for prefix in ("Not implemented: ", "Unsupported facility: ", "Recovery: "):
                    self.assertEqual(self.judge(label, family, output(family, MARKERS[label], prefix + message)).outcome, "fail")
                for tail in ("internal compiler error: failure\n", "error: Internal: verifier failed\n",
                             "ASR verify pass error\n", "out of memory\n"):
                    self.assertEqual(self.judge(label, family, good + tail).outcome, "fail")
                self.assertEqual(self.judge(label, family, good, 0, True).outcome, "fail")
                self.assertEqual(self.judge(label, family, good, -11).outcome, "fail")
                self.assertEqual(self.judge(label, family, good, 139).outcome, "fail")

    def test_unsupported_and_internal_wrappers_fail_through_real_input_staging(self):
        prefixes = ("", "Not implemented: ", "Unsupported facility: ",
                    "Not yet implemented: ", "Unimplemented: ", "Internal: ")
        checks = 0
        for label, case in self.negative.items():
            for family in ("lfortran", "gfortran", "flang"):
                compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else
                                           "f2018" if family == "flang" else "f2023")
                for status in (0, 1, 2):
                    for prefix in prefixes:
                        checks += 1
                        with self.subTest(label=label, family=family, status=status, prefix=prefix):
                            text = output(family, MARKERS[label], prefix + GNU_CAUSES[label])
                            with patch.object(runner, "run", return_value=runner.ProcessResult(status, text)):
                                check = runner.check_invalid(
                                    case.path, case.isolated[-1], case.isolated[0], case.rule,
                                    case.isolated[3], compiler, case.meta, contract=case.contract)
                            self.assertEqual(check.outcome, "fail" if prefix else "pass")
                            self.assertEqual(check.phase, "compile")
                            self.assertEqual(check.input_hashes, {
                                "C801_invalid.f90": hashlib.sha256(case.isolated[-1].encode()).hexdigest()})
                            self.assertEqual(len(check.trace), 1)
        self.assertEqual(checks, 270)

    def temporary_contract_cases(self, root, data):
        path = root / "C801_invalid.f90"
        path.write_bytes((ROOT / generated.INVALID).read_bytes())
        path.with_suffix(".cases.json").write_text(json.dumps(data))
        cases = [runner.SuiteCase(
            "C801_invalid:" + item[2], "C801", "invalid", str(path),
            runner.metadata(str(path), "C801"), "C801_invalid", isolated=item)
            for item in runner.isolated_cases(str(path), "C801")]
        apply_case_contracts(cases, runner.PROFILES, root)
        return cases

    def test_existing_sidecar_schema_enforces_exact_ids_and_blocks_unapproved_extensions(self):
        mutations = [
            lambda data: data["cases"].pop("parameter"),
            lambda data: data["cases"].update(extra=data["cases"]["parameter"]),
            lambda data: data["cases"]["intent"].update(outcome="reject"),
            lambda data: data["cases"]["intent"].update(standard="f2023"),
            lambda data: data["cases"]["intent"].update(profiles=["no-such-profile"]),
            lambda data: data["cases"]["intent"]["diagnostic"].update(line=16),
            lambda data: data["cases"]["intent"]["diagnostic"].update(file="different.f90"),
            lambda data: data["cases"]["intent"]["diagnostic"].update(allow_nonfatal=[]),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for mutate in mutations:
                data = copy.deepcopy(self.sidecar)
                mutate(data)
                with self.assertRaises(SuiteError):
                    self.temporary_contract_cases(root, data)
            cases = self.temporary_contract_cases(root, self.sidecar)
            self.assertEqual({case.review_key for case in cases}, {"C801_invalid:" + label for label in FACETS})
            self.assertTrue(all(case.meta.standard == "" and case.meta.profiles == [] for case in cases))

    def test_exact_generated_files_and_idempotent_source_view_preserve_all_other_plans(self):
        controls = {path for path in (ROOT / "tests/fixtures").glob("c801_declaration_*/*") if path.is_file()}
        self.assertEqual(len(controls), 10)
        self.assertEqual(controls, {path for path in self.files if "/fixtures/" in str(path)})
        self.assertEqual(len(self.files), 12)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        self.assertEqual(generated.synced_catalogue(self.catalogue), self.catalogue)
        changed = generated.synced_catalogue(self.catalogue)
        self.assertEqual({k: v for k, v in changed.items() if k != "requirements"},
                         {k: v for k, v in self.catalogue.items() if k != "requirements"})
        for old, new in zip(self.catalogue["requirements"], changed["requirements"]):
            if old["id"] != "C801":
                self.assertEqual(new, old)
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(generated.render_view(view, changed, self.pairs), view)
        self.assertEqual(view.count(generated.INTEGRATION), 1)
        native = Registry(ROOT)
        native.catalogues = {section: native.catalogues[section] for section in ("8.1", "8.2")}
        native.render()

    def test_definition_only_8_1_and_exact_six_facet_118_pending_limit(self):
        definitions = self.registry.catalogues["8.1"]
        self.assertEqual(definitions["requirements"], [])
        self.assertEqual(sum(map(len, definitions["subunits"].values())), 14)
        self.assertEqual(len(definitions["accounting"]), 17)
        self.assertEqual(len(self.catalogue["requirements"]), 23)
        self.assertEqual(sum(map(len, self.catalogue["subunits"].values())), 102)
        self.assertEqual(len(self.catalogue["accounting"]), 127)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 124)
        # Facets discharged by later packets that share this catalogue (e.g. batch156's
        # type_declaration_ fixtures) are excluded, so this legacy invariant only covers C801's own work.
        external = set()
        for manifest in (ROOT / "tests" / "fixtures").glob("type_declaration_*/fixture.json"):
            data = json.loads(manifest.read_text())
            external |= {(data["rule"], facet) for facet in data["facets"]}
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]) + len(external), 118)
        selected = set(FACETS.values()) | {"distinct-attributes-admission"}
        for requirement in self.catalogue["requirements"]:
            bound_elsewhere = {facet for rule, facet in external if rule == requirement["id"]}
            self.assertEqual(set(requirement["pending"]),
                             set(requirement["facets"]) - (selected if requirement["id"] == "C801" else set())
                             - bound_elsewhere)
        c801 = next(r for r in self.catalogue["requirements"] if r["id"] == "C801")
        self.assertEqual(len(c801["pending"]), 17)
        self.assertIn("duplicate-private", c801["pending"])
        self.assertIn("duplicate-intent-out", c801["pending"])
        self.assertIn("duplicate-rank", c801["pending"])


if __name__ == "__main__":
    unittest.main()
