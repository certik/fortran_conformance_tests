#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 name association rules in 19.5.1.3-19.5.1.6."""

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
TOPIC = "association_19_5_1"
FIXTURE_ROOT = Path("tests/fixtures") / TOPIC
SUMMARY = "ASSOCIATION 19.5.1"

CATALOGUES = {
    "19.5.1.3": "doc/catalogues/use_association_summary_19_5_1_3.json",
    "19.5.1.4": "doc/catalogues/host_association_19_5_1_4.json",
    "19.5.1.5": "doc/catalogues/linkage_association_19_5_1_5.json",
    "19.5.1.6": "doc/catalogues/construct_association_19_5_1_6.json",
}

ORACLE_PREFIXES = {
    "S19.5.1.3-001": "S19.5.1.3-001 use association runtime fixtures: ",
    "S19.5.1.4-001": "S19.5.1.4-001 host access runtime fixtures: ",
    "S19.5.1.4-003": "S19.5.1.4-003 host hiding by use/global names runtime fixtures: ",
    "S19.5.1.4-004": "S19.5.1.4-004 local identifiers hide host runtime fixtures: ",
    "S19.5.1.4-007": "S19.5.1.4-007 hidden host type object access runtime fixture: ",
    "S19.5.1.4-008": "S19.5.1.4-008 host external procedure positive-control fixture: ",
    "S19.5.1.4-009": "S19.5.1.4-009 host intrinsic procedure positive-control fixture: ",
    "S19.5.1.5-001": "S19.5.1.5-001 BIND(C) linkage runtime fixture: ",
    "S19.5.1.6-001": "S19.5.1.6-001 construct association establishment runtime fixtures: ",
    "S19.5.1.6-003": "S19.5.1.6-003 selector object/value association runtime fixtures: ",
    "S19.5.1.6-004": "S19.5.1.6-004 associate-name lifetime/access runtime fixture: ",
    "S19.5.1.6-005": "S19.5.1.6-005 pointer selector target association runtime fixture: ",
}
LIMIT_PREFIXES = {rule: prefix.replace(" runtime fixture", " fixture boundaries").replace(" runtime fixtures", " fixture boundaries") for rule, prefix in ORACLE_PREFIXES.items()}

ORACLES = {
    "S19.5.1.3-001": ORACLE_PREFIXES["S19.5.1.3-001"] + (
        "one module/client program USEs a module variable, renames it as alias, changes it in one contained procedure, "
        "and reads the same storage later in another contained procedure. Distinct assertions check imported-name access, "
        "renamed access, a wrong-resolution local sentinel, and execution-long persistence. Feature mutations redirect the "
        "USE to a wrong variable, remove the rename, and skip the earlier write."
    ),
    "S19.5.1.4-001": ORACLE_PREFIXES["S19.5.1.4-001"] + (
        "host access is observed by exact sentinels in derived type definitions, internal and module procedures, host "
        "variables, host nonvariable type/procedure/generic identifiers, and preserved PARAMETER/TARGET attributes. "
        "Every assertion has a wrong-resolution or feature-removal mutation that remains conforming. Interface-body and "
        "submodule access plus broad taxonomy examples without a portable single-image value remain pending."
    ),
    "S19.5.1.4-003": ORACLE_PREFIXES["S19.5.1.4-003"] + (
        "one program checks that a use-associated same nongeneric name and a module-name global identifier hide host "
        "integers with the same spelling: provider x=602 is read while host x=601 remains, and USE m accesses module "
        "m's value=604 while host integer m=603 remains. Mutations redirect the use/module names to wrong companions."
    ),
    "S19.5.1.4-004": ORACLE_PREFIXES["S19.5.1.4-004"] + (
        "local declaration fixtures give each claimed list item its own wrong-resolution sentinel. In every case a host "
        "integer x has one value, the local declaration creates a different local identifier x and observes its own exact "
        "value, and the feature mutation removes or renames that local declaration so the host entity is seen or changed."
    ),
    "S19.5.1.4-007": ORACLE_PREFIXES["S19.5.1.4-007"] + (
        "a host object obj of host type box remains accessible after an inner local type box hides the host type name; "
        "the fixture writes and reads obj%v exactly. A feature mutation adds a local obj of the local type, proving the "
        "host object/subobject access is load-bearing."
    ),
    "S19.5.1.4-008": ORACLE_PREFIXES["S19.5.1.4-008"] + (
        "the host explicitly declares integer external function ext and an internal procedure invokes the host-associated "
        "implicit-interface function, observing exact 45. A local statement-function mutation of ext returns a distinct "
        "value. Other establishment paths stay pending as source-control matrix entries."
    ),
    "S19.5.1.4-009": ORACLE_PREFIXES["S19.5.1.4-009"] + (
        "the host establishes ABS as intrinsic and an internal procedure accesses that host-associated intrinsic to compute "
        "exact ABS(-3)=3. A local statement-function mutation named abs returns 37. Other establishment paths stay pending."
    ),
    "S19.5.1.5-001": ORACLE_PREFIXES["S19.5.1.5-001"] + (
        "a Fortran module variable with BIND(C,name='assoc_link_value') is modified by C companion functions to 42 and "
        "then 77, and Fortran reads both exact values through the same variable, proving C linkage and program-long "
        "persistence. COMMON/C linkage remains pending because the suite supports C sources but this packet ships only the "
        "portable BIND module-variable companion."
    ),
    "S19.5.1.6-001": ORACLE_PREFIXES["S19.5.1.6-001"] + (
        "ASSOCIATE, SELECT TYPE, and SELECT RANK fixtures use variable selectors and two-way sentinels: writes through the "
        "associate name are visible in the selector and writes through the selector are visible through the associate name. "
        "CHANGE TEAM remains pending as coarray/team dependent."
    ),
    "S19.5.1.6-003": ORACLE_PREFIXES["S19.5.1.6-003"] + (
        "variable-selector object association is checked by two-way ASSOCIATE writes. Expression and vector-subscript "
        "selectors are checked as pre-evaluated values: changing the contributing variables or selected array elements "
        "inside the block does not change the associate-name values."
    ),
    "S19.5.1.6-004": ORACLE_PREFIXES["S19.5.1.6-004"] + (
        "inside one ASSOCIATE block the associate name first reads the selector value, remains associated through an IF "
        "and DO block, and after END ASSOCIATE a host variable with the same name is assigned independently while the "
        "selector keeps the value written through the associate name."
    ),
    "S19.5.1.6-005": ORACLE_PREFIXES["S19.5.1.6-005"] + (
        "with pointer p associated to target t, ASSOCIATE(a=>p) writes through a and observes t, then writes t and "
        "observes a, proving the associate name is associated with the pointer target. No runtime inquiry can prove the "
        "absence of the POINTER attribute, so that facet remains pending."
    ),
}

LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "only the listed single-image exact integer/logical effects are claimed. Coarray/team cases, submodule execution, "
        "enum/enumeration syntax, inaccessible-name negative diagnostics, reverse accessibility, DATA ordering restrictions, "
        "COMMON/C linkage, IMPORT-only interface-body failure modes, ASYNCHRONOUS/VOLATILE runtime behavior, absent "
        "ALLOCATABLE/POINTER attribute inquiries, addresses, diagnostic text, and processor-dependent representations are "
        "not asserted and remain pending where appropriate."
    ) for rule in ORACLE_PREFIXES
}

CASES = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def add_case(variant, rule, facets, source, mutations, files=None, evidence="effect"):
    cid = identifier_from(variant, rule)
    if files is None:
        files = {"source.f90": source}
    CASES[variant] = {
        "id": cid,
        "variant": variant,
        "rule": rule,
        "facets": facets,
        "evidence": evidence,
        "files": files,
        "mutations": mutations,
    }


def identifier_from(variant, rule):
    return rule.replace(".", "_").replace("-", "_") + "_valid__association_19_5_1_" + variant


def completion(variant):
    return f"{SUMMARY} {variant.upper().replace('_', ' ')} OK\n"


def header(rule, facets, evidence="effect"):
    covers = f"! covers: {' '.join(facets)}\n"
    if len(covers.rstrip("\n")) > 132:
        covers = "! covers:\n" + "".join(f"!   {facet}\n" for facet in facets)
    return (
        f"! rule: {rule}\n"
        f"{covers}"
        f"! evidence: {evidence}\n"
        "! standard: f2023\n"
        "! oracle-basis: standard\n"
    )

EXPECT = r'''
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
'''

def wrap_program(name, declarations, setup, calls, contains_body="", extra_after=""):
    return f'''program {name}
  implicit none
{declarations}
  checks = 0
{setup}
{calls}
  write(*,'(a)') '{completion(name.replace('association_', '')).strip()}'
{EXPECT}{contains_body}end program {name}
{extra_after}'''

# 19.5.1.3 use association
use_source = header("S19.5.1.3-001", [
    "use-stmt-name-association", "use-renaming-cross-reference", "use-associated-access-throughout-execution"] ) + r'''module association_use_provider
  implicit none
  integer :: shared = 41
  integer :: wrong_shared = 91
end module association_use_provider
program association_use_persistence
  use association_use_provider, only: alias => shared, wrong_shared
  implicit none
  integer :: shared, first_seen, later_seen, checks
  shared = 501
  first_seen = -11
  later_seen = -12
  checks = 0
  call read_imported()
  call mutate_imported()
  call read_later()
  call expect_equal(first_seen, 41, 'use associated original value')
  call expect_equal(alias, 77, 'renamed use association after write')
  call expect_equal(later_seen, 77, 'use association persists through execution')
  call expect_equal(shared, 501, 'local wrong-resolution sentinel')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 USE PERSISTENCE OK'
contains
  subroutine read_imported()
    implicit none
    first_seen = alias
  end subroutine read_imported
  subroutine mutate_imported()
    implicit none
    alias = 77
  end subroutine mutate_imported
  subroutine read_later()
    implicit none
    later_seen = alias
  end subroutine read_later
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_use_persistence
'''
add_case("use_persistence", "S19.5.1.3-001", [
    "use-stmt-name-association", "use-renaming-cross-reference", "use-associated-access-throughout-execution"], use_source, [
    {"id": "use-imports-wrong-entity", "kind": "feature", "facets": ["use-stmt-name-association"], "replacements": [("alias => shared", "alias => wrong_shared")]},
    {"id": "rename-removed-source-name-used", "kind": "feature", "facets": ["use-renaming-cross-reference"], "replacements": [
        ("only: alias => shared, wrong_shared", "only: shared, wrong_shared"),
        ("  integer :: shared, first_seen, later_seen, checks", "  integer :: first_seen, later_seen, checks"),
        ("  shared = 501", "  ! local same-name sentinel removed with the rename"),
        ("first_seen = alias", "first_seen = shared"),
        ("alias = 77", "shared = 77"),
        ("later_seen = alias", "later_seen = shared"),
        ("expect_equal(alias, 77", "expect_equal(shared, 77"),
    ]},
    {"id": "earlier-use-write-skipped", "kind": "feature", "facets": ["use-associated-access-throughout-execution"], "replacements": [("    alias = 77", "    ! use-associated write removed by mutation")]},
])

# 19.5.1.4 p1 host access core
host_core = header("S19.5.1.4-001", [
    "internal-subprogram-host-instance-access", "host-variable-previously-declared",
    "host-nonvariable-previously-defined", "host-identifier-and-attributes-preserved"]) + r'''program association_host_core
  implicit none
  type :: box
    integer :: v
  end type box
  interface g
    procedure g_int
  end interface g
  integer, parameter :: p = 3
  integer, target :: t
  integer :: x, y, observed, observed_y, generic_seen, type_seen, extent_seen, pointer_seen, checks
  integer, pointer :: q
  x = 1
  y = 43
  t = 5
  observed = -11
  observed_y = -16
  generic_seen = -12
  type_seen = -13
  extent_seen = -14
  pointer_seen = -15
  checks = 0
  call inner()
  call expect_equal(x, 42, 'host instance variable changed')
  call expect_equal(observed, 42, 'host variable previously declared')
  call expect_equal(observed_y, 43, 'separate host variable previously declared')
  call expect_equal(type_seen, 64, 'host type nonvariable previously defined')
  call expect_equal(generic_seen, 77, 'host generic nonvariable previously defined')
  call expect_equal(extent_seen, 3, 'host parameter attribute preserved')
  call expect_equal(pointer_seen, 5, 'host target attribute preserved')
  call expect_equal(checks, 7, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST CORE OK'
contains
  integer function g_int(n)
    integer, intent(in) :: n
    g_int = 76 + n
  end function g_int
  subroutine inner()
    implicit none
    type(box) :: local_box
    integer :: arr(p)
    x = 42
    observed = x
    observed_y = y
    local_box = box(64)
    type_seen = local_box%v
    generic_seen = g(1)
    extent_seen = size(arr)
    q => t
    pointer_seen = q
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_core
'''
add_case("host_core", "S19.5.1.4-001", [
    "internal-subprogram-host-instance-access", "host-variable-previously-declared",
    "host-nonvariable-previously-defined", "host-identifier-and-attributes-preserved"], host_core, [
    {"id": "local-x-hides-host-instance", "kind": "feature", "facets": ["internal-subprogram-host-instance-access"], "replacements": [("    type(box) :: local_box\n    integer :: arr(p)", "    type(box) :: local_box\n    integer :: arr(p)\n    integer :: x")]},
    {"id": "local-y-hides-host-variable", "kind": "feature", "facets": ["host-variable-previously-declared"], "replacements": [
        ("    type(box) :: local_box\n    integer :: arr(p)", "    type(box) :: local_box\n    integer :: arr(p)\n    integer :: y"),
        ("    observed_y = y", "    y = 44\n    observed_y = y"),
    ]},
    {"id": "local-type-hides-host-type", "kind": "feature", "facets": ["host-nonvariable-previously-defined"], "replacements": [
        ("    type(box) :: local_box\n    integer :: arr(p)", "    type :: box\n      integer :: v = 65\n    end type box\n    type(box) :: local_box\n    integer :: arr(p)"),
        ("local_box = box(64)", "local_box = box()"),
    ]},
    {"id": "local-statement-function-hides-host-generic", "kind": "feature", "facets": ["host-nonvariable-previously-defined"], "replacements": [
        ("    type(box) :: local_box\n    integer :: arr(p)", "    type(box) :: local_box\n    integer :: arr(p)\n    integer :: g, n\n    g(n) = 80 + n"),
    ]},
    {"id": "parameter-attribute-not-used", "kind": "feature", "facets": ["host-identifier-and-attributes-preserved"], "replacements": [("integer :: arr(p)", "integer :: arr(4)")]},
    {"id": "target-object-swapped", "kind": "feature", "facets": ["host-identifier-and-attributes-preserved"], "replacements": [
        ("integer, target :: t", "integer, target :: t, wrong_t"),
        ("  t = 5", "  t = 5\n  wrong_t = 6"),
        ("q => t\n    pointer_seen = q", "q => wrong_t\n    pointer_seen = q"),
    ]},
])

host_derived_type = header("S19.5.1.4-001", ["derived-type-host-access"]) + r'''program association_host_derived_type
  implicit none
  integer, parameter :: n = 3
  integer, parameter :: wrong_n = 5
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 3, 'derived type definition used host parameter')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST DERIVED TYPE OK'
contains
  subroutine inner()
    implicit none
    type :: local_box
      character(len=n) :: text
    end type local_box
    type(local_box) :: obj
    observed = len(obj%text)
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_derived_type
'''
add_case("host_derived_type", "S19.5.1.4-001", ["derived-type-host-access"], host_derived_type, [
    {"id": "component-uses-wrong-host-parameter", "kind": "feature", "facets": ["derived-type-host-access"], "replacements": [("character(len=n) :: text", "character(len=wrong_n) :: text")]},
])

host_module_proc = header("S19.5.1.4-001", ["module-subprogram-host-access"]) + r'''module association_host_module_proc_mod
  implicit none
  integer :: x = 42
contains
  subroutine read_module_host(observed)
    implicit none
    integer, intent(out) :: observed
    observed = x
  end subroutine read_module_host
end module association_host_module_proc_mod
program association_host_module_proc
  use association_host_module_proc_mod, only: read_module_host
  implicit none
  integer :: observed, checks
  observed = -11
  checks = 0
  call read_module_host(observed)
  call expect_equal(observed, 42, 'module procedure host access')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST MODULE PROC OK'
contains
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_module_proc
'''
add_case("host_module_proc", "S19.5.1.4-001", ["module-subprogram-host-access"], host_module_proc, [
    {"id": "module-procedure-local-x-hides-host", "kind": "feature", "facets": ["module-subprogram-host-access"], "replacements": [("    integer, intent(out) :: observed\n    observed = x", "    integer, intent(out) :: observed\n    integer :: x\n    x = 43\n    observed = x")]},
])

host_hiding_global = header("S19.5.1.4-003", ["use-associated-name-hides-host", "module-name-global-hides-host"]) + r'''module association_provider_x
  implicit none
  integer :: x = 602
  integer :: wrong_x = 692
end module association_provider_x
module m
  implicit none
  integer :: value = 604
end module m
module wrong_m
  implicit none
  integer :: value = 694
end module wrong_m
program association_host_hiding_global
  implicit none
  integer :: x, m, use_seen, module_seen, checks
  x = 601
  m = 603
  use_seen = -11
  module_seen = -12
  checks = 0
  call read_use_name()
  call read_module_name()
  call expect_equal(use_seen, 602, 'use-associated name hides host')
  call expect_equal(x, 601, 'host x unchanged by use association')
  call expect_equal(module_seen, 604, 'module-name global hides host')
  call expect_equal(m, 603, 'host m unchanged by module-name')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST HIDING GLOBAL OK'
contains
  subroutine read_use_name()
    use association_provider_x, only: x, wrong_x
    implicit none
    use_seen = x
  end subroutine read_use_name
  subroutine read_module_name()
    use m, only: value
    implicit none
    module_seen = value
  end subroutine read_module_name
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_hiding_global
'''
add_case("host_hiding_global", "S19.5.1.4-003", ["use-associated-name-hides-host", "module-name-global-hides-host"], host_hiding_global, [
    {"id": "use-name-redirected", "kind": "feature", "facets": ["use-associated-name-hides-host"], "replacements": [("use association_provider_x, only: x, wrong_x", "use association_provider_x, only: x => wrong_x, wrong_x")]},
    {"id": "module-name-redirected", "kind": "feature", "facets": ["module-name-global-hides-host"], "replacements": [("use m, only: value", "use wrong_m, only: value")]},
])

external_global = header("S19.5.1.4-003", ["external-global-name-hides-host"]) + r'''program association_external_global_hide
  implicit none
  integer :: x, observed, checks
  x = 605
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 606, 'external global name hides host')
  call expect_equal(x, 605, 'host x unchanged by external global')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 EXTERNAL GLOBAL HIDE OK'
contains
  subroutine inner()
    implicit none
    integer, external :: x
    observed = x()
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_external_global_hide
integer function x()
  implicit none
  x = 606
end function x
'''
add_case("external_global_hide", "S19.5.1.4-003", ["external-global-name-hides-host"], external_global, [
    {"id": "external-declaration-removed-host-seen", "kind": "feature", "facets": ["external-global-name-hides-host"], "replacements": [("    integer, external :: x\n    observed = x()", "    ! external declaration removed by mutation\n    observed = x")]},
])

# Local declaration cases for S19.5.1.4-004.
def local_case_source(variant, facet, host_init, local_body, assertions, extra_decls="", extra_after=""):
    return header("S19.5.1.4-004", [facet]) + f'''program association_{variant}
  implicit none
  integer :: abs, x, observed, checks
{extra_decls}  x = {host_init}
  observed = -11
  checks = 0
  call inner()
{assertions}  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') '{completion(variant).strip()}'
contains
  subroutine inner()
    implicit none
{local_body}  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_{variant}
{extra_after}'''

def add_local(variant, facet, host_init, local_body, expected, mutation_old, mutation_new, extra_decls="", extra_after=""):
    assertions = f"  call expect_equal(observed, {expected}, '{facet} local value')\n  call expect_equal(x, {host_init}, '{facet} host unchanged')\n"
    src = local_case_source(variant, facet, host_init, local_body, assertions, extra_decls, extra_after)
    add_case(variant, "S19.5.1.4-004", [facet], src, [
        {"id": "remove-local-declaration-host-seen", "kind": "feature", "facets": [facet], "replacements": [(mutation_old, mutation_new)]},
    ])

add_local("local_object", "local-object-declaration-hides-host", 201,
          "    integer :: x\n    x = 302\n    observed = x\n", 302,
          "    integer :: x\n    x = 302", "    ! local object declaration removed by mutation\n    x = 302")
add_local("local_function", "local-function-name-hides-host", 202,
          "    integer :: x, n\n    x(n) = 303 + n\n    observed = x(0)\n", 303,
          "    integer :: x, n\n    x(n) = 303 + n\n    observed = x(0)", "    ! local statement function removed by mutation\n    x = 303\n    observed = x")
type_param_src = header("S19.5.1.4-004", ["local-type-param-name-hides-host"]) + r'''program association_local_type_param
  implicit none
  integer, parameter :: x = 203
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 304, 'local-type-param-name-hides-host local value')
  call expect_equal(x, 203, 'local-type-param-name-hides-host host unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL TYPE PARAM OK'
contains
  subroutine inner()
    implicit none
    type :: box(x)
      integer, len :: x = 304
      character(len=x) :: text
    end type box
    type(box) :: obj
    observed = len(obj%text)
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_type_param
'''
add_case("local_type_param", "S19.5.1.4-004", ["local-type-param-name-hides-host"], type_param_src, [
    {"id": "remove-local-declaration-host-seen", "kind": "feature", "facets": ["local-type-param-name-hides-host"], "replacements": [("    type :: box(x)\n      integer, len :: x = 304\n      character(len=x) :: text", "    type :: box\n      character(len=x) :: text")]},
])
add_local("local_named_constant", "local-named-constant-hides-host", 205,
          "    integer, parameter :: x = 306\n    observed = x\n", 306,
          "    integer, parameter :: x = 306\n    observed = x", "    ! local named constant removed by mutation\n    observed = x")
add_local("local_common_variable", "local-common-variable-hides-host", 207,
          "    integer :: x\n    common /association_local_common_blk/ x\n    x = 308\n    observed = x\n", 308,
          "    integer :: x\n    common /association_local_common_blk/ x", "    ! local common variable declaration removed by mutation")
add_local("local_array", "local-array-name-hides-host", 208,
          "    integer :: x\n    dimension x(1)\n    x = [309]\n    observed = x(1)\n", 309,
          "    integer :: x\n    dimension x(1)\n    x = [309]\n    observed = x(1)", "    ! local array declaration removed by mutation\n    x = 309\n    observed = x")
add_local("local_data_initialized", "local-data-initialized-variable-hides-host", 209,
          "    integer :: x\n    data x /310/\n    observed = x\n", 310,
          "    integer :: x\n    data x /310/", "    ! local DATA initialized variable removed by mutation")
add_local("local_equivalenced", "local-equivalenced-object-hides-host", 211,
          "    integer :: x, y\n    equivalence (x, y)\n    y = 312\n    observed = x\n", 312,
          "    integer :: x, y\n    equivalence (x, y)", "    ! local equivalenced object removed by mutation", extra_decls="  integer :: y\n", extra_after="")

# Dummy/result/intrinsic/generic need custom source/mutations.
dummy_src = header("S19.5.1.4-004", ["local-dummy-arg-name-hides-host"]) + r'''program association_local_dummy
  implicit none
  integer :: x, actual, observed, checks
  x = 213
  actual = 313
  observed = -11
  checks = 0
  call inner(actual)
  call expect_equal(observed, 314, 'dummy argument local value')
  call expect_equal(actual, 314, 'actual changed through dummy')
  call expect_equal(x, 213, 'host x unchanged')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL DUMMY OK'
contains
  subroutine inner(x)
    implicit none
    integer, intent(inout) :: x
    x = 314
    observed = x
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_dummy
'''
add_case("local_dummy", "S19.5.1.4-004", ["local-dummy-arg-name-hides-host"], dummy_src, [
    {"id": "dummy-renamed-host-seen", "kind": "feature", "facets": ["local-dummy-arg-name-hides-host"], "replacements": [("  subroutine inner(x)\n    implicit none\n    integer, intent(inout) :: x\n    x = 314\n    observed = x", "  subroutine inner(y)\n    implicit none\n    integer, intent(inout) :: y\n    x = 314\n    observed = y")]},
])

result_src = header("S19.5.1.4-004", ["local-result-name-hides-host"]) + r'''program association_local_result
  implicit none
  integer :: x, observed, checks
  x = 215
  observed = -11
  checks = 0
  observed = f()
  call expect_equal(observed, 316, 'result name local value')
  call expect_equal(x, 215, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL RESULT OK'
contains
  integer function f() result(x)
    implicit none
    x = 316
  end function f
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_result
'''
add_case("local_result", "S19.5.1.4-004", ["local-result-name-hides-host"], result_src, [
    {"id": "result-renamed-host-seen", "kind": "feature", "facets": ["local-result-name-hides-host"], "replacements": [("  integer function f() result(x)\n    implicit none\n    x = 316", "  integer function f() result(y)\n    implicit none\n    y = -416\n    x = 316")]},
])

intrinsic_src = header("S19.5.1.4-004", ["local-intrinsic-procedure-name-hides-host"]) + r'''program association_local_intrinsic
  implicit none
  integer :: abs, x, observed, checks
  x = 217
  abs = 39
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 3, 'local intrinsic abs value')
  call expect_equal(x, 217, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL INTRINSIC OK'
contains
  subroutine inner()
    implicit none
    intrinsic :: abs
    observed = abs(-3)
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_intrinsic
'''
add_case("local_intrinsic", "S19.5.1.4-004", ["local-intrinsic-procedure-name-hides-host"], intrinsic_src, [
    {"id": "intrinsic-statement-removed-host-seen", "kind": "feature", "facets": ["local-intrinsic-procedure-name-hides-host"], "replacements": [("    intrinsic :: abs\n    observed = abs(-3)", "    ! local intrinsic statement removed by mutation\n    observed = abs")]},
])

generic_src = header("S19.5.1.4-004", ["local-generic-name-hides-host"]) + r'''program association_local_generic
  implicit none
  interface x
    integer function host_x(n)
      integer, intent(in) :: n
    end function host_x
  end interface
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 318, 'local generic value')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL GENERIC OK'
contains
  subroutine inner()
    implicit none
    interface x
      integer function local_x(n)
        integer, intent(in) :: n
      end function local_x
    end interface
    observed = x(0)
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_generic
integer function host_x(n)
  implicit none
  integer, intent(in) :: n
  host_x = 217 + n
end function host_x
integer function local_x(n)
  implicit none
  integer, intent(in) :: n
  local_x = 318 + n
end function local_x
'''
add_case("local_generic", "S19.5.1.4-004", ["local-generic-name-hides-host"], generic_src, [
    {"id": "local-generic-interface-removed-host-seen", "kind": "feature", "facets": ["local-generic-name-hides-host"], "replacements": [("    interface x\n      integer function local_x(n)\n        integer, intent(in) :: n\n      end function local_x\n    end interface\n    observed = x(0)", "    ! local generic interface removed by mutation\n    observed = x(0)")]},
])

interface_entity_src = header("S19.5.1.4-004", ["local-interface-entity-hides-host"]) + r'''program association_local_interface_entity
  implicit none
  integer :: x, observed, checks
  x = 219
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 320, 'local interface entity value')
  call expect_equal(x, 219, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL INTERFACE ENTITY OK'
contains
  subroutine inner()
    implicit none
    interface
      integer function x()
      end function x
    end interface
    observed = x()
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_interface_entity
integer function x()
  implicit none
  x = 320
end function x
'''
add_case("local_interface_entity", "S19.5.1.4-004", ["local-interface-entity-hides-host"], interface_entity_src, [
    {"id": "interface-body-removed-host-seen", "kind": "feature", "facets": ["local-interface-entity-hides-host"], "replacements": [("    interface\n      integer function x()\n      end function x\n    end interface\n    observed = x()", "    ! local interface body removed by mutation\n    observed = x")]},
])

derived_type_name_src = header("S19.5.1.4-004", ["local-derived-type-name-hides-host"]) + r'''program association_local_derived_type_name
  implicit none
  integer :: x, observed, checks
  x = 221
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 322, 'local derived type name value')
  call expect_equal(x, 221, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL DERIVED TYPE NAME OK'
contains
  subroutine inner()
    implicit none
    type :: x
      integer :: v
    end type x
    type(x) :: obj
    obj%v = 322
    observed = obj%v
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_derived_type_name
'''
add_case("local_derived_type_name", "S19.5.1.4-004", ["local-derived-type-name-hides-host"], derived_type_name_src, [
    {"id": "derived-type-definition-removed-host-seen", "kind": "feature", "facets": ["local-derived-type-name-hides-host"], "replacements": [("    type :: x\n      integer :: v\n    end type x\n    type(x) :: obj\n    obj%v = 322\n    observed = obj%v", "    ! local derived type definition removed by mutation\n    observed = x")]},
])

proc_pointer_src = header("S19.5.1.4-004", ["local-procedure-pointer-external-hides-host"]) + r'''program association_local_proc_pointer
  implicit none
  abstract interface
    integer function intfun()
    end function intfun
  end interface
  procedure(intfun), pointer :: x
  integer :: observed, checks
  x => host_target
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 324, 'local procedure pointer value')
  call expect_equal(x(), 223, 'host procedure pointer unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL PROC POINTER OK'
contains
  integer function host_target()
    implicit none
    host_target = 223
  end function host_target
  integer function local_target()
    implicit none
    local_target = 324
  end function local_target
  subroutine inner()
    implicit none
    procedure(intfun), pointer :: x
    x => local_target
    observed = x()
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_proc_pointer
'''
add_case("local_proc_pointer", "S19.5.1.4-004", ["local-procedure-pointer-external-hides-host"], proc_pointer_src, [
    {"id": "procedure-pointer-declaration-removed-host-seen", "kind": "feature", "facets": ["local-procedure-pointer-external-hides-host"], "replacements": [("    procedure(intfun), pointer :: x\n    x => local_target", "    ! local procedure pointer declaration removed by mutation\n    x => local_target")]},
])

# Host type name hidden but object/subobject still accessible.
host_type_obj = header("S19.5.1.4-007", ["host-derived-type-object-remains-accessible", "host-derived-type-subobject-remains-accessible"]) + r'''program association_host_type_object
  implicit none
  type :: box
    integer :: v
  end type box
  type(box) :: obj
  integer :: observed, checks
  obj%v = 401
  observed = -11
  checks = 0
  call inner()
  call expect_equal(obj%v, 402, 'host object remains accessible')
  call expect_equal(observed, 402, 'host subobject remains accessible')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST TYPE OBJECT OK'
contains
  subroutine inner()
    implicit none
    type :: box
      integer :: v = 499
    end type box
    obj%v = 402
    observed = obj%v
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_type_object
'''
add_case("host_type_object", "S19.5.1.4-007", ["host-derived-type-object-remains-accessible", "host-derived-type-subobject-remains-accessible"], host_type_obj, [
    {"id": "local-object-hides-host-object", "kind": "feature", "facets": ["host-derived-type-object-remains-accessible"], "replacements": [("    type :: box\n      integer :: v = 499\n    end type box\n    obj%v = 402", "    type :: box\n      integer :: v = 499\n    end type box\n    type(box) :: obj\n    obj%v = 402")]},
    {"id": "subobject-read-uses-local-object", "kind": "feature", "facets": ["host-derived-type-subobject-remains-accessible"], "replacements": [("    observed = obj%v", "    block\n      type(box) :: local_subobject_source\n      observed = local_subobject_source%v\n    end block")]},
])

# Positive controls for host external/intrinsic restrictions.
host_external = header("S19.5.1.4-008", ["host-external-attribute-required", "host-established-function-type-required"], "positive-control") + r'''program association_host_external
  implicit none
  integer, external :: ext
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 45, 'host external function value')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST EXTERNAL OK'
contains
  subroutine inner()
    implicit none
    observed = ext(3)
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_external
integer function ext(n)
  implicit none
  integer, intent(in) :: n
  ext = 42 + n
end function ext
'''
host_intrinsic = header("S19.5.1.4-009", ["host-intrinsic-establishment-required"], "positive-control") + r'''program association_host_intrinsic
  implicit none
  intrinsic :: abs
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 3, 'host intrinsic abs value')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST INTRINSIC OK'
contains
  subroutine inner()
    implicit none
    observed = abs(-3)
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_intrinsic
'''
add_case("host_intrinsic", "S19.5.1.4-009", ["host-intrinsic-establishment-required"], host_intrinsic, [
    {"id": "local-object-hides-host-intrinsic", "kind": "feature", "facets": ["host-intrinsic-establishment-required"], "replacements": [("    observed = abs(-3)", "    integer :: abs\n    abs = 37\n    observed = abs")]},
], evidence="positive-control")

# Linkage association with C companion.
link_fortran = header("S19.5.1.5-001", ["bind-module-variable-c-linkage", "linkage-association-program-long"]) + r'''module association_linkage_mod
  use iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c, name="assoc_link_value") :: link_value = 1_c_int
  interface
    subroutine c_set_link_value(v) bind(c, name="assoc_set_link_value")
      import c_int
      integer(c_int), value :: v
    end subroutine c_set_link_value
    integer(c_int) function c_get_link_value() bind(c, name="assoc_get_link_value")
      import c_int
    end function c_get_link_value
  end interface
end module association_linkage_mod
program association_linkage_bind_module
  use iso_c_binding, only: c_int
  use association_linkage_mod, only: link_value, c_set_link_value, c_get_link_value
  implicit none
  integer :: checks
  checks = 0
  link_value = 5_c_int
  call c_set_link_value(42_c_int)
  call expect_equal(int(link_value), 42, 'C write visible through BIND module variable')
  call expect_equal(int(c_get_link_value()), 42, 'C read sees Fortran BIND module variable')
  link_value = 11_c_int
  call c_set_link_value(77_c_int)
  call expect_equal(int(link_value), 77, 'linkage association persists through program execution')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LINKAGE BIND MODULE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_linkage_bind_module
'''
link_c = r'''extern int assoc_link_value;
void assoc_set_link_value(int v)
{
    assoc_link_value = v;
}
int assoc_get_link_value(void)
{
    return assoc_link_value;
}
'''
add_case("linkage_bind_module", "S19.5.1.5-001", ["bind-module-variable-c-linkage", "linkage-association-program-long"], link_fortran, [
    {"id": "c-writes-wrong-value-first", "kind": "feature", "facets": ["bind-module-variable-c-linkage"], "file": "link.c", "replacements": [("assoc_link_value = v;", "assoc_link_value = v + 1;")]},
    {"id": "second-c-write-skipped", "kind": "feature", "facets": ["linkage-association-program-long"], "replacements": [("  call c_set_link_value(77_c_int)", "  ! second C write removed by mutation")]},
], files={"source.f90": link_fortran, "link.c": link_c})

# Construct association fixtures.
construct_associate = header("S19.5.1.6-001", ["associate-establishes-selector-association"]) + r'''program association_construct_associate
  implicit none
  integer :: x, checks
  x = 1
  checks = 0
  associate (a => x)
    a = 42
    call expect_equal(x, 42, 'associate-to-selector write')
    x = 77
    call expect_equal(a, 77, 'selector-to-associate write')
  end associate
  call expect_equal(x, 77, 'selector final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT ASSOCIATE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_construct_associate
'''
add_case("construct_associate", "S19.5.1.6-001", ["associate-establishes-selector-association"], construct_associate, [
    {"id": "associate-wrong-selector", "kind": "feature", "facets": ["associate-establishes-selector-association"], "replacements": [("integer :: x, checks", "integer :: x, y, checks"), ("  x = 1", "  x = 1\n  y = 9"), ("associate (a => x)", "associate (a => y)")]},
])

select_type = header("S19.5.1.6-001", ["select-type-establishes-selector-association"]) + r'''program association_construct_select_type
  implicit none
  type :: parent
    integer :: v
  end type parent
  type, extends(parent) :: child
  end type child
  class(parent), allocatable :: poly
  integer :: checks
  allocate(child :: poly)
  poly%v = 1
  checks = 0
  select type (a => poly)
  type is (child)
    a%v = 42
    call expect_equal(poly%v, 42, 'select type associate-to-selector')
    poly%v = 77
    call expect_equal(a%v, 77, 'select type selector-to-associate')
  class default
    error stop 'wrong dynamic type'
  end select
  call expect_equal(poly%v, 77, 'select type final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT SELECT TYPE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_construct_select_type
'''
add_case("construct_select_type", "S19.5.1.6-001", ["select-type-establishes-selector-association"], select_type, [
    {"id": "select-type-wrong-final-write", "kind": "feature", "facets": ["select-type-establishes-selector-association"], "replacements": [("poly%v = 77", "poly%v = 76")]},
])

select_rank = header("S19.5.1.6-001", ["select-rank-establishes-selector-association"]) + r'''program association_construct_select_rank
  implicit none
  integer :: x(2), checks
  x = [1, 2]
  checks = 0
  call inner(x)
  call expect_equal(x(2), 77, 'select rank final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT SELECT RANK OK'
contains
  subroutine inner(selector)
    implicit none
    integer, intent(inout) :: selector(..)
    select rank (a => selector)
    rank (1)
      a(2) = 42
      call expect_equal(x(2), 42, 'select rank associate-to-selector')
      x(2) = 77
      call expect_equal(a(2), 77, 'select rank selector-to-associate')
    rank default
      error stop 'wrong rank'
    end select
  end subroutine inner
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_construct_select_rank
'''
add_case("construct_select_rank", "S19.5.1.6-001", ["select-rank-establishes-selector-association"], select_rank, [
    {"id": "select-rank-wrong-final-write", "kind": "feature", "facets": ["select-rank-establishes-selector-association"], "replacements": [("x(2) = 77", "x(2) = 76")]},
])

variable_object = header("S19.5.1.6-003", ["variable-selector-object-association"]) + construct_associate.split("\n", 5)[5].replace("ASSOCIATION 19.5.1 CONSTRUCT ASSOCIATE OK", "ASSOCIATION 19.5.1 VARIABLE OBJECT OK")
add_case("variable_object", "S19.5.1.6-003", ["variable-selector-object-association"], variable_object, [
    {"id": "variable-selector-wrong-object", "kind": "feature", "facets": ["variable-selector-object-association"], "replacements": [("integer :: x, checks", "integer :: x, y, checks"), ("  x = 1", "  x = 1\n  y = 9"), ("associate (a => x)", "associate (a => y)")]},
])

value_selectors = header("S19.5.1.6-003", ["expression-selector-value-association", "vector-subscript-section-value-association", "selector-value-evaluated-before-block"]) + r'''program association_value_selectors
  implicit none
  integer :: x, i, arr(3), idx(2), expr_seen, vector_seen(2), timed_seen, checks
  x = 5
  i = 1
  arr = [10, 20, 30]
  idx = [3, 1]
  expr_seen = -11
  vector_seen = [-12, -13]
  timed_seen = -14
  checks = 0
  associate (a => x + 1)
    expr_seen = a
    x = 100
    call expect_equal(a, 6, 'expression selector value unchanged')
  end associate
  associate (a => arr(idx))
    vector_seen = a
    arr(3) = 99
    call expect_equal(a(1), 30, 'vector subscript first value unchanged')
    call expect_equal(a(2), 10, 'vector subscript second value unchanged')
  end associate
  associate (a => arr(i) + 5)
    timed_seen = a
    i = 2
    arr(1) = 88
    call expect_equal(a, 15, 'selector value evaluated before block')
  end associate
  call expect_equal(expr_seen, 6, 'expression selector recorded value')
  call expect_equal(vector_seen(1), 30, 'vector selector recorded first')
  call expect_equal(vector_seen(2), 10, 'vector selector recorded second')
  call expect_equal(timed_seen, 15, 'timed selector recorded value')
  call expect_equal(checks, 8, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 VALUE SELECTORS OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_value_selectors
'''
add_case("value_selectors", "S19.5.1.6-003", ["expression-selector-value-association", "vector-subscript-section-value-association", "selector-value-evaluated-before-block"], value_selectors, [
    {"id": "expression-selector-uses-variable", "kind": "feature", "facets": ["expression-selector-value-association"], "replacements": [("associate (a => x + 1)", "associate (a => x)")]},
    {"id": "vector-selector-order-changed", "kind": "feature", "facets": ["vector-subscript-section-value-association"], "replacements": [("idx = [3, 1]", "idx = [1, 3]")]},
    {"id": "timed-selector-wrong-subscript", "kind": "feature", "facets": ["selector-value-evaluated-before-block"], "replacements": [("associate (a => arr(i) + 5)", "associate (a => arr(2) + 5)")]},
])

lifetime = header("S19.5.1.6-004", ["associate-name-remains-associated-through-block", "selector-accessed-by-associate-name", "construct-association-terminates-on-completion"]) + r'''program association_construct_lifetime
  implicit none
  integer :: x, a, observed, checks
  x = 1
  a = -777
  observed = -11
  checks = 0
  associate (a => x)
    call expect_equal(a, 1, 'associate name accesses selector')
    a = 42
    if (x == 42) then
      do observed = 1, 2
        a = a + observed
      end do
    end if
    call expect_equal(a, 45, 'associate name remains through block')
  end associate
  a = 99
  call expect_equal(x, 45, 'selector keeps associated write after construct')
  call expect_equal(a, 99, 'outer name restored after construct')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 CONSTRUCT LIFETIME OK'
contains
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_construct_lifetime
'''
add_case("construct_lifetime", "S19.5.1.6-004", ["associate-name-remains-associated-through-block", "selector-accessed-by-associate-name", "construct-association-terminates-on-completion"], lifetime, [
    {"id": "initial-selector-wrong", "kind": "feature", "facets": ["selector-accessed-by-associate-name"], "replacements": [("  x = 1", "  x = 2")]},
    {"id": "loop-update-removed", "kind": "feature", "facets": ["associate-name-remains-associated-through-block"], "replacements": [("        a = a + observed", "        ! block update removed by mutation")]},
    {"id": "outer-after-construct-changes-selector", "kind": "feature", "facets": ["construct-association-terminates-on-completion"], "replacements": [("  a = 99\n  call expect_equal(x, 45", "  x = 99\n  call expect_equal(x, 45")]},
])

pointer_target = header("S19.5.1.6-005", ["pointer-associate-name-target"]) + r'''program association_pointer_target
  implicit none
  integer, target :: t
  integer, pointer :: p
  integer :: checks
  t = 1
  p => t
  checks = 0
  associate (a => p)
    a = 42
    call expect_equal(t, 42, 'pointer associate writes target')
    t = 77
    call expect_equal(a, 77, 'target write visible through associate')
  end associate
  call expect_equal(t, 77, 'target final value')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 POINTER TARGET OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_pointer_target
'''
add_case("pointer_target", "S19.5.1.6-005", ["pointer-associate-name-target"], pointer_target, [
    {"id": "pointer-associated-wrong-target", "kind": "feature", "facets": ["pointer-associate-name-target"], "replacements": [("integer, target :: t", "integer, target :: t, u"), ("  t = 1", "  t = 1\n  u = 9"), ("  p => t", "  p => u")]},
])

# Covered facets by owning rule.
FACETS_BY_RULE = {}
for data in CASES.values():
    FACETS_BY_RULE.setdefault(data["rule"], [])
    for facet in data["facets"]:
        if facet not in FACETS_BY_RULE[data["rule"]]:
            FACETS_BY_RULE[data["rule"]].append(facet)

FACET_ASSERTION_MUTATION_TABLE = {
    "use-stmt-name-association": [("first_seen=41", "use-imports-wrong-entity")],
    "use-renaming-cross-reference": [("alias=77", "rename-removed-source-name-used")],
    "use-associated-access-throughout-execution": [("later_seen=77", "earlier-use-write-skipped")],
    "internal-subprogram-host-instance-access": [("host x=42 after inner", "local-x-hides-host-instance")],
    "host-variable-previously-declared": [("observed_y=43", "local-y-hides-host-variable")],
    "host-nonvariable-previously-defined": [
        ("type_seen=64", "local-type-hides-host-type"),
        ("generic_seen=77", "local-statement-function-hides-host-generic"),
    ],
    "host-identifier-and-attributes-preserved": [
        ("extent_seen=3", "parameter-attribute-not-used"),
        ("pointer_seen=5", "target-object-swapped"),
    ],
    "derived-type-host-access": [("observed=3", "component-uses-wrong-host-parameter")],
    "module-subprogram-host-access": [("observed=42", "module-procedure-local-x-hides-host")],
    "use-associated-name-hides-host": [("use_seen=602", "use-name-redirected")],
    "module-name-global-hides-host": [("module_seen=604", "module-name-redirected")],
    "external-global-name-hides-host": [("observed=606", "external-declaration-removed-host-seen")],
    "local-object-declaration-hides-host": [("observed=302", "remove-local-declaration-host-seen")],
    "local-function-name-hides-host": [("observed=303", "remove-local-declaration-host-seen")],
    "local-type-param-name-hides-host": [("observed=304", "remove-local-declaration-host-seen")],
    "local-named-constant-hides-host": [("observed=306", "remove-local-declaration-host-seen")],
    "local-common-variable-hides-host": [("observed=308", "remove-local-declaration-host-seen")],
    "local-array-name-hides-host": [("observed=309", "remove-local-declaration-host-seen")],
    "local-data-initialized-variable-hides-host": [("observed=310", "remove-local-declaration-host-seen")],
    "local-equivalenced-object-hides-host": [("observed=312", "remove-local-declaration-host-seen")],
    "local-dummy-arg-name-hides-host": [("observed=314", "dummy-renamed-host-seen")],
    "local-result-name-hides-host": [("observed=316", "result-renamed-host-seen")],
    "local-intrinsic-procedure-name-hides-host": [("observed=3", "intrinsic-statement-removed-host-seen")],
    "local-generic-name-hides-host": [("observed=318", "local-generic-interface-removed-host-seen")],
    "local-interface-entity-hides-host": [("observed=320", "interface-body-removed-host-seen")],
    "local-derived-type-name-hides-host": [("observed=322", "derived-type-definition-removed-host-seen")],
    "local-procedure-pointer-external-hides-host": [("observed=324", "procedure-pointer-declaration-removed-host-seen")],
    "host-derived-type-object-remains-accessible": [("obj%v=402", "local-object-hides-host-object")],
    "host-derived-type-subobject-remains-accessible": [("observed=402", "subobject-read-uses-local-object")],
    "host-intrinsic-establishment-required": [("observed=3", "local-object-hides-host-intrinsic")],
    "bind-module-variable-c-linkage": [("link_value=42", "c-writes-wrong-value-first")],
    "linkage-association-program-long": [("link_value=77", "second-c-write-skipped")],
    "associate-establishes-selector-association": [("a/x two-way 42/77", "associate-wrong-selector")],
    "select-type-establishes-selector-association": [("a%v/poly%v two-way", "select-type-wrong-final-write")],
    "select-rank-establishes-selector-association": [("a(2)/x(2) two-way", "select-rank-wrong-final-write")],
    "variable-selector-object-association": [("a/x two-way 42/77", "variable-selector-wrong-object")],
    "expression-selector-value-association": [("a remains 6", "expression-selector-uses-variable")],
    "vector-subscript-section-value-association": [("a=[30,10]", "vector-selector-order-changed")],
    "selector-value-evaluated-before-block": [("a remains 15", "timed-selector-wrong-subscript")],
    "associate-name-remains-associated-through-block": [("a remains 45 through block", "loop-update-removed")],
    "selector-accessed-by-associate-name": [("initial a=1", "initial-selector-wrong")],
    "construct-association-terminates-on-completion": [("outer a=99 after construct", "outer-after-construct-changes-selector")],
    "pointer-associate-name-target": [("a/t two-way 42/77", "pointer-associated-wrong-target")],
}


def case_files_with_headers(case):
    out = {}
    for name, text in case["files"].items():
        out[name] = text
    return out


def source_specs():
    specs = {}
    for variant, case in CASES.items():
        cid = case["id"]
        files = case_files_with_headers(case)
        files_sha = {name: sha(text.encode("ascii")) for name, text in files.items()}
        specs[cid] = {
            "id": cid,
            "variant": variant,
            "rule": case["rule"],
            "facets": case["facets"],
            "evidence": case["evidence"],
            "files": copy.deepcopy(files),
            "files_sha256": files_sha,
            "completion": completion(variant),
            "mutations": copy.deepcopy(case["mutations"]),
        }
    return specs


def manifest(case_id, variant, data):
    files = list(data["files"])
    build = []
    for name in files:
        if name.endswith(".f90"):
            build.append({"id": Path(name).stem, "source": name, "language": "fortran", "form": "free", "output": Path(name).stem + ".o"})
        elif name.endswith(".c"):
            build.append({"id": Path(name).stem, "source": name, "language": "c", "output": Path(name).stem + ".o"})
        else:
            raise ValueError(name)
    return {
        "schema_version": 1,
        "id": case_id,
        "rule": data["rule"],
        "facets": data["facets"],
        "evidence": data["evidence"],
        "standard": "f2023",
        "oracle_basis": "standard",
        "files": files,
        "build": build,
        "link": {"driver": "fortran", "objects": [step["output"] for step in build], "output": "program"},
        "expect": {"phase": "run", "outcome": "success", "exit_code": 0, "stdout": completion(variant), "stderr": ""},
    }


def build_corpus():
    specs = source_specs()
    files = {}
    for variant, case in CASES.items():
        cid = case["id"]
        folder = ROOT / FIXTURE_ROOT / cid
        for name, text in case_files_with_headers(case).items():
            files[folder / name] = text.encode("ascii")
        files[folder / "fixture.json"] = (json.dumps(manifest(cid, variant, case), indent=2) + "\n").encode("ascii")
    return files, specs


def catalogue_path_for_rule(rule):
    if rule.startswith("S19.5.1.3-"):
        return CATALOGUES["19.5.1.3"]
    if rule.startswith("S19.5.1.4-"):
        return CATALOGUES["19.5.1.4"]
    if rule.startswith("S19.5.1.5-"):
        return CATALOGUES["19.5.1.5"]
    if rule.startswith("S19.5.1.6-"):
        return CATALOGUES["19.5.1.6"]
    raise KeyError(rule)


def synced_catalogue(path, catalogue):
    result = copy.deepcopy(catalogue)
    for req in result["requirements"]:
        rule = req["id"]
        if rule in FACETS_BY_RULE:
            for facet in FACETS_BY_RULE[rule]:
                req.get("pending", {}).pop(facet, None)
            req["oracle"] = ORACLES[rule]
            req["oracle_limitation"] = LIMITATIONS[rule]
    return result


def synced_catalogues(root=ROOT):
    out = {}
    for rel in sorted(set(CATALOGUES.values())):
        path = root / rel
        out[path] = synced_catalogue(rel, json.loads(path.read_text()))
    return out


def generate(root=ROOT, check=False):
    files, specs = build_corpus()
    outputs = {path: raw for path, raw in files.items()}
    for path, data in synced_catalogues(root).items():
        outputs[path] = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    if check:
        stale = [path for path, raw in outputs.items() if not path.exists() or path.read_bytes() != raw]
        if stale:
            raise SystemExit("generated files are stale: " + ", ".join(str(p.relative_to(root)) for p in stale))
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


def mutated_files(spec, mutation):
    files = copy.deepcopy(spec["files"])
    target = mutation.get("file", "source.f90")
    text = files[target]
    changed = text
    for old, new in mutation["replacements"]:
        if changed.count(old) != 1:
            raise ValueError(f"{spec['variant']}:{mutation['id']} replacement is not load-bearing: {old!r}")
        changed = changed.replace(old, new, 1)
    if changed == text:
        raise ValueError(f"{spec['variant']}:{mutation['id']} did not change source")
    files[target] = changed
    return files


def std_flag(compiler, std):
    name = Path(compiler).name.lower()
    return f"--std={std}" if "lfortran" in name else f"-std={std}"


def run_command(argv, cwd, timeout=60):
    env = os.environ.copy()
    env["TMPDIR"] = str((ROOT / ".association_19_5_1_tmp").resolve())
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)


def compile_and_run(files, compiler, std, cc, workdir):
    objects = []
    for name, text in files.items():
        (workdir / name).write_text(text)
    for name in files:
        stem = Path(name).stem
        obj = stem + ".o"
        if name.endswith(".f90"):
            cmd = [compiler, std_flag(compiler, std), "-c", name, "-o", obj]
        elif name.endswith(".c"):
            cmd = [cc, "-c", name, "-o", obj]
        else:
            continue
        comp = run_command(cmd, workdir)
        if comp.returncode != 0:
            return {"phase": "compile", "returncode": comp.returncode, "stdout": comp.stdout, "stderr": comp.stderr, "command": " ".join(cmd)}
        objects.append(obj)
    link = run_command([compiler, *objects, "-o", "program"], workdir)
    if link.returncode != 0:
        return {"phase": "link", "returncode": link.returncode, "stdout": link.stdout, "stderr": link.stderr}
    run = run_command([str(workdir / "program")], workdir)
    return {"phase": "run", "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}


def mutation_matrix(compiler, std="f2023", cc="cc", root=ROOT, keep=False):
    _, specs = build_corpus()
    scratch_root = root / ".association_19_5_1_mutation_work"
    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    scratch_root.mkdir()
    results = []
    try:
        for cid, spec in specs.items():
            parent_dir = scratch_root / cid / "parent"
            parent_dir.mkdir(parents=True)
            parent = compile_and_run(spec["files"], compiler, std, cc, parent_dir)
            parent_ok = (parent["phase"] == "run" and parent["returncode"] == 0
                         and parent["stdout"] == spec["completion"] and parent["stderr"] == "")
            results.append({"case": cid, "mutation": "parent", "ok": parent_ok, **parent})
            if not parent_ok:
                continue
            for mutation in spec["mutations"]:
                mdir = scratch_root / cid / mutation["id"]
                mdir.mkdir(parents=True)
                observed = compile_and_run(mutated_files(spec, mutation), compiler, std, cc, mdir)
                failed_as_required = (observed["phase"] == "run" and not (
                    observed["returncode"] == 0 and observed["stdout"] == spec["completion"] and observed["stderr"] == ""))
                results.append({"case": cid, "mutation": mutation["id"], "kind": mutation["kind"],
                                "ok": failed_as_required, **observed})
    finally:
        if not keep:
            shutil.rmtree(scratch_root, ignore_errors=True)
            shutil.rmtree(root / ".association_19_5_1_tmp", ignore_errors=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--cc", default="cc")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--passing-parents-only", action="store_true")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            raise SystemExit("--mutation-check requires --compiler")
        results = mutation_matrix(args.compiler, args.std, args.cc, keep=args.keep_work)
        total = sum(1 for row in results if row["mutation"] != "parent")
        parents = sum(1 for row in results if row["mutation"] == "parent" and row["ok"])
        if args.passing_parents_only:
            failed = [row for row in results if row["mutation"] != "parent" and not row["ok"]]
            skipped = [row for row in results if row["mutation"] == "parent" and not row["ok"]]
        else:
            failed = [row for row in results if not row["ok"]]
            skipped = []
        if failed:
            for row in failed:
                print(json.dumps({k: row[k] for k in ("case", "mutation", "phase", "returncode", "stdout", "stderr", "command") if k in row}, indent=2))
            raise SystemExit(f"mutation matrix failed: {len(failed)} bad rows out of {len(results)}")
        suffix = f"; {len(skipped)} parents skipped" if skipped else ""
        print(f"mutation matrix OK: {parents} parents passed; {total} mutants failed on {Path(args.compiler).name} {args.std}{suffix}")
        return
    generate(ROOT, check=args.check)
    print(f"generated {len(CASES)} {TOPIC} fixtures")


if __name__ == "__main__":
    main()
