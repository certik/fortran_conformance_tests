#!/usr/bin/env python3
"""Two complete C851 contexts with exact dummy-list-only repairs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.12"
RULE = "C851"
CATALOGUE = "doc/catalogues/optional_attribute_8_5_12.json"
VIEW = "doc/fortran_2023_8_5_12.md"
FACETS = ("data-dummy-admission", "procedure-dummy-admission", "nondummy-exclusion")
GNU_CAUSE = "Symbol at (1) is not a DUMMY variable"
FLANG_CAUSE = (
    "Only a dummy argument should have an INTENT, VALUE, or OPTIONAL attribute "
    "[-Wignore-irrelevant-attributes]"
)
CAUSES = (GNU_CAUSE, FLANG_CAUSE)
NONFATAL = (dict(compiler="flang", severity="warning", equals_any=[FLANG_CAUSE]),)
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "cannot read module", "missing interface", "syntax error", "malformed",
)
ORACLE_PREFIX = "C851 ordinary OPTIONAL eligibility family: "
LIMIT_PREFIX = "C851 ordinary OPTIONAL eligibility limits: "
ORACLE = ORACLE_PREFIX + (
    "four complete compile/f2023 cases form two diagnostic/positive-control pairs. "
    "An external subroutine declares ordinary INTEGER OPTIONAL subject, and a module-contained "
    "procedure declares ordinary nonpointer PROCEDURE(signature) OPTIONAL callback with a prior "
    "abstract subroutine interface. Each invalid omits its subject from the dummy list; the sole "
    "repair inserts that name in the existing procedure header, preserving all other bytes. "
    "The actual staged declarations at lines3 and10 contain OPTIONAL and no INTENT or VALUE, "
    "so the exact measured GNU nondummy-role error and Flang full attribute/nondummy-role warning "
    "identify this predicate. A report must match a complete extracted cause at its actual staged "
    "subject declaration; generic argument words, echoes and foreign origins do not qualify. "
    "Only the observed exact Flang warning is a nonfatal allowance. Both controls require successful "
    "object compilation and retain positive-control evidence, not runtime effect."
)
LIMITATION = LIMIT_PREFIX + (
    "this family represents only data-dummy-admission, procedure-dummy-admission and nondummy-exclusion. "
    "It is not an exhaustive C851 case census. The callback repair remains a nonpointer dummy "
    "procedure, without INTENT, POINTER, initialization or SAVE. There are no calls, allocation, "
    "association, VALUE, C/coarray, payload or runtime operations. Entry/other-attribute boundaries "
    "and all S8.5.12-001 plans retain their independently managed states. The PRESENT note supplies "
    "no new case or source-use/runtime credit. Reporting capability does not prescribe fatal status, "
    "English wording or a printed code; these finite exact messages are calibrated qualification "
    "routes, not a universal vocabulary. No additional source span is needed by the measured "
    "reports, and neither coalesced lines nor widened spans are used. Unsupported procedures, "
    "Internal/ASR/crash/resource failures, quoted examples, source echoes and wrong-file reports "
    "never count. Flang f2018 evidence is not relabelled f2023. Generation preserves unselected "
    "pending/control and all review records, without approving, renewing, retagging or updating a baseline."
)
SUMMARY_BEGIN = "<!-- BEGIN OPTIONAL ELIGIBILITY SUMMARY -->"
SUMMARY_END = "<!-- END OPTIONAL ELIGIBILITY SUMMARY -->"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, negative=False):
    return RULE + ("_invalid" if negative else "_valid") + "__optional_" + variant + (
        "_nondummy" if negative else "_dummy_control")


def source_specs():
    contexts = {
        "data": (
            "subroutine optional_data_context()\n"
            "  implicit none\n"
            "  integer, optional :: subject\n"
            "end subroutine optional_data_context\n",
            "optional_data_context", "subject", 1, 3, "data-dummy-admission"),
        "procedure": (
            "module optional_procedure_scope\n"
            "  implicit none\n"
            "  abstract interface\n"
            "    subroutine signature()\n"
            "    end subroutine signature\n"
            "  end interface\n"
            "contains\n"
            "  subroutine declaration_context()\n"
            "    implicit none\n"
            "    procedure(signature), optional :: callback\n"
            "  end subroutine declaration_context\n"
            "end module optional_procedure_scope\n",
            "declaration_context", "callback", 8, 10, "procedure-dummy-admission"),
    }
    specs = {}
    for variant, (source, procedure, subject, header_line, declaration_line, admission) in contexts.items():
        raw = source.encode("ascii")
        header = ("subroutine " + procedure + "(").encode()
        if raw.count(header) != 1:
            raise ValueError("expected one subject procedure header")
        offset = raw.index(header) + len(header)
        if raw[offset:offset + 1] != b")":
            raise ValueError("the negative dummy list must be empty")
        inserted = subject.encode("ascii")
        control = raw[:offset] + inserted + raw[offset:]
        negative_id, control_id = identifier(variant, True), identifier(variant)
        repair = dict(
            negative_id=negative_id, control_id=control_id, header_line=header_line,
            insertion_byte_offset=offset, inserted=subject,
            negative_sha256=sha(raw), control_sha256=sha(control),
            dummy_list_role_only=True, all_other_bytes_unchanged=True,
        )
        for name, data, invalid in ((negative_id, raw, True), (control_id, control, False)):
            specs[name] = dict(
                id=name, variant=variant, kind="invalid" if invalid else "valid",
                evidence="effect" if invalid else "positive-control",
                facets=["nondummy-exclusion"] if invalid else [admission, "nondummy-exclusion"],
                subject=subject, source=data.decode(), source_sha256=sha(data),
                header_line=header_line, declaration_line=declaration_line, repair=repair,
                directory="tests/fixtures/optional_eligibility_" + variant + ("_invalid" if invalid else "_control"),
            )
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        invalid = spec["kind"] == "invalid"
        manifest = dict(
            schema_version=1, id=spec["id"], rule=RULE, facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", step="source", outcome="diagnose" if invalid else "success"),
        )
        if invalid:
            manifest["expect"]["diagnostic"] = dict(
                file="source.f90", line=spec["declaration_line"], end_line=spec["declaration_line"],
                equals_any=list(CAUSES), excludes_any=list(EXCLUSIONS),
                allow_nonfatal=copy.deepcopy(list(NONFATAL)),
            )
        directory = Path(root) / spec["directory"]
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        spec["path"], spec["manifest"] = spec["directory"] + "/fixture.json", manifest
    return files, specs


def owned_paragraph(value, prefix, replacement):
    paragraphs = value.split("\n\n")
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned C851 oracle paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return value + ("\n\n" if value else "") + replacement


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    matches = [row for row in updated["requirements"] if row["id"] == RULE]
    if len(matches) != 1 or not set(FACETS) <= set(matches[0]["facets"]):
        raise ValueError("the selected C851 requirement/facet definitions changed")
    requirement = matches[0]
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    requirement["oracle"] = owned_paragraph(requirement.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    requirement["oracle_limitation"] = owned_paragraph(requirement.get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    text = (Path(root) / VIEW).read_text()
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the OPTIONAL generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    anchor = "The canonical catalogue is "
    if before.count(anchor) != 1:
        raise ValueError("the OPTIONAL source narrative boundary changed")
    source = anchor + before.split(anchor, 1)[1]
    if SUMMARY_BEGIN in source:
        if source.count(SUMMARY_BEGIN) != 1 or source.count(SUMMARY_END) != 1:
            raise ValueError("the C851 family-summary boundaries changed")
        source, owned = source.split(SUMMARY_BEGIN)
        _, tail = owned.split(SUMMARY_END)
        source += tail
    else:
        legacy = "This registration adds no fixtures,"
        if legacy not in source:
            raise ValueError("the initial source-only narrative boundary changed")
        source = source.split(legacy, 1)[0]
    header = (
        "# Fortran 2023 8.5.12: OPTIONAL attribute\n\n"
        "Effective source status is `Registry.catalogue_review_state(\"8.5.12\")`,\n"
        "not a cached claim derived from the raw review field. The original source\n"
        "review is recorded in batch054. Source, fixture and inventory approvals\n"
        "remain independent and content-bound; generation grants none.\n\n"
    )
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Bounded ordinary C851 eligibility family\n\n"
        "Four compile/f2023 fixtures form two nondummy/valid-dummy pairs: an\n"
        "ordinary INTEGER entity in an external subroutine and a nonpointer\n"
        "dummy procedure with a complete abstract subroutine interface. Each\n"
        "repair adds only the subject to its existing subroutine header.\n"
        "No INTENT, POINTER, initialization, SAVE, call or runtime operation is\n"
        "added. The two valid cases are compile/positive-controls requiring\n"
        "objects; the two invalids are diagnostic-only evidence.\n\n"
        "The exact calibrated nondummy-role causes are bound to actual staged\n"
        "declaration lines3/10, whose only relevant attribute is OPTIONAL.\n"
        "Only the measured Flang warning is allowed nonfatally. Neither fatal\n"
        "status, a rule code nor standardized English is required. A bare\n"
        "argument word, source echo, quoted example, foreign path, unsupported\n"
        "procedure or Internal/ASR failure cannot supply the cause.\n\n"
        "This generator manages only the three selected C851 pending entries\n"
        "and its bounded oracle paragraphs. All unselected C851 facets, other\n"
        "requirements, control designations and review records retain their\n"
        "current independent state. It does not require future C851 cases to\n"
        "belong to this family. No PRESENT, omission, SourceUses or runtime\n"
        "effect credit, canonical link, approval or baseline update is added.\n"
        + SUMMARY_END + "\n\n"
    )
    return (header + source.rstrip() + "\n\n" + summary + begin + "\n\n"
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
            raise ValueError("stale C851 eligibility family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} C851 compile cases and {len(FACETS)} selected facets.")


if __name__ == "__main__":
    main()
