#!/usr/bin/env python3
"""Runtime fixtures for ISO_C_BINDING 18.1 and 18.2 named entities."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "iso_c_binding_18_1_18_2"
FIXTURE_ROOT = Path("tests/fixtures") / TOPIC
SUMMARY = "ISO_C_BINDING 18.1/18.2"

CATALOGUES = {
    "18.1": "doc/catalogues/interoperability_overview_18_1.json",
    "18.2.1": "doc/catalogues/iso_c_binding_accessibility_18_2_1.json",
    "18.2.2": "doc/catalogues/iso_c_binding_named_constants_derived_types_18_2_2.json",
    "18.2.3.1": "doc/catalogues/iso_c_binding_procedures_general_18_2_3_1.json",
    "18.2.3.2": "doc/catalogues/c_associated_18_2_3_2.json",
}

ORACLE_PREFIX = {
    "S18.1-001": "S18.1-001 C procedure reference fixture: ",
    "S18.1-002": "S18.1-002 C-to-Fortran reference fixture: ",
    "S18.1-003": "S18.1-003 C external global association fixture: ",
    "S18.1-004": "S18.1-004 C-type correspondence fixture: ",
    "S18.1-006": "S18.1-006 interoperable equivalent/no-partner fixture: ",
    "S18.2.1-001": "S18.2.1-001 required ISO_C_BINDING entities fixture: ",
    "S18.2.2-001": "S18.2.2-001 Table 18.2 default-integer constants fixture: ",
    "S18.2.2-002": "S18.2.2-002 C representation round-trip fixture: ",
    "S18.2.2-003": "S18.2.2-003 C_INT valid-kind fixture: ",
    "S18.2.2-004": "S18.2.2-004 optional integer valid-kind branch fixture: ",
    "S18.2.2-006": "S18.2.2-006 real valid-kind branch fixture: ",
    "S18.2.2-007": "S18.2.2-007 complex/real kind equality fixture: ",
    "S18.2.2-009": "S18.2.2-009 C_BOOL valid-kind fixture: ",
    "S18.2.2-011": "S18.2.2-011 C_CHAR valid-kind fixture: ",
    "S18.2.2-013": "S18.2.2-013 C special-character constants fixture: ",
    "S18.2.2-014": "S18.2.2-014 null pointer constants fixture: ",
    "S18.2.3.1-001": "S18.2.3.1-001 generic C_ASSOCIATED fixture: ",
    "S18.2.3.2-001": "S18.2.3.2-001 C_ASSOCIATED query fixture: ",
    "S18.2.3.2-003": "S18.2.3.2-003 C_ASSOCIATED argument positive-control fixture: ",
    "S18.2.3.2-004": "S18.2.3.2-004 C_ASSOCIATED result characteristics fixture: ",
    "S18.2.3.2-005": "S18.2.3.2-005 C_ASSOCIATED absent-argument values fixture: ",
    "S18.2.3.2-006": "S18.2.3.2-006 C_ASSOCIATED present-argument values fixture: ",
}
LIMIT_PREFIX = {rule: prefix.replace(" fixture: ", " boundaries: ") for rule, prefix in ORACLE_PREFIX.items()}

ORACLES = {
    "S18.1-001": ORACLE_PREFIX["S18.1-001"] + (
        "a C function add_one is referenced from Fortran through an interoperable BIND(C) interface and "
        "returns 42 from exact integer(C_INT) input 41. A separate Fortran BIND(C) function, whose interface "
        "is describable by a C prototype but is not C-defined, is referenced from Fortran and returns 36 from "
        "12. Feature mutants redirect each call to a different conforming exact computation."),
    "S18.1-002": ORACLE_PREFIX["S18.1-002"] + (
        "a C bridge calls the Fortran subroutine mark_from_c exported with BIND(C); the Fortran program first "
        "sets a nondefault sentinel and then observes exact value 31 after the C call. The mutation skips the C "
        "callback while preserving a conforming C/Fortran link."),
    "S18.1-003": ORACLE_PREFIX["S18.1-003"] + (
        "a module integer(C_INT), BIND(C,name='batch310_shared_counter') is initialized to -5 and modified by "
        "a C companion through extern int batch310_shared_counter; Fortran then observes exact 123. The mutation "
        "writes a different value through the same C external linkage."),
    "S18.1-004": ORACLE_PREFIX["S18.1-004"] + (
        "integer(C_INT) and a BIND(C) derived type with integer(C_INT) components are exchanged with C. The C "
        "companion sees exact integer values and returns exact checksums for the scalar kind constant and the C "
        "struct-shaped derived value. Enumeration correspondence remains pending."),
    "S18.1-006": ORACLE_PREFIX["S18.1-006"] + (
        "C mutates the address of a TARGET integer(C_INT) obtained by C_LOC, showing an equivalent C entity can "
        "interoperate, while a distinct BIND(C) Fortran function and BIND(C) variable with no C companion are "
        "used only from Fortran and retain exact values."),
    "S18.2.1-001": ORACLE_PREFIX["S18.2.1-001"] + (
        "the fixture imports ISO_C_BINDING by intrinsic USE, imports all required null, Table 18.1 character, "
        "Table 18.2 kind constants and C_PTR/C_FUNPTR by ONLY, and observes exact null association, constant "
        "assignment, character length/value, and scalar pointer declarations. The C_F_STRPOINTER/F_C_STRING "
        "procedure-access facet remains pending because the f2023 reference on this host does not provide them."),
    "S18.2.2-001": ORACLE_PREFIX["S18.2.2-001"] + (
        "direct KIND inquiries on every Table 18.2 constant expression are compared with KIND(0), proving they "
        "are default integer named constants without asserting their processor-dependent values."),
    "S18.2.2-002": ORACLE_PREFIX["S18.2.2-002"] + (
        "integer(C_INT), real(C_FLOAT), real(C_DOUBLE), real(C_LONG_DOUBLE), logical(C_BOOL), and "
        "character(C_CHAR) values are passed by value to C functions of the corresponding C types and exact "
        "representable nondefault results are returned. The _Bool branch observes C true/false as 1/0. The "
        "fixture requires the c-long-double-positive processor profile before declaring real(C_LONG_DOUBLE)."),
    "S18.2.2-003": ORACLE_PREFIX["S18.2.2-003"] + (
        "direct KIND(0_C_INT) equals C_INT and an integer(C_INT) sentinel assignment changes from -7_C_INT to "
        "19_C_INT, proving C_INT is accepted as an integer kind parameter."),
    "S18.2.2-004": ORACLE_PREFIX["S18.2.2-004"] + (
        "the host valid branch is exercised for optional C integer kind constants by declaring integer(k) values "
        "for C_SHORT, C_LONG, C_LONG_LONG, C_SIZE_T and stdint-family constants that are positive on both target "
        "toolchains. Negative sentinel branches are not observed on this host and remain pending."),
    "S18.2.2-006": ORACLE_PREFIX["S18.2.2-006"] + (
        "C_FLOAT, C_DOUBLE, and C_LONG_DOUBLE are positive on both target toolchains; real(k) values 1.5 are "
        "passed through C float, double, and long double functions and return exactly 2.5 with direct KIND "
        "inquiries. The fixture requires the c-long-double-positive processor profile; negative real sentinel "
        "branches remain pending."),
    "S18.2.2-007": ORACLE_PREFIX["S18.2.2-007"] + (
        "three independent logical assertions compare C_FLOAT_COMPLEX with C_FLOAT, C_DOUBLE_COMPLEX with "
        "C_DOUBLE, and C_LONG_DOUBLE_COMPLEX with C_LONG_DOUBLE. The fixture requires the c-long-double-positive "
        "processor profile before asserting the long-double pair on processors where C_LONG_DOUBLE is a valid kind."),
    "S18.2.2-009": ORACLE_PREFIX["S18.2.2-009"] + (
        "C_BOOL is positive on both target toolchains; logical(C_BOOL) true and false are passed to a C _Bool "
        "checker and exact 1/0 observations plus KIND(.TRUE._C_BOOL)==C_BOOL are asserted."),
    "S18.2.2-011": ORACLE_PREFIX["S18.2.2-011"] + (
        "C_CHAR is nonnegative on both target toolchains; character(kind=C_CHAR,len=1) values including "
        "C_NULL_CHAR and C_NEW_LINE are passed to a C char checker, and KIND(C_NULL_CHAR)==C_CHAR is inquired "
        "directly on the constant expression."),
    "S18.2.2-013": ORACLE_PREFIX["S18.2.2-013"] + (
        "all eight Table 18.1 character constants are imported and observed as length one; the positive C_CHAR "
        "branch checks KIND(C_NULL_CHAR)==C_CHAR and a C companion compares the values with C escapes \\0, "
        "\\a, \\b, \\f, \\n, \\r, \\t, and \\v."),
    "S18.2.2-014": ORACLE_PREFIX["S18.2.2-014"] + (
        "C_NULL_PTR and C_NULL_FUNPTR are assigned to scalar C_PTR/C_FUNPTR variables that previously held "
        "nonnull C_LOC/C_FUNLOC values, and C_ASSOCIATED then returns .false. for each null value."),
    "S18.2.3.1-001": ORACLE_PREFIX["S18.2.3.1-001"] + (
        "the generic name C_ASSOCIATED is imported once and resolves for both TYPE(C_PTR) and TYPE(C_FUNPTR) "
        "null arguments, with exact .false. results for both calls."),
    "S18.2.3.2-001": ORACLE_PREFIX["S18.2.3.2-001"] + (
        "C_ASSOCIATED is used as the operation that distinguishes null, nonnull, equal and unequal C pointer "
        "statuses through exact logical results; feature mutants replace the queried pointer status."),
    "S18.2.3.2-003": ORACLE_PREFIX["S18.2.3.2-003"] + (
        "positive-control calls use scalar TYPE(C_PTR) and scalar TYPE(C_FUNPTR) first arguments, and two "
        "same-type TYPE(C_PTR) arguments; no unnumbered restriction is used as a diagnostic oracle."),
    "S18.2.3.2-004": ORACLE_PREFIX["S18.2.3.2-004"] + (
        "direct inquiries KIND(C_ASSOCIATED(C_NULL_PTR)) and RANK(C_ASSOCIATED(C_NULL_PTR)) prove default "
        "logical scalar result characteristics without inquiring an assigned variable."),
    "S18.2.3.2-005": ORACLE_PREFIX["S18.2.3.2-005"] + (
        "with the optional second argument absent, C_ASSOCIATED(C_NULL_PTR) is .false. from a .true. sentinel, "
        "and C_ASSOCIATED(C_LOC(target)) is .true. from a .false. sentinel."),
    "S18.2.3.2-006": ORACLE_PREFIX["S18.2.3.2-006"] + (
        "with the optional second argument present, a null first C pointer is .false., two C_LOC values for the "
        "same target are .true., and C_LOC values for distinct targets are .false. No pointer bit pattern is "
        "observed."),
}

LIMITATION_COMMON = (
    "Only the listed exact single-image integer, logical and character effects are claimed. Processor-dependent "
    "numeric kind values, pointer bit patterns, storage alignment, warning text, extra ISO_C_BINDING public "
    "entities, C_F_STRPOINTER/F_C_STRING availability on a reference that lacks them, ISO_Fortran_binding.h "
    "descriptor semantics, interoperable enumeration transfer, negative optional-kind sentinel branches not "
    "manifest on this host, C_LONG_DOUBLE declarations when the c-long-double-positive profile exits 77, and "
    "later 18.2.3 procedures remain pending or belong to sibling catalogues. Every "
    "owned facet has a distinct assertion and conforming feature mutation in this generator."
)
LIMITATIONS = {rule: LIMIT_PREFIX[rule] + LIMITATION_COMMON for rule in ORACLE_PREFIX}

CASES = {}

def sha(raw):
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def header(rule, facets, evidence="effect"):
    covers = "! covers: " + " ".join(facets) + "\n"
    if len(covers.rstrip()) > 132:
        covers = "! covers:\n" + "".join(f"!   {facet}\n" for facet in facets)
    return (f"! rule: {rule}\n" + covers + f"! evidence: {evidence}\n"
            "! standard: f2023\n! oracle-basis: standard\n")

def identifier(rule, variant):
    return rule.replace('.', '_').replace('-', '_') + "_valid__" + TOPIC + "_" + variant

def add_case(variant, rule, facets, files, mutations, evidence="effect", profiles=()):
    cid = identifier(rule, variant)
    CASES[variant] = dict(id=cid, variant=variant, rule=rule, facets=facets,
                          evidence=evidence, profiles=list(profiles), files=files, mutations=mutations)

def fexpect():
    return r'''
contains
  subroutine expect_int(actual, expected, label)
    integer(c_int), intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_logical(actual, expected, label)
    logical, intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual .neqv. expected) then
      write(*,'(a,1x,a,1x,l1,1x,l1)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
'''

def expect_body():
    text = fexpect()
    return text.split("contains\n", 1)[1].rsplit("end program\n", 1)[0]

# S18.1-001
add_case("c_procedure_reference", "S18.1-001",
    ["reference-c-defined-procedure", "reference-c-prototype-described-procedure"],
    {
"source.f90": header("S18.1-001", ["reference-c-defined-procedure", "reference-c-prototype-described-procedure"]) + r'''program iso_c_binding_c_procedure_reference
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  interface
    integer(c_int) function c_add_one(value) bind(c, name="batch310_add_one")
      import c_int
      integer(c_int), value :: value
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(c_add_one(41_c_int), 42_c_int, 'C defined function result')
  call expect_int(proto_times_three(12_c_int), 36_c_int, 'C prototype described Fortran function')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 C PROCEDURE REFERENCE OK'
contains
  integer(c_int) function proto_times_three(value) bind(c)
    integer(c_int), value :: value
    proto_times_three = value * 3_c_int
  end function
''' + expect_body() + "end program\n",
"bridge.c": "int batch310_add_one(int value) { return value + 1; }\n",
    }, [
        dict(id="c-defined-add-one-changed", facets=["reference-c-defined-procedure"],
             replacements=[("return value + 1;", "return value + 2;")]),
        dict(id="prototype-fortran-body-changed", facets=["reference-c-prototype-described-procedure"],
             replacements=[("proto_times_three = value * 3_c_int", "proto_times_three = value * 4_c_int")]),
    ])

# S18.1-002
add_case("fortran_called_from_c", "S18.1-002", ["fortran-subprogram-referenceable-from-c"],
    {
"source.f90": header("S18.1-002", ["fortran-subprogram-referenceable-from-c"]) + r'''module iso_c_binding_callback_state
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: marker = -9_c_int
contains
  subroutine mark_from_c() bind(c, name="batch310_mark_from_c")
    marker = 31_c_int
  end subroutine
end module
program iso_c_binding_fortran_called_from_c
  use, intrinsic :: iso_c_binding, only: c_int
  use iso_c_binding_callback_state, only: marker
  implicit none
  interface
    subroutine c_call_fortran_marker() bind(c, name="batch310_call_fortran_marker")
    end subroutine
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  marker = -9_c_int
  call c_call_fortran_marker()
  call expect_int(marker, 31_c_int, 'Fortran subroutine called from C')
  call expect_int(checks, 1_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 FORTRAN CALLED FROM C OK'
''' + fexpect(),
"bridge.c": "extern void batch310_mark_from_c(void);\nvoid batch310_call_fortran_marker(void) { batch310_mark_from_c(); }\n",
    }, [dict(id="c-callback-skipped", facets=["fortran-subprogram-referenceable-from-c"],
             replacements=[("batch310_mark_from_c();", "/* conforming mutation: do not call back */")])])

# S18.1-003
add_case("c_external_global", "S18.1-003", ["fortran-global-variable-associated-with-c-external"],
    {
"source.f90": header("S18.1-003", ["fortran-global-variable-associated-with-c-external"]) + r'''module iso_c_binding_external_global_m
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c, name="batch310_shared_counter") :: shared_counter = -5_c_int
end module
program iso_c_binding_c_external_global
  use, intrinsic :: iso_c_binding, only: c_int
  use iso_c_binding_external_global_m, only: shared_counter
  implicit none
  interface
    subroutine c_store_shared_counter() bind(c, name="batch310_store_shared_counter")
    end subroutine
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  shared_counter = -5_c_int
  call c_store_shared_counter()
  call expect_int(shared_counter, 123_c_int, 'C external linkage variable')
  call expect_int(checks, 1_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 C EXTERNAL GLOBAL OK'
''' + fexpect(),
"bridge.c": "extern int batch310_shared_counter;\nvoid batch310_store_shared_counter(void) { batch310_shared_counter = 123; }\n",
    }, [dict(id="c-external-writes-different-value", facets=["fortran-global-variable-associated-with-c-external"],
             replacements=[("shared_counter = 123;", "shared_counter = 124;")])])

# S18.1-004
add_case("c_type_correspondence", "S18.1-004", ["iso-c-binding-kind-constants", "derived-types-correspond-to-c-types"],
    {
"source.f90": header("S18.1-004", ["iso-c-binding-kind-constants", "derived-types-correspond-to-c-types"]) + r'''program iso_c_binding_c_type_correspondence
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  type, bind(c) :: pair
    integer(c_int) :: left
    integer(c_int) :: right
  end type
  interface
    integer(c_int) function c_int_identity(value) bind(c, name="batch310_int_identity")
      import c_int
      integer(c_int), value :: value
    end function
    integer(c_int) function c_pair_sum(value) bind(c, name="batch310_pair_sum")
      import c_int, pair
      type(pair), value :: value
    end function
  end interface
  type(pair) :: item
  integer(c_int) :: checks
  checks = 0_c_int
  item%left = 17_c_int
  item%right = 25_c_int
  call expect_int(c_int_identity(55_c_int), 55_c_int, 'C_INT corresponding C int')
  call expect_int(c_pair_sum(item), 42_c_int, 'BIND(C) derived type corresponding struct')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 C TYPE CORRESPONDENCE OK'
''' + fexpect(),
"bridge.c": "struct pair { int left; int right; };\nint batch310_int_identity(int value) { return value; }\nint batch310_pair_sum(struct pair value) { return value.left + value.right; }\n",
    }, [
        dict(id="c-int-correspondence-offset", facets=["iso-c-binding-kind-constants"],
             replacements=[("return value;", "return value + 1;")]),
        dict(id="c-struct-uses-one-component", facets=["derived-types-correspond-to-c-types"],
             replacements=[("return value.left + value.right;", "return value.left + value.right + 1;")]),
    ])

# S18.1-006
add_case("equivalent_and_no_partner", "S18.1-006", ["interoperable-entity-equivalent-c-entity", "no-actual-c-entity-required"],
    {
"source.f90": header("S18.1-006", ["interoperable-entity-equivalent-c-entity", "no-actual-c-entity-required"]) + r'''module iso_c_binding_no_partner_m
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c, name="batch310_no_partner_variable") :: no_partner_variable = -2_c_int
contains
  integer(c_int) function no_partner_function(value) bind(c, name="batch310_no_partner_function")
    integer(c_int), value :: value
    no_partner_function = value + no_partner_variable
  end function
end module
program iso_c_binding_equivalent_and_no_partner
  use, intrinsic :: iso_c_binding, only: c_int, c_loc
  use iso_c_binding_no_partner_m, only: no_partner_variable, no_partner_function
  implicit none
  interface
    subroutine c_mutate_address(ptr) bind(c, name="batch310_mutate_address")
      import c_int
      integer(c_int), intent(inout) :: ptr
    end subroutine
  end interface
  integer(c_int), target :: target_value
  integer(c_int) :: checks
  checks = 0_c_int
  target_value = -8_c_int
  no_partner_variable = -2_c_int
  call c_mutate_address(target_value)
  call expect_int(target_value, 64_c_int, 'equivalent C entity through C_LOC-compatible address')
  call expect_int(no_partner_function(19_c_int), 17_c_int, 'BIND(C) entity without actual C partner')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 EQUIVALENT AND NO PARTNER OK'
''' + fexpect(),
"bridge.c": "void batch310_mutate_address(int *ptr) { *ptr = 64; }\n",
    }, [
        dict(id="c-equivalent-mutates-different-value", facets=["interoperable-entity-equivalent-c-entity"],
             replacements=[("*ptr = 64;", "*ptr = 65;")]),
        dict(id="no-partner-fortran-function-offset", facets=["no-actual-c-entity-required"],
             replacements=[("no_partner_function = value + no_partner_variable", "no_partner_function = value + no_partner_variable + 1_c_int")]),
    ])

# S18.2.1-001
KIND_NAMES = ["c_signed_char", "c_short", "c_int", "c_long", "c_long_long", "c_size_t",
    "c_int8_t", "c_int16_t", "c_int32_t", "c_int64_t", "c_int_least8_t", "c_int_least16_t",
    "c_int_least32_t", "c_int_least64_t", "c_int_fast8_t", "c_int_fast16_t", "c_int_fast32_t",
    "c_int_fast64_t", "c_intmax_t", "c_intptr_t", "c_ptrdiff_t", "c_float", "c_double",
    "c_long_double", "c_float_complex", "c_double_complex", "c_long_double_complex", "c_bool", "c_char"]
CHAR_NAMES = ["c_null_char", "c_alert", "c_backspace", "c_form_feed", "c_new_line",
              "c_carriage_return", "c_horizontal_tab", "c_vertical_tab"]
only_access = ", ".join(["c_ptr", "c_funptr", "c_null_ptr", "c_null_funptr", "c_associated"] + KIND_NAMES + CHAR_NAMES)
kind_sum = " + ".join(KIND_NAMES)
char_len_sum = " + ".join(f"len({name})" for name in CHAR_NAMES)
access_source = header("S18.2.1-001", ["iso-c-binding-module-provided", "required-null-constants-accessible", "required-kind-and-character-constants-accessible", "c-pointer-types-accessible"]) + f'''program iso_c_binding_required_entities_access
  use, intrinsic :: iso_c_binding, only: {only_access}
  implicit none
  type(c_ptr) :: p
  type(c_funptr) :: fp
  integer :: module_probe, kind_total, char_total
  integer(c_int) :: checks
  checks = 0_c_int
  p = c_null_ptr
  fp = c_null_funptr
  module_probe = -777
  kind_total = -999
  char_total = -888
  module_probe = c_int
  kind_total = {kind_sum}
  char_total = {char_len_sum}
  call expect_logical(module_probe /= -777, .true., 'intrinsic ISO_C_BINDING module provided')
  call expect_logical(c_associated(p), .false., 'C_NULL_PTR accessible')
  call expect_logical(c_associated(fp), .false., 'C_NULL_FUNPTR accessible')
  call expect_logical(kind_total /= -999, .true., 'Table 18.2 constants accessible')
  call expect_int(int(char_total, c_int), 8_c_int, 'Table 18.1 constants accessible')
  call expect_int(checks, 5_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.1 REQUIRED ENTITIES ACCESS OK'
''' + fexpect()
add_case("required_entities_access", "S18.2.1-001",
    ["iso-c-binding-module-provided", "required-null-constants-accessible", "required-kind-and-character-constants-accessible", "c-pointer-types-accessible"],
    {"source.f90": access_source}, [
        dict(id="module-use-sentinel-not-updated", facets=["iso-c-binding-module-provided"],
             replacements=[("module_probe = c_int", "module_probe = -777")]),
        dict(id="null-ptr-replaced-with-nonnull", facets=["required-null-constants-accessible"],
             replacements=[("p = c_null_ptr", "p = c_loc_target()")]),
        dict(id="kind-constants-assignment-omitted", facets=["required-kind-and-character-constants-accessible"],
             replacements=[("kind_total = " + kind_sum, "kind_total = -999")]),
        dict(id="pointer-type-second-null-check-changed", facets=["c-pointer-types-accessible"],
             replacements=[("fp = c_null_funptr", "fp = c_funloc_target()")]),
    ])
# add helper functions for mutation only by replacing names with internal calls; keep parent free of C_LOC/C_FUNLOC imports not possible
access_source = access_source.replace("end program\n", r'''
  function c_loc_target() result(r)
    use, intrinsic :: iso_c_binding, only: c_loc, c_ptr
    type(c_ptr) :: r
    integer(c_int), target, save :: x = 1_c_int
    r = c_loc(x)
  end function
  function c_funloc_target() result(r)
    use, intrinsic :: iso_c_binding, only: c_funloc, c_funptr
    type(c_funptr) :: r
    r = c_funloc(local_target)
  end function
  integer(c_int) function local_target() bind(c)
    local_target = 1_c_int
  end function
end program
''')
CASES["required_entities_access"]["files"]["source.f90"] = access_source

# S18.2.2-001
kind_checks = "\n".join(f"  call expect_int(kind({name}), default_kind, '{name} default integer kind')" for name in KIND_NAMES)
defint_source = header("S18.2.2-001", ["table-18-2-default-integer-named-constants"]) + f'''program iso_c_binding_default_integer_constants
  use, intrinsic :: iso_c_binding, only: c_int, {", ".join(KIND_NAMES)}
  implicit none
  integer, parameter :: default_kind = kind(0)
  integer(c_int) :: checks
  checks = 0_c_int
{kind_checks}
  call expect_int(checks, 29_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 DEFAULT INTEGER CONSTANTS OK'
''' + fexpect()
add_case("default_integer_constants", "S18.2.2-001", ["table-18-2-default-integer-named-constants"],
         {"source.f90": defint_source},
         [dict(id="default-kind-direct-inquiry-substituted", facets=["table-18-2-default-integer-named-constants"],
               replacements=[("kind(c_int)", "selected_int_kind(18)")])])

# S18.2.2 representation and valid branches
rep_source = header("S18.2.2-002", ["c-compatible-kind-representation", "c-bool-true-false-representation"]) + r'''program iso_c_binding_representation_roundtrip
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_long_double, c_bool, c_char
  implicit none
  interface
    integer(c_int) function c_int_roundtrip(value) bind(c, name="batch310_int_roundtrip")
      import c_int
      integer(c_int), value :: value
    end function
    real(c_float) function c_float_add_one(value) bind(c, name="batch310_float_add_one")
      import c_float
      real(c_float), value :: value
    end function
    real(c_double) function c_double_add_one(value) bind(c, name="batch310_double_add_one")
      import c_double
      real(c_double), value :: value
    end function
    real(c_long_double) function c_long_double_add_one(value) bind(c, name="batch310_long_double_add_one")
      import c_long_double
      real(c_long_double), value :: value
    end function
    integer(c_int) function c_bool_codes(t, f) bind(c, name="batch310_bool_codes")
      import c_int, c_bool
      logical(c_bool), value :: t, f
    end function
    integer(c_int) function c_char_code(ch) bind(c, name="batch310_char_code")
      import c_int, c_char
      character(kind=c_char), value :: ch
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(c_int_roundtrip(-3_c_int), -3_c_int, 'integer(C_INT) C representation negative')
  call expect_int(c_int_roundtrip(42_c_int), 42_c_int, 'integer(C_INT) C representation positive')
  call expect_logical(c_float_add_one(1.5_c_float) == 2.5_c_float, .true., 'C_FLOAT exact roundtrip')
  call expect_logical(c_double_add_one(1.5_c_double) == 2.5_c_double, .true., 'C_DOUBLE exact roundtrip')
  call expect_logical(c_long_double_add_one(1.5_c_long_double) == 2.5_c_long_double, .true., 'C_LONG_DOUBLE exact roundtrip')
  call expect_int(c_bool_codes(.true._c_bool, .false._c_bool), 10_c_int, 'C_BOOL true false C codes')
  call expect_int(c_char_code(c_char_'A'), 65_c_int, 'C_CHAR C char value')
  call expect_int(checks, 7_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 REPRESENTATION ROUNDTRIP OK'
''' + fexpect()
rep_c = r'''#include <stdbool.h>
int batch310_int_roundtrip(int value) { return value; }
float batch310_float_add_one(float value) { return value + 1.0f; }
double batch310_double_add_one(double value) { return value + 1.0; }
long double batch310_long_double_add_one(long double value) { return value + 1.0L; }
int batch310_bool_codes(_Bool t, _Bool f) { return (t == (_Bool)1 && f == (_Bool)0) ? 10 : -10; }
int batch310_char_code(char ch) { return ch == 'A' ? 65 : -65; }
'''
add_case("representation_roundtrip", "S18.2.2-002", ["c-compatible-kind-representation", "c-bool-true-false-representation"],
         {"source.f90": rep_source, "bridge.c": rep_c}, [
             dict(id="c-int-roundtrip-offset", facets=["c-compatible-kind-representation"],
                  replacements=[("return value;", "return value + 1;")]),
             dict(id="c-bool-codes-inverted", facets=["c-bool-true-false-representation"],
                  replacements=[("? 10 : -10", "? 11 : -10")]),
         ], profiles=["c-long-double-positive"])

add_case("c_int_valid_kind", "S18.2.2-003", ["c-int-valid-integer-kind"],
    {"source.f90": header("S18.2.2-003", ["c-int-valid-integer-kind"]) + r'''program iso_c_binding_c_int_valid_kind
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: value
  integer(c_int) :: checks
  checks = 0_c_int
  value = -7_c_int
  value = 19_c_int
  call expect_int(kind(0_c_int), c_int, 'direct C_INT kind inquiry')
  call expect_int(value, 19_c_int, 'integer(C_INT) assignment')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 C INT VALID KIND OK'
''' + fexpect()},
    [dict(id="c-int-assignment-feature-changed", facets=["c-int-valid-integer-kind"],
          replacements=[("value = 19_c_int", "value = 20_c_int")])])

optional_int_source = header("S18.2.2-004", ["optional-integer-kind-valid-branch"]) + r'''program iso_c_binding_optional_integer_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_short, c_long, c_long_long, c_size_t, c_int8_t, c_int16_t, c_int32_t, c_int64_t
  implicit none
  integer(c_short) :: s
  integer(c_long) :: l
  integer(c_long_long) :: ll
  integer(c_size_t) :: n
  integer(c_int8_t) :: i8
  integer(c_int16_t) :: i16
  integer(c_int32_t) :: i32
  integer(c_int64_t) :: i64
  integer(c_int) :: checks
  checks = 0_c_int
  s = 5_c_short; l = 6_c_long; ll = 7_c_long_long; n = 8_c_size_t
  i8 = 2_c_int8_t; i16 = 3_c_int16_t; i32 = 4_c_int32_t; i64 = 5_c_int64_t
  call expect_int(kind(s), c_short, 'C_SHORT valid integer kind')
  call expect_int(kind(l), c_long, 'C_LONG valid integer kind')
  call expect_int(kind(ll), c_long_long, 'C_LONG_LONG valid integer kind')
  call expect_int(kind(n), c_size_t, 'C_SIZE_T valid integer kind')
  call expect_int(kind(i8), c_int8_t, 'C_INT8_T valid integer kind')
  call expect_int(kind(i16), c_int16_t, 'C_INT16_T valid integer kind')
  call expect_int(kind(i32), c_int32_t, 'C_INT32_T valid integer kind')
  call expect_int(kind(i64), c_int64_t, 'C_INT64_T valid integer kind')
  call expect_int(checks, 8_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 OPTIONAL INTEGER VALID BRANCH OK'
''' + fexpect()
add_case("optional_integer_valid_branch", "S18.2.2-004", ["optional-integer-kind-valid-branch"],
         {"source.f90": optional_int_source},
         [dict(id="optional-integer-kind-inquiry-substituted", facets=["optional-integer-kind-valid-branch"],
               replacements=[("kind(i32)", "kind(i16)")])])

real_valid_source = header("S18.2.2-006", ["real-kind-valid-branch"]) + r'''program iso_c_binding_real_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_long_double
  implicit none
  interface
    real(c_float) function c_float_add_one(value) bind(c, name="batch310_float_add_one")
      import c_float
      real(c_float), value :: value
    end function
    real(c_double) function c_double_add_one(value) bind(c, name="batch310_double_add_one")
      import c_double
      real(c_double), value :: value
    end function
    real(c_long_double) function c_long_double_add_one(value) bind(c, name="batch310_long_double_add_one")
      import c_long_double
      real(c_long_double), value :: value
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(0.0_c_float), c_float, 'C_FLOAT direct kind inquiry')
  call expect_int(kind(0.0_c_double), c_double, 'C_DOUBLE direct kind inquiry')
  call expect_int(kind(0.0_c_long_double), c_long_double, 'C_LONG_DOUBLE direct kind inquiry')
  call expect_logical(c_float_add_one(1.5_c_float) == 2.5_c_float, .true., 'C_FLOAT exact C roundtrip')
  call expect_logical(c_double_add_one(1.5_c_double) == 2.5_c_double, .true., 'C_DOUBLE exact C roundtrip')
  call expect_logical(c_long_double_add_one(1.5_c_long_double) == 2.5_c_long_double, .true., 'C_LONG_DOUBLE exact C roundtrip')
  call expect_int(checks, 6_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 REAL VALID BRANCH OK'
''' + fexpect()
add_case("real_valid_branch", "S18.2.2-006", ["real-kind-valid-branch"],
         {"source.f90": real_valid_source, "bridge.c": "float batch310_float_add_one(float value) { return value + 1.0f; }\ndouble batch310_double_add_one(double value) { return value + 1.0; }\nlong double batch310_long_double_add_one(long double value) { return value + 1.0L; }\n"},
         [dict(id="real-c-roundtrip-offset", facets=["real-kind-valid-branch"],
               replacements=[("return value + 1.0;", "return value + 2.0;")])],
         profiles=["c-long-double-positive"])

complex_eq_source = header("S18.2.2-007", ["float-complex-kind-equals-float", "double-complex-kind-equals-double", "long-double-complex-kind-equals-long-double"]) + r'''program iso_c_binding_complex_kind_equalities
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_long_double, c_float_complex, c_double_complex, c_long_double_complex
  implicit none
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_logical(c_float_complex == c_float, .true., 'C_FLOAT_COMPLEX equals C_FLOAT')
  call expect_logical(c_double_complex == c_double, .true., 'C_DOUBLE_COMPLEX equals C_DOUBLE')
  call expect_logical(c_long_double_complex == c_long_double, .true., 'C_LONG_DOUBLE_COMPLEX equals C_LONG_DOUBLE')
  call expect_int(checks, 3_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 COMPLEX KIND EQUALITIES OK'
''' + fexpect()
add_case("complex_kind_equalities", "S18.2.2-007", ["float-complex-kind-equals-float", "double-complex-kind-equals-double", "long-double-complex-kind-equals-long-double"],
         {"source.f90": complex_eq_source}, [
             dict(id="float-complex-compared-to-double", facets=["float-complex-kind-equals-float"],
                  replacements=[("c_float_complex == c_float", "c_float_complex == c_double")]),
             dict(id="double-complex-compared-to-float", facets=["double-complex-kind-equals-double"],
                  replacements=[("c_double_complex == c_double", "c_double_complex == c_float")]),
             dict(id="long-double-complex-compared-to-double", facets=["long-double-complex-kind-equals-long-double"],
                  replacements=[("c_long_double_complex == c_long_double", "c_long_double_complex == c_float")]),
         ], profiles=["c-long-double-positive"])

add_case("c_bool_valid_branch", "S18.2.2-009", ["c-bool-valid-logical-kind-branch"],
    {"source.f90": header("S18.2.2-009", ["c-bool-valid-logical-kind-branch"]) + r'''program iso_c_binding_c_bool_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_bool
  implicit none
  interface
    integer(c_int) function c_bool_codes(t, f) bind(c, name="batch310_bool_codes")
      import c_int, c_bool
      logical(c_bool), value :: t, f
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(.true._c_bool), c_bool, 'C_BOOL direct kind inquiry')
  call expect_int(c_bool_codes(.true._c_bool, .false._c_bool), 10_c_int, 'C_BOOL C _Bool true false')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 C BOOL VALID BRANCH OK'
''' + fexpect(), "bridge.c": "#include <stdbool.h>\nint batch310_bool_codes(_Bool t, _Bool f) { return (t == (_Bool)1 && f == (_Bool)0) ? 10 : -10; }\n"},
    [dict(id="c-bool-c-code-changed", facets=["c-bool-valid-logical-kind-branch"],
          replacements=[("? 10 : -10", "? 11 : -10")])])

add_case("c_char_valid_branch", "S18.2.2-011", ["c-char-valid-character-kind-branch"],
    {"source.f90": header("S18.2.2-011", ["c-char-valid-character-kind-branch"]) + r'''program iso_c_binding_c_char_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_char, c_null_char, c_new_line
  implicit none
  interface
    integer(c_int) function c_two_chars(a, b) bind(c, name="batch310_two_chars")
      import c_int, c_char
      character(kind=c_char), value :: a, b
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(c_null_char), c_char, 'C_CHAR direct constant kind inquiry')
  call expect_int(c_two_chars(c_null_char, c_new_line), 10_c_int, 'C_CHAR C escape values')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 C CHAR VALID BRANCH OK'
''' + fexpect(), "bridge.c": "int batch310_two_chars(char a, char b) { return (a == '\\0' && b == '\\n') ? 10 : -10; }\n"},
    [dict(id="c-char-c-code-changed", facets=["c-char-valid-character-kind-branch"],
          replacements=[("? 10 : -10", "? 11 : -10")])])

special_source = header("S18.2.2-013", ["c-special-character-named-constants", "c-special-character-length-one", "c-special-character-kind-branch", "c-special-character-table-values"]) + r'''program iso_c_binding_special_character_constants
  use, intrinsic :: iso_c_binding, only: c_int, c_char, c_null_char, c_alert, c_backspace, c_form_feed, c_new_line, c_carriage_return, c_horizontal_tab, c_vertical_tab
  implicit none
  interface
    integer(c_int) function c_check_chars(nul, alert, back, form, newline, carriage, tab, vertical) bind(c, name="batch310_check_chars")
      import c_int, c_char
      character(kind=c_char), value :: nul, alert, back, form, newline, carriage, tab, vertical
    end function
  end interface
  character(kind=kind(c_null_char), len=1) :: holder
  integer(c_int) :: checks
  checks = 0_c_int
  holder = '#'
  holder = c_null_char
  call expect_logical(holder == c_null_char, .true., 'C_NULL_CHAR named constant assignment')
  call expect_int(len(c_null_char), 1_c_int, 'C_NULL_CHAR length one')
  call expect_int(len(c_alert), 1_c_int, 'C_ALERT length one')
  call expect_int(len(c_backspace), 1_c_int, 'C_BACKSPACE length one')
  call expect_int(len(c_form_feed), 1_c_int, 'C_FORM_FEED length one')
  call expect_int(len(c_new_line), 1_c_int, 'C_NEW_LINE length one')
  call expect_int(len(c_carriage_return), 1_c_int, 'C_CARRIAGE_RETURN length one')
  call expect_int(len(c_horizontal_tab), 1_c_int, 'C_HORIZONTAL_TAB length one')
  call expect_int(len(c_vertical_tab), 1_c_int, 'C_VERTICAL_TAB length one')
  call expect_int(kind(c_null_char), c_char, 'C special character kind branch')
  call expect_int(c_check_chars(c_null_char, c_alert, c_backspace, c_form_feed, c_new_line, c_carriage_return, c_horizontal_tab, c_vertical_tab), 8_c_int, 'C special character table values')
  call expect_int(checks, 11_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 SPECIAL CHARACTER CONSTANTS OK'
''' + fexpect()
special_c = r'''int batch310_check_chars(char nul, char alert, char back, char form, char newline, char carriage, char tab, char vertical) {
  return (nul == '\0' && alert == '\a' && back == '\b' && form == '\f' && newline == '\n' && carriage == '\r' && tab == '\t' && vertical == '\v') ? 8 : -8;
}
'''
add_case("special_character_constants", "S18.2.2-013", ["c-special-character-named-constants", "c-special-character-length-one", "c-special-character-kind-branch", "c-special-character-table-values"],
         {"source.f90": special_source, "bridge.c": special_c}, [
             dict(id="special-character-holder-not-assigned", facets=["c-special-character-named-constants"],
                  replacements=[("holder = c_null_char", "holder = '#'")]),
             dict(id="special-character-length-inquiry-substituted", facets=["c-special-character-length-one"],
                  replacements=[("len(c_vertical_tab)", "2")]),
             dict(id="special-character-kind-inquiry-substituted", facets=["c-special-character-kind-branch"],
                  replacements=[("kind(c_null_char), c_char", "kind(c_null_char), c_int")]),
             dict(id="special-character-c-value-changed", facets=["c-special-character-table-values"],
                  replacements=[("vertical == '\\v'", "vertical == '\\t'")]),
         ])

null_source = header("S18.2.2-014", ["c-null-ptr-type-and-value", "c-null-funptr-type-and-value"]) + r'''program iso_c_binding_null_pointer_constants
  use, intrinsic :: iso_c_binding, only: c_int, c_ptr, c_funptr, c_null_ptr, c_null_funptr, c_loc, c_funloc, c_associated
  implicit none
  integer(c_int), target :: target
  type(c_ptr) :: p
  type(c_funptr) :: fp
  integer(c_int) :: checks
  checks = 0_c_int
  target = 77_c_int
  p = c_loc(target)
  fp = c_funloc(local_function)
  p = c_null_ptr
  fp = c_null_funptr
  call expect_logical(c_associated(p), .false., 'C_NULL_PTR null value')
  call expect_logical(c_associated(fp), .false., 'C_NULL_FUNPTR null value')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 NULL POINTER CONSTANTS OK'
contains
  integer(c_int) function local_function() bind(c)
    local_function = 1_c_int
  end function
''' + fexpect().replace("contains\n", "")
add_case("null_pointer_constants", "S18.2.2-014", ["c-null-ptr-type-and-value", "c-null-funptr-type-and-value"],
         {"source.f90": null_source}, [
             dict(id="null-c-ptr-assignment-skipped", facets=["c-null-ptr-type-and-value"],
                  replacements=[("p = c_null_ptr", "! p remains associated by mutation")]),
             dict(id="null-c-funptr-assignment-skipped", facets=["c-null-funptr-type-and-value"],
                  replacements=[("fp = c_null_funptr", "! fp remains associated by mutation")]),
         ])

# S18.2.3.1-001 and C_ASSOCIATED
assoc_common_facets = ["c-associated-description", "c-associated-result-default-logical-scalar", "c-associated-absent-null-false", "c-associated-absent-nonnull-true", "c-associated-present-first-null-false", "c-associated-present-equal-true", "c-associated-present-unequal-false"]
assoc_source = header("S18.2.3.2-001", ["c-associated-description"]) + r'''program iso_c_binding_c_associated_values
  use, intrinsic :: iso_c_binding, only: c_int, c_ptr, c_null_ptr, c_loc, c_associated
  implicit none
  integer(c_int), target :: first, second
  type(c_ptr) :: p_first, p_first_again, p_second, p_null
  logical :: result
  integer(c_int) :: checks
  checks = 0_c_int
  first = 91_c_int
  second = 92_c_int
  p_first = c_loc(first)
  p_first_again = c_loc(first)
  p_second = c_loc(second)
  p_null = c_null_ptr
  result = .true.
  result = c_associated(p_null)
  call expect_logical(result, .false., 'absent second null false')
  result = .false.
  result = c_associated(p_first)
  call expect_logical(result, .true., 'absent second nonnull true')
  result = .true.
  result = c_associated(p_null, p_first)
  call expect_logical(result, .false., 'present second first null false')
  result = .false.
  result = c_associated(p_first, p_first_again)
  call expect_logical(result, .true., 'present second equal true')
  result = .true.
  result = c_associated(p_first, p_second)
  call expect_logical(result, .false., 'present second unequal false')
  call expect_int(checks, 5_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.3.2 C ASSOCIATED VALUES OK'
''' + fexpect()
add_case("c_associated_values", "S18.2.3.2-001", ["c-associated-description"],
         {"source.f90": assoc_source},
         [dict(id="query-description-null-replaced-with-nonnull", facets=["c-associated-description"],
               replacements=[("result = c_associated(p_null)\n  call expect_logical(result, .false., 'absent second null false')", "result = c_associated(p_first)\n  call expect_logical(result, .false., 'absent second null false')")])])
# Additional manifests use the same body? Avoid same program same mutants blocker. Create derived sources with distinct rule headers and mutated assertions.
add_case("c_associated_absent_values", "S18.2.3.2-005", ["c-associated-absent-null-false", "c-associated-absent-nonnull-true"],
         {"source.f90": assoc_source.replace("S18.2.3.2-001", "S18.2.3.2-005").replace("c-associated-description", "c-associated-absent-null-false c-associated-absent-nonnull-true")},
         [dict(id="absent-null-uses-nonnull", facets=["c-associated-absent-null-false"],
               replacements=[("result = c_associated(p_null)\n  call expect_logical(result, .false., 'absent second null false')", "result = c_associated(p_first)\n  call expect_logical(result, .false., 'absent second null false')")]),
          dict(id="absent-nonnull-uses-null", facets=["c-associated-absent-nonnull-true"],
               replacements=[("result = c_associated(p_first)\n  call expect_logical(result, .true., 'absent second nonnull true')", "result = c_associated(p_null)\n  call expect_logical(result, .true., 'absent second nonnull true')")])])
add_case("c_associated_present_values", "S18.2.3.2-006", ["c-associated-present-first-null-false", "c-associated-present-equal-true", "c-associated-present-unequal-false"],
         {"source.f90": assoc_source.replace("S18.2.3.2-001", "S18.2.3.2-006").replace("c-associated-description", "c-associated-present-first-null-false c-associated-present-equal-true c-associated-present-unequal-false")},
         [dict(id="present-first-null-uses-nonnull", facets=["c-associated-present-first-null-false"],
               replacements=[("result = c_associated(p_null, p_first)\n  call expect_logical(result, .false., 'present second first null false')", "result = c_associated(p_first, p_first)\n  call expect_logical(result, .false., 'present second first null false')")]),
          dict(id="present-equal-uses-unequal", facets=["c-associated-present-equal-true"],
               replacements=[("result = c_associated(p_first, p_first_again)\n  call expect_logical(result, .true., 'present second equal true')", "result = c_associated(p_first, p_second)\n  call expect_logical(result, .true., 'present second equal true')")]),
          dict(id="present-unequal-uses-equal", facets=["c-associated-present-unequal-false"],
               replacements=[("result = c_associated(p_first, p_second)\n  call expect_logical(result, .false., 'present second unequal false')", "result = c_associated(p_first, p_first_again)\n  call expect_logical(result, .false., 'present second unequal false')")])])

arg_control_source = header("S18.2.3.2-003", ["c-associated-first-argument-scalar-c-pointer", "c-associated-second-argument-same-type"], evidence="positive-control") + r'''program iso_c_binding_c_associated_argument_controls
  use, intrinsic :: iso_c_binding, only: c_int, c_ptr, c_funptr, c_null_ptr, c_null_funptr, c_loc, c_associated
  implicit none
  integer(c_int), target :: value
  type(c_ptr) :: p1, p2
  type(c_funptr) :: fp
  integer(c_int) :: checks
  checks = 0_c_int
  value = 77_c_int
  p1 = c_loc(value)
  p2 = c_null_ptr
  fp = c_null_funptr
  call expect_logical(c_associated(p1), .true., 'scalar C_PTR first argument')
  call expect_logical(c_associated(fp), .false., 'scalar C_FUNPTR first argument')
  call expect_logical(c_associated(p2, p1), .false., 'same TYPE(C_PTR) second argument')
  call expect_int(checks, 3_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.3.2 C ASSOCIATED ARGUMENT CONTROLS OK'
''' + fexpect()
add_case("c_associated_argument_controls", "S18.2.3.2-003", ["c-associated-first-argument-scalar-c-pointer", "c-associated-second-argument-same-type"],
         {"source.f90": arg_control_source}, [
             dict(id="scalar-c-ptr-first-argument-null", facets=["c-associated-first-argument-scalar-c-pointer"],
                  replacements=[("p1 = c_loc(value)", "p1 = c_null_ptr")]),
             dict(id="same-type-second-argument-nonnull", facets=["c-associated-second-argument-same-type"],
                  replacements=[("p2 = c_null_ptr", "p2 = c_loc(value)")]),
         ], evidence="positive-control")

generic_source = header("S18.2.3.1-001", ["iso-c-binding-procedure-names-generic"]) + r'''program iso_c_binding_c_associated_generic
  use, intrinsic :: iso_c_binding, only: c_int, c_null_ptr, c_null_funptr, c_funloc, c_associated
  implicit none
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_logical(c_associated(c_null_ptr), .false., 'C_ASSOCIATED generic resolves C_PTR')
  call expect_logical(c_associated(c_funloc(local_function)), .true., 'C_ASSOCIATED generic resolves C_FUNPTR')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.3.1 C ASSOCIATED GENERIC OK'
contains
  integer(c_int) function local_function() bind(c)
    local_function = 1_c_int
  end function
''' + expect_body() + "end program\n"
add_case("c_associated_generic", "S18.2.3.1-001", ["iso-c-binding-procedure-names-generic"],
         {"source.f90": generic_source}, [
             dict(id="generic-c-funptr-replaced-with-null", facets=["iso-c-binding-procedure-names-generic"],
                  replacements=[("c_associated(c_funloc(local_function)), .true.", "c_associated(c_null_funptr), .true.")])
         ])


def manifest_for(spec):
    files = list(spec["files"])
    build = []
    for name in files:
        if name.endswith(".f90"):
            build.append(dict(id=Path(name).stem, source=name, language="fortran", form="free", output=Path(name).stem + ".o"))
        elif name.endswith(".c"):
            build.append(dict(id=Path(name).stem, source=name, language="c", output=Path(name).stem + ".o"))
    objects = [step["output"] for step in build]
    import re
    stdout_match = re.search(r"write\(\*,'\(a\)'\) '([^']+)'", spec["files"]["source.f90"])
    stdout = (stdout_match.group(1) if stdout_match else f"{SUMMARY} {spec['variant'].upper().replace('_', ' ')} OK") + "\n"
    manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                    evidence=spec["evidence"], standard="f2023", oracle_basis="standard",
                    files=files, build=build, link=dict(driver="fortran", objects=objects, output="program"),
                    expect=dict(phase="run", outcome="success", exit_code=0,
                                stdout=stdout, stderr=""))
    if spec.get("profiles"):
        manifest["profiles"] = list(spec["profiles"])
    return manifest

def build_corpus(root=ROOT):
    files, specs = {}, copy.deepcopy(CASES)
    for spec in specs.values():
        rel = FIXTURE_ROOT / spec["id"]
        for name, text in spec["files"].items():
            files[Path(root) / rel / name] = text.encode("utf-8")
        manifest = manifest_for(spec)
        files[Path(root) / rel / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        spec["path"] = (rel / "fixture.json").as_posix()
        spec["manifest"] = manifest
    return files, specs

def owned_paragraph(text, prefix, replacement):
    parts = text.split("\n\n") if text else []
    matches = [i for i, p in enumerate(parts) if p.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned ISO_C_BINDING oracle paragraph")
    if matches:
        parts[matches[0]] = replacement
        return "\n\n".join(parts)
    return text + ("\n\n" if text else "") + replacement

def synced_catalogues(root=ROOT):
    _, specs = build_corpus(root)
    by_rule = {}
    for spec in specs.values():
        by_rule.setdefault(spec["rule"], set()).update(spec["facets"])
    result = {}
    for section, rel in CATALOGUES.items():
        path = Path(root) / rel
        data = json.loads(path.read_text())
        updated = copy.deepcopy(data)
        for req in updated["requirements"]:
            facets = by_rule.get(req["id"], set())
            if not facets:
                continue
            if not facets <= set(req["facets"]):
                raise ValueError(f"unknown facets for {req['id']}: {sorted(facets)}")
            for facet in facets:
                req["pending"].pop(facet, None)
            req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIX[req["id"]], ORACLES[req["id"]])
            req["oracle_limitation"] = owned_paragraph(req.get("oracle_limitation", ""), LIMIT_PREFIX[req["id"]], LIMITATIONS[req["id"]])
        result[rel] = updated
    return result

def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    rel = catalogue["render"]["path"]
    path = Path(root) / rel
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"view boundaries changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    return before + begin + "\n\n" + "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n" + end + after

def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues = synced_catalogues(root)
    views = {}
    for section, rel in CATALOGUES.items():
        views[Path(root) / catalogues[rel]["render"]["path"]] = render_view(section, catalogues[rel], root)
    if check:
        stale = [p.relative_to(root).as_posix() for p, raw in files.items() if not p.is_file() or p.read_bytes() != raw]
        for rel, data in catalogues.items():
            p = root / rel
            if json.loads(p.read_text()) != data:
                stale.append(rel)
        for p, text in views.items():
            if p.read_text() != text:
                stale.append(p.relative_to(root).as_posix())
        if stale:
            raise ValueError("stale ISO_C_BINDING fixtures: " + ", ".join(stale))
    else:
        for p, raw in files.items():
            if not p.is_file() or p.read_bytes() != raw:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(raw)
        if sync_catalogue:
            for rel, data in catalogues.items():
                (root / rel).write_text(json.dumps(data, indent=2) + "\n")
            for p, text in views.items():
                p.write_text(text)
    return specs

def apply_mutation(files, mutation):
    mutated = dict(files)
    for old, new in mutation["replacements"]:
        hits = [name for name, text in mutated.items() if old in text]
        if len(hits) != 1:
            raise ValueError(f"{mutation['id']}: replacement {old!r} hits {hits}")
        name = hits[0]
        if mutated[name].count(old) != 1:
            raise ValueError(f"{mutation['id']}: replacement {old!r} is not unique in {name}")
        mutated[name] = mutated[name].replace(old, new)
    return mutated

def compiler_flags(family, std):
    if family == "lfortran":
        return ["--std=" + std, "--no-color", "--separate-compilation"]
    flags = ["-std=" + std]
    if family == "gfortran":
        flags.append("-fdiagnostics-color=never")
    return flags

def run_command(cmd, cwd, timeout=20):
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)

def compile_and_run(files, compiler, family, std, cc, workdir):
    objects = []
    for name, text in files.items():
        (workdir / name).write_text(text)
    for name in files:
        out = Path(name).with_suffix(".o").name
        if name.endswith(".c"):
            cmd = [cc, "-std=c11", "-c", name, "-o", out]
        else:
            cmd = [compiler] + compiler_flags(family, std) + ["-c", name, "-o", out]
        res = run_command(cmd, workdir)
        if res.returncode != 0 or not (workdir / out).is_file():
            return "compile", res.returncode, res.stdout
        objects.append(out)
    exe = "program"
    res = run_command([compiler] + (["--std=" + std, "--no-color"] if family == "lfortran" else ["-std=" + std]) + objects + ["-o", exe], workdir)
    if res.returncode != 0 or not (workdir / exe).is_file():
        return "link", res.returncode, res.stdout
    res = run_command([str(workdir / exe)], workdir)
    return "run", res.returncode, res.stdout

def mutation_check(root, compiler, family, std, cc):
    specs = generate(root)
    scratch = Path(root) / f".mutation-work-iso-c-binding-18-1-18-2-{family}"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    results = []
    try:
        for spec in specs.values():
            for mutation in spec["mutations"]:
                work = scratch / spec["variant"] / mutation["id"]
                work.mkdir(parents=True)
                files = apply_mutation(spec["files"], mutation)
                phase, code, output = compile_and_run(files, compiler, family, std, cc, work)
                if phase != "run" or code == 0:
                    raise RuntimeError(f"mutation survived or failed before run: {spec['id']} {mutation['id']} {phase} {code}\n{output}")
                results.append((spec["id"], mutation["id"], phase, code))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--family", choices=["gfortran", "lfortran"])
    parser.add_argument("--std")
    parser.add_argument("--cc", default="cc")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_check:
        if not (args.compiler and args.family and args.std):
            parser.error("--mutation-check requires --compiler, --family and --std")
        results = mutation_check(args.root, args.compiler, args.family, args.std, args.cc)
        print(f"Mutation checked {len(results)} ISO_C_BINDING feature mutants with {args.family}; all failed at run time.")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} ISO_C_BINDING 18.1/18.2 fixtures.")

if __name__ == "__main__":
    main()
