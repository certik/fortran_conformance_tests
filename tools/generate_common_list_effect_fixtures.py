#!/usr/bin/env python3
"""Four COMMON list effects with protected seeding and complete-parent sensitivity."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import (
    probe_verdict as ordinary_probe_verdict,
    sha,
    wrong_oracle_source as replace_source_span,
)


ROOT = Path(__file__).resolve().parents[1]
RULE, SECTION = "S8.10.2.1-001", "8.10.2.1"
CATALOGUE = "doc/catalogues/common_statement_8_10_2_1.json"
VIEW = "doc/fortran_2023_8_10_2_1.md"
VARIANTS = {
    "named_single": "named-one-statement",
    "named_multiple": "named-multiple-statements",
    "blank": "blank-spelling-continuation",
    "interleaved": "interleaved-distinct-blocks",
}
FACETS = tuple(VARIANTS.values())
COMPLETIONS = {variant: "COMMON LIST " + variant.upper() + " OK\n" for variant in VARIANTS}
SUMMARY_BEGIN = "<!-- BEGIN COMMON LIST EFFECTS -->"
SUMMARY_END = "<!-- END COMMON LIST EFFECTS -->"
STALE_SENTENCES = (
    ("oracle",
     "No such program or mutation has been implemented here.",
     "Four complete programs and their whole-program mutations now implement exactly the"
     " four ordered-list facets named above; every other plan under this requirement"
     " remains unimplemented.",
     ("complete programs", "ordered-list facets named above", "remains unimplemented")),
    ("oracle_limitation",
     "All proposed evidence remains PENDING. No case, direct/linked facet, SourceUse"
     " relationship, inventory renewal, source approval, baseline change or universal"
     " conformance credit is created.",
     "Only the four named ordered-list facets are represented by cases; every other"
     " proposed effect under this requirement remains PENDING. Those four cases create no"
     " linked facet, SourceUse relationship, inventory renewal, source approval, baseline"
     " change or universal conformance credit.",
     ("ordered-list facets are represented by cases", "Those four cases create no")),
)


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown COMMON list variant")
    return "S8_10_2_1_001_valid__common_list_effect_" + variant


class Program:
    def __init__(self, variant):
        self.variant, self.text = variant, ""
        self.guards, self.probes = [], []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def guard(self, name, expression, expected, *, counter="caller_checks", category="event"):
        expected = str(expected)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"CLE:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=str(int(expected) + 1), span=[start, start + len(expected)],
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


def view_declarations(variant, seed=False):
    if variant == "interleaved":
        left, right = ("seed_left", "seed_right") if seed else ("left_view", "right_view")
        return (
            f"  integer :: {left}(2), {right}(2)\n"
            f"  common /left_block/ {left}\n  common /right_block/ {right}\n"
            "  save /left_block/\n  save /right_block/\n")
    name = "seed_values" if seed else "view"
    block = "//" if variant == "blank" else "/packet/"
    return f"  integer :: {name}(4)\n  common {block} {name}\n" + (
        "" if variant == "blank" else "  save /packet/\n")


def program(variant):
    identifier(variant)
    p = Program(variant)
    p.add(
        f"program common_list_{variant}_effect\n  implicit none\n"
        "  integer :: seed_entries, seed_writes, seed_returns\n"
        "  integer :: writer_entries, writer_writes, writer_returns\n"
        "  integer :: reader_entries, reader_checks, reader_returns, caller_checks\n"
        "  external :: seed_common, write_common, read_common\n"
        "  seed_entries=0\n  seed_writes=0\n  seed_returns=0\n"
        "  writer_entries=0\n  writer_writes=0\n  writer_returns=0\n"
        "  reader_entries=0\n  reader_checks=0\n  reader_returns=0\n  caller_checks=0\n")
    seed_call = p.add("  call seed_common(seed_entries, seed_writes)\n")
    p.add("  seed_returns=seed_returns+1\n")
    caller_guards = []
    for name, expression, expected in (
            ("seed-entries", "seed_entries", 1), ("seed-writes", "seed_writes", 4),
            ("seed-returns", "seed_returns", 1)):
        caller_guards.append(p.guard(name, expression, expected))
    writer_call = p.add("  call write_common(writer_entries, writer_writes)\n")
    writer_return = p.add("  writer_returns=writer_returns+1\n")
    for name, expression, expected in (
            ("writer-entries", "writer_entries", 1), ("writer-writes", "writer_writes", 4),
            ("writer-returns", "writer_returns", 1)):
        caller_guards.append(p.guard(name, expression, expected))
    reader_call = p.add("  call read_common(reader_entries, reader_checks)\n")
    reader_return = p.add("  reader_returns=reader_returns+1\n")
    for name, expression, expected in (
            ("reader-entries", "reader_entries", 1), ("reader-checks", "reader_checks", 4),
            ("reader-returns", "reader_returns", 1)):
        caller_guards.append(p.guard(name, expression, expected))
    total = p.guard("caller-check-total", "caller_checks", 9, counter=None, category="completion")
    completion = p.completion()
    p.add(f"end program common_list_{variant}_effect\n\n")

    seed_start = len(p.text)
    p.add("subroutine seed_common(entries, writes)\n  implicit none\n"
          "  integer, intent(inout) :: entries, writes\n" + view_declarations(variant, seed=True)
          + "  entries=entries+1\n")
    seeds = ([("seed_left(1)", -101), ("seed_left(2)", -102),
              ("seed_right(1)", -103), ("seed_right(2)", -104)] if variant == "interleaved" else
             [("seed_values(1)", -101), ("seed_values(2)", -102),
              ("seed_values(3)", -103), ("seed_values(4)", -104)])
    for expression, value in seeds:
        p.add(f"  {expression}={value}\n  writes=writes+1\n")
    p.add("  return\nend subroutine seed_common\n")
    seed_procedure = [seed_start, len(p.text)]

    p.add("\nsubroutine write_common(entries, writes)\n  implicit none\n"
          "  integer, intent(inout) :: entries, writes\n")
    if variant == "interleaved":
        p.add("  integer :: a, b, x, y\n"
              "  common /left_block/ a\n  common /right_block/ x\n"
              "  common /left_block/ b\n  common /right_block/ y\n"
              "  save /left_block/\n  save /right_block/\n")
        assignments = [("a", 11, "left-1"), ("x", 33, "right-1"),
                       ("b", 22, "left-2"), ("y", 44, "right-2")]
    else:
        p.add("  integer :: a, b, c, d\n")
        common = {
            "named_single": "  common /packet/ a, b /packet/ c, d\n",
            "named_multiple": "  common /packet/ a, b\n  common /packet/ c, d\n",
            "blank": "  common a, b\n  common // c, d\n",
        }
        p.add(common[variant])
        if variant != "blank":
            p.add("  save /packet/\n")
        assignments = [("a", 11, "position-1"), ("b", 22, "position-2"),
                       ("c", 33, "position-3"), ("d", 44, "position-4")]
    writer_start = len(p.text)
    p.add("  entries=entries+1\n")
    writes_start = len(p.text)
    writer_operations = []
    for expression, value, observation in assignments:
        span = p.add(f"  {expression}={value}\n")
        p.add("  writes=writes+1\n")
        writer_operations.append(dict(expression=expression, value=value, span=span, observation=observation))
    writer_body, all_writes = [writer_start, len(p.text)], [writes_start, len(p.text)]
    p.add("  return\nend subroutine write_common\n")

    p.add("\nsubroutine read_common(entries, checks)\n  implicit none\n"
          "  integer, intent(inout) :: entries, checks\n" + view_declarations(variant))
    reader_start = len(p.text)
    p.add("  entries=entries+1\n")
    observations_start = len(p.text)
    # These ordered literal oracles are independent of the writer assignment list.
    expected = ([("left-1", "left_view(1)", 11), ("left-2", "left_view(2)", 22),
                 ("right-1", "right_view(1)", 33), ("right-2", "right_view(2)", 44)]
                if variant == "interleaved" else
                [("position-1", "view(1)", 11), ("position-2", "view(2)", 22),
                 ("position-3", "view(3)", 33), ("position-4", "view(4)", 44)])
    observations = [p.guard(name, expression, value, counter="checks", category="value")
                    for name, expression, value in expected]
    reader_body = [reader_start, len(p.text)]
    all_observations = [observations_start, len(p.text)]
    p.add("  return\nend subroutine read_common\n")
    by_id = {g["id"]: g for g in p.guards}
    extra = dict(observations[0], id="wrong-position-order", category="order", replacement="22",
                 mutation="wrong-position-literal")
    p.probes.append(extra)
    if variant == "interleaved":
        p.probes.append(dict(observations[0], id="wrong-block-value", category="block", replacement="33",
                             mutation="wrong-block-literal"))
    omissions = [
        ("omit-writer-call", writer_call, by_id["writer-entries"]),
        ("omit-reader-call", reader_call, by_id["reader-entries"]),
        ("noop-writer-body", writer_body, by_id["writer-entries"]),
        ("noop-reader-body", reader_body, by_id["reader-entries"]),
        ("omit-all-writes", all_writes, by_id["writer-writes"]),
        ("omit-all-reader-checks", all_observations, by_id["reader-checks"]),
        ("omit-writer-return-count", writer_return, by_id["writer-returns"]),
        ("omit-reader-return-count", reader_return, by_id["reader-returns"]),
    ]
    omissions += [("omit-write-" + row["expression"], row["span"], by_id[row["observation"]])
                  for row in writer_operations]
    omissions += [("omit-reader-check-" + g["id"], g["block_span"], by_id["reader-checks"])
                  for g in observations]
    omissions += [("omit-caller-check-" + g["id"], g["block_span"], total) for g in caller_guards]
    plans = []
    for name, span, failure in omissions:
        start, end = span
        plans.append(dict(
            id=name, guard_id=failure["id"], kind="guard", category="omission", span=span,
            expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
            guard_line=failure["line"], mutation="whole-program-omission",
            failure_token=failure["failure_token"], failure_stdout=failure["failure_stdout"]))
    start, end = completion["block_span"]
    plans.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        span=[start, end], expected=p.text[start:end], replacement="", line=p.text[:start].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    spec = dict(
        id=identifier(variant), variant=variant, facets=[VARIANTS[variant]],
        evidence="effect", standard="f2023", phase="run",
        source=p.text, source_sha256=sha(p.text.encode("ascii")), completion=COMPLETIONS[variant],
        guards=p.guards, probes=p.probes, omissions=plans, observations=observations,
        writer_operations=writer_operations,
        seed_assignments=[dict(expression=expression, value=value) for expression, value in seeds],
        protected_spans=[seed_call, seed_procedure], seed_call=seed_call, seed_procedure=seed_procedure,
        calls=dict(seed=seed_call, writer=writer_call, reader=reader_call),
        expected_counts=dict(seed_entries=1, seed_writes=4, seed_returns=1,
                             writer_entries=1, writer_writes=4, writer_returns=1,
                             reader_entries=1, reader_checks=4, reader_returns=1, caller_checks=9))
    for probe in spec["probes"] + spec["omissions"]:
        wrong_oracle_source(spec, probe)
    return spec


def wrong_oracle_source(spec, probe):
    start, end = probe["span"]
    if any(start < last and end > first for first, last in spec["protected_spans"]):
        raise ValueError("a COMMON mutation must preserve the protected seed stage")
    return replace_source_span(spec, probe)


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


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("common_list_effect_" + spec["variant"])
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
    result = copy.deepcopy(catalogue)
    matches = [r for r in result["requirements"] if r["id"] == RULE]
    if len(matches) != 1 or set(matches[0]["facets"]) != set(FACETS):
        raise ValueError("the selected COMMON list definitions changed")
    owner = matches[0]
    if owner["category"] != "effect" or owner.get("positive_control_facets"):
        raise ValueError("the selected COMMON list facets must remain runtime effects")
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    for field, stale, current, anchors in STALE_SENTENCES:
        text = owner[field]
        present, inherited = text.count(current), text.count(stale)
        if any(text.count(anchor) != present for anchor in anchors):
            raise ValueError("the inherited COMMON " + field + " wording changed")
        if present == 1 and inherited == 0:
            continue
        if inherited != 1 or present != 0:
            raise ValueError("the inherited COMMON " + field + " wording changed")
        owner[field] = text.replace(stale, current)
    return result


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the COMMON generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "This source-only packet introduces 56 pending facets and no cases.",
        "The original source-only registration introduced56 pending facets and no cases.\n"
        "Current facet accounting is authoritative in the catalogue; source, case and\n"
        "execution-inventory reviews remain separate.")
    before = before.replace(
        "No compiler was invoked for this source packet.",
        "No compiler was invoked for the original source-only registration.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Four bounded ordered-list runtime fixtures\n\n"
        "Four complete run/effect/f2023 programs represent only the four S8.10.2.1-001\n"
        "facets. Their drivers declare no COMMON. Ordinary external seed, writer and\n"
        "reader procedures have matching complete default-INTEGER storage sequences.\n"
        "Named blocks have SAVE /block/ in every declaring procedure. The blank case\n"
        "has no SAVE, DATA or declaration initialization; its nonpointer objects retain\n"
        "defined values across returns under8.10.2.5/19.6.6.\n\n"
        "A separately called and counted seed defines all observed positions to\n"
        "-101/-102/-103/-104 before the writer. Seeding survives every mutation.\n"
        "The writer uses repeated /packet/ groups in one statement, repeated named\n"
        "statements, omitted-name plus // blank continuation, or four interleaved\n"
        "/left_block/ and /right_block/ statements. Readers check each actual COMMON\n"
        "coordinate against independent11/22/33/44 literals: one four-element tuple\n"
        "or separate left11/22 and right33/44 tuples, never a commutative sum.\n\n"
        "Control arguments are distinct initialized driver scalars, never COMMON\n"
        "members. Seed/writer/reader entries, four writes/observations and normal\n"
        "returns are guarded; nine counted caller checks precede exact externally\n"
        "checked completion, empty runtime stderr and exit0. A missing writer or\n"
        "no-op body is caught before the reader. Individual omitted writes leave\n"
        "defined sentinels, so value-guard failures do not read undefined storage.\n\n"
        "Full-parent sensitivity covers every assertion, wrong order/block values,\n"
        "individual writes/observations, body/call/return-count omissions, caller\n"
        "checks and wrong or absent completion. Completion mismatches can correctly\n"
        "fail with exit0. Failed or stale parents, incomplete traces, internal/resource\n"
        "failures and preempting guards never qualify. F2018 remains supplementary.\n\n"
        "The generator removes the four selected pending entries and replaces the two\n"
        "inherited sentences that said no program or mutation existed. All other\n"
        "requirement fields, including the original source plans of the113 unrepresented\n"
        "facets, remain exact. No source/case/inventory approval, link, SourceUse,\n"
        "baseline update or byte-layout/representation credit is supplied.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the COMMON effect-summary boundaries changed")
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
        stale = [p.relative_to(root).as_posix() for p, raw in files.items()
                 if not p.is_file() or p.read_bytes() != raw]
        if updated != catalogue:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale COMMON list family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} COMMON list cases, "
          f"{sum(len(s['probes']) for s in specs.values())} wrong-oracle and "
          f"{sum(len(s['omissions']) for s in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
