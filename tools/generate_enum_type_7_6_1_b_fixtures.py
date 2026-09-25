#!/usr/bin/env python3
"""Additional 7.6.1 unnamed ENUM,BIND(C) diagnostic fixtures."""
import argparse
from dataclasses import dataclass
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.6.1"
CATALOGUE = "doc/catalogues/enum_type_7_6_1.json"
VIEW = "doc/fortran_2023_7_6_1.md"
PREFIX = "enum_type_7_6_1_b_"

SELECTED = {
    "R760": {"required-bind-c", "required-comma", "c-language-designator"},
    "R761": {"list-separator"},
    "R762": {"scalar-initializer", "integer-initializer"},
    "R763": {"trailing-name"},
    "C7111": {"first-initializer", "later-list-initializer", "later-statement-initializer"},
}

DIAGNOSTIC_EXCLUSIONS = [
    "internal compiler error",
    "internal error",
    "AssertFailed",
    "LCOMPILERS_ASSERT",
    "traceback",
    "segmentation fault",
    "not implemented",
    "verifier",
    "out of memory",
]

ORACLE_PREFIXES = {rule: f"{rule} enum_type_7_6_1_b diagnostic fixtures: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} enum_type_7_6_1_b diagnostic boundaries: " for rule in SELECTED}

ORACLES = {
    "R760": ORACLE_PREFIXES["R760"] + (
        "three line-anchored compile diagnostic/control pairs isolate the required `, BIND(C)` suffix, "
        "the comma before BIND, and the literal C language designator. Each control changes only the "
        "header spelling while retaining the same single enumerator and END ENUM."
    ),
    "R761": ORACLE_PREFIXES["R761"] + (
        "one compile diagnostic/control pair writes two colon-free enumerator names without the required "
        "comma; the control inserts only that comma, keeping the unnamed enum header and terminator fixed."
    ),
    "R762": ORACLE_PREFIXES["R762"] + (
        "two compile diagnostic/control pairs isolate the initializer expression grammar. The invalid "
        "sources use a rank-one INTEGER array constructor and a scalar REAL literal respectively; the "
        "controls replace only the initializer token with scalar INTEGER constant `4`."
    ),
    "R763": ORACLE_PREFIXES["R763"] + (
        "one compile diagnostic/control pair appends a name after END ENUM in an otherwise complete "
        "unnamed definition; the control removes only the trailing name, isolating the R763 closing form."
    ),
    "C7111": ORACLE_PREFIXES["C7111"] + (
        "three compile diagnostic/control pairs isolate the double-colon requirement when `=` appears: "
        "on the first enumerator, on a later item in the same list, and on a later ENUMERATOR statement. "
        "Each control inserts only `::` before that statement's enumerator-list."
    ),
}

LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "these are compile-diagnostic fixtures, not runtime value witnesses. Diagnostics accept any "
        "compiler error anchored at the violating line and exclude ICE/internal-error/not-implemented text. "
        "Named enum type, enum-constructor, BOZ, C companion, representation and source-use graph facets "
        "remain pending; GNU Fortran 16.1 rejects `ENUM, BIND(C) :: name` before any named-type control "
        "can qualify."
    )
    for rule in SELECTED
}


@dataclass(frozen=True)
class DiagnosticCase:
    rule: str
    facet: str
    variant: str
    invalid: str
    control: str
    invalid_line: int
    repair_from: str
    repair_to: str


def src(body):
    return "program p\n  implicit none\n" + body + "end program p\n"


CASES = [
    DiagnosticCase(
        "R760", "required-bind-c", "missing_bind_c",
        src("  enum\n    enumerator :: first\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first\n  end enum\n"),
        3, "  enum\n", "  enum, bind(c)\n"),
    DiagnosticCase(
        "R760", "required-comma", "missing_comma",
        src("  enum bind(c)\n    enumerator :: first\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first\n  end enum\n"),
        3, "  enum bind(c)\n", "  enum, bind(c)\n"),
    DiagnosticCase(
        "R760", "c-language-designator", "wrong_bind_language",
        src("  enum, bind(fortran)\n    enumerator :: first\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first\n  end enum\n"),
        3, "bind(fortran)", "bind(c)"),
    DiagnosticCase(
        "R761", "list-separator", "missing_name_comma",
        src("  enum, bind(c)\n    enumerator first second\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator first, second\n  end enum\n"),
        4, "first second", "first, second"),
    DiagnosticCase(
        "R762", "scalar-initializer", "array_initializer",
        src("  enum, bind(c)\n    enumerator :: first=[4]\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first=4\n  end enum\n"),
        4, "first=[4]", "first=4"),
    DiagnosticCase(
        "R762", "integer-initializer", "real_initializer",
        src("  enum, bind(c)\n    enumerator :: first=4.0\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first=4\n  end enum\n"),
        4, "first=4.0", "first=4"),
    DiagnosticCase(
        "R763", "trailing-name", "trailing_end_name",
        src("  enum, bind(c)\n    enumerator :: first\n  end enum tone\n"),
        src("  enum, bind(c)\n    enumerator :: first\n  end enum\n"),
        5, "  end enum tone\n", "  end enum\n"),
    DiagnosticCase(
        "C7111", "first-initializer", "first_initializer_without_colons",
        src("  enum, bind(c)\n    enumerator first=4\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first=4\n  end enum\n"),
        4, "    enumerator first=4\n", "    enumerator :: first=4\n"),
    DiagnosticCase(
        "C7111", "later-list-initializer", "later_list_initializer_without_colons",
        src("  enum, bind(c)\n    enumerator first, second=4\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator :: first, second=4\n  end enum\n"),
        4, "    enumerator first, second=4\n", "    enumerator :: first, second=4\n"),
    DiagnosticCase(
        "C7111", "later-statement-initializer", "later_statement_initializer_without_colons",
        src("  enum, bind(c)\n    enumerator first\n    enumerator second=4\n  end enum\n"),
        src("  enum, bind(c)\n    enumerator first\n    enumerator :: second=4\n  end enum\n"),
        5, "    enumerator second=4\n", "    enumerator :: second=4\n"),
]

DIAGNOSTIC_END_LINES = {
    "missing_bind_c": 5,
    "wrong_bind_language": 5,
}


def valid_id(case):
    return case.rule.replace(".", "_").replace("-", "_") + "_valid__" + PREFIX.rstrip("_") + "_" + case.variant + "_control"


def invalid_id(case):
    return case.rule.replace(".", "_").replace("-", "_") + "_invalid__" + PREFIX.rstrip("_") + "_" + case.variant


def source_specs():
    specs = {}
    for case in CASES:
        if case.invalid.replace(case.repair_from, case.repair_to, 1) != case.control:
            raise ValueError("control is not a one-property repair for " + case.variant)
        control_name = valid_id(case)
        invalid_name = invalid_id(case)
        specs[control_name] = dict(
            id=control_name, rule=case.rule, facet=case.facet, facets=[case.facet],
            variant=case.variant + "_control", kind="valid", phase="compile",
            evidence="positive-control", source=case.control, pair=invalid_name)
        specs[invalid_name] = dict(
            id=invalid_name, rule=case.rule, facet=case.facet, facets=[case.facet],
            variant=case.variant, kind="invalid", phase="compile", evidence="effect",
            source=case.invalid, control_id=control_name,
            repair_from=case.repair_from, repair_to=case.repair_to,
            diagnostic=dict(file="source.f90", line=case.invalid_line,
                            end_line=DIAGNOSTIC_END_LINES.get(case.variant, case.invalid_line),
                            excludes_any=list(DIAGNOSTIC_EXCLUSIONS)))
    return specs


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = root / "tests/fixtures" / (PREFIX + spec["variant"])
        expect = dict(phase="compile", step="source")
        if spec["kind"] == "invalid":
            expect.update(outcome="diagnose", diagnostic=spec["diagnostic"])
        else:
            expect.update(outcome="success")
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran",
                        form="free", output="source.o")],
            expect=expect)
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    import generate_enum_type_fixtures as enum_type
    updated = copy.deepcopy(catalogue)
    coverage = enum_type.union_coverage()
    for requirement in updated["requirements"]:
        facets = coverage.get(requirement["id"], set())
        for facet in facets:
            requirement["pending"].pop(facet, None)
        expected_pending = set(requirement["facets"]) - facets
        if set(requirement.get("pending", {})) != expected_pending:
            raise ValueError("enum_type_7_6_1_b pending partition mismatch for " + requirement["id"])
        if requirement["id"] not in SELECTED:
            continue
        rule = requirement["id"]
        requirement["oracle"] = owned_paragraph(
            requirement.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        requirement["oracle_limitation"] = owned_paragraph(
            requirement.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue):
    import generate_enum_type_fixtures as enum_type
    return enum_type.render_view(catalogue)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {path for path in (root / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()}
        stale += [path.relative_to(root).as_posix() for path in sorted(actual - set(files))]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale enum_type_7_6_1_b fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return files, specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    _, specs = generate(args.root, args.check, args.sync_catalogue)
    invalids = sum(1 for spec in specs.values() if spec["kind"] == "invalid")
    facets = sum(len(facets) for facets in SELECTED.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} enum_type_7_6_1_b cases, "
          f"{invalids} diagnostics and {facets} new facet bindings.")


if __name__ == "__main__":
    main()
