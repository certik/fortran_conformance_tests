#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.121-16.9.127 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_p"
SECTIONS = ("16.9.121", "16.9.122", "16.9.123", "16.9.124", "16.9.125", "16.9.126", "16.9.127")
CATALOGUES = {
    "16.9.121": "doc/catalogues/leadz_16_9_121.json",
    "16.9.122": "doc/catalogues/len_intrinsic_16_9_122.json",
    "16.9.123": "doc/catalogues/len_trim_16_9_123.json",
    "16.9.124": "doc/catalogues/lge_intrinsic_16_9_124.json",
    "16.9.125": "doc/catalogues/lgt_intrinsic_16_9_125.json",
    "16.9.126": "doc/catalogues/lle_intrinsic_16_9_126.json",
    "16.9.127": "doc/catalogues/llt_intrinsic_16_9_127.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.P FIXTURES {section} -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.P FIXTURES {section} -->"
REMAINING_PENDING = {
    "S16.9.124-004": {
        "LGE-non-ASCII-result-processor-dependent":
            "Left pending by intrinsics_16_9_p: p5 makes the truth value processor dependent whenever either operand contains a non-ASCII character."
    },
    "S16.9.125-004": {
        "LGT-non-ASCII-result-processor-dependent":
            "Left pending by intrinsics_16_9_p: p5 makes the truth value processor dependent whenever either operand contains a non-ASCII character."
    },
    "S16.9.126-004": {
        "LLE-non-ASCII-result-processor-dependent":
            "Left pending by intrinsics_16_9_p: p5 makes the truth value processor dependent whenever either operand contains a non-ASCII character."
    },
    "S16.9.127-004": {
        "LLT-non-ASCII-result-processor-dependent":
            "Left pending by intrinsics_16_9_p: p5 makes the truth value processor dependent whenever either operand contains a non-ASCII character."
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace(".", "_").replace("-", "_") + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Case:
    section: str
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[tuple[str, str, str], ...]
    oracle: str
    profiles: tuple[str, ...] = ()

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.P " + self.variant.upper().replace("_", " ") + " OK\n"


HELPERS = """contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program {program}
"""


def wrap(variant: str, declarations: str, body: str) -> str:
    program = "i169p_" + variant
    return (
        f"program {program}\n"
        "  implicit none\n"
        + declarations
        + body
        + f"  write(*,'(a)') 'INTRINSICS 16.9.P {variant.upper().replace('_', ' ')} OK'\n"
        + HELPERS.format(program=program)
    )


def leadz_arguments_source():
    return wrap("leadz_integer_argument", "  integer :: integer_actual\n",
        "  integer_actual = 0\n"
        "  call require_true('leadz accepts integer actual', leadz(integer_actual) == bit_size(integer_actual))\n")


def leadz_result_kind_source():
    return wrap("leadz_result_kind", "  integer, parameter :: alt_ik = merge(8, 4, kind(0) /= 8)\n  integer :: one\n",
        "  one = 1\n"
        "  call require_true('leadz result default integer kind', kind(leadz(one)) == kind(0))\n")


def leadz_values_source():
    return wrap("leadz_values", "  integer :: zero\n  integer :: one\n",
        "  zero = 0\n"
        "  one = 1\n"
        "  call require_true('all zero bits return bit size', leadz(zero) == bit_size(zero))\n"
        "  call require_true('one low bit counts leading zeros', leadz(one) == bit_size(one) - 1)\n"
        "  call require_true('leftmost one bit has zero leading zeros', &\n"
        "       leadz(ibset(0, bit_size(0) - 1)) == 0)\n"
        "  call require_true('all one bits have zero leading zeros', leadz(not(0)) == 0)\n")


def len_arguments_source():
    return wrap("len_argument_controls",
        "  integer, parameter :: wide_kind = selected_int_kind(18)\n"
        "  character(len=5) :: scalar = 'AB'\n"
        "  character(len=6), allocatable :: unallocated_fixed\n"
        "  character(len=4), pointer :: unassociated_fixed => null()\n",
        "  call require_true('len accepts character string argument', len(scalar) == 5)\n"
        "  call require_true('len permits nondeferred absent allocation association', &\n"
        "       len(unallocated_fixed) == 6 .and. len(unassociated_fixed) == 4)\n"
        "  call require_true('len kind argument is scalar integer constant', &\n"
        "       kind(len(scalar, kind=wide_kind)) == wide_kind)\n")


def len_characteristics_source():
    return wrap("len_characteristics",
        "  integer, parameter :: wide_kind = selected_int_kind(18)\n"
        "  character(len=3) :: words(2) = [character(len=3) :: 'ab', 'cd']\n",
        "  call require_true('len result is scalar for array string', rank(len(words)) == 0)\n"
        "  call require_true('len result kind follows kind argument or default', &\n"
        "       kind(len(words)) == kind(0) .and. kind(len(words, kind=wide_kind)) == wide_kind)\n")


def len_values_source():
    return wrap("len_values",
        "  character(len=5) :: padded = 'AB'\n"
        "  character(len=3) :: words(2) = [character(len=3) :: 'abc', 'xy']\n"
        "  character(len=0) :: empty = ''\n"
        "  character(len=:), allocatable :: allocated_s\n"
        "  character(len=7), target :: target_s = 'ABCDEFG'\n"
        "  character(len=:), pointer :: pointer_s\n",
        "  allocate(character(len=7) :: allocated_s)\n"
        "  pointer_s => target_s\n"
        "  call require_true('len scalar character length', len(padded) == 5)\n"
        "  call require_true('len array element character length', len(words) == 3)\n"
        "  call require_true('len zero length character', len(empty) == 0)\n"
        "  call require_true('len allocated deferred length character', len(allocated_s) == 7)\n"
        "  call require_true('len associated deferred pointer length', len(pointer_s) == 7)\n")


def len_trim_arguments_source():
    return wrap("len_trim_argument_controls",
        "  integer, parameter :: wide_kind = selected_int_kind(18)\n"
        "  character(len=5) :: scalar = 'A B'\n",
        "  call require_true('len_trim accepts character string argument', len_trim(scalar) == 3)\n"
        "  call require_true('len_trim kind argument is scalar integer constant', &\n"
        "       kind(len_trim(scalar, kind=wide_kind)) == wide_kind)\n")


def len_trim_characteristics_source():
    return wrap("len_trim_characteristics",
        "  integer, parameter :: wide_kind = selected_int_kind(18)\n"
        "  character(len=4) :: scalar = 'A'\n",
        "  call require_true('len_trim result is integer scalar', len_trim(scalar) == 1)\n"
        "  call require_true('len_trim result kind follows kind argument or default', &\n"
        "       kind(len_trim(scalar)) == kind(0) .and. kind(len_trim(scalar, kind=wide_kind)) == wide_kind)\n")


def len_trim_values_source():
    return wrap("len_trim_values",
        "  character(len=5) :: trailing = 'AB'\n"
        "  character(len=5) :: internal = 'A B'\n"
        "  character(len=3) :: blanks = '   '\n"
        "  character(len=3) :: companion = ' A '\n",
        "  call require_true('len_trim removes trailing blanks', len_trim(trailing) == 2)\n"
        "  call require_true('len_trim preserves internal blanks', len_trim(internal) == 3)\n"
        "  call require_true('len_trim all blank string zero', &\n"
        "       len_trim(blanks) == 0 .and. len_trim(companion) == 2)\n")


def char_argument_source(intr: str, true_left: str, true_right: str):
    variant = intr + "_argument_controls"
    return wrap(variant,
        f"  character(len=1) :: string_a = '{true_left}'\n"
        f"  character(len=1) :: string_b = '{true_right}'\n"
        f"  character(kind=kind('A'), len=1) :: same_a = '{true_left}'\n"
        f"  character(kind=kind('A'), len=1) :: same_b = '{true_right}'\n",
        f"  call require_true('{intr} accepts default ascii string_a', {intr}(string_a, string_b))\n"
        f"  call require_true('{intr} uses same-kind character operands', {intr}(same_a, same_b))\n")


def char_result_kind_source(intr: str, left: str, right: str):
    return wrap(intr + "_result_kind",
        "  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)\n",
        f"  call require_true('{intr} result default logical kind', kind({intr}('{left}', '{right}')) == kind(.false.))\n")


def ge_gt_padding_source(intr: str):
    return wrap(intr + "_blank_padding",
        "  character(len=1) :: short_a = 'A'\n"
        "  character(len=2) :: a_exclaim = 'A!'\n",
        f"  call require_true('{intr} blank padding lengths shorter left', &\n"
        "       len(short_a) == 1 .and. len(a_exclaim) == 2)\n"
        f"  call require_false('{intr} blank padding shorter left', {intr}(short_a, a_exclaim))\n"
        f"  call require_true('{intr} blank padding shorter right', {intr}(a_exclaim, short_a))\n")


def ge_gt_order_source(intr: str):
    return wrap(intr + "_ascii_order",
        "  character(len=2) :: eq_a = 'Az'\n"
        "  character(len=2) :: eq_b = 'Az'\n"
        "  character(len=1) :: digit = '9'\n"
        "  character(len=1) :: upper_a = 'A'\n"
        "  character(len=1) :: upper_z = 'Z'\n"
        "  character(len=1) :: underscore = '_'\n"
        "  character(len=1) :: lower_a = 'a'\n",
        f"  call require_{'true' if intr == 'lge' else 'false'}('{intr} equal strings {'true' if intr == 'lge' else 'false'}', {intr}(eq_a, eq_b))\n"
        f"  call require_true('{intr} ascii following true', &\n"
        f"       {intr}(upper_a, digit) .and. {intr}(lower_a, upper_z) .and. &\n"
        f"       {intr}(lower_a, upper_a) .and. {intr}(underscore, upper_z))\n"
        f"  call require_false('{intr} ascii preceding false', &\n"
        f"       {intr}(digit, upper_a) .or. {intr}(upper_z, lower_a) .or. &\n"
        f"       {intr}(upper_a, lower_a) .or. {intr}(upper_z, underscore))\n")


def le_lt_values_source(intr: str):
    return wrap(intr + "_ascii_values",
        "  character(len=1) :: short_a = 'A'\n"
        "  character(len=2) :: a_blank = 'A '\n"
        "  character(len=2) :: a_exclaim = 'A!'\n"
        "  character(len=2) :: eq_a = 'AZ'\n"
        "  character(len=2) :: eq_b = 'AZ'\n"
        "  character(len=0) :: empty_a = ''\n"
        "  character(len=0) :: empty_b = ''\n"
        "  character(len=1) :: digit = '9'\n"
        "  character(len=1) :: upper_a = 'A'\n"
        "  character(len=1) :: upper_z = 'Z'\n"
        "  character(len=1) :: underscore = '_'\n"
        "  character(len=1) :: lower_a = 'a'\n"
        "  character(len=3) :: one = 'ONE'\n"
        "  character(len=3) :: two = 'TWO'\n",
        f"  call require_true('{intr} blank padding lengths', &\n"
        "       len(short_a) == 1 .and. len(a_blank) == 2 .and. len(a_exclaim) == 2)\n"
        + (f"  call require_true('{intr} shorter left pads equal', {intr}(short_a, a_blank))\n"
           f"  call require_false('{intr} exclaim follows padded blank', {intr}(a_exclaim, a_blank))\n"
           if intr == "lle" else
           f"  call require_true('{intr} shorter left precedes exclaim', {intr}(short_a, a_exclaim))\n"
           f"  call require_false('{intr} padded equality false', {intr}(short_a, a_blank))\n")
        + f"  call require_{'true' if intr == 'lle' else 'false'}('{intr} equal nonempty strings {'true' if intr == 'lle' else 'false'}', &\n"
        f"       {intr}(eq_a, eq_b))\n"
        f"  call require_{'true' if intr == 'lle' else 'false'}('{intr} equal zero length strings {'true' if intr == 'lle' else 'false'}', &\n"
        f"       {intr}(empty_a, empty_b))\n"
        f"  call require_true('{intr} ascii precedes true', &\n"
        f"       {intr}(digit, upper_a) .and. {intr}(upper_a, lower_a) .and. &\n"
        f"       {intr}(upper_z, lower_a) .and. {intr}(upper_z, underscore) .and. {intr}(one, two))\n"
        f"  call require_false('{intr} ascii follows false', &\n"
        f"       {intr}(upper_a, digit) .or. {intr}(lower_a, upper_a) .or. &\n"
        f"       {intr}(lower_a, upper_z) .or. {intr}(underscore, upper_z))\n")


def make_cases():
    cases = []

    def add(section, variant, rule, facets, evidence, source, mutations, oracle, profiles=()):
        cases.append(Case(section, variant, rule, tuple(facets), evidence, source, tuple(mutations), oracle, tuple(profiles)))

    add("16.9.121", "leadz_integer_argument", "S16.9.121-001", ["LEADZ-I-integer"], "positive-control",
        leadz_arguments_source(),
        [("integer-actual-feature", "integer_actual = 0", "integer_actual = 1")],
        "LEADZ is called with an integer actual argument; the zero-bit result is checked against BIT_SIZE of that argument.")
    add("16.9.121", "leadz_result_kind", "S16.9.121-002", ["LEADZ-result-default-integer"], "effect",
        leadz_result_kind_source(),
        [("default-integer-kind-feature", "kind(leadz(one)) == kind(0)", "kind(int(leadz(one), kind=alt_ik)) == kind(0)")],
        "KIND is inquired directly on the LEADZ expression and compared with default integer kind.",
        ("integer-kinds-4-8",))
    add("16.9.121", "leadz_values", "S16.9.121-003",
        ["LEADZ-all-zero-bits", "LEADZ-one-low-bit-count", "LEADZ-leftmost-one-count-zero", "LEADZ-all-one-bits"], "effect",
        leadz_values_source(),
        [("all-zero-to-one", "leadz(zero) == bit_size(zero)", "leadz(one) == bit_size(zero)"),
         ("one-low-bit-to-trailz", "leadz(one) == bit_size(one) - 1", "trailz(one) == bit_size(one) - 1"),
         ("leftmost-one-to-low-bit", "ibset(0, bit_size(0) - 1)", "ibset(0, 0)"),
         ("all-one-to-zero", "leadz(not(0)) == 0", "leadz(0) == 0")],
        "LEADZ exact values use BIT_SIZE-relative formulas, IBSET for the leftmost bit, and NOT(0) for all-one bits without assuming a 32-bit model.")

    add("16.9.122", "len_argument_controls", "S16.9.122-001",
        ["LEN-STRING-character", "LEN-unallocated-or-unassociated-string-nondeferred-length", "LEN-KIND-scalar-integer-constant-expression"],
        "positive-control", len_arguments_source(),
        [("string-character-feature", "len(scalar) == 5", "len_trim(scalar) == 5"),
         ("nondeferred-unallocated-feature", "character(len=6), allocatable :: unallocated_fixed", "character(len=5), allocatable :: unallocated_fixed"),
         ("kind-constant-feature", "kind(len(scalar, kind=wide_kind)) == wide_kind", "kind(len(scalar)) == wide_kind")],
        "LEN is exercised with character STRING, nondeferred unallocated/unassociated STRING controls, and a scalar integer constant KIND.",
        ("integer-kinds-4-8",))
    add("16.9.122", "len_characteristics", "S16.9.122-002",
        ["LEN-result-integer-scalar", "LEN-result-kind-from-KIND-or-default"], "effect",
        len_characteristics_source(),
        [("scalar-result-feature", "rank(len(words)) == 0", "rank([len(words)]) == 0"),
         ("kind-result-feature", "kind(len(words, kind=wide_kind)) == wide_kind", "kind(len(words)) == wide_kind")],
        "RANK and KIND are inquired directly on LEN expressions; absent KIND gives default integer and present KIND selects the constant kind.",
        ("integer-kinds-4-8",))
    add("16.9.122", "len_values", "S16.9.122-003",
        ["LEN-scalar-character-length", "LEN-array-element-character-length", "LEN-zero-length-character", "LEN-allocated-deferred-length-character", "LEN-associated-deferred-length-pointer"],
        "effect", len_values_source(),
        [("scalar-length-feature", "len(padded) == 5", "len_trim(padded) == 5"),
         ("array-element-length-feature", "len(words) == 3", "size(words) == 3"),
         ("zero-length-feature", "character(len=0) :: empty", "character(len=1) :: empty"),
         ("allocated-deferred-feature", "allocate(character(len=7) :: allocated_s)", "allocate(character(len=5) :: allocated_s)"),
         ("associated-pointer-feature", "character(len=7), target :: target_s", "character(len=5), target :: target_s")],
        "LEN exact values distinguish scalar length, array element length, zero length, allocated deferred length, and associated deferred pointer target length.")

    add("16.9.123", "len_trim_argument_controls", "S16.9.123-001",
        ["LEN_TRIM-STRING-character", "LEN_TRIM-KIND-scalar-integer-constant-expression"],
        "positive-control", len_trim_arguments_source(),
        [("string-character-feature", "len_trim(scalar) == 3", "len_trim('AB   ') == 3"),
         ("kind-constant-feature", "kind(len_trim(scalar, kind=wide_kind)) == wide_kind", "kind(len_trim(scalar)) == wide_kind")],
        "LEN_TRIM is exercised with a character STRING and a scalar integer constant KIND expression.",
        ("integer-kinds-4-8",))
    add("16.9.123", "len_trim_characteristics", "S16.9.123-002",
        ["LEN_TRIM-result-integer", "LEN_TRIM-result-kind-from-KIND-or-default"], "effect",
        len_trim_characteristics_source(),
        [("integer-scalar-feature", "len_trim(scalar) == 1", "len(scalar) == 1"),
         ("kind-result-feature", "kind(len_trim(scalar, kind=wide_kind)) == wide_kind", "kind(len_trim(scalar)) == wide_kind")],
        "RANK and KIND are inquired directly on LEN_TRIM expressions; absent KIND is default integer and present KIND selects the constant kind.",
        ("integer-kinds-4-8",))
    add("16.9.123", "len_trim_values", "S16.9.123-003",
        ["LEN_TRIM-removes-trailing-blanks", "LEN_TRIM-preserves-internal-blanks", "LEN_TRIM-all-blank-zero"], "effect",
        len_trim_values_source(),
        [("trailing-blanks-feature", "len_trim(trailing) == 2", "len(trailing) == 2"),
         ("internal-blanks-feature", "len_trim(internal) == 3", "len_trim('AB   ') == 3"),
         ("all-blank-feature", "len_trim(blanks) == 0", "len_trim(companion) == 0")],
        "LEN_TRIM exact values remove only trailing blanks, retain internal blanks, and return zero for an all-blank argument with a nonzero companion check.")

    char_specs = {
        "lge": ("16.9.124", "S16.9.124-001", "S16.9.124-002", "S16.9.124-003", "S16.9.124-005", "A", "9"),
        "lgt": ("16.9.125", "S16.9.125-001", "S16.9.125-002", "S16.9.125-003", "S16.9.125-005", "A", "9"),
        "lle": ("16.9.126", "S16.9.126-001", "S16.9.126-002", "S16.9.126-003", "S16.9.126-003", "9", "A"),
        "llt": ("16.9.127", "S16.9.127-001", "S16.9.127-002", "S16.9.127-003", "S16.9.127-003", "9", "A"),
    }
    for intr, (section, arg_rule, kind_rule, pad_rule, value_rule, left, right) in char_specs.items():
        prefix = intr.upper()
        add(section, intr + "_argument_controls", arg_rule,
            [f"{prefix}-STRING_A-default-or-ASCII-character", f"{prefix}-STRING_B-same-character-kind" if intr in {"lle", "llt"} else f"{prefix}-STRING_B-same-character-kind-as-STRING_A"],
            "positive-control", char_argument_source(intr, left, right),
            [("string-a-feature", f"{intr}(string_a, string_b)", f"{intr}(string_b, string_a)"),
             ("same-kind-feature", f"{intr}(same_a, same_b)", f"{intr}(same_b, same_a)")],
            f"{prefix} is exercised with default ASCII STRING_A and same-kind character STRING_B operands.")
        add(section, intr + "_result_kind", kind_rule, [f"{prefix}-result-default-logical"], "effect",
            char_result_kind_source(intr, left, right),
            [("default-logical-kind-feature", f"kind({intr}('{left}', '{right}')) == kind(.false.)",
              f"kind(logical({intr}('{left}', '{right}'), kind=alt_lk)) == kind(.false.)")],
            f"KIND is inquired directly on the {prefix} expression and compared with default logical kind.",
            ("logical-kinds-1-4",))

    add("16.9.124", "lge_blank_padding", "S16.9.124-003",
        ["LGE-blank-padding-shorter-left", "LGE-blank-padding-shorter-right"], "effect",
        ge_gt_padding_source("lge"),
        [("shorter-left-padding-feature", "lge(short_a, a_exclaim)", "lge(a_exclaim, short_a)"),
         ("shorter-right-padding-feature", "lge(a_exclaim, short_a)", "lge(short_a, a_exclaim)")],
        "LGE blank-padding checks compare unequal lengths after LEN-verified right padding of the shorter operand.")
    add("16.9.124", "lge_ascii_order", "S16.9.124-005",
        ["LGE-equal-strings-true", "LGE-following-true", "LGE-preceding-false"], "effect",
        ge_gt_order_source("lge"),
        [("equal-to-lgt-sibling", "lge(eq_a, eq_b)", "lgt(eq_a, eq_b)"),
         ("following-reversed-feature", "lge(upper_a, digit)", "lge(digit, upper_a)"),
         ("preceding-reversed-feature", "lge(digit, upper_a)", "lge(upper_a, digit)")],
        "LGE exact results use ASCII equality and ASCII-following pairs such as 'A' after '9', with reverse false companions.")
    add("16.9.125", "lgt_blank_padding", "S16.9.125-003",
        ["LGT-blank-padding-shorter-left", "LGT-blank-padding-shorter-right"], "effect",
        ge_gt_padding_source("lgt"),
        [("shorter-left-padding-feature", "lgt(short_a, a_exclaim)", "lgt(a_exclaim, short_a)"),
         ("shorter-right-padding-feature", "lgt(a_exclaim, short_a)", "lgt(short_a, a_exclaim)")],
        "LGT blank-padding checks compare unequal lengths after LEN-verified right padding of the shorter operand.")
    add("16.9.125", "lgt_ascii_order", "S16.9.125-005",
        ["LGT-following-true", "LGT-equal-strings-false", "LGT-preceding-false"], "effect",
        ge_gt_order_source("lgt"),
        [("following-reversed-feature", "lgt(upper_a, digit)", "lgt(digit, upper_a)"),
         ("equal-to-lge-sibling", "lgt(eq_a, eq_b)", "lge(eq_a, eq_b)"),
         ("preceding-reversed-feature", "lgt(digit, upper_a)", "lgt(upper_a, digit)")],
        "LGT exact results use ASCII-following pairs and equality false, with LGE sibling substitution on equal strings.")
    add("16.9.126", "lle_ascii_values", "S16.9.126-003",
        ["LLE-unequal-length-blank-padding", "LLE-equal-strings-true", "LLE-ascii-precedes-true", "LLE-ascii-follows-false"], "effect",
        le_lt_values_source("lle"),
        [("blank-padding-feature", "lle(a_exclaim, a_blank)", "lle(a_blank, a_exclaim)"),
         ("equal-nonempty-to-llt-sibling", "lle(eq_a, eq_b)", "llt(eq_a, eq_b)"),
         ("equal-zero-length-to-llt-sibling", "lle(empty_a, empty_b)", "llt(empty_a, empty_b)"),
         ("precedes-reversed-feature", "lle(digit, upper_a)", "lle(upper_a, digit)"),
         ("follows-reversed-feature", "lle(upper_a, digit)", "lle(digit, upper_a)")],
        "LLE exact results use LEN-verified blank padding, equality true, and ASCII-preceding pairs with reverse false companions.")
    add("16.9.127", "llt_ascii_values", "S16.9.127-003",
        ["LLT-unequal-length-blank-padding", "LLT-ascii-precedes-true", "LLT-equal-strings-false", "LLT-ascii-follows-false"], "effect",
        le_lt_values_source("llt"),
        [("blank-padding-feature", "llt(short_a, a_blank)", "lle(short_a, a_blank)"),
         ("precedes-reversed-feature", "llt(digit, upper_a)", "llt(upper_a, digit)"),
         ("equal-nonempty-to-lle-sibling", "llt(eq_a, eq_b)", "lle(eq_a, eq_b)"),
         ("equal-zero-length-to-lle-sibling", "llt(empty_a, empty_b)", "lle(empty_a, empty_b)"),
         ("follows-reversed-feature", "llt(upper_a, digit)", "llt(digit, upper_a)")],
        "LLT exact results use LEN-verified blank padding, ASCII-preceding true, equality false, and reverse false companions.")

    return {identifier(case.rule, case.variant): case for case in cases}


def mutation_records(case: Case):
    records = []
    raw = case.source.encode("ascii")
    for mid, expected, replacement in case.mutations:
        count = case.source.count(expected)
        if count != 1:
            raise ValueError(f"{case.variant}:{mid} expected unique mutation text {expected!r}, saw {count}")
        start = case.source.index(expected)
        mutated = raw[:start] + replacement.encode("ascii") + raw[start + len(expected):]
        records.append(dict(id=mid, kind="feature", expected=expected, replacement=replacement,
                            span=[start, start + len(expected)], source_sha256=sha(mutated)))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for name, case in make_cases().items():
        raw = case.source.encode("ascii")
        mutations = mutation_records(case)
        spec = dict(id=name, section=case.section, variant=case.variant, rule=case.rule, facets=list(case.facets),
                    evidence=case.evidence, source=case.source, source_sha256=sha(raw), completion=case.completion,
                    mutations=mutations, oracle=case.oracle, profiles=list(case.profiles))
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case.variant)
        manifest = dict(schema_version=1, id=name, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=case.completion, stderr=""))
        if case.profiles:
            manifest["profiles"] = list(case.profiles)
        spec["path"], spec["manifest"] = directory.relative_to(root).as_posix() + "/fixture.json", manifest
        specs[name] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def sync_catalogue(section, catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    grouped = {}
    for spec in specs.values():
        if spec["section"] == section:
            grouped.setdefault(spec["rule"], []).append(spec)
    for rule, rule_specs in grouped.items():
        row = by_rule[rule]
        facets = set().union(*(set(spec["facets"]) for spec in rule_specs))
        if not facets <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + rule)
        for facet in facets:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = rule + f" {TOPIC} runtime fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + " ".join(spec["oracle"] for spec in rule_specs))
        limit_prefix = rule + f" {TOPIC} boundaries: "
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""), limit_prefix,
            limit_prefix + "This packet supplies only the named single-image runtime/effect or positive-control fixtures. "
            "It does not claim diagnostics for unnumbered argument restrictions, non-ASCII character truth values, "
            "coarray behavior, compiler consensus, source-review approval, or unrelated facets.")
    for rule, pending in REMAINING_PENDING.items():
        if rule in by_rule:
            row_pending = by_rule[rule].setdefault("pending", {})
            for facet, reason in pending.items():
                row_pending.setdefault(facet, reason)
            if set(row_pending) != set(pending):
                raise ValueError("unexpected remaining pending facets for " + rule)
    return result


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    _, specs = build_corpus(root)
    owned = [spec for spec in specs.values() if spec["section"] == section]
    pending_note = ""
    if section in {"16.9.124", "16.9.125", "16.9.126", "16.9.127"}:
        pending_note = " Non-ASCII truth values remain pending because p5 makes them processor dependent."
    summary = (SUMMARY_BEGIN.format(section=section) + "\n"
        "## Intrinsics 16.9.P runtime observations\n\n"
        f"This batch adds {len(owned)} generated single-image runtime fixtures for {section}, covering "
        f"{sum(len(spec['facets']) for spec in owned)} facets with exact BIT_SIZE-relative LEADZ, LEN, "
        "LEN_TRIM, or ASCII-collating character comparison observations. Result characteristics are inquired "
        "directly on intrinsic expressions, and every discharged facet has a conforming feature mutation "
        f"compiled and run by the mutation checker.{pending_note}\n" + SUMMARY_END.format(section=section))
    if SUMMARY_BEGIN.format(section=section) in before or SUMMARY_END.format(section=section) in before:
        head, tail = before.split(SUMMARY_BEGIN.format(section=section))
        _, rest_tail = tail.split(SUMMARY_END.format(section=section))
        before = head + summary + rest_tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    generated = "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n"
    return before + begin + generated + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        updated = sync_catalogue(section, catalogue, specs)
        updated_catalogues[rel] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        for rel, updated in updated_catalogues.items():
            if json.loads((root / rel).read_text()) != updated:
                stale.append(rel)
        for rel, text in updated_views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise ValueError("stale intrinsics_16_9_p generated files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogues:
            for rel, updated in updated_catalogues.items():
                (root / rel).write_text(json.dumps(updated, indent=2) + "\n")
            for rel, text in updated_views.items():
                (root / rel).write_text(text)
    return files, specs


def mutate_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["id"])
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span lost complete-parent binding")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def compile_and_run(workdir, compiler, std, source_bytes):
    source = workdir / "source.f90"
    exe = workdir / "program"
    source.write_bytes(source_bytes)
    cmd = [str(compiler), ("--std=" if "lfortran" in Path(str(compiler)).name.lower() else "-std=") + std,
           "source.f90", "-o", "program"]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if comp.returncode != 0:
        return "compile-fail", comp.returncode, comp.stdout, comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if run.returncode == 0:
        return "pass", run.returncode, run.stdout, run.stderr
    return "run-fail", run.returncode, run.stdout, run.stderr


def check_mutations(root, compiler, std, inject_survivor=False, skip_parent_failures=False):
    root = Path(root)
    _, specs = build_corpus(root)
    workspace = root / ("." + TOPIC + "_mutation_runs") / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    failures, checked, parents, skipped = [], 0, 0, []
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, rc, stdout, stderr = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"))
            if status != "pass" or stdout != spec["completion"] or stderr != "":
                message = f"{spec['id']} parent failed {status} rc={rc}\nstdout={stdout}\nstderr={stderr}"
                if skip_parent_failures:
                    skipped.append(message)
                    continue
                failures.append(message)
                continue
            parents += 1
            for mutation in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mutation["id"])
                case_dir.mkdir()
                source = spec["source"].encode("ascii") if inject_survivor and checked == 1 else mutate_source(spec, mutation)
                status, rc, stdout, stderr = compile_and_run(case_dir, compiler, std, source)
                passed = status == "pass" and stdout == spec["completion"] and stderr == ""
                if status == "compile-fail" or passed:
                    failures.append(f"{spec['id']}:{mutation['id']} bad mutant status={status} rc={rc}\nstdout={stdout}\nstderr={stderr}")
        if failures:
            raise SystemExit("\n\n".join(failures[:20]))
        return parents, checked, skipped
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--inject-survivor", action="store_true")
    parser.add_argument("--skip-parent-failures", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        parents, checked, skipped = check_mutations(
            args.root, args.compiler, args.std, args.inject_survivor, args.skip_parent_failures)
        print(f"Mutation-checked {checked} intrinsics_16_9_p mutations across {parents} parents; {len(skipped)} parents skipped.")
    else:
        _, specs = generate(args.root, check=args.check, sync_catalogues=args.sync_catalogues)
        if not args.check:
            print(f"Generated {len(specs)} intrinsics_16_9_p fixtures with {sum(len(s['facets']) for s in specs.values())} facets.")


if __name__ == "__main__":
    main()
