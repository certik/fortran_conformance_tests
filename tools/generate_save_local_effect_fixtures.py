#!/usr/bin/env python3
"""Two saved-local effects with independent values, lifecycle guards and full-parent probes."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, probe_verdict, sha, wrong_oracle_source


ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.5.16-001"
SECTION = "8.5.16"
CATALOGUE = "doc/catalogues/save_attribute_8_5_16.json"
VIEW = "doc/fortran_2023_8_5_16.md"
FACETS = ("return-defined-values", "shared-recursive-instances")
COMPLETIONS = {
    "return": "SAVE LOCAL RETURN OK\n",
    "recursive": "SAVE LOCAL RECURSIVE OK\n",
}
ORACLE_PREFIX = "S8.5.16-001 bounded saved-local effects: "
LIMIT_PREFIX = "S8.5.16-001 bounded saved-local limits: "
SUMMARY_BEGIN = "<!-- BEGIN SAVE LOCAL EFFECTS -->"
SUMMARY_END = "<!-- END SAVE LOCAL EFFECTS -->"
ORACLE = ORACLE_PREFIX + (
    "two complete run/effect/f2023 programs each declare one actual INTEGER,SAVE local kept, "
    "without a declaration initializer. The RETURN program calls the same internal explicit-interface "
    "subroutine in phases1/2/3: first define11 before any read and RETURN; next observe11, store17 "
    "and RETURN; finally observe17 and RETURN. Main independently checks literal snapshots11/17/17, "
    "entry and before-return events1/2/3, normal caller returns1/2/3, and local guard totals3/7/11. "
    "Fifteen main checks precede its completion check. The RECURSIVE program initializes kept=11 "
    "in the outer instance, enters the same subprogram again while the outer instance remains active, "
    "reads kept directly as11 in the inner instance, sets it to17 there, explicitly RETURNs and reads "
    "the actual kept directly as17 in the resumed outer instance. Ordinary exported snapshots11/11/17, "
    "two entries, two before-return events, one inner normal return, one outer normal return, twelve "
    "local checks and eight main checks have independent literal oracles. Phase/depth and entry "
    "expectations are separate literal dummy arguments; none is the saved object. Fallthrough beyond "
    "the explicit RETURN branches would poison the independently checked exit counter. A distinct unsaved "
    "activation ordinal identifies each dynamic guard failure, including the resumed outer frame. "
    "Every assertion guard, each repeated activation and both completion literals have one-span "
    "whole-program wrong-oracle probes. Exact completion stdout, empty stderr and normal exit0 "
    "are the parent run contract, not evidence inferred from compiler consensus."
)
LIMITATION = LIMIT_PREFIX + (
    "only return-defined-values and shared-recursive-instances are represented. The earlier source-only "
    "packet supplied plans, not these later fixture observations. All other pending facets, control "
    "designations, oracle paragraphs and raw source/case reviews remain independently managed. "
    "Neither program uses declaration/DATA initialization, pointers, allocatables, CHARACTER/PDT data, "
    "default initialization, BIND, COMMON, BLOCK, finalization, threads, coarrays or C. Scalar observer "
    "dummies have distinct ordinary actuals and are accessed through their dummy chain; kept is never "
    "passed as an aliased defining dummy or replaced by a copied-value proxy. No undefined saved value "
    "is read before first definition. Explicit RECURSIVE records intent; actual nested execution, not "
    "the advisory prefix or sequential calls alone, establishes the sharing witness. Existing S7 "
    "initialization/END contrasts, BIND-common effect and explicit-SAVE positive-control, S10 and "
    "finalization owners are unchanged and no link, retagging or control opt-in is created. Sensitivity "
    "requires a current passing complete parent and the intended runtime guard/output failure; failed "
    "parents, preemption, missing traces, build blockage, native failures and unrun plans never qualify. "
    "Markers are program output, not required processor ERROR STOP wording or a universal numeric "
    "termination status. Actual f2018 observations remain supplementary to f2023 qualification. "
    "Generation grants no approval and changes no baseline, index, evidence or inventory receipt."
)


def identifier(variant):
    if variant not in COMPLETIONS:
        raise ValueError("unknown saved-local effect variant")
    return "S8_5_16_001_valid__save_local_effect_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.text = ""
        self.calls = []
        self.guards = []

    def add(self, text):
        self.text += text

    def call(self, procedure, control, expected_control, expected_entry, actuals, *, indent="  ", continued=False):
        prefix = indent + f"call {procedure}({control}, "
        first = len(self.text) + len(prefix)
        second = first + len(str(expected_control)) + 2
        self.calls.append(dict(
            control=control, expected_control=expected_control, expected_entry=expected_entry,
            activation=expected_entry, line=self.text.count("\n") + 1,
            control_site=dict(span=[first, first + len(str(expected_control))],
                              expected=str(expected_control)),
            entry_site=dict(span=[second, second + len(str(expected_entry))],
                            expected=str(expected_entry))))
        tail = (", &\n" + indent + "           ").join(actuals) if continued else actuals[0]
        self.add(prefix + f"{expected_control}, {expected_entry}, " + tail + ")\n")

    def guard(self, name, expression, expected, *, indent="  ", counter="main_checks",
              activation=None, call_site=None, category="event"):
        expected = str(expected)
        prefix = indent + f"if ({expression} /= "
        start = len(self.text) + len(prefix)
        token = f"SLE:{self.variant}:{name}"
        self.guards.append(dict(
            id=name, kind="guard", category=category, expression=expression, expected=expected,
            span=[start, start + len(expected)], line=self.text.count("\n") + 1,
            counter=counter, activation=activation, call_site=call_site, failure_token=token))
        self.add(prefix + expected + ") then\n")
        if activation is not None or call_site is not None:
            self.add(indent + f"  write(*,'(a,i0)') '{token}:activation=', activation\n")
        else:
            self.add(indent + f"  write(*,'(a)') '{token}'\n")
        self.add(indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")

    def completion(self):
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        self.guards.append(dict(
            id="completion-output", kind="output", category="completion", expected=literal,
            span=[start, start + len(literal)], line=self.text.count("\n") + 1,
            counter=None, activation=None, call_site=None))
        self.add(prefix + literal + "'\n")

    def finish(self):
        probes = []
        for guard in self.guards:
            if guard["call_site"]:
                guard["activations"] = [call["activation"] for call in self.calls]
                for call in self.calls:
                    site = call[guard["call_site"] + "_site"]
                    probes.append(dict(
                        id=guard["id"] + f":activation-{call['activation']}", guard_id=guard["id"],
                        kind="guard", category=guard["category"], **site,
                        line=call["line"], guard_line=guard["line"], activation=call["activation"],
                        replacement=str(int(site["expected"]) + 1), mutation="literal-actual-expectation",
                        failure_token=guard["failure_token"],
                        failure_stdout=guard["failure_token"] + f":activation={call['activation']}\n"))
            else:
                guard["activations"] = [guard["activation"]]
                probe = dict(guard, guard_id=guard["id"], guard_line=guard["line"],
                             mutation="completion-literal" if guard["kind"] == "output" else "guard-literal-expectation",
                             replacement=guard["expected"].replace(" OK", " BAD") if guard["kind"] == "output"
                             else str(int(guard["expected"]) + 1))
                if guard["kind"] == "guard":
                    suffix = "" if guard["activation"] is None else f":activation={guard['activation']}"
                    probe["failure_stdout"] = guard["failure_token"] + suffix + "\n"
                probes.append(probe)
        if len({probe["id"] for probe in probes}) != len(probes):
            raise ValueError("duplicate saved-local probe ID")
        return dict(
            id=identifier(self.variant), variant=self.variant, source=self.text, source_sha256=sha(self.text.encode("ascii")),
            completion=COMPLETIONS[self.variant], guards=self.guards, probes=probes, calls=self.calls,
            facets=[FACETS[0] if self.variant == "return" else FACETS[1]])


def program(variant):
    p = Program(variant)
    if variant == "return":
        p.add(
            "program save_local_return_effect\n"
            "  implicit none\n"
            "  integer :: snapshot, entries, exits, returns, local_checks, main_checks\n"
            "  entries=0\n  exits=0\n  returns=0\n  local_checks=0\n  main_checks=0\n")
        for phase, value, checks in ((1, 11, 3), (2, 17, 7), (3, 17, 11)):
            p.add(f"  snapshot=-{phase}\n")
            p.call("visit", phase, phase, phase, ["snapshot, entries, exits, local_checks"])
            p.add("  returns=returns+1\n")
            for name, expression, expected in (
                ("entries", "entries", phase), ("exits", "exits", phase), ("returns", "returns", phase),
                ("snapshot", "snapshot", value), ("local-checks", "local_checks", checks)):
                p.guard(f"after-{phase}-{name}", expression, expected,
                        category="value" if name == "snapshot" else "event")
        p.guard("main-check-total", "main_checks", 15, counter=None, category="completion")
        p.completion()
        p.add(
            "contains\n"
            "  subroutine visit(phase, expected_phase, expected_entry, snapshot, entries, exits, checks)\n"
            "    implicit none\n"
            "    integer, intent(in) :: phase, expected_phase, expected_entry\n"
            "    integer, intent(out) :: snapshot\n"
            "    integer, intent(inout) :: entries, exits, checks\n"
            "    integer :: activation\n"
            "    integer, save :: kept\n"
            "    entries=entries+1\n"
            "    activation=entries\n")
        p.guard("phase", "phase", "expected_phase", indent="    ", counter="checks",
                call_site="control", category="phase")
        p.guard("entry", "entries", "expected_entry", indent="    ", counter="checks",
                call_site="entry", category="entry")
        p.add("    if (phase == 1) then\n      kept=11\n")
        p.guard("first-defined", "kept", 11, indent="      ", counter="checks", activation=1, category="value")
        p.add("      snapshot=kept\n      exits=exits+1\n      return\n    else if (phase == 2) then\n")
        p.guard("second-retained", "kept", 11, indent="      ", counter="checks", activation=2, category="value")
        p.add("      kept=17\n")
        p.guard("second-updated", "kept", 17, indent="      ", counter="checks", activation=2, category="value")
        p.add("      snapshot=kept\n      exits=exits+1\n      return\n    else\n")
        p.guard("last-phase", "phase", 3, indent="      ", counter="checks", activation=3, category="phase")
        p.guard("third-retained", "kept", 17, indent="      ", counter="checks", activation=3, category="value")
        p.add(
            "      snapshot=kept\n      exits=exits+1\n      return\n"
            "    end if\n"
            "    exits=exits+1\n"
            "  end subroutine visit\n"
            "end program save_local_return_effect\n")
    elif variant == "recursive":
        p.add(
            "program save_local_recursive_effect\n"
            "  implicit none\n"
            "  integer :: before_snapshot, inner_snapshot, after_snapshot\n"
            "  integer :: entries, exits, child_returns, returns, local_checks, main_checks\n"
            "  before_snapshot=-1\n  inner_snapshot=-2\n  after_snapshot=-3\n"
            "  entries=0\n  exits=0\n  child_returns=0\n  returns=0\n  local_checks=0\n  main_checks=0\n")
        actuals = ["before_snapshot, inner_snapshot, after_snapshot", "entries, exits, child_returns, local_checks"]
        p.call("share", 0, 0, 1, actuals, continued=True)
        p.add("  returns=returns+1\n")
        for name, expression, expected in (
            ("entries", "entries", 2), ("exits", "exits", 2), ("child-returns", "child_returns", 1),
            ("outer-returns", "returns", 1), ("before-snapshot", "before_snapshot", 11),
            ("inner-snapshot", "inner_snapshot", 11), ("after-snapshot", "after_snapshot", 17),
            ("local-checks", "local_checks", 12)):
            p.guard("caller-" + name, expression, expected, category="value" if "snapshot" in name else "event")
        p.guard("main-check-total", "main_checks", 8, counter=None, category="completion")
        p.completion()
        p.add(
            "contains\n"
            "  recursive subroutine share(depth, expected_depth, expected_entry, before_snapshot, &\n"
            "                             inner_snapshot, after_snapshot, entries, exits, child_returns, checks)\n"
            "    implicit none\n"
            "    integer, intent(in) :: depth, expected_depth, expected_entry\n"
            "    integer, intent(inout) :: before_snapshot, inner_snapshot, after_snapshot\n"
            "    integer, intent(inout) :: entries, exits, child_returns, checks\n"
            "    integer :: activation\n"
            "    integer, save :: kept\n"
            "    entries=entries+1\n"
            "    activation=entries\n")
        p.guard("depth", "depth", "expected_depth", indent="    ", counter="checks",
                call_site="control", category="depth")
        p.guard("entry", "entries", "expected_entry", indent="    ", counter="checks",
                call_site="entry", category="entry")
        p.add("    if (depth == 0) then\n      kept=11\n")
        p.guard("outer-defined", "kept", 11, indent="      ", counter="checks", activation=1, category="value")
        p.add("      before_snapshot=kept\n")
        p.call("share", 1, 1, 2,
               ["before_snapshot, inner_snapshot, after_snapshot", "entries, exits, child_returns, checks"],
               indent="      ", continued=True)
        p.add("      child_returns=child_returns+1\n")
        p.guard("inner-return", "child_returns", 1, indent="      ", counter="checks", activation=1, category="return")
        p.guard("outer-resumed-entries", "entries", 2, indent="      ", counter="checks", activation=1, category="entry")
        p.guard("inner-exit", "exits", 1, indent="      ", counter="checks", activation=1, category="return")
        p.guard("outer-shared", "kept", 17, indent="      ", counter="checks", activation=1, category="value")
        p.add("      after_snapshot=kept\n      exits=exits+1\n      return\n    else\n")
        p.guard("inner-depth", "depth", 1, indent="      ", counter="checks", activation=2, category="depth")
        p.guard("inner-shared", "kept", 11, indent="      ", counter="checks", activation=2, category="value")
        p.add("      inner_snapshot=kept\n      kept=17\n")
        p.guard("inner-updated", "kept", 17, indent="      ", counter="checks", activation=2, category="value")
        p.add(
            "      exits=exits+1\n      return\n"
            "    end if\n"
            "    exits=exits+1\n"
            "  end subroutine share\n"
            "end program save_local_recursive_effect\n")
    else:
        raise ValueError("unknown saved-local effect variant")
    return p.finish()


def source_specs():
    return {identifier(variant): program(variant) for variant in COMPLETIONS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("save_local_effect_" + spec["variant"])
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
        raise ValueError("the selected saved-local effect definitions changed")
    owner = matches[0]
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the SAVE generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "**Unapproved source-only draft. All 32 new facets are PENDING.**\n"
        "This catalogue supplies finite plans, not new fixtures, compiler\n"
        "observations, approvals, canonical links or baseline changes.",
        'Original source review is recorded in batch061. Effective content-bound\n'
        'status is `Registry.catalogue_review_state("8.5.16")`, not a cached\n'
        "claim from the raw source record. Source, fixture and inventory reviews\n"
        "remain separate; this generator grants or renews none.")
    before = before.replace(
        "The initial effect designs use explicitly saved local data variables,",
        "The original source-only effect plans use explicitly saved local data variables,")
    before = before.replace(
        "[11,13]/[17,19] for nonempty allocation data; these are proposals, not\nmeasurements.",
        "[11,13]/[17,19] for nonempty allocation data; those broader plans are not\n"
        "completed by the bounded saved-scalar family below.")
    after = after.replace(
        "Across this packet's two sections there are **15 original units and\n"
        "80 fine units**, with **12 requirements and 90 pending facets**.",
        "The original PROTECTED/SAVE source packet accounted for **15 original\n"
        "units and 80 fine units** in **12 requirements**. Current implementation\n"
        "and pending states follow the independently managed catalogue data.")
    after = after.replace(
        "The local validation index appends only these two catalogues and remains\nuncommitted.",
        "The source catalogues are already registered in this fixture packet's base;\n"
        "no validation-index overlay or index change is supplied here.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Bounded saved-scalar RETURN and active-recursion effects\n\n"
        "Two complete run/effect/f2023 programs use actual `integer, save :: kept`\n"
        "locals without declaration initializers. The RETURN program defines11,\n"
        "returns, observes11 and stores17, returns, then observes17 and returns.\n"
        "Independent main snapshots11/17/17, three entry/exit/normal-return\n"
        "events, eleven local checks and fifteen caller checks precede completion.\n\n"
        "Falling through beyond the explicit RETURN branches would add an extra\n"
        "exit event, rejected by the independent caller or resumed-outer checks.\n\n"
        "The explicitly RECURSIVE program defines11 in the outer instance. While\n"
        "that instance is still active, the inner invocation reads the actual\n"
        "saved local as11 and sets it to17; the resumed outer invocation reads\n"
        "that same saved local as17. Main consumes snapshots11/11/17, two entries\n"
        "and exit events, an inner and outer normal return, twelve local checks\n"
        "and eight caller checks. The snapshots and counters are separate ordinary\n"
        "dummies; the saved object is never passed as an aliased defining actual.\n\n"
        "Every runtime assertion, repeated activation and completion literal has\n"
        "a single-span complete-program wrong-oracle plan. Only a current passing\n"
        "parent and its intended runtime failure qualify sensitivity. Native\n"
        "failures, preempted guards, build-blocked or unrun plans remain explicit.\n"
        "Synthetic transports are not compiler observations, and f2018 remains\n"
        "supplementary to f2023 reference qualification.\n\n"
        "Only the two selected S8.5.16-001 pending entries and the bounded oracle\n"
        "paragraphs are generator-owned. Unselected pending/control/raw-review\n"
        "states, other source owners and all old cases remain independent.\n"
        "There is no pointer/allocation/BLOCK/finalization/default-initialization,\n"
        "BIND/common, thread, C or coarray effect, copied-value substitute, address\n"
        "oracle, new canonical link, role opt-in, approval or baseline change.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the saved-local summary boundaries changed")
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
            raise ValueError("stale saved-local effect family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} saved-local runtime cases, "
          f"{len(FACETS)} facets and {sum(len(row['probes']) for row in specs.values())} whole-program probes.")


if __name__ == "__main__":
    main()
