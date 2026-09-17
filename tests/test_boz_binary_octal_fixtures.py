"""Source/repair/digit-position and actual diagnostic-predicate regression probes."""
from collections import Counter
import copy
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_boz_binary_octal_fixtures as generated
import generate_derived_parameter_fixtures as parameters

CONTROLS = {
    "R773": "apostrophe_control quotation_control",
    "C7117": "digit_control interior_control",
    "R774": "apostrophe_control quotation_control",
    "C7118": "digit_control interior_control",
}
NEGATIVES = {
    "R773": "empty_apostrophe empty_quotation nondigit_letter nondigit_underscore nondigit_plus nondigit_minus",
    "C7117": "digit_2 digit_3 digit_4 digit_5 digit_6 digit_7 digit_8 digit_9 interior_digit",
    "R774": "empty_apostrophe empty_quotation nondigit_letter nondigit_underscore nondigit_plus nondigit_minus",
    "C7118": "digit_8 digit_9 interior_digit",
}
WRONG_CAUSES = [
    "Empty CHARACTER literal",
    "Empty DATA value list",
    "Too many values in DATA statement",
    "INTEGER object 'subject' has already been initialized",
    "A REAL DATA recipient cannot have a BOZ initializer",
    "BOZ constant is not allowed as an ordinary procedure argument",
    "Invalid integer kind selector",
    "Invalid digit in a formatted input field",
    "Expected digit",
    "Syntax error in DATA statement",
    "Illegal character in BOZ constant at (1)",
    "Expected '/' in DATA statement",
    "Unterminated string",
    "Unexpected end of file",
    "Unknown type 'binary'",
]


def judge(case, message, family="lfortran", code=1, line=None, file=None, severity=None,
          echo=False, timed_out=False, exclusions=True, trailer=""):
    predicate = case.fixture.expectation.diagnostic
    if not exclusions:
        predicate = dict(predicate, excludes_any=[])
    line = predicate["line"] if line is None else line
    file = predicate["file"] if file is None else file
    point = f"{line}-{line}:1-200" if family == "lfortran" else f"{line}:1"
    severity = severity or ("syntax error" if family == "lfortran" else "error")
    output = f"{file}:{point}: {severity}: {'unrelated failure' if echo else message}\n"
    if echo:
        output += "  1 | " + message + "\n"
    output += trailer
    result = runner.judge_diagnostic(
        runner.ProcessResult(code, output, timed_out=timed_out),
        runner.Compiler(family, family, "f23" if family == "lfortran" else
                        "f2018" if family == "flang" else "f2023"),
        case.rule, predicate)
    return result.outcome


def predicate_probes(cases):
    """Synthetic predicate evaluations, explicitly not compiler observations."""
    specs = generated.build_corpus()[1]
    for name, case in sorted(cases.items()):
        if case.kind != "invalid":
            continue
        predicate = case.fixture.expectation.diagnostic
        for family in ("lfortran", "gfortran", "flang"):
            for message in predicate["contains_any"]:
                for code in (0, 1):
                    yield dict(case=name, category="qualified-report-no-fatal-policy",
                               arguments=dict(message=message, family=family, code=code), expected="pass")
                for wrong, right in (("binary", "octal"), ("octal", "binary")):
                    if wrong in message:
                        yield dict(case=name, category="wrong-radix",
                                   arguments=dict(message=message.replace(wrong, right), family=family, exclusions=False),
                                   expected="fail")
                for wrong, right in (("'b\"", "'o\""), ("'o\"", "'b\"")):
                    if wrong in message:
                        yield dict(case=name, category="wrong-radix-token",
                                   arguments=dict(message=message.replace(wrong, right), family=family, exclusions=False),
                                   expected="fail")
            for message in WRONG_CAUSES:
                yield dict(case=name, category="wrong-role-property-or-generic-recovery",
                           arguments=dict(message=message, family=family, exclusions=False), expected="fail")
            if specs[name]["body"]:
                yield dict(case=name, category="nonempty-body-not-empty-recovery",
                           arguments=dict(message="Empty set of digits in BOZ constant at (1)",
                                          family=family, exclusions=False), expected="fail")
            message = predicate["contains_any"][0]
            for category, extra in [
                ("wrong-file", dict(file="other.f90")),
                ("wrong-line", dict(line=predicate["line"]-1)),
                ("source-echo", dict(echo=True)),
                ("timeout", dict(timed_out=True)),
                ("crash", dict(code=-11)),
            ]:
                yield dict(case=name, category=category, arguments=dict(message=message, family=family, **extra),
                           expected="fail")
            for suffix in (" not implemented", " unsupported", " ASR verify pass error",
                           " internal compiler error", " out of memory"):
                yield dict(case=name, category="failure-not-corroboration",
                           arguments=dict(message=message+suffix, family=family), expected="fail")
            internal = f"{predicate['file']}:{predicate['line']}:1: error: Internal: no symbol found for 'subject'\n"
            yield dict(case=name, category="native-internal-veto",
                       arguments=dict(message=message, family=family, trailer=internal), expected="fail")


class BozBinaryOctalFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in cls.all_cases if "/fixtures/boz_binary_octal_" in c.path}
        cls.catalogue = cls.registry.catalogues["7.7"]

    def source(self, name):
        return (self.cases[name].fixture.root / "source.f90").read_text()

    def parse_context(self, source):
        lines = source.splitlines()
        self.assertEqual(lines[:2], ["program boz_lexical", "implicit none"])
        self.assertEqual(lines[-1], "end program boz_lexical")
        declarations, pairs = [], []
        saw_data = False
        for number, line in enumerate(lines[2:-1], 3):
            declaration = re.fullmatch(r"integer :: ([a-z]\w*)", line)
            if declaration:
                self.assertFalse(saw_data)
                declarations.append(declaration[1])
                continue
            data = re.fullmatch(r"data ([a-z]\w*) / ([BO])(['\"])([^'\"]*)\3 /", line)
            self.assertIsNotNone(data, line)
            saw_data = True
            name, prefix, quote, body = data.groups()
            pairs.append(dict(object=name, prefix=prefix, quote=quote, body=body, line=number))
        self.assertEqual(len(declarations), len(set(declarations)))
        self.assertEqual(Counter(p["object"] for p in pairs), Counter(declarations))
        self.assertTrue(all(count == 1 for count in Counter(p["object"] for p in pairs).values()))
        self.assertEqual(pairs[-1]["object"], "subject")
        return pairs

    def test_exact_case_ids_roles_phases_and_twelve_facets(self):
        expected = {generated.identifier(rule, variant): "valid"
                    for rule, variants in CONTROLS.items() for variant in variants.split()}
        expected.update({generated.identifier(rule, variant, True): "invalid"
                         for rule, variants in NEGATIVES.items() for variant in variants.split()})
        self.assertEqual(len(expected), 32)
        self.assertEqual(set(expected), set(self.specs))
        self.assertEqual(set(expected), set(self.cases))
        self.assertEqual(Counter(expected.values()), {"valid": 8, "invalid": 24})
        covered = {}
        for name, kind in expected.items():
            case, spec = self.cases[name], self.specs[name]
            covered.setdefault(case.rule, set()).update(spec["facets"])
            self.assertEqual(case.kind, kind)
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertEqual(case.fixture.expectation.step, "source")
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if kind == "invalid" else "success")
            self.assertEqual(case.meta.evidence, "effect" if kind == "invalid" else "positive-control")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertIsNone(case.fixture.link)
            self.assertFalse(case.rule.startswith("S"))
        self.assertEqual(covered, {r: set(fs) for r, fs in generated.ELIGIBLE.items()})
        self.assertEqual(sum(map(len, covered.values())), 12)

    def test_exact_generated_files_and_no_nonlexical_execution(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("boz_binary_octal_*/*") if p.is_file()}
        self.assertEqual(set(self.files), actual)
        self.assertEqual(len(actual), 64)
        for path, content in self.files.items():
            self.assertEqual(path.read_bytes(), content)
            content.decode("ascii")
            self.assertTrue(content.endswith(b"\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, content.splitlines())), 132)
                self.assertNotRegex(content.decode().lower(), r"\b(?:real|complex|character|pointer|allocatable|parameter|kind)\b")
                self.assertNotRegex(content.decode().lower(), r"\b(?:call|print|if|stop|allocate|deallocate)\b")
                self.assertNotRegex(content.decode(), r"\b[Zz]['\"]")
            else:
                manifest = json.loads(content)
                self.assertNotIn("run", manifest)
                self.assertNotIn("requires", manifest)
                self.assertNotIn("profiles", manifest)

    def test_every_actual_DATA_context_is_complete_unique_and_default_INTEGER(self):
        for name, spec in self.specs.items():
            with self.subTest(case=name):
                pairs = self.parse_context(self.source(name))
                self.assertEqual(len(pairs), len(spec["prelude"]) + 1)
                for actual, prelude in zip(pairs[:-1], spec["prelude"]):
                    self.assertEqual(actual["object"], prelude["object"])
                    self.assertEqual(generated.token(actual["prefix"], actual["quote"], actual["body"]), prelude["literal"])
                    self.assertEqual(generated.lexical_conditions(actual["prefix"], actual["body"])["owners"], [])
                target = pairs[-1]
                self.assertEqual((target["prefix"], target["quote"], target["body"]),
                                 (spec["prefix"], spec["quote"], spec["body"]))
                self.assertEqual(spec["receiver"], dict(
                    type="integer", kind="default", rank=0, pointer=False, allocatable=False,
                    dummy=False, automatic=False, other_initialization=False, data_values_per_object=1))
                expected = [] if spec["kind"] == "valid" else [spec["rule"]]
                self.assertEqual(generated.lexical_conditions(spec["prefix"], spec["body"])["owners"], expected)
                self.assertIsNone(spec["lexical_conditions"]["numeric_value"])

    def test_context_guards_reject_receiver_double_initialization_and_missing_declaration(self):
        source = self.source(generated.identifier("R773", "apostrophe_control"))
        for mutant in [
            source.replace("integer :: subject", "real :: subject"),
            source.replace("integer :: subject\n", ""),
            source.replace("integer :: subject", "integer :: subject=0"),
            source.replace("data subject / B'0' /", "data subject / B'0' /\ndata subject / B'0' /"),
            source.replace("data subject / B'0' /", "data subject / B'0',B'0' /"),
        ]:
            with self.assertRaises(AssertionError):
                self.parse_context(mutant)

    def test_all_closed_empty_quotes_and_nondigit_candidates_have_correct_owners(self):
        for rule, prefix in (("R773", "B"), ("R774", "O")):
            for variant, quote in (("empty_apostrophe", "'"), ("empty_quotation", '"')):
                name = generated.identifier(rule, variant, True)
                spec = self.specs[name]
                self.assertEqual(spec["literal"], prefix + quote + quote)
                self.assertTrue(spec["lexical_conditions"]["empty"])
                self.assertEqual(self.repairs[name]["body_after"], "0")
            for variant, char in (("nondigit_letter", "A"), ("nondigit_underscore", "_"),
                                  ("nondigit_plus", "+"), ("nondigit_minus", "-")):
                name = generated.identifier(rule, variant, True)
                self.assertEqual(self.specs[name]["body"], char)
                self.assertEqual(self.specs[name]["lexical_conditions"]["nondigit_positions"], [1])
                self.assertEqual(self.specs[name]["lexical_conditions"]["excluded_decimal_positions"], [])
                self.assertEqual(self.repairs[name]["body_after"], "0")

    def test_all_decimal_alphabets_and_interior_positions_are_exhaustive_and_independent(self):
        for prefix, valid, rule in (("B", "01", "C7117"), ("O", "01234567", "C7118")):
            for digit in "0123456789":
                result = generated.lexical_conditions(prefix, digit)
                self.assertEqual(result["nondigit_positions"], [])
                self.assertEqual(result["excluded_decimal_positions"], [] if digit in valid else [1])
                self.assertEqual(result["owners"], [] if digit in valid else [rule])
            for char in "A_+-":
                result = generated.lexical_conditions(prefix, char)
                self.assertEqual(result["owners"], ["R773" if prefix == "B" else "R774"])
                self.assertEqual(result["nondigit_positions"], [1])
            self.assertEqual(generated.lexical_conditions(prefix, "\u0662")["nondigit_positions"], [1])
        for rule, before, after, digit in (("C7117", "1021", "1011", "2"), ("C7118", "1781", "1771", "8")):
            spec = self.specs[generated.identifier(rule, "interior_digit", True)]
            self.assertEqual(spec["body"], before)
            self.assertEqual(spec["source_anchor"]["offending_body_positions"], [3])
            self.assertEqual(before[2], digit)
            self.assertEqual(self.repairs[generated.identifier(rule, "interior_digit", True)]["body_after"], after)
            self.assertEqual(before[:2], after[:2])
            self.assertEqual(before[3:], after[3:])
        self.assertEqual({self.specs[generated.identifier("C7117", v, True)]["body"]
                          for v in NEGATIVES["C7117"].split() if v.startswith("digit_")}, set("23456789"))

    def test_requested_quoted_and_alphabet_admissions_are_in_actual_controls(self):
        for rule, tokens in (
            ("R773", {'B"0"', 'B"1"', 'B"101"'}),
            ("R774", {'O"0"', 'O"7"', 'O"157"'}),
        ):
            for variant in CONTROLS[rule].split():
                literals = {item["literal"] for item in self.specs[generated.identifier(rule, variant)]["prelude"]}
                self.assertTrue(tokens <= literals)
        for variant in CONTROLS["C7117"].split():
            literals = {p["literal"] for p in self.specs[generated.identifier("C7117", variant)]["prelude"]}
            self.assertEqual(literals, {"B'0'", "B'1'", "B'101'", 'B"0"', 'B"1"', 'B"101"'})
        for variant in CONTROLS["C7118"].split():
            literals = {p["literal"] for p in self.specs[generated.identifier("C7118", variant)]["prelude"]}
            self.assertTrue({f"O'{n}'" for n in "01234567"} <= literals)
            self.assertIn('O"157"', literals)

    def test_exact_focused_repairs_and_same_primary_control_sharing(self):
        self.assertEqual(set(self.repairs), {name for name, spec in self.specs.items() if spec["kind"] == "invalid"})
        for name, repair in self.repairs.items():
            bad, good = self.source(name), self.source(repair["control"])
            spec, control = self.specs[name], self.specs[repair["control"]]
            self.assertEqual(spec["rule"], control["rule"])
            self.assertEqual(control["kind"], "valid")
            self.assertEqual(bad.count(repair["wrong"]), 1)
            self.assertEqual(bad.replace(repair["wrong"], repair["repaired"], 1), good)
            self.assertEqual(spec["prefix"], control["prefix"])
            self.assertEqual(spec["quote"], control["quote"])
            self.assertEqual(spec["prelude"], control["prelude"])
            if spec["body"]:
                self.assertEqual(len(spec["body"]), len(control["body"]))
                self.assertEqual(sum(a != b for a, b in zip(spec["body"], control["body"])), 1)
            else:
                self.assertEqual(control["body"], "0")
        use_counts = Counter(r["control"] for r in self.repairs.values())
        self.assertEqual(sorted(use_counts.values()), [1,1,1,1,2,5,5,8])
        for rule, variants in CONTROLS.items():
            sources = [self.source(generated.identifier(rule, v)) for v in variants.split()]
            self.assertEqual(len(sources), len(set(sources)))

    def test_exact_token_and_character_columns_are_source_bound_not_fictional_matchers(self):
        for name, spec in self.specs.items():
            anchor = spec["source_anchor"]
            line = self.source(name).splitlines()[anchor["line"]-1]
            self.assertEqual(line[anchor["token_first_column"]-1:anchor["token_last_column"]], spec["literal"])
            for position, column in zip(anchor["offending_body_positions"], anchor["offending_columns"]):
                self.assertEqual(line[column-1], spec["body"][position-1])
            if not spec["body"]:
                self.assertEqual(line[anchor["empty_body_insertion_column"]-1], spec["quote"])
            if name in self.repairs:
                predicate = self.cases[name].fixture.expectation.diagnostic
                self.assertEqual(predicate["file"], "source.f90")
                self.assertEqual(predicate["line"], anchor["line"])
                self.assertNotIn("column", predicate)
                self.assertNotIn("end_line", predicate)

    def test_all_predicate_report_wrong_cause_location_nonfatal_and_failure_probes(self):
        counts = Counter()
        for probe in predicate_probes(self.cases):
            actual = judge(self.cases[probe["case"]], **probe["arguments"])
            self.assertEqual(actual, probe["expected"], probe)
            counts[probe["category"]] += 1
        self.assertGreater(counts["qualified-report-no-fatal-policy"], 100)
        self.assertGreater(counts["wrong-role-property-or-generic-recovery"], 500)
        self.assertEqual(counts["native-internal-veto"], 72)

    def test_other_body_characters_or_properties_cannot_supply_the_cause(self):
        for name in self.repairs:
            spec = self.specs[name]
            for family in ("lfortran", "gfortran", "flang"):
                if spec["body"]:
                    if spec["lexical_conditions"]["nondigit_positions"]:
                        wrong = f"Invalid digit '2' in a {spec['radix']} BOZ literal"
                    else:
                        wrong = f"Invalid character 'A' in a {spec['radix']} BOZ literal"
                    self.assertEqual(judge(self.cases[name], wrong, family, exclusions=False), "fail")
                wrong = f"A {spec['radix']} BOZ literal has an unsupported result kind"
                self.assertEqual(judge(self.cases[name], wrong, family, exclusions=False), "fail")
        for rule, original, wrong_body, digit, prefix in (
            ("C7117", "1021", "2011", "2", "b"), ("C7118", "1781", "1871", "8", "o")):
            case = self.cases[generated.identifier(rule, "interior_digit", True)]
            self.assertEqual(self.specs[case.name]["body"], original)
            for family in ("lfortran", "gfortran", "flang"):
                message = f"Invalid digit ('{digit}') in BOZ literal '{prefix}\"{wrong_body}\"'"
                self.assertEqual(judge(case, message, family, exclusions=False), "fail")

    def test_generic_native_string_and_DATA_recovery_stays_uncredited(self):
        for name in self.repairs:
            case, spec = self.cases[name], self.specs[name]
            displayed = spec["quote"] + spec["body"] + spec["quote"]
            messages = [f"Token '{displayed}' (of type 'string') is unexpected here",
                        "expected '/'", "Illegal character in BOZ constant at (1)"]
            for family in ("lfortran", "gfortran", "flang"):
                for message in messages:
                    self.assertEqual(judge(case, message, family, exclusions=False), "fail")

    def test_nonfatal_warning_admission_requires_a_bound_exact_family_message(self):
        for name in self.repairs:
            case = self.cases[name]
            predicate = case.fixture.expectation.diagnostic
            allowances = predicate.get("allow_nonfatal", [])
            for family in ("lfortran", "gfortran", "flang"):
                message = predicate["contains_any"][0]
                permitted = any(a["compiler"] == family and a["severity"] == "warning"
                                and message in a.get("equals_any", []) for a in allowances)
                self.assertEqual(judge(case, message, family, code=0, severity="warning"),
                                 "pass" if permitted else "fail")
            for allowance in allowances:
                self.assertEqual(set(allowance), {"compiler", "severity", "equals_any"})
                for message in allowance["equals_any"]:
                    self.assertIn(message, predicate["contains_any"])
                    self.assertEqual(judge(case, message, allowance["compiler"], code=0,
                                           severity=allowance["severity"]), "pass")

    def test_all_unselected_facets_stay_pending_and_views_preserve_administration(self):
        self.assertEqual(len(self.catalogue["requirements"]), 9)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 64)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 52)
        for r in self.catalogue["requirements"]:
            covered = set(generated.ELIGIBLE.get(r["id"], []))
            self.assertEqual(set(r["pending"]), set(r["facets"]) - covered)
            if r["id"] not in generated.ELIGIBLE:
                self.assertEqual(set(r["pending"]), set(r["facets"]))
        self.assertEqual(generated.synced_catalogue(self.catalogue, self.specs), self.catalogue)
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs, self.repairs))
        self.assertIn("This generator does not register the catalogue", view)
        self.assertIn("Subsequent main registration and adjudication belong to the coordinator", view)
        native = Registry(ROOT)
        native.catalogues = {"7.7": self.catalogue}
        native.render()
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split("## Reproduction and remaining gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 52)
        for r in self.catalogue["requirements"]:
            for facet, plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed.update(review_state="reviewed", review_rationale="Synthetic in-memory transition, not an approval.")
        native = Registry(ROOT)
        native.catalogues["7.7"] = reviewed
        reviewed["review_fingerprint"] = native.catalogue_fingerprint("7.7")
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs, self.repairs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs, self.repairs))

    def test_old_case_registration_and_shared_parameter_sources_are_preserved(self):
        old = Registry(ROOT)
        local_rules = {r["id"] for r in old.catalogues["7.7"]["requirements"]}
        del old.catalogues["7.7"]
        del old.accounting["7.7"]
        old.index["catalogues"].remove(generated.CATALOGUE)
        for rule in local_rules:
            del old.requirements[rule]
            del old.requirement_sections[rule]
        prior = [c for c in self.all_cases if c.rule not in local_rules]
        self.assertGreaterEqual(len(prior), 1937)
        for case in prior:
            self.assertEqual(case.fingerprint(old), case.fingerprint(self.registry), case.name)
        shared = parameters.build_corpus()
        self.assertEqual((len(shared.cases), len(shared.files)), (66, 105))
        self.assertFalse(set(shared.files) & set(self.files))
        for path, content in shared.files.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
