#!/usr/bin/env python3
"""Two NAME-presence violations with one byte-identical shared repair."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.6.4"
RULE = "C877"
CATALOGUE = "doc/catalogues/bind_statement_8_6_4.json"
VIEW = "doc/fortran_2023_8_6_4.md"
FACETS = ("two-variables-empty-name", "blank-name-still-conditional")
CAUSE = "Multiple identifiers provided with single NAME= specifier at (1)"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "cannot read module", "missing interface", "syntax error", "malformed",
)
ORACLE_PREFIX = "C877 finite empty-label cardinality family: "
LIMIT_PREFIX = "C877 finite empty-label cardinality boundaries: "
ORACLE = ORACLE_PREFIX + (
    "two complete module compile/f2023 negatives use BIND(C,NAME='') or BIND(C,NAME='   ') "
    "on the same two ordinary scalar INTEGER(C_INT) variables. C_INT is imported from the intrinsic "
    "ISO_C_BINDING module and is guaranteed by18.2.2p3; no numeric kind value is assumed. The sole "
    "repair deletes the comma-NAME clause in each source, producing the same complete BIND(C) "
    "module byte-for-byte. One shared compile/positive-control fixture therefore supports both "
    "exclusion facets without duplicated execution. NAME presence, not a nonempty trimmed label, "
    "activates C877. Empty and all-blank values avoid a competing shared nonempty global label. "
    "The complete calibrated multiple-identifiers/single-NAME cause must be reported at the actual "
    "staged BIND statement on line5. The control must produce an object; no link or run is part of "
    "the contract."
)
LIMITATION = LIMIT_PREFIX + (
    "only two-variables-empty-name and blank-name-still-conditional are represented. All "
    "other C877 facets and every R835/R836, source/use and review state remain independently "
    "managed. A common block, nonempty binding label, procedure/type BIND form, C companion, "
    "symbol name, storage layout, runtime value or SAVE effect is not tested. The module identifier "
    "and two repaired default labels are distinct. Neither variable is initialized, PARAMETER, "
    "POINTER, ALLOCATABLE, a coarray or a COMMON member. No optional kind/profile gate is "
    "introduced. Reporting capability does not require fatal status, standard English or a printed "
    "C877; this exact measured cause is a finite calibration route, not a vocabulary policy. No "
    "warning allowance, widened/additional source interval, generic NAME/identifier message, "
    "duplicate-label report, source echo, quoted example, foreign origin, unsupported feature "
    "or native compiler failure qualifies. Silent target/reference acceptance remains a failure; "
    "actual Flangf2018 evidence is supplementary rather than f2023 validation. Generation "
    "grants no source/case/link/inventory approval or baseline update."
)
SUMMARY_BEGIN = "<!-- BEGIN BIND NAME CARDINALITY -->"
SUMMARY_END = "<!-- END BIND NAME CARDINALITY -->"


def identifier(variant):
    names = {
        "empty": "C877_invalid__bind_empty_name_two_variables",
        "blank": "C877_invalid__bind_blank_name_two_variables",
        "control": "C877_valid__bind_no_name_shared_control",
    }
    return names[variant]


def source_specs():
    prefix = (
        "module bind_name_cardinality_scope\n"
        "  use, intrinsic :: iso_c_binding, only: c_int\n"
        "  implicit none\n"
        "  integer(c_int) :: first_value, second_value\n")
    suffix = " :: first_value, second_value\nend module bind_name_cardinality_scope\n"
    control = (prefix + "  bind(c)" + suffix).encode("ascii")
    result = {}
    for variant, literal, facet in (("empty", "", FACETS[0]), ("blank", "   ", FACETS[1])):
        removed = (", name='" + literal + "'").encode("ascii")
        raw = (prefix + "  bind(c").encode("ascii") + removed + (")" + suffix).encode("ascii")
        start = len((prefix + "  bind(c").encode("ascii"))
        end = start + len(removed)
        assert raw[:start] + raw[end:] == control
        name = identifier(variant)
        result[name] = dict(
            id=name, variant=variant, kind="invalid", evidence="effect", facets=[facet],
            source=raw.decode(), source_sha256=sha(raw), name_value=literal,
            repair=dict(span=[start, end], removed=removed.decode(), replacement="",
                        line=5, control_id=identifier("control"), control_sha256=sha(control),
                        all_other_bytes_unchanged=True))
    result[identifier("control")] = dict(
        id=identifier("control"), variant="control", kind="valid", evidence="positive-control",
        facets=list(FACETS), source=control.decode(), source_sha256=sha(control),
        shared_by=[identifier("empty"), identifier("blank")])
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
                file="source.f90", line=5, end_line=5, equals_any=[CAUSE], excludes_any=list(EXCLUSIONS))
        relative = "tests/fixtures/bind_name_cardinality_" + spec["variant"]
        directory = Path(root) / relative
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        spec["path"], spec["manifest"] = relative + "/fixture.json", manifest
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    matches = [row for row in updated["requirements"] if row["id"] == RULE]
    if len(matches) != 1 or not set(FACETS) <= set(matches[0]["facets"]):
        raise ValueError("the selected C877 facet definitions changed")
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
        raise ValueError("the BIND statement generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Finite empty/blank NAME cardinality family\n\n"
        "Two complete module negatives bind the same two ordinary INTEGER(C_INT)\n"
        "variables with an empty or all-blank NAME value. Both still contain a\n"
        "NAME specifier, although neither supplies a nonempty binding label.\n"
        "Deleting only the comma-NAME clause produces one byte-identical shared\n"
        "control with no NAME. The single control is registered and compiled once\n"
        "per configuration; it is not cloned to support the second negative.\n\n"
        "The exact multiple-identifiers/single-NAME report must originate from\n"
        "the actual staged BIND statement on line5. The positive control must\n"
        "produce an object. Generic identifier/label errors, source echoes, quoted\n"
        "examples, unrelated origins, silence, unsupported features and compiler\n"
        "failures do not satisfy the contract. There is no fatal-status, printed\n"
        "rule-code, compulsory English or unmeasured warning policy.\n\n"
        "Only the two selected C877 pending entries and bounded oracle paragraphs\n"
        "are generator-owned. Every other facet, source/role and review state\n"
        "remains independently managed. No COMMON, nonempty label, C companion,\n"
        "symbol/layout, runtime value, SAVE, canonical link or source-use evidence\n"
        "is added; actual f2018 evidence is not relabelled as f2023.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the BIND cardinality summary boundaries changed")
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
            raise ValueError("stale BIND NAME cardinality family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} C877 compile cases, "
          "two exclusion facets and one shared control.")


if __name__ == "__main__":
    main()
