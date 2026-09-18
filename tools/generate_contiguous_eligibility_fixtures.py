#!/usr/bin/env python3
"""Finite C830 declaration contexts with byte-exact CONTIGUOUS-only repairs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.7"
RULE = "C830"
CATALOGUE = "doc/catalogues/contiguous_attribute_8_5_7.json"
VIEW = "doc/fortran_2023_8_5_7.md"
NEGATIVES = {
    "ordinary_scalar": ("ordinary-scalar-excluded", "integer, contiguous :: subject", False),
    "scalar_pointer": ("scalar-pointer-excluded", "integer, pointer, contiguous :: subject", False),
    "explicit_shape": ("explicit-shape-excluded", "integer, contiguous :: subject(2)", False),
    "allocatable_fixed_rank": (
        "allocatable-fixed-rank-excluded", "integer, allocatable, contiguous :: subject(:)", False),
    "assumed_size": ("assumed-size-excluded", "integer, contiguous :: subject(*)", True),
}
ADMISSIONS = {
    "array_pointer": ("array-pointer-admission", "integer, pointer, contiguous :: subject(:)", False),
    "assumed_shape": ("assumed-shape-admission", "integer, contiguous :: subject(:)", True),
    "assumed_rank": ("assumed-rank-admission", "integer, contiguous :: subject(..)", True),
    "allocatable_assumed_rank": (
        "assumed-rank-admission", "integer, allocatable, contiguous :: subject(..)", True),
}
FACETS = tuple(dict.fromkeys(row[0] for row in (*NEGATIVES.values(), *ADMISSIONS.values())))
GNU_CAUSE = (
    "'subject' at (1) has the CONTIGUOUS attribute but is not an array pointer "
    "or an assumed-shape or assumed-rank array"
)
FLANG_CAUSE = (
    "CONTIGUOUS entity 'subject' should be an array pointer, assumed-shape, "
    "or assumed-rank [-Wredundant-contiguous]"
)
CAUSES = {variant: (GNU_CAUSE, FLANG_CAUSE) for variant in NEGATIVES}
NONFATAL = (dict(compiler="flang", severity="portability", equals_any=[FLANG_CAUSE]),)
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "kind", "initialization", "initializer", "syntax error", "malformed",
    "duplicate", "cannot read module", "missing interface",
)
ORACLE = (
    "Fourteen complete compile/f2023 program units represent eight C830 facets. Five negatives "
    "give CONTIGUOUS to an ordinary scalar, scalar pointer, ordinary explicit-shape array, "
    "fixed-rank deferred-shape ALLOCATABLE array, or nonpointer assumed-size dummy. Each control "
    "deletes only ', contiguous', preserving every other byte and the actual entity category. "
    "Four additional admissions declare an array pointer and explicit-interface assumed-shape, "
    "ordinary assumed-rank and ALLOCATABLE assumed-rank dummies. A negative needs the actual "
    "located CONTIGUOUS/entity-category cause in the actual staged input, matching one complete "
    "extracted diagnostic message. The four ordinary declarations retain their line3 anchor. "
    "The assumed-size dummy has primary declaration line6 and additional procedure-header line4 "
    "as separate subject anchors; gap line5 and cross-anchor ranges do not qualify. An ordinary zero or "
    "nonzero reporting status can satisfy that capability. Only the exact observed Flang "
    "portability message is an allowed nonfatal report. Every valid case requires successful "
    "object compilation and is positive-control evidence, not a runtime effect."
)
LIMITATION = (
    "The assumed-size pair preserves the original complete module/procedure source and its "
    "CONTIGUOUS-only repair. Its declaration/header relation uses the independently reviewed "
    "disjoint-anchor infrastructure from batch048, not a broadened span, coalesced statements "
    "or a false GNU conformance failure for selecting the header. Source, fixture and processor "
    "adjudications remain separate from representing that relation. "
    "This finite eligibility matrix is not an enumeration of all possible declarations, actual "
    "arguments or processor modes. Ordinary fixed-rank exclusions do not ban eligible assumed-rank "
    "dummies, and actual whole-array contiguity does not authorize the attribute. Module-contained "
    "procedures supply explicit interfaces without requiring any unavailable payload, allocation "
    "or pointer-association inquiry. No initializer, DATA, SAVE, coarray, C companion, user-defined "
    "type, argument call, pointer assignment or runtime observer is present. All four S-owned "
    "contiguity requirements, residual processor choices and canonical component/source-use owners "
    "remain separate. No fatal exit, printed rule code or prescribed English text is required. "
    "Exact finite message alternatives are qualification predicates, not standardized wording. "
    "Quoted examples inside another error and foreign paths sharing the source basename cannot "
    "supply this cause or source identity. "
    "Source echoes, bare attribute words, unrelated shape/type/kind failures, unsupported facilities, "
    "Internal/ASR/verifier, timeout/crash/resource failures and wrong-source reports do not count. "
    "Generation preserves independent source, case, link, SourceUses and inventory adjudications; "
    "it neither approves them nor relabels earlier compiler observations."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, negative=False):
    return RULE + ("_invalid" if negative else "_valid") + "__contiguous_eligibility_" + variant


def program(declaration, dummy):
    if dummy:
        return (
            "module eligibility_scope\n  implicit none\ncontains\n"
            "  subroutine declaration_context(subject)\n    implicit none\n"
            f"    {declaration}\n"
            "  end subroutine declaration_context\nend module eligibility_scope\n"
        ), 6
    return (
        f"program declaration_context\n  implicit none\n  {declaration}\n"
        "end program declaration_context\n"
    ), 3


def source_specs():
    specs = {}
    for variant, (facet, declaration, dummy) in NEGATIVES.items():
        source, line = program(declaration, dummy)
        raw, deletion = source.encode("ascii"), b", contiguous"
        if raw.count(deletion) != 1:
            raise ValueError("a C830 repair needs exactly one CONTIGUOUS specification")
        start = raw.index(deletion)
        end = start + len(deletion)
        repaired = raw[:start] + raw[end:]
        negative, control = identifier(variant, True), identifier(variant + "_control")
        repair = dict(
            negative_id=negative, control_id=control, line=line,
            byte_span_zero_based_half_open=[start, end], deleted=deletion.decode(),
            negative_sha256=sha(raw), control_sha256=sha(repaired),
            only_CONTIGUOUS_and_separator_deleted=True, all_other_source_bytes_unchanged=True,
        )
        for name, text, invalid in ((negative, source, True), (control, repaired.decode(), False)):
            specs[name] = dict(
                id=name, variant=variant + ("" if invalid else "_control"),
                kind="invalid" if invalid else "valid", facet=facet, source=text,
                source_sha256=sha(text.encode()), declaration_line=line, subject="subject",
                context="module-procedure-dummy" if dummy else "main-local", repair=repair,
                evidence="effect" if invalid else "positive-control",
            )
    for variant, (facet, declaration, dummy) in ADMISSIONS.items():
        source, line = program(declaration, dummy)
        name = identifier(variant)
        specs[name] = dict(
            id=name, variant=variant, kind="valid", facet=facet, source=source,
            source_sha256=sha(source.encode()), declaration_line=line, subject="subject",
            context="module-procedure-dummy" if dummy else "main-local",
            evidence="positive-control",
        )
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        invalid = spec["kind"] == "invalid"
        directory = "tests/fixtures/contiguous_eligibility_" + spec["variant"] + ("_invalid" if invalid else "")
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=[spec["facet"]], standard="f2023",
            evidence=spec["evidence"], files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", outcome="diagnose" if invalid else "success", step="source"),
        )
        if invalid:
            causes = CAUSES.get(spec["variant"])
            if not causes:
                raise ValueError("native causal calibration is required for " + spec["variant"])
            manifest["expect"]["diagnostic"] = dict(
                file="source.f90", line=spec["declaration_line"], end_line=spec["declaration_line"],
                equals_any=list(causes), excludes_any=list(EXCLUSIONS),
                allow_nonfatal=copy.deepcopy(list(NONFATAL)),
            )
            if spec["variant"] == "assumed_size":
                manifest["expect"]["diagnostic"]["additional_spans"] = [dict(line=4)]
        spec["path"], spec["manifest"] = directory + "/fixture.json", manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(item for item in result["requirements"] if item["id"] == RULE)
    if not set(FACETS) <= set(requirement["facets"]):
        raise ValueError("the selected C830 facet definitions changed")
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    requirement["oracle"] = ORACLE
    requirement["oracle_limitation"] = LIMITATION
    return result


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(root)
    registry.catalogues[SECTION] = catalogue
    state = registry.catalogue_review_state(SECTION)
    requirement = next(item for item in catalogue["requirements"] if item["id"] == RULE)
    other_pending = sum(len(item["pending"]) for item in catalogue["requirements"] if item["id"] != RULE)
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    text = (Path(root) / VIEW).read_text()
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the 8.5.7 generated-region boundary changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    first, last = "The catalogue is ", "Existing C715, C748, C757, C769 and R738"
    if before.count(first) != 1 or before.count(last) != 1:
        raise ValueError("the 8.5.7 source and canonical-ownership boundaries changed")
    preserved = first + before.split(first, 1)[1].split(last, 1)[0]
    header = (
        "# Fortran 2023 8.5.7: CONTIGUOUS attribute\n\n"
        f"**Source review: {state}.** Effective content-bound status is computed by\n"
        '`Registry.catalogue_review_state("8.5.7")`, not the raw review field.\n'
        "The original independent source gate is recorded in batch038. Fixture,\n"
        "source and observational-inventory adjudications remain separate.\n\n"
        "## Bounded C830 eligibility matrix\n\n"
        "Fourteen compile/f2023 cases represent eight C830 facets: five invalid\n"
        "entity categories and exact CONTIGUOUS-only repairs, plus four admissions\n"
        "covering the three eligible categories. Assumed-rank admissions include\n"
        "both ordinary and ALLOCATABLE dummies. Every repair deletes only\n"
        "`, contiguous`, keeping the original rank, POINTER/ALLOCATABLE role,\n"
        "dummy/interface context and all other source bytes.\n\n"
        "The nine valid cases are compile/positive-control evidence. No link, run,\n"
        "allocation, association, payload, argument-copy or contiguity inquiry is\n"
        "observed. Negatives require a located entity-category cause, not a bare\n"
        "attribute word, source echo, unrelated error or native compiler failure.\n"
        "A full extracted cause must match an exact reviewed alternative in the\n"
        "actual staged source. Quoted example text and foreign same-basename paths\n"
        "cannot supply the cause or its origin. Other wording remains unqualified,\n"
        "not a claim that the standard mandates these English messages.\n"
        "Required reporting does not prescribe fatal rejection or a printed code.\n"
        "Only the exact observed Flang portability cause is a qualified nonfatal\n"
        "report; its f2018 mode is not relabelled as f2023 corroboration.\n\n"
        f"{len(requirement['pending'])} C830 facets remain PENDING; the other requirements currently\n"
        f"have {other_pending} pending facets ({len(requirement['pending']) + other_pending} total in 8.5.7).\n"
        "Generation changes only the selected requirement's pending/oracle fields\n"
        "and preserves all independent administrative records without renewing them.\n\n"
    )
    ownership = (
        "Existing C715, C748, C757, C769 and R738 witnesses retain their original\n"
        "IDs, inputs, roles and owners. No C814/C815/CODIM/R402 work is changed.\n"
        "The current finite R402 declaration-name SourceUse is retained without\n"
        "execution or facet-completion credit. This packet adds no inventory\n"
        "instance, source-use record or canonical link.\n\n"
        "The following definitions are generated from the catalogue. Admission,\n"
        "runtime-effect, reporting and source-only plans remain separate.\n\n"
    )
    relation = (
        "The assumed-size pair retains the original complete module/procedure\n"
        "sources and exact attribute-only repair. Its primary declaration anchor\n"
        "is line6; additional line4 identifies the same dummy in the procedure\n"
        "header. Each reported range must fit one anchor. Gap line5 and a4..6\n"
        "recovery range do not qualify. This uses the independently reviewed\n"
        "batch048 infrastructure without source coalescing or a false GNU failure.\n"
        "The registered contracts and fresh observations still require independent\n"
        "source/fixture adjudication; earlier raw calibration remains historical.\n\n"
    )
    return (header + relation + preserved + ownership + begin + "\n\n"
            + "\n".join(render_requirement(item) for item in catalogue["requirements"])
            + "\n" + end + after)


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
    actual = {path for path in (ROOT / "tests/fixtures").glob("contiguous_eligibility_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale C830 eligibility corpus: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded C830 corpus")
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files: "
          f"{len(files) // 2} compile cases, {len(FACETS)} C830 facets.")


if __name__ == "__main__":
    main()
