#!/usr/bin/env python3
"""Exact integer division and character concatenation runtime fixtures."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import (
    owned_paragraph,
    probe_verdict as ordinary_probe_verdict,
    sha,
    wrong_oracle_source,
)


ROOT = Path(__file__).resolve().parents[1]
INT_SECTION = "10.1.5.2.2"
CHAR_SECTION = "10.1.5.3.1"
INT_CATALOGUE = "doc/catalogues/integer_division_10_1_5_2_2.json"
CHAR_CATALOGUE = "doc/catalogues/character_intrinsic_operation_10_1_5_3_1.json"
INT_VIEW = "doc/fortran_2023_10_1_5_2_2.md"
CHAR_VIEW = "doc/fortran_2023_10_1_5_3_1.md"
INT_RULE = "S10.1.5.2.2-001"
CHAR_RULE_TYPE = "S10.1.5.3.1-001"
CHAR_RULE_VALUE = "S10.1.5.3.1-002"
CHAR_RULE_PARENS = "S10.1.5.3.1-003"

INT_VARIANTS = {
    "positive_truncates_toward_zero": "positive-truncates-toward-zero",
    "negative_dividend_truncates_toward_zero": "negative-dividend-truncates-toward-zero",
    "negative_divisor_truncates_toward_zero": "negative-divisor-truncates-toward-zero",
    "exact_integer_division": "exact-integer-division",
}
CHAR_VARIANTS = {
    "default_character_same_kind": (CHAR_RULE_TYPE, "default-character-same-kind"),
    "character_result_type": (CHAR_RULE_TYPE, "character-result-type"),
    "right_append_value": (CHAR_RULE_VALUE, "right-append-value"),
    "result_length_sum": (CHAR_RULE_VALUE, "result-length-sum"),
    "zero_length_left": (CHAR_RULE_VALUE, "zero-length-left"),
    "zero_length_right": (CHAR_RULE_VALUE, "zero-length-right"),
    "left_grouped_concatenation_value": (CHAR_RULE_PARENS, "left-grouped-concatenation-value"),
    "right_grouped_concatenation_value": (CHAR_RULE_PARENS, "right-grouped-concatenation-value"),
    "nested_parentheses_value": (CHAR_RULE_PARENS, "nested-parentheses-value"),
}
VARIANTS = {**{name: (INT_RULE, facet) for name, facet in INT_VARIANTS.items()}, **CHAR_VARIANTS}
INT_FACETS = tuple(INT_VARIANTS.values())
CHAR_FACETS_BY_RULE = {
    CHAR_RULE_TYPE: ("default-character-same-kind", "character-result-type"),
    CHAR_RULE_VALUE: ("right-append-value", "result-length-sum", "zero-length-left", "zero-length-right"),
    CHAR_RULE_PARENS: ("left-grouped-concatenation-value", "right-grouped-concatenation-value", "nested-parentheses-value"),
}
CHAR_REMAINING_PENDING = {
    CHAR_RULE_TYPE: {"nondefault-same-kind-profile", "different-kind-boundary"},
    CHAR_RULE_VALUE: set(),
    CHAR_RULE_PARENS: set(),
}
COMPLETIONS = {
    name: ("EXACT ARITHMETIC " + name.upper().replace("_", " ") + " OK\n")
    for name in VARIANTS
}
INT_ORACLE_PREFIX = "S10.1.5.2.2-001 exact integer division runtime fixtures: "
INT_LIMIT_PREFIX = "S10.1.5.2.2-001 exact integer division fixture boundaries: "
CHAR_TYPE_ORACLE_PREFIX = "S10.1.5.3.1-001 default character concatenation runtime fixtures: "
CHAR_TYPE_LIMIT_PREFIX = "S10.1.5.3.1-001 character type fixture boundaries: "
CHAR_VALUE_ORACLE_PREFIX = "S10.1.5.3.1-002 character concatenation value runtime fixtures: "
CHAR_VALUE_LIMIT_PREFIX = "S10.1.5.3.1-002 character value fixture boundaries: "
CHAR_PARENS_ORACLE_PREFIX = "S10.1.5.3.1-003 character parentheses runtime fixtures: "
CHAR_PARENS_LIMIT_PREFIX = "S10.1.5.3.1-003 character parentheses fixture boundaries: "
INT_SUMMARY_BEGIN = "<!-- BEGIN EXACT INTEGER DIVISION FIXTURES -->"
INT_SUMMARY_END = "<!-- END EXACT INTEGER DIVISION FIXTURES -->"
CHAR_SUMMARY_BEGIN = "<!-- BEGIN CHARACTER CONCATENATION FIXTURES -->"
CHAR_SUMMARY_END = "<!-- END CHARACTER CONCATENATION FIXTURES -->"

INT_ORACLE = INT_ORACLE_PREFIX + (
    "four complete run/effect/f2023 programs use INTEGER operands and the intrinsic division operator /, "
    "then compare the result with independently hand-computed integer literal constants. The cases are "
    "8/3==2, (-8)/3==-2, 8/(-3)==-2 and 8/4==2. Comments in each source show the mathematical quotient "
    "and the standard's closest integer between zero and the quotient. The two negative nonexact cases are "
    "nonvacuous against flooring division: (-8)/3 would floor to -3 and 8/(-3) would floor to -3, but the "
    "standard result is -2. The fixtures use no MOD, MODULO, FLOOR, CEILING, INT, NINT, real or complex "
    "oracle, overflow, division by zero, compiler-consensus oracle, or mathematically-equivalent rewrite. "
    "Each assertion increments a counter and a final total guard precedes exact completion stdout, empty "
    "stderr and exit0. Wrong-oracle mutations cover every guard and completion literal; omissions remove "
    "individual observations or the completion line."
)
INT_LIMITATION = INT_LIMIT_PREFIX + (
    "only the four S10.1.5.2.2-001 integer division facets are represented. Positive 8/3 and exact 8/4 "
    "are included because they are named catalogue facets, but flooring-vs-truncation sensitivity is carried "
    "by the negative dividend and negative divisor cases. The programs do not claim division-by-zero, overflow, "
    "real or complex arithmetic, algebraic rewrite permissions, kind-range boundaries, diagnostics, coarrays, "
    "multi-image behavior, or universal compiler conformance. Generation grants no review approval, evidence "
    "link, baseline update, SourceUse renewal or expected-failure adjudication."
)
CHAR_TYPE_ORACLE = CHAR_TYPE_ORACLE_PREFIX + (
    "two complete run/positive-control/f2023 programs use only default CHARACTER operands. The default-same-kind case "
    "checks KIND(left)==KIND(right), KIND(left//right)==KIND(left), LEN(left//right)==5 and the exact "
    "equal-length value 'AXb7q' from left 'AX' followed by right 'b7q'. The result-type case assigns "
    "left 'R4' // right 's9T' to a declared CHARACTER(LEN=5) variable, then checks the assigned equal-length "
    "value, LEN(result)==5 and KIND(result)==KIND(left). These are runtime type/kind/length witnesses, not "
    "storage-byte or TRANSFER tests."
)
CHAR_TYPE_LIMITATION = CHAR_TYPE_LIMIT_PREFIX + (
    "only default-character-same-kind and character-result-type are represented. nondefault-same-kind-profile "
    "remains pending because Fortran does not require a nondefault character kind to exist, and different-kind-"
    "boundary remains pending because it is a diagnostic/control boundary requiring independently established "
    "distinct character kinds rather than a portable positive runtime effect. No nondefault kind, mixed-kind "
    "diagnostic, TRANSFER, storage layout, address arithmetic, TRIM, INDEX, REPEAT or blank-padded unequal-length "
    "value oracle is used."
)
CHAR_VALUE_ORACLE = CHAR_VALUE_ORACLE_PREFIX + (
    "four complete run/effect/f2023 programs observe Table 10.4 and p3. Distinct default-character operands of "
    "unequal lengths make swapped order and wrong length visible. The right-append case uses left 'AB' and right "
    "'q7Z', expecting LEN 5 and equal-length value 'ABq7Z'; swapping would be 'q7ZAB'. The length-sum case uses "
    "left 'mN' and right 'p8R', expecting LEN 5 from 2+3 and value 'mNp8R'. The zero-length-left case uses "
    "LEN(left)==0 and right 'R9q', expecting LEN 3 and value 'R9q'. The zero-length-right case uses left 'L0xP' "
    "and LEN(right)==0, expecting LEN 4 and value 'L0xP'. Every value comparison is against an equal-length "
    "literal and every length facet has an explicit LEN guard."
)
CHAR_VALUE_LIMITATION = CHAR_VALUE_LIMIT_PREFIX + (
    "only right-append-value, result-length-sum, zero-length-left and zero-length-right are represented. The "
    "programs do not use TRIM, INDEX, REPEAT, blank-padded unequal-length positive comparisons, assumed operand "
    "evaluation order, nondefault character kinds, diagnostics, coarrays or multi-image behavior. Zero-length "
    "cases establish concatenation of a zero-length operand with a nonzero default-character operand; they do not "
    "claim anything about padding, allocation, deferred length, or processor-dependent character kinds."
)
CHAR_PARENS_ORACLE = CHAR_PARENS_ORACLE_PREFIX + (
    "three complete run/effect/f2023 programs observe only final value and length for parenthesized character "
    "concatenation. The left-grouped case evaluates ('A'//'bc')//'D3e' and expects LEN 6 and value 'AbcD3e'. "
    "The right-grouped case evaluates 'A'//('bc'//'D3e') with the same LEN 6 and value. The nested-parentheses "
    "case evaluates ((( 'u' )))//(('V2')//(('wx9'))) without relying on operand evaluation order, expecting "
    "LEN 6 and equal-length value 'uV2wx9'."
)
CHAR_PARENS_LIMITATION = CHAR_PARENS_LIMIT_PREFIX + (
    "only left-grouped-concatenation-value, right-grouped-concatenation-value and nested-parentheses-value are "
    "represented. These fixtures make no evaluation-order, short-circuit, side-effect, defined-operator, allocation, "
    "diagnostic, nondefault-kind or blank-padding claim. Parentheses are observed only through the final character "
    "value and LEN of intrinsic default-character concatenations."
)


class Program:
    def __init__(self, variant, rule, facet):
        self.variant = variant
        self.rule = rule
        self.facet = facet
        self.text = ""
        self.guards = []
        self.probes = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def guard(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected = str(expected)
        replacement = str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"EAF:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter}={counter}+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        if counter:
            self.observations.append(guard)
        return guard

    def completion(self):
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        guard = dict(
            id="completion-output", guard_id="completion-output", kind="output", category="completion",
            expected=literal, replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
            line=self.text.count("\n") + 1, counter=None, activation=None, mutation="completion-literal")
        guard["block_span"] = self.add(prefix + literal + "'\n")
        self.guards.append(guard)
        self.probes.append(dict(guard))
        return guard


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown exact arithmetic variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__exact_arithmetic_" + variant


def header(p):
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")


def finish_program(p):
    total = p.guard("check-total", "checks", len(p.observations), len(p.observations) + 1,
                    category="completion", counter=None)
    completion = p.completion()
    p.add(f"end program exact_arithmetic_{p.variant}\n")
    omissions = []
    start, end = completion["block_span"]
    omissions.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    plans = [("omit-observation-" + guard["id"], guard["block_span"], total) for guard in p.observations]
    if len(p.observations) > 1:
        plans.append(("omit-all-observations", [p.observations[0]["block_span"][0], p.observations[-1]["block_span"][1]], total))
    for name, span, failure in plans:
        start, end = span
        omissions.append(dict(
            id=name, guard_id=failure["id"], kind="guard", category="omission", span=span,
            expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=failure["line"], mutation="whole-program-omission",
            failure_token=failure["failure_token"], failure_stdout=failure["failure_stdout"]))
    return omissions


def integer_program(variant):
    rule, facet = VARIANTS[variant]
    p = Program(variant, rule, facet)
    header(p)
    p.add("! Oracle constants are hand-computed integer literals from Fortran 2023 10.1.5.2.2.\n")
    p.add(f"program exact_arithmetic_{variant}\n  implicit none\n  integer :: checks, result\n  checks=0\n")
    if variant == "positive_truncates_toward_zero":
        p.add("  ! 8/3 has mathematical quotient 2.666..., so the closest integer between 0 and 2.666... is 2.\n")
        p.add("  result = 8 / 3\n")
        p.guard("positive-eight-over-three", "result", 2, 3, category="integer-division")
    elif variant == "negative_dividend_truncates_toward_zero":
        p.add("  ! (-8)/3 has mathematical quotient -2.666..., so the closest integer between 0 and -2.666... is -2.\n")
        p.add("  ! Flooring division would give -3; this fixture distinguishes truncation toward zero from floor.\n")
        p.add("  result = (-8) / 3\n")
        p.guard("negative-dividend-eight-over-three", "result", -2, -3, category="integer-division")
    elif variant == "negative_divisor_truncates_toward_zero":
        p.add("  ! 8/(-3) has mathematical quotient -2.666..., so the closest integer between 0 and -2.666... is -2.\n")
        p.add("  ! Flooring division would give -3; this fixture distinguishes truncation toward zero from floor.\n")
        p.add("  result = 8 / (-3)\n")
        p.guard("negative-divisor-eight-over-three", "result", -2, -3, category="integer-division")
    elif variant == "exact_integer_division":
        p.add("  ! 8/4 has mathematical quotient exactly 2, already an integer between 0 and 2.\n")
        p.add("  result = 8 / 4\n")
        p.guard("exact-eight-over-four", "result", 2, 3, category="integer-division")
    else:
        raise ValueError("unknown integer variant")
    omissions = finish_program(p)
    return finalize_spec(p, omissions)


def character_program(variant):
    rule, facet = VARIANTS[variant]
    p = Program(variant, rule, facet)
    header(p)
    p.add("! Character value comparisons use equal-length expected literals; each length claim uses LEN.\n")
    p.add(f"program exact_arithmetic_{variant}\n  implicit none\n  integer :: checks\n")
    if variant == "default_character_same_kind":
        p.add("  character(len=2) :: left\n  character(len=3) :: right\n  checks=0\n")
        p.add("  left = 'AX'\n  right = 'b7q'\n")
        p.add("  ! 'AX' // 'b7q' appends the right operand, giving length 2+3=5 and value 'AXb7q'.\n")
        p.guard("default-operands-same-kind", "kind(left)", "kind(right)", "kind(right)+1", category="kind")
        p.guard("default-result-kind", "kind(left // right)", "kind(left)", "kind(left)+1", category="kind")
        p.guard("default-result-length", "len(left // right)", 5, 4, category="length")
        p.guard("default-result-value", "left // right", "'AXb7q'", "'AXq7b'", category="value")
    elif variant == "character_result_type":
        p.add("  character(len=2) :: left\n  character(len=3) :: right\n  character(len=5) :: result\n  checks=0\n")
        p.add("  left = 'R4'\n  right = 's9T'\n")
        p.add("  ! Assigning 'R4' // 's9T' to CHARACTER(LEN=5) observes a character result value 'R4s9T'.\n")
        p.add("  result = left // right\n")
        p.guard("assigned-character-value", "result", "'R4s9T'", "'R4T9s'", category="type-value")
        p.guard("assigned-character-length", "len(result)", 5, 4, category="type-length")
        p.guard("assigned-character-kind", "kind(result)", "kind(left)", "kind(left)+1", category="type-kind")
    elif variant == "right_append_value":
        p.add("  character(len=2) :: left\n  character(len=3) :: right\n  checks=0\n")
        p.add("  left = 'AB'\n  right = 'q7Z'\n")
        p.add("  ! 'AB' // 'q7Z' is left followed by right: 'ABq7Z'; swapped order would be 'q7ZAB'.\n")
        p.guard("right-append-length", "len(left // right)", 5, 4, category="length")
        p.guard("right-append-value", "left // right", "'ABq7Z'", "'q7ZAB'", category="value")
    elif variant == "result_length_sum":
        p.add("  character(len=2) :: left\n  character(len=3) :: right\n  checks=0\n")
        p.add("  left = 'mN'\n  right = 'p8R'\n")
        p.add("  ! Operand lengths are 2 and 3, so LEN(left // right) must be 2+3=5.\n")
        p.guard("length-sum", "len(left // right)", 5, 6, category="length")
        p.guard("length-sum-value", "left // right", "'mNp8R'", "'p8RmN'", category="value")
    elif variant == "zero_length_left":
        p.add("  character(len=0) :: left\n  character(len=3) :: right\n  checks=0\n")
        p.add("  left = ''\n  right = 'R9q'\n")
        p.add("  ! The left operand length is 0, so '' // 'R9q' has length 0+3=3 and value 'R9q'.\n")
        p.guard("zero-left-left-length", "len(left)", 0, 1, category="control-length")
        p.guard("zero-left-result-length", "len(left // right)", 3, 2, category="length")
        p.guard("zero-left-result-value", "left // right", "'R9q'", "'q9R'", category="value")
    elif variant == "zero_length_right":
        p.add("  character(len=4) :: left\n  character(len=0) :: right\n  checks=0\n")
        p.add("  left = 'L0xP'\n  right = ''\n")
        p.add("  ! The right operand length is 0, so 'L0xP' // '' has length 4+0=4 and value 'L0xP'.\n")
        p.guard("zero-right-right-length", "len(right)", 0, 1, category="control-length")
        p.guard("zero-right-result-length", "len(left // right)", 4, 3, category="length")
        p.guard("zero-right-result-value", "left // right", "'L0xP'", "'P0xL'", category="value")
    elif variant == "left_grouped_concatenation_value":
        p.add("  character(len=1) :: first\n  character(len=2) :: second\n  character(len=3) :: third\n  checks=0\n")
        p.add("  first = 'A'\n  second = 'bc'\n  third = 'D3e'\n")
        p.add("  ! ('A' // 'bc') // 'D3e' has length (1+2)+3=6 and value 'AbcD3e'.\n")
        p.guard("left-grouped-length", "len((first // second) // third)", 6, 5, category="length")
        p.guard("left-grouped-value", "(first // second) // third", "'AbcD3e'", "'ADe3bc'", category="value")
    elif variant == "right_grouped_concatenation_value":
        p.add("  character(len=1) :: first\n  character(len=2) :: second\n  character(len=3) :: third\n  checks=0\n")
        p.add("  first = 'A'\n  second = 'bc'\n  third = 'D3e'\n")
        p.add("  ! 'A' // ('bc' // 'D3e') has length 1+(2+3)=6 and value 'AbcD3e'.\n")
        p.guard("right-grouped-length", "len(first // (second // third))", 6, 5, category="length")
        p.guard("right-grouped-value", "first // (second // third)", "'AbcD3e'", "'bcD3eA'", category="value")
    elif variant == "nested_parentheses_value":
        p.add("  character(len=1) :: first\n  character(len=2) :: second\n  character(len=3) :: third\n  checks=0\n")
        p.add("  first = 'u'\n  second = 'V2'\n  third = 'wx9'\n")
        p.add("  ! Nested parentheses do not change the final value: 'u' // ('V2' // 'wx9') = 'uV2wx9'.\n")
        p.guard("nested-parentheses-length", "len((((first)) // ((second) // ((third)))))", 6, 5, category="length")
        p.guard("nested-parentheses-value", "(((first)) // ((second) // ((third))))", "'uV2wx9'", "'V2uwx9'", category="value")
    else:
        raise ValueError("unknown character variant")
    omissions = finish_program(p)
    return finalize_spec(p, omissions)


def finalize_spec(p, omissions):
    raw = p.text.encode("ascii")
    for probe in p.probes + omissions:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError("an exact-arithmetic mutation lost its complete-parent span")
    return dict(
        id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=[p.facet],
        evidence="positive-control" if p.rule == CHAR_RULE_TYPE else "effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[p.variant],
        guards=p.guards, probes=p.probes, omissions=omissions, observations=p.observations,
        expected_counts=dict(checks=len(p.observations)))


def program(variant):
    if variant in INT_VARIANTS:
        return integer_program(variant)
    return character_program(variant)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("exact_arithmetic_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence=spec["evidence"], standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_integer_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    owner = next(row for row in updated["requirements"] if row["id"] == INT_RULE)
    if owner["category"] != "effect" or not set(INT_FACETS) <= set(owner["facets"]):
        raise ValueError("integer division facets changed")
    for facet in INT_FACETS:
        owner["pending"].pop(facet, None)
    if owner.get("pending", {}):
        raise ValueError("all integer division pending facets should be implemented")
    owner["oracle"] = owned_paragraph(owner.get("oracle", ""), INT_ORACLE_PREFIX, INT_ORACLE)
    limitation = owner.get("oracle_limitation", "")
    old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
           "processor, approves no fixture or oracle, and claims no coverage.")
    new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
           "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
           "the selected runtime fixtures and mutation plans without granting those approvals or claims.")
    if old in limitation:
        limitation = limitation.replace(old, new)
    owner["oracle_limitation"] = owned_paragraph(limitation, INT_LIMIT_PREFIX, INT_LIMITATION)
    return updated


def synced_character_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in CHAR_FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] not in {"effect", "restriction"} or not set(facets) <= set(owner["facets"]):
            raise ValueError("character concatenation facets changed")
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != CHAR_REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining character pending facets for " + rule)
    by_rule[CHAR_RULE_TYPE]["oracle"] = owned_paragraph(
        by_rule[CHAR_RULE_TYPE].get("oracle", ""), CHAR_TYPE_ORACLE_PREFIX, CHAR_TYPE_ORACLE)
    by_rule[CHAR_RULE_VALUE]["oracle"] = owned_paragraph(
        by_rule[CHAR_RULE_VALUE].get("oracle", ""), CHAR_VALUE_ORACLE_PREFIX, CHAR_VALUE_ORACLE)
    by_rule[CHAR_RULE_PARENS]["oracle"] = owned_paragraph(
        by_rule[CHAR_RULE_PARENS].get("oracle", ""), CHAR_PARENS_ORACLE_PREFIX, CHAR_PARENS_ORACLE)
    replacements = {
        CHAR_RULE_TYPE: (CHAR_TYPE_LIMIT_PREFIX, CHAR_TYPE_LIMITATION),
        CHAR_RULE_VALUE: (CHAR_VALUE_LIMIT_PREFIX, CHAR_VALUE_LIMITATION),
        CHAR_RULE_PARENS: (CHAR_PARENS_LIMIT_PREFIX, CHAR_PARENS_LIMITATION),
    }
    old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
           "processor, approves no fixture or oracle, and claims no coverage.")
    new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
           "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
           "selected runtime fixtures and mutation plans without granting those approvals or claims.")
    for rule, (prefix, paragraph) in replacements.items():
        limitation = by_rule[rule].get("oracle_limitation", "")
        if old in limitation:
            limitation = limitation.replace(old, new)
        by_rule[rule]["oracle_limitation"] = owned_paragraph(limitation, prefix, paragraph)
    return updated


def render_view(catalogue, section, view_path, root=ROOT, *, character=False):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / view_path
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    if character:
        before = before.replace(
            "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
            "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
            "Catalogue: `doc/catalogues/character_intrinsic_operation_10_1_5_3_1.json`. The original source-only "
            "registration supplied pending plans; the bounded runtime fixtures below supply selected cases and "
            "mutation plans, not oracle approval, fixture approval or universal coverage.")
        summary = (
            CHAR_SUMMARY_BEGIN + "\n"
            "## Character concatenation runtime observations\n\n"
            "Nine complete run/effect/f2023 programs cover default-character same-kind/result observations, "
            "right-appended value, length sums, zero-length operands and parenthesized concatenation values. "
            "Operands have distinctive unequal lengths where order or length is being tested. Every length claim "
            "uses `LEN` explicitly, and every value oracle compares against an equal-length literal so blank padding "
            "cannot hide a wrong result. No TRIM, INDEX, REPEAT, TRANSFER, nondefault kind assumption or evaluation-order "
            "oracle is used.\n\n"
            "`nondefault-same-kind-profile` and `different-kind-boundary` remain pending: the first lacks a portable "
            "required nondefault character kind, and the second is a mixed-kind diagnostic/control boundary rather "
            "than a portable positive runtime effect. No evidence link, baseline update, SourceUse renewal or approval "
            "is created.\n"
            + CHAR_SUMMARY_END)
        start_marker, stop_marker = CHAR_SUMMARY_BEGIN, CHAR_SUMMARY_END
    else:
        before = before.replace(
            "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
            "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
            "Catalogue: `doc/catalogues/integer_division_10_1_5_2_2.json`. The original source-only registration "
            "supplied pending plans; the bounded runtime fixtures below supply cases and mutation plans, not oracle "
            "approval, fixture approval or universal coverage.")
        summary = (
            INT_SUMMARY_BEGIN + "\n"
            "## Integer division runtime observations\n\n"
            "Four complete run/effect/f2023 programs cover the pending integer division facets with hand-computed "
            "integer literal expectations. The negative dividend and negative divisor cases use quotients -8/3 and "
            "8/(-3), both expected to truncate toward zero to -2 and both distinguishing the standard from flooring "
            "division, which would give -3. The positive and exact cases are included for their catalogue facets. "
            "No MOD, MODULO, FLOOR, CEILING, INT, NINT, real/complex oracle, overflow or division by zero is used.\n\n"
            "All S10.1.5.2.2 pending facets are removed by the generated fixture manifests. No evidence link, baseline "
            "update, SourceUse renewal or approval is created.\n"
            + INT_SUMMARY_END)
        start_marker, stop_marker = INT_SUMMARY_BEGIN, INT_SUMMARY_END
    if start_marker in before or stop_marker in before:
        if before.count(start_marker) != 1 or before.count(stop_marker) != 1:
            raise ValueError("summary boundaries changed for " + section)
        leading, owned = before.split(start_marker)
        _, trailing = owned.split(stop_marker)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def probe_verdict(spec, probe, parent, observed, *, parent_binding_current):
    verdict = ordinary_probe_verdict(spec, probe, parent, observed, parent_binding_current=parent_binding_current)
    if (probe.get("mutation") != "completion-statement-omission" or observed is None
            or not verdict["parent_passed"]):
        return verdict
    sys.path.insert(0, str(ROOT / "tests"))
    from run_tests import ProcessResult, failure
    trace = observed.get("trace", [])
    intended = (
        observed.get("outcome") == "fail" and observed.get("phase") == "run"
        and observed.get("input_hashes") == {"source.f90": sha(wrong_oracle_source(spec, probe))}
        and [step["phase"] for step in trace] == ["compile", "link", "run"]
        and all(step["returncode"] == 0 and not step["timed_out"]
                and not failure(ProcessResult(step["returncode"], step["stdout"] + step["stderr"],
                                              step["timed_out"]), step["phase"]) for step in trace)
        and trace[-1]["stdout"] == "" and trace[-1]["stderr"] == "")
    qualified = bool(verdict["parent_passed"] and intended)
    return dict(
        status="sensitive" if qualified else "not-sensitive", qualified=qualified,
        parent_passed=verdict["parent_passed"], intended_failure=bool(intended), parent_preempted=False,
        reason="Current complete parent passes and omission removes its externally required completion."
        if qualified else "Current parent, complete source/trace or exact missing-completion failure is not established.")


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    int_catalogue = json.loads((root / INT_CATALOGUE).read_text())
    char_catalogue = json.loads((root / CHAR_CATALOGUE).read_text())
    updated_int = synced_integer_catalogue(int_catalogue)
    updated_char = synced_character_catalogue(char_catalogue)
    int_view = render_view(updated_int, INT_SECTION, INT_VIEW, root, character=False)
    char_view = render_view(updated_char, CHAR_SECTION, CHAR_VIEW, root, character=True)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if int_catalogue != updated_int:
            stale.append(INT_CATALOGUE)
        if char_catalogue != updated_char:
            stale.append(CHAR_CATALOGUE)
        if (root / INT_VIEW).read_text() != int_view:
            stale.append(INT_VIEW)
        if (root / CHAR_VIEW).read_text() != char_view:
            stale.append(CHAR_VIEW)
        if stale:
            raise ValueError("stale exact-arithmetic fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / INT_CATALOGUE).write_text(json.dumps(updated_int, indent=2) + "\n")
            (root / CHAR_CATALOGUE).write_text(json.dumps(updated_char, indent=2) + "\n")
            (root / INT_VIEW).write_text(int_view)
            (root / CHAR_VIEW).write_text(char_view)
    return specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} exact-arithmetic cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
