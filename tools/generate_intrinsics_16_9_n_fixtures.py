#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.109 through 16.9.113."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_n"
SECTIONS = ("16.9.109", "16.9.110", "16.9.111", "16.9.112", "16.9.113")
CATALOGUES = {
    "16.9.109": "doc/catalogues/index_intrinsic_16_9_109.json",
    "16.9.110": "doc/catalogues/int_intrinsic_16_9_110.json",
    "16.9.111": "doc/catalogues/ior_intrinsic_16_9_111.json",
    "16.9.112": "doc/catalogues/iparity_16_9_112.json",
    "16.9.113": "doc/catalogues/ishft_16_9_113.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9 N FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9 N FIXTURES -->"

SELECTED = {
    "S16.9.109-002": ("effect", ("INDEX-integer-result", "INDEX-kind-present-result-kind", "INDEX-kind-absent-default-kind")),
    "S16.9.109-003": ("effect", ("INDEX-string-shorter-than-substring-zero",)),
    "S16.9.109-004": ("effect", ("INDEX-forward-smallest-position", "INDEX-backward-greatest-position",
                                  "INDEX-empty-substring-forward-one", "INDEX-empty-substring-backward-len-plus-one")),
    "S16.9.109-005": ("effect", ("INDEX-no-match-zero",)),
    "S16.9.110-002": ("effect", ("INT-integer-result", "INT-kind-present-result-kind", "INT-kind-absent-default-kind")),
    "S16.9.110-003": ("effect", ("INT-integer-identity", "INT-real-magnitude-less-than-one-zero",
                                  "INT-real-truncates-toward-zero", "INT-complex-uses-real-part")),
    "S16.9.110-004": ("effect", ("INT-enum-corresponding-integer-value",)),
    "S16.9.110-005": ("effect", ("INT-boz-bit-sequence-padding-truncation",)),
    "S16.9.111-002": ("effect", ("IOR-result-kind-from-I-or-J",)),
    "S16.9.111-003": ("effect", ("IOR-boz-converted-as-int-to-other-kind",)),
    "S16.9.111-004": ("effect", ("IOR-inclusive-or-truth-table", "IOR-negative-operand-bit-pattern")),
    "S16.9.112-002": ("effect", ("IPARITY-result-same-type-kind-as-array", "IPARITY-result-scalar-without-dim",
                                  "IPARITY-result-rank-and-shape-with-dim")),
    "S16.9.112-003": ("effect", ("IPARITY-all-elements-exclusive-or", "IPARITY-zero-size-array-zero")),
    "S16.9.112-004": ("effect", ("IPARITY-mask-pack-equivalence", "IPARITY-all-false-mask-zero")),
    "S16.9.112-005": ("effect", ("IPARITY-rank-one-dim-equals-no-dim", "IPARITY-dim-vector-section-reduction",
                                  "IPARITY-dim-mask-section-reduction")),
    "S16.9.113-002": ("effect", ("ISHFT-result-same-integer-kind-as-I",)),
    "S16.9.113-003": ("effect", ("ISHFT-positive-left-shift-bits", "ISHFT-negative-right-shift-bits",
                                  "ISHFT-zero-shift-preserves-bits", "ISHFT-shifted-out-bits-lost-and-zeros-shifted-in")),
}

REMAINING_PENDING = {
    "S16.9.109-001": {
        "INDEX-string-character": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "INDEX-substring-character-same-kind": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "INDEX-back-logical": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "INDEX-kind-scalar-integer-constant": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
    },
    "S16.9.110-001": {
        "INT-a-allowed-type-or-boz": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "INT-kind-scalar-integer-constant": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
    },
    "S16.9.110-004": {
        "INT-enumeration-ordinal-position": "Left pending by intrinsics_16_9_n: the reference gfortran on this host rejects typed enumeration syntax, so no reference validation exists for this portable rule yet.",
    },
    "S16.9.110-006": {
        "INT-boz-msb-one-numeric-interpretation-processor-dependent": "Left pending by intrinsics_16_9_n: 16.9.110 p5 makes the numeric interpretation processor dependent when the most significant bit is 1.",
    },
    "S16.9.111-001": {
        "IOR-I-integer-or-boz": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "IOR-J-integer-or-boz": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "IOR-integer-kinds-match": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "IOR-not-both-boz": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
    },
    "S16.9.112-001": {
        "IPARITY-array-integer-array": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "IPARITY-dim-integer-scalar-valid-range": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "IPARITY-mask-logical-conformable": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
    },
    "S16.9.113-001": {
        "ISHFT-I-integer": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "ISHFT-SHIFT-integer": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
        "ISHFT-SHIFT-absolute-value-not-greater-than-bit-size": "Left pending by intrinsics_16_9_n: unnumbered argument restrictions are not diagnostic facets.",
    },
}

ORACLE_PREFIXES = {rule: f"{rule} intrinsics_16_9_n runtime fixture: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} intrinsics_16_9_n fixture boundaries: " for rule in SELECTED}
ORACLES = {
    rule: ORACLE_PREFIXES[rule] + "Generated runtime fixtures check only source-stated exact properties: direct kind/shape inquiries on intrinsic expressions, exact INDEX positions including zero-length substrings, exact INT truncation for exactly representable operands, and bit results observed by BTEST, POPCNT, or whole-model bit comparison."
    for rule in SELECTED
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + "Only the listed portable facets are discharged. Unnumbered argument restrictions remain pending as non-diagnostic source restrictions; processor-dependent BOZ numeric interpretation with a most-significant one bit is not asserted."
    for rule in SELECTED
}
SOURCE_ONLY_PATTERNS = [
    ("Source registration only. Future fixtures use exact integer, logical, character, kind, rank, shape, and bit-pattern observations; bit results are observed in bit context by BTEST, POPCNT, or equality only when a whole bit sequence equality is modeled.",
     "Original source registration only; selected intrinsics_16_9_n facets now have bounded runtime fixtures and mutation plans."),
    ("Source registration only. Future fixtures use exact integer, logical, character, shape, kind, and bit-pattern observations, and use real values only for exact operations or standard inquiry-model values.",
     "Original source registration only; selected intrinsics_16_9_n facets now have bounded runtime fixtures and mutation plans."),
    ("Source registration only.",
     "Original source registration only; selected intrinsics_16_9_n facets now have bounded runtime fixtures and mutation plans."),
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
  logical function same_bits(a, b)
    integer, intent(in) :: a, b
    integer :: k
    same_bits = .true.
    do k = 0, bit_size(a) - 1
      if (btest(a, k) .neqv. btest(b, k)) same_bits = .false.
    end do
  end function same_bits
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


def make_source(name, rule, facets, declarations, body, checks):
    completion = "INTRINSICS 16.9 N " + name.upper().replace("_", " ") + " OK\n"
    return header(rule, facets, "i169n_" + name) + declarations + "  checks = 0\n" + body + finish("i169n_" + name, completion, checks), completion


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
                source=source, source_sha256=sha(raw), completion=completion, mutations=materialized,
                profiles=list(profiles))


def cases():
    out = []
    ik_decl = "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
    out.append(build_case(
        "index_positions_and_kinds", "S16.9.109-002", SELECTED["S16.9.109-002"][1],
        ik_decl + "  integer :: checks\n  integer :: pos\n",
        "  pos = index('FORTRAN', 'R')\n"
        "  call require('INDEX result is integer assignment with exact example value', pos == 3, checks)\n"
        "  call require('INDEX present KIND selects result kind', kind(index('AB', 'B', kind=ik)) == ik, checks)\n"
        "  call require('INDEX absent KIND is default integer kind', kind(index('AB', 'B')) == kind(0), checks)\n",
        [mut("index-integer-result-search", "INDEX-integer-result", "pos = index('FORTRAN', 'R')", "pos = index('FORTRAN', 'T')"),
         mut("index-present-kind-omitted", "INDEX-kind-present-result-kind", "kind(index('AB', 'B', kind=ik))", "kind(index('AB', 'B'))"),
         mut("index-absent-kind-added", "INDEX-kind-absent-default-kind", "kind(index('AB', 'B')) == kind(0)", "kind(index('AB', 'B', kind=ik)) == kind(0)")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "index_result_values", "S16.9.109-003", SELECTED["S16.9.109-003"][1],
        "  integer :: checks\n",
        "  call require('INDEX shorter string than substring gives zero', index('AB', 'ABC') == 0, checks)\n",
        [mut("index-shorter-substring-found", "INDEX-string-shorter-than-substring-zero", "index('AB', 'ABC')", "index('AB', 'A')")]))
    out.append(build_case(
        "index_back_empty_values", "S16.9.109-004", SELECTED["S16.9.109-004"][1],
        "  integer :: checks\n",
        "  call require('INDEX forward smallest matching position', index('ABABA', 'BA') == 2, checks)\n"
        "  call require('INDEX backward greatest matching position', index('ABABA', 'BA', back=.true.) == 4, checks)\n"
        "  call require('INDEX empty substring forward gives one', index('ABCD', '', back=.false.) == 1, checks)\n"
        "  call require('INDEX empty substring backward gives length plus one', &\n"
        "       index('ABCD', '', back=.true.) == len('ABCD') + 1, checks)\n",
        [mut("index-forward-to-backward", "INDEX-forward-smallest-position", "index('ABABA', 'BA')", "index('ABABA', 'BA', back=.true.)"),
         mut("index-backward-to-forward", "INDEX-backward-greatest-position", "index('ABABA', 'BA', back=.true.)", "index('ABABA', 'BA', back=.false.)"),
         mut("index-empty-forward-to-backward", "INDEX-empty-substring-forward-one", "index('ABCD', '', back=.false.)", "index('ABCD', '', back=.true.)"),
         mut("index-empty-backward-to-forward", "INDEX-empty-substring-backward-len-plus-one", "index('ABCD', '', back=.true.)", "index('ABCD', '', back=.false.)")]))
    out.append(build_case(
        "index_no_match", "S16.9.109-005", SELECTED["S16.9.109-005"][1],
        "  integer :: checks\n",
        "  call require('INDEX no matching substring gives zero', index('ABCDEF', 'XY') == 0, checks)\n",
        [mut("index-no-match-to-match", "INDEX-no-match-zero", "index('ABCDEF', 'XY')", "index('ABCDEF', 'CD')")]))

    out.append(build_case(
        "int_numeric_and_boz", "S16.9.110-002", SELECTED["S16.9.110-002"][1],
        ik_decl + "  integer :: checks\n  integer :: got\n",
        "  got = int(17)\n"
        "  call require('INT result is integer assignment with exact value', got == 17, checks)\n"
        "  call require('INT present KIND selects result kind', kind(int(17, kind=ik)) == ik, checks)\n"
        "  call require('INT absent KIND is default integer kind', kind(int(17)) == kind(0), checks)\n",
        [mut("int-integer-result-argument", "INT-integer-result", "got = int(17)", "got = int(18)"),
         mut("int-present-kind-omitted", "INT-kind-present-result-kind", "kind(int(17, kind=ik))", "kind(int(17))"),
         mut("int-absent-kind-added", "INT-kind-absent-default-kind", "kind(int(17)) == kind(0)", "kind(int(17, kind=ik)) == kind(0)")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "int_value_rules", "S16.9.110-003", SELECTED["S16.9.110-003"][1],
        "  integer :: checks\n",
        "  call require('INT integer argument is identity', int(-42) == -42, checks)\n"
        "  call require('INT real magnitude less than one gives zero', &\n"
        "       int(0.5) == 0 .and. int(-0.5) == 0, checks)\n"
        "  call require('INT real truncates toward zero exactly', &\n"
        "       int(3.75) == 3 .and. int(-3.75) == -3, checks)\n"
        "  call require('INT complex argument uses real part', int(cmplx(-3.75, 99.0)) == -3, checks)\n",
        [mut("int-identity-argument", "INT-integer-identity", "int(-42) == -42", "int(-41) == -42"),
         mut("int-small-real-nonzero", "INT-real-magnitude-less-than-one-zero", "int(-0.5) == 0", "int(-1.5) == 0"),
         mut("int-truncation-fraction", "INT-real-truncates-toward-zero", "int(-3.75) == -3", "int(-4.75) == -3"),
         mut("int-complex-real-part-swapped", "INT-complex-uses-real-part", "int(cmplx(-3.75, 99.0))", "int(cmplx(99.0, -3.75))")]))
    out.append(build_case(
        "int_enum_value", "S16.9.110-004", SELECTED["S16.9.110-004"][1],
        "  integer :: checks\n"
        "  enum, bind(c)\n"
        "    enumerator :: enum_negative = -2, enum_positive = 4\n"
        "  end enum\n",
        "  call require('INT enum returns corresponding integer value', &\n"
        "       int(enum_negative) == -2 .and. int(enum_positive) == 4, checks)\n",
        [mut("int-enum-value", "INT-enum-corresponding-integer-value", "int(enum_positive) == 4", "int(enum_negative) == 4")]))
    out.append(build_case(
        "int_boz_bits", "S16.9.110-005", SELECTED["S16.9.110-005"][1],
        ik_decl + "  integer :: checks\n  integer :: b6\n  integer(kind=ik) :: z15\n",
        "  b6 = int(b'0110')\n"
        "  z15 = int(z'000F', kind=ik)\n"
        "  call require('INT BOZ low bit sequence is padded or truncated then preserved', &\n"
        "       btest(b6, 1) .and. btest(b6, 2) .and. popcnt(b6) == 2 .and. &\n"
        "       btest(z15, 0) .and. btest(z15, 1) .and. btest(z15, 2) .and. btest(z15, 3) .and. &\n"
        "       popcnt(z15) == 4, checks)\n",
        [mut("int-boz-digits", "INT-boz-bit-sequence-padding-truncation", "b6 = int(b'0110')", "b6 = int(b'0010')")],
        profiles=["integer-kinds-4-8"]))

    out.append(build_case(
        "ior_bit_model", "S16.9.111-002", SELECTED["S16.9.111-002"][1],
        ik_decl + "  integer :: checks\n  integer(kind=ik) :: mixed\n",
        "  mixed = ior(z'05', 2_ik)\n"
        "  call require('IOR result kind comes from integer operand', &\n"
        "       kind(ior(5_ik, 3_ik)) == ik .and. kind(ior(z'01', 3_ik)) == ik .and. &\n"
        "       kind(ior(3_ik, z'01')) == ik, checks)\n",
        [mut("ior-result-kind-default", "IOR-result-kind-from-I-or-J", "kind(ior(5_ik, 3_ik)) == ik", "kind(ior(5, 3)) == ik")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "ior_boz_and_values", "S16.9.111-003", SELECTED["S16.9.111-003"][1],
        ik_decl + "  integer :: checks\n  integer(kind=ik) :: from_left, from_right\n",
        "  from_left = ior(z'05', 2_ik)\n"
        "  from_right = ior(2_ik, z'05')\n"
        "  call require('IOR BOZ operand is converted like INT to other kind', &\n"
        "       btest(from_left, 0) .and. btest(from_left, 1) .and. btest(from_left, 2) .and. &\n"
        "       popcnt(from_left) == 3 .and. btest(from_right, 0) .and. btest(from_right, 1) .and. &\n"
        "       btest(from_right, 2) .and. popcnt(from_right) == 3, checks)\n",
        [mut("ior-boz-left-digits", "IOR-boz-converted-as-int-to-other-kind", "from_left = ior(z'05', 2_ik)", "from_left = ior(z'01', 2_ik)")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "ior_truth_table", "S16.9.111-004", SELECTED["S16.9.111-004"][1],
        "  integer :: checks\n",
        "  call require('IOR inclusive OR truth table sets either one bits', &\n"
        "       btest(ior(5, 3), 0) .and. btest(ior(5, 3), 1) .and. btest(ior(5, 3), 2) .and. &\n"
        "       popcnt(iand(ior(5, 3), 7)) == 3, checks)\n"
        "  call require('IOR negative operand bit pattern keeps every one bit', &\n"
        "       same_bits(ior(-1, 0), -1) .and. same_bits(ior(-1, -1), -1), checks)\n",
        [mut("ior-truth-to-exclusive", "IOR-inclusive-or-truth-table", "popcnt(iand(ior(5, 3), 7))", "popcnt(iand(ieor(5, 3), 7))"),
         mut("ior-negative-to-and", "IOR-negative-operand-bit-pattern", "same_bits(ior(-1, 0), -1)", "same_bits(iand(-1, 0), -1)")]))

    out.append(build_case(
        "iparity_characteristics", "S16.9.112-002", SELECTED["S16.9.112-002"][1],
        ik_decl + "  integer :: checks\n  integer(kind=ik) :: wide(3)\n  integer :: a(2,3)\n",
        "  wide = [1_ik, 2_ik, 4_ik]\n"
        "  a = reshape([1, 2, 4, 8, 16, 32], [2, 3])\n"
        "  call require('IPARITY result has same kind as ARRAY', kind(iparity(wide)) == ik, checks)\n"
        "  call require('IPARITY without DIM is scalar', size(shape(iparity(a))) == 0, checks)\n"
        "  call require('IPARITY with DIM has rank one and remaining shape', &\n"
        "       size(shape(iparity(a, dim=1))) == 1 .and. all(shape(iparity(a, dim=1)) == [3]), checks)\n",
        [mut("iparity-kind-default", "IPARITY-result-same-type-kind-as-array", "kind(iparity(wide)) == ik", "kind(iparity([1, 2, 4])) == ik"),
         mut("iparity-scalar-to-dim", "IPARITY-result-scalar-without-dim", "shape(iparity(a))", "shape(iparity(a, dim=1))"),
         mut("iparity-dim-shape", "IPARITY-result-rank-and-shape-with-dim", "shape(iparity(a, dim=1)) == [3]", "shape(iparity(a, dim=2)) == [3]")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "iparity_value_reductions", "S16.9.112-003", SELECTED["S16.9.112-003"][1],
        "  integer :: checks\n  integer, allocatable :: empty(:)\n",
        "  allocate(empty(0))\n"
        "  call require('IPARITY all elements are exclusive OR reduced', &\n"
        "       same_bits(iparity([14, 13, 8]), ieor(ieor(14, 13), 8)), checks)\n"
        "  call require('IPARITY zero-size array has zero value', &\n"
        "       popcnt(iparity(empty)) == 0 .and. popcnt(iparity([1, 2, 4])) == 3, checks)\n",
        [mut("iparity-third-element", "IPARITY-all-elements-exclusive-or", "iparity([14, 13, 8])", "iparity([14, 13, 9])"),
         mut("iparity-empty-to-nonempty", "IPARITY-zero-size-array-zero", "iparity(empty)", "iparity([1, 2, 4])")]))
    out.append(build_case(
        "iparity_mask_values", "S16.9.112-004", SELECTED["S16.9.112-004"][1],
        "  integer :: checks\n  integer :: a(3)\n  logical :: mask_some(3), mask_none(3)\n",
        "  a = [14, 13, 8]\n"
        "  mask_some = [.true., .false., .true.]\n"
        "  mask_none = [.false., .false., .false.]\n"
        "  call require('IPARITY with MASK equals packed ARRAY reduction', &\n"
        "       same_bits(iparity(a, mask=mask_some), iparity(pack(a, mask_some))), checks)\n"
        "  call require('IPARITY all-false MASK gives zero', &\n"
        "       popcnt(iparity(a, mask=mask_none)) == 0 .and. popcnt(iparity(a, mask=mask_some)) > 0, checks)\n",
        [mut("iparity-mask-pack-feature", "IPARITY-mask-pack-equivalence", "same_bits(iparity(a, mask=mask_some), iparity(pack(a, mask_some)))", "same_bits(iparity(a, mask=mask_none), iparity(pack(a, mask_some)))"),
         mut("iparity-mask-none-to-some", "IPARITY-all-false-mask-zero", "mask_none = [.false., .false., .false.]", "mask_none = [.true., .false., .true.]")]))
    out.append(build_case(
        "iparity_dim_sections", "S16.9.112-005", SELECTED["S16.9.112-005"][1],
        "  integer :: checks\n  integer :: a(2,3)\n  logical :: mask_cols(2,3)\n",
        "  a = reshape([1, 2, 4, 8, 16, 32], [2, 3])\n"
        "  mask_cols = reshape([.true., .false., .false., .true., .true., .true.], [2, 3])\n"
        "  call require('IPARITY rank-one DIM equals no-DIM reduction', &\n"
        "       same_bits(iparity([1, 2, 4], dim=1), iparity([1, 2, 4])), checks)\n"
        "  call require('IPARITY DIM reduces each vector section', &\n"
        "       all(iparity(a, dim=1) == [3, 12, 48]) .and. all(iparity(a, dim=2) == [21, 42]), checks)\n"
        "  call require('IPARITY DIM with MASK reduces masked vector sections', &\n"
        "       all(iparity(a, dim=1, mask=mask_cols) == [1, 8, 48]), checks)\n",
        [mut("iparity-rank-one-rhs", "IPARITY-rank-one-dim-equals-no-dim", "iparity([1, 2, 4]))", "iparity([1, 2, 5]))"),
         mut("iparity-dim-data", "IPARITY-dim-vector-section-reduction", "16, 32", "16, 64"),
         mut("iparity-dim-mask-columns", "IPARITY-dim-mask-section-reduction", "[.true., .false., .false., .true., .true., .true.]", "[.false., .true., .false., .true., .true., .true.]")]))

    out.append(build_case(
        "ishft_kind_and_bits", "S16.9.113-002", SELECTED["S16.9.113-002"][1],
        ik_decl + "  integer :: checks\n  integer :: n, x\n  integer(kind=ik) :: wide\n",
        "  n = bit_size(0)\n"
        "  x = ibset(ibset(0, 0), 2)\n"
        "  wide = 3_ik\n"
        "  call require('ISHFT result has same kind as I', kind(ishft(wide, 1)) == ik, checks)\n",
        [mut("ishft-kind-default", "ISHFT-result-same-integer-kind-as-I", "kind(ishft(wide, 1)) == ik", "kind(ishft(3, 1)) == ik")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "ishft_value_bits", "S16.9.113-003", SELECTED["S16.9.113-003"][1],
        "  integer :: checks\n  integer :: n, left_in, right_in, stable\n",
        "  n = bit_size(0)\n"
        "  left_in = ibset(ibset(0, 0), 2)\n"
        "  right_in = ibset(ibset(0, 4), 6)\n"
        "  stable = ibset(ibset(ibset(0, 0), 3), n - 2)\n"
        "  call require('ISHFT positive SHIFT moves bits left', &\n"
        "       same_bits(ishft(left_in, 3), ibset(ibset(0, 3), 5)), checks)\n"
        "  call require('ISHFT negative SHIFT moves bits right', &\n"
        "       same_bits(ishft(right_in, -2), ibset(ibset(0, 2), 4)), checks)\n"
        "  call require('ISHFT zero SHIFT preserves all bits', same_bits(ishft(stable, 0), stable), checks)\n"
        "  call require('ISHFT shifted-out bits are lost and zeros shifted in', &\n"
        "       popcnt(ishft(ibset(0, n - 1), 1)) == 0 .and. popcnt(ishft(1, -1)) == 0, checks)\n",
        [mut("ishft-left-to-right", "ISHFT-positive-left-shift-bits", "ishft(left_in, 3)", "ishft(left_in, -3)"),
         mut("ishft-right-to-left", "ISHFT-negative-right-shift-bits", "ishft(right_in, -2)", "ishft(right_in, 2)"),
         mut("ishft-zero-to-one", "ISHFT-zero-shift-preserves-bits", "ishft(stable, 0)", "ishft(stable, 1)"),
         mut("ishft-lost-to-zero-shift", "ISHFT-shifted-out-bits-lost-and-zeros-shifted-in", "ishft(ibset(0, n - 1), 1)", "ishft(ibset(0, n - 1), 0)")]))
    return out


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for spec in cases():
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        if spec.get("profiles"):
            manifest["profiles"] = spec["profiles"]
        spec = dict(spec)
        spec["path"], spec["manifest"] = directory.relative_to(root).as_posix() + "/fixture.json", manifest
        specs[spec["id"]] = spec
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    specs = build_corpus()[1]
    by_rule_facets = {}
    for spec in specs.values():
        by_rule_facets.setdefault(spec["rule"], set()).update(spec["facets"])
    for rule, facets in by_rule_facets.items():
        if rule not in by_rule:
            continue
        row = by_rule[rule]
        if not facets <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + rule)
        for facet in facets:
            row.setdefault("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    for rule, pending_items in REMAINING_PENDING.items():
        if rule in by_rule:
            row = by_rule[rule]
            pending = row.setdefault("pending", {})
            for facet, reason in pending_items.items():
                pending[facet] = reason
    for row in result["requirements"]:
        for old, new in SOURCE_ONLY_PATTERNS:
            if row.get("oracle") == old:
                row["oracle"] = new
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
    owned_cases = [spec for spec in build_corpus(root)[1].values() if spec["rule"].startswith("S" + section + "-")]
    covered = sum(len(spec["facets"]) for spec in owned_cases)
    summary = (SUMMARY_BEGIN + "\n"
        f"## Intrinsics 16.9.N runtime observations\n\n"
        f"This batch adds {len(owned_cases)} generated runtime fixtures for {section}, covering {covered} pending facets "
        f"with exact INDEX, INT, IOR, IPARITY, and ISHFT observations. Mutations perturb the load-bearing intrinsic "
        f"expression or source data for each facet and mutation checking requires every mutant to compile and fail at run time. "
        f"Unnumbered argument restrictions and processor-dependent most-significant-one BOZ interpretation remain pending.\n"
        + SUMMARY_END)
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
        updated = synced_catalogue(catalogue)
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
            raise ValueError("stale intrinsics_16_9_n generated files: " + ", ".join(stale))
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


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["id"])
    mutated = raw
    for start, end, old, new in reversed(mutation["spans"]):
        if raw[start:end].decode("ascii") != old:
            raise ValueError("mutation span lost complete-parent binding")
        mutated = mutated[:start] + new.encode("ascii") + mutated[end:]
    return mutated


KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "index_positions_and_kinds",
        "index_back_empty_values",
        "ior_bit_model",
        "ior_boz_and_values",
        "iparity_characteristics",
        "iparity_dim_sections",
    }
}


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(str(compiler)).name.lower() else "gfortran"


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
    failures, checked, skipped, parents = [], 0, 0, 0
    family = compiler_family(compiler)
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, rc, stdout, stderr = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"))
            parent_passed = status == "pass" and stdout == spec["completion"] and stderr == ""
            parent_known = spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set())
            if not parent_passed:
                if not parent_known:
                    failures.append(f"{spec['id']} parent failed {status} rc={rc}\nstdout={stdout}\nstderr={stderr}")
                else:
                    skipped += len(spec["mutations"])
                continue
            parents += 1
            for mutation in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mutation["id"])
                case_dir.mkdir()
                source = spec["source"].encode("ascii") if inject_survivor and checked == 1 else mutated_source(spec, mutation)
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
        parents, checked, skipped = check_mutations(args.root, args.compiler, args.std, args.inject_surviving_mutant)
        print(f"Mutation-checked {checked} intrinsics_16_9_n mutations across {parents} parents; "
              f"{skipped} skipped for known parent failures.")
        return
    _, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics 16.9.n cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} mutations.")


if __name__ == "__main__":
    main()
