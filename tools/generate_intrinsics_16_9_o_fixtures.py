#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.114-16.9.119 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_o"
SECTIONS = ("16.9.114", "16.9.115", "16.9.116", "16.9.117", "16.9.118", "16.9.119")
CATALOGUES = {
    "16.9.114": "doc/catalogues/ishftc_16_9_114.json",
    "16.9.115": "doc/catalogues/is_contiguous_16_9_115.json",
    "16.9.116": "doc/catalogues/is_iostat_end_16_9_116.json",
    "16.9.117": "doc/catalogues/is_iostat_eor_16_9_117.json",
    "16.9.118": "doc/catalogues/kind_intrinsic_16_9_118.json",
    "16.9.119": "doc/catalogues/lbound_16_9_119.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.O FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.O FIXTURES -->"
KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "is_contiguous_assumed_rank",
        "is_contiguous_rank_zero",
        "lbound_assumed_rank_argument",
    }
}

RESTORED_PENDING = {
    "S16.9.115-002": {
        "IS_CONTIGUOUS-pointer-ARRAY-associated": (
            "PENDING after batch301 review: this is an unnumbered pointer association restriction; "
            "a positive associated-pointer control does not discharge the forbidden disassociated-pointer case, "
            "and no diagnostic is required."
        ),
    },
    "S16.9.119-001": {
        "LBOUND-ARRAY-allocated-or-associated": (
            "PENDING after batch301 review: this is an unnumbered shall-not restriction forbidding "
            "unallocated allocatable and disassociated pointer ARRAY arguments; positive allocated/associated "
            "controls do not discharge the forbidden cases, and no diagnostic is required."
        ),
        "LBOUND-DIM-corresponding-actual-present-associated-allocated": (
            "PENDING after batch301 review: this is an unnumbered shall-not restriction forbidding absent, "
            "disassociated, or unallocated DIM corresponding actual arguments; positive present/associated/allocated "
            "controls do not discharge the forbidden cases, and no diagnostic is required."
        ),
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace(".", "_").replace("-", "_") + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Mutation:
    id: str
    facet: str
    expected: str
    replacement: str


@dataclass(frozen=True)
class Case:
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[Mutation, ...]
    oracle: str
    profiles: tuple[str, ...] = ()

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.O " + self.variant.upper().replace("_", " ") + " OK\n"


REQUIRE_HELPERS = """contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
"""


def program(name: str, declarations: str, body: str, completion: str, use_lines: str = "", helpers: str = "") -> str:
    return f"""program i169o_{name}
{use_lines}  implicit none
{declarations}{body}  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}{helpers}end program i169o_{name}
"""


def ishftc_argument_controls_source(completion):
    return program("ishftc_argument_controls", """  integer :: i_value
  integer :: shift_value
  integer :: size_value
  integer :: full_size
  integer :: absent_result
  integer :: explicit_result
""", """  i_value = ibset(ibset(0, 0), 1)
  call require_true('ishftc integer i argument controls bit result', &
      btest(ishftc(i_value, 1, 4), 1) .and. btest(ishftc(i_value, 1, 4), 2))
  shift_value = 1
  call require_true('ishftc integer shift argument controls direction', &
      btest(ishftc(1, shift_value, 4), 1) .and. .not. btest(ishftc(1, shift_value, 4), 3))
  call require_true('ishftc shift magnitude may equal size', btest(ishftc(1, 4, 4), 0))
  size_value = 4
  call require_true('ishftc positive size controls wrap point', btest(ishftc(8, 1, size_value), 0))
  full_size = bit_size(i_value)
  absent_result = ishftc(ibset(0, full_size - 1), 1)
  explicit_result = ishftc(ibset(0, full_size - 1), 1, full_size)
  call require_true('ishftc absent size acts as bit_size', same_bits(absent_result, explicit_result))
""", completion, helpers="""  logical function same_bits(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    integer :: pos
    same_bits = .true.
    do pos = 0, bit_size(lhs) - 1
      same_bits = same_bits .and. (btest(lhs, pos) .eqv. btest(rhs, pos))
    end do
  end function same_bits
""")


def ishftc_characteristics_source(completion):
    return program("ishftc_characteristics", """  integer, parameter :: wide_k = selected_int_kind(18)
  integer(kind=wide_k) :: wide_value
""", """  wide_value = 3_wide_k
  call require_true('ishftc result kind is same as i expression', &
      kind(ishftc(wide_value, 1, 3)) == wide_k)
""", completion)


def ishftc_bit_results_source(completion):
    return program("ishftc_bit_results", """  integer :: positive_value
  integer :: negative_value
  integer :: zero_value
  integer :: wrap_value
  integer :: outside_value
""", """  positive_value = ibset(ibset(0, 0), 1)
  call require_true('ishftc positive shift moves bits left', &
      btest(ishftc(positive_value, 1, 4), 1) .and. btest(ishftc(positive_value, 1, 4), 2) .and. &
      .not. btest(ishftc(positive_value, 1, 4), 3))
  negative_value = ibset(ibset(0, 0), 1)
  call require_true('ishftc negative shift moves bits right', &
      btest(ishftc(negative_value, -1, 4), 0) .and. btest(ishftc(negative_value, -1, 4), 3) .and. &
      .not. btest(ishftc(negative_value, -1, 4), 2))
  zero_value = ibset(ibset(ibset(ibset(0, 0), 2), 4), 6)
  call require_true('ishftc zero shift preserves selected bits', &
      same_bits(ishftc(zero_value, 0, 5), zero_value))
  wrap_value = ibset(0, 3)
  call require_true('ishftc loses no rightmost field bits', btest(ishftc(wrap_value, 1, 4), 0))
  outside_value = ibset(ibset(0, 5), 8)
  call require_true('ishftc leaves outside field bits unaltered', &
      btest(ishftc(outside_value, 1, 4), 5) .and. btest(ishftc(outside_value, 1, 4), 8))
""", completion, helpers="""  logical function same_bits(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    integer :: pos
    same_bits = .true.
    do pos = 0, bit_size(lhs) - 1
      same_bits = same_bits .and. (btest(lhs, pos) .eqv. btest(rhs, pos))
    end do
  end function same_bits
""")


def is_contiguous_types_source(completion):
    return program("is_contiguous_types", """  type :: sample_type
    integer :: n
  end type sample_type
  integer :: ints(6) = [11, 12, 13, 14, 15, 16]
  real :: reals(2) = [1.0, 2.0]
  complex :: complexes(2) = [(1.0, 2.0), (3.0, 4.0)]
  logical :: logicals(2) = [.true., .false.]
  character(len=3) :: chars(2) = ['abc', 'def']
  type(sample_type) :: deriveds(2) = [sample_type(1), sample_type(2)]
""", """  call require_true('is_contiguous accepts whole arrays of every intrinsic and derived type', &
      is_contiguous(ints) .and. is_contiguous(reals) .and. is_contiguous(complexes) .and. &
      is_contiguous(logicals) .and. is_contiguous(chars) .and. is_contiguous(deriveds))
""", completion)


def is_contiguous_assumed_rank_source(completion):
    return program("is_contiguous_assumed_rank", """  integer, target :: whole(6) = [1, 2, 3, 4, 5, 6]
  integer, pointer :: strided(:)
""", """  strided => whole(1:6:2)
  call require_true('is_contiguous direct array argument admitted', is_contiguous(whole))
  call require_true('is_contiguous assumed-rank scalar rank-zero true', assumed_rank_contiguous(17))
""", completion, helpers="""  logical function assumed_rank_contiguous(x)
    integer, intent(in) :: x(..)
    assumed_rank_contiguous = is_contiguous(x)
  end function assumed_rank_contiguous
""")


def is_contiguous_values_source(completion):
    return program("is_contiguous_values", """  integer, target :: target(10) = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  integer, pointer :: contiguous_pointer(:)
  integer, pointer :: strided_pointer(:)
""", """  contiguous_pointer => target
  strided_pointer => target(1:10:2)
  call require_true('is_contiguous associated pointer argument true for whole target', &
      associated(contiguous_pointer) .and. is_contiguous(contiguous_pointer))
  call require_true('is_contiguous result default logical scalar', &
      kind(is_contiguous(target)) == kind(.false.) .and. rank(is_contiguous(target)) == 0)
  call require_true('is_contiguous whole nonpointer array is true', is_contiguous(target))
  call require_false('is_contiguous strided pointer section is false', is_contiguous(strided_pointer))
""", completion)


def iostat_end_source(completion):
    return program("is_iostat_end_actual", """  integer :: end_status
  integer :: ok_status
  integer :: observed_status
  logical :: observed_logical
""", """  call eof_status(end_status)
  call ok_read_status(ok_status)
  observed_status = end_status
  observed_logical = is_iostat_end(end_status)
  call require_true('is_iostat_end accepts integer i from iostat', is_iostat_end(observed_status))
  call require_true('is_iostat_end result default logical scalar', &
      observed_logical .and. kind(is_iostat_end(end_status)) == kind(.false.))
  call require_true('is_iostat_end true for actual end condition', is_iostat_end(end_status))
  call require_true('successful guarded read gives zero iostat', ok_status == 0)
  call require_false('is_iostat_end false for zero non-end status', is_iostat_end(ok_status))
""", completion, helpers="""  subroutine eof_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: value
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,*) 12345
    rewind(unit)
    value = -777
    if (value /= -777) error stop
    read(unit,*,iostat=stat) value
    if (stat /= 0 .or. value /= 12345) error stop
    value = -777
    if (value /= -777) error stop
    read(unit,*,iostat=stat) value
    call require_true('end read leaves sentinel target unchanged', value == -777)
    close(unit)
  end subroutine eof_status
  subroutine ok_read_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: value
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,*) 24680
    rewind(unit)
    value = -777
    if (value /= -777) error stop
    read(unit,*,iostat=stat) value
    call require_true('successful read defines sentinel target', value == 24680)
    close(unit)
  end subroutine ok_read_status
""")


def iostat_eor_source(completion):
    return program("is_iostat_eor_actual", """  integer :: eor_status
  integer :: ok_status
  integer :: observed_status
  logical :: observed_logical
""", """  call eor_read_status(eor_status)
  call ok_nonadvance_status(ok_status)
  observed_status = eor_status
  observed_logical = is_iostat_eor(eor_status)
  call require_true('is_iostat_eor accepts integer i from iostat', is_iostat_eor(observed_status))
  call require_true('is_iostat_eor result default logical scalar', &
      observed_logical .and. kind(is_iostat_eor(eor_status)) == kind(.false.))
  call require_true('is_iostat_eor true for actual end of record condition', is_iostat_eor(eor_status))
  call require_true('initial nonadvancing read gives zero iostat', ok_status == 0)
  call require_false('is_iostat_eor false for zero non-eor status', is_iostat_eor(ok_status))
""", completion, helpers="""  subroutine eor_read_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: amount
    character(len=3) :: chunk
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,'(a)') 'ABCDE'
    rewind(unit)
    chunk = '###'
    if (chunk /= '###') error stop
    read(unit,'(a)',advance='no',iostat=stat,size=amount) chunk
    call require_true('first nonadvancing read fills target', stat == 0 .and. chunk == 'ABC' .and. amount == 3)
    chunk = '###'
    if (chunk /= '###') error stop
    read(unit,'(a)',advance='no',iostat=stat,size=amount) chunk
    call require_true('eor read reports available characters', chunk(1:2) == 'DE' .and. amount == 2)
    close(unit)
  end subroutine eor_read_status
  subroutine ok_nonadvance_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: amount
    character(len=3) :: chunk
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,'(a)') 'ABCDE'
    rewind(unit)
    chunk = '###'
    if (chunk /= '###') error stop
    read(unit,'(a)',advance='no',iostat=stat,size=amount) chunk
    call require_true('nonadvancing zero-status read defines sentinel target', chunk == 'ABC' .and. amount == 3)
    close(unit)
  end subroutine ok_nonadvance_status
""")


def kind_forms_source(completion):
    return program("kind_forms", """  integer :: ints(-1:1) = [7, 8, 9]
  real :: real_value = 1.25
  complex :: complex_value = (2.0, -3.0)
  logical :: logical_value = .true.
  character(len=4) :: char_value = 'WXYZ'
""", """  call require_true('kind admits all intrinsic type arguments', &
      kind(17) == kind(ints(0)) .and. kind(real_value) == kind(1.0) .and. &
      kind(complex_value) == kind((1.0, 0.0)) .and. kind(logical_value) == kind(.true.) .and. &
      kind(char_value) == kind('A'))
  call require_true('kind admits scalar and array arguments', &
      kind(ints) == kind(ints(0)) .and. kind(17) == kind(ints(0)))
  call require_true('kind result default integer scalar', &
      kind(kind(char_value)) == kind(0) .and. rank(kind(ints)) == 0)
""", completion)


def kind_values_source(completion):
    return program("kind_values", """  integer, parameter :: wide_int_k = selected_int_kind(18)
  integer(kind=wide_int_k) :: wide_integer = 123_wide_int_k
  real(kind=kind(0.0d0)) :: double_real = 1.5d0
  complex(kind=kind(0.0d0)) :: double_complex = (2.0d0, -3.0d0)
  logical :: logical_value = .true.
  character(len=5) :: char_value = 'HELLO'
""", """  call require_true('kind returns integer kind parameter', kind(wide_integer) == wide_int_k)
  call require_true('kind returns real kind parameter', kind(double_real) == kind(0.0d0))
  call require_true('kind returns complex kind parameter', kind(double_complex) == kind((0.0d0, 0.0d0)))
  call require_true('kind returns logical kind parameter', logical_value .and. kind(logical_value) == kind(.true.))
  call require_true('kind returns character kind parameter independent of length', &
      len(char_value) == 5 .and. kind(char_value) == kind('A'))
""", completion)


def lbound_assumed_rank_source(completion):
    return program("lbound_assumed_rank_argument", """  integer :: explicit_array(2:4) = [21, 22, 23]
""", """  call require_true('lbound accepts ordinary array argument', lbound(explicit_array, dim=1) == 2)
  call check_assumed_rank(explicit_array)
""", completion, helpers="""  subroutine check_assumed_rank(x)
    integer, intent(in) :: x(..)
    call require_true('lbound accepts assumed-rank rank-one argument', &
        rank(x) == 1 .and. size(lbound(x)) == 1 .and. lbound(x, dim=1) == 1)
  end subroutine check_assumed_rank
""")


def lbound_argument_controls_source(completion):
    return program("lbound_argument_controls", """  integer, parameter :: wide_k = selected_int_kind(18)
  integer, allocatable :: alloc_array(:)
  integer, target :: target_array(-4:-2) = [41, 42, 43]
  integer, pointer :: pointer_array(:)
  integer :: rank_two(-3:4, 7:9)
  integer, target :: dim_target = 2
  integer :: plain_dim = 2
  integer, pointer :: dim_pointer
  integer, allocatable :: dim_alloc
""", """  allocate(alloc_array(-2:2))
  pointer_array => target_array
  call require_true('lbound requires allocated or associated array arguments positively', &
      lbound(alloc_array, dim=1) == -2 .and. lbound(pointer_array, dim=1) == -4)
  call require_true('lbound dim is integer scalar in rank range', &
      lbound(rank_two, dim=1) == -3 .and. lbound(rank_two, dim=2) == 7)
  dim_pointer => dim_target
  allocate(dim_alloc)
  dim_alloc = 1
  call require_true('lbound dim corresponding actual present associated allocated', &
      plain_dim_result(rank_two, plain_dim) == 7 .and. pointer_dim_result(rank_two, dim_pointer) == 7 .and. &
      alloc_dim_result(rank_two, dim_alloc) == -3)
  call require_true('lbound kind is scalar integer constant expression', &
      kind(lbound(rank_two, kind=wide_k)) == wide_k)
""", completion, helpers="""  integer function plain_dim_result(array, dim)
    integer, intent(in) :: array(-3:, 7:)
    integer, intent(in) :: dim
    plain_dim_result = lbound(array, dim=dim)
  end function plain_dim_result
  integer function pointer_dim_result(array, dim)
    integer, intent(in) :: array(-3:, 7:)
    integer, pointer, intent(in) :: dim
    pointer_dim_result = lbound(array, dim=dim)
  end function pointer_dim_result
  integer function alloc_dim_result(array, dim)
    integer, intent(in) :: array(-3:, 7:)
    integer, allocatable, intent(in) :: dim
    alloc_dim_result = lbound(array, dim=dim)
  end function alloc_dim_result
""")


def lbound_characteristics_source(completion):
    return program("lbound_characteristics", """  integer, parameter :: wide_k = selected_int_kind(18)
  integer :: a(-3:4, 7:9)
""", """  call require_true('lbound result integer kind default or kind argument', &
      kind(lbound(a)) == kind(0) .and. kind(lbound(a, kind=wide_k)) == wide_k)
  call require_true('lbound result scalar when dim present', &
      rank(lbound(a, dim=2)) == 0 .and. lbound(a, dim=2) == 7)
  call require_true('lbound result rank one size rank when dim absent', &
      rank(lbound(a)) == 1 .and. size(lbound(a)) == rank(a) .and. lbound(lbound(a), dim=1) == 1)
""", completion)


def lbound_dim_values_source(completion):
    return program("lbound_dim_values", """  integer :: whole(-3:4, 7:9)
  integer :: zero_extent(5:4)
""", """  call require_true('lbound dim whole nonzero extent returns declared lower bounds', &
      lbound(whole, dim=1) == -3 .and. lbound(whole, dim=2) == 7)
  call check_assumed_size(whole)
  call require_true('lbound dim otherwise returns one for section and zero extent', &
      lbound(whole(-3:4:2, 7:9), dim=1) == 1 .and. lbound(zero_extent, dim=1) == 1)
""", completion, helpers="""  subroutine check_assumed_size(dummy)
    integer, intent(in) :: dummy(2:*)
    call require_true('lbound assumed-size rank dim lower bound', lbound(dummy, dim=1) == 2)
  end subroutine check_assumed_size
""")


def lbound_vector_values_source(completion):
    return program("lbound_vector_values", """  integer, parameter :: wide_k = selected_int_kind(18)
  integer :: a(-3:4, 7:9, 0:2)
""", """  call require_true('lbound vector elements match dim inquiries', &
      size(lbound(a)) == 3 .and. all(lbound(a) == [lbound(a, dim=1), lbound(a, dim=2), lbound(a, dim=3)]))
  call require_true('lbound vector kind elements match selected kind inquiries', &
      kind(lbound(a, kind=wide_k)) == wide_k .and. &
      all(lbound(a, kind=wide_k) == [lbound(a, dim=1, kind=wide_k), lbound(a, dim=2, kind=wide_k), &
                                     lbound(a, dim=3, kind=wide_k)]))
  call check_assumed_shape(a)
""", completion, helpers="""  subroutine check_assumed_shape(dummy)
    integer, intent(in) :: dummy(5:, :, 0:)
    call require_true('lbound assumed-shape uses dummy lower bounds', &
        all(lbound(dummy) == [5, 1, 0]) .and. lbound(dummy, dim=1) == 5 .and. &
        lbound(dummy, dim=2) == 1 .and. lbound(dummy, dim=3) == 0)
  end subroutine check_assumed_shape
""")


def make_cases():
    raw = []

    def add(variant, rule, facets, evidence, source_func, mutations, oracle, profiles=()):
        completion = "INTRINSICS 16.9.O " + variant.upper().replace("_", " ") + " OK\n"
        raw.append(Case(variant, rule, tuple(facets), evidence, source_func(completion), tuple(mutations), oracle, tuple(profiles)))

    add("ishftc_argument_controls", "S16.9.114-001", [
        "ISHFTC-I-integer", "ISHFTC-SHIFT-integer", "ISHFTC-SHIFT-magnitude-not-greater-than-SIZE",
        "ISHFTC-SIZE-positive-integer-not-greater-than-bit-size", "ISHFTC-absent-SIZE-defaults-to-bit-size"],
        "positive-control", ishftc_argument_controls_source, [
            Mutation("i-argument-bits-changed", "ISHFTC-I-integer", "i_value = ibset(ibset(0, 0), 1)", "i_value = ibset(0, 0)"),
            Mutation("shift-value-changed", "ISHFTC-SHIFT-integer", "shift_value = 1", "shift_value = -1"),
            Mutation("boundary-shift-not-size", "ISHFTC-SHIFT-magnitude-not-greater-than-SIZE", "ishftc(1, 4, 4)", "ishftc(1, 3, 4)"),
            Mutation("size-wrap-point-changed", "ISHFTC-SIZE-positive-integer-not-greater-than-bit-size", "size_value = 4", "size_value = 5"),
            Mutation("absent-size-explicit-short", "ISHFTC-absent-SIZE-defaults-to-bit-size", "explicit_result = ishftc(ibset(0, full_size - 1), 1, full_size)", "explicit_result = ishftc(ibset(0, full_size - 1), 1, full_size - 1)"),
        ], "ISHFTC argument fixture uses integer I/SHIFT/SIZE controls, boundary SHIFT=SIZE, SIZE wrap points, and absent SIZE equivalence to BIT_SIZE(I).")
    add("ishftc_characteristics", "S16.9.114-002", ["ISHFTC-result-same-integer-kind-as-I"],
        "effect", ishftc_characteristics_source, [
            Mutation("result-kind-demoted", "ISHFTC-result-same-integer-kind-as-I", "kind(ishftc(wide_value, 1, 3)) == wide_k", "kind(ishftc(int(wide_value), 1, 3)) == wide_k"),
        ], "ISHFTC result-characteristics fixture inquires KIND directly on ISHFTC(wide_value,1,3).")
    add("ishftc_bit_results", "S16.9.114-003", [
        "ISHFTC-positive-left-circular-shift", "ISHFTC-negative-right-circular-shift", "ISHFTC-zero-shift-preserves-bits",
        "ISHFTC-no-bits-lost-in-rightmost-field", "ISHFTC-unshifted-bits-unaltered"],
        "effect", ishftc_bit_results_source, [
            Mutation("positive-shift-direction-reversed", "ISHFTC-positive-left-circular-shift", "btest(ishftc(positive_value, 1, 4), 1) .and. btest(ishftc(positive_value, 1, 4), 2) .and. &\n      .not. btest(ishftc(positive_value, 1, 4), 3)", "btest(ishftc(positive_value, -1, 4), 1) .and. btest(ishftc(positive_value, -1, 4), 2) .and. &\n      .not. btest(ishftc(positive_value, -1, 4), 3)"),
            Mutation("negative-shift-direction-reversed", "ISHFTC-negative-right-circular-shift", "btest(ishftc(negative_value, -1, 4), 0) .and. btest(ishftc(negative_value, -1, 4), 3) .and. &\n      .not. btest(ishftc(negative_value, -1, 4), 2)", "btest(ishftc(negative_value, 1, 4), 0) .and. btest(ishftc(negative_value, 1, 4), 3) .and. &\n      .not. btest(ishftc(negative_value, 1, 4), 2)"),
            Mutation("zero-shift-changed", "ISHFTC-zero-shift-preserves-bits", "ishftc(zero_value, 0, 5)", "ishftc(zero_value, 1, 5)"),
            Mutation("wrap-size-changed", "ISHFTC-no-bits-lost-in-rightmost-field", "ishftc(wrap_value, 1, 4)", "ishftc(wrap_value, 1, 5)"),
            Mutation("outside-field-included", "ISHFTC-unshifted-bits-unaltered", "btest(ishftc(outside_value, 1, 4), 5) .and. btest(ishftc(outside_value, 1, 4), 8)", "btest(ishftc(outside_value, 1, 6), 5) .and. btest(ishftc(outside_value, 1, 6), 8)"),
        ], "ISHFTC bit-result fixture observes required circular left, right, zero, wrap, and outside-field bits with BTEST.")

    add("is_contiguous_types", "S16.9.115-001", ["IS_CONTIGUOUS-ARRAY-any-type-admitted"],
        "effect", is_contiguous_types_source, [
            Mutation("one-type-made-noncontiguous", "IS_CONTIGUOUS-ARRAY-any-type-admitted", "is_contiguous(deriveds)", "is_contiguous(ints(1:6:2))"),
        ], "IS_CONTIGUOUS type-admission fixture calls the intrinsic on whole arrays of integer, real, complex, logical, character, and derived type.")
    add("is_contiguous_assumed_rank", "S16.9.115-002", ["IS_CONTIGUOUS-ARRAY-assumed-rank-or-array"],
        "positive-control", is_contiguous_assumed_rank_source, [
            Mutation("direct-array-replaced-by-stride", "IS_CONTIGUOUS-ARRAY-assumed-rank-or-array", "is_contiguous(whole)", "is_contiguous(strided)"),
        ], "IS_CONTIGUOUS argument-form fixture uses a direct rank-one array and an assumed-rank scalar dummy.")
    add("is_contiguous_rank_zero", "S16.9.115-004", ["IS_CONTIGUOUS-rank-zero-true"],
        "effect", is_contiguous_assumed_rank_source, [
            Mutation("rank-zero-actual-replaced", "IS_CONTIGUOUS-rank-zero-true", "assumed_rank_contiguous(17)", "assumed_rank_contiguous(strided)"),
        ], "IS_CONTIGUOUS rank-zero fixture passes a scalar actual to an assumed-rank dummy and observes the required true result.")
    add("is_contiguous_characteristics", "S16.9.115-003", ["IS_CONTIGUOUS-result-default-logical-scalar"],
        "effect", is_contiguous_values_source, [
            Mutation("scalar-result-wrapped", "IS_CONTIGUOUS-result-default-logical-scalar", "rank(is_contiguous(target)) == 0", "rank([is_contiguous(target)]) == 0"),
        ], "IS_CONTIGUOUS result-characteristics fixture inquires KIND and RANK directly on IS_CONTIGUOUS(target).")
    add("is_contiguous_truth_values", "S16.9.115-004", ["IS_CONTIGUOUS-contiguous-array-true", "IS_CONTIGUOUS-noncontiguous-array-false"],
        "effect", is_contiguous_values_source, [
            Mutation("whole-array-made-strided", "IS_CONTIGUOUS-contiguous-array-true", "call require_true('is_contiguous whole nonpointer array is true', is_contiguous(target))", "call require_true('is_contiguous whole nonpointer array is true', is_contiguous(strided_pointer))"),
            Mutation("strided-pointer-made-whole", "IS_CONTIGUOUS-noncontiguous-array-false", "strided_pointer => target(1:10:2)", "strided_pointer => target"),
        ], "IS_CONTIGUOUS truth-value fixture observes true for a whole array and false for a pointer to a strided section required noncontiguous by 8.5.7.")

    add("is_iostat_end_actual", "S16.9.116-001", ["IS_IOSTAT_END-I-integer"],
        "positive-control", iostat_end_source, [
            Mutation("integer-status-changed-to-zero", "IS_IOSTAT_END-I-integer", "observed_status = end_status", "observed_status = 0"),
        ], "IS_IOSTAT_END argument fixture passes an integer IOSTAT value produced by a guarded READ at EOF.")
    add("is_iostat_end_characteristics", "S16.9.116-002", ["IS_IOSTAT_END-result-default-logical"],
        "effect", iostat_end_source, [
            Mutation("end-result-status-changed", "IS_IOSTAT_END-result-default-logical", "observed_logical = is_iostat_end(end_status)", "observed_logical = is_iostat_end(ok_status)"),
        ], "IS_IOSTAT_END characteristics fixture inquires KIND and RANK directly on IS_IOSTAT_END(end_status).")
    add("is_iostat_end_values", "S16.9.116-003", ["IS_IOSTAT_END-true-for-end-of-file-status", "IS_IOSTAT_END-false-for-non-end-of-file-status"],
        "effect", iostat_end_source, [
            Mutation("end-condition-made-successful", "IS_IOSTAT_END-true-for-end-of-file-status", "call eof_status(end_status)", "call ok_read_status(end_status)"),
            Mutation("zero-status-made-eof", "IS_IOSTAT_END-false-for-non-end-of-file-status", "call ok_read_status(ok_status)", "call eof_status(ok_status)"),
        ], "IS_IOSTAT_END value fixture uses actual successful and end-of-file READ IOSTAT values; only zero/nonzero and the predicate are asserted.")

    add("is_iostat_eor_actual", "S16.9.117-001", ["IS_IOSTAT_EOR-I-integer"],
        "positive-control", iostat_eor_source, [
            Mutation("integer-eor-status-changed-to-zero", "IS_IOSTAT_EOR-I-integer", "observed_status = eor_status", "observed_status = 0"),
        ], "IS_IOSTAT_EOR argument fixture passes an integer IOSTAT value produced by a guarded nonadvancing READ at EOR.")
    add("is_iostat_eor_characteristics", "S16.9.117-002", ["IS_IOSTAT_EOR-result-default-logical"],
        "effect", iostat_eor_source, [
            Mutation("eor-result-status-changed", "IS_IOSTAT_EOR-result-default-logical", "observed_logical = is_iostat_eor(eor_status)", "observed_logical = is_iostat_eor(ok_status)"),
        ], "IS_IOSTAT_EOR characteristics fixture inquires KIND and RANK directly on IS_IOSTAT_EOR(eor_status).")
    add("is_iostat_eor_values", "S16.9.117-003", ["IS_IOSTAT_EOR-true-for-end-of-record-status", "IS_IOSTAT_EOR-false-for-non-end-of-record-status"],
        "effect", iostat_eor_source, [
            Mutation("eor-condition-made-successful", "IS_IOSTAT_EOR-true-for-end-of-record-status", "call eor_read_status(eor_status)", "call ok_nonadvance_status(eor_status)"),
            Mutation("zero-status-made-eor", "IS_IOSTAT_EOR-false-for-non-end-of-record-status", "call ok_nonadvance_status(ok_status)", "call eor_read_status(ok_status)"),
        ], "IS_IOSTAT_EOR value fixture uses actual successful and end-of-record nonadvancing READ IOSTAT values; only zero/nonzero and the predicate are asserted.")

    add("kind_forms", "S16.9.118-001", ["KIND-X-any-intrinsic-type", "KIND-X-scalar-or-array"],
        "positive-control", kind_forms_source, [
            Mutation("character-kind-expected-wrong", "KIND-X-any-intrinsic-type", "kind(char_value) == kind('A')", "kind(char_value) == len(char_value)"),
            Mutation("array-argument-replaced", "KIND-X-scalar-or-array", "kind(ints) == kind(ints(0))", "kind(char_value) == kind(ints(0))"),
        ], "KIND form fixture calls KIND on every intrinsic type and on both scalar and rank-one array arguments.")
    add("kind_characteristics", "S16.9.118-002", ["KIND-result-default-integer-scalar"],
        "effect", kind_forms_source, [
            Mutation("kind-result-array-wrapped", "KIND-result-default-integer-scalar", "rank(kind(ints)) == 0", "rank([kind(ints)]) == 0"),
        ], "KIND result-characteristics fixture inquires KIND and RANK directly on KIND expressions.")
    add("kind_values", "S16.9.118-003", [
        "KIND-returns-integer-kind-parameter", "KIND-returns-real-kind-parameter", "KIND-returns-complex-kind-parameter",
        "KIND-returns-logical-kind-parameter", "KIND-returns-character-kind-parameter"],
        "effect", kind_values_source, [
            Mutation("integer-kind-demoted", "KIND-returns-integer-kind-parameter", "kind(wide_integer) == wide_int_k", "kind(int(wide_integer)) == wide_int_k"),
            Mutation("real-kind-demoted", "KIND-returns-real-kind-parameter", "kind(double_real) == kind(0.0d0)", "kind(real(double_real)) == kind(0.0d0)"),
            Mutation("complex-kind-demoted", "KIND-returns-complex-kind-parameter", "kind(double_complex) == kind((0.0d0, 0.0d0))", "kind(cmplx(double_complex)) == kind((0.0d0, 0.0d0))"),
            Mutation("logical-value-changed", "KIND-returns-logical-kind-parameter", "logical :: logical_value = .true.", "logical :: logical_value = .false."),
            Mutation("character-kind-confused-with-length", "KIND-returns-character-kind-parameter", "kind(char_value) == kind('A')", "kind(char_value) == len(char_value)"),
        ], "KIND value fixture compares KIND(X) with the kind type parameter of integer, real, complex, logical, and character X.")

    add("lbound_assumed_rank_argument", "S16.9.119-001", ["LBOUND-ARRAY-assumed-rank-or-array"],
        "positive-control", lbound_assumed_rank_source, [
            Mutation("ordinary-array-lower-bound-changed", "LBOUND-ARRAY-assumed-rank-or-array", "integer :: explicit_array(2:4)", "integer :: explicit_array(1:3)"),
        ], "LBOUND argument-form fixture calls LBOUND on an ordinary array and on a rank-one assumed-rank dummy.")
    add("lbound_argument_controls", "S16.9.119-001", [
        "LBOUND-DIM-integer-scalar-in-rank-range", "LBOUND-KIND-scalar-integer-constant-expression"],
        "positive-control", lbound_argument_controls_source, [
            Mutation("dim-one-changed-to-two", "LBOUND-DIM-integer-scalar-in-rank-range", "lbound(rank_two, dim=1) == -3", "lbound(rank_two, dim=2) == -3"),
            Mutation("kind-constant-demoted", "LBOUND-KIND-scalar-integer-constant-expression", "kind(lbound(rank_two, kind=wide_k)) == wide_k", "kind(lbound(rank_two)) == wide_k"),
        ], "LBOUND argument-controls fixture uses scalar DIM values in range and a scalar integer constant KIND expression; allocation/association status restrictions remain pending.")
    add("lbound_characteristics", "S16.9.119-002", [
        "LBOUND-result-integer-kind-default-or-KIND", "LBOUND-result-scalar-with-DIM", "LBOUND-result-rank-one-size-rank-without-DIM"],
        "effect", lbound_characteristics_source, [
            Mutation("selected-kind-demoted", "LBOUND-result-integer-kind-default-or-KIND", "kind(lbound(a, kind=wide_k)) == wide_k", "kind(lbound(a)) == wide_k"),
            Mutation("scalar-dim-removed", "LBOUND-result-scalar-with-DIM", "rank(lbound(a, dim=2)) == 0", "rank(lbound(a)) == 0"),
            Mutation("vector-result-made-scalar", "LBOUND-result-rank-one-size-rank-without-DIM", "rank(lbound(a)) == 1", "rank(lbound(a, dim=1)) == 1"),
        ], "LBOUND characteristics fixture inquires KIND, RANK, and SIZE directly on LBOUND expressions with and without DIM/KIND.")
    add("lbound_dim_values", "S16.9.119-003", [
        "LBOUND-DIM-whole-nonzero-extent-lower-bound", "LBOUND-DIM-assumed-size-rank-DIM-lower-bound", "LBOUND-DIM-otherwise-one"],
        "effect", lbound_dim_values_source, [
            Mutation("whole-array-changed-to-section", "LBOUND-DIM-whole-nonzero-extent-lower-bound", "lbound(whole, dim=1) == -3", "lbound(whole(:,:), dim=1) == -3"),
            Mutation("assumed-size-lower-bound-changed", "LBOUND-DIM-assumed-size-rank-DIM-lower-bound", "integer, intent(in) :: dummy(2:*)", "integer, intent(in) :: dummy(1:*)"),
            Mutation("otherwise-section-made-whole", "LBOUND-DIM-otherwise-one", "lbound(whole(-3:4:2, 7:9), dim=1) == 1", "lbound(whole, dim=1) == 1"),
        ], "LBOUND DIM-value fixture observes whole nonzero lower bounds, assumed-size dummy lower bounds, and required one for sections/zero extent.")
    add("lbound_vector_values", "S16.9.119-004", [
        "LBOUND-vector-elements-match-DIM-inquiries", "LBOUND-vector-KIND-elements-match-selected-kind-inquiries"],
        "effect", lbound_vector_values_source, [
            Mutation("vector-actual-made-section", "LBOUND-vector-elements-match-DIM-inquiries", "size(lbound(a)) == 3 .and. all(lbound(a) == [lbound(a, dim=1), lbound(a, dim=2), lbound(a, dim=3)])", "size(lbound(a)) == 3 .and. all(lbound(a(:,:,:)) == [lbound(a, dim=1), lbound(a, dim=2), lbound(a, dim=3)])"),
            Mutation("vector-kind-demoted", "LBOUND-vector-KIND-elements-match-selected-kind-inquiries", "kind(lbound(a, kind=wide_k)) == wide_k", "kind(lbound(a)) == wide_k"),
        ], "LBOUND vector-value fixture checks DIM-absent vector elements against scalar inquiries and repeats them with selected KIND; an assumed-shape helper observes dummy lower bounds.")
    return {identifier(case.rule, case.variant): case for case in raw}


def mutation_records(case: Case):
    records = []
    raw = case.source.encode("ascii")
    for mutation in case.mutations:
        count = case.source.count(mutation.expected)
        if count != 1:
            raise ValueError(f"{case.variant}:{mutation.id} expected unique mutation text {mutation.expected!r}, saw {count}")
        start = case.source.index(mutation.expected)
        mutated = raw[:start] + mutation.replacement.encode("ascii") + raw[start + len(mutation.expected):]
        records.append(dict(id=mutation.id, facet=mutation.facet, kind="feature", expected=mutation.expected,
                            replacement=mutation.replacement, span=[start, start + len(mutation.expected)],
                            source_sha256=sha(mutated)))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for name, case in make_cases().items():
        raw = case.source.encode("ascii")
        mutations = mutation_records(case)
        spec = dict(id=name, variant=case.variant, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                    source=case.source, source_sha256=sha(raw), completion=case.completion, mutations=mutations,
                    oracle=case.oracle, profiles=list(case.profiles))
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case.variant)
        manifest = dict(schema_version=1, id=name, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=case.completion, stderr=""))
        if case.profiles:
            manifest["profiles"] = list(case.profiles)
        spec["path"], spec["manifest"] = directory.relative_to(root).as_posix() + "/fixture.json", manifest
        specs[name] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
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


def sync_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for rule, reasons in RESTORED_PENDING.items():
        if rule in by_rule:
            pending = by_rule[rule].setdefault("pending", {})
            for facet, reason in reasons.items():
                if facet not in covered.get(rule, set()):
                    pending[facet] = reason
    for spec in specs.values():
        row = by_rule[spec["rule"]]
        if not set(spec["facets"]) <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + spec["rule"])
        for facet in spec["facets"]:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = spec["rule"] + " intrinsics_16_9_o fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + spec["oracle"])
        limit_prefix = spec["rule"] + " intrinsics_16_9_o boundaries: "
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), limit_prefix,
            limit_prefix + "This packet supplies only exact integer/logical/kind/bounds/bit and guarded-I/O observations; it does not assert processor-dependent contiguity cases, IOSTAT numbers, IOMSG text, coarray behavior, diagnostics for unnumbered restrictions, approximations, or compiler consensus.")
    return result


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    owned_cases = [case for case in make_cases().values() if case.rule.startswith("S" + section + "-")]
    covered = sum(len(case.facets) for case in owned_cases)
    summary = (SUMMARY_BEGIN + "\n"
        "## Intrinsics 16.9.O runtime observations\n\n"
        f"This batch adds {len(owned_cases)} generated run/effect or positive-control fixtures for {section}, "
        f"covering {covered} pending facets for ISHFTC, IS_CONTIGUOUS, IS_IOSTAT_END, IS_IOSTAT_EOR, KIND, "
        f"and LBOUND. Oracles use BTEST bit observations, direct KIND/RANK inquiries on intrinsic expressions, "
        f"guarded actual READ IOSTAT values, and exact lower-bound rules including DIM, KIND, zero extent, "
        f"assumed-size, and assumed-shape cases. Processor-dependent contiguity and coarray LCOBOUND cases are outside this packet.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        head, tail = before.split(SUMMARY_BEGIN)
        _, rest_tail = tail.split(SUMMARY_END)
        before = head + summary + rest_tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    generated = "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n"
    return before + begin + generated + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        section_specs = {k: v for k, v in specs.items() if v["rule"].startswith("S" + section + "-")}
        updated = sync_catalogue(catalogue, section_specs)
        updated_catalogues[rel] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        for rel, updated in updated_catalogues.items():
            if json.loads((root / rel).read_text()) != updated:
                stale.append(rel)
        for rel, text in updated_views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise ValueError("stale intrinsics_16_9_o generated files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogues:
            for rel, updated in updated_catalogues.items():
                (root / rel).write_text(json.dumps(updated, indent=2) + "\n")
            for rel, text in updated_views.items():
                (root / rel).write_text(text)
    return files, specs


def mutate_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["id"])
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span lost complete-parent binding")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(str(compiler)).name.lower() else "gfortran"


def compiler_command(compiler, std, source, output):
    family = compiler_family(compiler)
    flag = ("--std=" if family == "lfortran" else "-std=") + std if std else ""
    return [str(compiler)] + ([flag] if flag else []) + [str(source), "-o", str(output)]


def run_source(compiler, std, case_dir, source_text, expected_stdout):
    source = case_dir / "source.f90"
    exe = case_dir / "program"
    source.write_text(source_text)
    compile_result = subprocess.run(compiler_command(compiler, std, source, exe), cwd=case_dir,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_result.returncode != 0:
        return dict(status="compile-fail", stdout=compile_result.stdout, stderr=compile_result.stderr,
                    returncode=compile_result.returncode)
    run_result = subprocess.run([str(exe)], cwd=case_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run_result.returncode == 0 and run_result.stdout == expected_stdout and run_result.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run_result.stdout,
                stderr=run_result.stderr, returncode=run_result.returncode)


def mutation_check(root, compiler, std, keep_work=False, inject_survivor=False):
    root = Path(root)
    _, specs = build_corpus(root)
    family = compiler_family(compiler)
    workspace = root / ".intrinsics_16_9_o_mutations" / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    report = []
    try:
        for case_index, spec in enumerate(specs.values(), 1):
            case_dir = workspace / f"{case_index:03d}_{spec['variant']}"
            case_dir.mkdir()
            parent = run_source(compiler, std, case_dir, spec["source"], spec["completion"])
            parent_ok = parent["status"] == "pass"
            parent_known = spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set())
            for index, mutation in enumerate(spec["mutations"]):
                if not parent_ok and parent_known:
                    report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                       kind=mutation["kind"], skipped=True, parent_ok=False, failed=True,
                                       status="known-parent-failure", stdout=parent["stdout"], stderr=parent["stderr"],
                                       returncode=parent["returncode"]))
                    continue
                mutant_dir = case_dir / f"mut_{index:03d}"
                mutant_dir.mkdir()
                mutant = spec["source"] if inject_survivor and not report else mutate_source(spec, mutation).decode("ascii")
                observed = run_source(compiler, std, mutant_dir, mutant, spec["completion"])
                failed = observed["status"] == "run-fail"
                report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                   kind=mutation["kind"], skipped=False, parent_ok=parent_ok, failed=failed,
                                   status=observed["status"], stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"]))
        bad = [row for row in report if (not row["parent_ok"] and not row.get("skipped")) or not row["failed"] or row["status"] == "compile-fail"]
        if bad:
            raise RuntimeError(json.dumps(bad[:10], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check))) > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work, args.inject_surviving_mutant)
        skipped = sum(1 for row in report if row.get("skipped"))
        print(f"Mutation-checked {len(report) - skipped} intrinsics_16_9_o mutations; {skipped} skipped for known parent failures.")
        return
    _, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_o cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} mutations.")


if __name__ == "__main__":
    main()
