#!/usr/bin/env python3
"""Generate finite component initialization, order and accessibility witnesses."""
import argparse
import importlib.util
import json
from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "parameter_fixture_helpers", ROOT / "tools/generate_derived_parameter_fixtures.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
SECTIONS = ("7.5.4.6", "7.5.4.7", "7.5.4.8")


def source(text):
    return textwrap.dedent(text).strip() + "\n"


def definition(component, prefix="", header="record"):
    return ("module component_definition\nimplicit none\n" + prefix
            + "type :: " + header + "\n" + component + "\nend type\nend module\n")


def program(declarations, checks, prefix="", suffix=""):
    return ("program component_witness\nimplicit none\n" + prefix
            + declarations + "\n" + checks + "\n" + suffix + "end program\n")


class Corpus(BASE.Corpus):
    def __init__(self):
        super().__init__(namespace="initialization", root=ROOT)
        self.repairs = []

    def pair(self, rule, variant, facets, bad, wrong, repaired, location, messages, **kwargs):
        super().pair(rule, variant, facets, bad, wrong, repaired, location, messages, **kwargs)
        self.repairs.append(dict(
            invalid=f"{rule}_invalid__initialization_{variant}",
            valid=f"{rule}_valid__initialization_{variant}_repair",
            file="source.f90", wrong=wrong, repaired=repaired))

    def run(self, rule, variant, facets, body, evidence="effect", requires=()):
        super().run(rule, "initialization_" + variant, facets, body, evidence, requires)

    def multi(self, rule, variant, facets, inputs, phase="run", diagnostic=None,
              evidence="effect"):
        kind = "invalid" if diagnostic else "valid"
        name = rule.replace(".", "_").replace("-", "_") + "_" + kind + "__initialization_" + variant
        folder = "tests/fixtures/component_initialization_" + name.lower()
        builds = [dict(id=Path(filename).stem, source=filename, language="fortran",
                       form="free", output=Path(filename).stem + ".o") for filename in inputs]
        expect = dict(phase=phase, outcome="diagnose" if diagnostic else "success")
        if phase == "compile":
            expect["step"] = builds[-1]["id"]
        else:
            expect["exit_code"] = 0
        if diagnostic:
            expect["diagnostic"] = diagnostic
        manifest = dict(schema_version=1, id=name, rule=rule, facets=facets,
                        standard="f2023", evidence=evidence, files=list(inputs),
                        build=builds, expect=expect)
        if phase == "run":
            manifest["link"] = dict(objects=[step["output"] for step in builds], output="program")
        for filename, content in inputs.items():
            self.put(folder + "/" + filename, source(content))
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, facets=facets, kind=kind, phase=phase,
                               path=folder + "/fixture.json")
        return name


def grammar_cases(c):
    for variant, facet, component, prefix in (
        ("scalar", "scalar-constant-value", "integer :: value = 3", ""),
        ("array", "array-constant-value", "integer :: values(2) = [2,3]", ""),
        ("null", "null-initializer", "integer, pointer :: alias => null()", ""),
        ("target", "initial-data-target", "integer, pointer :: alias => target",
         "integer, target, save :: target = 7\n"),
    ):
        c.compile("R743", variant, [facet], definition(component, prefix))
    for variant, facet, component, wrong, repair in (
        ("missing_value", "missing-value-operand", "integer :: value =", "value =", "value = 3"),
        ("missing_pointer", "missing-pointer-operand", "integer, pointer :: alias =>",
         "alias =>", "alias => null()"),
    ):
        messages = (["Missing initializer for component 'value'", "Expected an initialization expression"]
                    if variant == "missing_value" else
                    ["Missing pointer initializer for component 'alias'",
                     "Expected pointer initialization expression"])
        c.pair("R743", variant, [facet], definition(component), wrong, repair, component, messages)

    prefix = ("integer, target, save :: scalar = 7\n"
              "integer, target, save :: values(4) = [2,3,5,7]\n"
              "character(4), target, save :: text = 'abcd'\n")
    for variant, facet, component in (
        ("name", "named-variable-designator", "integer, pointer :: alias => scalar"),
        ("element", "array-element-designator", "integer, pointer :: alias => values(2)"),
        ("section", "array-section-designator", "integer, pointer :: alias(:) => values(1:4:2)"),
        ("substring", "substring-designator", "character(2), pointer :: alias => text(2:3)"),
    ):
        c.compile("R744", variant, [facet], definition(component, prefix))
    component = "integer, pointer :: alias => scalar+0"
    c.pair("R744", "arithmetic", ["arithmetic-expression-excluded"], definition(component, prefix),
           "scalar+0", "scalar", component,
           ["Initial data target for component 'alias' must be a designator",
            "Arithmetic expression is not an initial data target",
            "Pointer initialization target must be a designator"])

    c.compile("C766", "separator", ["initialized-with-separator"], definition("integer :: value = 3"))
    c.compile("C766", "no_initialization", ["uninitialized-without-separator"],
              definition("integer value"))
    component = "integer value = 3"
    c.pair("C766", "missing_separator", ["missing-separator"], definition(component),
           component, "integer :: value = 3", component,
           ["Initialization of component 'value' requires '::'",
            "Initialization in a component declaration requires a double colon",
            "Invalid syntax for variable initialization (try inserting '::' after the type)"])

    c.compile("C767", "constants", ["constant-parameters-and-bounds"], definition(
        "character(2) :: text = 'abcd'\ninteger :: values(-1:1) = 3"))
    c.compile("C767", "deferred_character", ["deferred-pointer-parameters"], definition(
        "character(:), pointer :: empty => null()\ncharacter(:), pointer :: alias => target",
        "character(3), target, save :: target = 'abc'\n"))
    c.compile("C767", "deferred_array", ["deferred-pointer-shape"], definition(
        "integer, pointer :: empty(:) => null()\ninteger, pointer :: alias(:) => target",
        "integer, target, save :: target(2) = [2,3]\n"))
    c.compile("C767", "kind_primary", ["prior-kind-constant-primary"], definition(
        "integer, kind :: extent\ninteger :: values(extent) = 3", header="record(extent)"))
    for variant, facet, component in (
        ("length", "nonconstant-length", "character(width) :: value = 'abc'"),
        ("lower", "nonconstant-lower-bound", "integer :: value(width:3) = 2"),
        ("upper", "nonconstant-upper-bound", "integer :: value(1:width) = 2"),
    ):
        declarations = "integer, len :: width = 2\n" + component
        initializer = " = 'abc'" if variant == "length" else " = 2"
        c.pair("C767", variant, [facet], definition(declarations, header="record(width)"),
               component, component.replace(initializer, ""), component,
               ["Initialized component 'value' must have constant type parameters and bounds",
                "Component 'value' with nonconstant length or bounds cannot have initialization"])

    target = "integer, target, save :: target = 7\n"
    for variant, facet, component in (
        ("pointer_null", "pointer-null-arrow", "integer, pointer :: alias => null()"),
        ("pointer_target", "pointer-target-arrow", "integer, pointer :: alias => target"),
        ("ordinary", "ordinary-equals", "integer :: value = 3"),
    ):
        c.compile("C768", variant, [facet], definition(component, target))
    for variant, facet, bad, wrong, repair, messages in (
        ("null_without_pointer", "null-arrow-without-pointer", "integer :: alias => null()",
         "integer ::", "integer, pointer ::",
         ["Component 'alias' with a pointer initializer must have the POINTER attribute",
          "Pointer initialization on non-POINTER component 'alias'",
          "Initialization at (1) isn't for a pointer variable",
          "Non-pointer component 'alias' initialized with null pointer"]),
        ("target_without_pointer", "target-arrow-without-pointer", "integer :: alias => target",
         "integer ::", "integer, pointer ::",
         ["Component 'alias' with a pointer initializer must have the POINTER attribute",
          "Pointer initialization on non-POINTER component 'alias'",
          "Initialization at (1) isn't for a pointer variable",
          "'alias' is not a pointer but is initialized like one"]),
        ("pointer_equals", "equals-with-pointer", "integer, pointer :: value = 3",
         ", pointer", "",
         ["Pointer component 'value' cannot have an equals initializer",
          "POINTER initialization at (1) must be of the form '=> null()' or '=> target'",
          "Pointer component 'value' must be initialized with '=>'",
          "Pointer initialization at (1) requires '=>', not '='",
          "'value' is a pointer but is not initialized like one"]),
        ("allocatable_equals", "equals-with-allocatable", "integer, allocatable :: value = 3",
         ", allocatable", "",
         ["Allocatable component 'value' cannot have default initialization",
          "Initialization of allocatable component 'value' is not allowed",
          "Allocatable component 'value' at (1) cannot have an initializer",
          "Initialization of allocatable component at (1) is not allowed",
          "Allocatable object 'value' cannot be initialized",
          "An 'allocatable' variable cannot have an initialization expression"]),
    ):
        c.pair("C768", variant, [facet], definition(bad, target), wrong, repair, bad, messages)


def target_cases(c):
    prefix = ("integer, target, save :: target = 7\n"
              "real, target, save :: other = 0.0\n"
              "integer, target, save :: values(4) = [2,3,5,7]\n"
              "character(3), target, save :: text = 'abc'\n")
    c.compile("C769", "matching", ["same-type-rank-parameters"], definition(
        "integer, pointer :: scalar => target\n"
        "integer, pointer :: vector(:) => values\n"
        "character(3), pointer :: word => text", prefix))
    inherited = ("type :: parent\ninteger :: value\nend type\n"
                 "type, extends(parent) :: child\ninteger :: extra\nend type\n"
                 "type(child), target, save :: target\n")
    c.compile("C769", "extension", ["polymorphic-compatible-extension"], definition(
        "class(parent), pointer :: alias => target", inherited))
    c.compile("C769", "contiguous", ["contiguous-target"], definition(
        "integer, pointer, contiguous :: alias(:) => values", prefix))
    # Numeric kind annotations in diagnostic routes are observed spellings, not source premises.
    for variant, facet, component, wrong, repair, messages in (
        ("type", "type-mismatch", "integer, pointer :: alias => other", "=> other", "=> target",
         ["Type mismatch in initialization of pointer component 'alias'",
          "Pointer component 'alias' is not type compatible with target 'other'",
          "Different types in pointer assignment at (1); attempted assignment of REAL",
          "Target type REAL(4) is not compatible with pointer type INTEGER(4)"]),
        ("rank", "rank-mismatch", "integer, pointer :: alias => values", "=> values", "=> values(1)",
         ["Rank mismatch in initialization of pointer component 'alias'",
          "Different ranks in pointer assignment at (1)",
          "Pointer component 'alias' and target 'values' must have the same rank",
          "Incompatible ranks `0` and `1` in assignment",
          "Pointer has rank 0 but target has rank 1"]),
        ("length", "character-length-mismatch", "character(2), pointer :: alias => text",
         "=> text", "=> text(1:2)",
         ["Character length mismatch in initialization of pointer component 'alias'",
          "Different character lengths in pointer assignment",
          "Unequal character lengths (2/3) in pointer assignment",
          "Target type CHARACTER(KIND=1,LEN=3_8) is not compatible with pointer type CHARACTER(KIND=1,LEN=2_8)"]),
        ("strided", "noncontiguous-target", "integer, pointer, contiguous :: alias(:) => values(1:4:2)",
         ", contiguous", "",
         ["CONTIGUOUS pointer component 'alias' requires a contiguous initial target",
          "Assignment to contiguous pointer from non-contiguous target",
          "Contiguous pointer 'alias' cannot be associated with a noncontiguous target",
          "CONTIGUOUS pointer may not be associated with a discontiguous target"]),
    ):
        c.pair("C769", variant, [facet], definition(component, prefix), wrong, repair,
               component, messages)
    pdt = ("type :: element(width)\ninteger, len :: width\n"
           "character(width) :: payload\nend type\n"
           "type(element(3)), target, save :: target\n")
    component = "type(element(2)), pointer :: alias => target"
    c.pair("C769", "pdt_length", ["nondeferred-pdt-parameter-mismatch"],
           definition(component, pdt), "type(element(2))", "type(element(3))", component,
           ["Type parameter 'width' differs between pointer component 'alias' and its initial target",
            "Nondeferred type parameter mismatch in initialization of pointer component 'alias'",
            "Type parameter 'width' mismatch in pointer assignment",
            "Target type element(width=3_4) is not compatible with pointer type element(width=2_4)"])

    c.compile("C770", "saved", ["saved-target-name"], definition(
        "integer, pointer :: alias => target", "integer, target, save :: target = 7\n"))
    c.compile("C770", "module_saved", ["saved-target-name"], definition(
        "integer, pointer :: alias => target", "integer, target :: target\n"))
    for variant, facet, component in (
        ("element", "constant-array-element", "integer, pointer :: alias => values(2)"),
        ("section", "constant-section-triplet", "integer, pointer :: alias(:) => values(1:4:2)"),
        ("substring", "constant-substring", "character(:), pointer :: alias => text(1:2)"),
    ):
        c.compile("C770", variant, [facet], definition(component, prefix))
    component = "integer, pointer :: alias => target"
    c.pair("C770", "no_target", ["missing-target"],
           definition(component, "integer, save :: target\n"),
           "integer, save :: target", "integer, target, save :: target", component,
           ["Initial target 'target' must have the TARGET attribute",
            "Pointer assignment target does not have the TARGET attribute",
            "Pointer assignment target is neither TARGET nor POINTER",
            "Pointer assignment target in initialization expression does not have the TARGET attribute",
            "An initial data target may not be a reference to an object 'target' that lacks the TARGET attribute"])
    unsaved = ("subroutine local_definition\nimplicit none\ninteger, target :: target\n"
               "type :: record\n" + component + "\nend type\nend subroutine\n")
    c.pair("C770", "no_save", ["missing-save"], unsaved,
           "integer, target :: target", "integer, target, save :: target", component,
           ["Initial target 'target' must have the SAVE attribute",
            "Pointer initialization target at (1) must have the SAVE attribute",
            "Initial data target 'target' is not saved",
            "An initial data target may not be a reference to an object 'target' that lacks the SAVE attribute"])
    c.pair("C770", "allocatable", ["allocatable-target"], definition(
        component, "integer, allocatable, target, save :: target\n"),
        "allocatable, ", "", component,
        ["Initial target 'target' must not be ALLOCATABLE",
         "Allocatable variable 'target' is not permitted as an initial data target",
         "Pointer initialization target must be nonallocatable",
         "Pointer initialization target at (1) must not be ALLOCATABLE",
         "An initial data target may not be a reference to an ALLOCATABLE 'target'"])
    coindexed = "integer, pointer :: alias => target[1]"
    c.pair("C770", "coindexed", ["coindexed-target"], definition(
        coindexed, "integer, target, save :: target[*]\n"),
        "target[1]", "target", coindexed,
        ["Coindexed object is not permitted as an initial data target",
         "Initial target of pointer component 'alias' must not be coindexed",
         "Pointer initialization target must be noncoindexed",
         "Data target at (1) shall not have a coindex"], requires=("coarray",))
    selectors = [
        ("vector", "vector-subscript", "integer, pointer :: alias(:) => values([1,3])",
         "values([1,3])", "values(1:3:2)",
         ["Vector subscript is not allowed in an initial data target",
          "Pointer initialization target must not have a vector subscript",
          "Pointer assignment with vector subscript on rhs"]),
        ("element_variable", "variable-element-subscript", "integer, pointer :: alias => values(index)",
         "values(index)", "values(1)", []),
        ("lower_variable", "variable-triplet-start", "integer, pointer :: alias(:) => values(index:3)",
         "values(index:3)", "values(1:3)", []),
        ("upper_variable", "variable-triplet-end", "integer, pointer :: alias(:) => values(1:index)",
         "values(1:index)", "values(1:3)", []),
        ("stride_variable", "variable-triplet-stride", "integer, pointer :: alias(:) => values(1:3:index)",
         "values(1:3:index)", "values(1:3:1)", []),
        ("substring_lower", "variable-substring-start", "character(:), pointer :: alias => text(index:2)",
         "text(index:2)", "text(1:2)", []),
        ("substring_upper", "variable-substring-end", "character(:), pointer :: alias => text(1:index)",
         "text(1:index)", "text(1:2)", []),
    ]
    for variant, facet, component, wrong, repair, messages in selectors:
        if not messages:
            if variant.startswith("substring"):
                messages = [
                    "Nonconstant substring endpoint in an initial data target",
                    "Initial data target substring bounds must be constant",
                    "Substring starting and ending points of target specification at (1) must be constant expressions",
                ]
            else:
                messages = [
                    "Initial data target subscript must be a constant expression",
                    "Pointer initialization target must have constant subscripts",
                    "Every subscript of target specification at (1) must be a constant expression",
                    "An initial data target must be a designator with constant subscripts",
                ]
        c.pair("C770", variant, [facet], definition(component, prefix + "integer :: index = 1\n"),
               wrong, repair, component, messages)


def event_types(kind):
    prefix = "module event_types\nimplicit none\ninteger :: checks_completed=0\n"
    definitions = ""
    functions = ""
    if kind in ("null_procedure", "procedure"):
        prefix += ("abstract interface\ninteger function calculation(x)\n"
                   "integer, intent(in) :: x\nend function\nend interface\n")
        initializer = "null()" if kind == "null_procedure" else "original"
        definitions = "procedure(calculation), pointer, nopass :: action => " + initializer
        functions = ("integer function original(x)\ninteger, intent(in) :: x\noriginal = x+3\nend function\n"
                     "integer function alternate(x)\ninteger, intent(in) :: x\nalternate = x+5\nend function\n")
        changed = "item%action => alternate"
        check = ("if (associated(item%action)) error stop 1" if kind == "null_procedure" else
                 "if (.not.associated(item%action,original)) error stop 1\n"
                 "if (item%action(4) /= 7) error stop 2")
    elif kind == "value":
        definitions, changed, check = ("integer :: value = 3", "item%value = 9",
                                       "if (item%value /= 3) error stop 1")
    else:
        prefix += "integer, target, save :: original = 7, alternate = 11\n"
        initializer = "null()" if kind == "null_data" else "original"
        definitions = "integer, pointer :: alias => " + initializer
        changed = "item%alias => alternate"
        check = ("if (associated(item%alias)) error stop 1" if kind == "null_data" else
                 "if (.not.associated(item%alias,original)) error stop 1\n"
                 "if (item%alias /= 7) error stop 2")
    return (prefix + "type :: record\n" + definitions + "\nend type\ncontains\n" + functions
            + "subroutine verify(item)\ntype(record), intent(in) :: item\n" + check
            + "\nchecks_completed=checks_completed+1\nend subroutine\n"
            + "subroutine change(item)\ntype(record), intent(inout) :: item\n" + changed + "\nend subroutine\n"
            + "subroutine reset(item)\ntype(record), intent(out) :: item\n"
              "call verify(item)\nend subroutine\nend module\n")


def event_program(kind, event):
    declarations, statements, internal = "", "", ""
    if event == "initial":
        declarations = "type(record), save :: item"
        statements = "call verify(item)\ncall change(item)"
    elif event == "local":
        statements = "call visit()\ncall visit()"
        internal = ("\ncontains\nsubroutine visit()\ntype(record) :: item\n"
                    "call verify(item)\ncall change(item)\nend subroutine\n")
    elif event == "intent_out":
        declarations = "type(record) :: item"
        statements = "call change(item)\ncall reset(item)\ncall verify(item)"
    elif event == "block":
        declarations = "integer :: iteration"
        statements = ("do iteration=1,2\nblock\ntype(record) :: item\n"
                      "call verify(item)\ncall change(item)\nend block\nend do")
    else:
        attr = "allocatable" if event == "allocate" else "pointer"
        initial = "" if attr == "allocatable" else " => null()"
        declarations = f"type(record), {attr} :: item{initial}\ninteger :: stat, iteration"
        guard = "allocated" if attr == "allocatable" else "associated"
        statements = ("do iteration=1,2\nallocate(item,stat=stat)\n"
                      "if (stat /= 0) error stop 10\n"
                      f"if (.not.{guard}(item)) error stop 12\ncall verify(item)\ncall change(item)\n"
                      "deallocate(item,stat=stat)\nif (stat /= 0) error stop 11\nend do")
    statements += f"\nif (checks_completed /= {1 if event == 'initial' else 2}) error stop 20"
    return (event_types(kind) + "program event_witness\nuse event_types\nimplicit none\n"
            + declarations + "\n" + statements + internal + "\nend program\n")


def state_and_value_cases(c):
    for kind, rule in (("null_data", "S7.5.4.6-003"), ("null_procedure", "S7.5.4.6-003"),
                       ("data", "S7.5.4.6-004"), ("procedure", "S7.5.4.6-005"),
                       ("value", "S7.5.4.6-006")):
        facets = dict(initial="initial-status", local="local-entry", intent_out="intent-out-entry",
                      block="block-entry", allocate="allocation-without-source",
                      allocate_pointer="allocation-without-source")
        if kind == "null_procedure":
            facets["initial"] = "procedure-null-status"
        if kind == "value":
            facets = dict(initial="scalar-integer-value", local="local-entry-value",
                          intent_out="intent-out-value", block="block-entry-value",
                          allocate="allocation-without-source-value",
                          allocate_pointer="allocation-without-source-value")
        for event, facet in facets.items():
            covered = [facet]
            if kind == "procedure" and event == "initial":
                covered.append("module-target-call")
            c.run(rule, kind + "_" + event, covered, event_program(kind, event))

    c.run("S7.5.4.6-004", "target_alias", ["defined-target-alias"],
          event_types("data") + source("""
          program alias_witness
          use event_types
          implicit none
          type(record) :: item
          call verify(item)
          item%alias = 13
          if (original /= 13) error stop 3
          if (alternate /= 11) error stop 4
          end program
          """))
    c.run("S7.5.4.6-005", "external_call", ["external-target-call"], """
        module external_types
        implicit none
        abstract interface
          integer function calculation(x)
            integer, intent(in) :: x
          end function
        end interface
        procedure(calculation) :: outside
        type :: record
          procedure(calculation), pointer, nopass :: action => outside
        end type
        end module
        integer function outside(x)
        implicit none
        integer, intent(in) :: x
        outside = x+3
        end function
        program external_witness
        use external_types
        implicit none
        type(record) :: item
        if (.not.associated(item%action,outside)) error stop 1
        if (item%action(4) /= 7) error stop 2
        end program
    """)

    for variant, declaration, expected_kind, initializer in (
        ("to_selected", "integer(ik)", "ik", "3"),
        ("to_default", "integer", "kind(0)", "3_ik"),
    ):
        c.run("S7.5.4.6-006", "integer_" + variant, ["integer-kind-conversion"], program(
            "integer, parameter :: ik=selected_int_kind(18)\n"
            "type :: record\n" + declaration + " :: value=" + initializer + "\nend type\n"
            "type(record) :: item",
            "if (item%value /= 3) error stop 1\ncall verify(item%value)",
            suffix="contains\nsubroutine verify(value)\ninteger(" + expected_kind
                   + "), intent(in) :: value\nif (value /= 3) error stop 2\nend subroutine\n"))
    for variant, length, initial, expected in (
        ("padded", 5, "'ab'", "'ab   '"), ("truncated", 2, "'abcd'", "'ab'"),
    ):
        c.run("S7.5.4.6-006", "character_" + variant, ["character-length-conversion"], program(
            f"type :: record\ncharacter({length}) :: text={initial}\nend type\ntype(record) :: item",
            f"if (len(item%text) /= {length}) error stop 1\nif (item%text /= {expected}) error stop 2"))
    for variant, facet, initializer, expected in (
        ("scalar_expansion", "scalar-to-array-expansion", "3", "[3,3,3]"),
        ("array_constant", "array-value-and-shape", "[-2,0,3]", "[-2,0,3]"),
    ):
        c.run("S7.5.4.6-006", variant, [facet], program(
            "type :: record\ninteger :: values(-1:1)=" + initializer + "\nend type\ntype(record) :: item",
            "if (size(item%values) /= 3) error stop 1\n"
            "if (lbound(item%values,1) /= -1 .or. ubound(item%values,1) /= 1) error stop 2\n"
            "if (any(item%values /= " + expected + ")) error stop 3"))

    alloc_type = ("type :: inner\ninteger, allocatable :: scalar, values(:)\nend type\n"
                  "type :: record\ntype(inner) :: nested\ninteger, allocatable :: values(:)\nend type\n")
    checks = ("if (allocated(item%values)) error stop 1\n"
              "if (allocated(item%nested%scalar)) error stop 2\n"
              "if (allocated(item%nested%values)) error stop 3")
    c.run("S7.5.4.6-001", "declared_unallocated",
          ["declared-object-status", "nested-container-status"],
          program(alloc_type + "type(record) :: item", checks))
    c.run("S7.5.4.6-001", "allocated_unallocated", ["allocated-container-status"], program(
        alloc_type + "type(record), allocatable :: item\ninteger :: stat",
        "allocate(item,stat=stat)\nif (stat /= 0) error stop 10\n"
        "if (.not.allocated(item)) error stop 12\n" + checks
        + "\ndeallocate(item,stat=stat)\nif (stat /= 0) error stop 11"))


def override_cases(c):
    inner = "type :: inner\ninteger :: value=3\nend type\n"
    c.run("S7.5.4.6-007", "nested_override", ["nested-value-override"], program(
        inner + "type :: outer\ntype(inner) :: nested=inner(7)\nend type\ntype(outer) :: item",
        "if (item%nested%value /= 7) error stop 1"))
    c.run("S7.5.4.6-007", "pointer_override", ["nested-pointer-status-override"], program(
        "integer, target, save :: target=11\n"
        "type :: inner\ninteger :: value=3\ninteger, pointer :: alias => target\nend type\n"
        "type :: outer\ntype(inner) :: nested=inner(7,null())\nend type\ntype(outer) :: item",
        "if (item%nested%value /= 7) error stop 1\n"
        "if (associated(item%nested%alias)) error stop 2\nif (target /= 11) error stop 3"))
    c.run("S7.5.4.6-007", "deep_override", ["multiple-nesting-levels"], program(
        inner + "type :: middle\ntype(inner) :: nested=inner(7)\nend type\n"
        "type :: outer\ntype(middle) :: nested=middle(inner(11))\nend type\ntype(outer) :: item",
        "if (item%nested%nested%value /= 11) error stop 1"))
    c.run("S7.5.4.6-008", "explicit_scalar", ["explicit-scalar-object"], program(
        inner + "type(inner) :: item=inner(7), defaults",
        "if (item%value /= 7) error stop 1\nif (defaults%value /= 3) error stop 2"))
    c.run("S7.5.4.6-008", "explicit_array", ["explicit-array-object"], program(
        inner + "type(inner) :: items(2)=[inner(2),inner(5)]",
        "if (size(items) /= 2) error stop 1\nif (any(items%value /= [2,5])) error stop 2"))
    c.run("S7.5.4.6-008", "explicit_nested", ["explicit-nested-object"], program(
        inner + "type :: outer\ntype(inner) :: nested=inner(7)\nend type\n"
        "type(outer) :: item=outer(inner(11)), defaults",
        "if (item%nested%value /= 11) error stop 1\n"
        "if (defaults%nested%value /= 7) error stop 2"))
    c.run("S7.5.4.6-009", "save_contrast",
          ["unsaved-local-reentry", "explicit-save-control"], """
        module save_types
        implicit none
        type :: record
          integer :: value=3
        end type
        end module
        program save_witness
        use save_types
        implicit none
        call visit(1)
        call visit(2)
        contains
        subroutine visit(iteration)
          integer, intent(in) :: iteration
          type(record) :: automatic
          type(record), save :: persistent
          if (automatic%value /= 3) error stop 1
          if (iteration == 1) then
            if (persistent%value /= 3) error stop 2
          else
            if (persistent%value /= 9) error stop 3
          end if
          automatic%value=9
          persistent%value=9
        end subroutine
        end program
    """)
    c.run("S7.5.4.6-010", "nested_default", ["ordinary-nested-default"], program(
        "type :: inner\ninteger :: value=3, untouched\nend type\n"
        "type :: outer\ntype(inner) :: nested\ninteger :: sibling\nend type\ntype(outer) :: item",
        "if (item%nested%value /= 3) error stop 1\n"
        "item%nested%untouched=5\nitem%sibling=7\n"
        "if (item%nested%untouched /= 5 .or. item%sibling /= 7) error stop 2"))


def order_cases(c):
    plain = "type :: record\ninteger :: zed, alpha\ninteger :: middle\nend type\n"
    c.run("S7.5.4.7-001", "positions",
          ["positional-constructor-order", "same-statement-declaration-list"], program(
        plain + "type(record) :: item",
        "item=record(2,3,5)\nif (item%zed /= 2 .or. item%alpha /= 3 .or. item%middle /= 5) error stop 1"))
    for direction in ("input", "output"):
        declarations = plain + "type(record) :: item\ncharacter(5) :: text\ninteger :: stat"
        if direction == "output":
            body = ("item%zed=2\nitem%alpha=3\nitem%middle=5\n"
                    "write(text,'(I1,1X,I1,1X,I1)',iostat=stat) item\n"
                    "if (stat /= 0) error stop 1\nif (text /= '2 3 5') error stop 2")
        else:
            body = ("text='7 4 1'\nread(text,'(I1,1X,I1,1X,I1)',iostat=stat) item\n"
                    "if (stat /= 0) error stop 1\n"
                    "if (item%zed /= 7 .or. item%alpha /= 4 .or. item%middle /= 1) error stop 2")
        c.run("S7.5.4.7-001", "formatted_" + direction,
              ["formatted-" + direction + "-order"], program(declarations, body))
    parent = "type :: parent\ninteger :: zed, alpha\nend type\n"
    child = "type, extends(parent) :: child\ninteger :: middle\nend type\n"
    check = "if (item%zed /= 2 .or. item%alpha /= 3 .or. item%middle /= 5) error stop 1"
    for variant, facet, expression in (
        ("flat", "inherited-prefix-constructor", "child(2,3,5)"),
        ("parent_keyword", "parent-keyword-control", "child(parent=parent(2,3),middle=5)"),
    ):
        c.run("S7.5.4.7-002", variant, [facet],
              program(parent + child + "type(child) :: item", "item=" + expression + "\n" + check))
    c.run("S7.5.4.7-002", "inherited_only", ["no-new-components"], program(
        parent + "type, extends(parent) :: child\nend type\ntype(child) :: item",
        "item=child(2,3)\nif (item%zed /= 2 .or. item%alpha /= 3) error stop 1"))
    c.run("S7.5.4.7-002", "three_generations", ["multi-generation-order"], program(
        parent + "type, extends(parent) :: middle\ninteger :: extra\nend type\n"
        "type, extends(middle) :: child\ninteger :: last\nend type\ntype(child) :: item",
        "item=child(2,3,5,7)\nif (item%zed /= 2 .or. item%alpha /= 3) error stop 1\n"
        "if (item%extra /= 5 .or. item%last /= 7) error stop 2"))
    for direction in ("input", "output"):
        declarations = parent + child + "type(child) :: item\ncharacter(5) :: text\ninteger :: stat"
        body = (("item%zed=2\nitem%alpha=3\nitem%middle=5\n"
                 "write(text,'(I1,1X,I1,1X,I1)',iostat=stat) item\n"
                 "if (stat /= 0) error stop 1\nif (text /= '2 3 5') error stop 2")
                if direction == "output" else
                ("text='7 4 1'\nread(text,'(I1,1X,I1,1X,I1)',iostat=stat) item\n"
                 "if (stat /= 0) error stop 1\n"
                 "if (item%zed /= 7 .or. item%alpha /= 4 .or. item%middle /= 1) error stop 2"))
        c.run("S7.5.4.7-002", "formatted_" + direction, ["formatted-inherited-order"],
              program(declarations, body))


def access_cases(c):
    c.compile("R745", "bare_private", ["bare-private-component-statement"], definition(
        "private\ninteger :: value"))
    c.pair("R745", "private_list", ["named-list-excluded"],
           definition("private :: value\ninteger :: value"), "private :: value", "private",
           "private :: value",
           ["PRIVATE component statement must not have a name list",
            "Expected a bare PRIVATE component statement"])
    c.compile("C771", "module", ["module-specification-control"],
              definition("private\ninteger :: value"))
    typedef = "type :: record\nprivate\ninteger :: value\nend type\n"
    for variant, facet, bad in (
        ("program", "main-program-excluded", "program access_context\nimplicit none\n" + typedef + "end program\n"),
        ("external", "external-procedure-excluded", "subroutine access_context\nimplicit none\n" + typedef + "end subroutine\n"),
        ("module_procedure", "module-procedure-body-excluded",
         "module access_context\nimplicit none\ncontains\nsubroutine local_context\n"
         + typedef + "end subroutine\nend module\n"),
    ):
        c.pair("C771", variant, [facet], bad, "private\n", "", "private",
               ["PRIVATE statement in a derived type definition is only allowed in the specification part of a module",
                "PRIVATE component statement must appear in a module specification part",
                "PRIVATE statement at (1) is only allowed in the specification part of a module",
                "PRIVATE is only allowed in a derived type that is in a module"])

    c.multi("S7.5.4.8-001", "public_default", ["public-default-client-use"], {
        "provider.f90": """
            module access_provider
            implicit none
            private
            public :: record
            type :: record
              integer :: value
            end type
            end module
        """,
        "main.f90": """
            program client
            use access_provider, only: record
            implicit none
            type(record) :: item
            item%value=7
            if (item%value /= 7) error stop 1
            end program
        """,
    })
    c.multi("S7.5.4.8-001", "public_override", ["public-overrides-private-default"], {
        "provider.f90": """
            module access_provider
            implicit none
            type :: record
              private
              integer :: hidden
              integer, public :: visible
            end type
            end module
        """,
        "main.f90": """
            program client
            use access_provider, only: record
            implicit none
            type(record) :: item
            item%visible=7
            if (item%visible /= 7) error stop 1
            end program
        """,
    })
    owner = """
        module access_provider
        implicit none
        type :: record
          private
          integer :: hidden
        end type
        contains
        subroutine fill(item)
          type(record), intent(out) :: item
          item%hidden=7
        end subroutine
        integer function read_value(item)
          type(record), intent(in) :: item
          read_value=item%hidden
        end function
        end module
    """
    client = """
        program client
        use access_provider, only: record, fill, read_value
        implicit none
        type(record) :: item
        call fill(item)
        if (read_value(item) /= 7) error stop 1
        end program
    """
    c.multi("S7.5.4.8-001", "private_owner", ["private-default-owner-use"],
            {"provider.f90": owner, "main.f90": client})
    transfer = source(client).replace(":: item", ":: item, copied").replace(
        "if (read_value(item) /= 7)", "copied=item\nif (read_value(copied) /= 7)")
    c.multi("S7.5.4.8-002", "whole_object",
            ["defining-module-reference", "whole-object-control"],
            {"provider.f90": owner, "main.f90": transfer}, evidence="positive-control")
    parent = """
        module access_provider
        implicit none
        type :: record
          private
          integer :: hidden
        end type
        interface
          module subroutine fill(item)
            type(record), intent(out) :: item
          end subroutine
          module integer function read_value(item)
            type(record), intent(in) :: item
          end function
        end interface
        end module
    """
    procedures = """
        contains
        module procedure fill
          item%hidden=7
        end procedure
        module procedure read_value
          read_value=item%hidden
        end procedure
        end submodule
    """
    c.multi("S7.5.4.8-002", "child", ["child-submodule-reference"], {
        "parent.f90": parent,
        "child.f90": "submodule(access_provider) access_child\n" + source(procedures),
        "main.f90": client,
    }, evidence="positive-control")
    c.multi("S7.5.4.8-002", "grandchild", ["grandchild-submodule-reference"], {
        "parent.f90": parent,
        "child.f90": "submodule(access_provider) access_child\nend submodule\n",
        "grandchild.f90": "submodule(access_provider:access_child) access_grandchild\n" + source(procedures),
        "main.f90": client,
    }, evidence="positive-control")

    for variant in ("default", "explicit"):
        component = "private\ninteger :: hidden" if variant == "default" else "integer, private :: hidden"
        provider = source("module access_provider\nimplicit none\ntype :: record\n"
                          + component + "\nend type\nend module\n")
        main = source("""
            program client
            use access_provider, only: record
            implicit none
            type(record) :: item
            item=record(hidden=7)
            end program
        """)
        point = main.splitlines().index("item=record(hidden=7)") + 1
        diagnostic = dict(file="main.f90", line=point, contains_any=[
            "Component 'hidden' is PRIVATE in this structure constructor",
            "Component 'hidden' at (1) is a PRIVATE component of 'record'",
            "PRIVATE component 'hidden' is not accessible in a structure constructor",
            "Private component 'hidden' is not accessible",
            "PRIVATE name 'hidden' is accessible only within module 'access_provider'"],
            excludes_any=BASE.EXCLUDED)
        bad = c.multi("C7107", variant + "_private", ["private-component-" + variant],
                      {"provider.f90": provider, "main.f90": main},
                      phase="compile", diagnostic=diagnostic, evidence="effect")
        wrong, repaired = ("private\n", "") if variant == "default" else (", private", ", public")
        assert provider.count(wrong) == 1
        good = c.multi("C7107", variant + "_private_repair", ["private-component-" + variant],
                       {"provider.f90": provider.replace(wrong, repaired, 1), "main.f90": main},
                       phase="compile", evidence="positive-control")
        c.repairs.append(dict(invalid=bad, valid=good, file="provider.f90", wrong=wrong, repaired=repaired))


def build_corpus():
    c = Corpus()
    grammar_cases(c)
    target_cases(c)
    state_and_value_cases(c)
    override_cases(c)
    order_cases(c)
    access_cases(c)
    return c


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    c = build_corpus()
    for path, raw in c.files.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                parser.error("generated input differs: " + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f"{'Checked' if args.check else 'Generated'} {len(c.files)} files for {len(c.cases)} initialization cases.")


if __name__ == "__main__":
    main()
