#!/usr/bin/env python3
"""Fixtures for Fortran 2023 argument correspondence and association rules in 15.5.2."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "argument_association_15_5_2_a"
PREFIX = TOPIC + "_"

CATALOGUES = {
    "15.5.2.1": "doc/catalogues/argument_correspondence_15_5_2_1.json",
    "15.5.2.2": "doc/catalogues/passed_object_dummy_argument_and_argument_correspondence_15_5_2_2.json",
    "15.5.2.3": "doc/catalogues/conditional_argument_correspondence_15_5_2_3.json",
    "15.5.2.4": "doc/catalogues/argument_association_15_5_2_4.json",
    "15.5.2.6": "doc/catalogues/allocatable_and_pointer_dummy_variables_15_5_2_6.json",
    "15.5.2.7": "doc/catalogues/allocatable_dummy_variables_15_5_2_7.json",
    "15.5.2.8": "doc/catalogues/pointer_dummy_variables_15_5_2_8.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}
SUMMARY_BEGIN = "<!-- BEGIN ARGUMENT ASSOCIATION 15.5.2A FIXTURES -->"
SUMMARY_END = "<!-- END ARGUMENT ASSOCIATION 15.5.2A FIXTURES -->"
EXCLUDES = ["not implemented", "not yet implemented", "unsupported", "internal error", "internal:", "asr", "verifier"]

RESTRICTION_RULES = {
    "S15.5.2.4-001", "S15.5.2.6-002", "S15.5.2.6-003", "S15.5.2.6-004",
    "S15.5.2.6-006", "S15.5.2.7-002", "S15.5.2.7-010",
    "S15.5.2.8-002", "S15.5.2.8-003", "C1550",
}

FACETS_BY_RULE = {
    "S15.5.2.1-001": ["keyword-correspondence", "positional-correspondence", "passed-object-reduced-list"],
    "S15.5.2.2-001": ["type-bound-data-ref-passed-object", "procedure-pointer-component-data-ref-passed-object"],
    "S15.5.2.3-001": ["first-true-consequent", "last-consequent-default"],
    "S15.5.2.3-002": ["chosen-variable-actual"],
    "S15.5.2.4-001": ["associated-pointer-actual-control", "intrinsic-inquiry-exception"],
    "S15.5.2.4-002": ["polymorphic-dummy-associated-with-pointer-target", "nonpolymorphic-dummy-associated-with-declared-type-part"],
    "S15.5.2.4-003": ["polymorphic-dummy-associated-with-nonpointer-actual", "nonpolymorphic-dummy-associated-with-nonpointer-declared-part"],
    "S15.5.2.4-004": ["value-dummy-initial-value", "value-dummy-definable-anonymous-object", "value-dummy-caller-unchanged"],
    "S15.5.2.4-005": ["pointer-dummy-associated-with-pointer-actual"],
    "S15.5.2.4-007": ["ultimate-argument-through-dummy-chain", "ultimate-argument-through-subobject-chain"],
    "S15.5.2.6-001": ["allocatable-pointer-same-attribute-scope"],
    "S15.5.2.6-002": ["allocatable-pointer-polymorphic-correspondence", "allocatable-pointer-unlimited-polymorphic-correspondence", "allocatable-pointer-declared-type-same"],
    "S15.5.2.6-003": ["allocatable-pointer-rank-match"],
    "S15.5.2.6-004": ["allocatable-pointer-type-parameter-agreement"],
    "S15.5.2.6-005": ["allocatable-pointer-assumed-type-parameter-capture"],
    "S15.5.2.6-006": ["allocatable-pointer-same-deferred-type-parameters"],
    "S15.5.2.7-001": ["allocatable-dummy-data-object-scope"],
    "S15.5.2.7-002": ["allocatable-dummy-actual-allocatable-required"],
    "S15.5.2.7-003": ["allocatable-dummy-unallocated-actual-permitted"],
    "S15.5.2.7-008": ["allocatable-target-dummy-invocation-pointer-association"],
    "S15.5.2.7-009": ["allocatable-target-dummy-completion-pointer-association"],
    "S15.5.2.7-010": ["allocatable-intent-out-inout-actual-definable"],
    "S15.5.2.7-011": ["allocatable-intent-out-actual-deallocated-on-entry"],
    "S15.5.2.8-001": ["dummy-data-pointer-scope"],
    "C1550": ["contiguous-dummy-pointer-simply-contiguous-positive", "contiguous-dummy-pointer-noncontiguous-actual-negative"],
    "S15.5.2.8-002": ["non-intent-in-dummy-pointer-actual-pointer-required"],
    "S15.5.2.8-003": ["intent-in-dummy-pointer-actual-pointer-or-target"],
    "S15.5.2.8-004": ["intent-in-dummy-pointer-associated-with-target-actual"],
}

EXPECTED_REMAINING = {
    "S15.5.2.6-003": {"assumed-rank-dummy-rank-admission"},
    "S15.5.2.1-001": {"nonoptional-exactly-one-correspondence", "optional-at-most-one-correspondence", "every-actual-has-dummy"},
    "S15.5.2.3-001": {"guard-evaluation-order"},
    "S15.5.2.3-002": {"chosen-expression-evaluated", "chosen-nil-actual-absent"},
    "S15.5.2.3-003": {"conditional-consequent-type-requirements", "conditional-consequent-kind-requirements", "conditional-consequent-attribute-requirements", "conditional-consequent-property-requirements"},
    "S15.5.2.3-004": {"conditional-type-kind-rank", "conditional-all-allocatable-or-pointer", "conditional-polymorphic-any-consequent", "conditional-corank-common-or-zero", "conditional-simple-contiguous-all"},
    "S15.5.2.4-001": {"disassociated-pointer-actual-source"},
    "S15.5.2.4-005": {"pointer-dummy-nonpointer-actual-not-argument-associated"},
    "S15.5.2.4-006": {"effective-argument-term-source-use"},
    "S15.5.2.7-004": {"allocatable-dummy-corank-match"},
    "S15.5.2.7-005": {"coindexed-allocatable-actual-intent-in-required"},
    "S15.5.2.7-006": {"allocatable-dummy-no-target-pointer-nonassociation"},
    "S15.5.2.7-007": {"allocatable-dummy-forwarded-target-association-processor-dependent"},
    "C1551": {"dummy-pointer-coindexed-actual-out-of-scope"},
    "S15.5.2.8-005": {"intent-out-dummy-pointer-actual-status-undefined"},
}

PENDING_REASONS = {
    "guard-evaluation-order": "PENDING after batch316: gfortran 16 accepts scalar conditional arguments but crashes on side-effecting guard functions needed to portably observe evaluation order; no reference-validated fixture is shipped.",
    "chosen-expression-evaluated": "PENDING after batch316: gfortran 16 segfaults when a function call consequent is used as a conditional actual argument; no reference-validated fixture is shipped.",
    "chosen-nil-actual-absent": "PENDING after batch316: gfortran 16 rejects .NIL. conditional consequent syntax, so the F2023 absence rule lacks reference validation on this host.",
    "conditional-type-kind-rank": "PENDING after batch316: gfortran 16 rejects array conditional arguments and the scalar controls here do not separately observe all type, kind, and rank characteristics.",
    "conditional-all-allocatable-or-pointer": "PENDING after batch316: gfortran 16 lacks enough conditional-argument support for allocatable or pointer consequent characteristic fixtures on this host.",
    "conditional-polymorphic-any-consequent": "PENDING after batch316: not shipped because reference validation of richer conditional consequent characteristics is unavailable on this host.",
    "conditional-simple-contiguous-all": "PENDING after batch316: gfortran 16 rejects array conditional arguments, including sections needed to observe simple contiguity.",
}

ORACLE_PREFIXES = {rule: f"{rule} argument_association_15_5_2_a fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} argument_association_15_5_2_a boundaries: " for rule in FACETS_BY_RULE}
ORACLES = {rule: ORACLE_PREFIXES[rule] + "Generated f2023 fixtures establish non-default sentinels, execute the relevant procedure reference, and assert exact integer, logical, character length/text, allocation, bounds, association, PRESENT-independent, or diagnostic-line properties required by the cited source unit. Each runtime facet has a distinct feature mutation that keeps the program conforming and changes the observed association, correspondence, or allocation effect." for rule in FACETS_BY_RULE}
ORACLES["C1550"] = ORACLE_PREFIXES["C1550"] + "A positive control passes a simply contiguous whole array to an INTEGER, POINTER, CONTIGUOUS, INTENT(IN) dummy and checks the first element. The negative changes only the actual argument to the strided section a(::2), which is not simply contiguous, and requires any compiler error anchored at that call line."
LIMITATIONS = {rule: LIMIT_PREFIXES[rule] + "Only single-image source-level argument correspondence and defined association/allocation states are asserted. Undefined pointer association status, coindexed/coarray behavior, processor-dependent forwarded TARGET association, storage addresses, descriptor identity, exact diagnostic wording, and unnumbered restrictions without required diagnostics remain pending or out of scope." for rule in FACETS_BY_RULE}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def header(rule, facets):
    return f"! rule: {rule}\n! covers: {' '.join(facets)}\n! evidence: effect\n! standard: f2023\n"


CORRESPONDENCE_SOURCE = dedent('''\
module argument_correspondence_objects
  implicit none
  type :: box
    integer :: slot = -9
    procedure(set_iface), pointer, pass(self) :: pp => null()
  contains
    procedure :: set => set_box
  end type
  abstract interface
    subroutine set_iface(self, value)
      import :: box
      class(box), intent(inout) :: self
      integer, intent(in) :: value
    end subroutine
  end interface
contains
  subroutine set_box(self, value)
    class(box), intent(inout) :: self
    integer, intent(in) :: value
    self%slot = value
  end subroutine
end module
program argument_correspondence_passed_object
  use argument_correspondence_objects
  implicit none
  integer :: checks = 0
  integer :: key_a = -71, key_b = -72, pos_a = -81, pos_b = -82
  type(box) :: reduced, type_bound, proc_ptr, untouched, pp_other
  call record_pair(b=17, a=11, out_a=key_a, out_b=key_b)
  call expect_equal(key_a, 11, 'keyword dummy a')
  call expect_equal(key_b, 17, 'keyword dummy b')
  call record_pair(23, 29, pos_a, pos_b)
  call expect_equal(pos_a, 23, 'positional dummy a')
  call expect_equal(pos_b, 29, 'positional dummy b')
  call reduced%set(41)
  call expect_equal(reduced%slot, 41, 'reduced list passed object')
  call expect_equal(untouched%slot, -9, 'untouched reduced peer')
  call type_bound%set(47)
  call expect_equal(type_bound%slot, 47, 'type-bound data-ref object')
  proc_ptr%pp => set_box
  pp_other%pp => set_box
  call proc_ptr%pp(43)
  call expect_equal(proc_ptr%slot, 43, 'procedure pointer component object')
  call expect_equal(checks, 8, 'check count')
  write(*,'(a)') 'ARGUMENT CORRESPONDENCE PASSED OBJECT OK'
contains
  subroutine record_pair(a, b, out_a, out_b)
    integer, intent(in) :: a, b
    integer, intent(out) :: out_a, out_b
    out_a = a
    out_b = b
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
''')

CONDITIONAL_SOURCE = dedent('''\
program conditional_argument_selection
  implicit none
  integer :: checks = 0
  integer :: got = -99, variable_actual = 57
  call take((.true. ? 101 : 202), got)
  call expect_equal(got, 101, 'first true consequent')
  call take((.false. ? 11 : 33), got)
  call expect_equal(got, 33, 'last consequent default')
  call take((.true. ? variable_actual : 58), got)
  call expect_equal(got, 57, 'chosen variable actual')
  call expect_equal(checks, 3, 'check count')
  write(*,'(a)') 'CONDITIONAL ARGUMENT SELECTION OK'
contains
  subroutine take(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
''')

ASSOCIATION_SOURCE = dedent('''\
module association_effects_m
  implicit none
  type :: parent
    integer :: base = -1
  end type
  type, extends(parent) :: child
    integer :: ext = -2
  end type
contains
  subroutine take_class(x, out_base, out_ext)
    class(parent), intent(inout) :: x
    integer, intent(out) :: out_base, out_ext
    select type (x)
    type is (child)
      out_base = x%base
      out_ext = x%ext
      x%base = 55
    class default
      out_base = x%base
      out_ext = -777
    end select
  end subroutine
  subroutine take_parent(x, out_base)
    type(parent), intent(inout) :: x
    integer, intent(out) :: out_base
    out_base = x%base
    x%base = 41
  end subroutine
  subroutine take_value(x, entry, local)
    integer, value :: x
    integer, intent(out) :: entry, local
    entry = x
    x = 29
    local = x
  end subroutine
  subroutine ptr_dummy(q)
    integer, pointer :: q
    integer, target, save :: second = 202
    q => second
  end subroutine
  subroutine outer(x)
    integer, intent(inout) :: x
    call inner(x)
  end subroutine
  subroutine inner(y)
    integer, intent(inout) :: y
    y = 83
  end subroutine
  subroutine outer_comp(obj)
    type(parent), intent(inout) :: obj
    call inner(obj%base)
  end subroutine
end module
program argument_association_effects
  use association_effects_m
  implicit none
  integer :: checks = 0
  integer, target :: target_value = 71, first = 101
  integer, pointer :: p, q
  logical :: inquiry = .true.
  integer :: base_seen = -5, ext_seen = -6
  type(child), target :: child_target
  class(parent), pointer :: class_pointer
  type(parent), pointer :: parent_pointer
  type(child) :: child_actual
  integer :: caller_value = 17, entry_seen = -1, local_seen = -2
  integer :: ultimate = -83
  type(parent) :: holder, sibling
  p => target_value
  call read_nonpointer(p, base_seen)
  call expect_equal(base_seen, 71, 'associated pointer actual')
  nullify(p)
  inquiry = associated(p)
  call expect_false(inquiry, 'intrinsic inquiry exception')
  child_target%base = 23; child_target%ext = 5; class_pointer => child_target
  call take_class(class_pointer, base_seen, ext_seen)
  call expect_equal(base_seen, 23, 'polymorphic pointer target base')
  call expect_equal(ext_seen, 5, 'polymorphic pointer target extension')
  child_target%base = 23; child_target%ext = 99; parent_pointer => child_target%parent
  call take_parent(parent_pointer, base_seen)
  call expect_equal(base_seen, 23, 'nonpolymorphic pointer declared part entry')
  call expect_equal(child_target%base, 41, 'nonpolymorphic pointer declared part update')
  call expect_equal(child_target%ext, 99, 'extension component not associated')
  child_actual%base = 7; child_actual%ext = 31
  call take_class(child_actual, base_seen, ext_seen)
  call expect_equal(ext_seen, 31, 'polymorphic nonpointer actual')
  child_actual%base = 7; child_actual%ext = 99
  call take_parent(child_actual%parent, base_seen)
  call expect_equal(base_seen, 7, 'nonpolymorphic nonpointer declared part entry')
  call expect_equal(child_actual%base, 41, 'nonpolymorphic nonpointer declared part update')
  call expect_equal(child_actual%ext, 99, 'nonpolymorphic nonpointer extension unchanged')
  caller_value = 17
  call take_value(caller_value, entry_seen, local_seen)
  call expect_equal(entry_seen, 17, 'value dummy initial value')
  call expect_equal(local_seen, 29, 'value dummy definable local')
  call expect_equal(caller_value, 17, 'value dummy caller unchanged')
  q => first
  call ptr_dummy(q)
  call expect_true(associated(q), 'pointer dummy actual associated')
  call expect_false(associated(q, first), 'pointer dummy actual retargeted')
  call expect_equal(q, 202, 'pointer dummy target value')
  ultimate = -83
  call outer(ultimate)
  call expect_equal(ultimate, 83, 'ultimate dummy chain')
  holder%base = -97; sibling%base = -96
  call outer_comp(holder)
  call expect_equal(holder%base, 83, 'ultimate subobject chain')
  call expect_equal(sibling%base, -96, 'ultimate sibling unchanged')
  call expect_equal(checks, 20, 'check count')
  write(*,'(a)') 'ARGUMENT ASSOCIATION EFFECTS OK'
contains
  subroutine read_nonpointer(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_true(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (.not. got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
''')

ALLOC_POINTER_SOURCE = dedent('''\
module alloc_pointer_dummy_m
  implicit none
  type :: parent
    integer :: base = -1
  end type
  type, extends(parent) :: child
    integer :: ext = -2
  end type
  integer, pointer :: observed_ptr(:) => null()
  integer, pointer :: module_p(:) => null()
  integer, target :: module_target_scalar = 42
contains
  subroutine alloc_scope(x, out)
    integer, allocatable, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine ptr_scope(p, out)
    integer, pointer, intent(in) :: p
    integer, intent(out) :: out
    out = p
  end subroutine
  subroutine class_ptr(p, out)
    class(parent), pointer, intent(in) :: p
    integer, intent(out) :: out
    select type (p)
    type is (child)
      out = p%ext
    class default
      out = -700
    end select
  end subroutine
  subroutine unlimited_alloc(x, out)
    class(*), allocatable, intent(in) :: x
    integer, intent(out) :: out
    select type (x)
    type is (integer)
      out = x
    class default
      out = -701
    end select
  end subroutine
  subroutine base_alloc(x, out)
    type(parent), allocatable, intent(in) :: x
    integer, intent(out) :: out
    out = x%base
  end subroutine
  subroutine rank_alloc(x, lo, hi, value)
    integer, allocatable, intent(in) :: x(:)
    integer, intent(out) :: lo, hi, value
    lo = lbound(x, 1)
    hi = ubound(x, 1)
    value = x(0)
  end subroutine
  subroutine fixed_char(x, out_len, out_text)
    character(len=2), allocatable, intent(in) :: x
    integer, intent(out) :: out_len
    character(len=2), intent(out) :: out_text
    out_len = len(x)
    out_text = x
  end subroutine
  subroutine assumed_char(p, out_len, out_ch)
    character(len=*), pointer, intent(in) :: p
    integer, intent(out) :: out_len
    character(len=1), intent(out) :: out_ch
    out_len = len(p)
    out_ch = p(3:3)
  end subroutine
  subroutine deferred_char(x, out_len, out_text)
    character(len=:), allocatable, intent(in) :: x
    integer, intent(out) :: out_len
    character(len=2), intent(out) :: out_text
    out_len = len(x)
    out_text = x
  end subroutine
  subroutine unallocated_inout(x, was_alloc)
    integer, allocatable, intent(inout) :: x
    logical, intent(out) :: was_alloc
    was_alloc = allocated(x)
    allocate(x)
    x = 42
  end subroutine
  subroutine intent_out_entry(x, was_alloc, lo, hi, value)
    integer, allocatable, intent(out) :: x(:)
    logical, intent(out) :: was_alloc
    integer, intent(out) :: lo, hi, value
    was_alloc = allocated(x)
    allocate(x(1:1))
    x(1) = 42
    lo = lbound(x, 1)
    hi = ubound(x, 1)
    value = x(1)
  end subroutine
  subroutine target_assoc(x, inside_assoc, inside_value)
    integer, allocatable, target, intent(inout) :: x(:)
    logical, intent(out) :: inside_assoc
    integer, intent(out) :: inside_value
    inside_assoc = associated(module_p, x)
    inside_value = x(0)
    observed_ptr => x
  end subroutine
  subroutine ptr_inout(q, is_assoc, value)
    integer, pointer, intent(inout) :: q
    logical, intent(out) :: is_assoc
    integer, intent(out) :: value
    is_assoc = associated(q)
    value = q
  end subroutine
  subroutine ptr_intent_in(q, is_assoc, value)
    integer, pointer, intent(in) :: q
    logical, intent(out) :: is_assoc
    integer, intent(out) :: value
    is_assoc = associated(q)
    value = q
  end subroutine
  subroutine ptr_target_in(q, is_assoc, value)
    integer, pointer, intent(in) :: q
    logical, intent(out) :: is_assoc
    integer, intent(out) :: value
    is_assoc = associated(q, module_target_scalar)
    value = q
  end subroutine
end module
program allocatable_pointer_dummy_effects
  use alloc_pointer_dummy_m
  implicit none
  integer :: checks = 0, out = -99, lo = -11, hi = -12, value = -13, len_value = -1
  logical :: flag = .true.
  character(len=2), allocatable :: ca
  character(len=:), allocatable :: cd
  character(len=2) :: text = '##'
  character(len=1) :: ch = '#'
  character(len=3), target :: char_target = 'abc'
  character(len=3), pointer :: char_pointer
  integer, allocatable, target :: array_actual(:)
  integer, allocatable :: scalar_alloc, unalloc, out_array(:)
  integer, target :: scalar_target = 43
  integer, pointer :: scalar_pointer, target_pointer
  type(child), target :: child_target
  class(parent), pointer :: poly_pointer
  class(*), allocatable :: any_alloc
  type(parent), allocatable :: base_actual
  allocate(scalar_alloc); scalar_alloc = 31
  call alloc_scope(scalar_alloc, out); call expect_equal(out, 31, 'allocatable same attribute scope')
  scalar_pointer => scalar_target
  call ptr_scope(scalar_pointer, out); call expect_equal(out, 43, 'pointer same attribute scope')
  child_target%base = 5; child_target%ext = 42; poly_pointer => child_target
  call class_ptr(poly_pointer, out); call expect_equal(out, 42, 'polymorphic pointer correspondence')
  allocate(any_alloc, source=42)
  call unlimited_alloc(any_alloc, out); call expect_equal(out, 42, 'unlimited polymorphic allocatable')
  allocate(base_actual); base_actual%base = 42
  call base_alloc(base_actual, out); call expect_equal(out, 42, 'declared type same allocatable')
  allocate(array_actual(-1:1)); array_actual = [40, 41, 42]
  call rank_alloc(array_actual, lo, hi, value)
  call expect_equal(lo, -1, 'allocatable rank lower bound')
  call expect_equal(hi, 1, 'allocatable rank upper bound')
  call expect_equal(value, 41, 'allocatable rank value')
  allocate(character(len=2) :: ca); ca = '42'
  call fixed_char(ca, len_value, text)
  call expect_equal(len_value, 2, 'fixed character length')
  call expect_char2(text, '42', 'fixed character text')
  char_pointer => char_target
  call assumed_char(char_pointer, len_value, ch)
  call expect_equal(len_value, 3, 'assumed character length')
  call expect_char1(ch, 'c', 'assumed character third')
  allocate(character(len=2) :: cd); cd = '42'
  call deferred_char(cd, len_value, text)
  call expect_equal(len_value, 2, 'deferred character length')
  call expect_char2(text, '42', 'deferred character text')
  if (allocated(unalloc)) error stop 91
  flag = .true.; call unallocated_inout(unalloc, flag)
  call expect_false(flag, 'unallocated actual passes in')
  call expect_true(allocated(unalloc), 'allocation status passes out')
  call expect_equal(unalloc, 42, 'allocated value passes out')
  allocate(out_array(-2:0)); out_array = [17, 18, 19]
  flag = .true.; call intent_out_entry(out_array, flag, lo, hi, value)
  call expect_false(flag, 'intent out deallocated on entry')
  call expect_equal(lo, 1, 'intent out new lower bound')
  call expect_equal(hi, 1, 'intent out new upper bound')
  call expect_equal(value, 42, 'intent out new value')
  deallocate(array_actual); allocate(array_actual(-1:1)); array_actual = [40, 41, 42]; module_p => array_actual
  flag = .false.; call target_assoc(array_actual, flag, value)
  call expect_true(flag, 'target dummy invocation pointer association')
  call expect_equal(value, 41, 'target dummy invocation value')
  call expect_true(associated(observed_ptr, array_actual), 'target dummy completion pointer association')
  call expect_equal(observed_ptr(0), 41, 'target dummy completion value')
  scalar_pointer => scalar_target
  flag = .false.; value = -42; call ptr_inout(scalar_pointer, flag, value)
  call expect_true(flag, 'non-intent-in pointer actual required')
  call expect_equal(value, 43, 'non-intent-in pointer value')
  target_pointer => module_target_scalar
  flag = .false.; value = -41; call ptr_intent_in(target_pointer, flag, value)
  call expect_true(flag, 'intent in pointer actual accepted')
  call expect_equal(value, 42, 'intent in pointer actual value')
  flag = .false.; value = -42; call ptr_target_in(module_target_scalar, flag, value)
  call expect_true(flag, 'intent in target actual associated')
  call expect_equal(value, 42, 'intent in target actual value')
  call expect_equal(checks, 31, 'check count')
  write(*,'(a)') 'ALLOCATABLE POINTER DUMMY EFFECTS OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_true(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (.not. got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (got) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char2(got, want, label)
    character(len=2), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 2 .or. got /= want) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char1(got, want, label)
    character(len=1), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 1 .or. got /= want) then
      write(*,'(a,1x,a)') 'AA1552-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
''')

C1550_SOURCE = dedent('''\
program c1550_contiguous_pointer_control
  implicit none
  integer :: checks = 0
  integer, target :: a(4) = [39, 40, 41, 42]
  integer, pointer, contiguous :: p(:)
  p => a
  call accept_contiguous(p)
  call expect_equal(checks, 1, 'check count')
  write(*,'(a)') 'C1550 CONTIGUOUS POINTER CONTROL OK'
contains
  subroutine accept_contiguous(q)
    integer, pointer, contiguous, intent(in) :: q(:)
    call expect_equal(q(1), 39, 'contiguous first element')
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
''')

C1550_INVALID_SOURCE = C1550_SOURCE.replace("integer, pointer, contiguous :: p(:)", "integer, pointer :: p(:)")


def mut(mid, facet, replacements):
    return {"id": mid, "facet": facet, "kind": "feature", "replacements": replacements}


def make_case_specs():
    completion1 = "ARGUMENT CORRESPONDENCE PASSED OBJECT OK\n"
    completion2 = "CONDITIONAL ARGUMENT SELECTION OK\n"
    completion3 = "ARGUMENT ASSOCIATION EFFECTS OK\n"
    completion4 = "ALLOCATABLE POINTER DUMMY EFFECTS OK\n"
    completion5 = "C1550 CONTIGUOUS POINTER CONTROL OK\n"
    return [
        ("correspondence", "S15.5.2.1-001", CORRESPONDENCE_SOURCE, completion1, [
            mut("remove-keywords-swaps-actuals", "keyword-correspondence", [("call record_pair(b=17, a=11, out_a=key_a, out_b=key_b)", "call record_pair(17, 11, key_a, key_b)")]),
            mut("swap-positional-actuals", "positional-correspondence", [("call record_pair(23, 29, pos_a, pos_b)", "call record_pair(29, 23, pos_a, pos_b)")]),
            mut("change-reduced-list-data-ref", "passed-object-reduced-list", [("call reduced%set(41)", "call untouched%set(41)")]),
        ], "valid"),
        ("passed_object", "S15.5.2.2-001", CORRESPONDENCE_SOURCE, completion1, [
            mut("change-type-bound-data-ref", "type-bound-data-ref-passed-object", [("call type_bound%set(47)", "call untouched%set(47)")]),
            mut("change-procedure-pointer-component-data-ref", "procedure-pointer-component-data-ref-passed-object", [("call proc_ptr%pp(43)", "call pp_other%pp(43)")]),
        ], "valid"),
        ("conditional_order", "S15.5.2.3-001", CONDITIONAL_SOURCE, completion2, [
            mut("first-guard-made-false", "first-true-consequent", [("call take((.true. ? 101 : 202), got)", "call take((.false. ? 101 : 202), got)")]),
            mut("default-guard-made-true", "last-consequent-default", [("call take((.false. ? 11 : 33), got)", "call take((.true. ? 11 : 33), got)")]),
        ], "valid"),
        ("conditional_actual", "S15.5.2.3-002", CONDITIONAL_SOURCE, completion2, [
            mut("choose-other-variable-consequent", "chosen-variable-actual", [("call take((.true. ? variable_actual : 58), got)", "call take((.false. ? variable_actual : 58), got)")]),
        ], "valid"),
        ("argument_association_p1", "S15.5.2.4-001", ASSOCIATION_SOURCE, completion3, [
            mut("pointer-actual-target-value-changed", "associated-pointer-actual-control", [("integer, target :: target_value = 71", "integer, target :: target_value = 72")]),
            mut("intrinsic-inquiry-associated-pointer", "intrinsic-inquiry-exception", [("inquiry = associated(p)", "p => target_value\n  inquiry = associated(p)")]),
        ], "valid"),
        ("argument_association_p2", "S15.5.2.4-002", ASSOCIATION_SOURCE, completion3, [
            mut("polymorphic-pointer-extension-changed", "polymorphic-dummy-associated-with-pointer-target", [("child_target%base = 23; child_target%ext = 5; class_pointer => child_target", "child_target%base = 23; child_target%ext = 6; class_pointer => child_target")]),
            mut("nonpolymorphic-pointer-base-changed", "nonpolymorphic-dummy-associated-with-declared-type-part", [("child_target%base = 23; child_target%ext = 99; parent_pointer => child_target%parent", "child_target%base = 24; child_target%ext = 99; parent_pointer => child_target%parent")]),
        ], "valid"),
        ("argument_association_p3", "S15.5.2.4-003", ASSOCIATION_SOURCE, completion3, [
            mut("polymorphic-nonpointer-extension-changed", "polymorphic-dummy-associated-with-nonpointer-actual", [("child_actual%base = 7; child_actual%ext = 31", "child_actual%base = 7; child_actual%ext = 32")]),
            mut("nonpolymorphic-nonpointer-base-changed", "nonpolymorphic-dummy-associated-with-nonpointer-declared-part", [("child_actual%base = 7; child_actual%ext = 99", "child_actual%base = 8; child_actual%ext = 99")]),
        ], "valid"),
        ("argument_association_value", "S15.5.2.4-004", ASSOCIATION_SOURCE, completion3, [
            mut("value-entry-initial-changed", "value-dummy-initial-value", [("caller_value = 17\n  call take_value", "caller_value = 18\n  call take_value")]),
            mut("value-local-assignment-changed", "value-dummy-definable-anonymous-object", [("x = 29\n    local = x", "x = 30\n    local = x")]),
            mut("value-caller-reassigned-after-call", "value-dummy-caller-unchanged", [("call take_value(caller_value, entry_seen, local_seen)", "call take_value(caller_value, entry_seen, local_seen)\n  caller_value = 29")]),
        ], "valid"),
        ("argument_association_pointer_dummy", "S15.5.2.4-005", ASSOCIATION_SOURCE, completion3, [
            mut("pointer-dummy-retarget-removed", "pointer-dummy-associated-with-pointer-actual", [("q => second", "nullify(q)")]),
        ], "valid"),
        ("argument_association_ultimate", "S15.5.2.4-007", ASSOCIATION_SOURCE, completion3, [
            mut("ultimate-chain-assignment-changed", "ultimate-argument-through-dummy-chain", [("y = 83", "y = 84")]),
            mut("ultimate-subobject-call-sibling", "ultimate-argument-through-subobject-chain", [("call outer_comp(holder)", "call outer_comp(sibling)")]),
        ], "valid"),
        ("alloc_pointer_scope", "S15.5.2.6-001", ALLOC_POINTER_SOURCE, completion4, [
            mut("allocatable-scope-value-changed", "allocatable-pointer-same-attribute-scope", [("scalar_alloc = 31", "scalar_alloc = 32")]),
        ], "valid"),
        ("alloc_pointer_polymorphic", "S15.5.2.6-002", ALLOC_POINTER_SOURCE, completion4, [
            mut("polymorphic-pointer-correspondence-ext-changed", "allocatable-pointer-polymorphic-correspondence", [("child_target%base = 5; child_target%ext = 42; poly_pointer => child_target", "child_target%base = 5; child_target%ext = 43; poly_pointer => child_target")]),
            mut("unlimited-alloc-source-changed", "allocatable-pointer-unlimited-polymorphic-correspondence", [("allocate(any_alloc, source=42)", "allocate(any_alloc, source=43)")]),
            mut("declared-type-base-changed", "allocatable-pointer-declared-type-same", [("base_actual%base = 42", "base_actual%base = 43")]),
        ], "valid"),
        ("alloc_pointer_rank", "S15.5.2.6-003", ALLOC_POINTER_SOURCE, completion4, [
            mut("rank-value-changed", "allocatable-pointer-rank-match", [("allocate(array_actual(-1:1)); array_actual = [40, 41, 42]\n  call rank_alloc", "allocate(array_actual(-1:1)); array_actual = [40, 44, 42]\n  call rank_alloc")]),
        ], "valid"),
        ("alloc_pointer_type_param", "S15.5.2.6-004", ALLOC_POINTER_SOURCE, completion4, [
            mut("fixed-character-text-changed", "allocatable-pointer-type-parameter-agreement", [("ca = '42'", "ca = '43'")]),
        ], "valid"),
        ("alloc_pointer_assumed_param", "S15.5.2.6-005", ALLOC_POINTER_SOURCE, completion4, [
            mut("assumed-character-target-changed", "allocatable-pointer-assumed-type-parameter-capture", [("char_target = 'abc'", "char_target = 'abd'")]),
        ], "valid"),
        ("alloc_pointer_deferred_param", "S15.5.2.6-006", ALLOC_POINTER_SOURCE, completion4, [
            mut("deferred-character-text-changed", "allocatable-pointer-same-deferred-type-parameters", [("cd = '42'", "cd = '43'")]),
        ], "valid"),
        ("alloc_dummy_scope", "S15.5.2.7-001", ALLOC_POINTER_SOURCE, completion4, [
            mut("allocatable-dummy-scope-value-changed", "allocatable-dummy-data-object-scope", [("scalar_alloc = 31", "scalar_alloc = 32")]),
        ], "valid"),
        ("alloc_dummy_actual", "S15.5.2.7-002", ALLOC_POINTER_SOURCE, completion4, [
            mut("allocatable-required-value-changed", "allocatable-dummy-actual-allocatable-required", [("scalar_alloc = 31", "scalar_alloc = 32")]),
        ], "valid"),
        ("alloc_dummy_unallocated", "S15.5.2.7-003", ALLOC_POINTER_SOURCE, completion4, [
            mut("unallocated-allocates-different-value", "allocatable-dummy-unallocated-actual-permitted", [("x = 42", "x = 43")]),
        ], "valid"),
        ("alloc_dummy_target_invocation", "S15.5.2.7-008", ALLOC_POINTER_SOURCE, completion4, [
            mut("target-association-module-pointer-retargeted", "allocatable-target-dummy-invocation-pointer-association", [("module_p => array_actual", "nullify(module_p)")]),
        ], "valid"),
        ("alloc_dummy_target_completion", "S15.5.2.7-009", ALLOC_POINTER_SOURCE, completion4, [
            mut("completion-pointer-not-saved", "allocatable-target-dummy-completion-pointer-association", [("observed_ptr => x", "nullify(observed_ptr)")]),
        ], "valid"),
        ("alloc_dummy_definable", "S15.5.2.7-010", ALLOC_POINTER_SOURCE, completion4, [
            mut("inout-definable-value-changed", "allocatable-intent-out-inout-actual-definable", [("x = 42", "x = 43")]),
        ], "valid"),
        ("alloc_dummy_intent_out", "S15.5.2.7-011", ALLOC_POINTER_SOURCE, completion4, [
            mut("intent-out-new-value-changed", "allocatable-intent-out-actual-deallocated-on-entry", [("x(1) = 42", "x(1) = 43")]),
        ], "valid"),
        ("pointer_dummy_scope", "S15.5.2.8-001", ALLOC_POINTER_SOURCE, completion4, [
            mut("pointer-dummy-scope-target-changed", "dummy-data-pointer-scope", [("integer, target :: module_target_scalar = 42", "integer, target :: module_target_scalar = 44")]),
        ], "valid"),
        ("c1550_control", "C1550", C1550_SOURCE, completion5, [
            mut("contiguous-control-first-value-changed", "contiguous-dummy-pointer-simply-contiguous-positive", [("integer, target :: a(4) = [39, 40, 41, 42]", "integer, target :: a(4) = [38, 40, 41, 42]")]),
        ], "valid"),
        ("c1550_noncontiguous", "C1550", C1550_INVALID_SOURCE, "", [], "invalid"),
        ("pointer_dummy_inout", "S15.5.2.8-002", ALLOC_POINTER_SOURCE, completion4, [
            mut("non-intent-in-pointer-target-changed", "non-intent-in-dummy-pointer-actual-pointer-required", [("integer, target :: scalar_target = 43", "integer, target :: scalar_target = 44")]),
        ], "valid"),
        ("pointer_dummy_intent_in", "S15.5.2.8-003", ALLOC_POINTER_SOURCE, completion4, [
            mut("intent-in-pointer-target-changed", "intent-in-dummy-pointer-actual-pointer-or-target", [("integer, target :: module_target_scalar = 42", "integer, target :: module_target_scalar = 44")]),
        ], "valid"),
        ("pointer_dummy_target", "S15.5.2.8-004", ALLOC_POINTER_SOURCE, completion4, [
            mut("intent-in-target-associated-value-changed", "intent-in-dummy-pointer-associated-with-target-actual", [("integer, target :: module_target_scalar = 42", "integer, target :: module_target_scalar = 44")]),
        ], "valid"),
    ]


def identifier(rule, variant, kind):
    stem = rule.replace('.', '_').replace('-', '_')
    return f"{stem}_{'invalid' if kind == 'invalid' else 'valid'}__{TOPIC}_{variant}"


def manifest(cid, rule, facets, kind, completion):
    base = {
        "schema_version": 1,
        "id": cid,
        "rule": rule,
        "facets": list(facets),
        "evidence": "effect" if kind == "invalid" else ("positive-control" if rule in RESTRICTION_RULES else "effect"),
        "standard": "f2023",
        "oracle_basis": "standard",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
    }
    if kind == "invalid":
        base["expect"] = {"phase": "compile", "step": "source", "outcome": "diagnose", "diagnostic": {"file": "source.f90", "line": 11, "end_line": 11, "excludes_any": EXCLUDES}}
    else:
        base["link"] = {"driver": "fortran", "objects": ["source.o"], "output": "program"}
        base["expect"] = {"phase": "run", "outcome": "success", "exit_code": 0, "stdout": completion, "stderr": ""}
    return base


def mutation_records(source, mutations):
    out = []
    for mutation in mutations:
        changed = source
        reps = []
        for expected, replacement in mutation["replacements"]:
            if changed.count(expected) != 1:
                raise ValueError(f"{mutation['id']} expected unique text {expected!r}, saw {changed.count(expected)}")
            start = changed.index(expected)
            reps.append({"expected": expected, "replacement": replacement, "span": [start, start + len(expected)]})
            changed = changed[:start] + replacement + changed[start + len(expected):]
        if changed == source:
            raise ValueError("mutation did not change source: " + mutation["id"])
        item = copy.deepcopy(mutation)
        item["replacements"] = reps
        item["mutant_sha256"] = sha(changed.encode("ascii"))
        out.append(item)
    return out


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for variant, rule, body, completion, muts, kind in make_case_specs():
        facets = FACETS_BY_RULE[rule] if kind == "invalid" else [m["facet"] for m in muts]
        # C1550 valid carries only the positive facet; invalid carries the negative facet.
        if variant == "c1550_control":
            facets = ["contiguous-dummy-pointer-simply-contiguous-positive"]
        if variant == "c1550_noncontiguous":
            facets = ["contiguous-dummy-pointer-noncontiguous-actual-negative"]
        cid = identifier(rule, variant, kind)
        source = header(rule, facets) + body
        directory = root / "tests" / "fixtures" / (PREFIX + variant)
        spec = {
            "id": cid,
            "variant": variant,
            "rule": rule,
            "kind": kind,
            "facets": facets,
            "source": source,
            "source_sha256": sha(source.encode("ascii")),
            "completion": completion,
            "manifest": manifest(cid, rule, facets, kind, completion),
            "path": directory.relative_to(root).as_posix() + "/fixture.json",
            "mutations": mutation_records(source, muts),
        }
        specs[cid] = spec
        files[directory / "source.f90"] = source.encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, p in enumerate(paragraphs) if p.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def synced_catalogue(section, catalogue, specs):
    updated = copy.deepcopy(catalogue)
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for req in updated["requirements"]:
        rule = req["id"]
        pending = req.setdefault("pending", {})
        for facet in covered.get(rule, set()):
            pending.pop(facet, None)
        for facet in EXPECTED_REMAINING.get(rule, set()):
            if facet in PENDING_REASONS:
                pending[facet] = PENDING_REASONS[facet]
        if rule in covered:
            req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
            req["oracle_limitation"] = owned_paragraph(req.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


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
    if section == "15.5.2.1":
        summary = SUMMARY_BEGIN + "\n## Argument association 15.5.2A fixtures\n\nBatch316 adds f2023 fixtures for selected argument correspondence, passed-object, conditional argument, ordinary/pointer/value association, allocatable dummy, pointer dummy, and C1550 contiguous-pointer facets. Conditional .NIL., side-effect guard order, richer conditional characteristics, coarray, undefined-status, and processor-dependent facets remain pending.\n" + SUMMARY_END
        if SUMMARY_BEGIN in before:
            leading, owned = before.split(SUMMARY_BEGIN)
            _, trailing = owned.split(SUMMARY_END)
            before = leading + summary + trailing
        else:
            before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generated_catalogues_and_views(root, specs):
    catalogues, views = {}, {}
    for section, rel in CATALOGUES.items():
        data = json.loads((Path(root) / rel).read_text())
        updated = synced_catalogue(section, data, specs)
        catalogues[rel] = updated
        views[VIEWS[section]] = rendered_view(section, updated, root)
    return catalogues, views


def generate(root=ROOT, check=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues, views = generated_catalogues_and_views(root, specs)
    if check:
        stale = [p.relative_to(root).as_posix() for p, raw in files.items() if not p.is_file() or p.read_bytes() != raw]
        stale += [rel for rel, data in catalogues.items() if json.loads((root / rel).read_text()) != data]
        stale += [rel for rel, text in views.items() if (root / rel).read_text() != text]
        if stale:
            raise SystemExit("stale argument_association_15_5_2_a files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for rel, data in catalogues.items():
            (root / rel).write_text(json.dumps(data, indent=2) + "\n")
        for rel, text in views.items():
            (root / rel).write_text(text)
    return files, specs


def mutate_source(spec, mutation):
    changed = spec["source"]
    for repl in mutation["replacements"]:
        if changed.count(repl["expected"]) != 1:
            raise ValueError("replacement no longer bound: " + repl["expected"])
        changed = changed.replace(repl["expected"], repl["replacement"], 1)
    if changed == spec["source"]:
        raise ValueError("mutation did not change source")
    return changed


def std_flag(compiler, std):
    return "--std=" + std if "lfortran" in Path(compiler).name.lower() else "-std=" + std


def run_command(argv, cwd, timeout=60):
    env = os.environ.copy()
    env["TMPDIR"] = str((ROOT / ".argument_association_15_5_2_a_tmp").resolve())
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)


def compile_and_run(source, compiler, std, workdir):
    (workdir / "source.f90").write_text(source)
    exe = workdir / "program"
    comp = run_command([compiler, std_flag(compiler, std), "source.f90", "-o", "program"], workdir)
    if comp.returncode != 0:
        return {"phase": "compile", "returncode": comp.returncode, "stdout": comp.stdout, "stderr": comp.stderr}
    run = run_command([str(exe)], workdir)
    return {"phase": "run", "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr, "compile_stdout": comp.stdout, "compile_stderr": comp.stderr}


def mutation_matrix(compiler, std="f2023", root=ROOT, keep=False):
    root = Path(root)
    _, specs = build_corpus(root)
    scratch = root / ".argument_association_15_5_2_a_mutation_work"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    results = []
    try:
        for cid, spec in specs.items():
            if spec["kind"] != "valid":
                continue
            parent_dir = scratch / cid / "parent"
            parent_dir.mkdir(parents=True)
            parent = compile_and_run(spec["source"], compiler, std, parent_dir)
            parent_ok = parent["phase"] == "run" and parent["returncode"] == 0 and parent["stdout"] == spec["completion"] and parent["stderr"] == ""
            results.append({"case": cid, "mutation": "parent", "ok": parent_ok, **parent})
            if not parent_ok:
                continue
            for mutation in spec["mutations"]:
                mdir = scratch / cid / mutation["id"]
                mdir.mkdir(parents=True)
                observed = compile_and_run(mutate_source(spec, mutation), compiler, std, mdir)
                failed = observed["phase"] == "run" and not (observed["returncode"] == 0 and observed["stdout"] == spec["completion"] and observed["stderr"] == "")
                results.append({"case": cid, "mutation": mutation["id"], "facet": mutation["facet"], "ok": failed, **observed})
    finally:
        if not keep:
            shutil.rmtree(scratch, ignore_errors=True)
            shutil.rmtree(root / ".argument_association_15_5_2_a_tmp", ignore_errors=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        results = mutation_matrix(args.compiler, args.std, args.root, args.keep_work)
        failed = [row for row in results if not row["ok"]]
        if failed:
            for row in failed:
                print(json.dumps({k: row.get(k) for k in ("case", "mutation", "phase", "returncode", "stdout", "stderr")}, indent=2))
            raise SystemExit(f"mutation matrix failed: {len(failed)} bad rows out of {len(results)}")
        print(f"mutation matrix OK: {sum(1 for r in results if r['mutation']=='parent')} parents passed; {sum(1 for r in results if r['mutation']!='parent')} mutants failed")
        return
    _, specs = generate(args.root, args.check)
    facet_count = sum(len(s["facets"]) for s in specs.values())
    print(f"{'checked' if args.check else 'generated'} {len(specs)} {TOPIC} fixtures, {facet_count} facets")


if __name__ == "__main__":
    main()
