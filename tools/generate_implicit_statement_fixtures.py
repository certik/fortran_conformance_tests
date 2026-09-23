#!/usr/bin/env python3
"""Bounded Fortran 2023 8.7 IMPLICIT statement fixtures."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.7"
CATALOGUE = "doc/catalogues/implicit_statement_8_7.json"
VIEW = "doc/fortran_2023_8_7.md"
PREFIX = "implicit_statement_"

EXCLUSIONS = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal error", "internal:", "ASR verify", "out of memory", "recovery", "segmentation fault",
]

SELECTED = {
    "R866": ["empty-parentheses-NONE", "TYPE-only-NONE", "default-null-and-host-map-source"],
    "R867": ["intrinsic-type-maps"],
    "R868": ["single-letter-form", "two-letter-range-form"],
    "R869": ["TYPE-keyword"],
    "C897": ["plain-NONE-plus-map", "EXTERNAL-only-coexistence"],
    "C899": ["local-external-subroutine"],
    "S8.7-002": ["default-map-route", "prior-explicit-map"],
}

ORACLE_PREFIXES = {rule: f"Batch173 IMPLICIT statement fixtures for {rule}: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"Batch173 IMPLICIT statement fixture boundaries for {rule}: " for rule in SELECTED}
ORACLES = {
    "R866": ORACLE_PREFIXES["R866"] + (
        "three complete controls admit IMPLICIT NONE(), IMPLICIT NONE(TYPE), and a host/internal inherited "
        "ordinary mapping. The host case maps A to INTEGER in the host and observes the internal procedure's "
        "unspecified A mapping through generic resolution, so the inherited mapping is a source property rather "
        "than a value coincidence."
    ),
    "R867": ORACLE_PREFIXES["R867"] + (
        "one complete runtime program uses IMPLICIT INTEGER(A) and a type-sensitive generic interface with "
        "INTEGER and REAL specifics to observe that ALPHA is an INTEGER implicit data entity."
    ),
    "R868": ORACLE_PREFIXES["R868"] + (
        "two complete runtime programs distinguish a singleton IMPLICIT REAL(I) map and an ascending "
        "IMPLICIT INTEGER(A-C) range. Each is observed by generic resolution and has conforming feature "
        "mutants that remove the statement or change the selected letter/range so the actual's type changes."
    ),
    "R869": ORACLE_PREFIXES["R869"] + (
        "the TYPE keyword is admitted in a complete IMPLICIT NONE(TYPE) control whose data entity is explicitly "
        "typed, distinguishing the keyword syntax from an undeclared-name diagnostic."
    ),
    "C897": ORACLE_PREFIXES["C897"] + (
        "one numbered diagnostic violates only the no-other-IMPLICIT rule by placing an ordinary map after bare "
        "IMPLICIT NONE; its one-property control deletes that map. A separate EXTERNAL-only control shows that "
        "IMPLICIT NONE(EXTERNAL) has a false C897 antecedent and can coexist with a later ordinary map."
    ),
    "C899": ORACLE_PREFIXES["C899"] + (
        "one numbered diagnostic calls an external subroutine under IMPLICIT NONE(EXTERNAL) without an explicit "
        "interface or EXTERNAL declaration. Its one-property control is bound to the same facet and adds only "
        "EXTERNAL PING, the explicit-EXTERNAL alternative named by C899."
    ),
    "S8.7-002": ORACLE_PREFIXES["S8.7-002"] + (
        "one default-map positive uses no IMPLICIT statement and observes I through N as INTEGER and A as REAL "
        "by generic resolution. One prior-map positive uses an explicit host IMPLICIT statement before the "
        "internal implicit declaration and observes the inherited INTEGER map by generic resolution."
    ),
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "Only the listed facets are represented. Character length maps, derived-type identity maps, TYPEOF/"
        "CLASSOF exclusions, NONE ordering before PARAMETER, repeated NONE specifiers, C898 range-order "
        "diagnostics, prose repeated-letter diagnostics, nondefault kind codes, interface-body defaults, module "
        "subprogram defaults, BLOCK propagation, dummy procedures, explicit-interface alternatives and function "
        "result override boundaries remain pending unless named here. Runtime fixtures use exact small numeric "
        "assignments only as defined payload; type is observed through generic resolution, not through a value "
        "that INTEGER and REAL could share."
    ) for rule in SELECTED
}

SUMMARY_BEGIN = "<!-- BEGIN IMPLICIT STATEMENT FIXTURES -->"
SUMMARY_END = "<!-- END IMPLICIT STATEMENT FIXTURES -->"

KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "R867_valid__implicit_statement_intrinsic_integer_singleton_generic",
        "R868_valid__implicit_statement_single_letter_real_i_generic",
        "R868_valid__implicit_statement_two_letter_integer_range_generic",
        "R866_valid__implicit_statement_internal_host_inherited_a_map",
        "S8_7_002_valid__implicit_statement_prior_explicit_host_map",
    }
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned IMPLICIT statement paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraphs)


def rule_token(rule):
    return rule.replace(".", "_").replace("-", "_")


def case_id(stem, kind, rule):
    return f"{rule_token(rule)}_{kind}__{PREFIX}{stem}"


def compiler_family(compiler):
    name = Path(str(compiler)).name.lower()
    if "lfortran" in name:
        return "lfortran"
    if "gfortran" in name:
        return "gfortran"
    return name


def compiler_command(compiler, std, source, exe):
    command = [str(compiler)]
    if compiler_family(compiler) == "lfortran":
        command += ["--std=" + std] if std else []
    else:
        command += ["-std=" + std] if std else []
    return command + [str(source), "-o", str(exe)]


def mutation(source, expected, replacement, name):
    if source.count(expected) != 1:
        raise ValueError(f"mutation {name} expected exactly one occurrence of {expected!r}")
    start = source.index(expected)
    return {
        "id": name, "kind": "feature", "expected": expected, "replacement": replacement,
        "span": [start, start + len(expected)],
    }


def runtime_manifest(spec):
    return {
        "schema_version": 1,
        "id": spec["id"],
        "rule": spec["rule"],
        "facets": spec["facets"],
        "evidence": spec["evidence"],
        "standard": "f2023",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran",
                   "form": "free", "output": "source.o"}],
        "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
        "expect": {"phase": "run", "outcome": "success", "exit_code": 0,
                   "stdout": spec["completion"], "stderr": ""},
    }


def compile_manifest(spec):
    invalid = spec["kind"] == "invalid"
    expect = {"phase": "compile", "step": "source", "outcome": "diagnose" if invalid else "success"}
    if invalid:
        diagnostic = {
            "file": "source.f90",
            "line": spec["line"],
            "end_line": spec["end_line"],
            "contains_any": spec["messages"],
            "excludes_any": EXCLUSIONS,
        }
        if spec.get("additional_spans"):
            diagnostic["additional_spans"] = spec["additional_spans"]
        expect["diagnostic"] = diagnostic
    return {
        "schema_version": 1,
        "id": spec["id"],
        "rule": spec["rule"],
        "facets": spec["facets"],
        "evidence": spec["evidence"],
        "standard": "f2023",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran",
                   "form": "free", "output": "source.o"}],
        "expect": expect,
    }


GENERIC_INTERFACE = """  interface classify
    procedure classify_integer
    procedure classify_real
  end interface
"""

GENERIC_PROCEDURES = """contains
  integer function classify_integer(x)
    integer, intent(in) :: x
    classify_integer = 1
  end function classify_integer
  integer function classify_real(x)
    real, intent(in) :: x
    classify_real = 2
  end function classify_real
"""


def runtime_spec(stem, rule, facets, evidence, source, completion, derivation, mutations):
    spec = {
        "id": case_id(stem, "valid", rule), "stem": stem, "rule": rule, "facets": list(facets),
        "kind": "valid", "evidence": evidence, "source": source, "completion": completion,
        "source_derivation": derivation, "mutations": list(mutations),
    }
    spec["source_sha256"] = sha(source.encode("ascii"))
    spec["manifest"] = runtime_manifest(spec)
    return spec


def compile_spec(stem, rule, facets, kind, evidence, source, derivation, *,
                 line=None, end_line=None, messages=None, additional_spans=None):
    spec = {
        "id": case_id(stem, kind, rule), "stem": stem, "rule": rule, "facets": list(facets),
        "kind": kind, "evidence": evidence, "source": source,
        "source_derivation": derivation, "mutations": [],
    }
    if kind == "invalid":
        spec.update(line=line, end_line=end_line or line, messages=list(messages),
                    additional_spans=list(additional_spans or []))
    spec["source_sha256"] = sha(source.encode("ascii"))
    spec["manifest"] = compile_manifest(spec)
    return spec


def build_specs():
    specs = []

    src = ("program p\n" + GENERIC_INTERFACE +
           "  ivalue = 4\n  alpha = 5\n"
           "  if (classify(ivalue) /= 1) error stop 1\n"
           "  if (classify(alpha) /= 2) error stop 2\n"
           "  print '(a)', 'implicit_statement default map generic ok'\n" +
           GENERIC_PROCEDURES + "end program p\n")
    specs.append(runtime_spec(
        "default_integer_real_generic", "S8.7-002", ["default-map-route"], "positive-control",
        src, "implicit_statement default map generic ok\n",
        "8.7 p3/p4 default maps I through N to INTEGER and A to REAL in a program unit; generic resolution observes both types.",
        [mutation(src, "classify(ivalue) /= 1", "classify(alpha) /= 1", "change_integer_name_to_default_real"),
         mutation(src, "classify(alpha) /= 2", "classify(ivalue) /= 2", "change_real_name_to_default_integer")]))

    src = ("program p\n  implicit integer (a)\n" + GENERIC_INTERFACE +
           "  alpha = 4\n  if (classify(alpha) /= 1) error stop 1\n"
           "  print '(a)', 'implicit_statement integer singleton generic ok'\n" +
           GENERIC_PROCEDURES + "end program p\n")
    specs.append(runtime_spec(
        "intrinsic_integer_singleton_generic", "R867", ["intrinsic-type-maps"], "effect",
        src, "implicit_statement integer singleton generic ok\n",
        "8.7 R867/p3 permits an INTEGER implicit-spec with a letter list; ALPHA is observed as INTEGER by generic resolution.",
        [mutation(src, "  implicit integer (a)\n", "", "remove_implicit_integer_map"),
         mutation(src, "implicit integer (a)", "implicit integer (b)", "move_singleton_off_entity_letter")]))

    src = ("program p\n  implicit real (i)\n" + GENERIC_INTERFACE +
           "  ivalue = 4\n  if (classify(ivalue) /= 2) error stop 1\n"
           "  print '(a)', 'implicit_statement single letter real generic ok'\n" +
           GENERIC_PROCEDURES + "end program p\n")
    specs.append(runtime_spec(
        "single_letter_real_i_generic", "R868", ["single-letter-form"], "effect",
        src, "implicit_statement single letter real generic ok\n",
        "8.7 R868 admits one letter; IMPLICIT REAL(I) changes IVALUE from the default INTEGER mapping to REAL.",
        [mutation(src, "  implicit real (i)\n", "", "remove_implicit_real_map"),
         mutation(src, "implicit real (i)", "implicit real (a)", "move_single_letter_off_entity_letter")]))

    src = ("program p\n  implicit integer (a-c)\n" + GENERIC_INTERFACE +
           "  bvalue = 4\n  if (classify(bvalue) /= 1) error stop 1\n"
           "  print '(a)', 'implicit_statement two letter range generic ok'\n" +
           GENERIC_PROCEDURES + "end program p\n")
    specs.append(runtime_spec(
        "two_letter_integer_range_generic", "R868", ["two-letter-range-form"], "effect",
        src, "implicit_statement two letter range generic ok\n",
        "8.7 R868/p2 admits A-C and expands it inclusively, so BVALUE is INTEGER rather than default REAL.",
        [mutation(src, "  implicit integer (a-c)\n", "", "remove_implicit_range_map"),
         mutation(src, "implicit integer (a-c)", "implicit integer (c-e)", "move_range_off_entity_letter")]))

    host_generic_tail = (
        "contains\n"
        "  subroutine child\n"
        "    apple = 7\n"
        "    if (classify(apple) /= 1) error stop 1\n"
        "    print '(a)', '{completion}'\n"
        "  end subroutine child\n"
        "  integer function classify_integer(x)\n"
        "    integer, intent(in) :: x\n"
        "    classify_integer = 1\n"
        "  end function classify_integer\n"
        "  integer function classify_real(x)\n"
        "    real, intent(in) :: x\n"
        "    classify_real = 2\n"
        "  end function classify_real\n"
        "end program p\n")
    src = ("program p\n  implicit integer (a)\n" + GENERIC_INTERFACE + "  call child\n" +
           host_generic_tail.format(completion="implicit_statement inherited host map ok"))
    specs.append(runtime_spec(
        "internal_host_inherited_a_map", "R866", ["default-null-and-host-map-source"], "effect",
        src, "implicit_statement inherited host map ok\n",
        "8.7 p3 says an internal subprogram's default mapping is its host mapping; APPLE is INTEGER in CHILD.",
        [mutation(src, "  implicit integer (a)\n", "", "remove_host_implicit_map"),
         mutation(src, "implicit integer (a)", "implicit integer (b)", "move_host_map_off_entity_letter")]))

    src = ("program p\n  implicit integer (a)\n" + GENERIC_INTERFACE + "  call child\n" +
           host_generic_tail.format(completion="implicit_statement prior explicit host map ok"))
    specs.append(runtime_spec(
        "prior_explicit_host_map", "S8.7-002", ["prior-explicit-map"], "positive-control",
        src, "implicit_statement prior explicit host map ok\n",
        "8.7 p4 requires the first-letter mapping to have been established by a prior IMPLICIT or default; the host IMPLICIT precedes CHILD's implicit APPLE declaration.",
        [mutation(src, "  implicit integer (a)\n", "", "remove_prior_host_implicit_map"),
         mutation(src, "implicit integer (a)", "implicit integer (b)", "move_prior_host_map_off_entity_letter")]))

    specs.append(compile_spec(
        "empty_parentheses_none_control", "R866", ["empty-parentheses-NONE"], "valid", "positive-control",
        "program p\n  implicit none()\n  integer :: x\nend program p\n",
        "8.7 R866 admits IMPLICIT NONE with present parentheses and absent implicit-none-spec-list."))
    specs.append(compile_spec(
        "type_only_none_control", "R866", ["TYPE-only-NONE"], "valid", "positive-control",
        "program p\n  implicit none(type)\n  integer :: x\nend program p\n",
        "8.7 R866/R869 admit the TYPE-only NONE form when all data entities are explicitly typed."))
    specs.append(compile_spec(
        "type_keyword_control", "R869", ["TYPE-keyword"], "valid", "positive-control",
        "program p\n  implicit none(type)\n  integer :: x\nend program p\n",
        "8.7 R869 names TYPE as an implicit-none-spec alternative."))

    specs.append(compile_spec(
        "plain_none_plus_map", "C897", ["plain-NONE-plus-map"], "invalid", "effect",
        "program p\n  implicit none\n  implicit integer (a)\n  integer :: x\nend program p\n",
        "8.7 C897 prohibits another IMPLICIT statement in the same scope after a no-list IMPLICIT NONE; deleting only the ordinary map is the control.",
        line=2, end_line=2, additional_spans=[{"line": 3}],
        messages=["No other implicit statement", "following an IMPLICIT NONE"]))
    specs.append(compile_spec(
        "plain_none_no_other_map_control", "C897", ["plain-NONE-plus-map"], "valid", "positive-control",
        "program p\n  implicit none\n  integer :: x\nend program p\n",
        "The C897 control differs only by deleting the other IMPLICIT statement."))
    specs.append(compile_spec(
        "external_only_coexistence_control", "C897", ["EXTERNAL-only-coexistence"], "valid", "positive-control",
        "program p\n  implicit none(external)\n  implicit integer (a)\n  integer :: x\nend program p\n",
        "8.7 C897's TYPE/no-list antecedent is false for EXTERNAL-only NONE, so the ordinary nonoverlapping map is admitted."))

    specs.append(compile_spec(
        "missing_external_attribute_subroutine", "C899", ["local-external-subroutine"], "invalid", "effect",
        "program p\n  implicit none(external)\n  call ping()\nend program p\nsubroutine ping()\nend subroutine ping\n",
        "8.7 C899 requires PING to have an explicit interface or explicit EXTERNAL attribute in this NONE(EXTERNAL) scope.",
        line=3, messages=["explicitly declared"]))
    specs.append(compile_spec(
        "explicit_external_subroutine_control", "C899", ["local-external-subroutine"], "valid", "positive-control",
        "program p\n  implicit none(external)\n  external ping\n  call ping()\nend program p\nsubroutine ping()\nend subroutine ping\n",
        "The C899 control adds only EXTERNAL PING, satisfying the explicit-EXTERNAL alternative."))

    ids = [spec["id"] for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate generated IMPLICIT statement case id")
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, {spec["id"]: spec for spec in build_specs()}
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["stem"])
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected IMPLICIT statement facets changed for " + rule)
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the IMPLICIT statement generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## IMPLICIT statement fixture packet\n\n"
        "Fourteen complete fixtures cover twelve selected 8.7 facets. Six runtime programs observe default, "
        "ordinary singleton, ordinary range and inherited host mappings through a type-sensitive generic "
        "interface with INTEGER and REAL specifics; numeric assignments supply defined payload only and are "
        "not the type oracle. Feature mutants remove or move the selected map/range/name so the generic "
        "specific changes while the mutant remains conforming.\n\n"
        "The diagnostic fixtures are restricted to numbered constraints with controls. C897 is checked by "
        "bare IMPLICIT NONE followed by one ordinary map, with the control deleting only that map. C899 is "
        "checked by a NONE(EXTERNAL) external subroutine call missing EXTERNAL, with the control adding only "
        "EXTERNAL PING. Prose repeated-letter p2/S8.7-001, C895 ordering/cardinality and C896 duplicate "
        "specifier plans remain pending in this packet.\n\n"
        "The frozen LFortran target currently resolves generic calls for explicitly implicitly typed local "
        "names as if their default first-letter mapping still applied, and it also accepts the C899 negative; "
        "the reference compiler validates the selected sources.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the IMPLICIT statement summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(
        render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def apply_mutation(spec, mutation_row):
    raw = spec["source"].encode("ascii")
    start, end = mutation_row["span"]
    if raw[start:end].decode("ascii") != mutation_row["expected"]:
        raise ValueError("complete parent input changed for " + spec["id"] + ":" + mutation_row["id"])
    return raw[:start] + mutation_row["replacement"].encode("ascii") + raw[end:]


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compiled = subprocess.run(
        compiler_command(compiler, std, source, exe), cwd=work_dir,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compiled.returncode != 0 or not exe.is_file():
        return {"status": "compile-fail", "stdout": compiled.stdout, "stderr": compiled.stderr,
                "returncode": compiled.returncode}
    run = subprocess.run([str(exe)], cwd=work_dir, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run.returncode == 0 and run.stdout == expected_stdout and run.stderr == ""
    return {"status": "pass" if passed else "run-fail", "stdout": run.stdout,
            "stderr": run.stderr, "returncode": run.returncode}


def mutation_check(root=ROOT, compiler=None, std=None, keep_work=False, inject_identical=False):
    if not compiler or std is None:
        raise ValueError("--mutation-check requires --compiler and --std")
    _, specs = build_corpus(root)
    family = compiler_family(compiler)
    work_parent = Path(tempfile.mkdtemp(prefix="implicit-statement-mutations-"))
    report = []
    try:
        injected = False
        for spec in specs.values():
            if spec["manifest"]["expect"]["phase"] != "run":
                continue
            work_dir = work_parent / spec["stem"]
            work_dir.mkdir()
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["completion"],
                                    spec["stem"] + "_parent")
            parent_known = spec["id"] in KNOWN_PARENT_FAILURES.get(family, set())
            for index, item in enumerate(spec["mutations"]):
                row = dict(item)
                if inject_identical and not injected:
                    row["replacement"] = row["expected"]
                    row["id"] += "_injected_identical"
                    injected = True
                if parent["status"] != "pass":
                    report.append({"id": spec["id"], "mutation": row["id"], "parent_status": parent["status"],
                                   "status": "n/a" if parent_known else "parent-fail",
                                   "failed": None, "stdout": parent["stdout"], "stderr": parent["stderr"],
                                   "returncode": parent["returncode"]})
                    continue
                mutant_source = apply_mutation(spec, row).decode("ascii")
                observed = run_one_source(compiler, std, work_dir, mutant_source, spec["completion"],
                                          f"{spec['stem']}_mut_{index:03d}")
                report.append({"id": spec["id"], "mutation": row["id"], "parent_status": parent["status"],
                               "status": observed["status"], "failed": observed["status"] != "pass",
                               "stdout": observed["stdout"], "stderr": observed["stderr"],
                               "returncode": observed["returncode"]})
        unexpected_parent = [row for row in report if row["status"] == "parent-fail"]
        survivors = [row for row in report if row["status"] == "pass"]
        invalid = [row for row in report if row["status"] == "compile-fail"]
        if unexpected_parent or survivors or invalid:
            raise RuntimeError(json.dumps(
                {"unexpected_parent_failures": unexpected_parent[:5], "survivors": survivors[:5],
                 "invalid_mutants": invalid[:5]}, indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_parent, ignore_errors=True)


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
            raise ValueError("stale IMPLICIT statement fixtures: " + ", ".join(stale))
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
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--self-test-vacuity", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_check or args.self_test_vacuity:
        if args.check or args.sync_catalogue:
            parser.error("--mutation-check is separate from generation/checking")
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        try:
            report = mutation_check(args.root, args.compiler, args.std, args.keep_work,
                                    inject_identical=args.self_test_vacuity)
        except RuntimeError as error:
            if args.self_test_vacuity and "survivors" in str(error):
                print("Vacuity self-test: injected identical mutant was reported as a survivor.")
                print(str(error).splitlines()[0])
                return
            raise
        if args.self_test_vacuity:
            raise RuntimeError("vacuity self-test did not produce a survivor")
        checked = sum(row["status"] in {"run-fail"} for row in report)
        skipped = sum(row["status"] == "n/a" for row in report)
        print(f"Mutation-checked {checked} IMPLICIT statement mutants; {skipped} skipped for known "
              f"{compiler_family(args.compiler)} parent failures; all checked mutants failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    runtime = sum(1 for spec in specs.values() if spec["manifest"]["expect"]["phase"] == "run")
    mutations = sum(len(spec["mutations"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} IMPLICIT statement cases, "
          f"{runtime} runtime cases, {mutations} feature mutants.")


if __name__ == "__main__":
    main()
