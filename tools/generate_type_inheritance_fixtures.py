#!/usr/bin/env python3
"""Generate only the reviewed finite runtime inheritance plans."""
import argparse
import copy
import json
from pathlib import Path
import sys
import textwrap

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ("7.5.7.1", "7.5.7.2")
PREFIX = "type_inheritance_"
ELIGIBLE = {
    "S7.5.7.1-003": (
        "root-reflexivity", "extended-reflexivity", "direct-and-indirect-ancestry",
        "reverse-direction", "sibling-and-unrelated-boundaries", "dynamic-effective-type"),
    "S7.5.7.2-001": ("inherited-public-components", "inherited-private-component-identity"),
    "S7.5.7.2-002": ("scalar-parent-type-observable", "parent-parameter-values", "array-designator-boundary"),
    "S7.5.7.2-003": ("use-alias-component-name", "original-module-public-access"),
    "S7.5.7.2-004": ("direct-associated-views", "recursive-ancestor-views"),
    "S7.5.7.2-005": ("named-generic-union", "union-with-specific-override", "different-generic-identifier"),
}
MATRIX_ORDER = ("root", "child", "grand", "sibling", "other")
MATRIX_ROWS = ("TFFFF", "TTFFF", "TTTFF", "TFFTF", "FFFFT")


def catalogue_path(section):
    return "doc/catalogues/derived_types_" + section.replace(".", "_") + ".json"


def view_path(section):
    return "doc/fortran_2023_" + section.replace(".", "_") + ".md"


def text(value):
    return textwrap.dedent(value).strip("\n") + "\n"


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__" + variant


def evidence_for_category(category):
    roles = {"effect": "effect", "restriction": "positive-control", "syntax": "positive-control",
             "undefined-result": "context-only"}
    if category not in roles:
        raise ValueError("unknown requirement category: " + category)
    return roles[category]


class Corpus(ParameterCorpus):
    def __init__(self, categories, root=ROOT):
        super().__init__(namespace="type_inheritance", root=root)
        self.categories = categories

    def run(self, rule, variant, facets, body, shared=None):
        name = identifier(rule, variant)
        if name in self.cases:
            raise ValueError("duplicate execution: " + name)
        inputs = body if isinstance(body, dict) else {
            rule.replace(".", "_").replace("-", "_") + ".f90": text(body)}
        folder = "tests/fixtures/" + PREFIX + name.lower()
        steps = []
        for filename, content in inputs.items():
            self.put(folder + "/" + filename, text(content))
            step = Path(filename).stem
            steps.append(dict(id=step, source=filename, language="fortran", form="free",
                              output=step + ".o", depends_on=[item["id"] for item in steps]))
        category = self.categories[rule]
        evidence = evidence_for_category(category)
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=list(facets), evidence=evidence,
            standard="f2023", files=list(inputs), build=steps,
            link=dict(objects=[item["output"] for item in steps], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0))
        path = folder + "/fixture.json"
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, category=category, facets=list(facets),
                                kind="valid", phase="run", evidence=evidence, standard="f2023",
                                coarray=False, profiles=[], images=1, path=path, shared_case=shared)

    def program(self, rule, variant, facets, body, shared=None):
        self.run(rule, variant, facets, "program p\n" + text(body) + "end program p\n", shared)


TREE = """type :: root
    integer :: payload
end type
type, extends(root) :: child
    integer :: child_marker
end type
type, extends(child) :: grand
    integer :: grand_marker
end type
"""


def ancestry(c):
    body = ("implicit none\n" + TREE
            + "type, extends(root) :: sibling\ninteger :: sibling_marker\nend type\n"
            "type :: other\ninteger :: payload\nend type\n"
            "type(root) :: root_value\ntype(child) :: child_value\ntype(grand) :: grand_value\n"
            "type(sibling) :: sibling_value\ntype(other) :: other_value\nlogical :: actual(5,5)\n"
            "root_value%payload = 11\nchild_value%payload = 13\nchild_value%child_marker = 41\n"
            "grand_value%payload = 17\ngrand_value%child_marker = 43\ngrand_value%grand_marker = 47\n"
            "sibling_value%payload = 19\nsibling_value%sibling_marker = 53\nother_value%payload = 23\n")
    for i, first in enumerate(MATRIX_ORDER, 1):
        for j, mold in enumerate(MATRIX_ORDER, 1):
            body += f"actual({i},{j}) = extends_type_of({first}_value, {mold}_value)\n"
    for i, row in enumerate(MATRIX_ROWS, 1):
        expected = ",".join(".true." if value == "T" else ".false." for value in row)
        body += f"if (any(actual({i},:) .neqv. [{expected}])) error stop {i}\n"
    c.program("S7.5.7.1-003", "matrix_m", ELIGIBLE["S7.5.7.1-003"][:5], body, shared="M")
    c.program("S7.5.7.1-003", "dynamic_dummy", ["dynamic-effective-type"],
              "implicit none\n" + TREE + """type(grand) :: value
type(child) :: mold
type(root) :: base
logical :: observed
value%payload = 17
value%child_marker = 41
value%grand_marker = 43
mold%payload = 19
mold%child_marker = 47
base%payload = 23
call inspect_dynamic(value, mold, observed)
if (.not. observed) error stop 1
if (extends_type_of(base, mold)) error stop 2
contains
subroutine inspect_dynamic(item, child_mold, result)
class(root), intent(in) :: item
type(child), intent(in) :: child_mold
logical, intent(out) :: result
if (item%payload /= 17 .or. child_mold%payload /= 19) error stop 3
result = extends_type_of(item, child_mold)
end subroutine
""")


def inherited_members(c):
    c.program("S7.5.7.2-001", "public_components", ["inherited-public-components"], """
        implicit none
        type :: parent
            integer :: left, right
        end type
        type, extends(parent) :: child
            integer :: marker
        end type
        type(child) :: object
        object%left = 3
        object%right = 7
        object%marker = 41
        if (object%left /= 3) error stop 1
        if (object%right /= 7) error stop 2
        if (object%marker /= 41) error stop 3
    """)
    c.run("S7.5.7.2-001", "private_homonym", ["inherited-private-component-identity"], {
        "provider.f90": """module provider
implicit none
private
public :: parent, set_hidden, get_hidden
type :: parent
    private
    integer :: hidden
end type
contains
subroutine set_hidden(object, number)
class(parent), intent(inout) :: object
integer, intent(in) :: number
object%hidden = number
end subroutine
integer function get_hidden(object) result(number)
class(parent), intent(in) :: object
number = object%hidden
end function
end module
""",
        "extension.f90": """module extension
use provider, only: parent
implicit none
type, extends(parent) :: child
    integer, public :: hidden
end type
end module
""",
        "S7_5_7_2_001.f90": """program p
use provider, only: set_hidden, get_hidden
use extension, only: child
implicit none
type(child) :: object
integer :: inherited_value
object%hidden = 9
call set_hidden(object, 7)
inherited_value = get_hidden(object)
if (inherited_value /= 7) error stop 1
if (object%hidden /= 9) error stop 2
end program
""",
    })


PARENT = """type :: parent
    integer :: payload
end type
type, extends(parent) :: child
    integer :: marker
end type
"""


def parent_components(c):
    c.program("S7.5.7.2-002", "scalar_parent", ["scalar-parent-type-observable"],
              "implicit none\n" + PARENT + """type(child) :: object
integer :: observed
object%payload = 17
object%marker = 41
if (rank(object%parent) /= 0) error stop 1
observed = parent_payload(object%parent)
if (observed /= 17) error stop 2
if (object%marker /= 41) error stop 3
contains
integer function parent_payload(item) result(value)
type(parent), intent(in) :: item
value = item%payload
end function
""")
    c.program("S7.5.7.2-002", "parent_parameters", ["parent-parameter-values"], """
        implicit none
        type :: parent(k,n)
            integer, kind :: k
            integer, len :: n
            integer :: payload
        end type
        type, extends(parent) :: child(m)
            integer, len :: m
            integer :: marker
        end type
        type(child(k=2,n=3,m=5)) :: object
        object%payload = 17
        object%marker = 41
        if (object%parent%k /= 2) error stop 1
        if (object%parent%n /= 3) error stop 2
        if (object%m /= 5) error stop 3
        if (object%parent%payload /= 17) error stop 4
        if (object%marker /= 41) error stop 5
    """)
    c.program("S7.5.7.2-002", "array_parent_designator", ["array-designator-boundary"],
              "implicit none\n" + PARENT + """type(child) :: objects(2)
objects%payload = [17,19]
objects%marker = [41,43]
if (rank(objects%parent) /= 1) error stop 1
if (rank(objects(1)%parent) /= 0) error stop 2
if (any(objects%parent%payload /= [17,19])) error stop 3
if (any(objects%marker /= [41,43])) error stop 4
""")


def parent_name(c):
    c.run("S7.5.7.2-003", "renamed_parent_n", ELIGIBLE["S7.5.7.2-003"], {
        "provider.f90": """module provider
implicit none
private
public :: set_payload
type, public :: original
    integer, public :: payload
end type
contains
subroutine set_payload(item)
class(original), intent(inout) :: item
item%payload = 17
end subroutine
end module
""",
        "extension.f90": """module extension
use provider, only: alias => original, set_payload
implicit none
private
private :: alias
public :: child, object, initialize
type, extends(alias) :: child
    private
    integer :: marker
end type
type(child) :: object
contains
subroutine initialize()
object%marker = 41
call set_payload(object)
end subroutine
end module
""",
        "S7_5_7_2_003.f90": """program p
use extension, only: object, initialize
implicit none
integer :: observed
call initialize()
observed = object%alias%payload
if (observed /= 17) error stop 1
end program
""",
    }, shared="N")


def associated_views(c):
    c.program("S7.5.7.2-004", "direct_views", ["direct-associated-views"], """
        implicit none
        type :: parent
            integer :: value
        end type
        type, extends(parent) :: child
            integer :: marker
        end type
        type(child) :: object
        object%value = 3
        object%marker = 41
        if (object%parent%value /= 3) error stop 1
        object%parent%value = 7
        if (object%value /= 7) error stop 2
        if (object%marker /= 41) error stop 3
        object%value = 11
        if (object%parent%value /= 11) error stop 4
        if (object%marker /= 41) error stop 5
    """)
    c.program("S7.5.7.2-004", "recursive_views", ["recursive-ancestor-views"], """
        implicit none
        type :: root
            integer :: value
        end type
        type, extends(root) :: mid
            integer :: mid_marker
        end type
        type, extends(mid) :: leaf
            integer :: leaf_marker
        end type
        type(leaf) :: object
        object%mid_marker = 41
        object%leaf_marker = 43
        object%mid%root%value = 31
        if (object%root%value /= 31) error stop 1
        if (object%value /= 31) error stop 2
        object%value = 37
        if (object%mid%root%value /= 37) error stop 3
        if (object%root%value /= 37) error stop 4
        if (object%mid_marker /= 41) error stop 5
        if (object%leaf_marker /= 43) error stop 6
    """)


def generic_family(c):
    declarations = """module generic_types
implicit none
type :: parent
    integer :: payload
contains
    procedure :: pi => parent_integer
    generic :: g => pi
end type
type, extends(parent) :: child
    integer :: marker
contains
    procedure :: cr => child_real
    generic :: g => cr
end type
type, extends(parent) :: overriding_child
    integer :: marker
contains
    procedure :: pi => override_integer
    procedure :: cr => override_real
    generic :: g => cr
end type
type, extends(parent) :: separate_child
    integer :: marker
contains
    procedure :: cr => separate_real
    generic :: h => cr
end type
contains
integer function parent_integer(self,x) result(value)
class(parent), intent(in) :: self
integer, intent(in) :: x
if (self%payload /= 17 .or. x /= 1) error stop 21
value = 11
end function
integer function override_integer(self,x) result(value)
class(overriding_child), intent(in) :: self
integer, intent(in) :: x
if (self%payload /= 17 .or. self%marker /= 41 .or. x /= 1) error stop 22
value = 33
end function
"""
    for procedure, typename, marker in (
        ("child_real", "child", 31), ("override_real", "overriding_child", 41),
        ("separate_real", "separate_child", 43),
    ):
        declarations += (f"integer function {procedure}(self,x) result(value)\n"
                         f"class({typename}), intent(in) :: self\nreal, intent(in) :: x\n"
                         f"if (self%payload /= 17 .or. self%marker /= {marker} .or. x /= 1.0) error stop 23\n"
                         "value = 22\nend function\n")
    declarations += "end module\n"
    main = """program p
use generic_types, only: child, overriding_child, separate_child
implicit none
type(child) :: a
type(overriding_child) :: b
type(separate_child) :: c
integer :: observed
a%payload = 17
a%marker = 31
b%payload = 17
b%marker = 41
c%payload = 17
c%marker = 43
observed = a%g(1)
if (observed /= 11) error stop 1
observed = a%g(1.0)
if (observed /= 22) error stop 2
observed = b%g(1)
if (observed /= 33) error stop 3
observed = b%g(1.0)
if (observed /= 22) error stop 4
observed = c%g(1)
if (observed /= 11) error stop 5
observed = c%h(1.0)
if (observed /= 22) error stop 6
end program
"""
    c.run("S7.5.7.2-005", "generic_union_g", ELIGIBLE["S7.5.7.2-005"],
          {"generic_types.f90": declarations, "S7_5_7_2_005.f90": main}, shared="G")


def build_corpus(root=ROOT, categories=None):
    if categories is None:
        categories = {}
        for section in SECTIONS:
            catalogue = json.loads((root / catalogue_path(section)).read_text())
            categories.update({req["id"]: req["category"] for req in catalogue["requirements"]})
    corpus = Corpus(categories, root)
    ancestry(corpus)
    inherited_members(corpus)
    parent_components(corpus)
    parent_name(corpus)
    associated_views(corpus)
    generic_family(corpus)
    return corpus.files, corpus.cases


ORACLES = {
    "S7.5.7.1-003": "One shared matrix M evaluates all25 ordered pairs once using five concrete, nonpointer, nonallocatable extensible objects. Literal expected rows TFFFF/TTFFF/TTTFF/TFFTF/FFFFT are independent of every inquiry result. Direct calls avoid an incompatible CLASS(root) helper for unrelated other. The separate dynamic case passes a live grand actual to CLASS(root), obtains true against a child MOLD, and independently checks that a real root object gives false against the same MOLD. All payloads and local markers are defined by named assignments.",
    "S7.5.7.2-001": "Two runtime cases observe inherited public values (3,7) with marker41 and independent private/public homonym values (7,9). The private provider setter writes only its CLASS(parent) dummy's own hidden field; the unrelated child's public hidden is set separately. The getter result and public field are checked after the calls return. No modified overlapping actuals, private client selectors or constructor-order setup are used.",
    "S7.5.7.2-002": "Three runtime cases observe a scalar parent component through RANK=0 and an explicit TYPE(parent) helper yielding17; keyword-instantiated abstract parameters k=2,n=3,m=5 through the actual parent selector; and rank1 for an array parent designator versus rank0 for one element's parent. Objects and markers are defined before inquiry or calls. No pointer/allocatable-absence or storage-layout property is inferred.",
    "S7.5.7.2-003": "One shared N case compiles provider, extension and client in order. Provider original and its payload are PUBLIC; extension alias is PRIVATE and its child has a PRIVATE component default. An owner CLASS(original) setter defines payload17 through the actual parent type, independently from the client object%alias%payload selector. The child/object/initializer are exported, and no private local marker or unavailable type name is used by the client.",
    "S7.5.7.2-004": "Two sequential runtime cases observe direct parent/inherited paths sharing3, then7, then11 while marker41 persists, and recursive root paths sharing31 then37 while mid/leaf markers41/43 persist. Each mutation completes before any comparison; no overlapping actual arguments, address comparison or positional constructor supplies the result.",
    "S7.5.7.2-005": "One shared G family observes (11,22), (33,22) and (11,22). A parent integer-specific pi is inherited; the first child adds only real cr to g; the second also overrides pi with matching names/positions/characteristics except self type; the third adds h instead of extending g. Each child has its own C765-correct real target. Six separately evaluated legal calls use only the nonpassed INTEGER/REAL discriminator and initialized receivers/results. No pi is repeated in a child GENERIC list and no child-only real generic is called through an ineligible declared type.",
}


def synced_catalogue(catalogue, specs):
    updated = copy.deepcopy(catalogue)
    for requirement in updated["requirements"]:
        rule = requirement["id"]
        represented = {facet for spec in specs.values() if spec["rule"] == rule for facet in spec["facets"]}
        if represented != set(ELIGIBLE.get(rule, ())):
            raise ValueError("unexpected runtime facet partition for " + rule)
        for facet in represented:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - represented:
            raise ValueError("missing original pending plan for " + rule)
        if rule in ORACLES:
            requirement["oracle"] = ORACLES[rule]
    return updated


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[catalogue["section"]] = catalogue
    return registry.catalogue_review_state(catalogue["section"])


def pending_appendix(catalogue):
    out = ["## Complete pending plans\n",
           "The following is the exact current JSON pending map. No graph, optional policy "
           "or declaration-only wrapper receives execution credit.\n"]
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            out.append(f"### Pending {requirement['id']}\n")
            for facet, plan in requirement["pending"].items():
                out.append(f"* **`{facet}`**: {plan}")
            out.append("")
    return "\n".join(out) + "\n"


PREMISES = """## Shared runtime premises P1-P7

* P1: Objects are live ordinary concrete extensible types, nonpointer and
  nonallocatable, with defined fields before reads. The explicit two-element
  selector case is the only array-object variation. Whole-parent observations
  use nonabstract parents.
* P2: Named assignments establish small values independently from result
  comparisons. Setter calls complete before getters and observations. There are
  no modified overlapping actuals, constructor-order cancellation or escaped
  pointer lifetimes.
* P3: Accessible module targets have explicit interfaces. Passed self is scalar
  CLASS of the declaring type, nonpointer, nonallocatable and non-VALUE; there
  are no LEN parameters in G. Ordinary TYPE(parent) and CLASS(parent) helpers
  are used only with their respective legal actual arguments.
* P4: G's one specific override preserves dummy names/positions, nonpassed
  INTEGER characteristics and scalar INTEGER result, except for self's
  declaring child type. It is a dependency of the authorized generic-union
  observation, not a new 7.5.7.3 fixture or added-parameter-domain interpretation.
* P5: All cases are runtime success expectations, with evidence roles derived
  from actual catalogue categories. No diagnostic/rejection policy or
  source-only classification program is introduced.
* P6: M contains exactly25 ordered EXTENDS_TYPE_OF calls on the five eligible
  objects. Its literal truth table follows the parent graph, not compiler
  inquiries. The dynamic case uses a live grand actual; absent, opaque,
  nonextensible and processor-dependent residual branches are excluded.
* P7: Private members are accessed only in their defining owner. N distinguishes
  original-module PUBLIC access from a PRIVATE imported alias and child default.
  No address, SIZEOF, representation, finalization or I/O-byte oracle is used.
"""


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    section = catalogue["section"]
    rows = [spec for spec in specs.values() if spec["rule"].startswith("S" + section + "-")]
    declared = sum(len(req["facets"]) for req in catalogue["requirements"])
    pending = sum(len(req["pending"]) for req in catalogue["requirements"])
    heading = ("Extensible, extended, and abstract types" if section == "7.5.7.1" else "Inheritance")
    out = (f"# Fortran 2023: {section} {heading} - runtime fixtures\n\n"
           f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
           "Case and evidence approvals are separate content-bound records.\n\n"
           "Authority: checksum-pinned J3/24-007, 18 December2023, original PDF104-106 "
           "and the directed canonical dependencies. Only7.5.7.1/.2 are owned here; the "
           "entire7.5.7.3 additional-parameter comparison question remains outside this work.\n\n"
           "Independent source, concrete oracle, namespace and runtime-mutation decisions "
           "are recorded in `doc/source_audits/batch_017.json`. Neither generation nor "
           "compiler agreement substitutes for the separate current adjudications.\n\n"
           f"This section has **{len(rows)} runtime cases**, representing **{declared-pending} "
           f"of {declared} facets**, with **{pending} PENDING**. Representation is neither "
           "compiler success nor independent adjudication. M/N/G are shared programs, not "
           "separate copies per facet.\n\n" + PREMISES + "\n")
    out += f"## Definitions\n\n<!-- BEGIN GENERATED {section} -->"
    out += "\n\n" + "\n".join(render_requirement(req) for req in catalogue["requirements"]) + "\n"
    out += f"<!-- END GENERATED {section} -->\n\n## Exact runtime case census\n\n"
    out += "| Execution | Primary owner | Evidence | Shared | Facets |\n| --- | --- | --- | --- | --- |\n"
    for name, spec in specs.items():
        if spec in rows:
            out += (f"| `{name}` | {spec['rule']} | {spec['evidence']} | {spec['shared_case'] or '-'} | "
                    + ", ".join("`" + facet + "`" for facet in spec["facets"]) + " |\n")
    out += "\n" + pending_appendix(catalogue)
    out += ("\n## Validation and review boundary\n\n"
            "`python3 -B tools/generate_type_inheritance_fixtures.py --check` checks the "
            "exact generated inputs, category-derived roles and both complete document "
            "regions. Focused tests use independent ancestry, sequential-view, namespace "
            "and generic countermodels as well as input checks. Current-fingerprint "
            "compiler and oracle-mutation reports are external artifacts, not approvals. "
            "The local index overlay is excluded. All unimplemented source-use and "
            "optional-policy plans remain pending; no compiler failure changes an oracle "
            "or turns a required runtime into an optional-success fallback.\n")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogues:
        parser.error("--check and --sync-catalogues are separate operations")
    files, specs = build_corpus()
    documents = {}
    for section in SECTIONS:
        catalogue = json.loads((ROOT / catalogue_path(section)).read_text())
        updated = synced_catalogue(catalogue, specs)
        documents[section] = (catalogue, updated, render_view(updated, specs))
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {path for path in (ROOT / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()}
        stale.extend(str(path.relative_to(ROOT)) for path in actual - set(files))
        for section, (catalogue, updated, view) in documents.items():
            if catalogue != updated:
                stale.append(catalogue_path(section))
            if (ROOT / view_path(section)).read_text() != view:
                stale.append(view_path(section))
        if stale:
            parser.exit(1, "Stale inheritance packet: " + ", ".join(sorted(stale)) + "\n")
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogues:
            for section, (_, updated, view) in documents.items():
                (ROOT / catalogue_path(section)).write_text(json.dumps(updated, indent=2) + "\n")
                (ROOT / view_path(section)).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(specs)} runtime cases.")


if __name__ == "__main__":
    main()
