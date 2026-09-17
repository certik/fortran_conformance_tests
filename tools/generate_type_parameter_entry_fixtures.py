#!/usr/bin/env python3
"""Finite local CHARACTER type-parameter entry-capture runtime witnesses."""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "doc/catalogues/automatic_data_objects_8_3.json"
VIEW = "doc/fortran_2023_8_3.md"
RULE = "S8.3-001"
FACETS = [
    "procedure-selector-snapshot", "procedure-entity-length-snapshot",
    "block-selector-snapshot", "block-entity-length-snapshot",
    "post-undefinition-snapshot", "fresh-entry-captures", "nested-block-snapshots",
]
CHECKERS = """subroutine check_integer(label,actual,expected)
character(len=*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'CHECK_INTEGER',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(len=*), intent(in) :: label
logical, intent(in) :: actual,expected
if (actual .neqv. expected) then
print *, 'CHECK_LOGICAL',label,'ACTUAL',actual,'EXPECTED',expected
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
"""


def identifier(variant):
    return "S8_3_001_valid__type_parameter_entry_" + variant


def literal(value):
    return (".true." if value else ".false.") if type(value) is bool else str(value)


def guard_code(guard):
    return f"call check_{guard['category']}('{guard['label']}',{guard['expression']},{literal(guard['expected'])})\n"


def scenario(name, context, declaration, entry, expected, payload, mutation, restored=None):
    return dict(name=name, context=context, declaration=declaration, source="n",
                entry_value=entry, expected_length=expected, payload=payload,
                source_after_entry=mutation, restored_value=restored,
                state_order=["source-defined-before-entry", "parameter-established-at-entry",
                             "payload-defined-in-body", "source-changed-in-body",
                             "named-local-LEN-and-payload-observed"] +
                            (["source-restored-by-literal-before-use"] if restored is not None else []))


def bind_spans(source, guards, expected_count):
    lines = source.splitlines()
    result = []
    for guard in guards:
        text = guard_code(guard).rstrip("\n")
        if lines.count(text) != 1:
            raise ValueError("every primitive guard must have a unique actual source location")
        value = literal(guard["expected"])
        first = text.rfind("," + value + ")") + 1
        if first < 1:
            raise ValueError("the expected scalar is not isolated at its guard")
        result.append(dict(**guard, line=lines.index(text) + 1, first_column=first + 1,
                           last_column=first + len(value), expected_text=value, source_text=text,
                           failure_marker="CHECK_LOGICAL" if guard["category"] == "logical" else "CHECK_INTEGER"))
    text = f"call finish_checks({expected_count})"
    if lines.count(text) != 1:
        raise ValueError("completion count must be observed exactly once")
    first = text.index("(") + 1
    result.append(dict(
        label="completion-count", expression="checked", expected=expected_count, family="completion-count",
        scope="main", category="integer", line=lines.index(text) + 1,
        first_column=first + 1, last_column=first + len(str(expected_count)),
        expected_text=str(expected_count), source_text=text, failure_marker="CHECK_COUNT"))
    return result


class Program:
    def __init__(self, variant, facets, declarations, initialization, entries):
        self.variant, self.facets = variant, facets
        self.declarations, self.initialization = declarations, initialization
        self.entries = entries
        self.guards = []

    def check(self, label, expression, expected, family, scope):
        item = dict(label=label, expression=expression, expected=expected, family=family,
                    scope=scope, category="logical" if type(expected) is bool else "integer")
        self.guards.append(item)
        return guard_code(item)

    def snapshot(self, prefix, local, expected, payload, scope, after_undefined=False):
        family = "post-undefinition-length" if after_undefined else "captured-length"
        return (self.check(prefix + ":length", f"len({local})", expected, family, scope) +
                self.check(prefix + ":payload", f"{local}=='{payload}'", True, "defined-payload", scope))

    def finish(self, main, procedures, expected_count):
        if len(self.guards) != expected_count or len({g["label"] for g in self.guards}) != expected_count:
            raise ValueError("the independent expected count must include every unique, executed primitive guard")
        source = "program p\nimplicit none\ninteger :: checked\n"
        source += "\n".join(self.declarations) + "\nchecked=0\n"
        source += "\n".join(self.initialization) + "\n" + main
        source += f"call finish_checks({expected_count})\ncontains\n" + procedures + CHECKERS + "end program p\n"
        spans = bind_spans(source, self.guards, expected_count)
        representatives = {}
        for item in spans:
            representatives.setdefault(item["family"], item["label"])
        name = identifier(self.variant)
        folder = "tests/fixtures/type_parameter_entry_" + self.variant
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=self.facets, standard="f2023", evidence="effect",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0))
        spec = dict(
            id=name, variant=self.variant, primary=RULE, facets=self.facets, path=folder + "/fixture.json",
            declarations=self.declarations, initialization=self.initialization, entry_plan=self.entries,
            primitive_guards=self.guards, guard_bindings=spans, expected_check_count=expected_count,
            sensitivity_representatives=representatives,
            length_guard_labels=[g["label"] for g in spans if g["family"] in ("captured-length", "post-undefinition-length")],
            standard="f2023", phase="run", evidence="effect",
            no_declaration_initialization_of_local_characters=True, no_undefined_source_value_observer=True)
        return {folder + "/source.f90": source.encode(),
                folder + "/fixture.json": (json.dumps(manifest, indent=2) + "\n").encode()}, spec


def procedure_program():
    entries = [
        scenario("procedure_selector", "procedure", "character(len=n) :: text", 2, 2, "ab", 5),
        scenario("procedure_entity", "procedure", "character :: text*(n)", 3, 3, "abc", 7),
    ]
    p = Program("procedures", FACETS[:2], ["integer :: n,entries"], ["entries=0"], entries)
    procedures = ""
    for order, entry in enumerate(entries, 1):
        name = entry["name"]
        procedures += f"subroutine {name}(n)\ninteger, intent(inout) :: n\n{entry['declaration']}\nentries=entries+1\n"
        procedures += p.check(name + ":entry", "entries", order, "entry-order", name)
        procedures += f"text='{entry['payload']}'\nn={entry['source_after_entry']}\n"
        procedures += p.check(name + ":source-now", "n", entry["source_after_entry"], "source-redefinition", name)
        procedures += p.snapshot(name, "text", entry["expected_length"], entry["payload"], name)
        procedures += f"end subroutine {name}\n"
    main = "n=2\ncall procedure_selector(n)\nn=3\ncall procedure_entity(n)\n"
    main += p.check("procedures:entries", "entries", 2, "entry-total", "main")
    return p.finish(main, procedures, 9)


def block_program():
    entries = [
        scenario("block_selector", "block", "character(len=n) :: text", 3, 3, "abc", 7),
        scenario("block_entity", "block", "character :: text*(n)", 2, 2, "ab", 5),
    ]
    p = Program("blocks", FACETS[2:4], ["integer :: n,entries"], ["entries=0"], entries)
    main = ""
    for order, entry in enumerate(entries, 1):
        name = entry["name"]
        main += f"n={entry['entry_value']}\n{name}: block\n{entry['declaration']}\nentries=entries+1\n"
        main += p.check(name + ":entry", "entries", order, "entry-order", name)
        main += f"text='{entry['payload']}'\nn={entry['source_after_entry']}\n"
        main += p.check(name + ":source-now", "n", entry["source_after_entry"], "source-redefinition", name)
        main += p.snapshot(name, "text", entry["expected_length"], entry["payload"], name)
        main += f"end block {name}\n"
    main += p.check("blocks:entries", "entries", 2, "entry-total", "main")
    return p.finish(main, "", 9)


def undefinition_program():
    entries = [
        scenario("undefined_procedure", "procedure", "character(len=n) :: text", 3, 3, "abc", "undefined", 5),
        scenario("undefined_block", "block", "character(len=n) :: text", 3, 3, "abc", "undefined", 7),
    ]
    p = Program("post_undefinition", ["post-undefinition-snapshot"],
                ["integer :: n,entries,undefinition_calls"], ["entries=0", "undefinition_calls=0"], entries)
    procedure = "subroutine undefined_procedure(n)\ninteger, intent(inout) :: n\ncharacter(len=n) :: text\nentries=entries+1\n"
    procedure += p.check("undefined_procedure:entry", "entries", 1, "entry-order", "undefined_procedure")
    procedure += "text='abc'\ncall undefine(n)\n"
    procedure += p.snapshot("undefined_procedure", "text", 3, "abc", "undefined_procedure", True)
    procedure += "n=5\n"
    procedure += p.check("undefined_procedure:restored", "n", 5, "restored-source", "undefined_procedure")
    procedure += "end subroutine undefined_procedure\n"
    procedure += (
        "subroutine undefine(x)\ninteger, intent(out) :: x\n"
        "undefinition_calls=undefinition_calls+1\nend subroutine undefine\n")
    main = "n=3\ncall undefined_procedure(n)\nn=3\nundefined_block: block\ncharacter(len=n) :: text\nentries=entries+1\n"
    main += p.check("undefined_block:entry", "entries", 2, "entry-order", "undefined_block")
    main += "text='abc'\ncall undefine(n)\n"
    main += p.snapshot("undefined_block", "text", 3, "abc", "undefined_block", True)
    main += "n=7\n"
    main += p.check("undefined_block:restored", "n", 7, "restored-source", "undefined_block")
    main += "end block undefined_block\n"
    main += p.check("undefined:calls", "undefinition_calls", 2, "undefinition-total", "main")
    main += p.check("undefined:entries", "entries", 2, "entry-total", "main")
    return p.finish(main, procedure, 10)


def fresh_program():
    entries = [
        scenario("fresh_procedure_first", "same-procedure", "character(len=n) :: text", 2, 2, "ab", 7),
        scenario("fresh_procedure_second", "same-procedure", "character(len=n) :: text", 4, 4, "abcd", 7),
        scenario("fresh_block_first", "same-block", "character(len=n) :: text", 3, 3, "abc", 7),
        scenario("fresh_block_second", "same-block", "character(len=n) :: text", 5, 5, "abcde", 7),
    ]
    p = Program("fresh_entries", ["fresh-entry-captures"], ["integer :: n,procedure_entries,block_entries,iteration"],
                ["procedure_entries=0", "block_entries=0"], entries)
    procedure = ("subroutine capture_fresh(n)\ninteger, intent(inout) :: n\ncharacter(len=n) :: text\n"
                 "procedure_entries=procedure_entries+1\nselect case(procedure_entries)\n")
    for order, entry in enumerate(entries[:2], 1):
        name = entry["name"]
        procedure += f"case({order})\n"
        procedure += p.check(name + ":entry", "procedure_entries", order, "entry-order", "capture_fresh")
        procedure += f"text='{entry['payload']}'\nn=7\n"
        procedure += p.check(name + ":source-now", "n", 7, "source-redefinition", "capture_fresh")
        procedure += p.snapshot(name, "text", entry["expected_length"], entry["payload"], "capture_fresh")
    procedure += ("case default\nprint *, 'UNEXPECTED_ENTRY','procedure',procedure_entries\nerror stop 4\n"
                  "end select\nend subroutine capture_fresh\n")
    main = "n=2\ncall capture_fresh(n)\nn=4\ncall capture_fresh(n)\n"
    main += p.check("fresh:procedure-count", "procedure_entries", 2, "entry-total", "main")
    main += ("do iteration=1,2\nif (iteration==1) then\nn=3\nelse\nn=5\nend if\n"
             "reentered: block\ncharacter(len=n) :: text\nblock_entries=block_entries+1\nselect case(block_entries)\n")
    for order, entry in enumerate(entries[2:], 1):
        name = entry["name"]
        main += f"case({order})\n"
        main += p.check(name + ":entry", "block_entries", order, "entry-order", "reentered")
        main += f"text='{entry['payload']}'\nn=7\n"
        main += p.check(name + ":source-now", "n", 7, "source-redefinition", "reentered")
        main += p.snapshot(name, "text", entry["expected_length"], entry["payload"], "reentered")
    main += ("case default\nprint *, 'UNEXPECTED_ENTRY','block',block_entries\nerror stop 4\n"
             "end select\nend block reentered\nend do\n")
    main += p.check("fresh:block-count", "block_entries", 2, "entry-total", "main")
    return p.finish(main, procedure, 18)


def nested_program():
    entries = [
        scenario("nested_outer", "outer-block", "character(len=n) :: outer_text", 3, 3, "abc", 5),
        scenario("nested_inner", "inner-block", "character(len=n) :: inner_text", 5, 5, "abcde", 7),
    ]
    p = Program("nested_blocks", ["nested-block-snapshots"], ["integer :: n,entries"], ["entries=0"], entries)
    main = "n=3\nouter_scope: block\ncharacter(len=n) :: outer_text\nentries=entries+1\n"
    main += p.check("nested_outer:entry", "entries", 1, "entry-order", "outer_scope")
    main += "outer_text='abc'\nn=5\n"
    main += p.check("nested:before-inner-source", "n", 5, "source-redefinition", "outer_scope")
    main += "inner_scope: block\ncharacter(len=n) :: inner_text\nentries=entries+1\n"
    main += p.check("nested_inner:entry", "entries", 2, "entry-order", "inner_scope")
    main += "inner_text='abcde'\nn=7\n"
    main += p.check("nested:inside-source", "n", 7, "source-redefinition", "inner_scope")
    main += p.snapshot("nested_outer", "outer_text", 3, "abc", "inner_scope")
    main += p.snapshot("nested_inner", "inner_text", 5, "abcde", "inner_scope")
    main += "end block inner_scope\n"
    main += p.snapshot("nested_outer_after_inner", "outer_text", 3, "abc", "outer_scope")
    main += "end block outer_scope\n"
    main += p.check("nested:entries", "entries", 2, "entry-total", "main")
    return p.finish(main, "", 11)


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for build in (procedure_program, block_program, undefinition_program, fresh_program, nested_program):
        generated, spec = build()
        if spec["id"] in specs or set(files) & {Path(root) / path for path in generated}:
            raise ValueError("duplicate finite entry-capture case or file")
        specs[spec["id"]] = spec
        files.update({Path(root) / path: content for path, content in generated.items()})
    if sorted(facet for spec in specs.values() for facet in spec["facets"]) != sorted(FACETS):
        raise ValueError("the exact seven-facet ownership partition changed")
    return files, specs


def accepts(guards, observed):
    expected = {guard["label"]: guard["expected"] for guard in guards}
    return set(expected) == set(observed) and all(
        type(observed[label]) is type(value) and observed[label] == value for label, value in expected.items())


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(r for r in result["requirements"] if r["id"] == RULE)
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
        raise ValueError("an unselected source plan has been cleared")
    original = requirement["oracle"].split("\n\nFinite entry-capture implementation:", 1)[0]
    requirement["oracle"] = original + (
        "\n\nFinite entry-capture implementation: five complete valid/effect/run/f2023 programs represent only the "
        "seven authorized procedure/BLOCK/undefinition/fresh/nested facets. Named local ordinary CHARACTER objects "
        "have nonconstant n-dependent selector or parenthesized individual lengths and no declaration initialization. "
        "Executable assignments define payloads after entry; independent literal LEN, payload, source-state and "
        "positive entry/count guards are consumed. The INTENT(OUT) helper leaves only the source integer undefined; "
        "no source value is read until literal restoration. Specification-expression ordering, SAVE retention, "
        "PDT/descriptor/RANK/intrinsic/source-use and other-owner coverage are not added. "
        "Original source-review administrative fields remain unchanged, so their binding may become stale without renewal.")
    return result


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(ROOT)
    registry.catalogues["8.3"] = catalogue
    state = registry.catalogue_review_state("8.3")
    pending = {requirement["id"]: len(requirement["pending"]) for requirement in catalogue["requirements"]}
    text = (
        "# Fortran 2023 8.3: Local type-parameter entry capture\n\n"
        f"**Source review: {state}.** Current fixture/evidence adjudications are separate content-bound records. "
        "This generated subset has five shared valid/effect/run/f2023 programs representing seven S8.3-001 facets. "
        f"{pending['C814']} C814 facets and {pending[RULE]} other S8.3-001 facets remain PENDING. "
        "This packet changes no8.4source, fixture or facet.\n\n"
        "Authority: J3/24-007,18December2023,688physical PDF pages,\n"
        "SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.\n"
        "Original8.3 is on PDF119 between the8.3 and8.4headings. Its3base/19fine/22accounting units, "
        "2requirements and18facet IDs are preserved. The original source review in "
        "`doc/source_audits/batch_027.json` does not automatically adjudicate these new inputs.\n\n"
        "## Exact premises and boundaries\n\n"
        "The local CHARACTER subjects meet3.151.2: they are not dummy arguments, global entities or exported "
        "objects. Their declaring subprogram/BLOCK determines entry. Contained-scope access to the outer "
        "object follows5.4.3.2.2p2; it does not recapture the outer parameter at inner entry. "
        "BLOCK declarations are construct entities under11.1.4/19.4, not host statement entities.\n\n"
        "Under10.1.11p1/p2(2)/(4)/p6, previously declared nonoptional INTEGER INTENT(INOUT) n and the "
        "defined host integer supply restricted, nonconstant value expressions. Executable assignments of2/3/4/5 "
        "do not make n PARAMETER or a constant expression. The individual length uses R723's *(n) parentheses. "
        "All actuals are defined before calls, and INOUT sources remain definable for the OUT helper under15.5.2.5p20. "
        "Internal procedures provide complete explicit interfaces.\n\n"
        "No local character declaration has an initializer, SAVE, POINTER or ALLOCATABLE. Its payload is assigned "
        "only in the body after parameter establishment. LEN16.9.122 inspects the actual named local data object "
        "and is compared with an independent scalar literal. Payload guards follow definition and a separate LEN guard, "
        "so padded comparison alone cannot conceal a wrong length. No RANK, KIND-code, byte/encoding, floating, "
        "descriptor, allocation-status or pointer query is used.\n\n"
        "The source mutation occurs after entry, without assuming left-to-right specification-expression ordering. "
        "11.1.4p3 establishes BLOCK specifications before its body. The OUT helper does not assign or read its "
        "dummy:19.6.6p1(15)(b)/(c) and8.5.10p3 supply the undefinition event. Only the source integer is left undefined; "
        "local payloads stay defined. LEN/payload checks do not reference that integer, which is then restored by "
        "literal assignment before any later use. No poisoning, changed-bit expectation or trap is an oracle.\n\n"
        "Fresh2/4procedure calls use the same procedure, and3/5BLOCK entries use the same syntactic BLOCK in a "
        "two-iteration ordinary DO. Explicit entry ordinals, totals and57primitive checks plus5completion guards "
        "detect missing/extra entries. Counters are ordinary live main-program integers initialized by executable "
        "assignment; their use is not SAVE-retention or specification-function-order coverage. Nested3/5objects "
        "are checked against separate literals while both are alive, after source n becomes7.\n\n"
        "Unsupported compilation or runtime behavior remains a failed run contract, never an admission, skip or "
        "weakened fixed-length declaration. Full-program single-span wrong-oracle probes use only processors that "
        "genuinely execute the current parent; they are empirical observer tests outside inventory, not intrinsic "
        "correctness proof or approval. Actual f2018 observations are not promoted to f2023.\n\n"
        "## Definitions\n\n<!-- BEGIN GENERATED 8.3 -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n<!-- END GENERATED 8.3 -->\n\n"
    text += "## Finite entry and oracle bindings\n\n"
    for name, spec in specs.items():
        text += f"### `{name}`\n\n**Facets:** " + ", ".join("`" + f + "`" for f in spec["facets"]) + ".\n\n"
        for entry in spec["entry_plan"]:
            text += (f"* `{entry['name']}`: {entry['context']}; `{entry['declaration']}`; source entry "
                     f"`{entry['entry_value']}`, later `{entry['source_after_entry']}`; literal LEN "
                     f"`{entry['expected_length']}` and body-defined `{entry['payload']}`")
            if entry["restored_value"] is not None:
                text += f"; source restored to literal `{entry['restored_value']}` before reuse"
            text += ".\n"
        text += f"\nExpected completed primitive guards: `{spec['expected_check_count']}`. Guard spans bind the actual scalar expectations.\n\n"
    text += "## Complete unselected pending plans\n\n"
    for requirement in catalogue["requirements"]:
        text += "### " + requirement["id"] + "\n\n"
        for facet, plan in requirement["pending"].items():
            text += f"* **`{facet}`** - {plan}\n"
        text += "\n"
    return text + (
        "## Validation and remaining gates\n\n"
        "`python3 -B tools/generate_type_parameter_entry_fixtures.py --check` verifies exact files and owned rendering. "
        "Targeted source/definedness/interface/entry-sequence/literal and metadata tests accompany the generator. "
        "The original author packet preserved its1972-case base, nine links and empty SourceUses. "
        "This generator does not renew source, fixture, link or inventory reviews; subsequent coordinator "
        "adjudications are read from their current records. Authorship and representation do not confer "
        "source/fixture/oracle/evidence approval.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, specs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, specs)
    actual = {path for path in (ROOT / "tests/fixtures").glob("type_parameter_entry_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale entry-capture packet: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded entry-capture corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(specs)} runtime cases and7facets.")


if __name__ == "__main__":
    main()
