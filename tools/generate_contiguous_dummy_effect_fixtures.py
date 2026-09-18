#!/usr/bin/env python3
"""Two complete strided-actual CONTIGUOUS dummy runs with literal property and caller oracles."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from generate_contiguous_eligibility_fixtures import render_view as eligibility_view

ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.5.7-001"
CATALOGUE = "doc/catalogues/contiguous_attribute_8_5_7.json"
VIEW = "doc/fortran_2023_8_5_7.md"
FACETS = ("strided-actual-assumed-shape", "strided-actual-assumed-rank")
COMPLETIONS = {
    "assumed_shape": "CONTIGUOUS ASSUMED SHAPE OK\n",
    "assumed_rank": "CONTIGUOUS ASSUMED RANK OK\n",
}
ORACLE = (
    "Two complete run/effect/f2023 programs implement only strided-actual-assumed-shape and "
    "strided-actual-assumed-rank. Main defines an ordinary INTEGER a(4) by the executable assignment "
    "a=[11,12,13,14] and passes only the definable nonvector section a(1:4:2) through a complete internal "
    "procedure interface to a CONTIGUOUS INTENT(INOUT) dummy. Direct IS_CONTIGUOUS(x) is compared with "
    "literal true, and actual dummy RANK/SIZE are checked against1/2. The ordinary assumed-shape case "
    "checks x(1:2) values11/13 separately, adds10 to each, and checks21/23. The assumed-rank case "
    "uses property inquiries on x as permitted by C840, then SELECT RANK(r=>x), RANK(1), for every "
    "payload read/write. The default branch ERROR STOPs. Main independently checks all four returned "
    "values21/12/23/14, so untouched elements and updates are both consumed. Entry, update, normal "
    "procedure-completion, rank-branch and guard-count observations plus exact completion stdout, empty "
    "stderr and normal exit0 reject missing calls, updates and no-op/early-success paths. Every contiguity, "
    "rank, size, value, event, check-total and output assertion has an exact one-span full-program "
    "wrong-oracle probe, qualified only when the unchanged current parent passes and the intended "
    "runtime guard/output mismatch occurs."
)
LIMITATION = (
    "Other S8.5.7-001 facets are outside this generator's coverage, and C830 plus the other S requirements "
    "retain their supplied source, fields, pending states and ownership. Both programs are effects; no control-role "
    "opt-in or C715 control reuse is supplied. The actual is a nonvector INTEGER triplet section with "
    "defined elements, no ASYNCHRONOUS, VOLATILE, POINTER, ALLOCATABLE, coarray, VALUE or overlapping "
    "dummy actuals. Matching default-INTEGER type/kind/rank and definability/explicit-interface conditions "
    "are preserved. The C1548/C1549 antecedents do not apply; the source's dummy guarantee does not "
    "assert that the caller has CONTIGUOUS. No optional actual-section contiguity inquiry, pointer "
    "assignment, fixed-rank observer temporary or RANK constructor appears. The rank-one associate "
    "designates the actual dummy, not a separate destination. No copying count, temporary/address, ABI, "
    "storage-stride or allocation mechanism is observed or required. Complete source and literal truth "
    "precede compiler calibration. Build/unsupported/resource/runtime failures remain real; failed "
    "parents and compile rejections do not qualify sensitivity. ERROR STOP token/status observations "
    "are empirical guard evidence, not mandatory printed rule codes or a numeric termination policy. "
    "Source, fixture, mode-qualified observations and inventory approval remain independent; no source-use, "
    "canonical-link, review or baseline record is renewed."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    return "S8_5_7_001_valid__contiguous_dummy_effect_" + variant


class Program:
    def __init__(self):
        self.text = ""
        self.guards = []

    def add(self, text):
        self.text += text

    def guard(self, name, expression, expected, *, logical=False, category="event",
              counter="checks", indent="  "):
        literal = ".true." if logical else str(expected)
        operator = ".neqv." if logical else "/="
        prefix = f"{indent}if ({expression} {operator} "
        start = len(self.text) + len(prefix)
        self.guards.append(dict(
            id=name, kind="guard", category=category, expression=expression, expected=literal,
            replacement=".false." if logical else str(int(expected) + 1),
            span=[start, start + len(literal)], line=self.text.count("\n") + 1,
            failure_token="CDE:" + name, counter=counter))
        self.add(prefix + literal + f") error stop 'CDE:{name}'\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")

    def completion(self, variant):
        literal = COMPLETIONS[variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        self.guards.append(dict(id="completion-output", kind="output", category="completion",
                                expected=literal, replacement=literal.replace(" OK", " BAD"),
                                span=[start, start + len(literal)], line=self.text.count("\n") + 1,
                                counter=None))
        self.add(prefix + literal + "'\n")


def source_specs():
    specs = {}
    for variant, facet in zip(("assumed_shape", "assumed_rank"), FACETS):
        ranked = variant == "assumed_rank"
        branch_arg = ", branches" if ranked else ""
        total = 11 if ranked else 10
        p = Program()
        p.add(f"program contiguous_{variant}_effect\n"
              "  implicit none\n"
              "  integer :: a(4)\n"
              f"  integer :: entries, updates, exits, checks, main_checks{branch_arg}\n"
              "  a=[11,12,13,14]\n"
              "  entries=0\n  updates=0\n  exits=0\n  checks=0\n  main_checks=0\n")
        if ranked:
            p.add("  branches=0\n")
        for i, value in enumerate((11,12,13,14), 1):
            p.guard(f"caller-initial-{i}", f"a({i})", value, category="data", counter="main_checks")
        p.add(f"  call update_section(a(1:4:2), entries, updates, exits, checks{branch_arg})\n")
        for name, expression, value in (
                ("entry", "entries", 1), ("updates", "updates", 2), ("return", "exits", 1),
                ("procedure-checks", "checks", total)):
            p.guard("caller-" + name, expression, value, counter="main_checks")
        if ranked:
            p.guard("caller-rank-branch", "branches", 1, counter="main_checks")
        for i, value in enumerate((21,12,23,14), 1):
            p.guard(f"caller-returned-{i}", f"a({i})", value, category="data", counter="main_checks")
        p.guard("caller-check-total", "main_checks", 13 if ranked else 12, category="completion", counter=None)
        p.completion(variant)
        p.add("contains\n"
              f"  subroutine update_section(x, entries, updates, exits, checks{branch_arg})\n"
              "    implicit none\n"
              f"    integer, contiguous, intent(inout) :: x({'..' if ranked else ':'})\n"
              f"    integer, intent(inout) :: entries, updates, exits, checks{branch_arg}\n"
              "    entries=entries+1\n")
        p.guard("dummy-entry", "entries", 1, indent="    ", category="entry")
        p.guard("dummy-contiguity", "is_contiguous(x)", True, logical=True, indent="    ", category="contiguity")
        p.guard("dummy-rank", "rank(x)", 1, indent="    ", category="rank")
        p.guard("dummy-size", "size(x)", 2, indent="    ", category="size")
        if ranked:
            p.add("    select rank (r => x)\n"
                  "    rank (1)\n"
                  "      branches=branches+1\n")
            p.guard("rank-one-branch", "branches", 1, indent="      ", category="branch")
        data = "r" if ranked else "x"
        indent = "      " if ranked else "    "
        for i, value in enumerate((11,13), 1):
            p.guard(f"dummy-initial-{i}", f"{data}({i})", value, indent=indent, category="data")
        for i, value in enumerate((21,23), 1):
            p.add(f"{indent}{data}({i})={data}({i})+10\n{indent}updates=updates+1\n")
            p.guard(f"dummy-updated-{i}", f"{data}({i})", value, indent=indent, category="data")
        p.guard("dummy-update-total", "updates", 2, indent=indent, category="update")
        if ranked:
            p.add("    rank default\n"
                  "      error stop 'CDE:unexpected-rank'\n"
                  "    end select\n")
        p.add("    exits=exits+1\n")
        p.guard("dummy-completed", "exits", 1, indent="    ", category="return")
        p.add("  end subroutine update_section\n" + f"end program contiguous_{variant}_effect\n")
        if sum(guard["counter"] == "checks" for guard in p.guards) != total:
            raise ValueError("the literal procedure check-total needs source review")
        if sum(guard["counter"] == "main_checks" for guard in p.guards) != (13 if ranked else 12):
            raise ValueError("the literal caller check-total needs source review")
        raw = p.text.encode("ascii")
        for guard in p.guards:
            start, end = guard["span"]
            if raw[start:end].decode() != guard["expected"]:
                raise ValueError("an oracle span no longer matches the complete source")
        name = identifier(variant)
        specs[name] = dict(id=name, variant=variant, facet=facet, source=p.text, source_sha256=sha(raw),
                           evidence="effect", standard="f2023", phase="run", guards=p.guards,
                           completion=COMPLETIONS[variant], procedure_checks=total,
                           main_checks=13 if ranked else 12)
    return specs


def wrong_oracle_source(spec, guard):
    raw = spec["source"].encode("ascii")
    start, end = guard["span"]
    if raw[start:end].decode() != guard["expected"]:
        raise ValueError("wrong-oracle edit does not bind its complete parent input")
    return raw[:start] + guard["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = "tests/fixtures/contiguous_dummy_effect_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=[spec["facet"]], evidence="effect",
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
    if not set(FACETS) <= set(requirement["facets"]):
        raise ValueError("the selected S8.5.7-001 facet definitions changed")
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    requirement["oracle"], requirement["oracle_limitation"] = ORACLE, LIMITATION
    return result


def render_view(catalogue, root=ROOT):
    text = eligibility_view(catalogue, root)
    begin, end = "<!-- BEGIN CONTIGUOUS DUMMY EFFECTS -->", "<!-- END CONTIGUOUS DUMMY EFFECTS -->"
    if begin in text or end in text:
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("invalid contiguous-dummy view boundaries")
        before, tail = text.split(begin)
        _, after = tail.split(end)
    else:
        before, after = text.rstrip() + "\n\n", "\n"
    requirement = next(row for row in catalogue["requirements"] if row["id"] == RULE)
    detail = (
        "## Bounded CONTIGUOUS dummy runtime effects\n\n"
        "Two complete run/effect programs initialize ordinary INTEGER a(4) to11/12/13/14\n"
        "and pass the nonvector section a(1:4:2) to a CONTIGUOUS INOUT dummy through\n"
        "a complete internal-procedure interface. The dummy itself must satisfy\n"
        "IS_CONTIGUOUS=true, RANK1 and SIZE2. Its initial values11/13 are checked\n"
        "separately, each is increased by10, and21/23 are checked in the procedure.\n"
        "The caller independently verifies21/12/23/14 after return.\n\n"
        "For the assumed-rank case, x appears only in permitted property inquiries\n"
        "and as SELECT RANK selector. All payload access uses its rank-one associate;\n"
        "the unexpected-rank branch ERROR STOPs. No constructor RANK, fixed-rank\n"
        "observer temporary, vector subscript, pointer or allocation route is used.\n\n"
        "Entry/update/procedure-completion/check totals, a rank-branch counter and\n"
        "exact stdout/empty-stderr/normal-zero contracts reject missing calls and\n"
        "no-op/early-success paths. Every predicate and completion literal has one\n"
        "bounded full-program wrong-oracle edit. A failed parent, build failure or\n"
        "wrong runtime guard cannot qualify sensitivity.\n\n"
        "Original8.5.7p1/NOTE3 supplies the dummy property without requiring actual\n"
        "CONTIGUOUS. C1548/C1549's extra-attribute antecedents are absent; ordinary\n"
        "type/kind/rank, definability and distinct-argument premises still apply.\n"
        "No actual-section contiguity query is added, and no copy count, temporary,\n"
        "address, ABI, storage stride or allocation mechanism is promised.\n\n"
        f"{len(requirement['pending'])} other {RULE} facets remain PENDING. The C830\n"
        "matrix's supplied fields, cases and adjudications are preserved, as are C715 and all\n"
        "other owners. Neither case is positive-control or S3/S4 coverage. Source,\n"
        "fixture, native mode qualification and inventory review remain separate.\n\n")
    return before + begin + "\n\n" + detail + end + after


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
    actual = {path for path in (ROOT / "tests/fixtures").glob("contiguous_dummy_effect_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale contiguous-dummy effects: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded contiguous-dummy corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} two CONTIGUOUS dummy run/effect programs and two facets.")


if __name__ == "__main__":
    main()
