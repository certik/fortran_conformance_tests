#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.101-16.9.106 intrinsic fixtures."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_m"
SECTIONS = ("16.9.101", "16.9.102", "16.9.103", "16.9.104", "16.9.105", "16.9.106")
CATALOGUES = {
    "16.9.101": "doc/catalogues/iany_16_9_101.json",
    "16.9.102": "doc/catalogues/ibclr_16_9_102.json",
    "16.9.103": "doc/catalogues/ibits_16_9_103.json",
    "16.9.104": "doc/catalogues/ibset_16_9_104.json",
    "16.9.105": "doc/catalogues/ichar_intrinsic_16_9_105.json",
    "16.9.106": "doc/catalogues/ieor_intrinsic_16_9_106.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9 M FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9 M FIXTURES -->"
INTEGER_PROFILE = "integer-kinds-4-8"

SELECTED = {
    "S16.9.101-002": ("effect", ("IANY-result-type-kind-from-array", "IANY-result-scalar-without-dim-or-rank-one", "IANY-result-shape-removes-dim")),
    "S16.9.101-003": ("effect", ("IANY-bitwise-or-all-elements", "IANY-zero-size-identity-zero-bits")),
    "S16.9.101-004": ("effect", ("IANY-mask-pack-equivalence", "IANY-all-false-mask-uses-zero-identity")),
    "S16.9.101-005": ("effect", ("IANY-dim-rank-one-equals-whole-array", "IANY-dim-section-wise-reduction", "IANY-dim-mask-section-wise-reduction")),
    "S16.9.102-002": ("effect", ("IBCLR-result-same-kind-as-I",)),
    "S16.9.102-003": ("effect", ("IBCLR-clears-selected-bit", "IBCLR-preserves-other-observed-bits")),
    "S16.9.103-002": ("effect", ("IBITS-result-same-kind-as-I",)),
    "S16.9.103-003": ("effect", ("IBITS-extracted-bits-right-adjusted", "IBITS-other-result-bits-zero", "IBITS-zero-len-result-zero")),
    "S16.9.104-002": ("effect", ("IBSET-result-same-kind-as-I",)),
    "S16.9.104-003": ("effect", ("IBSET-sets-selected-bit", "IBSET-preserves-other-observed-bits")),
    "S16.9.105-002": ("effect", ("ICHAR-result-integer-kind-from-KIND", "ICHAR-result-default-integer-kind-without-KIND")),
    "S16.9.105-003": ("effect", ("ICHAR-CHAR-index-round-trip-guaranteed-range",)),
    "S16.9.105-004": ("effect", ("ICHAR-result-nonnegative",)),
    "S16.9.105-005": ("effect", ("ICHAR-order-consistent-with-character-le", "ICHAR-equality-consistent-with-character-equality")),
    "S16.9.106-002": ("effect", ("IEOR-result-kind-from-I-or-J",)),
    "S16.9.106-003": ("effect", ("IEOR-boz-converted-as-int-to-other-kind",)),
    "S16.9.106-004": ("effect", ("IEOR-exclusive-or-truth-table", "IEOR-negative-operand-bit-pattern")),
}

REMAINING_PENDING = {
    "S16.9.101-001": {
        "IANY-ARRAY-integer-array": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; conforming positive controls do not discharge it and no diagnostic is required.",
        "IANY-DIM-integer-scalar-valid-range": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; conforming DIM calls do not discharge invalid DIM values and no diagnostic is required.",
        "IANY-MASK-logical-conformable": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; conforming MASK calls do not discharge nonconforming masks and no diagnostic is required.",
    },
    "S16.9.102-001": {
        "IBCLR-I-integer": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IBCLR-POS-integer": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IBCLR-POS-nonnegative": "Left pending by intrinsics_16_9_m: unnumbered range restriction; boundary positive controls do not discharge invalid POS values.",
        "IBCLR-POS-less-than-bit-size": "Left pending by intrinsics_16_9_m: unnumbered range restriction; boundary positive controls do not discharge invalid POS values.",
    },
    "S16.9.103-001": {
        "IBITS-I-integer": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IBITS-POS-integer-nonnegative": "Left pending by intrinsics_16_9_m: unnumbered argument/range restriction; no portable diagnostic facet is claimed.",
        "IBITS-LEN-integer-nonnegative": "Left pending by intrinsics_16_9_m: unnumbered argument/range restriction; no portable diagnostic facet is claimed.",
        "IBITS-POS-plus-LEN-in-range": "Left pending by intrinsics_16_9_m: unnumbered range restriction; high-edge positive controls do not discharge invalid POS+LEN values.",
    },
    "S16.9.104-001": {
        "IBSET-I-integer": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IBSET-POS-integer": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IBSET-POS-nonnegative": "Left pending by intrinsics_16_9_m: unnumbered range restriction; boundary positive controls do not discharge invalid POS values.",
        "IBSET-POS-less-than-bit-size": "Left pending by intrinsics_16_9_m: unnumbered range restriction; boundary positive controls do not discharge invalid POS values.",
    },
    "S16.9.105-001": {
        "ICHAR-C-character-length-one-representable": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; conforming one-character controls do not discharge invalid C values.",
        "ICHAR-KIND-scalar-integer-constant-expression": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no diagnostic facet is claimed.",
    },
    "S16.9.105-003": {
        "ICHAR-arbitrary-character-position-processor-dependent": "Left pending by intrinsics_16_9_m: p5 makes native absolute positions processor-collating-sequence dependent; no fixed numeric oracle is portable.",
    },
    "S16.9.105-004": {
        "ICHAR-result-less-than-collating-sequence-size": "Left pending by intrinsics_16_9_m: the processor collating-sequence size n is not exposed by a portable single-image inquiry.",
        "ICHAR-result-kind-represents-sequence-size": "Left pending by intrinsics_16_9_m: proving a requested kind represents the complete processor character set needs an independent profile of n.",
    },
    "S16.9.106-001": {
        "IEOR-I-integer-or-boz": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IEOR-J-integer-or-boz": "Left pending by intrinsics_16_9_m: unnumbered argument shall-restriction; no portable diagnostic facet is claimed.",
        "IEOR-integer-kinds-match": "Left pending by intrinsics_16_9_m: unnumbered same-kind restriction; positive controls do not discharge mismatched-kind programs.",
        "IEOR-not-both-boz": "Left pending by intrinsics_16_9_m: unnumbered not-both-BOZ restriction; no diagnostic facet is claimed.",
    },
}

ORACLE_PREFIXES = {rule: f"{rule} intrinsics_16_9_m runtime fixture: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} intrinsics_16_9_m fixture boundaries: " for rule in SELECTED}
ORACLES = {
    rule: ORACLE_PREFIXES[rule] + "Generated fixtures check only source-stated exact properties: direct KIND/SHAPE inquiries on intrinsic expressions, exact low-bit BTEST/POPCNT observations, CHAR/ICHAR inverse positions, and IEOR truth-table bits."
    for rule in SELECTED
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + "Only the listed single-image portable facets are discharged. Unnumbered argument restrictions remain pending without diagnostic claims; processor-dependent native character positions and unexposed collating-sequence size are not asserted."
    for rule in SELECTED
}
SOURCE_ONLY_PATTERNS = [
    ("Source accounting only. This packet creates no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.",
     "Original source accounting created no Fortran fixture, compiler invocation, execution evidence link, fixture approval, oracle approval, or coverage claim; this intrinsics_16_9_m generator supplies selected runtime fixtures and mutation plans without universal coverage."),
    ("Source registration only.", "Original source registration only; selected facets now have bounded runtime fixtures and mutation plans."),
]

HELPERS = """  subroutine require(label, condition, checks)
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

TYPE_CODE_HELPERS = """  integer function code_integer(x)
    integer, intent(in) :: x
    code_integer = 1
  end function code_integer
  integer function code_integer_alt(x)
    integer(kind=ik), intent(in) :: x
    code_integer_alt = 1
  end function code_integer_alt
  integer function code_real(x)
    real, intent(in) :: x
    code_real = 2
  end function code_real
"""


def identifier(variant, rule):
    return rule.replace('.', '_').replace('-', '_') + f"_valid__{TOPIC}_{variant}"


def mut(mid, facet, expected, replacement, category="feature"):
    return {"id": mid, "facet": facet, "kind": "source", "category": category,
            "replacements": [{"expected": expected, "replacement": replacement}]}


def header(rule, facets, name):
    return "\n".join([f"! rule: {rule}"] + [f"! covers: {facet}" for facet in facets]) + f"\nprogram {name}\n  implicit none\n"


def finish(name, completion, checks, extra_helpers=""):
    return f"  if (checks /= {checks}) error stop\n  write(*,'(a)') '{completion.rstrip()}'\ncontains\n" + extra_helpers + HELPERS.format(name=name)


def make_source(variant, rule, facets, declarations, body, extra_helpers=""):
    name = "i169m_" + variant
    completion = "INTRINSICS 16.9 M " + variant.upper().replace("_", " ") + " OK\n"
    return header(rule, facets, name) + declarations + "  checks = 0\n" + body + finish(name, completion, len(facets), extra_helpers), completion


def build_case(variant, rule, facets, declarations, body, mutations, profiles=(), extra_helpers=""):
    evidence = SELECTED[rule][0]
    source, completion = make_source(variant, rule, facets, declarations, body, extra_helpers)
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
    if {m["facet"] for m in materialized} != set(facets):
        raise ValueError(f"{variant} lacks one mutation for each facet")
    return dict(id=identifier(variant, rule), variant=variant, rule=rule, facets=list(facets), evidence=evidence,
                source=source, source_sha256=sha(raw), completion=completion, mutations=materialized,
                profiles=list(profiles))


def cases():
    out = []
    out.append(build_case(
        "iany_result_kind", "S16.9.101-002", ("IANY-result-type-kind-from-array",),
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer(kind=ik) :: wide(3)\n  integer :: checks\n",
        "  wide = [1_ik, 3_ik, 4_ik]\n"
        "  call require('IANY result kind follows integer ARRAY kind', kind(iany(wide)) == ik, checks)\n",
        [mut("array-kind-to-default", "IANY-result-type-kind-from-array", "kind(iany(wide)) == ik", "kind(iany(int(wide))) == ik")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "iany_scalar_result", "S16.9.101-002", ("IANY-result-scalar-without-dim-or-rank-one",),
        "  integer :: checks\n",
        "  call require('IANY result scalar without DIM or rank one DIM', &\n"
        "       size(shape(iany([1, 2, 4]))) == 0 .and. size(shape(iany([1, 2, 4], dim=1))) == 0, checks)\n",
        [mut("rank-one-scalar-wrapped", "IANY-result-scalar-without-dim-or-rank-one", "size(shape(iany([1, 2, 4], dim=1))) == 0", "size(shape([iany([1, 2, 4], dim=1)])) == 0")]))
    out.append(build_case(
        "iany_dim_shape", "S16.9.101-002", ("IANY-result-shape-removes-dim",),
        "  integer :: grid(2,3), checks\n",
        "  grid = reshape([1, 2, 4, 8, 16, 32], [2, 3])\n"
        "  call require('IANY DIM shape removes selected extent', &\n"
        "       all(shape(iany(grid, dim=1)) == [3]) .and. all(shape(iany(grid, dim=2)) == [2]), checks)\n",
        [mut("dim-shape-sibling", "IANY-result-shape-removes-dim", "shape(iany(grid, dim=1)) == [3]", "shape(iany(grid, dim=2)) == [3]")]))
    out.append(build_case(
        "iany_whole_array", "S16.9.101-003", SELECTED["S16.9.101-003"][1],
        "  integer :: a(3), zero(0), r, checks\n",
        "  a = [1, 3, 4]\n  r = iany(a)\n"
        "  call require('IANY whole array is bitwise OR of elements', &\n"
        "       btest(r, 0) .and. btest(r, 1) .and. btest(r, 2) .and. popcnt(r) == 3, checks)\n"
        "  call require('IANY zero-size array gives zero bits', &\n"
        "       popcnt(iany(zero)) == 0 .and. popcnt(iany(a)) /= 0, checks)\n",
        [mut("iany-to-iparity", "IANY-bitwise-or-all-elements", "r = iany(a)", "r = iparity(a)"),
         mut("zero-size-to-nonzero", "IANY-zero-size-identity-zero-bits", "popcnt(iany(zero)) == 0", "popcnt(iany([1])) == 0")]))
    out.append(build_case(
        "iany_mask", "S16.9.101-004", SELECTED["S16.9.101-004"][1],
        "  integer :: arr(4), checks\n  logical :: mask(4), false_mask(4)\n",
        "  arr = [3, 8, 1, 4]\n  mask = [.true., .false., .true., .false.]\n  false_mask = .false.\n"
        "  call require('IANY MASK is equivalent to PACK selection', &\n"
        "       iany(arr, mask=mask) == iany(pack(arr, mask)) .and. btest(iany(arr, mask=mask), 0), checks)\n"
        "  call require('IANY all-false MASK uses zero identity', &\n"
        "       popcnt(iany(arr, mask=false_mask)) == 0 .and. popcnt(iany(arr, mask=mask)) /= 0, checks)\n",
        [mut("mask-iany-to-iparity", "IANY-mask-pack-equivalence", "iany(arr, mask=mask) == iany(pack(arr, mask))", "iparity(arr, mask=mask) == iany(pack(arr, mask))"),
         mut("false-mask-to-selected", "IANY-all-false-mask-uses-zero-identity", "popcnt(iany(arr, mask=false_mask)) == 0", "popcnt(iany(arr, mask=mask)) == 0")]))
    out.append(build_case(
        "iany_dim", "S16.9.101-005", SELECTED["S16.9.101-005"][1],
        "  integer :: vec(3), grid(2,2), r1, rdim1(2), rdim2(2), rmask(2), checks\n"
        "  logical :: m2(2,2)\n",
        "  vec = [3, 1, 4]\n  r1 = iany(vec, dim=1)\n"
        "  call require('IANY rank-one DIM equals whole-array form', r1 == iany(vec) .and. btest(r1, 0), checks)\n"
        "  grid = reshape([3, 1, 6, 3], [2, 2])\n  rdim1 = iany(grid, dim=1)\n  rdim2 = iany(grid, dim=2)\n"
        "  call require('IANY DIM reduces each selected section', &\n"
        "       all(rdim1 == [3, 7]) .and. all(rdim2 == [7, 3]), checks)\n"
        "  m2 = reshape([.true., .true., .true., .false.], [2, 2])\n  rmask = iany(grid, dim=1, mask=m2)\n"
        "  call require('IANY DIM with MASK reduces corresponding sections', &\n"
        "       all(rmask == [3, 6]) .and. iany(pack(grid(:,2), m2(:,2))) == 6, checks)\n",
        [mut("rank-one-to-iparity", "IANY-dim-rank-one-equals-whole-array", "r1 = iany(vec, dim=1)", "r1 = iparity(vec, dim=1)"),
         mut("dim-sections-to-iparity", "IANY-dim-section-wise-reduction", "rdim1 = iany(grid, dim=1)", "rdim1 = iparity(grid, dim=1)"),
         mut("dim-mask-to-iparity", "IANY-dim-mask-section-wise-reduction", "rmask = iany(grid, dim=1, mask=m2)", "rmask = iparity(grid, dim=1, mask=m2)")]))
    out.append(build_case(
        "ibclr_kind", "S16.9.102-002", SELECTED["S16.9.102-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('IBCLR result has same kind as I', kind(ibclr(7_ik, 1)) == ik, checks)\n",
        [mut("kind-to-default", "IBCLR-result-same-kind-as-I", "kind(ibclr(7_ik, 1)) == ik", "kind(ibclr(7, 1)) == ik")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "ibclr_bits", "S16.9.102-003", SELECTED["S16.9.102-003"][1],
        "  integer :: seed, r, z, checks\n",
        "  z = bit_size(0)\n  seed = 0\n  seed = ibset(seed, 0)\n  seed = ibset(seed, 1)\n"
        "  seed = ibset(seed, 3)\n  seed = ibset(seed, z - 1)\n  r = ibclr(seed, 1)\n"
        "  call require('IBCLR clears selected bit', .not. btest(r, 1), checks)\n"
        "  call require('IBCLR preserves other observed bits', &\n"
        "       btest(r, 0) .and. btest(r, 3) .and. btest(r, z - 1) .and. .not. btest(r, 2), checks)\n",
        [mut("clear-to-set", "IBCLR-clears-selected-bit", "r = ibclr(seed, 1)", "r = ibset(seed, 1)"),
         mut("clear-other-position", "IBCLR-preserves-other-observed-bits", "r = ibclr(seed, 1)", "r = ibclr(seed, 3)")]))
    out.append(build_case(
        "ibits_kind", "S16.9.103-002", SELECTED["S16.9.103-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('IBITS result has same kind as I', kind(ibits(7_ik, 1, 2)) == ik, checks)\n",
        [mut("kind-to-default", "IBITS-result-same-kind-as-I", "kind(ibits(7_ik, 1, 2)) == ik", "kind(ibits(7, 1, 2)) == ik")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "ibits_bits", "S16.9.103-003", SELECTED["S16.9.103-003"][1],
        "  integer :: seed, r, zlen, z, checks\n",
        "  z = bit_size(0)\n  seed = 0\n  seed = ibset(seed, 2)\n  seed = ibset(seed, 4)\n  seed = ibset(seed, 5)\n"
        "  r = ibits(seed, 2, 3)\n  zlen = ibits(seed, 2, 0)\n"
        "  call require('IBITS extracts LEN bits right-adjusted', &\n"
        "       btest(r, 0) .and. .not. btest(r, 1) .and. btest(r, 2) .and. &\n"
        "       ibits(ibset(0, z - 1), z - 1, 1) == 1, checks)\n"
        "  call require('IBITS zeros every other result bit', popcnt(r) == 2 .and. .not. btest(r, 3), checks)\n"
        "  call require('IBITS zero LEN gives zero with nonzero companion', popcnt(zlen) == 0 .and. popcnt(r) == 2, checks)\n",
        [mut("shift-pos", "IBITS-extracted-bits-right-adjusted", "r = ibits(seed, 2, 3)", "r = ibits(seed, 3, 3)"),
         mut("extend-len", "IBITS-other-result-bits-zero", "r = ibits(seed, 2, 3)", "r = ibits(seed, 2, 4)"),
         mut("zero-len-to-three", "IBITS-zero-len-result-zero", "zlen = ibits(seed, 2, 0)", "zlen = ibits(seed, 2, 3)")]))
    out.append(build_case(
        "ibset_kind", "S16.9.104-002", SELECTED["S16.9.104-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('IBSET result has same kind as I', kind(ibset(7_ik, 1)) == ik, checks)\n",
        [mut("kind-to-default", "IBSET-result-same-kind-as-I", "kind(ibset(7_ik, 1)) == ik", "kind(ibset(7, 1)) == ik")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "ibset_bits", "S16.9.104-003", SELECTED["S16.9.104-003"][1],
        "  integer :: seed, r, z, checks\n",
        "  z = bit_size(0)\n  seed = 0\n  seed = ibset(seed, 0)\n  seed = ibset(seed, 3)\n"
        "  seed = ibset(seed, z - 1)\n  r = ibset(seed, 1)\n"
        "  call require('IBSET sets selected bit', btest(r, 1), checks)\n"
        "  call require('IBSET preserves other observed bits', &\n"
        "       btest(r, 0) .and. btest(r, 3) .and. btest(r, z - 1) .and. .not. btest(r, 2), checks)\n",
        [mut("set-to-clear", "IBSET-sets-selected-bit", "r = ibset(seed, 1)", "r = ibclr(seed, 1)"),
         mut("set-other-position", "IBSET-preserves-other-observed-bits", "r = ibset(seed, 1)", "r = ibset(seed, 2)")]))
    out.append(build_case(
        "ichar_kinds", "S16.9.105-002", SELECTED["S16.9.105-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('ICHAR present KIND selects integer result kind', kind(ichar('A', kind=ik)) == ik, checks)\n"
        "  call require('ICHAR absent KIND gives default integer kind', kind(ichar('A')) == kind(0), checks)\n",
        [mut("remove-kind", "ICHAR-result-integer-kind-from-KIND", "kind(ichar('A', kind=ik)) == ik", "kind(ichar('A')) == ik"),
         mut("add-nondefault-kind", "ICHAR-result-default-integer-kind-without-KIND", "kind(ichar('A')) == kind(0)", "kind(ichar('A', kind=ik)) == kind(0)")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "ichar_roundtrip", "S16.9.105-003", SELECTED["S16.9.105-003"][1],
        "  integer :: checks\n",
        "  call require('ICHAR CHAR index round trip for guaranteed range', &\n"
        "       ichar(char(0)) == 0 .and. ichar(char(32)) == 32 .and. ichar(char(65)) == 65, checks)\n",
        [mut("roundtrip-index", "ICHAR-CHAR-index-round-trip-guaranteed-range", "ichar(char(65)) == 65", "ichar(char(64)) == 65")]))
    out.append(build_case(
        "ichar_nonnegative", "S16.9.105-004", SELECTED["S16.9.105-004"][1],
        "  integer :: checks\n",
        "  call require('ICHAR result is nonnegative for representable character', &\n"
        "       ichar(char(1)) > 0 .and. ichar('A') >= 0 .and. ichar('0') >= 0 .and. ichar(' ') >= 0, checks)\n",
        [mut("positive-char-to-zero", "ICHAR-result-nonnegative", "ichar(char(1)) > 0", "ichar(char(0)) > 0")]))
    out.append(build_case(
        "ichar_order_equality", "S16.9.105-005", SELECTED["S16.9.105-005"][1],
        "  character(len=1) :: c10, c11, c12, c13\n  integer :: checks\n",
        "  c10 = char(10)\n  c11 = char(11)\n  c12 = char(12)\n  c13 = char(13)\n"
        "  call require('ICHAR order agrees with character comparison', c10 <= c11 .and. ichar(c10) <= ichar(c11), checks)\n"
        "  call require('ICHAR equality agrees with character equality', &\n"
        "       c12 == char(12) .and. ichar(c12) == ichar(char(12)) .and. c12 /= c13 .and. ichar(c12) /= ichar(c13), checks)\n",
        [mut("ordered-char-swapped", "ICHAR-order-consistent-with-character-le", "c11 = char(11)", "c11 = char(9)"),
         mut("distinct-char-equalized", "ICHAR-equality-consistent-with-character-equality", "c13 = char(13)", "c13 = char(12)")]))
    out.append(build_case(
        "ieor_kind", "S16.9.106-002", SELECTED["S16.9.106-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('IEOR result kind follows non-BOZ integer operand', &\n"
        "       kind(ieor(z'01', 3_ik)) == ik .and. kind(ieor(3_ik, z'01')) == ik, checks)\n",
        [mut("boz-other-kind-default", "IEOR-result-kind-from-I-or-J", "kind(ieor(z'01', 3_ik)) == ik", "kind(ieor(z'01', 3)) == ik")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "ieor_boz", "S16.9.106-003", SELECTED["S16.9.106-003"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer(kind=ik) :: left, right, expect\n  integer :: checks\n",
        "  left = ieor(z'0F', 10_ik)\n  right = ieor(10_ik, z'0F')\n  expect = ieor(int(z'0F', kind=ik), 10_ik)\n"
        "  call require('IEOR BOZ operand is converted as INT to other kind', &\n"
        "       left == expect .and. right == expect .and. btest(left, 0) .and. btest(left, 2), checks)\n",
        [mut("boz-literal-changed", "IEOR-boz-converted-as-int-to-other-kind", "left = ieor(z'0F', 10_ik)", "left = ieor(z'03', 10_ik)")],
        profiles=[INTEGER_PROFILE]))
    out.append(build_case(
        "ieor_bit_results", "S16.9.106-004", SELECTED["S16.9.106-004"][1],
        "  integer :: pos, checks\n  logical :: all_ones, all_zero\n",
        "  call require('IEOR exclusive OR truth table bits', &\n"
        "       btest(ieor(1, 0), 0) .and. btest(ieor(0, 2), 1) .and. &\n"
        "       .not. btest(ieor(1, 1), 0) .and. .not. btest(ieor(0, 0), 0) .and. ieor(1, 3) == 2, checks)\n"
        "  all_ones = .true.\n  all_zero = .true.\n  do pos = 0, bit_size(0) - 1\n"
        "    all_ones = all_ones .and. (btest(ieor(-1, 0), pos) .eqv. btest(-1, pos))\n"
        "    all_zero = all_zero .and. .not. btest(ieor(-1, -1), pos)\n  end do\n"
        "  call require('IEOR negative operand bit patterns are combined bitwise', all_ones .and. all_zero, checks)\n",
        [mut("truth-table-to-ior", "IEOR-exclusive-or-truth-table", "ieor(1, 3) == 2", "ior(1, 3) == 2"),
         mut("negative-equal-to-ior", "IEOR-negative-operand-bit-pattern", "btest(ieor(-1, -1), pos)", "btest(ior(-1, -1), pos)")]))
    return out


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for spec in cases():
        directory = root / "tests" / "fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=spec["completion"], stderr=""))
        if spec.get("profiles"):
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        specs[spec["id"]] = spec
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def softened(text):
    for old, new in SOURCE_ONLY_PATTERNS:
        text = text.replace(old, new)
    return text


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, pending in REMAINING_PENDING.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        for facet, reason in pending.items():
            if facet not in owner["facets"]:
                raise ValueError("remaining pending facet changed for " + rule)
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
        owner["oracle"] = owned_paragraph(softened(owner.get("oracle", "")), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(softened(owner.get("oracle_limitation", "")), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
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
               "## Intrinsics 16.9 M runtime observations\n\n"
               f"The `intrinsics_16_9_m` generator supplies {len(selected_here)} requirement bindings "
               f"covering {facet_count} portable facets in this section. Oracles use direct result inquiries, "
               "bit-context observations with BTEST/POPCNT, CHAR/ICHAR inverse positions, and exact IEOR truth-table bits. "
               "Unnumbered argument restrictions and processor-dependent native character positions remain pending.\n"
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
            raise ValueError("stale intrinsics_16_9_m fixtures: " + ", ".join(stale))
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


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["id"])
    mutant = raw
    for start, end, old, new in reversed(mutation["spans"]):
        if raw[start:end].decode("ascii") != old:
            raise ValueError("mutation span lost parent binding")
        mutant = mutant[:start] + new.encode("ascii") + mutant[end:]
    return mutant


KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "iany_dim_shape",
        "iany_mask",
        "iany_dim",
        "ieor_kind",
        "ieor_boz",
    }
}


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(compiler).name.lower() else "gfortran"

def compiler_command(compiler, std, source, output):
    flag = (("--std=" if "lfortran" in Path(compiler).name.lower() else "-std=") + std) if std else ""
    return [str(compiler)] + ([flag] if flag else []) + [str(source), "-o", str(output)]


def run_source(compiler, std, case_dir, source_text, expected_stdout):
    source = case_dir / "source.f90"
    exe = case_dir / "program"
    source.write_text(source_text)
    comp = subprocess.run(compiler_command(compiler, std, source, exe), cwd=case_dir,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if comp.returncode != 0:
        return dict(status="compile-fail", stdout=comp.stdout, stderr=comp.stderr, returncode=comp.returncode)
    run = subprocess.run([str(exe)], cwd=case_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run.returncode == 0 and run.stdout == expected_stdout and run.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr, returncode=run.returncode)


def mutation_check(root, compiler, std, keep_work=False, inject_survivor=False):
    root = Path(root)
    _, specs = build_corpus(root)
    workspace = root / ".intrinsics_16_9_m_mutations" / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    report = []
    try:
        for case_index, spec in enumerate(specs.values(), 1):
            case_dir = workspace / f"{case_index:03d}_{spec['variant']}"
            case_dir.mkdir()
            parent = run_source(compiler, std, case_dir, spec["source"], spec["completion"])
            family = compiler_family(compiler)
            parent_known = spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set())
            if parent["status"] != "pass" and not parent_known:
                raise RuntimeError(json.dumps(dict(parent=spec["variant"], result=parent), indent=2))
            for index, mutation in enumerate(spec["mutations"]):
                if parent["status"] != "pass" and parent_known:
                    report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                       failed=True, skipped=True, status="known-parent-failure",
                                       stdout=parent["stdout"], stderr=parent["stderr"], returncode=parent["returncode"]))
                    continue
                mutant_dir = case_dir / f"mut_{index:03d}"
                mutant_dir.mkdir()
                source = spec["source"] if inject_survivor and not report else mutated_source(spec, mutation).decode("ascii")
                observed = run_source(compiler, std, mutant_dir, source, spec["completion"])
                failed = observed["status"] == "run-fail"
                row = dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                           failed=failed, skipped=False, status=observed["status"], stdout=observed["stdout"],
                           stderr=observed["stderr"], returncode=observed["returncode"])
                report.append(row)
        bad = [row for row in report if not row["failed"] or row["status"] == "compile-fail"]
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
        print(f"Mutation-checked {len(report) - skipped}/{len(report) - skipped} intrinsics_16_9_m mutants; {skipped} skipped for known parent failures.")
        return
    files, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_m cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
