#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic operation classification."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha, wrong_oracle_source


ROOT = Path(__file__).resolve().parents[1]
SECTION = "10.1.5.1"
CATALOGUE = "doc/catalogues/intrinsic_operation_classification_10_1_5_1.json"
VIEW = "doc/fortran_2023_10_1_5_1.md"
SUMMARY_BEGIN = "<!-- BEGIN INTRINSIC OPERATION CLASSIFICATION FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSIC OPERATION CLASSIFICATION FIXTURES -->"

VARIANTS = {
    "unary_plus_integer": ("S10.1.5.1-001", "unary-plus-integer"),
    "numeric_add_op": ("S10.1.5.1-003", "numeric-add-op"),
    "numeric_subtract_op": ("S10.1.5.1-003", "numeric-subtract-op"),
    "numeric_multiply_op": ("S10.1.5.1-003", "numeric-multiply-op"),
    "numeric_divide_op": ("S10.1.5.1-003", "numeric-divide-op"),
    "numeric_power_op": ("S10.1.5.1-003", "numeric-power-op"),
    "default_character_concat": ("S10.1.5.1-004", "default-character-concat"),
    "character_result_length_value": ("S10.1.5.1-004", "character-result-length-value"),
    "logical_not": ("S10.1.5.1-005", "logical-not"),
    "logical_and": ("S10.1.5.1-005", "logical-and"),
    "logical_or": ("S10.1.5.1-005", "logical-or"),
    "logical_eqv": ("S10.1.5.1-005", "logical-eqv"),
    "logical_neqv": ("S10.1.5.1-005", "logical-neqv"),
}
FACETS_BY_RULE = {
    "S10.1.5.1-001": ["unary-plus-integer"],
    "S10.1.5.1-003": [
        "numeric-add-op",
        "numeric-subtract-op",
        "numeric-multiply-op",
        "numeric-divide-op",
        "numeric-power-op",
    ],
    "S10.1.5.1-004": ["default-character-concat", "character-result-length-value"],
    "S10.1.5.1-005": ["logical-not", "logical-and", "logical-or", "logical-eqv", "logical-neqv"],
}
REMAINING_PENDING = {
    "S10.1.5.1-001": {"unary-minus-real", "unary-minus-complex", "unary-logical-not-separated"},
    "S10.1.5.1-002": {
        "integer-left-numeric-results",
        "real-left-numeric-results",
        "complex-left-numeric-results",
        "conformable-array-binary-operation",
        "nonconformable-boundary",
    },
    "S10.1.5.1-003": set(),
    "S10.1.5.1-004": {"nondefault-same-kind-concat-boundary", "different-character-kind-boundary"},
    "S10.1.5.1-005": {"nonlogical-operand-boundary"},
    "S10.1.5.1-006": {
        "numeric-equality-relations",
        "numeric-order-relations",
        "complex-equality-only",
        "character-equality-and-order",
        "character-kind-match-restriction",
        "same-enumeration-relations",
        "enum-with-same-enum-relations",
        "enum-with-enumerator-integer-expression",
        "relational-spelling-pairs",
    },
    "S10.1.5.1-007": {
        "numeric-array-interpretation",
        "character-array-interpretation",
        "logical-array-interpretation",
        "relational-array-interpretation",
    },
}
COMPLETIONS = {
    name: "INTRINSIC CLASSIFICATION " + name.upper().replace("_", " ") + " OK\n"
    for name in VARIANTS
}
ORACLE_PREFIXES = {
    "S10.1.5.1-001": "S10.1.5.1-001 unary classification runtime fixture: ",
    "S10.1.5.1-003": "S10.1.5.1-003 numeric-operator classification runtime fixtures: ",
    "S10.1.5.1-004": "S10.1.5.1-004 character-operation classification runtime fixtures: ",
    "S10.1.5.1-005": "S10.1.5.1-005 logical-operator classification runtime fixtures: ",
}
LIMIT_PREFIXES = {
    "S10.1.5.1-001": "S10.1.5.1-001 unary classification fixture boundaries: ",
    "S10.1.5.1-003": "S10.1.5.1-003 numeric classification fixture boundaries: ",
    "S10.1.5.1-004": "S10.1.5.1-004 character classification fixture boundaries: ",
    "S10.1.5.1-005": "S10.1.5.1-005 logical classification fixture boundaries: ",
}
ORACLES = {
    "S10.1.5.1-001": ORACLE_PREFIXES["S10.1.5.1-001"] + (
        "one complete run/effect/f2023 program applies unary + to an INTEGER variable initialized to -19, "
        "then observes the integer value consequence directly as -19. The negative operand distinguishes unary plus "
        "from an absolute-value-like or dropped-sign interpretation. The program observes value preservation and normal "
        "execution, not the abstract classification label itself."
    ),
    "S10.1.5.1-003": ORACLE_PREFIXES["S10.1.5.1-003"] + (
        "five complete run/effect/f2023 programs exercise +, binary -, *, /, and ** on INTEGER operands with "
        "hand-computed literal results: 14+(-5)=9, 14-(-5)=19, (-6)*7=-42, 17/5=3 by integer division, and "
        "2**5=32. Operands are selected so the plausible wrong numeric operator alternatives do not produce the "
        "same value; the division guard compares the expression directly so a real-division interpretation would "
        "produce 3.4 and fail rather than being hidden by integer assignment."
    ),
    "S10.1.5.1-004": ORACLE_PREFIXES["S10.1.5.1-004"] + (
        "two complete run/effect/f2023 programs concatenate default CHARACTER operands of unequal lengths. The "
        "default-character case uses left 'Q3' and right 'z9X', expecting KIND(left//right)==KIND(left), LEN 5, "
        "and equal-length value 'Q3z9X'. The length/value case assigns 'Lm'//'h5K' to CHARACTER(LEN=5) result and "
        "checks LEN(result)==5 plus value 'Lmh5K'. The operands are non-palindromic and unequal length so swapped, "
        "truncated, padded, or length-one interpretations fail."
    ),
    "S10.1.5.1-005": ORACLE_PREFIXES["S10.1.5.1-005"] + (
        "five complete run/effect/f2023 programs exercise .NOT., .AND., .OR., .EQV., and .NEQV. with literal "
        "LOGICAL operands and branch-only observations of the result. .NOT. checks both .FALSE. -> .TRUE. and "
        ".TRUE. -> .FALSE. The four binary-operator cases each check the complete TT, TF, FT and FF truth table. "
        "That makes every operand literal load-bearing and makes each asserted row set inconsistent with each of "
        "the other three binary logical operators; operator-substitution mutations replace the operator under "
        "test with each alternative and are required to fail."
    ),
}
LIMITATIONS = {
    "S10.1.5.1-001": LIMIT_PREFIXES["S10.1.5.1-001"] + (
        "only unary-plus-integer is represented. unary-minus-real and unary-minus-complex remain pending because "
        "this packet intentionally avoids real approximation and complex component dependencies; unary-logical-not-"
        "separated remains pending as a source-boundary contrast with S10.1.5.1-005. The fixture observes only the "
        "value consequence of an admitted unary numeric operation, not the classification label directly."
    ),
    "S10.1.5.1-003": LIMIT_PREFIXES["S10.1.5.1-003"] + (
        "all five numeric-operator classification facets are represented only with default INTEGER operands. The "
        "fixtures do not cover real or complex arithmetic, overflow, division by zero, reassociation, precedence, "
        "evaluation order, kind selection, or processor diagnostics. Expected values are hand arithmetic, not "
        "compiler consensus."
    ),
    "S10.1.5.1-004": LIMIT_PREFIXES["S10.1.5.1-004"] + (
        "only default-character-concat and character-result-length-value are represented. nondefault-same-kind-"
        "concat-boundary remains pending because a nondefault character kind is not required to exist, and different-"
        "character-kind-boundary remains pending because this classification unit by itself does not supply a portable "
        "diagnostic case. The fixtures use LEN and KIND inquiries as dependencies and do not use TRANSFER, storage "
        "bytes, TRIM, INDEX, REPEAT, or blank-padded unequal-length value comparisons."
    ),
    "S10.1.5.1-005": LIMIT_PREFIXES["S10.1.5.1-005"] + (
        "only the five positive logical operators are represented. nonlogical-operand-boundary remains pending: p5 "
        "defines a logical intrinsic operation but contains no shall-style prohibition requiring a portable diagnostic "
        "for a nonlogical operand under this unit. The fixtures make no short-circuit, side-effect, associativity, "
        "evaluation-order, kind-selection, defined-operator, or diagnostic claim."
    ),
}


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facet = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.probes = []
        self.input_mutations = []
        self.operator_mutations = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def input_assignment(self, line, expected, replacement, name):
        start = len(self.text) + line.index(expected)
        self.add(line)
        self.input_mutations.append(dict(
            id="input-" + name, kind="input", category="input", expected=expected, replacement=replacement,
            span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
            mutation="input-literal", failure_stdout=""))

    def guard_equal(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected = str(expected)
        replacement = str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"IOC:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter}={counter}+1\n")
            self.observations.append(guard)
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        return guard

    def guard_logical(self, name, expression, expected_true, *, category="logical"):
        block_start = len(self.text)
        prefix = "  if ("
        start = block_start + len(prefix)
        token = f"IOC:{self.variant}:{name}"
        if expected_true:
            self.add(prefix + expression + ") then\n  checks=checks+1\n  else\n"
                     + f"    write(*,'(a)') '{token}'\n    error stop\n  end if\n")
        else:
            self.add(prefix + expression + ") then\n"
                     + f"    write(*,'(a)') '{token}'\n    error stop\n  else\n  checks=checks+1\n  end if\n")
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expression, replacement=f".not. ({expression})", span=[start, start + len(expression)],
            line=self.text[:start].count("\n") + 1, counter="checks", activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="logical-branch-expectation",
            block_span=[block_start, len(self.text)], expected_truth=expected_true)
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        return guard

    def finish(self):
        total = self.guard_equal("check-total", "checks", len(self.observations), len(self.observations) + 1,
                                 category="completion", counter=None)
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        completion = dict(
            id="completion-output", guard_id="completion-output", kind="output", category="completion",
            expected=literal, replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
            line=self.text.count("\n") + 1, counter=None, activation=None, mutation="completion-literal",
            block_span=None, failure_stdout="")
        completion["block_span"] = self.add(prefix + literal + "'\n")
        self.guards.append(completion)
        self.probes.append(dict(completion))
        self.add(f"end program ioc_{self.variant}\n")
        omissions = [dict(
            id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
            span=completion["block_span"], expected=self.text[completion["block_span"][0]:completion["block_span"][1]],
            replacement="", line=self.text[:completion["block_span"][0]].count("\n") + 1,
            mutation="completion-statement-omission", failure_stdout="")]
        for guard in self.observations:
            start, end = guard["block_span"]
            omissions.append(dict(
                id="omit-observation-" + guard["id"], guard_id=total["id"], kind="guard", category="omission",
                span=[start, end], expected=self.text[start:end], replacement="",
                line=self.text[:start].count("\n") + 1, guard_line=total["line"],
                mutation="whole-program-omission", failure_token=total["failure_token"],
                failure_stdout=total["failure_stdout"]))
        if len(self.observations) > 1:
            start, end = self.observations[0]["block_span"][0], self.observations[-1]["block_span"][1]
            omissions.append(dict(
                id="omit-all-observations", guard_id=total["id"], kind="guard", category="omission",
                span=[start, end], expected=self.text[start:end], replacement="",
                line=self.text[:start].count("\n") + 1, guard_line=total["line"],
                mutation="whole-program-omission", failure_token=total["failure_token"],
                failure_stdout=total["failure_stdout"]))
        return omissions


BINARY_LOGICAL_OPERATORS = {
    "logical_and": ".and.",
    "logical_or": ".or.",
    "logical_eqv": ".eqv.",
    "logical_neqv": ".neqv.",
}


def add_operator_mutations(p):
    if p.variant not in BINARY_LOGICAL_OPERATORS:
        return
    operator = BINARY_LOGICAL_OPERATORS[p.variant]
    alternatives = [item for item in BINARY_LOGICAL_OPERATORS.values() if item != operator]
    raw = p.text.encode("ascii")
    spans = []
    start = 0
    while True:
        index = p.text.find(" " + operator + " ", start)
        if index == -1:
            break
        spans.append([index + 1, index + 1 + len(operator)])
        start = index + len(operator) + 2
    if len(spans) != 4:
        raise ValueError("expected four binary logical operator sites")
    for replacement in alternatives:
        mutation = dict(
            id="operator-" + operator.strip(".") + "-to-" + replacement.strip("."),
            kind="operator", category="operator", expected=operator, replacement=replacement,
            spans=spans, line=p.text[:spans[0][0]].count("\n") + 1,
            mutation="operator-under-test-substitution", failure_stdout="")
        for start, end in spans:
            if raw[start:end].decode("ascii") != operator:
                raise ValueError("operator mutation lost its complete-parent span")
        p.operator_mutations.append(mutation)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown intrinsic operation classification variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__intrinsic_operation_classification_" + variant


def start_program(p):
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")
    p.add("! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.\n")
    p.add(f"program ioc_{p.variant}\n  implicit none\n  integer :: checks\n")


def numeric_program(variant):
    p = Program(variant)
    start_program(p)
    p.add("  integer :: left, right, result\n  checks=0\n")
    if variant == "unary_plus_integer":
        p.input_assignment("  left = -19\n", "-19", "19", "left")
        p.add("  ! Unary plus preserves the integer operand value; an absolute-value-like result would be 19.\n")
        p.add("  result = + left\n")
        p.guard_equal("unary-plus-value", "result", -19, 19)
    elif variant == "numeric_add_op":
        p.input_assignment("  left = 14\n", "14", "15", "left")
        p.input_assignment("  right = -5\n", "-5", "-4", "right")
        p.add("  ! 14 + (-5) = 9; subtraction would be 19 and multiplication -70.\n")
        p.add("  result = left + right\n")
        p.guard_equal("add-value", "result", 9, 19)
    elif variant == "numeric_subtract_op":
        p.input_assignment("  left = 14\n", "14", "15", "left")
        p.input_assignment("  right = -5\n", "-5", "-4", "right")
        p.add("  ! 14 - (-5) = 19; addition would be 9.\n")
        p.add("  result = left - right\n")
        p.guard_equal("subtract-value", "result", 19, 9)
    elif variant == "numeric_multiply_op":
        p.input_assignment("  left = -6\n", "-6", "-5", "left")
        p.input_assignment("  right = 7\n", "7", "8", "right")
        p.add("  ! (-6) * 7 = -42; addition would be 1 and subtraction -13.\n")
        p.add("  result = left * right\n")
        p.guard_equal("multiply-value", "result", -42, -13)
    elif variant == "numeric_divide_op":
        p.input_assignment("  left = 17\n", "17", "21", "left")
        p.input_assignment("  right = 5\n", "5", "6", "right")
        p.add("  ! Integer division 17 / 5 gives 3; real division would be 3.4 and fail this direct expression guard.\n")
        p.guard_equal("divide-value", "left / right", 3, 4)
    elif variant == "numeric_power_op":
        p.input_assignment("  left = 2\n", "2", "3", "left")
        p.input_assignment("  right = 5\n", "5", "4", "right")
        p.add("  ! 2 ** 5 = 32; multiplication would be 10.\n")
        p.add("  result = left ** right\n")
        p.guard_equal("power-value", "result", 32, 10)
    else:
        raise ValueError("unknown numeric variant")
    return finalize(p)


def character_program(variant):
    p = Program(variant)
    start_program(p)
    if variant == "default_character_concat":
        p.add("  character(len=2) :: left\n  character(len=3) :: right\n  checks=0\n")
        p.input_assignment("  left = 'Q3'\n", "'Q3'", "'R3'", "left")
        p.input_assignment("  right = 'z9X'\n", "'z9X'", "'z9Y'", "right")
        p.add("  ! 'Q3' // 'z9X' has default character kind, length 2+3=5, and value 'Q3z9X'.\n")
        p.guard_equal("concat-kind", "kind(left // right)", "kind(left)", "kind(left)+1", category="kind")
        p.guard_equal("concat-length", "len(left // right)", 5, 4, category="length")
        p.guard_equal("concat-value", "left // right", "'Q3z9X'", "'z9XQ3'", category="value")
    elif variant == "character_result_length_value":
        p.add("  character(len=2) :: left\n  character(len=3) :: right\n  character(len=5) :: result\n  checks=0\n")
        p.input_assignment("  left = 'Lm'\n", "'Lm'", "'Ln'", "left")
        p.input_assignment("  right = 'h5K'\n", "'h5K'", "'h5J'", "right")
        p.add("  ! Assigning 'Lm' // 'h5K' observes length 2+3=5 and value 'Lmh5K'.\n")
        p.add("  result = left // right\n")
        p.guard_equal("result-length", "len(result)", 5, 4, category="length")
        p.guard_equal("result-value", "result", "'Lmh5K'", "'h5KLm'", category="value")
    else:
        raise ValueError("unknown character variant")
    return finalize(p)


def logical_program(variant):
    p = Program(variant)
    start_program(p)
    if variant == "logical_not":
        p.add("  logical :: false_value, true_value, result_false, result_true\n  checks=0\n")
        p.input_assignment("  false_value = .false.\n", ".false.", ".true.", "false-value")
        p.input_assignment("  true_value = .true.\n", ".true.", ".false.", "true-value")
        p.add("  ! .NOT. is checked on both logical input values: false -> true and true -> false.\n")
        p.add("  result_false = .not. false_value\n  result_true = .not. true_value\n")
        p.guard_logical("not-false-is-true", "result_false", True)
        p.guard_logical("not-true-is-false", "result_true", False)
    elif variant == "logical_and":
        p.add("  logical :: t, f, result_tt, result_tf, result_ft, result_ff\n  checks=0\n")
        p.input_assignment("  t = .true.\n", ".true.", ".false.", "true")
        p.input_assignment("  f = .false.\n", ".false.", ".true.", "false")
        p.add("  ! Complete .AND. truth table: only true and true gives true.\n")
        p.add("  result_tt = t .and. t\n  result_tf = t .and. f\n")
        p.add("  result_ft = f .and. t\n  result_ff = f .and. f\n")
        p.guard_logical("and-true-true", "result_tt", True)
        p.guard_logical("and-true-false", "result_tf", False)
        p.guard_logical("and-false-true", "result_ft", False)
        p.guard_logical("and-false-false", "result_ff", False)
    elif variant == "logical_or":
        p.add("  logical :: t, f, result_tt, result_tf, result_ft, result_ff\n  checks=0\n")
        p.input_assignment("  t = .true.\n", ".true.", ".false.", "true")
        p.input_assignment("  f = .false.\n", ".false.", ".true.", "false")
        p.add("  ! Complete .OR. truth table: only false and false gives false.\n")
        p.add("  result_tt = t .or. t\n  result_tf = t .or. f\n")
        p.add("  result_ft = f .or. t\n  result_ff = f .or. f\n")
        p.guard_logical("or-true-true", "result_tt", True)
        p.guard_logical("or-true-false", "result_tf", True)
        p.guard_logical("or-false-true", "result_ft", True)
        p.guard_logical("or-false-false", "result_ff", False)
    elif variant == "logical_eqv":
        p.add("  logical :: t, f, result_tt, result_tf, result_ft, result_ff\n  checks=0\n")
        p.input_assignment("  t = .true.\n", ".true.", ".false.", "true")
        p.input_assignment("  f = .false.\n", ".false.", ".true.", "false")
        p.add("  ! Complete .EQV. truth table: equal operands give true, unequal operands false.\n")
        p.add("  result_tt = t .eqv. t\n  result_tf = t .eqv. f\n")
        p.add("  result_ft = f .eqv. t\n  result_ff = f .eqv. f\n")
        p.guard_logical("eqv-true-true", "result_tt", True)
        p.guard_logical("eqv-true-false", "result_tf", False)
        p.guard_logical("eqv-false-true", "result_ft", False)
        p.guard_logical("eqv-false-false", "result_ff", True)
    elif variant == "logical_neqv":
        p.add("  logical :: t, f, result_tt, result_tf, result_ft, result_ff\n  checks=0\n")
        p.input_assignment("  t = .true.\n", ".true.", ".false.", "true")
        p.input_assignment("  f = .false.\n", ".false.", ".true.", "false")
        p.add("  ! Complete .NEQV. truth table: unequal operands give true, equal operands false.\n")
        p.add("  result_tt = t .neqv. t\n  result_tf = t .neqv. f\n")
        p.add("  result_ft = f .neqv. t\n  result_ff = f .neqv. f\n")
        p.guard_logical("neqv-true-true", "result_tt", False)
        p.guard_logical("neqv-true-false", "result_tf", True)
        p.guard_logical("neqv-false-true", "result_ft", True)
        p.guard_logical("neqv-false-false", "result_ff", False)
    else:
        raise ValueError("unknown logical variant")
    return finalize(p)


def finalize(p):
    omissions = p.finish()
    add_operator_mutations(p)
    raw = p.text.encode("ascii")
    for probe in p.probes + omissions + p.input_mutations:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError(f"mutation span {probe['id']} lost its complete-parent binding")
    for probe in p.operator_mutations:
        for start, end in probe["spans"]:
            if raw[start:end].decode("ascii") != probe["expected"]:
                raise ValueError(f"operator mutation span {probe['id']} lost its complete-parent binding")
    return dict(
        id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=[p.facet], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[p.variant],
        guards=p.guards, probes=p.probes, omissions=omissions, input_mutations=p.input_mutations,
        operator_mutations=p.operator_mutations,
        observations=p.observations, expected_counts=dict(checks=len(p.observations)))


def program(variant):
    if variant.startswith("numeric_") or variant == "unary_plus_integer":
        return numeric_program(variant)
    if variant.startswith("character_") or variant == "default_character_concat":
        return character_program(variant)
    return logical_program(variant)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def mutated_source(spec, mutation):
    if "spans" in mutation:
        raw = spec["source"].encode("ascii")
        if sha(raw) != spec["source_sha256"]:
            raise ValueError("the complete parent input no longer matches its fingerprint")
        mutated = raw
        for start, end in reversed(mutation["spans"]):
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError("the operator-substitution span does not bind the complete parent")
            mutated = mutated[:start] + mutation["replacement"].encode("ascii") + mutated[end:]
        return mutated
    return wrong_oracle_source(spec, mutation)


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("intrinsic_operation_classification_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect", standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("intrinsic classification facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        limitation = owner.get("oracle_limitation", "")
        old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
               "processor, approves no fixture or oracle, and claims no coverage.")
        new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
               "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
               "selected runtime fixtures and mutation plans without granting those approvals or claims.")
        if old in limitation:
            limitation = limitation.replace(old, new)
        owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    for rule, remaining in REMAINING_PENDING.items():
        if rule in by_rule and rule not in FACETS_BY_RULE:
            if set(by_rule[rule].get("pending", {})) != remaining:
                raise ValueError("unselected pending facets changed for " + rule)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/intrinsic_operation_classification_10_1_5_1.json`. The original source-only "
        "registration supplied pending plans; the bounded runtime fixtures below supply selected cases and "
        "mutation plans, not oracle approval, fixture approval, source-review renewal, or universal coverage.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Intrinsic operation classification runtime observations\n\n"
        "Thirteen complete run/effect/f2023 programs cover a bounded scalar subset: unary integer plus, all five "
        "numeric intrinsic operator spellings with exact integer operands, default-character concatenation value/"
        "length/kind consequences, and the five logical intrinsic operators, now including the complete unary .NOT. "
        "table and complete binary truth tables. Because 10.1.5.1 is a classification "
        "subclause, each program observes only a runtime consequence (type, length, kind, branch, or value), not "
        "the classification label itself. All operands are literals or variables with exact hand-derived oracles; "
        "no real approximation, complex component dependency, short-circuit, evaluation-order, TRANSFER, storage, "
        "or compiler-consensus oracle is used. Operator-substitution mutations for the four binary logical fixtures "
        "are part of the generated campaign because value/input mutations alone cannot prove operator identity.\n\n"
        "Binary result-type combinations, arrays, relation families, nondefault character kinds, complex unary minus, "
        "and all diagnostic/control boundaries remain pending with their original plans. No evidence link, baseline "
        "update, SourceUse renewal, catalogue source-review renewal, or approval is created.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale intrinsic-operation-classification fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsic-operation-classification cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle, "
          f"{sum(len(row['input_mutations']) for row in specs.values())} input, "
          f"{sum(len(row['operator_mutations']) for row in specs.values())} operator and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
