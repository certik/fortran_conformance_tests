#!/usr/bin/env python3
"""Generate finite derived-definition fixtures without invoking a compiler."""

import argparse
import json
from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_CAUSES = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported feature",
    "not supported yet", "not yet supported", "not currently supported",
    "implementation limitation", "ASR verify", "ASR verifier", "internal compiler error",
    "unexpected end of file", "unexpected eof", "missing end", "obsolescent",
    "obsolete feature", "out of memory", "overflow",
]


def text(value):
    return textwrap.dedent(value).strip("\n") + "\n"


def case_id(rule, variant, invalid=False):
    return (rule.replace(".", "_").replace("-", "_")
            + ("_invalid" if invalid else "_valid") + "__" + variant)


class Corpus:
    def __init__(self):
        self.files = {}
        self.cases = {}
        self.repairs = {}

    def put(self, relative, content):
        path = ROOT / relative
        if path in self.files:
            raise ValueError(f"duplicate output: {relative}")
        self.files[path] = content.encode("ascii") if isinstance(content, str) else content

    def record(self, name, rule, facets, phase, path, evidence, **extra):
        if name in self.cases:
            raise ValueError(f"duplicate case: {name}")
        self.cases[name] = dict(rule=rule, facets=list(facets), phase=phase, path=path,
                                evidence=evidence, standard="f2023", **extra)

    def program(self, rule, variant, facets, body):
        name = case_id(rule, variant)
        path = f"tests/clause07/{name}.f90"
        evidence = "effect" if rule.startswith("S") else "positive-control"
        header = (f"! rule: {rule}\n! covers: {' '.join(facets)}\n"
                  f"! evidence: {evidence}\n! standard: f2023\n")
        self.put(path, header + "program p\n" + text(body) + "end program\n")
        self.record(name, rule, facets, "run", path, evidence, coarray=False)

    def fixture(self, name, rule, facets, inputs, phase="compile", diagnostic=None,
                coarray=False, relation="", evidence=None):
        folder = "tests/fixtures/derived_definition_" + name.lower()
        if evidence is None:
            evidence = "effect" if diagnostic or rule.startswith("S") else "positive-control"
        steps = []
        for filename, content in inputs.items():
            step = Path(filename).stem
            steps.append(dict(id=step, source=filename, language="fortran", form="free",
                              output=step + ".o", depends_on=[s["id"] for s in steps]))
            self.put(folder + "/" + filename, content)
        manifest = dict(schema_version=1, id=name, rule=rule, facets=list(facets),
                        evidence=evidence, standard="f2023", files=list(inputs), build=steps,
                        expect=dict(phase=phase, outcome="diagnose" if diagnostic else "success"))
        if coarray:
            manifest["requires"] = ["coarray"]
        if phase == "compile":
            manifest["expect"]["step"] = steps[-1]["id"]
        else:
            manifest["link"] = dict(objects=[s["output"] for s in steps], output="program")
            manifest["expect"]["exit_code"] = 0
        if diagnostic:
            manifest["expect"]["diagnostic"] = diagnostic
        path = folder + "/fixture.json"
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        self.record(name, rule, facets, phase, path, evidence, coarray=coarray,
                    source_relation=relation)

    def compile(self, rule, variant, facets, body, coarray=False):
        self.fixture(case_id(rule, variant), rule, facets, {"source.f90": text(body)},
                     coarray=coarray)

    def run(self, rule, variant, facets, inputs, evidence=None):
        self.fixture(case_id(rule, variant), rule, facets,
                     {name: text(content) for name, content in inputs.items()}, phase="run",
                     evidence=evidence)

    def pair(self, rule, variant, facets, inputs, wrong, repaired, anchor, messages,
             edit_file="source.f90", anchor_file="source.f90", end_anchor=None,
             relation="", coarray=False, control_name=None, control_phase="compile",
             nonfatal=(), exclusions=()):
        inputs = {name: text(content) for name, content in inputs.items()}
        original = inputs[edit_file]
        if original.count(wrong) != 1 or wrong == repaired:
            raise ValueError(f"{rule}/{variant}: repair must select one exact source span")
        lines = inputs[anchor_file].splitlines()
        matches = [i for i, line in enumerate(lines, 1) if line.strip() == anchor]
        if len(matches) != 1:
            raise ValueError(f"{rule}/{variant}: diagnostic anchor is not unique: {anchor}")
        diagnostic = dict(file=anchor_file, line=matches[0],
                          contains_any=list(messages),
                          excludes_any=list(EXCLUDED_CAUSES) + list(exclusions))
        if nonfatal:
            diagnostic["allow_nonfatal"] = [dict(compiler="flang", severity="warning",
                                                 equals_any=list(nonfatal))]
        if end_anchor:
            ends = [i for i, line in enumerate(lines, 1) if line.strip() == end_anchor]
            if len(ends) != 1 or ends[0] < matches[0] or not relation:
                raise ValueError(f"{rule}/{variant}: invalid source relation")
            diagnostic["end_line"] = ends[0]
        negative = case_id(rule, variant, invalid=True)
        positive = control_name or case_id(rule, variant + "_repair")
        self.fixture(negative, rule, facets, inputs, diagnostic=diagnostic,
                     coarray=coarray, relation=relation)
        good = dict(inputs)
        good[edit_file] = original.replace(wrong, repaired, 1)
        self.fixture(positive, rule, facets, good, phase=control_phase,
                     coarray=coarray, relation=relation)
        self.repairs[negative] = dict(control=positive, file=edit_file, wrong=wrong,
                                      repaired=repaired, relation=relation,
                                      bad_source=original, control_phase=control_phase)


def ordinary_definitions(c):
    c.compile("R726", "empty", ["empty-definition"], """
        module definitions
        implicit none
        type :: record
        end type
        end module
    """)
    c.run("R726", "parameters", ["parameter-part"], {"source.f90": """
        module definitions
        implicit none
        type :: record(k,n)
            integer, kind :: k = 1
            integer, len :: n = 2
            private
            integer :: payload(n)
        end type
        contains
        subroutine check()
            type(record(1,2)) :: value
            value%payload = [11,13]
            if (value%k /= 1 .or. value%n /= 2) error stop 1
            if (size(value%payload) /= 2) error stop 2
            if (any(value%payload /= [11,13])) error stop 3
        end subroutine
        end module
        program p
        use definitions, only: check
        implicit none
        call check()
        end program
    """})
    c.run("R726", "components", ["component-part"], {"source.f90": """
        module definitions
        implicit none
        abstract interface
            integer function answer_interface()
            end function
        end interface
        type :: record
            integer :: payload
            procedure(answer_interface), pointer, nopass :: answer
        end type
        contains
        integer function answer_implementation()
            answer_implementation = 17
        end function
        end module
        program p
        use definitions
        implicit none
        type(record) :: value
        value%payload = 11
        value%answer => answer_implementation
        if (.not. associated(value%answer)) error stop 1
        if (value%payload /= 11) error stop 2
        if (value%answer() /= 17) error stop 3
        end program
    """})
    c.compile("R726", "empty_binding_part", ["binding-part"], """
        module definitions
        implicit none
        type :: record
        contains
        end type
        end module
    """)
    c.run("R726", "binding", ["binding-part"], {"source.f90": """
        module definitions
        implicit none
        type :: record
            integer :: payload
        contains
            procedure, nopass :: answer
        end type
        contains
        integer function answer()
            answer = 17
        end function
        end module
        program p
        use definitions
        implicit none
        type(record) :: value
        value%payload = 11
        if (value%payload /= 11 .or. value%answer() /= 17) error stop 1
        end program
    """})
    c.pair("R726", "late_parameter", ["parameter-ordering"], {"source.f90": """
        module definitions
        implicit none
        type :: record(k)
            integer :: payload
            integer, kind :: k = 1
        end type
        end module
    """}, "integer :: payload\n    integer, kind :: k = 1",
           "integer, kind :: k = 1\n    integer :: payload",
           "integer, kind :: k = 1", [
               "Type parameter 'k' must be defined before components of 'record'",
               "Type parameter definitions must appear before component declarations",
           ], relation="The parameter definition is after the first component; only those adjacent statements are exchanged.")
    c.pair("R726", "late_component_private", ["private-ordering"], {"source.f90": """
        module definitions
        implicit none
        type :: record
            integer :: payload
            private
        end type
        end module
    """}, "integer :: payload\n    private", "private\n    integer :: payload", "private", [
        "PRIVATE statement in the component part must precede component declarations",
        "PRIVATE statement at (1) must precede structure components",
    ], relation="Only the component PRIVATE statement moves before the first component; there is no binding part.")
    c.pair("R726", "component_after_contains", ["component-binding-ordering"], {"source.f90": """
        module definitions
        implicit none
        type :: record
        contains
            integer :: payload
        end type
        end module
    """}, "contains\n    integer :: payload", "    integer :: payload\ncontains",
           "integer :: payload", [
               "Data component 'payload' may not appear in the type-bound procedure part",
               "Component declaration must precede CONTAINS in derived type 'record'",
               "Components in TYPE at (1) must precede CONTAINS",
           ], relation="Move only the integer component before CONTAINS, retaining the legal empty binding part.")
    for variant, header, facet in (
        ("bare", "type record", "bare-header"),
        ("colons", "type :: record", "double-colon-header"),
    ):
        c.program("R727", variant, [facet], f"""
            implicit none
            {header}
                integer :: payload
            end type
            type(record) :: value
            value%payload = 11
            if (value%payload /= 11) error stop 1
        """)
    c.pair("R727", "missing_colons", ["attribute-needs-colons"], {"source.f90": """
        module definitions
        implicit none
        type, abstract record
            integer :: payload
        end type
        end module
    """}, "abstract record", "abstract :: record", "type, abstract record", [
        "Derived type attributes require a double-colon before the type name",
        "Missing :: after ABSTRACT in derived-type-stmt",
        "Expected :: in TYPE definition at (1)",
    ])
    c.pair("R727", "empty_parameter_list", ["nonempty-parameter-list"], {"source.f90": """
        module definitions
        implicit none
        type :: record()
            integer :: payload
        end type
        end module
    """}, "record()", "record", "type :: record()", [
        "Type parameter name list in a derived-type-stmt must not be empty",
        "Empty type parameter declaration list for 'record'",
        "A type parameter list is required at (1)",
    ])
    c.compile("R728", "abstract", ["abstract-attribute"], """
        module definitions
        implicit none
        type, abstract :: record
            integer :: payload
        end type
        end module
    """)
    c.run("R728", "public", ["public-attribute"], {
        "provider.f90": """
            module provider
            implicit none
            private
            type, public :: record
                integer :: payload
            end type
            end module
        """,
        "main.f90": """
            program p
            use provider, only: record
            implicit none
            type(record) :: value
            value%payload = 11
            if (value%payload /= 11) error stop 1
            end program
        """,
    })
    c.run("R728", "private", ["private-attribute"], {"source.f90": """
        module provider
        implicit none
        type, private :: record
            integer :: payload
        end type
        contains
        integer function check()
            type(record) :: value
            value%payload = 11
            check = value%payload
        end function
        end module
        program p
        use provider, only: check
        implicit none
        if (check() /= 11) error stop 1
        end program
    """})
    c.compile("R728", "bind_c", ["bind-c-attribute"], """
        module definitions
        use iso_c_binding, only: c_int
        implicit none
        type, bind(c) :: record
            integer(c_int) :: payload
        end type
        end module
    """)
    c.program("R728", "extends", ["extends-attribute"], """
        implicit none
        type :: parent
            integer :: inherited
        end type
        type, extends(parent) :: child
            integer :: added
        end type
        type(child) :: value
        value%inherited = 11
        value%added = 13
        if (value%inherited /= 11 .or. value%added /= 13) error stop 1
    """)
    c.pair("R728", "bind_name", ["no-type-binding-label"], {"source.f90": """
        module definitions
        use iso_c_binding, only: c_int
        implicit none
        type, bind(c,name='label') :: record
            integer(c_int) :: payload
        end type
        end module
    """}, ",name='label'", "", "type, bind(c,name='label') :: record", [
        "NAME= is not permitted in the BIND attribute of a derived type",
        "Binding label is not permitted for derived type 'record'",
    ])
    c.pair("R728", "parameterized_parent", ["parent-name-not-parameterization"], {"source.f90": """
        module definitions
        implicit none
        type :: parent(k)
            integer, kind :: k = 1
            integer :: payload
        end type
        type, extends(parent(1)) :: child
        end type
        end module
    """}, "extends(parent(1))", "extends(parent)", "type, extends(parent(1)) :: child", [
        "EXTENDS requires a parent type name, not a parameterized type specification",
        "Type parameter values are not permitted in EXTENDS",
    ])
    for variant, spelling in (
        ("integer", "iNtEgEr"), ("real", "real"), ("complex", "complex"),
        ("character", "character"), ("logical", "logical"),
        ("doubleprecision", "doubleprecision"),
    ):
        fixed = "double_precision" if variant == "doubleprecision" else "record"
        c.pair("C734", variant, ["doubleprecision-name" if variant == "doubleprecision" else "five-intrinsic-names"],
               {"source.f90": f"""
                   module definitions
                   implicit none
                   type :: {spelling}
                       integer :: payload
                   end type
                   end module
               """}, f"type :: {spelling}", f"type :: {fixed}", f"type :: {spelling}", [
                   f"Derived type name '{spelling.lower()}' cannot be the name of an intrinsic type",
                   f"Derived type name '{spelling.lower()}' at (1) cannot be the same as an intrinsic type",
                   f"'{spelling.lower()}' is not permitted as a derived type name",
                   f"Type name '{spelling.lower()}' at (1) cannot be the same as an intrinsic type",
                   "A derived type name cannot be the name of an intrinsic type",
               ])
    c.compile("C734", "subjects", ["name-subject-and-spelling-boundaries"], """
        module definitions
        implicit none
        type :: record
            integer :: real, integer
        end type
        type :: double_precision
            integer :: payload
        end type
        end module
    """)
    for variant, attribute, facet in (
        ("abstract", "abstract", "duplicate-abstract"),
        ("public", "public", "duplicate-access"),
        ("private", "private", "duplicate-access"),
        ("bind", "bind(c)", "duplicate-bind"),
        ("extends", "extends(parent)", "duplicate-extends"),
    ):
        prelude = "use iso_c_binding, only: c_int\n" if variant == "bind" else ""
        parent = "type :: parent\nend type\n" if variant == "extends" else ""
        component = "integer(c_int)" if variant == "bind" else "integer"
        header = f"type, {attribute}, {attribute} :: record"
        warning_attribute = "BIND(C)" if variant == "bind" else attribute.upper()
        flang_message = f"Attribute '{warning_attribute}' cannot be used more than once"
        nonfatal = []
        if variant != "extends":
            flang_message += " [-Wredundant-attribute]"
            nonfatal = [flang_message]
        else:
            flang_message = "Attribute 'EXTENDS' cannot be used more than once"
        messages = [
            f"Derived type 'record' has duplicate {attribute.upper()} attributes",
            f"{attribute.upper()} is repeated in the derived-type-stmt for 'record'",
            flang_message,
        ]
        if variant in ("abstract", "bind", "extends"):
            label = {"abstract": "ABSTRACT", "bind": "BIND", "extends": "EXTENDS"}[variant]
            messages.append(f"Duplicate {label} attribute specified at (1)")
        if variant == "extends":
            messages.append("DerivedType can only extend one another DerivedType")
        c.pair("C735", variant, [facet], {"source.f90":
            f"module definitions\n{prelude}implicit none\n{parent}{header}\n"
            f"    {component} :: payload\nend type\nend module\n"},
            f", {attribute}, {attribute}", f", {attribute}", header, messages,
            nonfatal=nonfatal,
            exclusions=["component", "binding '", "procedure '", "variable '"])
    for variant, names, attribute, value, facet in (
        ("kind_name", "k,k", "kind", 1, "duplicate-kind-name"),
        ("length_name", "n,N", "len", 2, "duplicate-length-name"),
    ):
        parameter = names[0]
        header = f"type :: record({names})"
        c.pair("C736", variant, [facet], {"source.f90": f"""
            module definitions
            implicit none
            {header}
                integer, {attribute} :: {parameter} = {value}
                integer :: payload
            end type
            end module
        """}, f"({names})", f"({parameter})", header, [
            f"Type parameter name '{parameter}' is repeated in the declaration of 'record'",
            f"Duplicate type parameter name '{parameter}' in derived-type-stmt",
            f"Duplicate name '{parameter}' in parameter list at (1)",
        ], exclusions=["component", "procedure binding", "dummy argument", "function '", "subroutine '"])
    c.program("C737", "prior_parent", ["prior-extensible-parent"], """
        implicit none
        type :: parent
            integer :: inherited
        end type
        type, extends(parent) :: child
            integer :: added
        end type
        type(child) :: value
        value%inherited = 11
        value%added = 13
        if (value%inherited /= 11 .or. value%added /= 13) error stop 1
    """)
    c.compile("C737", "abstract_parent", ["prior-extensible-parent"], """
        module definitions
        implicit none
        type, abstract :: parent
            integer :: inherited
        end type
        type, extends(parent) :: child
        end type
        end module
    """)
    c.run("C737", "renamed_parent", ["renamed-or-host-parent"], {
        "parent.f90": """
            module parent_module
            implicit none
            type :: original
                integer :: payload
            end type
            end module
        """,
        "main.f90": """
            program p
            use parent_module, only: local_parent => original
            implicit none
            type, extends(local_parent) :: child
            end type
            type(child) :: value
            value%payload = 17
            if (value%payload /= 17) error stop 1
            end program
        """,
    })
    c.program("C737", "host_parent", ["renamed-or-host-parent"], """
        implicit none
        type :: parent
            integer :: payload
        end type
        call check()
    contains
        subroutine check()
            type, extends(parent) :: child
            end type
            type(child) :: value
            value%payload = 17
            if (value%payload /= 17) error stop 1
        end subroutine
    """)
    alternatives = [
        ("nontype_parent", "selector", "integer, parameter :: selector = 1\n", "", "parent-is-a-type",
         ["Parent name 'selector' is not a derived type", "'selector' in EXTENDS is not a type name",
          "'selector' is not a derived type"]),
        ("forward_parent", "later", "", "type :: later\nend type\n", "prior-definition-required",
         ["Parent type 'later' must be previously defined", "Derived type 'later' has not been defined",
          "Symbol 'later' at (1) has not been previously defined", "Derived type 'later' not found"]),
        ("sequence_parent", "seq_parent",
         "type :: seq_parent\nsequence\ninteger :: seed\nend type\n", "", "sequence-parent-exclusion",
         ["SEQUENCE type 'seq_parent' cannot be extended", "Parent type 'seq_parent' is not extensible",
          "'seq_parent' cannot be extended at (1) because it is a SEQUENCE type",
          "The parent type is not extensible", "'child' extends 'seq_parent', which is a sequence type"]),
        ("bind_parent", "c_parent",
         "type, bind(c) :: c_parent\ninteger(c_int) :: seed\nend type\n", "", "bind-parent-exclusion",
         ["BIND(C) type 'c_parent' cannot be extended", "Parent type 'c_parent' is not extensible",
          "'c_parent' cannot be extended at (1) because it is BIND(C)",
          "The parent type is not extensible"]),
        ("c_ptr", "c_ptr", "", "", "intrinsic-pointer-type-exclusions",
         ["Type 'c_ptr' from ISO_C_BINDING is not extensible", "C_PTR cannot be extended",
          "'c_ptr' cannot be extended at (1)", "The parent type is not extensible"]),
        ("c_funptr", "c_funptr", "", "", "intrinsic-pointer-type-exclusions",
         ["Type 'c_funptr' from ISO_C_BINDING is not extensible", "C_FUNPTR cannot be extended",
          "'c_funptr' cannot be extended at (1)", "The parent type is not extensible"]),
    ]
    for variant, parent, before, after, facet, messages in alternatives:
        imported = {"bind_parent": "c_int", "c_ptr": "c_ptr", "c_funptr": "c_funptr"}.get(variant)
        use = f"use iso_c_binding, only: {imported}\n" if imported else ""
        header = f"type, extends({parent}) :: child"
        c.pair("C737", variant, [facet], {"source.f90":
            f"module definitions\n{use}implicit none\ntype :: good_parent\nend type\n"
            + before + header + "\ninteger :: payload\nend type\n" + after + "end module\n"},
            f"extends({parent})", "extends(good_parent)", header, messages)
    interface = """abstract interface
    subroutine action_interface(tag)
        integer, intent(out) :: tag
    end subroutine
end interface
"""
    local = ("module definitions\nimplicit none\n" + interface
             + "type :: record\ncontains\nprocedure(action_interface), deferred, nopass :: action\n"
             + "end type\nend module\n")
    c.pair("C738", "local_deferred", ["local-deferred"], {"source.f90": local},
           "type :: record", "type, abstract :: record", "type :: record", [
               "Non-ABSTRACT derived type 'record' may not contain a DEFERRED type-bound procedure",
               "Derived-type 'record' declared at (1) must be ABSTRACT because 'action' is DEFERRED and not overridden",
               "Type 'record' containing DEFERRED binding at (1) is not ABSTRACT",
               "Procedure bound to non-ABSTRACT derived type 'record' may not be DEFERRED",
               "'record' is not abstract but does not override the deferred type bound procedure 'action'",
           ], end_anchor="procedure(action_interface), deferred, nopass :: action",
           relation="The nonabstract type header and its DEFERRED action declaration are the two sides of the condition.")
    parent = (interface + "type, abstract :: parent\ncontains\n"
              "procedure(action_interface), deferred, nopass :: action\nend type\n")
    c.pair("C738", "inherited_deferred", ["inherited-deferred"], {"source.f90":
        "module definitions\nimplicit none\n" + parent
        + "type, extends(parent) :: child\nend type\nend module\n"},
        "type, extends(parent) :: child", "type, abstract, extends(parent) :: child",
        "type, extends(parent) :: child", [
            "Derived-type 'child' declared at (1) must be ABSTRACT because 'action' is DEFERRED and not overridden",
            "Non-ABSTRACT type 'child' inherits deferred binding 'action'",
            "'child' is not abstract but does not override the deferred type bound procedure 'action'",
            "Non-ABSTRACT extension of ABSTRACT derived type 'parent' lacks a binding for DEFERRED procedure 'action'",
        ])
    private_parent = parent.replace("deferred, nopass", "deferred, nopass, private")
    c.pair("C738", "private_inherited", ["private-inherited-deferred"], {
        "parent.f90": "module private_parent\nimplicit none\n" + private_parent + "end module\n",
        "child.f90": "module child_module\nuse private_parent, only: parent\nimplicit none\n"
                     "type, extends(parent) :: child\nend type\nend module\n",
    }, "type, extends(parent) :: child", "type, abstract, extends(parent) :: child",
        "type, extends(parent) :: child", [
            "Derived-type 'child' declared at (1) must be ABSTRACT because 'action' is DEFERRED and not overridden",
            "Non-ABSTRACT type 'child' inherits deferred binding 'action'",
            "'child' is not abstract but does not override the deferred type bound procedure 'action'",
            "Non-ABSTRACT extension of ABSTRACT derived type 'parent' lacks a binding for DEFERRED procedure 'action'",
        ], edit_file="child.f90", anchor_file="child.f90",
        relation="The child lacks ABSTRACT; the parent's inaccessible deferred binding is inherited, not absent.")
    c.run("C738", "concrete_override", ["concrete-override-boundary"], {"source.f90":
        "module definitions\nimplicit none\n" + parent + """
type, extends(parent) :: child
    integer :: payload
contains
    procedure, nopass :: action => implementation
end type
contains
subroutine implementation(tag)
    integer, intent(out) :: tag
    tag = 17
end subroutine
end module
program p
use definitions
implicit none
type(child) :: value
integer :: tag
value%payload = 11
call value%action(tag)
if (tag /= 17 .or. value%payload /= 11) error stop 1
end program
"""})
    c.pair("C739", "sequence", ["abstract-sequence-exclusion"], {"source.f90": """
        module definitions
        implicit none
        type, abstract :: record
            sequence
            integer :: payload
        end type
        end module
    """}, "    sequence\n", "", "type, abstract :: record", [
        "Derived type 'record' cannot be both ABSTRACT and SEQUENCE",
        "ABSTRACT derived type 'record' must be extensible",
        "Non-extensible derived-type 'record' at (1) must not be ABSTRACT",
        "An ABSTRACT derived type must be extensible",
    ], end_anchor="sequence", relation="ABSTRACT on the header conflicts with this type's SEQUENCE statement.")
    c.pair("C739", "bind", ["abstract-bind-exclusion"], {"source.f90": """
        module definitions
        use iso_c_binding, only: c_int
        implicit none
        type, abstract, bind(c) :: record
            integer(c_int) :: payload
        end type
        end module
    """}, ", bind(c)", "", "type, abstract, bind(c) :: record", [
        "Derived type 'record' cannot be both ABSTRACT and BIND(C)",
        "ABSTRACT derived type 'record' must be extensible",
        "Non-extensible derived-type 'record' at (1) must not be ABSTRACT",
        "An ABSTRACT derived type must be extensible",
    ])
    c.compile("C739", "ordinary", ["ordinary-abstract-admission"], """
        module definitions
        implicit none
        type, abstract :: record
        end type
        end module
    """)
    c.pair("C740", "child_sequence", ["child-sequence-exclusion"], {"source.f90": """
        module definitions
        implicit none
        type :: parent
        end type
        type, extends(parent) :: child
            sequence
            integer :: payload
        end type
        end module
    """}, "    sequence\n", "", "type, extends(parent) :: child", [
        "Derived type 'child' cannot have both EXTENDS and SEQUENCE",
        "An extended derived type cannot have the SEQUENCE attribute",
        "A sequence type may not have the EXTENDS attribute",
        "'child' is a sequence type, so it cannot extend another type",
    ], end_anchor="sequence", relation="The child EXTENDS header and child SEQUENCE statement conflict; the parent is extensible.")
    c.compile("R729", "private", ["component-private-alternative"], """
        module definitions
        implicit none
        type :: record
            private
            integer :: payload
        end type
        end module
    """)
    for variant, statements in (
        ("private_sequence", "private\nsequence"), ("sequence_private", "sequence\nprivate"),
    ):
        c.compile("R729", variant, ["both-orders"],
                  f"module definitions\nimplicit none\ntype :: record\n{statements}\n"
                  "integer :: payload\nend type\nend module\n")
    for variant, statement, facet in (
        ("private", "private", "duplicate-component-private"),
        ("sequence", "sequence", "duplicate-sequence"),
    ):
        warning = f"{statement.upper()} should not appear more than once in derived type components [-Wredundant-attribute]"
        messages = [
            f"Duplicate {statement.upper()} statement in the component part of 'record'",
            f"{statement.upper()} statement occurs more than once in derived type 'record'",
            warning,
        ]
        if variant == "sequence":
            messages += ["Duplicate SEQUENCE statement at (1)",
                         "SEQUENCE attribute at (1) already specified in TYPE statement"]
        c.pair("C743", variant, [facet], {"source.f90":
            "module definitions\nimplicit none\ntype :: record\n"
            + statement + "\n" + statement + " ! second occurrence\n"
            "integer :: payload\nend type\nend module\n"},
            statement + " ! second occurrence\n", "",
            statement + " ! second occurrence", messages, nonfatal=[warning],
            exclusions=["binding", "in a derived-type-stmt"])
    c.run("C743", "private_roles", ["separate-private-roles"], {"source.f90": """
        module definitions
        implicit none
        type, public :: record
            private
            integer, public :: payload
        contains
            private
            procedure, public, nopass :: answer
        end type
        contains
        integer function answer()
            answer = 17
        end function
        end module
        program p
        use definitions, only: record
        implicit none
        type(record) :: value
        value%payload = 11
        if (value%payload /= 11 .or. value%answer() /= 17) error stop 1
        end program
    """})
    for variant, ending, facet in (
        ("unnamed", "end type", "unnamed-ending"),
        ("named", "end type record", "named-ending"),
    ):
        c.program("R730", variant, [facet], f"""
            implicit none
            type :: record
                integer :: payload
            {ending}
            type(record) :: value
            value%payload = 11
            if (value%payload /= 11) error stop 1
        """)
    c.pair("C744", "end_name", ["mismatching-name"], {"source.f90": """
        module definitions
        implicit none
        type :: other
        end type
        type :: record
            integer :: payload
        end type other
        end module
    """}, "end type other", "end type record", "end type other", [
        "END TYPE name 'other' does not match type 'record'",
        "Expected label 'record' for END TYPE statement",
        "derived type definition name mismatch",
    ], relation="The END TYPE name must match the corresponding record header, not the separately defined other type.")
    c.program("C744", "case_equivalent", ["case-equivalent-name"], """
        implicit none
        type :: MiXeD
            integer :: payload
        end type mixed
        type(MIXED) :: value
        value%payload = 11
        if (value%payload /= 11) error stop 1
    """)


def coarray_definitions(c):
    for variant, nested, facet in (
        ("direct", False, "direct-introduction"), ("nested", True, "nested-introduction"),
    ):
        leaf = ("type :: leaf\ninteger, allocatable :: co[:]\nend type\n" if nested else "")
        parent_member = "type(leaf) :: seed" if nested else "integer, allocatable :: seed[:]"
        child_member = "type(leaf) :: added" if nested else "integer, allocatable :: added[:]"
        code = ("module definitions\nimplicit none\n" + leaf
                + "type :: empty_parent\nend type\ntype :: co_parent\n" + parent_member
                + "\nend type\ntype, extends(empty_parent) :: child\n" + child_member
                + "\nend type\nend module\n")
        c.pair("C741", variant, [facet], {"source.f90": code},
               "extends(empty_parent)", "extends(co_parent)",
               "type, extends(empty_parent) :: child", [
                   "Parent type 'empty_parent' lacks a coarray potential subobject component required by 'child'",
                   "Type 'child' introduces a coarray potential subobject but its parent does not have one",
                   "As extending type 'child' at (1) has a coarray component, parent type 'empty_parent' shall also have one",
                   "Type 'child' has a coarray ultimate component so the type at the base of its type extension chain ('empty_parent') must be a type that has a coarray ultimate component",
               ], end_anchor=child_member, coarray=True,
               relation="The child declaration and added coarray-potential component are the trigger; the alternative parent supplies the required presence.")
    c.compile("C741", "ancestor_presence", ["inherited-parent-presence"], """
        module definitions
        implicit none
        type :: root
            integer, allocatable :: seed[:]
        end type
        type, extends(root) :: middle
            integer :: payload
        end type
        type, extends(middle) :: child
            integer, allocatable :: added[:]
        end type
        end module
    """, coarray=True)
    special = [("event", "event_type"), ("lock", "lock_type"), ("notify", "notify_type")]
    for variant, name in special:
        messages = [
            f"Parent of 'child' must be or contain EVENT_TYPE, LOCK_TYPE or NOTIFY_TYPE because of '{name}'",
            f"Extension 'child' adds {name.upper()} without a qualifying parent type",
        ]
        if variant in ("event", "lock"):
            messages.append("Type 'child' has an EVENT_TYPE or LOCK_TYPE component, so the type at the base of its type extension chain ('parent') must either have an EVENT_TYPE or LOCK_TYPE component, or be EVENT_TYPE or LOCK_TYPE")
        c.pair("C742", variant, [variant + "-introduction"], {"source.f90": f"""
            module definitions
            use iso_fortran_env, only: {name}
            implicit none
            type :: parent
                integer, allocatable :: co[:]
            end type
            type, extends(parent) :: child
                type({name}) :: added
            end type
            end module
        """}, "integer, allocatable :: co[:]",
               f"integer, allocatable :: co[:]\n    type({name}) :: seed",
               "type, extends(parent) :: child", messages,
               end_anchor=f"type({name}) :: added", coarray=True,
               relation="The parent already has a coarray, independently satisfying C741. Only its missing special-type component is repaired; no objects or opaque operations occur.")
        c.compile("C742", variant + "_parent", ["special-parent-alternatives"], f"""
            module definitions
            use iso_fortran_env, only: {name}
            implicit none
            type, extends({name}) :: child
                integer :: payload
            end type
            end module
        """, coarray=True)
    for variant, first, second in (
        ("event_to_lock", "event_type", "lock_type"),
        ("lock_to_notify", "lock_type", "notify_type"),
        ("notify_to_event", "notify_type", "event_type"),
    ):
        c.compile("C742", variant, ["cross-category-potential-parent"], f"""
            module definitions
            use iso_fortran_env, only: {first}, {second}
            implicit none
            type :: parent
                integer, allocatable :: co[:]
                type({first}) :: seed
            end type
            type, extends(parent) :: child
                type({second}) :: added
            end type
            end module
        """, coarray=True)


def accessibility(c):
    variants = [
        ("public_public", "public-name-public-members", True, False, False),
        ("public_private", "public-name-private-members", True, True, False),
        ("private_public", "private-name-public-members", False, False, False),
        ("private_private", "private-name-private-members", False, True, True),
        ("component_private", "component-private-binding-public", True, True, False),
        ("binding_private", "binding-private-component-public", True, False, True),
    ]
    for variant, facet, public_name, private_data, private_bindings in variants:
        privacy = "    private\n" if private_data else ""
        binding_privacy = "    private\n" if private_bindings else ""
        data_attribute = ", public" if variant == "public_public" else ""
        binding_attribute = ", public" if variant in ("public_public", "public_private", "private_public") else ""
        module = (
            "module provider\nimplicit none\nprivate\n"
            "public :: published, initialize, mutate_inside, check_inside\n"
            f"type, {'public' if public_name else 'private'} :: record\n"
            + privacy + f"    integer{data_attribute} :: payload\ncontains\n"
            + binding_privacy + f"    procedure{binding_attribute} :: get_value, set_value\n"
            "end type\ntype(record) :: published\ncontains\n"
            "subroutine initialize()\npublished%payload = 11\nend subroutine\n"
            "subroutine mutate_inside()\ncall published%set_value(13)\nend subroutine\n"
            "integer function check_inside()\ncheck_inside = published%get_value()\nend function\n"
            "integer function get_value(self)\nclass(record), intent(in) :: self\n"
            "get_value = self%payload\nend function\n"
            "subroutine set_value(self, number)\nclass(record), intent(inout) :: self\n"
            "integer, intent(in) :: number\nself%payload = number\nend subroutine\nend module\n")
        imports = "published, initialize, mutate_inside, check_inside" + (", record" if public_name else "")
        main = "program p\nuse provider, only: " + imports + "\nimplicit none\n"
        if public_name:
            main += "type(record) :: local\n"
        main += "call initialize()\nif (check_inside() /= 11) error stop 1\n"
        if not private_data:
            main += "if (published%payload /= 11) error stop 2\npublished%payload = 13\n"
        else:
            main += "call mutate_inside()\n"
        main += "if (check_inside() /= 13) error stop 3\n"
        if not private_bindings:
            main += "if (published%get_value() /= 13) error stop 4\ncall published%set_value(17)\n"
            main += "if (check_inside() /= 17) error stop 5\n"
            if public_name:
                main += "call local%set_value(19)\nif (local%get_value() /= 19) error stop 6\n"
        elif public_name:
            main += "local%payload = 19\nif (local%payload /= 19) error stop 6\n"
        main += "end program\n"
        c.run("S7.5.2.2-001", variant, [facet], {"provider.f90": module, "main.f90": main})
    c.run("S7.5.2.2-002", "module_constructor", ["module-constructor-access"], {
        "provider.f90": """
            module provider
            implicit none
            private
            public :: inspect
            type :: hidden_record
                integer :: payload
            end type
            contains
            integer function inspect()
                type(hidden_record) :: value
                value = hidden_record(17)
                inspect = value%payload
            end function
            end module
        """,
        "main.f90": """
            program p
            use provider, only: inspect
            implicit none
            if (inspect() /= 17) error stop 1
            end program
        """,
    }, evidence="positive-control")
    c.run("S7.5.2.2-002", "descendant_constructor", ["descendant-constructor-access"], {
        "root.f90": """
            module root
            implicit none
            private
            public :: inspect
            type :: hidden_record
                integer :: payload
            end type
            interface
                module subroutine inspect(tag)
                    integer, intent(out) :: tag
                end subroutine
            end interface
            end module
        """,
        "first.f90": """
            submodule(root) first
            implicit none
            end submodule
        """,
        "second.f90": """
            submodule(root:first) second
            implicit none
            contains
            module procedure inspect
                type(hidden_record) :: value
                value = hidden_record(17)
                tag = value%payload
            end procedure
            end submodule
        """,
        "main.f90": """
            program p
            use root, only: inspect
            implicit none
            integer :: tag
            call inspect(tag)
            if (tag /= 17) error stop 1
            end program
        """,
    }, evidence="positive-control")
    c.pair("C1409", "private_derived_name", [], {
        "provider.f90": """
            module provider
            implicit none
            type, private :: hidden_record
                integer :: payload
            end type
            end module
        """,
        "main.f90": """
            program p
            use provider, only: hidden_record
            implicit none
            type(hidden_record) :: value
            value = hidden_record(17)
            if (value%payload /= 17) error stop 1
            end program
        """,
    }, "type, private :: hidden_record", "type, public :: hidden_record",
        "use provider, only: hidden_record", [
            "Derived type name 'hidden_record' is PRIVATE in module 'provider'",
            "Symbol 'hidden_record' referenced at (1) not found in module 'provider'",
            "PRIVATE type 'hidden_record' cannot be accessed by USE",
            "'hidden_record' is PRIVATE in 'provider'",
        ], edit_file="provider.f90", anchor_file="main.f90", control_phase="run",
        relation="The existing provider type is private; only that type-name accessibility changes. The consumer USE name and constructor are unchanged.")


def sequence_definitions(c):
    c.program("R731", "sequence_statement", ["sequence-statement-admission"], """
        implicit none
        type :: record
            sequence
            integer :: first, second
        end type
        type(record) :: value
        value%first = 11
        value%second = 13
        if (value%first /= 11 .or. value%second /= 13) error stop 1
    """)
    c.pair("C745", "empty", ["nonempty-type"], {"source.f90": """
        module definitions
        implicit none
        type :: record
        sequence
        end type
        end module
    """}, "sequence\n", "sequence\ninteger :: payload\n", "type :: record", [
        "SEQUENCE type 'record' must have at least one component",
        "Derived type 'record' at (1) must have at least one component because it is a SEQUENCE type",
        "A sequence type should have at least one component [-Wempty-sequence-type]",
    ], end_anchor="end type", relation="This entire three-line SEQUENCE definition has no component.",
        nonfatal=["A sequence type should have at least one component [-Wempty-sequence-type]"])
    c.program("C745", "data_types", ["intrinsic-and-sequence-data"], """
        implicit none
        type :: leaf
            sequence
            integer :: payload
        end type
        type :: record
            sequence
            integer :: i
            real :: r
            double precision :: d
            complex :: z
            logical :: flag
            character(2) :: label
            type(leaf) :: nested
        end type
        type(record) :: value
        value%i = 11
        value%r = 0.0
        value%d = 0.0d0
        value%z = (0.0,0.0)
        value%flag = .true.
        value%label = 'AB'
        value%nested%payload = 13
        if (value%i /= 11 .or. value%nested%payload /= 13) error stop 1
        if (value%r /= 0.0 .or. value%d /= 0.0d0) error stop 2
        if (value%z /= (0.0,0.0)) error stop 3
        if (.not. value%flag .or. value%label /= 'AB') error stop 4
    """)
    c.pair("C745", "ordinary_component", ["nonsequence-derived-data-exclusion"], {"source.f90": """
        module definitions
        implicit none
        type :: leaf
            integer :: payload
        end type
        type :: record
            sequence
            type(leaf) :: member
        end type
        end module
    """}, "type :: leaf\n", "type :: leaf\n    sequence\n", "type :: record", [
        "Component 'member' of SEQUENCE type 'record' has nonsequence type 'leaf'",
        "Component 'member' must be of an intrinsic type or a SEQUENCE type",
        "Component leaf of SEQUENCE type declared at (1) does not have the SEQUENCE attribute",
        "A sequence type data component must either be of an intrinsic type or a derived sequence type",
    ], end_anchor="type(leaf) :: member",
        relation="The SEQUENCE record header and member declaration select defined but nonsequence leaf; only SEQUENCE in that leaf is added.")
    for variant, declaration in (
        ("enum_component", "enum, bind(c) :: category\nenumerator :: one=1\nend enum\n"),
        ("enumeration_component", "enumeration type :: category\nenumerator :: one\nend enumeration type\n"),
    ):
        c.pair("C745", variant, ["enum-data-exclusions"], {"source.f90":
            "module definitions\nimplicit none\n" + declaration
            + "type :: record\nsequence\ntype(category) :: payload\nend type\nend module\n"},
            "type(category) :: payload", "integer :: payload", "type(category) :: payload", [
                "Component 'payload' of SEQUENCE type 'record' is neither intrinsic nor sequence type",
                "Component 'payload' must be of an intrinsic type or a SEQUENCE type",
            ], relation="The named enum/enumeration definition remains; only the nonintrinsic component type is replaced by INTEGER.")
    for variant, parameter, attribute, value, facet in (
        ("kind_parameter", "k", "kind", 1, "kind-parameter-exclusion"),
        ("length_parameter", "n", "len", 2, "length-parameter-exclusion"),
    ):
        header = f"type :: record({parameter})"
        c.pair("C745", variant, [facet], {"source.f90": f"""
            module definitions
            implicit none
            {header}
                integer, {attribute} :: {parameter} = {value}
                sequence
                integer :: payload
            end type
            end module
        """}, "    sequence\n", "", header, [
            "SEQUENCE type 'record' cannot have type parameters",
            "A parameterized derived type cannot have the SEQUENCE attribute",
            "A sequence type may not have type parameters",
        ], end_anchor="sequence",
            relation=f"Parameter {parameter} is correctly declared with {attribute.upper()}; remove only SEQUENCE.")
    c.pair("C745", "empty_contains", ["binding-part-exclusion"], {"source.f90": """
        module definitions
        implicit none
        type :: record
            sequence
            integer :: payload
        contains
        end type
        end module
    """}, "contains\n", "", "type :: record", [
        "SEQUENCE type 'record' cannot have a type-bound-procedure-part",
        "Derived type 'record' with SEQUENCE must not have CONTAINS",
        "Derived-type 'record' with SEQUENCE must not have a CONTAINS section at (1)",
        "A sequence type may not have a CONTAINS statement",
    ], end_anchor="contains", relation="CONTAINS introduces the binding part even though its binding list is empty.")
    c.pair("C745", "specific_binding", ["binding-part-exclusion"], {"source.f90": """
        module definitions
        implicit none
        type :: record
            sequence
            integer :: payload
        contains
            procedure, nopass :: answer
        end type
        contains
        integer function answer()
            answer = 17
        end function
        end module
    """}, "    sequence\n", "", "type :: record", [
        "SEQUENCE type 'record' cannot have a type-bound-procedure-part",
        "SEQUENCE type 'record' cannot have type-bound procedure 'answer'",
        "Derived-type 'record' with SEQUENCE must not have a CONTAINS section at (1)",
        "A sequence type may not have a CONTAINS statement",
    ], end_anchor="procedure, nopass :: answer",
        relation="The specific binding is valid for the repaired ordinary type; no interface or passed-object error is introduced.")
    c.run("C745", "component_kinds", ["pointer-allocatable-procedure-component-admission"], {
        "source.f90": """
            module definitions
            implicit none
            abstract interface
                integer function answer_interface()
                end function
            end interface
            type :: record
                sequence
                integer, pointer :: pointer_data(:)
                integer, allocatable :: allocated_data(:)
                procedure(answer_interface), pointer, nopass :: answer
            end type
            contains
            integer function answer_implementation()
                answer_implementation = 17
            end function
            end module
            program p
            use definitions
            implicit none
            type(record) :: value
            integer, target :: target(2)
            integer :: stat
            target = [11,13]
            value%pointer_data => target
            value%answer => answer_implementation
            allocate(value%allocated_data(2), stat=stat)
            if (stat /= 0) error stop 1
            if (.not. allocated(value%allocated_data)) error stop 2
            if (.not. associated(value%pointer_data)) error stop 3
            if (.not. associated(value%answer)) error stop 4
            value%allocated_data = [19,23]
            if (any(value%pointer_data /= [11,13])) error stop 5
            if (any(value%allocated_data /= [19,23])) error stop 6
            if (value%answer() /= 17) error stop 7
            end program
        """,
    })
    c.program("S7.5.2.3-001", "numeric_order", ["numeric-storage-order"], """
        implicit none
        type :: record
            sequence
            integer :: first, second
        end type
        type(record) :: value
        integer :: flat(2)
        equivalence(value,flat)
        value%first = 11
        value%second = 13
        if (flat(1) /= 11 .or. flat(2) /= 13) error stop 1
        flat(2) = 17
        if (value%first /= 11 .or. value%second /= 17) error stop 2
    """)
    c.program("S7.5.2.3-001", "nested_order", ["nested-numeric-storage-order"], """
        implicit none
        type :: leaf
            sequence
            integer :: first, second
        end type
        type :: record
            sequence
            type(leaf) :: inner
            integer :: last
        end type
        type(record) :: value
        integer :: flat(3)
        equivalence(value,flat)
        value%inner%first = 11
        value%inner%second = 13
        value%last = 17
        if (any(flat /= [11,13,17])) error stop 1
        flat(2) = 19
        if (value%inner%first /= 11) error stop 2
        if (value%inner%second /= 19 .or. value%last /= 17) error stop 3
    """)
    for variant, empty in (("character_order", False), ("zero_member", True)):
        empty_decl = "    character(0) :: empty\n" if empty else ""
        empty_write = "value%empty = ''\n" if empty else ""
        empty_check = "if (len(value%empty) /= 0) error stop 4\n" if empty else ""
        c.program("S7.5.2.3-001", variant, ["character-storage-order"],
                  "implicit none\ntype :: record\nsequence\ncharacter(1) :: first\n"
                  + empty_decl + "character(2) :: last\nend type\ntype(record) :: value\n"
                  "character(3) :: flat\nequivalence(value,flat)\nvalue%first = 'A'\n"
                  + empty_write + "value%last = 'BC'\nif (flat /= 'ABC') error stop 1\n"
                  "if (len(flat) /= 3) error stop 2\nflat(1:1) = 'D'\nflat(2:3) = 'EF'\n"
                  "if (value%first /= 'D' .or. value%last /= 'EF') error stop 3\n" + empty_check)


def identity_inputs(body_a, body_b, setup, check_a="", check_b="", name_a="record",
                    name_b="record", alias_a="record", alias_b="record", co_declarations=""):
    type_a = "module types_a\nuse iso_c_binding, only: c_int\nimplicit none\n" + text(body_a) + "end module\n"
    type_b = "module types_b\nuse iso_c_binding, only: c_int\nimplicit none\n" + text(body_b) + "end module\n"
    dispatch = (
        "module dispatch\nimplicit none\ninterface identify\n"
        "module procedure left_tag, right_tag\nend interface\ncontains\n"
        "integer function left_tag(value) result(tag)\n"
        f"use types_a, only: {alias_a} => {name_a}\nuse iso_c_binding, only: c_int\nimplicit none\n"
        f"type({alias_a}), intent(in) :: value\n" + check_a + "tag = 1\nend function\n"
        "integer function right_tag(value) result(tag)\n"
        f"use types_b, only: {alias_b} => {name_b}\nuse iso_c_binding, only: c_int\nimplicit none\n"
        f"type({alias_b}), intent(in) :: value\n" + check_b + "tag = 2\nend function\nend module\n")
    main = (
        f"program p\nuse types_a, only: a_record => {name_a}\n"
        f"use types_b, only: b_record => {name_b}\nuse dispatch, only: identify\n"
        "use iso_c_binding, only: c_int\nimplicit none\n"
        "type(a_record) :: a\ntype(b_record) :: b\n" + co_declarations
        + setup + "if (identify(a) /= 1) error stop 1\nif (identify(b) /= 2) error stop 2\nend program\n")
    return {"types_a.f90": type_a, "types_b.f90": type_b, "dispatch.f90": dispatch, "main.f90": main}


def identity(c):
    c.program("S7.5.2.4-001", "local", ["local-definition"], """
        implicit none
        type :: record
            integer :: payload
        end type
        type(record) :: first, second
        first%payload = 11
        second%payload = 13
        if (.not. same_type_as(first,second)) error stop 1
        second = first
        if (second%payload /= 11) error stop 2
    """)
    c.program("S7.5.2.4-001", "host", ["host-associated-definition"], """
        implicit none
        type :: record
            integer :: payload
        end type
        type(record) :: value
        value%payload = 11
        call change(value)
        if (value%payload /= 13) error stop 1
    contains
        subroutine change(item)
            type(record), intent(inout) :: item
            if (item%payload /= 11) error stop 2
            item%payload = 13
        end subroutine
    """)
    c.run("S7.5.2.4-001", "use_alias", ["use-renamed-definition"], {
        "types.f90": """
            module types
            implicit none
            type :: record
                integer :: payload
            end type
            end module
        """,
        "worker.f90": """
            module worker
            use types, only: worker_record => record
            implicit none
            contains
            subroutine change(value)
                type(worker_record), intent(inout) :: value
                type(worker_record) :: local
                local%payload = 17
                if (.not. same_type_as(value,local)) error stop 1
                if (value%payload /= 11) error stop 2
                value%payload = local%payload
            end subroutine
            end module
        """,
        "main.f90": """
            program p
            use types, only: caller_record => record
            use worker, only: change
            implicit none
            type(caller_record) :: value
            value%payload = 11
            call change(value)
            if (value%payload /= 17) error stop 3
            end program
        """,
    })
    c.program("S7.5.2.4-001", "parameters", ["parameter-values-not-type-identity"], """
        implicit none
        type :: record(k,n)
            integer, kind :: k
            integer, len :: n
            integer :: payload(n)
        end type
        type(record(1,2)) :: a
        type(record(2,3)) :: b
        a%payload = [11,13]
        b%payload = [17,19,23]
        if (a%k /= 1 .or. a%n /= 2) error stop 1
        if (b%k /= 2 .or. b%n /= 3) error stop 2
        if (.not. same_type_as(a,b)) error stop 3
        if (any(a%payload /= [11,13])) error stop 4
        if (any(b%payload /= [17,19,23])) error stop 5
    """)
    ordinary = "type :: record\ninteger :: payload\nend type\n"
    c.run("S7.5.2.4-002", "ordinary_distinct", ["ordinary-definitions-remain-distinct"], {
        "types_a.f90": "module types_a\nimplicit none\n" + ordinary + "end module\n",
        "types_b.f90": "module types_b\nimplicit none\n" + ordinary + "end module\n",
        "main.f90": """
            program p
            use types_a, only: a_record => record
            use types_b, only: b_record => record
            implicit none
            type(a_record) :: a
            type(b_record) :: b
            a%payload = 11
            b%payload = 13
            if (same_type_as(a,b)) error stop 1
            if (a%payload /= 11 .or. b%payload /= 13) error stop 2
            end program
        """,
    })
    for variant, bound, aliases, facet in (
        ("sequence_match", False, False, "matching-sequence-definitions"),
        ("bind_match", True, False, "matching-bind-definitions"),
        ("same_name_aliases", False, True, "definition-name-versus-alias"),
    ):
        body = ("type, bind(c) :: record\ninteger(c_int) :: first, second\nend type\n" if bound else
                "type :: record\nsequence\ninteger :: code\ncharacter(2) :: label\nend type\n")
        type_a = "module types_a\nuse iso_c_binding, only: c_int\nimplicit none\n" + body + "end module\n"
        body_b = body.replace(":: record", ":: RECORD") if aliases else body
        type_b = "module types_b\nuse iso_c_binding, only: c_int\nimplicit none\n" + body_b + "end module\n"
        local_type = "remote_record" if aliases else "record"
        use = f"use types_b, only: {local_type} => record" if aliases else "use types_b, only: record"
        if bound:
            before = "if (value%first /= 0_c_int .or. value%second /= 1_c_int) error stop 1\n"
            mutation = "value%first = 1_c_int\nvalue%second = 0_c_int\n"
            setup = "value%first = 0_c_int\nvalue%second = 1_c_int\n"
            after = "if (value%first /= 1_c_int .or. value%second /= 0_c_int) error stop 2\n"
        else:
            before = "if (value%code /= 11 .or. value%label /= 'AB') error stop 1\n"
            mutation = "value%code = 13\nvalue%label = 'CD'\n"
            setup = "value%code = 11\nvalue%label = 'AB'\n"
            after = "if (value%code /= 13 .or. value%label /= 'CD') error stop 2\n"
        worker = ("module worker\n" + use + "\nuse iso_c_binding, only: c_int\nimplicit none\n"
                  "contains\nsubroutine change(value)\n"
                  f"type({local_type}), intent(inout) :: value\n" + before + mutation + "end subroutine\nend module\n")
        main_type = "caller_record" if aliases else "record"
        main_use = f"use types_a, only: {main_type} => record" if aliases else "use types_a, only: record"
        main = ("program p\n" + main_use + "\nuse worker, only: change\nuse iso_c_binding, only: c_int\n"
                "implicit none\n" + f"type({main_type}) :: value\n" + setup
                + "call change(value)\n" + after + "end program\n")
        c.run("S7.5.2.4-002", variant, [facet],
              {"types_a.f90": type_a, "types_b.f90": type_b, "worker.f90": worker, "main.f90": main})
    inputs = identity_inputs(
        "type :: left_record\nsequence\ninteger :: payload\nend type",
        "type :: right_record\nsequence\ninteger :: payload\nend type",
        "a%payload = 11\nb%payload = 13\n",
        "if (value%payload /= 11) error stop 3\n", "if (value%payload /= 13) error stop 4\n",
        name_a="left_record", name_b="right_record")
    c.run("S7.5.2.4-002", "different_names_same_alias", ["definition-name-versus-alias"], inputs)
    definitions = [
        ("component_order", "component-order-distinction",
         "integer :: x,y", "integer :: y,x",
         "a%x=11\na%y=13\nb%x=17\nb%y=19\n",
         "if (value%x/=11 .or. value%y/=13) error stop 3\n",
         "if (value%x/=17 .or. value%y/=19) error stop 4\n"),
        ("component_name", "component-name-distinction",
         "integer :: x,y", "integer :: x,z",
         "a%x=11\na%y=13\nb%x=17\nb%z=19\n",
         "if (value%x/=11 .or. value%y/=13) error stop 3\n",
         "if (value%x/=17 .or. value%z/=19) error stop 4\n"),
        ("component_kind", "component-kind-distinction",
         "real(kind=kind(0.0)) :: payload", "real(kind=kind(0.0d0)) :: payload",
         "a%payload=0.0\nb%payload=0.0d0\n",
         "if (value%payload/=0.0) error stop 3\n",
         "if (value%payload/=0.0d0) error stop 4\n"),
        ("component_rank", "component-rank-distinction",
         "integer :: payload", "integer :: payload(2)",
         "a%payload=11\nb%payload=[13,17]\n",
         "if (value%payload/=11) error stop 3\n",
         "if (any(value%payload/=[13,17])) error stop 4\n"),
    ]
    for variant, facet, a, b, setup, check_a, check_b in definitions:
        c.run("S7.5.2.4-002", variant, [facet],
              identity_inputs("type :: record\nsequence\n" + a + "\nend type",
                              "type :: record\nsequence\n" + b + "\nend type",
                              setup, check_a, check_b))
    c.run("S7.5.2.4-002", "component_attributes", ["pointer-allocatable-attribute-distinction"],
          identity_inputs(
              "type :: record\nsequence\ninteger, pointer :: payload(:)\nend type",
              "type :: record\nsequence\ninteger, allocatable :: payload(:)\nend type",
              "target=[11,13]\na%payload=>target\nallocate(b%payload(2),stat=stat)\n"
              "if (stat/=0) error stop 7\nif (.not. allocated(b%payload)) error stop 8\nb%payload=[17,19]\n",
              "if (.not. associated(value%payload)) error stop 3\n"
              "if (size(value%payload)/=2) error stop 4\nif (any(value%payload/=[11,13])) error stop 5\n",
              "if (.not. allocated(value%payload)) error stop 3\n"
              "if (size(value%payload)/=2) error stop 4\nif (any(value%payload/=[17,19])) error stop 5\n",
              co_declarations="integer, target :: target(2)\ninteger :: stat\n"))
    forms = {
        "sequence": "type :: record\nsequence\ninteger(c_int) :: payload\nend type",
        "ordinary": "type :: record\ninteger(c_int) :: payload\nend type",
        "bind": "type, bind(c) :: record\ninteger(c_int) :: payload\nend type",
    }
    for variant, left, right in (
        ("sequence_vs_ordinary", "sequence", "ordinary"),
        ("bind_vs_ordinary", "bind", "ordinary"),
        ("sequence_vs_bind", "sequence", "bind"),
    ):
        c.run("S7.5.2.4-002", variant, ["uniform-sequence-or-bind-condition"],
              identity_inputs(forms[left], forms[right], "a%payload=0_c_int\nb%payload=1_c_int\n",
                              "if (value%payload/=0_c_int) error stop 3\n",
                              "if (value%payload/=1_c_int) error stop 4\n"))
    same = "type :: record\nsequence\ninteger :: payload\nend type"
    canonical = identity_inputs(same, same, "", alias_a="left_record", alias_b="right_record")
    canonical.pop("main.f90")
    c.pair("C1514", "sequence_definition_identity", [], canonical,
           "integer :: payload", "integer :: renamed_payload",
           "interface identify", [
               "Ambiguous interfaces in generic interface 'identify' for 'left_tag' at (1) and 'right_tag' at (2)",
               "Generic 'identify' may not have specific procedures 'left_tag' and 'right_tag' as their interfaces are not distinguishable",
           ], edit_file="types_b.f90", anchor_file="dispatch.f90",
           end_anchor="type(left_record), intent(in) :: value",
           control_name="C1514_valid__sequence_component_name_repair",
           relation="The named generic declaration and first specific's TYPE dummy form the bounded reporting relation; both named specifics use module definitions of the same SEQUENCE type. Rename only the second component, with no calls or field accesses.")


def build_corpus():
    corpus = Corpus()
    ordinary_definitions(corpus)
    coarray_definitions(corpus)
    accessibility(corpus)
    sequence_definitions(corpus)
    identity(corpus)
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
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if stale:
        parser.exit(1, "Stale generated derived-definition files:\n" + "\n".join(stale) + "\n")
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(cases)} executions; no compiler invoked.")


if __name__ == "__main__":
    main()
