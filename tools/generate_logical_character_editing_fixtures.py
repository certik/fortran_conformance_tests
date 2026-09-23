#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 logical and character editing."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGICAL_SECTION = "13.7.3"
CHARACTER_SECTION = "13.7.4"
LOGICAL_CATALOGUE = "doc/catalogues/logical_editing_13_7_3.json"
CHARACTER_CATALOGUE = "doc/catalogues/character_editing_13_7_4.json"
LOGICAL_VIEW = "doc/fortran_2023_13_7_3.md"
CHARACTER_VIEW = "doc/fortran_2023_13_7_4.md"
SUMMARY_BEGIN = "<!-- BEGIN LOGICAL CHARACTER EDITING FIXTURES -->"
SUMMARY_END = "<!-- END LOGICAL CHARACTER EDITING FIXTURES -->"

CASES = [
    dict(variant="l_logical_output", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-001", facets=("L-logical-output",), evidence="positive-control",
         title="L editing uses a logical item", builder="l_logical_output"),
    dict(variant="g_logical_output", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-001", facets=("G-logical-editing-permitted",), evidence="positive-control",
         title="G output may edit logical data", builder="g_logical_output"),
    dict(variant="l_output_fields", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-004", facets=("true-output-field", "false-output-field"),
         title="L output fields for true and false", builder="l_output_fields"),
    dict(variant="l_true_forms_and_trailing", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-002", facets=("true-standard-input", "trailing-characters-ignored"),
         title="L input true form with trailing characters", builder="l_true_forms_and_trailing"),
    dict(variant="l_false_standard_input", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-002", facets=("false-standard-input",),
         title="L input false standard form", builder="l_false_standard_input"),
    dict(variant="l_lowercase_t", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-003", facets=("lowercase-t-true",),
         title="L input lowercase t is true", builder="l_lowercase_t"),
    dict(variant="l_lowercase_f", section=LOGICAL_SECTION, catalogue=LOGICAL_CATALOGUE,
         rule="S13.7.3-003", facets=("lowercase-f-false",),
         title="L input lowercase f is false", builder="l_lowercase_f"),
    dict(variant="a_character_item", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-001", facets=("A-character-item",), evidence="positive-control",
         title="A editing uses a character item", builder="a_character_item"),
    dict(variant="g_character_output", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-001", facets=("G-character-editing-permitted",), evidence="positive-control",
         title="G output may edit character data", builder="g_character_output"),
    dict(variant="a_explicit_width_output", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-002", facets=("A-explicit-width",),
         title="A output explicit width pads left", builder="a_explicit_width_output"),
    dict(variant="a_omitted_width_output", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-002", facets=("A-omitted-width-item-length",),
         title="A output omitted width uses item length", builder="a_omitted_width_output"),
    dict(variant="a_input_wide_rightmost", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-003", facets=("input-wide-field-rightmost",),
         title="A input wide field takes rightmost characters", builder="a_input_wide_rightmost"),
    dict(variant="a_input_short_left_justified", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-003", facets=("input-short-field-left-justified",),
         title="A input short field left-justifies", builder="a_input_short_left_justified"),
    dict(variant="a_output_wide_left_padded", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-004", facets=("output-wide-field-left-padded",),
         title="A output wide field pads on the left", builder="a_output_wide_left_padded"),
    dict(variant="a_output_narrow_leftmost", section=CHARACTER_SECTION, catalogue=CHARACTER_CATALOGUE,
         rule="S13.7.4-004", facets=("output-narrow-field-leftmost",),
         title="A output narrow field takes leftmost characters", builder="a_output_narrow_leftmost"),
]

CASE_BY_VARIANT = {case["variant"]: case for case in CASES}
SELECTED_FACETS_BY_CATALOGUE_RULE = {}
for case in CASES:
    SELECTED_FACETS_BY_CATALOGUE_RULE.setdefault((case["catalogue"], case["rule"]), set()).update(case["facets"])

ORACLE_PARAGRAPHS = {
    (LOGICAL_CATALOGUE, "S13.7.3-001"): (
        "S13.7.3-001 logical-editing runtime fixtures: two complete internal-file positive-control programs "
        "discharge selected L and G logical facets. WRITE(field,'(L2)') .true. expects exactly ' T', proving "
        "L editing with a logical effective item. WRITE(field,'(G0)') .false. expects exactly 'F ' in a "
        "length-2 internal file by the 13.7.5.3 G0-as-L1 dependency; the length-2 file makes the selected "
        "width observable because legal L2 writes ' F'. C1306 keeps L0 outside this unit: w may be zero only "
        "for I, B, O, Z, D, E, EN, ES, EX, F, and G, and w is positive for L. Descriptor substitutions "
        "L2->L1 and G0->L2 are conforming on logical items, load-bearing on the selected data, and fail."),
    (LOGICAL_CATALOGUE, "S13.7.3-002"): (
        "S13.7.3-002 logical-input runtime fixtures: two complete internal READ programs use targets "
        "initialized to the opposite logical value and guard-checked before READ. Field ' .Txx' with L5 "
        "expects .true.; the leading blank, optional period, T, and ignored trailing characters are all within "
        "p2's standard form. Field '   F' with L4 expects .false. after optional leading blanks and F. The "
        "fixture also reads a following one-character standard true field solely to make the conforming L4->L3 "
        "width mutant deterministic: if the three-blank first field is rejected, IOSTAT is nonzero; if a "
        "processor accepts it as an extension, the following L1 field reads F rather than the parent's T and "
        "the boundary check fails. Descriptor substitutions L5->L2 and L4->L3 are load-bearing, and every "
        "input target has remove/expected sentinel-init probes."),
    (LOGICAL_CATALOGUE, "S13.7.3-003"): (
        "S13.7.3-003 lowercase logical-input runtime fixtures: two complete internal READ programs guard "
        "opposite-value logical sentinels before READ. Field ' t' with L2 expects .true. and field '.f' with "
        "L2 expects .false., proving lowercase letters are equivalent to uppercase in logical input fields. "
        "The lowercase-t descriptor substitution L2->L1 removes the decisive lowercase letter. The lowercase-f "
        "fixture also reads a following one-character standard true field solely to make the conforming L2->L1 "
        "width mutant deterministic: if the period-only first field is rejected, IOSTAT is nonzero; if a "
        "processor accepts it as an extension, the following L1 field reads f rather than the parent's t and "
        "the boundary check fails. The expected-value sentinel-init probes fail before READ."),
    (LOGICAL_CATALOGUE, "S13.7.3-004"): (
        "S13.7.3-004 logical-output runtime fixture: one complete internal-file program writes .true. with L3 "
        "and .false. with L2, expecting '  T' and ' F'. The outputs are exactly w-1 blanks followed by T or F. "
        "Width substitutions L3->L2 and L2->L1 are load-bearing and fail against the original exact fields."),
    (CHARACTER_CATALOGUE, "S13.7.4-001"): (
        "S13.7.4-001 character-editing runtime fixtures: two complete internal-file positive-control programs "
        "discharge selected A and G character facets. WRITE(field,'(A2)') 'xy' expects exactly 'xy', proving "
        "A editing with a default-character effective item, and WRITE(field,'(G0)') 'xy' expects exactly 'xy' by the "
        "13.7.5.4 G0-as-A dependency. Descriptor substitutions A2->A1 and G0->A1 are load-bearing. AT facets "
        "remain pending in this packet because the f2023 reference rejects the AT descriptor, so there is no "
        "reference-validated fixture to ship."),
    (CHARACTER_CATALOGUE, "S13.7.4-002"): (
        "S13.7.4-002 A-width runtime fixtures: two complete internal WRITE programs discharge explicit and "
        "omitted-width facets. A4 on the length-2 value 'xy' produces a field of four characters, exactly "
        "'  xy'; A without w on the same length-2 item produces exactly 'xy'. A4->A3 and A->A1 substitutions "
        "change the selected field on the chosen values and fail."),
    (CHARACTER_CATALOGUE, "S13.7.4-003"): (
        "S13.7.4-003 A-input runtime fixtures: two complete internal READ programs initialize nonblank "
        "character targets with sentinels and guard them before READ. Reading field 'abcd' with A4 into "
        "character(len=2) expects the rightmost two characters 'cd'. Reading 'xy' with A2 into "
        "character(len=4) expects exactly 'xy  ', including the trailing blanks; length is checked before "
        "equality so character-comparison blank padding cannot hide errors. A4->A3 and A2->A1 substitutions "
        "and remove/expected/blank sentinel-init probes all fail."),
    (CHARACTER_CATALOGUE, "S13.7.4-004"): (
        "S13.7.4-004 A-output runtime fixtures: two complete internal WRITE programs cover both branches. "
        "A4 on length-2 'xy' expects '  xy', proving left blank padding when w>len. A2 on length-4 'wxyz' "
        "expects 'wx', proving the leftmost w characters are output when w<=len. A4->A3 and A2->A1 "
        "substitutions are load-bearing and fail."),
}

LIMIT_PARAGRAPHS = {
    LOGICAL_CATALOGUE: (
        "Logical-editing fixture boundaries: this packet discharges only the selected L and G logical facets "
        "removed from pending above. It leaves nonlogical L-item diagnostics and nonstandard logical input "
        "latitude pending. L0 is not tested here because 13.3.2 C1306 requires positive w for L; zero-width "
        "selected output belongs only to the descriptor families named in 13.7.2.1(6), not to L editing. "
        "All input targets start from the opposite logical value, are guard-checked before READ, and have "
        "expected-value sentinel-init mutants."),
    CHARACTER_CATALOGUE: (
        "Character-editing fixture boundaries: this packet discharges only selected default-character A and G "
        "facets removed from pending above. It deliberately leaves AT descriptors pending because the f2023 "
        "reference used by this suite rejects AT format descriptors, leaves AT-input diagnostics and "
        "nondefault-kind implications pending, and leaves stream NEW_LINE/file-positioning facets for a future "
        "external-file packet. Character assertions check LEN before equality and use nonblank sentinels so "
        "blank padding cannot satisfy an oracle vacuously."),
}

SUMMARY_BY_SECTION = {
    LOGICAL_SECTION: (
        "This packet adds complete internal-file programs for selected 13.7.3 logical editing facets. L output "
        "uses positive widths only, because C1306 requires L widths to be positive; L input targets are "
        "initialized to the opposite value and guard-checked before READ, with permanent expected-value "
        "sentinel-init probes."),
    CHARACTER_SECTION: (
        "This packet adds complete internal-file programs for selected 13.7.4 default-character editing facets. "
        "A output covers w<len, w=len/omitted, and w>len; A input covers rightmost-character and left-justified "
        "trailing-blank rules. LEN is checked before equality so blank padding cannot hide errors."),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def all_facets(case):
    return list(case["facets"])


def identifier(variant):
    case = CASE_BY_VARIANT[variant]
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__logical_character_editing_" + variant


def program_name(variant):
    return "lce_" + variant


class Program:
    def __init__(self, case):
        self.case = case
        self.variant = case["variant"]
        self.text = ""
        self.probes = []
        self.observations = []
        self.declarations = []
        self.body = []

    def render_prefix(self):
        covers = "".join(f"! covers: {facet}\n" for facet in all_facets(self.case))
        return (f"program {program_name(self.variant)}\n"
                "  implicit none\n"
                f"! rule: {self.case['rule']}\n" + covers +
                "  integer :: checks\n" +
                "\n".join(self.declarations) + ("\n" if self.declarations else "") +
                "  checks = 0\n")

    def completion_literal(self):
        return "LOGICAL CHARACTER EDITING " + self.variant.upper().replace("_", " ") + " OK"

    def render_suffix(self, total):
        completion = self.completion_literal()
        return (
            f"  if (checks /= {total}) then\n"
            f"    write(*,'(a)') 'LCE:{self.variant}:check-total'\n"
            "    error stop 1\n"
            "  end if\n"
            f"  write(*,'(a)') '{completion}'\n"
            "contains\n"
            "  subroutine mark_logical(name, value, guard, sentinel)\n"
            "    character(len=*), intent(in) :: name\n"
            "    logical, intent(out) :: value\n"
            "    integer, intent(out) :: guard\n"
            "    logical, intent(in) :: sentinel\n"
            "    if (len(name) == 0) error stop 1\n"
            "    value = sentinel\n"
            "    guard = 1\n"
            "  end subroutine mark_logical\n"
            "  subroutine mark_text(name, value, guard, sentinel)\n"
            "    character(len=*), intent(in) :: name\n"
            "    character(len=*), intent(out) :: value\n"
            "    integer, intent(out) :: guard\n"
            "    character(len=*), intent(in) :: sentinel\n"
            "    if (len(name) == 0) error stop 1\n"
            "    value = sentinel\n"
            "    guard = 1\n"
            "  end subroutine mark_text\n"
            "  subroutine expect_text(observed, expected, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'LCE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'LCE:text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_text\n"
            "  subroutine expect_logical(observed, expected, label)\n"
            "    logical, intent(in) :: observed, expected\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (observed .neqv. expected) then\n"
            "      write(*,'(a,1x,a)') 'LCE:logical', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_logical\n"
            "  subroutine expect_int(observed, expected, label)\n"
            "    integer, intent(in) :: observed, expected\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'LCE:int', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_int\n"
            "  subroutine expect_pre_logical(observed, expected, guard, label)\n"
            "    logical, intent(in) :: observed, expected\n"
            "    integer, intent(in) :: guard\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (guard /= 1) then\n"
            "      write(*,'(a,1x,a)') 'LCE:pre-logical', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed .neqv. expected) then\n"
            "      write(*,'(a,1x,a)') 'LCE:pre-logical', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_pre_logical\n"
            "  subroutine expect_pre_text(observed, expected, guard, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    integer, intent(in) :: guard\n"
            "    if (guard /= 1) then\n"
            "      write(*,'(a,1x,a)') 'LCE:pre-text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'LCE:pre-text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'LCE:pre-text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_pre_text\n"
            f"end program {program_name(self.variant)}\n")

    def source(self):
        prefix = self.render_prefix()
        body = "".join(self.body)
        total = len(self.observations)
        suffix_start = len(prefix) + len(body)
        suffix = self.render_suffix(total)
        self.text = prefix + body + suffix
        needle = f"checks /= {total}"
        start = suffix_start + suffix.index(needle)
        self.probes.append(dict(
            id="reverse-check-total", kind="reverse", category="sentinel", mutation="reverse-total-sentinel",
            span=[start + len("checks "), start + len("checks ") + len("/=")], expected="/=", replacement="==",
            failure_stdout=f"LCE:{self.variant}:check-total\n"))
        literal = self.completion_literal()
        marker = f"write(*,'(a)') '{literal}'"
        start = suffix_start + suffix.index(marker) + marker.index(literal)
        self.probes.append(dict(
            id="oracle-completion", kind="output", category="oracle", mutation="completion-literal",
            span=[start, start + len(literal)], expected=literal, replacement=literal.replace(" OK", " BAD"),
            failure_stdout=""))
        raw = self.text.encode("ascii")
        for probe in self.probes:
            lo, hi = probe["span"]
            if raw[lo:hi].decode("ascii") != probe["expected"]:
                raise ValueError(f"probe span lost complete-parent binding: {self.variant}:{probe['id']}")
        return self.text

    def declare(self, line):
        self.declarations.append("  " + line)

    def add(self, text):
        self.body.append(text)

    def current_length(self):
        return len(self.render_prefix()) + sum(len(part) for part in self.body)

    def mutate_span_in_next(self, line, expected, replacement, probe_id, mutation, category,
                            failure_stdout=None, discriminant=None):
        start = self.current_length() + line.index(expected)
        probe = dict(id=probe_id, kind="source", category=category, mutation=mutation,
                     span=[start, start + len(expected)], expected=expected, replacement=replacement,
                     failure_stdout=failure_stdout if failure_stdout is not None else f"LCE:{self.variant}")
        if discriminant:
            probe["discriminant"] = discriminant
        self.probes.append(probe)

    def assign_logical(self, name, value, replacement):
        line = f"  {name} = {value}\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-value", "input")
        self.add(line)

    def assign_character(self, name, value, replacement):
        line = f"  {name} = '{value}'\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-field", "input")
        self.add(line)

    def set_buffer(self, name, sentinel):
        self.add(f"  {name} = '{sentinel}'\n")

    def init_logical_target(self, name, guard, sentinel, expected_after_read, label):
        line = f"  call mark_logical('{label}', {name}, {guard}, {sentinel})\n"
        start = self.current_length()
        for suffix, replacement, note in (
            ("remove", "", f"{name}: removing the opposite-value sentinel leaves the pre-READ guard unset"),
            ("expected", f"  call mark_logical('{label}', {name}, {guard}, {expected_after_read})\n",
             f"{name}: initializing to the expected READ result would make a missing READ vacuous"),
        ):
            self.probes.append(dict(
                id=f"sentinel-{label}-{suffix}", kind="source", category="sentinel-init",
                mutation="sentinel-initialization-" + suffix,
                span=[start, start + len(line)], expected=line, replacement=replacement,
                failure_stdout=f"LCE:pre-logical {label}\n", discriminant=note))
        self.add(line)
        self.expect_pre_logical(name, sentinel, guard, label)

    def init_text_target(self, name, guard, sentinel, expected_after_read, label):
        line = f"  call mark_text('{label}', {name}, {guard}, '{sentinel}')\n"
        start = self.current_length()
        for suffix, replacement, note in (
            ("remove", "", f"{name}: removing the nonblank sentinel leaves the pre-READ guard unset"),
            ("expected", f"  call mark_text('{label}', {name}, {guard}, '{expected_after_read}')\n",
             f"{name}: initializing to the expected READ result would make a missing READ vacuous"),
            ("blank", f"  call mark_text('{label}', {name}, {guard}, '{' ' * len(sentinel)}')\n",
             f"{name}: blank initialization is distinguishable from the nonblank sentinel and expected result"),
        ):
            self.probes.append(dict(
                id=f"sentinel-{label}-{suffix}", kind="source", category="sentinel-init",
                mutation="sentinel-initialization-" + suffix,
                span=[start, start + len(line)], expected=line, replacement=replacement,
                failure_stdout=f"LCE:pre-text {label}\n", discriminant=note))
        self.add(line)
        self.expect_pre_text(name, sentinel, guard, label)

    def write_stmt(self, buf, fmt, value_name, *, descriptor_mutations=()):
        line = f"  write({buf},'({fmt})') {value_name}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def read_stmt(self, text_var, fmt, out_var, *, descriptor_mutations=()):
        line = f"  read({text_var},'({fmt})') {out_var}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def read_stmt_iostat(self, text_var, fmt, out_vars, ios_var, *, descriptor_mutations=()):
        line = f"  read({text_var},'({fmt})', iostat={ios_var}) {out_vars}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def expect_text(self, buf, expected, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_text({buf}, '{expected}', '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "text-oracle", "oracle",
                                 f"LCE:text {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_logical(self, var, expected, replacement, label):
        line = f"  call expect_logical({var}, {expected}, '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "logical-oracle", "oracle",
                                 f"LCE:logical {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_int(self, var, expected, replacement, label):
        line = f"  call expect_int({var}, {expected}, '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "int-oracle", "oracle",
                                 f"LCE:int {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_pre_logical(self, var, expected, guard, label):
        line = f"  call expect_pre_logical({var}, {expected}, {guard}, '{label}')\n"
        self.mutate_span_in_next(line, expected, logical_opposite(expected), f"pre-{label}",
                                 "pre-read-guard", "sentinel", f"LCE:pre-logical {label}\n")
        self.add(line)
        self.observations.append("pre-" + label)

    def expect_pre_text(self, var, expected, guard, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_pre_text({var}, '{expected}', {guard}, '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"pre-{label}",
                                 "pre-read-guard", "sentinel", f"LCE:pre-text {label}\n")
        self.add(line)
        self.observations.append("pre-" + label)


def logical_opposite(value):
    if value == ".true.":
        return ".false."
    if value == ".false.":
        return ".true."
    raise ValueError(value)


def corrupt_text(value):
    chars = list(value)
    for index in range(len(chars) - 1, -1, -1):
        if chars[index] != " ":
            chars[index] = "X" if chars[index] != "X" else "Y"
            return "".join(chars)
    chars[0] = "X"
    return "".join(chars)


def dsub(old, new, tag, discriminant):
    return {"from": old, "to": new, "id": "descriptor-" + tag, "discriminant": discriminant}


def make_program(case):
    p = Program(case)
    getattr(sys.modules[__name__], "build_" + case["builder"])(p)
    return p, p.source()


def build_l_logical_output(p):
    p.declare("logical :: value")
    p.declare("character(len=2) :: field")
    p.assign_logical("value", ".true.", ".false.")
    p.set_buffer("field", "##")
    p.write_stmt("field", "L2", "value", descriptor_mutations=(
        dsub("L2", "L1", "l2-to-l1", ".true.: L2 is ' T', L1 is 'T' and leaves position 2 unchanged"),
    ))
    p.expect_text("field", " T", "l-logical-item")


def build_l_output_fields(p):
    p.declare("logical :: true_value, false_value")
    p.declare("character(len=3) :: true_field")
    p.declare("character(len=2) :: false_field")
    p.assign_logical("true_value", ".true.", ".false.")
    p.assign_logical("false_value", ".false.", ".true.")
    p.set_buffer("true_field", "###")
    p.write_stmt("true_field", "L3", "true_value", descriptor_mutations=(
        dsub("L3", "L2", "l3-to-l2", ".true.: L3 is '  T', L2 is ' T' and leaves position 3 unchanged"),
    ))
    p.expect_text("true_field", "  T", "l3-true")
    p.set_buffer("false_field", "##")
    p.write_stmt("false_field", "L2", "false_value", descriptor_mutations=(
        dsub("L2", "L1", "l2-to-l1", ".false.: L2 is ' F', L1 is 'F' and leaves position 2 unchanged"),
    ))
    p.expect_text("false_field", " F", "l2-false")


def build_l_true_forms_and_trailing(p):
    p.declare("character(len=5) :: field")
    p.declare("logical :: value")
    p.declare("integer :: guard")
    p.assign_character("field", " .Txx", " .Fxx")
    p.add("  guard = 0\n")
    p.init_logical_target("value", "guard", ".false.", ".true.", "true-trailing")
    p.read_stmt("field", "L5", "value", descriptor_mutations=(
        dsub("L5", "L2", "l5-to-l2", "' .Txx': L5 reaches T; L2 reads only blank and period"),
    ))
    p.expect_logical("value", ".true.", ".false.", "true-trailing")


def build_l_false_standard_input(p):
    p.declare("character(len=4) :: field")
    p.declare("character(len=1) :: boundary_field")
    p.declare("character(len=5) :: record")
    p.declare("logical :: value, boundary_value")
    p.declare("integer :: guard, boundary_guard, ios")
    p.assign_character("field", "   F", "   T")
    p.add("  boundary_field = 'T'\n")
    p.add("  record = field // boundary_field\n")
    p.add("  guard = 0\n")
    p.add("  boundary_guard = 0\n")
    p.init_logical_target("value", "guard", ".true.", ".false.", "false-standard")
    p.init_logical_target("boundary_value", "boundary_guard", ".false.", ".true.", "false-boundary")
    p.add("  ios = -1\n")
    p.read_stmt_iostat("record", "L4,L1", "value, boundary_value", "ios", descriptor_mutations=(
        dsub("L4", "L3", "l4-to-l3",
             "'   FT': L4 reads standard false from positions 1-4 and L1 reads true at position 5; L3 shifts the next L1 to F"),
    ))
    p.expect_int("ios", "0", "1", "false-standard-ios")
    p.expect_logical("value", ".false.", ".true.", "false-standard")
    p.expect_logical("boundary_value", ".true.", ".false.", "false-boundary")


def build_l_lowercase_t(p):
    p.declare("character(len=2) :: field")
    p.declare("logical :: value")
    p.declare("integer :: guard")
    p.assign_character("field", " t", " f")
    p.add("  guard = 0\n")
    p.init_logical_target("value", "guard", ".false.", ".true.", "lower-t")
    p.read_stmt("field", "L2", "value", descriptor_mutations=(
        dsub("L2", "L1", "l2-to-l1", "' t': L2 reaches lowercase t; L1 reads only an optional blank"),
    ))
    p.expect_logical("value", ".true.", ".false.", "lower-t")


def build_l_lowercase_f(p):
    p.declare("character(len=2) :: field")
    p.declare("character(len=1) :: boundary_field")
    p.declare("character(len=3) :: record")
    p.declare("logical :: value, boundary_value")
    p.declare("integer :: guard, boundary_guard, ios")
    p.assign_character("field", ".f", ".t")
    p.add("  boundary_field = 't'\n")
    p.add("  record = field // boundary_field\n")
    p.add("  guard = 0\n")
    p.add("  boundary_guard = 0\n")
    p.init_logical_target("value", "guard", ".true.", ".false.", "lower-f")
    p.init_logical_target("boundary_value", "boundary_guard", ".false.", ".true.", "lower-f-boundary")
    p.add("  ios = -1\n")
    p.read_stmt_iostat("record", "L2,L1", "value, boundary_value", "ios", descriptor_mutations=(
        dsub("L2", "L1", "l2-to-l1",
             "'.ft': L2 reads standard lowercase false from positions 1-2 and L1 reads true at position 3; L1 shifts the next field to f"),
    ))
    p.expect_int("ios", "0", "1", "lower-f-ios")
    p.expect_logical("value", ".false.", ".true.", "lower-f")
    p.expect_logical("boundary_value", ".true.", ".false.", "lower-f-boundary")


def build_g_logical_output(p):
    p.declare("logical :: value")
    p.declare("character(len=2) :: field")
    p.assign_logical("value", ".false.", ".true.")
    p.set_buffer("field", "##")
    p.write_stmt("field", "G0", "value", descriptor_mutations=(
        dsub("G0", "L2", "g0-to-l2", ".false.: G0 writes selected-width 'F ', L2 writes fixed-width ' F'"),
    ))
    p.expect_text("field", "F ", "g0-logical")


def build_a_character_item(p):
    p.declare("character(len=2) :: value")
    p.declare("character(len=2) :: field")
    p.assign_character("value", "xy", "xz")
    p.set_buffer("field", "##")
    p.write_stmt("field", "A2", "value", descriptor_mutations=(
        dsub("A2", "A1", "a2-to-a1", "'xy': A2 writes 'xy', A1 writes 'x' and leaves position 2 unchanged"),
    ))
    p.expect_text("field", "xy", "a-character-item")


def build_a_explicit_width_output(p):
    p.declare("character(len=2) :: value")
    p.declare("character(len=4) :: field")
    p.assign_character("value", "xy", "xz")
    p.set_buffer("field", "####")
    p.write_stmt("field", "A4", "value", descriptor_mutations=(
        dsub("A4", "A3", "a4-to-a3", "'xy': A4 is '  xy', A3 is ' xy' and leaves position 4 unchanged"),
    ))
    p.expect_text("field", "  xy", "a4-wide")


def build_a_omitted_width_output(p):
    p.declare("character(len=2) :: value")
    p.declare("character(len=2) :: field")
    p.assign_character("value", "xy", "xz")
    p.set_buffer("field", "##")
    p.write_stmt("field", "A", "value", descriptor_mutations=(
        dsub("A", "A1", "a-to-a1", "length-2 'xy': A without w is 'xy', A1 is 'x' and leaves position 2 unchanged"),
    ))
    p.expect_text("field", "xy", "a-omitted")


def build_a_input_wide_rightmost(p):
    p.declare("character(len=4) :: field")
    p.declare("character(len=2) :: value")
    p.declare("integer :: guard")
    p.assign_character("field", "abcd", "abce")
    p.add("  guard = 0\n")
    p.init_text_target("value", "guard", "??", "cd", "wide-rightmost")
    p.read_stmt("field", "A4", "value", descriptor_mutations=(
        dsub("A4", "A3", "a4-to-a3", "'abcd' into len=2: A4 takes 'cd'; A3 takes rightmost 'bc'"),
    ))
    p.expect_text("value", "cd", "wide-rightmost")


def build_a_input_short_left_justified(p):
    p.declare("character(len=2) :: field")
    p.declare("character(len=4) :: value")
    p.declare("integer :: guard")
    p.assign_character("field", "xy", "xz")
    p.add("  guard = 0\n")
    p.init_text_target("value", "guard", "????", "xy  ", "short-left")
    p.read_stmt("field", "A2", "value", descriptor_mutations=(
        dsub("A2", "A1", "a2-to-a1", "'xy' into len=4: A2 gives 'xy  ', A1 gives 'x   '"),
    ))
    p.expect_text("value", "xy  ", "short-left")


def build_a_output_wide_left_padded(p):
    p.declare("character(len=2) :: value")
    p.declare("character(len=4) :: field")
    p.assign_character("value", "xy", "xz")
    p.set_buffer("field", "####")
    p.write_stmt("field", "A4", "value", descriptor_mutations=(
        dsub("A4", "A3", "a4-to-a3", "'xy': A4 is '  xy', A3 is ' xy' and leaves position 4 unchanged"),
    ))
    p.expect_text("field", "  xy", "a4-wide-output")


def build_a_output_narrow_leftmost(p):
    p.declare("character(len=4) :: value")
    p.declare("character(len=2) :: field")
    p.assign_character("value", "wxyz", "wyxz")
    p.set_buffer("field", "##")
    p.write_stmt("field", "A2", "value", descriptor_mutations=(
        dsub("A2", "A1", "a2-to-a1", "'wxyz': A2 writes 'wx', A1 writes 'w' and leaves position 2 unchanged"),
    ))
    p.expect_text("field", "wx", "a2-narrow")


def build_g_character_output(p):
    p.declare("character(len=2) :: value")
    p.declare("character(len=2) :: field")
    p.assign_character("value", "xy", "xz")
    p.set_buffer("field", "##")
    p.write_stmt("field", "G0", "value", descriptor_mutations=(
        dsub("G0", "A1", "g0-to-a1", "length-2 'xy': G0 writes 'xy', A1 writes 'x' and leaves position 2 unchanged"),
    ))
    p.expect_text("field", "xy", "g0-character")


def source_specs():
    specs = {}
    for case in CASES:
        program, source = make_program(case)
        raw = source.encode("ascii")
        name = identifier(case["variant"])
        specs[name] = dict(
            id=name, variant=case["variant"], rule=case["rule"], facets=all_facets(case),
            profiles=list(case.get("profiles", ())), section=case["section"], title=case["title"],
            evidence=case.get("evidence", "effect"),
            source=source, source_sha256=sha(raw), probes=copy.deepcopy(program.probes),
            observations=list(program.observations), completion=program.completion_literal() + "\n")
    return specs


def wrong_oracle_source(spec, probe):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = probe["span"]
    if raw[start:end].decode("ascii") != probe["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + probe["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, spec in specs.items():
        directory = "tests/fixtures/logical_character_editing_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence=spec["evidence"],
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate logical/character fixture paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue, catalogue_path):
    result = copy.deepcopy(catalogue)
    selected_by_rule = {rule: facets for (cat, rule), facets in SELECTED_FACETS_BY_CATALOGUE_RULE.items()
                        if cat == catalogue_path}
    for rule, facets in selected_by_rule.items():
        rows = [row for row in result["requirements"] if row["id"] == rule]
        if len(rows) != 1:
            raise ValueError(f"selected requirement {rule} changed")
        row = rows[0]
        if not facets <= set(row["facets"]):
            raise ValueError(f"selected facets for {rule} changed")
        for facet in sorted(facets):
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), rule + " ", ORACLE_PARAGRAPHS[(catalogue_path, rule)])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""),
                                                   LIMIT_PARAGRAPHS[catalogue_path].split(":", 1)[0] + ":",
                                                   LIMIT_PARAGRAPHS[catalogue_path])
    return result


def summary_text(section):
    return SUMMARY_BEGIN + "\n## Executable logical/character editing fixtures\n\n" + SUMMARY_BY_SECTION[section] + "\n" + SUMMARY_END


def render_view(catalogue, section, view_path, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / view_path
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated boundary changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError(f"summary boundary changed for {section}")
        leading, rest_summary = before.split(SUMMARY_BEGIN)
        _, trailing = rest_summary.split(SUMMARY_END)
        before = leading.rstrip() + "\n\n" + trailing.lstrip()
    return before.rstrip() + "\n\n" + summary_text(section) + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    logical_catalogue = json.loads((root / LOGICAL_CATALOGUE).read_text())
    character_catalogue = json.loads((root / CHARACTER_CATALOGUE).read_text())
    updated_logical = synced_catalogue(logical_catalogue, LOGICAL_CATALOGUE)
    updated_character = synced_catalogue(character_catalogue, CHARACTER_CATALOGUE)
    updated_logical_view = render_view(updated_logical, LOGICAL_SECTION, LOGICAL_VIEW, root)
    updated_character_view = render_view(updated_character, CHARACTER_SECTION, CHARACTER_VIEW, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if json.loads((root / LOGICAL_CATALOGUE).read_text()) != updated_logical:
            stale.append(LOGICAL_CATALOGUE)
        if json.loads((root / CHARACTER_CATALOGUE).read_text()) != updated_character:
            stale.append(CHARACTER_CATALOGUE)
        if (root / LOGICAL_VIEW).read_text() != updated_logical_view:
            stale.append(LOGICAL_VIEW)
        if (root / CHARACTER_VIEW).read_text() != updated_character_view:
            stale.append(CHARACTER_VIEW)
        if stale:
            raise ValueError("stale logical/character editing fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            (root / LOGICAL_CATALOGUE).write_text(json.dumps(updated_logical, indent=2) + "\n")
            (root / CHARACTER_CATALOGUE).write_text(json.dumps(updated_character, indent=2) + "\n")
            (root / LOGICAL_VIEW).write_text(updated_logical_view)
            (root / CHARACTER_VIEW).write_text(updated_character_view)
    return specs


def compiler_command(compiler, std, source, output):
    command = [str(compiler)]
    if std:
        command.append(std)
    command += [str(source), "-o", str(output)]
    return command


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compile_run = subprocess.run(compiler_command(compiler, std, source, exe), text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_run.returncode != 0:
        return dict(status="compile-fail", stdout=compile_run.stdout, stderr=compile_run.stderr,
                    returncode=compile_run.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = (run.returncode == 0 and run.stdout == expected_stdout and run.stderr == "")
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr,
                returncode=run.returncode)


def mutation_check(root, compiler, std, keep_work=False):
    root = Path(root)
    specs = source_specs()
    work_dir = root / ".logical_character_editing_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    try:
        report = []
        for spec in specs.values():
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["completion"], spec["variant"] + "_parent")
            parent_ok = parent["status"] == "pass"
            for index, probe in enumerate(spec["probes"]):
                mutant_source = wrong_oracle_source(spec, probe).decode("ascii")
                observed = run_one_source(compiler, std, work_dir, mutant_source, spec["completion"],
                                          f"{spec['variant']}_mut_{index:03d}")
                failed = not (observed["status"] == "pass")
                report.append(dict(variant=spec["variant"], probe=probe["id"], mutation=probe["mutation"],
                                   category=probe["category"], expected=probe["expected"],
                                   replacement=probe["replacement"],
                                   discriminant=probe.get("discriminant", ""), parent_ok=parent_ok,
                                   failed=failed, status=observed["status"], stdout=observed["stdout"],
                                   stderr=observed["stderr"], returncode=observed["returncode"]))
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:5], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)


def counts(specs):
    facets = {facet for spec in specs.values() for facet in spec["facets"]}
    mutations = sum(len(spec["probes"]) for spec in specs.values())
    descriptor = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["mutation"] == "descriptor-substitution")
    inputs = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "input")
    sentinels = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "sentinel-init")
    pre_guards = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["mutation"] == "pre-read-guard")
    return len(specs), len(facets), mutations, descriptor, inputs, sentinels, pre_guards


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogues:
        parser.error("--check and --sync-catalogues are separate operations")
    if args.mutation_check:
        if args.check or args.sync_catalogues:
            parser.error("--mutation-check is separate from generation/checking")
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        total = len(report)
        descriptor = sum(row["mutation"] == "descriptor-substitution" for row in report)
        sentinels = sum(row["category"] == "sentinel-init" for row in report)
        pre_guards = sum(row["mutation"] == "pre-read-guard" for row in report)
        print(f"Mutation-checked {total} logical/character editing mutations: {descriptor} descriptor, "
              f"{sentinels} sentinel-init, {pre_guards} pre-read guards; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count, descriptor_count, input_count, sentinel_count, pre_guard_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} logical/character editing cases, "
          f"{facet_count} facets and {mutation_count} mutations "
          f"({descriptor_count} descriptor, {input_count} input, {sentinel_count} sentinel-init, "
          f"{pre_guard_count} pre-read guards).")


if __name__ == "__main__":
    main()
