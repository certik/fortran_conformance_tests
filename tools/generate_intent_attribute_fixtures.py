#!/usr/bin/env python3
"""Finite INTENT attribute fixtures for Fortran 2023 8.5.10."""
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
SECTION = "8.5.10"
CATALOGUE = "doc/catalogues/intent_attribute_8_5_10.json"
VIEW = "doc/fortran_2023_8_5_10.md"
PREFIX = "intent_attribute_"
SUMMARY_BEGIN = "<!-- BEGIN INTENT ATTRIBUTE FIXTURES -->"
SUMMARY_END = "<!-- END INTENT ATTRIBUTE FIXTURES -->"
KNOWN_PARENT_FAILURES = {
    "lfortran": {"S8_5_10_002_valid__intent_attribute_pointer_dummy_target"},
}
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "assert", "asr", "verifier", "out of memory", "traceback",
    "unknown exception", "segmentation", "bus error", "abort", "cannot read module",
)
SELECTED = {
    "C846": ["assignment-and-loop-contexts"],
    "S8.5.10-002": ["target-definition-controls"],
    "S8.5.10-003": [
        "plain-entry-context", "default-initialized-exception-source",
        "allocatable-entry-deallocation", "redefinition-before-use",
    ],
    "S8.5.10-004": ["definable-variable-controls"],
    "S8.5.10-008": [
        "definable-actual-controls", "nonmodifying-inout-source", "partial-definition-and-retention",
    ],
    "S8.5.10-011": ["pointer-subobject-target-boundary"],
}
ORACLE_PREFIXES = {
    "C846": "C846 assignment diagnostic fixture family: ",
    "S8.5.10-002": "S8.5.10-002 IN pointer target-definition fixture: ",
    "S8.5.10-003": "S8.5.10-003 OUT entry effect fixtures: ",
    "S8.5.10-004": "S8.5.10-004 OUT definable actual fixture: ",
    "S8.5.10-008": "S8.5.10-008 INOUT definable actual fixtures: ",
    "S8.5.10-011": "S8.5.10-011 inherited pointer-subobject INTENT fixture: ",
}
LIMIT_PREFIXES = {
    "C846": "C846 assignment diagnostic boundaries: ",
    "S8.5.10-002": "S8.5.10-002 IN pointer target-definition boundaries: ",
    "S8.5.10-003": "S8.5.10-003 OUT entry effect boundaries: ",
    "S8.5.10-004": "S8.5.10-004 OUT definable actual boundaries: ",
    "S8.5.10-008": "S8.5.10-008 INOUT definable actual boundaries: ",
    "S8.5.10-011": "S8.5.10-011 pointer-subobject boundaries: ",
}
ORACLES = {
    "C846": ORACLE_PREFIXES["C846"] + (
        "two compile/f2023 negatives put an ordinary nonpointer INTEGER dummy declared INTENT(IN) in "
        "19.6.7 variable definition contexts: an intrinsic assignment-stmt variable and a do-variable in "
        "a DO statement. The assignment control changes only the dummy attribute to INTENT(INOUT), calls it "
        "with a writable scalar actual, and observes the returned value 5. The DO control changes only the "
        "DO variable to a local INTEGER variable and observes a three-iteration marker count while leaving "
        "the INTENT(IN) dummy unchanged. Diagnostics must originate at the offending assignment or DO line "
        "and must mention INTENT(IN) or intent(in), while unsupported-feature, internal-error and source-echo "
        "routes are excluded."
    ),
    "S8.5.10-002": ORACLE_PREFIXES["S8.5.10-002"] + (
        "one run/positive-control/f2023 fixture passes a pointer dummy with INTENT(IN) that is already "
        "associated with a live INTEGER target. The callee verifies defined association to the target, "
        "executes p = 13 to define that target without changing pointer association, and the caller verifies "
        "both unchanged association and the distinguished target value 13. The mutation changes only the "
        "assigned target value to 17, so association-only implementations or target-write rejections are exposed."
    ),
    "S8.5.10-003": ORACLE_PREFIXES["S8.5.10-003"] + (
        "three run/context-only/f2023 fixtures observe selected portable consequences of nonpointer INTENT(OUT). "
        "The scalar fixture calls an OUT dummy with a writable actual and reads the actual only after the callee "
        "defines it as 47. The derived-type fixture enters with an actual whose default-initialized component "
        "has the nondefault value 17; on invocation the OUT dummy's default-initialized component has value 41, "
        "while the non-default component is assigned 23 before any read. The allocatable fixture allocates the "
        "actual to size 5 before the call, observes inside the OUT callee that the dummy is not allocated, then "
        "allocates size 2 and returns values [31,37]. Feature mutations remove INTENT(OUT), change the default "
        "initializer, or alter the returned values, so old-value retention, missing entry deallocation and wrong "
        "post-definition implementations fail without reading undefined data. Finalization evidence is split out "
        "and remains pending."
    ),
    "S8.5.10-004": ORACLE_PREFIXES["S8.5.10-004"] + (
        "the scalar OUT fixture uses a writable ordinary INTEGER actual, never reads the initially undefined "
        "dummy, and observes only the value 47 after the callee defines it. Mutations that remove or change the "
        "definition fail at run time."
    ),
    "S8.5.10-008": ORACLE_PREFIXES["S8.5.10-008"] + (
        "two run/positive-control/f2023 fixtures use ordinary writable scalar actuals for nonpointer INOUT "
        "dummies. The nonmodifying call reads a defined incoming value 61 and returns without changing it, "
        "showing INOUT's definable-actual requirement is not coupled to a write. The writing call assigns 73 "
        "before the caller reads the result. Mutations remove or change the write or incoming value checks, so "
        "no no-op or OUT-style entry-undefinition oracle can survive."
    ),
    "S8.5.10-011": ORACLE_PREFIXES["S8.5.10-011"] + (
        "one run/positive-control/f2023 fixture passes a nonpointer derived-type dummy with INTENT(IN) and a pointer "
        "component already associated with a live INTEGER target. The callee verifies the pointer component's "
        "association to that target, assigns 90 through the component to define the target, and the caller "
        "verifies both unchanged association and the target value. This observes the pointer-subobject/target "
        "boundary without reassociating the INTENT(IN) pointer subobject."
    ),
}
LIMITATIONS = {
    "C846": LIMIT_PREFIXES["C846"] + (
        "only ordinary intrinsic assignment and a DO-statement control variable for a scalar INTEGER nonpointer "
        "INTENT(IN) dummy are represented. I/O implied-DO variables, READ items, result specifiers, allocation "
        "outputs, associate names, coarray controls and subobject contexts remain pending. Reporting is required "
        "for the numbered constraint, but fatal status, exact English and printed rule numbers are not."
    ),
    "S8.5.10-002": LIMIT_PREFIXES["S8.5.10-002"] + (
        "only a data pointer dummy associated with a scalar INTEGER target is covered. Procedure pointers, "
        "nonpointer actual source relations, other-route deallocation, pointer association changes and pointer "
        "components are separate facets. The fixture never queries an undefined association and never deallocates "
        "the target. Frozen LFortran rejects this conforming source by treating p = 13 as assignment to the "
        "INTENT(IN) pointer rather than definition of its target; the reference compiler runs it."
    ),
    "S8.5.10-003": LIMIT_PREFIXES["S8.5.10-003"] + (
        "only single-image INTEGER scalar, a simple derived type with one default-initialized component, and an "
        "ordinary INTEGER allocatable vector are covered. The fixtures do not read a non-default component before "
        "the callee defines it, do not prescribe any bit pattern for undefined data, and do not cover finalization, "
        "pointer OUT association status, OPTIONAL absence, polymorphism, coarrays or statement-wide interference."
    ),
    "S8.5.10-004": LIMIT_PREFIXES["S8.5.10-004"] + (
        "only an ordinary writable scalar actual is covered. Literals, named constants, expressions, data-pointer "
        "function results, optional absence, array sections, vector subscripts and aliasing restrictions remain pending."
    ),
    "S8.5.10-008": LIMIT_PREFIXES["S8.5.10-008"] + (
        "only ordinary writable scalar actuals with already defined values are covered. No invalid expression actual "
        "is shipped because the prose requirement is context-dependent and this packet avoids inventing a compulsory "
        "diagnostic beyond a numbered constraint. Pointer, allocatable, OPTIONAL and data-pointer-result boundaries "
        "remain pending."
    ),
    "S8.5.10-011": LIMIT_PREFIXES["S8.5.10-011"] + (
        "only a data pointer component target-definition control is covered. Reassociation negatives, array elements, "
        "substrings, nonpointer components, allocatable components and complete C846/C847 inherited-intent censuses "
        "remain pending. The target is observed through its independent name after the call; no pointer target is "
        "treated as a subobject that inherits INTENT."
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(rule, variant, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__intent_attribute_{variant}"


def locate_line(source, needle):
    matches = [i + 1 for i, line in enumerate(source.splitlines()) if needle in line]
    if len(matches) != 1:
        raise ValueError(f"line anchor is not unique for {needle!r}")
    return matches[0]


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"mutation text is not unique: {old!r}")
    return source.replace(old, new, 1)


def valid_case(rule, variant, facets, source, derivation, observations, mutations, *, evidence="effect"):
    return dict(id=identifier(rule, variant), rule=rule, variant=variant, kind="valid",
                evidence=evidence, facets=list(facets), source=source, source_sha256=sha(source.encode("ascii")),
                completion=f"INTENT ATTRIBUTE {variant.upper().replace('_', ' ')} OK\n",
                derivation=derivation, observations=list(observations), mutations=list(mutations))


def invalid_case(rule, variant, facets, source, derivation, diagnostic_line, contains, control_id, repair_note):
    return dict(id=identifier(rule, variant, "invalid"), rule=rule, variant=variant, kind="invalid",
                evidence="effect", facets=list(facets), source=source, source_sha256=sha(source.encode("ascii")),
                derivation=derivation,
                diagnostic=dict(file="source.f90", line=diagnostic_line, end_line=diagnostic_line,
                                contains_any=list(contains), excludes_any=list(EXCLUSIONS)),
                control_id=control_id, repair_note=repair_note, observations=[], mutations=[])


def source_specs():
    specs = []
    c846_control = """program p
implicit none
integer :: actual
actual = 19
call define_inout(actual)
if (actual /= 5) error stop 1
write(*,'(a)') 'INTENT ATTRIBUTE C846 ASSIGNMENT CONTROL OK'
contains
subroutine define_inout(x)
  integer, intent(inout) :: x
  x = 5
end subroutine
end program p
"""
    specs.append(valid_case(
        "C846", "c846_assignment_control", ["assignment-and-loop-contexts"], c846_control,
        "C846 prohibits the INTENT(IN) form; changing only IN to INOUT gives a conforming variable-definition context with writable actual.",
        ["writable actual actual becomes 5"],
        [dict(id="remove-assignment", source=replace_once(c846_control, "  x = 5", "  ! x = 5")),
         dict(id="change-defined-value", source=replace_once(c846_control, "  x = 5", "  x = 7"))],
        evidence="positive-control"))
    c846_invalid = replace_once(c846_control, "integer, intent(inout) :: x", "integer, intent(in) :: x")
    c846_invalid = replace_once(c846_invalid, "INTENT ATTRIBUTE C846 ASSIGNMENT CONTROL OK", "INTENT ATTRIBUTE C846 ASSIGNMENT INVALID OK")
    specs.append(invalid_case(
        "C846", "c846_assignment_to_in", ["assignment-and-loop-contexts"], c846_invalid,
        "The only repair is INTENT(IN) to INTENT(INOUT); the assignment statement then reaches C846's variable-definition context prohibition.",
        locate_line(c846_invalid, "x = 5"), ["intent(in)", "INTENT(IN)"], specs[0]["id"],
        "change only the dummy attribute from INTENT(IN) back to INTENT(INOUT)"))

    c846_do_control = """program p
implicit none
integer :: actual
integer :: marker
actual = 19
call local_do_control(actual, marker)
if (actual /= 19) error stop 1
if (marker /= 3) error stop 2
write(*,'(a)') 'INTENT ATTRIBUTE C846 DO VARIABLE CONTROL OK'
contains
subroutine local_do_control(i, marker)
  integer, intent(in) :: i
  integer, intent(out) :: marker
  integer :: j
  marker = 0
  do j = 1, 3
    marker = marker + 1
  end do
end subroutine
end program p
"""
    specs.append(valid_case(
        "C846", "c846_do_variable_control", ["assignment-and-loop-contexts"], c846_do_control,
        "C846 prohibits using the INTENT(IN) dummy as a DO variable; changing only the loop control variable to a local INTEGER gives a conforming three-iteration control.",
        ["INTENT(IN) dummy actual remains 19", "local DO variable produces marker 3"],
        [dict(id="remove-do-marker-increment", source=replace_once(c846_do_control, "    marker = marker + 1", "    ! marker = marker + 1")),
         dict(id="change-do-trip-count", source=replace_once(c846_do_control, "  do j = 1, 3", "  do j = 1, 2"))],
        evidence="positive-control"))
    c846_do_invalid = replace_once(c846_do_control, "  do j = 1, 3", "  do i = 1, 3")
    c846_do_invalid = replace_once(c846_do_invalid, "INTENT ATTRIBUTE C846 DO VARIABLE CONTROL OK", "INTENT ATTRIBUTE C846 DO VARIABLE INVALID OK")
    specs.append(invalid_case(
        "C846", "c846_do_variable_to_in", ["assignment-and-loop-contexts"], c846_do_invalid,
        "The only repair is changing the DO variable from the INTENT(IN) dummy i to local variable j; the invalid source reaches the 19.6.7 DO-variable context.",
        locate_line(c846_do_invalid, "do i = 1, 3"), ["intent(in)", "INTENT(IN)"], specs[-1]["id"],
        "change only the DO variable from the INTENT(IN) dummy i back to local variable j"))

    pointer_dummy = """program p
implicit none
integer, target :: target
integer, target :: other
integer, pointer :: actual
target = 71
other = 82
actual => target
call define_pointer_dummy_target(actual, target)
if (.not. associated(actual, target)) error stop 1
if (associated(actual, other)) error stop 2
if (target /= 13) error stop 3
write(*,'(a)') 'INTENT ATTRIBUTE POINTER DUMMY TARGET OK'
contains
subroutine define_pointer_dummy_target(p, original)
  integer, pointer, intent(in) :: p
  integer, target, intent(inout) :: original
  if (.not. associated(p, original)) error stop 4
  p = 13
  if (.not. associated(p, original)) error stop 5
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-002", "pointer_dummy_target", ["target-definition-controls"], pointer_dummy,
        "8.5.10p2 restricts an INTENT(IN) pointer dummy's association, not definition of its associated definable target; p = 13 changes the target value while association remains with original.",
        ["pointer dummy remains associated with original target", "target value becomes 13"],
        [dict(id="change-pointer-target-definition", source=replace_once(pointer_dummy, "  p = 13", "  p = 17"))],
        evidence="positive-control"))

    out_scalar = """program p
implicit none
integer :: actual
actual = 29
call define_out(actual)
if (actual /= 47) error stop 1
write(*,'(a)') 'INTENT ATTRIBUTE OUT SCALAR DEFINE OK'
contains
subroutine define_out(x)
  integer, intent(out) :: x
  x = 47
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-004", "out_scalar_define", ["definable-variable-controls"], out_scalar,
        "8.5.10p3 requires a definable actual for a nonpointer OUT dummy; the writable scalar actual is read only after x is defined as 47.",
        ["actual is 47 after OUT callee assignment"],
        [dict(id="remove-out-definition", source=replace_once(out_scalar, "  x = 47", "  ! x = 47")),
         dict(id="change-out-definition", source=replace_once(out_scalar, "  x = 47", "  x = 49"))],
        evidence="positive-control"))

    out_default = """program p
implicit none
type box
  integer :: stamp = 41
  integer :: payload
end type box
type(box) :: actual
actual%stamp = 17
actual%payload = 19
call observe_out_default(actual)
if (actual%stamp /= 41) error stop 1
if (actual%payload /= 23) error stop 2
write(*,'(a)') 'INTENT ATTRIBUTE OUT DEFAULT INITIALIZED OK'
contains
subroutine observe_out_default(x)
  type(box), intent(out) :: x
  if (x%stamp /= 41) error stop 3
  x%payload = 23
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-003", "out_default_initialized", ["default-initialized-exception-source", "redefinition-before-use"], out_default,
        "8.5.10p3 makes a nonpointer OUT dummy undefined on invocation except default-initialized subcomponents; x%stamp is 41 on entry and x%payload is assigned before any read.",
        ["default-initialized component stamp is 41 on entry", "payload is defined as 23 before caller reads it"],
        [dict(id="remove-out-intent", source=replace_once(out_default, "type(box), intent(out) :: x", "type(box) :: x")),
         dict(id="change-default-initializer", source=replace_once(out_default, "integer :: stamp = 41", "integer :: stamp = 43")),
         dict(id="change-payload-definition", source=replace_once(out_default, "  x%payload = 23", "  x%payload = 25"))],
        evidence="context-only"))

    out_alloc = """program p
implicit none
integer, allocatable :: actual(:)
allocate(actual(5))
actual = [1,2,3,4,5]
call observe_out_allocatable(actual)
if (.not. allocated(actual)) error stop 1
if (size(actual) /= 2) error stop 2
if (any(actual /= [31,37])) error stop 3
write(*,'(a)') 'INTENT ATTRIBUTE OUT ALLOCATABLE DEALLOCATED OK'
contains
subroutine observe_out_allocatable(x)
  integer, allocatable, intent(out) :: x(:)
  if (allocated(x)) error stop 4
  allocate(x(2))
  x = [31,37]
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-003", "out_allocatable_deallocated", ["allocatable-entry-deallocation"], out_alloc,
        "An allocated actual associated with an allocatable INTENT(OUT) dummy is deallocated on entry; the callee observes .not.allocated before allocating size 2.",
        ["allocated size-5 actual is unallocated on callee entry", "returned allocation has size 2 and values 31,37"],
        [dict(id="remove-out-intent", source=replace_once(out_alloc, "integer, allocatable, intent(out) :: x(:)", "integer, allocatable :: x(:)")),
         dict(id="change-returned-value", source=replace_once(out_alloc, "  x = [31,37]", "  x = [31,39]"))],
        evidence="context-only"))

    out_plain = """program p
implicit none
integer :: actual
actual = 83
call plain_out(actual)
if (actual /= 47) error stop 1
write(*,'(a)') 'INTENT ATTRIBUTE OUT PLAIN ENTRY OK'
contains
subroutine plain_out(x)
  integer, intent(out) :: x
  x = 47
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-003", "out_plain_entry", ["plain-entry-context"], out_plain,
        "The call establishes a nonpointer OUT invocation context and defines the dummy before any subsequent reference to the actual.",
        ["actual is 47 after OUT callee assignment"],
        [dict(id="remove-out-definition", source=replace_once(out_plain, "  x = 47", "  ! x = 47")),
         dict(id="change-out-definition", source=replace_once(out_plain, "  x = 47", "  x = 48"))],
        evidence="context-only"))

    inout = """program p
implicit none
integer :: actual
actual = 61
call retain_inout(actual)
if (actual /= 61) error stop 1
call write_inout(actual)
if (actual /= 73) error stop 2
write(*,'(a)') 'INTENT ATTRIBUTE INOUT DEFINABLE ACTUAL OK'
contains
subroutine retain_inout(x)
  integer, intent(inout) :: x
  if (x /= 61) error stop 3
end subroutine
subroutine write_inout(x)
  integer, intent(inout) :: x
  x = 73
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-008", "inout_definable_actual", ["definable-actual-controls", "nonmodifying-inout-source", "partial-definition-and-retention"], inout,
        "8.5.10p4 requires a definable actual for nonpointer INOUT; a writable scalar is valid for both a nonmodifying read and a later defining call.",
        ["nonmodifying INOUT call retains 61", "writing INOUT call returns 73"],
        [dict(id="change-incoming-value", source=replace_once(inout, "actual = 61", "actual = 62")),
         dict(id="remove-inout-write", source=replace_once(inout, "  x = 73", "  ! x = 73")),
         dict(id="change-inout-write", source=replace_once(inout, "  x = 73", "  x = 79"))],
        evidence="positive-control"))

    component = """program p
implicit none
type pointer_box
  integer, pointer :: p
end type pointer_box
type(pointer_box) :: actual
integer, target :: target
integer, target :: other
target = 70
other = 80
actual%p => target
call define_pointer_component_target(actual, target)
if (.not. associated(actual%p, target)) error stop 1
if (associated(actual%p, other)) error stop 2
if (target /= 90) error stop 3
write(*,'(a)') 'INTENT ATTRIBUTE POINTER COMPONENT TARGET OK'
contains
subroutine define_pointer_component_target(x, original)
  type(pointer_box), intent(in) :: x
  integer, target, intent(inout) :: original
  if (.not. associated(x%p, original)) error stop 4
  x%p = 90
  if (.not. associated(x%p, original)) error stop 5
end subroutine
end program p
"""
    specs.append(valid_case(
        "S8.5.10-011", "pointer_component_target", ["pointer-subobject-target-boundary"], component,
        "8.5.10p6 gives the pointer component itself inherited IN intent, but note3's normative distinction means the associated definable target can be defined through it without reassociation.",
        ["component pointer remains associated with original target", "target value becomes 90"],
        [dict(id="remove-target-definition", source=replace_once(component, "  x%p = 90", "  ! x%p = 90")),
         dict(id="change-target-definition", source=replace_once(component, "  x%p = 90", "  x%p = 91"))],
        evidence="positive-control"))

    return {spec["id"]: spec for spec in specs}


def manifest(spec):
    item = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                standard="f2023", evidence=spec["evidence"], files=["source.f90"],
                build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
    if spec["kind"] == "invalid":
        item["expect"] = dict(phase="compile", step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
    else:
        item["link"] = dict(driver="fortran", objects=["source.o"], output="program")
        item["expect"] = dict(phase="run", outcome="success", exit_code=0,
                               stdout=[spec["completion"]], stderr=[""])
    return item


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, source_specs()
    for spec in specs.values():
        folder = root / "tests" / "fixtures" / (PREFIX + spec["variant"])
        spec["path"] = folder.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest(spec)
        files[folder / "source.f90"] = spec["source"].encode("ascii")
        files[folder / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    s003 = by_rule.get("S8.5.10-003")
    if s003 is not None:
        facets = s003["facets"]
        if "allocation-finalization-relations" in facets:
            index = facets.index("allocation-finalization-relations")
            facets[index:index + 1] = ["allocatable-entry-deallocation", "finalization-relations"]
        elif "allocatable-entry-deallocation" not in facets:
            facets.append("allocatable-entry-deallocation")
        pending = s003.setdefault("pending", {})
        pending.pop("allocation-finalization-relations", None)
        pending.setdefault(
            "finalization-relations",
            "PENDING exact 7.5.6.3 pre-undefinition finalization relations for nonallocatable and "
            "allocatable OUT entry paths, using a finalizable derived type with a distinguished marker. "
            "The allocatable entry-deallocation fixture does not claim finalization evidence.")
    for rule, facets in SELECTED.items():
        if rule not in by_rule:
            raise ValueError(f"missing rule {rule}")
        row = by_rule[rule]
        if not set(facets) <= set(row["facets"]):
            raise ValueError(f"selected facets changed for {rule}")
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        if not row.get("pending"):
            row.pop("pending", None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    old = "**Source independently reviewed in batch053.** Every implementation facet\nremains pending. Effective source status is\n`Registry.catalogue_review_state(\"8.5.10\")`. No case, source-use,\ncanonical-link or compiler approval follows from source accounting."
    new = "**Source independently reviewed in batch053.** Selected implementation facets\nare now discharged by the generated INTENT attribute fixture packet below.\nEffective source status remains\n`Registry.catalogue_review_state(\"8.5.10\")`; no unlisted case, source-use,\ncanonical-link or compiler approval follows from source accounting."
    if old in text:
        text = text.replace(old, new, 1)
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (SUMMARY_BEGIN + "\n"
        "## INTENT attribute fixture packet\n\n"
        "Eleven generated fixtures discharge eleven selected 8.5.10 facets. Two C846\n"
        "compile negatives assign to, or use as a DO variable, an INTENT(IN) scalar\n"
        "dummy and each has a one-property conforming control. Runtime fixtures observe\n"
        "IN pointer target definition, OUT scalar definition, default initialization of\n"
        "an OUT derived-type subcomponent, allocatable OUT entry deallocation, INOUT\n"
        "definable-actual controls, and the inherited INTENT pointer-component target\n"
        "boundary. No fixture reads an undefined OUT value.\n\n"
        "The selected mutation matrix changes the feature under test or a required\n"
        "literal while keeping mutants conforming: removing INTENT(OUT) from the\n"
        "allocatable case leaves the dummy allocated on entry, removing INTENT(OUT)\n"
        "from the default-initialization case exposes the old stamp value, and removing\n"
        "target or result definitions leaves independently checked sentinels unchanged.\n"
        "The allocatable OUT case is split from finalization, which remains pending.\n"
        "Every unselected context, pointer reassociation negative, coarray/opaque-type\n"
        "case and undefined-state source relation remains pending.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("intent summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, _ = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
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
            raise ValueError("stale INTENT attribute fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return files, source_specs()


def executable_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}", str(source), "-o", str(output)]
    return [compiler, f"-std={std}", str(source), "-o", str(output)]


def compiler_family(compiler):
    name = Path(compiler).name.lower()
    return "lfortran" if "lfortran" in name else "gfortran"


def run_source(compiler, std, root, source, exe):
    compile_result = subprocess.run(
        executable_command(compiler, std, source, exe), cwd=root,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if compile_result.returncode != 0:
        return "compile-fail", compile_result.stdout
    run_result = subprocess.run([str(exe)], cwd=root, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    return ("pass" if run_result.returncode == 0 else "run-fail"), run_result.stdout


def check_mutations(root, compiler, std):
    root = Path(root)
    _, specs = build_corpus(root)
    mutations = [(spec, mutation) for spec in specs.values() if spec["kind"] == "valid"
                 for mutation in spec["mutations"]]
    if not mutations:
        raise SystemExit("no INTENT attribute mutations defined")
    workspace = root / ".intent_attribute_mutations"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    failures = []
    skipped = []
    checked = 0
    family = compiler_family(compiler)
    try:
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
            case_dir.mkdir()
            parent_source = case_dir / "parent.f90"
            parent_exe = case_dir / "parent"
            parent_source.write_text(spec["source"])
            parent_status, parent_output = run_source(compiler, std, root, parent_source, parent_exe)
            if parent_status != "pass" and spec["id"] in KNOWN_PARENT_FAILURES.get(family, set()):
                skipped.append(f"{spec['id']}:{mutation['id']}")
                continue
            if parent_status != "pass":
                failures.append(f"{spec['id']} parent did not pass before mutation ({parent_status}):\n{parent_output}")
                continue
            source = case_dir / "source.f90"
            exe = case_dir / "program"
            source.write_text(mutation["source"])
            status, output = run_source(compiler, std, root, source, exe)
            if status == "compile-fail":
                failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{output}")
                continue
            checked += 1
            if status == "pass":
                failures.append(f"{spec['id']}:{mutation['id']} survived")
        if failures:
            raise SystemExit("\n\n".join(failures))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    note = f"; {len(skipped)} known parent-failure mutants not run" if skipped else ""
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
    if args.check_mutations and (not args.compiler or not args.std):
        parser.error("--check-mutations requires --compiler and --std")
    if args.check_mutations:
        check_mutations(args.root, args.compiler, args.std)
        return
    _, specs = generate(args.root, args.check, args.sync_catalogue)
    facets = sum(len(spec["facets"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} INTENT attribute cases and {facets} facet bindings.")


if __name__ == "__main__":
    main()
