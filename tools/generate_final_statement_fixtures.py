#!/usr/bin/env python3
"""Generate compile-only FINAL statement declarations and diagnostic controls."""
import argparse
import copy
import json
from pathlib import Path
import sys
import textwrap

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "doc/catalogues/derived_types_7_5_6_1.json"
VIEW = "doc/fortran_2023_7_5_6_1.md"
PREFIX = "final_statement_"
EXCLUDED = [
    "unsupported", "not supported", "not yet supported", "not implemented",
    "not yet implemented", "unimplemented", "implementation limitation",
    "internal compiler error", "internal:", "ASR verify", "ASR verifier",
    "LLVM ERROR", "LCOMPILERS_ASSERT", "segmentation fault", "stack trace",
    "out of memory", "unexpected end of file", "unexpected eof", "missing end",
    "obsolescent", "obsolete feature",
]
ELIGIBLE = {
    "R753": ("with-double-colon", "without-double-colon", "multiple-final-names",
             "missing-name-list", "missing-list-separator"),
    "C791": ("module-scalar-control", "module-array-control", "separate-module-control",
             "assumed-rank-control", "elemental-control", "nonmodule-procedure",
             "zero-dummies", "two-dummies", "optional-dummy", "coarray-dummy",
             "pointer-dummy", "allocatable-dummy", "polymorphic-dummy",
             "different-derived-type", "first-length-not-assumed",
             "second-length-not-assumed", "intent-out-dummy", "value-dummy"),
    "C792": ("one-specification", "duplicate-in-one-list", "duplicate-across-statements",
             "case-equivalent-name"),
    "C793": ("different-ranks", "different-kind-values", "same-kind-rank-conflict",
             "full-kind-tuple", "elemental-scalar-rank-conflict"),
    "C794": ("sole-assumed-rank-final", "different-kind-assumed-rank-family",
             "assumed-rank-plus-scalar", "assumed-rank-plus-vector",
             "assumed-rank-plus-elemental"),
}


def text(value):
    return textwrap.dedent(value).strip("\n") + "\n"


def identifier(rule, variant, invalid=False):
    return rule + ("_invalid__" if invalid else "_valid__") + variant


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="final_statement", root=root)
        self.repairs = {}

    def fixture(self, name, rule, facets, inputs, diagnostic=None, coarray=False, relation=""):
        if name in self.cases:
            raise ValueError("duplicate execution: " + name)
        folder = "tests/fixtures/" + PREFIX + name.lower()
        steps = []
        for filename, body in inputs.items():
            self.put(folder + "/" + filename, text(body))
            step = Path(filename).stem
            steps.append(dict(id=step, source=filename, language="fortran", form="free",
                              output=step + ".o", depends_on=[item["id"] for item in steps]))
        expectation = dict(phase="compile", step=steps[-1]["id"],
                           outcome="diagnose" if diagnostic else "success")
        evidence = "effect" if diagnostic else "positive-control"
        manifest = dict(schema_version=1, id=name, rule=rule, facets=list(facets),
                        evidence=evidence, standard="f2023", files=list(inputs),
                        build=steps, expect=expectation)
        if diagnostic:
            expectation["diagnostic"] = diagnostic
        if coarray:
            manifest["requires"] = ["coarray"]
        path = folder + "/fixture.json"
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, facets=list(facets),
                                kind="invalid" if diagnostic else "valid",
                                phase="compile", evidence=evidence, standard="f2023",
                                coarray=coarray, profiles=[], images=1,
                                path=path, source_relation=relation)
        return name

    def compile(self, rule, variant, facets, body, coarray=False):
        inputs = body if isinstance(body, dict) else {rule + ".f90": body}
        return self.fixture(identifier(rule, variant), rule, facets, inputs, coarray=coarray)

    def pair(self, rule, variant, facets, body, wrong, repaired, anchor, messages,
             edit_file=None, anchor_file=None, end_anchor=None, relation="", coarray=False,
             exclusions=()):
        inputs = body if isinstance(body, dict) else {rule + ".f90": body}
        inputs = {name: text(content) for name, content in inputs.items()}
        edit_file = edit_file or rule + ".f90"
        anchor_file = anchor_file or edit_file
        original = inputs[edit_file]
        if original.count(wrong) != 1 or wrong == repaired:
            raise ValueError(f"{rule}/{variant}: repair must select one unique source span")
        lines = inputs[anchor_file].splitlines()
        points = [n for n, line in enumerate(lines, 1) if line.strip() == anchor]
        if len(points) != 1:
            raise ValueError(f"{rule}/{variant}: nonunique source anchor {anchor!r}")
        diagnostic = dict(file=anchor_file, line=points[0], contains_any=list(messages),
                          excludes_any=EXCLUDED + list(exclusions))
        if end_anchor:
            ends = [n for n, line in enumerate(lines, 1) if line.strip() == end_anchor]
            if len(ends) != 1 or ends[0] < points[0] or not relation:
                raise ValueError(f"{rule}/{variant}: unjustified source relation")
            diagnostic["end_line"] = ends[0]
        negative = self.fixture(identifier(rule, variant, True), rule, facets, inputs,
                                diagnostic, coarray, relation)
        control = dict(inputs)
        control[edit_file] = original.replace(wrong, repaired, 1)
        positive = self.fixture(identifier(rule, variant + "_repair"), rule, facets, control,
                                coarray=coarray, relation=relation)
        self.repairs[negative] = [dict(control=positive, file=edit_file, wrong=wrong,
                                       repaired=repaired, source_relation=relation)]
        return negative

    def extra_control(self, negative, variant, body, wrong, repaired):
        spec = self.cases[negative]
        filename = spec["rule"] + ".f90"
        original = text(body)
        if original.count(wrong) != 1:
            raise ValueError("nonunique additional control: " + negative)
        name = identifier(spec["rule"], variant)
        self.fixture(name, spec["rule"], spec["facets"],
                     {filename: original.replace(wrong, repaired, 1)},
                     coarray=spec["coarray"], relation=spec["source_relation"])
        self.repairs[negative].append(dict(control=name, file=filename, wrong=wrong,
                                           repaired=repaired, source_relation=spec["source_relation"]))


def final_procedure(name="finish", argument="self", selector="record", shape="",
                    attributes="intent(inout)", elemental=False):
    prefix = "impure elemental " if elemental else ""
    return (f"{prefix}subroutine {name}({argument})\n"
            f"type({selector}), {attributes} :: {argument}{shape}\n"
            f"end subroutine {name}\n")


def definition(finals, procedures="", parameters="", before="", interfaces=""):
    return ("module final_defs\nimplicit none\n" + before
            + "type :: record" + parameters + "\n"
            + ("integer, kind :: k\ninteger, len :: n\n" if parameters == "(k,n)" else
               "integer, kind :: k1,k2\ninteger, len :: n\n" if parameters == "(k1,k2,n)" else
               "integer, len :: n,m\n" if parameters == "(n,m)" else "")
            + "integer :: payload\ncontains\n" + finals + "\nend type record\n"
            + interfaces + ("contains\n" + procedures if procedures else "")
            + "end module final_defs\n")


def grammar(c):
    for variant, statement, facet in (
        ("with_double_colon", "final :: finish", "with-double-colon"),
        ("without_double_colon", "final finish", "without-double-colon"),
    ):
        c.compile("R753", variant, [facet], definition(statement, final_procedure()))
    pair_bodies = (final_procedure("finish_scalar", "scalar")
                   + final_procedure("finish_vector", "vector", shape="(:)"))
    c.compile("R753", "multiple_names", ["multiple-final-names"],
              definition("final :: finish_scalar, finish_vector", pair_bodies))
    for variant, statement, repaired in (
        ("missing_name_bare", "final", "final finish"),
        ("missing_name_colons", "final ::", "final :: finish"),
    ):
        c.pair("R753", variant, ["missing-name-list"], definition(statement, final_procedure()),
               statement + "\n", repaired + "\n", statement, [
                   "FINAL statement requires a nonempty final-subroutine-name list",
                   "Missing final subroutine name after FINAL",
               ])
    statement = "final :: finish_scalar finish_vector"
    c.pair("R753", "missing_list_separator", ["missing-list-separator"],
           definition(statement, pair_bodies),
           "finish_scalar finish_vector", "finish_scalar, finish_vector", statement, [
               "Missing comma between FINAL names 'finish_scalar' and 'finish_vector'",
               "FINAL subroutine names 'finish_scalar' and 'finish_vector' require a comma separator",
           ])


def dummy_constraints(c):
    for variant, shape, elemental, facet in (
        ("module_scalar", "", False, "module-scalar-control"),
        ("module_array", "(:)", False, "module-array-control"),
        ("assumed_rank", "(..)", False, "assumed-rank-control"),
        ("elemental", "", True, "elemental-control"),
    ):
        c.compile("C791", variant, [facet],
                  definition("final :: finish", final_procedure(shape=shape, elemental=elemental)))
    parent = definition("final :: finish", interfaces=(
        "interface\nmodule subroutine finish(self)\n"
        "type(record), intent(inout) :: self\nend subroutine finish\nend interface\n"))
    c.compile("C791", "separate_module", ["separate-module-control"], {
        "C791.f90": parent,
        "implementation.f90": (
            "submodule(final_defs) implementation\nimplicit none\ncontains\n"
            "module procedure finish\nend procedure finish\nend submodule implementation\n"),
    })
    external_interface = (
        "interface\nsubroutine finish_external(self)\nimport :: record\n"
        "type(record), intent(inout) :: self\nend subroutine finish_external\nend interface\n")
    external_definition = (
        "subroutine finish_external(self)\nuse final_defs, only: record\nimplicit none\n"
        "type(record), intent(inout) :: self\nend subroutine finish_external\n")
    body = (definition("final :: finish_external", final_procedure("finish_module"),
                       interfaces=external_interface) + external_definition)
    c.pair("C791", "nonmodule_procedure", ["nonmodule-procedure"], body,
           "final :: finish_external", "final :: finish_module", "final :: finish_external", [
               "Final subroutine 'finish_external' must be a module procedure",
               "External subroutine 'finish_external' cannot be a FINAL procedure",
           ], relation="Both complete interfaces and definitions use this same prior record type; only the FINAL target changes.",
           exclusions=["cannot open module", "module file", "not found in module"])
    zero = "subroutine finish()\nend subroutine finish\n"
    c.pair("C791", "zero_dummies", ["zero-dummies"], definition("final :: finish", zero),
           "subroutine finish()\n", "subroutine finish(self)\ntype(record), intent(inout) :: self\n",
           "final :: finish", [
               "Final subroutine 'finish' must have exactly one dummy argument",
               "Final subroutine 'finish' has no dummy argument",
           ], end_anchor="subroutine finish()",
           relation="The FINAL declaration refers to the zero-dummy procedure; the repair adds both signature and declaration, not a local finalizable record.")
    two = ("subroutine finish(self, spare)\ntype(record), intent(inout) :: self\n"
           "integer :: spare\nend subroutine finish\n")
    c.pair("C791", "two_dummies", ["two-dummies"], definition("final :: finish", two),
           "finish(self, spare)", "finish(self)", "final :: finish", [
               "Final subroutine 'finish' must have exactly one dummy argument",
               "Final subroutine 'finish' has more than one dummy argument",
           ], end_anchor="subroutine finish(self, spare)",
           relation="The FINAL declaration and two-dummy signature form the reporting relation. Removing spare leaves its plain INTEGER declaration legal as a local.")
    variants = [
        ("optional_dummy", "optional-dummy", "type(record), optional, intent(inout) :: self",
         "type(record), intent(inout) :: self", "OPTIONAL"),
        ("coarray_dummy", "coarray-dummy", "type(record), intent(inout) :: self[*]",
         "type(record), intent(inout) :: self", "a coarray"),
        ("pointer_dummy", "pointer-dummy", "type(record), pointer, intent(inout) :: self",
         "type(record), intent(inout) :: self", "POINTER"),
        ("allocatable_dummy", "allocatable-dummy", "type(record), allocatable, intent(inout) :: self",
         "type(record), intent(inout) :: self", "ALLOCATABLE"),
        ("polymorphic_dummy", "polymorphic-dummy", "class(record), intent(inout) :: self",
         "type(record), intent(inout) :: self", "polymorphic"),
        ("different_derived_type", "different-derived-type", "type(other), intent(inout) :: self",
         "type(record), intent(inout) :: self", "of type 'other' instead of 'record'"),
        ("intent_out_dummy", "intent-out-dummy", "type(record), intent(out) :: self",
         "type(record), intent(inout) :: self", "INTENT(OUT)"),
        ("value_dummy", "value-dummy", "type(record), value, intent(in) :: self",
         "type(record), intent(in) :: self", "VALUE"),
    ]
    for variant, facet, bad, good, property_name in variants:
        before = "type :: other\ninteger :: payload\nend type other\n" if variant == "different_derived_type" else ""
        procedure = f"subroutine finish(self)\n{bad}\nend subroutine finish\n"
        c.pair("C791", variant, [facet], definition("final :: finish", procedure, before=before),
               bad, good, "final :: finish", [
                   f"Dummy argument 'self' of final subroutine 'finish' must not be {property_name}",
                   f"Final subroutine 'finish' has forbidden {property_name} dummy 'self'",
               ], end_anchor=bad, coarray=variant == "coarray_dummy",
               relation=f"The FINAL target and its sole dummy self establish the {facet} condition; only that dummy property changes.")
    for parameter, selector, facet in (
        ("n", "record(2,*)", "first-length-not-assumed"),
        ("m", "record(*,3)", "second-length-not-assumed"),
    ):
        bad = f"type({selector}), intent(inout) :: self"
        good = "type(record(*,*)), intent(inout) :: self"
        procedure = f"subroutine finish(self)\n{bad}\nend subroutine finish\n"
        c.pair("C791", "length_" + parameter, [facet],
               definition("final :: finish", procedure, parameters="(n,m)"),
               bad, good, "final :: finish", [
                   f"Length parameter '{parameter}' of final dummy 'self' in 'finish' must be assumed",
                   f"Final subroutine 'finish' dummy 'self' has non-assumed length parameter '{parameter}'",
               ], end_anchor=bad,
               relation=f"Only {parameter} is explicit; the other LEN parameter is already assumed. Declared type is record in both sources.")


def duplicate_names(c):
    c.compile("C792", "one_specification", ["one-specification"],
              definition("final :: finish", final_procedure()))
    for variant, names in (("duplicate_list", "finish, finish"),
                           ("case_equivalent", "finish, FiNiSh")):
        statement = "final :: " + names
        c.pair("C792", variant,
               ["case-equivalent-name" if variant == "case_equivalent" else "duplicate-in-one-list"],
               definition(statement, final_procedure()), statement, "final :: finish", statement, [
                   "Final subroutine 'finish' is already specified for type 'record'",
                   "Duplicate specification of FINAL procedure 'finish'",
               ])
    statements = "final :: finish\nfinal :: finish ! repeated occurrence"
    c.pair("C792", "duplicate_statements", ["duplicate-across-statements"],
           definition(statements, final_procedure()),
           "final :: finish ! repeated occurrence\n", "",
           "final :: finish ! repeated occurrence", [
               "Final subroutine 'finish' is already specified for type 'record'",
               "Duplicate specification of FINAL procedure 'finish'",
           ], relation="Remove the entire redundant FINAL statement, preserving the first complete one.")


def signature_uniqueness(c):
    ranks = final_procedure("finish_scalar", "scalar") + final_procedure("finish_vector", "vector", shape="(:)")
    c.compile("C793", "different_ranks", ["different-ranks"],
              definition("final :: finish_scalar\nfinal :: finish_vector", ranks))
    kinds = (final_procedure("finish_first", "first", "record(1,*)")
             + final_procedure("finish_second", "second", "record(2,*)"))
    c.compile("C793", "different_kind_values", ["different-kind-values"],
              definition("final :: finish_first, finish_second", kinds, parameters="(k,n)"))
    procedures = final_procedure("finish_first", "first") + final_procedure("finish_second", "second")
    c.pair("C793", "same_kind_rank", ["same-kind-rank-conflict"],
           definition("final :: finish_first, finish_second", procedures),
           "type(record), intent(inout) :: second", "type(record), intent(inout) :: second(:)",
           "final :: finish_first, finish_second", [
               "Final subroutines 'finish_first' and 'finish_second' have the same KIND parameters and rank",
               "FINAL procedures 'finish_first' and 'finish_second' have indistinguishable kind-and-rank signatures",
           ], end_anchor="type(record), intent(inout) :: second",
           relation="Two distinct module procedures have the same scalar signature; only second's rank changes.")
    tuple_procedures = (final_procedure("finish_first", "first", "record(1,2,*)")
                        + final_procedure("finish_second", "second", "record(1,2,*)"))
    tuple_body = definition("final :: finish_first, finish_second", tuple_procedures, parameters="(k1,k2,n)")
    wrong = "type(record(1,2,*)), intent(inout) :: second"
    negative = c.pair("C793", "full_kind_tuple", ["full-kind-tuple"], tuple_body,
                      wrong, "type(record(1,3,*)), intent(inout) :: second",
                      "final :: finish_first, finish_second", [
                          "Final subroutines 'finish_first' and 'finish_second' have the same KIND parameters and rank",
                          "FINAL procedures 'finish_first' and 'finish_second' have identical kind tuples and scalar rank",
                      ], end_anchor=wrong,
                      relation="The abstract KIND tuple is (1,2) on both scalar dummies. LEN n stays assumed; one KIND coordinate alone changes.")
    c.extra_control(negative, "full_kind_tuple_first_repair", tuple_body,
                    wrong, "type(record(2,2,*)), intent(inout) :: second")
    ordinary = final_procedure("finish_ordinary", "ordinary")
    elemental = final_procedure("finish_elemental", "element", elemental=True)
    body = definition("final :: finish_ordinary, finish_elemental", ordinary + elemental)
    c.pair("C793", "elemental_scalar_conflict", ["elemental-scalar-rank-conflict"], body,
           "type(record), intent(inout) :: ordinary",
           "type(record), intent(inout) :: ordinary(:)",
           "final :: finish_ordinary, finish_elemental", [
               "Final subroutines 'finish_ordinary' and 'finish_elemental' have the same KIND parameters and rank",
               "Scalar elemental final 'finish_elemental' conflicts with scalar final 'finish_ordinary'",
           ], end_anchor="type(record), intent(inout) :: element",
           relation="The ordinary and IMPURE ELEMENTAL dummies are both scalar; only the ordinary dummy becomes rank one.")


def assumed_rank_exclusivity(c):
    c.compile("C794", "sole_assumed_rank", ["sole-assumed-rank-final"],
              definition("final :: finish_any", final_procedure("finish_any", "any_rank", shape="(..)")))
    family = (final_procedure("finish_any", "any_rank", "record(1,*)", shape="(..)")
              + final_procedure("finish_fixed", "fixed", "record(2,*)"))
    c.compile("C794", "different_kind_family", ["different-kind-assumed-rank-family"],
              definition("final :: finish_any, finish_fixed", family, parameters="(k,n)"))
    for variant, shape, elemental, facet in (
        ("plus_scalar", "", False, "assumed-rank-plus-scalar"),
        ("plus_vector", "(:)", False, "assumed-rank-plus-vector"),
        ("plus_elemental", "", True, "assumed-rank-plus-elemental"),
    ):
        bodies = (final_procedure("finish_any", "any_rank", shape="(..)")
                  + final_procedure("finish_fixed", "fixed", shape=shape, elemental=elemental))
        body = definition("final :: finish_any\nfinal :: finish_fixed", bodies)
        c.pair("C794", variant, [facet], body,
               "final :: finish_fixed\n", "", "final :: finish_any", [
                   "Assumed-rank final 'finish_any' cannot coexist with same-KIND final 'finish_fixed'",
                   "Final subroutines 'finish_any' and 'finish_fixed' share KIND parameters with an assumed-rank dummy",
               ], end_anchor=f"type(record), intent(inout) :: fixed{shape}",
               relation="Remove the complete competing FINAL statement; both procedure definitions remain otherwise valid and no callback is invoked.")


def qualified_diagnostic_routes(corpus):
    routes = {
        "R753_invalid__missing_name_colons": ["Empty FINAL at (1)"],
        "C791_invalid__zero_dummies": [
            "FINAL procedure at (1) must have exactly one argument",
            "FINAL subroutine 'finish' of derived type 'record' must have a single dummy argument",
        ],
        "C791_invalid__two_dummies": [
            "FINAL procedure at (1) must have exactly one argument",
            "FINAL subroutine 'finish' of derived type 'record' must have a single dummy argument",
        ],
        "C791_invalid__optional_dummy": [
            "Argument of FINAL procedure at (1) must not be OPTIONAL",
            "FINAL subroutine 'finish' of derived type 'record' must not have an OPTIONAL dummy argument",
        ],
        "C791_invalid__coarray_dummy": [
            "FINAL subroutine 'finish' of derived type 'record' must not have a coarray dummy argument",
        ],
        "C791_invalid__pointer_dummy": [
            "Argument of FINAL procedure at (1) must not be a POINTER",
            "FINAL subroutine 'finish' of derived type 'record' must not have a POINTER dummy argument",
        ],
        "C791_invalid__allocatable_dummy": [
            "Argument of FINAL procedure at (1) must not be ALLOCATABLE",
            "FINAL subroutine 'finish' of derived type 'record' must not have an ALLOCATABLE dummy argument",
        ],
        "C791_invalid__polymorphic_dummy": [
            "FINAL subroutine 'finish' of derived type 'record' must not have a polymorphic dummy argument",
        ],
        "C791_invalid__different_derived_type": [
            "Argument of FINAL procedure at (1) must be of type 'record'",
            "FINAL subroutine 'finish' of derived type 'record' must have a TYPE(record) dummy argument",
        ],
        "C791_invalid__intent_out_dummy": [
            "Argument of FINAL procedure at (1) must not be INTENT(OUT)",
            "FINAL subroutine 'finish' of derived type 'record' must not have a dummy argument with INTENT(OUT)",
        ],
        "C791_invalid__value_dummy": [
            "FINAL subroutine 'finish' of derived type 'record' must not have a dummy argument with the VALUE attribute",
        ],
        "C791_invalid__length_n": [
            "FINAL subroutine 'finish' of derived type 'record' must have a dummy argument with an assumed LEN type parameter 'n=*'",
        ],
        "C791_invalid__length_m": [
            "FINAL subroutine 'finish' of derived type 'record' must have a dummy argument with an assumed LEN type parameter 'm=*'",
        ],
    }
    for variant in ("duplicate_list", "duplicate_statements", "case_equivalent"):
        routes["C792_invalid__" + variant] = [
            "'finish' at (1) is already defined as FINAL procedure",
            "FINAL subroutine 'finish' already appeared in this derived type",
        ]
    for variant in ("same_kind_rank", "full_kind_tuple"):
        routes["C793_invalid__" + variant] = [
            "FINAL subroutines 'finish_second' and 'finish_first' of derived type 'record' cannot be distinguished by rank or KIND type parameter value",
        ]
    routes["C793_invalid__same_kind_rank"].append(
        "FINAL procedure 'finish_second' declared at (1) has the same rank (0) as 'finish_first'")
    routes["C793_invalid__elemental_scalar_conflict"] = [
        "FINAL subroutines 'finish_ordinary' and 'finish_elemental' of derived type 'record' cannot be distinguished by rank or KIND type parameter value",
        "FINAL procedure 'finish_elemental' declared at (1) has the same rank (0) as 'finish_ordinary'",
    ]
    for variant in ("plus_scalar", "plus_vector", "plus_elemental"):
        routes["C794_invalid__" + variant] = [
            "FINAL procedure at (1) with assumed rank argument must be the only finalizer with the same kind/type",
        ]
    for name, messages in routes.items():
        path = corpus.root / corpus.cases[name]["path"]
        manifest = json.loads(corpus.files[path])
        diagnostic = manifest["expect"]["diagnostic"]
        diagnostic["contains_any"] = list(dict.fromkeys(diagnostic["contains_any"] + messages))
        corpus.files[path] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")


def build_corpus(root=ROOT):
    corpus = Corpus(root)
    grammar(corpus)
    dummy_constraints(corpus)
    duplicate_names(corpus)
    signature_uniqueness(corpus)
    assumed_rank_exclusivity(corpus)
    qualified_diagnostic_routes(corpus)
    return corpus.files, corpus.cases, corpus.repairs


ORACLES = {
    "R753": "Compile admissions distinguish the two FINAL separator spellings and a comma-separated scalar/rank-one family. Two missing-name forms are repaired by inserting finish, and a missing comma is inserted between otherwise legal distinct finals. Every target has a complete conforming module definition. Declaration acceptance is not callback execution.",
    "C791": "Five compile admissions exercise scalar, assumed-shape, separate module, assumed-rank and IMPURE ELEMENTAL finals. Thirteen source-minimal pairs isolate external-versus-module selection, dummy count, each prohibited attribute/category and each of two nonassumed LEN values. The external pair changes only its FINAL name, retains explicit interface/IMPORT and complete same-type definitions, and does not rely on a prior missing module. The zero-dummy repair adds signature and declaration together; the removed second dummy remains a legal plain INTEGER local. Coarray syntax is explicit with no dummy SAVE; VALUE uses INTENT(IN). No finalizer body executes.",
    "C792": "One compile admission and three duplicate-name pairs use the same actual module final identity, including case-equivalent spelling. List repairs remove one occurrence. The repeated-statement repair removes the whole redundant FINAL statement rather than leaving a bare FINAL. Distinct source scopes are not merged by textual basename.",
    "C793": "Compile-only rank and abstract-KIND families are independently legal. Equal scalar signatures are repaired by changing only the second rank. The two-KIND tuple case has independent one-coordinate repairs, with LEN remaining assumed and no intrinsic representation selector. The ordinary/IMPURE ELEMENTAL scalar conflict is repaired by making only the ordinary dummy an array. No payload, dispatch or callback count is observed.",
    "C794": "A sole assumed-rank final and a different-KIND assumed-rank/fixed-rank family have compile admissions. Three same-KIND conflicts pair assumed rank with scalar, vector or legal IMPURE ELEMENTAL scalar finals. Each repair removes the whole competing FINAL statement while preserving both valid procedure bodies. Rank distinction is not used to evade same-KIND exclusivity; no runtime precedence or assumed-rank payload query is inferred.",
}


def synced_catalogue(catalogue, specs):
    updated = copy.deepcopy(catalogue)
    for requirement in updated["requirements"]:
        rule = requirement["id"]
        represented = {facet for spec in specs.values() if spec["rule"] == rule for facet in spec["facets"]}
        if represented != set(ELIGIBLE.get(rule, ())):
            raise ValueError("unexpected direct facet partition for " + rule)
        for facet in represented:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - represented:
            raise ValueError("missing pending source plan for " + rule)
        if rule in ORACLES:
            requirement["oracle"] = ORACLES[rule]
    return updated


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues["7.5.6.1"] = catalogue
    return registry.catalogue_review_state("7.5.6.1")


def pending_appendix(catalogue):
    out = ["## Complete finite pending plans\n",
           "These are the complete current JSON `pending` maps. No empty program, inferred "
           "callback absence or invented inquiry supplies this evidence.\n"]
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            out.append(f"### Pending {requirement['id']}\n")
            for facet, plan in requirement["pending"].items():
                out.append(f"* **`{facet}`**: {plan}")
            out.append("")
    return "\n".join(out) + "\n"


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    negatives = sum(spec["kind"] == "invalid" for spec in specs.values())
    pending = sum(len(req["pending"]) for req in catalogue["requirements"])
    declared = sum(len(req["facets"]) for req in catalogue["requirements"])
    out = (
        "# Fortran 2023: 7.5.6.1 FINAL statement - declaration fixtures\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Case approvals and processor observations are separate content-bound records.\n\n"
        f"The bounded packet has **{len(specs)} compile-only cases**: **{negatives} diagnostic "
        f"inputs** and **{len(specs)-negatives} positive controls/admissions**. "
        f"Of **{declared} facets**, **{declared-pending} are directly represented** and "
        f"**{pending} remain PENDING**. Representation is not approval or compiler success.\n\n"
        "## Source and scope\n\n"
        "Independent source, fixture and finite signature-model decisions are recorded "
        "in `doc/source_audits/batch_015.json`. The source eligibility gate and all "
        "current case adjudications remain separate from code generation.\n\n"
        "Authority: checksum-pinned J3/24-007, 18 December 2023, original PDF 102. "
        "The corrected elemental dependencies are 15.9.1/15.9.3, PDF 362-363, not Simple "
        "procedures in 15.8. Final dummies use TYPE(record), not a C765 CLASS passed object. "
        "All otherwise eligible dummies have one ordinary nonabstract defining type and all "
        "LEN parameters assumed. Small KIND tuples are abstract parameters, not processor kind IDs.\n\n"
        "Every body is empty; no program is linked or run. Coarray metadata qualifies only "
        "declaration compilation, not an image configuration. No classification, finalization "
        "timing, callback execution or termination evidence is claimed. Sections 7.5.6.2-.4 "
        "and their source catalogues are outside this implementation.\n\n"
        "## Diagnostic/control contract\n\n"
        "Each negative has a complete context and an exact one-span source repair. Reports need "
        "a real source point or bounded relation and the actual final procedure, dummy or signature "
        "cause. Unsupported facilities, wrong subjects, generic recovery, source echoes, internal "
        "errors, verifier failures, crashes, resource failures and timeouts are not that cause. "
        "Ordinary status zero can still report a violation; neither a fatal exit nor a printed "
        "standard code is mandated. Native nonfatal permissions, if any, must be exact and "
        "family-specific. Current unqualified messages remain unqualified rather than weakening "
        "the source or oracle to force agreement.\n\n"
        "## Definitions\n\n<!-- BEGIN GENERATED 7.5.6.1 -->"
    )
    out += "\n\n" + "\n".join(render_requirement(req) for req in catalogue["requirements"]) + "\n"
    out += "<!-- END GENERATED 7.5.6.1 -->\n\n"
    out += "## Finite declaration census\n\n| Owner | Cases | Diagnostic | Compile admission/control |\n"
    out += "| --- | ---: | ---: | ---: |\n"
    for rule in ELIGIBLE:
        rows = [spec for spec in specs.values() if spec["rule"] == rule]
        bad = sum(spec["kind"] == "invalid" for spec in rows)
        out += f"| {rule} | {len(rows)} | {bad} | {len(rows)-bad} |\n"
    out += "\n" + pending_appendix(catalogue)
    out += ("\n## Reproduction and review boundary\n\n"
            "`python3 -B tools/generate_final_statement_fixtures.py --check` validates exact "
            "generated bytes and this view, including the complete pending appendix. "
            "`tests/test_final_statement_fixtures.py` checks the exact ID/phase/facet census, "
            "minimal repairs, independent source premises and diagnostic safety matrix. "
            "The local catalogue-index overlay is excluded from the author commit. "
            "Current-fingerprint compiler reports and any source-only candidates require "
            "independent adjudication; generation never approves cases or updates baselines.\n")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, specs, _ = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs)
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {path for path in (ROOT / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()}
        stale.extend(str(path.relative_to(ROOT)) for path in actual - set(files))
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            parser.exit(1, "Stale FINAL statement packet: " + ", ".join(sorted(stale)) + "\n")
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(specs)} compile-only cases.")


if __name__ == "__main__":
    main()
