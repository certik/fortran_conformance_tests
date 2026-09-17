#!/usr/bin/env python3
"""Per-execution C801 reporting contracts and five exact legacy-input deletion repairs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from run_tests import isolated_cases
from suite_data import render_requirement

INVALID = "tests/clause08/C801_invalid.f90"
VALID = "tests/clause08/C801_valid.f90"
SIDECAR = "tests/clause08/C801_invalid.cases.json"
CATALOGUE = "doc/catalogues/type_declaration_statements_8_2.json"
VIEW = "doc/fortran_2023_8_2.md"
INVALID_SHA = "d603976ab70bebc2cda0f9557d2f9531fb0c9119af5106293093afd563639136"
VALID_BODY_SHA = "eb5a32b631c396b98a5463bb0ca6709d252837c2cee886a374c501b913fd897e"
VALID_HEADER = b"! covers: distinct-attributes-admission\n"
CASES = {
    "access-spec": dict(attribute="public", subject="m", facet="duplicate-public", marker=23,
                        context="Initialized module INTEGER m=1 in the specification part."),
    "allocatable": dict(attribute="allocatable", subject="b", facet="duplicate-allocatable", marker=5,
                        context="Local deferred-shape REAL b(:), with its ALLOCATE(b(2)) retained."),
    "dimension": dict(attribute="dimension(3)", subject="a", facet="duplicate-dimension", marker=10,
                      context="Local explicit-shape INTEGER a(3), with the complete a=1 assignment retained."),
    "intent": dict(attribute="intent(in)", subject="x", facet="duplicate-intent-in", marker=15,
                   context="Scalar INTEGER dummy x with INTENT(IN), unmodified and unread in its complete procedure."),
    "parameter": dict(attribute="parameter", subject="n", facet="duplicate-parameter", marker=19,
                      context="INTEGER named constant n=1; its required constant initializer is retained."),
}
FACETS = [item["facet"] for item in CASES.values()] + ["distinct-attributes-admission"]
CAUSES = {
    "access-spec": ["Duplicate PUBLIC attribute", "Attribute 'PUBLIC' cannot be used more than once"],
    "allocatable": ["Duplicate ALLOCATABLE attribute", "Attribute 'ALLOCATABLE' cannot be used more than once"],
    "dimension": ["Dimensions specified twice", "Duplicate DIMENSION attribute",
                  "Attribute 'DIMENSION' cannot be used more than once"],
    "intent": ["Duplicate INTENT (IN) attribute", "Attribute 'INTENT(IN)' cannot be used more than once"],
    "parameter": ["Duplicate PARAMETER attribute", "Attribute 'PARAMETER' cannot be used more than once"],
}
EXCLUSIONS = [
    "not implemented", "not yet implemented", "unimplemented", "not yet supported", "not supported", "unsupported",
    "has no implicit type", "neither a data pointer nor an allocatable variable",
    "internal error", "internal:", "ASR verify", "out of memory", "recovery",
]
OBSERVED_CAUSES = {
    label: dict(
        gfortran=dict(severity="error", message=CAUSES[label][1 if label == "dimension" else 0] + " at (1)"),
        flang=dict(severity="error" if label == "dimension" else "warning",
                   message=CAUSES[label][-1] + ("" if label == "dimension" else " [-Wredundant-attribute]")))
    for label in CASES
}
OBSERVED_CAUSES["dimension"]["lfortran"] = dict(severity="error", message="Dimensions specified twice")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def control_id(label):
    return "C801_valid__c801_declaration_" + label.replace("-", "_") + "_control"


def valid_body(root=ROOT):
    raw = (root / VALID).read_bytes()
    body = raw[len(VALID_HEADER):] if raw.startswith(VALID_HEADER) else raw
    if sha(body) != VALID_BODY_SHA:
        raise ValueError("C801_valid body or pre-existing comments changed beyond the authorized additive header")
    return body


def repair_source(source, line, attribute):
    lines = source.splitlines(keepends=True)
    statement = lines[line - 1]
    repeated = ", " + attribute + ", " + attribute
    if statement.count(repeated) != 1 or statement.split("!", 1)[0].count(attribute) != 2:
        raise ValueError("the finite repair requires exactly two identical attribute specifications at its marker")
    column = statement.index(repeated) + len(", " + attribute)
    deleted = ", " + attribute
    offset = sum(len(item.encode("ascii")) for item in lines[:line - 1]) + column
    raw = source.encode("ascii")
    if raw[offset:offset + len(deleted)] != deleted.encode("ascii"):
        raise ValueError("attribute/comma deletion is not bound to the actual isolated bytes")
    repaired = raw[:offset] + raw[offset + len(deleted):]
    changed_lines = repaired.decode("ascii").splitlines(keepends=True)
    if len(lines) != len(changed_lines) or [i + 1 for i, pair in enumerate(zip(lines, changed_lines))
                                          if pair[0] != pair[1]] != [line]:
        raise ValueError("repair changed more than its one declaration line")
    return repaired, dict(
        line=line, first_column=column + 1, last_column=column + len(deleted),
        byte_span_zero_based_half_open=[offset, offset + len(deleted)], deleted=deleted,
        negative_statement=statement.rstrip("\n"), repaired_statement=changed_lines[line - 1].rstrip("\n"),
        deletion_scope="Only the second identical attribute specification and its preceding comma/space.",
        marker_comment_retained=True, all_other_input_bytes_unchanged=True)


def build_corpus(root=ROOT):
    root = Path(root)
    raw = (root / INVALID).read_bytes()
    if sha(raw) != INVALID_SHA:
        raise ValueError("the retained C801_invalid container must remain byte-for-byte unchanged")
    isolated = {item[2]: item for item in isolated_cases(str(root / INVALID), "C801")}
    if set(isolated) != set(CASES):
        raise ValueError("the retained C801 execution set differs from its five authorized isolated units")
    files, pairs, contracts = {}, {}, {}
    for label, entry in CASES.items():
        line, rule, name, bounds, source = isolated[label]
        if (line, rule, name) != (entry["marker"], "C801", label):
            raise ValueError("the original case ID or source marker moved")
        repaired, repair = repair_source(source, line, entry["attribute"])
        folder = "tests/fixtures/c801_declaration_" + label.replace("-", "_")
        manifest = dict(
            schema_version=1, id=control_id(label), rule="C801", facets=[entry["facet"]],
            evidence="positive-control", standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile", outcome="success", step="source"))
        files[root / folder / "source.f90"] = repaired
        files[root / folder / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        contracts[label] = dict(
            facets=[entry["facet"]], outcome="diagnose",
            diagnostic=dict(line=line, end_line=line, contains_any=list(CAUSES[label]), excludes_any=list(EXCLUSIONS)))
        pairs[label] = dict(
            **entry, negative_id="C801_invalid:" + label, control_id=control_id(label),
            negative_path=INVALID, control_path=folder + "/fixture.json",
            isolated_bounds=list(bounds), negative_source=source, negative_sha256=sha(source.encode()),
            repair_source=repaired.decode(), repair_sha256=sha(repaired), repair=repair,
            causal_contract=contracts[label], observed_native_causes=OBSERVED_CAUSES[label],
            old_review_key="C801_invalid", new_review_key="C801_invalid:" + label,
            retained_standard="", retained_evidence="effect", retained_profiles=[],
            warning_limitation="Retained sidecars have no allow_nonfatal field; observed warning reports remain explicit noncredit.")
    files[root / SIDECAR] = (json.dumps(dict(schema_version=1, cases=contracts), indent=2) + "\n").encode()
    files[root / VALID] = VALID_HEADER + valid_body(root)
    return files, pairs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    found = False
    for requirement in result["requirements"]:
        if requirement["id"] != "C801":
            continue
        found = True
        if not set(FACETS) <= set(requirement["facets"]):
            raise ValueError("unknown C801 facet in the bounded migration")
        for facet in FACETS:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
            raise ValueError("an unselected C801 plan is not pending")
        original = requirement["oracle"].split("\n\nC801 declaration integration:", 1)[0]
        requirement["oracle"] = original + (
            "\n\nC801 declaration integration: five existing isolated inputs retain their IDs and complete bytes. "
            "Each receives exactly one facet and an exact-marker, attribute-repetition diagnose contract, with its "
            "full case ID as review key. Five compile-only positive controls delete only one repeated specification "
            "and its comma from those exact inputs. C801_valid retains its run/effect body and size3/size2 checks, "
            "with only an additive distinct-attributes-admission header. Retained standard/evidence/profiles are unchanged; "
            "new controls use f2023. Error-typed reporting may return0 or ordinary nonzero; no fatal exit or printed rule code is required.")
        requirement["oracle_limitation"] = (
            "Six facets are represented; representation does not confer approval. The other17C801 facets and "
            "all101other8.2 facets remain pending. Original grouped evidence remains historical: the invalid group "
            "is retired, while the retained valid review key requires its own explicit current renewal. "
            "Actual cause wording is finite calibration, not prescribed language. Flang's four located nonfatal duplicate-attribute "
            "warnings cannot be admitted by the existing retained-sidecar schema; preserve their explicit noncredit without claiming "
            "absence of reporting capability or changing warnings/profiles/harness. Source and inventory adjudication remain separate.")
    if not found:
        raise ValueError("the registered8.2 source catalogue lacks C801")
    return result


OLD_INTRO = (
    "**DRAFT, UNAPPROVED, SOURCE ONLY.** Every facet is pending; no fixture,\n"
    "compiler observation, source approval or case approval is added.\n")
AUTHOR_INTRO = (
    "**DRAFT, UNAPPROVED C801 INTEGRATION.** Six retained cases and five\n"
    "source-minimal compile controls represent six C801 facets;118facets remain\n"
    "pending. No source, fixture, case, link or inventory approval is added.\n")
NEW_INTRO = (
    "**C801 SOURCE/CONTRACT INTEGRATION.** Six retained cases and five\n"
    "source-minimal compile controls represent six C801 facets;118facets remain\n"
    "pending. Authorship does not confer source, fixture, case, link or inventory\n"
    "approval; current adjudications are separate content-bound records.\n")
OLD_LEGACY = (
    "facet/causal-contract decisions, not a file-level union. The valid program\n"
    "remains a real run/effect. Neither old metadata nor grouped reviews are\n"
    "silently rewritten. No old observation is relabelled with a new fingerprint.")
AUTHOR_LEGACY = (
    "facet/causal-contract bindings, now supplied by the exact-case\n"
    "sidecar, never a file-level union. Their container bytes remain unchanged.\n"
    "The valid program remains a real run/effect with only an additive header.\n"
    "The intentional metadata/review-key migration does not rewrite old grouped\n"
    "receipts or relabel any old observation with a new fingerprint.")
NEW_LEGACY = (
    "facet/causal-contract bindings, now supplied by the exact-case\n"
    "sidecar, never a file-level union. Their container bytes remain unchanged.\n"
    "The valid program remains a real run/effect with only an additive header.\n"
    "Original grouped evidence remains historical: the invalid group is retired,\n"
    "while the valid key requires explicit current renewal. No old observation\n"
    "is relabelled with a new fingerprint.")
BEGIN = "<!-- BEGIN GENERATED 8.2 -->"
END = "<!-- END GENERATED 8.2 -->"
INTEGRATION = "## Finite C801 metadata and causal-contract integration"


def render_view(text, catalogue, pairs):
    if BEGIN not in text or END not in text:
        raise ValueError("the owned8.2 view lacks its native generated boundaries")
    prefix = text.split(BEGIN, 1)[0]
    suffix = text.split(END, 1)[1]
    if INTEGRATION in suffix:
        suffix = suffix.split(INTEGRATION, 1)[0]
    prefix = prefix.replace(OLD_INTRO, NEW_INTRO).replace(AUTHOR_INTRO, NEW_INTRO)
    if NEW_INTRO not in prefix:
        raise ValueError("the owned source-view introduction has changed unexpectedly")
    prefix = prefix.replace(
        "The definitions below are generated by `Registry.render(write=True)`.",
        "The definitions below follow the native renderer; `Registry.render()` defaults to check-only.")
    prefix = prefix.replace(
        "All 124 facets across the 23 requirements are explicitly pending.",
        "Six C801 facets are represented;118other facets across the23requirements remain pending.")
    prefix = re.sub(
        r"(?m)^\| TD-Q06 \|.*\|$",
        "| TD-Q06 | The five exact per-case contracts and additive valid header resolve the native collection gate. "
        "Five source-minimal repairs are supplied. Original grouped receipts stay historical/stale; current "
        "source/case/cause approval remains independent. |", prefix)
    prefix = prefix.replace(OLD_LEGACY, NEW_LEGACY).replace(AUTHOR_LEGACY, NEW_LEGACY)
    native = "\n".join(render_requirement(requirement) for requirement in catalogue["requirements"])
    text = prefix + BEGIN + "\n\n" + native + "\n" + END + suffix.rstrip() + "\n\n" + INTEGRATION + "\n\n"
    text += (
        "The original six execution IDs remain. Five negative inputs are produced by the existing\n"
        "`isolated_cases` helper, including its original blank-line padding and marker comments.\n"
        "The new positive controls delete only the second repeated attribute specification and its\n"
        "preceding comma/space. They do not reconstruct or simplify the program units.\n\n"
        "| Retained negative | Only facet | Original marker | Compile-only repair |\n"
        "| --- | --- | ---: | --- |\n")
    for pair in pairs.values():
        text += f"| `{pair['negative_id']}` | `{pair['facet']}` | {pair['marker']} | `{pair['control_id']}` |\n"
    text += "\n"
    for pair in pairs.values():
        text += f"* `{pair['negative_id']}`: {pair['context']} Delete exactly `{pair['repair']['deleted']}`.\n"
    return text + (
        "\n`C801_valid` is only `distinct-attributes-admission`: its complete existing body,\n"
        "DIMENSION/PARAMETER and ALLOCATABLE/DIMENSION declarations, allocation, definition\n"
        "and size3/size2 guards are unchanged. It remains run/effect, not an empty compile\n"
        "substitute or the repair of any negative. Retained effective standard/evidence/profiles\n"
        "are unchanged; only the five new compile controls declare f2023.\n\n"
        "Each negative now has `outcome=diagnose` and its own full-ID review key, deliberately\n"
        "replacing old reject/group-key semantics. Its sole facet, exact isolated marker line,\n"
        "observed attribute-repetition cause phrases and exclusions are in\n"
        "`tests/clause08/C801_invalid.cases.json`. No file-wide facet union is introduced.\n"
        "Original grouped evidence remains historical. The invalid group is retired, while\n"
        "the valid key requires explicit current renewal; current bindings need independent review.\n\n"
        "C801 is statement-local. C815 and individual attribute eligibility remain prerequisites,\n"
        "not new coverage. PUBLIC stays in a module specification part; ALLOCATABLE retains its\n"
        "REAL deferred-shape array and allocation; DIMENSION retains INTEGER shape3 and a=1;\n"
        "INTENT retains the unchanged INTEGER IN dummy; PARAMETER retains n=1. No mixed\n"
        "PUBLIC/PRIVATE, INTENT payload, RANK/DIMENSION or other attribute contrast is added.\n\n"
        "The required capability under4.2p2(3) is reporting, not mandatory fatal rejection or\n"
        "printed rule codes. A located, cause-matching error diagnostic can have return0 or an\n"
        "ordinary nonzero status. Bare keywords, source echoes, unrelated typing/allocation,\n"
        "recovery, unsupported facilities, Internal/verifier/resource failures and timeouts\n"
        "do not corroborate repetition. Native wording is not prescribed by the standard.\n\n"
        "The frozen calibration records Flang warnings for PUBLIC, ALLOCATABLE, INTENT(IN)\n"
        "and PARAMETER. They are genuine located repetition reports, but retained sidecars\n"
        "currently cannot encode `allow_nonfatal`. Their noncredit is preserved as a mechanism\n"
        "limitation, not absence of reporting capability. No warning flag, profile, shared\n"
        "harness change or forced reference agreement is used. F2018 results are not promoted\n"
        "to F2023 qualification of this source packet.\n\n"
        "The original author packet excluded its local8.1/8.2index overlay, preserving1972\n"
        "retained IDs,1966unaffected fingerprints, nine links and the empty SourceUses registry.\n"
        "Six C801 fingerprints intentionally changed, and five new controls yielded1977cases.\n"
        "Subsequent registration and source/case/inventory adjudication are coordinator actions,\n"
        "not generator side effects. Current receipt states must be read from the registry.\n\n"
        "`python3 -B tools/generate_c801_declaration_fixtures.py --check` verifies exact generated\n"
        "inputs, the additive header, sidecar and owned8.2render. Bounded regressions cover\n"
        "minimal repairs, individual facets, migration, actual markers, causal/nonfatal/failure\n"
        "predicates and administrative preservation. Independent source/fixture/oracle review\n"
        "and current-main index/inventory integration remain separate gates.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, pairs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view((ROOT / VIEW).read_text(), updated, pairs)
    actual = {path for path in (ROOT / "tests/fixtures").glob("c801_declaration_*/*") if path.is_file()}
    generated_controls = {path for path in files if "/fixtures/" in str(path)}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - generated_controls]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale C801 declaration packet: " + ", ".join(sorted(stale)))
    else:
        if actual - generated_controls:
            raise ValueError("unexpected C801 control files would remain in the finite corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
        elif catalogue != updated or (ROOT / VIEW).read_text() != view:
            raise SystemExit("generated inputs; run --sync-catalogue for the owned source-view integration")
    print(f"{'Checked' if args.check else 'Generated'} 12 files: five controls, one retained header and one five-case sidecar; six facets.")


if __name__ == "__main__":
    main()
