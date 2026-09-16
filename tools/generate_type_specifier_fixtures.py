#!/usr/bin/env python3
"""Bounded compile admissions and causal diagnostic pairs for derived-type specifiers."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.9"
CATALOGUE = "doc/catalogues/derived_types_7_5_9.json"
VIEW = "doc/fortran_2023_7_5_9.md"
ELIGIBLE = {
    "R754": ["bare-nonparameterized-name", "bare-defaulted-parameterized-name",
             "explicit-positional-list", "explicit-keyword-list", "mixed-positional-keyword-list",
             "empty-parenthesized-list", "missing-list-separator"],
    "R755": ["keyword-equals-not-arrow", "nonempty-keyword", "nonempty-parameter-value"],
    "C795": ["local-derived-type", "use-associated-type", "ordinary-object-not-type-name",
             "inaccessible-provider-type"],
    "C796": ["nonparameterized-list-exclusion"],
    "C797": ["required-values-supplied", "missing-required-kind", "missing-required-length",
             "duplicate-keyword", "positional-keyword-duplicate"],
    "C798": ["keyword-then-positional", "positional-keyword-positional"],
    "C799": ["unknown-keyword", "component-name-not-parameter"],
    "C7100": ["dummy-declaration", "associate-name-type-guard", "dummy-allocation",
              "ordinary-local-declaration-exclusion"],
}
EXCLUDED = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "implementation limitation", "internal compiler error", "ASR verify", "ASR verifier",
    "module failed verification", "out of memory", "cannot allocate memory", "segmentation fault",
    "unexpected end of file", "unexpected eof", "missing end", "stack trace",
]


def identifier(rule, variant, invalid=False):
    return rule + ("_invalid__type_specifier_" if invalid else "_valid__type_specifier_") + variant


def formal(name, category, default=None):
    return dict(name=name, category=category, default=default)


def entry(keyword, value, operator="=", parenthesized=False):
    return dict(keyword=keyword, value=value, operator=operator, parenthesized=parenthesized)


def scenario(formals=(), entries=(), listed=True, context="declaration", type_name="record",
             symbol_kind="derived", accessible=True, separator=","):
    return dict(formals=list(formals), entries=list(entries), listed=listed, context=context,
                type_name=type_name, symbol_kind=symbol_kind, accessible=accessible, separator=separator)


def specifier(plan):
    result = plan["type_name"]
    if not plan["listed"]:
        return result
    items = []
    for item in plan["entries"]:
        value = "" if item["value"] is None else str(item["value"])
        if item["parenthesized"]:
            value = "(" + value + ")"
        prefix = "" if item["keyword"] is None else item["keyword"] + item["operator"]
        items.append(prefix + value)
    return result + "(" + plan["separator"].join(items) + ")"


def model(plan):
    """Finite admission checks; invalid lists never receive a value correspondence."""
    if plan["symbol_kind"] in ("intrinsic", "enum", "enumeration"):
        raise ValueError("legitimate R703 alternatives are outside this derived-type-spec model")
    formals = {f["name"]: f for f in plan["formals"]}
    if len(formals) != len(plan["formals"]):
        raise ValueError("formal definitions must be unique")
    if plan["symbol_kind"] != "derived" or not plan["accessible"]:
        return dict(issues=["C795"], mapping=None)
    if plan["listed"] and (not plan["entries"] or plan["separator"] != ","):
        return dict(issues=["R754"], mapping=None)
    if any(e["keyword"] == "" or e["operator"] != "=" or e["value"] is None for e in plan["entries"]):
        return dict(issues=["R755"], mapping=None)
    if plan["listed"] and not formals:
        return dict(issues=["C796"], mapping=None)
    named_seen = False
    for item in plan["entries"]:
        if item["keyword"] is None and named_seen:
            return dict(issues=["C798"], mapping=None)
        named_seen = named_seen or item["keyword"] is not None
    if any(e["keyword"] is not None and e["keyword"] not in formals for e in plan["entries"]):
        return dict(issues=["C799"], mapping=None)
    issues, supplied = set(), {}
    positional = 0
    for item in plan["entries"]:
        if item["keyword"] is None:
            if positional >= len(formals):
                issues.add("C797")
                continue
            name = plan["formals"][positional]["name"]
            positional += 1
        else:
            name = item["keyword"]
        if name in supplied:
            issues.add("C797")
        value = item["value"]
        supplied[name] = value
        if formals[name]["category"] == "kind" and type(value) is not int:
            issues.add("C701")
        if value == "*" and plan["context"] not in ("dummy", "associate", "dummy-allocation"):
            issues.add("C7100")
        if value == ":":
            issues.add("C702")
        if type(value) is not int and value not in ("*", ":"):
            issues.add("R701")
    for name, f in formals.items():
        if name not in supplied:
            if f["default"] is None:
                issues.add("C797")
            else:
                supplied[name] = f["default"]
    return dict(issues=sorted(issues), mapping=None if issues else supplied)


def allocation_model(dummy, actual, allocated_values, objects):
    issues = []
    if not objects:
        return ["R929"]
    if dummy["type"] != actual["type"] or dummy["polymorphic"] != actual["polymorphic"]:
        issues.append("15.5.2.6p2")
    if dummy["rank"] != actual["rank"] or dummy["kinds"] != actual["kinds"]:
        issues.append("15.5.2.6p3")
    if dummy["deferred"] != actual["deferred"]:
        issues.append("15.5.2.6p4")
    if not dummy["allocatable"] or not actual["allocatable"]:
        issues.append("15.5.2.7p2")
    for parameter, value in dummy["kinds"].items():
        if type(allocated_values[parameter]) is not int:
            issues.append("C701")
        if allocated_values[parameter] != value:
            issues.append("C940")
    for parameter, value in allocated_values.items():
        assumed_by_all = all(obj["dummy"] and parameter in obj["assumed"] for obj in objects)
        if (value == "*") != assumed_by_all:
            issues.append("C939")
    return sorted(set(issues))


def definition(formals, name="record"):
    header = name + ("(" + ",".join(f["name"] for f in formals) + ")" if formals else "")
    result = "type :: " + header + "\n"
    for f in formals:
        result += f"integer, {f['category']} :: {f['name']}"
        if f["default"] is not None:
            result += "=" + str(f["default"])
        result += "\n"
    return result + "integer :: payload\nend type " + name + "\n"


def declaration_source(plan, before=""):
    return ("module specifier_definitions\nimplicit none\n" + definition(plan["formals"])
            + before + f"type({specifier(plan)}) :: value\nend module specifier_definitions\n")


def diagnostic_routes():
    """Prospective role/property predicates, not a claim that every string was observed."""
    return {
        ("R754", "empty_list"): [
            "Type parameter list for derived type 'record' must not be empty",
            "Empty type parameter specification list is not allowed for 'record'"],
        ("R754", "missing_separator"): [
            "Missing comma in the type parameter specification list of 'record'",
            "Expected ',' between type parameter specifications for 'record'"],
        ("R755", "arrow"): [
            "Expected '=' after type parameter keyword 'n'",
            "Type parameter keyword 'n' uses '=' rather than '=>'"],
        ("R755", "empty_keyword"): [
            "Expected a type parameter keyword before '=' in derived type specifier 'record'",
            "Missing type parameter keyword in derived type specifier 'record'"],
        ("R755", "empty_value"): [
            "Missing value for type parameter 'n' in derived type specifier 'record'",
            "Expected a value for type parameter 'n' in derived type specifier 'record'"],
        ("C795", "ordinary_object"): [
            "'scalar_name' is not the name of a derived type",
            "'scalar_name' is not a derived type",
            "Derived type `scalar_name` is not defined",
            "Derived type 'scalar_name' is not declared",
            "Derived type 'scalar_name' has not been declared",
            "Derived type 'scalar_name' at (1) is being used before it is defined",
            "Type name 'scalar_name' denotes a data object, not a derived type"],
        ("C795", "private_type"): [
            "'hidden' is not an accessible derived type",
            "'hidden' is not the name of a derived type",
            "Derived type 'hidden' is not declared",
            "Derived type 'hidden' has not been declared",
            "Derived type 'hidden' not found",
            "Derived type 'hidden' at (1) is being used before it is defined"],
        ("C796", "nonparameterized_list"): [
            "Derived type 'record' is not parameterized",
            "Derived type 'record' has no type parameters",
            "'record' is not a parameterized derived type",
            "Type 'record' is not parameterized and so the type parameter spec list at (1) may not appear"],
        ("C797", "missing_kind"): [
            "No value was provided for type parameter 'k'",
            "Type parameter 'k' lacks a value and has no default",
            "The derived parameter 'k' at (1) does not have a default value",
            "Type parameter 'k' of derived type 'record' needs a value because it has no default"],
        ("C797", "missing_length"): [
            "No value was provided for type parameter 'n'",
            "Type parameter 'n' lacks a value and has no default",
            "The derived parameter 'n' at (1) does not have a default value",
            "Type parameter 'n' of derived type 'record' needs a value because it has no default"],
        ("C797", "duplicate_keyword"): [
            "Multiple values given for type parameter 'n'",
            "Type parameter 'n' was already specified",
            "Type parameter 'n' is specified more than once",
            "Duplicate value for type parameter 'n'"],
        ("C797", "positional_keyword_duplicate"): [
            "Multiple values given for type parameter 'k'",
            "Type parameter 'k' was already specified",
            "Type parameter 'k' is specified more than once",
            "Duplicate value for type parameter 'k'"],
        ("C798", "keyword_then_positional"): [
            "Positional argument after keyword argument in parameterized derived type 'record'",
            "A positional type parameter specification may not follow a keyword specification",
            "Type parameter specification without a keyword follows one with a keyword",
            "Type parameter value must have a keyword after a keyword type parameter value"],
        ("C798", "positional_keyword_positional"): [
            "Positional argument after keyword argument in parameterized derived type 'record'",
            "A positional type parameter specification may not follow a keyword specification",
            "Type parameter specification without a keyword follows one with a keyword",
            "Type parameter value must have a keyword after a keyword type parameter value"],
        ("C799", "unknown_keyword"): [
            "'nn' is not the name of a parameter for derived type 'record'",
            "Type parameter keyword 'nn' is not a parameter of derived type 'record'",
            "Unknown type parameter keyword 'nn' for derived type 'record'"],
        ("C799", "component_keyword"): [
            "'payload' is not the name of a parameter for derived type 'record'",
            "Type parameter keyword 'payload' is not a parameter of derived type 'record'",
            "Component name 'payload' is not a type parameter keyword of 'record'"],
        ("C7100", "local_assumed_length"): [
            "The object 'value' at (1) with ASSUMED type parameters must be a dummy or a SELECT TYPE selector",
            "Assumed type parameter 'n' is not allowed for local variable 'value'",
            "Object 'value' with assumed type parameter 'n' must be a dummy argument",
            "Assumed length type parameter 'n' in a declaration requires a dummy argument or associate name"],
    }


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="type_specifier", root=root)
        self.repairs = {}
        self.inputs = {}

    def fixture(self, rule, variant, facets, inputs, plan, premises, diagnostic=None):
        name = identifier(rule, variant, diagnostic is not None)
        if name in self.cases:
            raise ValueError("duplicate case " + name)
        inputs = {"source.f90": inputs} if isinstance(inputs, str) else inputs
        inputs = {file: text.strip() + "\n" for file, text in inputs.items()}
        folder = "tests/fixtures/type_specifier_" + name.lower()
        steps = []
        for filename, source in inputs.items():
            stem = Path(filename).stem
            steps.append(dict(id=stem, source=filename, language="fortran", form="free",
                              output=stem + ".o", depends_on=[step["id"] for step in steps]))
            self.put(folder + "/" + filename, source)
        expectation = dict(phase="compile", step=steps[-1]["id"],
                           outcome="diagnose" if diagnostic is not None else "success")
        if diagnostic is not None:
            expectation["diagnostic"] = diagnostic
        evidence = "effect" if diagnostic is not None else "positive-control"
        manifest = dict(schema_version=1, id=name, rule=rule, facets=list(facets), standard="f2023",
                        evidence=evidence, files=list(inputs), build=steps, expect=expectation)
        path = folder + "/fixture.json"
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        self.inputs[name] = inputs
        self.cases[name] = dict(rule=rule, facets=list(facets), kind="invalid" if diagnostic else "valid",
                                phase="compile", evidence=evidence, path=path, plan=copy.deepcopy(plan),
                                premises=premises)
        return name

    def control(self, rule, variant, facets, inputs, plan, premises):
        if model(plan)["issues"]:
            raise ValueError("invalid control model: " + variant)
        return self.fixture(rule, variant, facets, inputs, plan, premises)

    def negative(self, rule, variant, facet, inputs, plan, control, wrong, repaired,
                 anchor, edit_file="source.f90", anchor_file="source.f90", premises=""):
        inputs = {"source.f90": inputs} if isinstance(inputs, str) else inputs
        inputs = {file: text.strip() + "\n" for file, text in inputs.items()}
        good = self.inputs[control]
        if set(inputs) != set(good) or self.cases[control]["rule"] != rule:
            raise ValueError("repair must keep the same source set and primary owner")
        if [file for file in inputs if inputs[file] != good[file]] != [edit_file]:
            raise ValueError("repair must change exactly the designated source")
        if inputs[edit_file].count(wrong) != 1 or inputs[edit_file].replace(wrong, repaired, 1) != good[edit_file]:
            raise ValueError("repair is not one exact source-minimal substitution")
        points = [i for i, line in enumerate(inputs[anchor_file].splitlines(), 1) if line == anchor]
        if len(points) != 1:
            raise ValueError("ambiguous diagnostic source anchor")
        if model(plan)["issues"] != [rule]:
            raise ValueError("bounded negative model has competing constraints: " + variant)
        predicate = dict(file=anchor_file, line=points[0],
                         contains_any=diagnostic_routes()[(rule, variant)], excludes_any=EXCLUDED)
        name = self.fixture(rule, variant, [facet], inputs, plan, premises, predicate)
        self.repairs[name] = dict(control=control, file=edit_file, wrong=wrong, repaired=repaired,
                                  anchor_file=anchor_file, line=points[0], cause=facet, premises=premises)
        return name


def grammar_cases(c):
    defaults = [formal("k", "kind", 7), formal("n", "len", 3)]
    nonparameterized = scenario(listed=False)
    c.control("R754", "bare_nonparameterized", ["bare-nonparameterized-name"],
              declaration_source(nonparameterized), nonparameterized,
              "Previously defined ordinary nonparameterized record, without a parameter list.")
    bare = scenario(defaults, listed=False)
    bare_id = c.control("R754", "bare_defaulted", ["bare-defaulted-parameterized-name", "empty-parenthesized-list"],
                        declaration_source(bare), bare, "Both genuine PDT formals have scalar INTEGER constant defaults.")
    positional = scenario(defaults, [entry(None, 5), entry(None, 11)])
    c.control("R754", "positional", ["explicit-positional-list"], declaration_source(positional), positional,
              "Abstract KIND5 and LEN11 are scalar integer values, not intrinsic representation selectors.")
    keywords = scenario(defaults, [entry("k", 5, parenthesized=True), entry("n", 11)])
    keywords_id = c.control("R754", "keywords", ["explicit-keyword-list", "missing-list-separator"],
                            declaration_source(keywords), keywords, "Known unique keywords and valid constant scalar values.")
    mixed = scenario(defaults, [entry(None, 5), entry("n", 11)])
    c.control("R754", "mixed", ["mixed-positional-keyword-list"], declaration_source(mixed), mixed,
              "A positional prefix is followed only by an unused formal keyword.")
    empty = scenario(defaults)
    c.negative("R754", "empty_list", "empty-parenthesized-list", declaration_source(empty), empty, bare_id,
               "record()", "record", "type(record()) :: value",
               premises="Parameterized and all-defaulted: neither C796 nor a missing-required C797 value is the defect.")
    separated = copy.deepcopy(keywords)
    separated["separator"] = " "
    c.negative("R754", "missing_separator", "missing-list-separator", declaration_source(separated),
               separated, keywords_id, "k=(5) n=11", "k=(5),n=11", "type(record(k=(5) n=11)) :: value",
               premises="The closed constant expression (5) prevents digit/name lexical merging; both complete keyword items "
                        "are known, unique and scalar INTEGER. Inserting their comma is the only selected repair.")
    single = scenario(defaults, [entry("n", 3)])
    single_id = c.control("R755", "keyword_repair", ELIGIBLE["R755"], declaration_source(single), single,
                          "One shared repair for three R755 syntax defects, not numbered-target reuse admission credit.")
    for variant, facet, item, wrong, repaired in [
        ("arrow", "keyword-equals-not-arrow", entry("n", 3, operator="=>"), "n=>3", "n=3"),
        ("empty_keyword", "nonempty-keyword", entry("", 3), "record(=3)", "record(n=3)"),
        ("empty_value", "nonempty-parameter-value", entry("n", None), "record(n=)", "record(n=3)"),
    ]:
        bad = scenario(defaults, [item])
        c.negative("R755", variant, facet, declaration_source(bad), bad, single_id, wrong, repaired,
                   f"type({specifier(bad)}) :: value",
                   premises="Actual derived-type parameter list; every other formal is defaulted. "
                            "Neither call arguments, constructor components nor intrinsic selectors are involved.")


def name_and_parameterization_cases(c):
    local = scenario(listed=False)
    before = "integer :: scalar_name\n"
    local_id = c.control("C795", "local_type_repair", ["local-derived-type", "ordinary-object-not-type-name"],
                         declaration_source(local, before), local, "An ordinary record definition exists before the declaration.")
    bad = scenario(listed=False, type_name="scalar_name", symbol_kind="object")
    c.negative("C795", "ordinary_object", "ordinary-object-not-type-name", declaration_source(bad, before),
               bad, local_id, "type(scalar_name)", "type(record)", "type(scalar_name) :: value",
               premises="scalar_name is an INTEGER object, not an intrinsic/enum/enumeration type alternative. "
                        "Only the type selector changes; the object declaration remains legal.")
    provider = ("module specifier_provider\nimplicit none\ntype, public :: hidden\n"
                "integer :: payload\nend type hidden\nend module specifier_provider\n")
    client = "module specifier_client\nuse specifier_provider\nimplicit none\ntype(hidden) :: value\nend module specifier_client\n"
    public = scenario(listed=False, type_name="hidden")
    public_id = c.control("C795", "public_provider_repair", ["use-associated-type", "inaccessible-provider-type"],
                          {"provider.f90": provider, "client.f90": client}, public,
                          "Provider first, unchanged client second. The exported name denotes the same derived definition.")
    private = scenario(listed=False, type_name="hidden", accessible=False)
    c.negative("C795", "private_type", "inaccessible-provider-type",
               {"provider.f90": provider.replace("public", "private"), "client.f90": client}, private, public_id,
               "type, private :: hidden", "type, public :: hidden", "type(hidden) :: value",
               edit_file="provider.f90", anchor_file="client.f90",
               premises="The provider must compile. Client USE has no ONLY/private-name import. "
                        "Only provider type-name PRIVATE->PUBLIC repairs the client TYPE(hidden) failure.")
    control = c.control("C796", "nonparameterized_repair", ["nonparameterized-list-exclusion"],
                        declaration_source(local), local,
                        "Own diagnostic repair only; the separate bare-name numbered-reuse facet remains pending.")
    extra = scenario(entries=[entry(None, 3)])
    c.negative("C796", "nonparameterized_list", "nonparameterized-list-exclusion",
               declaration_source(extra), extra, control, "record(3)", "record", "type(record(3)) :: value",
               premises="A true non-PDT gets one positional integer; no unknown keyword creates a secondary C799 cause.")


def correspondence_cases(c):
    required = [formal("k", "kind"), formal("n", "len"), formal("pad", "len", 5)]
    all_values = scenario(required, [entry("k", 7), entry("n", 3)])
    control = c.control("C797", "required_keywords_repair",
                        ["required-values-supplied", "missing-required-kind", "missing-required-length", "duplicate-keyword"],
                        declaration_source(all_values), all_values,
                        "Required KIND k and LEN n are supplied once. The third formal pad has a valid default.")
    for variant, facet, entries, wrong, fixed in [
        ("missing_kind", "missing-required-kind", [entry("n", 3)], "record(n=3)", "record(k=7,n=3)"),
        ("missing_length", "missing-required-length", [entry("k", 7)], "record(k=7)", "record(k=7,n=3)"),
        ("duplicate_keyword", "duplicate-keyword", [entry("k", 7), entry("n", 3), entry("n", 5)],
         ",n=5", ""),
    ]:
        bad = scenario(required, entries)
        c.negative("C797", variant, facet, declaration_source(bad), bad, control, wrong, fixed,
                   f"type({specifier(bad)}) :: value",
                   premises="Other required formals use valid keywords. Defaults are not occurrences; "
                            "three explicit items do not exceed the three-formal count in the duplicate case.")
    mixed = scenario(required, [entry(None, 7), entry("n", 3)])
    mixed_id = c.control("C797", "required_mixed_repair",
                         ["required-values-supplied", "positional-keyword-duplicate"],
                         declaration_source(mixed), mixed, "The first formal is supplied positionally, then n by keyword.")
    duplicate = scenario(required, [entry(None, 7), entry("n", 3), entry("k", 5)])
    c.negative("C797", "positional_keyword_duplicate", "positional-keyword-duplicate",
               declaration_source(duplicate), duplicate, mixed_id, ",k=5", "",
               "type(record(7,n=3,k=5)) :: value",
               premises="All keywords are real; a legal positional prefix avoids C798, and three items fit three formals. "
                        "The only repeated correspondence is k.")
    for variant, names, good_entries, bad_entries, wrong, fixed in [
        ("keyword_then_positional", "abc", [entry("c", 31), entry("a", 11)],
         [entry("c", 31), entry(None, 11)], "c=31,11", "c=31,a=11"),
        ("positional_keyword_positional", "abcd", [entry(None, 11), entry("d", 44), entry("b", 22)],
         [entry(None, 11), entry("d", 44), entry(None, 22)], "d=44,22", "d=44,b=22"),
    ]:
        formals = [formal(name, "kind", i) for i, name in enumerate(names, 1)]
        good, bad = scenario(formals, good_entries), scenario(formals, bad_entries)
        facet = variant.replace("_", "-")
        good_id = c.control("C798", variant + "_repair", [facet], declaration_source(good), good,
                            "All abstract KIND formals have independent constant defaults; the repair uses an unused earlier keyword.")
        c.negative("C798", variant, facet, declaration_source(bad), bad, good_id, wrong, fixed,
                   f"type({specifier(bad)}) :: value",
                   premises="Three/four defaulted formals; the named later formal is distinct from the valid positional prefix. "
                            "No missing-required or obvious duplicate cause is introduced. Invalid ordering has no value mapping.")


def keyword_cases(c):
    defaults = [formal("k", "kind", 7), formal("n", "len", 3)]
    good = scenario(defaults, [entry("n", 3)])
    control = c.control("C799", "keyword_repair", ["unknown-keyword", "component-name-not-parameter"],
                        declaration_source(good), good, "All actual formals are defaulted; n is an unused real formal.")
    for variant, facet, keyword in [
        ("unknown_keyword", "unknown-keyword", "nn"),
        ("component_keyword", "component-name-not-parameter", "payload"),
    ]:
        bad = scenario(defaults, [entry(keyword, 3)])
        c.negative("C799", variant, facet, declaration_source(bad), bad, control,
                   keyword + "=3", "n=3", f"type({specifier(bad)}) :: value",
                   premises="Only the keyword's membership changes. payload is a real ordinary component, "
                            "not a formal parameter; this is a TYPE declaration, never a constructor component list.")


def assumed_length_cases(c):
    formals = [formal("k", "kind"), formal("n", "len")]
    beginning = "module specifier_definitions\nimplicit none\n" + definition(formals) + "contains\n"
    ending = "end module specifier_definitions\n"
    guard = scenario(formals, [entry("k", 7), entry("n", "*")], context="associate")
    guard_source = beginning + """subroutine select_record(item)
class(record(k=7,n=*)), intent(in) :: item
select type(view=>item)
type is(record(k=7,n=*))
continue
end select
end subroutine select_record
subroutine possible_caller()
type(record(k=7,n=5)) :: actual
actual%payload=0
call select_record(actual)
end subroutine possible_caller
""" + ending
    guard["selector"] = dict(polymorphic=True, optional=False, allocatable=False, pointer=False,
                             declared_type="record", guard_type="record", kinds={"k": 7},
                             assumed_lengths=["n"], extensible=True, guard_count=1)
    c.control("C7100", "associate_guard", ["associate-name-type-guard"], guard_source, guard,
              "A genuinely polymorphic ordinary nonoptional dummy is always present, not an unallocated selector. "
              "One ordinary extensible TYPE IS guard uses matching constant KIND7 and every LEN assumed; a defined fixed actual is possible.")
    allocated = scenario(formals, [entry("k", 7), entry("n", "*")], context="dummy-allocation")
    common = dict(type="record", polymorphic=False, rank=0, kinds={"k": 7}, deferred=[], allocatable=True)
    allocated["dummy"] = dict(common, lengths={"n": "*"})
    allocated["actual"] = dict(common, lengths={"n": 5})
    allocated["allocation"] = dict(values={"k": 7, "n": "*"}, objects=[dict(name="item", dummy=True, assumed=["n"])])
    assert not allocation_model(allocated["dummy"], allocated["actual"],
                                allocated["allocation"]["values"], allocated["allocation"]["objects"])
    allocation_source = beginning + """subroutine allocate_dummy(item)
type(record(k=7,n=*)), allocatable, intent(inout) :: item
integer :: status
if (.not.allocated(item)) then
allocate(record(k=7,n=*) :: item,stat=status)
if (status/=0) error stop 1
end if
item%payload=0
end subroutine allocate_dummy
subroutine possible_caller()
type(record(k=7,n=5)), allocatable :: actual
call allocate_dummy(actual)
end subroutine possible_caller
""" + ending
    c.control("C7100", "dummy_allocation", ["dummy-declaration", "dummy-allocation"], allocation_source, allocated,
              "Shared declaration/allocation admission: scalar TYPE dummy and actual are both allocatable/nonpolymorphic, "
              "KIND7, with identical empty deferred-parameter sets. Actual LEN5 is fixed, not deferred. "
              "C939 requires n=* for the one assumed-LEN dummy object. Allocation is guarded and STAT failure is explicit; "
              "there is no SOURCE/MOLD or inquiry of unallocated deferred LEN.")
    local = scenario(formals, [entry("k", 7), entry("n", 3)], context="local")
    local_body = beginning + "subroutine local_context()\ntype(record(k=7,n=3)) :: value\n" + (
        "value%payload=0\nend subroutine local_context\n") + ending
    control = c.control("C7100", "local_explicit_length_repair", ["ordinary-local-declaration-exclusion"],
                        local_body, local, "A local non-dummy variable has complete constant KIND/LEN values.")
    assumed = scenario(formals, [entry("k", 7), entry("n", "*")], context="local")
    c.negative("C7100", "local_assumed_length", "ordinary-local-declaration-exclusion",
               local_body.replace("record(k=7,n=3)", "record(k=7,n=*)"), assumed, control, "n=*", "n=3",
               "type(record(k=7,n=*)) :: value",
               premises="Only the LEN asterisk changes. The variable is neither dummy nor associate; no FUNCTION/RESULT, "
                        "PARAMETER/constructor or ALLOCATE/C939 negative is smuggled into C7100.")


def build_corpus(root=ROOT):
    corpus = Corpus(root)
    grammar_cases(corpus)
    name_and_parameterization_cases(corpus)
    correspondence_cases(corpus)
    keyword_cases(corpus)
    assumed_length_cases(corpus)
    if corpus.coverage() != {rule: set(facets) for rule, facets in ELIGIBLE.items()}:
        raise ValueError("coverage differs from the authorized 28 compile facets")
    if set(corpus.repairs) != {identifier(rule, variant, True) for rule, variant in diagnostic_routes()}:
        raise ValueError("diagnostic route/repair mismatch")
    return corpus.files, corpus.cases, corpus.repairs


def synced_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    for requirement in result["requirements"]:
        cases = [s for s in specs.values() if s["rule"] == requirement["id"]]
        covered = {facet for case in cases for facet in case["facets"]}
        if covered - set(requirement["facets"]):
            raise ValueError("unknown generated facet")
        for facet in covered:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - covered:
            raise ValueError("missing preserved pending plan for " + requirement["id"])
        if cases:
            bad = sum(case["kind"] == "invalid" for case in cases)
            original = requirement["oracle"].split("\n\nFinite compile implementation:", 1)[0]
            requirement["oracle"] = original + (
                f"\n\nFinite compile implementation: {len(cases)} compile-only cases represent {len(covered)} facets: "
                f"{bad} diagnostic inputs and {len(cases)-bad} positive controls/admissions. "
                "Each negative has a same-primary source-minimal conforming repair; a control may support several "
                "such contrasts and explicit admission facets. No runtime parameter-value effect or unsupported reuse "
                "graph is credited. Located role/property predicates are causal evidence guards, not mandatory wording, "
                "fatal-exit or printed-rule-code policies. Current source/case/evidence adjudications remain separate "
                "content-bound records, not inferred from generation or observations.")
    return result


CONDITIONS = """## Source and concrete qualification

Authority: J3/24-007, 18 December 2023, 688 physical PDF pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Only 7.5.9 on PDF106 is implemented, ending before the actual 7.5.10 heading.
Its 11 original units, 36 fine units, 47 accounting rows and 11 requirement IDs
are preserved. Independent source eligibility is not fixture approval.

Original R401/list notation (PDF44-45), R701/C701/C702 and R703 alternatives
(PDF76-77), R733 and parameter definition/order (PDF91-92), type-name privacy
(PDF89), C939/allocation rules (PDF160-162), inquiry limits (PDF153), SELECT TYPE
(PDF224-226), and actual/dummy agreement (PDF342-343) supply the concrete premises.
All parameter expressions used as values/defaults are scalar INTEGER constants;
KIND tags are abstract user parameters, never intrinsic representation selectors.

R754's empty group is on a genuinely parameterized all-defaulted record. Its
repair deletes only that group. The missing comma separates two complete known
keyword items, with `(5)` closed before the next keyword so digits cannot merge
lexically. R755 changes are in actual derived-type parameter lists, not calls,
constructors or intrinsic selectors. C795's object name is `scalar_name`, not a
legitimate TYPE(INTEGER/enum/enumeration) alternative. The PRIVATE-type provider
must compile; an unchanged client USE without ONLY fails at TYPE(hidden).
Only provider type-name PRIVATE-to-PUBLIC repairs that case.

C796 uses a positional value on a true non-PDT, without a spurious keyword.
C797 uses required k/n and a defaulted third formal pad: duplicate tests do not
even exceed the formal count. Missing values are repaired by inserting only
their keywords/values, never by changing defaults or shifting positional values.
C798 uses three/four all-defaulted abstract KIND formals, a later keyword, and
an unused earlier keyword in the repair. Invalid lists receive no runtime or
model value mapping. C799 defaults every real formal; `payload` is a genuine
ordinary component, but not a type-parameter keyword.

C7100's shared dummy declaration/allocation control has TYPE(record(k=7,n=*)),
ALLOCATABLE, INTENT(INOUT), with a scalar allocatable fixed-n=5 actual.
Both deferred-parameter sets are empty; neither n is deferred. C939 requires
the allocation's n=* exactly for the one assumed-LEN dummy object, with constant
KIND7 and no SOURCE/MOLD. The body allocates only when unallocated, checks STAT
with explicit failure, then defines payload; it never inquires about absent LEN.
The SELECT TYPE control uses a genuinely polymorphic nonoptional ordinary dummy,
not an unallocated selector. Its one ordinary extensible guard has matching KIND
and all LENs assumed, with a fully defined compatible fixed actual available.
These are compile admissions, not allocation, parameter-value or finalization
runtime observations. The sole C7100 negative is an ordinary local LEN asterisk,
repaired to a scalar integer; coupled function-result, named-constant and C939
negative contexts remain pending.

## Reporting and ownership limits

The eight numbered rules require reporting capability under 4.2, not fatal
rejection, rule codes or fixed wording. Contracts match located finite
type-specifier-role/property messages. Their prospective phrases are not
fabricated native observations. Generic parser recovery, wrong subjects or
properties, echoed source, unsupported facilities, Internal/verifier failures,
resource errors and timeouts never corroborate the intended cause. A native
message that does not establish the cause remains a failing observation.
Only an independently justified exact family-native warning allowance may
admit a nonfatal warning; no additional diagnostic policy is adopted.

Controls are shared within a primary rule when the exact repaired sources
coincide. A repair control for C796/R755/C799 is not a duplicate wrapper used
to clear that rule's separately pending canonical-reuse admission. No existing
R/C target, family or documentary graph is registered. All fifteen S-owned
facets, including runtime correspondence/conversion/default effects, remain
pending, as do the other conditional and canonical-use facets. No 7.5.8,
constructor or inherited-parameter program is added or repurposed.
"""


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def render_view(catalogue, specs, repairs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    facets = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    bad = len(repairs)
    result = (
        "# Fortran 2023: 7.5.9 Derived-type specifier - compile implementation\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Current case/evidence adjudications are separate content-bound records.\n\n"
        f"The packet has **{len(specs)} compile-only cases**: **{bad} diagnostic inputs** and "
        f"**{len(specs)-bad} positive controls/admissions**, with **zero runtime cases**. "
        f"**{facets-pending} of {facets} facets are represented; {pending} remain PENDING.** "
        "Representation is not compiler success, fixture approval or source closure.\n\n"
        + CONDITIONS + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.5.9 -->\n\n")
    result += "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    result += "<!-- END GENERATED 7.5.9 -->\n\n## Exact finite case and repair census\n\n"
    for name, spec in specs.items():
        result += f"### `{name}`\n\n**Primary:** {spec['rule']}; **phase/evidence:** compile / {spec['evidence']}.\n\n"
        result += "**Facets:** " + ", ".join("`" + facet + "`" for facet in spec["facets"]) + ".\n\n"
        result += spec["premises"] + "\n\n"
        if name in repairs:
            repair = repairs[name]
            result += f"**Minimal repair:** `{repair['control']}`; `{repair['file']}` changes "
            result += f"`{repair['wrong']}` to `{repair['repaired']}` once. "
            result += f"**Diagnostic anchor:** `{repair['anchor_file']}:{repair['line']}`.\n\n"
    result += "## Complete finite pending plans\n\n"
    result += "These maps are copied exactly from current canonical JSON; no declaration or observation supplies missing reuse evidence.\n\n"
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            result += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                result += f"* **`{facet}`** - {plan}\n"
            result += "\n"
    return result + (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_type_specifier_fixtures.py --check` verifies exact input bytes, "
        "source/phase metadata and both Markdown regions. Targeted regressions check all minimal repairs, "
        "shared controls, constraint interactions, invalid-order noninterpretation, C7100 complete contexts "
        "and located role/property/failure guards. The original case bindings remain unchanged.\n\n"
        "Independent source/fixture/cause review is recorded in `doc/source_audits/batch_020.json`. "
        "Twenty-three cases have qualifying GNU f2023 observations; eleven negatives retain source-only "
        "adjudication and explicit limits on conservative diagnostic noncredit. All seventeen controls "
        "compile with GNU. Observations preserve exact IDs/current fingerprints, complete commands, "
        "source roots/input hashes and actual reference modes. Twelve calibrated negative predicates "
        "have genuinely refreshed observations; archived rows are not relabelled. No compile admission "
        "becomes a runtime effect, and all31 pending facets remain open.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    outputs, specs, repairs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs, repairs)
    if args.check:
        bad = [str(path.relative_to(ROOT)) for path, raw in outputs.items()
               if not path.is_file() or path.read_bytes() != raw]
        actual = {p for p in (ROOT / "tests/fixtures").glob("type_specifier_*/*") if p.is_file()}
        bad += [str(path.relative_to(ROOT)) for path in actual - set(outputs)]
        if catalogue != updated:
            bad.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            bad.append(VIEW)
        if bad:
            raise SystemExit("stale type-specifier packet: " + ", ".join(sorted(bad)))
    else:
        for path, raw in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files for {len(specs)} "
          f"compile cases, {len(repairs)} repairs and 28 represented facets.")


if __name__ == "__main__":
    main()
