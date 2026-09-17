#!/usr/bin/env python3
"""C815 per-execution reporting contracts and exact cross-statement deletion controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from run_tests import isolated_cases
from suite_data import render_requirement

INVALID = "tests/clause08/C815_invalid.f90"
VALID = "tests/clause08/C815_valid.f90"
SIDECAR = "tests/clause08/C815_invalid.cases.json"
CATALOGUE = "doc/catalogues/attribute_specification_8_5_1.json"
ACCESS_CATALOGUE = "doc/catalogues/accessibility_attribute_8_5_2.json"
VIEW = "doc/fortran_2023_8_5_1.md"
ACCESS_VIEW = "doc/fortran_2023_8_5_2.md"
INVALID_SHA = "1a75480da64388dfd60a50c2170dd4147c8709d2252a07793afcd005aa9b849c"
VALID_BODY_SHA = "1eeac48954c88e528408bb1aa2b9be38dd1326b496d0e8f5d7f5b9dfb5d3bd57"
VALID_HEADER = b"! covers: mixed-single-specification\n"
CASES = {
    "allocatable-stmt": dict(facet="repeat-allocatable", subject="b", marker=7,
                            first="integer, allocatable :: b(:)", second="allocatable :: b",
                            retained="INTEGER deferred-shape b(:) and ALLOCATE(b(2))."),
    "dimension-stmt": dict(facet="repeat-dimension", subject="a", marker=13,
                          first="integer, dimension(3) :: a", second="dimension :: a(3)",
                          retained="INTEGER a(3) and the complete a=1 assignment."),
    "intent-stmt": dict(facet="repeat-intent", subject="x", marker=19,
                       first="integer, intent(in) :: x", second="intent(in) :: x",
                       retained="The original INTEGER dummy x with INTENT(IN), without a body definition."),
    "save-stmt": dict(facet="repeat-save", subject="n", marker=24,
                     first="integer, save :: n = 0", second="save :: n",
                     retained="INTEGER,SAVE n=0 and n=n+1; the first explicit SAVE confirms implied SAVE legitimately."),
    "access-stmt": dict(facet="repeat-public", subject="m", marker=30,
                       first="integer, public :: m = 1", second="public :: m",
                       retained="Initialized module INTEGER,PUBLIC m=1 in the same specification part."),
}
FACETS = [entry["facet"] for entry in CASES.values()] + ["mixed-single-specification"]
CAUSES = {
    "allocatable-stmt": ["Duplicate ALLOCATABLE attribute specified", "ALLOCATABLE attribute was already specified on 'b'"],
    "dimension-stmt": ["Duplicate DIMENSION attribute specified", "The dimensions of 'a' have already been declared"],
    "intent-stmt": ["INTENT (IN) conflicts with INTENT(IN)", "INTENT_IN attribute was already specified on 'x'"],
    "save-stmt": ["Duplicate SAVE attribute specified", "SAVE attribute was already specified on 'n'"],
    "access-stmt": ["ACCESS specification at (1) was already specified",
                    "The accessibility of 'm' has already been specified as PUBLIC"],
}
EXCLUSIONS = [
    "unsupported", "not implemented", "not yet implemented", "unimplemented", "not yet supported", "not supported",
    "has no implicit type", "neither a data pointer nor an allocatable variable",
    "implicit confirmation", "internal error", "internal:", "ASR verify", "out of memory", "recovery",
]
NATIVE_SAMPLES = {
    "allocatable-stmt": {
        "gfortran": ("error", "Duplicate ALLOCATABLE attribute specified at (1)"),
        "flang": ("error", "ALLOCATABLE attribute was already specified on 'b'")},
    "dimension-stmt": {
        "lfortran": ("error", "Duplicate DIMENSION attribute specified"),
        "gfortran": ("error", "Duplicate DIMENSION attribute specified at (1)"),
        "flang": ("error", "The dimensions of 'a' have already been declared")},
    "intent-stmt": {
        "gfortran": ("error", "INTENT (IN) conflicts with INTENT(IN) at (1)"),
        "flang": ("error", "INTENT_IN attribute was already specified on 'x'")},
    "save-stmt": {
        "gfortran": ("error", "Legacy Extension: Duplicate SAVE attribute specified at (1)"),
        "flang": ("warning", "SAVE attribute was already specified on 'n' [-Wredundant-attribute]")},
    "access-stmt": {
        "gfortran": ("error", "ACCESS specification at (1) was already specified"),
        "flang": ("warning", "The accessibility of 'm' has already been specified as PUBLIC [-Wredundant-attribute]")},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def control_id(label):
    return "C815_valid__c815_attribute_" + label.replace("-", "_") + "_control"


def valid_body(root=ROOT):
    raw = (Path(root) / VALID).read_bytes()
    body = raw[len(VALID_HEADER):] if raw.startswith(VALID_HEADER) else raw
    if sha(body) != VALID_BODY_SHA:
        raise ValueError("C815_valid permits only its additive facet header, not body or prior-comment edits")
    return body


def remove_statement(source, label):
    entry = CASES[label]
    lines = source.splitlines(keepends=True)
    first, second = entry["marker"] - 2, entry["marker"] - 1
    if lines[first].strip() != entry["first"] or lines[second].split("!", 1)[0].strip() != entry["second"]:
        raise ValueError("the original first/second attribute relation changed")
    if "{error C815 " + label + "}" not in lines[second]:
        raise ValueError("the original second-statement marker is missing")
    syntax = entry["second"]
    column = lines[second].index(syntax)
    offset = sum(len(line.encode("ascii")) for line in lines[:second]) + column
    removed = syntax.encode("ascii")
    raw = source.encode("ascii")
    repaired = raw[:offset] + raw[offset + len(removed):]
    comment_line = lines[second][:column] + lines[second][column + len(syntax):]
    if repaired != "".join(lines[:second] + [comment_line] + lines[second + 1:]).encode("ascii"):
        raise ValueError("the repair is not exactly one statement-syntax deletion")
    return repaired, dict(
        first_statement_line=first + 1, statement_line=second + 1,
        first_column=column + 1, last_column=column + len(syntax),
        byte_span_zero_based_half_open=[offset, offset + len(removed)],
        deleted=removed.decode("ascii"), original_first_statement=lines[first].rstrip("\n"),
        indentation_preserved=True, comment_and_newline_preserved=True,
        all_other_padding_and_input_bytes_preserved=True)


def build_corpus(root=ROOT):
    root = Path(root)
    if sha((root / INVALID).read_bytes()) != INVALID_SHA:
        raise ValueError("C815_invalid must remain byte-for-byte unchanged")
    isolated = {item[2]: item for item in isolated_cases(str(root / INVALID), "C815")}
    if set(isolated) != set(CASES):
        raise ValueError("the retained five-case C815 execution set changed")
    files, pairs, contracts = {}, {}, {}
    for label, entry in CASES.items():
        line, rule, found, bounds, source = isolated[label]
        if (line, rule, found) != (entry["marker"], "C815", label):
            raise ValueError("the original C815 case marker or ID changed")
        repaired, deletion = remove_statement(source, label)
        directory = "tests/fixtures/c815_attribute_" + label.replace("-", "_")
        manifest = dict(
            schema_version=1, id=control_id(label), rule="C815", facets=[entry["facet"]],
            standard="f2023", evidence="positive-control", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", outcome="success", step="source"))
        files[root / directory / "source.f90"] = repaired
        files[root / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        contracts[label] = dict(
            facets=[entry["facet"]], outcome="diagnose",
            diagnostic=dict(line=line - 1, end_line=line, contains_any=list(CAUSES[label]), excludes_any=list(EXCLUSIONS)))
        pairs[label] = dict(
            **entry, negative_id="C815_invalid:" + label, control_id=control_id(label),
            control_path=directory + "/fixture.json", negative_source=source, repaired_source=repaired.decode(),
            negative_sha256=sha(source.encode()), repaired_sha256=sha(repaired),
            isolated_bounds=list(bounds), repair=deletion, contract=contracts[label],
            old_review_key="C815_invalid", new_review_key="C815_invalid:" + label)
    files[root / SIDECAR] = (json.dumps(dict(schema_version=1, cases=contracts), indent=2) + "\n").encode()
    files[root / VALID] = VALID_HEADER + valid_body(root)
    return files, pairs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(item for item in result["requirements"] if item["id"] == "C815")
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
        raise ValueError("an unselected C815 facet is not pending")
    original = requirement["oracle"].split("\n\nCross-statement implementation:", 1)[0]
    requirement["oracle"] = original + (
        "\n\nCross-statement implementation: five retained isolated complete inputs each have one facet, a first/second-statement "
        "source span and a located attribute/entity-repetition diagnose predicate. Their five compile-only positive controls delete "
        "only the second attribute statement's syntax, preserving its indentation, marker comment, newline and every other byte. "
        "The existing C815_valid body keeps its run/effect role, m=1/get_p()=2 and size3/2/2 observations, with only additive facet metadata. "
        "Retained standard/evidence/profiles remain unchanged; new controls use f2023. Native cause phrases are finite calibration, "
        "not prescribed wording; ordinary zero/nonzero reporting does not require fatal rejection or printed rule codes.")
    requirement["oracle_limitation"] = (
        "Six C815 facets have these explicit fixture roles; six other C815 facets and all other source plans remain pending. "
        "Representation is not approval. The invalid grouped key is retired as history; each negative uses its full-ID key. "
        "C815_valid retains its key and can receive a legitimate content-bound current review. Source, case, link and inventory "
        "adjudications are independent and are preserved by generation. Schema-limited nonfatal warnings remain raw report/noncredit "
        "evidence, not proof of absent reporting capability. Source echoes, bare keywords, wrong attributes/entities, implicit "
        "confirmation, unsupported facilities, Internal/verifier/resource failures and recovery are not causal corroboration. "
        "No C801, C816, accessibility, source-use or diagnostic-policy coverage is added.")
    return result


OLD_INTRO = (
    "**DRAFT, UNAPPROVED, SOURCE ONLY.** No fixtures, models, compiler probes,\n"
    "metadata integration or approvals are authored. The source of truth is\n"
    "`doc/catalogues/attribute_specification_8_5_1.json`; every facet is pending.")
NEW_INTRO = (
    "**C815 fixture representation.** Six retained executions and five exact\n"
    "cross-statement repair controls represent six C815 facets. The source of\n"
    "truth is `doc/catalogues/attribute_specification_8_5_1.json`. Representation\n"
    "does not grant approval; current source/case/link/inventory reviews are\n"
    "independent content-bound records.")
OLD_LEGACY = (
    "The six existing C815 executions are byte-preserved:\n"
    "`C815_invalid:access-stmt`, `C815_invalid:allocatable-stmt`,\n"
    "`C815_invalid:dimension-stmt`, `C815_invalid:intent-stmt`,\n"
    "`C815_invalid:save-stmt` and `C815_valid`. They have no detailed facets yet.\n"
    "Registration therefore changes their requirement-bound fingerprints and\n"
    "requires a later authorized per-case mapping; the two historical grouped\n"
    "review records remain untouched. The valid program retains its real\n"
    "run/effect role, and the five negatives must not receive a file-wide union\n"
    "of facets. No old observation is relabelled.")
NEW_LEGACY = (
    "The six existing IDs remain: `C815_invalid:access-stmt`,\n"
    "`C815_invalid:allocatable-stmt`, `C815_invalid:dimension-stmt`,\n"
    "`C815_invalid:intent-stmt`, `C815_invalid:save-stmt` and `C815_valid`.\n"
    "The invalid container and all complete Fortran bodies are unchanged; the\n"
    "valid source receives only an additive facet header. Each negative has\n"
    "one facet and a full-ID diagnose contract, never a file-wide facet union.\n"
    "The invalid grouped review is historical after key migration. The valid\n"
    "key is retained and explicitly renewable against its current fingerprint.\n"
    "Generation preserves whatever legitimate current review records exist;\n"
    "it neither writes approvals nor assumes permanent stale/draft states.")
OLD_LINKS = (
    "Six existing canonical links explicitly cite the original 8.5.2 base\n"
    "paragraphs. New accounting and the new draft catalogue review prerequisite\n"
    "legitimately stale those source-bound receipts even though their Fortran\n"
    "members and case fingerprints are unchanged. No anchor is dropped, no\n"
    "receipt is renewed and no validation is bypassed to keep them current.\n"
    "The handoff measures these separately from the C815 metadata blocker and\n"
    "the whole-suite source-context inventory impact.")
NEW_LINKS = (
    "Six existing canonical links explicitly cite the original 8.5.2 base\n"
    "paragraphs. New accounting and source-review preconditions can stale those\n"
    "content-bound receipts without changing their Fortran members or case\n"
    "fingerprints. Their actual current/stale states come from native evidence\n"
    "validation and may change after independent source and link adjudication.\n"
    "Generation does not renew records, drop anchors or bypass validation.\n"
    "The source-accounting impact is distinct from C815 metadata migration and\n"
    "whole-inventory context; neither authorship nor representation grants approval.")


def render_view(text, catalogue, pairs=None):
    section = catalogue["section"]
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if begin not in text or end not in text:
        raise ValueError("owned source view lacks its native render boundaries")
    prefix = text.split(begin, 1)[0]
    suffix = text.split(end, 1)[1]
    if section == "8.5.1":
        prefix = prefix.replace(OLD_INTRO, NEW_INTRO).replace(OLD_LEGACY, NEW_LEGACY)
        if NEW_INTRO not in prefix or NEW_LEGACY not in prefix:
            raise ValueError("the controlled C815 view preamble has changed unexpectedly")
        prefix = prefix.replace(
            "rows. The two canonical C requirements have twenty facets, all pending.",
            "rows. The two canonical C requirements have twenty facets: six represented,\nand fourteen pending.")
        suffix = suffix.split("## Exact cross-statement corpus", 1)[0]
    elif section == "8.5.2":
        prefix = prefix.replace(
            "**DRAFT, UNAPPROVED, SOURCE ONLY.** All finite plans remain pending.",
            "**Accessibility source plans.** All thirty-five finite plans remain pending.\n"
            "Current content-bound review states are independent of this representation.")
        prefix = prefix.replace("No fixtures, compiler observations, source-use inventories, links or\napprovals are added.",
                                "This view does not grant or withdraw source, fixture, link or inventory\n"
                                "adjudication. It adds no accessibility execution or SourceUses instance.")
        prefix = prefix.replace(OLD_LINKS, NEW_LINKS)
    else:
        raise ValueError("only the two owned source views are supported")
    prefix = prefix.replace(
        "`Registry.render(write=True)` for this owned view only.",
        "the native renderer; `Registry.render()` defaults to check-only.")
    content = "\n".join(render_requirement(requirement) for requirement in catalogue["requirements"])
    result = prefix + begin + "\n\n" + content + "\n" + end + suffix.rstrip() + "\n"
    if section != "8.5.1":
        return result
    if pairs is None:
        raise ValueError("the C815 representation needs its exact finite repair bindings")
    result += (
        "\n## Exact cross-statement corpus\n\n"
        "Five compile/positive-control/f2023 fixtures come from the actual padded\n"
        "isolated legacy inputs, not reconstructed programs. Exactly the second\n"
        "attribute statement's syntax is deleted. Its indentation, original marker\n"
        "comment, newline and all padding remain, so every control retains31lines.\n"
        "Markers in controls are historical metadata, not diagnostic expectations.\n"
        "All other bytes, declarations, initializers and operations remain.\n\n"
        "| Retained execution | Only facet | Declaration/second-statement span | Repair control |\n"
        "| --- | --- | --- | --- |\n")
    for pair in pairs.values():
        result += (f"| `{pair['negative_id']}` | `{pair['facet']}` | "
                   f"{pair['marker'] - 1}-{pair['marker']} | `{pair['control_id']}` |\n")
    result += "\n"
    for pair in pairs.values():
        result += f"* `{pair['negative_id']}` retains {pair['retained']}\n"
    return result + (
        "\nThe SAVE negative repeats two explicit specifications. Initializer-implied\n"
        "SAVE plus the first explicit confirmation is permitted; the control keeps\n"
        "both n=0 and n=n+1. C815_valid is not any negative's focused repair: it\n"
        "retains its complete module/program, m=1, get_p()=2, size3/2/2 checks and\n"
        "run/effect role. Its key remains renewable. Retained standard/evidence/profile\n"
        "settings are unchanged, while the five new controls declare f2023.\n\n"
        "Predicates use actual calibrated attribute/entity-repetition messages and\n"
        "the original two-statement relation span. C801's same-statement examples,\n"
        "mixed access/INTENT values, RANK/DIMENSION alternatives and other owners\n"
        "are outside this finite corpus. Ordinary zero/nonzero reporting is not a\n"
        "fatal-return or mandatory-rule-code policy. Schema-limited nonfatal warnings\n"
        "remain raw report/noncredit, never an absence-of-reporting assertion.\n\n"
        "Source and fixture reviews may be draft, stale or legitimately current.\n"
        "Generation and tests preserve those independent administrative records.\n"
        "Actual source/link/inventory state changes are reported by the native\n"
        "content-bound validators, not forced by this view. A local index overlay\n"
        "can load these catalogues without replacing existing catalogues, evidence\n"
        "pointers or SourceUses. Source registration alone completes no source-use graph.\n\n"
        "`python3 -B tools/generate_c815_attribute_fixtures.py --check` verifies the\n"
        "exact generated files and both native view regions. Source/repair/marker/cause,\n"
        "nonfatal/failure, facet/key-migration and administrative-renewal regressions\n"
        "accompany the finite corpus. Independent adjudication remains a separate operation.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, pairs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    access = json.loads((ROOT / ACCESS_CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    views = {VIEW: render_view((ROOT / VIEW).read_text(), updated, pairs),
             ACCESS_VIEW: render_view((ROOT / ACCESS_VIEW).read_text(), access)}
    controls = {path for path in (ROOT / "tests/fixtures").glob("c815_attribute_*/*") if path.is_file()}
    expected_controls = {path for path in files if "/fixtures/" in str(path)}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in controls - expected_controls]
        if catalogue != updated:
            stale.append(CATALOGUE)
        stale += [path for path, text in views.items() if (ROOT / path).read_text() != text]
        if stale:
            raise SystemExit("stale C815 representation: " + ", ".join(sorted(stale)))
    else:
        if controls - expected_controls:
            raise ValueError("unexpected control files outside the finite C815 corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            for path, text in views.items():
                (ROOT / path).write_text(text)
    print(f"{'Checked' if args.check else 'Generated'} five exact C815 controls, five contracts and one additive valid header; six facets.")


if __name__ == "__main__":
    main()
