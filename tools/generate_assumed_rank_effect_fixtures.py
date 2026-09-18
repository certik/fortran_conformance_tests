#!/usr/bin/env python3
"""Two ordinary assumed-rank observers and complete-program oracle mutations."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.5.8.7-001"
SECTION = "8.5.8.7"
CATALOGUE = "doc/catalogues/assumed_rank_8_5_8_7.json"
VIEW = "doc/fortran_2023_8_5_8_7.md"
FACETS = ("scalar-and-array-effective-ranks", "zero-size-array-rank")
COMPLETIONS = {
    "ordinary": "ASSUMED RANK ORDINARY OK\n",
    "zero_size": "ASSUMED RANK ZERO SIZE OK\n",
}
ORACLE_PREFIX = "S8.5.8.7-001 ordinary rank effect family: "
LIMIT_PREFIX = "S8.5.8.7-001 ordinary rank effect boundaries: "
ORACLE = ORACLE_PREFIX + (
    "two complete run/effect/f2023 programs use an internal explicit-interface observer with "
    "INTEGER INTENT(IN) x(..). Each observer obtains its result directly from RANK(x), never from "
    "a constructor, copied data object or fixed-rank observer. The ordinary program passes a defined "
    "named scalar, vector(3) and matrix(2,3) to the same observer with independent literal rank "
    "expectations0/1/2. The zero-size program passes named a(0) and b(0,3), expecting literal ranks1/2 "
    "without any element access. Present nonpointer/non-VALUE dummy and nonpointer actual entities "
    "are argument associated under15.5.2.4p3; that associated entity is the effective argument underp6. "
    "Each call checks rank and its independent visit ordinal, counts the actual observed rank category, "
    "and returns to an independently incremented caller counter. Final visit/category/return/observer-check "
    "and caller-check totals precede exact completion stdout, empty stderr and normal exit0. Full-parent "
    "one-span wrong-oracle probes target every guard, separately for each repeated observer activation, "
    "and each completion literal. Passing current parent plus the intended runtime guard or output failure "
    "is necessary for sensitivity credit."
)
LIMITATION = LIMIT_PREFIX + (
    "only scalar-and-array-effective-ranks and zero-size-array-rank are represented. Zero element count "
    "does not remove declared dimensions or make an array scalar.19.6.2's always-defined empty arrays "
    "are not a presence, allocation or pointer-association equivalence. Nonempty actuals and all counters "
    "are explicitly defined before use. No SIZE, SHAPE, LBOUND, UBOUND, payload, SELECT RANK, "
    "POINTER, ALLOCATABLE, OPTIONAL, assumed-size, assumed-type, polymorphism, coarray, C, "
    "CONTIGUOUS, VALUE, ASYNCHRONOUS or VOLATILE mechanism is used. No shape/bounds facet is "
    "claimed. The pointer-dummy/nonpointer-actual exception is not imported. Lexical double-dot, "
    "C714/C716 and finalization witnesses keep their original owners and positive-control/effect roles; "
    "no case is cloned or retagged as reuse. All unselected pending/control/review state remains "
    "independently managed. Compile/link failures, failed parents, preempting guards, crashes and "
    "resource/time failures cannot establish probe sensitivity; blocked plans remain explicit. Guard "
    "markers are program output, not mandated processor diagnostic wording or ERROR STOP exit codes. "
    "Runtime requirements are not weakened for unsupported processors. Source, fixture, native-mode "
    "and inventory adjudications remain distinct; no approval, baseline, link or SourceUses renewal is made."
)
SUMMARY_BEGIN = "<!-- BEGIN ASSUMED RANK EFFECTS -->"
SUMMARY_END = "<!-- END ASSUMED RANK EFFECTS -->"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    return "S8_5_8_7_001_valid__assumed_rank_effect_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.text = ""
        self.guards = []
        self.calls = []
        self.probes = []

    def add(self, text):
        self.text += text

    def call(self, actual, rank, visit):
        prefix = f"  call observe({actual}, "
        rank_start = len(self.text) + len(prefix)
        visit_start = rank_start + len(str(rank)) + 2
        line = self.text.count("\n") + 1
        self.calls.append(dict(
            actual=actual, rank=rank, visit=visit, line=line,
            rank_site=dict(span=[rank_start, rank_start + len(str(rank))], expected=str(rank), line=line),
            visit_site=dict(span=[visit_start, visit_start + len(str(visit))], expected=str(visit), line=line)))
        self.add(prefix + f"{rank}, {visit})\n  returns=returns+1\n")

    def guard(self, name, expression, expected, *, category="event", counter="main_checks", repeated=False):
        expected = str(expected)
        indent = "    " if repeated else "  "
        prefix = indent + f"if ({expression} /= "
        start = len(self.text) + len(prefix)
        token = f"ARE:{self.variant}:{name}"
        guard = dict(
            id=name, kind="guard", category=category, expression=expression, expected=expected,
            span=[start, start + len(expected)], line=self.text.count("\n") + 1,
            failure_token=token, counter=counter,
            activations=[call["visit"] for call in self.calls] if repeated else [None])
        self.guards.append(guard)
        self.add(prefix + expected + ") then\n")
        if repeated:
            self.add(indent + f"  write(*,'(a,i1)') '{token}:activation=', visits\n")
        else:
            self.add(indent + f"  write(*,'(a)') '{token}'\n")
        self.add(indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")
        if repeated:
            site_key = "rank_site" if category == "rank" else "visit_site"
            for call in self.calls:
                site = call[site_key]
                self.probes.append(dict(
                    id=name + f":activation-{call['visit']}", guard_id=name, kind="guard", category=category,
                    **site, replacement=str(int(site["expected"]) + 1), activation=call["visit"],
                    mutation="literal-actual-expectation", guard_line=guard["line"], failure_token=token,
                    failure_stdout=f"{token}:activation={call['visit']}\n"))
        else:
            self.probes.append(dict(
                id=name, guard_id=name, kind="guard", category=category, span=guard["span"],
                line=guard["line"], expected=expected, replacement=str(int(expected) + 1),
                activation=None, mutation="guard-literal-expectation", guard_line=guard["line"],
                failure_token=token, failure_stdout=token + "\n"))

    def completion(self):
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        guard = dict(
            id="completion-output", kind="output", category="completion", expected=literal,
            span=[start, start + len(literal)], line=self.text.count("\n") + 1, activations=[None], counter=None)
        self.guards.append(guard)
        self.probes.append(dict(
            guard, guard_id=guard["id"], activation=None, mutation="completion-literal",
            replacement=literal.replace(" OK", " BAD")))
        self.add(prefix + literal + "'\n")


def program(variant):
    ordinary = variant == "ordinary"
    p = Program(variant)
    calls = (("scalar", 0, 1), ("vector", 1, 2), ("matrix", 2, 3)) if ordinary else (
        ("a", 1, 1), ("b", 2, 2))
    categories = ((0, "scalar_visits"), (1, "rank_one_visits"), (2, "rank_two_visits")) if ordinary else (
        (1, "rank_one_visits"), (2, "rank_two_visits"))
    p.add(f"program assumed_rank_{variant}_effect\n  implicit none\n")
    p.add("  integer :: scalar, vector(3), matrix(2,3)\n" if ordinary else "  integer :: a(0), b(0,3)\n")
    p.add("  integer :: visits, returns, observer_checks, main_checks\n")
    p.add("  integer :: " + ", ".join(name for _, name in categories) + "\n")
    if ordinary:
        p.add("  scalar=11\n  vector=12\n  matrix=13\n")
    for name in ("visits", "returns", "observer_checks", "main_checks", *(name for _, name in categories)):
        p.add(f"  {name}=0\n")
    for actual, rank, visit in calls:
        p.call(actual, rank, visit)
    p.guard("total-visits", "visits", len(calls))
    for rank, name in categories:
        p.guard(f"category-{rank}", name, 1, category="category")
    p.guard("normal-returns", "returns", len(calls), category="return")
    p.guard("observer-checks", "observer_checks", 2 * len(calls), category="completion")
    main_checks = sum(guard["counter"] == "main_checks" for guard in p.guards)
    p.guard("caller-checks", "main_checks", main_checks, counter=None, category="completion")
    p.completion()
    p.add(
        "contains\n"
        "  subroutine observe(x, expected_rank, expected_visit)\n"
        "    implicit none\n"
        "    integer, intent(in) :: x(..)\n"
        "    integer, intent(in) :: expected_rank, expected_visit\n"
        "    integer :: observed_rank\n"
        "    visits=visits+1\n"
        "    observed_rank=rank(x)\n")
    p.guard("observer-rank", "observed_rank", "expected_rank", category="rank",
            counter="observer_checks", repeated=True)
    p.guard("observer-visit", "visits", "expected_visit", category="event",
            counter="observer_checks", repeated=True)
    p.add("    select case (observed_rank)\n")
    for rank, name in categories:
        p.add(f"    case ({rank})\n      {name}={name}+1\n")
    p.add("    end select\n  end subroutine observe\n" + f"end program assumed_rank_{variant}_effect\n")
    return p, main_checks


def source_specs():
    specs = {}
    for variant, facet in zip(("ordinary", "zero_size"), FACETS):
        p, main_checks = program(variant)
        raw = p.text.encode("ascii")
        for probe in p.probes:
            start, end = probe["span"]
            if raw[start:end].decode("ascii") != probe["expected"]:
                raise ValueError("a complete-parent oracle mutation lost its exact input span")
        name = identifier(variant)
        specs[name] = dict(
            id=name, variant=variant, facets=[facet], evidence="effect", standard="f2023", phase="run",
            source=p.text, source_sha256=sha(raw), calls=p.calls, guards=p.guards, probes=p.probes,
            completion=COMPLETIONS[variant], observer_checks=2 * len(p.calls), main_checks=main_checks)
    return specs


def wrong_oracle_source(spec, probe):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = probe["span"]
    if raw[start:end].decode("ascii") != probe["expected"]:
        raise ValueError("the wrong-oracle span does not bind the complete parent")
    return raw[:start] + probe["replacement"].encode("ascii") + raw[end:]


def probe_verdict(spec, probe, parent, observed, *, parent_binding_current):
    sys.path.insert(0, str(ROOT / "tests"))
    from run_tests import ProcessResult, failure

    def complete_run(check, source_hash):
        trace = check.get("trace", [])
        return (check.get("phase") == "run" and [step["phase"] for step in trace] == ["compile", "link", "run"]
                and check.get("input_hashes") == {"source.f90": source_hash}
                and all(step["returncode"] == 0 and not step["timed_out"] for step in trace[:2])
                and all(not failure(ProcessResult(step["returncode"], step["stdout"] + step["stderr"],
                                                  step["timed_out"]), step["phase"]) for step in trace))

    parent_passed = (parent_binding_current and parent.get("outcome") == "pass"
                     and complete_run(parent, spec["source_sha256"])
                     and parent["trace"][-1]["returncode"] == 0
                     and parent["trace"][-1]["stdout"] == spec["completion"]
                     and parent["trace"][-1]["stderr"] == "")
    if observed is None:
        return dict(status="UNTESTED", qualified=False, parent_passed=bool(parent_passed),
                    intended_failure=False, parent_preempted=False,
                    reason="No probe execution; retain the explicit blocking parent/plan.")
    intended = False
    if observed.get("outcome") == "fail" and complete_run(observed, sha(wrong_oracle_source(spec, probe))):
        terminal = observed["trace"][-1]
        if probe["kind"] == "output":
            intended = (terminal["returncode"] == 0 and terminal["stdout"] == probe["replacement"] + "\n"
                        and terminal["stderr"] == "")
        else:
            intended = (0 < terminal["returncode"] < 128 and terminal["stdout"] == probe["failure_stdout"])
    preempted = (not parent_passed and not intended and parent.get("outcome") == "fail"
                 and parent.get("phase") == observed.get("phase") == "run"
                 and complete_run(parent, spec["source_sha256"])
                 and complete_run(observed, sha(wrong_oracle_source(spec, probe)))
                 and bool(parent.get("trace")) and bool(observed.get("trace"))
                 and bool(parent["trace"][-1]["stdout"])
                 and parent["trace"][-1]["stdout"] == observed["trace"][-1]["stdout"])
    status = "sensitive" if parent_passed and intended else (
        "parent-preempted" if preempted else "unqualified-parent" if not parent_passed else "not-sensitive")
    return dict(status=status, qualified=bool(parent_passed and intended), parent_passed=bool(parent_passed),
                intended_failure=bool(intended), parent_preempted=bool(preempted),
                reason=("Current complete parent passes and the intended runtime oracle fails."
                        if parent_passed and intended else
                        "Parent/input binding, complete execution or intended runtime failure is not established."))


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = "tests/fixtures/assumed_rank_effect_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=spec["facets"], evidence="effect", standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"], spec["manifest"] = directory + "/fixture.json", manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n")
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned assumed-rank oracle paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    matches = [row for row in result["requirements"] if row["id"] == RULE]
    if len(matches) != 1 or not set(FACETS) <= set(matches[0]["facets"]):
        raise ValueError("the selected S8.5.8.7-001 facet definitions changed")
    requirement = matches[0]
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    requirement["oracle"] = owned_paragraph(requirement.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    requirement["oracle_limitation"] = owned_paragraph(requirement.get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    return result


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the assumed-rank native rendering boundary changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    anchor = "The catalogue is `doc/catalogues/assumed_rank_8_5_8_7.json`."
    if before.count(anchor) != 1:
        raise ValueError("the original assumed-rank source narrative boundary changed")
    narrative = anchor + before.split(anchor, 1)[1]
    if SUMMARY_BEGIN in narrative or SUMMARY_END in narrative:
        if narrative.count(SUMMARY_BEGIN) != 1 or narrative.count(SUMMARY_END) != 1:
            raise ValueError("the bounded assumed-rank summary boundary changed")
        leading, rest = narrative.split(SUMMARY_BEGIN)
        _, trailing = rest.split(SUMMARY_END)
        narrative = leading + trailing
    narrative = narrative.replace(
        "This packet adds no fixtures, compiler observations, profiles, approvals,",
        "The original batch047 source packet added no fixtures, compiler observations, profiles, approvals,")
    header = (
        "# Fortran 2023 8.5.8.7: Assumed-rank entity\n\n"
        "Original source review is recorded in batch047. Effective content-bound\n"
        'status is `Registry.catalogue_review_state("8.5.8.7")`, not a cached claim\n'
        "from the raw review field. Source, fixture and evidence approvals are\n"
        "separate; generation grants or renews none.\n\n")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Ordinary effective-rank observations\n\n"
        "Two complete run/effect programs use genuine internal explicit-interface\n"
        "`integer, intent(in) :: x(..)` observers and direct `RANK(x)`. One calls\n"
        "the same observer with a defined named scalar, vector and matrix and\n"
        "independent literal rank expectations 0, 1 and 2. The other passes\n"
        "named zero-sized `a(0)` and `b(0,3)` and expects ranks 1 and 2. Neither\n"
        "empty object becomes scalar; no payload or shape/size/bounds inquiry\n"
        "is performed. Ordinary argument association supplies the effective\n"
        "argument; no pointer-dummy exception is being used.\n\n"
        "Visit ordinals, actual rank-category counters, normal-return counters,\n"
        "observer/caller check totals and exact completion output reject missing\n"
        "calls or no-op paths. Each guard and each repeated activation has a\n"
        "one-span whole-parent wrong-oracle plan, as does each completion literal.\n"
        "Only a passing unchanged parent and the intended runtime failure can\n"
        "qualify sensitivity; preempted or build-blocked plans are not passes.\n\n"
        "Only the two selected S8.5.8.7-001 pending entries and bounded oracle\n"
        "paragraphs are generator-owned. All other pending/control/review state\n"
        "remains independently managed, without fixed remaining-pending counts.\n"
        "Existing lexical, C714/C716 and finalization witnesses retain their\n"
        "owners and roles. No new link, SourceUse, approval, baseline update or\n"
        "shape/bounds credit is supplied.\n" + SUMMARY_END + "\n\n")
    return (header + narrative.rstrip() + "\n\n" + summary + begin + "\n\n"
            + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale assumed-rank effect family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} assumed-rank runtime cases, "
          f"{len(FACETS)} facets and {sum(len(row['probes']) for row in specs.values())} full-program probes.")


if __name__ == "__main__":
    main()
