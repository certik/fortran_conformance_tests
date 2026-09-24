#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.18-16.9.21 intrinsic fixtures."""

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
TOPIC = "intrinsics_16_9_c"
SECTIONS = ("16.9.18", "16.9.19", "16.9.20", "16.9.21")
CATALOGUES = {
    "16.9.18": "doc/catalogues/asinh_intrinsic_16_9_18.json",
    "16.9.19": "doc/catalogues/asinpi_intrinsic_16_9_19.json",
    "16.9.20": "doc/catalogues/associated_intrinsic_16_9_20.json",
    "16.9.21": "doc/catalogues/atan_intrinsic_16_9_21.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.C FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.C FIXTURES -->"
RESTORED_PENDING = {
    "S16.9.20-004": {
        "associated-pointer-argument-is-pointer": (
            "PENDING after batch268 re-review: replacing the POINTER argument by a nonpointer actual would "
            "violate this unnumbered restriction, so this packet keeps only the defined-status positive "
            "control with a conforming mutation."
        ),
    },
    "S16.9.20-005": {
        "associated-target-pointer-or-targetable-entity": (
            "PENDING after batch268 re-review: removing the TARGET attribute or using a nontargetable "
            "actual would violate this unnumbered restriction; the defined pointer TARGET status facet "
            "has the load-bearing conforming mutation in this packet."
        ),
    },
    "S16.9.20-007": {
        "associated-data-target-noncoindexed-target": (
            "PENDING after batch268 re-review: the noncoindexed/coindexed TARGET boundary requires "
            "coarrays or a nontargetable/nonconforming actual and remains outside this single-image "
            "fixture packet."
        ),
        "associated-data-target-type-compatible-equal-kind": (
            "PENDING after batch268 review: a mismatched type or kind target would be nonconforming under "
            "this unnumbered restriction, and the packet does not have a conforming feature mutation that "
            "distinguishes this property."
        ),
        "associated-data-target-same-rank-when-required": (
            "PENDING after batch268 review: a rank-mismatch target would be nonconforming under this "
            "unnumbered restriction, and the packet does not have a conforming feature mutation that "
            "distinguishes this property."
        ),
    }
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace('.', '_').replace('-', '_') + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Case:
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[tuple[str, str, str], ...]
    oracle: str

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.C " + self.variant.upper().replace("_", " ") + " OK\n"


def program(name: str, body: str, completion: str, declarations: str = "") -> str:
    return f"""program i169c_{name}
  implicit none
{declarations}{body}  write(*,'(a)') '{completion.rstrip()}'
end program i169c_{name}
"""


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

MODULE_REQUIRE_HELPERS = """
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


def associated_status_source(completion):
    return f"""program i169c_associated_status_inquiry
  implicit none
  integer, target :: target_value = 17
  integer, pointer :: pointer_value
  logical :: observed
  nullify(pointer_value)
  observed = .true.
  observed = associated(pointer_value)
  call require_false('status nullified false', observed)
  pointer_value => target_value
  observed = .false.
  observed = associated(pointer_value)
  call require_true('status assigned true', observed)
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_status_inquiry
"""


def associated_inquiry_source(completion):
    return f"""program i169c_associated_inquiry_no_side_effect
  implicit none
  integer, target :: target_value = 41
  integer, pointer :: pointer_value
  logical :: before, after
  pointer_value => target_value
  before = associated(pointer_value)
  after = associated(pointer_value)
  call require_true('first inquiry true', before)
  call require_true('second inquiry true', after)
  call require_true('pointer remains associated', associated(pointer_value, target_value))
  call require_true('target value unchanged', target_value == 41)
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_inquiry_no_side_effect
"""


def associated_any_type_source(completion):
    return f"""module i169c_assoc_any_type_mod
  implicit none
  type :: payload
    integer :: tag
  end type payload
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  integer function proc_target(x)
    integer, intent(in) :: x
    proc_target = x + 3
  end function proc_target
end module i169c_assoc_any_type_mod
program i169c_associated_any_type
  use i169c_assoc_any_type_mod
  implicit none
  integer, target :: int_target = 5
  real, target :: real_target = 2.0
  type(payload), target :: derived_target
  integer, pointer :: int_pointer
  real, pointer :: real_pointer
  type(payload), pointer :: derived_pointer
  procedure(int_fun), pointer :: procedure_pointer
  derived_target%tag = 19
  int_pointer => int_target
  real_pointer => real_target
  derived_pointer => derived_target
  procedure_pointer => proc_target
  call require_true('integer data pointer admitted', associated(int_pointer))
  call require_true('real data pointer admitted', associated(real_pointer))
  call require_true('derived data pointer admitted', associated(derived_pointer))
  call require_true('procedure pointer admitted', associated(procedure_pointer))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_any_type
"""


def associated_pointer_arg_source(completion):
    return f"""program i169c_associated_pointer_argument
  implicit none
  integer, target :: target_value = 23
  integer, pointer :: pointer_value
  nullify(pointer_value)
  call require_false('defined null pointer status', associated(pointer_value))
  pointer_value => target_value
  call require_true('defined associated pointer status', associated(pointer_value))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_pointer_argument
"""


def associated_target_arg_source(completion):
    return f"""program i169c_associated_target_argument
  implicit none
  integer, target :: target_value = 29
  integer, target :: other_target = 31
  integer, pointer :: pointer_value, target_pointer
  pointer_value => target_value
  target_pointer => target_value
  call require_true('target entity with TARGET attribute', associated(pointer_value, target_value))
  call require_true('defined pointer target argument true', associated(pointer_value, target_pointer))
  target_pointer => other_target
  call require_false('defined pointer target argument false control', associated(pointer_value, target_pointer))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_target_argument
"""


def associated_proc_restriction_source(completion):
    return f"""module i169c_assoc_proc_restriction_mod
  implicit none
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  integer function proc_a(x)
    integer, intent(in) :: x
    proc_a = x + 1
  end function proc_a
  integer function proc_b(x)
    integer, intent(in) :: x
    proc_b = x + 2
  end function proc_b
end module i169c_assoc_proc_restriction_mod
program i169c_associated_proc_restriction
  use i169c_assoc_proc_restriction_mod
  implicit none
  procedure(int_fun), pointer :: p, q
  p => proc_a
  q => proc_b
  call require_true('allowable procedure target true', associated(p, proc_a))
  call require_true('same characteristics procedure target true', associated(q, proc_b))
  call require_false('same characteristics wrong procedure false', associated(p, proc_b))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_proc_restriction
"""


def associated_data_restriction_source(completion):
    return f"""module i169c_assoc_data_restriction_mod
  implicit none
  integer, target :: module_target = 37
contains
  function pointer_function() result(result_pointer)
    integer, pointer :: result_pointer
    result_pointer => module_target
  end function pointer_function
end module i169c_assoc_data_restriction_mod
program i169c_associated_data_restriction
  use i169c_assoc_data_restriction_mod
  implicit none
  integer, target :: scalar_target = 37
  integer, target :: array_target(3) = [1, 2, 3]
  integer, pointer :: scalar_pointer
  integer, pointer :: array_pointer(:)
  scalar_pointer => scalar_target
  array_pointer => array_target
  call require_true('targetable scalar positive control true', associated(scalar_pointer, scalar_target))
  scalar_pointer => module_target
  call require_true('data pointer function result true', associated(scalar_pointer, pointer_function()))
  call require_true('whole array no vector subscript true', associated(array_pointer, array_target))
  call require_true('same integer kind target true', kind(scalar_pointer) == kind(scalar_target))
  call require_true('same rank array target true', rank(array_pointer) == rank(array_target))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_data_restriction
"""


def associated_result_source(completion):
    return f"""program i169c_associated_result_default_logical
  implicit none
  integer, target :: target_value = 43
  integer, pointer :: pointer_value
  logical :: observed
  nullify(pointer_value)
  observed = .true.
  observed = associated(pointer_value)
  call require_true('result has default logical kind', kind(observed) == kind(.false.))
  call require_false('default logical scalar false', observed)
  pointer_value => target_value
  observed = .false.
  observed = associated(pointer_value)
  call require_true('default logical scalar true', observed)
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_result_default_logical
"""


def associated_no_target_source(completion):
    return f"""program i169c_associated_no_target
  implicit none
  integer, target :: target_value = 47
  integer, pointer :: pointer_value
  nullify(pointer_value)
  call require_false('no target absent false iff disassociated', associated(pointer_value))
  pointer_value => target_value
  call require_true('no target absent true iff associated', associated(pointer_value))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_no_target
"""


def associated_proc_cases_source(completion):
    return f"""module i169c_assoc_proc_cases_mod
  implicit none
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  integer function proc_a(x)
    integer, intent(in) :: x
    proc_a = x + 1
  end function proc_a
  integer function proc_b(x)
    integer, intent(in) :: x
    proc_b = x + 2
  end function proc_b
  subroutine check_dummy(dummy)
    procedure(int_fun) :: dummy
    procedure(int_fun), pointer :: p
    p => dummy
    call require_true('dummy procedure ultimate argument true', associated(p, dummy))
    call require_false('dummy procedure wrong target false', associated(p, proc_b))
  end subroutine check_dummy
{MODULE_REQUIRE_HELPERS}end module i169c_assoc_proc_cases_mod
program i169c_associated_proc_cases
  use i169c_assoc_proc_cases_mod
  implicit none
  procedure(int_fun), pointer :: p, q
  p => proc_a
  q => proc_a
  call require_true('same procedure target true', associated(p, proc_a))
  call require_false('different procedure target false', associated(p, proc_b))
  call require_true('procedure pointer same procedure true', associated(p, q))
  q => proc_b
  call require_false('procedure pointer different procedure false', associated(p, q))
  call check_dummy(proc_a)
  write(*,'(a)') '{completion.rstrip()}'
end program i169c_associated_proc_cases
"""


def associated_host_source(completion):
    return f"""module i169c_assoc_host_mod
  implicit none
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  recursive subroutine host(depth, carried, saw)
    integer, intent(in) :: depth
    procedure(int_fun), pointer :: carried
    logical, intent(inout) :: saw(6)
    procedure(int_fun), pointer :: current, current2
    current => inner
    if (depth == 1) then
      carried => inner
      call host(2, carried, saw)
    else
      current2 => inner
      saw(1) = associated(current, inner)
      saw(2) = .not. associated(carried, inner)
      saw(3) = .not. associated(carried, current)
      saw(4) = associated(current, current2)
      call dummy_check(inner, current, carried, saw)
    end if
  contains
    integer function inner(x)
      integer, intent(in) :: x
      inner = x + depth
    end function inner
    subroutine dummy_check(dummy, pcur, pother, saw)
      procedure(int_fun) :: dummy
      procedure(int_fun), pointer :: pcur, pother
      logical, intent(inout) :: saw(6)
      saw(5) = associated(pcur, dummy)
      saw(6) = .not. associated(pother, dummy)
    end subroutine dummy_check
  end subroutine host
end module i169c_assoc_host_mod
program i169c_associated_host_instance
  use i169c_assoc_host_mod
  implicit none
  procedure(int_fun), pointer :: outer_pointer
  logical :: saw(6)
  saw = .false.
  nullify(outer_pointer)
  call host(1, outer_pointer, saw)
  if (.not. all(saw)) then
    write(*,'(a)') 'host instance distinction failed'
    error stop
  end if
  write(*,'(a)') '{completion.rstrip()}'
end program i169c_associated_host_instance
"""


def associated_data_cases_source(completion):
    return f"""program i169c_associated_data_cases
  implicit none
  integer, target :: scalar_target = 53, other_scalar = 59
  integer, target :: array_target(4) = [1, 2, 3, 4]
  integer, target :: other_array(4) = [5, 6, 7, 8]
  character(len=1), target :: nonzero_char = 'x'
  character(len=0), target :: zero_char = ''
  character(len=1), target :: nonzero_chars(1) = ['y']
  character(len=0), target :: zero_chars(1) = ['']
  integer, pointer :: scalar_pointer
  integer, pointer :: array_pointer(:)
  character(len=:), pointer :: char_pointer
  character(len=:), pointer :: char_array_pointer(:)
  scalar_pointer => scalar_target
  call require_true('scalar same nonzero storage true', associated(scalar_pointer, scalar_target))
  call require_false('scalar wrong target false', associated(scalar_pointer, other_scalar))
  array_pointer => array_target
  call require_true('array same shape full true', associated(array_pointer, array_target))
  call require_false('array different target false', associated(array_pointer, other_array))
  call require_false('array different shape false', associated(array_pointer, array_target(1:3)))
  array_pointer => array_target(1:3)
  call require_true('array nonzero elements true', associated(array_pointer, array_target(1:3)))
  array_pointer => array_target(1:3)
  call require_false('array same shape shifted storage false', associated(array_pointer, array_target(2:4)))
  char_pointer => nonzero_char
  call require_true('scalar character nonzero storage true', associated(char_pointer, nonzero_char))
  char_pointer => zero_char
  call require_false('scalar character zero storage false', associated(char_pointer, zero_char))
  array_pointer => array_target(1:0)
  call require_false('array target size zero false', associated(array_pointer, array_target(1:0)))
  char_array_pointer => nonzero_chars
  call require_true('array element nonzero storage true', associated(char_array_pointer, nonzero_chars))
  char_array_pointer => zero_chars
  call require_false('array element zero storage false', associated(char_array_pointer, zero_chars))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_data_cases
"""


def associated_pointer_cases_source(completion):
    return f"""program i169c_associated_pointer_cases
  implicit none
  integer, target :: scalar_target = 61, other_scalar = 67
  integer, target :: array_target(4) = [1, 2, 3, 4]
  character(len=1), target :: nonzero_char = 'x'
  character(len=0), target :: zero_char = ''
  character(len=1), target :: nonzero_chars(1) = ['y']
  character(len=0), target :: zero_chars(1) = ['']
  integer, pointer :: p_scalar, q_scalar
  integer, pointer :: p_array(:), q_array(:)
  character(len=:), pointer :: p_char, q_char
  character(len=:), pointer :: p_chars(:), q_chars(:)
  p_scalar => scalar_target
  nullify(q_scalar)
  call require_false('scalar pointer target one disassociated false', associated(p_scalar, q_scalar))
  q_scalar => scalar_target
  call require_true('scalar pointer both associated true', associated(p_scalar, q_scalar))
  q_scalar => scalar_target
  call require_true('scalar pointer same target true', associated(p_scalar, q_scalar))
  q_scalar => other_scalar
  call require_false('scalar pointer distinct target false', associated(p_scalar, q_scalar))
  p_array => array_target
  nullify(q_array)
  call require_false('array pointer target one disassociated false', associated(p_array, q_array))
  q_array => array_target
  call require_true('array pointer both associated true', associated(p_array, q_array))
  q_array => array_target
  call require_true('array pointer same shape true', associated(p_array, q_array))
  q_array => array_target(1:3)
  call require_false('array pointer different shape false', associated(p_array, q_array))
  p_array => array_target(1:3)
  q_array => array_target(1:3)
  call require_true('array pointer same storage order true', associated(p_array, q_array))
  p_array => array_target(1:3)
  q_array => array_target(1:3)
  q_array => array_target(2:4)
  call require_false('array pointer shifted storage false', associated(p_array, q_array))
  p_char => nonzero_char
  q_char => nonzero_char
  call require_true('scalar pointer nonzero storage true', associated(p_char, q_char))
  p_char => zero_char
  q_char => zero_char
  call require_false('scalar pointer zero storage false', associated(p_char, q_char))
  p_array => array_target(1:0)
  q_array => array_target(1:0)
  call require_false('array pointer size zero false', associated(p_array, q_array))
  p_chars => nonzero_chars
  q_chars => nonzero_chars
  call require_true('array pointer element nonzero storage true', associated(p_chars, q_chars))
  p_chars => zero_chars
  q_chars => zero_chars
  call require_false('array pointer element zero storage false', associated(p_chars, q_chars))
  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169c_associated_pointer_cases
"""


def asinh_elemental_source(completion):
    return program("asinh_elemental", """  real :: x(3) = [-2.0, 0.25, 3.0]
  associate(result => asinh(x))
    if (rank(result) /= 1) error stop
    if (size(result) /= 3) error stop
  end associate
""", completion)


def asinh_argument_source(completion):
    return program("asinh_arguments", """  real :: real_x = 0.25
  complex :: complex_x = (2.0, 2.0)
  real :: pi
  real :: real_result
  complex :: complex_result
  pi = acos(-1.0)
  real_result = asinh(real_x)
  complex_result = asinh(complex_x)
  if (kind(real_result) /= kind(real_x)) error stop
  if (kind(complex_result) /= kind(complex_x)) error stop
  if (aimag(complex_result) < -pi / 2.0 .or. aimag(complex_result) > pi / 2.0) error stop
""", completion)


def asinh_characteristics_source(completion):
    return program("asinh_characteristics", """  real :: x(3) = [-2.0, 0.25, 3.0]
  real :: y(3)
  y = asinh(x)
  associate(result => asinh(x))
    if (rank(result) /= rank(x)) error stop
    if (size(result) /= size(x)) error stop
  end associate
  if (kind(y) /= kind(x)) error stop
  if (rank(y) /= rank(x)) error stop
  if (any(shape(y) /= shape(x))) error stop
""", completion)


def asinh_range_source(completion):
    return program("asinh_complex_range", """  integer :: i
  real :: pi
  complex :: x(2), y(2)
  pi = acos(-1.0)
  x = [(cmplx(2.0, 1.4), i = 1, 2)]
  y = asinh(x)
  if (any(aimag(y) < -pi / 2.0 .or. aimag(y) > pi / 2.0)) error stop
""", completion)


def atan_elemental_source(completion):
    return program("atan_elemental", """  real :: x(3) = [-1.4, 0.0, 1.4]
  associate(result => atan(x))
    if (rank(result) /= 1) error stop
    if (size(result) /= 3) error stop
  end associate
""", completion)


def atan_argument_source(completion):
    return program("atan_arguments", """  real :: x(3) = [1.0, 0.0, 1.0]
  real :: y(3) = [0.0, 1.0, 1.0]
  real :: boundary_x(2) = [1.0, 0.0]
  real :: boundary_y(2) = [0.0, 1.0]
  complex :: z = (2.0, 0.25)
  real :: pi
  real :: y_real_result(3), same_kind_result(3), boundary_result(2), one_arg(3)
  complex :: complex_arg
  pi = acos(-1.0)
  y_real_result = atan(y, x)
  if (any(y_real_result /= atan2(y, x))) error stop
  same_kind_result = atan(y, x)
  if (kind(same_kind_result) /= kind(x)) error stop
  if (any(same_kind_result /= atan2(y, x))) error stop
  boundary_result = atan(boundary_y, boundary_x)
  if (any(boundary_result /= atan2(boundary_y, boundary_x))) error stop
  one_arg = atan(x)
  complex_arg = atan(z)
  if (kind(one_arg) /= kind(x)) error stop
  if (kind(complex_arg) /= kind(z)) error stop
  if (real(complex_arg) < -pi / 2.0 .or. real(complex_arg) > pi / 2.0) error stop
""", completion)


def atan_characteristics_source(completion):
    return program("atan_characteristics", """  real :: x(3) = [1.0, 0.0, 1.0]
  real :: y(3) = [0.0, 1.0, 1.0]
  real :: result(3)
  result = atan(y, x)
  associate(observed => atan(y, x))
    if (rank(observed) /= rank(x)) error stop
    if (size(observed) /= size(x)) error stop
  end associate
  if (kind(result) /= kind(x)) error stop
  if (rank(result) /= rank(x)) error stop
  if (any(shape(result) /= shape(x))) error stop
""", completion)


def atan2_source(completion):
    return program("atan_same_as_atan2", """  real :: x(3) = [1.0, 0.0, 1.0]
  real :: y(3) = [0.0, 1.0, 1.0]
  real :: observed(3), reference(3)
  observed = atan(y, x)
  reference = atan2(y, x)
  if (any(observed /= reference)) error stop
""", completion)


def atan_range_source(completion):
    return program("atan_one_arg_range", """  real :: pi
  real :: real_result
  complex :: complex_result
  pi = acos(-1.0)
  real_result = atan(1.4)
  complex_result = atan(cmplx(1.4, 0.25))
  if (real_result < -pi / 2.0 .or. real_result > pi / 2.0) error stop
  if (real(complex_result) < -pi / 2.0 .or. real(complex_result) > pi / 2.0) error stop
""", completion)


def make_cases():
    raw = []
    def add(variant, rule, facets, evidence, source_func, mutations, oracle):
        completion = "INTRINSICS 16.9.C " + variant.upper().replace("_", " ") + " OK\n"
        raw.append(Case(variant, rule, tuple(facets), evidence, source_func(completion), tuple(mutations), oracle))

    add("asinh_elemental", "S16.9.18-002", ["asinh-elemental-function-class"], "effect", asinh_elemental_source,
        [("array-argument-to-singleton-array", "asinh(x)", "[asinh(x(1))]")],
        "ASINH elemental fixture applies ASINH to a rank-one real array and observes the expression rank and size required by elemental application.")
    add("asinh_arguments", "S16.9.18-003", ["asinh-argument-restrictions"], "positive-control", asinh_argument_source,
        [("complex-intrinsic-removed", "complex_result = asinh(complex_x)", "complex_result = complex_x")],
        "ASINH argument positive control calls ASINH with both permitted real and complex arguments and observes same-kind assignment completion.")
    add("asinh_characteristics", "S16.9.18-004", ["asinh-result-same-as-x"], "effect", asinh_characteristics_source,
        [("array-argument-to-singleton-array", "asinh(x))\n    if (rank(result)", "[asinh(x(1))])\n    if (rank(result)")],
        "ASINH result-characteristics fixture assigns the array result and checks kind, rank, and shape match X without comparing approximate values.")
    add("asinh_complex_range", "S16.9.18-006", ["asinh-complex-imaginary-part-radians", "asinh-complex-imaginary-part-range"], "effect", asinh_range_source,
        [("wrong-intrinsic-sinh", "y = asinh(x)", "y = sinh(x)"), ("feature-removed", "y = asinh(x)", "y = cmplx(0.0, 2.0)")],
        "ASINH complex-range fixture uses complex input and checks only the required AIMAG range -pi/2 through pi/2.")

    add("atan_elemental", "S16.9.21-002", ["atan-elemental-function-class"], "effect", atan_elemental_source,
        [("array-argument-to-singleton-array", "atan(x)", "[atan(x(1))]")],
        "ATAN elemental fixture applies one-argument ATAN to a rank-one real array and observes expression rank and size.")
    add("atan_arguments", "S16.9.21-003", ["atan-y-real", "atan-two-argument-x-real-same-kind", "atan-two-argument-zero-zero-excluded", "atan-one-argument-x-real-or-complex"], "positive-control", atan_argument_source,
        [("y-real-call-removed", "y_real_result = atan(y, x)", "y_real_result = 0.0"),
         ("same-kind-call-removed", "same_kind_result = atan(y, x)", "same_kind_result = 0.0"),
         ("boundary-call-removed", "boundary_result = atan(boundary_y, boundary_x)", "boundary_result = 0.0"),
         ("complex-one-arg-removed", "complex_arg = atan(z)", "complex_arg = z")],
        "ATAN argument positive control uses real Y, same-kind real X including (0,1)/(1,0) boundary pairs, and real plus complex one-argument X.")
    add("atan_characteristics", "S16.9.21-004", ["atan-result-same-as-x"], "effect", atan_characteristics_source,
        [("singleton-array-result", "atan(y, x))\n    if (rank(observed)", "[atan(y(1), x(1))])\n    if (rank(observed)")],
        "ATAN result-characteristics fixture checks same kind, rank, and shape for the two-argument array result.")
    add("atan_same_as_atan2", "S16.9.21-005", ["atan-two-argument-same-as-atan2"], "effect", atan2_source,
        [("swap-two-arg", "observed = atan(y, x)", "observed = atan(x, y)"), ("feature-removed", "observed = atan(y, x)", "observed = 0.0")],
        "ATAN two-argument fixture compares ATAN(Y,X) exactly with ATAN2(Y,X), which 16.9.21 p5 defines as the same result.")
    add("atan_one_arg_range", "S16.9.21-007", ["atan-one-argument-real-part-radians", "atan-one-argument-real-part-range"], "effect", atan_range_source,
        [("real-wrong-intrinsic-tan", "real_result = atan(1.4)", "real_result = tan(1.4)"), ("complex-wrong-intrinsic-tan", "complex_result = atan(cmplx(1.4, 0.25))", "complex_result = tan(cmplx(1.4, 0.25))")],
        "ATAN one-argument range fixture checks only the required real-part radian interval -pi/2 through pi/2 for real and complex X.")

    add("associated_status_inquiry", "S16.9.20-001", ["associated-pointer-association-status-inquiry"], "effect", associated_status_source,
        [("remove-pointer-assignment", "pointer_value => target_value", "nullify(pointer_value)")],
        "ASSOCIATED status fixture nullifies then pointer-assigns a data pointer and observes false then true status.")
    add("associated_inquiry_no_side_effect", "S16.9.20-002", ["associated-inquiry-function-class"], "effect", associated_inquiry_source,
        [("remove-inquiry-feature", "after = associated(pointer_value)", "after = .false.")],
        "ASSOCIATED inquiry fixture repeats the inquiry and confirms pointer association and target value are unchanged.")
    add("associated_any_type", "S16.9.20-003", ["associated-pointer-any-type-permitted", "associated-pointer-procedure-pointer-permitted"], "effect", associated_any_type_source,
        [("integer-assignment-removed", "int_pointer => int_target", "nullify(int_pointer)"), ("procedure-assignment-removed", "procedure_pointer => proc_target", "nullify(procedure_pointer)")],
        "ASSOCIATED type-permission fixture uses integer, real, derived-type data pointers and a procedure pointer as POINTER arguments.")
    add("associated_pointer_argument", "S16.9.20-004", ["associated-pointer-status-defined"], "positive-control", associated_pointer_arg_source,
        [("remove-defined-associated-state", "pointer_value => target_value", "nullify(pointer_value)")],
        "ASSOCIATED pointer-argument positive control explicitly defines pointer status with NULLIFY and pointer assignment before each inquiry.")
    add("associated_target_argument", "S16.9.20-005", ["associated-target-pointer-status-defined"], "positive-control", associated_target_arg_source,
        [("wrong-pointer-target", "target_pointer => target_value", "target_pointer => other_target")],
        "ASSOCIATED target-argument positive control uses a TARGET variable and defined pointer TARGET arguments with true and wrong-target controls.")
    add("associated_proc_restriction", "S16.9.20-006", ["associated-procedure-target-allowable", "associated-procedure-target-same-characteristics"], "positive-control", associated_proc_restriction_source,
        [("wrong-procedure-target", "p => proc_a", "p => proc_b"),
         ("wrong-same-characteristics-target", "q => proc_b", "q => proc_a")],
        "ASSOCIATED procedure-target positive control uses same-characteristics module procedures and distinguishes the assigned procedure from a wrong target.")
    add("associated_data_restriction", "S16.9.20-007", ["associated-data-target-data-pointer-function", "associated-data-target-no-vector-subscript-section"], "positive-control", associated_data_restriction_source,
        [("function-wrong-target", "result_pointer => module_target", "nullify(result_pointer)"),
         ("whole-array-target-removed", "array_pointer => array_target", "nullify(array_pointer)")],
        "ASSOCIATED data-target positive control uses a data-pointer function result and a whole-array target that is not an array section with a vector subscript.")
    add("associated_result_default_logical", "S16.9.20-008", ["associated-result-default-logical-scalar"], "effect", associated_result_source,
        [("remove-pointer-assignment", "pointer_value => target_value", "nullify(pointer_value)")],
        "ASSOCIATED result fixture assigns the inquiry result to a default LOGICAL scalar and checks kind plus false/true values.")
    add("associated_no_target", "S16.9.20-009", ["associated-no-target-true-iff-pointer-associated"], "effect", associated_no_target_source,
        [("remove-pointer-assignment", "pointer_value => target_value", "nullify(pointer_value)")],
        "ASSOCIATED absent-TARGET fixture observes false for a nullified pointer and true after pointer assignment.")
    add("associated_proc_cases", "S16.9.20-010", ["associated-procedure-target-same-procedure", "associated-dummy-procedure-ultimate-argument", "associated-procedure-pointer-same-procedure"], "effect", associated_proc_cases_source,
        [("wrong-procedure-assignment", "p => proc_a", "p => proc_b"),
         ("wrong-procedure-pointer", "q => proc_a", "q => proc_b"),
         ("wrong-dummy-ultimate-argument", "p => dummy", "p => proc_b")],
        "ASSOCIATED procedure cases fixture checks module procedure identity, dummy procedure ultimate argument, and procedure-pointer target identity.")
    add("associated_host_instance", "S16.9.20-010", ["associated-procedure-target-same-host-instance"], "effect", associated_host_source,
        [("disable-recursion", "call host(2, carried, saw)", "saw = .false.")],
        "ASSOCIATED host-instance fixture keeps recursive host instances live and distinguishes current internal procedure targets from the outer instance.")
    add("associated_data_cases", "S16.9.20-011", ["associated-scalar-target-same-nonzero-storage", "associated-array-target-same-shape", "associated-array-target-nonzero-elements", "associated-array-target-same-storage-array-order", "associated-scalar-target-not-zero-sized-storage-sequence", "associated-array-target-not-size-zero", "associated-array-target-elements-not-zero-sized-storage-sequences"], "effect", associated_data_cases_source,
        [("scalar-wrong-target", "scalar_pointer => scalar_target", "scalar_pointer => other_scalar"),
         ("array-shape-target-removed", "array_pointer => array_target\n  call require_true('array same shape full true'", "nullify(array_pointer)\n  call require_true('array same shape full true'"),
         ("array-nonzero-elements-removed", "array_pointer => array_target(1:3)\n  call require_true('array nonzero elements true'", "array_pointer => array_target(1:0)\n  call require_true('array nonzero elements true'"),
         ("array-storage-order-shifted", "array_pointer => array_target(1:3)\n  call require_false('array same shape shifted storage false'", "array_pointer => array_target(2:4)\n  call require_false('array same shape shifted storage false'"),
         ("zero-char-nonzero", "char_pointer => zero_char\n  call require_false('scalar character zero storage false', associated(char_pointer, zero_char))", "char_pointer => nonzero_char\n  call require_false('scalar character zero storage false', associated(char_pointer, nonzero_char))"),
         ("zero-size-array-nonzero", "array_pointer => array_target(1:0)\n  call require_false('array target size zero false', associated(array_pointer, array_target(1:0)))", "array_pointer => array_target\n  call require_false('array target size zero false', associated(array_pointer, array_target))"),
         ("zero-sized-elements-nonzero", "char_array_pointer => zero_chars\n  call require_false('array element zero storage false', associated(char_array_pointer, zero_chars))", "char_array_pointer => nonzero_chars\n  call require_false('array element zero storage false', associated(char_array_pointer, nonzero_chars))")],
        "ASSOCIATED data TARGET cases fixture checks scalar and array same-storage true controls plus wrong-target, different-shape, shifted-storage, zero-size, and zero-sized-storage false controls.")
    add("associated_pointer_cases", "S16.9.20-012", ["associated-scalar-pointer-target-both-associated", "associated-scalar-pointer-target-same-nonzero-storage", "associated-array-pointer-target-both-associated", "associated-array-pointer-target-same-shape", "associated-array-pointer-target-same-storage-array-order", "associated-scalar-pointer-target-not-zero-sized-storage-sequence", "associated-array-pointer-target-not-size-zero", "associated-array-pointer-target-elements-not-zero-sized-storage-sequences"], "effect", associated_pointer_cases_source,
        [("scalar-both-associated-removed", "q_scalar => scalar_target\n  call require_true('scalar pointer both associated true'", "nullify(q_scalar)\n  call require_true('scalar pointer both associated true'"),
         ("scalar-wrong-target", "q_scalar => scalar_target\n  call require_true('scalar pointer same target true'", "q_scalar => other_scalar\n  call require_true('scalar pointer same target true'"),
         ("array-both-associated-removed", "q_array => array_target\n  call require_true('array pointer both associated true'", "nullify(q_array)\n  call require_true('array pointer both associated true'"),
         ("array-shape-target-removed", "q_array => array_target\n  call require_true('array pointer same shape true', associated(p_array, q_array))", "q_array => array_target(1:3)\n  call require_true('array pointer same shape true', associated(p_array, q_array))"),
         ("array-storage-order-shifted", "p_array => array_target(1:3)\n  q_array => array_target(1:3)\n  q_array => array_target(2:4)\n  call require_false('array pointer shifted storage false'", "p_array => array_target(2:4)\n  q_array => array_target(1:3)\n  q_array => array_target(2:4)\n  call require_false('array pointer shifted storage false'"),
         ("zero-char-nonzero", "p_char => zero_char\n  q_char => zero_char\n  call require_false('scalar pointer zero storage false', associated(p_char, q_char))", "p_char => nonzero_char\n  q_char => nonzero_char\n  call require_false('scalar pointer zero storage false', associated(p_char, q_char))"),
         ("zero-size-array-nonzero", "p_array => array_target(1:0)\n  q_array => array_target(1:0)\n  call require_false('array pointer size zero false', associated(p_array, q_array))", "p_array => array_target\n  q_array => array_target\n  call require_false('array pointer size zero false', associated(p_array, q_array))"),
         ("zero-sized-elements-nonzero", "p_chars => zero_chars\n  q_chars => zero_chars\n  call require_false('array pointer element zero storage false', associated(p_chars, q_chars))", "p_chars => nonzero_chars\n  q_chars => nonzero_chars\n  call require_false('array pointer element zero storage false', associated(p_chars, q_chars))")],
        "ASSOCIATED pointer TARGET cases fixture checks both-associated and same-target true controls plus disassociated, wrong-target, shape, shifted-storage, zero-size, and zero-sized-storage false controls.")
    return {identifier(case.rule, case.variant): case for case in raw}


def mutation_records(case: Case):
    records = []
    raw = case.source.encode("ascii")
    for mid, expected, replacement in case.mutations:
        count = case.source.count(expected)
        if count != 1:
            raise ValueError(f"{case.variant}:{mid} expected unique mutation text {expected!r}, saw {count}")
        start = case.source.index(expected)
        mutated = raw[:start] + replacement.encode("ascii") + raw[start + len(expected):]
        records.append(dict(id=mid, expected=expected, replacement=replacement, span=[start, start + len(expected)], source_sha256=sha(mutated)))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for name, case in make_cases().items():
        source = case.source
        raw = source.encode("ascii")
        mutations = mutation_records(case)
        spec = dict(id=name, variant=case.variant, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                    source=source, source_sha256=sha(raw), completion=case.completion, mutations=mutations,
                    oracle=case.oracle)
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case.variant)
        manifest = dict(schema_version=1, id=name, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=case.completion, stderr=""))
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
    data_target = by_rule.get("S16.9.20-007")
    if data_target and "associated-data-target-noncoindexed-or-data-pointer-function" in data_target["facets"]:
        facets = data_target["facets"]
        index = facets.index("associated-data-target-noncoindexed-or-data-pointer-function")
        facets[index:index + 1] = [
            "associated-data-target-noncoindexed-target",
            "associated-data-target-data-pointer-function",
        ]
        data_target.setdefault("pending", {}).pop("associated-data-target-noncoindexed-or-data-pointer-function", None)
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for rule, reasons in RESTORED_PENDING.items():
        if rule in by_rule:
            pending = by_rule[rule].setdefault("pending", {})
            for facet, reason in reasons.items():
                if facet not in covered.get(rule, set()):
                    pending.setdefault(facet, reason)
    for spec in specs.values():
        row = by_rule[spec["rule"]]
        if not set(spec["facets"]) <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + spec["rule"])
        for facet in spec["facets"]:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = spec["rule"] + " intrinsics_16_9_c fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + spec["oracle"])
        limit_prefix = spec["rule"] + " intrinsics_16_9_c boundaries: "
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), limit_prefix,
            limit_prefix + "This packet supplies the named run/effect or positive-control fixture only; it does not approve unrelated facets, diagnostics, source review, evidence links, baselines, coarray behavior, processor-dependent approximations, or compiler consensus oracles.")
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
    summary = (SUMMARY_BEGIN + "\n"
        "## Intrinsics 16.9.C runtime observations\n\n"
        "This batch adds bounded generated fixtures for ASINH, ASSOCIATED, and ATAN. "
        "ASINPI remains pending because the reference compiler parsed the intrinsic but failed to link `_asinpif`; "
        "processor-dependent approximate numerical values remain pending.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def expected_pending(specs):
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    return covered


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
            raise ValueError("stale intrinsics_16_9_c generated files: " + ", ".join(stale))
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
    return specs


def mutate_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["id"])
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span lost complete-parent binding")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def compile_and_run(workdir, compiler, std, source_bytes):
    source = workdir / "source.f90"
    exe = workdir / "program"
    source.write_bytes(source_bytes)
    cmd = [str(compiler)]
    if "lfortran" in Path(str(compiler)).name:
        cmd.append("--std=" + std)
    else:
        cmd.append("-std=" + std)
    cmd += ["source.f90", "-o", "program"]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if comp.returncode != 0:
        return "compile-fail", comp.stdout + comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if run.returncode == 0:
        return "pass", run.stdout + run.stderr
    return "run-fail", run.stdout + run.stderr


def check_mutations(root, compiler, std, skip_parent_failures=False):
    root = Path(root)
    specs = generate(root)
    workspace = root / ("." + TOPIC + "_mutation_runs") / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    failures, skipped, checked = [], [], 0
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, output = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"))
            if status != "pass":
                if skip_parent_failures:
                    skipped.append(spec["id"] + ":" + status + ":" + output.splitlines()[0][:120] if output else spec["id"] + ":" + status)
                    continue
                failures.append(spec["id"] + " parent did not pass (" + status + "):\n" + output)
                continue
            for mutation in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mutation["id"])
                case_dir.mkdir()
                status, output = compile_and_run(case_dir, compiler, std, mutate_source(spec, mutation))
                if status == "compile-fail":
                    failures.append(spec["id"] + ":" + mutation["id"] + " failed to compile:\n" + output)
                elif status == "pass":
                    failures.append(spec["id"] + ":" + mutation["id"] + " survived")
        if failures:
            raise SystemExit("\n\n".join(failures))
        return checked, skipped
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--skip-parent-failures", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        checked, skipped = check_mutations(args.root, args.compiler, args.std, args.skip_parent_failures)
        print(f"Mutation-checked {checked} intrinsics_16_9_c mutations; {len(skipped)} parents skipped.")
        if skipped:
            print("Skipped parents:")
            for row in skipped:
                print("  " + row)
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_c cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} mutations.")


if __name__ == "__main__":
    main()
