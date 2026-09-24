#!/usr/bin/env python3
"""Fixtures for Fortran 2023 expression grammar levels 2 through 4."""

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
PREFIX = "expressions_10_1_2_5_10_1_2_7_"
BUILD_ROOT = ".expressions_10_1_2_5_10_1_2_7_mutation_check"
SUMMARY_BEGIN = "<!-- BEGIN EXPRESSIONS 10.1.2.5-10.1.2.7 FIXTURES -->"
SUMMARY_END = "<!-- END EXPRESSIONS 10.1.2.5-10.1.2.7 FIXTURES -->"

CATALOGUES = {
    "10.1.2.5": "doc/catalogues/level_2_expressions_10_1_2_5.json",
    "10.1.2.6": "doc/catalogues/level_3_expressions_10_1_2_6.json",
    "10.1.2.7": "doc/catalogues/level_4_expressions_10_1_2_7.json",
}
VIEWS = {
    "10.1.2.5": "doc/fortran_2023_10_1_2_5.md",
    "10.1.2.6": "doc/fortran_2023_10_1_2_6.md",
    "10.1.2.7": "doc/fortran_2023_10_1_2_7.md",
}

EXCLUDES = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal compiler error", "Internal Compiler Error", "ASR verify", "module failed verification",
    "LLVM ERROR", "out of memory", "segmentation fault", "stack trace",
]

SELECTED = {
    "S10.1.2.5-001": ["level-1-base", "power-layer", "multiply-divide-layer", "add-subtract-layer"],
    "R1005": ["level-1-only", "single-power", "right-recursive-power", "missing-right-mult-operand-rejected"],
    "R1006": ["single-mult-operand", "multiplication-chain", "division-chain", "left-recursive-mixed-chain", "missing-right-mult-operand-rejected"],
    "R1007": ["plain-add-operand", "unary-plus", "unary-minus", "binary-plus", "binary-minus", "left-recursive-add-chain", "missing-add-operand-rejected"],
    "R1008": ["double-asterisk-token", "single-asterisk-not-power"],
    "R1009": ["asterisk-token", "slash-token"],
    "R1010": ["plus-token", "minus-token", "unary-position", "binary-position"],
    "S10.1.2.6-001": ["level-2-base", "concatenation-layer", "left-concatenation-chain"],
    "R1011": ["single-level-2", "single-concat", "left-recursive-concat", "missing-right-level-2-rejected"],
    "R1012": ["double-slash-token"],
    "S10.1.2.7-001": ["level-3-base", "single-relation-layer"],
    "R1013": ["single-level-3", "relational-operation", "chained-relation-rejected", "missing-right-level-3-rejected"],
    "R1014": ["dot-eq", "dot-ne", "dot-lt", "dot-le", "dot-gt", "dot-ge", "eqeq", "slash-eq", "lt", "le", "gt", "ge"],
}

PENDING_NOTES = {
    "S10.1.2.7-001": {
        "no-unparenthesized-relation-chain": "PENDING batch295: the diagnostic obligation is supplied by numbered R1013; this non-numbered summary facet is left pending rather than binding a rejection case to prose p1."
    },
    "R1009": {
        "other-token-rejected": "PENDING batch295: left pending because substituting a non-'*'/'/' token between otherwise valid numeric operands is parsed either as another expression level (for + or -) or as a defined/lexical operator case; this packet has no one-property diagnostic whose attribution is only R1009 membership."
    },
    "R1010": {
        "other-token-rejected": "PENDING batch295: left pending because a token that is not '+' or '-' in the R1007 add-op slot either belongs to another expression level or to lexical/defined-operator syntax; this packet has no isolated R1010-only diagnostic."
    },
    "R1012": {
        "single-slash-not-concat": "PENDING batch295: left pending because a single '/' between character operands is first a valid mult-op token and the observable rejection is operand-type interpretation, not an isolated concat-op spelling diagnostic."
    },
    "R1014": {
        "non-rel-op-rejected": "PENDING batch295: left pending because candidate replacements such as defined-operator spellings or doubled relational tokens introduce lower-level defined-operation or lexical errors rather than a one-property R1014 rel-op membership diagnostic."
    },
}

ORACLE_PREFIX = "Batch295 expressions 10.1.2.5-10.1.2.7 fixtures: "
LIMIT_PREFIX = "Batch295 expressions 10.1.2.5-10.1.2.7 boundaries: "

ORACLE_TEXT = {
    "S10.1.2.5-001": ORACLE_PREFIX + (
        "one run/positive-control/f2023 program observes exact integer values for a level-1 base expression 2, "
        "right-recursive power 2**3**2=512, left-recursive multiplication/division 24/3*2=16, "
        "and add/subtract forms including 10-3-2=5 and -2**2=-4. Each assertion has a conforming "
        "feature mutation that changes the relevant operator, operand, or grouping and fails at run time."
    ),
    "R1005": ORACLE_PREFIX + (
        "the level-2 numeric program observes a bare level-1 literal 4, single power 2**3=8, and "
        "right-recursive power 2**3**2=512; a diagnostic fixture isolates a missing mult-operand after a valid '**'."
    ),
    "R1006": ORACLE_PREFIX + (
        "the numeric program observes add-operands that are a single mult-operand 2**3, a multiplication chain 2*3*4=24, "
        "a division chain 24/3/2=4, and mixed left recursion 24/3*2=16; a diagnostic fixture isolates a missing mult-operand after '*'."
    ),
    "R1007": ORACLE_PREFIX + (
        "the numeric program observes a plain add-operand 2*3, unary +5, unary -5, binary 2+3 and 7-2, "
        "and left-recursive 10-3-2=5; a diagnostic fixture and compiled one-property control isolate a missing add-operand after '+'."
    ),
    "R1008": ORACLE_PREFIX + (
        "the numeric program observes the '**' token in 2**3=8 and a boundary assertion that 2*3 is multiplication, not power. "
        "Feature mutations swap between conforming '*' and '**' forms with distinct exact integer results."
    ),
    "R1009": ORACLE_PREFIX + (
        "the numeric program observes '*' in 2*4=8 and '/' in 8/2=4 with sibling operator substitutions that stay conforming and fail the literal integer assertions."
    ),
    "R1010": ORACLE_PREFIX + (
        "the numeric program observes '+' and '-' in unary and binary positions using exact integer assertions; sibling substitutions or operand changes make each assertion load-bearing."
    ),
    "S10.1.2.6-001": ORACLE_PREFIX + (
        "character fixtures observe a level-2 character expression by direct LEN/value checks, intrinsic concatenation 'ab'//'cd' with LEN 4 and value 'abcd', "
        "and a non-associative defined extension of // where an unparenthesized three-operand chain produces the left-grouped value."
    ),
    "R1011": ORACLE_PREFIX + (
        "character fixtures observe a single level-2 expression, a single intrinsic concat, and a left-recursive defined-// chain; a diagnostic fixture and compiled one-property control isolate a missing level-2 expression after a valid '//'."
    ),
    "R1012": ORACLE_PREFIX + (
        "the intrinsic concatenation fixture observes the '//' token with direct LEN('ab'//'cd') and value checks; a feature mutation replaces the construct with another conforming concatenation of different length/value."
    ),
    "S10.1.2.7-001": ORACLE_PREFIX + (
        "relational fixtures observe a level-3 expression without rel-op, one relation 2<3, and diagnostics for an unparenthesized relation chain. Runtime operators use exact logical results; character equality checks first inquire LEN on each operand to show blank-padding width."
    ),
    "R1013": ORACLE_PREFIX + (
        "relational fixtures observe a single level-3 expression and one relational operation; diagnostics plus compiled one-property controls isolate a second unparenthesized rel-op and a missing right level-3 expression. The chained-relation negative is a genuine frozen-LFortran defect case: gfortran diagnoses it while the target accepts it as an extension."
    ),
    "R1014": ORACLE_PREFIX + (
        "one runtime fixture observes all twelve rel-op spellings with exact logical assertions. .EQ. and == are both exercised on character operands of lengths 1 and 2 after direct LEN checks, relying on blank padding; ordering operators use integers to avoid character collating-order dependence."
    ),
}

LIMIT_TEXT = {
    rule: LIMIT_PREFIX + (
        "Only the listed selected facets are represented by batch295 fixtures. Existing source review state, evidence approval, "
        "rollout progress, xfail policy, and unrelated facets are not changed. Remaining pending facets are left for the reasons recorded in pending. "
        "All runtime oracles use exact integer, logical, character LEN, or literal character equality properties and no real arithmetic, evaluation order, address, or compiler-consensus property."
    ) for rule in SELECTED
}
LIMIT_TEXT["R1009"] += " The other-token-rejected facet remains pending: no isolated one-property R1009-only diagnostic was identified."
LIMIT_TEXT["R1010"] += " The other-token-rejected facet remains pending: no isolated one-property R1010-only diagnostic was identified."
LIMIT_TEXT["R1012"] += " The single-slash-not-concat facet remains pending because single slash is a valid mult-op token before character operand validity is considered."
LIMIT_TEXT["R1013"] += " The chained-relation diagnostic is shipped as a genuine LFortran defect: gfortran diagnoses the isolated R1013 violation, while the frozen target accepts it with an extension warning."
LIMIT_TEXT["R1014"] += " The non-rel-op-rejected facet remains pending: candidate malformed tokens were not attributable solely to R1014."


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant, rule, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + "_" + kind + "__" + PREFIX + variant


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
    spec = dict(id=identifier(variant, rule, "valid"), variant=variant, rule=rule, facets=list(facets),
                kind="valid", evidence=evidence, source=source, completion=completion, mutations=[],
                derivation=derivation)
    for facet, name, pairs, rationale in mutations:
        if facet not in facets:
            raise ValueError(f"mutation {name} names unowned facet {facet}")
        mutated = apply_pairs(source, pairs)
        spec["mutations"].append(dict(id=name, facet=facet, replacements=pairs, source=mutated, rationale=rationale))
    return spec


def invalid_case(variant, rule, facet, source, line, messages, repair, derivation):
    return dict(id=identifier(variant, rule, "invalid"), variant=variant, rule=rule, facets=[facet],
                kind="invalid", evidence="effect", source=source, line=line, messages=list(messages),
                repair=repair, derivation=derivation, mutations=[])


def numeric_source():
    return """program expr_l2_numeric_layers
  implicit none
  integer :: checks, x
  checks = 0
  x = 2
  if (x /= 2) error stop 'L2:s-level1-base'
  checks = checks + 1
  x = 3**2**3
  if (x /= 6561) error stop 'L2:s-power-layer'
  checks = checks + 1
  x = 30/5*3
  if (x /= 18) error stop 'L2:s-multiply-divide-layer'
  checks = checks + 1
  x = 12-4+1
  if (x /= 9) error stop 'L2:s-add-subtract-layer'
  checks = checks + 1
  x = 4
  if (x /= 4) error stop 'L2:r1005-level1-only'
  checks = checks + 1
  x = 2**3
  if (x /= 8) error stop 'L2:r1005-single-power'
  checks = checks + 1
  x = 2**3**2
  if (x /= 512) error stop 'L2:r1005-power-right'
  checks = checks + 1
  x = 3**2
  if (x /= 9) error stop 'L2:r1006-single-mult-operand'
  checks = checks + 1
  x = 2*3*4
  if (x /= 24) error stop 'L2:multiply-chain'
  checks = checks + 1
  x = 24/3/2
  if (x /= 4) error stop 'L2:division-chain'
  checks = checks + 1
  x = 24/3*2
  if (x /= 16) error stop 'L2:mixed-chain'
  checks = checks + 1
  x = 2*3
  if (x /= 6) error stop 'L2:plain-add-operand'
  checks = checks + 1
  x = +5
  if (x /= 5) error stop 'L2:unary-plus'
  checks = checks + 1
  x = -2**2
  if (x /= -4) error stop 'L2:unary-minus'
  checks = checks + 1
  x = 2+3
  if (x /= 5) error stop 'L2:binary-plus'
  checks = checks + 1
  x = 7-2
  if (x /= 5) error stop 'L2:binary-minus'
  checks = checks + 1
  x = 10-3-2
  if (x /= 5) error stop 'L2:add-left'
  checks = checks + 1
  x = 4**2
  if (x /= 16) error stop 'L2:double-asterisk-token'
  checks = checks + 1
  x = 3*2
  if (x /= 6) error stop 'L2:single-star-not-power'
  checks = checks + 1
  x = 2*4
  if (x /= 8) error stop 'L2:asterisk-token'
  checks = checks + 1
  x = 8/2
  if (x /= 4) error stop 'L2:slash-token'
  checks = checks + 1
  x = 4+5
  if (x /= 9) error stop 'L2:plus-token'
  checks = checks + 1
  x = 9-4
  if (x /= 5) error stop 'L2:minus-token'
  checks = checks + 1
  x = -6
  if (x /= -6) error stop 'L2:unary-position'
  checks = checks + 1
  x = 6+2
  if (x /= 8) error stop 'L2:binary-position'
  checks = checks + 1
  if (checks /= 25) error stop 'L2:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 2 NUMERIC OK'
end program expr_l2_numeric_layers
"""

def source_specs():
    specs = {}
    def add(spec):
        if spec["id"] in specs:
            raise ValueError("duplicate spec id " + spec["id"])
        specs[spec["id"]] = spec

    source = numeric_source()
    add(valid_case("level2_numeric_layers", "S10.1.2.5-001", SELECTED["S10.1.2.5-001"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("level-1-base", "level1-base-literal", [("  x = 2\n  if (x /= 2) error stop 'L2:s-level1-base'", "  x = 3\n  if (x /= 2) error stop 'L2:s-level1-base'")], "change the level-1 literal admitted as level-2"),
        ("power-layer", "power-layer-parenthesized-left", [("  x = 3**2**3\n  if (x /= 6561) error stop 'L2:s-power-layer'", "  x = (3**2)**3\n  if (x /= 6561) error stop 'L2:s-power-layer'")], "insert conforming parentheses that change power grouping"),
        ("multiply-divide-layer", "multiply-divide-right-group", [("  x = 30/5*3\n  if (x /= 18) error stop 'L2:s-multiply-divide-layer'", "  x = 30/(5*3)\n  if (x /= 18) error stop 'L2:s-multiply-divide-layer'")], "insert conforming parentheses that change mult/div grouping"),
        ("add-subtract-layer", "add-subtract-right-group", [("  x = 12-4+1\n  if (x /= 9) error stop 'L2:s-add-subtract-layer'", "  x = 12-(4+1)\n  if (x /= 9) error stop 'L2:s-add-subtract-layer'")], "insert conforming parentheses that change add/subtract grouping"),
    ], "10.1.2.5 p1 defines level-2 expressions as level-1 forms optionally involving power, mult, and add operators."))

    add(valid_case("r1005_power_forms", "R1005", ["level-1-only", "single-power", "right-recursive-power"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("level-1-only", "r1005-level1-only-literal", [("  x = 4\n  if (x /= 4) error stop 'L2:r1005-level1-only'", "  x = 5\n  if (x /= 4) error stop 'L2:r1005-level1-only'")], "change the bare level-1 expression used as a mult-operand"),
        ("single-power", "r1005-single-power-operator", [("  x = 2**3\n  if (x /= 8) error stop 'L2:r1005-single-power'", "  x = 2*3\n  if (x /= 8) error stop 'L2:r1005-single-power'")], "replace the conforming power operation with conforming multiplication"),
        ("right-recursive-power", "r1005-right-recursive-parentheses", [("  x = 2**3**2\n  if (x /= 512) error stop 'L2:r1005-power-right'", "  x = (2**3)**2\n  if (x /= 512) error stop 'L2:r1005-power-right'")], "change right recursion to explicit left grouping"),
    ], "R1005 admits a level-1-expr optionally followed by ** and another mult-operand, making power right-recursive."))

    add(valid_case("r1006_mult_forms", "R1006", ["single-mult-operand", "multiplication-chain", "division-chain", "left-recursive-mixed-chain"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("single-mult-operand", "r1006-single-mult-operand", [("  x = 3**2\n  if (x /= 9) error stop 'L2:r1006-single-mult-operand'", "  x = 3**3\n  if (x /= 9) error stop 'L2:r1006-single-mult-operand'")], "change the single mult-operand value"),
        ("multiplication-chain", "r1006-multiply-chain-operand", [("  x = 2*3*4\n  if (x /= 24) error stop 'L2:multiply-chain'", "  x = 2*3*5\n  if (x /= 24) error stop 'L2:multiply-chain'")], "change one operand in a conforming multiplication chain"),
        ("division-chain", "r1006-division-right-group", [("  x = 24/3/2\n  if (x /= 4) error stop 'L2:division-chain'", "  x = 24/(3/2)\n  if (x /= 4) error stop 'L2:division-chain'")], "insert conforming parentheses that change left-recursive division"),
        ("left-recursive-mixed-chain", "r1006-mixed-right-group", [("  x = 24/3*2\n  if (x /= 16) error stop 'L2:mixed-chain'", "  x = 24/(3*2)\n  if (x /= 16) error stop 'L2:mixed-chain'")], "insert conforming parentheses that change mixed mult/div grouping"),
    ], "R1006 builds an add-operand as a left-recursive chain of mult-operands joined by * or /."))

    add(valid_case("r1007_add_forms", "R1007", ["plain-add-operand", "unary-plus", "unary-minus", "binary-plus", "binary-minus", "left-recursive-add-chain"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("plain-add-operand", "r1007-plain-add-operand", [("  x = 2*3\n  if (x /= 6) error stop 'L2:plain-add-operand'", "  x = 2*4\n  if (x /= 6) error stop 'L2:plain-add-operand'")], "change the add-operand value"),
        ("unary-plus", "r1007-unary-plus-sign", [("  x = +5\n  if (x /= 5) error stop 'L2:unary-plus'", "  x = -5\n  if (x /= 5) error stop 'L2:unary-plus'")], "replace unary plus with conforming unary minus"),
        ("unary-minus", "r1007-unary-minus-sign", [("  x = -2**2\n  if (x /= -4) error stop 'L2:unary-minus'", "  x = +2**2\n  if (x /= -4) error stop 'L2:unary-minus'")], "replace unary minus with conforming unary plus"),
        ("binary-plus", "r1007-binary-plus-token", [("  x = 2+3\n  if (x /= 5) error stop 'L2:binary-plus'", "  x = 2*3\n  if (x /= 5) error stop 'L2:binary-plus'")], "replace binary plus with a conforming lower-level operator"),
        ("binary-minus", "r1007-binary-minus-token", [("  x = 7-2\n  if (x /= 5) error stop 'L2:binary-minus'", "  x = 7+2\n  if (x /= 5) error stop 'L2:binary-minus'")], "replace binary minus with conforming binary plus"),
        ("left-recursive-add-chain", "r1007-add-chain-right-group", [("  x = 10-3-2\n  if (x /= 5) error stop 'L2:add-left'", "  x = 10-(3-2)\n  if (x /= 5) error stop 'L2:add-left'")], "insert conforming parentheses that change add/subtract recursion"),
    ], "R1007 admits a plain add-operand, unary add-op, or a left-recursive level-2 add-op chain."))

    add(valid_case("r1008_power_token", "R1008", SELECTED["R1008"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("double-asterisk-token", "r1008-double-asterisk-token", [("  x = 4**2\n  if (x /= 16) error stop 'L2:double-asterisk-token'", "  x = 4*2\n  if (x /= 16) error stop 'L2:double-asterisk-token'")], "replace the ** power token with conforming multiplication"),
        ("single-asterisk-not-power", "r1008-single-asterisk-boundary", [("  x = 3*2\n  if (x /= 6) error stop 'L2:single-star-not-power'", "  x = 3**2\n  if (x /= 6) error stop 'L2:single-star-not-power'")], "replace single asterisk with power to show it is not the power token"),
    ], "R1008 spells power-op as **; a single * remains a distinct mult-op token and has a different exact value."))

    add(valid_case("r1009_mult_tokens", "R1009", SELECTED["R1009"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("asterisk-token", "r1009-asterisk-token", [("  x = 2*4\n  if (x /= 8) error stop 'L2:asterisk-token'", "  x = 2+4\n  if (x /= 8) error stop 'L2:asterisk-token'")], "replace * with conforming + producing a different exact result"),
        ("slash-token", "r1009-slash-token", [("  x = 8/2\n  if (x /= 4) error stop 'L2:slash-token'", "  x = 8-2\n  if (x /= 4) error stop 'L2:slash-token'")], "replace / with conforming - producing a different exact result"),
    ], "R1009 spells mult-op as * or /; exact integer controls avoid rounding and truncation ambiguity."))

    add(valid_case("r1010_add_tokens", "R1010", SELECTED["R1010"], "positive-control", source,
                   "EXPRESSIONS LEVEL 2 NUMERIC OK\n", [
        ("plus-token", "r1010-plus-token", [("  x = 4+5\n  if (x /= 9) error stop 'L2:plus-token'", "  x = 4*5\n  if (x /= 9) error stop 'L2:plus-token'")], "replace + with conforming * producing a different exact result"),
        ("minus-token", "r1010-minus-token", [("  x = 9-4\n  if (x /= 5) error stop 'L2:minus-token'", "  x = 9+4\n  if (x /= 5) error stop 'L2:minus-token'")], "replace - with conforming + producing a different exact result"),
        ("unary-position", "r1010-unary-position", [("  x = -6\n  if (x /= -6) error stop 'L2:unary-position'", "  x = +6\n  if (x /= -6) error stop 'L2:unary-position'")], "swap conforming unary add-op positions"),
        ("binary-position", "r1010-binary-position", [("  x = 6+2\n  if (x /= 8) error stop 'L2:binary-position'", "  x = 6-2\n  if (x /= 8) error stop 'L2:binary-position'")], "swap conforming binary add-op token"),
    ], "R1010 spells add-op as + or - and R1007 admits those tokens in unary and binary positions."))

    add(invalid_case("r1005_missing_power_rhs", "R1005", "missing-right-mult-operand-rejected", """program expr_r1005_missing_power_rhs
  implicit none
  integer :: x
  x = 2**
  print *, x
end program expr_r1005_missing_power_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair only the missing R1005 right mult-operand by changing 'x = 2**' to 'x = 2**3', which computes 8.", "R1005 requires a mult-operand after a present power-op."))
    add(valid_case("r1005_missing_power_rhs_control", "R1005", ["missing-right-mult-operand-rejected"], "positive-control", """program expr_r1005_missing_power_rhs_control
  implicit none
  integer :: x
  x = 2**3
  if (x /= 8) error stop 'R1005:control'
  write(*,'(a)') 'EXPRESSIONS R1005 MISSING RHS CONTROL OK'
end program expr_r1005_missing_power_rhs_control
""", "EXPRESSIONS R1005 MISSING RHS CONTROL OK\n", [
        ("missing-right-mult-operand-rejected", "r1005-control-right-operand", [("  x = 2**3\n  if (x /= 8) error stop 'R1005:control'", "  x = 2**2\n  if (x /= 8) error stop 'R1005:control'")], "change the supplied right mult-operand in the conforming control"),
    ], "Control for the R1005 diagnostic: appending the single missing mult-operand makes 2**3 a conforming mult-operand."))

    add(invalid_case("r1006_missing_mult_rhs", "R1006", "missing-right-mult-operand-rejected", """program expr_r1006_missing_mult_rhs
  implicit none
  integer :: x
  x = 2*
  print *, x
end program expr_r1006_missing_mult_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair only the missing R1006 right mult-operand by changing 'x = 2*' to 'x = 2*3', which computes 6.", "R1006 requires a mult-operand after a present mult-op."))
    add(valid_case("r1006_missing_mult_rhs_control", "R1006", ["missing-right-mult-operand-rejected"], "positive-control", """program expr_r1006_missing_mult_rhs_control
  implicit none
  integer :: x
  x = 2*3
  if (x /= 6) error stop 'R1006:control'
  write(*,'(a)') 'EXPRESSIONS R1006 MISSING RHS CONTROL OK'
end program expr_r1006_missing_mult_rhs_control
""", "EXPRESSIONS R1006 MISSING RHS CONTROL OK\n", [
        ("missing-right-mult-operand-rejected", "r1006-control-right-operand", [("  x = 2*3\n  if (x /= 6) error stop 'R1006:control'", "  x = 2*4\n  if (x /= 6) error stop 'R1006:control'")], "change the supplied right mult-operand in the conforming control"),
    ], "Control for the R1006 diagnostic: appending the single missing mult-operand makes 2*3 a conforming add-operand."))

    add(invalid_case("r1007_missing_add_rhs", "R1007", "missing-add-operand-rejected", """program expr_r1007_missing_add_rhs
  implicit none
  integer :: x
  x = 1+
  print *, x
end program expr_r1007_missing_add_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair only the missing R1007 right add-operand by changing 'x = 1+' to 'x = 1+2', which computes 3.", "R1007 requires an add-operand after a present add-op in the binary form."))

    char_source = """module expr_l3_defined_concat_mod
  implicit none
  type :: token
    integer :: value
  end type token
  interface operator(//)
    module procedure join_token
  end interface
  interface operator(.cat.)
    module procedure cat_char
  end interface
contains
  pure function join_token(lhs, rhs) result(out)
    type(token), intent(in) :: lhs, rhs
    type(token) :: out
    out%value = 10*lhs%value + rhs%value
  end function join_token
  pure function cat_char(lhs, rhs) result(out)
    character(len=*), intent(in) :: lhs, rhs
    character(len=len(lhs)+len(rhs)) :: out
    out = rhs // lhs
  end function cat_char
end module expr_l3_defined_concat_mod

program expr_l3_concat_layers
  use expr_l3_defined_concat_mod
  implicit none
  integer :: checks
  character(len=5) :: single_s, single_r
  character(len=4) :: joined_s, joined_r, joined_token
  type(token) :: a, b, c, d, e, f, left_one, left_two
  checks = 0
  single_s = 'x'
  if (len('x') /= 1) error stop 'L3:s-single-len'
  if (single_s /= 'x') error stop 'L3:s-single-value'
  checks = checks + 1
  joined_s = 'ab'//'cd'
  if (len('ab'//'cd') /= 4) error stop 'L3:s-concat-len'
  if (joined_s /= 'abcd') error stop 'L3:s-concat-value'
  checks = checks + 1
  a = token(1); b = token(2); c = token(3)
  left_one = a // b // c
  if (left_one%value /= 123) error stop 'L3:left-one'
  checks = checks + 1
  single_r = 'y'
  if (len('y') /= 1) error stop 'L3:r-single-len'
  if (single_r /= 'y') error stop 'L3:r-single-value'
  checks = checks + 1
  joined_r = 'pq'//'rs'
  if (len('pq'//'rs') /= 4) error stop 'L3:r-concat-len'
  if (joined_r /= 'pqrs') error stop 'L3:r-concat-value'
  checks = checks + 1
  d = token(4); e = token(5); f = token(6)
  left_two = d // e // f
  if (left_two%value /= 456) error stop 'L3:left-two'
  checks = checks + 1
  joined_token = 'lm'//'no'
  if (len('lm'//'no') /= 4) error stop 'L3:token-concat-len'
  if (joined_token /= 'lmno') error stop 'L3:token-concat-value'
  checks = checks + 1
  if (checks /= 7) error stop 'L3:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 3 CONCAT OK'
end program expr_l3_concat_layers
"""
    add(valid_case("r1007_missing_add_rhs_control", "R1007", ["missing-add-operand-rejected"], "positive-control", """program expr_r1007_missing_add_rhs_control
  implicit none
  integer :: x
  x = 1+2
  if (x /= 3) error stop 'R1007:control'
  write(*,'(a)') 'EXPRESSIONS R1007 MISSING RHS CONTROL OK'
end program expr_r1007_missing_add_rhs_control
""", "EXPRESSIONS R1007 MISSING RHS CONTROL OK\n", [
        ("missing-add-operand-rejected", "r1007-control-right-operand", [("  x = 1+2\n  if (x /= 3) error stop 'R1007:control'", "  x = 1+3\n  if (x /= 3) error stop 'R1007:control'")], "change the supplied right add-operand in the conforming control"),
    ], "Control for the R1007 diagnostic: appending the single missing add-operand makes 1+2 a conforming level-2 expression."))

    add(valid_case("level3_concat_layers", "S10.1.2.6-001", SELECTED["S10.1.2.6-001"], "positive-control", char_source,
                   "EXPRESSIONS LEVEL 3 CONCAT OK\n", [
        ("level-2-base", "l3-level2-base-literal", [("  single_s = 'x'\n  if (len('x') /= 1) error stop 'L3:s-single-len'", "  single_s = 'y'\n  if (len('x') /= 1) error stop 'L3:s-single-len'")], "change the character primary used as a level-3 expression"),
        ("concatenation-layer", "l3-concat-layer-defined-cat", [("  joined_s = 'ab'//'cd'\n  if (len('ab'//'cd') /= 4) error stop 'L3:s-concat-len'", "  joined_s = 'ab' .cat. 'cd'\n  if (len('ab' .cat. 'cd') /= 4) error stop 'L3:s-concat-len'")], "replace intrinsic // with conforming defined .cat. that reverses operands"),
        ("left-concatenation-chain", "l3-left-chain-right-group-one", [("  left_one = a // b // c\n  if (left_one%value /= 123) error stop 'L3:left-one'", "  left_one = a // (b // c)\n  if (left_one%value /= 123) error stop 'L3:left-one'")], "parenthesize a defined // chain with right grouping"),
    ], "10.1.2.6 p1 admits level-2 expressions with optional concat-op; R1011 supplies left recursion for // chains."))

    add(valid_case("r1011_concat_forms", "R1011", ["single-level-2", "single-concat", "left-recursive-concat"], "positive-control", char_source,
                   "EXPRESSIONS LEVEL 3 CONCAT OK\n", [
        ("single-level-2", "r1011-single-level2-value", [("  single_r = 'y'\n  if (len('y') /= 1) error stop 'L3:r-single-len'", "  single_r = 'z'\n  if (len('z') /= 1) error stop 'L3:r-single-len'")], "change the character level-2 expression value"),
        ("single-concat", "r1011-single-concat-defined-cat", [("  joined_r = 'pq'//'rs'\n  if (len('pq'//'rs') /= 4) error stop 'L3:r-concat-len'", "  joined_r = 'pq' .cat. 'rs'\n  if (len('pq' .cat. 'rs') /= 4) error stop 'L3:r-concat-len'")], "replace intrinsic // with conforming defined .cat. that reverses operands"),
        ("left-recursive-concat", "r1011-left-recursive-right-group", [("  left_two = d // e // f\n  if (left_two%value /= 456) error stop 'L3:left-two'", "  left_two = d // (e // f)\n  if (left_two%value /= 456) error stop 'L3:left-two'")], "parenthesize a second defined // chain with right grouping"),
    ], "R1011 is a left-recursive chain of level-2 expressions joined by concat-op."))

    add(valid_case("r1012_concat_token", "R1012", SELECTED["R1012"], "positive-control", char_source,
                   "EXPRESSIONS LEVEL 3 CONCAT OK\n", [
        ("double-slash-token", "r1012-double-slash-token", [("  joined_token = 'lm'//'no'\n  if (len('lm'//'no') /= 4) error stop 'L3:token-concat-len'", "  joined_token = 'lm' .cat. 'no'\n  if (len('lm' .cat. 'no') /= 4) error stop 'L3:token-concat-len'")], "replace the // token with conforming defined .cat. that reverses operands"),
    ], "R1012 spells concat-op as //; direct LEN and value checks observe the token-bearing intrinsic concatenation."))

    add(invalid_case("r1011_missing_concat_rhs", "R1011", "missing-right-level-2-rejected", """program expr_r1011_missing_concat_rhs
  implicit none
  character(len=2) :: s
  s = 'a'//
  print *, s
end program expr_r1011_missing_concat_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair only the missing R1011 right level-2 expression by changing the line to s = 'a'//'b', which yields 'ab'.", "R1011 requires a level-2 expression after a present concat-op."))

    rel_source = """program expr_l4_relational_layers
  implicit none
  integer :: checks, x, y
  logical :: ok
  checks = 0
  x = 4
  if (x /= 4) error stop 'L4:level3-base'
  checks = checks + 1
  ok = 2 < 3
  if (.not. ok) error stop 'L4:single-relation-layer'
  checks = checks + 1
  y = 5
  if (y /= 5) error stop 'L4:r1013-single-level3'
  checks = checks + 1
  ok = 3 <= 4
  if (.not. ok) error stop 'L4:r1013-relational-operation'
  checks = checks + 1
  if (len('A') /= 1) error stop 'L4:dot-eq-left-len'
  if (len('A ') /= 2) error stop 'L4:dot-eq-right-len'
  ok = 'A' .EQ. 'A '
  if (.not. ok) error stop 'L4:dot-eq'
  checks = checks + 1
  ok = 4 .NE. 5
  if (.not. ok) error stop 'L4:dot-ne'
  checks = checks + 1
  ok = 3 .LT. 4
  if (.not. ok) error stop 'L4:dot-lt'
  checks = checks + 1
  ok = 4 .LE. 4
  if (.not. ok) error stop 'L4:dot-le'
  checks = checks + 1
  ok = 5 .GT. 4
  if (.not. ok) error stop 'L4:dot-gt'
  checks = checks + 1
  ok = 5 .GE. 5
  if (.not. ok) error stop 'L4:dot-ge'
  checks = checks + 1
  if (len('B') /= 1) error stop 'L4:eqeq-left-len'
  if (len('B ') /= 2) error stop 'L4:eqeq-right-len'
  ok = 'B' == 'B '
  if (.not. ok) error stop 'L4:eqeq'
  checks = checks + 1
  ok = 6 /= 7
  if (.not. ok) error stop 'L4:slash-eq'
  checks = checks + 1
  ok = 1 < 2
  if (.not. ok) error stop 'L4:lt'
  checks = checks + 1
  ok = 2 <= 2
  if (.not. ok) error stop 'L4:le'
  checks = checks + 1
  ok = 3 > 2
  if (.not. ok) error stop 'L4:gt'
  checks = checks + 1
  ok = 3 >= 3
  if (.not. ok) error stop 'L4:ge'
  checks = checks + 1
  if (checks /= 16) error stop 'L4:checks'
  write(*,'(a)') 'EXPRESSIONS LEVEL 4 RELATIONAL OK'
end program expr_l4_relational_layers
"""
    add(valid_case("r1011_missing_concat_rhs_control", "R1011", ["missing-right-level-2-rejected"], "positive-control", """program expr_r1011_missing_concat_rhs_control
  implicit none
  character(len=2) :: s
  s = 'a'//'b'
  if (len('a'//'b') /= 2) error stop 'R1011:control-len'
  if (s /= 'ab') error stop 'R1011:control-value'
  write(*,'(a)') 'EXPRESSIONS R1011 MISSING RHS CONTROL OK'
end program expr_r1011_missing_concat_rhs_control
""", "EXPRESSIONS R1011 MISSING RHS CONTROL OK\n", [
        ("missing-right-level-2-rejected", "r1011-control-right-operand", [("  s = 'a'//'b'\n  if (len('a'//'b') /= 2) error stop 'R1011:control-len'", "  s = 'a'//'c'\n  if (len('a'//'c') /= 2) error stop 'R1011:control-len'")], "change the supplied right level-2 expression in the conforming control"),
    ], "Control for the R1011 diagnostic: appending the single missing character level-2 expression makes 'a'//'b' conforming."))

    add(valid_case("level4_relational_layers", "S10.1.2.7-001", ["level-3-base", "single-relation-layer"], "positive-control", rel_source,
                   "EXPRESSIONS LEVEL 4 RELATIONAL OK\n", [
        ("level-3-base", "l4-level3-base-literal", [("  x = 4\n  if (x /= 4) error stop 'L4:level3-base'", "  x = 5\n  if (x /= 4) error stop 'L4:level3-base'")], "change the level-3 expression admitted as level-4"),
        ("single-relation-layer", "l4-single-relation-token", [("  ok = 2 < 3\n  if (.not. ok) error stop 'L4:single-relation-layer'", "  ok = 2 > 3\n  if (.not. ok) error stop 'L4:single-relation-layer'")], "replace one conforming relation with another producing false"),
    ], "10.1.2.7 p1 admits a level-3 expression or one relation between level-3 expressions."))

    add(valid_case("r1013_relational_forms", "R1013", ["single-level-3", "relational-operation"], "positive-control", rel_source,
                   "EXPRESSIONS LEVEL 4 RELATIONAL OK\n", [
        ("single-level-3", "r1013-single-level3-literal", [("  y = 5\n  if (y /= 5) error stop 'L4:r1013-single-level3'", "  y = 6\n  if (y /= 5) error stop 'L4:r1013-single-level3'")], "change the single level-3 expression value"),
        ("relational-operation", "r1013-relational-operation-token", [("  ok = 3 <= 4\n  if (.not. ok) error stop 'L4:r1013-relational-operation'", "  ok = 3 > 4\n  if (.not. ok) error stop 'L4:r1013-relational-operation'")], "replace the relation with a conforming false relation"),
    ], "R1013 is either a single level-3 expression or one rel-op between two level-3 expressions."))

    add(valid_case("r1014_relop_tokens", "R1014", SELECTED["R1014"], "positive-control", rel_source,
                   "EXPRESSIONS LEVEL 4 RELATIONAL OK\n", [
        ("dot-eq", "r1014-dot-eq-token", [("  ok = 'A' .EQ. 'A '\n  if (.not. ok) error stop 'L4:dot-eq'", "  ok = 'A' .NE. 'A '\n  if (.not. ok) error stop 'L4:dot-eq'")], "replace .EQ. with conforming .NE. on blank-padded equal operands"),
        ("dot-ne", "r1014-dot-ne-token", [("  ok = 4 .NE. 5\n  if (.not. ok) error stop 'L4:dot-ne'", "  ok = 4 .EQ. 5\n  if (.not. ok) error stop 'L4:dot-ne'")], "replace .NE. with conforming .EQ."),
        ("dot-lt", "r1014-dot-lt-token", [("  ok = 3 .LT. 4\n  if (.not. ok) error stop 'L4:dot-lt'", "  ok = 3 .GT. 4\n  if (.not. ok) error stop 'L4:dot-lt'")], "replace .LT. with conforming .GT."),
        ("dot-le", "r1014-dot-le-token", [("  ok = 4 .LE. 4\n  if (.not. ok) error stop 'L4:dot-le'", "  ok = 4 .LT. 4\n  if (.not. ok) error stop 'L4:dot-le'")], "replace .LE. with conforming strict .LT."),
        ("dot-gt", "r1014-dot-gt-token", [("  ok = 5 .GT. 4\n  if (.not. ok) error stop 'L4:dot-gt'", "  ok = 5 .LT. 4\n  if (.not. ok) error stop 'L4:dot-gt'")], "replace .GT. with conforming .LT."),
        ("dot-ge", "r1014-dot-ge-token", [("  ok = 5 .GE. 5\n  if (.not. ok) error stop 'L4:dot-ge'", "  ok = 5 .GT. 5\n  if (.not. ok) error stop 'L4:dot-ge'")], "replace .GE. with conforming strict .GT."),
        ("eqeq", "r1014-eqeq-token", [("  ok = 'B' == 'B '\n  if (.not. ok) error stop 'L4:eqeq'", "  ok = 'B' /= 'B '\n  if (.not. ok) error stop 'L4:eqeq'")], "replace == with conforming /= on blank-padded equal operands"),
        ("slash-eq", "r1014-slash-eq-token", [("  ok = 6 /= 7\n  if (.not. ok) error stop 'L4:slash-eq'", "  ok = 6 == 7\n  if (.not. ok) error stop 'L4:slash-eq'")], "replace /= with conforming =="),
        ("lt", "r1014-lt-token", [("  ok = 1 < 2\n  if (.not. ok) error stop 'L4:lt'", "  ok = 1 > 2\n  if (.not. ok) error stop 'L4:lt'")], "replace < with conforming >"),
        ("le", "r1014-le-token", [("  ok = 2 <= 2\n  if (.not. ok) error stop 'L4:le'", "  ok = 2 < 2\n  if (.not. ok) error stop 'L4:le'")], "replace <= with conforming strict <"),
        ("gt", "r1014-gt-token", [("  ok = 3 > 2\n  if (.not. ok) error stop 'L4:gt'", "  ok = 3 < 2\n  if (.not. ok) error stop 'L4:gt'")], "replace > with conforming <"),
        ("ge", "r1014-ge-token", [("  ok = 3 >= 3\n  if (.not. ok) error stop 'L4:ge'", "  ok = 3 > 3\n  if (.not. ok) error stop 'L4:ge'")], "replace >= with conforming strict >"),
    ], "R1014 enumerates the twelve rel-op spellings; truth interpretation is the dependency on relational intrinsic operations."))

    add(invalid_case("r1013_relation_chain", "R1013", "chained-relation-rejected", """program expr_r1013_relation_chain
  implicit none
  logical :: ok
  ok = 1 < 2 < 3
  print *, ok
end program expr_r1013_relation_chain
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "Unclassifiable", "LOGICAL", "INTEGER"], "Repair by splitting the chain into ok = (1 < 2) .and. (2 < 3), leaving both individual relations valid.", "R1013 has only one optional left level-3 expression and rel-op before the right level-3 expression."))
    add(valid_case("r1013_relation_chain_control", "R1013", ["chained-relation-rejected"], "positive-control", """program expr_r1013_relation_chain_control
  implicit none
  logical :: ok
  ok = 1 < 2
  if (.not. ok) error stop 'R1013:chain-control'
  write(*,'(a)') 'EXPRESSIONS R1013 CHAIN CONTROL OK'
end program expr_r1013_relation_chain_control
""", "EXPRESSIONS R1013 CHAIN CONTROL OK\n", [
        ("chained-relation-rejected", "r1013-chain-control-relation", [("  ok = 1 < 2\n  if (.not. ok) error stop 'R1013:chain-control'", "  ok = 1 > 2\n  if (.not. ok) error stop 'R1013:chain-control'")], "change the single conforming relation in the chain diagnostic control"),
    ], "Control for the R1013 chained-relation diagnostic: deleting the second rel-op leaves the conforming one-relation level-4 expression 1<2."))

    add(invalid_case("r1013_missing_relation_rhs", "R1013", "missing-right-level-3-rejected", """program expr_r1013_missing_relation_rhs
  implicit none
  logical :: ok
  ok = 1 <
  print *, ok
end program expr_r1013_missing_relation_rhs
""", 4, ["Expected", "Syntax", "Invalid", "Unexpected", "operand"], "Repair only the missing right level-3 expression by changing the line to ok = 1 < 2, which is true.", "R1013 requires a level-3 expression after a present rel-op."))
    add(valid_case("r1013_missing_relation_rhs_control", "R1013", ["missing-right-level-3-rejected"], "positive-control", """program expr_r1013_missing_relation_rhs_control
  implicit none
  logical :: ok
  ok = 1 < 2
  if (.not. ok) error stop 'R1013:missing-rhs-control'
  write(*,'(a)') 'EXPRESSIONS R1013 MISSING RHS CONTROL OK'
end program expr_r1013_missing_relation_rhs_control
""", "EXPRESSIONS R1013 MISSING RHS CONTROL OK\n", [
        ("missing-right-level-3-rejected", "r1013-missing-rhs-control", [("  ok = 1 < 2\n  if (.not. ok) error stop 'R1013:missing-rhs-control'", "  ok = 1 > 2\n  if (.not. ok) error stop 'R1013:missing-rhs-control'")], "change the supplied right level-3 expression relation in the conforming control"),
    ], "Control for the R1013 missing-right diagnostic: appending the single missing level-3 expression makes 1<2 conforming."))


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
        "the bounded batch295 fixtures below supply selected cases and mutation/diagnostic plans, not oracle approval, "
        "fixture approval, source-review renewal, or universal coverage.")
    selected_here = [rule for rule in SELECTED if rule in {row["id"] for row in catalogue["requirements"]}]
    summary = (
        SUMMARY_BEGIN + "\n"
        f"## Batch295 expression fixtures for {section}\n\n"
        f"Generated batch295 fixtures cover selected facets for: {', '.join(selected_here)}. Runtime cases use exact integer, "
        "logical, and character LEN/value oracles; diagnostic cases are line-anchored one-property malformed forms with "
        "conforming repairs documented in generator metadata. Feature mutations, including concat operator replacements with defined .cat. controls, are permanent and checked on both the "
        "reference gfortran and frozen LFortran target. Facets not listed remain pending for the recorded reasons.\n"
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
            raise SystemExit("stale expressions 10.1.2.5-10.1.2.7 fixtures: " + ", ".join(stale))
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
