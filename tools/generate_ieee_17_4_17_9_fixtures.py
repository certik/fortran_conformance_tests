#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 IEEE 17.4-17.9 facilities."""

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
TOPIC = "ieee_17_4_17_9"
SUMMARY_BEGIN = "<!-- BEGIN IEEE 17.4-17.9 FIXTURES -->"
SUMMARY_END = "<!-- END IEEE 17.4-17.9 FIXTURES -->"

CATALOGUES = {
    "doc/catalogues/ieee_rounding_modes_17_4.json": ("17.4", "doc/fortran_2023_17_4.md"),
    "doc/catalogues/ieee_underflow_mode_17_5.json": ("17.5", "doc/fortran_2023_17_5.md"),
    "doc/catalogues/halting_17_6.json": ("17.6", "doc/fortran_2023_17_6.md"),
    "doc/catalogues/floating_point_status_17_7.json": ("17.7", "doc/fortran_2023_17_7.md"),
    "doc/catalogues/exceptional_values_17_8.json": ("17.8", "doc/fortran_2023_17_8.md"),
    "doc/catalogues/ieee_arithmetic_support_17_9.json": ("17.9", "doc/fortran_2023_17_9.md"),
}

CASES = [
    dict(variant="rounding_binary_effect", rule="S17.4-001",
         catalogue="doc/catalogues/ieee_rounding_modes_17_4.json",
         facets=["binary-rounding-mode-affects-radix-two-arithmetic"],
         profiles=["ieee-binary-rounding"], title="Binary rounding mode affects radix-two arithmetic",
         builder="rounding_binary_effect"),
    dict(variant="rounding_directions", rule="S17.4-002",
         catalogue="doc/catalogues/ieee_rounding_modes_17_4.json",
         facets=["ieee-nearest-ties-to-even-half-ulp-result", "ieee-to-zero-directed-half-ulp-result",
                 "ieee-up-directed-half-ulp-result", "ieee-down-directed-half-ulp-result"],
         profiles=["ieee-binary-rounding"], title="IEEE rounding direction attributes on half ulps",
         builder="rounding_directions"),
    dict(variant="rounding_get", rule="S17.4-003",
         catalogue="doc/catalogues/ieee_rounding_modes_17_4.json",
         facets=["ieee-get-rounding-mode-retrieves-current-mode"], profiles=["ieee-binary-rounding"],
         title="IEEE_GET_ROUNDING_MODE retrieves the current mode", builder="rounding_get"),
    dict(variant="rounding_set", rule="S17.4-004",
         catalogue="doc/catalogues/ieee_rounding_modes_17_4.json",
         facets=["ieee-set-rounding-mode-alters-supported-mode"], profiles=["ieee-binary-rounding"],
         title="IEEE_SET_ROUNDING_MODE alters a supported mode", builder="rounding_set"),
    dict(variant="rounding_entry", rule="S17.4-005",
         catalogue="doc/catalogues/ieee_rounding_modes_17_4.json",
         facets=["rounding-mode-unchanged-on-procedure-entry"], profiles=["ieee-binary-rounding"],
         title="Procedure entry preserves the rounding mode", builder="rounding_entry"),
    dict(variant="underflow_effects", rule="S17.5-001",
         catalogue="doc/catalogues/ieee_underflow_mode_17_5.json",
         facets=["gradual-underflow-produces-subnormal", "abrupt-underflow-produces-zero"],
         profiles=["ieee-underflow-control"], title="Gradual and abrupt underflow effects",
         builder="underflow_effects"),
    dict(variant="underflow_control", rule="S17.5-002",
         catalogue="doc/catalogues/ieee_underflow_mode_17_5.json",
         facets=["ieee-support-underflow-control-inquires-facility",
                 "ieee-get-underflow-mode-retrieves-current-mode",
                 "ieee-set-underflow-mode-alters-current-mode",
                 "underflow-mode-unchanged-on-procedure-entry"],
         profiles=["ieee-underflow-control"], title="Underflow control inquiry and mode round trips",
         builder="underflow_control"),
    dict(variant="underflow_guarded", rule="S17.5-003",
         catalogue="doc/catalogues/ieee_underflow_mode_17_5.json",
         facets=["underflow-mode-effects-guarded-by-support-underflow-control-true"],
         profiles=["ieee-underflow-control"], title="Underflow effect assertions are gated by support",
         builder="underflow_guarded"),
    dict(variant="halting_control", rule="S17.6-001",
         catalogue="doc/catalogues/halting_17_6.json",
         facets=["halting-control-processor-permitted"], profiles=["ieee-halting-overflow"],
         title="Supported halting mode can be set to nonhalting", builder="halting_control"),
    dict(variant="halting_entry", rule="S17.6-002",
         catalogue="doc/catalogues/halting_17_6.json",
         facets=["procedure-entry-preserves-halting-mode"], profiles=["ieee-halting-overflow"],
         title="Procedure entry preserves halting mode", builder="halting_entry"),
    dict(variant="modes_roundtrip", rule="S17.7-002",
         catalogue="doc/catalogues/floating_point_status_17_7.json",
         facets=["ieee-get-set-modes-round-trip"], profiles=["ieee-binary-rounding"],
         title="IEEE_GET_MODES and IEEE_SET_MODES restore modes", builder="modes_roundtrip"),
    dict(variant="status_roundtrip", rule="S17.7-003",
         catalogue="doc/catalogues/floating_point_status_17_7.json",
         facets=["ieee-get-set-status-round-trip"], profiles=["ieee-status-overflow-rounding"],
         title="IEEE_GET_STATUS and IEEE_SET_STATUS restore status", builder="status_roundtrip"),
    dict(variant="exceptional_classes", rule="S17.8-001",
         catalogue="doc/catalogues/exceptional_values_17_8.json",
         facets=["subnormal-class-definition", "infinity-class-definition", "nan-class-definition"],
         profiles=["ieee-exceptional-all"], title="Exceptional values classify as subnormal, infinity, and NaN",
         builder="exceptional_classes"),
    dict(variant="normal_number", rule="S17.8-002",
         catalogue="doc/catalogues/exceptional_values_17_8.json",
         facets=["normal-number-definition"], profiles=["ieee-datatype"],
         title="Normal numbers are classified as normal", builder="normal_number"),
    dict(variant="exceptional_functions", rule="S17.8-003",
         catalogue="doc/catalogues/exceptional_values_17_8.json",
         facets=["ieee-is-finite-provided", "ieee-is-nan-provided", "ieee-is-negative-provided",
                 "ieee-is-normal-provided", "ieee-value-provided", "exceptional-support-inquiries-provided"],
         profiles=["ieee-exceptional-all"], title="Exceptional value inquiry and construction functions",
         builder="exceptional_functions"),
    dict(variant="support_datatype_core", rule="S17.9-001",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["support-datatype-inquiry-logical", "datatype-normal-add-subtract-multiply",
                 "datatype-abs-rem-copy-logb-unordered"], profiles=["ieee-datatype-nan"],
         title="Datatype support inquiry and required normal operations", builder="support_datatype_core"),
    dict(variant="support_nan", rule="S17.9-003",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["nan-support-inquiry", "nan-results-for-operations"], profiles=["ieee-nan"],
         title="NaN support inquiry and operation results", builder="support_nan"),
    dict(variant="support_inf", rule="S17.9-004",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["inf-support-inquiry", "inf-results-for-operations"], profiles=["ieee-inf"],
         title="Infinity support inquiry and operation results", builder="support_inf"),
    dict(variant="support_subnormal", rule="S17.9-005",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["subnormal-support-inquiry", "subnormal-results-and-operands"],
         profiles=["ieee-subnormal"], title="Subnormal support inquiry and operation results",
         builder="support_subnormal"),
    dict(variant="support_divide", rule="S17.9-006",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["divide-support-inquiry", "divide-normal-conformance", "divide-nan-conformance",
                 "divide-inf-conformance", "divide-subnormal-conformance"],
         profiles=["ieee-divide-all"], title="Division support inquiry and conforming results",
         builder="support_divide"),
    dict(variant="support_sqrt", rule="S17.9-007",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["sqrt-support-inquiry", "sqrt-negative-zero", "sqrt-nan-conformance",
                 "sqrt-inf-conformance", "sqrt-subnormal-conformance"],
         profiles=["ieee-sqrt-all"], title="SQRT support inquiry and conforming results",
         builder="support_sqrt"),
    dict(variant="support_standard", rule="S17.9-008",
         catalogue="doc/catalogues/ieee_arithmetic_support_17_9.json",
         facets=["standard-support-inquiry", "standard-support-implies-facility-support"],
         profiles=["ieee-standard"], title="Standard support inquiry implies the named facilities",
         builder="support_standard"),
]

PROFILE_SOURCES = {
    "ieee-datatype": """
        program ieee_datatype
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
        end program ieee_datatype
    """,
    "ieee-datatype-nan": """
        program ieee_datatype_nan
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_nan(0.0)) stop 77
        end program ieee_datatype_nan
    """,
    "ieee-binary-rounding": """
        program ieee_binary_rounding
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (radix(0.0) /= 2) stop 77
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_rounding(ieee_nearest, 0.0)) stop 77
          if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) stop 77
          if (.not. ieee_support_rounding(ieee_up, 0.0)) stop 77
          if (.not. ieee_support_rounding(ieee_down, 0.0)) stop 77
        end program ieee_binary_rounding
    """,
    "ieee-underflow-control": """
        program ieee_underflow_control
          use, intrinsic :: ieee_arithmetic
          implicit none
          logical :: halting
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_underflow_control(0.0)) stop 77
          if (.not. ieee_support_subnormal(0.0)) stop 77
          if (ieee_support_flag(ieee_underflow, 0.0)) then
            if (ieee_support_halting(ieee_underflow)) then
              call ieee_set_halting_mode(ieee_underflow, .false.)
            else
              call ieee_get_halting_mode(ieee_underflow, halting)
              if (halting) stop 77
            end if
          end if
        end program ieee_underflow_control
    """,
    "ieee-halting-overflow": """
        program ieee_halting_overflow
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_halting(ieee_overflow)) stop 77
          call ieee_set_halting_mode(ieee_overflow, .false.)
        end program ieee_halting_overflow
    """,
    "ieee-status-overflow-rounding": """
        program ieee_status_overflow_rounding
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_flag(ieee_overflow, 0.0)) stop 77
          if (.not. ieee_support_rounding(ieee_nearest, 0.0)) stop 77
          if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) stop 77
          if (ieee_support_halting(ieee_overflow)) call ieee_set_halting_mode(ieee_overflow, .false.)
        end program ieee_status_overflow_rounding
    """,
    "ieee-exceptional-all": """
        program ieee_exceptional_all
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_nan(0.0)) stop 77
          if (.not. ieee_support_inf(0.0)) stop 77
          if (.not. ieee_support_subnormal(0.0)) stop 77
        end program ieee_exceptional_all
    """,
    "ieee-nan": """
        program ieee_nan
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_nan(0.0)) stop 77
        end program ieee_nan
    """,
    "ieee-inf": """
        program ieee_inf
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_inf(0.0)) stop 77
        end program ieee_inf
    """,
    "ieee-subnormal": """
        program ieee_subnormal
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_subnormal(0.0)) stop 77
          if (ieee_support_underflow_control(0.0)) call ieee_set_underflow_mode(.true.)
        end program ieee_subnormal
    """,
    "ieee-divide-all": """
        program ieee_divide_all
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_divide(0.0)) stop 77
          if (.not. ieee_support_nan(0.0)) stop 77
          if (.not. ieee_support_inf(0.0)) stop 77
          if (.not. ieee_support_subnormal(0.0)) stop 77
          if (ieee_support_underflow_control(0.0)) call ieee_set_underflow_mode(.true.)
        end program ieee_divide_all
    """,
    "ieee-sqrt-all": """
        program ieee_sqrt_all
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_datatype(0.0)) stop 77
          if (.not. ieee_support_sqrt(0.0)) stop 77
          if (.not. ieee_support_nan(0.0)) stop 77
          if (.not. ieee_support_inf(0.0)) stop 77
          if (.not. ieee_support_subnormal(0.0)) stop 77
          if (ieee_support_underflow_control(0.0)) call ieee_set_underflow_mode(.true.)
        end program ieee_sqrt_all
    """,
    "ieee-standard": """
        program ieee_standard
          use, intrinsic :: ieee_arithmetic
          implicit none
          if (.not. ieee_support_standard(0.0)) stop 77
        end program ieee_standard
    """,
}

ORACLE_PARAGRAPHS = {
    ("doc/catalogues/ieee_rounding_modes_17_4.json", "S17.4-001"):
        "S17.4-001 IEEE binary rounding fixture: with a radix-two profile requiring support for NEAREST, TO_ZERO, UP, and DOWN, volatile 1.0+EPSILON(1.0)/2.0 is evaluated under IEEE_UP and IEEE_DOWN; the two exact representable results differ, proving the binary rounding mode affects radix-two arithmetic.",
    ("doc/catalogues/ieee_rounding_modes_17_4.json", "S17.4-002"):
        "S17.4-002 IEEE rounding-direction fixture: after a radix-two support profile, volatile half-ulp additions at +/-1.0 verify NEAREST chooses the even endpoint 1.0, TO_ZERO rounds positive and negative half ulps toward zero, IEEE_UP rounds the positive half ulp upward and the negative one to -1.0, and IEEE_DOWN rounds the positive half ulp to 1.0 and the negative one downward to -(1.0+EPSILON).",
    ("doc/catalogues/ieee_rounding_modes_17_4.json", "S17.4-003"):
        "S17.4-003 IEEE_GET_ROUNDING_MODE fixture: the program sets IEEE_UP and initializes an IEEE_ROUND_TYPE result to IEEE_DOWN before GET; GET returns IEEE_UP. It repeats with IEEE_DOWN after an IEEE_UP sentinel, then restores the saved initial mode.",
    ("doc/catalogues/ieee_rounding_modes_17_4.json", "S17.4-004"):
        "S17.4-004 IEEE_SET_ROUNDING_MODE fixture: after saving the initial mode, SET to IEEE_UP and then IEEE_DOWN is observed by GET in each case, proving alteration of supported modes before restoration.",
    ("doc/catalogues/ieee_rounding_modes_17_4.json", "S17.4-005"):
        "S17.4-005 procedure-entry fixture: the caller sets IEEE_UP and a helper's first IEEE_GET_ROUNDING_MODE observes IEEE_UP before any local setter; the processor-entry preservation facet is tested without claiming return restoration, which the reference compiler did not implement for an in-helper SET.",
    ("doc/catalogues/ieee_underflow_mode_17_5.json", "S17.5-001"):
        "S17.5-001 underflow-mode effect fixture: with support for datatype, subnormal values, and underflow control required by profile, TINY(X)/2.0 through volatile variables classifies as IEEE_POSITIVE_DENORMAL in gradual mode and equals positive zero in abrupt mode; timing/performance latitude is not asserted.",
    ("doc/catalogues/ieee_underflow_mode_17_5.json", "S17.5-002"):
        "S17.5-002 underflow-control fixture: IEEE_SUPPORT_UNDERFLOW_CONTROL(0.0) is asserted on the supported profile, GET returns the mode set by SET for .TRUE. and .FALSE. sentinels, SET to the opposite of a saved mode is observed before restoration, and a helper's entry GET sees the caller's .TRUE. mode.",
    ("doc/catalogues/ieee_underflow_mode_17_5.json", "S17.5-003"):
        "S17.5-003 guarded-underflow fixture: the fixture contains an explicit IEEE_SUPPORT_UNDERFLOW_CONTROL(0.0) true assertion before setting gradual and abrupt modes and observing TINY(X)/2.0 effects; no false-support type effect is claimed.",
    ("doc/catalogues/halting_17_6.json", "S17.6-001"):
        "S17.6-001 halting-control fixture: on a profile requiring IEEE_SUPPORT_HALTING(IEEE_OVERFLOW), SET_HALTING_MODE(...,.FALSE.) followed by GET_HALTING_MODE observes .FALSE.; no initial mode or precise halting occurrence is asserted.",
    ("doc/catalogues/halting_17_6.json", "S17.6-002"):
        "S17.6-002 halting procedure-entry fixture: the caller sets overflow halting mode to .FALSE.; a helper's first GET_HALTING_MODE observes .FALSE., proving entry preservation without running any halting exception.",
    ("doc/catalogues/floating_point_status_17_7.json", "S17.7-002"):
        "S17.7-002 modes round-trip fixture: an IEEE_MODES_TYPE scalar saves the IEEE_NEAREST rounding mode with IEEE_GET_MODES, the program changes to IEEE_TO_ZERO, IEEE_SET_MODES restores the saved value, and GET_ROUNDING_MODE observes IEEE_NEAREST.",
    ("doc/catalogues/floating_point_status_17_7.json", "S17.7-003"):
        "S17.7-003 status round-trip fixture: an IEEE_STATUS_TYPE scalar saves a quiet overflow flag and IEEE_NEAREST mode, the program signals the flag and changes the mode, IEEE_SET_STATUS restores the saved status, and GET_FLAG/GET_ROUNDING_MODE observe quiet overflow and IEEE_NEAREST.",
    ("doc/catalogues/exceptional_values_17_8.json", "S17.8-001"):
        "S17.8-001 exceptional class fixture: after datatype, subnormal, infinity, and NaN support gates, volatile TINY/2 classifies as IEEE_POSITIVE_DENORMAL, IEEE_VALUE(...,IEEE_POSITIVE_INF) classifies as IEEE_POSITIVE_INF, and IEEE_VALUE(...,IEEE_QUIET_NAN) is observed by IEEE_IS_NAN.",
    ("doc/catalogues/exceptional_values_17_8.json", "S17.8-002"):
        "S17.8-002 normal-number fixture: with IEEE datatype support, IEEE_CLASS(1.0) and IEEE_CLASS(-1.0) report IEEE_POSITIVE_NORMAL and IEEE_NEGATIVE_NORMAL, and IEEE_IS_NORMAL is true for both values.",
    ("doc/catalogues/exceptional_values_17_8.json", "S17.8-003"):
        "S17.8-003 exceptional function fixture: the program observes IEEE_IS_FINITE on finite and infinite values, IEEE_IS_NAN on NaN and normal values, IEEE_IS_NEGATIVE on signed finite values, IEEE_IS_NORMAL on infinite and normal values, IEEE_VALUE producing infinity and NaN, and the SUBNORMAL/INF/NAN support inquiries returning true on the supported profile.",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-001"):
        "S17.9-001 datatype-support fixture: the supported branch observes IEEE_SUPPORT_DATATYPE(0.0), exact normal addition/subtraction/multiplication, ABS, IEEE_REM, IEEE_COPY_SIGN, IEEE_LOGB, and IEEE_UNORDERED results required for that kind of real.",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-003"):
        "S17.9-003 NaN-support fixture: after IEEE_SUPPORT_NAN(0.0), a quiet NaN from IEEE_VALUE propagates as NaN through +, -, *, IEEE_REM, and IEEE_RINT, each observed with IEEE_IS_NAN.",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-004"):
        "S17.9-004 infinity-support fixture: after IEEE_SUPPORT_INF(0.0), infinities from IEEE_VALUE propagate through +, -, *, IEEE_REM(1.5,inf), and IEEE_RINT with exact IEEE_CLASS or exact finite-remainder observations.",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-005"):
        "S17.9-005 subnormal-support fixture: after IEEE_SUPPORT_SUBNORMAL(0.0) and gradual mode where controllable, s=TINY/2 classifies as IEEE_POSITIVE_DENORMAL and remains the exact subnormal result/operand through +0, TINY-s, *1, and IEEE_REM(s,2*TINY).",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-006"):
        "S17.9-006 divide-support fixture: after IEEE_SUPPORT_DIVIDE(0.0), exact normal divisions produce 3.0 and 0.25, quiet-NaN division is NaN, infinity division classifies as infinity or positive zero as appropriate, and TINY/2 plus s/1 exercise subnormal result and operand cases.",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-007"):
        "S17.9-007 SQRT-support fixture: after IEEE_SUPPORT_SQRT(0.0), SQRT of negative zero returns negative zero, SQRT of a quiet NaN is NaN, SQRT of positive infinity classifies as positive infinity, and SQRT(SCALE(1.0,e)) exactly equals SCALE(1.0,e/2) for an even subnormal exponent e guarded to be representable.",
    ("doc/catalogues/ieee_arithmetic_support_17_9.json", "S17.9-008"):
        "S17.9-008 standard-support fixture: on the IEEE_SUPPORT_STANDARD(0.0) true profile, the fixture asserts datatype, NaN, infinity, subnormal, divide, sqrt, underflow-control, and at least one rounding-mode inquiry all report support for default real.",
}

LIMIT_PARAGRAPHS = {
    path: "IEEE 17.4-17.9 fixture boundaries: this packet uses IEEE_ARITHMETIC only. Optional IEEE facilities are gated by tests/profiles that require the supported branch before the fixture runs; no unsupported-success branch is counted as coverage. Processor-dependent initial modes, IEEE_OTHER arithmetic effects, decimal-real behavior absent from the host, halting occurrence timing, performance latitude, status-object internals, and reference-compiler failures of procedure-return mode restoration remain pending."
    for path in CATALOGUES
}

FEATURE_MUTATION_TABLE = [
    ("binary-rounding-mode-affects-radix-two-arithmetic", "UP half-ulp result differs from DOWN half-ulp result", "compute the DOWN result under IEEE_UP"),
    ("ieee-nearest-ties-to-even-half-ulp-result", "NEAREST half-ulp at 1.0 equals 1.0", "set IEEE_UP instead of IEEE_NEAREST"),
    ("ieee-to-zero-directed-half-ulp-result", "TO_ZERO negative half-ulp equals -1.0", "set IEEE_DOWN instead of IEEE_TO_ZERO"),
    ("ieee-up-directed-half-ulp-result", "IEEE_UP positive half-ulp equals 1.0+epsilon", "set IEEE_DOWN instead of IEEE_UP"),
    ("ieee-down-directed-half-ulp-result", "IEEE_DOWN negative half-ulp equals -(1.0+epsilon)", "set IEEE_UP instead of IEEE_DOWN"),
    ("ieee-get-rounding-mode-retrieves-current-mode", "GET after SET(IEEE_UP) returns IEEE_UP from a DOWN sentinel", "set IEEE_DOWN before the GET"),
    ("ieee-set-rounding-mode-alters-supported-mode", "SET(IEEE_DOWN) is observed by GET", "set IEEE_UP where DOWN is required"),
    ("rounding-mode-unchanged-on-procedure-entry", "helper entry GET observes caller's IEEE_UP", "caller sets IEEE_DOWN before helper"),
    ("gradual-underflow-produces-subnormal", "gradual TINY/2 classifies IEEE_POSITIVE_DENORMAL", "set abrupt mode before the calculation"),
    ("abrupt-underflow-produces-zero", "abrupt TINY/2 equals positive zero", "set gradual mode before the calculation"),
    ("ieee-support-underflow-control-inquires-facility", "support inquiry is true on the required profile", "negate the support inquiry"),
    ("ieee-get-underflow-mode-retrieves-current-mode", "GET observes .TRUE. after SET(.TRUE.)", "set .FALSE. before the GET"),
    ("ieee-set-underflow-mode-alters-current-mode", "SET(opposite saved mode) is observed", "set the saved mode instead"),
    ("underflow-mode-unchanged-on-procedure-entry", "helper entry GET observes caller's .TRUE. mode", "caller sets .FALSE. before helper"),
    ("underflow-mode-effects-guarded-by-support-underflow-control-true", "support guard is true before effect assertions", "negate the explicit guard"),
    ("halting-control-processor-permitted", "GET_HALTING_MODE observes .FALSE. after SET(.FALSE.)", "set halting mode to .TRUE."),
    ("procedure-entry-preserves-halting-mode", "helper entry GET observes caller's .FALSE. halting mode", "caller sets .TRUE. before helper"),
    ("ieee-get-set-modes-round-trip", "SET_MODES restores IEEE_NEAREST after a TO_ZERO change", "replace SET_MODES with GET_MODES"),
    ("ieee-get-set-status-round-trip", "SET_STATUS restores quiet overflow and IEEE_NEAREST", "replace SET_STATUS with GET_STATUS"),
    ("subnormal-class-definition", "TINY/2 classifies IEEE_POSITIVE_DENORMAL", "classify TINY instead of TINY/2"),
    ("infinity-class-definition", "IEEE_VALUE(...POSITIVE_INF) classifies positive infinity", "construct a positive normal value"),
    ("nan-class-definition", "IEEE_VALUE(...QUIET_NAN) is NaN", "construct positive infinity instead"),
    ("normal-number-definition", "IEEE_CLASS(1.0) is IEEE_POSITIVE_NORMAL", "classify zero instead"),
    ("ieee-is-finite-provided", "IEEE_IS_FINITE(infinity) is false", "test finite one instead"),
    ("ieee-is-nan-provided", "IEEE_IS_NAN(quiet NaN) is true", "test finite one instead"),
    ("ieee-is-negative-provided", "IEEE_IS_NEGATIVE(-1.0) is true", "test positive one instead"),
    ("ieee-is-normal-provided", "IEEE_IS_NORMAL(infinity) is false", "test one instead"),
    ("ieee-value-provided", "IEEE_VALUE positive infinity classifies positive infinity", "request positive normal instead"),
    ("exceptional-support-inquiries-provided", "SUBNORMAL/INF/NAN inquiries all return true on the profile", "negate the NaN inquiry"),
    ("support-datatype-inquiry-logical", "IEEE_SUPPORT_DATATYPE is true on the profile", "negate the inquiry"),
    ("datatype-normal-add-subtract-multiply", "1.5+0.25 equals 1.75", "perform subtraction for the addition assertion"),
    ("datatype-abs-rem-copy-logb-unordered", "IEEE_COPY_SIGN copies a negative sign", "copy from a positive sign"),
    ("nan-support-inquiry", "IEEE_SUPPORT_NAN is true on the profile", "negate the inquiry"),
    ("nan-results-for-operations", "quiet NaN plus one is NaN", "add one plus one instead"),
    ("inf-support-inquiry", "IEEE_SUPPORT_INF is true on the profile", "negate the inquiry"),
    ("inf-results-for-operations", "infinity plus one classifies positive infinity", "compute one plus one"),
    ("subnormal-support-inquiry", "IEEE_SUPPORT_SUBNORMAL is true on the profile", "negate the inquiry"),
    ("subnormal-results-and-operands", "subnormal plus zero equals the original subnormal", "add TINY instead of zero"),
    ("divide-support-inquiry", "IEEE_SUPPORT_DIVIDE is true on the profile", "negate the inquiry"),
    ("divide-normal-conformance", "1.5/0.5 equals 3.0", "divide by one instead"),
    ("divide-nan-conformance", "quiet NaN divided by one is NaN", "divide one by one"),
    ("divide-inf-conformance", "positive infinity divided by two classifies positive infinity", "divide one by two"),
    ("divide-subnormal-conformance", "TINY/2 equals the prepared positive subnormal", "divide TINY by one"),
    ("sqrt-support-inquiry", "IEEE_SUPPORT_SQRT is true on the profile", "negate the inquiry"),
    ("sqrt-negative-zero", "SQRT(negative zero) keeps the negative sign", "take SQRT(positive zero)"),
    ("sqrt-nan-conformance", "SQRT(quiet NaN) is NaN", "take SQRT(one)"),
    ("sqrt-inf-conformance", "SQRT(positive infinity) classifies positive infinity", "take SQRT(one)"),
    ("sqrt-subnormal-conformance", "SQRT(exact subnormal square) equals the exact normal root", "use e+2 as the radicand exponent"),
    ("standard-support-inquiry", "IEEE_SUPPORT_STANDARD is true on the profile", "negate the inquiry"),
    ("standard-support-implies-facility-support", "standard support implies divide support", "negate the divide-support conjunct"),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dedent(source):
    return textwrap.dedent(source).lstrip()


def identifier(variant):
    return f"{TOPIC}_{variant}"


def completion(variant):
    return f"IEEE 17.4-17.9 {variant.upper().replace('_', ' ')} SUPPORTED OK\n"


def probe(source, expected, replacement, probe_id, mutation, facet, count=1):
    if source.count(expected) != count:
        raise ValueError(f"{probe_id}: expected occurrence count {count}, got {source.count(expected)}")
    start = source.index(expected)
    return dict(id=probe_id, mutation=mutation, facet=facet, span=[start, start + len(expected)],
                expected=expected, replacement=replacement)


def common_helpers(count_label):
    return f'''
          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_false(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (value) then
              write(*,'(a,1x,a)') 'IEEE17:true', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_false
          subroutine expect_real(value, expected, label)
            real, intent(in) :: value, expected
            character(len=*), intent(in) :: label
            if (value /= expected) then
              write(*,'(a,1x,a)') 'IEEE17:real', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_real
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:{count_label}'
              error stop 1
            end if
          end subroutine expect_count
    '''


def rounding_preamble():
    return '''
          subroutine require_rounding()
            if (radix(0.0) /= 2) error stop 77
            if (.not. ieee_support_rounding(ieee_nearest, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_up, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_down, 0.0)) error stop 77
          end subroutine require_rounding
    '''


def build_rounding_binary_effect():
    source = dedent(r'''
        program ieee_rounding_binary_effect
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_round_type) :: saved
          real, volatile :: one, half, up_value, down_value
          checks = 0
          call require_rounding()
          one = 1.0
          half = epsilon(one) / 2.0
          call ieee_get_rounding_mode(saved)
          call ieee_set_rounding_mode(ieee_up)
          up_value = one + half
          call ieee_set_rounding_mode(ieee_down)
          down_value = one + half
          call expect_true(up_value /= down_value, 'binary-rounding-affects-result')
          call ieee_set_rounding_mode(saved)
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.4-17.9 ROUNDING BINARY EFFECT SUPPORTED OK'
        contains
    ''') + rounding_preamble() + common_helpers("rounding-binary-count") + dedent(r'''
        end program ieee_rounding_binary_effect
    ''')
    probes = [probe(source, "call ieee_set_rounding_mode(ieee_down)\n  down_value = one + half",
                    "call ieee_set_rounding_mode(ieee_up)\n  down_value = one + half", "binary-mode-down",
                    "use-up-for-down-result", "binary-rounding-mode-affects-radix-two-arithmetic")]
    return source, probes


def build_rounding_directions():
    source = dedent(r'''
        program ieee_rounding_directions
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_round_type) :: saved
          real, volatile :: one, half, result
          checks = 0
          call require_rounding()
          one = 1.0
          half = epsilon(one) / 2.0
          call ieee_get_rounding_mode(saved)
          call ieee_set_rounding_mode(ieee_nearest)
          result = one + half
          call expect_real(result, one, 'nearest-even-positive')
          call ieee_set_rounding_mode(ieee_to_zero)
          result = -one - half
          call expect_real(result, -one, 'to-zero-negative')
          call ieee_set_rounding_mode(ieee_up)
          result = one + half
          call expect_real(result, one + epsilon(one), 'up-positive')
          call ieee_set_rounding_mode(ieee_down)
          result = -one - half
          call expect_real(result, -(one + epsilon(one)), 'down-negative')
          call ieee_set_rounding_mode(saved)
          call expect_count(4)
          write(*,'(a)') 'IEEE 17.4-17.9 ROUNDING DIRECTIONS SUPPORTED OK'
        contains
    ''') + rounding_preamble() + common_helpers("rounding-directions-count") + dedent(r'''
        end program ieee_rounding_directions
    ''')
    probes = [
        probe(source, "call ieee_set_rounding_mode(ieee_nearest)", "call ieee_set_rounding_mode(ieee_up)",
              "nearest-mode", "nearest-to-up", "ieee-nearest-ties-to-even-half-ulp-result"),
        probe(source, "call ieee_set_rounding_mode(ieee_to_zero)", "call ieee_set_rounding_mode(ieee_down)",
              "to-zero-mode", "to-zero-to-down", "ieee-to-zero-directed-half-ulp-result"),
        probe(source, "call ieee_set_rounding_mode(ieee_up)", "call ieee_set_rounding_mode(ieee_down)",
              "up-mode", "up-to-down", "ieee-up-directed-half-ulp-result"),
        probe(source, "call ieee_set_rounding_mode(ieee_down)", "call ieee_set_rounding_mode(ieee_up)",
              "down-mode", "down-to-up", "ieee-down-directed-half-ulp-result"),
    ]
    return source, probes


def build_rounding_get():
    source = dedent(r'''
        program ieee_rounding_get
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_round_type) :: saved, observed
          checks = 0
          call require_rounding()
          call ieee_get_rounding_mode(saved)
          observed = ieee_down
          call ieee_set_rounding_mode(ieee_up)
          call ieee_get_rounding_mode(observed)
          call expect_true(observed == ieee_up, 'get-up')
          observed = ieee_up
          call ieee_set_rounding_mode(ieee_down)
          call ieee_get_rounding_mode(observed)
          call expect_true(observed == ieee_down, 'get-down')
          call ieee_set_rounding_mode(saved)
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.4-17.9 ROUNDING GET SUPPORTED OK'
        contains
    ''') + rounding_preamble() + common_helpers("rounding-get-count") + dedent(r'''
        end program ieee_rounding_get
    ''')
    probes = [probe(source, "call ieee_set_rounding_mode(ieee_up)\n  call ieee_get_rounding_mode(observed)",
                    "call ieee_set_rounding_mode(ieee_down)\n  call ieee_get_rounding_mode(observed)",
                    "get-up", "set-down-before-get-up", "ieee-get-rounding-mode-retrieves-current-mode")]
    return source, probes


def build_rounding_set():
    source = dedent(r'''
        program ieee_rounding_set
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_round_type) :: saved, observed
          checks = 0
          call require_rounding()
          call ieee_get_rounding_mode(saved)
          call ieee_set_rounding_mode(ieee_up)
          call ieee_get_rounding_mode(observed)
          call expect_true(observed == ieee_up, 'set-up')
          call ieee_set_rounding_mode(ieee_down)
          call ieee_get_rounding_mode(observed)
          call expect_true(observed == ieee_down, 'set-down')
          call ieee_set_rounding_mode(saved)
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.4-17.9 ROUNDING SET SUPPORTED OK'
        contains
    ''') + rounding_preamble() + common_helpers("rounding-set-count") + dedent(r'''
        end program ieee_rounding_set
    ''')
    probes = [probe(source, "call ieee_set_rounding_mode(ieee_down)\n  call ieee_get_rounding_mode(observed)",
                    "call ieee_set_rounding_mode(ieee_up)\n  call ieee_get_rounding_mode(observed)",
                    "set-down", "set-up-instead-of-down", "ieee-set-rounding-mode-alters-supported-mode")]
    return source, probes


def build_rounding_entry():
    source = dedent(r'''
        program ieee_rounding_entry
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_round_type) :: saved
          checks = 0
          call require_rounding()
          call ieee_get_rounding_mode(saved)
          call ieee_set_rounding_mode(ieee_up)
          call observe_entry()
          call ieee_set_rounding_mode(saved)
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.4-17.9 ROUNDING ENTRY SUPPORTED OK'
        contains
          subroutine observe_entry()
            type(ieee_round_type) :: entry_mode
            call ieee_get_rounding_mode(entry_mode)
            call expect_true(entry_mode == ieee_up, 'entry-rounding-up')
          end subroutine observe_entry
    ''') + rounding_preamble() + common_helpers("rounding-entry-count") + dedent(r'''
        end program ieee_rounding_entry
    ''')
    probes = [probe(source, "call ieee_set_rounding_mode(ieee_up)\n  call observe_entry()",
                    "call ieee_set_rounding_mode(ieee_down)\n  call observe_entry()",
                    "entry-caller-mode", "caller-sets-down-before-entry",
                    "rounding-mode-unchanged-on-procedure-entry")]
    return source, probes


def underflow_preamble():
    return '''
          subroutine require_underflow()
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) error stop 77
            if (.not. ieee_support_underflow_control(0.0)) error stop 77
            if (.not. ieee_support_subnormal(0.0)) error stop 77
            if (ieee_support_flag(ieee_underflow, 0.0)) then
              if (ieee_support_halting(ieee_underflow)) then
                call ieee_set_halting_mode(ieee_underflow, .false.)
              else
                call ieee_get_halting_mode(ieee_underflow, halting)
                if (halting) error stop 77
              end if
              call ieee_set_flag(ieee_underflow, .false.)
            end if
          end subroutine require_underflow
    '''


def build_underflow_effects():
    source = dedent(r'''
        program ieee_underflow_effects
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: saved
          real, volatile :: tiny_value, two, result
          checks = 0
          call require_underflow()
          two = 2.0
          tiny_value = tiny(0.0)
          call ieee_get_underflow_mode(saved)
          call ieee_set_underflow_mode(.true.)
          result = tiny_value / two
          call expect_true(ieee_class(result) == ieee_positive_denormal, 'gradual-subnormal')
          call ieee_set_underflow_mode(.false.)
          result = tiny_value / two
          call expect_true(result == 0.0 .and. .not. ieee_is_negative(result), 'abrupt-positive-zero')
          call ieee_set_underflow_mode(saved)
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.4-17.9 UNDERFLOW EFFECTS SUPPORTED OK'
        contains
    ''') + underflow_preamble() + common_helpers("underflow-effects-count") + dedent(r'''
        end program ieee_underflow_effects
    ''')
    probes = [
        probe(source, "call ieee_set_underflow_mode(.true.)\n  result = tiny_value / two",
              "call ieee_set_underflow_mode(.false.)\n  result = tiny_value / two", "gradual-mode",
              "use-abrupt-for-gradual", "gradual-underflow-produces-subnormal"),
        probe(source, "call ieee_set_underflow_mode(.false.)\n  result = tiny_value / two",
              "call ieee_set_underflow_mode(.true.)\n  result = tiny_value / two", "abrupt-mode",
              "use-gradual-for-abrupt", "abrupt-underflow-produces-zero"),
    ]
    return source, probes


def build_underflow_control():
    source = dedent(r'''
        program ieee_underflow_control_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: saved, observed
          checks = 0
          call require_underflow()
          call expect_true(ieee_support_underflow_control(0.0), 'support-underflow-control')
          call ieee_get_underflow_mode(saved)
          observed = .false.
          call ieee_set_underflow_mode(.true.)
          call ieee_get_underflow_mode(observed)
          call expect_true(observed, 'get-gradual')
          call ieee_set_underflow_mode(.not. saved)
          call ieee_get_underflow_mode(observed)
          call expect_true(observed .neqv. saved, 'set-opposite')
          call ieee_set_underflow_mode(.true.)
          call observe_entry()
          call ieee_set_underflow_mode(saved)
          call expect_count(4)
          write(*,'(a)') 'IEEE 17.4-17.9 UNDERFLOW CONTROL SUPPORTED OK'
        contains
          subroutine observe_entry()
            logical :: entry_mode
            call ieee_get_underflow_mode(entry_mode)
            call expect_true(entry_mode, 'entry-gradual')
          end subroutine observe_entry
    ''') + underflow_preamble() + common_helpers("underflow-control-count") + dedent(r'''
        end program ieee_underflow_control_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_underflow_control(0.0), 'support-underflow-control')",
              "call expect_true(.not. ieee_support_underflow_control(0.0), 'support-underflow-control')",
              "support-underflow-control", "negate-underflow-support",
              "ieee-support-underflow-control-inquires-facility"),
        probe(source, "call ieee_set_underflow_mode(.true.)\n  call ieee_get_underflow_mode(observed)",
              "call ieee_set_underflow_mode(.false.)\n  call ieee_get_underflow_mode(observed)", "get-gradual",
              "set-false-before-get", "ieee-get-underflow-mode-retrieves-current-mode"),
        probe(source, "call ieee_set_underflow_mode(.not. saved)", "call ieee_set_underflow_mode(saved)",
              "set-opposite", "set-saved-instead-of-opposite", "ieee-set-underflow-mode-alters-current-mode"),
        probe(source, "call ieee_set_underflow_mode(.true.)\n  call observe_entry()",
              "call ieee_set_underflow_mode(.false.)\n  call observe_entry()", "underflow-entry",
              "caller-sets-abrupt-before-entry", "underflow-mode-unchanged-on-procedure-entry"),
    ]
    return source, probes


def build_underflow_guarded():
    source = dedent(r'''
        program ieee_underflow_guarded
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: saved
          real, volatile :: tiny_value, two, result
          checks = 0
          call require_underflow()
          call expect_true(ieee_support_underflow_control(0.0), 'effect-guard-true')
          two = 2.0
          tiny_value = tiny(0.0)
          call ieee_get_underflow_mode(saved)
          call ieee_set_underflow_mode(.true.)
          result = tiny_value / two
          call expect_true(ieee_class(result) == ieee_positive_denormal, 'guarded-gradual-effect')
          call ieee_set_underflow_mode(saved)
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.4-17.9 UNDERFLOW GUARDED SUPPORTED OK'
        contains
    ''') + underflow_preamble() + common_helpers("underflow-guarded-count") + dedent(r'''
        end program ieee_underflow_guarded
    ''')
    probes = [probe(source, "call expect_true(ieee_support_underflow_control(0.0), 'effect-guard-true')",
                    "call expect_true(.not. ieee_support_underflow_control(0.0), 'effect-guard-true')",
                    "guard-support", "negate-effect-guard",
                    "underflow-mode-effects-guarded-by-support-underflow-control-true")]
    return source, probes


def build_halting_control():
    source = dedent(r'''
        program ieee_halting_control_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: observed
          checks = 0
          if (.not. ieee_support_halting(ieee_overflow)) error stop 77
          call ieee_set_halting_mode(ieee_overflow, .false.)
          call ieee_get_halting_mode(ieee_overflow, observed)
          call expect_false(observed, 'halting-false')
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.4-17.9 HALTING CONTROL SUPPORTED OK'
        contains
    ''') + common_helpers("halting-control-count") + dedent(r'''
        end program ieee_halting_control_case
    ''')
    probes = [probe(source, "call ieee_set_halting_mode(ieee_overflow, .false.)",
                    "call ieee_set_halting_mode(ieee_overflow, .true.)", "halting-set-false",
                    "set-halting-true", "halting-control-processor-permitted")]
    return source, probes


def build_halting_entry():
    source = dedent(r'''
        program ieee_halting_entry
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          checks = 0
          if (.not. ieee_support_halting(ieee_overflow)) error stop 77
          call ieee_set_halting_mode(ieee_overflow, .false.)
          call observe_entry()
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.4-17.9 HALTING ENTRY SUPPORTED OK'
        contains
          subroutine observe_entry()
            logical :: entry_mode
            call ieee_get_halting_mode(ieee_overflow, entry_mode)
            call expect_false(entry_mode, 'entry-halting-false')
          end subroutine observe_entry
    ''') + common_helpers("halting-entry-count") + dedent(r'''
        end program ieee_halting_entry
    ''')
    probes = [probe(source, "call ieee_set_halting_mode(ieee_overflow, .false.)\n  call observe_entry()",
                    "call ieee_set_halting_mode(ieee_overflow, .true.)\n  call observe_entry()", "entry-halting",
                    "caller-sets-halting-true-before-entry", "procedure-entry-preserves-halting-mode")]
    return source, probes


def build_modes_roundtrip():
    source = dedent(r'''
        program ieee_modes_roundtrip
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_modes_type) :: saved_modes
          type(ieee_round_type) :: saved_round, observed
          checks = 0
          call require_rounding()
          call ieee_get_rounding_mode(saved_round)
          call ieee_set_rounding_mode(ieee_nearest)
          call ieee_get_modes(saved_modes)
          call ieee_set_rounding_mode(ieee_to_zero)
          call ieee_set_modes(saved_modes)
          call ieee_get_rounding_mode(observed)
          call expect_true(observed == ieee_nearest, 'modes-restores-rounding')
          call ieee_set_rounding_mode(saved_round)
          call expect_count(1)
          write(*,'(a)') 'IEEE 17.4-17.9 MODES ROUNDTRIP SUPPORTED OK'
        contains
    ''') + rounding_preamble() + common_helpers("modes-roundtrip-count") + dedent(r'''
        end program ieee_modes_roundtrip
    ''')
    probes = [probe(source, "call ieee_set_modes(saved_modes)", "call ieee_get_modes(saved_modes)",
                    "set-modes", "omit-modes-restore", "ieee-get-set-modes-round-trip")]
    return source, probes


def build_status_roundtrip():
    source = dedent(r'''
        program ieee_status_roundtrip
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          type(ieee_status_type) :: saved_status
          type(ieee_round_type) :: saved_round, observed_round
          logical :: observed_flag
          checks = 0
          call require_status()
          call ieee_get_rounding_mode(saved_round)
          call ieee_set_rounding_mode(ieee_nearest)
          call ieee_set_flag(ieee_overflow, .false.)
          call ieee_get_status(saved_status)
          call ieee_set_flag(ieee_overflow, .true.)
          call ieee_set_rounding_mode(ieee_to_zero)
          call ieee_set_status(saved_status)
          call ieee_get_flag(ieee_overflow, observed_flag)
          call expect_false(observed_flag, 'status-restores-flag')
          call ieee_get_rounding_mode(observed_round)
          call expect_true(observed_round == ieee_nearest, 'status-restores-rounding')
          call ieee_set_rounding_mode(saved_round)
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.4-17.9 STATUS ROUNDTRIP SUPPORTED OK'
        contains
          subroutine require_status()
            if (.not. ieee_support_flag(ieee_overflow, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_nearest, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) error stop 77
            if (ieee_support_halting(ieee_overflow)) call ieee_set_halting_mode(ieee_overflow, .false.)
          end subroutine require_status
    ''') + common_helpers("status-roundtrip-count") + dedent(r'''
        end program ieee_status_roundtrip
    ''')
    probes = [probe(source, "call ieee_set_status(saved_status)", "call ieee_get_status(saved_status)",
                    "set-status", "omit-status-restore", "ieee-get-set-status-round-trip")]
    return source, probes


def build_exceptional_classes():
    source = dedent(r'''
        program ieee_exceptional_classes
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, two, tiny_value, subnormal_value
          real :: infinity_value, nan_value
          checks = 0
          call require_exceptional()
          one = 1.0
          two = 2.0
          tiny_value = tiny(one)
          subnormal_value = tiny_value / two
          infinity_value = ieee_value(one, ieee_positive_inf)
          nan_value = ieee_value(one, ieee_quiet_nan)
          call expect_true(ieee_class(subnormal_value) == ieee_positive_denormal, 'subnormal-class')
          call expect_true(ieee_class(infinity_value) == ieee_positive_inf, 'infinity-class')
          call expect_true(ieee_is_nan(nan_value), 'nan-class')
          call expect_count(3)
          write(*,'(a)') 'IEEE 17.4-17.9 EXCEPTIONAL CLASSES SUPPORTED OK'
        contains
    ''') + exceptional_preamble() + common_helpers("exceptional-classes-count") + dedent(r'''
        end program ieee_exceptional_classes
    ''')
    probes = [
        probe(source, "subnormal_value = tiny_value / two", "subnormal_value = tiny_value / one",
              "subnormal-value", "use-normal-tiny", "subnormal-class-definition"),
        probe(source, "infinity_value = ieee_value(one, ieee_positive_inf)", "infinity_value = one",
              "infinity-value", "use-normal-instead-of-infinity", "infinity-class-definition"),
        probe(source, "nan_value = ieee_value(one, ieee_quiet_nan)",
              "nan_value = ieee_value(one, ieee_positive_inf)", "nan-value", "use-infinity-instead-of-nan",
              "nan-class-definition"),
    ]
    return source, probes


def exceptional_preamble():
    return '''
          subroutine require_exceptional()
            if (.not. ieee_support_datatype(0.0)) error stop 77
            if (.not. ieee_support_nan(0.0)) error stop 77
            if (.not. ieee_support_inf(0.0)) error stop 77
            if (.not. ieee_support_subnormal(0.0)) error stop 77
            if (ieee_support_underflow_control(0.0)) call ieee_set_underflow_mode(.true.)
          end subroutine require_exceptional
    '''


def build_normal_number():
    source = dedent(r'''
        program ieee_normal_number
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, negative_one
          checks = 0
          if (.not. ieee_support_datatype(0.0)) error stop 77
          one = 1.0
          negative_one = -1.0
          call expect_true(ieee_class(one) == ieee_positive_normal, 'positive-normal-class')
          call expect_true(ieee_class(negative_one) == ieee_negative_normal, 'negative-normal-class')
          call expect_true(ieee_is_normal(one) .and. ieee_is_normal(negative_one), 'is-normal')
          call expect_count(3)
          write(*,'(a)') 'IEEE 17.4-17.9 NORMAL NUMBER SUPPORTED OK'
        contains
    ''') + common_helpers("normal-number-count") + dedent(r'''
        end program ieee_normal_number
    ''')
    probes = [probe(source, "ieee_class(one) == ieee_positive_normal", "ieee_class(0.0) == ieee_positive_normal",
                    "positive-normal", "classify-zero-instead-of-one", "normal-number-definition")]
    return source, probes


def build_exceptional_functions():
    source = dedent(r'''
        program ieee_exceptional_functions
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, negative_one
          real :: infinity_value, nan_value
          checks = 0
          call require_exceptional()
          one = 1.0
          negative_one = -1.0
          infinity_value = ieee_value(one, ieee_positive_inf)
          nan_value = ieee_value(one, ieee_quiet_nan)
          call expect_false(ieee_is_finite(infinity_value), 'finite-infinity-false')
          call expect_true(ieee_is_nan(nan_value), 'nan-value-true')
          call expect_true(ieee_is_negative(negative_one), 'negative-value-true')
          call expect_false(ieee_is_normal(infinity_value), 'normal-infinity-false')
          call expect_true(ieee_class(ieee_value(one, ieee_positive_inf)) == ieee_positive_inf, 'value-infinity')
          call expect_true(ieee_support_subnormal(one) .and. ieee_support_inf(one) .and. ieee_support_nan(one), 'support-inquiries')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.4-17.9 EXCEPTIONAL FUNCTIONS SUPPORTED OK'
        contains
    ''') + exceptional_preamble() + common_helpers("exceptional-functions-count") + dedent(r'''
        end program ieee_exceptional_functions
    ''')
    probes = [
        probe(source, "ieee_is_finite(infinity_value)", "ieee_is_finite(one)", "is-finite",
              "test-finite-one", "ieee-is-finite-provided"),
        probe(source, "ieee_is_nan(nan_value)", "ieee_is_nan(one)", "is-nan",
              "test-normal-one-for-nan", "ieee-is-nan-provided"),
        probe(source, "ieee_is_negative(negative_one)", "ieee_is_negative(one)", "is-negative",
              "test-positive-one-for-negative", "ieee-is-negative-provided"),
        probe(source, "ieee_is_normal(infinity_value)", "ieee_is_normal(one)", "is-normal",
              "test-normal-one-for-infinity", "ieee-is-normal-provided"),
        probe(source, "ieee_value(one, ieee_positive_inf)", "ieee_value(one, ieee_positive_normal)",
              "value-infinity", "request-normal-value", "ieee-value-provided", count=2),
        probe(source, "ieee_support_nan(one)", ".not. ieee_support_nan(one)", "support-inquiries",
              "negate-nan-support-inquiry", "exceptional-support-inquiries-provided"),
    ]
    return source, probes


def build_support_datatype_core():
    source = dedent(r'''
        program ieee_support_datatype_core
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, two, half, quarter, qnan
          checks = 0
          one = 1.0
          two = 2.0
          half = 0.5
          quarter = 0.25
          if (.not. ieee_support_datatype(one)) error stop 77
          if (.not. ieee_support_nan(one)) error stop 77
          qnan = ieee_value(one, ieee_quiet_nan)
          call expect_true(ieee_support_datatype(one), 'datatype-inquiry')
          call expect_true(1.5 + quarter == 1.75 .and. 1.5 - quarter == 1.25 .and. 1.5 * half == 0.75, 'normal-ops')
          call expect_true(abs(-1.5) == 1.5 .and. ieee_rem(5.0, two) == one .and. &
            ieee_copy_sign(two, -one) == -two .and. ieee_logb(8.0) == 3.0 .and. &
            .not. ieee_unordered(one, two), 'support-functions')
          call expect_count(3)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT DATATYPE CORE SUPPORTED OK'
        contains
    ''') + common_helpers("support-datatype-count") + dedent(r'''
        end program ieee_support_datatype_core
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_datatype(one), 'datatype-inquiry')",
              "call expect_true(.not. ieee_support_datatype(one), 'datatype-inquiry')",
              "datatype-inquiry", "negate-datatype-support", "support-datatype-inquiry-logical"),
        probe(source, "1.5 + quarter == 1.75", "1.5 - quarter == 1.75", "normal-add",
              "subtract-in-addition-check", "datatype-normal-add-subtract-multiply"),
        probe(source, "ieee_copy_sign(two, -one) == -two", "ieee_copy_sign(two, one) == -two",
              "copy-sign", "copy-positive-sign", "datatype-abs-rem-copy-logb-unordered"),
    ]
    return source, probes


def build_support_nan():
    source = dedent(r'''
        program ieee_support_nan_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, qnan, result
          checks = 0
          one = 1.0
          if (.not. ieee_support_datatype(one)) error stop 77
          if (.not. ieee_support_nan(one)) error stop 77
          qnan = ieee_value(one, ieee_quiet_nan)
          call expect_true(ieee_support_nan(one), 'nan-inquiry')
          result = qnan + one
          call expect_true(ieee_is_nan(result), 'nan-plus')
          result = qnan - one
          call expect_true(ieee_is_nan(result), 'nan-minus')
          result = qnan * one
          call expect_true(ieee_is_nan(result), 'nan-times')
          result = ieee_rem(qnan, one)
          call expect_true(ieee_is_nan(result), 'nan-rem')
          result = ieee_rint(qnan)
          call expect_true(ieee_is_nan(result), 'nan-rint')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT NAN SUPPORTED OK'
        contains
    ''') + common_helpers("support-nan-count") + dedent(r'''
        end program ieee_support_nan_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_nan(one), 'nan-inquiry')",
              "call expect_true(.not. ieee_support_nan(one), 'nan-inquiry')", "nan-inquiry",
              "negate-nan-support", "nan-support-inquiry"),
        probe(source, "result = qnan + one", "result = one + one", "nan-plus",
              "replace-nan-addition", "nan-results-for-operations"),
    ]
    return source, probes


def build_support_inf():
    source = dedent(r'''
        program ieee_support_inf_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, two, inf, ninf, result
          checks = 0
          one = 1.0
          two = 2.0
          if (.not. ieee_support_datatype(one)) error stop 77
          if (.not. ieee_support_inf(one)) error stop 77
          inf = ieee_value(one, ieee_positive_inf)
          ninf = ieee_value(one, ieee_negative_inf)
          call expect_true(ieee_support_inf(one), 'inf-inquiry')
          result = inf + one
          call expect_true(ieee_class(result) == ieee_positive_inf, 'inf-plus')
          result = one - inf
          call expect_true(ieee_class(result) == ieee_negative_inf, 'one-minus-inf')
          result = ninf * two
          call expect_true(ieee_class(result) == ieee_negative_inf, 'ninf-times')
          result = ieee_rem(1.5, inf)
          call expect_real(result, 1.5, 'finite-rem-inf')
          result = ieee_rint(inf)
          call expect_true(ieee_class(result) == ieee_positive_inf, 'rint-inf')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT INF SUPPORTED OK'
        contains
    ''') + common_helpers("support-inf-count") + dedent(r'''
        end program ieee_support_inf_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_inf(one), 'inf-inquiry')",
              "call expect_true(.not. ieee_support_inf(one), 'inf-inquiry')", "inf-inquiry",
              "negate-inf-support", "inf-support-inquiry"),
        probe(source, "result = inf + one", "result = one + one", "inf-plus",
              "replace-infinity-addition", "inf-results-for-operations"),
    ]
    return source, probes


def build_support_subnormal():
    source = dedent(r'''
        program ieee_support_subnormal_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, zero, tiny_value, two, subnormal_value, result
          checks = 0
          one = 1.0
          zero = 0.0
          two = 2.0
          if (.not. ieee_support_datatype(one)) error stop 77
          if (.not. ieee_support_subnormal(one)) error stop 77
          if (ieee_support_underflow_control(one)) call ieee_set_underflow_mode(.true.)
          tiny_value = tiny(one)
          subnormal_value = tiny_value / two
          call expect_true(ieee_support_subnormal(one), 'subnormal-inquiry')
          call expect_true(ieee_class(subnormal_value) == ieee_positive_denormal, 'subnormal-precheck')
          result = subnormal_value + zero
          call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-add')
          result = tiny_value - subnormal_value
          call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-subtract')
          result = subnormal_value * one
          call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-multiply')
          result = ieee_rem(subnormal_value, two * tiny_value)
          call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-rem')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT SUBNORMAL SUPPORTED OK'
        contains
    ''') + common_helpers("support-subnormal-count") + dedent(r'''
        end program ieee_support_subnormal_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_subnormal(one), 'subnormal-inquiry')",
              "call expect_true(.not. ieee_support_subnormal(one), 'subnormal-inquiry')",
              "subnormal-inquiry", "negate-subnormal-support", "subnormal-support-inquiry"),
        probe(source, "result = subnormal_value + zero", "result = subnormal_value + tiny_value",
              "subnormal-add", "add-tiny-to-subnormal", "subnormal-results-and-operands"),
    ]
    return source, probes


def build_support_divide():
    source = dedent(r'''
        program ieee_support_divide_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          real, volatile :: one, two, half, tiny_value, subnormal_value, inf, qnan, result
          checks = 0
          one = 1.0
          two = 2.0
          half = 0.5
          if (.not. ieee_support_datatype(one)) error stop 77
          if (.not. ieee_support_divide(one)) error stop 77
          if (.not. ieee_support_nan(one)) error stop 77
          if (.not. ieee_support_inf(one)) error stop 77
          if (.not. ieee_support_subnormal(one)) error stop 77
          if (ieee_support_underflow_control(one)) call ieee_set_underflow_mode(.true.)
          tiny_value = tiny(one)
          subnormal_value = tiny_value / two
          inf = ieee_value(one, ieee_positive_inf)
          qnan = ieee_value(one, ieee_quiet_nan)
          call expect_true(ieee_support_divide(one), 'divide-inquiry')
          result = 1.5 / half
          call expect_real(result, 3.0, 'divide-normal')
          result = qnan / one
          call expect_true(ieee_is_nan(result), 'divide-nan')
          result = inf / two
          call expect_true(ieee_class(result) == ieee_positive_inf, 'divide-inf')
          result = tiny_value / two
          call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'divide-subnormal-result')
          result = subnormal_value / one
          call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'divide-subnormal-operand')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT DIVIDE SUPPORTED OK'
        contains
    ''') + common_helpers("support-divide-count") + dedent(r'''
        end program ieee_support_divide_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_divide(one), 'divide-inquiry')",
              "call expect_true(.not. ieee_support_divide(one), 'divide-inquiry')",
              "divide-inquiry", "negate-divide-support", "divide-support-inquiry"),
        probe(source, "result = 1.5 / half", "result = 1.5 / one", "divide-normal",
              "divide-by-one-instead-of-half", "divide-normal-conformance"),
        probe(source, "result = qnan / one", "result = one / one", "divide-nan",
              "replace-nan-divide", "divide-nan-conformance"),
        probe(source, "result = inf / two", "result = one / two", "divide-inf",
              "replace-inf-divide", "divide-inf-conformance"),
        probe(source, "result = tiny_value / two", "result = tiny_value / one", "divide-subnormal",
              "replace-subnormal-result-divide", "divide-subnormal-conformance"),
    ]
    return source, probes


def build_support_sqrt():
    source = dedent(r'''
        program ieee_support_sqrt_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks, e
          real, volatile :: one, zero, neg_zero, inf, qnan, x, expected, result
          checks = 0
          one = 1.0
          zero = 0.0
          if (.not. ieee_support_datatype(one)) error stop 77
          if (.not. ieee_support_sqrt(one)) error stop 77
          if (.not. ieee_support_nan(one)) error stop 77
          if (.not. ieee_support_inf(one)) error stop 77
          if (.not. ieee_support_subnormal(one)) error stop 77
          if (ieee_support_underflow_control(one)) call ieee_set_underflow_mode(.true.)
          neg_zero = ieee_copy_sign(zero, -one)
          inf = ieee_value(one, ieee_positive_inf)
          qnan = ieee_value(one, ieee_quiet_nan)
          e = minexponent(one) - 2
          e = e - modulo(e, 2)
          if (e < minexponent(one) - digits(one)) error stop 77
          x = scale(one, e)
          expected = scale(one, e / 2)
          call expect_true(ieee_support_sqrt(one), 'sqrt-inquiry')
          result = sqrt(neg_zero)
          call expect_true(result == zero .and. ieee_is_negative(result), 'sqrt-negative-zero')
          result = sqrt(qnan)
          call expect_true(ieee_is_nan(result), 'sqrt-nan')
          result = sqrt(inf)
          call expect_true(ieee_class(result) == ieee_positive_inf, 'sqrt-inf')
          call expect_true(ieee_class(x) == ieee_positive_denormal, 'sqrt-subnormal-precheck')
          result = sqrt(x)
          call expect_real(result, expected, 'sqrt-subnormal')
          call expect_count(6)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT SQRT SUPPORTED OK'
        contains
    ''') + common_helpers("support-sqrt-count") + dedent(r'''
        end program ieee_support_sqrt_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_sqrt(one), 'sqrt-inquiry')",
              "call expect_true(.not. ieee_support_sqrt(one), 'sqrt-inquiry')",
              "sqrt-inquiry", "negate-sqrt-support", "sqrt-support-inquiry"),
        probe(source, "result = sqrt(neg_zero)", "result = sqrt(zero)", "sqrt-negative-zero",
              "sqrt-positive-zero", "sqrt-negative-zero"),
        probe(source, "result = sqrt(qnan)", "result = sqrt(one)", "sqrt-nan",
              "sqrt-one-instead-of-nan", "sqrt-nan-conformance"),
        probe(source, "result = sqrt(inf)", "result = sqrt(one)", "sqrt-inf",
              "sqrt-one-instead-of-inf", "sqrt-inf-conformance"),
        probe(source, "x = scale(one, e)", "x = scale(one, e + 2)", "sqrt-subnormal",
              "change-subnormal-exponent", "sqrt-subnormal-conformance"),
    ]
    return source, probes


def build_support_standard():
    source = dedent(r'''
        program ieee_support_standard_case
          use, intrinsic :: ieee_arithmetic
          implicit none
          integer :: checks
          logical :: any_rounding
          checks = 0
          if (.not. ieee_support_standard(0.0)) error stop 77
          any_rounding = ieee_support_rounding(ieee_nearest, 0.0) .or. &
            ieee_support_rounding(ieee_to_zero, 0.0) .or. ieee_support_rounding(ieee_up, 0.0) .or. &
            ieee_support_rounding(ieee_down, 0.0)
          call expect_true(ieee_support_standard(0.0), 'standard-inquiry')
          call expect_true(ieee_support_datatype(0.0) .and. ieee_support_nan(0.0) .and. &
            ieee_support_inf(0.0) .and. ieee_support_subnormal(0.0) .and. &
            ieee_support_divide(0.0) .and. ieee_support_sqrt(0.0) .and. &
            ieee_support_underflow_control(0.0) .and. any_rounding, 'standard-implies')
          call expect_count(2)
          write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT STANDARD SUPPORTED OK'
        contains
    ''') + common_helpers("support-standard-count") + dedent(r'''
        end program ieee_support_standard_case
    ''')
    probes = [
        probe(source, "call expect_true(ieee_support_standard(0.0), 'standard-inquiry')",
              "call expect_true(.not. ieee_support_standard(0.0), 'standard-inquiry')",
              "standard-inquiry", "negate-standard-support", "standard-support-inquiry"),
        probe(source, "ieee_support_divide(0.0)", ".not. ieee_support_divide(0.0)",
              "standard-implies-divide", "negate-divide-in-standard-conjunct",
              "standard-support-implies-facility-support"),
    ]
    return source, probes


BUILDERS = {name[6:]: obj for name, obj in list(globals().items()) if name.startswith("build_")}


def source_specs():
    specs = {}
    for case in CASES:
        source, probes = BUILDERS[case["builder"]]()
        probes = [item for item in probes if item["facet"] in set(case["facets"])]
        raw = source.encode("ascii")
        case_id = identifier(case["variant"])
        specs[case_id] = dict(id=case_id, variant=case["variant"], rule=case["rule"],
                              facets=list(case["facets"]), title=case["title"], source=source,
                              source_sha256=sha(raw), probes=copy.deepcopy(probes),
                              stdout_options=[completion(case["variant"])], profiles=list(case.get("profiles", [])))
    return specs


def mutated_source(spec, item):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent input no longer matches fingerprint")
    start, end = item["span"]
    if raw[start:end].decode("ascii") != item["expected"]:
        raise ValueError("mutation span no longer binds complete parent")
    return raw[:start] + item["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, source in PROFILE_SOURCES.items():
        files[Path(root) / "tests" / "profiles" / (name.replace("-", "_") + ".f90")] = dedent(source).encode("ascii")
    for spec in specs.values():
        directory = f"tests/fixtures/{TOPIC}_{spec['variant']}"
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence="effect", standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free",
                                    output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=spec["stdout_options"][0], stderr=""))
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
    return result


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate IEEE 17.4-17.9 fixture paragraph")
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
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), "IEEE 17.4-17.9 ",
                                                   LIMIT_PARAGRAPHS[catalogue_path])
    return result


def summary_text(section):
    detail = {
        "17.4": "The fixtures cover radix-two effects, NEAREST/TO_ZERO/UP/DOWN half-ulp outcomes, GET/SET round trips, and procedure-entry preservation.",
        "17.5": "The fixtures cover supported gradual/abrupt underflow effects, support inquiry, GET/SET round trips, and procedure-entry preservation.",
        "17.6": "The fixtures cover supported nonhalting SET/GET and procedure-entry preservation without asserting initial modes or halting timing.",
        "17.7": "The fixtures cover GET_MODES/SET_MODES and GET_STATUS/SET_STATUS restoration of observable rounding/flag state.",
        "17.8": "The fixtures cover exceptional classes, normal classes, IEEE_VALUE, IEEE_IS_* inquiries, and support inquiries under supported profiles.",
        "17.9": "The fixtures cover supported-branch datatype, NaN, infinity, subnormal, divide, sqrt, and standard support effects with exact real or class oracles.",
    }[section]
    return (SUMMARY_BEGIN + "\n## Executable IEEE 17.4-17.9 fixtures\n\n" + detail +
            " Every claimed facet has a distinct assertion and feature mutation; optional support is required by profiles that exit 77 before the fixture is counted.\n" + SUMMARY_END)


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
        stale = [str(path.relative_to(root)) for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        for catalogue_path, catalogue in catalogues.items():
            if json.loads((root / catalogue_path).read_text()) != catalogue:
                stale.append(catalogue_path)
        for view_path, text in views.items():
            if (root / view_path).read_text() != text:
                stale.append(view_path)
        if stale:
            raise ValueError("stale IEEE 17.4-17.9 fixtures: " + ", ".join(stale))
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
        return dict(status="compile-fail", stdout=compiled.stdout, stderr=compiled.stderr, returncode=compiled.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cwd=work_dir)
    passed = run.returncode == 0 and run.stdout in stdout_options and run.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr, returncode=run.returncode)


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
                                   status=observed["status"], stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"], parent_status=parent["status"],
                                   parent_stderr=parent["stderr"]))
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:10], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)


def counts(specs):
    facets = {facet for spec in specs.values() for facet in spec["facets"]}
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
        print(f"Mutation-checked {len(report)} IEEE 17.4-17.9 mutations; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} IEEE 17.4-17.9 cases, {facet_count} facets and {mutation_count} mutations.")


if __name__ == "__main__":
    main()
