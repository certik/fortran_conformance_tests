#!/usr/bin/env python3
"""Finite PROTECTED attribute fixtures for Fortran 2023 8.5.15."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.15"
CATALOGUE = "doc/catalogues/protected_attribute_8_5_15.json"
VIEW = "doc/fortran_2023_8_5_15.md"
PREFIX = "protected_attribute_"
SUMMARY_BEGIN = "<!-- BEGIN PROTECTED ATTRIBUTE FIXTURES -->"
SUMMARY_END = "<!-- END PROTECTED ATTRIBUTE FIXTURES -->"

EXCLUSIONS = (
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "assert", "asr", "verifier", "out of memory", "traceback",
    "segmentation", "bus error", "abort", "cannot open module", "cannot read module",
)

SELECTED = {
    "C856": ["main-scope-excluded", "procedure-scope-excluded", "block-scope-excluded"],
    "C857": ["nonpointer-variable", "data-pointer-variable", "procedure-pointer", "named-constant-excluded"],
    "C858": ["ordinary-module-control"],
    "C859": ["assignment", "do-variable", "nonpointer-out-inout-actual", "data-target", "readonly-control"],
    "C860": ["nullify-data-pointer", "data-pointer-assignment", "association-query-and-call-control"],
    "S8.5.15-001": ["module-host-setter-control"],
    "S8.5.15-002": ["unprotected-target-definition-control", "procedure-call-control"],
}

KNOWN_PARENT_FAILURES = {
    "lfortran": {"S8_5_15_002_valid__protected_attribute_target_definition_control"},
}

ORACLE_PREFIXES = {
    "C856": "C856 module-specification diagnostic fixtures: ",
    "C857": "C857 admitted/excluded entity fixtures: ",
    "C858": "C858 ordinary module control fixture: ",
    "C859": "C859 use-associated nonpointer context fixtures: ",
    "C860": "C860 protected pointer context fixtures: ",
    "S8.5.15-001": "S8.5.15-001 owner-module definition control fixture: ",
    "S8.5.15-002": "S8.5.15-002 protected pointer target/call controls: ",
}
LIMIT_PREFIXES = {
    "C856": "C856 module-specification diagnostic boundaries: ",
    "C857": "C857 admitted/excluded entity boundaries: ",
    "C858": "C858 ordinary module control boundaries: ",
    "C859": "C859 use-associated nonpointer context boundaries: ",
    "C860": "C860 protected pointer context boundaries: ",
    "S8.5.15-001": "S8.5.15-001 owner-module definition boundaries: ",
    "S8.5.15-002": "S8.5.15-002 protected pointer target/call boundaries: ",
}
ORACLES = {
    "C856": ORACLE_PREFIXES["C856"] + (
        "three compile/diagnose negatives put the PROTECTED attribute on an otherwise ordinary "
        "INTEGER entity in a main program specification part, an external subroutine "
        "specification part, and a BLOCK specification part. Each paired control deletes only "
        "the PROTECTED attr-spec and runs the complete source. The diagnostic is anchored on "
        "the declaration line and must report PROTECTED placement rather than an unsupported "
        "facility, crash, missing provider, or unrelated syntax error."
    ),
    "C857": ORACLE_PREFIXES["C857"] + (
        "one run/positive-control module declares an INTEGER nonpointer variable, a data pointer "
        "variable initially NULL, and a procedure pointer, all with PROTECTED in the module "
        "specification part. Owner procedures associate the pointers and the client observes the "
        "defined scalar value, the data-pointer association, and a procedure-pointer call result. "
        "A separate numbered negative gives PROTECTED to an INTEGER PARAMETER named constant; "
        "deleting only PARAMETER yields the paired variable control."
    ),
    "C858": ORACLE_PREFIXES["C858"] + (
        "one run/positive-control module keeps a protected INTEGER out of COMMON, sets it through "
        "an owner procedure, and lets the client read the value. This covers only the ordinary "
        "module-side control for the common-block exclusion."
    ),
    "C859": ORACLE_PREFIXES["C859"] + (
        "four compile/diagnose negatives use a complete provider/client pair where the subject is "
        "a nonpointer object with PROTECTED accessed by USE association. The selected forbidden "
        "contexts are intrinsic assignment, ordinary DO variable, actual argument corresponding "
        "to an explicit-interface INTENT(OUT) nonpointer dummy, and data-target in pointer "
        "assignment. Each repair deletes only PROTECTED at the provider and runs. A separate "
        "readonly control USEs and renames protected integers, reads them, and passes one to an "
        "INTENT(IN) dummy without any definition context."
    ),
    "C860": ORACLE_PREFIXES["C860"] + (
        "two compile/diagnose negatives use a USE-associated protected data pointer in pointer "
        "association contexts: NULLIFY and data-pointer assignment to a live local TARGET. Each "
        "repair deletes only PROTECTED and runs. The positive control queries a protected data "
        "pointer with ASSOCIATED and calls a protected procedure pointer after owner-side "
        "association, leaving both associations unchanged outside the module."
    ),
    "S8.5.15-001": ORACLE_PREFIXES["S8.5.15-001"] + (
        "one run/effect fixture gives a PUBLIC module INTEGER the PROTECTED attribute, mutates it "
        "only inside the owner module by a setter, and has a client observe the nonzero values 17 "
        "and 29 after separate calls. No protected object is passed by the client as an OUT or "
        "INOUT actual."
    ),
    "S8.5.15-002": ORACLE_PREFIXES["S8.5.15-002"] + (
        "one run/effect fixture associates a protected data pointer with an unprotected live "
        "module TARGET inside the owner, then the client defines that target through the pointer "
        "and verifies the independent target value and unchanged association. A separate "
        "run/effect fixture associates a protected procedure pointer inside the owner and the "
        "client calls it while leaving association unchanged."
    ),
}
LIMITATIONS = {
    "C856": LIMIT_PREFIXES["C856"] + (
        "only main-program, external-subroutine and BLOCK local declarations are covered. Module "
        "specification forms that use a separate PROTECTED statement, interface-body scope, "
        "submodule scope, contained-procedure locals and respecification of imported entities "
        "remain pending. Reporting is required, but fatal rejection, exact text and rule-number "
        "spelling are not."
    ),
    "C857": LIMIT_PREFIXES["C857"] + (
        "the positive entity fixture covers default INTEGER variables, data pointers, and one "
        "non-elemental INTEGER function procedure pointer. It does not dereference a "
        "disassociated pointer. Only PARAMETER/named-constant exclusion is diagnosed here; "
        "ordinary-procedure exclusion remains pending."
    ),
    "C858": LIMIT_PREFIXES["C858"] + (
        "only the ordinary protected-module-variable control is selected. Named and blank COMMON "
        "diagnostics remain pending because they need their own one-property controls and current "
        "frozen LFortran accepts the invalid COMMON forms rather than diagnosing C858."
    ),
    "C859": LIMIT_PREFIXES["C859"] + (
        "only assignment, ordinary DO, OUT actual, data-target, and readonly USE controls are "
        "selected. READ, NAMELIST, internal-file WRITE, SIZE/IOMSG/INQUIRE/NEWUNIT, allocation "
        "outputs, coarray synchronization outputs, construct selectors, initial-data-targets, "
        "subobjects, empty contexts and the remaining 19.6.7 families remain pending."
    ),
    "C860": LIMIT_PREFIXES["C860"] + (
        "only NULLIFY, data-pointer assignment and read-only association query/procedure call "
        "controls are covered. Procedure-pointer NULLIFY/assignment, allocation/deallocation, "
        "OUT/INOUT pointer dummies and pointer subobjects remain pending."
    ),
    "S8.5.15-001": LIMIT_PREFIXES["S8.5.15-001"] + (
        "only direct owner-module mutation by a setter is covered. Descendant submodule mutation, "
        "foreign host routes and alias-to-protected-target restrictions remain pending. This is "
        "positive conforming evidence, not a manufactured diagnostic for the prose restriction."
    ),
    "S8.5.15-002": LIMIT_PREFIXES["S8.5.15-002"] + (
        "only a scalar INTEGER data pointer target definition and a live module procedure-pointer "
        "call are covered. Other-route deallocation, BLOCK/RETURN/END target-lifetime exceptions, "
        "descendant association controls and no-INTENT pointer-alias restrictions remain pending. "
        "Frozen LFortran rejects the conforming target-definition fixture by treating assignment "
        "through the pointer as assignment to the protected pointer object; the case is retained "
        "because the reference compiler runs it and p2 protects association, not target value."
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(rule, variant, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__{PREFIX}{variant}"


def locate_line(source, needle):
    matches = [i + 1 for i, line in enumerate(source.splitlines()) if needle in line]
    if len(matches) != 1:
        raise ValueError(f"line anchor is not unique for {needle!r}: {matches}")
    return matches[0]


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"replacement text is not unique: {old!r} appears {source.count(old)} times")
    return source.replace(old, new, 1)


def valid_case(rule, variant, facets, source, derivation, observations, mutations, *, evidence="effect"):
    return dict(
        id=identifier(rule, variant), rule=rule, variant=variant, kind="valid",
        evidence=evidence, facets=list(facets), source=source,
        source_sha256=sha(source.encode("ascii")),
        completion=f"PROTECTED ATTRIBUTE {variant.upper().replace('_', ' ')} OK\n",
        derivation=derivation, observations=list(observations), mutations=list(mutations),
    )


def invalid_case(rule, variant, facets, source, derivation, diagnostic_line, contains, control_id, repair_note):
    return dict(
        id=identifier(rule, variant, "invalid"), rule=rule, variant=variant, kind="invalid",
        evidence="effect", facets=list(facets), source=source,
        source_sha256=sha(source.encode("ascii")), derivation=derivation,
        diagnostic=dict(
            file="source.f90", line=diagnostic_line, end_line=diagnostic_line,
            contains_any=list(contains), excludes_any=list(EXCLUSIONS)),
        control_id=control_id, repair_note=repair_note, observations=[], mutations=[],
    )


def source_specs():
    specs = []
    entity = """module protected_attribute_entities
  implicit none
  integer, protected :: scalar = 5
  integer, pointer, protected :: data_ptr => null()
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer, protected :: proc => null()
contains
  integer function plus_one(v)
    integer, intent(in) :: v
    plus_one = v + 1
  end function
  subroutine bind_proc()
    proc => plus_one
  end subroutine
  subroutine bind_data(target)
    integer, target, intent(inout) :: target
    data_ptr => target
  end subroutine
end module
program main
  use protected_attribute_entities, only: scalar, data_ptr, proc, bind_proc, bind_data
  implicit none
  integer, target :: local
  local = 37
  if (scalar /= 5) error stop 1
  if (associated(data_ptr)) error stop 2
  call bind_data(local)
  if (.not. associated(data_ptr, local)) error stop 3
  call bind_proc()
  if (.not. associated(proc)) error stop 4
  if (proc(41) /= 42) error stop 5
  write(*,'(a)') 'PROTECTED ATTRIBUTE ENTITY ADMISSION OK'
end program
"""
    specs.append(valid_case(
        "C857", "entity_admission",
        ["nonpointer-variable", "data-pointer-variable", "procedure-pointer"], entity,
        "C857 admits variables and procedure pointers with PROTECTED in a module specification part.",
        ["scalar has value 5", "data_ptr is owner-associated to local", "proc(41) returns 42"],
        [
            dict(id="change-scalar-initializer", replacements=[["integer, protected :: scalar = 5",
                                                                "integer, protected :: scalar = 6"]],
                 conforming=True),
            dict(id="remove-data-pointer-association", replacements=[["    data_ptr => target",
                                                                       "    continue"]],
                 conforming=True),
            dict(id="change-procedure-result", replacements=[["    plus_one = v + 1",
                                                               "    plus_one = v + 2"]],
                 conforming=True),
        ], evidence="positive-control"))

    c857_control = """module protected_attribute_parameter_control_m
  implicit none
  integer, protected :: c = 5
end module
program main
  use protected_attribute_parameter_control_m, only: c
  implicit none
  if (c /= 5) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE PARAMETER CONTROL OK'
end program
"""
    specs.append(valid_case(
        "C857", "parameter_control", ["named-constant-excluded"], c857_control,
        "Deleting PARAMETER from the negative makes c an admitted protected variable under C857.",
        ["c is an ordinary protected variable with value 5"],
        [dict(id="change-variable-value", replacements=[["integer, protected :: c = 5",
                                                         "integer, protected :: c = 6"]],
              conforming=True)],
        evidence="positive-control"))
    c857_invalid = replace_once(c857_control, "integer, protected :: c = 5",
                                "integer, parameter, protected :: c = 5")
    specs.append(invalid_case(
        "C857", "parameter_constant", ["named-constant-excluded"], c857_invalid,
        "The only changed property is PARAMETER, making c a named constant rather than a variable.",
        locate_line(c857_invalid, "integer, parameter, protected :: c = 5"),
        ["parameter", "PARAMETER", "protected", "PROTECTED"], specs[-1]["id"],
        "delete only the PARAMETER attribute so c remains a protected module variable"))

    c858 = """module protected_attribute_common_control_m
  implicit none
  integer, protected :: x = -9
contains
  subroutine set_x(v)
    integer, intent(in) :: v
    x = v
  end subroutine
end module
program main
  use protected_attribute_common_control_m, only: x, set_x
  implicit none
  call set_x(33)
  if (x /= 33) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE ORDINARY MODULE CONTROL OK'
end program
"""
    specs.append(valid_case(
        "C858", "ordinary_module_control", ["ordinary-module-control"], c858,
        "C858 excludes COMMON membership; this control keeps the protected variable in ordinary module storage.",
        ["owner setter defines x as 33", "client reads x as 33"],
        [dict(id="remove-owner-definition", replacements=[["    x = v", "    continue"]], conforming=True),
         dict(id="change-owner-definition", replacements=[["    x = v", "    x = v + 1"]], conforming=True)],
        evidence="positive-control"))

    setter = """module protected_attribute_setter_m
  implicit none
  integer, protected :: x = -11
contains
  subroutine set_x(v)
    integer, intent(in) :: v
    x = v
  end subroutine
end module
program main
  use protected_attribute_setter_m, only: x, set_x
  implicit none
  call set_x(17)
  if (x /= 17) error stop 1
  call set_x(29)
  if (x /= 29) error stop 2
  write(*,'(a)') 'PROTECTED ATTRIBUTE MODULE SETTER CONTROL OK'
end program
"""
    specs.append(valid_case(
        "S8.5.15-001", "module_setter_control", ["module-host-setter-control"], setter,
        "8.5.15p2 excludes only uses outside the owner/descendant; this setter defines x within its owner module.",
        ["x changes from the nondefault initializer to 17 and then 29"],
        [dict(id="remove-owner-definition", replacements=[["    x = v", "    continue"]], conforming=True),
         dict(id="change-second-observed-value", replacements=[["    x = v", "    x = v + 1"]], conforming=True)],
        evidence="positive-control"))

    readonly = """module protected_attribute_readonly_m
  implicit none
  integer, protected :: x = 41
  integer, protected :: z = 13
end module
program main
  use protected_attribute_readonly_m, only: x, y => z
  implicit none
  integer :: observed
  observed = x + y
  if (observed /= 54) error stop 1
  call take_in(x)
  write(*,'(a)') 'PROTECTED ATTRIBUTE READONLY USE OK'
contains
  subroutine take_in(v)
    integer, intent(in) :: v
    if (v /= 41) error stop 2
  end subroutine
end program
"""
    specs.append(valid_case(
        "C859", "readonly_use", ["readonly-control"], readonly,
        "C859 prohibits definition/target contexts; ordinary reads, USE renaming and INTENT(IN) actuals remain valid.",
        ["x+y is 54", "INTENT(IN) dummy sees x as 41"],
        [dict(id="change-renamed-value", replacements=[["integer, protected :: z = 13",
                                                        "integer, protected :: z = 14"]],
              conforming=True),
              dict(id="change-read-value", replacements=[["integer, protected :: x = 41",
                                                          "integer, protected :: x = 42"]],
              conforming=True)],
        evidence="positive-control"))

    c860_query = """module protected_attribute_pointer_query_m
  implicit none
  integer, target :: store = 19
  integer, pointer, protected :: data_ptr => null()
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer, protected :: proc => null()
contains
  integer function times_two(v)
    integer, intent(in) :: v
    times_two = v * 2
  end function
  subroutine bind_all()
    data_ptr => store
    proc => times_two
  end subroutine
end module
program main
  use protected_attribute_pointer_query_m, only: data_ptr, proc, store, bind_all
  implicit none
  call bind_all()
  if (.not. associated(data_ptr, store)) error stop 1
  if (.not. associated(proc)) error stop 2
  if (proc(21) /= 42) error stop 3
  write(*,'(a)') 'PROTECTED ATTRIBUTE POINTER QUERY CONTROL OK'
end program
"""
    specs.append(valid_case(
        "C860", "pointer_query_control", ["association-query-and-call-control"], c860_query,
        "C860 excludes association-changing contexts, not ASSOCIATED inquiry or a call through an associated procedure pointer.",
        ["data_ptr is associated with store", "proc(21) returns 42"],
        [dict(id="remove-data-association", replacements=[["    data_ptr => store", "    continue"]],
              conforming=True),
         dict(id="remove-procedure-association", replacements=[["    proc => times_two", "    continue"]],
              conforming=True),
         dict(id="change-procedure-result", replacements=[["    times_two = v * 2", "    times_two = v * 3"]],
              conforming=True)],
        evidence="positive-control"))

    proc_call = """module protected_attribute_proc_call_m
  implicit none
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer, protected :: proc => null()
contains
  integer function add_three(v)
    integer, intent(in) :: v
    add_three = v + 3
  end function
  subroutine bind_proc()
    proc => add_three
  end subroutine
end module
program main
  use protected_attribute_proc_call_m, only: proc, bind_proc
  implicit none
  call bind_proc()
  if (.not. associated(proc)) error stop 1
  if (proc(39) /= 42) error stop 2
  write(*,'(a)') 'PROTECTED ATTRIBUTE PROCEDURE CALL CONTROL OK'
end program
"""
    specs.append(valid_case(
        "S8.5.15-002", "procedure_call_control", ["procedure-call-control"], proc_call,
        "8.5.15p2 preserves pointer association outside the owner; a client may call an already associated protected procedure pointer.",
        ["proc is associated by the owner", "proc(39) returns 42"],
        [dict(id="remove-procedure-association", replacements=[["    proc => add_three", "    continue"]],
              conforming=True),
         dict(id="change-procedure-result", replacements=[["    add_three = v + 3", "    add_three = v + 4"]],
              conforming=True)],
        evidence="positive-control"))

    target_def = """module protected_attribute_target_definition_m
  implicit none
  integer, target :: storage = -9
  integer, pointer, protected :: data_ptr => null()
contains
  subroutine bind_storage()
    data_ptr => storage
  end subroutine
end module
program main
  use protected_attribute_target_definition_m, only: data_ptr, storage, bind_storage
  implicit none
  call bind_storage()
  if (.not. associated(data_ptr, storage)) error stop 1
  data_ptr = 23
  if (storage /= 23) error stop 2
  if (.not. associated(data_ptr, storage)) error stop 3
  write(*,'(a)') 'PROTECTED ATTRIBUTE TARGET DEFINITION CONTROL OK'
end program
"""
    specs.append(valid_case(
        "S8.5.15-002", "target_definition_control", ["unprotected-target-definition-control"], target_def,
        "8.5.15p2 protects the pointer association status; the separately unprotected live target remains definable.",
        ["data_ptr is associated with storage", "assignment through data_ptr changes storage to 23"],
        [dict(id="remove-target-definition", replacements=[["  data_ptr = 23", "  continue"]],
              conforming=True),
         dict(id="change-target-definition", replacements=[["  data_ptr = 23", "  data_ptr = 24"]],
              conforming=True)],
        evidence="positive-control"))

    c856_cases = {
        "main": (["main-scope-excluded"], """program main
  implicit none
  integer, protected :: x
  write(*,'(a)') 'PROTECTED ATTRIBUTE C856 MAIN CONTROL OK'
end program
"""),
        "procedure": (["procedure-scope-excluded"], """subroutine local_owner()
  implicit none
  integer, protected :: x
end subroutine
program main
  implicit none
  call local_owner()
  write(*,'(a)') 'PROTECTED ATTRIBUTE C856 PROCEDURE CONTROL OK'
end program
"""),
        "block": (["block-scope-excluded"], """program main
  implicit none
  block
    integer, protected :: x
  end block
  write(*,'(a)') 'PROTECTED ATTRIBUTE C856 BLOCK CONTROL OK'
end program
"""),
    }
    for variant, (facets, invalid_source) in c856_cases.items():
        control_source = invalid_source.replace(", protected", "")
        control = valid_case(
            "C856", f"c856_{variant}_control", facets, control_source,
            "Deleting only PROTECTED leaves the same complete nonmodule scoping-unit declaration valid.",
            ["control source reaches normal completion"], [], evidence="positive-control")
        specs.append(control)
        specs.append(invalid_case(
            "C856", f"c856_{variant}", facets, invalid_source,
            "C856 allows PROTECTED only in a module specification part; this declaration is in a nonmodule specification part.",
            locate_line(invalid_source, "protected :: x"), ["protected", "PROTECTED"], control["id"],
            "delete only the PROTECTED attr-spec from the declaration"))

    c859_sources = {
        "assignment": (["assignment"], """module protected_attribute_c859_assignment_m
  implicit none
  integer, protected :: x = 11
end module
program main
  use protected_attribute_c859_assignment_m, only: x
  implicit none
  x = 12
  if (x /= 12) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 ASSIGNMENT CONTROL OK'
end program
""", "x = 12"),
        "do_variable": (["do-variable"], """module protected_attribute_c859_do_m
  implicit none
  integer, protected :: x = 11
end module
program main
  use protected_attribute_c859_do_m, only: x
  implicit none
  integer :: visits
  visits = -3
  visits = 0
  do x = 1, 2
    visits = visits + 1
  end do
  if (visits /= 2) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 DO VARIABLE CONTROL OK'
end program
""", "do x = 1, 2"),
        "out_actual": (["nonpointer-out-inout-actual"], """module protected_attribute_c859_out_m
  implicit none
  integer, protected :: x = 11
end module
program main
  use protected_attribute_c859_out_m, only: x
  implicit none
  call define(x)
  if (x /= 18) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 OUT ACTUAL CONTROL OK'
contains
  subroutine define(a)
    integer, intent(out) :: a
    a = 18
  end subroutine
end program
""", "call define(x)"),
        "data_target": (["data-target"], """module protected_attribute_c859_target_m
  implicit none
  integer, target, protected :: x = 11
end module
program main
  use protected_attribute_c859_target_m, only: x
  implicit none
  integer, pointer :: q
  q => x
  if (q /= 11) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C859 DATA TARGET CONTROL OK'
end program
""", "q => x"),
    }
    for variant, (facets, invalid_source, anchor) in c859_sources.items():
        control_source = invalid_source.replace(", protected", "")
        control = valid_case(
            "C859", f"c859_{variant}_control", facets, control_source,
            "Deleting only PROTECTED at the provider makes the selected client context valid.",
            ["control source reaches the selected definition/target context and completes"], [],
            evidence="positive-control")
        specs.append(control)
        specs.append(invalid_case(
            "C859", f"c859_{variant}", facets, invalid_source,
            "The USE-associated nonpointer protected object appears in the selected C859-prohibited context.",
            locate_line(invalid_source, anchor), ["protected", "PROTECTED"], control["id"],
            "delete only PROTECTED at the provider, preserving type, USE association and context"))

    c860_sources = {
        "nullify_data_pointer": (["nullify-data-pointer"], """module protected_attribute_c860_nullify_m
  implicit none
  integer, pointer, protected :: p => null()
end module
program main
  use protected_attribute_c860_nullify_m, only: p
  implicit none
  nullify(p)
  if (associated(p)) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C860 NULLIFY DATA POINTER CONTROL OK'
end program
""", "nullify(p)"),
        "data_pointer_assignment": (["data-pointer-assignment"], """module protected_attribute_c860_assign_m
  implicit none
  integer, pointer, protected :: p => null()
end module
program main
  use protected_attribute_c860_assign_m, only: p
  implicit none
  integer, target :: local
  local = 2
  p => local
  if (.not. associated(p, local)) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C860 DATA POINTER ASSIGNMENT CONTROL OK'
end program
""", "p => local"),
    }
    for variant, (facets, invalid_source, anchor) in c860_sources.items():
        control_source = invalid_source.replace(", protected", "")
        control = valid_case(
            "C860", f"c860_{variant}_control", facets, control_source,
            "Deleting only PROTECTED at the provider makes the selected pointer association context valid.",
            ["control source reaches the selected association-changing context and completes"], [],
            evidence="positive-control")
        specs.append(control)
        specs.append(invalid_case(
            "C860", f"c860_{variant}", facets, invalid_source,
            "The USE-associated protected pointer appears in the selected C860 pointer-association context.",
            locate_line(invalid_source, anchor), ["protected", "PROTECTED"], control["id"],
            "delete only PROTECTED at the provider, preserving pointer nature and association context"))

    return specs


def build_specs():
    specs = source_specs()
    ids = [spec["id"] for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate protected attribute fixture id")
    return {spec["id"]: spec for spec in specs}


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent source no longer matches its fingerprint")
    text = spec["source"]
    for expected, replacement in mutation["replacements"]:
        if text.count(expected) != 1:
            raise ValueError(f"mutation token count changed for {expected!r}: {text.count(expected)}")
        text = text.replace(expected, replacement, 1)
    return text.encode("ascii")


def build_corpus(root=ROOT):
    files, specs = {}, build_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / spec["id"]
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        )
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(
                phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr="")
        else:
            manifest["expect"] = dict(
                phase="compile", step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
            control = specs[spec["control_id"]]
            spec["repair"] = dict(
                control_id=control["id"], control_sha256=control["source_sha256"],
                note=spec["repair_note"])
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected PROTECTED facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## PROTECTED attribute fixture packet\n\n"
        "Twenty-seven fixtures cover nineteen selected facets of 8.5.15. C856 diagnostics "
        "anchor PROTECTED declarations in nonmodule specification parts. C857 admits protected "
        "variables and procedure pointers while excluding a named constant, and C858 contributes "
        "the ordinary protected-module-variable control. C859 diagnostics cover assignment, DO "
        "control variable, nonpointer INTENT(OUT) actual, and data-target contexts, with a "
        "readonly USE/rename/INTENT(IN) control. C860 covers NULLIFY, data-pointer assignment, "
        "and read-only association query/procedure call controls.\n\n"
        "Runtime effects use nondefault integer sentinels and permanent feature mutations. Owner "
        "setters define protected nonpointers inside the module; protected pointers are associated "
        "inside the owner and then queried, called, or used to define an unprotected target outside "
        "without changing association. Frozen LFortran currently rejects the conforming target "
        "definition through a protected pointer and accepts several required diagnostics; those "
        "reference-backed cases are retained for XFAIL review rather than weakened.\n\n"
        "Separate PROTECTED statement admission, interface/submodule C856 scopes, C858 COMMON "
        "negatives, remaining C859 19.6.7 families, initial-data-targets, subobject propagation, "
        "procedure-pointer C860 negatives, allocation/deallocation contexts, pointer OUT/INOUT "
        "actuals, descendant submodule controls, alias routes and lifetime-ending exceptions remain "
        "pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("PROTECTED summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    rendered = "\n".join(render_requirement(row) for row in catalogue["requirements"])
    return before + begin + "\n\n" + rendered + "\n" + end + after


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
            raise ValueError("stale PROTECTED attribute fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(str(compiler)).name.lower() else "gfortran"


def std_flag(compiler, std):
    return f"--std={std}" if compiler_family(compiler) == "lfortran" else f"-std={std}"


def run_source(compiler, std, case_dir, source, exe):
    compiled = subprocess.run(
        [str(compiler), std_flag(compiler, std), str(source.resolve()), "-o", str(exe.resolve())],
        cwd=case_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if compiled.returncode != 0:
        return "compile-fail", compiled.stdout
    run = subprocess.run([str(exe.resolve())], cwd=case_dir, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if run.returncode == 0:
        return "pass", run.stdout
    return "run-fail", run.stdout


def check_mutations(root, compiler, std, *, inject_survivor=False):
    _, specs = build_corpus(root)
    mutations = [(spec, mutation) for spec in specs.values() if spec["kind"] == "valid"
                 for mutation in spec["mutations"]]
    if not mutations:
        raise SystemExit("no PROTECTED attribute mutations defined")
    family = compiler_family(compiler)
    failures = []
    checked = 0
    known_parent_failures = []
    with tempfile.TemporaryDirectory(prefix="protected_attribute_mutations_") as tmp:
        workspace = Path(tmp).resolve()
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
            case_dir.mkdir()
            parent_source = case_dir / "parent.f90"
            parent_exe = case_dir / "parent"
            parent_source.write_text(spec["source"])
            parent_status, parent_output = run_source(compiler, std, case_dir, parent_source, parent_exe)
            known_parent_failure = (
                parent_status != "pass" and spec["id"] in KNOWN_PARENT_FAILURES.get(family, set()))
            if parent_status != "pass" and not known_parent_failure:
                failures.append(f"{spec['id']} parent did not pass before mutation ({parent_status}):\n{parent_output}")
                continue
            if known_parent_failure:
                known_parent_failures.append(f"{spec['id']}:{mutation['id']}")
            mutant_source = case_dir / "source.f90"
            mutant_exe = case_dir / "program"
            if inject_survivor and index == 1:
                mutant_source.write_text(spec["source"])
                mutation_id = mutation["id"] + "_injected_survivor"
            else:
                mutant_source.write_bytes(mutated_source(spec, mutation))
                mutation_id = mutation["id"]
            status, output = run_source(compiler, std, case_dir, mutant_source, mutant_exe)
            checked += 1
            if status == "compile-fail":
                if not known_parent_failure:
                    failures.append(f"{spec['id']}:{mutation_id} did not compile:\n{output}")
                continue
            if status == "pass" and output == spec["completion"]:
                failures.append(f"{spec['id']}:{mutation_id} survived")
    if failures:
        raise SystemExit("\n\n".join(failures))
    note = f"; {len(known_parent_failures)} mutants had a known failing parent" if known_parent_failures else ""
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
        check_mutations(args.root, args.compiler, args.std, inject_survivor=args.inject_surviving_mutant)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    selected = sum(len(v) for v in SELECTED.values())
    mutations = sum(len(row["mutations"]) for row in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} PROTECTED attribute cases, "
          f"{selected} facets and {mutations} mutations.")


if __name__ == "__main__":
    main()
