#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.2 through 16.9.10."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha, wrong_oracle_source

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_a"
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9 A FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9 A FIXTURES -->"
SECTIONS = (
    "16.9.2", "16.9.3", "16.9.4", "16.9.5", "16.9.6", "16.9.7", "16.9.8", "16.9.9", "16.9.10")
CATALOGUES = {
    "16.9.2": "doc/catalogues/abs_intrinsic_16_9_2.json",
    "16.9.3": "doc/catalogues/achar_intrinsic_16_9_3.json",
    "16.9.4": "doc/catalogues/acos_intrinsic_16_9_4.json",
    "16.9.5": "doc/catalogues/acosd_intrinsic_16_9_5.json",
    "16.9.6": "doc/catalogues/acosh_intrinsic_16_9_6.json",
    "16.9.7": "doc/catalogues/acospi_intrinsic_16_9_7.json",
    "16.9.8": "doc/catalogues/adjustl_16_9_8.json",
    "16.9.9": "doc/catalogues/adjustr_16_9_9.json",
    "16.9.10": "doc/catalogues/aimag_16_9_10.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}

SELECTED = {
    "S16.9.2-001": ("positive-control", ("abs-argument-integer-real-or-complex",)),
    "S16.9.2-002": ("effect", ("abs-integer-result-characteristics", "abs-real-result-characteristics",
                                 "abs-complex-result-real-characteristics")),
    "S16.9.2-003": ("effect", ("abs-integer-negative-to-positive", "abs-integer-nonnegative-unchanged",
                                 "abs-real-exact-sign-removal")),
    "S16.9.3-001": ("positive-control", ("achar-i-argument-integer",)),
    "S16.9.3-002": ("effect", ("achar-result-length-one",)),
    "S16.9.3-003": ("effect", ("achar-ascii-code-88-is-x", "achar-ascii-digit-and-letter-codes")),
    "S16.9.3-005": ("effect", ("achar-iachar-default-character-roundtrip",)),
    "S16.9.4-001": ("positive-control", ("acos-argument-admissible",)),
    "S16.9.4-002": ("effect", ("acos-result-characteristics-same-as-x",)),
    "S16.9.4-004": ("effect", ("acos-real-result-radians-range", "acos-complex-real-part-radians-range")),
    "S16.9.5-001": ("positive-control", ("acosd-argument-admissible",)),
    "S16.9.5-002": ("effect", ("acosd-result-characteristics-same-as-x",)),
    "S16.9.5-004": ("effect", ("acosd-result-degrees-range",)),
    "S16.9.6-001": ("positive-control", ("acosh-argument-admissible",)),
    "S16.9.6-002": ("effect", ("acosh-result-characteristics-same-as-x",)),
    "S16.9.6-004": ("effect", ("acosh-complex-real-part-nonnegative",
                                 "acosh-complex-imaginary-part-radians-range")),
    "S16.9.7-001": ("positive-control", ("acospi-argument-admissible",)),
    "S16.9.7-002": ("effect", ("acospi-result-characteristics-same-as-x",)),
    "S16.9.7-004": ("effect", ("acospi-result-half-revolutions-range",)),
    "S16.9.8-003": ("positive-control", ("string-character-argument",)),
    "S16.9.8-004": ("effect", ("result-same-length",)),
    "S16.9.8-005": ("effect", ("leading-blanks-deleted", "trailing-blanks-inserted")),
    "S16.9.9-003": ("positive-control", ("string-character-argument",)),
    "S16.9.9-004": ("effect", ("result-same-length",)),
    "S16.9.9-005": ("effect", ("trailing-blanks-deleted", "leading-blanks-inserted")),
    "S16.9.10-003": ("positive-control", ("z-complex-argument",)),
    "S16.9.10-004": ("effect", ("result-real-type", "result-same-kind-as-z")),
    "S16.9.10-005": ("effect", ("imaginary-component-value",)),
}

VARIANTS = {
    "abs_argument_control": "S16.9.2-001",
    "abs_result_characteristics": "S16.9.2-002",
    "abs_integer_real_values": "S16.9.2-003",
    "achar_argument_control": "S16.9.3-001",
    "achar_result_characteristics": "S16.9.3-002",
    "achar_ascii_mapping": "S16.9.3-003",
    "achar_iachar_roundtrip": "S16.9.3-005",
    "acos_argument_control": "S16.9.4-001",
    "acos_result_characteristics": "S16.9.4-002",
    "acos_result_ranges": "S16.9.4-004",
    "acosd_argument_control": "S16.9.5-001",
    "acosd_result_characteristics": "S16.9.5-002",
    "acosd_result_range": "S16.9.5-004",
    "acosh_argument_control": "S16.9.6-001",
    "acosh_result_characteristics": "S16.9.6-002",
    "acosh_complex_ranges": "S16.9.6-004",
    "acospi_argument_control": "S16.9.7-001",
    "acospi_result_characteristics": "S16.9.7-002",
    "acospi_result_range": "S16.9.7-004",
    "adjustl_argument_control": "S16.9.8-003",
    "adjustl_result_characteristics": "S16.9.8-004",
    "adjustl_blank_movement": "S16.9.8-005",
    "adjustr_argument_control": "S16.9.9-003",
    "adjustr_result_characteristics": "S16.9.9-004",
    "adjustr_blank_movement": "S16.9.9-005",
    "aimag_argument_control": "S16.9.10-003",
    "aimag_result_characteristics": "S16.9.10-004",
    "aimag_imaginary_component": "S16.9.10-005",
}

COMPLETIONS = {name: "INTRINSICS 16.9 A " + name.upper().replace("_", " ") + " OK\n" for name in VARIANTS}

ORACLE_PREFIXES = {rule: f"{rule} intrinsics_16_9_a runtime fixture: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} intrinsics_16_9_a fixture boundaries: " for rule in SELECTED}
RESTORED_PENDING = {
    "S16.9.3-001": {
        "achar-kind-argument-scalar-integer-constant":
            "Left pending after fixture review: a valid call with KIND=KIND('A') is not load-bearing, "
            "and Fortran does not guarantee a supported nondefault character kind for a portable "
            "feature mutation. A future character-kind profile may claim this facet."
    },
    "S16.9.3-002": {
        "achar-result-default-character-kind-when-kind-absent":
            "Left pending after fixture review: KIND(ACHAR(88)) can be queried directly, but no "
            "portable, conforming feature mutation changes the result kind because no nondefault "
            "character kind is guaranteed. A future character-kind profile may claim this facet."
    },
    "S16.9.8-004": {
        "result-same-kind":
            "Left pending after fixture review: KIND(ADJUSTL(STRING)) can be queried directly, but "
            "no portable, conforming feature mutation changes the character kind when only default "
            "character kind support is guaranteed. A future character-kind profile may claim this facet."
    },
    "S16.9.9-004": {
        "result-same-kind":
            "Left pending after fixture review: KIND(ADJUSTR(STRING)) can be queried directly, but "
            "no portable, conforming feature mutation changes the character kind when only default "
            "character kind support is guaranteed. A future character-kind profile may claim this facet."
    },
}

ORACLES = {
    "S16.9.2-001": ORACLE_PREFIXES["S16.9.2-001"] +
        "one positive-control program calls ABS with integer, real, and complex actual arguments and observes nonzero, finite, source-derived results, proving the selected admissible forms are reached without claiming any diagnostic for inadmissible forms.",
    "S16.9.2-002": ORACLE_PREFIXES["S16.9.2-002"] +
        "one program uses nondefault selected integer and real kinds and a complex value of the same real kind. It checks KIND(ABS(integer)) equals the integer kind, KIND(ABS(real)) equals the real kind, and ABS(complex) is assignable to REAL of the complex kind with KIND(ABS(complex)) equal to that kind; no nontrivial complex magnitude equality is asserted.",
    "S16.9.2-003": ORACLE_PREFIXES["S16.9.2-003"] +
        "one exact-value program initializes integer and real operands to nonzero sentinels, then verifies ABS(-7)=7, ABS(5)=5, ABS(-2.0)=2.0, and ABS(3.0)=3.0. All real values are exactly representable small integers.",
    "S16.9.3-001": ORACLE_PREFIXES["S16.9.3-001"] +
        "one positive-control program calls ACHAR with integer I values and checks length and character values for representable ASCII positions. The optional KIND argument facet remains pending because no portable nondefault character kind exists for a load-bearing feature mutation.",
    "S16.9.3-002": ORACLE_PREFIXES["S16.9.3-002"] +
        "one program checks LEN(ACHAR(88)) == 1 directly on the intrinsic expression, with an exact 'X' value control. The default-kind-when-absent facet remains pending because no portable nondefault character kind exists for a load-bearing feature mutation.",
    "S16.9.3-003": ORACLE_PREFIXES["S16.9.3-003"] +
        "one program checks representable default-character ASCII mappings ACHAR(88)='X', ACHAR(48)='0', ACHAR(65)='A', and ACHAR(122)='z', asserting LEN == 1 before each equality so blank padding cannot satisfy the oracle.",
    "S16.9.3-005": ORACLE_PREFIXES["S16.9.3-005"] +
        "one program round-trips default characters 'A', 'z', '0', and '_' through ACHAR(IACHAR(C)), checking LEN == 1 and exact equality for each nonblank sample.",
    "S16.9.4-001": ORACLE_PREFIXES["S16.9.4-001"] +
        "one positive-control program calls ACOS with admissible real values satisfying |X| <= 1 and with a complex value, checking only source-stated range properties and not exact transcendental results.",
    "S16.9.4-002": ORACLE_PREFIXES["S16.9.4-002"] +
        "one program uses selected real kind RK and complex(kind=RK) operands, checking KIND(ACOS(real)) == RK and KIND(ACOS(complex)) == RK while avoiding exact arccosine values.",
    "S16.9.4-004": ORACLE_PREFIXES["S16.9.4-004"] +
        "one range program checks a real ACOS result is between 0 and 4 (a portable consequence of 0 <= result <= pi) and that REAL(ACOS(complex)) is between 0 and 4. It also rejects NaN by using ordinary comparisons; no exact result value is asserted.",
    "S16.9.5-001": ORACLE_PREFIXES["S16.9.5-001"] +
        "one positive-control program calls ACOSD with admissible real values satisfying |X| <= 1 and checks only the source-stated [0,180] range.",
    "S16.9.5-002": ORACLE_PREFIXES["S16.9.5-002"] +
        "one program uses selected real kind RK and checks KIND(ACOSD(X)) == RK without comparing a rounded degree value exactly.",
    "S16.9.5-004": ORACLE_PREFIXES["S16.9.5-004"] +
        "one program checks ACOSD values for admissible inputs lie in the exact source range 0 <= result <= 180 and uses no exact transcendental equality.",
    "S16.9.6-001": ORACLE_PREFIXES["S16.9.6-001"] +
        "one positive-control program calls ACOSH with real and complex arguments and observes only nonnegative/range properties, not exact inverse-hyperbolic-cosine values.",
    "S16.9.6-002": ORACLE_PREFIXES["S16.9.6-002"] +
        "one program uses selected real kind RK and complex(kind=RK) operands, checking KIND(ACOSH(real)) == RK and KIND(ACOSH(complex)) == RK without exact value comparisons.",
    "S16.9.6-004": ORACLE_PREFIXES["S16.9.6-004"] +
        "one complex ACOSH program checks REAL(result) >= 0 and -4 <= AIMAG(result) <= 4, a portable wider bound implied by the source's -pi through pi range, while rejecting NaN through comparisons and avoiding exact rounded values.",
    "S16.9.7-001": ORACLE_PREFIXES["S16.9.7-001"] +
        "one positive-control program calls ACOSPI with admissible real values satisfying |X| <= 1 and checks only the source-stated [0,1] range.",
    "S16.9.7-002": ORACLE_PREFIXES["S16.9.7-002"] +
        "one program uses selected real kind RK and checks KIND(ACOSPI(X)) == RK without relying on exact half-revolution approximation values.",
    "S16.9.7-004": ORACLE_PREFIXES["S16.9.7-004"] +
        "one program checks ACOSPI values for admissible inputs lie in the exact source range 0 <= result <= 1 and uses no exact transcendental equality.",
    "S16.9.8-003": ORACLE_PREFIXES["S16.9.8-003"] +
        "one positive-control program calls ADJUSTL with a character argument, checks LEN(result)==5 before exact character equality, and then checks the exact adjusted value, without claiming a diagnostic for noncharacter arguments.",
    "S16.9.8-004": ORACLE_PREFIXES["S16.9.8-004"] +
        "one program initializes a length-5 default-character string and checks LEN(ADJUSTL(STRING))==5 directly on the intrinsic expression together with exact value 'AB#  '. The same-kind facet remains pending because no portable nondefault character kind exists for a load-bearing feature mutation.",
    "S16.9.8-005": ORACLE_PREFIXES["S16.9.8-005"] +
        "one program checks ADJUSTL('  AB#') with split assertions: VERIFY(result,' ')==1 proves leading blanks were deleted, and after a LEN(result)==5 guard the substring result(4:5)=='  ' proves the same number of trailing blanks were inserted. The feature mutants ADJUSTL->ADJUSTR and ADJUSTL->TRIM(ADJUSTL)//'QQ' distinguish deletion from insertion.",
    "S16.9.9-003": ORACLE_PREFIXES["S16.9.9-003"] +
        "one positive-control program calls ADJUSTR with a character argument, checks LEN(result)==5 before exact character equality, and then checks the exact adjusted value, without claiming a diagnostic for noncharacter arguments.",
    "S16.9.9-004": ORACLE_PREFIXES["S16.9.9-004"] +
        "one program initializes a length-5 default-character string and checks LEN(ADJUSTR(STRING))==5 directly on the intrinsic expression together with exact value '  AB#'. The same-kind facet remains pending because no portable nondefault character kind exists for a load-bearing feature mutation.",
    "S16.9.9-005": ORACLE_PREFIXES["S16.9.9-005"] +
        "one program checks ADJUSTR('AB#  ') with split assertions: VERIFY(result,' ',BACK=.TRUE.)==5 proves trailing blanks were deleted, and after a LEN(result)==5 guard the substring result(1:2)=='  ' proves the same number of leading blanks were inserted. The feature mutants ADJUSTR->ADJUSTL and ADJUSTR->TRIM(source)//'QQ' distinguish deletion from insertion.",
    "S16.9.10-003": ORACLE_PREFIXES["S16.9.10-003"] +
        "one positive-control program calls AIMAG with complex arguments and observes exact imaginary components, without claiming a diagnostic for noncomplex arguments.",
    "S16.9.10-004": ORACLE_PREFIXES["S16.9.10-004"] +
        "one program uses complex(kind=RK), checks TYPE_CODE(AIMAG(Z)) resolves to the real-kind specific procedure, checks KIND(AIMAG(Z)) == RK, assigns AIMAG(Z) to a REAL(kind=RK) variable, and verifies an exact small-integer component value. Feature mutations replace AIMAG(Z) with Z in the generic call and with default-kind REAL(AIMAG(Z)) in the kind inquiry.",
    "S16.9.10-005": ORACLE_PREFIXES["S16.9.10-005"] +
        "one program initializes Z as CMPLX(2.0_RK,-3.0_RK,KIND=RK), then checks AIMAG(Z) equals -3.0_RK exactly, distinguishing the imaginary component from REAL(Z).",
}
LIMITATIONS = {rule: LIMIT_PREFIXES[rule] +
    "Only the listed portable positive-control or effect facets are discharged. Unnumbered restrictions have no invalid diagnostic claim. Processor-dependent approximations, exact transcendental values, IEEE flag behavior, deferred-length command/environment assignment, out-of-range ACHAR results, and characteristics needing an unavailable guaranteed nondefault character kind remain pending where applicable."
    for rule in SELECTED}

SOURCE_ONLY_PATTERNS = [
    ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no processor, approves no fixture or oracle, and claims no coverage.",
     "The original source-only catalogue recorded pending plans only. This intrinsics_16_9_a generator supplies selected runtime fixtures and mutation plans without granting fixture approval, oracle approval, source-review renewal, or universal coverage."),
    ("Source accounting only. This packet creates no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.",
     "Original source accounting created no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim; this intrinsics_16_9_a generator supplies selected runtime fixtures and mutation plans without granting those approvals or universal coverage."),
    ("No fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim is created by this packet.",
     "This catalogue originally created no fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim; this intrinsics_16_9_a generator now supplies selected runtime fixtures and mutation plans without granting those approvals or universal coverage."),
]


def identifier(variant):
    rule = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__intrinsics_16_9_a_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule = VARIANTS[variant]
        self.evidence, facets = SELECTED[self.rule]
        self.facets = list(facets)
        self.text = ""
        self.guards = []
        self.observations = []
        self.mutations = []
        self.contains = ""

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def token(self, name):
        return "I16A:" + self.variant + ":" + name

    def fail_block(self, token):
        return f"    write(*,'(a)') '{token}'\n    error stop\n"

    def guard_true(self, name, condition, replacement=".false.", category="property", count=True):
        block_start = len(self.text)
        prefix = "  if (.not. ("
        start = block_start + len(prefix)
        token = self.token(name)
        self.add(prefix + condition + ")) then\n" + self.fail_block(token) + "  end if\n")
        if count:
            self.add("  checks=checks+1\n")
        guard = dict(id=name, guard_id=name, kind="guard", category=category, span=[start, start + len(condition)],
                     expected=condition, replacement=replacement, line=self.text[:start].count("\n") + 1,
                     mutation="guard-condition-replacement", failure_token=token, failure_stdout=token + "\n",
                     block_span=[block_start, len(self.text)])
        self.guards.append(guard)
        if count:
            self.observations.append(guard)
        self.mutations.append(dict(guard))
        return guard

    def guard_eq(self, name, expression, expected, replacement, category="value", count=True):
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        expected, replacement = str(expected), str(replacement)
        start = block_start + len(prefix)
        token = self.token(name)
        self.add(prefix + expected + ") then\n" + self.fail_block(token) + "  end if\n")
        if count:
            self.add("  checks=checks+1\n")
        guard = dict(id=name, guard_id=name, kind="guard", category=category, expression=expression,
                     span=[start, start + len(expected)], expected=expected, replacement=replacement,
                     line=self.text[:start].count("\n") + 1, mutation="guard-literal-replacement",
                     failure_token=token, failure_stdout=token + "\n", block_span=[block_start, len(self.text)])
        self.guards.append(guard)
        if count:
            self.observations.append(guard)
        self.mutations.append(dict(guard))
        return guard

    def guard_char(self, name, expression, expected, replacement):
        return self.guard_eq(name, expression, "'" + expected + "'", "'" + replacement + "'", category="character")

    def assignment(self, variable, expression):
        prefix = f"  {variable} = "
        start = len(self.text) + len(prefix)
        self.add(prefix + expression + "\n")
        return [start, start + len(expression)]

    def source_probe(self, name, span, expected, replacement, failure_guard, mutation="source-feature-mutation"):
        probe = dict(id=name, guard_id=failure_guard["id"], kind="source", category="feature", span=span,
                     expected=expected, replacement=replacement, line=self.text[:span[0]].count("\n") + 1,
                     guard_line=failure_guard["line"], mutation=mutation,
                     failure_token=failure_guard["failure_token"], failure_stdout=failure_guard["failure_stdout"])
        self.mutations.append(probe)
        return probe

    def completion(self):
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        self.add(prefix + literal + "'\n")
        guard = dict(id="completion-output", guard_id="completion-output", kind="output", category="completion",
                     span=[start, start + len(literal)], expected=literal,
                     replacement=literal.replace(" OK", " BAD"), line=self.text[:start].count("\n") + 1,
                     mutation="completion-literal-replacement", block_span=[start - len(prefix), len(self.text)],
                     failure_stdout="")
        self.guards.append(guard)
        self.mutations.append(dict(guard))
        return guard


def begin(p):
    p.add(f"! rule: {p.rule}\n")
    for facet in p.facets:
        p.add(f"! covers: {facet}\n")
    p.add("! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.\n")
    p.add(f"program intrinsics_16_9_a_{p.variant}\n  implicit none\n  integer :: checks\n")


def finish(p):
    total = p.guard_eq("check-total", "checks", len(p.observations), len(p.observations) + 1,
                       "completion", count=False)
    completion = p.completion()
    if p.contains:
        p.add(p.contains)
    p.add(f"end program intrinsics_16_9_a_{p.variant}\n")
    omissions = []
    start, end = completion["block_span"]
    omissions.append(dict(id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
                          span=[start, end], expected=p.text[start:end], replacement="",
                          line=p.text[:start].count("\n") + 1, mutation="completion-statement-omission",
                          failure_stdout=""))
    for guard in p.observations:
        start, end = guard["block_span"]
        omissions.append(dict(id="omit-observation-" + guard["id"], guard_id=total["id"], kind="guard",
                              category="omission", span=[start, end], expected=p.text[start:end], replacement="",
                              line=p.text[:start].count("\n") + 1, guard_line=total["line"],
                              mutation="whole-observation-omission", failure_token=total["failure_token"],
                              failure_stdout=total["failure_stdout"]))
    p.mutations.extend(omissions)
    return omissions


def kind_guard_with_feature(p, name, expression, expected, replacement_expr):
    guard = p.guard_eq(name, f"kind({expression})", expected, expected + "+1", category="kind")
    target = f"kind({expression})"
    start = p.text.index(target, guard["block_span"][0]) + len("kind(")
    p.source_probe("feature-" + name, [start, start + len(expression)], expression, replacement_expr, guard,
                   mutation="intrinsic-kind-expression-substitution")
    return guard


def program(variant):
    p = Program(variant)
    begin(p)
    v = variant
    if v == "abs_argument_control":
        p.add("  integer :: iv\n  real :: rv, cv\n  checks=0\n")
        p.assignment("iv", "abs(-7)")
        p.assignment("rv", "abs(-2.0)")
        span = p.assignment("cv", "abs(cmplx(0.0,-3.0))")
        g = p.guard_true("all-admissible-forms", "iv == 7 .and. rv == 2.0 .and. cv > 0.0")
        p.source_probe("complex-abs-to-aimag", span, "abs(cmplx(0.0,-3.0))", "aimag(cmplx(0.0,-3.0))", g)
    elif v == "abs_result_characteristics":
        p.add("  integer, parameter :: ik = selected_int_kind(18)\n")
        p.add("  integer, parameter :: rk = selected_real_kind(10)\n")
        p.add("  integer(kind=ik) :: i\n  real(kind=rk) :: x, cabs\n  complex(kind=rk) :: z\n  checks=0\n")
        p.add("  i = -7_ik\n  x = -2.0_rk\n  z = cmplx(0.0_rk, -2.0_rk, kind=rk)\n")
        kind_guard_with_feature(p, "integer-kind", "abs(i)", "ik", "int(abs(i), kind=kind(0))")
        kind_guard_with_feature(p, "real-kind", "abs(x)", "rk", "real(abs(real(x)), kind=kind(1.0))")
        kind_guard_with_feature(p, "complex-result-kind", "abs(z)", "rk", "int(abs(z))")
        span = p.assignment("cabs", "abs(z)")
        g = p.guard_true("complex-real-assignment", "cabs >= 0.0_rk")
        p.source_probe("complex-abs-to-aimag", span, "abs(z)", "aimag(z)", g)
    elif v == "abs_integer_real_values":
        p.add("  integer :: neg_i, pos_i\n  real :: neg_r, pos_r\n  checks=0\n")
        p.add("  neg_i = -7\n  pos_i = 5\n  neg_r = -2.0\n  pos_r = 3.0\n")
        span = p.assignment("neg_i", "abs(neg_i)")
        g = p.guard_eq("integer-negative", "neg_i", 7, -7)
        p.source_probe("negative-abs-to-identity", span, "abs(neg_i)", "neg_i", g)
        p.assignment("pos_i", "abs(pos_i)")
        g = p.guard_eq("integer-positive", "pos_i", 5, -5)
        positive_span = [
            p.text.index("abs(pos_i)"),
            p.text.index("abs(pos_i)") + len("abs(pos_i)")]
        p.source_probe("positive-abs-to-negation", positive_span, "abs(pos_i)", "-pos_i", g)
        span = p.assignment("neg_r", "abs(neg_r)")
        g = p.guard_eq("real-negative", "neg_r", "2.0", "-2.0")
        p.source_probe("real-abs-to-identity", span, "abs(neg_r)", "neg_r", g)
        p.assignment("pos_r", "abs(pos_r)")
        g = p.guard_eq("real-positive", "pos_r", "3.0", "-3.0")
        positive_span = [
            p.text.index("abs(pos_r)"),
            p.text.index("abs(pos_r)") + len("abs(pos_r)")]
        p.source_probe("positive-real-abs-to-negation", positive_span, "abs(pos_r)", "-pos_r", g)
    elif v == "achar_argument_control":
        p.add("  character(len=1) :: c\n  checks=0\n")
        span = p.assignment("c", "achar(88)")
        g = p.guard_true("integer-i-argument", "len(c) == 1 .and. c == 'X'")
        p.source_probe("achar-i-code-perturb", span, "achar(88)", "achar(89)", g)
    elif v == "achar_result_characteristics":
        p.add("  character(len=1) :: c\n  checks=0\n")
        span = p.assignment("c", "achar(88)")
        g = p.guard_eq("length-one", "len(achar(88))", 1, 2, category="length")
        length_span = [
            p.text.index("achar(88)", g["block_span"][0]),
            p.text.index("achar(88)", g["block_span"][0]) + len("achar(88)")]
        p.source_probe("length-expression-concat", length_span, "achar(88)", "achar(88)//'Q'", g)
        g = p.guard_char("value-control", "c", "X", "Y")
        p.source_probe("achar-code-perturb", span, "achar(88)", "achar(89)", g)
    elif v == "achar_ascii_mapping":
        p.add("  character(len=1) :: x, zero, upper, lower\n  checks=0\n")
        span = p.assignment("x", "achar(88)")
        p.assignment("zero", "achar(48)")
        p.assignment("upper", "achar(65)")
        p.assignment("lower", "achar(122)")
        g = p.guard_true("lengths-one", "len(x)==1 .and. len(zero)==1 .and. len(upper)==1 .and. len(lower)==1")
        p.guard_char("code-88-x", "x", "X", "Y")
        digit_guard = p.guard_char("digit-zero", "zero", "0", "1")
        upper_guard = p.guard_char("letter-a", "upper", "A", "B")
        lower_guard = p.guard_char("letter-z", "lower", "z", "y")
        p.source_probe("x-code-perturb", span, "achar(88)", "achar(89)", p.guards[-4])
        zero_start = p.text.index("achar(48)")
        p.source_probe("zero-code-perturb", [zero_start, zero_start + len("achar(48)")],
                       "achar(48)", "achar(49)", digit_guard)
        upper_start = p.text.index("achar(65)")
        p.source_probe("upper-code-perturb", [upper_start, upper_start + len("achar(65)")],
                       "achar(65)", "achar(66)", upper_guard)
        lower_start = p.text.index("achar(122)")
        p.source_probe("lower-code-perturb", [lower_start, lower_start + len("achar(122)")],
                       "achar(122)", "achar(121)", lower_guard)
    elif v == "achar_iachar_roundtrip":
        p.add("  character(len=1) :: a, z, zero, under\n  checks=0\n")
        span = p.assignment("a", "achar(iachar('A'))")
        g = p.guard_true("roundtrip-a", "len(a) == 1 .and. a == 'A'")
        p.source_probe("roundtrip-a-perturb", span, "achar(iachar('A'))", "achar(iachar('B'))", g)
        p.assignment("z", "achar(iachar('z'))")
        p.guard_true("roundtrip-z", "len(z) == 1 .and. z == 'z'")
        p.assignment("zero", "achar(iachar('0'))")
        p.guard_true("roundtrip-zero", "len(zero) == 1 .and. zero == '0'")
        p.assignment("under", "achar(iachar('_'))")
        p.guard_true("roundtrip-underscore", "len(under) == 1 .and. under == '_'")
    elif v.startswith("acos_"):
        acos_program(p, v, "acos", "4.0_rk")
    elif v.startswith("acosd_"):
        real_arc_program(p, v, "acosd", "180.0_rk")
    elif v.startswith("acosh_"):
        acosh_program(p, v)
    elif v.startswith("acospi_"):
        real_arc_program(p, v, "acospi", "1.0_rk")
    elif v.startswith("adjustl_"):
        adjust_program(p, v, "adjustl", "  AB#", "AB#  ", "adjustr")
    elif v.startswith("adjustr_"):
        adjust_program(p, v, "adjustr", "AB#  ", "  AB#", "adjustl")
    elif v.startswith("aimag_"):
        aimag_program(p, v)
    else:
        raise ValueError("unknown variant " + v)
    omissions = finish(p)
    return finalize(p, omissions)


def acos_program(p, variant, intrinsic, upper):
    p.add("  integer, parameter :: rk = selected_real_kind(10)\n")
    if variant.endswith("argument_control"):
        p.add("  real(kind=rk) :: xr, rr\n  complex(kind=rk) :: z, rz\n  checks=0\n")
        p.add("  xr = 0.25_rk\n  z = cmplx(0.25_rk, 0.5_rk, kind=rk)\n")
        p.assignment("rr", "acos(xr)")
        span = p.assignment("rz", "acos(z)")
        g = p.guard_true("admissible-real-complex", "rr >= 0.0_rk .and. rr <= 4.0_rk .and. real(rz) >= 0.0_rk .and. real(rz) <= 4.0_rk")
        p.source_probe("complex-acos-negate", span, "acos(z)", "-acos(z)", g)
    elif variant.endswith("result_characteristics"):
        p.add("  real(kind=rk) :: x\n  complex(kind=rk) :: z\n  checks=0\n")
        p.add("  x = 0.25_rk\n  z = cmplx(0.25_rk, 0.5_rk, kind=rk)\n")
        kind_guard_with_feature(p, "real-result-kind", "acos(x)", "rk", "real(acos(real(x)), kind=kind(1.0))")
        kind_guard_with_feature(p, "complex-result-kind", "acos(z)", "rk", "cmplx(real(acos(z)), aimag(acos(z)), kind=kind(1.0))")
    else:
        p.add("  real(kind=rk) :: x, rr\n  complex(kind=rk) :: z, rz\n  checks=0\n")
        p.add("  x = 0.25_rk\n  z = cmplx(0.25_rk, 0.5_rk, kind=rk)\n")
        span = p.assignment("rr", "acos(x)")
        g = p.guard_true("real-radians-range", "rr >= 0.0_rk .and. rr <= 4.0_rk")
        p.source_probe("real-acos-negate", span, "acos(x)", "-acos(x)", g)
        span = p.assignment("rz", "acos(z)")
        g = p.guard_true("complex-real-part-range", "real(rz) >= 0.0_rk .and. real(rz) <= 4.0_rk")
        p.source_probe("complex-acos-negate", span, "acos(z)", "-acos(z)", g)


def real_arc_program(p, variant, intrinsic, upper):
    if intrinsic == "acospi":
        p.add("  integer, parameter :: rk = selected_real_kind(10)\n")
        p.add("  real(kind=rk), parameter :: x = 0.25_rk\n  real(kind=rk) :: y\n  checks=0\n")
    else:
        p.add("  integer, parameter :: rk = selected_real_kind(10)\n  real(kind=rk) :: x, y\n  checks=0\n")
        p.add("  x = 0.25_rk\n")
    if variant.endswith("argument_control"):
        span = p.assignment("y", f"{intrinsic}(x)")
        g = p.guard_true("admissible-real", f"y >= 0.0_rk .and. y <= {upper}")
        p.source_probe("negated-call", span, f"{intrinsic}(x)", f"-{intrinsic}(x)", g)
    elif variant.endswith("result_characteristics"):
        kind_guard_with_feature(p, "result-kind", f"{intrinsic}(x)", "rk", f"real({intrinsic}(real(x)), kind=kind(1.0))")
    else:
        span = p.assignment("y", f"{intrinsic}(x)")
        g = p.guard_true("source-range", f"y >= 0.0_rk .and. y <= {upper}")
        p.source_probe("negated-call", span, f"{intrinsic}(x)", f"-{intrinsic}(x)", g)


def acosh_program(p, variant):
    p.add("  integer, parameter :: rk = selected_real_kind(10)\n")
    if variant.endswith("argument_control"):
        p.add("  real(kind=rk) :: xr, rr\n  complex(kind=rk) :: z, rz\n  checks=0\n")
        p.add("  xr = 2.0_rk\n  z = cmplx(0.25_rk, 0.5_rk, kind=rk)\n")
        p.assignment("rr", "acosh(xr)")
        span = p.assignment("rz", "acosh(z)")
        g = p.guard_true("complex-argument-range", "real(rz) >= 0.0_rk .and. aimag(rz) >= -4.0_rk .and. aimag(rz) <= 4.0_rk")
        p.source_probe("complex-acosh-negate", span, "acosh(z)", "-acosh(z)", g)
    elif variant.endswith("result_characteristics"):
        p.add("  real(kind=rk) :: x\n  complex(kind=rk) :: z\n  checks=0\n")
        p.add("  x = 2.0_rk\n  z = cmplx(0.25_rk, 0.5_rk, kind=rk)\n")
        kind_guard_with_feature(p, "real-result-kind", "acosh(x)", "rk", "real(acosh(real(x)), kind=kind(1.0))")
        kind_guard_with_feature(p, "complex-result-kind", "acosh(z)", "rk", "cmplx(real(acosh(z)), aimag(acosh(z)), kind=kind(1.0))")
    else:
        p.add("  complex(kind=rk) :: z, r\n  checks=0\n")
        p.add("  z = cmplx(0.25_rk, 0.5_rk, kind=rk)\n")
        span = p.assignment("r", "acosh(z)")
        g = p.guard_true("complex-real-nonnegative", "real(r) >= 0.0_rk")
        p.source_probe("negated-acosh-real", span, "acosh(z)", "-acosh(z)", g)
        g = p.guard_true("complex-imag-range", "aimag(r) >= -4.0_rk .and. aimag(r) <= 4.0_rk")
        imag_start = p.text.index("acosh(z)")
        p.source_probe("force-imag-out-of-range", [imag_start, imag_start + len("acosh(z)")],
                       "acosh(z)", "cmplx(real(acosh(z)), 5.0_rk, kind=rk)", g)


def adjust_program(p, variant, intrinsic, source, expected, sibling):
    p.add("  character(len=5) :: s, r\n  checks=0\n")
    p.add(f"  s = '{source}'\n")
    span = p.assignment("r", f"{intrinsic}(s)")
    if variant.endswith("argument_control"):
        p.guard_eq("result-length-before-equality", "len(r)", 5, 4, category="length")
        g = p.guard_char("character-argument-result", "r", expected, source)
        p.source_probe("sibling-intrinsic", span, f"{intrinsic}(s)", f"{sibling}(s)", g)
    elif variant.endswith("result_characteristics"):
        g = p.guard_eq("same-length", f"len({intrinsic}(s))", 5, 4, category="length")
        length_start = p.text.index(f"{intrinsic}(s)", g["block_span"][0])
        p.source_probe("length-expression-concat", [length_start, length_start + len(f"{intrinsic}(s)")],
                       f"{intrinsic}(s)", f"{intrinsic}(s)//'Q'", g)
        g = p.guard_char("value-control", "r", expected, source)
        p.source_probe("sibling-intrinsic", span, f"{intrinsic}(s)", f"{sibling}(s)", g)
    else:
        p.guard_eq("result-length-before-equality", "len(r)", 5, 4, category="length")
        if intrinsic == "adjustl":
            g = p.guard_eq("leading-first-nonblank", "verify(r, ' ')", 1, 3, category="position")
            p.source_probe("sibling-intrinsic-leading", span, "adjustl(s)", "adjustr(s)", g)
            g = p.guard_char("trailing-two-blanks", "r(4:5)", "  ", "QQ")
            p.source_probe("trim-concat-no-trailing-blanks", span, "adjustl(s)", "trim(adjustl(s))//'QQ'", g)
        else:
            g = p.guard_eq("trailing-last-nonblank", "verify(r, ' ', back=.true.)", 5, 3,
                           category="position")
            p.source_probe("sibling-intrinsic-trailing", span, "adjustr(s)", "adjustl(s)", g)
            g = p.guard_char("leading-two-blanks", "r(1:2)", "  ", "QQ")
            p.source_probe("trim-concat-no-leading-blanks", span, "adjustr(s)", "trim(s)//'QQ'", g)


def aimag_program(p, variant):
    p.add("  integer, parameter :: rk = selected_real_kind(10)\n")
    p.add("  complex(kind=rk) :: z\n  real(kind=rk) :: y\n")
    if variant.endswith("result_characteristics"):
        p.add("  interface type_code\n    procedure real_code\n    procedure complex_code\n  end interface\n")
    p.add("  checks=0\n")
    p.add("  z = cmplx(2.0_rk, -3.0_rk, kind=rk)\n")
    span = p.assignment("y", "aimag(z)")
    if variant.endswith("argument_control"):
        g = p.guard_eq("complex-argument-value", "y", "-3.0_rk", "2.0_rk")
        p.source_probe("aimag-to-real", span, "aimag(z)", "real(z)", g)
    elif variant.endswith("result_characteristics"):
        g = p.guard_eq("real-type-resolution", "type_code(aimag(z))", 11, 29, category="type")
        type_start = p.text.index("aimag(z)", g["block_span"][0])
        p.source_probe("aimag-to-complex-generic", [type_start, type_start + len("aimag(z)")],
                       "aimag(z)", "z", g)
        g = p.guard_eq("same-kind", "kind(aimag(z))", "rk", "rk+1", category="kind")
        kind_start = p.text.index("aimag(z)", g["block_span"][0])
        p.source_probe("aimag-to-default-real-kind", [kind_start, kind_start + len("aimag(z)")],
                       "aimag(z)", "real(aimag(z), kind(1.0))", g)
        g = p.guard_eq("real-assignment-value", "y", "-3.0_rk", "2.0_rk")
        p.source_probe("aimag-to-real", span, "aimag(z)", "real(z)", g)
        p.contains = (
            "contains\n"
            "  integer function real_code(x)\n"
            "    real(kind=rk), intent(in) :: x\n"
            "    real_code = 11\n"
            "  end function real_code\n"
            "  integer function complex_code(x)\n"
            "    complex(kind=rk), intent(in) :: x\n"
            "    complex_code = 29\n"
            "  end function complex_code\n")
    else:
        g = p.guard_eq("imaginary-component", "y", "-3.0_rk", "2.0_rk")
        p.source_probe("aimag-to-real", span, "aimag(z)", "real(z)", g)


def finalize(p, omissions):
    raw = p.text.encode("ascii")
    for mutation in p.mutations:
        start, end = mutation["span"]
        if mutation["expected"] and raw[start:end].decode("ascii") != mutation["expected"]:
            raise ValueError(f"{p.variant}: mutation span lost complete parent")
    return dict(id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=p.facets, evidence=p.evidence,
                standard="f2023", phase="run", source=p.text, source_sha256=sha(raw),
                completion=COMPLETIONS[p.variant], guards=p.guards, mutations=p.mutations,
                omissions=omissions, observations=p.observations, expected_counts=dict(checks=len(p.observations)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def soften_source_only(text):
    for old, new in SOURCE_ONLY_PATTERNS:
        text = text.replace(old, new)
    return text


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, (evidence, facets) in SELECTED.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet, reason in RESTORED_PENDING.get(rule, {}).items():
            if facet not in owner["facets"]:
                raise ValueError("restored pending facet changed for " + rule)
            owner.setdefault("pending", {})[facet] = reason
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner.setdefault("pending", {})
        owner["oracle"] = soften_source_only(owner.get("oracle", ""))
        owner["oracle_limitation"] = soften_source_only(owner.get("oracle_limitation", ""))
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
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
    before = before.replace("This source packet records source accounting and pending plans only, not fixture approval.",
                            "This source packet records source accounting; selected pending facets now have bounded runtime fixtures, not fixture approval.")
    before = before.replace("This source packet records source accounting and pending plans only, not fixture approval.",
                            "This source packet records source accounting; selected pending facets now have bounded runtime fixtures, not fixture approval.")
    before = before.replace("Clause 16 note: argument restrictions are unnumbered program restrictions and therefore carry no diagnostic fixture plan in this source packet; exact result values remain pending positive-runtime plans.",
                            "Clause 16 note: argument restrictions are unnumbered program restrictions and therefore carry no diagnostic fixture plan; selected exact result facets now have positive-runtime fixtures.")
    selected_here = [rule for rule in SELECTED if rule in {row["id"] for row in catalogue["requirements"]}]
    facet_count = sum(len(SELECTED[rule][1]) for rule in selected_here)
    summary = (SUMMARY_BEGIN + "\n"
               f"## Intrinsics 16.9 A runtime observations\n\n"
               f"The `intrinsics_16_9_a` generator supplies {len(selected_here)} fixture requirement bindings "
               f"covering {facet_count} portable facets in this section. Oracles are limited to exact type/kind/length "
               "inquiries, exact integer/character/small-real effects, and source-stated range inequalities. "
               "Processor-dependent approximations, exact transcendental values, unnumbered negative diagnostics, "
               "and unsupported optional-kind/IEEE/deferred-length cases remain pending.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("summary boundaries changed for " + section)
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
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for path, updated in updated_catalogues.items():
            if json.loads((root / path).read_text()) != updated:
                stale.append(path)
        for path, updated in updated_views.items():
            if (root / path).read_text() != updated:
                stale.append(path)
        if stale:
            raise ValueError("stale intrinsics_16_9_a fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogues:
            for path, updated in updated_catalogues.items():
                (root / path).write_text(json.dumps(updated, indent=2) + "\n")
            for path, updated in updated_views.items():
                (root / path).write_text(updated)
    return files, specs


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    flag = ("--std=" if "lfortran" in name else "-std=") + std if std else ""
    return [str(compiler)] + ([flag] if flag else []) + [str(source), "-o", str(output)]


def run_source(compiler, std, case_dir, source_text, expected_stdout):
    source = case_dir / "source.f90"
    exe = case_dir / "program"
    source.write_text(source_text)
    compile_result = subprocess.run(compiler_command(compiler, std, source, exe), cwd=case_dir,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_result.returncode != 0:
        return dict(status="compile-fail", stdout=compile_result.stdout, stderr=compile_result.stderr,
                    returncode=compile_result.returncode)
    run_result = subprocess.run([str(exe)], cwd=case_dir, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run_result.returncode == 0 and run_result.stdout == expected_stdout and run_result.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run_result.stdout,
                stderr=run_result.stderr, returncode=run_result.returncode)


def mutation_check(root, compiler, std, keep_work=False, inject_survivor=False):
    root = Path(root)
    specs = source_specs()
    workspace = root / ".intrinsics_16_9_a_mutations" / sha((str(compiler) + std).encode())[:12]
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
            for index, mutation in enumerate(spec["mutations"]):
                if mutation.get("span") == [0, 0] and not mutation.get("expected"):
                    continue
                mutant_dir = case_dir / f"mut_{index:03d}"
                mutant_dir.mkdir()
                if inject_survivor and not report:
                    mutant = spec["source"]
                else:
                    mutant = wrong_oracle_source(spec, mutation).decode("ascii")
                observed = run_source(compiler, std, mutant_dir, mutant, spec["completion"])
                failed = observed["status"] != "pass"
                row = dict(variant=spec["variant"], mutation=mutation["id"], kind=mutation["kind"],
                           category=mutation["category"], parent_ok=parent_ok, failed=failed,
                           status=observed["status"], stdout=observed["stdout"], stderr=observed["stderr"],
                           returncode=observed["returncode"])
                report.append(row)
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
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
    if args.inject_surviving_mutant and not args.mutation_check:
        parser.error("--inject-surviving-mutant requires --mutation-check")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work, args.inject_surviving_mutant)
        source = sum(row["kind"] == "source" for row in report)
        print(f"Mutation-checked {len(report)} intrinsics_16_9_a mutants ({source} feature/source); all failed.")
        return
    files, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_a cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
