#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 F editing."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
F_SECTION = "13.7.2.3.2"
F_CATALOGUE = "doc/catalogues/f_editing_13_7_2_3_2.json"
F_VIEW = "doc/fortran_2023_13_7_2_3_2.md"
SUMMARY_BEGIN = "<!-- BEGIN F EDITING FIXTURES -->"
SUMMARY_END = "<!-- END F EDITING FIXTURES -->"

CASES = [
    dict(variant="field_width_fixed_selected", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-001", facets=("F-field-width",),
         title="F fixed and selected output widths", builder="field_width_fixed_selected"),
    dict(variant="fractional_digits", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-001", facets=("F-fractional-digits",),
         title="F output fractional digit count", builder="fractional_digits"),
    dict(variant="lowercase_real_exponent", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-002", facets=("lowercase-real-exponent-input",),
         title="Lowercase E exponent input", builder="lowercase_real_exponent"),
    dict(variant="lowercase_ieee_exceptional_input", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-002", facets=("lowercase-ieee-exceptional-input",),
         title="Lowercase IEEE exceptional input", builder="lowercase_ieee_exceptional_input",
         profiles=("ieee-binary",)),
    dict(variant="input_ieee_form", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-003", facets=("F-input-ieee-form",),
         title="F input IEEE exceptional form", builder="input_ieee_form", profiles=("ieee-binary",)),
    dict(variant="input_mantissa_decimal", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-003", facets=("F-input-mantissa-with-decimal-symbol",),
         title="F input mantissa decimal symbol overrides d", builder="input_mantissa_decimal"),
    dict(variant="input_omitted_decimal_d", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-003", facets=("F-input-omitted-decimal-uses-d",),
         title="F input omitted decimal uses d", builder="input_omitted_decimal_d"),
    dict(variant="input_e_exponent", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-003", facets=("F-input-E-exponent-form",),
         title="F input E exponent form", builder="input_e_exponent"),
    dict(variant="input_d_exponent", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-003", facets=("F-input-D-exponent-form",),
         title="F input D exponent form", builder="input_d_exponent"),
    dict(variant="d_exponent_same_as_e", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-004", facets=("D-exponent-same-as-E-exponent",),
         title="D exponent input equals E exponent input", builder="d_exponent_same_as_e"),
    dict(variant="ieee_infinity_input_syntax", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-006", facets=("ieee-infinity-input-syntax", "ieee-exceptional-leading-trailing-blanks"),
         title="IEEE infinity input syntax and blanks", builder="ieee_infinity_input_syntax", profiles=("ieee-binary",)),
    dict(variant="ieee_nan_input_syntax", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-006", facets=("ieee-nan-input-syntax",),
         title="IEEE NaN input syntax", builder="ieee_nan_input_syntax", profiles=("ieee-binary",)),
    dict(variant="nan_empty_payload_quiet", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-007", facets=("nan-empty-payload-quiet",),
         title="NaN empty payload input is quiet", builder="nan_empty_payload_quiet",
         profiles=("ieee-binary",)),
    dict(variant="infinity_output_wide", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-010", facets=("infinity-output-right-justified", "infinity-output-infinity-form-when-wide"),
         title="Infinity output wide form", builder="infinity_output_wide", profiles=("ieee-binary",)),
    dict(variant="infinity_output_narrow", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-010", facets=("infinity-output-inf-form-when-narrow",
                                          "infinity-output-asterisks-when-too-narrow"),
         title="Infinity output narrow forms", builder="infinity_output_narrow", profiles=("ieee-binary",)),
    dict(variant="nan_output_forced_widths", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-011", facets=("nan-output-NaN-right-justified",
                                          "nan-output-too-narrow-asterisks", "nan-output-w0-NaN"),
         title="NaN output forced width forms", builder="nan_output_forced_widths", profiles=("ieee-binary",)),
    dict(variant="finite_output_sign", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-012", facets=("F-finite-output-sign",),
         title="Finite F output required minus", builder="finite_output_sign"),
    dict(variant="finite_output_decimal_fraction", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-012", facets=("F-finite-output-decimal-symbol", "F-finite-output-d-fractional-digits"),
         title="Finite F output decimal symbol and d fractional digits", builder="finite_output_decimal_fraction"),
    dict(variant="finite_output_leading_zero", section=F_SECTION, catalogue=F_CATALOGUE,
         rule="S13.7.2.3.2-012", facets=("F-finite-output-leading-zero-rule",),
         title="Finite F output leading zero before decimal", builder="finite_output_leading_zero"),
]

CASE_BY_VARIANT = {case["variant"]: case for case in CASES}
SELECTED_FACETS_BY_CATALOGUE_RULE = {}
for case in CASES:
    SELECTED_FACETS_BY_CATALOGUE_RULE.setdefault((case["catalogue"], case["rule"]), set()).update(case["facets"])

ORACLE_PARAGRAPHS = {
    (F_CATALOGUE, "S13.7.2.3.2-001"): (
        "S13.7.2.3.2-001 F-editing runtime fixtures: two complete internal-file programs discharge selected "
        "field-width and fractional-digit effects. (SS,F5.1) with exact -3.0 writes ' -3.0' in five positions; "
        "(SS,F0.1) with exact 3.0 writes selected-width '3.0' in a length-3 internal file; and (SS,F5.2) "
        "with exact 1.25 writes ' 1.25'. SS suppresses optional plus signs. The generator permanently mutates "
        "F5.1->F6.1/F5.2, F0.1->F4.1, and F5.2->F5.3/E12.4; every substitution changes the selected value's "
        "field and is required to fail."),
    (F_CATALOGUE, "S13.7.2.3.2-002"): (
        "S13.7.2.3.2-002 lowercase runtime fixtures: two complete programs internally read exact lowercase "
        "fields. '1e1' with F3.0 expects exactly 10.0 because lowercase e is equivalent to E in a numeric "
        "exponent; 'inf' with F3.0, under the ieee-binary profile, expects IEEE positive infinity because "
        "lowercase letters are equivalent in IEEE exceptional specifications. Descriptor substitutions "
        "F3.0->F3.1 and F3.0->F2.0 respectively change the omitted-decimal interpretation or truncate the "
        "exceptional spelling and fail."),
    (F_CATALOGUE, "S13.7.2.3.2-003"): (
        "S13.7.2.3.2-003 F-input runtime fixtures: five complete programs read standard input forms into "
        "default real values that are exactly representable: uppercase INF with F3.0 as IEEE positive infinity, "
        "'1.5' with F3.0 as 1.5, '15' with F2.1 as 1.5, '1E+1' with F4.0 as 10.0, and '1D+1' with F4.0 "
        "as 10.0. Descriptor substitutions narrow the field or change d so the value or validity changes; "
        "hexadecimal-significand and extra-digit latitude facets remain pending."),
    (F_CATALOGUE, "S13.7.2.3.2-004"): (
        "S13.7.2.3.2-004 D/E exponent runtime fixture: one complete program reads '1E+1' and '1D+1' with "
        "F4.0 and requires the two exact default-real results to be equal to 10.0. Substituting F4.1 for either "
        "read changes the omitted-decimal interpretation to 1.0 and fails."),
    (F_CATALOGUE, "S13.7.2.3.2-006"): (
        "S13.7.2.3.2-006 IEEE exceptional input syntax runtime fixtures: two complete programs read uppercase "
        "' INF ' with F5.0 and uppercase 'NAN()' with F5.0. The infinity case checks IEEE positive infinity and "
        "the leading/trailing blanks; the NaN case checks IEEE NaN. F5.0->F3.0 and F5.0->F2.0 substitutions "
        "truncate the required spelling and fail."),
    (F_CATALOGUE, "S13.7.2.3.2-007"): (
        "S13.7.2.3.2-007 NaN empty-payload runtime fixture: one complete program reads uppercase 'NAN()' "
        "with F5.0 under the ieee-binary profile after initializing the real variable to finite -99.0. It "
        "asserts ieee_class(value) == ieee_quiet_nan, proving p6's required quiet-NaN result without asserting "
        "any payload value or sign interpretation. F5.0->F2.0 truncates the spelling and fails."),
    (F_CATALOGUE, "S13.7.2.3.2-010"): (
        "S13.7.2.3.2-010 infinity output runtime fixtures: two complete programs write IEEE positive infinity "
        "under the ieee-binary profile. (SS,F9.1) expects exactly ' Infinity': width 9 is at least the minimum "
        "for the Infinity form with no sign, SS suppresses the optional plus, and the one leading blank proves "
        "right justification. (SS,F4.1) expects exactly ' Inf' because width 4 is less than the eight positions "
        "needed for 'Infinity' but at least the three positions needed for 'Inf'; (SS,F2.1) expects exactly "
        "'**' because width 2 is below the minimum for any infinity form. Descriptor substitutions "
        "F9.1->F8.1/F4.1, F4.1->F3.1, and F2.1->F3.1 select different fields and fail."),
    (F_CATALOGUE, "S13.7.2.3.2-011"): (
        "S13.7.2.3.2-011 NaN output runtime fixture: one complete program writes an IEEE quiet NaN under the "
        "ieee-binary profile without asserting any payload spelling or sign interpretation. (SS,F5.1) writes "
        "exactly '  NaN': width 5 admits the right-justified NaN form but cannot contain any one-to-w-5 "
        "alphanumeric payload character. (SS,F0.1) writes exactly 'NaN' to a length-3 internal file because "
        "w=0 selects the NaN output field; (SS,F2.1) writes exactly '**' because positive widths less than 3 "
        "are filled with asterisks. Descriptor substitutions F5.1->F4.1, F0.1->F4.1, and F2.1->F3.1 select "
        "different fields and fail."),
    (F_CATALOGUE, "S13.7.2.3.2-012"): (
        "S13.7.2.3.2-012 finite F-output runtime fixtures: three complete programs write exact finite values "
        "to internal character variables. (SS,F5.1) with -3.0 expects ' -3.0' for the required minus; "
        "(SS,F5.2) with 1.25 expects ' 1.25' for POINT decimal symbol and two fractional digits; and "
        "(SS,RZ,F3.0) with exact 0.25 expects ' 0.'. RZ pins 13.7.2.3.8 rounding toward zero, so 0.25 with "
        "d=0 is not a tie and rounds to magnitude zero; without the zero required by p11 there would be no "
        "digits in the field. This proves only the mandatory leading-zero half, not any rounding facet. "
        "All positive finite outputs use SS. Descriptor substitutions F5.1->F5.2/F6.1, F5.2->F5.3/E12.4, and "
        "F3.0->F2.0 change the chosen value's field and fail."),
}

LIMIT_PARAGRAPH = (
    "F-editing fixture boundaries: this packet discharges only the selected 25 finite, exponent, IEEE-input, "
    "infinity-output, and forced-width NaN-output facets removed from pending above. It deliberately leaves F0 "
    "input source-control, hexadecimal-significand input, embedded-blank controls, nonstandard processor-"
    "acceptable input, NaN payload/sign latitude, explicit rounded-output facets, scale factor, "
    "leading-zero mode, decimal comma mode, external files, diagnostics, and processor-dependent latitude "
    "pending. Expected finite strings are hand-derived from 13.7.2.3.2, 13.7.2.3.8, 13.8.4, and 13.8.5 using "
    "exactly representable binary values and internal WRITE/READ only; the RZ descriptor in the leading-zero "
    "fixture pins rounding solely to make p11's mandatory no-digits case observable."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    case = CASE_BY_VARIANT[variant]
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__f_editing_" + variant


def program_name(variant):
    return "fe_" + variant


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
        covers = "".join(f"! covers: {facet}\n" for facet in self.case["facets"])
        use_line = "  use, intrinsic :: ieee_arithmetic\n" if self.case.get("profiles") else ""
        return (f"program {program_name(self.variant)}\n" + use_line +
                "  implicit none\n"
                f"! rule: {self.case['rule']}\n" + covers +
                "  integer :: checks\n" +
                "\n".join(self.declarations) + ("\n" if self.declarations else "") +
                "  checks = 0\n")

    def render_suffix(self, total):
        completion = self.completion_literal()
        return (
            f"  if (checks /= {total}) then\n"
            f"    write(*,'(a)') 'FE:{self.variant}:check-total'\n"
            "    error stop 1\n"
            "  end if\n"
            f"  write(*,'(a)') '{completion}'\n"
            "contains\n"
            "  subroutine expect_text(observed, expected, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'FE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'FE:text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_text\n"
            "  subroutine expect_real(observed, expected, label)\n"
            "    real, intent(in) :: observed, expected\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'FE:real', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_real\n"
            "  subroutine expect_true(observed, label)\n"
            "    logical, intent(in) :: observed\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (.not. observed) then\n"
            "      write(*,'(a,1x,a)') 'FE:logical', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_true\n"
            f"end program {program_name(self.variant)}\n")

    def completion_literal(self):
        return "F EDITING " + self.variant.upper().replace("_", " ") + " OK"

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
            failure_stdout=f"FE:{self.variant}:check-total\n"))
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
                     failure_stdout=failure_stdout if failure_stdout is not None else f"FE:{self.variant}")
        if discriminant:
            probe["discriminant"] = discriminant
        self.probes.append(probe)

    def assign_real(self, name, value, replacement):
        line = f"  {name} = {value}\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-value", "input")
        self.add(line)

    def assign_character(self, name, value, replacement):
        line = f"  {name} = '{value}'\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-field", "input")
        self.add(line)

    def init_real(self, name, value, expected_after_read, label):
        line = f"  {name} = {value}\n"
        start = self.current_length()
        for suffix, replacement, note in (
            ("remove", "", f"{name}: removing distinguished sentinel leaves the pre-READ guard unestablished"),
            ("expected", f"  {name} = {expected_after_read}\n",
             f"{name}: initializing to the expected READ result would make a missing READ vacuous"),
            ("zero", f"  {name} = 0.0\n",
             f"{name}: default-equivalent zero is distinguishable from the sentinel and expected result"),
        ):
            self.probes.append(dict(
                id=f"sentinel-{label}-{suffix}", kind="source", category="sentinel-init",
                mutation="sentinel-initialization-" + suffix,
                span=[start, start + len(line)], expected=line, replacement=replacement,
                failure_stdout=f"FE:real {label}\n", discriminant=note))
        self.add(line)
        self.expect_real(name, value, "0.0", label)

    def set_buffer(self, name, sentinel):
        self.add(f"  {name} = '{sentinel}'\n")

    def write_stmt(self, buf, fmt, value_name, *, descriptor_mutations=(), sign_mutation=False):
        line = f"  write({buf},'({fmt})') {value_name}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        if sign_mutation:
            self.mutate_span_in_next(line, "SS", "SP", f"sign-{buf}", "sign-mode-substitution", "sign")
        self.add(line)

    def read_stmt(self, text_var, fmt, out_var, *, descriptor_mutations=()):
        line = f"  read({text_var},'({fmt})') {out_var}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def expect_text(self, buf, expected, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_text({buf}, '{expected}', '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "text-oracle", "oracle",
                                 f"FE:text {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_real(self, var, expected, replacement, label):
        line = f"  call expect_real({var}, {expected}, '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "real-oracle", "oracle",
                                 f"FE:real {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_true(self, expression, replacement, label):
        line = f"  call expect_true({expression}, '{label}')\n"
        self.mutate_span_in_next(line, expression, replacement, f"oracle-{label}", "logical-oracle", "oracle",
                                 f"FE:logical {label}\n")
        self.add(line)
        self.observations.append(label)


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


def build_field_width_fixed_selected(p):
    p.declare("real :: negative_value, positive_value")
    p.declare("character(len=5) :: fixed")
    p.declare("character(len=3) :: selected")
    p.assign_real("negative_value", "-3.0", "-2.0")
    p.assign_real("positive_value", "3.0", "2.0")
    p.set_buffer("fixed", "#####")
    p.write_stmt("fixed", "SS,F5.1", "negative_value", descriptor_mutations=(
        dsub("F5.1", "F6.1", "f5_1-to-f6_1", "-3.0: F5.1 is ' -3.0', F6.1 needs six positions '  -3.0'"),
        dsub("F5.1", "F5.2", "f5_1-to-f5_2", "-3.0: F5.1 is ' -3.0', F5.2 is '-3.00'"),
    ))
    p.expect_text("fixed", " -3.0", "f5-1-fixed")
    p.set_buffer("selected", "###")
    p.write_stmt("selected", "SS,F0.1", "positive_value", descriptor_mutations=(
        dsub("F0.1", "F4.1", "f0_1-to-f4_1", "3.0: F0.1 selects '3.0', F4.1 needs four positions ' 3.0'"),
    ), sign_mutation=True)
    p.expect_text("selected", "3.0", "f0-1-selected")


def build_fractional_digits(p):
    p.declare("real :: value")
    p.declare("character(len=5) :: field")
    p.assign_real("value", "1.25", "1.75")
    p.set_buffer("field", "#####")
    p.write_stmt("field", "SS,F5.2", "value", descriptor_mutations=(
        dsub("F5.2", "F5.3", "f5_2-to-f5_3", "1.25: F5.2 is ' 1.25', F5.3 is '1.250'"),
        dsub("F5.2", "E12.4", "f5_2-to-e12_4", "1.25: F5.2 fixed field differs from E12.4 exponent field"),
    ), sign_mutation=True)
    p.expect_text("field", " 1.25", "f5-2-fraction")


def build_lowercase_real_exponent(p):
    p.declare("character(len=3) :: field")
    p.declare("real :: value")
    p.assign_character("field", "1e1", "1e2")
    p.init_real("value", "-99.0", "10.0", "sentinel-lower-e")
    p.read_stmt("field", "F3.0", "value", descriptor_mutations=(
        dsub("F3.0", "F3.1", "f3_0-to-f3_1", "'1e1': F3.0 gives 10.0, F3.1 gives 1.0"),
    ))
    p.expect_real("value", "10.0", "11.0", "lower-e")


def build_lowercase_ieee_exceptional_input(p):
    p.declare("character(len=3) :: field")
    p.declare("real :: value")
    p.assign_character("field", "inf", "inx")
    p.init_real("value", "-99.0", "ieee_value(0.0, ieee_positive_inf)", "sentinel-lower-inf")
    p.read_stmt("field", "F3.0", "value", descriptor_mutations=(
        dsub("F3.0", "F2.0", "f3_0-to-f2_0", "'inf': F3.0 is a lowercase IEEE exceptional field, F2.0 reads only 'in'"),
    ))
    p.expect_real("value", "ieee_value(0.0, ieee_positive_inf)", "0.0", "lower-inf")


def build_input_ieee_form(p):
    p.declare("character(len=3) :: field")
    p.declare("real :: value")
    p.assign_character("field", "INF", "INX")
    p.init_real("value", "-99.0", "ieee_value(0.0, ieee_positive_inf)", "sentinel-ieee-inf-form")
    p.read_stmt("field", "F3.0", "value", descriptor_mutations=(
        dsub("F3.0", "F2.0", "f3_0-to-f2_0", "'INF': F3.0 is an IEEE exceptional field, F2.0 reads only 'IN'"),
    ))
    p.expect_real("value", "ieee_value(0.0, ieee_positive_inf)", "0.0", "ieee-inf-form")


def build_input_mantissa_decimal(p):
    p.declare("character(len=3) :: field")
    p.declare("real :: value")
    p.assign_character("field", "1.5", "2.5")
    p.init_real("value", "-99.0", "1.5", "sentinel-decimal-symbol")
    p.read_stmt("field", "F3.0", "value", descriptor_mutations=(
        dsub("F3.0", "F2.0", "f3_0-to-f2_0", "'1.5': F3.0 gives 1.5, F2.0 reads '1.' as 1.0"),
    ))
    p.expect_real("value", "1.5", "2.5", "decimal-symbol")


def build_input_omitted_decimal_d(p):
    p.declare("character(len=2) :: field")
    p.declare("real :: value")
    p.assign_character("field", "15", "25")
    p.init_real("value", "-99.0", "1.5", "sentinel-omitted-decimal")
    p.read_stmt("field", "F2.1", "value", descriptor_mutations=(
        dsub("F2.1", "F2.0", "f2_1-to-f2_0", "'15': F2.1 gives 1.5, F2.0 gives 15.0"),
    ))
    p.expect_real("value", "1.5", "2.5", "omitted-decimal")


def build_input_e_exponent(p):
    p.declare("character(len=4) :: field")
    p.declare("real :: value")
    p.assign_character("field", "1E+1", "1E+2")
    p.init_real("value", "-99.0", "10.0", "sentinel-e-exponent")
    p.read_stmt("field", "F4.0", "value", descriptor_mutations=(
        dsub("F4.0", "F4.1", "f4_0-to-f4_1", "'1E+1': F4.0 gives 10.0, F4.1 gives 1.0"),
    ))
    p.expect_real("value", "10.0", "11.0", "e-exponent")


def build_input_d_exponent(p):
    p.declare("character(len=4) :: field")
    p.declare("real :: value")
    p.assign_character("field", "1D+1", "1D+2")
    p.init_real("value", "-99.0", "10.0", "sentinel-d-exponent")
    p.read_stmt("field", "F4.0", "value", descriptor_mutations=(
        dsub("F4.0", "F4.1", "f4_0-to-f4_1", "'1D+1': F4.0 gives 10.0, F4.1 gives 1.0"),
    ))
    p.expect_real("value", "10.0", "11.0", "d-exponent")


def build_d_exponent_same_as_e(p):
    p.declare("character(len=4) :: e_field, d_field")
    p.declare("real :: e_value, d_value")
    p.assign_character("e_field", "1E+1", "1E+2")
    p.assign_character("d_field", "1D+1", "1D+2")
    p.init_real("e_value", "-99.0", "10.0", "sentinel-e-control")
    p.init_real("d_value", "-88.0", "10.0", "sentinel-d-control")
    p.read_stmt("e_field", "F4.0", "e_value", descriptor_mutations=(
        dsub("F4.0", "F4.1", "e-f4_0-to-f4_1", "'1E+1': F4.0 gives 10.0, F4.1 gives 1.0"),
    ))
    p.read_stmt("d_field", "F4.0", "d_value", descriptor_mutations=(
        dsub("F4.0", "F4.1", "d-f4_0-to-f4_1", "'1D+1': F4.0 gives 10.0, F4.1 gives 1.0"),
    ))
    p.expect_real("e_value", "10.0", "11.0", "e-control")
    p.expect_real("d_value", "10.0", "11.0", "d-control")
    p.expect_true("d_value == e_value", "d_value /= e_value", "d-same-e")


def build_ieee_infinity_input_syntax(p):
    p.declare("character(len=5) :: field")
    p.declare("real :: value")
    p.assign_character("field", " INF ", " INX ")
    p.init_real("value", "-99.0", "ieee_value(0.0, ieee_positive_inf)", "sentinel-inf-blanks")
    p.read_stmt("field", "F5.0", "value", descriptor_mutations=(
        dsub("F5.0", "F3.0", "f5_0-to-f3_0", "' INF ': F5.0 includes optional blanks and INF, F3.0 reads ' IN'"),
    ))
    p.expect_real("value", "ieee_value(0.0, ieee_positive_inf)", "0.0", "inf-blanks")


def build_ieee_nan_input_syntax(p):
    p.declare("character(len=5) :: field")
    p.declare("real :: value")
    p.assign_character("field", "NAN()", "NAX()")
    p.init_real("value", "-99.0", "ieee_value(0.0, ieee_quiet_nan)", "sentinel-nan-empty")
    p.read_stmt("field", "F5.0", "value", descriptor_mutations=(
        dsub("F5.0", "F2.0", "f5_0-to-f2_0", "'NAN()': F5.0 is NAN empty payload, F2.0 reads only 'NA'"),
    ))
    p.expect_true("ieee_is_nan(value)", "ieee_is_finite(value)", "nan-empty")


def build_nan_empty_payload_quiet(p):
    p.declare("character(len=5) :: field")
    p.declare("real :: value")
    p.assign_character("field", "NAN()", "NAX()")
    p.init_real("value", "-99.0", "ieee_value(0.0, ieee_quiet_nan)", "sentinel-nan-empty-quiet")
    p.read_stmt("field", "F5.0", "value", descriptor_mutations=(
        dsub("F5.0", "F2.0", "f5_0-to-f2_0", "'NAN()': F5.0 is NAN empty payload, F2.0 reads only 'NA'"),
    ))
    p.expect_true("ieee_class(value) == ieee_quiet_nan",
                  "ieee_class(value) /= ieee_quiet_nan", "nan-empty-quiet")


def build_infinity_output_wide(p):
    p.declare("real :: value")
    p.declare("character(len=9) :: field")
    p.assign_real("value", "ieee_value(0.0, ieee_positive_inf)", "0.0")
    p.set_buffer("field", "#########")
    p.write_stmt("field", "SS,F9.1", "value", descriptor_mutations=(
        dsub("F9.1", "F8.1", "f9_1-to-f8_1", "positive infinity: F9.1 is ' Infinity', F8.1 is 'Infinity'"),
        dsub("F9.1", "F4.1", "f9_1-to-f4_1", "positive infinity: F9.1 selects 'Infinity', F4.1 selects ' Inf'"),
    ), sign_mutation=True)
    p.expect_text("field", " Infinity", "inf-f9-1")


def build_infinity_output_narrow(p):
    p.declare("real :: value")
    p.declare("character(len=4) :: inf_field")
    p.declare("character(len=2) :: star_field")
    p.assign_real("value", "ieee_value(0.0, ieee_positive_inf)", "0.0")
    p.set_buffer("inf_field", "####")
    p.write_stmt("inf_field", "SS,F4.1", "value", descriptor_mutations=(
        dsub("F4.1", "F3.1", "f4_1-to-f3_1", "positive infinity: F4.1 is ' Inf', F3.1 is 'Inf'"),
    ), sign_mutation=True)
    p.expect_text("inf_field", " Inf", "inf-f4-1")
    p.set_buffer("star_field", "##")
    p.write_stmt("star_field", "SS,F2.1", "value", descriptor_mutations=(
        dsub("F2.1", "F3.1", "f2_1-to-f3_1", "positive infinity: F2.1 is '**', F3.1 is 'Inf'"),
    ))
    p.expect_text("star_field", "**", "inf-f2-1")


def build_nan_output_forced_widths(p):
    p.declare("real :: value")
    p.declare("character(len=5) :: right_field")
    p.declare("character(len=3) :: nan_field")
    p.declare("character(len=2) :: star_field")
    p.assign_real("value", "ieee_value(0.0, ieee_quiet_nan)", "0.0")
    p.set_buffer("right_field", "#####")
    p.write_stmt("right_field", "SS,F5.1", "value", descriptor_mutations=(
        dsub("F5.1", "F4.1", "f5_1-to-f4_1", "quiet NaN: F5.1 is '  NaN', F4.1 is ' NaN'"),
    ))
    p.expect_text("right_field", "  NaN", "nan-f5-1")
    p.set_buffer("nan_field", "###")
    p.write_stmt("nan_field", "SS,F0.1", "value", descriptor_mutations=(
        dsub("F0.1", "F4.1", "f0_1-to-f4_1", "quiet NaN: F0.1 is 'NaN', F4.1 needs four positions ' NaN' or a permitted payload"),
    ))
    p.expect_text("nan_field", "NaN", "nan-f0-1")
    p.set_buffer("star_field", "##")
    p.write_stmt("star_field", "SS,F2.1", "value", descriptor_mutations=(
        dsub("F2.1", "F3.1", "f2_1-to-f3_1", "quiet NaN: F2.1 is '**', F3.1 is 'NaN'"),
    ))
    p.expect_text("star_field", "**", "nan-f2-1")


def build_finite_output_sign(p):
    p.declare("real :: value")
    p.declare("character(len=5) :: field")
    p.assign_real("value", "-3.0", "-2.0")
    p.set_buffer("field", "#####")
    p.write_stmt("field", "SS,F5.1", "value", descriptor_mutations=(
        dsub("F5.1", "F6.1", "f5_1-to-f6_1", "-3.0: F5.1 is ' -3.0', F6.1 needs six positions '  -3.0'"),
        dsub("F5.1", "F5.2", "f5_1-to-f5_2", "-3.0: F5.1 is ' -3.0', F5.2 is '-3.00'"),
    ))
    p.expect_text("field", " -3.0", "minus-sign")


def build_finite_output_decimal_fraction(p):
    p.declare("real :: value")
    p.declare("character(len=5) :: field")
    p.assign_real("value", "1.25", "1.75")
    p.set_buffer("field", "#####")
    p.write_stmt("field", "SS,F5.2", "value", descriptor_mutations=(
        dsub("F5.2", "F5.3", "f5_2-to-f5_3", "1.25: F5.2 is ' 1.25', F5.3 is '1.250'"),
        dsub("F5.2", "E12.4", "f5_2-to-e12_4", "1.25: F5.2 fixed field differs from E12.4 exponent field"),
    ), sign_mutation=True)
    p.expect_text("field", " 1.25", "decimal-fraction")


def build_finite_output_leading_zero(p):
    p.declare("real :: value")
    p.declare("character(len=3) :: field")
    p.assign_real("value", "0.25", "1.25")
    p.set_buffer("field", "###")
    p.write_stmt("field", "SS,RZ,F3.0", "value", descriptor_mutations=(
        dsub("F3.0", "F2.0", "f3_0-to-f2_0", "0.25 with RZ and d=0: F3.0 is ' 0.', F2.0 is '0.'"),
    ), sign_mutation=True)
    p.expect_text("field", " 0.", "leading-zero")


def source_specs():
    specs = {}
    for case in CASES:
        program, source = make_program(case)
        raw = source.encode("ascii")
        name = identifier(case["variant"])
        specs[name] = dict(
            id=name, variant=case["variant"], rule=case["rule"], facets=list(case["facets"]),
            profiles=list(case.get("profiles", ())), section=case["section"], title=case["title"],
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
        directory = "tests/fixtures/f_editing_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        if spec["profiles"]:
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate F-editing fixture paragraph")
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
                                                   "F-editing fixture boundaries:", LIMIT_PARAGRAPH)
    return result


def summary_text():
    return (SUMMARY_BEGIN + "\n"
            "## Executable F editing fixtures\n\n"
            "This packet adds complete internal-file programs for 25 selected 13.7.2.3.2 F-editing facets. "
            "The fixtures use only exactly representable finite values or IEEE exceptional values under the "
            "ieee-binary profile, initialize character buffers with '#' sentinels, guard-check distinguished "
            "input target sentinels before READ, check LEN before every character equality, use SS for all "
            "positive output fields, and include permanent descriptor- and sentinel-substitution matrices whose "
            "alternatives differ on the selected values. Review state and execution approval remain integrator-owned.\n"
            + SUMMARY_END)


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
    return before.rstrip() + "\n\n" + summary_text() + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / F_CATALOGUE).read_text())
    updated_catalogue = synced_catalogue(catalogue, F_CATALOGUE)
    updated_view = render_view(updated_catalogue, F_SECTION, F_VIEW, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if json.loads((root / F_CATALOGUE).read_text()) != updated_catalogue:
            stale.append(F_CATALOGUE)
        if (root / F_VIEW).read_text() != updated_view:
            stale.append(F_VIEW)
        if stale:
            raise ValueError("stale F editing fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            (root / F_CATALOGUE).write_text(json.dumps(updated_catalogue, indent=2) + "\n")
            (root / F_VIEW).write_text(updated_view)
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
    work_dir = root / ".f_editing_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
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
    sign = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["mutation"] == "sign-mode-substitution")
    inputs = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "input")
    sentinels = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "sentinel-init")
    return len(specs), len(facets), mutations, descriptor, sign, inputs, sentinels


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
        sentinels = sum(row["category"] == "sentinel-init" for row in report)
        print(f"Mutation-checked {total} F-editing mutations: {descriptor} descriptor, {sign} sign, "
              f"{sentinels} sentinel-init; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count, descriptor_count, sign_count, input_count, sentinel_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} F editing cases, "
          f"{facet_count} facets and {mutation_count} mutations "
          f"({descriptor_count} descriptor, {sign_count} sign, {input_count} input, "
          f"{sentinel_count} sentinel-init).")


if __name__ == "__main__":
    main()
