#!/usr/bin/env python3
"""Two finite assumed-rank restrictions with single-site conforming repairs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.8.7"
CATALOGUE = "doc/catalogues/assumed_rank_8_5_8_7.json"
VIEW = "doc/fortran_2023_8_5_8_7.md"
SCOPES = {
    "local": ("C839", "ordinary-local-excluded", 3),
    "expression": ("C840", "data-expression-excluded", 10),
}
CAUSES = {
    "local": (
        "Assumed-rank variable 'subject' must be a dummy argument.",
        "Assumed-rank array at (1) must be a dummy argument",
        "Assumed-rank array 'subject' must be a dummy argument",
    ),
    "expression": (
        "Assumed-rank arrays are not supported in print statements",
        "Assumed-rank variable x at (1) may only be used as actual argument",
    ),
}
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "internal:", "internal error",
    "asr", "verifier", "out of memory", "recovery", "cannot read module", "missing interface",
    "syntax error", "malformed",
)
SUMMARY_BEGIN = "<!-- BEGIN ASSUMED RANK USAGE -->"
SUMMARY_END = "<!-- END ASSUMED RANK USAGE -->"
ORACLES = {
    "C839": (
        "a complete external subroutine declares ordinary INTEGER subject(..) without a dummy "
        "argument. Its sole repair inserts subject into the existing empty dummy list, preserving "
        "every other byte. Both cases contain no executable operation or competing attribute. "
        "The invalid requires a located complete assumed-rank/nondummy cause at the actual staged "
        "declaration on line3; the repair must produce an object and remains a compile positive control."
    ),
    "C840": (
        "a complete program passes a defined ordinary INTEGER scalar to an internal explicit-interface "
        "INTEGER INTENT(IN) x(..) observer. Direct PRINT of x on line10 is repaired only to PRINT of "
        "RANK(x), preserving the declaration, caller and all other bytes. The invalid requires a "
        "complete prohibited assumed-rank-use cause at that actual staged output-list item; the "
        "repair must produce an object and remains a compile positive control. Direct RANK(x) uses "
        "the first inquiry dummy, not a fixed-rank observer or a constructor. The measured target "
        "message names precisely the assumed-rank PRINT prohibition. Its exact phrase containing "
        "'not supported' is not generalized into permission for generic unimplemented-feature reports."
    ),
}
LIMITATION = (
    "only the selected exclusion facet is represented, not the whole constraint or every admitted "
    "dummy/use category. Other pending facets, oracle paragraphs, control designations and raw review "
    "states remain independently managed. C839 dummy-admission and C840 first-inquiry-dummy plans "
    "remain separate: the two repairs do not close their broader attribute/state matrices. No new "
    "runtime RANK, output-value, payload, shape/bounds, VALUE, C/coarray, SELECT RANK, canonical reuse "
    "or SourceUses credit is created. Reporting capability prescribes neither fatal status, printed "
    "rule identifiers nor standardized English. Exact calibrated causes admit ordinary error reports "
    "even with status0, but no warning/portability allowance is invented. Silence, generic feature "
    "unavailability, wrapped or quoted examples, source echoes, wrong subjects/files/lines, parser "
    "recovery and Internal/ASR/crash/resource failures do not qualify. Real reference failures remain "
    "failures; Flang's actual f2018 observations are never relabelled as f2023. Generation approves "
    "nothing and never changes reviews, links, SourceUses, the execution inventory or baseline."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, invalid=False):
    return SCOPES[variant][0] + ("_invalid" if invalid else "_valid") + "__assumed_rank_" + variant + (
        "" if invalid else "_control")


def source_specs():
    originals = {
        "local": (
            "subroutine assumed_rank_local_context()\n"
            "  implicit none\n"
            "  integer :: subject(..)\n"
            "end subroutine assumed_rank_local_context\n"),
        "expression": (
            "program assumed_rank_expression_context\n"
            "  implicit none\n"
            "  integer :: subject\n"
            "  subject=7\n"
            "  call observe(subject)\n"
            "contains\n"
            "  subroutine observe(x)\n"
            "    implicit none\n"
            "    integer, intent(in) :: x(..)\n"
            "    print *, x\n"
            "  end subroutine observe\n"
            "end program assumed_rank_expression_context\n"),
    }
    specs = {}
    for variant, text in originals.items():
        raw = text.encode("ascii")
        if variant == "local":
            prefix = b"subroutine assumed_rank_local_context("
            start = len(prefix)
            old, new = b"", b"subject"
            assert raw.startswith(prefix + b")\n")
            repair_line = 1
        else:
            prefix = b"    print *, "
            assert raw.count(prefix + b"x\n") == 1
            start = raw.index(prefix) + len(prefix)
            old, new = b"x", b"rank(x)"
            repair_line = 10
        end = start + len(old)
        assert raw[start:end] == old
        fixed = raw[:start] + new + raw[end:]
        repair = dict(
            span=[start, end], old=old.decode(), replacement=new.decode(), line=repair_line,
            negative_id=identifier(variant, True), control_id=identifier(variant),
            negative_sha256=sha(raw), control_sha256=sha(fixed), all_other_bytes_unchanged=True)
        rule, facet, line = SCOPES[variant]
        for invalid, data in ((True, raw), (False, fixed)):
            name = identifier(variant, invalid)
            specs[name] = dict(
                id=name, rule=rule, variant=variant, kind="invalid" if invalid else "valid",
                facets=[facet], evidence="effect" if invalid else "positive-control",
                source=data.decode(), source_sha256=sha(data), diagnostic_line=line, repair=repair,
                subject="subject" if variant == "local" else "x",
                directory="tests/fixtures/assumed_rank_usage_" + variant + ("_invalid" if invalid else "_control"))
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        invalid = spec["kind"] == "invalid"
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", step="source", outcome="diagnose" if invalid else "success"))
        if invalid:
            manifest["expect"]["diagnostic"] = dict(
                file="source.f90", line=spec["diagnostic_line"], end_line=spec["diagnostic_line"],
                equals_any=list(CAUSES[spec["variant"]]), excludes_any=list(EXCLUSIONS))
        directory = Path(root) / spec["directory"]
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        spec["manifest"], spec["path"] = manifest, spec["directory"] + "/fixture.json"
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    for rule, facet, _ in SCOPES.values():
        matches = [row for row in updated["requirements"] if row["id"] == rule]
        if len(matches) != 1 or facet not in matches[0]["facets"]:
            raise ValueError("the selected assumed-rank usage requirement/facet definition changed")
        row = matches[0]
        row["pending"].pop(facet, None)
        for field, label, text in (("oracle", "oracle", ORACLES[rule]),
                                   ("oracle_limitation", "boundaries", LIMITATION)):
            prefix = rule + " finite assumed-rank usage " + label + ": "
            row[field] = owned_paragraph(row.get(field, ""), prefix, prefix + text)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the assumed-rank generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Finite local-role and output-list restrictions\n\n"
        "Four compile/f2023 cases form two single-site diagnostic/positive-control\n"
        "pairs. C839's ordinary local declaration is repaired only by inserting\n"
        "the entity into the dummy list. C840's direct `PRINT *, x` in a complete\n"
        "internal assumed-rank observer is repaired only to `PRINT *, RANK(x)`.\n"
        "The defined scalar caller, dummy declaration and remaining source stay\n"
        "unchanged. Both controls must produce objects; neither is a runtime effect.\n\n"
        "Exact calibrated causes bind the actual staged declaration on line3 or\n"
        "output-list item on line10. The target's exact assumed-rank PRINT\n"
        "prohibition is distinguished from a generic unsupported-feature report,\n"
        "even though that complete diagnostic uses the words `not supported`.\n"
        "No fatal status, printed code, mandatory English or unmeasured warning\n"
        "allowance is imposed. Echoes, quoted examples, wrong origins, silent\n"
        "acceptance and compiler failures cannot supply the required cause.\n\n"
        "Only the two selected C839/C840 pending entries and bounded oracle\n"
        "paragraphs are owned by this generator. Broader dummy-admission and\n"
        "first-inquiry matrices retain their independent states. Existing rank\n"
        "runtime effects, other source owners, roles and raw reviews are preserved.\n"
        "No runtime, shape/bounds, VALUE, interoperability, canonical-link or\n"
        "source-use coverage or approval is supplied by these compile repairs.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the assumed-rank usage summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        offset = before.find("<!-- BEGIN ")
        offset = len(before) if offset < 0 else offset
        before = before[:offset].rstrip() + "\n\n" + summary + "\n\n" + before[offset:]
    return (before + begin + "\n\n"
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
            raise ValueError("stale assumed-rank usage family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} assumed-rank compile cases and two exclusion facets.")


if __name__ == "__main__":
    main()
