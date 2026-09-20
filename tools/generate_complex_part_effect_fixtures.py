#!/usr/bin/env python3
"""Complex part designator runtime effects with whole-parent mutations."""

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
RULE = "S9.4.4-001"
SECTION = "9.4.4"
CATALOGUE = "doc/catalogues/complex_part_9_4_4.json"
VIEW = "doc/fortran_2023_9_4_4.md"
VARIANTS = {
    "real_part_selection": "real-part-selection",
    "imaginary_part_selection": "imaginary-part-selection",
    "kind_inherited": "kind-inherited",
    "scalar_shape_inherited": "scalar-shape-inherited",
    "array_shape_inherited": "array-shape-inherited",
    "defining_context_boundary": "defining-context-boundary",
}
FACETS = tuple(VARIANTS.values())
COMPLETIONS = {
    variant: "COMPLEX PART " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
ORACLE_PREFIX = "S9.4.4-001 complex part runtime effects: "
LIMIT_PREFIX = "S9.4.4-001 complex part runtime boundaries: "
SUMMARY_BEGIN = "<!-- BEGIN COMPLEX PART EFFECTS -->"
SUMMARY_END = "<!-- END COMPLEX PART EFFECTS -->"
ORACLE = ORACLE_PREFIX + (
    "six complete run/effect/f2023 programs observe the selected p1 effects with actual %RE/%IM "
    "designators. Scalar real and imaginary selection compare z%RE and z%IM from a defined "
    "COMPLEX z=(7.0,-2.0) against independent literal 7.0 and -2.0 oracles, never REAL, "
    "AIMAG or CMPLX. The kind case declares COMPLEX(KIND(0.0D0)), defines finite literal "
    "parts, and compares KIND(z%RE) and KIND(z%IM) directly with KIND(z) without assuming a "
    "numeric kind value. The scalar-shape case assigns z%RE to an ordinary scalar REAL and "
    "checks the literal selected value. The array-shape case defines three explicit complex "
    "elements with distinct real and imaginary parts, then checks SIZE(a%RE)==3 and "
    "SUM(a%IM)==1.5 against independent exact literals. The defining-context case assigns "
    "literal 4.0 through z%IM, then checks that z%IM is 4.0 and z%RE remains its original "
    "literal 3.0. Each assertion increments a counter and a final total guard precedes exact "
    "completion stdout, empty stderr and exit0. Wrong-oracle mutations cover every assertion "
    "and completion literal; whole-program omissions remove observations, grouped observations, "
    "the defining assignment where safe, or the completion line. Only a current passing complete "
    "parent and the intended runtime failure establish mutation sensitivity."
)
LIMITATION = LIMIT_PREFIX + (
    "only real-part-selection, imaginary-part-selection, kind-inherited, scalar-shape-inherited, "
    "array-shape-inherited and defining-context-boundary are represented. The result-real-type "
    "facet remains pending for diagnostic/control design. These cases do not use source rewrites, "
    "layout, TRANSFER, address arithmetic, REAL, AIMAG, CMPLX, undefined values, epsilon tolerances, "
    "coarrays, multi-image behavior, extra I/O, STOP codes or nonliteral value oracles. KIND is used "
    "only for the kind facet; SIZE and SUM are used only for the array-shape facet. The scalar-shape "
    "observation is a scalar-context witness paired with the separate array source, not a general rank "
    "diagnostic. Guard markers are program output, not mandated ERROR STOP wording or a universal "
    "numeric error status. Unsupported processors must still fail honestly; no workaround weakens "
    "the Fortran source. Generation grants no review approval, evidence link, baseline update, "
    "SourceUse renewal or universal compiler-conformance credit."
)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown complex part variant")
    return "S9_4_4_001_valid__complex_part_effect_" + variant


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
        token = f"CPE:{self.variant}:{name}"
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
    if variant == "real_part_selection":
        declarations = "  complex :: z\n  integer :: checks\n"
        definitions = ["  z=(7.0, -2.0)\n"]
        observations = [("real-selected", "z%RE", "7.0", "-2.0", "value")]
    elif variant == "imaginary_part_selection":
        declarations = "  complex :: z\n  integer :: checks\n"
        definitions = ["  z=(7.0, -2.0)\n"]
        observations = [("imaginary-selected", "z%IM", "-2.0", "7.0", "value")]
    elif variant == "kind_inherited":
        declarations = "  complex(kind(0.0d0)) :: z\n  integer :: checks\n"
        definitions = ["  z=(3.0d0, -4.0d0)\n"]
        observations = [
            ("real-kind", "kind(z%RE)", "kind(z)", "kind(z)+1", "kind"),
            ("imaginary-kind", "kind(z%IM)", "kind(z)", "kind(z)+1", "kind"),
        ]
    elif variant == "scalar_shape_inherited":
        declarations = "  complex :: z\n  real :: selected\n  integer :: checks\n"
        definitions = ["  z=(5.0, -6.0)\n", "  selected=-8.0\n", "  selected=z%RE\n"]
        observations = [("scalar-selected", "selected", "5.0", "-6.0", "shape")]
    elif variant == "array_shape_inherited":
        declarations = "  complex :: a(3)\n  integer :: checks\n"
        definitions = [
            "  a(1)=(1.0, 0.5)\n",
            "  a(2)=(-2.0, 1.25)\n",
            "  a(3)=(4.0, -0.25)\n",
        ]
        observations = [
            ("real-size", "size(a%RE)", "3", "2", "shape"),
            ("imaginary-sum", "sum(a%IM)", "1.5", "3.0", "value"),
        ]
    elif variant == "defining_context_boundary":
        declarations = "  complex :: z\n  integer :: checks\n"
        definitions = ["  z=(3.0, -1.0)\n", "  z%IM=4.0\n"]
        observations = [
            ("imaginary-assigned", "z%IM", "4.0", "-1.0", "definition"),
            ("real-unchanged", "z%RE", "3.0", "4.0", "boundary"),
        ]
    else:
        raise ValueError("unknown complex part variant")
    return declarations, definitions, observations


def program(variant):
    declarations, definitions, observations = spec_rows(variant)
    p = Program(variant)
    p.add(f"program complex_part_{variant}_effect\n  implicit none\n" + declarations + "  checks=0\n")
    definition_spans = [(text, p.add(text)) for text in definitions]
    observed = [p.guard(name, expression, expected, replacement, category=category)
                for name, expression, expected, replacement, category in observations]
    total = p.guard("check-total", "checks", str(len(observed)), str(len(observed) + 1),
                    counter=None, category="completion")
    completion = p.completion()
    p.add(f"end program complex_part_{variant}_effect\n")

    omissions = []
    plans = [("omit-observation-" + guard["id"], guard["block_span"], total) for guard in observed]
    if len(observed) > 1:
        plans.append(("omit-all-observations", [observed[0]["block_span"][0], observed[-1]["block_span"][1]], total))
    if variant == "scalar_shape_inherited":
        # selected remains explicitly defined to the sentinel, so the later read is still defined.
        plans.append(("omit-scalar-selection", definition_spans[-1][1], observed[0]))
    if variant == "defining_context_boundary":
        # z remains explicitly defined by the first assignment, including its original imaginary part.
        plans.append(("omit-imaginary-definition", definition_spans[-1][1], observed[0]))
    start, end = completion["block_span"]
    omissions.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
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
            raise ValueError("a complex-part oracle mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, facets=[VARIANTS[variant]], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(p.text.encode("ascii")),
        completion=COMPLETIONS[variant], guards=p.guards, probes=p.probes, omissions=omissions,
        observations=observed, definitions=[dict(text=text, span=span) for text, span in definition_spans],
        expected_counts=dict(checks=len(observed)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("complex_part_effect_" + spec["variant"])
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
    if len(matches) != 1 or not set(FACETS + ("result-real-type",)) <= set(matches[0]["facets"]):
        raise ValueError("the selected complex-part definitions changed")
    owner = matches[0]
    if owner["category"] != "effect" or set(FACETS) & set(owner.get("positive_control_facets", [])):
        raise ValueError("the selected complex-part facets must remain runtime effects")
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    if set(owner.get("pending", {})) != {"result-real-type"}:
        raise ValueError("only result-real-type should remain pending for S9.4.4-001")
    owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    limitation = owner.get("oracle_limitation", "")
    old = ("This is a source-only catalogue packet. It creates no Fortran test program, execution, "
           "evidence link, fixture approval, oracle approval, or coverage claim.")
    new = ("The original source-only registration created no Fortran test program, execution, evidence "
           "link, fixture approval, oracle approval, or coverage claim; this generator supplies the six "
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
        raise ValueError("the complex-part generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: `doc/catalogues/complex_part_9_4_4.json`.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/complex_part_9_4_4.json`.\n"
        "The original source-only registration supplied pending plans; the bounded runtime fixtures below "
        "supply cases and mutation plans, not oracle approval, fixture approval or universal coverage.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Complex part runtime observations\n\n"
        "Six complete run/effect/f2023 programs cover the selected S9.4.4-001 facets.\n"
        "The real and imaginary cases define `z=(7.0,-2.0)` and compare `%RE` or\n"
        "`%IM` directly with independent exact literals. The kind case uses\n"
        "`COMPLEX(KIND(0.0D0))` and compares both part-designator kinds with\n"
        "`KIND(z)`, never with a baked-in numeric kind. The scalar-shape case\n"
        "assigns `z%RE` to a scalar REAL; the array-shape case checks\n"
        "`SIZE(a%RE)==3` and `SUM(a%IM)==1.5` for three defined elements with\n"
        "distinct real and imaginary parts. The defining-context case assigns\n"
        "through `z%IM` and verifies the imaginary update and unchanged real part.\n\n"
        "Every assertion prints a unique `CPE:` failure token and stops on mismatch,\n"
        "increments a check counter, and is followed by a final check-total guard\n"
        "before exact completion stdout, empty stderr and exit0. Wrong-oracle plans\n"
        "cover every guard and completion literal. Omission plans delete observation\n"
        "blocks, grouped observations where present, safe defining assignments and\n"
        "the completion line. Mutations are complete-parent byte spans.\n\n"
        "Only the six selected pending entries are removed. `result-real-type` remains\n"
        "pending. The programs intentionally use no REAL, AIMAG, CMPLX, TRANSFER,\n"
        "layout assumptions, undefined reads, tolerances, coarrays or multi-image I/O.\n"
        "No evidence link, baseline update, SourceUse renewal or approval is created.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the complex-part effect summary boundaries changed")
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
            raise ValueError("stale complex-part effect family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} complex-part cases, "
          f"{len(FACETS)} facets, {sum(len(row['probes']) for row in specs.values())} wrong-oracle "
          f"and {sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
