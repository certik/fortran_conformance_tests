#!/usr/bin/env python3
"""Additional BLOCK and ASSOCIATE fixtures for Fortran 2023 11.1.1-11.1.3.3."""
import argparse
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "associate_blocks_11_1"
SECTIONS = ("11.1.1", "11.1.2.1", "11.1.2.2", "11.1.3.1", "11.1.3.2", "11.1.3.3")
CATALOGUES = {
    "11.1.1": "doc/catalogues/blocks_11_1_1.json",
    "11.1.2.1": "doc/catalogues/control_flow_in_blocks_11_1_2_1.json",
    "11.1.2.2": "doc/catalogues/execution_of_a_block_11_1_2_2.json",
    "11.1.3.1": "doc/catalogues/purpose_and_form_of_the_associate_construct_11_1_3_1.json",
    "11.1.3.2": "doc/catalogues/execution_of_the_associate_construct_11_1_3_2.json",
    "11.1.3.3": "doc/catalogues/other_attributes_of_associate_names_11_1_3_3.json",
}
VIEWS = {sec: f"doc/fortran_2023_{sec.replace('.', '_')}.md" for sec in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN ASSOCIATE BLOCKS 11.1 FIXTURES -->"
SUMMARY_END = "<!-- END ASSOCIATE BLOCKS 11.1 FIXTURES -->"
EXCLUSIONS = [
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal error", "internal compiler error", "asr", "verifier", "segmentation fault", "traceback",
    "assertion failed", "module failed verification", "out of memory", "recovery",
]

SELECTED = {
    "R1101": ["nonempty-block-form"],
    "S11.1.2.1-001": ["procedure-return-exception-control"],
    "S11.1.2.1-002": ["within-block-transfer-source", "out-of-block-transfer-source"],
    "S11.1.2.1-003": ["subroutine-reference-in-block-source", "function-reference-in-block-source"],
    "S11.1.2.2-001": ["first-construct-reached"],
    "S11.1.2.2-002": ["last-construct-completion", "outward-branch-completion", "return-completion-source", "exit-cycle-containing-construct-completion-source"],
    "S11.1.3.1-001": ["associate-name-source-control", "construct-entity-scope-source", "expression-and-variable-selector-classification"],
    "R1102": ["associate-construct-form"],
    "R1103": ["unnamed-associate-stmt", "named-associate-stmt", "multiple-association-list"],
    "R1104": ["association-arrow-form", "associate-name-binding-source"],
    "R1105": ["expression-selector-form", "variable-selector-form"],
    "R1106": ["unnamed-end-associate", "named-end-associate"],
    "C1101": ["definable-variable-selector-control", "expression-selector-definition-rejected", "vector-subscript-selector-definition-rejected"],
    "C1102": ["distinct-associate-names-control", "duplicate-associate-name-rejected"],
    "C1104": ["nonvariable-expression-selector-control", "variable-selector-route-source-control"],
    "C1105": ["data-expression-selector-control"],
    "C1106": ["matching-associate-construct-name-control", "end-associate-name-mismatch-rejected", "unnamed-associate-end-name-rejected"],
    "S11.1.3.2-001": ["block-executes-after-selector-evaluation"],
    "S11.1.3.2-003": ["declared-type-control", "polymorphic-selector-control"],
    "S11.1.3.2-005": ["internal-end-associate-branch-control"],
    "S11.1.3.3-004": ["dynamic-type-and-parameters", "optional-selector-present-control", "contiguity-iff-selector"],
}
FACETS_BY_RULE = {rule: tuple(facets) for rule, facets in SELECTED.items()}
REMAINING_PENDING = {
    "S11.1.1-001": {"listed-block-construct-families"},
    "R1101": {"empty-block-form"},
    "S11.1.1-002": {"block-control-classification", "construct-specific-boundary-source"},
    "S11.1.2.1-001": {"outside-branch-entry-rejected"},
    "S11.1.2.1-002": set(),
    "S11.1.2.1-003": set(),
    "S11.1.2.2-001": {"empty-block-source-boundary"},
    "S11.1.2.2-002": set(),
    "S11.1.3.1-001": set(),
    "R1102": set(),
    "R1103": set(),
    "R1104": set(),
    "R1105": set(),
    "R1106": set(),
    "C1101": {"expression-selector-pointer-association-rejected"},
    "C1102": set(),
    "C1103": {"coindexed-variable-selector-rejected", "local-variable-selector-control"},
    "C1104": set(),
    "C1105": {"procedure-pointer-designator-selector-rejected", "procedure-pointer-function-selector-rejected"},
    "C1106": set(),
    "S11.1.3.2-001": set(),
    "S11.1.3.2-002": set(),
    "S11.1.3.2-003": {"kind-type-parameter-source", "nonpolymorphic-selector-control"},
    "S11.1.3.2-004": {"attribute-ownership-boundary"},
    "S11.1.3.2-005": {"outside-end-associate-branch-rejected"},
    "S11.1.3.3-001": {"no-allocatable-attribute-source", "no-pointer-attribute-source"},
    "S11.1.3.3-002": {"same-corank-as-selector-source", "coarray-cobounds-same-source"},
    "S11.1.3.3-003": {"change-team-associating-entity-coarray-source", "codimension-decl-corank-cobounds-source"},
    "S11.1.3.3-004": {"asynchronous-volatile-variable-selector", "no-optional-attribute-source"},
    "S11.1.3.3-005": {"nondefinable-selector-definition-rejected", "nondefinable-selector-undefinition-rejected", "selector-not-vdc-associate-definition-rejected", "selector-not-vdc-pointer-association-rejected"},
}
ORACLE_PREFIXES = {rule: f"{rule} associate-blocks 11.1 fixtures: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} associate-blocks 11.1 fixture boundaries: " for rule in SELECTED}


def ident(rule, variant, invalid=False):
    return rule.replace('.', '_').replace('-', '_') + ("_invalid__" if invalid else "_valid__") + PREFIX + "_" + variant


def valid_spec(rule, variant, facets, source, mutations, evidence="effect"):
    comp = source.rsplit("write(*,'(a)') '", 1)[1].split("'", 1)[0] + "\n"
    raw = source.encode("ascii")
    return dict(id=ident(rule, variant), rule=rule, variant=variant, facets=list(facets), kind="valid",
                evidence=evidence, source=source, source_sha256=sha(raw), completion=comp,
                mutations=mutations)


def invalid_spec(rule, variant, facets, source, line, control_variant):
    prefix = f"! rule: {rule}\n! covers: {', '.join(facets)}\n"
    source = prefix + source
    line += prefix.count("\n")
    raw = source.encode("ascii")
    return dict(id=ident(rule, variant, True), rule=rule, variant=variant, facets=list(facets), kind="invalid",
                evidence="effect", source=source, source_sha256=sha(raw), line=line,
                control=ident(rule, control_variant), mutations=[])


def feature(name, expected, replacement, facet):
    return dict(id=name, kind="feature", expected=expected, replacement=replacement, facet=facet)


def header(rule, facets, program):
    cover_text = ", ".join(facets)
    if len(cover_text) > 100:
        cover_text = facets[0] + ", ..."
    return f"! rule: {rule}\n! covers: {cover_text}\nprogram {program}\n  implicit none\n"


def finish(program, completion, checks):
    body = ""
    for expr, token in checks:
        body += f"  if ({expr}) then\n    write(*,'(a)') '{token}'\n    error stop\n  end if\n"
    body += f"  write(*,'(a)') '{completion.rstrip()}'\n"
    return body + f"\nend program {program}\n"


def source_specs():
    specs = {}
    def add(spec): specs[spec["id"]] = spec

    src = header("R1101", ["nonempty-block-form"], "ab1101_nonempty") + \
"  integer :: marker\n  marker=-7\n  block\n    marker=41\n  end block\n" + finish("ab1101_nonempty", "ASSOCIATE BLOCKS NONEMPTY BLOCK OK\n", [("marker /= 41", "R1101-NONEMPTY")])
    add(valid_spec("R1101", "nonempty_block", ["nonempty-block-form"], src, [feature("change-block-assignment", "marker=41", "marker=-41", "nonempty-block-form")], "positive-control"))

    src = header("S11.1.2.1-001", ["procedure-return-exception-control"], "ab1121_return_exception") + \
"  integer :: value\n  value=3\n  call inner(value)\n" + finish("ab1121_return_exception", "ASSOCIATE BLOCKS RETURN EXCEPTION OK\n", [("value /= 19", "P1-RETURN")]) + \
"contains\n  subroutine inner(arg)\n    integer, intent(inout) :: arg\n    block\n      arg=19\n      return\n    end block\n    arg=-19\n  end subroutine inner\n"
    src = src.replace("end program ab1121_return_exception\ncontains", "contains").replace("  write(*,'(a)') 'ASSOCIATE BLOCKS RETURN EXCEPTION OK'\ncontains", "  write(*,'(a)') 'ASSOCIATE BLOCKS RETURN EXCEPTION OK'\ncontains")
    src += "end program ab1121_return_exception\n" if not src.endswith("end program ab1121_return_exception\n") else ""
    add(valid_spec("S11.1.2.1-001", "procedure_return_exception", ["procedure-return-exception-control"], src, [feature("change-returned-value", "arg=19", "arg=-19", "procedure-return-exception-control")], "positive-control"))

    src = header("S11.1.2.1-002", ["within-block-transfer-source", "out-of-block-transfer-source"], "ab1121_transfers") + \
"  integer :: within_value, outward_value, after_value\n  within_value=-1; outward_value=-2; after_value=-3\n  block\n    goto 10\n    within_value=-10\n10  within_value=31\n  end block\n  block\n    outward_value=43\n    goto 30\n    outward_value=-43\n  end block\n  outward_value=-99\n30 after_value=57\n" + finish("ab1121_transfers", "ASSOCIATE BLOCKS TRANSFERS OK\n", [("within_value /= 31", "WITHIN"), ("outward_value /= 43", "OUTWARD"), ("after_value /= 57", "AFTER")])
    add(valid_spec("S11.1.2.1-002", "within_and_outward_transfers", SELECTED["S11.1.2.1-002"], src, [feature("within-target-disabled", "within_value=31", "within_value=-31", "within-block-transfer-source"), feature("outward-target-disabled", "after_value=57", "after_value=-57", "out-of-block-transfer-source")]))

    src = header("S11.1.2.1-003", SELECTED["S11.1.2.1-003"], "ab1121_procedure_refs") + \
"  integer :: sub_value, fun_value\n  sub_value=-4; fun_value=-5\n  block\n    call set_value(sub_value)\n    fun_value = add_seven(20)\n  end block\n" + finish("ab1121_procedure_refs", "ASSOCIATE BLOCKS PROCEDURE REFS OK\n", [("sub_value /= 64", "SUBREF"), ("fun_value /= 27", "FUNREF")]) + \
"contains\n  subroutine set_value(arg)\n    integer, intent(out) :: arg\n    arg=64\n  end subroutine set_value\n  integer function add_seven(arg)\n    integer, intent(in) :: arg\n    add_seven=arg+7\n  end function add_seven\n"
    src = src.replace("end program ab1121_procedure_refs\ncontains", "contains") + ("end program ab1121_procedure_refs\n" if not src.endswith("end program ab1121_procedure_refs\n") else "")
    add(valid_spec("S11.1.2.1-003", "procedure_references", SELECTED["S11.1.2.1-003"], src, [feature("subroutine-result", "arg=64", "arg=-64", "subroutine-reference-in-block-source"), feature("function-result", "add_seven=arg+7", "add_seven=arg-7", "function-reference-in-block-source")]))

    src = header("S11.1.2.2-001", ["first-construct-reached"], "ab1122_first") + \
"  integer :: first_value, second_value\n  first_value=-8; second_value=-9\n  block\n    first_value=101\n    second_value=first_value+1\n  end block\n" + finish("ab1122_first", "ASSOCIATE BLOCKS FIRST CONSTRUCT OK\n", [("first_value /= 101", "FIRST"), ("second_value /= 102", "SECOND")])
    add(valid_spec("S11.1.2.2-001", "first_construct_reached", ["first-construct-reached"], src, [feature("first-statement-value", "first_value=101", "first_value=-101", "first-construct-reached")]))

    src = header("S11.1.2.2-002", SELECTED["S11.1.2.2-002"], "ab1122_completion") + \
"  integer :: last_value, branch_value, return_value, exit_value, cycle_value, i\n  last_value=-1; branch_value=-2; return_value=-3; exit_value=-4; cycle_value=0\n  block\n    last_value=201\n  end block\n  block\n    branch_value=202\n    goto 40\n    branch_value=-202\n  end block\n  branch_value=-99\n40 continue\n  call returner(return_value)\n  do i=1,4\n    block\n      if (i == 2) cycle\n      if (i == 4) exit\n      cycle_value=cycle_value+i\n    end block\n    exit_value=i\n  end do\n" + finish("ab1122_completion", "ASSOCIATE BLOCKS COMPLETION OK\n", [("last_value /= 201", "LAST"), ("branch_value /= 202", "BRANCH"), ("return_value /= 203", "RETURN"), ("cycle_value /= 4", "CYCLE"), ("exit_value /= 3", "EXIT")]) + \
"contains\n  subroutine returner(v)\n    integer, intent(out) :: v\n    block\n      v=203\n      return\n    end block\n    v=-203\n  end subroutine returner\n"
    src = src.replace("end program ab1122_completion\ncontains", "contains") + ("end program ab1122_completion\n" if not src.endswith("end program ab1122_completion\n") else "")
    add(valid_spec("S11.1.2.2-002", "block_completion_causes", SELECTED["S11.1.2.2-002"], src, [feature("last-value", "last_value=201", "last_value=-201", "last-construct-completion"), feature("branch-value", "branch_value=202", "branch_value=-202", "outward-branch-completion"), feature("return-value", "v=203", "v=-203", "return-completion-source"), feature("cycle-path", "cycle_value=cycle_value+i", "cycle_value=cycle_value-i", "exit-cycle-containing-construct-completion-source")]))

    src = header("S11.1.3.1-001", SELECTED["S11.1.3.1-001"], "ab1131_purpose") + \
"  integer :: outer, target, expr_seen, var_seen\n  outer=700; target=12; expr_seen=-1; var_seen=-2\n  associate (outer => target, expr_alias => target + 5)\n    outer=33\n    expr_seen=expr_alias\n    var_seen=outer\n  end associate\n" + finish("ab1131_purpose", "ASSOCIATE BLOCKS PURPOSE OK\n", [("outer /= 700", "OUTER"), ("target /= 33", "TARGET"), ("expr_seen /= 17", "EXPR"), ("var_seen /= 33", "VAR")])
    add(valid_spec("S11.1.3.1-001", "purpose_and_names", SELECTED["S11.1.3.1-001"], src, [feature("association-purpose", "target=12", "target=13", "expression-and-variable-selector-classification"), feature("associate-write", "outer=33", "outer=34", "associate-name-source-control"), feature("outer-sentinel", "outer=700", "outer=701", "construct-entity-scope-source")]))

    src = header("R1102", SELECTED["R1102"], "ab_r1102_form") + \
"  integer :: v\n  v=1\n  associate (a => v)\n    a=81\n  end associate\n" + finish("ab_r1102_form", "ASSOCIATE BLOCKS R1102 FORM OK\n", [("v /= 81", "R1102")])
    add(valid_spec("R1102", "associate_construct_form", SELECTED["R1102"], src, [feature("associate-body", "a=81", "a=-81", "associate-construct-form")], "positive-control"))

    src = header("R1103", SELECTED["R1103"], "ab_r1103_stmt") + \
"  integer :: x, y, named_seen, unnamed_seen, multi_seen\n  x=2; y=5; named_seen=-1; unnamed_seen=-2; multi_seen=-3\n  associate (u => x)\n    unnamed_seen=u+10\n  end associate\n  named: associate (n => y)\n    named_seen=n+20\n  end associate named\n  associate (a => x, b => y)\n    multi_seen=a*10+b\n  end associate\n" + finish("ab_r1103_stmt", "ASSOCIATE BLOCKS R1103 STMT OK\n", [("unnamed_seen /= 12", "UNNAMED"), ("named_seen /= 25", "NAMED"), ("multi_seen /= 25", "MULTI")])
    add(valid_spec("R1103", "associate_statement_forms", SELECTED["R1103"], src, [feature("unnamed-value", "unnamed_seen=u+10", "unnamed_seen=u-10", "unnamed-associate-stmt"), feature("named-value", "named_seen=n+20", "named_seen=n-20", "named-associate-stmt"), feature("multi-value", "multi_seen=a*10+b", "multi_seen=a+b", "multiple-association-list")], "positive-control"))

    src = header("R1104", SELECTED["R1104"], "ab_r1104_assoc") + \
"  integer :: selector, result\n  selector=14; result=-1\n  associate (alias => selector)\n    alias=28\n    result=alias\n  end associate\n" + finish("ab_r1104_assoc", "ASSOCIATE BLOCKS R1104 ASSOC OK\n", [("selector /= 28", "ARROW"), ("result /= 28", "BIND")])
    add(valid_spec("R1104", "association_arrow", SELECTED["R1104"], src, [feature("alias-assignment", "alias=28", "alias=-28", "association-arrow-form"), feature("alias-read", "result=alias", "result=-alias", "associate-name-binding-source")], "positive-control"))

    src = header("R1105", SELECTED["R1105"], "ab_r1105_selector") + \
"  integer :: base, variable_result, expression_result\n  base=9; variable_result=-1; expression_result=-2\n  associate (expr_name => base + 4)\n    expression_result=expr_name\n  end associate\n  associate (var_name => base)\n    var_name=45\n  end associate\n  variable_result=base\n" + finish("ab_r1105_selector", "ASSOCIATE BLOCKS R1105 SELECTOR OK\n", [("expression_result /= 13", "EXPRFORM"), ("variable_result /= 45", "VARFORM")])
    add(valid_spec("R1105", "selector_forms", SELECTED["R1105"], src, [feature("expr-selector", "base + 4", "base + 5", "expression-selector-form"), feature("variable-selector", "var_name=45", "var_name=-45", "variable-selector-form")], "positive-control"))

    src = header("R1106", SELECTED["R1106"], "ab_r1106_end") + \
"  integer :: x, y\n  x=1; y=2\n  associate (a => x)\n    a=11\n  end associate\n  named_end: associate (b => y)\n    b=22\n  end associate named_end\n" + finish("ab_r1106_end", "ASSOCIATE BLOCKS R1106 END OK\n", [("x /= 11", "R1106U"), ("y /= 22", "R1106N")])
    add(valid_spec("R1106", "end_associate_forms", SELECTED["R1106"], src, [feature("unnamed-end-body", "a=11", "a=-11", "unnamed-end-associate"), feature("named-end-body", "b=22", "b=-22", "named-end-associate")], "positive-control"))

    src = header("C1101", ["definable-variable-selector-control"], "ab_c1101_control") + \
"  integer :: store(4), idx(2)\n  store=[1,2,3,4]; idx=[1,3]\n  associate (section => store(2:4))\n    section=[20,30,40]\n  end associate\n" + finish("ab_c1101_control", "ASSOCIATE BLOCKS C1101 CONTROL OK\n", [("store(2) /= 20", "C1101A"), ("store(4) /= 40", "C1101B")])
    add(valid_spec("C1101", "definable_selector_control", ["definable-variable-selector-control"], src, [feature("section-assignment", "section=[20,30,40]", "section=[21,30,40]", "definable-variable-selector-control")], "positive-control"))
    add(invalid_spec("C1101", "expression_selector_definition", ["expression-selector-definition-rejected"], "program ab_c1101_expr\n  implicit none\n  integer :: seed\n  seed=3\n  associate (a => seed + 1)\n    a=5\n  end associate\nend program ab_c1101_expr\n", 6, "definable_selector_control"))
    add(invalid_spec("C1101", "vector_subscript_definition", ["vector-subscript-selector-definition-rejected"], "program ab_c1101_vector\n  implicit none\n  integer :: store(4), idx(2)\n  store=[1,2,3,4]; idx=[1,3]\n  associate (a => store(idx))\n    a=[9,8]\n  end associate\nend program ab_c1101_vector\n", 6, "definable_selector_control"))

    src = header("C1102", ["distinct-associate-names-control"], "ab_c1102_distinct") + \
"  integer :: x, y, result\n  x=4; y=8; result=-1\n  associate (left => x, right => y)\n    result=left*10+right\n  end associate\n" + finish("ab_c1102_distinct", "ASSOCIATE BLOCKS C1102 DISTINCT OK\n", [("result /= 48", "C1102")])
    add(valid_spec("C1102", "distinct_names_control", ["distinct-associate-names-control"], src, [feature("right-selector", "right => y", "right => x", "distinct-associate-names-control")], "positive-control"))
    add(invalid_spec("C1102", "duplicate_associate_name", ["duplicate-associate-name-rejected"], "program ab_c1102_duplicate\n  implicit none\n  integer :: x, y\n  x=4; y=8\n  associate (item => x, item => y)\n    x=item\n  end associate\nend program ab_c1102_duplicate\n", 5, "distinct_names_control"))

    src = header("C1104", SELECTED["C1104"], "ab_c1104_routes") + \
"  integer :: base, expr_seen, var_seen\n  base=6; expr_seen=-1; var_seen=-2\n  associate (expr_alias => base + 2)\n    expr_seen=expr_alias\n  end associate\n  associate (var_alias => base)\n    var_alias=18\n  end associate\n  var_seen=base\n" + finish("ab_c1104_routes", "ASSOCIATE BLOCKS C1104 ROUTES OK\n", [("expr_seen /= 8", "C1104E"), ("var_seen /= 18", "C1104V")])
    add(valid_spec("C1104", "expr_and_variable_routes", SELECTED["C1104"], src, [feature("nonvariable-expression", "base + 2", "base + 3", "nonvariable-expression-selector-control"), feature("variable-route", "var_alias=18", "var_alias=-18", "variable-selector-route-source-control")], "positive-control"))

    src = header("C1105", ["data-expression-selector-control"], "ab_c1105_data") + \
"  integer :: base, result\n  base=30; result=-1\n  associate (data_expr => base + 12)\n    result=data_expr\n  end associate\n" + finish("ab_c1105_data", "ASSOCIATE BLOCKS C1105 DATA OK\n", [("result /= 42", "C1105")])
    add(valid_spec("C1105", "data_expression_control", ["data-expression-selector-control"], src, [feature("data-expression", "base + 12", "base + 13", "data-expression-selector-control")], "positive-control"))

    src = header("C1106", ["matching-associate-construct-name-control"], "ab_c1106_matching") + \
"  integer :: x\n  x=5\n  outer: associate (a => x)\n    a=55\n  end associate outer\n" + finish("ab_c1106_matching", "ASSOCIATE BLOCKS C1106 MATCHING OK\n", [("x /= 55", "C1106")])
    add(valid_spec("C1106", "matching_name_control", ["matching-associate-construct-name-control"], src, [feature("named-body", "a=55", "a=-55", "matching-associate-construct-name-control")], "positive-control"))
    add(invalid_spec("C1106", "end_name_mismatch", ["end-associate-name-mismatch-rejected"], "program ab_c1106_mismatch\n  implicit none\n  integer :: x\n  x=5\n  outer: associate (a => x)\n    a=55\n  end associate inner\nend program ab_c1106_mismatch\n", 7, "matching_name_control"))
    add(invalid_spec("C1106", "unnamed_end_name", ["unnamed-associate-end-name-rejected"], "program ab_c1106_unnamed\n  implicit none\n  integer :: x\n  x=5\n  associate (a => x)\n    a=55\n  end associate inner\nend program ab_c1106_unnamed\n", 7, "matching_name_control"))

    src = header("S11.1.3.2-001", ["block-executes-after-selector-evaluation"], "ab1132_eval_block") + \
"  integer :: counter, result, inside\n  counter=0; result=-1; inside=-2\n  associate (value => bump())\n    inside=counter\n    result=value\n  end associate\n" + finish("ab1132_eval_block", "ASSOCIATE BLOCKS EVAL BLOCK OK\n", [("counter /= 1", "COUNTER"), ("inside /= 1", "INSIDE"), ("result /= 72", "RESULT")]) + \
"contains\n  integer function bump()\n    counter=counter+1\n    bump=72\n  end function bump\n"
    src = src.replace("end program ab1132_eval_block\ncontains", "contains") + ("end program ab1132_eval_block\n" if not src.endswith("end program ab1132_eval_block\n") else "")
    add(valid_spec("S11.1.3.2-001", "selector_evaluation_before_block", ["block-executes-after-selector-evaluation"], src, [feature("selector-result", "bump=72", "bump=-72", "block-executes-after-selector-evaluation")]))

    src = header("S11.1.3.2-003", ["declared-type-control"], "ab1132_declared_type") + \
"  type :: packet\n    integer :: tag\n  end type packet\n  type(packet) :: item\n  integer :: result\n  item%tag=91; result=-1\n  associate (alias => item)\n    result=alias%tag\n  end associate\n" + finish("ab1132_declared_type", "ASSOCIATE BLOCKS DECLARED TYPE OK\n", [("result /= 91", "DECLTYPE")])
    add(valid_spec("S11.1.3.2-003", "declared_type_control", ["declared-type-control"], src, [feature("component-value", "item%tag=91", "item%tag=-91", "declared-type-control")]))

    src = header("S11.1.3.2-003", ["polymorphic-selector-control"], "ab1132_polymorphic") + \
"  type :: base\n    integer :: tag\n  end type base\n  type, extends(base) :: child\n    integer :: extra\n  end type child\n  class(base), allocatable :: obj\n  integer :: seen_tag, seen_extra\n  allocate(child :: obj)\n  select type (obj)\n  type is (child)\n    obj%tag=15; obj%extra=26\n  end select\n  seen_tag=-1; seen_extra=-2\n  associate (alias => obj)\n    select type (alias)\n    type is (child)\n      seen_tag=alias%tag\n      seen_extra=alias%extra\n    class default\n      seen_tag=-15\n    end select\n  end associate\n" + finish("ab1132_polymorphic", "ASSOCIATE BLOCKS POLYMORPHIC OK\n", [("seen_tag /= 15", "POLYTAG"), ("seen_extra /= 26", "POLYEXTRA")])
    add(valid_spec("S11.1.3.2-003", "polymorphic_selector", ["polymorphic-selector-control"], src, [feature("dynamic-extra", "obj%extra=26", "obj%extra=-26", "polymorphic-selector-control")]))

    src = header("S11.1.3.2-005", ["internal-end-associate-branch-control"], "ab1132_end_branch") + \
"  integer :: x, after\n  x=1; after=-1\n  associate (a => x)\n    a=44\n    goto 60\n    a=-44\n60 end associate\n  after=x\n" + finish("ab1132_end_branch", "ASSOCIATE BLOCKS END BRANCH OK\n", [("x /= 44", "ENDX"), ("after /= 44", "ENDAFTER")])
    add(valid_spec("S11.1.3.2-005", "internal_end_associate_branch", ["internal-end-associate-branch-control"], src, [feature("pre-branch-assignment", "a=44", "a=-44", "internal-end-associate-branch-control")], "positive-control"))

    src = header("S11.1.3.3-004", ["dynamic-type-and-parameters"], "ab1133_dynamic_type") + \
"  type :: base\n    integer :: tag\n  end type base\n  type, extends(base) :: child\n    integer :: extra\n  end type child\n  class(base), allocatable :: obj\n  integer :: observed\n  allocate(child :: obj)\n  select type (obj)\n  type is (child)\n    obj%tag=3; obj%extra=88\n  end select\n  observed=-1\n  associate (alias => obj)\n    select type (alias)\n    type is (child)\n      observed=alias%extra\n    class default\n      observed=-88\n    end select\n  end associate\n" + finish("ab1133_dynamic_type", "ASSOCIATE BLOCKS DYNAMIC TYPE OK\n", [("observed /= 88", "DYN")])
    add(valid_spec("S11.1.3.3-004", "dynamic_type", ["dynamic-type-and-parameters"], src, [feature("dynamic-observed", "obj%extra=88", "obj%extra=-88", "dynamic-type-and-parameters")]))

    src = header("S11.1.3.3-004", ["optional-selector-present-control"], "ab1133_optional_present") + \
"  integer :: observed\n  observed=-1\n  call use_optional(17, observed)\n" + finish("ab1133_optional_present", "ASSOCIATE BLOCKS OPTIONAL PRESENT OK\n", [("observed /= 22", "OPT")]) + \
"contains\n  subroutine use_optional(arg, out)\n    integer, optional, intent(in) :: arg\n    integer, intent(out) :: out\n    if (.not. present(arg)) error stop\n    associate (alias => arg)\n      out=alias+5\n    end associate\n  end subroutine use_optional\n"
    src = src.replace("end program ab1133_optional_present\ncontains", "contains") + ("end program ab1133_optional_present\n" if not src.endswith("end program ab1133_optional_present\n") else "")
    add(valid_spec("S11.1.3.3-004", "optional_present", ["optional-selector-present-control"], src, [feature("optional-actual", "call use_optional(17, observed)", "call use_optional(18, observed)", "optional-selector-present-control")]))

    src = header("S11.1.3.3-004", ["contiguity-iff-selector"], "ab1133_contiguity") + \
"  integer :: base(6), contiguous_seen, strided_seen\n  base=[1,2,3,4,5,6]; contiguous_seen=-1; strided_seen=-1\n  associate (whole => base)\n    if (is_contiguous(whole)) contiguous_seen=1\n  end associate\n  associate (stride => base(1:6:2))\n    if (.not. is_contiguous(stride)) strided_seen=1\n  end associate\n" + finish("ab1133_contiguity", "ASSOCIATE BLOCKS CONTIGUITY OK\n", [("contiguous_seen /= 1", "CONTIG"), ("strided_seen /= 1", "STRIDE")])
    add(valid_spec("S11.1.3.3-004", "contiguity", ["contiguity-iff-selector"], src, [feature("strided-selector", "base(1:6:2)", "base", "contiguity-iff-selector")]))

    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr="")
        else:
            manifest["expect"] = dict(phase="compile", step="source", outcome="diagnose",
                                      diagnostic=dict(file="source.f90", line=spec["line"], end_line=spec["line"], excludes_any=EXCLUSIONS))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            owner.setdefault("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES.get(rule, ORACLE_PREFIXES[rule] + oracle_text(rule, facets)))
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS.get(rule, LIMIT_PREFIXES[rule] + limitation_text(rule)))
    for rule, remaining in REMAINING_PENDING.items():
        if rule in by_rule and set(by_rule[rule].get("pending", {})) != set(remaining):
            raise ValueError(f"unexpected remaining pending facets for {rule}: {sorted(by_rule[rule].get('pending', {}))}")
    return updated


def oracle_text(rule, facets):
    return ("complete f2023 fixtures in the associate_blocks_11_1 family exercise " + ", ".join(facets) +
            " with integer/logical inquiries or exact scalar sentinel values derived from Fortran 2023 11.1 text. "
            "Each claimed facet has a distinct assertion and a feature-level mutation recorded in the generator; "
            "numbered constraint negatives have one-property conforming controls and line-anchored diagnostics.")


def limitation_text(rule):
    return ("only the listed associate_blocks_11_1 facets are represented. Unselected branch-entry diagnostics for "
            "unnumbered prose, coindexed/coarray cases, procedure-pointer selector exclusions, kind-availability, "
            "ASYNCHRONOUS/VOLATILE and no-OPTIONAL/no-ALLOCATABLE/no-POINTER attribute source contrasts remain "
            "pending with their catalogue reasons. The fixtures do not assert addresses, copy temporaries, storage layout, "
            "message wording, procedure call counts except the explicit selector-evaluation counter, or processor-dependent values.")


ORACLES = {}
LIMITATIONS = {}


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
    summary = (SUMMARY_BEGIN + "\n## Associate/block 11.1 executable fixtures\n\n"
               "The associate_blocks_11_1 generator adds bounded positive and numbered-diagnostic fixtures for "
               "BLOCK execution, legal in-block/outward transfers, procedure references, ASSOCIATE syntax/control "
               "forms, selector evaluation before block execution, declared and dynamic type association, optional "
               "present selectors, and contiguity inheritance. Mutations are feature-level source changes that keep "
               "runtime parents conforming and are checked separately on both compilers; diagnostic negatives are "
               "line-anchored with one-property controls. Existing ASSOCIATE construct fixture paragraphs remain intact.\n"
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
    updates, views, stale = {}, {}, []
    for section in SECTIONS:
        path = root / CATALOGUES[section]
        catalogue = json.loads(path.read_text())
        updated = synced_catalogue(section, catalogue)
        view = render_view(section, updated, root)
        updates[section], views[section] = updated, view
        if catalogue != updated:
            stale.append(CATALOGUES[section])
        if (root / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    stale.extend(path.relative_to(root).as_posix() for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw)
    if check:
        if stale:
            raise ValueError("stale associate_blocks_11_1 family: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updates[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs


def mutant_source(spec, mutation):
    raw = spec["source"]
    if raw.count(mutation["expected"]) != 1:
        raise ValueError(spec["id"] + " mutation token is not unique: " + mutation["id"])
    return raw.replace(mutation["expected"], mutation["replacement"], 1)


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    flag = (("--std=" if "lfortran" in name else "-std=") + std) if std else ""
    return [str(compiler)] + ([flag] if flag else []) + [str(source), "-o", str(output)]


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(compiler).name.lower() else "gfortran"


KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "block_completion_causes",
        "internal_end_associate_branch",
    },
}


def check_mutations(root, compiler, std):
    specs = source_specs()
    work = Path(root) / ".associate_blocks_11_1_mutation_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    family = compiler_family(compiler)
    total = skipped = skipped_parents = 0
    try:
        for spec in specs.values():
            if spec["kind"] != "valid":
                continue
            case_dir = work / (spec["variant"] + "_parent")
            case_dir.mkdir()
            src = case_dir / "source.f90"
            exe = case_dir / "program"
            src.write_text(spec["source"])
            built = subprocess.run(compiler_command(compiler, std, src, exe), cwd=case_dir,
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if built.returncode != 0:
                parent_failure = f"compile failed: {built.stdout}{built.stderr}"
            else:
                ran = subprocess.run([str(exe)], cwd=case_dir, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, timeout=30)
                parent_failure = (
                    "" if ran.returncode == 0 and ran.stdout == spec["completion"]
                    else f"run failed: {ran.returncode} {ran.stdout} {ran.stderr}")
            if parent_failure:
                if spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set()):
                    skipped += len(spec["mutations"])
                    skipped_parents += 1
                    continue
                raise RuntimeError(f"parent {spec['id']} failed: {parent_failure}")
            for index, mutation in enumerate(spec["mutations"]):
                label = mutation["id"]
                case_dir = work / (spec["variant"] + f"_mut_{index:03d}")
                case_dir.mkdir()
                src = case_dir / "source.f90"
                exe = case_dir / "program"
                src.write_text(mutant_source(spec, mutation))
                built = subprocess.run(compiler_command(compiler, std, src, exe), cwd=case_dir,
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if built.returncode != 0:
                    raise RuntimeError(f"{label} for {spec['id']} did not compile: {built.stdout}{built.stderr}")
                ran = subprocess.run([str(exe)], cwd=case_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                total += 1
                if ran.returncode == 0 and ran.stdout == spec["completion"]:
                    raise RuntimeError(f"mutation survived: {spec['id']} {label}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return total, skipped, skipped_parents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sync-catalogue", action="store_true")
    ap.add_argument("--check-mutations", action="store_true")
    ap.add_argument("--compiler")
    ap.add_argument("--std")
    args = ap.parse_args()
    if args.check_mutations:
        if not args.compiler or not args.std:
            ap.error("--check-mutations requires --compiler and --std")
        total, skipped, skipped_parents = check_mutations(args.root, args.compiler, args.std)
        note = f"; skipped {skipped} mutants from {skipped_parents} known parent failures" if skipped else ""
        print(f"Checked {total} associate_blocks_11_1 feature mutations with {args.compiler}{note}.")
        return
    if args.check and args.sync_catalogue:
        ap.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} associate_blocks_11_1 cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets and "
          f"{sum(len(s['mutations']) for s in specs.values())} feature mutations.")

if __name__ == "__main__":
    main()
