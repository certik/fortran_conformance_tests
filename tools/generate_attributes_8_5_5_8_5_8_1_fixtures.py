#!/usr/bin/env python3
"""Batch 296 attribute fixtures for BIND(C), CONTIGUOUS and DIMENSION."""
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from generate_bind_common_save_fixtures import render_view as bind_prior_view
from generate_contiguous_property_fixtures import render_view as contiguous_prior_view

ROOT = Path(__file__).resolve().parents[1]
BIND_CATALOGUE = "doc/catalogues/bind_attribute_data_entities_8_5_5.json"
CONTIG_CATALOGUE = "doc/catalogues/contiguous_attribute_8_5_7.json"
DIM_CATALOGUE = "doc/catalogues/dimension_general_8_5_8_1.json"
BIND_VIEW = "doc/fortran_2023_8_5_5.md"
CONTIG_VIEW = "doc/fortran_2023_8_5_7.md"
DIM_VIEW = "doc/fortran_2023_8_5_8_1.md"
PREFIX = "attributes_8_5_5_8_5_8_1"
COMPLETIONS = {
    "bind_variable_interop": "ATTRIBUTES BIND VARIABLE INTEROP OK\n",
    "bind_common_interop": "ATTRIBUTES BIND COMMON INTEROP OK\n",
    "dimension_grammar": "ATTRIBUTES DIMENSION GRAMMAR OK\n",
    "dimension_assumed_rank": "ATTRIBUTES DIMENSION ASSUMED RANK OK\n",
    "contiguous_assumed_rank": "ATTRIBUTES CONTIGUOUS ASSUMED RANK OK\n",
}

BIND_VAR_FACETS = ("integer-scalar-admission", "integer-array-admission", "companion-variable-runtime-gate")
BIND_COMMON_FACETS = ("all-members-admission", "companion-common-runtime-gate")
DIM_R814_FACETS = ("explicit-shape-list", "assumed-shape-list", "assumed-size", "implied-shape", "shared-implied-assumed-size")
DIM_EFFECT_FACETS = ("scalar-effective-argument", "rank-one-effective-argument", "rank-two-shape-order", "zero-extent-effective-argument")
CONTIG_FACETS = ("assumed-rank-contiguous-effective",)

BIND_C820_ORACLE = (
    "Batch296 adds one C companion run for three C820 facets. A module defines an omitted-NAME "
    "INTEGER(C_INT) scalar, an explicit NAME scalar, a nonunit-lower-bound explicit-shape "
    "INTEGER(C_INT) array, and a separate zero-size INTEGER(C_INT) array with BIND(C). C functions access the same nonzero external objects through "
    "independent writes and reads: 11/13 through the omitted default label, 17/19 through the "
    "explicit scalar label, and 23/29 then 31/37 through the two nonzero array elements; SIZE(empty_array)=0 checks the zero-size category. Every check uses "
    "a literal value independent of the operation that produced it. C-source feature mutations "
    "redirect the corresponding companion accessor family to private shadow storage, so the program "
    "still compiles and links but the relevant Fortran/C visibility assertion fails at run time."
)
BIND_C820_LIMIT = (
    "Only guaranteed C_INT scalar and explicit-shape array data, including one zero-size category admission, are covered. No kind code, byte "
    "width, storage offset, descriptor, coarray, pointer, allocatable, character kind, derived type, "
    "zero-size C counterpart or ABI decoration is inferred. The C source declares the Fortran BIND "
    "objects as extern and defines only accessor procedures, so one processor initially defines each "
    "linked variable. Other C820 facets remain pending."
)
BIND_C821_ORACLE = (
    "Batch296 adds one C companion run for two C821 facets. Two INTEGER(C_INT) variables are the only "
    "members of one named COMMON block, and BIND(C,NAME='attr_bind_common') is applied to the block, "
    "not to either member. A C struct with corresponding first and second int components is accessed "
    "through setter/getter procedures: C writes 41/43 and Fortran observes both members, then Fortran "
    "writes 47/53 and C observes both members. Feature mutations redirect the C common accessors to "
    "private shadow storage, preserving a valid build but breaking the cross-language member checks."
)
BIND_C821_LIMIT = (
    "Only the finite two-C_INT-member common block is covered. There is no padding, offset, bit-field, "
    "union, flexible-array, component-name, obsolescence-warning or duplicate-common declaration oracle. "
    "The fixture does not give BIND or SAVE to individual members. Pointer, character, sequence-type and "
    "form-exclusion facets remain pending."
)
DIM_R814_ORACLE = (
    "Batch296 adds one runtime grammar-admission program for five R814 alternatives whose resulting "
    "rank/bounds can be portably inquired: explicit-shape list r2(2,3), assumed-shape list x(0:), "
    "assumed-size x(0:*), implied-shape named constants with explicit lower bound, and the shared single "
    "assumed-implied-spec form in a named constant. Each facet has a separate bounds, shape or payload "
    "assertion and a declaration/call feature mutation that remains conforming and makes that assertion fail."
)
DIM_R814_LIMIT = (
    "Vector bound alternatives are left pending because the reference compiler rejected the attempted "
    "rank-one bound expressions in ordinary declarations on this host. Deferred-shape syntax is not claimed "
    "because its declaration alone has no shape until allocation/association, and this packet avoids cloning "
    "allocation ownership. The fixture does not query SHAPE of an assumed-size dummy."
)
DIM_EFFECT_ORACLE = (
    "Batch296 adds one assumed-rank effect program for four S8.5.8.1-001 facets. Four explicit-interface "
    "calls pass a scalar, a three-element rank-one array, a rank-two array of shape [2,3], and a rank-two "
    "zero-extent array of shape [0,4] to assumed-rank INTENT(IN) dummies. Direct RANK, SHAPE and SIZE "
    "inquiries on the dummy are compared with literal expectations; no fixed-rank proxy supplies the result. "
    "Feature mutations change the effective argument for each call so the corresponding rank/shape/size "
    "assertion fails while the source remains conforming."
)
DIM_EFFECT_LIMIT = (
    "The fixture observes only rank, shape and size transfer for defined present actual arguments. It does "
    "not assert lower-bound transfer, assumed-size sentinel conventions, unavailable allocation or pointer "
    "state, optional/not-present actuals, descriptor layout, coarrays or escaped association."
)
CONTIG_ORACLE = (
    "Batch296 adds one S8.5.7-003 run for assumed-rank-contiguous-effective. A whole explicit-shape "
    "INTEGER array with shape [2,3] is passed to a non-CONTIGUOUS assumed-rank dummy. Direct "
    "IS_CONTIGUOUS(x), RANK(x), SIZE(x) and SELECT RANK payload checks establish that the dummy's "
    "effective argument is a contiguous whole array. The feature mutation changes only the actual argument "
    "to a gapped nonvector section a(1:2:1,1:3:2), which remains a conforming call but makes the literal "
    "contiguity assertion fail on the reference compiler."
)
CONTIG_LIMIT = (
    "Only the positive p2 assumed-rank/effective-argument route is covered. No CONTIGUOUS attribute, "
    "copy strategy, address, stride, temporary, vector-subscript, singleton, complex-part or residual "
    "processor-dependent case is asserted. Frozen LFortran currently ICEs on this valid assumed-rank "
    "IS_CONTIGUOUS inquiry; the reference compiler passes."
)

BASE_ORACLE_TEXT = {
    "C820": "Complete source/category admissions and isolated pointer, allocation, coarray, CHARACTER-length and derived-type report/control relations where their independent premises hold. Multilang evidence additionally binds the selected companion, object declarations, source inputs, ordered build/link and defined runtime values.",
    "C821": "Member-specific compile reports and focused repairs distinguish which otherwise valid COMMON member lacks interoperability. Actual C common-block evidence requires the full18.9.1 relationship and compatible typed companion objects; it is not supplied by declaration syntax.",
    "S8.5.7-003": "Eight complete run/effect/f2023 programs discharge eight S8.5.7-003 facets. Each program uses direct IS_CONTIGUOUS on the actual designator named by a complete p2 route and expects literal true: a CONTIGUOUS associated array pointer, a nonpointer explicit-shape whole array, an assumed-shape dummy associated with a contiguous whole-array actual, arrays allocated by ALLOCATE statements (ordinary allocatable nonzero, ordinary allocatable zero-size, and allocated pointer target), a non-CONTIGUOUS pointer associated with a contiguous whole target, a gap-free INTEGER section, a multi-dimensional section taking full leading dimensions, and a full-length CHARACTER substring array section. Every fixture also checks hand-computed bounds, shape, and nonzero INTEGER or CHARACTER payload values that are independent of the contiguity inquiry. Feature mutations replace the inquired expression with a p3 nonconsecutive array subobject; the character full-substring fixture uses a same-program INTEGER p3 sentinel so the mutation is not weakened by processor latitude for residual character-section handling. Each mutated complete program fails before printing the completion line.",
    "R814": "Finite grammar admissions and exact canonical source relations. A future syntax negative must exclude all valid alternative parses and have a minimally repaired valid control; no negative is invented for every permitted alternative.",
    "S8.5.8.1-001": "Actual assumed-rank dummy inquiries on complete conforming calls, with independently fixed small integer expectations. The scalar and empty-array routes have different rank, shape and size; array lower bounds follow the applicable argument rules, not a generalized shape-copy assertion.",
}
BASE_LIMIT_TEXT = {
    "C820": "No unsupported kind, invalid COMMON member, illegal shape declaration, incomplete interface, raw byte layout or undocumented ABI is an oracle. Optional mapping absence is not permission to skip required C_INT behavior or emit success-shaped coverage; unqualified cases remain pending. Source, compiler acceptance, C object compatibility and header/runtime consistency are separate claims.",
    "C821": "COMMON obsolescence warnings, unsupported binding implementations, invalid general COMMON membership, layout guesses and missing companion symbols are not interchangeable with this condition. No new fixture, profile, C companion, header selection or approval is supplied by the source plan.",
    "S8.5.7-003": "The selected p2 cases establish only the standard-required result of IS_CONTIGUOUS and ordinary bounds/shape/value preservation for the finite designators present in the sources. They do not measure addresses, storage stride, allocation layout, copy creation, temporaries, timing, padding, or optimization. The assumed-rank, explicit-stride singleton, vector/multiple-subscript and ranked-part/complex source-use facets remain pending. A missing positive route is never interpreted as false; false expectations belong only to the two separately selected S8.5.7-004 fixtures. The zero-size allocated object is queried only for ALLOCATED, IS_CONTIGUOUS and SHAPE, never for payload.",
    "R814": "No source-use record, execution or facet credit is created here. Existing R/C cases cannot be relabelled or cloned merely to populate this grammar selector. Numbered reporting is a capability, not mandated fatal exit, code or English wording; unsupported language features, crashes, echoes and unrelated recovery do not count.",
    "S8.5.8.1-001": "No runtime effect is weakened to compile-only because a processor lacks the language feature. Pure source-use gates and intrinsic sentinel conventions grant no execution/facet credit. Avoid optional/not-present actuals, undefined values, escaped pointers, coarray proxies and descriptor-derived expected results.",
}
ORACLE_PREFIXES = {
    "C820": "Batch296 C820 data interop fixtures: ",
    "C821": "Batch296 C821 common interop fixtures: ",
    "S8.5.7-003": "Batch296 S8.5.7-003 assumed-rank route: ",
    "R814": "Batch296 R814 DIMENSION grammar fixtures: ",
    "S8.5.8.1-001": "Batch296 S8.5.8.1-001 assumed-rank effect fixtures: ",
}
LIMIT_PREFIXES = {
    "C820": "Batch296 C820 data interop limits: ",
    "C821": "Batch296 C821 common interop limits: ",
    "S8.5.7-003": "Batch296 S8.5.7-003 assumed-rank limits: ",
    "R814": "Batch296 R814 DIMENSION grammar limits: ",
    "S8.5.8.1-001": "Batch296 S8.5.8.1-001 assumed-rank effect limits: ",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def manifest(spec):
    files = ["source.f90"] + (["companion.c"] if "c_source" in spec else [])
    build = [dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")]
    if "c_source" in spec:
        build.append(dict(id="companion", source="companion.c", language="c", output="companion.o"))
    objects = [step["output"] for step in build]
    return dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=list(spec["facets"]),
                evidence="effect", standard="f2023", oracle_basis="standard", files=files, build=build,
                link=dict(driver="fortran", objects=objects, output="program"),
                expect=dict(phase="run", outcome="success", exit_code=0,
                            stdout=COMPLETIONS[spec["variant"]], stderr=""))


def bind_variable_spec():
    f = r'''module attributes_bind_variable_mod
  use iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c) :: default_label_value = -1_c_int
  integer(c_int), bind(c, name="attr_bind_scalar") :: scalar_value = -2_c_int
  integer(c_int), bind(c, name="attr_bind_array") :: array_value(2:3) = [-3_c_int, -4_c_int]
  integer(c_int), bind(c, name="attr_bind_empty_array") :: empty_array(5:4)
  interface
    subroutine c_set_default(v) bind(c, name="c_set_default")
      import c_int
      integer(c_int), value :: v
    end subroutine
    integer(c_int) function c_get_default() bind(c, name="c_get_default")
      import c_int
    end function
    subroutine c_set_scalar(v) bind(c, name="c_set_scalar")
      import c_int
      integer(c_int), value :: v
    end subroutine
    integer(c_int) function c_get_scalar() bind(c, name="c_get_scalar")
      import c_int
    end function
    subroutine c_set_array(i, v) bind(c, name="c_set_array")
      import c_int
      integer(c_int), value :: i, v
    end subroutine
    integer(c_int) function c_get_array(i) bind(c, name="c_get_array")
      import c_int
      integer(c_int), value :: i
    end function
  end interface
end module attributes_bind_variable_mod
program attributes_bind_variable_interop
  use iso_c_binding, only: c_int
  use attributes_bind_variable_mod
  implicit none
  integer :: checks
  checks = 0
  call c_set_default(11_c_int)
  call expect_equal(int(default_label_value), 11, 'default-label C write')
  default_label_value = 13_c_int
  call expect_equal(int(c_get_default()), 13, 'default-label Fortran write')
  call c_set_scalar(17_c_int)
  call expect_equal(int(scalar_value), 17, 'explicit scalar C write')
  scalar_value = 19_c_int
  call expect_equal(int(c_get_scalar()), 19, 'explicit scalar Fortran write')
  call c_set_array(0_c_int, 23_c_int)
  call c_set_array(1_c_int, 29_c_int)
  call expect_equal(int(array_value(2)), 23, 'array element two C write')
  call expect_equal(int(array_value(3)), 29, 'array element three C write')
  array_value(2) = 31_c_int
  array_value(3) = 37_c_int
  call expect_equal(int(c_get_array(0_c_int)), 31, 'array element two Fortran write')
  call expect_equal(int(c_get_array(1_c_int)), 37, 'array element three Fortran write')
  call expect_equal(size(empty_array), 0, 'zero-size BIND array admission')
  call expect_equal(checks, 9, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES BIND VARIABLE INTEROP OK'
contains
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-BIND-VAR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_bind_variable_interop
'''
    c = r'''extern int default_label_value;
extern int attr_bind_scalar;
extern int attr_bind_array[2];
void c_set_default(int v) { default_label_value = v; }
int c_get_default(void) { return default_label_value; }
void c_set_scalar(int v) { attr_bind_scalar = v; }
int c_get_scalar(void) { return attr_bind_scalar; }
void c_set_array(int i, int v) { attr_bind_array[i] = v; }
int c_get_array(int i) { return attr_bind_array[i]; }
'''
    return dict(id="C820_valid__attributes_bind_variable_interop", variant="bind_variable_interop",
                rule="C820", facets=BIND_VAR_FACETS, source=f, c_source=c,
                derivation="C820 invokes 18.3 interoperability; C_INT scalar and explicit-shape array BIND(C) objects are accessed by extern C functions through independent values.",
                mutations={
                    "default-label-c-accessor-shadow": ("companion.c", "default_label_value", "default_label_value_shadow"),
                    "explicit-scalar-c-accessor-shadow": ("companion.c", "attr_bind_scalar", "attr_bind_scalar_shadow"),
                    "explicit-array-c-accessor-shadow": ("companion.c", "attr_bind_array", "attr_bind_array_shadow"),
                    "zero-size-array-bound": ("source.f90", "empty_array(5:4)", "empty_array(5:5)"),
                }, c_prelude="static int default_label_value_shadow; static int attr_bind_scalar_shadow; static int attr_bind_array_shadow[2];\n")


def bind_common_spec():
    f = r'''module attributes_bind_common_mod
  use iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: common_first, common_second
  common /fortran_common_pair/ common_first, common_second
  bind(c, name="attr_bind_common") :: /fortran_common_pair/
  interface
    subroutine c_set_common(a, b) bind(c, name="c_set_common")
      import c_int
      integer(c_int), value :: a, b
    end subroutine
    subroutine c_get_common(a, b) bind(c, name="c_get_common")
      import c_int
      integer(c_int), intent(out) :: a, b
    end subroutine
  end interface
end module attributes_bind_common_mod
program attributes_bind_common_interop
  use iso_c_binding, only: c_int
  use attributes_bind_common_mod
  implicit none
  integer(c_int) :: left_seen, right_seen
  integer :: checks
  checks = 0
  call c_set_common(41_c_int, 43_c_int)
  call expect_equal(int(common_first), 41, 'common first C write')
  call expect_equal(int(common_second), 43, 'common second C write')
  common_first = 47_c_int
  common_second = 53_c_int
  call c_get_common(left_seen, right_seen)
  call expect_equal(int(left_seen), 47, 'common first Fortran write')
  call expect_equal(int(right_seen), 53, 'common second Fortran write')
  call expect_equal(checks, 4, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES BIND COMMON INTEROP OK'
contains
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-BIND-COMMON-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_bind_common_interop
'''
    c = r'''struct attr_pair { int first; int second; };
extern struct attr_pair attr_bind_common;
void c_set_common(int a, int b) { attr_bind_common.first = a; attr_bind_common.second = b; }
void c_get_common(int *a, int *b) { *a = attr_bind_common.first; *b = attr_bind_common.second; }
'''
    return dict(id="C821_valid__attributes_bind_common_interop", variant="bind_common_interop",
                rule="C821", facets=BIND_COMMON_FACETS, source=f, c_source=c,
                derivation="C821 requires each member of a BIND common block to be interoperable; two C_INT members correspond to a C struct and are checked in both directions.",
                mutations={
                    "common-c-setter-shadow": ("companion.c", "attr_bind_common.first = a; attr_bind_common.second = b;", "attr_bind_common_shadow.first = a; attr_bind_common_shadow.second = b;"),
                    "common-c-getter-shadow": ("companion.c", "*a = attr_bind_common.first; *b = attr_bind_common.second;", "*a = attr_bind_common_shadow.first; *b = attr_bind_common_shadow.second;"),
                },
                c_prelude="static struct attr_pair attr_bind_common_shadow;\n")


def dimension_grammar_spec():
    f = r'''program attributes_dimension_grammar
  implicit none
  integer :: r2(2,3)
  integer, parameter :: implied(-2:*) = [10, 20, 30]
  integer, parameter :: shared_star(*) = [5, 7]
  integer :: base(-1:1)
  integer :: checks
  r2 = reshape([1, 2, 3, 4, 5, 6], shape(r2))
  base = [11, 13, 17]
  checks = 0
  call expect_equal(rank(r2), 2, 'explicit rank')
  call expect_equal(size(r2, 1), 2, 'explicit first extent')
  call expect_equal(size(r2, 2), 3, 'explicit second extent')
  call check_assumed_shape(base)
  call check_assumed_size(base)
  call expect_equal(lbound(implied, 1), -2, 'implied lower bound')
  call expect_equal(ubound(implied, 1), 0, 'implied upper bound')
  call expect_equal(implied(-1), 20, 'implied payload')
  call expect_equal(lbound(shared_star, 1), 1, 'shared star lower bound')
  call expect_equal(ubound(shared_star, 1), 2, 'shared star upper bound')
  call expect_equal(shared_star(2), 7, 'shared star payload')
  call expect_equal(checks, 15, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES DIMENSION GRAMMAR OK'
contains
  subroutine check_assumed_shape(x)
    integer, intent(in) :: x(0:)
    call expect_equal(rank(x), 1, 'assumed-shape rank')
    call expect_equal(lbound(x, 1), 0, 'assumed-shape lower bound')
    call expect_equal(ubound(x, 1), 2, 'assumed-shape upper bound')
  end subroutine
  subroutine check_assumed_size(x)
    integer, intent(in) :: x(0:*)
    call expect_equal(lbound(x, 1), 0, 'assumed-size lower bound')
    call expect_equal(x(0), 11, 'assumed-size first payload')
    call expect_equal(x(2), 17, 'assumed-size last payload')
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-DIM-GRAMMAR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_dimension_grammar
'''
    return dict(id="R814_valid__attributes_dimension_grammar", variant="dimension_grammar",
                rule="R814", facets=DIM_R814_FACETS, source=f,
                derivation="R814 alternatives are observed through direct rank, bounds, shape and payload inquiries on entities declared with the selected array-spec forms.",
                mutations={
                    "explicit-shape-list-r2-extent": ("source.f90", "integer :: r2(2,3)", "integer :: r2(3,2)"),
                    "assumed-shape-list-lower-bound": ("source.f90", "integer, intent(in) :: x(0:)", "integer, intent(in) :: x(1:)"),
                    "assumed-size-lower-bound": ("source.f90", "integer, intent(in) :: x(0:*)", "integer, intent(in) :: x(1:*)"),
                    "implied-shape-lower-bound": ("source.f90", "integer, parameter :: implied(-2:*)", "integer, parameter :: implied(-1:*)"),
                    "shared-star-lower-bound": ("source.f90", "integer, parameter :: shared_star(*)", "integer, parameter :: shared_star(2:*)"),
                })


def dimension_effect_spec():
    f = r'''program attributes_dimension_assumed_rank
  implicit none
  integer :: scalar
  integer :: rank_one(-1:1)
  integer :: rank_two(2,3)
  integer :: zero_extent(1:0,4)
  integer :: checks
  scalar = 7
  rank_one = [11, 13, 17]
  rank_two = reshape([1, 2, 3, 4, 5, 6], shape(rank_two))
  checks = 0
  call check_scalar(scalar)
  call check_rank_one(rank_one)
  call check_rank_two(rank_two)
  call check_zero_extent(zero_extent)
  call expect_equal(checks, 12, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES DIMENSION ASSUMED RANK OK'
contains
  subroutine check_scalar(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 0, 'scalar effective rank')
    call expect_equal(size(shape(x)), 0, 'scalar shape vector size')
    call expect_equal(size(x), 1, 'scalar size empty product')
  end subroutine
  subroutine check_rank_one(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 1, 'rank-one effective rank')
    call expect_shape(shape(x), [3], 'rank-one shape')
    call expect_equal(size(x), 3, 'rank-one size')
  end subroutine
  subroutine check_rank_two(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 2, 'rank-two effective rank')
    call expect_shape(shape(x), [2, 3], 'rank-two shape')
    call expect_equal(size(x), 6, 'rank-two size')
  end subroutine
  subroutine check_zero_extent(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 2, 'zero-extent effective rank')
    call expect_shape(shape(x), [0, 4], 'zero shape')
    call expect_equal(size(x), 0, 'zero total size')
  end subroutine

  subroutine expect_shape(observed, expected, label)
    integer, intent(in) :: observed(:), expected(:)
    character(len=*), intent(in) :: label
    if (size(observed) /= size(expected) .or. any(observed /= expected)) then
      write(*,'(a,1x,a)') 'ATTR-DIM-AR-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-DIM-AR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_dimension_assumed_rank
'''
    return dict(id="S8_5_8_1_001_valid__attributes_dimension_assumed_rank", variant="dimension_assumed_rank",
                rule="S8.5.8.1-001", facets=DIM_EFFECT_FACETS, source=f,
                derivation="8.5.8.1 p1 says assumed-rank dummies have the rank, shape and size of the effective argument; direct inquiries on x are compared with literal values.",
                mutations={
                    "scalar-effective-argument-to-rank-one": ("source.f90", "call check_scalar(scalar)", "call check_scalar(rank_one)"),
                    "rank-one-effective-argument-to-scalar": ("source.f90", "call check_rank_one(rank_one)", "call check_rank_one(scalar)"),
                    "rank-two-effective-argument-to-rank-one": ("source.f90", "call check_rank_two(rank_two)", "call check_rank_two(rank_one)"),
                    "zero-extent-effective-argument-to-rank-two": ("source.f90", "call check_zero_extent(zero_extent)", "call check_zero_extent(rank_two)"),
                })


def contiguous_spec():
    f = r'''program attributes_contiguous_assumed_rank
  implicit none
  integer :: a(2,3)
  integer :: checks
  a = reshape([11, 13, 17, 19, 23, 29], shape(a))
  checks = 0
  call check_effective(a)
  call expect_equal(checks, 5, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES CONTIGUOUS ASSUMED RANK OK'
contains
  subroutine check_effective(x)
    integer, intent(in) :: x(..)
    call expect_logical(is_contiguous(x), .true., 'assumed-rank contiguous effective')
    call expect_equal(rank(x), 2, 'assumed-rank rank')
    call expect_equal(size(x), 6, 'assumed-rank size')
    select rank (r => x)
    rank (2)
      call expect_equal(r(1,1), 11, 'payload first')
      call expect_equal(r(2,3), 29, 'payload last')
    rank default
      error stop 'ATTR-CONTIG-AR:wrong-rank'
    end select
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-CONTIG-AR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_logical(observed, expected, label)
    logical, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed .neqv. expected) then
      write(*,'(a,1x,a)') 'ATTR-CONTIG-AR-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_contiguous_assumed_rank
'''
    return dict(id="S8_5_7_003_valid__attributes_contiguous_assumed_rank", variant="contiguous_assumed_rank",
                rule="S8.5.7-003", facets=CONTIG_FACETS, source=f,
                derivation="8.5.7 p2 includes an assumed-rank dummy whose effective argument is contiguous; direct IS_CONTIGUOUS(x) is required true for the whole-array actual.",
                mutations={"assumed-rank-effective-argument-gapped-section": ("source.f90", "call check_effective(a)", "call check_effective(a(1:2:1,1:3:2))")})


def specs():
    rows = [bind_variable_spec(), bind_common_spec(), dimension_grammar_spec(), dimension_effect_spec(), contiguous_spec()]
    return {row["id"]: row for row in rows}


def build_corpus(root=ROOT):
    files = {}
    rows = specs()
    for spec in rows.values():
        directory = Path(root) / "tests" / "fixtures" / f"{PREFIX}_{spec['variant']}"
        spec["manifest"] = manifest(spec)
        spec["path"] = (directory / "fixture.json").relative_to(root).as_posix()
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        if "c_source" in spec:
            files[directory / "companion.c"] = spec["c_source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, rows


def owned_paragraph(text, prefix, replacement):
    paragraphs = [part for part in text.split("\n\n") if part]
    matches = [index for index, part in enumerate(paragraphs) if part.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph prefix: " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraphs)


def set_owned_text(requirement, rule, oracle, limitation):
    requirement["oracle"] = owned_paragraph(BASE_ORACLE_TEXT[rule], ORACLE_PREFIXES[rule],
                                            ORACLE_PREFIXES[rule] + oracle)
    requirement["oracle_limitation"] = owned_paragraph(BASE_LIMIT_TEXT[rule], LIMIT_PREFIXES[rule],
                                                       LIMIT_PREFIXES[rule] + limitation)


def synced_catalogues(catalogues):
    bind = copy.deepcopy(catalogues["8.5.5"])
    c820 = next(row for row in bind["requirements"] if row["id"] == "C820")
    for facet in BIND_VAR_FACETS:
        c820["pending"].pop(facet, None)
    set_owned_text(c820, "C820", BIND_C820_ORACLE, BIND_C820_LIMIT)
    c821 = next(row for row in bind["requirements"] if row["id"] == "C821")
    for facet in BIND_COMMON_FACETS:
        c821["pending"].pop(facet, None)
    set_owned_text(c821, "C821", BIND_C821_ORACLE, BIND_C821_LIMIT)

    contig = copy.deepcopy(catalogues["8.5.7"])
    s857 = next(row for row in contig["requirements"] if row["id"] == "S8.5.7-003")
    for facet in CONTIG_FACETS:
        s857["pending"].pop(facet, None)
    set_owned_text(s857, "S8.5.7-003", CONTIG_ORACLE, CONTIG_LIMIT)

    dim = copy.deepcopy(catalogues["8.5.8.1"])
    r814 = next(row for row in dim["requirements"] if row["id"] == "R814")
    for facet in DIM_R814_FACETS:
        r814["pending"].pop(facet, None)
    set_owned_text(r814, "R814", DIM_R814_ORACLE, DIM_R814_LIMIT)
    s858 = next(row for row in dim["requirements"] if row["id"] == "S8.5.8.1-001")
    for facet in DIM_EFFECT_FACETS:
        s858["pending"].pop(facet, None)
    set_owned_text(s858, "S8.5.8.1-001", DIM_EFFECT_ORACLE, DIM_EFFECT_LIMIT)
    return {"8.5.5": bind, "8.5.7": contig, "8.5.8.1": dim}


def render_bind_view(catalogue, root=ROOT):
    text = bind_prior_view(catalogue, root)
    begin, end = "<!-- BEGIN ATTRIBUTES BIND DATA INTEROP -->", "<!-- END ATTRIBUTES BIND DATA INTEROP -->"
    section = ("## Batch296 BIND(C) data companion runs\n\n"
               "Two new fixtures use declared C companion sources because `run_tests.py` supports C build steps. "
               "The variable case checks omitted-label scalar, explicit-label scalar and explicit-shape array "
               "visibility in both directions. The common-block case checks both INTEGER(C_INT) members against "
               "a corresponding C struct. Mutations redirect companion accessors to private shadow storage so "
               "build/link still succeed and runtime assertions fail. No existing BIND fixtures or bindings are changed.\n\n")
    return replace_section(text, begin, end, section)


def render_contig_view(catalogue, root=ROOT):
    text = contiguous_prior_view(catalogue, root)
    begin, end = "<!-- BEGIN ATTRIBUTES CONTIGUOUS ASSUMED RANK -->", "<!-- END ATTRIBUTES CONTIGUOUS ASSUMED RANK -->"
    section = ("## Batch296 assumed-rank contiguity route\n\n"
               "One new fixture covers only the 8.5.7 p2 route where an assumed-rank dummy has a contiguous "
               "effective argument. The source uses direct `IS_CONTIGUOUS(x)`, rank/size inquiries and SELECT "
               "RANK payload checks. The mutation changes the actual to a gapped section. Residual singleton, "
               "vector, complex-part and processor-dependent cases remain pending.\n\n")
    return replace_section(text, begin, end, section)


def render_dim_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / DIM_VIEW).read_text()
    begin, end = "<!-- BEGIN GENERATED 8.5.8.1 -->", "<!-- END GENERATED 8.5.8.1 -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("dimension generated region changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary_begin, summary_end = "<!-- BEGIN ATTRIBUTES DIMENSION RUNTIME -->", "<!-- END ATTRIBUTES DIMENSION RUNTIME -->"
    summary = ("## Batch296 DIMENSION rank/bounds inquiries\n\n"
               "Two new fixtures use direct inquiry results as oracles. The R814 fixture covers five supported "
               "array-spec alternatives with separate rank, bounds, shape or payload assertions. The p1 fixture "
               "passes scalar, rank-one, rank-two and zero-extent effective arguments to assumed-rank dummies "
               "and checks RANK, SHAPE and SIZE directly on the dummy. Vector-bound alternatives remain pending "
               "after the reference compiler rejected the attempted rank-one bound expressions.\n\n")
    before = replace_section(before.rstrip() + "\n\n", summary_begin, summary_end, summary)
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def replace_section(text, begin, end, body):
    block = begin + "\n\n" + body + end
    if begin in text or end in text:
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("invalid generated subsection boundaries")
        before, rest = text.split(begin)
        _, after = rest.split(end)
        return before.rstrip() + "\n\n" + block + after
    return text.rstrip() + "\n\n" + block + "\n"


def mutation_sources(spec):
    base_files = {"source.f90": spec["source"].encode("ascii")}
    if "c_source" in spec:
        base_files["companion.c"] = spec["c_source"].encode("ascii")
    result = {}
    for name, (file_name, old, new) in spec["mutations"].items():
        files = dict(base_files)
        text = files[file_name].decode("ascii")
        if text.count(old) < 1:
            raise ValueError(f"mutation {name} old text not found")
        if file_name == "companion.c" and "c_prelude" in spec:
            text = spec["c_prelude"] + text.replace(old, new)
        else:
            text = text.replace(old, new, 1)
        files[file_name] = text.encode("ascii")
        result[name] = files
    return result


def run_mutations(compiler, std, cc="cc", only=None):
    selected = specs()
    if only:
        selected = {k: v for k, v in selected.items() if only in k or only in v["variant"]}
    scratch = ROOT / ".mutation_attributes_8_5_5_8_5_8_1"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    failures = []
    try:
        for spec in selected.values():
            cases = {"parent": {"source.f90": spec["source"].encode("ascii")}}
            if "c_source" in spec:
                cases["parent"]["companion.c"] = spec["c_source"].encode("ascii")
            cases.update(mutation_sources(spec))
            for mut_name, files in cases.items():
                work = scratch / spec["variant"] / mut_name
                work.mkdir(parents=True)
                for file_name, raw in files.items():
                    (work / file_name).write_bytes(raw)
                objects = []
                commands = []
                fcmd = [compiler, f"--std={std}" if "lfortran" in Path(compiler).name else f"-std={std}", "-c", "source.f90", "-o", "source.o"]
                commands.append(fcmd)
                objects.append("source.o")
                if "companion.c" in files:
                    commands.append([cc, "-c", "companion.c", "-o", "companion.o"])
                    objects.append("companion.o")
                link = [compiler, f"--std={std}" if "lfortran" in Path(compiler).name else f"-std={std}", *objects, "-o", "program"]
                commands.append(link)
                ok = True
                output = ""
                for cmd in commands:
                    proc = subprocess.run(cmd, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
                    output += proc.stdout + proc.stderr
                    if proc.returncode != 0:
                        ok = False
                        break
                if ok:
                    proc = subprocess.run([str(work / "program")], cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                    output += proc.stdout + proc.stderr
                    if mut_name == "parent":
                        if proc.returncode != 0 or proc.stdout != COMPLETIONS[spec["variant"]] or proc.stderr != "":
                            failures.append(f"{spec['variant']} parent failed: rc={proc.returncode}\n{output}")
                    else:
                        if proc.returncode == 0 and proc.stdout == COMPLETIONS[spec["variant"]] and proc.stderr == "":
                            failures.append(f"{spec['variant']} mutation survived: {mut_name}")
                elif mut_name == "parent":
                    failures.append(f"{spec['variant']} parent did not build: {output}")
                else:
                    failures.append(f"{spec['variant']} mutation did not compile/link: {mut_name}\n{output}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if failures:
        raise SystemExit("\n---\n".join(failures))
    print(f"Mutation check passed for {len(selected)} parents on {compiler}")


def generate(check=False, sync_catalogue=False):
    files, rows = build_corpus(ROOT)
    catalogues = {
        "8.5.5": json.loads((ROOT / BIND_CATALOGUE).read_text()),
        "8.5.7": json.loads((ROOT / CONTIG_CATALOGUE).read_text()),
        "8.5.8.1": json.loads((ROOT / DIM_CATALOGUE).read_text()),
    }
    updated = synced_catalogues(catalogues)
    views = {BIND_VIEW: render_bind_view(updated["8.5.5"]),
             CONTIG_VIEW: render_contig_view(updated["8.5.7"]),
             DIM_VIEW: render_dim_view(updated["8.5.8.1"])}
    if check:
        stale = [p.relative_to(ROOT).as_posix() for p, raw in files.items() if not p.is_file() or p.read_bytes() != raw]
        for path, cat in ((BIND_CATALOGUE, updated["8.5.5"]), (CONTIG_CATALOGUE, updated["8.5.7"]), (DIM_CATALOGUE, updated["8.5.8.1"])):
            if json.loads((ROOT / path).read_text()) != cat:
                stale.append(path)
        for path, text in views.items():
            if (ROOT / path).read_text() != text:
                stale.append(path)
        if stale:
            raise SystemExit("stale attributes batch296 corpus: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogue:
            (ROOT / BIND_CATALOGUE).write_text(json.dumps(updated["8.5.5"], indent=2) + "\n")
            (ROOT / CONTIG_CATALOGUE).write_text(json.dumps(updated["8.5.7"], indent=2) + "\n")
            (ROOT / DIM_CATALOGUE).write_text(json.dumps(updated["8.5.8.1"], indent=2) + "\n")
            for path, text in views.items():
                (ROOT / path).write_text(text)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    parser.add_argument("--cc", default="cc")
    parser.add_argument("--only")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler or not args.std:
            parser.error("--mutation-check requires --compiler and --std")
        run_mutations(args.compiler, args.std, args.cc, args.only)
        return
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    rows = generate(args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(rows)} batch296 attribute fixtures.")


if __name__ == "__main__":
    main()
