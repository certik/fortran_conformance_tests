#!/usr/bin/env python3
"""Fixtures for Fortran 2023 expressions 10.1.2.8 through 10.1.3."""

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
PREFIX = "expressions_10_1_2_8_10_1_3_"
BUILD_ROOT = ".expressions_10_1_2_8_10_1_3_mutation_check"
SUMMARY_BEGIN = "<!-- BEGIN EXPRESSIONS 10.1.2.8-10.1.3 FIXTURES -->"
SUMMARY_END = "<!-- END EXPRESSIONS 10.1.2.8-10.1.3 FIXTURES -->"

CATALOGUES = {
    "10.1.2.8": "doc/catalogues/level_5_expressions_10_1_2_8.json",
    "10.1.2.9": "doc/catalogues/general_form_of_an_expression_10_1_2_9.json",
    "10.1.3": "doc/catalogues/precedence_of_operators_10_1_3.json",
}
VIEWS = {
    "10.1.2.8": "doc/fortran_2023_10_1_2_8.md",
    "10.1.2.9": "doc/fortran_2023_10_1_2_9.md",
    "10.1.3": "doc/fortran_2023_10_1_3.md",
}

EXCLUDES = [
    "not implemented", "not yet implemented", "unimplemented",
    "internal compiler error", "Internal Compiler Error", "ASR verify", "module failed verification",
    "LLVM ERROR", "ICE",
]

SELECTED = {
    "S10.1.2.8-001": ["level-4-base", "not-layer", "and-layer", "or-layer", "equivalence-layer"],
    "R1015": ["level-4-only", "not-level-4", "double-not-without-parentheses-rejected"],
    "R1016": ["single-and-operand", "and-chain", "left-recursive-and", "missing-right-and-operand-rejected"],
    "R1017": ["single-or-operand", "or-chain", "and-before-or-precedence", "missing-right-or-operand-rejected"],
    "R1018": ["single-equiv-operand", "eqv-chain", "neqv-chain", "left-recursive-equiv", "missing-right-equiv-operand-rejected"],
    "R1019": ["dot-not-token"],
    "R1020": ["dot-and-token"],
    "R1021": ["dot-or-token"],
    "R1022": ["dot-eqv-token", "dot-neqv-token"],
    "S10.1.2.9-001": ["level-5-base", "defined-binary-after-intrinsic", "defined-binary-left-chain", "parenthesized-defined-binary-operand"],
    "R1023": ["single-level-5", "defined-binary-operation", "left-recursive-defined-binary", "right-defined-binary-requires-parentheses", "missing-right-level-5-rejected"],
    "R1024": ["single-letter", "multiple-letters", "missing-leading-dot-rejected", "missing-trailing-dot-rejected", "digit-in-name-rejected"],
    "C1006": ["sixty-three-letter-control", "sixty-four-letter-rejected", "logical-true-spelling-rejected", "logical-false-spelling-rejected"],
    "S10.1.3-001": ["power-before-unary-minus", "multiply-before-binary-plus", "unary-before-binary-plus", "character-before-relational", "relational-before-logical-or", "not-before-and", "and-before-or", "or-before-eqv", "defined-binary-lowest", "parentheses-override-category-precedence"],
    "S10.1.3-002": ["extended-intrinsic-operator-precedence", "defined-unary-operator-highest", "defined-binary-operator-lowest", "dotted-name-not-intrinsic-symbol-precedence"],
    "S10.1.3-003": ["left-grouped-subtraction", "left-grouped-division", "right-grouped-exponentiation", "left-grouped-concatenation-boundary", "logical-same-class-grouping-boundary", "parentheses-override-same-class-grouping"],
}

PENDING_NOTES = {
    "R1015": {"not-before-level-5-rejected": "PENDING batch304: no isolated negative was found; unparenthesized forms such as .NOT. a .AND. b parse validly as (.NOT. a) .AND. b, while parenthesized .NOT.(a .AND. b) supplies a level-4 primary."},
    "R1019": {"other-token-rejected": "PENDING batch304: a dotted non-.NOT. spelling in this position is a defined-unary/generic-resolution case rather than an isolated R1019 token-membership diagnostic."},
    "R1020": {"other-token-rejected": "PENDING batch304: replacing .AND. by a different dotted token between operands is parsed as another logical layer or as a defined-binary/generic-resolution case, not an isolated R1020 token-membership diagnostic."},
    "R1021": {"other-token-rejected": "PENDING batch304: replacing .OR. by a different dotted token between operands is parsed as another logical layer or as a defined-binary/generic-resolution case, not an isolated R1021 token-membership diagnostic."},
    "R1022": {"other-token-rejected": "PENDING batch304: a non-equivalence dotted token at this precedence is a defined-binary/generic-resolution case or another logical operator, not an isolated R1022 membership diagnostic."},
    "C1006": {
        "intrinsic-operator-spelling-rejected": "PENDING batch304: OPERATOR(.AND.) is also the syntax for extending an intrinsic operator, so failures with nonlogical operands are attributable to operator applicability rather than solely to C1006 defined-binary spelling.",
    },
}

ORACLE_PREFIX = "Batch304 expressions 10.1.2.8-10.1.3 fixtures: "
LIMIT_PREFIX = "Batch304 expressions 10.1.2.8-10.1.3 boundaries: "

ORACLE_TEXT = {rule: ORACLE_PREFIX + (
    "the batch304 fixtures observe the selected facets with exact integer, logical, character LEN/value, or derived-operation integer component assertions. "
    "Each selected runtime facet has a distinct assertion and a conforming feature mutation that changes an operator, operand, or parenthesization and fails at run time on both toolchains; selected diagnostic facets have one-property compiled controls."
) for rule in SELECTED}
LIMIT_TEXT = {rule: LIMIT_PREFIX + (
    "Only the selected facets are discharged. Existing source review state, unrelated bindings, approval state, and rollout progress are not changed. "
    "Remaining pending facets stay pending for the recorded reasons. No oracle depends on operand evaluation order, short-circuiting, side effects, address identity, real rounding, or compiler consensus."
) for rule in SELECTED}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, rule, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + "_" + kind + "__" + PREFIX + variant


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"mutation span is not unique: {old!r} count={source.count(old)}")
    return source.replace(old, new, 1)


def apply_pairs(source, pairs):
    result = source
    for old, new in pairs:
        result = replace_once(result, old, new)
    return result


def valid_case(variant, rule, facets, evidence, source, completion, mutations, derivation):
    spec = dict(id=identifier(variant, rule, "valid"), variant=variant, rule=rule, facets=list(facets),
                kind="valid", evidence=evidence, source=source, completion=completion, mutations=[],
                derivation=derivation)
    for facet, name, pairs, rationale in mutations:
        if facet not in facets:
            raise ValueError(f"mutation {name} names unowned facet {facet}")
        spec["mutations"].append(dict(id=name, facet=facet, replacements=pairs,
                                      source=apply_pairs(source, pairs), rationale=rationale))
    return spec


def invalid_case(variant, rule, facet, source, line, messages, repair, derivation):
    return dict(id=identifier(variant, rule, "invalid"), variant=variant, rule=rule, facets=[facet],
                kind="invalid", evidence="effect", source=source, line=line, messages=[],
                repair=repair, derivation=derivation, mutations=[])


def logical_source():
    return """program expr_level5_logical_layers
  implicit none
  integer :: checks
  logical :: ok
  checks = 0
  ok = 2 < 3
  if (.not. ok) error stop 'L5:s-level4-base'
  checks = checks + 1
  ok = .not. false_a()
  if (.not. ok) error stop 'L5:s-not-layer'
  checks = checks + 1
  ok = true_a() .and. false_a()
  if (ok) error stop 'L5:s-and-layer'
  checks = checks + 1
  ok = true_a() .or. false_a() .and. false_b()
  if (.not. ok) error stop 'L5:s-or-layer'
  checks = checks + 1
  ok = true_a() .or. false_a() .eqv. false_b()
  if (ok) error stop 'L5:s-equivalence-layer'
  checks = checks + 1
  ok = 4 == 4
  if (.not. ok) error stop 'R1015:level4-only'
  checks = checks + 1
  ok = .not. (5 == 6)
  if (.not. ok) error stop 'R1015:not-level4'
  checks = checks + 1
  ok = .not. false_b()
  if (.not. ok) error stop 'R1016:single-and-operand'
  checks = checks + 1
  ok = true_a() .and. true_b() .and. false_a()
  if (ok) error stop 'R1016:and-chain'
  checks = checks + 1
  ok = true_a() .and. true_b()
  if (.not. ok) error stop 'R1017:single-or-operand'
  checks = checks + 1
  ok = false_a() .or. true_b()
  if (.not. ok) error stop 'R1017:or-chain'
  checks = checks + 1
  ok = true_b() .or. false_a() .and. false_b()
  if (.not. ok) error stop 'R1017:and-before-or'
  checks = checks + 1
  ok = false_b() .or. true_a()
  if (.not. ok) error stop 'R1018:single-equiv-operand'
  checks = checks + 1
  ok = true_a() .eqv. true_b()
  if (.not. ok) error stop 'R1018:eqv-chain'
  checks = checks + 1
  ok = true_a() .neqv. false_a()
  if (.not. ok) error stop 'R1018:neqv-chain'
  checks = checks + 1
  ok = .not. false_a()
  if (.not. ok) error stop 'R1019:dot-not-token'
  checks = checks + 1
  ok = true_a() .and. false_b()
  if (ok) error stop 'R1020:dot-and-token'
  checks = checks + 1
  ok = false_a() .or. true_a()
  if (.not. ok) error stop 'R1021:dot-or-token'
  checks = checks + 1
  ok = true_b() .eqv. true_a()
  if (.not. ok) error stop 'R1022:dot-eqv-token'
  checks = checks + 1
  ok = true_b() .neqv. false_b()
  if (.not. ok) error stop 'R1022:dot-neqv-token'
  checks = checks + 1
  if (checks /= 20) error stop 'L5:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 5 LOGICAL OK'
contains
  pure logical function true_a()
    true_a = .true.
  end function true_a
  pure logical function true_b()
    true_b = .true.
  end function true_b
  pure logical function false_a()
    false_a = .false.
  end function false_a
  pure logical function false_b()
    false_b = .false.
  end function false_b
end program expr_level5_logical_layers
"""


def defined_binary_source():
    op63 = "a" * 63
    return f"""module expr_defined_binary_mod
  implicit none
  interface operator(.join.)
    module procedure join_i
  end interface
  interface operator(.b.)
    module procedure b_i
  end interface
  interface operator(.union.)
    module procedure union_i
  end interface
  interface operator(.{op63}.)
    module procedure long_i
  end interface
contains
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
  pure integer function b_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    b_i = lhs + 10*rhs
  end function b_i
  pure integer function union_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    union_i = 100*lhs + rhs
  end function union_i
  pure integer function long_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    long_i = 1000*lhs + rhs
  end function long_i
end module expr_defined_binary_mod

program expr_defined_binary_forms
  use expr_defined_binary_mod
  implicit none
  integer :: checks, x
  logical :: ok
  checks = 0
  ok = .true. .and. .true.
  if (.not. ok) error stop 'GEN:level5-base'
  checks = checks + 1
  x = 1 + 2 .join. 3 * 4
  if (x /= 42) error stop 'GEN:defined-after-intrinsic'
  checks = checks + 1
  x = 1 .join. 2 .join. 3
  if (x /= 123) error stop 'GEN:defined-left-chain'
  checks = checks + 1
  x = 1 .join. (2 .join. 3)
  if (x /= 33) error stop 'GEN:parenthesized-defined-right'
  checks = checks + 1
  ok = .false. .or. .true.
  if (.not. ok) error stop 'R1023:single-level5'
  checks = checks + 1
  x = 4 .join. 5
  if (x /= 45) error stop 'R1023:defined-operation'
  checks = checks + 1
  x = 6 .join. 7 .join. 8
  if (x /= 678) error stop 'R1023:left-recursive-defined'
  checks = checks + 1
  x = 6 .join. (7 .join. 8)
  if (x /= 138) error stop 'R1023:right-parenthesized'
  checks = checks + 1
  x = 2 .b. 3
  if (x /= 32) error stop 'R1024:single-letter'
  checks = checks + 1
  x = 2 .union. 3
  if (x /= 203) error stop 'R1024:multiple-letters'
  checks = checks + 1
  x = 2 .{op63}. 3
  if (x /= 2003) error stop 'C1006:sixty-three'
  checks = checks + 1
  if (checks /= 11) error stop 'GEN:checks'
  write(*,'(a)') 'EXPRESSIONS DEFINED BINARY OK'
end program expr_defined_binary_forms
"""


def precedence_source():
    return """module expr_precedence_mod
  implicit none
  type :: box
    integer :: value
  end type box
  interface operator(//)
    module procedure concat_box_box, concat_box_logical
  end interface
  interface operator(==)
    module procedure equal_box_box
  end interface
  interface operator(+)
    module procedure plus_box_box
  end interface
  interface operator(*)
    module procedure times_box_box
  end interface
  interface operator(**)
    module procedure power_box_box
  end interface
  interface operator(.neg.)
    module procedure neg_box
  end interface
  interface operator(.or.)
    module procedure or_box_box
  end interface
  interface operator(.join.)
    module procedure join_i
  end interface
  interface operator(.starstar.)
    module procedure starstar_i
  end interface
contains
  pure function concat_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function concat_box_box
  pure logical function concat_box_logical(lhs, rhs)
    type(box), intent(in) :: lhs
    logical, intent(in) :: rhs
    concat_box_logical = rhs
  end function concat_box_logical
  pure logical function equal_box_box(lhs, rhs)
    type(box), intent(in) :: lhs, rhs
    equal_box_box = lhs%value == rhs%value
  end function equal_box_box
  pure function plus_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 100*lhs%value + rhs%value
  end function plus_box_box
  pure function times_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function times_box_box
  pure function power_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function power_box_box
  pure function neg_box(arg) result(out)
    type(box), intent(in) :: arg
    type(box) :: out
    out%value = 100 + arg%value
  end function neg_box
  pure function or_box_box(lhs, rhs) result(out)
    type(box), intent(in) :: lhs, rhs
    type(box) :: out
    out%value = 10*lhs%value + rhs%value
  end function or_box_box
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
  pure integer function starstar_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    starstar_i = 10*lhs + rhs
  end function starstar_i
end module expr_precedence_mod

program expr_operator_precedence
  use expr_precedence_mod
  implicit none
  integer :: checks, x
  logical :: ok
  type(box) :: a, b, c, r
  checks = 0
  x = -2**2
  if (x /= -4) error stop 'PREC:power-before-unary-minus'
  checks = checks + 1
  x = 2+3*4
  if (x /= 14) error stop 'PREC:multiply-before-plus'
  checks = checks + 1
  x = -3 + 10
  if (x /= 7) error stop 'PREC:unary-before-binary-plus'
  checks = checks + 1
  a = box(1); b = box(2); c = box(12)
  ok = a // b == c
  if (.not. ok) error stop 'PREC:character-before-relational'
  checks = checks + 1
  ok = .false. .or. 2+3 >= 5
  if (.not. ok) error stop 'PREC:relational-before-or'
  checks = checks + 1
  ok = .not. .false. .and. .false.
  if (ok) error stop 'PREC:not-before-and'
  checks = checks + 1
  ok = .true. .or. .false. .and. .false.
  if (.not. ok) error stop 'PREC:and-before-or'
  checks = checks + 1
  ok = .true. .or. .false. .eqv. .false.
  if (ok) error stop 'PREC:or-before-eqv'
  checks = checks + 1
  x = 1 + 2 .join. 3
  if (x /= 33) error stop 'PREC:defined-binary-lowest'
  checks = checks + 1
  x = (2+3)*4
  if (x /= 20) error stop 'PREC:parentheses-category'
  checks = checks + 1
  a = box(1); b = box(2); c = box(3)
  r = a + b ** c
  if (r%value /= 123) error stop 'P2:extended-intrinsic-precedence'
  checks = checks + 1
  r = .neg. a * b
  if (r%value /= 1012) error stop 'P2:defined-unary-highest'
  checks = checks + 1
  x = 4 + 5 .join. 6
  if (x /= 96) error stop 'P2:defined-binary-lowest'
  checks = checks + 1
  x = 2 * 3 .starstar. 4
  if (x /= 64) error stop 'P2:dotted-name-lowest'
  checks = checks + 1
  x = 10-3-2
  if (x /= 5) error stop 'P3:left-subtraction'
  checks = checks + 1
  x = 64/4/2
  if (x /= 8) error stop 'P3:left-division'
  checks = checks + 1
  x = 2**3**2
  if (x /= 512) error stop 'P3:right-exponentiation'
  checks = checks + 1
  a = box(4); b = box(5); c = box(6)
  r = a // b // c
  if (r%value /= 456) error stop 'P3:left-concat-boundary'
  checks = checks + 1
  a = box(1); b = box(2); c = box(3)
  r = a .or. b .or. c
  if (r%value /= 123) error stop 'P3:logical-same-class'
  checks = checks + 1
  x = 10-(3-2)
  if (x /= 9) error stop 'P3:parentheses-same-class'
  checks = checks + 1
  if (checks /= 20) error stop 'PREC:checks'
  write(*,'(a)') 'EXPRESSIONS PRECEDENCE OK'
end program expr_operator_precedence
"""


def source_specs():
    specs = {}
    def add(spec):
        if spec["id"] in specs:
            raise ValueError(spec["id"])
        specs[spec["id"]] = spec

    logical = logical_source()
    add(valid_case("level5_logical_layers", "S10.1.2.8-001", SELECTED["S10.1.2.8-001"], "positive-control", logical,
                   "EXPRESSIONS LEVEL 5 LOGICAL OK\n", [
        ("level-4-base", "s10128-level4-base-mut", [("  ok = 2 < 3\n  if (.not. ok) error stop 'L5:s-level4-base'", "  ok = 2 > 3\n  if (.not. ok) error stop 'L5:s-level4-base'")], "change the level-4 relational operand truth value"),
        ("not-layer", "s10128-not-layer-mut", [("  ok = .not. false_a()\n  if (.not. ok) error stop 'L5:s-not-layer'", "  ok = false_a()\n  if (.not. ok) error stop 'L5:s-not-layer'")], "remove the not-op feature"),
        ("and-layer", "s10128-and-layer-mut", [("  ok = true_a() .and. false_a()\n  if (ok) error stop 'L5:s-and-layer'", "  ok = true_a() .or. false_a()\n  if (ok) error stop 'L5:s-and-layer'")], "replace .AND. by a conforming .OR. expression"),
        ("or-layer", "s10128-or-layer-mut", [("  ok = true_a() .or. false_a() .and. false_b()\n  if (.not. ok) error stop 'L5:s-or-layer'", "  ok = (true_a() .or. false_a()) .and. false_b()\n  if (.not. ok) error stop 'L5:s-or-layer'")], "parenthesize the lower-precedence OR grouping differently"),
        ("equivalence-layer", "s10128-equiv-layer-mut", [("  ok = true_a() .or. false_a() .eqv. false_b()\n  if (ok) error stop 'L5:s-equivalence-layer'", "  ok = true_a() .or. (false_a() .eqv. false_b())\n  if (ok) error stop 'L5:s-equivalence-layer'")], "parenthesize the OR/EQV relation differently"),
    ], "10.1.2.8 p1 layers level-4, NOT, AND, OR, and equivalence; exact logical truth tables give the oracle."))

    add(valid_case("r1015_and_operand_forms", "R1015", ["level-4-only", "not-level-4"], "positive-control", logical,
                   "EXPRESSIONS LEVEL 5 LOGICAL OK\n", [
        ("level-4-only", "r1015-level4-only-mut", [("  ok = 4 == 4\n  if (.not. ok) error stop 'R1015:level4-only'", "  ok = 4 /= 4\n  if (.not. ok) error stop 'R1015:level4-only'")], "change the level-4 expression used as the and-operand"),
        ("not-level-4", "r1015-not-level4-mut", [("  ok = .not. (5 == 6)\n  if (.not. ok) error stop 'R1015:not-level4'", "  ok = (5 == 6)\n  if (.not. ok) error stop 'R1015:not-level4'")], "remove the optional not-op before the level-4 expression"),
    ], "R1015 admits either a level-4 expression or .NOT. followed by one; both are checked by exact logical values."))
    add(invalid_case("r1015_double_not", "R1015", "double-not-without-parentheses-rejected", """program expr_r1015_double_not
  implicit none
  logical :: ok
  ok = .not. .not. .false.
  print *, ok
end program expr_r1015_double_not
""", 4, ["name", "not", "defined operator"], "Repair by changing the expression to .not.(.not. .false.), which is a parenthesized level-4 primary and evaluates false.", "R1015 permits at most one not-op before a level-4-expr; the second unparenthesized .NOT. cannot start that operand."))
    add(valid_case("r1015_double_not_control", "R1015", ["double-not-without-parentheses-rejected"], "positive-control", """program expr_r1015_double_not_control
  implicit none
  logical :: ok
  ok = .not.(.not. .false.)
  if (ok) error stop 'R1015:double-not-control'
  write(*,'(a)') 'EXPRESSIONS R1015 DOUBLE NOT CONTROL OK'
end program expr_r1015_double_not_control
""", "EXPRESSIONS R1015 DOUBLE NOT CONTROL OK\n", [
        ("double-not-without-parentheses-rejected", "r1015-double-not-control-mut", [("  ok = .not.(.not. .false.)\n  if (ok) error stop 'R1015:double-not-control'", "  ok = .not. .false.\n  if (ok) error stop 'R1015:double-not-control'")], "remove the parentheses/inner negation repair while staying conforming"),
    ], "The control adds only parentheses around the inner .NOT. expression and observes the resulting false value."))

    add(valid_case("r1016_and_operand_forms", "R1016", ["single-and-operand", "and-chain"], "positive-control", logical,
                   "EXPRESSIONS LEVEL 5 LOGICAL OK\n", [
        ("single-and-operand", "r1016-single-and-mut", [("  ok = .not. false_b()\n  if (.not. ok) error stop 'R1016:single-and-operand'", "  ok = false_b()\n  if (.not. ok) error stop 'R1016:single-and-operand'")], "remove the not-op inside the single and-operand"),
        ("and-chain", "r1016-and-chain-mut", [("  ok = true_a() .and. true_b() .and. false_a()\n  if (ok) error stop 'R1016:and-chain'", "  ok = true_a() .and. true_b() .or. false_a()\n  if (ok) error stop 'R1016:and-chain'")], "replace the second and-op with a conforming lower-precedence OR"),
    ], "R1016 admits an and-operand alone or a chain joined by .AND.; literal logical results distinguish the forms."))
    add(invalid_case("r1016_missing_and_rhs", "R1016", "missing-right-and-operand-rejected", """program expr_r1016_missing_and_rhs
  implicit none
  logical :: ok
  ok = .true. .and.
  print *, ok
end program expr_r1016_missing_and_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair by appending the missing and-operand .false.; the completed expression evaluates false.", "R1016 requires an and-operand after a present and-op."))
    add(valid_case("r1016_missing_and_rhs_control", "R1016", ["missing-right-and-operand-rejected"], "positive-control", """program expr_r1016_missing_and_rhs_control
  implicit none
  logical :: ok
  ok = .true. .and. .false.
  if (ok) error stop 'R1016:missing-and-control'
  write(*,'(a)') 'EXPRESSIONS R1016 MISSING AND RHS CONTROL OK'
end program expr_r1016_missing_and_rhs_control
""", "EXPRESSIONS R1016 MISSING AND RHS CONTROL OK\n", [
        ("missing-right-and-operand-rejected", "r1016-missing-and-control-mut", [("  ok = .true. .and. .false.\n  if (ok) error stop 'R1016:missing-and-control'", "  ok = .true. .and. .true.\n  if (ok) error stop 'R1016:missing-and-control'")], "change the supplied right and-operand in the conforming control"),
    ], "The control appends only the missing R1016 right and-operand."))
    add(valid_case("r1016_defined_and_grouping", "R1016", ["left-recursive-and"], "effect", """module expr_r1016_defined_and_mod
  implicit none
  type :: token
    integer :: value
  end type token
  interface operator(.and.)
    module procedure join_and
  end interface
contains
  pure function join_and(lhs, rhs) result(out)
    type(token), intent(in) :: lhs, rhs
    type(token) :: out
    out%value = 10*lhs%value + rhs%value
  end function join_and
end module expr_r1016_defined_and_mod

program expr_r1016_defined_and_grouping
  use expr_r1016_defined_and_mod
  implicit none
  type(token) :: a, b, c, r
  a = token(1); b = token(2); c = token(3)
  r = a .and. b .and. c
  if (r%value /= 123) error stop 'R1016:left-recursive-and'
  write(*,'(a)') 'EXPRESSIONS R1016 DEFINED AND GROUPING OK'
end program expr_r1016_defined_and_grouping
""", "EXPRESSIONS R1016 DEFINED AND GROUPING OK\n", [
        ("left-recursive-and", "r1016-defined-and-right-group-mut", [("  r = a .and. b .and. c\n  if (r%value /= 123) error stop 'R1016:left-recursive-and'", "  r = a .and. (b .and. c)\n  if (r%value /= 123) error stop 'R1016:left-recursive-and'")], "parenthesize the right .AND. operation instead of the R1016 left-recursive grouping"),
    ], "R1016 is left-recursive for .AND.; a non-associative defined extension encodes left grouping as 123 and right grouping as 33."))

    add(valid_case("r1017_or_operand_forms", "R1017", ["single-or-operand", "or-chain", "and-before-or-precedence"], "positive-control", logical,
                   "EXPRESSIONS LEVEL 5 LOGICAL OK\n", [
        ("single-or-operand", "r1017-single-or-mut", [("  ok = true_a() .and. true_b()\n  if (.not. ok) error stop 'R1017:single-or-operand'", "  ok = true_a() .and. false_b()\n  if (.not. ok) error stop 'R1017:single-or-operand'")], "change the contained or-operand truth value"),
        ("or-chain", "r1017-or-chain-mut", [("  ok = false_a() .or. true_b()\n  if (.not. ok) error stop 'R1017:or-chain'", "  ok = false_a() .and. true_b()\n  if (.not. ok) error stop 'R1017:or-chain'")], "replace the or-op by a conforming and-op"),
        ("and-before-or-precedence", "r1017-and-before-or-mut", [("  ok = true_b() .or. false_a() .and. false_b()\n  if (.not. ok) error stop 'R1017:and-before-or'", "  ok = (true_b() .or. false_a()) .and. false_b()\n  if (.not. ok) error stop 'R1017:and-before-or'")], "add parentheses that override the AND-before-OR interpretation"),
    ], "R1017 admits an or-operand alone or .OR. chains, and the grammar places .AND. inside each or-operand."))
    add(invalid_case("r1017_missing_or_rhs", "R1017", "missing-right-or-operand-rejected", """program expr_r1017_missing_or_rhs
  implicit none
  logical :: ok
  ok = .false. .or.
  print *, ok
end program expr_r1017_missing_or_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair by appending the missing or-operand .true.; the completed expression evaluates true.", "R1017 requires an or-operand after a present or-op."))
    add(valid_case("r1017_missing_or_rhs_control", "R1017", ["missing-right-or-operand-rejected"], "positive-control", """program expr_r1017_missing_or_rhs_control
  implicit none
  logical :: ok
  ok = .false. .or. .true.
  if (.not. ok) error stop 'R1017:missing-or-control'
  write(*,'(a)') 'EXPRESSIONS R1017 MISSING OR RHS CONTROL OK'
end program expr_r1017_missing_or_rhs_control
""", "EXPRESSIONS R1017 MISSING OR RHS CONTROL OK\n", [
        ("missing-right-or-operand-rejected", "r1017-missing-or-control-mut", [("  ok = .false. .or. .true.\n  if (.not. ok) error stop 'R1017:missing-or-control'", "  ok = .false. .or. .false.\n  if (.not. ok) error stop 'R1017:missing-or-control'")], "change the supplied right or-operand in the conforming control"),
    ], "The control appends only the missing R1017 right or-operand."))

    add(valid_case("r1018_equiv_operand_forms", "R1018", ["single-equiv-operand", "eqv-chain", "neqv-chain"], "positive-control", logical,
                   "EXPRESSIONS LEVEL 5 LOGICAL OK\n", [
        ("single-equiv-operand", "r1018-single-equiv-mut", [("  ok = false_b() .or. true_a()\n  if (.not. ok) error stop 'R1018:single-equiv-operand'", "  ok = false_b() .or. false_a()\n  if (.not. ok) error stop 'R1018:single-equiv-operand'")], "change the contained equiv-operand truth value"),
        ("eqv-chain", "r1018-eqv-chain-mut", [("  ok = true_a() .eqv. true_b()\n  if (.not. ok) error stop 'R1018:eqv-chain'", "  ok = true_a() .neqv. true_b()\n  if (.not. ok) error stop 'R1018:eqv-chain'")], "replace .EQV. by sibling .NEQV."),
        ("neqv-chain", "r1018-neqv-chain-mut", [("  ok = true_a() .neqv. false_a()\n  if (.not. ok) error stop 'R1018:neqv-chain'", "  ok = true_a() .eqv. false_a()\n  if (.not. ok) error stop 'R1018:neqv-chain'")], "replace .NEQV. by sibling .EQV."),
    ], "R1018 admits an equiv-operand alone and chains joined by .EQV. or .NEQV.; exact truth tables supply the oracle."))
    add(invalid_case("r1018_missing_equiv_rhs", "R1018", "missing-right-equiv-operand-rejected", """program expr_r1018_missing_equiv_rhs
  implicit none
  logical :: ok
  ok = .true. .eqv.
  print *, ok
end program expr_r1018_missing_equiv_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair by appending the missing equiv-operand .false.; the completed expression evaluates false.", "R1018 requires an equiv-operand after a present equiv-op."))
    add(valid_case("r1018_missing_equiv_rhs_control", "R1018", ["missing-right-equiv-operand-rejected"], "positive-control", """program expr_r1018_missing_equiv_rhs_control
  implicit none
  logical :: ok
  ok = .true. .eqv. .false.
  if (ok) error stop 'R1018:missing-equiv-control'
  write(*,'(a)') 'EXPRESSIONS R1018 MISSING EQUIV RHS CONTROL OK'
end program expr_r1018_missing_equiv_rhs_control
""", "EXPRESSIONS R1018 MISSING EQUIV RHS CONTROL OK\n", [
        ("missing-right-equiv-operand-rejected", "r1018-missing-equiv-control-mut", [("  ok = .true. .eqv. .false.\n  if (ok) error stop 'R1018:missing-equiv-control'", "  ok = .true. .eqv. .true.\n  if (ok) error stop 'R1018:missing-equiv-control'")], "change the supplied right equiv-operand in the conforming control"),
    ], "The control appends only the missing R1018 right equiv-operand."))
    add(valid_case("r1018_defined_equiv_grouping", "R1018", ["left-recursive-equiv"], "effect", """module expr_r1018_defined_equiv_mod
  implicit none
  type :: token
    integer :: value
  end type token
  interface operator(.eqv.)
    module procedure join_eqv
  end interface
contains
  pure function join_eqv(lhs, rhs) result(out)
    type(token), intent(in) :: lhs, rhs
    type(token) :: out
    out%value = 10*lhs%value + rhs%value
  end function join_eqv
end module expr_r1018_defined_equiv_mod

program expr_r1018_defined_equiv_grouping
  use expr_r1018_defined_equiv_mod
  implicit none
  type(token) :: a, b, c, r
  a = token(1); b = token(2); c = token(3)
  r = a .eqv. b .eqv. c
  if (r%value /= 123) error stop 'R1018:left-recursive-equiv'
  write(*,'(a)') 'EXPRESSIONS R1018 DEFINED EQUIV GROUPING OK'
end program expr_r1018_defined_equiv_grouping
""", "EXPRESSIONS R1018 DEFINED EQUIV GROUPING OK\n", [
        ("left-recursive-equiv", "r1018-defined-equiv-right-group-mut", [("  r = a .eqv. b .eqv. c\n  if (r%value /= 123) error stop 'R1018:left-recursive-equiv'", "  r = a .eqv. (b .eqv. c)\n  if (r%value /= 123) error stop 'R1018:left-recursive-equiv'")], "parenthesize the right equivalence operation instead of the R1018 left-recursive grouping"),
    ], "R1018 is left-recursive for .EQV.; a non-associative defined extension encodes left grouping as 123 and right grouping as 33."))

    for rule, facets, muts, deriv in [
        ("R1019", ["dot-not-token"], [("dot-not-token", "r1019-dot-not-mut", [("  ok = .not. false_a()\n  if (.not. ok) error stop 'R1019:dot-not-token'", "  ok = false_a()\n  if (.not. ok) error stop 'R1019:dot-not-token'")], "remove the .NOT. token")], "R1019 defines the .NOT. token; the assertion observes its exact negation truth value."),
        ("R1020", ["dot-and-token"], [("dot-and-token", "r1020-dot-and-mut", [("  ok = true_a() .and. false_b()\n  if (ok) error stop 'R1020:dot-and-token'", "  ok = true_a() .or. false_b()\n  if (ok) error stop 'R1020:dot-and-token'")], "replace .AND. by sibling .OR.")], "R1020 defines the .AND. token; the assertion observes its exact conjunction truth value."),
        ("R1021", ["dot-or-token"], [("dot-or-token", "r1021-dot-or-mut", [("  ok = false_a() .or. true_a()\n  if (.not. ok) error stop 'R1021:dot-or-token'", "  ok = false_a() .and. true_a()\n  if (.not. ok) error stop 'R1021:dot-or-token'")], "replace .OR. by sibling .AND.")], "R1021 defines the .OR. token; the assertion observes its exact disjunction truth value."),
        ("R1022", ["dot-eqv-token", "dot-neqv-token"], [("dot-eqv-token", "r1022-dot-eqv-mut", [("  ok = true_b() .eqv. true_a()\n  if (.not. ok) error stop 'R1022:dot-eqv-token'", "  ok = true_b() .neqv. true_a()\n  if (.not. ok) error stop 'R1022:dot-eqv-token'")], "replace .EQV. by sibling .NEQV."), ("dot-neqv-token", "r1022-dot-neqv-mut", [("  ok = true_b() .neqv. false_b()\n  if (.not. ok) error stop 'R1022:dot-neqv-token'", "  ok = true_b() .eqv. false_b()\n  if (.not. ok) error stop 'R1022:dot-neqv-token'")], "replace .NEQV. by sibling .EQV.")], "R1022 defines the .EQV. and .NEQV. token alternatives; assertions observe exact truth-table results."),
    ]:
        add(valid_case(rule.lower() + "_token_forms", rule, facets, "positive-control", logical,
                       "EXPRESSIONS LEVEL 5 LOGICAL OK\n", muts, deriv))

    defined = defined_binary_source()
    add(valid_case("general_defined_binary_forms", "S10.1.2.9-001", SELECTED["S10.1.2.9-001"], "positive-control", defined,
                   "EXPRESSIONS DEFINED BINARY OK\n", [
        ("level-5-base", "s10129-level5-base-mut", [("  ok = .true. .and. .true.\n  if (.not. ok) error stop 'GEN:level5-base'", "  ok = .true. .and. .false.\n  if (.not. ok) error stop 'GEN:level5-base'")], "change the level-5 logical expression truth value"),
        ("defined-binary-after-intrinsic", "s10129-defined-after-intrinsic-mut", [("  x = 1 + 2 .join. 3 * 4\n  if (x /= 42) error stop 'GEN:defined-after-intrinsic'", "  x = (1 + 2 .join. 3) * 4\n  if (x /= 42) error stop 'GEN:defined-after-intrinsic'")], "add parentheses that change which operands feed the defined binary call"),
        ("defined-binary-left-chain", "s10129-defined-left-chain-mut", [("  x = 1 .join. 2 .join. 3\n  if (x /= 123) error stop 'GEN:defined-left-chain'", "  x = 1 .join. (2 .join. 3)\n  if (x /= 123) error stop 'GEN:defined-left-chain'")], "parenthesize the right defined-binary operation"),
        ("parenthesized-defined-binary-operand", "s10129-parenthesized-right-mut", [("  x = 1 .join. (2 .join. 3)\n  if (x /= 33) error stop 'GEN:parenthesized-defined-right'", "  x = 1 .join. 2 .join. 3\n  if (x /= 33) error stop 'GEN:parenthesized-defined-right'")], "remove the parentheses that make the right operand a defined-binary expression"),
    ], "10.1.2.9 p1 places defined binary operations below level-5 operands; the join function encodes its two integer operands exactly."))

    add(valid_case("r1023_expr_forms", "R1023", ["single-level-5", "defined-binary-operation", "left-recursive-defined-binary", "right-defined-binary-requires-parentheses"], "positive-control", defined,
                   "EXPRESSIONS DEFINED BINARY OK\n", [
        ("single-level-5", "r1023-single-level5-mut", [("  ok = .false. .or. .true.\n  if (.not. ok) error stop 'R1023:single-level5'", "  ok = .false. .or. .false.\n  if (.not. ok) error stop 'R1023:single-level5'")], "change the single level-5 expression truth value"),
        ("defined-binary-operation", "r1023-defined-operation-mut", [("  x = 4 .join. 5\n  if (x /= 45) error stop 'R1023:defined-operation'", "  x = 4 .join. 6\n  if (x /= 45) error stop 'R1023:defined-operation'")], "change the right level-5 operand of the defined binary operation"),
        ("left-recursive-defined-binary", "r1023-left-recursive-mut", [("  x = 6 .join. 7 .join. 8\n  if (x /= 678) error stop 'R1023:left-recursive-defined'", "  x = 6 .join. (7 .join. 8)\n  if (x /= 678) error stop 'R1023:left-recursive-defined'")], "parenthesize the right operation instead of the left-recursive form"),
        ("right-defined-binary-requires-parentheses", "r1023-right-parenthesized-mut", [("  x = 6 .join. (7 .join. 8)\n  if (x /= 138) error stop 'R1023:right-parenthesized'", "  x = 6 .join. 7 .join. 8\n  if (x /= 138) error stop 'R1023:right-parenthesized'")], "remove the parentheses that make the right operand a primary"),
    ], "R1023 admits a level-5 expression or a left-recursive defined-binary chain; encoded integer results distinguish groupings."))
    add(invalid_case("r1023_missing_level5_rhs", "R1023", "missing-right-level-5-rejected", """module expr_r1023_missing_rhs_mod
  implicit none
  interface operator(.join.)
    module procedure join_i
  end interface
contains
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
end module expr_r1023_missing_rhs_mod
program expr_r1023_missing_level5_rhs
  use expr_r1023_missing_rhs_mod
  implicit none
  integer :: x
  x = 1 .join.
  print *, x
end program expr_r1023_missing_level5_rhs
""", 16, ["syntax error", "Newline", "Syntax", "expression"], "Repair by appending the missing level-5 expression 2 after .join.; the completed defined operation evaluates 12.", "R1023 requires a level-5-expr after a present defined-binary-op."))
    add(valid_case("r1023_missing_level5_rhs_control", "R1023", ["missing-right-level-5-rejected"], "positive-control", """module expr_r1023_missing_rhs_control_mod
  implicit none
  interface operator(.join.)
    module procedure join_i
  end interface
contains
  pure integer function join_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    join_i = 10*lhs + rhs
  end function join_i
end module expr_r1023_missing_rhs_control_mod
program expr_r1023_missing_level5_rhs_control
  use expr_r1023_missing_rhs_control_mod
  implicit none
  integer :: x
  x = 1 .join. 2
  if (x /= 12) error stop 'R1023:missing-rhs-control'
  write(*,'(a)') 'EXPRESSIONS R1023 MISSING RHS CONTROL OK'
end program expr_r1023_missing_level5_rhs_control
""", "EXPRESSIONS R1023 MISSING RHS CONTROL OK\n", [
        ("missing-right-level-5-rejected", "r1023-missing-rhs-control-mut", [("  x = 1 .join. 2\n  if (x /= 12) error stop 'R1023:missing-rhs-control'", "  x = 1 .join. 3\n  if (x /= 12) error stop 'R1023:missing-rhs-control'")], "change the supplied right level-5 expression in the conforming control"),
    ], "The control appends only the missing R1023 right level-5 expression."))

    add(valid_case("r1024_defined_binary_tokens", "R1024", ["single-letter", "multiple-letters"], "positive-control", defined,
                   "EXPRESSIONS DEFINED BINARY OK\n", [
        ("single-letter", "r1024-single-letter-mut", [("  x = 2 .b. 3\n  if (x /= 32) error stop 'R1024:single-letter'", "  x = 2 .b. 4\n  if (x /= 32) error stop 'R1024:single-letter'")], "change the right operand of the single-letter operator"),
        ("multiple-letters", "r1024-multiple-letters-mut", [("  x = 2 .union. 3\n  if (x /= 203) error stop 'R1024:multiple-letters'", "  x = 3 .union. 3\n  if (x /= 203) error stop 'R1024:multiple-letters'")], "change the left operand of the multiple-letter operator"),
    ], "R1024 admits dotted letter sequences; .b. and .union. call distinct two-argument functions with exact integer results."))
    r1024_invalids = [
        ("r1024_missing_leading_dot", "missing-leading-dot-rejected", "  x = 1 b. 2", 4, "Repair to 'x = 1 .b. 2', preserving operands and function."),
        ("r1024_missing_trailing_dot", "missing-trailing-dot-rejected", "  x = 1 .b 2", 4, "Repair to 'x = 1 .b. 2', preserving operands and function."),
        ("r1024_digit_in_name", "digit-in-name-rejected", "  x = 1 .b1. 2", 4, "Repair to 'x = 1 .ba. 2', preserving the dotted-letter shape."),
    ]
    for variant, facet, bad_line, line, repair in r1024_invalids:
        control_op = ".ba." if "digit" in variant else ".b."
        control_name = "ba_i" if "digit" in variant else "b_i"
        add(invalid_case(variant, "R1024", facet, f"""module expr_{variant}_mod
  implicit none
  interface operator({control_op})
    module procedure {control_name}
  end interface
contains
  pure integer function {control_name}(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    {control_name} = 10*lhs + rhs
  end function {control_name}
end module expr_{variant}_mod
program expr_{variant}
  use expr_{variant}_mod
  implicit none
  integer :: x
{bad_line}
  print *, x
end program expr_{variant}
""", 16, ["Unclassifiable", "statement", "syntax error", "tokenizer", "Bad character"], repair, "R1024 requires a leading dot, letters only, and a trailing dot in a defined-binary-op."))
        control_variant = variant + "_control"
        add(valid_case(control_variant, "R1024", [facet], "positive-control", f"""module expr_{control_variant}_mod
  implicit none
  interface operator({control_op})
    module procedure {control_name}
  end interface
contains
  pure integer function {control_name}(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    {control_name} = 10*lhs + rhs
  end function {control_name}
end module expr_{control_variant}_mod
program expr_{control_variant}
  use expr_{control_variant}_mod
  implicit none
  integer :: x
  x = 1 {control_op} 2
  if (x /= 12) error stop 'R1024:{facet}'
  write(*,'(a)') 'EXPRESSIONS R1024 {facet.upper()} CONTROL OK'
end program expr_{control_variant}
""", f"EXPRESSIONS R1024 {facet.upper()} CONTROL OK\n", [
            (facet, variant + "-control-mut", [(f"  x = 1 {control_op} 2\n  if (x /= 12) error stop 'R1024:{facet}'", f"  x = 1 {control_op} 3\n  if (x /= 12) error stop 'R1024:{facet}'")], "change the supplied right operand in the conforming spelling control"),
        ], "The control repairs only the R1024 operator spelling and observes the encoded function result."))

    add(valid_case("c1006_length_control", "C1006", ["sixty-three-letter-control"], "positive-control", defined,
                   "EXPRESSIONS DEFINED BINARY OK\n", [
        ("sixty-three-letter-control", "c1006-sixty-three-mut", [(f"  x = 2 .{'a'*63}. 3\n  if (x /= 2003) error stop 'C1006:sixty-three'", f"  x = 2 .{'a'*63}. 4\n  if (x /= 2003) error stop 'C1006:sixty-three'")], "change the right operand of the 63-letter defined-binary operator"),
    ], "C1006 permits no more than 63 letters; the 63-letter operator is defined and returns an exact encoded value."))
    add(invalid_case("c1006_sixty_four_letters", "C1006", "sixty-four-letter-rejected", """module expr_c1006_sixty_four_letters_mod
  implicit none
  interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)
    module procedure long_i
  end interface
contains
  pure integer function long_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    long_i = 10*lhs + rhs
  end function long_i
end module expr_c1006_sixty_four_letters_mod
program expr_c1006_sixty_four_letters
  use expr_c1006_sixty_four_letters_mod
  implicit none
  integer :: x
  x = 1 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 2
  print *, x
end program expr_c1006_sixty_four_letters
""", 3, ["too long", "63", "64"], "Repair by removing one letter from the operator name in both the interface and expression; the 63-letter control computes 12.", "C1006 prohibits a defined-binary-op containing more than 63 letters."))
    add(valid_case("c1006_sixty_four_letters_control", "C1006", ["sixty-four-letter-rejected"], "positive-control", """module expr_c1006_sixty_four_letters_control_mod
  implicit none
  interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)
    module procedure long_i
  end interface
contains
  pure integer function long_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    long_i = 10*lhs + rhs
  end function long_i
end module expr_c1006_sixty_four_letters_control_mod
program expr_c1006_sixty_four_letters_control
  use expr_c1006_sixty_four_letters_control_mod
  implicit none
  integer :: x
  x = 1 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 2
  if (x /= 12) error stop 'C1006:sixty-four-control'
  write(*,'(a)') 'EXPRESSIONS C1006 SIXTY FOUR CONTROL OK'
end program expr_c1006_sixty_four_letters_control
""", "EXPRESSIONS C1006 SIXTY FOUR CONTROL OK\n", [
        ("sixty-four-letter-rejected", "c1006-sixty-four-control-mut", [("  x = 1 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 2\n  if (x /= 12) error stop 'C1006:sixty-four-control'", "  x = 1 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 3\n  if (x /= 12) error stop 'C1006:sixty-four-control'")], "change the supplied right operand in the conforming 63-letter control"),
    ], "The control repairs only the C1006 length by using the maximum 63-letter defined-binary-op spelling."))

    c1006_reserved_controls = [
        ("c1006_logical_true_spelling", "logical-true-spelling-rejected", ".true.", ".truth.", "truth_i", "TRUE"),
        ("c1006_logical_false_spelling", "logical-false-spelling-rejected", ".false.", ".falsity.", "falsity_i", "FALSE"),
    ]
    for variant, facet, bad_op, control_op, function_name, label in c1006_reserved_controls:
        add(invalid_case(variant, "C1006", facet, f"""module expr_{variant}_mod
  implicit none
  interface operator({bad_op})
    module procedure {function_name}
  end interface
contains
  pure integer function {function_name}(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    {function_name} = 10*lhs + rhs
  end function {function_name}
end module expr_{variant}_mod
program expr_{variant}
  use expr_{variant}_mod
  implicit none
  integer :: x
  x = 1 {bad_op} 2
  print *, x
end program expr_{variant}
""", 3, ["cannot be used", "logical", "unexpected", "syntax"], f"Repair by changing the operator spelling to {control_op} in the interface and expression; the control computes 12.", "C1006 prohibits a defined-binary-op from being the same as a logical-literal-constant."))
        control_variant = variant + "_control"
        add(valid_case(control_variant, "C1006", [facet], "positive-control", f"""module expr_{control_variant}_mod
  implicit none
  interface operator({control_op})
    module procedure {function_name}
  end interface
contains
  pure integer function {function_name}(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    {function_name} = 10*lhs + rhs
  end function {function_name}
end module expr_{control_variant}_mod
program expr_{control_variant}
  use expr_{control_variant}_mod
  implicit none
  integer :: x
  x = 1 {control_op} 2
  if (x /= 12) error stop 'C1006:{facet}'
  write(*,'(a)') 'EXPRESSIONS C1006 {label} CONTROL OK'
end program expr_{control_variant}
""", f"EXPRESSIONS C1006 {label} CONTROL OK\n", [
            (facet, variant + "-control-mut", [(f"  x = 1 {control_op} 2\n  if (x /= 12) error stop 'C1006:{facet}'", f"  x = 1 {control_op} 3\n  if (x /= 12) error stop 'C1006:{facet}'")], "change the supplied right operand in the conforming logical-literal spelling control"),
        ], f"The control repairs only the C1006 reserved logical-literal spelling by using {control_op}."))


    prec = precedence_source()
    add(valid_case("operator_precedence_table", "S10.1.3-001", SELECTED["S10.1.3-001"], "effect", prec,
                   "EXPRESSIONS PRECEDENCE OK\n", [
        ("power-before-unary-minus", "s1013-power-before-unary-mut", [("  x = -2**2\n  if (x /= -4) error stop 'PREC:power-before-unary-minus'", "  x = (-2)**2\n  if (x /= -4) error stop 'PREC:power-before-unary-minus'")], "add parentheses to override exponentiation before unary minus"),
        ("multiply-before-binary-plus", "s1013-multiply-before-plus-mut", [("  x = 2+3*4\n  if (x /= 14) error stop 'PREC:multiply-before-plus'", "  x = (2+3)*4\n  if (x /= 14) error stop 'PREC:multiply-before-plus'")], "add parentheses to override multiply before plus"),
        ("unary-before-binary-plus", "s1013-unary-before-plus-mut", [("  x = -3 + 10\n  if (x /= 7) error stop 'PREC:unary-before-binary-plus'", "  x = -(3 + 10)\n  if (x /= 7) error stop 'PREC:unary-before-binary-plus'")], "add parentheses to change the unary operand"),
        ("character-before-relational", "s1013-char-before-rel-mut", [("  ok = a // b == c\n  if (.not. ok) error stop 'PREC:character-before-relational'", "  ok = a // (b == c)\n  if (.not. ok) error stop 'PREC:character-before-relational'")], "parenthesize the relational operation as the right operand of defined //"),
        ("relational-before-logical-or", "s1013-rel-before-or-mut", [("  ok = .false. .or. 2+3 >= 5\n  if (.not. ok) error stop 'PREC:relational-before-or'", "  ok = .false. .or. (2+3 > 5)\n  if (.not. ok) error stop 'PREC:relational-before-or'")], "parenthesize and alter the relational operand to make the logical result differ"),
        ("not-before-and", "s1013-not-before-and-mut", [("  ok = .not. .false. .and. .false.\n  if (ok) error stop 'PREC:not-before-and'", "  ok = .not. (.false. .and. .false.)\n  if (ok) error stop 'PREC:not-before-and'")], "add parentheses to override NOT before AND"),
        ("and-before-or", "s1013-and-before-or-mut", [("  ok = .true. .or. .false. .and. .false.\n  if (.not. ok) error stop 'PREC:and-before-or'", "  ok = (.true. .or. .false.) .and. .false.\n  if (.not. ok) error stop 'PREC:and-before-or'")], "add parentheses to override AND before OR"),
        ("or-before-eqv", "s1013-or-before-eqv-mut", [("  ok = .true. .or. .false. .eqv. .false.\n  if (ok) error stop 'PREC:or-before-eqv'", "  ok = .true. .or. (.false. .eqv. .false.)\n  if (ok) error stop 'PREC:or-before-eqv'")], "add parentheses to override OR before EQV"),
        ("defined-binary-lowest", "s1013-defined-binary-lowest-mut", [("  x = 1 + 2 .join. 3\n  if (x /= 33) error stop 'PREC:defined-binary-lowest'", "  x = 1 + (2 .join. 3)\n  if (x /= 33) error stop 'PREC:defined-binary-lowest'")], "add parentheses to force the defined binary operation before addition"),
        ("parentheses-override-category-precedence", "s1013-parentheses-category-mut", [("  x = (2+3)*4\n  if (x /= 20) error stop 'PREC:parentheses-category'", "  x = 2+3*4\n  if (x /= 20) error stop 'PREC:parentheses-category'")], "remove parentheses that override category precedence"),
    ], "10.1.3 p1/Table 10.1 gives category precedence; exact values differ when parentheses change the grouping."))

    add(valid_case("defined_operation_precedence", "S10.1.3-002", SELECTED["S10.1.3-002"], "effect", prec,
                   "EXPRESSIONS PRECEDENCE OK\n", [
        ("extended-intrinsic-operator-precedence", "s1013p2-extended-intrinsic-mut", [("  r = a + b ** c\n  if (r%value /= 123) error stop 'P2:extended-intrinsic-precedence'", "  r = (a + b) ** c\n  if (r%value /= 123) error stop 'P2:extended-intrinsic-precedence'")], "add parentheses to override the extended ** precedence"),
        ("defined-unary-operator-highest", "s1013p2-defined-unary-mut", [("  r = .neg. a * b\n  if (r%value /= 1012) error stop 'P2:defined-unary-highest'", "  r = .neg. (a * b)\n  if (r%value /= 1012) error stop 'P2:defined-unary-highest'")], "add parentheses to make multiplication the operand of the defined unary operator"),
        ("defined-binary-operator-lowest", "s1013p2-defined-binary-mut", [("  x = 4 + 5 .join. 6\n  if (x /= 96) error stop 'P2:defined-binary-lowest'", "  x = 4 + (5 .join. 6)\n  if (x /= 96) error stop 'P2:defined-binary-lowest'")], "add parentheses to force the defined binary operation before addition"),
        ("dotted-name-not-intrinsic-symbol-precedence", "s1013p2-dotted-name-mut", [("  x = 2 * 3 .starstar. 4\n  if (x /= 64) error stop 'P2:dotted-name-lowest'", "  x = 2 * 3 ** 4\n  if (x /= 64) error stop 'P2:dotted-name-lowest'")], "replace dotted .starstar. by intrinsic ** with its higher precedence"),
    ], "10.1.3 p2 gives each defined operation the precedence of its operator; encoded results distinguish operator tokens."))

    add(valid_case("same_class_grouping", "S10.1.3-003", SELECTED["S10.1.3-003"], "effect", prec,
                   "EXPRESSIONS PRECEDENCE OK\n", [
        ("left-grouped-subtraction", "s1013p3-left-sub-mut", [("  x = 10-3-2\n  if (x /= 5) error stop 'P3:left-subtraction'", "  x = 10-(3-2)\n  if (x /= 5) error stop 'P3:left-subtraction'")], "add parentheses to override left grouping of subtraction"),
        ("left-grouped-division", "s1013p3-left-div-mut", [("  x = 64/4/2\n  if (x /= 8) error stop 'P3:left-division'", "  x = 64/(4/2)\n  if (x /= 8) error stop 'P3:left-division'")], "add parentheses to override left grouping of division"),
        ("right-grouped-exponentiation", "s1013p3-right-exp-mut", [("  x = 2**3**2\n  if (x /= 512) error stop 'P3:right-exponentiation'", "  x = (2**3)**2\n  if (x /= 512) error stop 'P3:right-exponentiation'")], "add parentheses to override right grouping of exponentiation"),
        ("left-grouped-concatenation-boundary", "s1013p3-left-concat-mut", [("  r = a // b // c\n  if (r%value /= 456) error stop 'P3:left-concat-boundary'", "  r = a // (b // c)\n  if (r%value /= 456) error stop 'P3:left-concat-boundary'")], "add parentheses to override left grouping of a non-associative defined // extension"),
        ("logical-same-class-grouping-boundary", "s1013p3-logical-same-mut", [("  r = a .or. b .or. c\n  if (r%value /= 123) error stop 'P3:logical-same-class'", "  r = a .or. (b .or. c)\n  if (r%value /= 123) error stop 'P3:logical-same-class'")], "add parentheses to override left grouping of a non-associative defined .OR. extension"),
        ("parentheses-override-same-class-grouping", "s1013p3-parentheses-same-mut", [("  x = 10-(3-2)\n  if (x /= 9) error stop 'P3:parentheses-same-class'", "  x = 10-3-2\n  if (x /= 9) error stop 'P3:parentheses-same-class'")], "remove parentheses that override same-class subtraction grouping"),
    ], "10.1.3 p3 gives same-class grouping from 10.1.2 unless parentheses change it; exact integer/component values distinguish the groupings."))

    return specs


def manifest(spec):
    item = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
    if spec["kind"] == "invalid":
        item["expect"] = dict(phase="compile", step="source", outcome="diagnose",
                              diagnostic=dict(file="source.f90", line=spec["line"],
                                              contains_any=spec["messages"], excludes_any=EXCLUDES))
    else:
        item["link"] = dict(driver="fortran", objects=["source.o"], output="program")
        item["expect"] = dict(phase="run", outcome="success", exit_code=0,
                              stdout=spec["completion"], stderr="")
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
        pending = owner.setdefault("pending", {})
        for facet in facets:
            if facet in owner["facets"]:
                pending.pop(facet, None)
        for facet, note in PENDING_NOTES.get(rule, {}).items():
            if facet in owner["facets"]:
                pending[facet] = note
        if not pending:
            owner["pending"] = {}
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
        "the bounded batch304 fixtures below supply selected cases and mutation/diagnostic plans, not oracle approval, "
        "fixture approval, source-review renewal, or universal coverage.")
    selected_here = [rule for rule in SELECTED if rule in {row["id"] for row in catalogue["requirements"]}]
    summary = (
        SUMMARY_BEGIN + "\n"
        f"## Batch304 expression fixtures for {section}\n\n"
        f"Generated batch304 fixtures cover selected facets for: {', '.join(selected_here)}. Runtime cases use exact integer, "
        "logical, character LEN/value, and derived-operation component oracles. Diagnostic cases are line-anchored one-property malformed forms with "
        "compiled conforming controls. Feature mutations are permanent and checked on both the reference gfortran and frozen LFortran target. "
        "Facets not listed remain pending for the recorded reasons.\n"
        + SUMMARY_END)
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
            raise SystemExit("stale expressions 10.1.2.8-10.1.3 fixtures: " + ", ".join(stale))
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
    root = Path(root).resolve()
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
