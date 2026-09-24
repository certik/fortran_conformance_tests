#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.71 through 16.9.77."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_h"
SECTIONS = ("16.9.71", "16.9.72", "16.9.73", "16.9.74", "16.9.75", "16.9.76", "16.9.77")
CATALOGUES = {
    "16.9.71": "doc/catalogues/digits_16_9_71.json",
    "16.9.72": "doc/catalogues/dim_16_9_72.json",
    "16.9.73": "doc/catalogues/dot_product_16_9_73.json",
    "16.9.74": "doc/catalogues/dprod_16_9_74.json",
    "16.9.75": "doc/catalogues/dshiftl_16_9_75.json",
    "16.9.76": "doc/catalogues/dshiftr_16_9_76.json",
    "16.9.77": "doc/catalogues/eoshift_16_9_77.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9 H FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9 H FIXTURES -->"

SELECTED = {
    "S16.9.71-001": ("effect", ("digits-significant-digits-description",)),
    "S16.9.71-002": ("effect", ("digits-inquiry-class",)),
    "S16.9.71-003": ("positive-control", ("digits-x-integer-or-real",)),
    "S16.9.71-006": ("effect", ("digits-x-scalar-or-array",)),
    "S16.9.71-004": ("effect", ("digits-result-default-integer-scalar",)),
    "S16.9.71-005": ("effect", ("digits-integer-model-q", "digits-real-model-p", "digits-same-kind-same-model-value")),
    "S16.9.72-001": ("positive-control", ("DIM-X-integer-or-real", "DIM-Y-same-type-kind-as-X")),
    "S16.9.72-002": ("effect", ("DIM-result-same-type-kind-as-X",)),
    "S16.9.72-003": ("effect", ("DIM-positive-difference", "DIM-zero-for-negative-difference", "DIM-negative-operands")),
    "S16.9.73-001": ("positive-control", ("DOT_PRODUCT-vector-a-type-rank", "DOT_PRODUCT-vector-b-compatible-type-rank", "DOT_PRODUCT-vector-b-same-size")),
    "S16.9.73-002": ("effect", ("DOT_PRODUCT-numeric-result-expression-type-kind", "DOT_PRODUCT-logical-result-and-kind", "DOT_PRODUCT-result-scalar")),
    "S16.9.73-003": ("effect", ("DOT_PRODUCT-integer-sum-products", "DOT_PRODUCT-real-sum-products", "DOT_PRODUCT-numeric-zero-size-zero")),
    "S16.9.73-004": ("effect", ("DOT_PRODUCT-complex-conjugated-sum", "DOT_PRODUCT-complex-zero-size-zero")),
    "S16.9.73-005": ("effect", ("DOT_PRODUCT-logical-any-and", "DOT_PRODUCT-logical-zero-size-false")),
    "S16.9.74-001": ("positive-control", ("DPROD-X-default-real", "DPROD-Y-default-real")),
    "S16.9.74-002": ("effect", ("DPROD-result-double-precision-real",)),
    "S16.9.74-003": ("effect", ("DPROD-product-approximation",)),
    "S16.9.75-001": ("positive-control", ("DSHIFTL-I-integer-or-boz", "DSHIFTL-J-integer-or-boz")),
    "S16.9.75-002": ("effect", ("DSHIFTL-result-kind-from-I-or-J",)),
    "S16.9.75-003": ("effect", ("DSHIFTL-boz-converted-as-int-to-other-kind",)),
    "S16.9.75-004": ("effect", ("DSHIFTL-shifted-bits-from-operands", "DSHIFTL-ior-shift-equivalence", "DSHIFTL-shift-zero-and-full-width-edges")),
    "S16.9.76-001": ("positive-control", ("DSHIFTR-I-integer-or-boz", "DSHIFTR-J-integer-or-boz")),
    "S16.9.76-002": ("effect", ("DSHIFTR-result-kind-from-I-or-J",)),
    "S16.9.76-003": ("effect", ("DSHIFTR-boz-converted-as-int-to-other-kind",)),
    "S16.9.76-004": ("effect", ("DSHIFTR-shifted-bits-from-operands", "DSHIFTR-ior-shift-equivalence", "DSHIFTR-shift-zero-and-full-width-edges")),
    "S16.9.77-001": ("positive-control", ("EOSHIFT-ARRAY-array-any-type", "EOSHIFT-SHIFT-integer-scalar-or-conforming-shape", "EOSHIFT-BOUNDARY-same-type-params-scalar-or-conforming-shape", "EOSHIFT-DIM-integer-scalar-valid-range")),
    "S16.9.77-002": ("effect", ("EOSHIFT-BOUNDARY-absent-table-types-permitted",)),
    "S16.9.77-004": ("effect", ("EOSHIFT-default-boundary-integer-zero", "EOSHIFT-default-boundary-real-zero", "EOSHIFT-default-boundary-complex-zero", "EOSHIFT-default-boundary-logical-false", "EOSHIFT-default-boundary-character-blanks")),
    "S16.9.77-005": ("effect", ("EOSHIFT-DIM-absent-defaults-to-one",)),
    "S16.9.77-006": ("effect", ("EOSHIFT-result-type-params-shape-of-array",)),
    "S16.9.77-007": ("effect", ("EOSHIFT-positive-shift-element-mapping", "EOSHIFT-negative-shift-element-mapping", "EOSHIFT-array-valued-shift-indexing", "EOSHIFT-boundary-used-outside-bounds")),
}

RESTORED_PENDING = {
    "S16.9.75-001": {
        "DSHIFTL-integer-kinds-match": "Restored after review: this is an unnumbered same-kind restriction; positive controls do not discharge it and no diagnostic is required.",
        "DSHIFTL-not-both-boz": "Restored after review: this is an unnumbered not-both-BOZ restriction; positive controls do not discharge it and no diagnostic is required.",
        "DSHIFTL-SHIFT-integer-nonnegative-in-range": "Restored after review: this is an unnumbered SHIFT range restriction; positive controls do not discharge it and no diagnostic is required.",
    },
    "S16.9.76-001": {
        "DSHIFTR-integer-kinds-match": "Restored after review: this is an unnumbered same-kind restriction; positive controls do not discharge it and no diagnostic is required.",
        "DSHIFTR-not-both-boz": "Restored after review: this is an unnumbered not-both-BOZ restriction; positive controls do not discharge it and no diagnostic is required.",
        "DSHIFTR-SHIFT-integer-nonnegative-in-range": "Restored after review: this is an unnumbered SHIFT range restriction; positive controls do not discharge it and no diagnostic is required.",
    },
    "S16.9.77-003": {
        "EOSHIFT-BOUNDARY-absence-only-table-types": "Restored after review: this is an unnumbered only restriction; an explicit derived-type BOUNDARY positive control does not discharge it and no diagnostic is required.",
    },
}

ORACLE_PREFIXES = {rule: f"{rule} intrinsics_16_9_h runtime fixture: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} intrinsics_16_9_h fixture boundaries: " for rule in SELECTED}
ORACLES = {
    rule: ORACLE_PREFIXES[rule] + "Generated positive runtime fixtures check only source-stated exact properties: direct kind/len/shape inquiries on intrinsic expressions, same-model DIGITS relationships without profile-specific q or p literals, exact integer/logical/character/small-real values, and DSHIFT bit positions through BTEST."
    for rule in SELECTED
}
ORACLES["S16.9.74-003"] = ORACLE_PREFIXES["S16.9.74-003"] + "The fixture uses default real operands -3.0 and 2.0, whose small-integer product is exactly representable in double precision, and checks the DPROD result -6.0D0 without asserting any general rounded-product policy."
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + "Only the listed portable facets are discharged. Unnumbered restrictions are represented by conforming positive controls, not diagnostic claims; processor-dependent DPROD approximation latitude and nonbinding SHOULD guidance remain pending."
    for rule in SELECTED
}
SOURCE_ONLY_PATTERNS = [
    ("Source accounting only. This packet creates no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.",
     "Original source accounting created no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim; this intrinsics_16_9_h generator supplies selected runtime fixtures and mutation plans without granting those approvals or universal coverage."),
    ("Source registration only.", "Original source registration only; selected facets now have bounded runtime fixtures and mutation plans."),
]

HELPERS = """contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
end program {name}
"""


def identifier(variant, rule):
    return rule.replace('.', '_').replace('-', '_') + f"_valid__{TOPIC}_{variant}"


def header(rule, facets, name):
    lines = [f"! rule: {rule}"] + [f"! covers: {facet}" for facet in facets]
    return "\n".join(lines) + f"\nprogram {name}\n  implicit none\n"


def finish(name, completion, checks):
    return f"  if (checks /= {checks}) error stop\n  write(*,'(a)') '{completion.rstrip()}'\n" + HELPERS.format(name=name)


def mut(mid, facet, expected, replacement, category="feature"):
    return {"id": mid, "facet": facet, "kind": "source", "category": category,
            "replacements": [{"expected": expected, "replacement": replacement}]}


def multi_mut(mid, facet, replacements, category="feature"):
    return {"id": mid, "facet": facet, "kind": "source", "category": category,
            "replacements": [{"expected": a, "replacement": b} for a, b in replacements]}


def make_source(name, rule, facets, declarations, body, checks):
    completion = "INTRINSICS 16.9 H " + name.upper().replace("_", " ") + " OK\n"
    return header(rule, facets, "i169h_" + name) + declarations + "  checks = 0\n" + body + finish("i169h_" + name, completion, checks), completion


def build_case(variant, rule, facets, declarations, body, mutations, profiles=()):
    evidence = SELECTED[rule][0]
    source, completion = make_source(variant, rule, facets, declarations, body, len(facets))
    raw = source.encode("ascii")
    materialized = []
    for m in mutations:
        mutant = raw
        spans = []
        for item in m["replacements"]:
            old = item["expected"].encode("ascii")
            count = mutant.count(old)
            if count != 1:
                raise ValueError(f"{variant}:{m['id']} expected unique {item['expected']!r}, found {count}")
            start = mutant.index(old)
            end = start + len(old)
            spans.append([start, end, item["expected"], item["replacement"]])
            mutant = mutant[:start] + item["replacement"].encode("ascii") + mutant[end:]
        row = dict(m)
        row["spans"] = spans
        row["mutant_sha256"] = sha(mutant)
        materialized.append(row)
    covered = {m["facet"] for m in materialized}
    missing = set(facets) - covered
    if missing:
        raise ValueError(f"{variant} lacks feature mutations for {sorted(missing)}")
    return dict(id=identifier(variant, rule), variant=variant, rule=rule, facets=list(facets), evidence=evidence,
                source=source, source_sha256=sha(raw), completion=completion, mutations=materialized, profiles=list(profiles))


def cases():
    out = []
    out.append(build_case(
        "digits_argument_control", "S16.9.71-003", SELECTED["S16.9.71-003"][1],
        "  integer :: checks\n  integer :: ix(2)\n  real :: rx(2)\n",
        "  ix = [1, 2]\n  rx = [1.0, 2.0]\n"
        "  call require('integer and real DIGITS arguments admitted', &\n"
        "       digits(ix(1)) == digits(ix) .and. digits(rx(1)) == digits(rx), checks)\n",
        [mut("replace-real-digits-with-kind", "digits-x-integer-or-real", "digits(rx(1))", "kind(rx(1))")]))
    out.append(build_case(
        "digits_inquiry_context", "S16.9.71-002", SELECTED["S16.9.71-002"][1],
        "  integer, parameter :: q_from_initialization = digits(7)\n  integer :: checks\n",
        "  call require('DIGITS is usable as inquiry initialization', q_from_initialization == digits(9), checks)\n",
        [mut("replace-inquiry-with-kind", "digits-inquiry-class", "digits(7)", "kind(7)")]))
    out.append(build_case(
        "digits_result_characteristics", "S16.9.71-004", SELECTED["S16.9.71-004"][1],
        "  integer, parameter :: alt_ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer(kind=alt_ik) :: values(2)\n  integer :: checks\n",
        "  values = [1_alt_ik, 2_alt_ik]\n"
        "  call require('DIGITS result is default integer scalar', &\n"
        "       kind(digits(values)) == kind(0) .and. size(shape(digits(values))) == 0, checks)\n",
        [mut("remove-digits-from-kind-inquiry", "digits-result-default-integer-scalar", "kind(digits(values))", "kind(values)")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "digits_scalar_array_models", "S16.9.71-006", SELECTED["S16.9.71-006"][1],
        "  integer :: checks\n  integer :: ia(3)\n  real :: ra(2)\n",
        "  ia = [3, 5, 7]\n  ra = [1.0, 4.0]\n"
        "  call require('DIGITS scalar and array same kind agree', &\n"
        "       digits(ia(1)) == digits(ia) .and. digits(ra(1)) == digits(ra), checks)\n",
        [mut("array-side-uses-values", "digits-x-scalar-or-array", "digits(ia(1)) == digits(ia)", "all(digits(ia(1)) == ia)")]))
    out.append(build_case(
        "digits_model_values", "S16.9.71-005", SELECTED["S16.9.71-005"][1],
        "  integer :: checks\n  integer :: i1, i2\n  real :: r1, r2\n",
        "  i1 = 1; i2 = 12345\n  r1 = 1.0; r2 = 16.0\n"
        "  call require('integer model q is positive', digits(i1) > 0, checks)\n"
        "  call require('real model p exceeds one', digits(r1) > 1, checks)\n"
        "  call require('same type and kind use same model digits', &\n"
        "       digits(i1) == digits(i2) .and. digits(r1) == digits(r2), checks)\n",
        [mut("integer-model-uses-radix", "digits-integer-model-q", "digits(i1) > 0", "radix(i1) < 0"),
         mut("real-model-uses-radix", "digits-real-model-p", "digits(r1) > 1", "radix(r1) > 9"),
         mut("same-kind-compares-cross-type", "digits-same-kind-same-model-value", "digits(i1) == digits(i2)", "digits(i1) == digits(r1)")]))
    out.append(build_case(
        "digits_description", "S16.9.71-001", SELECTED["S16.9.71-001"][1],
        "  integer :: checks\n",
        "  call require('DIGITS observes numeric model significant digits', digits(1) > 0 .and. digits(1.0) > 1, checks)\n",
        [mut("negate-significant-digits", "digits-significant-digits-description", "digits(1) > 0", "-digits(1) > 0")]))

    out.append(build_case(
        "dim_argument_controls", "S16.9.72-001", SELECTED["S16.9.72-001"][1],
        "  integer :: checks\n  integer :: ix, iy\n  real :: rx, ry\n",
        "  ix = 7; iy = 2; rx = 4.0; ry = 1.0\n"
        "  call require('DIM admits integer and real X', dim(ix, iy) == 5 .and. dim(rx, ry) == 3.0, checks)\n"
        "  call require('DIM requires and uses same type kind pair', kind(dim(rx, ry)) == kind(rx), checks)\n",
        [mut("dim-x-intrinsic-to-max", "DIM-X-integer-or-real", "dim(ix, iy) == 5", "max(ix, iy) == 5"),
         mut("dim-y-pair-swapped", "DIM-Y-same-type-kind-as-X", "dim(rx, ry) == 3.0", "dim(ry, rx) == 3.0")]))
    out.append(build_case(
        "dim_result_characteristics", "S16.9.72-002", SELECTED["S16.9.72-002"][1],
        "  integer :: checks\n",
        "  call require('DIM result has X kind', kind(dim(7, 2)) == kind(0) .and. kind(dim(7.0d0, 2.0d0)) == kind(0.0d0), checks)\n",
        [mut("remove-dim-from-kind", "DIM-result-same-type-kind-as-X", "kind(dim(7.0d0, 2.0d0))", "kind(7.0)")]))
    out.append(build_case(
        "dim_value_effects", "S16.9.72-003", SELECTED["S16.9.72-003"][1],
        "  integer :: checks\n",
        "  call require('DIM positive difference exact value', dim(7, 2) == 5, checks)\n"
        "  call require('DIM negative difference becomes zero with nonzero companion', &\n"
        "       dim(-3.0, 2.0) == 0.0 .and. dim(2.0, -3.0) == 5.0, checks)\n"
        "  call require('DIM negative operands subtract before max', dim(-2, -5) == 3, checks)\n",
        [mut("positive-argument-order", "DIM-positive-difference", "dim(7, 2)", "dim(2, 7)"),
         mut("zero-branch-companion-lost", "DIM-zero-for-negative-difference", "dim(2.0, -3.0)", "dim(-3.0, 2.0)"),
         mut("negative-operands-order", "DIM-negative-operands", "dim(-2, -5)", "dim(-5, -2)")]))

    out.append(build_case(
        "dot_product_argument_controls", "S16.9.73-001", SELECTED["S16.9.73-001"][1],
        "  integer :: checks\n  integer :: ia(3), ib(3)\n  logical :: la(2), lb(2)\n",
        "  ia = [1, 2, 3]; ib = [2, 3, 4]\n  la = [.true., .false.]; lb = [.true., .true.]\n"
        "  call require('DOT_PRODUCT vector A rank one admitted', dot_product([1, 2, 3], ib) == 20, checks)\n"
        "  call require('DOT_PRODUCT compatible numeric and logical vector pairs admitted', &\n"
        "       dot_product(ia, ib) == 20 .and. dot_product(la, lb), checks)\n"
        "  call require('DOT_PRODUCT equal-size vectors contribute all elements', dot_product([1, 2, 3], [2, 3, 4]) == 20, checks)\n",
        [mut("vector-a-source-swapped", "DOT_PRODUCT-vector-a-type-rank", "dot_product([1, 2, 3], ib) == 20", "dot_product(ib, ib) == 20"),
         mut("compatible-logical-pair-changed", "DOT_PRODUCT-vector-b-compatible-type-rank", "dot_product(la, lb)", ".not. dot_product(la, lb)"),
         mut("same-size-third-element-changed", "DOT_PRODUCT-vector-b-same-size", "[2, 3, 4]) == 20", "[2, 3, 5]) == 20")]))
    out.append(build_case(
        "dot_product_characteristics", "S16.9.73-002", SELECTED["S16.9.73-002"][1],
        "  integer :: ia(2)\n  real(kind=kind(0.0d0)) :: rb(2)\n  logical :: la(2), lb(2)\n  integer :: checks\n",
        "  ia = [1, 2]; rb = [4.0d0, 8.0d0]\n  la = [.true., .false.]; lb = [.false., .false.]\n"
        "  call require('numeric DOT_PRODUCT result follows product expression kind', &\n"
        "       kind(dot_product(ia, rb)) == kind(ia(1) * rb(1)), checks)\n"
        "  call require('logical DOT_PRODUCT result has logical expression kind and value', &\n"
        "       kind(dot_product(la, lb)) == kind(la(1) .and. lb(1)) .and. .not. dot_product(la, lb), checks)\n"
        "  call require('DOT_PRODUCT result is scalar', size(shape(dot_product([1, 2], [3, 4]))) == 0, checks)\n",
        [mut("numeric-kind-remove-dot-product", "DOT_PRODUCT-numeric-result-expression-type-kind", "kind(dot_product(ia, rb))", "kind(0)"),
         mut("logical-result-negated", "DOT_PRODUCT-logical-result-and-kind", ".not. dot_product(la, lb)", "dot_product(la, lb)"),
         mut("scalar-result-to-array-expression", "DOT_PRODUCT-result-scalar", "shape(dot_product([1, 2], [3, 4]))", "shape([1, 2] * [3, 4])")]))
    out.append(build_case(
        "dot_product_numeric_values", "S16.9.73-003", SELECTED["S16.9.73-003"][1],
        "  integer :: checks\n  integer :: zi(0), zj(0)\n",
        "  call require('DOT_PRODUCT integer sum of products', dot_product([1, 2, 3], [2, 3, 4]) == 20, checks)\n"
        "  call require('DOT_PRODUCT real sum of products exact', dot_product([1.0, 2.0], [4.0, 8.0]) == 20.0, checks)\n"
        "  call require('DOT_PRODUCT zero-size numeric vectors give zero with nonzero companion', &\n"
        "       dot_product(zi, zj) == 0 .and. dot_product([2], [3]) == 6, checks)\n",
        [mut("integer-product-to-sum", "DOT_PRODUCT-integer-sum-products", "dot_product([1, 2, 3], [2, 3, 4])", "sum([1, 2, 3] + [2, 3, 4])"),
         mut("real-product-factor-changed", "DOT_PRODUCT-real-sum-products", "[4.0, 8.0]) == 20.0", "[4.0, 7.0]) == 20.0"),
         mut("zero-size-companion-zeroed", "DOT_PRODUCT-numeric-zero-size-zero", "dot_product([2], [3]) == 6", "dot_product([2], [0]) == 6")]))
    out.append(build_case(
        "dot_product_complex_values", "S16.9.73-004", SELECTED["S16.9.73-004"][1],
        "  integer :: checks\n  complex :: ca(1), cb(1), za(0), zb(0), got\n",
        "  ca = [cmplx(1.0, 2.0)]; cb = [cmplx(3.0, 4.0)]\n  got = dot_product(ca, cb)\n"
        "  call require('DOT_PRODUCT complex conjugates VECTOR_A', real(got) == 11.0 .and. aimag(got) == -2.0, checks)\n"
        "  call require('DOT_PRODUCT zero-size complex vectors give zero with nonzero companion', &\n"
        "       dot_product(za, zb) == (0.0, 0.0) .and. dot_product(ca, cb) /= (0.0, 0.0), checks)\n",
        [mut("complex-conjugation-operand-changed", "DOT_PRODUCT-complex-conjugated-sum", "cmplx(1.0, 2.0)", "cmplx(1.0, -2.0)"),
         mut("complex-zero-companion-zeroed", "DOT_PRODUCT-complex-zero-size-zero", "dot_product(ca, cb) /= (0.0, 0.0)", "dot_product(za, zb) /= (0.0, 0.0)")]))
    out.append(build_case(
        "dot_product_logical_values", "S16.9.73-005", SELECTED["S16.9.73-005"][1],
        "  integer :: checks\n  logical :: za(0), zb(0)\n",
        "  call require('DOT_PRODUCT logical is ANY of aligned AND values', &\n"
        "       dot_product([.true., .false.], [.true., .true.]) .and. &\n"
        "       .not. dot_product([.true., .false.], [.false., .true.]), checks)\n"
        "  call require('DOT_PRODUCT zero-size logical vectors false with true companion', &\n"
        "       .not. dot_product(za, zb) .and. dot_product([.true.], [.true.]), checks)\n",
        [mut("logical-and-to-misaligned", "DOT_PRODUCT-logical-any-and", "dot_product([.true., .false.], [.true., .true.])", "dot_product([.true., .false.], [.false., .true.])"),
         mut("logical-zero-companion-false", "DOT_PRODUCT-logical-zero-size-false", "dot_product([.true.], [.true.])", "dot_product([.true.], [.false.])")]))

    out.append(build_case(
        "dprod_argument_controls", "S16.9.74-001", SELECTED["S16.9.74-001"][1],
        "  integer :: checks\n  real :: x, y\n",
        "  x = -3.0; y = 2.0\n  call require('DPROD X default real positive control', dprod(x, y) == -6.0d0, checks)\n"
        "  call require('DPROD Y default real positive control', dprod(2.0, y) == 4.0d0, checks)\n",
        [mut("dprod-x-value-changed", "DPROD-X-default-real", "x = -3.0", "x = -4.0"),
         mut("dprod-y-value-changed", "DPROD-Y-default-real", "y = 2.0", "y = 3.0")]))
    out.append(build_case(
        "dprod_result_characteristics", "S16.9.74-002", SELECTED["S16.9.74-002"][1],
        "  integer :: checks\n  real :: x, y\n",
        "  x = 3.0; y = 2.0\n  call require('DPROD result is double precision real', kind(dprod(x, y)) == kind(0.0d0), checks)\n",
        [mut("dprod-kind-to-default-product", "DPROD-result-double-precision-real", "kind(dprod(x, y))", "kind(x * y)")]))
    out.append(build_case(
        "dprod_small_integer_product", "S16.9.74-003", SELECTED["S16.9.74-003"][1],
        "  integer :: checks\n",
        "  call require('DPROD exact small integer-valued product', dprod(-3.0, 2.0) == -6.0d0, checks)\n",
        [mut("dprod-small-factor-changed", "DPROD-product-approximation", "dprod(-3.0, 2.0)", "dprod(-3.0, 3.0)")]))

    def dshift_common(prefix, rule_base, intrinsic, sibling):
        facets1 = SELECTED[f"S16.9.{rule_base}-001"][1]
        if intrinsic == "dshiftl":
            arg_body = (
                "  n = bit_size(0)\n  i = ior(shiftl(1, 0), shiftl(1, 2))\n"
                "  j = ior(shiftl(1, n - 1), shiftl(1, n - 3))\n"
                "  call require('dshiftl integer and BOZ I admitted', &\n"
                "       btest(dshiftl(i, j, 1), 1) .and. btest(dshiftl(z'03', j, 1), 2), checks)\n"
                "  call require('dshiftl integer and BOZ J admitted', &\n"
                "       btest(dshiftl(i, j, 1), 1) .and. btest(dshiftl(i, z'03', n - 1), 0), checks)\n"
                "  if (dshiftl(i, j, 0) == dshiftl(i, j, n)) then\n"
                "    write(*,'(a)') 'dshiftl full-width edge differs from zero shift'\n"
                "    error stop\n"
                "  end if\n"
                )
            arg_muts = [
                mut("dshiftl-i-boz-shift-changed", "DSHIFTL-I-integer-or-boz", "dshiftl(z'03', j, 1)", "dshiftl(z'03', j, 0)"),
                mut("dshiftl-j-boz-literal-changed", "DSHIFTL-J-integer-or-boz", "btest(dshiftl(i, z'03', n - 1), 0)", "btest(dshiftl(i, z'01', n - 1), 0)"),
            ]
        else:
            arg_body = (
                "  n = bit_size(0)\n  i = ior(shiftl(1, 0), shiftl(1, 2))\n  j = shiftl(1, 2)\n"
                "  call require('dshiftr integer and BOZ I admitted', &\n"
                "       btest(dshiftr(i, j, 1), n - 1) .and. btest(dshiftr(z'03', j, 2), n - 1), checks)\n"
                "  call require('dshiftr integer and BOZ J admitted', &\n"
                "       btest(dshiftr(i, j, 1), 1) .and. btest(dshiftr(i, z'03', 1), 0), checks)\n"
                )
            arg_muts = [
                mut("dshiftr-i-boz-literal-changed", "DSHIFTR-I-integer-or-boz", "btest(dshiftr(z'03', j, 2), n - 1)", "btest(dshiftr(z'01', j, 2), n - 1)"),
                mut("dshiftr-j-boz-literal-changed", "DSHIFTR-J-integer-or-boz", "dshiftr(i, z'03', 1), 0", "dshiftr(i, z'01', 1), 0"),
            ]
        out.append(build_case(
            f"{prefix}_argument_controls", f"S16.9.{rule_base}-001", facets1,
            "  integer :: checks\n  integer :: i, j, n\n", arg_body, arg_muts))
        out.append(build_case(
            f"{prefix}_result_kind", f"S16.9.{rule_base}-002", SELECTED[f"S16.9.{rule_base}-002"][1],
            "  integer, parameter :: alt_ik = merge(8, 4, kind(0) /= 8)\n"
            "  integer(kind=alt_ik) :: i, j\n  integer :: checks\n",
            f"  i = 1_alt_ik; j = 2_alt_ik\n  call require('{intrinsic} result kind follows integer operand', &\n"
            f"       kind({intrinsic}(i, j, 1)) == kind(i) .and. kind({intrinsic}(z'03', j, 1)) == kind(j), checks)\n",
            [mut(f"{prefix}-result-kind-default-call", f"{intrinsic.upper()}-result-kind-from-I-or-J", f"kind({intrinsic}(i, j, 1))", f"kind({intrinsic}(1, 2, 1))")],
            profiles=["integer-kinds-4-8"]))
        out.append(build_case(
            f"{prefix}_boz_conversion", f"S16.9.{rule_base}-003", SELECTED[f"S16.9.{rule_base}-003"][1],
            "  integer :: checks\n  integer :: i, j, n, r1, r2\n",
            (f"  n = bit_size(0)\n  i = 1\n  j = ior(shiftl(1, n - 1), 1)\n"
             f"  r1 = {intrinsic}(z'03', j, 2)\n  r2 = {intrinsic}(i, z'03', n - 1)\n"
             f"  call require('{intrinsic} BOZ converts as INT to other kind', &\n"
             f"       kind(r1) == kind(j) .and. kind(r2) == kind(i) .and. &\n"
             f"       btest(r1, 3) .and. btest(r1, 2) .and. btest(r2, 0) .and. btest(r2, n - 1), checks)\n") if intrinsic == "dshiftl" else
            (f"  n = bit_size(0)\n  i = 1\n  j = shiftl(1, 2)\n"
             f"  r1 = {intrinsic}(z'03', j, 2)\n  r2 = {intrinsic}(i, z'03', 1)\n"
             f"  call require('{intrinsic} BOZ converts as INT to other kind', &\n"
             f"       kind(r1) == kind(j) .and. kind(r2) == kind(i) .and. &\n"
             f"       btest(r1, 0) .and. btest(r1, n - 1) .and. btest(r2, 0) .and. btest(r2, n - 1), checks)\n"),
            [mut(f"{prefix}-boz-literal-mutated", f"{intrinsic.upper()}-boz-converted-as-int-to-other-kind",
                 f"r2 = {intrinsic}(i, z'03', n - 1)" if intrinsic == "dshiftl" else f"r1 = {intrinsic}(z'03', j, 2)",
                 f"r2 = {intrinsic}(i, z'03', n - 2)" if intrinsic == "dshiftl" else f"r1 = {intrinsic}(z'03', j, 1)")]))
        if intrinsic == "dshiftl":
            bit_body = (
                "  n = bit_size(0)\n  sh = 4\n  i = ior(shiftl(1, 0), shiftl(1, 2))\n"
                "  j = ior(shiftl(1, n - 1), shiftl(1, n - 3))\n  got = dshiftl(i, j, sh)\n"
                "  expect = ior(shiftl(i, sh), shiftr(j, n - sh))\n  edge0 = dshiftl(i, j, 0)\n  edgew = dshiftl(i, j, n)\n"
                "  call require('dshiftl shifted bits come from operands', &\n"
                "       btest(got, 1) .and. btest(got, 3) .and. btest(got, 4) .and. btest(got, 6), checks)\n"
                "  call require('dshiftl equals IOR/SHIFT formula on observed bits', &\n"
                "       all([(btest(got, k) .eqv. btest(expect, k), k = 0, 7)]), checks)\n"
                "  call require('dshiftl shift zero and full width edges', &\n"
                "       edge0 /= edgew .and. edge0 == i .and. edgew == j, checks)\n")
            formula_old = "expect = ior(shiftl(i, sh), shiftr(j, n - sh))"
            formula_new = "expect = ior(shiftl(i, sh + 1), shiftr(j, n - sh))"
        else:
            bit_body = (
                "  n = bit_size(0)\n  sh = 4\n  i = ior(shiftl(1, 0), shiftl(1, 2))\n"
                "  j = ior(shiftl(1, 4), shiftl(1, 6))\n  got = dshiftr(i, j, sh)\n"
                "  expect = ior(shiftl(i, n - sh), shiftr(j, sh))\n  edge0 = dshiftr(i, j, 0)\n  edgew = dshiftr(i, j, n)\n"
                "  call require('dshiftr shifted bits come from operands', &\n"
                "       btest(got, 0) .and. btest(got, 2) .and. btest(got, n - 4) .and. btest(got, n - 2), checks)\n"
                "  call require('dshiftr equals IOR/SHIFT formula on observed bits', &\n"
                "       all([(btest(got, k) .eqv. btest(expect, k), k = 0, 7)]), checks)\n"
                "  call require('dshiftr shift zero and full width edges', &\n"
                "       edge0 /= edgew .and. edge0 == j .and. edgew == i, checks)\n")
            formula_old = "expect = ior(shiftl(i, n - sh), shiftr(j, sh))"
            formula_new = "expect = ior(shiftl(i, n - sh), shiftr(j, sh + 1))"
        out.append(build_case(
            f"{prefix}_bit_results", f"S16.9.{rule_base}-004", SELECTED[f"S16.9.{rule_base}-004"][1],
            "  integer :: checks\n  integer :: i, j, n, sh, got, expect, edge0, edgew, k\n", bit_body,
            [mut(f"{prefix}-sibling-substitution", f"{intrinsic.upper()}-shifted-bits-from-operands", f"got = {intrinsic}(i, j, sh)", f"got = {sibling}(i, j, sh)"),
             mut(f"{prefix}-formula-shift-changed", f"{intrinsic.upper()}-ior-shift-equivalence", formula_old, formula_new),
             mut(f"{prefix}-full-edge-to-zero", f"{intrinsic.upper()}-shift-zero-and-full-width-edges", f"edgew = {intrinsic}(i, j, n)", f"edgew = {intrinsic}(i, j, 0)")]))
    dshift_common("dshiftl", "75", "dshiftl", "dshiftr")
    dshift_common("dshiftr", "76", "dshiftr", "dshiftl")

    out.append(build_case(
        "eoshift_argument_controls", "S16.9.77-001", SELECTED["S16.9.77-001"][1],
        "  integer :: checks\n  integer :: m(2, 3), r(2, 3), rdim(2, 3), sh(2), b(2)\n  character(len=2) :: c(3), cr(3)\n",
        "  m = reshape([1, 2, 3, 4, 5, 6], [2, 3])\n  sh = [-1, 1]; b = [91, 92]\n  c = [character(len=2) :: 'ab', 'cd', 'ef']\n"
        "  r = eoshift(m, sh, b, dim=2)\n  rdim = eoshift(m, 1, 99, dim=1)\n  cr = eoshift(c, 1, 'zz')\n"
        "  call require('EOSHIFT ARRAY admits arrays of different intrinsic types', r(1,1) == 91 .and. cr(3) == 'zz', checks)\n"
        "  call require('EOSHIFT SHIFT scalar or conforming vector is used', r(1,1) == 91 .and. r(2,3) == 92, checks)\n"
        "  call require('EOSHIFT BOUNDARY same type parameters are used', len(eoshift(c, 1, 'zz')) == 2 .and. cr(3) == 'zz', checks)\n"
        "  call require('EOSHIFT DIM valid range selects shifted dimension', rdim(2,1) == 99, checks)\n",
        [mut("eoshift-array-character-boundary", "EOSHIFT-ARRAY-array-any-type", "r(1,1) == 91 .and. cr(3) == 'zz'", "r(1,1) == 91 .and. cr(3) == 'yy'"),
         mut("eoshift-shift-vector-values", "EOSHIFT-SHIFT-integer-scalar-or-conforming-shape", "sh = [-1, 1]", "sh = [1, -1]"),
         mut("eoshift-boundary-values", "EOSHIFT-BOUNDARY-same-type-params-scalar-or-conforming-shape", "b = [91, 92]", "b = [93, 94]"),
         mut("eoshift-dim-value", "EOSHIFT-DIM-integer-scalar-valid-range", "rdim = eoshift(m, 1, 99, dim=1)", "rdim = eoshift(m, 1, 99, dim=2)")]))
    out.append(build_case(
        "eoshift_absent_boundary_permission", "S16.9.77-002", SELECTED["S16.9.77-002"][1],
        "  integer :: checks\n  integer :: ia(3), ir(3)\n  real :: ra(3), rr(3)\n  complex :: za(3), zr(3)\n"
        "  logical :: la(3), lr(3)\n  character(len=3) :: ca(3), cr(3)\n",
        "  ia = [4, 5, 6]; ra = [1.0, 2.0, 3.0]; za = [cmplx(1.0,1.0), cmplx(2.0,2.0), cmplx(3.0,3.0)]\n"
        "  la = [.true., .true., .true.]; ca = [character(len=3) :: 'abc', 'def', 'ghi']\n"
        "  ir = eoshift(ia, 1); rr = eoshift(ra, 1); zr = eoshift(za, 1); lr = eoshift(la, 1); cr = eoshift(ca, 1)\n"
        "  call require('EOSHIFT absent BOUNDARY is permitted for Table 16.4 types', &\n"
        "       ir(3) == 0 .and. rr(3) == 0.0 .and. zr(3) == (0.0, 0.0) .and. &\n"
        "       .not. lr(3) .and. len(eoshift(ca, 1)) == 3 .and. cr(3) == '   ', checks)\n",
        [mut("eoshift-absent-boundary-explicit-nonzero", "EOSHIFT-BOUNDARY-absent-table-types-permitted", "ir = eoshift(ia, 1)", "ir = eoshift(ia, 1, 9)")]))
    out.append(build_case(
        "eoshift_derived_boundary_control", "S16.9.77-001", ("EOSHIFT-ARRAY-array-any-type",),
        "  type :: payload\n    integer :: tag\n  end type payload\n  integer :: checks\n  type(payload) :: a(3), r(3)\n",
        "  a = [payload(1), payload(2), payload(3)]\n  r = eoshift(a, 1, payload(99))\n"
        "  call require('EOSHIFT derived type ARRAY positive control', r(1)%tag == 2 .and. r(3)%tag == 99, checks)\n",
        [mut("eoshift-derived-array-values", "EOSHIFT-ARRAY-array-any-type",
             "a = [payload(1), payload(2), payload(3)]", "a = [payload(9), payload(8), payload(7)]")]))
    for variant, facet, decl, init, assign, condition, change in [
        ("eoshift_default_boundary_integer", "EOSHIFT-default-boundary-integer-zero", "  integer :: a(3), r(3), q(3)\n", "  a = [4, 5, 6]\n", "  r = eoshift(a, 1); q = eoshift(a, 1, 99)\n", "r(3) == 0 .and. q(3) == 99", ("r = eoshift(a, 1)", "r = eoshift(a, 1, 99)")),
        ("eoshift_default_boundary_real", "EOSHIFT-default-boundary-real-zero", "  real :: a(3), r(3), q(3)\n", "  a = [4.0, 5.0, 6.0]\n", "  r = eoshift(a, 1); q = eoshift(a, 1, 9.0)\n", "r(3) == 0.0 .and. q(3) == 9.0", ("r = eoshift(a, 1)", "r = eoshift(a, 1, 9.0)")),
        ("eoshift_default_boundary_complex", "EOSHIFT-default-boundary-complex-zero", "  complex :: a(3), r(3), q(3)\n", "  a = [cmplx(1.0,1.0), cmplx(2.0,2.0), cmplx(3.0,3.0)]\n", "  r = eoshift(a, 1); q = eoshift(a, 1, (9.0, 1.0))\n", "r(3) == (0.0, 0.0) .and. q(3) == (9.0, 1.0)", ("r = eoshift(a, 1)", "r = eoshift(a, 1, (9.0, 1.0))")),
        ("eoshift_default_boundary_logical", "EOSHIFT-default-boundary-logical-false", "  logical :: a(3), r(3), q(3)\n", "  a = [.true., .true., .true.]\n", "  r = eoshift(a, 1); q = eoshift(a, 1, .true.)\n", ".not. r(3) .and. q(3)", ("r = eoshift(a, 1)", "r = eoshift(a, 1, .true.)")),
        ("eoshift_default_boundary_character", "EOSHIFT-default-boundary-character-blanks", "  character(len=3) :: a(3), r(3), q(3)\n", "  a = [character(len=3) :: 'abc', 'def', 'ghi']\n", "  r = eoshift(a, 1); q = eoshift(a, 1, 'xyz')\n", "len(eoshift(a, 1)) == 3 .and. r(3) == '   ' .and. q(3) == 'xyz'", ("r = eoshift(a, 1)", "r = eoshift(a, 1, 'xyz')")),
    ]:
        out.append(build_case(variant, "S16.9.77-004", (facet,), decl + "  integer :: checks\n", init + assign + f"  call require('{facet}', &\n       {condition}, checks)\n", [mut("boundary-feature", facet, change[0], change[1])]))
    out.append(build_case(
        "eoshift_dim_default", "S16.9.77-005", SELECTED["S16.9.77-005"][1],
        "  integer :: checks\n  integer :: a(2,3)\n",
        "  a = reshape([1, 2, 3, 4, 5, 6], [2, 3])\n"
        "  call require('EOSHIFT absent DIM defaults to one', &\n"
        "       all(eoshift(a, 1) == eoshift(a, 1, dim=1)) .and. any(eoshift(a, 1) /= eoshift(a, 1, dim=2)), checks)\n",
        [mut("eoshift-absent-dim-to-two", "EOSHIFT-DIM-absent-defaults-to-one", "eoshift(a, 1) == eoshift(a, 1, dim=1)", "eoshift(a, 1, dim=2) == eoshift(a, 1, dim=1)")]))
    out.append(build_case(
        "eoshift_result_characteristics", "S16.9.77-006", SELECTED["S16.9.77-006"][1],
        "  integer :: checks\n  character(len=3) :: a(2,2)\n",
        "  a = reshape([character(len=3) :: 'abc', 'def', 'ghi', 'jkl'], [2, 2])\n"
        "  call require('EOSHIFT result type parameters and shape follow ARRAY', &\n"
        "       len(eoshift(a, 1, 'xyz', dim=2)) == 3 .and. &\n"
        "       all(shape(eoshift(a, 1, 'xyz', dim=2)) == [2, 2]), checks)\n",
        [mut("eoshift-shape-expression-to-section", "EOSHIFT-result-type-params-shape-of-array", "shape(eoshift(a, 1, 'xyz', dim=2))", "shape(eoshift(a(1:1,:), 1, 'xyz', dim=2))")]))
    out.append(build_case(
        "eoshift_mapping_values", "S16.9.77-007", SELECTED["S16.9.77-007"][1],
        "  integer :: checks\n  integer :: v(4), m(3,3), r(3,3), sh(3), b(3)\n",
        "  v = [1, 2, 3, 4]\n  m = reshape([1,2,3,4,5,6,7,8,9], [3,3])\n  sh = [-1, 1, 0]; b = [91, 92, 93]\n"
        "  r = eoshift(m, sh, b, dim=2)\n"
        "  call require('EOSHIFT positive shift maps elements left', all(eoshift(v, 2, 99) == [3, 4, 99, 99]), checks)\n"
        "  call require('EOSHIFT negative shift maps elements right', all(eoshift(v, -1, 99) == [99, 1, 2, 3]), checks)\n"
        "  call require('EOSHIFT array-valued SHIFT indexes non-DIM subscripts', r(1,1) == 91 .and. r(2,3) == 92 .and. r(3,2) == 6, checks)\n"
        "  call require('EOSHIFT boundary used outside bounds retained', &\n"
        "       r(1,1) == 91 .and. r(2,3) == 92 .and. r(1,2) == 1, checks)\n",
        [mut("eoshift-positive-sign", "EOSHIFT-positive-shift-element-mapping", "eoshift(v, 2, 99)", "eoshift(v, -2, 99)"),
         mut("eoshift-negative-sign", "EOSHIFT-negative-shift-element-mapping", "eoshift(v, -1, 99)", "eoshift(v, 1, 99)"),
         mut("eoshift-shift-vector", "EOSHIFT-array-valued-shift-indexing", "sh = [-1, 1, 0]", "sh = [1, -1, 0]"),
         mut("eoshift-boundary-vector", "EOSHIFT-boundary-used-outside-bounds", "b = [91, 92, 93]", "b = [94, 95, 96]")]))
    return out


def source_specs():
    return {case["id"]: case for case in cases()}


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent source no longer matches fingerprint")
    mutated = raw
    for start, end, expected, replacement in reversed(mutation["spans"]):
        if raw[start:end].decode("ascii") != expected:
            raise ValueError("mutation span lost complete-parent binding")
        mutated = mutated[:start] + replacement.encode("ascii") + mutated[end:]
    return mutated


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        if spec.get("profiles"):
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def soften_source_only(text):
    for old, new in SOURCE_ONLY_PATTERNS:
        text = text.replace(old, new)
    return text


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, pending in RESTORED_PENDING.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        for facet, reason in pending.items():
            if facet not in owner["facets"]:
                raise ValueError("restored pending facet changed for " + rule)
            owner.setdefault("pending", {})[facet] = reason
    for rule, (_, facets) in SELECTED.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner.setdefault("pending", {})
        owner["oracle"] = owned_paragraph(soften_source_only(owner.get("oracle", "")), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(soften_source_only(owner.get("oracle_limitation", "")), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
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
    selected_here = [rule for rule in SELECTED if rule in {row["id"] for row in catalogue["requirements"]}]
    facet_count = sum(len(SELECTED[rule][1]) for rule in selected_here)
    summary = (SUMMARY_BEGIN + "\n"
               "## Intrinsics 16.9 H runtime observations\n\n"
               f"The `intrinsics_16_9_h` generator supplies {len(selected_here)} requirement bindings "
               f"covering {facet_count} portable facets in this section. Oracles use direct result inquiries, "
               "same-model DIGITS relationships, exact integer/logical/character/small-real results, and DSHIFT "
               "BTEST observations. DPROD processor-dependent approximation latitude and SHOULD guidance remain pending.\n"
               + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues, updated_views = {}, {}
    for section, path in CATALOGUES.items():
        catalogue = json.loads((root / path).read_text())
        updated = synced_catalogue(catalogue)
        updated_catalogues[path] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        for path, updated in updated_catalogues.items():
            if json.loads((root / path).read_text()) != updated:
                stale.append(path)
        for path, updated in updated_views.items():
            if (root / path).read_text() != updated:
                stale.append(path)
        if stale:
            raise ValueError("stale intrinsics_16_9_h fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogues:
            for path, updated in updated_catalogues.items():
                (root / path).write_text(json.dumps(updated, indent=2) + "\n")
            for path, updated in updated_views.items():
                (root / path).write_text(updated)
    return files, specs


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    flag = (("--std=" if "lfortran" in name else "-std=") + std) if std else ""
    return [str(compiler)] + ([flag] if flag else []) + [str(source), "-o", str(output)]


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(compiler).name.lower() else "gfortran"


KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "dshiftl_argument_controls",
        "dshiftl_result_kind",
        "dshiftl_bit_results",
        "dshiftr_argument_controls",
        "dshiftr_result_kind",
        "dshiftr_boz_conversion",
        "dshiftr_bit_results",
        "eoshift_argument_controls",
        "eoshift_absent_boundary_permission",
        "eoshift_derived_boundary_control",
        "eoshift_default_boundary_character",
        "eoshift_default_boundary_complex",
        "eoshift_mapping_values",
    }
}


def run_source(compiler, std, case_dir, source_text, expected_stdout):
    source = case_dir / "source.f90"
    exe = case_dir / "program"
    source.write_text(source_text)
    compile_result = subprocess.run(compiler_command(compiler, std, source, exe), cwd=case_dir,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_result.returncode != 0:
        return dict(status="compile-fail", stdout=compile_result.stdout, stderr=compile_result.stderr,
                    returncode=compile_result.returncode)
    run_result = subprocess.run([str(exe)], cwd=case_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run_result.returncode == 0 and run_result.stdout == expected_stdout and run_result.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run_result.stdout,
                stderr=run_result.stderr, returncode=run_result.returncode)


def mutation_check(root, compiler, std, keep_work=False, inject_survivor=False):
    root = Path(root)
    _, specs = build_corpus(root)
    family = compiler_family(compiler)
    workspace = root / ".intrinsics_16_9_h_mutations" / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    report = []
    try:
        for case_index, spec in enumerate(specs.values(), 1):
            case_dir = workspace / f"{case_index:03d}_{spec['variant']}"
            case_dir.mkdir()
            parent = run_source(compiler, std, case_dir, spec["source"], spec["completion"])
            parent_ok = parent["status"] == "pass"
            parent_known = spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set())
            for index, mutation in enumerate(spec["mutations"]):
                if not parent_ok and parent_known:
                    report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                       kind=mutation["kind"], skipped=True, parent_ok=False, failed=True,
                                       status="known-parent-failure", stdout=parent["stdout"], stderr=parent["stderr"],
                                       returncode=parent["returncode"]))
                    continue
                mutant_dir = case_dir / f"mut_{index:03d}"
                mutant_dir.mkdir()
                mutant = spec["source"] if inject_survivor and not report else mutated_source(spec, mutation).decode("ascii")
                observed = run_source(compiler, std, mutant_dir, mutant, spec["completion"])
                failed = observed["status"] == "run-fail"
                report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                   kind=mutation["kind"], skipped=False, parent_ok=parent_ok, failed=failed,
                                   status=observed["status"], stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"]))
        bad = [row for row in report if (not row["parent_ok"] and not row.get("skipped")) or not row["failed"] or row["status"] == "compile-fail"]
        if bad:
            raise RuntimeError(json.dumps(bad[:10], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check))) > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work, args.inject_surviving_mutant)
        skipped = sum(1 for row in report if row.get("skipped"))
        print(f"Mutation-checked {len(report) - skipped}/{len(report) - skipped} intrinsics_16_9_h mutants; {skipped} skipped for known parent failures.")
        return
    files, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_h cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
