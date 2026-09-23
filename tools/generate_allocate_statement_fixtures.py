#!/usr/bin/env python3
"""Form and required-diagnostic fixtures for Fortran 2023 ALLOCATE statements in 9.7.1.1."""

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "9.7.1.1"
CATALOGUE = "doc/catalogues/allocate_statement_9_7_1_1.json"
VIEW = "doc/fortran_2023_9_7_1_1.md"
SUMMARY_BEGIN = "<!-- BEGIN ALLOCATE STATEMENT FORM FIXTURES -->"
SUMMARY_END = "<!-- END ALLOCATE STATEMENT FORM FIXTURES -->"

EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "cannot read module", "missing interface", "syntax error", "malformed",
)

FACETS_BY_RULE = {
    "S9.7.1.1-001": ["allocatable-variable-created", "pointer-target-created"],
    "R929": ["bare-allocation-list", "typed-allocation"],
    "R930": ["stat-option", "errmsg-option", "source-option"],
    "R931": ["scalar-default-character-variable"],
    "R933": ["object-allocation-scalar"],
    "R934": ["variable-name-object"],
    "C936": ["allocatable-variable", "data-pointer", "ordinary-variable-rejected"],
    "C937": ["deferred-parameter-covered"],
    "C943": ["array-without-shape-or-same-rank-source-rejected"],
    "C944": ["scalar-without-shape"],
    "C946": ["shape-count-mismatch-rejected"],
    "C949": ["type-spec-without-source", "type-spec-and-source-rejected"],
    "C950": ["wrong-rank-source-rejected"],
    "C951": ["mismatched-source-kind-rejected"],
}
SELECTED_FACETS = {facet for facets in FACETS_BY_RULE.values() for facet in facets}
RESTORED_PENDING = {
    "C944": {
        "scalar-shape-spec-rejected": (
            "PENDING overlap note: a scalar allocate-object with any allocate-shape-spec-list "
            "necessarily has at least one allocate-shape-spec, so it violates both C944 "
            "(scalar allocate-object shall not have a shape-spec-list) and numbered C946 "
            "(shape-spec count shall equal rank; scalar rank is zero). No C944-only diagnostic "
            "fixture is shipped."
        )
    }
}

ORACLE_PREFIXES = {rule: f"{rule} ALLOCATE statement form fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} ALLOCATE statement fixture boundaries: " for rule in FACETS_BY_RULE}

ORACLE_TEXT = {
    "S9.7.1.1-001": (
        "one complete run/effect/f2023 program executes ALLOCATE on an ordinary INTEGER allocatable "
        "scalar and on an ordinary INTEGER pointer scalar. It then observes ALLOCATED(x), ASSOCIATED(ptr), "
        "and two nonzero assigned payload values, so both dynamic creation routes are reached without address, "
        "undefined-value, allocation-failure, or coarray assumptions."
    ),
    "R929": (
        "one complete run/effect/f2023 program contains both ALLOCATE(x) with a bare allocation-list and "
        "ALLOCATE(CHARACTER(LEN=5)::c) with a type-spec and double-colon. It observes allocation, length five, "
        "and nonblank payloads after the statements execute."
    ),
    "R930": (
        "one complete run/effect/f2023 program executes ALLOCATE(x,SOURCE=source_value,STAT=s,ERRMSG=msg). "
        "It observes ALLOCATED(x), STAT zero on success, and the nondefault SOURCE= scalar value 37 in x as "
        "required by 9.7.1.2p8. It also observes the ERRMSG variable unchanged from the nonblank same-length "
        "sentinel UNCHANGED as required by 9.7.5p2 when no error condition occurs."
    ),
    "R931": (
        "the same scalar default CHARACTER ERRMSG variable admission is represented by a complete successful "
        "ALLOCATE with ERRMSG=msg. The oracle checks LEN(msg)==9 before comparing the unchanged same-length "
        "sentinel, avoiding blank-padding ambiguity."
    ),
    "R933": (
        "one complete run/effect/f2023 program allocates an ordinary scalar allocate-object with no shape or "
        "coarray suffix and observes ALLOCATED plus a nonzero scalar payload."
    ),
    "R934": (
        "one complete run/effect/f2023 program uses an ordinary variable-name allocate-object, then observes "
        "allocation and a nonzero assigned payload. Structure-component and forbidden object forms remain separate."
    ),
    "C936": (
        "one complete run/effect/f2023 program demonstrates the two admitted allocate-object classes selected "
        "here: an allocatable variable and a data pointer. A paired compile/diagnose fixture changes only the "
        "declaration of the allocated scalar from allocatable to ordinary INTEGER; its one-property control restores "
        "ALLOCATABLE and must compile."
    ),
    "C937": (
        "one complete run/effect/f2023 program allocates CHARACTER(:),ALLOCATABLE with an explicit "
        "CHARACTER(LEN=5) type-spec, reaching the deferred-type-parameter premise and observing length five."
    ),
    "C943": (
        "one compile/diagnose fixture allocates a rank-one allocatable array with no allocate-shape-spec-list, "
        "no upper-bounds-expr form, and no SOURCE= expression. Its one-property control adds (1:3) and must compile."
    ),
    "C944": (
        "one complete run/effect/f2023 program allocates a scalar allocate-object without any shape-spec-list "
        "and observes the allocated scalar payload. The scalar-shape diagnostic facet remains pending because "
        "any scalar shape-spec-list necessarily also violates numbered C946's rank/count constraint."
    ),
    "C946": (
        "one compile/diagnose fixture allocates a rank-two allocatable array with one allocate-shape-spec. Its "
        "one-property control supplies two shape specs, preserving the object and bounds otherwise."
    ),
    "C949": (
        "one complete run/effect/f2023 program uses an explicit type-spec without SOURCE= and observes the "
        "selected character length and payload. A paired compile/diagnose fixture adds SOURCE= to the same "
        "type-spec ALLOCATE statement; its one-property control removes only SOURCE=."
    ),
    "C950": (
        "one compile/diagnose fixture supplies an explicit shape for a rank-one INTEGER allocatable array and a "
        "rank-two INTEGER SOURCE= expression, isolating SOURCE rank conformance from C943. Its control changes "
        "only the source expression to a rank-one array."
    ),
    "C951": (
        "one compile/diagnose fixture allocates REAL(REAL64) from a REAL(REAL32) SOURCE= expression, preserving "
        "the intrinsic declared type while changing only the kind type parameter. Its control uses REAL64 source."
    ),
}

LIMIT_TEXT = {
    rule: (
        "only the listed facets are owned by this generator. No coarray, image selector, multi-image behavior, "
        "allocation failure, allocation-status subclause coverage, pointer address identity, storage layout, "
        "finalization, unlimited polymorphic dynamic-type execution, SOURCE/MOLD execution transfer, or processor "
        "message vocabulary beyond the measured line-anchored diagnostics is claimed. Diagnostics require a real "
        "located error and exclude unsupported, not-implemented, internal, ASR/verifier, recovery, and resource-failure text."
    ) for rule in FACETS_BY_RULE
}

COMPLETIONS = {
    "creation": "ALLOCATE STATEMENT CREATION OK\n",
    "r929_forms": "ALLOCATE STATEMENT R929 FORMS OK\n",
    "r930_options": "ALLOCATE STATEMENT R930 OPTIONS OK\n",
    "r931_errmsg": "ALLOCATE STATEMENT R931 ERRMSG OK\n",
    "r933_scalar": "ALLOCATE STATEMENT R933 SCALAR OK\n",
    "r934_variable": "ALLOCATE STATEMENT R934 VARIABLE OK\n",
    "c936_targets": "ALLOCATE STATEMENT C936 TARGETS OK\n",
    "c937_deferred": "ALLOCATE STATEMENT C937 DEFERRED OK\n",
    "c944_scalar_no_shape": "ALLOCATE STATEMENT C944 SCALAR NO SHAPE OK\n",
    "c949_type_no_source": "ALLOCATE STATEMENT C949 TYPE NO SOURCE OK\n",
}

POSITIVE_CASES = {
    "creation": ("S9.7.1.1-001", FACETS_BY_RULE["S9.7.1.1-001"]),
    "r929_forms": ("R929", FACETS_BY_RULE["R929"]),
    "r930_options": ("R930", FACETS_BY_RULE["R930"]),
    "r931_errmsg": ("R931", FACETS_BY_RULE["R931"]),
    "r933_scalar": ("R933", FACETS_BY_RULE["R933"]),
    "r934_variable": ("R934", FACETS_BY_RULE["R934"]),
    "c936_targets": ("C936", ["allocatable-variable", "data-pointer"]),
    "c937_deferred": ("C937", FACETS_BY_RULE["C937"]),
    "c944_scalar_no_shape": ("C944", ["scalar-without-shape"]),
    "c949_type_no_source": ("C949", ["type-spec-without-source"]),
}

DIAGNOSTICS = {
    "c936_ordinary_variable": dict(
        rule="C936", facet="ordinary-variable-rejected", line_token="allocate(x)",
        messages=["Allocatable or Pointer type inputs", "neither a data pointer nor an allocatable variable"],
        invalid=("program allocate_statement_c936_ordinary_variable\n"
                 "  implicit none\n"
                 "  integer :: x\n"
                 "  allocate(x)\n"
                 "end program allocate_statement_c936_ordinary_variable\n"),
        control=("program allocate_statement_c936_ordinary_variable\n"
                 "  implicit none\n"
                 "  integer, allocatable :: x\n"
                 "  allocate(x)\n"
                 "end program allocate_statement_c936_ordinary_variable\n"),
        repair="add ALLOCATABLE to the declaration of x"),
    "c943_array_without_shape": dict(
        rule="C943", facet="array-without-shape-or-same-rank-source-rejected", line_token="allocate(a)",
        messages=["arrays should have dimensions specified", "Array specification required"],
        invalid=("program allocate_statement_c943_array_without_shape\n"
                 "  implicit none\n"
                 "  integer, allocatable :: a(:)\n"
                 "  allocate(a)\n"
                 "end program allocate_statement_c943_array_without_shape\n"),
        control=("program allocate_statement_c943_array_without_shape\n"
                 "  implicit none\n"
                 "  integer, allocatable :: a(:)\n"
                 "  allocate(a(1:3))\n"
                 "end program allocate_statement_c943_array_without_shape\n"),
        repair="add the rank-one allocate-shape-spec list (1:3)"),
    "c946_shape_count": dict(
        rule="C946", facet="shape-count-mismatch-rejected", line_token="allocate(a(1:2))",
        messages=["Rank mismatch in array reference"],
        invalid=("program allocate_statement_c946_shape_count\n"
                 "  implicit none\n"
                 "  integer, allocatable :: a(:,:)\n"
                 "  allocate(a(1:2))\n"
                 "end program allocate_statement_c946_shape_count\n"),
        control=("program allocate_statement_c946_shape_count\n"
                 "  implicit none\n"
                 "  integer, allocatable :: a(:,:)\n"
                 "  allocate(a(1:2,1:2))\n"
                 "end program allocate_statement_c946_shape_count\n"),
        repair="add the second rank-matching allocate-shape-spec"),
    "c949_type_and_source": dict(
        rule="C949", facet="type-spec-and-source-rejected", line_token="allocate(integer :: x, source=17)",
        messages=["SOURCE tag", "typespec", "type-spec"],
        invalid=("program allocate_statement_c949_type_and_source\n"
                 "  implicit none\n"
                 "  integer, allocatable :: x\n"
                 "  allocate(integer :: x, source=17)\n"
                 "end program allocate_statement_c949_type_and_source\n"),
        control=("program allocate_statement_c949_type_and_source\n"
                 "  implicit none\n"
                 "  integer, allocatable :: x\n"
                 "  allocate(integer :: x)\n"
                 "end program allocate_statement_c949_type_and_source\n"),
        repair="remove only SOURCE= from the ALLOCATE statement that has a type-spec"),
    "c950_wrong_rank_source": dict(
        rule="C950", facet="wrong-rank-source-rejected", line_token="allocate(a(1:2), source=reshape([11,22,33,44],[2,2]))",
        messages=["Dimension mismatch in `allocate` statement", "must be scalar or have the same rank"],
        invalid=("program allocate_statement_c950_wrong_rank_source\n"
                 "  implicit none\n"
                 "  integer, allocatable :: a(:)\n"
                 "  allocate(a(1:2), source=reshape([11,22,33,44],[2,2]))\n"
                 "end program allocate_statement_c950_wrong_rank_source\n"),
        control=("program allocate_statement_c950_wrong_rank_source\n"
                 "  implicit none\n"
                 "  integer, allocatable :: a(:)\n"
                 "  allocate(a(1:2), source=[11,22])\n"
                 "end program allocate_statement_c950_wrong_rank_source\n"),
        repair="replace only the rank-two SOURCE expression with a rank-one INTEGER source"),
    "c951_source_kind": dict(
        rule="C951", facet="mismatched-source-kind-rejected", line_token="allocate(x, source=real(1.0, real32))",
        messages=["same type as the allocated variable", "same kind type parameter"],
        invalid=("program allocate_statement_c951_source_kind\n"
                 "  use, intrinsic :: iso_fortran_env, only: real32, real64\n"
                 "  implicit none\n"
                 "  real(real64), allocatable :: x\n"
                 "  allocate(x, source=real(1.0, real32))\n"
                 "end program allocate_statement_c951_source_kind\n"),
        control=("program allocate_statement_c951_source_kind\n"
                 "  use, intrinsic :: iso_fortran_env, only: real32, real64\n"
                 "  implicit none\n"
                 "  real(real64), allocatable :: x\n"
                 "  allocate(x, source=real(1.0, real64))\n"
                 "end program allocate_statement_c951_source_kind\n"),
        repair="change only the SOURCE kind from REAL32 to REAL64"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def case_id(rule, kind, variant):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__allocate_statement_{variant}"


class RuntimeProgram:
    def __init__(self, variant):
        self.variant = variant
        self.text = ""
        self.mutations = []
        self.guards = []
        self.observations = 0

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def mutate_first(self, expected, replacement, id_, mutation="feature-under-test-substitution", category="feature"):
        start = self.text.index(expected)
        self.mutations.append(dict(id=id_, kind="source", category=category, mutation=mutation,
                                   expected=expected, replacement=replacement,
                                   span=[start, start + len(expected)],
                                   line=self.text[:start].count("\n") + 1))

    def guard(self, id_, condition, failure_stdout=None):
        token = f"ASTMT:{self.variant}:{id_}"
        if failure_stdout is None:
            failure_stdout = token + "\n"
        block = (f"  if ({condition}) then\n"
                 f"    write(*,'(a)') '{token}'\n"
                 "    error stop\n"
                 "  end if\n"
                 "  checks=checks+1\n")
        start = len(self.text)
        self.add(block)
        self.guards.append(dict(id=id_, condition=condition, line=self.text[:start].count("\n") + 1,
                                failure_stdout=failure_stdout))
        self.observations += 1

    def finish(self):
        self.guard("check-total", f"checks /= {self.observations}")
        literal = COMPLETIONS[self.variant].rstrip("\n")
        self.add(f"  write(*,'(a)') '{literal}'\n")


def creation_source():
    p = RuntimeProgram("creation")
    p.add("program allocate_statement_creation\n  implicit none\n"
          "  integer, allocatable :: x\n  integer, pointer :: ptr\n  integer :: checks\n  checks=0\n")
    p.add("  allocate(x)\n")
    p.mutate_first("  allocate(x)\n", "  ! allocate(x)\n", "feature-remove-allocatable-allocation")
    p.guard("allocatable-created", ".not. allocated(x)")
    p.add("  x=17\n")
    p.guard("allocatable-payload", "x /= 17")
    p.add("  allocate(ptr)\n")
    p.mutate_first("  allocate(ptr)\n", "  nullify(ptr)\n", "feature-remove-pointer-allocation")
    p.guard("pointer-created", ".not. associated(ptr)")
    p.add("  ptr=23\n")
    p.guard("pointer-payload", "ptr /= 23")
    p.finish()
    p.add("end program allocate_statement_creation\n")
    return p


def r929_source():
    p = RuntimeProgram("r929_forms")
    p.add("program allocate_statement_r929_forms\n  implicit none\n"
          "  integer, allocatable :: x\n  character(len=:), allocatable :: c\n  integer :: checks\n  checks=0\n")
    p.add("  allocate(x)\n")
    p.mutate_first("  allocate(x)\n", "  ! allocate(x)\n", "feature-remove-bare-allocation")
    p.guard("bare-allocated", ".not. allocated(x)")
    p.add("  x=19\n")
    p.guard("bare-payload", "x /= 19")
    p.add("  allocate(character(len=5) :: c)\n")
    p.mutate_first("character(len=5)", "character(len=4)", "feature-type-spec-length")
    p.guard("typed-allocated", ".not. allocated(c)")
    p.guard("typed-length", "len(c) /= 5")
    p.add("  c='abcde'\n")
    p.guard("typed-payload-length", "len(c) /= 5")
    p.guard("typed-payload", "c /= 'abcde'")
    p.finish()
    p.add("end program allocate_statement_r929_forms\n")
    return p


def r930_source(variant="r930_options"):
    p = RuntimeProgram(variant)
    program = "allocate_statement_" + variant
    p.add(f"program {program}\n  implicit none\n"
          "  integer, allocatable :: x\n  integer :: s, t, source_value\n"
          "  character(len=9) :: msg\n  integer :: checks\n"
          "  checks=0\n  s=-5\n  t=-9\n  source_value=37\n  msg='UNCHANGED'\n")
    p.mutate_first("source_value=37", "source_value=38", "input-source-value", category="input")
    p.mutate_first("msg='UNCHANGED'", "msg='MUTATION!'", "input-errmsg-prefill", category="input")
    p.add("  allocate(x, source=source_value, stat=s, errmsg=msg)\n")
    p.mutate_first("  allocate(x, source=source_value, stat=s, errmsg=msg)\n",
                   "  allocate(x, source=source_value, stat=s)\n"
                   "  if (allocated(x)) deallocate(x)\n"
                   "  msg='MUTATED!!'\n"
                   "  allocate(x, source=source_value, stat=s)\n",
                   "feature-remove-errmsg-specifier")
    p.mutate_first("source=source_value", "source=source_value+1", "feature-source-expression")
    p.mutate_first("stat=s", "stat=t", "feature-stat-variable")
    p.guard("stat-zero", "s /= 0")
    p.guard("allocated", ".not. allocated(x)")
    p.guard("source-value", "x /= 37")
    p.guard("errmsg-length", "len(msg) /= 9")
    p.guard("errmsg-unchanged", "msg /= 'UNCHANGED'")
    p.guard("alternate-stat-untouched", "t /= -9")
    p.finish()
    p.add(f"end program {program}\n")
    return p


def scalar_source(variant):
    p = RuntimeProgram(variant)
    program = "allocate_statement_" + variant
    p.add(f"program {program}\n  implicit none\n"
          "  integer, allocatable :: x\n  integer :: checks\n  checks=0\n")
    p.add("  allocate(x)\n")
    p.mutate_first("  allocate(x)\n", "  ! allocate(x)\n", "feature-remove-scalar-allocation")
    p.guard("scalar-allocated", ".not. allocated(x)")
    p.add("  x=41\n")
    p.guard("scalar-payload", "x /= 41")
    p.finish()
    p.add(f"end program {program}\n")
    return p


def c936_source():
    p = RuntimeProgram("c936_targets")
    p.add("program allocate_statement_c936_targets\n  implicit none\n"
          "  integer, allocatable :: x\n  integer, pointer :: ptr\n  integer :: checks\n  checks=0\n")
    p.add("  allocate(x)\n")
    p.mutate_first("  allocate(x)\n", "  ! allocate(x)\n", "feature-remove-allocatable-object")
    p.guard("allocatable-object", ".not. allocated(x)")
    p.add("  x=43\n")
    p.guard("allocatable-object-payload", "x /= 43")
    p.add("  allocate(ptr)\n")
    p.mutate_first("  allocate(ptr)\n", "  nullify(ptr)\n", "feature-remove-pointer-object")
    p.guard("data-pointer-object", ".not. associated(ptr)")
    p.add("  ptr=47\n")
    p.guard("data-pointer-payload", "ptr /= 47")
    p.finish()
    p.add("end program allocate_statement_c936_targets\n")
    return p


def typed_char_source(variant):
    p = RuntimeProgram(variant)
    program = "allocate_statement_" + variant
    p.add(f"program {program}\n  implicit none\n"
          "  character(len=:), allocatable :: c\n  integer :: checks\n  checks=0\n")
    p.add("  allocate(character(len=5) :: c)\n")
    p.mutate_first("character(len=5)", "character(len=4)", "feature-type-spec-length")
    p.guard("allocated", ".not. allocated(c)")
    p.guard("length", "len(c) /= 5")
    p.add("  c='vwxyz'\n")
    p.guard("payload-length", "len(c) /= 5")
    p.guard("payload", "c /= 'vwxyz'")
    p.finish()
    p.add(f"end program {program}\n")
    return p


POSITIVE_BUILDERS = {
    "creation": creation_source,
    "r929_forms": r929_source,
    "r930_options": lambda: r930_source("r930_options"),
    "r931_errmsg": lambda: r930_source("r931_errmsg"),
    "r933_scalar": lambda: scalar_source("r933_scalar"),
    "r934_variable": lambda: scalar_source("r934_variable"),
    "c936_targets": c936_source,
    "c937_deferred": lambda: typed_char_source("c937_deferred"),
    "c944_scalar_no_shape": lambda: scalar_source("c944_scalar_no_shape"),
    "c949_type_no_source": lambda: typed_char_source("c949_type_no_source"),
}


def positive_specs():
    specs = {}
    for variant, builder in POSITIVE_BUILDERS.items():
        rule, facets = POSITIVE_CASES[variant]
        program = builder()
        raw = program.text.encode("ascii")
        for mutation in program.mutations:
            start, end = mutation["span"]
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError(f"mutation span lost binding for {variant}:{mutation['id']}")
        name = case_id(rule, "valid", variant)
        specs[name] = dict(id=name, variant=variant, rule=rule, facets=list(facets), kind="valid",
                           evidence="effect", source=program.text, source_sha256=sha(raw),
                           completion=COMPLETIONS[variant], mutations=program.mutations,
                           guards=program.guards, expected_checks=program.observations)
    return specs


def diagnostic_specs():
    specs = {}
    for variant, info in DIAGNOSTICS.items():
        rule, facet = info["rule"], info["facet"]
        invalid = info["invalid"]
        control = info["control"]
        line = invalid[:invalid.index(info["line_token"])].count("\n") + 1
        invalid_name = case_id(rule, "invalid", variant)
        control_name = case_id(rule, "valid", variant + "_control")
        repair = dict(control_id=control_name, description=info["repair"], invalid_line=line,
                      invalid_sha256=sha(invalid.encode("ascii")), control_sha256=sha(control.encode("ascii")))
        specs[invalid_name] = dict(id=invalid_name, variant=variant, rule=rule, facets=[facet], kind="invalid",
                                   evidence="effect", source=invalid, source_sha256=repair["invalid_sha256"],
                                   diagnostic_line=line, messages=info["messages"], repair=repair)
        specs[control_name] = dict(id=control_name, variant=variant + "_control", rule=rule, facets=[facet],
                                   kind="valid", evidence="positive-control", source=control,
                                   source_sha256=repair["control_sha256"], controls=invalid_name, repair=repair)
    return specs


def source_specs():
    result = positive_specs()
    result.update(diagnostic_specs())
    return result


def manifest_for(spec):
    manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                    evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                    build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
    if spec["kind"] == "invalid":
        manifest["expect"] = dict(phase="compile", step="source", outcome="diagnose",
                                   diagnostic=dict(file="source.f90", line=spec["diagnostic_line"],
                                                   end_line=spec["diagnostic_line"],
                                                   contains_any=spec["messages"],
                                                   excludes_any=list(EXCLUSIONS)))
    elif spec["evidence"] == "positive-control":
        manifest["expect"] = dict(phase="compile", step="source", outcome="success")
    else:
        manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
        manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                   stdout=spec["completion"], stderr="")
    return manifest


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / ("allocate_statement_" + spec["variant"])
        manifest = manifest_for(spec)
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
    return files, specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def all_mutations(spec):
    return list(spec.get("mutations", []))


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_id = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        if rule not in by_id or not set(facets) <= set(by_id[rule]["facets"]):
            raise ValueError(f"selected {rule} facet definitions changed")
        row = by_id[rule]
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule],
                                         ORACLE_PREFIXES[rule] + ORACLE_TEXT[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule],
                                                    LIMIT_PREFIXES[rule] + LIMIT_TEXT[rule])
    for rule, pending in RESTORED_PENDING.items():
        by_id[rule].setdefault("pending", {}).update(pending)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for 9.7.1.1 view")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## ALLOCATE statement form fixture packet\n\n"
        "Ten complete runtime positives cover selected ordinary scalar, pointer, type-spec, "
        "SOURCE=, STAT= and ERRMSG= admission facets. Six required diagnostic negatives each "
        "have a one-property conforming compile control in this same packet. The diagnostics "
        "target only numbered constraints C936, C943, C946, C949, C950 and C951 and require located "
        "messages that are not unsupported-feature or compiler-internal failures.\n\n"
        "Coarray, image selector, multiple-image, MOLD= execution, "
        "special intrinsic synchronization/source types, allocation failures, and unnumbered "
        "dependency restrictions remain pending or owned elsewhere. The ERRMSG success case "
        "uses a nonblank same-length sentinel and 9.7.5p2's unchanged-value rule. The C944 "
        "scalar-shape diagnostic remains pending because every such negative also violates numbered C946.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("ALLOCATE statement summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


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
            raise ValueError("stale ALLOCATE statement fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def compiler_command(compiler, family, std, source, output):
    if family == "lfortran":
        return [compiler, "--std=" + std, "--no-color", str(source), "-o", str(output)]
    return [compiler, "-std=" + std, "-fdiagnostics-color=never", str(source), "-o", str(output)]


def mutation_check(root=ROOT, compiler=None, family=None, std=None, keep_work=False):
    root = Path(root)
    specs = source_specs()
    if family is None:
        name = Path(compiler).name.lower()
        family = "lfortran" if "lfortran" in name else "gfortran"
    if std is None:
        std = "f23" if family == "lfortran" else "f2023"
    work = root / ".allocate_statement_mutation_runs" / sha((str(compiler) + family + std).encode())[:12]
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    report = []
    try:
        for spec in specs.values():
            if spec["kind"] != "valid" or spec["evidence"] != "effect":
                continue
            for mutation in all_mutations(spec):
                folder = work / spec["variant"] / mutation["id"]
                folder.mkdir(parents=True)
                source = folder / "source.f90"
                exe = folder / "program"
                source.write_bytes(mutated_source(spec, mutation))
                comp = subprocess.run(compiler_command(compiler, family, std, source, exe),
                                      cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                run = None
                output = comp.stdout + comp.stderr
                if comp.returncode != 0:
                    raise RuntimeError(
                        f"runtime mutation did not compile on {family}: "
                        f"{spec['variant']} {mutation['id']}: {output[:400]}")
                run = subprocess.run([str(exe)], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, timeout=30)
                output += run.stdout + run.stderr
                failed = run.returncode != 0 or run.stdout != spec["completion"] or run.stderr != ""
                if not failed:
                    raise RuntimeError(f"mutation unexpectedly survived: {spec['variant']} {mutation['id']}")
                report.append(dict(variant=spec["variant"], mutation=mutation["id"],
                                   compile_returncode=comp.returncode,
                                   run_returncode=None if run is None else run.returncode,
                                   category=mutation["category"]))
    finally:
        if not keep_work:
            shutil.rmtree(work, ignore_errors=True)
    return report


def counts(specs):
    cases = len(specs)
    facets = len(SELECTED_FACETS)
    mutations = sum(len(all_mutations(spec)) for spec in specs.values())
    diagnostics = sum(1 for spec in specs.values() if spec["kind"] == "invalid")
    controls = sum(1 for spec in specs.values() if spec.get("evidence") == "positive-control")
    return cases, facets, mutations, diagnostics, controls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--family", choices=("lfortran", "gfortran"))
    parser.add_argument("--std")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.mutation_check))) > 1:
        parser.error("--check, --sync-catalogue and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.family, args.std, args.keep_work)
        print(f"Mutation-checked {len(report)} ALLOCATE statement runtime mutations; "
              "all compiled and failed at run time.")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    cases, facets, mutations, diagnostics, controls = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {cases} ALLOCATE statement cases, "
          f"{facets} facets, {diagnostics} diagnostics, {controls} controls and {mutations} runtime mutations.")


if __name__ == "__main__":
    main()
