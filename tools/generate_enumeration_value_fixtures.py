#!/usr/bin/env python3
"""Generate only the eight ordinary ENUMERATION TYPE runtime facets."""
import argparse
import copy
from dataclasses import dataclass
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.6.2"
CATALOGUE = "doc/catalogues/enumeration_type_7_6_2.json"
VIEW = "doc/fortran_2023_7_6_2.md"
ELIGIBLE = {
    "S7.6.2-001": ["public-header-defaults", "enumerator-confirmation-and-override"],
    "S7.6.2-002": ["ordered-three-member-values", "across-enumerator-statements", "single-member-and-last-context"],
    "S7.6.2-003": ["first-interior-last-values", "dynamic-integer-position", "constant-and-scalar-result-contexts"],
}
CHECKS = """module enumeration_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, finish_checks
contains
subroutine check_integer(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'ORDINAL',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(*), intent(in) :: label
logical, intent(in) :: actual,expected
if (actual .neqv. expected) then
print *, 'RELATION',label,'ACTUAL',actual,'EXPECTED',expected
error stop 2
end if
checked=checked+1
end subroutine check_logical
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked/=expected) then
print *, 'CHECK_COUNT',checked,'EXPECTED',expected
error stop 3
end if
end subroutine finish_checks
end module enumeration_checks
"""


@dataclass(frozen=True)
class EnumerationValue:
    type_id: str
    member: str


def members(definition):
    result = [name for group in definition["groups"] for name in group]
    if not result or len(result) != len({name.lower() for name in result}):
        raise ValueError("an enumeration needs unique nonempty member names")
    return result


def enumeration_value(definition, name):
    if name not in members(definition):
        raise ValueError("unknown enumeration member")
    return EnumerationValue(definition["module"] + "::" + definition["name"], name)


def ordinal(definition, value):
    if not isinstance(value, EnumerationValue):
        raise TypeError("an enumeration value is not an INTEGER substitute")
    if value.type_id != definition["module"] + "::" + definition["name"]:
        raise TypeError("different enumeration types cannot be compared as identical")
    return members(definition).index(value.member) + 1


def construct(definition, index):
    if type(index) is not int:
        raise TypeError("constructor index must be scalar INTEGER")
    names = members(definition)
    if not 1 <= index <= len(names):
        raise ValueError("constructor index is outside this finite type")
    return enumeration_value(definition, names[index - 1])


def last_value(definition, value):
    ordinal(definition, value)
    return enumeration_value(definition, members(definition)[-1])


def same_value(definition, left, right):
    ordinal(definition, left)
    ordinal(definition, right)
    return left == right


def accessibility(definitions, module_default, statements):
    result = {}
    explicit = set()
    for definition in definitions:
        default = definition["access"] or module_default
        if definition["name"] in result:
            raise ValueError("duplicate type name")
        result[definition["name"]] = default
        if definition["access"]:
            explicit.add(definition["name"])
        for name in members(definition):
            if name in result:
                raise ValueError("duplicate identifier in one module scope")
            result[name] = default
    for name, access in statements:
        if name not in result or access not in ("public", "private"):
            raise ValueError("invalid explicit accessibility")
        if name in explicit:
            raise ValueError("duplicate explicit accessibility for " + name)
        explicit.add(name)
        result[name] = access
    return result


def definition(module, name, groups, access=None):
    return dict(module=module, name=name, groups=groups, access=access)


def declaration(item):
    prefix = ", " + item["access"] if item["access"] else ""
    lines = [f"enumeration type{prefix} :: {item['name']}"]
    for group in item["groups"]:
        lines.append("enumerator :: " + ", ".join(group))
    return "\n".join(lines + [f"end enumeration type {item['name']}"]) + "\n"


def observation(label, expression, expected):
    return dict(label=label, expression=expression, expected=expected,
                category="logical" if type(expected) is bool else "integer")


def observation_code(item):
    expected = (".true." if item["expected"] else ".false.") if item["category"] == "logical" else str(item["expected"])
    return f"call check_{item['category']}('{item['label']}',{item['expression']},{expected})\n"


def accepts(expected, observed):
    wanted = {item["label"]: item["expected"] for item in expected}
    return set(wanted) == set(observed) and all(
        type(observed[label]) is type(value) and observed[label] == value for label, value in wanted.items())


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__enumeration_value_" + variant


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="enumeration_value", root=root)

    def add(self, rule, variant, inputs, definitions, observations, premises, **details):
        name = identifier(rule, variant)
        if name in self.cases or not observations or len({o["label"] for o in observations}) != len(observations):
            raise ValueError("case/observer labels must be unique and observations nonempty")
        folder = "tests/fixtures/enumeration_value_" + name.lower()
        steps = []
        for filename, text in inputs.items():
            step = Path(filename).stem
            self.put(folder + "/" + filename, text)
            steps.append(dict(id=step, source=filename, language="fortran", form="free",
                              output=step + ".o", depends_on=[s["id"] for s in steps]))
        manifest = dict(schema_version=1, id=name, rule=rule, facets=ELIGIBLE[rule], evidence="effect",
                        standard="f2023", files=list(inputs), build=steps,
                        link=dict(objects=[s["output"] for s in steps], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0))
        path = folder + "/fixture.json"
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, facets=list(ELIGIBLE[rule]), kind="valid", phase="run",
                                evidence="effect", path=path, definitions=definitions, observations=observations,
                                expected_check_count=len(observations), premises=premises, **details)


def access_case(c):
    definitions = [
        definition("enumeration_provider", "public_kind", [["zebra_default", "apple_default"]], "public"),
        definition("enumeration_provider", "confirmed_kind",
                   [["zebra_confirmed", "apple_visible", "mango_private"]], "public"),
        definition("enumeration_provider", "hidden_kind",
                   [["hidden_zebra", "exposed_apple", "hidden_mango"]], "private"),
    ]
    statements = [("zebra_confirmed", "public"), ("mango_private", "private"), ("exposed_apple", "public")]
    access = accessibility(definitions, "private", statements)
    imports = ["public_kind", "zebra_default", "apple_default", "zebra_confirmed", "apple_visible", "exposed_apple"]
    if any(access[name] != "public" for name in imports):
        raise ValueError("client imports a nonpublic identifier")
    provider = "module enumeration_provider\nimplicit none\nprivate\n"
    provider += "".join(declaration(item) for item in definitions)
    provider += "".join(f"{access} :: {name}\n" for name, access in statements)
    provider += "end module enumeration_provider\n"
    observations = [
        observation("public-first", "int(zebra_default)", 1),
        observation("public-second", "int(apple_default)", 2),
        observation("confirmed-first", "int(zebra_confirmed)", 1),
        observation("unmodified-second", "int(apple_visible)", 2),
        observation("private-type-export", "int(exposed_apple)", 2),
        observation("public-type-value", "public_value==apple_default", True),
        observation("public-type-ordinal", "int(public_value)", 2),
    ]
    client = CHECKS + """program p
use enumeration_provider, only: public_kind, zebra_default, apple_default, &
    zebra_confirmed, apple_visible, exposed_apple
use enumeration_checks, only: check_integer, check_logical, finish_checks
implicit none
type(public_kind) :: public_value
public_value=apple_default
"""
    client += "".join(observation_code(o) for o in observations)
    client += "call finish_checks(7)\nend program p\n"
    c.add("S7.6.2-001", "access", {"provider.f90": provider, "client.f90": client},
          definitions, observations,
          "A default-PRIVATE module exports a PUBLIC-header type and untouched default-public constants. "
          "A different PUBLIC-header type confirms one constant and makes another PRIVATE. "
          "A PRIVATE-header type exports one constant, consumed only by INT in the client without naming its type. "
          "Allowed exported uses are the effect; no private-name rejection is claimed.",
          module_default="private", explicit_access=statements, client_imports=imports,
          variables={"public_value": "enumeration_provider::public_kind"},
          setup=["public_value=apple_default"])


def order_case(c):
    definitions = [
        definition("enumeration_list", "list_kind", [["zephyr", "amber", "maple"]]),
        definition("enumeration_split", "split_kind", [["walrus"], ["banana", "quail"]]),
        definition("enumeration_single", "single_kind", [["only_value"]]),
    ]
    source = CHECKS
    for item in definitions:
        source += f"module {item['module']}\nimplicit none\n" + declaration(item)
        source += f"end module {item['module']}\n"
    observations = [
        observation("list-first", "int(zephyr)", 1),
        observation("list-second", "int(amber)", 2),
        observation("list-third", "int(maple)", 3),
        observation("split-first", "int(walrus)", 1),
        observation("split-second", "int(banana)", 2),
        observation("split-third", "int(quail)", 3),
        observation("list-order", "zephyr<amber .and. amber<maple", True),
        observation("list-reverse", "maple<zephyr", False),
        observation("split-order", "walrus<banana .and. banana<quail", True),
        observation("split-reverse", "quail<walrus", False),
        observation("single-ordinal", "int(only_value)", 1),
        observation("single-huge-value", "huge(only_value)==only_value", True),
        observation("single-huge-ordinal", "int(huge(only_value))", 1),
        observation("list-last-value", "huge(zephyr)==maple", True),
        observation("list-last-ordinal", "int(huge(zephyr))", 3),
    ]
    source += """program p
use enumeration_list, only: zephyr, amber, maple
use enumeration_split, only: walrus, banana, quail
use enumeration_single, only: only_value
use enumeration_checks, only: check_integer, check_logical, finish_checks
implicit none
"""
    source += "".join(observation_code(o) for o in observations)
    source += "call finish_checks(15)\nend program p\n"
    c.add("S7.6.2-002", "order", {"source.f90": source}, definitions, observations,
          "Fresh names in three separate module scopes establish nonalphabetic declaration order. "
          "The split variant preserves the first/second/third roles across two ENUMERATOR statements. "
          "All relation operands belong to the same enumeration type. HUGE consumes known-defined enumeration constants "
          "and returns the last value, including the one-member ordinal1 case. There is no NEXT/PREVIOUS call.",
          order_roles={"list_kind": ["zephyr", "amber", "maple"],
                       "split_kind": ["walrus", "banana", "quail"],
                       "single_kind": ["only_value"]},
          variables={}, setup=[])


def construction_case(c):
    item = definition("enumeration_construction", "selection_kind", [["zulu_pick", "alpha_pick", "mango_pick"]])
    source = CHECKS + "module enumeration_construction\n"
    source += "use enumeration_checks, only: check_integer, check_logical\nimplicit none\n"
    source += declaration(item)
    source += """type(selection_kind), parameter :: fixed_middle=selection_kind(2)
contains
subroutine observe_selection(label,actual,expected,expected_ordinal)
character(*), intent(in) :: label
type(selection_kind), intent(in) :: actual,expected
integer, intent(in) :: expected_ordinal
call check_logical(label//':member',actual==expected,.true.)
call check_integer(label//':ordinal',int(actual),expected_ordinal)
end subroutine observe_selection
end module enumeration_construction
program p
use enumeration_construction, only: selection_kind, zulu_pick, alpha_pick, mango_pick, &
    fixed_middle, observe_selection
use enumeration_checks, only: finish_checks
implicit none
type(selection_kind) :: value
integer :: index
"""
    stages = [
        dict(label="first", setup=["value=selection_kind(1)"], actual="value",
             expected_member="zulu_pick", expected_ordinal=1, index=1, origin="literal"),
        dict(label="interior", setup=["value=selection_kind(2)"], actual="value",
             expected_member="alpha_pick", expected_ordinal=2, index=2, origin="literal"),
        dict(label="last", setup=["value=selection_kind(3)"], actual="value",
             expected_member="mango_pick", expected_ordinal=3, index=3, origin="literal"),
        dict(label="dynamic-second", setup=["index=2", "value=selection_kind(index)"], actual="value",
             expected_member="alpha_pick", expected_ordinal=2, index=2, origin="variable"),
        dict(label="dynamic-third", setup=["index=3", "value=selection_kind(index)"], actual="value",
             expected_member="mango_pick", expected_ordinal=3, index=3, origin="variable"),
        dict(label="constant", setup=[], actual="fixed_middle",
             expected_member="alpha_pick", expected_ordinal=2, index=2, origin="parameter"),
        dict(label="scalar-result", setup=["index=2"], actual="selection_kind(index)",
             expected_member="alpha_pick", expected_ordinal=2, index=2, origin="scalar-expression"),
    ]
    observations = []
    for stage in stages:
        if construct(item, stage["index"]) != enumeration_value(item, stage["expected_member"]):
            raise ValueError("independent named member does not match the source constructor position")
        source += "".join(line + "\n" for line in stage["setup"])
        source += (f"call observe_selection('{stage['label']}',{stage['actual']},"
                   f"{stage['expected_member']},{stage['expected_ordinal']})\n")
        observations += [
            observation(stage["label"] + ":member", stage["actual"] + "==" + stage["expected_member"], True),
            observation(stage["label"] + ":ordinal", "int(" + stage["actual"] + ")", stage["expected_ordinal"]),
        ]
    source += "call finish_checks(14)\nend program p\n"
    c.add("S7.6.2-003", "construction", {"source.f90": source}, [item], observations,
          "Every constructor input is a defined scalar INTEGER1..3. Named same-type values, not another constructor "
          "or an INT inverse, are the primary oracle; independent INT1/2/3 checks are secondary. "
          "The dynamic index is assigned2 then3 in separate evaluations. A genuine same-type PARAMETER initialized "
          "by selection_kind(2) and a scalar runtime constructor are both consumed through complete TYPE INTENT(IN) dummies. "
          "No S004 range-control or policy facet is claimed.",
          variables={"value": "enumeration_construction::selection_kind", "index": "integer"},
          parameter={"name": "fixed_middle", "type": item["name"], "initializer": "selection_kind(2)"},
          stages=stages, setup=[])


def build_corpus(root=ROOT):
    c = Corpus(root)
    access_case(c)
    order_case(c)
    construction_case(c)
    if c.coverage() != {r: set(facets) for r, facets in ELIGIBLE.items()}:
        raise ValueError("runtime corpus differs from the eight authorized facets")
    return c.files, c.cases


def synced_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    for requirement in result["requirements"]:
        cases = [s for s in specs.values() if s["rule"] == requirement["id"]]
        covered = {f for case in cases for f in case["facets"]}
        for facet in covered:
            if facet not in requirement["facets"]:
                raise ValueError("unknown runtime facet")
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - covered:
            raise ValueError("missing original pending plans for " + requirement["id"])
        if cases:
            old = requirement["oracle"].split("\n\nFinite runtime implementation:", 1)[0]
            requirement["oracle"] = old + (
                f"\n\nFinite runtime implementation: {len(cases)} shared run-phase effect case represents "
                f"{len(covered)} authorized facets with defined same-enumeration values, independent literal ordinal "
                "checks and nonvacuous observer counts. Constructor values are compared to named same-type constants "
                "before secondary INT checks. Compile admission is not a runtime substitute. All other plans remain "
                "pending; source eligibility and compiler observations do not confer case/source/link approval.")
            prefix = "No executable evidence is authored. "
            if requirement["oracle_limitation"].startswith(prefix):
                requirement["oracle_limitation"] = (
                    "Finite runtime inputs and observations do not confer adjudication. "
                    + requirement["oracle_limitation"][len(prefix):])
    return result


CONDITIONS = """## Source and finite qualifications

Authority is J3/24-007, 18 December 2023, 688 physical PDF pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The original7.6.2 spans PDF111-113 and ends before7.7. All16 base units,
54 fine units,70 accounting rows,13 requirements and52 facet IDs are preserved.
The immutable fa1fbf02 source and independent source review establish qualified
eligibility, not fixture approval.

These are ENUMERATION TYPE values: nonintrinsic, nonderived, noninteroperable,
without kind parameters. Enumerators are defined scalar named constants of
their enumeration type. INT returns ordinal positions; HUGE returns a scalar
of the same enumeration type denoting its last enumerator. No INTEGER
enumerator, zero-default ENUM/BIND(C), KIND, byte/representation, C companion,
BOZ, CLASS(enumeration_name), NEXT or PREVIOUS behavior is substituted.

Original access rules (PDF120/134), same-enumeration relations (PDF175/181),
constant constructors (10.1.12p1(5), PDF187-188), same-type intrinsic assignment
(PDF189), PARAMETER (PDF130), scalar dummy association/definedness (PDF340/563),
INT (PDF421-422) and HUGE (PDF416) qualify the actual calls. All type definitions
precede their uses. All explicit header access is in a module specification
part. Each explicit identifier access is supplied once; a member default can
be confirmed without repeating the type name's explicit header access.

The accessibility case contains three distinct definitions in one provider:
untouched PUBLIC-header defaults under module PRIVATE; a separate confirmed
PUBLIC member and PRIVATE override; and a PRIVATE-header type with one
exported constant. The client imports/uses the public type and values, and
consumes the exported private-type constant through INT without naming that
type. Private members' forbidden use is not executed or purportedly proved.
C1409 and the module-default/private-use source graphs remain pending.

The declaration-order case uses nonalphabetic names, fresh split-statement
names in a separate scope, and a separate one-member type. Each INT result
has an independent literal1/2/3 expectation. Same-type relational checks and
HUGE of known-defined constants retain their actual enumeration domains;
different types are never compared as if identical.

The constructor case uses only scalar INTEGER positions1..3, with independent
named first/interior/last values as primary expectations. Dynamic indices are
assigned2 then3 separately. A same-type PARAMETER constructor and a runtime
scalar constructor are actually consumed through explicit scalar TYPE dummies
with INTENT(IN); declarations alone do not establish an effect. Every ordinary
value is assigned before use, and every counter is initialized. Error output
prints only primitive logical/INTEGER observations, not enumeration values by
unsupported list-directed I/O.

All three S7.6.2-004 range/control/policy facets remain pending. Boundary values
already used here may support a later separately reviewed connection, not
another cloned program or automatic range coverage. The original note's
NEXT(last) without STAT error-terminates (ENS-Q02); its equality EXIT loop is
not copied. ENS-Q01/03/04's named-enum, BOZ, companion, representation and
policy qualifications remain outside this corpus. ENS-Q05/06's name/scope,
definedness and evidence-role distinctions are preserved.

Runtime expectations remain run-phase even when a processor fails compilation.
Reference f2018 execution, if any, is not relabelled as f2023 qualification.
Separate observer-sensitivity runs, when supported by a successful reference,
are artifacts rather than conformance cases. No profile, policy, source/case
approval, canonical link or baseline change is authored.
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
    observations = sum(len(s["observations"]) for s in specs.values())
    text = (
        "# Fortran 2023: 7.6.2 Enumeration types - ordinary value implementation\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Current case/evidence adjudications are separate content-bound records.\n\n"
        f"The finite corpus has **{len(specs)} shared run-phase effect cases** and "
        f"**{observations} value/ordinal/relation observations**. **{total-pending} of {total} facets "
        f"are represented; {pending} remain PENDING.** Representation is not approval or source closure.\n\n"
        + CONDITIONS + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.6.2 -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    text += "<!-- END GENERATED 7.6.2 -->\n\n## Exact finite observations\n\n"
    for name, spec in specs.items():
        text += f"### `{name}`\n\n**Primary:** {spec['rule']}; **phase/evidence:** run / effect.\n\n"
        text += "**Facets:** " + ", ".join("`" + f + "`" for f in spec["facets"]) + ".\n\n"
        text += spec["premises"] + "\n\n"
        text += "| Observation | Actual expression/context | Independent expected value |\n| --- | --- | --- |\n"
        for item in spec["observations"]:
            expected = str(item["expected"]).lower()
            text += f"| {item['label']} | `{item['expression']}` | `{expected}` |\n"
        text += f"\nThe final observer count must be `{spec['expected_check_count']}`; an empty or incomplete run cannot pass.\n\n"
    text += "## Complete finite pending plans\n\n"
    text += "Every entry below remains PENDING exactly as in canonical JSON. No boundary observation or source-use capability clears it automatically.\n\n"
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            text += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                text += f"* **`{facet}`** - {plan}\n"
            text += "\n"
    return text + (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_enumeration_value_fixtures.py --check` checks exact generated bytes, "
        "source/phase/pending metadata and both document regions. Targeted regressions use independent "
        "ordinal/type/access/constructor countermodels and inspect actual declarations, index assignments, "
        "typed consumers, primitive observer guards and mandatory counts. The original1907 case bindings "
        "and nine links are protected by the scoped receipt.\n\n"
        "Consult current independent fixture/oracle adjudications before integration. Source eligibility, "
        "compiler agreement and sensitivity tests do not approve cases or links. The author-local index "
        "overlay is excluded; source-context/inventory staleness is reported, not renewed.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, specs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, b in files.items() if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob("enumeration_value_*/*") if p.is_file()}
        stale += [str(p.relative_to(ROOT)) for p in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale enumeration-value packet: " + ", ".join(sorted(stale)))
    else:
        for path, data in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(specs)} enumeration run cases and8 facets.")


if __name__ == "__main__":
    main()
