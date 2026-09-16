#!/usr/bin/env python3
"""Generate the bounded ordinary overriding runtime witnesses."""
import argparse
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.7.3"
CATALOGUE = "doc/catalogues/derived_types_7_5_7_3.json"
VIEW = "doc/fortran_2023_7_5_7_3.md"
ELIGIBLE = {
    "S7.5.7.3-001": [
        "same-binding-different-target", "explicit-parent-component-call",
        "different-binding-name", "inaccessible-private-homonym", "accessible-private-parent"],
    "S7.5.7.3-011": ["override-then-inherit", "inherit-then-override"],
}
OBSERVER = """subroutine expect_value(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual /= expected) then
print *, 'OBSERVATION',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
end subroutine expect_value
"""


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__type_overriding_" + variant


def binding(target, value, name="work", access="public", passed=True):
    return dict(name=name, target=target, result=value, access=access, passed=passed)


def derived(name, parent=None, fields=None, bindings=(), module="overriding_provider"):
    return dict(name=name, parent=parent, fields=fields or {}, bindings=list(bindings), module=module)


def ancestry(types, name):
    result = []
    while name is not None:
        if name in result:
            raise ValueError("cyclic finite type graph")
        result.append(name)
        name = types[name]["parent"]
    return result


def visible_binding(types, declared, name, scope):
    for owner in ancestry(types, declared):
        for item in types[owner]["bindings"]:
            if item["name"] == name and (item["access"] == "public" or types[owner]["module"] == scope):
                return owner, item
    raise ValueError("no accessible specific binding in this finite graph")


def binding_identity(types, owner, name):
    current = next(b for b in types[owner]["bindings"] if b["name"] == name)
    parent = types[owner]["parent"]
    if parent is not None:
        inherited = [(ancestor, b) for ancestor in ancestry(types, parent)
                     for b in types[ancestor]["bindings"]
                     if b["name"] == current["name"]
                     and (b["access"] == "public" or types[ancestor]["module"] == types[owner]["module"])]
        if inherited:
            ancestor, item = inherited[0]
            return binding_identity(types, ancestor, item["name"])
    return owner, name


def resolve_binding(types, declared, dynamic, name, scope):
    if declared not in ancestry(types, dynamic):
        raise ValueError("dynamic type is outside the declared-type extension chain")
    owner, selected = visible_binding(types, declared, name, scope)
    identity = binding_identity(types, owner, selected["name"])
    for candidate in ancestry(types, dynamic):
        for item in types[candidate]["bindings"]:
            if binding_identity(types, candidate, item["name"]) == identity:
                return candidate, item
    raise ValueError("selected identity has no corresponding dynamic binding")


def model_observations(spec):
    return {call["label"]: resolve_binding(
        spec["types"], call["declared_type"], call["dynamic_type"],
        call["binding"], call["scope"])[1]["result"] for call in spec["observations"]}


def accepts(spec, observed):
    expected = {call["label"]: call["expected"] for call in spec["observations"]}
    return expected == observed


def inherited_fields(types, name):
    result = {}
    for owner in reversed(ancestry(types, name)):
        for field, value in types[owner]["fields"].items():
            if field in result:
                raise ValueError("finite fixtures require distinct accessible primitive field names")
            result[field] = value
    return result


def call(label, expression, expected, declared, dynamic, scope="client", name="work"):
    return dict(label=label, expression=expression, expected=expected,
                declared_type=declared, dynamic_type=dynamic, binding=name, scope=scope)


def setup_fields(types, variable, typename):
    result = {}
    route = variable
    for owner in ancestry(types, typename):
        for field, value in types[owner]["fields"].items():
            result[route + "%" + field] = value
        parent = types[owner]["parent"]
        if parent is not None:
            route += "%" + parent
    return result


def function_source(types, owner, item):
    name = item["target"]
    result = f"integer function {name}({'self' if item['passed'] else ''}) result(value)\n"
    if item["passed"]:
        result += f"class({owner}), intent(in) :: self\n"
        for index, (field, value) in enumerate(inherited_fields(types, owner).items(), 101):
            result += f"if (self%{field} /= {value}) error stop {index}\n"
    result += f"value={item['result']}\nend function {name}\n"
    return result


def module_source(types, helper_type):
    modules = list(dict.fromkeys(t["module"] for t in types.values()))
    result = ""
    for module in modules:
        members = [t for t in types.values() if t["module"] == module]
        result += f"module {module}\n"
        imports = {}
        for t in members:
            parent = t["parent"]
            if parent is not None and types[parent]["module"] != module:
                imports.setdefault(types[parent]["module"], []).append(parent)
        for provider, names in imports.items():
            result += f"use {provider}, only: " + ", ".join(names) + "\n"
        result += "implicit none\nprivate\n"
        owns_helper = types[helper_type]["module"] == module
        if owns_helper:
            result += "public :: dispatch\n"
        for t in members:
            result += "type, public" + (f", extends({t['parent']})" if t["parent"] else "")
            result += " :: " + t["name"] + "\n"
            for field in t["fields"]:
                result += f"integer :: {field}\n"
            if t["bindings"]:
                result += "contains\n"
                for item in t["bindings"]:
                    result += f"procedure, {item['access']}" + ("" if item["passed"] else ", nopass")
                    result += f" :: {item['name']} => {item['target']}\n"
            result += f"end type {t['name']}\n"
        result += "contains\n"
        for t in members:
            for item in t["bindings"]:
                result += function_source(types, t["name"], item)
        if owns_helper:
            result += (
                f"integer function dispatch(self) result(value)\n"
                f"class({helper_type}), intent(in) :: self\n"
                "value=self%work()\nend function dispatch\n")
        result += f"end module {module}\n"
    return result


def program_source(spec):
    types = spec["types"]
    imports = {}
    for typename in dict.fromkeys(spec["variables"].values()):
        imports.setdefault(types[typename]["module"], []).append(typename)
    imports.setdefault(types[spec["helper_type"]]["module"], []).append("dispatch")
    result = "program p\n"
    for module, names in imports.items():
        result += f"use {module}, only: " + ", ".join(names) + "\n"
    result += "implicit none\n"
    for variable, typename in spec["variables"].items():
        result += f"type({typename}) :: {variable}\n"
    for target, value in spec["setup"].items():
        result += f"{target}={value}\n"
    for observation in spec["observations"]:
        result += (f"call expect_value('{observation['label']}',"
                   f"{observation['expression']},{observation['expected']})\n")
    return result + "contains\n" + OBSERVER + "end program p\n"


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="type_overriding", root=root)

    def add(self, rule, variant, facets, types, variables, helper_type, observations, relations, premises):
        name = identifier(rule, variant)
        folder = "tests/fixtures/type_overriding_" + name.lower()
        type_map = {t["name"]: t for t in types}
        if len(type_map) != len(types):
            raise ValueError("duplicate finite type name")
        setup = {}
        for variable, typename in variables.items():
            setup.update(setup_fields(type_map, variable, typename))
        spec = dict(rule=rule, facets=facets, kind="valid", phase="run", evidence="effect",
                    path=folder + "/fixture.json", types=type_map, variables=variables,
                    helper_type=helper_type, setup=setup, observations=observations,
                    relations=relations, premises=premises)
        if not observations or len({o["label"] for o in observations}) != len(observations):
            raise ValueError("observations must be nonempty and uniquely labelled")
        if not accepts(spec, model_observations(spec)):
            raise ValueError("literal oracle disagrees with the finite binding graph")
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=facets, standard="f2023", evidence="effect",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0))
        self.put(folder + "/source.f90", module_source(type_map, helper_type) + program_source(spec))
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = spec


def ordinary_cases(c):
    rule = "S7.5.7.3-001"
    c.add(rule, "same_binding", ELIGIBLE[rule][:2], [
        derived("parent", fields={"parent_token": 17}, bindings=[binding("parent_work", 11)]),
        derived("child", "parent", {"child_token": 29}, [binding("child_work", 22)]),
    ], {"base": "parent", "extended": "child"}, "parent", [
        call("parent-direct", "base%work()", 11, "parent", "parent"),
        call("parent-helper", "dispatch(base)", 11, "parent", "parent", "overriding_provider"),
        call("child-helper", "dispatch(extended)", 22, "parent", "child", "overriding_provider"),
        call("explicit-parent", "extended%parent%work()", 11, "parent", "parent"),
        call("child-direct", "extended%work()", 22, "child", "child"),
    ], ["parent.work -> child.work: override; distinct module procedure targets",
        "extended%parent: nonpolymorphic, nonabstract parent view, not child dynamic dispatch"],
        "One program represents both same-binding/different-target dispatch and its explicit parent-component contrast. "
        "Independent named parent/child tokens are checked by the selected functions; each result has a literal oracle.")
    c.add(rule, "different_binding", ["different-binding-name"], [
        derived("parent", fields={"parent_token": 17}, bindings=[binding("parent_work", 11)]),
        derived("child", "parent", {"child_token": 29}, [binding("child_extra", 33, name="extra")]),
    ], {"base": "parent", "extended": "child"}, "parent", [
        call("parent-direct", "base%work()", 11, "parent", "parent"),
        call("inherited-direct", "extended%work()", 11, "child", "child"),
        call("inherited-helper", "dispatch(extended)", 11, "parent", "child", "overriding_provider"),
        call("extra-direct", "extended%extra()", 33, "child", "child", name="extra"),
    ], ["parent.work -> child.work: inheritance", "child.extra is a distinct binding, not an override of work"],
        "The extra binding has a valid child self interface but a different binding name. "
        "Both inherited work and extra are independently checked; no generic binding or union is used.")


def private_cases(c):
    rule = "S7.5.7.3-001"
    c.add(rule, "private_homonym", ["inaccessible-private-homonym"], [
        derived("parent", fields={"parent_token": 17},
                bindings=[binding("parent_work", 7, access="private")]),
        derived("child", "parent", bindings=[binding("foreign_work", 9, passed=False)],
                module="unrelated_extension"),
    ], {"base": "parent", "extended": "child"}, "parent", [
        call("private-parent-helper", "dispatch(base)", 7, "parent", "parent", "overriding_provider"),
        call("private-child-helper", "dispatch(extended)", 7, "parent", "child", "overriding_provider"),
        call("public-homonym", "extended%work()", 9, "child", "child"),
    ], ["parent.work remains inherited and private; unrelated child.work has a distinct identity",
        "provider CLASS(parent) lookup retains parent.work; child PUBLIC NOPASS lookup selects foreign_work"],
        "Only the provider helper names the private parent binding. The child is defined in an unrelated module, "
        "not a descendant module. Its PUBLIC NOPASS work has no passed-object parity obligation with the inaccessible binding.")
    c.add(rule, "accessible_private", ["accessible-private-parent"], [
        derived("parent", fields={"parent_token": 17},
                bindings=[binding("parent_work", 11, access="private")]),
        derived("child", "parent", {"child_token": 29}, [binding("child_work", 22)]),
    ], {"base": "parent", "extended": "child"}, "parent", [
        call("private-parent-helper", "dispatch(base)", 11, "parent", "parent", "overriding_provider"),
        call("overridden-child-helper", "dispatch(extended)", 22, "parent", "child", "overriding_provider"),
        call("public-child", "extended%work()", 22, "child", "child"),
    ], ["same-module accessible parent.work -> PUBLIC child.work: actual override"],
        "Parent and child are defined in the same provider module, so the private parent binding is accessible "
        "at the child definition. Both interfaces have scalar CLASS self at position one; PRIVATE-to-PUBLIC is permitted.")


def correspondence_cases(c):
    rule = "S7.5.7.3-011"
    c.add(rule, "override_then_inherit", ["override-then-inherit"], [
        derived("root", fields={"root_token": 17}, bindings=[binding("root_work", 11)]),
        derived("child", "root", {"child_token": 29}, [binding("child_work", 22)]),
        derived("grand", "child"),
    ], {"original": "root", "last": "grand"}, "root", [
        call("root-direct", "original%work()", 11, "root", "root"),
        call("root-helper", "dispatch(original)", 11, "root", "root", "overriding_provider"),
        call("grand-helper", "dispatch(last)", 22, "root", "grand", "overriding_provider"),
        call("grand-direct", "last%work()", 22, "grand", "grand"),
    ], ["root.work -> child.work: override", "child.work -> grand.work: inheritance",
        "root.work corresponds through both generations without equal-target identity inference"],
        "The grandchild adds no binding. Its root and child primitive fields are independently defined through "
        "named ancestor components; the inherited child implementation checks both before returning22.")
    c.add(rule, "inherit_then_override", ["inherit-then-override"], [
        derived("root", fields={"root_token": 17}, bindings=[binding("root_work", 11)]),
        derived("middle", "root"),
        derived("leaf", "middle", {"leaf_token": 41}, [binding("leaf_work", 33)]),
    ], {"original": "root", "last": "leaf"}, "root", [
        call("root-direct", "original%work()", 11, "root", "root"),
        call("root-helper", "dispatch(original)", 11, "root", "root", "overriding_provider"),
        call("leaf-helper", "dispatch(last)", 33, "root", "leaf", "overriding_provider"),
        call("explicit-middle", "last%middle%work()", 11, "middle", "middle"),
        call("leaf-direct", "last%work()", 33, "leaf", "leaf"),
    ], ["root.work -> middle.work: inheritance", "middle.work -> leaf.work: override",
        "last%middle has middle dynamic type and its inherited root implementation"],
        "The leaf overrides work inherited through an unchanged middle. Whole middle is nonabstract, so its explicit "
        "component selector is valid and yields11 rather than the leaf's33. No parameter-comparison question is instantiated.")


def build_corpus(root=ROOT):
    corpus = Corpus(root)
    ordinary_cases(corpus)
    private_cases(corpus)
    correspondence_cases(corpus)
    if corpus.coverage() != {rule: set(facets) for rule, facets in ELIGIBLE.items()}:
        raise ValueError("finite runtime coverage differs from the authorized seven facets")
    return corpus.files, corpus.cases


def synced_catalogue(catalogue, specs):
    result = json.loads(json.dumps(catalogue))
    for requirement in result["requirements"]:
        cases = [s for s in specs.values() if s["rule"] == requirement["id"]]
        represented = {facet for case in cases for facet in case["facets"]}
        if represented - set(requirement["facets"]):
            raise ValueError("unknown represented facet: " + requirement["id"])
        for facet in represented:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - represented:
            raise ValueError("missing preserved pending plan: " + requirement["id"])
        if cases:
            original = requirement["oracle"].split("\n\nFinite runtime implementation:", 1)[0]
            requirement["oracle"] = original + (
                f"\n\nFinite runtime implementation: {len(cases)} run-phase effect cases represent "
                f"{len(represented)} facets using ordinary nonparameterized, nonabstract types. "
                "Primitive setup uses named components; every selected implementation verifies its defined "
                "receiver fields before returning an independent integer literal. Both dynamic and required "
                "explicit ancestor-view results are checked. All other facet plans remain pending. "
                "Separate content-bound source/case/evidence adjudications, not authorship or compiler outcomes, "
                "determine approval.")
    return result


CONDITIONS = """## Source and concrete premises

Authority is J3/24-007, 18 December 2023, 688 physical PDF pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The section starts on PDF105 and includes the informative NOTE continuation on
PDF106 through `END FUNCTION POINT_3D_LENGTH`, before the actual 7.5.8 heading.
The two note fragments remain separate census units of one informative example.
There are five original units, 45 fine units and 50 reciprocal accounting rows.

All receivers are live ordinary nonparameterized, nonabstract scalar objects.
Parent types are previously defined, public and extensible, without SEQUENCE,
BIND(C), DEFERRED, NON_OVERRIDABLE, coarrays, pointers or allocatables. Components
are public primitive integers, independently initialized by name, including
explicit ancestor-component paths. Selected procedures read only defined current
`self` fields; each scalar default-integer result is assigned before return.
There is no whole-object or constructor setup and no storage/ABI/identity inquiry.

Every actual overriding pair uses one dummy named `self` at position one,
`CLASS(the_type_being_defined), INTENT(IN)`, scalar, nonpointer, nonallocatable and
without VALUE. Only the permitted declared-type characteristic changes.
There are no KIND/LEN parameters or other dummy arguments. Both functions have
the same scalar default-integer result characteristics; neither is PURE, SIMPLE
or ELEMENTAL. Public parents remain public when overridden. The accessible
private-parent case deliberately permits a PUBLIC child override in the same
module. An unrelated module's private homonym is a distinct binding, so its
explicit NOPASS is not an overriding-interface mismatch.

The CLASS(parent/root) helpers reference the ordinary named binding `work`.
Original 7.3.2.3/7.3.3 (PDF79), 7.5.4.5/C765 (PDF96), 7.5.5 (PDF99-101),
7.5.7.2 (PDF104), 15.3 (PDF324), 15.5.1/.2/.6 (PDF335/337-340/352),
19.3.4 (PDF550), 19.5.4/.5 (PDF561) and 19.6.1/.5 (PDF562-563) establish the
type, accessibility, correspondence, dispatch, definition and lifetime premises.
An explicit nonpolymorphic parent/middle component has that component's dynamic
type (7.3.2.3 and 9.4.2, PDF79/151-152). These are semantic selector results,
not requirements about virtual tables, machine calls, addresses or layout.

Only S7.5.7.3-001 and S7.5.7.3-011 runtime facets are represented. No generic
lookup or interface-union program is cloned from 7.5.7.1/.2. Parent/PASS,
characteristic and reference rules are prerequisites, not separately credited
admission or reuse facets. C789/C790 keep their canonical owners and inputs.
Every unnumbered restriction retains its original not-required diagnostic duty;
no optional diagnostic policy, negative fixture or mandatory fatal/code claim
is introduced.

`7.5.7.3#p2.b07-additional-parameter-domain` remains explicitly unresolved.
The additional passed-object KIND/LEN comparison, all admission/policy contrasts,
and source-use graphs remain pending. Finite Python binding-identity models are
regression countermodels, not executable language inquiries or graph-coverage
evidence. Compiler failures do not change a runtime effect into a compile case.
"""


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    total = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    count = sum(len(s["observations"]) for s in specs.values())
    result = (
        "# Fortran 2023: 7.5.7.3 Type-bound procedure overriding - runtime implementation\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Source eligibility is not fixture approval; current adjudications are separate content-bound records.\n\n"
        f"The finite packet contains **{len(specs)} run-phase effect cases**, **{count} literal-result observations**, "
        f"and **{total-pending} represented facets out of {total}**. **{pending} facets remain PENDING**. "
        "Representation is not a claim of processor success, approval or whole-source closure.\n\n"
        + CONDITIONS + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.5.7.3 -->\n\n")
    result += "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    result += "<!-- END GENERATED 7.5.7.3 -->\n\n## Exact finite runtime observations\n\n"
    for name, spec in specs.items():
        result += f"### `{name}`\n\n**Primary:** {spec['rule']}; **phase/evidence:** run / effect. "
        result += "**Facets:** " + ", ".join("`" + f + "`" for f in spec["facets"]) + ".\n\n"
        result += spec["premises"] + "\n\n"
        for relation in spec["relations"]:
            result += "* " + relation + ".\n"
        result += "\n| Observation | Expression | Expected literal |\n| --- | --- | ---: |\n"
        for observation in spec["observations"]:
            result += f"| {observation['label']} | `{observation['expression']}` | {observation['expected']} |\n"
        result += "\n"
    result += "## Complete finite pending plans\n\n"
    result += ("All entries below remain PENDING exactly as recorded in canonical JSON. "
               "No finite program, compiler observation or Python truth model clears these gates.\n\n")
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            result += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                result += f"* **`{facet}`** - {plan}\n"
            result += "\n"
    return result + (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_type_overriding_fixtures.py --check` verifies the exact "
        "generated inputs, canonical pending metadata and both Markdown regions. "
        "`tests/test_type_overriding_fixtures.py` checks independent identity/ancestry/dispatch "
        "truth tables, wrong-selection countermodels, actual literal guards and complete "
        "defined-receiver setup. Shared parameter helper inputs are unchanged.\n\n"
        "The independent source and fixture review is recorded in "
        "`doc/source_audits/batch_018.json`; current approvals remain separate content-bound records. "
        "Five cases have qualifying GNU f2023 observations. The private-binding homonym "
        "retains its source-only adjudication and literal 7/7/9 oracle despite GNU and "
        "LFortran compilation failures; Flang's actual f2018 run is supplementary only. "
        "Observations retain exact selected IDs, current fingerprints, complete commands and "
        "actual reference modes. Unsupported facilities, crashes or unrelated diagnostics do "
        "not corroborate runtime behavior. All 50 pending facets and the additional-parameter "
        "source question remain open; no optional rejection policy or new canonical link is adopted.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    outputs, specs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs)
    if args.check:
        bad = [str(p.relative_to(ROOT)) for p, data in outputs.items()
               if not p.is_file() or p.read_bytes() != data]
        actual = {p for p in (ROOT / "tests/fixtures").glob("type_overriding_*/*") if p.is_file()}
        bad += [str(p.relative_to(ROOT)) for p in actual - set(outputs)]
        if catalogue != updated:
            bad.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            bad.append(VIEW)
        if bad:
            raise SystemExit("stale type-overriding packet: " + ", ".join(sorted(bad)))
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files for "
          f"{len(specs)} overriding run cases and 7 represented facets.")


if __name__ == "__main__":
    main()
