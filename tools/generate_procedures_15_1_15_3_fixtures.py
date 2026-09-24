#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 procedure concepts and characteristics, 15.1-15.3.2.2."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "procedures_15_1_15_3"
SUMMARY_BEGIN = "<!-- BEGIN PROCEDURES 15.1-15.3 FIXTURES -->"
SUMMARY_END = "<!-- END PROCEDURES 15.1-15.3 FIXTURES -->"

CATALOGUES = {
    "15.1": "doc/catalogues/procedure_concepts_15_1.json",
    "15.2.1": "doc/catalogues/functions_subroutines_and_elemental_procedures_15_2_1.json",
    "15.2.2.1": "doc/catalogues/intrinsic_procedures_15_2_2_1.json",
    "15.2.2.2": "doc/catalogues/external_internal_and_module_procedures_15_2_2_2.json",
    "15.2.2.3": "doc/catalogues/dummy_procedures_15_2_2_3.json",
    "15.2.2.4": "doc/catalogues/procedure_pointers_15_2_2_4.json",
    "15.2.2.5": "doc/catalogues/statement_functions_15_2_2_5.json",
    "15.3.1": "doc/catalogues/procedure_characteristics_general_15_3_1.json",
    "15.3.2.1": "doc/catalogues/dummy_argument_kind_characteristics_15_3_2_1.json",
    "15.3.2.2": "doc/catalogues/dummy_data_object_characteristics_15_3_2_2.json",
}

CASES = [
    dict(
        variant="procedure_reference_actions",
        rule="S15.1-001",
        section="15.1",
        facets=["procedure-reference-executes-specified-actions"],
        completion="PROCEDURES 15.1 PROCEDURE REFERENCE ACTIONS OK\n",
        source="""module procedure_reference_actions_m
  implicit none
contains
  subroutine set_answer(x)
    integer, intent(out) :: x
    x = 42
  end subroutine
  subroutine leave_sentinel(x)
    integer, intent(inout) :: x
    x = x
  end subroutine
end module
program procedure_reference_actions
  use procedure_reference_actions_m
  implicit none
  integer :: actual
  actual = -333
  call set_answer(actual)
  if (actual /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.1 PROCEDURE REFERENCE ACTIONS OK'
end program
""",
        mutations=[
            ("remove-procedure-reference", "call set_answer(actual)", "call leave_sentinel(actual)", "feature"),
            ("alter-specified-action", "x = 42", "x = 41", "feature"),
            ("alter-result-guard", "actual /= 42", "actual /= 41", "oracle"),
        ],
    ),
    dict(
        variant="argument_association_access",
        rule="S15.1-002",
        section="15.1",
        facets=["procedure-action-accesses-actual-via-argument-association"],
        completion="PROCEDURES 15.1 ARGUMENT ASSOCIATION ACCESS OK\n",
        source="""module argument_association_access_m
  implicit none
contains
  subroutine bump(x)
    integer, intent(inout) :: x
    x = x + 31
  end subroutine
  subroutine leave_sentinel(x)
    integer, intent(inout) :: x
    x = x
  end subroutine
end module
program argument_association_access
  use argument_association_access_m
  implicit none
  integer :: actual
  actual = 11
  call bump(actual)
  if (actual /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.1 ARGUMENT ASSOCIATION ACCESS OK'
end program
""",
        mutations=[
            ("remove-associated-action", "call bump(actual)", "call leave_sentinel(actual)", "feature"),
            ("alter-associated-update", "x = x + 31", "x = x + 30", "feature"),
            ("alter-initial-actual", "actual = 11", "actual = 10", "input"),
        ],
    ),
    dict(
        variant="dummy_arg_names",
        rule="S15.1-003",
        section="15.1",
        facets=["dummy-arg-name-defines-dummy-argument"],
        completion="PROCEDURES 15.1 DUMMY ARG NAMES OK\n",
        source="""module dummy_arg_names_m
  implicit none
contains
  subroutine scale(x)
    integer, intent(inout) :: x
    x = x * 2
  end subroutine
  integer function twice(y)
    integer, intent(in) :: y
    twice = y * 2
  end function
end module
program dummy_arg_names
  use dummy_arg_names_m
  implicit none
  integer :: actual, result
  actual = 21
  call scale(actual)
  if (actual /= 42) error stop 1
  result = -777
  result = twice(21)
  if (result /= 42) error stop 2
  print '(a)', 'PROCEDURES 15.1 DUMMY ARG NAMES OK'
end program
""",
        mutations=[
            ("alter-subroutine-dummy-use", "x = x * 2", "x = x * 3", "feature"),
            ("alter-function-dummy-use", "twice = y * 2", "twice = y + 2", "feature"),
            ("alter-function-actual", "result = twice(21)", "result = twice(20)", "input"),
        ],
    ),
    dict(
        variant="intrinsic_dummy_keywords",
        rule="S15.1-003",
        section="15.1",
        facets=["intrinsic-procedure-dummy-arguments-specified"],
        completion="PROCEDURES 15.1 INTRINSIC DUMMY KEYWORDS OK\n",
        source="""program intrinsic_dummy_keywords
  implicit none
  integer :: value
  value = -777
  value = abs(a=-42)
  if (value /= 42) error stop 1
  value = -778
  value = index(substring='42', string='ab42')
  if (value /= 3) error stop 2
  print '(a)', 'PROCEDURES 15.1 INTRINSIC DUMMY KEYWORDS OK'
end program
""",
        mutations=[
            ("alter-abs-keyword-actual", "abs(a=-42)", "abs(a=-41)", "feature"),
            ("swap-index-keyword-association", "index(substring='42', string='ab42')", "index(string='42', substring='ab42')", "feature"),
            ("alter-index-keyword-oracle", "value /= 3", "value /= 4", "oracle"),
        ],
    ),
    dict(
        variant="function_subroutine_references",
        rule="S15.2.1-001",
        section="15.2.1",
        facets=[
            "function-definition-and-explicit-reference",
            "function-reference-implied-by-defined-operation",
            "subroutine-reference-call",
            "subroutine-reference-defined-assignment",
            "subroutine-reference-defined-io",
            "subroutine-reference-finalization",
        ],
        completion="PROCEDURES 15.2.1 FUNCTION SUBROUTINE REFERENCES OK\n",
        source="""module function_subroutine_references_m
  implicit none
  integer :: finalized = -1
  type :: box
    integer :: value
  contains
    procedure :: write_formatted
    generic :: write(formatted) => write_formatted
    final :: finalize_box
  end type
  interface operator(.plusone.)
    module procedure plusone
  end interface
  interface assignment(=)
    module procedure assign_box
  end interface
contains
  integer function answer()
    answer = 42
  end function
  integer function plusone(x)
    integer, intent(in) :: x
    plusone = x + 1
  end function
  subroutine set_answer(x)
    integer, intent(out) :: x
    x = 42
  end subroutine
  subroutine leave_sentinel(x)
    integer, intent(inout) :: x
    x = x
  end subroutine
  subroutine assign_box(lhs, rhs)
    type(box), intent(out) :: lhs
    integer, intent(in) :: rhs
    lhs%value = rhs + 21
  end subroutine
  subroutine write_formatted(dtv, unit, iotype, v_list, iostat, iomsg)
    class(box), intent(in) :: dtv
    integer, intent(in) :: unit
    character(len=*), intent(in) :: iotype
    integer, intent(in) :: v_list(:)
    integer, intent(out) :: iostat
    character(len=*), intent(inout) :: iomsg
    write(unit,'(a,i0)') 'DEFINED_IO:', dtv%value
    iostat = 0
  end subroutine
  subroutine finalize_box(item)
    type(box), intent(inout) :: item
    finalized = item%value
  end subroutine
end module
program function_subroutine_references
  use function_subroutine_references_m
  implicit none
  integer :: value, unit
  character(len=32) :: line
  type(box) :: assigned
  value = -100
  value = answer()
  if (value /= 42) error stop 1
  value = -101
  value = .plusone. 41
  if (value /= 42) error stop 2
  value = -102
  call set_answer(value)
  if (value /= 42) error stop 3
  assigned%value = -7
  assigned = 21
  if (assigned%value /= 42) error stop 4
  open(newunit=unit, file='defined_io_record.txt', status='replace', action='readwrite')
  write(unit,'(dt)') assigned
  rewind(unit)
  line = '################################'
  read(unit,'(a)') line
  close(unit, status='delete')
  if (len_trim(line) /= 13) error stop 5
  if (line(:13) /= 'DEFINED_IO:42') error stop 6
  block
    type(box) :: local
    local%value = 42
  end block
  if (finalized /= 42) error stop 7
  print '(a)', 'PROCEDURES 15.2.1 FUNCTION SUBROUTINE REFERENCES OK'
end program
""",
        mutations=[
            ("remove-explicit-function-reference", "value = answer()", "value = 41", "feature"),
            ("remove-defined-operation-reference", "value = .plusone. 41", "value = plusone(40)", "feature"),
            ("remove-subroutine-call-reference", "call set_answer(value)", "call leave_sentinel(value)", "feature"),
            ("remove-defined-assignment-reference", "assigned = 21", "assigned%value = 21", "feature"),
            ("remove-defined-io-reference", "write(unit,'(dt)') assigned", "write(unit,'(a)') 'ORDINARY_IO:41'", "feature"),
            ("alter-defined-io-action", "'DEFINED_IO:', dtv%value", "'DEFINED_IO:', dtv%value - 1", "feature"),
            ("remove-final-subroutine-reference", "final :: finalize_box", "! no final binding", "feature"),
        ],
    ),
    dict(
        variant="elemental_reference",
        rule="S15.2.1-002",
        section="15.2.1",
        facets=["elemental-procedure-referenced-elementally"],
        completion="PROCEDURES 15.2.1 ELEMENTAL REFERENCE OK\n",
        source="""module elemental_reference_m
  implicit none
contains
  elemental integer function inc(x)
    integer, intent(in) :: x
    inc = x + 1
  end function
end module
program elemental_reference
  use elemental_reference_m
  implicit none
  integer :: result(2)
  result = [-777, -778]
  result = inc([1, 41])
  if (any(result /= [2, 42])) error stop 1
  print '(a)', 'PROCEDURES 15.2.1 ELEMENTAL REFERENCE OK'
end program
""",
        mutations=[
            ("remove-elemental-reference", "result = inc([1, 41])", "result = [2, 41]", "feature"),
            ("alter-elemental-action", "inc = x + 1", "inc = x + 2", "feature"),
            ("alter-elemental-input", "[1, 41]", "[1, 40]", "input"),
        ],
    ),
    dict(
        variant="intrinsic_abs",
        rule="S15.2.2.1-001",
        section="15.2.2.1",
        facets=["intrinsic-procedure-processor-provided"],
        completion="PROCEDURES 15.2.2.1 INTRINSIC ABS OK\n",
        source="""program intrinsic_abs
  implicit none
  intrinsic :: abs
  integer :: result
  result = -777
  result = abs(-42)
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.1 INTRINSIC ABS OK'
contains
  integer function user_abs(x)
    integer, intent(in) :: x
    user_abs = -999
  end function
end program
""",
        mutations=[
            ("select-noninherent-procedure", "result = abs(-42)", "result = user_abs(-42)", "feature"),
            ("alter-intrinsic-argument", "abs(-42)", "abs(-41)", "input"),
        ],
    ),
    dict(
        variant="external_subprogram",
        rule="S15.2.2.2-001",
        section="15.2.2.2",
        facets=["external-subprogram-defines-external-procedure"],
        completion="PROCEDURES 15.2.2.2 EXTERNAL SUBPROGRAM OK\n",
        source="""integer function ext_answer()
  implicit none
  ext_answer = 42
end function
integer function wrong_answer()
  implicit none
  wrong_answer = -999
end function
program external_subprogram
  implicit none
  interface
    integer function ext_answer()
    end function
    integer function wrong_answer()
    end function
  end interface
  integer :: result
  result = -777
  result = ext_answer()
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.2 EXTERNAL SUBPROGRAM OK'
end program
""",
        mutations=[
            ("remove-external-target", "result = ext_answer()", "result = wrong_answer()", "feature"),
            ("alter-external-action", "ext_answer = 42", "ext_answer = 41", "feature"),
        ],
    ),
    dict(
        variant="internal_procedure_properties",
        rule="S15.2.2.2-002",
        section="15.2.2.2",
        facets=[
            "internal-subprogram-defines-internal-procedure",
            "internal-procedure-host-association",
        ],
        completion="PROCEDURES 15.2.2.2 INTERNAL PROPERTIES OK\n",
        source="""subroutine left_host(y)
  implicit none
  integer, intent(out) :: y
  y = local_answer()
contains
  integer function local_answer()
    local_answer = 41
  end function
end subroutine
subroutine right_host(y)
  implicit none
  integer, intent(out) :: y
  y = local_answer()
contains
  integer function local_answer()
    local_answer = 42
  end function
end subroutine
subroutine host_assoc_wrapper(y)
  implicit none
  integer, intent(out) :: y
  integer :: base
  base = 40
  y = add_two()
contains
  integer function add_two()
    add_two = base + 2
  end function
end subroutine
program internal_procedure_properties
  implicit none
  integer :: y
  interface
    subroutine left_host(y)
      integer, intent(out) :: y
    end subroutine
    subroutine right_host(y)
      integer, intent(out) :: y
    end subroutine
    subroutine host_assoc_wrapper(y)
      integer, intent(out) :: y
    end subroutine
  end interface
  y = -1
  call main_internal(y)
  if (y /= 42) error stop 1
  call left_host(y)
  if (y /= 41) error stop 2
  call right_host(y)
  if (y /= 42) error stop 3
  call host_assoc_wrapper(y)
  if (y /= 42) error stop 4
  print '(a)', 'PROCEDURES 15.2.2.2 INTERNAL PROPERTIES OK'
contains
  subroutine main_internal(y)
    integer, intent(out) :: y
    y = answer()
  end subroutine
  integer function answer()
    answer = 42
  end function
end program
""",
        mutations=[
            ("remove-main-internal-reference", "call main_internal(y)", "y = -1", "feature"),
            ("alter-host-associated-base", "base = 40", "base = 39", "feature"),
        ],
    ),
    dict(
        variant="internal_host_placements",
        rule="S15.2.2.2-003",
        section="15.2.2.2",
        facets=[
            "internal-subprogram-in-main-program",
            "internal-subprogram-in-external-subprogram",
            "internal-subprogram-in-module-subprogram",
        ],
        completion="PROCEDURES 15.2.2.2 INTERNAL HOST PLACEMENTS OK\n",
        source="""module internal_host_placements_m
  implicit none
contains
  subroutine module_wrapper(y)
    integer, intent(out) :: y
    y = answer()
  contains
    integer function answer()
      answer = 42
    end function
  end subroutine
end module
subroutine external_wrapper(y)
  implicit none
  integer, intent(out) :: y
  y = answer()
contains
  integer function answer()
    answer = 42
  end function
end subroutine
program internal_host_placements
  use internal_host_placements_m
  implicit none
  integer :: y
  interface
    subroutine external_wrapper(y)
      integer, intent(out) :: y
    end subroutine
  end interface
  y = -1
  call main_wrapper(y)
  if (y /= 42) error stop 1
  call external_wrapper(y)
  if (y /= 42) error stop 2
  call module_wrapper(y)
  if (y /= 42) error stop 3
  print '(a)', 'PROCEDURES 15.2.2.2 INTERNAL HOST PLACEMENTS OK'
contains
  subroutine main_wrapper(y)
    integer, intent(out) :: y
    y = answer()
  end subroutine
  integer function answer()
    answer = 42
  end function
end program
""",
        mutations=[
            ("remove-main-host-internal", "call main_wrapper(y)", "y = -1", "feature"),
            ("alter-external-host-internal", "y = answer()\ncontains\n  integer function answer()\n    answer = 42\n  end function\nend subroutine\nprogram", "y = 41\ncontains\n  integer function answer()\n    answer = 42\n  end function\nend subroutine\nprogram", "feature"),
            ("alter-module-host-internal", "module_wrapper(y)\n    integer, intent(out) :: y\n    y = answer()", "module_wrapper(y)\n    integer, intent(out) :: y\n    y = 41", "feature"),
        ],
    ),
    dict(
        variant="module_subprogram_procedure",
        rule="S15.2.2.2-006",
        section="15.2.2.2",
        facets=["module-subprogram-defines-module-procedure"],
        completion="PROCEDURES 15.2.2.2 MODULE PROCEDURE OK\n",
        source="""module module_subprogram_procedure_m
  implicit none
contains
  integer function answer()
    answer = 42
  end function
  integer function wrong_answer()
    wrong_answer = -999
  end function
end module
program module_subprogram_procedure
  use module_subprogram_procedure_m
  implicit none
  integer :: result
  result = -777
  result = answer()
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.2 MODULE PROCEDURE OK'
end program
""",
        mutations=[
            ("remove-module-procedure-target", "result = answer()", "result = wrong_answer()", "feature"),
            ("alter-module-procedure-action", "answer = 42", "answer = 41", "feature"),
        ],
    ),
    dict(
        variant="subprogram_and_entry",
        rule="S15.2.2.2-007",
        section="15.2.2.2",
        facets=[
            "subprogram-defines-procedure-for-function-or-subroutine",
            "entry-statement-defines-additional-procedure",
        ],
        completion="PROCEDURES 15.2.2.2 SUBPROGRAM AND ENTRY OK\n",
        source="""subroutine primary(x)
  implicit none
  integer, intent(out) :: x
  x = 42
  return
entry alternate(x)
  x = 42
end subroutine
subroutine leave_sentinel(x)
  implicit none
  integer, intent(inout) :: x
  x = x
end subroutine
program subprogram_and_entry
  implicit none
  integer :: result
  interface
    subroutine primary(x)
      integer, intent(out) :: x
    end subroutine
    subroutine alternate(x)
      integer, intent(out) :: x
    end subroutine
    subroutine leave_sentinel(x)
      integer, intent(inout) :: x
    end subroutine
  end interface
  result = -6
  call primary(result)
  if (result /= 42) error stop 1
  result = -7
  call alternate(result)
  if (result /= 42) error stop 2
  print '(a)', 'PROCEDURES 15.2.2.2 SUBPROGRAM AND ENTRY OK'
end program
""",
        mutations=[
            ("remove-subroutine-statement-procedure", "call primary(result)", "call leave_sentinel(result)", "feature"),
            ("remove-entry-procedure-reference", "call alternate(result)", "call leave_sentinel(result)", "feature"),
        ],
    ),
    dict(
        variant="dummy_procedures",
        rule="S15.2.2.3-001",
        section="15.2.2.3",
        facets=[
            "dummy-procedure-specified-as-procedure",
            "dummy-procedure-as-procedure-designator",
            "dummy-procedure-pointer-has-pointer-attribute",
        ],
        completion="PROCEDURES 15.2.2.3 DUMMY PROCEDURES OK\n",
        source="""module dummy_procedures_m
  implicit none
  abstract interface
    integer function int_fun()
    end function
    integer function int_arg_fun(i)
      integer, intent(in) :: i
    end function
    subroutine sub_proc(x)
      integer, intent(inout) :: x
    end subroutine
  end interface
contains
  integer function answer()
    answer = 42
  end function
  subroutine apply_sub(proc, x)
    procedure(sub_proc) :: proc
    integer, intent(inout) :: x
    call proc(x)
  end subroutine
  subroutine apply_fun(proc, y)
    procedure(int_arg_fun) :: proc
    integer, intent(out) :: y
    y = proc(41)
  end subroutine
  subroutine call_pointer(proc, y)
    procedure(int_fun), pointer :: proc
    integer, intent(out) :: y
    y = proc()
  end subroutine
end module
integer function plus_one(i)
  implicit none
  integer, intent(in) :: i
  plus_one = i + 1
end function
subroutine bump(x)
  implicit none
  integer, intent(inout) :: x
  x = x + 1
end subroutine
program dummy_procedures
  use dummy_procedures_m
  implicit none
  interface
    integer function plus_one(i)
      integer, intent(in) :: i
    end function
    subroutine bump(x)
      integer, intent(inout) :: x
    end subroutine
  end interface
  procedure(int_fun), pointer :: p
  integer :: x, y
  x = 41
  call apply_sub(bump, x)
  if (x /= 42) error stop 1
  y = -777
  call apply_fun(plus_one, y)
  if (y /= 42) error stop 2
  p => answer
  y = -3
  call call_pointer(p, y)
  if (y /= 42) error stop 3
  print '(a)', 'PROCEDURES 15.2.2.3 DUMMY PROCEDURES OK'
end program
""",
        mutations=[
            ("remove-dummy-procedure-call", "call proc(x)", "x = -999", "feature"),
            ("remove-dummy-procedure-designator", "y = proc(41)", "y = -999", "feature"),
            ("remove-dummy-procedure-pointer-call", "y = proc()", "y = -999", "feature"),
        ],
    ),
    dict(
        variant="procedure_pointer_attribute",
        rule="S15.2.2.4-001",
        section="15.2.2.4",
        facets=["procedure-pointer-has-pointer-attribute"],
        completion="PROCEDURES 15.2.2.4 PROCEDURE POINTER ATTRIBUTE OK\n",
        source="""module procedure_pointer_attribute_m
  implicit none
  abstract interface
    integer function int_fun()
    end function
  end interface
contains
  integer function answer()
    answer = 42
  end function
  integer function wrong_answer()
    wrong_answer = -999
  end function
end module
program procedure_pointer_attribute
  use procedure_pointer_attribute_m
  implicit none
  procedure(int_fun), pointer :: p
  integer :: result
  p => answer
  result = -8
  result = p()
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.4 PROCEDURE POINTER ATTRIBUTE OK'
end program
""",
        mutations=[
            ("associate-wrong-target", "p => answer", "p => wrong_answer", "feature"),
            ("remove-pointer-reference", "result = p()", "result = answer() - 1", "feature"),
        ],
    ),
    dict(
        variant="procedure_pointer_targets",
        rule="S15.2.2.4-002",
        section="15.2.2.4",
        facets=[
            "procedure-pointer-associated-external",
            "procedure-pointer-associated-internal",
            "procedure-pointer-associated-intrinsic",
            "procedure-pointer-associated-module",
        ],
        completion="PROCEDURES 15.2.2.4 PROCEDURE POINTER TARGETS OK\n",
        source="""module procedure_pointer_targets_m
  implicit none
  abstract interface
    integer function int_fun()
    end function
    integer function int_arg_fun(i)
      integer, intent(in) :: i
    end function
  end interface
contains
  integer function module_answer()
    module_answer = 42
  end function
  integer function module_wrong()
    module_wrong = -999
  end function
end module
integer function ext_answer()
  implicit none
  ext_answer = 42
end function
integer function ext_wrong()
  implicit none
  ext_wrong = -999
end function
program procedure_pointer_targets
  use procedure_pointer_targets_m
  implicit none
  intrinsic :: iabs
  interface
    integer function ext_answer()
    end function
    integer function ext_wrong()
    end function
  end interface
  procedure(int_fun), pointer :: p0
  procedure(int_arg_fun), pointer :: p1
  integer :: result
  p0 => ext_answer
  result = p0()
  if (result /= 42) error stop 1
  p0 => internal_answer
  result = p0()
  if (result /= 42) error stop 2
  p1 => iabs
  result = p1(-42)
  if (result /= 42) error stop 3
  p0 => module_answer
  result = p0()
  if (result /= 42) error stop 4
  print '(a)', 'PROCEDURES 15.2.2.4 PROCEDURE POINTER TARGETS OK'
contains
  integer function internal_answer()
    internal_answer = 42
  end function
  integer function internal_wrong()
    internal_wrong = -999
  end function
  integer function wrong_iabs(i)
    integer, intent(in) :: i
    wrong_iabs = -999
  end function
end program
""",
        mutations=[
            ("associate-external-wrong", "p0 => ext_answer", "p0 => ext_wrong", "feature"),
            ("associate-internal-wrong", "p0 => internal_answer", "p0 => internal_wrong", "feature"),
            ("associate-intrinsic-wrong", "p1 => iabs", "p1 => wrong_iabs", "feature"),
            ("associate-module-wrong", "p0 => module_answer", "p0 => module_wrong", "feature"),
        ],
    ),
    dict(
        variant="statement_function",
        rule="S15.2.2.5-001",
        section="15.2.2.5",
        facets=["statement-function-single-statement-definition"],
        completion="PROCEDURES 15.2.2.5 STATEMENT FUNCTION OK\n",
        source="""program statement_function
  implicit none
  integer :: f, i, result
  f(i) = i + 1
  result = -10
  result = f(41)
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.5 STATEMENT FUNCTION OK'
end program
""",
        mutations=[
            ("alter-statement-function-definition", "f(i) = i + 1", "f(i) = i + 2", "feature"),
            ("remove-statement-function-reference", "result = f(41)", "result = 41", "feature"),
        ],
    ),

]

FACETS_BY_RULE = {}
for case in CASES:
    FACETS_BY_RULE.setdefault(case["rule"], [])
    FACETS_BY_RULE[case["rule"]].extend(case["facets"])

RESTORED_PENDING = {
    "S15.2.2.2-002": {
        "internal-procedure-name-not-global": (
            "Left pending after batch269 review: the previous same-local-name runtime observation lacked "
            "a conforming feature mutation that changes global-identifier status; needs a separate "
            "load-bearing owner-rule oracle or remains definitional."
        ),
    },
    "S15.3.1-001": {
        facet: (
            "Left pending after batch269 review: this procedure characteristic needs observation through "
            "a rule that depends on characteristic agreement, such as interface/procedure-pointer "
            "compatibility or distinguishability with a one-property conforming control; body-value "
            "observations are not sufficient."
        ) for facet in [
            "procedure-kind-characteristic",
            "procedure-pure-characteristic",
            "procedure-simple-characteristic",
            "procedure-elemental-characteristic",
            "procedure-bind-characteristic",
            "procedure-dummy-arguments-characteristics",
            "procedure-function-result-characteristics",
        ]
    },
    "S15.3.2.1-001": {
        facet: (
            "Left pending after batch269 review: this dummy-argument kind needs a feature mutation or "
            "owner-rule oracle that changes the argument kind itself, not just the procedure body action."
        ) for facet in [
            "dummy-data-object-characteristic",
            "dummy-procedure-characteristic",
            "dummy-asterisk-alternate-return-characteristic",
        ]
    },
    "S15.3.2.2-001": {
        facet: (
            "Left pending after batch269 review: this dummy data object characteristic needs observation "
            "where a later rule depends on characteristic agreement, or a conforming feature mutation "
            "that changes the characteristic itself; value/payload observations are insufficient."
        ) for facet in [
            "dummy-data-declared-type-characteristic",
            "dummy-data-type-parameters-characteristic",
            "dummy-data-shape-characteristic",
            "dummy-data-intent-characteristic",
            "dummy-data-optional-characteristic",
            "dummy-data-allocatable-characteristic",
            "dummy-data-asynchronous-contiguous-value-volatile-characteristics",
            "dummy-data-polymorphic-characteristic",
            "dummy-data-pointer-target-characteristics",
            "dummy-data-nonconstant-parameter-bound-dependence-characteristic",
            "dummy-data-assumed-or-deferred-properties-characteristic",
        ]
    },
}
RESTORED_PENDING["S15.3.2.2-001"]["dummy-data-corank-codimensions-characteristic"] = (
    "Out of scope for this single-image fixture packet: coarray corank and codimensions need coarray/image evidence."
)

ORACLE_PREFIXES = {rule: f"{rule} procedures_15_1_15_3 runtime fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} procedures_15_1_15_3 boundaries: " for rule in FACETS_BY_RULE}

ORACLES = {
    rule: ORACLE_PREFIXES[rule]
    + f"Generated run/effect/f2023 fixtures {', '.join(c['variant'] for c in CASES if c['rule'] == rule)} "
    + "exercise the selected facets with nondefault integer sentinels and exact integer, logical, "
      "character-length, shape, pointer-association, procedure-reference, or control-flow observations. "
      "Every case prints one exact completion line only after all guards have reached the rule-owned effect. "
      "Generated feature mutations redirect the procedure designator, remove the reference form, alter the "
      "selected target, or change the declared characteristic being observed so the parent oracle is load-bearing."
    for rule in FACETS_BY_RULE
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule]
    + "Coverage is limited to ordinary single-image Fortran sources accepted by both validation compilers. "
      "The fixtures do not assert addresses, layout, processor-dependent diagnostics, IOMSG text, IEEE or "
      "coarray behavior, interoperability with a separate C companion, or unnumbered-prose rejection. "
      "Facets left pending remain source-use-only, coarray-only, governed by later owner rules, or lacked a "
      "load-bearing portable mutation in this packet."
    for rule in FACETS_BY_RULE
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(case):
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__" + TOPIC + "_" + case["variant"]


def fixture_dir(case):
    return "tests/fixtures/" + TOPIC + "_" + case["variant"]


def source_text(case):
    header = (
        f"! rule: {case['rule']}\n"
        "! covers: see fixture.json facets\n"
        "! evidence: effect\n"
        "! standard: f2023\n"
    )
    return header + case["source"]


def mutation_records(case, source):
    records = []
    raw = source.encode("ascii")
    for mid, expected, replacement, kind in case["mutations"]:
        expected_b = expected.encode("ascii")
        count = raw.count(expected_b)
        if count != 1:
            raise ValueError(f"{case['variant']} mutation {mid}: expected unique span for {expected!r}, found {count}")
        start = raw.index(expected_b)
        records.append(dict(
            id=mid, kind=kind, expected=expected, replacement=replacement,
            span=[start, start + len(expected_b)], line=raw[:start].count(b"\n") + 1))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for case in CASES:
        case = copy.deepcopy(case)
        name = identifier(case)
        source = source_text(case)
        mutations = mutation_records(case, source)
        manifest = dict(
            schema_version=1,
            id=name,
            rule=case["rule"],
            facets=case["facets"],
            evidence="effect",
            standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0,
                        stdout=case["completion"], stderr=""),
        )
        directory = fixture_dir(case)
        spec = dict(case)
        spec.update(id=name, path=directory + "/fixture.json", source=source,
                    source_sha256=sha(source.encode("ascii")), mutations=mutations,
                    manifest=manifest, completion=case["completion"])
        specs[name] = spec
        files[Path(root) / directory / "source.f90"] = source.encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def all_mutations(spec):
    return list(spec["mutations"])


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError(f"{spec['id']}: mutation does not match complete parent input")
    start, end = mutation["span"]
    expected = mutation["expected"].encode("ascii")
    if raw[start:end] != expected:
        raise ValueError(f"{spec['id']}:{mutation['id']}: stale mutation span")
    replacement = mutation["replacement"].encode("ascii")
    mutant = raw[:start] + replacement + raw[end:]
    if mutant == raw:
        raise ValueError(f"{spec['id']}:{mutation['id']}: mutation is identical to parent")
    return mutant


def synced_catalogue(catalogue):
    section = catalogue["section"]
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    claimed_by_rule = {rule: set(facets) for rule, facets in FACETS_BY_RULE.items()}
    for restored_rule, restored in RESTORED_PENDING.items():
        if restored_rule in by_rule:
            pending = by_rule[restored_rule].setdefault("pending", {})
            for facet, reason in restored.items():
                if facet not in claimed_by_rule.get(restored_rule, set()):
                    pending[facet] = reason
    for rule, facets in FACETS_BY_RULE.items():
        if not rule.startswith("S" + section):
            continue
        if rule not in by_rule:
            raise ValueError(f"{rule}: missing from catalogue {section}")
        row = by_rule[rule]
        missing = set(facets) - set(row["facets"])
        if missing:
            raise ValueError(f"{rule}: missing facets {sorted(missing)}")
        pending = row.setdefault("pending", {})
        for facet in facets:
            pending.pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    target = catalogue.get("render", {}).get("path")
    if not target:
        return None
    path = Path(root) / target
    section = catalogue["section"]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"{target}: generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    generated = "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n"
    return before + begin + generated + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_updates = {}
    view_updates = {}
    for catalogue_path in CATALOGUES.values():
        path = root / catalogue_path
        original = json.loads(path.read_text())
        updated = synced_catalogue(original)
        catalogue_updates[path] = updated
        view = render_view(updated, root)
        if view is not None:
            view_updates[root / updated["render"]["path"]] = view
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for path, updated in catalogue_updates.items():
            if json.loads(path.read_text()) != updated:
                stale.append(path.relative_to(root).as_posix())
        for path, text in view_updates.items():
            if path.read_text() != text:
                stale.append(path.relative_to(root).as_posix())
        if stale:
            raise ValueError("stale procedures_15_1_15_3 fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for path, updated in catalogue_updates.items():
                path.write_text(json.dumps(updated, indent=2) + "\n")
            for path, text in view_updates.items():
                path.write_text(text)
    return specs


def compiler_std_arg(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return "--std=" + std
    return "-std=" + ("f2023" if std == "f23" else std)


def compile_and_run(compiler, std, source_bytes, expected_stdout, workdir):
    source = workdir / "source.f90"
    exe = workdir / "program"
    source.write_bytes(source_bytes)
    command = [compiler, str(source), compiler_std_arg(compiler, std), "-o", str(exe)]
    compile_result = subprocess.run(command, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if compile_result.returncode != 0:
        return "compile-failed", compile_result.stdout + compile_result.stderr
    run_result = subprocess.run([str(exe)], cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if run_result.returncode == 0 and run_result.stdout == expected_stdout and run_result.stderr == "":
        return "survived", run_result.stdout + run_result.stderr
    return "killed", run_result.stdout + run_result.stderr


def run_mutation_matrix(compiler, std="f23", root=ROOT):
    _, specs = build_corpus(root)
    root = Path(root)
    work_root = root / ".mutation_work_procedures_15_1_15_3"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir()
    results = []
    try:
        for spec in specs.values():
            for mutation in all_mutations(spec):
                mutant = mutated_source(spec, mutation)
                with tempfile.TemporaryDirectory(prefix=spec["variant"] + "_", dir=work_root) as folder:
                    status, output = compile_and_run(
                        compiler, std, mutant, spec["completion"], Path(folder))
                row = dict(case=spec["id"], mutation=mutation["id"], status=status, output=output)
                results.append(row)
                if status != "killed":
                    raise RuntimeError(
                        f"{spec['id']}:{mutation['id']} {status} on {compiler}:\n{output}")
    finally:
        shutil.rmtree(work_root, ignore_errors=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f23")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        results = run_mutation_matrix(args.compiler, args.std, args.root)
        print(f"Mutation matrix killed {len(results)}/{len(results)} procedures_15_1_15_3 mutants with {args.compiler}.")
        return
    specs = generate(args.root, check=args.check, sync_catalogue=args.sync_catalogue)
    facets = sum(len(spec["facets"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} procedures_15_1_15_3 fixtures covering {facets} facets.")


if __name__ == "__main__":
    main()
