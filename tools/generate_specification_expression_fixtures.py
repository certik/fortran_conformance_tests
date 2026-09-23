#!/usr/bin/env python3
"""Specification-expression positive controls with permanent feature mutations."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SECTION = "10.1.11"
CATALOGUE = "doc/catalogues/specification_expression_10_1_11.json"
VIEW = "doc/fortran_2023_10_1_11.md"
PREFIX = "specification_expression_"
SUMMARY_BEGIN = "<!-- BEGIN SPECIFICATION EXPRESSION FIXTURES -->"
SUMMARY_END = "<!-- END SPECIFICATION EXPRESSION FIXTURES -->"
BUILD_ROOT = ".specification_expression_mutation_check"

SELECTED = {
    "S10.1.11-001": ("constant-expression-default", "subprogram-specification-part-exception"),
    "R1029": ("scalar-int-expression-form",),
    "C1011": (
        "intrinsic-operation", "constant-primary", "dummy-designator-primary",
        "common-designator-primary", "host-use-designator-primary",
        "specification-inquiry-restricted-argument", "specification-inquiry-variable-argument",
        "constant-specification-inquiry-primary", "standard-intrinsic-primary",
        "specification-function-primary", "parenthesized-restricted-expression",
        "restricted-subscripts-and-type-params",
    ),
    "S10.1.11-002": ("intrinsic-inquiry-excluding-present",),
    "S10.1.11-003": ("pure-function", "nonstandard-intrinsic", "no-dummy-procedure-argument"),
    "S10.1.11-005": ("host-use-associated-typing",),
}

ORACLE_PREFIXES = {
    "S10.1.11-001": "Fixture packet batch171 p1 positive controls: ",
    "R1029": "Fixture packet batch171 R1029 positive control: ",
    "C1011": "Fixture packet batch171 C1011 restricted-expression controls: ",
    "S10.1.11-002": "Fixture packet batch171 p3 inquiry control: ",
    "S10.1.11-003": "Fixture packet batch171 p4 specification-function control: ",
    "S10.1.11-005": "Fixture packet batch171 p6 association typing control: ",
}

LIMIT_PREFIXES = {key: value.replace("control", "boundaries") for key, value in ORACLE_PREFIXES.items()}

ORACLES = {
    "S10.1.11-001": ORACLE_PREFIXES["S10.1.11-001"] + (
        "one complete positive-control program declares a main-program explicit-shape array with prior "
        "INTEGER PARAMETER k=7, proving the default specification-expression context is satisfied by a "
        "constant expression, and separately calls a subprogram twice with n=7 then n=4 where INTEGER :: "
        "dynamic(n) is admitted in the subprogram specification part. Runtime SIZE checks use independent "
        "literal expected values and an exact completion line. Feature mutants replace both bounds by fixed1 "
        "or change the actual argument while leaving the oracle unchanged, so a no-op or non-capturing bound "
        "cannot pass."
    ),
    "R1029": ORACLE_PREFIXES["R1029"] + (
        "one complete positive-control program declares INTEGER :: a(2*3+1), a scalar integer expression, "
        "and checks SIZE(a)==7 before exact completion. Feature mutants replace the scalar expression by1 "
        "or by 2*3+2; both remain scalar integer expressions and fail only the runtime oracle."
    ),
    "C1011": ORACLE_PREFIXES["C1011"] + (
        "eight complete positive-control programs exercise thirteen selected restricted-expression primary "
        "and operation routes in contexts that require specification expressions. They observe: ((n+1)) "
        "using intrinsic integer addition, a literal constant primary and a nonoptional non-OUT dummy; a "
        "COMMON base object; both USE- and host-associated base objects; SIZE and LEN specification inquiries "
        "of nonoptional dummies; SIZE of a constant explicit-shape object as a constant specification inquiry; "
        "MAX(n,1) as a standard intrinsic; a PURE module function add_two(n) as a specification-function "
        "primary; and restricted subscript, substring-bound and CHARACTER length type-parameter values. "
        "Each runtime check uses independent expected values, including two distinct dynamic activations when "
        "the bound source can vary. Feature mutants replace the selected expression by fixed1 or by a load-"
        "bearing sibling expression/input, and every mutant remains conforming and fails at runtime."
    ),
    "S10.1.11-002": ORACLE_PREFIXES["S10.1.11-002"] + (
        "one complete effect program uses intrinsic inquiry functions SIZE and LEN, excluding PRESENT, as "
        "specification inquiries in automatic array and character declarations. Calls with lengths 7/5 and "
        "4/3 prove the declarations depend on the inquired dummy properties. Feature mutants replace the "
        "inquiries by fixed1 or add one to each inquiry result; both compile and fail the runtime guards."
    ),
    "S10.1.11-003": ORACLE_PREFIXES["S10.1.11-003"] + (
        "one complete effect program uses a PURE module function width with only an INTEGER dummy argument "
        "as a specification function in INTEGER :: a(width(n)). Calls with n=4 and n=7 check extents 7 and10. "
        "The function is non-internal and nonintrinsic, but this packet claims the pure-function, nonstandard-intrinsic and "
        "no-dummy-procedure-argument facets. Feature mutants remove the call or add one to the function result "
        "and fail at runtime after successful compilation."
    ),
    "S10.1.11-005": ORACLE_PREFIXES["S10.1.11-005"] + (
        "one complete positive-control program types use_n by USE association and host_n by host association "
        "before each appears in a specification expression. The program sets them to 8 and4, declares local "
        "arrays with those bounds in their associated scopes, and checks the extents independently. Mutants "
        "replace the associated bounds by fixed1 or alter the associated value while preserving the checks."
    ),
}

LIMITATIONS = {
    "S10.1.11-001": LIMIT_PREFIXES["S10.1.11-001"] + (
        "only the constant-expression-default and subprogram-specification-part-exception facets are covered. "
        "No diagnostic, interface body, BLOCK construct, derived type definition or FUNCTION statement type-spec "
        "case is claimed. Array-bound ownership remains with its declaration rules; this packet observes only "
        "that the p1 contexts admit the specification expression."
    ),
    "R1029": LIMIT_PREFIXES["R1029"] + (
        "only a valid scalar integer expression form is covered. Noninteger and nonscalar boundaries remain "
        "pending because their required diagnoses must be isolated under the exact owning context."
    ),
    "C1011": LIMIT_PREFIXES["C1011"] + (
        "only the thirteen selected positive-control facets are covered. PRESENT, array constructors, structure, "
        "enum and enumeration constructors, IEEE/ISO_C transformational functions, derived-type parameters, "
        "ac-do-variable primaries and all excluded-primary diagnostics remain pending. No negative is filed under "
        "10.1.11 unless C1011 itself, not a use-site rule, requires the diagnosis. COMMON obsolescence warnings "
        "are not part of the oracle."
    ),
    "S10.1.11-002": LIMIT_PREFIXES["S10.1.11-002"] + (
        "only ordinary intrinsic inquiry functions SIZE and LEN are covered. Type-parameter, IEEE, C_SIZEOF and "
        "compiler-version/options inquiries, and the PRESENT contrast, remain pending. No processor-dependent "
        "inquiry result or message text is compared."
    ),
    "S10.1.11-003": LIMIT_PREFIXES["S10.1.11-003"] + (
        "only positive classification evidence for a pure nonintrinsic function without a dummy procedure argument is covered. "
        "Not-internal-function, not-statement-function and impure-function-boundary facets "
        "remain pending, and no diagnostic is attributed to the p4 definition alone."
    ),
    "S10.1.11-005": LIMIT_PREFIXES["S10.1.11-005"] + (
        "only host/use associated typing is covered. Previous declaration, implicit typing, subsequent "
        "confirmation and derived-type-prior-definition facets remain pending. Association semantics beyond the "
        "typing source are owned elsewhere."
    ),
}


def identifier(variant):
    return "S10_1_11_valid__specification_expression_" + variant


def manifest(spec):
    return dict(
        schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        link=dict(driver="fortran", objects=["source.o"], output="program"),
        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"mutation span is not unique: {old!r}")
    return source.replace(old, new, 1)


def apply_pairs(source, pairs):
    result = source
    for old, new in pairs:
        result = replace_once(result, old, new)
    return result


def make_case(variant, rule, facets, evidence, source, completion, mutation_plans, derivation):
    spec = dict(
        id=identifier(variant), variant=variant, rule=rule, facets=list(facets), evidence=evidence,
        source=source, completion=completion, mutations=[], derivation=derivation)
    for name, pairs, rationale in mutation_plans:
        mutated = apply_pairs(source, pairs)
        if mutated == source:
            raise ValueError("empty mutation: " + name)
        spec["mutations"].append(dict(id=name, replacements=pairs, source=mutated, rationale=rationale))
    return spec


def source_specs():
    specs = []
    completion = "SPECEXPR P1 CONTEXTS OK\n"
    source = """program specification_expression_p1_contexts
  implicit none
  integer, parameter :: k=7
  integer :: a(k)
  if (size(a) /= 7) error stop 'SEP1:constant'
  call observe(7, 7)
  call observe(4, 4)
  write(*,'(a)') 'SPECEXPR P1 CONTEXTS OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: dynamic(n)
    if (size(dynamic) /= expected) error stop 'SEP1:subprogram'
  end subroutine observe
end program specification_expression_p1_contexts
"""
    specs.append(make_case(
        "p1_contexts", "S10.1.11-001",
        ["constant-expression-default", "subprogram-specification-part-exception"], "positive-control",
        source, completion,
        [
            ("remove-bounds", [("  integer :: a(k)\n", "  integer :: a(1)\n"),
                               ("    integer :: dynamic(n)\n", "    integer :: dynamic(1)\n")],
             "replace the admitted specification expressions by fixed extent 1"),
            ("changed-dummy-argument", [("  call observe(7, 7)\n", "  call observe(5, 7)\n")],
             "change the dummy argument value while retaining the independent expected size"),
        ],
        "10.1.11 p1 admits constant expressions generally and nonconstant specification expressions in a subprogram specification part."))

    completion = "SPECEXPR R1029 SCALAR OK\n"
    source = """program specification_expression_r1029_scalar
  implicit none
  integer :: a(2*3+1)
  if (size(a) /= 7) error stop 'SER1029:scalar'
  write(*,'(a)') 'SPECEXPR R1029 SCALAR OK'
end program specification_expression_r1029_scalar
"""
    specs.append(make_case(
        "r1029_scalar", "R1029", ["scalar-int-expression-form"], "positive-control", source, completion,
        [
            ("remove-scalar-expression", [("  integer :: a(2*3+1)\n", "  integer :: a(1)\n")],
             "replace the scalar integer expression by fixed extent 1"),
            ("sibling-scalar-expression", [("  integer :: a(2*3+1)\n", "  integer :: a(2*3+2)\n")],
             "substitute another scalar integer expression with a distinct value"),
        ],
        "10.1.11 R1029 defines specification-expr as scalar-int-expr; 2*3+1 is scalar integer."))

    completion = "SPECEXPR C1011 INTRINSIC DUMMY OK\n"
    source = """program specification_expression_c1011_intrinsic_dummy
  implicit none
  call observe(6, 7)
  call observe(3, 4)
  write(*,'(a)') 'SPECEXPR C1011 INTRINSIC DUMMY OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a((n+1))
    if (size(a) /= expected) error stop 'SEC1011:intrinsic-dummy'
  end subroutine observe
end program specification_expression_c1011_intrinsic_dummy
"""
    specs.append(make_case(
        "c1011_intrinsic_dummy", "C1011",
        ["intrinsic-operation", "constant-primary", "dummy-designator-primary",
         "parenthesized-restricted-expression"], "positive-control", source, completion,
        [
            ("remove-dummy-expression", [("    integer :: a((n+1))\n", "    integer :: a(1)\n")],
             "replace the dummy-dependent parenthesized expression by fixed extent 1"),
            ("sibling-intrinsic-operation", [("    integer :: a((n+1))\n", "    integer :: a((n+2))\n")],
             "substitute a different intrinsic addition expression"),
        ],
        "10.1.11 C1011/p2 permits intrinsic operations, constants, eligible dummy designators and parenthesized restricted expressions."))

    completion = "SPECEXPR C1011 COMMON OK\n"
    source = """program specification_expression_c1011_common
  implicit none
  integer :: n_common
  common /specblk/ n_common
  n_common=5
  call observe(5)
  n_common=2
  call observe(2)
  write(*,'(a)') 'SPECEXPR C1011 COMMON OK'
contains
  subroutine observe(expected)
    integer, intent(in) :: expected
    integer :: n_common
    common /specblk/ n_common
    integer :: a(n_common)
    if (size(a) /= expected) error stop 'SEC1011:common'
  end subroutine observe
end program specification_expression_c1011_common
"""
    specs.append(make_case(
        "c1011_common", "C1011", ["common-designator-primary"], "positive-control", source, completion,
        [
            ("remove-common-bound", [("    integer :: a(n_common)\n", "    integer :: a(1)\n")],
             "replace the COMMON-base designator by fixed extent 1"),
            ("changed-common-value", [("  n_common=5\n  call observe(5)\n", "  n_common=6\n  call observe(5)\n")],
             "change the COMMON value while retaining the independent expected size"),
        ],
        "10.1.11 C1011/p2(3) permits object designators whose base object is in a common block."))

    completion = "SPECEXPR C1011 HOST USE OK\n"
    source = """module specification_expression_provider
  implicit none
  integer :: use_n
end module specification_expression_provider
module specification_expression_host_scope
  implicit none
  integer :: host_n
contains
  subroutine observe_host(expected)
    integer, intent(in) :: expected
    integer :: a(host_n)
    if (size(a) /= expected) error stop 'SEC1011:host'
  end subroutine observe_host
end module specification_expression_host_scope
program specification_expression_c1011_host_use
  use specification_expression_provider, only: use_n
  use specification_expression_host_scope, only: host_n, observe_host
  implicit none
  use_n=8
  call observe_use(8)
  host_n=4
  call observe_host(4)
  write(*,'(a)') 'SPECEXPR C1011 HOST USE OK'
contains
  subroutine observe_use(expected)
    use specification_expression_provider, only: use_n
    integer, intent(in) :: expected
    integer :: a(use_n)
    if (size(a) /= expected) error stop 'SEC1011:use'
  end subroutine observe_use
end program specification_expression_c1011_host_use
"""
    specs.append(make_case(
        "c1011_host_use", "C1011", ["host-use-designator-primary"], "positive-control", source, completion,
        [
            ("remove-associated-bounds", [("    integer :: a(host_n)\n", "    integer :: a(1)\n"),
                                          ("    integer :: a(use_n)\n", "    integer :: a(1)\n")],
             "replace both associated-object bounds by fixed extent 1"),
            ("changed-use-value", [("  use_n=8\n  call observe_use(8)\n", "  use_n=6\n  call observe_use(8)\n")],
             "change the use-associated value while retaining the expected size"),
        ],
        "10.1.11 C1011/p2(4) permits object designators made accessible by use or host association."))

    completion = "SPECEXPR C1011 INQUIRIES OK\n"
    source = """program specification_expression_c1011_inquiries
  implicit none
  call observe([1,2,3,4,5,6,7], 'abcde', 7, 5)
  call observe([1,2,3,4], 'xyz', 4, 3)
  write(*,'(a)') 'SPECEXPR C1011 INQUIRIES OK'
contains
  subroutine observe(vals, word, expected_count, expected_len)
    integer, intent(in) :: vals(:), expected_count, expected_len
    character(len=*), intent(in) :: word
    integer :: a(size(vals,1))
    character(len=len(word)) :: copy
    if (size(a) /= expected_count) error stop 'SEC1011:size-inquiry'
    if (len(copy) /= expected_len) error stop 'SEC1011:len-inquiry'
  end subroutine observe
end program specification_expression_c1011_inquiries
"""
    specs.append(make_case(
        "c1011_inquiries", "C1011",
        ["specification-inquiry-restricted-argument", "specification-inquiry-variable-argument"],
        "positive-control", source, completion,
        [
            ("remove-inquiries", [("    integer :: a(size(vals,1))\n", "    integer :: a(1)\n"),
                                  ("    character(len=len(word)) :: copy\n", "    character(len=1) :: copy\n")],
             "replace both inquiry results by fixed extent/length 1"),
            ("sibling-inquiry-values", [("    integer :: a(size(vals,1))\n", "    integer :: a(size(vals,1)+1)\n"),
                                        ("    character(len=len(word)) :: copy\n", "    character(len=len(word)+1) :: copy\n")],
             "substitute restricted inquiry expressions with distinct values"),
        ],
        "10.1.11 C1011/p2(9) permits specification inquiries with restricted or nonoptional variable arguments."))

    completion = "SPECEXPR C1011 CONSTANT INQUIRY OK\n"
    source = """program specification_expression_c1011_constant_inquiry
  implicit none
  integer, parameter :: fixed(7)=[1,2,3,4,5,6,7]
  integer :: a(size(fixed))
  if (size(a) /= 7) error stop 'SEC1011:constant-inquiry'
  write(*,'(a)') 'SPECEXPR C1011 CONSTANT INQUIRY OK'
end program specification_expression_c1011_constant_inquiry
"""
    specs.append(make_case(
        "c1011_constant_inquiry", "C1011", ["constant-specification-inquiry-primary"],
        "positive-control", source, completion,
        [
            ("remove-constant-inquiry", [("  integer :: a(size(fixed))\n", "  integer :: a(1)\n")],
             "replace the constant specification inquiry by fixed extent 1"),
            ("sibling-constant-inquiry", [("  integer :: a(size(fixed))\n", "  integer :: a(size(fixed)-1)\n")],
             "substitute a distinct constant expression derived from the same inquiry"),
        ],
        "10.1.11 C1011/p2(10) permits a specification inquiry that is a constant expression."))

    completion = "SPECEXPR C1011 STANDARD INTRINSIC OK\n"
    source = """program specification_expression_c1011_standard_intrinsic
  implicit none
  call observe(7, 7)
  call observe(0, 1)
  write(*,'(a)') 'SPECEXPR C1011 STANDARD INTRINSIC OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a(max(n,1))
    if (size(a) /= expected) error stop 'SEC1011:max'
  end subroutine observe
end program specification_expression_c1011_standard_intrinsic
"""
    specs.append(make_case(
        "c1011_standard_intrinsic", "C1011", ["standard-intrinsic-primary"],
        "positive-control", source, completion,
        [
            ("remove-standard-intrinsic", [("    integer :: a(max(n,1))\n", "    integer :: a(1)\n")],
             "replace MAX by fixed extent 1"),
            ("sibling-standard-intrinsic", [("    integer :: a(max(n,1))\n", "    integer :: a(min(n,1))\n")],
             "substitute MIN for MAX, a load-bearing standard intrinsic change"),
        ],
        "10.1.11 C1011/p2(12) permits standard intrinsic function references with restricted arguments."))

    completion = "SPECEXPR C1011 SPEC FUNCTION OK\n"
    source = """module specification_expression_c1011_functions
  implicit none
contains
  pure integer function add_two(i)
    integer, intent(in) :: i
    add_two=i+2
  end function add_two
end module specification_expression_c1011_functions
program specification_expression_c1011_spec_function
  use specification_expression_c1011_functions, only: add_two
  implicit none
  call observe(5, 7)
  call observe(2, 4)
  write(*,'(a)') 'SPECEXPR C1011 SPEC FUNCTION OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a(add_two(n))
    if (size(a) /= expected) error stop 'SEC1011:spec-function'
  end subroutine observe
end program specification_expression_c1011_spec_function
"""
    specs.append(make_case(
        "c1011_spec_function", "C1011", ["specification-function-primary"],
        "positive-control", source, completion,
        [
            ("remove-specification-function", [("    integer :: a(add_two(n))\n", "    integer :: a(n)\n")],
             "remove the specification-function primary from the bound"),
            ("sibling-specification-function-value", [("    integer :: a(add_two(n))\n", "    integer :: a(add_two(n)+1)\n")],
             "substitute a distinct restricted expression using the same function"),
        ],
        "10.1.11 C1011/p2(14) permits specification-function references with restricted arguments."))

    completion = "SPECEXPR C1011 SUBSCRIPTS TYPEPARAMS OK\n"
    source = """program specification_expression_c1011_subscripts_typeparams
  implicit none
  call observe(2, 'abzz', 4)
  call observe(3, 'abczz', 7)
  write(*,'(a)') 'SPECEXPR C1011 SUBSCRIPTS TYPEPARAMS OK'
contains
  subroutine observe(n, text, expected_size)
    integer, intent(in) :: n, expected_size
    character(len=*), intent(in) :: text
    integer, parameter :: table(4)=[2,4,7,9]
    character(len=n) :: word
    integer :: a(table(n-1)+len(text(1:n)))
    if (len(word) /= n) error stop 'SEC1011:type-param'
    if (size(a) /= expected_size) error stop 'SEC1011:subscript-substring'
  end subroutine observe
end program specification_expression_c1011_subscripts_typeparams
"""
    specs.append(make_case(
        "c1011_subscripts_typeparams", "C1011", ["restricted-subscripts-and-type-params"],
        "positive-control", source, completion,
        [
            ("remove-restricted-subexpressions", [("    character(len=n) :: word\n", "    character(len=1) :: word\n"),
                                                 ("    integer :: a(table(n-1)+len(text(1:n)))\n", "    integer :: a(1)\n")],
             "replace type-parameter, subscript and substring-bound uses by fixed 1"),
            ("sibling-subscript-substring", [("    integer :: a(table(n-1)+len(text(1:n)))\n", "    integer :: a(table(1)+len(text(1:1)))\n")],
             "substitute restricted subscript and substring bounds with a distinct value"),
        ],
        "10.1.11 C1011 final sentence requires subscripts, substring bounds and type parameter values to be restricted expressions."))

    completion = "SPECEXPR P3 INTRINSIC INQUIRY OK\n"
    source = """program specification_expression_p3_intrinsic_inquiry
  implicit none
  call observe([1,2,3,4,5,6,7], 'abcde', 7, 5)
  call observe([1,2,3,4], 'xyz', 4, 3)
  write(*,'(a)') 'SPECEXPR P3 INTRINSIC INQUIRY OK'
contains
  subroutine observe(vals, word, expected_count, expected_len)
    integer, intent(in) :: vals(:), expected_count, expected_len
    character(len=*), intent(in) :: word
    integer :: a(size(vals,1))
    character(len=len(word)) :: copy
    if (size(a) /= expected_count) error stop 'SEP3:size'
    if (len(copy) /= expected_len) error stop 'SEP3:len'
  end subroutine observe
end program specification_expression_p3_intrinsic_inquiry
"""
    specs.append(make_case(
        "p3_intrinsic_inquiry", "S10.1.11-002", ["intrinsic-inquiry-excluding-present"],
        "effect", source, completion,
        [
            ("remove-inquiry-functions", [("    integer :: a(size(vals,1))\n", "    integer :: a(1)\n"),
                                         ("    character(len=len(word)) :: copy\n", "    character(len=1) :: copy\n")],
             "replace SIZE and LEN by fixed extent/length 1"),
            ("sibling-inquiry-results", [("    integer :: a(size(vals,1))\n", "    integer :: a(size(vals,1)+1)\n"),
                                        ("    character(len=len(word)) :: copy\n", "    character(len=len(word)+1) :: copy\n")],
             "substitute distinct inquiry expressions"),
        ],
        "10.1.11 p3 defines specification inquiry to include intrinsic inquiry functions other than PRESENT; SIZE and LEN are used."))

    completion = "SPECEXPR P4 SPEC FUNCTION OK\n"
    source = """module specification_expression_p4_functions
  implicit none
contains
  pure integer function width(i)
    integer, intent(in) :: i
    width=i+3
  end function width
end module specification_expression_p4_functions
program specification_expression_p4_spec_function
  use specification_expression_p4_functions, only: width
  implicit none
  call observe(4, 7)
  call observe(7, 10)
  write(*,'(a)') 'SPECEXPR P4 SPEC FUNCTION OK'
contains
  subroutine observe(n, expected)
    integer, intent(in) :: n, expected
    integer :: a(width(n))
    if (size(a) /= expected) error stop 'SEP4:spec-function'
  end subroutine observe
end program specification_expression_p4_spec_function
"""
    specs.append(make_case(
        "p4_spec_function", "S10.1.11-003", ["pure-function", "nonstandard-intrinsic", "no-dummy-procedure-argument"],
        "effect", source, completion,
        [
            ("remove-pure-function", [("    integer :: a(width(n))\n", "    integer :: a(n)\n")],
             "remove the pure function reference from the specification expression"),
            ("sibling-function-value", [("    integer :: a(width(n))\n", "    integer :: a(width(n)+1)\n")],
             "substitute a distinct value still using the pure function"),
        ],
        "10.1.11 p4 defines a specification function as pure and without a dummy procedure argument; width has only an INTEGER dummy."))

    completion = "SPECEXPR P6 ASSOCIATION TYPING OK\n"
    source = """module specification_expression_p6_provider
  implicit none
  integer :: use_n
end module specification_expression_p6_provider
module specification_expression_p6_host_scope
  implicit none
  integer :: host_n
contains
  subroutine observe_host(expected)
    integer, intent(in) :: expected
    integer :: a(host_n)
    if (size(a) /= expected) error stop 'SEP6:host-typing'
  end subroutine observe_host
end module specification_expression_p6_host_scope
program specification_expression_p6_association_typing
  use specification_expression_p6_provider, only: use_n
  use specification_expression_p6_host_scope, only: host_n, observe_host
  implicit none
  use_n=8
  call observe_use(8)
  host_n=4
  call observe_host(4)
  write(*,'(a)') 'SPECEXPR P6 ASSOCIATION TYPING OK'
contains
  subroutine observe_use(expected)
    use specification_expression_p6_provider, only: use_n
    integer, intent(in) :: expected
    integer :: a(use_n)
    if (size(a) /= expected) error stop 'SEP6:use-typing'
  end subroutine observe_use
end program specification_expression_p6_association_typing
"""
    specs.append(make_case(
        "p6_association_typing", "S10.1.11-005", ["host-use-associated-typing"],
        "positive-control", source, completion,
        [
            ("remove-associated-typing-bounds", [("    integer :: a(host_n)\n", "    integer :: a(1)\n"),
                                                ("    integer :: a(use_n)\n", "    integer :: a(1)\n")],
             "replace associated variables in specification expressions by fixed extent 1"),
            ("changed-associated-value", [("  use_n=8\n  call observe_use(8)\n", "  use_n=6\n  call observe_use(8)\n")],
             "change the associated value while retaining the independent expected size"),
        ],
        "10.1.11 p6 permits variables in specification expressions to be typed by host or use association."))

    return {spec["id"]: spec for spec in specs}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["variant"])
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest(spec)
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(existing, prefix, paragraph):
    parts = existing.split("\n\n") if existing else []
    matches = [i for i, part in enumerate(parts) if part.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph: " + prefix)
    if matches:
        parts[matches[0]] = paragraph
    else:
        parts.append(paragraph)
    return "\n\n".join(part for part in parts if part)


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_id = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        req = by_id[rule]
        if not set(facets) <= set(req["facets"]):
            raise ValueError("selected facets are absent from " + rule)
        for facet in facets:
            req["pending"].pop(facet, None)
        req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        req["oracle_limitation"] = owned_paragraph(req.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import Registry, render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("specification-expression generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    registry = Registry(root)
    registry.catalogues[SECTION] = catalogue
    before = (
        "# Fortran 2023: 10.1.11 Specification expression\n\n"
        f"**Source review: {registry.catalogue_review_state(SECTION)}.** The original source-only catalogue is now "
        "supplemented by batch171 positive-control/effect fixtures for selected facets. Fixture, source-review and "
        "inventory adjudications remain separate; no baseline or review approval is renewed here.\n\n")
    rendered = "\n".join(render_requirement(row) for row in catalogue["requirements"])
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Batch171 specification-expression observations\n\n"
        "Thirteen complete f2023 runtime programs cover twenty facets: two p1 context facets, R1029's scalar "
        "integer form, thirteen C1011 restricted-expression routes, one p3 SIZE/LEN inquiry facet, two p4 "
        "specification-function classification facets, and p6 host/use-associated typing. Dynamic cases use "
        "distinguished values such as 7/4, 8/4, 5/2, and 4/7 so changing the source value changes the observed "
        "SIZE or LEN. Every success oracle is an exact completion line after independent SIZE/LEN guards.\n\n"
        "The permanent mutation matrix is generated from complete-parent feature substitutions, not oracle-only "
        "edits. Each fixture has a fixed-1 removal mutant and a load-bearing sibling or changed-input mutant; all "
        "mutants remain conforming and are required to compile and fail at runtime on both the frozen LFortran "
        "target and the gfortran reference. No negative diagnostic is filed in this packet. PRESENT, array "
        "constructors, structure/enum constructors, IEEE/ISO_C transformational functions, derived-type parameters, "
        "ordinary-local and OPTIONAL/INTENT(OUT) exclusion cases, and p7-p9 restrictions remain pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in after or SUMMARY_END in after:
        if after.count(SUMMARY_BEGIN) != 1 or after.count(SUMMARY_END) != 1:
            raise ValueError("specification-expression summary boundaries changed")
        leading, owned = after.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        after = leading + summary + trailing
    else:
        after = after.rstrip() + "\n\n" + summary + "\n"
    return before + begin + "\n\n" + rendered + "\n" + end + after


def compiler_command(compiler, std, source, output):
    compiler = str(compiler)
    if "gfortran" in Path(compiler).name:
        return [compiler, f"-std={std}", str(source), "-o", str(output)]
    return [compiler, f"--std={std}", str(source), "-o", str(output)]


def run_program(executable, cwd=None):
    return subprocess.run([str(executable)], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=20, check=False)


def git_status_snapshot(root):
    checked = subprocess.run(["git", "--no-pager", "status", "--porcelain"], cwd=root,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             timeout=20, check=False)
    if checked.returncode != 0:
        raise RuntimeError("git status failed: " + checked.stderr)
    return checked.stdout


def mutation_check(root=ROOT, compiler=None, std=None, keep=False):
    if not compiler or not std:
        raise ValueError("--mutation-check requires --compiler and --std")
    root = Path(root)
    specs = source_specs()
    build_root = root / BUILD_ROOT / (Path(compiler).name + "_" + std.replace("/", "_"))
    if build_root.exists():
        shutil.rmtree(build_root)
    status_before = None if keep else git_status_snapshot(root)
    failures = []
    try:
        for spec in specs.values():
            parent_dir = build_root / spec["variant"] / "parent"
            parent_dir.mkdir(parents=True, exist_ok=True)
            parent_source = parent_dir / "source.f90"
            parent_source.write_text(spec["source"])
            parent_exe = parent_dir / "program"
            compiled = subprocess.run(compiler_command(compiler, std, Path("source.f90"), Path("program")),
                                      cwd=parent_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                      timeout=30, check=False)
            if compiled.returncode != 0:
                failures.append((spec["variant"], "parent-compile", compiled.stdout + compiled.stderr))
                continue
            ran = run_program(parent_exe, cwd=parent_dir)
            if ran.returncode != 0 or ran.stdout != spec["completion"] or ran.stderr != "":
                failures.append((spec["variant"], "parent-run", ran.stdout + ran.stderr))
                continue
            for mutation in spec["mutations"]:
                work = build_root / spec["variant"] / mutation["id"]
                work.mkdir(parents=True, exist_ok=True)
                source = work / "source.f90"
                source.write_text(mutation["source"])
                exe = work / "program"
                compiled = subprocess.run(compiler_command(compiler, std, Path("source.f90"), Path("program")),
                                          cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                          timeout=30, check=False)
                if compiled.returncode != 0:
                    failures.append((spec["variant"], mutation["id"] + " compile", compiled.stdout + compiled.stderr))
                    continue
                ran = run_program(exe, cwd=work)
                if ran.returncode == 0:
                    failures.append((spec["variant"], mutation["id"] + " survived", ran.stdout + ran.stderr))
        if failures:
            lines = ["mutation check failed:"]
            for variant, phase, output in failures:
                lines.append(f"{variant} {phase}: {output[:600]}")
            raise SystemExit("\n".join(lines))
        return sum(len(spec["mutations"]) for spec in specs.values())
    finally:
        if not keep and build_root.exists():
            shutil.rmtree(build_root)
            try:
                (root / BUILD_ROOT).rmdir()
            except OSError:
                pass
        if status_before is not None:
            status_after = git_status_snapshot(root)
            if status_after != status_before:
                raise SystemExit("mutation check changed git status:\n" + status_after)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_path = root / CATALOGUE
    view_path = root / VIEW
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    actual = {path for path in (root / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()}
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [path.relative_to(root).as_posix() for path in sorted(actual - set(files))]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if view_path.read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale specification-expression fixtures: " + ", ".join(stale))
    else:
        extras = actual - set(files)
        if extras:
            raise ValueError("unexpected specification-expression files: "
                             + ", ".join(path.relative_to(root).as_posix() for path in sorted(extras)))
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            view_path.write_text(view)
    return specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    parser.add_argument("--keep-mutation-work", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_check:
        count = mutation_check(args.root, args.compiler, args.std, args.keep_mutation_work)
        print(f"Mutation-checked {count} specification-expression feature mutants with {args.compiler} ({args.std}).")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    facet_count = sum(len(spec["facets"]) for spec in specs.values())
    mutant_count = sum(len(spec["mutations"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} specification-expression fixtures, "
          f"{facet_count} facets, {mutant_count} feature mutants.")


if __name__ == "__main__":
    main()
