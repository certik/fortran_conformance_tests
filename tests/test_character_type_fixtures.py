"""Exact-input and causal-oracle regressions for the bounded character corpus."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_character_type_fixtures as generated


RUN_VARIANTS = {
    "S7.4.4.1-001": "positions lengths",
    "S7.4.4.1-002": "default_method named_selection",
    "S7.4.4.1-003": "constructed",
    "R721": "len_kind_keywords positional positional_keyword kind_only kind_len_keywords",
    "R722": "parentheses star_forms comma selected_length_expression",
    "R723": "expression integer assumed_deferred",
    "C725": "parenthesized_suffix",
    "C731": "constant_lengths",
    "C732": "supported",
    "S7.4.4.2-001": "bare length_only",
    "S7.4.4.2-002": "repertoire",
    "S7.4.4.2-004": "selector entity component default_one",
    "S7.4.4.2-005": "constant runtime individual",
    "S7.4.4.2-006": ("dummy optional allocatable_dummy pointer_dummy allocate_assumed "
                     "allocate_assumed_pointers guard external access_routes"),
    "S7.4.4.3-001": "default named_prefix",
    "S7.4.4.3-002": "free_graphics fixed_graphics",
    "S7.4.4.3-003": "apostrophe quotation opposite_delimiters",
    "S7.4.4.3-004": "apostrophe quotation boundaries",
    "S7.4.4.3-005": "apostrophe quotation context",
    "S7.4.4.4-002": "uppercase digits lowercase blank_uppercase blank_lowercase",
    "S7.4.4.4-004": "default padding_empty iachar_consistency",
}
PAIR_VARIANTS = {
    "R721": "len_keyword_positional_kind kind_keyword_positional_length",
    "R723": "bare_expression",
    "C724": "negative",
    "C725": "bare_suffix",
    "C726": "allocate_mixed",
    "C728": "pure elemental recursive array pointer",
    "C729": "component_comma function_comma allocate_comma",
    "C730": "double_colon",
    "C731": "function_length dummy_length",
    "R724": "apostrophe_closer quotation_closer prefix_separator",
}
LEGACY = {
    "component": ("forbidden-component", "component_repair", 12),
    "module-function-result": ("forbidden-module-result", "module_result_repair", 19),
    "local-variable": ("forbidden-local", "local_repair", 25),
    "allocate-local": ("allocate-nondummy", "allocate_local_repair", 31),
    "allocate-dummy-deferred": ("allocate-deferred-dummy", "allocate_deferred_repair", 36),
    "internal-function-result": ("forbidden-internal-result", "internal_result_repair", 43),
}


def case_id(rule, state, variant):
    return rule.replace(".", "_").replace("-", "_") + "_" + state + "__" + variant


def decode_literal(token):
    delimiter = token[0]
    if delimiter not in "'\"":
        raise ValueError("not a character literal")
    value, index = [], 1
    while index < len(token):
        character = token[index]
        if character == delimiter:
            if index + 1 < len(token) and token[index + 1] == delimiter:
                value.append(delimiter)
                index += 2
                continue
            if token[index + 1:].strip():
                raise ValueError("unexpected data after literal")
            return "".join(value)
        value.append(character)
        index += 1
    raise ValueError("unterminated character literal")


class CharacterTypeCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated_files, cls.plans, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in all_cases if (
            case.rule in {"R721", "R722", "R723", "R724", *(f"C{i}" for i in range(724, 733))}
            or case.rule.startswith("S7.4.4."))}
        cls.negatives = {name: case for name, case in cls.cases.items() if case.kind == "invalid"}

    def input(self, name, filename=None):
        case = self.cases[name]
        if case.fixture:
            return (case.fixture.root / (filename or "source.f90")).read_bytes()
        return Path(case.path).read_bytes()

    def parameter(self, name, parameter):
        text = self.input(name).decode("ascii")
        match = re.search(r"^\s*character.*?::\s*" + re.escape(parameter) + r"\s*=\s*(.+)$",
                          text, re.I | re.M)
        self.assertIsNotNone(match, (name, parameter))
        return decode_literal(match.group(1))

    def diagnostic(self, case):
        return case.contract["diagnostic"] if case.contract else case.fixture.expectation.diagnostic

    def output(self, case, message, family="lfortran", filename=None, line=None, end_line=None):
        diagnostic = self.diagnostic(case)
        filename = filename or diagnostic["file"]
        line = diagnostic["line"] if line is None else line
        if family == "lfortran":
            return (f"{filename}:{line}-{line if end_line is None else end_line}:1-90: "
                    f"semantic error: {message}\n")
        return f"{filename}:{line}:1: error: {message}\n"

    def judge(self, case, output, family="lfortran", returncode=1, timed_out=False):
        compiler = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023")
        result = runner.ProcessResult(returncode, output, timed_out=timed_out)
        return runner.judge_diagnostic(result, compiler, case.rule, self.diagnostic(case)).outcome

    def test_exact_execution_ids_phases_and_no_duplicate_discovery(self):
        expected = {"C726_valid"}
        for rule, variants in RUN_VARIANTS.items():
            expected.update(case_id(rule, "valid", variant) for variant in variants.split())
        for rule, variants in PAIR_VARIANTS.items():
            for variant in variants.split():
                expected.add(case_id(rule, "invalid", variant))
                expected.add(case_id(rule, "valid", variant + "_repair"))
        expected.update({"C724_valid__supported", "C727_valid__unused_dummy_function",
                         "C727_valid__caller_assumed_repair"})
        for member, (_, repair, _) in LEGACY.items():
            expected.add("C726_invalid:" + member)
            expected.add("C726_valid__" + repair)
        self.assertEqual(len(expected), 116)
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.plans), expected)
        self.assertEqual(len(self.negatives), 26)
        for name, case in self.cases.items():
            plan = self.plans[name]
            phase = case.fixture.expectation.phase if case.fixture else (
                "compile" if case.kind == "invalid" else "run")
            with self.subTest(case=name):
                self.assertEqual(phase, plan["phase"])
                self.assertEqual(set(case.meta.facets), set(plan["facets"]))
                self.assertFalse(case.meta.profiles)
                if not name.startswith("C726_invalid:"):
                    self.assertEqual(case.meta.standard, "f2023")
        self.assertEqual(sum(plan["phase"] == "run" for plan in self.plans.values()), 61)
        self.assertEqual(sum(plan["phase"] == "compile" for plan in self.plans.values()), 55)

    def test_generator_matches_exact_committed_input_bytes(self):
        for path, expected in self.generated_files.items():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(path.read_bytes(), expected)
        for case in self.cases.values():
            self.assertTrue(case.meta.facets)
            if case.fixture:
                self.assertEqual(case.fixture.expectation.exit_code, 0)

    def test_legacy_container_and_runtime_body_are_preserved(self):
        raw = (ROOT / "tests/clause07/C726_invalid.f90").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "b879e1f2b42ec9deca084b660798d658bf1bc5e1989c53d81b14aa1c3005784e")
        valid = self.input("C726_valid")
        body = valid[valid.index(b"module c726_valid_m"):]
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "d9e18100d37041c969513f1bb2e5e05147ecc9f3cfce62ec1766c363671584cd")
        self.assertNotIn(b"every permitted use", valid)
        self.assertEqual(self.cases["C726_valid"].meta.evidence, "positive-control")
        self.assertEqual(set(self.cases["C726_valid"].meta.facets),
                         {"ordinary-dummies", "named-constant", "character-type-guard"})
        data = json.loads((ROOT / "tests/clause07/C726_invalid.cases.json").read_text())
        self.assertEqual(set(data["cases"]), set(LEGACY))
        for member, (facet, _, marker) in LEGACY.items():
            case = self.cases["C726_invalid:" + member]
            with self.subTest(member=member):
                self.assertEqual(case.path, str(ROOT / "tests/clause07/C726_invalid.f90"))
                self.assertEqual(case.review_key, case.name)
                self.assertEqual(case.meta.facets, [facet])
                self.assertEqual(case.isolated[0], marker)
                self.assertEqual(case.contract["outcome"], "diagnose")
                self.assertNotIn("allow_nonfatal", self.diagnostic(case))
        internal = self.cases["C726_invalid:internal-function-result"]
        self.assertEqual((self.diagnostic(internal)["line"], self.diagnostic(internal)["end_line"]), (42, 43))
        message = "Character-valued internal function 'g' must not be assumed length"
        self.assertEqual(self.judge(internal, self.output(internal, message, line=40)), "fail")

    def test_each_negative_has_one_exact_line_local_minimal_repair(self):
        fixes = {
            ("R721", "len_keyword_positional_kind"): ("len=3,dk", "len=3,kind=dk"),
            ("R721", "kind_keyword_positional_length"): ("kind=dk,3", "kind=dk,len=3"),
            ("R723", "bare_expression"): ("character*2+1", "character*(2+1)"),
            ("C724", "negative"): ("kind=-1", "kind=kind('A')"),
            ("C725", "bare_suffix"): ("character*3_ik", "character*3"),
            ("C726", "allocate_mixed"): ("assumed_dummy,local_deferred", "assumed_dummy"),
            ("C730", "double_colon"): ("character*3,", "character*3"),
            ("R724", "apostrophe_closer"): ("'ABC\"", "'ABC'"),
            ("R724", "quotation_closer"): ("\"ABC'", '"ABC"'),
            ("R724", "prefix_separator"): ("dk'ABC'", "dk_'ABC'"),
        }
        for variant in PAIR_VARIANTS["C728"].split():
            fixes["C728", variant] = ("character(*)", "character(3)")
        for variant in PAIR_VARIANTS["C729"].split():
            fixes["C729", variant] = ("character*3,", "character*3")
        for variant in PAIR_VARIANTS["C731"].split():
            fixes["C731", variant] = ("character(n)", "character(2)")
        self.assertEqual(len(fixes), 20)
        for (rule, variant), (wrong, repair) in fixes.items():
            name = case_id(rule, "invalid", variant)
            before = self.input(name)
            after = self.input(case_id(rule, "valid", variant + "_repair"))
            with self.subTest(case=name):
                self.assertEqual(before.count(wrong.encode()), 1)
                self.assertEqual(before.replace(wrong.encode(), repair.encode(), 1), after)
                self.assertEqual(sum(a != b for a, b in zip(before.splitlines(), after.splitlines())), 1)
                self.assertEqual(len(before.splitlines()), len(after.splitlines()))
        for member, (_, variant, _) in LEGACY.items():
            before = self.cases["C726_invalid:" + member].isolated[-1].encode("ascii")
            length = b"1" if member == "internal-function-result" else b"3"
            after = self.input("C726_valid__" + variant)
            with self.subTest(case=member):
                self.assertEqual(before.count(b"character(*)"), 1)
                self.assertEqual(before.replace(b"character(*)", b"character(" + length + b")"), after)

    def test_wrong_causes_and_source_recovery_never_credit_a_negative(self):
        wrong_causes = [
            "Only Integer literals or expressions which reduce to constant Integer are accepted as kind parameters",
            "Expected a type, kind, parameter, function, or constant expression",
            "Unexpected end of file; missing END statement",
            "Function results are not supported",
            "Error in enclosing PRINT statement",
            "Invalid character in name",
            "Missing right parenthesis",
            "expected ')'",
            "Fortran obsolescent feature: statement function",
        ]
        for name, case in self.negatives.items():
            diagnostic = self.diagnostic(case)
            good = diagnostic["contains_any"][0]
            for cause in wrong_causes:
                for family in ("lfortran", "gfortran", "flang"):
                    with self.subTest(case=name, cause=cause, family=family):
                        self.assertEqual(self.judge(case, self.output(case, cause, family), family), "fail")
            for text in (
                self.output(case, "Not yet implemented: " + good),
                self.output(case, "Unsupported feature: " + good),
                self.output(case, good, filename="unrelated.f90"),
                self.output(case, good, line=diagnostic["line"] - 1),
                self.output(case, good, end_line=diagnostic.get("end_line", diagnostic["line"]) + 1),
                self.output(case, "unrelated problem") + "  1 | " + good,
                self.output(case, good) + "ASR verify pass error\n",
                self.output(case, good) + "LLVM ERROR: invalid IR\n",
                self.output(case, good) + "error: out of memory\n",
            ):
                with self.subTest(case=name, output=text):
                    self.assertEqual(self.judge(case, text), "fail")
            for status, timed_out in ((-11, False), (139, False), (1, True)):
                with self.subTest(case=name, status=status, timed_out=timed_out):
                    self.assertEqual(self.judge(case, self.output(case, good),
                                                returncode=status, timed_out=timed_out), "fail")

    def test_specific_reports_can_count_without_mandatory_fatal_exit(self):
        messages = {
            "C724_invalid__negative": "Kind -1 not supported for type CHARACTER at (1)",
            "C725_invalid__bare_suffix": "Old-style character length at (1) does not allow a kind parameter",
            "C726_invalid:component": "A CHARACTER component must have a constant length",
            "C726_invalid:module-function-result": "Character-valued module procedure 'f' must not be assumed length",
            "C726_invalid:internal-function-result": "Character-valued internal procedure 'g' must not be assumed length",
            "C726_invalid:local-variable": "Assumed-length character entity 's' must be a dummy argument or a named constant",
            "R724_invalid__apostrophe_closer": "Unterminated character constant beginning at (1)",
            "R724_invalid__quotation_closer": "Unterminated character literal",
            "R724_invalid__prefix_separator": "Missing underscore after character kind prefix",
            "R721_invalid__len_keyword_positional_kind": "KIND= is required after LEN=",
            "R721_invalid__kind_keyword_positional_length": "LEN= is required after KIND=",
            "R723_invalid__bare_expression": "Character length expression must be parenthesized",
            "C730_invalid__double_colon": "Character length comma is not permitted with a double-colon separator",
        }
        for name in ("C726_invalid:allocate-local", "C726_invalid:allocate-dummy-deferred",
                     "C726_invalid__allocate_mixed"):
            messages[name] = "Each allocate-object must be a dummy argument with assumed character length"
        attributes = {
            "array": "return an array", "pointer": "return a POINTER",
            "pure": "be PURE", "elemental": "be ELEMENTAL", "recursive": "be RECURSIVE",
        }
        for variant, predicate in attributes.items():
            messages[case_id("C728", "invalid", variant)] = "An assumed-length CHARACTER(*) function cannot " + predicate
        for variant in PAIR_VARIANTS["C729"].split():
            messages[case_id("C729", "invalid", variant)] = "Character length comma is only allowed in a type declaration"
        messages["C731_invalid__function_length"] = (
            "Character-valued statement function 'f' at (1) must have constant length")
        messages["C731_invalid__dummy_length"] = (
            "Character-valued argument 'x' of statement function at (1) must have constant length")
        self.assertEqual(set(messages), set(self.negatives))
        for name, message in messages.items():
            for family in ("lfortran", "gfortran", "flang"):
                for status in (0, 1):
                    case = self.negatives[name]
                    with self.subTest(case=name, family=family, status=status):
                        self.assertEqual(self.judge(case, self.output(case, message, family),
                                                    family, returncode=status), "pass")

    def test_attribute_diagnostics_do_not_credit_a_different_function_context(self):
        for variant in PAIR_VARIANTS["C728"].split():
            case = self.negatives[case_id("C728", "invalid", variant)]
            for message in (
                "Assumed-length character function must be external",
                "Assumed character length is only allowed for external functions",
                "The character-valued function must not be assumed length",
            ):
                with self.subTest(case=case.name, cause=message):
                    self.assertEqual(self.judge(case, self.output(case, message)), "fail")
        local_message = ("AssumedLength-string variable should be a dummy variable "
                         "(intent IN or OUT or INOUT) or a function return variable.")
        for member in ("module-function-result", "internal-function-result"):
            case = self.negatives["C726_invalid:" + member]
            self.assertEqual(self.judge(case, self.output(case, local_message)), "fail")
        for member in ("component", "local-variable"):
            case = self.negatives["C726_invalid:" + member]
            self.assertEqual(self.judge(case, self.output(case, local_message)), "pass")
        for variant in PAIR_VARIANTS["C731"].split():
            case = self.negatives[case_id("C731", "invalid", variant)]
            self.assertEqual(self.judge(case, self.output(case, "must have a constant character length")), "fail")

    def test_c731_cross_subject_reports_fail_at_every_allowed_location(self):
        subjects = {
            "function_length": (
                b"character(n) :: f", b"character(2) :: x",
                "Character-valued statement function 'f' at (1) must have constant length",
                [
                    "character length of a statement function dummy argument must be constant",
                    "Character-valued argument 'x' of statement function at (1) must have constant length",
                    "Dummy argument x must have constant character length in a statement function",
                ]),
            "dummy_length": (
                b"character(n) :: x", b"character(2) :: f",
                "Character-valued argument 'x' of statement function at (1) must have constant length",
                [
                    "character length of a statement function must be constant",
                    "Character-valued statement function 'f' at (1) must have constant length",
                    "Result f must have constant character length in a statement function",
                ]),
        }
        for variant, (nonconstant, constant, correct, wrong_messages) in subjects.items():
            case = self.negatives["C731_invalid__" + variant]
            self.assertIn(nonconstant, self.input(case.name))
            self.assertIn(constant, self.input(case.name))
            diagnostic = self.diagnostic(case)
            for line in range(diagnostic["line"], diagnostic["end_line"] + 1):
                for family in ("lfortran", "gfortran", "flang"):
                    for status in (0, 1):
                        with self.subTest(case=case.name, line=line, family=family, status=status):
                            self.assertEqual(self.judge(
                                case, self.output(case, correct, family, line=line),
                                family, returncode=status), "pass")
                        for wrong in wrong_messages:
                            with self.subTest(case=case.name, line=line, family=family,
                                              status=status, wrong=wrong):
                                self.assertEqual(self.judge(
                                    case, self.output(case, wrong, family, line=line),
                                    family, returncode=status), "fail")

    def test_c727_withdrawal_retains_only_independent_admission_controls(self):
        removed = "C727_invalid__caller_assumed"
        self.assertNotIn(removed, self.cases)
        self.assertNotIn(removed, self.plans)
        self.assertNotIn(removed, self.repairs)
        folder = ROOT / "tests/fixtures/character_type_c727_invalid__caller_assumed"
        self.assertFalse((folder / "fixture.json").exists())
        self.assertFalse((folder / "source.f90").exists())
        self.assertFalse(any(folder in path.parents for path in self.generated_files))
        fixed = self.cases["C727_valid__caller_assumed_repair"]
        dummy = self.cases["C727_valid__unused_dummy_function"]
        self.assertEqual(self.input(fixed.name),
                         b"program p\n    implicit none\n    character(3), external :: f\nend program\n")
        self.assertEqual(self.input(dummy.name),
                         b"subroutine p(f)\n    implicit none\n    character(*), external :: f\nend subroutine\n")
        self.assertEqual(fixed.meta.facets, ["fixed-length-external-declaration"])
        self.assertEqual(dummy.meta.facets, ["dummy-function-declaration"])
        for case in (fixed, dummy):
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, "positive-control")
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.diagnostic, {})
        self.assertFalse(any(case.rule == "C727" for case in self.negatives.values()))
        self.assertIn("caller-declaration-exclusion", self.registry.requirements["C727"]["pending"])

    def test_repertoire_and_literal_values_are_independently_counted(self):
        name = "S7_4_4_2_002_valid__repertoire"
        upper = self.parameter(name, "upper")
        lower = self.parameter(name, "lower")
        digits = self.parameter(name, "digits")
        special = self.parameter(name, "special")
        expected_special = [" ", "=", "+", "-", "*", "/", "\\", "(", ")", "[", "]", "{", "}",
                            ",", ".", ":", ";", "!", '"', "%", "&", "~", "<", ">", "?", "'",
                            "`", "^", "|", "$", "#", "@"]
        self.assertEqual(upper, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.assertEqual(lower, "abcdefghijklmnopqrstuvwxyz")
        self.assertEqual(digits, "0123456789")
        self.assertEqual(list(special), expected_special)
        repertoire = upper + lower + digits + "_" + special
        self.assertEqual(len(repertoire), 95)
        self.assertEqual(len(set(repertoire)), 95)
        self.assertIn(b"len(repertoire) /= 95", self.input(name))
        expected = {
            ("S7_4_4_3_003_valid__opposite_delimiters", "a"): 'A"B',
            ("S7_4_4_3_003_valid__opposite_delimiters", "b"): "A'B",
            ("S7_4_4_3_004_valid__apostrophe", "text"): "A'B",
            ("S7_4_4_3_004_valid__quotation", "text"): 'A"B',
            ("S7_4_4_3_004_valid__boundaries", "a"): "'X'",
            ("S7_4_4_3_004_valid__boundaries", "a2"): "''",
            ("S7_4_4_3_004_valid__boundaries", "q"): '"X"',
            ("S7_4_4_3_004_valid__boundaries", "q2"): '""',
            ("S7_4_4_3_005_valid__context", "a"): "'",
            ("S7_4_4_3_005_valid__context", "q"): '"',
        }
        for (case, variable), value in expected.items():
            with self.subTest(case=case, variable=variable):
                self.assertEqual(self.parameter(case, variable), value)
        self.assertEqual(decode_literal("''"), "")
        self.assertEqual(decode_literal('""'), "")
        self.assertEqual(decode_literal("' '"), " ")
        self.assertEqual(decode_literal("''''"), "'")
        self.assertEqual(decode_literal('""""'), '"')

    def test_free_and_fixed_literal_case_blanks_and_record_bytes(self):
        for variant in ("free_graphics", "fixed_graphics"):
            name = "S7_4_4_3_002_valid__" + variant
            self.assertEqual(self.parameter(name, "a"), " A  a ")
            self.assertEqual(self.parameter(name, "b"), "a  A  ")
            raw = self.input(name)
            self.assertIn(b"a(2:2) == a(5:5)", raw)
            self.assertIn(b"len(a) /= 6", raw)
        fixed = self.input("S7_4_4_3_002_valid__fixed_graphics")
        self.assertTrue(fixed.endswith(b"\n"))
        self.assertTrue(all(len(line) == 72 for line in fixed.splitlines()))
        self.assertTrue(all(line[:6] == b"      " for line in fixed.splitlines()))
        self.assertEqual(self.cases["S7_4_4_3_002_valid__fixed_graphics"].fixture.build[0].form, "fixed")

    def test_default_order_obligations_are_not_ascii_code_arithmetic(self):
        for variant, text, comparisons in (
            ("uppercase", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 25),
            ("digits", "0123456789", 9),
            ("lowercase", "abcdefghijklmnopqrstuvwxyz", 25),
        ):
            name = "S7_4_4_4_002_valid__" + variant
            self.assertEqual(self.parameter(name, "alphabet"), text)
            self.assertIn(f"do i = 1, {comparisons}".encode(), self.input(name))
            self.assertIn(b"alphabet(i:i) < alphabet(i+1:i+1)", self.input(name))
        for variant, first, last in (("blank_uppercase", "A", "Z"), ("blank_lowercase", "a", "z")):
            raw = self.input("S7_4_4_4_002_valid__" + variant)
            self.assertIn(f"' ' < '0' .and. '0' < '9' .and. '9' < '{first}'".encode(), raw)
            self.assertIn(f"' ' < '{first}' .and. '{first}' < '{last}' .and. '{last}' < '0'".encode(), raw)
            self.assertIn(b"digits_first .or. letters_first", raw)
        for path, raw in self.generated_files.items():
            if path.suffix == ".f90":
                with self.subTest(path=path):
                    self.assertNotRegex(raw.lower(), rb"\bichar\s*\(")
                    self.assertNotRegex(raw.lower(), rb"\b(?:transfer|storage_size|c_sizeof)\s*\(")
                    self.assertNotRegex(raw.lower(), rb"\bstop\s+77\b")
                    self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_assumed_dummy_allocation_and_external_premises_remain_real_effects(self):
        optional = self.input("S7_4_4_2_006_valid__optional")
        self.assertIn(b"if (present(text)) then", optional)
        self.assertIn(b"else\n", optional)
        self.assertNotRegex(optional.lower(), rb"present\(text\).*(?:\.and\.|\.or\.)")
        for variant, attribute in (("allocate_assumed", b"allocatable"),
                                   ("allocate_assumed_pointers", b"pointer")):
            name = "S7_4_4_2_006_valid__" + variant
            raw = self.input(name)
            self.assertIn(b"character(2), " + attribute, raw)
            self.assertIn(b"character(5), " + attribute, raw)
            self.assertIn(b"character(*), " + attribute + b", intent(inout)", raw)
            self.assertIn(b"allocate(character(*) :: a, b, stat=stat)", raw)
            self.assertLess(raw.index(b"if (stat /= 0)"), raw.index(b"if (len(a)"))
            self.assertEqual(self.plans[name]["phase"], "run")
        external = self.cases["S7_4_4_2_006_valid__external"].fixture
        self.assertEqual([step.source for step in external.build], ["external.f90", "main.f90"])
        self.assertIn(b"character(*) :: text", self.input(external.name, "external.f90"))
        self.assertIn(b"if (len(text) /= expected)", self.input(external.name, "external.f90"))
        callers = self.input(external.name, "main.f90")
        self.assertIn(b"character(2), external :: character_external", callers)
        self.assertIn(b"character(5), external :: character_external", callers)
        routes = self.cases["S7_4_4_2_006_valid__access_routes"].fixture
        self.assertEqual(routes.expectation.phase, "run")
        self.assertEqual([step.source for step in routes.build],
                         ["declarations.f90", "external.f90", "routes.f90", "main.f90"])
        self.assertIn(b"call forwarded(f)", self.input(routes.name, "routes.f90"))
        self.assertIn(b"use character_declarations", self.input(routes.name, "routes.f90"))

    def test_only_actual_direct_facets_leave_pending_and_no_links_are_created(self):
        coverage = {}
        for case in self.cases.values():
            coverage.setdefault(case.rule, set()).update(case.meta.facets)
        for section in ("7.4.4.1", "7.4.4.2", "7.4.4.3", "7.4.4.4"):
            catalogue = self.registry.catalogues[section]
            for requirement in catalogue["requirements"]:
                covered = coverage.get(requirement["id"], set())
                self.assertEqual(set(requirement["pending"]), set(requirement["facets"]) - covered)
        for rule, facet in (
            ("S7.4.4.1-001", "length-parameter-integer-kind"),
            ("S7.4.4.1-002", "method-kind-inquiry"),
            ("S7.4.4.2-006", "named-constant-value-length"),
            ("S7.4.4.4-001", "method-cardinality-and-result-kind"),
            ("S7.4.4.2-003", "blank-designation-interface"),
            ("S7.4.4.3-002", "fixed-control-policy"),
            ("S7.4.4.4-003", "external-collation-reference"),
            ("R721", "kind-expression-premises"),
        ):
            self.assertIn(facet, self.registry.requirements[rule]["pending"])


if __name__ == "__main__":
    unittest.main()
