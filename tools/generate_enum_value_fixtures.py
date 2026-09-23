#!/usr/bin/env python3
"""Finite unnamed ENUM value and definition-local KIND runtime witnesses."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus
from generate_assumed_rank_effect_fixtures import owned_paragraph
from generate_type_inheritance_fixtures import evidence_for_category

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.6.1"
CATALOGUE = "doc/catalogues/enum_type_7_6_1.json"
VIEW = "doc/fortran_2023_7_6_1.md"
PREFIX = "enum_value_"
ELIGIBLE = {
    "S7.6.1-001": ["within-definition-common-kind"],
    "S7.6.1-004": [
        "first-implicit-zero", "explicit-values", "successor-after-explicit",
        "across-statement-boundary", "negative-and-repeated-values", "new-definition-reset",
    ],
}

OBSERVER = """module enum_value_observer
implicit none
private
public :: check_definition
contains
subroutine check_definition(tag,actual,expected,kind_agrees)
integer, intent(in) :: tag,actual(:),expected(:)
logical, intent(in) :: kind_agrees
if (size(actual)/=size(expected)) then
print *, 'ENUM_SIZE_MISMATCH',tag
error stop 101
end if
if (size(actual)==0) then
print *, 'ENUM_EMPTY_OBSERVATION',tag
error stop 102
end if
if (any(actual/=expected)) then
print *, 'ENUM_VALUE_MISMATCH',tag
print *, actual
error stop 104
end if
if (.not.kind_agrees) then
print *, 'ENUM_KIND_MISMATCH',tag
error stop 105
end if
end subroutine check_definition
end module enum_value_observer
"""


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__enum_value_" + variant


def definition(label, tag, names, initializers, partitions, expected):
    if not names or len(names) != len(initializers) or len(names) != len(expected):
        raise ValueError("enum definition and literal oracle lengths differ")
    if sum(partitions) != len(names) or any(n < 1 for n in partitions):
        raise ValueError("enum statement partition is not complete")
    if len(set(names)) != len(names):
        raise ValueError("duplicate enumerator name")
    return dict(label=label, tag=tag, names=names, initializers=initializers,
                partitions=partitions, expected=expected)


def enum_source(group):
    result, start = "enum, bind(c)\n", 0
    for count in group["partitions"]:
        items = [name + (f"={value}" if value is not None else "")
                 for name, value in zip(group["names"][start:start+count],
                                        group["initializers"][start:start+count])]
        result += "enumerator :: " + ",".join(items) + "\n"
        start += count
    return result + "end enum\n"


def array_source(items, width=4):
    chunks = [",".join(items[start:start+width]) for start in range(0, len(items), width)]
    return "[" + ", &\n     ".join(chunks) + "]"


def observation_source(group):
    names = group["names"]
    actual = array_source([f"int({name})" for name in names])
    expected = "[" + ",".join(map(str, group["expected"])) + "]"
    kinds = array_source([f"kind({name})" for name in names])
    return (f"! definition: {group['label']}\ncall check_definition({group['tag']}, &\n"
            f"    {actual}, &\n    {expected}, &\n"
            f"    all({kinds} == kind({names[0]})))\n")


def observer_accepts(actual, kinds, expected):
    return (len(actual) == len(expected) == len(kinds) and len(actual) > 0
            and list(actual) == list(expected) and all(kind == kinds[0] for kind in kinds))


class Corpus(ParameterCorpus):
    def __init__(self, categories, root=ROOT):
        super().__init__(namespace="enum_value", root=root)
        self.categories = categories

    def add(self, rule, variant, groups):
        name = identifier(rule, variant)
        names = [value for group in groups for value in group["names"]]
        if len(set(names)) != len(names):
            raise ValueError("ENUM does not create a separate namespace for its constants")
        if self.categories[rule] != "effect":
            raise ValueError("only the two selected runtime effect requirements are authorized")
        source = (OBSERVER + "program enum_values\n"
                  "use enum_value_observer, only: check_definition\nimplicit none\n"
                  + "".join(enum_source(group) for group in groups)
                  + "".join(observation_source(group) for group in groups)
                  + "end program enum_values\n")
        folder = "tests/fixtures/" + PREFIX + name.lower()
        file = rule.replace(".", "_").replace("-", "_") + ".f90"
        evidence = evidence_for_category(self.categories[rule])
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=ELIGIBLE[rule], standard="f2023",
            evidence=evidence, files=[file],
            build=[dict(id=Path(file).stem, source=file, language="fortran", form="free",
                        output=Path(file).stem + ".o", depends_on=[])],
            link=dict(objects=[Path(file).stem + ".o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0),
        )
        self.put(folder + "/" + file, source)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        bindings = []
        for group in groups:
            block = observation_source(group)
            if source.count(block) != 1:
                raise ValueError("observation is not uniquely bound to its definition")
            start = source.index(block)
            bindings.append(dict(label=group["label"], line=source[:start].count("\n")+1,
                                 end_line=source[:start+len(block)].count("\n"),
                                 sha256=hashlib.sha256(block.encode("ascii")).hexdigest()))
        self.cases[name] = dict(
            rule=rule, facets=list(ELIGIBLE[rule]), phase="run", kind="valid", evidence=evidence,
            path=folder + "/fixture.json", source_file=file, definitions=groups,
            observation_bindings=bindings,
        )


def build_corpus(root=ROOT):
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    categories = {r["id"]: r["category"] for r in catalogue["requirements"]}
    c = Corpus(categories, root)
    c.add("S7.6.1-001", "common_kind", [
        definition("common", 1,
                   ["common_zero", "common_one", "common_four", "common_five", "common_nine", "common_ten"],
                   [None, None, 4, None, 9, None], [3, 3], [0, 1, 4, 5, 9, 10]),
    ])
    groups = []
    for label, tag, partitions in [("flat", 2, [8]), ("split", 3, [3, 5])]:
        groups.append(definition(
            label, tag, [label + "_" + n for n in ["zero", "one", "four", "five", "nine", "ten", "reset", "next"]],
            [None, None, 4, None, 9, None, 4, None], partitions, [0, 1, 4, 5, 9, 10, 4, 5]))
    groups.append(definition("negative", 4,
                             ["negative_start", "negative_next", "negative_four", "negative_repeat", "negative_five"],
                             [-3, None, 4, 4, None], [2, 3], [-3, -2, 4, 4, 5]))
    groups.append(definition("fresh", 5, ["fresh_zero", "fresh_one"], [None, None], [2], [0, 1]))
    c.add("S7.6.1-004", "sequence_matrix", groups)
    if c.coverage() != {r: set(facets) for r, facets in ELIGIBLE.items()} or len(c.cases) != 2:
        raise ValueError("the finite enum corpus must be two programs covering seven facets")
    return c.files, c.cases


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def synced_catalogue(catalogue, specs):
    import generate_enum_type_fixtures as enum_type
    result = copy.deepcopy(catalogue)
    shared_coverage = {rule: set(facets) for rule, facets in enum_type.SELECTED.items()}
    for rule, facets in ELIGIBLE.items():
        shared_coverage.setdefault(rule, set()).update(facets)
    for requirement in result["requirements"]:
        rows = [s for s in specs.values() if s["rule"] == requirement["id"]]
        coverage = {f for row in rows for f in row["facets"]}
        for facet in coverage:
            requirement["pending"].pop(facet, None)
        expected_pending = set(requirement["facets"]) - shared_coverage.get(requirement["id"], set())
        if set(requirement["pending"]) != expected_pending:
            raise ValueError("enum shared pending partition mismatch for " + requirement["id"])
        if not rows:
            continue
        paragraph = (
            f"Finite unnamed-enum implementation: {len(rows)} shared runtime program represents "
            f"{len(coverage)} selected facets. Independent literal vectors are checked separately for "
            "each definition, including flat/split forms, negative/repeated values and fresh-definition "
            "reset where applicable. Every definition compares each INTEGER enumerator's KIND to its "
            "own first member; no cross-definition or numeric KIND-code equality is imposed. Small "
            "value-only INT conversions use the required default INTEGER representation. All other "
            "original plans remain pending; observations do not confer source/case approval.")
        requirement["oracle"] = owned_paragraph(
            requirement["oracle"], "Finite unnamed-enum implementation: ", paragraph)
        requirement["oracle_limitation"] = requirement["oracle_limitation"].replace(
            "No executable evidence is authored. ", "", 1).replace(
            "Future runtime effects must remain runtime on implementation failure.",
            "Runtime effects remain runtime on implementation failure.").replace(
            "No companion profile or C experiment is supplied in this source-only packet.",
            "No companion profile or C experiment is supplied in this bounded runtime packet.")
    return result


DOCUMENT = """## Bounded source gate and preserved ownership

Authority: J3/24-007, **18 December 2023**, **688 physical PDF pages**, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The original source commit is `fa1fbf02ec0ee55dffb543c509aa276f418cc35d`.
Independent `enumerations-source-review.json` has SHA-256
`2cba3b4a7bc9d6371ae4c81829e44eb0617e45ed5fd0ee8d99e2563d761b53e9`.
Original7.6.1 on PDF109-111 and directed INTEGER, PARAMETER, constant-expression,
INT and KIND dependencies were read. No7.6.2 or7.7 body is required or newly owned.

All23 original base units,93 fine units,116 accounting rows,15 requirements and64
facet identities are preserved. Only the seven selected pending/oracle
implementation entries change. Named enum types, ENUMERATION TYPE, BOZ,
representation/C-companion profiles, unsigned extremes, source-use links and
diagnostic policies remain outside this packet.

## Concrete finite effects

The common-kind program uses one unnamed `ENUM,BIND(C)` definition across two
ENUMERATOR statements. Its six INTEGER constants have independent expected
values0/1/4/5/9/10. KIND is queried on these intrinsic INTEGER entities, never
on a nonintrinsic enum object, and every member is compared to this definition's
first member without guessing an identifier or comparing independent definitions.

The shared sequence program has four definitions with fresh names. Flat and
two-statement forms each check `[0,1,4,5,9,10,4,5]` against their own literal
expectation. The later explicit4 after10 resets the following value to5. Neither
definition is used as the other's oracle. A separate `[-3,-2,4,4,5]` definition
checks negative and repeated numerical values, and a fresh `[0,1]` definition
checks reset after the preceding5. Unique names, not distinct numerical values,
are required. Every omitted initializer here produces a defined named constant.

INT only converts these small values to default INTEGER for homogeneous observer
arrays;7.4.3.1p4 guarantees that representation's range is ample. It does not
convert KIND codes or select any extra kind. The KIND results already have
default INTEGER type. Each call supplies a separate definition-local comparison;
no global KIND variable or equality between definitions is used.

The observer checks nonempty matching vector sizes, exact ordered values and
the computed within-definition KIND condition. Expected literals and source
initializer/statement partitions are independently modeled in the regressions.
Runtime wrong-expectation sensitivity probes are session-only and require a
successful reference build before an intended runtime self-check failure; they
are not new language-invalid cases or diagnostic policies.

## Source qualifications and evidence limits

ENS-Q01's12345 illustration, ENS-Q02's NEXT endpoint/error termination,
ENS-Q03's BOZ contexts and ENS-Q04's representation/companion gaps stay out of
this implementation. ENS-Q05 is enforced through fresh constant names and
defined implicit values; ENS-Q06 keeps runtime effects distinct from restriction
controls, definitions, profiles and source-use work.

`S6_3_2_2_005_valid__enum` and all1907 author-base source/manifest/ID/fingerprint
bindings are unchanged. That existing Clause6 spelling case checks explicit1/2;
it is neither copied nor re-owned. Integration separately retains main's later
three metadata renewals and nine current links rather than restoring the older
author context. Source/case/inventory adjudications are separate content-bound
records, not actions performed by this generator.

All cases remain run-phase on implementation failure. Frozen LF411, GNU actual
f2023 and Flang actual f2018 observations retain their original inputs, compiler
identities, ordered compile/link/run traces and source_root. No f2018 observation
is relabelled as f2023 and no compiler consensus supplies an expected value.
"""


def render_view(catalogue, specs):
    enum_type_generator = ROOT / "tools" / "generate_enum_type_fixtures.py"
    if enum_type_generator.is_file():
        import generate_enum_type_fixtures as enum_type
        return enum_type.render_view(catalogue)
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    out = (
        "# Fortran 2023: 7.6.1 Interoperable enumerations and enum types\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Case and evidence adjudications are separate content-bound records.\n\n"
        f"**{len(specs)} runtime effect programs** represent **{64-pending} of64 facets**; "
        f"**{pending} remain pending**. There are no new diagnostic or compile-only cases.\n\n"
        + DOCUMENT + "\n## Preserved source accounting\n\n")
    for row in catalogue["accounting"]:
        out += (f"* `{row['unit']}`: **{row['disposition']}** - "
                + (", ".join(row.get("requirements", [])) or row["rationale"]) + "\n")
    out += ("\n## Definitions\n\n<!-- BEGIN GENERATED 7.6.1 -->\n\n"
            + "\n".join(render_requirement(r) for r in catalogue["requirements"])
            + "\n<!-- END GENERATED 7.6.1 -->\n\n## Shared runtime cases\n\n")
    for name, spec in specs.items():
        out += (f"### `{name}`\n\nPrimary `{spec['rule']}`; run / {spec['evidence']}; facets "
                + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n")
        for group in spec["definitions"]:
            out += (f"* `{group['label']}`: literal values `{group['expected']}`; statement partition "
                    f"`{group['partitions']}`; KIND comparisons are only to `{group['names'][0]}`.\n")
        out += "\n"
    out += ("## Complete finite pending plans\n\n"
            "Every unselected original plan is retained. Incidental checks do not create "
            "source-use/link or extra requirement credit.\n\n")
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            out += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                out += f"* **`{facet}`** - {plan}\n"
            out += "\n"
    out += (
        "## Reproduction and separate gates\n\n"
        "`python3 -B tools/generate_enum_value_fixtures.py --check` verifies exact bytes, "
        "the seven/57 partition and both generated view regions. Source/observer models, "
        "current processor reports and sensitivity records are bound in `enum-values-handoff.json`. "
        "Independent source/oracle/provenance decisions and explicit integration renewals are "
        "recorded in `doc/source_audits/batch_022.json`. Both cases have qualifying GNU f2023 "
        "runtime evidence; actual Flang f2018 remains supplementary. These finite value and "
        "within-definition KIND effects do not qualify any companion/representation or pending facet.\n")
    return out


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
        bad = [str(p.relative_to(ROOT)) for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob(PREFIX + "*/*") if p.is_file()}
        bad += [str(p.relative_to(ROOT)) for p in actual - set(outputs)]
        if catalogue != updated:
            bad.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            bad.append(VIEW)
        if bad:
            raise SystemExit("stale enum-value packet: " + ", ".join(sorted(bad)))
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files, "
          f"{len(specs)} enum-value runs and seven represented facets.")


if __name__ == "__main__":
    main()
