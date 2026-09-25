#!/usr/bin/env python3
"""Additional Fortran 2023 7.5.10 structure-constructor fixtures."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.10"
CATALOGUE = "doc/catalogues/derived_types_7_5_10.json"
VIEW = "doc/fortran_2023_7_5_10.md"
TOPIC = "structure_constructor_7_5_10_b"
SUMMARY_BEGIN = "<!-- BEGIN STRUCTURE CONSTRUCTOR 7.5.10 B FIXTURES -->"
SUMMARY_END = "<!-- END STRUCTURE CONSTRUCTOR 7.5.10 B FIXTURES -->"
EXCLUDED = ["not implemented", "not supported", "unsupported", "internal compiler error", "asr verify",
            "llvm error", "compiler limitation", "segmentation fault"]

RUNTIME_CASES = {
    "pdt_kind_parameter": {
        "rule": "S7.5.10-001",
        "facets": ["parameter-specifier-source-use"],
        "completion": "STRUCTURE CONSTRUCTOR PDT KIND PARAMETER OK\n",
    },
    "ordinary_character_defined_assignment": {
        "rule": "S7.5.10-003",
        "facets": ["character-length-conversion", "no-defined-assignment-during-construction"],
        "completion": "STRUCTURE CONSTRUCTOR CHARACTER AND DEFINED ASSIGNMENT OK\n",
    },
    "private_omissions": {
        "rule": "C7107",
        "facets": ["omitted-private-default", "omitted-private-allocatable"],
        "completion": "STRUCTURE CONSTRUCTOR PRIVATE OMISSIONS OK\n",
    },
    "pointer_default_private_omission": {
        "rule": "S7.5.10-005",
        "facets": ["pointer-default-source-use", "private-omission-source-use"],
        "completion": "STRUCTURE CONSTRUCTOR POINTER DEFAULT PRIVATE OMIT OK\n",
    },
    "procedure_pointer_target": {
        "rule": "S7.5.10-007",
        "facets": ["procedure-target-call"],
        "completion": "STRUCTURE CONSTRUCTOR PROCEDURE POINTER TARGET OK\n",
    },
    "allocatable_same_rank_sources": {
        "rule": "S7.5.10-008",
        "facets": ["same-rank-allocatable-source-use", "same-rank-other-source-use"],
        "completion": "STRUCTURE CONSTRUCTOR ALLOCATABLE SAME RANK SOURCES OK\n",
    },
    "allocatable_source_matrix": {
        "rule": "S7.5.10-009",
        "facets": ["allocated-source-bounds-values", "nonallocatable-whole-array-source",
                   "ordinary-scalar-conversion"],
        "completion": "STRUCTURE CONSTRUCTOR ALLOCATABLE SOURCE MATRIX OK\n",
    },
    "generic_precedence": {
        "rule": "C7108",
        "facets": ["resolvable-function-precedence", "keyword-constructor-fallback", "type-constructor-fallback"],
        "completion": "STRUCTURE CONSTRUCTOR GENERIC PRECEDENCE OK\n",
    },
}
COMPILE_CASES = {
    "binding_keyword": {
        "rule": "C7106",
        "facets": ["binding-is-not-component"],
    }
}
FACETS_BY_RULE = {}
for spec in list(RUNTIME_CASES.values()) + list(COMPILE_CASES.values()):
    FACETS_BY_RULE.setdefault(spec["rule"], []).extend(spec["facets"])
FACETS_BY_RULE = {key: tuple(value) for key, value in FACETS_BY_RULE.items()}

ORACLE_PREFIXES = {
    "S7.5.10-001": "S7.5.10-001 structure-constructor PDT parameter fixture (batch317): ",
    "S7.5.10-003": "S7.5.10-003 structure-constructor character/assignment fixtures (batch317): ",
    "C7107": "C7107 structure-constructor private omission fixtures (batch317): ",
    "S7.5.10-005": "S7.5.10-005 structure-constructor omitted default/private fixtures (batch317): ",
    "S7.5.10-007": "S7.5.10-007 structure-constructor procedure pointer fixture (batch317): ",
    "S7.5.10-008": "S7.5.10-008 structure-constructor same-rank source fixtures (batch317): ",
    "S7.5.10-009": "S7.5.10-009 structure-constructor allocatable source matrix fixtures (batch317): ",
    "C7108": "C7108 structure-constructor generic precedence fixtures (batch317): ",
    "C7106": "C7106 structure-constructor binding keyword diagnostic (batch317): ",
}
LIMIT_PREFIXES = {rule: text.replace("fixtures", "boundaries").replace("fixture", "boundary").replace(
    "diagnostic", "diagnostic boundary") for rule, text in ORACLE_PREFIXES.items()}
ORACLES = {
    "S7.5.10-001": ORACLE_PREFIXES["S7.5.10-001"] +
        "one run/effect program constructs packet(k=kind(0.0))(payload=4.0) with separate PDT parameter and "
        "component lists, observes KIND(payload)=KIND(0.0) and exact value 4.0 through a typed observer.",
    "S7.5.10-003": ORACLE_PREFIXES["S7.5.10-003"] +
        "one run/effect program checks CHARACTER padding/truncation with LEN guards and exact nonblank values, "
        "then directly observes outer(src) while a matching defined assignment counter remains zero and the nested "
        "component value stays 17.",
    "C7107": ORACLE_PREFIXES["C7107"] +
        "one client-scope run/effect program constructs public types while omitting private defaulted and private "
        "allocatable components; owner-scope observers check the hidden default value 17 and unallocated hidden store.",
    "S7.5.10-005": ORACLE_PREFIXES["S7.5.10-005"] +
        "one run/effect program omits a default-initialized data pointer and private default/allocatable components; "
        "the owner observer checks disassociation, hidden value 17, unallocated private storage and public tag 29.",
    "S7.5.10-007": ORACLE_PREFIXES["S7.5.10-007"] +
        "one run/effect program supplies an eligible module function as a NOPASS procedure-pointer component, guards "
        "ASSOCIATED, then calls the component with argument 3 and requires exact result 8.",
    "S7.5.10-008": ORACLE_PREFIXES["S7.5.10-008"] +
        "one run/effect program supplies a same-rank allocated allocatable array source and a same-rank ordinary array "
        "source to allocatable components, checking allocated status, representative bounds and values for each branch.",
    "S7.5.10-009": ORACLE_PREFIXES["S7.5.10-009"] +
        "one run/effect program checks p7 allocated-source bounds/values, p8 whole-array bounds/values and p8 scalar "
        "REAL-to-INTEGER allocation/conversion after allocation guards.",
    "C7108": ORACLE_PREFIXES["C7108"] +
        "one run/effect program contrasts record(11) resolving to a same-named generic function with payload 29, "
        "record(payload=11) falling back to the constructor, and token(21) falling back when the same-named generic "
        "accepts only CHARACTER.",
    "C7106": ORACLE_PREFIXES["C7106"] +
        "one invalid compile fixture supplies get=19 where get is a type-bound binding, not a component; the paired "
        "positive control deletes only that component-spec and keeps payload present.",
}
LIMITATIONS = {
    "S7.5.10-001": LIMIT_PREFIXES["S7.5.10-001"] +
        "only a KIND PDT parameter is represented; LEN parameters and source-use graph reuse remain pending.",
    "S7.5.10-003": LIMIT_PREFIXES["S7.5.10-003"] +
        "only default CHARACTER padding/truncation and absence of a defined-assignment callback during direct "
        "construction are represented; mismatch diagnostics and assignment-owner reuse remain pending.",
    "C7107": LIMIT_PREFIXES["C7107"] +
        "only legal omission of private defaulted/allocatable components is represented; type-name access, parent "
        "private leaves and broader use-graph evidence remain pending.",
    "S7.5.10-005": LIMIT_PREFIXES["S7.5.10-005"] +
        "only omitted pointer default status and private omission effects are represented; default-vs-explicit owner "
        "reuse remains pending.",
    "S7.5.10-007": LIMIT_PREFIXES["S7.5.10-007"] +
        "only a live module procedure target with matching explicit interface is represented; target repair, "
        "contiguity/interface and lifetime graphs remain pending.",
    "S7.5.10-008": LIMIT_PREFIXES["S7.5.10-008"] +
        "only same-rank allocated allocatable and ordinary-array source admissions are represented; unallocated "
        "source status, rank-mismatch and NULL identity/context source-use remain pending.",
    "S7.5.10-009": LIMIT_PREFIXES["S7.5.10-009"] +
        "only allocated integer array source, nonallocatable whole-array source and scalar conversion are represented; "
        "unallocated, expression-bound, polymorphic, zero-extent and assignment-boundary cases remain pending.",
    "C7108": LIMIT_PREFIXES["C7108"] +
        "only unambiguous same-named generic function precedence and two constructor fallbacks are represented; "
        "generic ambiguity and elemental/name-association source-use remain pending.",
    "C7106": LIMIT_PREFIXES["C7106"] +
        "the diagnostic is line-anchored and excludes unsupported/internal failures, but no exact wording or fatal "
        "status is required.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def runtime_id(variant):
    rule = RUNTIME_CASES[variant]["rule"]
    return rule.replace(".", "_").replace("-", "_") + "_valid__" + TOPIC + "_" + variant


def compile_id(variant, invalid):
    rule = COMPILE_CASES[variant]["rule"]
    role = "invalid" if invalid else "valid"
    suffix = variant if invalid else variant + "_repair"
    return rule.replace(".", "_").replace("-", "_") + f"_{role}__" + TOPIC + "_" + suffix


def find_edit(source, expected, replacement, occurrence=1):
    matches = [m for m in re.finditer(re.escape(expected), source)]
    if len(matches) < occurrence:
        raise ValueError(f"{expected!r} has {len(matches)} matches, need {occurrence}")
    m = matches[occurrence - 1]
    return {"span": [m.start(), m.end()], "expected": expected, "replacement": replacement}


def mutation(id_, facet, source, edits):
    if isinstance(edits, dict):
        edits = [edits]
    return {"id": id_, "facet": facet, "group": "feature", "kind": "feature", "edits": edits}


def source_header(rule, facets):
    return f"! rule: {rule}\n! covers: {', '.join(facets)}\n! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.\n"


def runtime_source(variant):
    spec = RUNTIME_CASES[variant]
    h = source_header(spec["rule"], spec["facets"])
    if variant == "pdt_kind_parameter":
        return h + """module sc_b_pdt_mod
implicit none
type :: packet(k)
  integer, kind :: k=kind(0.0)
  real(kind=k) :: payload
end type packet
contains
subroutine observe(x)
  type(packet(kind(0.0))), intent(in) :: x
  integer :: checks
  checks = 0
  if (kind(x%payload) /= kind(0.0)) error stop 1
  checks = checks + 1
  if (x%payload /= 4.0) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
end subroutine observe
end module sc_b_pdt_mod
program structure_constructor_7_5_10_b_pdt_kind_parameter
use sc_b_pdt_mod
implicit none
call observe(packet(k=kind(0.0))(payload=4.0))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR PDT KIND PARAMETER OK'
end program structure_constructor_7_5_10_b_pdt_kind_parameter
"""
    if variant == "ordinary_character_defined_assignment":
        return h + """module sc_b_assignment_mod
implicit none
integer :: calls = 0
type :: chars
  character(len=5) :: wide
  character(len=2) :: narrow
end type chars
type :: inner
  integer :: value
contains
  procedure :: assign_inner
  generic :: assignment(=) => assign_inner
end type inner
type :: outer
  type(inner) :: item
end type outer
contains
subroutine assign_inner(lhs, rhs)
  class(inner), intent(out) :: lhs
  type(inner), intent(in) :: rhs
  calls = calls + 1
  lhs%value = rhs%value + 100
end subroutine assign_inner
subroutine observe_chars(x)
  type(chars), intent(in) :: x
  if (len(x%wide) /= 5) error stop 1
  if (x%wide /= 'AB   ') error stop 2
  if (len(x%narrow) /= 2) error stop 3
  if (x%narrow /= 'WX') error stop 4
end subroutine observe_chars
subroutine observe_outer(x)
  type(outer), intent(in) :: x
  if (x%item%value /= 17) error stop 5
  if (calls /= 0) error stop 6
end subroutine observe_outer
end module sc_b_assignment_mod
program structure_constructor_7_5_10_b_character_assignment
use sc_b_assignment_mod
implicit none
character(len=2) :: short
character(len=4) :: long
character(len=1) :: sentinel
 type(inner) :: src
 type(outer) :: scratch
sentinel = '#'
short = 'AB'
long = 'WXYZ'
src%value = 17
calls = 0
call observe_chars(chars(short, long))
call observe_outer(outer(src))
if (sentinel /= '#') error stop 7
write(*,'(a)') 'STRUCTURE CONSTRUCTOR CHARACTER AND DEFINED ASSIGNMENT OK'
end program structure_constructor_7_5_10_b_character_assignment
""".replace("\n type(inner)", "\ntype(inner)").replace("\n type(outer)", "\ntype(outer)")
    if variant == "private_omissions":
        return h + """module sc_b_private_mod
implicit none
private
public :: default_box, alloc_box, observe_default_box, observe_alloc_box
type :: default_box
  integer, public :: tag
  integer, private :: hidden = 17
end type default_box
type :: alloc_box
  integer, public :: tag
  integer, allocatable, private :: store(:)
end type alloc_box
contains
subroutine observe_default_box(x)
  type(default_box), intent(in) :: x
  if (x%tag /= 29) error stop 1
  if (x%hidden /= 17) error stop 2
end subroutine observe_default_box
subroutine observe_alloc_box(x)
  type(alloc_box), intent(in) :: x
  if (x%tag /= 31) error stop 3
  if (allocated(x%store)) error stop 4
end subroutine observe_alloc_box
end module sc_b_private_mod
program structure_constructor_7_5_10_b_private_omissions
use sc_b_private_mod
implicit none
call observe_default_box(default_box(tag=29))
call observe_alloc_box(alloc_box(tag=31))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR PRIVATE OMISSIONS OK'
end program structure_constructor_7_5_10_b_private_omissions
"""
    if variant == "pointer_default_private_omission":
        return h + """module sc_b_default_mod
implicit none
private
public :: record, observe_record, default_target
integer, target, save :: default_target = 41
type :: record
  integer, public :: tag
  integer, pointer, public :: p => null()
  integer, private :: hidden = 17
  integer, allocatable, private :: store(:)
end type record
contains
subroutine observe_record(x)
  type(record), intent(in) :: x
  if (x%tag /= 29) error stop 1
  if (associated(x%p)) error stop 2
  if (x%hidden /= 17) error stop 3
  if (allocated(x%store)) error stop 4
end subroutine observe_record
end module sc_b_default_mod
program structure_constructor_7_5_10_b_pointer_default_private
use sc_b_default_mod
implicit none
call observe_record(record(tag=29))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR POINTER DEFAULT PRIVATE OMIT OK'
end program structure_constructor_7_5_10_b_pointer_default_private
"""
    if variant == "procedure_pointer_target":
        return h + """module sc_b_procptr_mod
implicit none
abstract interface
  integer function fun(i)
    integer, intent(in) :: i
  end function fun
end interface
type :: holder
  procedure(fun), pointer, nopass :: action => null()
end type holder
contains
integer function worker(i)
  integer, intent(in) :: i
  worker = i + 5
end function worker
integer function other_worker(i)
  integer, intent(in) :: i
  other_worker = i + 6
end function other_worker
subroutine observe(x)
  type(holder), intent(in) :: x
  if (.not. associated(x%action)) error stop 1
  if (x%action(3) /= 8) error stop 2
end subroutine observe
end module sc_b_procptr_mod
program structure_constructor_7_5_10_b_procptr
use sc_b_procptr_mod
implicit none
call observe(holder(worker))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR PROCEDURE POINTER TARGET OK'
end program structure_constructor_7_5_10_b_procptr
"""
    if variant == "allocatable_same_rank_sources":
        return h + """program structure_constructor_7_5_10_b_same_rank_sources
implicit none
type :: box
  integer, allocatable :: from_alloc(:)
  integer, allocatable :: from_ordinary(:)
end type box
integer, allocatable :: source(:)
integer :: ordinary(-2:0)
allocate(source(-2:0))
source(-2)=11
source(-1)=13
source(0)=17
ordinary(-2)=21
ordinary(-1)=23
ordinary(0)=27
call observe(box(from_alloc=source, from_ordinary=ordinary))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR ALLOCATABLE SAME RANK SOURCES OK'
contains
subroutine observe(x)
  type(box), intent(in) :: x
  if (.not. allocated(x%from_alloc)) error stop 1
  if (lbound(x%from_alloc,1) /= -2) error stop 2
  if (x%from_alloc(-1) /= 13) error stop 3
  if (.not. allocated(x%from_ordinary)) error stop 4
  if (lbound(x%from_ordinary,1) /= -2) error stop 5
  if (x%from_ordinary(-1) /= 23) error stop 6
end subroutine observe
end program structure_constructor_7_5_10_b_same_rank_sources
"""
    if variant == "allocatable_source_matrix":
        return h + """program structure_constructor_7_5_10_b_alloc_matrix
implicit none
type :: box
  integer, allocatable :: from_alloc(:)
  integer, allocatable :: from_ordinary(:)
  integer, allocatable :: scalar
end type box
integer, allocatable :: source(:)
integer :: ordinary(-2:0)
real :: scalar_source
allocate(source(-2:0))
source(-2)=11
source(-1)=13
source(0)=17
ordinary(-2)=21
ordinary(-1)=23
ordinary(0)=27
scalar_source = 4.0
call observe(box(from_alloc=source, from_ordinary=ordinary, scalar=scalar_source))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR ALLOCATABLE SOURCE MATRIX OK'
contains
subroutine observe(x)
  type(box), intent(in) :: x
  if (.not. allocated(x%from_alloc)) error stop 1
  if (lbound(x%from_alloc,1) /= -2) error stop 2
  if (ubound(x%from_alloc,1) /= 0) error stop 3
  if (x%from_alloc(-1) /= 13) error stop 4
  if (.not. allocated(x%from_ordinary)) error stop 5
  if (lbound(x%from_ordinary,1) /= -2) error stop 6
  if (x%from_ordinary(-1) /= 23) error stop 7
  if (.not. allocated(x%scalar)) error stop 8
  if (x%scalar /= 4) error stop 9
end subroutine observe
end program structure_constructor_7_5_10_b_alloc_matrix
"""
    if variant == "generic_precedence":
        return h + """module sc_b_generic_mod
implicit none
type :: record
  integer :: payload
end type record
type :: token
  integer :: payload
end type token
interface record
  module procedure make_record
end interface record
interface token
  module procedure make_token
end interface token
contains
function make_record(n) result(out)
  integer, intent(in) :: n
  type(record) :: out
  out%payload = n + 18
end function make_record
function make_token(s) result(out)
  character(*), intent(in) :: s
  type(token) :: out
  out%payload = len(s) + 40
end function make_token
subroutine observe()
  type(record) :: generic_value
  type(record) :: keyword_value
  type(token) :: fallback_value
  generic_value = record(11)
  keyword_value = record(payload=11)
  fallback_value = token(21)
  if (generic_value%payload /= 29) error stop 1
  if (keyword_value%payload /= 11) error stop 2
  if (fallback_value%payload /= 21) error stop 3
end subroutine observe
end module sc_b_generic_mod
program structure_constructor_7_5_10_b_generic_precedence
use sc_b_generic_mod
implicit none
call observe()
write(*,'(a)') 'STRUCTURE CONSTRUCTOR GENERIC PRECEDENCE OK'
end program structure_constructor_7_5_10_b_generic_precedence
"""
    raise ValueError(variant)


def runtime_mutations(variant, source):
    if variant == "pdt_kind_parameter":
        return [mutation("pdt-kind-parameter-list", "parameter-specifier-source-use", source, [
            find_edit(source, "integer, kind :: k=kind(0.0)", "integer, kind :: k=kind(0.0d0)"),
            find_edit(source, "type(packet(kind(0.0))), intent(in) :: x", "type(packet(kind(0.0d0))), intent(in) :: x"),
            find_edit(source, "kind(x%payload) /= kind(0.0)", "kind(x%payload) /= kind(0.0)"),
            find_edit(source, "packet(k=kind(0.0))(payload=4.0)", "packet(k=kind(0.0d0))(payload=4.0d0)"),
        ])]
    if variant == "ordinary_character_defined_assignment":
        return [
            mutation("wide-character-length", "character-length-conversion", source,
                     find_edit(source, "character(len=5) :: wide", "character(len=4) :: wide")),
            mutation("narrow-character-length", "character-length-conversion", source,
                     find_edit(source, "character(len=2) :: narrow", "character(len=3) :: narrow")),
            mutation("defined-assignment-callback", "no-defined-assignment-during-construction", source,
                     find_edit(source, "call observe_outer(outer(src))",
                               "call assign_inner(scratch%item, src)\ncall observe_outer(outer(src))")),
        ]
    if variant == "private_omissions":
        return [
            mutation("private-default-value", "omitted-private-default", source,
                     find_edit(source, "integer, private :: hidden = 17", "integer, private :: hidden = 18")),
            mutation("private-allocatable-explicit-source", "omitted-private-allocatable", source, [
                find_edit(source, "integer, allocatable, private :: store(:)",
                          "integer, allocatable, public :: store(:)"),
                find_edit(source, "alloc_box(tag=31)", "alloc_box(tag=31, store=[1,2,3])"),
            ]),
        ]
    if variant == "pointer_default_private_omission":
        return [
            mutation("explicit-pointer-target", "pointer-default-source-use", source,
                     find_edit(source, "record(tag=29)", "record(tag=29, p=default_target)")),
            mutation("private-default-value", "private-omission-source-use", source,
                     find_edit(source, "integer, private :: hidden = 17", "integer, private :: hidden = 18")),
        ]
    if variant == "procedure_pointer_target":
        return [mutation("alternate-procedure-target", "procedure-target-call", source,
                         find_edit(source, "holder(worker)", "holder(other_worker)"))]
    if variant == "allocatable_same_rank_sources":
        return [
            mutation("allocatable-source-bounds", "same-rank-allocatable-source-use", source, [
                find_edit(source, "allocate(source(-2:0))", "allocate(source(-1:1))"),
                find_edit(source, "source(-2)=11\nsource(-1)=13\nsource(0)=17",
                          "source(-1)=11\nsource(0)=13\nsource(1)=17"),
            ]),
            mutation("ordinary-source-value", "same-rank-other-source-use", source,
                     find_edit(source, "ordinary(-1)=23", "ordinary(-1)=24")),
        ]
    if variant == "allocatable_source_matrix":
        return [
            mutation("allocated-source-value", "allocated-source-bounds-values", source,
                     find_edit(source, "source(-1)=13", "source(-1)=14")),
            mutation("ordinary-array-source-value", "nonallocatable-whole-array-source", source,
                     find_edit(source, "ordinary(-1)=23", "ordinary(-1)=24")),
            mutation("scalar-source-value", "ordinary-scalar-conversion", source,
                     find_edit(source, "scalar_source = 4.0", "scalar_source = 5.0")),
        ]
    if variant == "generic_precedence":
        return [
            mutation("generic-function-result", "resolvable-function-precedence", source,
                     find_edit(source, "out%payload = n + 18", "out%payload = n + 19")),
            mutation("keyword-constructor-payload", "keyword-constructor-fallback", source,
                     find_edit(source, "record(payload=11)", "record(payload=12)")),
            mutation("type-constructor-fallback-payload", "type-constructor-fallback", source,
                     find_edit(source, "token(21)", "token(22)")),
        ]
    raise ValueError(variant)


def compile_sources():
    bad = source_header("C7106", ["binding-is-not-component"]) + """module sc_b_binding_mod
implicit none
type :: gadget
  integer :: payload
contains
  procedure :: get
end type gadget
contains
integer function get(self)
  class(gadget), intent(in) :: self
  get = self%payload
end function get
end module sc_b_binding_mod
program structure_constructor_7_5_10_b_binding_keyword
use sc_b_binding_mod
implicit none
type(gadget) :: value
value = gadget(payload=11, get=19)
end program structure_constructor_7_5_10_b_binding_keyword
"""
    good = bad.replace(", get=19", "")
    return bad, good


def apply_edits(raw, edits):
    result = raw
    for edit in sorted(edits, key=lambda e: e["span"][0], reverse=True):
        start, end = edit["span"]
        if result[start:end].decode("ascii") != edit["expected"]:
            raise ValueError("mutation edit does not bind complete parent")
        result = result[:start] + edit["replacement"].encode("ascii") + result[end:]
    return result


def mutated_source(spec, mut):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent input changed")
    return apply_edits(raw, mut["edits"])


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for variant in RUNTIME_CASES:
        spec0 = RUNTIME_CASES[variant]
        source = runtime_source(variant)
        raw = source.encode("ascii")
        if max(map(len, source.splitlines())) > 132:
            raise ValueError(f"{variant}: source line too long")
        muts = runtime_mutations(variant, source)
        seen = set()
        for mut in muts:
            mraw = mutated_source({"source": source, "source_sha256": sha(raw)}, mut)
            digest = sha(mraw)
            if digest in seen:
                raise ValueError(f"{variant}: duplicate mutation")
            seen.add(digest)
        case_id = runtime_id(variant)
        directory = root / "tests/fixtures" / (TOPIC + "_" + variant)
        manifest = {
            "schema_version": 1, "id": case_id, "rule": spec0["rule"], "facets": spec0["facets"],
            "evidence": "effect", "standard": "f2023", "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free",
                       "output": "source.o"}],
            "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0,
                       "stdout": spec0["completion"], "stderr": ""},
        }
        spec = dict(spec0, id=case_id, variant=variant, source=source, source_sha256=sha(raw), mutations=muts,
                    path=(directory / "fixture.json").relative_to(root).as_posix(), manifest=manifest)
        specs[case_id] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    bad, good = compile_sources()
    for invalid, source in [(True, bad), (False, good)]:
        case_id = compile_id("binding_keyword", invalid)
        directory = root / "tests/fixtures" / (TOPIC + "_" + ("binding_keyword" if invalid else "binding_keyword_repair"))
        line = source.splitlines().index("value = gadget(payload=11, get=19)" if invalid else
                                         "value = gadget(payload=11)") + 1
        expect = {"phase": "compile", "step": "source", "outcome": "diagnose" if invalid else "success"}
        if invalid:
            expect["diagnostic"] = {"file": "source.f90", "line": line, "excludes_any": EXCLUDED}
        manifest = {"schema_version": 1, "id": case_id, "rule": "C7106", "facets": ["binding-is-not-component"],
                    "evidence": "effect" if invalid else "positive-control", "standard": "f2023",
                    "files": ["source.f90"],
                    "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free",
                               "output": "source.o", "depends_on": []}],
                    "expect": expect}
        spec = dict(COMPILE_CASES["binding_keyword"], id=case_id, variant="binding_keyword", source=source,
                    source_sha256=sha(source.encode("ascii")), invalid=invalid, mutations=[], manifest=manifest,
                    path=(directory / "fixture.json").relative_to(root).as_posix())
        specs[case_id] = spec
        files[directory / "source.f90"] = source.encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(str(compiler)).name.lower() else "gfortran"


def compile_and_run(workdir, compiler, std, source_bytes, expect_stdout):
    (workdir / "source.f90").write_bytes(source_bytes)
    exe = workdir / "program"
    flag = ("--std=" if compiler_family(compiler) == "lfortran" else "-std=") + std
    comp = subprocess.run([str(compiler), flag, "source.f90", "-o", "program"], cwd=workdir,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if comp.returncode != 0:
        return "compile-fail", comp.returncode, comp.stdout, comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if run.returncode == 0 and run.stdout == expect_stdout and run.stderr == "":
        return "pass", run.returncode, run.stdout, run.stderr
    return "run-fail", run.returncode, run.stdout, run.stderr


def check_mutations(root, compiler, std, inject_survivor=False):
    root = Path(root)
    _, specs = build_corpus(root)
    workspace = root / ("." + TOPIC + "_mutation_runs") / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    failures, checked, parents = [], 0, 0
    try:
        for spec in specs.values():
            if not spec.get("mutations"):
                continue
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, rc, stdout, stderr = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"),
                                                         spec["completion"])
            if status != "pass":
                failures.append(f"{spec['id']} parent failed {status} rc={rc}\nstdout={stdout}\nstderr={stderr}")
                continue
            parents += 1
            for mut in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mut["id"])
                case_dir.mkdir()
                msource = spec["source"].encode("ascii") if inject_survivor and checked == 1 else mutated_source(spec, mut)
                status, rc, stdout, stderr = compile_and_run(case_dir, compiler, std, msource, spec["completion"])
                if status == "compile-fail" or status == "pass":
                    failures.append(f"{spec['id']}:{mut['id']} bad mutant status={status} rc={rc}\nstdout={stdout}\nstderr={stderr}")
        if failures:
            raise SystemExit("\n\n".join(failures[:20]))
        return parents, checked
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    import generate_constructor_declaration_fixtures as declaration_generated
    import generate_structure_constructor_effect_fixtures as runtime_generated
    represented_by_rule = {}
    for family in (runtime_generated,):
        for rule, facets in family.FACETS_BY_RULE.items():
            represented_by_rule.setdefault(rule, set()).update(facets)
    for rule, facets in declaration_generated.ELIGIBLE.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
    for rule, facets in declaration_generated.EXISTING.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
    for rule, facets in FACETS_BY_RULE.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError(f"selected facets for {rule} changed")
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule],
                                                     LIMITATIONS[rule])
    for owner in updated["requirements"]:
        expected = set(owner["facets"]) - represented_by_rule.get(owner["id"], set())
        if set(owner.get("pending", {})) != expected:
            raise ValueError("structure-constructor 7.5.10 b pending partition mismatch: " + owner["id"])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = re.sub(r"\*\*Catalogue source review: [^.]+\.\*\*",
                    f"**Catalogue source review: {catalogue_review_status(catalogue)}.**", before, count=1)
    represented = sum(len(r["facets"]) - len(r.get("pending", {})) for r in catalogue["requirements"])
    pending = sum(len(r.get("pending", {})) for r in catalogue["requirements"])
    before = re.sub(r"\*\*\d+ of98 facets are represented; \d+ remain pending\*\*",
                    f"**{represented} of98 facets are represented; {pending} remain pending**", before, count=1)
    summary = (SUMMARY_BEGIN + "\n"
        "## Structure constructor batch317 observations\n\n"
        "Eight run/effect programs and one diagnostic/control pair discharge additional 7.5.10 facets for "
        "PDT KIND parameters, character conversion, omitted private/defaulted components, procedure-pointer "
        "targets, allocatable same-rank sources, allocatable source state/value rules, same-named generic "
        "precedence and a binding-name keyword negative. Runtime fixtures include feature-level mutations for "
        "every claimed facet, checked in compiler-specific scratch subdirectories.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    marker, repro = "## Complete finite pending plans\n", "## Reproduction and separate gates"
    if marker in after and repro in after:
        prefix, rest_after = after.split(marker, 1)
        _, suffix = rest_after.split(repro, 1)
        appendix = (marker + "\nThe following original plan text is retained verbatim as plan metadata. "
                    "Authorship or a prerequisite observation does not implement a graph or policy.\n\n")
        for requirement in catalogue["requirements"]:
            if requirement.get("pending"):
                appendix += f"### Pending {requirement['id']}\n\n"
                for facet, plan in requirement["pending"].items():
                    appendix += f"* **`{facet}`** - {plan}\n"
                appendix += "\n"
        after = prefix + appendix + repro + suffix
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
            raise ValueError("stale structure-constructor 7.5.10 b corpus: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return files, specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogue, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogue and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        parents, checked = check_mutations(args.root, args.compiler, args.std, args.inject_surviving_mutant)
        print(f"Mutation-checked {checked} structure_constructor_7_5_10_b mutants across {parents} parents.")
        return
    _, specs = generate(args.root, args.check, args.sync_catalogue)
    runtime = sum(1 for s in specs.values() if s.get("mutations"))
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} structure-constructor 7.5.10 b cases "
          f"({runtime} runtime parents), {sum(len(s['facets']) for s in specs.values())} manifest facet entries, "
          f"{sum(len(s.get('mutations', [])) for s in specs.values())} feature mutations.")


if __name__ == "__main__":
    main()
