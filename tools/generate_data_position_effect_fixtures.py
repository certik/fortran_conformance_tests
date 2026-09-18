#!/usr/bin/env python3
"""Finite DATA correspondence and initial-state effects with complete-source probes."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, probe_verdict, sha, wrong_oracle_source


ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.6.7-004"
SECTION = "8.6.7"
CATALOGUE = "doc/catalogues/data_statement_8_6_7.json"
VIEW = "doc/fortran_2023_8_6_7.md"
VARIANTS = {
    "scalar": "scalar-position-order",
    "array": "whole-array-element-order",
    "nonexecution": "initialization-not-execution",
}
FACETS = tuple(VARIANTS.values())
COMPLETIONS = {variant: "DATA POSITION " + variant.upper() + " OK\n" for variant in VARIANTS}
ORACLE_PREFIX = "S8.6.7-004 finite DATA position effects: "
LIMIT_PREFIX = "S8.6.7-004 finite DATA position boundaries: "
SUMMARY_BEGIN = "<!-- BEGIN DATA POSITION EFFECTS -->"
SUMMARY_END = "<!-- END DATA POSITION EFFECTS -->"
ORACLE = ORACLE_PREFIX + (
    "three complete run/effect/f2023 programs initialize actual ordinary default INTEGER variables "
    "exactly once using DATA. The scalar program observes i,j,k directly against independent11/22/33 "
    "before any executable definition of those subjects, with three counted observations. The array "
    "program declares a(2,3), initializes its whole name from the flat sequence11,21,12,22,13,23, and "
    "checks six separate coordinates(1,1),(2,1),(1,2),(2,2),(1,3),(2,3) against those independent literals. "
    "The rank-two Table9.1 order is1+(s1-1)+2*(s2-1); no RESHAPE, loop or re-expanded DATA is the oracle. "
    "The nonexecution program calls one internal INTEGER function whose explicitly declared ordinary "
    "local kept is directly checked as7 and returned before the physical DATA kept/7/ statement. "
    "Prior explicit locality excludes the DATA-only host-hiding condition of19.5.1.4p3. Main checks "
    "one entry, one before-RETURN event, one normal caller return, one direct local check, result7 "
    "and zero execution of the ordinary statement physically after DATA. Six caller checks precede "
    "completion. All parents require exact stdout, empty runtime stderr and exit0. Every guard and "
    "completion has a one-span full-source wrong-oracle plan. Omission plans remove reached checks "
    "with their increments, omit the function call, replace its executable prefix with a defined-result "
    "no-op, or remove RETURN so the after-DATA event is reached. DATA initialization is preserved in "
    "every mutation. Only current passing complete parents and intended runtime failures qualify."
)
LIMITATION = LIMIT_PREFIX + (
    "only scalar-position-order, whole-array-element-order and initialization-not-execution are "
    "represented. The other18 owner facets and all foreign requirements/pending/control/raw-review "
    "states remain independent. The DATA statements are initialization, not executable assignments "
    "or runtime scalar broadcasting; the array has exactly six object and value contributions. No "
    "subject has declaration/default/overlapping initialization, dummy/result/COMMON/host-data role, "
    "pointer, allocation, optional kind, REAL, BOZ, character conversion, component or implied-DO "
    "mechanism. The local kept is not the function result. No mutation deletes DATA or reads an "
    "uninitialized subject or result. Obsolescent placement under B.3.5 remains a conforming construct "
    "whose warning/report is not a wrong-value failure; no warning-as-error allowance is added. "
    "No SAVE retention, physical static storage, finalization, ABI or canonical graph is claimed. "
    "Crashes/internal/resource/time failures, missing artifacts/traces, failed/stale parents and "
    "preempting guards cannot establish sensitivity. Guard markers are program output, not required "
    "ERROR STOP English or a universal error status. F2018 observations remain supplementary to "
    "f2023 qualification. Generation grants no review and changes no baseline, index or evidence inventory."
)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown DATA position variant")
    return "S8_6_7_004_valid__data_position_effect_" + variant


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

    def guard(self, name, expression, expected, *, category="value", counter="checks", indent="  "):
        expected = str(expected)
        block_start = len(self.text)
        prefix = indent + f"if ({expression} /= "
        start = block_start + len(prefix)
        token = f"DPE:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=str(int(expected) + 1), span=[start, start + len(expected)],
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
    identifier(variant)
    p = Program(variant)
    p.add(f"program data_position_{variant}_effect\n  implicit none\n")
    omissions = []
    if variant in {"scalar", "array"}:
        if variant == "scalar":
            p.add("  integer :: i, j, k, checks\n  data i,j,k /11,22,33/\n")
            values = [("i", "i", 11), ("j", "j", 22), ("k", "k", 33)]
        else:
            p.add("  integer :: a(2,3), checks\n  data a /11,21,12,22,13,23/\n")
            values = [("a11", "a(1,1)", 11), ("a21", "a(2,1)", 21),
                      ("a12", "a(1,2)", 12), ("a22", "a(2,2)", 22),
                      ("a13", "a(1,3)", 13), ("a23", "a(2,3)", 23)]
        p.add("  checks=0\n")
        start = len(p.text)
        observations = [p.guard(name, expression, expected) for name, expression, expected in values]
        all_observations = [start, len(p.text)]
        total = p.guard("check-total", "checks", len(values), counter=None, category="completion")
        p.completion()
        p.add(f"end program data_position_{variant}_effect\n")
        plans = [("omit-observation-" + guard["id"], guard["block_span"], "", total) for guard in observations]
        plans += [("omit-all-observations", all_observations, "", total)]
        for name, span, replacement, failure in plans:
            omissions.append((name, span, replacement, failure))
        expected_counts = dict(value_checks=len(values), caller_checks=0)
    else:
        p.add(
            "  integer :: observed, entries, before_returns, returns, body_checks, after_data, checks\n"
            "  observed=-1\n  entries=0\n  before_returns=0\n  returns=0\n"
            "  body_checks=0\n  after_data=0\n  checks=0\n")
        call_span = p.add("  observed=read_kept()\n")
        p.add("  returns=returns+1\n")
        main_guards = []
        for name, expression, expected in (
                ("function-entries", "entries", 1), ("before-return-events", "before_returns", 1),
                ("normal-returns", "returns", 1), ("body-checks", "body_checks", 1),
                ("returned-value", "observed", 7), ("after-data-events", "after_data", 0)):
            main_guards.append(p.guard(name, expression, expected,
                                       category="value" if name == "returned-value" else "event"))
        total = p.guard("check-total", "checks", 6, counter=None, category="completion")
        p.completion()
        p.add("contains\n  integer function read_kept() result(value)\n    implicit none\n    integer :: kept\n")
        body_start = len(p.text)
        p.add("    entries=entries+1\n")
        direct = p.guard("local-initial-value", "kept", 7, counter="body_checks", indent="    ")
        p.add("    value=kept\n    before_returns=before_returns+1\n")
        return_span = p.add("    return\n")
        prefix_span = [body_start, len(p.text)]
        p.add("    data kept /7/\n    after_data=after_data+1\n"
              "  end function read_kept\nend program data_position_nonexecution_effect\n")
        omissions += [
            ("omit-function-call", call_span, "", main_guards[0]),
            ("defined-noop-function", prefix_span, "    value=-1\n    return\n", main_guards[0]),
            ("omit-explicit-return", return_span, "", main_guards[-1]),
            ("omit-local-observation", direct["block_span"], "", main_guards[3]),
        ]
        omissions += [("omit-caller-check-" + guard["id"], guard["block_span"], "", total)
                      for guard in main_guards]
        observations = [direct, main_guards[4]]
        expected_counts = dict(value_checks=1, caller_checks=6)
    plans = []
    for name, span, replacement, failure in omissions:
        start, end = span
        plans.append(dict(
            id=name, guard_id=failure["id"], kind="guard", category="omission", span=span,
            expected=p.text[start:end], replacement=replacement, line=p.text[:start].count("\n") + 1,
            guard_line=failure["line"], mutation="whole-program-omission",
            failure_token=failure["failure_token"], failure_stdout=failure["failure_stdout"]))
    for probe in p.probes + plans:
        start, end = probe["span"]
        if p.text[start:end] != probe["expected"]:
            raise ValueError("a DATA position mutation lost its complete-parent span")
    return dict(
        id=identifier(variant), variant=variant, facets=[VARIANTS[variant]],
        source=p.text, source_sha256=sha(p.text.encode("ascii")), completion=COMPLETIONS[variant],
        guards=p.guards, probes=p.probes, omissions=plans, observations=observations, **expected_counts)


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("data_position_effect_" + spec["variant"])
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
        raise ValueError("the selected DATA position definitions changed")
    owner = matches[0]
    if set(FACETS) & set(owner.get("positive_control_facets", [])):
        raise ValueError("the selected DATA position facets must remain effects")
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    oracle = owner.get("oracle", "").replace(
        "no fixture or connection is authored here.", "the original source-only packet authored no fixture or connection.")
    limitation = owner.get("oracle_limitation", "")
    if limitation.startswith("All facets remain pending. "):
        limitation = ("All facets were pending at the original source-only registration. "
                      + limitation[len("All facets remain pending. "):])
    owner["oracle"] = owned_paragraph(oracle, ORACLE_PREFIX, ORACLE)
    owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the DATA generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source review is recorded in batch073. All 185 facets remain PENDING.\n"
        "Source registration adds no Fortran program, fixture, compiler observation,\n"
        "source-use instance, canonical link or fixture approval. Its source of truth is",
        "The original source review is recorded in batch073. Current facet states\n"
        "remain in the catalogue, and source, fixture and inventory reviews stay\n"
        "separate. This generator grants or renews none. The source of truth is")
    before = before.replace(
        "evidence; syntax admission is not a substitute for those observations.",
        "evidence, not just syntax admission.\n"
        "The bounded implemented subset below does not complete the other plans.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Finite DATA position and initial-state effects\n\n"
        "Three complete run/effect/f2023 programs initialize actual default INTEGER\n"
        "variables once. One checks the distinct scalar values11/22/33 before any\n"
        "executable assignment to them, with three observations. Another initializes\n"
        "a(2,3) from11,21,12,22,13,23 and checks every coordinate against independent\n"
        "literals in Table9.1 order, with six observations and no reconstructed oracle.\n\n"
        "The third calls an internal INTEGER function whose explicitly declared\n"
        "local kept is directly checked and returned as7 before the physical\n"
        "DATA kept/7/ statement. Main checks entry, before-return, normal-return,\n"
        "local-check and result events plus zero execution of the ordinary action\n"
        "after DATA. Six caller checks precede exact completion. This tests initial\n"
        "definition, not executable DATA, a saved-lifetime effect or an undefined\n"
        "DATA-only host-shadowing case. B.3.5 obsolescent placement stays allowed.\n\n"
        "Every guard/completion has a complete-parent wrong-oracle plan. Separate\n"
        "omissions target observations with their counters, the actual call, a\n"
        "defined-result no-op function and the explicit RETURN. All DATA initializers\n"
        "survive every mutation; no undefined subject or function result is created.\n"
        "Current passing parents and intended runtime failures are necessary for\n"
        "sensitivity. Synthetic transports and f2018 supplementary observations do\n"
        "not become f2023 native qualification.\n\n"
        "Only three S8.6.7-004 facets and their bounded oracle text are generator-owned.\n"
        "The other18 owner facets, all foreign requirements and independently managed\n"
        "pending/control/raw-review state remain unchanged. No repeat/implied-DO,\n"
        "pointer/component/character/BOZ/profile, source-use or canonical-link credit\n"
        "is added. Generation supplies neither approval nor baseline changes.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the DATA position summary boundaries changed")
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
            raise ValueError("stale DATA position family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} DATA position cases, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
