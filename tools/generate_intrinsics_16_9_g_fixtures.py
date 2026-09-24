#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.67-16.9.70 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_g"
SECTIONS = ("16.9.67", "16.9.68", "16.9.69", "16.9.70")
CATALOGUES = {
    "16.9.67": "doc/catalogues/cpu_time_16_9_67.json",
    "16.9.68": "doc/catalogues/cshift_16_9_68.json",
    "16.9.69": "doc/catalogues/date_and_time_16_9_69.json",
    "16.9.70": "doc/catalogues/dble_16_9_70.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.G FIXTURES {section} -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.G FIXTURES {section} -->"
RESTORED_PENDING = {
    "S16.9.69-010": {
        "values-zone-element-or-negative-huge": (
            "Left pending after intrinsics_16_9_g mutation review: p3 gives the unavailable -HUGE value "
            "and otherwise only says VALUES(4) is a UTC offset in minutes, without a portable single-image "
            "range or exact value that distinguishes an arbitrary non-HUGE sentinel from a conforming offset."
        )
    }
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace(".", "_").replace("-", "_") + f"_valid__{TOPIC}_{variant}"


def completion(variant: str) -> str:
    return "INTRINSICS 16.9.G " + variant.upper().replace("_", " ") + " OK\n"


HELPERS = """contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program {program}
"""


def wrap(variant: str, declarations: str, body: str, extra_contains: str = "") -> str:
    program = "i169g_" + variant
    tail = extra_contains if extra_contains else HELPERS.format(program=program)
    use_lines = ""
    while declarations.startswith("  use "):
        line, declarations = declarations.split("\n", 1)
        use_lines += line + "\n"
    return (
        f"program {program}\n"
        + use_lines
        + "  implicit none\n"
        + declarations
        + body
        + f"  write(*,'(a)') '{completion(variant).rstrip()}'\n"
        + tail
    )


def cshift_matrix_init() -> str:
    return (
        "  m(1,:) = [1, 2, 3]\n"
        "  m(2,:) = [4, 5, 6]\n"
        "  m(3,:) = [7, 8, 9]\n"
    )


def date_helpers(program: str) -> str:
    return f"""contains
  logical function all_digits(s)
    character(len=*), intent(in) :: s
    all_digits = verify(s, '0123456789') == 0
  end function all_digits
  integer function digit_value(c)
    character(len=1), intent(in) :: c
    digit_value = index('0123456789', c) - 1
  end function digit_value
  integer function decimal2(s)
    character(len=*), intent(in) :: s
    decimal2 = 10 * digit_value(s(1:1)) + digit_value(s(2:2))
  end function decimal2
  integer function decimal3(s)
    character(len=*), intent(in) :: s
    decimal3 = 100 * digit_value(s(1:1)) + 10 * digit_value(s(2:2)) + digit_value(s(3:3))
  end function decimal3
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program {program}
"""


def cases():
    data = []

    def add(section, rule, facets, evidence, variant, source, mutations, oracle, profiles=()):
        data.append(dict(section=section, rule=rule, facets=list(facets), evidence=evidence,
                         variant=variant, source=source, mutations=list(mutations), oracle=oracle,
                         profiles=list(profiles)))

    cpu_profile = ["cpu-time-available"]
    add("16.9.67", "S16.9.67-002", ["cpu-time-subroutine-class"], "effect", "cpu_time_subroutine_call",
        wrap("cpu_time_subroutine_call", "  real :: t\n", "  t = -10.0\n  call cpu_time(t)\n  call require_true('cpu_time assigned available value', t >= 0.0)\n"),
        [("feature-cpu-time-call", "call cpu_time(t)", "t = -10.0")],
        "CALL CPU_TIME(T) is executed as a subroutine; the cpu-time-available profile restricts the run to processors where the assigned TIME value is nonnegative rather than the unavailable negative branch.", cpu_profile)
    add("16.9.67", "S16.9.67-003", ["cpu-time-time-real-scalar"], "positive-control", "cpu_time_real_scalar_argument",
        wrap("cpu_time_real_scalar_argument", "  real :: t, sink\n", "  t = -10.0\n  sink = -10.0\n  call cpu_time(t)\n  call require_true('real scalar actual receives time', t >= 0.0)\n"),
        [("feature-time-actual-swapped", "call cpu_time(t)", "call cpu_time(sink)")],
        "A default real scalar variable is the TIME actual argument in a conforming CALL CPU_TIME; the available-time profile makes the scalar assignment observable without requiring an exact duration.", cpu_profile)
    add("16.9.67", "S16.9.67-004", ["cpu-time-time-intent-out"], "effect", "cpu_time_intent_out_assignment",
        wrap("cpu_time_intent_out_assignment", "  real :: t, sink\n", "  t = -10.0\n  sink = -10.0\n  call cpu_time(t)\n  call require_true('intent out actual overwritten', t /= -10.0 .and. t >= 0.0)\n"),
        [("feature-time-actual-swapped", "call cpu_time(t)", "call cpu_time(sink)")],
        "With cpu-time-available satisfied, a distinguished negative sentinel real actual is overwritten by CALL CPU_TIME, observing the INTENT(OUT) assignment without asserting exact seconds.", cpu_profile)

    add("16.9.68", "S16.9.68-001", ["cshift-circular-shift-description"], "effect", "cshift_circular_description",
        wrap("cshift_circular_description", "  integer :: v(6), left(6), right(6)\n",
             "  v = [1, 2, 3, 4, 5, 6]\n  left = cshift(v, 2)\n  right = cshift(v, -2)\n  call require_true('left circular shift', all(left == [3, 4, 5, 6, 1, 2]))\n  call require_true('right circular shift', all(right == [5, 6, 1, 2, 3, 4]))\n"),
        [("feature-left-shift-distance", "left = cshift(v, 2)", "left = cshift(v, 1)")],
        "Rank-one exact integer arrays observe CSHIFT as a circular left shift for positive SHIFT and right shift for negative SHIFT by the p5 formula.")
    add("16.9.68", "S16.9.68-002", ["cshift-transformational-class"], "effect", "cshift_transformational_rank",
        wrap("cshift_transformational_rank", "  integer :: rect(2,3)\n",
             "  rect(1,:) = [1, 2, 3]\n  rect(2,:) = [4, 5, 6]\n  call require_true('rank two result preserved', size(shape(cshift(rect, 1, dim=1))) == 2)\n  call require_true('whole array transformed shape', all(shape(cshift(rect, 1, dim=1)) == [2, 3]))\n"),
        [("feature-transform-result-expression",
          "all(shape(cshift(rect, 1, dim=1)) == [2, 3])",
          "all(shape(transpose(cshift(rect, 1, dim=1))) == [2, 3])")],
        "A rank-two ARRAY is transformed as a whole array: direct RANK and SHAPE inquiries on CSHIFT show a rank-two array result, not a scalar elemental mapping.")
    add("16.9.68", "S16.9.68-008", ["cshift-array-any-type-array"], "effect", "cshift_integer_character_arrays",
        wrap("cshift_integer_character_arrays", "  integer :: iv(4)\n  character(len=3) :: words(4), shifted(4)\n",
             "  iv = [10, 20, 30, 40]\n  words = [character(len=3) :: 'aa1', 'bb2', 'cc3', 'dd4']\n  shifted = cshift(words, 1)\n  call require_true('integer array shifted', all(cshift(iv, -1) == [40, 10, 20, 30]))\n  call require_true('character array shifted', &\n       len(cshift(words, 1)) == 3 .and. &\n       all(shifted == [character(len=3) :: 'bb2', 'cc3', 'dd4', 'aa1']))\n"),
        [("feature-character-shift-distance", "shifted = cshift(words, 1)", "shifted = cshift(words, 2)")],
        "The same CSHIFT operation is applied to integer and length-three character arrays; exact values and LEN show the any-type ARRAY admission is load-bearing.")
    add("16.9.68", "S16.9.68-003",
        ["cshift-shift-integer-scalar-for-rank-one", "cshift-shift-scalar-or-rank-minus-one-shape", "cshift-dim-integer-scalar-in-range"],
        "positive-control", "cshift_argument_controls",
        wrap("cshift_argument_controls", "  integer :: v(6), m(3,3), r(3,3), expected(3,3)\n",
             "  v = [1, 2, 3, 4, 5, 6]\n" + cshift_matrix_init() +
             "  call require_true('rank one scalar integer shift', all(cshift(v, 2) == [3, 4, 5, 6, 1, 2]))\n"
             "  r = cshift(m, shift=[-1, 1, 0], dim=2)\n  expected(1,:) = [3, 1, 2]\n  expected(2,:) = [5, 6, 4]\n  expected(3,:) = [7, 8, 9]\n  call require_true('rank two vector shift shape', all(r == expected))\n"
             "  r = cshift(m, shift=1, dim=1)\n  expected(1,:) = [4, 5, 6]\n  expected(2,:) = [7, 8, 9]\n  expected(3,:) = [1, 2, 3]\n  call require_true('dim one in range selected', all(r == expected))\n"),
        [("feature-rank-one-shift", "cshift(v, 2)", "cshift(v, 1)"),
         ("feature-shift-vector-values", "shift=[-1, 1, 0]", "shift=[0, 0, 0]"),
         ("feature-dim-selection", "r = cshift(m, shift=1, dim=1)", "r = cshift(m, shift=1, dim=2)")],
        "Conforming CSHIFT calls use scalar integer SHIFT for rank one, a rank-one SHIFT vector whose shape is the non-DIM extent for rank two, and DIM=1 within the rank range; exact results distinguish each argument property.")
    add("16.9.68", "S16.9.68-004", ["cshift-absent-dim-defaults-to-one"], "effect", "cshift_absent_dim_default",
        wrap("cshift_absent_dim_default", "  integer :: m(3,3), expected(3,3)\n",
             cshift_matrix_init() +
             "  expected(1,:) = [4, 5, 6]\n  expected(2,:) = [7, 8, 9]\n  expected(3,:) = [1, 2, 3]\n  call require_true('absent dim acts as dim one', all(cshift(m, 1) == expected))\n  call require_true('dim two would differ', any(cshift(m, 1, dim=2) /= expected))\n"),
        [("feature-absent-dim-to-dim-two", "cshift(m, 1) == expected", "cshift(m, 1, dim=2) == expected")],
        "For a rank-two array where DIM=1 and DIM=2 differ, CSHIFT(M,1) has exactly the DIM=1 section-shift value, proving the absent-DIM default.")
    add("16.9.68", "S16.9.68-005", ["cshift-result-type-parameters-of-array", "cshift-result-shape-of-array"], "effect", "cshift_result_characteristics",
        wrap("cshift_result_characteristics", "  character(len=3) :: words(4)\n  integer :: rect(2,3)\n",
             "  words = [character(len=3) :: 'aa1', 'bb2', 'cc3', 'dd4']\n  rect(1,:) = [1, 2, 3]\n  rect(2,:) = [4, 5, 6]\n  call require_true('character length parameter preserved', len(cshift(words, 1)) == 3)\n  call require_true('rank two shape preserved', all(shape(cshift(rect, 1, dim=2)) == [2, 3]))\n"),
        [("feature-character-length-parameter", "character(len=3) :: words(4)", "character(len=4) :: words(4)"),
         ("feature-shape-expression", "shape(cshift(rect, 1, dim=2))", "shape(transpose(cshift(rect, 1, dim=2)))")],
        "Direct LEN and SHAPE inquiries on CSHIFT expressions show the result keeps ARRAY's character length parameter and non-square rank-two shape.")
    add("16.9.68", "S16.9.68-006", ["cshift-rank-one-left-right-values"], "effect", "cshift_rank_one_values",
        wrap("cshift_rank_one_values", "  integer :: v(6), left(6), right(6)\n",
             "  v = [1, 2, 3, 4, 5, 6]\n  left = cshift(v, 2)\n  right = cshift(v, -2)\n  call require_true('rank one left formula', all(left == [3, 4, 5, 6, 1, 2]))\n  call require_true('rank one right formula', all(right == [5, 6, 1, 2, 3, 4]))\n"),
        [("feature-rank-one-left-distance", "left = cshift(v, 2)", "left = cshift(v, 1)")],
        "The p5 rank-one MODULO formula gives exact left and right rotations for SHIFT=2 and SHIFT=-2 on [1..6].")
    add("16.9.68", "S16.9.68-007", ["cshift-rank-two-dim-section-values", "cshift-rank-two-shift-vector-values"], "effect", "cshift_rank_two_sections",
        wrap("cshift_rank_two_sections", "  integer :: m(3,3), r(3,3), expected(3,3)\n",
             cshift_matrix_init() +
             "  r = cshift(m, shift=-1, dim=2)\n  expected(1,:) = [3, 1, 2]\n  expected(2,:) = [6, 4, 5]\n  expected(3,:) = [9, 7, 8]\n  call require_true('rank two scalar shift along dim two', all(r == expected))\n"
             "  r = cshift(m, shift=[-1, 1, 0], dim=2)\n  expected(1,:) = [3, 1, 2]\n  expected(2,:) = [5, 6, 4]\n  expected(3,:) = [7, 8, 9]\n  call require_true('rank two vector shifts by section', all(r == expected))\n"),
        [("feature-rank-two-dim", "r = cshift(m, shift=-1, dim=2)", "r = cshift(m, shift=-1, dim=1)"),
         ("feature-rank-two-shift-vector", "shift=[-1, 1, 0]", "shift=[0, 0, 0]")],
        "Rank-two CSHIFT is checked section-by-section along DIM=2, once with a scalar SHIFT and once with a per-row SHIFT vector.")

    date_profile = ["date-and-time-date-available"]
    time_profile = ["date-and-time-time-available"]
    zone_profile = ["date-and-time-zone-available"]
    values_date_time_profiles = [
        "date-and-time-values-1-available", "date-and-time-values-2-available",
        "date-and-time-values-3-available", "date-and-time-values-4-available",
        "date-and-time-values-5-available", "date-and-time-values-6-available", "date-and-time-values-7-available",
        "date-and-time-values-8-available"]
    add("16.9.69", "S16.9.69-002", ["date-and-time-subroutine-class"], "effect", "date_and_time_subroutine_call",
        wrap("date_and_time_subroutine_call", "  character(len=8) :: date_value\n",
             "  date_value = '########'\n  call date_and_time(date=date_value)\n  call require_true('subroutine call assigned date', verify(date_value, '0123456789') == 0)\n"),
        [("feature-date-and-time-call", "call date_and_time(date=date_value)", "date_value = '########'")],
        "CALL DATE_AND_TIME is executed as a subroutine; the availability profile selects the date-available branch, so the DATE actual receives required decimal digits.", date_profile)
    add("16.9.69", "S16.9.69-004", ["date-yyyy-mm-dd-digits-or-blanks"], "effect", "date_and_time_date_digits",
        wrap("date_and_time_date_digits", "  character(len=8) :: date_value, date_sink\n  integer :: month, day\n",
             "  date_value = '########'\n  date_sink = '!!!!!!!!'\n  call date_and_time(date_value)\n  month = decimal2(date_value(5:6))\n  day = decimal2(date_value(7:8))\n  call require_true('date has eight digits', len(date_value) == 8 .and. all_digits(date_value))\n  call require_true('date month day positions', month >= 1 .and. month <= 12 .and. day >= 1 .and. day <= 31)\n",
             date_helpers("i169g_date_and_time_date_digits")),
        [("feature-date-actual-swapped", "call date_and_time(date_value)", "call date_and_time(date_sink)")],
        "With date availability profiled, DATE is not the all-blank fallback; it has the required YYYYMMDD digit form with month/day substrings in their source-specified positions.", date_profile)
    add("16.9.69", "S16.9.69-006", ["time-hhmmss-sss-digits-dot-or-blanks"], "effect", "date_and_time_time_digits",
        wrap("date_and_time_time_digits", "  character(len=10) :: time_value, time_sink\n  integer :: hour, minute, second, millis\n",
             "  time_value = '##########'\n  time_sink = '!!!!!!!!!!'\n  call date_and_time(time=time_value)\n  hour = decimal2(time_value(1:2))\n  minute = decimal2(time_value(3:4))\n  second = decimal2(time_value(5:6))\n  millis = decimal3(time_value(8:10))\n  call require_true('time digits and decimal point', &\n       len(time_value) == 10 .and. time_value(7:7) == '.' .and. &\n       all_digits(time_value(1:6)//time_value(8:10)))\n  call require_true('time fields in source ranges', &\n       hour >= 0 .and. hour <= 23 .and. minute >= 0 .and. minute <= 59 .and. &\n       second >= 0 .and. second <= 60 .and. millis >= 0 .and. millis <= 999)\n",
             date_helpers("i169g_date_and_time_time_digits")),
        [("feature-time-actual-swapped", "call date_and_time(time=time_value)", "call date_and_time(time=time_sink)")],
        "With clock availability profiled, TIME is not the all-blank fallback; it has hhmmss.sss syntax and each numeric field lies in the ranges fixed by p3.", time_profile)
    add("16.9.69", "S16.9.69-008", ["zone-signed-hhmm-digits-or-blanks"], "effect", "date_and_time_zone_digits",
        wrap("date_and_time_zone_digits", "  character(len=5) :: zone_value, zone_sink\n",
             "  zone_value = '#####'\n  zone_sink = '!!!!!'\n  call date_and_time(zone=zone_value)\n  call require_true('zone sign and digits', &\n       len(zone_value) == 5 .and. &\n       (zone_value(1:1) == '+' .or. zone_value(1:1) == '-') .and. &\n       verify(zone_value(2:5), '0123456789') == 0)\n"),
        [("feature-zone-actual-swapped", "call date_and_time(zone=zone_value)", "call date_and_time(zone=zone_sink)")],
        "With time-zone availability profiled, ZONE is not the all-blank fallback; it has the required sign followed by four decimal digits.", zone_profile)
    add("16.9.69", "S16.9.69-010", ["values-date-elements-or-negative-huge", "values-time-elements-or-negative-huge", "values-zone-element-or-negative-huge"], "effect", "date_and_time_values_ranges",
        wrap("date_and_time_values_ranges", "  integer :: date_values(8), time_values(8), zone_values(8), values_sink(8)\n  integer :: zone_minutes\n  character(len=5) :: zone_value\n",
             "  date_values = 123456789\n  time_values = 123456789\n  zone_values = 123456789\n  values_sink = 123456789\n  zone_value = '#####'\n  call date_and_time(values=date_values)\n  call require_true('values date fields available and ranged', &\n       date_values(1) /= -huge(date_values(1)) .and. &\n       date_values(2) >= 1 .and. date_values(2) <= 12 .and. &\n       date_values(3) >= 1 .and. date_values(3) <= 31)\n  call date_and_time(values=time_values)\n  call require_true('values time fields available and ranged', &\n       all(time_values(5:8) /= -huge(time_values(1))) .and. &\n       time_values(5) >= 0 .and. time_values(5) <= 23 .and. &\n       time_values(6) >= 0 .and. time_values(6) <= 59 .and. &\n       time_values(7) >= 0 .and. time_values(7) <= 60 .and. &\n       time_values(8) >= 0 .and. time_values(8) <= 999)\n  call date_and_time(zone=zone_value, values=zone_values)\n  zone_minutes = 60 * decimal2(zone_value(2:3)) + decimal2(zone_value(4:5))\n  if (zone_value(1:1) == '-') zone_minutes = -zone_minutes\n  call require_true('values zone agrees with zone argument', &\n       zone_values(4) /= -huge(zone_values(1)) .and. zone_values(4) == zone_minutes)\n",
             date_helpers("i169g_date_and_time_values_ranges")),
        [("feature-values-date-actual-swapped", "call date_and_time(values=date_values)", "call date_and_time(values=values_sink)"),
         ("feature-values-time-actual-swapped", "call date_and_time(values=time_values)", "call date_and_time(values=values_sink)"),
         ("feature-values-zone-compare-wrong-field", "zone_values(4) == zone_minutes", "zone_values(5) == zone_minutes")],
        "The per-field VALUES availability profiles select the available branches, so VALUES(1:3) and VALUES(5:8) are checked against the p3 ranges, and a same-call ZONE/VALUES observation checks VALUES(4) is the parsed UTC offset in minutes.", values_date_time_profiles + zone_profile)

    add("16.9.70", "S16.9.70-001", ["dble-conversion-description"], "effect", "dble_conversion_description",
        wrap("dble_conversion_description", "  double precision :: y\n",
             "  y = dble(-3)\n  call require_true('dble converts integer to double value', kind(y) == kind(0.0d0) .and. y == -3.0d0)\n"),
        [("feature-dble-conversion-sign", "y = dble(-3)", "y = dble(3)")],
        "DBLE(-3) is assigned to a double precision result and has the exact REAL(A,KIND(0.0D0)) value -3.0D0.")
    add("16.9.70", "S16.9.70-002", ["dble-elemental-class"], "effect", "dble_elemental_array",
        wrap("dble_elemental_array", "  integer :: input(3)\n  double precision :: output(3)\n",
             "  input = [-3, 0, 5]\n  output = dble(input)\n  call require_true('elemental array shape direct', all(shape(dble(input)) == [3]))\n  call require_true('elemental element values', all(output == [-3.0d0, 0.0d0, 5.0d0]))\n"),
        [("feature-dble-array-expression", "shape(dble(input))", "shape([dble(input(1))])")],
        "As an elemental function, DBLE applied to a rank-one integer array yields a rank-one result with corresponding exact converted elements.")
    add("16.9.70", "S16.9.70-003", ["dble-a-integer-real-complex-or-boz"], "positive-control", "dble_argument_forms",
        wrap("dble_argument_forms", "  integer, parameter :: boz_words = (storage_size(0.0d0) + storage_size(0) - 1) / storage_size(0)\n  integer :: boz_bits(boz_words), ref_bits(boz_words)\n  complex :: z\n",
             "  z = cmplx(-4.0, 7.0)\n  boz_bits = transfer(dble(z'0000000000000001'), boz_bits, boz_words)\n  ref_bits = transfer(real(z'0000000000000001', kind(0.0d0)), ref_bits, boz_words)\n  call require_true('all dble argument forms reached', &\n       dble(-3) == -3.0d0 .and. dble(-2.5) == -2.5d0 .and. &\n       dble(z) == -4.0d0 .and. all(boz_bits == ref_bits))\n"),
        [("feature-boz-dble-actual", "dble(z'0000000000000001')", "dble(z'0000000000000002')")],
        "The positive control reaches DBLE with integer, exactly representable real, complex, and BOZ literal actual arguments; BOZ is checked only by equality to REAL of the same BOZ literal and double kind.")
    add("16.9.70", "S16.9.70-004", ["dble-result-double-precision-real"], "effect", "dble_result_kind",
        wrap("dble_result_kind", "  integer :: input(2)\n",
             "  input = [1, 2]\n  call require_true('scalar result double precision kind', kind(dble(1)) == kind(0.0d0))\n  call require_true('array result double precision kind', kind(dble(input)) == kind(0.0d0) .and. all(shape(dble(input)) == [2]))\n"),
        [("feature-dble-kind-expression", "kind(dble(1))", "kind(real(1))")],
        "Direct KIND inquiries on scalar and array DBLE expressions show the result kind is KIND(0.0D0), i.e. double precision real.")
    add("16.9.70", "S16.9.70-005",
        ["dble-integer-real-conversion-value", "dble-real-real-conversion-value", "dble-complex-real-part-conversion-value", "dble-boz-real-conversion-delegates-to-real"],
        "effect", "dble_result_values",
        wrap("dble_result_values", "  integer, parameter :: boz_words = (storage_size(0.0d0) + storage_size(0) - 1) / storage_size(0)\n  complex :: z\n  integer :: dble_bits(boz_words), real_bits(boz_words)\n",
             "  z = cmplx(-4.0, 7.0)\n  dble_bits = transfer(dble(z'0000000000000001'), dble_bits, boz_words)\n  real_bits = transfer(real(z'0000000000000001', kind(0.0d0)), real_bits, boz_words)\n  call require_true('integer conversions exact', dble(-3) == -3.0d0 .and. dble(5) == 5.0d0)\n  call require_true('real conversions exact', dble(-2.5) == -2.5d0 .and. dble(0.5) == 0.5d0)\n  call require_true('complex real part converted', dble(z) == -4.0d0)\n  call require_true('boz delegates to real representation', all(dble_bits == real_bits))\n"),
        [("feature-integer-conversion-value", "dble(-3) == -3.0d0", "dble(-4) == -3.0d0"),
         ("feature-real-conversion-value", "dble(-2.5) == -2.5d0", "dble(-3.5) == -2.5d0"),
         ("feature-complex-real-part", "dble(z) == -4.0d0", "dble(cmplx(7.0, -4.0)) == -4.0d0"),
         ("feature-boz-literal-equivalence", "real(z'0000000000000001', kind(0.0d0))", "real(z'0000000000000002', kind(0.0d0))")],
        "DBLE(A) is compared with exact double precision results for integer and exactly representable real A, with the converted real part for complex A, and with REAL(A,KIND(0.0D0)) by bit transfer for BOZ A.")

    return data


def mutation_records(case):
    records = []
    source = case["source"]
    raw = source.encode("ascii")
    for facet_index, (mid, expected, replacement) in enumerate(case["mutations"], 1):
        if source.count(expected) != 1:
            raise ValueError(f"{case['variant']} mutation {mid} token count is {source.count(expected)}: {expected!r}")
        start = source.index(expected)
        record = dict(id=mid, kind="feature", category="intrinsic-feature", expected=expected,
                      replacement=replacement, span=[start, start + len(expected)],
                      mutation="facet-feature-mutation", line=source[:start].count("\n") + 1)
        if raw[start:start + len(expected)].decode("ascii") != expected:
            raise ValueError("mutation span lost parent binding")
        records.append(record)
    completion_line = f"  write(*,'(a)') '{completion(case['variant']).rstrip()}'"
    if source.count(completion_line) != 1:
        raise ValueError("completion line missing for " + case["variant"])
    start = source.index(completion_line)
    records.append(dict(id="completion-output-omission", kind="output", category="completion",
                        expected=completion_line, replacement="! completion omitted",
                        span=[start, start + len(completion_line)], mutation="completion-omission",
                        line=source[:start].count("\n") + 1))
    return records


def source_specs():
    specs = {}
    for case in cases():
        raw = case["source"].encode("ascii")
        spec_id = identifier(case["rule"], case["variant"])
        mutations = mutation_records(case)
        specs[spec_id] = dict(id=spec_id, variant=case["variant"], section=case["section"], rule=case["rule"],
                              facets=case["facets"], evidence=case["evidence"], source=case["source"],
                              source_sha256=sha(raw), completion=completion(case["variant"]),
                              mutations=mutations, oracle=case["oracle"], profiles=case["profiles"])
    return specs


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = root / "tests" / "fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=spec["completion"], stderr=""))
        if spec["profiles"]:
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def profile_files(root=ROOT):
    root = Path(root)
    return {
        root / "tests" / "profiles" / "cpu_time_available.f90": b"program cpu_time_available\n  implicit none\n  real :: t\n  t = -10.0\n  call cpu_time(t)\n  if (.not. (t >= 0.0)) stop 77\nend program cpu_time_available\n",
        root / "tests" / "profiles" / "date_and_time_date_available.f90": b"program date_and_time_date_available\n  implicit none\n  character(len=8) :: d\n  d = '########'\n  call date_and_time(date=d)\n  if (verify(d, '0123456789') /= 0) stop 77\nend program date_and_time_date_available\n",
        root / "tests" / "profiles" / "date_and_time_time_available.f90": b"program date_and_time_time_available\n  implicit none\n  character(len=10) :: t\n  t = '##########'\n  call date_and_time(time=t)\n  if (t(7:7) /= '.') stop 77\n  if (verify(t(1:6)//t(8:10), '0123456789') /= 0) stop 77\nend program date_and_time_time_available\n",
        root / "tests" / "profiles" / "date_and_time_zone_available.f90": b"program date_and_time_zone_available\n  implicit none\n  character(len=5) :: z\n  z = '#####'\n  call date_and_time(zone=z)\n  if (.not. (z(1:1) == '+' .or. z(1:1) == '-')) stop 77\n  if (verify(z(2:5), '0123456789') /= 0) stop 77\nend program date_and_time_zone_available\n",
        root / "tests" / "profiles" / "date_and_time_values_1_available.f90": b"program date_and_time_values_1_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(1) == -huge(v(1))) stop 77\nend program date_and_time_values_1_available\n",
        root / "tests" / "profiles" / "date_and_time_values_2_available.f90": b"program date_and_time_values_2_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(2) == -huge(v(1))) stop 77\nend program date_and_time_values_2_available\n",
        root / "tests" / "profiles" / "date_and_time_values_3_available.f90": b"program date_and_time_values_3_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(3) == -huge(v(1))) stop 77\nend program date_and_time_values_3_available\n",
        root / "tests" / "profiles" / "date_and_time_values_4_available.f90": b"program date_and_time_values_4_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(4) == -huge(v(1))) stop 77\nend program date_and_time_values_4_available\n",
        root / "tests" / "profiles" / "date_and_time_values_5_available.f90": b"program date_and_time_values_5_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(5) == -huge(v(1))) stop 77\nend program date_and_time_values_5_available\n",
        root / "tests" / "profiles" / "date_and_time_values_6_available.f90": b"program date_and_time_values_6_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(6) == -huge(v(1))) stop 77\nend program date_and_time_values_6_available\n",
        root / "tests" / "profiles" / "date_and_time_values_7_available.f90": b"program date_and_time_values_7_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(7) == -huge(v(1))) stop 77\nend program date_and_time_values_7_available\n",
        root / "tests" / "profiles" / "date_and_time_values_8_available.f90": b"program date_and_time_values_8_available\n  implicit none\n  integer :: v(8)\n  v = 123456789\n  call date_and_time(values=v)\n  if (v(8) == -huge(v(1))) stop 77\nend program date_and_time_values_8_available\n",
    }


def sync_catalogue(section, catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for rule, reasons in RESTORED_PENDING.items():
        if rule in by_rule:
            pending = by_rule[rule].setdefault("pending", {})
            for facet, reason in reasons.items():
                if facet not in covered.get(rule, set()):
                    pending[facet] = reason
    for spec in specs.values():
        if spec["section"] != section:
            continue
        row = by_rule[spec["rule"]]
        if not set(spec["facets"]) <= set(row["facets"]):
            raise ValueError("selected facets changed for " + spec["rule"])
        for facet in spec["facets"]:
            row.setdefault("pending", {}).pop(facet, None)
        row.setdefault("pending", {})
        prefix = f"{spec['rule']} {TOPIC} runtime fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + spec["oracle"])
        limit_prefix = f"{spec['rule']} {TOPIC} fixture boundaries: "
        limitation = ("This packet supplies only the named single-image valid fixture facets. "
                      "Unnumbered argument restrictions are positive controls only; no rejection diagnostic, "
                      "processor-dependent exact time, current calendar value, coarray behavior, source review, "
                      "evidence link, or fixture approval is asserted. Profiled CPU_TIME and DATE_AND_TIME cases "
                      "require the available branch and do not count unavailable fallback behavior as covered.")
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), limit_prefix,
                                                    limit_prefix + limitation)
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
    specs = [spec for spec in source_specs().values() if spec["section"] == section]
    facet_count = sum(len(spec["facets"]) for spec in specs)
    owned_begin, owned_end = SUMMARY_BEGIN.format(section=section), SUMMARY_END.format(section=section)
    summary = (owned_begin + "\n\n"
               f"## `{TOPIC}` executable fixture observations\n\n"
               f"This packet adds {len(specs)} generated run/f2023 fixture(s) for {section}, covering {facet_count} portable facet(s). "
               "CSHIFT and DBLE use exact values, direct characteristics inquiries, and BOZ bit-equivalence where required. "
               "CPU_TIME and DATE_AND_TIME fixtures are guarded by processor profiles that require the available branch, so unavailable fallback branches remain pending where not directly observed.\n"
               + owned_end)
    if owned_begin in before or owned_end in before:
        if before.count(owned_begin) != 1 or before.count(owned_end) != 1:
            raise ValueError("fixture summary boundaries changed for " + section)
        head, tail = before.split(owned_begin)
        _, rest_tail = tail.split(owned_end)
        before = head + summary + rest_tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    generated = "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n"
    return before + begin + generated + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    profiles = profile_files(root)
    files.update(profiles)
    updated_catalogues, updated_views = {}, {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        updated = sync_catalogue(section, catalogue, specs)
        updated_catalogues[rel] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for rel, updated in updated_catalogues.items():
            if json.loads((root / rel).read_text()) != updated:
                stale.append(rel)
        for rel, text in updated_views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise ValueError("stale intrinsics_16_9_g generated files: " + ", ".join(stale))
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
        raise ValueError("mutation span lost complete parent binding")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def std_args(compiler, std):
    name = Path(str(compiler)).name.lower()
    if "gfortran" in name:
        return ["-std=" + std]
    return ["--std=" + std]


def compile_and_run(workdir, compiler, std, source_bytes, expected_stdout, timeout=30):
    workdir.mkdir(parents=True, exist_ok=True)
    source = workdir / "source.f90"
    exe = workdir / "program"
    source.write_bytes(source_bytes)
    cmd = [str(compiler)] + std_args(compiler, std) + [str(source), "-o", str(exe)]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if comp.returncode != 0:
        return dict(status="compile-fail", returncode=comp.returncode, stdout=comp.stdout, stderr=comp.stderr)
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    passed = run.returncode == 0 and run.stdout == expected_stdout and run.stderr == ""
    return dict(status="pass" if passed else "run-fail", returncode=run.returncode, stdout=run.stdout, stderr=run.stderr)


def run_mutations(root, compiler, std, inject_survivor=False):
    root = Path(root)
    specs = source_specs()
    work = root / ("scratch_" + TOPIC + "_mutations") / sha((str(compiler) + std).encode())[:12]
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    checked = 0
    failures = []
    try:
        for case_index, spec in enumerate(specs.values(), 1):
            parent_dir = work / f"{case_index:03d}_{spec['variant']}_parent"
            parent = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"), spec["completion"])
            if parent["status"] != "pass":
                failures.append((spec["id"], "parent", parent))
                continue
            for mutation_index, mutation in enumerate(spec["mutations"], 1):
                checked += 1
                mutant = spec["source"].encode("ascii") if inject_survivor and checked == 1 else mutate_source(spec, mutation)
                result = compile_and_run(work / f"{case_index:03d}_{mutation_index:03d}_{mutation['id']}",
                                         compiler, std, mutant, spec["completion"])
                if result["status"] == "compile-fail" or result["status"] == "pass":
                    failures.append((spec["id"], mutation["id"], result))
        if failures:
            lines = [f"mutation check failed for {len(failures)} item(s)"]
            for case_id, mutation_id, result in failures[:20]:
                lines.append(f"{case_id} {mutation_id}: status={result['status']} rc={result['returncode']}")
                lines.append("stdout=" + result["stdout"][:500].replace("\n", "\\n"))
                lines.append("stderr=" + result["stderr"][:500].replace("\n", "\\n"))
            raise RuntimeError("\n".join(lines))
        return checked, len(specs)
    finally:
        shutil.rmtree(work, ignore_errors=True)


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
    if sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check))) > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.inject_surviving_mutant and not args.mutation_check:
        parser.error("--inject-surviving-mutant requires --mutation-check")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        checked, parents = run_mutations(args.root, args.compiler, args.std, args.inject_surviving_mutant)
        print(f"Mutation check OK: {parents}/{parents} parents passed; {checked}/{checked} mutants failed as expected.")
        return
    files, specs = generate(args.root, args.check, args.sync_catalogues)
    mutation_total = sum(len(spec["mutations"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} {TOPIC} cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, {mutation_total} mutations.")


if __name__ == "__main__":
    main()
