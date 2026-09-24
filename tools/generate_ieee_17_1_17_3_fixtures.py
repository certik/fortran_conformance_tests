#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 IEEE overview, constants, and exceptions."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "ieee_17_1_17_3"
SUMMARY_BEGIN = "<!-- BEGIN IEEE 17.1-17.3 FIXTURES -->"
SUMMARY_END = "<!-- END IEEE 17.1-17.3 FIXTURES -->"

CATALOGUES = {
    "doc/catalogues/ieee_types_constants_17_2.json": ("17.2", "doc/fortran_2023_17_2.md"),
    "doc/catalogues/ieee_exceptions_17_3.json": ("17.3", "doc/fortran_2023_17_3.md"),
}


CASES = [
    dict(variant="class_constants_core", rule="S17.2-003",
         catalogue="doc/catalogues/ieee_types_constants_17_2.json",
         facets=["ieee-class-type-listed-class-constants",
                 "ieee-denormal-class-aliases-equal-subnormal-classes",
                 "ieee-class-type-values-comparable"],
         profiles=["ieee-binary"],
         title="IEEE class constants and comparison operators", builder="class_constants_core"),
    dict(variant="round_constants_core", rule="S17.2-004",
         catalogue="doc/catalogues/ieee_types_constants_17_2.json",
         facets=["ieee-round-type-listed-rounding-constants",
                 "ieee-other-rounding-constant-defined",
                 "ieee-types-equality-operator-same-values",
                 "ieee-types-inequality-operator-different-values"],
         profiles=["ieee-binary"],
         title="IEEE round constants and comparison operators", builder="round_constants_core"),
    dict(variant="exception_arrays_status", rule="S17.2-002",
         catalogue="doc/catalogues/ieee_types_constants_17_2.json",
         facets=["ieee-flag-type-values-are-named-exception-constants",
                 "ieee-usual-array-has-overflow-divide-invalid",
                 "ieee-all-array-extends-usual-underflow-inexact",
                 "ieee-modes-status-types-defined"],
         profiles=["ieee-flags-all"],
         title="IEEE exception flag arrays and modes/status types", builder="exception_arrays_status"),
    dict(variant="flag_lifecycle", rule="S17.3-005",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["flags-initially-quiet",
                 "set-flag-and-set-status-change-flag-status",
                 "signaling-flag-persists-until-set-quiet"],
         profiles=["ieee-flag-overflow"],
         title="IEEE flag initial state, setters, and persistence", builder="flag_lifecycle"),
    dict(variant="procedure_flag_semantics", rule="S17.3-006",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["flag-signaled-inside-procedure-not-quieted-on-return"],
         profiles=["ieee-flag-divide"],
         title="IEEE flag signaled inside a procedure remains signaling on return",
         builder="procedure_flag_semantics"),
    dict(variant="exception_overflow", rule="S17.3-001",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["overflow-signals-for-supported-real-arithmetic"],
         profiles=["ieee-flag-overflow"],
         title="Supported IEEE overflow operation sets overflow flag", builder="exception_overflow"),
    dict(variant="exception_divide", rule="S17.3-002",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["divide-by-zero-signals-for-supported-real-division"],
         profiles=["ieee-flag-divide"],
         title="Supported IEEE division by zero sets divide flag", builder="exception_divide"),
    dict(variant="exception_invalid_sqrt", rule="S17.3-003",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["invalid-signals-for-negative-real-sqrt"],
         profiles=["ieee-flag-invalid-nan"],
         title="Supported negative real SQRT sets invalid flag", builder="exception_invalid_sqrt"),
    dict(variant="exception_underflow_inexact", rule="S17.3-004",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["underflow-signals-for-inexact-tiny-real-result-under-support",
                 "inexact-signals-for-inexact-real-result-under-support"],
         profiles=["ieee-flag-underflow-inexact"],
         title="Supported underflow and inexact operations set flags", builder="exception_underflow_inexact"),
    dict(variant="relational_invalid_table", rule="S17.3-009",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["real-less-less-equal-greater-greater-equal-quiet-nan-signal-invalid",
                 "real-equality-inequality-quiet-nan-do-not-signal-invalid",
                 "relational-operator-predicate-mapping-table"],
         profiles=["ieee-flag-invalid-nan"],
         title="IEEE relational invalid predicate mapping", builder="relational_invalid_table"),
    dict(variant="masking_no_extra_operations", rule="S17.3-012",
         catalogue="doc/catalogues/ieee_exceptions_17_3.json",
         facets=["no-signal-from-unexecuted-if-branch-operation",
                 "no-signal-from-masked-where-operation"],
         profiles=["ieee-flag-divide"],
         title="No signal from unexecuted IF and masked WHERE operations", builder="masking_no_extra_operations"),
]

ORACLE_PARAGRAPHS = {
    ("doc/catalogues/ieee_types_constants_17_2.json", "S17.2-002"):
        "S17.2-002 IEEE exception type fixture: with the ieee-flags-all profile requiring all five "
        "default-real flags to be supported and nonhalting, the program imports IEEE_ARITHMETIC only, "
        "declares IEEE_MODES_TYPE and IEEE_STATUS_TYPE dummies, and uses IEEE_SET_FLAG/IEEE_GET_FLAG "
        "to prove the scalar flag constants, IEEE_USUAL ordering, and IEEE_ALL extension.",
    ("doc/catalogues/ieee_types_constants_17_2.json", "S17.2-003"):
        "S17.2-003 IEEE class constant fixture: the program imports the listed class constants "
        "from IEEE_ARITHMETIC and OPERATOR(==)/OPERATOR(/=), assigns them to IEEE_CLASS_TYPE "
        "objects, checks selected distinct named values, checks DENORMAL aliases equal the corresponding "
        "SUBNORMAL constants, and checks same-value/different-value comparisons. This is intentionally "
        "IEEE_ARITHMETIC-only: S17.1 p1 makes module provision processor dependent, but if "
        "IEEE_ARITHMETIC is provided it defines these S17.2 p3 public constants; the frozen target "
        "provides IEEE_ARITHMETIC but omits IEEE_NEGATIVE_SUBNORMAL.",
    ("doc/catalogues/ieee_types_constants_17_2.json", "S17.2-004"):
        "S17.2-004 IEEE round constant/operator fixture: the program imports IEEE_NEAREST, "
        "IEEE_TO_ZERO, IEEE_UP, IEEE_DOWN, IEEE_AWAY, IEEE_OTHER, and comparison operators from "
        "IEEE_ARITHMETIC. It assigns the listed values to IEEE_ROUND_TYPE objects, checks adjacent "
        "distinctness, checks IEEE_OTHER is a defined same-value constant, and uses elemental == and /= "
        "on rank-one round-type arrays. The frozen target provides IEEE_ARITHMETIC but omits IEEE_AWAY.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-001"):
        "S17.3-001 overflow fixture: with the ieee-flag-overflow profile requiring supported default-real "
        "overflow and a nonhalting branch, volatile HUGE(x)*2.0 is evaluated and IEEE_GET_FLAG observes "
        "IEEE_OVERFLOW signaling. The feature mutant replaces the overflowing operation with a safe one.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-002"):
        "S17.3-002 divide-by-zero fixture: with the ieee-flag-divide profile, volatile 1.0/0.0 is "
        "evaluated and IEEE_GET_FLAG observes IEEE_DIVIDE_BY_ZERO signaling. The mutant divides by one.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-003"):
        "S17.3-003 invalid SQRT fixture: with the ieee-flag-invalid-nan profile, SQRT of a volatile "
        "negative real sets IEEE_INVALID and produces an IEEE_IS_NAN result. The mutant takes SQRT(1.0).",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-004"):
        "S17.3-004 underflow/inexact fixture: with the ieee-flag-underflow-inexact profile, volatile "
        "TINY(x)/3.0 and 1.0/3.0 respectively set IEEE_UNDERFLOW and IEEE_INEXACT. Mutants replace "
        "the divisors with one.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-005"):
        "S17.3-005 flag lifecycle fixture: with the ieee-flag-overflow profile, a fresh program observes "
        "the overflow flag initially quiet, checks IEEE_GET_FLAG's logical domain, round-trips "
        "IEEE_SET_FLAG true/false, saves/restores a signaling flag with IEEE_GET_STATUS/IEEE_SET_STATUS, "
        "and observes signaling persistence until an explicit clear.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-006"):
        "S17.3-006 procedure flag fixture: with the ieee-flag-divide profile, a helper procedure performs "
        "volatile 1.0/0.0 and the caller observes IEEE_DIVIDE_BY_ZERO still signaling on return.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-009"):
        "S17.3-009 relational fixture: with the ieee-flag-invalid-nan profile, a quiet NaN built by "
        "IEEE_VALUE is compared by <, <=, >, >=, ==, and /=. Signaling predicates set IEEE_INVALID; "
        "quiet equality and inequality leave it quiet while returning false/true.",
    ("doc/catalogues/ieee_exceptions_17_3.json", "S17.3-012"):
        "S17.3-012 no-extra-operation fixture: with the ieee-flag-divide profile, an unexecuted IF "
        "branch containing 1.0/z and a WHERE assignment masked off for a zero element both leave "
        "IEEE_DIVIDE_BY_ZERO quiet while selected nonzero effects are observed.",
}


LIMIT_PARAGRAPHS = {
    "doc/catalogues/ieee_types_constants_17_2.json":
        "IEEE 17.2 fixture boundaries: this packet uses IEEE_ARITHMETIC only. IEEE_FEATURES_TYPE and "
        "IEEE_FEATURES constants remain pending because 17.1 p1 makes IEEE_FEATURES provision and "
        "contents processor dependent. Exception flag type, array, modes, and status facets are gated by "
        "profiles that require the needed IEEE_SUPPORT_FLAG branches before the case runs.",
    "doc/catalogues/ieee_exceptions_17_3.json":
        "IEEE 17.3 fixture boundaries: each exception/flag fixture declares a profile that compiles the "
        "IEEE_ARITHMETIC inquiry path and exits 77 unless the relevant optional flag/datatype/NaN support "
        "and nonhalting execution branch are available. The fixture itself contains no unsupported-success "
        "branch; unsupported processors are skipped by the profile rather than counted as coverage. Latitude "
        "phrased as processor dependent or may signal remains pending.",
}


PROFILE_SOURCES = {
    "ieee-flag-overflow": r'''
        program ieee_flag_overflow
          use, intrinsic :: ieee_arithmetic
          implicit none
          call require_flag(ieee_overflow)
        contains
          subroutine require_flag(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) stop 77
            if (.not. ieee_support_flag(flag, 0.0)) stop 77
            if (.not. ieee_support_halting(flag)) then
              call ieee_get_halting_mode(flag, halting)
              if (halting) stop 77
            end if
          end subroutine require_flag
        end program ieee_flag_overflow
    ''',
    "ieee-flag-divide": r'''
        program ieee_flag_divide
          use, intrinsic :: ieee_arithmetic
          implicit none
          call require_flag(ieee_divide_by_zero)
        contains
          subroutine require_flag(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) stop 77
            if (.not. ieee_support_flag(flag, 0.0)) stop 77
            if (.not. ieee_support_halting(flag)) then
              call ieee_get_halting_mode(flag, halting)
              if (halting) stop 77
            end if
          end subroutine require_flag
        end program ieee_flag_divide
    ''',
    "ieee-flag-invalid-nan": r'''
        program ieee_flag_invalid_nan
          use, intrinsic :: ieee_arithmetic
          implicit none
          call require_flag(ieee_invalid)
          if (.not. ieee_support_nan(0.0)) stop 77
        contains
          subroutine require_flag(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) stop 77
            if (.not. ieee_support_flag(flag, 0.0)) stop 77
            if (.not. ieee_support_halting(flag)) then
              call ieee_get_halting_mode(flag, halting)
              if (halting) stop 77
            end if
          end subroutine require_flag
        end program ieee_flag_invalid_nan
    ''',
    "ieee-flag-underflow-inexact": r'''
        program ieee_flag_underflow_inexact
          use, intrinsic :: ieee_arithmetic
          implicit none
          call require_flag(ieee_underflow)
          call require_flag(ieee_inexact)
        contains
          subroutine require_flag(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) stop 77
            if (.not. ieee_support_flag(flag, 0.0)) stop 77
            if (.not. ieee_support_halting(flag)) then
              call ieee_get_halting_mode(flag, halting)
              if (halting) stop 77
            end if
          end subroutine require_flag
        end program ieee_flag_underflow_inexact
    ''',
    "ieee-flags-all": r'''
        program ieee_flags_all
          use, intrinsic :: ieee_arithmetic
          implicit none
          call require_flag(ieee_overflow)
          call require_flag(ieee_divide_by_zero)
          call require_flag(ieee_invalid)
          call require_flag(ieee_underflow)
          call require_flag(ieee_inexact)
        contains
          subroutine require_flag(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) stop 77
            if (.not. ieee_support_flag(flag, 0.0)) stop 77
            if (.not. ieee_support_halting(flag)) then
              call ieee_get_halting_mode(flag, halting)
              if (halting) stop 77
            end if
          end subroutine require_flag
        end program ieee_flags_all
    ''',
}


FEATURE_MUTATION_TABLE = [
    ("ieee-flag-type-values-are-named-exception-constants",
     "assert_sets_flag(IEEE_INVALID, IEEE_INVALID) observes the invalid flag signaling",
     "set IEEE_OVERFLOW while still observing IEEE_INVALID"),
    ("ieee-usual-array-has-overflow-divide-invalid",
     "assert_sets_flag(IEEE_USUAL(2), IEEE_DIVIDE_BY_ZERO) observes divide-by-zero signaling",
     "use IEEE_USUAL(1) where the divide-by-zero element is required"),
    ("ieee-all-array-extends-usual-underflow-inexact",
     "assert_sets_flag(IEEE_ALL(4), IEEE_UNDERFLOW) observes underflow signaling",
     "use IEEE_ALL(3) where the underflow element is required"),
    ("ieee-modes-status-types-defined",
     "IEEE_GET_STATUS saves a signaling overflow flag and IEEE_SET_STATUS restores it after clearing",
     "replace IEEE_SET_STATUS(status) with IEEE_GET_STATUS(status), so the cleared flag is not restored"),
    ("ieee-class-type-listed-class-constants",
     "class array contains the listed IEEE_CLASS_TYPE constants and adjacent values differ",
     "duplicate IEEE_POSITIVE_INF in the class array"),
    ("ieee-denormal-class-aliases-equal-subnormal-classes",
     "IEEE_NEGATIVE_DENORMAL equals IEEE_NEGATIVE_SUBNORMAL",
     "compare the negative denormal alias with the positive subnormal constant"),
    ("ieee-class-type-values-comparable",
     "IEEE_POSITIVE_ZERO differs from IEEE_NEGATIVE_ZERO through OPERATOR(/=)",
     "substitute OPERATOR(==) for the distinct zero-class comparison"),
    ("ieee-round-type-listed-rounding-constants",
     "round array contains the listed IEEE_ROUND_TYPE constants and adjacent values differ",
     "duplicate IEEE_DOWN in the round array where IEEE_AWAY is required"),
    ("ieee-other-rounding-constant-defined",
     "IEEE_OTHER compares equal to itself",
     "substitute OPERATOR(/=) for the same-value IEEE_OTHER comparison"),
    ("ieee-types-equality-operator-same-values",
     "elemental == returns true for matching round arrays",
     "change one right-hand array element from IEEE_UP to IEEE_DOWN"),
    ("ieee-types-inequality-operator-different-values",
     "elemental /= returns true for different round arrays",
     "make the right-hand array identical to the left-hand array"),
    ("overflow-signals-for-supported-real-arithmetic",
     "volatile HUGE(x)*2.0 sets IEEE_OVERFLOW",
     "replace the overflowing operation with HUGE(x)/HUGE(x)"),
    ("divide-by-zero-signals-for-supported-real-division",
     "volatile 1.0/0.0 sets IEEE_DIVIDE_BY_ZERO",
     "replace the zero divisor with one"),
    ("invalid-signals-for-negative-real-sqrt",
     "SQRT of a volatile negative real sets IEEE_INVALID and yields a NaN",
     "replace the negative SQRT argument with positive one"),
    ("underflow-signals-for-inexact-tiny-real-result-under-support",
     "volatile TINY(x)/3.0 sets IEEE_UNDERFLOW",
     "replace the divisor with one"),
    ("inexact-signals-for-inexact-real-result-under-support",
     "volatile 1.0/3.0 sets IEEE_INEXACT",
     "replace the divisor with one"),
    ("flags-initially-quiet",
     "a fresh program observes IEEE_OVERFLOW quiet before any local setter",
     "set IEEE_OVERFLOW signaling before the first observation"),
    ("set-flag-and-set-status-change-flag-status",
     "IEEE_SET_STATUS(saved) restores a saved signaling overflow flag",
     "replace SET_STATUS with another GET_STATUS so no restore happens"),
    ("signaling-flag-persists-until-set-quiet",
     "after explicitly setting IEEE_OVERFLOW true, a GET before clearing still observes true",
     "set IEEE_OVERFLOW false instead of true before the persistence observation"),
    ("flag-signaled-inside-procedure-not-quieted-on-return",
     "helper procedure performs volatile 1.0/0.0 and caller observes divide-by-zero signaling",
     "replace the helper's division by zero with division by one"),
    ("real-less-less-equal-greater-greater-equal-quiet-nan-signal-invalid",
     "quiet-NaN less-than comparison sets IEEE_INVALID",
     "replace the quiet-NaN comparison with an ordinary one<one comparison"),
    ("real-equality-inequality-quiet-nan-do-not-signal-invalid",
     "quiet-NaN equality leaves IEEE_INVALID quiet",
     "replace equality with less-than, a signaling predicate"),
    ("relational-operator-predicate-mapping-table",
     "dotted .LE. quiet-NaN comparison maps to a signaling predicate",
     "replace .LE. with quiet equality"),
    ("no-signal-from-unexecuted-if-branch-operation",
     "false IF guard leaves the 1.0/z operation unexecuted and the divide flag quiet",
     "change the guard input so the branch executes"),
    ("no-signal-from-masked-where-operation",
     "WHERE mask excludes the zero element and the divide flag remains quiet",
     "change the mask to include the zero element"),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    return f"{TOPIC}_{variant}"


def completion(variant, supported=True):
    branch = "SUPPORTED" if supported else "UNSUPPORTED"
    return f"IEEE 17.1-17.3 {variant.upper().replace('_', ' ')} {branch} OK\n"


def dedent(source):
    return textwrap.dedent(source).lstrip()


def probe(source, expected, replacement, probe_id, mutation, facet, count=1):
    if source.count(expected) != count:
        raise ValueError(f"{probe_id}: expected occurrence count {count}, got {source.count(expected)}")
    start = source.index(expected)
    return dict(id=probe_id, mutation=mutation, facet=facet, span=[start, start + len(expected)],
                expected=expected, replacement=replacement)


def build_class_constants_core():
    source = dedent(r'''
        program ieee_class_constants_core
          use, intrinsic :: ieee_arithmetic, only: ieee_class_type, &
            ieee_signaling_nan, ieee_quiet_nan, ieee_negative_inf, ieee_negative_normal, &
            ieee_negative_subnormal, ieee_negative_zero, ieee_positive_zero, &
            ieee_positive_subnormal, ieee_positive_normal, ieee_positive_inf, &
            ieee_other_value, ieee_negative_denormal, ieee_positive_denormal, &
            operator(==), operator(/=)
          implicit none
          integer :: checks
          type(ieee_class_type) :: classes(11)
          checks = 0
          classes = [ieee_signaling_nan, ieee_quiet_nan, ieee_negative_inf, &
            ieee_negative_normal, ieee_negative_subnormal, ieee_negative_zero, &
            ieee_positive_zero, ieee_positive_subnormal, ieee_positive_normal, &
            ieee_positive_inf, ieee_other_value]
          call expect_true(all(classes(1:10) /= classes(2:11)), 'class-listed-distinct')
          call expect_true(ieee_negative_denormal == ieee_negative_subnormal, 'negative-denormal-alias')
          call expect_true(ieee_positive_denormal == ieee_positive_subnormal, 'positive-denormal-alias')
          call expect_true(ieee_positive_zero /= ieee_negative_zero, 'class-comparable')
          call expect_count(4)
          write(*,'(a)') 'IEEE 17.1-17.3 CLASS CONSTANTS CORE SUPPORTED OK'
        contains
          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:class-count'
              error stop 1
            end if
          end subroutine expect_count
        end program ieee_class_constants_core
    ''')
    probes = [
        probe(source, "ieee_other_value]", "ieee_positive_inf]", "class-listed-constant",
              "duplicate-class-constant", "ieee-class-type-listed-class-constants"),
        probe(source, "ieee_negative_denormal == ieee_negative_subnormal",
              "ieee_negative_denormal == ieee_positive_subnormal", "negative-denormal-alias",
              "swap-denormal-alias", "ieee-denormal-class-aliases-equal-subnormal-classes"),
        probe(source, "ieee_positive_zero /= ieee_negative_zero", "ieee_positive_zero == ieee_negative_zero",
              "class-comparison-operator", "swap-class-comparison", "ieee-class-type-values-comparable"),
    ]
    return source, probes, [completion("class_constants_core")]


def build_round_constants_core():
    source = dedent(r'''
        program ieee_round_constants_core
          use, intrinsic :: ieee_arithmetic, only: ieee_round_type, ieee_nearest, &
            ieee_to_zero, ieee_up, ieee_down, ieee_away, ieee_other, operator(==), operator(/=)
          implicit none
          integer :: checks
          type(ieee_round_type) :: rounds(6)
          logical :: same_round(2), different_round(2)
          checks = 0
          rounds = [ieee_nearest, ieee_to_zero, ieee_up, ieee_down, ieee_away, ieee_other]
          call expect_true(all(rounds(1:5) /= rounds(2:6)), 'round-listed-distinct')
          call expect_true(ieee_other == ieee_other, 'round-other-defined')
          same_round = [ieee_nearest, ieee_up] == [ieee_nearest, ieee_up]
          different_round = [ieee_nearest, ieee_up] /= [ieee_down, ieee_to_zero]
          call expect_true(all(same_round), 'round-elemental-equality')
          call expect_true(all(different_round), 'round-elemental-inequality')
          call expect_count(4)
          write(*,'(a)') 'IEEE 17.1-17.3 ROUND CONSTANTS CORE SUPPORTED OK'
        contains
          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:round-count'
              error stop 1
            end if
          end subroutine expect_count
        end program ieee_round_constants_core
    ''')
    probes = [
        probe(source, "ieee_away, ieee_other]", "ieee_down, ieee_other]", "round-listed-constant",
              "duplicate-round-constant", "ieee-round-type-listed-rounding-constants"),
        probe(source, "ieee_other == ieee_other", "ieee_other /= ieee_other", "round-other-same",
              "swap-round-other-operator", "ieee-other-rounding-constant-defined"),
        probe(source, "[ieee_nearest, ieee_up] == [ieee_nearest, ieee_up]",
              "[ieee_nearest, ieee_up] == [ieee_nearest, ieee_down]", "round-equality-array",
              "change-equality-right-hand-value", "ieee-types-equality-operator-same-values"),
        probe(source, "[ieee_nearest, ieee_up] /= [ieee_down, ieee_to_zero]",
              "[ieee_nearest, ieee_up] /= [ieee_nearest, ieee_up]", "round-inequality-array",
              "change-inequality-right-hand-values", "ieee-types-inequality-operator-different-values"),
    ]
    return source, probes, [completion("round_constants_core")]


def build_exception_arrays_status():
    source = dedent(r'''
        program ieee_exception_arrays_status
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real :: sample
          type(ieee_modes_type) :: modes
          type(ieee_status_type) :: status
          logical :: observed
          checks = 0
          sample = 0.0
          call accept_modes(modes)
          call ieee_get_status(status)
          call accept_status(status)
          call prepare(ieee_overflow)
          call ieee_set_flag(ieee_overflow, .true.)
          call ieee_get_status(status)
          call ieee_set_flag(ieee_overflow, .false.)
          call ieee_set_status(status)
          call ieee_get_flag(ieee_overflow, observed)
          call expect_true(observed, 'status-restores-overflow')
          call assert_sets_flag(ieee_overflow, ieee_overflow, 'flag-overflow')
          call assert_sets_flag(ieee_divide_by_zero, ieee_divide_by_zero, 'flag-divide')
          call assert_sets_flag(ieee_invalid, ieee_invalid, 'flag-invalid')
          call assert_sets_flag(ieee_underflow, ieee_underflow, 'flag-underflow')
          call assert_sets_flag(ieee_inexact, ieee_inexact, 'flag-inexact')
          call assert_sets_flag(ieee_usual(1), ieee_overflow, 'usual-overflow')
          call assert_sets_flag(ieee_usual(2), ieee_divide_by_zero, 'usual-divide')
          call assert_sets_flag(ieee_usual(3), ieee_invalid, 'usual-invalid')
          call assert_sets_flag(ieee_all(1), ieee_overflow, 'all-overflow')
          call assert_sets_flag(ieee_all(2), ieee_divide_by_zero, 'all-divide')
          call assert_sets_flag(ieee_all(3), ieee_invalid, 'all-invalid')
          call assert_sets_flag(ieee_all(4), ieee_underflow, 'all-underflow')
          call assert_sets_flag(ieee_all(5), ieee_inexact, 'all-inexact')
          call expect_count(16)
          write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION ARRAYS STATUS SUPPORTED OK'
        contains
          subroutine accept_modes(value)
            type(ieee_modes_type), intent(in) :: value
            checks = checks + 1
          end subroutine accept_modes
          subroutine accept_status(value)
            type(ieee_status_type), intent(in) :: value
            checks = checks + 1
          end subroutine accept_status
          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:true', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine assert_sets_flag(setter, expected, label)
            type(ieee_flag_type), intent(in) :: setter, expected
            character(len=*), intent(in) :: label
            logical :: observed
            call prepare(expected)
            call ieee_set_flag(setter, .true.)
            call ieee_get_flag(expected, observed)
            if (.not. observed) then
              write(*,'(a,1x,a)') 'IEEE17:flag-array', label
              error stop 1
            end if
            call ieee_set_flag(expected, .false.)
            checks = checks + 1
          end subroutine assert_sets_flag
          subroutine prepare(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_flag(flag, sample)) error stop 77
            if (ieee_support_halting(flag)) then
              call ieee_set_halting_mode(flag, .false.)
            else
              call ieee_get_halting_mode(flag, halting)
              if (halting) error stop 77
            end if
            call ieee_set_flag(flag, .false.)
          end subroutine prepare
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:array-count'
              error stop 1
            end if
          end subroutine expect_count
        end program ieee_exception_arrays_status
    ''')
    probes = [
        probe(source, "call assert_sets_flag(ieee_invalid, ieee_invalid, 'flag-invalid')",
              "call assert_sets_flag(ieee_overflow, ieee_invalid, 'flag-invalid')", "scalar-flag-invalid",
              "set-different-scalar-flag", "ieee-flag-type-values-are-named-exception-constants"),
        probe(source, "call assert_sets_flag(ieee_usual(2), ieee_divide_by_zero, 'usual-divide')",
              "call assert_sets_flag(ieee_usual(1), ieee_divide_by_zero, 'usual-divide')", "usual-array-divide",
              "swap-usual-array-index", "ieee-usual-array-has-overflow-divide-invalid"),
        probe(source, "call assert_sets_flag(ieee_all(4), ieee_underflow, 'all-underflow')",
              "call assert_sets_flag(ieee_all(3), ieee_underflow, 'all-underflow')", "all-array-underflow",
              "swap-all-array-index", "ieee-all-array-extends-usual-underflow-inexact"),
        probe(source, "call ieee_set_status(status)", "call ieee_get_status(status)", "status-round-trip",
              "omit-status-restore", "ieee-modes-status-types-defined"),
    ]
    return source, probes, [completion("exception_arrays_status")]


def flag_preamble_source():
    return '''
          subroutine prepare(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_flag(flag, 0.0)) error stop 77
            if (ieee_support_halting(flag)) then
              call ieee_set_halting_mode(flag, .false.)
            else
              call ieee_get_halting_mode(flag, halting)
              if (halting) error stop 77
            end if
            call ieee_set_flag(flag, .false.)
          end subroutine prepare
    '''


def expect_helpers_source(count_label):
    return f'''
          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:true', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_false(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_false
          subroutine expect_flag(flag, expected, label)
            type(ieee_flag_type), intent(in) :: flag
            logical, intent(in) :: expected
            character(len=*), intent(in) :: label
            logical :: observed
            call ieee_get_flag(flag, observed)
            if (observed .neqv. expected) then
              write(*,'(a,1x,a)') 'IEEE17:flag', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_flag
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:{count_label}'
              error stop 1
            end if
          end subroutine expect_count
    '''


def build_exception_overflow():
    source = dedent(r'''
        program ieee_exception_overflow
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: huge_value, two, sink
          checks = 0
          huge_value = huge(0.0)
          two = 2.0
          call prepare(ieee_overflow)
          sink = huge_value * two
          call expect_flag(ieee_overflow, .true., 'overflow-multiply')
          if (sink == -12345.0) error stop 1
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION OVERFLOW SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + expect_helpers_source("overflow-count") + dedent(r'''
        end program ieee_exception_overflow
    ''')
    probes = [probe(source, "sink = huge_value * two", "sink = huge_value / huge_value", "overflow-operation",
                    "replace-overflow-with-safe-operation", "overflow-signals-for-supported-real-arithmetic")]
    return source, probes, [completion("exception_overflow")]


def build_exception_divide():
    source = dedent(r'''
        program ieee_exception_divide
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, zero, sink
          checks = 0
          one = 1.0
          zero = 0.0
          call prepare(ieee_divide_by_zero)
          sink = one / zero
          call expect_flag(ieee_divide_by_zero, .true., 'divide-real')
          if (sink == -12345.0) error stop 1
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION DIVIDE SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + expect_helpers_source("divide-count") + dedent(r'''
        end program ieee_exception_divide
    ''')
    probes = [probe(source, "sink = one / zero", "sink = one / one", "divide-operation",
                    "replace-divide-by-zero-with-safe-divide",
                    "divide-by-zero-signals-for-supported-real-division")]
    return source, probes, [completion("exception_divide")]


def build_exception_invalid_sqrt():
    source = dedent(r'''
        program ieee_exception_invalid_sqrt
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: negative, sink
          checks = 0
          negative = -1.0
          call prepare(ieee_invalid)
          sink = sqrt(negative)
          call expect_flag(ieee_invalid, .true., 'invalid-sqrt-flag')
          call expect_true(ieee_is_nan(sink), 'invalid-sqrt-nan')
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION INVALID SQRT SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + expect_helpers_source("invalid-count") + dedent(r'''
        end program ieee_exception_invalid_sqrt
    ''')
    probes = [probe(source, "sink = sqrt(negative)", "sink = sqrt(1.0)", "invalid-sqrt-operation",
                    "replace-negative-sqrt-with-positive-sqrt", "invalid-signals-for-negative-real-sqrt")]
    return source, probes, [completion("exception_invalid_sqrt")]


def build_exception_underflow_inexact():
    source = dedent(r'''
        program ieee_exception_underflow_inexact
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, three, tiny_value, sink
          checks = 0
          one = 1.0
          three = 3.0
          tiny_value = tiny(0.0)
          call prepare(ieee_underflow)
          sink = tiny_value / three
          call expect_flag(ieee_underflow, .true., 'underflow-tiny-inexact')
          call prepare(ieee_inexact)
          sink = one / three
          call expect_flag(ieee_inexact, .true., 'inexact-division')
          if (sink == -12345.0) error stop 1
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION UNDERFLOW INEXACT SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + expect_helpers_source("underflow-inexact-count") + dedent(r'''
        end program ieee_exception_underflow_inexact
    ''')
    probes = [
        probe(source, "sink = tiny_value / three", "sink = tiny_value / one", "underflow-operation",
              "replace-underflow-with-normal-operation",
              "underflow-signals-for-inexact-tiny-real-result-under-support"),
        probe(source, "sink = one / three", "sink = one / one", "inexact-operation",
              "replace-inexact-with-exact-operation", "inexact-signals-for-inexact-real-result-under-support"),
    ]
    return source, probes, [completion("exception_underflow_inexact")]


def build_flag_lifecycle():
    source = dedent(r'''
        program ieee_flag_lifecycle
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: observed
          type(ieee_status_type) :: saved
          checks = 0
          call ieee_get_flag(ieee_overflow, observed)
          call expect_false(observed, 'initial-overflow-quiet')
          call prepare(ieee_overflow)
          call ieee_set_flag(ieee_overflow, .true.)
          call ieee_get_flag(ieee_overflow, observed)
          call expect_true(observed, 'set-flag-true')
          call ieee_get_status(saved)
          call ieee_set_flag(ieee_overflow, .false.)
          call ieee_get_flag(ieee_overflow, observed)
          call expect_false(observed, 'set-flag-false')
          call ieee_set_status(saved)
          call ieee_get_flag(ieee_overflow, observed)
          call expect_true(observed, 'set-status-restores')
          call ieee_set_flag(ieee_overflow, .true.)
          call ieee_get_flag(ieee_overflow, observed)
          call expect_true(observed, 'persists-before-clear')
          call ieee_set_flag(ieee_overflow, .false.)
          call ieee_get_flag(ieee_overflow, observed)
          call expect_false(observed, 'persists-until-clear')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.1-17.3 FLAG LIFECYCLE SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + expect_helpers_source("lifecycle-count") + dedent(r'''
        end program ieee_flag_lifecycle
    ''')
    probes = [
        probe(source, "call ieee_get_flag(ieee_overflow, observed)\n  call expect_false(observed, 'initial-overflow-quiet')",
              "if (ieee_support_halting(ieee_overflow)) call ieee_set_halting_mode(ieee_overflow, .false.)\n"
              "  call ieee_set_flag(ieee_overflow, .true.)\n"
              "  call ieee_get_flag(ieee_overflow, observed)\n"
              "  call expect_false(observed, 'initial-overflow-quiet')", "initial-quiet",
              "set-flag-before-initial-observation", "flags-initially-quiet"),
        probe(source, "call ieee_set_status(saved)", "call ieee_get_status(saved)", "set-status-restore",
              "omit-set-status-restore", "set-flag-and-set-status-change-flag-status"),
        probe(source, "call ieee_set_flag(ieee_overflow, .true.)\n  call ieee_get_flag(ieee_overflow, observed)\n"
              "  call expect_true(observed, 'persists-before-clear')",
              "call ieee_set_flag(ieee_overflow, .false.)\n  call ieee_get_flag(ieee_overflow, observed)\n"
              "  call expect_true(observed, 'persists-before-clear')", "persistence-before-clear",
              "clear-before-persistence-observation", "signaling-flag-persists-until-set-quiet"),
    ]
    return source, probes, [completion("flag_lifecycle")]


def build_procedure_flag_semantics():
    source = dedent(r'''
        program ieee_procedure_flag_semantics
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: observed
          checks = 0
          call prepare(ieee_divide_by_zero)
          call signal_divide_inside()
          call ieee_get_flag(ieee_divide_by_zero, observed)
          call expect_true(observed, 'inside-signal-preserved')
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.1-17.3 PROCEDURE FLAG SEMANTICS SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + dedent(r'''
          subroutine signal_divide_inside()
            real, volatile :: one, zero, sink
            one = 1.0
            zero = 0.0
            sink = one / zero
            if (sink == -12345.0) error stop 1
          end subroutine signal_divide_inside
    ''') + expect_helpers_source("procedure-count") + dedent(r'''
        end program ieee_procedure_flag_semantics
    ''')
    probes = [probe(source, "sink = one / zero", "sink = one / one", "inside-divide-operation",
                    "replace-inside-divide-by-safe-operation",
                    "flag-signaled-inside-procedure-not-quieted-on-return")]
    return source, probes, [completion("procedure_flag_semantics")]


def build_relational_invalid_table():
    source = dedent(r'''
        program ieee_relational_invalid_table
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: relation
          real, volatile :: qnan, one
          checks = 0
          one = 1.0
          qnan = ieee_value(one, ieee_quiet_nan)
          call prepare(ieee_invalid)
          relation = qnan < one
          call expect_relation(relation, .false., ieee_invalid, .true., 'lt-symbolic')
          call prepare(ieee_invalid)
          relation = qnan .le. one
          call expect_relation(relation, .false., ieee_invalid, .true., 'le-dotted')
          call prepare(ieee_invalid)
          relation = qnan > one
          call expect_relation(relation, .false., ieee_invalid, .true., 'gt-symbolic')
          call prepare(ieee_invalid)
          relation = qnan .ge. one
          call expect_relation(relation, .false., ieee_invalid, .true., 'ge-dotted')
          call prepare(ieee_invalid)
          relation = qnan == one
          call expect_relation(relation, .false., ieee_invalid, .false., 'eq-symbolic')
          call prepare(ieee_invalid)
          relation = qnan .ne. one
          call expect_relation(relation, .true., ieee_invalid, .false., 'ne-dotted')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.1-17.3 RELATIONAL INVALID TABLE SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + dedent(r'''
          subroutine expect_relation(value, expected, flag, flag_expected, label)
            logical, intent(in) :: value, expected, flag_expected
            type(ieee_flag_type), intent(in) :: flag
            character(len=*), intent(in) :: label
            if (value .neqv. expected) then
              write(*,'(a,1x,a)') 'IEEE17:relation', label
              error stop 1
            end if
            call expect_flag(flag, flag_expected, label)
          end subroutine expect_relation
    ''') + expect_helpers_source("relational-count") + dedent(r'''
        end program ieee_relational_invalid_table
    ''')
    probes = [
        probe(source, "relation = qnan < one", "relation = one < one", "lt-invalid-mapping",
              "replace-less-quiet-nan-with-ordinary-comparison",
              "real-less-less-equal-greater-greater-equal-quiet-nan-signal-invalid"),
        probe(source, "relation = qnan == one", "relation = qnan < one", "eq-quiet-invalid",
              "replace-quiet-equality-with-signaling-less",
              "real-equality-inequality-quiet-nan-do-not-signal-invalid"),
        probe(source, "relation = qnan .le. one", "relation = qnan == one", "table-dotted-mapping",
              "replace-dotted-less-equal-with-equality", "relational-operator-predicate-mapping-table"),
    ]
    return source, probes, [completion("relational_invalid_table")]


def build_masking_no_extra_operations():
    source = dedent(r'''
        program ieee_masking_no_extra_operations
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, zero, y, z
          real :: a(3)
          checks = 0
          one = 1.0
          zero = 0.0
          call prepare(ieee_divide_by_zero)
          z = 0.0
          y = -9.0
          if (zero_function(z) > 0.0) y = one / z
          call expect_real(y, -9.0, 'if-branch-not-executed')
          call expect_flag(ieee_divide_by_zero, .false., 'if-branch-no-divide-flag')
          call prepare(ieee_divide_by_zero)
          a = [2.0, 0.0, -4.0]
          where (a > 0.0) a = one / a
          call expect_real(a(1), 0.5, 'where-positive-updated')
          call expect_real(a(2), 0.0, 'where-zero-masked')
          call expect_real(a(3), -4.0, 'where-negative-masked')
          call expect_flag(ieee_divide_by_zero, .false., 'where-no-divide-flag')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.1-17.3 MASKING NO EXTRA OPERATIONS SUPPORTED OK'
        contains
    ''') + flag_preamble_source() + dedent(r'''
          real function zero_function(value)
            real, intent(in) :: value
            zero_function = value
          end function zero_function
          subroutine expect_real(value, expected, label)
            real, intent(in) :: value, expected
            character(len=*), intent(in) :: label
            if (value /= expected) then
              write(*,'(a,1x,a)') 'IEEE17:real', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_real
    ''') + expect_helpers_source("masking-count") + dedent(r'''
        end program ieee_masking_no_extra_operations
    ''')
    probes = [
        probe(source, "if (zero_function(z) > 0.0) y = one / z", "if (zero_function(one) > 0.0) y = one / z",
              "if-branch-mask", "execute-formerly-unexecuted-if-branch",
              "no-signal-from-unexecuted-if-branch-operation"),
        probe(source, "where (a > 0.0) a = one / a", "where (a >= 0.0) a = one / a",
              "where-mask", "unmask-zero-where-element", "no-signal-from-masked-where-operation"),
    ]
    return source, probes, [completion("masking_no_extra_operations")]


BUILDERS = {
    "class_constants_core": build_class_constants_core,
    "round_constants_core": build_round_constants_core,
    "exception_arrays_status": build_exception_arrays_status,
    "flag_lifecycle": build_flag_lifecycle,
    "procedure_flag_semantics": build_procedure_flag_semantics,
    "exception_overflow": build_exception_overflow,
    "exception_divide": build_exception_divide,
    "exception_invalid_sqrt": build_exception_invalid_sqrt,
    "exception_underflow_inexact": build_exception_underflow_inexact,
    "relational_invalid_table": build_relational_invalid_table,
    "masking_no_extra_operations": build_masking_no_extra_operations,
}


def source_specs():
    specs = {}
    for case in CASES:
        source, probes, stdout_options = BUILDERS[case["builder"]]()
        probes = [item for item in probes if item["facet"] in set(case["facets"])]
        raw = source.encode("ascii")
        case_id = identifier(case["variant"])
        all_rules = {case["rule"]: list(case["facets"])}
        all_rules.update(copy.deepcopy(case.get("extra_rules", {})))
        specs[case_id] = dict(
            id=case_id, variant=case["variant"], rule=case["rule"], facets=list(case["facets"]),
            extra_rules=all_rules, title=case["title"], source=source, source_sha256=sha(raw),
            probes=copy.deepcopy(probes), stdout_options=stdout_options,
            profiles=list(case.get("profiles", [])),
        )
    return specs


def mutated_source(spec, probe):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent input no longer matches fingerprint")
    start, end = probe["span"]
    if raw[start:end].decode("ascii") != probe["expected"]:
        raise ValueError("mutation span no longer binds complete parent")
    return raw[:start] + probe["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, source in PROFILE_SOURCES.items():
        files[Path(root) / "tests" / "profiles" / (name.replace("-", "_") + ".f90")] = (
            dedent(source).encode("ascii"))
    for spec in specs.values():
        directory = f"tests/fixtures/{TOPIC}_{spec['variant']}"
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0,
                        stdout=spec["stdout_options"] if len(spec["stdout_options"]) > 1 else spec["stdout_options"][0],
                        stderr=""),
        )
        if spec["profiles"]:
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def covered_facets_by_rule(catalogue_path):
    result = {}
    for case in CASES:
        if case["catalogue"] == catalogue_path:
            result.setdefault(case["rule"], set()).update(case["facets"])
        for rule, facets in case.get("extra_rules", {}).items():
            target = rule_to_catalogue(rule)
            if target == catalogue_path:
                result.setdefault(rule, set()).update(facets)
    return result


def rule_to_catalogue(rule):
    if rule.startswith("S17.2"):
        return "doc/catalogues/ieee_types_constants_17_2.json"
    if rule.startswith("S17.3"):
        return "doc/catalogues/ieee_exceptions_17_3.json"
    raise ValueError(rule)


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate IEEE 17 fixture paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue, catalogue_path):
    result = copy.deepcopy(catalogue)
    selected = covered_facets_by_rule(catalogue_path)
    for rule, facets in selected.items():
        rows = [row for row in result["requirements"] if row["id"] == rule]
        if len(rows) != 1:
            raise ValueError(f"selected requirement changed: {rule}")
        row = rows[0]
        if not facets <= set(row["facets"]):
            raise ValueError(f"selected facets for {rule} changed: {sorted(facets - set(row['facets']))}")
        for facet in sorted(facets):
            row.get("pending", {}).pop(facet, None)
        paragraph = ORACLE_PARAGRAPHS.get((catalogue_path, rule))
        if paragraph:
            row["oracle"] = owned_paragraph(row.get("oracle", ""), rule + " ", paragraph)
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), "IEEE 17.",
                                                   LIMIT_PARAGRAPHS[catalogue_path])
    return result


def summary_text(section):
    if section == "17.1":
        detail = ("This packet uses IEEE_ARITHMETIC, whose 17.1 p1 description says it behaves as if it "
                  "contained a USE statement for IEEE_EXCEPTIONS. It covers support and halting inquiry "
                  "callability through IEEE_ARITHMETIC; IEEE_FEATURES provision/contents remain pending.")
    elif section == "17.2":
        detail = ("This packet covers IEEE_ARITHMETIC class/round constants and comparison operators, "
                  "plus IEEE_EXCEPTIONS public flag arrays and modes/status types through the "
                  "IEEE_ARITHMETIC reexport path. IEEE_FEATURES facets remain pending.")
    else:
        detail = ("This packet covers supported-branch flag effects only. Each optional flag operation is "
                  "declared with a profile that exits 77 when the relevant support inquiry is false, so "
                  "unsupported processors skip rather than pass the facet.")
    return (SUMMARY_BEGIN + "\n## Executable IEEE 17.1-17.3 fixtures\n\n" + detail +
            " No fixture contains an unsupported-success oracle; all discharged facets have load-bearing "
            "feature mutations.\n" + SUMMARY_END)


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
    catalogues = {}
    views = {}
    for catalogue_path, (section, view_path) in CATALOGUES.items():
        updated = synced_catalogue(json.loads((root / catalogue_path).read_text()), catalogue_path)
        catalogues[catalogue_path] = updated
        views[view_path] = render_view(updated, section, view_path, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for catalogue_path, catalogue in catalogues.items():
            if json.loads((root / catalogue_path).read_text()) != catalogue:
                stale.append(catalogue_path)
        for view_path, text in views.items():
            if (root / view_path).read_text() != text:
                stale.append(view_path)
        if stale:
            raise ValueError("stale IEEE 17.1-17.3 fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for catalogue_path, catalogue in catalogues.items():
                (root / catalogue_path).write_text(json.dumps(catalogue, indent=2) + "\n")
            for view_path, text in views.items():
                (root / view_path).write_text(text)
    return specs


def compiler_command(compiler, std, source, output):
    command = [str(compiler)]
    if std:
        command.append(std)
    command += [str(source), "-o", str(output)]
    return command


def run_one_source(compiler, std, work_dir, source_text, stdout_options, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compiled = subprocess.run(compiler_command(compiler, std, source, exe), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cwd=work_dir)
    if compiled.returncode != 0:
        return dict(status="compile-fail", stdout=compiled.stdout, stderr=compiled.stderr,
                    returncode=compiled.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         timeout=60, cwd=work_dir)
    passed = run.returncode == 0 and run.stdout in stdout_options and run.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr,
                returncode=run.returncode)


def mutation_check(root, compiler, std, keep_work=False):
    root = Path(root)
    specs = source_specs()
    work_dir = root / f".{TOPIC}_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    try:
        report = []
        for spec in specs.values():
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["stdout_options"],
                                    spec["variant"] + "_parent")
            parent_ok = parent["status"] == "pass"
            accepted_stdout = [parent["stdout"]] if parent_ok else spec["stdout_options"]
            for index, item in enumerate(spec["probes"]):
                mutant = mutated_source(spec, item).decode("ascii")
                observed = run_one_source(compiler, std, work_dir, mutant, accepted_stdout,
                                          f"{spec['variant']}_mut_{index:03d}")
                failed = observed["status"] != "pass"
                report.append(dict(variant=spec["variant"], probe=item["id"], mutation=item["mutation"],
                                   facet=item["facet"], parent_ok=parent_ok, failed=failed,
                                   status=observed["status"], stdout=observed["stdout"],
                                   stderr=observed["stderr"], returncode=observed["returncode"],
                                   parent_status=parent["status"], parent_stderr=parent["stderr"]))
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:5], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)


def counts(specs):
    facets = set()
    for spec in specs.values():
        for items in spec["extra_rules"].values():
            facets.update(items)
    return len(specs), len(facets), sum(len(spec["probes"]) for spec in specs.values())


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
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        print(f"Mutation-checked {len(report)} IEEE 17.1-17.3 mutations; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} IEEE 17.1-17.3 cases, "
          f"{facet_count} facets and {mutation_count} mutations.")


if __name__ == "__main__":
    main()
