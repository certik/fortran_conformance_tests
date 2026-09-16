#!/usr/bin/env python3
"""Generate bounded PDT parameter definition, value and ordering fixtures."""
import argparse
import json
from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = [
    "not implemented", "not yet implemented", "unimplemented",
    "not supported", "unsupported", "internal compiler error",
]


def source(text):
    return textwrap.dedent(text).strip() + "\n"


def definition(header, declarations, prefix=""):
    return ("module parameter_definition\nimplicit none\n" + prefix
            + "type :: " + header + "\n" + declarations
            + "\nend type\nend module\n")


class Corpus:
    def __init__(self, namespace="parameter", root=ROOT):
        self.namespace = namespace
        self.root = root
        self.files = {}
        self.cases = {}

    def put(self, relative, content):
        path = self.root / relative
        if path in self.files:
            raise ValueError(f"duplicate generated path: {relative}")
        raw = content.encode("ascii")
        if path.suffix == ".f90" and max(map(len, raw.splitlines()), default=0) > 132:
            raise ValueError(f"unintended line-length boundary: {relative}")
        self.files[path] = raw

    def compile(self, rule, variant, facets, text, diagnostic=None, requires=()):
        kind = "invalid" if diagnostic else "valid"
        name = rule + "_" + kind + "__" + self.namespace + "_" + variant
        folder = "tests/fixtures/derived_" + self.namespace + "_" + rule.lower() + "_" + variant + "_" + kind
        expectation = dict(phase="compile", step="source", outcome="diagnose" if diagnostic else "success")
        if diagnostic:
            expectation["diagnostic"] = diagnostic
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=facets, standard="f2023",
            evidence="effect" if diagnostic else "positive-control", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=expectation)
        if requires:
            manifest["requires"] = list(requires)
        self.put(folder + "/source.f90", text)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, facets=facets, kind=kind, phase="compile",
                                path=folder + "/fixture.json")
        return name

    def pair(self, rule, variant, facets, bad, wrong, repaired, location, messages,
             relation=False, last_occurrence=False, requires=()):
        if bad.count(wrong) != 1:
            raise ValueError(f"{rule}/{variant}: repair is not unique")
        lines = bad.splitlines()
        points = [index + 1 for index, line in enumerate(lines) if line == location]
        if not points or (len(points) != 1 and not last_occurrence):
            raise ValueError(f"{rule}/{variant}: diagnostic source point is not unique")
        diagnostic = dict(file="source.f90", line=points[-1] if last_occurrence else points[0],
                          contains_any=messages, excludes_any=EXCLUDED)
        if relation:
            diagnostic["end_line"] = lines.index("end type") + 1
        self.compile(rule, variant, facets, bad, diagnostic, requires=requires)
        self.compile(rule, variant + "_repair", facets, bad.replace(wrong, repaired, 1),
                     requires=requires)

    def run(self, rule, variant, facets, body, evidence="effect", requires=()):
        name = rule.replace(".", "_").replace("-", "_") + "_valid__" + variant
        header = (f"! rule: {rule}\n! covers: {' '.join(facets)}\n"
                  f"! evidence: {evidence}\n! standard: f2023\n")
        if requires:
            header += "! requires: " + " ".join(requires) + "\n"
        path = "tests/clause07/" + name + ".f90"
        self.put(path, header + source(body))
        self.cases[name] = dict(rule=rule, facets=facets, kind="valid", phase="run", path=path)

    def coverage(self):
        result = {}
        for case in self.cases.values():
            result.setdefault(case["rule"], set()).update(case["facets"])
        return result


def definition_cases(c):
    for category, facet in (("kind", "default-integer-kind-parameter"),
                            ("len", "default-integer-length-parameter")):
        c.compile("R732", category, [facet], definition("packet(tag)", f"integer, {category} :: tag"))
        c.compile("R732", category + "_selected", ["selected-integer-specification"],
                  definition("packet(tag)", f"integer(ik), {category} :: tag",
                             "integer, parameter :: ik = selected_int_kind(18)\n"))
    c.compile("R732", "declaration_list", ["declaration-list"],
              definition("packet(left,right)", "integer, kind :: left = 2, right"))
    base = definition("packet(tag)", "integer, kind :: tag")
    c.pair("R732", "comma", ["comma-separator"], base.replace("integer, kind", "integer kind"),
           "integer kind", "integer, kind", "integer kind :: tag",
           ["Missing comma between INTEGER and KIND in a type parameter definition",
            "Token '::' is unexpected here"])
    c.pair("R732", "colons", ["double-colon-separator"], base.replace(":: tag", ": tag"),
           ": tag", ":: tag", "integer, kind : tag",
           ["Missing double colon in a type parameter definition", "Token ':' is unexpected here"])
    c.pair("R732", "integer_prefix", ["integer-prefix-required"], base.replace("integer, kind", "real, kind"),
           "real, kind", "integer, kind", "real, kind :: tag",
           ["Type parameter 'tag' must be declared INTEGER",
            "Component with KIND attribute at (1) must be INTEGER"])

    c.compile("R733", "no_defaults", ["without-default"],
              definition("packet(tag,width)", "integer, kind :: tag\ninteger, len :: width"))
    c.compile("R733", "literal_defaults", ["literal-default"],
              definition("packet(tag,width)", "integer, kind :: tag = 2\ninteger, len :: width = 3"))
    c.compile("R733", "expression_defaults", ["expression-default"],
              definition("packet(left,right)", "integer, kind :: right = (2+3), left"))
    bad = definition("packet(width)", "integer, len :: width =")
    c.pair("R733", "missing_default", ["default-needs-expression"], bad, "width =", "width = 3",
           "integer, len :: width =", ["Missing default expression for type parameter 'width'",
                                     "Expected an initialization expression"], relation=True)

    for category, facet in (("kind", "listed-kind-name"), ("len", "listed-length-name")):
        c.compile("C746", category, [facet], definition("packet(tag)", f"integer, {category} :: tag"))
        bad = definition("packet(tag)", f"integer, kind :: tag\ninteger, {category} :: extra")
        c.pair("C746", "unlisted_" + category, ["unlisted-local-name"], bad,
               "packet(tag)", "packet(tag,extra)", f"integer, {category} :: extra",
               ["Type parameter 'extra' is not listed in the TYPE statement",
                "'extra' is not a parameter of this derived type",
                "The component with KIND or LEN attribute at (1) does not not appear in the type parameter list at (2)"])
    bad = definition("packet", "integer, kind :: tag")
    c.pair("C746", "missing_header", ["missing-local-header-list"], bad,
           "type :: packet", "type :: packet(tag)", "integer, kind :: tag",
           ["Type parameter 'tag' is not listed in the TYPE statement",
            "'tag' is not a parameter of this derived type",
            "Type parameter 'tag' at (1) has no corresponding entry in the type parameter name list at (2)"])

    for category, facet in (("kind", "complete-kind-list"), ("len", "complete-length-list")):
        c.compile("C747", category, [facet],
                  definition("packet(left,right)", f"integer, {category} :: left, right"))
    c.compile("C747", "mixed", ["mixed-categories"],
              definition("packet(tag,width)", "integer, kind :: tag\ninteger, len :: width"))
    c.compile("C747", "reversed_statements", ["definition-order-independent"],
              definition("packet(left,right)", "integer, kind :: right\ninteger, kind :: left"))
    c.compile("C747", "reversed_list", ["definition-order-independent"],
              definition("packet(left,right)", "integer, kind :: right, left"))
    for absent, existing, inserted in (
            ("width", "integer, kind :: tag", "integer, len :: width"),
            ("tag", "integer, len :: width", "integer, kind :: tag")):
        bad = definition("packet(tag,width)", existing)
        c.pair("C747", "missing_" + absent, ["missing-definition"], bad,
               existing, existing + "\n" + inserted, "type :: packet(tag,width)",
               [f"Type parameter '{absent}' has no definition",
                f"No definition found for type parameter '{absent}'",
                f"Parameterized type 'packet' does not have a component corresponding to parameter '{absent}' at (1)"],
               relation=True)
    bad = definition("packet(tag)", "integer, kind :: tag, tag")
    c.pair("C747", "duplicate_list", ["duplicate-in-one-statement"], bad,
           "tag, tag", "tag", "integer, kind :: tag, tag",
           ["Type parameter 'tag' is defined more than once",
            "Type parameter 'tag' was already declared in this derived type",
            "Component 'tag' at (1) already declared at (2)"])
    bad = definition("packet(width)", "integer, len :: width\ninteger, len :: width")
    c.pair("C747", "duplicate_statement", ["duplicate-in-separate-statements"], bad,
           "integer, len :: width\ninteger, len :: width", "integer, len :: width",
           "integer, len :: width", ["Type parameter 'width' is defined more than once",
                                   "Type parameter 'width' was already declared in this derived type",
                                   "Component 'width' at (1) already declared at (2)"],
           last_occurrence=True)
    c.compile("R734", "kind", ["kind-alternative"],
              definition("packet(extent)", "integer, kind :: extent"))
    c.compile("R734", "len", ["len-alternative"],
              definition("packet(tag)", "integer, len :: tag"))


def parameter_probe(category, declaration, actual, expected, integer_kind="kind(0)", prefix=""):
    return f"""
        program parameter_probe
            implicit none
        {prefix}
            type :: packet(tag)
                {declaration}, {category} :: tag
                integer :: payload
            end type
            type(packet({actual})) :: item
            item%payload = 7
            if (item%tag /= {expected}) error stop 1
            if (kind(item%tag) /= {integer_kind}) error stop 2
            call check(item%tag)
        contains
            subroutine check(value)
                integer({integer_kind}), intent(in) :: value
                if (value /= {expected}) error stop 3
            end subroutine
        end program
    """


def value_cases(c):
    for category, value in (("kind", "2"), ("len", "3")):
        c.run("S7.5.3.1-001", category + "_default_integer",
              ["default-kind-parameter-integer-kind" if category == "kind"
               else "default-length-parameter-integer-kind"],
              parameter_probe(category, "integer", value, value))
    for variant, value in (("negative", "-2"), ("zero", "0"), ("positive", "3")):
        c.run("S7.5.3.1-002", "kind_default_" + variant, ["kind-default-value"],
              parameter_probe("kind", "integer", "", value).replace(
                  "integer, kind :: tag", "integer, kind :: tag = " + value).replace("packet()", "packet"))
    c.run("S7.5.3.1-002", "length_default", ["length-default-value"],
          parameter_probe("len", "integer", "", "3").replace(
              "integer, len :: tag", "integer, len :: tag = 3").replace("packet()", "packet"))
    c.run("S7.5.3.1-002", "expression_and_override", ["expression-default-value"], """
        program defaults
            implicit none
            type :: packet(tag)
                integer, kind :: tag = 2+3
                integer :: payload
            end type
            type(packet) :: defaulted
            type(packet(7)) :: explicit_value
            defaulted%payload = 0
            explicit_value%payload = 0
            if (defaulted%tag /= 5) error stop 1
            if (explicit_value%tag /= 7) error stop 2
        end program
    """)
    for category, value in (("kind", "-2"), ("len", "3")):
        c.run("S7.5.3.1-002", category + "_default_to_selected",
              ["default-to-selected-integer-conversion"],
              parameter_probe(category, "integer(ik)", "", value, "ik",
                              "integer, parameter :: ik = selected_int_kind(18)").replace(
                  f"integer(ik), {category} :: tag", f"integer(ik), {category} :: tag = {value}"
              ).replace("packet()", "packet"))
        c.run("S7.5.3.1-002", category + "_selected_to_default",
              ["selected-to-default-integer-conversion"],
              parameter_probe(category, "integer", "", value, prefix=
                              "integer, parameter :: ik = selected_int_kind(18)").replace(
                  f"integer, {category} :: tag", f"integer, {category} :: tag = {value}_ik"
              ).replace("packet()", "packet"))
    c.run("S7.5.3.1-002", "per_declarator", ["defaults-per-declarator"], """
        program defaults
            implicit none
            type :: packet(left,right)
                integer, kind :: left = 2, right = 5
                integer :: payload
            end type
            type(packet) :: item
            item%payload = 0
            if (item%left /= 2) error stop 1
            if (item%right /= 5) error stop 2
        end program
    """)


def specification_cases(c):
    for category, bound, facet, first, second, size_a, size_b in (
            ("kind", "extent", "kind-primary-in-component-bound", 2, 5, 2, 5),
            ("len", "extent+1", "length-primary-in-component-bound", 2, 4, 3, 5)):
        c.run("S7.5.3.1-003", category + "_component_bound", [facet], f"""
            program bounds
                implicit none
                type :: packet(extent)
                    integer, {category} :: extent
                    integer :: values({bound})
                end type
                type(packet({first})) :: a
                type(packet({second})) :: b
                if (a%extent /= {first} .or. b%extent /= {second}) error stop 1
                if (size(a%values) /= {size_a} .or. size(b%values) /= {size_b}) error stop 2
                if (lbound(a%values,1) /= 1 .or. lbound(b%values,1) /= 1) error stop 3
                a%values = 3
                b%values = 7
                if (any(a%values /= 3) .or. any(b%values /= 7)) error stop 4
            end program
        """)
    c.run("S7.5.3.1-003", "component_character", ["length-primary-in-component-length"], """
        program lengths
            implicit none
            type :: packet(count)
                integer, len :: count
                character(count) :: text
            end type
            type(packet(2)) :: a
            type(packet(3)) :: b
            if (a%count /= 2 .or. b%count /= 3) error stop 1
            if (len(a%text) /= 2 .or. len(b%text) /= 3) error stop 2
            a%text = 'ab'
            b%text = 'xyz'
            if (a%text /= 'ab' .or. b%text /= 'xyz') error stop 3
        end program
    """)
    c.run("S7.5.3.1-003", "mixed_parameters", ["mixed-parameter-expression"], """
        program bounds
            implicit none
            type :: packet(tag,extent)
                integer, kind :: tag
                integer, len :: extent
                integer :: values(tag+extent)
            end type
            type(packet(2,3)) :: a
            type(packet(3,4)) :: b
            if (a%tag /= 2 .or. a%extent /= 3) error stop 1
            if (b%tag /= 3 .or. b%extent /= 4) error stop 2
            if (size(a%values) /= 5 .or. size(b%values) /= 7) error stop 3
            a%values = 1
            b%values = 2
            if (any(a%values /= 1) .or. any(b%values /= 2)) error stop 4
        end program
    """)


def constant_cases(c):
    c.run("S7.5.3.1-004", "dependent_default", ["prior-kind-in-parameter-default"], """
        program defaults
            implicit none
            type :: packet(tag,extent)
                integer, kind :: tag = 2
                integer, len :: extent = tag+1
                integer :: value
            end type
            type(packet) :: a
            type(packet(tag=5)) :: b
            a%value = 0
            b%value = 0
            if (a%tag /= 2 .or. a%extent /= 3) error stop 1
            if (b%tag /= 5 .or. b%extent /= 6) error stop 2
        end program
    """)
    c.run("S7.5.3.1-004", "integer_selector", ["prior-kind-in-integer-selector"], """
        program selectors
            implicit none
            integer, parameter :: ik = selected_int_kind(18)
            type :: packet(carrier,count)
                integer, kind :: carrier = kind(0)
                integer(carrier), len :: count = 3
                integer :: value
            end type
            type(packet) :: a
            type(packet(ik)) :: b
            a%value = 0
            b%value = 0
            if (a%carrier /= kind(0) .or. b%carrier /= ik) error stop 1
            if (kind(a%count) /= kind(0) .or. kind(b%count) /= ik) error stop 2
            call default_value(a%count)
            call selected_value(b%count)
        contains
            subroutine default_value(value)
                integer, intent(in) :: value
                if (value /= 3) error stop 3
            end subroutine
            subroutine selected_value(value)
                integer(ik), intent(in) :: value
                if (value /= 3_ik) error stop 4
            end subroutine
        end program
    """)
    c.run("S7.5.3.1-004", "component_default", ["prior-kind-in-component-initialization"], """
        program initialized
            implicit none
            type :: packet(tag)
                integer, kind :: tag
                integer :: value = tag+2
            end type
            type(packet(2)) :: a
            type(packet(5)) :: b
            if (a%value /= 4 .or. b%value /= 7) error stop 1
        end program
    """)


def order_cases(c):
    for variant, header, definitions, facet in (
            ("header", "left,right", "integer, kind :: left\ninteger, kind :: right", "header-position-values"),
            ("reversed_statements", "left,right", "integer, kind :: right\ninteger, kind :: left",
             "definition-statement-order"),
            ("reversed_list", "left,right", "integer, kind :: right,left", "declarator-list-order"),
            ("mixed_categories", "left,right", "integer, kind :: right\ninteger, len :: left",
             "mixed-kind-length-order")):
        c.run("S7.5.3.2-001", variant, [facet],
              "program parameter_order\nimplicit none\ntype :: packet(" + header + ")\n"
              + definitions + "\ninteger :: payload\nend type\n"
              "type(packet(2,3)) :: item\nitem%payload = 0\n"
              "if (item%left /= 2 .or. item%right /= 3) error stop 1\nend program\n")
    parent = ("type :: parent(first,second)\ninteger, kind :: first\n"
              "integer, len :: second\ninteger :: payload\nend type\n")
    for variant, child, parameters, checks, facet in (
            ("parent_prefix", "type, extends(parent) :: child(third)\ninteger, kind :: third\nend type\n",
             "2,3,5", "if (item%third /= 5) error stop 2\n", "parent-prefix"),
            ("local_suffix", "type, extends(parent) :: child(third,fourth)\n"
             "integer, kind :: fourth,third\nend type\n", "2,3,5,7",
             "if (item%third /= 5 .or. item%fourth /= 7) error stop 2\n", "local-header-suffix"),
            ("inherited_only", "type, extends(parent) :: child\nend type\n",
             "2,3", "", "inherited-only-extension"),
            ("ancestor_chain", "type, extends(parent) :: middle(third)\ninteger, kind :: third\nend type\n"
             "type, extends(middle) :: child(fourth)\ninteger, len :: fourth\nend type\n",
             "2,3,5,7", "if (item%third /= 5 .or. item%fourth /= 7) error stop 2\n",
             "multi-generation-order")):
        c.run("S7.5.3.2-002", variant, [facet],
              "program inherited_order\nimplicit none\n" + parent + child
              + "type(child(" + parameters + ")) :: item\nitem%payload = 0\n"
              "if (item%first /= 2 .or. item%second /= 3) error stop 1\n"
              + checks + "end program\n")


def build_corpus():
    corpus = Corpus()
    definition_cases(corpus)
    value_cases(corpus)
    specification_cases(corpus)
    constant_cases(corpus)
    order_cases(corpus)
    return corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    corpus = build_corpus()
    for path, raw in corpus.files.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                parser.error("generated input differs: " + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f"{'Checked' if args.check else 'Generated'} {len(corpus.files)} files for {len(corpus.cases)} parameter cases.")


if __name__ == "__main__":
    main()
