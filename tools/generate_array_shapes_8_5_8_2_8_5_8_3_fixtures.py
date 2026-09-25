#!/usr/bin/env python3
"""Finite explicit-shape and assumed-shape array fixtures for 8.5.8.2/8.5.8.3."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPLICIT_SECTION = "8.5.8.2"
ASSUMED_SECTION = "8.5.8.3"
EXPLICIT_CATALOGUE = "doc/catalogues/explicit_shape_8_5_8_2.json"
ASSUMED_CATALOGUE = "doc/catalogues/assumed_shape_8_5_8_3.json"
EXPLICIT_VIEW = "doc/fortran_2023_8_5_8_2.md"
ASSUMED_VIEW = "doc/fortran_2023_8_5_8_3.md"
PREFIX = "array_shapes_8_5_8_2_8_5_8_3_"
EXPLICIT_SUMMARY_BEGIN = "<!-- BEGIN BATCH314 ARRAY SHAPES 8.5.8.2 -->"
EXPLICIT_SUMMARY_END = "<!-- END BATCH314 ARRAY SHAPES 8.5.8.2 -->"
ASSUMED_SUMMARY_BEGIN = "<!-- BEGIN BATCH314 ARRAY SHAPES 8.5.8.3 -->"
ASSUMED_SUMMARY_END = "<!-- END BATCH314 ARRAY SHAPES 8.5.8.3 -->"
KNOWN_PARENT_FAILURES = {
    "lfortran": {"S8_5_8_3_002_valid__array_shapes_assumed_empty_inquiry"},
}

SELECTED = {
    EXPLICIT_SECTION: {
        "R815": ["upper-only", "explicit-lower", "multidimensional-list"],
        "R816": ["scalar-integer-lower"],
        "R817": ["scalar-integer-upper"],
        "C831": ["constant-context-admissions", "subprogram-nonconstant", "block-nonconstant"],
        "S8.5.8.2-001": ["list-rank"],
    },
    ASSUMED_SECTION: {
        "R820": ["omitted-lower", "specified-scalar-lower"],
        "S8.5.8.3-001": ["list-rank"],
        "S8.5.8.3-002": ["omitted-defaults", "specified-scalar-lowers", "mixed-list-defaults", "zero-extent-inquiry-boundary"],
        "S8.5.8.3-003": ["whole-actual-extents", "section-effective-extent", "nonempty-upper-relation", "empty-extent-effect"],
    },
}

ORACLE_PREFIXES = {
    "R815": "Batch314 scalar explicit-shape syntax controls: ",
    "R816": "Batch314 lower-bound specification control: ",
    "R817": "Batch314 upper-bound specification control: ",
    "C831": "Batch314 explicit-shape context controls: ",
    "S8.5.8.2-001": "Batch314 explicit-shape list-rank effect: ",
    "R820": "Batch314 scalar assumed-shape syntax controls: ",
    "S8.5.8.3-001": "Batch314 assumed-shape list-rank effect: ",
    "S8.5.8.3-002": "Batch314 assumed-shape lower-bound effects: ",
    "S8.5.8.3-003": "Batch314 assumed-shape extent and upper-bound effects: ",
}
LIMIT_PREFIXES = {rule: prefix.replace(": ", " boundaries: ") for rule, prefix in ORACLE_PREFIXES.items()}

ORACLES = {
    "R815": ORACLE_PREFIXES["R815"] + (
        "one run/positive-control/f2023 program declares ordinary local INTEGER arrays with `a(4)`, "
        "`b(-2:1)` and `c(2,0:2)`. Direct LBOUND/UBOUND/RANK assertions distinguish the omitted "
        "lower bound, explicit scalar lower bound and two-entry scalar explicit-shape-spec list. "
        "Feature mutations replace the upper-only form by a same-extent explicit lower, shift the "
        "explicit lower range, or collapse the two-entry list to a rank-one declaration; all remain "
        "conforming and fail before the completion line."
    ),
    "R816": ORACLE_PREFIXES["R816"] + (
        "one run/positive-control/f2023 program uses the scalar INTEGER lower bound in `a(-2:1)` "
        "and directly observes LBOUND(a)=[-2]. Its feature mutation changes only that lower bound "
        "to -1 while preserving extent and conformance, making the lower-bound assertion fail."
    ),
    "R817": ORACLE_PREFIXES["R817"] + (
        "one run/positive-control/f2023 program admits positive, zero and negative scalar INTEGER "
        "upper bounds with `positive(3)`, `zero(0:0)` and `negative(-3:-1)` and directly observes "
        "their upper bounds. Feature mutations change upper-bound values while preserving valid "
        "ranges, so the upper-bound assertions are load-bearing."
    ),
    "C831": ORACLE_PREFIXES["C831"] + (
        "one run/positive-control/f2023 program covers constant main/module bounds and nonconstant "
        "subprogram and BLOCK contexts. Module and main arrays use named constants; a subroutine "
        "declares `local(n)` from an INTENT(IN) dummy; a BLOCK declares `b(n)` from a host scalar "
        "defined before the BLOCK statement. SIZE assertions use independent literals. Feature "
        "mutations change the named constant, the subprogram actual, or the host scalar before BLOCK, "
        "all as conforming programs that fail the corresponding assertion."
    ),
    "S8.5.8.2-001": ORACLE_PREFIXES["S8.5.8.2-001"] + (
        "one run/effect/f2023 program declares constant-bound explicit-shape arrays in a module and "
        "main program, including a zero-extent first dimension, and directly requires RANK=2 on the "
        "declared objects. The feature mutation changes the main two-specification list to one "
        "specification, so the direct rank assertion fails while the program remains conforming."
    ),
    "R820": ORACLE_PREFIXES["R820"] + (
        "one run/positive-control/f2023 program has complete explicit-interface assumed-shape dummies "
        "`x(:)` and `x(-3:)` associated with a defined rank-one INTEGER actual. Direct lower-bound "
        "assertions distinguish omitted default lower bound one and a specified scalar lower bound. "
        "Feature mutations swap those declarations to other conforming scalar lower-bound forms, "
        "making the assertions fail."
    ),
    "S8.5.8.3-001": ORACLE_PREFIXES["S8.5.8.3-001"] + (
        "one run/effect/f2023 program passes a rank-two INTEGER actual to a dummy declared `x(:,:)` "
        "and directly requires RANK(x)=2. Its feature mutation consistently changes the actual and "
        "dummy to rank one, preserving conformance and making the rank assertion fail."
    ),
    "S8.5.8.3-002": ORACLE_PREFIXES["S8.5.8.3-002"] + (
        "two run/effect/f2023 programs observe assumed-shape dummy lower bounds. The nonempty program "
        "passes a defined actual of shape [3,2] with nonunit actual lower bounds to dummies `x(:,:)`, "
        "`x(0:,-3:)` and `x(0:,:)`, requiring literal lower and upper bounds for omitted, specified "
        "and mixed scalar lower specifications. The empty-inquiry program passes `empty(5:3,-2:1)` "
        "to `x(5:,-2:)` and requires the legal whole-dummy empty-dimension LBOUND=[1,-2] and "
        "UBOUND=[0,1] without element access. Feature mutations alter the dummy lower specifications "
        "or change the empty actual to a singleton first dimension, so each assertion is load-bearing."
    ),
    "S8.5.8.3-003": ORACLE_PREFIXES["S8.5.8.3-003"] + (
        "two run/effect/f2023 programs observe extents and upper bounds. The nonempty program checks "
        "whole-actual SHAPE=[3,2]/SIZE=6, scalar-lower upper relation `x(-5:,7:)` -> UBOUND=[-3,8], "
        "and a section actual `v(1:5:2)` associated with `x(-1:)`, requiring extent three, upper one "
        "and values [11,13,15]. The empty-effect program passes `empty(5:3,-2:1)` to `x(:,:)` and "
        "requires RANK=2, SHAPE=[0,4] and SIZE=0 with no element access. Feature mutations change the "
        "whole actual extent, lower bounds, section stride or empty first dimension, all conforming."
    ),
}
LIMITATIONS = {
    "R815": LIMIT_PREFIXES["R815"] + "Only scalar-list admissions with small default INTEGER bounds are covered; declaration strides, vector bounds and malformed alternatives remain pending.",
    "R816": LIMIT_PREFIXES["R816"] + "Only the scalar INTEGER lower-bound admission is covered; restricted-function, prior-typing and context-source diagnostics remain pending.",
    "R817": LIMIT_PREFIXES["R817"] + "Only scalar INTEGER upper-bound admissions are covered; restricted-function, prior-typing and context-source diagnostics remain pending.",
    "C831": LIMIT_PREFIXES["C831"] + "Only constant main/module, subprogram and BLOCK positive controls are covered. Derived-type, interface-body and forbidden main/module nonconstant diagnostics remain pending.",
    "S8.5.8.2-001": LIMIT_PREFIXES["S8.5.8.2-001"] + "Only scalar explicit-shape-spec-list rank is covered. Vector-bounds rank and zero-size vector scalar behavior remain pending because the reference compiler rejects the F2023 vector-bound forms on this host.",
    "R820": LIMIT_PREFIXES["R820"] + "Only scalar assumed-shape positive controls are covered; expression/alternative-source diagnostics remain pending.",
    "S8.5.8.3-001": LIMIT_PREFIXES["S8.5.8.3-001"] + "Only list colon-count rank is covered. Vector-rank, zero-vector scalar and rank-clause source facets remain pending.",
    "S8.5.8.3-002": LIMIT_PREFIXES["S8.5.8.3-002"] + "Only scalar-list lower-bound effects and the empty whole-dummy inquiry boundary are covered. Vector lower-bound forms remain pending because the reference compiler rejects `x(lower:)` vector-bound syntax here.",
    "S8.5.8.3-003": LIMIT_PREFIXES["S8.5.8.3-003"] + "Only whole actual, section extent, nonempty upper relation and empty extent are covered. Interface/contiguity source gates remain pending; no address, copy, storage-layout or CONTIGUOUS strategy is asserted.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph for " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def case(rule, slug, facets, evidence, source, stdout, mutations, section):
    ident = rule.replace(".", "_").replace("-", "_") + "_valid__array_shapes_" + slug
    return dict(id=ident, rule=rule, slug=slug, facets=facets, evidence=evidence,
                source=source, stdout=stdout, mutations=mutations, section=section)


def repl(source, expected, replacement, mid, facet):
    start = source.index(expected)
    return dict(id=mid, facet=facet, replacements=[dict(span=[start, start + len(expected)], expected=expected, replacement=replacement)])


def multi_repl(source, edits, mid, facet):
    used = []
    reps = []
    for expected, replacement in edits:
        start = source.index(expected)
        if any(a <= start < b or start <= a < start + len(expected) for a, b in used):
            raise ValueError("overlapping mutation replacements")
        used.append((start, start + len(expected)))
        reps.append(dict(span=[start, start + len(expected)], expected=expected, replacement=replacement))
    return dict(id=mid, facet=facet, replacements=reps)


def source_specs():
    specs = []
    s = """program explicit_r815_scalar_forms
  implicit none
  integer :: checks
  integer :: upper_only(4)
  integer :: explicit_lower(-2:1)
  integer :: multi(2,0:2)
  checks=0
  if (any(lbound(upper_only) /= [1])) error stop 'R815 upper lower'
  checks=checks+1
  if (any(ubound(upper_only) /= [4])) error stop 'R815 upper upper'
  checks=checks+1
  if (any(lbound(explicit_lower) /= [-2])) error stop 'R815 explicit lower'
  checks=checks+1
  if (rank(multi) /= 2) error stop 'R815 multidimensional rank'
  checks=checks+1
  if (checks /= 4) error stop 'R815 check count'
  write(*,'(a)') 'ARRAY SHAPES R815 OK'
end program explicit_r815_scalar_forms
"""
    specs.append(case("R815", "explicit_r815_scalar_forms", SELECTED[EXPLICIT_SECTION]["R815"], "positive-control", s, "ARRAY SHAPES R815 OK\n", [
        repl(s, "upper_only(4)", "upper_only(0:3)", "feature-upper-only-to-explicit-lower", "upper-only"),
        repl(s, "explicit_lower(-2:1)", "explicit_lower(-1:2)", "feature-shift-explicit-lower", "explicit-lower"),
        repl(s, "multi(2,0:2)", "multi(6)", "feature-collapse-two-spec-list", "multidimensional-list"),
    ], EXPLICIT_SECTION))

    s = """program explicit_r816_lower_bound
  implicit none
  integer :: a(-2:1)
  if (any(lbound(a) /= [-2])) error stop 'R816 lower bound'
  write(*,'(a)') 'ARRAY SHAPES R816 OK'
end program explicit_r816_lower_bound
"""
    specs.append(case("R816", "explicit_r816_lower_bound", SELECTED[EXPLICIT_SECTION]["R816"], "positive-control", s, "ARRAY SHAPES R816 OK\n", [
        repl(s, "a(-2:1)", "a(-1:2)", "feature-lower-bound-value", "scalar-integer-lower"),
    ], EXPLICIT_SECTION))

    s = """program explicit_r817_upper_bound
  implicit none
  integer :: positive(3)
  integer :: zero(0:0)
  integer :: negative(-3:-1)
  if (any(ubound(positive) /= [3])) error stop 'R817 positive upper'
  if (any(ubound(zero) /= [0])) error stop 'R817 zero upper'
  if (any(ubound(negative) /= [-1])) error stop 'R817 negative upper'
  write(*,'(a)') 'ARRAY SHAPES R817 OK'
end program explicit_r817_upper_bound
"""
    specs.append(case("R817", "explicit_r817_upper_bound", SELECTED[EXPLICIT_SECTION]["R817"], "positive-control", s, "ARRAY SHAPES R817 OK\n", [
        repl(s, "positive(3)", "positive(4)", "feature-positive-upper-value", "scalar-integer-upper"),
    ], EXPLICIT_SECTION))

    s = """module explicit_c831_constants
  implicit none
  integer, parameter :: module_n=3
  integer :: module_a(module_n)
end module explicit_c831_constants
program explicit_c831_contexts
  use explicit_c831_constants
  implicit none
  integer, parameter :: main_n=2
  integer :: main_a(main_n)
  integer :: n
  if (size(module_a) /= 3) error stop 'C831 module constant'
  if (size(main_a) /= 2) error stop 'C831 main constant'
  call subprogram_case(4)
  n=5
  block
    integer :: b(n)
    if (size(b) /= 5) error stop 'C831 block nonconstant'
  end block
  write(*,'(a)') 'ARRAY SHAPES C831 OK'
contains
  subroutine subprogram_case(n)
    integer, intent(in) :: n
    integer :: local(n)
    if (size(local) /= 4) error stop 'C831 subprogram nonconstant'
  end subroutine subprogram_case
end program explicit_c831_contexts
"""
    specs.append(case("C831", "explicit_c831_contexts", SELECTED[EXPLICIT_SECTION]["C831"], "positive-control", s, "ARRAY SHAPES C831 OK\n", [
        repl(s, "module_n=3", "module_n=4", "feature-constant-context-size", "constant-context-admissions"),
        repl(s, "call subprogram_case(4)", "call subprogram_case(5)", "feature-subprogram-nonconstant-size", "subprogram-nonconstant"),
        repl(s, "n=5\n  block", "n=6\n  block", "feature-block-nonconstant-size", "block-nonconstant"),
    ], EXPLICIT_SECTION))

    s = """module explicit_s001_rank_module
  implicit none
  integer :: module_rank_two(2,3)
end module explicit_s001_rank_module
program explicit_s001_list_rank
  use explicit_s001_rank_module
  implicit none
  integer :: main_rank_two(2,3)
  integer :: zero_extent(0,3)
  if (rank(module_rank_two) /= 2) error stop 'S001 module rank'
  if (rank(main_rank_two) /= 2) error stop 'S001 main rank'
  if (rank(zero_extent) /= 2) error stop 'S001 zero extent rank'
  write(*,'(a)') 'ARRAY SHAPES EXPLICIT S001 OK'
end program explicit_s001_list_rank
"""
    specs.append(case("S8.5.8.2-001", "explicit_s001_list_rank", SELECTED[EXPLICIT_SECTION]["S8.5.8.2-001"], "effect", s, "ARRAY SHAPES EXPLICIT S001 OK\n", [
        repl(s, "main_rank_two(2,3)", "main_rank_two(6)", "feature-list-rank-collapse", "list-rank"),
    ], EXPLICIT_SECTION))

    s = """program assumed_r820_scalar_specs
  implicit none
  integer :: actual(-2:0)
  actual=17
  call omitted(actual)
  call specified(actual)
  write(*,'(a)') 'ARRAY SHAPES R820 OK'
contains
  subroutine omitted(x)
    integer, intent(in) :: x(:)
    if (any(lbound(x) /= [1])) error stop 'R820 omitted lower'
  end subroutine omitted
  subroutine specified(x)
    integer, intent(in) :: x(-3:)
    if (any(lbound(x) /= [-3])) error stop 'R820 specified lower'
  end subroutine specified
end program assumed_r820_scalar_specs
"""
    specs.append(case("R820", "assumed_r820_scalar_specs", SELECTED[ASSUMED_SECTION]["R820"], "positive-control", s, "ARRAY SHAPES R820 OK\n", [
        repl(s, "x(:)\n    if (any(lbound(x) /= [1]))", "x(0:)\n    if (any(lbound(x) /= [1]))", "feature-omitted-lower-to-zero", "omitted-lower"),
        repl(s, "x(-3:)\n    if (any(lbound(x) /= [-3]))", "x(-2:)\n    if (any(lbound(x) /= [-3]))", "feature-specified-lower-shift", "specified-scalar-lower"),
    ], ASSUMED_SECTION))

    s = """program assumed_s001_list_rank
  implicit none
  integer :: actual(3,2)
  actual=23
  call observe_rank(actual)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S001 OK'
contains
  subroutine observe_rank(x)
    integer, intent(in) :: x(:,:)
    if (rank(x) /= 2) error stop 'assumed list rank'
  end subroutine observe_rank
end program assumed_s001_list_rank
"""
    specs.append(case("S8.5.8.3-001", "assumed_s001_list_rank", SELECTED[ASSUMED_SECTION]["S8.5.8.3-001"], "effect", s, "ARRAY SHAPES ASSUMED S001 OK\n", [
        multi_repl(s, [("actual(3,2)", "actual(6)"), ("x(:,:)", "x(:)")], "feature-list-rank-collapse", "list-rank"),
    ], ASSUMED_SECTION))

    s = """program assumed_s002_scalar_lowers
  implicit none
  integer :: actual(-2:0,4:5)
  actual=31
  call omitted(actual)
  call specified(actual)
  call mixed(actual)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S002 LOWERS OK'
contains
  subroutine omitted(x)
    integer, intent(in) :: x(:,:)
    if (any(lbound(x) /= [1,1])) error stop 'S002 omitted lower'
    if (any(ubound(x) /= [3,2])) error stop 'S002 omitted upper'
  end subroutine omitted
  subroutine specified(x)
    integer, intent(in) :: x(0:,-3:)
    if (any(lbound(x) /= [0,-3])) error stop 'S002 specified lower'
    if (any(ubound(x) /= [2,-2])) error stop 'S002 specified upper'
  end subroutine specified
  subroutine mixed(x)
    integer, intent(in) :: x(0:,:)
    if (any(lbound(x) /= [0,1])) error stop 'S002 mixed lower'
    if (any(ubound(x) /= [2,2])) error stop 'S002 mixed upper'
  end subroutine mixed
end program assumed_s002_scalar_lowers
"""
    specs.append(case("S8.5.8.3-002", "assumed_s002_scalar_lowers", ["omitted-defaults", "specified-scalar-lowers", "mixed-list-defaults"], "effect", s, "ARRAY SHAPES ASSUMED S002 LOWERS OK\n", [
        repl(s, "x(:,:)\n    if (any(lbound(x) /= [1,1]))", "x(0:,-3:)\n    if (any(lbound(x) /= [1,1]))", "feature-omitted-to-specified-lowers", "omitted-defaults"),
        repl(s, "x(0:,-3:)\n    if (any(lbound(x) /= [0,-3]))", "x(:,:)\n    if (any(lbound(x) /= [0,-3]))", "feature-specified-to-omitted-lowers", "specified-scalar-lowers"),
        repl(s, "x(0:,:)\n    if (any(lbound(x) /= [0,1]))", "x(:,:)\n    if (any(lbound(x) /= [0,1]))", "feature-mixed-to-omitted-lowers", "mixed-list-defaults"),
    ], ASSUMED_SECTION))

    s = """program assumed_s002_empty_inquiry
  implicit none
  integer :: empty(5:3,-2:1)
  call observe_empty(empty)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S002 EMPTY OK'
contains
  subroutine observe_empty(x)
    integer, intent(in) :: x(5:,-2:)
    if (any(lbound(x) /= [1,-2])) error stop 'S002 empty lbound'
    if (any(ubound(x) /= [0,1])) error stop 'S002 empty ubound'
  end subroutine observe_empty
end program assumed_s002_empty_inquiry
"""
    specs.append(case("S8.5.8.3-002", "assumed_empty_inquiry", ["zero-extent-inquiry-boundary"], "effect", s, "ARRAY SHAPES ASSUMED S002 EMPTY OK\n", [
        repl(s, "empty(5:3,-2:1)", "empty(5:5,-2:1)", "feature-empty-to-singleton-actual", "zero-extent-inquiry-boundary"),
    ], ASSUMED_SECTION))

    s = """program assumed_s003_extent_relation
  implicit none
  integer :: actual(-2:0,4:5)
  integer :: v(5)
  actual=37
  v=[11,12,13,14,15]
  call whole(actual)
  call shifted_lowers(actual)
  call section_case(v(1:5:2))
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S003 EXTENTS OK'
contains
  subroutine whole(x)
    integer, intent(in) :: x(:,:)
    if (any(shape(x) /= [3,2])) error stop 'S003 whole shape'
    if (size(x) /= 6) error stop 'S003 whole size'
    if (count(x == 37) /= 6) error stop 'S003 whole values'
  end subroutine whole
  subroutine shifted_lowers(x)
    integer, intent(in) :: x(-5:,7:)
    if (any(ubound(x) /= [-3,8])) error stop 'S003 upper relation'
  end subroutine shifted_lowers
  subroutine section_case(x)
    integer, intent(in) :: x(-1:)
    if (any(shape(x) /= [3])) error stop 'S003 section shape'
    if (any(ubound(x) /= [1])) error stop 'S003 section upper'
    if (any(x /= [11,13,15])) error stop 'S003 section values'
  end subroutine section_case
end program assumed_s003_extent_relation
"""
    specs.append(case("S8.5.8.3-003", "assumed_s003_extent_relation", ["whole-actual-extents", "section-effective-extent", "nonempty-upper-relation"], "effect", s, "ARRAY SHAPES ASSUMED S003 EXTENTS OK\n", [
        repl(s, "actual(-2:0,4:5)", "actual(-2:1,4:5)", "feature-whole-actual-extent", "whole-actual-extents"),
        repl(s, "x(-5:,7:)\n    if (any(ubound(x) /= [-3,8]))", "x(-4:,7:)\n    if (any(ubound(x) /= [-3,8]))", "feature-lower-changes-upper-relation", "nonempty-upper-relation"),
        repl(s, "v(1:5:2)", "v(1:5:1)", "feature-section-effective-extent", "section-effective-extent"),
    ], ASSUMED_SECTION))

    s = """program assumed_s003_empty_extent
  implicit none
  integer :: empty(5:3,-2:1)
  call observe_empty_shape(empty)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S003 EMPTY OK'
contains
  subroutine observe_empty_shape(x)
    integer, intent(in) :: x(:,:)
    if (rank(x) /= 2) error stop 'S003 empty rank'
    if (any(shape(x) /= [0,4])) error stop 'S003 empty shape'
    if (size(x) /= 0) error stop 'S003 empty size'
  end subroutine observe_empty_shape
end program assumed_s003_empty_extent
"""
    specs.append(case("S8.5.8.3-003", "assumed_empty_extent", ["empty-extent-effect"], "effect", s, "ARRAY SHAPES ASSUMED S003 EMPTY OK\n", [
        repl(s, "empty(5:3,-2:1)", "empty(5:5,-2:1)", "feature-empty-extent-to-singleton", "empty-extent-effect"),
    ], ASSUMED_SECTION))
    for spec in specs:
        spec["source_sha256"] = sha(spec["source"].encode("ascii"))
    return {spec["id"]: spec for spec in specs}


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source no longer matches fingerprint")
    result = raw
    for rep in sorted(mutation["replacements"], key=lambda r: r["span"][0], reverse=True):
        start, end = rep["span"]
        if raw[start:end].decode("ascii") != rep["expected"]:
            raise ValueError(f"mutation span lost parent binding: {spec['id']} {mutation['id']}")
        result = result[:start] + rep["replacement"].encode("ascii") + result[end:]
    return result


def build_corpus(root=ROOT):
    root = Path(root)
    files = {}
    specs = source_specs()
    for spec in specs.values():
        directory = root / "tests/fixtures" / (PREFIX + spec["slug"])
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["stdout"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def sync_catalogue(catalogue, section):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    for rule, facets in SELECTED[section].items():
        row = by_rule[rule]
        for facet in facets:
            if facet not in row["facets"]:
                raise ValueError(f"unknown selected facet {rule}:{facet}")
            row["pending"].pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return result


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    if section == EXPLICIT_SECTION:
        sys.path.insert(0, str(Path(root) / "tools"))
        import generate_explicit_shape_fixtures as explicit_shape
        text = explicit_shape.render_view(catalogue, root)
        begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError(f"generated-region boundary changed for {section}")
        before, rest = text.split(begin)
        generated, after = begin + rest.split(end, 1)[0] + end, rest.split(end, 1)[1]
        summary = (EXPLICIT_SUMMARY_BEGIN + "\n\n"
                   "## Batch314 scalar explicit-shape controls\n\n"
                   "This packet adds positive controls for scalar explicit-shape syntax and C831 contexts, "
                   "plus one list-rank runtime effect. It intentionally leaves vector-bound and source-gated "
                   "diagnostic facets pending because the reference compiler rejects the F2023 vector-bound forms "
                   "or the catalogue calls for separate causal adjudication. Existing scalar-bound and entry-capture "
                   "generator regions are preserved.\n\n" + EXPLICIT_SUMMARY_END)
        if EXPLICIT_SUMMARY_BEGIN in after or EXPLICIT_SUMMARY_END in after:
            if after.count(EXPLICIT_SUMMARY_BEGIN) != 1 or after.count(EXPLICIT_SUMMARY_END) != 1:
                raise ValueError("explicit batch314 summary boundary changed")
            leading, owned = after.split(EXPLICIT_SUMMARY_BEGIN)
            _, trailing = owned.split(EXPLICIT_SUMMARY_END)
            after = leading + summary + trailing
        else:
            after = "\n\n" + summary + after
    else:
        path = Path(root) / ASSUMED_VIEW
        text = path.read_text()
        begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError(f"generated-region boundary changed for {section}")
        before, rest = text.split(begin)
        _, after = rest.split(end)
        before = before.replace(
            "This packet creates no fixtures, compiler observations, profiles, approvals,\n"
            "SourceUses entries or canonical links. Existing source and evidence bindings\n"
            "are measured separately in the handoff, not renewed to force currentness.",
            "Batch314 adds finite scalar assumed-shape fixtures and compiler observations\n"
            "for selected rank, lower-bound and extent facets. Source/evidence approvals,\n"
            "SourceUses entries and canonical links remain measured separately; vector and\n"
            "role/source-gated facets stay pending.")
        generated = begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end
        summary = (ASSUMED_SUMMARY_BEGIN + "\n\n"
                   "## Batch314 scalar assumed-shape effects\n\n"
                   "This packet adds scalar assumed-shape controls and runtime effects for colon-count rank, "
                   "default/specified/mixed lower bounds, whole and section effective extents, upper-bound relation, "
                   "and zero-extent handling. Vector lower-bound and rank-clause/source gates remain pending; the "
                   "reference compiler rejects the F2023 vector-bound dummy form used by those plans.\n\n" + ASSUMED_SUMMARY_END)
        if ASSUMED_SUMMARY_BEGIN in before or ASSUMED_SUMMARY_END in before:
            if before.count(ASSUMED_SUMMARY_BEGIN) != 1 or before.count(ASSUMED_SUMMARY_END) != 1:
                raise ValueError("assumed batch314 summary boundary changed")
            leading, owned = before.split(ASSUMED_SUMMARY_BEGIN)
            _, trailing = owned.split(ASSUMED_SUMMARY_END)
            before = leading + summary + trailing
        else:
            before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + generated + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    explicit_path, assumed_path = root / EXPLICIT_CATALOGUE, root / ASSUMED_CATALOGUE
    explicit = json.loads(explicit_path.read_text())
    assumed = json.loads(assumed_path.read_text())
    explicit_updated = sync_catalogue(explicit, EXPLICIT_SECTION)
    assumed_updated = sync_catalogue(assumed, ASSUMED_SECTION)
    explicit_view = render_view(EXPLICIT_SECTION, explicit_updated, root)
    assumed_view = render_view(ASSUMED_SECTION, assumed_updated, root)
    actual = {path for path in (root / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()}
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [path.relative_to(root).as_posix() for path in actual - set(files)]
        if explicit != explicit_updated:
            stale.append(EXPLICIT_CATALOGUE)
        if assumed != assumed_updated:
            stale.append(ASSUMED_CATALOGUE)
        if (root / EXPLICIT_VIEW).read_text() != explicit_view:
            stale.append(EXPLICIT_VIEW)
        if (root / ASSUMED_VIEW).read_text() != assumed_view:
            stale.append(ASSUMED_VIEW)
        if stale:
            raise SystemExit("stale array-shapes fixtures: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in array-shapes corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogues:
            explicit_path.write_text(json.dumps(explicit_updated, indent=2) + "\n")
            assumed_path.write_text(json.dumps(assumed_updated, indent=2) + "\n")
            (root / EXPLICIT_VIEW).write_text(explicit_view)
            (root / ASSUMED_VIEW).write_text(assumed_view)
    return files, specs


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    flag = f"--std={std}" if "lfortran" in name else f"-std={std}"
    return [compiler, flag, str(source), "-o", str(output)]


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(compiler).name.lower() else "gfortran"


def run_source(compiler, std, work, source_bytes):
    source = work / "source.f90"
    exe = work / "program"
    source.write_bytes(source_bytes)
    compiled = subprocess.run(compiler_command(compiler, std, source, exe), cwd=work, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if compiled.returncode != 0:
        return dict(status="compile-fail", output=compiled.stdout)
    executed = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=30)
    return dict(status="pass" if executed.returncode == 0 else "run-fail", output=executed.stdout,
                returncode=executed.returncode)


def mutation_check(root, compiler, std):
    root = Path(root)
    _, specs = build_corpus(root)
    family = compiler_family(compiler)
    workspace = root / f".array_shapes_mutations_{family}_{std}"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    failures = []
    checked = 0
    skipped = 0
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["id"] + "_parent")
            parent_dir.mkdir()
            parent = run_source(compiler, std, parent_dir, spec["source"].encode("ascii"))
            known_parent = spec["id"] in KNOWN_PARENT_FAILURES.get(family, set())
            if parent["status"] != "pass":
                if known_parent:
                    skipped += len(spec["mutations"])
                    continue
                failures.append(f"{spec['id']} parent failed ({parent['status']}):\n{parent['output']}")
                continue
            for mutation in spec["mutations"]:
                work = workspace / (spec["id"] + "_" + mutation["id"])
                work.mkdir()
                result = run_source(compiler, std, work, mutated_source(spec, mutation))
                if result["status"] == "compile-fail":
                    failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{result['output']}")
                    continue
                checked += 1
                if result["status"] == "pass":
                    failures.append(f"{spec['id']}:{mutation['id']} survived")
        if failures:
            raise SystemExit("\n\n".join(failures))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    note = f"; {skipped} skipped for known parent failures" if skipped else ""
    print(f"Mutation check failed all {checked} array-shapes mutants with {Path(compiler).name} {std}{note}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check))) > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler or not args.std:
            parser.error("--mutation-check requires --compiler and --std")
        mutation_check(args.root, args.compiler, args.std)
        return
    _, specs = generate(args.root, args.check, args.sync_catalogues)
    facet_total = sum(len(spec["facets"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} array-shapes fixtures and {facet_total} facet bindings.")


if __name__ == "__main__":
    main()
