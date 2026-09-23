#!/usr/bin/env python3
"""Deterministic fixtures and mutation metadata for Fortran 2023 9.7.3.2 deallocation effects."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION = "9.7.3.2"

VARIANTS = {'dealloc_allocated_control': {'completion': 'DEALLOC ALLOCATED CONTROL OK\n',
                               'evidence': 'positive-control',
                               'facets': ['allocated-control-no-error'],
                               'rule': 'S9.7.3.2-001'},
 'dealloc_automatic_same_effect': {'completion': 'DEALLOC AUTOMATIC SAME EFFECT OK\n',
                                   'evidence': 'effect',
                                   'facets': ['automatic-deallocation-same-effect'],
                                   'rule': 'S9.7.3.2-014'},
 'dealloc_block_local_auto': {'completion': 'DEALLOC BLOCK LOCAL AUTO OK\n',
                              'evidence': 'effect',
                              'facets': ['block-local-automatic-deallocation'],
                              'rule': 'S9.7.3.2-005'},
 'dealloc_derived_subobject': {'completion': 'DEALLOC DERIVED SUBOBJECT OK\n',
                               'evidence': 'effect',
                               'facets': ['derived-deallocation-deallocates-allocatable-subobject'],
                               'rule': 'S9.7.3.2-010'},
 'dealloc_function_result_retains': {'completion': 'DEALLOC FUNCTION RESULT RETAINS OK\n',
                                     'evidence': 'effect',
                                     'facets': ['function-result-retains-status'],
                                     'rule': 'S9.7.3.2-004'},
 'dealloc_intent_out_actual': {'completion': 'DEALLOC INTENT OUT ACTUAL OK\n',
                               'evidence': 'effect',
                               'facets': ['intent-out-allocatable-actual-deallocated'],
                               'rule': 'S9.7.3.2-008'},
 'dealloc_intent_out_subobject': {'completion': 'DEALLOC INTENT OUT SUBOBJECT OK\n',
                                  'evidence': 'effect',
                                  'facets': ['intent-out-actual-subobject-deallocated'],
                                  'rule': 'S9.7.3.2-008'},
 'dealloc_intrinsic_assignment_subobject': {'completion': 'DEALLOC INTRINSIC ASSIGNMENT SUBOBJECT '
                                                          'OK\n',
                                            'evidence': 'effect',
                                            'facets': ['intrinsic-assignment-noncoarray-subobject-before-assignment'],
                                            'rule': 'S9.7.3.2-009'},
 'dealloc_procedure_local_auto': {'completion': 'DEALLOC PROCEDURE LOCAL AUTO OK\n',
                                  'evidence': 'effect',
                                  'facets': ['ordinary-unsaved-local-deallocated'],
                                  'rule': 'S9.7.3.2-004'},
 'dealloc_saved_local_control': {'completion': 'DEALLOC SAVED LOCAL CONTROL OK\n',
                                 'evidence': 'positive-control',
                                 'facets': ['saved-local-control'],
                                 'rule': 'S9.7.3.2-004'},
 'dealloc_unallocated_error': {'completion': 'DEALLOC UNALLOCATED ERROR OK\n',
                               'evidence': 'effect',
                               'facets': ['unallocated-allocatable-deallocate-error'],
                               'rule': 'S9.7.3.2-001'}}

SOURCES = {'dealloc_allocated_control': '! rule: S9.7.3.2-001\n'
                              '! covers: allocated-control-no-error\n'
                              '! A positive allocated state is established before DEALLOCATE; only '
                              'ALLOCATED is queried after.\n'
                              'program dealloc_allocated_control\n'
                              '  implicit none\n'
                              '  integer, allocatable :: x(:)\n'
                              '  integer :: stat, checks\n'
                              '  checks = 0\n'
                              '\n'
                              '  allocate(x(-9:-7), stat=stat)\n'
                              "  if (stat /= 0) error stop 'D9732:allocated:allocate-stat'\n"
                              '  x = [67, 71, 73]\n'
                              '  if (.not. allocated(x)) error stop '
                              "'D9732:allocated:before-allocated'\n"
                              '  checks = checks + 1\n'
                              "  if (lbound(x,1) /= -9) error stop 'D9732:allocated:before-lower'\n"
                              '  checks = checks + 1\n'
                              "  if (ubound(x,1) /= -7) error stop 'D9732:allocated:before-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (any(x /= [67, 71, 73])) error stop '
                              "'D9732:allocated:before-values'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  deallocate(x, stat=stat)\n'
                              "  if (stat /= 0) error stop 'D9732:allocated:deallocate-stat'\n"
                              '  checks = checks + 1\n'
                              "  if (allocated(x)) error stop 'D9732:allocated:after-unallocated'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  allocate(x(4:6), stat=stat)\n'
                              "  if (stat /= 0) error stop 'D9732:allocated:reallocate-stat'\n"
                              '  x = [79, 83, 89]\n'
                              "  if (lbound(x,1) /= 4) error stop 'D9732:allocated:realloc-lower'\n"
                              '  checks = checks + 1\n'
                              "  if (ubound(x,1) /= 6) error stop 'D9732:allocated:realloc-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (any(x /= [79, 83, 89])) error stop '
                              "'D9732:allocated:realloc-values'\n"
                              '  checks = checks + 1\n'
                              "  if (checks /= 9) error stop 'D9732:allocated:check-total'\n"
                              "  write(*,'(a)') 'DEALLOC ALLOCATED CONTROL OK'\n"
                              'end program dealloc_allocated_control\n',
 'dealloc_automatic_same_effect': '! rule: S9.7.3.2-014\n'
                                  '! covers: automatic-deallocation-same-effect\n'
                                  '! Explicit DEALLOCATE without options and automatic '
                                  'procedure-exit deallocation are both observed only by '
                                  'status/reallocation.\n'
                                  'module dealloc_automatic_same_effect_m\n'
                                  '  implicit none\n'
                                  '  integer :: checks = 0\n'
                                  'contains\n'
                                  '  subroutine automatic_visit(pass)\n'
                                  '    integer, intent(in) :: pass\n'
                                  '    integer, allocatable :: auto(:)\n'
                                  '    integer :: stat\n'
                                  '    if (allocated(auto)) error stop '
                                  "'D9732:auto-same:entry-unallocated'\n"
                                  '    checks = checks + 1\n'
                                  '    if (pass == 1) then\n'
                                  '      allocate(auto(-5:-3), stat=stat)\n'
                                  "      if (stat /= 0) error stop 'D9732:auto-same:first-stat'\n"
                                  '      auto = [307, 311, 313]\n'
                                  '      if (.not. allocated(auto)) error stop '
                                  "'D9732:auto-same:first-allocated'\n"
                                  '      checks = checks + 1\n'
                                  '      if (lbound(auto,1) /= -5) error stop '
                                  "'D9732:auto-same:first-lower'\n"
                                  '      checks = checks + 1\n'
                                  '      if (ubound(auto,1) /= -3) error stop '
                                  "'D9732:auto-same:first-upper'\n"
                                  '      checks = checks + 1\n'
                                  '      if (any(auto /= [307, 311, 313])) error stop '
                                  "'D9732:auto-same:first-values'\n"
                                  '      checks = checks + 1\n'
                                  '      return\n'
                                  '    end if\n'
                                  '    allocate(auto(10:12), stat=stat)\n'
                                  "    if (stat /= 0) error stop 'D9732:auto-same:second-stat'\n"
                                  '    auto = [317, 331, 337]\n'
                                  '    if (lbound(auto,1) /= 10) error stop '
                                  "'D9732:auto-same:second-lower'\n"
                                  '    checks = checks + 1\n'
                                  '    if (ubound(auto,1) /= 12) error stop '
                                  "'D9732:auto-same:second-upper'\n"
                                  '    checks = checks + 1\n'
                                  '    if (any(auto /= [317, 331, 337])) error stop '
                                  "'D9732:auto-same:second-values'\n"
                                  '    checks = checks + 1\n'
                                  '  end subroutine automatic_visit\n'
                                  'end module dealloc_automatic_same_effect_m\n'
                                  '\n'
                                  'program dealloc_automatic_same_effect\n'
                                  '  use dealloc_automatic_same_effect_m\n'
                                  '  implicit none\n'
                                  '  integer, allocatable :: explicit(:)\n'
                                  '  integer :: stat\n'
                                  '  allocate(explicit(-10:-8), stat=stat)\n'
                                  "  if (stat /= 0) error stop 'D9732:auto-same:explicit-stat'\n"
                                  '  explicit = [293, 299, 301]\n'
                                  '  if (.not. allocated(explicit)) error stop '
                                  "'D9732:auto-same:explicit-before-allocated'\n"
                                  '  checks = checks + 1\n'
                                  '  if (lbound(explicit,1) /= -10) error stop '
                                  "'D9732:auto-same:explicit-before-lower'\n"
                                  '  checks = checks + 1\n'
                                  '  if (ubound(explicit,1) /= -8) error stop '
                                  "'D9732:auto-same:explicit-before-upper'\n"
                                  '  checks = checks + 1\n'
                                  '  if (any(explicit /= [293, 299, 301])) error stop '
                                  "'D9732:auto-same:explicit-before-values'\n"
                                  '  checks = checks + 1\n'
                                  '  deallocate(explicit)\n'
                                  '  if (allocated(explicit)) error stop '
                                  "'D9732:auto-same:explicit-after-unallocated'\n"
                                  '  checks = checks + 1\n'
                                  '  allocate(explicit(4:6), stat=stat)\n'
                                  '  if (stat /= 0) error stop '
                                  "'D9732:auto-same:explicit-reallocate-stat'\n"
                                  '  explicit = [347, 349, 353]\n'
                                  '  if (lbound(explicit,1) /= 4) error stop '
                                  "'D9732:auto-same:explicit-realloc-lower'\n"
                                  '  checks = checks + 1\n'
                                  '  if (ubound(explicit,1) /= 6) error stop '
                                  "'D9732:auto-same:explicit-realloc-upper'\n"
                                  '  checks = checks + 1\n'
                                  '  if (any(explicit /= [347, 349, 353])) error stop '
                                  "'D9732:auto-same:explicit-realloc-values'\n"
                                  '  checks = checks + 1\n'
                                  '\n'
                                  '  call automatic_visit(1)\n'
                                  '  call automatic_visit(2)\n'
                                  "  if (checks /= 17) error stop 'D9732:auto-same:check-total'\n"
                                  "  write(*,'(a)') 'DEALLOC AUTOMATIC SAME EFFECT OK'\n"
                                  'end program dealloc_automatic_same_effect\n',
 'dealloc_block_local_auto': '! rule: S9.7.3.2-005\n'
                             '! covers: block-local-automatic-deallocation\n'
                             '! The first BLOCK execution proves allocation; the second execution '
                             'observes unallocated status on entry.\n'
                             'program dealloc_block_local_auto\n'
                             '  implicit none\n'
                             '  integer :: pass, stat, checks\n'
                             '  checks = 0\n'
                             '  do pass = 1, 2\n'
                             '    block\n'
                             '      integer, allocatable :: local(:)\n'
                             '      if (allocated(local)) error stop '
                             "'D9732:block-local:entry-unallocated'\n"
                             '      checks = checks + 1\n'
                             '      if (pass == 1) then\n'
                             '        allocate(local(-6:-4), stat=stat)\n'
                             "        if (stat /= 0) error stop 'D9732:block-local:first-stat'\n"
                             '        local = [157, 163, 167]\n'
                             '        if (.not. allocated(local)) error stop '
                             "'D9732:block-local:first-allocated'\n"
                             '        checks = checks + 1\n'
                             '        if (lbound(local,1) /= -6) error stop '
                             "'D9732:block-local:first-lower'\n"
                             '        checks = checks + 1\n'
                             '        if (ubound(local,1) /= -4) error stop '
                             "'D9732:block-local:first-upper'\n"
                             '        checks = checks + 1\n'
                             '        if (any(local /= [157, 163, 167])) error stop '
                             "'D9732:block-local:first-values'\n"
                             '        checks = checks + 1\n'
                             '      else\n'
                             '        allocate(local(7:9), stat=stat)\n'
                             "        if (stat /= 0) error stop 'D9732:block-local:second-stat'\n"
                             '        local = [173, 179, 181]\n'
                             '        if (lbound(local,1) /= 7) error stop '
                             "'D9732:block-local:second-lower'\n"
                             '        checks = checks + 1\n'
                             '        if (ubound(local,1) /= 9) error stop '
                             "'D9732:block-local:second-upper'\n"
                             '        checks = checks + 1\n'
                             '        if (any(local /= [173, 179, 181])) error stop '
                             "'D9732:block-local:second-values'\n"
                             '        checks = checks + 1\n'
                             '      end if\n'
                             '    end block\n'
                             '  end do\n'
                             "  if (checks /= 9) error stop 'D9732:block-local:check-total'\n"
                             "  write(*,'(a)') 'DEALLOC BLOCK LOCAL AUTO OK'\n"
                             'end program dealloc_block_local_auto\n',
 'dealloc_derived_subobject': '! rule: S9.7.3.2-010\n'
                              '! covers: derived-deallocation-deallocates-allocatable-subobject\n'
                              '! Parent and component allocation are proved before DEALLOCATE; '
                              'component deallocation is observed only by finalizer log.\n'
                              'module dealloc_derived_subobject_log\n'
                              '  implicit none\n'
                              '  private\n'
                              '  integer, parameter :: capacity = 8\n'
                              '  integer, save :: nlog = 0\n'
                              '  integer, save :: log_value(capacity) = -1\n'
                              '  public :: reset_log, record_log, expect_log\n'
                              'contains\n'
                              '  subroutine reset_log()\n'
                              '    nlog = 0\n'
                              '    log_value = -1\n'
                              '  end subroutine reset_log\n'
                              '\n'
                              '  subroutine record_log(value)\n'
                              '    integer, intent(in) :: value\n'
                              '    if (nlog >= capacity) error stop '
                              "'D9732:derived-subobject:log-capacity'\n"
                              '    nlog = nlog + 1\n'
                              '    log_value(nlog) = value\n'
                              '  end subroutine record_log\n'
                              '\n'
                              '  subroutine expect_log(expected)\n'
                              '    integer, intent(in) :: expected(:)\n'
                              '    if (nlog /= size(expected)) error stop '
                              "'D9732:derived-subobject:log-count'\n"
                              '    if (any(log_value(1:nlog) /= expected)) error stop '
                              "'D9732:derived-subobject:log-values'\n"
                              '  end subroutine expect_log\n'
                              'end module dealloc_derived_subobject_log\n'
                              '\n'
                              'module dealloc_derived_subobject_types\n'
                              '  use dealloc_derived_subobject_log, only: record_log\n'
                              '  implicit none\n'
                              '  private\n'
                              '  public :: leaf, owner\n'
                              '  type :: leaf\n'
                              '    integer :: token = -1\n'
                              '  contains\n'
                              '    final :: finish_leaf_vector\n'
                              '  end type leaf\n'
                              '  type :: owner\n'
                              '    integer :: tag = -1\n'
                              '    type(leaf), allocatable :: part(:)\n'
                              '  end type owner\n'
                              'contains\n'
                              '  subroutine finish_leaf_vector(x)\n'
                              '    type(leaf), intent(inout) :: x(:)\n'
                              '    integer :: i\n'
                              '    call record_log(size(x))\n'
                              '    do i = 1, size(x)\n'
                              '      call record_log(x(i)%token)\n'
                              '    end do\n'
                              '  end subroutine finish_leaf_vector\n'
                              'end module dealloc_derived_subobject_types\n'
                              '\n'
                              'program dealloc_derived_subobject\n'
                              '  use dealloc_derived_subobject_log, only: reset_log, expect_log\n'
                              '  use dealloc_derived_subobject_types, only: owner\n'
                              '  implicit none\n'
                              '  type(owner), allocatable :: item\n'
                              '  integer :: stat, checks\n'
                              '  checks = 0\n'
                              '  call reset_log()\n'
                              '\n'
                              '  allocate(item, stat=stat)\n'
                              '  if (stat /= 0) error stop '
                              "'D9732:derived-subobject:parent-allocate-stat'\n"
                              '  allocate(item%part(-11:-9), stat=stat)\n'
                              '  if (stat /= 0) error stop '
                              "'D9732:derived-subobject:component-allocate-stat'\n"
                              '  item%tag = 359\n'
                              '  item%part%token = [367, 373, 379]\n'
                              '  if (.not. allocated(item)) error stop '
                              "'D9732:derived-subobject:before-parent-allocated'\n"
                              '  checks = checks + 1\n'
                              '  if (.not. allocated(item%part)) error stop '
                              "'D9732:derived-subobject:before-component-allocated'\n"
                              '  checks = checks + 1\n'
                              '  if (lbound(item%part,1) /= -11) error stop '
                              "'D9732:derived-subobject:before-lower'\n"
                              '  checks = checks + 1\n'
                              '  if (ubound(item%part,1) /= -9) error stop '
                              "'D9732:derived-subobject:before-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (item%tag /= 359) error stop '
                              "'D9732:derived-subobject:before-tag'\n"
                              '  checks = checks + 1\n'
                              '  if (any(item%part%token /= [367, 373, 379])) error stop '
                              "'D9732:derived-subobject:before-values'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  deallocate(item, stat=stat)\n'
                              '  if (stat /= 0) error stop '
                              "'D9732:derived-subobject:deallocate-stat'\n"
                              '  checks = checks + 1\n'
                              '  if (allocated(item)) error stop '
                              "'D9732:derived-subobject:after-parent-unallocated'\n"
                              '  checks = checks + 1\n'
                              '  call expect_log([3, 367, 373, 379])\n'
                              '  checks = checks + 1\n'
                              '\n'
                              '  if (checks /= 9) error stop '
                              "'D9732:derived-subobject:check-total'\n"
                              "  write(*,'(a)') 'DEALLOC DERIVED SUBOBJECT OK'\n"
                              'end program dealloc_derived_subobject\n',
 'dealloc_function_result_retains': '! rule: S9.7.3.2-004\n'
                                    '! covers: function-result-retains-status\n'
                                    '! The function result is proved allocated and defined before '
                                    'END; the caller observes the retained value.\n'
                                    'program dealloc_function_result_retains\n'
                                    '  implicit none\n'
                                    '  integer, allocatable :: got(:)\n'
                                    '  integer :: checks\n'
                                    '  checks = 0\n'
                                    '\n'
                                    '  got = make_result()\n'
                                    '  if (.not. allocated(got)) error stop '
                                    "'D9732:function-result:caller-allocated'\n"
                                    '  checks = checks + 1\n'
                                    '  if (size(got) /= 3) error stop '
                                    "'D9732:function-result:caller-size'\n"
                                    '  checks = checks + 1\n'
                                    '  if (any(got /= [97, 101, 103])) error stop '
                                    "'D9732:function-result:caller-values'\n"
                                    '  checks = checks + 1\n'
                                    '  if (checks /= 3) error stop '
                                    "'D9732:function-result:check-total'\n"
                                    "  write(*,'(a)') 'DEALLOC FUNCTION RESULT RETAINS OK'\n"
                                    'contains\n'
                                    '  function make_result() result(r)\n'
                                    '    integer, allocatable :: r(:)\n'
                                    '    allocate(r(-5:-3))\n'
                                    '    r = [97, 101, 103]\n'
                                    '    if (.not. allocated(r)) error stop '
                                    "'D9732:function-result:result-allocated'\n"
                                    '    if (lbound(r,1) /= -5) error stop '
                                    "'D9732:function-result:result-lower'\n"
                                    '    if (ubound(r,1) /= -3) error stop '
                                    "'D9732:function-result:result-upper'\n"
                                    '    if (any(r /= [97, 101, 103])) error stop '
                                    "'D9732:function-result:result-values'\n"
                                    '  end function make_result\n'
                                    'end program dealloc_function_result_retains\n',
 'dealloc_intent_out_actual': '! rule: S9.7.3.2-008\n'
                              '! covers: intent-out-allocatable-actual-deallocated\n'
                              '! The caller proves the allocatable actual is allocated before '
                              'invocation; the callee observes it unallocated on entry.\n'
                              'program dealloc_intent_out_actual\n'
                              '  implicit none\n'
                              '  integer, allocatable :: actual(:)\n'
                              '  integer :: stat, checks\n'
                              '  checks = 0\n'
                              '  allocate(actual(-4:-2), stat=stat)\n'
                              '  if (stat /= 0) error stop '
                              "'D9732:intent-out-actual:allocate-stat'\n"
                              '  actual = [191, 193, 197]\n'
                              '  if (.not. allocated(actual)) error stop '
                              "'D9732:intent-out-actual:before-allocated'\n"
                              '  checks = checks + 1\n'
                              '  if (lbound(actual,1) /= -4) error stop '
                              "'D9732:intent-out-actual:before-lower'\n"
                              '  checks = checks + 1\n'
                              '  if (ubound(actual,1) /= -2) error stop '
                              "'D9732:intent-out-actual:before-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (any(actual /= [191, 193, 197])) error stop '
                              "'D9732:intent-out-actual:before-values'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  call replace_actual(actual, checks)\n'
                              '\n'
                              '  if (.not. allocated(actual)) error stop '
                              "'D9732:intent-out-actual:after-allocated'\n"
                              '  checks = checks + 1\n'
                              '  if (lbound(actual,1) /= 8) error stop '
                              "'D9732:intent-out-actual:after-lower'\n"
                              '  checks = checks + 1\n'
                              '  if (ubound(actual,1) /= 10) error stop '
                              "'D9732:intent-out-actual:after-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (any(actual /= [199, 211, 223])) error stop '
                              "'D9732:intent-out-actual:after-values'\n"
                              '  checks = checks + 1\n'
                              '  if (checks /= 9) error stop '
                              "'D9732:intent-out-actual:check-total'\n"
                              "  write(*,'(a)') 'DEALLOC INTENT OUT ACTUAL OK'\n"
                              'contains\n'
                              '  subroutine replace_actual(x, checks)\n'
                              '    integer, allocatable, intent(out) :: x(:)\n'
                              '    integer, intent(inout) :: checks\n'
                              '    integer :: stat\n'
                              '    if (allocated(x)) error stop '
                              "'D9732:intent-out-actual:callee-entry-unallocated'\n"
                              '    checks = checks + 1\n'
                              '    allocate(x(8:10), stat=stat)\n'
                              '    if (stat /= 0) error stop '
                              "'D9732:intent-out-actual:callee-allocate-stat'\n"
                              '    x = [199, 211, 223]\n'
                              '    if (lbound(x,1) /= 8) error stop '
                              "'D9732:intent-out-actual:callee-lower'\n"
                              '    if (ubound(x,1) /= 10) error stop '
                              "'D9732:intent-out-actual:callee-upper'\n"
                              '  end subroutine replace_actual\n'
                              'end program dealloc_intent_out_actual\n',
 'dealloc_intent_out_subobject': '! rule: S9.7.3.2-008\n'
                                 '! covers: intent-out-actual-subobject-deallocated\n'
                                 '! The allocatable component is allocated before invocation; '
                                 'INTENT(OUT) deallocates it before callee code.\n'
                                 'program dealloc_intent_out_subobject\n'
                                 '  implicit none\n'
                                 '  type :: holder\n'
                                 '    integer :: tag = -1\n'
                                 '    integer, allocatable :: part(:)\n'
                                 '  end type holder\n'
                                 '  type(holder) :: actual\n'
                                 '  integer :: stat, checks\n'
                                 '  checks = 0\n'
                                 '  allocate(actual%part(-7:-5), stat=stat)\n'
                                 '  if (stat /= 0) error stop '
                                 "'D9732:intent-out-subobject:allocate-stat'\n"
                                 '  actual%tag = 227\n'
                                 '  actual%part = [229, 233, 239]\n'
                                 '  if (.not. allocated(actual%part)) error stop '
                                 "'D9732:intent-out-subobject:before-allocated'\n"
                                 '  checks = checks + 1\n'
                                 '  if (lbound(actual%part,1) /= -7) error stop '
                                 "'D9732:intent-out-subobject:before-lower'\n"
                                 '  checks = checks + 1\n'
                                 '  if (ubound(actual%part,1) /= -5) error stop '
                                 "'D9732:intent-out-subobject:before-upper'\n"
                                 '  checks = checks + 1\n'
                                 '  if (actual%tag /= 227) error stop '
                                 "'D9732:intent-out-subobject:before-tag'\n"
                                 '  checks = checks + 1\n'
                                 '  if (any(actual%part /= [229, 233, 239])) error stop '
                                 "'D9732:intent-out-subobject:before-values'\n"
                                 '  checks = checks + 1\n'
                                 '\n'
                                 '  call reset_holder(actual, checks)\n'
                                 '\n'
                                 '  if (.not. allocated(actual%part)) error stop '
                                 "'D9732:intent-out-subobject:after-allocated'\n"
                                 '  checks = checks + 1\n'
                                 '  if (lbound(actual%part,1) /= 3) error stop '
                                 "'D9732:intent-out-subobject:after-lower'\n"
                                 '  checks = checks + 1\n'
                                 '  if (ubound(actual%part,1) /= 5) error stop '
                                 "'D9732:intent-out-subobject:after-upper'\n"
                                 '  checks = checks + 1\n'
                                 '  if (actual%tag /= 241) error stop '
                                 "'D9732:intent-out-subobject:after-tag'\n"
                                 '  checks = checks + 1\n'
                                 '  if (any(actual%part /= [251, 257, 263])) error stop '
                                 "'D9732:intent-out-subobject:after-values'\n"
                                 '  checks = checks + 1\n'
                                 '  if (checks /= 11) error stop '
                                 "'D9732:intent-out-subobject:check-total'\n"
                                 "  write(*,'(a)') 'DEALLOC INTENT OUT SUBOBJECT OK'\n"
                                 'contains\n'
                                 '  subroutine reset_holder(h, checks)\n'
                                 '    type(holder), intent(out) :: h\n'
                                 '    integer, intent(inout) :: checks\n'
                                 '    integer :: stat\n'
                                 '    if (allocated(h%part)) error stop '
                                 "'D9732:intent-out-subobject:callee-entry-unallocated'\n"
                                 '    checks = checks + 1\n'
                                 '    allocate(h%part(3:5), stat=stat)\n'
                                 '    if (stat /= 0) error stop '
                                 "'D9732:intent-out-subobject:callee-allocate-stat'\n"
                                 '    h%tag = 241\n'
                                 '    h%part = [251, 257, 263]\n'
                                 '    if (lbound(h%part,1) /= 3) error stop '
                                 "'D9732:intent-out-subobject:callee-lower'\n"
                                 '    if (ubound(h%part,1) /= 5) error stop '
                                 "'D9732:intent-out-subobject:callee-upper'\n"
                                 '  end subroutine reset_holder\n'
                                 'end program dealloc_intent_out_subobject\n',
 'dealloc_intrinsic_assignment_subobject': '! rule: S9.7.3.2-009\n'
                                           '! covers: '
                                           'intrinsic-assignment-noncoarray-subobject-before-assignment\n'
                                           '! The left allocatable component is proved allocated '
                                           'before intrinsic assignment and unallocated after.\n'
                                           'program dealloc_intrinsic_assignment_subobject\n'
                                           '  implicit none\n'
                                           '  type :: holder\n'
                                           '    integer :: tag = -1\n'
                                           '    integer, allocatable :: part(:)\n'
                                           '  end type holder\n'
                                           '  type(holder) :: lhs, rhs\n'
                                           '  integer :: stat, checks\n'
                                           '  checks = 0\n'
                                           '  allocate(lhs%part(-6:-4), stat=stat)\n'
                                           '  if (stat /= 0) error stop '
                                           "'D9732:assignment:allocate-stat'\n"
                                           '  lhs%tag = 269\n'
                                           '  lhs%part = [271, 277, 281]\n'
                                           '  rhs%tag = 283\n'
                                           '  if (.not. allocated(lhs%part)) error stop '
                                           "'D9732:assignment:before-allocated'\n"
                                           '  checks = checks + 1\n'
                                           '  if (lbound(lhs%part,1) /= -6) error stop '
                                           "'D9732:assignment:before-lower'\n"
                                           '  checks = checks + 1\n'
                                           '  if (ubound(lhs%part,1) /= -4) error stop '
                                           "'D9732:assignment:before-upper'\n"
                                           '  checks = checks + 1\n'
                                           '  if (lhs%tag /= 269) error stop '
                                           "'D9732:assignment:before-tag'\n"
                                           '  checks = checks + 1\n'
                                           '  if (any(lhs%part /= [271, 277, 281])) error stop '
                                           "'D9732:assignment:before-values'\n"
                                           '  checks = checks + 1\n'
                                           '  if (allocated(rhs%part)) error stop '
                                           "'D9732:assignment:rhs-unallocated'\n"
                                           '  checks = checks + 1\n'
                                           '\n'
                                           '  lhs = rhs\n'
                                           '\n'
                                           '  if (lhs%tag /= 283) error stop '
                                           "'D9732:assignment:after-tag'\n"
                                           '  checks = checks + 1\n'
                                           '  if (allocated(lhs%part)) error stop '
                                           "'D9732:assignment:after-component-unallocated'\n"
                                           '  checks = checks + 1\n'
                                           '  if (checks /= 8) error stop '
                                           "'D9732:assignment:check-total'\n"
                                           "  write(*,'(a)') 'DEALLOC INTRINSIC ASSIGNMENT "
                                           "SUBOBJECT OK'\n"
                                           'end program dealloc_intrinsic_assignment_subobject\n',
 'dealloc_procedure_local_auto': '! rule: S9.7.3.2-004\n'
                                 '! covers: ordinary-unsaved-local-deallocated\n'
                                 '! First invocation proves allocation; second invocation observes '
                                 'the unsaved local starts unallocated.\n'
                                 'module dealloc_procedure_local_auto_m\n'
                                 '  implicit none\n'
                                 '  integer :: checks = 0\n'
                                 'contains\n'
                                 '  subroutine visit(pass)\n'
                                 '    integer, intent(in) :: pass\n'
                                 '    integer, allocatable :: scratch(:)\n'
                                 '    integer :: stat\n'
                                 '    if (allocated(scratch)) error stop '
                                 "'D9732:proc-local:entry-unallocated'\n"
                                 '    checks = checks + 1\n'
                                 '    if (pass == 1) then\n'
                                 '      allocate(scratch(-4:-2), stat=stat)\n'
                                 "      if (stat /= 0) error stop 'D9732:proc-local:first-stat'\n"
                                 '      scratch = [107, 109, 113]\n'
                                 '      if (.not. allocated(scratch)) error stop '
                                 "'D9732:proc-local:first-allocated'\n"
                                 '      checks = checks + 1\n'
                                 '      if (lbound(scratch,1) /= -4) error stop '
                                 "'D9732:proc-local:first-lower'\n"
                                 '      checks = checks + 1\n'
                                 '      if (ubound(scratch,1) /= -2) error stop '
                                 "'D9732:proc-local:first-upper'\n"
                                 '      checks = checks + 1\n'
                                 '      if (any(scratch /= [107, 109, 113])) error stop '
                                 "'D9732:proc-local:first-values'\n"
                                 '      checks = checks + 1\n'
                                 '      return\n'
                                 '    end if\n'
                                 '    allocate(scratch(6:8), stat=stat)\n'
                                 "    if (stat /= 0) error stop 'D9732:proc-local:second-stat'\n"
                                 '    scratch = [127, 131, 137]\n'
                                 '    if (lbound(scratch,1) /= 6) error stop '
                                 "'D9732:proc-local:second-lower'\n"
                                 '    checks = checks + 1\n'
                                 '    if (ubound(scratch,1) /= 8) error stop '
                                 "'D9732:proc-local:second-upper'\n"
                                 '    checks = checks + 1\n'
                                 '    if (any(scratch /= [127, 131, 137])) error stop '
                                 "'D9732:proc-local:second-values'\n"
                                 '    checks = checks + 1\n'
                                 '  end subroutine visit\n'
                                 'end module dealloc_procedure_local_auto_m\n'
                                 '\n'
                                 'program dealloc_procedure_local_auto\n'
                                 '  use dealloc_procedure_local_auto_m\n'
                                 '  implicit none\n'
                                 '  call visit(1)\n'
                                 '  call visit(2)\n'
                                 "  if (checks /= 9) error stop 'D9732:proc-local:check-total'\n"
                                 "  write(*,'(a)') 'DEALLOC PROCEDURE LOCAL AUTO OK'\n"
                                 'end program dealloc_procedure_local_auto\n',
 'dealloc_saved_local_control': '! rule: S9.7.3.2-004\n'
                                '! covers: saved-local-control\n'
                                '! A SAVE allocatable is proved allocated on re-entry, contrasting '
                                'the unsaved automatic case.\n'
                                'module dealloc_saved_local_control_m\n'
                                '  implicit none\n'
                                '  integer :: checks = 0\n'
                                'contains\n'
                                '  subroutine visit(pass)\n'
                                '    integer, intent(in) :: pass\n'
                                '    integer, allocatable, save :: retained(:)\n'
                                '    integer :: stat\n'
                                '    if (pass == 1) then\n'
                                '      if (allocated(retained)) error stop '
                                "'D9732:saved-local:first-entry'\n"
                                '      checks = checks + 1\n'
                                '      allocate(retained(-8:-6), stat=stat)\n'
                                '      if (stat /= 0) error stop '
                                "'D9732:saved-local:allocate-stat'\n"
                                '      retained = [139, 149, 151]\n'
                                '      if (.not. allocated(retained)) error stop '
                                "'D9732:saved-local:before-allocated'\n"
                                '      checks = checks + 1\n'
                                '      if (lbound(retained,1) /= -8) error stop '
                                "'D9732:saved-local:before-lower'\n"
                                '      checks = checks + 1\n'
                                '      if (ubound(retained,1) /= -6) error stop '
                                "'D9732:saved-local:before-upper'\n"
                                '      checks = checks + 1\n'
                                '      if (any(retained /= [139, 149, 151])) error stop '
                                "'D9732:saved-local:before-values'\n"
                                '      checks = checks + 1\n'
                                '      return\n'
                                '    end if\n'
                                '    if (.not. allocated(retained)) error stop '
                                "'D9732:saved-local:retained-allocated'\n"
                                '    checks = checks + 1\n'
                                '    if (lbound(retained,1) /= -8) error stop '
                                "'D9732:saved-local:retained-lower'\n"
                                '    checks = checks + 1\n'
                                '    if (ubound(retained,1) /= -6) error stop '
                                "'D9732:saved-local:retained-upper'\n"
                                '    checks = checks + 1\n'
                                '    if (any(retained /= [139, 149, 151])) error stop '
                                "'D9732:saved-local:retained-values'\n"
                                '    checks = checks + 1\n'
                                '    deallocate(retained, stat=stat)\n'
                                "    if (stat /= 0) error stop 'D9732:saved-local:cleanup-stat'\n"
                                '    checks = checks + 1\n'
                                '    if (allocated(retained)) error stop '
                                "'D9732:saved-local:cleanup-unallocated'\n"
                                '    checks = checks + 1\n'
                                '  end subroutine visit\n'
                                'end module dealloc_saved_local_control_m\n'
                                '\n'
                                'program dealloc_saved_local_control\n'
                                '  use dealloc_saved_local_control_m\n'
                                '  implicit none\n'
                                '  call visit(1)\n'
                                '  call visit(2)\n'
                                "  if (checks /= 11) error stop 'D9732:saved-local:check-total'\n"
                                "  write(*,'(a)') 'DEALLOC SAVED LOCAL CONTROL OK'\n"
                                'end program dealloc_saved_local_control\n',
 'dealloc_unallocated_error': '! rule: S9.7.3.2-001\n'
                              '! covers: unallocated-allocatable-deallocate-error\n'
                              '! The object is first proved allocated with nonunit bounds and '
                              'nonzero values, then deallocated.\n'
                              'program dealloc_unallocated_error\n'
                              '  use iso_fortran_env, only: stat_stopped_image, stat_failed_image\n'
                              '  implicit none\n'
                              '  integer, allocatable :: x(:)\n'
                              '  integer :: stat, checks\n'
                              '  checks = 0\n'
                              '\n'
                              '  allocate(x(-3:-1), stat=stat)\n'
                              '  if (stat /= 0) error stop '
                              "'D9732:unallocated:initial-allocate-stat'\n"
                              '  x = [37, 41, 43]\n'
                              '  if (.not. allocated(x)) error stop '
                              "'D9732:unallocated:initial-allocated'\n"
                              '  checks = checks + 1\n'
                              '  if (lbound(x,1) /= -3) error stop '
                              "'D9732:unallocated:initial-lower'\n"
                              '  checks = checks + 1\n'
                              '  if (ubound(x,1) /= -1) error stop '
                              "'D9732:unallocated:initial-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (any(x /= [37, 41, 43])) error stop '
                              "'D9732:unallocated:initial-values'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  deallocate(x, stat=stat)\n'
                              '  if (stat /= 0) error stop '
                              "'D9732:unallocated:first-deallocate-stat'\n"
                              '  checks = checks + 1\n'
                              '  if (allocated(x)) error stop '
                              "'D9732:unallocated:first-deallocated'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  stat = -777\n'
                              '  deallocate(x, stat=stat)\n'
                              '  if (stat <= 0) error stop '
                              "'D9732:unallocated:error-stat-positive'\n"
                              '  checks = checks + 1\n'
                              '  if (stat == stat_stopped_image .or. stat == stat_failed_image) '
                              "error stop 'D9732:unallocated:error-stat-not-image'\n"
                              '  checks = checks + 1\n'
                              '  if (allocated(x)) error stop '
                              "'D9732:unallocated:remains-unallocated'\n"
                              '  checks = checks + 1\n'
                              '\n'
                              '  allocate(x(5:7), stat=stat)\n'
                              "  if (stat /= 0) error stop 'D9732:unallocated:reallocate-stat'\n"
                              '  x = [53, 59, 61]\n'
                              '  if (lbound(x,1) /= 5) error stop '
                              "'D9732:unallocated:realloc-lower'\n"
                              '  checks = checks + 1\n'
                              '  if (ubound(x,1) /= 7) error stop '
                              "'D9732:unallocated:realloc-upper'\n"
                              '  checks = checks + 1\n'
                              '  if (any(x /= [53, 59, 61])) error stop '
                              "'D9732:unallocated:realloc-values'\n"
                              '  checks = checks + 1\n'
                              "  if (checks /= 12) error stop 'D9732:unallocated:check-total'\n"
                              "  write(*,'(a)') 'DEALLOC UNALLOCATED ERROR OK'\n"
                              'end program dealloc_unallocated_error\n'}

SENTINELS = {'dealloc_allocated_control': ('[67, 71, 73]', '[67, 71, 97]', []),
 'dealloc_automatic_same_effect': ('[293, 299, 301]', '[293, 299, 359]', []),
 'dealloc_block_local_auto': ('[157, 163, 167]', '[157, 163, 191]', []),
 'dealloc_derived_subobject': ('[367, 373, 379]',
                               '[367, 373, 383]',
                               [('[3, 367, 373, 379]', '[3, 367, 373, 383]')]),
 'dealloc_function_result_retains': ('[97, 101, 103]', '[97, 101, 107]', []),
 'dealloc_intent_out_actual': ('[191, 193, 197]', '[191, 193, 229]', []),
 'dealloc_intent_out_subobject': ('[229, 233, 239]', '[229, 233, 271]', []),
 'dealloc_intrinsic_assignment_subobject': ('[271, 277, 281]', '[271, 277, 307]', []),
 'dealloc_procedure_local_auto': ('[107, 109, 113]', '[107, 109, 127]', []),
 'dealloc_saved_local_control': ('[139, 149, 151]', '[139, 149, 157]', []),
 'dealloc_unallocated_error': ('[37, 41, 43]', '[37, 41, 47]', [])}

FEATURE_MUTATION_PLAN = {'dealloc_allocated_control': [('remove-explicit-deallocate',
                                '  deallocate(x, stat=stat)\n',
                                '  ! mutation: removed DEALLOCATE(x)\n',
                                1)],
 'dealloc_automatic_same_effect': [('remove-explicit-deallocate',
                                    '  deallocate(explicit)\n',
                                    '  ! mutation: removed DEALLOCATE(explicit)\n',
                                    1),
                                   ('make-automatic-local-saved',
                                    '    integer, allocatable :: auto(:)',
                                    '    integer, allocatable, save :: auto(:)',
                                    1)],
 'dealloc_block_local_auto': [('make-block-local-saved',
                               '      integer, allocatable :: local(:)',
                               '      integer, allocatable, save :: local(:)',
                               1)],
 'dealloc_derived_subobject': [('remove-derived-deallocate',
                                '  deallocate(item, stat=stat)\n',
                                '  ! mutation: removed DEALLOCATE(item)\n',
                                1)],
 'dealloc_function_result_retains': [('deallocate-result-before-return',
                                      '    if (any(r /= [97, 101, 103])) error stop '
                                      "'D9732:function-result:result-values'\n"
                                      '  end function make_result\n',
                                      '    if (any(r /= [97, 101, 103])) error stop '
                                      "'D9732:function-result:result-values'\n"
                                      '    deallocate(r)\n'
                                      '  end function make_result\n',
                                      1)],
 'dealloc_intent_out_actual': [('intent-out-to-inout',
                                '    integer, allocatable, intent(out) :: x(:)',
                                '    integer, allocatable, intent(inout) :: x(:)',
                                1)],
 'dealloc_intent_out_subobject': [('intent-out-to-inout',
                                   '    type(holder), intent(out) :: h',
                                   '    type(holder), intent(inout) :: h',
                                   1)],
 'dealloc_intrinsic_assignment_subobject': [('remove-intrinsic-assignment',
                                             '  lhs = rhs\n',
                                             '  ! mutation: removed intrinsic assignment\n',
                                             1)],
 'dealloc_procedure_local_auto': [('make-automatic-local-saved',
                                   '    integer, allocatable :: scratch(:)',
                                   '    integer, allocatable, save :: scratch(:)',
                                   1)],
 'dealloc_saved_local_control': [('remove-save-attribute',
                                  '    integer, allocatable, save :: retained(:)',
                                  '    integer, allocatable :: retained(:)',
                                  1)],
 'dealloc_unallocated_error': [('remove-second-deallocate',
                                '  deallocate(x, stat=stat)\n',
                                '  ! mutation: removed second DEALLOCATE(x)\n',
                                2)]}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown deallocation variant")
    rule = VARIANTS[variant]["rule"]
    return rule.replace(".", "_").replace("-", "_") + "_valid__" + variant


def _nth_span(text, token, occurrence=1):
    start = -1
    pos = 0
    for _ in range(occurrence):
        start = text.find(token, pos)
        if start < 0:
            raise ValueError(f"token not found {occurrence} time(s): {token!r}")
        pos = start + len(token)
    return [start, start + len(token)]


def _mutation(variant, id_, kind, expected, replacement, occurrence=1, category=None):
    source = SOURCES[variant]
    start, end = _nth_span(source, expected, occurrence)
    return dict(
        id=id_, kind=kind, category=category or kind, expected=expected, replacement=replacement,
        occurrence=occurrence, span=[start, end], line=source[:start].count("\n") + 1)


def _first_check_omission(variant):
    text = SOURCES[variant]
    expected = "  checks = checks + 1\n"
    start, end = _nth_span(text, expected, 1)
    return dict(
        id="omit-first-check-increment", kind="omission", category="omission",
        expected=expected, replacement="  ! mutation: omitted first check sentinel increment\n",
        occurrence=1, span=[start, end], line=text[:start].count("\n") + 1)


def source_specs():
    specs = {}
    for variant, meta in VARIANTS.items():
        source = SOURCES[variant]
        raw = source.encode("ascii")
        sentinel, replacement, extra_reverse = SENTINELS[variant]
        oracle = _mutation(variant, "oracle-corrupt-primary-sentinel", "oracle", sentinel, replacement, 2)
        input_ = _mutation(variant, "input-corrupt-primary-sentinel", "input", sentinel, replacement, 1)
        omissions = [_first_check_omission(variant)]
        features = [
            _mutation(variant, id_, "feature", expected, repl, occurrence, "feature-level")
            for id_, expected, repl, occurrence in FEATURE_MUTATION_PLAN[variant]
        ]
        replacements = [dict(expected=sentinel, replacement=replacement, all=True)]
        replacements.extend(dict(expected=old, replacement=new, all=True) for old, new in extra_reverse)
        reverse = [dict(id="reverse-primary-sentinel", kind="reverse", category="reverse", replacements=replacements)]
        specs[identifier(variant)] = dict(
            id=identifier(variant), variant=variant, rule=meta["rule"], facets=meta["facets"],
            evidence=meta["evidence"], standard="f2023", phase="run", source=source,
            source_sha256=sha(raw), completion=meta["completion"], oracle_mutations=[oracle],
            input_mutations=[input_], omissions=omissions, feature_mutations=features,
            reverse_mutations=reverse)
    return specs


def mutated_source(spec, mutation):
    if mutation.get("kind") == "reverse":
        text = spec["source"]
        for item in mutation["replacements"]:
            count = -1 if item.get("all") else 1
            if item["expected"] not in text:
                raise ValueError("reverse mutation token not found")
            text = text.replace(item["expected"], item["replacement"], count)
        return text.encode("ascii")
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def failing_mutations(spec):
    return spec["oracle_mutations"] + spec["input_mutations"] + spec["omissions"] + spec["feature_mutations"]


def all_mutations(spec):
    return failing_mutations(spec) + spec["reverse_mutations"]


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = root / "tests/fixtures" / spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0,
                        stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def mutation_counts(specs):
    return dict(
        cases=len(specs), facets=sum(len(spec["facets"]) for spec in specs.values()),
        failing_mutations=sum(len(failing_mutations(spec)) for spec in specs.values()),
        feature_mutations=sum(len(spec["feature_mutations"]) for spec in specs.values()),
        reverse_controls=sum(len(spec["reverse_mutations"]) for spec in specs.values()))


def generate(root=ROOT, check=False):
    root = Path(root)
    files, specs = build_corpus(root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if stale:
            raise ValueError("stale deallocation fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
    return specs


def summary_line(checked, specs):
    counts = mutation_counts(specs)
    action = "Checked" if checked else "Generated"
    return (f"{action} {counts['cases']} deallocation cases, {counts['facets']} facets, "
            f"{counts['failing_mutations']} failing mutations "
            f"({counts['feature_mutations']} feature-level) and "
            f"{counts['reverse_controls']} reverse controls.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    specs = generate(args.root, args.check)
    print(summary_line(args.check, specs))


if __name__ == "__main__":
    main()
