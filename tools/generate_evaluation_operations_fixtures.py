#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 subclause 10.1.4 evaluation of operations."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha, wrong_oracle_source

ROOT = Path(__file__).resolve().parents[1]
SECTION = "10.1.4"
CATALOGUE = "doc/catalogues/evaluation_of_operations_10_1_4.json"
VIEW = "doc/fortran_2023_10_1_4.md"
SUMMARY_BEGIN = "<!-- BEGIN EVALUATION OF OPERATIONS FIXTURES -->"
SUMMARY_END = "<!-- END EVALUATION OF OPERATIONS FIXTURES -->"

VARIANTS = {
    "unary_intrinsic_operand_value": ("S10.1.4-001", "unary-intrinsic-operand-value"),
    "binary_intrinsic_both_operand_values": ("S10.1.4-001", "binary-intrinsic-both-operand-values"),
    "array_intrinsic_element_values": ("S10.1.4-001", "array-intrinsic-element-values"),
    "implied_do_initial_expression": ("S10.1.4-003", "implied-do-initial-expression"),
    "implied_do_terminal_expression": ("S10.1.4-003", "implied-do-terminal-expression"),
    "implied_do_stride_expression": ("S10.1.4-003", "implied-do-stride-expression"),
    "nested_implied_do_controls": ("S10.1.4-003", "nested-implied-do-controls"),
    "scalar_left_array_right": ("S10.1.4-004", "scalar-left-array-right"),
    "array_left_scalar_right": ("S10.1.4-004", "array-left-scalar-right"),
    "same_shape_array_operands": ("S10.1.4-004", "same-shape-array-operands"),
    "corresponding_element_pairing": ("S10.1.4-004", "corresponding-element-pairing"),
    "intrinsic_unary_array_values": ("S10.1.4-005", "intrinsic-unary-array-values"),
    "unary_result_same_shape": ("S10.1.4-005", "unary-result-same-shape"),
    "pure_elemental_function_array_values": ("S10.1.4-005", "pure-elemental-function-array-values"),
}

FACETS_BY_RULE = {}
for rule, facet in VARIANTS.values():
    FACETS_BY_RULE.setdefault(rule, []).append(facet)
FACETS_BY_RULE = {rule: tuple(facets) for rule, facets in FACETS_BY_RULE.items()}
REMAINING_PENDING = {
    "S10.1.4-001": set(),
    "S10.1.4-003": set(),
    "S10.1.4-004": set(),
    "S10.1.4-005": {"pure-element-order-latitude"},
}
COMPLETIONS = {name: "EVALUATION OPERATIONS " + name.upper().replace("_", " ") + " OK\n" for name in VARIANTS}

ORACLE_PREFIXES = {
    "S10.1.4-001": "S10.1.4-001 operand-value runtime fixtures: ",
    "S10.1.4-003": "S10.1.4-003 ac-implied-do runtime fixtures: ",
    "S10.1.4-004": "S10.1.4-004 binary elemental runtime fixtures: ",
    "S10.1.4-005": "S10.1.4-005 unary elemental runtime fixtures: ",
}
LIMIT_PREFIXES = {
    "S10.1.4-001": "S10.1.4-001 operand-value fixture boundaries: ",
    "S10.1.4-003": "S10.1.4-003 ac-implied-do fixture boundaries: ",
    "S10.1.4-004": "S10.1.4-004 binary elemental fixture boundaries: ",
    "S10.1.4-005": "S10.1.4-005 unary elemental fixture boundaries: ",
}
ORACLES = {
    "S10.1.4-001": ORACLE_PREFIXES["S10.1.4-001"] + (
        "three complete run/effect/f2023 programs establish operand values before evaluation and then use "
        "integer intrinsic operations with literal, hand-derived oracles. The unary case sets x=-7 and y=4, "
        "then checks -x=7 and -y=-4, so an absolute-value implementation or a constant result cannot pass. "
        "The binary case sets left=19 and right=6, checking left-right=13 and right-left=-13; changing either "
        "operand or commutatively pairing them changes at least one guard. The array case sets a=[8,-3,15] and "
        "b=[2,5,-4], then checks a-b=[6,-8,19] plus the element total 17. No side effects, undefined values, "
        "evaluation counts, real arithmetic or operand-order assertion is used. Wrong-oracle mutations cover every "
        "guard and completion literal; input mutations change every source operand literal used by the facet."
    ),
    "S10.1.4-003": ORACLE_PREFIXES["S10.1.4-003"] + (
        "four complete run/effect/f2023 programs use array constructors whose ac-implied-do control expressions "
        "contain nontrivial integer arithmetic. The initial-control case [(i,i=1+1,4)] produces [2,3,4]; the "
        "terminal-control case [(i,i=1,2+2)] produces [1,2,3,4]; the stride-control case [(i,i=1,5,1+1)] "
        "produces [1,3,5]; and the nested-control case [((10*i+j,i=2-1,3,1+1),j=1+2,4+1,1+1)] produces "
        "[13,33,15,35]. The arithmetic changes extents or values relative to bare literals, making the controls "
        "load-bearing without function side effects, evaluation counts, RESHAPE or compiler-consensus oracles."
    ),
    "S10.1.4-004": ORACLE_PREFIXES["S10.1.4-004"] + (
        "four complete run/effect/f2023 programs use rank-one integer arrays with distinct elements. They check "
        "10-[1,4,7]=[9,6,3], [1,4,7]-10=[-9,-6,-3], [1,2,3]+[10,20,30]=[11,22,33], and "
        "[1,100,7]-[10,1,-5]=[-9,99,12]. The left-scalar and right-scalar subtraction cases have different "
        "expected signs, and the corresponding-pairing case distinguishes elementwise pairing from reductions, "
        "permutations, endpoint-only checks, or scalar reuse. Expected values are literal integer arithmetic and no "
        "storage order, address, TRANSFER or element evaluation order is observed."
    ),
    "S10.1.4-005": ORACLE_PREFIXES["S10.1.4-005"] + (
        "three complete run/effect/f2023 programs observe only values and shape, never element order. The intrinsic "
        "unary array case checks -[1,-2,3]=[-1,2,-3]. The same-shape case applies unary minus to a rank-two "
        "array a(2:3,-1:1), checks shape(-a)=[2,3], and checks interior and endpoint values 11, -23 and 32. "
        "The pure elemental function case maps pure elemental bump(x)=x+3 over [-2,0,5], expecting [1,3,8]. "
        "All expected values are hand-computed integer literals; no side effects, counters in element operations, "
        "ordering oracle, real arithmetic, TRANSFER or address observation is used."
    ),
}
LIMITATIONS = {
    "S10.1.4-001": LIMIT_PREFIXES["S10.1.4-001"] + (
        "only unary-intrinsic-operand-value, binary-intrinsic-both-operand-values and array-intrinsic-element-values "
        "are represented. The fixtures do not claim operand evaluation order, mandatory evaluation of unneeded "
        "expression parts, exceptions, overflow, real/complex arithmetic, diagnostics, coarrays, multi-image behavior "
        "or universal compiler conformance."
    ),
    "S10.1.4-003": LIMIT_PREFIXES["S10.1.4-003"] + (
        "only the four ac-implied-do control-expression facets are represented. Constructor syntax, scalar-int-expr "
        "typing, assignment and SIZE/array comparison behavior remain dependencies. The programs do not assert how "
        "many times a control expression is evaluated, evaluate side-effecting controls, or observe iteration order "
        "beyond the standard constructor values."
    ),
    "S10.1.4-004": LIMIT_PREFIXES["S10.1.4-004"] + (
        "only scalar-left-array-right, array-left-scalar-right, same-shape-array-operands and corresponding-element-"
        "pairing are represented. Conformability diagnostics, rank-two or higher arrays, noninteger operands, storage "
        "layout, element evaluation order, vectorization choices and processor performance are not claimed."
    ),
    "S10.1.4-005": LIMIT_PREFIXES["S10.1.4-005"] + (
        "only intrinsic-unary-array-values, unary-result-same-shape and pure-elemental-function-array-values are "
        "represented. pure-element-order-latitude remains pending/unimplemented because the source grants a processor "
        "permission to choose simultaneous or arbitrary element order; a conforming positive runtime test may not fail "
        "one permitted order, and side effects or counters would be the wrong oracle. The fixtures do not claim lower "
        "bounds, defined operators, evaluation order, diagnostics, coarrays or multi-image behavior."
    ),
}


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown evaluation-of-operations variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__evaluation_operations_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facet = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.probes = []
        self.input_probes = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def input_line(self, name, prefix, literal, suffix, replacement):
        start = len(self.text) + len(prefix)
        line = self.text.count("\n") + 1
        self.add(prefix + literal + suffix)
        self.input_probes.append(dict(
            id=name, guard_id="input-" + name, kind="input", category="input", span=[start, start + len(literal)],
            line=line, expected=literal, replacement=replacement, activation=None,
            mutation="source-input-literal", failure_stdout=None))

    def guard(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"EOP:{self.variant}:{name}"
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

    def array_guard(self, name, expression, expected, replacement, *, category="array"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if (any({expression} /= "
        start = block_start + len(prefix)
        token = f"EOP:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter="checks", activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ")) then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        self.add("  checks=checks+1\n")
        self.observations.append(guard)
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
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


def begin(p):
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")
    p.add("! Expected values are hand-computed integer literals from Fortran 2023 10.1.4.\n")
    p.add(f"program evaluation_operations_{p.variant}\n  implicit none\n  integer :: checks\n")


def finish(p, extra_contains=""):
    total = p.guard("check-total", "checks", len(p.observations), len(p.observations) + 1,
                    category="completion", counter=None)
    completion = p.completion()
    if extra_contains:
        p.add(extra_contains)
    p.add(f"end program evaluation_operations_{p.variant}\n")
    omissions = []
    start, end = completion["block_span"]
    omissions.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission", span=[start, end],
        expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    for guard in p.observations:
        start, end = guard["block_span"]
        omissions.append(dict(
            id="omit-observation-" + guard["id"], guard_id=total["id"], kind="guard", category="omission",
            span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=total["line"], mutation="whole-program-omission", failure_token=total["failure_token"],
            failure_stdout=total["failure_stdout"]))
    if p.observations:
        start, end = p.observations[0]["block_span"][0], p.observations[-1]["block_span"][1]
        omissions.append(dict(
            id="omit-all-observations", guard_id=total["id"], kind="guard", category="omission", span=[start, end],
            expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=total["line"], mutation="whole-program-omission", failure_token=total["failure_token"],
            failure_stdout=total["failure_stdout"]))
    return omissions


def finalized(p, omissions):
    raw = p.text.encode("ascii")
    for probe in p.probes + p.input_probes + omissions:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError("an evaluation-of-operations mutation lost its complete-parent span")
    return dict(
        id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=[p.facet], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[p.variant],
        guards=p.guards, probes=p.probes, input_probes=p.input_probes, omissions=omissions,
        observations=p.observations, expected_counts=dict(checks=len(p.observations)))


def program(variant):
    p = Program(variant)
    begin(p)
    v = variant
    if v == "unary_intrinsic_operand_value":
        p.add("  integer :: x, y, r1, r2\n  checks=0\n")
        p.input_line("negative-operand", "  x = ", "-7", "\n", "-8")
        p.input_line("positive-operand", "  y = ", "4", "\n", "5")
        p.add("  ! -(-7)=7, and -(4)=-4; the second case rejects absolute-value behavior.\n")
        p.add("  r1 = -x\n  r2 = -y\n")
        p.guard("minus-negative-seven", "r1", 7, 8)
        p.guard("minus-positive-four", "r2", -4, 4)
        omissions = finish(p)
    elif v == "binary_intrinsic_both_operand_values":
        p.add("  integer :: left, right, forward, reverse\n  checks=0\n")
        p.input_line("left-operand", "  left = ", "19", "\n", "20")
        p.input_line("right-operand", "  right = ", "6", "\n", "5")
        p.add("  ! 19-6=13 and 6-19=-13; both operand values and order matter.\n")
        p.add("  forward = left - right\n  reverse = right - left\n")
        p.guard("left-minus-right", "forward", 13, 14)
        p.guard("right-minus-left", "reverse", -13, 13)
        omissions = finish(p)
    elif v == "array_intrinsic_element_values":
        p.add("  integer :: a(3), b(3), result(3)\n  checks=0\n")
        p.input_line("left-array", "  a = ", "[8,-3,15]", "\n", "[9,-3,15]")
        p.input_line("right-array", "  b = ", "[2,5,-4]", "\n", "[2,6,-4]")
        p.add("  ! Element values: [8-2, -3-5, 15-(-4)] = [6,-8,19].\n")
        p.add("  result = a - b\n")
        p.array_guard("array-subtraction-values", "result", "[6,-8,19]", "[6,-7,19]")
        p.guard("array-subtraction-sum", "sum(result)", 17, 18)
        omissions = finish(p)
    elif v == "implied_do_initial_expression":
        p.add("  integer :: i\n  integer :: result(3)\n  checks=0\n")
        p.input_line("initial-expression", "  result = [(i, i=", "1+1", ", 4)]\n", "1")
        p.add("  ! The initial expression is 2, so the constructor is [2,3,4], not [1,2,3,4].\n")
        p.array_guard("initial-values", "result", "[2,3,4]", "[1,2,3]")
        p.guard("initial-size", "size(result)", 3, 4, category="extent")
        omissions = finish(p)
    elif v == "implied_do_terminal_expression":
        p.add("  integer :: i\n  integer :: result(4)\n  checks=0\n")
        p.input_line("terminal-expression", "  result = [(i, i=1, ", "2+2", ")]\n", "3")
        p.add("  ! The terminal expression is 4, giving [1,2,3,4].\n")
        p.array_guard("terminal-values", "result", "[1,2,3,4]", "[1,2,3,5]")
        p.guard("terminal-size", "size(result)", 4, 3, category="extent")
        omissions = finish(p)
    elif v == "implied_do_stride_expression":
        p.add("  integer :: i\n  integer :: result(3)\n  checks=0\n")
        p.input_line("stride-expression", "  result = [(i, i=1, 5, ", "1+1", ")]\n", "1")
        p.add("  ! The stride expression is 2, so the sequence is 1,3,5.\n")
        p.array_guard("stride-values", "result", "[1,3,5]", "[1,2,3]")
        p.guard("stride-size", "size(result)", 3, 5, category="extent")
        omissions = finish(p)
    elif v == "nested_implied_do_controls":
        p.add("  integer :: i, j\n  integer :: result(4)\n  checks=0\n")
        p.input_line("outer-initial", "  result = [((10*i+j, i=2-1, 3, 1+1), j=", "1+2", ", 4+1, 1+1)]\n", "2")
        p.add("  ! Inner i values are 1,3 and outer j values are 3,5: [13,33,15,35].\n")
        p.array_guard("nested-values", "result", "[13,33,15,35]", "[12,32,14,34]")
        p.guard("nested-size", "size(result)", 4, 6, category="extent")
        omissions = finish(p)
    elif v == "scalar_left_array_right":
        p.add("  integer :: a(3), result(3)\n  checks=0\n")
        p.input_line("right-array", "  a = ", "[1,4,7]", "\n", "[1,5,7]")
        p.add("  ! 10-[1,4,7] = [9,6,3].\n")
        p.add("  result = 10 - a\n")
        p.array_guard("scalar-left-values", "result", "[9,6,3]", "[-9,-6,-3]")
        p.guard("scalar-left-middle", "result(2)", 6, 4)
        omissions = finish(p)
    elif v == "array_left_scalar_right":
        p.add("  integer :: a(3), result(3)\n  checks=0\n")
        p.input_line("left-array", "  a = ", "[1,4,7]", "\n", "[1,5,7]")
        p.add("  ! [1,4,7]-10 = [-9,-6,-3], distinct from 10-array.\n")
        p.add("  result = a - 10\n")
        p.array_guard("array-left-values", "result", "[-9,-6,-3]", "[9,6,3]")
        p.guard("array-left-middle", "result(2)", -6, 6)
        omissions = finish(p)
    elif v == "same_shape_array_operands":
        p.add("  integer :: a(3), b(3), result(3)\n  checks=0\n")
        p.input_line("left-array", "  a = ", "[1,2,3]", "\n", "[1,2,4]")
        p.input_line("right-array", "  b = ", "[10,20,30]", "\n", "[10,21,30]")
        p.add("  ! Corresponding sums are [1+10,2+20,3+30] = [11,22,33].\n")
        p.add("  result = a + b\n")
        p.array_guard("same-shape-values", "result", "[11,22,33]", "[11,23,33]")
        p.guard("same-shape-sum", "sum(result)", 66, 65)
        omissions = finish(p)
    elif v == "corresponding_element_pairing":
        p.add("  integer :: a(3), b(3), result(3)\n  checks=0\n")
        p.input_line("left-pairing-array", "  a = ", "[1,100,7]", "\n", "[1,99,7]")
        p.input_line("right-pairing-array", "  b = ", "[10,1,-5]", "\n", "[10,2,-5]")
        p.add("  ! Pairwise subtraction gives [1-10,100-1,7-(-5)] = [-9,99,12].\n")
        p.add("  result = a - b\n")
        p.array_guard("corresponding-values", "result", "[-9,99,12]", "[99,-9,12]")
        p.guard("corresponding-middle", "result(2)", 99, -9)
        omissions = finish(p)
    elif v == "intrinsic_unary_array_values":
        p.add("  integer :: a(3), result(3)\n  checks=0\n")
        p.input_line("unary-array", "  a = ", "[1,-2,3]", "\n", "[1,-3,3]")
        p.add("  ! Elementwise unary minus gives [-1,2,-3].\n")
        p.add("  result = -a\n")
        p.array_guard("unary-array-values", "result", "[-1,2,-3]", "[1,2,3]")
        p.guard("unary-array-sum", "sum(result)", -2, 2)
        omissions = finish(p)
    elif v == "unary_result_same_shape":
        p.add("  integer :: a(2:3,-1:1), result(2:3,-1:1)\n  checks=0\n")
        p.input_line("first-element", "  a(2,-1) = ", "-11", "\n", "-12")
        p.add("  a(3,-1) = 12\n  a(2,0) = -21\n")
        p.input_line("interior-element", "  a(3,0) = ", "23", "\n", "24")
        p.add("  a(2,1) = 31\n")
        p.input_line("last-element", "  a(3,1) = ", "-32", "\n", "-33")
        p.add("  ! The operand has extents 2 by 3; unary minus preserves result shape.\n")
        p.add("  result = -a\n")
        p.array_guard("unary-shape", "shape(-a)", "[2,3]", "[3,2]", category="shape")
        p.guard("unary-lower-corner", "result(2,-1)", 11, -11)
        p.guard("unary-interior", "result(3,0)", -23, 23)
        p.guard("unary-upper-corner", "result(3,1)", 32, -32)
        omissions = finish(p)
    elif v == "pure_elemental_function_array_values":
        p.add("  integer :: a(3), result(3)\n  checks=0\n")
        p.input_line("pure-elemental-array", "  a = ", "[-2,0,5]", "\n", "[-2,1,5]")
        p.add("  ! Pure elemental bump maps x to x+3: [1,3,8].\n")
        p.add("  result = bump(a)\n")
        p.array_guard("pure-elemental-values", "result", "[1,3,8]", "[1,4,8]")
        p.guard("pure-elemental-sum", "sum(result)", 12, 11)
        contains = (
            "contains\n"
            "  pure elemental integer function bump(x)\n"
            "    integer, intent(in) :: x\n"
            "    bump = x + 3\n"
            "  end function bump\n")
        omissions = finish(p, contains)
    else:
        raise ValueError("unknown variant")
    return finalized(p, omissions)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("evaluation_operations_" + spec["variant"])
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
            raise ValueError("selected evaluation-of-operations facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
               "processor, approves no fixture or oracle, and claims no coverage.")
        new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
               "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
               "selected runtime fixtures and mutation plans without granting those approvals or claims.")
        if old in owner.get("oracle_limitation", ""):
            owner["oracle_limitation"] = owner["oracle_limitation"].replace(old, new)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the evaluation-of-operations generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/evaluation_of_operations_10_1_4.json`. The original source-only registration "
        "supplied pending plans; the bounded runtime fixtures below supply selected cases and mutation plans, not "
        "oracle approval, fixture approval or universal coverage.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Evaluation-of-operations runtime observations\n\n"
        "Fourteen complete run/effect/f2023 programs cover operand values for intrinsic operations, ac-implied-do "
        "control expression values, scalar/array and array/array elemental binary operations, and observable unary "
        "elemental values/shape. All oracles are hand-computed integer literals or standard integer inquiries. "
        "The fixtures intentionally avoid real arithmetic, side-effect counters, operand or element evaluation order, "
        "storage layout, TRANSFER, address arithmetic and compiler-consensus oracles.\n\n"
        "The p5 `pure-element-order-latitude` facet remains pending/unimplemented: the source grants order latitude "
        "for pure elemental operations, and a conforming runtime test cannot fail one permitted order or count element "
        "evaluations. S10.1.4-002 restrictions and all conditional-expression facets remain pending with their original "
        "plans. No evidence link, baseline update, SourceUse renewal or approval is created.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the evaluation-of-operations summary boundaries changed")
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
            raise ValueError("stale evaluation-of-operations fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} evaluation-of-operations cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle, "
          f"{sum(len(row['input_probes']) for row in specs.values())} input and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
