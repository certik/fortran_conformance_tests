#!/usr/bin/env python3
"""Fixtures for Fortran 2023 pointer-assignment-stmt syntax and constraints."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "10.2.2.2"
CATALOGUE = "doc/catalogues/pointer_assignment_statement_syntax_10_2_2_2.json"
VIEW = "doc/fortran_2023_10_2_2_2.md"
PREFIX = "pointer_assignment_syntax_"
SUMMARY_BEGIN = "<!-- BEGIN POINTER ASSIGNMENT SYNTAX FIXTURES -->"
SUMMARY_END = "<!-- END POINTER ASSIGNMENT SYNTAX FIXTURES -->"

SELECTED = {
    "R1034": [
        "data-pointer-bounds-spec-list-form",
        "data-pointer-bounds-remapping-form",
        "procedure-pointer-target-form",
    ],
    "R1036": ["lower-bound-expr-colon-form"],
    "R1037": ["lower-upper-bound-expr-form"],
    "C1016": [
        "compatible-type-control",
        "incompatible-type-rejected",
        "kind-parameter-match-control",
        "kind-parameter-mismatch-rejected",
    ],
    "C1018": [
        "matching-bounds-spec-count",
        "too-few-bounds-specs-rejected",
        "too-many-bounds-specs-rejected",
    ],
    "C1019": [
        "matching-bounds-remapping-count",
        "too-few-bounds-remappings-rejected",
        "too-many-bounds-remappings-rejected",
    ],
    "C1022": ["same-rank-no-remap-control", "rank-mismatch-rejected"],
    "C1028": [
        "target-variable-designator-control",
        "non-target-non-pointer-designator-rejected",
        "vector-subscript-section-rejected",
    ],
}

ORACLE_PREFIXES = {
    "R1034": "R1034 pointer-assignment syntax fixtures: ",
    "R1036": "R1036 bounds-spec syntax fixture: ",
    "R1037": "R1037 bounds-remapping syntax fixture: ",
    "C1016": "C1016 data-target compatibility fixtures: ",
    "C1018": "C1018 bounds-spec count fixtures: ",
    "C1019": "C1019 bounds-remapping count fixtures: ",
    "C1022": "C1022 rank-without-remap fixtures: ",
    "C1028": "C1028 data-target eligibility fixtures: ",
}
LIMIT_PREFIXES = {
    rule: prefix.replace(" fixtures: ", " fixture boundaries: ").replace(" fixture: ", " fixture boundaries: ")
    for rule, prefix in ORACLE_PREFIXES.items()
}
ORACLES = {
    "R1034": ORACLE_PREFIXES["R1034"] + (
        "three positive-control/f2023 sources exercise the data-pointer bounds-spec-list form, "
        "the data-pointer bounds-remapping-list form, and the proc-pointer-object => proc-target form. "
        "The two data-pointer forms are complete run fixtures with nondefault pointer lower bounds, "
        "LBOUND/UBOUND/SHAPE observations, and two-way element aliasing checks. The procedure-pointer "
        "form assigns a named procedure pointer to an internal procedure and calls through it only to "
        "establish that the parsed source was reached; detailed procedure-pointer assignment semantics "
        "remain dependencies of 10.2.2.4."
    ),
    "R1036": ORACLE_PREFIXES["R1036"] + (
        "one bounds-spec positive-control uses p(-4:,6:) => t. The nondefault lower-bound "
        "expressions are observed through LBOUND after the assignment and are protected by a feature "
        "mutation that removes the parenthesized bounds-spec-list."
    ),
    "R1037": ORACLE_PREFIXES["R1037"] + (
        "one bounds-remapping positive-control uses p(-1:0,4:6) => v. Both lower and upper "
        "bound expressions are nondefault or nonunit where load-bearing, with SHAPE and two-way "
        "aliasing observations; conforming feature mutations change the remapped shape or shift "
        "the first remapped lower bound while preserving element count."
    ),
    "C1016": ORACLE_PREFIXES["C1016"] + (
        "four scalar compile fixtures isolate data-target compatibility. The type control and "
        "type negative differ only by the declared type of the pointer object while the scalar TARGET "
        "and rank are fixed. The kind control and kind negative use a parameterized derived type with "
        "kind parameter values 1 and 2, so no processor-dependent intrinsic kind availability is assumed; "
        "the negative differs only in the target's kind parameter value."
    ),
    "C1018": ORACLE_PREFIXES["C1018"] + (
        "one run positive-control has a rank-two pointer with exactly two bounds-specs, p(-4:,6:) => t. "
        "Two compile diagnostics keep target rank, type and TARGET status fixed while changing only the "
        "number of bounds-specs to one for a rank-two pointer or two for a rank-one pointer."
    ),
    "C1019": ORACLE_PREFIXES["C1019"] + (
        "one run positive-control has a rank-two pointer with exactly two bounds-remappings, "
        "p(-1:0,4:6) => v. Two compile diagnostics keep the rank-one TARGET storage and pointer type "
        "fixed while changing only the number of remapping pairs to one for a rank-two pointer or two "
        "for a rank-one pointer."
    ),
    "C1022": ORACLE_PREFIXES["C1022"] + (
        "a scalar positive-control has neither a bounds-remapping-list nor an upper-bounds-expr and "
        "uses equal pointer-object and target ranks. The negative changes only the target declaration "
        "to rank two, leaving type and TARGET status fixed and using no remapping or upper-bounds-expr."
    ),
    "C1028": ORACLE_PREFIXES["C1028"] + (
        "one scalar TARGET designator control, one one-property non-TARGET/non-POINTER diagnostic, "
        "and one vector-subscript diagnostic are provided. The non-target negative is repaired by adding "
        "only TARGET to the same scalar variable. The vector-subscript negative is repaired by replacing "
        "only t([1,2,3]) with the triplet section t(1:3)."
    ),
}
LIMITATIONS = {
    "R1034": LIMIT_PREFIXES["R1034"] + (
        "only three R1034 alternatives are discharged. The lower-bounds-expr array form and the "
        "lower/upper-bounds-expr array form remain pending. Runtime observations are used solely as "
        "portable reachability and non-vacuity evidence for the source forms; this packet does not "
        "claim independent 10.2.2.3 or 10.2.2.4 semantic-facet coverage."
    ),
    "R1036": LIMIT_PREFIXES["R1036"] + (
        "only the lower-bound-expr-colon form inside a rank-two data-pointer assignment is covered. "
        "The fixture does not claim expression-evaluation ordering, descriptor layout, or any bounds "
        "effect beyond the separately cited data-pointer assignment dependency used as an observation."
    ),
    "R1037": LIMIT_PREFIXES["R1037"] + (
        "only a two-dimensional pointer remapped over rank-one integer TARGET storage is covered. "
        "Storage sequence, addresses, TRANSFER/LOC, and remapping effects outside the observed bounds, "
        "shape and two element aliases are not tested."
    ),
    "C1016": LIMIT_PREFIXES["C1016"] + (
        "only scalar default INTEGER/REAL type mismatch and a simple parameterized-derived-type kind "
        "parameter mismatch are covered. Unlimited polymorphism, inheritance, length type parameters, "
        "allocatables, arrays and dynamic type changes remain pending or owned elsewhere."
    ),
    "C1018": LIMIT_PREFIXES["C1018"] + (
        "only too-few and too-many bounds-spec counts are tested. The diagnostics do not assert exact "
        "English, fatal status, a printed rule number, or any lower-bound semantic result."
    ),
    "C1019": LIMIT_PREFIXES["C1019"] + (
        "only too-few and too-many bounds-remapping counts are tested. The diagnostics do not assert "
        "storage-size conformance, contiguity semantics, exact English, or a printed rule number."
    ),
    "C1022": LIMIT_PREFIXES["C1022"] + (
        "only the no-remapping/no-upper-bounds rank-match and a rank mismatch diagnostic are covered. "
        "The remapping and upper-bounds exceptions remain pending except where syntax facets are "
        "separately discharged."
    ),
    "C1028": LIMIT_PREFIXES["C1028"] + (
        "only TARGET designator admission, a designator lacking both TARGET and POINTER, and a vector "
        "subscript section are covered. POINTER designator targets, data-pointer function references, "
        "non-designator expressions, and nonpointer function results remain pending."
    ),
}

EXCLUSIONS = [
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "cannot read module", "missing interface", "syntax error", "malformed",
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(name):
    return PREFIX + name


def compile_manifest(spec):
    invalid = spec["kind"] == "invalid"
    manifest = dict(
        schema_version=1,
        id=spec["id"],
        rule=spec["rule"],
        facets=spec["facets"],
        evidence="effect" if invalid else "positive-control",
        standard="f2023",
        files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        expect=dict(phase="compile", step="source", outcome="diagnose" if invalid else "success"),
    )
    if invalid:
        manifest["expect"]["diagnostic"] = dict(
            file="source.f90",
            line=spec["diagnostic_line"],
            end_line=spec["diagnostic_line"],
            contains_any=spec["contains_any"],
            excludes_any=EXCLUSIONS,
        )
    return manifest


def run_manifest(spec):
    return dict(
        schema_version=1,
        id=spec["id"],
        rule=spec["rule"],
        facets=spec["facets"],
        evidence="positive-control",
        standard="f2023",
        files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        link=dict(driver="fortran", objects=["source.o"], output="program"),
        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["stdout"], stderr=""),
    )


def bounds_spec_source():
    return """program pointer_assignment_syntax_bounds_spec
  implicit none
  integer, target :: t(2:4,10:11), other(2:4,10:11)
  integer, pointer :: p(:,:)
  integer :: checks
  checks = 0
  t(2,10) = 201
  t(3,10) = 301
  t(4,10) = 401
  t(2,11) = 202
  t(3,11) = 302
  t(4,11) = 402
  other(2,10) = -700
  other(3,10) = -700
  other(4,10) = -700
  other(2,11) = -700
  other(3,11) = -700
  other(4,11) = -700
  p(-4:,6:) => t
  if (any(lbound(p) /= [-4,6])) error stop 101
  checks = checks + 1
  if (any(ubound(p) /= [-2,7])) error stop 102
  checks = checks + 1
  if (any(shape(p) /= [3,2])) error stop 103
  checks = checks + 1
  p(-4,6) = 741
  if (t(2,10) /= 741) error stop 104
  checks = checks + 1
  t(3,11) = 852
  if (p(-3,7) /= 852) error stop 105
  checks = checks + 1
  if (other(2,10) /= -700) error stop 106
  checks = checks + 1
  if (checks /= 6) error stop 107
  write(*,'(a)') 'pointer_assignment_syntax_bounds_spec OK'
end program pointer_assignment_syntax_bounds_spec
"""


def remap_source():
    return """program pointer_assignment_syntax_remap
  implicit none
  integer, target :: v(-3:2), alt(-3:2)
  integer, pointer :: p(:,:)
  integer :: checks
  checks = 0
  v(-3) = 101
  v(-2) = 102
  v(-1) = 103
  v(0) = 104
  v(1) = 105
  v(2) = 106
  alt(-3) = -900
  alt(-2) = -900
  alt(-1) = -900
  alt(0) = -900
  alt(1) = -900
  alt(2) = -900
  p(-1:0,4:6) => v
  if (any(lbound(p) /= [-1,4])) error stop 201
  checks = checks + 1
  if (any(ubound(p) /= [0,6])) error stop 202
  checks = checks + 1
  if (any(shape(p) /= [2,3])) error stop 203
  checks = checks + 1
  p(0,6) = 961
  if (v(2) /= 961) error stop 204
  checks = checks + 1
  v(-1) = 862
  if (p(-1,5) /= 862) error stop 205
  checks = checks + 1
  if (alt(2) /= -900) error stop 206
  checks = checks + 1
  if (checks /= 6) error stop 207
  write(*,'(a)') 'pointer_assignment_syntax_remap OK'
end program pointer_assignment_syntax_remap
"""


def procedure_source():
    return """program pointer_assignment_syntax_procedure
  implicit none
  abstract interface
    integer function op(x)
      integer, intent(in) :: x
    end function op
  end interface
  procedure(op), pointer :: pp
  pp => double_it
  if (pp(21) /= 42) error stop 301
  write(*,'(a)') 'pointer_assignment_syntax_procedure OK'
contains
  integer function double_it(x)
    integer, intent(in) :: x
    double_it = 2*x
  end function double_it
  integer function triple_it(x)
    integer, intent(in) :: x
    triple_it = 3*x
  end function triple_it
end program pointer_assignment_syntax_procedure
"""


def source_templates():
    return {
        "type_control": """program pointer_assignment_syntax_type_mismatch
  implicit none
  integer, pointer :: p
  integer, target :: t
  p => t
end program pointer_assignment_syntax_type_mismatch
""",
        "type_mismatch": """program pointer_assignment_syntax_type_mismatch
  implicit none
  real, pointer :: p
  integer, target :: t
  p => t
end program pointer_assignment_syntax_type_mismatch
""",
        "kind_control": """program pointer_assignment_syntax_kind_mismatch
  implicit none
  type :: box(k)
    integer, kind :: k
    integer :: value
  end type box
  type(box(1)), pointer :: p
  type(box(1)), target :: t
  p => t
end program pointer_assignment_syntax_kind_mismatch
""",
        "kind_mismatch": """program pointer_assignment_syntax_kind_mismatch
  implicit none
  type :: box(k)
    integer, kind :: k
    integer :: value
  end type box
  type(box(1)), pointer :: p
  type(box(2)), target :: t
  p => t
end program pointer_assignment_syntax_kind_mismatch
""",
        "rank_control": """program pointer_assignment_syntax_rank_mismatch
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(2:5)
  p => t
end program pointer_assignment_syntax_rank_mismatch
""",
        "rank_mismatch": """program pointer_assignment_syntax_rank_mismatch
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(2:3,4:5)
  p => t
end program pointer_assignment_syntax_rank_mismatch
""",
        "bounds_spec_few": """program pointer_assignment_syntax_bounds_spec_few
  implicit none
  integer, pointer :: p(:,:)
  integer, target :: t(2:3,4:5)
  p(-4:) => t
end program pointer_assignment_syntax_bounds_spec_few
""",
        "bounds_spec_rank2_control": """program pointer_assignment_syntax_bounds_spec_few
  implicit none
  integer, pointer :: p(:,:)
  integer, target :: t(2:3,4:5)
  p(-4:,6:) => t
end program pointer_assignment_syntax_bounds_spec_few
""",
        "bounds_spec_many": """program pointer_assignment_syntax_bounds_spec_many
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(2:4)
  p(-4:,6:) => t
end program pointer_assignment_syntax_bounds_spec_many
""",
        "bounds_spec_rank1_control": """program pointer_assignment_syntax_bounds_spec_many
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(2:4)
  p(-4:) => t
end program pointer_assignment_syntax_bounds_spec_many
""",
        "remap_few": """program pointer_assignment_syntax_remap_few
  implicit none
  integer, pointer :: p(:,:)
  integer, target :: v(-3:2)
  p(-1:4) => v
end program pointer_assignment_syntax_remap_few
""",
        "remap_rank2_control": """program pointer_assignment_syntax_remap_few
  implicit none
  integer, pointer :: p(:,:)
  integer, target :: v(-3:2)
  p(-1:0,4:6) => v
end program pointer_assignment_syntax_remap_few
""",
        "remap_many": """program pointer_assignment_syntax_remap_many
  implicit none
  integer, pointer :: p(:)
  integer, target :: v(-3:2)
  p(-1:0,4:6) => v
end program pointer_assignment_syntax_remap_many
""",
        "remap_rank1_control": """program pointer_assignment_syntax_remap_many
  implicit none
  integer, pointer :: p(:)
  integer, target :: v(-3:2)
  p(-1:4) => v
end program pointer_assignment_syntax_remap_many
""",
        "target_control": """program pointer_assignment_syntax_non_target
  implicit none
  integer, pointer :: p
  integer, target :: t
  p => t
end program pointer_assignment_syntax_non_target
""",
        "non_target": """program pointer_assignment_syntax_non_target
  implicit none
  integer, pointer :: p
  integer :: t
  p => t
end program pointer_assignment_syntax_non_target
""",
        "vector_control": """program pointer_assignment_syntax_vector_subscript
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(5)
  p => t(1:3)
end program pointer_assignment_syntax_vector_subscript
""",
        "vector_subscript": """program pointer_assignment_syntax_vector_subscript
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(5)
  p => t([1,2,3])
end program pointer_assignment_syntax_vector_subscript
""",
    }


def line_of(source, needle):
    return source[:source.index(needle)].count("\n") + 1


def find_span(source, expected):
    start = source.index(expected)
    return [start, start + len(expected)]


def mutation(source, mid, expected, replacement, category):
    start, end = find_span(source, expected)
    return dict(
        id=mid,
        kind="feature" if category == "feature" else "guard",
        category=category,
        expected=expected,
        replacement=replacement,
        span=[start, end],
        line=source[:start].count("\n") + 1,
        mutation="feature-under-test-substitution" if category == "feature" else "guard-expectation-substitution",
    )


def runtime_mutations(variant, source):
    if variant == "bounds_spec":
        return [
            mutation(source, "remove-bounds-spec-list", "p(-4:,6:) => t", "p => t", "feature"),
            mutation(source, "swap-target", "p(-4:,6:) => t", "p(-4:,6:) => other", "feature"),
            mutation(source, "wrong-lbound-oracle", "[-4,6]", "[2,10]", "guard"),
            mutation(source, "wrong-ubound-oracle", "[-2,7]", "[4,11]", "guard"),
            mutation(source, "wrong-shape-oracle", "[3,2]", "[2,3]", "guard"),
            mutation(source, "wrong-pointer-to-target-alias", "t(2,10) /= 741", "t(2,10) /= 742", "guard"),
            mutation(source, "wrong-target-to-pointer-alias", "p(-3,7) /= 852", "p(-3,7) /= 853", "guard"),
        ]
    if variant == "remap":
        return [
            mutation(source, "change-remap-shape", "p(-1:0,4:6) => v", "p(-1:1,4:5) => v", "feature"),
            mutation(source, "shift-remap-lower-bound", "p(-1:0,4:6) => v", "p(0:1,4:6) => v", "feature"),
            mutation(source, "swap-target", "p(-1:0,4:6) => v", "p(-1:0,4:6) => alt", "feature"),
            mutation(source, "wrong-lbound-oracle", "[-1,4]", "[1,1]", "guard"),
            mutation(source, "wrong-ubound-oracle", "[0,6]", "[2,3]", "guard"),
            mutation(source, "wrong-shape-oracle", "[2,3]", "[3,2]", "guard"),
            mutation(source, "wrong-pointer-to-target-alias", "v(2) /= 961", "v(2) /= 962", "guard"),
            mutation(source, "wrong-target-to-pointer-alias", "p(-1,5) /= 862", "p(-1,5) /= 863", "guard"),
        ]
    if variant == "procedure":
        return [
            mutation(source, "swap-procedure-target", "pp => double_it", "pp => triple_it", "feature"),
            mutation(source, "wrong-procedure-call-oracle", "pp(21) /= 42", "pp(21) /= 63", "guard"),
        ]
    return []


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def source_specs():
    templates = source_templates()
    specs = {}

    def add(name, rule, facets, source, *, phase="compile", kind="valid", contains_any=None,
            diagnostic_needle="=>", variant=None, control=None, repair=None):
        sid = identifier(name)
        spec = dict(
            id=sid,
            name=name,
            rule=rule,
            facets=list(facets),
            kind=kind,
            source=source,
            source_sha256=sha(source.encode("ascii")),
            phase=phase,
            variant=variant or name,
        )
        if phase == "run":
            completion = source[source.rindex("write(*,'(a)') '") + len("write(*,'(a)') '"):]
            completion = completion[:completion.index("'")] + "\n"
            spec["stdout"] = completion
            spec["mutations"] = runtime_mutations(spec["variant"], source)
        else:
            spec["mutations"] = []
        if kind == "invalid":
            spec["contains_any"] = contains_any
            spec["diagnostic_line"] = line_of(source, diagnostic_needle)
            spec["control"] = control
            spec["repair"] = repair
        specs[sid] = spec

    bs = bounds_spec_source()
    rm = remap_source()
    pr = procedure_source()
    add("valid__R1034_bounds_spec_form", "R1034", ["data-pointer-bounds-spec-list-form"], bs,
        phase="run", variant="bounds_spec")
    add("valid__R1034_bounds_remap_form", "R1034", ["data-pointer-bounds-remapping-form"], rm,
        phase="run", variant="remap")
    add("valid__R1034_procedure_pointer_target", "R1034", ["procedure-pointer-target-form"], pr,
        phase="run", variant="procedure")
    add("valid__R1036_bounds_spec_colon", "R1036", ["lower-bound-expr-colon-form"], bs,
        phase="run", variant="bounds_spec")
    add("valid__R1037_bounds_remap_colon", "R1037", ["lower-upper-bound-expr-form"], rm,
        phase="run", variant="remap")
    add("valid__C1018_matching_bounds_spec_count", "C1018", ["matching-bounds-spec-count"],
        templates["bounds_spec_rank2_control"])
    add("invalid__C1018_too_few_bounds_specs", "C1018", ["too-few-bounds-specs-rejected"],
        templates["bounds_spec_few"], kind="invalid", contains_any=["rank mismatch in array reference"],
        diagnostic_needle="p(-4:) => t", control=identifier("valid__C1018_matching_bounds_spec_count"),
        repair=dict(expected="p(-4:) => t", replacement="p(-4:,6:) => t"))
    add("invalid__C1018_too_many_bounds_specs", "C1018", ["too-many-bounds-specs-rejected"],
        templates["bounds_spec_many"], kind="invalid", contains_any=["rank mismatch in array reference"],
        diagnostic_needle="p(-4:,6:) => t", control=identifier("valid__C1018_matching_bounds_spec_rank1"),
        repair=dict(expected="p(-4:,6:) => t", replacement="p(-4:) => t"))
    add("valid__C1018_matching_bounds_spec_rank1", "C1018", ["matching-bounds-spec-count"],
        templates["bounds_spec_rank1_control"])
    add("valid__C1019_matching_bounds_remap_count", "C1019", ["matching-bounds-remapping-count"],
        templates["remap_rank2_control"])
    add("invalid__C1019_too_few_bounds_remappings", "C1019", ["too-few-bounds-remappings-rejected"],
        templates["remap_few"], kind="invalid", contains_any=["rank mismatch in array reference"],
        diagnostic_needle="p(-1:4) => v", control=identifier("valid__C1019_matching_bounds_remap_count"),
        repair=dict(expected="p(-1:4) => v", replacement="p(-1:0,4:6) => v"))
    add("invalid__C1019_too_many_bounds_remappings", "C1019", ["too-many-bounds-remappings-rejected"],
        templates["remap_many"], kind="invalid", contains_any=["rank mismatch in array reference"],
        diagnostic_needle="p(-1:0,4:6) => v", control=identifier("valid__C1019_matching_bounds_remap_rank1"),
        repair=dict(expected="p(-1:0,4:6) => v", replacement="p(-1:4) => v"))
    add("valid__C1019_matching_bounds_remap_rank1", "C1019", ["matching-bounds-remapping-count"],
        templates["remap_rank1_control"])
    add("valid__C1016_compatible_type_control", "C1016", ["compatible-type-control"], templates["type_control"])
    add("invalid__C1016_incompatible_type", "C1016", ["incompatible-type-rejected"],
        templates["type_mismatch"], kind="invalid",
        contains_any=["different types in pointer assignment", "type mismatch"],
        diagnostic_needle="p => t", control=identifier("valid__C1016_compatible_type_control"),
        repair=dict(expected="real, pointer :: p", replacement="integer, pointer :: p"))
    add("valid__C1016_kind_parameter_match", "C1016", ["kind-parameter-match-control"], templates["kind_control"])
    add("invalid__C1016_kind_parameter_mismatch", "C1016", ["kind-parameter-mismatch-rejected"],
        templates["kind_mismatch"], kind="invalid",
        contains_any=["different types in pointer assignment", "kind", "type mismatch"],
        diagnostic_needle="p => t", control=identifier("valid__C1016_kind_parameter_match"),
        repair=dict(expected="type(box(2)), target :: t", replacement="type(box(1)), target :: t"))
    add("valid__C1022_same_rank_no_remap", "C1022", ["same-rank-no-remap-control"], templates["rank_control"])
    add("invalid__C1022_rank_mismatch", "C1022", ["rank-mismatch-rejected"],
        templates["rank_mismatch"], kind="invalid",
        contains_any=["different ranks in pointer assignment", "rank mismatch"],
        diagnostic_needle="p => t", control=identifier("valid__C1022_same_rank_no_remap"),
        repair=dict(expected="integer, target :: t(2:3,4:5)", replacement="integer, target :: t(2:5)"))
    add("valid__C1028_target_designator", "C1028", ["target-variable-designator-control"],
        templates["target_control"])
    add("invalid__C1028_non_target_designator", "C1028", ["non-target-non-pointer-designator-rejected"],
        templates["non_target"], kind="invalid",
        contains_any=["neither target nor pointer", "pointer assignment target"],
        diagnostic_needle="p => t", control=identifier("valid__C1028_target_designator"),
        repair=dict(expected="integer :: t", replacement="integer, target :: t"))
    add("valid__C1028_triplet_section_control", "C1028", ["target-variable-designator-control"],
        templates["vector_control"])
    add("invalid__C1028_vector_subscript_section", "C1028", ["vector-subscript-section-rejected"],
        templates["vector_subscript"], kind="invalid",
        contains_any=["vector subscript"], diagnostic_needle="p => t([1,2,3])",
        control=identifier("valid__C1028_triplet_section_control"),
        repair=dict(expected="t([1,2,3])", replacement="t(1:3)"))
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / spec["id"]
        manifest = run_manifest(spec) if spec["phase"] == "run" else compile_manifest(spec)
        spec["manifest"] = manifest
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        if rule not in by_rule or not set(facets) <= set(by_rule[rule]["facets"]):
            raise ValueError("selected pointer-assignment facets changed for " + rule)
        owner = by_rule[rule]
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        limitation = owner.get("oracle_limitation", "")
        old = (
            "This source-only catalogue records pending plans only. It creates no Fortran test program, "
            "invokes no processor, approves no fixture or oracle, and claims no coverage."
        )
        new = (
            "The original source-only catalogue recorded pending plans only; this generator supplies "
            "selected executable positive controls and diagnostic fixtures without granting unselected "
            "fixture approval, oracle approval, or universal coverage."
        )
        if old in limitation:
            limitation = limitation.replace(old, new)
        owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: see `doc/catalogues/pointer_assignment_statement_syntax_10_2_2_2.json`.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/pointer_assignment_statement_syntax_10_2_2_2.json`. "
        "Selected pointer-assignment syntax controls and diagnostics are now supplied; unselected facets "
        "remain pending and no whole-section coverage claim is made.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Pointer assignment syntax fixture packet\n\n"
        "Twenty selected facets of 10.2.2.2 are bound to generated fixtures. Run fixtures cover "
        "bounds-spec-list, bounds-remapping-list and procedure-pointer target source forms. The data "
        "pointer run cases use nondefault pointer lower bounds, explicit LBOUND/UBOUND/SHAPE checks, "
        "and two-way element aliasing writes; feature mutations remove the bounds-spec, change the "
        "remap shape, shift the remap lower bound, and swap targets. Compile diagnostics cover bounds-spec and "
        "bounds-remapping count errors plus selected type, kind, rank, target-attribute and vector-subscript "
        "constraints, each with a one-property conforming control.\n\n"
        "The packet deliberately does not discharge data-pointer assignment semantic facets from 10.2.2.3 "
        "or procedure-pointer assignment semantic/interface facets from 10.2.2.4. POINTER-target controls, "
        "data-pointer function targets, lower/upper-bounds-expr array forms, coarray/VOLATILE constraints, "
        "procedure component references and most procedure target eligibility alternatives remain pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("pointer assignment summary boundaries changed")
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
            raise ValueError("stale pointer assignment syntax fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def all_mutations(spec):
    return spec.get("mutations", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, check=args.check, sync_catalogue=args.sync_catalogue)
    facets = sorted({(spec["rule"], facet) for spec in specs.values() for facet in spec["facets"]})
    mutations = sum(len(all_mutations(spec)) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} pointer assignment syntax cases, "
          f"{len(facets)} selected facets, {mutations} runtime mutations.")


if __name__ == "__main__":
    main()
