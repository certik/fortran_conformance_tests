#!/usr/bin/env python3
"""Generate the finite data/procedure-component corpus without running compilers."""
import argparse
import json
from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_CAUSES = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported feature",
    "unsupported",
    "not supported", "not yet supported", "implementation limitation",
    "ASR verify", "ASR verifier", "internal compiler error", "LLVM ERROR",
    "unexpected end of file", "unexpected eof", "missing end", "obsolescent",
    "obsolete feature", "out of memory", "overflow",
]


def text(value):
    return textwrap.dedent(value).strip("\n") + "\n"


def case_id(rule, variant, invalid=False):
    return (rule.replace(".", "_").replace("-", "_")
            + ("_invalid__" if invalid else "_valid__") + variant)


def source_name(rule):
    return rule.replace(".", "_").replace("-", "_") + ".f90"


def module(body, before="", after=""):
    return "module definitions\nimplicit none\n" + before + text(body) + after + "end module\n"


def record(member, prefix="", attributes=""):
    return prefix + "type" + attributes + " :: record\n    " + member + "\nend type\n"


class Corpus:
    def __init__(self):
        self.files = {}
        self.cases = {}
        self.repairs = {}

    def fixture(self, name, rule, facets, inputs, phase="compile", diagnostic=None,
                coarray=False, relation=""):
        if name in self.cases:
            raise ValueError(f"duplicate execution: {name}")
        folder = ROOT / "tests/fixtures" / ("data_component_" + name.lower())
        inputs = {file: text(content) for file, content in inputs.items()}
        steps = []
        for file, content in inputs.items():
            path = folder / file
            if path in self.files:
                raise ValueError(f"duplicate input: {path}")
            self.files[path] = content.encode("ascii")
            step = Path(file).stem
            steps.append(dict(id=step, source=file, language="fortran", form="free",
                              output=step + ".o", depends_on=[item["id"] for item in steps]))
        evidence = "effect" if diagnostic or rule.startswith("S") else "positive-control"
        expectation = dict(phase=phase, outcome="diagnose" if diagnostic else "success")
        manifest = dict(schema_version=1, id=name, rule=rule, facets=list(facets),
                        evidence=evidence, standard="f2023", files=list(inputs), build=steps,
                        expect=expectation)
        if phase == "compile":
            expectation["step"] = steps[-1]["id"]
        else:
            manifest["link"] = dict(objects=[step["output"] for step in steps], output="program")
            expectation["exit_code"] = 0
        if coarray:
            manifest["requires"] = ["coarray"]
        if diagnostic:
            expectation["diagnostic"] = diagnostic
        path = folder / "fixture.json"
        self.files[path] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        self.cases[name] = dict(rule=rule, kind="invalid" if diagnostic else "valid",
                                facets=list(facets), phase=phase, evidence=evidence,
                                standard="f2023", profiles=[], images=1, coarray=coarray,
                                path=path.relative_to(ROOT).as_posix(), source_relation=relation)

    def compile(self, rule, variant, facets, body, coarray=False):
        self.fixture(case_id(rule, variant), rule, facets,
                     {source_name(rule): body}, coarray=coarray)

    def run(self, rule, variant, facets, inputs, coarray=False):
        if isinstance(inputs, str):
            inputs = {source_name(rule): inputs}
        self.fixture(case_id(rule, variant), rule, facets, inputs, "run", coarray=coarray)

    def program(self, rule, variant, facets, body, coarray=False):
        self.run(rule, variant, facets, "program p\n" + text(body) + "end program\n", coarray)

    def pair(self, rule, variant, facets, inputs, wrong, repaired, anchor, messages,
             edit_file=None, anchor_file=None, end_anchor=None, relation="", coarray=False,
             control_variant=None, control_facets=None, exclusions=()):
        if isinstance(inputs, str):
            inputs = {source_name(rule): inputs}
        inputs = {file: text(content) for file, content in inputs.items()}
        edit_file = edit_file or source_name(rule)
        anchor_file = anchor_file or edit_file
        raw = inputs[edit_file]
        if raw.count(wrong) != 1 or wrong == repaired:
            raise ValueError(f"{rule}/{variant}: repair must change one unique source span")
        lines = inputs[anchor_file].splitlines()
        starts = [n for n, line in enumerate(lines, 1) if line.strip() == anchor]
        if len(starts) != 1:
            raise ValueError(f"{rule}/{variant}: nonunique diagnostic anchor: {anchor}")
        diagnostic = dict(file=anchor_file, line=starts[0], contains_any=list(messages),
                          excludes_any=EXCLUDED_CAUSES + list(exclusions))
        if end_anchor:
            ends = [n for n, line in enumerate(lines, 1) if line.strip() == end_anchor]
            if len(ends) != 1 or ends[0] < starts[0] or not relation:
                raise ValueError(f"{rule}/{variant}: unjustified diagnostic relation")
            diagnostic["end_line"] = ends[0]
        negative = case_id(rule, variant, True)
        control = case_id(rule, control_variant or variant + "_repair")
        self.fixture(negative, rule, facets, inputs, diagnostic=diagnostic,
                     coarray=coarray, relation=relation)
        good = dict(inputs)
        good[edit_file] = raw.replace(wrong, repaired, 1)
        self.fixture(control, rule, control_facets or facets, good,
                     coarray=coarray, relation=relation)
        self.repairs[negative] = [dict(control=control, file=edit_file, wrong=wrong,
                                       repaired=repaired, relation=relation)]
        return negative

    def extra_repair(self, negative, variant, inputs, wrong, repaired, facets=None):
        spec = self.cases[negative]
        rule = spec["rule"]
        file = source_name(rule)
        if isinstance(inputs, str):
            inputs = {file: text(inputs)}
        inputs = {name: text(raw) for name, raw in inputs.items()}
        if inputs[file].count(wrong) != 1:
            raise ValueError(f"{negative}: nonunique additional repair")
        inputs[file] = inputs[file].replace(wrong, repaired, 1)
        control = case_id(rule, variant)
        self.fixture(control, rule, facets or spec["facets"], inputs,
                     coarray=spec["coarray"], relation=spec["source_relation"])
        self.repairs[negative].append(dict(control=control, file=file, wrong=wrong,
                                           repaired=repaired, relation=spec["source_relation"]))


def basic_declarations(c):
    c.program("R735", "multiple_statements", ["multiple-statements"], """
        implicit none
        type :: record
            integer :: first
            integer :: second
        end type
        type(record) :: value
        value%first = 11
        value%second = 13
        if (value%first /= 11 .or. value%second /= 13) error stop 1
    """)
    for variant, separator, facet in (
        ("plain", "", "plain-without-colons"), ("colons", ":: ", "plain-with-colons"),
    ):
        c.program("R737", variant, [facet], f"""
            implicit none
            type :: record
                integer {separator}first, second
            end type
            type(record) :: value
            value%first = 11
            value%second = 13
            if (value%first /= 11 .or. value%second /= 13) error stop 1
        """)
    c.pair("R737", "missing_colons", ["attribute-separator"],
           module(record("integer, pointer field(:)")),
           "pointer field", "pointer :: field", "integer, pointer field(:)", [
               "Missing :: after the attributes of data component 'field'",
               "Data component attributes require a double-colon separator before 'field'",
           ])
    for variant in ("public", "private"):
        provider = ("module provider\nimplicit none\ntype, public :: record\n"
                    + ("private\ninteger, public :: field\n" if variant == "public" else
                       "integer, private :: field\n")
                    + "end type\ntype(record) :: published\ncontains\n"
                    "subroutine initialize()\npublished%field = 11\nend subroutine\n"
                    "integer function inspect()\ninspect = published%field\nend function\nend module\n")
        check = ("if (published%field /= 11) error stop 1\n" if variant == "public" else
                 "if (inspect() /= 11) error stop 1\n")
        c.run("R738", variant, [variant], {
            "provider.f90": provider,
            source_name("R738"): "program p\nuse provider, only: published, initialize, inspect\n"
                                "implicit none\ncall initialize()\n" + check + "end program\n",
        })
    c.program("R738", "allocatable", ["allocatable"], """
        implicit none
        type :: record
            integer, allocatable :: field(:)
        end type
        type(record) :: value
        integer :: stat
        if (allocated(value%field)) error stop 1
        allocate(value%field(2), stat=stat)
        if (stat /= 0) error stop 2
        if (.not. allocated(value%field)) error stop 3
        value%field = [11,13]
        if (size(value%field) /= 2) error stop 4
        if (any(value%field /= [11,13])) error stop 5
        deallocate(value%field, stat=stat)
        if (stat /= 0) error stop 6
    """)
    c.program("R738", "contiguous", ["contiguous"], """
        implicit none
        type :: record
            integer, pointer, contiguous :: field(:)
        end type
        type(record) :: value
        integer, target :: target(2)
        target = [11,13]
        nullify(value%field)
        if (associated(value%field)) error stop 1
        value%field => target
        if (.not. associated(value%field)) error stop 2
        if (.not. is_contiguous(value%field)) error stop 3
        if (any(value%field /= [11,13])) error stop 4
        value%field(2) = 17
        if (any(target /= [11,17])) error stop 5
        nullify(value%field)
    """)
    c.program("R738", "pointer", ["pointer"], """
        implicit none
        type :: record
            integer, pointer :: field
        end type
        type(record) :: value
        integer, target :: target
        target = 11
        nullify(value%field)
        if (associated(value%field)) error stop 1
        value%field => target
        if (.not. associated(value%field)) error stop 2
        if (value%field /= 11) error stop 3
        value%field = 13
        if (target /= 13) error stop 4
        nullify(value%field)
    """)
    for variant, attribute, extra, shape, facet in (
        ("public", "public", "", "", "duplicate-access"),
        ("private", "private", "", "", "duplicate-access"),
        ("allocatable", "allocatable", "", "(:)", "duplicate-allocatable"),
        ("codimension", "codimension[:]", ", allocatable", "", "duplicate-codimension"),
        ("contiguous", "contiguous", ", pointer", "(:)", "duplicate-contiguous"),
        ("dimension", "dimension(2)", "", "", "duplicate-dimension"),
        ("pointer", "pointer", "", "(:)", "duplicate-pointer"),
    ):
        declaration = f"integer, {attribute}, {attribute}{extra} :: field{shape}"
        c.pair("C748", variant, [facet], module(record(declaration)),
               f", {attribute}, {attribute}", f", {attribute}", declaration, [
                   f"Data component 'field' has duplicate {attribute.upper()} attributes",
                   f"Repeated {attribute.upper()} attribute for component 'field'",
               ], coarray=variant == "codimension",
               exclusions=["dummy argument", "type-bound", "binding '", "variable '"])


def data_types(c):
    c.program("C749", "intrinsic_members", ["intrinsic-admission"], """
        implicit none
        type :: record
            integer :: count
            real :: number
            complex :: pair
            logical :: flag
            character(2) :: label
        end type
        type(record) :: value
        value%count = 11
        value%number = 0.0
        value%pair = (0.0,0.0)
        value%flag = .true.
        value%label = 'AB'
        if (value%count /= 11 .or. value%number /= 0.0) error stop 1
        if (value%pair /= (0.0,0.0)) error stop 2
        if (.not. value%flag .or. value%label /= 'AB') error stop 3
    """)
    leaf = "type :: leaf\ninteger :: field\nend type\n"
    c.program("C749", "prior_derived", ["prior-derived-admission"],
              "implicit none\n" + leaf + record("type(leaf) :: child")
              + "type(record) :: value\nvalue%child%field = 13\n"
              "if (value%child%field /= 13) error stop 1\n")
    for variant, definition, facet in (
        ("prior_enum", "enum, bind(c) :: category\nenumerator :: zero=0, one=1\nend enum\n",
         "prior-enum-admission"),
        ("prior_enumeration", "enumeration type :: category\nenumerator :: zero, one\nend enumeration type\n",
         "prior-enumeration-admission"),
    ):
        c.compile("C749", variant, [facet],
                  module(record("type(category) :: field"), before=definition))
    self_source = module(record("type(record) :: next"))
    negative = c.pair("C749", "self_value", ["self-value-exclusion"], self_source,
                      "type(record) :: next", "type(record), pointer :: next", "type(record) :: next", [
                          "Nonpointer nonallocatable component 'next' uses incomplete type 'record'",
                          "Component 'next' of type 'record' must have POINTER or ALLOCATABLE",
                      ], control_facets=["self-value-exclusion", "indirection-boundaries"])
    c.extra_repair(negative, "self_allocatable_repair", self_source, "type(record) :: next",
                   "type(record), allocatable :: next", ["self-value-exclusion", "indirection-boundaries"])
    before = "type :: good_type\ninteger :: payload\nend type\n"
    after = "type :: later_type\ninteger :: payload\nend type\n"
    forward = module(record("type(later_type) :: field"), before, after)
    c.pair("C749", "forward_value", ["forward-value-exclusion"], forward,
           "type(later_type) :: field", "type(good_type) :: field", "type(later_type) :: field", [
               "Type 'later_type' of nonpointer nonallocatable component 'field' must be previously defined",
               "Component 'field' uses derived type 'later_type' before its definition",
           ])
    for attribute in ("pointer", "allocatable"):
        c.compile("C749", "forward_" + attribute, ["indirection-boundaries"],
                  forward.replace("type(later_type) :: field",
                                  f"type(later_type), {attribute} :: field"))


def shapes_and_coarray_constraints(c):
    for variant, declaration, wrong, good, facet in (
        ("pointer_local", "integer, pointer :: field(2)", "(2)", "(:)", "pointer-local-shape"),
        ("pointer_dimension", "integer, pointer, dimension(2) :: field",
         "dimension(2)", "dimension(:)", "pointer-shared-shape"),
        ("allocatable_local", "integer, allocatable :: field(2,3)", "(2,3)", "(:,:)", "allocatable-local-shape"),
        ("allocatable_dimension", "integer, allocatable, dimension(2,3) :: field",
         "dimension(2,3)", "dimension(:,:)", "allocatable-shared-shape"),
        ("overridden_dimension", "integer, pointer, dimension(2) :: field(:)",
         "dimension(2)", "dimension(:)", "overridden-shape-still-constrained"),
    ):
        attribute = "ALLOCATABLE" if variant.startswith("allocatable") else "POINTER"
        messages = [f"Component 'field' with {attribute} must have deferred shape",
                    f"{attribute} component 'field' cannot have explicit shape"]
        if variant == "overridden_dimension":
            messages = ["DIMENSION specification of POINTER component 'field' must be deferred shape",
                        "Overridden DIMENSION of pointer component 'field' is not deferred shape"]
        c.pair("C750", variant, [facet], module(record(declaration)), wrong, good, declaration, messages)
    for variant, declaration, wrong, good, facet in (
        ("explicit_suffix", "integer, allocatable :: field[*]", "[*]", "[:]", "individual-deferred-coshape"),
        ("explicit_codimension", "integer, allocatable, codimension[*] :: field",
         "codimension[*]", "codimension[:]", "attribute-deferred-coshape"),
        ("missing_allocatable_suffix", "integer :: field[:]", "integer ::", "integer, allocatable ::",
         "individual-allocatable-required"),
        ("missing_allocatable_codimension", "integer, codimension[:] :: field",
         "integer,", "integer, allocatable,", "attribute-allocatable-required"),
        ("overridden_codimension", "integer, allocatable, codimension[*] :: field[:]",
         "codimension[*]", "codimension[:]", "overridden-coshape-still-constrained"),
    ):
        messages = (["Coarray component 'field' must have the ALLOCATABLE attribute",
                     "Coarray component 'field' lacks ALLOCATABLE"] if variant.startswith("missing") else
                    ["Coarray component 'field' must have deferred coshape",
                     "Explicit coshape is not permitted for coarray component 'field'"])
        if variant == "overridden_codimension":
            messages = ["CODIMENSION specification of component 'field' must be deferred coshape",
                        "Overridden CODIMENSION of component 'field' is not deferred coshape"]
        c.pair("C751", variant, [facet], module(record(declaration)), wrong, good,
               declaration, messages, coarray=True)
    for typename, mod, facet in (
        ("c_ptr", "iso_c_binding", "c-ptr-exclusion"),
        ("c_funptr", "iso_c_binding", "c-funptr-exclusion"),
        ("team_type", "iso_fortran_env", "team-type-exclusion"),
    ):
        for renamed in (False, True):
            local = "handle" if renamed else typename
            imported = f"handle => {typename}" if renamed else typename
            declaration = f"type({local}), allocatable :: field[:]"
            body = (f"module definitions\nuse {mod}, only: {imported}\nimplicit none\n"
                    + record(declaration) + "end module\n")
            facets = [facet] + (["module-identity-boundaries"] if renamed else [])
            c.pair("C752", typename + ("_renamed" if renamed else ""), facets, body,
                   f"type({local})", "integer", declaration, [
                       f"Coarray component 'field' may not have type {typename.upper()}",
                       f"Component 'field' of type '{typename}' from {mod.upper()} cannot be a coarray",
                   ], coarray=True)
    local_types = "".join(f"type :: {name}\ninteger :: payload\nend type\n"
                          for name in ("c_ptr", "c_funptr", "team_type"))
    members = "\n".join(f"type({name}), allocatable :: {name}_field[:]"
                        for name in ("c_ptr", "c_funptr", "team_type"))
    c.compile("C752", "unrelated_same_spelling", ["module-identity-boundaries"],
              module(record(members), before=local_types), coarray=True)
    leaf = "type :: leaf\ninteger, allocatable :: co[:]\nend type\n"
    for variant, declaration, wrong, good, messages in (
        ("pointer", "type(leaf), pointer :: field", ", pointer", "", [
            "Component 'field' with coarray potential subobjects cannot be POINTER",
            "POINTER component 'field' may not have a coarray ultimate component"]),
        ("allocatable", "type(leaf), allocatable :: field", ", allocatable", "", [
            "Component 'field' with coarray potential subobjects cannot be ALLOCATABLE",
            "ALLOCATABLE component 'field' may not have a coarray ultimate component"]),
        ("array", "type(leaf) :: field(2)", "field(2)", "field", [
            "Component 'field' with coarray potential subobjects must be scalar",
            "Array component 'field' may not have a coarray ultimate component"]),
    ):
        facet = {"pointer": "nonpointer", "allocatable": "nonallocatable", "array": "scalar"}[variant]
        c.pair("C753", variant, [facet], module(record(declaration), before=leaf),
               declaration, declaration.replace(wrong, good, 1), declaration, messages, coarray=True,
               relation="The complete leaf has one legal allocatable coarray; only the outer field property changes.")
    for variant, declaration, wrong, good, facet in (
        ("individual", "integer :: field(:)", "field(:)", "field(2)", "individual-explicit-shape"),
        ("dimension", "integer, dimension(:,:) :: field", "dimension(:,:)", "dimension(2,3)",
         "shared-explicit-shape"),
        ("overridden_dimension", "integer, dimension(:) :: field(2)", "dimension(:)", "dimension(3)",
         "overridden-shape-still-constrained"),
    ):
        messages = ["Nonpointer nonallocatable component 'field' must have explicit shape",
                    "Deferred shape is not permitted for ordinary component 'field'"]
        if variant == "overridden_dimension":
            messages = ["DIMENSION of nonpointer nonallocatable component 'field' must be explicit shape",
                        "Overridden DIMENSION of ordinary component 'field' is not explicit shape"]
        c.pair("C754", variant, [facet], module(record(declaration)), wrong, good, declaration, messages)


def component_expressions(c):
    c.program("C755", "kind_len_bounds", ["parameter-bound-admission"], """
        implicit none
        type :: record(k,n)
            integer, kind :: k
            integer, len :: n
            integer :: field(k,n)
        end type
        type(record(2,2)) :: first
        type(record(2,3)) :: second
        first%field = 11
        second%field = 13
        if (rank(first%field) /= 2 .or. rank(second%field) /= 2) error stop 1
        if (any(shape(first%field) /= [2,2])) error stop 2
        if (any(shape(second%field) /= [2,3])) error stop 3
        if (any(first%field /= 11) .or. any(second%field /= 13)) error stop 4
    """)
    c.program("C755", "inherited_len_bound", ["parameter-bound-admission"], """
        implicit none
        type :: parent(n)
            integer, len :: n
            integer :: first(n)
        end type
        type, extends(parent) :: child
            integer :: second(n+1)
        end type
        type(child(2)) :: value
        value%first = [11,13]
        value%second = [17,19,23]
        if (size(value%first) /= 2 .or. size(value%second) /= 3) error stop 1
        if (any(value%first /= [11,13])) error stop 2
        if (any(value%second /= [17,19,23])) error stop 3
    """)
    c.program("C755", "constant_property", ["constant-inquiry-admission"], """
        implicit none
        integer :: prototype(3)
        type :: record
            integer :: field(size(prototype))
        end type
        type(record) :: value
        value%field = [11,13,17]
        if (size(value%field) /= 3) error stop 1
        if (any(value%field /= [11,13,17])) error stop 2
    """)
    for variant, bounds, repaired in (
        ("lower_variable", "width:3", "2:3"), ("upper_variable", "1:width", "1:2"),
    ):
        declaration = f"integer :: field({bounds})"
        c.pair("C755", variant, ["lower-and-upper-variable-exclusion"],
               module(record(declaration), before="integer :: width = 2\n"),
               f"field({bounds})", f"field({repaired})", declaration, [
                   "Component bound of 'field' depends on the value of variable 'width'",
                   "Variable 'width' is not permitted in the component specification expression for 'field'",
               ], relation="width is a previously declared host variable, not a type parameter or an undeclared symbol.")
    function = """module functions
implicit none
contains
pure integer function extent(n)
integer, intent(in) :: n
extent = n
end function
end module
"""
    body = ("module definitions\nuse functions, only: extent\nimplicit none\n"
            + record("integer :: field(extent(2))") + "end module\n")
    c.pair("C755", "specification_function", ["specification-function-exclusion"],
           {"functions.f90": function, source_name("C755"): body},
           "extent(2)", "2", "integer :: field(extent(2))", [
               "Specification function 'extent' is not permitted in component bound 'field'",
               "Component specification expression for 'field' may not reference specification function 'extent'",
           ])
    body = """module definitions
implicit none
contains
subroutine outer(dummy)
integer, intent(in) :: dummy(:)
type :: record
    integer :: field(size(dummy))
end type
end subroutine
end module
"""
    c.pair("C755", "assumed_shape_inquiry", ["nonconstant-inquiry-exclusion"], body,
           "size(dummy)", "2", "integer :: field(size(dummy))", [
               "SIZE of assumed-shape dummy 'dummy' is not a constant inquiry in component bound 'field'",
               "Component specification inquiry for 'field' depends on the assumed shape of 'dummy'",
           ])


def attribute_conflicts_and_lengths(c):
    for variant, shape, facet in (("scalar", "", "scalar-exclusion"), ("array", "(:)", "array-exclusion")):
        declaration = f"integer, pointer, allocatable :: field{shape}"
        inputs = module(record(declaration))
        negative = c.pair("C756", variant, [facet], inputs,
                          ", pointer", "", declaration, [
                              "Component 'field' cannot have both POINTER and ALLOCATABLE",
                              "POINTER and ALLOCATABLE attributes conflict for component 'field'",
                          ])
        c.extra_repair(negative, variant + "_pointer_repair", inputs, ", allocatable", "")
    c.pair("C757", "scalar_pointer", ["scalar-pointer-exclusion"],
           module(record("integer, pointer, contiguous :: field")),
           ", contiguous", "", "integer, pointer, contiguous :: field", [
               "CONTIGUOUS pointer component 'field' must be an array",
               "Scalar pointer component 'field' cannot have CONTIGUOUS",
           ])
    c.pair("C757", "ordinary_array", ["nonpointer-array-exclusion"],
           module(record("integer, contiguous :: field(2)")),
           ", contiguous", "", "integer, contiguous :: field(2)", [
               "CONTIGUOUS component 'field' must have the POINTER attribute",
               "Nonpointer component 'field' cannot have CONTIGUOUS",
           ])
    for variant, typename, before in (
        ("integer_suffix", "integer", ""),
        ("derived_suffix", "type(leaf)", "type :: leaf\ninteger :: payload\nend type\n"),
    ):
        declaration = typename + " :: field*2"
        c.pair("C758", variant, ["noncharacter-suffix-exclusion"],
               module(record(declaration), before=before),
               "field*2", "field", declaration, [
                   "Noncharacter component 'field' cannot have a character length suffix",
                   "Character length suffix is only permitted for CHARACTER component 'field'",
               ])
    c.program("C759", "own_len_parameter", ["data-parameter-expression"], """
        implicit none
        type :: record(n)
            integer, len :: n
            character(len=n) :: field
        end type
        type(record(2)) :: first
        type(record(3)) :: second
        first%field = 'AB'
        second%field = 'CDE'
        if (len(first%field) /= 2 .or. len(second%field) /= 3) error stop 1
        if (first%field /= 'AB' .or. second%field /= 'CDE') error stop 2
    """)
    for variant, suffix, facet in (
        ("host_variable", "", "data-parameter-expression"),
        ("overridden_length", "*2", "overridden-parameter-still-constrained"),
    ):
        declaration = "character(len=width) :: field" + suffix
        messages = ["Length parameter of component 'field' depends on variable 'width'",
                    "Variable 'width' is not permitted in the component type parameter of 'field'"]
        c.pair("C759", variant, [facet],
               module(record(declaration), before="integer :: width = 2\n"),
               "len=width", "len=2", declaration, messages,
               relation="The shared length selector contains width; any individual *2 suffix is already constant.")
    c.program("C759", "deferred_allocatable", ["deferred-length-boundaries"], """
        implicit none
        type :: record
            character(:), allocatable :: field
        end type
        type(record) :: value
        integer :: stat
        if (allocated(value%field)) error stop 1
        allocate(character(2) :: value%field, stat=stat)
        if (stat /= 0) error stop 2
        if (.not. allocated(value%field)) error stop 3
        value%field = 'AB'
        if (len(value%field) /= 2 .or. value%field /= 'AB') error stop 4
        deallocate(value%field, stat=stat)
        if (stat /= 0) error stop 5
    """)
    c.program("C759", "deferred_pointer", ["deferred-length-boundaries"], """
        implicit none
        type :: record
            character(:), pointer :: field
        end type
        type(record) :: value
        character(3), target :: target
        target = 'ABC'
        nullify(value%field)
        if (associated(value%field)) error stop 1
        value%field => target
        if (.not. associated(value%field)) error stop 2
        if (len(value%field) /= 3 .or. value%field /= 'ABC') error stop 3
        value%field = 'DEF'
        if (target /= 'DEF') error stop 4
        nullify(value%field)
    """)
    body = """module definitions
implicit none
type :: carrier
    integer, public :: payload
end type
type(carrier) :: a, b
type :: record
    procedure(character(len=merge(2,3,same_type_as(a,b)))), pointer, nopass :: action
end type
end module
"""
    c.pair("C759", "procedure_constant_inquiry", ["procedure-interface-parameter"], body,
           "merge(2,3,same_type_as(a,b))", "2",
           "procedure(character(len=merge(2,3,same_type_as(a,b)))), pointer, nopass :: action", [
               "SAME_TYPE_AS is not permitted in the component result length of 'action'",
               "Procedure component 'action' result parameter may not reference SAME_TYPE_AS",
           ], control_variant="procedure_parameter_repair",
           exclusions=["not constant", "nonconstant", "must be constant", "explicit interface required",
                       "requires an explicit interface", "data component '"],
           relation="The fixed-type inquiry and MERGE are constant, but the named inquiry is explicitly banned in a component specification expression.")


def integer_interface():
    return ("abstract interface\ninteger function iface()\nend function\nend interface\n")


def component_interface_source(declaration, dummy="class(record), intent(in) :: self",
                               parameters=False, before=""):
    header = "type :: record(n,m)\ninteger, len :: n,m\n" if parameters else "type :: record\n"
    members = "character(n) :: label\ninteger :: values(m)\n" if parameters else "integer :: payload\n"
    imports = "record, other" if "class(other)" in dummy else "record"
    if "procedure(callback)" in dummy:
        imports += ", callback"
    return ("module definitions\nimplicit none\n" + before + header + members + declaration
            + "\nend type\nabstract interface\nsubroutine iface(self)\nimport :: " + imports
            + "\n" + dummy + "\nend subroutine\nend interface\nend module\n")


def binding_source(dummy, parameters=False, before="", record_witness=False):
    header = "type :: record(n,m)\ninteger, len :: n,m\n" if parameters else "type :: record\n"
    members = "character(n) :: label\ninteger :: values(m)\n" if parameters else "integer :: payload\n"
    arguments = "self, witness" if record_witness else "self"
    witness = "class(record), intent(in) :: witness\n" if record_witness else ""
    return ("module definitions\nimplicit none\n" + before + header + members
            + "contains\nprocedure :: action\nend type\ncontains\n"
            + f"subroutine action({arguments})\n" + dummy + "\n"
            + witness + "end subroutine\nend module\n")


def procedure_declarations(c):
    zero = integer_interface()
    c.run("R741", "explicit_interface", ["explicit-interface"], """module definitions
implicit none
abstract interface
    integer function iface()
    end function
end interface
type :: record
    procedure(iface), pointer, nopass :: action => null()
end type
contains
integer function implementation()
implementation = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
if (associated(value%action)) error stop 1
value%action => implementation
if (.not. associated(value%action)) error stop 2
if (value%action() /= 17) error stop 3
end program
""")
    c.run("R741", "omitted_interface", ["omitted-interface"], {
        "target.f90": """subroutine target(tag)
implicit none
integer :: tag
tag = 17
end subroutine
""",
        source_name("R741"): """program p
implicit none
type :: record
    procedure(), pointer, nopass :: action
end type
type(record) :: value
external :: target
integer :: tag
tag = 0
nullify(value%action)
value%action => target
if (.not. associated(value%action)) error stop 1
call value%action(tag)
if (tag /= 17) error stop 2
end program
""",
    })
    c.run("R741", "typed_interface", ["typed-implicit-interface"], {
        "target.f90": """integer function target()
implicit none
target = 17
end function
""",
        source_name("R741"): """program p
implicit none
type :: record
    procedure(integer), pointer, nopass :: action
end type
type(record) :: value
integer, external :: target
nullify(value%action)
value%action => target
if (.not. associated(value%action)) error stop 1
if (value%action() /= 17) error stop 2
end program
""",
    })
    c.pair("R741", "missing_colons", ["separator-and-list"],
           module(record("procedure(iface), pointer, nopass action"), before=zero),
           "nopass action", "nopass :: action", "procedure(iface), pointer, nopass action", [
               "Missing :: before procedure component 'action'",
               "Procedure component attributes require a double-colon before 'action'",
           ])
    c.run("R741", "multiple_declarators", ["separator-and-list"],
          "module definitions\nimplicit none\n" + zero
          + record("procedure(iface), pointer, nopass :: first, second")
          + """contains
integer function first_target()
first_target = 11
end function
integer function second_target()
second_target = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
nullify(value%first, value%second)
value%first => first_target
value%second => second_target
if (.not. associated(value%first)) error stop 1
if (.not. associated(value%second)) error stop 2
if (value%first() /= 11 .or. value%second() /= 17) error stop 3
end program
""")
    for access in ("public", "private"):
        member = f"procedure(iface), pointer, nopass, {access} :: action"
        provider = ("module provider\nimplicit none\n" + zero + "type, public :: record\n"
                    + ("private\n" if access == "public" else "") + member + "\nend type\n"
                    "type(record) :: published\ncontains\nsubroutine initialize()\n"
                    "published%action => implementation\nend subroutine\n"
                    "integer function inspect()\nif (.not. associated(published%action)) error stop 1\n"
                    "inspect = published%action()\nend function\n"
                    "integer function implementation()\nimplementation = 17\nend function\nend module\n")
        call = ("if (.not. associated(published%action)) error stop 2\n"
                "if (published%action() /= 17) error stop 3\n" if access == "public" else
                "if (inspect() /= 17) error stop 2\n")
        c.run("R742", access, [access + "-access"], {
            "provider.f90": provider,
            source_name("R742"): "program p\nuse provider, only: published, initialize, inspect\n"
                                "implicit none\ncall initialize()\n" + call + "end program\n",
        })
    for variant, attributes, repeated, facet, needs_self in (
        ("public", "pointer, nopass, public, public", "public", "duplicate-access", False),
        ("private", "pointer, nopass, private, private", "private", "duplicate-access", False),
        ("pointer", "pointer, pointer, nopass", "pointer", "duplicate-pointer", False),
        ("nopass", "pointer, nopass, nopass", "nopass", "duplicate-nopass", False),
        ("pass", "pointer, pass, pass", "pass", "duplicate-pass", True),
        ("named_pass", "pointer, pass(self), pass(self)", "pass(self)", "duplicate-pass", True),
    ):
        declaration = f"procedure(iface), {attributes} :: action"
        body = (component_interface_source(declaration) if needs_self else
                module(record(declaration), before=zero))
        c.pair("C760", variant, [facet], body, repeated + ", " + repeated, repeated,
               declaration, [
                   f"Procedure component 'action' has duplicate {repeated.upper()} attributes",
                   f"Repeated {repeated.upper()} attribute on procedure pointer component 'action'",
               ], exclusions=["data component", "type-bound", "dummy argument '"])
    c.pair("C761", "missing_pointer", ["pointer-required"],
           module(record("procedure(iface), nopass :: action"), before=zero),
           "procedure(iface), nopass", "procedure(iface), pointer, nopass",
           "procedure(iface), nopass :: action", [
               "Procedure component 'action' must have the POINTER attribute",
               "Procedure pointer component 'action' is missing POINTER",
           ], control_variant="pointer_repair")
    for variant, interface, before, facet in (
        ("omitted_interface", "", "", "implicit-interface"),
        ("typed_interface", "integer", "", "implicit-interface"),
        ("zero_arguments", "iface", zero, "zero-argument-explicit-interface"),
    ):
        declaration = f"procedure({interface}), pointer :: action"
        cause = ("Procedure component 'action' with no dummy arguments requires NOPASS" if interface == "iface"
                 else "Procedure component 'action' with an implicit interface requires NOPASS")
        c.pair("C762", variant, [facet], module(record(declaration), before=before),
               ", pointer ::", ", pointer, nopass ::", declaration, [cause],
               exclusions=(["implicit interface"] if interface == "iface" else ["no dummy arguments"]))
    named = """module definitions
implicit none
type :: record
    integer :: payload
    procedure(iface), pointer, pass(absent) :: action
end type
abstract interface
    subroutine iface(tag,self)
        import :: record
        integer, intent(in) :: tag
        class(record), intent(in) :: self
    end subroutine
end interface
end module
"""
    c.pair("C763", "missing_name", ["dummy-name-existence"], named,
           "pass(absent)", "pass(self)", "procedure(iface), pointer, pass(absent) :: action", [
               "PASS name 'absent' is not a dummy argument of procedure component 'action'",
               "Procedure component 'action' has no dummy argument named 'absent'",
           ], exclusions=["dummy argument 'tag'"],
           relation="The component selects absent; the explicit interface has only tag and the qualifying self.")
    for variant, passing in (("bare", "pass"), ("named", "pass(self)")):
        declaration = f"procedure(iface), pointer, {passing}, nopass :: action"
        body = component_interface_source(declaration)
        negative = c.pair("C764", variant, [variant + "-pass-conflict"], body,
                          ", nopass", "", declaration, [
                              "Procedure component 'action' cannot have both PASS and NOPASS",
                              "PASS and NOPASS attributes conflict for procedure component 'action'",
                          ], exclusions=["duplicate", "type-bound"])
        c.extra_repair(negative, variant + "_nopass_repair", body, ", " + passing, "")


def passing_program(component=True, passing="", named=False, optional=False,
                    target=False, sequence=False):
    self_type = "type(record)" if sequence else "class(record)"
    self_attrs = ", optional" if optional else ", target" if target else ""
    self_decl = self_type + self_attrs + ", intent(in) :: self"
    args = "tag,self" if named else "self,tag"
    declarations = self_decl + "\ninteger, intent(inout) :: tag\n"
    body = ("if (.not. present(self)) error stop 5\n" if optional else "")
    body += "if (self%payload /= 11 .or. tag /= 17) error stop 6\ntag = 19\n"
    attributes = ", " + passing if passing else ""
    type_body = "type :: record\n" + ("sequence\n" if sequence else "") + "integer :: payload\n"
    if component:
        type_body += "procedure(iface), pointer" + attributes + " :: action\nend type\n"
        type_body += ("abstract interface\nsubroutine iface(" + args + ")\nimport :: record\n"
                      + declarations + "end subroutine\nend interface\n")
    else:
        type_body += "contains\nprocedure" + attributes + " :: action => implementation\nend type\n"
    module_body = ("module definitions\nimplicit none\n" + type_body + "contains\n"
                   "subroutine implementation(" + args + ")\n" + declarations + body
                   + "end subroutine\nend module\n")
    main = ("program p\nuse definitions\nimplicit none\ntype(record)"
            + (", target" if target else "") + " :: value\ninteger :: tag\n"
            "value%payload = 11\ntag = 17\n")
    if component:
        main += ("nullify(value%action)\nvalue%action => implementation\n"
                 "if (.not. associated(value%action)) error stop 1\n")
    main += ("call value%action(tag)\nif (tag /= 19 .or. value%payload /= 11) error stop 2\nend program\n")
    return module_body + main


def passing_modes(c):
    for component, variant in ((True, "component_nopass"), (False, "binding_nopass")):
        field = ("procedure(iface), pointer, nopass :: action" if component else
                 "contains\nprocedure, nopass :: action => implementation")
        interface = ("abstract interface\ninteger function iface(tag)\ninteger, intent(in) :: tag\n"
                     "end function\nend interface\n" if component else "")
        code = ("module definitions\nimplicit none\n" + interface
                + "type :: record\ninteger :: payload\n" + field + "\nend type\ncontains\n"
                "integer function implementation(tag)\ninteger, intent(in) :: tag\n"
                "if (tag /= 17) error stop 5\nimplementation = 19\nend function\nend module\n"
                "program p\nuse definitions\nimplicit none\ntype(record) :: value\n"
                "value%payload = 11\n")
        if component:
            code += ("nullify(value%action)\nvalue%action => implementation\n"
                     "if (.not. associated(value%action)) error stop 1\n")
        code += "if (value%action(17) /= 19) error stop 2\nif (value%payload /= 11) error stop 3\nend program\n"
        c.run("S7.5.4.5-001", variant, [variant.replace("_", "-")], code)
    for component, kind in ((True, "component"), (False, "binding")):
        for attribute, suffix, facet in (("", "default", "default"), ("pass", "pass", "bare-pass")):
            c.run("S7.5.4.5-002", kind + "_" + suffix, [kind + "-" + facet],
                  passing_program(component=component, passing=attribute))
        c.run("S7.5.4.5-003", kind + "_named", [kind + "-second-dummy"],
              passing_program(component=component, passing="pass(self)", named=True))
    c.run("C763", "case_equivalent", ["case-equivalent-name"],
          passing_program(passing="pass(sElF)", named=True))
    c.run("S7.5.4.5-003", "two_binding_contexts", ["shared-procedure-contexts"], """module definitions
implicit none
type :: first_type
    integer :: payload
contains
    procedure, pass(a) :: action => implementation
end type
type :: second_type
    integer :: payload
contains
    procedure, pass(b) :: action => implementation
end type
contains
integer function implementation(a,b)
class(first_type), intent(in) :: a
class(second_type), intent(in) :: b
if (a%payload /= 11 .or. b%payload /= 17) error stop 5
implementation = 19
end function
end module
program p
use definitions
implicit none
type(first_type) :: first
type(second_type) :: second
first%payload = 11
second%payload = 17
if (first%action(second) /= 19) error stop 1
if (second%action(first) /= 19) error stop 2
end program
""")


def passed_object_constraints(c):
    callback = "abstract interface\nsubroutine callback()\nend subroutine\nend interface\n"
    declaration = "procedure(iface), pointer :: action"
    dummy = "procedure(callback) :: self"
    c.pair("C765", "procedure_dummy", ["dummy-data-object"],
           component_interface_source(declaration, dummy, before=callback),
           dummy, "class(record) :: self", declaration, [
               "Passed-object dummy 'self' of 'action' must be a data object, not a procedure",
               "Procedure dummy 'self' cannot be the passed-object dummy of 'action'",
           ], end_anchor=dummy, relation="The component's explicit interface selects its sole procedure dummy self.")
    variants = [
        ("array_self", "scalar", "class(record), intent(in) :: self(:)",
         "class(record), intent(in) :: self",
         ["Passed-object dummy 'self' of 'action' must be scalar",
          "Passed-object dummy argument of 'action' at (1) must be scalar"]),
        ("pointer_self", "nonpointer", "class(record), pointer, intent(in) :: self",
         "class(record), intent(in) :: self",
         ["Passed-object dummy 'self' of 'action' must not have POINTER",
          "Passed-object dummy argument of 'action' at (1) must not be POINTER"]),
        ("allocatable_self", "nonallocatable", "class(record), allocatable, intent(in) :: self",
         "class(record), intent(in) :: self",
         ["Passed-object dummy 'self' of 'action' must not have ALLOCATABLE",
          "Passed-object dummy argument of 'action' at (1) must not be ALLOCATABLE"]),
        ("other_type", "same-declared-type", "class(other), intent(in) :: self",
         "class(record), intent(in) :: self",
         ["Passed-object dummy 'self' of 'action' must have declared type 'record', not 'other'",
          "Argument 'self' of 'action' with PASS(self) at (1) must be of the derived-type 'record'"]),
        ("nonpolymorphic", "extensible-polymorphic", "type(record), intent(in) :: self",
         "class(record), intent(in) :: self",
         ["Passed-object dummy 'self' of 'action' must be polymorphic because 'record' is extensible",
          "Non-polymorphic passed-object dummy argument of 'action' at (1)"]),
        ("value_self", "no-value", "class(record), value, intent(in) :: self",
         "class(record), intent(in) :: self",
         ["Passed-object dummy 'self' of 'action' must not have VALUE",
          "Passed-object dummy argument of 'action' at (1) must not have the VALUE attribute"]),
    ]
    for variant, facet, bad, good, messages in variants:
        before = "type :: other\ninteger :: payload\nend type\n" if variant == "other_type" else ""
        for component, kind in ((True, "component"), (False, "binding")):
            record_witness = variant == "other_type" and not component
            inputs = (component_interface_source(declaration, bad, before=before) if component else
                      binding_source(bad, before=before, record_witness=record_witness))
            anchor = declaration if component else "procedure :: action"
            relation = f"The new {kind} action selects self; only self's {facet} property is repaired."
            if record_witness:
                relation += (" The separate non-passed CLASS(record) witness satisfies C784 in both sources;"
                             " self remains first and selected by default PASS.")
            c.pair("C765", variant + "_" + kind, [facet], inputs, bad, good, anchor,
                   messages, end_anchor=bad,
                   relation=relation)
    for parameter, selector, repaired in (("n", "2,*", "*,*"), ("m", "*,3", "*,*")):
        bad = f"class(record({selector})), intent(in) :: self"
        good = f"class(record({repaired})), intent(in) :: self"
        for component, kind in ((True, "component"), (False, "binding")):
            body = (component_interface_source(declaration, bad, parameters=True) if component else
                    binding_source(bad, parameters=True))
            c.pair("C765", "length_" + parameter + "_" + kind, ["all-lengths-assumed"],
                   body, bad, good, declaration if component else "procedure :: action", [
                       f"Length parameter '{parameter}' of passed-object dummy 'self' in 'action' must be assumed",
                       f"Passed-object dummy 'self' of 'action' has nonassumed length parameter '{parameter}'",
                   ], end_anchor=bad,
                   relation=f"Only LEN {parameter} is explicit; the other LEN parameter is already assumed.",
                   exclusions=[f"nonassumed length parameter '{'m' if parameter == 'n' else 'n'}'"])
    c.run("C765", "assumed_lengths", ["all-lengths-assumed"], """module definitions
implicit none
type :: record(n,m)
    integer, len :: n,m
    character(n) :: label
    integer :: values(m)
    procedure(iface), pointer :: action
end type
abstract interface
    subroutine iface(self,tag)
        import :: record
        class(record(*,*)), intent(in) :: self
        integer, intent(out) :: tag
    end subroutine
end interface
contains
subroutine implementation(self,tag)
class(record(*,*)), intent(in) :: self
integer, intent(out) :: tag
if (self%n /= 2 .or. self%m /= 3) error stop 5
if (self%label /= 'AB') error stop 6
if (any(self%values /= [11,13,17])) error stop 7
tag = 19
end subroutine
end module
program p
use definitions
implicit none
type(record(2,3)) :: value
integer :: tag
value%label = 'AB'
value%values = [11,13,17]
nullify(value%action)
value%action => implementation
if (.not. associated(value%action)) error stop 1
call value%action(tag)
if (tag /= 19) error stop 2
end program
""")
    sequence = """module definitions
implicit none
type :: record
    sequence
    integer, public :: payload
    procedure(iface), pointer, public :: action
end type
type(record) :: seed
abstract interface
    subroutine iface(self)
        import :: seed
        classof(seed), intent(in) :: self
    end subroutine
end interface
end module
"""
    c.pair("C765", "classof_sequence", ["nonextensible-nonpolymorphic"], sequence,
           "classof(seed)", "typeof(seed)", "procedure(iface), pointer, public :: action", [
               "Passed-object dummy 'self' of 'action' must be nonpolymorphic because 'record' is not extensible",
               "Polymorphic passed-object dummy 'self' is not permitted for SEQUENCE type 'record'",
           ], end_anchor="classof(seed), intent(in) :: self", control_variant="typeof_sequence_repair",
           relation="Complete public-component SEQUENCE definition, then seed, then the IMPORT seed interface; only CLASSOF changes to TYPEOF.",
           exclusions=["CLASS must specify an extensible", "CLASS entity must be of extensible",
                       "CLASS type specifier must specify an extensible"])
    c.run("C765", "sequence_nonpolymorphic", ["nonextensible-nonpolymorphic"],
          passing_program(sequence=True))
    c.run("C765", "optional_self", ["other-dummy-attributes"], passing_program(optional=True))
    c.run("C765", "target_self", ["other-dummy-attributes"],
          passing_program(component=False, target=True))


def shared_properties(c):
    c.program("S7.5.4.1-001", "shared_parameters", ["shared-type-and-parameters"], """
        implicit none
        type :: record
            character(len=3) :: first, second
            integer :: left, right
        end type
        type(record) :: value
        value%first = 'ABC'
        value%second = 'DEF'
        value%left = 11
        value%right = 13
        if (len(value%first) /= 3 .or. len(value%second) /= 3) error stop 1
        if (value%first /= 'ABC' .or. value%second /= 'DEF') error stop 2
        if (value%left /= 11 .or. value%right /= 13) error stop 3
    """)
    c.program("S7.5.4.1-001", "shared_allocatable", ["shared-attributes"], """
        implicit none
        type :: record
            integer, allocatable :: first(:), second(:)
        end type
        type(record) :: value
        integer :: stat
        if (allocated(value%first) .or. allocated(value%second)) error stop 1
        allocate(value%first(2), stat=stat)
        if (stat /= 0) error stop 2
        if (.not. allocated(value%first)) error stop 3
        if (allocated(value%second)) error stop 4
        value%first = [11,13]
        if (any(value%first /= [11,13])) error stop 5
        allocate(value%second(3), stat=stat)
        if (stat /= 0) error stop 6
        if (.not. allocated(value%second)) error stop 7
        value%second = [17,19,23]
        if (size(value%first) /= 2 .or. size(value%second) /= 3) error stop 8
        if (any(value%second /= [17,19,23])) error stop 9
        deallocate(value%first, value%second, stat=stat)
        if (stat /= 0) error stop 10
    """)


def array_components(c):
    c.program("S7.5.4.2-001", "individual", ["individual-shape"], """
        implicit none
        type :: record
            integer :: field(-1:0,2:4)
        end type
        type(record) :: value
        value%field = 11
        value%field(0,4) = 13
        if (rank(value%field) /= 2) error stop 1
        if (any(shape(value%field) /= [2,3])) error stop 2
        if (any(lbound(value%field) /= [-1,2])) error stop 3
        if (any(ubound(value%field) /= [0,4])) error stop 4
        if (value%field(-1,2) /= 11 .or. value%field(0,4) /= 13) error stop 5
    """)
    c.program("S7.5.4.2-001", "dimension", ["shared-dimension"], """
        implicit none
        type :: record
            integer, dimension(2,3) :: first, second
        end type
        type(record) :: value
        value%first = 11
        value%second = 13
        if (rank(value%first) /= 2 .or. rank(value%second) /= 2) error stop 1
        if (any(shape(value%first) /= [2,3])) error stop 2
        if (any(shape(value%second) /= [2,3])) error stop 3
        if (any(lbound(value%first) /= [1,1])) error stop 4
        if (any(lbound(value%second) /= [1,1])) error stop 5
        if (any(value%first /= 11) .or. any(value%second /= 13)) error stop 6
    """)
    c.program("S7.5.4.2-001", "rank_override", ["individual-rank-override"], """
        implicit none
        type :: record
            integer, dimension(2,3) :: local(4), inherited
        end type
        type(record) :: value
        value%local = [11,13,17,19]
        value%inherited = 23
        if (rank(value%local) /= 1 .or. size(value%local) /= 4) error stop 1
        if (rank(value%inherited) /= 2) error stop 2
        if (any(shape(value%inherited) /= [2,3])) error stop 3
        if (any(value%local /= [11,13,17,19])) error stop 4
        if (any(value%inherited /= 23)) error stop 5
    """)
    c.program("S7.5.4.2-001", "bound_override", ["individual-bound-override"], """
        implicit none
        type :: record
            integer, dimension(-1:1) :: local(2:4), inherited
        end type
        type(record) :: value
        value%local = [11,13,17]
        value%inherited = [19,23,29]
        if (rank(value%local) /= 1 .or. rank(value%inherited) /= 1) error stop 1
        if (size(value%local) /= 3 .or. size(value%inherited) /= 3) error stop 2
        if (lbound(value%local,1) /= 2 .or. ubound(value%local,1) /= 4) error stop 3
        if (lbound(value%inherited,1) /= -1 .or. ubound(value%inherited,1) /= 1) error stop 4
        if (any(value%local /= [11,13,17])) error stop 5
        if (any(value%inherited /= [19,23,29])) error stop 6
    """)
    c.program("S7.5.4.2-001", "zero_extent", ["zero-extent"], """
        implicit none
        type :: record
            integer :: field(2:1), other
        end type
        type(record) :: value
        value%other = 11
        if (rank(value%field) /= 1 .or. size(value%field) /= 0) error stop 1
        if (any(shape(value%field) /= [0])) error stop 2
        if (value%other /= 11) error stop 3
    """)


def coarray_components(c):
    for variant, declaration, allocations, checks, facet in (
        ("individual", "integer, allocatable :: field[:]",
         [("field", "[0:*]")],
         "if (size(lcobound(value%field)) /= 1) error stop 21\n"
         "if (any(lcobound(value%field) /= [0])) error stop 22\n"
         "value%field = 11\nif (value%field /= 11) error stop 23\n", "individual-corank"),
        ("codimension", "integer, allocatable, codimension[:,:] :: field",
         [("field", "[0:0,1:*]")],
         "if (size(lcobound(value%field)) /= 2) error stop 21\n"
         "if (any(lcobound(value%field) /= [0,1])) error stop 22\n"
         "value%field = 11\nif (value%field /= 11) error stop 23\n", "shared-corank"),
        ("corank_override", "integer, allocatable, codimension[:,:] :: local[:], inherited",
         [("local", "[0:*]"), ("inherited", "[0:0,1:*]")],
         "if (size(lcobound(value%local)) /= 1) error stop 21\n"
         "if (size(lcobound(value%inherited)) /= 2) error stop 22\n"
         "if (any(lcobound(value%local) /= [0])) error stop 23\n"
         "if (any(lcobound(value%inherited) /= [0,1])) error stop 24\n"
         "value%local = 11\nvalue%inherited = 13\n"
         "if (value%local /= 11 .or. value%inherited /= 13) error stop 25\n", "individual-corank-override"),
        ("rank_and_corank", "integer, allocatable, codimension[:,:] :: field(:)",
         [("field", "(2)[0:0,1:*]")],
         "value%field = [11,13]\n"
         "if (rank(value%field) /= 1 .or. size(value%field) /= 2) error stop 21\n"
         "if (size(lcobound(value%field)) /= 2) error stop 22\n"
         "if (any(lcobound(value%field) /= [0,1])) error stop 23\n"
         "if (any(value%field /= [11,13])) error stop 24\n", "array-rank-independent"),
    ):
        body = ("implicit none\n" + record(declaration)
                + "type(record), save :: value\ninteger :: stat\n"
                "if (num_images() /= 1) error stop 1\n")
        for field, allocation in allocations:
            body += (f"if (allocated(value%{field})) error stop 2\n"
                     f"allocate(value%{field}{allocation}, stat=stat)\n"
                     "if (stat /= 0) error stop 3\n"
                     f"if (.not. allocated(value%{field})) error stop 4\n")
        body += checks
        for field, _ in allocations:
            body += (f"deallocate(value%{field}, stat=stat)\n"
                     "if (stat /= 0) error stop 31\n"
                     f"if (allocated(value%{field})) error stop 32\n")
        c.program("S7.5.4.3-001", variant, [facet], body, coarray=True)


def qualified_diagnostic_routes(c):
    routes = {}
    nonfatal = {}

    def add(rule, variants, *messages):
        for variant in variants.split():
            routes.setdefault(case_id(rule, variant, True), []).extend(messages)

    add("C749", "forward_value",
        "Derived type 'later_type' not found", "Derived type `later_type` is not defined")
    add("C749", "self_value",
        "Recursive use of the derived type requires POINTER or ALLOCATABLE",
        "Derived type `record` is not defined")
    add("C750", "pointer_local pointer_dimension",
        "Array pointer component 'field' must have deferred shape",
        "Pointer array component of structure at (1) must have a deferred shape")
    add("C750", "allocatable_local allocatable_dimension",
        "Allocatable array component 'field' must have deferred shape",
        "Allocatable component of structure at (1) must have a deferred shape")
    add("C751", "explicit_suffix explicit_codimension",
        "'field' is an ALLOCATABLE coarray and must have a deferred coshape",
        "A coarray with the `allocatable` attribute must have a deferred coshape (every codimension written as `:`)")
    add("C751", "missing_allocatable_suffix missing_allocatable_codimension",
        "Component 'field' is a coarray and must have the ALLOCATABLE attribute")
    add("C752", "c_ptr c_ptr_renamed c_funptr c_funptr_renamed",
        "Component 'field' at (1) of TYPE(C_PTR) or TYPE(C_FUNPTR) shall not be a coarray")
    add("C752", "c_ptr c_ptr_renamed c_funptr c_funptr_renamed team_type team_type_renamed",
        "Coarray 'field' may not have type TEAM_TYPE, C_PTR, or C_FUNPTR")
    add("C753", "pointer allocatable array",
        "Component 'field' at (1) with coarray component shall be a nonpointer, nonallocatable scalar")
    add("C753", "allocatable array",
        "Allocatable or array component 'field' may not have a coarray ultimate component '%co'")
    add("C753", "pointer", "Pointer 'field' may not have a coarray potential component '%co'")
    add("C754", "individual dimension",
        "Component array 'field' without ALLOCATABLE or POINTER attribute must have explicit shape",
        "Array component of structure at (1) must have an explicit shape")
    add("C755", "lower_variable upper_variable",
        "Variable 'width' cannot appear in the expression at (1)",
        "Variable `width` cannot appear in the expression as it is not a constant")
    add("C755", "specification_function",
        "Invalid specification expression: reference to function 'extent' not allowed for derived type components or type parameter values")
    add("C756", "scalar array", "'field' may not have both the POINTER and ALLOCATABLE attributes")
    add("C757", "scalar_pointer ordinary_array",
        "Component 'field' at (1) has the CONTIGUOUS attribute but is not an array pointer")
    contiguous = "CONTIGUOUS component 'field' should be an array with the POINTER attribute [-Wredundant-contiguous]"
    add("C757", "scalar_pointer ordinary_array", contiguous)
    for variant in ("scalar_pointer", "ordinary_array"):
        nonfatal[case_id("C757", variant, True)] = contiguous
    add("C758", "integer_suffix derived_suffix",
        "A length specifier cannot be used to declare the non-character entity 'field'",
        "length specifier is only valid for character type")
    add("C759", "host_variable overridden_length",
        "Variable 'width' cannot appear in the expression at (1)")
    add("C761", "missing_pointer",
        "Procedure component 'action' must have POINTER attribute",
        "POINTER attribute is required for procedure pointer component at (1)")
    add("C762", "omitted_interface typed_interface",
        "Procedure component 'action' must have NOPASS attribute or explicit interface")
    add("C762", "zero_arguments",
        "Procedure component 'action' with no dummy arguments must have NOPASS attribute",
        "Procedure pointer component 'action' with PASS at (1) must have at least one argument")
    add("C763", "missing_name",
        "Procedure pointer component 'action' with PASS(absent) at (1) has no argument 'absent'",
        "'absent' is not a dummy argument of procedure interface 'iface'")
    for kind in ("component", "binding"):
        add("C765", "array_self_" + kind,
            "Passed-object dummy argument 'self' of procedure 'action' must be scalar")
        add("C765", "allocatable_self_" + kind,
            "Passed-object dummy argument 'self' of procedure 'action' may not have the ALLOCATABLE attribute")
        add("C765", "nonpolymorphic_" + kind,
            "Passed-object dummy argument 'self' of procedure 'action' must be polymorphic because 'record' is extensible")
        add("C765", "other_type_" + kind,
            "Passed-object dummy argument 'self' of procedure 'action' must be of type 'record' but is 'CLASS(other)'")
        add("C765", "value_self_" + kind,
            "Passed-object dummy argument 'self' of procedure 'action' may not have the VALUE attribute")
        for parameter in ("n", "m"):
            add("C765", f"length_{parameter}_{kind}",
                f"Passed-object dummy argument 'self' of procedure 'action' has non-assumed length parameter '{parameter}'")
    add("C765", "array_self_component",
        "Argument 'self' of 'action' with PASS(self) at (1) must be scalar")
    add("C765", "allocatable_self_component",
        "Argument 'self' of 'action' with PASS(self) at (1) may not be ALLOCATABLE")
    add("C765", "pointer_self_component",
        "Argument 'self' of 'action' with PASS(self) at (1) may not have the POINTER attribute",
        "Passed-object dummy argument 'self' of procedure 'action' used as procedure pointer component interface may not have the POINTER attribute")
    add("C765", "other_type_component",
        "Argument 'self' of 'action' with PASS(self) at (1) must be of the derived type 'record'")
    add("C765", "procedure_dummy",
        "Passed-object dummy argument 'self' of procedure 'action' must be a data object")
    pointer_warning = "Passed-object dummy argument 'self' of procedure 'action' that is an INTENT(IN) POINTER is not standard [-Wpointer-pass-object]"
    add("C765", "pointer_self_binding", pointer_warning)
    nonfatal[case_id("C765", "pointer_self_binding", True)] = pointer_warning
    for name, messages in routes.items():
        path = ROOT / c.cases[name]["path"]
        manifest = json.loads(c.files[path])
        diagnostic = manifest["expect"]["diagnostic"]
        diagnostic["contains_any"] = list(dict.fromkeys(diagnostic["contains_any"] + messages))
        if name in nonfatal:
            diagnostic["allow_nonfatal"] = [
                dict(compiler="flang", severity="portability", equals_any=[nonfatal[name]])]
        c.files[path] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")


def build_corpus():
    corpus = Corpus()
    basic_declarations(corpus)
    data_types(corpus)
    shapes_and_coarray_constraints(corpus)
    component_expressions(corpus)
    attribute_conflicts_and_lengths(corpus)
    procedure_declarations(corpus)
    passing_modes(corpus)
    passed_object_constraints(corpus)
    shared_properties(corpus)
    array_components(corpus)
    coarray_components(corpus)
    qualified_diagnostic_routes(corpus)
    return corpus.files, corpus.cases, corpus.repairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, cases, _ = build_corpus()
    stale = []
    for path, content in files.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if stale:
        parser.exit(1, "Stale data-component fixtures:\n" + "\n".join(stale) + "\n")
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(cases)} executions.")


if __name__ == "__main__":
    main()
