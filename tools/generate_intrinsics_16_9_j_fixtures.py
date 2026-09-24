#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.88-16.9.91 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_j"
SECTIONS = ("16.9.88", "16.9.89", "16.9.90", "16.9.91")
CATALOGUES = {
    "16.9.88": "doc/catalogues/findloc_16_9_88.json",
    "16.9.89": "doc/catalogues/floor_16_9_89.json",
    "16.9.90": "doc/catalogues/fraction_16_9_90.json",
    "16.9.91": "doc/catalogues/gamma_16_9_91.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}

REMAINING_PENDING = {
    "S16.9.90-007": {
        "fraction-ieee-nan-identity-no-portable-oracle": (
            "PENDING after intrinsics_16_9_j: the executable IEEE fixture checks only that FRACTION(NaN) is a NaN; "
            "Fortran IEEE inquiry support used by this suite provides no portable payload/signaling identity comparison."
        ),
    },
    "S16.9.91-001": {
        "gamma-function-inquiry": (
            "PENDING after intrinsics_16_9_j: p5 makes the numeric GAMMA value a processor-dependent approximation, "
            "so this packet covers only valid source use, elemental shape, and direct kind characteristics."
        ),
    },
    "S16.9.91-004": {
        "gamma-x-not-negative-integer-or-zero": (
            "PENDING after F289R-1: this is an unnumbered shall-not argument restriction; a positive control with "
            "allowed values does not discharge it, and calls with zero or negative integers have no required diagnostic facet."
        ),
    },
    "S16.9.91-006": {
        "gamma-processor-dependent-approximation": (
            "PENDING after intrinsics_16_9_j: no exact or tolerance-free portable oracle exists for the processor-dependent "
            "approximation, including GAMMA(1.0); exact real equality is intentionally not asserted."
        ),
    },
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


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


def without_owned_paragraph(text, prefix):
    return "\n\n".join(paragraph for paragraph in (text.split("\n\n") if text else [])
                       if not paragraph.startswith(prefix))


def fail_block(token):
    return f"    write(*,'(a)') '{token}'\n    error stop\n"


def guard(variant, name, condition):
    token = f"I16J:{variant}:{name}"
    return f"  if ({condition}) then\n{fail_block(token)}  end if\n  checks=checks+1\n"


def finish_source(variant, body, use_ieee=False):
    checks = body.count("checks=checks+1")
    program = "intrinsics_16_9_j_" + variant
    completion = "INTRINSICS 16.9.J " + variant.upper().replace("_", " ") + " OK"
    use_line = "  use, intrinsic :: ieee_arithmetic\n" if use_ieee else ""
    source = (
        f"program {program}\n"
        + use_line +
        "  implicit none\n"
        "  integer :: checks\n"
        + body.replace("__CHECKS__", str(checks)) +
        f"  write(*,'(a)') '{completion}'\n"
        f"end program {program}\n"
    )
    return source, completion + "\n", checks


def make_case(section, rule, facets, variant, body, features, derivation, evidence="effect", profiles=None, use_ieee=False):
    source, completion, checks = finish_source(variant, body, use_ieee=use_ieee)
    return dict(section=section, rule=rule, facets=list(facets), variant=variant, source=source,
                completion=completion, checks=checks, feature_specs=list(features), derivation=derivation,
                evidence=evidence, profiles=list(profiles or []))


IK_DECL = "  integer, parameter :: ik = selected_int_kind(12)\n"
RK_DECL = "  integer, parameter :: rk = kind(0.0d0)\n"
CHECK_TOTAL = "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16J:check-total") + "  end select\n"


CASES = [
    make_case(
        "16.9.88", "S16.9.88-001", ["findloc-signature-array-value-optional-arguments"],
        "findloc_signature_options",
        IK_DECL +
        "  integer :: grid(2,3)\n"
        "  logical :: mask(2,3)\n"
        "  integer(ik), allocatable :: masked_back(:)\n"
        "  integer, allocatable :: positional(:), dimmed(:)\n"
        "  checks=0\n"
        "  grid = reshape([1, 2, 7, 4, 7, 6], [2,3])\n"
        "  mask = reshape([.false., .true., .true., .false., .true., .true.], [2,3])\n"
        "  positional = findloc(grid, 7)\n" +
        guard("findloc_signature_options", "positional-array-value", "any(positional /= [1, 2])") +
        "  masked_back = findloc(array=grid, value=7, mask=mask, kind=ik, back=.true.)\n" +
        guard("findloc_signature_options", "named-optional-arguments", "any(masked_back /= [1_ik, 3_ik])") +
        "  dimmed = findloc(grid, 7, dim=1, mask=mask)\n" +
        guard("findloc_signature_options", "dim-mask-branch", "any(dimmed /= [0, 1, 1])") + CHECK_TOTAL,
        [("findloc-signature-array-value-optional-arguments", "back=.true.", "back=.false.")],
        "The signature line admits positional ARRAY/VALUE plus named MASK, KIND, BACK and DIM forms; exact FINDLOC results distinguish the selected optional-argument branch."
    ),
    make_case(
        "16.9.88", "S16.9.88-003", ["findloc-transformational-function-class"],
        "findloc_transformational_class",
        "  integer :: grid(2,2)\n"
        "  checks=0\n"
        "  grid = reshape([1, 5, 5, 9], [2,2])\n" +
        guard("findloc_transformational_class", "whole-array-transform", "size(findloc(grid, 5)) /= rank(grid)") +
        guard("findloc_transformational_class", "subscript-vector", "any(findloc(grid, 5) /= [2, 1])") + CHECK_TOTAL,
        [("findloc-transformational-function-class", "findloc(grid, 5)) /= rank(grid)", "findloc(grid(:,1), 5)) /= rank(grid)")],
        "The p2 transformational classification is reached by applying FINDLOC to a whole rank-two array and observing its rank-sized subscript-vector result."
    ),
    make_case(
        "16.9.88", "S16.9.88-004", ["findloc-array-intrinsic-array"],
        "findloc_array_argument_types",
        "  integer :: ints(3)\n"
        "  character(len=2) :: words(3)\n"
        "  integer, allocatable :: word_hit(:)\n"
        "  checks=0\n"
        "  ints = [9, 2, 4]\n"
        "  words = ['aa', 'bb', 'cc']\n"
        "  word_hit = findloc(words, 'bb')\n" +
        guard("findloc_array_argument_types", "character-array", "any(word_hit /= [2])") +
        "  word_hit = findloc(ints, 9)\n" +
        guard("findloc_array_argument_types", "integer-array", "any(word_hit /= [1])") + CHECK_TOTAL,
        [("findloc-array-intrinsic-array", "findloc(words, 'bb')", "findloc(words, 'cc')")],
        "The ARRAY restriction is exercised by conforming intrinsic-type arrays, including character and integer arrays, with exact equality-based locations.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.88", "S16.9.88-005", ["findloc-value-scalar-type-conformant"],
        "findloc_value_argument",
        "  logical :: flags(4)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  flags = [.false., .true., .true., .false.]\n"
        "  hit = findloc(flags, .true.)\n" +
        guard("findloc_value_argument", "logical-scalar-value", "any(hit /= [2])") + CHECK_TOTAL,
        [("findloc-value-scalar-type-conformant", "findloc(flags, .true.)", "findloc(flags, .false.)")],
        "The VALUE restriction is exercised with a scalar logical VALUE conforming to a logical ARRAY, and the exact first .EQV. match is observed.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.88", "S16.9.88-006", ["findloc-dim-scalar-valid-range"],
        "findloc_dim_argument",
        "  integer :: grid(2,3)\n"
        "  integer, allocatable :: dim_hit(:)\n"
        "  checks=0\n"
        "  grid = reshape([1, 2, 2, 3, 4, 2], [2,3])\n"
        "  dim_hit = findloc(grid, 2, dim=1)\n" +
        guard("findloc_dim_argument", "dim-one-in-range", "any(dim_hit /= [2, 1, 2])") + CHECK_TOTAL,
        [("findloc-dim-scalar-valid-range", "dim=1", "dim=2")],
        "The DIM restriction is exercised by a scalar integer DIM=1 in range for a rank-two ARRAY; switching to the other valid DIM changes the section reductions.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.88", "S16.9.88-007", ["findloc-mask-logical-conformable"],
        "findloc_mask_argument",
        "  integer :: grid(2,3)\n"
        "  logical :: mask(2,3), all_true(2,3)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  grid = reshape([0, 3, 7, 4, 7, 6], [2,3])\n"
        "  mask = reshape([.false., .false., .false., .false., .true., .false.], [2,3])\n"
        "  all_true = .true.\n"
        "  hit = findloc(grid, 7, mask=mask)\n" +
        guard("findloc_mask_argument", "logical-conformable-mask", "any(hit /= [1, 3])") + CHECK_TOTAL,
        [("findloc-mask-logical-conformable", "mask=mask", "mask=all_true")],
        "The MASK restriction is exercised by a logical conformable mask whose true element selects a later matching ARRAY element.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.88", "S16.9.88-008", ["findloc-kind-scalar-integer-constant"],
        "findloc_kind_argument",
        IK_DECL +
        "  checks=0\n" +
        guard("findloc_kind_argument", "constant-kind", "kind(findloc([2, 4], 4, kind=ik)) /= ik") + CHECK_TOTAL,
        [("findloc-kind-scalar-integer-constant", "kind=ik", "kind=kind(0)")],
        "The KIND restriction is exercised with the scalar integer constant parameter IK and a direct KIND inquiry on the FINDLOC expression.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.88", "S16.9.88-009", ["findloc-back-logical-scalar"],
        "findloc_back_argument",
        "  integer :: values(4)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  values = [2, 6, 4, 6]\n"
        "  hit = findloc(values, 6, back=.true.)\n" +
        guard("findloc_back_argument", "logical-scalar-back", "any(hit /= [4])") + CHECK_TOTAL,
        [("findloc-back-logical-scalar", "back=.true.", "back=.false.")],
        "The BACK restriction is exercised with a logical scalar BACK=.TRUE.; repeated matches make the exact last-location result load-bearing.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.88", "S16.9.88-010", ["findloc-default-integer-kind", "findloc-kind-selects-result-kind"],
        "findloc_result_kind",
        IK_DECL +
        "  checks=0\n" +
        guard("findloc_result_kind", "default-kind", "kind(findloc([2, 4], 4)) /= kind(0)") +
        guard("findloc_result_kind", "selected-kind", "kind(findloc([2, 4], 4, kind=ik)) /= ik") + CHECK_TOTAL,
        [("findloc-default-integer-kind", "kind(findloc([2, 4], 4))", "kind(findloc([2, 4], 4, kind=ik))"),
         ("findloc-kind-selects-result-kind", "kind(findloc([2, 4], 4, kind=ik))", "kind(findloc([2, 4], 4))")],
        "p4 fixes default integer kind when KIND is absent and the requested kind when KIND is present; both are inquired directly on FINDLOC expressions."
    ),
    make_case(
        "16.9.88", "S16.9.88-011", ["findloc-no-dim-rank-one", "findloc-no-dim-size-array-rank"],
        "findloc_no_dim_shape",
        "  integer :: vector(3), grid(2,3)\n"
        "  checks=0\n"
        "  vector = [2, 6, 4]\n"
        "  grid = reshape([1, 2, 2, 3, 4, 2], [2,3])\n" +
        guard("findloc_no_dim_shape", "rank-one-result", "size(shape(findloc(vector, 6))) /= 1") +
        guard("findloc_no_dim_shape", "size-equals-array-rank", "size(findloc(grid, 2)) /= rank(grid)") + CHECK_TOTAL,
        [("findloc-no-dim-rank-one", "size(shape(findloc(vector, 6)))", "size(shape(findloc(vector, 6, dim=1)))"),
         ("findloc-no-dim-size-array-rank", "size(findloc(grid, 2))", "size(findloc(grid(:,1), 2))")],
        "p4 says absent DIM yields a rank-one result sized by ARRAY rank; direct RANK and SIZE inquiries observe those characteristics."
    ),
    make_case(
        "16.9.88", "S16.9.88-012", ["findloc-dim-result-rank-n-minus-one", "findloc-dim-result-shape-drops-dim"],
        "findloc_dim_shape",
        "  integer :: vector(3), grid(2,3)\n"
        "  checks=0\n"
        "  vector = [2, 6, 4]\n"
        "  grid = reshape([1, 2, 2, 3, 4, 2], [2,3])\n" +
        guard("findloc_dim_shape", "rank-n-minus-one", "size(shape(findloc(vector, 6, dim=1))) /= 0") +
        guard("findloc_dim_shape", "shape-drops-dim", "any(shape(findloc(grid, 2, dim=1)) /= [3])") + CHECK_TOTAL,
        [("findloc-dim-result-rank-n-minus-one", "size(shape(findloc(vector, 6, dim=1)))", "size(shape(findloc(vector, 6)))"),
         ("findloc-dim-result-shape-drops-dim", "dim=1)) /= [3]", "dim=2)) /= [3]")],
        "p4 says present DIM drops that dimension; direct RANK and SHAPE inquiries on FINDLOC expressions observe the scalar rank-one case and a 2x3 DIM=1 shape."
    ),
    make_case(
        "16.9.88", "S16.9.88-002", ["findloc-specified-value-location"],
        "findloc_specified_value",
        "  integer :: values(4)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  values = [3, 8, 9, 8]\n"
        "  hit = findloc(values, 9)\n" +
        guard("findloc_specified_value", "specified-value", "any(hit /= [3])") + CHECK_TOTAL,
        [("findloc-specified-value-location", "findloc(values, 9)", "findloc(values, 8)")],
        "p1 describes location of a specified VALUE; exact subscript [3] is returned for the only element equal to 9."
    ),
    make_case(
        "16.9.88", "S16.9.88-013", ["findloc-case-i-match-subscript-values", "findloc-case-i-no-match-all-zero", "findloc-case-i-zero-size-all-zero"],
        "findloc_case_i_values",
        "  integer :: values(4), misses(3)\n"
        "  integer, allocatable :: empty(:), hit(:)\n"
        "  checks=0\n"
        "  values = [2, 6, 4, 6]\n"
        "  misses = [2, 4, 8]\n"
        "  allocate(empty(0))\n"
        "  empty = 6\n"
        "  hit = findloc(values, 6)\n" +
        guard("findloc_case_i_values", "matching-subscript", "any(hit /= [2])") +
        "  hit = findloc(misses, 6)\n" +
        guard("findloc_case_i_values", "no-match-zero", "any(hit /= [0])") +
        "  hit = findloc(empty, 6)\n" +
        guard("findloc_case_i_values", "zero-size-zero", "any(hit /= [0])") + CHECK_TOTAL,
        [("findloc-case-i-match-subscript-values", "values = [2, 6, 4, 6]", "values = [6, 2, 4, 6]"),
         ("findloc-case-i-no-match-all-zero", "misses = [2, 4, 8]", "misses = [2, 6, 8]"),
         ("findloc-case-i-zero-size-all-zero", "allocate(empty(0))", "allocate(empty(1))")],
        "p5 case (i) fixes exact subscript values for a match and all-zero vectors for no-match and zero-size arrays."
    ),
    make_case(
        "16.9.88", "S16.9.88-014", ["findloc-case-ii-masked-match-subscripts", "findloc-case-ii-masked-no-match-zero", "findloc-case-ii-all-false-mask-zero"],
        "findloc_case_ii_mask",
        "  integer :: grid(2,3)\n"
        "  logical :: select_last(2,3), select_first(2,3), no_match_mask(2,3), false_mask(2,3)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  grid = reshape([0, 3, 7, 4, 7, 6], [2,3])\n"
        "  select_last = reshape([.false., .false., .false., .false., .true., .false.], [2,3])\n"
        "  select_first = reshape([.false., .false., .true., .false., .false., .false.], [2,3])\n"
        "  no_match_mask = reshape([.true., .true., .false., .true., .false., .true.], [2,3])\n"
        "  false_mask = .false.\n"
        "  hit = findloc(grid, 7, mask=select_last)\n" +
        guard("findloc_case_ii_mask", "masked-match", "any(hit /= [1, 3])") +
        "  hit = findloc(grid, 7, mask=no_match_mask)\n" +
        guard("findloc_case_ii_mask", "masked-no-match", "any(hit /= [0, 0])") +
        "  hit = findloc(grid, 7, mask=false_mask)\n" +
        guard("findloc_case_ii_mask", "all-false-mask", "any(hit /= [0, 0])") + CHECK_TOTAL,
        [("findloc-case-ii-masked-match-subscripts", "mask=select_last", "mask=select_first"),
         ("findloc-case-ii-masked-no-match-zero", "mask=no_match_mask", "mask=select_last"),
         ("findloc-case-ii-all-false-mask-zero", "false_mask = .false.", "false_mask = select_last")],
        "p5 case (ii) applies MASK before matching: a true matching mask selects [1,3], while no true matching element or all-false MASK yields all zeros."
    ),
    make_case(
        "16.9.88", "S16.9.88-015", ["findloc-case-iii-rank-one-dim-scalar", "findloc-case-iii-section-wise-dim-values"],
        "findloc_case_iii_dim",
        "  integer :: vector(3), grid(2,3), scalar_hit\n"
        "  integer, allocatable :: dim_hit(:)\n"
        "  checks=0\n"
        "  vector = [2, 6, 4]\n"
        "  grid = reshape([1, 2, 2, 2, -9, 6], [2,3])\n"
        "  scalar_hit = findloc(vector, 6, dim=1)\n" +
        guard("findloc_case_iii_dim", "rank-one-dim-scalar", "scalar_hit /= 2") +
        "  dim_hit = findloc(grid, 2, dim=1)\n" +
        guard("findloc_case_iii_dim", "section-wise-dim", "any(dim_hit /= [2, 1, 0])") + CHECK_TOTAL,
        [("findloc-case-iii-rank-one-dim-scalar", "findloc(vector, 6, dim=1)", "findloc(vector, 4, dim=1)"),
         ("findloc-case-iii-section-wise-dim-values", "grid = reshape([1, 2, 2, 2, -9, 6], [2,3])", "grid = reshape([2, 1, 2, 2, -9, 6], [2,3])")],
        "p5 case (iii) fixes the rank-one DIM scalar and section-wise DIM reductions, including both nonzero and zero section results."
    ),
    make_case(
        "16.9.88", "S16.9.88-016", ["findloc-logical-comparison-eqv", "findloc-nonlogical-comparison-equality"],
        "findloc_comparison_semantics",
        "  logical :: flags(4)\n"
        "  character(len=2) :: words(3)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  flags = [.false., .true., .true., .false.]\n"
        "  words = ['aa', 'bb', 'aa']\n"
        "  hit = findloc(flags, .true.)\n" +
        guard("findloc_comparison_semantics", "logical-eqv", "any(hit /= [2])") +
        "  hit = findloc(words, 'bb')\n" +
        guard("findloc_comparison_semantics", "nonlogical-equality", "any(hit /= [2])") + CHECK_TOTAL,
        [("findloc-logical-comparison-eqv", "findloc(flags, .true.)", "findloc(flags, .false.)"),
         ("findloc-nonlogical-comparison-equality", "findloc(words, 'bb')", "findloc(words, 'aa')")],
        "p6 selects .EQV. for logical ARRAY/VALUE and == for nonlogical intrinsic types; exact first matches distinguish the comparison."
    ),
    make_case(
        "16.9.88", "S16.9.88-017", ["findloc-back-absent-or-false-first", "findloc-back-true-last", "findloc-back-array-element-order"],
        "findloc_back_order",
        "  integer :: values(4), grid(2,3)\n"
        "  integer, allocatable :: hit(:)\n"
        "  checks=0\n"
        "  values = [2, 6, 4, 6]\n"
        "  grid = reshape([9, 1, 9, 1, 1, 9], [2,3])\n"
        "  hit = findloc(values, 6, back=.false.)\n" +
        guard("findloc_back_order", "back-false-first", "any(hit /= [2])") +
        "  hit = findloc(values, 6, back=.true.)\n" +
        guard("findloc_back_order", "back-true-last", "any(hit /= [4])") +
        "  hit = findloc(grid, 9, back=.true.)\n" +
        guard("findloc_back_order", "array-element-order", "any(hit /= [2, 3])") + CHECK_TOTAL,
        [("findloc-back-absent-or-false-first", "back=.false.", "back=.true."),
         ("findloc-back-true-last", "findloc(values, 6, back=.true.)", "findloc(values, 6, back=.false.)"),
         ("findloc-back-array-element-order", "grid = reshape([9, 1, 9, 1, 1, 9], [2,3])", "grid = reshape([9, 1, 9, 1, 9, 1], [2,3])")],
        "p7 selects first or last matching element in Fortran array element order; repeated vector and rank-two matches make BACK and element order exact."
    ),
    make_case(
        "16.9.89", "S16.9.89-001", ["floor-greatest-integer-inquiry"],
        "floor_inquiry",
        "  integer :: observed\n"
        "  checks=0\n"
        "  observed = floor(-3.25)\n" +
        guard("floor_inquiry", "greatest-integer", "observed /= -4") + CHECK_TOTAL,
        [("floor-greatest-integer-inquiry", "floor(-3.25)", "ceiling(-3.25)")],
        "p1 describes the greatest integer not greater than A; exact -3.25 distinguishes FLOOR (-4) from CEILING/truncation."
    ),
    make_case(
        "16.9.89", "S16.9.89-002", ["floor-elemental-function-class"],
        "floor_elemental",
        "  real :: values(3)\n"
        "  integer :: observed(3)\n"
        "  checks=0\n"
        "  values = [3.75, -3.25, -3.0]\n"
        "  observed = floor(values)\n" +
        guard("floor_elemental", "elementwise-values", "any(observed /= [3, -4, -3])") +
        guard("floor_elemental", "elementwise-shape", "any(shape(floor(values)) /= [3])") + CHECK_TOTAL,
        [("floor-elemental-function-class", "observed = floor(values)", "observed = floor(values(1))")],
        "p2 classifies FLOOR as elemental; a rank-one real array yields corresponding exact integer elements and shape."
    ),
    make_case(
        "16.9.89", "S16.9.89-003", ["floor-a-real", "floor-kind-scalar-integer-constant"],
        "floor_arguments",
        IK_DECL + RK_DECL +
        "  real(rk) :: high\n"
        "  integer(ik) :: selected\n"
        "  checks=0\n"
        "  high = 5.75_rk\n"
        "  selected = floor(high, kind=ik)\n" +
        guard("floor_arguments", "real-a", "selected /= 5_ik") +
        guard("floor_arguments", "constant-kind", "kind(floor(high, kind=ik)) /= ik") + CHECK_TOTAL,
        [("floor-a-real", "high = 5.75_rk", "high = 4.75_rk"),
         ("floor-kind-scalar-integer-constant", "kind(floor(high, kind=ik))", "kind(floor(high))")],
        "p3 is exercised by a selected-kind real A and scalar integer constant KIND; direct KIND inquiry verifies the constant branch.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.89", "S16.9.89-004", ["floor-default-integer-kind", "floor-kind-selects-result-kind"],
        "floor_result_kind",
        IK_DECL +
        "  checks=0\n" +
        guard("floor_result_kind", "default-kind", "kind(floor(3.75)) /= kind(0)") +
        guard("floor_result_kind", "selected-kind", "kind(floor(3.75, kind=ik)) /= ik") + CHECK_TOTAL,
        [("floor-default-integer-kind", "kind(floor(3.75))", "kind(floor(3.75, kind=ik))"),
         ("floor-kind-selects-result-kind", "kind(floor(3.75, kind=ik))", "kind(floor(3.75))")],
        "p4 fixes default integer kind without KIND and requested integer kind with KIND; both are inquired directly on FLOOR expressions."
    ),
    make_case(
        "16.9.89", "S16.9.89-005", ["floor-positive-fraction", "floor-negative-fraction", "floor-exact-integer-unchanged"],
        "floor_exact_values",
        "  integer :: pos, neg, exact\n"
        "  checks=0\n"
        "  pos = floor(3.75)\n" +
        guard("floor_exact_values", "positive-fraction", "pos /= 3") +
        "  neg = floor(-3.25)\n" +
        guard("floor_exact_values", "negative-fraction", "neg /= -4") +
        "  exact = floor(-3.0)\n" +
        guard("floor_exact_values", "exact-integer", "exact /= -3") + CHECK_TOTAL,
        [("floor-positive-fraction", "floor(3.75)", "ceiling(3.75)"),
         ("floor-negative-fraction", "floor(-3.25)", "int(-3.25)"),
         ("floor-exact-integer-unchanged", "floor(-3.0)", "floor(-3.25)")],
        "p5 gives exact greatest-integer values; 3.75, -3.25, and -3.0 are exactly representable binary fractions/integers."
    ),
    make_case(
        "16.9.90", "S16.9.90-001", ["fraction-fractional-part-inquiry"],
        "fraction_inquiry",
        "  real :: expected, observed\n"
        "  checks=0\n"
        "  expected = 1.0 / real(radix(1.0), kind=kind(1.0))\n"
        "  observed = fraction(1.0)\n" +
        guard("fraction_inquiry", "model-fraction", "observed /= expected") + CHECK_TOTAL,
        [("fraction-fractional-part-inquiry", "fraction(1.0)", "nearest(1.0, -1.0)")],
        "p1 is observed through the real-model fractional part of the exact power b**0: FRACTION(1.0) equals 1/RADIX for the kind."
    ),
    make_case(
        "16.9.90", "S16.9.90-002", ["fraction-elemental-function-class"],
        "fraction_elemental",
        "  real :: values(3), observed(3), expected(3)\n"
        "  checks=0\n"
        "  values = [0.0, 1.0, real(radix(1.0), kind=kind(1.0))]\n"
        "  expected = [0.0, 1.0 / real(radix(1.0), kind=kind(1.0)), 1.0 / real(radix(1.0), kind=kind(1.0))]\n"
        "  observed = fraction(values)\n" +
        guard("fraction_elemental", "elementwise-values", "any(observed /= expected)") +
        guard("fraction_elemental", "elementwise-shape", "any(shape(fraction(values)) /= [3])") + CHECK_TOTAL,
        [("fraction-elemental-function-class", "observed = fraction(values)", "observed = fraction(values(1))")],
        "p2 classifies FRACTION as elemental; zero and powers of the radix give exact elementwise model values."
    ),
    make_case(
        "16.9.90", "S16.9.90-003", ["fraction-x-real"],
        "fraction_argument_real",
        RK_DECL +
        "  real(rk) :: high, expected, observed\n"
        "  checks=0\n"
        "  high = 1.0_rk\n"
        "  expected = 1.0_rk / real(radix(high), kind=rk)\n"
        "  observed = fraction(high)\n" +
        guard("fraction_argument_real", "selected-real-x", "observed /= expected") + CHECK_TOTAL,
        [("fraction-x-real", "high = 1.0_rk", "high = 1.5_rk")],
        "p3 is exercised by a selected-kind real X; exact powers of the model radix keep the positive control portable.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.90", "S16.9.90-004", ["fraction-result-same-kind-as-x"],
        "fraction_result_kind",
        RK_DECL +
        "  real(rk) :: high\n"
        "  checks=0\n"
        "  high = 1.0_rk\n" +
        guard("fraction_result_kind", "same-kind", "kind(fraction(high)) /= kind(high)") + CHECK_TOTAL,
        [("fraction-result-same-kind-as-x", "kind(fraction(high))", "kind(fraction(real(high, kind=kind(0.0))))")],
        "p4 says the result is same as X; the fixture inquires KIND directly on the FRACTION expression."
    ),
    make_case(
        "16.9.90", "S16.9.90-005", ["fraction-finite-model-value"],
        "fraction_finite_model",
        RK_DECL +
        "  real(rk) :: one, radix_power, expected, observed_one, observed_power\n"
        "  checks=0\n"
        "  one = 1.0_rk\n"
        "  radix_power = real(radix(one), kind=rk)\n"
        "  expected = 1.0_rk / real(radix(one), kind=rk)\n"
        "  observed_one = fraction(one)\n" +
        guard("fraction_finite_model", "one-model-value", "observed_one /= expected") +
        "  observed_power = fraction(radix_power)\n" +
        guard("fraction_finite_model", "radix-power-model-value", "observed_power /= expected") + CHECK_TOTAL,
        [("fraction-finite-model-value", "observed_power = fraction(radix_power)", "observed_power = nearest(fraction(radix_power), 1.0_rk)")],
        "p5 finite nonzero rule gives X*b**(-e); for exact powers of the model radix the result is exactly 1/RADIX for the kind."
    ),
    make_case(
        "16.9.90", "S16.9.90-006", ["fraction-zero-result-zero"],
        "fraction_zero",
        "  real :: zero, observed, nonzero_expected\n"
        "  checks=0\n"
        "  zero = 0.0\n"
        "  nonzero_expected = 1.0 / real(radix(1.0), kind=kind(1.0))\n"
        "  observed = fraction(zero)\n" +
        guard("fraction_zero", "zero-result", "observed /= 0.0") +
        guard("fraction_zero", "nonzero-companion", "fraction(1.0) /= nonzero_expected") + CHECK_TOTAL,
        [("fraction-zero-result-zero", "zero = 0.0", "zero = 1.0")],
        "p5 separately fixes zero to zero; a nonzero exact model companion prevents the all-zero branch from being the only observation."
    ),
    make_case(
        "16.9.90", "S16.9.90-007", ["fraction-ieee-nan-result-is-nan", "fraction-ieee-infinity-yields-nan"],
        "fraction_ieee_specials",
        "  real :: qnan, pinf, nan_result, inf_result\n"
        "  checks=0\n"
        "  qnan = ieee_value(0.0, ieee_quiet_nan)\n"
        "  pinf = ieee_value(0.0, ieee_positive_inf)\n"
        "  nan_result = fraction(qnan)\n" +
        guard("fraction_ieee_specials", "nan-remains-nan", ".not. ieee_is_nan(nan_result)") +
        "  inf_result = fraction(pinf)\n" +
        guard("fraction_ieee_specials", "infinity-yields-nan", ".not. ieee_is_nan(inf_result)") + CHECK_TOTAL,
        [("fraction-ieee-nan-result-is-nan", "nan_result = fraction(qnan)", "nan_result = fraction(1.0)"),
         ("fraction-ieee-infinity-yields-nan", "inf_result = fraction(pinf)", "inf_result = fraction(1.0)")],
        "p5 fixes only NaN class for IEEE NaN and infinity branches; the ieee-binary profile supplies the IEEE datatype support and no NaN payload identity is asserted.",
        profiles=["ieee-binary"], use_ieee=True
    ),
    make_case(
        "16.9.91", "S16.9.91-002", ["gamma-elemental-function-class"],
        "gamma_elemental",
        "  real :: values(3)\n"
        "  checks=0\n"
        "  values = [1.0, 1.5, -0.5]\n" +
        guard("gamma_elemental", "elementwise-shape", "any(shape(gamma(values)) /= [3])") + CHECK_TOTAL,
        [("gamma-elemental-function-class", "shape(gamma(values))", "shape(gamma(values(1:2)))")],
        "p2 classifies GAMMA as elemental; allowed rank-one inputs yield a rank-one result shape without asserting approximate values."
    ),
    make_case(
        "16.9.91", "S16.9.91-003", ["gamma-x-real"],
        "gamma_argument_real",
        RK_DECL +
        "  real(rk) :: high\n"
        "  checks=0\n"
        "  high = 1.5_rk\n" +
        guard("gamma_argument_real", "real-x", "kind(gamma(high)) /= kind(high)") + CHECK_TOTAL,
        [("gamma-x-real", "kind(gamma(high))", "kind(gamma(real(high, kind=kind(0.0))))")],
        "p3 is exercised by a selected-kind real X positive control, with only direct result kind observed.",
        evidence="positive-control"
    ),
    make_case(
        "16.9.91", "S16.9.91-005", ["gamma-result-same-kind-as-x"],
        "gamma_result_kind",
        RK_DECL +
        "  real(rk) :: high\n"
        "  checks=0\n"
        "  high = 1.5_rk\n" +
        guard("gamma_result_kind", "same-kind", "kind(gamma(high)) /= kind(high)") + CHECK_TOTAL,
        [("gamma-result-same-kind-as-x", "kind(gamma(high))", "kind(gamma(real(high, kind=kind(0.0))))")],
        "p4 says the result is same as X; KIND is inquired directly on the GAMMA expression and no approximate value is compared."
    ),
]


def identifier(case):
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__" + TOPIC + "_" + case["variant"]


def case_dir(root, case):
    return Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case["variant"])


def mutation_span(source, expected):
    count = source.count(expected)
    if count != 1:
        raise ValueError(f"mutation token is not unique ({count}): {expected!r}")
    start = source.index(expected)
    return [start, start + len(expected)]


def source_specs():
    specs = {}
    for case in CASES:
        source = case["source"]
        raw = source.encode("ascii")
        fid = identifier(case)
        completion_line = f"  write(*,'(a)') '{case['completion'].rstrip()}'"
        features = []
        if len(case["feature_specs"]) != len(case["facets"]):
            raise ValueError("feature/facet count mismatch for " + case["variant"])
        for facet, expected, replacement in case["feature_specs"]:
            features.append(dict(id="feature-" + facet, facet=facet, kind="feature", category="intrinsic-effect",
                                 expected=expected, replacement=replacement, span=mutation_span(source, expected),
                                 mutation="facet-feature-perturbation"))
        oracle = dict(id="check-count-oracle", kind="oracle", category="check-total",
                      expected=f"case ({case['checks']})", replacement=f"case ({case['checks'] + 1})",
                      span=mutation_span(source, f"case ({case['checks']})"), mutation="oracle-check-count")
        omission = dict(id="completion-omission", kind="output", category="completion",
                        expected=completion_line, replacement="! completion omitted",
                        span=mutation_span(source, completion_line), mutation="completion-omission")
        mutations = features + [oracle, omission]
        for mutation in mutations:
            start, end = mutation["span"]
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError("mutation span does not bind parent source")
            mutation["line"] = source[:start].count("\n") + 1
        specs[fid] = dict(id=fid, variant=case["variant"], section=case["section"], rule=case["rule"],
                          facets=case["facets"], evidence=case["evidence"], profiles=case["profiles"],
                          source=source, source_sha256=sha(raw), completion=case["completion"], checks=case["checks"],
                          derivation=case["derivation"], mutations=mutations, feature_mutations=features)
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = case_dir(root, spec)
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        if spec["profiles"]:
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def facets_by_rule():
    result = {}
    for case in CASES:
        result.setdefault(case["rule"], []).extend(case["facets"])
    return result


FACETS_BY_RULE = facets_by_rule()


def oracle_for(rule, specs):
    selected = [spec for spec in specs.values() if spec["rule"] == rule]
    prefix = f"{rule} {TOPIC} runtime fixture: "
    variants = ", ".join(spec["variant"] for spec in selected)
    facets = ", ".join(facet for spec in selected for facet in spec["facets"])
    derivations = " ".join(spec["derivation"] for spec in selected)
    return prefix + (f"the generated valid/f2023 fixture(s) `{variants}` cover {facets}. {derivations} "
                     "The source uses direct intrinsic-expression inquiries for result characteristics and exact integer, logical, character, shape, kind, IEEE NaN-class, or real-model power-of-radix observations; processor-dependent approximations are not compared exactly.")


def limitation_for(rule):
    prefix = f"{rule} {TOPIC} fixture boundaries: "
    return prefix + ("Only ordinary single-image valid programs are covered. Clause 16 unnumbered argument restrictions are "
                     "positive controls only and no diagnostic rejection is claimed. The fixtures do not assert compiler consensus, "
                     "coarray behavior, evaluation order beyond FINDLOC array element order, NaN payload identity, or exact values for "
                     "processor-dependent transcendental approximations.")


def synced_catalogue(section, catalogue, specs):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, pending in REMAINING_PENDING.items():
        if rule in by_rule:
            row = by_rule[rule]
            oprefix = f"{rule} {TOPIC} runtime fixture: "
            lprefix = f"{rule} {TOPIC} fixture boundaries: "
            row["oracle"] = without_owned_paragraph(row.get("oracle", ""), oprefix)
            row["oracle_limitation"] = without_owned_paragraph(row.get("oracle_limitation", ""), lprefix)
            for facet, reason in pending.items():
                if facet not in FACETS_BY_RULE.get(rule, []):
                    row.setdefault("pending", {})[facet] = reason
    for rule, facets in FACETS_BY_RULE.items():
        if not rule.startswith("S" + section):
            continue
        row = by_rule[rule]
        if not set(facets) <= set(row["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row.setdefault("pending", {})
        oprefix = f"{rule} {TOPIC} runtime fixture: "
        lprefix = f"{rule} {TOPIC} fixture boundaries: "
        row["oracle"] = owned_paragraph(without_owned_paragraph(row.get("oracle", ""), oprefix), oprefix,
                                          oracle_for(rule, specs))
        row["oracle_limitation"] = owned_paragraph(without_owned_paragraph(row.get("oracle_limitation", ""), lprefix),
                                                    lprefix, limitation_for(rule))
    for rule, pending in REMAINING_PENDING.items():
        if rule in by_rule:
            for facet in pending:
                if facet in FACETS_BY_RULE.get(rule, []):
                    raise ValueError("facet both covered and pending: " + facet)
    return updated


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
    owned_begin = f"<!-- BEGIN INTRINSICS 16.9.J FIXTURES {section} -->"
    owned_end = f"<!-- END INTRINSICS 16.9.J FIXTURES {section} -->"
    owned_cases = [case for case in CASES if case["section"] == section]
    covered = sum(len(case["facets"]) for case in owned_cases)
    pending = sum(len(p) for rule, p in REMAINING_PENDING.items() if rule.startswith("S" + section))
    summary = (owned_begin + "\n\n"
               f"## `{TOPIC}` executable fixture observations\n\n"
               f"This packet adds {len(owned_cases)} generated valid/f2023 fixtures for {section}, covering {covered} facets "
               "with exact FINDLOC/FLOOR integer results, direct result-characteristic inquiries, FRACTION real-model "
               "power-of-radix checks, IEEE NaN-class checks, and GAMMA characteristic-only checks. "
               f"{pending} facet(s) remain pending where no portable oracle exists.\n"
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


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues, rendered_views = {}, {}
    for section in SECTIONS:
        catalogue = json.loads((root / CATALOGUES[section]).read_text())
        updated = synced_catalogue(section, catalogue, specs)
        updated_catalogues[section] = updated
        rendered_views[section] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section in SECTIONS:
            if json.loads((root / CATALOGUES[section]).read_text()) != updated_catalogues[section]:
                stale.append(CATALOGUES[section])
            if (root / VIEWS[section]).read_text() != rendered_views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale intrinsics 16.9.j fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updated_catalogues[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(rendered_views[section])
    return specs


def std_args(compiler, std):
    name = Path(compiler).name.lower()
    if "gfortran" in name:
        return [f"-std={std}"]
    return [f"--std={std}"]


def compile_and_run(compiler, std, source, workdir, expected_stdout, timeout=30):
    workdir.mkdir(parents=True, exist_ok=True)
    source_path = workdir / "source.f90"
    exe_path = workdir / "program"
    source_path.write_bytes(source)
    cmd = [compiler] + std_args(compiler, std) + [str(source_path), "-o", str(exe_path)]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if comp.returncode != 0:
        return dict(phase="compile", passed=False, returncode=comp.returncode, stdout=comp.stdout, stderr=comp.stderr)
    run = subprocess.run([str(exe_path)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return dict(phase="run", passed=(run.returncode == 0 and run.stdout == expected_stdout and run.stderr == ""),
                returncode=run.returncode, stdout=run.stdout, stderr=run.stderr)


def run_mutations(root, compiler, std, skip_parent_failures=False):
    root = Path(root)
    specs = source_specs()
    work = root / "scratch_intrinsics_16_9_j_mutations"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    try:
        parents = mutants_failed = mutants_total = 0
        failures = []
        skipped = []
        for index, spec in enumerate(specs.values(), 1):
            parent = compile_and_run(compiler, std, spec["source"].encode("ascii"),
                                     work / f"{index:03d}_parent", spec["completion"])
            if not parent["passed"]:
                if skip_parent_failures:
                    skipped.append((spec["id"], parent))
                    continue
                failures.append((spec["id"], "parent", parent))
                continue
            parents += 1
            for midx, mutation in enumerate(spec["mutations"], 1):
                mutants_total += 1
                result = compile_and_run(compiler, std, mutated_source(spec, mutation),
                                         work / f"{index:03d}_{midx:02d}_{mutation['id']}", spec["completion"])
                if result["phase"] != "run" or result["passed"]:
                    failures.append((spec["id"], mutation["id"], result))
                else:
                    mutants_failed += 1
        if failures:
            lines = [f"mutation check failed for {len(failures)} item(s)"]
            for case_id, mutation_id, result in failures[:30]:
                lines.append(f"{case_id} {mutation_id} phase={result['phase']} rc={result['returncode']}")
                lines.append("stdout=" + result["stdout"][:500].replace("\n", "\\n"))
                lines.append("stderr=" + result["stderr"][:500].replace("\n", "\\n"))
            raise RuntimeError("\n".join(lines))
        return dict(parents=parents, mutants=mutants_failed, total=mutants_total, skipped=skipped)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-compiler")
    parser.add_argument("--mutation-std", default="f2023")
    parser.add_argument("--skip-parent-failures", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_compiler:
        result = run_mutations(args.root, args.mutation_compiler, args.mutation_std, args.skip_parent_failures)
        print(f"Mutation check OK: {result['parents']}/{len(CASES)} parents passed; "
              f"{result['mutants']}/{result['total']} mutants failed as expected; "
              f"{len(result['skipped'])} parents skipped.")
        if result["skipped"]:
            for case_id, parent in result["skipped"]:
                first = (parent["stdout"] + parent["stderr"]).splitlines()[:1]
                print("Skipped parent: " + case_id + (" :: " + first[0] if first else ""))
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics 16.9.j cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
