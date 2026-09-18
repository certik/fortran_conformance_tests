#!/usr/bin/env python3
"""Standalone CONTIGUOUS forms and their source-minimal missing-list repairs."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.6.6"
RULE = "R839"
CATALOGUE = "doc/catalogues/contiguous_statement_8_6_6.json"
VIEW = "doc/fortran_2023_8_6_6.md"
FORMS = {"no_colon": "no-double-colon-form", "double_colon": "double-colon-form"}
FACETS = ("double-colon-form", "no-double-colon-form", "missing-object-list")
CAUSE = "expected object names"
NAME_CAUSE = "Invalid character in name at (1)"
NEWLINE_CAUSE = "Newline is unexpected here"
CAUSES = {
    "no_colon": (CAUSE, NAME_CAUSE),
    "double_colon": (CAUSE, NAME_CAUSE, NEWLINE_CAUSE),
}
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "cannot read module", "missing interface", "unexpected end", "missing end",
)
ORACLE_PREFIX = "R839 finite missing-list matrix: "
LIMIT_PREFIX = "R839 finite missing-list boundaries: "
ORACLE = ORACLE_PREFIX + (
    "four complete module compile/f2023 fixtures use one separately declared ordinary "
    "INTEGER,POINTER subject(:). Each negative has a standalone CONTIGUOUS or CONTIGUOUS :: "
    "statement with no object-name list. Its sole repair inserts ' subject' at the end of that "
    "same physical statement, retaining the chosen separator form and every other byte. The "
    "two distinct compile positive controls name that actual rank-one deferred-shape array "
    "pointer, independently satisfying C830/C834, through the sole explicit CONTIGUOUS route. "
    "R401 requires a nonempty list; explicit R804/C810, not an assumed R402 production, owns "
    "the data-object name. Reporting is qualified by the forbidden form in this complete "
    "source/control context, not by a required diagnostic vocabulary. At the actual staged "
    "listless statement on line4, the exact 'expected object names' and 'Invalid character "
    "in name at (1)' messages identify the absent first name. The latter is the expected-name "
    "parser's end-of-statement failure here, not a separate illegal character elsewhere. "
    "Only the double-colon negative also admits the exact 'Newline is unexpected here' cause: "
    "its terminator immediately follows the valid CONTIGUOUS :: prefix where that first name "
    "is mandatory. Full-message and live-origin predicates remain case-specific. No "
    "lookahead/EOF point, widened interval or additional span is used. Each one-insertion "
    "control must produce its object; no link or runtime operation is requested."
)
LIMITATION = LIMIT_PREFIX + (
    "only double-colon-form, no-double-colon-form and missing-object-list are represented. "
    "Both missing-list alternatives have their own complete negative and distinct repair; "
    "controls carry their form facet and missing-object-list as compile positive controls. "
    "The other facet plans and raw source/fixture/evidence states remain independently managed. "
    "The source has no malformed declaration, invalid subject category or missing END MODULE; "
    "the first missing object name is the sole defect. These condition-bound causes do not "
    "license arbitrary name/newline tokens or an error elsewhere. In particular, the bare-form "
    "'Attribute declaration not supported yet' report remains unqualified, and the newline "
    "alternative is not enabled for that form. Unlisted messages, fragments, quoted/echoed "
    "causes, context-only or malformed locations, foreign origins, EOF/missing-END reports, "
    "unsupported features and native/internal/resource failures do not qualify. Reporting "
    "capability does not mandate fatal status, fixed English or printed R839, and no "
    "unobserved warning allowance is introduced. Effective source/case reviews and current "
    "fingerprint-, phase- and mode-bound observations determine qualification; f2018 evidence "
    "cannot substitute for f2023 corroboration. Historical verdicts belong to their immutable "
    "dated reports, not regenerated present-state assertions. There is no pointer initialization, "
    "association inquiry, payload access, allocation, call, runtime contiguity, layout, descriptor "
    "or strategy oracle. Existing C830 and S8.5.7-001 witnesses retain their type-declaration "
    "occurrences, owners, roles, fingerprints, reviews and historical failures/ICEs or UNTESTED "
    "plans. Generation alone grants no approval, baseline update or new C830/runtime/link/"
    "SourceUses credit."
)
SUMMARY_BEGIN = "<!-- BEGIN CONTIGUOUS STATEMENT SYNTAX -->"
SUMMARY_END = "<!-- END CONTIGUOUS STATEMENT SYNTAX -->"


def identifier(form, invalid=False):
    return "R839_" + ("invalid" if invalid else "valid") + "__contiguous_" + form + (
        "_missing_list" if invalid else "_control")


def source_specs():
    prefix = ("module contiguous_statement_syntax_scope\n"
              "  implicit none\n"
              "  integer, pointer :: subject(:)\n")
    suffix = "\nend module contiguous_statement_syntax_scope\n"
    result = {}
    for form, facet in FORMS.items():
        statement = "  contiguous" + (" ::" if form == "double_colon" else "")
        invalid_raw = (prefix + statement + suffix).encode("ascii")
        insertion = len((prefix + statement).encode("ascii"))
        control_raw = invalid_raw[:insertion] + b" subject" + invalid_raw[insertion:]
        for invalid, raw in ((True, invalid_raw), (False, control_raw)):
            name = identifier(form, invalid)
            spec = dict(
                id=name, form=form, variant=form + ("_invalid" if invalid else "_control"),
                kind="invalid" if invalid else "valid",
                evidence="effect" if invalid else "positive-control",
                facets=["missing-object-list"] if invalid else [facet, "missing-object-list"],
                source=raw.decode(), source_sha256=sha(raw))
            if invalid:
                spec["repair"] = dict(
                    span=[insertion, insertion], removed="", replacement=" subject", line=4,
                    control_id=identifier(form), control_sha256=sha(control_raw),
                    all_other_bytes_unchanged=True)
            result[name] = spec
    return result


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        invalid = spec["kind"] == "invalid"
        manifest = dict(
            schema_version=1, id=spec["id"], rule=RULE, facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", step="source", outcome="diagnose" if invalid else "success"))
        if invalid:
            manifest["expect"]["diagnostic"] = dict(
                file="source.f90", line=4, end_line=4, equals_any=list(CAUSES[spec["form"]]),
                excludes_any=list(EXCLUSIONS) + ([NEWLINE_CAUSE] if spec["form"] == "no_colon" else []))
        relative = "tests/fixtures/contiguous_statement_syntax_" + spec["variant"]
        directory = Path(root) / relative
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        spec["path"], spec["manifest"] = relative + "/fixture.json", manifest
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    matches = [row for row in updated["requirements"] if row["id"] == RULE]
    if (updated["section"] != SECTION or len(matches) != 1
            or not set(FACETS) <= set(matches[0]["facets"])
            or matches[0]["category"] != "syntax" or matches[0]["diagnostic_obligation"] != "required"):
        raise ValueError("the selected R839 source/facet definitions changed")
    owner = matches[0]
    for facet in FACETS:
        owner["pending"].pop(facet, None)
    owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE)
    limitation = owner.get("oracle_limitation", "")
    legacy_prefix = "All facets are pending. "
    if limitation.startswith(legacy_prefix):
        limitation = limitation[len(legacy_prefix):]
    owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the CONTIGUOUS statement generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Finite standalone missing-list matrix\n\n"
        "Four complete module compile/f2023 cases preserve one ordinary rank-one\n"
        "INTEGER pointer declaration. Bare CONTIGUOUS and CONTIGUOUS :: each lack\n"
        "the required object-name list; inserting only ` subject` produces their\n"
        "respective valid standalone-statement controls. No type-declaration\n"
        "CONTIGUOUS, initializer, pointer inquiry, payload, call, link or run is used.\n\n"
        "Qualification follows the fixed source/control context and actual line4\n"
        "origin, not one compiler's vocabulary. Exact missing-object-names and\n"
        "expected-name-parser messages report the same absent first name. Only the\n"
        "double-colon negative also admits its exact premature-newline report.\n"
        "The bare-form unsupported-declaration report remains unqualified. No\n"
        "loose name/newline token matching, extra span, context-only attribution,\n"
        "fatal-status, printed-code or unmeasured warning policy is added.\n\n"
        "Only the two form facets and missing-object-list are represented. Other\n"
        "facet states, the source/case/inventory adjudications, and all historical\n"
        "C830/S8.5.7 owners and observations stay separate. Generation or registration\n"
        "alone grants no approval: effective source/case reviews and current bound\n"
        "observations determine status. Historical verdicts remain in immutable\n"
        "dated reports. Declaration admission is not runtime contiguity evidence.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the CONTIGUOUS statement summary boundaries changed")
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
            raise ValueError("stale CONTIGUOUS statement matrix: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} R839 compile cases, "
          "two statement forms and both missing-list repairs.")


if __name__ == "__main__":
    main()
