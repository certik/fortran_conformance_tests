#!/usr/bin/env python3
"""Fixture packet for Fortran 2023 8.6.12-8.6.17 attribute statements."""

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
PREFIX = "attribute_statements_8_6_b"
WORKDIR = ".attribute_statements_8_6_b_mutations"
EXCLUSIONS = (
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "assert", "asr", "verifier", "out of memory", "traceback",
    "segmentation", "bus error", "abort", "cannot open module", "cannot read module",
)
CATALOGUES = {
    "8.6.12": "doc/catalogues/pointer_statement_8_6_12.json",
    "8.6.13": "doc/catalogues/protected_statement_8_6_13.json",
    "8.6.14": "doc/catalogues/save_statement_8_6_14.json",
    "8.6.15": "doc/catalogues/target_statement_8_6_15.json",
    "8.6.16": "doc/catalogues/value_statement_8_6_16.json",
    "8.6.17": "doc/catalogues/volatile_statement_8_6_17.json",
}
VIEWS = {
    section: path.replace("doc/catalogues/", "doc/fortran_2023_").replace("_statement", "").replace(".json", ".md")
    for section, path in CATALOGUES.items()
}
# Keep the exact reviewed view names.
VIEWS.update({
    "8.6.12": "doc/fortran_2023_8_6_12.md",
    "8.6.13": "doc/fortran_2023_8_6_13.md",
    "8.6.14": "doc/fortran_2023_8_6_14.md",
    "8.6.15": "doc/fortran_2023_8_6_15.md",
    "8.6.16": "doc/fortran_2023_8_6_16.md",
    "8.6.17": "doc/fortran_2023_8_6_17.md",
})
SELECTED = {
    "8.6.12": {
        "R857": ["inline-rank-two"],
    },
    "8.6.13": {
        "R858": ["missing-list-exclusion", "name-not-declarator"],
    },
    "8.6.14": {
        "C893": ["bare-and-listed-statements"],
    },
    "8.6.15": {
        "R863": ["inline-explicit-array-shape"],
    },
    "8.6.16": {
        "R864": ["multiple-data-dummies", "required-name-list", "single-colon-repair", "list-separator-repairs",
                 "anonymous-object-and-component-source"],
    },
    "8.6.17": {
        "R865": ["required-name-list", "single-colon-repair", "list-separator-repairs",
                 "name-not-designator"],
    },
}
ALL_RULES = ("R856", "R857", "C892", "R858", "R859", "R860", "C893", "R862", "R863", "R864", "R865")
ORACLE_PREFIX = {rule: f"Batch320 {rule} attribute-statement fixtures: " for rule in ALL_RULES}
LIMIT_PREFIX = {rule: f"Batch320 {rule} limits: " for rule in ALL_RULES}
ORACLES = {
    "R856": ORACLE_PREFIX["R856"] + "three run controls use POINTER statements with and without double colons, and one mixed data/procedure-pointer list. Pointer assignment, ASSOCIATED, and integer/procedure results prove the named entities really acquired the POINTER attribute through the statement occurrence.",
    "R857": ORACLE_PREFIX["R857"] + "the rank-two deferred-shape data-pointer declaration is exercised through valid pointer association. The fixture directly asserts RANK/SIZE and payload after association; its feature mutant changes the pointer declaration and target to rank one so the rank assertion fails.",
    "C892": ORACLE_PREFIX["C892"] + "the procedure-pointer list member is declared by a PROCEDURE declaration without POINTER and receives POINTER from the statement; the PROCEDURE declaration supplies the EXTERNAL route and the associated callback is invoked only after owner-side association.",
    "R858": ORACLE_PREFIX["R858"] + "two diagnostic pairs isolate an omitted PROTECTED entity list and an array declarator suffix, each repaired by adding or retaining the same eligible module entity. No syntax-form admission facet is claimed without a malformed-statement control.",
    "R859": ORACLE_PREFIX["R859"] + "SAVE statement controls cover listed forms with and without double colons, a bare omitted-list form, and a mixed list containing an ordinary variable, procedure pointer, and named COMMON block. A same-scope bare-plus-listed negative is paired with the one-deletion control.",
    "R860": ORACLE_PREFIX["R860"] + "the SAVE mixed-list control resolves a local object name, a procedure-pointer name with a complete abstract interface, and slash-delimited named COMMON block; no COMMON member is individually listed.",
    "C893": ORACLE_PREFIX["C893"] + "a numbered diagnostic has one bare SAVE and one listed SAVE in the same subroutine; deleting only the listed statement yields the passing control, so the omitted-list antecedent and same-scope forbidden appearance are fixed.",
    "R862": ORACLE_PREFIX["R862"] + "TARGET statement controls cover optional-colon spelling and multiple scalar target declarations. Pointer assignment to each listed target plus value checks proves the statement-supplied TARGET attribute is load-bearing.",
    "R863": ORACLE_PREFIX["R863"] + "one inline array-shape control declares rank-one and rank-two TARGET objects through R863 and checks direct RANK/SIZE/LBOUND/UBOUND and payload properties. Its feature mutant changes the inline shape while preserving a conforming program, so the shape assertion fails.",
    "R864": ORACLE_PREFIX["R864"] + "VALUE statement controls cover a two-dummy list and anonymous effective-object behavior. Calls mutate local VALUE dummies and then assert caller actuals remain unchanged; feature mutants remove VALUE from individual dummies. Three diagnostic pairs isolate missing list, single colon, and comma defects with one-property repairs.",
    "R865": ORACLE_PREFIX["R865"] + "four diagnostics isolate VOLATILE missing-list, single-colon, missing-comma, and array-element designator forms with source-minimal repairs. No valid VOLATILE syntax-form facet is claimed without a malformed-statement control.",
}
LIMITS = {
    "R856": LIMIT_PREFIX["R856"] + "only ordinary INTEGER data pointers and one integer procedure pointer are covered; empty-list and punctuation negatives remain pending.",
    "R857": LIMIT_PREFIX["R857"] + "only the rank-two deferred-shape data branch is covered with a runtime-distinguishable rank mutation. Scalar data, procedure-pointer names, rank-one, separately declared rank, malformed shape lists, procedure-array ambiguity, and finite source graph facets remain pending.",
    "C892": LIMIT_PREFIX["C892"] + "only the PROCEDURE-declaration/EXTERNAL route is executed here. Interface-body routes and a robust missing-EXTERNAL diagnostic remain pending because the source review requires a separately adjudicated identity/cause pair.",
    "R858": LIMIT_PREFIX["R858"] + "only the omitted-list and declarator-suffix diagnostics are covered. Optional-colon forms, multi-name/mixed lists, source relationships to C857-C860, single-specification overlaps, use-context links, and pointer/subobject state remain pending. Frozen LFortran rejects the paired conforming PROTECTED controls as unsupported; those reference-valid controls are retained.",
    "R859": LIMIT_PREFIX["R859"] + "admissions are finite statement forms; retained-value semantics, implicit-SAVE source links, separator-only grammar negatives, and canonical occurrence/source relationships remain pending.",
    "R860": LIMIT_PREFIX["R860"] + "only one object/procedure-pointer/common-block mixed list is covered. Missing slash/name diagnostics, designator exclusion, homonym identity, and complete program-wide COMMON obligations remain pending.",
    "C893": LIMIT_PREFIX["C893"] + "only bare-plus-listed statement order is diagnosed. Two bare statements, bare plus type-attribute SAVE, implicit-SAVE controls, BLOCK/scope boundaries, and procedure-attribute overlaps remain pending. Frozen LFortran currently accepts the invalid pair.",
    "R862": LIMIT_PREFIX["R862"] + "only scalar target declaration lists are covered. Empty-list, punctuation repair, and source-relationship facets remain pending.",
    "R863": LIMIT_PREFIX["R863"] + "only small constant explicit array shapes are covered. Coarray declarator groups, deferred coarrays, delimiter/order diagnostics, designator exclusions, and canonical lifetime/source links remain pending. Frozen LFortran mishandles the conforming inline TARGET array declaration on this host.",
    "R864": LIMIT_PREFIX["R864"] + "only ordinary scalar data dummies in non-BIND module procedures are covered. Optional-colon syntax forms, designator, array, interoperability, conflicting-attribute, and canonical component/pointer source relations remain pending. Frozen LFortran rejects VALUE statements as unsupported.",
    "R865": LIMIT_PREFIX["R865"] + "only local grammar repairs are covered. Optional-colon forms, multiple-object admission, USE/HOST/BLOCK scoped effects, pointer/allocatable state, coarray restrictions, subobject propagation, and external-event modality remain pending; no timing or optimizer behavior is asserted.",
}
SUMMARY = {
    "8.6.12": "Batch320 POINTER statement fixtures retain only the rank-two data-pointer facet with direct rank/value assertions and a rank-changing feature mutation; syntax-form admission facets are restored to pending.",
    "8.6.13": "Batch320 PROTECTED statement fixtures retain omitted-list and declarator-suffix diagnostic/control pairs. Frozen LFortran rejects the conforming PROTECTED controls, so those reference-backed failures are reported rather than weakened.",
    "8.6.14": "Batch320 SAVE statement fixtures retain the C893 bare/listed negative-control pair; pure SAVE form-admission facets are restored to pending.",
    "8.6.15": "Batch320 TARGET statement fixtures retain one inline explicit-array shape control with direct rank/bounds inquiries and a shape-changing feature mutation.",
    "8.6.16": "Batch320 VALUE statement fixtures retain scalar dummy-copy observations and syntax diagnostics; frozen LFortran lacks VALUE statement support and is reported as a known parent defect in mutation mode.",
    "8.6.17": "Batch320 VOLATILE statement fixtures retain grammar diagnostics without claiming valid syntax-form or external-event timing facets.",
}
SUMMARY_BEGIN = {section: f"<!-- BEGIN BATCH320 ATTRIBUTE STATEMENTS {section} -->" for section in CATALOGUES}
SUMMARY_END = {section: f"<!-- END BATCH320 ATTRIBUTE STATEMENTS {section} -->" for section in CATALOGUES}
KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "R857_valid__attribute_statements_8_6_b_pointer_rank_two_deferred_shape",
        "R858_valid__attribute_statements_8_6_b_protected_data_double_colon",
        "R858_valid__attribute_statements_8_6_b_protected_mixed_no_colon",
        "R858_valid__attribute_statements_8_6_b_protected_missing_list_control",
        "R858_valid__attribute_statements_8_6_b_protected_declarator_control",
        "R863_valid__attribute_statements_8_6_b_target_inline_array_shape",
        "R864_valid__attribute_statements_8_6_b_value_copy_double_colon",
        "R864_valid__attribute_statements_8_6_b_value_copy_no_colon",
        "R864_valid__attribute_statements_8_6_b_value_missing_list_control",
        "R864_valid__attribute_statements_8_6_b_value_single_colon_control",
        "R864_valid__attribute_statements_8_6_b_value_separator_control",
    }
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def ident(rule, variant, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__{PREFIX}_{variant}"

def locate_line(source, needle):
    matches = [i + 1 for i, line in enumerate(source.splitlines()) if needle in line]
    if len(matches) != 1:
        raise ValueError(f"line anchor {needle!r} matches {matches}")
    return matches[0]

def valid(rule, variant, facets, source, derivation, observations, mutations, evidence="positive-control"):
    return dict(id=ident(rule, variant), rule=rule, variant=variant, kind="valid",
                facets=list(facets), source=source, source_sha256=sha(source.encode("ascii")),
                completion=f"ATTRIBUTE STATEMENTS {variant.upper().replace('_', ' ')} OK\n",
                derivation=derivation, observations=list(observations), mutations=list(mutations), evidence=evidence)

def invalid(rule, variant, facets, source, derivation, diagnostic_line, contains, control_id, repair_note):
    return dict(id=ident(rule, variant, "invalid"), rule=rule, variant=variant, kind="invalid",
                evidence="effect", facets=list(facets), source=source,
                source_sha256=sha(source.encode("ascii")), derivation=derivation,
                diagnostic=dict(file="source.f90", line=diagnostic_line, end_line=diagnostic_line,
                                excludes_any=list(EXCLUSIONS)),
                control_id=control_id, repair_note=repair_note, observations=[], mutations=[])

def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"replacement token {old!r} count {source.count(old)}")
    return source.replace(old, new, 1)

def build_specs():
    specs = []
    pointer_double = """program main
  implicit none
  integer, target :: target_value = 41
  integer :: p
  pointer p
  p => target_value
  if (.not. associated(p, target_value)) error stop 1
  if (p /= 41) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS POINTER SCALAR NO COLON OK'
end program
"""
    specs.append(valid("R856", "pointer_scalar_no_colon", ["no-double-colon-form"], pointer_double,
        "R856 permits POINTER without double colons; pointer assignment to target_value requires p to have the statement-supplied POINTER attribute.",
        ["p is associated with target_value", "p reads 41"],
        [dict(id="change-target-sentinel", replacements=[["target_value = 41", "target_value = 42"]], conforming=True)]))
    pointer_scalar_r857 = """program main
  implicit none
  integer, target :: target_value = 52
  integer :: p
  pointer p
  p => target_value
  if (.not. associated(p, target_value)) error stop 1
  if (rank(p) /= 0) error stop 2
  if (p /= 52) error stop 3
  write(*,'(a)') 'ATTRIBUTE STATEMENTS POINTER SCALAR DATA NAME OK'
end program
"""
    specs.append(valid("R857", "pointer_scalar_data_name", ["scalar-data-name"], pointer_scalar_r857,
        "R857's data-object branch can be a scalar object name with no inline shape; direct RANK on the pointer expression is zero after association.",
        ["p is associated with target_value", "rank(p) is 0", "p reads 52"],
        [dict(id="change-scalar-to-rank-one-pointer", replacements=[
            ["integer, target :: target_value = 52", "integer, target :: target_value(1) = [52]"],
            ["pointer p", "pointer p(:)"],
            ["if (p /= 52) error stop 3", "if (p(1) /= 52) error stop 3"]],
              conforming=True)]))
    pointer_colon = pointer_double.replace("pointer p", "pointer :: p").replace("NO COLON", "DOUBLE COLON")
    specs.append(valid("R856", "pointer_scalar_double_colon", ["double-colon-form"], pointer_colon,
        "R856 permits the optional double-colon form; the subsequent pointer assignment reaches that declaration.",
        ["p is associated with target_value", "p reads 41"],
        [dict(id="change-target-sentinel", replacements=[["target_value = 41", "target_value = 43"]], conforming=True)]))
    pointer_rank2 = """program main
  implicit none
  integer, target :: target_matrix(2,2)
  integer :: p
  pointer :: p(:,:)
  target_matrix = reshape([11, 12, 13, 14], [2, 2])
  p => target_matrix
  if (.not. associated(p, target_matrix)) error stop 1
  if (rank(p) /= 2) error stop 2
  if (size(p) /= 4) error stop 3
  if (p(2,2) /= 14) error stop 4
  write(*,'(a)') 'ATTRIBUTE STATEMENTS POINTER RANK TWO DEFERRED SHAPE OK'
end program
"""
    specs.append(valid("R857", "pointer_rank_two_deferred_shape", ["inline-rank-two"], pointer_rank2,
        "R857's p(:,:) deferred-shape list gives p rank two; direct RANK/SIZE and payload checks are made only after association to a rank-two TARGET.",
        ["rank(p) is 2", "size(p) is 4", "p(2,2) is 14"],
        [dict(id="change-rank-two-to-rank-one-pointer", replacements=[
            ["integer, target :: target_matrix(2,2)", "integer, target :: target_matrix(4)"],
            ["pointer :: p(:,:)", "pointer :: p(:)"],
            ["target_matrix = reshape([11, 12, 13, 14], [2, 2])", "target_matrix = [11, 12, 13, 14]"],
            ["if (p(2,2) /= 14) error stop 4", "if (p(4) /= 14) error stop 4"]],
              conforming=True)]))
    pointer_mixed = """module attribute_statements_pointer_mixed_m
  implicit none
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i) :: cb
  integer :: p
  pointer :: p, cb
contains
  integer function add_five(v)
    integer, intent(in) :: v
    add_five = v + 5
  end function
end module
program main
  use attribute_statements_pointer_mixed_m
  implicit none
  integer, target :: target_value
  target_value = 17
  p => target_value
  cb => add_five
  if (.not. associated(p, target_value)) error stop 1
  if (p /= 17) error stop 2
  if (.not. associated(cb)) error stop 3
  if (cb(6) /= 11) error stop 4
  write(*,'(a)') 'ATTRIBUTE STATEMENTS POINTER MIXED PROCEDURE LIST OK'
end program
"""
    specs.append(valid("R856", "pointer_mixed_procedure_list", ["mixed-data-procedure-list"], pointer_mixed,
        "One POINTER statement lists a data object and a procedure entity; both are subsequently associated and observed.",
        ["p reads target_value 17", "cb(6) returns 11"],
        [dict(id="change-data-target", replacements=[["target_value = 17", "target_value = 18"]], conforming=True)]))
    pointer_proc_name = pointer_mixed.replace("POINTER MIXED PROCEDURE LIST", "POINTER PROCEDURE NAME")
    specs.append(valid("R857", "pointer_procedure_name", ["procedure-pointer-name"], pointer_proc_name,
        "The cb list item is the R857 procedure-pointer-name branch and is called only after procedure pointer association.",
        ["associated(cb) is true", "cb(6) returns 11"],
        [dict(id="change-procedure-result", replacements=[["add_five = v + 5", "add_five = v + 6"]], conforming=True)]))
    pointer_external = pointer_mixed.replace("POINTER MIXED PROCEDURE LIST", "POINTER EXTERNAL STATEMENT ROUTE")
    specs.append(valid("C892", "pointer_external_statement_route", ["external-statement-route"], pointer_external,
        "The PROCEDURE declaration supplies EXTERNAL for cb while the POINTER statement supplies the pointer attribute required by the later association.",
        ["cb is associated with add_five", "cb(6) returns 11"],
        [dict(id="change-callback-result", replacements=[["add_five = v + 5", "add_five = v + 7"]], conforming=True)]))

    protected_data = """module attribute_statements_protected_data_m
  implicit none
  integer :: x = 19
  integer :: y = 23
  protected :: x, y
contains
  subroutine set_values(a, b)
    integer, intent(in) :: a, b
    x = a
    y = b
  end subroutine
end module
program main
  use attribute_statements_protected_data_m, only: x, y, set_values
  implicit none
  call set_values(31, 37)
  if (x /= 31) error stop 1
  if (y /= 37) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS PROTECTED DATA DOUBLE COLON OK'
end program
"""
    specs.append(valid("R858", "protected_data_double_colon", ["double-colon-form", "multiple-module-data"], protected_data,
        "R858 admits PROTECTED :: x,y in a module specification part; owner-module assignment then client reads show the listed entities are the protected variables.",
        ["x is 31", "y is 37"],
        [dict(id="change-owner-x", replacements=[["x = a", "x = a + 1"]], conforming=True),
         dict(id="change-owner-y", replacements=[["y = b", "y = b + 1"]], conforming=True)]))
    protected_mixed = """module attribute_statements_protected_mixed_m
  implicit none
  integer :: x = 5
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer :: cb => null()
  protected x, cb
contains
  integer function triple(v)
    integer, intent(in) :: v
    triple = v * 3
  end function
  subroutine bind_cb()
    cb => triple
  end subroutine
end module
program main
  use attribute_statements_protected_mixed_m, only: x, cb, bind_cb
  implicit none
  call bind_cb()
  if (x /= 5) error stop 1
  if (.not. associated(cb)) error stop 2
  if (cb(7) /= 21) error stop 3
  write(*,'(a)') 'ATTRIBUTE STATEMENTS PROTECTED MIXED NO COLON OK'
end program
"""
    specs.append(valid("R858", "protected_mixed_no_colon", ["no-double-colon-form", "mixed-variable-procedure-pointer"], protected_mixed,
        "R858 also admits omission of both colons; the list contains an ordinary variable and a procedure pointer.",
        ["x is 5", "cb(7) returns 21"],
        [dict(id="change-protected-scalar", replacements=[["integer :: x = 5", "integer :: x = 6"]], conforming=True),
         dict(id="change-procedure-result", replacements=[["triple = v * 3", "triple = v * 4"]], conforming=True)]))
    prot_control = protected_data.replace("protected :: x, y", "protected :: x").replace("call set_values(31, 37)", "call set_values(31, 37)").replace("PROTECTED DATA DOUBLE COLON", "PROTECTED MISSING LIST CONTROL")
    specs.append(valid("R858", "protected_missing_list_control", ["missing-list-exclusion"], prot_control,
        "Adding the existing eligible module variable x repairs the otherwise empty PROTECTED :: statement.",
        ["x is 31", "y is 37"],
        [dict(id="change-owner-x", replacements=[["x = a", "x = a + 2"]], conforming=True)]))
    prot_bad = replace_once(prot_control, "protected :: x", "protected ::")
    specs.append(invalid("R858", "protected_missing_list", ["missing-list-exclusion"], prot_bad,
        "R858 requires a nonempty entity-name list after PROTECTED ::; the paired control adds only x.",
        locate_line(prot_bad, "protected ::"), ["PROTECTED", "protected", "entity", "name"], specs[-1]["id"],
        "insert the already declared eligible module variable x"))
    prot_decl_control = """module attribute_statements_protected_decl_m
  implicit none
  integer :: a(2) = [3, 4]
  protected :: a
contains
  subroutine set_a(v)
    integer, intent(in) :: v
    a(1) = v
  end subroutine
end module
program main
  use attribute_statements_protected_decl_m, only: a, set_a
  implicit none
  call set_a(9)
  if (a(1) /= 9) error stop 1
  if (a(2) /= 4) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS PROTECTED DECLARATOR CONTROL OK'
end program
"""
    specs.append(valid("R858", "protected_declarator_control", ["name-not-declarator"], prot_decl_control,
        "The conforming repair names the whole module array a; the PROTECTED statement has no array-declarator suffix.",
        ["a(1) is set inside the owner", "a(2) remains 4"],
        [dict(id="change-array-element", replacements=[["a(1) = v", "a(1) = v + 1"]], conforming=True)]))
    prot_decl_bad = replace_once(prot_decl_control, "protected :: a", "protected :: a(:)")
    specs.append(invalid("R858", "protected_declarator_suffix", ["name-not-declarator"], prot_decl_bad,
        "R858 takes entity names, not array declarators; deleting only (:) restores the same whole array.",
        locate_line(prot_decl_bad, "protected :: a(:)"), ["PROTECTED", "protected", "syntax", "Syntax"], specs[-1]["id"],
        "delete only the array suffix from the PROTECTED statement"))

    save_double = """subroutine save_listed_double_colon()
  implicit none
  integer :: kept
  save :: kept
  kept = 7
  if (kept /= 7) error stop 1
end subroutine
program main
  implicit none
  call save_listed_double_colon()
  write(*,'(a)') 'ATTRIBUTE STATEMENTS SAVE LISTED DOUBLE COLON OK'
end program
"""
    specs.append(valid("R859", "save_listed_double_colon", ["listed-double-colon-form"], save_double,
        "R859 admits SAVE :: kept with a nonempty saved-entity list in an ordinary subroutine.",
        ["the subroutine reaches the kept value check"],
        [dict(id="change-kept-value", replacements=[["kept = 7", "kept = 8"]], conforming=True)]))
    save_ordinary = save_double.replace("SAVE LISTED DOUBLE COLON", "SAVE ORDINARY VARIABLE")
    specs.append(valid("R860", "save_ordinary_variable", ["ordinary-variable-name"], save_ordinary,
        "The saved entity kept is an ordinary local object name, not a designator or COMMON member.",
        ["kept is assigned and checked as 7"],
        [dict(id="change-kept-value", replacements=[["kept = 7", "kept = 9"]], conforming=True)]))
    save_mixed = """subroutine save_mixed_entities()
  implicit none
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer :: callback
  integer :: member
  common /packet_block/ member
  save callback, /packet_block/
  member = 6
  if (member /= 6) error stop 1
end subroutine
program main
  implicit none
  call save_mixed_entities()
  write(*,'(a)') 'ATTRIBUTE STATEMENTS SAVE MIXED NO COLON OK'
end program
"""
    specs.append(valid("R859", "save_mixed_no_colon", ["listed-no-double-colon-form", "mixed-list-and-separators"], save_mixed,
        "R859 admits the list form without double colons and with comma-separated procedure-pointer and named-COMMON alternatives.",
        ["member is assigned and checked through the COMMON declaration context"],
        [dict(id="change-common-member", replacements=[["member = 6", "member = 7"]], conforming=True)]))
    save_proc_common = save_mixed.replace("SAVE MIXED NO COLON", "SAVE PROCEDURE POINTER AND COMMON")
    specs.append(valid("R860", "save_procedure_pointer_and_common", ["procedure-pointer-name", "named-common-block"], save_proc_common,
        "R860's procedure-pointer-name and /common-block-name/ alternatives are both present in one SAVE list.",
        ["the slash-delimited packet_block is a COMMON block", "callback is a local procedure pointer"],
        [dict(id="change-common-member", replacements=[["member = 6", "member = 8"]], conforming=True)]))
    save_bare = """subroutine save_bare_scope()
  implicit none
  integer :: x
  save
  x = 12
  if (x /= 12) error stop 1
end subroutine
program main
  implicit none
  call save_bare_scope()
  write(*,'(a)') 'ATTRIBUTE STATEMENTS SAVE BARE SCOPE OK'
end program
"""
    specs.append(valid("R859", "save_bare_scope", ["omitted-list-form"], save_bare,
        "R859 admits a SAVE statement with the entire saved-entity list omitted in an ordinary subroutine.",
        ["the subroutine reaches the x value check"],
        [dict(id="change-local-value", replacements=[["x = 12", "x = 13"]], conforming=True)]))
    save_c893_control = replace_once(save_bare, "  x = 12", "  x = 12").replace("SAVE BARE SCOPE", "SAVE C893 CONTROL")
    specs.append(valid("C893", "save_c893_control", ["bare-and-listed-statements"], save_c893_control,
        "Deleting the listed SAVE statement leaves exactly one bare SAVE in the scoping unit.",
        ["the control reaches the x value check"],
        [dict(id="change-local-value", replacements=[["x = 12", "x = 14"]], conforming=True)]))
    save_c893_bad = replace_once(save_c893_control, "  x = 12", "  save :: x\n  x = 12")
    specs.append(invalid("C893", "save_bare_and_listed", ["bare-and-listed-statements"], save_c893_bad,
        "C893 forbids another SAVE statement in the same scope after an omitted-list SAVE appears.",
        locate_line(save_c893_bad, "save :: x"), ["SAVE", "save"], specs[-1]["id"],
        "delete only the listed SAVE :: x statement"))

    target_double = """program main
  implicit none
  integer :: t
  target :: t
  integer, pointer :: p
  t = 33
  p => t
  if (.not. associated(p, t)) error stop 1
  if (p /= 33) error stop 2
  p = 35
  if (t /= 35) error stop 3
  write(*,'(a)') 'ATTRIBUTE STATEMENTS TARGET SCALAR DOUBLE COLON OK'
end program
"""
    specs.append(valid("R862", "target_scalar_double_colon", ["double-colon-form"], target_double,
        "R862 admits TARGET :: t; the subsequent pointer assignment to t requires the statement-supplied TARGET attribute.",
        ["p is associated with t", "assignment through p changes t to 35"],
        [dict(id="change-target-initial-value", replacements=[["t = 33", "t = 34"]], conforming=True)]))
    target_bare_scalar = target_double.replace("TARGET SCALAR DOUBLE COLON", "TARGET BARE SCALAR NAME")
    specs.append(valid("R863", "target_bare_scalar_name", ["bare-scalar-name"], target_bare_scalar,
        "R863's target-decl is the bare object name t with no array or coarray group; pointer association reaches that object.",
        ["p is associated with scalar t", "t is changed to 35 through p"],
        [dict(id="change-pointer-store", replacements=[["p = 35", "p = 36"]], conforming=True)]))
    target_arrays = """program main
  implicit none
  integer :: values, matrix
  target :: values(3), matrix(0:1,2)
  values = [1, 2, 3]
  matrix = reshape([11, 12, 13, 14], [2, 2])
  if (rank(values) /= 1) error stop 1
  if (size(values) /= 3) error stop 2
  if (values(3) /= 3) error stop 3
  if (rank(matrix) /= 2) error stop 4
  if (lbound(matrix, 1) /= 0) error stop 5
  if (ubound(matrix, 1) /= 1) error stop 6
  if (ubound(matrix, 2) /= 2) error stop 7
  if (matrix(1,2) /= 14) error stop 8
  write(*,'(a)') 'ATTRIBUTE STATEMENTS TARGET INLINE ARRAY SHAPE OK'
end program
"""
    specs.append(valid("R863", "target_inline_array_shape", ["inline-explicit-array-shape"], target_arrays,
        "R863 inline array-specs supply rank and bounds for values and matrix; all inquiries are direct on those declared objects.",
        ["values has rank one and size three", "matrix has lower bound 0 and upper bounds 1,2", "matrix(1,2) is 14"],
        [dict(id="change-values-shape", replacements=[
            ["target :: values(3), matrix(0:1,2)", "target :: values(4), matrix(0:1,2)"],
            ["values = [1, 2, 3]", "values = [1, 2, 3, 4]"]], conforming=True)]))
    target_no = target_double.replace("target :: t", "target t").replace("TARGET SCALAR DOUBLE COLON", "TARGET SCALAR NO COLON")
    specs.append(valid("R862", "target_scalar_no_colon", ["no-double-colon-form"], target_no,
        "R862 also admits TARGET t with both colons omitted; the pointer association and store check use the same target.",
        ["p is associated with t", "assignment through p changes t to 35"],
        [dict(id="change-target-initial-value", replacements=[["t = 33", "t = 31"]], conforming=True)]))
    target_multi = """program main
  implicit none
  integer :: first, second
  target :: first, second
  integer, pointer :: p, q
  first = 21
  second = 22
  p => first
  q => second
  if (.not. associated(p, first)) error stop 1
  if (.not. associated(q, second)) error stop 2
  if (p + q /= 43) error stop 3
  write(*,'(a)') 'ATTRIBUTE STATEMENTS TARGET MULTIPLE SCALARS OK'
end program
"""
    specs.append(valid("R862", "target_multiple_scalars", ["multiple-target-declarations"], target_multi,
        "R862's list has two distinct scalar target-decls, each used as a data target in pointer assignment.",
        ["p and q are associated to different targets", "p+q is 43"],
        [dict(id="change-second-target", replacements=[["second = 22", "second = 23"]], conforming=True)]))

    value_double = """module attribute_statements_value_double_m
  implicit none
contains
  subroutine bump(x, y)
    integer :: x, y
    value :: x, y
    x = x + 10
    y = y + 20
  end subroutine
end module
program main
  use attribute_statements_value_double_m
  implicit none
  integer :: a, b
  a = 3
  b = 4
  call bump(a, b)
  if (a /= 3) error stop 1
  if (b /= 4) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VALUE COPY DOUBLE COLON OK'
end program
"""
    specs.append(valid("R864", "value_copy_double_colon", ["double-colon-form", "multiple-data-dummies", "anonymous-object-and-component-source"], value_double,
        "R864 admits VALUE :: x,y; 15.5.2.4 gives present VALUE dummies anonymous definable objects, so local assignments do not alter actuals a and b.",
        ["a remains 3", "b remains 4"],
        [dict(id="remove-value-from-x", replacements=[["    value :: x, y", "    value :: y"]], conforming=True),
         dict(id="remove-value-from-y", replacements=[["    value :: x, y", "    value :: x"]], conforming=True)]))
    value_no = """module attribute_statements_value_no_colon_m
  implicit none
contains
  subroutine bump(x)
    integer :: x
    value x
    x = x + 10
  end subroutine
end module
program main
  use attribute_statements_value_no_colon_m
  implicit none
  integer :: a
  a = 3
  call bump(a)
  if (a /= 3) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VALUE COPY NO COLON OK'
end program
"""
    specs.append(valid("R864", "value_copy_no_colon", ["no-double-colon-form"], value_no,
        "R864 admits VALUE x with both colons omitted; local assignment to x does not alter the actual a.",
        ["a remains 3 after bump"],
        [dict(id="remove-value", replacements=[["    value x", "    continue"]], conforming=True)]))
    val_control = value_no.replace("VALUE COPY NO COLON", "VALUE MISSING LIST CONTROL")
    specs.append(valid("R864", "value_missing_list_control", ["required-name-list"], val_control,
        "Adding the already declared dummy x repairs a VALUE statement with no required list.",
        ["a remains 3 after bump"],
        [dict(id="remove-value", replacements=[["    value x", "    continue"]], conforming=True)]))
    val_bad = replace_once(val_control, "    value x", "    value")
    specs.append(invalid("R864", "value_missing_list", ["required-name-list"], val_bad,
        "R864 requires a nonempty dummy-arg-name list after VALUE.", locate_line(val_bad, "    value"),
        ["Unclassifiable", "Error", "VALUE", "value", "dummy", "name"], specs[-1]["id"], "insert the already declared dummy x"))
    val_colon_control = val_control.replace("VALUE MISSING LIST CONTROL", "VALUE SINGLE COLON CONTROL").replace("    value x", "    value :: x")
    specs.append(valid("R864", "value_single_colon_control", ["single-colon-repair"], val_colon_control,
        "Inserting the second colon repairs VALUE : x while preserving the same dummy.",
        ["a remains 3 after bump"],
        [dict(id="remove-value", replacements=[["    value :: x", "    continue"]], conforming=True)]))
    val_colon_bad = replace_once(val_colon_control, "    value :: x", "    value : x")
    specs.append(invalid("R864", "value_single_colon", ["single-colon-repair"], val_colon_bad,
        "R864 permits zero or two colons, not one colon.", locate_line(val_colon_bad, "value : x"),
        ["VALUE", "value", ":", "colon"], specs[-1]["id"], "insert only the second colon"))
    val_sep_control = value_double.replace("VALUE COPY DOUBLE COLON", "VALUE SEPARATOR CONTROL")
    specs.append(valid("R864", "value_separator_control", ["list-separator-repairs"], val_sep_control,
        "The control has the required comma between two distinct VALUE dummy names.",
        ["a remains 3", "b remains 4"],
        [dict(id="remove-value-from-x", replacements=[["    value :: x, y", "    value :: y"]], conforming=True)]))
    val_sep_bad = replace_once(val_sep_control, "    value :: x, y", "    value :: x y")
    specs.append(invalid("R864", "value_missing_comma", ["list-separator-repairs"], val_sep_bad,
        "The x y spelling omits the R401 comma between dummy names; inserting only the comma gives the control.",
        locate_line(val_sep_bad, "value :: x y"), ["VALUE", "value", "comma", "syntax", "Syntax"], specs[-1]["id"],
        "insert the missing comma between x and y"))

    volatile_double = """program main
  implicit none
  integer :: x, y
  volatile :: x, y
  x = 8
  y = 13
  if (x + y /= 21) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VOLATILE DOUBLE MULTI OK'
end program
"""
    specs.append(valid("R865", "volatile_double_multi", ["double-colon-form", "multiple-object-names"], volatile_double,
        "R865 admits VOLATILE :: x,y for two ordinary variables; the program performs only ordinary portable assignments and reads.",
        ["x+y is 21"],
        [dict(id="change-y", replacements=[["y = 13", "y = 14"]], conforming=True)]))
    volatile_no = volatile_double.replace("volatile :: x, y", "volatile x").replace("x + y /= 21", "x /= 8").replace("VOLATILE DOUBLE MULTI", "VOLATILE NO COLON")
    specs.append(valid("R865", "volatile_no_colon", ["no-double-colon-form"], volatile_no,
        "R865 admits VOLATILE x with both colons omitted in an ordinary local variable context.",
        ["x is 8"],
        [dict(id="change-x", replacements=[["x = 8", "x = 9"]], conforming=True)]))
    vol_missing_control = volatile_no.replace("VOLATILE NO COLON", "VOLATILE MISSING LIST CONTROL")
    specs.append(valid("R865", "volatile_missing_list_control", ["required-name-list"], vol_missing_control,
        "Adding the already declared object x repairs a listless VOLATILE statement.",
        ["x is 8"], [dict(id="change-x", replacements=[["x = 8", "x = 10"]], conforming=True)]))
    vol_missing_bad = replace_once(vol_missing_control, "  volatile x", "  volatile")
    specs.append(invalid("R865", "volatile_missing_list", ["required-name-list"], vol_missing_bad,
        "R865 requires a nonempty object-name list after VOLATILE.", locate_line(vol_missing_bad, "  volatile"),
        ["Unclassifiable", "Error", "VOLATILE", "volatile", "name", "object"], specs[-1]["id"], "insert the already declared object x"))
    vol_colon_control = vol_missing_control.replace("VOLATILE MISSING LIST CONTROL", "VOLATILE SINGLE COLON CONTROL").replace("  volatile x", "  volatile :: x")
    specs.append(valid("R865", "volatile_single_colon_control", ["single-colon-repair"], vol_colon_control,
        "Adding the second colon repairs the unadmitted VOLATILE : x form.",
        ["x is 8"], [dict(id="change-x", replacements=[["x = 8", "x = 11"]], conforming=True)]))
    vol_colon_bad = replace_once(vol_colon_control, "  volatile :: x", "  volatile : x")
    specs.append(invalid("R865", "volatile_single_colon", ["single-colon-repair"], vol_colon_bad,
        "R865 permits an omitted or double-colon separator, not a single colon.", locate_line(vol_colon_bad, "volatile : x"),
        ["VOLATILE", "volatile", ":", "colon"], specs[-1]["id"], "insert only the second colon"))
    vol_sep_control = volatile_double.replace("VOLATILE DOUBLE MULTI", "VOLATILE SEPARATOR CONTROL")
    specs.append(valid("R865", "volatile_separator_control", ["list-separator-repairs"], vol_sep_control,
        "The control has the required comma between two distinct object names.",
        ["x+y is 21"], [dict(id="change-y", replacements=[["y = 13", "y = 15"]], conforming=True)]))
    vol_sep_bad = replace_once(vol_sep_control, "  volatile :: x, y", "  volatile :: x y")
    specs.append(invalid("R865", "volatile_missing_comma", ["list-separator-repairs"], vol_sep_bad,
        "The x y spelling omits the R401 comma between object names.", locate_line(vol_sep_bad, "volatile :: x y"),
        ["VOLATILE", "volatile", "comma", "syntax", "Syntax"], specs[-1]["id"], "insert the missing comma"))
    vol_design_control = """program main
  implicit none
  integer :: a(2)
  volatile :: a
  a = [5, 6]
  if (a(1) + a(2) /= 11) error stop 1
  write(*,'(a)') 'ATTRIBUTE STATEMENTS VOLATILE DESIGNATOR CONTROL OK'
end program
"""
    specs.append(valid("R865", "volatile_designator_control", ["name-not-designator"], vol_design_control,
        "The conforming control names the whole array object a; R865 has no array-element designator alternative.",
        ["a(1)+a(2) is 11"], [dict(id="change-array-value", replacements=[["a = [5, 6]", "a = [5, 7]"]], conforming=True)]))
    vol_design_bad = replace_once(vol_design_control, "  volatile :: a", "  volatile :: a(1)")
    specs.append(invalid("R865", "volatile_designator", ["name-not-designator"], vol_design_bad,
        "R865 takes object names, not array element designators; deleting only (1) gives the control.",
        locate_line(vol_design_bad, "volatile :: a(1)"), ["VOLATILE", "volatile", "syntax", "Syntax"], specs[-1]["id"],
        "delete only the array-element suffix"))

    selected_by_rule = {
        rule: set(facets)
        for section in SELECTED.values()
        for rule, facets in section.items()
    }
    by_id = {}
    for spec in specs:
        selected_facets = [facet for facet in spec["facets"] if facet in selected_by_rule.get(spec["rule"], set())]
        if not selected_facets:
            continue
        spec["facets"] = selected_facets
        if spec["id"] in by_id:
            raise ValueError("duplicate fixture id " + spec["id"])
        by_id[spec["id"]] = spec
    missing_controls = [
        spec["control_id"] for spec in by_id.values()
        if spec["kind"] == "invalid" and spec["control_id"] not in by_id
    ]
    if missing_controls:
        raise ValueError("selected invalid fixture lost controls: " + ", ".join(missing_controls))
    return by_id

def mutated_source(spec, mutation):
    text = spec["source"]
    for old, new in mutation["replacements"]:
        if text.count(old) != 1:
            raise ValueError(f"mutation token {old!r} count {text.count(old)} in {spec['id']}")
        text = text.replace(old, new, 1)
    return text.encode("ascii")

def build_corpus(root=ROOT):
    specs = build_specs()
    files = {}
    for spec in specs.values():
        case_dir = Path(root) / "tests/fixtures" / spec["id"]
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                      stdout=spec["completion"], stderr="")
        else:
            manifest["expect"] = dict(phase="compile", step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
            control = specs[spec["control_id"]]
            spec["repair"] = dict(control_id=control["id"], control_sha256=control["source_sha256"], note=spec["repair_note"])
        spec["path"] = (case_dir.relative_to(root) / "fixture.json").as_posix()
        spec["manifest"] = manifest
        files[case_dir / "source.f90"] = spec["source"].encode("ascii")
        files[case_dir / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs

def rule_to_section(rule):
    if rule in {"R856", "R857", "C892"}:
        return "8.6.12"
    if rule == "R858":
        return "8.6.13"
    if rule in {"R859", "R860", "C893"}:
        return "8.6.14"
    if rule in {"R862", "R863"}:
        return "8.6.15"
    if rule == "R864":
        return "8.6.16"
    if rule == "R865":
        return "8.6.17"
    raise KeyError(rule)

def remove_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    kept = [paragraph for paragraph in paragraphs if not paragraph.startswith(prefix)]
    return "\n\n".join(kept)

def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    selected_rules = set(SELECTED[section])
    for rule in ALL_RULES:
        if rule_to_section(rule) != section or rule in selected_rules or rule not in by_rule:
            continue
        row = by_rule[rule]
        row["oracle"] = remove_owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX[rule])
        row["oracle_limitation"] = remove_owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIX[rule])
    for rule, facets in SELECTED[section].items():
        row = by_rule[rule]
        if not set(facets) <= set(row["facets"]):
            raise ValueError(f"selected facets changed for {rule}")
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMITS[rule])
    return updated

def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated region changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = SUMMARY_BEGIN[section] + "\n" + SUMMARY[section] + "\n" + SUMMARY_END[section]
    if SUMMARY_BEGIN[section] in before or SUMMARY_END[section] in before:
        if before.count(SUMMARY_BEGIN[section]) != 1 or before.count(SUMMARY_END[section]) != 1:
            raise ValueError(f"summary region changed for {section}")
        lead, owned = before.split(SUMMARY_BEGIN[section])
        _, trail = owned.split(SUMMARY_END[section])
        before = lead + summary + trail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    rendered = "\n".join(render_requirement(row) for row in catalogue["requirements"])
    return before + begin + "\n\n" + rendered + "\n" + end + after

def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues = {section: json.loads((root / path).read_text()) for section, path in CATALOGUES.items()}
    synced = {section: synced_catalogue(section, cat) for section, cat in catalogues.items()}
    views = {section: render_view(section, synced[section], root) for section in CATALOGUES}
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, path in CATALOGUES.items():
            if catalogues[section] != synced[section]:
                stale.append(path)
            if (root / VIEWS[section]).read_text() != views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale attribute statement fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section, path in CATALOGUES.items():
                (root / path).write_text(json.dumps(synced[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs

def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(str(compiler)).name.lower() else "gfortran"

def std_flag(compiler, std):
    return f"--std={std}" if compiler_family(compiler) == "lfortran" else f"-std={std}"

def run_source(compiler, std, case_dir, source, exe):
    compiled = subprocess.run([str(compiler), std_flag(compiler, std), str(source.resolve()), "-o", str(exe.resolve())],
                              cwd=case_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=40)
    if compiled.returncode != 0:
        return "compile-fail", compiled.stdout
    run = subprocess.run([str(exe.resolve())], cwd=case_dir, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=40)
    if run.returncode == 0:
        return "pass", run.stdout
    return "run-fail", run.stdout

def check_mutations(root, compiler, std, inject_survivor=False):
    _, specs = build_corpus(root)
    mutations = [(spec, mut) for spec in specs.values() if spec["kind"] == "valid" for mut in spec["mutations"]]
    family = compiler_family(compiler)
    if not mutations:
        raise SystemExit("no mutations defined")
    workspace = Path(root) / WORKDIR
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    failures, skipped = [], []
    checked = 0
    try:
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
            case_dir.mkdir()
            parent_source = case_dir / "parent.f90"
            parent_exe = case_dir / "parent"
            parent_source.write_text(spec["source"])
            parent_status, parent_output = run_source(compiler, std, case_dir, parent_source, parent_exe)
            if parent_status != "pass":
                if spec["id"] in KNOWN_PARENT_FAILURES.get(family, set()):
                    skipped.append(f"{spec['id']}:{mutation['id']}:{parent_status}")
                    continue
                failures.append(f"{spec['id']} parent failed ({parent_status}):\n{parent_output}")
                continue
            mutant_source = case_dir / "source.f90"
            mutant_exe = case_dir / "program"
            if inject_survivor and checked == 0:
                mutant_source.write_text(spec["source"])
                mutation_id = mutation["id"] + "_injected_survivor"
            else:
                mutant_source.write_bytes(mutated_source(spec, mutation))
                mutation_id = mutation["id"]
            status, output = run_source(compiler, std, case_dir, mutant_source, mutant_exe)
            checked += 1
            if status == "compile-fail":
                failures.append(f"{spec['id']}:{mutation_id} did not compile:\n{output}")
            elif status == "pass" and output == spec["completion"]:
                failures.append(f"{spec['id']}:{mutation_id} survived")
    finally:
        if workspace.exists():
            shutil.rmtree(workspace)
    if failures:
        raise SystemExit("\n\n".join(failures))
    note = f"; skipped {len(skipped)} known failing parents" if skipped else ""
    if skipped:
        print("Known failing parents skipped: " + ", ".join(skipped))
    print(f"Mutation check: {checked}/{checked} mutants failed for {compiler} ({std}){note}.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--check-mutations", action="store_true")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.check_mutations))) > 1:
        parser.error("--check, --sync-catalogue and --check-mutations are separate operations")
    if args.inject_surviving_mutant and not args.check_mutations:
        parser.error("--inject-surviving-mutant requires --check-mutations")
    if args.check_mutations:
        if not args.compiler or not args.std:
            parser.error("--check-mutations requires --compiler and --std")
        check_mutations(args.root, args.compiler, args.std, args.inject_surviving_mutant)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    selected = sum(len(facets) for rules in SELECTED.values() for facets in rules.values())
    mutations = sum(len(row["mutations"]) for row in specs.values() if row["kind"] == "valid")
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} attribute statement cases, {selected} facets and {mutations} mutations.")

if __name__ == "__main__":
    main()
