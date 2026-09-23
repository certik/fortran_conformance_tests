#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 integer and BOZ editing."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INT_SECTION = "13.7.2.2"
BOZ_SECTION = "13.7.2.4"
INT_CATALOGUE = "doc/catalogues/integer_editing_13_7_2_2.json"
BOZ_CATALOGUE = "doc/catalogues/b_o_and_z_editing_13_7_2_4.json"
INT_VIEW = "doc/fortran_2023_13_7_2_2.md"
BOZ_VIEW = "doc/fortran_2023_13_7_2_4.md"
SUMMARY_BEGIN = "<!-- BEGIN INTEGER BOZ EDITING FIXTURES -->"
SUMMARY_END = "<!-- END INTEGER BOZ EDITING FIXTURES -->"

CASES = [
    dict(variant="i_width_fixed_selected", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-001", facets=("I-width-fixed-or-selected",),
         title="I5 and I0 output widths", builder="i_width_fixed_selected"),
    dict(variant="i_input_m_ignored", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-002", facets=("I-input-m-ignored",),
         title="I input ignores m", builder="i_input_m_ignored"),
    dict(variant="i_input_signed_digit", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-003", facets=("I-input-signed-digit-string",),
         title="I input signed digit string", builder="i_input_signed_digit"),
    dict(variant="i_output_leading_blanks", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-004", facets=("I-output-leading-blanks",),
         title="I5 positive output leading blanks", builder="i_output_leading_blanks"),
    dict(variant="i_output_negative_minus", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-004", facets=("I-output-negative-minus",),
         title="I5 negative output required minus", builder="i_output_negative_minus"),
    dict(variant="i_output_no_leading_zero", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-004", facets=("I-output-no-leading-zero-magnitude",),
         title="I5 positive magnitude has no leading zeros", builder="i_output_no_leading_zero"),
    dict(variant="i_output_minimum_m_digits", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-005", facets=("I-output-minimum-m-digits",),
         title="I5.4 pads to four digits", builder="i_output_minimum_m_digits"),
    dict(variant="i_output_leading_zeros_to_m", section=INT_SECTION, catalogue=INT_CATALOGUE,
         rule="S13.7.2.2-005", facets=("I-output-leading-zeros-to-m",),
         title="I3.2 inserts one leading zero", builder="i_output_leading_zeros_to_m"),
    dict(variant="boz_width_fixed_selected", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-001", facets=("BOZ-field-width",),
         title="B5 and B0 output widths", builder="boz_width_fixed_selected"),
    dict(variant="boz_input_m_ignored", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-002", facets=("BOZ-input-m-ignored",),
         title="B input ignores m", builder="boz_input_m_ignored"),
    dict(variant="b_input_binary_digits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-003", facets=("B-input-binary-digits",),
         title="B input binary digits", builder="b_input_binary_digits"),
    dict(variant="o_input_octal_digits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-003", facets=("O-input-octal-digits",),
         title="O input octal digits", builder="o_input_octal_digits"),
    dict(variant="z_input_hex_digits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-003", facets=("Z-input-hex-digits",),
         title="Z input uppercase hex digits", builder="z_input_hex_digits"),
    dict(variant="z_input_lowercase_equivalence", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-003", facets=("Z-input-lowercase-equivalence",),
         title="Z input lowercase equals uppercase", builder="z_input_lowercase_equivalence"),
    dict(variant="b_output_no_leading_zero_bits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-005", facets=("B-output-digits-no-leading-zero-bits",),
         title="B5 output omits leading zero bits", builder="b_output_no_leading_zero_bits"),
    dict(variant="o_output_no_leading_zero_bits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-005", facets=("O-output-digits-no-leading-zero-bits",),
         title="O4 output omits leading zero bits", builder="o_output_no_leading_zero_bits"),
    dict(variant="z_output_no_leading_zero_bits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-005", facets=("Z-output-digits-no-leading-zero-bits",),
         title="Z3 output omits leading zero bits", builder="z_output_no_leading_zero_bits"),
    dict(variant="boz_output_minimum_m_digits", section=BOZ_SECTION, catalogue=BOZ_CATALOGUE,
         rule="S13.7.2.4-007", facets=("BOZ-output-minimum-m-digits",),
         title="B/O/Z w.m pad to m digits", builder="boz_output_minimum_m_digits"),
]

CASE_BY_VARIANT = {case["variant"]: case for case in CASES}
SELECTED_FACETS_BY_CATALOGUE_RULE = {}
for case in CASES:
    SELECTED_FACETS_BY_CATALOGUE_RULE.setdefault((case["catalogue"], case["rule"]), set()).update(case["facets"])

ORACLE_PARAGRAPHS = {
    (INT_CATALOGUE, "S13.7.2.2-001"): (
        "S13.7.2.2-001 integer-width runtime fixture: one complete run/effect/f2023 program writes "
        "the exact value 42 with (SS,I5) to a length-5 internal file and expects the five characters "
        "'   42', then writes the same value with (SS,I0) to a length-2 internal file and expects '42'. "
        "The SS sign mode suppresses the optional plus; the I5 field width supplies three leading blanks. "
        "Permanent descriptor substitutions I5->I6 and I5->I5.4, sign-control substitution SS->SP, "
        "input-value mutation 42->43, and exact-string oracle mutations are all required to fail."),
    (INT_CATALOGUE, "S13.7.2.2-002"): (
        "S13.7.2.2-002 integer-input m runtime fixture: one complete program reads the exact character "
        "field '7' with I1.1 and with I1 into separate integers and expects both results to be 7. The only "
        "format difference is the .m component; input-field and integer-oracle mutations are required to fail."),
    (INT_CATALOGUE, "S13.7.2.2-003"): (
        "S13.7.2.2-003 signed-digit input runtime fixture: one complete program reads '-42' with I3 and "
        "expects -42, and reads ' 42' with I3 and expects 42 after leading-blank handling. The signs and "
        "digits are hand-derived signed-digit strings; both field-value and integer-oracle mutations fail."),
    (INT_CATALOGUE, "S13.7.2.2-004"): (
        "S13.7.2.2-004 Iw output runtime fixtures: three complete programs cover leading blanks, required "
        "minus, and no leading-zero magnitude. (SS,I5) with 42 expects '   42'; I5 with -42 expects '  -42'; "
        "and (SS,I5) with 7 expects '    7'. Positive cases use SS so the optional plus latitude is not an "
        "oracle. Exact field length is checked before character equality. I5 descriptor, SS sign, value, and "
        "literal-oracle mutations are load-bearing."),
    (INT_CATALOGUE, "S13.7.2.2-005"): (
        "S13.7.2.2-005 Iw.m output runtime fixtures: two complete programs cover minimum digit count and "
        "zero insertion to m. (SS,I5.4) with 42 expects ' 0042': four magnitude digits are formed as 0042 "
        "and right-justified in width 5. (SS,I3.2) with 7 expects ' 07': two magnitude digits are formed as "
        "07 and right-justified in width 3. Descriptor, SS sign, value, and exact-string mutations fail."),
    (BOZ_CATALOGUE, "S13.7.2.4-001"): (
        "S13.7.2.4-001 BOZ-width runtime fixture: one complete program writes integer 5 with B5 and expects "
        "'  101', then writes the same value with B0 to a length-3 internal file and expects '101'. Binary "
        "digits for 5 are 101; B5 right-justifies them in five positions, while B0 selects the three-character "
        "width. Value and exact-string mutations fail."),
    (BOZ_CATALOGUE, "S13.7.2.4-002"): (
        "S13.7.2.4-002 BOZ-input m runtime fixture: one complete program reads '101' with B3.3 and with B3 "
        "into separate integers and expects both results to be 5. The only format difference is .m; field and "
        "integer-oracle mutations fail."),
    (BOZ_CATALOGUE, "S13.7.2.4-003"): (
        "S13.7.2.4-003 BOZ input digit runtime fixtures: four complete programs read '101' with B3 as 5, "
        "'10' with O2 as 8, '0A' with Z2 as 10, and '0a' with Z2 as 10. The lowercase case is compared to "
        "the same exact integer value as uppercase A. Each fixture mutates the field and the expected integer."),
    (BOZ_CATALOGUE, "S13.7.2.4-005"): (
        "S13.7.2.4-005 BOZ output digit runtime fixtures: three complete programs write nonzero default "
        "integers whose binary, octal, and hexadecimal constant digits are unambiguous. B5 with 5 expects "
        "'  101'; O4 with 8 expects '  10'; Z3 with 10 expects '  A'. These are the digit strings after "
        "removing leading zero bits and right-justifying in the requested field width. Value, descriptor, and "
        "literal-oracle mutations fail."),
    (BOZ_CATALOGUE, "S13.7.2.4-007"): (
        "S13.7.2.4-007 BOZ w.m minimum-digit runtime fixture: one complete program writes 5 with B4.4 "
        "expecting '0101', 8 with O4.4 expecting '0010', and 10 with Z4.4 expecting '000A'. Each digit string "
        "is padded with leading zeros to four digits and right-justified in width 4. The permanent descriptor "
        "substitution matrix replaces each of B4.4, O4.4, and Z4.4 by the other two descriptors; every "
        "substitution must fail against the original exact oracle."),
}

LIMIT_PARAGRAPHS = {
    INT_CATALOGUE: (
        "Integer-editing fixture boundaries: this packet discharges only the selected integer facets removed "
        "from pending above. It deliberately does not test the unnumbered I0 input restriction, real/item-type "
        "mismatch controls, optional plus under processor S control, m>w restrictions, zero m special cases, "
        "enum/enumeration editing, G/B/O/Z delegation, diagnostics, external files, list-directed I/O, kind "
        "selection, overflow, or universal compiler conformance. Expected strings are hand-derived from "
        "13.7.2.2 and use internal WRITE/READ only."),
    BOZ_CATALOGUE: (
        "BOZ-editing fixture boundaries: this packet discharges only the selected integer BOZ facets removed "
        "from pending above. It avoids real and complex BOZ bit-sequence results, enum/enumeration constructors, "
        "B0/O0/Z0 input controls, unacceptable-field IOSTAT behavior, m>w restrictions, zero m special cases, "
        "R1323 syntax-only coverage, diagnostics, external files, list-directed I/O, and processor representation "
        "claims. Expected strings are hand-derived from 13.7.2.4 for nonnegative default integers."),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    case = CASE_BY_VARIANT[variant]
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__integer_boz_editing_" + variant


def program_name(variant):
    return "ibe_" + variant


class Program:
    def __init__(self, case):
        self.case = case
        self.variant = case["variant"]
        self.text = ""
        self.probes = []
        self.observations = []
        self.declarations = []
        self.body = []

    def add_body(self, text):
        self.body.append(text)

    def render_prefix(self):
        covers = "".join(f"! covers: {facet}\n" for facet in self.case["facets"])
        return (f"program {program_name(self.variant)}\n"
                "  implicit none\n"
                f"! rule: {self.case['rule']}\n" + covers +
                "  integer :: checks\n" +
                "\n".join(self.declarations) + ("\n" if self.declarations else "") +
                "  checks = 0\n")

    def render_suffix(self, total):
        completion = self.completion_literal()
        return (
            f"  if (checks /= {total}) then\n"
            f"    write(*,'(a)') 'IBE:{self.variant}:check-total'\n"
            "    error stop 1\n"
            "  end if\n"
            f"  write(*,'(a)') '{completion}'\n"
            "contains\n"
            "  subroutine expect_text(observed, expected, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'IBE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'IBE:text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_text\n"
            "  subroutine expect_int(observed, expected, label)\n"
            "    integer, intent(in) :: observed, expected\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'IBE:int', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_int\n"
            f"end program {program_name(self.variant)}\n")

    def completion_literal(self):
        return "INTEGER BOZ EDITING " + self.variant.upper().replace("_", " ") + " OK"

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
            failure_stdout=f"IBE:{self.variant}:check-total\n"))
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

    def mutate_span_in_next(self, line, expected, replacement, probe_id, mutation, category, failure_stdout=None):
        start = self.current_length() + line.index(expected)
        self.probes.append(dict(
            id=probe_id, kind="source", category=category, mutation=mutation,
            span=[start, start + len(expected)], expected=expected, replacement=replacement,
            failure_stdout=failure_stdout if failure_stdout is not None else f"IBE:{self.variant}"))

    def assign_integer(self, name, value, replacement):
        line = f"  {name} = {value}\n"
        self.mutate_span_in_next(line, str(value), str(replacement), f"input-{name}", "input-value", "input")
        self.add(line)

    def assign_character(self, name, value, replacement):
        line = f"  {name} = '{value}'\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-field", "input")
        self.add(line)

    def write_stmt(self, buf, fmt, value_name, *, descriptor_mutations=(), sign_mutation=False):
        line = f"  write({buf},'({fmt})') {value_name}\n"
        for expected, replacement, tag in descriptor_mutations:
            self.mutate_span_in_next(line, expected, replacement, f"descriptor-{tag}", "descriptor-substitution", "descriptor")
        if sign_mutation:
            self.mutate_span_in_next(line, "SS", "SP", f"sign-{buf}", "sign-mode-substitution", "sign")
        self.add(line)

    def read_stmt(self, text_var, fmt, out_var):
        self.add(f"  read({text_var},'({fmt})') {out_var}\n")

    def expect_text(self, buf, expected, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_text({buf}, '{expected}', '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "text-oracle", "oracle",
                                 f"IBE:text {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_int(self, var, expected, replacement, label):
        line = f"  call expect_int({var}, {expected}, '{label}')\n"
        self.mutate_span_in_next(line, str(expected), str(replacement), f"oracle-{label}", "integer-oracle", "oracle",
                                 f"IBE:int {label}\n")
        self.add(line)
        self.observations.append(label)


def corrupt_text(value):
    if not value:
        raise ValueError("empty text oracle")
    chars = list(value)
    for index in range(len(chars) - 1, -1, -1):
        if chars[index] != " ":
            chars[index] = "X" if chars[index] != "X" else "Y"
            return "".join(chars)
    chars[0] = "X"
    return "".join(chars)


def make_program(case):
    p = Program(case)
    builder = case["builder"]
    getattr(sys.modules[__name__], "build_" + builder)(p)
    text = p.source()
    return p, text


def build_i_width_fixed_selected(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: fixed")
    p.declare("character(len=2) :: selected")
    p.assign_integer("value", 42, 43)
    p.write_stmt("fixed", "SS,I5", "value", descriptor_mutations=(("I5", "I6", "i5-to-i6"), ("I5", "I5.4", "i5-to-i5_4")), sign_mutation=True)
    p.expect_text("fixed", "   42", "i5-fixed")
    p.write_stmt("selected", "SS,I0", "value")
    p.expect_text("selected", "42", "i0-selected")


def build_i_input_m_ignored(p):
    p.declare("character(len=1) :: field_m, field_plain")
    p.declare("integer :: got_m, got_plain")
    p.assign_character("field_m", "7", "8")
    p.assign_character("field_plain", "7", "8")
    p.read_stmt("field_m", "I1.1", "got_m")
    p.expect_int("got_m", 7, 8, "i1-m")
    p.read_stmt("field_plain", "I1", "got_plain")
    p.expect_int("got_plain", 7, 8, "i1-plain")


def build_i_input_signed_digit(p):
    p.declare("character(len=3) :: field_negative, field_positive")
    p.declare("integer :: got_negative, got_positive")
    p.assign_character("field_negative", "-42", "-43")
    p.assign_character("field_positive", " 42", " 43")
    p.read_stmt("field_negative", "I3", "got_negative")
    p.expect_int("got_negative", -42, -43, "i3-negative")
    p.read_stmt("field_positive", "I3", "got_positive")
    p.expect_int("got_positive", 42, 43, "i3-positive")


def build_i_output_leading_blanks(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: field")
    p.assign_integer("value", 42, 43)
    p.write_stmt("field", "SS,I5", "value", descriptor_mutations=(("I5", "I6", "i5-to-i6"), ("I5", "I5.4", "i5-to-i5_4")), sign_mutation=True)
    p.expect_text("field", "   42", "i5-leading")


def build_i_output_negative_minus(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: field")
    p.assign_integer("value", -42, -43)
    p.write_stmt("field", "I5", "value")
    p.expect_text("field", "  -42", "i5-negative")


def build_i_output_no_leading_zero(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: field")
    p.assign_integer("value", 7, 8)
    p.write_stmt("field", "SS,I5", "value", descriptor_mutations=(("I5", "I5.4", "i5-to-i5_4"),), sign_mutation=True)
    p.expect_text("field", "    7", "i5-no-zero")


def build_i_output_minimum_m_digits(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: field")
    p.assign_integer("value", 42, 43)
    p.write_stmt("field", "SS,I5.4", "value", descriptor_mutations=(("I5.4", "I5", "i5_4-to-i5"),), sign_mutation=True)
    p.expect_text("field", " 0042", "i5-4-minimum")


def build_i_output_leading_zeros_to_m(p):
    p.declare("integer :: value")
    p.declare("character(len=3) :: field")
    p.assign_integer("value", 7, 8)
    p.write_stmt("field", "SS,I3.2", "value", descriptor_mutations=(("I3.2", "I3", "i3_2-to-i3"),), sign_mutation=True)
    p.expect_text("field", " 07", "i3-2-zero")


def build_boz_width_fixed_selected(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: fixed")
    p.declare("character(len=3) :: selected")
    p.assign_integer("value", 5, 6)
    p.write_stmt("fixed", "B5", "value")
    p.expect_text("fixed", "  101", "b5-fixed")
    p.write_stmt("selected", "B0", "value")
    p.expect_text("selected", "101", "b0-selected")


def build_boz_input_m_ignored(p):
    p.declare("character(len=3) :: field_m, field_plain")
    p.declare("integer :: got_m, got_plain")
    p.assign_character("field_m", "101", "100")
    p.assign_character("field_plain", "101", "100")
    p.read_stmt("field_m", "B3.3", "got_m")
    p.expect_int("got_m", 5, 4, "b3-m")
    p.read_stmt("field_plain", "B3", "got_plain")
    p.expect_int("got_plain", 5, 4, "b3-plain")


def build_b_input_binary_digits(p):
    p.declare("character(len=3) :: field")
    p.declare("integer :: got")
    p.assign_character("field", "101", "100")
    p.read_stmt("field", "B3", "got")
    p.expect_int("got", 5, 4, "b3-digits")


def build_o_input_octal_digits(p):
    p.declare("character(len=2) :: field")
    p.declare("integer :: got")
    p.assign_character("field", "10", "11")
    p.read_stmt("field", "O2", "got")
    p.expect_int("got", 8, 9, "o2-digits")


def build_z_input_hex_digits(p):
    p.declare("character(len=2) :: field")
    p.declare("integer :: got")
    p.assign_character("field", "0A", "0B")
    p.read_stmt("field", "Z2", "got")
    p.expect_int("got", 10, 11, "z2-upper")


def build_z_input_lowercase_equivalence(p):
    p.declare("character(len=2) :: field")
    p.declare("integer :: got")
    p.assign_character("field", "0a", "0b")
    p.read_stmt("field", "Z2", "got")
    p.expect_int("got", 10, 11, "z2-lower")


def build_b_output_no_leading_zero_bits(p):
    p.declare("integer :: value")
    p.declare("character(len=5) :: field")
    p.assign_integer("value", 5, 6)
    p.write_stmt("field", "B5", "value")
    p.expect_text("field", "  101", "b5-no-leading")


def build_o_output_no_leading_zero_bits(p):
    p.declare("integer :: value")
    p.declare("character(len=4) :: field")
    p.assign_integer("value", 8, 9)
    p.write_stmt("field", "O4", "value")
    p.expect_text("field", "  10", "o4-no-leading")


def build_z_output_no_leading_zero_bits(p):
    p.declare("integer :: value")
    p.declare("character(len=3) :: field")
    p.assign_integer("value", 10, 11)
    p.write_stmt("field", "Z3", "value")
    p.expect_text("field", "  A", "z3-no-leading")


def build_boz_output_minimum_m_digits(p):
    matrix = (("B4.4", "O4.4", "b-to-o"), ("B4.4", "Z4.4", "b-to-z"),
              ("O4.4", "B4.4", "o-to-b"), ("O4.4", "Z4.4", "o-to-z"),
              ("Z4.4", "B4.4", "z-to-b"), ("Z4.4", "O4.4", "z-to-o"))
    p.declare("integer :: b_value, o_value, z_value")
    p.declare("character(len=4) :: b_field, o_field, z_field")
    p.assign_integer("b_value", 5, 6)
    p.assign_integer("o_value", 8, 9)
    p.assign_integer("z_value", 10, 11)
    p.write_stmt("b_field", "B4.4", "b_value", descriptor_mutations=matrix[0:2])
    p.expect_text("b_field", "0101", "b4-4-minimum")
    p.write_stmt("o_field", "O4.4", "o_value", descriptor_mutations=matrix[2:4])
    p.expect_text("o_field", "0010", "o4-4-minimum")
    p.write_stmt("z_field", "Z4.4", "z_value", descriptor_mutations=matrix[4:6])
    p.expect_text("z_field", "000A", "z4-4-minimum")


def source_specs():
    specs = {}
    for case in CASES:
        program, source = make_program(case)
        raw = source.encode("ascii")
        name = identifier(case["variant"])
        specs[name] = dict(
            id=name, variant=case["variant"], rule=case["rule"], facets=list(case["facets"]),
            section=case["section"], title=case["title"], source=source, source_sha256=sha(raw),
            probes=copy.deepcopy(program.probes), observations=list(program.observations),
            completion=program.completion_literal() + "\n")
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
        directory = "tests/fixtures/integer_boz_editing_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect",
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
        raise ValueError("duplicate integer/BOZ fixture paragraph")
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
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""),
            ("Integer-editing fixture boundaries:" if catalogue_path == INT_CATALOGUE else "BOZ-editing fixture boundaries:"),
            LIMIT_PARAGRAPHS[catalogue_path])
    return result


def render_view(catalogue, section, catalogue_path, view_path, root=ROOT):
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
    note = summary_text(section)
    return before.rstrip() + "\n\n" + note + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def summary_text(section):
    if section == INT_SECTION:
        return (SUMMARY_BEGIN + "\n"
                "## Executable integer editing fixtures\n\n"
                "This packet adds eight complete internal-file programs for selected 13.7.2.2 integer editing "
                "facets. Each output fixture writes an exact nonzero integer value to a CHARACTER variable, "
                "checks LEN before comparing the whole expected field, and uses SS where a positive sign would "
                "otherwise be optional. Input fixtures read exact internal character fields and compare integer "
                "sentinels. The generator owns only the listed selected facets and mutation plans; review state and "
                "execution approval remain integrator-owned.\n"
                + SUMMARY_END)
    return (SUMMARY_BEGIN + "\n"
            "## Executable BOZ editing fixtures\n\n"
            "This packet adds ten complete internal-file programs for selected 13.7.2.4 BOZ editing facets. "
            "The fixtures use nonnegative default integers with hand-derived binary, octal, and hexadecimal "
            "strings, avoid real/complex representation latitude, and include a permanent B4.4/O4.4/Z4.4 "
            "descriptor-substitution matrix. Every output oracle checks LEN before character equality, so no "
            "case can pass by blank-padding a shorter expected literal.\n"
            + SUMMARY_END)


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for catalogue_path, section, view_path in ((INT_CATALOGUE, INT_SECTION, INT_VIEW), (BOZ_CATALOGUE, BOZ_SECTION, BOZ_VIEW)):
        catalogue = json.loads((root / catalogue_path).read_text())
        updated = synced_catalogue(catalogue, catalogue_path)
        updated_catalogues[catalogue_path] = updated
        updated_views[view_path] = render_view(updated, section, catalogue_path, view_path, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for catalogue_path, updated in updated_catalogues.items():
            if json.loads((root / catalogue_path).read_text()) != updated:
                stale.append(catalogue_path)
        for view_path, updated in updated_views.items():
            if (root / view_path).read_text() != updated:
                stale.append(view_path)
        if stale:
            raise ValueError("stale integer/BOZ editing fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for catalogue_path, updated in updated_catalogues.items():
                (root / catalogue_path).write_text(json.dumps(updated, indent=2) + "\n")
            for view_path, updated in updated_views.items():
                (root / view_path).write_text(updated)
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
    work_dir = root / ".integer_boz_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
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
                                   category=probe["category"], parent_ok=parent_ok, failed=failed,
                                   status=observed["status"], stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"]))
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
    sign = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["mutation"] == "sign-mode-substitution")
    inputs = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "input")
    return len(specs), len(facets), mutations, descriptor, sign, inputs


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
        sign = sum(row["mutation"] == "sign-mode-substitution" for row in report)
        print(f"Mutation-checked {total} integer/BOZ mutations: {descriptor} descriptor, {sign} sign; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count, descriptor_count, sign_count, input_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} integer/BOZ editing cases, "
          f"{facet_count} facets and {mutation_count} mutations "
          f"({descriptor_count} descriptor, {sign_count} sign, {input_count} input).")


if __name__ == "__main__":
    main()
