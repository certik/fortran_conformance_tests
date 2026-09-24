#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 pointer association status rules in 19.5.2."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "pointer_association_19_5_2"
PREFIX = TOPIC + "_"

CATALOGUES = {
    "19.5.2.1": "doc/catalogues/pointer_association_general_19_5_2_1.json",
    "19.5.2.2": "doc/catalogues/pointer_association_status_19_5_2_2.json",
    "19.5.2.3": "doc/catalogues/pointer_becomes_associated_19_5_2_3.json",
    "19.5.2.4": "doc/catalogues/pointer_becomes_disassociated_19_5_2_4.json",
    "19.5.2.5": "doc/catalogues/pointer_association_status_undefined_19_5_2_5.json",
    "19.5.2.6": "doc/catalogues/other_pointer_association_status_events_19_5_2_6.json",
    "19.5.2.7": "doc/catalogues/pointer_definition_status_19_5_2_7.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}
SUMMARY_BEGIN = "<!-- BEGIN POINTER ASSOCIATION 19.5.2 FIXTURES -->"
SUMMARY_END = "<!-- END POINTER ASSOCIATION 19.5.2 FIXTURES -->"

FACETS_BY_RULE = {
    "S19.5.2.1-001": (
        "pointer-reference-reads-target",
        "pointer-reference-defines-target",
    ),
    "S19.5.2.1-002": (
        "associated-status-over-time",
        "disassociated-status-over-time",
        "different-own-image-targets",
    ),
    "S19.5.2.1-003": (
        "associated-pointer-definition-status-is-target",
        "deferred-shape-from-target",
        "deferred-type-parameters-from-target",
        "polymorphic-pointer-dynamic-type-from-target",
    ),
    "S19.5.2.2-001": (
        "association-status-changes",
        "initialized-disassociated-status",
        "initialized-associated-status",
    ),
    "S19.5.2.3-001": (
        "allocate-pointer-associated",
        "pointer-assignment-associated-target",
        "pointer-assignment-target-attribute",
        "pointer-assignment-allocated-allocatable-target",
        "source-allocate-associated-pointer-subobject",
        "dummy-pointer-nonpointer-actual-associated",
        "default-initialized-component-intent-out-associated",
        "default-initialized-component-unsaved-local-associated",
        "default-initialized-component-block-local-associated",
        "default-initialized-component-allocated-associated",
    ),
    "S19.5.2.4-001": (
        "nullify-pointer-disassociated",
        "deallocate-pointer-disassociated",
        "pointer-assignment-disassociated-pointer",
        "source-allocate-disassociated-pointer-subobject",
        "default-null-component-intent-out-disassociated",
        "default-null-component-unsaved-local-disassociated",
        "default-null-component-block-local-disassociated",
        "default-null-component-allocated-disassociated",
    ),
    "S19.5.2.6-001": ("name-associated-pointer-status-propagates",),
    "S19.5.2.7-001": (
        "associated-data-pointer-defined-target-value",
        "pointer-definition-through-definable-target",
    ),
}

EXPECTED_REMAINING = {
    "S19.5.2.1-001": set(),
    "S19.5.2.1-002": {"undefined-status-no-oracle"},
    "S19.5.2.1-003": set(),
    "S19.5.2.2-001": {
        "association-status-three-states",
        "uninitialized-pointer-status-undefined-no-oracle",
    },
    "S19.5.2.3-001": set(),
    "S19.5.2.4-001": set(),
    "S19.5.2.5-001": {
        "undefined-from-undefined-pointer-assignment",
        "undefined-from-different-image-target",
        "undefined-from-target-deallocated-not-through-pointer",
        "undefined-from-companion-object-lifetime-end",
        "undefined-from-move-alloc-without-target-to",
        "undefined-from-subprogram-target-undefined",
        "undefined-from-block-target-undefined",
        "undefined-from-host-instance-completed",
        "undefined-from-unsaved-local-pointer-on-return",
        "undefined-from-dummy-target-nontarget-or-vector",
        "undefined-from-dummy-target-value",
        "undefined-from-unsaved-block-pointer",
        "undefined-from-do-concurrent-multiple-status-changes",
        "undefined-from-do-concurrent-local-target",
        "undefined-from-allocated-nondefault-uninitialized-component",
        "undefined-from-source-undefined-component",
        "undefined-from-intent-out-nondefault-component",
        "undefined-from-pointer-dummy-intent-out",
        "undefined-from-unevaluated-function-side-effect",
    },
    "S19.5.2.6-001": {
        "storage-associated-pointer-status-propagates",
        "inheritance-associated-pointer-status-propagates",
    },
    "S19.5.2.6-002": {"volatile-pointer-status-external-change-latitude"},
    "S19.5.2.7-001": set(),
    "S19.5.2.7-002": {"not-associated-pointer-definition-status-undefined-no-oracle"},
}

ORACLE_PREFIXES = {rule: f"{rule} pointer-association runtime fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} pointer-association fixture boundaries: " for rule in FACETS_BY_RULE}

ORACLES = {
    "S19.5.2.1-001": ORACLE_PREFIXES["S19.5.2.1-001"] + (
        "one run/effect/f2023 program pointer-assigns one pointer to target read_target=42 and reads through "
        "the pointer into a distinguished sentinel, then pointer-assigns another pointer to write_target=1, "
        "assigns through the pointer, and reads write_target=77 directly. Feature mutants redirect each "
        "pointer assignment to a different target so the read and write assertions fail."
    ),
    "S19.5.2.1-002": ORACLE_PREFIXES["S19.5.2.1-002"] + (
        "one run/effect/f2023 program initializes a pointer disassociated, then pointer-assigns it to target "
        "a=11, target b=22 on the same image, and NULLIFYs it. It observes ASSOCIATED and exact values only "
        "while the status is defined. Feature mutants redirect the first assignment, keep the first target for "
        "the second assignment, or replace NULLIFY by an association event. Undefined status remains pending."
    ),
    "S19.5.2.1-003": ORACLE_PREFIXES["S19.5.2.1-003"] + (
        "one program associates defined scalar, rank-one, deferred-length character, and polymorphic pointers "
        "with defined targets. It reads the scalar value, inquires LBOUND/UBOUND and element value directly "
        "through the pointer, checks LEN and padded character equality, and SELECT TYPEs a child dynamic type. "
        "Feature mutants redirect each pointer assignment to a different conforming target."
    ),
    "S19.5.2.2-001": ORACLE_PREFIXES["S19.5.2.2-001"] + (
        "one program checks explicit NULL() initialization yields ASSOCIATED false, non-NULL pointer "
        "initialization yields ASSOCIATED true with the initialized target, and a runtime pointer changes "
        "from associated to disassociated to associated with another target. Feature mutants replace NULL() "
        "initialization, redirect non-NULL initialization, or remove the NULLIFY event."
    ),
    "S19.5.2.3-001": ORACLE_PREFIXES["S19.5.2.3-001"] + (
        "four programs cover all listed associated-status events. They observe ALLOCATE(pointer), pointer "
        "assignment to an associated pointer, to a TARGET object, and to an allocated allocatable TARGET; "
        "SOURCE= allocation of an object with an associated pointer subobject; pointer dummy argument "
        "association with a nonpointer TARGET actual; and four default-initialized non-NULL pointer component "
        "events (INTENT(OUT), unsaved local, BLOCK local, and allocation without SOURCE=). Feature mutants "
        "nullify, redirect targets, use a different actual, or replace each non-NULL default initializer by "
        "NULL()."
    ),
    "S19.5.2.4-001": ORACLE_PREFIXES["S19.5.2.4-001"] + (
        "two programs cover all listed disassociated-status events. One establishes associated states before "
        "NULLIFY, DEALLOCATE, and pointer assignment to a disassociated pointer, then observes ASSOCIATED false. "
        "The other observes SOURCE= allocation from a disassociated pointer subobject and NULL default pointer "
        "component effects for INTENT(OUT), unsaved local, BLOCK local, and allocation without SOURCE=. Feature "
        "mutants replace the disassociating event by a conforming association-preserving event."
    ),
    "S19.5.2.6-001": ORACLE_PREFIXES["S19.5.2.6-001"] + (
        "one program passes a pointer actual to a pointer dummy, changes the dummy's association status by "
        "pointer assignment, and observes the actual pointer is associated with the same target after return. "
        "The feature mutant NULLIFYs the dummy instead."
    ),
    "S19.5.2.7-001": ORACLE_PREFIXES["S19.5.2.7-001"] + (
        "one program associates a data pointer with a defined target and reads the exact target value through "
        "the pointer, then associates a second pointer with a definable target, defines through the pointer, "
        "and reads the target directly. Feature mutants redirect each pointer assignment to another target."
    ),
}

LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "only single-image defined association statuses, exact integer values, character length/equality, "
        "bounds inquiries, and SELECT TYPE reachability are asserted. Undefined pointer association status and "
        "undefined definition status are not inspected, passed to ASSOCIATED, dereferenced, compared, or used as "
        "diagnostic oracles. Coarray/different-image, companion-processor lifetime, VOLATILE interference, "
        "storage/inheritance-association owners, addresses, finalization, and processor-dependent diagnostics "
        "remain outside this packet."
    ) for rule in FACETS_BY_RULE
}

PENDING_REASONS = {
    "association-status-three-states": (
        "PENDING after batch286: this facet includes undefined association status, which has no portable "
        "positive runtime oracle; associated and disassociated changes are covered by separate facets."
    ),
    "uninitialized-pointer-status-undefined-no-oracle": (
        "PENDING after batch286: ASSOCIATED or dereference of an uninitialized pointer would be nonconforming; "
        "fixtures initialize status before inquiry."
    ),
    "undefined-status-no-oracle": (
        "PENDING after batch286: undefined pointer association status is source-recorded only and is never "
        "portably observable by ASSOCIATED or dereference."
    ),
}


@dataclass(frozen=True)
class Case:
    variant: str
    rule: str
    facets: tuple[str, ...]
    source: str
    mutations: tuple[dict, ...]
    lfortran_parent_failure: str = ""

    @property
    def id(self):
        return self.rule.replace(".", "_").replace("-", "_") + "_valid__" + TOPIC + "_" + self.variant

    @property
    def completion(self):
        return "POINTER ASSOCIATION 19.5.2 " + self.variant.upper().replace("_", " ") + " OK\n"


HELPERS = """contains
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'PA1952-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (observed) then
      write(*,'(a,1x,a)') 'PA1952-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'PA1952-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
"""


def header(rule, facets):
    return (
        f"! rule: {rule}\n"
        f"! covers: {' '.join(facets)}\n"
        "! evidence: effect\n"
        "! standard: f2023\n"
        "! oracle-basis: standard\n"
    )


def finish(name, completion, total):
    return (
        f"  call expect_equal(checks, {total}, 'check count before completion')\n"
        f"  write(*,'(a)') '{completion.rstrip()}'\n"
        + HELPERS
        + f"end program {name}\n"
    )


def mut(mid, facet, replacements):
    return {"id": mid, "facet": facet, "kind": "feature", "replacements": replacements}


def make_cases():
    cases = []

    def add(variant, rule, facets, body, mutations, prefix="", lfortran_parent_failure=""):
        source = header(rule, facets) + prefix + body
        cases.append(Case(variant, rule, tuple(facets), source, tuple(mutations), lfortran_parent_failure))

    add(
        "reference_general",
        "S19.5.2.1-001",
        FACETS_BY_RULE["S19.5.2.1-001"],
        f"""program pa1952_reference_general
  implicit none
  integer, target :: read_target = 42, wrong_read_target = 64
  integer, target :: write_target = 1, wrong_write_target = 5
  integer, pointer :: reader, writer
  integer :: observed, checks
  checks = 0
  observed = -777
  reader => read_target
  observed = reader
  call expect_equal(observed, 42, 'pointer reference reads target')
  writer => write_target
  writer = 77
  call expect_equal(write_target, 77, 'pointer reference defines target')
""" + finish("pa1952_reference_general", "POINTER ASSOCIATION 19.5.2 REFERENCE GENERAL OK\n", 2),
        [
            mut("read-pointer-wrong-target", "pointer-reference-reads-target",
                [("reader => read_target", "reader => wrong_read_target")]),
            mut("write-pointer-wrong-target", "pointer-reference-defines-target",
                [("writer => write_target", "writer => wrong_write_target")]),
        ],
    )

    add(
        "status_over_time",
        "S19.5.2.1-002",
        FACETS_BY_RULE["S19.5.2.1-002"],
        f"""program pa1952_status_over_time
  implicit none
  integer, target :: first_target = 11, second_target = 22, wrong_target = 33
  integer, pointer :: p
  integer :: checks
  checks = 0
  nullify(p)
  p => first_target
  call expect_true(associated(p, first_target), 'associated with first target')
  call expect_equal(p, 11, 'first target value')
  p => second_target
  call expect_true(associated(p, second_target), 'associated with second own-image target')
  call expect_equal(p, 22, 'second own-image target value')
  nullify(p)
  call expect_false(associated(p), 'disassociated after nullify')
""" + finish("pa1952_status_over_time", "POINTER ASSOCIATION 19.5.2 STATUS OVER TIME OK\n", 5),
        [
            mut("first-assignment-wrong-target", "associated-status-over-time",
                [("p => first_target", "p => wrong_target")]),
            mut("second-assignment-keeps-first", "different-own-image-targets",
                [("p => second_target", "p => first_target")]),
            mut("nullify-replaced-by-association", "disassociated-status-over-time",
                [("nullify(p)\n  call expect_false", "p => second_target\n  call expect_false")]),
        ],
    )

    add(
        "target_characteristics",
        "S19.5.2.1-003",
        FACETS_BY_RULE["S19.5.2.1-003"],
        f"""program pa1952_target_characteristics
  implicit none
  type :: base
    integer :: tag
  end type
  type, extends(base) :: child
    integer :: payload
  end type
  integer, target :: scalar_target = 51, scalar_wrong = 62
  integer, target :: array_target(2:4) = [71, 72, 73]
  integer, target :: other_array(1:3) = [81, 82, 83]
  character(len=5), target :: text_target = 'abcde'
  character(len=3), target :: short_text = 'xyz'
  type(child), target :: child_target
  type(base), target :: base_target
  integer, pointer :: p_scalar
  integer, pointer :: p_array(:)
  character(len=:), pointer :: p_text
  class(base), pointer :: p_poly
  integer :: checks
  checks = 0
  child_target%tag = 9
  child_target%payload = 88
  base_target%tag = 6
  p_scalar => scalar_target
  call expect_equal(p_scalar, 51, 'defined target value through data pointer')
  p_array => array_target
  call expect_equal(lbound(p_array, 1), 2, 'deferred shape lower bound')
  call expect_equal(ubound(p_array, 1), 4, 'deferred shape upper bound')
  call expect_equal(p_array(3), 72, 'deferred shape element value')
  p_text => text_target
  call expect_equal(len(p_text), 5, 'deferred character length')
  if (len(p_text) /= 5 .or. p_text /= 'abcde') error stop 'PA1952-FAIL deferred character value'
  checks = checks + 1
  p_poly => child_target
  select type (p_poly)
  type is (child)
    call expect_equal(p_poly%payload, 88, 'polymorphic dynamic type child payload')
  class default
    error stop 'PA1952-FAIL polymorphic dynamic type branch'
  end select
""" + finish("pa1952_target_characteristics", "POINTER ASSOCIATION 19.5.2 TARGET CHARACTERISTICS OK\n", 7),
        [
            mut("defined-target-wrong-scalar", "associated-pointer-definition-status-is-target",
                [("p_scalar => scalar_target", "p_scalar => scalar_wrong")]),
            mut("array-pointer-section", "deferred-shape-from-target",
                [("p_array => array_target", "p_array => array_target(2:4)")]),
            mut("character-wrong-length-target", "deferred-type-parameters-from-target",
                [("p_text => text_target", "p_text => short_text")]),
            mut("polymorphic-base-target", "polymorphic-pointer-dynamic-type-from-target",
                [("p_poly => child_target", "p_poly => base_target")]),
        ],
    )

    add(
        "initialization_status",
        "S19.5.2.2-001",
        FACETS_BY_RULE["S19.5.2.2-001"],
        f"""program pa1952_initialization_status
  implicit none
  integer, target, save :: associated_target = 31, other_target = 47
  integer, pointer :: dis => null()
  integer, pointer :: assoc => associated_target
  integer, pointer :: changing
  integer :: checks
  checks = 0
  call expect_false(associated(dis), 'explicit null initialization disassociated')
  call expect_true(associated(assoc, associated_target), 'explicit target initialization associated')
  changing => associated_target
  call expect_true(associated(changing, associated_target), 'changing pointer first association')
  nullify(changing)
  call expect_false(associated(changing), 'changing pointer after nullify')
  changing => other_target
  call expect_true(associated(changing, other_target), 'changing pointer second association')
""" + finish("pa1952_initialization_status", "POINTER ASSOCIATION 19.5.2 INITIALIZATION STATUS OK\n", 5),
        [
            mut("null-initializer-to-target", "initialized-disassociated-status",
                [("dis => null()", "dis => associated_target")]),
            mut("associated-initializer-wrong-target", "initialized-associated-status",
                [("assoc => associated_target", "assoc => other_target")]),
            mut("status-change-nullify-removed", "association-status-changes",
                [("nullify(changing)", "changing => other_target")]),
        ],
        lfortran_parent_failure="frozen LFortran rejects non-NULL pointer initialization as non-constant",
    )

    add(
        "definition_status",
        "S19.5.2.7-001",
        FACETS_BY_RULE["S19.5.2.7-001"],
        f"""program pa1952_definition_status
  implicit none
  integer, target :: defined_target = 123, wrong_defined = 456
  integer, target :: definable_target = 5, wrong_definable = 7
  integer, pointer :: reader, writer
  integer :: observed, checks
  checks = 0
  observed = -909
  reader => defined_target
  observed = reader
  call expect_equal(observed, 123, 'associated pointer has target definition status')
  writer => definable_target
  writer = 789
  call expect_equal(definable_target, 789, 'definition through pointer defines target')
""" + finish("pa1952_definition_status", "POINTER ASSOCIATION 19.5.2 DEFINITION STATUS OK\n", 2),
        [
            mut("defined-status-wrong-target", "associated-data-pointer-defined-target-value",
                [("reader => defined_target", "reader => wrong_defined")]),
            mut("definable-target-wrong-target", "pointer-definition-through-definable-target",
                [("writer => definable_target", "writer => wrong_definable")]),
        ],
    )

    add(
        "associated_allocate_assignment",
        "S19.5.2.3-001",
        (
            "allocate-pointer-associated",
            "pointer-assignment-associated-target",
            "pointer-assignment-target-attribute",
            "pointer-assignment-allocated-allocatable-target",
        ),
        f"""program pa1952_associated_allocate_assignment
  implicit none
  integer, target :: source_target = 211, direct_target = 223, wrong_target = 227
  integer, allocatable, target :: alloc_target
  integer, pointer :: p_alloc, p_from_pointer, source_pointer, p_direct, p_allocatable
  integer :: checks
  checks = 0
  nullify(p_alloc)
  allocate(p_alloc)
  call expect_true(associated(p_alloc), 'allocated pointer becomes associated')
  source_pointer => source_target
  nullify(p_from_pointer)
  p_from_pointer => source_pointer
  call expect_true(associated(p_from_pointer, source_target), 'pointer assignment to associated pointer')
  call expect_equal(p_from_pointer, 211, 'associated pointer assignment value')
  nullify(p_direct)
  p_direct => direct_target
  call expect_true(associated(p_direct, direct_target), 'pointer assignment to TARGET object')
  allocate(alloc_target)
  alloc_target = 239
  nullify(p_allocatable)
  p_allocatable => alloc_target
  call expect_true(associated(p_allocatable), 'pointer assignment to allocated allocatable target')
  call expect_equal(p_allocatable, 239, 'allocated allocatable target value')
""" + finish("pa1952_associated_allocate_assignment", "POINTER ASSOCIATION 19.5.2 ASSOCIATED ALLOCATE ASSIGNMENT OK\n", 6),
        [
            mut("allocate-replaced-by-nullify", "allocate-pointer-associated",
                [("allocate(p_alloc)", "nullify(p_alloc)")]),
            mut("associated-pointer-wrong-target", "pointer-assignment-associated-target",
                [("p_from_pointer => source_pointer", "p_from_pointer => wrong_target")]),
            mut("target-attribute-wrong-target", "pointer-assignment-target-attribute",
                [("p_direct => direct_target", "p_direct => wrong_target")]),
            mut("allocatable-target-wrong-target", "pointer-assignment-allocated-allocatable-target",
                [("p_allocatable => alloc_target", "p_allocatable => wrong_target")]),
        ],
    )

    add(
        "associated_source_dummy",
        "S19.5.2.3-001",
        (
            "source-allocate-associated-pointer-subobject",
            "dummy-pointer-nonpointer-actual-associated",
        ),
        f"""program pa1952_associated_source_dummy
  implicit none
  type :: box
    integer, pointer :: p
  end type
  integer, target :: source_target = 307, dummy_target = 311, other_target = 313
  type(box) :: src
  type(box), allocatable :: dst
  integer :: checks
  checks = 0
  src%p => source_target
  allocate(dst, source=src)
  call expect_true(associated(dst%p, source_target), 'SOURCE associated pointer subobject')
  call expect_equal(dst%p, 307, 'SOURCE associated subobject value')
  call check_dummy(dummy_target)
""" + finish("pa1952_associated_source_dummy", "POINTER ASSOCIATION 19.5.2 ASSOCIATED SOURCE DUMMY OK\n", 4).replace(
            "contains\n", """contains
  subroutine check_dummy(dummy)
    integer, pointer, intent(in) :: dummy
    call expect_true(associated(dummy, dummy_target), 'pointer dummy associated with nonpointer actual')
    call expect_equal(dummy, 311, 'pointer dummy actual value')
  end subroutine
""", 1),
        [
            mut("source-subobject-wrong-target", "source-allocate-associated-pointer-subobject",
                [("src%p => source_target", "src%p => other_target")]),
            mut("dummy-actual-other-target", "dummy-pointer-nonpointer-actual-associated",
                [("call check_dummy(dummy_target)", "call check_dummy(other_target)")]),
        ],
    )

    default_assoc_prefix = """module pa1952_default_assoc_m
  implicit none
  integer, target, save :: default_target = 401, other_target = 409
  type :: box_intent
    integer, pointer :: p => default_target
  end type
  type :: box_local
    integer, pointer :: p => default_target
  end type
  type :: box_block
    integer, pointer :: p => default_target
  end type
  type :: box_alloc
    integer, pointer :: p => default_target
  end type
contains
  subroutine intent_out_event(box)
    type(box_intent), intent(out) :: box
  end subroutine
  subroutine local_event(ok, value)
    logical, intent(out) :: ok
    integer, intent(out) :: value
    type(box_local) :: local
    ok = associated(local%p, default_target)
    value = local%p
  end subroutine
  subroutine block_event(ok, value)
    logical, intent(out) :: ok
    integer, intent(out) :: value
    block
      type(box_block) :: local
      ok = associated(local%p, default_target)
      value = local%p
    end block
  end subroutine
end module pa1952_default_assoc_m
"""
    add(
        "associated_default_components",
        "S19.5.2.3-001",
        (
            "default-initialized-component-intent-out-associated",
            "default-initialized-component-unsaved-local-associated",
            "default-initialized-component-block-local-associated",
            "default-initialized-component-allocated-associated",
        ),
        f"""program pa1952_associated_default_components
  use pa1952_default_assoc_m
  implicit none
  type(box_intent) :: intent_box
  type(box_alloc), allocatable :: allocated_box
  logical :: ok
  integer :: value, checks
  checks = 0
  intent_box%p => other_target
  call intent_out_event(intent_box)
  call expect_true(associated(intent_box%p, default_target), 'INTENT(OUT) non-NULL default component')
  call expect_equal(intent_box%p, 401, 'INTENT(OUT) non-NULL default value')
  call local_event(ok, value)
  call expect_true(ok, 'unsaved local non-NULL default component')
  call expect_equal(value, 401, 'unsaved local non-NULL default value')
  call block_event(ok, value)
  call expect_true(ok, 'BLOCK local non-NULL default component')
  call expect_equal(value, 401, 'BLOCK local non-NULL default value')
  allocate(box_alloc :: allocated_box)
  call expect_true(associated(allocated_box%p, default_target), 'allocated non-NULL default component')
  call expect_equal(allocated_box%p, 401, 'allocated non-NULL default value')
""" + finish("pa1952_associated_default_components", "POINTER ASSOCIATION 19.5.2 ASSOCIATED DEFAULT COMPONENTS OK\n", 8),
        [
            mut("intent-default-to-null", "default-initialized-component-intent-out-associated",
                [("type :: box_intent\n    integer, pointer :: p => default_target",
                  "type :: box_intent\n    integer, pointer :: p => null()")]),
            mut("local-default-to-null", "default-initialized-component-unsaved-local-associated",
                [("type :: box_local\n    integer, pointer :: p => default_target",
                  "type :: box_local\n    integer, pointer :: p => null()")]),
            mut("block-default-to-null", "default-initialized-component-block-local-associated",
                [("type :: box_block\n    integer, pointer :: p => default_target",
                  "type :: box_block\n    integer, pointer :: p => null()")]),
            mut("allocated-default-to-null", "default-initialized-component-allocated-associated",
                [("type :: box_alloc\n    integer, pointer :: p => default_target",
                  "type :: box_alloc\n    integer, pointer :: p => null()")]),
        ],
        prefix=default_assoc_prefix,
        lfortran_parent_failure="frozen LFortran rejects non-NULL default pointer component initialization",
    )

    add(
        "disassociated_direct",
        "S19.5.2.4-001",
        (
            "nullify-pointer-disassociated",
            "deallocate-pointer-disassociated",
            "pointer-assignment-disassociated-pointer",
        ),
        f"""program pa1952_disassociated_direct
  implicit none
  integer, target :: nullify_target = 503, dealloc_replacement = 509, assignment_target = 521
  integer, pointer :: p_nullify, p_dealloc, p_assignment, q_null
  integer :: checks
  checks = 0
  p_nullify => nullify_target
  call expect_true(associated(p_nullify), 'nullify precondition associated')
  nullify(p_nullify)
  call expect_false(associated(p_nullify), 'nullify makes pointer disassociated')
  allocate(p_dealloc)
  call expect_true(associated(p_dealloc), 'deallocate precondition associated')
  deallocate(p_dealloc)
  call expect_false(associated(p_dealloc), 'deallocate makes pointer disassociated')
  p_assignment => assignment_target
  nullify(q_null)
  p_assignment => q_null
  call expect_false(associated(p_assignment), 'assignment to disassociated pointer')
""" + finish("pa1952_disassociated_direct", "POINTER ASSOCIATION 19.5.2 DISASSOCIATED DIRECT OK\n", 5),
        [
            mut("nullify-keeps-associated", "nullify-pointer-disassociated",
                [("nullify(p_nullify)", "p_nullify => nullify_target")]),
            mut("deallocate-replaced-by-association", "deallocate-pointer-disassociated",
                [("deallocate(p_dealloc)", "p_dealloc => dealloc_replacement")]),
            mut("disassociated-assignment-keeps-target", "pointer-assignment-disassociated-pointer",
                [("p_assignment => q_null", "p_assignment => assignment_target")]),
        ],
    )

    add(
        "disassociated_source_default",
        "S19.5.2.4-001",
        (
            "source-allocate-disassociated-pointer-subobject",
            "default-null-component-intent-out-disassociated",
            "default-null-component-unsaved-local-disassociated",
            "default-null-component-block-local-disassociated",
            "default-null-component-allocated-disassociated",
        ),
        f"""program pa1952_disassociated_source_default
  implicit none
  type :: source_box
    integer, pointer :: p
  end type
  type :: box_intent
    integer, pointer :: p => null()
  end type
  type :: box_local
    integer, pointer :: p => null()
  end type
  type :: box_block
    integer, pointer :: p => null()
  end type
  type :: box_alloc
    integer, pointer :: p => null()
  end type
  integer, target :: target = 607
  type(source_box) :: src
  type(source_box), allocatable :: dst
  type(box_intent) :: intent_box
  type(box_alloc), allocatable :: allocated_box
  type(box_alloc) :: source_assoc
  integer :: checks
  checks = 0
  nullify(src%p)
  allocate(dst, source=src)
  call expect_false(associated(dst%p), 'SOURCE disassociated pointer subobject')
  intent_box%p => target
  call intent_out_event(intent_box)
  call expect_false(associated(intent_box%p), 'INTENT(OUT) NULL default component')
  call local_event()
  call local_event()
  call block_event()
  call block_event()
  source_assoc%p => target
  allocate(box_alloc :: allocated_box)
  call expect_false(associated(allocated_box%p), 'allocated NULL default component')
""" + finish("pa1952_disassociated_source_default", "POINTER ASSOCIATION 19.5.2 DISASSOCIATED SOURCE DEFAULT OK\n", 7).replace(
            "contains\n", """contains
  subroutine intent_out_event(box)
    type(box_intent), intent(out) :: box
  end subroutine
  subroutine local_event()
    type(box_local) :: local
    call expect_false(associated(local%p), 'unsaved local NULL default component')
    local%p => target
  end subroutine
  subroutine block_event()
    block
      type(box_block) :: local
      call expect_false(associated(local%p), 'BLOCK local NULL default component')
      local%p => target
    end block
  end subroutine
""", 1),
        [
            mut("source-null-subobject-associated", "source-allocate-disassociated-pointer-subobject",
                [("nullify(src%p)", "src%p => target")]),
            mut("intent-out-to-inout", "default-null-component-intent-out-disassociated",
                [("type(box_intent), intent(out) :: box", "type(box_intent), intent(inout) :: box")]),
            mut("local-object-saved", "default-null-component-unsaved-local-disassociated",
                [("type(box_local) :: local", "type(box_local), save :: local")]),
            mut("block-object-saved", "default-null-component-block-local-disassociated",
                [("type(box_block) :: local", "type(box_block), save :: local")]),
            mut("allocated-with-source-associated", "default-null-component-allocated-disassociated",
                [("allocate(box_alloc :: allocated_box)", "allocate(allocated_box, source=source_assoc)")]),
        ],
    )

    add(
        "name_association_propagates",
        "S19.5.2.6-001",
        FACETS_BY_RULE["S19.5.2.6-001"],
        f"""program pa1952_name_association_propagates
  implicit none
  integer, target :: target = 701
  integer, pointer :: actual
  integer :: checks
  checks = 0
  nullify(actual)
  call change_dummy(actual)
  call expect_true(associated(actual, target), 'name-associated dummy changes actual status')
  call expect_equal(actual, 701, 'name-associated actual target value')
""" + finish("pa1952_name_association_propagates", "POINTER ASSOCIATION 19.5.2 NAME ASSOCIATION PROPAGATES OK\n", 2).replace(
            "contains\n", """contains
  subroutine change_dummy(dummy)
    integer, pointer :: dummy
    dummy => target
  end subroutine
""", 1),
        [
            mut("dummy-nullified-instead", "name-associated-pointer-status-propagates",
                [("dummy => target", "nullify(dummy)")]),
        ],
    )

    return {case.id: case for case in cases}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest(case):
    return {
        "schema_version": 1,
        "id": case.id,
        "rule": case.rule,
        "facets": list(case.facets),
        "evidence": "effect",
        "standard": "f2023",
        "oracle_basis": "standard",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
        "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
        "expect": {"phase": "run", "outcome": "success", "exit_code": 0, "stdout": case.completion, "stderr": ""},
    }


def mutation_records(case):
    records = []
    for mutation in case.mutations:
        changed = case.source
        replacements = []
        for expected, replacement in mutation["replacements"]:
            count = changed.count(expected)
            if count != 1:
                raise ValueError(f"{case.variant}:{mutation['id']} expected unique text {expected!r}, saw {count}")
            start = changed.index(expected)
            replacements.append({"expected": expected, "replacement": replacement, "span": [start, start + len(expected)]})
            changed = changed[:start] + replacement + changed[start + len(expected):]
        if changed == case.source:
            raise ValueError(f"{case.variant}:{mutation['id']} did not change the source")
        item = copy.deepcopy(mutation)
        item["replacements"] = replacements
        item["mutant_sha256"] = sha(changed.encode("ascii"))
        records.append(item)
    return records


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for cid, case in make_cases().items():
        raw = case.source.encode("ascii")
        directory = root / "tests" / "fixtures" / (PREFIX + case.variant)
        spec = {
            "id": cid,
            "variant": case.variant,
            "rule": case.rule,
            "facets": list(case.facets),
            "source": case.source,
            "source_sha256": sha(raw),
            "completion": case.completion,
            "manifest": manifest(case),
            "path": directory.relative_to(root).as_posix() + "/fixture.json",
            "mutations": mutation_records(case),
            "lfortran_parent_failure": case.lfortran_parent_failure,
        }
        specs[cid] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def synced_catalogue(section, catalogue, specs):
    result = copy.deepcopy(catalogue)
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for requirement in result["requirements"]:
        rule = requirement["id"]
        pending = requirement.setdefault("pending", {})
        for facet in covered.get(rule, set()):
            pending.pop(facet, None)
        for facet in EXPECTED_REMAINING.get(rule, set()):
            if facet in PENDING_REASONS:
                pending[facet] = PENDING_REASONS[facet]
        if rule in ORACLES:
            requirement["oracle"] = owned_paragraph(
                requirement.get("oracle", ""),
                ORACLE_PREFIXES[rule],
                ORACLES[rule],
            )
            requirement["oracle_limitation"] = owned_paragraph(
                requirement.get("oracle_limitation", ""),
                LIMIT_PREFIXES[rule],
                LIMITATIONS[rule],
            )
    return result


def rendered_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    if section == "19.5.2.1":
        summary = (
            SUMMARY_BEGIN + "\n"
            "## Pointer association 19.5.2 runtime observations\n\n"
            "Batch286 adds single-image fixtures for defined pointer association/disassociation events, "
            "target reference, definition-through-pointer, deferred shape/type-parameter adoption, and dynamic "
            "type adoption. Undefined association status is intentionally left pending because ASSOCIATED or "
            "dereference of an undefined pointer is nonconforming.\n"
            + SUMMARY_END
        )
        if SUMMARY_BEGIN in before and SUMMARY_END in before:
            leading, owned = before.split(SUMMARY_BEGIN)
            _, trailing = owned.split(SUMMARY_END)
            before = leading + summary + trailing
        else:
            before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generated_catalogues_and_views(root, specs):
    root = Path(root)
    catalogues, views = {}, {}
    for section, rel in CATALOGUES.items():
        data = json.loads((root / rel).read_text())
        updated = synced_catalogue(section, data, specs)
        catalogues[rel] = updated
        views[VIEWS[section]] = rendered_view(section, updated, root)
    return catalogues, views


def generate(root=ROOT, check=False, sync_catalogues=True):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues, views = generated_catalogues_and_views(root, specs)
    stale = []
    if check:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                stale.append(path.relative_to(root).as_posix())
        for rel, data in catalogues.items():
            if json.loads((root / rel).read_text()) != data:
                stale.append(rel)
        for rel, text in views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise SystemExit("stale pointer_association_19_5_2 generated files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogues:
            for rel, data in catalogues.items():
                (root / rel).write_text(json.dumps(data, indent=2) + "\n")
            for rel, text in views.items():
                (root / rel).write_text(text)
    return files, specs


def mutate_source(spec, mutation, allow_identical=False):
    text = spec["source"]
    changed = text
    for repl in mutation["replacements"]:
        expected, replacement = repl["expected"], repl["replacement"]
        if changed.count(expected) != 1:
            raise ValueError(f"{spec['variant']}:{mutation['id']} replacement is not bound: {expected!r}")
        changed = changed.replace(expected, replacement, 1)
    if changed == text and not allow_identical:
        raise ValueError(f"{spec['variant']}:{mutation['id']} did not change the source")
    return changed


def std_flag(compiler, std):
    name = Path(compiler).name.lower()
    return "--std=" + std if "lfortran" in name else "-std=" + std


def run_command(argv, cwd, timeout=40):
    env = os.environ.copy()
    env["TMPDIR"] = str((ROOT / ".pointer_association_19_5_2_tmp").resolve())
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)


def compile_and_run(source, compiler, std, workdir):
    source_path = workdir / "source.f90"
    exe = workdir / "program"
    source_path.write_text(source)
    comp = run_command([compiler, std_flag(compiler, std), "source.f90", "-o", "program"], workdir)
    if comp.returncode != 0:
        return {"phase": "compile", "returncode": comp.returncode, "stdout": comp.stdout, "stderr": comp.stderr}
    run = run_command([str(exe)], workdir)
    return {
        "phase": "run",
        "returncode": run.returncode,
        "stdout": run.stdout,
        "stderr": run.stderr,
        "compile_stdout": comp.stdout,
        "compile_stderr": comp.stderr,
    }


def mutation_matrix(compiler, std="f2023", root=ROOT, keep=False, skip_parent_failures=False):
    root = Path(root)
    _, specs = build_corpus(root)
    scratch = root / ".pointer_association_19_5_2_mutation_work"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    results = []
    try:
        for cid, spec in specs.items():
            parent_dir = scratch / cid / "parent"
            parent_dir.mkdir(parents=True)
            parent = compile_and_run(spec["source"], compiler, std, parent_dir)
            parent_ok = (parent["phase"] == "run" and parent["returncode"] == 0
                         and parent["stdout"] == spec["completion"] and parent["stderr"] == "")
            results.append({"case": cid, "mutation": "parent", "ok": parent_ok, **parent})
            if not parent_ok:
                if skip_parent_failures:
                    continue
                continue
            for mutation in spec["mutations"]:
                mdir = scratch / cid / mutation["id"]
                mdir.mkdir(parents=True)
                observed = compile_and_run(mutate_source(spec, mutation), compiler, std, mdir)
                failed_as_required = (observed["phase"] == "run" and not (
                    observed["returncode"] == 0 and observed["stdout"] == spec["completion"] and observed["stderr"] == ""))
                results.append({"case": cid, "mutation": mutation["id"], "facet": mutation["facet"],
                                "kind": mutation["kind"], "ok": failed_as_required, **observed})
    finally:
        if not keep:
            shutil.rmtree(scratch, ignore_errors=True)
            shutil.rmtree(root / ".pointer_association_19_5_2_tmp", ignore_errors=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--skip-parent-failures", action="store_true")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        results = mutation_matrix(args.compiler, args.std, args.root, args.keep_work, args.skip_parent_failures)
        failed = [row for row in results if not row["ok"] and not (args.skip_parent_failures and row["mutation"] == "parent")]
        if failed:
            for row in failed:
                print(json.dumps({k: row.get(k) for k in ("case", "mutation", "phase", "returncode", "stdout", "stderr")}, indent=2))
            raise SystemExit(f"mutation matrix failed: {len(failed)} bad rows out of {len(results)}")
        parents = sum(1 for row in results if row["mutation"] == "parent" and row["ok"])
        mutants = sum(1 for row in results if row["mutation"] != "parent")
        skipped = sum(1 for row in results if row["mutation"] == "parent" and not row["ok"])
        print(f"mutation matrix OK: {parents} parents passed; {mutants} mutants failed; {skipped} parents skipped")
        return
    _, specs = generate(args.root, args.check)
    print(f"{'checked' if args.check else 'generated'} {len(specs)} {TOPIC} fixtures, "
          f"{sum(len(s['facets']) for s in specs.values())} facets")


if __name__ == "__main__":
    main()
