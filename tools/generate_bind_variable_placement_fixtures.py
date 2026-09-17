#!/usr/bin/env python3
"""Seven compile-only C819 cases with exact BIND(C)-and-comma repairs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.5"
RULE = "C819"
CATALOGUE = "doc/catalogues/bind_attribute_data_entities_8_5_5.json"
VIEW = "doc/fortran_2023_8_5_5.md"
FACETS = ("module-admission", "main-local", "external-procedure-local", "contained-procedure-local")
CONTEXTS = {
    "main_local": "main-local",
    "external_local": "external-procedure-local",
    "contained_local": "contained-procedure-local",
}
CAUSES = (
    "Variable 'bound_value' at (1) cannot be BIND(C) because it is neither a COMMON block nor declared at the module level scope",
    "A variable with BIND(C) attribute may only appear in the specification part of a module",
)
NONFATAL = ()
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "dummy", "function result", "procedure name", "named constant", "common member",
    "pointer", "allocatable", "coarray", "kind", "implicit type", "missing interface",
    "initialization", "initializer", "syntax error", "malformed",
)
DECLARATION = "integer(c_int), bind(c) :: bound_value"
IMPORT = "use, intrinsic :: iso_c_binding, only: c_int"
ORACLE = (
    "Seven complete compile/f2023 fixtures represent module-admission, main-local, external-procedure-local "
    "and contained-procedure-local. A proper module specification-part admits one ordinary scalar "
    "INTEGER(C_INT),BIND(C) variable. Three negatives declare that same eligible variable in a main program, "
    "an external subroutine and a module-contained subroutine's own specification-part. Each control deletes "
    "only ', bind(c)', preserving every other byte, including the local entity, intrinsic USE, type, rank, "
    "executable assignment and complete outer context. Admission requires successful object compilation; "
    "the controls are positive-control evidence, not runtime effects. A negative requires an actual located "
    "BIND-variable/module-declaration-context report at its sole entity declaration. Ordinary zero/nonzero "
    "and specifically qualified nonfatal reporting may satisfy that capability; neither fatal rejection, "
    "a printed C819 code nor generic keyword output is required or sufficient."
)
LIMITATION = (
    "Submodule placement, common-placement source-use and interface/result/dummy source-use remain pending. "
    "All six other 8.5.5 requirements and their plans are preserved. Prior intrinsic ISO_C_BINDING makes "
    "the guaranteed C_INT kind accessible in the actual declaring scope. Each variable is scalar, "
    "noncoarray, nonpointer, nonallocatable, nondummy and not a function result or named constant, with no "
    "initializer or duplicate binding. Under 18.3.1/18.3.5 its type and parameters are interoperable; "
    "18.9.1p4 requires no associated C entity. No kind code, width, ABI, foreign counterpart, link, "
    "runtime retention, module SAVE or S8.5.5-002 effect is observed. Wrong entity/type/kind/attribute, "
    "missing module/interface, malformed declaration, source echo, bare BIND/module words, unsupported/"
    "unimplemented recovery, Internal/ASR/verifier, crash, resource and timeout failures are noncredit. "
    "A literal predicate without a supported causal report remains unqualified, not compiler-consensus "
    "proof. Source, fixture, observational-inventory and processor-mode qualification remain independent; "
    "generation preserves their administrative records without renewing them."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, negative=False):
    return RULE + ("_invalid" if negative else "_valid") + "__bind_variable_placement_" + variant


def source_specs():
    sources = {
        "main_local": (
            f"program main_local\n  {IMPORT}\n  implicit none\n  {DECLARATION}\n"
            "  bound_value=1_c_int\nend program main_local\n"),
        "external_local": (
            f"subroutine external_local()\n  {IMPORT}\n  implicit none\n  {DECLARATION}\n"
            "  bound_value=1_c_int\nend subroutine external_local\n"),
        "contained_local": (
            "module placement_host\n  implicit none\ncontains\n  subroutine contained_local()\n"
            f"    {IMPORT}\n    implicit none\n    {DECLARATION}\n"
            "    bound_value=1_c_int\n  end subroutine contained_local\nend module placement_host\n"),
    }
    specs = {}
    for variant, source in sources.items():
        raw = source.encode("ascii")
        deletion = b", bind(c)"
        if raw.count(deletion) != 1:
            raise ValueError("each negative must have exactly one variable BIND(C) specification")
        start = raw.index(deletion)
        end = start + len(deletion)
        line = raw[:start].count(b"\n") + 1
        first_column = start - raw.rfind(b"\n", 0, start)
        repaired = raw[:start] + raw[end:]
        negative, control = identifier(variant, True), identifier(variant + "_control")
        repair = dict(
            negative_id=negative, control_id=control, line=line,
            first_column=first_column, last_column=first_column + len(deletion) - 1,
            byte_span_zero_based_half_open=[start, end], deleted=deletion.decode(),
            negative_sha256=sha(raw), control_sha256=sha(repaired),
            only_BIND_C_and_separator_deleted=True, all_other_source_bytes_unchanged=True)
        for name, text, invalid in ((negative, source, True), (control, repaired.decode(), False)):
            specs[name] = dict(
                id=name, variant=variant + ("" if invalid else "_control"),
                kind="invalid" if invalid else "valid", facet=CONTEXTS[variant],
                declaration_line=line, source=text, source_sha256=sha(text.encode()),
                subject="bound_value", context=variant, repair=repair,
                standard="f2023", evidence="effect" if invalid else "positive-control")
    source = f"module module_admission\n  {IMPORT}\n  implicit none\n  {DECLARATION}\nend module module_admission\n"
    name = identifier("module_admission")
    specs[name] = dict(
        id=name, variant="module_admission", kind="valid", facet="module-admission",
        declaration_line=4, source=source, source_sha256=sha(source.encode()),
        subject="bound_value", context="module-specification-part",
        standard="f2023", evidence="positive-control")
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        invalid = spec["kind"] == "invalid"
        directory = "tests/fixtures/bind_variable_placement_" + spec["variant"] + ("_invalid" if invalid else "")
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=[spec["facet"]], standard="f2023",
            evidence=spec["evidence"], files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", outcome="diagnose" if invalid else "success", step="source"))
        if invalid:
            if not CAUSES:
                raise ValueError("native causal-diagnostic calibration is required before writing C819 contracts")
            diagnostic = dict(file="source.f90", line=spec["declaration_line"], end_line=spec["declaration_line"],
                              contains_any=list(CAUSES), excludes_any=list(EXCLUSIONS))
            if NONFATAL:
                diagnostic["allow_nonfatal"] = copy.deepcopy(list(NONFATAL))
            manifest["expect"]["diagnostic"] = diagnostic
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(item for item in result["requirements"] if item["id"] == RULE)
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
        raise ValueError("unselected C819 facets must retain their pending plans")
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
        raise ValueError("the native 8.5.5 generated-region boundary changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    authority = "Source: original J3/24-007"
    if before.count(authority) != 1:
        raise ValueError("the original 8.5.5 authority/qualification boundary changed")
    preserved = authority + before.split(authority, 1)[1]
    history = "The base for this packet is the committed `39bbf4ca` corpus"
    if history in preserved:
        preserved = preserved.split(history, 1)[0]
    current_history = "The original source-only integration is recorded in batch032."
    if current_history in preserved:
        preserved = preserved.split(current_history, 1)[0]
    header = (
        "# Fortran 2023 8.5.5: BIND attribute for data entities\n\n"
        f"**Source review: {state}.** Effective content-bound status is computed by\n"
        '`Registry.catalogue_review_state("8.5.5")`, not the raw review field.\n'
        "The independent source gate in `doc/source_audits/batch_032.json` is historical;\n"
        "source, fixture and observational-inventory adjudications remain separate.\n\n"
        "## Bounded C819 module-placement subset\n\n"
        "Seven compile/f2023 cases represent four C819 facets: one proper-module\n"
        "admission, plus main-program, external-subroutine and module-contained-subroutine\n"
        "negatives with their exact controls. Each repair deletes only `, bind(c)`.\n"
        "The same `bound_value`, prior intrinsic USE of symbolic C_INT, scalar type,\n"
        "complete context and executable body remain. The contained procedure declares\n"
        "the variable in its own specification-part, not its outer module's.\n\n"
        "All four positives are compile/positive-control evidence. No C counterpart,\n"
        "link, runtime, SAVE-retention or definition-use credit is added. Each negative\n"
        "needs the located BIND-variable/declaration-context cause, not bare keywords,\n"
        "an echo, a different entity/type/kind error, unsupported recovery or a native\n"
        "compiler failure. Ordinary zero/nonzero reports do not require fatal rejection\n"
        "or a printed rule code. Only specifically qualified nonfatal reports can count.\n\n"
        f"{len(requirement['pending'])} C819 facets remain PENDING; the other requirements currently\n"
        f"have {other_pending} pending facets ({len(requirement['pending']) + other_pending} total in 8.5.5).\n"
        "Submodule-local and the common/interface/result/dummy source-use boundaries are\n"
        "not implemented. Generation preserves current unrelated requirements and all\n"
        "independent administrative records; it does not approve or renew them.\n\n")
    history_text = (
        current_history + "\n"
        "Its older corpus and empty SourceUses descriptions are not current-main claims.\n"
        "This subset starts from committed `94b6b1ea`; the existing R402 declaration-name\n"
        "SourceUse, its review and all canonical links are retained without new credit.\n"
        "Their effective state is derived from the current native registries.\n\n")
    return (header + preserved + history_text + begin + "\n\n"
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
    actual = {path for path in (ROOT / "tests/fixtures").glob("bind_variable_placement_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale C819 placement subset: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded C819 corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} fourteen files: seven compile cases, four C819 facets.")


if __name__ == "__main__":
    main()
