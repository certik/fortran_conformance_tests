#!/usr/bin/env python3
"""POINTER/SAVE attribute fixtures for 8.5.14 and 8.5.16."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
POINTER_SECTION = "8.5.14"
SAVE_SECTION = "8.5.16"
CATALOGUES = {
    POINTER_SECTION: "doc/catalogues/pointer_attribute_8_5_14.json",
    SAVE_SECTION: "doc/catalogues/save_attribute_8_5_16.json",
}
VIEWS = {
    POINTER_SECTION: "doc/fortran_2023_8_5_14.md",
    SAVE_SECTION: "doc/fortran_2023_8_5_16.md",
}
SUMMARY_BEGIN = "<!-- BEGIN POINTER SAVE 8.5.14 8.5.16 FIXTURES -->"
SUMMARY_END = "<!-- END POINTER SAVE 8.5.14 8.5.16 FIXTURES -->"
EXCLUDES = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal error", "asr", "verifier", "ice", "out of memory", "segmentation fault",
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def owned_paragraph(text, prefix, replacement):
    parts = text.split("\n\n") if text else []
    matches = [i for i, part in enumerate(parts) if part.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph for " + prefix)
    if matches:
        parts[matches[0]] = replacement
    else:
        parts.append(replacement)
    return "\n\n".join(part for part in parts if part)


SOURCES = {
"pointer_data_basic": """program pointer_data_basic
  implicit none
  integer, target :: t, v, u
  integer, pointer :: p
  integer :: checks
  checks = 0
  t = 17
  v = 41
  p => t
  if (.not. associated(p, t)) error stop
  checks = checks + 1
  if (p /= 17) error stop
  checks = checks + 1
  p = 19
  if (t /= 19) error stop
  checks = checks + 1
  p => u
  if (.not. associated(p, u)) error stop
  checks = checks + 1
  p = 23
  if (u /= 23) error stop
  checks = checks + 1
  if (checks /= 5) error stop
  print '(a)', 'POINTER DATA BASIC OK'
end program pointer_data_basic
""",
"pointer_character_parameter": """program pointer_character_parameter
  implicit none
  character(:), pointer :: p
  character(len=2), target :: short, raw
  character(len=5), target :: long
  integer :: checks
  checks = 0
  short = 'ab'
  long = 'pqrst'
  p => short
  if (len(p) /= 2) error stop
  checks = checks + 1
  if (p /= 'ab') error stop
  checks = checks + 1
  p => long
  if (len(p) /= 5) error stop
  checks = checks + 1
  if (p /= 'pqrst') error stop
  checks = checks + 1
  p => raw
  if (len(p) /= 2) error stop
  checks = checks + 1
  p = 'xy'
  if (raw /= 'xy') error stop
  checks = checks + 1
  if (checks /= 6) error stop
  print '(a)', 'POINTER CHARACTER PARAMETER OK'
end program pointer_character_parameter
""",
"procedure_pointer_call": """program procedure_pointer_call
  implicit none
  abstract interface
    integer function unary(x)
      integer, intent(in) :: x
    end function unary
  end interface
  procedure(unary), pointer :: fp
  integer :: checks
  checks = 0
  nullify(fp)
  if (associated(fp)) error stop
  checks = checks + 1
  fp => add_eleven
  if (.not. associated(fp)) error stop
  checks = checks + 1
  if (fp(4) /= 15) error stop
  checks = checks + 1
  if (checks /= 3) error stop
  print '(a)', 'PROCEDURE POINTER CALL OK'
contains
  integer function add_eleven(x)
    integer, intent(in) :: x
    add_eleven = x + 11
  end function add_eleven
  integer function add_twelve(x)
    integer, intent(in) :: x
    add_twelve = x + 12
  end function add_twelve
end program procedure_pointer_call
""",
"save_local_states": """module save_state_targets
  implicit none
  integer, target :: live = 11
end module save_state_targets
program save_local_states
  use save_state_targets
  implicit none
  integer :: checks
  checks = 0
  call visit(1, checks)
  live = 17
  call visit(2, checks)
  call visit(3, checks)
  if (checks /= 16) error stop
  print '(a)', 'SAVE LOCAL STATES OK'
contains
  subroutine visit(phase, checks)
    use save_state_targets
    implicit none
    integer, intent(in) :: phase
    integer, intent(inout) :: checks
    integer, pointer, save :: p
    integer, pointer, save :: q
    integer, allocatable, save :: a(:), empty(:), never(:)
    if (phase == 1) then
      p => live
      nullify(q)
      allocate(a(2))
      a = [11, 13]
      if (allocated(never)) error stop
      checks = checks + 1
      allocate(empty(0))
      return
    else if (phase == 2) then
      if (.not. associated(p, live)) error stop
      checks = checks + 1
      if (p /= 17) error stop
      checks = checks + 1
      if (associated(q)) error stop
      checks = checks + 1
      if (.not. allocated(a)) error stop
      checks = checks + 1
      if (size(a) /= 2) error stop
      checks = checks + 1
      if (a(1) /= 11 .or. a(2) /= 13) error stop
      checks = checks + 1
      a = [17, 19]
      if (allocated(never)) error stop
      checks = checks + 1
      if (.not. allocated(empty)) error stop
      checks = checks + 1
      if (size(empty) /= 0) error stop
      checks = checks + 1
      return
    else
      if (a(1) /= 17 .or. a(2) /= 19) error stop
      checks = checks + 1
      allocate(never(1))
      never = 29
      if (.not. allocated(never)) error stop
      checks = checks + 1
      if (never(1) /= 29) error stop
      checks = checks + 1
      if (.not. allocated(empty)) error stop
      checks = checks + 1
      if (size(empty) /= 0) error stop
      checks = checks + 1
      if (associated(q)) error stop
      checks = checks + 1
    end if
  end subroutine visit
end program save_local_states
""",
"block_save_states": """program block_save_states
  implicit none
  integer, target :: live
  integer :: iter, checks
  live = 31
  checks = 0
  do iter = 1, 3
    block
      integer, save :: kept
      integer, pointer, save :: p
      integer, pointer, save :: q
      integer, allocatable, save :: a(:), empty(:), never(:)
      if (iter == 1) then
        kept = 11
        p => live
        nullify(q)
        allocate(a(2))
        a = [21, 23]
        if (allocated(never)) error stop
        checks = checks + 1
        allocate(empty(0))
      else if (iter == 2) then
        if (kept /= 11) error stop
        checks = checks + 1
        kept = 17
        live = 37
        if (.not. associated(p, live)) error stop
        checks = checks + 1
        if (p /= 37) error stop
        checks = checks + 1
        if (associated(q)) error stop
        checks = checks + 1
        if (.not. allocated(a)) error stop
        checks = checks + 1
        if (size(a) /= 2) error stop
        checks = checks + 1
        if (a(1) /= 21 .or. a(2) /= 23) error stop
        checks = checks + 1
        a = [27, 29]
        if (allocated(never)) error stop
        checks = checks + 1
        if (.not. allocated(empty)) error stop
        checks = checks + 1
        if (size(empty) /= 0) error stop
        checks = checks + 1
      else
        if (kept /= 17) error stop
        checks = checks + 1
        if (a(1) /= 27 .or. a(2) /= 29) error stop
        checks = checks + 1
        allocate(never(1))
        never = 41
        if (never(1) /= 41) error stop
        checks = checks + 1
        if (.not. allocated(empty)) error stop
        checks = checks + 1
        if (size(empty) /= 0) error stop
        checks = checks + 1
        if (associated(q)) error stop
        checks = checks + 1
      end if
    end block
  end do
  if (checks /= 17) error stop
  print '(a)', 'SAVE BLOCK STATES OK'
end program block_save_states
""",
"pointer_allocatable_conflict": """program pointer_allocatable_conflict
  implicit none
  integer, pointer, allocatable :: p
end program pointer_allocatable_conflict
""",
"pointer_allocatable_control": """program pointer_allocatable_control
  implicit none
  integer, pointer :: p
  nullify(p)
  if (associated(p)) error stop
  print '(a)', 'POINTER ALLOCATABLE CONTROL OK'
end program pointer_allocatable_control
""",
"pointer_target_conflict": """program pointer_target_conflict
  implicit none
  integer, pointer, target :: p
end program pointer_target_conflict
""",
"pointer_target_control": """program pointer_target_control
  implicit none
  integer, pointer :: p
  nullify(p)
  if (associated(p)) error stop
  print '(a)', 'POINTER TARGET CONTROL OK'
end program pointer_target_control
""",
"save_parameter_conflict": """program save_parameter_conflict
  implicit none
  integer, parameter :: k = 3
  save :: k
end program save_parameter_conflict
""",
"save_parameter_control": """program save_parameter_control
  implicit none
  integer :: k = 3
  save :: k
  if (k /= 3) error stop
  print '(a)', 'SAVE PARAMETER CONTROL OK'
end program save_parameter_control
""",
"save_dummy_conflict": """module save_dummy_conflict_mod
contains
  subroutine takes_saved_dummy(x)
    implicit none
    integer, intent(in) :: x
    save :: x
  end subroutine takes_saved_dummy
end module save_dummy_conflict_mod
""",
"save_dummy_control": """module save_dummy_control_mod
contains
  subroutine takes_unsaved_dummy(x)
    implicit none
    integer, intent(in) :: x
    if (x /= 5) error stop
  end subroutine takes_unsaved_dummy
end module save_dummy_control_mod
program save_dummy_control
  use save_dummy_control_mod
  implicit none
  call takes_unsaved_dummy(5)
  print '(a)', 'SAVE DUMMY CONTROL OK'
end program save_dummy_control
""",
"save_result_conflict": """module save_result_conflict_mod
contains
  function saved_result() result(answer)
    implicit none
    integer :: answer
    save :: answer
    answer = 7
  end function saved_result
end module save_result_conflict_mod
""",
"save_result_control": """module save_result_control_mod
contains
  function unsaved_result() result(answer)
    implicit none
    integer :: answer
    answer = 7
  end function unsaved_result
end module save_result_control_mod
program save_result_control
  use save_result_control_mod
  implicit none
  if (unsaved_result() /= 7) error stop
  print '(a)', 'SAVE RESULT CONTROL OK'
end program save_result_control
""",
"save_common_member_conflict": """program save_common_member_conflict
  implicit none
  integer :: x
  common /shared/ x
  save :: x
end program save_common_member_conflict
""",
"save_common_member_control": """program save_common_member_control
  implicit none
  integer :: x
  common /shared/ x
  save /shared/
  x = 13
  if (x /= 13) error stop
  print '(a)', 'SAVE COMMON MEMBER CONTROL OK'
end program save_common_member_control
""",
}

CASES = [
    dict(key="pointer_data_basic", fixture="pointer_save_data_basic", id="S8_5_14_001_valid__pointer_save_data_basic", section=POINTER_SECTION,
         rule="S8.5.14-001", facets=["defined-target-reference", "undefined-target-definition-control"], evidence="positive-control",
         stdout="POINTER DATA BASIC OK\n", mutations=[
             dict(id="defined-target-reference-associate-alt", facet="defined-target-reference", old="p => t\n  if (.not. associated(p, t))", new="p => v\n  if (.not. associated(p, t))"),
             dict(id="definition-control-associate-alt", facet="undefined-target-definition-control", old="p => u\n  if (.not. associated(p, u))", new="p => v\n  if (.not. associated(p, u))"),
         ]),
    dict(key="pointer_character_parameter", fixture="pointer_save_character_parameter", id="S8_5_14_002_valid__pointer_save_character_parameter", section=POINTER_SECTION,
         rule="S8.5.14-002", facets=["character-parameter-reuse", "associated-undefined-payload-boundary"], evidence="effect",
         stdout="POINTER CHARACTER PARAMETER OK\n", mutations=[
             dict(id="character-parameter-short-to-long", facet="character-parameter-reuse", old="p => short\n  if (len(p) /= 2)", new="p => long\n  if (len(p) /= 2)"),
             dict(id="undefined-payload-raw-to-long", facet="associated-undefined-payload-boundary", old="p => raw\n  if (len(p) /= 2)", new="p => long\n  if (len(p) /= 2)"),
         ]),
    dict(key="procedure_pointer_call", fixture="pointer_save_procedure_pointer_call", id="S8_5_14_003_valid__pointer_save_procedure_pointer_call", section=POINTER_SECTION,
         rule="S8.5.14-003", facets=["associated-call-control", "status-and-argument-contexts"], evidence="positive-control",
         stdout="PROCEDURE POINTER CALL OK\n", mutations=[
             dict(id="status-start-associated", facet="status-and-argument-contexts", old="nullify(fp)\n  if (associated(fp))", new="fp => add_eleven\n  if (associated(fp))"),
             dict(id="associated-call-wrong-target", facet="associated-call-control", old="fp => add_eleven\n  if (.not. associated(fp))", new="fp => add_twelve\n  if (.not. associated(fp))"),
         ]),
    dict(key="save_local_states", fixture="pointer_save_local_states", id="S8_5_16_001_valid__pointer_save_local_states", section=SAVE_SECTION,
         rule="S8.5.16-001", facets=["live-data-pointer-association", "defined-disassociated-pointer", "allocated-object-retention", "unallocated-status-retention", "allocated-empty-status"], evidence="effect",
         stdout="SAVE LOCAL STATES OK\n", mutations=[
             dict(id="live-pointer-nullified", facet="live-data-pointer-association", old="p => live", new="nullify(p)"),
             dict(id="disassociated-pointer-associated", facet="defined-disassociated-pointer", old="nullify(q)", new="q => live"),
             dict(id="allocated-object-wrong-value", facet="allocated-object-retention", old="a = [11, 13]", new="a = [11, 14]"),
             dict(id="unallocated-status-preallocated", facet="unallocated-status-retention", old="a = [11, 13]\n      if (allocated(never)) error stop\n      checks = checks + 1", new="a = [11, 13]\n      allocate(never(1))\n      if (allocated(never)) error stop\n      checks = checks + 1"),
             dict(id="allocated-empty-nonempty", facet="allocated-empty-status", old="allocate(empty(0))", new="allocate(empty(1))"),
         ]),
    dict(key="block_save_states", fixture="pointer_save_block_states", id="S8_5_16_002_valid__pointer_save_block_states", section=SAVE_SECTION,
         rule="S8.5.16-002", facets=["same-block-defined-values", "block-live-pointer-association", "block-disassociated-pointer", "block-allocated-status", "block-unallocated-status", "block-allocated-empty"], evidence="effect",
         stdout="SAVE BLOCK STATES OK\n", mutations=[
             dict(id="block-kept-wrong-first-value", facet="same-block-defined-values", old="kept = 11", new="kept = 12"),
             dict(id="block-live-pointer-nullified", facet="block-live-pointer-association", old="p => live", new="nullify(p)"),
             dict(id="block-disassociated-pointer-associated", facet="block-disassociated-pointer", old="nullify(q)", new="q => live"),
             dict(id="block-allocated-object-wrong-value", facet="block-allocated-status", old="a = [21, 23]", new="a = [21, 24]"),
             dict(id="block-unallocated-preallocated", facet="block-unallocated-status", old="a = [21, 23]\n        if (allocated(never)) error stop\n        checks = checks + 1", new="a = [21, 23]\n        allocate(never(1))\n        if (allocated(never)) error stop\n        checks = checks + 1"),
             dict(id="block-empty-nonempty", facet="block-allocated-empty", old="allocate(empty(0))", new="allocate(empty(1))"),
         ]),
    dict(key="pointer_allocatable_conflict", fixture="pointer_save_pointer_allocatable_conflict_invalid", id="C854_invalid__pointer_save_pointer_allocatable_conflict", section=POINTER_SECTION,
         rule="C854", facets=["allocatable-conflict"], evidence="effect", invalid=True, line=3, control="pointer_allocatable_control"),
    dict(key="pointer_allocatable_control", fixture="pointer_save_pointer_allocatable_control", id="C854_valid__pointer_save_pointer_allocatable_control", section=POINTER_SECTION,
         rule="C854", facets=["allocatable-conflict"], evidence="positive-control", stdout="POINTER ALLOCATABLE CONTROL OK\n"),
    dict(key="pointer_target_conflict", fixture="pointer_save_pointer_target_conflict_invalid", id="C854_invalid__pointer_save_pointer_target_conflict", section=POINTER_SECTION,
         rule="C854", facets=["target-conflict-owner"], evidence="effect", invalid=True, line=3, control="pointer_target_control"),
    dict(key="pointer_target_control", fixture="pointer_save_pointer_target_control", id="C854_valid__pointer_save_pointer_target_control", section=POINTER_SECTION,
         rule="C854", facets=["target-conflict-owner"], evidence="positive-control", stdout="POINTER TARGET CONTROL OK\n"),
    dict(key="save_parameter_conflict", fixture="pointer_save_parameter_conflict_invalid", id="C861_invalid__pointer_save_parameter_conflict", section=SAVE_SECTION,
         rule="C861", facets=["named-constant-excluded"], evidence="effect", invalid=True, line=4, control="save_parameter_control"),
    dict(key="save_parameter_control", fixture="pointer_save_parameter_control", id="C861_valid__pointer_save_parameter_control", section=SAVE_SECTION,
         rule="C861", facets=["named-constant-excluded"], evidence="positive-control", stdout="SAVE PARAMETER CONTROL OK\n"),
    dict(key="save_dummy_conflict", fixture="pointer_save_dummy_conflict_invalid", id="C862_invalid__pointer_save_dummy_conflict", section=SAVE_SECTION,
         rule="C862", facets=["dummy-argument"], evidence="effect", invalid=True, line=6, control="save_dummy_control"),
    dict(key="save_dummy_control", fixture="pointer_save_dummy_control", id="C862_valid__pointer_save_dummy_control", section=SAVE_SECTION,
         rule="C862", facets=["dummy-argument"], evidence="positive-control", stdout="SAVE DUMMY CONTROL OK\n"),
    dict(key="save_result_conflict", fixture="pointer_save_result_conflict_invalid", id="C862_invalid__pointer_save_result_conflict", section=SAVE_SECTION,
         rule="C862", facets=["function-result"], evidence="effect", invalid=True, line=6, control="save_result_control"),
    dict(key="save_result_control", fixture="pointer_save_result_control", id="C862_valid__pointer_save_result_control", section=SAVE_SECTION,
         rule="C862", facets=["function-result"], evidence="positive-control", stdout="SAVE RESULT CONTROL OK\n"),
    dict(key="save_common_member_conflict", fixture="pointer_save_common_member_conflict_invalid", id="C862_invalid__pointer_save_common_member_conflict", section=SAVE_SECTION,
         rule="C862", facets=["common-member"], evidence="effect", invalid=True, line=5, control="save_common_member_control"),
    dict(key="save_common_member_control", fixture="pointer_save_common_member_control", id="C862_valid__pointer_save_common_member_control", section=SAVE_SECTION,
         rule="C862", facets=["common-member"], evidence="positive-control", stdout="SAVE COMMON MEMBER CONTROL OK\n"),
]

ORACLE_PREFIXES = {
    (POINTER_SECTION, "C854"): "C854 pointer-entity conflict diagnostics: ",
    (POINTER_SECTION, "S8.5.14-001"): "S8.5.14-001 data-pointer state fixtures: ",
    (POINTER_SECTION, "S8.5.14-002"): "S8.5.14-002 deferred-parameter fixtures: ",
    (POINTER_SECTION, "S8.5.14-003"): "S8.5.14-003 procedure-pointer invocation fixture: ",
    (SAVE_SECTION, "C861"): "C861 SAVE excluded-constant diagnostic fixture: ",
    (SAVE_SECTION, "C862"): "C862 explicit-SAVE exclusion diagnostics: ",
    (SAVE_SECTION, "S8.5.16-001"): "S8.5.16-001 saved local state fixtures: ",
    (SAVE_SECTION, "S8.5.16-002"): "S8.5.16-002 saved BLOCK state fixtures: ",
}
LIMIT_PREFIXES = {}
ORACLES = {
    (POINTER_SECTION, "C854"): "C854 pointer-entity conflict diagnostics: two compile/f2023 negatives place POINTER with ALLOCATABLE or TARGET on the same ordinary scalar entity on line3. Each has a one-property positive control deleting only the conflicting attribute and safely nullifying/inquiring the pointer before exact output.",
    (POINTER_SECTION, "S8.5.14-001"): "S8.5.14-001 data-pointer state fixtures: one complete run/effect program associates a data pointer with a defined integer target t=17, checks ASSOCIATED(p,t), reads literal17, defines through p and observes t=19. It then associates the same pointer with a separate live but previously undefined definable target u, checks ASSOCIATED(p,u), defines through p and observes u=23. Feature mutations redirect each pointer assignment to an alternate defined target before the guarded assertion.",
    (POINTER_SECTION, "S8.5.14-002"): "S8.5.14-002 deferred-parameter fixtures: one complete run/effect program associates a deferred-length CHARACTER data pointer with length2 and length5 targets and checks LEN directly on the pointer before literal payload checks. It separately associates the pointer with an initially undefined length2 target, observes only LEN=2, then defines the target through the pointer before reading raw='xy'. Feature mutations substitute the length5 target for each selected association.",
    (POINTER_SECTION, "S8.5.14-003"): "S8.5.14-003 procedure-pointer invocation fixture: one complete run/effect program declares PROCEDURE(unary),POINTER fp, establishes defined disassociation by NULLIFY and checks ASSOCIATED(fp)=false without invocation, then associates fp with add_eleven and checks ASSOCIATED(fp) and fp(4)=15. Feature mutations pre-associate the status control or redirect the call to add_twelve.",
    (SAVE_SECTION, "C861"): "C861 SAVE excluded-constant diagnostic fixture: one compile/f2023 negative specifies SAVE for PARAMETER k on line4. The one-property repair removes PARAMETER while retaining initialization and the SAVE statement, yielding an ordinary variable control that compiles and runs with k=3.",
    (SAVE_SECTION, "C862"): "C862 explicit-SAVE exclusion diagnostics: three compile/f2023 negatives specify SAVE for an ordinary scalar dummy argument, a distinct function RESULT name and an individual COMMON member at the marked lines. Each repair deletes only the explicit SAVE from the excluded entity or replaces the member operand by SAVE /shared/ and compiles/runs a complete positive control.",
    (SAVE_SECTION, "S8.5.16-001"): "S8.5.16-001 saved local state fixtures: one complete run/effect program calls the same internal subroutine three times. Explicitly saved local pointer p remains associated with a module target whose value changes to17, saved pointer q remains defined-disassociated, saved allocatable a retains allocation, size and values [11,13] then [17,19], saved allocatable never remains unallocated through the second entry before later allocation, and saved allocatable empty retains allocated size0. Guards precede every dependent inquiry; feature mutations alter the establishment of each retained state.",
    (SAVE_SECTION, "S8.5.16-002"): "S8.5.16-002 saved BLOCK state fixtures: one complete run/effect program executes the same lexical BLOCK in three loop iterations. BLOCK-local saved integer kept retains 11 then17, saved pointer p remains associated with a live target, saved pointer q remains disassociated, saved allocatable a retains allocation and values [21,23] then [27,29], never remains unallocated until the final iteration, and empty retains allocated size0. All observations occur inside the BLOCK; feature mutations alter the corresponding first-iteration state.",
}
LIMITATIONS = {
    (POINTER_SECTION, "C854"): "C854 pointer-entity conflict diagnostic boundaries: only ALLOCATABLE and TARGET conflicts on ordinary scalar entities are discharged. INTRINSIC and coarray conflicts, component/parent roles and target-attribute controls remain pending. LFortran target acceptance or ASR/internal reports are reported as compiler defects, not accepted diagnostics.",
    (POINTER_SECTION, "S8.5.14-001"): "S8.5.14-001 data-pointer state boundaries: no invalid unassociated dereference, nondefinable target, zero-size target, aliasing, lifetime or diagnostic policy is claimed. The undefined target's old value is never read before pointer definition.",
    (POINTER_SECTION, "S8.5.14-002"): "S8.5.14-002 deferred-parameter boundaries: only default CHARACTER deferred length and the undefined-payload LEN boundary are covered. PDT parameters, disassociated/inactive inquiries and procedure-result boundaries remain pending; no address or descriptor representation is asserted.",
    (POINTER_SECTION, "S8.5.14-003"): "S8.5.14-003 procedure-pointer boundaries: only status inquiry without invocation and a compatible associated function call are covered. Disassociated calls, dummy-procedure argument contexts, intrinsic targets and lifetime/source contrasts remain pending.",
    (SAVE_SECTION, "C861"): "C861 SAVE excluded-constant diagnostic boundaries: only named-constant-excluded is discharged. Admission-only ordinary-variable, procedure-pointer and named-common-block facets are restored to pending because they have no diagnostic negative/control pair or conforming feature mutation in this packet. Procedure-name forms and C862 exclusions retain separate owners.",
    (SAVE_SECTION, "C862"): "C862 explicit-SAVE exclusion diagnostic boundaries: only dummy, result and common-member exclusions are discharged. Automatic-array/character cases and bare SAVE controls remain pending under their C814/C862 owner-gate notes. LFortran acceptance is reported as a defect, not treated as conformance.",
    (SAVE_SECTION, "S8.5.16-001"): "S8.5.16-001 saved local state boundaries: only live pointer, disassociated pointer, nonempty allocated allocatable, unallocated allocatable and allocated-empty allocatable local states are covered. The fixture does not read undefined values, extend a dead target, test procedure pointers, finalization, END fallthrough or coarrays.",
    (SAVE_SECTION, "S8.5.16-002"): "S8.5.16-002 saved BLOCK state boundaries: only sequential reentry of the same lexical BLOCK is covered. The BLOCK shared-recursive-instances facet remains pending, and no saved name is referenced outside its BLOCK scope.",
}

LIMIT_PREFIXES = {key: value.split(": ", 1)[0] + ": " for key, value in LIMITATIONS.items()}


def manifest_for(case):
    source = SOURCES[case["key"]]
    manifest = dict(schema_version=1, id=case["id"], rule=case["rule"], facets=case["facets"],
                    evidence=case["evidence"], standard="f2023", files=["source.f90"],
                    build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
    if case.get("invalid"):
        manifest["expect"] = dict(phase="compile", step="source", outcome="diagnose",
                                   diagnostic=dict(file="source.f90", line=case["line"], end_line=case["line"],
                                                   excludes_any=EXCLUDES))
    else:
        manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
        manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                   stdout=case["stdout"], stderr="")
    return manifest


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for case in CASES:
        source = SOURCES[case["key"]]
        directory = Path(root) / "tests/fixtures" / case["fixture"]
        manifest = manifest_for(case)
        spec = dict(case, source=source, source_sha256=sha(source.encode("ascii")), manifest=manifest,
                    path=(directory / "fixture.json").relative_to(root).as_posix())
        specs[case["id"]] = spec
        files[directory / "source.f90"] = source.encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def selected_by_section():
    result = {POINTER_SECTION: {}, SAVE_SECTION: {}}
    for case in CASES:
        if case["evidence"] == "positive-control" and case["id"].endswith("_control"):
            continue
        section = case["section"]
        result[section].setdefault(case["rule"], set()).update(case["facets"])
    return result


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    selected = selected_by_section()[section]
    for rule, facets in selected.items():
        matches = [row for row in updated["requirements"] if row["id"] == rule]
        if len(matches) != 1:
            raise ValueError(f"requirement {rule} not found exactly once")
        owner = matches[0]
        missing = facets - set(owner["facets"])
        if missing:
            raise ValueError(f"selected facets missing for {rule}: {sorted(missing)}")
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        key = (section, rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[key], ORACLES[key])
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIXES[key], LIMITATIONS[key])
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated-region boundaries changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = SUMMARY_BEGIN + "\n" + summary_text(section) + "\n" + SUMMARY_END
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("summary boundaries changed")
        lead, owned = before.split(SUMMARY_BEGIN)
        _, tail = owned.split(SUMMARY_END)
        before = lead.rstrip() + "\n\n" + summary + tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def summary_text(section):
    if section == POINTER_SECTION:
        return """## POINTER/SAVE packet additions for POINTER

This packet adds bounded POINTER fixtures: line-anchored C854 ALLOCATABLE and
TARGET conflicts with one-property controls; a data-pointer run/effect program
for defined-target reference and definition through a previously undefined but
definable target; a CHARACTER deferred-length association program including an
undefined-payload LEN boundary; and a procedure-pointer status/invocation
program. Mutations redirect the association or target procedure so the guarded
feature-specific assertion fails without relying on addresses, undefined reads
or processor diagnostic wording.

Unimplemented facets remain pending for INTRINSIC/coarray conflicts, broader
role/source gates, PDT parameters, invalid dereference or invocation, lifetime
and argument-context source contrasts."""
    return """## POINTER/SAVE packet additions for SAVE

This packet adds a C861 named-constant negative with one-property control,
C862 line-anchored dummy/result/common-member negatives with one-property
controls, explicit saved-local pointer/allocatable state retention, and saved
BLOCK-local state retention. Runtime fixtures guard association or allocation
status before dependent inquiries and mutate the state-establishing feature for
each selected runtime facet.

LFortran-specific acceptance/runtime defects are reported separately; they do
not broaden the standard oracle. C861 admission-only category facets, S8.5.16-003
common-block scope controls, automatic-object cases, recursive BLOCK sharing,
missing-other-scope policy, BIND/bare-SAVE candidates and unselected source-use
gates remain pending."""


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues = {}
    views = {}
    for section, rel in CATALOGUES.items():
        original = json.loads((root / rel).read_text())
        updated = synced_catalogue(section, original)
        catalogues[section] = (original, updated)
        views[section] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, rel in CATALOGUES.items():
            original, updated = catalogues[section]
            if original != updated:
                stale.append(rel)
            if (root / VIEWS[section]).read_text() != views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale pointer/SAVE fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section, rel in CATALOGUES.items():
                (root / rel).write_text(json.dumps(catalogues[section][1], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs


def compiler_command(compiler, std, source, exe):
    name = Path(compiler).name.lower()
    flag = f"--std={std}" if "lfortran" in name else f"-std={std}"
    return [str(compiler), flag, str(source), "-o", str(exe)]


def run_one(command, cwd):
    return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)


def apply_mutation(source, mutation):
    if source.count(mutation["old"]) != 1:
        raise ValueError(f"mutation {mutation['id']} old text not unique")
    return source.replace(mutation["old"], mutation["new"])


KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "S8_5_16_001_valid__pointer_save_local_states",
        "S8_5_16_002_valid__pointer_save_block_states",
    }
}


def compiler_family(compiler):
    name = Path(str(compiler)).name.lower()
    if "lfortran" in name:
        return "lfortran"
    if "gfortran" in name:
        return "gfortran"
    return name


def known_parent_failure(compiler, case_id):
    return case_id in KNOWN_PARENT_FAILURES.get(compiler_family(compiler), set())


def run_mutations(root=ROOT, compiler=None, std=None):
    root = Path(root)
    specs = generate(root, check=True)
    work = root / ".mutation-work-pointer-save"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    results = []
    try:
        for spec in specs.values():
            if spec.get("invalid") or not spec.get("mutations"):
                continue
            case_dir = work / spec["id"]
            case_dir.mkdir()
            parent_src = case_dir / "source.f90"
            parent_src.write_text(spec["source"])
            exe = case_dir / "program"
            comp = run_one(compiler_command(compiler, std, parent_src, exe), case_dir)
            if comp.returncode != 0:
                status = "skipped-known-parent" if known_parent_failure(compiler, spec["id"]) else "parent-compile-failed"
                results.append(dict(case=spec["id"], mutant="<parent>", status=status,
                                    reason="known LFortran parent defect" if status == "skipped-known-parent" else None,
                                    stderr=comp.stderr))
                continue
            run = run_one([str(exe)], case_dir)
            if run.returncode != 0 or run.stdout != spec["stdout"] or run.stderr != "":
                status = "skipped-known-parent" if known_parent_failure(compiler, spec["id"]) else "parent-run-failed"
                results.append(dict(case=spec["id"], mutant="<parent>", status=status,
                                    reason="known LFortran parent defect" if status == "skipped-known-parent" else None,
                                    stdout=run.stdout, stderr=run.stderr, code=run.returncode))
                continue
            for mutation in spec["mutations"]:
                mdir = case_dir / mutation["id"]
                mdir.mkdir()
                msrc = mdir / "source.f90"
                msrc.write_text(apply_mutation(spec["source"], mutation))
                mexe = mdir / "program"
                mcomp = run_one(compiler_command(compiler, std, msrc, mexe), mdir)
                if mcomp.returncode != 0:
                    results.append(dict(case=spec["id"], mutant=mutation["id"], facet=mutation["facet"], status="mutant-compile-failed", stderr=mcomp.stderr))
                    continue
                mrun = run_one([str(mexe)], mdir)
                failed = mrun.returncode != 0 or mrun.stdout != spec["stdout"] or mrun.stderr != ""
                results.append(dict(case=spec["id"], mutant=mutation["id"], facet=mutation["facet"], status="failed" if failed else "survived", code=mrun.returncode, stdout=mrun.stdout, stderr=mrun.stderr))
        bad = [r for r in results if r["status"] not in {"failed", "skipped-known-parent"}]
        skipped = [r for r in results if r["status"] == "skipped-known-parent"]
        print(json.dumps(dict(compiler=str(compiler), std=std, total=len(results),
                              failed=sum(1 for r in results if r["status"] == "failed"),
                              skipped_known_parent=len(skipped), bad=bad, skipped=skipped,
                              results=results), indent=2))
        if bad:
            raise SystemExit(1)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutations", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if args.mutations:
        if not args.compiler or not args.std:
            parser.error("--mutations requires --compiler and --std")
        run_mutations(args.root, args.compiler, args.std)
        return
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    selected = selected_by_section()
    facet_count = sum(len(facets) for rules in selected.values() for facets in rules.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} POINTER/SAVE cases and {facet_count} discharged facets.")


if __name__ == "__main__":
    main()
