#!/usr/bin/env python3
"""Fixtures for Fortran 2023 expression syntax and semantics 10.1.1-10.1.2.4."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "expressions_10_1_1_10_1_2_4_"
BUILD_ROOT = ".expressions_10_1_1_10_1_2_4_mutation_check"
SUMMARY_BEGIN = "<!-- BEGIN EXPRESSIONS 10.1.1-10.1.2.4 FIXTURES -->"
SUMMARY_END = "<!-- END EXPRESSIONS 10.1.1-10.1.2.4 FIXTURES -->"

CATALOGUES = {
    "10.1.1": "doc/catalogues/expression_semantics_10_1_1.json",
    "10.1.2.1": "doc/catalogues/overall_expression_syntax_10_1_2_1.json",
    "10.1.2.2": "doc/catalogues/primary_10_1_2_2.json",
    "10.1.2.3": "doc/catalogues/conditional_expressions_10_1_2_3.json",
    "10.1.2.4": "doc/catalogues/level_1_expressions_10_1_2_4.json",
}
VIEWS = {
    "10.1.1": "doc/fortran_2023_10_1_1.md",
    "10.1.2.1": "doc/fortran_2023_10_1_2_1.md",
    "10.1.2.2": "doc/fortran_2023_10_1_2_2.md",
    "10.1.2.3": "doc/fortran_2023_10_1_2_3.md",
    "10.1.2.4": "doc/fortran_2023_10_1_2_4.md",
}

EXCLUDES = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal compiler error", "Internal Compiler Error", "ASR verify", "module failed verification",
    "LLVM ERROR", "out of memory", "segmentation fault", "stack trace",
]

SELECTED = {
    "S10.1.1-001": [
        "data-object-reference-expression", "computation-expression",
        "scalar-expression-value", "array-expression-value",
    ],
    "S10.1.1-002": [
        "integer-type-value", "character-length-parameter", "scalar-shape", "array-shape",
    ],
    "S10.1.2.1-001": [
        "operand-operator-parenthesis-form", "scalar-operand", "array-operand",
        "intrinsic-operation", "defined-operation", "nested-expression-operand",
    ],
    "S10.1.2.1-002": [
        "primary-category", "level-1-category", "level-2-category",
        "level-3-category", "level-4-category", "level-5-category",
    ],
    "S10.1.2.1-003": ["recursive-category-definition", "primary-as-simplest-form"],
    "R1001": [
        "literal-constant", "designator", "array-constructor", "structure-constructor",
        "function-reference", "parenthesized-expr", "conditional-expr",
    ],
    "C1002": ["ordinary-designator-control", "assumed-size-element-control", "whole-assumed-size-array-rejected"],
    "C1003": ["ordinary-parenthesized-expression"],
    "S10.1.2.3-001": [
        "primary-classification", "true-arm-selection", "false-arm-selection", "nested-selection",
    ],
    "R1002": [
        "two-arm-form", "chained-guard-form", "scalar-logical-guard",
        "missing-final-colon-rejected", "missing-question-rejected",
    ],
    "C1004": [
        "same-characteristics-control", "declared-type-mismatch-rejected",
        "kind-parameter-mismatch-rejected", "rank-mismatch-rejected", "nested-arm-characteristics",
    ],
    "S10.1.2.4-001": [
        "defined-unary-before-intrinsic", "defined-unary-on-parenthesized-expression",
        "primary-without-defined-unary",
    ],
    "R1003": ["primary-only", "defined-unary-primary", "two-unary-without-parentheses-rejected"],
    "R1004": ["single-letter", "multiple-letters", "digit-in-name-rejected"],
    "C1005": ["sixty-three-letter-control", "sixty-four-letter-rejected", "intrinsic-operator-spelling-rejected", "logical-true-spelling-rejected", "logical-false-spelling-rejected"],
}

ORACLE_PREFIX = "Batch291 expressions runtime/diagnostic fixtures: "
LIMIT_PREFIX = "Batch291 expressions fixture boundaries: "

ORACLE_TEXT = {
    "S10.1.1-001": ORACLE_PREFIX + (
        "one run/effect/f2023 program observes a declared scalar object value 17, the integer computation 2+5=7, "
        "a scalar integer expression value 42, and a rank-one array expression with shape [2] and values [3,5]. "
        "Each assertion has a separate conforming feature mutation changing the referenced object, operation, scalar "
        "literal, or array constructor value. No storage address, evaluation-order, real, or compiler-consensus oracle is used."
    ),
    "S10.1.1-002": ORACLE_PREFIX + (
        "one run/effect/f2023 program directly inquires on expressions: kind(40+2), len('ab'//'cde'), rank(21+1), "
        "and shape([8,13]). The integer kind is compared with kind(1), the character length with 5, scalar rank with "
        "0, and array shape with [2]. Mutations change the expression under inquiry, not a variable assigned from it."
    ),
    "S10.1.2.1-001": ORACLE_PREFIX + (
        "one positive-control program uses parenthesized arithmetic, scalar and array operands, intrinsic multiplication, "
        "a user-defined binary .combine. operator, and nested subexpressions. Literal integer and array oracles make each "
        "form load-bearing while detailed grammar and interpretation remain dependencies of the numbered rules."
    ),
    "S10.1.2.1-002": ORACLE_PREFIX + (
        "one positive-control program gives separate literal observations for primary, level-1 defined unary, level-2 "
        "power, level-3 concatenation, level-4 relation, and level-5 logical categories. Mutations substitute a conforming "
        "sibling expression for the category under observation."
    ),
    "S10.1.2.1-003": ORACLE_PREFIX + (
        "one positive-control program observes ((1+2)*3)==9 and the same primary literal admitted through both arithmetic "
        "and relational contexts. The precedence-ladder facet remains pending because the full ladder is owned by later "
        "numbered rules and not completely covered by this bounded packet."
    ),
    "R1001": ORACLE_PREFIX + (
        "one positive-control program exercises seven R1001 primary alternatives: literal constant, designator, array "
        "constructor, structure constructor, function reference, parenthesized expr, and conditional expr. Each alternative "
        "has a distinct assertion and a feature mutation changing that alternative's source construct."
    ),
    "C1002": ORACLE_PREFIX + (
        "one positive-control program distinguishes a local whole-array designator and an assumed-size element designator; "
        "one diagnostic fixture isolates a whole assumed-size array primary. The C1002 negative is a genuine LFortran "
        "defect case: gfortran diagnoses it, while the frozen LFortran target ICEs instead of reporting the constraint."
    ),
    "C1003": ORACLE_PREFIX + (
        "one positive-control program observes an ordinary parenthesized integer expression. Data-pointer and procedure-"
        "pointer function-reference boundaries remain pending because the frozen LFortran target fails a conforming "
        "parenthesized data-pointer result control during code generation."
    ),
    "S10.1.2.3-001": ORACLE_PREFIX + (
        "one run/effect/f2023 program uses conditional expressions as primaries and side-effecting branch functions to "
        "show that true, false, and chained selections evaluate exactly the chosen branch in the observed single-image cases."
    ),
    "R1002": ORACLE_PREFIX + (
        "three positive controls cover the two-arm form, chained guarded form, and scalar logical guard, while two compile "
        "diagnostic fixtures omit only the final colon or only the question mark. Repairs are the corresponding positive forms."
    ),
    "C1004": ORACLE_PREFIX + (
        "two positive-control programs check scalar INTEGER arms of the same type, kind, and rank plus a chained "
        "same-characteristics form. Three diagnostics isolate declared-type, kind-parameter, and rank mismatches; "
        "the rank negative changes only the false arm from scalar 2 to rank-one [2], and the [2] -> 2 repair runs on both compilers."
    ),
    "S10.1.2.4-001": ORACLE_PREFIX + (
        "one positive-control program defines .u. as 10*x and observes .u.2*3=60, .u.(1+2)=30, and primary 6*2=12. "
        "The values distinguish defined-unary grouping before lower intrinsic levels and the parenthesized operand form."
    ),
    "R1003": ORACLE_PREFIX + (
        "one positive control observes primary-only and defined-unary-primary level-1 forms, and one diagnostic fixture "
        "uses .u. .v. x with valid interfaces so the absence of a primary after the first operator is isolated."
    ),
    "R1004": ORACLE_PREFIX + (
        "one positive control observes single-letter .u. and letters-only .inverse. operators, and one diagnostic fixture "
        "uses the dotted spelling .u1. so the digit-in-name syntax violation is isolated."
    ),
    "C1005": ORACLE_PREFIX + (
        "one positive control uses a generated 63-letter defined unary operator. Four diagnostics isolate 64 letters, "
        "intrinsic .not. spelling, and .true./.false. logical-literal spellings while keeping the dotted-letter syntax otherwise intact."
    ),
}

LIMIT_TEXT = {
    rule: LIMIT_PREFIX + (
        "Only the listed selected facets are represented by batch291 fixtures. Existing source review state, evidence "
        "approval, rollout progress, xfail policy, and unrelated facets are not changed. Remaining pending facets are left "
        "for later packets where this generator does not provide a portable, both-toolchain parent/control."
    ) for rule in SELECTED
}
LIMIT_TEXT["S10.1.1-002"] += " The derived-type-parameter facet is left pending because the frozen LFortran target reports LEN parameters in parameterized derived types as unsupported."
LIMIT_TEXT["R1001"] += " Enum-constructor, enumeration-constructor, type-param-inquiry, type-param-name, and nonprimary-token diagnostics are not claimed."
LIMIT_TEXT["C1002"] += " The whole-assumed-size-array diagnostic is shipped as a genuine LFortran defect: gfortran diagnoses the isolated negative, while the frozen LFortran target ICEs."
LIMIT_TEXT["C1003"] += " The data-pointer and procedure-pointer function-reference facets are not shipped because the required data-pointer control does not pass the target LFortran build."
LIMIT_TEXT["C1004"] += " Array-valued conforming-arm conditionals remain outside this packet; the shipped rank mismatch uses one scalar arm and one rank-one arm solely as a diagnostic negative with scalar repair."
LIMIT_TEXT["C1005"] += " The 64-letter and intrinsic-operator-spelling diagnostics are shipped as genuine LFortran defects: gfortran diagnoses both isolated negatives, while the frozen LFortran target accepts them."


def identifier(variant, rule, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + "_" + kind + "__expressions_10_1_1_10_1_2_4_" + variant


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"mutation span is not unique: {old!r}")
    return source.replace(old, new, 1)


def apply_pairs(source, pairs):
    result = source
    for old, new in pairs:
        result = replace_once(result, old, new)
    return result


def valid_case(variant, rule, facets, evidence, source, completion, mutations, derivation):
    spec = dict(
        id=identifier(variant, rule, "valid"), variant=variant, rule=rule, facets=list(facets), kind="valid",
        evidence=evidence, source=source, completion=completion, mutations=[], derivation=derivation)
    for facet, name, pairs, rationale in mutations:
        if facet not in facets:
            raise ValueError(f"mutation {name} names unowned facet {facet}")
        mutated = apply_pairs(source, pairs)
        spec["mutations"].append(dict(id=name, facet=facet, replacements=pairs, source=mutated, rationale=rationale))
    return spec


def invalid_case(variant, rule, facet, source, line, messages, repair, derivation):
    return dict(
        id=identifier(variant, rule, "invalid"), variant=variant, rule=rule, facets=[facet], kind="invalid",
        evidence="effect", source=source, line=line, messages=list(messages), repair=repair,
        derivation=derivation, mutations=[])


def source_specs():
    specs = {}
    def add(spec):
        if spec["id"] in specs:
            raise ValueError("duplicate spec id " + spec["id"])
        specs[spec["id"]] = spec

    source = """program expr_semantics_representation
  implicit none
  integer :: checks, object_value, computed_value, scalar_value
  integer :: array_value(2)
  checks=0
  object_value = 17
  if (object_value /= 17) error stop 'ESR:object'
  checks=checks+1
  computed_value = 2 + 5
  if (computed_value /= 7) error stop 'ESR:computation'
  checks=checks+1
  scalar_value = 42
  if (scalar_value /= 42) error stop 'ESR:scalar'
  checks=checks+1
  array_value = [3,5]
  if (any(shape(array_value) /= [2])) error stop 'ESR:array-shape'
  if (any(array_value /= [3,5])) error stop 'ESR:array-values'
  checks=checks+1
  if (checks /= 4) error stop 'ESR:checks'
  write(*,'(a)') 'EXPRESSIONS SEMANTICS REPRESENTATION OK'
end program expr_semantics_representation
"""
    add(valid_case("semantics_representation", "S10.1.1-001", SELECTED["S10.1.1-001"], "effect", source,
                   "EXPRESSIONS SEMANTICS REPRESENTATION OK\n", [
        ("data-object-reference-expression", "object-value-source", [("  object_value = 17\n", "  object_value = 18\n")], "change the object value before it is used as an expression"),
        ("computation-expression", "computation-right-operand", [("  computed_value = 2 + 5\n", "  computed_value = 2 + 6\n")], "change one operand of the computation"),
        ("scalar-expression-value", "scalar-expression-literal", [("  scalar_value = 42\n", "  scalar_value = 41\n")], "substitute a distinct scalar expression value"),
        ("array-expression-value", "array-constructor-element", [("  array_value = [3,5]\n", "  array_value = [3,6]\n")], "substitute one element in the array expression"),
    ], "10.1.1 p1 says an expression represents an object reference or computation and has scalar or array value."))

    source = """program expr_value_characteristics
  implicit none
  integer :: checks
  checks=0
  if (kind(40+2) /= kind(1)) error stop 'EVC:integer-kind'
  checks=checks+1
  if (len('ab'//'cde') /= 5) error stop 'EVC:character-len'
  checks=checks+1
  if (rank(21+1) /= 0) error stop 'EVC:scalar-rank'
  checks=checks+1
  if (any(shape([8,13]) /= [2])) error stop 'EVC:array-shape'
  checks=checks+1
  if (checks /= 4) error stop 'EVC:checks'
  write(*,'(a)') 'EXPRESSIONS VALUE CHARACTERISTICS OK'
end program expr_value_characteristics
"""
    add(valid_case("value_characteristics", "S10.1.1-002", SELECTED["S10.1.1-002"], "effect", source,
                   "EXPRESSIONS VALUE CHARACTERISTICS OK\n", [
        ("integer-type-value", "integer-kind-expression", [("kind(40+2)", "kind('x')")], "change the directly inquired expression to noninteger kind"),
        ("character-length-parameter", "character-concat-length", [("'ab'//'cde'", "'ab'//'cd'")], "change a character operand length under direct LEN inquiry"),
        ("scalar-shape", "scalar-rank-expression", [("rank(21+1)", "rank([21+1])")], "change the expression under RANK from scalar to rank one"),
        ("array-shape", "array-shape-expression", [("shape([8,13])", "shape([8,13,21])")], "change the array constructor extent under direct SHAPE inquiry"),
    ], "10.1.1 p1 says evaluation produces a value with type, parameters when appropriate, and shape."))

    source = """module expr_overall_defined_m
  implicit none
  interface operator(.combine.)
    module procedure combine
  end interface
contains
  integer function combine(left, right)
    integer, intent(in) :: left, right
    combine = 70 + left + 2*right
  end function combine
end module expr_overall_defined_m
program expr_overall_forms
  use expr_overall_defined_m
  implicit none
  integer :: checks, left, right, scalar_result
  integer :: a(2), b(2), array_result(2)
  checks=0
  scalar_result = (2+3)
  if (scalar_result /= 5) error stop 'EOF:paren'
  checks=checks+1
  left = 8
  right = 9
  if (left + right /= 17) error stop 'EOF:scalar'
  checks=checks+1
  a = [1,2]
  b = [3,4]
  array_result = a + b
  if (any(array_result /= [4,6])) error stop 'EOF:array'
  checks=checks+1
  if (4 * 5 /= 20) error stop 'EOF:intrinsic'
  checks=checks+1
  if ((3 .combine. 4) /= 81) error stop 'EOF:defined'
  checks=checks+1
  if ((1+2)*(3+4) /= 21) error stop 'EOF:nested'
  checks=checks+1
  if (checks /= 6) error stop 'EOF:checks'
  write(*,'(a)') 'EXPRESSIONS OVERALL FORMS OK'
end program expr_overall_forms
"""
    add(valid_case("overall_forms", "S10.1.2.1-001", SELECTED["S10.1.2.1-001"], "positive-control", source,
                   "EXPRESSIONS OVERALL FORMS OK\n", [
        ("operand-operator-parenthesis-form", "parenthesized-operator-form", [("  scalar_result = (2+3)\n", "  scalar_result = (2+4)\n")], "change an operand inside the parenthesized operation"),
        ("scalar-operand", "scalar-operand-value", [("  right = 9\n", "  right = 10\n")], "change one scalar operand before the scalar expression"),
        ("array-operand", "array-operand-value", [("  b = [3,4]\n", "  b = [3,5]\n")], "change one array operand element"),
        ("intrinsic-operation", "intrinsic-operator-substitution", [("4 * 5", "4 + 5")], "substitute a conforming intrinsic operator"),
        ("defined-operation", "defined-operator-body", [("    combine = 70 + left + 2*right\n", "    combine = 70 + left + right\n")], "change the defined operator function result"),
        ("nested-expression-operand", "nested-expression-operand", [("(1+2)*(3+4)", "(1+2)*(3+5)")], "change an operand inside a nested subexpression"),
    ], "10.1.2.1 p1 forms expressions from operands, operators, parentheses, intrinsic and defined operations."))

    source = """module expr_category_unary_m
  implicit none
  interface operator(.u.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = 10*x
  end function u
end module expr_category_unary_m
program expr_overall_categories
  use expr_category_unary_m
  implicit none
  integer :: checks
  character(len=4) :: word
  checks=0
  if (6 /= 6) error stop 'EOC:primary'
  checks=checks+1
  if (.u. 5 /= 50) error stop 'EOC:level1'
  checks=checks+1
  if (2**3 /= 8) error stop 'EOC:level2'
  checks=checks+1
  word = 'ab'//'cd'
  if (len(word) /= 4) error stop 'EOC:level3-len'
  if (word /= 'abcd') error stop 'EOC:level3'
  checks=checks+1
  if (.not. (9 > 4)) error stop 'EOC:level4'
  checks=checks+1
  if (.not. (.true. .and. .true.)) error stop 'EOC:level5'
  checks=checks+1
  if (checks /= 6) error stop 'EOC:checks'
  write(*,'(a)') 'EXPRESSIONS OVERALL CATEGORIES OK'
end program expr_overall_categories
"""
    add(valid_case("overall_categories", "S10.1.2.1-002", SELECTED["S10.1.2.1-002"], "positive-control", source,
                   "EXPRESSIONS OVERALL CATEGORIES OK\n", [
        ("primary-category", "primary-literal", [("if (6 /= 6)", "if (7 /= 6)")], "change the literal primary under observation"),
        ("level-1-category", "level1-defined-unary", [(".u. 5", ".u. 6")], "change the primary operand of the level-1 expression"),
        ("level-2-category", "level2-power", [("2**3", "2**4")], "change the level-2 power expression"),
        ("level-3-category", "level3-concat", [("'ab'//'cd'", "'ab'//'ce'")], "change the concatenation expression"),
        ("level-4-category", "level4-relation", [("9 > 4", "9 < 4")], "substitute the relational operator"),
        ("level-5-category", "level5-logical", [(".true. .and. .true.", ".true. .and. .false.")], "change one logical operand in the level-5 expression"),
    ], "10.1.2.1 p2 names primary and level-1 through level-5 expression categories."))

    source = """program expr_overall_recursive_primary
  implicit none
  integer :: checks, primary_value
  checks=0
  if (((1+2)*3) /= 9) error stop 'EOR:recursive'
  checks=checks+1
  primary_value = 6
  if (primary_value + 4 /= 10) error stop 'EOR:primary-add'
  if (.not. (primary_value == 6)) error stop 'EOR:primary-relation'
  checks=checks+1
  if (checks /= 2) error stop 'EOR:checks'
  write(*,'(a)') 'EXPRESSIONS OVERALL RECURSIVE PRIMARY OK'
end program expr_overall_recursive_primary
"""
    add(valid_case("overall_recursive_primary", "S10.1.2.1-003", SELECTED["S10.1.2.1-003"], "positive-control", source,
                   "EXPRESSIONS OVERALL RECURSIVE PRIMARY OK\n", [
        ("recursive-category-definition", "recursive-subexpression", [("((1+2)*3)", "((1+3)*3)")], "change a nested subexpression inside the recursive category chain"),
        ("primary-as-simplest-form", "primary-literal-reuse", [("  primary_value = 6\n", "  primary_value = 7\n")], "change the single primary used through higher contexts"),
    ], "10.1.2.1 p3 says categories are defined in terms of other categories and bottom out at primary."))

    source = """program expr_primary_core_forms
  implicit none
  type :: pair
    integer :: a, b
  end type pair
  integer :: checks, designator_value, array_value(2), function_value, parenthesized_value, conditional_value
  type(pair) :: constructed
  checks=0
  if (19 /= 19) error stop 'EPC:literal'
  checks=checks+1
  designator_value = 23
  if (designator_value /= 23) error stop 'EPC:designator'
  checks=checks+1
  array_value = [3,5]
  if (any(array_value /= [3,5])) error stop 'EPC:array'
  checks=checks+1
  constructed = pair(7,11)
  if (constructed%b /= 11) error stop 'EPC:structure'
  checks=checks+1
  function_value = make_value(4)
  if (function_value /= 29) error stop 'EPC:function'
  checks=checks+1
  parenthesized_value = (2+6)
  if (parenthesized_value /= 8) error stop 'EPC:parenthesized'
  checks=checks+1
  conditional_value = (.true. ? 31 : 41)
  if (conditional_value /= 31) error stop 'EPC:conditional'
  checks=checks+1
  if (checks /= 7) error stop 'EPC:checks'
  write(*,'(a)') 'EXPRESSIONS PRIMARY CORE FORMS OK'
contains
  integer function make_value(x)
    integer, intent(in) :: x
    make_value = 25 + x
  end function make_value
end program expr_primary_core_forms
"""
    add(valid_case("primary_core_forms", "R1001", SELECTED["R1001"], "positive-control", source,
                   "EXPRESSIONS PRIMARY CORE FORMS OK\n", [
        ("literal-constant", "literal-primary", [("if (19 /= 19)", "if (20 /= 19)")], "change the literal constant primary"),
        ("designator", "designator-primary", [("  designator_value = 23\n", "  designator_value = 24\n")], "change the object named by the designator primary"),
        ("array-constructor", "array-constructor-primary", [("  array_value = [3,5]\n", "  array_value = [3,6]\n")], "change an element in the array-constructor primary"),
        ("structure-constructor", "structure-constructor-primary", [("  constructed = pair(7,11)\n", "  constructed = pair(7,12)\n")], "change a component value in the structure-constructor primary"),
        ("function-reference", "function-reference-primary", [("  function_value = make_value(4)\n", "  function_value = make_value(5)\n")], "change the actual argument in the function-reference primary"),
        ("parenthesized-expr", "parenthesized-expr-primary", [("  parenthesized_value = (2+6)\n", "  parenthesized_value = (2+7)\n")], "change the expression inside the parenthesized primary"),
        ("conditional-expr", "conditional-expr-primary", [("(.true. ? 31 : 41)", "(.false. ? 31 : 41)")], "change the conditional guard selecting the primary's arm"),
    ], "10.1.2.2 R1001 lists literal, designator, constructors, function-reference, parenthesized, and conditional primaries."))

    source = """program expr_c1002_controls
  implicit none
  integer :: checks, local_array(3), actual(3)
  checks=0
  local_array = [4,5,6]
  if (any(local_array /= [4,5,6])) error stop 'EC1002:ordinary'
  checks=checks+1
  actual = [10,20,30]
  call observe(actual)
  checks=checks+1
  if (checks /= 2) error stop 'EC1002:checks'
  write(*,'(a)') 'EXPRESSIONS C1002 CONTROLS OK'
contains
  subroutine observe(a)
    integer, intent(in) :: a(*)
    if (a(1) /= 10) error stop 'EC1002:element'
  end subroutine observe
end program expr_c1002_controls
"""
    add(valid_case("c1002_controls", "C1002", ["ordinary-designator-control", "assumed-size-element-control"], "positive-control", source,
                   "EXPRESSIONS C1002 CONTROLS OK\n", [
        ("ordinary-designator-control", "ordinary-designator-values", [("  local_array = [4,5,6]\n", "  local_array = [4,5,7]\n")], "change the ordinary whole-array designator's values"),
        ("assumed-size-element-control", "assumed-size-element-value", [("  actual = [10,20,30]\n", "  actual = [11,20,30]\n")], "change the actual element observed through an assumed-size element designator"),
    ], "10.1.2.2 C1002 allows designator primaries that are not whole assumed-size arrays."))
    add(invalid_case("c1002_whole_assumed_size", "C1002", "whole-assumed-size-array-rejected", """program expr_c1002_whole_assumed_size
  implicit none
  integer :: actual(3) = [1,2,3]
  call observe(actual)
contains
  subroutine observe(a)
    integer, intent(in) :: a(*)
    integer :: b(3)
    b = a
  end subroutine observe
end program expr_c1002_whole_assumed_size
""", 9, ["upper bound in the last dimension", "assumed size array"],
                     "Repair only the primary to a(:3), a bounded section with the same element type and rank.",
                     "C1002 prohibits using a whole assumed-size array designator as a primary."))

    source = """program expr_c1003_parenthesized_control
  implicit none
  integer :: checks, i
  checks=0
  i = 4
  if ((i+1) /= 5) error stop 'EC1003:ordinary'
  checks=checks+1
  if (checks /= 1) error stop 'EC1003:checks'
  write(*,'(a)') 'EXPRESSIONS C1003 PAREN CONTROL OK'
end program expr_c1003_parenthesized_control
"""
    add(valid_case("c1003_parenthesized_control", "C1003", SELECTED["C1003"], "positive-control", source,
                   "EXPRESSIONS C1003 PAREN CONTROL OK\n", [
        ("ordinary-parenthesized-expression", "ordinary-parenthesized-expression", [("if ((i+1) /= 5)", "if ((i+2) /= 5)")], "change the ordinary expression inside parentheses"),
    ], "10.1.2.2 C1003 does not prohibit ordinary parenthesized expressions."))

    source = """program expr_conditional_selection
  implicit none
  integer :: checks, calls, seen, x
  checks=0
  calls=0; seen=0
  x = 10 * (.true. ? branch(1,2) : branch(9,3))
  if (x /= 20 .or. calls /= 1 .or. seen /= 1) error stop 'ECS:primary'
  checks=checks+1
  calls=0; seen=0
  x = (.true. ? branch(2,11) : branch(8,22))
  if (x /= 11 .or. calls /= 1 .or. seen /= 2) error stop 'ECS:true'
  checks=checks+1
  calls=0; seen=0
  x = (.false. ? branch(3,11) : branch(4,22))
  if (x /= 22 .or. calls /= 1 .or. seen /= 4) error stop 'ECS:false'
  checks=checks+1
  calls=0; seen=0
  x = (.false. ? branch(5,10) : .true. ? branch(6,20) : branch(7,30))
  if (x /= 20 .or. calls /= 1 .or. seen /= 6) error stop 'ECS:nested'
  checks=checks+1
  if (checks /= 4) error stop 'ECS:checks'
  write(*,'(a)') 'EXPRESSIONS CONDITIONAL SELECTION OK'
contains
  integer function branch(tag, value)
    integer, intent(in) :: tag, value
    calls = calls + 1
    seen = tag
    branch = value
  end function branch
end program expr_conditional_selection
"""
    add(valid_case("conditional_selection", "S10.1.2.3-001", SELECTED["S10.1.2.3-001"], "effect", source,
                   "EXPRESSIONS CONDITIONAL SELECTION OK\n", [
        ("primary-classification", "conditional-primary-in-multiply", [("x = 10 * (.true. ? branch(1,2) : branch(9,3))", "x = 11 * (.true. ? branch(1,2) : branch(9,3))")], "change the higher expression using the conditional primary"),
        ("true-arm-selection", "true-arm-guard", [("x = (.true. ? branch(2,11) : branch(8,22))", "x = (.false. ? branch(2,11) : branch(8,22))")], "change the guard so the other arm is selected"),
        ("false-arm-selection", "false-arm-guard", [("x = (.false. ? branch(3,11) : branch(4,22))", "x = (.true. ? branch(3,11) : branch(4,22))")], "change the guard so the true arm is selected"),
        ("nested-selection", "nested-middle-guard", [("x = (.false. ? branch(5,10) : .true. ? branch(6,20) : branch(7,30))", "x = (.false. ? branch(5,10) : .false. ? branch(6,20) : branch(7,30))")], "change the chained guard so the final arm is selected"),
    ], "10.1.2.3 p1 says a conditional expression is a primary that selectively evaluates a chosen subexpression."))

    source = """program expr_conditional_syntax_forms
  implicit none
  integer :: checks, i, x
  checks=0
  x = (.true. ? 3 : 4)
  if (x /= 3) error stop 'ER1002:two-arm'
  checks=checks+1
  x = (.false. ? 3 : .true. ? 5 : 6)
  if (x /= 5) error stop 'ER1002:chain'
  checks=checks+1
  i = 1
  x = (i == 1 ? 7 : 8)
  if (x /= 7) error stop 'ER1002:scalar-guard'
  checks=checks+1
  if (checks /= 3) error stop 'ER1002:checks'
  write(*,'(a)') 'EXPRESSIONS CONDITIONAL SYNTAX FORMS OK'
end program expr_conditional_syntax_forms
"""
    add(valid_case("conditional_syntax_forms", "R1002", ["two-arm-form", "chained-guard-form", "scalar-logical-guard"], "positive-control", source,
                   "EXPRESSIONS CONDITIONAL SYNTAX FORMS OK\n", [
        ("two-arm-form", "two-arm-guard", [("x = (.true. ? 3 : 4)", "x = (.false. ? 3 : 4)")], "change the guard in the two-arm conditional"),
        ("chained-guard-form", "chained-guard", [("x = (.false. ? 3 : .true. ? 5 : 6)", "x = (.false. ? 3 : .false. ? 5 : 6)")], "change the repeated guard in the chained form"),
        ("scalar-logical-guard", "scalar-logical-guard", [("  i = 1\n", "  i = 2\n")], "change the scalar variable feeding the logical guard"),
    ], "10.1.2.3 R1002 defines two-arm, repeated guarded, and scalar logical guard syntax."))

    add(invalid_case("r1002_missing_final_colon", "R1002", "missing-final-colon-rejected", """program expr_r1002_missing_final_colon
  implicit none
  integer :: x
  x = (.true. ? 3 )
end program expr_r1002_missing_final_colon
""", 4, ["Expected ':' in conditional expression", "Token ')' is unexpected"],
                     "Insert only ': 4' to obtain x = (.true. ? 3 : 4), the two-arm-form control.",
                     "R1002 requires a colon and final expr after the true expr."))
    add(invalid_case("r1002_missing_question", "R1002", "missing-question-rejected", """program expr_r1002_missing_question
  implicit none
  integer :: x
  x = (.true. 3 : 4)
end program expr_r1002_missing_question
""", 4, ["Expected a right parenthesis in expression", "Token '3'"],
                     "Insert only '?' after the scalar logical guard to obtain x = (.true. ? 3 : 4).",
                     "R1002 requires a question mark after each scalar-logical-expr guard."))

    source = """program expr_conditional_characteristics
  use iso_fortran_env, only: int32
  implicit none
  integer :: checks, x
  checks=0
  if (kind((.true. ? 3_int32 : 4_int32)) /= int32) error stop 'EC1004:kind'
  if ((.true. ? 3_int32 : 4_int32) /= 3_int32) error stop 'EC1004:value'
  checks=checks+1
  x = (.false. ? 10_int32 : .true. ? 20_int32 : 30_int32)
  if (x /= 20) error stop 'EC1004:nested'
  checks=checks+1
  if (checks /= 2) error stop 'EC1004:checks'
  write(*,'(a)') 'EXPRESSIONS CONDITIONAL CHARACTERISTICS OK'
end program expr_conditional_characteristics
"""
    add(valid_case("conditional_characteristics", "C1004", ["same-characteristics-control", "nested-arm-characteristics"], "positive-control", source,
                   "EXPRESSIONS CONDITIONAL CHARACTERISTICS OK\n", [
        ("same-characteristics-control", "same-kind-selected-value", [("(.true. ? 3_int32 : 4_int32) /= 3_int32", "(.false. ? 3_int32 : 4_int32) /= 3_int32")], "change the guard while preserving both arms same type kind and rank"),
        ("nested-arm-characteristics", "nested-arm-selection", [(".true. ? 20_int32 : 30_int32", ".false. ? 20_int32 : 30_int32")], "change the nested guard while all arms keep the same characteristics"),
    ], "10.1.2.3 C1004 requires all conditional result arms to have the same declared type, kind parameters, and rank."))
    add(invalid_case("c1004_type_mismatch", "C1004", "declared-type-mismatch-rejected", """program expr_c1004_type_mismatch
  implicit none
  integer :: x
  x = (.true. ? 1 : 2.0)
end program expr_c1004_type_mismatch
""", 4, ["same declared type", "same type and kind", "type mismatch"],
                     "Change only 2.0 to integer literal 2 to match the declared type of the other result arm.",
                     "C1004 requires every result expr of a conditional-expr to have the same declared type."))
    add(invalid_case("c1004_kind_mismatch", "C1004", "kind-parameter-mismatch-rejected", """program expr_c1004_kind_mismatch
  use iso_fortran_env, only: int32, int64
  implicit none
  integer(int32) :: x
  x = (.true. ? 1_int32 : 2_int64)
end program expr_c1004_kind_mismatch
""", 5, ["same kind parameter", "same type and kind", "type mismatch"],
                     "Change only 2_int64 to 2_int32 to match the kind parameter of the other result arm.",
                     "C1004 requires every result expr of a conditional-expr to have the same kind type parameters."))
    source = """program expr_c1004_rank_control
  implicit none
  integer :: checks, x
  checks=0
  x = (.true. ? 1 : 2)
  if (x /= 1) error stop 'EC1004:rank-control'
  checks=checks+1
  if (checks /= 1) error stop 'EC1004:checks'
  write(*,'(a)') 'EXPRESSIONS C1004 RANK CONTROL OK'
end program expr_c1004_rank_control
"""
    add(valid_case("c1004_rank_control", "C1004", ["rank-mismatch-rejected"], "positive-control", source,
                   "EXPRESSIONS C1004 RANK CONTROL OK\n", [
        ("rank-mismatch-rejected", "rank-control-select-other-scalar", [("x = (.true. ? 1 : 2)", "x = (.false. ? 1 : 2)")], "change the scalar guard while preserving scalar rank for both arms"),
    ], "The one-property C1004 rank repair [2] -> 2 is a conforming scalar conditional expression that runs on both compilers."))
    add(invalid_case("c1004_rank_mismatch", "C1004", "rank-mismatch-rejected", """program expr_c1004_rank_mismatch
  implicit none
  integer :: x
  x = (.true. ? 1 : [2])
end program expr_c1004_rank_mismatch
""", 4, ["same rank", "rank mismatch"],
                     "Change only the false arm [2] to scalar 2; the repaired scalar conditional is the c1004_rank_control fixture.",
                     "C1004 requires every result expr of a conditional-expr to have the same rank."))

    unary_module = """module expr_defined_unary_m
  implicit none
  interface operator(.u.)
    module procedure u
  end interface
  interface operator(.inverse.)
    module procedure inverse
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = 10*x
  end function u
  integer function inverse(x)
    integer, intent(in) :: x
    inverse = 100 + x
  end function inverse
end module expr_defined_unary_m
"""
    source = unary_module + """program expr_level1_precedence
  use expr_defined_unary_m
  implicit none
  integer :: checks, x
  checks=0
  x = .u. 2 * 3
  if (x /= 60) error stop 'EL1:precedence'
  checks=checks+1
  x = .u.(1+2)
  if (x /= 30) error stop 'EL1:parenthesized'
  checks=checks+1
  x = 6 * 2
  if (x /= 12) error stop 'EL1:primary-only'
  checks=checks+1
  if (checks /= 3) error stop 'EL1:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL1 PRECEDENCE OK'
end program expr_level1_precedence
"""
    add(valid_case("level1_precedence", "S10.1.2.4-001", SELECTED["S10.1.2.4-001"], "positive-control", source,
                   "EXPRESSIONS LEVEL1 PRECEDENCE OK\n", [
        ("defined-unary-before-intrinsic", "remove-defined-unary-before-multiply", [("  x = .u. 2 * 3\n", "  x = 2 * 3\n")], "remove the defined unary operator before multiplication"),
        ("defined-unary-on-parenthesized-expression", "parenthesized-operand-value", [("  x = .u.(1+2)\n", "  x = .u.(1+3)\n")], "change the parenthesized expression operand"),
        ("primary-without-defined-unary", "primary-only-expression", [("  x = 6 * 2\n", "  x = 7 * 2\n")], "change the primary used without a defined unary operator"),
    ], "10.1.2.4 p1 says defined unary operators have highest precedence and level-1 is primary optionally so operated."))

    source = unary_module + """program expr_r1003_forms
  use expr_defined_unary_m
  implicit none
  integer :: checks, x
  checks=0
  x = 6
  if (x /= 6) error stop 'ER1003:primary'
  checks=checks+1
  x = .u. 6
  if (x /= 60) error stop 'ER1003:defined'
  checks=checks+1
  if (checks /= 2) error stop 'ER1003:checks'
  write(*,'(a)') 'EXPRESSIONS R1003 FORMS OK'
end program expr_r1003_forms
"""
    add(valid_case("r1003_forms", "R1003", ["primary-only", "defined-unary-primary"], "positive-control", source,
                   "EXPRESSIONS R1003 FORMS OK\n", [
        ("primary-only", "r1003-primary-only", [("  x = 6\n", "  x = 7\n")], "change the primary-only level-1 expression"),
        ("defined-unary-primary", "r1003-defined-unary", [("  x = .u. 6\n", "  x = .u. 7\n")], "change the primary operand following the defined unary operator"),
    ], "10.1.2.4 R1003 defines level-1-expr as primary or defined-unary-op primary."))
    add(invalid_case("r1003_double_unary", "R1003", "two-unary-without-parentheses-rejected", unary_module + """program expr_r1003_double_unary
  use expr_defined_unary_m
  implicit none
  integer :: x
  x = 3
  x = .u. .inverse. x
end program expr_r1003_double_unary
""", 24, ["Invalid character in name", "Token '.inverse.'"],
                     "Repair to x = .u.(.inverse. x) changes only the operand into a parenthesized primary.",
                     "R1003 permits one defined-unary-op followed by a primary, not another bare defined-unary-op."))

    source = unary_module + """program expr_r1004_spelling
  use expr_defined_unary_m
  implicit none
  integer :: checks, x
  checks=0
  x = .u. 4
  if (x /= 40) error stop 'ER1004:single'
  checks=checks+1
  x = .inverse. 5
  if (x /= 105) error stop 'ER1004:multiple'
  checks=checks+1
  if (checks /= 2) error stop 'ER1004:checks'
  write(*,'(a)') 'EXPRESSIONS R1004 SPELLING OK'
end program expr_r1004_spelling
"""
    add(valid_case("r1004_spelling", "R1004", ["single-letter", "multiple-letters"], "positive-control", source,
                   "EXPRESSIONS R1004 SPELLING OK\n", [
        ("single-letter", "single-letter-operator", [("  x = .u. 4\n", "  x = .u. 5\n")], "change the operand of the single-letter defined unary operator"),
        ("multiple-letters", "multiple-letter-operator", [("  x = .inverse. 5\n", "  x = .inverse. 6\n")], "change the operand of the multiple-letter defined unary operator"),
    ], "10.1.2.4 R1004 spells a defined-unary-op as dot, letters, dot."))
    add(invalid_case("r1004_digit_in_name", "R1004", "digit-in-name-rejected", """module expr_r1004_digit_in_name
  implicit none
  interface operator(.u1.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = x
  end function u
end module expr_r1004_digit_in_name
""", 3, ["Bad character '1' in OPERATOR name", "Token '.' is not recognized"],
                     "Repair only the spelling to .ua.; the dots and interface shape remain unchanged.",
                     "R1004 permits letters between the delimiting periods; digit 1 is not a letter."))

    longop = "." + "a"*63 + "."
    source = f"""module expr_c1005_long_m
  implicit none
  interface operator({longop})
    module procedure longop_impl
  end interface
contains
  integer function longop_impl(x)
    integer, intent(in) :: x
    longop_impl = 1000 + x
  end function longop_impl
end module expr_c1005_long_m
program expr_c1005_controls
  use expr_c1005_long_m
  implicit none
  integer :: checks, x
  checks=0
  x = {longop} 7
  if (x /= 1007) error stop 'EC1005:long'
  checks=checks+1
  if (checks /= 1) error stop 'EC1005:checks'
  write(*,'(a)') 'EXPRESSIONS C1005 CONTROLS OK'
end program expr_c1005_controls
"""
    add(valid_case("c1005_controls", "C1005", ["sixty-three-letter-control"], "positive-control", source,
                   "EXPRESSIONS C1005 CONTROLS OK\n", [
        ("sixty-three-letter-control", "sixty-three-letter-operator", [(f"  x = {longop} 7\n", f"  x = {longop} 8\n")], "change the operand of the valid 63-letter defined unary operator"),
    ], "10.1.2.4 C1005 allows a defined-unary-op containing no more than 63 letters when otherwise valid."))
    long64 = "." + "a"*64 + "."
    add(invalid_case("c1005_sixty_four_letters", "C1005", "sixty-four-letter-rejected", f"""module expr_c1005_sixty_four_letters
  implicit none
  interface operator({long64})
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = x
  end function u
end module expr_c1005_sixty_four_letters
""", 3, ["Name at", "too long"],
                     "Repair only the operator spelling by deleting one letter, yielding the 63-letter control spelling.",
                     "C1005 prohibits a defined-unary-op containing more than 63 letters."))
    add(invalid_case("c1005_intrinsic_not", "C1005", "intrinsic-operator-spelling-rejected", """module expr_c1005_intrinsic_not
  implicit none
  interface operator(.not.)
    module procedure u
  end interface
contains
  logical function u(x)
    logical, intent(in) :: x
    u = .not. x
  end function u
end module expr_c1005_intrinsic_not
""", 4, ["conflicts with intrinsic interface", "intrinsic"],
                     "Repair only the spelling to .notx.; the interface remains a valid defined unary operator.",
                     "C1005 excludes spellings that are the same as intrinsic operators such as .NOT.."))

    for lit, facet in (("true", "logical-true-spelling-rejected"), ("false", "logical-false-spelling-rejected")):
        add(invalid_case(f"c1005_logical_{lit}", "C1005", facet, f"""module expr_c1005_logical_{lit}
  implicit none
  interface operator(.{lit}.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = x
  end function u
end module expr_c1005_logical_{lit}
""", 3, [f"The name '{lit}' cannot be used as a defined operator", f"Token '.{lit}.'"],
                         f"Repair only the spelling to .{lit}x.; dots and letters-only form remain.",
                         f"C1005 excludes the logical literal constant spelling .{lit.upper()}. from defined unary operator names."))

    return specs


def manifest(spec):
    item = dict(
        schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
    )
    if spec["kind"] == "invalid":
        item["expect"] = dict(
            phase="compile", step="source", outcome="diagnose",
            diagnostic=dict(file="source.f90", line=spec["line"], contains_any=spec["messages"], excludes_any=EXCLUDES),
        )
    else:
        item["link"] = dict(driver="fortran", objects=["source.o"], output="program")
        item["expect"] = dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr="")
    return item


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["variant"])
        spec["source_sha256"] = sha(spec["source"].encode("ascii"))
        spec["manifest"] = manifest(spec)
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        owner.setdefault("pending", {})
        local = [facet for facet in facets if facet in owner["facets"]]
        if not set(local) <= set(owner.get("pending", {})) | (set(owner["facets"]) - set(owner.get("pending", {}))):
            raise ValueError("selected facets changed for " + rule)
        for facet in local:
            owner.get("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE_TEXT[rule])
        limitation = owner.get("oracle_limitation", "")
        old = ("This source-only catalogue records pending plans only. It creates no Fortran test program, invokes no "
               "processor, approves no fixture or oracle, and claims no coverage.")
        new = ("The original source-only catalogue recorded pending plans only and created no Fortran test program, "
               "compiler invocation, fixture approval, oracle approval, or coverage claim; this generator supplies "
               "selected fixtures and mutation/diagnostic plans without granting unrelated approvals or claims.")
        if old in limitation:
            limitation = limitation.replace(old, new)
        owner["oracle_limitation"] = owned_paragraph(limitation, LIMIT_PREFIX, LIMIT_TEXT[rule])
    return updated


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
    before = before.replace(
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `" + CATALOGUES[section] + "`. The original source-only registration supplied pending plans; "
        "the bounded batch291 fixtures below supply selected cases and mutation/diagnostic plans, not oracle approval, "
        "fixture approval, source-review renewal, or universal coverage.")
    selected_here = [rule for rule in SELECTED if rule in {row["id"] for row in catalogue["requirements"]}]
    summary = (
        SUMMARY_BEGIN + "\n"
        f"## Batch291 expression fixtures for {section}\n\n"
        f"This section has generated batch291 fixtures for: {', '.join(selected_here)}. Runtime cases use exact "
        "integer, logical, character length/kind, rank, and shape oracles; diagnostic cases are line-anchored "
        "one-property malformed forms with conforming repairs documented in generator metadata. Feature mutations "
        "are permanent and checked on both the reference gfortran 16.1 and the frozen LFortran target. Facets not "
        "listed remain pending for the reasons recorded in each requirement.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("summary boundaries changed for " + section)
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues, rendered = {}, {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        updated = synced_catalogue(catalogue)
        updated_catalogues[rel] = updated
        rendered[VIEWS[section]] = render_view(section, updated, root)
    actual = {path for path in (root / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()}
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [path.relative_to(root).as_posix() for path in sorted(actual - set(files))]
        for rel, updated in updated_catalogues.items():
            if json.loads((root / rel).read_text()) != updated:
                stale.append(rel)
        for rel, text in rendered.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise SystemExit("stale expressions 10.1.1-10.1.2.4 fixtures: " + ", ".join(stale))
    else:
        extras = actual - set(files)
        if extras:
            raise ValueError("unexpected generated expression fixture files: " + ", ".join(str(p) for p in sorted(extras)))
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for rel, updated in updated_catalogues.items():
                (root / rel).write_text(json.dumps(updated, indent=2) + "\n")
            for rel, text in rendered.items():
                (root / rel).write_text(text)
    return specs


def compiler_command(compiler, std, source, output):
    compiler = str(compiler)
    if "gfortran" in Path(compiler).name:
        return [compiler, f"-std={std}", str(source), "-o", str(output)]
    return [compiler, f"--std={std}", str(source), "-o", str(output)]


def git_status(root):
    ran = subprocess.run(["git", "--no-pager", "status", "--porcelain"], cwd=root,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20, check=False)
    if ran.returncode != 0:
        raise RuntimeError(ran.stderr)
    return ran.stdout


def run_one(source, compiler, std, work):
    work.mkdir(parents=True, exist_ok=True)
    (work / "source.f90").write_text(source)
    compiled = subprocess.run(compiler_command(compiler, std, Path("source.f90"), Path("program")), cwd=work,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
    if compiled.returncode != 0:
        return dict(phase="compile", returncode=compiled.returncode, stdout=compiled.stdout, stderr=compiled.stderr)
    ran = subprocess.run([str(work / "program")], cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, timeout=30, check=False)
    return dict(phase="run", returncode=ran.returncode, stdout=ran.stdout, stderr=ran.stderr)


def mutation_check(root=ROOT, compiler=None, std=None, keep=False):
    if not compiler or not std:
        raise ValueError("--mutation-check requires --compiler and --std")
    root = Path(root)
    specs = source_specs()
    build_root = root / BUILD_ROOT / (Path(compiler).name + "_" + std.replace("/", "_"))
    if build_root.exists():
        shutil.rmtree(build_root)
    before = None if keep else git_status(root)
    failures = []
    total = 0
    try:
        for spec in specs.values():
            if spec["kind"] != "valid":
                continue
            parent = run_one(spec["source"], compiler, std, build_root / spec["variant"] / "parent")
            if parent["phase"] != "run" or parent["returncode"] != 0 or parent["stdout"] != spec["completion"] or parent["stderr"] != "":
                failures.append((spec["variant"], "parent", parent))
                continue
            for mutation in spec["mutations"]:
                total += 1
                observed = run_one(mutation["source"], compiler, std, build_root / spec["variant"] / mutation["id"])
                if observed["phase"] != "run":
                    failures.append((spec["variant"], mutation["id"] + " compile", observed))
                elif observed["returncode"] == 0 and observed["stdout"] == spec["completion"] and observed["stderr"] == "":
                    failures.append((spec["variant"], mutation["id"] + " survived", observed))
        if failures:
            lines = ["mutation check failed:"]
            for variant, ident, observed in failures:
                lines.append(f"{variant}:{ident}: {observed['phase']} rc={observed['returncode']} stdout={observed['stdout'][:200]!r} stderr={observed['stderr'][:400]!r}")
            raise SystemExit("\n".join(lines))
        return total
    finally:
        if not keep and build_root.exists():
            shutil.rmtree(build_root)
            try:
                (root / BUILD_ROOT).rmdir()
            except OSError:
                pass
        if before is not None:
            after = git_status(root)
            if after != before:
                raise SystemExit("mutation check changed git status:\n" + after)


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
        print(f"Mutation-checked {count} expression feature mutants with {args.compiler} ({args.std}).")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    valid = sum(1 for spec in specs.values() if spec["kind"] == "valid")
    invalid = len(specs) - valid
    facets = sum(len(spec["facets"]) for spec in specs.values())
    mutations = sum(len(spec["mutations"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {valid} valid and {invalid} invalid expression fixtures, {facets} facet bindings, {mutations} feature mutants.")


if __name__ == "__main__":
    main()
