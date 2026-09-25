#!/usr/bin/env python3
"""Generated fixtures for Fortran 2023 ordinary dummy variables, 15.5.2.5."""

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
TOPIC = "ordinary_dummies_15_5_2_5"
PREFIX = TOPIC + "_"

CATALOGUES = {"15.5.2.5": "doc/catalogues/ordinary_dummy_variables_15_5_2_5.json"}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}
SUMMARY_BEGIN = "<!-- BEGIN ORDINARY DUMMIES 15.5.2.5 FIXTURES -->"
SUMMARY_END = "<!-- END ORDINARY DUMMIES 15.5.2.5 FIXTURES -->"
EXCLUDES = ["not implemented", "not yet implemented", "unsupported", "internal error", "internal:", "asr", "verifier"]

RESTRICTION_RULES = {
    "S15.5.2.5-002", "S15.5.2.5-003", "S15.5.2.5-007", "S15.5.2.5-015",
    "S15.5.2.5-016", "S15.5.2.5-017", "S15.5.2.5-021", "S15.5.2.5-022",
    "C1548", "C1549",
}

FACETS_BY_RULE = {
    "S15.5.2.5-001": ["ordinary-dummy-scope-source-use"],
    "S15.5.2.5-004": ["scalar-character-length-bound", "scalar-character-leftmost-association", "array-character-leftmost-element-sequence-association"],
    "S15.5.2.5-005": ["assumed-character-length-from-effective-argument"],
    "S15.5.2.5-007": ["allocatable-inquiry-exception"],
    "S15.5.2.5-010": ["target-dummy-invocation-pointer-association", "target-dummy-return-surviving-pointer-remains-associated"],
    "S15.5.2.5-015": ["assumed-rank-scalar-actual-exception"],
    "S15.5.2.5-018": ["assumed-rank-accepts-scalar", "assumed-rank-accepts-array"],
    "S15.5.2.5-019": ["assumed-rank-rank-and-extents", "assumed-rank-lower-bound-one", "assumed-rank-upper-bound-extent"],
    "S15.5.2.5-020": ["array-actual-element-order-association"],
    "S15.5.2.5-023": ["intent-out-default-initialized-direct-component-exception"],
    "C1548": ["nonpointer-async-discontiguous-dummy-shape-restriction", "nonpointer-volatile-discontiguous-dummy-shape-restriction", "nonpointer-discontiguous-dummy-no-contiguous"],
    "C1549": ["array-pointer-async-noncontiguous-dummy-form-restriction", "array-pointer-volatile-noncontiguous-dummy-form-restriction", "array-pointer-noncontiguous-dummy-no-contiguous"],
}

ORACLE_PREFIXES = {rule: f"{rule} ordinary_dummies_15_5_2_5 fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} ordinary_dummies_15_5_2_5 boundaries: " for rule in FACETS_BY_RULE}
ORACLES = {
    rule: ORACLE_PREFIXES[rule]
    + "Generated f2023 fixtures establish non-default sentinels, call a nonelemental procedure with nonallocatable nonpointer ordinary dummies, and assert exact integer, logical, character length/text, rank/shape/bound, or defined pointer-association properties required by the cited source unit. Each runtime or positive-control facet has a distinct conforming feature mutation that changes the observed dummy-argument association property."
    for rule in FACETS_BY_RULE
}
ORACLES["C1548"] = ORACLE_PREFIXES["C1548"] + "Positive controls pass asynchronous or volatile discontiguous nonpointer array sections to allowed assumed-shape non-CONTIGUOUS dummies and check exact element values. Negative fixtures change only the C1548-constrained dummy form or CONTIGUOUS property and require any compiler diagnostic anchored at the call line."
ORACLES["C1549"] = ORACLE_PREFIXES["C1549"] + "Positive controls pass asynchronous or volatile noncontiguous array pointer actuals to allowed assumed-shape non-CONTIGUOUS dummies and check exact element values. Negative fixtures change only the C1549-constrained dummy form or CONTIGUOUS property and require any compiler diagnostic anchored at the call line."
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule]
    + "Only single-image, defined states are asserted. Coindexed/coarray arguments, assumed-type negative exclusions, PDT LEN parameter fixtures, undefined pointer or definition status, processor-dependent forwarded TARGET association, storage addresses, descriptor identity, exact diagnostic wording, and unnumbered restrictions without a portable runtime observation remain pending."
    for rule in FACETS_BY_RULE
}

RESTORE_PENDING = {
    "S15.5.2.5-002": {
        "type-compatible-ordinary-dummy": "Positive plan passes a child actual to CLASS(parent) dummy and a parent actual to TYPE(parent) dummy, with component sentinels 11 and 13. Source-control negative passes an unrelated derived type; no required diagnostic claim.",
        "polymorphic-assumed-size-requires-polymorphic-dummy": "Source-control negative passes a polymorphic assumed-size actual onward to a nonpolymorphic dummy; positive control uses CLASS(parent) dummy and observes selected parent values 3 and 5.",
    },
    "S15.5.2.5-003": {
        "kind-parameter-agreement": "Positive plan calls a selected_int_kind(4) dummy with the same kind and value 123; source-control negative changes only actual kind while preserving value spelling.",
        "default-or-c-character-length-exception": "Positive plan passes CHARACTER(5) actual \"ABCDE\" to CHARACTER(3) scalar dummy and observes \"ABC\" under p4; companion noncharacter PDT keeps length agreement load-bearing.",
    },
    "S15.5.2.5-007": {
        "allocated-allocatable-actual-control": "Allocate integer allocatable a with value 67, pass to a nonoptional nonallocatable dummy, and expect callee observes 67 in sentinel -67.",
    },
    "S15.5.2.5-015": {
        "noncoindexed-scalar-actual-scalar-dummy-rule": "Positive plan passes integer scalar 41 to scalar dummy and observes 41; source-control negative passes the same scalar to rank-one explicit-shape dummy outside every listed exception, with no required diagnostic claim.",
        "character-scalar-sequence-exception": "Pass default CHARACTER scalar \"WXYZ\" to an explicit-shape CHARACTER(1) dummy array of size 4 and expect elements \"W\",\"X\",\"Y\",\"Z\" under sequence-association ownership. Also pass substring actual a(2)(2:4), where a is a default-character explicit-shape array that is not assumed-shape, pointer, or polymorphic and a(2) is \"vwxyz\"; expect dummy elements \"w\",\"x\",\"y\" and a companion assignment d(2)=\"Q\" to make a(2)(3:3)==\"Q\".",
    },
    "S15.5.2.5-016": {
        "generic-nonelemental-rank-agreement": "Positive plan defines generic g with rank-one dummy and passes rank-one actual [2,4], expecting sum 6; source-control negative passes scalar 2 to that generic-specific path.",
        "defined-operator-nonelemental-rank-agreement": "Positive plan defines operator .twice. for rank-one integer arrays and expects [4,8] from [2,4]; source-control negative applies it to a scalar.",
        "defined-assignment-nonelemental-rank-agreement": "Positive plan defines assignment from rank-one integer source to rank-one derived target and expects target payload [3,5]; source-control negative assigns scalar source to that interface.",
    },
    "S15.5.2.5-017": {
        "assumed-shape-same-rank-actual": "Pass rank-two actual shape [2,3] to rank-two assumed-shape dummy, initialize shape sentinels to [-1,-1], and expect [2,3]. Source-control negative changes only actual rank.",
    },
    "S15.5.2.5-020": {
        "sequence-association-element-order-association": "Use integer array a=[10,20,30,40,50] and pass actual array element a(3) to explicit-shape dummy d(3); expect d == [30,40,50], proving element-order sequence association starts at the actual element's position. Companion writes d(2)=99 and after return expects a(4)==99 while a(1:3) and a(5) remain [10,20,30,50]. Detailed sequence eligibility stays with 15.5.2.12.",
    },
    "S15.5.2.5-021": {
        "nonelemental-scalar-dummy-scalar-actual": "Positive plan passes scalar integer 73 to scalar dummy and expects 73; source-control negative passes rank-one array [73] to the same scalar dummy, with no required diagnostic claim.",
    },
    "S15.5.2.5-022": {
        "intent-out-actual-definable": "Positive plan passes variable v initialized to -1 to INTENT(OUT) dummy and assigns 89; after return expect v=89. Source-control negative passes expression v+1, with no required diagnostic claim.",
        "intent-inout-actual-definable": "Positive plan passes variable v initialized to 5 to INTENT(INOUT) dummy that adds 10; after return expect 15. Source-control negative passes constant 5, with no required diagnostic claim.",
    },
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def header(rule, facets):
    return f"! rule: {rule}\n! covers: {' '.join(facets)}\n! evidence: effect\n! standard: f2023\n"


CORE_SOURCE = dedent('''\
module ordinary_dummy_core_m
  implicit none
  integer, parameter :: k4 = selected_int_kind(4)
  type :: parent
    integer :: base = -1
  end type
  type, extends(parent) :: child
    integer :: ext = -2
  end type
  integer, pointer :: module_p => null(), module_q => null()
contains
  subroutine observe_scope(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine observe_class(x, out_base, out_ext)
    class(parent), intent(in) :: x
    integer, intent(out) :: out_base, out_ext
    select type (x)
    type is (child)
      out_base = x%base
      out_ext = x%ext
    class default
      out_base = x%base
      out_ext = -777
    end select
  end subroutine
  subroutine observe_poly_assumed_size(x, out_ext)
    class(parent), intent(in) :: x(*)
    integer, intent(out) :: out_ext
    select type (x)
    type is (child)
      out_ext = x(1)%ext
    class default
      out_ext = -778
    end select
  end subroutine
  subroutine observe_kind(x, out_kind, out_value)
    integer(kind=k4), intent(in) :: x
    integer, intent(out) :: out_kind, out_value
    out_kind = kind(x)
    out_value = int(x)
  end subroutine
  subroutine observe_char_scalar(x, out_len, out_text)
    character(len=3), intent(inout) :: x
    integer, intent(out) :: out_len
    character(len=3), intent(out) :: out_text
    out_len = len(x)
    out_text = x
    x = 'XYZ'
  end subroutine
  subroutine observe_char_array(x, seen)
    character(len=1), intent(inout) :: x(4)
    character(len=4), intent(out) :: seen
    seen = x(1) // x(2) // x(3) // x(4)
    x(3) = 'Q'
  end subroutine
  subroutine observe_assumed_char(x, out_len, out_last)
    character(len=*), intent(in) :: x
    integer, intent(out) :: out_len
    character(len=1), intent(out) :: out_last
    out_len = len(x)
    out_last = x(len(x):len(x))
  end subroutine
  subroutine read_allocated(x, out)
    integer, allocatable, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine observe_target(x, inside_assoc, inside_value)
    integer, target, intent(inout) :: x
    logical, intent(out) :: inside_assoc
    integer, intent(out) :: inside_value
    inside_assoc = associated(module_p, x)
    inside_value = x
    module_q => x
  end subroutine
  subroutine observe_scalar_rule(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
end module
program ordinary_dummy_core
  use ordinary_dummy_core_m
  implicit none
  integer :: checks = 0, out = -91, out_kind = -92, out_len = -93
  integer(kind=k4) :: kind_actual = 123_k4
  type(child) :: child_actual, poly_array(2)
  character(len=5) :: char_actual = 'ABCDE'
  character(len=3) :: char_text = '###'
  character(len=2) :: char_matrix(3) = ['AB', 'CD', 'EF']
  character(len=4) :: seq_seen = '####'
  character(len=7) :: long_char = 'ABCDEFG'
  character(len=1) :: last_char = '#'
  integer, allocatable :: allocated_value, not_allocated
  logical :: flag = .false.
  integer, target :: target_value = 79
  call observe_scope(31, out)
  call expect_equal(out, 31, 'ordinary dummy scope scalar')
  child_actual%base = 11; child_actual%ext = 13
  call observe_class(child_actual, out, out_kind)
  call expect_equal(out, 11, 'type compatible parent part')
  call expect_equal(out_kind, 13, 'type compatible extension part')
  poly_array(1)%base = 21; poly_array(1)%ext = 44
  call observe_poly_assumed_size(poly_array, out)
  call expect_equal(out, 44, 'polymorphic assumed-size actual')
  call observe_kind(kind_actual, out_kind, out)
  call expect_equal(out_kind, k4, 'kind parameter agreement kind')
  call expect_equal(out, 123, 'kind parameter agreement value')
  call observe_char_scalar(char_actual, out_len, char_text)
  call expect_equal(out_len, 3, 'scalar character dummy length')
  call expect_char3(char_text, 'ABC', 'default character length exception')
  call expect_char5(char_actual, 'XYZDE', 'scalar leftmost definition')
  call observe_char_array(char_matrix, seq_seen)
  call expect_char4(seq_seen, 'ABCD', 'array character leftmost sequence')
  call expect_char2(char_matrix(2), 'QD', 'array character definition')
  call observe_assumed_char(long_char, out_len, last_char)
  call expect_equal(out_len, 7, 'assumed character length')
  call expect_char1(last_char, 'G', 'assumed character last')
  allocate(allocated_value); allocated_value = 67
  call read_allocated(allocated_value, out)
  call expect_equal(out, 67, 'allocated allocatable actual')
  flag = .true.
  flag = allocated(not_allocated)
  call expect_false(flag, 'allocatable inquiry exception')
  module_p => target_value
  flag = .false.; out = -94
  call observe_target(target_value, flag, out)
  call expect_true(flag, 'target dummy invocation association')
  call expect_equal(out, 79, 'target dummy invocation value')
  call expect_true(associated(module_q, target_value), 'target dummy return association')
  call expect_equal(module_q, 79, 'target dummy return value')
  call observe_scalar_rule(73, out)
  call expect_equal(out, 73, 'nonelemental scalar dummy scalar actual')
  call expect_equal(checks, 20, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY CORE OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_true(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (.not. got) then
      write(*,'(a,1x,a)') 'OD15525-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(got, label)
    logical, intent(in) :: got
    character(len=*), intent(in) :: label
    if (got) then
      write(*,'(a,1x,a)') 'OD15525-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char1(got, want, label)
    character(len=1), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 1 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char2(got, want, label)
    character(len=2), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 2 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char3(got, want, label)
    character(len=3), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 3 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char4(got, want, label)
    character(len=4), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 4 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_char5(got, want, label)
    character(len=5), intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (len(got) /= 5 .or. got /= want) error stop label
    checks = checks + 1
  end subroutine
end program
''')

RANK_SOURCE = dedent('''\
module ordinary_dummy_rank_m
  implicit none
  type :: sink
    integer :: vals(2) = [-9, -8]
  end type
  interface generic_sum
    module procedure sum_rank_one
  end interface
  interface operator(.twice.)
    module procedure twice_rank_one
  end interface
  interface assignment(=)
    module procedure assign_rank_one
  end interface
contains
  subroutine scalar_only(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine assumed_rank_observe(x, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
    integer, intent(in) :: x(..)
    integer, intent(out) :: rank_seen, shape_seen(2), lower_seen(2), upper_seen(2), value_seen
    shape_seen = [-7, -8]
    lower_seen = [-9, -10]
    upper_seen = [-11, -12]
    value_seen = -13
    select rank (x)
    rank (0)
      rank_seen = 0
      value_seen = x
    rank (1)
      rank_seen = 1
      shape_seen = [size(x), -8]
      lower_seen = [lbound(x, 1), -10]
      upper_seen = [ubound(x, 1), -12]
      value_seen = x(1)
    rank (2)
      rank_seen = rank(x)
      shape_seen = shape(x)
      lower_seen = lbound(x)
      upper_seen = ubound(x)
      value_seen = x(2,2)
    rank default
      error stop 91
    end select
  end subroutine
  subroutine assumed_shape_observe(x, shape_seen, value_seen)
    integer, intent(in) :: x(:,:)
    integer, intent(out) :: shape_seen(2), value_seen
    shape_seen = shape(x)
    value_seen = x(2,3)
  end subroutine
  integer function sum_rank_one(x)
    integer, intent(in) :: x(:)
    sum_rank_one = sum(x)
  end function
  function twice_rank_one(x) result(out)
    integer, intent(in) :: x(:)
    integer :: out(size(x))
    out = 2*x
  end function
  subroutine assign_rank_one(lhs, rhs)
    type(sink), intent(out) :: lhs
    integer, intent(in) :: rhs(:)
    lhs%vals = rhs
  end subroutine
  subroutine array_order(x, before, after)
    integer, intent(inout) :: x(2,3)
    integer, intent(out) :: before, after
    before = x(2,2)
    x(2,2) = 144
    after = x(2,2)
  end subroutine
end module
program ordinary_dummy_rank
  use ordinary_dummy_rank_m
  implicit none
  integer :: checks = 0, out = -31, rank_seen = -32, value_seen = -33
  integer :: shape_seen(2) = [-1, -2], lower_seen(2) = [-3, -4], upper_seen(2) = [-5, -6]
  integer :: actual_rank2(2,3), shape_actual(2,3), bound_vec(4)
  integer :: order_actual(2,3), before = -34, after = -35
  type(sink) :: assigned
  call scalar_only(41, out)
  call expect_equal(out, 41, 'noncoindexed scalar actual scalar dummy')
  call assumed_rank_observe(53, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
  call expect_equal(rank_seen, 0, 'assumed-rank scalar exception rank')
  call expect_equal(value_seen, 53, 'assumed-rank accepts scalar value')
  actual_rank2 = reshape([1,2,3,4,5,6], [2,3])
  call assumed_rank_observe(actual_rank2, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
  call expect_equal(rank_seen, 2, 'assumed-rank array rank')
  call expect_vector2(shape_seen, [2,3], 'assumed-rank array extents')
  call expect_vector2(lower_seen, [1,1], 'assumed-rank array lower controls')
  call expect_equal(value_seen, 4, 'assumed-rank array value')
  bound_vec = [8,9,10,11]
  call assumed_rank_observe(bound_vec, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
  call expect_vector2(upper_seen, [4,-12], 'assumed-rank upper bound extent')
  shape_actual = reshape([7,8,9,10,11,12], [2,3])
  call assumed_shape_observe(shape_actual, shape_seen, value_seen)
  call expect_vector2(shape_seen, [2,3], 'assumed-shape same rank shape')
  call expect_equal(value_seen, 12, 'assumed-shape value')
  call expect_equal(generic_sum([2,4]), 6, 'generic nonelemental rank agreement')
  call expect_vector2(.twice. [6,8], [12,16], 'defined operator rank agreement')
  assigned = [3,5]
  call expect_vector2(assigned%vals, [3,5], 'defined assignment rank agreement')
  order_actual = reshape([11,22,33,44,55,66], [2,3])
  call array_order(order_actual, before, after)
  call expect_equal(before, 44, 'array element order entry')
  call expect_equal(after, 144, 'array element order dummy update')
  call expect_vector6(reshape(order_actual, [6]), [11,22,33,144,55,66], 'array element order caller update')
  call expect_equal(checks, 16, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY RANK OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_vector2(got, want, label)
    integer, intent(in) :: got(2), want(2)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
    checks = checks + 1
  end subroutine
  subroutine expect_vector6(got, want, label)
    integer, intent(in) :: got(6), want(6)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
    checks = checks + 1
  end subroutine
end program
''')

LOWER_SOURCE = dedent('''\
module ordinary_dummy_lower_m
  implicit none
contains
  subroutine observe_lower(x, lower_seen)
    integer, intent(in) :: x(..)
    integer, intent(out) :: lower_seen(2)
    select rank (x)
    rank (2)
      lower_seen = lbound(x)
    rank default
      error stop 91
    end select
  end subroutine
end module
program ordinary_dummy_lower
  use ordinary_dummy_lower_m
  implicit none
  integer :: checks = 0, i, j
  integer :: actual(-2:-1,4:6)
  integer :: lower_seen(2) = [-7, -8]
  do j = 4, 6
    do i = -2, -1
      actual(i,j) = 10*j + i
    end do
  end do
  call observe_lower(actual, lower_seen)
  call expect_vector2(lower_seen, [1,1], 'assumed-rank lower bound one')
  call expect_equal(checks, 1, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY LOWER OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_vector2(got, want, label)
    integer, intent(in) :: got(2), want(2)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
    checks = checks + 1
  end subroutine
end program
''')

INTENT_SOURCE = dedent('''\
module ordinary_dummy_intent_m
  implicit none
  type :: defaulted
    integer :: keep = 17
    integer :: fill
  end type
contains
  subroutine observe_defaulted_out(x, keep_seen)
    type(defaulted), intent(out) :: x
    integer, intent(out) :: keep_seen
    keep_seen = x%keep
    x%keep = 23
    x%fill = 45
  end subroutine
end module
program ordinary_dummy_intent
  use ordinary_dummy_intent_m
  implicit none
  integer :: checks = 0, keep_seen = -2
  type(defaulted) :: item
  item%keep = 101; item%fill = 102
  call observe_defaulted_out(item, keep_seen)
  call expect_equal(keep_seen, 17, 'intent out default component entry')
  call expect_equal(item%keep, 23, 'intent out default component return')
  call expect_equal(item%fill, 45, 'intent out fill component return')
  call expect_equal(checks, 3, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY INTENT OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
''')


def c1548_source(attribute, dummy_decl, completion):
    return dedent(f'''\
program c1548_{attribute.lower()}_control
  implicit none
  integer, {attribute.lower()} :: a(3) = [10, 20, 30]
  integer :: seen(2) = [-1, -2]
  call observe(a(3:1:-2), seen)
  call expect_vector2(seen, [30,10], '{attribute.lower()} nonpointer discontiguous values')
  write(*,'(a)') '{completion}'
contains
  subroutine observe(x, seen)
    {dummy_decl} :: x(:)
    integer, intent(out) :: seen(2)
    seen = x
  end subroutine
  subroutine expect_vector2(got, want, label)
    integer, intent(in) :: got(2), want(2)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
  end subroutine
end program
''')


def c1548_invalid_source(attribute, dummy_decl):
    return dedent(f'''\
program c1548_{attribute.lower()}_invalid
  implicit none
  integer, {attribute.lower()} :: a(3) = [10, 20, 30]
  call bad(a(3:1:-2))
contains
  subroutine bad(x)
    {dummy_decl} :: x(2)
    if (x(1) /= 30) error stop 1
  end subroutine
end program
''')


def c1548_contig_invalid_source():
    return dedent('''\
program c1548_contiguous_invalid
  implicit none
  integer, volatile :: a(3) = [10, 20, 30]
  call bad(a(3:1:-2))
contains
  subroutine bad(x)
    integer, volatile, contiguous :: x(:)
    if (x(1) /= 30) error stop 1
  end subroutine
end program
''')


def c1549_source(attribute, dummy_decl, completion):
    return dedent(f'''\
program c1549_{attribute.lower()}_control
  implicit none
  integer, target :: a(5) = [10, 20, 30, 40, 50]
  integer, pointer, {attribute.lower()} :: p(:)
  integer :: seen(3) = [-1, -2, -3]
  p => a(1:5:2)
  call observe(p, seen)
  call expect_vector3(seen, [10,30,50], '{attribute.lower()} pointer discontiguous values')
  write(*,'(a)') '{completion}'
contains
  subroutine observe(x, seen)
    {dummy_decl} :: x(:)
    integer, intent(out) :: seen(3)
    seen = x
  end subroutine
  subroutine expect_vector3(got, want, label)
    integer, intent(in) :: got(3), want(3)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
  end subroutine
end program
''')


def c1549_invalid_source(attribute, dummy_decl):
    return dedent(f'''\
program c1549_{attribute.lower()}_invalid
  implicit none
  integer, target :: a(5) = [10, 20, 30, 40, 50]
  integer, pointer, {attribute.lower()} :: p(:)
  p => a(1:5:2)
  call bad(p)
contains
  subroutine bad(x)
    {dummy_decl} :: x(3)
    if (x(1) /= 10) error stop 1
  end subroutine
end program
''')


def c1549_contig_invalid_source():
    return dedent('''\
program c1549_contiguous_invalid
  implicit none
  integer, target :: a(5) = [10, 20, 30, 40, 50]
  integer, pointer, volatile :: p(:)
  p => a(1:5:2)
  call bad(p)
contains
  subroutine bad(x)
    integer, volatile, contiguous :: x(:)
    if (x(1) /= 10) error stop 1
  end subroutine
end program
''')


def mut(mid, facet, replacements):
    return {"id": mid, "facet": facet, "kind": "feature", "replacements": replacements}


def make_case_specs():
    core_ok = "ORDINARY DUMMY CORE OK\n"
    rank_ok = "ORDINARY DUMMY RANK OK\n"
    lower_ok = "ORDINARY DUMMY LOWER OK\n"
    intent_ok = "ORDINARY DUMMY INTENT OK\n"
    c1548_async_ok = "C1548 ASYNC CONTROL OK\n"
    c1548_vol_ok = "C1548 VOLATILE CONTROL OK\n"
    c1548_contig_ok = "C1548 CONTIGUOUS CONTROL OK\n"
    c1549_async_ok = "C1549 ASYNC CONTROL OK\n"
    c1549_vol_ok = "C1549 VOLATILE CONTROL OK\n"
    c1549_contig_ok = "C1549 CONTIGUOUS CONTROL OK\n"
    cases = [
        ("ordinary_scope", "S15.5.2.5-001", CORE_SOURCE, core_ok, [mut("ordinary-scope-actual-changed", "ordinary-dummy-scope-source-use", [("call observe_scope(31, out)", "call observe_scope(32, out)")])], "valid"),
        ("scalar_character_length", "S15.5.2.5-004", CORE_SOURCE, core_ok, [mut("scalar-character-dummy-length-changed", "scalar-character-length-bound", [("character(len=3), intent(inout) :: x", "character(len=4), intent(inout) :: x")])], "valid"),
        ("scalar_character_leftmost", "S15.5.2.5-004", CORE_SOURCE, core_ok, [mut("scalar-character-definition-changed", "scalar-character-leftmost-association", [("x = 'XYZ'", "x = 'XYQ'")])], "valid"),
        ("array_character_leftmost", "S15.5.2.5-004", CORE_SOURCE, core_ok, [mut("array-character-sequence-source-changed", "array-character-leftmost-element-sequence-association", [("character(len=2) :: char_matrix(3) = ['AB', 'CD', 'EF']", "character(len=2) :: char_matrix(3) = ['AB', 'QD', 'EF']")])], "valid"),
        ("assumed_character", "S15.5.2.5-005", CORE_SOURCE, core_ok, [mut("assumed-character-length-changed", "assumed-character-length-from-effective-argument", [("character(len=7) :: long_char = 'ABCDEFG'", "character(len=6) :: long_char = 'ABCDEF'")])], "valid"),
        ("allocatable_inquiry", "S15.5.2.5-007", CORE_SOURCE, core_ok, [mut("allocatable-inquiry-replaced", "allocatable-inquiry-exception", [("flag = allocated(not_allocated)", "flag = .true.")])], "valid"),
        ("target_invocation", "S15.5.2.5-010", CORE_SOURCE, core_ok, [mut("target-invocation-pointer-nullified", "target-dummy-invocation-pointer-association", [("module_p => target_value", "nullify(module_p)")])], "valid"),
        ("target_return", "S15.5.2.5-010", CORE_SOURCE, core_ok, [mut("target-return-pointer-not-saved", "target-dummy-return-surviving-pointer-remains-associated", [("module_q => x", "nullify(module_q)")])], "valid"),
        ("assumed_rank_scalar_exception", "S15.5.2.5-015", RANK_SOURCE, rank_ok, [mut("scalar-exception-actual-made-rank-one", "assumed-rank-scalar-actual-exception", [("call assumed_rank_observe(53, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)", "call assumed_rank_observe([53], rank_seen, shape_seen, lower_seen, upper_seen, value_seen)")])], "valid"),
        ("assumed_rank_scalar", "S15.5.2.5-018", RANK_SOURCE, rank_ok, [mut("assumed-rank-scalar-actual-made-rank-one", "assumed-rank-accepts-scalar", [("call assumed_rank_observe(53, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)", "call assumed_rank_observe([53], rank_seen, shape_seen, lower_seen, upper_seen, value_seen)")])], "valid"),
        ("assumed_rank_array", "S15.5.2.5-018", RANK_SOURCE, rank_ok, [mut("assumed-rank-array-value-changed", "assumed-rank-accepts-array", [("actual_rank2 = reshape([1,2,3,4,5,6], [2,3])", "actual_rank2 = reshape([1,2,3,40,5,6], [2,3])")])], "valid"),
        ("assumed_rank_extents", "S15.5.2.5-019", RANK_SOURCE, rank_ok, [mut("assumed-rank-array-shape-changed", "assumed-rank-rank-and-extents", [("call assumed_rank_observe(actual_rank2, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)", "call assumed_rank_observe(actual_rank2(:,1:2), rank_seen, shape_seen, lower_seen, upper_seen, value_seen)")])], "valid"),
        ("assumed_rank_lower", "S15.5.2.5-019", LOWER_SOURCE, lower_ok, [mut("assumed-rank-dummy-replaced-by-assumed-shape-lower-zero", "assumed-rank-lower-bound-one", [("integer, intent(in) :: x(..)", "integer, intent(in) :: x(0:,0:)"), ("select rank (x)\n    rank (2)\n      lower_seen = lbound(x)\n    rank default\n      error stop 91\n    end select", "lower_seen = lbound(x)")])], "valid"),
        ("assumed_rank_upper", "S15.5.2.5-019", RANK_SOURCE, rank_ok, [mut("assumed-rank-vector-extent-changed", "assumed-rank-upper-bound-extent", [("integer :: actual_rank2(2,3), shape_actual(2,3), bound_vec(4)", "integer :: actual_rank2(2,3), shape_actual(2,3), bound_vec(5)"), ("bound_vec = [8,9,10,11]", "bound_vec = [8,9,10,11,12]")])], "valid"),
        ("array_element_order", "S15.5.2.5-020", RANK_SOURCE, rank_ok, [mut("array-element-order-update-moved", "array-actual-element-order-association", [("x(2,2) = 144", "x(1,2) = 144")])], "valid"),
        ("intent_out_default_component", "S15.5.2.5-023", INTENT_SOURCE, intent_ok, [mut("intent-out-default-initializer-changed", "intent-out-default-initialized-direct-component-exception", [("integer :: keep = 17", "integer :: keep = 18")])], "valid"),
    ]
    cases += [
        ("c1548_async_control", "C1548", c1548_source("ASYNCHRONOUS", "integer, asynchronous, intent(in)", c1548_async_ok.strip()), c1548_async_ok, [], "valid", ["nonpointer-async-discontiguous-dummy-shape-restriction"]),
        ("c1548_async_invalid", "C1548", c1548_invalid_source("ASYNCHRONOUS", "integer, asynchronous"), "", [], "invalid", ["nonpointer-async-discontiguous-dummy-shape-restriction"]),
        ("c1548_volatile_control", "C1548", c1548_source("VOLATILE", "integer, volatile", c1548_vol_ok.strip()), c1548_vol_ok, [], "valid", ["nonpointer-volatile-discontiguous-dummy-shape-restriction"]),
        ("c1548_volatile_invalid", "C1548", c1548_invalid_source("VOLATILE", "integer, volatile"), "", [], "invalid", ["nonpointer-volatile-discontiguous-dummy-shape-restriction"]),
        ("c1548_contiguous_control", "C1548", c1548_source("VOLATILE", "integer, volatile", c1548_contig_ok.strip()), c1548_contig_ok, [], "valid", ["nonpointer-discontiguous-dummy-no-contiguous"]),
        ("c1548_contiguous_invalid", "C1548", c1548_contig_invalid_source(), "", [], "invalid", ["nonpointer-discontiguous-dummy-no-contiguous"]),
        ("c1549_async_control", "C1549", c1549_source("ASYNCHRONOUS", "integer, asynchronous, intent(in)", c1549_async_ok.strip()), c1549_async_ok, [], "valid", ["array-pointer-async-noncontiguous-dummy-form-restriction"]),
        ("c1549_async_invalid", "C1549", c1549_invalid_source("ASYNCHRONOUS", "integer, asynchronous"), "", [], "invalid", ["array-pointer-async-noncontiguous-dummy-form-restriction"]),
        ("c1549_volatile_control", "C1549", c1549_source("VOLATILE", "integer, volatile", c1549_vol_ok.strip()), c1549_vol_ok, [], "valid", ["array-pointer-volatile-noncontiguous-dummy-form-restriction"]),
        ("c1549_volatile_invalid", "C1549", c1549_invalid_source("VOLATILE", "integer, volatile"), "", [], "invalid", ["array-pointer-volatile-noncontiguous-dummy-form-restriction"]),
        ("c1549_contiguous_control", "C1549", c1549_source("VOLATILE", "integer, volatile", c1549_contig_ok.strip()), c1549_contig_ok, [], "valid", ["array-pointer-noncontiguous-dummy-no-contiguous"]),
        ("c1549_contiguous_invalid", "C1549", c1549_contig_invalid_source(), "", [], "invalid", ["array-pointer-noncontiguous-dummy-no-contiguous"]),
    ]
    return cases


def identifier(rule, variant, kind):
    stem = rule.replace('.', '_').replace('-', '_')
    return f"{stem}_{'invalid' if kind == 'invalid' else 'valid'}__{TOPIC}_{variant}"


def diagnostic_line(source):
    for lineno, line in enumerate(source.splitlines(), 1):
        if "call bad(" in line:
            return lineno
    raise ValueError("invalid source has no call bad line")


def manifest(cid, rule, facets, kind, completion, source):
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
        line = diagnostic_line(source)
        base["expect"] = {"phase": "compile", "step": "source", "outcome": "diagnose", "diagnostic": {"file": "source.f90", "line": line, "end_line": line, "excludes_any": EXCLUDES}}
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
            count = changed.count(expected)
            if count != 1:
                raise ValueError(f"{mutation['id']} expected unique text {expected!r}, saw {count}")
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
    for entry in make_case_specs():
        if len(entry) == 6:
            variant, rule, body, completion, muts, kind = entry
            facets = [m["facet"] for m in muts] if kind == "valid" else FACETS_BY_RULE[rule]
        else:
            variant, rule, body, completion, muts, kind, facets = entry
        cid = identifier(rule, variant, kind)
        source = header(rule, facets) + body
        directory = root / "tests" / "fixtures" / (PREFIX + variant)
        spec = {
            "id": cid,
            "variant": variant,
            "rule": rule,
            "kind": kind,
            "facets": list(facets),
            "source": source,
            "source_sha256": sha(source.encode("ascii")),
            "completion": completion,
            "manifest": manifest(cid, rule, facets, kind, completion, source),
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


def without_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    return "\n\n".join(p for p in paragraphs if not p.startswith(prefix))


def synced_catalogue(section, catalogue, specs):
    updated = copy.deepcopy(catalogue)
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for req in updated["requirements"]:
        rule = req["id"]
        for facet, reason in RESTORE_PENDING.get(rule, {}).items():
            req.setdefault("pending", {}).setdefault(facet, reason)
        if rule not in covered:
            req["oracle"] = without_owned_paragraph(
                req.get("oracle", ""), f"{rule} ordinary_dummies_15_5_2_5 fixtures: "
            )
            req["oracle_limitation"] = without_owned_paragraph(
                req.get("oracle_limitation", ""), f"{rule} ordinary_dummies_15_5_2_5 boundaries: "
            )
            continue
        pending = req.setdefault("pending", {})
        for facet in covered[rule]:
            pending.pop(facet, None)
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
    summary = SUMMARY_BEGIN + "\n## Ordinary dummy 15.5.2.5 fixtures\n\nBatch324 adds f2023 fixtures for ordinary nonallocatable nonpointer dummy association, character length and sequence effects, assumed-rank properties, TARGET pointer association, INTENT(OUT) default-initialized components, and C1548/C1549 diagnostic controls. Coarray, undefined-status, PDT, assumed-type exclusion, nonportable processor-dependent, and unnumbered no-diagnostic facets remain pending.\n" + SUMMARY_END
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
            raise SystemExit("stale ordinary_dummies_15_5_2_5 files: " + ", ".join(stale))
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
    env["TMPDIR"] = str((ROOT / ".ordinary_dummies_15_5_2_5_tmp").resolve())
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
    scratch = root / ".ordinary_dummies_15_5_2_5_mutation_work"
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
            shutil.rmtree(root / ".ordinary_dummies_15_5_2_5_tmp", ignore_errors=True)
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
    unique_facets = {(s["rule"], f) for s in specs.values() for f in s["facets"]}
    print(f"{'checked' if args.check else 'generated'} {len(specs)} {TOPIC} fixtures, {len(unique_facets)} unique facets")


if __name__ == "__main__":
    main()
