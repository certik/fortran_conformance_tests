#!/usr/bin/env python3
"""Substring runtime effect fixtures for Fortran 2023 subclause 9.4.1."""

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
RULE = "S9.4.1-001"
SECTION = "9.4.1"
CATALOGUE = "doc/catalogues/substring_9_4_1.json"
VIEW = "doc/fortran_2023_9_4_1.md"
VARIANTS = {
    "contiguous_portion": "contiguous-portion",
    "first_expression_start": "first-expression-start",
    "second_expression_end": "second-expression-end",
    "inclusive_character_selection": "inclusive-character-selection",
    "default_start_one": "default-start-one",
    "default_end_parent_length": "default-end-parent-length",
    "length_formula": "length-formula",
    "zero_length_when_start_exceeds_end": "zero-length-when-start-exceeds-end",
}
FACETS = tuple(VARIANTS.values())
COMPLETIONS = {
    variant: "SUBSTRING " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
ORACLE_PREFIX = "S9.4.1-001 substring runtime effects: "
LIMIT_PREFIX = "S9.4.1-001 substring runtime boundaries: "
SUMMARY_BEGIN = "<!-- BEGIN SUBSTRING EFFECTS -->"
SUMMARY_END = "<!-- END SUBSTRING EFFECTS -->"
ORACLE = ORACLE_PREFIX + (
    "eight complete run/effect/f2023 programs observe the p1-p3 substring effects with "
    "defined CHARACTER parents and actual substring references. Distinctive parents such as "
    "'abcdef' make off-by-one endpoints visible. Value oracles compare whole substring values "
    "directly with independent character literals of the same nonzero length; no INDEX, SCAN, "
    "TRIM, ADJUSTL or derived character oracle is used. The contiguous case checks c(2:5) "
    "against 'bcde', mutates c(3:4), and checks the changed middle against 'bXYe'. The start "
    "and end expression cases use integer variables assigned by executed statements and then "
    "changed for a second branch. Inclusive selection checks c(2:2)=='b' and LEN 1. The default "
    "cases compare the defaulted form with both an independent literal and the explicit endpoint "
    "form. The length case checks LEN values 3, 1 and 0, with companion literal value checks. "
    "The zero-length case checks LEN(c(4:3))==0, the zero-length value, unchanged parent text and "
    "a neighboring nonzero substring. Each assertion increments a counter and a final total guard "
    "precedes exact completion stdout, empty stderr and exit0. Wrong-oracle mutations cover every "
    "assertion and completion literal; omissions remove observations, grouped observations, "
    "selected safe defining mutations and the completion line."
)
LIMITATION = LIMIT_PREFIX + (
    "only the eight S9.4.1-001 effect facets are represented. R908, R909, R910, C908 and "
    "S9.4.1-002 remain pending. The programs do not use source rewrites, character intrinsics "
    "as value oracles, undefined reads, coarrays, multi-image execution, extra I/O, STOP codes, "
    "bounds-violating nonzero substrings, blank-padded unequal-length positive oracles, or "
    "diagnostic claims. LEN is used only where the planned observation is explicitly about "
    "length. The zero-length literal comparison is paired with the LEN guard that carries the "
    "facet. Guard markers are program output, not mandated ERROR STOP wording or universal "
    "numeric status. Generation grants no review approval, evidence link, baseline update, "
    "SourceUse renewal or universal compiler-conformance credit."
)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown substring variant")
    return "S9_4_1_001_valid__substring_effect_" + variant


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
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"SSE:{self.variant}:{name}"
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


def spec_rows(variant):
    if variant == "contiguous_portion":
        declarations = "  character(len=6) :: c\n  integer :: checks\n"
        definitions = ["  c='abcdef'\n"]
        observations = [
            ("contiguous-value", "c(2:5)", "'bcde'", "'bcdf'", "value"),
            ("contiguous-mutated-middle", "c(2:5)", "'bXYe'", "'bXZe'", "value"),
        ]
        interleaves = {1: ["  c(3:4)='XY'\n"]}
        omission_targets = [("omit-middle-mutation", (1, 0), "contiguous-mutated-middle")]
    elif variant == "first_expression_start":
        declarations = "  character(len=6) :: c\n  integer :: f, seed, checks\n"
        definitions = ["  c='abcdef'\n", "  seed=1\n", "  f=seed+2\n"]
        observations = [
            ("start-three", "c(f:5)", "'cde'", "'bcd'", "value"),
            ("start-two", "c(f:5)", "'bcde'", "'cdef'", "value"),
        ]
        interleaves = {1: ["  f=f-1\n"]}
        omission_targets = []
    elif variant == "second_expression_end":
        declarations = "  character(len=6) :: c\n  integer :: l, seed, checks\n"
        definitions = ["  c='abcdef'\n", "  seed=2\n", "  l=seed+2\n"]
        observations = [
            ("end-four", "c(2:l)", "'bcd'", "'bcde'", "value"),
            ("end-five", "c(2:l)", "'bcde'", "'bcd'", "value"),
        ]
        interleaves = {1: ["  l=l+1\n"]}
        omission_targets = []
    elif variant == "inclusive_character_selection":
        declarations = "  character(len=3) :: c\n  integer :: checks\n"
        definitions = ["  c='abc'\n"]
        observations = [
            ("single-endpoint-value", "c(2:2)", "'b'", "'a'", "value"),
            ("single-endpoint-length", "len(c(2:2))", "1", "2", "length"),
        ]
        interleaves = {}
        omission_targets = []
    elif variant == "default_start_one":
        declarations = "  character(len=6) :: c\n  integer :: checks\n"
        definitions = ["  c='abcdef'\n"]
        observations = [
            ("default-start-value", "c(:3)", "'abc'", "'bcd'", "value"),
            ("default-start-explicit", "c(:3)", "c(1:3)", "c(2:4)", "default"),
        ]
        interleaves = {}
        omission_targets = []
    elif variant == "default_end_parent_length":
        declarations = "  character(len=6) :: c\n  integer :: checks\n"
        definitions = ["  c='abcdef'\n"]
        observations = [
            ("default-end-value", "c(4:)", "'def'", "'cde'", "value"),
            ("default-end-length", "len(c(4:))", "3", "2", "length"),
            ("default-end-explicit", "c(4:)", "c(4:6)", "c(3:5)", "default"),
            ("default-end-mutated-last", "c(4:)", "'deZ'", "'def'", "value"),
        ]
        interleaves = {3: ["  c(6:6)='Z'\n"]}
        omission_targets = [("omit-last-character-mutation", (3, 0), "default-end-mutated-last")]
    elif variant == "length_formula":
        declarations = "  character(len=6) :: c\n  integer :: checks\n"
        definitions = ["  c='abcdef'\n"]
        observations = [
            ("length-three", "len(c(2:4))", "3", "4", "length"),
            ("length-three-value", "c(2:4)", "'bcd'", "'abc'", "value"),
            ("length-one", "len(c(4:4))", "1", "2", "length"),
            ("length-one-value", "c(4:4)", "'d'", "'c'", "value"),
            ("length-zero", "len(c(4:3))", "0", "1", "length"),
            ("length-zero-value", "c(4:3)", "''", "'x'", "value"),
        ]
        interleaves = {}
        omission_targets = []
    elif variant == "zero_length_when_start_exceeds_end":
        declarations = "  character(len=6) :: c\n  integer :: checks\n"
        definitions = ["  c='abcdef'\n"]
        observations = [
            ("zero-length", "len(c(4:3))", "0", "1", "length"),
            ("zero-length-value", "c(4:3)", "''", "'x'", "value"),
            ("parent-unchanged", "c", "'abcdef'", "'abcxef'", "boundary"),
            ("neighbor-nonzero", "c(3:4)", "'cd'", "'dc'", "control"),
        ]
        interleaves = {}
        omission_targets = []
    else:
        raise ValueError("unknown substring variant")
    return declarations, definitions, observations, interleaves, omission_targets


def program(variant):
    declarations, definitions, observations, interleaves, omission_targets = spec_rows(variant)
    p = Program(variant)
    p.add(f"program substring_{variant}_effect\n  implicit none\n" + declarations + "  checks=0\n")
    definition_spans = [(text, p.add(text)) for text in definitions]
    interleave_spans = {}
    observed = []
    for index, (name, expression, expected, replacement, category) in enumerate(observations):
        for offset, text in enumerate(interleaves.get(index, [])):
            interleave_spans[(index, offset)] = p.add(text)
        observed.append(p.guard(name, expression, expected, replacement, category=category))
    for index in range(len(observations), len(observations) + 1):
        for offset, text in enumerate(interleaves.get(index, [])):
            interleave_spans[(index, offset)] = p.add(text)
    total = p.guard("check-total", "checks", str(len(observed)), str(len(observed) + 1),
                    counter=None, category="completion")
    completion = p.completion()
    p.add(f"end program substring_{variant}_effect\n")

    omissions = []
    start, end = completion["block_span"]
    omissions.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    plans = [("omit-observation-" + guard["id"], guard["block_span"], total) for guard in observed]
    if len(observed) > 1:
        plans.append(("omit-all-observations", [observed[0]["block_span"][0], observed[-1]["block_span"][1]], total))
    by_id = {guard["id"]: guard for guard in observed + [total]}
    for name, key, guard_id in omission_targets:
        plans.append((name, interleave_spans[key], by_id[guard_id]))
    for name, span, failure in plans:
        start, end = span
        omissions.append(dict(
            id=name, guard_id=failure["id"], kind="guard", category="omission", span=span,
            expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=failure["line"], mutation="whole-program-omission",
            failure_token=failure["failure_token"], failure_stdout=failure["failure_stdout"]))
    for probe in p.probes + omissions:
        start, end = probe["span"]
        if p.text[start:end] != probe["expected"]:
            raise ValueError("a substring oracle mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, facets=[VARIANTS[variant]], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(p.text.encode("ascii")),
        completion=COMPLETIONS[variant], guards=p.guards, probes=p.probes, omissions=omissions,
        observations=observed, definitions=[dict(text=text, span=span) for text, span in definition_spans],
        interleaves=[dict(text=p.text[span[0]:span[1]], span=span) for span in interleave_spans.values()],
        expected_counts=dict(checks=len(observed)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("substring_effect_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=spec["facets"], evidence="effect", standard="f2023",
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
    matches = [row for row in updated["requirements"] if row["id"] == RULE]
    if len(matches) != 1 or not set(FACETS) <= set(matches[0]["facets"]):
        raise ValueError("the selected substring effect definitions changed")
    owner = matches[0]
    if owner["category"] != "effect" or set(FACETS) & set(owner.get("positive_control_facets", [])):
        raise ValueError("the selected substring facets must remain runtime effects")
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    if set(owner.get("pending", {})):
        raise ValueError("all S9.4.1-001 pending facets should be implemented by this packet")
    owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    limitation = owner.get("oracle_limitation", "")
    old = ("This is a source-only catalogue packet. It creates no Fortran test program, execution, "
           "evidence link, fixture approval, oracle approval, or coverage claim.")
    new = ("The original source-only registration created no Fortran test program, execution, evidence "
           "link, fixture approval, oracle approval, or coverage claim; this generator supplies the eight "
           "selected runtime fixtures and mutation plans without granting those approvals or claims.")
    if old in limitation:
        limitation = limitation.replace(old, new)
    owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the substring generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Eight base units: p1, R908, R909, R910, C908, p2, p3 and the unnumbered note. "
        "This source-only packet records substring syntax, character parent strings, endpoint defaults, "
        "length and range plans without approving any fixture.\n\n"
        "All facets in this packet are pending source plans. No Fortran test program,\n"
        "compiler invocation, execution evidence, oracle approval, fixture approval or\n"
        "coverage claim is supplied here.",
        "Eight base units: p1, R908, R909, R910, C908, p2, p3 and the unnumbered note. "
        "The original source-only packet recorded substring syntax, character parent strings, "
        "endpoint defaults, length and range plans; the bounded runtime fixtures below now "
        "implement S9.4.1-001 effect cases and mutation plans without approving unrelated fixtures.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Substring runtime observations\n\n"
        "Eight complete run/effect/f2023 programs cover the S9.4.1-001 facets.\n"
        "They use distinctive CHARACTER parents, actual substring references and direct\n"
        "whole-value comparisons against independent literals. The start and end\n"
        "expression cases use integer variables assigned by executed statements. The\n"
        "default cases compare omitted endpoints with explicit endpoint forms as well\n"
        "as with independent literals. LEN appears only for planned length\n"
        "observations, including the zero-length cases.\n\n"
        "Every assertion prints a unique `SSE:` failure token and stops on mismatch,\n"
        "increments a check counter, and is followed by a final check-total guard\n"
        "before exact completion stdout, empty stderr and exit0. Wrong-oracle plans\n"
        "cover every guard and completion literal. Omission plans delete observation\n"
        "blocks, grouped observations, selected safe defining mutations and the\n"
        "completion line. Mutations are complete-parent byte spans.\n\n"
        "Only S9.4.1-001 pending entries are removed. R908, R909, R910, C908 and\n"
        "S9.4.1-002 remain pending. No evidence link, baseline update, SourceUse\n"
        "renewal or approval is created.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the substring effect summary boundaries changed")
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
        status="sensitive" if qualified else "not-sensitive",
        qualified=qualified, parent_passed=verdict["parent_passed"], intended_failure=bool(intended),
        parent_preempted=False,
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
            raise ValueError("stale substring effect family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} substring cases, "
          f"{len(FACETS)} facets, {sum(len(row['probes']) for row in specs.values())} wrong-oracle "
          f"and {sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
