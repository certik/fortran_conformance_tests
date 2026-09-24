#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.45-16.9.53 intrinsic fixtures."""

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
TOPIC = "intrinsics_16_9_e"
SECTIONS = ("16.9.45", "16.9.46", "16.9.47", "16.9.48", "16.9.49", "16.9.50", "16.9.51", "16.9.52", "16.9.53")
CATALOGUES = {
    "16.9.45": "doc/catalogues/bge_intrinsic_16_9_45.json",
    "16.9.46": "doc/catalogues/bgt_intrinsic_16_9_46.json",
    "16.9.47": "doc/catalogues/bit_size_intrinsic_16_9_47.json",
    "16.9.48": "doc/catalogues/ble_intrinsic_16_9_48.json",
    "16.9.49": "doc/catalogues/blt_intrinsic_16_9_49.json",
    "16.9.50": "doc/catalogues/btest_intrinsic_16_9_50.json",
    "16.9.51": "doc/catalogues/ceiling_16_9_51.json",
    "16.9.52": "doc/catalogues/char_16_9_52.json",
    "16.9.53": "doc/catalogues/cmplx_16_9_53.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.E FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.E FIXTURES -->"
PROFILE_BY_VARIANT = {
    "bge_result_kind": ["logical-kinds-1-4"],
    "bgt_result_kind": ["logical-kinds-1-4"],
    "ble_result_kind": ["logical-kinds-1-4"],
    "blt_result_kind": ["logical-kinds-1-4"],
    "btest_result_kind": ["logical-kinds-1-4"],
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace(".", "_").replace("-", "_") + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Case:
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[tuple[str, str, str], ...]
    oracle: str

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.E " + self.variant.upper().replace("_", " ") + " OK\n"


REQUIRE_HELPERS = """contains
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
"""


def program(name: str, declarations: str, body: str, completion: str, extra_contains: str = "") -> str:
    return f"""program i169e_{name}
  implicit none
{declarations}{body}  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}{extra_contains}end program i169e_{name}
"""


TYPE_CODE_INTERFACE = """  interface type_code
    procedure code_integer, code_real, code_complex
  end interface
"""

TYPE_CODE_HELPERS = """  integer function code_integer(x)
    integer, intent(in) :: x
    code_integer = 1
  end function code_integer
  integer function code_real(x)
    real, intent(in) :: x
    code_real = 2
  end function code_real
  integer function code_complex(x)
    complex, intent(in) :: x
    code_complex = 3
  end function code_complex
"""

def bit_compare_source(intrinsic: str, true_expr: str, false_expr: str, completion: str) -> str:
    return program(
        intrinsic,
        "  logical :: observed\n",
        f"""  observed = {true_expr}
  call require_true('{intrinsic} true bit-sequence comparison', observed)
  observed = {false_expr}
  call require_false('{intrinsic} false bit-sequence comparison', observed)
  call require_true('{intrinsic} result default logical', kind({intrinsic}(1, 1)) == kind(.false.))
""",
        completion,
    )


def bit_result_source(intrinsic: str, true_expr: str, false_expr: str, completion: str) -> str:
    return program(
        intrinsic + "_result_kind",
        "  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)\n  logical :: observed\n",
        f"""  observed = {true_expr}
  call require_true('{intrinsic} true bit-sequence comparison', observed)
  observed = {false_expr}
  call require_false('{intrinsic} false bit-sequence comparison', observed)
  call require_true('{intrinsic} result default logical', &
      kind({intrinsic}(1, 1)) == kind(.false.) .and. alt_lk /= kind(.false.) .and. &
      kind(logical({intrinsic}(1, 1), kind=alt_lk)) == alt_lk)
""",
        completion,
    )


def bit_size_source(completion: str) -> str:
    return program(
        "bit_size_model",
        "  integer, parameter :: ik = selected_int_kind(12)\n  integer :: scalar_z\n  integer(kind=ik) :: wide_z\n",
        """  scalar_z = bit_size(0)
  wide_z = bit_size([0_ik, 1_ik])
  call require_true('bit_size scalar integer argument', scalar_z > 0)
  call require_true('bit_size scalar argument gives scalar result', rank(bit_size(0)) == 0)
  call require_true('bit_size array argument scalar result', rank(bit_size([0, 1])) == 0)
  call require_true('bit_size same kind result', &
      kind(bit_size(0_ik)) == ik .and. rank(bit_size(0_ik)) == 0 .and. kind(wide_z) == ik)
  call require_true('bit_size supplies high model position', btest(ibset(0, scalar_z - 1), scalar_z - 1))
""",
        completion,
    )


def btest_result_source(completion: str) -> str:
    return program(
        "btest_result_kind",
        "  integer, parameter :: alt_lk = merge(1, 4, kind(.false.) /= 1)\n",
        """  call require_true('btest result default logical', &
      kind(btest(1, 0)) == kind(.false.) .and. alt_lk /= kind(.false.) .and. &
      kind(logical(btest(1, 0), kind=alt_lk)) == alt_lk)
""",
        completion,
    )


def btest_source(completion: str) -> str:
    return program(
        "btest_bits",
        "  logical :: low_bit, high_bit, zero_bit\n  integer :: z\n",
        """  z = bit_size(0)
  low_bit = btest(1, 0)
  high_bit = btest(ibset(0, z - 1), z - 1)
  zero_bit = btest(1, 1)
  call require_true('btest integer i and pos zero one-bit', low_bit)
  call require_true('btest upper valid pos one-bit', high_bit)
  call require_false('btest zero bit false', zero_bit)
  call require_true('btest result default logical', kind(btest(1, 0)) == kind(.false.))
""",
        completion,
    )


def ceiling_source(completion: str) -> str:
    return program(
        "ceiling_exact",
        TYPE_CODE_INTERFACE + "  integer, parameter :: ik = selected_int_kind(12)\n  real :: a\n  integer(kind=ik) :: wide\n  integer :: defaulted\n",
        """  a = 3.25
  wide = ceiling(a, kind=ik)
  defaulted = ceiling(-3.25)
  call require_true('ceiling real argument exact positive', ceiling(a) == 4)
  call require_true('ceiling result integer type', type_code(ceiling(a)) == 1)
  call require_true('ceiling kind scalar constant selects kind', kind(ceiling(a, kind=ik)) == ik .and. wide == 4_ik)
  call require_true('ceiling default integer kind absent', kind(ceiling(-3.25)) == kind(0))
  call require_true('ceiling least integer negative', defaulted == -3)
  call require_true('ceiling integral value unchanged', ceiling(3.0) == 3)
""",
        completion,
        TYPE_CODE_HELPERS,
    )


def char_source(completion: str) -> str:
    return program(
        "char_roundtrip",
        "  character(len=1) :: c, d, e\n  integer :: i\n",
        """  i = ichar('Q')
  c = char(i)
  d = char(ichar('K'), kind=kind('A'))
  e = char(ichar('Z'))
  call require_true('char integer argument in collating range', len(c) == 1 .and. c == 'Q')
  call require_true('char kind scalar constant argument', len(d) == 1 .and. d == 'K')
  call require_true('char result length one', len(char(ichar('Z'))) == 1)
  call require_true('char collating position result', ichar(c) == i)
  call require_true('ichar char integer roundtrip', ichar(char(i)) == i)
  call require_true('char ichar character roundtrip', len(char(ichar('Z'))) == 1 .and. char(ichar('Z')) == 'Z')
""",
        completion,
    )


def cmplx_complex_source(completion: str) -> str:
    return program(
        "cmplx_complex_form",
        "  integer, parameter :: rk = selected_real_kind(10)\n  complex(kind=rk) :: z, result\n",
        """  z = cmplx(1.25_rk, -2.5_rk, kind=rk)
  result = cmplx(z, kind=rk)
  call require_true('cmplx complex x argument', real(result, kind=rk) == 1.25_rk)
  call require_true('cmplx complex kind constant', kind(cmplx(z, kind=rk)) == rk)
  call require_true('cmplx result complex type and kind', kind(cmplx(1.0_rk, 2.0_rk, kind=rk)) == rk)
  call require_true('cmplx complex decomposes to parts', aimag(result) == -2.5_rk)
""",
        completion,
    )


def cmplx_real_source(completion: str) -> str:
    return program(
        "cmplx_real_form",
        "  integer, parameter :: rk = selected_real_kind(10)\n  complex(kind=rk) :: a, b, boz_pair\n",
        """  a = cmplx(3, -2.0, kind=rk)
  b = cmplx(4.0_rk, 5, kind=rk)
  boz_pair = cmplx(z'3', z'4', kind=rk)
  call require_true('cmplx integer x real y exact', real(a, kind=rk) == 3.0_rk .and. aimag(a) == -2.0_rk)
  call require_true('cmplx real x integer y exact', real(b, kind=rk) == 4.0_rk .and. aimag(b) == 5.0_rk)
  call require_true('cmplx boz x y match real conversions', &
      real(boz_pair, kind=rk) == real(z'3', kind=rk) .and. aimag(boz_pair) == real(z'4', kind=rk))
  call require_true('cmplx real form kind constant', kind(cmplx(3, -2.0, kind=rk)) == rk)
  call require_true('cmplx components are real conversions', &
      real(a, kind=rk) == real(3, kind=rk) .and. aimag(a) == real(-2.0, kind=rk))
""",
        completion,
    )


def cmplx_defaults_source(completion: str) -> str:
    return program(
        "cmplx_defaults",
        "  complex :: z\n",
        """  z = cmplx(-3)
  call require_true('cmplx absent y zero imaginary', real(z) == -3.0 .and. aimag(z) == 0.0)
  call require_true('cmplx absent kind default real kind', kind(cmplx(-3)) == kind(cmplx(0.0, 0.0)))
  call require_true('cmplx result is complex assignable', real(z) == -3.0)
""",
        completion,
    )



def cmplx_characteristics_source(completion: str) -> str:
    return program(
        "cmplx_characteristics",
        TYPE_CODE_INTERFACE + "  integer, parameter :: rk = selected_real_kind(10)\n  complex :: defaulted\n  complex(kind=rk) :: selected\n",
        """  selected = cmplx(1.0_rk, 2.0_rk, kind=rk)
  defaulted = cmplx(-3)
  call require_true('cmplx result complex type', type_code(cmplx(1.0, 2.0)) == 3)
  call require_true('cmplx present kind selects complex kind', kind(cmplx(1.0_rk, 2.0_rk, kind=rk)) == rk)
  call require_true('cmplx absent kind default real kind', kind(cmplx(-3)) == kind(cmplx(0.0, 0.0)))
""",
        completion,
        TYPE_CODE_HELPERS,
    )


def cmplx_values_source(completion: str) -> str:
    return program(
        "cmplx_values",
        "  integer, parameter :: rk = selected_real_kind(10)\n  complex :: defaulted\n  complex(kind=rk) :: from_parts, from_complex\n  complex(kind=rk) :: z\n",
        """  defaulted = cmplx(-3)
  z = cmplx(1.25_rk, -2.5_rk, kind=rk)
  from_complex = cmplx(z, kind=rk)
  from_parts = cmplx(3, -2.0, kind=rk)
  call require_true('cmplx absent y supplies zero', real(defaulted) == -3.0 .and. aimag(defaulted) == 0.0)
  call require_true('cmplx absent kind supplies default', kind(cmplx(-3)) == kind(cmplx(0.0, 0.0)))
  call require_true('cmplx complex x decomposes', real(from_complex, kind=rk) == 1.25_rk .and. aimag(from_complex) == -2.5_rk)
  call require_true('cmplx components from real conversions', &
      real(from_parts, kind=rk) == real(3, kind=rk) .and. aimag(from_parts) == real(-2.0, kind=rk))
""",
        completion,
    )

def make_cases():
    raw = []

    def add(variant, rule, facets, evidence, source_func, mutations, oracle):
        completion = "INTRINSICS 16.9.E " + variant.upper().replace("_", " ") + " OK\n"
        raw.append(Case(variant, rule, tuple(facets), evidence, source_func(completion), tuple(mutations), oracle))

    add(
        "bge_bit_order", "S16.9.45-003", ["bge-true-case", "bge-false-case"], "effect",
        lambda c: bit_compare_source("bge", "bge(z'80000000', 1)", "bge(1, z'80000000')", c),
        [("bge-true-to-bgt-equal", "observed = bge(z'80000000', 1)", "observed = bgt(z'80000000', z'80000000')"),
         ("bge-false-to-true", "observed = bge(1, z'80000000')", "observed = bge(z'80000000', 1)")],
        "BGE compares BOZ and integer bit sequences left-to-right using 16.3.2; Z'80000000' is greater than the padded one-bit sequence, while one is not greater than or equal to it."
    )
    add(
        "bge_arguments", "S16.9.45-001", ["bge-i-integer-or-boz", "bge-j-integer-or-boz"], "positive-control",
        lambda c: bit_compare_source("bge", "bge(not(0), 1)", "bge(1, not(0))", c),
        [("bge-i-feature", "observed = bge(not(0), 1)", "observed = bge(1, not(0))"),
         ("bge-j-feature", "observed = bge(1, not(0))", "observed = bge(not(0), 1)")],
        "BGE accepts integer arguments as bit sequences; NOT(0) supplies an all-one sequence, which is greater than one in the 16.3.2 ordering."
    )
    add(
        "bge_result_kind", "S16.9.45-002", ["bge-result-default-logical"], "effect",
        lambda c: bit_result_source("bge", "bge(z'80000000', 1)", "bge(1, z'80000000')", c),
        [("bge-kind-feature", "kind(bge(1, 1)) == kind(.false.)", "kind(logical(bge(1, 1), kind=alt_lk)) == kind(.false.)")],
        "The BGE result is assignable to default LOGICAL and KIND(BGE(1,1)) equals KIND(.FALSE.)."
    )

    add(
        "bgt_bit_order", "S16.9.46-003", ["bgt-true-case", "bgt-false-case"], "effect",
        lambda c: bit_compare_source("bgt", "bgt(z'80000000', 1)", "bgt(1, z'80000000')", c),
        [("bgt-true-to-equal", "observed = bgt(z'80000000', 1)", "observed = bgt(z'80000000', z'80000000')"),
         ("bgt-false-to-true", "observed = bgt(1, z'80000000')", "observed = bgt(z'80000000', 1)")],
        "BGT is true only when the first bit sequence is strictly greater by 16.3.2; the high-bit BOZ sequence is greater than one, and one is not greater than it."
    )
    add(
        "bgt_arguments", "S16.9.46-001", ["bgt-i-integer-or-boz", "bgt-j-integer-or-boz"], "positive-control",
        lambda c: bit_compare_source("bgt", "bgt(not(0), 1)", "bgt(1, not(0))", c),
        [("bgt-i-feature", "observed = bgt(not(0), 1)", "observed = bgt(1, not(0))"),
         ("bgt-j-feature", "observed = bgt(1, not(0))", "observed = bgt(not(0), 1)")],
        "BGT accepts integer arguments as bit sequences; NOT(0) produces an all-one bit sequence that compares greater than one."
    )
    add(
        "bgt_result_kind", "S16.9.46-002", ["bgt-result-default-logical"], "effect",
        lambda c: bit_result_source("bgt", "bgt(z'80000000', 1)", "bgt(1, z'80000000')", c),
        [("bgt-kind-feature", "kind(bgt(1, 1)) == kind(.false.)", "kind(logical(bgt(1, 1), kind=alt_lk)) == kind(.false.)")],
        "The BGT result is default LOGICAL, observed with a KIND inquiry on a scalar result."
    )

    add(
        "bit_size_model", "S16.9.47-001", ["bit_size-i-integer"], "positive-control",
        bit_size_source,
        [("scalar-argument-feature", "scalar_z = bit_size(0)", "scalar_z = 0")],
        "BIT_SIZE accepts an integer argument and returns a positive scalar model bit count for default integer."
    )
    add(
        "bit_size_scalar_array", "S16.9.47-002", ["bit_size-scalar-argument-permitted", "bit_size-array-argument-permitted"], "effect",
        bit_size_source,
        [("scalar-argument-feature", "rank(bit_size(0)) == 0", "rank([bit_size(0)]) == 0"),
         ("array-argument-feature", "rank(bit_size([0, 1])) == 0", "rank([bit_size([0, 1])]) == 0")],
        "BIT_SIZE permits both scalar and array integer arguments; the array call is used in an expression whose rank is observed as scalar."
    )
    add(
        "bit_size_characteristics", "S16.9.47-003", ["bit_size-result-scalar", "bit_size-result-integer-same-kind"], "effect",
        bit_size_source,
        [("result-scalar-feature", "rank(bit_size(0_ik)) == 0", "rank([bit_size(0_ik)]) == 0"),
         ("same-kind-feature", "kind(bit_size(0_ik)) == ik", "kind(bit_size(0)) == ik")],
        "BIT_SIZE has scalar integer result characteristics and the result kind is the kind of I, checked with a selected nondefault integer kind."
    )
    add(
        "bit_size_model_value", "S16.9.47-004", ["bit_size-result-model-z"], "effect",
        bit_size_source,
        [("model-z-feature", "btest(ibset(0, scalar_z - 1), scalar_z - 1)", "btest(ibset(0, scalar_z - 2), scalar_z - 1)")],
        "BIT_SIZE supplies the model bit count z: z-1 is used as the leftmost valid bit position and BTEST observes that bit after IBSET sets it."
    )

    add(
        "ble_bit_order", "S16.9.48-003", ["ble-true-case", "ble-false-case"], "effect",
        lambda c: bit_compare_source("ble", "ble(1, z'80000000')", "ble(z'80000000', 1)", c),
        [("ble-true-to-false", "observed = ble(1, z'80000000')", "observed = ble(z'80000000', 1)"),
         ("ble-false-to-true", "observed = ble(z'80000000', 1)", "observed = ble(1, z'80000000')")],
        "BLE follows 16.3.2 less-than-or-equal comparison; one is less than the high-bit BOZ sequence, while the high-bit sequence is not less than or equal to one."
    )
    add(
        "ble_arguments", "S16.9.48-001", ["ble-i-integer-or-boz", "ble-j-integer-or-boz"], "positive-control",
        lambda c: bit_compare_source("ble", "ble(1, not(0))", "ble(not(0), 1)", c),
        [("ble-i-feature", "observed = ble(1, not(0))", "observed = ble(not(0), 1)"),
         ("ble-j-feature", "observed = ble(not(0), 1)", "observed = ble(1, not(0))")],
        "BLE accepts integer arguments interpreted as bit sequences; one is less than the all-one NOT(0) sequence."
    )
    add(
        "ble_result_kind", "S16.9.48-002", ["ble-result-default-logical"], "effect",
        lambda c: bit_result_source("ble", "ble(1, z'80000000')", "ble(z'80000000', 1)", c),
        [("ble-kind-feature", "kind(ble(1, 1)) == kind(.false.)", "kind(logical(ble(1, 1), kind=alt_lk)) == kind(.false.)")],
        "The BLE result is default LOGICAL, observed with KIND(BLE(1,1))."
    )

    add(
        "blt_bit_order", "S16.9.49-003", ["blt-true-case", "blt-false-case"], "effect",
        lambda c: bit_compare_source("blt", "blt(1, z'80000000')", "blt(z'80000000', 1)", c),
        [("blt-true-to-equal", "observed = blt(1, z'80000000')", "observed = blt(z'80000000', z'80000000')"),
         ("blt-false-to-true", "observed = blt(z'80000000', 1)", "observed = blt(1, z'80000000')")],
        "BLT is true only when the first bit sequence is strictly less by 16.3.2; one is less than the high-bit BOZ sequence."
    )
    add(
        "blt_arguments", "S16.9.49-001", ["blt-i-integer-or-boz", "blt-j-integer-or-boz"], "positive-control",
        lambda c: bit_compare_source("blt", "blt(1, not(0))", "blt(not(0), 1)", c),
        [("blt-i-feature", "observed = blt(1, not(0))", "observed = blt(not(0), 1)"),
         ("blt-j-feature", "observed = blt(not(0), 1)", "observed = blt(1, not(0))")],
        "BLT accepts integer arguments interpreted as bit sequences; one is less than the all-one NOT(0) sequence."
    )
    add(
        "blt_result_kind", "S16.9.49-002", ["blt-result-default-logical"], "effect",
        lambda c: bit_result_source("blt", "blt(1, z'80000000')", "blt(z'80000000', 1)", c),
        [("blt-kind-feature", "kind(blt(1, 1)) == kind(.false.)", "kind(logical(blt(1, 1), kind=alt_lk)) == kind(.false.)")],
        "The BLT result is default LOGICAL, observed with KIND(BLT(1,1))."
    )

    add(
        "btest_arguments", "S16.9.50-001", ["btest-i-integer", "btest-pos-integer", "btest-pos-nonnegative", "btest-pos-less-than-bit-size"], "positive-control",
        btest_source,
        [("btest-pos-zero", "low_bit = btest(1, 0)", "low_bit = btest(1, 1)"),
         ("btest-upper-pos", "high_bit = btest(ibset(0, z - 1), z - 1)", "high_bit = btest(ibset(0, z - 2), z - 1)")],
        "BTEST accepts integer I and integer POS values at the lower boundary 0 and upper valid boundary BIT_SIZE(I)-1."
    )
    add(
        "btest_result_kind", "S16.9.50-002", ["btest-result-default-logical"], "effect",
        btest_result_source,
        [("btest-kind-feature", "kind(btest(1, 0)) == kind(.false.)", "kind(logical(btest(1, 0), kind=alt_lk)) == kind(.false.)")],
        "The BTEST result is default LOGICAL, observed with KIND(BTEST(1,0))."
    )
    add(
        "btest_values", "S16.9.50-003", ["btest-true-for-one-bit", "btest-false-for-zero-bit"], "effect",
        btest_source,
        [("btest-one-bit-feature", "low_bit = btest(1, 0)", "low_bit = btest(1, 1)"),
         ("btest-zero-bit-feature", "zero_bit = btest(1, 1)", "zero_bit = btest(1, 0)")],
        "BTEST returns true for a one bit at POS and false for a zero bit at POS, using exact positions 0 and 1 of integer value one."
    )

    add(
        "ceiling_arguments", "S16.9.51-001", ["A-real-argument", "KIND-scalar-integer-constant-expression"], "positive-control",
        ceiling_source,
        [("ceiling-real-feature", "ceiling(a) == 4", "floor(a) == 4"),
         ("ceiling-kind-feature", "wide = ceiling(a, kind=ik)", "wide = floor(a, kind=ik)")],
        "CEILING accepts real A and a scalar integer constant KIND; A=3.25 is exactly representable and KIND=ik is a constant."
    )
    add(
        "ceiling_characteristics", "S16.9.51-002", ["result-integer-type", "present-KIND-selects-result-kind", "absent-KIND-default-integer-kind"], "effect",
        ceiling_source,
        [("ceiling-result-type-feature", "type_code(ceiling(a)) == 1", "type_code(real(ceiling(a))) == 1"),
         ("ceiling-kind-selection", "kind(ceiling(a, kind=ik)) == ik", "kind(ceiling(a)) == ik"),
         ("ceiling-absent-kind", "kind(ceiling(-3.25)) == kind(0)", "kind(ceiling(-3.25, kind=ik)) == kind(0)")],
        "CEILING has integer result type; present KIND selects ik and absent KIND gives default integer kind."
    )
    add(
        "ceiling_values", "S16.9.51-003", ["least-integer-greater-or-equal-value"], "effect",
        ceiling_source,
        [("ceiling-to-floor-positive", "ceiling(a) == 4", "floor(a) == 4"),
         ("ceiling-to-floor-negative", "defaulted = ceiling(-3.25)", "defaulted = floor(-3.25)")],
        "CEILING returns the least integer greater than or equal to A; exact 3.25, -3.25, and 3.0 check upward, negative, and integral cases."
    )

    add(
        "char_arguments", "S16.9.52-001", ["I-integer-in-collating-range", "KIND-scalar-integer-constant-expression"], "positive-control",
        char_source,
        [("char-i-feature", "c = char(i)", "c = char(ichar('R'))"),
         ("char-kind-call-feature", "d = char(ichar('K'), kind=kind('A'))", "d = char(ichar('L'), kind=kind('A'))")],
        "CHAR accepts an integer collating-sequence position obtained from ICHAR and a scalar integer constant KIND expression."
    )
    add(
        "char_characteristics", "S16.9.52-002", ["result-character-length-one"], "effect",
        char_source,
        [("char-length-feature", "call require_true('char result length one', len(char(ichar('Z'))) == 1)", "call require_true('char result length one', len('YZ') == 1)")],
        "CHAR returns a character result of length one; absent-default-kind remains pending because the only load-bearing alternate kind is not available on both validation profiles."
    )
    add(
        "char_collating_result", "S16.9.52-003", ["collating-position-result"], "effect",
        char_source,
        [("char-position-feature", "c = char(i)", "c = char(ichar('R'))")],
        "CHAR(I) returns the character at position I of the collating sequence; ICHAR of that character returns the original I."
    )
    add(
        "char_roundtrips", "S16.9.52-004", ["ICHAR-CHAR-integer-roundtrip", "CHAR-ICHAR-character-roundtrip"], "effect",
        char_source,
        [("integer-roundtrip-feature", "ichar(char(i)) == i", "ichar(char(i + 1)) == i"),
         ("character-roundtrip-feature", "len(char(ichar('Z'))) == 1 .and. char(ichar('Z')) == 'Z'", "len(char(ichar('Z'))) == 1 .and. char(ichar('Y')) == 'Z'")],
        "The result-value paragraph explicitly requires ICHAR(CHAR(I,KIND(C)))==I and CHAR(ICHAR(C),KIND(C))==C for representable characters."
    )

    add(
        "cmplx_complex_form", "S16.9.53-001", ["complex-form-X-complex", "complex-form-KIND-scalar-integer-constant-expression"], "positive-control",
        cmplx_complex_source,
        [("complex-x-feature", "result = cmplx(z, kind=rk)", "result = cmplx(aimag(z), real(z, kind=rk), kind=rk)"),
         ("complex-kind-feature", "kind(cmplx(z, kind=rk)) == rk", "kind(cmplx(z)) == rk")],
        "CMPLX accepts the complex-X form with scalar integer constant KIND and preserves exact components when converting to the same kind."
    )
    add(
        "cmplx_real_form", "S16.9.53-002", ["real-form-X-integer-real-or-BOZ", "real-form-Y-integer-real-or-BOZ", "real-form-KIND-scalar-integer-constant-expression"], "positive-control",
        cmplx_real_source,
        [("real-form-x-feature", "a = cmplx(3, -2.0, kind=rk)", "a = cmplx(4, -2.0, kind=rk)"),
         ("real-form-y-feature", "b = cmplx(4.0_rk, 5, kind=rk)", "b = cmplx(4.0_rk, 6, kind=rk)"),
         ("real-form-boz-x-feature", "boz_pair = cmplx(z'3', z'4', kind=rk)", "boz_pair = cmplx(z'5', z'4', kind=rk)"),
         ("real-form-boz-y-feature", "boz_pair = cmplx(z'3', z'4', kind=rk)", "boz_pair = cmplx(z'3', z'6', kind=rk)"),
         ("real-form-kind-feature", "kind(cmplx(3, -2.0, kind=rk)) == rk", "kind(cmplx(3, -2.0)) == rk")],
        "CMPLX accepts integer, real, and BOZ X/Y arguments in the real form; BOZ components are checked only against the same-program REAL(boz,KIND) conversions required by p6."
    )
    add(
        "cmplx_characteristics", "S16.9.53-003", ["result-complex-type", "present-KIND-selects-complex-kind", "absent-KIND-default-real-kind"], "effect",
        cmplx_characteristics_source,
        [("complex-result-type-feature", "type_code(cmplx(1.0, 2.0)) == 3", "type_code(real(cmplx(1.0, 2.0))) == 3"),
         ("present-kind-feature", "kind(cmplx(1.0_rk, 2.0_rk, kind=rk)) == rk", "kind(cmplx(1.0_rk, 2.0_rk)) == rk"),
         ("absent-kind-feature", "kind(cmplx(-3)) == kind(cmplx(0.0, 0.0))", "kind(cmplx(-3, kind=rk)) == kind(cmplx(0.0, 0.0))")],
        "CMPLX has complex type; present KIND is checked in sibling exact-kind fixtures, while absent KIND has the default real kind."
    )
    add(
        "cmplx_values", "S16.9.53-004", ["absent-Y-supplies-zero-imaginary-part", "absent-KIND-supplies-default-real-kind", "complex-X-decomposes-to-parts", "components-come-from-REAL-conversions"], "effect",
        cmplx_values_source,
        [("absent-y-feature", "defaulted = cmplx(-3)", "defaulted = cmplx(-3, 1)"),
         ("absent-kind-feature", "kind(cmplx(-3)) == kind(cmplx(0.0, 0.0))", "kind(cmplx(-3, kind=rk)) == kind(cmplx(0.0, 0.0))"),
         ("complex-x-feature", "from_complex = cmplx(z, kind=rk)", "from_complex = cmplx(aimag(z), real(z, kind=rk), kind=rk)"),
         ("components-feature", "from_parts = cmplx(3, -2.0, kind=rk)", "from_parts = cmplx(4, -2.0, kind=rk)")],
        "CMPLX(X,Y,KIND) has real and imaginary parts equal to REAL(X,KIND) and REAL(Y,KIND) for exact small integer and real operands."
    )
    add(
        "cmplx_absent_y", "S16.9.53-004", ["absent-Y-supplies-zero-imaginary-part", "absent-KIND-supplies-default-real-kind"], "effect",
        cmplx_defaults_source,
        [("absent-y-feature", "z = cmplx(-3)", "z = cmplx(-3, 1)"),
         ("absent-kind-default-feature", "kind(cmplx(-3)) == kind(cmplx(0.0, 0.0))", "kind(cmplx(-3, kind=kind(0.0d0))) == kind(cmplx(0.0, 0.0))")],
        "When Y is absent CMPLX supplies zero for the imaginary part, and absent KIND is default real kind."
    )
    add(
        "cmplx_complex_parts", "S16.9.53-004", ["complex-X-decomposes-to-parts"], "effect",
        cmplx_complex_source,
        [("complex-parts-feature", "result = cmplx(z, kind=rk)", "result = cmplx(aimag(z), real(z, kind=rk), kind=rk)")],
        "For complex X, CMPLX is the same as CMPLX(REAL(X),AIMAG(X),KIND), observed with exact components."
    )
    return {identifier(case.rule, case.variant): case for case in raw}


REMAINING_PENDING = {
    "S16.9.52-002": {"present-KIND-selects-character-kind", "absent-KIND-default-character-kind"},
    "S16.9.53-005": {"inexact-REAL-conversion-not-exact-oracle"},
}


def mutation_records(case: Case):
    records = []
    raw = case.source.encode("ascii")
    completion_line = f"  write(*,'(a)') '{case.completion.rstrip()}'"
    all_mutations = list(case.mutations) + [("completion-omission", completion_line, "! completion omitted")]
    for mid, expected, replacement in all_mutations:
        count = case.source.count(expected)
        if count != 1:
            raise ValueError(f"{case.variant}:{mid} expected unique mutation text {expected!r}, saw {count}")
        start = case.source.index(expected)
        mutated = raw[:start] + replacement.encode("ascii") + raw[start + len(expected):]
        records.append(dict(id=mid, expected=expected, replacement=replacement, span=[start, start + len(expected)], source_sha256=sha(mutated)))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for name, case in make_cases().items():
        raw = case.source.encode("ascii")
        mutations = mutation_records(case)
        profiles = PROFILE_BY_VARIANT.get(case.variant, [])
        spec = dict(id=name, variant=case.variant, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                    source=case.source, source_sha256=sha(raw), completion=case.completion,
                    mutations=mutations, oracle=case.oracle, profiles=profiles)
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case.variant)
        manifest = dict(schema_version=1, id=name, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=case.completion, stderr=""))
        if profiles:
            manifest["profiles"] = profiles
        spec["path"], spec["manifest"] = directory.relative_to(root).as_posix() + "/fixture.json", manifest
        specs[name] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, p in enumerate(paragraphs) if p.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def sync_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    by_rule_facets = {}
    by_rule_oracles = {}
    for spec in specs.values():
        by_rule_facets.setdefault(spec["rule"], set()).update(spec["facets"])
        by_rule_oracles.setdefault(spec["rule"], []).append(spec)
    for rule, facets in by_rule_facets.items():
        row = by_rule[rule]
        if not facets <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + rule)
        for facet in facets:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = rule + f" {TOPIC} fixture: "
        oracle_text = prefix + " ".join(spec["oracle"] for spec in by_rule_oracles[rule])
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, oracle_text)
        limit_prefix = rule + f" {TOPIC} boundaries: "
        limits = (limit_prefix + "This packet supplies only the named single-image run/effect or positive-control fixtures. "
                  "It does not claim diagnostics for unnumbered argument restrictions, coarray behavior, source-review approval, "
                  "nondefault character kinds not guaranteed by the processor, inexact conversion values, or processor-dependent approximations.")
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), limit_prefix, limits)
    for rule, remaining in REMAINING_PENDING.items():
        if rule in by_rule:
            pending = by_rule[rule].setdefault("pending", {})
            for facet in remaining:
                pending.setdefault(facet, "Left pending by intrinsics_16_9_e: no load-bearing portable fixture is shipped for this facet on both validation toolchains.")
            if set(pending) != remaining:
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
    owned_cases = [case for case in make_cases().values() if case.rule.startswith("S" + section + "-")]
    covered = sum(len(case.facets) for case in owned_cases)
    pending_note = ""
    if section == "16.9.52":
        pending_note = " The present-KIND character-kind facet remains pending because no nondefault character kind is guaranteed."
    if section == "16.9.53":
        pending_note = " The inexact REAL-conversion caveat remains pending because it is a non-oracle warning, not an exact runtime effect."
    summary = (SUMMARY_BEGIN + "\n"
        f"## Intrinsics 16.9.E runtime observations\n\n"
        f"This batch adds {len(owned_cases)} generated run/effect or positive-control fixtures for {section}, "
        f"covering {covered} pending facets with exact logical, kind, rank, integer, character round-trip, "
        f"bit-sequence, CEILING, and CMPLX component observations. Mutation metadata perturbs each fixture's "
        f"load-bearing intrinsic expression and completion output; mutation checking compiles each mutant in "
        f"a repository-local scratch directory and requires the mutant not to pass.{pending_note}\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        head, tail = before.split(SUMMARY_BEGIN)
        _, rest_tail = tail.split(SUMMARY_END)
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
        section_specs = {k: v for k, v in specs.items() if v["rule"].startswith("S" + section + "-")}
        updated = sync_catalogue(catalogue, section_specs)
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
            raise ValueError("stale intrinsics_16_9_e generated files: " + ", ".join(stale))
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
    cmd = [str(compiler)]
    cmd.append(("--std=" if "lfortran" in Path(str(compiler)).name.lower() else "-std=") + std)
    cmd += ["source.f90", "-o", "program"]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if comp.returncode != 0:
        return "compile-fail", comp.returncode, comp.stdout, comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if run.returncode == 0:
        return "pass", run.returncode, run.stdout, run.stderr
    return "run-fail", run.returncode, run.stdout, run.stderr


def check_mutations(root, compiler, std, inject_survivor=False):
    root = Path(root)
    _, specs = build_corpus(root)
    workspace = root / ("." + TOPIC + "_mutation_runs") / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    failures, checked, parents = [], 0, 0
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, rc, stdout, stderr = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"))
            if status != "pass" or stdout != spec["completion"] or stderr != "":
                failures.append(f"{spec['id']} parent failed {status} rc={rc}\nstdout={stdout}\nstderr={stderr}")
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
        return parents, checked
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        parents, checked = check_mutations(args.root, args.compiler, args.std, args.inject_surviving_mutant)
        print(f"Mutation-checked {checked} intrinsics_16_9_e mutations across {parents} parents.")
        return
    _, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics 16.9.e cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} mutations.")


if __name__ == "__main__":
    main()
