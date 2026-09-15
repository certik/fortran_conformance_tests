import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from execution_commands import case_plan
from suite_data import Registry


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import generate_numeric_literal_fixtures as generator


COMPLEX_TERMINAL_CASES = [
    ("R718", "missing_comma", "expected ','"),
    ("R718", "third_part", "expected ')'"),
    ("R719", "constant_expression_part", "expected ','"),
    ("R720", "constant_expression_part", "expected ')'"),
    ("R719", "signed_name_part", "expected '.'"),
    ("R720", "signed_name_part", "expected '.'"),
]

# Observed Flang f2018 stderr, with temporary filenames normalized.
FLANG_LITERAL_REPORTS = {
    ("R718", "missing_comma"): """error: Could not parse source.f90
source.f90:5:20: error: expected ','
      data z /(0.0d0 0.0d0)/
                     ^
source.f90:5:13: in the context: COMPLEX literal constant
      data z /(0.0d0 0.0d0)/
              ^
source.f90:5:5: in the context: DATA statement
      data z /(0.0d0 0.0d0)/
      ^
""",
    ("R718", "third_part"): """error: Could not parse source.f90
source.f90:5:25: error: expected ')'
      data z /(0.0d0,0.0d0,0.0d0)/
                          ^
source.f90:5:13: in the context: COMPLEX literal constant
      data z /(0.0d0,0.0d0,0.0d0)/
              ^
source.f90:5:5: in the context: DATA statement
      data z /(0.0d0,0.0d0,0.0d0)/
      ^
""",
    ("R719", "constant_expression_part"): """error: Could not parse source.f90
source.f90:7:19: error: expected ','
      data z /(0.0d0+0.0d0, 0.0d0)/
                    ^
source.f90:7:13: in the context: COMPLEX literal constant
      data z /(0.0d0+0.0d0, 0.0d0)/
              ^
source.f90:7:5: in the context: DATA statement
      data z /(0.0d0+0.0d0, 0.0d0)/
      ^
""",
    ("R720", "constant_expression_part"): """error: Could not parse source.f90
source.f90:7:26: error: expected ')'
      data z /(0.0d0, 0.0d0+0.0d0)/
                           ^
source.f90:7:13: in the context: COMPLEX literal constant
      data z /(0.0d0, 0.0d0+0.0d0)/
              ^
source.f90:7:5: in the context: DATA statement
      data z /(0.0d0, 0.0d0+0.0d0)/
      ^
""",
    ("R719", "signed_name_part"): """error: Could not parse source.f90
source.f90:7:15: error: expected '.'
      data z /(-r, 0.0d0)/
                ^
source.f90:7:15: in the context: REAL literal constant
      data z /(-r, 0.0d0)/
                ^
source.f90:7:13: in the context: COMPLEX literal constant
      data z /(-r, 0.0d0)/
              ^
""",
    ("R720", "signed_name_part"): """error: Could not parse source.f90
source.f90:7:22: error: expected '.'
      data z /(0.0d0, -r)/
                       ^
source.f90:7:22: in the context: REAL literal constant
      data z /(0.0d0, -r)/
                       ^
source.f90:7:13: in the context: COMPLEX literal constant
      data z /(0.0d0, -r)/
              ^
""",
}

TARGET_TOKEN_REPORTS = {
    ("R718", "missing_comma"): "source.f90:5-5:20-24: syntax error: "
    "Token '0.0d0' (of type 'real') is unexpected here\n",
    ("R718", "third_part"): "source.f90:5-5:25-25: syntax error: Token ',' is unexpected here\n",
    ("R719", "constant_expression_part"): "source.f90:7-7:19-19: syntax error: "
    "Token '+' is unexpected here\n",
    ("R720", "constant_expression_part"): "source.f90:7-7:26-26: syntax error: "
    "Token '+' is unexpected here\n",
}


class NumericLiteralFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = generator.build()
        cls.registry = Registry(ROOT)
        cls.cases = {case.name: case for case in runner.collect_cases(ROOT / "tests", cls.registry)
                     if case.name in cls.bundle.cases}

    def manifest(self, path):
        return json.loads(self.bundle.files[path])

    def source(self, manifest_path):
        return self.bundle.files[str(Path(manifest_path).with_name("source.f90"))].decode()

    def diagnostic(self, pair):
        return self.manifest(pair["invalid"])["expect"]["diagnostic"]

    def pair(self, rule, name):
        return next(pair for pair in self.bundle.pairs
                    if pair["rule"] == rule and pair["name"] == name)

    def judge(self, rule, diagnostic, message, family="lfortran", severity="error",
              line=None, filename=None, returncode=1, timed_out=False):
        line = diagnostic["line"] if line is None else line
        filename = diagnostic["file"] if filename is None else filename
        if family == "lfortran":
            output = f"{filename}:{line}-{line}:1-8: semantic {severity}: {message}\n"
        elif family == "gfortran":
            output = f"{filename}:{line}:1:\n{severity.capitalize()}: {message}\n"
        else:
            output = f"{filename}:{line}:1: {severity}: {message}\n"
        compiler = runner.Compiler("/synthetic/" + family, family,
                                   "f23" if family == "lfortran" else "f2023")
        result = runner.ProcessResult(returncode, output, timed_out=timed_out)
        return runner.judge_diagnostic(result, compiler, rule, diagnostic).outcome

    def test_generated_files_have_exact_deterministic_bytes(self):
        self.assertEqual(self.bundle.files, generator.build().files)
        for path, data in self.bundle.files.items():
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), data)
                self.assertTrue(data.endswith(b"\n"))
                data.decode("ascii")
                if path.endswith(".f90"):
                    self.assertLessEqual(max(map(len, data.splitlines())), 132)

    def test_only_declared_scopes_and_unique_execution_ids_are_generated(self):
        self.assertEqual(set(self.cases), set(self.bundle.cases))
        numbered = {"R713", "R714", "R715", "R716", "R717", "R718", "R719", "R720",
                    "C721", "C722", "C723", "R725", "C733"}
        prefixes = ("S7.4.3.2-", "S7.4.3.3-", "S7.4.5-")
        for identifier, expected in self.bundle.cases.items():
            case = self.cases[identifier]
            self.assertTrue(case.rule in numbered or case.rule.startswith(prefixes))
            self.assertEqual(case.rule, expected["rule"])
            self.assertEqual(set(case.meta.facets), set(expected["facets"]))
            self.assertEqual(case.meta.profiles, expected["profiles"])
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case_plan(case)["expectation"]["phase"], expected["phase"])
        for rule in ["R704", "R706", "C717"]:
            self.assertEqual(self.registry.requirement_sections[rule], "7.4.1")
        for rule in ["R709", "R710", "R711", "R712"]:
            self.assertEqual(self.registry.requirement_sections[rule], "7.4.3.1")
        self.assertNotIn("R606", self.bundle.coverage())
        self.assertNotIn("R710", self.bundle.coverage())

    def test_pending_is_exactly_the_unimplemented_scoped_facets(self):
        coverage = self.bundle.coverage()
        for section in ["7.4.3.2", "7.4.3.3", "7.4.5"]:
            for requirement in self.registry.catalogues[section]["requirements"]:
                self.assertEqual(set(requirement["pending"]),
                                 set(requirement["facets"]) - coverage.get(requirement["id"], set()))
        for rule, facet in [
            ("R717", "canonical-sign-control-link"),
            ("R719", "variable-not-named-constant"),
            ("R720", "variable-not-named-constant"),
            ("C722", "supported-digit"),
            ("C722", "absent-zero-alternative"),
            ("S7.4.3.2-003", "sign-distinguishing-profile"),
            ("S7.4.3.2-003", "remaining-intrinsic-use-matrix"),
            ("S7.4.5-004", "named-true"),
            ("S7.4.5-004", "named-false"),
        ]:
            self.assertIn(facet, self.registry.requirements[rule]["pending"])
        for rule in ["S7.4.3.2-007", "S7.4.3.2-008", "S7.4.3.3-001"]:
            self.assertNotIn(rule, coverage)

    def test_runtime_effects_and_mandatory_checks_are_not_profiled_admission_tests(self):
        effects = [case for case in self.cases.values() if case.rule.startswith("S")]
        self.assertEqual(len(effects), 38)
        for case in effects:
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual(case.meta.profiles, [])
            self.assertEqual(case_plan(case)["expectation"]["phase"], "run")
        self.assertEqual(case_plan(self.cases["C722_valid"])["expectation"]["phase"], "run")
        for rule in ["S7.4.3.2-004", "S7.4.3.2-005"]:
            for case in effects:
                if case.rule == rule:
                    self.assertNotIn("stop 77", Path(case.path).read_text().lower())
        thresholds = "\n".join(Path(case.path).read_text() for case in effects
                               if case.rule == "S7.4.3.2-005")
        self.assertIn("precision(0.0d0) < 10", thresholds)
        self.assertIn("range(0.0d0) < 37", thresholds)

    def test_each_new_negative_has_one_minimal_source_repair_and_exact_point(self):
        self.assertEqual(len(self.bundle.pairs), 27)
        for pair in self.bundle.pairs:
            with self.subTest(rule=pair["rule"], name=pair["name"]):
                bad = self.source(pair["invalid"])
                good = self.source(pair["valid"])
                self.assertEqual(bad.count(pair["bad"]), 1)
                self.assertEqual(bad.replace(pair["bad"], pair["repair"], 1), good)
                self.assertEqual(sum(a != b for a, b in zip(bad.splitlines(), good.splitlines())), 1)
                invalid = self.manifest(pair["invalid"])
                valid = self.manifest(pair["valid"])
                self.assertEqual(invalid["expect"]["outcome"], "diagnose")
                self.assertEqual(valid["expect"]["outcome"], "success")
                self.assertEqual(valid["expect"]["phase"], "compile")
                self.assertEqual(valid["evidence"], "positive-control")
                point = invalid["expect"]["diagnostic"]
                self.assertEqual(point["file"], "source.f90")
                self.assertEqual(point["line"], pair["line"])
                self.assertNotIn("end_line", point)
                self.assertIn("data ", bad.splitlines()[point["line"] - 1].lower())

    def test_legacy_bodies_and_all_six_execution_ids_are_preserved(self):
        positive = generator.legacy_positive_body()
        negative = generator.legacy_negative_body()
        self.assertEqual(hashlib.sha256(positive.encode()).hexdigest(), generator.LEGACY_POSITIVE_SHA256)
        self.assertEqual(hashlib.sha256(negative.encode()).hexdigest(), generator.LEGACY_NEGATIVE_SHA256)
        ids = {"C722_valid"} | {"C722_invalid:" + name for name in generator.LEGACY_FACETS}
        self.assertTrue(ids <= self.cases.keys())
        sidecar = self.manifest("tests/clause07/C722_invalid.cases.json")
        self.assertEqual(set(sidecar["cases"]), set(generator.LEGACY_FACETS))
        fingerprints = set()
        for name, facet in generator.LEGACY_FACETS.items():
            case = self.cases["C722_invalid:" + name]
            self.assertEqual(case.review_key, case.name)
            self.assertEqual(case.meta.facets, [facet])
            self.assertEqual(case.path, str(ROOT / "tests/clause07/C722_invalid.f90"))
            self.assertEqual(case.contract["diagnostic"]["line"], case.isolated[0])
            self.assertEqual(case.contract["diagnostic"]["file"], "C722_invalid.f90")
            self.assertEqual(case.meta.profiles, [generator.LEGACY_DEFAULT_PROFILE, "absent-real-kind-seven"])
            self.assertNotIn("file", sidecar["cases"][name]["diagnostic"])
            self.assertNotIn("line", sidecar["cases"][name]["diagnostic"])
            self.assertNotIn("allow_nonfatal", sidecar["cases"][name]["diagnostic"])
            fingerprints.add(case.fingerprint(self.registry))
        self.assertEqual(len(fingerprints), 5)

    def test_retained_controls_change_only_the_declared_kind_defect(self):
        for name, repair in self.bundle.legacy_repairs.items():
            with self.subTest(name=name):
                self.assertEqual(repair["invalid_source"].replace(
                    repair["bad"], repair["repair"], 1).rstrip("\n") + "\n",
                                 repair["control_source"])
                self.assertEqual(repair["control_source"], self.source(repair["path"]))
                self.assertEqual(self.manifest(repair["path"])["expect"]["phase"], "compile")
        array = self.bundle.legacy_repairs["array-constructor"]
        self.assertEqual(array["invalid_source"].count("_7"), 2)
        self.assertNotIn("_7", array["control_source"])
        named = self.bundle.legacy_repairs["named-constant"]
        self.assertIn("integer, parameter :: k = kind(0.0)", named["control_source"])

    def test_legacy_positive_is_narrow_and_real128_zero_is_not_claimed(self):
        case = self.cases["C722_valid"]
        self.assertEqual(case.meta.evidence, "positive-control")
        self.assertEqual(case.meta.oracle_basis, "processor-profile")
        self.assertEqual(case.meta.oracle_profile, generator.LEGACY_POSITIVE_PROFILE)
        self.assertEqual(case.meta.facets, ["supported-name", "legacy-supported-digit-codes"])
        profile = self.bundle.files["tests/profiles/numeric_literal_legacy_real_kinds.f90"].decode()
        self.assertIn("if (real32 /= 4 .or. real64 /= 8) stop 77", profile)
        self.assertIn("if (dk /= real64) stop 77", profile)
        self.assertIn("merge(real128, real64, real128 > 0)", profile)
        self.assertNotIn("real128 >= 0)", profile)
        self.assertIn("merge(real32, dk, real32 >= 0)", profile)
        self.assertIn("merge(real64, dk, real64 >= 0)", profile)
        for raw in [-2, -1, 0, 16]:
            selected = raw if raw > 0 else 8
            self.assertEqual(selected, 16 if raw == 16 else 8)
        self.assertNotIn("1.5", profile)
        self.assertNotIn("2.5", profile)

    def test_profiles_have_only_zero_real_inputs_and_no_physical_representation_oracle(self):
        for path, data in self.bundle.files.items():
            if path.startswith("tests/profiles/"):
                source = data.decode().lower()
                self.assertNotIn("ieee_", source)
                self.assertNotIn("transfer(", source)
                self.assertIn("error stop", source)
                self.assertIn("stop 77", source)
                self.assertIn("real_kinds", source)
                literals = re.findall(r"(?<![\w.])\d+\.\d+(?:[ed][+-]?\d+)?", source)
                self.assertTrue(all(float(literal.replace("d", "e")) == 0 for literal in literals))

    def test_unprofiled_source_does_not_guess_kind_codes_or_narrow_identifiers(self):
        for case in self.cases.values():
            if case.fixture:
                source = Path(case.fixture.root / "source.f90").read_text()
            else:
                source = Path(case.path).read_text()
            lower = source.lower()
            self.assertNotIn("transfer(", lower)
            self.assertNotIn("ieee_", lower)
            self.assertNotRegex(lower, r"\bint\(\s*(?:kr|kd|lk|first|second|selected_qp|real32|real64|real128)\b")
            if not case.meta.profiles:
                self.assertNotRegex(lower, r"\b\d+(?:\.\d*)?(?:[ed][+-]?\d+)?_[0-9]+\b")

    def test_complex_literal_alternatives_are_not_masked_by_named_part_support(self):
        for rule in ["R719", "R720"]:
            for variant, facet in [("integer_part_forms", "signed-integer-part"),
                                   ("real_part_forms", "signed-real-part"),
                                   ("part_alternatives", "named-part")]:
                case = self.cases[f"{rule}_valid__numeric_{variant}"]
                self.assertEqual(case.meta.facets, [facet])
            pair = self.pair(rule, "constant_expression_part")
            self.assertIn("0.0d0+0.0d0", pair["bad"])
            self.assertEqual(pair["repair"].count("0.0d0"), 2)
            self.assertEqual(self.manifest(pair["valid"])["facets"], ["signed-real-part"])
            self.assertNotIn("variable", " ".join(self.bundle.coverage()[rule]))

    def test_zero_relations_cover_all_spellings_without_ordering_complex_values(self):
        same_kind = [Path(case.path).read_text() for case in self.cases.values()
                     if case.name.endswith(("_numeric_default_zero_relations", "_numeric_double_zero_relations"))]
        self.assertEqual(len(same_kind), 2)
        for source in same_kind:
            for operator, expected in generator.RELATIONS:
                self.assertIn("p " + operator + " n", source)
                self.assertIn("n " + operator + " p", source)
        mixed = next(Path(case.path).read_text() for case in self.cases.values()
                     if case.name.endswith("_numeric_complex_real_zeros"))
        self.assertNotRegex(mixed, r"(?:<=|>=|\.lt\.|\.le\.|\.gt\.|\.ge\.)")
        for operator in [" == ", " /= ", " .eq. ", " .ne. "]:
            self.assertIn(operator, mixed)

    def test_all_contracts_reject_generic_and_wrong_cause_reports(self):
        wrong = [
            "Kind not supported", "Expected a constant expression",
            "Syntax error in DATA statement at (1)", "Syntax error in COMPLEX constant at (1)",
            "expected expression", "Expected PARAMETER symbol in complex constant at (1)",
            "Variable '0' not declared", "array constructor has the wrong number of elements",
            "Token 'bad' (of type 'identifier') is unexpected here",
        ]
        for pair in self.bundle.pairs:
            diagnostic = self.diagnostic(pair)
            for message in wrong:
                with self.subTest(pair=pair["name"], rule=pair["rule"], message=message):
                    self.assertEqual(self.judge(pair["rule"], diagnostic, message), "fail")
            self.assertNotIn("expected", diagnostic["contains_any"])
            self.assertNotIn("kind", diagnostic["contains_any"])
        for case in self.cases.values():
            if case.contract:
                for message in wrong + [
                    "Invalid logical kind 7", "Invalid real kind 0",
                    "Real number at (1) has a 'd' exponent and an explicit kind",
                ]:
                    self.assertEqual(self.judge(case.rule, case.contract["diagnostic"], message), "fail")

    def test_causal_messages_do_not_accept_wrong_files_locations_or_failures(self):
        for pair in self.bundle.pairs:
            diagnostic = self.diagnostic(pair)
            message = diagnostic["contains_any"][0]
            with self.subTest(rule=pair["rule"], name=pair["name"]):
                self.assertEqual(self.judge(pair["rule"], diagnostic, message), "pass")
                self.assertEqual(self.judge(pair["rule"], diagnostic, message,
                                            filename="other.f90"), "fail")
                self.assertEqual(self.judge(pair["rule"], diagnostic, message,
                                            line=diagnostic["line"] + 1), "fail")
                self.assertEqual(self.judge(pair["rule"], diagnostic, message,
                                            timed_out=True), "fail")
                self.assertEqual(self.judge(pair["rule"], diagnostic, message,
                                            returncode=-11), "fail")
                for prefix in ["not implemented: ", "internal compiler error: ",
                               "ASR verify pass error: ", "ASR verifier failure: ",
                               "out of memory: ", "resource exhausted: "]:
                    self.assertEqual(self.judge(pair["rule"], diagnostic, prefix + message), "fail")

    def test_kind_value_reports_remain_intended_while_constancy_is_excluded(self):
        for name in generator.LEGACY_FACETS:
            case = self.cases["C722_invalid:" + name]
            diagnostic = case.contract["diagnostic"]
            self.assertEqual(self.judge("C722", diagnostic, "Invalid real kind 7 at (1)",
                                       family="gfortran"), "pass")
            self.assertEqual(self.judge("C722", diagnostic, "Unsupported REAL(KIND=7)",
                                       family="flang"), "pass")
            self.assertEqual(self.judge("C722", diagnostic, "Kind not supported"), "fail")
            self.assertEqual(self.judge("C722", diagnostic,
                                       "kind 7 not supported for type real: must be a constant expression"), "fail")
            for prefix in ["ASR verify pass error: ", "out of memory: ", "not implemented: "]:
                self.assertEqual(self.judge("C722", diagnostic, prefix + "Unsupported REAL(KIND=7)",
                                           family="flang"), "fail")
        for pair in self.bundle.pairs:
            if pair["rule"] == "C733":
                diagnostic = self.diagnostic(pair)
                self.assertEqual(self.judge("C733", diagnostic, "Bad kind for logical constant at (1)",
                                           family="gfortran"), "pass")
                self.assertEqual(self.judge("C733", diagnostic, "unsupported LOGICAL(KIND=0)",
                                           family="flang"), "pass")
                self.assertEqual(self.judge("C733", diagnostic, "Variable '0' not declared"), "fail")

    def test_rank_type_and_constancy_causes_are_not_interchangeable(self):
        for position in ["real", "imaginary"]:
            rank = self.diagnostic(self.pair("C723", position + "_rank"))
            self.assertEqual(self.judge("C723", rank, "Scalar PARAMETER required in complex constant at (1)",
                                       family="gfortran"), "pass")
            self.assertEqual(self.judge("C723", rank, "Numeric PARAMETER required in complex constant at (1)"), "fail")
            for category in ["logical_type", "character_type"]:
                diagnostic = self.diagnostic(self.pair("C723", position + "_" + category))
                self.assertEqual(self.judge("C723", diagnostic, "Numeric PARAMETER required in complex constant at (1)",
                                           family="gfortran"), "pass")
                self.assertEqual(self.judge("C723", diagnostic, "Scalar PARAMETER required in complex constant at (1)"), "fail")
            complex_type = self.diagnostic(self.pair("C723", position + "_complex_type"))
            self.assertEqual(self.judge("C723", complex_type, "Numeric PARAMETER required in complex constant at (1)"), "fail")
            self.assertEqual(self.judge("C723", complex_type,
                                       "operands must be INTEGER, UNSIGNED, REAL, or BOZ",
                                       family="flang"), "pass")

    def test_nonfatal_reporting_is_exact_family_severity_and_cause_qualified(self):
        for pair in self.bundle.pairs:
            diagnostic = self.diagnostic(pair)
            for route in diagnostic.get("allow_nonfatal", []):
                self.assertEqual(route["compiler"], "flang")
                self.assertEqual(route["severity"], "portability")
                message = route["equals_any"][0]
                self.assertEqual(self.judge(pair["rule"], diagnostic, message,
                                           family="flang", severity="portability", returncode=0), "pass")
                self.assertEqual(self.judge(pair["rule"], diagnostic, message + " unrelated",
                                           family="flang", severity="portability", returncode=0), "fail")
                self.assertEqual(self.judge(pair["rule"], diagnostic, message,
                                           family="flang", severity="warning", returncode=0), "fail")

    def test_same_point_wrong_context_terminal_reports_fail_in_all_families_and_statuses(self):
        checked = 0
        for rule, name, terminal in COMPLEX_TERMINAL_CASES:
            pair = self.pair(rule, name)
            diagnostic = self.diagnostic(pair)
            self.assertNotIn(terminal, diagnostic["contains_any"])
            self.assertEqual(diagnostic["excludes_any"], generator.SYNTAX_EXCLUSIONS)
            self.assertFalse(any("procedure argument list" in text
                                 or "in the context" in text for text in diagnostic["excludes_any"]))
            for family in ["lfortran", "gfortran", "flang"]:
                compiler = runner.Compiler("/synthetic/" + family, family,
                                           "f23" if family == "lfortran" else "f2023")
                for status in [0, 1]:
                    line = diagnostic["line"]
                    message = terminal + " in a procedure argument list"
                    output = (f"source.f90:{line}-{line}:1-8: syntax error: {message}\n"
                              if family == "lfortran"
                              else f"source.f90:{line}:1: error: {message}\n")
                    with self.subTest(rule=rule, name=name, family=family, status=status):
                        result = runner.judge_diagnostic(
                            runner.ProcessResult(status, output), compiler, rule, diagnostic)
                        self.assertEqual(result.outcome, "fail")
                    checked += 1
        self.assertEqual(checked, 36)

    def test_actual_flang_context_mutations_cannot_restore_removed_terminal_routes(self):
        compiler = runner.Compiler("/observed/flang", "flang", "f2018")
        self.assertEqual(set(FLANG_LITERAL_REPORTS), {(rule, name) for rule, name, _ in COMPLEX_TERMINAL_CASES})
        for (rule, name), output in FLANG_LITERAL_REPORTS.items():
            diagnostic = self.diagnostic(self.pair(rule, name))
            self.assertEqual(output.count("in the context: COMPLEX literal constant"), 1)
            mutated = output.replace("in the context: COMPLEX literal constant",
                                     "in the context: procedure argument list")
            if name == "signed_name_part":
                self.assertEqual(output.count("in the context: REAL literal constant"), 1)
                mutated = mutated.replace("in the context: REAL literal constant",
                                          "in the context: LOGICAL literal constant")
            with self.subTest(rule=rule, name=name):
                self.assertNotEqual(mutated, output)
                for candidate in [output, mutated]:
                    result = runner.judge_diagnostic(
                        runner.ProcessResult(1, candidate), compiler, rule, diagnostic)
                    self.assertEqual(result.outcome, "fail")

    def test_retained_actual_token_specific_reports_still_pass(self):
        compiler = runner.Compiler("/observed/lfortran", "lfortran", "f23")
        self.assertEqual(len(TARGET_TOKEN_REPORTS), 4)
        for (rule, name), output in TARGET_TOKEN_REPORTS.items():
            diagnostic = self.diagnostic(self.pair(rule, name))
            for status in [0, 1]:
                with self.subTest(rule=rule, name=name, status=status):
                    result = runner.judge_diagnostic(
                        runner.ProcessResult(status, output), compiler, rule, diagnostic)
                    self.assertEqual(result.outcome, "pass")

    def test_signed_name_contracts_are_position_specific_and_prospective(self):
        for rule, position in [("R719", "real"), ("R720", "imaginary")]:
            diagnostic = self.diagnostic(self.pair(rule, "signed_name_part"))
            message = ("A sign before a named constant is not permitted in the "
                       + position + " part of a complex literal")
            self.assertEqual(diagnostic["contains_any"], [message])
            other_position = "imaginary" if position == "real" else "real"
            wrong = message.replace(position + " part", other_position + " part")
            for status in [0, 1]:
                # Contract probes only, not claimed compiler observations.
                self.assertEqual(self.judge(rule, diagnostic, message, returncode=status), "pass")
                self.assertEqual(self.judge(rule, diagnostic, wrong, returncode=status), "fail")
            self.assertEqual(self.judge(rule, diagnostic, "Token 'r' (of type 'identifier') is unexpected here"), "fail")
            self.assertEqual(self.judge(rule, diagnostic, "Token 'n' (of type 'identifier') is unexpected here"), "fail")


if __name__ == "__main__":
    unittest.main()
