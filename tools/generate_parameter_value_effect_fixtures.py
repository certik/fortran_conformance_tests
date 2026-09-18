#!/usr/bin/env python3
"""Finite PARAMETER values, complete execution guards and whole-parent mutations."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, probe_verdict, sha, wrong_oracle_source


ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.6.11-004"
SECTION = "8.6.11"
CATALOGUE = "doc/catalogues/parameter_statement_8_6_11.json"
VIEW = "doc/fortran_2023_8_6_11.md"
VARIANTS = {
    "integer": "corresponding-integer-values",
    "logical": "logical-values",
    "character_padding": "character-padding",
    "character_truncation": "character-truncation",
    "array": "conforming-array-values",
    "scalar_array": "scalar-to-explicit-array-values",
}
FACETS = tuple(VARIANTS.values())
COMPLETIONS = {variant: "PARAMETER VALUES " + variant.upper().replace("_", " ") + " OK\n"
               for variant in VARIANTS}
ORACLE_PREFIX = "S8.6.11-004 finite statement-value effects: "
LIMIT_PREFIX = "S8.6.11-004 finite statement-value boundaries: "
SUMMARY_BEGIN = "<!-- BEGIN PARAMETER VALUE EFFECTS -->"
SUMMARY_END = "<!-- END PARAMETER VALUE EFFECTS -->"
ORACLE = ORACLE_PREFIX + (
    "six complete run/effect/f2023 programs define actual named constants using PARAMETER statements "
    "after explicit type and rank declarations. An internal observer directly checks the host-associated "
    "constants, not copied variable stand-ins. The INTEGER program checks separate first=3 and second=7 "
    "values and MOD(28,3) against the independent literal1. The LOGICAL program checks true and false "
    "using logical equivalence without a representation or I/O-spelling assumption. Default CHARACTER "
    "programs check length4 and AB followed by two blanks, and length2 with right truncation to AB; "
    "whole values and individual positions have independent character literals. The truncation program "
    "also observes an actual assumed-length named constant defined as CDE, with independent length3 "
    "and value CDE. A fixed vector is checked elementwise against3/7; a fixed2x2 array with scalar "
    "initializer5 has all four actual elements checked against5. Main requires one observer entry, "
    "one normal return, all individual value/property checks and three completed caller checks before "
    "exact completion stdout, empty stderr and exit0. Every assertion and completion literal has a "
    "one-span complete-parent wrong-oracle mutation. Separate full-program omissions remove the call, "
    "the observer body or one observation with its check increment; entry/count guards detect them. "
    "Only a current passing complete parent and the intended runtime failure establish sensitivity."
)
LIMITATION = LIMIT_PREFIX + (
    "only the six named finite default-kind value facets are represented. The simple-derived and "
    "numeric-kind-and-BOZ plans remain pending, as do every foreign requirement and unselected "
    "source/interface/grammar facet. No implicit-typing, late-rank, implied-shape, zero-sized-array, "
    "optional-kind, REAL/COMPLEX, BOZ, storage-layout, ABI, pointer, allocation, finalization or "
    "defined-assignment effect is inferred. The MOD observation uses literal1, not a second MOD "
    "evaluation. Padding compares both trailing positions and the declared length, without relying "
    "only on unequal-length character comparison. Named constants are never assigned or passed to "
    "a defining dummy, and the PARAMETER conversion reference is not a runtime assignment operation. "
    "Canonical constant-expression, MOD, LEN, character, constructor and intrinsic-assignment rules "
    "retain their owners; no reuse link or duplicate runtime execution is invented. Guard markers "
    "are program output, not mandated ERROR STOP English or a universal numeric error status. "
    "Build failures, missing artifacts/traces, failed or stale parents, preempting guards, crashes "
    "and resource/time failures cannot qualify sensitivity. Actual f2018 observations are supplementary "
    "to f2023 qualification. Generation grants no review and changes no baseline, index or evidence inventory."
)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown PARAMETER value variant")
    return "S8_6_11_004_valid__parameter_value_effect_" + variant


def observations(variant):
    if variant == "integer":
        declarations = (
            "  integer :: first, second, remainder\n"
            "  parameter (first=3, second=7, remainder=mod(28,3))\n")
        values = [
            ("first", "first", "3", "4", "/=", "value"),
            ("second", "second", "7", "8", "/=", "value"),
            ("remainder", "remainder", "1", "2", "/=", "value"),
        ]
    elif variant == "logical":
        declarations = "  logical :: yes, no\n  parameter (yes=.true., no=.false.)\n"
        values = [
            ("true", "yes", ".true.", ".false.", ".neqv.", "value"),
            ("false", "no", ".false.", ".true.", ".neqv.", "value"),
        ]
    elif variant in {"character_padding", "character_truncation"}:
        padding = variant == "character_padding"
        length, value = (4, "AB  ") if padding else (2, "AB")
        declarations = f"  character(len={length}) :: word\n"
        if not padding:
            declarations += "  character(len=*) :: full_word\n"
        declarations += "  parameter (word='AB')\n" if padding else (
            "  parameter (word='ABCDE', full_word='CDE')\n")
        values = [
            ("length", "len(word)", str(length), str(length + 1), "/=", "length"),
            ("whole-word", "word", repr(value), repr("X" + value[1:]), "/=", "value"),
        ]
        values += [(f"position-{index}", f"word({index}:{index})", repr(character), "'X'", "/=", "value")
                   for index, character in enumerate(value, 1)]
        if not padding:
            values += [
                ("assumed-length", "len(full_word)", "3", "4", "/=", "length"),
                ("assumed-value", "full_word", "'CDE'", "'XDE'", "/=", "value"),
            ]
    elif variant == "array":
        declarations = "  integer :: values(2)\n  parameter (values=[3,7])\n"
        values = [
            ("element-1", "values(1)", "3", "4", "/=", "value"),
            ("element-2", "values(2)", "7", "8", "/=", "value"),
        ]
    elif variant == "scalar_array":
        declarations = "  integer :: values(2,2)\n  parameter (values=5)\n"
        values = [(f"element-{i}-{j}", f"values({i},{j})", "5", "6", "/=", "value")
                  for j in (1, 2) for i in (1, 2)]
    else:
        raise ValueError("unknown PARAMETER value variant")
    return declarations, values


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

    def guard(self, name, expression, expected, replacement, *, operator="/=", category="event",
              counter="main_checks", indent="  "):
        block_start = len(self.text)
        prefix = indent + f"if ({expression} {operator} "
        start = block_start + len(prefix)
        token = f"PVE:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            operator=operator, expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ") then\n" + indent + f"  write(*,'(a)') '{token}'\n"
                 + indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")
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
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.add(prefix + literal + "'\n")


def program(variant):
    declarations, values = observations(variant)
    p = Program(variant)
    p.add(f"program parameter_value_{variant}_effect\n  implicit none\n" + declarations
          + "  integer :: visits, returns, observed_checks, main_checks\n"
          + "  visits=0\n  returns=0\n  observed_checks=0\n  main_checks=0\n")
    call_span = p.add("  call observe\n")
    p.add("  returns=returns+1\n")
    entry = p.guard("observer-visits", "visits", "1", "2")
    p.guard("normal-returns", "returns", "1", "2")
    checks = p.guard("observed-checks", "observed_checks", str(len(values)), str(len(values) + 1),
                     category="completion")
    p.guard("main-check-total", "main_checks", "3", "4", counter=None, category="completion")
    p.completion()
    p.add("contains\n  subroutine observe\n    implicit none\n")
    body_start = len(p.text)
    p.add("    visits=visits+1\n")
    observed = [p.guard(name, expression, expected, replacement, operator=operator, category=category,
                        counter="observed_checks", indent="    ")
                for name, expression, expected, replacement, operator, category in values]
    body_span = [body_start, len(p.text)]
    p.add(f"  end subroutine observe\nend program parameter_value_{variant}_effect\n")
    omissions = []
    plans = [("omit-observer-call", call_span, entry), ("empty-observer-body", body_span, entry)]
    plans += [("omit-observation-" + guard["id"], guard["block_span"], checks) for guard in observed]
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
            raise ValueError("a PARAMETER oracle mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, facets=[VARIANTS[variant]],
        source=p.text, source_sha256=sha(p.text.encode("ascii")), completion=COMPLETIONS[variant],
        guards=p.guards, probes=p.probes, omissions=omissions, observations=observed,
        observed_checks=len(values), main_checks=3, call_span=call_span, body_span=body_span)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("parameter_value_effect_" + spec["variant"])
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
        raise ValueError("the selected PARAMETER value definitions changed")
    owner = matches[0]
    if set(FACETS) & set(owner.get("positive_control_facets", [])):
        raise ValueError("the selected PARAMETER value facets must remain effects")
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    limitation = owner.get("oracle_limitation", "")
    old = "No cases are implemented here. "
    if limitation.startswith(old):
        limitation = "The original source-only registration supplied no cases. " + limitation[len(old):]
    owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the PARAMETER generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "separate. This source-only packet introduces pending plans, not execution.",
        "separate. The original source-only packet supplied pending plans; the\n"
        "bounded value fixtures below neither grant nor renew those reviews.")
    before = before.replace(
        "conversion. Its pending meaningful observations use independent INTEGER,",
        "conversion. The original finite value plans use independent INTEGER,")
    before = before.replace(
        "No cases, compiler runs, profiles, reviews, baseline changes, canonical links\n"
        "or SourceUses are created by this author packet.",
        "The original source registration supplied no cases or compiler runs.\n"
        "The value generator supplies fixtures and mutation plans, not approvals,\n"
        "baseline changes, profiles, canonical links or SourceUses.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Finite PARAMETER value observations\n\n"
        "Six complete run/effect/f2023 programs observe actual named constants\n"
        "defined by PARAMETER after prior type and rank declarations. The INTEGER\n"
        "case checks separate3/7 values and MOD(28,3) against literal1. LOGICAL\n"
        "checks use equivalence to true/false, without a storage representation.\n"
        "Default CHARACTER cases observe AB padded to length4 and ABCDE truncated\n"
        "to AB at length2, including individual positions and both trailing blanks.\n"
        "The latter also checks the actual assumed-length constant CDE at length3.\n"
        "A vector's two elements have separate3/7 oracles; scalar expansion into\n"
        "an explicit2x2 array checks each of its four elements against literal5.\n\n"
        "One internal observer directly references each host-associated constant.\n"
        "Its entry and every value/property check are counted. Main checks one\n"
        "entry, one normal return, the exact observation count and three caller\n"
        "checks before exact completion output. No copied variable is the subject.\n"
        "Whole-program wrong-oracle plans cover every assertion and completion;\n"
        "separate omissions remove the call, observer body or one check with its\n"
        "increment. Only actual intended failures following a current passing\n"
        "parent qualify sensitivity; synthetic transports are not native evidence.\n\n"
        "Only the selected six S8.6.11-004 facets and their bounded oracle text are\n"
        "generator-owned. Simple-derived and numeric-kind/BOZ plans remain pending;\n"
        "foreign source, case and review state remains independently managed.\n"
        "No assignment callback, allocation, address, optional representation,\n"
        "implied-shape or zero-sized-array effect is claimed. F2018 observations\n"
        "remain supplementary to the declared f2023 qualification.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the PARAMETER value summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return (before + begin + "\n\n"
            + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after)


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
            raise ValueError("stale PARAMETER value family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} PARAMETER value cases, "
          f"{len(FACETS)} facets, {sum(len(row['probes']) for row in specs.values())} wrong-oracle "
          f"and {sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
