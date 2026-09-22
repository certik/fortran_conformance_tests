#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 masked WHERE assignment semantics."""

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
SECTION = "10.2.3.2"
CATALOGUE = "doc/catalogues/interpretation_of_masked_array_assignments_10_2_3_2.json"
FORM_SECTION = "10.2.3.1"
FORM_CATALOGUE = "doc/catalogues/general_form_of_the_masked_array_assignment_10_2_3_1.json"
VIEW = "doc/fortran_2023_10_2_3_2.md"
SUMMARY_BEGIN = "<!-- BEGIN WHERE MASKING FIXTURES -->"
SUMMARY_END = "<!-- END WHERE MASKING FIXTURES -->"

SCENARIOS = {
    "where_stmt_nonunit": "top-level WHERE statement with nonunit lower bound and mixed mask",
    "where_construct_simple": "top-level WHERE construct without ELSEWHERE leaves false-mask sentinels",
    "where_construct_elsewhere": "top-level WHERE construct with masked ELSEWHERE and final ELSEWHERE",
    "nested_construct_simple": "nested WHERE construct partitions outer true elements by inner mask",
    "nested_construct_restore": "nested WHERE construct restores outer control and pending masks",
    "nested_stmt_simple": "nested WHERE statement selects outer-and-inner true only",
    "nested_stmt_pending": "nested WHERE statement does not alter outer pending mask",
    "nested_stmt_restore": "nested WHERE statement restores the outer control mask",
}

VARIANTS = {
    "where_stmt_top_level_selected": ("S10.2.3.2-001", "top-level-where-stmt-selected-elements", "where_stmt_nonunit"),
    "where_stmt_selected_assigned": ("S10.2.3.2-012", "where-stmt-selected-elements-assigned", "where_stmt_nonunit"),
    "where_stmt_unselected_unchanged": ("S10.2.3.2-012", "where-stmt-unselected-elements-unchanged", "where_stmt_nonunit"),
    "corresponding_element_values": ("S10.2.3.2-012", "corresponding-element-values", "where_stmt_nonunit"),
    "construct_initial_then_region": ("S10.2.3.2-001", "top-level-where-construct-initial-then-region", "where_construct_simple"),
    "construct_selected_assigned": ("S10.2.3.2-012", "where-construct-selected-elements-assigned", "where_construct_simple"),
    "construct_unselected_unchanged": ("S10.2.3.2-012", "where-construct-unselected-elements-unchanged", "where_construct_simple"),
    "construct_initial_pending_region": ("S10.2.3.2-001", "top-level-where-construct-initial-pending-region", "where_construct_elsewhere"),
    "masked_elsewhere_selects_pending_true": ("S10.2.3.2-004", "masked-elsewhere-selects-prior-pending-and-mask-true", "where_construct_elsewhere"),
    "masked_elsewhere_excludes_prior_true": ("S10.2.3.2-004", "masked-elsewhere-leaves-prior-true-excluded", "where_construct_elsewhere"),
    "masked_elsewhere_pending_retains_false": ("S10.2.3.2-004", "masked-elsewhere-pending-retains-mask-false", "where_construct_elsewhere"),
    "elsewhere_selects_current_pending": ("S10.2.3.2-005", "elsewhere-selects-current-pending", "where_construct_elsewhere"),
    "elsewhere_does_not_reopen_prior": ("S10.2.3.2-005", "elsewhere-does-not-reopen-prior-branches", "where_construct_elsewhere"),
    "nested_construct_then_requires_outer_inner": ("S10.2.3.2-007", "nested-construct-then-requires-outer-and-inner-true", "nested_construct_simple"),
    "nested_construct_elsewhere_requires_outer_not_inner": ("S10.2.3.2-007", "nested-construct-elsewhere-requires-outer-true-inner-false", "nested_construct_simple"),
    "nested_construct_outer_false_unchanged": ("S10.2.3.2-007", "nested-construct-outer-false-remains-unassigned", "nested_construct_simple"),
    "nested_construct_restores_outer_control": ("S10.2.3.2-006", "nested-construct-restores-outer-control", "nested_construct_restore"),
    "nested_construct_restores_outer_pending": ("S10.2.3.2-006", "nested-construct-restores-outer-pending", "nested_construct_restore"),
    "nested_stmt_requires_outer_inner": ("S10.2.3.2-008", "nested-where-stmt-requires-outer-and-inner-true", "nested_stmt_simple"),
    "nested_stmt_outer_false_unchanged": ("S10.2.3.2-008", "nested-where-stmt-outer-false-unchanged", "nested_stmt_simple"),
    "nested_stmt_pending_not_altered": ("S10.2.3.2-008", "nested-where-stmt-does-not-change-outer-pending", "nested_stmt_pending"),
    "nested_stmt_restores_outer_control": ("S10.2.3.2-006", "nested-where-stmt-restores-outer-control", "nested_stmt_restore"),
}

FACETS_BY_RULE = {}
for rule, facet, _ in VARIANTS.values():
    FACETS_BY_RULE.setdefault(rule, set()).add(facet)
FACETS_BY_RULE = {rule: tuple(sorted(facets)) for rule, facets in sorted(FACETS_BY_RULE.items())}

REMAINING_PENDING = {
    "S10.2.3.2-001": set(),
    "S10.2.3.2-004": set(),
    "S10.2.3.2-005": set(),
    "S10.2.3.2-006": set(),
    "S10.2.3.2-007": {"nested-construct-mask-snapshot-source-control"},
    "S10.2.3.2-008": set(),
    "S10.2.3.2-012": set(),
}

COMPLETIONS = {
    variant: "WHERE MASKING " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}

ORACLE_PREFIX = {
    rule: rule + " WHERE masking runtime fixtures: " for rule in FACETS_BY_RULE
}
LIMIT_PREFIX = {
    rule: rule + " WHERE masking fixture boundaries: " for rule in FACETS_BY_RULE
}

ORACLES = {
    "S10.2.3.2-001": ORACLE_PREFIX["S10.2.3.2-001"] + (
        "three complete run/effect/f2023 programs execute a top-level WHERE statement and two top-level "
        "WHERE constructs with side-effect-free logical array masks. The statement case declares "
        "INTEGER actual(-2:3), preloads every element with a distinct negative sentinel, assigns "
        "coordinate-specific RHS values under the mask [.TRUE.,.FALSE.,.TRUE.,.FALSE.,.TRUE.,.FALSE.], "
        "and checks selected and unselected elements directly. The construct-then case uses a construct "
        "without ELSEWHERE to show that its initial control mask selects only true-mask elements. The "
        "ELSEWHERE case uses initial mask [T,F,F,T,F,T] and a masked-ELSEWHERE mask [T,T,F,T,F,F]; "
        "direct final values 101,202,303,104,305,106 show that the construct pending mask is the "
        "complement of the initial mask and feeds later ELSEWHERE branches. No expected value is computed "
        "with MERGE, PACK, COUNT, UNPACK or an equivalent selection intrinsic."
    ),
    "S10.2.3.2-004": ORACLE_PREFIX["S10.2.3.2-004"] + (
        "six direct element checks in the shared masked-ELSEWHERE scenario distinguish all p4 classes. "
        "For initial mask [T,F,F,T,F,T] and ELSEWHERE mask [T,T,F,T,F,F], prior-pending/mask-true "
        "element 2 receives 202, initial-true elements 1 and 4 keep 101 and 104 even though the "
        "ELSEWHERE mask is true there, and prior-pending/mask-false elements 3 and 5 are left for the "
        "final ELSEWHERE values 303 and 305. Treating the masked ELSEWHERE as using only its own mask, "
        "or failing to carry mc .AND. .NOT. mask into the pending mask, changes at least one asserted "
        "literal."
    ),
    "S10.2.3.2-005": ORACLE_PREFIX["S10.2.3.2-005"] + (
        "the final ELSEWHERE in the same three-branch construct observes the current pending mask after "
        "the masked ELSEWHERE. Elements 3 and 5, which are initial-false and masked-ELSEWHERE-false, "
        "receive 303 and 305. Elements already handled by the initial WHERE body or the masked ELSEWHERE "
        "retain 101, 202, 104 and 106, proving that ELSEWHERE neither reopens prior branches nor creates "
        "a new pending mask visible in this construct."
    ),
    "S10.2.3.2-006": ORACLE_PREFIX["S10.2.3.2-006"] + (
        "three nested fixtures observe restoration through later ordinary assignments or outer ELSEWHERE "
        "branches. In the nested-construct restoration case, outer mask [T,T,F,F,T,T] and inner mask "
        "[T,F,T,F,F,T] first produce inner values 101,202,205,106 for the outer-true elements; after "
        "END WHERE restores the outer control mask, a following outer-body assignment adds 1000 to all "
        "and only outer-true elements, and the outer ELSEWHERE assigns 303 and 304 to the original "
        "outer-false elements. The nested-statement restoration fixture similarly proves that a WHERE "
        "statement body restores the outer control mask before a following outer assignment, giving "
        "1101,98,-803,-804,95,1106 from distinguishable sentinels and inner values."
    ),
    "S10.2.3.2-007": ORACLE_PREFIX["S10.2.3.2-007"] + (
        "three fixtures over the four outer/inner truth classes execute an actual nested WHERE construct "
        "inside a WHERE body. With outer [T,T,F,F,T,T] and inner [T,F,T,F,F,T], the nested THEN assigns "
        "only positions 1 and 6 to 101 and 106, the nested ELSEWHERE assigns only outer-true/inner-false "
        "positions 2 and 5 to 202 and 205, and outer-false positions 3 and 4 retain sentinels -803 and "
        "-804. If a processor treated the nested construct like a WHERE statement with no nested pending "
        "mask, positions 2 and 5 would not receive the 200-series values. If it ignored the outer mask, "
        "positions 3 or 4 would lose their sentinels."
    ),
    "S10.2.3.2-008": ORACLE_PREFIX["S10.2.3.2-008"] + (
        "three fixtures execute a nested WHERE statement, not a construct, with the same outer and inner "
        "masks. The simple nested-statement fixture assigns only outer-true/inner-true positions 1 and 6, "
        "leaving outer-true/inner-false and outer-false positions at sentinels. A separate pending-mask "
        "fixture places an outer ELSEWHERE after the nested statement: positions 3 and 4, the original "
        "outer-false elements, receive 303 and 304, while positions 2 and 5 remain sentinels. If the "
        "nested statement incorrectly established a pending mask like a construct, positions 2 and 5 "
        "would be assigned by the outer ELSEWHERE and positions 3 and 4 would differ."
    ),
    "S10.2.3.2-012": ORACLE_PREFIX["S10.2.3.2-012"] + (
        "five fixtures make the p12 assignment effect non-vacuous. The WHERE statement case uses "
        "nonunit bounds -2:3, direct scalar RHS literals 501,503,505 for selected elements, and distinct "
        "negative sentinels at every unselected element. The construct case separately checks that true "
        "mask elements receive their corresponding RHS values and false mask elements retain sentinels. "
        "The corresponding-element-values fixture relies on the same nonunit lower-bound statement source "
        "and checks each selected scalar subscript against a hand-written literal, not against a packed or "
        "merged oracle."
    ),
}

LIMITATIONS = {
    "S10.2.3.2-001": LIMIT_PREFIX["S10.2.3.2-001"] + (
        "only the three top-level control/pending facets are established. These programs do not prove mask "
        "evaluation counts, element assignment order, function side effects, invalid-shape diagnostics or "
        "storage implementation."
    ),
    "S10.2.3.2-004": LIMIT_PREFIX["S10.2.3.2-004"] + (
        "only branch membership and final values for a masked ELSEWHERE are observed. The fixtures do not "
        "infer the order of element assignments, the number of times a mask expression is evaluated, or "
        "whether expressions for unselected elements were evaluated."
    ),
    "S10.2.3.2-005": LIMIT_PREFIX["S10.2.3.2-005"] + (
        "only final ELSEWHERE membership after one masked ELSEWHERE is represented. No diagnostic, "
        "processor-temporary, storage or per-element ordering claim is made."
    ),
    "S10.2.3.2-006": LIMIT_PREFIX["S10.2.3.2-006"] + (
        "the fixtures observe restoration only through subsequent branch membership and scalar integer "
        "values. They do not assert a stack representation for masks or any order among element updates."
    ),
    "S10.2.3.2-007": LIMIT_PREFIX["S10.2.3.2-007"] + (
        "the three runtime branch-membership facets are covered. The nested-construct-mask-snapshot-source-control "
        "facet remains pending because p7's at-most-once wording cannot be proven by a conforming call-count or "
        "side-effect oracle."
    ),
    "S10.2.3.2-008": LIMIT_PREFIX["S10.2.3.2-008"] + (
        "only nested statement control and unchanged-pending effects are observed. These cases do not claim "
        "mask-expression evaluation counts, function side-effect ordering or diagnostics."
    ),
    "S10.2.3.2-012": LIMIT_PREFIX["S10.2.3.2-012"] + (
        "only integer array assignment with side-effect-free masks is represented. The fixtures do not test "
        "defined assignment, character padding, real or complex values, evaluation of unselected RHS expressions, "
        "or element assignment order."
    ),
}


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown WHERE masking variant")
    rule, _, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__where_masking_" + variant


def program_unit_name(variant):
    return "wm" + f"{list(VARIANTS).index(variant) + 1:02d}"


class Program:
    def __init__(self, variant, rule, facet, scenario):
        self.variant = variant
        self.rule = rule
        self.facet = facet
        self.scenario = scenario
        self.text = ""
        self.guards = []
        self.probes = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def guard(self, name, expression, expected, replacement=None, *, category="value", counter="checks",
              observation=True):
        expected = str(expected)
        if replacement is None:
            replacement = str(int(expected) + 1)
        replacement = str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"WM:{self.variant}:{name}"
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
        if observation:
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


def bool_literal(value):
    return ".true." if value else ".false."


def emit_integer_values(p, name, values):
    for index, value in values.items():
        p.add(f"  {name}({index})={value}\n")


def emit_logical_values(p, name, values):
    for index, value in values.items():
        p.add(f"  {name}({index})={bool_literal(value)}\n")


def finish(p, expected, notes):
    p.add("\n")
    for note in notes:
        p.add("  ! " + note + "\n")
    for index in sorted(expected):
        p.guard(f"final-{index}", f"actual({index})", expected[index])
    total = p.guard("check-total", "checks", len(expected), len(expected) + 1,
                    category="completion", counter=None, observation=False)
    completion = p.completion()
    p.add(f"end program {program_unit_name(p.variant)}\n")
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


def program(variant):
    rule, facet, scenario = VARIANTS[variant]
    p = Program(variant, rule, facet, scenario)
    p.add(f"! rule: {rule}\n! covers: {facet}\n")
    p.add("! Sentinels are distinct from every value any WHERE branch can assign.\n")
    p.add("! Expected values below are hand-written scalar literals; no masking intrinsic is used.\n")
    unit_name = program_unit_name(variant)
    p.add(f"program {unit_name}\n  implicit none\n  integer :: checks\n")

    if scenario == "where_stmt_nonunit":
        indices = [-2, -1, 0, 1, 2, 3]
        sentinels = {-2: -902, -1: -901, 0: -900, 1: -899, 2: -898, 3: -897}
        rhs = {-2: 501, -1: 502, 0: 503, 1: 504, 2: 505, 3: 506}
        mask = {-2: True, -1: False, 0: True, 1: False, 2: True, 3: False}
        expected = {i: rhs[i] if mask[i] else sentinels[i] for i in indices}
        p.add("  integer :: actual(-2:3), rhs(-2:3)\n  logical :: mask(-2:3)\n  checks=0\n")
        emit_integer_values(p, "actual", sentinels)
        emit_integer_values(p, "rhs", rhs)
        emit_logical_values(p, "mask", mask)
        p.add("  ! Mask true at -2, 0 and 2; false elements must retain sentinels.\n")
        p.add("  where (mask) actual = rhs\n")
        notes = ["Expected final actual(-2:3) = [501,-901,503,-899,505,-897].",
                 "Ignoring the mask would write 502,504,506 into the false positions."]
    elif scenario == "where_construct_simple":
        indices = [1, 2, 3, 4, 5, 6]
        sentinels = {i: -700 - i for i in indices}
        rhs = {i: 100 + i for i in indices}
        mask = {1: True, 2: False, 3: True, 4: False, 5: False, 6: True}
        expected = {i: rhs[i] if mask[i] else sentinels[i] for i in indices}
        p.add("  integer :: actual(1:6), rhs(1:6)\n  logical :: mask(1:6)\n  checks=0\n")
        emit_integer_values(p, "actual", sentinels)
        emit_integer_values(p, "rhs", rhs)
        emit_logical_values(p, "mask", mask)
        p.add("  ! Construct control mask true at 1, 3 and 6.\n")
        p.add("  where (mask)\n    actual = rhs\n  end where\n")
        notes = ["Expected final actual(1:6) = [101,-702,103,-704,-705,106].",
                 "Treating the construct as unmasked would overwrite positions 2,4,5."]
    elif scenario == "where_construct_elsewhere":
        indices = [1, 2, 3, 4, 5, 6]
        sentinels = {i: -710 - i for i in indices}
        then_values = {i: 100 + i for i in indices}
        masked_values = {i: 200 + i for i in indices}
        else_values = {i: 300 + i for i in indices}
        first = {1: True, 2: False, 3: False, 4: True, 5: False, 6: True}
        second = {1: True, 2: True, 3: False, 4: True, 5: False, 6: False}
        expected = {1: 101, 2: 202, 3: 303, 4: 104, 5: 305, 6: 106}
        p.add("  integer :: actual(1:6), then_values(1:6), masked_values(1:6), else_values(1:6)\n")
        p.add("  logical :: first_mask(1:6), second_mask(1:6)\n  checks=0\n")
        emit_integer_values(p, "actual", sentinels)
        emit_integer_values(p, "then_values", then_values)
        emit_integer_values(p, "masked_values", masked_values)
        emit_integer_values(p, "else_values", else_values)
        emit_logical_values(p, "first_mask", first)
        emit_logical_values(p, "second_mask", second)
        p.add("  ! first_mask=[T,F,F,T,F,T], second_mask=[T,T,F,T,F,F].\n")
        p.add("  where (first_mask)\n    actual = then_values\n  elsewhere (second_mask)\n    actual = masked_values\n  elsewhere\n    actual = else_values\n  end where\n")
        notes = ["Expected final actual(1:6) = [101,202,303,104,305,106].",
                 "A masked ELSEWHERE using only second_mask would overwrite positions 1 and 4 with 201 and 204.",
                 "A final ELSEWHERE reopening prior branches would overwrite positions already set to 101,202,104,106."]
    elif scenario in {"nested_construct_simple", "nested_construct_restore"}:
        indices = [1, 2, 3, 4, 5, 6]
        sentinels = {i: -800 - i for i in indices}
        then_values = {i: 100 + i for i in indices}
        inner_else_values = {i: 200 + i for i in indices}
        outer_else_values = {i: 300 + i for i in indices}
        outer = {1: True, 2: True, 3: False, 4: False, 5: True, 6: True}
        inner = {1: True, 2: False, 3: True, 4: False, 5: False, 6: True}
        p.add("  integer :: actual(1:6), then_values(1:6), inner_else_values(1:6), outer_else_values(1:6)\n")
        p.add("  logical :: outer_mask(1:6), inner_mask(1:6)\n  checks=0\n")
        emit_integer_values(p, "actual", sentinels)
        emit_integer_values(p, "then_values", then_values)
        emit_integer_values(p, "inner_else_values", inner_else_values)
        emit_integer_values(p, "outer_else_values", outer_else_values)
        emit_logical_values(p, "outer_mask", outer)
        emit_logical_values(p, "inner_mask", inner)
        p.add("  ! outer=[T,T,F,F,T,T], inner=[T,F,T,F,F,T].\n")
        if scenario == "nested_construct_simple":
            expected = {1: 101, 2: 202, 3: -803, 4: -804, 5: 205, 6: 106}
            p.add("  where (outer_mask)\n    where (inner_mask)\n      actual = then_values\n    elsewhere\n      actual = inner_else_values\n    end where\n  end where\n")
            notes = ["Expected final actual(1:6) = [101,202,-803,-804,205,106].",
                     "Statement-like nesting would not give positions 2 and 5 the inner ELSEWHERE values.",
                     "Ignoring the outer mask would change positions 3 or 4 instead of preserving sentinels."]
        else:
            expected = {1: 1101, 2: 1202, 3: 303, 4: 304, 5: 1205, 6: 1106}
            p.add("  where (outer_mask)\n    where (inner_mask)\n      actual = then_values\n    elsewhere\n      actual = inner_else_values\n    end where\n    actual = actual + 1000\n  elsewhere\n    actual = outer_else_values\n  end where\n")
            notes = ["Expected final actual(1:6) = [1101,1202,303,304,1205,1106].",
                     "If END WHERE failed to restore outer control, positions 1 and 6 would miss the +1000 update.",
                     "If inner pending leaked outward, the outer ELSEWHERE would not assign exactly positions 3 and 4."]
    elif scenario in {"nested_stmt_simple", "nested_stmt_pending", "nested_stmt_restore"}:
        indices = [1, 2, 3, 4, 5, 6]
        sentinels = {i: -800 - i for i in indices}
        then_values = {i: 100 + i for i in indices}
        outer_else_values = {i: 300 + i for i in indices}
        outer = {1: True, 2: True, 3: False, 4: False, 5: True, 6: True}
        inner = {1: True, 2: False, 3: True, 4: False, 5: False, 6: True}
        p.add("  integer :: actual(1:6), then_values(1:6), outer_else_values(1:6)\n")
        p.add("  logical :: outer_mask(1:6), inner_mask(1:6)\n  checks=0\n")
        emit_integer_values(p, "actual", sentinels)
        emit_integer_values(p, "then_values", then_values)
        emit_integer_values(p, "outer_else_values", outer_else_values)
        emit_logical_values(p, "outer_mask", outer)
        emit_logical_values(p, "inner_mask", inner)
        p.add("  ! outer=[T,T,F,F,T,T], inner=[T,F,T,F,F,T].\n")
        if scenario == "nested_stmt_simple":
            expected = {1: 101, 2: -802, 3: -803, 4: -804, 5: -805, 6: 106}
            p.add("  where (outer_mask)\n    where (inner_mask) actual = then_values\n  end where\n")
            notes = ["Expected final actual(1:6) = [101,-802,-803,-804,-805,106].",
                     "A nested statement must require both outer and inner masks; outer-false position 3 has inner true but stays sentinel."]
        elif scenario == "nested_stmt_pending":
            expected = {1: 101, 2: -802, 3: 303, 4: 304, 5: -805, 6: 106}
            p.add("  where (outer_mask)\n    where (inner_mask) actual = then_values\n  elsewhere\n    actual = outer_else_values\n  end where\n")
            notes = ["Expected final actual(1:6) = [101,-802,303,304,-805,106].",
                     "If the nested statement altered pending like a construct, positions 2 and 5 would be assigned by the outer ELSEWHERE.",
                     "The original outer-false positions 3 and 4 prove the outer pending mask was preserved."]
        else:
            expected = {1: 1101, 2: 198, 3: -803, 4: -804, 5: 195, 6: 1106}
            p.add("  where (outer_mask)\n    where (inner_mask) actual = then_values\n    actual = actual + 1000\n  end where\n")
            notes = ["Expected final actual(1:6) = [1101,198,-803,-804,195,1106].",
                     "The +1000 assignment after the nested statement must use the restored outer control mask."]
    else:
        raise ValueError("unknown WHERE masking scenario")

    omissions = finish(p, expected, notes)
    raw = p.text.encode("ascii")
    for probe in p.probes + omissions:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError("a WHERE masking mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, scenario=scenario, scenario_note=SCENARIOS[scenario],
        rule=rule, facets=[facet], evidence="effect", standard="f2023", phase="run", source=p.text,
        source_sha256=sha(raw), completion=COMPLETIONS[variant], guards=p.guards, probes=p.probes,
        omissions=omissions, observations=p.observations, expected=expected)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("where_masking_" + spec["variant"])
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
    if set(FACETS_BY_RULE) - set(by_rule):
        raise ValueError("WHERE masking requirement IDs changed")
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("selected WHERE masking facets changed for " + rule)
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMITATIONS[rule])
        source_only = "This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no processor, approves no fixture or oracle, and claims no coverage."
        replacement = "The original source-only catalogue recorded pending plans only. The selected runtime fixtures now supply executable observations for the covered facets, while any facets still listed in pending remain unimplemented."
        if source_only in owner["oracle_limitation"]:
            owner["oracle_limitation"] = owner["oracle_limitation"].replace(source_only, replacement)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the WHERE interpretation generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\nNo Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Selected runtime fixtures now exercise executable WHERE masking effects; unlisted facets remain pending.\nNo oracle approval, fixture approval, or coverage claim is supplied by generation alone.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## WHERE masking runtime observations\n\n"
        "Twenty-two complete run/effect/f2023 programs observe selected 10.2.3.2 masked-array-assignment "
        "effects through direct scalar element inspections. They cover top-level WHERE statements, top-level "
        "WHERE constructs, masked ELSEWHERE and final ELSEWHERE pending-mask transitions, nested WHERE "
        "constructs, and nested WHERE statements. Every array element starts from a sentinel distinct from "
        "all branch values, every mask has a mix of true and false elements, and expected final values are "
        "hand-written integer literals. No MERGE, PACK, COUNT, UNPACK, ALL, ANY or equivalent selection "
        "intrinsic is used as an oracle.\n\n"
        "The nested construct and nested statement cases deliberately use the same outer mask "
        "[T,T,F,F,T,T] and inner mask [T,F,T,F,F,T]. A nested construct assigns outer-true/inner-false "
        "positions 2 and 5 in its own ELSEWHERE; a nested statement leaves those positions for later outer "
        "logic and does not alter the outer pending mask. Treating one form as the other changes the final "
        "arrays, so the distinction is non-vacuous.\n\n"
        "At-most-once mask evaluation, element assignment order, expression evaluation for unselected elements, "
        "function side effects, non-elemental full evaluation, array-constructor unmasked evaluation, diagnostics "
        "and source-control/name/shape records remain pending where not explicitly removed below.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the WHERE masking summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
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
            raise ValueError("stale WHERE masking fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} WHERE masking cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
