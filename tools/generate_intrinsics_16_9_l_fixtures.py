#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.96-16.9.100."""

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
TOPIC = "intrinsics_16_9_l"
SECTIONS = ("16.9.96", "16.9.97", "16.9.98", "16.9.99", "16.9.100")
CATALOGUES = {
    "16.9.96": "doc/catalogues/huge_intrinsic_16_9_96.json",
    "16.9.97": "doc/catalogues/hypot_intrinsic_16_9_97.json",
    "16.9.98": "doc/catalogues/iachar_intrinsic_16_9_98.json",
    "16.9.99": "doc/catalogues/iall_16_9_99.json",
    "16.9.100": "doc/catalogues/iand_intrinsic_16_9_100.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9 L FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9 L FIXTURES -->"
INTEGER_MODEL_PROFILE = "intrinsics-16-9-l-integer-model-4-8-distinct"
REAL_MODEL_PROFILE = "intrinsics-16-9-l-real-binary-4-8-distinct"

SELECTED = {
    "S16.9.96-001": ("positive-control", ("HUGE-X-integer-real-or-enumeration", "HUGE-X-scalar-or-array")),
    "S16.9.96-002": ("effect", ("HUGE-result-scalar", "HUGE-result-same-type-and-kind-as-X")),
    "S16.9.96-003": ("effect", ("HUGE-integer-model-upper-bound", "HUGE-integer-distinguishes-kinds")),
    "S16.9.96-004": ("effect", ("HUGE-real-model-largest-value", "HUGE-real-distinguishes-kinds")),
    "S16.9.97-001": ("positive-control", ("HYPOT-X-real", "HYPOT-Y-real-same-kind-as-X")),
    "S16.9.97-002": ("effect", ("HYPOT-result-same-real-kind-as-X",)),
    "S16.9.98-001": ("positive-control", ("IACHAR-C-character-length-one", "IACHAR-KIND-scalar-integer-constant-expression")),
    "S16.9.98-002": ("effect", ("IACHAR-result-integer", "IACHAR-result-default-kind-without-KIND", "IACHAR-result-kind-from-KIND")),
    "S16.9.98-003": ("effect", ("IACHAR-ASCII-position-exact", "IACHAR-ASCII-result-range")),
    "S16.9.98-005": ("effect", ("IACHAR-LLE-implies-code-le", "IACHAR-LGE-implies-code-ge", "IACHAR-equality-consistent-codes")),
    "S16.9.99-001": ("positive-control", ("IALL-ARRAY-integer-array", "IALL-DIM-integer-scalar-valid-range", "IALL-MASK-logical-conformable")),
    "S16.9.99-002": ("effect", ("IALL-result-type-kind-from-array", "IALL-result-scalar-without-dim-or-rank-one", "IALL-result-shape-removes-dim")),
    "S16.9.99-003": ("effect", ("IALL-bitwise-and-all-elements", "IALL-zero-size-identity-all-one-bits")),
    "S16.9.99-004": ("effect", ("IALL-mask-pack-equivalence", "IALL-all-false-mask-uses-zero-size-identity")),
    "S16.9.99-005": ("effect", ("IALL-dim-rank-one-equals-whole-array", "IALL-dim-section-wise-reduction", "IALL-dim-mask-section-wise-reduction")),
    "S16.9.100-001": ("positive-control", ("IAND-I-integer-or-boz", "IAND-J-integer-or-boz")),
    "S16.9.100-002": ("effect", ("IAND-result-kind-from-non-boz-operand",)),
    "S16.9.100-003": ("effect", ("IAND-boz-converted-as-int-to-other-kind",)),
    "S16.9.100-004": ("effect", ("IAND-bit-truth-table",)),
}

RESTORED_PENDING = {
    "S16.9.96-005": {
        "HUGE-enumeration-last-enumerator": "Left pending by intrinsics_16_9_l: GNU Fortran 16.1.0 rejects the Fortran 2023 enumeration type syntax needed for a reference-validated HUGE enumeration fixture.",
        "HUGE-enumeration-singleton-last-enumerator": "Left pending by intrinsics_16_9_l: GNU Fortran 16.1.0 rejects the Fortran 2023 enumeration type syntax needed for a singleton enumeration fixture.",
    },
    "S16.9.97-003": {
        "HYPOT-euclidean-distance-processor-dependent-approximation": "Left pending by intrinsics_16_9_l: p5 explicitly makes the numeric approximation processor dependent, so no exact value oracle is asserted."
    },
    "S16.9.97-004": {
        "HYPOT-without-undue-overflow-underflow": "Left pending by intrinsics_16_9_l: p5 gives no portable numeric bound for undue overflow or underflow."
    },
    "S16.9.98-004": {
        "IACHAR-non-ASCII-result-processor-dependent": "Left pending by intrinsics_16_9_l: p5 explicitly makes non-ASCII code values processor dependent."
    },
    "S16.9.100-001": {
        "IAND-integer-kinds-match": "Restored by intrinsics_16_9_l: this unnumbered same-kind restriction is source-control only; no diagnostic is required and a positive control does not discharge it.",
        "IAND-not-both-boz": "Restored by intrinsics_16_9_l: this unnumbered not-both-BOZ restriction is source-control only; no diagnostic is required and a positive control does not discharge it.",
    },
}

ORACLE_PREFIXES = {rule: f"{rule} {TOPIC} runtime fixture: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} {TOPIC} fixture boundaries: " for rule in SELECTED}
ORACLES = {
    rule: ORACLE_PREFIXES[rule] +
    "Generated run/effect or positive-control fixtures check only source-stated portable properties: direct KIND/SHAPE inquiries on intrinsic expressions, exact ASCII IACHAR positions, exact integer bit observations through BTEST, IALL zero-size identity against NOT(0_kind), and HUGE integer/real model decompositions under explicit model profiles."
    for rule in SELECTED
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] +
    "Only the listed facets are discharged. Enumeration HUGE waits for a reference compiler accepting Fortran 2023 enumeration type syntax; HYPOT numeric approximation and undue-overflow details remain pending; non-ASCII IACHAR values remain processor dependent; and IAND unnumbered invalid-call restrictions are not diagnostic claims."
    for rule in SELECTED
}

SOURCE_ONLY_PATTERNS = [
    ("Source accounting only. This packet creates no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.",
     "Original source accounting created no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim; this intrinsics_16_9_l generator supplies selected runtime fixtures and mutation plans without granting universal coverage."),
    ("Source registration only.", "Original source registration only; selected facets now have bounded runtime fixtures and mutation plans."),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, rule):
    return rule.replace(".", "_").replace("-", "_") + f"_valid__{TOPIC}_{variant}"


def mut(mid, facet, expected, replacement):
    return {"id": mid, "facet": facet, "kind": "source", "category": "feature",
            "replacements": [{"expected": expected, "replacement": replacement}]}


def multi_mut(mid, facet, replacements):
    return {"id": mid, "facet": facet, "kind": "source", "category": "feature",
            "replacements": [{"expected": old, "replacement": new} for old, new in replacements]}


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
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program {program}
"""


def source_program(variant, rule, facets, declarations, body, checks):
    program = "i169l_" + variant
    completion = "INTRINSICS 16.9 L " + variant.upper().replace("_", " ") + " OK\n"
    header = [f"! rule: {rule}"] + [f"! covers: {facet}" for facet in facets]
    interface = "  interface type_code\n    procedure type_code_integer, type_code_real\n  end interface\n"
    source = ("\n".join(header) + f"\nprogram {program}\n  implicit none\n" + interface +
              declarations + "  checks = 0\n" + body +
              f"  if (checks /= {checks}) error stop\n  write(*,'(a)') '{completion.rstrip()}'\n" +
              HELPERS.format(program=program))
    return source, completion


def build_case(variant, rule, facets, declarations, body, mutations, profiles=()):
    evidence = SELECTED[rule][0]
    facets = tuple(facets)
    source, completion = source_program(variant, rule, facets, declarations, body, len(facets))
    raw = source.encode("ascii")
    materialized = []
    for mutation in mutations:
        mutant = raw
        spans = []
        for item in mutation["replacements"]:
            old = item["expected"].encode("ascii")
            count = mutant.count(old)
            if count != 1:
                raise ValueError(f"{variant}:{mutation['id']} expected unique {item['expected']!r}, found {count}")
            start = mutant.index(old)
            end = start + len(old)
            spans.append([start, end, item["expected"], item["replacement"]])
            mutant = mutant[:start] + item["replacement"].encode("ascii") + mutant[end:]
        row = dict(mutation)
        row["spans"] = spans
        row["mutant_sha256"] = sha(mutant)
        materialized.append(row)
    if {m["facet"] for m in materialized} != set(facets):
        raise ValueError(f"{variant} mutations do not cover facets")
    return dict(id=identifier(variant, rule), variant=variant, rule=rule, facets=list(facets), evidence=evidence,
                source=source, source_sha256=sha(raw), completion=completion,
                mutations=materialized, profiles=list(profiles))


def cases():
    out = []
    out.append(build_case(
        "huge_argument_controls", "S16.9.96-001", SELECTED["S16.9.96-001"][1],
        "  integer :: checks\n  integer :: ia(2)\n  real :: ra(2)\n",
        "  ia = [1, 2]\n  ra = [1.0, 2.0]\n"
        "  call require('HUGE admits integer and real arguments', &\n"
        "       huge(ia(1)) > ia(1) .and. huge(ra(1)) > ra(1), checks)\n"
        "  call require('HUGE scalar result for scalar and array X', &\n"
        "       size(shape(huge(ia))) == 0 .and. size(shape(huge(ra))) == 0, checks)\n",
        [mut("replace-real-huge-with-tiny", "HUGE-X-integer-real-or-enumeration", "huge(ra(1)) > ra(1)", "tiny(ra(1)) > ra(1)"),
         mut("remove-huge-array-inquiry", "HUGE-X-scalar-or-array", "size(shape(huge(ia))) == 0", "size(shape(ia)) == 0")]))
    out.append(build_case(
        "huge_result_characteristics", "S16.9.96-002", SELECTED["S16.9.96-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer :: checks\n  integer(kind=ik) :: wide(2)\n  real(kind=8) :: rd\n",
        "  wide = [1_ik, 2_ik]\n  rd = 1.0_8\n"
        "  call require('HUGE result is scalar even for arrays', &\n"
        "       size(shape(huge(wide))) == 0 .and. size(shape(huge([rd, rd]))) == 0, checks)\n"
        "  call require('HUGE result has X type and kind', &\n"
        "       type_code(huge(1)) == 1 .and. type_code(huge(1.0)) == 2 .and. &\n"
        "       kind(huge(wide)) == ik .and. kind(huge(rd)) == kind(rd), checks)\n",
        [mut("remove-huge-from-shape", "HUGE-result-scalar", "size(shape(huge(wide))) == 0", "size(shape(wide)) == 0"),
         mut("drop-nondefault-integer-kind", "HUGE-result-same-type-and-kind-as-X", "kind(huge(wide)) == ik", "kind(huge(int(wide))) == ik")],
        profiles=["integer-kinds-4-8", "real-kinds-4-8"]))
    out.append(build_case(
        "huge_integer_model", "S16.9.96-003", SELECTED["S16.9.96-003"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer :: checks\n  integer :: model_default\n  integer(kind=ik) :: model_wide\n",
        "  model_default = integer_huge_model(0)\n  model_wide = integer_huge_model_kind(0_ik)\n"
        "  call require('HUGE integer equals r**q minus one model', &\n"
        "       huge(0) == model_default .and. huge(0_ik) == model_wide, checks)\n"
        "  call require('HUGE integer model distinguishes selected kinds', &\n"
        "       digits(0_ik) /= digits(0) .and. huge(0_ik) == model_wide, checks)\n",
        [mut("subtract-one-from-default-model", "HUGE-integer-model-upper-bound", "huge(0) == model_default", "huge(0) == model_default - 1"),
         mut("replace-wide-kind-with-default", "HUGE-integer-distinguishes-kinds", "digits(0_ik) /= digits(0)", "digits(0_ik) == digits(0)")],
        profiles=[INTEGER_MODEL_PROFILE]))
    out[-1]["source"] = out[-1]["source"].replace(
        "end program i169l_huge_integer_model\n",
        "  integer function integer_huge_model(x) result(model)\n"
        "    integer, intent(in) :: x\n"
        "    integer :: k, r\n"
        "    model = 0\n"
        "    r = radix(x)\n"
        "    do k = 1, digits(x)\n"
        "      model = model * r + (r - 1)\n"
        "    end do\n"
        "  end function integer_huge_model\n"
        "  integer(kind=ik) function integer_huge_model_kind(x) result(model)\n"
        "    integer(kind=ik), intent(in) :: x\n"
        "    integer :: k\n"
        "    integer(kind=ik) :: r\n"
        "    model = 0_ik\n"
        "    r = int(radix(x), kind=ik)\n"
        "    do k = 1, digits(x)\n"
        "      model = model * r + (r - 1_ik)\n"
        "    end do\n"
        "  end function integer_huge_model_kind\n"
        "end program i169l_huge_integer_model\n")
    rematerialize(out[-1])

    out.append(build_case(
        "huge_real_model", "S16.9.96-004", SELECTED["S16.9.96-004"][1],
        "  integer, parameter :: rk = merge(8, 4, kind(0.0) /= 8)\n"
        "  integer :: checks\n  real(kind=rk) :: x\n",
        "  x = 1.0_rk\n"
        "  call require('HUGE real exponent and fraction match model', &\n"
        "       exponent(huge(0.0)) == maxexponent(0.0) .and. &\n"
        "       fraction(huge(0.0)) == 1.0 - scale(1.0, -digits(0.0)), checks)\n"
        "  call require('HUGE real model distinguishes selected kinds', &\n"
        "       maxexponent(x) /= maxexponent(0.0) .and. &\n"
        "       exponent(huge(x)) == maxexponent(x) .and. &\n"
        "       fraction(huge(x)) == 1.0_rk - scale(1.0_rk, -digits(x)), checks)\n",
        [mut("change-real-fraction-model", "HUGE-real-model-largest-value", "scale(1.0, -digits(0.0))", "scale(1.0, 1 - digits(0.0))"),
         mut("compare-selected-to-default-model", "HUGE-real-distinguishes-kinds", "maxexponent(x) /= maxexponent(0.0)", "maxexponent(x) == maxexponent(0.0)")],
        profiles=[REAL_MODEL_PROFILE]))

    out.append(build_case(
        "hypot_argument_controls", "S16.9.97-001", SELECTED["S16.9.97-001"][1],
        "  integer, parameter :: rk = merge(8, 4, kind(0.0) /= 8)\n"
        "  integer :: checks\n  real(kind=rk) :: x, y\n",
        "  x = 0.0_rk\n  y = 0.0_rk\n"
        "  call require('HYPOT admits a real X argument', kind(hypot(x, y)) == kind(x), checks)\n"
        "  call require('HYPOT admits same-kind real Y argument', kind(hypot(x, y)) == kind(y), checks)\n",
        [mut("use-default-x-pair", "HYPOT-X-real", "kind(hypot(x, y)) == kind(x)", "kind(hypot(0.0, 0.0)) == kind(x)"),
         mut("compare-y-to-default-kind", "HYPOT-Y-real-same-kind-as-X", "kind(hypot(x, y)) == kind(y)", "kind(hypot(0.0, 0.0)) == kind(y)")],
        profiles=["real-kinds-4-8"]))
    out.append(build_case(
        "hypot_result_characteristics", "S16.9.97-002", SELECTED["S16.9.97-002"][1],
        "  integer, parameter :: rk = merge(8, 4, kind(0.0) /= 8)\n"
        "  integer :: checks\n  real(kind=rk) :: x, y\n",
        "  x = 0.0_rk\n  y = 0.0_rk\n"
        "  call require('HYPOT result has same kind as X', kind(hypot(x, y)) == kind(x), checks)\n",
        [mut("drop-result-kind-through-default-arguments", "HYPOT-result-same-real-kind-as-X", "kind(hypot(x, y)) == kind(x)", "kind(hypot(0.0, 0.0)) == kind(x)")],
        profiles=["real-kinds-4-8"]))

    out.append(build_case(
        "iachar_argument_controls", "S16.9.98-001", SELECTED["S16.9.98-001"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('IACHAR admits length-one character C', iachar('A') == 65, checks)\n"
        "  call require('IACHAR admits scalar integer constant KIND', &\n"
        "       kind(iachar('B', kind=ik)) == ik .and. iachar('B', kind=ik) == 66_ik, checks)\n",
        [mut("change-character-argument", "IACHAR-C-character-length-one", "iachar('A') == 65", "iachar('B') == 65"),
         mut("drop-kind-argument", "IACHAR-KIND-scalar-integer-constant-expression", "kind(iachar('B', kind=ik)) == ik", "kind(iachar('B')) == ik")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "iachar_result_characteristics", "S16.9.98-002", SELECTED["S16.9.98-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n  integer :: checks\n",
        "  call require('IACHAR result is integer', type_code(iachar('A')) == 1, checks)\n"
        "  call require('IACHAR without KIND is default integer kind', kind(iachar('A')) == kind(0), checks)\n"
        "  call require('IACHAR result kind follows KIND', kind(iachar('A', kind=ik)) == ik, checks)\n",
        [mut("convert-result-away-from-integer", "IACHAR-result-integer", "type_code(iachar('A')) == 1", "type_code(real(iachar('A'))) == 1"),
         mut("add-nondefault-kind-to-default-assertion", "IACHAR-result-default-kind-without-KIND", "kind(iachar('A')) == kind(0)", "kind(iachar('A', kind=ik)) == kind(0)"),
         mut("remove-kind-argument", "IACHAR-result-kind-from-KIND", "kind(iachar('A', kind=ik)) == ik", "kind(iachar('A')) == ik")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "iachar_ascii_positions", "S16.9.98-003", SELECTED["S16.9.98-003"][1],
        "  integer :: checks\n",
        "  call require('IACHAR ASCII positions are exact', &\n"
        "       iachar(' ') == 32 .and. iachar('0') == 48 .and. &\n"
        "       iachar('A') == 65 .and. iachar('X') == 88, checks)\n"
        "  call require('IACHAR ASCII positions are in range', &\n"
        "       all([iachar(' '), iachar('0'), iachar('A'), iachar('X')] >= 0) .and. &\n"
        "       all([iachar(' '), iachar('0'), iachar('A'), iachar('X')] <= 127), checks)\n",
        [mut("swap-exact-ascii-character", "IACHAR-ASCII-position-exact", "iachar('X') == 88", "iachar('W') == 88"),
         mut("tighten-ascii-range", "IACHAR-ASCII-result-range", "<= 127", "<= 87")]))
    out.append(build_case(
        "iachar_lexical_consistency", "S16.9.98-005", SELECTED["S16.9.98-005"][1],
        "  integer :: checks\n",
        "  call require('IACHAR codes follow LLE ordering', &\n"
        "       lle('A','B') .and. iachar('A') <= iachar('B'), checks)\n"
        "  call require('IACHAR codes follow LGE ordering', &\n"
        "       lge('X','0') .and. iachar('X') >= iachar('0'), checks)\n"
        "  call require('IACHAR equal characters have equal codes', &\n"
        "       lle('X','X') .and. lge('X','X') .and. iachar('X') == iachar('X'), checks)\n",
        [mut("reverse-lle-pair", "IACHAR-LLE-implies-code-le", "iachar('A') <= iachar('B')", "iachar('B') <= iachar('A')"),
         mut("reverse-lge-pair", "IACHAR-LGE-implies-code-ge", "iachar('X') >= iachar('0')", "iachar('0') >= iachar('X')"),
         mut("change-equality-character", "IACHAR-equality-consistent-codes", "iachar('X') == iachar('X')", "iachar('X') == iachar('Y')")]))

    iall_decls = "  integer :: checks\n  integer :: a2(2,3), k\n  integer :: r1(3), r2(2), rm(3)\n  logical :: mask2(2,3)\n"
    iall_setup = (
        "  a2(:,1) = [14, 11]\n  a2(:,2) = [13, 7]\n  a2(:,3) = [15, 12]\n"
        "  mask2(:,1) = [.true., .true.]\n  mask2(:,2) = [.true., .false.]\n"
        "  mask2(:,3) = [.false., .false.]\n")
    out.append(build_case(
        "iall_argument_controls", "S16.9.99-001", SELECTED["S16.9.99-001"][1],
        iall_decls,
        iall_setup +
        "  call require('IALL accepts integer ARRAY', &\n"
        "       btest(iall([14, 13, 11]), 3) .and. .not. btest(iall([14, 13, 11]), 2), checks)\n"
        "  call require('IALL accepts valid scalar DIM', &\n"
        "       all(shape(iall(a2, dim=1)) == [3]) .and. all(shape(iall(a2, dim=2)) == [2]), checks)\n"
        "  call require('IALL accepts conformable logical MASK', &\n"
        "       btest(iall(a2, mask=mask2), 3) .and. .not. btest(iall(a2, mask=mask2), 1), checks)\n",
        [mut("replace-array-reduction-with-or", "IALL-ARRAY-integer-array", "btest(iall([14, 13, 11]), 3)", "btest(iany([14, 13, 11]), 4)"),
         mut("change-dim-shape", "IALL-DIM-integer-scalar-valid-range", "all(shape(iall(a2, dim=1)) == [3])", "all(shape(iall(a2, dim=1)) == [2])"),
         mut("change-mask-selection", "IALL-MASK-logical-conformable",
             "mask2(:,2) = [.true., .false.]", "mask2(:,2) = [.false., .false.]")]))
    out.append(build_case(
        "iall_result_characteristics", "S16.9.99-002", SELECTED["S16.9.99-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer :: checks\n  integer(kind=ik) :: wide(3)\n  integer :: a2(2,3)\n",
        "  wide = int([14, 13, 11], kind=ik)\n"
        "  a2(:,1) = [14, 11]\n  a2(:,2) = [13, 7]\n  a2(:,3) = [15, 12]\n"
        "  call require('IALL result kind follows ARRAY', kind(iall(wide)) == ik, checks)\n"
        "  call require('IALL rank-one DIM or no DIM result is scalar', &\n"
        "       size(shape(iall(wide))) == 0 .and. size(shape(iall(wide, dim=1))) == 0, checks)\n"
        "  call require('IALL DIM result shape removes DIM extent', &\n"
        "       all(shape(iall(a2, dim=1)) == [3]) .and. all(shape(iall(a2, dim=2)) == [2]), checks)\n",
        [mut("drop-wide-kind", "IALL-result-type-kind-from-array", "kind(iall(wide)) == ik", "kind(iall(int(wide))) == ik"),
         mut("remove-iall-from-rank-one-shape", "IALL-result-scalar-without-dim-or-rank-one", "size(shape(iall(wide))) == 0", "size(shape(wide)) == 0"),
         mut("expect-wrong-dim-shape", "IALL-result-shape-removes-dim", "all(shape(iall(a2, dim=1)) == [3])", "all(shape(iall(a2, dim=1)) == [2])")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "iall_full_reduction", "S16.9.99-003", SELECTED["S16.9.99-003"][1],
        "  integer :: checks\n  integer :: empty(0)\n  integer :: k\n",
        "  call require('IALL full reduction is bitwise AND of all elements', &\n"
        "       btest(iall([14, 13, 11]), 3) .and. &\n"
        "       .not. btest(iall([14, 13, 11]), 2) .and. &\n"
        "       .not. btest(iall([14, 13, 11]), 1), checks)\n"
        "  call require('IALL zero-size identity has all model bits set', &\n"
        "       all([(btest(iall(empty), k) .eqv. btest(not(0), k), k = 0, 7)]) .and. &\n"
        "       (btest(iall(empty), bit_size(0)-1) .eqv. btest(not(0), bit_size(0)-1)), checks)\n",
        [mut("substitute-iany-for-full-reduction", "IALL-bitwise-and-all-elements", "btest(iall([14, 13, 11]), 3)", "btest(iany([14, 13, 11]), 4)"),
         mut("substitute-iany-for-zero-size", "IALL-zero-size-identity-all-one-bits",
             "all([(btest(iall(empty), k)", "all([(btest(iany(empty), k)")]))
    out.append(build_case(
        "iall_mask_reduction", "S16.9.99-004", SELECTED["S16.9.99-004"][1],
        "  integer :: checks\n  integer :: values(4), k\n  logical :: mask(4), refmask(4), none(4), one(4)\n",
        "  values = [15, 14, 13, 11]\n  mask = [.false., .true., .false., .true.]\n"
        "  refmask = [.false., .true., .false., .true.]\n"
        "  none = .false.\n  one = [.false., .true., .false., .false.]\n"
        "  call require('IALL MASK is equivalent to reducing PACK', &\n"
        "       all([(btest(iall(values, mask=mask), k) .eqv. &\n"
        "              btest(iall(pack(values, refmask)), k), k = 0, 4)]), checks)\n"
        "  call require('IALL all-false MASK uses zero-size identity', &\n"
        "       all([(btest(iall(values, mask=none), k) .eqv. btest(not(0), k), k = 0, 7)]) .and. &\n"
        "       .not. btest(iall(values, mask=one), bit_size(0)-1), checks)\n",
        [mut("change-pack-mask", "IALL-mask-pack-equivalence",
             "  mask = [.false., .true., .false., .true.]",
             "  mask = [.true., .true., .false., .false.]"),
         mut("use-one-true-mask-for-identity", "IALL-all-false-mask-uses-zero-size-identity", "mask=none", "mask=one")]))
    out.append(build_case(
        "iall_dim_reduction", "S16.9.99-005", SELECTED["S16.9.99-005"][1],
        iall_decls,
        iall_setup +
        "  call require('IALL rank-one DIM equals whole-array form', &\n"
        "       all([(btest(iall([14,13,11], dim=1), k) .eqv. &\n"
        "              btest(iall([14,13,11]), k), k = 0, 4)]), checks)\n"
        "  r1 = iall(a2, dim=1)\n  r2 = iall(a2, dim=2)\n"
        "  call require('IALL DIM applies to each rank-one section', &\n"
        "       btest(r1(1), 1) .and. .not. btest(r1(2), 1) .and. &\n"
        "       btest(r2(1), 2) .and. .not. btest(r2(2), 0), checks)\n"
        "  rm = iall(a2, dim=1, mask=mask2)\n"
        "  call require('IALL DIM with MASK applies section masks', &\n"
        "       btest(rm(1), 1) .and. btest(rm(2), 0) .and. &\n"
        "       btest(rm(3), bit_size(0)-1), checks)\n",
        [mut("change-rank-one-dim-array", "IALL-dim-rank-one-equals-whole-array", "[14,13,11], dim=1", "[14,13,7], dim=1"),
         mut("change-dim-section-data", "IALL-dim-section-wise-reduction", "a2(:,2) = [13, 7]", "a2(:,2) = [15, 15]"),
         mut("change-dim-mask-section", "IALL-dim-mask-section-wise-reduction", "mask2(:,3) = [.false., .false.]", "mask2(:,3) = [.true., .false.]")]))

    out.append(build_case(
        "iand_argument_controls", "S16.9.100-001", SELECTED["S16.9.100-001"][1],
        "  integer :: checks\n  integer :: j\n",
        "  j = int(z'0A')\n"
        "  call require('IAND accepts integer or BOZ I', &\n"
        "       btest(iand(z'0F', j), 3) .and. .not. btest(iand(z'0F', j), 2), checks)\n"
        "  call require('IAND accepts integer or BOZ J', &\n"
        "       btest(iand(j, z'0F'), 3) .and. .not. btest(iand(j, z'0F'), 2), checks)\n",
        [mut("change-boz-i", "IAND-I-integer-or-boz",
             "btest(iand(z'0F', j), 3)", "btest(iand(z'05', j), 3)"),
         mut("change-boz-j", "IAND-J-integer-or-boz",
             "btest(iand(j, z'0F'), 3)", "btest(iand(j, z'05'), 3)")]))
    out.append(build_case(
        "iand_result_kind", "S16.9.100-002", SELECTED["S16.9.100-002"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer :: checks\n  integer(kind=ik) :: a, b\n",
        "  a = int(z'0A', kind=ik)\n  b = int(z'0F', kind=ik)\n"
        "  call require('IAND result kind follows non-BOZ operand', &\n"
        "       kind(iand(a, b)) == ik .and. kind(iand(z'0F', a)) == ik, checks)\n",
        [mut("drop-nondefault-iand-kind", "IAND-result-kind-from-non-boz-operand", "kind(iand(z'0F', a)) == ik", "kind(iand(z'0F', int(a))) == ik")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "iand_boz_conversion", "S16.9.100-003", SELECTED["S16.9.100-003"][1],
        "  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)\n"
        "  integer :: checks, k\n  integer(kind=ik) :: v\n",
        "  v = int(z'0A', kind=ik)\n"
        "  call require('IAND converts BOZ as INT to other kind', &\n"
        "       all([(btest(iand(z'0F', v), k) .eqv. &\n"
        "              btest(iand(int(z'0F', kind=ik), v), k), k = 0, 4)]), checks)\n",
        [mut("change-boz-conversion-literal", "IAND-boz-converted-as-int-to-other-kind", "iand(z'0F', v)", "iand(z'07', v)")],
        profiles=["integer-kinds-4-8"]))
    out.append(build_case(
        "iand_truth_table", "S16.9.100-004", SELECTED["S16.9.100-004"][1],
        "  integer :: checks\n  integer :: left, right, got\n",
        "  left = ior(shiftl(1, 3), shiftl(1, 2))\n"
        "  right = ior(shiftl(1, 3), shiftl(1, 1))\n"
        "  got = iand(left, right)\n"
        "  call require('IAND truth table keeps only one-one bit pairs', &\n"
        "       btest(got, 3) .and. .not. btest(got, 2) .and. &\n"
        "       .not. btest(got, 1) .and. .not. btest(got, 0), checks)\n",
        [mut("substitute-ior-truth-table", "IAND-bit-truth-table", "got = iand(left, right)", "got = ior(left, right)")]))
    return out


def rematerialize(spec):
    raw = spec["source"].encode("ascii")
    materialized = []
    for mutation in spec["mutations"]:
        mutant = raw
        spans = []
        for item in mutation["replacements"]:
            old = item["expected"].encode("ascii")
            count = mutant.count(old)
            if count != 1:
                raise ValueError(f"{spec['variant']}:{mutation['id']} expected unique {item['expected']!r}, found {count}")
            start = mutant.index(old)
            end = start + len(old)
            spans.append([start, end, item["expected"], item["replacement"]])
            mutant = mutant[:start] + item["replacement"].encode("ascii") + mutant[end:]
        row = dict(mutation)
        row["spans"] = spans
        row["mutant_sha256"] = sha(mutant)
        materialized.append(row)
    spec["source_sha256"] = sha(raw)
    spec["mutations"] = materialized


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["variant"])
    mutant = raw
    for start, end, expected, replacement in reversed(mutation["spans"]):
        if raw[start:end].decode("ascii") != expected:
            raise ValueError("mutation span lost binding for " + spec["variant"])
        mutant = mutant[:start] + replacement.encode("ascii") + mutant[end:]
    return mutant


def build_corpus(root=ROOT):
    root = Path(root)
    specs = {case["id"]: case for case in cases()}
    files = {
        root / "tests/profiles" / (INTEGER_MODEL_PROFILE.replace("-", "_") + ".f90"):
            ("program intrinsics_16_9_l_integer_model_4_8_distinct\n"
             "  use iso_fortran_env, only: integer_kinds\n"
             "  implicit none\n"
             "  if (.not. any(integer_kinds == 4)) stop 77\n"
             "  if (.not. any(integer_kinds == 8)) stop 77\n"
             "  if (digits(0_4) == digits(0_8)) stop 77\n"
             "end program intrinsics_16_9_l_integer_model_4_8_distinct\n").encode("ascii"),
        root / "tests/profiles" / (REAL_MODEL_PROFILE.replace("-", "_") + ".f90"):
            ("program intrinsics_16_9_l_real_binary_4_8_distinct\n"
             "  use iso_fortran_env, only: real_kinds\n"
             "  implicit none\n"
             "  if (.not. any(real_kinds == 4)) stop 77\n"
             "  if (.not. any(real_kinds == 8)) stop 77\n"
             "  if (radix(0.0_4) /= 2 .or. radix(0.0_8) /= 2) stop 77\n"
             "  if (maxexponent(0.0_4) == maxexponent(0.0_8)) stop 77\n"
             "end program intrinsics_16_9_l_real_binary_4_8_distinct\n").encode("ascii"),
    }
    for spec in specs.values():
        directory = root / "tests/fixtures" / (TOPIC + "_" + spec["variant"])
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
               "## Intrinsics 16.9 L runtime observations\n\n"
               f"The `intrinsics_16_9_l` generator supplies {len(selected_here)} requirement bindings "
               f"covering {facet_count} portable facets in this section. Oracles use direct intrinsic-expression "
               "kind/shape inquiries, exact ASCII code points, bit-context IALL/IAND checks, NOT(0_kind) "
               "for IALL zero-size identity, and HUGE model decomposition under explicit profiles. "
               "Enumeration HUGE, HYPOT approximation latitude, non-ASCII IACHAR values, and IAND invalid-call "
               "restrictions remain pending where no portable runtime oracle is available.\n" + SUMMARY_END)
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
            raise ValueError("stale intrinsics_16_9_l fixtures: " + ", ".join(stale))
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
        "iand_result_kind",
        "iand_boz_conversion",
        "iall_argument_controls",
        "iall_result_characteristics",
        "iall_mask_reduction",
        "iall_dim_reduction",
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
    workspace = root / ".intrinsics_16_9_l_mutations" / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    report = []
    try:
        for case_index, spec in enumerate(specs.values(), 1):
            case_dir = workspace / f"{case_index:03d}_{spec['variant']}"
            case_dir.mkdir()
            parent = run_source(compiler, std, case_dir, spec["source"], spec["completion"])
            if parent["status"] != "pass":
                if spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set()):
                    for mutation in spec["mutations"]:
                        report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                           parent_ok=False, skipped=True, failed=True,
                                           status="known-parent-failure", stdout=parent["stdout"],
                                           stderr=parent["stderr"], returncode=parent["returncode"]))
                    continue
                report.append(dict(variant=spec["variant"], mutation="<parent>", facet="<parent>",
                                   parent_ok=False, failed=False, status=parent["status"],
                                   stdout=parent["stdout"], stderr=parent["stderr"],
                                   returncode=parent["returncode"]))
                continue
            for index, mutation in enumerate(spec["mutations"]):
                mutant_dir = case_dir / f"mut_{index:03d}"
                mutant_dir.mkdir()
                mutant = spec["source"] if inject_survivor and not report else mutated_source(spec, mutation).decode("ascii")
                observed = run_source(compiler, std, mutant_dir, mutant, spec["completion"])
                failed = observed["status"] == "run-fail"
                report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                   parent_ok=True, failed=failed, status=observed["status"],
                                   stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"]))
        bad = [row for row in report
               if (not row["parent_ok"] and not row.get("skipped")) or not row["failed"] or row["status"] == "compile-fail"]
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
        print(f"Mutation-checked {len(report) - skipped}/{len(report) - skipped} intrinsics_16_9_l mutants; "
              f"{skipped} skipped for known parent failures.")
        return
    files, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_l cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
