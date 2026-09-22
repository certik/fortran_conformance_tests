#!/usr/bin/env python3
"""Relational intrinsic operation runtime fixtures for Fortran 2023 10.1.5.5.1."""

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
SECTION = "10.1.5.5.1"
CATALOGUE = "doc/catalogues/relational_intrinsic_operation_interpretation_10_1_5_5_1.json"
VIEW = "doc/fortran_2023_10_1_5_5_1.md"
RULE_GENERAL = "S10.1.5.5.1-001"
RULE_PAIRS = "S10.1.5.5.1-002"
RULE_CHAR_EQUALITY = "S10.1.5.5.1-010"
SUMMARY_BEGIN = "<!-- BEGIN RELATIONAL INTRINSIC FIXTURES -->"
SUMMARY_END = "<!-- END RELATIONAL INTRINSIC FIXTURES -->"

PAIR_OPERATORS = {
    "lt_symbolic_pair": dict(op="lt", facet="lt-symbolic-pair", dotted=".LT.", symbolic="<"),
    "le_symbolic_pair": dict(op="le", facet="le-symbolic-pair", dotted=".LE.", symbolic="<="),
    "gt_symbolic_pair": dict(op="gt", facet="gt-symbolic-pair", dotted=".GT.", symbolic=">"),
    "ge_symbolic_pair": dict(op="ge", facet="ge-symbolic-pair", dotted=".GE.", symbolic=">="),
    "eq_symbolic_pair": dict(op="eq", facet="eq-symbolic-pair", dotted=".EQ.", symbolic="=="),
    "ne_symbolic_pair": dict(op="ne", facet="ne-symbolic-pair", dotted=".NE.", symbolic="/="),
}
OPERATOR_ORDER = ("lt", "le", "gt", "ge", "eq", "ne")
OPERATOR_NAMES = {
    "lt": "less than",
    "le": "less than or equal",
    "gt": "greater than",
    "ge": "greater than or equal",
    "eq": "equal to",
    "ne": "not equal to",
}
ROW_OPERANDS = {
    "less": (-4, 3, "less row: -4 is less than 3"),
    "equal": (5, 5, "equal row: 5 is equal to 5"),
    "greater": (8, 1, "greater row: 8 is greater than 1"),
}
ROW_ORDER = ("less", "equal", "greater")
TRUTH_TABLE = {
    "lt": {"less": True, "equal": False, "greater": False},
    "le": {"less": True, "equal": True, "greater": False},
    "gt": {"less": False, "equal": False, "greater": True},
    "ge": {"less": False, "equal": True, "greater": True},
    "eq": {"less": False, "equal": True, "greater": False},
    "ne": {"less": True, "equal": False, "greater": True},
}
DISCRIMINATION_ROWS = {
    (operator, alternative): next(
        row for row in ROW_ORDER if TRUTH_TABLE[operator][row] != TRUTH_TABLE[alternative][row])
    for operator in OPERATOR_ORDER for alternative in OPERATOR_ORDER if alternative != operator
}

VARIANTS = {
    "default_logical_result": (RULE_GENERAL, ("two-operand-comparison",)),
    **{name: (RULE_PAIRS, (data["facet"],)) for name, data in PAIR_OPERATORS.items()},
    "same_length_character_equality": (RULE_CHAR_EQUALITY, ("same-length-character-equality",)),
    "right_blank_padding_equality": (RULE_CHAR_EQUALITY, ("right-blank-padding-equality", "all-characters-equal")),
    "right_blank_padding_inequality": (RULE_CHAR_EQUALITY, ("right-blank-padding-inequality",)),
    "zero_length_equality": (RULE_CHAR_EQUALITY, ("zero-length-equality",)),
}
FACETS_BY_RULE = {
    RULE_GENERAL: ("two-operand-comparison",),
    RULE_PAIRS: tuple(data["facet"] for data in PAIR_OPERATORS.values()),
    RULE_CHAR_EQUALITY: (
        "same-length-character-equality", "right-blank-padding-equality",
        "right-blank-padding-inequality", "zero-length-equality", "all-characters-equal"),
}
REMAINING_PENDING = {
    RULE_GENERAL: {"listed-operator-set", "default-logical-result", "type-admission-delegation"},
    RULE_PAIRS: set(),
    RULE_CHAR_EQUALITY: set(),
}
DEFAULT_LOGICAL_PENDING = (
    "PENDING  correction note: no executable fixture is authored in this packet because assigning a "
    "relational expression to a default LOGICAL variable proves only the variable declaration. A future "
    "positive-control plan must assert the kind of the relational expression directly, for example "
    "KIND(left < right)==KIND(.FALSE.), and provide a load-bearing nondefault-kind mutation without "
    "assuming that any nondefault logical kind exists."
)
COMPLETIONS = {
    name: "RELATIONAL INTRINSIC " + name.upper().replace("_", " ") + " OK\n"
    for name in VARIANTS
}

GENERAL_ORACLE_PREFIX = "S10.1.5.5.1-001 relational two-operand runtime fixture: "
PAIR_ORACLE_PREFIX = "S10.1.5.5.1-002 relational spelling-pair runtime fixtures: "
CHAR_ORACLE_PREFIX = "S10.1.5.5.1-010 character equality runtime fixtures: "
GENERAL_LIMIT_PREFIX = "S10.1.5.5.1-001 relational two-operand fixture boundaries: "
PAIR_LIMIT_PREFIX = "S10.1.5.5.1-002 relational spelling-pair fixture boundaries: "
CHAR_LIMIT_PREFIX = "S10.1.5.5.1-010 character equality fixture boundaries: "
OLD_GENERAL_ORACLE_PREFIX = "S10.1.5.5.1-001 relational default-logical runtime fixture: "
OLD_GENERAL_LIMIT_PREFIX = "S10.1.5.5.1-001 relational default-logical fixture boundaries: "

GENERAL_ORACLE = GENERAL_ORACLE_PREFIX + (
    "one complete run/effect/f2023 program evaluates the two-operand integer relation left < right with "
    "left=-3 and right=2. The source stores the result in a LOGICAL scalar and verifies the value is true. "
    "A false control evaluates right < left and must be false. The operands are exact default integers with "
    "unequal values, so a single-operand, symmetric, always-true, always-false, or swapped-operand "
    "implementation would not satisfy the source. Wrong-oracle mutations flip each logical expectation, "
    "swap the true-control operands, and remove observations to prove the final count is load-bearing."
)
GENERAL_LIMITATION = GENERAL_LIMIT_PREFIX + (
    "only two-operand-comparison is represented. default-logical-result remains pending because this packet "
    "does not supply a direct, portable expression-kind oracle with a load-bearing nondefault-kind mutation; "
    "assigning a relation to a default LOGICAL variable would only prove the variable declaration. "
    "listed-operator-set remains a source/Table 10.7 inventory claim, and type-admission-delegation remains "
    "a source ownership boundary to 10.1.5.1. This fixture does not assert every permitted operand family, "
    "diagnostics, source grammar, enumeration or enum relations, nondefault kinds, real comparisons, "
    "evaluation order, or universal compiler conformance."
)
PAIR_ORACLE = PAIR_ORACLE_PREFIX + (
    "six complete run/effect/f2023 programs cover the .LT./<, .LE./<=, .GT./>, .GE./>=, .EQ./== and .NE./="
    " spelling pairs. Each fixture evaluates the dotted and symbolic spellings on the same named integer "
    "operands for all three ordering rows: -4 rel-op 3, 5 rel-op 5, and 8 rel-op 1. The "
    "expected truth values are hand-derived from exact small integers, not from compiler consensus or MIN/MAX/"
    "MERGE. Each fixture separately checks the dotted result, symbolic result, and their .EQV. agreement via a "
    ".NEQV. sentinel on each row. For every operator, those three rows are inconsistent with every one of the "
    "other five relational operators. Permanent wrong-operator substitution plans replace each dotted and "
    "symbolic spelling with every alternative spelling at a row that distinguishes the two operators. "
    "Operand-swap and operand-perturbation mutation plans accompany the ordinary true/false oracle flips."
)
PAIR_LIMITATION = PAIR_LIMIT_PREFIX + (
    "only the six symbolic-pair facets of S10.1.5.5.1-002 are represented. The Table 10.7 row-meaning facets "
    "S10.1.5.5.1-003 through -008 remain pending in this packet even though the sources exercise the same "
    "operators as controls. The fixtures do not claim token grammar beyond compiling ordinary free-form source, "
    "nor do they test real, complex, character, enumeration, enum, kind-conversion, diagnostic, coarray or "
    "multi-image behavior."
)
CHAR_ORACLE = CHAR_ORACLE_PREFIX + (
    "four complete run/effect/f2023 programs cover character equality after the p8 left-to-right comparison and "
    "right blank padding rule. The same-length fixture compares 'M5' with 'M5' as true and 'M5' with 'M6' as "
    "false. The padding-equality fixture asserts LEN(short)==1 and LEN(padded)==2 before comparing 'A' with "
    "'A '; after extending the shorter operand to 'A ', every corresponding character is equal. The padding-"
    "inequality fixture asserts LEN(short)==1 and LEN(long)==4 before comparing 'A' with 'A  B'; after extending "
    "the shorter operand to 'A   ', the first difference is at position 4 (blank versus 'B'), so equality is false "
    "and inequality is true without using a collation-order oracle. The zero-length fixture declares two length-zero "
    "default-character operands, checks both lengths explicitly, and expects equality true and inequality false "
    "without indexing either value."
)
CHAR_LIMITATION = CHAR_LIMIT_PREFIX + (
    "only same-length-character-equality, right-blank-padding-equality, right-blank-padding-inequality, "
    "zero-length-equality and all-characters-equal are represented. Character ordering facets, default collation "
    "boundaries, processor-dependent collation, and nondefault blank padding remain pending in S10.1.5.5.1-011 "
    "or note2. These fixtures do not use LLT/LLE/LGT/LGE, ACHAR, IACHAR, storage order, TRANSFER, TRIM, INDEX, "
    "nondefault character kinds or compiler agreement as an oracle."
)


class Program:
    def __init__(self, variant, rule, facets):
        self.variant = variant
        self.rule = rule
        self.facets = list(facets)
        self.text = ""
        self.guards = []
        self.probes = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def token(self, name):
        return f"RIF:{self.variant}:{name}"

    def fail_block(self, token, indent="    "):
        return indent + f"write(*,'(a)') '{token}'\n" + indent + "error stop\n"

    def logical_guard(self, name, expression, expected, *, category="logical"):
        condition = f".not. ({expression})" if expected else expression
        replacement = f"({expression})" if expected else f".not. ({expression})"
        return self.condition_guard(name, condition, replacement, category=category,
                                    mutation="logical-expectation-flip")

    def equivalence_guard(self, name, left, right, *, category="spelling-equivalence"):
        condition = f"{left} .neqv. {right}"
        replacement = f"{left} .eqv. {right}"
        return self.condition_guard(name, condition, replacement, category=category,
                                    mutation="equivalence-sentinel-reversal")

    def condition_guard(self, name, condition, replacement, *, category, mutation):
        block_start = len(self.text)
        prefix = "  if ("
        start = block_start + len(prefix)
        token = self.token(name)
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expected=condition,
            replacement=replacement, span=[start, start + len(condition)], line=self.text.count("\n") + 1,
            counter="checks", activation=None, mutation=mutation, failure_token=token,
            failure_stdout=token + "\n")
        self.add(prefix + condition + ") then\n" + self.fail_block(token) + "  end if\n  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        return guard

    def select_guard(self, name, expression, expected, replacement, *, category="integer", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  select case ({expression})\n  case ("
        start = block_start + len(prefix)
        token = self.token(name)
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            mutation="select-case-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expected + ")\n")
        if counter:
            self.add(f"    {counter}={counter}+1\n")
        self.add("  case default\n" + self.fail_block(token) + "  end select\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        if counter:
            self.observations.append(guard)
        return guard

    def source_probe(self, name, span, expected, replacement, failure_guard, *, category, mutation):
        probe = dict(
            id=name, guard_id=failure_guard["id"], kind="source", category=category,
            span=span, expected=expected, replacement=replacement, line=self.text[:span[0]].count("\n") + 1,
            guard_line=failure_guard["line"], counter=None, activation=None, mutation=mutation,
            failure_token=failure_guard["failure_token"], failure_stdout=failure_guard["failure_stdout"])
        self.probes.append(probe)
        return probe

    def assign_logical(self, name, variable, expression, *, replacement=None, failure_guard=None, mutation=None):
        prefix = f"  {variable} = "
        start = len(self.text) + len(prefix)
        self.add(prefix + expression + "\n")
        if replacement is not None and failure_guard is not None:
            self.source_probe(name, [start, start + len(expression)], expression, replacement, failure_guard,
                              category="source-expression", mutation=mutation or "source-expression-mutation")
        return [start, start + len(expression)]

    def assignment_with_literal_probe(self, name, variable, literal, replacement, failure_guard, *, category):
        prefix = f"  {variable} = "
        start = len(self.text) + len(prefix)
        self.add(prefix + literal + "\n")
        self.source_probe(name, [start, start + len(literal)], literal, replacement, failure_guard,
                          category=category, mutation="operand-literal-perturbation")

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
        raise ValueError("unknown relational intrinsic variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__relational_intrinsic_" + variant


def begin_program(p):
    p.add(f"! rule: {p.rule}\n")
    for facet in p.facets:
        p.add(f"! covers: {facet}\n")
    p.add("! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.\n")
    p.add(f"program rel_intrinsic_{p.variant}\n  implicit none\n  integer :: checks\n")


def finish_program(p):
    total = p.select_guard("check-total", "checks", len(p.observations), len(p.observations) + 1,
                           category="completion", counter=None)
    completion = p.completion()
    p.add(f"end program rel_intrinsic_{p.variant}\n")
    omissions = []
    start, end = completion["block_span"]
    omissions.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    plans = [("omit-observation-" + guard["id"], guard["block_span"], total) for guard in p.observations]
    if len(p.observations) > 1:
        plans.append(("omit-all-observations", [p.observations[0]["block_span"][0],
                                                p.observations[-1]["block_span"][1]], total))
    for name, span, failure in plans:
        start, end = span
        omissions.append(dict(
            id=name, guard_id=failure["id"], kind="guard", category="omission", span=span,
            expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=failure["line"], mutation="whole-program-omission",
            failure_token=failure["failure_token"], failure_stdout=failure["failure_stdout"]))
    return omissions


def finalize_spec(p, omissions, notes):
    raw = p.text.encode("ascii")
    for probe in p.probes + omissions:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError("a relational intrinsic mutation lost its complete-parent span")
    return dict(
        id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=p.facets,
        evidence="effect", standard="f2023", phase="run", source=p.text, source_sha256=sha(raw),
        completion=COMPLETIONS[p.variant], guards=p.guards, probes=p.probes,
        omissions=omissions, observations=p.observations, notes=notes,
        expected_counts=dict(checks=len(p.observations)))


def default_logical_program():
    rule, facets = VARIANTS["default_logical_result"]
    p = Program("default_logical_result", rule, facets)
    begin_program(p)
    p.add("  integer :: left, right\n  logical :: observed, false_control\n  checks=0\n")
    p.add("  left = -3\n  right = 2\n")
    p.add("  ! -3 is less than 2, so left < right is true; the reversed comparison is false.\n")
    p.assign_logical("reverse-default-relation", "observed", "left < right")
    true_guard = p.logical_guard("two-operand-relation-true", "observed", True)
    p.assign_logical("reverse-false-control", "false_control", "right < left")
    p.logical_guard("reversed-relation-false", "false_control", False)
    assignment = "observed = left < right"
    expr_start = p.text.index(assignment) + len("observed = ")
    p.source_probe("swap-default-relation-operands", [expr_start, expr_start + len("left < right")],
                   "left < right", "right < left", true_guard, category="operand-swap",
                   mutation="reverse-operand-mutation")
    omissions = finish_program(p)
    return finalize_spec(p, omissions, ["left=-3,right=2 -> true", "right=2,left=-3 -> false"])


def pair_program(variant):
    rule, facets = VARIANTS[variant]
    data = PAIR_OPERATORS[variant]
    p = Program(variant, rule, facets)
    begin_program(p)
    op = data["op"]
    p.add("  integer :: less_left, less_right, equal_left, equal_right, greater_left, greater_right\n")
    p.add("  logical :: dotted_less, symbolic_less, dotted_equal, symbolic_equal\n")
    p.add("  logical :: dotted_greater, symbolic_greater\n")
    p.add("  checks=0\n")
    for row in ROW_ORDER:
        left, right, note = ROW_OPERANDS[row]
        p.add(f"  {row}_left = {left}\n  {row}_right = {right}\n")
        p.add(f"  ! {note}; {OPERATOR_NAMES[op]} is {str(TRUTH_TABLE[op][row]).lower()} on this row.\n")
    dotted = data["dotted"]
    symbolic = data["symbolic"]
    assignment_spans, row_guards = {}, {}
    for row in ROW_ORDER:
        expected = TRUTH_TABLE[op][row]
        dotted_var = f"dotted_{row}"
        symbolic_var = f"symbolic_{row}"
        dotted_expr = f"{row}_left {dotted} {row}_right"
        symbolic_expr = f"{row}_left {symbolic} {row}_right"
        assignment_spans[("dotted", row)] = p.assign_logical(
            f"dotted-{row}-source", dotted_var, dotted_expr)
        row_guards[("dotted", row)] = p.logical_guard(f"dotted-{row}-control", dotted_var, expected)
        assignment_spans[("symbolic", row)] = p.assign_logical(
            f"symbolic-{row}-source", symbolic_var, symbolic_expr)
        row_guards[("symbolic", row)] = p.logical_guard(f"symbolic-{row}-control", symbolic_var, expected)
        p.equivalence_guard(f"{row}-spellings-agree", dotted_var, symbolic_var)
    true_row = next(
        (row for row in ROW_ORDER
         if TRUTH_TABLE[op][row] and ROW_OPERANDS[row][0] != ROW_OPERANDS[row][1]),
        next(row for row in ROW_ORDER if TRUTH_TABLE[op][row]))
    false_row = next(row for row in ROW_ORDER if not TRUTH_TABLE[op][row])
    true_expr = f"{true_row}_left {dotted} {true_row}_right"
    start, _ = assignment_spans[("dotted", true_row)]
    if op in {"eq", "ne"}:
        p.source_probe("perturb-dotted-true-operand", [start, start + len(true_expr)], true_expr,
                       f"{false_row}_left {dotted} {false_row}_right",
                       row_guards[("dotted", true_row)], category="operand-perturbation",
                       mutation="operand-perturbation")
    else:
        p.source_probe("reverse-dotted-true-operands", [start, start + len(true_expr)], true_expr,
                       f"{true_row}_right {dotted} {true_row}_left",
                       row_guards[("dotted", true_row)], category="operand-swap",
                       mutation="reverse-operand-mutation")
    false_expr = f"{false_row}_left {dotted} {false_row}_right"
    start, _ = assignment_spans[("dotted", false_row)]
    p.source_probe("reverse-dotted-false-control", [start, start + len(false_expr)], false_expr,
                   f"{true_row}_left {dotted} {true_row}_right",
                   row_guards[("dotted", false_row)], category="operand-swap",
                   mutation="false-control-reversal")
    for alternative in OPERATOR_ORDER:
        if alternative == op:
            continue
        row = DISCRIMINATION_ROWS[(op, alternative)]
        for spelling, original, replacement in (
                ("dotted", dotted, PAIR_OPERATORS[alternative + "_symbolic_pair"]["dotted"]),
                ("symbolic", symbolic, PAIR_OPERATORS[alternative + "_symbolic_pair"]["symbolic"])):
            expr_start, _ = assignment_spans[(spelling, row)]
            expr = f"{row}_left {original} {row}_right"
            op_start = expr_start + len(f"{row}_left ")
            p.source_probe(
                f"wrong-operator-{spelling}-{op}-to-{alternative}",
                [op_start, op_start + len(original)], original, replacement,
                row_guards[(spelling, row)], category="wrong-operator",
                mutation="wrong-operator-substitution")
    omissions = finish_program(p)
    notes = [
        f"{dotted} and {symbolic} use identical operands",
        "asserted rows: less (-4,3), equal (5,5), greater (8,1)",
    ]
    return finalize_spec(p, omissions, notes)


def character_program(variant):
    rule, facets = VARIANTS[variant]
    p = Program(variant, rule, facets)
    begin_program(p)
    p.add("  logical :: equal_result, unequal_result\n")
    if variant == "same_length_character_equality":
        p.add("  character(len=2) :: left, same, different\n  checks=0\n")
        p.add("  left = 'M5'\n  same = 'M5'\n  different = 'M6'\n")
        p.add("  ! Same length: 'M5' equals 'M5', while position 2 differs in 'M6'.\n")
        p.select_guard("left-length", "len(left)", 2, 3, category="length")
        p.select_guard("same-length", "len(same)", 2, 3, category="length")
        p.select_guard("different-length", "len(different)", 2, 3, category="length")
        p.assign_logical("same-length-equality-source", "equal_result", "left == same")
        p.logical_guard("same-length-equality-true", "equal_result", True)
        p.assign_logical("same-length-inequality-source", "unequal_result", "left == different")
        p.logical_guard("same-length-difference-false", "unequal_result", False)
        notes = ["'M5' == 'M5' true", "'M5' == 'M6' false at character 2"]
    elif variant == "right_blank_padding_equality":
        p.add("  character(len=1) :: short\n  character(len=2) :: padded\n  checks=0\n")
        p.add("  short = 'A'\n  padded = 'A '\n")
        p.add("  ! Padding extends short to 'A '; both corresponding default characters are equal.\n")
        p.select_guard("short-length", "len(short)", 1, 2, category="length")
        p.select_guard("padded-length", "len(padded)", 2, 1, category="length")
        p.assign_logical("padding-equality-source", "equal_result", "short == padded")
        eq_guard = p.logical_guard("padding-equality-true", "equal_result", True)
        literal_start = p.text.index("'A '")
        p.source_probe("perturb-padding-blank-to-b", [literal_start, literal_start + 4], "'A '", "'AB'",
                       eq_guard, category="character-literal", mutation="blank-padding-perturbation")
        notes = ["LEN(short)=1", "LEN(padded)=2", "'A' pads to 'A '"]
    elif variant == "right_blank_padding_inequality":
        p.add("  character(len=1) :: short\n  character(len=4) :: long\n  checks=0\n")
        p.add("  short = 'A'\n  long = 'A  B'\n")
        p.add("  ! Padding extends short to 'A   '; first difference is position 4, blank versus 'B'.\n")
        p.select_guard("short-length", "len(short)", 1, 2, category="length")
        p.select_guard("long-length", "len(long)", 4, 3, category="length")
        p.assign_logical("padding-inequality-eq-source", "equal_result", "short == long")
        p.logical_guard("padding-inequality-equality-false", "equal_result", False)
        p.assign_logical("padding-inequality-ne-source", "unequal_result", "short /= long")
        ne_guard = p.logical_guard("padding-inequality-not-equal-true", "unequal_result", True)
        expr = "short /= long"
        start = p.text.index(expr)
        p.source_probe("swap-inequality-to-equality", [start, start + len(expr)], expr, "short == long",
                       ne_guard, category="operator-swap", mutation="inequality-operator-reversal")
        notes = ["LEN(short)=1", "LEN(long)=4", "'A' pads to 'A   '"]
    elif variant == "zero_length_equality":
        p.add("  character(len=0) :: left, right\n  checks=0\n")
        p.add("  left = ''\n  right = ''\n")
        p.add("  ! Both operands have zero length; p8 says x1 is equal to x2 without indexing.\n")
        p.select_guard("left-zero-length", "len(left)", 0, 1, category="length")
        p.select_guard("right-zero-length", "len(right)", 0, 1, category="length")
        p.assign_logical("zero-length-eq-source", "equal_result", "left == right")
        p.logical_guard("zero-length-equality-true", "equal_result", True)
        p.assign_logical("zero-length-ne-source", "unequal_result", "left /= right")
        p.logical_guard("zero-length-inequality-false", "unequal_result", False)
        notes = ["LEN(left)=LEN(right)=0", "no character position is indexed"]
    else:
        raise ValueError("unknown character variant")
    omissions = finish_program(p)
    return finalize_spec(p, omissions, notes)


def program(variant):
    if variant == "default_logical_result":
        return default_logical_program()
    if variant in PAIR_OPERATORS:
        return pair_program(variant)
    return character_program(variant)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("relational_intrinsic_" + spec["variant"])
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
            raise ValueError("selected relational intrinsic facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if rule == RULE_GENERAL:
            owner["pending"]["default-logical-result"] = DEFAULT_LOGICAL_PENDING
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
    old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
           "processor, approves no fixture or oracle, and claims no coverage.")
    new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
           "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
           "selected runtime fixtures and mutation plans without granting those approvals or claims.")
    replacements = {
        RULE_GENERAL: (GENERAL_ORACLE_PREFIX, GENERAL_ORACLE, GENERAL_LIMIT_PREFIX, GENERAL_LIMITATION),
        RULE_PAIRS: (PAIR_ORACLE_PREFIX, PAIR_ORACLE, PAIR_LIMIT_PREFIX, PAIR_LIMITATION),
        RULE_CHAR_EQUALITY: (CHAR_ORACLE_PREFIX, CHAR_ORACLE, CHAR_LIMIT_PREFIX, CHAR_LIMITATION),
    }
    for rule, (oracle_prefix, oracle, limit_prefix, limitation) in replacements.items():
        owner = by_rule[rule]
        if rule == RULE_GENERAL:
            owner["oracle"] = "\n\n".join(
                paragraph for paragraph in owner.get("oracle", "").split("\n\n")
                if not paragraph.startswith(OLD_GENERAL_ORACLE_PREFIX))
            owner["oracle_limitation"] = "\n\n".join(
                paragraph for paragraph in owner.get("oracle_limitation", "").split("\n\n")
                if not paragraph.startswith(OLD_GENERAL_LIMIT_PREFIX))
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), oracle_prefix, oracle)
        text = owner.get("oracle_limitation", "")
        if old in text:
            text = text.replace(old, new)
        owner["oracle_limitation"] = owned_paragraph(text, limit_prefix, limitation)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the relational intrinsic generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/relational_intrinsic_operation_interpretation_10_1_5_5_1.json`. "
        "The original source-only registration supplied pending plans; the bounded runtime fixtures below "
        "supply selected cases and mutation plans, not oracle approval, fixture approval or universal coverage.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Relational intrinsic operation runtime observations\n\n"
        "Eleven complete run/effect/f2023 programs cover twelve selected facets. Six integer fixtures "
        "evaluate each dotted relational spelling and its symbolic spelling on identical operands, with paired "
        "less/equal/greater ordering rows and .NEQV. sentinels proving the two spellings agree. Each operator's "
        "row set is inconsistent with every one of the other five relational operators, and wrong-operator "
        "substitution plans permanently cover all thirty operator/alternative pairs for both spellings. A "
        "separate integer fixture checks a two-operand relational comparison with true and false controls. "
        "Four default-character fixtures "
        "cover same-length equality, blank-padded equality, blank-padded inequality and zero-length equality; "
        "every character length is asserted with LEN before the comparison oracle is used.\n\n"
        "The fixtures use exact default INTEGER and default CHARACTER operands only. No compiler-consensus oracle, "
        "MIN/MAX/MERGE, LLT/LLE/LGT/LGE, ACHAR/IACHAR, TRANSFER, TRIM, INDEX, real value, complex value, "
        "nondefault kind or collation-order assertion is used. Wrong-oracle, operand-swap, operand-perturbation "
        "and omission mutation plans bind complete-parent byte spans.\n\n"
        "The remaining pending facets are source inventory/delegation/default-logical boundaries in "
        "S10.1.5.5.1-001, all Table 10.7 row-meaning requirements S10.1.5.5.1-003 through -008, numeric "
        "conversion facets in -009, character ordering/collation facets in -011, and enumeration/enum facets "
        "in -012/-013.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the relational intrinsic summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(
        render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


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
            raise ValueError("stale relational-intrinsic fixture family: " + ", ".join(stale))
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
    wrong_operator = sum(
        1 for row in specs.values() for probe in row["probes"]
        if probe.get("mutation") == "wrong-operator-substitution")
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} relational-intrinsic cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans, "
          f"including {wrong_operator} wrong-operator substitutions "
          f"({wrong_operator // 2} operator/alternative pairs across both spellings).")


if __name__ == "__main__":
    main()
