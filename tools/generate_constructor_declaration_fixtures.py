#!/usr/bin/env python3
"""Bounded compile-only structure-constructor declarations and diagnostic controls."""
import argparse
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus
from generate_type_bound_fixtures import EXCLUDED as BINDING_EXCLUSIONS, text
from generate_data_component_fixtures import EXCLUDED_CAUSES, source_name

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.10"
CATALOGUE = "doc/catalogues/derived_types_7_5_10.json"
VIEW = "doc/fortran_2023_7_5_10.md"
PREFIX = "constructor_declaration_"
EXCLUDED = list(dict.fromkeys(BINDING_EXCLUSIONS + EXCLUDED_CAUSES + [
    "module failed verification", "asr_to_llvm", "compiler limitation",
]))
ELIGIBLE = {
    "R756": ["empty-component-list"],
    "C7101": ["abstract-constructor", "concrete-constructor-admission"],
    "C7102": ["repeated-keyword", "positional-keyword-repeat", "different-components-admission"],
    "C7103": ["parent-and-inherited-member", "disjoint-ancestor-and-child"],
    "C7104": ["missing-ordinary-component", "missing-pointer-component"],
    "C7105": ["positional-after-keyword", "positional-prefix-admission"],
    "C7106": ["unknown-component-keyword", "parameter-is-not-component"],
    "C7109": ["procedure-target-in-data-slot", "data-target-in-procedure-slot"],
    "C7110": ["array-target-to-scalar-pointer", "scalar-target-to-array-pointer", "same-rank-and-null-context"],
    "S7.5.10-006": ["prior-definition-admission"],
}
EXISTING = {"C7107": {"private-component-default", "private-component-explicit"}}
LEGACY_IDS = [
    "C7107_invalid__initialization_default_private",
    "C7107_invalid__initialization_explicit_private",
    "C7107_valid__initialization_default_private_repair",
    "C7107_valid__initialization_explicit_private_repair",
]


def identifier(rule, variant, invalid=False):
    return rule.replace(".", "_").replace("-", "_") + (
        "_invalid__constructor_decl_" if invalid else "_valid__constructor_decl_") + variant


def quote_variants(messages):
    result = []
    for message in messages:
        pieces = message.split("'")
        curly = "".join(piece + ("\u2018" if i % 2 == 0 else "\u2019")
                        for i, piece in enumerate(pieces[:-1])) + pieces[-1]
        result.extend([message, message.replace("'", '"'), curly])
    return list(dict.fromkeys(result))


def diagnostic_routes():
    duplicate = [
        "Component 'left' is initialized twice in the structure constructor",
        "Component 'left' is already initialized in this structure constructor",
        "Duplicate component specification for 'left' in constructor 'pair'",
        "Component 'left' conflicts with another component earlier in this structure constructor",
    ]
    return {
        ("C7101", "abstract"): [
            "Cannot construct ABSTRACT type 'base'",
            "Abstract type 'base' cannot be used in a structure constructor",
            "Cannot use abstract type 'base' in a structure constructor",
            "ABSTRACT derived type 'base' may not be used in a structure constructor",
        ],
        ("C7102", "repeated_keyword"): duplicate + [
            "Keyword 'left' at (1) has already appeared in the current argument list",
        ],
        ("C7102", "positional_repeat"): duplicate,
        ("C7103", "ancestor_overlap"): [
            "Component 'x' is already initialized by parent component 'parent'",
            "Component 'x' conflicts with parent component 'parent'",
            "Cannot specify component 'x' when ancestor component 'parent' is specified",
            "component 'x' at (1) has already been set by a parent derived type constructor",
            "Component 'x' conflicts with another component earlier in this structure constructor",
        ],
        ("C7104", "missing_ordinary"): [
            "No initializer for component 'right' given in the structure constructor",
            "Missing value for required component 'right' in constructor 'pair'",
            "Structure constructor lacks a value for component 'right'",
        ],
        ("C7104", "missing_pointer"): [
            "No initializer for component 'p' given in the structure constructor",
            "Missing value for required component 'p' in constructor 'holder'",
        ],
        ("C7105", "keyword_order"): [
            "A positional component follows a keyword component in structure constructor 'pair'",
            "Positional component after keyword in structure constructor 'pair'",
            "All component specifications after keyword 'left' must have keywords in a structure constructor",
            "Value in structure constructor lacks a component name",
        ],
        ("C7106", "unknown_keyword"): [
            "Component 'extra' is not a member of derived type 'packet'",
            "'extra' is not a component of derived type 'packet'",
            "Unknown component keyword 'extra' in constructor 'packet'",
            "'extra' at (1) is not a member of the 'packet' structure",
            "Keyword 'extra=' does not name a component of derived type 'packet'",
        ],
        ("C7106", "parameter_keyword"): [
            "'k' is not a component of derived type 'packet'",
            "Type parameter 'k' cannot be specified as a component keyword",
            "Unknown component keyword 'k' in constructor 'packet'",
            "Type parameter 'k' may not appear as a component of a structure constructor",
        ],
        ("C7109", "procedure_in_data"): [
            "Procedure target 'worker' cannot initialize data pointer component 'p'",
            "Data pointer component 'p' cannot be initialized with procedure 'worker'",
            "The element in the structure constructor at (1), for pointer component 'p', is PROCEDURE but should be INTEGER",
            "In assignment to object pointer 'p', the target 'worker' is a procedure designator",
        ],
        ("C7109", "data_in_procedure"): [
            "Data target 'datum' cannot initialize procedure pointer component 'action'",
            "Procedure pointer component 'action' requires a procedure target, not data object 'datum'",
            "In assignment to procedure pointer 'action', the target is not a procedure or procedure pointer",
        ],
        ("C7110", "array_to_scalar"): [
            "Data target 'vec' has rank 1 but pointer component 'one' has rank 0.",
            "Rank of value in structure constructor is 1 but component 'one' has rank 0.",
            "The rank of the element in the structure constructor at (1) does not match that of the component (1/0)",
        ],
        ("C7110", "scalar_to_array"): [
            "Data target 'scalar_target' has rank 0 but pointer component 'many' has rank 1.",
            "Rank of value in structure constructor is 0 but component 'many' has rank 1.",
            "The rank of the element in the structure constructor at (1) does not match that of the component (0/1)",
        ],
    }


def complete(definitions, declarations, body, procedures="", interfaces=""):
    result = "module constructor_types\nimplicit none\n"
    if interfaces:
        result += text(interfaces)
    result += text(definitions)
    if procedures:
        result += "contains\n" + text(procedures)
    return (result + "end module constructor_types\nprogram constructor_case\n"
            "use constructor_types\nimplicit none\n" + text(declarations)
            + text(body) + "end program constructor_case\n")


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="constructor_declaration", root=root)
        self.repairs = {}

    def compile(self, rule, variant, facets, source, diagnostic=None, premise="", constructor=""):
        name = identifier(rule, variant, diagnostic is not None)
        folder = "tests/fixtures/" + PREFIX + name.lower()
        file = source_name(rule)
        expectation = dict(phase="compile", step=Path(file).stem,
                           outcome="diagnose" if diagnostic else "success")
        if diagnostic:
            expectation["diagnostic"] = diagnostic
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=list(facets), standard="f2023",
            evidence="effect" if diagnostic else "positive-control", files=[file],
            build=[dict(id=Path(file).stem, source=file, language="fortran", form="free",
                        output=Path(file).stem + ".o", depends_on=[])],
            expect=expectation,
        )
        self.put(folder + "/" + file, text(source))
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, variant=variant, kind="invalid" if diagnostic else "valid",
                                phase="compile", evidence=manifest["evidence"], facets=list(facets),
                                path=folder + "/fixture.json", source_file=file,
                                source_premise=premise, constructor=constructor)
        return name

    def pair(self, rule, variant, facet, source, wrong, repaired, anchor, premise, constructor,
             admission=None, exclusions=()):
        source = text(source)
        if source.count(wrong) != 1 or wrong == repaired:
            raise ValueError(f"{rule}/{variant}: repair is not one unique source span")
        points = [i for i, line in enumerate(source.splitlines(), 1) if line == anchor]
        if len(points) != 1:
            raise ValueError(f"{rule}/{variant}: diagnostic source anchor is not unique")
        route = diagnostic_routes()[(rule, variant)]
        diagnostic = dict(file=source_name(rule), line=points[0],
                          contains_any=quote_variants(route), excludes_any=EXCLUDED + list(exclusions))
        bad = self.compile(rule, variant, [facet], source, diagnostic, premise, constructor)
        good_facets = [facet] + ([admission] if admission else [])
        good = self.compile(rule, variant + "_repair", good_facets, source.replace(wrong, repaired, 1),
                            premise=premise, constructor=constructor)
        self.repairs[bad] = dict(control=good, file=source_name(rule), wrong=wrong, repaired=repaired,
                                 anchor=anchor, line=points[0], source_relation=premise)
        return bad


PAIR = "type :: pair\ninteger :: left\ninteger :: right\nend type pair\n"
PAIR_DECL = "type(pair) :: value\n"
POINTER_HOLDER = """type :: holder
integer, pointer :: one=>null()
integer, pointer :: many(:)=>null()
end type holder
"""
POINTER_DECL = """type(holder) :: value
integer, target :: scalar_target,vec(2)
integer, pointer :: scalar_mold=>null()
integer, pointer :: array_mold(:)=>null()
"""
POINTER_CONTEXTS = """scalar_target=17
vec(1)=11
vec(2)=13
value=holder(one=scalar_target,many=vec)
value=holder(one=vec(1),many=vec(1:2))
value=holder(one=null(),many=null())
value=holder(one=null(mold=scalar_mold),many=null(mold=array_mold))
"""


def build_corpus(root=ROOT):
    c = Corpus(root)
    c.compile("R756", "empty_components", ["empty-component-list"],
              complete("type :: empty\nend type empty\n"
                       "type :: defaulted\ninteger :: payload=11\nend type defaulted\n",
                       "type(empty) :: a\ntype(defaulted) :: b\n", "a=empty()\nb=defaulted()\n"),
              premise="Two nonabstract ordinary types: genuinely empty and actually defaulted. "
              "Both component parentheses remain. No same-name generic or runtime-value oracle.")
    source = complete("type, abstract :: base\ninteger :: payload\nend type base\n", "",
                      "call observe(base(payload=17))\n",
                      "subroutine observe(self)\nclass(base), intent(in) :: self\nend subroutine observe\n")
    c.pair("C7101", "abstract", "abstract-constructor", source, ", abstract", "",
           "call observe(base(payload=17))",
           "Only ABSTRACT and its comma are removed. The type has no deferred bindings, and the explicit "
           "CLASS(base),IN observer stays legal; no TYPE(base) variable/dummy introduces C706.",
           "base", "concrete-constructor-admission")
    for variant, facet, expr in (
        ("repeated_keyword", "repeated-keyword", "pair(left=11,left=13,right=17)"),
        ("positional_repeat", "positional-keyword-repeat", "pair(11,left=13,right=17)"),
    ):
        source = complete(PAIR, PAIR_DECL, "value=pair(left=11,right=11)\nvalue=" + expr + "\n")
        c.pair("C7102", variant, facet, source, "left=13,", "", "value=" + expr,
               "Every required component is supplied; delete only the repeated left specification. "
               "Both sources also contain the legal equal-valued distinct-component admission, so the "
               "repair is the admission witness without a cloned third program.",
               "pair", "different-components-admission")
    source = complete(
        "type :: parent\ninteger :: x\ninteger :: y\nend type parent\n"
        "type, extends(parent) :: child\ninteger :: z\nend type child\n",
        "type(parent) :: parent_value\ntype(child) :: value\n",
        "parent_value%x=11\nparent_value%y=13\nvalue=child(parent=parent_value,x=17,z=19)\n")
    c.pair("C7103", "ancestor_overlap", "parent-and-inherited-member", source, "x=17,", "",
           "value=child(parent=parent_value,x=17,z=19)",
           "Named primitive parent setup gives x11/y13. Delete only inherited x from the constructor; "
           "the supplied nonabstract parent still covers x/y and required local z remains19. No positional "
           "parent constructor, inaccessible component or duplicate component identity supplies the cause.",
           "child", "disjoint-ancestor-and-child")
    c.pair("C7104", "missing_ordinary", "missing-ordinary-component",
           complete(PAIR, PAIR_DECL, "value=pair(left=11)\n"),
           "pair(left=11)", "pair(left=11,right=13)", "value=pair(left=11)",
           "Only required right is absent; adding right=13 leaves type, access and left unchanged.", "pair")
    c.pair("C7104", "missing_pointer", "missing-pointer-component",
           complete("type :: holder\ninteger, pointer :: p\nend type holder\n",
                    "type(holder) :: value\n", "value=holder()\n"),
           "holder()", "holder(p=null())", "value=holder()",
           "The nonallocatable pointer p has no default. Contextual NULL supplies it in the repair; "
           "no target, pointer value or bounds are read.", "holder")
    c.pair("C7105", "keyword_order", "positional-after-keyword",
           complete(PAIR, PAIR_DECL, "value=pair(11,right=13)\nvalue=pair(left=11,13)\n"),
           "pair(left=11,13)", "pair(left=11,right=13)", "value=pair(left=11,13)",
           "Insert only the later right keyword; the two components are otherwise supplied once. "
           "Both sources retain the distinct legal positional-prefix form, so the repair also witnesses "
           "that admission. An ordinary-call, duplicate or missing-component cause cannot qualify.",
           "pair", "positional-prefix-admission")
    c.pair("C7106", "unknown_keyword", "unknown-component-keyword",
           complete("type :: packet\ninteger :: payload\nend type packet\n",
                    "type(packet) :: value\n", "value=packet(payload=17,extra=19)\n"),
           ",extra=19", "", "value=packet(payload=17,extra=19)",
           "Delete only noncomponent keyword extra; required payload17 stays present. No competing generic.",
           "packet")
    c.pair("C7106", "parameter_keyword", "parameter-is-not-component",
           complete("type :: packet(k)\ninteger, kind :: k\ninteger :: payload\nend type packet\n",
                    "type(packet(k=2)) :: value\n", "value=packet(k=2)(payload=17,k=3)\n"),
           ",k=3", "", "value=packet(k=2)(payload=17,k=3)",
           "k=2 belongs to the complete first PDT list. Delete only second-list k=3; k is a user type "
           "parameter, never an intrinsic representation selector, and payload remains17.", "packet")
    definitions = """type :: holder
integer, pointer :: p=>null()
procedure(action_interface), pointer, nopass :: action=>null()
end type holder
"""
    interfaces = "abstract interface\nsubroutine action_interface()\nend subroutine action_interface\nend interface\n"
    procedures = "subroutine worker()\nend subroutine worker\n"
    declarations = "type(holder) :: value\ninteger, target :: datum\n"
    for variant, facet, expr, fixed in (
        ("procedure_in_data", "procedure-target-in-data-slot", "holder(p=worker)", "holder(action=worker)"),
        ("data_in_procedure", "data-target-in-procedure-slot", "holder(action=datum)", "holder(p=datum)"),
    ):
        c.pair("C7109", variant, facet,
               complete(definitions, declarations, "datum=17\nvalue=" + expr + "\n", procedures, interfaces),
               expr, fixed, "value=" + expr,
               "Only the receiving keyword changes. Both pointer defaults are bare NULL(). The module "
               "procedure has a complete matching zero-argument explicit interface and the component has "
               "NOPASS; datum is a defined live scalar INTEGER TARGET. No target is dereferenced or called.",
               "holder")
    for variant, facet, expr, fixed in (
        ("array_to_scalar", "array-target-to-scalar-pointer", "holder(one=vec)", "holder(one=vec(1))"),
        ("scalar_to_array", "scalar-target-to-array-pointer", "holder(many=scalar_target)", "holder(one=scalar_target)"),
    ):
        c.pair("C7110", variant, facet,
               complete(POINTER_HOLDER, POINTER_DECL, POINTER_CONTEXTS + "value=" + expr + "\n"),
               expr, fixed, "value=" + expr,
               "Repair only the TARGET element selection or receiving keyword. Both omitted pointer slots "
               "are genuinely defaulted. Shared valid contexts cover scalar/array variables, a true TARGET "
               "element and same-rank section, contextual NULL and typed NULL(MOLD=...) with declared "
               "disassociated pointer molds. No broadcasting, remapping, target or bounds inquiry is used.",
               "holder", "same-rank-and-null-context")
    c.compile("S7.5.10-006", "prior_definition", ["prior-definition-admission"],
              complete("type :: prior\ninteger :: payload\nend type prior\n",
                       "type(prior), parameter :: declared=prior(payload=17)\n", ""),
              premise="The accessible complete type precedes a valid initialized PARAMETER declaration. "
              "This is a genuine compile-only positive control for an unnumbered restriction, not an effect "
              "or mandatory diagnostic policy.")
    if c.coverage() != {r: set(f) for r, f in ELIGIBLE.items()}:
        raise ValueError("constructor declaration coverage differs from the twenty authorized facets")
    if len(c.cases) != 28 or len(c.repairs) != 13:
        raise ValueError("the bounded corpus requires thirteen pairs and two additional admissions")
    return c.files, c.cases, c.repairs


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def synced_catalogue(catalogue, specs):
    result = json.loads(json.dumps(catalogue))
    for requirement in result["requirements"]:
        owned = [s for s in specs.values() if s["rule"] == requirement["id"]]
        represented = {f for s in owned for f in s["facets"]}
        for facet in represented:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != (
                set(requirement["facets"]) - represented - EXISTING.get(requirement["id"], set())):
            raise ValueError("constructor pending partition mismatch: " + requirement["id"])
        if owned:
            old = requirement["oracle"].split("\n\nCompile-only declaration packet:", 1)[0]
            requirement["oracle"] = old + (
                f"\n\nCompile-only declaration packet: {len(owned)} cases represent {len(represented)} "
                "selected facets. Invalid cases require located, subject/role/property-specific reporting; "
                "normal zero/nonzero compiler statuses do not replace that obligation. Repairs and valid "
                "admissions are positive controls. No runtime effect, new policy or unregistered source-use "
                "credit is inferred. All other original pending plans and qualifications are retained.")
    return result


DOCUMENT = """## Bounded source and implementation gate

Authority: J3/24-007, **18 December 2023**, **688 physical PDF pages**, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The source checkpoint is `8ba944c4fffb6ea56a4594e75b3d8bff9d6abcda`.
Independent `constructors-source-review.json` has SHA-256
`132824f1265b76f2c836b99bb649379d88da7023eb709d2eca7ba1b12a09ee04`.
The exact compile-only scope map has SHA-256
`4cc8d934e25a610115683da1a5f815780ba6b1a888f09963e94424f4935c80d3`.
Original PDF106-109 and the directed abstract/PDT/component/inheritance,
pointer-assignment, NULL, accessibility and reporting dependencies were read.
Neither a compiler outcome nor another language's convention defines an oracle.

The source identity/accounting is unchanged:28 base units,114 fine units and142
accounting rows. On PDF107, the retained `note4` census slice completes NOTE2's
embedded reference to7.5.7.2 NOTE4; it is not a fresh note heading. `note2.2`
continues NOTE2 on PDF108. `note4.2` is the genuine NOTE4 there. All these
identities, source qualifiers and dispositions remain intact, ending before7.5.11.

## Concrete declaration and reporting premises

* Empty constructors have actual empty/defaulted types, required parentheses and
  no same-name generic. There is no empty-value runtime assertion.
* The abstract negative has no deferred binding and uses an explicit CLASS(base),
  INTENT(IN) observer. Its only repair removes ABSTRACT and its comma; no illegal
  TYPE(base) variable or dummy introduces a different abstract-type condition.
* Duplicate-component sources supply every other required component. Distinct
  components may have equal literals; both sources retain that valid context.
  Ancestor overlap instead uses parent x11/y13 set by independent named writes,
  supplies required local z19, and removes only the overlapping inherited x.
* Missing ordinary/pointer components are actually nondefaulted. Contextual
  NULL() supplies the missing pointer without a target/bounds read. Keyword-order
  repairs leave every component once and preserve the admitted positional prefix.
* The user PDT tag k=2 is specified only in the first parameter list. The extra
  second-list k is deleted; no intrinsic hardware kind or empty first parameter
  list is introduced.
* Data/procedure-pointer category repairs change only the receiving keyword.
  Both slots really default to bare NULL(). A complete explicit interface and
  NOPASS match the eligible module subroutine; the data TARGET is defined/live.
* Rank repairs use a true TARGET element or change to the correctly ranked slot.
  Both slots have actual defaults. Same-rank variables/sections, contextual NULL
  and NULL(MOLD=typed_pointer) appear in the shared sources. Molds are explicitly
  disassociated, but no pointer is dereferenced. General NULL construction is
  not the R806/C813 no-argument null-init context.
* Every new case is compile-phase. Thirteen source-minimal repairs also supply
  the corresponding admissions, including additional legal forms in the same
  source, rather than cloned third programs. S7.5.10-006 is a positive control for
  a restriction, using prior definition and constant declaration initialization.
* Numbered reporting capability is not fatal rejection or mandatory printed
  codes. Normal-status error reports may qualify; warnings/portability require
  exact family/severity permissions, not blanket warning acceptance. Cause,
  subject/property, input file and source point must all match.
* The TBFR-001/002 and DCFR-001 lessons are retained: no bare punctuation/attribute
  predicates, unsupported wrappers, wrong-role/property/source echoes, generic
  recovery, Internal/verifier/crash, timeout or resource failure can supply a
  different diagnostic. No unsupported facility is turned into a skip or success.

### Native cause qualification

The named repeated-keyword report is accepted only for the actual repeated-keyword
C7102 form, not its positional/keyword counterpart. For C7103, a constructor
conflict naming x is bound to the source where the only earlier specification is
its ancestor parent; a bare duplicate-component claim is not substituted.
C7105 can use the specific constructor-value-missing-name report at its unique
post-keyword positional entry, but not the companion missing-right recovery or
an ordinary-call argument-list error. C7106 does not accept the erroneous claim
that the user type parameter k is a component initialized twice.

Bare terminal rank messages are not adopted: the contains-only predicate could
otherwise match rank10 as rank1. The complete parenthesized GNU rank pair and
punctuated case-specific forms retain numeric boundaries. This limitation does
not justify a shared harness change or a weaker rank oracle. Original failures
and the exact current-fingerprint refresh selection are preserved separately.

## Historical C7107 representation and integration boundary

The four existing C7107 manifests, provider/client bytes, IDs, facets and
compile/effect versus compile/positive-control roles are unchanged. At the
author base98c6db06c759d46fff2c142a2614a402309ee6a9, registering the detailed
C7107 requirement deliberately changes their four requirement-bound fingerprints
and three dependent link fingerprints. The historical two represented facets
remain represented; authorship is not current approval. Independent decisions
and explicit source/case/link/inventory renewals are recorded in
`doc/source_audits/batch_023.json`, not performed by this generator.

Original and any refreshed observations retain their actual source_root,
compiler identities, standards, inputs and commands. Exact current-row selection
is recorded in `constructor-declarations-handoff.json`, never as an invented
combined run. Frozen LF411, GNU f2023 and actual Flang f2018 are not relabelled.
The other1869 base case fingerprints/inputs and all protected shared files stay
unchanged. The local index overlay is excluded from the owned commit.

No runtime, source-contrast, profile, C companion, coarray or diagnostic policy
is implemented by these fixtures. Integration retains the then-current nine
link declarations and explicitly renews only the three C7107-dependent receipts;
the separate five binding-reuse connections are not overwritten by the older
author context. Remaining original plans below stay pending in full.
"""


def render_view(catalogue, specs, repairs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    out = (
        "# Fortran 2023: 7.5.10 Construction of derived-type values\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Case and evidence adjudications are separate content-bound records.\n\n"
        f"The bounded declaration corpus has **{len(specs)} new compile-only cases**: "
        f"**{len(repairs)} diagnostics** and **{len(specs)-len(repairs)} positive controls**. "
        f"Together with the **four unchanged C7107 cases**, **{98-pending} of98 facets "
        f"are represented; {pending} remain pending**.\n\n" + DOCUMENT
        + "\n## Preserved source accounting\n\n")
    for row in catalogue["accounting"]:
        detail = ", ".join(row.get("requirements", [])) or row["rationale"]
        out += f"* `{row['unit']}`: **{row['disposition']}** - {detail}\n"
    out += ("\n## Definitions\n\n<!-- BEGIN GENERATED 7.5.10 -->\n\n"
            + "\n".join(render_requirement(r) for r in catalogue["requirements"])
            + "\n<!-- END GENERATED 7.5.10 -->\n\n## Exact compile-only cases and repairs\n\n")
    for name, spec in specs.items():
        out += (f"### `{name}`\n\n**Primary:** {spec['rule']}; **facets:** "
                + ", ".join(f"`{f}`" for f in spec["facets"])
                + f"; **phase/evidence:** compile / {spec['evidence']}.\n\n{spec['source_premise']}\n\n")
        if name in repairs:
            repair = repairs[name]
            out += (f"Control: `{repair['control']}`. The sole source repair in `{repair['file']}` "
                    f"is `{repair['wrong']}` -> `{repair['repaired']}`; diagnostic point "
                    f"is line{repair['line']}.\n\n")
    out += ("## Complete finite pending plans\n\n"
            "The following original plan text is retained verbatim as plan metadata. "
            "Authorship or a prerequisite observation does not implement a graph or policy.\n\n")
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            out += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                out += f"* **`{facet}`** - {plan}\n"
            out += "\n"
    out += (
        "## Reproduction and separate gates\n\n"
        "`python3 -B tools/generate_constructor_declaration_fixtures.py --check` checks the "
        "exact owned fixture bytes, facet partition and phase-aware rendered view. The focused "
        "regressions exercise minimal repairs, independently derived source faults, reporting "
        "capability at normal statuses and strict cause/nonfatal/failure guards. No check or "
        "processor observation grants a case, catalogue or link approval. The independent "
        "fixture/cause and current-observation decisions are in `doc/source_audits/batch_023.json`; "
        "all17valid controls compile with GNU f2023, and three negatives retain explicit "
        "source-only adjudication without weakening their source or reporting expectations.\n")
    return out


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
        wrong = [str(p.relative_to(ROOT)) for p, b in outputs.items()
                 if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob(PREFIX + "*/*") if p.is_file()}
        wrong += [str(p.relative_to(ROOT)) for p in actual - set(outputs)]
        if catalogue != updated:
            wrong.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            wrong.append(VIEW)
        if wrong:
            raise SystemExit("stale constructor declaration packet: " + ", ".join(sorted(wrong)))
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files; {len(specs)} compile cases, "
          f"{len(repairs)} minimal repairs, 20 new represented facets.")


if __name__ == "__main__":
    main()
