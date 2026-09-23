#!/usr/bin/env python3
"""Runtime effect fixtures for Fortran 2023 subclause 9.4.2 structure components."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, probe_verdict as ordinary_probe_verdict

ROOT = Path(__file__).resolve().parents[1]
SECTION = "9.4.2"
CATALOGUE = "doc/catalogues/structure_component_9_4_2.json"
VIEW = "doc/fortran_2023_9_4_2.md"
SUMMARY_BEGIN = "<!-- BEGIN STRUCTURE COMPONENT FIXTURES -->"
SUMMARY_END = "<!-- END STRUCTURE COMPONENT FIXTURES -->"

VARIANTS = {
    "derived_type_object_part": ("S9.4.2-001", "derived-type-object-part"),
    "object_designator_reference": ("S9.4.2-001", "object-designator-reference"),
    "scalar_component": ("S9.4.2-001", "scalar-component"),
    "array_component": ("S9.4.2-001", "array-component"),
    "bare_part_name_rank": ("S9.4.2-002", "bare-part-name-rank"),
    "triplet_rank_contribution": ("S9.4.2-002", "triplet-rank-contribution"),
    "vector_subscript_rank_contribution": ("S9.4.2-002", "vector-subscript-rank-contribution"),
    "rank_from_nonzero_part_ref": ("S9.4.2-003", "rank-from-nonzero-part-ref"),
    "rank_zero_when_no_nonzero_part_ref": ("S9.4.2-003", "rank-zero-when-no-nonzero-part-ref"),
    "base_object_leftmost": ("S9.4.2-003", "base-object-leftmost"),
    "type_from_rightmost": ("S9.4.2-003", "type-from-rightmost"),
    "type_parameters_from_rightmost": ("S9.4.2-003", "type-parameters-from-rightmost"),
}

FACETS_BY_RULE = {
    "S9.4.2-001": tuple(facet for rule, facet in VARIANTS.values() if rule == "S9.4.2-001"),
    "S9.4.2-002": tuple(facet for rule, facet in VARIANTS.values() if rule == "S9.4.2-002"),
    "S9.4.2-003": tuple(facet for rule, facet in VARIANTS.values() if rule == "S9.4.2-003"),
}
REMAINING_PENDING = {
    "S9.4.2-001": set(),
    "S9.4.2-002": {"multiple-section-subscript-rank-contribution"},
    "S9.4.2-003": set(),
}

COMPLETIONS = {variant: "STRUCTURE COMPONENT " + variant.upper().replace("_", " ") + " OK\n"
               for variant in VARIANTS}

ORACLE_PREFIX = {
    "S9.4.2-001": "S9.4.2-001 structure component runtime fixtures: ",
    "S9.4.2-002": "S9.4.2-002 part-reference rank runtime fixtures: ",
    "S9.4.2-003": "S9.4.2-003 data-reference attribute runtime fixtures: ",
}
LIMIT_PREFIX = {
    "S9.4.2-001": "S9.4.2-001 structure component fixture boundaries: ",
    "S9.4.2-002": "S9.4.2-002 part-reference rank fixture boundaries: ",
    "S9.4.2-003": "S9.4.2-003 data-reference attribute fixture boundaries: ",
}
ORACLE = {
    "S9.4.2-001": ORACLE_PREFIX["S9.4.2-001"] + (
        "four complete run/effect/f2023 programs observe structure components through actual percent "
        "references, not copied locals or whole-object comparisons. The derived-object, object-designator, "
        "scalar-component and array-component cases define every observed component before use, give the "
        "parallel component distinct values, and check direct component reads against independent integer "
        "literals. The array-component case uses a scalar parent and an INTEGER component declared with "
        "nonunit bounds -5:-3; it checks SHAPE [3], LBOUND [-5], UBOUND [-3] and all three element "
        "values. Each source also contains a parent-array control x(2)%alpha with distinct x(3)%alpha, so "
        "parent-subscript mutations are load-bearing."
    ),
    "S9.4.2-002": ORACLE_PREFIX["S9.4.2-002"] + (
        "three complete run/effect/f2023 programs observe p2 rank contribution for a bare array part-name, "
        "a subscript-triplet and a vector subscript. The bare case uses scalar parent obj%avec(-5:-3), for "
        "which p2 makes the part-ref rank the rank of the part-name; the program checks SHAPE [3], LBOUND "
        "[-5], UBOUND [-3] and the distinct values. The triplet case uses obj%grid(-4:-2,5:8)(-4:-3,7), "
        "where one triplet and one scalar subscript give rank one, default array-section bounds 1:2, and "
        "values from column 7. The vector case uses obj%grid(picks,8) with picks=[-2,-4], where one vector subscript gives "
        "rank one with shape [2] in vector order. All expected shapes, bounds and values are hand-derived "
        "from p2 plus 9.5.3.1-.2; no storage layout, TRANSFER or address oracle is used."
    ),
    "S9.4.2-003": ORACLE_PREFIX["S9.4.2-003"] + (
        "five complete run/effect/f2023 programs observe p3-p4 data-ref attributes. The nonzero-rank case "
        "uses parent array section x(2:6:2)%alpha; p3 gives the data-ref rank from that leftmost nonzero "
        "part-ref, so SHAPE [3], LBOUND [1], UBOUND [3] and values x(2),x(4),x(6) are checked. The "
        "zero-rank case observes scalar x(2)%alpha in scalar contexts. The base-object case initializes two "
        "different leftmost objects, left%inner%alpha and right%inner%alpha, and observes only the selected "
        "leftmost object's literal. The type case uses rightmost INTEGER and CHARACTER components in "
        "type-appropriate expressions. The type-parameter case checks LEN(x(2)%text)==5 and compares the "
        "five-character value with a same-length literal, while a seven-character sibling component proves the "
        "length comes from the rightmost part name."
    ),
}
LIMITATION = {
    "S9.4.2-001": LIMIT_PREFIX["S9.4.2-001"] + (
        "only the four S9.4.2-001 effect facets are represented. The fixtures cite but do not re-prove "
        "derived-type declaration validity, component declaration syntax, assignment semantics, object "
        "definition rules or default initialization. They do not assert component storage order, offsets, "
        "addresses, padding, finalization, inheritance, allocatable/pointer components, coarrays, image "
        "selectors, polymorphism or diagnostics."
    ),
    "S9.4.2-002": LIMIT_PREFIX["S9.4.2-002"] + (
        "only bare-part-name-rank, triplet-rank-contribution and vector-subscript-rank-contribution are "
        "represented. The multiple-section-subscript-rank-contribution facet remains pending because the "
        "reference compiler in this packet rejects the Fortran 2023 @ multiple-subscript syntax, so no "
        "portable reference-validated executable can yet observe it. The fixtures do not use or accept the "
        "prohibited general form x%array_component when x is an array; C919's at-most-one-nonzero-rank "
        "restriction remains with its catalogue facets."
    ),
    "S9.4.2-003": LIMIT_PREFIX["S9.4.2-003"] + (
        "only the five S9.4.2-003 effect facets are represented. The shape checks cover array-valued "
        "data-refs whose sole nonzero-rank part-ref is either a parent section or a rightmost component "
        "section; they do not establish diagnostics for invalid two-nonzero-rank references such as x%a "
        "where both the parent and component are arrays. Character comparisons use same-length nonblank "
        "literals and explicit LEN checks to avoid blank-padding ambiguity."
    ),
}
SUMMARY = (
    SUMMARY_BEGIN + "\n"
    "## Structure component runtime observations\n\n"
    "Twelve complete run/effect/f2023 fixtures now discharge the S9.4.2-001, selected "
    "S9.4.2-002 and S9.4.2-003 effect facets. They exercise actual percent component "
    "references with scalar parents, scalarized array parents and parent array sections. "
    "Array-valued references assert SHAPE, LBOUND and UBOUND as well as coordinate-coded "
    "values, using nonunit bounds and unequal extents where the component has rank two.\n\n"
    "The rank derivation is from 9.4.2 p2-p3: a bare part-name part-ref has the rank of "
    "that part-name; a section-subscript-list contributes triplets, vector subscripts and "
    "multiple-subscript array sizes; a data-ref has the rank of the one nonzero-rank "
    "part-ref, if any, otherwise zero. C919 permits no more than one nonzero-rank part-ref, "
    "so these fixtures never use the invalid general form array_parent%array_component.\n\n"
    "Every source has distinct values for every observed component and array element. Planned "
    "mutation metadata covers every oracle, every observed input literal, component-reference "
    "substitution, parent-subscript substitution, component-value swapping and a reverse "
    "input+oracle sentinel control. No observed sentinel is zero, `.FALSE.` or blank.\n"
    + SUMMARY_END
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown structure component variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__structure_component_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facet = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.observations = []
        self.probes = []
        self.omissions = []
        self.input_mutations = []
        self.feature_mutations = []
        self.reverse_mutations = []
        self.component_mutation_added = False
        self.parent_mutation_added = False
        self.swap_mutation_added = False

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def add_input_line(self, line, expected, replacement, name):
        start = len(self.text) + line.index(expected)
        self.add(line)
        self.input_mutations.append(dict(
            id=name, kind="input", category="input-literal", expected=expected, replacement=replacement,
            span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
            mutation="input-literal", failure_stdout=""))

    def append_input_in_last_line(self, expected, replacement, name):
        line_start = self.text.rfind("\n", 0, len(self.text) - 1) + 1
        pos = self.text.index(expected, line_start)
        self.input_mutations.append(dict(
            id=name, kind="input", category="input-literal", expected=expected, replacement=replacement,
            span=[pos, pos + len(expected)], line=self.text[:pos].count("\n") + 1,
            mutation="input-literal", failure_stdout=""))

    def guard_equal(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"SC:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            mutation="guard-literal-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter}={counter}+1\n")
            self.observations.append(guard)
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        return guard

    def guard_any(self, name, expression, expected, replacement, *, category="shape"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if (any({expression} /= "
        start = block_start + len(prefix)
        token = f"SC:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter="checks", activation=None,
            mutation="guard-vector-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expected + ")) then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        return guard

    def add_feature_replace(self, expected, replacement, name, *, category="feature", occurrence=1):
        start = -1
        search = 0
        for _ in range(occurrence):
            start = self.text.index(expected, search)
            search = start + len(expected)
        self.feature_mutations.append(dict(
            id=name, kind="feature", category=category, expected=expected, replacement=replacement,
            span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
            mutation="feature-under-test-substitution", failure_stdout=""))

    def add_feature_multi(self, replacements, name, *, category="feature"):
        spans = []
        for replacement in replacements:
            start = self.text.index(replacement["expected"])
            spans.append([start, start + len(replacement["expected"])])
        self.feature_mutations.append(dict(
            id=name, kind="feature", category=category, replacements=replacements, spans=spans,
            mutation="feature-under-test-substitution", failure_stdout=""))

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
            failure_stdout="")
        completion["block_span"] = self.add(prefix + literal + "'\n")
        self.guards.append(completion)
        self.probes.append(dict(completion))
        self.add(f"end program structure_component_{self.variant}\n")
        self.omissions.append(dict(
            id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
            span=completion["block_span"], expected=self.text[completion["block_span"][0]:completion["block_span"][1]],
            replacement="", line=self.text[:completion["block_span"][0]].count("\n") + 1,
            mutation="completion-statement-omission", failure_stdout=""))
        for guard in self.observations:
            start, end = guard["block_span"]
            self.omissions.append(dict(
                id="omit-observation-" + guard["id"], guard_id=total["id"], kind="guard", category="omission",
                span=[start, end], expected=self.text[start:end], replacement="",
                line=self.text[:start].count("\n") + 1, guard_line=total["line"],
                mutation="whole-program-omission", failure_token=total["failure_token"],
                failure_stdout=total["failure_stdout"]))
        if self.observations:
            start, end = self.observations[0]["block_span"][0], self.observations[-1]["block_span"][1]
            self.omissions.append(dict(
                id="omit-all-observations", guard_id=total["id"], kind="guard", category="omission",
                span=[start, end], expected=self.text[start:end], replacement="",
                line=self.text[:start].count("\n") + 1, guard_line=total["line"],
                mutation="whole-program-omission", failure_token=total["failure_token"],
                failure_stdout=total["failure_stdout"]))


def header(p):
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")
    p.add("! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.\n")
    p.add(f"program structure_component_{p.variant}\n  implicit none\n")


def cell_type(p, *, with_text=False, with_inner=False):
    if with_inner:
        p.add("  type :: inner_t\n")
        p.add("    integer :: alpha\n    integer :: beta\n  end type inner_t\n")
    p.add("  type :: cell_t\n")
    p.add("    integer :: alpha\n    integer :: beta\n")
    p.add("    integer :: avec(-5:-3)\n    integer :: bvec(-5:-3)\n")
    p.add("    integer :: grid(-4:-2,5:8)\n    integer :: other_grid(-4:-2,5:8)\n")
    if with_text:
        p.add("    character(len=5) :: text\n    character(len=5) :: other_text\n")
        p.add("    character(len=7) :: longer_text\n")
    if with_inner:
        p.add("    type(inner_t) :: inner\n    type(inner_t) :: other_inner\n")
    p.add("  end type cell_t\n")


def declare_x(p, *, with_text=False, with_inner=False, scalar_obj=True, parent_array=True):
    cell_type(p, with_text=with_text, with_inner=with_inner)
    decls = []
    if scalar_obj:
        decls.append("obj")
    if parent_array:
        decls.append("x(2:6)")
    p.add("  type(cell_t) :: " + ", ".join(decls) + "\n")
    if with_inner:
        p.add("  type(cell_t) :: left_obj, right_obj\n")
    p.add("  integer :: checks\n")


def init_parent_control(p, *, alpha="211", beta="299"):
    p.add("  checks=0\n")
    p.add_input_line(f"  x(2)%alpha = {alpha}\n", alpha, str(int(alpha) + 1), "input-x2-alpha")
    p.add_input_line("  x(3)%alpha = 313\n", "313", "314", "input-x3-alpha")
    p.add_input_line(f"  x(2)%beta = {beta}\n", beta, str(int(beta) + 1), "input-x2-beta")
    p.guard_equal("parent-subscript-control", "x(2)%alpha", alpha, str(int(alpha) + 2), category="control")
    p.guard_equal("component-peer-control", "x(2)%beta", beta, str(int(beta) + 2), category="control")
    p.guard_equal("parent-neighbor-control", "x(3)%alpha", 313, int(alpha), category="control")
    p.add_feature_replace("x(2)%alpha", "x(3)%alpha", "feature-parent-subscript-x2-to-x3", category="parent-subscript", occurrence=2)
    p.parent_mutation_added = True
    p.add_feature_replace("x(2)%alpha", "x(2)%beta", "feature-component-alpha-to-beta", category="component-reference", occurrence=2)
    p.component_mutation_added = True
    p.add_feature_multi([
        {"expected": f"x(2)%alpha = {alpha}", "replacement": f"x(2)%alpha = {beta}"},
        {"expected": f"x(2)%beta = {beta}", "replacement": f"x(2)%beta = {alpha}"},
    ], "feature-swap-alpha-beta-values", category="component-value-swap")
    p.swap_mutation_added = True
    p.reverse_mutations.append(dict(
        id="reverse-x2-alpha-with-oracle", kind="reverse", category="sentinel-load-bearing",
        replacements=[{"expected": f"x(2)%alpha = {alpha}", "replacement": f"x(2)%alpha = {int(alpha) + 5}"},
                      {"expected": f"x(2)%alpha /= {alpha}", "replacement": f"x(2)%alpha /= {int(alpha) + 5}"}],
        mutation="reverse-input-and-oracle-sentinel", intended="pass"))


def assign_vec(p, lhs, values, prefix):
    text = "  " + lhs + " = [" + ", ".join(map(str, values)) + "]\n"
    p.add_input_line(text, str(values[0]), str(values[0] + 9), prefix + "-first")
    for i, value in enumerate(values[1:], 2):
        p.append_input_in_last_line(str(value), str(value + 9), f"{prefix}-{i}")


def add_grid_assignment(p, component, i, j, value, name):
    p.add_input_line(f"  obj%{component}({i},{j}) = {value}\n", str(value), str(value + 1), name)


def assign_triplet_grid_values(p):
    add_grid_assignment(p, "grid", -4, 7, 473, "input-grid-minus4-7")
    add_grid_assignment(p, "grid", -3, 7, 373, "input-grid-minus3-7")
    add_grid_assignment(p, "grid", -2, 7, 273, "input-grid-minus2-7")
    add_grid_assignment(p, "other_grid", -4, 7, 673, "input-other-grid-minus4-7")
    add_grid_assignment(p, "other_grid", -3, 7, 573, "input-other-grid-minus3-7")


def assign_vector_grid_values(p):
    add_grid_assignment(p, "grid", -2, 8, 284, "input-grid-minus2-8")
    add_grid_assignment(p, "grid", -4, 8, 484, "input-grid-minus4-8")
    add_grid_assignment(p, "grid", -3, 8, 384, "input-grid-minus3-8")
    add_grid_assignment(p, "other_grid", -2, 8, 784, "input-other-grid-minus2-8")
    add_grid_assignment(p, "other_grid", -4, 8, 684, "input-other-grid-minus4-8")


def common_array_observations(p, expr, expected_values, *, shape, lbounds, ubounds):
    shape_replacement = list(reversed(shape)) if list(reversed(shape)) != shape else [shape[0] + 1]
    p.guard_any("shape", f"shape({expr})", bracket(shape), bracket(shape_replacement), category="shape")
    p.guard_any("lbound", f"lbound({expr})", bracket(lbounds), bracket([v + 1 for v in lbounds]), category="lbound")
    p.guard_any("ubound", f"ubound({expr})", bracket(ubounds), bracket([v + 1 for v in ubounds]), category="ubound")
    p.guard_any("values", expr, bracket(expected_values), bracket(expected_values[1:] + expected_values[:1]), category="value")


def bracket(values):
    return "[" + ", ".join(map(str, values)) + "]"


def program_derived_type_object_part():
    p = Program("derived_type_object_part")
    header(p)
    declare_x(p)
    init_parent_control(p, alpha="217", beta="281")
    p.add_input_line("  obj%alpha = 431\n", "431", "432", "input-obj-alpha")
    p.add_input_line("  obj%beta = 587\n", "587", "588", "input-obj-beta")
    p.guard_equal("object-part-alpha", "obj%alpha", 431, 587)
    p.guard_equal("distinct-neighbor-beta", "obj%beta", 587, 431, category="control")
    p.add_feature_replace("obj%alpha", "obj%beta", "feature-object-component-alpha-to-beta", category="component-reference", occurrence=2)
    p.finish()
    return p


def program_object_designator_reference():
    p = Program("object_designator_reference")
    header(p)
    declare_x(p)
    p.add("  integer :: observed\n")
    init_parent_control(p, alpha="223", beta="291")
    p.add_input_line("  obj%alpha = 337\n", "337", "338", "input-obj-alpha-initial")
    p.add_input_line("  obj%beta = 449\n", "449", "451", "input-obj-beta")
    p.add_input_line("  observed = obj%alpha + 19\n", "19", "21", "input-expression-addend")
    p.guard_equal("expression-reference", "observed", 356, 357)
    p.add_input_line("  obj%alpha = obj%alpha + 23\n", "23", "25", "input-defining-addend")
    p.guard_equal("defined-component-reference", "obj%alpha", 360, 449)
    p.guard_equal("neighbor-unchanged", "obj%beta", 449, 360, category="control")
    p.add_feature_replace("obj%alpha", "obj%beta", "feature-expression-alpha-to-beta", category="component-reference", occurrence=2)
    p.finish()
    return p


def program_scalar_component():
    p = Program("scalar_component")
    header(p)
    declare_x(p)
    init_parent_control(p, alpha="229", beta="293")
    p.add_input_line("  obj%alpha = 523\n", "523", "524", "input-scalar-alpha")
    p.add_input_line("  obj%beta = 641\n", "641", "642", "input-scalar-beta")
    p.guard_equal("scalar-alpha", "obj%alpha", 523, 641)
    p.guard_equal("scalar-beta-control", "obj%beta", 641, 523, category="control")
    p.add_feature_replace("obj%alpha", "obj%beta", "feature-scalar-alpha-to-beta", category="component-reference", occurrence=2)
    p.finish()
    return p


def program_array_component():
    p = Program("array_component")
    header(p)
    declare_x(p)
    init_parent_control(p, alpha="233", beta="295")
    assign_vec(p, "obj%avec", [719, 727, 733], "input-obj-avec")
    assign_vec(p, "obj%bvec", [839, 853, 857], "input-obj-bvec")
    common_array_observations(p, "obj%avec", [719, 727, 733], shape=[3], lbounds=[-5], ubounds=[-3])
    p.guard_any("neighbor-vector-control", "obj%bvec", bracket([839, 853, 857]), bracket([853, 857, 839]), category="control")
    p.add_feature_replace("obj%avec", "obj%bvec", "feature-array-component-avec-to-bvec", category="component-reference", occurrence=5)
    p.finish()
    return p


def program_bare_part_name_rank():
    p = Program("bare_part_name_rank")
    header(p)
    declare_x(p)
    init_parent_control(p, alpha="239", beta="299")
    assign_vec(p, "obj%avec", [911, 919, 929], "input-obj-avec")
    assign_vec(p, "obj%bvec", [941, 947, 953], "input-obj-bvec")
    common_array_observations(p, "obj%avec", [911, 919, 929], shape=[3], lbounds=[-5], ubounds=[-3])
    p.guard_any("neighbor-vector-control", "obj%bvec", bracket([941, 947, 953]), bracket([947, 953, 941]), category="control")
    p.add_feature_replace("obj%avec", "obj%bvec", "feature-bare-part-name-avec-to-bvec", category="component-reference", occurrence=5)
    p.finish()
    return p


def program_triplet_rank_contribution():
    p = Program("triplet_rank_contribution")
    header(p)
    declare_x(p)
    init_parent_control(p, alpha="241", beta="301")
    assign_triplet_grid_values(p)
    expr = "obj%grid(-4:-3,7)"
    common_array_observations(p, expr, [473, 373], shape=[2], lbounds=[1], ubounds=[2])
    p.guard_equal("triplet-shift-value-control", "obj%grid(-2,7)", 273, 473, category="control")
    p.guard_equal("other-grid-first-control", "obj%other_grid(-4,7)", 673, 573, category="control")
    p.guard_equal("other-grid-second-control", "obj%other_grid(-3,7)", 573, 673, category="control")
    p.add_feature_replace("obj%grid", "obj%other_grid", "feature-grid-to-other-grid", category="component-reference", occurrence=7)
    p.add_feature_replace("-4:-3,7", "-3:-2,7", "feature-triplet-shift", category="section-subscript", occurrence=4)
    p.finish()
    return p


def program_vector_subscript_rank_contribution():
    p = Program("vector_subscript_rank_contribution")
    header(p)
    declare_x(p)
    p.add("  integer :: picks(2)\n")
    init_parent_control(p, alpha="251", beta="307")
    assign_vector_grid_values(p)
    assign_vec(p, "picks", [-2, -4], "input-vector-picks")
    expr = "obj%grid(picks,8)"
    common_array_observations(p, expr, [284, 484], shape=[2], lbounds=[1], ubounds=[2])
    p.guard_equal("vector-feature-value-control", "obj%grid(-3,8)", 384, 484, category="control")
    p.guard_equal("other-grid-first-control", "obj%other_grid(-2,8)", 784, 684, category="control")
    p.guard_equal("other-grid-second-control", "obj%other_grid(-4,8)", 684, 784, category="control")
    p.add_feature_replace("obj%grid", "obj%other_grid", "feature-vector-grid-to-other-grid", category="component-reference", occurrence=7)
    p.add_feature_replace("picks,8", "[-3, -4],8", "feature-vector-subscript-values", category="vector-subscript", occurrence=4)
    p.finish()
    return p


def program_rank_from_nonzero_part_ref():
    p = Program("rank_from_nonzero_part_ref")
    header(p)
    declare_x(p, scalar_obj=False, parent_array=True)
    p.add("  checks=0\n")
    for sub, alpha in [(2, 311), (3, 313), (4, 317), (5, 319), (6, 331)]:
        p.add_input_line(f"  x({sub})%alpha = {alpha}\n", str(alpha), str(alpha + 1), f"input-x{sub}-alpha")
    p.add_input_line("  x(2)%beta = 811\n", "811", "812", "input-x2-beta")
    p.guard_equal("parent-subscript-control", "x(2)%alpha", 311, 313, category="control")
    p.guard_equal("component-peer-control", "x(2)%beta", 811, 311, category="control")
    p.guard_equal("parent-neighbor-x3-control", "x(3)%alpha", 313, 311, category="control")
    p.guard_equal("parent-neighbor-x5-control", "x(5)%alpha", 319, 331, category="control")
    p.add_feature_replace("x(2)%alpha", "x(3)%alpha", "feature-parent-subscript-x2-to-x3", category="parent-subscript")
    p.add_feature_replace("x(2)%alpha", "x(2)%beta", "feature-component-alpha-to-beta", category="component-reference", occurrence=2)
    p.add_feature_multi([
        {"expected": "x(2)%alpha = 311", "replacement": "x(2)%alpha = 811"},
        {"expected": "x(2)%beta = 811", "replacement": "x(2)%beta = 311"},
    ], "feature-swap-alpha-beta-values", category="component-value-swap")
    p.reverse_mutations.append(dict(
        id="reverse-x2-alpha-with-oracle", kind="reverse", category="sentinel-load-bearing",
        replacements=[{"expected": "x(2)%alpha = 311", "replacement": "x(2)%alpha = 316"},
                      {"expected": "x(2)%alpha /= 311", "replacement": "x(2)%alpha /= 316"},
                      {"expected": "[311, 317, 331]", "replacement": "[316, 317, 331]"}],
        mutation="reverse-input-and-oracle-sentinel", intended="pass"))
    expr = "x(2:6:2)%alpha"
    common_array_observations(p, expr, [311, 317, 331], shape=[3], lbounds=[1], ubounds=[3])
    p.add_feature_replace("x(2:6:2)%alpha", "x(3:5:1)%alpha", "feature-parent-section-shift", category="parent-subscript", occurrence=4)
    p.finish()
    return p


def program_rank_zero_when_no_nonzero_part_ref():
    p = Program("rank_zero_when_no_nonzero_part_ref")
    header(p)
    declare_x(p)
    init_parent_control(p, alpha="257", beta="311")
    p.add_input_line("  obj%alpha = 673\n", "673", "674", "input-obj-alpha")
    p.add_input_line("  obj%beta = 761\n", "761", "762", "input-obj-beta")
    assign_vec(p, "obj%avec", [881, 883, 887], "input-array-neighbor")
    p.guard_equal("scalar-expression", "obj%alpha + 17", 690, 691)
    p.guard_equal("scalar-component", "obj%alpha", 673, 761)
    p.guard_equal("scalar-neighbor-beta-control", "obj%beta", 761, 673, category="control")
    p.guard_any("array-neighbor-control", "obj%avec", bracket([881, 883, 887]), bracket([883, 887, 881]), category="control")
    p.add_feature_replace("obj%alpha", "obj%beta", "feature-scalar-alpha-to-beta", category="component-reference", occurrence=2)
    p.finish()
    return p


def program_base_object_leftmost():
    p = Program("base_object_leftmost")
    header(p)
    declare_x(p, with_inner=True, scalar_obj=True, parent_array=True)
    init_parent_control(p, alpha="263", beta="317")
    p.add_input_line("  left_obj%inner%alpha = 971\n", "971", "972", "input-left-inner-alpha")
    p.add_input_line("  left_obj%inner%beta = 983\n", "983", "984", "input-left-inner-beta")
    p.add_input_line("  right_obj%inner%alpha = 1091\n", "1091", "1092", "input-right-inner-alpha")
    p.add_input_line("  right_obj%inner%beta = 1103\n", "1103", "1104", "input-right-inner-beta")
    p.guard_equal("leftmost-base-object", "left_obj%inner%alpha", 971, 1091)
    p.guard_equal("right-object-control", "right_obj%inner%alpha", 1091, 971, category="control")
    p.guard_equal("nested-neighbor-control", "left_obj%inner%beta", 983, 971, category="control")
    p.guard_equal("right-nested-neighbor-control", "right_obj%inner%beta", 1103, 983, category="control")
    p.add_feature_replace("left_obj%inner%alpha", "right_obj%inner%alpha", "feature-leftmost-object-left-to-right", category="base-object", occurrence=2)
    p.add_feature_replace("left_obj%inner%alpha", "left_obj%inner%beta", "feature-nested-component-alpha-to-beta", category="component-reference", occurrence=2)
    p.finish()
    return p


def program_type_from_rightmost():
    p = Program("type_from_rightmost")
    header(p)
    declare_x(p, with_text=True)
    init_parent_control(p, alpha="269", beta="331")
    p.add_input_line("  obj%alpha = 1231\n", "1231", "1232", "input-obj-alpha")
    p.add_input_line("  obj%beta = 1289\n", "1289", "1291", "input-obj-beta")
    p.add_input_line("  obj%text = 'ABCDE'\n", "'ABCDE'", "'ABCDF'", "input-obj-text")
    p.add_input_line("  obj%other_text = 'UVWXY'\n", "'UVWXY'", "'UVWXZ'", "input-obj-other-text")
    p.guard_equal("integer-rightmost-expression", "obj%alpha + 37", 1268, 1269)
    p.guard_equal("integer-rightmost-value", "obj%alpha", 1231, 1289)
    p.guard_equal("integer-neighbor-beta-control", "obj%beta", 1289, 1231, category="control")
    p.guard_equal("character-rightmost-length", "len(obj%text)", 5, 7, category="length")
    p.guard_equal("character-rightmost-value", "obj%text", "'ABCDE'", "'UVWXY'", category="character")
    p.guard_equal("character-neighbor-control", "obj%other_text", "'UVWXY'", "'ABCDE'", category="control")
    p.add_feature_replace("obj%alpha", "obj%beta", "feature-integer-component-alpha-to-beta", category="component-reference", occurrence=2)
    p.add_feature_replace("obj%text", "obj%other_text", "feature-character-component-text-to-other", category="component-reference", occurrence=3)
    p.finish()
    return p


def program_type_parameters_from_rightmost():
    p = Program("type_parameters_from_rightmost")
    header(p)
    declare_x(p, with_text=True)
    init_parent_control(p, alpha="271", beta="337")
    p.add_input_line("  obj%text = 'KLMNO'\n", "'KLMNO'", "'KLMNP'", "input-obj-text")
    p.add_input_line("  obj%other_text = 'PQRST'\n", "'PQRST'", "'PQRSS'", "input-obj-other-text")
    p.add_input_line("  obj%longer_text = 'ABCDEFG'\n", "'ABCDEFG'", "'ABCDEFH'", "input-obj-longer-text")
    p.guard_equal("rightmost-character-length", "len(obj%text)", 5, 7, category="length")
    p.guard_equal("rightmost-character-value", "obj%text", "'KLMNO'", "'PQRST'", category="character")
    p.guard_equal("same-type-neighbor-length", "len(obj%other_text)", 5, 7, category="control")
    p.guard_equal("same-type-neighbor-value", "obj%other_text", "'PQRST'", "'KLMNO'", category="control")
    p.guard_equal("longer-component-length-control", "len(obj%longer_text)", 7, 5, category="control")
    p.guard_equal("longer-component-value-control", "obj%longer_text", "'ABCDEFG'", "'ABCDEFH'", category="control")
    p.add_feature_replace("obj%text", "obj%other_text", "feature-character-component-text-to-other", category="component-reference", occurrence=3)
    p.finish()
    return p


PROGRAMS = {
    "derived_type_object_part": program_derived_type_object_part,
    "object_designator_reference": program_object_designator_reference,
    "scalar_component": program_scalar_component,
    "array_component": program_array_component,
    "bare_part_name_rank": program_bare_part_name_rank,
    "triplet_rank_contribution": program_triplet_rank_contribution,
    "vector_subscript_rank_contribution": program_vector_subscript_rank_contribution,
    "rank_from_nonzero_part_ref": program_rank_from_nonzero_part_ref,
    "rank_zero_when_no_nonzero_part_ref": program_rank_zero_when_no_nonzero_part_ref,
    "base_object_leftmost": program_base_object_leftmost,
    "type_from_rightmost": program_type_from_rightmost,
    "type_parameters_from_rightmost": program_type_parameters_from_rightmost,
}


def wrong_oracle_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    if "span" in mutation:
        start, end = mutation["span"]
        if raw[start:end].decode("ascii") != mutation["expected"]:
            raise ValueError("the mutation span does not bind the complete parent")
        return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]
    mutated = raw
    for start, end, repl in sorted(((s[0], s[1], r["replacement"]) for s, r in zip(mutation["spans"], mutation["replacements"])), reverse=True):
        expected = next(r["expected"] for s, r in zip(mutation["spans"], mutation["replacements"]) if s == [start, end])
        if raw[start:end].decode("ascii") != expected:
            raise ValueError("the mutation span does not bind the complete parent")
        mutated = mutated[:start] + repl.encode("ascii") + mutated[end:]
    return mutated


def mutated_source(spec, mutation):
    if mutation.get("kind") != "reverse":
        return wrong_oracle_source(spec, mutation)
    text = spec["source"]
    for item in mutation["replacements"]:
        if item["expected"] not in text:
            raise ValueError("reverse mutation token not found")
        text = text.replace(item["expected"], item["replacement"], 1)
    return text.encode("ascii")


def all_failing_mutations(spec):
    return spec["probes"] + spec["omissions"] + spec["input_mutations"] + spec["feature_mutations"]


def source_specs():
    specs = {}
    for variant, builder in PROGRAMS.items():
        p = builder()
        raw = p.text.encode("ascii")
        for probe in p.probes + p.omissions + p.input_mutations:
            start, end = probe["span"]
            if raw[start:end].decode("ascii") != probe["expected"]:
                raise ValueError(f"mutation span {probe['id']} lost its complete-parent binding")
        for probe in p.feature_mutations:
            if "span" in probe:
                start, end = probe["span"]
                if raw[start:end].decode("ascii") != probe["expected"]:
                    raise ValueError(f"feature mutation span {probe['id']} lost its complete-parent binding")
            else:
                for span, replacement in zip(probe["spans"], probe["replacements"]):
                    start, end = span
                    if raw[start:end].decode("ascii") != replacement["expected"]:
                        raise ValueError(f"feature mutation span {probe['id']} lost its complete-parent binding")
        if not p.component_mutation_added and not any(m["category"] == "component-reference" for m in p.feature_mutations):
            raise ValueError("missing component-reference mutation")
        if not p.parent_mutation_added and not any(m["category"] == "parent-subscript" for m in p.feature_mutations):
            raise ValueError("missing parent-subscript mutation")
        if not p.swap_mutation_added and not any(m["category"] == "component-value-swap" for m in p.feature_mutations):
            raise ValueError("missing component-value-swap mutation")
        specs[identifier(variant)] = dict(
            id=identifier(variant), variant=variant, rule=p.rule, facets=[p.facet], evidence="effect",
            standard="f2023", phase="run", source=p.text, source_sha256=sha(raw),
            completion=COMPLETIONS[variant], guards=p.guards, probes=p.probes,
            omissions=p.omissions, input_mutations=p.input_mutations,
            feature_mutations=p.feature_mutations, reverse_mutations=p.reverse_mutations,
            observations=p.observations, expected_counts=dict(checks=len(p.observations)))
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("structure_component_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
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
            raise ValueError("selected structure component facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
    old_oracle = ("Source-qualified pending plans pair each positive or diagnostic source shape with an "
                  "independent literal value, inquiry result, or single-token/single-attribute repair. "
                  "Future executable observations must first establish definedness and reached execution; "
                  "future diagnostics must identify the stated grammar or semantic predicate rather than an "
                  "unrelated parse, declaration, support, or runtime failure.")
    new_oracle = ("The original source-only catalogue recorded pending plans. The selected runtime fixtures "
                  "below now supply executable standard-oracle observations for the covered effect facets; "
                  "facets still listed in pending remain unimplemented.")
    old_limitation = ("This is a source-only catalogue packet. It creates no Fortran test program, execution, "
                      "evidence link, fixture approval, oracle approval, or coverage claim.")
    new_limitation = ("The original source-only catalogue created no Fortran test program, execution, evidence "
                      "link, fixture approval, oracle approval, or coverage claim; this generator supplies "
                      "selected runtime fixtures and mutation plans without granting those approvals or claims.")
    for rule in FACETS_BY_RULE:
        owner = by_rule[rule]
        if owner.get("oracle") == old_oracle:
            owner["oracle"] = new_oracle
        elif owner.get("oracle", "").startswith(old_oracle + "\n\n"):
            owner["oracle"] = new_oracle + owner["oracle"][len(old_oracle):]
        if old_limitation in owner.get("oracle_limitation", ""):
            owner["oracle_limitation"] = owner["oracle_limitation"].replace(old_limitation, new_limitation)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX[rule], ORACLE[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMITATION[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the structure component generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "This source-only packet records data-ref and structure-component source requirements and pending plans without approving any fixture.",
        "This packet records data-ref and structure-component requirements; twelve selected effect facets now have bounded runtime fixtures without approving the new cases.")
    before = before.replace(
        "All facets in this packet are pending source plans. No Fortran test program,\ncompiler invocation, execution evidence, oracle approval, fixture approval or\ncoverage claim is supplied here.",
        "Selected effect facets now have executable fixtures and mutation plans. Remaining pending facets, reviews and approvals stay integrator-owned.")
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the structure component summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + SUMMARY + trailing
    else:
        before = before.rstrip() + "\n\n" + SUMMARY + "\n\n"
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
            raise ValueError("stale structure-component fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} structure-component cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} oracle, "
          f"{sum(len(row['input_mutations']) for row in specs.values())} input, "
          f"{sum(len(row['feature_mutations']) for row in specs.values())} feature, "
          f"{sum(len(row['omissions']) for row in specs.values())} omission mutations and "
          f"{sum(len(row['reverse_mutations']) for row in specs.values())} reverse controls.")


if __name__ == "__main__":
    main()
