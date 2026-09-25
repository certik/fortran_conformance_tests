#!/usr/bin/env python3
"""ASSOCIATE construct runtime effect fixtures for Fortran 2023 11.1.3.2-11.1.3.3."""

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
SECTIONS = ("11.1.3.2", "11.1.3.3")
CATALOGUES = {
    "11.1.3.2": "doc/catalogues/execution_of_the_associate_construct_11_1_3_2.json",
    "11.1.3.3": "doc/catalogues/other_attributes_of_associate_names_11_1_3_3.json",
}
VIEWS = {
    "11.1.3.2": "doc/fortran_2023_11_1_3_2.md",
    "11.1.3.3": "doc/fortran_2023_11_1_3_3.md",
}
SUMMARY_BEGIN = "<!-- BEGIN ASSOCIATE CONSTRUCT FIXTURES -->"
SUMMARY_END = "<!-- END ASSOCIATE CONSTRUCT FIXTURES -->"
VARIANTS = {
    "expression_selector_value": ("S11.1.3.2-001", "expression-selector-value-before-block"),
    "subscript_expression_capture": ("S11.1.3.2-001", "variable-designator-subexpressions-before-block"),
    "expression_associate_read": ("S11.1.3.2-002", "associate-name-reads-expression-value"),
    "variable_selector_define": ("S11.1.3.2-002", "associate-name-defines-variable-selector"),
    "outer_homonym_scope": ("S11.1.3.2-002", "associate-name-not-outside-block-source"),
    "character_length_parameter": ("S11.1.3.2-003", "character-length-type-parameter"),
    "rank_shape": ("S11.1.3.3-001", "same-rank-as-selector"),
    "lower_bound_lbound": ("S11.1.3.3-001", "nondefault-lower-bound"),
    "upper_bound_extent": ("S11.1.3.3-001", "upper-bound-from-extent"),
    "definable_selector_assignment": ("S11.1.3.3-005", "definable-selector-assignment-control"),
}
FACETS_BY_RULE = {
    "S11.1.3.2-001": [
        "expression-selector-value-before-block",
        "variable-designator-subexpressions-before-block",
    ],
    "S11.1.3.2-002": [
        "associate-name-reads-expression-value",
        "associate-name-defines-variable-selector",
        "associate-name-not-outside-block-source",
    ],
    "S11.1.3.2-003": ["character-length-type-parameter"],
    "S11.1.3.3-001": ["same-rank-as-selector", "nondefault-lower-bound", "upper-bound-from-extent"],
    "S11.1.3.3-005": ["definable-selector-assignment-control"],
}
REMAINING_PENDING = {
    "S11.1.3.2-001": set(),
    "S11.1.3.2-002": set(),
    "S11.1.3.2-003": {
        "kind-type-parameter-source",
        "nonpolymorphic-selector-control",
    },
    "S11.1.3.2-004": {"attribute-ownership-boundary"},
    "S11.1.3.2-005": {"outside-end-associate-branch-rejected"},
    "S11.1.3.3-001": {"no-allocatable-attribute-source", "no-pointer-attribute-source"},
    "S11.1.3.3-002": {"same-corank-as-selector-source", "coarray-cobounds-same-source"},
    "S11.1.3.3-003": {"change-team-associating-entity-coarray-source", "codimension-decl-corank-cobounds-source"},
    "S11.1.3.3-004": {
        "asynchronous-volatile-variable-selector",
        "no-optional-attribute-source",
    },
    "S11.1.3.3-005": {
        "nondefinable-selector-definition-rejected",
        "nondefinable-selector-undefinition-rejected",
        "selector-not-vdc-associate-definition-rejected",
        "selector-not-vdc-pointer-association-rejected",
    },
}
COMPLETIONS = {
    variant: "ASSOCIATE " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
ORACLE_PREFIXES = {
    "S11.1.3.2-001": "S11.1.3.2-001 ASSOCIATE selector-evaluation runtime fixtures: ",
    "S11.1.3.2-002": "S11.1.3.2-002 ASSOCIATE association runtime fixtures: ",
    "S11.1.3.2-003": "S11.1.3.2-003 ASSOCIATE type-parameter runtime fixture: ",
    "S11.1.3.3-001": "S11.1.3.3-001 ASSOCIATE rank and bounds runtime fixtures: ",
    "S11.1.3.3-005": "S11.1.3.3-005 ASSOCIATE definability runtime fixture: ",
}
LIMIT_PREFIXES = {
    "S11.1.3.2-001": "S11.1.3.2-001 ASSOCIATE selector-evaluation fixture boundaries: ",
    "S11.1.3.2-002": "S11.1.3.2-002 ASSOCIATE association fixture boundaries: ",
    "S11.1.3.2-003": "S11.1.3.2-003 ASSOCIATE type-parameter fixture boundaries: ",
    "S11.1.3.3-001": "S11.1.3.3-001 ASSOCIATE rank and bounds fixture boundaries: ",
    "S11.1.3.3-005": "S11.1.3.3-005 ASSOCIATE definability fixture boundaries: ",
}
ORACLES = {
    "S11.1.3.2-001": ORACLE_PREFIXES["S11.1.3.2-001"] + (
        "two complete run/effect/f2023 programs observe selector evaluation before ASSOCIATE block "
        "execution without side-effect or call-count oracles. The expression-selector case evaluates "
        "seed+17 while seed is 23, then changes seed to -900 inside the block and reads the associate "
        "name as literal 40; a rule that re-evaluated after the block assignment would produce -883. "
        "The variable-designator case uses a(idx) with idx=2, changes idx to 4 inside the block, assigns "
        "through cell, and checks that a(2) becomes 77 while a(4) remains 44; a deferred-subscript rule "
        "would update the wrong element. The selector expressions are ordinary integer expressions and "
        "the observations are final scalar values plus exact completion stdout."
    ),
    "S11.1.3.2-002": ORACLE_PREFIXES["S11.1.3.2-002"] + (
        "three complete run/effect/f2023 programs observe the associate name identifying the associated "
        "entity during the block. The expression-read case binds expr_value to left*10+right with left=12 "
        "and right=5, changes both operands in the block, and requires expr_value to remain 125. The "
        "variable-selector case binds alias to target, assigns alias=271 inside the block, and observes "
        "target changed from 314 to 271. The scope case preloads an outer integer named item with sentinel "
        "707, binds the associate name item to target, writes only 303 through the associate name, and "
        "after END ASSOCIATE requires outer item still 707 and target 303. Thus the outer sentinel is "
        "distinct from every value written inside the construct."
    ),
    "S11.1.3.2-003": ORACLE_PREFIXES["S11.1.3.2-003"] + (
        "one complete run/effect/f2023 program observes a required character type parameter directly "
        "with LEN. The selector is the substring parent(3:8) of a CHARACTER(LEN=9) variable, so the "
        "selector's length type parameter is 6 by the substring endpoints and the associating entity "
        "must assume that value. The program checks LEN(slice)==6 explicitly; no blank-padded character "
        "comparison is used as a length oracle. A rule copying the parent length 9, using default length "
        "1, or otherwise not assuming the selector type parameter would fail."
    ),
    "S11.1.3.3-001": ORACLE_PREFIXES["S11.1.3.3-001"] + (
        "three complete run/effect/f2023 programs observe rank and bounds with inquiry functions whose "
        "expected results are required by p1. The rank case associates tile with a rank-two section "
        "grid(-1:3:2,8:12:4), assigns SHAPE(tile) to a length-two integer vector, and requires [3,2]. "
        "The lower-bound case checks both a whole-array selector, for which LBOUND(whole,1) is the "
        "nondefault declared lower bound -5, and a section selector base(-3:3:2), for which LBOUND(sec,1) "
        "is 1 even though the selected subscripts run from -3 to 3. The upper-bound case associates vec "
        "with base(12:20:3), whose extent is 3 and whose LBOUND result is 1, so UBOUND(vec,1) must be "
        "1+3-1 = 3 rather than the selector subscript upper bound 20 or underlying array upper bound 21."
    ),
    "S11.1.3.3-005": ORACLE_PREFIXES["S11.1.3.3-005"] + (
        "one complete run/positive-control/f2023 program observes definability through a definable variable selector. "
        "The selector is the triplet section store(6:8), which has no vector subscript and is initialized "
        "to values distinct from the assigned values. Inside ASSOCIATE, vec is assigned [601,602,603]; "
        "after END ASSOCIATE the corresponding selector elements store(6:8) must hold those values while "
        "neighboring store(5) remains 50. A copy-only, expression-only or nondefinable associate-name rule "
        "would not update the selector."
    ),
}
LIMITATIONS = {
    "S11.1.3.2-001": LIMIT_PREFIXES["S11.1.3.2-001"] + (
        "only expression-selector-value-before-block and variable-designator-subexpressions-before-block "
        "are represented by this generator. block-executes-after-selector-evaluation is supplied by the "
        "associate_blocks_11_1 generator. The programs do not observe evaluation order among multiple selectors, function "
        "side effects, call counts, undefined values, diagnostics, addresses or temporary storage."
    ),
    "S11.1.3.2-002": LIMIT_PREFIXES["S11.1.3.2-002"] + (
        "only value reads, assignment through a definable selector and an outer-homonym runtime scoping "
        "control are represented. The scope fixture proves that this ASSOCIATE construct did not modify "
        "the outer homonym; it is not a general Clause 19 name-resolution or lifetime proof and makes no "
        "diagnostic claim about using an associate name after the construct."
    ),
    "S11.1.3.2-003": LIMIT_PREFIXES["S11.1.3.2-003"] + (
        "only character-length-type-parameter is represented by this generator. declared-type-control and "
        "polymorphic-selector-control are supplied by the associate_blocks_11_1 generator. "
        "kind-type-parameter-source remains pending because this packet does not assume a non-default kind "
        "exists on every processor, and nonpolymorphic-selector-control remains pending until a distinct "
        "consumer rule requires nonpolymorphism."
    ),
    "S11.1.3.3-001": LIMIT_PREFIXES["S11.1.3.3-001"] + (
        "only same-rank-as-selector, nondefault-lower-bound and upper-bound-from-extent are represented. "
        "The section-bound fixtures deliberately make associating-entity bounds differ from selector "
        "subscript bounds and underlying declared bounds, so copying those bounds would fail. The "
        "whole-array lower-bound control catches a processor that defaulted every associate-name lower "
        "bound to 1. no-allocatable-attribute-source and no-pointer-attribute-source remain pending as "
        "source/diagnostic contrasts rather than runtime effects."
    ),
    "S11.1.3.3-005": LIMIT_PREFIXES["S11.1.3.3-005"] + (
        "only definable-selector-assignment-control is represented. The four negative facets for "
        "nondefinable selectors and variable-definition/pointer-association contexts remain pending "
        "because they require their selector-owner rules and Clause 19 context rules to isolate a "
        "diagnostic. No pointer association, undefinition, protected object, optional dummy or procedure "
        "dummy mechanism is used."
    ),
}


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown ASSOCIATE fixture variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__associate_construct_" + variant


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
        token = f"ACF:{self.variant}:{name}"
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


def begin_program(p, rule, facet):
    p.add(f"! rule: {rule}\n! covers: {facet}\n")
    p.add("! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.\n")
    p.add(f"program associate_construct_{p.variant}_effect\n  implicit none\n  integer :: checks\n")


def finish_program(p, observations):
    total = p.guard("check-total", "checks", len(observations), len(observations) + 1,
                    category="completion", counter=None)
    completion = p.completion()
    p.add(f"end program associate_construct_{p.variant}_effect\n")
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


def program(variant):
    rule, facet = VARIANTS[variant]
    p = Program(variant)
    begin_program(p, rule, facet)
    observations = []
    notes = []

    if variant == "expression_selector_value":
        p.add("  integer :: seed\n  seed=23\n  checks=0\n")
        p.add("  ! seed+17 is evaluated before the block; changing seed later must not change value.\n")
        p.add("  associate (value => seed + 17)\n    seed=-900\n")
        observations.append(p.guard("value-before-block", "value", 40, -883))
        observations.append(p.guard("operand-changed-control", "seed", -900, 23, category="control"))
        p.add("  end associate\n")
        notes = ["selector seed+17 with seed=23", "associate name value expected 40"]
    elif variant == "subscript_expression_capture":
        p.add("  integer :: idx\n  integer :: a(1:4)\n  a=[11,22,33,44]\n  idx=2\n  checks=0\n")
        p.add("  ! idx in a(idx) is evaluated before the block; changing idx to 4 must not retarget cell.\n")
        p.add("  associate (cell => a(idx))\n    idx=4\n    cell=77\n  end associate\n")
        observations.append(p.guard("captured-element-updated", "a(2)", 77, 22))
        observations.append(p.guard("deferred-index-not-updated", "a(4)", 44, 77, category="control"))
        observations.append(p.guard("index-change-control", "idx", 4, 2, category="control"))
        notes = ["selector a(idx) with idx=2", "inside block idx=4, cell assignment updates a(2)"]
    elif variant == "expression_associate_read":
        p.add("  integer :: left, right\n  left=12\n  right=5\n  checks=0\n")
        p.add("  ! expr_value identifies the evaluated expression entity throughout this block.\n")
        p.add("  associate (expr_value => left*10 + right)\n    left=-1\n    right=-2\n")
        observations.append(p.guard("expression-read", "expr_value", 125, -12))
        observations.append(p.guard("left-mutated-control", "left", -1, 12, category="control"))
        observations.append(p.guard("right-mutated-control", "right", -2, 5, category="control"))
        p.add("  end associate\n")
        notes = ["selector left*10+right with left=12 right=5", "associate name expr_value expected 125"]
    elif variant == "variable_selector_define":
        p.add("  integer :: target\n  target=314\n  checks=0\n")
        p.add("  ! alias identifies target, so defining alias in the block changes target.\n")
        p.add("  associate (alias => target)\n    alias=271\n  end associate\n")
        observations.append(p.guard("selector-defined", "target", 271, 314))
        notes = ["selector target initial 314", "alias assignment expected target 271"]
    elif variant == "outer_homonym_scope":
        p.add("  integer :: item, target\n  item=707\n  target=101\n  checks=0\n")
        p.add("  ! Outer item sentinel 707 is distinct from inner writes 303 and target initial 101.\n")
        p.add("  associate (item => target)\n    item=303\n  end associate\n")
        observations.append(p.guard("outer-sentinel-preserved", "item", 707, 303, category="scope"))
        observations.append(p.guard("selector-received-inner-write", "target", 303, 101, category="scope"))
        notes = ["outer item sentinel 707", "inside writes associate item=303, target expected 303"]
    elif variant == "character_length_parameter":
        p.add("  character(len=9) :: parent\n  parent='abcdefghi'\n  checks=0\n")
        p.add("  ! The selector parent(3:8) has character length type parameter 6.\n")
        p.add("  associate (slice => parent(3:8))\n")
        observations.append(p.guard("slice-length", "len(slice)", 6, 9, category="length"))
        observations.append(p.guard("parent-length-control", "len(parent)", 9, 6, category="control"))
        p.add("  end associate\n")
        notes = ["selector parent(3:8)", "associate name slice LEN expected 6, parent LEN 9"]
    elif variant == "rank_shape":
        p.add("  integer :: grid(-2:4,7:12)\n  integer :: dims(2)\n  grid=0\n  checks=0\n")
        p.add("  ! Section grid(-1:3:2,8:12:4) is rank two with extents 3 and 2.\n")
        p.add("  associate (tile => grid(-1:3:2,8:12:4))\n    dims=shape(tile)\n")
        observations.append(p.guard("rank-two-first-extent", "dims(1)", 3, 2, category="shape"))
        observations.append(p.guard("rank-two-second-extent", "dims(2)", 2, 3, category="shape"))
        p.add("  end associate\n")
        notes = ["selector grid(-1:3:2,8:12:4)", "shape(tile) expected [3,2]"]
    elif variant == "lower_bound_lbound":
        p.add("  integer :: base(-5:5)\n  integer :: whole_lower, section_lower\n  base=0\n  checks=0\n")
        p.add("  ! Whole-array LBOUND is -5; section base(-3:3:2) has LBOUND result 1.\n")
        p.add("  associate (whole => base)\n    whole_lower=lbound(whole,1)\n  end associate\n")
        p.add("  associate (sec => base(-3:3:2))\n    section_lower=lbound(sec,1)\n  end associate\n")
        observations.append(p.guard("whole-nondefault-lower", "whole_lower", -5, 1, category="bounds"))
        observations.append(p.guard("section-lbound-result", "section_lower", 1, -3, category="bounds"))
        notes = ["whole selector base lower bound -5", "section selector base(-3:3:2) associate lower bound 1"]
    elif variant == "upper_bound_extent":
        p.add("  integer :: base(10:21)\n  integer :: lo, hi, extent\n  base=0\n  checks=0\n")
        p.add("  ! Section base(12:20:3) selects 12,15,18: LBOUND 1, extent 3, UBOUND 3.\n")
        p.add("  associate (vec => base(12:20:3))\n    lo=lbound(vec,1)\n    hi=ubound(vec,1)\n    extent=size(vec)\n  end associate\n")
        observations.append(p.guard("section-lower-one", "lo", 1, 12, category="bounds"))
        observations.append(p.guard("section-extent-three", "extent", 3, 4, category="bounds"))
        observations.append(p.guard("upper-from-extent", "hi", 3, 20, category="bounds"))
        notes = ["selector base(12:20:3) extent 3", "associate vec bounds expected 1:3"]
    elif variant == "definable_selector_assignment":
        p.add("  integer :: store(5:9)\n  store=[50,60,70,80,90]\n  checks=0\n")
        p.add("  ! The triplet section store(6:8) is definable and has no vector subscript.\n")
        p.add("  associate (vec => store(6:8))\n    vec=[601,602,603]\n  end associate\n")
        observations.append(p.guard("first-selector-element", "store(6)", 601, 60))
        observations.append(p.guard("middle-selector-element", "store(7)", 602, 70))
        observations.append(p.guard("last-selector-element", "store(8)", 603, 80))
        observations.append(p.guard("neighbor-unchanged", "store(5)", 50, 601, category="control"))
        notes = ["selector store(6:8)", "assigning vec updates store(6:8) to 601,602,603"]
    else:
        raise ValueError("unknown ASSOCIATE fixture variant")

    omissions = finish_program(p, observations)
    raw = p.text.encode("ascii")
    for probe in p.probes + omissions:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError("an ASSOCIATE mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, rule=rule, facets=[facet],
        evidence="positive-control" if variant == "definable_selector_assignment" else "effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[variant],
        guards=p.guards, probes=p.probes, omissions=omissions, observations=observations, notes=notes,
        expected_counts=dict(checks=len(observations)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("associate_construct_" + spec["variant"])
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


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected ASSOCIATE facets changed for " + rule)
        for facet in facets:
            owner.setdefault("pending", {}).pop(facet, None)
        expected_remaining = REMAINING_PENDING[rule]
        if set(owner.get("pending", {})) != expected_remaining:
            raise ValueError("unexpected remaining pending facets for " + rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEWS[section]).read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the ASSOCIATE generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    replacement_intro = (
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.")
    before = before.replace(
        replacement_intro,
        "Catalogue: see the corresponding `doc/catalogues/*.json` entry. Selected ASSOCIATE runtime "
        "fixtures now supply executable standard-oracle observations; no oracle approval, fixture "
        "approval, or coverage claim is supplied here.")
    if section == "11.1.3.2":
        summary = (
            SUMMARY_BEGIN + "\n"
            "## ASSOCIATE execution runtime observations\n\n"
            "Six complete run/effect/f2023 programs observe selector evaluation before the block, "
            "reading expression-selector associate names, defining variable selectors through associate "
            "names, preserving an outer homonym sentinel after END ASSOCIATE, and the character length "
            "type parameter of a substring selector. Each source has exactly one `! rule:` and one "
            "`! covers:` header. Expected values are literal integers derived from 11.1.3.2, with `LEN` "
            "used explicitly for the character-length fixture.\n\n"
            "The `associate_blocks_11_1` generator supplies the remaining selector/block sequencing, "
            "declared-type, polymorphic-selector and internal end-branch controls. Attribute ownership, "
            "outside-branch-control, kind and nonpolymorphism facets remain pending for the reasons recorded "
            "in the owning catalogue entries.\n"
            + SUMMARY_END)
    else:
        summary = (
            SUMMARY_BEGIN + "\n"
            "## ASSOCIATE attribute runtime observations\n\n"
            "Three complete run/effect/f2023 programs observe rank, lower bounds and upper bounds; one "
            "run/positive-control/f2023 program observes definability. The bounds fixtures use nonunit declared bounds and array-section selectors "
            "whose associate-name bounds differ from selector subscript bounds, while a whole-array "
            "control catches an always-lower-bound-one implementation. Assignment through an associate "
            "name for a definable section is observed by reading the original selector afterwards.\n\n"
            "ALLOCATABLE/POINTER attribute negatives, coarray/corank rules, CHANGE TEAM, ASYNCHRONOUS, "
            "VOLATILE, no-OPTIONAL and nondefinable-context negatives remain pending because they need "
            "source/diagnostic contexts or unregistered Clause 15/19 owners. Dynamic type, optional-present "
            "and contiguity observations are supplied by the `associate_blocks_11_1` generator.\n"
            + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the ASSOCIATE summary boundaries changed for " + section)
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
    stale = []
    updates = {}
    views = {}
    for section in SECTIONS:
        path = root / CATALOGUES[section]
        catalogue = json.loads(path.read_text())
        updated = synced_catalogue(section, catalogue)
        view = render_view(section, updated, root)
        updates[section] = updated
        views[section] = view
        if catalogue != updated:
            stale.append(CATALOGUES[section])
        if (root / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    stale.extend(path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw)
    if check:
        if stale:
            raise ValueError("stale ASSOCIATE fixture family: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updates[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} ASSOCIATE cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
