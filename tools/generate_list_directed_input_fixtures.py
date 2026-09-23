#!/usr/bin/env python3
"""List-directed input runtime fixtures for Fortran 2023 13.10.2-13.10.3.2."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ("13.10.2", "13.10.3.1", "13.10.3.2")
CATALOGUES = {
    "13.10.2": "doc/catalogues/values_and_value_separators_13_10_2.json",
    "13.10.3.1": "doc/catalogues/list_directed_input_forms_13_10_3_1.json",
    "13.10.3.2": "doc/catalogues/null_values_13_10_3_2.json",
}
VIEWS = {
    "13.10.2": "doc/fortran_2023_13_10_2.md",
    "13.10.3.1": "doc/fortran_2023_13_10_3_1.md",
    "13.10.3.2": "doc/fortran_2023_13_10_3_2.md",
}
SUMMARY_BEGIN = "<!-- BEGIN LIST-DIRECTED INPUT FIXTURES -->"
SUMMARY_END = "<!-- END LIST-DIRECTED INPUT FIXTURES -->"

VARIANTS = {
    "record_end_as_blank": ("S13.10.2-001", "record-end-as-blank"),
    "multiple_blanks_collapse": ("S13.10.2-001", "multiple-blanks-collapse"),
    "character_constants_preserve_blanks": ("S13.10.2-001", "character-constants-preserve-blanks"),
    "repeat_constant": ("S13.10.2-002", "repeat-constant"),
    "repeat_null": ("S13.10.2-002", "repeat-null"),
    "comma_separator": ("S13.10.2-003", "comma-separator"),
    "edit_compatible_forms": ("S13.10.3.1-001", "edit-compatible-forms"),
    "blanks_not_zeros": ("S13.10.3.1-001", "blanks-not-zeros"),
    "repeat_undelimited_character": ("S13.10.3.1-002", "repeat-undelimited-character"),
    "repeat_literal_otherwise": ("S13.10.3.1-002", "repeat-literal-otherwise"),
    "character_delimited_sequence": ("S13.10.3.1-007", "character-delimited-sequence"),
    "character_blank_padding": ("S13.10.3.1-009", "character-blank-padding"),
    "repeat_null_form": ("S13.10.3.2-001", "repeat-null-form"),
    "empty_between_separators": ("S13.10.3.2-001", "empty-between-separators"),
    "leading_empty_first_record": ("S13.10.3.2-001", "leading-empty-first-record"),
    "null_preserves_value": ("S13.10.3.2-002", "null-preserves-value"),
    "slash_terminates": ("S13.10.3.2-003", "slash-terminates"),
    "slash_null_supplies_remaining": ("S13.10.3.2-003", "slash-null-supplies-remaining"),
}
FACETS_BY_RULE = {}
for _variant, (_rule, _facet) in VARIANTS.items():
    FACETS_BY_RULE.setdefault(_rule, []).append(_facet)

POSITIVE_CONTROL_RULES = {"S13.10.2-002", "S13.10.3.1-001", "S13.10.3.2-002"}

REMAINING_PENDING = {
    "S13.10.2-001": set(),
    "S13.10.2-002": {"constant-value", "no-kind-parameters", "no-embedded-blanks-in-repeat-form"},
    "S13.10.2-003": {"semicolon-separator-in-comma-mode", "slash-separator", "blank-separator"},
    "S13.10.3.1-001": {"unacceptable-form-error", "embedded-blanks-limited"},
    "S13.10.3.1-002": set(),
    "S13.10.3.1-003": {"integer-i-editing"},
    "S13.10.3.1-004": {"real-decimal-field", "real-no-decimal-fraction-digits"},
    "S13.10.3.1-005": {"complex-point-comma", "complex-comma-mode-semicolon", "complex-real-imaginary-order", "complex-record-end-allowances"},
    "S13.10.3.1-006": {"logical-separator-excluded"},
    "S13.10.3.1-007": {"character-continuation-no-record-blank", "doubled-delimiter-not-split", "separator-characters-in-delimited-character"},
    "S13.10.3.1-008": {"undelimited-character-admitted", "undelimited-termination", "undelimited-quotes-not-doubled", "undelimited-repeat-prefix-excluded"},
    "S13.10.3.1-009": {"character-truncation"},
    "S13.10.3.2-001": set(),
    "S13.10.3.2-002": {"single-null-entire-complex", "null-not-complex-part"},
    "S13.10.3.2-003": {"slash-ignores-rest"},
}

COMPLETIONS = {name: "LIST DIRECTED INPUT " + name.upper().replace("_", " ") + " OK\n" for name in VARIANTS}

ORACLE_PREFIXES = {
    "S13.10.2-001": "S13.10.2-001 list-directed record normalization runtime fixtures: ",
    "S13.10.2-002": "S13.10.2-002 list-directed repeated value runtime fixtures: ",
    "S13.10.2-003": "S13.10.2-003 list-directed comma separator runtime fixture: ",
    "S13.10.3.1-001": "S13.10.3.1-001 list-directed type-form runtime controls: ",
    "S13.10.3.1-002": "S13.10.3.1-002 r*c character-vs-literal runtime fixtures: ",
    "S13.10.3.1-007": "S13.10.3.1-007 delimited character runtime fixture: ",
    "S13.10.3.1-009": "S13.10.3.1-009 character padding runtime fixture: ",
    "S13.10.3.2-001": "S13.10.3.2-001 null form runtime fixtures: ",
    "S13.10.3.2-002": "S13.10.3.2-002 null-preservation runtime control: ",
    "S13.10.3.2-003": "S13.10.3.2-003 slash termination runtime fixtures: ",
}
LIMIT_PREFIXES = {
    rule: prefix.replace(" runtime fixtures: ", " fixture boundaries: ").replace(
        " runtime fixture: ", " fixture boundaries: ")
    for rule, prefix in ORACLE_PREFIXES.items()
}
ORACLES = {
    "S13.10.2-001": ORACLE_PREFIXES["S13.10.2-001"] + (
        "three complete internal READ programs use exact INTEGER and default CHARACTER observations. "
        "The two-record internal file ['1','2'] reads integers 1 then 2 because the record end acts as a blank; "
        "the single record '1   2' reads 1 then 2 because a run of blanks is one blank separator; and the record "
        "\"'A  B'\" reads CHARACTER(LEN=4) value 'A  B', with LEN checked explicitly so blank padding cannot hide "
        "lost embedded blanks. Feature mutations remove separators, reorder values, or alter the READ item count."
    ),
    "S13.10.2-002": ORACLE_PREFIXES["S13.10.2-002"] + (
        "two complete positive-control programs exercise r*c and r* input forms. The repeat-constant case reads "
        "'11,3*7,29' into five integers and requires [11,7,7,7,29], making a 3*7 to 2*7 mutation and value reordering "
        "visible through distinct surrounding values. The repeat-null case initializes [101,202,303], reads '2*' into "
        "the first two effective items, and requires all sentinels to remain [101,202,303]. No sentinel is zero."
    ),
    "S13.10.2-003": ORACLE_PREFIXES["S13.10.2-003"] + (
        "one complete run/effect program reads record '1, 2' into two integers and requires 1 then 2. "
        "A separator-removal mutation changes the record to '12', a value-reordering mutation changes it to '2, 1', "
        "and a READ-list mutation removes the second item; each is expected to fail."
    ),
    "S13.10.3.1-001": ORACLE_PREFIXES["S13.10.3.1-001"] + (
        "two complete positive-control programs use exact type-appropriate forms. The edit-compatible fixture reads "
        "'42' into an INTEGER and '.TRUE.' into a LOGICAL in separate internal READ controls, requiring 42 and true. "
        "The blanks-not-zeros fixture reads '1 2' into two integers and requires 1 then 2, which would fail if the blank "
        "were treated as a zero inside one integer constant."
    ),
    "S13.10.3.1-002": ORACLE_PREFIXES["S13.10.3.1-002"] + (
        "two complete run/effect programs use r*c records. '2*ab' is read into CHARACTER(LEN=2) array elements and "
        "requires both exact values 'ab' with LEN 2 checks; '5,2*7,19' is read into four integers and requires "
        "[5,7,7,19], proving that for integer effective items c is interpreted as a literal constant rather than as "
        "character text. Distinct surrounding values make repeat-count and ordering mutations fail."
    ),
    "S13.10.3.1-007": ORACLE_PREFIXES["S13.10.3.1-007"] + (
        "one complete run/effect program reads record \"'A,B/;'\" into CHARACTER(LEN=5), explicitly checks LEN==5, "
        "and compares against the equal-length literal 'A,B/;'. Thus comma, slash and semicolon are data characters "
        "inside the delimited character sequence, not value separators."
    ),
    "S13.10.3.1-009": ORACLE_PREFIXES["S13.10.3.1-009"] + (
        "one complete run/effect program reads record \"'AB'\" into CHARACTER(LEN=4), explicitly checks LEN==4, "
        "and compares against the equal-length literal 'AB  ', deriving the two trailing blanks from len-w = 2."
    ),
    "S13.10.3.2-001": ORACLE_PREFIXES["S13.10.3.2-001"] + (
        "three complete run/effect programs initialize nonzero integer sentinels before internal READ. Record '1*' "
        "leaves x at sentinel 907; record '10,,30' changes only positions 1 and 3 of [111,222,333] to [10,222,30]; "
        "and record ',9' leaves x at 707 while assigning y=9. The unchanged values are observable only because every "
        "receiving variable started with a distinctive nonzero sentinel."
    ),
    "S13.10.3.2-002": ORACLE_PREFIXES["S13.10.3.2-002"] + (
        "one complete positive-control program initializes x=717 and y=818, reads record ',44' into x,y, and requires "
        "x to remain 717 while y becomes 44. The first empty field is the null value; the second item proves that the "
        "READ did consume the following value."
    ),
    "S13.10.3.2-003": ORACLE_PREFIXES["S13.10.3.2-003"] + (
        "two complete run/effect programs initialize nonzero sentinels before slash input. Record '1 / 99' assigns "
        "x=1 and leaves y=-802, proving termination after the previous value and null-supply for the remaining item. "
        "Record '1 /' read into [501,602,703] yields [1,602,703], proving additional effective items are left unchanged. "
        "Deleting the slash makes the trailing value visible or causes a count failure."
    ),
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + "These fixtures are bounded internal list-directed input observations only. They do not assert list-directed output spelling, field widths, record wrapping, DECIMAL='COMMA', DELIM=, input-error IOSTAT mechanics, processor diagnostics, nondefault character kinds, enum input, real/complex approximations, defined I/O, files, external units, coarrays, or universal compiler conformance. Remaining facets stay pending with their source-authored plans."
    for rule in ORACLE_PREFIXES
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__list_directed_input_" + variant


def fstr(text):
    if '"' in text:
        raise ValueError("test records deliberately avoid double quotes for simple source quoting")
    return '"' + text + '"'


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facet = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.observations = []
        self.probes = []
        self.omissions = []
        self.input_mutations = []
        self.feature_mutations = []
        self.reverse_mutations = []
        self.records = []
        self.sentinels = []
        self.read_lists = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def add_record(self, lhs, record, *, replacement, mutation_id, category="record-text"):
        line = f"  {lhs} = {fstr(record)}\n"
        start = len(self.text) + line.index(record)
        self.add(line)
        item = dict(id=mutation_id, kind="input", category=category, expected=record, replacement=replacement,
                    span=[start, start + len(record)], line=self.text[:start].count("\n") + 1,
                    mutation="input-record-text")
        self.input_mutations.append(item)
        self.records.append(dict(lhs=lhs, text=record, mutation=item))
        return item

    def add_record_array(self, lhs, records, *, replacement, mutation_id):
        joined = ", ".join(fstr(row) for row in records)
        line = f"  {lhs} = [character(len={len(records[0])}) :: {joined}]\n"
        start = len(self.text) + line.index(fstr(records[0])) + 1
        self.add(line)
        item = dict(id=mutation_id, kind="input", category="record-array-text", expected=records[0],
                    replacement=replacement, span=[start, start + len(records[0])],
                    line=self.text[:start].count("\n") + 1, mutation="input-record-text")
        self.input_mutations.append(item)
        self.records.append(dict(lhs=lhs, text=list(records), mutation=item))
        return item

    def add_read(self, source, items, *, replacement=None):
        line = f"  read({source},*) {items}\n"
        start = len(self.text) + len(f"  read({source},*) ")
        self.add(line)
        if replacement is None:
            replacement = items + ", stray" if "," not in items else items.rsplit(",", 1)[0]
        item = dict(id="read-list-item-count", kind="feature", category="read-list-cardinality",
                    expected=items, replacement=replacement, span=[start, start + len(items)],
                    line=self.text[:start].count("\n") + 1, mutation="read-list-cardinality")
        self.feature_mutations.append(item)
        self.read_lists.append(item)
        return item

    def feature_replace(self, expected, replacement, mutation_id, category):
        start = self.text.index(expected)
        item = dict(id=mutation_id, kind="feature", category=category, expected=expected, replacement=replacement,
                    span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
                    mutation="feature-under-test-substitution")
        self.feature_mutations.append(item)
        return item

    def guard_int(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"LDI:{self.variant}:{name}"
        guard = dict(id=name, guard_id=name, kind="guard", category=category, expression=expression,
                     expected=expected, replacement=replacement, span=[start, start + len(expected)],
                     line=self.text.count("\n") + 1, counter=counter, activation=None,
                     mutation="guard-literal-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n" + "    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter}={counter}+1\n")
            self.observations.append(guard)
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        return guard

    def guard_logical(self, name, expression, expected, replacement=".false.", *, category="logical"):
        expected_text = ".true." if expected else ".false."
        replacement_text = replacement
        block_start = len(self.text)
        prefix = f"  if ({expression} .neqv. "
        start = block_start + len(prefix)
        token = f"LDI:{self.variant}:{name}"
        guard = dict(id=name, guard_id=name, kind="guard", category=category, expression=expression,
                     expected=expected_text, replacement=replacement_text, span=[start, start + len(expected_text)],
                     line=self.text.count("\n") + 1, counter="checks", activation=None,
                     mutation="guard-logical-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expected_text + ") then\n" + f"    write(*,'(a)') '{token}'\n" + "    error stop\n  end if\n")
        self.add("  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        return guard

    def guard_char(self, name, expression, expected, replacement, *, length_expr=None):
        if length_expr:
            self.guard_int(name + "-len", f"len({length_expr})", len(expected), len(expected) + 1, category="length")
        block_start = len(self.text)
        literal = "'" + expected + "'"
        repl = "'" + replacement + "'"
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"LDI:{self.variant}:{name}"
        guard = dict(id=name, guard_id=name, kind="guard", category="character", expression=expression,
                     expected=literal, replacement=repl, span=[start, start + len(literal)],
                     line=self.text.count("\n") + 1, counter="checks", activation=None,
                     mutation="guard-character-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + literal + ") then\n" + f"    write(*,'(a)') '{token}'\n" + "    error stop\n  end if\n")
        self.add("  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        return guard

    def finish(self):
        total = self.guard_int("check-total", "checks", len(self.observations), len(self.observations) + 1,
                               category="completion", counter=None)
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        completion = dict(id="completion-output", guard_id="completion-output", kind="output", category="completion",
                          expected=literal, replacement=literal.replace(" OK", " BAD"),
                          span=[start, start + len(literal)], line=self.text.count("\n") + 1, counter=None,
                          activation=None, mutation="completion-literal")
        completion["block_span"] = self.add(prefix + literal + "'\n")
        self.guards.append(completion)
        self.probes.append(dict(completion))
        self.add(f"end program list_directed_input_{self.variant}\n")
        start, end = completion["block_span"]
        self.omissions.append(dict(id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
                                   span=[start, end], expected=self.text[start:end], replacement="",
                                   line=self.text[:start].count("\n") + 1,
                                   mutation="completion-statement-omission", failure_stdout=""))
        plans = [("omit-observation-" + guard["id"], guard["block_span"], total) for guard in self.observations]
        if len(self.observations) > 1:
            plans.append(("omit-all-observations", [self.observations[0]["block_span"][0], self.observations[-1]["block_span"][1]], total))
        for name, span, failure in plans:
            start, end = span
            self.omissions.append(dict(id=name, guard_id=failure["id"], kind="guard", category="omission",
                                       span=span, expected=self.text[start:end], replacement="",
                                       line=self.text[:start].count("\n") + 1, guard_line=failure["line"],
                                       mutation="whole-program-omission", failure_token=failure["failure_token"],
                                       failure_stdout=failure["failure_stdout"]))


def begin_program(p, declarations):
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")
    p.add("! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.\n")
    p.add(f"program list_directed_input_{p.variant}\n  implicit none\n  integer :: checks, stray\n")
    for line in declarations:
        p.add("  " + line + "\n")
    p.add("  checks=0\n  stray=-909\n")


def program(variant):
    p = Program(variant)
    notes = []
    if variant == "record_end_as_blank":
        begin_program(p, ["character(len=1) :: recs(2)", "integer :: a, b"])
        p.add("  a=-101\n  b=-202\n")
        p.sentinels += ["a=-101", "b=-202"]
        p.add_record_array("recs", ["1", "2"], replacement="9", mutation_id="record-end-first-value-changed")
        p.add_read("recs", "a, b")
        p.feature_replace("[character(len=1) :: \"1\", \"2\"]", "[character(len=1) :: \"2\", \"1\"]", "reorder-record-values", "value-order")
        p.guard_int("first-value", "a", 1, 2)
        p.guard_int("second-value", "b", 2, 1)
        notes = ["records ['1','2']", "record end acts as blank separator", "result a=1,b=2"]
    elif variant == "multiple_blanks_collapse":
        begin_program(p, ["character(len=5) :: rec", "integer :: a, b"])
        p.add("  a=-111\n  b=-222\n")
        p.sentinels += ["a=-111", "b=-222"]
        p.add_record("rec", "1   2", replacement="12", mutation_id="remove-blank-separator")
        p.add_read("rec", "a, b")
        p.input_mutations.append(dict(id="reorder-blank-separated-values", kind="input", category="value-order", expected="1   2", replacement="2   1", span=p.input_mutations[-1]["span"], line=p.input_mutations[-1]["line"], mutation="input-record-text"))
        p.guard_int("first-value", "a", 1, 2)
        p.guard_int("second-value", "b", 2, 1)
        notes = ["record '1   2'", "consecutive blanks collapse to one blank separator", "result a=1,b=2"]
    elif variant == "character_constants_preserve_blanks":
        begin_program(p, ["character(len=6) :: rec", "character(len=4) :: text"])
        p.add("  text='ZZZZ'\n")
        p.sentinels.append("text='ZZZZ'")
        p.add_record("rec", "'A  B'", replacement="'A B'", mutation_id="remove-embedded-character-blank")
        p.add_read("rec", "text")
        p.guard_char("preserved-blanks", "text", "A  B", "A B ", length_expr="text")
        notes = ["record \"'A  B'\"", "blanks are within a character constant", "result text='A  B' and LEN(text)=4"]
    elif variant == "repeat_constant":
        begin_program(p, ["character(len=9) :: rec", "integer :: x(5)"])
        p.add("  x=[101,202,303,404,505]\n")
        p.sentinels.append("x=[101,202,303,404,505]")
        p.add_record("rec", "11,3*7,29", replacement="11,2*7,29", mutation_id="change-3star7-to-2star7", category="repeat-count")
        p.add_read("rec", "x")
        p.feature_replace("11,3*7,29", "29,3*7,11", "reorder-repeat-surrounding-values", "value-order")
        for i, expected in enumerate([11, 7, 7, 7, 29], 1):
            p.guard_int(f"x{i}", f"x({i})", expected, expected + 1)
        notes = ["record '11,3*7,29'", "3*7 is three successive integer constants", "result x=[11,7,7,7,29]"]
    elif variant == "repeat_null":
        begin_program(p, ["character(len=3) :: rec", "integer :: x(3)"])
        p.add("  x=[101,202,303]\n")
        p.sentinels.append("x=[101,202,303]")
        p.add_record("rec", "2*", replacement="1*", mutation_id="change-repeat-null-count", category="repeat-null-count")
        p.add_read("rec", "x(1), x(2)", replacement="x(1), x(2), stray")
        p.feature_replace("2*", "2*5", "turn-repeat-null-into-repeat-value", "null-removal")
        for i, expected in enumerate([101, 202, 303], 1):
            p.guard_int(f"sentinel-{i}", f"x({i})", expected, expected + 1, category="sentinel")
        p.reverse_mutations.append(dict(id="reverse-repeat-null-zero-sentinel", kind="reverse", category="sentinel", replacements=[
            dict(expected="x=[101,202,303]", replacement="x=[101,0,303]"),
            dict(expected="x(2) /= 202", replacement="x(2) /= 0")]))
        notes = ["record '2*' read into x(1),x(2)", "r* supplies two null values", "result x=[101,202,303] unchanged"]
    elif variant == "comma_separator":
        begin_program(p, ["character(len=4) :: rec", "integer :: a, b"])
        p.add("  a=-301\n  b=-302\n")
        p.sentinels += ["a=-301", "b=-302"]
        p.add_record("rec", "1, 2", replacement="12", mutation_id="remove-comma-separator")
        p.add_read("rec", "a, b")
        p.feature_replace("1, 2", "2, 1", "reorder-comma-values", "value-order")
        p.guard_int("first", "a", 1, 2)
        p.guard_int("second", "b", 2, 1)
        notes = ["record '1, 2'", "comma is a value separator", "result a=1,b=2"]
    elif variant == "edit_compatible_forms":
        begin_program(p, ["character(len=6) :: rec_i, rec_l", "integer :: n", "logical :: flag"])
        p.add("  n=-404\n  flag=.false.\n")
        p.sentinels += ["n=-404", "flag=.false."]
        p.add_record("rec_i", "42", replacement="24", mutation_id="change-integer-input")
        p.add_read("rec_i", "n")
        p.add_record("rec_l", ".TRUE.", replacement=".FALSE.", mutation_id="change-logical-input")
        p.add_read("rec_l", "flag")
        p.guard_int("integer-value", "n", 42, 24)
        p.guard_logical("logical-value", "flag", True)
        notes = ["records '42' and '.TRUE.' in separate READs", "integer form gives n=42", "logical form gives flag=.true."]
    elif variant == "blanks_not_zeros":
        begin_program(p, ["character(len=3) :: rec", "integer :: a, b"])
        p.add("  a=-501\n  b=-502\n")
        p.sentinels += ["a=-501", "b=-502"]
        p.add_record("rec", "1 2", replacement="12", mutation_id="remove-blank-separator")
        p.add_read("rec", "a, b")
        p.feature_replace("1 2", "2 1", "reorder-blank-values", "value-order")
        p.guard_int("first", "a", 1, 12)
        p.guard_int("second", "b", 2, 1)
        notes = ["record '1 2'", "blank separates values and is never zero", "result a=1,b=2"]
    elif variant == "repeat_undelimited_character":
        begin_program(p, ["character(len=4) :: rec", "character(len=2) :: words(2)"])
        p.add("  words=[character(len=2) :: 'QQ','RR']\n")
        p.sentinels.append("words=['QQ','RR']")
        p.add_record("rec", "2*ab", replacement="1*ab", mutation_id="change-character-repeat-count", category="repeat-count")
        p.add_read("rec", "words")
        p.guard_char("word1", "words(1)", "ab", "QQ", length_expr="words(1)")
        p.guard_char("word2", "words(2)", "ab", "RR", length_expr="words(2)")
        notes = ["record '2*ab'", "first effective item is character so c is undelimited character", "result words=['ab','ab']"]
    elif variant == "repeat_literal_otherwise":
        begin_program(p, ["character(len=8) :: rec", "integer :: x(4)"])
        p.add("  x=[501,502,503,504]\n")
        p.sentinels.append("x=[501,502,503,504]")
        p.add_record("rec", "5,2*7,19", replacement="5,1*7,19", mutation_id="change-integer-repeat-count", category="repeat-count")
        p.add_read("rec", "x")
        p.feature_replace("5,2*7,19", "19,2*7,5", "reorder-repeat-literal-values", "value-order")
        for i, expected in enumerate([5, 7, 7, 19], 1):
            p.guard_int(f"x{i}", f"x({i})", expected, expected + 1)
        notes = ["record '5,2*7,19'", "integer effective item interprets c as literal constant", "result x=[5,7,7,19]"]
    elif variant == "character_delimited_sequence":
        begin_program(p, ["character(len=7) :: rec", "character(len=5) :: text"])
        p.add("  text='ZZZZZ'\n")
        p.sentinels.append("text='ZZZZZ'")
        p.add_record("rec", "'A,B/;'", replacement="'A B ;'", mutation_id="change-delimited-character-data")
        p.add_read("rec", "text")
        p.guard_char("delimited-value", "text", "A,B/;", "A B ;", length_expr="text")
        notes = ["record \"'A,B/;'\"", "comma, slash and semicolon are characters inside delimiters", "result text='A,B/;' LEN=5"]
    elif variant == "character_blank_padding":
        begin_program(p, ["character(len=4) :: rec", "character(len=4) :: text"])
        p.add("  text='ZZZZ'\n")
        p.sentinels.append("text='ZZZZ'")
        p.add_record("rec", "'AB'", replacement="'ABCD'", mutation_id="remove-blank-padding-need")
        p.add_read("rec", "text")
        p.guard_char("padded-value", "text", "AB  ", "ABCD", length_expr="text")
        notes = ["record \"'AB'\"", "len=4,w=2 so two blanks fill the effective item", "result text='AB  ' LEN=4"]
    elif variant == "repeat_null_form":
        begin_program(p, ["character(len=3) :: rec", "integer :: x"])
        p.add("  x=907\n")
        p.sentinels.append("x=907")
        p.add_record("rec", "1*", replacement="1*0", mutation_id="turn-rstar-null-into-zero", category="null-removal")
        p.add_read("rec", "x")
        p.guard_int("sentinel-preserved", "x", 907, 0, category="sentinel")
        p.reverse_mutations.append(dict(id="reverse-repeat-null-form-zero-sentinel", kind="reverse", category="sentinel", replacements=[
            dict(expected="x=907", replacement="x=0"), dict(expected="x /= 907", replacement="x /= 0")]))
        notes = ["record '1*'", "r* form supplies one null value", "result x remains sentinel 907"]
    elif variant == "empty_between_separators":
        begin_program(p, ["character(len=6) :: rec", "integer :: x(3)"])
        p.add("  x=[111,222,333]\n")
        p.sentinels.append("x=[111,222,333]")
        p.add_record("rec", "10,,30", replacement="10,30", mutation_id="remove-empty-null-field", category="null-removal")
        p.add_read("rec", "x")
        p.feature_replace("10,,30", "30,,10", "reorder-around-null", "value-order")
        for i, expected in enumerate([10, 222, 30], 1):
            p.guard_int(f"x{i}", f"x({i})", expected, expected + 1 if expected != 222 else 0,
                        category="sentinel" if i == 2 else "value")
        p.reverse_mutations.append(dict(id="reverse-empty-between-zero-sentinel", kind="reverse", category="sentinel", replacements=[
            dict(expected="x=[111,222,333]", replacement="x=[111,0,333]"), dict(expected="x(2) /= 222", replacement="x(2) /= 0")]))
        notes = ["record '10,,30'", "no characters between separators supplies a null for x(2)", "result x=[10,222,30]"]
    elif variant == "leading_empty_first_record":
        begin_program(p, ["character(len=2) :: rec", "integer :: x, y"])
        p.add("  x=707\n  y=808\n")
        p.sentinels += ["x=707", "y=808"]
        p.add_record("rec", ",9", replacement="9", mutation_id="remove-leading-null", category="null-removal")
        p.add_read("rec", "x, y", replacement="x")
        p.guard_int("x-sentinel", "x", 707, 9, category="sentinel")
        p.guard_int("y-value", "y", 9, 808)
        notes = ["record ',9'", "no characters before first separator in first record supplies null for x", "result x=707,y=9"]
    elif variant == "null_preserves_value":
        begin_program(p, ["character(len=3) :: rec", "integer :: x, y"])
        p.add("  x=717\n  y=818\n")
        p.sentinels += ["x=717", "y=818"]
        p.add_record("rec", ",44", replacement="44", mutation_id="remove-null-before-value", category="null-removal")
        p.add_read("rec", "x, y", replacement="x")
        p.guard_int("x-preserved", "x", 717, 44, category="sentinel")
        p.guard_int("y-value", "y", 44, 818)
        p.reverse_mutations.append(dict(id="reverse-null-preserves-zero-sentinel", kind="reverse", category="sentinel", replacements=[
            dict(expected="x=717", replacement="x=0"), dict(expected="x /= 717", replacement="x /= 0")]))
        notes = ["record ',44'", "null has no effect on next effective item definition status", "result x=717,y=44"]
    elif variant == "slash_terminates":
        begin_program(p, ["character(len=6) :: rec", "integer :: x, y"])
        p.add("  x=-701\n  y=-802\n")
        p.sentinels += ["x=-701", "y=-802"]
        p.add_record("rec", "1 / 99", replacement="1 99", mutation_id="delete-slash-separator", category="slash-deletion")
        p.add_read("rec", "x, y", replacement="y")
        p.feature_replace("1 / 99", "99 / 1", "reorder-before-slash-value", "value-order")
        p.guard_int("x-value", "x", 1, 99)
        p.guard_int("y-sentinel", "y", -802, 99, category="sentinel")
        notes = ["record '1 / 99'", "slash terminates after transferring previous value", "result x=1,y=-802 unchanged"]
    elif variant == "slash_null_supplies_remaining":
        begin_program(p, ["character(len=3) :: rec", "integer :: x(3)"])
        p.add("  x=[501,602,703]\n")
        p.sentinels.append("x=[501,602,703]")
        p.add_record("rec", "1 /", replacement="1 8", mutation_id="delete-slash-before-remaining", category="slash-deletion")
        p.add_read("rec", "x", replacement="x(2)")
        for i, expected in enumerate([1, 602, 703], 1):
            p.guard_int(f"x{i}", f"x({i})", expected, expected + 1 if i == 1 else 0,
                        category="sentinel" if i > 1 else "value")
        p.reverse_mutations.append(dict(id="reverse-slash-null-zero-sentinel", kind="reverse", category="sentinel", replacements=[
            dict(expected="x=[501,602,703]", replacement="x=[501,0,703]"), dict(expected="x(2) /= 602", replacement="x(2) /= 0")]))
        notes = ["record '1 /'", "slash supplies null values for remaining effective items", "result x=[1,602,703]"]
    else:
        raise ValueError("unknown list-directed input variant")
    p.finish()
    raw = p.text.encode("ascii")
    for mutation in all_mutations_from_program(p):
        start, end = mutation["span"]
        if raw[start:end].decode("ascii") != mutation["expected"]:
            raise ValueError(f"mutation span lost parent binding: {variant} {mutation['id']}")
    return dict(id=identifier(variant), variant=variant, rule=p.rule, facets=[p.facet],
                evidence="positive-control" if p.rule in POSITIVE_CONTROL_RULES else "effect",
                standard="f2023", phase="run", source=p.text, source_sha256=sha(raw),
                completion=COMPLETIONS[variant], guards=p.guards, probes=p.probes,
                omissions=p.omissions, input_mutations=p.input_mutations, feature_mutations=p.feature_mutations,
                reverse_mutations=p.reverse_mutations, observations=p.observations,
                expected_counts=dict(checks=len(p.observations)), records=p.records,
                sentinels=p.sentinels, read_lists=p.read_lists, notes=notes)


def all_mutations_from_program(p):
    return p.probes + p.omissions + p.input_mutations + p.feature_mutations


def all_mutations(spec):
    return spec["probes"] + spec["omissions"] + spec["input_mutations"] + spec["feature_mutations"]


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def mutated_source(spec, mutation):
    if mutation.get("kind") == "reverse":
        text = spec["source"]
        for item in mutation["replacements"]:
            if item["expected"] not in text:
                raise ValueError("reverse mutation token not found")
            text = text.replace(item["expected"], item["replacement"], 1)
        return text.encode("ascii")
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("list_directed_input_" + spec["variant"])
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected list-directed input facets changed for " + rule)
        for facet in facets:
            owner.setdefault("pending", {}).pop(facet, None)
        if rule in REMAINING_PENDING and set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        if rule in ORACLES:
            owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
            owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEWS[section]).read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    old = "This source packet records source accounting and pending plans only, not fixture approval."
    new = ("This source packet records source accounting. Selected list-directed input fixtures now supply "
           "executable standard-oracle observations and mutation plans; fixture approval remains separate.")
    before = before.replace(old, new)
    summary = (SUMMARY_BEGIN + "\n"
               "## List-directed input runtime observations\n\n"
               "Eighteen complete internal READ fixtures cover selected values, separators, input forms, null values "
               "and slash termination from 13.10.2, 13.10.3.1 and 13.10.3.2. Every receiving variable is initialized "
               "to a distinctive nonzero sentinel before READ; character fixtures assert LEN explicitly before equal-length "
               "value comparisons. The generator permanently records oracle, input-record, feature-level, READ-list and "
               "reverse sentinel mutations. These cases make no claim about list-directed output form.\n"
               + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    stale = []
    updates, views = {}, {}
    for section in SECTIONS:
        path = root / CATALOGUES[section]
        catalogue = json.loads(path.read_text())
        updated = synced_catalogue(section, catalogue)
        view = render_view(section, updated, root)
        updates[section] = updated
        views[section] = view
        if catalogue != updated:
            stale.append(CATALOGUES[section])
        if (root / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    stale.extend(path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw)
    if check:
        if stale:
            raise ValueError("stale list-directed input fixture family: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updates[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} list-directed input cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(all_mutations(row)) for row in specs.values())} failing mutations and "
          f"{sum(len(row['reverse_mutations']) for row in specs.values())} reverse controls.")


if __name__ == "__main__":
    main()
