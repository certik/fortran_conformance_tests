#!/usr/bin/env python3
"""Generate the finite, source-supported 7.5.5 implementation packet."""
import argparse
import json
from pathlib import Path
import sys
import textwrap

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "doc/catalogues/derived_types_7_5_5.json"
VIEW = "doc/fortran_2023_7_5_5.md"
PREFIX = "type_bound_"
EXCLUDED = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported",
    "not supported", "implementation limitation", "internal compiler error",
    "ASR verify", "ASR verifier", "unexpected end of file", "unexpected eof",
    "missing end", "out of memory", "segmentation fault", "stack trace",
    "obsolescent", "obsolete feature",
]
ELIGIBLE = {
    "R746": "private-only-part private-before-bindings single-private-slot",
    "R747": "no-access-list no-public-statement",
    "C772": "module-specification-admission main-program-local-type module-procedure-local-type submodule-local-type",
    "R749": "colon-concrete attributed-declaration-list named-interface-form attribute-colons-required nonempty-binding-list",
    "R750": "explicit-target target-is-name-not-call",
    "C773": "target-without-attributes target-with-colons",
    "C774": "local-module-target use-renamed-module-target explicit-external-target implicit-external-interface internal-target-category inaccessible-module-target",
    "C775": "same-statement-duplicate separate-statement-duplicate distinct-aliases-one-target",
    "R751": "named-generic-admission explicit-access-admission missing-association-arrow nonempty-member-list",
    "C776": "explicit-access-conflict implicit-private-conflict implicit-public-agreement same-identifier-and-type-boundaries",
    "C777": "local-specific-member forward-specific-member inherited-specific-new-generic procedure-name-not-binding generic-is-not-specific component-is-not-specific",
    "C778": "repeated-local-membership same-list-membership inherited-generic-membership same-specific-different-generics",
    "C779": "operator-nopass assignment-nopass four-io-nopass named-generic-nopass",
    "R752": "empty-pass-parentheses pointer-is-not-binding-attribute",
    "C783": "duplicate-access duplicate-deferred duplicate-non-overridable duplicate-nopass duplicate-pass",
    "C784": "no-dummy only-unrelated-dummy typed-dummy-with-nopass nonfirst-typed-dummy",
    "C785": "nonexistent-dummy-name first-dummy-name",
    "C786": "bare-pass-conflict named-pass-conflict distinct-binding-choices",
    "C787": "incompatible-attributes separate-bindings",
    "C788": "interface-without-deferred deferred-without-interface both-present-admission both-absent-admission",
    "C789": "nondeferred-to-deferred deferred-to-deferred",
    "C790": "forbidden-accessible-override inherited-nonoverridable-admission different-binding-name-admission",
    "S7.5.5-001": "omitted-explicit-same-name renamed-accessible-target",
    "S7.5.5-003": "concrete-interface-call deferred-interface-call",
    "S7.5.5-004": "two-statement-name-union declaration-order-independence",
    "S7.5.5-005": "explicit-public-over-private",
    "S7.5.5-006": "private-type-public-object public-generic-private-specific",
    "S7.5.5-007": "descendant-control unrelated-client-call unrelated-module-call private-generic-name-call inherited-private-call",
}


def text(value):
    return textwrap.dedent(value).strip() + "\n"


def identifier(rule, variant, invalid=False):
    return rule.replace(".", "_").replace("-", "_") + (
        "_invalid__tbp_" if invalid else "_valid__tbp_") + variant


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="type_bound", root=root)
        self.repairs = {}

    def fixture(self, rule, variant, facets, inputs, diagnostic=None, phase="compile",
                evidence=None, relation=""):
        name = identifier(rule, variant, bool(diagnostic))
        folder = "tests/fixtures/" + PREFIX + name.lower()
        steps = []
        for filename, body in inputs.items():
            body = text(body)
            step = Path(filename).stem
            steps.append(dict(id=step, source=filename, language="fortran", form="free",
                              output=step + ".o", depends_on=[s["id"] for s in steps]))
            self.put(folder + "/" + filename, body)
        evidence = evidence or ("effect" if diagnostic or phase == "run" else "positive-control")
        expect = dict(phase=phase, outcome="diagnose" if diagnostic else "success")
        if phase == "compile":
            expect["step"] = steps[-1]["id"]
        else:
            expect["exit_code"] = 0
        if diagnostic:
            expect["diagnostic"] = diagnostic
        manifest = dict(schema_version=1, id=name, rule=rule, facets=list(facets),
                        evidence=evidence, standard="f2023", files=list(inputs),
                        build=steps, expect=expect)
        if phase == "run":
            manifest["link"] = dict(objects=[s["output"] for s in steps], output="program")
        path = folder + "/fixture.json"
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        if name in self.cases:
            raise ValueError("duplicate case " + name)
        self.cases[name] = dict(rule=rule, facets=list(facets), phase=phase,
                                kind="invalid" if diagnostic else "valid", evidence=evidence,
                                path=path, source_relation=relation)
        return name

    def compile(self, rule, variant, facets, body):
        inputs = body if isinstance(body, dict) else {"source.f90": body}
        return self.fixture(rule, variant, facets, inputs)

    def run(self, rule, variant, facets, body):
        inputs = body if isinstance(body, dict) else {"source.f90": body}
        return self.fixture(rule, variant, facets, inputs, phase="run")

    def pair(self, rule, variant, facets, body, wrong, repaired, anchor,
             edit_file="source.f90", anchor_file="source.f90", occurrence=1,
             end_anchor=None, good_facets=None, exclusions=(), relation=""):
        inputs = body if isinstance(body, dict) else {"source.f90": body}
        inputs = {k: text(v) for k, v in inputs.items()}
        original = inputs[edit_file]
        if original.count(wrong) != 1 or wrong == repaired:
            raise ValueError(f"{rule}/{variant}: nonunique or empty repair")
        lines = inputs[anchor_file].splitlines()
        points = [n for n, line in enumerate(lines, 1) if line.strip() == anchor]
        if len(points) < occurrence or (len(points) != 1 and occurrence == 1):
            raise ValueError(f"{rule}/{variant}: ambiguous anchor {anchor!r}")
        route = diagnostic_routes()[(rule, variant)]
        diagnostic = dict(file=anchor_file, line=points[occurrence - 1],
                          contains_any=list(route["messages"]), excludes_any=EXCLUDED + list(exclusions))
        if route.get("nonfatal"):
            diagnostic["allow_nonfatal"] = route["nonfatal"]
        if end_anchor:
            ends = [n for n, line in enumerate(lines, 1) if line.strip() == end_anchor]
            if len(ends) != 1 or ends[0] < diagnostic["line"] or not relation:
                raise ValueError(f"{rule}/{variant}: invalid related span")
            diagnostic["end_line"] = ends[0]
        negative = self.fixture(rule, variant, facets, inputs, diagnostic=diagnostic, relation=relation)
        control = dict(inputs)
        control[edit_file] = original.replace(wrong, repaired, 1)
        positive = self.fixture(rule, variant + "_repair", good_facets or facets, control,
                                relation=relation)
        self.repairs[negative] = dict(control=positive, file=edit_file, wrong=wrong,
                                      repaired=repaired, anchor_file=anchor_file,
                                      relation=relation)
        return negative, positive


def record_module(bindings, bodies="", components="", attributes="", before="", interfaces="",
                  extra_types=""):
    return ("module tbp_defs\nimplicit none\n" + before
            + "type" + (", " + attributes if attributes else "") + " :: record\n"
            + components + "contains\n" + bindings + "\nend type record\n"
            + extra_types + interfaces
            + ("contains\n" + bodies if bodies else "") + "end module tbp_defs\n")


EMPTY = "subroutine impl()\nend subroutine impl\n"
SELF = ("subroutine impl(self)\nclass(record), intent(in) :: self\n"
        "end subroutine impl\n")
ABSTRACT = "abstract interface\nsubroutine iface()\nend subroutine iface\nend interface\n"


def overload_bodies(child=False):
    owner = "child" if child else "record"
    return (
        "integer function integer_impl(self,n) result(value)\n"
        f"class({owner}), intent(in) :: self\ninteger, intent(in) :: n\n"
        "value = 11\nend function integer_impl\n"
        "integer function real_impl(self,x) result(value)\n"
        f"class({owner}), intent(in) :: self\nreal, intent(in) :: x\n"
        "value = 22\nend function real_impl\n"
    )


OVERLOADS = "procedure :: int_case => integer_impl\nprocedure :: real_case => real_impl"


def grammar_cases(c):
    c.compile("R746", "private_only", ["private-only-part"], record_module("private"))
    bad = record_module("procedure, nopass :: act => impl\nprivate", EMPTY)
    c.pair("R746", "late_private", ["private-before-bindings"], bad,
           "procedure, nopass :: act => impl\nprivate", "private\nprocedure, nopass :: act => impl",
           "private",
           exclusions=["component accessibility", "private-components-stmt"])
    c.pair("R746", "duplicate_private", ["single-private-slot"],
           record_module("private\nprivate"), "private\nprivate", "private", "private",
           occurrence=2, exclusions=["component PRIVATE", "private-components-stmt"])
    body = record_module("private :: act\nprocedure, public, nopass :: act => impl", EMPTY)
    c.pair("R747", "private_list", ["no-access-list"], body, "private :: act", "private",
           "private :: act")
    body = record_module("public\nprocedure, nopass :: act => impl", EMPTY)
    c.pair("R747", "public_statement", ["no-public-statement"], body, "public\n", "",
           "public")
    c.compile("C772", "module_private", ["module-specification-admission"], record_module("private"))
    local = "type :: record\ncontains\nprivate\nend type record\n"
    c.pair("C772", "main_private", ["main-program-local-type"],
           "program p\nimplicit none\n" + local + "end program p\n",
           "private\n", "", "private")
    c.pair("C772", "procedure_private", ["module-procedure-local-type"],
           "module tbp_host\nimplicit none\ncontains\nsubroutine host()\n" + local
           + "end subroutine host\nend module tbp_host\n", "private\n", "", "private")
    ancestor = ("module tbp_ancestor\nimplicit none\ninterface\n"
                "module subroutine anchor()\nend subroutine anchor\nend interface\nend module tbp_ancestor\n")
    descendant = ("submodule(tbp_ancestor) tbp_descendant\nimplicit none\n" + local
                  + "contains\nmodule procedure anchor\nend procedure anchor\nend submodule tbp_descendant\n")
    c.pair("C772", "submodule_private", ["submodule-local-type"],
           {"ancestor.f90": ancestor, "descendant.f90": descendant},
           "private\n", "", "private",
           edit_file="descendant.f90", anchor_file="descendant.f90")
    c.compile("R749", "colon", ["colon-concrete"], record_module("procedure :: impl", SELF))
    c.compile("R749", "declaration_list", ["attributed-declaration-list"],
              record_module("procedure, nopass :: first => impl, second => other",
                            EMPTY + "subroutine other()\nend subroutine other\n"))
    c.compile("R749", "interface_list", ["named-interface-form"],
              record_module("procedure(iface), deferred, nopass :: first, second",
                            attributes="abstract", before=ABSTRACT))
    c.pair("R749", "attribute_colons", ["attribute-colons-required"],
           record_module("procedure, nopass impl", EMPTY), "nopass impl", "nopass :: impl",
           "procedure, nopass impl")
    for variant, bindings, bodies, attrs, before, repair in [
        ("concrete", "procedure, nopass ::", EMPTY, "", "", "procedure, nopass :: impl"),
        ("interface", "procedure(iface), deferred, nopass ::", "", "abstract", ABSTRACT,
         "procedure(iface), deferred, nopass :: act"),
    ]:
        c.pair("R749", "empty_" + variant, ["nonempty-binding-list"],
               record_module(bindings, bodies, attributes=attrs, before=before),
               bindings, repair, bindings)
    c.compile("R750", "explicit_target", ["explicit-target"],
              record_module("procedure, nopass :: alias => impl", EMPTY))
    c.pair("R750", "target_call", ["target-is-name-not-call"],
           record_module("procedure, nopass :: alias => impl()", EMPTY),
           "=> impl()", "=> impl", "procedure, nopass :: alias => impl()")
    c.pair("C773", "target_colons", ["target-without-attributes"],
           record_module("procedure alias => impl", SELF),
           "procedure alias", "procedure :: alias", "procedure alias => impl", good_facets=["target-without-attributes", "target-with-colons"])


def target_cases(c):
    c.compile("C774", "module_target", ["local-module-target"],
              record_module("procedure, nopass :: act => impl", EMPTY))
    provider = "module tbp_provider\nimplicit none\ncontains\n" + EMPTY + "end module tbp_provider\n"
    imported = record_module("procedure, nopass :: act => local_impl").replace(
        "implicit none\n", "use tbp_provider, only: local_impl => impl\nimplicit none\n", 1)
    c.compile("C774", "renamed_target", ["use-renamed-module-target"],
              {"provider.f90": provider, "consumer.f90": imported})
    explicit = "interface\nsubroutine work()\nend subroutine work\nend interface\n"
    external = record_module("procedure, nopass :: act => work", before=explicit) + (
        "subroutine work()\nend subroutine work\n")
    c.compile("C774", "external_target", ["explicit-external-target"], external)
    bad = external.replace(explicit, "external :: work\n")
    c.pair("C774", "implicit_external", ["implicit-external-interface"], bad,
           "external :: work\n", explicit, "procedure, nopass :: act => work")
    main = """program p
use tbp_provider, only: impl
implicit none
type :: record
contains
procedure, nopass :: act => internal_work
end type record
contains
subroutine internal_work()
end subroutine internal_work
end program p
"""
    c.pair("C774", "internal_target", ["internal-target-category"],
           {"provider.f90": provider, "client.f90": main},
           "=> internal_work", "=> impl", "procedure, nopass :: act => internal_work",
           edit_file="client.f90", anchor_file="client.f90")
    private_provider = provider.replace("implicit none\n", "implicit none\nprivate :: impl\n")
    consumer = record_module("procedure, nopass :: act => impl").replace(
        "implicit none\n", "use tbp_provider\nimplicit none\n", 1)
    c.pair("C774", "inaccessible_target", ["inaccessible-module-target"],
           {"provider.f90": private_provider, "consumer.f90": consumer},
           "private :: impl", "public :: impl", "procedure, nopass :: act => impl",
           edit_file="provider.f90", anchor_file="consumer.f90",
           relation="Only the provider implementation-name accessibility changes; no client binding access is tested.")
    bodies = EMPTY + "subroutine other()\nend subroutine other\n"
    c.pair("C775", "duplicate_list", ["same-statement-duplicate"],
           record_module("procedure, nopass :: act => impl, act => other", bodies),
           "act => other", "second => other", "procedure, nopass :: act => impl, act => other",
           exclusions=["Component 'act'", "Type parameter 'act'"])
    c.pair("C775", "duplicate_statement", ["separate-statement-duplicate"],
           record_module("procedure, nopass :: act => impl\nprocedure, nopass :: act => other", bodies),
           "procedure, nopass :: act => other\n", "", "procedure, nopass :: act => other",
           exclusions=["Component 'act'", "Type parameter 'act'"])
    c.compile("C775", "target_aliases", ["distinct-aliases-one-target"],
              record_module("procedure, nopass :: first => impl, second => impl", EMPTY))


def inherited_generic(repeat=False, new_name=False):
    generic = "h" if new_name else "g"
    members = "int_case, real_case" if repeat else "real_case"
    return """module tbp_defs
implicit none
type :: record
contains
procedure :: int_case => integer_impl
generic :: g => int_case
end type record
type, extends(record) :: child
contains
procedure :: real_case => child_real
generic :: """ + generic + " => " + members + """
end type child
contains
integer function integer_impl(self,n) result(value)
class(record), intent(in) :: self
integer, intent(in) :: n
value = 11
end function integer_impl
integer function child_real(self,x) result(value)
class(child), intent(in) :: self
real, intent(in) :: x
value = 22
end function child_real
end module tbp_defs
"""


def generic_cases(c):
    basic = "procedure, nopass :: specific => impl\ngeneric :: g => specific"
    c.compile("R751", "named_generic", ["named-generic-admission"], record_module(basic, EMPTY))
    c.compile("R751", "public_generic", ["explicit-access-admission"],
              record_module("private\nprocedure, nopass :: specific => impl\ngeneric, public :: g => specific", EMPTY))
    c.pair("R751", "missing_arrow", ["missing-association-arrow"],
           record_module(basic.replace("g =>", "g"), EMPTY), "generic :: g specific",
           "generic :: g => specific", "generic :: g specific")
    c.pair("R751", "missing_member", ["nonempty-member-list"],
           record_module("procedure, nopass :: specific => impl\ngeneric :: g =>", EMPTY),
           "generic :: g =>\n", "generic :: g => specific\n", "generic :: g =>")
    two = OVERLOADS + "\ngeneric, public :: g => int_case\ngeneric, private :: g => real_case"
    c.pair("C776", "explicit_access", ["explicit-access-conflict"], record_module(two, overload_bodies()),
           "generic, private :: g", "generic, public :: g", "generic, private :: g => real_case")
    two = "private\n" + OVERLOADS + "\ngeneric :: g => int_case\ngeneric, public :: g => real_case"
    c.pair("C776", "implicit_access", ["implicit-private-conflict"], record_module(two, overload_bodies()),
           "generic, public :: g", "generic :: g", "generic, public :: g => real_case")
    c.compile("C776", "access_agreement", ["implicit-public-agreement"],
              record_module(OVERLOADS.replace("procedure :: int_case", "procedure, private :: int_case")
                            + "\ngeneric :: g => int_case\ngeneric, public :: g => real_case", overload_bodies()))
    second = """type :: another
contains
procedure, nopass :: specific => impl
generic, private :: g => specific
end type another
"""
    c.compile("C776", "access_scopes", ["same-identifier-and-type-boundaries"],
              record_module("procedure, nopass :: specific => impl\n"
                            "generic, public :: g => specific\ngeneric, private :: h => specific",
                            EMPTY, extra_types=second))
    c.compile("C777", "local_member", ["local-specific-member"], record_module(basic, EMPTY))
    c.compile("C777", "forward_member", ["forward-specific-member"],
              record_module("generic :: g => specific\nprocedure, nopass :: specific => impl", EMPTY))
    inherited = inherited_generic(new_name=True).replace("generic :: h => real_case",
                                                         "generic :: h => int_case")
    c.compile("C777", "inherited_member", ["inherited-specific-new-generic"], inherited)
    for variant, facet, bindings, wrong, repair, anchor, components in [
        ("procedure_member", "procedure-name-not-binding",
         "procedure, nopass :: alias => impl\ngeneric :: g => impl", "g => impl", "g => alias",
         "generic :: g => impl", ""),
        ("generic_member", "generic-is-not-specific",
         "procedure, nopass :: specific => impl\ngeneric :: h => specific\ngeneric :: g => h",
         "g => h", "g => specific", "generic :: g => h", ""),
        ("component_member", "component-is-not-specific",
         "procedure, nopass :: specific => impl\ngeneric :: g => payload",
         "g => payload", "g => specific", "generic :: g => payload", "integer :: payload\n"),
    ]:
        c.pair("C777", variant, [facet], record_module(bindings, EMPTY, components),
               wrong, repair, anchor)
    repeat = OVERLOADS + "\ngeneric :: g => int_case\ngeneric :: g => int_case, real_case"
    c.pair("C778", "repeated_member", ["repeated-local-membership"],
           record_module(repeat, overload_bodies()), "g => int_case, real_case", "g => real_case",
           "generic :: g => int_case, real_case")
    c.pair("C778", "duplicate_member", ["same-list-membership"],
           record_module("procedure, nopass :: specific => impl\ngeneric :: g => specific, specific", EMPTY),
           "specific, specific", "specific", "generic :: g => specific, specific")
    c.pair("C778", "inherited_repeat", ["inherited-generic-membership"],
           inherited_generic(repeat=True), "g => int_case, real_case", "g => real_case",
           "generic :: g => int_case, real_case")
    c.compile("C778", "distinct_generics", ["same-specific-different-generics"],
              record_module(basic + "\ngeneric :: h => specific", EMPTY))


def io_body(direction, form):
    formatted = form == "formatted"
    arguments = "dtv,unit," + ("iotype,v_list," if formatted else "") + "iostat,iomsg"
    return (
        f"subroutine io_impl({arguments})\n"
        f"class(record), intent({'inout' if direction == 'read' else 'in'}) :: dtv\n"
        "integer, intent(in) :: unit\n"
        + ("character(*), intent(in) :: iotype\ninteger, intent(in) :: v_list(:)\n" if formatted else "")
        + "integer, intent(out) :: iostat\ncharacter(*), intent(inout) :: iomsg\n"
        "iostat = 0\nend subroutine io_impl\n"
    )


def nonname_pass_cases(c):
    unary = ("integer function op_impl(self) result(value)\n"
             "class(record), intent(in) :: self\nvalue = 17\nend function op_impl\n")
    binding = "procedure, nopass :: op => op_impl\ngeneric :: operator(.probe.) => op"
    c.pair("C779", "operator_nopass", ["operator-nopass"], record_module(binding, unary),
           "procedure, nopass :: op", "procedure :: op",
           "generic :: operator(.probe.) => op")
    assignment = ("subroutine assign_impl(lhs,rhs)\nclass(record), intent(inout) :: lhs\n"
                  "integer, intent(in) :: rhs\nlhs%payload = rhs\nend subroutine assign_impl\n")
    binding = "procedure, nopass :: assign => assign_impl\ngeneric :: assignment(=) => assign"
    c.pair("C779", "assignment_nopass", ["assignment-nopass"],
           record_module(binding, assignment, "integer :: payload\n"),
           "procedure, nopass :: assign", "procedure :: assign", "generic :: assignment(=) => assign")
    for direction in ["read", "write"]:
        for form in ["formatted", "unformatted"]:
            binding = f"procedure, nopass :: io => io_impl\ngeneric :: {direction}({form}) => io"
            c.pair("C779", direction + "_" + form, ["four-io-nopass"],
                   record_module(binding, io_body(direction, form)),
                   "procedure, nopass :: io", "procedure :: io",
                   f"generic :: {direction}({form}) => io")
    c.compile("C779", "named_nopass", ["named-generic-nopass"],
              record_module("procedure, nopass :: act => impl\ngeneric :: g => act", EMPTY))


def attribute_cases(c):
    c.pair("R752", "empty_pass", ["empty-pass-parentheses"],
           record_module("procedure, pass() :: act => impl", SELF),
           "pass()", "pass", "procedure, pass() :: act => impl")
    c.pair("R752", "pointer_attribute", ["pointer-is-not-binding-attribute"],
           record_module("procedure, pointer, nopass :: act => impl", EMPTY),
           "pointer, ", "", "procedure, pointer, nopass :: act => impl",
           exclusions=["procedure pointer component", "data pointer component"])
    for variant, attribute, facet in [
        ("public", "public", "duplicate-access"), ("private", "private", "duplicate-access"),
        ("deferred", "deferred", "duplicate-deferred"),
        ("non_overridable", "non_overridable", "duplicate-non-overridable"),
        ("nopass", "nopass", "duplicate-nopass"),
        ("pass", "pass", "duplicate-pass"), ("pass_name", "pass(self)", "duplicate-pass"),
    ]:
        repeated = attribute + ", " + attribute
        if variant == "deferred":
            body = record_module("procedure(iface), " + repeated + ", nopass :: act",
                                 attributes="abstract", before=ABSTRACT)
        else:
            attrs = repeated + (", nopass" if variant in ["public", "private", "non_overridable"] else "")
            body = record_module("procedure, " + attrs + " :: act => impl",
                                 SELF if variant.startswith("pass") else EMPTY)
        line = next(x for x in body.splitlines() if x.startswith("procedure"))
        c.pair("C783", "duplicate_" + variant, [facet], body, repeated, attribute, line,
               exclusions=["component", "type-attr-spec", "derived-type-stmt"])
    c.pair("C784", "no_arguments", ["no-dummy"], record_module("procedure :: impl", EMPTY),
           "procedure :: impl", "procedure, nopass :: impl", "procedure :: impl")
    integer_dummy = "subroutine impl(number)\ninteger, intent(in) :: number\nend subroutine impl\n"
    c.pair("C784", "integer_argument", ["only-unrelated-dummy"],
           record_module("procedure :: impl", integer_dummy),
           "procedure :: impl", "procedure, nopass :: impl", "procedure :: impl")
    c.compile("C784", "typed_nopass", ["typed-dummy-with-nopass"],
              record_module("procedure, nopass :: act => impl", SELF))
    second = ("subroutine impl(number,self)\ninteger, intent(in) :: number\n"
              "class(record), intent(in) :: self\nend subroutine impl\n")
    c.compile("C784", "nonfirst_pass", ["nonfirst-typed-dummy"],
              record_module("procedure, pass(self) :: act => impl", second))
    c.pair("C785", "missing_pass_name", ["nonexistent-dummy-name"],
           record_module("procedure, pass(slef) :: act => impl", SELF),
           "pass(slef)", "pass(self)", "procedure, pass(slef) :: act => impl")
    c.compile("C785", "first_pass", ["first-dummy-name"],
              record_module("procedure, pass(self) :: act => impl", SELF))
    for variant, facet, attributes, repaired in [
        ("bare", "bare-pass-conflict", "pass, nopass", "pass"),
        ("named", "named-pass-conflict", "pass(self), nopass", "nopass"),
    ]:
        line = "procedure, " + attributes + " :: act => impl"
        c.pair("C786", variant + "_conflict", [facet], record_module(line, SELF),
               attributes, repaired, line,
               exclusions=["component", "proc-component"])
    c.compile("C786", "separate_choices", ["distinct-binding-choices"],
              record_module("procedure, pass :: with_self => impl\nprocedure, nopass :: without_self => other",
                            SELF + "subroutine other()\nend subroutine other\n"))
    bad = record_module("procedure(iface), deferred, non_overridable, nopass :: act",
                        attributes="abstract", before=ABSTRACT)
    c.pair("C787", "incompatible_attributes", ["incompatible-attributes"], bad,
           "deferred, non_overridable", "deferred",
           "procedure(iface), deferred, non_overridable, nopass :: act")
    c.compile("C787", "separate_bindings", ["separate-bindings"],
              record_module("procedure(iface), deferred, nopass :: pending\n"
                            "procedure, non_overridable, nopass :: stable => impl",
                            EMPTY, attributes="abstract", before=ABSTRACT))
    c.pair("C788", "missing_deferred", ["interface-without-deferred"],
           record_module("procedure(iface), nopass :: act", attributes="abstract", before=ABSTRACT),
           "procedure(iface), nopass", "procedure(iface), deferred, nopass",
           "procedure(iface), nopass :: act",
           good_facets=["interface-without-deferred", "both-present-admission"])
    c.pair("C788", "missing_interface", ["deferred-without-interface"],
           record_module("procedure, deferred, nopass :: impl", EMPTY, attributes="abstract"),
           "procedure, deferred, nopass", "procedure, nopass", "procedure, deferred, nopass :: impl",
           good_facets=["deferred-without-interface", "both-absent-admission"])


def override_module(deferred_parent=False, deferred_child=False, nonoverridable=False,
                    child_binding=True, other_name=False):
    parent_binding = ("procedure(parent_iface), deferred :: act" if deferred_parent else
                      "procedure" + (", non_overridable" if nonoverridable else "") + " :: act => parent_impl")
    name = "extra" if other_name else "act"
    binding = ("procedure(child_iface), deferred :: " + name if deferred_child else
               "procedure :: " + name + " => child_impl")
    return (
        "module tbp_defs\nimplicit none\n"
        + ("type, abstract :: record\n" if deferred_parent else "type :: record\n")
        + "contains\n" + parent_binding + "\nend type record\n"
        + ("type, abstract, extends(record) :: child\n" if deferred_child else
           "type, extends(record) :: child\n")
        + "contains\n" + (binding + "\n" if child_binding else "") + "end type child\n"
        + "abstract interface\nsubroutine parent_iface(self)\nimport record\n"
        "class(record), intent(in) :: self\nend subroutine parent_iface\n"
        "subroutine child_iface(self)\nimport child\nclass(child), intent(in) :: self\n"
        "end subroutine child_iface\nend interface\ncontains\n"
        "subroutine parent_impl(self)\nclass(record), intent(in) :: self\nend subroutine parent_impl\n"
        "subroutine child_impl(self)\nclass(child), intent(in) :: self\nend subroutine child_impl\n"
        "end module tbp_defs\n"
    )


def override_cases(c):
    c.pair("C789", "redefer_concrete", ["nondeferred-to-deferred"],
           override_module(deferred_child=True), "procedure(child_iface), deferred :: act\n", "",
           "type, abstract, extends(record) :: child",
           end_anchor="end type child", relation="Child DEFERRED override of accessible concrete parent act.")
    c.compile("C789", "deferred_override", ["deferred-to-deferred"],
              override_module(deferred_parent=True, deferred_child=True))
    c.pair("C790", "nonoverridable_override", ["forbidden-accessible-override"],
           override_module(nonoverridable=True), "procedure, non_overridable :: act",
           "procedure :: act", "type, extends(record) :: child",
           end_anchor="end type child", relation="Accessible child act overrides inherited NON_OVERRIDABLE act.")
    c.compile("C790", "inherited_nonoverridable", ["inherited-nonoverridable-admission"],
              override_module(nonoverridable=True, child_binding=False))
    c.compile("C790", "distinct_binding", ["different-binding-name-admission"],
              override_module(nonoverridable=True, other_name=True))


def same_name_runtime():
    return """module tbp_defs
implicit none
type :: first
integer :: payload
contains
procedure :: first_value
procedure :: explicit_first => first_value
end type first
type :: second
integer :: payload
contains
procedure :: second_value
procedure :: explicit_second => second_value
end type second
contains
subroutine prepare_first(item)
type(first), intent(inout) :: item
item%payload = 17
end subroutine prepare_first
subroutine prepare_second(item)
type(second), intent(inout) :: item
item%payload = 29
end subroutine prepare_second
integer function first_value(self) result(value)
class(first), intent(in) :: self
value = self%payload
end function first_value
integer function second_value(self) result(value)
class(second), intent(in) :: self
value = 2*self%payload+1
end function second_value
end module tbp_defs
program p
use tbp_defs
implicit none
type(first) :: a
type(second) :: b
integer :: observed
call prepare_first(a)
call prepare_second(b)
observed = a%first_value()
if (observed /= 17) error stop 1
observed = a%explicit_first()
if (observed /= 17) error stop 2
observed = b%second_value()
if (observed /= 59) error stop 3
observed = b%explicit_second()
if (observed /= 59) error stop 4
end program p
"""


def interface_runtime(deferred=False):
    if not deferred:
        definitions = """type :: record
integer :: payload
contains
procedure :: alias => implementation
end type record
"""
        extra = ""
        passed_type = "record"
        call = "observed = item%alias(scale=3)"
    else:
        definitions = """type, abstract :: base
integer :: payload
contains
procedure(method_interface), deferred :: alias
end type base
type, extends(base) :: record
integer :: marker
contains
procedure :: alias => implementation
end type record
abstract interface
integer function method_interface(self,scale) result(value)
import base
class(base), intent(in) :: self
integer, intent(in) :: scale
end function method_interface
end interface
"""
        extra = """integer function through_base(item) result(value)
class(base), intent(in) :: item
value = item%alias(scale=3)
end function through_base
"""
        passed_type = "record"
        call = "observed = through_base(item)"
    return (
        "module tbp_defs\nimplicit none\n" + definitions + "contains\n"
        "subroutine prepare(item)\ntype(record), intent(inout) :: item\nitem%payload = 17\n"
        + ("item%marker = 29\n" if deferred else "")
        + "end subroutine prepare\ninteger function implementation(self,scale) result(value)\n"
        f"class({passed_type}), intent(in) :: self\ninteger, intent(in) :: scale\n"
        "value = self%payload+scale\nend function implementation\n" + extra
        + "end module tbp_defs\nprogram p\nuse tbp_defs\nimplicit none\n"
        "type(record) :: item\ninteger :: observed\ncall prepare(item)\n" + call
        + "\nif (observed /= 20) error stop 1\n"
        + ("if (item%marker /= 29) error stop 2\n" if deferred else "")
        + "end program p\n"
    )


def generic_runtime(forward=False):
    specifics = "procedure :: int_case => int_impl\nprocedure :: real_case => real_impl\n"
    generics = "generic :: g => int_case\ngeneric :: g => real_case\n"
    return (
        "module tbp_defs\nimplicit none\ntype :: record\ninteger :: payload\ncontains\n"
        + (generics + specifics if forward else specifics + generics)
        + "end type record\ncontains\n"
        "subroutine prepare(item,payload)\ntype(record), intent(inout) :: item\n"
        "integer, intent(in) :: payload\nitem%payload = payload\nend subroutine prepare\n"
        "integer function int_impl(self,n) result(value)\nclass(record), intent(in) :: self\n"
        "integer, intent(in) :: n\nvalue = self%payload+2*n\nend function int_impl\n"
        "integer function real_impl(self,x) result(value)\nclass(record), intent(in) :: self\n"
        "real, intent(in) :: x\nvalue = self%payload+17\nend function real_impl\n"
        "end module tbp_defs\nprogram p\nuse tbp_defs\nimplicit none\n"
        "type(record) :: item\ninteger :: observed\ncall prepare(item,payload=5)\n"
        "observed = item%g(3)\nif (observed /= 11) error stop 1\n"
        "observed = item%g(1.0)\nif (observed /= 22) error stop 2\n"
        "call prepare(item,payload=7)\n"
        "observed = item%g(3)\nif (observed /= 13) error stop 3\n"
        "observed = item%g(1.0)\nif (observed /= 24) error stop 4\nend program p\n"
    )


def public_runtime(private_type=False, generic=False):
    return {
        "provider.f90": (
            "module tbp_provider\nimplicit none\nprivate\n"
            + ("type :: record\n" if private_type else "type, public :: record\n")
            + "private\ninteger :: payload\ncontains\nprivate\n"
            + ("procedure, private :: specific => implementation\ngeneric, public :: get => specific\n" if generic
               else "procedure, public :: get => implementation\n")
            + "end type record\ntype(record), public :: object\npublic :: prepare\ncontains\n"
            "subroutine prepare()\nobject%payload = 17\nend subroutine prepare\n"
            "integer function implementation(self) result(value)\nclass(record), intent(in) :: self\n"
            "value = self%payload\nend function implementation\nend module tbp_provider\n"
        ),
        "client.f90": (
            "program p\nuse tbp_provider, only: object, prepare\nimplicit none\n"
            "integer :: observed\ncall prepare()\nobserved = object%get()\n"
            "if (observed /= 17) error stop 1\nend program p\n"
        ),
    }


def runtime_cases(c):
    c.run("S7.5.5-001", "same_name", ["omitted-explicit-same-name"], same_name_runtime())
    provider = """module tbp_provider
implicit none
contains
integer function provider_value() result(value)
value = 22
end function provider_value
end module tbp_provider
"""
    consumer = """module tbp_consumer
use tbp_provider, only: local_name => provider_value
implicit none
type :: record
integer :: payload
contains
procedure, nopass :: local_name
procedure, nopass :: explicit_alias => local_name
end type record
end module tbp_consumer
"""
    client = """program p
use tbp_consumer, only: record
implicit none
type(record) :: item
integer :: observed
item%payload = 11
observed = item%local_name()
if (observed /= 22) error stop 1
observed = item%explicit_alias()
if (observed /= 22) error stop 2
if (item%payload /= 11) error stop 3
end program p
"""
    c.run("S7.5.5-001", "renamed_target", ["renamed-accessible-target"],
          {"provider.f90": provider, "consumer.f90": consumer, "client.f90": client})
    c.run("S7.5.5-003", "concrete_interface", ["concrete-interface-call"], interface_runtime())
    c.run("S7.5.5-003", "deferred_interface", ["deferred-interface-call"], interface_runtime(True))
    c.run("S7.5.5-004", "generic_union", ["two-statement-name-union"], generic_runtime())
    c.run("S7.5.5-004", "forward_generic_union", ["declaration-order-independence"], generic_runtime(True))
    c.run("S7.5.5-005", "public_over_private", ["explicit-public-over-private"], public_runtime())
    c.run("S7.5.5-006", "private_type", ["private-type-public-object"], public_runtime(private_type=True))
    c.run("S7.5.5-006", "public_generic", ["public-generic-private-specific"], public_runtime(generic=True))


def privacy_provider(default=False, generic=False, ancestor=False):
    name = "parent" if ancestor else "record"
    binding = ("private\nprocedure :: secret => implementation" if default else
               "procedure, private :: secret => implementation")
    if generic:
        binding = "procedure :: specific => implementation\ngeneric, private :: g => specific"
    return (
        "module tbp_provider\nimplicit none\ntype :: " + name + "\ninteger :: payload\ncontains\n"
        + binding + "\nend type " + name + "\n"
        + ("" if ancestor else "type(record) :: object\n")
        + "contains\ninteger function implementation(self) result(value)\n"
        f"class({name}), intent(in) :: self\nvalue = self%payload\n"
        "end function implementation\nend module tbp_provider\n"
    )




def privacy_cases(c):
    for variant, default in [("explicit_private_client", False), ("default_private_client", True)]:
        provider = privacy_provider(default=default)
        client = """program p
use tbp_provider, only: object
implicit none
integer :: observed
object%payload = 17
observed = object%secret()
end program p
"""
        wrong, fixed = (("private\n", "") if default else
                        ("procedure, private :: secret", "procedure, public :: secret"))
        c.pair("S7.5.5-007", variant, ["unrelated-client-call"],
               {"provider.f90": provider, "client.f90": client}, wrong, fixed,
               "observed = object%secret()",
               edit_file="provider.f90", anchor_file="client.f90",
               relation="Binding PRIVATE default removal." if default else "Explicit binding PRIVATE-to-PUBLIC.",
               exclusions=["private component", "Component 'secret'"])
    consumer = """module tbp_consumer
use tbp_provider, only: object
implicit none
contains
integer function attempt() result(observed)
object%payload = 17
observed = object%secret()
end function attempt
end module tbp_consumer
"""
    c.pair("S7.5.5-007", "private_other_module", ["unrelated-module-call"],
           {"provider.f90": privacy_provider(), "consumer.f90": consumer},
           "procedure, private :: secret", "procedure, public :: secret",
           "observed = object%secret()",
           edit_file="provider.f90", anchor_file="consumer.f90",
           relation="Only binding accessibility changes; the consumer is not a descendant module.",
           exclusions=["private component", "Component 'secret'"])
    client = """program p
use tbp_provider, only: object
implicit none
integer :: observed
object%payload = 17
observed = object%g()
end program p
"""
    c.pair("S7.5.5-007", "private_generic", ["private-generic-name-call"],
           {"provider.f90": privacy_provider(generic=True), "client.f90": client},
           "generic, private :: g", "generic, public :: g", "observed = object%g()",
           edit_file="provider.f90", anchor_file="client.f90",
           relation="The generic-name binding's PRIVATE-to-PUBLIC repair; no interface/member changes.",
           exclusions=["private component", "Component 'g'"])
    child = """module tbp_child
use tbp_provider, only: parent
implicit none
type, extends(parent) :: child
integer :: marker
end type child
type(child) :: child_object
end module tbp_child
"""
    client = """program p
use tbp_child, only: child_object
implicit none
integer :: observed
child_object%payload = 17
child_object%marker = 29
observed = child_object%secret()
end program p
"""
    c.pair("S7.5.5-007", "private_inherited", ["inherited-private-call"],
           {"provider.f90": privacy_provider(ancestor=True), "child.f90": child, "client.f90": client},
           "procedure, private :: secret", "procedure, public :: secret",
           "observed = child_object%secret()",
           edit_file="provider.f90", anchor_file="client.f90",
           relation="Only inherited parent binding accessibility changes; no child homonym or abstract type.",
           exclusions=["private component", "Component 'secret'"])
    ancestor = privacy_provider().replace(
        "contains\ninteger function implementation",
        "interface\nmodule subroutine inspect()\nend subroutine inspect\nend interface\n"
        "contains\ninteger function implementation")
    descendant = """submodule(tbp_provider) tbp_descendant
implicit none
contains
module procedure inspect
integer :: observed
object%payload = 17
observed = object%secret()
end procedure inspect
end submodule tbp_descendant
"""
    c.compile("S7.5.5-007", "private_descendant", ["descendant-control"],
              {"provider.f90": ancestor, "descendant.f90": descendant})


def diagnostic_routes():
    """Finite role/property predicates; bare tokens and generic recovery are not causes."""
    result = {}

    def route(rule, variant, *messages, nonfatal=None):
        key = (rule, variant)
        if key in result:
            raise ValueError("duplicate diagnostic route " + str(key))
        result[key] = dict(messages=list(messages))
        if nonfatal:
            result[key]["nonfatal"] = nonfatal

    route("R746", "late_private",
          "Binding PRIVATE must precede type-bound procedure bindings",
          "PRIVATE statement at (1) must precede procedure bindings")
    route("R746", "duplicate_private",
          "Duplicate binding PRIVATE statement",
          "PRIVATE statement may appear only once in the type-bound procedure part")
    route("R747", "private_list",
          "Binding PRIVATE statement cannot have a name list",
          "PRIVATE statement in type-bound procedure part must not have a list",
          "Unexpected '::' in binding PRIVATE statement")
    route("R747", "public_statement",
          "PUBLIC statement is not allowed in the type-bound procedure part",
          "PUBLIC statement at (1) is only allowed in the specification part of a module")
    for variant in ["main_private", "procedure_private", "submodule_private"]:
        route("C772", variant,
              "PRIVATE statement in a type-bound procedure part is only allowed in a module",
              "PRIVATE statement at (1) is only allowed in the specification part of a module",
              "PRIVATE is only allowed in a derived type that is in a module")
    route("R749", "attribute_colons",
          "Expected '::' after binding-attributes at (1)",
          "Missing double colon after type-bound PROCEDURE binding attributes")
    route("R749", "empty_concrete",
          "expected type bound procedure declarations",
          "A concrete PROCEDURE binding declaration requires at least one binding name")
    route("R749", "empty_interface",
          "A PROCEDURE(interface) binding declaration requires at least one binding name",
          "Expected binding-name-list after PROCEDURE(interface) binding attributes")
    route("R750", "target_call",
          "Procedure binding target 'impl' must be a name, not a reference",
          "Unexpected '(' after procedure binding target 'impl'")
    portability = "type-bound procedure statement should have '::' if it has '=>'"
    route("C773", "target_colons",
          "'::' needed in PROCEDURE binding with explicit target at (1)",
          "Type-bound PROCEDURE declaration with an explicit target requires '::'",
          portability,
          nonfatal=[dict(compiler="flang", severity="portability", equals_any=[portability])])
    for variant, target in [("implicit_external", "work"), ("internal_target", "internal_work"),
                            ("inaccessible_target", "impl")]:
        route("C774", variant,
              f"'{target}' must be a module procedure or an external procedure with an explicit interface",
              f"The binding of 'act' ('{target}') must be either an accessible module procedure "
              "or an external procedure with an explicit interface")
    for variant in ["duplicate_list", "duplicate_statement"]:
        route("C775", variant,
              "There is already a procedure with binding name 'act' for the derived type 'record'",
              "Specific binding 'act' is declared more than once in derived type 'record'")
    route("R751", "missing_arrow",
          "Missing '=>' between generic binding 'g' and its specific binding list",
          "Expected '=>' in type-bound GENERIC statement for 'g'")
    route("R751", "missing_member",
          "Type-bound GENERIC 'g' requires a nonempty specific binding list",
          "Expected a specific binding name in type-bound GENERIC 'g'")
    for variant in ["explicit_access", "implicit_access"]:
        route("C776", variant,
              "Binding at (1) must have the same access as already defined binding 'g'",
              "Generic binding 'g' has conflicting accessibility in this type")
    route("C777", "procedure_member",
          "Undefined specific binding 'impl' as target of GENERIC 'g'",
          "Binding name 'impl' not found in this derived type")
    route("C777", "generic_member",
          "GENERIC 'g' at (1) must target a specific binding, 'h' is GENERIC, too",
          "'h' is not the name of a specific binding of this type")
    route("C777", "component_member",
          "Undefined specific binding 'payload' as target of GENERIC 'g'",
          "'payload' is not the name of a specific binding of this type")
    for variant, member in [("duplicate_member", "specific"), ("repeated_member", "int_case"),
                            ("inherited_repeat", "int_case")]:
        route("C778", variant,
              f"'{member}' already defined as specific binding for the generic 'g'",
              f"Binding name '{member}' was already specified for generic 'g'",
              f"Specific binding '{member}' was already inherited for generic 'g'")
    route("C779", "operator_nopass",
          "Type-bound operator at (1) cannot be NOPASS",
          "OPERATOR(.probe.) procedure 'op' may not have NOPASS attribute")
    route("C779", "assignment_nopass",
          "Defined assignment procedure 'assign' may not have NOPASS attribute",
          "Type-bound assignment binding 'assign' requires a passed-object dummy argument")
    for direction in ["read", "write"]:
        for form in ["formatted", "unformatted"]:
            route("C779", direction + "_" + form,
                  "Defined input/output procedure 'io' may not have NOPASS attribute",
                  "Defined I/O binding 'io' requires a passed-object dummy argument")
    route("R752", "empty_pass",
          "PASS() in a type-bound binding attribute requires an argument name",
          "Missing argument name in the PASS parentheses of binding 'act'")
    route("R752", "pointer_attribute",
          "POINTER is not a type-bound procedure binding attribute",
          "POINTER attribute is not allowed for type-bound binding 'act'")
    for variant in ["public", "private", "deferred", "non_overridable", "nopass", "pass", "pass_name"]:
        token = "PASS" if variant.startswith("pass") else variant.upper()
        messages = [f"Duplicate {token} binding attribute",
                    f"Type-bound binding 'act' specifies {token} more than once"]
        nonfatal = None
        if variant != "pass_name":
            warning = f"Attribute '{token}' cannot be used more than once [-Wredundant-attribute]"
            messages.append(warning)
            nonfatal = [dict(compiler="flang", severity="warning", equals_any=[warning])]
        route("C783", "duplicate_" + variant, *messages, nonfatal=nonfatal)
    route("C784", "no_arguments",
          "Procedure 'impl' with PASS at (1) must have at least one argument",
          "Procedure binding 'impl' with no dummy arguments must have NOPASS attribute")
    route("C784", "integer_argument",
          "Passed-object dummy argument 'number' of procedure 'impl' must be of type 'record'",
          "Binding 'impl' has no dummy of the defining type 'record' and requires NOPASS")
    route("C785", "missing_pass_name",
          "Passed object dummy argument slef not found in function arguments",
          "Procedure 'impl' with PASS(slef) at (1) has no argument 'slef'",
          "'slef' is not a dummy argument of procedure interface 'impl'")
    for variant in ["bare_conflict", "named_conflict"]:
        route("C786", variant,
              "Pass and NoPass attributes cannot be provided together",
              "Attributes 'PASS' and 'NOPASS' conflict with each other",
              "Binding 'act' may not specify both PASS and NOPASS")
    route("C787", "incompatible_attributes",
          "NON_OVERRIDABLE and DEFERRED cannot both appear at (1)",
          "Type-bound procedure 'act' may not be both DEFERRED and NON_OVERRIDABLE")
    route("C788", "missing_deferred",
          "PROCEDURE(interface) at (1) should be declared DEFERRED",
          "DEFERRED is required when an interface-name is provided")
    route("C788", "missing_interface",
          "Interface must be specified for DEFERRED binding at (1)",
          "DEFERRED is only allowed when an interface-name is provided")
    route("C789", "redefer_concrete",
          "'act' at (1) must not be DEFERRED as it overrides a non-DEFERRED binding",
          "Override of non-DEFERRED 'act' must not be DEFERRED")
    route("C790", "nonoverridable_override",
          "'act' at (1) overrides a procedure binding declared NON_OVERRIDABLE",
          "Override of NON_OVERRIDABLE 'act' is not permitted")
    for variant in ["default_private_client", "explicit_private_client", "private_other_module"]:
        route("S7.5.5-007", variant,
              "'secret' of 'record' is PRIVATE at (1)",
              "PRIVATE name 'secret' is accessible only within module 'tbp_provider'",
              "Private binding 'secret' cannot be referenced from this client scope")
    route("S7.5.5-007", "private_inherited",
          "'secret' of 'parent' is PRIVATE at (1)",
          "'secret' of 'child' is PRIVATE at (1)",
          "PRIVATE name 'secret' is accessible only within module 'tbp_provider'")
    route("S7.5.5-007", "private_generic",
          "'g' of 'record' is PRIVATE at (1)",
          "PRIVATE generic binding 'g' cannot be referenced from this client scope")
    if len(result) != 57:
        raise ValueError("diagnostic routes must cover exactly 57 negative cases")
    return result


def build_corpus(root=ROOT):
    c = Corpus(root)
    for build in [grammar_cases, target_cases, generic_cases, nonname_pass_cases,
                  attribute_cases, override_cases, runtime_cases, privacy_cases]:
        build(c)
    if set(c.repairs) != {identifier(r, v, True) for r, v in diagnostic_routes()}:
        raise ValueError("diagnostic routes differ from the negative case set")
    expected = {r: set(v.split()) for r, v in ELIGIBLE.items()}
    if c.coverage() != expected:
        raise ValueError("generated coverage differs from the reviewed finite eligible plan")
    return c.files, c.cases, c.repairs


CONTRACT = """## Source, interpretation and observation boundaries

Source authority is J3/24-007, **18 December 2023**, **688 PDF pages**, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The section starts at physical PDF99 (printed85), continues through PDF100-101
and NOTE3's continuation on PDF102, and ends before the actual 7.5.6 heading.
The 39 base units, 145 fine units, 33 requirement IDs, definitions, classifications
and reciprocal accounting remain those of the source packet.

The author source commit `50be5268940cc2a56523922c331a89bc72fae16c` and coordinator
corrections `6d988a3a6da8f26ca9d589f48a8eea2aaf4e5d1a` and
`e8eb0932bb80d01192e9fac13ff0e171556104c5` are preserved. The coordinator's
original-source review is retained in the session artifact
`type-bound-coordinator-source-review.json`; the integrated source, fixture and
correction decisions are recorded in `doc/source_audits/batch_013.json`.
Eligibility is not fixture approval. This generator neither self-approves
sources/cases nor changes baselines.

### P1-P6 retained premises

* **P1 — live type/rank/state.** Runtime objects are ordinary scalar noncoarray,
  nonpointer and nonallocatable. No abstract object is instantiated. Deferred
  interfaces are implemented by concrete children before invocation; CLASS(base)
  helpers receive live concrete child actuals. There are no unallocated receiver,
  dangling-pointer or whole abstract-parent references.
* **P2 — independent defined inputs/results.** Named setup routines or explicit
  component assignments define every read payload. No structure-constructor
  ordering/default initialization is used to make an oracle cancel its own
  setup error. Calls are evaluated separately; every runtime result is compared
  with an independent integer literal, not only with a second binding's result.
  Results and markers are defined and stay in scope; no evaluation-order or
  short-circuit assumption is used.
* **P3 — actual interfaces and PASS.** Concrete targets are eligible accessible
  module procedures or explicitly interfaced externals. Abstract interface bodies
  import required already-defined types. Default/bare PASS selects the first
  dummy; named PASS selects an existing eligible dummy; NOPASS has no implicit
  object argument. C765's scalar/nonpointer/nonallocatable/same-declared-type,
  assumed-length, polymorphic-iff-extensible and no-VALUE conditions remain.
  Nonpassed actual type/kind/rank and keyword correspondence also remain valid.
* **P4 — inheritance and generic resolution.** Overriding fixtures preserve
  passed-object name/position, all other dummy/result characteristics, PURE/SIMPLE/
  ELEMENTAL relations and public accessibility except the tested C789/C790
  attribute. Named generics use distinguishable nonpassed default INTEGER/REAL
  dummies; no physical kind numbers or dynamic-only overload lookup. Inherited
  private bindings remain inherited, not public and not replaced by a homonym.
* **P5 — private contexts and evidence roles.** Private representations are
  accessed only in the defining module/descendants. Public callers receive values
  through public bindings on accessible objects, even when the type name or
  implementation is private. Named outside-call contrasts have actual PRIVATE
  attribute or bare binding PRIVATE repairs. Internal wrappers are allowed-use
  controls, not effects proving outside inaccessibility. The descendant control
  has a real ancestor separate-module-procedure declaration.
* **P6 — I/O/final/representation limits.** C779's six nameless-generic pairs
  preserve valid operator/assignment/four defined-I/O interfaces while changing
  only NOPASS. Those I/O procedures have correct scalar CLASS dtv, default-kind
  arguments, iotype/v_list only in formatted forms, and the required intents.
  Their bodies assign iostat=0 and do not change iomsg or execute I/O.
  No I/O transfer, finalization, representation or undefined-pointer inquiry is
  implemented for a canonical wrapper graph.

## Reporting, repair and review limits

Numbered grammar/constraint reporting uses 4.2 p2(3).
Named private-binding access under S7.5.5-007 uses **19.3.4 p5 and 4.2 p2(6)**.
That duty is not weakened by the separate old component metadata correction.
Reporting capability is not a requirement for fatal rejection, printed rule
codes or exact prose. These compile manifests expect `diagnose`, allowing a
proper located nonfatal report. No new LFortran-only policy is introduced.

Every negative has one exact source-minimal conforming repair. Diagnostics
bind the intended failing build step, file/span and cause; a provider failure
cannot satisfy an intended client diagnostic. Wrong-role/context messages,
source echo, unsupported language facilities, crashes, verifier errors, timeouts
and resource failures do not corroborate the target. A correct source fixture
can retain a failing compiler observation or an uncorroborated diagnostic.
Expectations are not derived from compiler acceptance, and reference disagreement
does not authorize weakening the source or changing ownership.

The frozen target is `files/toolchains/lfortran-411-a0afaa840b-20260914/bin/lfortran`.
Bounded observations use GNU16.1 in f2023 and Flang22 with the recorded f2018
fallback; no fallback observation is relabelled f2023. Original and refreshed
reports, hashes and per-case current-fingerprint selection are retained in
the phase-2 handoff. They are not a fictitious combined compiler run or approval.

## Existing ownership and pending mechanisms

The author packet preserved its 1395 base execution IDs, paths and fingerprints.
Integration separately retains the current main bindings, including the three
metadata-only component-scope-duty corrections recorded in
`doc/source_audits/component_scope_duty_001.json`. In particular preserve
`S7_5_2_2_001_valid__component_private`,
`__binding_private`, `__private_private` and `__public_public` rather than
copying them under S7.5.5. The genuine S7.5.5-007 outside-call pairs and
S7.5.2.2-001 public-call runtime witnesses are candidates for finite canonical
connections, not automatic facet credit. Any registered targets are listed
separately below; they are not directly
authored facets or additional executions. Registration does not approve a
connection, and link/case/source adjudications remain independently bound.
The current link schema supports explicit finite S-owned diagnostic/control
pairs and singleton runtime-effect or positive-control witnesses. Arbitrary
numbered wrappers and general source-use graphs remain outside those finite
patterns. This generator reads registered links but neither installs them nor
copies their canonical programs.

C784's INTEGER-only binding interface necessarily also violates C765 while
implicit PASS remains. Its NOPASS repair removes passed-object status; adding
a defining-type witness would instead defeat C784's antecedent. This is not
perfect single-clause isolation and is distinct from the avoidable C765-primary
overlap corrected in the separate data-component packet.

C780/C781/C782 canonical interface/wrapper graphs, C783 mixed-access attribution,
conditional operator-result and dtv-type isolation, nameless privacy causality
and unrepresented source-use graphs remain pending. Finalization and extension
source work and the separate A-component fixture review are not altered.
The real-BOZ needs-oracle member and 7.5.2.4 private-identity question remain
out of scope. This is not whole-suite or whole-standard completion.
"""


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues["7.5.5"] = catalogue
    return registry.catalogue_review_state("7.5.5")


def facet_partitions(catalogue, specs, linked=None):
    """Partition one catalogue; an explicit override is scoped to its requirements."""
    requirements = {r["id"]: r for r in catalogue["requirements"]}
    if linked is None:
        sys.path.insert(0, str(ROOT / "tests"))
        from suite_data import Registry
        registry = Registry(ROOT)
        # Case collection requires the pending partition to have been synchronized already.
        linked = {}
        for link in registry.evidence.links.values():
            target = link["target"]
            if target["requirement"] in requirements:
                linked.setdefault(target["requirement"], {})[target["facet"]] = link["id"]
    elif set(linked) - set(requirements):
        raise ValueError("unknown linked requirement for this catalogue: "
                         + ", ".join(sorted(set(linked) - set(requirements))))
    if {s["rule"] for s in specs.values()} - set(requirements):
        raise ValueError("generated case has an unknown primary requirement")
    result = {}
    for rule, requirement in requirements.items():
        direct = {facet for spec in specs.values() if spec["rule"] == rule for facet in spec["facets"]}
        connections = dict(linked.get(rule, {}))
        declared = set(requirement["facets"])
        if (direct | set(connections)) - declared:
            raise ValueError("unknown generated or linked facet for " + rule)
        if direct & set(connections):
            raise ValueError("direct and linked facets overlap for " + rule)
        result[rule] = dict(direct=direct, linked=connections,
                            pending=declared - direct - set(connections))
    return result


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    negative = sum(s["kind"] == "invalid" for s in specs.values())
    runtime = sum(s["phase"] == "run" for s in specs.values())
    controls = len(specs) - negative - runtime
    partitions = facet_partitions(catalogue, specs)
    direct = sum(len(p["direct"]) for p in partitions.values())
    linked = sum(len(p["linked"]) for p in partitions.values())
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    declared = sum(len(r["facets"]) for r in catalogue["requirements"])
    for requirement in catalogue["requirements"]:
        if set(requirement["pending"]) != partitions[requirement["id"]]["pending"]:
            raise ValueError("inconsistent pending partition for " + requirement["id"])
    out = (
        "# Fortran 2023: 7.5.5 Type-bound procedures — phase-2 implementation\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Case and evidence adjudications are maintained in their separate content-bound records.\n\n"
        f"The finite packet has **{len(specs)} cases**: **{negative} diagnostic inputs**, "
        f"**{controls} compile-only positive controls/admissions**, and **{runtime} runtime effect cases**. "
        f"Of **{declared} facets**, **{direct} are directly represented**, "
        f"**{linked} have registered canonical links**, and "
        f"**{pending} remain PENDING**. Representation is not a claim of compiler success, "
        "independent review or source closure.\n\n" + CONTRACT
        + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.5.5 -->"
    )
    out += "\n\n" + "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    out += "<!-- END GENERATED 7.5.5 -->\n\n## Implemented finite case census\n\n"
    out += "| Primary owner | Cases | Diagnostic | Compile control | Runtime | Represented facets |\n"
    out += "| --- | ---: | ---: | ---: | ---: | --- |\n"
    for rule, facets in ELIGIBLE.items():
        rows = [s for s in specs.values() if s["rule"] == rule]
        bad = sum(s["kind"] == "invalid" for s in rows)
        run = sum(s["phase"] == "run" for s in rows)
        out += f"| {rule} | {len(rows)} | {bad} | {len(rows)-bad-run} | {run} | "
        out += ", ".join("`" + f + "`" for f in facets.split()) + " |\n"
    out += "\n## Registered canonical connections\n\n"
    out += ("These targets reuse their canonical cases without adding or duplicating executions. "
            "Registered, independently approved, observed and passing evidence remain separate states; "
            "this table grants no link approval or derived runtime-effect pass.\n\n")
    out += "| Target requirement | Linked facet | Canonical connection |\n"
    out += "| --- | --- | --- |\n"
    for rule, partition in partitions.items():
        for facet, name in sorted(partition["linked"].items()):
            out += f"| {rule} | `{facet}` | `{name}` |\n"
    out += "\n## Complete finite pending plans\n\n"
    out += "This appendix is generated from the canonical JSON `pending` maps, not a stale copy "
    out += "of the original all-pending source packet. Every row below remains **PENDING**; "
    out += "no compiler observation supplies a missing evidence mechanism.\n\n"
    for r in catalogue["requirements"]:
        if not r["pending"]:
            continue
        out += f"### Pending {r['id']}\n\n"
        for facet, plan in r["pending"].items():
            out += f"* **`{facet}`** — {plan}\n"
        out += "\n"
    out += (
        "## Reproduction and gates\n\n"
        "`python3 -B tools/generate_type_bound_fixtures.py --check` checks exact generated "
        "bytes and both document views. `tests/test_type_bound_fixtures.py` checks the "
        "case/facet/pending census, phases, unique repairs, source premises and diagnostic guards. "
        "The author worktree's validation-only index overlay is not merged wholesale. "
        "Coordinator index integration and source/case/evidence adjudications are separate "
        "from code generation and never inferred from compiler observations.\n\n"
        "Independent connection and metadata-renewal decisions are recorded in "
        "`doc/source_audits/batch_021.json`, including the restored/partial-state and explicit-owner "
        "corrections. Current content-bound fixture, source and connection approvals remain separate. "
        "Retained observation handoffs and per-case current-fingerprint indexes record "
        "reference failures and source-valid controls without inventing a combined run. "
        "The original `type-bound-phase2-handoff.json` and subsequent correction handoffs "
        "remain separate provenance records; this view does not confer approval.\n"
    )
    return out


def synced_catalogue(catalogue, specs, linked=None):
    catalogue = json.loads(json.dumps(catalogue))
    partitions = facet_partitions(catalogue, specs, linked)
    for r in catalogue["requirements"]:
        rows = [s for s in specs.values() if s["rule"] == r["id"]]
        partition = partitions[r["id"]]
        represented, connections = partition["direct"], partition["linked"]
        for facet in represented | set(connections):
            r["pending"].pop(facet, None)
        if set(r["pending"]) != partition["pending"]:
            raise ValueError("missing original pending source plans for " + r["id"])
        if rows:
            old = r["oracle"].split("\n\nPhase 2 implementation:", 1)[0]
            if r["id"] == "S7.5.5-001":
                old = ("Named setup assigns first/second payloads 17/29. Omitted and explicit bindings "
                       "are each checked against independent expected results 17/59, not just each other; "
                       "the second function computes 2*29+1. A separate renamed NOPASS target has expected "
                       "result22 and preserves payload11. Every receiver/result is defined and live.")
            elif r["id"] == "S7.5.5-004":
                old = ("Both independent declaration-order variants use named payload setup. "
                       "Integer/real generic branches must yield 11/22 with payload5 and 13/24 with "
                       "payload7, using distinct nonpassed argument types and separate call evaluation. "
                       "This tests cumulative membership and receiver use without real arithmetic or "
                       "constructor-order cancellation.")
            elif r["id"] == "S7.5.5-005":
                old = ("The directly owned explicit-public-over-private runtime observes an allowed client "
                       "call and integer result17. The existing S7.5.2.2-001 default-public runtime and "
                       "S7.5.5-007 outside-call/public-repair pairs are canonical reuse candidates, not "
                       "automatically linked facets. "
                       "A legal owner wrapper alone would not establish outside inaccessibility. Original "
                       "primary owners, diagnostic duties, runtime premises and independent literal oracles "
                       "are preserved. The exact registered map and pending plans determine the current "
                       "partition; registration is not connection approval.")
                r["oracle_limitation"] = (
                    "Direct runtime cases make only legal calls. Any registered outside-call "
                    "diagnostic/control pair retains S7.5.5-007 ownership and its reporting basis, "
                    "not a new duty for this default rule. Component PRIVATE before CONTAINS and "
                    "binding PRIVATE after it have independent subjects.")
            elif r["id"] == "S7.5.5-006":
                old = ("Two directly owned legal-call cases expose17 through an inaccessible type name "
                       "and through a public generic naming a private specific. The existing S7.5.2.2-001 "
                       "public-type/public-object and private-implementation-name runtimes, with their "
                       "defined13/17/19observations, are canonical reuse candidates rather than new local "
                       "programs. Their allowed object-based calls do not establish direct private-name "
                       "rejection or a completed general use graph. The exact registered map and pending "
                       "plans determine the current partition; registration is not connection approval.")
            bad = sum(x["kind"] == "invalid" for x in rows)
            run = sum(x["phase"] == "run" for x in rows)
            r["oracle"] = old + (
                f"\n\nPhase 2 implementation: {len(rows)} uniquely named cases represent "
                f"{len(represented)} facets: {bad} diagnostic inputs, {len(rows)-bad-run} compile-only "
                f"positive controls/admissions and {run} runtime effect cases. "
                f"{len(r['pending'])} source-use/conditional facets remain pending. "
                "Authorship and observations do not establish adjudication; approval status is held "
                "in separate content-bound review records. A control remains distinct from a runtime effect."
            )
            if connections:
                r["oracle"] += (
                    f" {len(connections)} additional facets have registered canonical links, not directly "
                    "owned cases or additional executions. Connection approval is independently content-bound."
                    " Registered canonical links: "
                    + ", ".join(f"{facet} ({name})" for facet, name in sorted(connections.items())) + ".")
            elif r["id"] in ("S7.5.5-005", "S7.5.5-006"):
                r["oracle"] += " No canonical links are registered for this requirement."
    return catalogue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true",
                        help="synchronize owned pending maps, phase text and both Markdown regions")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    outputs, specs, _ = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, content in outputs.items()
                 if not p.is_file() or p.read_bytes() != content]
        actual = {p for p in (ROOT / "tests/fixtures").glob(PREFIX + "*/*") if p.is_file()}
        stale += [str(p.relative_to(ROOT)) for p in actual - set(outputs)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale type-bound packet: " + ", ".join(sorted(stale)))
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    partitions = facet_partitions(updated, specs)
    direct = sum(len(p["direct"]) for p in partitions.values())
    linked = sum(len(p["linked"]) for p in partitions.values())
    pending = sum(len(p["pending"]) for p in partitions.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files for {len(specs)} "
          f"type-bound cases: {direct} direct, {linked} registered linked and {pending} pending facets.")


if __name__ == "__main__":
    main()
