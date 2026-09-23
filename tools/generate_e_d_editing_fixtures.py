#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 E and D real editing."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SECTION = "13.7.2.3.3"
CATALOGUE = "doc/catalogues/e_and_d_editing_13_7_2_3_3.json"
VIEW = "doc/fortran_2023_13_7_2_3_3.md"
SUMMARY_BEGIN = "<!-- BEGIN E D EDITING FIXTURES -->"
SUMMARY_END = "<!-- END E D EDITING FIXTURES -->"

HIGH_EXP_EXPECTED = "   " + "1" + "0" * 100 + ".0-100"
HIGH_EXP_CHUNKS = (HIGH_EXP_EXPECTED[:55], HIGH_EXP_EXPECTED[55:])

CASES = [
    dict(variant="field_width", rule="S13.7.2.3.3-001", facets=("E-D-field-width",),
         title="E output occupies the requested field width", builder="e_exact_output",
         descriptor="2P,E10.3E2", value="0.5", replacement_value="1.0", expected=" 50.00E-02",
         derivation="With k=2 and d=3, 0.5 is written as 50.00 with exponent -02 in exactly ten positions."),
    dict(variant="fractional_digits", rule="S13.7.2.3.3-001", facets=("E-D-fractional-digits",),
         title="E output fractional part has d digits", builder="e_exact_output",
         descriptor="1P,E9.2E2", value="1.0", replacement_value="2.0", expected=" 1.00E+00",
         derivation="With k=1 and d=2, the fractional part has exactly two digits, giving 1.00E+00 in a nine-position field."),
    dict(variant="exponent_digit_count", rule="S13.7.2.3.3-001", facets=("E-D-exponent-digit-count",),
         title="Explicit Ee fixes exponent digit count", builder="e_exact_output",
         descriptor="2P,E11.3E3", value="0.5", replacement_value="1.0", expected=" 50.00E-002",
         derivation="With explicit E3, the adjusted exponent -2 is written with exactly three exponent digits: E-002."),
    dict(variant="e_no_input_effect", rule="S13.7.2.3.3-001", facets=("E-D-e-no-input-effect",),
         title="Ee has no effect on input", builder="e_no_input_effect",
         derivation="The e part has no input effect, so E4.0E2 and E4.0 both read the exact field 1E+1 as 10.0."),
    dict(variant="input_same_as_f", rule="S13.7.2.3.3-002", facets=("E-D-input-same-as-F",),
         title="E and D input follow F input interpretation", builder="input_same_as_f",
         derivation="Because E/D input is interpreted as F input, E2.1 and D2.1 read an omitted decimal field 15 as exact 1.5."),
    dict(variant="ieee_output_same_as_f", rule="S13.7.2.3.3-003", facets=("E-D-ieee-output-same-as-F",),
         title="E and D infinity output follows F form", builder="ieee_output_same_as_f", profiles=("ieee-binary",),
         derivation="For IEEE positive infinity, E4.1 and D4.1 use the same forced F output form, right-justified Inf."),
    dict(variant="finite_normalized_form", rule="S13.7.2.3.3-004", facets=("E-D-finite-normalized-form",),
         title="Finite E output has normalized zero-scale form", builder="zero_scale_substring", replacement_value="2.0",
         check="field(3:10)", expected=".100E+01",
         derivation="With k=0, 1.0 has significand .100 and exponent E+01; the optional zero before the decimal is not asserted."),
    dict(variant="finite_decimal_symbol", rule="S13.7.2.3.3-004", facets=("E-D-finite-decimal-symbol",),
         title="Finite E output contains the decimal symbol", builder="zero_scale_substring", replacement_value="1.0e30",
         check="field(3:3)", expected=".",
         derivation="In POINT mode the decimal symbol in the k=0 E form appears immediately before the d digits; the optional leading zero is not asserted."),
    dict(variant="finite_d_digits", rule="S13.7.2.3.3-004", facets=("E-D-finite-d-digits",),
         title="Finite E output has d significant digits", builder="zero_scale_substring", replacement_value="2.0",
         check="field(4:6)", expected="100",
         derivation="For E10.3E2 of exact 1.0 at k=0, the three most significant rounded digits after the decimal are 100."),
    dict(variant="finite_exp_from_table", rule="S13.7.2.3.3-004", facets=("E-D-finite-exp-from-table",),
         title="Finite E output exponent comes from Table 13.1", builder="zero_scale_substring", replacement_value="0.5",
         check="field(7:10)", expected="E+01",
         derivation="The explicit E2 descriptor selects the Table 13.1 E+z1z2 exponent form; for 1.0 at k=0 the exponent is +01."),
    dict(variant="table_e_w_d_abs_le_99", rule="S13.7.2.3.3-005", facets=("table13_1_E_w_d_abs_le_99",),
         title="Ew.d exponent form for small exponent", builder="table_e_w_d_abs_le_99",
         derivation="For E10.3 without Ee, exponent +1 has one of the two Table 13.1 spellings E+01 or +001; both are accepted."),

    dict(variant="table_e_w_d_abs_100_to_999", rule="S13.7.2.3.3-005", facets=("table13_1_E_w_d_abs_100_to_999",),
         title="Ew.d exponent form for exponent magnitude 100", builder="table_high_exponent",
         descriptor="E110.101", value="1.0", replacement_value="2.0", expected=HIGH_EXP_EXPECTED,
         derivation="With 101P,E110.101, k=101 and d=101 give 101 significant digits left of the decimal, one digit right, and exponent -100 in the sign-plus-three-digit form."),
    dict(variant="table_e_w_d_ee_positive", rule="S13.7.2.3.3-005", facets=("table13_1_E_w_d_Ee_positive",),
         title="Ew.dEe exponent form with positive e", builder="e_exact_output",
         descriptor="2P,E10.3E2", value="0.5", replacement_value="1.0", expected=" 50.00E-02",
         derivation="For E10.3E2, the adjusted exponent -2 is within range and Table 13.1 requires E-02 with exactly two digits."),
    dict(variant="table_e0_or_e0_d", rule="S13.7.2.3.3-005", facets=("table13_1_E_E0_or_E0_d",),
         title="E0/E0.d uses minimum exponent digits", builder="e_exact_output",
         descriptor="1P,E0.3E0", value="1.0", replacement_value="2.0", expected="1.000E+0",
         derivation="For E0.3E0, w=0 selects the smallest field and E0 uses the minimum one digit for exponent zero."),
    dict(variant="table_d_w_d_abs_le_99", rule="S13.7.2.3.3-005", facets=("table13_1_D_w_d_abs_le_99",),
         title="Dw.d exponent form for small exponent", builder="table_d_w_d_abs_le_99",
         derivation="For D10.3 at k=1, Table 13.1 permits D+00, E+00, or +000; the fixture asserts only this permitted set."),

    dict(variant="table_d_w_d_abs_100_to_999", rule="S13.7.2.3.3-005", facets=("table13_1_D_w_d_abs_100_to_999",),
         title="Dw.d exponent form for exponent magnitude 100", builder="table_high_exponent",
         descriptor="D110.101", value="1.0", replacement_value="2.0", expected=HIGH_EXP_EXPECTED,
         derivation="With 101P,D110.101, k=101 and d=101 give 101 significant digits left of the decimal, one digit right, and exponent -100; Table 13.1 has no D/E-letter alternative for this magnitude row."),
    dict(variant="zero_exponent_plus", rule="S13.7.2.3.3-005", facets=("table13_1_zero_exponent_plus",),
         title="Zero exponent uses a plus sign", builder="zero_exponent_plus",
         derivation="With 1P,E0.3E0 of 1.0 the adjusted exponent is zero; Table 13.1 requires the exponent sign to be plus."),
    dict(variant="scale_negative_to_zero", rule="S13.7.2.3.3-006", facets=("E-D-scale-negative-to-zero-normalization",),
         title="Negative scale factor controls E normalization", builder="scale_negative",
         derivation="For -1P,E10.3E2, k=-1 gives one leading zero after the decimal and two following significant digits, with exponent +02."),
    dict(variant="scale_positive", rule="S13.7.2.3.3-006", facets=("E-D-scale-positive-normalization",),
         title="Positive scale factor controls E normalization", builder="e_exact_output",
         descriptor="1P,E10.3E2", value="1.0", replacement_value="2.0", expected=" 1.000E+00",
         derivation="For k=1 and d=3, there is one significant digit to the left of the decimal and three to the right, with exponent zero."),
]

CASE_BY_VARIANT = {case["variant"]: case for case in CASES}
LFORTRAN_HIGH_EXPONENT_DEFECTS = {"table_e_w_d_abs_100_to_999", "table_d_w_d_abs_100_to_999"}
SELECTED_FACETS_BY_RULE = {}
for case in CASES:
    SELECTED_FACETS_BY_RULE.setdefault(case["rule"], set()).update(case["facets"])

ORACLE_PARAGRAPHS = {
    "S13.7.2.3.3-001": (
        "S13.7.2.3.3-001 E/D-editing runtime fixtures: complete internal-file programs use exact default-real values, SS sign mode, and descriptors chosen to avoid processor latitude. "
        "(SS,2P,E10.3E2) of 0.5 expects ' 50.00E-02' and proves the ten-position field; (SS,1P,E9.2E2) expects ' 1.00E+00' and proves d=2 fractional digits; "
        "(SS,2P,E11.3E3) of 0.5 expects ' 50.00E-002' and proves explicit E3 exponent digits. A sentinel-guarded input fixture reads '1E+1' with E4.0E2 and E4.0 and requires both exact results to be 10.0, proving e has no input effect. Descriptor and sentinel substitutions are permanent and fail."),
    "S13.7.2.3.3-002": (
        "S13.7.2.3.3-002 E/D-input runtime fixture: a complete internal-file program initializes two real targets to distinguished sentinels, guard-checks those sentinels before READ, then reads the exact character field '15' using E2.1 and D2.1. Both results must be exact 1.5, following the F-input rule for an omitted decimal symbol and d=1. E2.1/D2.1 to E2.0/D2.0 substitutions, input-field substitutions, and sentinel-initialization probes fail."),
    "S13.7.2.3.3-003": (
        "S13.7.2.3.3-003 IEEE-output runtime fixture: under the ieee-binary profile, a complete program writes IEEE positive infinity with SS,E4.1, SS,D4.1, and SS,F4.1; each field must be the same right-justified F form ' Inf'. It also writes IEEE quiet NaN with SS,E5.1, SS,D5.1, and SS,F5.1; width 5 forces '  NaN' because no payload character can fit. Width substitutions to two-position fields produce asterisks and fail; no NaN payload or sign latitude is asserted."),
    "S13.7.2.3.3-004": (
        "S13.7.2.3.3-004 finite E-output runtime fixtures: complete internal-file programs write exact 1.0 with (SS,E10.3E2) at scale factor zero. Because 13.8.5 makes the zero immediately left of the decimal optional for E editing, fixtures assert only invariant slices: field(3:10)=='.100E+01', field(3:3)=='.', field(4:6)=='100', and field(7:10)=='E+01'. Right justification keeps these positions fixed whether the optional leading zero is printed or suppressed. Descriptor substitutions to ES, EN, F, changed d, and changed e fail."),
    "S13.7.2.3.3-005": (
        "S13.7.2.3.3-005 Table 13.1 runtime fixtures: E10.3 without Ee accepts exactly the two permitted small-exponent spellings E+01 and +001 after the invariant .100 significand; E110.101 and D110.101 with 101P on exact 1.0 expect the same 110-character field with three leading blanks, 101 significant digits to the left of the decimal symbol, one digit to the right, and exponent -100 in the sign-plus-three-digit form with no exponent letter; E10.3E2 via 2P on 0.5 expects E-02 with two exponent digits; E0.3E0 via 1P expects selected-width '1.000E+0' with the minimum one exponent digit; D10.3 via 1P accepts only the permitted D+00, E+00, or +000 alternatives; and the zero-exponent fixture separately checks the required plus sign. The D0.d row remains pending as described in the limitations."),
    "S13.7.2.3.3-006": (
        "S13.7.2.3.3-006 scale-factor runtime fixtures: (SS,-1P,E10.3E2) of exact 1.0 checks field(3:10)=='.010E+02', proving one leading zero after the decimal and two following significant digits without asserting the optional zero before the decimal. (SS,1P,E10.3E2) expects ' 1.000E+00', proving one significant digit left of the decimal and three to the right. Both k values satisfy -d<k<=0 or 0<k<d+2; the out-of-range restriction remains pending because this unit creates no required diagnostic."),
}

LIMIT_PARAGRAPH = (
    "E/D-editing fixture boundaries: this packet discharges only the selected 19 facets removed from pending above. It deliberately leaves the D0.d minimum-exponent row and the out-of-range scale-factor restriction pending. "
    "D exponent-letter alternatives are treated as latitude: D fixtures accept the permitted D/E/sign-only alternatives and do not use D<->E substitutions because Table 13.1 allows overlapping spellings. "
    "All finite positive output uses SS, exact binary values whose discarded decimal digits are zero, LEN-before-equality character checks, and # character sentinels. Input fixtures use distinguished nonzero sentinels, pre-READ guards, and sentinel-initialization probes."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    case = CASE_BY_VARIANT[variant]
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__e_d_editing_" + variant


def program_name(variant):
    return "ede_" + variant


def bare_descriptor(descriptor):
    return descriptor.split(",")[-1]


def field_width_from_descriptor(descriptor):
    bare = bare_descriptor(descriptor)
    digits = ""
    for ch in bare[1:]:
        if ch.isdigit():
            digits += ch
        else:
            break
    return int(digits)


class Program:
    def __init__(self, case):
        self.case = case
        self.variant = case["variant"]
        self.declarations = []
        self.body = []
        self.probes = []
        self.observations = []
        self.text = ""

    def render_prefix(self):
        covers = "".join(f"! covers: {facet}\n" for facet in self.case["facets"])
        use_line = "  use, intrinsic :: ieee_arithmetic\n" if self.case.get("profiles") else ""
        return (f"program {program_name(self.variant)}\n" + use_line +
                "  implicit none\n" +
                f"! rule: {self.case['rule']}\n" + covers +
                "  integer :: checks\n" +
                "\n".join(self.declarations) + ("\n" if self.declarations else "") +
                "  checks = 0\n")

    def completion_literal(self):
        return "E D EDITING " + self.variant.upper().replace("_", " ") + " OK"

    def render_suffix(self, total):
        completion = self.completion_literal()
        return (
            f"  if (checks /= {total}) then\n"
            f"    write(*,'(a)') 'EDE:{self.variant}:check-total'\n"
            "    error stop 1\n"
            "  end if\n"
            f"  write(*,'(a)') '{completion}'\n"
            "contains\n"
            "  subroutine expect_text(observed, expected, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'EDE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'EDE:text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_text\n"
            "  subroutine expect_one_of(observed, first, second, third, label)\n"
            "    character(len=*), intent(in) :: observed, first, second, third, label\n"
            "    if (len(observed) /= len(first) .or. len(observed) /= len(second) .or. len(observed) /= len(third)) then\n"
            "      write(*,'(a,1x,a)') 'EDE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= first .and. observed /= second .and. observed /= third) then\n"
            "      write(*,'(a,1x,a)') 'EDE:one-of', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_one_of\n"
            "  subroutine expect_either(observed, first, second, label)\n"
            "    character(len=*), intent(in) :: observed, first, second, label\n"
            "    if (len(observed) /= len(first) .or. len(observed) /= len(second)) then\n"
            "      write(*,'(a,1x,a)') 'EDE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= first .and. observed /= second) then\n"
            "      write(*,'(a,1x,a)') 'EDE:either', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_either\n"
            "  subroutine expect_real(observed, expected, label)\n"
            "    real, intent(in) :: observed, expected\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'EDE:real', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_real\n"
            "  subroutine expect_true(observed, label)\n"
            "    logical, intent(in) :: observed\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (.not. observed) then\n"
            "      write(*,'(a,1x,a)') 'EDE:logical', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_true\n"
            f"end program {program_name(self.variant)}\n")

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
                     failure_stdout=failure_stdout if failure_stdout is not None else f"EDE:{self.variant}")
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

    def init_real(self, name, sentinel, expected_after_read, label):
        line = f"  {name} = {sentinel}\n"
        start = self.current_length()
        for suffix, replacement, note in (
            ("remove", "", f"{name}: removing the distinguished sentinel leaves the pre-READ guard unestablished"),
            ("expected", f"  {name} = {expected_after_read}\n", f"{name}: initializing to the expected READ result would make a missing READ vacuous"),
            ("zero", f"  {name} = 0.0\n", f"{name}: zero is distinguishable from the sentinel and expected value"),
        ):
            self.probes.append(dict(
                id=f"sentinel-{label}-{suffix}", kind="source", category="sentinel-init",
                mutation="sentinel-initialization-" + suffix, span=[start, start + len(line)],
                expected=line, replacement=replacement, failure_stdout=f"EDE:real {label}\n",
                discriminant=note))
        self.add(line)
        self.expect_real(name, sentinel, "0.0", label)

    def set_buffer(self, name, width):
        self.add(f"  {name} = '{'#' * width}'\n")

    def write_stmt(self, buf, fmt, value_name, descriptor_mutations=(), sign_mutation=True):
        line = f"  write({buf},'({fmt})') {value_name}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        if sign_mutation:
            self.mutate_span_in_next(line, "SS", "SP", f"sign-{buf}", "sign-mode-substitution", "sign")
        self.add(line)

    def read_stmt(self, field, fmt, out_var, descriptor_mutations=()):
        line = f"  read({field},'({fmt})') {out_var}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def expect_text(self, observed, expected, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_text({observed}, '{expected}', '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "text-oracle", "oracle",
                                 f"EDE:text {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_one_of(self, observed, first, second, third, label):
        line = f"  call expect_one_of({observed}, '{first}', '{second}', '{third}', '{label}')\n"
        self.mutate_span_in_next(line, first, corrupt_text(first), f"oracle-{label}-first", "one-of-oracle", "oracle",
                                 f"EDE:one-of {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_either(self, observed, first, second, label):
        line = f"  call expect_either({observed}, '{first}', '{second}', '{label}')\n"
        self.mutate_span_in_next(line, first, corrupt_text(first), f"oracle-{label}-first", "either-oracle", "oracle",
                                 f"EDE:either {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_real(self, var, expected, replacement, label):
        line = f"  call expect_real({var}, {expected}, '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "real-oracle", "oracle",
                                 f"EDE:real {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_true(self, expression, replacement, label):
        line = f"  call expect_true({expression}, '{label}')\n"
        self.mutate_span_in_next(line, expression, replacement, f"oracle-{label}", "logical-oracle", "oracle",
                                 f"EDE:logical {label}\n")
        self.add(line)
        self.observations.append(label)

    def source(self):
        prefix = self.render_prefix()
        body = "".join(self.body)
        total = len(self.observations)
        suffix_start = len(prefix) + len(body)
        suffix = self.render_suffix(total)
        self.text = prefix + body + suffix
        needle = f"checks /= {total}"
        start = suffix_start + suffix.index(needle)
        self.probes.append(dict(id="reverse-check-total", kind="reverse", category="sentinel",
                                mutation="reverse-total-sentinel",
                                span=[start + len("checks "), start + len("checks ") + len("/=")],
                                expected="/=", replacement="==",
                                failure_stdout=f"EDE:{self.variant}:check-total\n"))
        literal = self.completion_literal()
        marker = f"write(*,'(a)') '{literal}'"
        start = suffix_start + suffix.index(marker) + marker.index(literal)
        self.probes.append(dict(id="oracle-completion", kind="output", category="oracle",
                                mutation="completion-literal",
                                span=[start, start + len(literal)], expected=literal,
                                replacement=literal.replace(" OK", " BAD"), failure_stdout=""))
        raw = self.text.encode("ascii")
        for probe in self.probes:
            lo, hi = probe["span"]
            if raw[lo:hi].decode("ascii") != probe["expected"]:
                raise ValueError(f"probe span lost complete-parent binding: {self.variant}:{probe['id']}")
        return self.text


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


def common_e_mutations(descriptor, value):
    bare = bare_descriptor(descriptor)
    mutations = []
    if bare.startswith("E") and "E" in bare[1:] and not descriptor.startswith("1P,"):
        mutations.append(dsub(bare, "ES" + bare[1:], "e-to-es", f"{value}: ES scientific form differs from E editing"))
        mutations.append(dsub(bare, "EN" + bare[1:], "e-to-en", f"{value}: EN engineering form differs from E editing"))
    if bare.startswith("E"):
        mutations.append(dsub(bare, "F" + bare[1:].split("E")[0], "e-to-f", f"{value}: F editing has no exponent field"))
        head, rest = bare[1:].split(".", 1)
        d_part, e_part = rest.split("E", 1) if "E" in rest else (rest, "")
        width = int(head)
        d_value = int(d_part)
        if width > 0:
            mutations.append(dsub(bare, f"E{width - 1}.{d_part}" + (f"E{e_part}" if e_part else ""),
                                  "e-width", f"{value}: changing w shifts or overflows the E field"))
        other_d = d_value - 1 if d_value > 0 else d_value + 1
        mutations.append(dsub(bare, f"E{head}.{other_d}" + (f"E{e_part}" if e_part else ""),
                              "e-digits", f"{value}: changing d changes the significand digit count"))
        if e_part and int(e_part) > 0:
            other_e = int(e_part) - 1 if int(e_part) > 1 else int(e_part) + 1
            mutations.append(dsub(bare, f"E{head}.{d_part}E{other_e}",
                                  "e-exp-digits", f"{value}: changing e changes the exponent digit count"))
    return tuple(mutations)


def build_e_exact_output(p):
    case = p.case
    width = field_width_from_descriptor(case["descriptor"]) or len(case["expected"])
    p.declare("real :: value")
    p.declare(f"character(len={width}) :: field")
    p.assign_real("value", case["value"], case["replacement_value"])
    p.set_buffer("field", width)
    p.write_stmt("field", "SS," + case["descriptor"], "value",
                 descriptor_mutations=common_e_mutations(case["descriptor"], case["value"]),
                 sign_mutation=True)
    p.expect_text("field", case["expected"], "field")


def build_e_no_input_effect(p):
    p.declare("character(len=4) :: field")
    p.declare("real :: with_e, without_e")
    p.assign_character("field", "1E+1", "1E+2")
    p.init_real("with_e", "-99.0", "10.0", "sentinel-with-e")
    p.init_real("without_e", "-88.0", "10.0", "sentinel-without-e")
    p.read_stmt("field", "E4.0E2", "with_e", descriptor_mutations=(
        dsub("E4.0E2", "E4.1E2", "e4_0e2-to-e4_1e2", "'1E+1': E4.0E2 gives 10.0, E4.1E2 gives 1.0"),
    ))
    p.read_stmt("field", "E4.0", "without_e", descriptor_mutations=(
        dsub("E4.0", "E4.1", "e4_0-to-e4_1", "'1E+1': E4.0 gives 10.0, E4.1 gives 1.0"),
    ))
    p.expect_real("with_e", "10.0", "11.0", "with-e")
    p.expect_real("without_e", "10.0", "11.0", "without-e")
    p.expect_true("with_e == without_e", "with_e /= without_e", "e-no-effect")


def build_input_same_as_f(p):
    p.declare("character(len=2) :: field")
    p.declare("real :: e_value, d_value")
    p.assign_character("field", "15", "25")
    p.init_real("e_value", "-99.0", "1.5", "sentinel-e-input")
    p.init_real("d_value", "-88.0", "1.5", "sentinel-d-input")
    p.read_stmt("field", "E2.1", "e_value", descriptor_mutations=(
        dsub("E2.1", "E2.0", "e2_1-to-e2_0", "'15': E2.1 follows F input as 1.5, while E2.0 gives 15.0"),
    ))
    p.read_stmt("field", "D2.1", "d_value", descriptor_mutations=(
        dsub("D2.1", "D2.0", "d2_1-to-d2_0", "'15': D2.1 follows F input as 1.5, while D2.0 gives 15.0"),
    ))
    p.expect_real("e_value", "1.5", "2.5", "e-input")
    p.expect_real("d_value", "1.5", "2.5", "d-input")
    p.expect_true("e_value == d_value", "e_value /= d_value", "e-d-input-same")


def build_ieee_output_same_as_f(p):
    p.declare("real :: value, nan_value")
    p.declare("character(len=4) :: e_field, d_field, f_field")
    p.declare("character(len=5) :: e_nan, d_nan, f_nan")
    p.assign_real("value", "ieee_value(0.0, ieee_positive_inf)", "0.0")
    p.assign_real("nan_value", "ieee_value(0.0, ieee_quiet_nan)", "0.0")
    for name, desc in (("e_field", "E4.1"), ("d_field", "D4.1"), ("f_field", "F4.1")):
        p.set_buffer(name, 4)
        p.write_stmt(name, "SS," + desc, "value", descriptor_mutations=(
            dsub(desc, desc[0] + "2.1", desc.lower().replace('.', '_') + "-to-" + desc[0].lower() + "2_1",
                 "positive infinity: width 4 gives ' Inf', width 2 gives '**'"),
        ), sign_mutation=True)
        p.expect_text(name, " Inf", name.replace("_field", "-inf"))
    for name, desc in (("e_nan", "E5.1"), ("d_nan", "D5.1"), ("f_nan", "F5.1")):
        p.set_buffer(name, 5)
        p.write_stmt(name, "SS," + desc, "nan_value", descriptor_mutations=(
            dsub(desc, desc[0] + "2.1", desc.lower().replace('.', '_') + "-to-" + desc[0].lower() + "2_1",
                 "quiet NaN: width 5 gives '  NaN', width 2 gives '**'"),
        ), sign_mutation=False)
        p.expect_text(name, "  NaN", name.replace("_nan", "-nan"))
    p.expect_true("e_field == f_field", "e_field /= f_field", "e-same-f")
    p.expect_true("d_field == f_field", "d_field /= f_field", "d-same-f")
    p.expect_true("e_nan == f_nan", "e_nan /= f_nan", "e-nan-same-f")
    p.expect_true("d_nan == f_nan", "d_nan /= f_nan", "d-nan-same-f")


def zero_scale_common(p):
    p.declare("real :: value")
    p.declare("character(len=10) :: field")
    if p.variant == "finite_decimal_symbol":
        p.add("  value = 1.0\n")
    else:
        p.assign_real("value", "1.0", p.case["replacement_value"])
    p.set_buffer("field", 10)
    mutations = [
        dsub("E10.3E2", "F10.3", "e-to-f", "1.0: F editing has no exponent field"),
    ]
    if p.variant != "finite_decimal_symbol":
        mutations.extend([
            dsub("E10.3E2", "ES10.3E2", "e-to-es", "1.0: E field has .100E+01, ES field has 1.000E+00"),
            dsub("E10.3E2", "EN10.3E2", "e-to-en", "1.0: E field has exponent +01, EN field has exponent +00"),
            dsub("E10.3E2", "E10.3E1", "e-exp-digits", "1.0: changing e changes exponent digit count and field layout"),
        ])
        if p.variant != "finite_exp_from_table":
            mutations.append(dsub("E10.3E2", "E10.2E2", "e-digits",
                                  "1.0: changing d removes one significand digit"))
    p.write_stmt("field", "SS,E10.3E2", "value", descriptor_mutations=tuple(mutations), sign_mutation=False)


def build_zero_scale_substring(p):
    zero_scale_common(p)
    p.expect_text(p.case["check"], p.case["expected"], "slice")


def build_table_e_w_d_abs_le_99(p):
    p.declare("real :: value")
    p.declare("character(len=10) :: field")
    p.assign_real("value", "1.0", "2.0")
    p.set_buffer("field", 10)
    p.write_stmt("field", "SS,E10.3", "value", descriptor_mutations=(
        dsub("E10.3", "ES10.3", "e-to-es", "1.0: ES scientific form differs from E's zero-scale significand"),
        dsub("E10.3", "EN10.3", "e-to-en", "1.0: EN engineering form differs from E's exponent"),
        dsub("E10.3", "F10.3", "e-to-f", "1.0: F editing has no exponent field"),
    ), sign_mutation=False)
    p.expect_text("field(3:6)", ".100", "significand")
    p.expect_either("field(7:10)", "E+01", "+001", "exponent")


def build_table_high_exponent(p):
    case = p.case
    desc = case["descriptor"]
    width = field_width_from_descriptor(desc)
    kind = desc[0]
    p.declare("real :: value")
    p.declare(f"character(len={width}) :: field")
    p.assign_real("value", case["value"], case["replacement_value"])
    p.set_buffer("field", width)
    p.write_stmt("field", "SS,101P," + desc, "value", descriptor_mutations=(
        dsub("101P", "100P", "scale-101p-to-100p",
             "1.0: 101P gives exponent -100 in the sign-plus-three-digit form, while 100P gives magnitude 99"),
        dsub(desc, kind + "109.101", kind.lower() + "-width-110-to-109",
             "1.0: reducing w leaves too little room for the high-exponent field"),
        dsub(desc, kind + "110.100", kind.lower() + "-d-101-to-100",
             "1.0: reducing d changes the positive-scale digit counts"),
        dsub(desc, "F110.101", kind.lower() + "-to-f",
             "1.0: F editing under 101P has no E/D high-exponent suffix"),
    ), sign_mutation=True)
    p.expect_text("field(1:55)", HIGH_EXP_CHUNKS[0], "field-first")
    p.expect_text("field(56:110)", HIGH_EXP_CHUNKS[1], "field-second")
    p.expect_text("field(107:110)", "-100", "exponent")


def build_table_d_w_d_abs_le_99(p):
    p.declare("real :: value")
    p.declare("character(len=10) :: field")
    p.assign_real("value", "1.0", "2.0")
    p.set_buffer("field", 10)
    p.write_stmt("field", "SS,1P,D10.3", "value", descriptor_mutations=(
        dsub("D10.3", "F10.3", "d-to-f", "1.0: F editing has no D/E/sign-only exponent field"),
        dsub("D10.3", "D9.3", "d-width", "1.0: D9.3 shifts the field because D10.3 has one leading blank"),
        dsub("D10.3", "D10.2", "d-digits", "1.0: D10.2 changes the number of fractional digits"),
    ), sign_mutation=False)
    p.expect_text("field(2:6)", "1.000", "significand")
    p.expect_one_of("field(7:10)", "D+00", "E+00", "+000", "exponent")


def build_zero_exponent_plus(p):
    p.declare("real :: value")
    p.declare("character(len=8) :: field")
    p.assign_real("value", "1.0", "2.0")
    p.set_buffer("field", 8)
    p.write_stmt("field", "SS,1P,E0.3E0", "value", descriptor_mutations=(
        dsub("E0.3E0", "F0.3", "e-to-f", "1.0: F editing has no exponent sign"),
        dsub("E0.3E0", "E0.2E0", "e-digits", "1.0: changing d shortens the selected-width field"),
    ), sign_mutation=False)
    p.expect_text("field", "1.000E+0", "field")
    p.expect_text("field(7:7)", "+", "exponent-sign")


def build_scale_negative(p):
    p.declare("real :: value")
    p.declare("character(len=10) :: field")
    p.assign_real("value", "1.0", "2.0")
    p.set_buffer("field", 10)
    p.write_stmt("field", "SS,-1P,E10.3E2", "value", descriptor_mutations=(
        dsub("-1P", "0P", "minus-one-p-to-zero-p", "1.0: -1P gives .010E+02, while 0P gives .100E+01"),
        dsub("E10.3E2", "E10.2E2", "e-digits", "1.0: changing d removes one fractional digit"),
        dsub("E10.3E2", "F10.3", "e-to-f", "1.0: F editing has no exponent field"),
    ), sign_mutation=False)
    p.expect_text("field(3:10)", ".010E+02", "scaled")


def make_program(case):
    p = Program(case)
    getattr(sys.modules[__name__], "build_" + case["builder"])(p)
    return p, p.source()


def source_specs():
    specs = {}
    for case in CASES:
        program, source = make_program(case)
        raw = source.encode("ascii")
        name = identifier(case["variant"])
        specs[name] = dict(id=name, variant=case["variant"], rule=case["rule"], facets=list(case["facets"]),
                           profiles=list(case.get("profiles", ())), section=SECTION, title=case["title"],
                           descriptor=case.get("descriptor", ""), input_value=case.get("value", ""),
                           expected=case.get("expected", ""), derivation=case["derivation"],
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
        directory = "tests/fixtures/e_d_editing_" + spec["variant"]
        evidence = "positive-control" if spec["rule"] == "S13.7.2.3.3-006" else "effect"
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence=evidence,
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
        raise ValueError("duplicate E/D fixture paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    for rule, facets in SELECTED_FACETS_BY_RULE.items():
        rows = [row for row in result["requirements"] if row["id"] == rule]
        if len(rows) != 1:
            raise ValueError(f"selected requirement {rule} changed")
        row = rows[0]
        if not facets <= set(row["facets"]):
            raise ValueError(f"selected facets for {rule} changed")
        for facet in sorted(facets):
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), rule + " ", ORACLE_PARAGRAPHS[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""),
                                                   "E/D-editing fixture boundaries:", LIMIT_PARAGRAPH)
    return result


def summary_text():
    return (SUMMARY_BEGIN + "\n"
            "## Executable E and D editing fixtures\n\n"
            "This packet adds complete internal-file programs for selected 13.7.2.3.3 E/D-editing facets. "
            "They use exact binary values, SS on positive output, # output sentinels, LEN-before-equality checks, "
            "pre-READ guards for input sentinels, and descriptor/sentinel mutation probes. Optional leading-zero "
            "positions and D exponent-letter alternatives are never asserted.\n"
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
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated_catalogue = synced_catalogue(catalogue)
    updated_view = render_view(updated_catalogue, SECTION, VIEW, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if json.loads((root / CATALOGUE).read_text()) != updated_catalogue:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != updated_view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale E/D editing fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            (root / CATALOGUE).write_text(json.dumps(updated_catalogue, indent=2) + "\n")
            (root / VIEW).write_text(updated_view)
    return specs


def compiler_command(compiler, std, source, output):
    command = [str(compiler)]
    name = Path(compiler).name.lower()
    if std:
        command.append(("--std=" if "lfortran" in name else "-std=") + std)
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
    work_dir = root / ".e_d_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    try:
        report = []
        for spec in specs.values():
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["completion"], spec["variant"] + "_parent")
            parent_ok = parent["status"] == "pass"
            known_parent_defect = "lfortran" in Path(compiler).name.lower() and spec["variant"] in LFORTRAN_HIGH_EXPONENT_DEFECTS
            for index, probe in enumerate(spec["probes"]):
                mutant_source = wrong_oracle_source(spec, probe).decode("ascii")
                observed = run_one_source(compiler, std, work_dir, mutant_source, spec["completion"],
                                          f"{spec['variant']}_mut_{index:03d}")
                failed = not (observed["status"] == "pass")
                report.append(dict(variant=spec["variant"], probe=probe["id"], mutation=probe["mutation"],
                                   category=probe["category"], expected=probe["expected"],
                                   replacement=probe["replacement"], discriminant=probe.get("discriminant", ""),
                                   parent_ok=parent_ok, known_parent_defect=known_parent_defect,
                                   failed=failed, status=observed["status"],
                                   stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"]))
        bad = [row for row in report if (not row["parent_ok"] and not row["known_parent_defect"]) or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:8], indent=2))
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


def mutation_matrix(report):
    matrix = {}
    for row in report:
        if row["mutation"] == "descriptor-substitution":
            key = (row["expected"], row["replacement"])
            matrix[key] = matrix.get(key, 0) + 1
    return matrix


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
        descriptor = sum(row["mutation"] == "descriptor-substitution" for row in report)
        sign = sum(row["mutation"] == "sign-mode-substitution" for row in report)
        sentinels = sum(row["category"] == "sentinel-init" for row in report)
        parent_defects = sorted({row["variant"] for row in report if row.get("known_parent_defect") and not row["parent_ok"]})
        matrix = mutation_matrix(report)
        pairs = ", ".join(f"{old}->{new}:{count}" for (old, new), count in sorted(matrix.items()))
        print(f"Mutation-checked {len(report)} E/D mutations: {descriptor} descriptor, {sign} sign, {sentinels} sentinel-init; all failed.")
        if parent_defects:
            print("Known LFortran parent failures retained: " + ", ".join(parent_defects))
        print("Descriptor matrix: " + pairs)
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count, descriptor_count, sign_count, input_count, sentinel_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} E/D editing cases, "
          f"{facet_count} facets and {mutation_count} mutations "
          f"({descriptor_count} descriptor, {sign_count} sign, {input_count} input, {sentinel_count} sentinel-init).")


if __name__ == "__main__":
    main()
