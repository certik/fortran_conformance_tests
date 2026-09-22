#!/usr/bin/env python3
"""Array element order runtime fixtures for Fortran 2023 subclause 9.5.3.3."""

import argparse
import copy
import json
from itertools import product
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import (
    owned_paragraph,
    probe_verdict as ordinary_probe_verdict,
    sha,
    wrong_oracle_source,
)


ROOT = Path(__file__).resolve().parents[1]
SECTION = "9.5.3.3"
CATALOGUE = "doc/catalogues/array_element_order_9_5_3_3.json"
VIEW = "doc/fortran_2023_9_5_3_3.md"
SUMMARY_BEGIN = "<!-- BEGIN ARRAY ELEMENT ORDER FIXTURES -->"
SUMMARY_END = "<!-- END ARRAY ELEMENT ORDER FIXTURES -->"
VARIANTS = {
    "sequence_rank_two": ("S9.5.3.3-001", "array-elements-form-sequence"),
    "position_rank_two": ("S9.5.3.3-001", "position-determined-by-subscript-order-value"),
    "rank_one": ("S9.5.3.3-002", "rank-one-order-value"),
    "rank_two": ("S9.5.3.3-002", "rank-two-order-value"),
    "rank_three": ("S9.5.3.3-002", "rank-three-order-value"),
    "rank_fifteen": ("S9.5.3.3-002", "rank-fifteen-pattern"),
}
FACETS_BY_RULE = {
    "S9.5.3.3-001": ("array-elements-form-sequence", "position-determined-by-subscript-order-value"),
    "S9.5.3.3-002": ("rank-one-order-value", "rank-two-order-value",
                       "rank-three-order-value", "rank-fifteen-pattern"),
}
REMAINING_PENDING = {
    "S9.5.3.3-001": {"table9-1-is-formula-source"},
    "S9.5.3.3-002": {"table-layout-ambiguity-recorded"},
}
COMPLETIONS = {
    variant: "ARRAY ELEMENT ORDER " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
ORACLE_PREFIX_001 = "S9.5.3.3-001 array element order runtime fixtures: "
ORACLE_PREFIX_002 = "S9.5.3.3-002 subscript order formula runtime fixtures: "
LIMIT_PREFIX_001 = "S9.5.3.3-001 array element order fixture boundaries: "
LIMIT_PREFIX_002 = "S9.5.3.3-002 subscript order formula fixture boundaries: "
ORACLE_001 = ORACLE_PREFIX_001 + (
    "two complete run/effect/f2023 programs use DATA statement initialization as the observable "
    "consumer of array element order, then read named elements by ordinary scalar subscripts. The "
    "sequence program declares INTEGER a(2:4,-1:2), giving d1=3 and d2=4, and supplies all twelve "
    "coordinate-coded literals in the hand-computed Table 9.1 order: (2,-1),(3,-1),(4,-1), "
    "(2,0), ... ,(4,2). It checks every element against its independent literal, so a row-major, "
    "transposed, endpoint-only or set-only implementation fails. The position program declares "
    "INTEGER a(5:7,20:23) and checks two interior coordinates whose hand positions are 5 and 7 "
    "from 1+(s1-j1)+(s2-j2)*d1, proving that position is determined by the formula rather than by "
    "source spelling or storage address. All lower bounds are nonunit, rank-two extents are distinct, "
    "and every value is coordinate-coded. Each assertion increments a counter and a final total guard "
    "precedes exact completion stdout, empty stderr and exit0. Wrong-oracle mutations cover every "
    "assertion and completion literal; omissions remove individual or grouped observations and the "
    "completion line."
)
ORACLE_002 = ORACLE_PREFIX_002 + (
    "four complete run/effect/f2023 programs cover the rank 1, rank 2, rank 3 and rank-15 Table 9.1 "
    "formula rows. The rank-one case uses a(3:7) and checks s1=5 at position 1+(5-3)=3. The rank-two "
    "case uses a(-2:1,4:6), so d1=4, and checks the interior element (0,5) at position "
    "1+(0-(-2))+(5-4)*4=7. The rank-three case uses a(-2:0,4:5,7:10), so d1=3 and d2=2, and checks "
    "(-1,5,9) at position 1+1+1*3+2*2*3=17. The rank-15 case uses nonunit lower bounds in all "
    "dimensions, extents 2,2,2,1,...,1,2, and checks the high-dimension coordinate "
    "(4,-1,6,8,9,10,11,12,13,14,15,16,17,18,-4) at position 16 by the displayed product chain. "
    "The numeric and character literals are hand-enumerated in formula order and compare directly "
    "against literal constants; no RESHAPE, PACK, TRANSFER, storage association, sequence association "
    "or compiler consensus oracle is used."
)
LIMITATION_001 = LIMIT_PREFIX_001 + (
    "only array-elements-form-sequence and position-determined-by-subscript-order-value are represented. "
    "The table9-1-is-formula-source facet remains pending because it is a source/PDF attribution claim, "
    "not a separate runtime effect; forcing it into a program would be circular. DATA statement list "
    "association is used only as the standard-defined context that observes array element order, while "
    "the expected values are independent coordinate-coded literals and comments with hand arithmetic. "
    "These cases do not claim bounds checking, diagnostics, storage layout, contiguity, pointer/argument "
    "association, coarray or multi-image behavior. Generation grants no review approval, evidence link, "
    "baseline update, SourceUse renewal or universal compiler-conformance credit."
)
LIMITATION_002 = LIMIT_PREFIX_002 + (
    "only rank-one-order-value, rank-two-order-value, rank-three-order-value and rank-fifteen-pattern "
    "are represented. The table-layout-ambiguity-recorded facet remains pending because its oracle is "
    "row-by-row visual inspection of Table 9.1 in the pinned PDF, including the ambiguous extracted "
    "rank-15 multiplication sign, and cannot be established by executing Fortran. The fixtures do not "
    "derive expected values with SIZE, LBOUND, UBOUND, SHAPE, RESHAPE, PACK, TRANSFER, sequence "
    "association, address arithmetic or storage layout. Compiler agreement is corroboration only, not "
    "the oracle. Unsupported processors must fail honestly; no workaround weakens the Fortran source."
)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown array element order variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__array_element_order_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.text = ""
        self.guards = []
        self.probes = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def guard(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"AEO:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter}=checks+1\n")
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


def coord2(i, j):
    return 1000 * i + (j + 50)


def coord3(i, j, k):
    return 10000 * (i + 10) + 100 * j + k


def char15(coords):
    return ",".join(str(item) for item in coords)


def ordered_points(bounds):
    ranges = [range(lo, hi + 1) for lo, hi in bounds]
    result = []
    for reversed_coords in product(*reversed(ranges)):
        result.append(tuple(reversed(reversed_coords)))
    return result


def data_statement(name, values, *, strings=False):
    rendered = [("'" + value + "'") if strings else str(value) for value in values]
    lines = [f"  data {name} / &\n"]
    for index, value in enumerate(rendered):
        suffix = " /" if index == len(rendered) - 1 else ", &"
        lines.append("    " + value + suffix + "\n")
    return "".join(lines)


def begin_program(p, rule, facet):
    p.add(f"! rule: {rule}\n! covers: {facet}\n")
    p.add("! Oracle constants are hand-computed from Fortran 2023 Table 9.1.\n")
    p.add("! The DATA list is already in that formula order; no storage-layout oracle is used.\n")


def finish_program(p, observations):
    total = p.guard("check-total", "checks", len(observations), len(observations) + 1,
                    category="completion", counter=None)
    completion = p.completion()
    p.add(f"end program array_element_order_{p.variant}_effect\n")
    omissions = []
    start, end = completion["block_span"]
    omissions.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    plans = [("omit-observation-" + guard["id"], guard["block_span"], total) for guard in observations]
    if len(observations) > 1:
        plans.append(("omit-all-observations", [observations[0]["block_span"][0], observations[-1]["block_span"][1]], total))
    for name, span, failure in plans:
        start, end = span
        omissions.append(dict(
            id=name, guard_id=failure["id"], kind="guard", category="omission", span=span,
            expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=failure["line"], mutation="whole-program-omission",
            failure_token=failure["failure_token"], failure_stdout=failure["failure_stdout"]))
    return omissions


def rank_two_declaration(bounds):
    (i0, i1), (j0, j1) = bounds
    return f"  integer :: a({i0}:{i1},{j0}:{j1})\n"


def program(variant):
    rule, facet = VARIANTS[variant]
    p = Program(variant)
    begin_program(p, rule, facet)
    p.add(f"program array_element_order_{variant}_effect\n  implicit none\n  integer :: checks\n")
    observations = []
    notes = []

    if variant == "rank_one":
        p.add("  integer :: a(3:7)\n")
        values = list(range(103, 108))
        p.add(data_statement("a", values))
        p.add("  checks=0\n")
        p.add("  ! rank 1: j1=3, s1=5 gives position 1+(5-3)=3; DATA value 105.\n")
        observations.append(p.guard("s1-five-position-three", "a(5)", 105, 104))
        p.add("  ! endpoint controls keep the nonunit lower-bound mapping visible.\n")
        observations.append(p.guard("lower-bound-control", "a(3)", 103, 105))
        observations.append(p.guard("upper-bound-control", "a(7)", 107, 106))
        notes = ["bounds 3:7", "s1=5 -> 1+(5-3)=3"]
    elif variant in {"sequence_rank_two", "position_rank_two", "rank_two"}:
        if variant == "sequence_rank_two":
            bounds = ((2, 4), (-1, 2))
            targets = ordered_points(bounds)
            heading = (
                "  ! rank 2 sequence: j1=2,j2=-1,d1=3; order is (2,-1),(3,-1),(4,-1), "
                "then s2 advances.\n")
        elif variant == "position_rank_two":
            bounds = ((5, 7), (20, 23))
            targets = [(6, 21), (5, 22), (7, 22)]
            heading = "  ! rank 2 positions: j1=5,j2=20,d1=3; selected positions are interior.\n"
        else:
            bounds = ((-2, 1), (4, 6))
            targets = [(0, 5), (-1, 5), (1, 6)]
            heading = "  ! rank 2 formula: j1=-2,j2=4,d1=4; extents 4 and 3 are distinct.\n"
        p.add(rank_two_declaration(bounds))
        values = [coord2(i, j) for i, j in ordered_points(bounds)]
        p.add(data_statement("a", values))
        p.add("  checks=0\n")
        p.add(heading)
        if variant == "sequence_rank_two":
            for position, (i, j) in enumerate(targets, 1):
                p.add(f"  ! ({i},{j}) position {position}: 1+({i}-{bounds[0][0]})+({j}-({bounds[1][0]}))*3 = {position}.\n")
                observations.append(p.guard(f"coordinate-{i}-{j}", f"a({i},{j})", coord2(i, j), coord2(i, j) + 1))
        else:
            d1 = bounds[0][1] - bounds[0][0] + 1
            for i, j in targets:
                position = 1 + (i - bounds[0][0]) + (j - bounds[1][0]) * d1
                p.add(f"  ! ({i},{j}) position {position}: 1+({i}-({bounds[0][0]}))+({j}-{bounds[1][0]})*{d1} = {position}.\n")
                observations.append(p.guard(f"coordinate-{i}-{j}", f"a({i},{j})", coord2(i, j), coord2(i, j) + 1))
        notes = [f"bounds {bounds}", "rank-two DATA list follows Table 9.1"]
    elif variant == "rank_three":
        bounds = ((-2, 0), (4, 5), (7, 10))
        p.add("  integer :: a(-2:0,4:5,7:10)\n")
        values = [coord3(*point) for point in ordered_points(bounds)]
        p.add(data_statement("a", values))
        p.add("  checks=0\n")
        p.add("  ! rank 3: j=(-2,4,7), d1=3, d2=2; s3 advances by d2*d1=6.\n")
        targets = [(-1, 5, 9), (-2, 4, 8), (0, 5, 10)]
        for i, j, k in targets:
            position = 1 + (i + 2) + (j - 4) * 3 + (k - 7) * 2 * 3
            p.add(f"  ! ({i},{j},{k}) position {position}: 1+({i}-(-2))+({j}-4)*3+({k}-7)*2*3 = {position}.\n")
            observations.append(p.guard(f"coordinate-{i}-{j}-{k}", f"a({i},{j},{k})", coord3(i, j, k), coord3(i, j, k) + 1))
        notes = ["bounds (-2:0,4:5,7:10)", "(-1,5,9) -> position 17"]
    elif variant == "rank_fifteen":
        bounds = [(3, 4), (-2, -1), (5, 6)] + [(n, n) for n in range(8, 19)] + [(-5, -4)]
        points = ordered_points(bounds)
        values = [char15(point) for point in points]
        char_len = max(len(value) for value in values)
        p.add(f"  character(len={char_len}) :: a(3:4,-2:-1,5:6, &\n")
        p.add("       8:8,9:9,10:10,11:11,12:12,13:13,14:14, &\n")
        p.add("       15:15,16:16,17:17,18:18,-5:-4)\n")
        p.add(data_statement("a", values, strings=True))
        p.add("  checks=0\n")
        p.add("  ! rank 15: d1=d2=d3=d15=2 and d4..d14=1; all lower bounds are nonunit.\n")
        targets = [points[-1], (4, -1, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, -5), points[0]]
        for point in targets:
            stride = 1
            position = 1
            nonzero_terms = []
            for axis, ((lo, hi), s) in enumerate(zip(bounds, point), 1):
                delta = s - lo
                position += delta * stride
                if delta:
                    if axis == 1:
                        nonzero_terms.append(f"({s}-({lo}))")
                    else:
                        nonzero_terms.append(f"({s}-({lo}))*{stride}")
                stride *= hi - lo + 1
            p.add("  ! (" + char15(point) + f") has Table 9.1 position {position}.\n")
            arithmetic = "1" + ("+" + "+".join(nonzero_terms) if nonzero_terms else "")
            p.add(f"  ! Arithmetic: {arithmetic} = {position}; dimensions 4:14 have zero deltas.\n")
            expected = "'" + char15(point) + "'"
            replacement = "'" + char15(points[0] if point != points[0] else points[-1]) + "'"
            sub = [str(item) for item in point]
            subscript = ",".join(sub[:10]) + ", &\n       " + ",".join(sub[10:])
            observations.append(p.guard("coordinate-" + str(position), f"a({subscript})", expected, replacement))
        notes = ["rank-15 extents 2,2,2,1,...,1,2", "high dimension target -> position 16"]
    else:
        raise ValueError("unknown variant")

    omissions = finish_program(p, observations)
    raw = p.text.encode("ascii")
    for probe in p.probes + omissions:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError("an array-element-order mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, rule=rule, facets=[facet], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[variant],
        guards=p.guards, probes=p.probes, omissions=omissions, observations=observations, notes=notes,
        expected_counts=dict(checks=len(observations)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("array_element_order_" + spec["variant"])
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
        raise ValueError("array element order requirement IDs changed")
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("selected array element order facets changed")
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
    old_oracle = ("Every facet is a pending source plan. Positive-control plans use independently chosen "
                  "literal values, SHAPE, SIZE, LBOUND, UBOUND, or scalar results that first establish "
                  "definedness and reached execution. Diagnostic-policy plans pair an otherwise legal source "
                  "with a minimal repair and require any future report to be attributable to the stated "
                  "requirement rather than an unrelated grammar, declaration, unsupported-feature, resource, "
                  "or runtime failure. Negative plans identify the violated owner and avoid programs already "
                  "invalid for a different rule.")
    new_oracle = ("The original source-only catalogue recorded pending plans. The selected runtime fixtures "
                  "below now supply executable standard-oracle observations for the covered effect facets; "
                  "facets still listed in pending remain unimplemented.")
    old_limitation_sentence = ("This source-only catalogue creates no Fortran test program, compiler invocation, "
                               "execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.")
    new_limitation_sentence = ("The original source-only catalogue created no Fortran test program, compiler "
                               "invocation, execution evidence, evidence link, fixture approval, oracle approval, "
                               "or coverage claim; this generator supplies selected runtime fixtures and mutation "
                               "plans without granting those approvals or claims.")
    for owner in (by_rule["S9.5.3.3-001"], by_rule["S9.5.3.3-002"]):
        if owner.get("oracle") == old_oracle:
            owner["oracle"] = new_oracle
        elif owner.get("oracle", "").startswith(old_oracle + "\n\n"):
            owner["oracle"] = new_oracle + owner["oracle"][len(old_oracle):]
        if old_limitation_sentence in owner.get("oracle_limitation", ""):
            owner["oracle_limitation"] = owner["oracle_limitation"].replace(
                old_limitation_sentence, new_limitation_sentence)
    by_rule["S9.5.3.3-001"]["oracle"] = owned_paragraph(
        by_rule["S9.5.3.3-001"].get("oracle", ""), ORACLE_PREFIX_001, ORACLE_001)
    by_rule["S9.5.3.3-001"]["oracle_limitation"] = owned_paragraph(
        by_rule["S9.5.3.3-001"].get("oracle_limitation", ""), LIMIT_PREFIX_001, LIMITATION_001)
    by_rule["S9.5.3.3-002"]["oracle"] = owned_paragraph(
        by_rule["S9.5.3.3-002"].get("oracle", ""), ORACLE_PREFIX_002, ORACLE_002)
    by_rule["S9.5.3.3-002"]["oracle_limitation"] = owned_paragraph(
        by_rule["S9.5.3.3-002"].get("oracle_limitation", ""), LIMIT_PREFIX_002, LIMITATION_002)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the array element order generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "The canonical catalogue is `doc/catalogues/array_element_order_9_5_3_3.json`. Effective review state comes from `Registry.catalogue_review_state`; this source-only packet does not approve cases, canonical relationships or an execution inventory.",
        "Catalogue: `doc/catalogues/array_element_order_9_5_3_3.json`. Fixture additions below do not approve cases, canonical relationships or an execution inventory.")
    before = before.replace(
        "All facets in this packet are pending source plans. No Fortran test program, compiler invocation, execution evidence, oracle approval, fixture approval or coverage claim is supplied here.",
        "Six bounded runtime fixtures now establish the non-source-only facets; two source/PDF review facets remain pending. No oracle approval, fixture approval or coverage claim is supplied here.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Array element order runtime observations\n\n"
        "Six complete run/effect/f2023 programs observe Table 9.1 order through DATA statement "
        "initialization and direct scalar subscript reads. All arrays use nonunit lower bounds. "
        "Rank-two cases use distinct extents and coordinate-coded integer literals; the sequence "
        "case checks every element in a 3 by 4 array, not just the set of values. Rank-one, "
        "rank-two and rank-three formula cases check hand-computed interior positions. The rank-15 "
        "case has extents 2,2,2,1,...,1,2 and checks a high-dimension product-chain position with "
        "coordinate-coded character literals.\n\n"
        "Every source has one `! rule:` and one `! covers:` header. Expected values are literal "
        "constants with comments showing the arithmetic. No RESHAPE, PACK, TRANSFER, storage "
        "association, sequence association, address arithmetic or compiler consensus oracle is used. "
        "Wrong-oracle and omission plans bind complete-parent byte spans.\n\n"
        "`table9-1-is-formula-source` and `table-layout-ambiguity-recorded` remain pending because "
        "they are source/PDF review claims rather than separate runtime effects.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the array element order summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return (before + begin + "\n\n"
            + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after)


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
            raise ValueError("stale array-element-order fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} array-element-order cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
