#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 scope and local identifier rules in 19.1-19.3.4."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "scoping_19_1_19_3"
FIXTURE_ROOT = Path("tests/fixtures") / TOPIC
SUMMARY = "SCOPING 19.1-19.3"

CATALOGUES = {
    "19.1": "doc/catalogues/scope_identifiers_entities_19_1.json",
    "19.3.1": "doc/catalogues/classes_of_local_identifiers_19_3_1.json",
    "19.3.2": "doc/catalogues/common_block_local_identifiers_19_3_2.json",
    "19.3.3": "doc/catalogues/function_results_19_3_3.json",
    "19.3.4": "doc/catalogues/components_type_parameters_bindings_19_3_4.json",
}

FACETS_BY_RULE = {
    "S19.1-002": [
        "local-identifier-inclusive-scope",
        "construct-identifier-construct-scope",
        "statement-identifier-statement-scope",
        "nested-scope-shadowing-exclusion",
    ],
    "S19.1-004": [
        "same-identifier-different-scope-association",
        "different-identifier-different-scope-association",
    ],
    "S19.3.1-001": [
        "per-type-class-two-local-identifiers",
        "per-procedure-argument-keyword-local-identifiers",
    ],
    "S19.3.1-003": [
        "use-rename-use-name-exception",
        "common-block-name-exception",
        "external-procedure-generic-name-exception",
        "external-function-defining-subprogram-exception",
    ],
    "S19.3.1-005": [
        "generic-name-same-as-procedure",
        "generic-name-same-as-derived-type",
        "different-local-classes-same-spelling",
    ],
    "S19.3.1-006": ["local-identifier-reuse-in-another-scope"],
    "S19.3.1-007": ["function-name-result-recursion-common-block-use"],
    "S19.3.2-002": ["common-block-homonym-local-reference"],
    "S19.3.3-001": [
        "function-statement-result-exists",
        "function-result-variable-or-procedure-pointer",
        "function-result-name-class-one-local",
    ],
    "S19.3.4-001": [
        "component-name-type-definition-scope",
        "component-name-designator-use",
        "component-keyword-structure-constructor-use",
    ],
    "S19.3.4-002": [
        "type-parameter-name-type-definition-scope",
        "type-parameter-keyword-use",
        "type-parameter-inquiry-use",
    ],
    "S19.3.4-003": [
        "binding-name-type-definition-scope",
        "binding-name-procedure-reference-use",
    ],
    "S19.3.4-004": ["nongeneric-spec-generic-binding-accessible-scope"],
}

ORACLE_PREFIXES = {
    "S19.1-002": "S19.1-002 scope runtime fixtures: ",
    "S19.1-004": "S19.1-004 association identifier runtime fixtures: ",
    "S19.3.1-001": "S19.3.1-001 local-identifier class runtime fixtures: ",
    "S19.3.1-003": "S19.3.1-003 global/local exception runtime fixtures: ",
    "S19.3.1-005": "S19.3.1-005 local class homonym runtime fixtures: ",
    "S19.3.1-006": "S19.3.1-006 other-scope reuse runtime fixture: ",
    "S19.3.1-007": "S19.3.1-007 function-name limited-use runtime fixture: ",
    "S19.3.2-002": "S19.3.2-002 common-block homonym runtime fixture: ",
    "S19.3.3-001": "S19.3.3-001 function-result runtime fixture: ",
    "S19.3.4-001": "S19.3.4-001 component-name runtime fixture: ",
    "S19.3.4-002": "S19.3.4-002 type-parameter runtime fixture: ",
    "S19.3.4-003": "S19.3.4-003 binding-name runtime fixture: ",
    "S19.3.4-004": "S19.3.4-004 nongeneric binding runtime fixture: ",
}
LIMIT_PREFIXES = {rule: prefix.replace(" runtime fixture", " fixture boundaries").replace(" runtime fixtures", " fixture boundaries") for rule, prefix in ORACLE_PREFIXES.items()}

ORACLES = {
    "S19.1-002": ORACLE_PREFIXES["S19.1-002"] + (
        "two complete run/effect/f2023 programs observe local scope boundaries with nondefault sentinels. "
        "The host/rename fixture initializes host token=41, has one internal procedure read that same spelling by host "
        "association, and has a second internal procedure declare a local token=73; it checks host_seen=41, "
        "inner_seen=73, and the host token still 41. The construct fixture initializes outer i=99, uses "
        "ASSOCIATE (i=>construct_source) to write [10,20,30], and uses an array-constructor implied-DO [(i,i=1,3)]; "
        "it checks both produced arrays and that outer i remains 99. Feature mutations add/remove the shadowing "
        "declaration, redirect the associate name to a wrong target, and replace the implied-DO with outer-i references."
    ),
    "S19.1-004": ORACLE_PREFIXES["S19.1-004"] + (
        "one complete run/effect/f2023 program observes association names with distinct wrong-resolution sentinels. "
        "An internal procedure reads the host variable token=41 by the same identifier. A USE rename imports "
        "source_name=52 as local_name while a separate local source_name=99 exists in the user scope; local_name, "
        "source_name, and token are all checked separately. A feature mutation redirects the rename to wrong_global=77."
    ),
    "S19.3.1-001": ORACLE_PREFIXES["S19.3.1-001"] + (
        "one run/effect/f2023 program covers the class (3) per-procedure argument-keyword facet. It defines two "
        "explicit-interface module procedures with the same dummy keyword names, calls each with reversed keyword "
        "order, and observes distinct arithmetic results. Class (1), class (2), and binding-label common-block "
        "taxonomy facets remain pending rather than being inferred from partial examples."
    ),
    "S19.3.1-003": ORACLE_PREFIXES["S19.3.1-003"] + (
        "four complete programs exercise each listed exception with distinct sentinels: USE local_name=>source_name "
        "beside a local source_name=99; common /blk/ storage cb_member=29 beside local blk=17; external generic "
        "chooser that has the same name as its specific external function and returns 47; and an external function whose "
        "defining subprogram assigns its function-name result variable."
    ),
    "S19.3.1-005": ORACLE_PREFIXES["S19.3.1-005"] + (
        "three complete programs observe the admitted cross-class homonyms. The external generic chooser shares a "
        "name with its specific function and returns 47. The generic/type fixture has derived type node and generic "
        "interface node; node(5) returns a constructor-like value 75 through the generic while node(v=31) constructs "
        "the type. The different-class fixture keeps an outer variable tag=99 while object%tag observes the component "
        "identifier with the same spelling."
    ),
    "S19.3.1-006": ORACLE_PREFIXES["S19.3.1-006"] + (
        "the host/shadow fixture reuses token in a contained subprogram. It observes inner token=73, then observes "
        "the host token remains 41 after return, so a mistaken single binding for both scopes is detected."
    ),
    "S19.3.1-007": ORACLE_PREFIXES["S19.3.1-007"] + (
        "the function-result fixture calls an external function that assigns its function-name result variable, and "
        "a recursive external function with an explicit RESULT variable that uses the function name as a recursive "
        "reference. Exact results 47 and 28 distinguish result assignment from recursive reference resolution."
    ),
    "S19.3.2-002": ORACLE_PREFIXES["S19.3.2-002"] + (
        "one complete program declares COMMON /blk/ cb_member and a local integer blk. It initializes cb_member=29 "
        "and blk=17, evaluates ordinary expression blk+1 expecting 18, and checks cb_member remains 29, proving "
        "ordinary occurrences resolve to the local identifier rather than the common block."
    ),
    "S19.3.3-001": ORACLE_PREFIXES["S19.3.3-001"] + (
        "one complete program calls external integer function scope_result, whose defining subprogram initializes "
        "and assigns the function-name result variable and returns 47. A second recursive function uses RESULT(answer) "
        "and a function-name recursive reference to return 28. The ordinary function result is a variable local "
        "identifier of class (1); no procedure-pointer result or ENTRY result is claimed."
    ),
    "S19.3.4-001": ORACLE_PREFIXES["S19.3.4-001"] + (
        "one complete program defines type_one and type_two, each with component tag, and keeps an outer tag=99. "
        "It checks left%tag=11 and right%tag=22, reads obj%tag=31, constructs type_one(tag=44), and verifies the "
        "outer tag remains 99. Feature mutations swap a designator to the outer variable, choose the other type's "
        "component value, and replace the constructor component keyword by a different component keyword."
    ),
    "S19.3.4-002": ORACLE_PREFIXES["S19.3.4-002"] + (
        "one complete program declares a parameterized derived type box(k) with kind type parameter k and component "
        "integer(kind=k) value. In a scope with ordinary integer k=99, it declares type(box(k=kind(0))) b, assigns "
        "b%value=123, and checks b%k, kind(b%value), int(b%value), and the outer k sentinel."
    ),
    "S19.3.4-003": ORACLE_PREFIXES["S19.3.4-003"] + (
        "one module type binds procedure calc=>calc_impl. A user scope declares an ordinary integer calc=99 and "
        "an object with base=60; obj%calc() returns 64 while the ordinary variable calc remains 99. A feature "
        "mutation redirects the binding name to a same-interface wrong implementation returning 91."
    ),
    "S19.3.4-004": ORACLE_PREFIXES["S19.3.4-004"] + (
        "one module type has a nongeneric-spec generic binding operator(+). A user scope with two accessible box "
        "objects computes left+right and checks result%v=67. The specific binding computes 10*left+right, making "
        "ordinary numeric addition, reversed operands, or a redirected generic binding observable."
    ),
}

LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "only the listed single-image positive runtime effects are claimed. Source-use taxonomy facets, image/coarray "
        "forms, IMPORT inaccessibility, processor-assigned globals, binding-label uniqueness, inaccessible PRIVATE "
        "component/binding restrictions, ENTRY results, procedure-pointer result association, and unnumbered same-name "
        "program restrictions without required diagnostics remain pending with their existing source-derived reasons. "
        "No fixture asserts diagnostic text, addresses, storage layout, I/O formatting, real rounding, or compiler consensus."
    ) for rule in ORACLE_PREFIXES
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    rule = CASES[variant]["rule"]
    return rule.replace(".", "_").replace("-", "_") + "_valid__scoping_19_1_19_3_" + variant


def completion(variant):
    return f"{SUMMARY} {variant.upper().replace('_', ' ')} OK\n"


def source_header(rule, facets, evidence="effect"):
    return (
        f"! rule: {rule}\n"
        f"! covers: {' '.join(facets)}\n"
        f"! evidence: {evidence}\n"
        "! standard: f2023\n"
        "! oracle-basis: standard\n"
    )


PROGRAMS = {
"host_rename_shadow": r'''module scoping_rename_provider
  implicit none
  integer :: source_name = 52
  integer :: wrong_global = 77
end module scoping_rename_provider
program scoping_host_rename_shadow
  use scoping_rename_provider, only: local_name => source_name, wrong_global
  implicit none
  integer :: token, source_name, host_seen, inner_seen, checks
  token = 41
  source_name = 99
  host_seen = -11
  inner_seen = -12
  checks = 0
  call read_host_token()
  call read_shadow_token()
  call expect_equal(host_seen, 41, 'host association same identifier')
  call expect_equal(inner_seen, 73, 'nested local identifier')
  call expect_equal(token, 41, 'host token unchanged')
  call expect_equal(local_name, 52, 'use rename associated value')
  call expect_equal(source_name, 99, 'local use-name homonym unchanged')
  call expect_equal(checks, 5, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 HOST RENAME SHADOW OK'
contains
  subroutine read_host_token()
    implicit none
    host_seen = token
  end subroutine read_host_token
  subroutine read_shadow_token()
    implicit none
    integer :: token
    token = 73
    inner_seen = token
  end subroutine read_shadow_token
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_host_rename_shadow
''',
"construct_statement_entities": r'''program scoping_construct_statement_entities
  implicit none
  integer :: i, checks
  integer :: concurrent_values(3), implied_values(3), construct_source(3), wrong_source(3)
  i = 99
  checks = 0
  concurrent_values = -7
  construct_source = [1, 2, 3]
  wrong_source = [7, 8, 9]
  associate (i => construct_source)
    concurrent_values = i * 10
  end associate
  implied_values = [(i, i = 1, 3)]
  call expect_equal(concurrent_values(1), 10, 'do concurrent first')
  call expect_equal(concurrent_values(2), 20, 'do concurrent second')
  call expect_equal(concurrent_values(3), 30, 'do concurrent third')
  call expect_equal(implied_values(1), 1, 'implied do first')
  call expect_equal(implied_values(2), 2, 'implied do second')
  call expect_equal(implied_values(3), 3, 'implied do third')
  call expect_equal(i, 99, 'outer i sentinel')
  call expect_equal(checks, 7, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 CONSTRUCT STATEMENT ENTITIES OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_construct_statement_entities
''',
"common_block_homonym": r'''program scoping_common_block_homonym
  implicit none
  integer :: cb_member
  common /blk/ cb_member
  integer :: blk, ordinary, checks
  cb_member = 29
  blk = 17
  checks = 0
  ordinary = blk + 1
  call expect_equal(ordinary, 18, 'ordinary local blk expression')
  call expect_equal(cb_member, 29, 'common member unchanged')
  call expect_equal(blk, 17, 'local blk unchanged')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 COMMON BLOCK HOMONYM OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_common_block_homonym
''',
"external_generic_same_name": r'''program scoping_external_generic_same_name
  implicit none
  interface chooser
    integer function chooser(x)
      integer, intent(in) :: x
    end function chooser
  end interface
  integer :: checks
  checks = 0
  call expect_equal(chooser(5), 47, 'generic external same name')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 EXTERNAL GENERIC SAME NAME OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_external_generic_same_name
integer function chooser(x)
  implicit none
  integer, intent(in) :: x
  chooser = 42 + x
end function chooser
''',
"function_results": r'''program scoping_function_results
  implicit none
  interface
    integer function scope_result(n)
      integer, intent(in) :: n
    end function scope_result
    recursive integer function scope_recur(n) result(answer)
      integer, intent(in) :: n
    end function scope_recur
  end interface
  integer :: scope_result_sentinel, checks
  scope_result_sentinel = -300
  checks = 0
  call expect_equal(scope_result(5), 47, 'function-name result variable')
  call expect_equal(scope_recur(2), 28, 'function-name recursive reference')
  call expect_equal(scope_result_sentinel, -300, 'caller sentinel unchanged')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 FUNCTION RESULTS OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_function_results
integer function scope_result(n)
  implicit none
  integer, intent(in) :: n
  scope_result = -90
  scope_result = 42 + n
end function scope_result
recursive integer function scope_recur(n) result(answer)
  implicit none
  integer, intent(in) :: n
  if (n == 0) then
    answer = 8
  else
    answer = scope_recur(n - 1) + 10
  end if
end function scope_recur
''',
"components": r'''program scoping_components
  implicit none
  type :: type_one
    integer :: tag = -123
    integer :: other = -456
  end type type_one
  type :: type_two
    integer :: tag = -222
  end type type_two
  type(type_one) :: left, obj, built
  type(type_two) :: right
  integer :: tag, selected, mixed_sum, checks
  tag = 99
  checks = 0
  left%tag = 11
  left%other = 101
  right%tag = 22
  obj%tag = 31
  selected = obj%tag
  built = type_one(tag=44)
  mixed_sum = left%tag + right%tag
  call expect_equal(left%tag, 11, 'type one component')
  call expect_equal(right%tag, 22, 'type two component')
  call expect_equal(mixed_sum, 33, 'per-type component names')
  call expect_equal(selected, 31, 'component designator')
  call expect_equal(built%tag, 44, 'constructor keyword tag')
  call expect_equal(tag, 99, 'outer tag unchanged')
  call expect_equal(checks, 6, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 COMPONENTS OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_components
''',
"argument_keywords": r'''module scoping_argument_keyword_mod
  implicit none
contains
  integer function first_proc(item, other)
    integer, intent(in) :: item, other
    first_proc = item * 10 + other
  end function first_proc
  integer function second_proc(item, other)
    integer, intent(in) :: item, other
    second_proc = item * 100 + other
  end function second_proc
end module scoping_argument_keyword_mod
program scoping_argument_keywords
  use scoping_argument_keyword_mod, only: first_proc, second_proc
  implicit none
  integer :: checks
  checks = 0
  call expect_equal(first_proc(other=7, item=3), 37, 'first procedure keyword class')
  call expect_equal(second_proc(other=8, item=4), 408, 'second procedure keyword class')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 ARGUMENT KEYWORDS OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_argument_keywords
''',
"generic_derived_type": r'''module scoping_generic_derived_type_mod
  implicit none
  type :: node
    integer :: v
  end type node
  interface node
    module procedure make_node
  end interface node
contains
  type(node) function make_node(x)
    integer, intent(in) :: x
    make_node%v = x + 70
  end function make_node
end module scoping_generic_derived_type_mod
program scoping_generic_derived_type
  use scoping_generic_derived_type_mod, only: node
  implicit none
  type(node) :: from_generic, from_constructor
  integer :: checks
  checks = 0
  from_generic = node(5)
  from_constructor = node(v=31)
  call expect_equal(from_generic%v, 75, 'generic name same as derived type')
  call expect_equal(from_constructor%v, 31, 'structure constructor keyword')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 GENERIC DERIVED TYPE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_generic_derived_type
''',
"type_parameters": r'''program scoping_type_parameters
  implicit none
  integer, parameter :: default_k = kind(0)
  type :: box(k)
    integer, kind :: k
    integer(kind=k) :: value
  end type box
  type(box(k=default_k)) :: b
  integer :: k, checks
  k = 99
  checks = 0
  b%value = 123
  call expect_equal(b%k, default_k, 'type parameter inquiry')
  call expect_equal(kind(b%value), default_k, 'type parameter definition scope')
  call expect_equal(int(b%value), 123, 'component value')
  call expect_equal(k, 99, 'outer k unchanged')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 TYPE PARAMETERS OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_type_parameters
''',
"binding_reference": r'''module scoping_binding_reference_mod
  implicit none
  private
  public :: box
  type :: box
    integer :: base
  contains
    procedure :: calc => calc_impl
  end type box
contains
  integer function calc_impl(self)
    class(box), intent(in) :: self
    calc_impl = self%base + 4
  end function calc_impl
  integer function wrong_calc_impl(self)
    class(box), intent(in) :: self
    wrong_calc_impl = self%base + 31
  end function wrong_calc_impl
end module scoping_binding_reference_mod
program scoping_binding_reference
  use scoping_binding_reference_mod, only: box
  implicit none
  type(box) :: obj
  integer :: calc, checks
  obj%base = 60
  calc = 99
  checks = 0
  call expect_equal(obj%calc(), 64, 'type-bound binding reference')
  call expect_equal(calc, 99, 'outer calc unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 BINDING REFERENCE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_binding_reference
''',
"generic_binding_operator": r'''module scoping_generic_binding_operator_mod
  implicit none
  private
  public :: box
  type :: box
    integer :: v
  contains
    procedure :: add_box
    procedure :: wrong_add_box
    generic :: operator(+) => add_box
  end type box
contains
  type(box) function add_box(left, right)
    class(box), intent(in) :: left
    type(box), intent(in) :: right
    add_box%v = left%v * 10 + right%v
  end function add_box
  type(box) function wrong_add_box(left, right)
    class(box), intent(in) :: left
    type(box), intent(in) :: right
    wrong_add_box%v = left%v + right%v
  end function wrong_add_box
end module scoping_generic_binding_operator_mod
program scoping_generic_binding_operator
  use scoping_generic_binding_operator_mod, only: box
  implicit none
  type(box) :: left, right, combined
  integer :: checks
  checks = 0
  left%v = 6
  right%v = 7
  combined = left + right
  call expect_equal(combined%v, 67, 'generic binding operator plus')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 GENERIC BINDING OPERATOR OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_generic_binding_operator
''',
}

CASES = {
    "host_rename_shadow": dict(rule="S19.1-004", facets=[
        "same-identifier-different-scope-association", "different-identifier-different-scope-association",
        "local-identifier-inclusive-scope", "nested-scope-shadowing-exclusion",
        "use-rename-use-name-exception", "local-identifier-reuse-in-another-scope"],
        extra_rules=["S19.1-002", "S19.3.1-003", "S19.3.1-006"]),
    "construct_statement_entities": dict(rule="S19.1-002", facets=[
        "construct-identifier-construct-scope", "statement-identifier-statement-scope"]),
    "common_block_homonym": dict(rule="S19.3.2-002", facets=[
        "common-block-homonym-local-reference", "common-block-name-exception"], extra_rules=["S19.3.1-003"]),
    "external_generic_same_name": dict(rule="S19.3.1-003", facets=[
        "external-procedure-generic-name-exception", "generic-name-same-as-procedure"], extra_rules=["S19.3.1-005"]),
    "function_results": dict(rule="S19.3.3-001", facets=[
        "function-statement-result-exists", "function-result-variable-or-procedure-pointer",
        "function-result-name-class-one-local", "external-function-defining-subprogram-exception",
        "function-name-result-recursion-common-block-use"], extra_rules=["S19.3.1-003", "S19.3.1-007"]),
    "components": dict(rule="S19.3.4-001", facets=[
        "component-name-type-definition-scope", "component-name-designator-use",
        "component-keyword-structure-constructor-use", "different-local-classes-same-spelling",
        "per-type-class-two-local-identifiers"], extra_rules=["S19.3.1-005", "S19.3.1-001"]),
    "argument_keywords": dict(rule="S19.3.1-001", facets=["per-procedure-argument-keyword-local-identifiers"]),
    "generic_derived_type": dict(rule="S19.3.1-005", facets=["generic-name-same-as-derived-type"]),
    "type_parameters": dict(rule="S19.3.4-002", facets=[
        "type-parameter-name-type-definition-scope", "type-parameter-keyword-use",
        "type-parameter-inquiry-use", "per-type-class-two-local-identifiers"], extra_rules=["S19.3.1-001"]),
    "binding_reference": dict(rule="S19.3.4-003", facets=[
        "binding-name-type-definition-scope", "binding-name-procedure-reference-use",
        "per-type-class-two-local-identifiers"], extra_rules=["S19.3.1-001"]),
    "generic_binding_operator": dict(rule="S19.3.4-004", facets=["nongeneric-spec-generic-binding-accessible-scope"]),
}

MUTATIONS = {
    "host_rename_shadow": [
        dict(id="rename-to-wrong-global", kind="feature", replacements=[("local_name => source_name", "local_name => wrong_global")]),
        dict(id="host-read-shadowed", kind="feature", replacements=[(
            "  subroutine read_host_token()\n    implicit none\n    host_seen = token\n  end subroutine read_host_token",
            "  subroutine read_host_token()\n    implicit none\n    integer :: token\n    token = 74\n    host_seen = token\n  end subroutine read_host_token")]),
        dict(id="remove-inner-shadow-declaration", kind="feature", replacements=[("    integer :: token\n    token = 73", "    ! shadow declaration removed by mutation\n    token = 73")]),
        dict(id="outer-sentinel", kind="input", replacements=[("  token = 41", "  token = 40")]),
        dict(id="local-use-name-sentinel", kind="input", replacements=[("  source_name = 99", "  source_name = 98")]),
    ],
    "construct_statement_entities": [
        dict(id="associate-wrong-target", kind="feature", replacements=[("associate (i => construct_source)", "associate (i => wrong_source)")]),
        dict(id="remove-implied-do", kind="feature", replacements=[("implied_values = [(i, i = 1, 3)]", "implied_values = [i, i, i]")]),
        dict(id="outer-i-sentinel", kind="input", replacements=[("  i = 99", "  i = 98")]),
    ],
    "common_block_homonym": [
        dict(id="ordinary-expression-uses-common-member", kind="feature", replacements=[("ordinary = blk + 1", "ordinary = cb_member + 1")]),
        dict(id="common-storage-sentinel", kind="input", replacements=[("  cb_member = 29", "  cb_member = 28")]),
        dict(id="local-blk-sentinel", kind="input", replacements=[("  blk = 17", "  blk = 16")]),
    ],
    "external_generic_same_name": [
        dict(id="generic-specific-renamed", kind="feature", replacements=[
            ("integer function chooser(x)\n      integer, intent(in) :: x\n    end function chooser", "integer function chooser_alt(x)\n      integer, intent(in) :: x\n    end function chooser_alt"),
            ("integer function chooser(x)\n  implicit none\n  integer, intent(in) :: x\n  chooser = 42 + x\nend function chooser", "integer function chooser_alt(x)\n  implicit none\n  integer, intent(in) :: x\n  chooser_alt = 99 + x\nend function chooser_alt"),
        ]),
        dict(id="specific-body-sentinel", kind="input", replacements=[("chooser = 42 + x", "chooser = 43 + x")]),
    ],
    "function_results": [
        dict(id="result-assignment-left-at-sentinel", kind="feature", replacements=[("  scope_result = 42 + n", "  ! result assignment removed by mutation")]),
        dict(id="recursive-step-wrong", kind="feature", replacements=[("answer = scope_recur(n - 1) + 10", "answer = scope_recur(n - 1) + 11")]),
        dict(id="caller-sentinel", kind="input", replacements=[("  scope_result_sentinel = -300", "  scope_result_sentinel = -301")]),
    ],
    "components": [
        dict(id="designator-uses-outer", kind="feature", replacements=[("selected = obj%tag", "selected = tag")]),
        dict(id="per-type-selection-duplicates-left", kind="feature", replacements=[("mixed_sum = left%tag + right%tag", "mixed_sum = left%tag + left%tag")]),
        dict(id="constructor-keyword-other", kind="feature", replacements=[("built = type_one(tag=44)", "built = type_one(other=44)")]),
        dict(id="outer-tag-sentinel", kind="input", replacements=[("  tag = 99", "  tag = 98")]),
    ],
    "argument_keywords": [
        dict(id="first-keywords-to-positional", kind="feature", replacements=[("first_proc(other=7, item=3)", "first_proc(7, 3)")]),
        dict(id="second-keywords-to-positional", kind="feature", replacements=[("second_proc(other=8, item=4)", "second_proc(8, 4)")]),
        dict(id="first-item-sentinel", kind="input", replacements=[("item=3", "item=2")]),
    ],
    "generic_derived_type": [
        dict(id="generic-call-becomes-constructor", kind="feature", replacements=[("from_generic = node(5)", "from_generic = node(v=5)")]),
        dict(id="constructor-sentinel", kind="input", replacements=[("from_constructor = node(v=31)", "from_constructor = node(v=30)")]),
    ],
    "type_parameters": [
        dict(id="type-param-keyword-different-kind", kind="feature", replacements=[("type(box(k=default_k)) :: b", "type(box(k=selected_int_kind(12))) :: b")]),
        dict(id="outer-k-sentinel", kind="input", replacements=[("  k = 99", "  k = 98")]),
    ],
    "binding_reference": [
        dict(id="binding-redirected", kind="feature", replacements=[("procedure :: calc => calc_impl", "procedure :: calc => wrong_calc_impl")]),
        dict(id="outer-calc-sentinel", kind="input", replacements=[("  calc = 99", "  calc = 98")]),
        dict(id="object-base-sentinel", kind="input", replacements=[("  obj%base = 60", "  obj%base = 61")]),
    ],
    "generic_binding_operator": [
        dict(id="generic-binding-redirected", kind="feature", replacements=[("generic :: operator(+) => add_box", "generic :: operator(+) => wrong_add_box")]),
        dict(id="left-sentinel", kind="input", replacements=[("  left%v = 6", "  left%v = 5")]),
        dict(id="right-sentinel", kind="input", replacements=[("  right%v = 7", "  right%v = 8")]),
    ],
}

# The suite manifest schema binds one fixture to one owning rule.  The larger
# programs above intentionally contain wrong-resolution sentinels for nearby
# rules, but only the owning-rule facets below are claimed by each manifest.
FACETS_BY_RULE = {
    "S19.1-002": [
        "local-identifier-inclusive-scope",
        "construct-identifier-construct-scope",
        "statement-identifier-statement-scope",
        "nested-scope-shadowing-exclusion",
    ],
    "S19.1-004": [
        "same-identifier-different-scope-association",
        "different-identifier-different-scope-association",
    ],
    "S19.3.1-001": ["per-procedure-argument-keyword-local-identifiers"],
    "S19.3.1-003": [
        "use-rename-use-name-exception",
        "common-block-name-exception",
        "external-procedure-generic-name-exception",
        "external-function-defining-subprogram-exception",
    ],
    "S19.3.1-005": [
        "generic-name-same-as-procedure",
        "generic-name-same-as-derived-type",
        "different-local-classes-same-spelling",
    ],
    "S19.3.1-006": ["local-identifier-reuse-in-another-scope"],
    "S19.3.2-002": ["common-block-homonym-local-reference"],
    "S19.3.3-001": [
        "function-statement-result-exists",
        "function-result-name-class-one-local",
    ],
    "S19.3.4-001": [
        "component-name-type-definition-scope",
        "component-name-designator-use",
        "component-keyword-structure-constructor-use",
    ],
    "S19.3.4-002": [
        "type-parameter-name-type-definition-scope",
        "type-parameter-keyword-use",
        "type-parameter-inquiry-use",
    ],
    "S19.3.4-003": [
        "binding-name-type-definition-scope",
        "binding-name-procedure-reference-use",
    ],
    "S19.3.4-004": ["nongeneric-spec-generic-binding-accessible-scope"],
}

PROGRAMS.update({
"association_rename": r'''module scoping_association_rename_mod
  implicit none
  integer :: source_name = 52
  integer :: wrong_global = 77
end module scoping_association_rename_mod
program scoping_association_rename
  use scoping_association_rename_mod, only: local_name => source_name, wrong_global
  implicit none
  integer :: token, source_name, host_seen, checks
  token = 41
  source_name = 99
  host_seen = -11
  checks = 0
  call read_host_token()
  call expect_equal(host_seen, 41, 'same identifier host association')
  call expect_equal(local_name, 52, 'different identifier use rename')
  call expect_equal(source_name, 99, 'local use-name sentinel')
  call expect_equal(token, 41, 'host token unchanged')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 ASSOCIATION RENAME OK'
contains
  subroutine read_host_token()
    implicit none
    host_seen = token
  end subroutine read_host_token
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_association_rename
''',
"use_rename_exception": r'''module scoping_use_rename_exception_mod
  implicit none
  integer :: source_name = 52
  integer :: wrong_global = 77
end module scoping_use_rename_exception_mod
program scoping_use_rename_exception
  use scoping_use_rename_exception_mod, only: local_name => source_name, wrong_global
  implicit none
  integer :: source_name, checks
  source_name = 99
  checks = 0
  call expect_equal(local_name, 52, 'use-name in rename')
  call expect_equal(source_name, 99, 'local homonym for use-name')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 USE RENAME EXCEPTION OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_use_rename_exception
''',
"common_block_exception": r'''program scoping_common_block_exception
  implicit none
  integer :: cb_member
  common /blk/ cb_member
  integer :: blk, checks
  cb_member = 29
  blk = 17
  checks = 0
  call expect_equal(blk, 17, 'local blk ordinary occurrence')
  call expect_equal(cb_member, 29, 'common block storage')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 COMMON BLOCK EXCEPTION OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_common_block_exception
''',
"function_exception": r'''program scoping_function_exception
  implicit none
  interface
    integer function scope_result(n)
      integer, intent(in) :: n
    end function scope_result
  end interface
  integer :: checks
  checks = 0
  call expect_equal(scope_result(5), 47, 'external function name in defining subprogram')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 FUNCTION EXCEPTION OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_function_exception
integer function scope_result(n)
  implicit none
  integer, intent(in) :: n
  scope_result = -90
  scope_result = 42 + n
end function scope_result
''',
"generic_procedure_homonym": PROGRAMS["external_generic_same_name"].replace(
    "EXTERNAL GENERIC SAME NAME", "GENERIC PROCEDURE HOMONYM").replace(
    "scoping_external_generic_same_name", "scoping_generic_procedure_homonym"),
"different_classes_homonym": r'''program scoping_different_classes_homonym
  implicit none
  type :: box
    integer :: tag
  end type box
  type(box) :: obj
  integer :: tag, checks
  tag = 99
  obj%tag = 31
  checks = 0
  call expect_equal(obj%tag, 31, 'component tag class')
  call expect_equal(tag, 99, 'ordinary local tag class')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 DIFFERENT CLASSES HOMONYM OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_different_classes_homonym
''',
"other_scope_reuse": r'''program scoping_other_scope_reuse
  implicit none
  integer :: token, inner_seen, checks
  token = 41
  inner_seen = -12
  checks = 0
  call read_shadow_token()
  call expect_equal(inner_seen, 73, 'reused local identifier')
  call expect_equal(token, 41, 'outer token unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 OTHER SCOPE REUSE OK'
contains
  subroutine read_shadow_token()
    implicit none
    integer :: token
    token = 73
    inner_seen = token
  end subroutine read_shadow_token
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_other_scope_reuse
''',
"function_name_limited": r'''program scoping_function_name_limited
  implicit none
  interface
    recursive integer function scope_recur(n) result(answer)
      integer, intent(in) :: n
    end function scope_recur
  end interface
  integer :: checks
  checks = 0
  call expect_equal(scope_recur(2), 28, 'function name recursive reference')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 FUNCTION NAME LIMITED OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_function_name_limited
recursive integer function scope_recur(n) result(answer)
  implicit none
  integer, intent(in) :: n
  if (n == 0) then
    answer = 8
  else
    answer = scope_recur(n - 1) + 10
  end if
end function scope_recur
''',
})

CASES = {
    "host_rename_shadow": dict(rule="S19.1-002", facets=[
        "local-identifier-inclusive-scope", "nested-scope-shadowing-exclusion"]),
    "construct_statement_entities": dict(rule="S19.1-002", facets=[
        "construct-identifier-construct-scope", "statement-identifier-statement-scope"]),
    "association_rename": dict(rule="S19.1-004", facets=[
        "same-identifier-different-scope-association", "different-identifier-different-scope-association"]),
    "argument_keywords": dict(rule="S19.3.1-001", facets=["per-procedure-argument-keyword-local-identifiers"]),
    "use_rename_exception": dict(rule="S19.3.1-003", facets=["use-rename-use-name-exception"]),
    "common_block_exception": dict(rule="S19.3.1-003", facets=["common-block-name-exception"]),
    "external_generic_same_name": dict(rule="S19.3.1-003", facets=["external-procedure-generic-name-exception"]),
    "function_exception": dict(rule="S19.3.1-003", facets=["external-function-defining-subprogram-exception"]),
    "generic_procedure_homonym": dict(rule="S19.3.1-005", facets=["generic-name-same-as-procedure"]),
    "generic_derived_type": dict(rule="S19.3.1-005", facets=["generic-name-same-as-derived-type"]),
    "different_classes_homonym": dict(rule="S19.3.1-005", facets=["different-local-classes-same-spelling"]),
    "other_scope_reuse": dict(rule="S19.3.1-006", facets=["local-identifier-reuse-in-another-scope"]),
    "common_block_homonym": dict(rule="S19.3.2-002", facets=["common-block-homonym-local-reference"]),
    "function_results": dict(rule="S19.3.3-001", facets=[
        "function-statement-result-exists", "function-result-name-class-one-local"]),
    "components": dict(rule="S19.3.4-001", facets=[
        "component-name-type-definition-scope", "component-name-designator-use",
        "component-keyword-structure-constructor-use"]),
    "type_parameters": dict(rule="S19.3.4-002", facets=[
        "type-parameter-name-type-definition-scope", "type-parameter-keyword-use",
        "type-parameter-inquiry-use"]),
    "binding_reference": dict(rule="S19.3.4-003", facets=[
        "binding-name-type-definition-scope", "binding-name-procedure-reference-use"]),
    "generic_binding_operator": dict(rule="S19.3.4-004", facets=["nongeneric-spec-generic-binding-accessible-scope"]),
}

MUTATIONS.update({
    "association_rename": MUTATIONS["host_rename_shadow"][:1] + [
        dict(id="host-read-shadowed", kind="feature", replacements=[(
            "  subroutine read_host_token()\n    implicit none\n    host_seen = token\n  end subroutine read_host_token",
            "  subroutine read_host_token()\n    implicit none\n    integer :: token\n    token = 74\n    host_seen = token\n  end subroutine read_host_token")]),
        dict(id="outer-token-sentinel", kind="input", replacements=[("  token = 41", "  token = 40")]),
    ],
    "use_rename_exception": [
        dict(id="rename-to-wrong-global", kind="feature", replacements=[("local_name => source_name", "local_name => wrong_global")]),
        dict(id="local-homonym-sentinel", kind="input", replacements=[("  source_name = 99", "  source_name = 98")]),
    ],
    "common_block_exception": [
        dict(id="ordinary-expression-uses-common-member", kind="feature", replacements=[("call expect_equal(blk, 17", "call expect_equal(cb_member, 17")]),
        dict(id="common-sentinel", kind="input", replacements=[("  cb_member = 29", "  cb_member = 28")]),
    ],
    "function_exception": [
        dict(id="result-assignment-left-at-sentinel", kind="feature", replacements=[("  scope_result = 42 + n", "  ! result assignment removed by mutation")]),
        dict(id="result-base-sentinel", kind="input", replacements=[("scope_result(5), 47", "scope_result(5), 48")]),
    ],
    "generic_procedure_homonym": MUTATIONS["external_generic_same_name"],
    "different_classes_homonym": [
        dict(id="designator-uses-outer", kind="feature", replacements=[("call expect_equal(obj%tag, 31", "call expect_equal(tag, 31")]),
        dict(id="outer-tag-sentinel", kind="input", replacements=[("  tag = 99", "  tag = 98")]),
    ],
    "other_scope_reuse": [
        dict(id="remove-inner-shadow-declaration", kind="feature", replacements=[("    integer :: token\n    token = 73", "    ! shadow declaration removed by mutation\n    token = 73")]),
        dict(id="outer-token-sentinel", kind="input", replacements=[("  token = 41", "  token = 40")]),
    ],
    "function_name_limited": [
        dict(id="recursive-step-wrong", kind="feature", replacements=[("answer = scope_recur(n - 1) + 10", "answer = scope_recur(n - 1) + 11")]),
        dict(id="base-case-wrong", kind="input", replacements=[("answer = 8", "answer = 9")]),
    ],
})

# Map each case's extra facets back to their owning catalogue rules for fixture manifests.
FACET_OWNER = {facet: rule for rule, facets in FACETS_BY_RULE.items() for facet in facets}


def case_source(variant):
    data = CASES[variant]
    return source_header(data["rule"], data["facets"], data.get("evidence", "effect")) + PROGRAMS[variant]


def manifest(case_id, variant, data):
    return {
        "schema_version": 1,
        "id": case_id,
        "rule": data["rule"],
        "facets": data["facets"],
        "evidence": data.get("evidence", "effect"),
        "standard": "f2023",
        "oracle_basis": "standard",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
        "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
        "expect": {"phase": "run", "outcome": "success", "exit_code": 0, "stdout": completion(variant), "stderr": ""},
    }


def source_specs():
    specs = {}
    for variant, data in CASES.items():
        raw_source = case_source(variant)
        raw = raw_source.encode("ascii")
        cid = identifier(variant)
        specs[cid] = {
            "id": cid,
            "variant": variant,
            "rule": data["rule"],
            "facets": data["facets"],
            "extra_rules": data.get("extra_rules", []),
            "source": raw_source,
            "source_sha256": sha(raw),
            "completion": completion(variant),
            "mutations": copy.deepcopy(MUTATIONS[variant]),
        }
    return specs


def mutated_source(spec, mutation):
    text = spec["source"]
    changed = text
    for old, new in mutation["replacements"]:
        if changed.count(old) != 1:
            raise ValueError(f"{spec['variant']}:{mutation['id']} replacement is not load-bearing: {old!r}")
        changed = changed.replace(old, new, 1)
    if changed == text:
        raise ValueError(f"{spec['variant']}:{mutation['id']} did not change source")
    return changed.encode("ascii")


def build_corpus():
    specs = source_specs()
    files = {}
    for cid, spec in specs.items():
        folder = ROOT / FIXTURE_ROOT / cid
        files[folder / "source.f90"] = spec["source"].encode("ascii")
        files[folder / "fixture.json"] = (json.dumps(manifest(cid, spec["variant"], CASES[spec["variant"]]), indent=2) + "\n").encode("ascii")
    return files, specs


def catalogue_path_for_rule(rule):
    if rule.startswith("S19.1-"):
        return CATALOGUES["19.1"]
    if rule.startswith("S19.3.1-"):
        return CATALOGUES["19.3.1"]
    if rule.startswith("S19.3.2-"):
        return CATALOGUES["19.3.2"]
    if rule.startswith("S19.3.3-"):
        return CATALOGUES["19.3.3"]
    if rule.startswith("S19.3.4-"):
        return CATALOGUES["19.3.4"]
    raise KeyError(rule)


def synced_catalogue(path, catalogue):
    result = copy.deepcopy(catalogue)
    for req in result["requirements"]:
        rule = req["id"]
        if rule not in FACETS_BY_RULE:
            continue
        for facet in FACETS_BY_RULE[rule]:
            req.get("pending", {}).pop(facet, None)
        req["oracle"] = ORACLES[rule]
        req["oracle_limitation"] = LIMITATIONS[rule]
    return result


def synced_catalogues(root=ROOT):
    out = {}
    for rel in sorted(set(CATALOGUES.values())):
        path = root / rel
        data = json.loads(path.read_text())
        out[path] = synced_catalogue(rel, data)
    return out


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def generate(root=ROOT, check=False):
    files, _ = build_corpus()
    outputs = {path: raw for path, raw in files.items()}
    for path, data in synced_catalogues(root).items():
        outputs[path] = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    if check:
        missing = [path for path in outputs if not path.exists()]
        changed = [path for path, raw in outputs.items() if path.exists() and path.read_bytes() != raw]
        if missing or changed:
            raise SystemExit("generated files are stale: " + ", ".join(str(p.relative_to(root)) for p in missing + changed))
        return files, source_specs()
    # Remove stale fixture directories owned by this topic before writing fresh outputs.
    fixture_root = root / FIXTURE_ROOT
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    for path, raw in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    sys.path.insert(0, str(root / "tests"))
    from suite_data import Registry
    Registry(root).render(write=True)
    return files, source_specs()


def std_flag(compiler, std):
    name = Path(compiler).name.lower()
    return f"--std={std}" if "lfortran" in name else f"-std={std}"


def run_command(argv, cwd, timeout=30):
    env = os.environ.copy()
    env["TMPDIR"] = str((ROOT / ".scoping_19_1_19_3_tmp").resolve())
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)


def compile_and_run(source, compiler, std, workdir):
    src = workdir / "source.f90"
    exe = workdir / "program"
    src.write_bytes(source)
    comp = run_command([compiler, std_flag(compiler, std), "source.f90", "-o", "program"], workdir)
    if comp.returncode != 0:
        return {"phase": "compile", "returncode": comp.returncode, "stdout": comp.stdout, "stderr": comp.stderr}
    run = run_command([str(exe)], workdir)
    return {"phase": "run", "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
            "compile_stdout": comp.stdout, "compile_stderr": comp.stderr}


def mutation_matrix(compiler, std="f2023", root=ROOT, keep=False):
    files, specs = build_corpus()
    scratch_root = root / ".scoping_19_1_19_3_mutation_work"
    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    scratch_root.mkdir()
    results = []
    try:
        for cid, spec in specs.items():
            parent_dir = scratch_root / cid / "parent"
            parent_dir.mkdir(parents=True)
            parent = compile_and_run(spec["source"].encode("ascii"), compiler, std, parent_dir)
            parent_ok = (parent["phase"] == "run" and parent["returncode"] == 0
                         and parent["stdout"] == spec["completion"] and parent["stderr"] == "")
            results.append({"case": cid, "mutation": "parent", "ok": parent_ok, **parent})
            if not parent_ok:
                continue
            for mutation in spec["mutations"]:
                mdir = scratch_root / cid / mutation["id"]
                mdir.mkdir(parents=True)
                observed = compile_and_run(mutated_source(spec, mutation), compiler, std, mdir)
                failed_as_required = (observed["phase"] == "run" and not (
                    observed["returncode"] == 0 and observed["stdout"] == spec["completion"] and observed["stderr"] == ""))
                results.append({"case": cid, "mutation": mutation["id"], "kind": mutation["kind"],
                                "ok": failed_as_required, **observed})
    finally:
        if not keep:
            shutil.rmtree(scratch_root, ignore_errors=True)
            shutil.rmtree(root / ".scoping_19_1_19_3_tmp", ignore_errors=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            raise SystemExit("--mutation-check requires --compiler")
        results = mutation_matrix(args.compiler, args.std, keep=args.keep_work)
        total = sum(1 for row in results if row["mutation"] != "parent")
        passed = sum(1 for row in results if row["mutation"] == "parent" and row["ok"])
        failed = [row for row in results if not row["ok"]]
        if failed:
            for row in failed:
                print(json.dumps({k: row[k] for k in ("case", "mutation", "phase", "returncode", "stdout", "stderr") if k in row}, indent=2))
            raise SystemExit(f"mutation matrix failed: {len(failed)} bad rows out of {len(results)}")
        print(f"mutation matrix OK: {passed} parents passed; {total} mutants failed on {Path(args.compiler).name} {args.std}")
        return
    generate(ROOT, check=args.check)
    print(f"generated {len(CASES)} {TOPIC} fixtures")


if __name__ == "__main__":
    main()
