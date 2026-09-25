#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 subclause 7.5.10 structure constructors."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.10"
CATALOGUE = "doc/catalogues/derived_types_7_5_10.json"
VIEW = "doc/fortran_2023_7_5_10.md"
SUMMARY_BEGIN = "<!-- BEGIN STRUCTURE CONSTRUCTOR EFFECT FIXTURES -->"
SUMMARY_END = "<!-- END STRUCTURE CONSTRUCTOR EFFECT FIXTURES -->"

VARIANTS = {
    "array_component_scalar": ("S7.5.10-001", "array-component-not-elemental-constructor"),
    "keyword_order": ("S7.5.10-002", "keyword-order-independent"),
    "numeric_conversion": ("S7.5.10-003", "numeric-conversion"),
    "scalar_array": ("S7.5.10-004", "scalar-to-ordinary-array"),
    "conforming_array": ("S7.5.10-004", "conforming-array-value"),
    "omitted_defaults": ("S7.5.10-005", "omitted-value-default"),
    "omitted_allocatables": ("S7.5.10-005", "omitted-allocatable-status"),
    "live_data_target": ("S7.5.10-007", "live-data-target-alias"),
    "pointer_source_bounds": ("S7.5.10-007", "pointer-source-association-and-bounds"),
    "known_disassociated_pointer": ("S7.5.10-007", "known-disassociated-pointer"),
    "contextual_mold_null": ("S7.5.10-007", "contextual-and-mold-null"),
    "no_mold_null_allocatable": ("S7.5.10-008", "no-mold-null-unallocated"),
    "typed_mold_null_allocatable": ("S7.5.10-008", "typed-mold-null-unallocated"),
    "allocated_char_source": ("S7.5.10-009", "allocated-source-deferred-length"),
    "ordinary_char_source": ("S7.5.10-009", "ordinary-character-deferred-length"),
}
FACETS_BY_RULE = {}
for rule, facet in VARIANTS.values():
    FACETS_BY_RULE.setdefault(rule, []).append(facet)
FACETS_BY_RULE = {key: tuple(value) for key, value in FACETS_BY_RULE.items()}

ORACLE_PREFIXES = {
    "S7.5.10-001": "S7.5.10-001 structure-constructor scalar value fixtures: ",
    "S7.5.10-002": "S7.5.10-002 structure-constructor component mapping fixtures: ",
    "S7.5.10-003": "S7.5.10-003 structure-constructor ordinary conversion fixture: ",
    "S7.5.10-004": "S7.5.10-004 structure-constructor ordinary array fixtures: ",
    "S7.5.10-005": "S7.5.10-005 structure-constructor omitted component fixtures: ",
    "S7.5.10-007": "S7.5.10-007 structure-constructor pointer component fixtures: ",
    "S7.5.10-008": "S7.5.10-008 structure-constructor allocatable NULL fixtures: ",
    "S7.5.10-009": "S7.5.10-009 structure-constructor allocatable character fixtures: ",
}
LIMIT_PREFIXES = {rule: prefix.replace("fixtures: ", "boundaries: ").replace("fixture: ", "boundaries: ")
                  for rule, prefix in ORACLE_PREFIXES.items()}
ORACLES = {
    "S7.5.10-001": ORACLE_PREFIXES["S7.5.10-001"] + (
        "one complete run/effect/f2023 program passes a scalar structure constructor with an ordinary rank-one "
        "INTEGER component to a typed scalar observer. The component source is a separately assigned array with "
        "hand literals 11, 13 and 17, and the observer checks exactly one scalar record and each named component "
        "element. This observes that the constructor produces a scalar value containing an array component, not an "
        "array of three records or an elemental same-named factory. A load-bearing default component -9051, two "
        "positional identity components 101 and 103, and mutation probes for default changes, component reordering "
        "and swapped positional values accompany the facet-specific source-value probe."
    ),
    "S7.5.10-002": ORACLE_PREFIXES["S7.5.10-002"] + (
        "one complete run/effect/f2023 program constructs a record with right=13 before left=11 after two "
        "positional controls. The observer checks left and right by name against distinct literals, plus the "
        "default and positional controls, so declaration-order, source-order and set-only implementations are "
        "distinguished."
    ),
    "S7.5.10-003": ORACLE_PREFIXES["S7.5.10-003"] + (
        "one complete run/effect/f2023 program supplies a separately defined default REAL source 4.0 to an "
        "INTEGER scalar component and observes integer value 4 through a typed observer. The oracle is the hand "
        "application of p2's intrinsic-assignment conversion rule, not a representation, kind code or compiler "
        "consensus."
    ),
    "S7.5.10-004": ORACLE_PREFIXES["S7.5.10-004"] + (
        "two complete run/effect/f2023 programs cover ordinary nonpointer nonallocatable array components. The "
        "scalar-expansion case supplies a separately assigned scalar 17 to INTEGER values(-1:1) and checks bounds "
        "-1:1 plus all three elements. The conforming-array case supplies a separately populated rank-one source "
        "11,13,17 and checks the component's declared bounds and each element by name, proving shape-conforming "
        "value assignment rather than storage remapping or pointer-rank behavior."
    ),
    "S7.5.10-005": ORACLE_PREFIXES["S7.5.10-005"] + (
        "two complete run/effect/f2023 programs observe omitted components. The default case constructs one value "
        "with both defaulted integer components omitted and a second with right=29, requiring left/right pairs "
        "11/13 and 11/29. The allocatable case omits scalar and rank-one allocatable components and observes only "
        "their allocation status as unallocated, never bounds or values."
    ),
    "S7.5.10-007": ORACLE_PREFIXES["S7.5.10-007"] + (
        "four complete run/effect/f2023 programs observe pointer component association. A live local TARGET datum "
        "is associated only during the observer call and yields value 17. A rank-one source pointer with remapped "
        "bounds 5:7 supplies copied association, bounds and values 11,13,17. A known disassociated source pointer "
        "yields a disassociated component. NULL() and NULL(MOLD=typed_pointer) produce disassociated compatible "
        "pointer components. All use ASSOCIATED/LBOUND/UBOUND/value inquiries on defined valid entities only, never "
        "addresses, TRANSFER, LOC or storage offsets."
    ),
    "S7.5.10-008": ORACLE_PREFIXES["S7.5.10-008"] + (
        "two complete run/effect/f2023 programs observe p6's intrinsic NULL branch for allocatable components. "
        "The no-MOLD case supplies NULL() for scalar and rank-one allocatable components; the typed-MOLD case uses "
        "NULL(MOLD=mold) with a declared unallocated same-rank allocatable mold. The only observed component state "
        "is ALLOCATED false, with no bounds, length or value inquiry."
    ),
    "S7.5.10-009": ORACLE_PREFIXES["S7.5.10-009"] + (
        "two complete run/effect/f2023 programs observe deferred-length allocatable CHARACTER components. The "
        "allocated-entity source case allocates CHARACTER(LEN=3) source and assigns 'QRS'; the ordinary-expression "
        "case uses a nonallocatable CHARACTER(LEN=3) variable 'LMN'. In both, the constructed component is first "
        "required allocated, then LEN 3 and the exact three nonblank characters are checked."
    ),
}
LIMITATIONS = {
    "S7.5.10-001": LIMIT_PREFIXES["S7.5.10-001"] + (
        "only array-component-not-elemental-constructor is represented. Scalar-value and parameter-specifier "
        "source-use remain pending because this packet does not install finite reuse links or a PDT parameter test."
    ),
    "S7.5.10-002": LIMIT_PREFIXES["S7.5.10-002"] + (
        "only keyword-order-independent is represented. Existing positional, inherited and parent-keyword cases "
        "remain at their original owners until a source-use graph is reviewed."
    ),
    "S7.5.10-003": LIMIT_PREFIXES["S7.5.10-003"] + (
        "only numeric-conversion is represented. Character padding/truncation, type-parameter conformance, defined "
        "assignment contrasts and outer-assignment ownership remain pending. The real source is the exact small "
        "model value 4.0 solely to exercise intrinsic conversion to INTEGER 4."
    ),
    "S7.5.10-004": LIMIT_PREFIXES["S7.5.10-004"] + (
        "only scalar-to-ordinary-array and conforming-array-value are represented. Nonconforming contrasts and "
        "elemental/generic source-use boundaries remain pending. The fixtures do not claim pointer rank, allocatable "
        "rank, storage sequence or same-size rank remapping."
    ),
    "S7.5.10-005": LIMIT_PREFIXES["S7.5.10-005"] + (
        "only omitted-value-default and omitted-allocatable-status are represented. Pointer defaults, private "
        "omission and default-vs-explicit source-use remain pending. Unallocated components are queried only for "
        "allocation status."
    ),
    "S7.5.10-007": LIMIT_PREFIXES["S7.5.10-007"] + (
        "only live-data-target-alias, pointer-source-association-and-bounds, known-disassociated-pointer and "
        "contextual-and-mold-null are represented. Procedure-target calls and canonical target/interface/lifetime "
        "source-use graphs remain pending. No dangling target or undefined pointer status is read."
    ),
    "S7.5.10-008": LIMIT_PREFIXES["S7.5.10-008"] + (
        "only no-mold-null-unallocated and typed-mold-null-unallocated are represented. Same-rank source-use, rank "
        "mismatch contrasts and NULL identity/context source-use remain pending."
    ),
    "S7.5.10-009": LIMIT_PREFIXES["S7.5.10-009"] + (
        "only allocated-source-deferred-length and ordinary-character-deferred-length are represented. Allocation "
        "status matrices for arrays, polymorphism, nonpolymorphic conversion, expression bounds, zero extent and "
        "assignment-boundary source-use remain pending. Character comparisons assert LEN explicitly and use nonblank "
        "three-character values."
    ),
}
COMPLETIONS = {name: "STRUCTURE CONSTRUCTOR " + name.upper().replace("_", " ") + " OK\n" for name in VARIANTS}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown structure-constructor variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__structure_constructor_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facet = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.oracle_mutations = []
        self.input_mutations = []
        self.feature_mutations = []
        self.reverse_mutations = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def guard(self, name, expression, expected, replacement=None, *, category="value", counter="checks", indent="  "):
        expected = str(expected)
        if replacement is None:
            replacement = str(int(expected) + 1) if re.fullmatch(r"-?\d+", expected) else expected + "X"
        replacement = str(replacement)
        block_start = len(self.text)
        prefix = indent + f"if ({expression} /= "
        start = block_start + len(prefix)
        token = f"DTSC:{self.variant}:{name}"
        self.add(prefix + expected + ") then\n" + indent + f"  write(*,'(a)') '{token}'\n"
                 + indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")
        guard = dict(id=name, kind="guard", category=category, expression=expression, expected=expected,
                     replacement=replacement, span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
                     counter=counter, failure_token=token, failure_stdout=token + "\n",
                     mutation="oracle-literal", block_span=[block_start, len(self.text)])
        self.guards.append(guard)
        self.oracle_mutations.append(_single_mutation(guard, "oracle", replacement))
        if counter:
            self.observations.append(guard)
        return guard

    def guard_true(self, name, expression, replacement_expression, *, category="state", counter="checks", indent="  "):
        block_start = len(self.text)
        prefix = indent + "if (.not. ("
        start = block_start + len(prefix)
        token = f"DTSC:{self.variant}:{name}"
        self.add(prefix + expression + ")) then\n" + indent + f"  write(*,'(a)') '{token}'\n"
                 + indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")
        guard = dict(id=name, kind="guard", category=category, expression=expression, expected=expression,
                     replacement=replacement_expression, span=[start, start + len(expression)],
                     line=self.text[:start].count("\n") + 1, counter=counter, failure_token=token,
                     failure_stdout=token + "\n", mutation="oracle-expression", block_span=[block_start, len(self.text)])
        self.guards.append(guard)
        self.oracle_mutations.append(_single_mutation(guard, "oracle", replacement_expression))
        if counter:
            self.observations.append(guard)
        return guard

    def finish(self):
        self.guard("check-total", "checks", "9", "8",
                   category="completion", counter=None)
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        self.add(prefix + literal + "'\n")
        guard = dict(id="completion-output", kind="output", category="completion", expected=literal,
                     replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
                     line=self.text[:start].count("\n") + 1, counter=None, failure_stdout="",
                     mutation="completion-literal")
        self.guards.append(guard)
        self.oracle_mutations.append(_single_mutation(guard, "oracle", guard["replacement"]))


def _single_mutation(site, group, replacement):
    start, end = site["span"]
    return dict(id=site["id"], group=group, kind=site.get("kind", group), category=site.get("category", group),
                mutation=site.get("mutation", group), edits=[dict(span=[start, end], expected=site["expected"],
                replacement=replacement)], failure_stdout=site.get("failure_stdout", ""))


def find_edit(source, expected, replacement, *, occurrence=1):
    matches = [m for m in re.finditer(re.escape(expected), source)]
    if len(matches) < occurrence:
        raise ValueError(f"{expected!r} has only {len(matches)} matches")
    match = matches[occurrence - 1]
    return dict(span=[match.start(), match.end()], expected=expected, replacement=replacement)


def add_named_mutation(collection, id_, source, edits, *, group="input", mutation="input-source"):
    if isinstance(edits, dict):
        edits = [edits]
    collection.append(dict(id=id_, group=group, kind=group, category=group, mutation=mutation, edits=edits,
                           failure_stdout=""))


def add_common_feature_mutations(p, constructor_prefix="record"):
    source = p.text
    add_named_mutation(p.feature_mutations, "change-default-stamp", source,
                       find_edit(source, "integer :: stamp = -9051", "integer :: stamp = -9052"),
                       group="feature", mutation="default-initialization-change")
    add_named_mutation(p.feature_mutations, "reorder-positional-components", source,
                       find_edit(source, "integer :: lead\n    integer :: swapped",
                                 "integer :: swapped\n    integer :: lead"),
                       group="feature", mutation="component-definition-reorder")
    add_named_mutation(p.feature_mutations, "swap-positional-control-values", source,
                       find_edit(source, f"{constructor_prefix}(101, 103", f"{constructor_prefix}(103, 101"),
                       group="feature", mutation="component-value-swap")
    stamp_guard = next(g for g in p.guards if g["id"] == "default-stamp")
    default_edit = find_edit(source, "integer :: stamp = -9051", "integer :: stamp = -9052")
    start, end = stamp_guard["span"]
    p.reverse_mutations.append(dict(
        id="reverse-default-stamp", group="reverse", kind="reverse", category="reverse",
        mutation="default-initialization-reverse", edits=[default_edit,
            dict(span=[start, end], expected="-9051", replacement="-9052")], failure_stdout=""))


def header(p):
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")
    p.add("! Expected component values are hand-derived from Fortran 2023 7.5.10 p1-p8.\n")
    p.add("! Each source has a nonzero default component plus positional controls for feature mutation.\n")


def add_standard_record_type(p, extra):
    p.add("  type :: record\n    integer :: lead\n    integer :: swapped\n    integer :: stamp = -9051\n")
    p.add(extra)
    p.add("  end type record\n")


def common_observer_checks(p, obj="obj", indent="    "):
    p.guard("lead-component", f"{obj}%lead", 101, 103, category="control", indent=indent)
    p.guard("swapped-component", f"{obj}%swapped", 103, 101, category="control", indent=indent)
    p.guard("default-stamp", f"{obj}%stamp", -9051, -9052, category="default", indent=indent)


def program(variant):
    p = Program(variant)
    header(p)
    p.add(f"program structure_constructor_{variant}_effect\n  implicit none\n  integer :: checks\n")
    if variant == "array_component_scalar":
        add_standard_record_type(p, "    integer :: values(3)\n")
        p.add("  integer :: source(3)\n  checks=0\n  source(1)=11\n  source(2)=13\n  source(3)=17\n")
        p.add("  call observe(record(101, 103, values=source))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        for index, expected in enumerate((11, 13, 17), 1):
            p.guard(f"array-value-{index}", f"obj%values({index})", expected, expected + 1, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_array_component_scalar_effect\n")
        add_named_mutation(p.input_mutations, "array-source-middle", p.text,
                           find_edit(p.text, "source(2)=13", "source(2)=31"))
    elif variant == "keyword_order":
        add_standard_record_type(p, "    integer :: left\n    integer :: right\n")
        p.add("  checks=0\n  call observe(record(101, 103, right=13, left=11))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard("left-by-name", "obj%left", 11, 13, indent="    ")
        p.guard("right-by-name", "obj%right", 13, 11, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_keyword_order_effect\n")
        add_named_mutation(p.input_mutations, "swap-keyword-values", p.text,
                           find_edit(p.text, "right=13, left=11", "right=11, left=13"))
    elif variant == "numeric_conversion":
        add_standard_record_type(p, "    integer :: value\n")
        p.add("  real :: source\n  checks=0\n  source=4.0\n  call observe(record(101, 103, value=source))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard("converted-integer", "obj%value", 4, 5, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_numeric_conversion_effect\n")
        add_named_mutation(p.input_mutations, "real-source-value", p.text,
                           find_edit(p.text, "source=4.0", "source=5.0"))
    elif variant == "scalar_array":
        add_standard_record_type(p, "    integer :: values(-1:1)\n")
        p.add("  integer :: scalar\n  checks=0\n  scalar=17\n  call observe(record(101, 103, values=scalar))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard("array-lbound", "lbound(obj%values,1)", -1, -2, category="bounds", indent="    ")
        p.guard("array-ubound", "ubound(obj%values,1)", 1, 2, category="bounds", indent="    ")
        for index in (-1, 0, 1):
            p.guard(f"scalar-expanded-{index}", f"obj%values({index})", 17, 18, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_scalar_array_effect\n")
        add_named_mutation(p.input_mutations, "scalar-source-value", p.text,
                           find_edit(p.text, "scalar=17", "scalar=18"))
    elif variant == "conforming_array":
        add_standard_record_type(p, "    integer :: values(-1:1)\n")
        p.add("  integer :: source(3)\n  checks=0\n  source(1)=11\n  source(2)=13\n  source(3)=17\n")
        p.add("  call observe(record(101, 103, values=source))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard("array-lbound", "lbound(obj%values,1)", -1, -2, category="bounds", indent="    ")
        p.guard("array-ubound", "ubound(obj%values,1)", 1, 2, category="bounds", indent="    ")
        for index, expected in zip((-1, 0, 1), (11, 13, 17)):
            p.guard(f"conforming-value-{index}", f"obj%values({index})", expected, expected + 1, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_conforming_array_effect\n")
        add_named_mutation(p.input_mutations, "array-source-middle", p.text,
                           find_edit(p.text, "source(2)=13", "source(2)=31"))
    elif variant == "omitted_defaults":
        add_standard_record_type(p, "    integer :: left = 11\n    integer :: right = 13\n")
        p.add("  checks=0\n  call observe_default(record(101, 103))\n  call observe_override(record(101, 103, right=29))\n")
        p.finish()
        p.add("contains\n  subroutine observe_default(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard("default-left", "obj%left", 11, 12, indent="    ")
        p.guard("default-right", "obj%right", 13, 14, indent="    ")
        p.add("  end subroutine observe_default\n  subroutine observe_override(obj)\n    type(record), intent(in) :: obj\n")
        p.guard("override-left-default", "obj%left", 11, 12, indent="    ")
        p.guard("override-right", "obj%right", 29, 30, indent="    ")
        p.add("  end subroutine observe_override\nend program structure_constructor_omitted_defaults_effect\n")
        add_named_mutation(p.input_mutations, "left-default-value", p.text,
                           find_edit(p.text, "integer :: left = 11", "integer :: left = 12"))
        add_named_mutation(p.input_mutations, "right-override-value", p.text,
                           find_edit(p.text, "right=29", "right=30"))
    elif variant == "omitted_allocatables":
        add_standard_record_type(p, "    integer, allocatable :: scalar\n    integer, allocatable :: vector(:)\n")
        p.add("  checks=0\n  call observe(record(101, 103))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("scalar-unallocated", ".not. allocated(obj%scalar)", "allocated(obj%scalar)", indent="    ")
        p.guard_true("vector-unallocated", ".not. allocated(obj%vector)", "allocated(obj%vector)", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_omitted_allocatables_effect\n")
        add_named_mutation(p.input_mutations, "supply-allocatable-components", p.text,
                           find_edit(p.text, "record(101, 103)", "record(101, 103, scalar=21, vector=[11,13,17]"))
    elif variant == "live_data_target":
        add_standard_record_type(p, "    integer, pointer :: p\n")
        p.add("  checks=0\n  call worker()\n")
        p.finish()
        p.add("contains\n  subroutine worker()\n    integer, target :: datum\n    datum=17\n")
        p.add("    call observe(record(101, 103, p=datum), datum)\n  end subroutine worker\n")
        p.add("  subroutine observe(obj, datum)\n    type(record), intent(in) :: obj\n    integer, target, intent(in) :: datum\n")
        common_observer_checks(p)
        p.guard_true("associated-with-live-target", "associated(obj%p, datum)", ".not. associated(obj%p, datum)", indent="    ")
        p.guard("target-value-through-pointer", "obj%p", 17, 18, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_live_data_target_effect\n")
        add_named_mutation(p.input_mutations, "target-value", p.text, find_edit(p.text, "datum=17", "datum=18"))
    elif variant == "pointer_source_bounds":
        add_standard_record_type(p, "    integer, pointer :: p(:)\n")
        p.add("  integer, target :: target(3)\n  integer, pointer :: source(:)\n  checks=0\n")
        p.add("  target(1)=11\n  target(2)=13\n  target(3)=17\n  source(5:7) => target\n")
        p.add("  call observe(record(101, 103, p=source), source)\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj, source)\n    type(record), intent(in) :: obj\n    integer, pointer, intent(in) :: source(:)\n")
        common_observer_checks(p)
        p.guard_true("associated-with-source-pointer", "associated(obj%p, source)", ".not. associated(obj%p, source)", indent="    ")
        p.guard("pointer-lbound", "lbound(obj%p,1)", 5, 6, category="bounds", indent="    ")
        p.guard("pointer-ubound", "ubound(obj%p,1)", 7, 8, category="bounds", indent="    ")
        for index, expected in zip((5, 6, 7), (11, 13, 17)):
            p.guard(f"pointer-value-{index}", f"obj%p({index})", expected, expected + 1, indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_pointer_source_bounds_effect\n")
        add_named_mutation(p.input_mutations, "source-pointer-bound", p.text,
                           find_edit(p.text, "source(5:7) => target", "source(6:8) => target"))
        add_named_mutation(p.input_mutations, "target-middle-value", p.text,
                           find_edit(p.text, "target(2)=13", "target(2)=31"))
    elif variant == "known_disassociated_pointer":
        add_standard_record_type(p, "    integer, pointer :: p\n")
        p.add("  integer, target :: target\n  integer, pointer :: source\n  checks=0\n  target=17\n  source => null()\n")
        p.add("  call observe(record(101, 103, p=source))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("component-disassociated", ".not. associated(obj%p)", "associated(obj%p)", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_known_disassociated_pointer_effect\n")
        add_named_mutation(p.input_mutations, "associate-source-pointer", p.text,
                           find_edit(p.text, "source => null()", "source => target"))
    elif variant == "contextual_mold_null":
        add_standard_record_type(p, "    integer, pointer :: p(:)\n    integer, pointer :: q(:)\n")
        p.add("  integer, target :: target(3)\n  integer, pointer :: mold(:)\n  checks=0\n")
        p.add("  target=[11,13,17]\n  mold => null()\n  call observe(record(101, 103, p=null(), q=null(mold=mold)))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("null-component-disassociated", ".not. associated(obj%p)", "associated(obj%p)", indent="    ")
        p.guard_true("mold-null-component-disassociated", ".not. associated(obj%q)", "associated(obj%q)", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_contextual_mold_null_effect\n")
        add_named_mutation(p.input_mutations, "replace-null-with-target", p.text,
                           find_edit(p.text, "p=null()", "p=target"))
        add_named_mutation(p.input_mutations, "replace-mold-null-with-target", p.text,
                           find_edit(p.text, "q=null(mold=mold)", "q=target"))
    elif variant == "no_mold_null_allocatable":
        add_standard_record_type(p, "    integer, allocatable :: scalar\n    integer, allocatable :: vector(:)\n")
        p.add("  checks=0\n  call observe(record(101, 103, scalar=null(), vector=null()))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("scalar-null-unallocated", ".not. allocated(obj%scalar)", "allocated(obj%scalar)", indent="    ")
        p.guard_true("vector-null-unallocated", ".not. allocated(obj%vector)", "allocated(obj%vector)", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_no_mold_null_allocatable_effect\n")
        add_named_mutation(p.input_mutations, "replace-null-with-values", p.text,
                           find_edit(p.text, "scalar=null(), vector=null()", "scalar=21, vector=[11,13,17]"))
    elif variant == "typed_mold_null_allocatable":
        add_standard_record_type(p, "    integer, allocatable :: vector(:)\n")
        p.add("  integer, allocatable :: mold(:)\n  checks=0\n  call observe(record(101, 103, vector=null(mold=mold)))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("typed-mold-null-unallocated", ".not. allocated(obj%vector)", "allocated(obj%vector)", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_typed_mold_null_allocatable_effect\n")
        add_named_mutation(p.input_mutations, "replace-typed-null-with-values", p.text,
                           find_edit(p.text, "vector=null(mold=mold)", "vector=[11,13,17]"))
    elif variant == "allocated_char_source":
        add_standard_record_type(p, "    character(:), allocatable :: text\n")
        p.add("  character(:), allocatable :: source\n  checks=0\n  allocate(character(len=3) :: source)\n")
        p.add("  source='QRS'\n  call observe(record(101, 103, text=source))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("text-allocated", "allocated(obj%text)", ".not. allocated(obj%text)", indent="    ")
        p.guard("text-len", "len(obj%text)", 3, 4, category="length", indent="    ")
        p.guard("text-value", "obj%text", "'QRS'", "'QRT'", category="value", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_allocated_char_source_effect\n")
        add_named_mutation(p.input_mutations, "allocated-character-value", p.text,
                           find_edit(p.text, "source='QRS'", "source='QRT'"))
    elif variant == "ordinary_char_source":
        add_standard_record_type(p, "    character(:), allocatable :: text\n")
        p.add("  character(len=3) :: source\n  checks=0\n  source='LMN'\n  call observe(record(101, 103, text=source))\n")
        p.finish()
        p.add("contains\n  subroutine observe(obj)\n    type(record), intent(in) :: obj\n")
        common_observer_checks(p)
        p.guard_true("text-allocated", "allocated(obj%text)", ".not. allocated(obj%text)", indent="    ")
        p.guard("text-len", "len(obj%text)", 3, 4, category="length", indent="    ")
        p.guard("text-value", "obj%text", "'LMN'", "'LMP'", category="value", indent="    ")
        p.add("  end subroutine observe\nend program structure_constructor_ordinary_char_source_effect\n")
        add_named_mutation(p.input_mutations, "ordinary-character-value", p.text,
                           find_edit(p.text, "source='LMN'", "source='LMP'"))
    else:
        raise ValueError("unknown variant")
    add_common_feature_mutations(p)
    return finalize_spec(p)


def apply_edits(raw, edits):
    result = raw
    for edit in sorted(edits, key=lambda e: e["span"][0], reverse=True):
        start, end = edit["span"]
        if result[start:end].decode("ascii") != edit["expected"]:
            raise ValueError("mutation edit does not bind the complete parent")
        result = result[:start] + edit["replacement"].encode("ascii") + result[end:]
    return result


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    return apply_edits(raw, mutation["edits"])


def finalize_spec(p):
    total = str(len(p.observations))
    total_replacement = str(len(p.observations) + 1)
    total_guard = next((g for g in p.guards if g["id"] == "check-total"), None)
    if total_guard is not None:
        start, end = total_guard["span"]
        if p.text[start:end] != "9":
            raise ValueError(f"{p.variant}: check-total placeholder changed")
        p.text = p.text[:start] + total + p.text[end:]
        total_guard["expected"] = total
        total_guard["replacement"] = total_replacement
        for mutation in p.oracle_mutations:
            if mutation["id"] == "check-total":
                mutation["edits"][0]["expected"] = total
                mutation["edits"][0]["replacement"] = total_replacement
                break
    raw = p.text.encode("ascii")
    if max(map(len, p.text.splitlines())) > 132:
        raise ValueError(f"{p.variant}: source line too long")
    all_mutations = p.oracle_mutations + p.input_mutations + p.feature_mutations + p.reverse_mutations
    hashes = set()
    for mutation in all_mutations:
        mutant = apply_edits(raw, mutation["edits"])
        digest = sha(mutant)
        if mutation["group"] != "reverse" and digest in hashes:
            raise ValueError(f"{p.variant}: duplicate mutation {mutation['id']}")
        hashes.add(digest)
    sentinels = ["101", "103", "-9051"]
    ignored = "typical zero/default fill would not supply lead 101, swapped 103 or stamp -9051; named guards reject it"
    return dict(
        id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=[p.facet], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[p.variant],
        guards=p.guards, oracle_mutations=p.oracle_mutations, input_mutations=p.input_mutations,
        feature_mutations=p.feature_mutations, reverse_mutations=p.reverse_mutations,
        observations=p.observations, sentinels=sentinels, ignored_feature=ignored,
        expected_counts=dict(checks=len(p.observations)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("structure_constructor_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect", standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    import generate_constructor_declaration_fixtures as declaration_generated
    import generate_structure_constructor_7_5_10_b_fixtures as batch317_generated
    represented_by_rule = {}
    for rule, facets in declaration_generated.ELIGIBLE.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
    for rule, facets in declaration_generated.EXISTING.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
    for rule, facets in batch317_generated.FACETS_BY_RULE.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
    for rule, facets in FACETS_BY_RULE.items():
        represented_by_rule.setdefault(rule, set()).update(facets)
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("selected structure-constructor facets changed")
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    for owner in updated["requirements"]:
        expected = set(owner["facets"]) - represented_by_rule.get(owner["id"], set())
        if set(owner.get("pending", {})) != expected:
            raise ValueError("structure-constructor pending partition mismatch: " + owner["id"])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the 7.5.10 generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = re.sub(r"\*\*Catalogue source review: [^.]+\.\*\*",
                    f"**Catalogue source review: {catalogue_review_status(catalogue)}.**", before, count=1)
    before = before.replace(
        "Together with the **four unchanged C7107 cases**, **22 of98 facets are represented; 76 remain pending**.",
        "Together with the **four unchanged C7107 cases**, **37 of98 facets are represented; 61 remain pending**.")
    before = before.replace(
        "No runtime, source-contrast, profile, C companion, coarray or diagnostic policy\nis implemented by these fixtures.",
        "Selected runtime constructor effects are now implemented by the generated fixtures below. No new\nsource-contrast, profile, C companion, coarray or diagnostic policy is implemented here.")
    before = before.replace("Remaining original plans below stay pending in full.",
                            "Unselected original plans below stay pending in full.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Structure constructor runtime observations\n\n"
        "Fifteen complete run/effect/f2023 programs discharge selected 7.5.10 effect facets. "
        "Every program uses a scalar typed observer, two positional identity components (101 and 103), "
        "and an omitted default-initialized component with sentinel -9051 before checking the facet-specific "
        "component by name. No fixture uses TRANSFER, LOC, C_LOC, EQUIVALENCE, COMMON, storage offsets or "
        "address comparison.\n\n"
        "Mutation metadata covers every oracle literal/expression/completion, every facet input value, and "
        "three feature-level mutations in each program: default-initialization change, component-definition "
        "reorder, and positional component-value swap. A reverse default-initialization mutation pairs the "
        "changed default with the changed oracle to prove the -9051 sentinel is load-bearing. Character cases "
        "assert LEN explicitly and use nonblank three-character values.\n\n"
        "The remaining source-use, diagnostic, polymorphic, procedure-pointer, expression-bound, zero-extent "
        "and assignment-boundary plans stay pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the structure-constructor summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    marker = "## Complete finite pending plans\n"
    repro = "## Reproduction and separate gates"
    if marker in after and repro in after:
        prefix, rest_after = after.split(marker, 1)
        _, suffix = rest_after.split(repro, 1)
        appendix = (marker + "\n"
            "The following original plan text is retained verbatim as plan metadata. "
            "Authorship or a prerequisite observation does not implement a graph or policy.\n\n")
        for requirement in catalogue["requirements"]:
            if requirement.get("pending"):
                appendix += f"### Pending {requirement['id']}\n\n"
                for facet, plan in requirement["pending"].items():
                    appendix += f"* **`{facet}`** - {plan}\n"
                appendix += "\n"
        after = prefix + appendix + repro + suffix
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


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
            raise ValueError("stale structure-constructor fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} structure-constructor cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['oracle_mutations']) for row in specs.values())} oracle, "
          f"{sum(len(row['input_mutations']) for row in specs.values())} input, "
          f"{sum(len(row['feature_mutations']) for row in specs.values())} feature and "
          f"{sum(len(row['reverse_mutations']) for row in specs.values())} reverse mutations.")


if __name__ == "__main__":
    main()
