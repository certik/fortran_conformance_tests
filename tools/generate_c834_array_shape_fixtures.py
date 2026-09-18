#!/usr/bin/env python3
"""Finite ordinary-array C834 declarations with exact array-spec-only repairs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.8.4"
RULE = "C834"
CATALOGUE = "doc/catalogues/deferred_shape_8_5_8_4.json"
VIEW = "doc/fortran_2023_8_5_8_4.md"
FACETS = ("pointer-deferred-list", "allocatable-deferred-list", "explicit-bound-exclusion")
VARIANTS = {
    "pointer_scalar": ("pointer", "2"),
    "pointer_vector": ("pointer", "[2]"),
    "allocatable_scalar": ("allocatable", "2"),
    "allocatable_vector": ("allocatable", "[2]"),
}
CAUSES = {
    "pointer_scalar": (
        "Pointer array 'a' must have a deferred shape or assumed rank",
        "Array pointer 'a' at (1) must have a deferred shape or assumed rank",
        "Array pointer 'a' must have deferred shape or assumed rank",
    ),
    "pointer_vector": (
        "Array pointer 'a' at (1) must have a deferred shape or assumed rank",
        "Array pointer 'a' must have deferred shape or assumed rank",
    ),
    "allocatable_scalar": (
        "Allocatable array 'a' must have a deferred shape or assumed rank",
        "Allocatable array 'a' at (1) must have a deferred shape or assumed rank",
        "Allocatable array 'a' must have deferred shape or assumed rank",
    ),
    "allocatable_vector": (
        "Allocatable array 'a' at (1) must have a deferred shape or assumed rank",
        "Allocatable array 'a' must have deferred shape or assumed rank",
    ),
}
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "expecting a scalar integer", "must be a scalar value", "rank-1 array",
    "kind", "unknown type", "initialization", "initializer", "syntax error", "malformed",
    "duplicate", "cannot read module", "missing interface",
)
ORACLE = (
    "Eight complete compile/f2023 external-subroutine units represent three ordinary-array C834 "
    "facets. Four negatives cross POINTER and ALLOCATABLE with a(2) and a([2]). The scalar bound "
    "is a constant specification expression; [2] is a restricted and constant rank-one INTEGER "
    "array constructor of size one. R818 and 8.5.8.2p1 therefore describe a rank-one explicit-shape "
    "array, not a zero-vector scalar. No RANK clause is present. Each paired control changes only "
    "the array-spec 2 or [2] to :, preserving rank one, attributes, entity and complete local "
    "context. Controls represent the corresponding pointer/allocatable deferred-list admission "
    "and the explicit-bound exclusion repair, not additional runtime effects. A negative requires "
    "an actual located full array/attribute/declaration-form cause at source.f90 line3, with exact "
    "case-specific alternatives and live staged-source identity. Ordinary zero or nonzero "
    "reporting statuses can satisfy capability; successful control object compilation is required."
)
LIMITATION = (
    "This is a finite rank-one ordinary-array matrix, not all C834 declarations. RANK-clause, "
    "scalar/assumed-rank and component-grammar facets remain pending. A([2]) has a nonzero-size-one "
    "bound vector and is not the scalar alternative; its element value two does not make its "
    "rank two. A generic scalar-expression, vector-unsupported, type/kind, initialization, "
    "association, recovery or checker-failure report is not the C834 cause. A distinct genuine "
    "C834 diagnostic can coexist with an unqualified scalar-only complaint; the latter is retained "
    "but earns no credit. Exact alternatives are calibrated evidence predicates, not standardized "
    "English. No fatal exit or printed rule code is mandated. No non-error warning/portability "
    "alternative was calibrated, so none is opted in. Flang f2018 observations are supplementary, "
    "not f2023 reference validation. All variables are unused ordinary locals of complete external "
    "subroutines, without initialization, explicit or implicit SAVE, dummy/target/coarray/C "
    "roles, allocation, association or payload inquiry. Existing C750/C754 component witnesses "
    "retain their owners. R822 and all S-owned runtime/state/source plans remain separate; no "
    "runtime contiguity, value, ABI or memory-layout claim follows from these compile controls. "
    "Generation preserves raw source/case/link/SourceUses/inventory reviews and never renews them."
)
OLD_FOOTER = "No fixtures, compiler invocations, profiles, source-use instances, links or\n"
NEW_FOOTER = "This packet registers only the bounded C834 declarations and paired compile controls.\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, invalid):
    return RULE + ("_invalid" if invalid else "_valid") + "__array_shape_" + variant


def program(attribute, bound):
    return (
        "subroutine array_shape_context()\n"
        "  implicit none\n"
        f"  integer, {attribute} :: a({bound})\n"
        "end subroutine array_shape_context\n"
    )


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for variant, (attribute, bound) in VARIANTS.items():
        original = program(attribute, bound).encode("ascii")
        start = original.index(("a(" + bound + ")").encode()) + 2
        end = start + len(bound)
        repaired = original[:start] + b":" + original[end:]
        if repaired != program(attribute, ":").encode("ascii"):
            raise ValueError("a C834 repair must change only the array-spec")
        repair = dict(
            byte_span_zero_based_half_open=[start, end], before=bound, after=":",
            negative_sha256=sha(original), control_sha256=sha(repaired),
            all_other_bytes_preserved=True,
        )
        for invalid, raw in ((True, original), (False, repaired)):
            suffix = variant if invalid else variant + "_control"
            name = identifier(suffix, invalid)
            directory = "tests/fixtures/c834_array_shape_" + variant + ("_invalid" if invalid else "_control")
            facets = ["explicit-bound-exclusion"] if invalid else [
                attribute + "-deferred-list", "explicit-bound-exclusion"]
            manifest = dict(
                schema_version=1, id=name, rule=RULE, facets=facets, standard="f2023",
                evidence="effect" if invalid else "positive-control", files=["source.f90"],
                build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                expect=dict(phase="compile", outcome="diagnose" if invalid else "success", step="source"),
            )
            if invalid:
                manifest["expect"]["diagnostic"] = dict(
                    file="source.f90", line=3, end_line=3,
                    equals_any=list(CAUSES[variant]), excludes_any=list(EXCLUSIONS))
            specs[name] = dict(
                id=name, variant=suffix, kind="invalid" if invalid else "valid",
                attribute=attribute, bound_form="vector" if bound == "[2]" else "scalar",
                array_spec=bound if invalid else ":", rank=1, declaration_line=3,
                source=raw.decode("ascii"), source_sha256=sha(raw), repair=repair,
                path=directory + "/fixture.json", manifest=manifest)
            files[Path(root) / directory / "source.f90"] = raw
            files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(item for item in result["requirements"] if item["id"] == RULE)
    if not set(FACETS) <= set(requirement["facets"]):
        raise ValueError("the selected C834 facet definitions changed")
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    requirement["oracle"], requirement["oracle_limitation"] = ORACLE, LIMITATION
    return result


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(root)
    registry.catalogues[SECTION] = catalogue
    state = registry.catalogue_review_state(SECTION)
    requirement = next(item for item in catalogue["requirements"] if item["id"] == RULE)
    others = sum(len(item["pending"]) for item in catalogue["requirements"] if item["id"] != RULE)
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    text = (Path(root) / VIEW).read_text()
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the deferred-shape generated boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    first = "The catalogue is "
    if before.count(first) != 1:
        raise ValueError("the original source-plan boundary changed")
    preserved = first + before.split(first, 1)[1]
    tails = [tail for tail in (OLD_FOOTER, NEW_FOOTER) if preserved.count(tail) == 1]
    if len(tails) != 1:
        raise ValueError("the source-only/current packet footer boundary changed")
    preserved = preserved.split(tails[0], 1)[0]
    header = (
        "# Fortran 2023 8.5.8.4: Deferred-shape array\n\n"
        f"**Source review: {state}.** Effective content-bound status is computed by\n"
        '`Registry.catalogue_review_state("8.5.8.4")`. The original independent\n'
        "source gate is batch041; fixture and observational-inventory adjudications\n"
        "remain separate and are not renewed by generation.\n\n"
        "## Bounded ordinary-array C834 matrix\n\n"
        "Eight compile/f2023 cases pair four ordinary POINTER/ALLOCATABLE array\n"
        "negatives with exact bound-only repairs. The forms `a(2)` and `a([2])`\n"
        "both declare rank-one arrays; `[2]` is a constant size-one integer vector,\n"
        "not a zero-vector scalar. Each repair replaces only `2` or `[2]` with `:`.\n"
        "Complete external-subroutine contexts avoid initialization and SAVE; no\n"
        "allocation, association, target access, inquiry, C companion or run is used.\n\n"
        "The four valid controls are compile/positive-control evidence for the\n"
        "corresponding deferred-list category and the exclusion's repair facet.\n"
        "There are no extra admission-only programs. Three C834 facets are represented\n"
        "in these finite contexts, not every RANK/scalar/assumed-rank/component form.\n"
        f"{len(requirement['pending'])} C834 facets remain PENDING; other requirements currently\n"
        f"have {others} pending facets ({len(requirement['pending']) + others} total in 8.5.8.4).\n\n"
        "Each negative requires a case-specific exact full cause at the actual\n"
        "staged declaration. Scalar-only or unsupported-vector complaints, quoted\n"
        "examples, wrong origins and checker failures do not supply that cause.\n"
        "A separate genuine cause may coexist with an unqualified ordinary error;\n"
        "both messages remain recorded. Only actual error-severity reports are\n"
        "calibrated here; no warning/portability opt-in is invented. Ordinary0/1/2\n"
        "reporting status is not a mandatory fatal-exit policy. English alternatives\n"
        "are finite evidence predicates, not standard-mandated wording. Flangf2018\n"
        "is supplementary; only qualified current f2023 evidence can corroborate.\n\n"
        "The original source-only distinctions and runtime plans below are retained;\n"
        "this packet does not satisfy or rewrite them.\n\n"
    )
    footer = (
        NEW_FOOTER
        + "No R822/S runtime facet, profile, canonical link, source-use instance or\n"
        "administrative approval is added. C750/C754 component owners are unchanged.\n\n"
    )
    return (header + preserved + footer + begin + "\n\n"
            + "\n".join(render_requirement(item) for item in catalogue["requirements"])
            + "\n" + end + after)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, specs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated)
    actual = {path for path in (ROOT / "tests/fixtures").glob("c834_array_shape_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale C834 corpus: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded C834 corpus")
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files: "
          f"{len(specs)} compile cases, {len(FACETS)} C834 facets.")


if __name__ == "__main__":
    main()
