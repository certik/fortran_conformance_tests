#!/usr/bin/env python3
"""Two complete named-local explicit-array bound capture programs, not descriptor proxies."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.5.8.2-005"
SECTION = "8.5.8.2"
CATALOGUE = "doc/catalogues/explicit_shape_8_5_8_2.json"
VIEW = "doc/fortran_2023_8_5_8_2.md"
FACETS = ("procedure-entry", "post-redefinition", "post-undefinition",
          "block-entry", "fresh-entries", "nested-blocks")
COMPLETIONS = {
    "procedure": "EXPLICIT PROCEDURE BOUNDS OK\n",
    "blocks": "EXPLICIT BLOCK BOUNDS OK\n",
}
ORACLE = (
    "Two complete run/effect/f2023 programs implement only the first six facets. The procedure case declares "
    "an ordinary unsaved local INTEGER a(-2:n) after its nonoptional INTEGER INTENT(INOUT) n. Calls with "
    "incoming n=3 and n=1 supply independent scalar literal upper/extent/value expectations3/6/101 and1/4/102. "
    "The payload is assigned100+visit before inquiry. Each activation checks the actual whole array with "
    "LBOUND, UBOUND, SIZE, SHAPE and all-element value comparisons, first on entry, then after n=0, then "
    "after a separate plain INTEGER INTENT(OUT) helper leaves only n undefined and increments its distinct "
    "initialized event counter. No read of n occurs in that last window; n is restored from the independent "
    "upper expectation before return and checked again by main. Entry, change, undefinition, return and "
    "twenty-procedure-check-per-entry counts are independently consumed. The BLOCK case executes the same "
    "outer BLOCK twice with n=3/1, then takes nested inner bounds1:5/1:2 after redefining the host source. "
    "Distinct defined payloads201/202 and301/302, both arrays' actual bounds/shape/size, redefinition to9, "
    "inner exit and outer lifetime are checked with independent literal branch expectations. Main declares "
    "no array. Entry/exit/event/check counters and exact completion stdout, empty stderr and normal exit0 "
    "reject early-success/no-op behavior. Full-program one-span wrong-oracle probes address every guard, "
    "each repeated activation separately, and both completion literals, only on processors that execute "
    "the current complete parent."
)
LIMITATION = (
    "Vector-bound-capture stays pending, and all twelve other explicit-shape requirements retain their "
    "source, plans and reviews. These are scalar R815-R817 bounds, not vector-bound syntax or copied "
    "S8.3 CHARACTER/type-parameter cases. The arrays are real named procedure/BLOCK locals, never array "
    "dummies, constructor RANK arguments, second expected descriptors, fixed destinations, allocatables, "
    "pointers, coarrays, COMMON/EQUIVALENCE objects or C interop storage. No SAVE, declaration/DATA/default "
    "initialization or escaped object masks their lifetime. Every payload is defined before inspection; "
    "only scalar independent observer inputs or literal branch expectations are used. The OUT helper "
    "neither reads nor defines the bound-source integer; all other actuals are distinct and defined, and "
    "restoration precedes the caller's next read. Inner arrays are never referenced after END BLOCK. "
    "Nonzero extents6/4 and5/2 make the whole-array inquiry bounds literal rather than zero-extent "
    "normalization cases. Runtime sensitivity requires completed builds, actual runtime and the intended "
    "unique guard/output failure; a compile rejection, unsupported facility, resource failure or crash "
    "is not a successful probe. ERROR STOP status/token behavior is empirically qualified, not a universal "
    "printed-code or numeric-status requirement. Source, fixture, native mode qualification and inventory "
    "adjudication remain separate; no approval, baseline, source-use or canonical-link renewal is added."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    return "S8_5_8_2_005_valid__explicit_bound_capture_" + variant


class Program:
    def __init__(self):
        self.text = ""
        self.guards = []

    def add(self, text):
        self.text += text

    def guard(self, name, expression, expected, *, kind="scalar", category="event",
              indent="  ", counter="checks", repeat=None):
        expected = str(expected)
        if kind == "vector":
            left, right = f"any({expression} /= [", "])"
        elif kind == "elements":
            left, right = f"any({expression} /= ", ")"
        else:
            left, right = f"{expression} /= ", ""
        prefix = indent + "if (" + left
        start = len(self.text) + len(prefix)
        condition = f"{prefix}{expected}{right})"
        if repeat:
            line = (condition + " then\n"
                    + indent + f"  write(*,'(a,i1)') 'EBC:{name}:activation=', {repeat}\n"
                    + indent + f"  error stop 'EBC:{name}'\n"
                    + indent + "end if\n")
        else:
            line = condition + f" error stop 'EBC:{name}'\n"
        self.guards.append(dict(
            id=name, expression=expression, expected=expected, kind="guard", comparison=kind,
            category=category, span=[start, start + len(expected)], line=self.text.count("\n") + 1,
            failure_token="EBC:" + name, repeat=repeat, counter=counter,
            activation_output_prefix=f"EBC:{name}:activation=" if repeat else None))
        self.add(line)
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")

    def array(self, prefix, name, lower, upper, extent, value, *, indent="    ", repeat="visit"):
        self.guard(prefix + "-lower", f"lbound({name},1)", lower, category="lower", indent=indent, repeat=repeat)
        self.guard(prefix + "-upper", f"ubound({name},1)", upper, category="upper", indent=indent, repeat=repeat)
        self.guard(prefix + "-size", f"size({name})", extent, category="size", indent=indent, repeat=repeat)
        self.guard(prefix + "-shape", f"shape({name})", extent, kind="vector", category="shape", indent=indent, repeat=repeat)
        self.guard(prefix + "-values", name, value, kind="elements", category="values", indent=indent, repeat=repeat)

    def completion(self, variant):
        literal = COMPLETIONS[variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        self.guards.append(dict(id=variant + "-output", expected=literal, kind="output",
                                span=[start, start + len(literal)], line=self.text.count("\n") + 1,
                                repeat=None, category="completion", counter=None))
        self.add(prefix + literal + "'\n")


def procedure_program():
    p = Program()
    p.add(
        "program explicit_procedure_bounds\n"
        "  implicit none\n"
        "  integer :: n, entries, changes, undefined_events, checks, returns, main_checks\n"
        "  entries=0\n  changes=0\n  undefined_events=0\n  checks=0\n  returns=0\n  main_checks=0\n")
    for visit, upper, extent, payload in ((1, 3, 6, 101), (2, 1, 4, 102)):
        p.add(f"  n={upper}\n"
              f"  call capture(n, {visit}, {upper}, {extent}, {payload}, entries, changes, undefined_events, checks)\n"
              "  returns=returns+1\n")
        for label, expression, expected in (
                ("restored", "n", upper), ("entries", "entries", visit), ("changes", "changes", visit),
                ("undefined-events", "undefined_events", visit), ("returns", "returns", visit),
                ("procedure-checks", "checks", 20 * visit)):
            p.guard(f"caller-{visit}-{label}", expression, expected, counter="main_checks",
                    category="completion" if label == "procedure-checks" else "event")
    p.guard("caller-check-total", "main_checks", 12, counter=None, category="completion")
    p.completion("procedure")
    p.add(
        "contains\n"
        "  subroutine capture(n, visit, upper_expected, extent_expected, value_expected, &\n"
        "                     entries, changes, undefined_events, checks)\n"
        "    integer, intent(inout) :: n, entries, changes, undefined_events, checks\n"
        "    integer, intent(in) :: visit, upper_expected, extent_expected, value_expected\n"
        "    integer :: a(-2:n)\n"
        "    a=100+visit\n"
        "    entries=entries+1\n")
    first = len(p.guards)
    p.guard("procedure-entry", "entries", "visit", indent="    ", repeat="visit", category="entry")
    p.array("procedure-initial", "a", "-2", "upper_expected", "extent_expected", "value_expected")
    p.add("    n=0\n    changes=changes+1\n")
    p.guard("procedure-change", "changes", "visit", indent="    ", repeat="visit")
    p.guard("procedure-source-zero", "n", "0", indent="    ", repeat="visit")
    p.array("procedure-redefined", "a", "-2", "upper_expected", "extent_expected", "value_expected")
    p.add("    call make_undefined(n, undefined_events)\n")
    p.guard("procedure-undefinition-event", "undefined_events", "visit", indent="    ", repeat="visit")
    p.array("procedure-undefined-source", "a", "-2", "upper_expected", "extent_expected", "value_expected")
    p.add("    n=upper_expected\n")
    p.guard("procedure-restored", "n", "upper_expected", indent="    ", repeat="visit")
    if len(p.guards) - first != 20:
        raise ValueError("the explicit twenty-check-per-procedure oracle needs source review")
    p.add(
        "  end subroutine capture\n"
        "  subroutine make_undefined(value, event_count)\n"
        "    integer, intent(out) :: value\n"
        "    integer, intent(inout) :: event_count\n"
        "    event_count=event_count+1\n"
        "  end subroutine make_undefined\n"
        "end program explicit_procedure_bounds\n")
    return p


def block_program():
    p = Program()
    p.add(
        "program explicit_block_bounds\n"
        "  implicit none\n"
        "  integer :: n, visit, outer_upper, outer_extent, outer_value\n"
        "  integer :: inner_bound, inner_upper, inner_extent, inner_value\n"
        "  integer :: outer_entries, inner_entries, inner_exits, outer_exits, events, checks\n"
        "  outer_entries=0\n  inner_entries=0\n  inner_exits=0\n  outer_exits=0\n  events=0\n  checks=0\n"
        "  do visit=1,2\n"
        "    if (visit == 1) then\n"
        "      n=3\n      outer_upper=3\n      outer_extent=6\n      outer_value=201\n"
        "      inner_bound=5\n      inner_upper=5\n      inner_extent=5\n      inner_value=301\n"
        "    else\n"
        "      n=1\n      outer_upper=1\n      outer_extent=4\n      outer_value=202\n"
        "      inner_bound=2\n      inner_upper=2\n      inner_extent=2\n      inner_value=302\n"
        "    end if\n"
        "    outer_activation: block\n"
        "      integer :: outer(-2:n)\n"
        "      outer=200+visit\n"
        "      outer_entries=outer_entries+1\n      events=events+1\n")
    p.guard("outer-entry", "outer_entries", "visit", indent="      ", repeat="visit", category="entry")
    p.guard("outer-entry-event", "events", "6*(visit-1)+1", indent="      ", repeat="visit")
    p.array("outer-initial", "outer", "-2", "outer_upper", "outer_extent", "outer_value", indent="      ")
    p.add("      n=inner_bound\n      events=events+1\n")
    p.guard("outer-source-redefined", "n", "inner_upper", indent="      ", repeat="visit")
    p.guard("outer-redefinition-event", "events", "6*(visit-1)+2", indent="      ", repeat="visit")
    p.array("outer-redefined", "outer", "-2", "outer_upper", "outer_extent", "outer_value", indent="      ")
    p.add(
        "      inner_activation: block\n"
        "        integer :: inner(1:n)\n"
        "        inner=300+visit\n"
        "        inner_entries=inner_entries+1\n        events=events+1\n")
    p.guard("inner-entry", "inner_entries", "visit", indent="        ", repeat="visit", category="entry")
    p.guard("inner-entry-event", "events", "6*(visit-1)+3", indent="        ", repeat="visit")
    p.array("inner-initial", "inner", "1", "inner_upper", "inner_extent", "inner_value", indent="        ")
    p.array("outer-with-inner", "outer", "-2", "outer_upper", "outer_extent", "outer_value", indent="        ")
    p.add("        n=9\n        events=events+1\n")
    p.guard("inner-source-redefined", "n", "9", indent="        ", repeat="visit")
    p.guard("inner-redefinition-event", "events", "6*(visit-1)+4", indent="        ", repeat="visit")
    p.array("inner-redefined", "inner", "1", "inner_upper", "inner_extent", "inner_value", indent="        ")
    p.array("outer-after-inner-change", "outer", "-2", "outer_upper", "outer_extent", "outer_value", indent="        ")
    p.add("      end block inner_activation\n      inner_exits=inner_exits+1\n      events=events+1\n")
    p.guard("inner-exit", "inner_exits", "visit", indent="      ", repeat="visit", category="exit")
    p.guard("inner-exit-event", "events", "6*(visit-1)+5", indent="      ", repeat="visit")
    p.array("outer-after-inner-exit", "outer", "-2", "outer_upper", "outer_extent", "outer_value", indent="      ")
    p.add("    end block outer_activation\n    outer_exits=outer_exits+1\n    events=events+1\n")
    p.guard("outer-exit", "outer_exits", "visit", indent="    ", repeat="visit", category="exit")
    p.guard("outer-exit-event", "events", "6*(visit-1)+6", indent="    ", repeat="visit")
    p.guard("host-source-after-exit", "n", "9", indent="    ", repeat="visit")
    if len(p.guards) != 48:
        raise ValueError("the explicit forty-eight-check-per-BLOCK-cycle oracle needs source review")
    p.guard("block-cycle-checks", "checks", "48*visit", indent="    ", repeat="visit", counter=None, category="completion")
    p.add("  end do\n")
    for expression, expected in (("outer_entries", 2), ("inner_entries", 2), ("inner_exits", 2),
                                 ("outer_exits", 2), ("events", 12), ("checks", 96)):
        p.guard("block-total-" + expression, expression, expected, counter=None, category="completion")
    p.completion("blocks")
    p.add("end program explicit_block_bounds\n")
    return p


def source_specs():
    result = {}
    for variant, program, facets in (
            ("procedure", procedure_program(), ["procedure-entry", "post-redefinition", "post-undefinition", "fresh-entries"]),
            ("blocks", block_program(), ["block-entry", "post-redefinition", "fresh-entries", "nested-blocks"])):
        raw = program.text.encode("ascii")
        probes = []
        for guard in program.guards:
            start, end = guard["span"]
            if raw[start:end].decode() != guard["expected"]:
                raise ValueError("the exact oracle span no longer matches its source")
            if guard["kind"] == "output":
                probes.append(dict(guard, id=guard["id"], replacement=guard["expected"].replace(" OK", " BAD"),
                                   activation=None))
            elif guard["repeat"]:
                variable = guard["repeat"]
                for activation, delta in ((1, f"2-{variable}"), (2, f"{variable}-1")):
                    probes.append(dict(guard, id=guard["id"] + f":activation-{activation}",
                                       replacement=f"({guard['expected']} + ({delta}))", activation=activation))
            else:
                probes.append(dict(guard, replacement=f"({guard['expected']} + 1)", activation=None))
        name = identifier(variant)
        result[name] = dict(id=name, variant=variant, facets=facets, evidence="effect", standard="f2023",
                            phase="run", source=program.text, source_sha256=sha(raw),
                            guards=program.guards, probes=probes, completion=COMPLETIONS[variant])
    return result


def wrong_oracle_source(spec, probe):
    raw = spec["source"].encode("ascii")
    start, end = probe["span"]
    if raw[start:end].decode() != probe["expected"]:
        raise ValueError("the wrong-oracle probe does not bind the complete parent input")
    return raw[:start] + probe["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = "tests/fixtures/explicit_bound_capture_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"], spec["manifest"] = directory + "/fixture.json", manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode()
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(row for row in result["requirements"] if row["id"] == RULE)
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
        raise ValueError("unselected explicit-bound source plans must remain pending")
    requirement["oracle"], requirement["oracle_limitation"] = ORACLE, LIMITATION
    return result


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(root)
    registry.catalogues[SECTION] = catalogue
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the explicit-shape native render boundary changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    anchor = "The catalogue is `doc/catalogues/explicit_shape_8_5_8_2.json`."
    if before.count(anchor) != 1:
        raise ValueError("the original explicit-shape qualification boundary changed")
    manual = anchor + before.split(anchor, 1)[1]
    manual = manual.replace("This source packet creates no fixtures", "The original batch039 source packet created no fixtures")
    pending = {row["id"]: len(row["pending"]) for row in catalogue["requirements"]}
    before = (
        "# Fortran 2023 8.5.8.2: Explicit-shape array\n\n"
        f"**Source review: {registry.catalogue_review_state(SECTION)}.** Original source review is recorded in batch039;\n"
        "current source, fixture and inventory adjudications are separate content-bound records.\n"
        "Two run/effect programs represent six named-local entry-capture facets of S8.5.8.2-005.\n"
        f"{pending[RULE]} S8.5.8.2-005 facet and {sum(pending.values()) - pending[RULE]} other local facets remain PENDING.\n\n"
        + manual)
    own_begin, own_end = "<!-- BEGIN EXPLICIT BOUND CAPTURE -->", "<!-- END EXPLICIT BOUND CAPTURE -->"
    if own_begin in after or own_end in after:
        if after.count(own_begin) != 1 or after.count(own_end) != 1:
            raise ValueError("the bound-capture view boundary changed")
        leading, tail = after.split(own_begin)
        _, trailing = tail.split(own_end)
    else:
        leading, trailing = after.rstrip() + "\n\n", "\n"
    detail = (
        "## Bounded ordinary-array entry capture\n\n"
        "The procedure owns a real `integer :: a(-2:n)`. Its previously typed nonoptional\n"
        "INOUT dummy arrives as3 then1; independent literal observer inputs specify\n"
        "upper/extent/value3/6/101 then1/4/102. Defined payload precedes every inquiry.\n"
        "The same named array is checked on entry, after n becomes0, and while n is\n"
        "undefined following a separate plain INTEGER INTENT(OUT) helper. That helper\n"
        "only increments its distinct event counter. Array inquiries and independent\n"
        "expectations do not read n; restoration precedes return and the caller's read.\n\n"
        "The BLOCK program has no main-program array. Two activations capture outer\n"
        "`outer(-2:n)` at3/1 and inner `inner(1:n)` at5/2. A later source value9 changes\n"
        "neither live array. Both have distinct defined payloads and literal branch\n"
        "expectations. Inner exit is followed only by outer observations; outer exit\n"
        "is followed only by live scalar counters, never expired objects.\n\n"
        "Whole-array LBOUND/UBOUND/SIZE/SHAPE and all-element data checks use no second\n"
        "descriptor oracle or constructor RANK. Positive entry/change/undefinition/\n"
        "exit/check counts and exact completion lines reject no-op and early success.\n"
        "Full-program one-span probes perturb every guard, separately on first and\n"
        "second activations where it repeats, plus each completion literal. A failure\n"
        "before runtime is not successful sensitivity evidence.\n\n"
        "Vector-bound syntax remains pending. No SAVE, initializer, allocation, pointer,\n"
        "coarray, COMMON/EQUIVALENCE, C interoperability, S8.3 proxy, fixture approval,\n"
        "baseline change, canonical-link or SourceUse credit is supplied.\n\n")
    return (before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"])
            + "\n" + end + leading + own_begin + "\n\n" + detail + own_end + trailing)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, _ = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated)
    actual = {path for path in (ROOT / "tests/fixtures").glob("explicit_bound_capture_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale explicit-bound subset: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded array-capture corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} two explicit-bound run/effect programs and six facets.")


if __name__ == "__main__":
    main()
