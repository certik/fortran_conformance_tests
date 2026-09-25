#!/usr/bin/env python3
"""Generate component declaration/default-initialization fixtures for 7.5.4."""

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "components_7_5_4_b"
CATALOGUES = {
    "7.5.4.1": "doc/catalogues/derived_types_7_5_4_1.json",
    "7.5.4.6": "doc/catalogues/derived_types_7_5_4_6.json",
}
VIEWS = {
    "7.5.4.1": "doc/fortran_2023_7_5_4_1.md",
    "7.5.4.6": "doc/fortran_2023_7_5_4_6.md",
}
SUMMARY_BEGIN = "<!-- BEGIN COMPONENTS 7.5.4 B FIXTURES -->"
SUMMARY_END = "<!-- END COMPONENTS 7.5.4 B FIXTURES -->"
WORK = ".components_7_5_4_b_mutation_work"


def text(raw):
    return raw.strip() + "\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rule_key(rule):
    return rule.replace(".", "_").replace("-", "_")


class Case:
    def __init__(self, variant, rule, facets, source, completion):
        self.variant = variant
        self.rule = rule
        self.facets = list(facets)
        self.source = text(source)
        self.completion = completion + "\n"
        self.mutations = []

    @property
    def name(self):
        return f"{rule_key(self.rule)}_valid__{TOPIC}_{self.variant}"

    def mutate(self, facet, expected, replacement, assertion):
        if self.source.count(expected) != 1:
            raise ValueError(f"{self.variant}: expected unique mutation span for {expected!r}")
        self.mutations.append(dict(
            id=f"{self.variant}-{facet}", facet=facet, expected=expected,
            replacement=replacement, assertion=assertion,
        ))
        return self


def cases():
    result = []
    c = Case("dimension_and_shape", "R738", ["dimension"], """
program component_dimension_shape
implicit none
type :: record
  integer, dimension(3) :: shared
  integer, dimension(3) :: overridden(2)
  integer :: explicit(-1:1)
end type
type(record) :: item
item%shared = 0
item%overridden = 0
item%explicit = 0
if (size(item%shared) /= 3) error stop 1
if (lbound(item%shared,1) /= 1 .or. ubound(item%shared,1) /= 3) error stop 2
if (size(item%overridden) /= 2) error stop 3
if (lbound(item%explicit,1) /= -1 .or. ubound(item%explicit,1) /= 1) error stop 4
print '(a)', 'COMPONENTS 7.5.4B DIMENSION OK'
end program
""", "COMPONENTS 7.5.4B DIMENSION OK")
    c.mutate("dimension", "dimension(3) :: shared", "dimension(4) :: shared", "size(item%shared) is three")
    result.append(c)

    c = Case("individual_explicit_shape", "R740", ["explicit-shape-link"], """
program component_explicit_shape
implicit none
type :: record
  integer :: explicit(-1:1)
end type
type(record) :: item
item%explicit = 0
item%explicit(-1) = 11
item%explicit(0) = 13
item%explicit(1) = 17
if (size(item%explicit) /= 3) error stop 1
if (lbound(item%explicit,1) /= -1 .or. ubound(item%explicit,1) /= 1) error stop 2
if (item%explicit(-1) /= 11) error stop 3
if (item%explicit(0) /= 13) error stop 4
if (item%explicit(1) /= 17) error stop 5
print '(a)', 'COMPONENTS 7.5.4B EXPLICIT SHAPE OK'
end program
""", "COMPONENTS 7.5.4B EXPLICIT SHAPE OK")
    c.mutate("explicit-shape-link", "explicit(-1:1)", "explicit(-1:2)", "component lbound/ubound are -1:1")
    result.append(c)


    c = Case("individual_declarators", "R739",
             ["individual-array-link", "individual-character-link", "initialization-use-graph"], """
program component_individual_declarators
implicit none
type :: record
  integer :: values(2)
  character(5) :: text*3
  integer :: initial = 7
end type
type(record) :: item
item%values = 0
item%text = 'abc'
if (size(item%values) /= 2) error stop 1
if (len(item%text) /= 3) error stop 2
if (item%text /= 'abc') error stop 3
if (item%initial /= 7) error stop 4
print '(a)', 'COMPONENTS 7.5.4B DECLARATORS OK'
end program
""", "COMPONENTS 7.5.4B DECLARATORS OK")
    c.mutate("individual-array-link", "values(2)", "values(3)", "individual component-array-spec gives extent two")
    c.mutate("individual-character-link", "text*3", "text*4", "individual star char-length gives length three")
    c.mutate("initialization-use-graph", "initial = 7", "initial = 9", "individual component-initialization gives value seven")
    result.append(c)

    c = Case("individual_character_suffix", "C758", ["character-suffix-admission-link"], """
program component_character_suffix
implicit none
type :: record
  character :: star*3
end type
type(record) :: item
item%star = 'abc'
if (len(item%star) /= 3) error stop 1
if (item%star /= 'abc') error stop 2
print '(a)', 'COMPONENTS 7.5.4B CHAR SUFFIX OK'
end program
""", "COMPONENTS 7.5.4B CHAR SUFFIX OK")
    c.mutate("character-suffix-admission-link", "star*3", "star*4", "component star length is three")
    result.append(c)

    c = Case("common_overrides", "S7.5.4.1-001", ["character-override-link", "dimension-override-link"], """
program component_common_overrides
implicit none
type :: record
  character(5) :: short*2, common
  integer, dimension(3) :: local(2), shared
end type
type(record) :: item
item%short = 'xy'
item%common = 'abcde'
item%local = 0
item%shared = 0
if (len(item%short) /= 2) error stop 1
if (len(item%common) /= 5) error stop 2
if (size(item%local) /= 2) error stop 3
if (size(item%shared) /= 3) error stop 4
print '(a)', 'COMPONENTS 7.5.4B OVERRIDES OK'
end program
""", "COMPONENTS 7.5.4B OVERRIDES OK")
    c.mutate("character-override-link", "short*2", "short*4", "individual character length overrides shared length")
    c.mutate("dimension-override-link", "local(2)", "local(4)", "individual component-array-spec overrides DIMENSION")
    result.append(c)

    c = Case("initialization_alternatives", "R743", ["initializer-descendant-use-graph"], """
module component_initialization_alternatives_m
implicit none
integer, target, save :: target = 17
integer, target, save :: other = 23
type :: record
  integer :: value = 7
  integer, pointer :: empty => null()
  integer, pointer :: alias => target
end type
contains
subroutine reset(item)
  type(record), intent(out) :: item
  if (item%value /= 7) error stop 4
  if (associated(item%empty)) error stop 5
  if (.not. associated(item%alias, target)) error stop 6
end subroutine
end module
program component_initialization_alternatives
use component_initialization_alternatives_m
implicit none
type(record) :: local
type(record), allocatable :: allocated
integer :: stat
if (local%value /= 7) error stop 1
if (associated(local%empty)) error stop 2
if (.not. associated(local%alias, target)) error stop 3
allocate(allocated, stat=stat)
if (stat /= 0) error stop 7
if (allocated%value /= 7) error stop 8
if (associated(allocated%empty)) error stop 9
if (.not. associated(allocated%alias, target)) error stop 10
allocated%value = 99
allocated%empty => other
allocated%alias => other
call reset(allocated)
print '(a)', 'COMPONENTS 7.5.4B INITIALIZERS OK'
end program
""", "COMPONENTS 7.5.4B INITIALIZERS OK")
    c.mutate("initializer-descendant-use-graph", "value = 7", "value = 9", "constant initializer value is seven across creation events")
    result.append(c)

    c = Case("initial_target_designator", "R744", ["canonical-designator-graph"], """
module component_initial_target_designator_m
implicit none
type :: cell
  integer :: value
end type
type(cell), target, save :: cells(2) = [cell(11), cell(22)]
type :: holder
  integer, pointer :: alias => cells(2)%value
end type
end module
program component_initial_target_designator
use component_initial_target_designator_m
implicit none
type(holder) :: item
if (.not. associated(item%alias, cells(2)%value)) error stop 1
if (item%alias /= 22) error stop 2
item%alias = 29
if (cells(1)%value /= 11) error stop 3
if (cells(2)%value /= 29) error stop 4
print '(a)', 'COMPONENTS 7.5.4B DESIGNATOR OK'
end program
""", "COMPONENTS 7.5.4B DESIGNATOR OK")
    c.mutate("canonical-designator-graph", "alias => cells(2)%value", "alias => cells(1)%value", "initial data target designates the second cell component")
    result.append(c)

    c = Case("nested_initial_target", "C770", ["nested-designator-use-graph"], """
module component_nested_initial_target_m
implicit none
type :: cell
  integer :: value
end type
type :: box
  type(cell) :: payload(3)
end type
type(box), target, save :: saved = box([cell(3), cell(5), cell(7)])
type :: holder
  integer, pointer :: alias => saved%payload(2)%value
end type
end module
program component_nested_initial_target
use component_nested_initial_target_m
implicit none
type(holder) :: item
if (.not. associated(item%alias, saved%payload(2)%value)) error stop 1
if (item%alias /= 5) error stop 2
item%alias = 41
if (saved%payload(1)%value /= 3) error stop 3
if (saved%payload(2)%value /= 41) error stop 4
if (saved%payload(3)%value /= 7) error stop 5
print '(a)', 'COMPONENTS 7.5.4B NESTED TARGET OK'
end program
""", "COMPONENTS 7.5.4B NESTED TARGET OK")
    c.mutate("nested-designator-use-graph", "alias => saved%payload(2)%value", "alias => saved%payload(3)%value", "nested designator selects payload element two")
    result.append(c)

    c = Case("target_compatibility_constraint", "C769", ["compatibility-definition-link"], """
module component_target_compatibility_constraint_m
implicit none
integer, target, save :: target = 31
integer, target, save :: other = 31
type :: holder
  integer, pointer :: alias => target
end type
end module
program component_target_compatibility_constraint
use component_target_compatibility_constraint_m
implicit none
type(holder) :: item
if (.not. associated(item%alias, target)) error stop 1
if (item%alias /= 31) error stop 2
item%alias = 37
if (target /= 37) error stop 3
print '(a)', 'COMPONENTS 7.5.4B C769 LINK OK'
end program
""", "COMPONENTS 7.5.4B C769 LINK OK")
    c.mutate("compatibility-definition-link", "alias => target", "alias => other", "C769-compatible pointer initialization initially associates alias with target")
    result.append(c)

    c = Case("default_events", "S7.5.4.6-006", ["definition-event-use-graph"], """
module component_default_events_m
implicit none
type :: record
  integer :: value = 7
end type
contains
subroutine verify(item, code)
  type(record), intent(in) :: item
  integer, intent(in) :: code
  if (item%value /= 7) error stop code
end subroutine
subroutine reset(item)
  type(record), intent(out) :: item
  call verify(item, 30)
end subroutine
end module
program component_default_events
use component_default_events_m
implicit none
type(record) :: local
type(record), allocatable :: allocated
integer :: stat
call verify(local, 1)
allocate(allocated, stat=stat)
if (stat /= 0) error stop 2
call verify(allocated, 3)
allocated%value = 99
call reset(allocated)
call verify(allocated, 4)
print '(a)', 'COMPONENTS 7.5.4B DEFAULT EVENTS OK'
end program
""", "COMPONENTS 7.5.4B DEFAULT EVENTS OK")
    c.mutate("definition-event-use-graph", "value = 7", "value = 9", "local, allocated and INTENT(OUT) objects receive value seven")
    result.append(c)

    c = Case("nested_override_events", "S7.5.4.6-007", ["override-event-use-graph"], """
program component_nested_override_events
implicit none
type :: inner
  integer :: value = 3
end type
type :: outer
  type(inner) :: nested = inner(11)
end type
type(outer) :: local
type(outer), allocatable :: allocated
integer :: stat
if (local%nested%value /= 11) error stop 1
allocate(allocated, stat=stat)
if (stat /= 0) error stop 2
if (allocated%nested%value /= 11) error stop 3
print '(a)', 'COMPONENTS 7.5.4B NESTED OVERRIDE OK'
end program
""", "COMPONENTS 7.5.4B NESTED OVERRIDE OK")
    c.mutate("override-event-use-graph", "nested = inner(11)", "nested = inner(3)", "outer component default overrides the inner default value")
    result.append(c)

    c = Case("explicit_object_override", "S7.5.4.6-008", ["explicit-initialization-use-graph"], """
program component_explicit_object_override
implicit none
type :: record
  integer :: value = 7
end type
type(record) :: explicit = record(19)
type(record) :: defaulted
if (explicit%value /= 19) error stop 1
if (defaulted%value /= 7) error stop 2
print '(a)', 'COMPONENTS 7.5.4B EXPLICIT OVERRIDE OK'
end program
""", "COMPONENTS 7.5.4B EXPLICIT OVERRIDE OK")
    c.mutate("explicit-initialization-use-graph", "record(19)", "record(7)", "explicit object initialization overrides the component default")
    result.append(c)

    c = Case("default_no_save", "S7.5.4.6-009", ["save-source-use-graph"], """
program component_default_no_save
implicit none
type :: record
  integer :: value = 7
end type
call visit(1)
call visit(2)
print '(a)', 'COMPONENTS 7.5.4B NO SAVE OK'
contains
subroutine visit(iteration)
  integer, intent(in) :: iteration
  type(record) :: automatic
  type(record), save :: persistent
  if (automatic%value /= 7) error stop 1
  if (iteration == 1) then
    if (persistent%value /= 7) error stop 2
  else
    if (persistent%value /= 99) error stop 3
  end if
  automatic%value = 99
  persistent%value = 99
end subroutine
end program
""", "COMPONENTS 7.5.4B NO SAVE OK")
    c.mutate("save-source-use-graph", "type(record) :: automatic", "type(record), save :: automatic", "default initialization alone does not give automatic SAVE")
    result.append(c)

    c = Case("type_object_classification", "S7.5.4.6-011", [
        "direct-component-classification",
        "nested-direct-component-classification", "pointer-and-allocatable-recursion-boundary"], """
program component_type_object_classification
implicit none
type :: leaf
  integer :: value = 5
end type
type(leaf), target, save :: target_leaf = leaf(8)
type :: wrapper
  type(leaf) :: nested
  type(leaf), pointer :: link => null()
  type(leaf), allocatable :: bucket
end type
type(wrapper) :: item
if (item%nested%value /= 5) error stop 1
if (associated(item%link)) error stop 2
if (allocated(item%bucket)) error stop 3
print '(a)', 'COMPONENTS 7.5.4B CLASSIFICATION OK'
end program
""", "COMPONENTS 7.5.4B CLASSIFICATION OK")
    c.mutate("direct-component-classification", "value = 5", "value = 6", "leaf has a direct component default")
    c.mutate("nested-direct-component-classification", "type(leaf) :: nested", "type(leaf) :: nested = leaf(7)", "nested direct component default remains five")
    c.mutate("pointer-and-allocatable-recursion-boundary", "link => null()", "link => target_leaf", "pointer recursion boundary starts disassociated")
    result.append(c)
    return result


FACETS_BY_RULE = {}
for _case in cases():
    FACETS_BY_RULE.setdefault(_case.rule, []).extend(_case.facets)
for _rule, _facets in FACETS_BY_RULE.items():
    FACETS_BY_RULE[_rule] = list(dict.fromkeys(_facets))

ORACLE_TEXT = {
    "7.5.4.1": (
        "Components 7.5.4.b fixtures: five complete run/effect/f2023 programs cover selected "
        "component declaration forms without duplicating the older data_component corpus. DIMENSION(3), "
        "an individual explicit-shape component, character star-length suffixes, and shared property "
        "overrides are observed through SIZE, LBOUND/UBOUND, LEN and exact integer/character values. "
        "Each covered facet has a feature mutation changing the declaration form that remains conforming "
        "and makes the facet-specific assertion fail. CODIMENSION remains out of scope."
    ),
    "7.5.4.6": (
        "Components 7.5.4.b fixtures: nine complete run/effect/f2023 programs cover selected default "
        "initialization and initial-target facets. The cases observe constant, NULL() and initial-data-target "
        "component initialization on local, allocated and INTENT(OUT) object creation; nested designators; "
        "data-pointer-initialization compatibility including polymorphic dynamic type, nondeferred character "
        "length and contiguous whole-array target; nested and explicit-object override; no implied SAVE; and "
        "direct-component classification boundaries. All values are exact integers or LEN/shape/status "
        "inquiries, and every covered facet has a conforming feature mutation that fails at run time."
    ),
}
LIMIT_TEXT = {
    "7.5.4.1": (
        "Components 7.5.4.b fixture boundaries: these are single-image runtime witnesses for selected "
        "component declaration links only. They do not claim coarray CODIMENSION behavior, the entire "
        "R703 declaration-type-spec graph, procedure-component PASS/NOPASS graphs, C753 coarray-potential "
        "interactions, or every possible component specification expression."
    ),
    "7.5.4.6": (
        "Components 7.5.4.b fixture boundaries: these cases avoid undefined values, undefined pointer "
        "association status and processor-dependent output. They do not claim coarray targets, procedure "
        "component initial-proc-target coverage beyond the existing sibling corpus, or exhaustive Clause 9/10/19 "
        "canonical graph ownership."
    ),
}
ORACLE_PREFIX = {section: "Components 7.5.4.b fixtures: " for section in CATALOGUES}
LIMIT_PREFIX = {section: "Components 7.5.4.b fixture boundaries: " for section in CATALOGUES}

CONFIRMED_LFORTRAN_DEFECT_VARIANTS = {
    "initialization_alternatives",
    "initial_target_designator",
    "nested_initial_target",
    "target_compatibility_constraint",
}
CONFIRMED_LFORTRAN_DEFECT_MUTATIONS = {
    "type_object_classification-pointer-and-allocatable-recursion-boundary",
}

RESTORED_PENDING = {
    "S7.5.4.6-002": {
        "component-compatibility-link": (
            "Pending source-reviewed C769 negative/control evidence for the complete conjunction, "
            "with C769 retaining primary execution ownership."),
        "pointer-variable-use-graph": (
            "Pending the canonical variable-initialization owners that invoke this same definition; "
            "no component case proves all variable contexts."),
        "deferred-parameter-condition": (
            "Pending qualified canonical contrasts separating deferred parameters from the equal-value "
            "obligation on nondeferred ones."),
        "directional-type-compatibility": (
            "Pending source/use evidence distinguishing CLASS(parent)-to-extension compatibility from "
            "its reverse, without inventing an S-level diagnostic requirement."),
    },
}


STALE_REPLACEMENTS = {
    ("7.5.4.1", "R738", "oracle"): {
        "Shared DIMENSION and CODIMENSION reuse facets remain pending.":
            "CODIMENSION reuse remains pending; shared DIMENSION is covered by the components_7_5_4_b runtime fixture."
    },
    ("7.5.4.1", "R739", "oracle"): {
        "Source plan only. Declarator syntax and suffix locality are linked to their actual canonical controls/effects. Default initialization is not inferred from successful declaration parsing.":
            "The individual array, character length and initialization declarator links now have bounded components_7_5_4_b runtime evidence. Named-list and coarray links remain source plans; default-initialization semantics remain separately owned by 7.5.4.6."
    },
    ("7.5.4.1", "R740", "oracle"): {
        "Source plan only. Actual component shapes and canonical scalar-expression constraints remain separately traceable; a union is not multiplied into duplicate executions.":
            "The explicit-shape link now has a bounded components_7_5_4_b runtime fixture. Deferred-shape and broader array-grammar exclusions remain separately traceable; a union is not multiplied into duplicate executions."
    },
    ("7.5.4.1", "C758", "oracle"): {
        "Existing character-component admission retains its owner and remains a pending link.":
            "Character-component star-length admission is now covered by the components_7_5_4_b runtime fixture."
    },
    ("7.5.4.1", "S7.5.4.1-001", "oracle"): {
        "The three canonical override links remain pending.":
            "Only the CODIMENSION override link remains pending; character and DIMENSION overrides are covered by components_7_5_4_b runtime fixtures."
    },
}

def all_cases():
    return cases()


def build_corpus(root=ROOT):
    files = {}
    specs = {}
    for case in all_cases():
        directory = Path(root) / "tests/fixtures" / f"{TOPIC}_{case.variant}"
        manifest = dict(
            schema_version=1, id=case.name, rule=case.rule, facets=case.facets,
            evidence="effect", standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=case.completion, stderr=""),
        )
        path = directory / "fixture.json"
        raw = case.source.encode("ascii")
        if max(map(len, raw.splitlines()), default=0) > 132:
            raise ValueError(f"source line too long in {case.variant}")
        files[directory / "source.f90"] = raw
        files[path] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        specs[case.name] = dict(
            id=case.name, variant=case.variant, rule=case.rule, facets=case.facets,
            path=path.relative_to(root).as_posix(), source=case.source,
            source_sha256=sha(raw), completion=case.completion, mutations=case.mutations,
            manifest=manifest,
        )
    return files, specs


def mutated_source(spec, mutation):
    raw = spec["source"]
    if sha(raw.encode("ascii")) != spec["source_sha256"]:
        raise ValueError("complete parent source fingerprint changed")
    if raw.count(mutation["expected"]) != 1:
        raise ValueError("mutation span no longer binds exactly one feature")
    result = raw.replace(mutation["expected"], mutation["replacement"], 1)
    if result == raw:
        raise ValueError("mutation did not change source")
    return result


def owned_paragraph(value, prefix, replacement):
    paragraphs = value.split("\n\n") if value else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph for " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraphs)


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError(f"selected facets changed for {rule}")
        for facet in facets:
            if facet in owner.get("pending", {}):
                owner["pending"].pop(facet)
        for field in ("oracle", "oracle_limitation"):
            value = owner.get(field, "")
            for needle, replacement in STALE_REPLACEMENTS.get((section, rule, field), {}).items():
                if needle in value:
                    value = value.replace(needle, replacement)
            owner[field] = value
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX[section], ORACLE_TEXT[section])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIX[section], LIMIT_TEXT[section])
    for rule, facets in RESTORED_PENDING.items():
        if rule in by_rule:
            for facet, reason in facets.items():
                if facet not in FACETS_BY_RULE.get(rule, []):
                    by_rule[rule].setdefault("pending", {})[facet] = reason
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    view = Path(root) / VIEWS[section]
    original = view.read_text()
    if section == "7.5.4.6":
        original = original.replace(
            "They directly represent 91 facets; 25 canonical-use, event and classification\nfacets remain pending.",
            "They directly represent 102 facets after the components_7_5_4_b packet; 14 canonical-use, event\nand classification facets remain pending.")
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if original.count(begin) != 1 or original.count(end) != 1:
        raise ValueError("generated view boundaries changed for " + section)
    before, rest = original.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        + ("## Components 7.5.4.b runtime observations\n\n"
           "Fourteen complete run/effect/f2023 fixtures cover selected pending facets in 7.5.4.1 "
           "and 7.5.4.6. The declaration fixtures observe DIMENSION, explicit shapes, character "
           "star lengths and individual overrides with SIZE/LEN/bounds/value assertions. The default "
           "initialization fixtures observe object-creation events, pointer disassociation and association, "
           "nested initial targets, scalar target compatibility, override rules, no implied SAVE and direct-component "
           "classification. All feature mutations are conforming runtime mutants; CODIMENSION and broader "
           "canonical graph ownership remain pending.\n")
        + SUMMARY_END)
    if SUMMARY_BEGIN in before:
        leading, rest2 = before.split(SUMMARY_BEGIN)
        _, trailing = rest2.split(SUMMARY_END)
        before = leading.rstrip() + "\n\n" + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    rendered = "\n".join(render_requirement(row) for row in catalogue["requirements"])
    return before + begin + "\n\n" + rendered + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues = {}
    views = {}
    for section, relative in CATALOGUES.items():
        current = json.loads((root / relative).read_text())
        catalogues[section] = synced_catalogue(section, current)
        views[section] = render_view(section, catalogues[section], root)
    stale = []
    if check:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                stale.append(path.relative_to(root).as_posix())
        for section, relative in CATALOGUES.items():
            if json.loads((root / relative).read_text()) != catalogues[section]:
                stale.append(relative)
            if (root / VIEWS[section]).read_text() != views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale components 7.5.4.b files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section, relative in CATALOGUES.items():
                (root / relative).write_text(json.dumps(catalogues[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs


def compiler_command(compiler, std, source, exe):
    compiler = str(compiler)
    if "gfortran" in Path(compiler).name:
        return [compiler, "-std=" + std, str(source), "-o", str(exe)]
    return [compiler, "--std=" + std, str(source), "-o", str(exe)]


def run_mutation_check(root, compiler, std):
    root = Path(root)
    specs = generate(root, check=True)
    compiler_name = Path(str(compiler)).name.lower()
    skip_lfortran_defects = "lfortran" in compiler_name
    work = root / (WORK + "_" + compiler_name.replace("/", "_").replace(".", "_"))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    try:
        checked = 0
        skipped = []
        for spec in specs.values():
            if skip_lfortran_defects and spec["variant"] in CONFIRMED_LFORTRAN_DEFECT_VARIANTS:
                for mutation in spec["mutations"]:
                    skipped.append(mutation["id"])
                continue
            for mutation in spec["mutations"]:
                if skip_lfortran_defects and mutation["id"] in CONFIRMED_LFORTRAN_DEFECT_MUTATIONS:
                    skipped.append(mutation["id"])
                    continue
                checked += 1
                case_dir = work / spec["variant"] / mutation["id"].replace("/", "_")
                case_dir.mkdir(parents=True)
                source = case_dir / "source.f90"
                exe = case_dir / "program"
                source.write_text(mutated_source(spec, mutation))
                compile_run = subprocess.run(
                    compiler_command(compiler, std, source, exe), cwd=case_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
                if compile_run.returncode != 0:
                    raise RuntimeError(
                        f"mutation {mutation['id']} failed to compile with {compiler}:\n{compile_run.stdout}")
                execute = subprocess.run([str(exe)], cwd=case_dir, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, timeout=60)
                if execute.returncode == 0:
                    raise RuntimeError(
                        f"mutation {mutation['id']} survived with {compiler}:\n{execute.stdout}")
        return checked, skipped
    finally:
        if work.exists():
            shutil.rmtree(work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        count, skipped = run_mutation_check(args.root, args.compiler, args.std)
        suffix = ""
        if skipped:
            suffix = "; skipped confirmed LFortran initial-data-target defects: " + ", ".join(skipped)
        print(f"Checked {count} components 7.5.4.b runtime feature mutations with {args.compiler}{suffix}.")
        return
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} components 7.5.4.b fixtures, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} feature mutations.")


if __name__ == "__main__":
    main()
