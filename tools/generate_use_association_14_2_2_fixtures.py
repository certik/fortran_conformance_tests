#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 USE association rules in 14.2.2."""

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
TOPIC = "use_association_14_2_2"
FIXTURE_ROOT = Path("tests/fixtures") / TOPIC
CATALOGUE = "doc/catalogues/use_statement_and_use_association_14_2_2.json"
SUMMARY = "USE ASSOCIATION 14.2.2"

FACETS_BY_RULE = {
    "S14.2.2-001": ["use-stmt-specifies-use-association", "use-stmt-references-module"],
    "S14.2.2-002": [
        "use-accesses-named-data-object", "use-accesses-nonintrinsic-type", "use-accesses-procedure",
        "use-accesses-generic-identifier", "use-accesses-namelist-group", "use-associated-entity-identity",
        "use-associated-attributes-preserved", "use-associated-variable-previously-declared",
        "use-associated-nonvariable-previously-defined"],
    "S14.2.2-012": [
        "use-associated-different-accessibility-permitted", "use-associated-asynchronous-permitted",
        "use-associated-volatile-permitted"],
    "S14.2.2-003": [
        "module-identifiers-identify-accessed-entities", "default-use-keeps-same-identifier",
        "rename-local-identifier-refers-to-module-entity"],
    "R1409": ["use-stmt-rename-list-form", "use-stmt-only-list-form", "use-stmt-module-nature-form"],
    "R1410": ["module-nature-intrinsic", "module-nature-nonintrinsic"],
    "R1411": ["rename-local-name-form", "rename-defined-operator-form"],
    "R1412": ["only-generic-spec-form", "only-use-name-form", "only-rename-form"],
    "R1413": ["only-use-name-designates-module-name"],
    "C1404": ["intrinsic-nature-intrinsic-module-control"],
    "C1405": ["nonintrinsic-nature-nonintrinsic-module-control"],
    "C1406": ["single-nature-module-reference-control"],
    "C1407": ["rename-operator-nontype-bound-control"],
    "C1408": ["only-generic-nontype-bound-control"],
    "C1410": ["only-use-name-nongeneric-control", "generic-name-only-item-is-generic-spec"],
    "R1414": ["local-defined-unary-operator", "local-defined-binary-operator"],
    "R1415": ["use-defined-unary-operator", "use-defined-binary-operator"],
    "S14.2.2-004": ["use-without-nature-accesses-module", "nonintrinsic-module-preferred-over-intrinsic"],
    "S14.2.2-005": ["use-without-only-accesses-all-public-entities"],
    "S14.2.2-006": ["only-list-accesses-listed-entities", "only-list-hides-unlisted-public-entities"],
    "S14.2.2-007": ["one-non-only-use-makes-all-public-accessible", "all-only-uses-union-only-lists"],
    "S14.2.2-013": ["multiple-use-same-module-permitted"],
    "S14.2.2-008": [
        "only-use-name-retains-module-identifier", "rename-creates-local-identifier",
        "unrenamed-entity-keeps-module-identifier", "multiple-local-identifiers-same-entity"],
    "S14.2.2-009": [
        "ultimate-entity-definition", "unused-conflicting-identifier-not-prohibited",
        "generic-interfaces-merge-across-use"],
    "S14.2.2-010": ["use-associated-public-private-exception", "use-associated-asynchronous-volatile-exception"],
}

DIAGNOSTIC_FACETS_BY_RULE = {
    "R1409": ["malformed-use-stmt-rejected"],
    "R1410": ["invalid-module-nature-rejected"],
    "R1411": ["malformed-rename-rejected"],
    "R1412": ["malformed-only-item-rejected"],
    "R1413": ["invalid-only-use-name-rejected"],
    "R1414": ["invalid-local-defined-operator-rejected"],
    "R1415": ["invalid-use-defined-operator-rejected"],
    "C1404": ["intrinsic-nature-nonintrinsic-module-rejected"],
    "C1405": ["nonintrinsic-nature-intrinsic-module-rejected"],
    "C1406": ["dual-nature-same-name-reference-rejected"],
    "C1407": ["rename-type-bound-generic-operator-rejected"],
    "C1408": ["only-type-bound-generic-rejected"],
}
ALL_COVERED_FACETS_BY_RULE = copy.deepcopy(FACETS_BY_RULE)
for _rule, _facets in DIAGNOSTIC_FACETS_BY_RULE.items():
    ALL_COVERED_FACETS_BY_RULE.setdefault(_rule, []).extend(_facets)

ORACLE_PREFIXES = {rule: f"{rule} USE-association fixture: " for rule in ALL_COVERED_FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} USE-association fixture boundaries: " for rule in FACETS_BY_RULE}
ORACLES = {
    rule: ORACLE_PREFIXES[rule] +
    "complete run/effect/f2023 source observes exact integer or logical consequences of the listed USE form with "
    "wrong-resolution sentinels. Generated feature mutations redirect the module, rename, ONLY member, exported "
    "value, generic specific, or attribute-bearing path so the corresponding assertion fails at run time."
    for rule in ALL_COVERED_FACETS_BY_RULE
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] +
    "only the listed positive single-image facets are discharged. Malformed syntax, invalid operator renames, "
    "PRIVATE identifier rejection, type-bound generic rejection, direct/indirect self-reference, unavailable build "
    "modules, namelist I/O, abstract-interface execution, unnumbered conflict diagnostics, and optimization-dependent "
    "ASYNCHRONOUS/VOLATILE effects remain pending unless explicitly covered by another fixture."
    for rule in ALL_COVERED_FACETS_BY_RULE
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    return CASES[variant]["rule"].replace(".", "_").replace("-", "_") + "_valid__" + TOPIC + "_" + variant


def diagnostic_identifier(variant):
    return DIAGNOSTIC_CASES[variant]["rule"].replace(".", "_").replace("-", "_") + "_invalid__" + TOPIC + "_" + variant


def completion(variant):
    if variant in {"only_operator_control"}:
        return f"{SUMMARY} OPERATOR CONTROL OK\n"
    return f"{SUMMARY} {variant.upper().replace('_', ' ')} OK\n"


def header(rule, facets):
    return f"! rule: {rule}\n! covers: {' '.join(facets)}\n! evidence: effect\n! standard: f2023\n! oracle-basis: standard\n"


def program(rule, facets, body):
    return header(rule, facets) + body.strip() + "\n"


CASES = {}
MUTATIONS = {}

def add_case(name, rule, body, mutations, facets=None):
    CASES[name] = {"rule": rule, "facets": list(facets or FACETS_BY_RULE[rule]), "body": body}
    MUTATIONS[name] = mutations

add_case("basic_reference", "S14.2.2-001", r'''
module s1422_001_provider
  implicit none
  integer :: answer = 42
end module
module s1422_001_wrong_provider
  implicit none
  integer :: answer = -999
end module
program use_assoc_basic_reference
  use s1422_001_provider, only: answer
  implicit none
  integer :: observed, checks
  checks = 0
  observed = -777
  observed = answer
  if (observed /= 42) error stop 1
  checks = checks + 1
  if (answer /= 42) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 BASIC REFERENCE OK'
end program
''', [
    {"id": "redirect-used-module", "kind": "feature", "replacements": [("use s1422_001_provider, only: answer", "use s1422_001_wrong_provider, only: answer")]},
    {"id": "change-public-answer", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
])

add_case("entity_kinds", "S14.2.2-002", r'''
module s1422_002_wrong_type_provider
  implicit none
  type :: box
    integer :: payload = -12
  end type
end module
module s1422_002_provider
  implicit none
  integer :: data_value = 11
  integer :: shared = 5
  integer, parameter :: width = 3
  integer :: nl_value = -777
  integer :: nl_shadow = -888
  namelist /provider_group/ nl_value
  abstract interface
    integer function abstract_answer()
    end function
  end interface
  type :: box
    integer :: payload = 12
  end type
  interface generic_value
    module procedure generic_int, generic_real
  end interface
contains
  integer function answer()
    answer = 23
  end function
  integer function generic_int(arg)
    integer, intent(in) :: arg
    generic_int = 31 + arg - arg
  end function
  integer function generic_real(arg)
    real, intent(in) :: arg
    generic_real = 32 + int(arg) - int(arg)
  end function
end module
program use_assoc_entity_kinds
  use s1422_002_provider, only: data_value, box, answer, abstract_answer, generic_value, &
       provider_group, nl_value, a => shared, b => shared, width
  implicit none
  integer :: checks, observed, bounds_array(width)
  character(len=48) :: nml_input
  procedure(abstract_answer), pointer :: proc
  type(box) :: item
  checks = 0
  observed = -777
  observed = data_value
  if (observed /= 11) error stop 1
  checks = checks + 1
  item = box()
  if (item%payload /= 12) error stop 2
  checks = checks + 1
  proc => local_abstract_answer
  if (proc() /= 70) error stop 3
  checks = checks + 1
  if (answer() /= 23) error stop 4
  checks = checks + 1
  if (generic_value(3) /= 31) error stop 5
  checks = checks + 1
  if (generic_value(2.0) /= 32) error stop 6
  checks = checks + 1
  if (nl_value /= -777) error stop 7
  checks = checks + 1
  nml_input = '&provider_group nl_value=64 /'
  read(nml_input, nml=provider_group)
  if (nl_value /= 64) error stop 8
  checks = checks + 1
  a = 41
  if (b /= 41) error stop 9
  checks = checks + 1
  if (size(bounds_array) /= 3) error stop 10
  checks = checks + 1
  b = 52
  if (a /= 52) error stop 11
  checks = checks + 1
  item = box(answer())
  if (item%payload /= 23) error stop 12
  checks = checks + 1
  if (checks /= 12) error stop 13
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ENTITY KINDS OK'
contains
  integer function local_abstract_answer()
    local_abstract_answer = 70
  end function
  integer function wrong_abstract_answer()
    wrong_abstract_answer = -70
  end function
end program
''', [
    {"id": "data-object-wrong-value", "kind": "feature", "replacements": [("integer :: data_value = 11", "integer :: data_value = 10")]},
    {"id": "type-access-wrong-module", "kind": "feature", "replacements": [("data_value, box, answer", "data_value, answer"), ("implicit none\n  integer :: checks, observed, bounds_array(width)", "use s1422_002_wrong_type_provider, only: box\n  implicit none\n  integer :: checks, observed, bounds_array(width)")]},
    {"id": "abstract-interface-wrong-procedure-binding", "kind": "feature", "replacements": [("proc => local_abstract_answer", "proc => wrong_abstract_answer")]},
    {"id": "procedure-wrong-result", "kind": "feature", "replacements": [("answer = 23", "answer = 24")]},
    {"id": "generic-int-wrong-result", "kind": "feature", "replacements": [("generic_int = 31 + arg - arg", "generic_int = 30 + arg - arg")]},
    {"id": "generic-real-wrong-result", "kind": "feature", "replacements": [("generic_real = 32 + int(arg) - int(arg)", "generic_real = 33 + int(arg) - int(arg)")]},
    {"id": "namelist-group-membership-wrong", "kind": "feature", "replacements": [("namelist /provider_group/ nl_value", "namelist /provider_group/ nl_shadow")]},
    {"id": "namelist-sentinel-init-removed", "kind": "feature", "replacements": [("integer :: nl_value = -777", "integer :: nl_value")]},
    {"id": "namelist-sentinel-init-at-read-value", "kind": "feature", "replacements": [("integer :: nl_value = -777", "integer :: nl_value = 64")]},
    {"id": "namelist-sentinel-init-zero", "kind": "feature", "replacements": [("integer :: nl_value = -777", "integer :: nl_value = 0")]},
    {"id": "break-shared-identity", "kind": "feature", "replacements": [("provider_group, nl_value, a => shared, b => shared, width", "provider_group, nl_value, a => shared, width"), ("implicit none\n  integer :: checks, observed, bounds_array(width)", "implicit none\n  integer :: checks, observed, bounds_array(width)\n  integer :: b = -888")]},
    {"id": "parameter-width-wrong", "kind": "feature", "replacements": [("integer, parameter :: width = 3", "integer, parameter :: width = 4")]},
    {"id": "second-shared-update-wrong", "kind": "feature", "replacements": [("b = 52", "b = 53")]},
])

add_case("attribute_exceptions", "S14.2.2-012", r'''
module s1422_012_provider
  implicit none
  integer :: shared = 42
end module
module s1422_012_attr_provider
  implicit none
  integer :: attr_shared = 42
end module
module s1422_012_reexporter
  use s1422_012_provider, only: shared
  implicit none
  private :: shared
  public :: read_shared
contains
  integer function read_shared()
    read_shared = shared
  end function
end module
program use_assoc_attribute_exceptions
  implicit none
  integer :: checks
  checks = 0
  call check_private(checks)
  call check_async(checks)
  call check_volatile(checks)
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ATTRIBUTE EXCEPTIONS OK'
contains
  subroutine check_private(checks)
    use s1422_012_reexporter, only: read_shared
    implicit none
    integer, intent(inout) :: checks
    if (read_shared() /= 42) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_async(checks)
    use s1422_012_attr_provider, only: async_shared => attr_shared
    implicit none
    asynchronous :: async_shared
    integer, intent(inout) :: checks
    if (async_shared /= 42) error stop 2
    checks = checks + 1
  end subroutine
  subroutine check_volatile(checks)
    use s1422_012_attr_provider, only: vol_shared => attr_shared
    implicit none
    volatile :: vol_shared
    integer, intent(inout) :: checks
    if (vol_shared /= 42) error stop 3
    checks = checks + 1
  end subroutine
end program
''', [
    {"id": "private-reexport-wrong-value", "kind": "feature", "replacements": [("integer :: shared = 42", "integer :: shared = 41")]},
    {"id": "async-alias-wrong-local", "kind": "feature", "replacements": [("use s1422_012_attr_provider, only: async_shared => attr_shared", "! removed async USE by mutation"), ("implicit none\n    asynchronous :: async_shared", "implicit none\n    integer :: async_shared = -1")]},
    {"id": "volatile-alias-wrong-local", "kind": "feature", "replacements": [("use s1422_012_attr_provider, only: vol_shared => attr_shared", "! removed volatile USE by mutation"), ("implicit none\n    volatile :: vol_shared", "implicit none\n    integer :: vol_shared = -2")]},
])

add_case("identifier_forms", "S14.2.2-003", r'''
module s1422_003_provider
  implicit none
  integer :: module_value = 42
  integer :: hidden = 51
  integer :: other = -999
end module
program use_assoc_identifier_forms
  use s1422_003_provider, only: module_value, local_hidden => hidden
  implicit none
  integer :: checks, hidden, other
  checks = 0
  hidden = -7
  other = -8
  if (module_value /= 42) error stop 1
  checks = checks + 1
  if (module_value + 0 /= 42) error stop 2
  checks = checks + 1
  if (local_hidden /= 51 .or. hidden /= -7 .or. other /= -8) error stop 3
  checks = checks + 1
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 IDENTIFIER FORMS OK'
end program
''', [
    {"id": "module-identifier-value", "kind": "feature", "replacements": [("integer :: module_value = 42", "integer :: module_value = 41")]},
    {"id": "default-identifier-local-sentinel", "kind": "feature", "replacements": [("use s1422_003_provider, only: module_value, local_hidden => hidden", "use s1422_003_provider, only: local_hidden => hidden"), ("implicit none\n  integer :: checks, hidden, other", "implicit none\n  integer :: checks, hidden, other\n  integer :: module_value = -999")]},
    {"id": "rename-target-wrong-entity", "kind": "feature", "replacements": [("local_hidden => hidden", "local_hidden => other")]},
])

add_case("use_stmt_forms", "R1409", r'''
module r1409_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 5
  integer :: noise = -999
end module
program use_stmt_forms
  use, non_intrinsic :: r1409_provider, only: nature_answer => answer
  use r1409_provider, rename_bonus => bonus
  use r1409_provider, only: only_answer => answer
  implicit none
  integer :: checks
  checks = 0
  if (rename_bonus /= 5) error stop 1
  checks = checks + 1
  if (only_answer /= 42) error stop 2
  checks = checks + 1
  if (nature_answer /= 42) error stop 3
  checks = checks + 1
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 USE STMT FORMS OK'
end program
''', [
    {"id": "rename-list-wrong-target", "kind": "feature", "replacements": [("rename_bonus => bonus", "rename_bonus => noise")]},
    {"id": "only-list-wrong-target", "kind": "feature", "replacements": [("only_answer => answer", "only_answer => noise")]},
    {"id": "module-nature-wrong-module", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
])

add_case("module_nature", "R1410", r'''
module r1410_provider
  implicit none
  integer :: answer = 42
end module
module r1410_shadow_env
  implicit none
  integer :: input_unit = -777
end module
program module_nature_forms
  use, intrinsic :: iso_fortran_env, only: input_unit
  use, non_intrinsic :: r1410_provider, only: answer
  implicit none
  integer :: checks
  checks = 0
  if (input_unit == -777) error stop 1
  checks = checks + 1
  if (answer /= 42) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 MODULE NATURE OK'
end program
''', [
    {"id": "intrinsic-nature-redirect-to-nonintrinsic", "kind": "feature", "replacements": [("use, intrinsic :: iso_fortran_env, only: input_unit", "use, non_intrinsic :: r1410_shadow_env, only: input_unit")]},
    {"id": "nonintrinsic-provider-wrong", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
])

add_case("rename_local_name", "R1411", r'''
module r1411_provider
  implicit none
  integer :: original = 42
  integer :: wrong = -999
end module
program rename_local_name
  use r1411_provider, local_name => original
  implicit none
  integer :: original, checks
  checks = 0
  original = -7
  if (local_name /= 42 .or. original /= -7) error stop 1
  checks = checks + 1
  if (checks /= 1) error stop 2
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RENAME LOCAL NAME OK'
end program
''', [
    {"id": "rename-use-name-wrong", "kind": "feature", "replacements": [("integer :: original = 42", "integer :: original = 41")]},
], facets=["rename-local-name-form"])

add_case("only_forms", "R1412", r'''
module r1412_provider
  implicit none
  integer :: answer = 42
  integer :: wrong = -999
  interface g
    module procedure gi
  end interface
contains
  integer function gi(i)
    integer, intent(in) :: i
    gi = 31 + i - i
  end function
end module
program only_forms
  implicit none
  integer :: checks
  checks = 0
  call check_generic(checks)
  call check_use_name(checks)
  call check_rename(checks)
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ONLY FORMS OK'
contains
  subroutine check_generic(checks)
    use r1412_provider, only: g
    implicit none
    integer, intent(inout) :: checks
    if (g(3) /= 31) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_use_name(checks)
    use r1412_provider, only: answer
    implicit none
    integer, intent(inout) :: checks
    if (answer /= 42) error stop 2
    checks = checks + 1
  end subroutine
  subroutine check_rename(checks)
    use r1412_provider, only: local_answer => answer
    implicit none
    integer, intent(inout) :: checks
    if (local_answer /= 42) error stop 3
    checks = checks + 1
  end subroutine
end program
''', [
    {"id": "generic-specific-wrong", "kind": "feature", "replacements": [("gi = 31 + i - i", "gi = 30 + i - i")]},
    {"id": "only-use-name-wrong", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
    {"id": "only-rename-wrong-target", "kind": "feature", "replacements": [("local_answer => answer", "local_answer => wrong")]},
])

add_case("only_use_name", "R1413", r'''
module r1413_provider
  implicit none
  integer :: answer = 42
end module
program only_use_name
  use r1413_provider, only: answer
  implicit none
  if (answer /= 42) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ONLY USE NAME OK'
end program
''', [
    {"id": "only-use-name-provider-value", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
])

add_case("intrinsic_control", "C1404", r'''
module c1404_shadow_env
  implicit none
  integer :: input_unit = -777
end module
program intrinsic_control
  use, intrinsic :: iso_fortran_env, only: input_unit
  implicit none
  if (input_unit == -777) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 INTRINSIC CONTROL OK'
end program
''', [
    {"id": "intrinsic-control-redirect-to-nonintrinsic", "kind": "feature", "replacements": [("use, intrinsic :: iso_fortran_env, only: input_unit", "use, non_intrinsic :: c1404_shadow_env, only: input_unit")]},
])

add_case("nonintrinsic_control", "C1405", r'''
module c1405_provider
  implicit none
  integer :: answer = 42
end module
program nonintrinsic_control
  use, non_intrinsic :: c1405_provider, only: answer
  implicit none
  if (answer /= 42) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 NONINTRINSIC CONTROL OK'
end program
''', [
    {"id": "nonintrinsic-control-value", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
])

add_case("single_nature_control", "C1406", r'''
module c1406_shadow_env
  implicit none
  integer :: input_unit = -777
end module
program single_nature_control
  use, intrinsic :: iso_fortran_env, only: input_unit
  implicit none
  if (input_unit == -777) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 SINGLE NATURE CONTROL OK'
end program
''', [
    {"id": "single-nature-redirect-to-nonintrinsic", "kind": "feature", "replacements": [("use, intrinsic :: iso_fortran_env, only: input_unit", "use, non_intrinsic :: c1406_shadow_env, only: input_unit")]},
])

OPERATOR_BODY = r'''
module operator_provider
  implicit none
  type :: box
    integer :: v
  end type
  interface operator(.addbox.)
    module procedure addbox
  end interface
contains
  integer function addbox(left, right)
    type(box), intent(in) :: left, right
    addbox = 100 * left%v + right%v
  end function
end module
program operator_control
  use operator_provider, only: box, operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(2)
  right = box(7)
  if ((left .addbox. right) /= 207) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 OPERATOR CONTROL OK'
end program
'''
add_case("only_operator_control", "C1408", OPERATOR_BODY, [
    {"id": "operator-only-implementation-wrong", "kind": "feature", "replacements": [("addbox = 100 * left%v + right%v", "addbox = 10 * left%v + right%v")]},
])


OPERATOR_RENAME_MODULE = r"""
module operator_rename_provider
  implicit none
  type :: box
    integer :: v
  end type
  interface operator(.addbox.)
    module procedure addbox
  end interface
  interface operator(.negbox.)
    module procedure negbox
  end interface
  interface operator(.wrongbox.)
    module procedure wrongbox
  end interface
  interface operator(.wrongneg.)
    module procedure wrongneg
  end interface
contains
  integer function addbox(left, right)
    type(box), intent(in) :: left, right
    addbox = 100 * left%v + right%v
  end function
  integer function negbox(value)
    type(box), intent(in) :: value
    negbox = -value%v
  end function
  integer function wrongbox(left, right)
    type(box), intent(in) :: left, right
    wrongbox = -999 - left%v - right%v
  end function
  integer function wrongneg(value)
    type(box), intent(in) :: value
    wrongneg = -999 - value%v
  end function
end module
"""

add_case("rename_defined_operator", "R1411", OPERATOR_RENAME_MODULE + r"""
program rename_defined_operator
  use operator_rename_provider, only: box, operator(.localadd.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(2)
  right = box(7)
  if ((left .localadd. right) /= 207) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RENAME DEFINED OPERATOR OK'
end program
""", [
    {"id": "rename-defined-operator-wrong-target", "kind": "feature", "replacements": [("operator(.localadd.) => operator(.addbox.)", "operator(.localadd.) => operator(.wrongbox.)")]},
], facets=["rename-defined-operator-form"])

add_case("local_defined_operators", "R1414", OPERATOR_RENAME_MODULE + r"""
program local_defined_operators
  use operator_rename_provider, only: box, operator(.localneg.) => operator(.negbox.), &
       operator(.localsum.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(5)
  right = box(4)
  if ((.localneg. left) /= -5) error stop 1
  if ((left .localsum. right) /= 504) error stop 2
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 LOCAL DEFINED OPERATORS OK'
end program
""", [
    {"id": "local-unary-operator-wrong-target", "kind": "feature", "replacements": [("operator(.localneg.) => operator(.negbox.)", "operator(.localneg.) => operator(.wrongneg.)")]},
    {"id": "local-binary-operator-wrong-target", "kind": "feature", "replacements": [("operator(.localsum.) => operator(.addbox.)", "operator(.localsum.) => operator(.wrongbox.)")]},
])

add_case("use_defined_operators", "R1415", OPERATOR_RENAME_MODULE + r"""
program use_defined_operators
  use operator_rename_provider, only: box, operator(.myneg.) => operator(.negbox.), &
       operator(.myadd.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(6)
  right = box(3)
  if ((.myneg. left) /= -6) error stop 1
  if ((left .myadd. right) /= 603) error stop 2
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 USE DEFINED OPERATORS OK'
end program
""", [
    {"id": "use-unary-operator-wrong-target", "kind": "feature", "replacements": [("operator(.myneg.) => operator(.negbox.)", "operator(.myneg.) => operator(.wrongneg.)")]},
    {"id": "use-binary-operator-wrong-target", "kind": "feature", "replacements": [("operator(.myadd.) => operator(.addbox.)", "operator(.myadd.) => operator(.wrongbox.)")]},
])

add_case("rename_operator_control", "C1407", OPERATOR_RENAME_MODULE + r"""
program rename_operator_control
  use operator_rename_provider, only: box, operator(.publicadd.) => operator(.addbox.)
  implicit none
  type(box) :: left, right
  left = box(8)
  right = box(1)
  if ((left .publicadd. right) /= 801) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RENAME OPERATOR CONTROL OK'
end program
""", [
    {"id": "rename-operator-control-wrong-target", "kind": "feature", "replacements": [("operator(.publicadd.) => operator(.addbox.)", "operator(.publicadd.) => operator(.wrongbox.)")]},
])

add_case("c1410_only_generic", "C1410", r'''
module c1410_provider
  implicit none
  integer :: answer = 42
  interface g
    module procedure gi, gr
  end interface
contains
  integer function gi(i)
    integer, intent(in) :: i
    gi = 31 + i - i
  end function
  integer function gr(x)
    real, intent(in) :: x
    gr = 32 + int(x) - int(x)
  end function
end module
program c1410_only_generic
  use c1410_provider, only: answer, g
  implicit none
  integer :: checks
  checks = 0
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (g(3) /= 31 .or. g(2.0) /= 32) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 C1410 ONLY GENERIC OK'
end program
''', [
    {"id": "nongeneric-only-value", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
    {"id": "generic-only-value", "kind": "feature", "replacements": [("gi = 31 + i - i", "gi = 30 + i - i")]},
])

add_case("without_nature", "S14.2.2-004", r'''
module plain_m
  implicit none
  integer :: answer = 42
end module
module iso_fortran_env
  implicit none
  integer :: collision_answer = 55
end module
program without_nature
  use plain_m, only: answer
  use iso_fortran_env, only: collision_answer
  implicit none
  integer :: checks
  checks = 0
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (collision_answer /= 55) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 WITHOUT NATURE OK'
end program
''', [
    {"id": "plain-use-value", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
    {"id": "nonintrinsic-collision-value", "kind": "feature", "replacements": [("integer :: collision_answer = 55", "integer :: collision_answer = 54")]},
])

add_case("without_only", "S14.2.2-005", r'''
module all_public_provider
  implicit none
  integer :: first = 41
  integer :: second = 42
  integer, private :: hidden = -999
end module
program without_only
  use all_public_provider
  implicit none
  if (first + second /= 83) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 WITHOUT ONLY OK'
end program
''', [
    {"id": "all-public-second-value", "kind": "feature", "replacements": [("integer :: second = 42", "integer :: second = 41")]},
])

add_case("only_access", "S14.2.2-006", r'''
module only_access_provider
  implicit none
  integer :: answer = 42
  integer :: noise = -999
end module
program only_access
  use only_access_provider, only: answer
  implicit none
  integer :: noise, checks
  checks = 0
  noise = -7
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (noise /= -7) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ONLY ACCESS OK'
end program
''', [
    {"id": "only-listed-value", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
    {"id": "only-hides-unlisted-add-noise", "kind": "feature", "replacements": [("use only_access_provider, only: answer", "use only_access_provider, only: answer, noise"), ("integer :: noise, checks", "integer :: checks"), ("  noise = -7\n", "")]},
])

add_case("multiple_use_access", "S14.2.2-007", r'''
module multi_use_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 1
  integer :: noise = -999
end module
module multi_wrong_provider
  implicit none
  integer :: noise = -7
end module
program multiple_use_access
  implicit none
  integer :: checks
  checks = 0
  call check_non_only(checks)
  call check_all_only_union(checks)
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 MULTIPLE USE ACCESS OK'
contains
  subroutine check_non_only(checks)
    use multi_use_provider, only: answer
    use multi_use_provider
    implicit none
    integer, intent(inout) :: checks
    if (answer + bonus + noise /= -956) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_all_only_union(checks)
    use multi_use_provider, only: answer
    use multi_use_provider, only: bonus
    use multi_wrong_provider, only: noise
    implicit none
    integer, intent(inout) :: checks
    if (answer + bonus + noise /= 36) error stop 2
    checks = checks + 1
  end subroutine
end program
''', [
    {"id": "non-only-use-removed", "kind": "feature", "replacements": [("use multi_use_provider\n    implicit none\n    integer, intent(inout) :: checks", "use multi_wrong_provider, only: noise\n    implicit none\n    integer, intent(inout) :: checks\n    integer :: bonus = -777")]},
    {"id": "all-only-union-bonus-removed", "kind": "feature", "replacements": [("use multi_use_provider, only: bonus", "! removed bonus ONLY by mutation"), ("use multi_wrong_provider, only: noise\n    implicit none\n    integer, intent(inout) :: checks", "use multi_wrong_provider, only: noise\n    implicit none\n    integer, intent(inout) :: checks\n    integer :: bonus = -777")]},
])

add_case("multiple_use_same_module", "S14.2.2-013", r'''
module same_module_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 41
end module
program multiple_use_same_module
  use same_module_provider, only: a => answer
  use same_module_provider, only: b => bonus
  implicit none
  if (a + b /= 83) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 MULTIPLE USE SAME MODULE OK'
end program
''', [
    {"id": "second-use-renamed-value", "kind": "feature", "replacements": [("integer :: bonus = 41", "integer :: bonus = 40")]},
])

add_case("identifier_assignment", "S14.2.2-008", r'''
module id_assign_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 1
  integer :: shared = 5
end module
program identifier_assignment
  use id_assign_provider, only: answer
  use id_assign_provider, local_bonus => bonus
  use id_assign_provider, a => shared, b => shared
  implicit none
  integer :: checks
  checks = 0
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (local_bonus /= 1) error stop 2
  checks = checks + 1
  if (answer + local_bonus /= 43) error stop 3
  checks = checks + 1
  a = 77
  if (b /= 77) error stop 4
  checks = checks + 1
  if (checks /= 4) error stop 5
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 IDENTIFIER ASSIGNMENT OK'
end program
''', [
    {"id": "only-use-name-value", "kind": "feature", "replacements": [("integer :: answer = 42", "integer :: answer = 41")]},
    {"id": "rename-local-identifier-value", "kind": "feature", "replacements": [("integer :: bonus = 1", "integer :: bonus = 2")]},
    {"id": "unrenamed-identifier-wrong-rename-target", "kind": "feature", "replacements": [("local_bonus => bonus", "local_bonus => shared")]},
    {"id": "same-entity-local-identifiers", "kind": "feature", "replacements": [("use id_assign_provider, a => shared, b => shared", "use id_assign_provider, a => shared"), ("implicit none\n  integer :: checks", "implicit none\n  integer :: checks\n  integer :: b = -777")]},
])

add_case("ultimate_and_generic", "S14.2.2-009", r'''
module ultimate_provider
  implicit none
  integer :: shared = 5
end module
module conflict_a
  implicit none
  integer :: x = -1
  integer :: answer_a = 42
end module
module conflict_b
  implicit none
  integer :: x = -2
  integer :: answer_b = 1
end module
module generic_a
  implicit none
  interface g
    module procedure gi
  end interface
contains
  integer function gi(i)
    integer, intent(in) :: i
    gi = 31 + i - i
  end function
end module
module generic_b
  implicit none
  interface g
    module procedure gr
  end interface
contains
  integer function gr(x)
    real, intent(in) :: x
    gr = 32 + int(x) - int(x)
  end function
end module
program ultimate_and_generic
  use ultimate_provider, only: a => shared, b => shared
  use conflict_a, only: x, answer_a
  use conflict_b, only: x, answer_b
  use generic_a
  use generic_b
  implicit none
  integer :: checks
  checks = 0
  a = 42
  if (b /= 42) error stop 1
  checks = checks + 1
  if (answer_a + answer_b /= 43) error stop 2
  checks = checks + 1
  if (g(3) /= 31 .or. g(2.0) /= 32) error stop 3
  checks = checks + 1
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ULTIMATE AND GENERIC OK'
end program
''', [
    {"id": "ultimate-shared-identity", "kind": "feature", "replacements": [("use ultimate_provider, only: a => shared, b => shared", "use ultimate_provider, only: a => shared"), ("implicit none\n  integer :: checks", "implicit none\n  integer :: checks\n  integer :: b = -777")]},
    {"id": "unused-conflict-side-value", "kind": "feature", "replacements": [("integer :: answer_b = 1", "integer :: answer_b = 2")]},
    {"id": "generic-merge-specific", "kind": "feature", "replacements": [("gr = 32 + int(x) - int(x)", "gr = 33 + int(x) - int(x)")]},
])

add_case("respec_exceptions", "S14.2.2-010", r'''
module respec_provider
  implicit none
  integer :: shared = 42
end module
module respec_attr_provider
  implicit none
  integer :: attr_shared = 42
end module
module respec_reexporter
  use respec_provider, only: shared
  implicit none
  private :: shared
  public :: read_shared
contains
  integer function read_shared()
    read_shared = shared
  end function
end module
program respec_exceptions
  implicit none
  integer :: checks
  checks = 0
  call check_private(checks)
  call check_async_volatile(checks)
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RESPEC EXCEPTIONS OK'
contains
  subroutine check_private(checks)
    use respec_reexporter, only: read_shared
    implicit none
    integer, intent(inout) :: checks
    if (read_shared() /= 42) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_async_volatile(checks)
    use respec_attr_provider, only: async_shared => attr_shared, vol_shared => attr_shared
    implicit none
    asynchronous :: async_shared
    volatile :: vol_shared
    integer, intent(inout) :: checks
    if (async_shared + vol_shared /= 84) error stop 2
    checks = checks + 1
  end subroutine
end program
''', [
    {"id": "public-private-exception-value", "kind": "feature", "replacements": [("integer :: shared = 42", "integer :: shared = 41")]},
    {"id": "async-volatile-remove-use-path", "kind": "feature", "replacements": [("use respec_attr_provider, only: async_shared => attr_shared, vol_shared => attr_shared", "! removed async/volatile USE by mutation"), ("implicit none\n    asynchronous :: async_shared\n    volatile :: vol_shared", "implicit none\n    integer :: async_shared = -1, vol_shared = -2")]},
])



DIAGNOSTIC_EXCLUDES = [
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "Internal Compiler Error", "LCOMPILERS_ASSERT", "ASR",
]
DIAGNOSTIC_CONTAINS = [
    "syntax", "unclassifiable", "missing", "module", "operator", "intrinsic",
    "non_intrinsic", "non-intrinsic", "conflict", "not found", "generic",
    "Token", "unexpected", "Cannot find", "Symbol",
]

DIAGNOSTIC_CASES = {
    "r1409_malformed_use": dict(rule="R1409", facets=["malformed-use-stmt-rejected"], line=6, source=r'''
module r1409_diag_provider
  implicit none
  integer :: answer = 1
end module
program r1409_malformed_use
  use, only: answer
  implicit none
end program
'''),
    "r1410_invalid_nature": dict(rule="R1410", facets=["invalid-module-nature-rejected"], line=2, source=r'''
program r1410_invalid_nature
  use, extrinsic :: iso_fortran_env, only: input_unit
  implicit none
end program
'''),
    "r1411_malformed_rename": dict(rule="R1411", facets=["malformed-rename-rejected"], line=6, source=r'''
module r1411_diag_provider
  implicit none
  integer :: original = 1
end module
program r1411_malformed_rename
  use r1411_diag_provider, local_name = original
  implicit none
end program
'''),
    "r1412_malformed_only": dict(rule="R1412", facets=["malformed-only-item-rejected"], line=6, source=r'''
module r1412_diag_provider
  implicit none
  integer :: answer = 1
end module
program r1412_malformed_only
  use r1412_diag_provider, only: => answer
  implicit none
end program
'''),
    "r1413_invalid_only_use_name": dict(rule="R1413", facets=["invalid-only-use-name-rejected"], line=6, source=r'''
module r1413_diag_provider
  implicit none
  integer :: answer = 1
end module
program r1413_invalid_only_use_name
  use r1413_diag_provider, only: 123
  implicit none
end program
'''),
    "r1414_invalid_local_operator": dict(rule="R1414", facets=["invalid-local-defined-operator-rejected"], line=8, source=r'''
module r1414_diag_provider
  type :: box; integer :: v; end type
  interface operator(.addbox.); module procedure addbox; end interface
contains
  integer function addbox(a,b); type(box),intent(in)::a,b; addbox=a%v+b%v; end function
end module
program r1414_invalid_local_operator
  use r1414_diag_provider, only: box, operator(+) => operator(.addbox.)
  implicit none
end program
'''),
    "r1415_invalid_use_operator": dict(rule="R1415", facets=["invalid-use-defined-operator-rejected"], line=8, source=r'''
module r1415_diag_provider
  type :: box; integer :: v; end type
  interface operator(.addbox.); module procedure addbox; end interface
contains
  integer function addbox(a,b); type(box),intent(in)::a,b; addbox=a%v+b%v; end function
end module
program r1415_invalid_use_operator
  use r1415_diag_provider, only: box, operator(.localadd.) => operator(+)
  implicit none
end program
'''),
    "c1404_intrinsic_nonintrinsic": dict(rule="C1404", facets=["intrinsic-nature-nonintrinsic-module-rejected"], line=6, source=r'''
module local_env
  implicit none
  integer :: answer = 1
end module
program c1404_intrinsic_nonintrinsic
  use, intrinsic :: local_env, only: answer
  implicit none
end program
'''),
    "c1405_nonintrinsic_intrinsic": dict(rule="C1405", facets=["nonintrinsic-nature-intrinsic-module-rejected"], line=2, source=r'''
program c1405_nonintrinsic_intrinsic
  use, non_intrinsic :: iso_fortran_env, only: input_unit
  implicit none
end program
'''),
    "c1406_dual_nature_same_name": dict(rule="C1406", facets=["dual-nature-same-name-reference-rejected"], line=7, source=r'''
module iso_fortran_env
  implicit none
  integer :: answer = 1
end module
program c1406_dual_nature_same_name
  use, intrinsic :: iso_fortran_env, only: input_unit
  use, non_intrinsic :: iso_fortran_env, only: answer
  implicit none
end program
'''),
    "c1407_type_bound_rename": dict(rule="C1407", facets=["rename-type-bound-generic-operator-rejected"], line=12, source=r'''
module c1407_type_bound_provider
  type :: box
    integer :: v
  contains
    procedure :: addbox
    generic :: operator(.addbox.) => addbox
  end type
contains
  integer function addbox(a,b); class(box),intent(in)::a; type(box),intent(in)::b; addbox=a%v+b%v; end function
end module
program c1407_type_bound_rename
  use c1407_type_bound_provider, only: box, operator(.localadd.) => operator(.addbox.)
  implicit none
end program
'''),
    "c1408_type_bound_only": dict(rule="C1408", facets=["only-type-bound-generic-rejected"], line=12, source=r'''
module c1408_type_bound_provider
  type :: box
    integer :: v
  contains
    procedure :: addbox
    generic :: operator(.addbox.) => addbox
  end type
contains
  integer function addbox(a,b); class(box),intent(in)::a; type(box),intent(in)::b; addbox=a%v+b%v; end function
end module
program c1408_type_bound_only
  use c1408_type_bound_provider, only: box, operator(.addbox.)
  implicit none
end program
'''),
}

def case_source(variant):
    data = CASES[variant]
    return program(data["rule"], data["facets"], data["body"])


def manifest(cid, variant):
    data = CASES[variant]
    evidence = "positive-control" if data["rule"].startswith(("R", "C")) or data["rule"] in {"S14.2.2-001", "S14.2.2-009", "S14.2.2-010"} else "effect"
    return {
        "schema_version": 1, "id": cid, "rule": data["rule"], "facets": data["facets"],
        "evidence": evidence, "standard": "f2023", "oracle_basis": "standard",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
        "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
        "expect": {"phase": "run", "outcome": "success", "exit_code": 0, "stdout": completion(variant), "stderr": ""},
    }


def source_specs():
    specs = {}
    for variant, data in CASES.items():
        source = case_source(variant)
        cid = identifier(variant)
        specs[cid] = {
            "id": cid, "variant": variant, "rule": data["rule"], "facets": data["facets"],
            "source": source, "source_sha256": sha(source.encode("ascii")),
            "completion": completion(variant), "mutations": copy.deepcopy(MUTATIONS[variant]),
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


def diagnostic_specs():
    specs = {}
    for variant, data in DIAGNOSTIC_CASES.items():
        source = header(data["rule"], data["facets"]) + data["source"].strip() + "\n"
        cid = diagnostic_identifier(variant)
        specs[cid] = {
            "id": cid, "variant": variant, "rule": data["rule"], "facets": data["facets"],
            "source": source, "source_sha256": sha(source.encode("ascii")), "line": data["line"] + 5,
        }
    return specs


def facet_assertion_mutation_table():
    table = {}
    overrides = {
        "use-accesses-procedure": "procedure-wrong-result",
        "use-accesses-generic-identifier": "generic-int-wrong-result",
        "use-accesses-namelist-group": "namelist-group-membership-wrong",
        "use-associated-entity-identity": "break-shared-identity",
        "use-associated-attributes-preserved": "parameter-width-wrong",
        "use-associated-variable-previously-declared": "break-shared-identity",
        "use-associated-nonvariable-previously-defined": "procedure-wrong-result",
        "only-list-hides-unlisted-public-entities": "only-hides-unlisted-add-noise",
        "unrenamed-entity-keeps-module-identifier": "unrenamed-identifier-wrong-rename-target",
    }
    for spec in source_specs().values():
        mutations = spec["mutations"]
        by_id = {mutation["id"]: mutation for mutation in mutations}
        for index, facet in enumerate(spec["facets"]):
            mutation = overrides.get(facet, mutations[min(index, len(mutations) - 1)]["id"])
            if mutation not in by_id:
                raise ValueError(f"{facet}: feature table mutation {mutation} is not in {spec['variant']}")
            table[facet] = {
                "case": spec["id"],
                "assertion": f"{spec['variant']} runtime assertion for {facet}",
                "feature_mutant": mutation,
            }
    control_by_rule = {
        "R1409": "use_stmt_forms", "R1410": "module_nature", "R1411": "rename_local_name",
        "R1412": "only_forms", "R1413": "only_use_name", "R1414": "local_defined_operators",
        "R1415": "use_defined_operators", "C1404": "intrinsic_control",
        "C1405": "nonintrinsic_control", "C1406": "single_nature_control",
        "C1407": "rename_operator_control", "C1408": "only_operator_control",
    }
    for spec in diagnostic_specs().values():
        for facet in spec["facets"]:
            table[facet] = {
                "case": spec["id"],
                "assertion": f"line-anchored required compile diagnostic for {facet}",
                "feature_mutant": "one-property invalid source; conforming control " + control_by_rule[spec["rule"]],
            }
    return dict(sorted(table.items()))


FACET_ASSERTION_MUTATION_TABLE = facet_assertion_mutation_table()


def diagnostic_manifest(cid, spec):
    return {
        "schema_version": 1, "id": cid, "rule": spec["rule"], "facets": spec["facets"],
        "evidence": "effect", "standard": "f2023", "oracle_basis": "standard",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
        "expect": {
            "phase": "compile", "step": "source", "outcome": "diagnose",
            "diagnostic": {
                "file": "source.f90", "line": spec["line"], "end_line": spec["line"],
                "contains_any": DIAGNOSTIC_CONTAINS, "excludes_any": DIAGNOSTIC_EXCLUDES,
            },
        },
    }


def build_corpus(root=ROOT):
    specs = source_specs()
    diag_specs = diagnostic_specs()
    files = {}
    for cid, spec in specs.items():
        folder = root / FIXTURE_ROOT / cid
        files[folder / "source.f90"] = spec["source"].encode("ascii")
        files[folder / "fixture.json"] = (json.dumps(manifest(cid, spec["variant"]), indent=2) + "\n").encode("ascii")
    for cid, spec in diag_specs.items():
        folder = root / FIXTURE_ROOT / cid
        files[folder / "source.f90"] = spec["source"].encode("ascii")
        files[folder / "fixture.json"] = (json.dumps(diagnostic_manifest(cid, spec), indent=2) + "\n").encode("ascii")
    specs.update(diag_specs)
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    if "C1407" in by_rule and "C1407" not in FACETS_BY_RULE:
        by_rule["C1407"]["pending"] = {
            "rename-operator-nontype-bound-control": "PENDING operator rename controls are withheld because the frozen LFortran target rejects conforming defined-operator renames; only non-renamed OPERATOR(.addbox.) ONLY access is covered under C1408 in this packet.",
            "rename-type-bound-generic-operator-rejected": "PENDING diagnostic/control pair changes only the provider of OPERATOR(.y.) from an interface-block generic to a type-bound generic interface of the same operator and result behavior; the USE rename is otherwise identical."
        }
        by_rule["C1407"]["oracle"] = "Source registration only for this packet; no C1407 fixture is claimed because the portable control requires defined-operator renaming, which is not accepted by the frozen LFortran target."
        by_rule["C1407"]["oracle_limitation"] = "No C1407 execution, diagnostic, or coverage claim is supplied by the use_association_14_2_2 packet."
    if "S14.2.2-002" in by_rule and "use-accesses-abstract-interface" not in FACETS_BY_RULE.get("S14.2.2-002", []):
        by_rule["S14.2.2-002"].setdefault("pending", {})["use-accesses-abstract-interface"] = (
            "PENDING restored after review: the positive probe still uses an abstract interface as supporting source, "
            "but this packet does not claim the facet because a distinct portable feature mutant for the abstract "
            "interface identity was not supplied."
        )
    for rule, facets in ALL_COVERED_FACETS_BY_RULE.items():
        row = by_rule[rule]
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = ORACLES[rule]
        row["oracle_limitation"] = LIMITATIONS[rule]
    return updated


def generate(root=ROOT, check=False):
    root = Path(root)
    files, specs = build_corpus(root)
    outputs = dict(files)
    catalogue_path = root / CATALOGUE
    updated = synced_catalogue(json.loads(catalogue_path.read_text()))
    outputs[catalogue_path] = (json.dumps(updated, indent=2) + "\n").encode("utf-8")
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in outputs.items()
                 if not path.exists() or path.read_bytes() != raw]
        if stale:
            raise SystemExit("generated files are stale: " + ", ".join(stale))
        return files, specs
    fixture_root = root / FIXTURE_ROOT
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    for path, raw in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    sys.path.insert(0, str(root / "tests"))
    from suite_data import Registry
    Registry(root).render(write=True)
    return files, specs


def std_flag(compiler, std):
    return f"--std={std}" if "lfortran" in Path(compiler).name.lower() else f"-std={std}"


def run_command(argv, cwd, timeout=30):
    env = os.environ.copy()
    env["TMPDIR"] = str((ROOT / ".use_association_14_2_2_tmp").resolve())
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
    specs = source_specs()
    scratch_root = root / ".use_association_14_2_2_mutation_work"
    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    scratch_root.mkdir()
    results = []
    try:
        for cid, spec in specs.items():
            parent_dir = scratch_root / cid / "parent"
            parent_dir.mkdir(parents=True)
            parent = compile_and_run(spec["source"].encode("ascii"), compiler, std, parent_dir)
            parent_ok = (parent["phase"] == "run" and parent["returncode"] == 0 and
                         parent["stdout"] == spec["completion"] and parent["stderr"] == "")
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
            shutil.rmtree(root / ".use_association_14_2_2_tmp", ignore_errors=True)
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
        parents = sum(1 for row in results if row["mutation"] == "parent" and row["ok"])
        failed = [row for row in results if not row["ok"]]
        if failed:
            for row in failed:
                print(json.dumps({k: row[k] for k in ("case", "mutation", "phase", "returncode", "stdout", "stderr") if k in row}, indent=2))
            raise SystemExit(f"mutation matrix failed: {len(failed)} bad rows out of {len(results)}")
        print(f"mutation matrix OK: {parents} parents passed; {total} mutants failed on {Path(args.compiler).name} {args.std}")
        return
    generate(ROOT, check=args.check)
    print(f"generated {len(CASES)} valid and {len(DIAGNOSTIC_CASES)} invalid {TOPIC} fixtures covering {sum(len(v) for v in ALL_COVERED_FACETS_BY_RULE.values())} facets")

if __name__ == "__main__":
    main()
