#!/usr/bin/env python3
"""BLOCK and branch-control fixtures for Fortran 2023 11.1.4 and 11.2."""
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
PREFIX = "block_branch_"
CATALOGUES = {
    "11.1.4": "doc/catalogues/block_construct_11_1_4.json",
    "11.2.1": "doc/catalogues/branch_concepts_11_2_1.json",
    "11.2.2": "doc/catalogues/go_to_statement_11_2_2.json",
    "11.2.3": "doc/catalogues/computed_go_to_statement_11_2_3.json",
}
VIEWS = {
    "11.1.4": "doc/fortran_2023_11_1_4.md",
    "11.2.1": "doc/fortran_2023_11_2_1.md",
    "11.2.2": "doc/fortran_2023_11_2_2.md",
    "11.2.3": "doc/fortran_2023_11_2_3.md",
}
SUMMARY_BEGIN = "<!-- BEGIN BLOCK BRANCH 11.1.4 11.2 FIXTURES -->"
SUMMARY_END = "<!-- END BLOCK BRANCH 11.1.4 11.2 FIXTURES -->"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "assert", "asr", "verifier", "out of memory", "traceback",
    "segmentation", "bus error", "abort", "cannot read module",
)
KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "S11_1_4_003_valid__block_spec_expression_bound",
        "S11_1_4_004_valid__block_internal_end_branch",
    }
}
SELECTED = {
    "S11.1.4-001": ["block-executable-construct-control", "declarations-in-block-source"],
    "C1107": [
        "ordinary-declaration-control", "common-in-block-rejected", "equivalence-in-block-rejected",
        "intent-in-block-rejected", "namelist-in-block-rejected", "optional-in-block-rejected",
        "statement-function-in-block-rejected", "value-in-block-rejected",
    ],
    "C1108": ["listed-save-entity-control", "common-block-save-in-block-rejected"],
    "C1110": ["matching-block-construct-name-control", "end-block-name-mismatch-rejected", "unnamed-block-end-name-rejected"],
    "S11.1.4-002": ["block-local-construct-entity-scope", "outer-homonym-unaffected"],
    "S11.1.4-003": ["specification-expressions-evaluated", "block-after-specification-evaluation"],
    "S11.1.4-004": ["internal-end-block-branch-control"],
    "S11.2.1-001": ["branch-alters-normal-sequence", "branch-target-same-inclusive-scope-concept"],
    "R1159": ["go-to-label-form", "label-token-required"],
    "C1174": ["go-to-valid-target-control", "go-to-nonbranch-target-rejected"],
    "S11.2.2-001": ["go-to-transfers-to-labeled-target", "go-to-skips-fallthrough"],
    "R1160": ["computed-go-to-with-comma", "computed-go-to-without-comma", "label-list-form", "scalar-integer-selector"],
    "C1175": ["computed-go-to-valid-labels-control", "computed-go-to-nonbranch-target-label-rejected"],
    "S11.2.3-001": [
        "selector-expression-evaluated", "first-label-selected", "middle-or-last-label-selected",
        "low-out-of-range-continues", "high-out-of-range-continues",
    ],
}
ORACLE_PREFIX = {
    rule: f"{rule} block-branch fixture family: " for rule in SELECTED
}
LIMIT_PREFIX = {
    rule: f"{rule} block-branch fixture boundaries: " for rule in SELECTED
}
ORACLES = {
    "S11.1.4-001": ORACLE_PREFIX["S11.1.4-001"] + (
        "one run/effect/f2023 program surrounds a reached BLOCK with before/body/after integer events. "
        "The body contains a BLOCK-local declaration and a separate assignment sentinel, so removing the "
        "declaration or changing the body event is load-bearing and normal execution after END BLOCK is observed."
    ),
    "C1107": ORACLE_PREFIX["C1107"] + (
        "one ordinary-declaration run/positive-control BLOCK uses only INTEGER declarations and no excluded "
        "specification form. Seven compile/f2023 negatives each differ from a real control by exactly one excluded "
        "COMMON, EQUIVALENCE, INTENT, NAMELIST, OPTIONAL, statement-function, or VALUE form in the BLOCK "
        "specification part; any error diagnostic at the violating line is sufficient, with unsupported/ICE routes excluded."
    ),
    "C1108": ORACLE_PREFIX["C1108"] + (
        "a run/positive-control/f2023 BLOCK-local INTEGER with SAVE :: kept is entered three times and increments "
        "1/2/3 without a declaration initializer; the conforming no-SAVE mutation reinitializes an unsaved local on "
        "each entry and fails the persistence assertions. A separate compile negative names a common block in the "
        "SAVE list while its control names an ordinary BLOCK-local entity."
    ),
    "C1110": ORACLE_PREFIX["C1110"] + (
        "one matching-name run/positive-control BLOCK proves a named block with the same END BLOCK name is admitted. "
        "Two compile negatives vary only the END BLOCK name: one mismatches a named opener and one supplies a name "
        "for an unnamed BLOCK."
    ),
    "S11.1.4-002": ORACLE_PREFIX["S11.1.4-002"] + (
        "one run/effect/f2023 program initializes an outer integer to101, declares a BLOCK-local homonym initialized "
        "to7, assigns/checks9 inside, and then observes the outer still101 after END BLOCK. Removing the local "
        "declaration makes the same name resolve to the outer variable and fails both local-scope and outer-homonym sentinels."
    ),
    "S11.1.4-003": ORACLE_PREFIX["S11.1.4-003"] + (
        "one run/effect/f2023 program enters a BLOCK whose specification part declares an automatic array with bound "
        "n+1, then the block immediately consumes SIZE(local_values)==4 and writes the fourth element. Mutating the "
        "bound or body value is conforming and fails the inquiry/value assertions without observing expression order."
    ),
    "S11.1.4-004": ORACLE_PREFIX["S11.1.4-004"] + (
        "one run/positive-control/f2023 program branches from inside a BLOCK to a label on that same END BLOCK, "
        "skipping a poison assignment and then checking the after-block value. The paired negative branches from "
        "outside to that END BLOCK label; the label and BLOCK syntax are otherwise the same."
    ),
    "S11.2.1-001": ORACLE_PREFIX["S11.2.1-001"] + (
        "one run/effect/f2023 program uses GO TO to alter the normal sequence from a source statement to a labeled "
        "same-inclusive-scope action statement, with independent fallthrough poison and target sentinels."
    ),
    "R1159": ORACLE_PREFIX["R1159"] + (
        "a run/positive-control/f2023 GO TO has the keyword pair followed by a valid numeric label and reaches that "
        "target; the label-token negative removes only the label token from the same complete source shape."
    ),
    "C1174": ORACLE_PREFIX["C1174"] + (
        "a run/positive-control/f2023 GO TO targets a labeled CONTINUE action statement in the same inclusive scope. "
        "The nonbranch-target negative changes only the target statement to FORMAT with the same label."
    ),
    "S11.2.2-001": ORACLE_PREFIX["S11.2.2-001"] + (
        "one run/effect/f2023 GO TO program sets a pre-branch sentinel, skips a poison fallthrough assignment, and "
        "executes the labeled target as the next effective statement before a common continuation. Retargeting the "
        "GO TO to a different valid label or removing the target update fails distinct assertions."
    ),
    "R1160": ORACLE_PREFIX["R1160"] + (
        "two run/positive-control/f2023 computed GO TO programs cover the comma-present and comma-omitted forms with "
        "multi-label lists and scalar integer selectors. A diagnostic negative changes only the selector to a rank-one "
        "integer array."
    ),
    "C1175": ORACLE_PREFIX["C1175"] + (
        "a run/positive-control/f2023 computed GO TO has every list entry as a same-scope labeled CONTINUE/action "
        "target. The nonbranch-target negative changes one listed label's target statement to FORMAT."
    ),
    "S11.2.3-001": ORACLE_PREFIX["S11.2.3-001"] + (
        "one run/effect/f2023 subroutine evaluates a scalar selector for i=1,2,3,0,4 against a three-label list, "
        "recording first/middle/last target values 11/22/33 and the fallthrough value44 for both low and high "
        "out-of-range cases. Selector, list-order, target-value and fallthrough mutations are conforming and fail."
    ),
}
LIMITATIONS = {
    rule: LIMIT_PREFIX[rule] + (
        "only the listed facets are represented by this generator. Other pending facets in the same requirement, "
        "including ASYNCHRONOUS/VOLATILE/IMPORT BLOCK exceptions, processor-dependent BLOCK specification-expression "
        "order, unsaved local undefined-on-exit behavior, USE/IMPORT ordering, bare SAVE in BLOCK, FORMAT/DATA first "
        "statements, complete branch-cause inventories, complete branch-target kind lists, and same-inclusive-scope "
        "negatives not isolated here remain pending. Diagnostics require a located error, not a fixed wording, rule "
        "number, fatal status, or LFortran agreement."
    ) for rule in SELECTED
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def line_of(source, needle):
    hits = [i + 1 for i, line in enumerate(source.splitlines()) if needle in line]
    if len(hits) != 1:
        raise ValueError(f"line anchor {needle!r} has {len(hits)} hits")
    return hits[0]


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"expected one occurrence of {old!r}")
    return source.replace(old, new, 1)


def valid(id_, rule, facets, source, completion, mutations=(), evidence="effect"):
    return dict(id=id_, rule=rule, kind="valid", evidence=evidence, facets=list(facets),
                source=source, completion=completion, mutations=list(mutations), source_sha256=sha(source.encode("ascii")))


def invalid(id_, rule, facets, source, line, control_id, end_line=None):
    return dict(id=id_, rule=rule, kind="invalid", evidence="effect", facets=list(facets), source=source,
                diagnostic=dict(file="source.f90", line=line, end_line=end_line or line, excludes_any=list(EXCLUSIONS)),
                control_id=control_id, source_sha256=sha(source.encode("ascii")))


def source_specs():
    specs = []
    src = """program block_executable_declaration_control
implicit none
integer :: before_event, body_event, after_event, local_marker
before_event=11
body_event=-1
after_event=-1
local_marker=99
block
  integer :: local_marker
  local_marker=23
  if (before_event /= 11) error stop 1
  body_event=local_marker
end block
after_event=37
if (body_event /= 23) error stop 2
if (after_event /= 37) error stop 3
if (local_marker /= 99) error stop 4
write(*,'(a)') 'BLOCK EXECUTABLE DECLARATION OK'
end program block_executable_declaration_control
"""
    specs.append(valid("S11_1_4_001_valid__block_executable_declaration_control", "S11.1.4-001",
                       SELECTED["S11.1.4-001"], src, "BLOCK EXECUTABLE DECLARATION OK\n", [
        dict(id="remove-local-declaration", facet="declarations-in-block-source",
             source=replace_once(src, "  integer :: local_marker\n", "  ! integer :: local_marker\n")),
        dict(id="poison-body-event", facet="block-executable-construct-control",
             source=replace_once(src, "  body_event=local_marker", "  body_event=local_marker+1")),
    ]))

    scope = """program block_local_homonym_scope
implicit none
integer :: value, inside_value, outside_value
value=101
inside_value=-1
outside_value=-1
block
  integer :: value
  value=7
  if (value /= 7) error stop 1
  value=9
  inside_value=value
end block
outside_value=value
if (inside_value /= 9) error stop 2
if (outside_value /= 101) error stop 3
write(*,'(a)') 'BLOCK LOCAL HOMONYM OK'
end program block_local_homonym_scope
"""
    no_local = replace_once(scope, "  integer :: value\n", "  ! integer :: value\n")
    specs.append(valid("S11_1_4_002_valid__block_local_homonym_scope", "S11.1.4-002",
                       SELECTED["S11.1.4-002"], scope, "BLOCK LOCAL HOMONYM OK\n", [
        dict(id="remove-local-homonym", facet="block-local-construct-entity-scope", source=no_local),
        dict(id="resolve-to-outer-homonym", facet="outer-homonym-unaffected", source=no_local),
    ]))

    spec_expr = """program block_spec_expression_bound
implicit none
integer :: n, observed_size, observed_value
n=3
observed_size=-1
observed_value=-1
block
  integer :: local_values(n+1)
  local_values=[11,13,17,19]
  observed_size=size(local_values)
  observed_value=local_values(4)
end block
if (observed_size /= 4) error stop 1
if (observed_value /= 19) error stop 2
write(*,'(a)') 'BLOCK SPEC EXPRESSION OK'
end program block_spec_expression_bound
"""
    specs.append(valid("S11_1_4_003_valid__block_spec_expression_bound", "S11.1.4-003",
                       SELECTED["S11.1.4-003"], spec_expr, "BLOCK SPEC EXPRESSION OK\n", [
        dict(id="change-spec-expression-bound", facet="specification-expressions-evaluated",
             source=replace_once(spec_expr, "integer :: local_values(n+1)", "integer :: local_values(n+2)")),
        dict(id="change-body-value", facet="block-after-specification-evaluation",
             source=replace_once(spec_expr, "17,19", "17,23")),
    ]))

    ordinary = """program block_ordinary_declaration_control
implicit none
integer :: result, local_value
result=-1
local_value=5
block
  integer :: local_value
  local_value=31
  result=local_value
end block
if (result /= 31) error stop 1
if (local_value /= 5) error stop 2
write(*,'(a)') 'BLOCK ORDINARY DECLARATION OK'
end program block_ordinary_declaration_control
"""
    specs.append(valid("C1107_valid__block_ordinary_declaration_control", "C1107",
                       ["ordinary-declaration-control"], ordinary, "BLOCK ORDINARY DECLARATION OK\n",
                       [dict(id="remove-ordinary-declaration", facet="ordinary-declaration-control",
                             source=replace_once(ordinary, "  integer :: local_value\n", "  ! integer :: local_value\n"))],
                       evidence="positive-control"))

    c1107_cases = {
        "common": ("common-in-block-rejected", "  integer :: local_value\n  common /blk/ local_value\n", "common /blk/"),
        "equivalence": ("equivalence-in-block-rejected", "  integer :: local_value, alias_value\n  equivalence (local_value, alias_value)\n", "equivalence"),
        "intent": ("intent-in-block-rejected", "  integer :: local_value\n  intent(in) :: local_value\n", "intent(in)"),
        "namelist": ("namelist-in-block-rejected", "  integer :: local_value\n  namelist /nml/ local_value\n", "namelist"),
        "optional": ("optional-in-block-rejected", "  integer :: local_value\n  optional :: local_value\n", "optional"),
        "statement_function": ("statement-function-in-block-rejected", "  integer :: local_value\n  local_value(i)=i+1\n", "local_value(i)"),
        "value": ("value-in-block-rejected", "  integer :: local_value\n  value :: local_value\n", "value ::"),
    }
    for variant, (facet, form, anchor) in c1107_cases.items():
        invalid_src = ordinary.replace("  integer :: local_value\n", form)
        specs.append(invalid(f"C1107_invalid__block_{variant}", "C1107", [facet], invalid_src,
                             line_of(invalid_src, anchor), "C1107_valid__block_ordinary_declaration_control"))

    save_src = """program block_save_local_persists
implicit none
integer :: pass, observed(3)
observed=-1
do pass=1,3
  block
    integer :: kept
    save :: kept
    if (pass == 1) kept=0
    kept=kept+1
    observed(pass)=kept
  end block
end do
if (any(observed /= [1,2,3])) error stop 1
write(*,'(a)') 'BLOCK SAVE LOCAL OK'
end program block_save_local_persists
"""
    save_mut = replace_once(save_src, "    save :: kept\n    if (pass == 1) kept=0\n", "    ! no saved entity list here\n    kept=0\n")
    specs.append(valid("C1108_valid__block_save_local_persists", "C1108", ["listed-save-entity-control"],
                       save_src, "BLOCK SAVE LOCAL OK\n", [
        dict(id="remove-save-and-reset-unsaved-local", facet="listed-save-entity-control", source=save_mut)
    ], evidence="positive-control"))
    common_save = """program block_common_save_name
implicit none
integer :: outer_value
common /outer_block/ outer_value
block
  save /outer_block/
  outer_value=1
end block
end program block_common_save_name
"""
    specs.append(invalid("C1108_invalid__block_common_save_name", "C1108",
                         ["common-block-save-in-block-rejected"], common_save,
                         line_of(common_save, "save /outer_block/"), "C1108_valid__block_save_local_persists"))

    name_ctrl = """program block_name_match_control
implicit none
integer :: value
value=0
named_region: block
  value=17
end block named_region
if (value /= 17) error stop 1
write(*,'(a)') 'BLOCK NAME MATCH OK'
end program block_name_match_control
"""
    specs.append(valid("C1110_valid__block_name_match_control", "C1110",
                       ["matching-block-construct-name-control"], name_ctrl, "BLOCK NAME MATCH OK\n",
                       [dict(id="change-named-block-body", facet="matching-block-construct-name-control",
                             source=replace_once(name_ctrl, "value=17", "value=19"))], evidence="positive-control"))
    mismatch = replace_once(name_ctrl, "end block named_region", "end block other_region")
    specs.append(invalid("C1110_invalid__block_end_name_mismatch", "C1110",
                         ["end-block-name-mismatch-rejected"], mismatch,
                         line_of(mismatch, "end block other_region"), "C1110_valid__block_name_match_control"))
    unnamed = name_ctrl.replace("named_region: block", "block").replace("end block named_region", "end block stray_name")
    specs.append(invalid("C1110_invalid__unnamed_block_end_name", "C1110",
                         ["unnamed-block-end-name-rejected"], unnamed,
                         line_of(unnamed, "end block stray_name"), "C1110_valid__block_name_match_control"))

    end_branch = """program block_internal_end_branch
implicit none
integer :: value
value=5
block
  value=11
  go to 100
  value=-99
100 end block
if (value /= 11) error stop 1
write(*,'(a)') 'BLOCK INTERNAL END BRANCH OK'
end program block_internal_end_branch
"""
    specs.append(valid("S11_1_4_004_valid__block_internal_end_branch", "S11.1.4-004",
                       ["internal-end-block-branch-control"], end_branch, "BLOCK INTERNAL END BRANCH OK\n",
                       [dict(id="retarget-inside-branch-before-poison", facet="internal-end-block-branch-control",
                             source=replace_once(end_branch, "go to 100", "go to 90").replace("  value=-99\n100 end block", "90 value=-99\n100 end block"))],
                       evidence="positive-control"))
    branch = """program branch_alters_sequence
implicit none
integer :: trace
trace=10
go to 100
trace=-99
100 trace=trace+5
if (trace /= 15) error stop 1
write(*,'(a)') 'BRANCH ALTER SEQUENCE OK'
end program branch_alters_sequence
"""
    specs.append(valid("S11_2_1_001_valid__branch_alters_sequence", "S11.2.1-001",
                       SELECTED["S11.2.1-001"], branch, "BRANCH ALTER SEQUENCE OK\n", [
        dict(id="disable-branch-transfer", facet="branch-alters-normal-sequence",
             source=replace_once(branch, "go to 100", "go to 90").replace("trace=-99\n100", "90 trace=-99\n100")),
        dict(id="retarget-outside-intended-label", facet="branch-target-same-inclusive-scope-concept",
             source=replace_once(branch, "go to 100", "go to 90").replace("trace=-99\n100", "90 trace=-99\n100")),
    ]))

    goto_form = """program go_to_label_form_control
implicit none
integer :: value
value=0
go to 100
value=-1
100 value=23
90 continue
if (value /= 23) error stop 1
write(*,'(a)') 'GO TO LABEL FORM OK'
end program go_to_label_form_control
"""
    specs.append(valid("R1159_valid__go_to_label_form_control", "R1159", ["go-to-label-form"],
                       goto_form, "GO TO LABEL FORM OK\n", [
        dict(id="retarget-label-form", facet="go-to-label-form",
             source=replace_once(goto_form, "go to 100", "go to 90"))
    ], evidence="positive-control"))
    missing = replace_once(goto_form, "go to 100", "go to")
    specs.append(invalid("R1159_invalid__go_to_missing_label", "R1159", ["label-token-required"],
                         missing, line_of(missing, "go to"), "R1159_valid__go_to_label_form_control"))

    c1174_ctrl = goto_form.replace("go_to_label_form_control", "go_to_valid_target_control").replace("GO TO LABEL FORM OK", "GO TO VALID TARGET OK")
    specs.append(valid("C1174_valid__go_to_valid_target_control", "C1174", ["go-to-valid-target-control"],
                       c1174_ctrl, "GO TO VALID TARGET OK\n", [
        dict(id="change-valid-target-value", facet="go-to-valid-target-control",
             source=replace_once(c1174_ctrl, "100 value=23", "100 value=29"))
    ], evidence="positive-control"))
    nonbranch = """program go_to_nonbranch_format_target
implicit none
go to 100
100 format('x')
end program go_to_nonbranch_format_target
"""
    specs.append(invalid("C1174_invalid__go_to_nonbranch_format_target", "C1174",
                         ["go-to-nonbranch-target-rejected"], nonbranch,
                         line_of(nonbranch, "100 format"), "C1174_valid__go_to_valid_target_control"))

    goto_flow = """program go_to_exact_flow
implicit none
integer :: trace, skipped
trace=100
skipped=0
go to 200
skipped=-77
200 trace=trace+7
if (trace /= 107) error stop 1
if (skipped /= 0) error stop 2
write(*,'(a)') 'GO TO EXACT FLOW OK'
end program go_to_exact_flow
"""
    specs.append(valid("S11_2_2_001_valid__go_to_exact_flow", "S11.2.2-001",
                       SELECTED["S11.2.2-001"], goto_flow, "GO TO EXACT FLOW OK\n", [
        dict(id="retarget-go-to-before-fallthrough", facet="go-to-transfers-to-labeled-target",
             source=replace_once(goto_flow, "go to 200", "go to 150").replace("skipped=-77\n200", "150 skipped=-77\n200")),
        dict(id="remove-target-update", facet="go-to-skips-fallthrough",
             source=replace_once(goto_flow, "200 trace=trace+7", "200 trace=trace+0")),
    ]))

    comp_comma = """program computed_go_to_comma_form
implicit none
integer :: value, selector
selector=2
value=-1
go to (100,200), selector
value=-9
go to 300
100 value=11
go to 300
200 value=22
300 if (value /= 22) error stop 1
write(*,'(a)') 'COMPUTED GO TO COMMA OK'
end program computed_go_to_comma_form
"""
    specs.append(valid("R1160_valid__computed_go_to_comma_form", "R1160",
                       ["computed-go-to-with-comma", "label-list-form"], comp_comma,
                       "COMPUTED GO TO COMMA OK\n", [
        dict(id="swap-comma-label-list", facet="label-list-form",
             source=replace_once(comp_comma, "go to (100,200), selector", "go to (200,100), selector")),
        dict(id="change-comma-selector", facet="computed-go-to-with-comma",
             source=replace_once(comp_comma, "selector=2", "selector=1")),
    ], evidence="positive-control"))
    comp_no = comp_comma.replace("computed_go_to_comma_form", "computed_go_to_without_comma").replace("go to (100,200), selector", "go to (100,200) selector").replace("COMPUTED GO TO COMMA OK", "COMPUTED GO TO NO COMMA OK")
    specs.append(valid("R1160_valid__computed_go_to_without_comma", "R1160",
                       ["computed-go-to-without-comma"], comp_no, "COMPUTED GO TO NO COMMA OK\n", [
        dict(id="change-no-comma-selector", facet="computed-go-to-without-comma",
             source=replace_once(comp_no, "selector=2", "selector=1"))
    ], evidence="positive-control"))
    nonscalar = """program computed_go_to_array_selector
implicit none
integer :: idx(1)
idx=[1]
go to (100), idx
100 continue
end program computed_go_to_array_selector
"""
    specs.append(invalid("R1160_invalid__computed_go_to_array_selector", "R1160",
                         ["scalar-integer-selector"], nonscalar,
                         line_of(nonscalar, "go to (100), idx"), "R1160_valid__computed_go_to_comma_form"))

    c1175_ctrl = comp_comma.replace("computed_go_to_comma_form", "computed_go_to_valid_labels").replace("COMPUTED GO TO COMMA OK", "COMPUTED GO TO VALID LABELS OK")
    specs.append(valid("C1175_valid__computed_go_to_valid_labels", "C1175",
                       ["computed-go-to-valid-labels-control"], c1175_ctrl,
                       "COMPUTED GO TO VALID LABELS OK\n", [
        dict(id="change-computed-valid-target-value", facet="computed-go-to-valid-labels-control",
             source=replace_once(c1175_ctrl, "200 value=22", "200 value=24"))
    ], evidence="positive-control"))
    comp_nonbranch = """program computed_go_to_format_target
implicit none
go to (100), 1
100 format('x')
end program computed_go_to_format_target
"""
    specs.append(invalid("C1175_invalid__computed_go_to_format_target", "C1175",
                         ["computed-go-to-nonbranch-target-label-rejected"], comp_nonbranch,
                         line_of(comp_nonbranch, "go to (100)"), "C1175_valid__computed_go_to_valid_labels",
                         end_line=line_of(comp_nonbranch, "100 format")))

    select = """program computed_go_to_selection
implicit none
integer :: observed(5)
observed=-99
call choose(1, observed(1))
call choose(2, observed(2))
call choose(3, observed(3))
call choose(0, observed(4))
call choose(4, observed(5))
if (any(observed /= [11,22,33,44,44])) error stop 1
write(*,'(a)') 'COMPUTED GO TO SELECTION OK'
contains
subroutine choose(selector, out)
  implicit none
  integer, intent(in) :: selector
  integer, intent(out) :: out
  out=-7
  go to (100,200,300), selector
  out=44
  return
100 out=11
  return
200 out=22
  return
300 out=33
end subroutine choose
end program computed_go_to_selection
"""
    specs.append(valid("S11_2_3_001_valid__computed_go_to_selection", "S11.2.3-001",
                       SELECTED["S11.2.3-001"], select, "COMPUTED GO TO SELECTION OK\n", [
        dict(id="change-first-label-target", facet="first-label-selected",
             source=replace_once(select, "100 out=11", "100 out=12")),
        dict(id="change-middle-label-target", facet="middle-or-last-label-selected",
             source=replace_once(select, "200 out=22", "200 out=24")),
        dict(id="change-selector-expression-argument", facet="selector-expression-evaluated",
             source=replace_once(select, "call choose(2, observed(2))", "call choose(1, observed(2))")),
        dict(id="change-low-out-of-range-fallthrough", facet="low-out-of-range-continues",
             source=replace_once(select, "call choose(0, observed(4))", "call choose(1, observed(4))")),
        dict(id="change-high-out-of-range-fallthrough", facet="high-out-of-range-continues",
             source=replace_once(select, "call choose(4, observed(5))", "call choose(3, observed(5))")),
    ]))
    return {spec["id"]: spec for spec in specs}


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["id"].lower().replace(".", "_").replace("__", "_"))
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                      stdout=spec["completion"], stderr="")
        else:
            manifest["expect"] = dict(phase="compile", step="source", outcome="diagnose",
                                      diagnostic=spec["diagnostic"])
        spec["manifest"] = manifest
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def section_for_rule(rule):
    if rule in {"S11.1.4-001", "C1107", "C1108", "C1110", "S11.1.4-002", "S11.1.4-003", "S11.1.4-004"}:
        return "11.1.4"
    if rule == "S11.2.1-001":
        return "11.2.1"
    if rule in {"R1159", "C1174", "S11.2.2-001"}:
        return "11.2.2"
    if rule in {"R1160", "C1175", "S11.2.3-001"}:
        return "11.2.3"
    raise ValueError(rule)


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    selected_rules = [rule for rule in SELECTED if section_for_rule(rule) == section]
    for rule in selected_rules:
        rows = [row for row in updated["requirements"] if row["id"] == rule]
        if len(rows) != 1 or not set(SELECTED[rule]) <= set(rows[0]["facets"]):
            raise ValueError(f"selected facets changed for {rule}")
        row = rows[0]
        for facet in SELECTED[rule]:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMITATIONS[rule])
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated-region boundaries changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    owned_rules = [rule for rule in SELECTED if section_for_rule(rule) == section]
    summary = (SUMMARY_BEGIN + "\n"
               f"## BLOCK/branch executable fixture packet for {section}\n\n"
               f"This packet adds generated f2023 fixtures for {', '.join(owned_rules)}. Runtime cases use integer "
               "sentinels and exact completion output. Diagnostic cases require a located error at the violating "
               "line and exclude unsupported-feature/internal-error routes. Pure processor latitude and facets whose "
               "single-image oracle is not isolated remain pending in the catalogue.\n"
               + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError(f"summary boundaries changed for {section}")
        lead, owned = before.split(SUMMARY_BEGIN)
        _, trail = owned.split(SUMMARY_END)
        before = lead + summary + trail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    views = {}
    for section, rel in CATALOGUES.items():
        original = json.loads((root / rel).read_text())
        updated = synced_catalogue(section, original)
        updated_catalogues[section] = (original, updated)
        views[section] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, rel in CATALOGUES.items():
            original, updated = updated_catalogues[section]
            if original != updated:
                stale.append(rel)
            if (root / VIEWS[section]).read_text() != views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale block-branch fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogue:
            for section, rel in CATALOGUES.items():
                (root / rel).write_text(json.dumps(updated_catalogues[section][1], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs


def compiler_family(compiler):
    name = Path(compiler).name.lower()
    return "lfortran" if "lfortran" in name else "gfortran"


def compile_cmd(compiler, std, source, output):
    if compiler_family(compiler) == "lfortran":
        return [compiler, f"--std={std}", str(source), "-o", str(output)]
    return [compiler, f"-std={std}", str(source), "-o", str(output)]


def run_source(compiler, std, cwd, source, exe):
    comp = subprocess.run(compile_cmd(compiler, std, source, exe), cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if comp.returncode != 0:
        return "compile-fail", comp.stdout
    run = subprocess.run([str(exe)], cwd=cwd, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=30)
    return ("pass" if run.returncode == 0 else "run-fail"), run.stdout


def check_mutations(root, compiler, std):
    root = Path(root)
    specs = generate(root, check=False, sync_catalogue=False)
    mutations = [(spec, mutation) for spec in specs.values() if spec["kind"] == "valid" for mutation in spec["mutations"]]
    workspace = root / ".block_branch_11_1_4_11_2_mutations"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    failures = []
    checked = skipped = 0
    family = compiler_family(compiler)
    try:
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['id']}_{mutation['id']}"
            case_dir.mkdir()
            parent = case_dir / "parent.f90"
            parent_exe = case_dir / "parent"
            parent.write_text(spec["source"])
            parent_status, parent_output = run_source(compiler, std, case_dir, parent, parent_exe)
            if parent_status != "pass":
                if spec["id"] in KNOWN_PARENT_FAILURES.get(family, set()):
                    skipped += 1
                    continue
                failures.append(f"{spec['id']} parent did not pass ({parent_status}):\n{parent_output}")
                continue
            source = case_dir / "source.f90"
            exe = case_dir / "program"
            source.write_text(mutation["source"])
            status, output = run_source(compiler, std, case_dir, source, exe)
            if status == "compile-fail":
                failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{output}")
            elif status == "pass":
                failures.append(f"{spec['id']}:{mutation['id']} survived")
            else:
                checked += 1
        if failures:
            raise SystemExit("\n\n".join(failures))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    note = f"; skipped {skipped} known parent-failure mutants" if skipped else ""
    print(f"Mutation check: {checked}/{checked} mutants failed for {compiler} ({std}){note}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--check-mutations", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.check_mutations))) > 1:
        parser.error("--check, --sync-catalogue and --check-mutations are separate operations")
    if args.check_mutations:
        if not args.compiler or not args.std:
            parser.error("--check-mutations requires --compiler and --std")
        check_mutations(args.root, args.compiler, args.std)
        return
    specs = generate(args.root, check=args.check, sync_catalogue=args.sync_catalogue)
    facets = sum(len(spec["facets"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} block/branch cases and {facets} facet bindings.")


if __name__ == "__main__":
    main()
