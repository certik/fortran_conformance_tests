#!/usr/bin/env python3
"""Fixtures for Fortran 2023 procedure references in 15.5.1."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "15.5.1"
CATALOGUE = "doc/catalogues/syntax_of_a_procedure_reference_15_5_1.json"
VIEW = "doc/fortran_2023_15_5_1.md"
SUMMARY_BEGIN = "<!-- BEGIN PROCEDURE REFERENCE 15.5.1 FIXTURES -->"
SUMMARY_END = "<!-- END PROCEDURE REFERENCE 15.5.1 FIXTURES -->"
EXCLUDES = [
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal compiler error", "internal error", "Internal Compiler Error", "ICE", "ASR verify",
    "asr.verify", "verifier", "AssertFailed", "Unhandled exception", "Traceback", "LLVM ERROR",
]

ORACLE_PREFIX = "Procedure-reference 15.5.1 fixture packet: "
LIMIT_PREFIX = "Procedure-reference 15.5.1 fixture boundaries: "
ORACLE = ORACLE_PREFIX + (
    "complete run/effect/f2023 programs exercise ordinary function and CALL syntax, procedure designator "
    "forms, keyword association, procedure-name and procedure-component actual procedures, alternate-return "
    "label selection, and the defined-operation/defined-assignment reference forms admitted by 15.5.1p4. "
    "Each runtime assertion starts from a nondefault sentinel, observes an exact integer state, and has a "
    "load-bearing conforming feature mutation: sibling procedure calls, keyword swaps, alternate-label swaps, "
    "or replacement by an ordinary intrinsic assignment. Compile/diagnose fixtures cover selected numbered "
    "constraints with one-property run controls; their diagnostic oracle requires any error on the violating "
    "line and excludes unsupported, unimplemented, ICE, internal-error, ASR-verifier, traceback, and LLVM-crash "
    "messages rather than matching processor wording."
)
LIMITATION = LIMIT_PREFIX + (
    "coverage is single-image and uses default INTEGER sentinels only. Conditional-argument rules R1526-R1528 "
    "and C1538-C1545, coindexed/coarray restrictions C1528/C1537 and corank facets, defined I/O, finalization, "
    "specific-intrinsic category enumeration, and unallocated/unassociated data-ref runtime errors remain pending "
    "or owned by later sections. Procedure bodies are used only to make procedure-reference dispatch observable; "
    "no ABI, storage address, finalization order, processor diagnostic vocabulary, warning severity, or exact "
    "IO formatting property is claimed."
)

RUNTIME_CASES = []
DIAGNOSTIC_CASES = []
CONTROLS = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def line_of(source, needle):
    for i, line in enumerate(source.splitlines(), 1):
        if needle in line:
            return i
    raise ValueError(f"cannot find diagnostic line {needle!r}")


def runtime_case(rule, variant, facets, source, stdout, mutations):
    case_id = rule.replace('.', '_').replace('-', '_') + "_valid__procedure_reference_15_5_1_" + variant
    RUNTIME_CASES.append(dict(id=case_id, rule=rule, variant=variant, facets=facets,
                              source=source, stdout=stdout, mutations=mutations))


def diagnostic_case(rule, variant, facet, invalid_source, control_source, invalid_needle, control_stdout):
    invalid_id = rule + "_invalid__procedure_reference_15_5_1_" + variant
    control_id = rule + "_valid__procedure_reference_15_5_1_" + variant + "_control"
    DIAGNOSTIC_CASES.append(dict(id=invalid_id, rule=rule, variant=variant, facets=[facet],
                                 source=invalid_source, line=line_of(invalid_source, invalid_needle),
                                 control_id=control_id))
    CONTROLS.append(dict(id=control_id, rule=rule, variant=variant + "_control", facets=[facet],
                         source=control_source, stdout=control_stdout, controls=invalid_id))


core_source = """module procedure_reference_15_5_1_core_m
  implicit none
  integer :: ping_seen = -91
  integer :: ping_empty_seen = -92
contains
  integer function f0()
    f0 = 11
  end function
  integer function f0_alt()
    f0_alt = 12
  end function
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  subroutine ping
    ping_seen = 31
  end subroutine
  subroutine ping_other
    ping_seen = 131
  end subroutine
  subroutine ping_empty()
    ping_empty_seen = 32
  end subroutine
  subroutine ping_empty_other()
    ping_empty_seen = 132
  end subroutine
  subroutine set_value(x)
    integer, intent(out) :: x
    x = 23
  end subroutine
  subroutine set_value_other(x)
    integer, intent(out) :: x
    x = 24
  end subroutine
  subroutine take(a)
    integer, intent(out) :: a
    a = 6
  end subroutine
  subroutine take_other(a)
    integer, intent(out) :: a
    a = 16
  end subroutine
  subroutine mix(a, b, out)
    integer, intent(in) :: a, b
    integer, intent(out) :: out
    out = 100 * a + b
  end subroutine
  subroutine accept_in(a, seen)
    integer, intent(in) :: a
    integer, intent(out) :: seen
    seen = a
  end subroutine
  subroutine set_out(x)
    integer, intent(out) :: x
    x = 9
  end subroutine
  subroutine set_out_other(x)
    integer, intent(out) :: x
    x = 19
  end subroutine
end module procedure_reference_15_5_1_core_m

program procedure_reference_15_5_1_core
  use procedure_reference_15_5_1_core_m
  implicit none
  integer :: observed_empty, observed_actual, actual_value
  integer :: pos, kwout, expr_seen, var_seen, checks
  checks = 0
  observed_empty = -9
  observed_empty = f0()
  if (observed_empty /= 11) error stop 101
  checks = checks + 1
  observed_actual = -9
  observed_actual = inc(4)
  if (observed_actual /= 5) error stop 102
  checks = checks + 1
  ping_seen = -91
  call ping
  if (ping_seen /= 31) error stop 103
  checks = checks + 1
  ping_empty_seen = -92
  call ping_empty()
  if (ping_empty_seen /= 32) error stop 104
  checks = checks + 1
  actual_value = -1
  call set_value(actual_value)
  if (actual_value /= 23) error stop 105
  checks = checks + 1
  pos = -5
  call take(pos)
  if (pos /= 6) error stop 106
  checks = checks + 1
  kwout = -7
  call mix(b=2, a=5, out=kwout)
  if (kwout /= 502) error stop 107
  checks = checks + 1
  expr_seen = -8
  call accept_in(2 + 3, expr_seen)
  if (expr_seen /= 5) error stop 108
  checks = checks + 1
  var_seen = -9
  call set_out(var_seen)
  if (var_seen /= 9) error stop 109
  checks = checks + 1
  if (checks /= 9) error stop 199
  print '(a)', 'PROCEDURE REFERENCE CORE OK'
end program procedure_reference_15_5_1_core
"""
runtime_case("R1520", "core_forms", [
    "function-reference-empty-list", "function-reference-with-actual-list",
], core_source, "PROCEDURE REFERENCE CORE OK\n", [
    dict(id="empty_function_sibling", facet="function-reference-empty-list", expected="observed_empty = f0()", replacement="observed_empty = f0_alt()"),
    dict(id="function_actual_value", facet="function-reference-with-actual-list", expected="observed_actual = inc(4)", replacement="observed_actual = inc(5)"),
])
runtime_case("R1521", "call_stmt_forms", [
    "call-stmt-no-parentheses", "call-stmt-empty-parentheses", "call-stmt-with-actual-list",
], core_source, "PROCEDURE REFERENCE CORE OK\n", [
    dict(id="call_without_parentheses_sibling", facet="call-stmt-no-parentheses", expected="call ping\n", replacement="call ping_other\n"),
    dict(id="call_empty_parentheses_sibling", facet="call-stmt-empty-parentheses", expected="call ping_empty()", replacement="call ping_empty_other()"),
    dict(id="call_actual_list_sibling", facet="call-stmt-with-actual-list", expected="call set_value(actual_value)", replacement="call set_value_other(actual_value)"),
])
runtime_case("R1523", "actual_arg_specs", [
    "actual-arg-spec-positional", "actual-arg-spec-keyword",
], core_source, "PROCEDURE REFERENCE CORE OK\n", [
    dict(id="positional_actual_sibling", facet="actual-arg-spec-positional", expected="call take(pos)", replacement="call take_other(pos)"),
    dict(id="keyword_actual_swap", facet="actual-arg-spec-keyword", expected="call mix(b=2, a=5, out=kwout)", replacement="call mix(a=2, b=5, out=kwout)"),
])
runtime_case("R1524", "expression_variable_actuals", [
    "actual-arg-expression", "actual-arg-variable",
], core_source, "PROCEDURE REFERENCE CORE OK\n", [
    dict(id="expression_actual_value", facet="actual-arg-expression", expected="call accept_in(2 + 3, expr_seen)", replacement="call accept_in(2 + 4, expr_seen)"),
    dict(id="variable_actual_sibling", facet="actual-arg-variable", expected="call set_out(var_seen)", replacement="call set_out_other(var_seen)"),
])

def_source = """module procedure_reference_15_5_1_definition_m
contains
  integer function module_add(n)
    integer, intent(in) :: n
    module_add = n + 6
  end function
  integer function module_alt(n)
    integer, intent(in) :: n
    module_alt = n + 60
  end function
end module procedure_reference_15_5_1_definition_m

integer function external_add(n)
  integer, intent(in) :: n
  external_add = n + 4
end function external_add

integer function external_alt(n)
  integer, intent(in) :: n
  external_alt = n + 40
end function external_alt

program procedure_reference_15_5_1_definition
  use procedure_reference_15_5_1_definition_m
  implicit none
  interface
    integer function external_add(n)
      integer, intent(in) :: n
    end function
    integer function external_alt(n)
      integer, intent(in) :: n
    end function
  end interface
  integer :: internal_value, module_value, external_value, checks
  checks = 0
  internal_value = -77
  module_value = -77
  external_value = -77
  internal_value = internal_add(5)
  if (internal_value /= 8) error stop 201
  checks = checks + 1
  module_value = module_add(5)
  if (module_value /= 11) error stop 202
  checks = checks + 1
  external_value = external_add(5)
  if (external_value /= 9) error stop 203
  checks = checks + 1
  if (checks /= 3) error stop 299
  print '(a)', 'PROCEDURE REFERENCE DEFINITION MECHANISMS OK'
contains
  integer function internal_add(n)
    integer, intent(in) :: n
    internal_add = n + 3
  end function
  integer function internal_alt(n)
    integer, intent(in) :: n
    internal_alt = n + 30
  end function
end program procedure_reference_15_5_1_definition
"""
runtime_case("S15.5.1-001", "definition_mechanisms", ["reference-form-definition-mechanism-independent"],
             def_source, "PROCEDURE REFERENCE DEFINITION MECHANISMS OK\n", [
    dict(id="internal_sibling", facet="reference-form-definition-mechanism-independent", expected="internal_value = internal_add(5)", replacement="internal_value = internal_alt(5)"),
    dict(id="module_sibling", facet="reference-form-definition-mechanism-independent", expected="module_value = module_add(5)", replacement="module_value = module_alt(5)"),
    dict(id="external_sibling", facet="reference-form-definition-mechanism-independent", expected="external_value = external_add(5)", replacement="external_value = external_alt(5)"),
])

designator_source = """module procedure_reference_15_5_1_designator_m
  implicit none
  abstract interface
    subroutine set_iface(x)
      integer, intent(out) :: x
    end subroutine
  end interface
  type holder
    procedure(set_iface), pointer, nopass :: op => null()
  end type
  type tagged
    integer :: value = -3
  contains
    procedure :: tb_set
    procedure :: tb_set_other
  end type
contains
  subroutine named_set(x)
    integer, intent(out) :: x
    x = 101
  end subroutine
  subroutine named_set_other(x)
    integer, intent(out) :: x
    x = 111
  end subroutine
  subroutine comp_set(x)
    integer, intent(out) :: x
    x = 202
  end subroutine
  subroutine comp_set_other(x)
    integer, intent(out) :: x
    x = 212
  end subroutine
  subroutine tb_set(self)
    class(tagged), intent(inout) :: self
    self%value = 303
  end subroutine
  subroutine tb_set_other(self)
    class(tagged), intent(inout) :: self
    self%value = 313
  end subroutine
end module procedure_reference_15_5_1_designator_m

program procedure_reference_15_5_1_designator
  use procedure_reference_15_5_1_designator_m
  implicit none
  type(holder) :: h
  type(tagged) :: obj
  integer :: named, component, checks
  checks = 0
  named = -4
  call named_set(named)
  if (named /= 101) error stop 301
  checks = checks + 1
  component = -5
  h%op => comp_set
  call h%op(component)
  if (component /= 202) error stop 302
  checks = checks + 1
  obj%value = -3
  call obj%tb_set()
  if (obj%value /= 303) error stop 303
  checks = checks + 1
  if (checks /= 3) error stop 399
  print '(a)', 'PROCEDURE REFERENCE DESIGNATORS OK'
end program procedure_reference_15_5_1_designator
"""
runtime_case("R1522", "designators", ["procedure-name-designator", "procedure-component-ref-designator", "type-bound-binding-designator"],
             designator_source, "PROCEDURE REFERENCE DESIGNATORS OK\n", [
    dict(id="procedure_name_sibling", facet="procedure-name-designator", expected="call named_set(named)", replacement="call named_set_other(named)"),
    dict(id="procedure_component_target", facet="procedure-component-ref-designator", expected="h%op => comp_set", replacement="h%op => comp_set_other"),
    dict(id="type_bound_sibling", facet="type-bound-binding-designator", expected="call obj%tb_set()", replacement="call obj%tb_set_other()"),
])

proc_actual_source = """module procedure_reference_15_5_1_actual_proc_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
  type holder
    procedure(int_fn), pointer, nopass :: op => null()
  end type
contains
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  integer function dec(n)
    integer, intent(in) :: n
    dec = n - 1
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_15_5_1_actual_proc_m

program procedure_reference_15_5_1_actual_proc
  use procedure_reference_15_5_1_actual_proc_m
  implicit none
  type(holder) :: h
  integer :: by_name, by_component, checks
  checks = 0
  by_name = -9
  by_name = apply(inc, 4)
  if (by_name /= 5) error stop 401
  checks = checks + 1
  h%op => inc
  by_component = -8
  by_component = apply(h%op, 5)
  if (by_component /= 6) error stop 402
  checks = checks + 1
  if (checks /= 2) error stop 499
  print '(a)', 'PROCEDURE REFERENCE PROCEDURE ACTUALS OK'
end program procedure_reference_15_5_1_actual_proc
"""
runtime_case("R1524", "procedure_actuals", ["actual-arg-procedure-name", "actual-arg-proc-component-ref"],
             proc_actual_source, "PROCEDURE REFERENCE PROCEDURE ACTUALS OK\n", [
    dict(id="procedure_name_actual_sibling", facet="actual-arg-procedure-name", expected="by_name = apply(inc, 4)", replacement="by_name = apply(dec, 4)"),
    dict(id="proc_component_actual_target", facet="actual-arg-proc-component-ref", expected="h%op => inc", replacement="h%op => dec"),
])

alt_source = """program procedure_reference_15_5_1_alt_return
  implicit none
  integer :: branch, checks
  checks = 0
  branch = -1
  call choose(2, *100, *200)
  branch = -99
  go to 900
100 branch = 100
  go to 900
200 branch = 200
  go to 900
300 branch = 300
  go to 900
900 if (branch /= 200) error stop 501
  checks = checks + 1
  if (checks /= 1) error stop 599
  print '(a)', 'PROCEDURE REFERENCE ALTERNATE RETURN OK'
contains
  subroutine choose(which, *, *)
    integer, intent(in) :: which
    if (which == 1) return 1
    return 2
  end subroutine
end program procedure_reference_15_5_1_alt_return
"""
runtime_case("R1524", "alternate_return_actual", ["actual-arg-alt-return"],
             alt_source, "PROCEDURE REFERENCE ALTERNATE RETURN OK\n", [
    dict(id="alternate_return_label_order", facet="actual-arg-alt-return", expected="call choose(2, *100, *200)", replacement="call choose(2, *200, *100)"),
])
runtime_case("R1525", "alternate_return", ["alt-return-star-label"],
             alt_source, "PROCEDURE REFERENCE ALTERNATE RETURN OK\n", [
    dict(id="alternate_return_star_label_target", facet="alt-return-star-label", expected="call choose(2, *100, *200)", replacement="call choose(2, *100, *300)"),
])

defined_source = """module procedure_reference_15_5_1_defined_m
  implicit none
  type box
    integer :: value = -9
  end type
  interface operator(.join.)
    module procedure join_values
  end interface
  interface operator(.other.)
    module procedure other_values
  end interface
  interface assignment(=)
    module procedure assign_integer
  end interface
contains
  integer function join_values(a, b)
    integer, intent(in) :: a, b
    join_values = 10 * a + b
  end function
  integer function other_values(a, b)
    integer, intent(in) :: a, b
    other_values = 10 * b + a
  end function
  subroutine assign_integer(lhs, rhs)
    type(box), intent(out) :: lhs
    integer, intent(in) :: rhs
    lhs%value = rhs + 5
  end subroutine
end module procedure_reference_15_5_1_defined_m

program procedure_reference_15_5_1_defined
  use procedure_reference_15_5_1_defined_m
  implicit none
  type(box) :: item
  integer :: op_value, checks
  checks = 0
  op_value = -1
  op_value = 3 .join. 4
  if (op_value /= 34) error stop 601
  checks = checks + 1
  item%value = -9
  item = 12
  if (item%value /= 17) error stop 602
  checks = checks + 1
  if (checks /= 2) error stop 699
  print '(a)', 'PROCEDURE REFERENCE DEFINED FORMS OK'
end program procedure_reference_15_5_1_defined
"""
runtime_case("S15.5.1-004", "defined_forms", ["function-defined-operation-reference", "subroutine-defined-assignment-reference"],
             defined_source, "PROCEDURE REFERENCE DEFINED FORMS OK\n", [
    dict(id="defined_operator_sibling", facet="function-defined-operation-reference", expected="op_value = 3 .join. 4", replacement="op_value = 3 .other. 4"),
    dict(id="defined_assignment_to_intrinsic_assignment", facet="subroutine-defined-assignment-reference", expected="item = 12", replacement="item = box(12)"),
])

# Compile-diagnostic cases and their run controls.
diagnostic_case("C1523", "subroutine_as_function", "function-reference-designator-is-function",
"""program procedure_reference_c1523_invalid
  implicit none
  interface
    subroutine sub(n)
      integer, intent(in) :: n
    end subroutine
  end interface
  integer :: x
  x = sub(4)
end program procedure_reference_c1523_invalid
""",
"""program procedure_reference_c1523_control
  implicit none
  interface
    integer function sub(n)
      integer, intent(in) :: n
    end function
  end interface
  integer :: x
  x = -9
  x = sub(4)
  if (x /= 5) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1523 CONTROL OK'
end program procedure_reference_c1523_control
integer function sub(n)
  integer, intent(in) :: n
  sub = n + 1
end function sub
""", "x = sub(4)", "PROCEDURE REFERENCE C1523 CONTROL OK\n")

diagnostic_case("C1524", "function_alt_return", "function-reference-no-alt-return-actual",
"""program procedure_reference_c1524_invalid
  implicit none
  integer :: x
  x = f(*100)
100 continue
contains
  integer function f(n)
    integer, intent(in) :: n
    f = n
  end function
end program procedure_reference_c1524_invalid
""",
"""program procedure_reference_c1524_control
  implicit none
  integer :: x
  x = -9
  x = f(7)
100 continue
  if (x /= 7) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1524 CONTROL OK'
contains
  integer function f(n)
    integer, intent(in) :: n
    f = n
  end function
end program procedure_reference_c1524_control
""", "x = f(*100)", "PROCEDURE REFERENCE C1524 CONTROL OK\n")

diagnostic_case("C1525", "function_as_call", "call-designator-is-subroutine",
"""program procedure_reference_c1525_invalid
  implicit none
  interface
    integer function f(n)
      integer, intent(in) :: n
    end function
  end interface
  call f(4)
end program procedure_reference_c1525_invalid
""",
"""program procedure_reference_c1525_control
  implicit none
  integer :: seen
  seen = -9
  call f(4, seen)
  if (seen /= 5) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1525 CONTROL OK'
contains
  subroutine f(n, out)
    integer, intent(in) :: n
    integer, intent(out) :: out
    out = n + 1
  end subroutine
end program procedure_reference_c1525_control
""", "call f(4)", "PROCEDURE REFERENCE C1525 CONTROL OK\n")

diagnostic_case("C1526", "data_object_as_procedure", "procedure-name-generic-or-procedure",
"""program procedure_reference_c1526_invalid
  implicit none
  integer :: pvar
  call pvar()
end program procedure_reference_c1526_invalid
""",
"""program procedure_reference_c1526_control
  implicit none
  integer :: seen
  seen = -1
  call pvar(seen)
  if (seen /= 42) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1526 CONTROL OK'
contains
  subroutine pvar(out)
    integer, intent(out) :: out
    out = 42
  end subroutine
end program procedure_reference_c1526_control
""", "call pvar()", "PROCEDURE REFERENCE C1526 CONTROL OK\n")

diagnostic_case("C1527", "binding_not_declared_type", "binding-name-belongs-to-declared-type",
"""module procedure_reference_c1527_m
  implicit none
  type parent
    integer :: value = -1
  contains
    procedure :: parent_set
  end type
  type, extends(parent) :: child
  contains
    procedure :: child_only
  end type
contains
  subroutine parent_set(self)
    class(parent), intent(inout) :: self
    self%value = 11
  end subroutine
  subroutine child_only(self)
    class(child), intent(inout) :: self
    self%value = 99
  end subroutine
end module procedure_reference_c1527_m
program procedure_reference_c1527_invalid
  use procedure_reference_c1527_m
  implicit none
  class(parent), allocatable :: obj
  allocate(child :: obj)
  call obj%child_only()
end program procedure_reference_c1527_invalid
""",
"""module procedure_reference_c1527_m
  implicit none
  type parent
    integer :: value = -1
  contains
    procedure :: parent_set
  end type
  type, extends(parent) :: child
  contains
    procedure :: child_only
  end type
contains
  subroutine parent_set(self)
    class(parent), intent(inout) :: self
    self%value = 11
  end subroutine
  subroutine child_only(self)
    class(child), intent(inout) :: self
    self%value = 99
  end subroutine
end module procedure_reference_c1527_m
program procedure_reference_c1527_control
  use procedure_reference_c1527_m
  implicit none
  class(parent), allocatable :: obj
  allocate(child :: obj)
  call obj%parent_set()
  if (obj%value /= 11) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1527 CONTROL OK'
end program procedure_reference_c1527_control
""", "call obj%child_only()", "PROCEDURE REFERENCE C1527 CONTROL OK\n")

diagnostic_case("C1529", "array_nopass_binding", "array-data-ref-type-bound-procedure-has-pass",
"""module procedure_reference_c1529_m
  implicit none
  type t
  contains
    procedure, nopass :: touch
  end type
contains
  subroutine touch()
  end subroutine
end module procedure_reference_c1529_m
program procedure_reference_c1529_invalid
  use procedure_reference_c1529_m
  implicit none
  type(t) :: a(2)
  call a%touch()
end program procedure_reference_c1529_invalid
""",
"""module procedure_reference_c1529_m
  implicit none
  type t
    integer :: value = -1
  contains
    procedure :: touch
  end type
contains
  elemental subroutine touch(self)
    class(t), intent(inout) :: self
    self%value = self%value + 10
  end subroutine
end module procedure_reference_c1529_m
program procedure_reference_c1529_control
  use procedure_reference_c1529_m
  implicit none
  type(t) :: a(2)
  a%value = [1, 2]
  call a%touch()
  if (any(a%value /= [11, 12])) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1529 CONTROL OK'
end program procedure_reference_c1529_control
""", "call a%touch()", "PROCEDURE REFERENCE C1529 CONTROL OK\n")

diagnostic_case("C1530", "keyword_implicit_interface", "no-keyword-actual-with-implicit-interface",
"""program procedure_reference_c1530_invalid
  implicit none
  integer :: x
  external ext
  x = 5
  call ext(a=x)
end program procedure_reference_c1530_invalid
subroutine ext(a)
  integer, intent(inout) :: a
  a = a + 1
end subroutine ext
""",
"""program procedure_reference_c1530_control
  implicit none
  interface
    subroutine ext(a)
      integer, intent(inout) :: a
    end subroutine
  end interface
  integer :: x
  x = 5
  call ext(a=x)
  if (x /= 6) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1530 CONTROL OK'
end program procedure_reference_c1530_control
subroutine ext(a)
  integer, intent(inout) :: a
  a = a + 1
end subroutine ext
""", "call ext(a=x)", "PROCEDURE REFERENCE C1530 CONTROL OK\n")

diagnostic_case("C1531", "positional_after_keyword", "no-positional-actual-after-keyword-actual",
"""program procedure_reference_c1531_invalid
  implicit none
  integer :: out
  out = -1
  call mix(a=5, 2, out=out)
contains
  subroutine mix(a, b, out)
    integer, intent(in) :: a, b
    integer, intent(out) :: out
    out = 100 * a + b
  end subroutine
end program procedure_reference_c1531_invalid
""",
"""program procedure_reference_c1531_control
  implicit none
  integer :: out
  out = -1
  call mix(a=5, b=2, out=out)
  if (out /= 502) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1531 CONTROL OK'
contains
  subroutine mix(a, b, out)
    integer, intent(in) :: a, b
    integer, intent(out) :: out
    out = 100 * a + b
  end subroutine
end program procedure_reference_c1531_control
""", "call mix(a=5, 2, out=out)", "PROCEDURE REFERENCE C1531 CONTROL OK\n")

diagnostic_case("C1532", "keyword_not_dummy", "keyword-names-dummy-argument",
"""program procedure_reference_c1532_invalid
  implicit none
  integer :: x, missing, out
  x = 5; missing = -99; out = -1
  call one(missing=x)
contains
  subroutine one(a)
    integer, intent(in) :: a
    out = a + 1
  end subroutine
end program procedure_reference_c1532_invalid
""",
"""program procedure_reference_c1532_control
  implicit none
  integer :: x, missing, out
  x = 5; missing = -99; out = -1
  call one(a=x)
  if (out /= 6) error stop 1
  if (missing /= -99) error stop 2
  print '(a)', 'PROCEDURE REFERENCE C1532 CONTROL OK'
contains
  subroutine one(a)
    integer, intent(in) :: a
    out = a + 1
  end subroutine
end program procedure_reference_c1532_control
""", "call one(missing=x)", "PROCEDURE REFERENCE C1532 CONTROL OK\n")

diagnostic_case("C1533", "elemental_actual_procedure", "nonintrinsic-elemental-not-actual-procedure",
"""module procedure_reference_c1533_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
contains
  elemental integer function elem(n)
    integer, intent(in) :: n
    elem = n + 1
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1533_m
program procedure_reference_c1533_invalid
  use procedure_reference_c1533_m
  implicit none
  integer :: x
  x = apply(elem, 4)
end program procedure_reference_c1533_invalid
""",
"""module procedure_reference_c1533_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
contains
  integer function elem(n)
    integer, intent(in) :: n
    elem = n + 1
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1533_m
program procedure_reference_c1533_control
  use procedure_reference_c1533_m
  implicit none
  integer :: x
  x = -1
  x = apply(elem, 4)
  if (x /= 5) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1533 CONTROL OK'
end program procedure_reference_c1533_control
""", "x = apply(elem, 4)", "PROCEDURE REFERENCE C1533 CONTROL OK\n")

diagnostic_case("C1534", "generic_actual_procedure", "generic-name-not-procedure-name-actual",
"""module procedure_reference_c1534_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
  interface gen
    module procedure inc, rinc
  end interface
contains
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  real function rinc(x)
    real, intent(in) :: x
    rinc = x + 1.0
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1534_m
program procedure_reference_c1534_invalid
  use procedure_reference_c1534_m
  implicit none
  integer :: x
  x = apply(gen, 4)
end program procedure_reference_c1534_invalid
""",
"""module procedure_reference_c1534_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
  interface gen
    module procedure inc, rinc
  end interface
contains
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  real function rinc(x)
    real, intent(in) :: x
    rinc = x + 1.0
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1534_m
program procedure_reference_c1534_control
  use procedure_reference_c1534_m
  implicit none
  integer :: x
  x = -1
  x = apply(inc, 4)
  if (x /= 5) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1534 CONTROL OK'
end program procedure_reference_c1534_control
""", "x = apply(gen, 4)", "PROCEDURE REFERENCE C1534 CONTROL OK\n")

diagnostic_case("C1536", "alt_return_format_label", "alt-return-label-branch-target",
"""program procedure_reference_c1536_branch_invalid
  implicit none
  call choose(*100)
100 format('not a branch target')
contains
  subroutine choose(*)
    return 1
  end subroutine
end program procedure_reference_c1536_branch_invalid
""",
"""program procedure_reference_c1536_branch_control
  implicit none
  integer :: branch
  branch = -1
  call choose(*100)
  branch = -2
  go to 900
100 branch = 100
900 if (branch /= 100) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1536 BRANCH CONTROL OK'
contains
  subroutine choose(*)
    return 1
  end subroutine
end program procedure_reference_c1536_branch_control
""", "call choose(*100)", "PROCEDURE REFERENCE C1536 BRANCH CONTROL OK\n")

RESTORED_PENDING = {
    "C1525": {
        "call-designator-is-subroutine": (
            "Pending after batch308: gfortran 16 rejects CALL of a function but reports the "
            "primary error at the function/interface declaration rather than at the CALL statement, "
            "so the line-anchored diagnostic oracle required for fixture packets is not portable."
        )
    },
    "C1526": {
        "procedure-name-generic-or-procedure": (
            "Pending after batch308: gfortran 16 rejects CALL of an integer data object but reports "
            "the primary error at the object declaration rather than at the CALL statement, so the "
            "line-anchored diagnostic oracle required for fixture packets is not portable."
        )
    },
}

DIAGNOSTIC_CASES[:] = [case for case in DIAGNOSTIC_CASES if case["rule"] not in RESTORED_PENDING]
CONTROLS[:] = [case for case in CONTROLS if case["rule"] not in RESTORED_PENDING]


def all_specs():
    result = []
    for spec in RUNTIME_CASES:
        row = copy.deepcopy(spec)
        row["kind"] = "valid"
        row["evidence"] = "effect"
        result.append(row)
    for spec in DIAGNOSTIC_CASES:
        row = copy.deepcopy(spec)
        row["kind"] = "invalid"
        row["evidence"] = "effect"
        result.append(row)
    for spec in CONTROLS:
        row = copy.deepcopy(spec)
        row["kind"] = "valid"
        row["evidence"] = "positive-control"
        result.append(row)
    return result


def directory_for(spec):
    return "tests/fixtures/procedure_reference_15_5_1_" + spec["variant"]


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for spec in all_specs():
        raw = spec["source"].encode("ascii")
        spec["source_sha256"] = sha(raw)
        relative = directory_for(spec)
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
        if spec["kind"] == "invalid":
            manifest["expect"] = dict(
                phase="compile", step="source", outcome="diagnose",
                diagnostic=dict(file="source.f90", line=spec["line"], end_line=spec["line"],
                                excludes_any=EXCLUDES))
        else:
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                       stdout=spec["stdout"], stderr="")
        spec["path"], spec["manifest"] = relative + "/fixture.json", manifest
        files[root / relative / "source.f90"] = raw
        files[root / relative / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        specs[spec["id"]] = spec
    return files, specs


def runtime_specs(root=ROOT):
    _, specs = build_corpus(root)
    return [spec for spec in specs.values() if spec["id"] in {case["id"] for case in RUNTIME_CASES}]


def mutated_source(spec, mutation, allow_identical=False):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent input changed for " + spec["id"])
    expected = mutation["expected"].encode("ascii")
    count = raw.count(expected)
    if count != 1:
        raise ValueError(f"{spec['id']}::{mutation['id']} expected token count {count}")
    start = raw.index(expected)
    mutant = raw[:start] + mutation["replacement"].encode("ascii") + raw[start + len(expected):]
    if mutant == raw and not allow_identical:
        raise ValueError(f"{spec['id']}::{mutation['id']} produced identical mutant")
    return mutant


def without_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    return "\n\n".join(paragraph for paragraph in paragraphs if not paragraph.startswith(prefix))


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_id = {row["id"]: row for row in updated["requirements"]}
    covered = {}
    for spec in all_specs():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for rule, facets in covered.items():
        if rule not in by_id or not facets <= set(by_id[rule]["facets"]):
            raise ValueError(f"selected {rule} facet definitions changed")
        for facet in facets:
            by_id[rule].get("pending", {}).pop(facet, None)
        by_id[rule]["oracle"] = owned_paragraph(by_id[rule].get("oracle", ""), ORACLE_PREFIX, ORACLE)
        by_id[rule]["oracle_limitation"] = owned_paragraph(
            by_id[rule].get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    for rule, pending in RESTORED_PENDING.items():
        owner = by_id[rule]
        owner.setdefault("pending", {}).update(pending)
        owner["oracle"] = without_owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX)
        owner["oracle_limitation"] = without_owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIX)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    before, rest = text.split(begin)
    _, after = rest.split(end)
    facets = sorted({facet for spec in all_specs() for facet in spec["facets"]})
    summary = (SUMMARY_BEGIN + "\n"
               "## Procedure reference fixture packet\n\n"
               f"This packet generates {len(RUNTIME_CASES)} runtime fixtures, {len(DIAGNOSTIC_CASES)} "
               f"diagnostic negatives, and {len(CONTROLS)} run controls for selected 15.5.1 facets. "
               "Runtime cases use exact integer sentinels and feature mutations; diagnostic cases require "
               "only a located error at the violating line and reject ICE/not-implemented/internal failures.\n\n"
               "Covered facets: " + ", ".join(f"`{facet}`" for facet in facets) + ".\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale procedure-reference fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def compiler_flag(compiler, standard):
    name = Path(str(compiler)).name.lower()
    return f"--std={standard}" if "lfortran" in name else f"-std={standard}"


def compile_and_run(source, compiler, standard, work):
    work.mkdir(parents=True, exist_ok=True)
    src = work / "source.f90"
    exe = work / "program"
    src.write_bytes(source if isinstance(source, bytes) else source.encode("ascii"))
    compile_result = subprocess.run(
        [str(compiler), compiler_flag(compiler, standard), "source.f90", "-o", "program"], cwd=work,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_result.returncode != 0:
        return dict(phase="compile", returncode=compile_result.returncode,
                    stdout=compile_result.stdout, stderr=compile_result.stderr)
    run_result = subprocess.run([str(exe.resolve())], cwd=work, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return dict(phase="run", returncode=run_result.returncode,
                stdout=run_result.stdout, stderr=run_result.stderr)


def mutation_matrix(root, compiler, standard, sabotage_first=False):
    root = Path(root)
    specs = runtime_specs(root)
    workspace = root / ".procedure_reference_15_5_1_mutations" / sha((str(compiler) + standard).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    rows, survivors, compile_failures, parent_failures = [], [], [], []
    first = True
    try:
        for case_index, spec in enumerate(specs, 1):
            case_dir = workspace / f"{case_index:03d}_{spec['variant']}"
            parent = compile_and_run(spec["source"], compiler, standard, case_dir / "parent")
            if parent["phase"] != "run" or parent["returncode"] != 0 or parent["stdout"] != spec["stdout"] or parent["stderr"] != "":
                parent_failures.append(dict(case=spec["id"], **parent))
                continue
            for mut_index, plan in enumerate(spec["mutations"], 1):
                active = copy.deepcopy(plan)
                allow_identical = False
                if sabotage_first and first:
                    active["replacement"] = active["expected"]
                    active["id"] += "__identity_sabotage"
                    allow_identical = True
                    first = False
                mutant = mutated_source(spec, active, allow_identical=allow_identical)
                result = compile_and_run(mutant, compiler, standard, case_dir / f"mut_{mut_index:03d}")
                row = dict(case=spec["id"], mutation=active["id"], facet=active["facet"], **result)
                rows.append(row)
                if result["phase"] != "run":
                    compile_failures.append(row)
                elif result["returncode"] == 0 and result["stdout"] == spec["stdout"] and result["stderr"] == "":
                    survivors.append(row)
        return dict(rows=rows, survivors=survivors, compile_failures=compile_failures,
                    parent_failures=parent_failures)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_mutation_check(root, compiler, standard):
    matrix = mutation_matrix(root, compiler, standard)
    if matrix["parent_failures"] or matrix["compile_failures"] or matrix["survivors"]:
        print(json.dumps(matrix, indent=2))
        raise SystemExit(1)
    print(f"Mutation check passed: {len(matrix['rows'])}/{len(matrix['rows'])} mutants failed on {compiler}.")


def prove_non_vacuous(root, compiler, standard):
    matrix = mutation_matrix(root, compiler, standard, sabotage_first=True)
    if not matrix["survivors"]:
        print(json.dumps(matrix, indent=2))
        raise SystemExit("identity sabotage was not reported as a surviving mutant")
    survivor = matrix["survivors"][0]
    print(f"Non-vacuity proof passed: {survivor['case']}::{survivor['mutation']} survived on {compiler}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--prove-non-vacuous", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--standard", default="f2023")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.mutation_check, args.prove_non_vacuous))) > 1:
        parser.error("--check, --sync-catalogue, --mutation-check and --prove-non-vacuous are separate operations")
    if args.mutation_check or args.prove_non_vacuous:
        if not args.compiler:
            parser.error("--compiler is required for mutation modes")
        if args.mutation_check:
            run_mutation_check(args.root, args.compiler, args.standard)
        else:
            prove_non_vacuous(args.root, args.compiler, args.standard)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    facets = {facet for spec in specs.values() for facet in spec["facets"]}
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} procedure-reference cases covering {len(facets)} facets.")


if __name__ == "__main__":
    main()
