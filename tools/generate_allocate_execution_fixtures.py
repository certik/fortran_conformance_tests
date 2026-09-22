#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 ALLOCATE execution effects in 9.7.1.2."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "9.7.1.2"
CATALOGUE = "doc/catalogues/execution_of_allocate_statement_9_7_1_2.json"
VIEW = "doc/fortran_2023_9_7_1_2.md"
SUMMARY_BEGIN = "<!-- BEGIN ALLOCATE EXECUTION FIXTURES -->"
SUMMARY_END = "<!-- END ALLOCATE EXECUTION FIXTURES -->"

VARIANTS = {
    "explicit_bounds": ("S9.7.1.2-001", ["explicit-lower-and-upper-bounds"]),
    "default_lower": ("S9.7.1.2-001", ["default-lower-bound-one"]),
    "bound_capture": ("S9.7.1.2-001", ["bounds-captured-after-expression-change"]),
    "zero_extent": ("S9.7.1.2-001", ["zero-extent-single-dimension", "zero-sized-array-defined-status-boundary"]),
    "source_shape_bounds": ("S9.7.1.2-008", [
        "shape-from-source-expr", "lower-bounds-from-source-lbound", "source-bound-changes-do-not-affect"]),
    "source_same_rank_vector": ("S9.7.1.2-010", ["ordinary-source-value-same-rank"]),
    "source_scalar_broadcast": ("S9.7.1.2-010", ["scalar-source-broadcast-to-array"]),
    "source_rank_two_array": ("S9.7.1.2-010", ["array-source-to-same-rank-array"]),
    "source_evaluated_once": ("S9.7.1.2-010", ["source-expression-evaluated-once"]),
    "mold_undefined_value": ("S9.7.1.2-011", ["mold-variable-value-need-not-be-defined"]),
}
FACETS_BY_RULE = {
    "S9.7.1.2-001": [
        "explicit-lower-and-upper-bounds", "default-lower-bound-one",
        "bounds-captured-after-expression-change", "zero-extent-single-dimension",
        "zero-sized-array-defined-status-boundary"],
    "S9.7.1.2-008": [
        "shape-from-source-expr", "lower-bounds-from-source-lbound", "source-bound-changes-do-not-affect"],
    "S9.7.1.2-010": [
        "ordinary-source-value-same-rank", "scalar-source-broadcast-to-array",
        "array-source-to-same-rank-array", "source-expression-evaluated-once"],
    "S9.7.1.2-011": ["mold-variable-value-need-not-be-defined"],
}
REMAINING_PENDING = {
    "S9.7.1.2-001": set(),
    "S9.7.1.2-002": {
        "vector-upper-bounds-default-lowers", "vector-lower-and-upper-bounds",
        "scalar-lower-broadcast", "scalar-upper-broadcast", "zero-extent-from-one-dimension"},
    "S9.7.1.2-003": {
        "explicit-cobounds", "default-lower-cobound-one", "cobounds-captured-after-expression-change",
        "multi-image-cobound-inquiries"},
    "S9.7.1.2-006": {
        "implicit-synchronization", "same-statement-same-count-delay", "segment-ordering",
        "stopped-or-failed-image-error-condition", "all-image-success-before-allocated"},
    "S9.7.1.2-008": set(),
    "S9.7.1.2-010": {"nonpolymorphic-ancestor-component-value", "definition-status-from-source-boundary"},
    "S9.7.1.2-011": set(),
    "S9.7.1.2-012": {"type-spec-nondeferred-length-mismatch-error", "source-nondeferred-length-mismatch-error"},
    "S9.7.1.2-013": {"processor-dependent-error-set-boundary", "error-without-stat-initiates-error-termination"},
}
COMPLETIONS = {
    variant: "ALLOCATE EXECUTION " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
ORACLE_PREFIXES = {
    "S9.7.1.2-001": "S9.7.1.2-001 allocate-shape runtime fixtures: ",
    "S9.7.1.2-008": "S9.7.1.2-008 SOURCE-shaped runtime fixture: ",
    "S9.7.1.2-010": "S9.7.1.2-010 SOURCE value runtime fixtures: ",
    "S9.7.1.2-011": "S9.7.1.2-011 MOLD undefined-value runtime fixture: ",
}
LIMIT_PREFIXES = {
    "S9.7.1.2-001": "S9.7.1.2-001 allocate-shape fixture boundaries: ",
    "S9.7.1.2-008": "S9.7.1.2-008 SOURCE-shaped fixture boundaries: ",
    "S9.7.1.2-010": "S9.7.1.2-010 SOURCE value fixture boundaries: ",
    "S9.7.1.2-011": "S9.7.1.2-011 MOLD fixture boundaries: ",
}
ORACLES = {
    "S9.7.1.2-001": ORACLE_PREFIXES["S9.7.1.2-001"] + (
        "four complete run/effect/f2023 programs exercise allocate-shape-spec-list execution. "
        "The explicit-bounds case allocates INTEGER a(3:5), observes LBOUND=3, UBOUND=5, SIZE=3, "
        "then writes whole-array sentinels [31,32,33] and reads a(3), a(4), a(5). The default-lower "
        "case allocates a(4) and a companion b(-2:1), proving a's lower bound is 1 rather than merely "
        "the extent four by checking both bound tuples and nonzero corner values. The capture case uses "
        "lo=2 and hi=4 in ALLOCATE(a(lo:hi)), then changes lo=-5 and hi=9 before observing the original "
        "2:4 bounds and [52,53,54]. The zero-extent case allocates a(5:3) with STAT=, observes STAT=0, "
        "ALLOCATED=.TRUE., SIZE=0, and a nonzero path sentinel, and never references an element. Every "
        "nonzero extent case checks lower bound, upper bound, size and defined payload before completion. "
        "Generated oracle, input and feature mutations corrupt each literal and perturb or default the "
        "ALLOCATE bounds so wrong lower-bound, wrong upper-bound, uncaptured-expression and nonzero-size "
        "implementations fail."
    ),
    "S9.7.1.2-008": ORACLE_PREFIXES["S9.7.1.2-008"] + (
        "one complete run/effect/f2023 program allocates source s(-3:-1,5:8), fills all twelve elements "
        "with coordinate-coded nonzero literals, then executes ALLOCATE(a,SOURCE=s) without an explicit "
        "shape or upper-bounds expression. It observes LBOUND(a)=[-3,5], UBOUND(a)=[-1,8], SHAPE(a)=[3,4], "
        "all twelve copied values, then reallocates s with different bounds and observes that "
        "a retains the original bounds and copied values. A feature mutation adds explicit 1-based bounds to "
        "the ALLOCATE statement, so default-lower, shape-only or live-source-descriptor implementations fail."
    ),
    "S9.7.1.2-010": ORACLE_PREFIXES["S9.7.1.2-010"] + (
        "four complete run/effect/f2023 programs cover ordinary SOURCE= value provision. The same-rank "
        "vector case allocates a(-4:-2) from SOURCE=[11,22,33] and checks the nonunit bounds plus all three "
        "values. The scalar-broadcast case allocates a(-2:2) from scalar SOURCE=7 and checks SIZE=5 plus "
        "all five elements equal 7. The rank-two array case allocates a(2:4,7:8) from a defined rank-two "
        "source with six coordinate-coded nonzero values and checks bounds, shape and all six copied values. The "
        "evaluation-once case uses SOURCE=produce(), where produce increments a saved counter and returns 79; "
        "the oracle is counter=1 and value 79. Feature mutations perturb allocation shape/bounds or call "
        "produce twice, so allocation-shape-only, ignored-SOURCE or repeated evaluation implementations fail."
    ),
    "S9.7.1.2-011": ORACLE_PREFIXES["S9.7.1.2-011"] + (
        "one complete run/effect/f2023 program allocates but never defines INTEGER mold(-6:-4,2:5), then "
        "executes ALLOCATE(a,MOLD=mold). It observes only allocation characteristics: ALLOCATED=.TRUE., "
        "LBOUND=[-6,2], UBOUND=[-4,5], SHAPE=[3,4], and then writes fresh nonzero sentinels into a before "
        "reading them. The undefined MOLD value is never read. Feature mutations replace MOLD-provided "
        "bounds with explicit 1-based bounds, so a processor that ignores MOLD lower bounds or requires a "
        "defined MOLD value is exposed without depending on undefined data."
    ),
}
LIMITATIONS = {
    "S9.7.1.2-001": LIMIT_PREFIXES["S9.7.1.2-001"] + (
        "only allocate-shape-spec-list effects in ordinary single-image allocatable INTEGER arrays are covered. "
        "The zero-size fixture establishes successful zero-size allocation and zero SIZE only; it does not read "
        "nonexistent elements or claim definition status beyond a separately assigned path sentinel. STAT=0 is "
        "used only for the successful non-error path, not for processor-dependent allocation failures."
    ),
    "S9.7.1.2-008": LIMIT_PREFIXES["S9.7.1.2-008"] + (
        "only a same-rank allocatable INTEGER source array is covered. The case uses SOURCE= as the standard "
        "context supplying source-expr shape and lower bounds, while copied values are checked only after the "
        "source has been defined. It does not cover coarrays, pointers, polymorphism, SOURCE conformance "
        "diagnostics, undefined source subobjects, storage layout or address identity."
    ),
    "S9.7.1.2-010": LIMIT_PREFIXES["S9.7.1.2-010"] + (
        "only ordinary integer SOURCE= value provision, scalar-to-array replication and exactly-once evaluation "
        "are covered. nonpolymorphic-ancestor-component-value remains pending because it needs a separate "
        "polymorphic dynamic-type fixture; definition-status-from-source-boundary remains pending because this "
        "packet never reads or infers undefined subobject status. No real, complex, character length mismatch, "
        "finalization, coarray, resource failure or diagnostic behavior is claimed."
    ),
    "S9.7.1.2-011": LIMIT_PREFIXES["S9.7.1.2-011"] + (
        "only the permission to use an undefined MOLD= variable value is covered, and only by observing allocation "
        "characteristics and fresh destination writes. The fixture does not read the mold value, prove arbitrary "
        "undefined-value propagation, cover SOURCE= with an undefined value, or claim type/kind/length behavior "
        "beyond default INTEGER array characteristics."
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__allocate_execution_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facets = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.observations = []
        self.input_mutations = []
        self.feature_mutations = []
        self.reverse_mutations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def literal_site(self, line, expected, replacement, name, bucket):
        start = len(self.text) + line.index(expected)
        self.add(line)
        bucket.append(dict(
            id=name, kind="input" if bucket is self.input_mutations else "feature", category="literal",
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text[:start].count("\n") + 1,
            mutation="input-literal" if bucket is self.input_mutations else "feature-literal"))

    def add_input_line(self, line, expected, replacement, name):
        self.literal_site(line, expected, replacement, name, self.input_mutations)

    def add_line_with_feature(self, line, expected, replacement, name):
        self.literal_site(line, expected, replacement, name, self.feature_mutations)

    def add_feature_replacement(self, expected, replacement, name):
        start = self.text.index(expected)
        self.feature_mutations.append(dict(
            id=name, kind="feature", category="allocate-feature", expected=expected, replacement=replacement,
            span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
            mutation="feature-under-test-substitution"))

    def guard_equal(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"AEX:{self.variant}:{name}"
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
        return guard

    def guard_any(self, name, expression, expected, replacement, *, category="shape"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if (any({expression} /= "
        start = block_start + len(prefix)
        token = f"AEX:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter="checks", activation=None,
            mutation="guard-vector-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expected + ")) then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.observations.append(guard)
        return guard

    def guard_true(self, name, expression, *, category="status"):
        block_start = len(self.text)
        prefix = "  if (.not. ("
        start = block_start + len(prefix)
        token = f"AEX:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expression, replacement=".false.", span=[start, start + len(expression)],
            line=self.text.count("\n") + 1, counter="checks", activation=None,
            mutation="logical-status-expectation", failure_token=token, failure_stdout=token + "\n")
        self.add(prefix + expression + ")) then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.observations.append(guard)
        return guard

    def finish(self):
        self.guard_equal("check-total", "checks", len(self.observations), len(self.observations) + 1,
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
        self.add(f"end program allocate_execution_{self.variant}\n")


def start_program(p):
    p.add(f"! rule: {p.rule}\n! covers: {','.join(p.facets)}\n")
    p.add("! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.\n")
    p.add(f"program allocate_execution_{p.variant}\n  implicit none\n  integer :: checks\n")


def explicit_bounds_program():
    p = Program("explicit_bounds")
    start_program(p)
    p.add("  integer, allocatable :: a(:)\n  integer :: stat\n  checks=0\n")
    p.add_line_with_feature("  allocate(a(3:5), stat=stat)\n", "3:5", "1:3", "feature-default-lower-same-extent")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("lower", "lbound(a,1)", 3, 1, category="lower")
    p.guard_equal("upper", "ubound(a,1)", 5, 3, category="upper")
    p.guard_equal("size", "size(a)", 3, 4, category="size")
    p.add_input_line("  a = [31, 32, 33]\n", "31", "34", "input-first-sentinel")
    append_last_input(p, "32", "35", "input-middle-sentinel")
    append_last_input(p, "33", "36", "input-upper-sentinel")
    p.guard_equal("value-lower", "a(3)", 31, 32)
    p.guard_equal("value-middle", "a(4)", 32, 31)
    p.guard_equal("value-upper", "a(5)", 33, 31)
    p.finish()
    return p


def default_lower_program():
    p = Program("default_lower")
    start_program(p)
    p.add("  integer, allocatable :: a(:), b(:)\n  integer :: stat\n  checks=0\n")
    p.add_line_with_feature("  allocate(a(4), stat=stat)\n", "a(4)", "a(-2:1)", "feature-explicit-nonunit-lower")
    p.add("  allocate(b(-2:1))\n")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("a-lower", "lbound(a,1)", 1, -2, category="lower")
    p.guard_equal("a-upper", "ubound(a,1)", 4, 1, category="upper")
    p.guard_equal("a-size", "size(a)", 4, 3, category="size")
    p.guard_equal("b-lower-control", "lbound(b,1)", -2, 1, category="control")
    p.guard_equal("b-upper-control", "ubound(b,1)", 1, 4, category="control")
    p.add_input_line("  a = [41, 42, 43, 44]\n", "41", "45", "input-a-first-sentinel")
    append_last_input(p, "42", "46", "input-a-second-sentinel")
    append_last_input(p, "43", "47", "input-a-third-sentinel")
    append_last_input(p, "44", "48", "input-a-fourth-sentinel")
    p.add_input_line("  b = [61, 62, 63, 64]\n", "61", "65", "input-b-first-sentinel")
    append_last_input(p, "62", "66", "input-b-second-sentinel")
    append_last_input(p, "63", "67", "input-b-third-sentinel")
    append_last_input(p, "64", "68", "input-b-fourth-sentinel")
    p.guard_equal("a-value-lower", "a(1)", 41, 42)
    p.guard_equal("a-value-second", "a(2)", 42, 41)
    p.guard_equal("a-value-third", "a(3)", 43, 42)
    p.guard_equal("a-value-upper", "a(4)", 44, 41)
    p.guard_equal("b-value-lower", "b(-2)", 61, 62)
    p.guard_equal("b-value-second", "b(-1)", 62, 61)
    p.guard_equal("b-value-third", "b(0)", 63, 62)
    p.guard_equal("b-value-upper", "b(1)", 64, 61)
    p.finish()
    return p


def bound_capture_program():
    p = Program("bound_capture")
    start_program(p)
    p.add("  integer, allocatable :: a(:)\n  integer :: lo, hi, stat\n  checks=0\n")
    p.add_input_line("  lo = 2\n", "2", "3", "input-lo")
    p.add_input_line("  hi = 4\n", "4", "5", "input-hi")
    p.add_line_with_feature("  allocate(a(lo:hi), stat=stat)\n", "lo:hi", "1:3", "feature-ignore-bound-vars")
    p.add("  lo = -5\n  hi = 9\n")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("lower-captured", "lbound(a,1)", 2, -5, category="lower")
    p.guard_equal("upper-captured", "ubound(a,1)", 4, 9, category="upper")
    p.guard_equal("size-captured", "size(a)", 3, 4, category="size")
    p.add_input_line("  a = [52, 53, 54]\n", "52", "55", "input-first-sentinel")
    append_last_input(p, "53", "56", "input-middle-sentinel")
    append_last_input(p, "54", "57", "input-upper-sentinel")
    p.guard_equal("value-lower", "a(2)", 52, 53)
    p.guard_equal("value-middle", "a(3)", 53, 52)
    p.guard_equal("value-upper", "a(4)", 54, 52)
    p.guard_equal("changed-lo", "lo", -5, 2, category="control")
    p.guard_equal("changed-hi", "hi", 9, 4, category="control")
    p.finish()
    return p


def zero_extent_program():
    p = Program("zero_extent")
    start_program(p)
    p.add("  integer, allocatable :: a(:)\n  integer :: stat, reached\n  checks=0\n")
    p.add_input_line("  reached=917\n", "917", "918", "input-path-sentinel")
    p.add_line_with_feature("  allocate(a(5:3), stat=stat)\n", "5:3", "5:5", "feature-nonzero-extent")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("size-zero", "size(a)", 0, 1, category="size")
    p.guard_equal("path-sentinel", "reached", 917, 918, category="path")
    p.finish()
    return p


def source_shape_bounds_program():
    p = Program("source_shape_bounds")
    start_program(p)
    p.add("  integer, allocatable :: s(:,:), a(:,:)\n  integer :: stat\n  checks=0\n")
    p.add("  allocate(s(-3:-1,5:8))\n")
    for line in (
        "  s(-3,5)=305\n", "  s(-2,5)=205\n", "  s(-1,5)=105\n", "  s(-3,6)=306\n",
        "  s(-2,6)=206\n", "  s(-1,6)=106\n", "  s(-3,7)=307\n", "  s(-2,7)=207\n",
        "  s(-1,7)=107\n", "  s(-3,8)=308\n", "  s(-2,8)=208\n", "  s(-1,8)=108\n"):
        p.add_input_line(line, line.split("=")[1].strip(), str(int(line.split("=")[1]) + 1),
                         "input-" + line.split("=")[0].strip().replace("s", "s-").replace("(", "").replace(")", "").replace(",", "-"))
    p.add_line_with_feature("  allocate(a, source=s, stat=stat)\n", "a, source=s", "a(1:3,1:4), source=s", "feature-explicit-default-bounds")
    p.add("  deallocate(s)\n  allocate(s(11:12,-7:-5))\n  s = 719\n")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_any("lower", "lbound(a)", "[-3,5]", "[1,1]", category="lower")
    p.guard_any("upper", "ubound(a)", "[-1,8]", "[3,4]", category="upper")
    p.guard_any("shape", "shape(a)", "[3,4]", "[4,3]", category="shape")
    p.guard_equal("value-lower-corner", "a(-3,5)", 305, 306)
    p.guard_equal("value-left-middle", "a(-2,5)", 205, 206)
    p.guard_equal("value-left-upper", "a(-1,5)", 105, 106)
    p.guard_equal("value-second-lower", "a(-3,6)", 306, 305)
    p.guard_equal("value-second-middle", "a(-2,6)", 206, 205)
    p.guard_equal("value-second-upper", "a(-1,6)", 106, 105)
    p.guard_equal("value-third-lower", "a(-3,7)", 307, 306)
    p.guard_equal("value-interior", "a(-2,7)", 207, 208)
    p.guard_equal("value-third-upper", "a(-1,7)", 107, 106)
    p.guard_equal("value-right-middle", "a(-2,8)", 208, 207)
    p.guard_equal("value-upper-corner", "a(-1,8)", 108, 107)
    p.guard_any("source-new-lower-control", "lbound(s)", "[11,-7]", "[-3,5]", category="control")
    p.guard_equal("a-retained-after-source-change", "a(-3,8)", 308, 719)
    p.finish()
    return p


def source_same_rank_vector_program():
    p = Program("source_same_rank_vector")
    start_program(p)
    p.add("  integer, allocatable :: a(:)\n  integer :: stat\n  checks=0\n")
    p.add_line_with_feature("  allocate(a(-4:-2), source=[11,22,33], stat=stat)\n",
                            "-4:-2", "1:3", "feature-default-bounds-same-size")
    append_last_input(p, "11", "12", "input-vector-first")
    append_last_input(p, "22", "23", "input-vector-second")
    append_last_input(p, "33", "34", "input-vector-third")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("lower", "lbound(a,1)", -4, 1, category="lower")
    p.guard_equal("upper", "ubound(a,1)", -2, 3, category="upper")
    p.guard_equal("size", "size(a)", 3, 4, category="size")
    p.guard_equal("value-first", "a(-4)", 11, 12)
    p.guard_equal("value-second", "a(-3)", 22, 21)
    p.guard_equal("value-third", "a(-2)", 33, 32)
    p.finish()
    return p


def source_scalar_broadcast_program():
    p = Program("source_scalar_broadcast")
    start_program(p)
    p.add("  integer, allocatable :: a(:)\n  integer :: stat\n  checks=0\n")
    p.add_line_with_feature("  allocate(a(-2:2), source=7, stat=stat)\n",
                            "-2:2", "1:5", "feature-default-lower-same-size")
    append_last_input(p, "7", "8", "input-scalar-source")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("lower", "lbound(a,1)", -2, 1, category="lower")
    p.guard_equal("upper", "ubound(a,1)", 2, 5, category="upper")
    p.guard_equal("size", "size(a)", 5, 4, category="size")
    for sub in range(-2, 3):
        p.guard_equal(f"value-{sub}", f"a({sub})", 7, 8)
    p.finish()
    p.reverse_mutations.append(dict(
        id="reverse-source-seven-to-eight-with-oracle", kind="reverse", category="sentinel-load-bearing",
        replacements=[{"expected": "source=7", "replacement": "source=8"},
                      {"expected": "/= 7", "replacement": "/= 8", "all": True}],
        mutation="reverse-input-and-oracle-sentinel", intended="pass"))
    return p


def source_rank_two_array_program():
    p = Program("source_rank_two_array")
    start_program(p)
    p.add("  integer :: s(2:4,7:8)\n  integer, allocatable :: a(:,:)\n  integer :: stat\n  checks=0\n")
    for line in ("  s(2,7)=127\n", "  s(3,7)=137\n", "  s(4,7)=147\n",
                 "  s(2,8)=128\n", "  s(3,8)=138\n", "  s(4,8)=148\n"):
        p.add_input_line(line, line.split("=")[1].strip(), str(int(line.split("=")[1]) + 1),
                         "input-" + line.split("=")[0].strip().replace("s", "s-").replace("(", "").replace(")", "").replace(",", "-"))
    p.add_line_with_feature("  allocate(a(2:4,7:8), source=s, stat=stat)\n",
                            "2:4,7:8", "1:3,1:2", "feature-default-bounds-same-shape")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_any("lower", "lbound(a)", "[2,7]", "[1,1]", category="lower")
    p.guard_any("upper", "ubound(a)", "[4,8]", "[3,2]", category="upper")
    p.guard_any("shape", "shape(a)", "[3,2]", "[2,3]", category="shape")
    p.guard_equal("value-lower-corner", "a(2,7)", 127, 128)
    p.guard_equal("value-lower-middle", "a(3,7)", 137, 127)
    p.guard_equal("value-lower-upper", "a(4,7)", 147, 137)
    p.guard_equal("value-upper-left", "a(2,8)", 128, 127)
    p.guard_equal("value-middle", "a(3,8)", 138, 137)
    p.guard_equal("value-upper-corner", "a(4,8)", 148, 147)
    p.finish()
    return p


def source_evaluated_once_program():
    p = Program("source_evaluated_once")
    start_program(p)
    p.add("  integer, allocatable :: a\n  integer :: stat\n  counter=0\n  checks=0\n")
    p.text = p.text.replace("  integer :: checks\n", "  integer :: checks\n  integer, save :: counter\n")
    p.add_line_with_feature("  allocate(a, source=produce(), stat=stat)\n",
                            "produce()", "produce()+produce()", "feature-evaluate-source-twice")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_equal("counter-once", "counter", 1, 2, category="evaluation-count")
    p.guard_equal("source-value", "a", 79, 158, category="value")
    p.guard_equal("check-total", "checks", 4, 5, category="completion", counter=None)
    literal = COMPLETIONS[p.variant].rstrip("\n")
    prefix = "  write(*,'(a)') '"
    start = len(p.text) + len(prefix)
    completion = dict(
        id="completion-output", guard_id="completion-output", kind="output", category="completion",
        expected=literal, replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
        line=p.text.count("\n") + 1, counter=None, activation=None, mutation="completion-literal",
        failure_stdout="")
    completion["block_span"] = p.add(prefix + literal + "'\n")
    p.guards.append(completion)
    p.add("contains\n  integer function produce()\n    counter=counter+1\n")
    p.add_input_line("    produce=79\n", "79", "80", "input-produce-result")
    p.add("  end function produce\n")
    p.add(f"end program allocate_execution_{p.variant}\n")
    return p


def mold_undefined_value_program():
    p = Program("mold_undefined_value")
    start_program(p)
    p.add("  integer, allocatable :: mold(:,:), a(:,:)\n  integer :: stat\n  checks=0\n")
    p.add_line_with_feature("  allocate(mold(-6:-4,2:5))\n", "-6:-4,2:5", "1:3,1:4", "feature-mold-bounds-perturbed")
    p.add_line_with_feature("  allocate(a, mold=mold, stat=stat)\n", "a, mold=mold", "a(1:3,1:4), mold=mold", "feature-explicit-default-bounds")
    p.guard_equal("stat-success", "stat", 0, 91, category="status")
    p.guard_true("allocated", "allocated(a)")
    p.guard_any("lower", "lbound(a)", "[-6,2]", "[1,1]", category="lower")
    p.guard_any("upper", "ubound(a)", "[-4,5]", "[3,4]", category="upper")
    p.guard_any("shape", "shape(a)", "[3,4]", "[4,3]", category="shape")
    p.add_input_line("  a(-6,2)=612\n", "612", "613", "input-written-lower-corner")
    p.add_input_line("  a(-4,5)=445\n", "445", "446", "input-written-upper-corner")
    p.guard_equal("written-lower-corner", "a(-6,2)", 612, 613)
    p.guard_equal("written-upper-corner", "a(-4,5)", 445, 446)
    p.finish()
    return p


def _find_last(text, token):
    start = text.rindex(token)
    return [start, start + len(token)]


def append_last_input(p, token, replacement, name):
    span = _find_last(p.text, token)
    p.input_mutations.append(dict(
        id=name, kind="input", category="input", expected=token, replacement=replacement, span=span,
        line=p.text[:span[0]].count("\n") + 1, mutation="input-literal"))


PROGRAMS = {
    "explicit_bounds": explicit_bounds_program,
    "default_lower": default_lower_program,
    "bound_capture": bound_capture_program,
    "zero_extent": zero_extent_program,
    "source_shape_bounds": source_shape_bounds_program,
    "source_same_rank_vector": source_same_rank_vector_program,
    "source_scalar_broadcast": source_scalar_broadcast_program,
    "source_rank_two_array": source_rank_two_array_program,
    "source_evaluated_once": source_evaluated_once_program,
    "mold_undefined_value": mold_undefined_value_program,
}


def source_specs():
    specs = {}
    for variant in VARIANTS:
        p = PROGRAMS[variant]()
        raw = p.text.encode("ascii")
        probes = []
        omissions = []
        for guard in p.guards:
            start, end = guard["span"]
            if raw[start:end].decode("ascii") != guard["expected"]:
                raise ValueError(f"guard span lost parent binding: {variant} {guard['id']}")
            probes.append(dict(guard))
            if guard["kind"] == "guard" and guard.get("counter"):
                start, end = guard["block_span"]
                omissions.append(dict(
                    id="omit-observation-" + guard["id"], guard_id="check-total", kind="guard",
                    category="omission", expected=p.text[start:end], replacement="", span=[start, end],
                    line=p.text[:start].count("\n") + 1, mutation="whole-observation-omission",
                    failure_token=f"AEX:{variant}:check-total", failure_stdout=f"AEX:{variant}:check-total\n"))
        completion = p.guards[-1]
        omissions.append(dict(
            id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
            expected=p.text[completion["block_span"][0]:completion["block_span"][1]], replacement="",
            span=completion["block_span"], line=p.text[:completion["block_span"][0]].count("\n") + 1,
            mutation="completion-statement-omission", failure_stdout=""))
        for mutation in p.input_mutations + p.feature_mutations:
            start, end = mutation["span"]
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError(f"mutation span lost parent binding: {variant} {mutation['id']}")
        name = identifier(variant)
        specs[name] = dict(
            id=name, variant=variant, rule=p.rule, facets=p.facets, evidence="effect", standard="f2023",
            phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[variant],
            guards=p.guards, probes=probes, omissions=omissions, input_mutations=p.input_mutations,
            feature_mutations=p.feature_mutations, reverse_mutations=p.reverse_mutations,
            observations=p.observations, expected_counts=dict(checks=len(p.observations)))
    return specs


def wrong_oracle_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def mutated_source(spec, mutation):
    if mutation.get("kind") != "reverse":
        return wrong_oracle_source(spec, mutation)
    text = spec["source"]
    for item in mutation["replacements"]:
        count = -1 if item.get("all") else 1
        if item["expected"] not in text:
            raise ValueError("reverse mutation token not found")
        text = text.replace(item["expected"], item["replacement"], count)
    return text.encode("ascii")


def all_mutations(spec):
    return spec["probes"] + spec["omissions"] + spec["input_mutations"] + spec["feature_mutations"]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("allocate_execution_" + spec["variant"])
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
            raise ValueError("selected ALLOCATE execution facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        limitation = owner.get("oracle_limitation", "")
        old = ("This is a source-only catalogue. It creates no Fortran test program, compiler invocation, "
               "execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.")
        new = ("The original source-only catalogue created no Fortran test program, compiler invocation, "
               "execution evidence, evidence link, fixture approval, oracle approval, or coverage claim; "
               "this generator supplies selected runtime fixtures and mutation plans without granting "
               "those approvals or claims.")
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
        "Source-only draft catalogue: `doc/catalogues/execution_of_allocate_statement_9_7_1_2.json`.\n"
        "No Fortran test program, compiler invocation, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/execution_of_allocate_statement_9_7_1_2.json`. The original source-only "
        "registration supplied pending plans; the bounded runtime fixtures below supply selected cases and "
        "mutation plans, not oracle approval, fixture approval, source-review renewal, or universal coverage.")
    before = before.replace(
        "All facets in this packet are pending source plans. Multi-image coarray allocation, failed/stopped images, and teams are separate gated capabilities.",
        "Selected single-image allocation, SOURCE= and MOLD= effects now have executable fixtures. "
        "Upper-bounds-expr allocation, coarray allocation, failed/stopped images, error-condition and "
        "polymorphic/undefined-source boundaries remain pending or separately gated.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## ALLOCATE execution runtime observations\n\n"
        "Ten complete run/effect/f2023 fixtures cover thirteen selected facets of 9.7.1.2: five "
        "allocate-shape-spec-list effects, three SOURCE-shaped bounds effects, four ordinary SOURCE= "
        "value/evaluation effects, and one MOLD= undefined-value effect. Nonzero sentinels are used for "
        "all payload and path observations. Except for the default-lower-bound and scalar-allocation "
        "facets, nonzero-extent array cases use nonunit lower bounds; rank-two cases use distinct extents. "
        "Every relevant fixture checks lower bounds, upper bounds, shape or size, "
        "and copied or freshly assigned values rather than ALLOCATED alone. Zero-size fixtures never read "
        "an element. MOLD= fixtures never read the undefined mold value.\n\n"
        "Generated mutation metadata covers every oracle guard, completion line, selected input literal, "
        "omission, and an ALLOCATE feature-level perturbation for every fixture. Feature mutations include "
        "defaulting or perturbing allocation bounds, replacing SOURCE-shaped and MOLD-shaped allocation "
        "with explicit default bounds, perturbing MOLD source bounds, and evaluating SOURCE twice. A reverse source-sentinel "
        "control for scalar SOURCE= changes both the sentinel and its oracle to demonstrate that the "
        "sentinel is load-bearing.\n\n"
        "The parenthesized upper-bounds-expr form in S9.7.1.2-002, coarray/team facets, deterministic error "
        "paths, polymorphic ancestor-component SOURCE=, and undefined-source definition-status boundaries "
        "remain pending with their original plans. No TRANSFER, LOC, storage-layout, resource-exhaustion, "
        "ERRMSG-text, compiler-consensus, or undefined-association oracle is used.\n"
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
            raise ValueError("stale ALLOCATE execution fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} ALLOCATE execution cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(all_mutations(row)) for row in specs.values())} failing mutations and "
          f"{sum(len(row['reverse_mutations']) for row in specs.values())} reverse controls.")


if __name__ == "__main__":
    main()
