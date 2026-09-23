#!/usr/bin/env python3
"""Logical intrinsic operation interpretation fixtures for Fortran 2023 10.1.5.4.1."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha, wrong_oracle_source


ROOT = Path(__file__).resolve().parents[1]
SECTION = "10.1.5.4.1"
CATALOGUE = "doc/catalogues/logical_intrinsic_operation_interpretation_10_1_5_4_1.json"
VIEW = "doc/fortran_2023_10_1_5_4_1.md"
SUMMARY_BEGIN = "<!-- BEGIN LOGICAL INTRINSIC INTERPRETATION FIXTURES -->"
SUMMARY_END = "<!-- END LOGICAL INTRINSIC INTERPRETATION FIXTURES -->"
CHECK_SENTINEL = 17

VARIANTS = {
    "context_type": ("S10.1.5.4.1-001", ["logical-computation-context", "logical-result-type"]),
    "not_truth_table": ("S10.1.5.4.1-002", ["not-true-is-false", "not-false-is-true", "not-table10-5-10-6-consistency"]),
    "and_truth_table": ("S10.1.5.4.1-003", ["and-true-true", "and-true-false", "and-false-true", "and-false-false"]),
    "or_truth_table": ("S10.1.5.4.1-004", ["or-true-true", "or-true-false", "or-false-true", "or-false-false"]),
    "eqv_truth_table": ("S10.1.5.4.1-005", ["eqv-true-true", "eqv-true-false", "eqv-false-true", "eqv-false-false"]),
    "neqv_truth_table": ("S10.1.5.4.1-006", ["neqv-true-true", "neqv-true-false", "neqv-false-true", "neqv-false-false"]),
}
FACETS_BY_RULE = {}
for rule, facets in VARIANTS.values():
    FACETS_BY_RULE.setdefault(rule, []).extend(facets)
REMAINING_PENDING = {
    "S10.1.5.4.1-001": {"operand-type-delegation"},
    "S10.1.5.4.1-002": set(),
    "S10.1.5.4.1-003": set(),
    "S10.1.5.4.1-004": set(),
    "S10.1.5.4.1-005": set(),
    "S10.1.5.4.1-006": set(),
}
COMPLETIONS = {
    variant: "LOGICAL INTRINSIC INTERPRETATION " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
BINARY_TRUTH_TABLES = {
    ".and.": {"TT": True, "TF": False, "FT": False, "FF": False},
    ".or.": {"TT": True, "TF": True, "FT": True, "FF": False},
    ".eqv.": {"TT": True, "TF": False, "FT": False, "FF": True},
    ".neqv.": {"TT": False, "TF": True, "FT": True, "FF": False},
}
BINARY_VARIANT_OPERATORS = {
    "and_truth_table": ".and.",
    "or_truth_table": ".or.",
    "eqv_truth_table": ".eqv.",
    "neqv_truth_table": ".neqv.",
}
DISCRIMINATION_ROWS = {
    ".and.": {".or.": "TF", ".eqv.": "FF", ".neqv.": "TT"},
    ".or.": {".and.": "TF", ".eqv.": "TF", ".neqv.": "TT"},
    ".eqv.": {".and.": "FF", ".or.": "TF", ".neqv.": "TT"},
    ".neqv.": {".and.": "TT", ".or.": "TT", ".eqv.": "TT"},
}
ORACLE_PREFIXES = {
    rule: f"{rule} logical intrinsic interpretation runtime fixtures: "
    for rule in FACETS_BY_RULE
}
LIMIT_PREFIXES = {
    rule: f"{rule} logical intrinsic interpretation fixture boundaries: "
    for rule in FACETS_BY_RULE
}
ORACLES = {
    "S10.1.5.4.1-001": ORACLE_PREFIXES["S10.1.5.4.1-001"] + (
        "one complete run/effect/f2023 program uses intrinsic logical operations directly in an IF context "
        "and as actual arguments to LOGICAL dummy arguments. The context witness checks the expression "
        "(.FALSE. .OR. .TRUE.) in the IF itself. The result-type witnesses pass (.TRUE. .EQV. .FALSE.) "
        "and (.NOT. .FALSE.) directly to LOGICAL dummy arguments whose bodies check the hand-derived "
        "truth values. No result is first assigned to a declared LOGICAL variable whose declaration would "
        "launder the expression type."
    ),
    "S10.1.5.4.1-002": ORACLE_PREFIXES["S10.1.5.4.1-002"] + (
        "one complete run/effect/f2023 program asserts both rows of the unary .NOT. truth table directly: "
        ".NOT. .TRUE. is false and .NOT. .FALSE. is true. The same source ties the Table 10.5 negation "
        "interpretation to both Table 10.6 rows."
    ),
    "S10.1.5.4.1-003": ORACLE_PREFIXES["S10.1.5.4.1-003"] + (
        "one complete run/effect/f2023 program asserts the full .AND. table TT/T, TF/F, FT/F and FF/F "
        "with direct literal expressions. The FF row is present specifically to separate .AND. from .EQV., "
        "and the generated operator-substitution campaign replaces all four .AND. operator sites with each "
        "of .OR., .EQV. and .NEQV.; every replacement must fail."
    ),
    "S10.1.5.4.1-004": ORACLE_PREFIXES["S10.1.5.4.1-004"] + (
        "one complete run/effect/f2023 program asserts the full inclusive .OR. table TT/T, TF/T, FT/T and "
        "FF/F with direct literal expressions. The TT row is present specifically to separate .OR. from "
        ".NEQV., and the generated operator-substitution campaign replaces all four .OR. operator sites "
        "with each of .AND., .EQV. and .NEQV.; every replacement must fail."
    ),
    "S10.1.5.4.1-005": ORACLE_PREFIXES["S10.1.5.4.1-005"] + (
        "one complete run/effect/f2023 program asserts the full .EQV. table TT/T, TF/F, FT/F and FF/T "
        "with direct literal expressions. The FF row separates .EQV. from .AND. and the generated "
        "operator-substitution campaign replaces all four .EQV. sites with .AND., .OR. and .NEQV.; every "
        "replacement must fail."
    ),
    "S10.1.5.4.1-006": ORACLE_PREFIXES["S10.1.5.4.1-006"] + (
        "one complete run/effect/f2023 program asserts the full .NEQV. table TT/F, TF/T, FT/T and FF/F "
        "with direct literal expressions. The TT row separates .NEQV. from .OR. and .EQV., and the "
        "generated operator-substitution campaign replaces all four .NEQV. sites with .AND., .OR. and "
        ".EQV.; every replacement must fail."
    ),
}
LIMITATIONS = {
    "S10.1.5.4.1-001": LIMIT_PREFIXES["S10.1.5.4.1-001"] + (
        "only logical-computation-context and logical-result-type are represented. operand-type-delegation "
        "remains pending because 10.1.5.4.1 p1 delegates permitted operand types to 10.1.5.1; this packet "
        "does not create nonlogical-operand diagnostic/control claims. The result-type witnesses use default "
        "logical literal operands and LOGICAL dummy arguments, not representation bits or mixed-kind selection."
    ),
    "S10.1.5.4.1-002": LIMIT_PREFIXES["S10.1.5.4.1-002"] + (
        "only the two value rows and their Table 10.5/Table 10.6 consistency are represented. The fixture "
        "does not claim parsing ownership for R1019, nondefault kind coverage, or any evaluation-order property."
    ),
    "S10.1.5.4.1-003": LIMIT_PREFIXES["S10.1.5.4.1-003"] + (
        "only scalar default-logical literal .AND. interpretation is represented. No short-circuit, side-effect, "
        "array, reassociation, kind-selection, defined-operator, diagnostic or evaluation-order claim is made."
    ),
    "S10.1.5.4.1-004": LIMIT_PREFIXES["S10.1.5.4.1-004"] + (
        "only scalar default-logical literal .OR. interpretation is represented. No short-circuit, side-effect, "
        "array, reassociation, kind-selection, defined-operator, diagnostic or evaluation-order claim is made."
    ),
    "S10.1.5.4.1-005": LIMIT_PREFIXES["S10.1.5.4.1-005"] + (
        "only scalar default-logical literal .EQV. interpretation is represented. No precedence, kind-selection, "
        "defined-operator, array, diagnostic or evaluation-order claim is made."
    ),
    "S10.1.5.4.1-006": LIMIT_PREFIXES["S10.1.5.4.1-006"] + (
        "only scalar default-logical literal .NEQV. interpretation is represented. No precedence, kind-selection, "
        "defined-operator, array, diagnostic or evaluation-order claim is made."
    ),
}


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown logical intrinsic interpretation variant")
    rule, _ = VARIANTS[variant]
    suffix = variant.replace("_truth_table", "")
    return rule.replace(".", "_").replace("-", "_") + "_valid__logical_intrinsic_interpretation_" + suffix


def row_expression(row, operator):
    left = ".true." if row[0] == "T" else ".false."
    right = ".true." if row[1] == "T" else ".false."
    return f"{left} {operator} {right}"


def row_input_sites(row, operator):
    """Return one row-input mutation plan that flips this operator row result."""
    plans = {
        ".and.": {
            "TT": [(0, ".true.", ".false.")],
            "TF": [(0, ".false.", ".true.")],
            "FT": [(0, ".false.", ".true.")],
            "FF": [(0, ".false.", ".true."), (1, ".false.", ".true.")],
        },
        ".or.": {
            "TT": [(0, ".true.", ".false."), (1, ".true.", ".false.")],
            "TF": [(0, ".true.", ".false.")],
            "FT": [(0, ".true.", ".false.")],
            "FF": [(0, ".false.", ".true.")],
        },
        ".eqv.": {
            "TT": [(0, ".true.", ".false.")],
            "TF": [(0, ".false.", ".true.")],
            "FT": [(0, ".false.", ".true.")],
            "FF": [(0, ".false.", ".true.")],
        },
        ".neqv.": {
            "TT": [(0, ".true.", ".false.")],
            "TF": [(0, ".false.", ".true.")],
            "FT": [(0, ".false.", ".true.")],
            "FF": [(0, ".false.", ".true.")],
        },
    }
    return plans[operator][row]


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facets = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.probes = []
        self.input_mutations = []
        self.operator_mutations = []
        self.sentinel_mutations = []
        self.observations = []
        self.needs_logical_dummies = False
        self.sentinel_span = None

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def start(self):
        self.add(f"program lio_{self.variant}\n  implicit none\n  integer :: checks\n")
        prefix = "  checks="
        start = len(self.text) + len(prefix)
        self.add(prefix + str(CHECK_SENTINEL) + "\n")
        self.sentinel_span = [start, start + len(str(CHECK_SENTINEL))]

    def _input_mutation(self, name, expression_start, expression, plan, token):
        sites = []
        for occurrence, expected, replacement in plan:
            positions = []
            start_at = 0
            while True:
                pos = expression.find(expected, start_at)
                if pos < 0:
                    break
                positions.append(pos)
                start_at = pos + len(expected)
            if occurrence >= len(positions):
                raise ValueError(f"input token {expected} occurrence {occurrence} not found in {expression}")
            pos = positions[occurrence]
            sites.append(dict(
                span=[expression_start + pos, expression_start + pos + len(expected)],
                expected=expected, replacement=replacement))
        self.input_mutations.append(dict(
            id="input-" + name, kind="input", category="input", sites=sites,
            line=self.text[:expression_start].count("\n") + 1,
            mutation="row-input-literal", failure_stdout=token + "\n"))

    def branch_guard(self, name, expression, expected_true, input_plan=None, *, category="logical"):
        block_start = len(self.text)
        prefix = "  if ("
        expression_start = block_start + len(prefix)
        token = f"LIO:{self.variant}:{name}"
        if expected_true:
            self.add(prefix + expression + ") then\n    checks=checks+1\n  else\n"
                     + f"    write(*,'(a)') '{token}'\n    error stop\n  end if\n")
        else:
            self.add(prefix + expression + ") then\n"
                     + f"    write(*,'(a)') '{token}'\n    error stop\n  else\n    checks=checks+1\n  end if\n")
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expression, replacement=f".not. ({expression})",
            span=[expression_start, expression_start + len(expression)],
            line=self.text[:expression_start].count("\n") + 1, counter="checks", activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="logical-branch-expectation",
            block_span=[block_start, len(self.text)], expected_truth=expected_true)
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        if input_plan:
            self._input_mutation(name, expression_start, expression, input_plan, token)
        return guard

    def call_guard(self, name, expression, expected_true, input_plan=None):
        self.needs_logical_dummies = True
        block_start = len(self.text)
        callee = "require_true" if expected_true else "require_false"
        prefix = f"  call {callee}("
        expression_start = block_start + len(prefix)
        token = f"LIO:{self.variant}:{name}"
        self.add(prefix + expression + f", '{token}')\n")
        guard = dict(
            id=name, guard_id=name, kind="guard", category="logical-dummy", expression=expression,
            expected=expression, replacement=f".not. ({expression})",
            span=[expression_start, expression_start + len(expression)],
            line=self.text[:expression_start].count("\n") + 1, counter="checks", activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="logical-dummy-expectation",
            block_span=[block_start, len(self.text)], expected_truth=expected_true)
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        if input_plan:
            self._input_mutation(name, expression_start, expression, input_plan, token)
        return guard

    def equal_guard(self, name, expression, expected, replacement, *, category="completion", counter=None):
        block_start = len(self.text)
        expected = str(expected)
        replacement = str(replacement)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"LIO:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        return guard

    def finish(self):
        expected_total = CHECK_SENTINEL + len(self.observations)
        total = self.equal_guard("check-total", "checks", expected_total, expected_total + 1)
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
        if self.needs_logical_dummies:
            self.add(
                "contains\n"
                "  subroutine require_true(value, token)\n"
                "    logical, intent(in) :: value\n"
                "    character(len=*), intent(in) :: token\n"
                "    if (value) then\n"
                "      checks=checks+1\n"
                "    else\n"
                "      write(*,'(a)') token\n"
                "      error stop\n"
                "    end if\n"
                "  end subroutine require_true\n"
                "  subroutine require_false(value, token)\n"
                "    logical, intent(in) :: value\n"
                "    character(len=*), intent(in) :: token\n"
                "    if (value) then\n"
                "      write(*,'(a)') token\n"
                "      error stop\n"
                "    else\n"
                "      checks=checks+1\n"
                "    end if\n"
                "  end subroutine require_false\n")
        self.add(f"end program lio_{self.variant}\n")
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
        self.sentinel_mutations.append(dict(
            id="reverse-check-sentinel", kind="sentinel", category="sentinel", span=self.sentinel_span,
            expected=str(CHECK_SENTINEL), replacement=str(CHECK_SENTINEL + 1),
            line=self.text[:self.sentinel_span[0]].count("\n") + 1,
            mutation="reverse-sentinel-initialization", failure_stdout=total["failure_stdout"],
            guard_id=total["id"], guard_line=total["line"]))
        return omissions


def add_operator_mutations(p):
    operator = BINARY_VARIANT_OPERATORS.get(p.variant)
    if operator is None:
        return
    alternatives = [item for item in BINARY_TRUTH_TABLES if item != operator]
    spans = []
    start = 0
    while True:
        index = p.text.find(" " + operator + " ", start)
        if index < 0:
            break
        spans.append([index + 1, index + 1 + len(operator)])
        start = index + len(operator) + 2
    if len(spans) != 4:
        raise ValueError("expected four binary logical operator sites")
    raw = p.text.encode("ascii")
    for replacement in alternatives:
        for start, end in spans:
            if raw[start:end].decode("ascii") != operator:
                raise ValueError("operator mutation span lost its complete-parent binding")
        p.operator_mutations.append(dict(
            id="operator-" + operator.strip(".") + "-to-" + replacement.strip("."),
            kind="operator", category="operator", expected=operator, replacement=replacement,
            spans=spans, line=p.text[:spans[0][0]].count("\n") + 1,
            mutation="operator-under-test-substitution", failure_stdout="",
            discriminator=DISCRIMINATION_ROWS[operator][replacement]))


def not_program():
    p = Program("not_truth_table")
    p.start()
    p.branch_guard("not-true-is-false", ".not. .true.", False, [(0, ".true.", ".false.")])
    p.branch_guard("not-false-is-true", ".not. .false.", True, [(0, ".false.", ".true.")])
    omissions = p.finish()
    return p, omissions


def binary_program(variant):
    operator = BINARY_VARIANT_OPERATORS[variant]
    p = Program(variant)
    p.start()
    prefix = operator.strip(".")
    for row in ("TT", "TF", "FT", "FF"):
        expected_true = BINARY_TRUTH_TABLES[operator][row]
        p.branch_guard(prefix + "-" + row.lower(), row_expression(row, operator), expected_true,
                       row_input_sites(row, operator), category="truth-table")
    omissions = p.finish()
    add_operator_mutations(p)
    return p, omissions


def context_type_program():
    p = Program("context_type")
    p.start()
    p.branch_guard("if-context-or", ".false. .or. .true.", True, [(0, ".true.", ".false.")],
                   category="if-context")
    p.call_guard("logical-dummy-eqv", ".true. .eqv. .false.", False, [(0, ".false.", ".true.")])
    p.call_guard("logical-dummy-not", ".not. .false.", True, [(0, ".false.", ".true.")])
    omissions = p.finish()
    return p, omissions


def program(variant):
    if variant == "context_type":
        return context_type_program()
    if variant == "not_truth_table":
        return not_program()
    if variant in BINARY_VARIANT_OPERATORS:
        return binary_program(variant)
    raise ValueError("unknown variant")


def source_specs():
    specs = {}
    for variant in VARIANTS:
        p, omissions = program(variant)
        raw = p.text.encode("ascii")
        for probe in p.probes + omissions + p.sentinel_mutations:
            start, end = probe["span"]
            if raw[start:end].decode("ascii") != probe["expected"]:
                raise ValueError(f"mutation span {probe['id']} lost its complete-parent binding")
        for mutation in p.input_mutations:
            for site in mutation["sites"]:
                start, end = site["span"]
                if raw[start:end].decode("ascii") != site["expected"]:
                    raise ValueError(f"input mutation span {mutation['id']} lost its complete-parent binding")
        for mutation in p.operator_mutations:
            for start, end in mutation["spans"]:
                if raw[start:end].decode("ascii") != mutation["expected"]:
                    raise ValueError(f"operator mutation span {mutation['id']} lost its complete-parent binding")
        specs[identifier(variant)] = dict(
            id=identifier(variant), variant=variant, rule=p.rule, facets=p.facets, evidence="effect",
            standard="f2023", phase="run", source=p.text, source_sha256=sha(raw),
            completion=COMPLETIONS[variant], guards=p.guards, probes=p.probes, omissions=omissions,
            input_mutations=p.input_mutations, operator_mutations=p.operator_mutations,
            sentinel_mutations=p.sentinel_mutations, observations=p.observations,
            expected_counts=dict(checks=CHECK_SENTINEL + len(p.observations)))
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    if "sites" in mutation:
        mutated = raw
        for site in sorted(mutation["sites"], key=lambda item: item["span"][0], reverse=True):
            start, end = site["span"]
            if raw[start:end].decode("ascii") != site["expected"]:
                raise ValueError("the input mutation span does not bind the complete parent")
            mutated = mutated[:start] + site["replacement"].encode("ascii") + mutated[end:]
        return mutated
    if "spans" in mutation:
        mutated = raw
        for start, end in sorted(mutation["spans"], reverse=True):
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError("the operator-substitution span does not bind the complete parent")
            mutated = mutated[:start] + mutation["replacement"].encode("ascii") + mutated[end:]
        return mutated
    return wrong_oracle_source(spec, mutation)


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = root / "tests/fixtures" / ("logical_intrinsic_interpretation_" + spec["variant"])
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
    old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
           "processor, approves no fixture or oracle, and claims no coverage.")
    new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
           "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
           "selected runtime fixtures and mutation plans without granting those approvals or claims.")
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("logical intrinsic interpretation facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        limitation = owner.get("oracle_limitation", "")
        if old in limitation:
            limitation = limitation.replace(old, new)
        owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIXES[rule], LIMITATIONS[rule])
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
        "Catalogue: `doc/catalogues/logical_intrinsic_operation_interpretation_10_1_5_4_1.json`. "
        "The original source-only registration supplied pending plans; the bounded runtime fixtures below "
        "supply selected cases and mutation plans, not oracle approval, fixture approval, source-review renewal, "
        "or universal coverage.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Logical intrinsic interpretation runtime observations\n\n"
        "Six complete run/effect/f2023 programs cover 21 pending facets: the p1 logical-computation and "
        "result-type witnesses, both .NOT. rows, and the full TT/TF/FT/FF truth tables for .AND., .OR., "
        ".EQV. and .NEQV. The p1 result-type source passes the operation expressions directly to LOGICAL "
        "dummy arguments; no declared result variable launders the expression type. All truth-table guards use "
        "literal operands in direct expressions and hand-derived branch oracles.\n\n"
        "The binary-operator programs intentionally assert every row. The generated discrimination table names "
        "a separating row for each operator and each alternative, including the load-bearing FF separation of "
        ".AND. from .EQV. and the load-bearing TT separation of .OR. from .NEQV. The permanent mutation "
        "campaign includes wrong-oracle mutations for every guard and completion literal, row-input mutations, "
        "whole-observation omissions, a nonzero reverse check-sentinel mutation, and all 12 binary operator "
        "substitutions.\n\n"
        "Only operand-type-delegation remains pending because p1 delegates permitted operand types to 10.1.5.1. "
        "The fixtures make no short-circuit, side-effect, reassociation, array, nondefault-kind, defined-operator, "
        "diagnostic or evaluation-order claim. No evidence link, baseline update, SourceUse renewal, catalogue "
        "source-review renewal or approval is created.\n"
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
            raise ValueError("stale logical-intrinsic-interpretation fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} logical-intrinsic-interpretation cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle, "
          f"{sum(len(row['input_mutations']) for row in specs.values())} input, "
          f"{sum(len(row['operator_mutations']) for row in specs.values())} operator, "
          f"{sum(len(row['sentinel_mutations']) for row in specs.values())} reverse-sentinel and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
