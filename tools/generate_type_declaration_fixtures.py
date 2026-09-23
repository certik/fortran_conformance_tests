#!/usr/bin/env python3
"""Finite Fortran 2023 type-declaration fixtures for 8.2."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.2"
CATALOGUE = "doc/catalogues/type_declaration_statements_8_2.json"
PREFIX = "type_declaration_"
EXCLUSIONS = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal error", "internal:", "ASR verify", "out of memory", "recovery", "segmentation fault",
]

SELECTED = {
    "C804": ["noncharacter-star-length", "character-star-length-admission"],
    "C805": ["constant-length-admission", "nonconstant-specification-admission", "deferred-length-contexts"],
    "C806": ["initializer-without-attributes"],
    "C807": ["missing-member-initializer", "all-members-initialized"],
    "C808": ["allocatable"],
    "R805": ["constant-expression-admission", "null-admission"],
    "R806": ["bare-null-reference"],
    "S8.2-001": ["declared-type-across-list", "entity-character-length"],
    "S8.2-002": ["entity-array-override"],
    "S8.2-004": ["numeric-admission", "character-kind-and-length-admission", "other-same-shape-admission"],
}
RESTORED_PENDING = {
    "R805": {
        "nonconstant-initializer": (
            "PENDING after batch156 review TDFR-002. The rejected candidate INTEGER :: x=n reaches "
            "10.1.12 C1012's constant-expression requirement, not R805's initializer syntax alternatives; "
            "do not file that diagnostic under 8.2."
        )
    }
}

ORACLE_PREFIXES = {rule: f"Batch156 type-declaration fixtures for {rule}: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"Batch156 type-declaration fixture boundaries for {rule}: " for rule in SELECTED}
ORACLES = {
    "C804": ORACLE_PREFIXES["C804"] + (
        "one compile/diagnose case declares a non-CHARACTER INTEGER entity with an individual *3 suffix, "
        "and the one-property control changes only the declaration type to CHARACTER and observes LEN=3 at run time."
    ),
    "C805": ORACLE_PREFIXES["C805"] + (
        "one run-time positive program observes literal and named-constant individual CHARACTER lengths, a dummy "
        "specification-expression length supplied by an INTEGER INTENT(IN) argument, and an allocatable deferred "
        "length established by allocation before LEN and value checks."
    ),
    "C806": ORACLE_PREFIXES["C806"] + (
        "one compile/diagnose case uses INTEGER x=1 with no attributes and no double-colon separator; the control "
        "inserts only :: and observes the nonzero initializer value."
    ),
    "C807": ORACLE_PREFIXES["C807"] + (
        "one compile/diagnose case omits only the second initializer in INTEGER, PARAMETER :: a=1, b. The control "
        "adds only =a+1 and observes b=2."
    ),
    "C808": ORACLE_PREFIXES["C808"] + (
        "one compile/diagnose case initializes an otherwise ordinary scalar ALLOCATABLE INTEGER. The control removes "
        "only the initializer and observes that the allocatable starts unallocated without reading a value."
    ),
    "R805": ORACLE_PREFIXES["R805"] + (
        "runtime positives observe nondefault constant-expression values and pointer initialization by NULL(). "
        "The nonconstant-initializer diagnostic plan is deliberately left pending because the known rejection "
        "is governed by C1012, not R805."
    ),
    "R806": ORACLE_PREFIXES["R806"] + (
        "the pointer NULL() runtime case uses the bare intrinsic function reference with no arguments and observes "
        "the resulting disassociated pointer."
    ),
    "S8.2-001": ORACLE_PREFIXES["S8.2-001"] + (
        "runtime cases observe the declared INTEGER type across a two-entity list through an INTEGER dummy observer, "
        "and observe a statement CHARACTER length overridden by per-entity * lengths using LEN before value equality."
    ),
    "S8.2-002": ORACLE_PREFIXES["S8.2-002"] + (
        "one runtime case declares a DIMENSION(2) list where the second entity has an entity array-spec (3), then "
        "checks extents and independent nondefault values. Coarray coverage is intentionally absent."
    ),
    "S8.2-004": ORACLE_PREFIXES["S8.2-004"] + (
        "one runtime positive program observes nonpointer declaration initialization for INTEGER, REAL, LOGICAL, "
        "fixed-length CHARACTER and same-shape rank-one INTEGER array entities with nondefault values."
    ),
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "Only the listed facets are represented. Attribute compatibility constraints governed by 8.5, coarrays, "
        "procedure declarations, COMMON/BLOCK DATA, C812 data-target compatibility, C813 non-bare NULL forms, "
        "processor-dependent diagnostic wording and review approval remain outside this packet."
    ) for rule in SELECTED
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned type-declaration oracle paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraphs)


def case_id(stem, kind, rule):
    return f"{rule.replace('.', '_').replace('-', '_')}_{kind}__{PREFIX}{stem}"


def compile_manifest(spec):
    invalid = spec["kind"] == "invalid"
    manifest = {
        "schema_version": 1,
        "id": spec["id"],
        "rule": spec["rule"],
        "facets": spec["facets"],
        "evidence": spec["evidence"],
        "standard": "f2023",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
        "expect": {"phase": "compile", "step": "source", "outcome": "diagnose" if invalid else "success"},
    }
    if invalid:
        manifest["expect"]["diagnostic"] = {
            "file": "source.f90",
            "line": spec["line"],
            "end_line": spec["line"],
            "contains_any": spec["messages"],
            "excludes_any": EXCLUSIONS,
        }
    return manifest


def run_manifest(spec):
    return {
        "schema_version": 1,
        "id": spec["id"],
        "rule": spec["rule"],
        "facets": spec["facets"],
        "evidence": spec["evidence"],
        "standard": "f2023",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
        "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
        "expect": {"phase": "run", "outcome": "success", "exit_code": 0,
                   "stdout": spec["completion"], "stderr": ""},
    }


def mutation(source, expected, replacement, name, role="feature"):
    count = source.count(expected)
    if count != 1:
        raise ValueError(f"mutation {name} expected exactly one occurrence of {expected!r}, found {count}")
    start = source.index(expected)
    return {"id": name, "expected": expected, "replacement": replacement,
            "span": [start, start + len(expected)], "kind": "feature", "role": role}


def mutation_at(source, occurrence, expected, replacement, name):
    start = source.index(occurrence) + occurrence.index(expected)
    return {"id": name, "expected": expected, "replacement": replacement,
            "span": [start, start + len(expected)], "kind": "feature"}


def runtime_spec(stem, rule, facets, evidence, source, completion, derivation, mutations):
    spec = {
        "id": case_id(stem, "valid", rule), "stem": stem, "rule": rule, "facets": facets,
        "kind": "valid", "evidence": evidence, "source": source, "completion": completion,
        "source_derivation": derivation, "mutations": mutations,
    }
    spec["source_sha256"] = sha(source.encode("ascii"))
    spec["manifest"] = run_manifest(spec)
    return spec


def compile_spec(stem, rule, facets, kind, evidence, source, derivation, *, line=None, messages=None):
    spec = {
        "id": case_id(stem, kind, rule), "stem": stem, "rule": rule, "facets": facets,
        "kind": kind, "evidence": evidence, "source": source,
        "source_derivation": derivation, "mutations": [],
    }
    if kind == "invalid":
        spec.update(line=line, messages=messages)
    spec["source_sha256"] = sha(source.encode("ascii"))
    spec["manifest"] = compile_manifest(spec)
    return spec


def build_specs():
    specs = []
    specs.append(compile_spec(
        "c804_noncharacter_star_length", "C804", ["noncharacter-star-length"], "invalid", "effect",
        "program main\n  implicit none\n  integer :: text*3\nend program main\n",
        "8.2 C804 prohibits *char-length when the entity is not CHARACTER; only INTEGER versus CHARACTER differs from its control.",
        line=3, messages=["Syntax error in data declaration", "length specifier is only valid for character type"]))
    src = "program main\n  implicit none\n  character :: text*3\n  text = 'abc'\n  if (len(text) /= 3) error stop\n  if (text /= 'abc') error stop\n  print '(a)', 'type_declaration c804 character length ok'\nend program main\n"
    specs.append(runtime_spec(
        "c804_character_star_length_control", "C804", ["character-star-length-admission"], "positive-control",
        src, "type_declaration c804 character length ok\n",
        "8.2 R803/C804 permits *char-length on a CHARACTER entity; LEN is checked before character equality.",
        [mutation(src, "character :: text*3", "character :: text", "remove_entity_star_length")]))

    specs.append(compile_spec(
        "c806_initializer_without_colons", "C806", ["initializer-without-attributes"], "invalid", "effect",
        "program main\n  implicit none\n  integer x=1\nend program main\n",
        "8.2 C806 requires a double-colon separator when initialization appears; the control inserts only ::.",
        line=3, messages=["Syntax error in data declaration", "Invalid syntax for variable initialization"]))
    src = "program main\n  implicit none\n  integer :: x=1\n  if (x /= 1) error stop\n  print '(a)', 'type_declaration c806 initializer control ok'\nend program main\n"
    specs.append(runtime_spec(
        "c806_initializer_with_colons_control", "C806", ["initializer-without-attributes"], "positive-control",
        src, "type_declaration c806 initializer control ok\n",
        "8.2 C806 is satisfied by adding :: before the initialized entity-decl list; x's nonzero value is observed.",
        [mutation(src, "integer :: x=1", "integer :: x\n  x = 2", "remove_initializer"),
         mutation(src, "integer :: x=1", "integer :: x=2", "change_initializer_value")]))

    specs.append(compile_spec(
        "c807_missing_initializer", "C807", ["missing-member-initializer"], "invalid", "effect",
        "program main\n  implicit none\n  integer, parameter :: a=1, b\nend program main\n",
        "8.2 C807 requires initialization in each entity-decl when PARAMETER appears; only b lacks initialization.",
        line=3, messages=["missing an initializer", "not initialised"]))
    src = "program main\n  implicit none\n  integer, parameter :: a=1, b=a+1\n  if (b /= 2) error stop\n  print '(a)', 'type_declaration c807 all initialized ok'\nend program main\n"
    specs.append(runtime_spec(
        "c807_all_initialized_control", "C807", ["all-members-initialized"], "positive-control",
        src, "type_declaration c807 all initialized ok\n",
        "8.2 C807 is satisfied because both PARAMETER entities have initialization; b=a+1 observes left-to-right constant use.",
        [mutation(src, "integer, parameter :: a=1, b=a+1", "integer :: a=2, b=3", "remove_parameter_initializers"),
         mutation(src, "a=1", "a=2", "change_first_initializer"),
         mutation(src, "b=a+1", "b=a+2", "change_second_initializer")]))

    specs.append(compile_spec(
        "c808_allocatable_initializer", "C808", ["allocatable"], "invalid", "effect",
        "program main\n  implicit none\n  integer, allocatable :: x = 1\nend program main\n",
        "8.2 C808 prohibits initialization on an allocatable variable; the control deletes only = 1.",
        line=3, messages=["cannot have an initializer", "cannot have an initialization expression"]))
    src = "program main\n  implicit none\n  integer, allocatable :: x\n  if (allocated(x)) error stop\n  print '(a)', 'type_declaration c808 allocatable control ok'\nend program main\n"
    specs.append(runtime_spec(
        "c808_allocatable_no_initializer_control", "C808", ["allocatable"], "positive-control",
        src, "type_declaration c808 allocatable control ok\n",
        "Deleting only the initializer leaves an ordinary unallocated scalar allocatable, which is not read.", []))

    src = "program main\n  implicit none\n  integer, parameter :: base = 7\n  integer :: value = base * 4 + 1\n  integer :: vector(2) = [base, base + 2]\n  if (value /= 29) error stop\n  if (any(vector /= [7,9])) error stop\n  print '(a)', 'type_declaration r805 constant expression ok'\nend program main\n"
    specs.append(runtime_spec(
        "r805_constant_expression_values", "R805", ["constant-expression-admission"], "positive-control",
        src, "type_declaration r805 constant expression ok\n",
        "8.2 R805 admits '=' constant-expr initialization; nondefault scalar and array values are observed at run time.",
        [mutation(src,
                  "integer :: value = base * 4 + 1\n  integer :: vector(2) = [base, base + 2]",
                  "integer :: value\n  integer :: vector(2) = [base, base + 2]\n  value = 30",
                  "remove_scalar_initializer"),
         mutation(src, "integer :: value = base * 4 + 1", "integer :: value = base * 4 + 2", "change_scalar_initializer"),
         mutation(src, "integer :: vector(2) = [base, base + 2]", "integer :: vector(2)\n  vector = [7,10]", "remove_array_initializer"),
         mutation(src, "integer :: vector(2) = [base, base + 2]", "integer :: vector(2) = [base, base + 3]", "change_array_initializer")]))

    src = "program main\n  implicit none\n  integer, target, save :: live_target\n  integer, pointer :: ptr => null()\n  live_target = 91\n  if (associated(ptr)) error stop\n  if (live_target /= 91) error stop\n  print '(a)', 'type_declaration r805 null init ok'\nend program main\n"
    specs.append(runtime_spec(
        "r805_r806_null_initialization", "R805", ["null-admission"], "positive-control",
        src, "type_declaration r805 null init ok\n",
        "8.2 R805 admits pointer initialization by => NULL(); the check observes disassociation, not a target value.",
        [mutation(src, "integer, pointer :: ptr => null()\n  live_target = 91",
                  "integer, pointer :: ptr\n  live_target = 91\n  ptr => live_target",
                  "remove_null_initializer")]))
    specs.append(runtime_spec(
        "r806_bare_null_reference", "R806", ["bare-null-reference"], "positive-control",
        src, "type_declaration r805 null init ok\n",
        "8.2 R806 defines null-init as a bare function-reference; this source uses intrinsic NULL with no arguments.",
        [mutation(src, "integer, pointer :: ptr => null()\n  live_target = 91",
                  "integer, pointer :: ptr\n  live_target = 91\n  ptr => live_target",
                  "remove_null_initializer")]))

    src = "program main\n  implicit none\n  interface which\n    procedure which_integer\n    procedure which_real\n  end interface\n  integer :: first = 11, second = 13\n  if (which(first) /= 1) error stop\n  if (which(second) /= 1) error stop\n  if (first /= 11) error stop\n  if (second /= 13) error stop\n  print '(a)', 'type_declaration s001 list type ok'\ncontains\n  integer function which_integer(value)\n    integer, intent(in) :: value\n    which_integer = 1\n  end function which_integer\n  integer function which_real(value)\n    real, intent(in) :: value\n    which_real = 2\n  end function which_real\nend program main\n"
    specs.append(runtime_spec(
        "s001_declared_type_across_list", "S8.2-001", ["declared-type-across-list"], "effect",
        src, "type_declaration s001 list type ok\n",
        "8.2 p1 applies the declared INTEGER type to both entities in the list; generic resolution and values observe it.",
        [mutation(src, "integer :: first = 11, second = 13", "real :: first = 11, second = 13", "change_list_declared_type"),
         mutation(src, "first = 11", "first = 12", "change_first_initializer", role="oracle-guard"),
         mutation(src, "second = 13", "second = 14", "change_second_initializer", role="oracle-guard")]))

    src = "program main\n  implicit none\n  character(len=4) :: base, short*2, wide*6, zero*0\n  if (len(base) /= 4) error stop\n  if (len(short) /= 2) error stop\n  if (len(wide) /= 6) error stop\n  if (len(zero) /= 0) error stop\n  base = 'wxyz'\n  short = 'uv'\n  wide = 'abcdef'\n  if (base /= 'wxyz') error stop\n  if (short /= 'uv') error stop\n  if (wide /= 'abcdef') error stop\n  print '(a)', 'type_declaration s001 character lengths ok'\nend program main\n"
    specs.append(runtime_spec(
        "s001_entity_character_length", "S8.2-001", ["entity-character-length"], "effect",
        src, "type_declaration s001 character lengths ok\n",
        "8.2 p1 permits entity *char-length to override the statement length; LEN is checked before equality.",
        [mutation(src, "short*2", "short", "remove_short_override"),
         mutation(src, "wide*6", "wide", "remove_wide_override")]))

    src = "program main\n  implicit none\n  integer, parameter :: named_len = 3\n  call automatic_len(5)\n  block\n    character :: literal*3, named*(named_len)\n    literal = 'abc'\n    named = 'xyz'\n    if (len(literal) /= 3) error stop\n    if (len(named) /= 3) error stop\n    if (literal /= 'abc') error stop\n    if (named /= 'xyz') error stop\n  end block\n  print '(a)', 'type_declaration c805 length forms ok'\ncontains\n  subroutine automatic_len(n)\n    integer, intent(in) :: n\n    character :: dummy_len*(n)\n    dummy_len = 'abcde'\n    if (len(dummy_len) /= n) error stop\n    if (dummy_len /= 'abcde') error stop\n  end subroutine automatic_len\nend program main\n"
    specs.append(runtime_spec(
        "c805_character_length_forms", "C805",
        ["constant-length-admission", "nonconstant-specification-admission"],
        "positive-control", src, "type_declaration c805 length forms ok\n",
        "8.2 C805 allows literal, named specification-expression and dummy specification-expression values in entity-decl char-length.",
        [mutation(src, "literal*3", "literal*2", "replace_literal_length"),
         mutation(src, "named*(named_len)", "named*2", "replace_named_length"),
         mutation(src, "dummy_len*(n)", "dummy_len*2", "replace_dummy_spec_length")]))

    src = "program main\n  implicit none\n  block\n    character, allocatable :: deferred*(:)\n    allocate(character(len=6) :: deferred)\n    deferred = 'pqrstu'\n    if (len(deferred) /= 6) error stop\n    if (deferred /= 'pqrstu') error stop\n  end block\n  print '(a)', 'type_declaration c805 deferred entity length ok'\nend program main\n"
    specs.append(runtime_spec(
        "c805_deferred_entity_length", "C805", ["deferred-length-contexts"], "positive-control",
        src, "type_declaration c805 deferred entity length ok\n",
        "8.2 C805 is reached by the entity-decl form deferred*(:); allocation establishes length6 before LEN and value checks.",
        [mutation(src, "deferred*(:)\n    allocate(character(len=6) :: deferred)",
                  "deferred*4\n    allocate(deferred)", "replace_deferred_entity_length")]))

    src = "program main\n  implicit none\n  integer, dimension(2) :: a, b(3)\n  a = [11,13]\n  b = [17,19,23]\n  call check_array(a, [11,13])\n  call check_array(b, [17,19,23])\n  print '(a)', 'type_declaration s002 array override ok'\ncontains\n  subroutine check_array(value, expected)\n    integer, intent(in) :: value(:), expected(:)\n    if (size(value) /= size(expected)) error stop\n    if (any(value /= expected)) error stop\n  end subroutine check_array\nend program main\n"
    specs.append(runtime_spec(
        "s002_entity_array_override", "S8.2-002", ["entity-array-override"], "effect",
        src, "type_declaration s002 array override ok\n",
        "8.2 p2 permits b's entity array-spec to override the DIMENSION(2) attr-spec; extents and values are observed.",
        [mutation(src, "a, b(3)\n  a = [11,13]\n  b = [17,19,23]",
                  "a, b\n  a = [11,13]\n  b = [17,19]", "remove_entity_array_spec")]))

    src = "program main\n  implicit none\n  integer :: i = 37\n  real :: r = 2.5\n  logical :: flag = .true.\n  character(len=3) :: word = 'xyz'\n  integer :: arr(3) = [4,5,6]\n  if (i /= 37) error stop\n  if (r /= 2.5) error stop\n  if (.not. flag) error stop\n  if (len(word) /= 3) error stop\n  if (word /= 'xyz') error stop\n  if (any(arr /= [4,5,6])) error stop\n  print '(a)', 'type_declaration s004 initializer values ok'\nend program main\n"
    specs.append(runtime_spec(
        "s004_initializer_values", "S8.2-004",
        ["numeric-admission", "character-kind-and-length-admission", "other-same-shape-admission"],
        "positive-control", src, "type_declaration s004 initializer values ok\n",
        "8.2 p4 admits these nonpointer initializers; exact integer, real, logical, character LEN/value and same-shape array values are observed.",
        [mutation(src, "integer :: i = 37", "integer :: i = 38", "change_integer_initializer"),
         mutation(src, "real :: r = 2.5", "real :: r = 3.5", "change_real_initializer"),
         mutation(src,
                  "logical :: flag = .true.\n  character(len=3) :: word = 'xyz'\n  integer :: arr(3) = [4,5,6]",
                  "logical :: flag\n  character(len=3) :: word = 'xyz'\n  integer :: arr(3) = [4,5,6]\n  flag = .false.",
                  "remove_logical_initializer"),
         mutation(src, "logical :: flag = .true.", "logical :: flag = .false.", "change_logical_initializer"),
         mutation(src, "character(len=3) :: word = 'xyz'", "character(len=3) :: word = 'xyq'", "change_character_initializer"),
         mutation(src, "integer :: arr(3) = [4,5,6]", "integer :: arr(3) = [4,5,7]", "change_array_initializer")]))
    return specs


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for spec in build_specs():
        dirname = "tests/fixtures/" + PREFIX + spec["stem"]
        spec["path"] = dirname + "/fixture.json"
        specs[spec["id"]] = spec
        files[root / dirname / "source.f90"] = spec["source"].encode("ascii")
        files[root / dirname / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    for rule, facets in SELECTED.items():
        if rule not in by_rule or not set(facets) <= set(by_rule[rule]["facets"]):
            raise ValueError(f"selected {rule} facet definitions changed")
        row = by_rule[rule]
        for facet in facets:
            row["pending"].pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    for rule, pending in RESTORED_PENDING.items():
        row = by_rule[rule]
        for facet, text in pending.items():
            if facet not in row["facets"]:
                raise ValueError(f"restored {rule} facet definition changed")
            row.setdefault("pending", {})[facet] = text
    return result


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if stale:
            raise ValueError("stale type-declaration fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("mutation is not bound to the complete parent input")
    start, end = mutation["span"]
    expected = mutation["expected"].encode("ascii")
    if raw[start:end] != expected:
        raise ValueError("mutation span does not match expected bytes")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def all_mutations(spec):
    return list(spec.get("mutations", []))


def compiler_family(compiler):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return "lfortran"
    if "gfortran" in name:
        return "gfortran"
    return name


def compiler_command(compiler, std, source, output):
    command = [str(compiler)]
    if std:
        if str(std).startswith("-"):
            command.append(str(std))
        elif compiler_family(compiler) == "lfortran":
            command.append("--std=" + str(std))
        else:
            command.append("-std=" + str(std))
    command += [str(source), "-o", str(output)]
    return command


KNOWN_PARENT_FAILURES = {
    "lfortran": {"C805_valid__type_declaration_c805_deferred_entity_length"},
}


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compile_run = subprocess.run(
        compiler_command(compiler, std, source, exe), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_run.returncode != 0 or not exe.is_file():
        return dict(status="compile-fail", stdout=compile_run.stdout, stderr=compile_run.stderr,
                    returncode=compile_run.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run.returncode == 0 and run.stdout == expected_stdout and run.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr,
                returncode=run.returncode)


def mutation_check(root=ROOT, compiler=None, std="", keep_work=False):
    root = Path(root)
    files, specs = build_corpus(root)
    del files
    family = compiler_family(compiler)
    work_dir = root / ".type_declaration_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    try:
        report = []
        parents = {}
        for spec in specs.values():
            if spec["manifest"]["expect"]["phase"] != "run":
                continue
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["completion"], spec["stem"] + "_parent")
            parents[spec["id"]] = parent["status"]
            if parent["status"] != "pass" and spec["id"] in KNOWN_PARENT_FAILURES.get(family, set()):
                for probe in all_mutations(spec):
                    report.append(dict(
                        id=spec["id"], mutation=probe["id"], expected=probe["expected"],
                        replacement=probe["replacement"], parent_status=parent["status"],
                        status="n/a", failed=None, stdout="", stderr="", returncode=None))
                continue
            for index, probe in enumerate(all_mutations(spec)):
                observed = run_one_source(
                    compiler, std, work_dir, mutated_source(spec, probe).decode("ascii"), spec["completion"],
                    f"{spec['stem']}_mut_{index:03d}")
                report.append(dict(
                    id=spec["id"], mutation=probe["id"], expected=probe["expected"],
                    replacement=probe["replacement"], parent_status=parent["status"],
                    status=observed["status"], failed=observed["status"] != "pass",
                    stdout=observed["stdout"], stderr=observed["stderr"], returncode=observed["returncode"]))
        unexpected_parent_failures = [
            dict(id=case_id, parent_status=status) for case_id, status in parents.items()
            if status != "pass" and case_id not in KNOWN_PARENT_FAILURES.get(family, set())
        ]
        survivors = [row for row in report if row["status"] == "pass"]
        invalid_mutants = [row for row in report if row["status"] == "compile-fail"]
        if unexpected_parent_failures or survivors or invalid_mutants:
            raise RuntimeError(json.dumps(
                dict(unexpected_parent_failures=unexpected_parent_failures, survivors=survivors[:5],
                     invalid_mutants=invalid_mutants[:5]), indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_check:
        if args.check or args.sync_catalogue:
            parser.error("--mutation-check is separate from generation/checking")
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        compile_fail = sum(row["status"] == "compile-fail" for row in report)
        run_fail = sum(row["status"] == "run-fail" for row in report)
        skipped = sum(row["status"] == "n/a" for row in report)
        print(f"Mutation-checked {len(report)} type-declaration mutations: "
              f"{run_fail} run-fail, {compile_fail} compile-fail, {skipped} n/a; all checked mutants failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    facets = sorted({facet for spec in specs.values() for facet in spec["facets"]})
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} type-declaration cases covering {len(facets)} facets.")


if __name__ == "__main__":
    main()
