#!/usr/bin/env python3
"""Ten bounded C814 compile cases with SAVE-only repairs and constant/no-list admissions."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from generate_type_parameter_entry_fixtures import build_corpus as entry_corpus
from generate_type_parameter_entry_fixtures import render_view as entry_view

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "doc/catalogues/automatic_data_objects_8_3.json"
VIEW = "doc/fortran_2023_8_3.md"
FACETS = ["character-selector-save", "character-entity-length-save", "explicit-bound-save",
          "constant-specification-admission", "bare-save-admission"]
NEGATIVE_FORMS = {
    "character_selector": dict(facet="character-selector-save", declaration="character(len=n), save :: text",
                               body="text='x'", subject="text",
                               premise="Nondummy local CHARACTER length from a previously typed nonoptional INTEGER INTENT(IN) n."),
    "character_entity": dict(facet="character-entity-length-save", declaration="character, save :: text*(n)",
                             body="text='x'", subject="text",
                             premise="The same nonconstant CHARACTER premise through R723's parenthesized individual length *(n)."),
    "explicit_bound": dict(facet="explicit-bound-save", declaration="integer, save :: a(n)",
                           body="a=1", subject="a",
                           premise="Ordinary nondummy INTEGER explicit-shape local a(n), with no initializer, pointer or allocatable attribute."),
}
CAUSES = {
    "character_selector": [
        "Automatic object 'text' at (1) cannot have the SAVE attribute",
        "The automatic object 'text' may not have an explicit SAVE attribute",
    ],
    "character_entity": [
        "Automatic object 'text' at (1) cannot have the SAVE attribute",
        "The automatic object 'text' may not have an explicit SAVE attribute",
    ],
    "explicit_bound": [
        "Automatic object 'a' at (1) cannot have the SAVE attribute",
        "The automatic object 'a' may not have an explicit SAVE attribute",
    ],
}
NONFATAL = {}
EXCLUSIONS = ["not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
              "must be a dummy", "function result", "implicit type", "missing interface", "initialization", "initializer",
              "malformed", "syntax error", "internal error", "internal:", "verifier", "out of memory", "recovery"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, negative=False):
    return "C814_" + ("invalid" if negative else "valid") + "__automatic_save_" + variant


def source_specs():
    result = {}
    for variant, form in NEGATIVE_FORMS.items():
        source = (f"subroutine {variant}(n)\nimplicit none\ninteger, intent(in) :: n\n"
                  + form["declaration"] + "\n" + form["body"] + f"\nend subroutine {variant}\n")
        raw = source.encode("ascii")
        declaration = source.splitlines()[3]
        offset = sum(len(line) for line in raw.splitlines(keepends=True)[:3]) + declaration.index(", save")
        deletion = b", save"
        assert raw[offset:offset + len(deletion)] == deletion and source.count(", save") == 1
        control = raw[:offset] + raw[offset + len(deletion):]
        negative = identifier(variant, True)
        positive = identifier(variant + "_control")
        repair = dict(negative_id=negative, control_id=positive, line=4,
                      first_column=declaration.index(", save") + 1,
                      last_column=declaration.index(", save") + len(deletion),
                      byte_span_zero_based_half_open=[offset, offset + len(deletion)],
                      deleted=deletion.decode(), only_SAVE_and_comma_deleted=True,
                      all_other_source_bytes_unchanged=True)
        for name, text, kind in ((negative, source, "invalid"), (positive, control.decode(), "valid")):
            result[name] = dict(
                id=name, variant=variant + ("" if kind == "invalid" else "_control"), kind=kind,
                facet=form["facet"], source=text, subject=form["subject"], source_sha256=sha(text.encode()),
                premise=form["premise"], automatic=True, repair=repair,
                expected_phase="compile", standard="f2023", evidence="effect" if kind == "invalid" else "positive-control")
    admissions = {
        "parameter_constant": (
            "subroutine parameter_constant()\nimplicit none\ninteger, parameter :: extent=3\n"
            "integer, save :: a(extent)\na=1\nend subroutine parameter_constant\n",
            "Prior INTEGER PARAMETER extent=3 supplies a constant explicit bound. SAVE is on the ordinary local a, not extent."),
        "len_constant": (
            "subroutine len_constant()\nimplicit none\ncharacter(len=3) :: basis\n"
            "character(len=len(basis)), save :: text\ntext='abc'\nend subroutine len_constant\n",
            "LEN queries previously declared fixed CHARACTER length3, not basis's undefined payload; it is a constant specification inquiry."),
        "size_constant": (
            "subroutine size_constant()\nimplicit none\ninteger :: basis(3)\n"
            "integer, save :: a(size(basis))\na=1\nend subroutine size_constant\n",
            "SIZE queries previously declared ordinary fixed-shape basis(3), not its undefined elements; it is a constant specification inquiry."),
    }
    for variant, (source, premise) in admissions.items():
        name = identifier(variant)
        result[name] = dict(id=name, variant=variant, kind="valid", facet="constant-specification-admission",
                            source=source, source_sha256=sha(source.encode()), premise=premise, automatic=False,
                            expected_phase="compile", standard="f2023", evidence="positive-control")
    source = ("subroutine bare_save(n)\nimplicit none\ninteger, intent(in) :: n\n"
              "character(len=n) :: text\nsave\ntext='x'\nend subroutine bare_save\n")
    name = identifier("bare_save")
    result[name] = dict(
        id=name, variant="bare_save", kind="valid", facet="bare-save-admission",
        source=source, source_sha256=sha(source.encode()), automatic=True,
        premise="One no-list SAVE in a procedure, no other SAVE specification. Allowed-item filtering excludes both "
                "the dummy n and the automatic text; no claim that either is saved and no BLOCK or runtime retention observer.",
        expected_phase="compile", standard="f2023", evidence="positive-control")
    if len(result) != 10 or sum(spec["kind"] == "invalid" for spec in result.values()) != 3:
        raise ValueError("the exact three-negative/seven-control source partition changed")
    return result


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = "tests/fixtures/automatic_save_" + spec["variant"] + ("_invalid" if spec["kind"] == "invalid" else "")
        manifest = dict(
            schema_version=1, id=name, rule="C814", facets=[spec["facet"]], standard="f2023", evidence=spec["evidence"],
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", outcome="diagnose" if spec["kind"] == "invalid" else "success", step="source"))
        if spec["kind"] == "invalid":
            if spec["variant"] not in CAUSES or not CAUSES[spec["variant"]]:
                raise ValueError("native diagnostic calibration is required before writing the C814 fixture contracts")
            diagnostic = dict(file="source.f90", line=4, end_line=4,
                              contains_any=list(CAUSES[spec["variant"]]), excludes_any=list(EXCLUSIONS))
            if NONFATAL.get(spec["variant"]):
                diagnostic["allow_nonfatal"] = copy.deepcopy(NONFATAL[spec["variant"]])
            manifest["expect"]["diagnostic"] = diagnostic
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode()
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(item for item in result["requirements"] if item["id"] == "C814")
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
        raise ValueError("unselected C814 plans must remain pending")
    original = requirement["oracle"].split("\n\nBounded automatic-SAVE implementation:", 1)[0]
    requirement["oracle"] = original + (
        "\n\nBounded automatic-SAVE implementation: ten compile/f2023 fixtures represent five selected facets. "
        "Three complete procedures put SAVE on a nondummy automatic CHARACTER selector-length local, a CHARACTER "
        "individual *(n) local, and an ordinary INTEGER a(n), with previously typed nonoptional INTEGER INTENT(IN) n. "
        "Their exact controls delete only ', save', retaining the same automatic local, dummy and executable body. "
        "Three distinct constant-specification controls use a prior INTEGER PARAMETER, LEN of a previously fixed-length "
        "CHARACTER object, or SIZE of a previously fixed-shape ordinary INTEGER array; neither inquiry reads payload. "
        "The seventh positive control has one no-list SAVE in a procedure: allowed-item filtering excludes the automatic "
        "local, without a retention claim. Reporting uses actual located automatic-object/SAVE causes, permits ordinary "
        "zero/nonzero and qualified nonfatal reporting, and requires no printed rule code or fatal-return policy.")
    requirement["oracle_limitation"] = (
        "Four C814 facets remain pending: PDT length, fixed-length ALLOCATABLE, fixed-length POINTER, and "
        "inquiry-dependent-bound negatives. The three selected controls remain automatic locals, not dummies, results "
        "or constants. No declaration initialization, pointer/allocatable/deferred/assumed shape, BLOCK no-list SAVE, "
        "retention run, bound/parameter-capture effect or definition-use credit is added. Fixed LEN/SIZE inquiry arguments "
        "have known declared properties; their uninitialized payload is never read. Bare SAVE/nonconstant words, echoes, "
        "wrong entities/attributes, malformed suffixes, unrelated initializer/eligibility/interface errors, unsupported/"
        "unimplemented facilities, Internal/verifier/resource failures and recovery do not corroborate C814. "
        "Generation preserves independent source/case/inventory adjudications; representation and processor agreement "
        "are not approval, and actual unsupported/reference failures remain recorded observations.")
    return result


def render_view(catalogue):
    return entry_view(catalogue, entry_corpus()[1])


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
    actual = {path for path in (ROOT / "tests/fixtures").glob("automatic_save_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale automatic-SAVE subset: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded automatic-SAVE corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for ten compile cases: three negatives, seven controls, five facets.")


if __name__ == "__main__":
    main()
