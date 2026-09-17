#!/usr/bin/env python3
"""Generate the finite, non-executable R402 declaration-name source inventory."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from suite_data import Registry, SuiteError, write_json

INVENTORY_ID = "R402.declaration-name-uses-8.2"
SECTION = "8.2"
SECTION_SHA256 = "d6affa6e58eeb3551bdca653eddc7ad666de72c8c426acf4be5776760ed61e2d"
HEADS_SHA256 = "e5f176b78bd8b6fb24d8aaf7c7280f094ab70f34c0781fb63ab9a3f5d19074e1"
HEAD_COUNT = 502
PDF_SHA256 = "7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2"

SUBUNITS = {
    "R801": "type-prefix double-colon-group attribute-separators entity-list",
    "p1": "list-declared-type list-parameters entity-character-override",
    "R802": "access allocatable asynchronous codimension contiguous dimension external intent intrinsic language-binding optional parameter pointer protected rank save target value volatile",
    "C801": "statement-scope same-specification single-occurrence",
    "C802": "name-present single-entity no-name-outside-premise",
    "C803": "binding-premise procedure-exclusion",
    "p2": "list-attributes entity-array-spec entity-coarray-spec",
    "R803": "object-name object-array-spec object-coarray-spec object-character-length object-initialization suffix-order function-name function-character-length",
    "C804": "noncharacter-premise no-star-length",
    "C805": "colon asterisk specification-expression",
    "C806": "initialization-premise double-colon",
    "C807": "parameter-keyword each-entity",
    "C808": "dummy function-result named-common block-data-exception blank-common allocatable automatic",
    "C809": "external-function intrinsic-function dummy-function procedure-pointer statement-function",
    "R804": "name",
    "C810": "data-object",
    "R805": "constant-expression null-init initial-data-target",
    "R806": "function-reference",
    "C811": "arrow-requires-pointer equals-excludes-pointer",
    "C812": "initial-target-premise compatibility-reference",
    "C813": "intrinsic-identity no-arguments",
    "p3": "specific-type specific-declaration-permission generic-type-no-effect",
    "p4": "nonpointer-premise type-parameters implied-shape-rank other-shape",
    "note-unnumbered": "example-introduction real-array logical-list complex-initialization",
    "note-unnumbered.2": "selected-integer selected-object typeof real-inquired-kind real-literal-kind complex-inquired-kind character-literal-kind character-lengths person null-node humongous classof definition-reference",
}
PARENT_TERMS = {
    "R803": ["object-name", "function-name"],
    "C808": ["object-name"],
    "C809": ["function-name"],
    "R804": ["object-name"],
    "C810": ["object-name"],
    "C812": ["object-name"],
}
NON_OCCURRENCES = {
    "R801": "The enclosing production uses entity-decl-list, not a suffixed -name term. Its members are traced at R803 rather than expanded into invented additional occurrences here.",
    "p1": "This prose supplies declared-type, parameter and per-entity length semantics without a suffixed -name class occurrence.",
    "R802": "The attribute alternatives contain no suffixed -name class. Attribute keywords are not variable-name productions.",
    "C801": "The statement-local repeated-attribute condition contains no suffixed -name class.",
    "C802": "NAME= is a binding-label specifier, not an R402 syntax-class occurrence or a Fortran entity-name alias.",
    "C803": "The prose phrase procedure names is not a literal function-name class occurrence. Its binding-context restriction is retained as a dependency of the R803/C809 function-name records.",
    "p2": "The list-attribute and per-entity shape/coshape prose contains no suffixed -name class.",
    "C804": "The CHARACTER-only length-suffix condition contains no suffixed -name class; it remains an enclosing R803 condition.",
    "C805": "The type-parameter-value alternatives contain no suffixed -name class; this is not a name-syntax restriction.",
    "C806": "Initializer-triggered double-colon presence contains no suffixed -name class.",
    "C807": "Per-entity PARAMETER initialization contains no suffixed -name class.",
    "R805": "The initialization alternatives use expression, null-init and target classes, not a suffixed -name term.",
    "R806": "The function-reference class is not a function-name occurrence. Transitive expansion of another production is not a new textual occurrence here.",
    "C811": "The initialization/POINTER relation contains no suffixed -name class.",
    "C813": "Intrinsic NULL identity and argument exclusion constrain function-reference, not a suffixed -name class.",
    "p3": "Specific and generic intrinsic function names are discussed in prose, without a suffixed syntax-class token. The type-declaration role remains a function-name dependency.",
    "p4": "Nonpointer initialization type/rank/shape obligations contain no suffixed -name class.",
    "note-unnumbered": "The informative examples contain program identifiers, not occurrences of the standard's suffixed -name syntax classes.",
    "note-unnumbered.2": "The continued examples and cross-reference contain program identifiers and other syntax, not suffixed -name class occurrences. Literal kind choices are not new name or processor promises.",
}
COMMON_BASIS = [
    "4.1.2#p2",
    "4.1.3#p1",
    "4.1.3#p2",
    "6.2.2#R603",
    "6.2.2#C601",
]
R803_CONTEXT = [
    "8.2#R801", "8.2#p1", "8.2#p2", "8.2#C801", "8.2#C802",
    "8.2#C803", "8.2#C804", "8.2#C805", "8.2#C806", "8.2#C807",
    "8.2#C808", "8.2#C809", "8.2#C811", "8.2#C812", "8.2#p3", "8.2#p4",
]


def reviewed_units(registry):
    if registry.standard["sha256"] != PDF_SHA256:
        raise SuiteError("declaration-name classification requires the pinned J3/24-007 document")
    section = registry.sections[SECTION]
    expected = {parent: [parent + "." + suffix for suffix in suffixes.split()]
                for parent, suffixes in SUBUNITS.items()}
    if section["sha256"] != SECTION_SHA256 or set(section["units"]) != set(SUBUNITS):
        raise SuiteError("8.2 original source census changed; review the name classification before regeneration")
    if registry.catalogues[SECTION].get("subunits", {}) != expected:
        raise SuiteError("8.2 fine source census changed; new or removed units require explicit name-use review")
    if set(PARENT_TERMS) & set(NON_OCCURRENCES) or set(PARENT_TERMS) | set(NON_OCCURRENCES) != set(SUBUNITS):
        raise SuiteError("the finite parent classification is not an exact partition")
    return expected


def occurrence(parent, unit, term):
    definition = "4.1.3#R402" if term == "function-name" else "8.2#R804"
    dependencies = set(COMMON_BASIS)
    if term == "object-name":
        dependencies.update(("8.2#R804", "8.2#C810"))
    else:
        dependencies.update(("8.2#R803", "8.2#C809", "8.2#C803", "8.2#p3"))
    if parent == "R803":
        dependencies.update(R803_CONTEXT)
    elif parent in ("C808", "C812"):
        dependencies.add("8.2#R803")
    if unit != parent:
        dependencies.add("8.2#" + parent)
    if term == "object-name":
        rationale = "R804 explicitly defines object-name; R402 does not own this occurrence. R603/C601 and the associated C810 data-object condition remain."
    else:
        rationale = "No numbered explicit function-name production overrides R402 in the pinned source. R603/C601 and this entity-declaration context's C809 roles and C803 binding exclusion remain."
    if parent == "R804":
        rationale += " This is the defining production head, not an additional program use."
    if unit != parent:
        rationale += " This fine record retains the parent's governing subject; ordinal1 identifies the same parent occurrence, not another physical token."
    return dict(term=term, ordinal=1,
                resolution="target" if term == "function-name" else "explicit-override",
                definition=definition, dependencies=sorted(dependencies - {definition}),
                rationale=rationale)


def build_inventory(registry):
    subdivisions = reviewed_units(registry)
    if "assumed-name-census" not in registry.requirements["R402"]["pending"]:
        raise SuiteError("R402 assumed-name-census must remain pending; this finite inventory cannot complete it")
    entries = []
    for parent, children in subdivisions.items():
        for unit in [parent, *children]:
            if parent in NON_OCCURRENCES:
                rationale = NON_OCCURRENCES[parent]
                if unit != parent:
                    rationale += " The fine subdivision retains that classification; names in an anchor label are not source occurrences."
                entries.append(dict(source="8.2#" + unit, disposition="not-applicable",
                                    rationale=rationale, occurrences=[]))
                continue
            terms = PARENT_TERMS[parent]
            if parent == "R803" and unit != parent:
                terms = ["function-name" if unit.startswith("R803.function-") else "object-name"]
            entries.append(dict(
                source="8.2#" + unit, disposition="mapped",
                rationale=("Original parent occurrence classification." if unit == parent else
                           "Contextual fine subdivision of the parent's shared name subject; not a new physical occurrence."),
                occurrences=[occurrence(parent, unit, term) for term in terms]))
    entries.sort(key=lambda entry: entry["source"])
    basis = set(COMMON_BASIS)
    for entry in entries:
        for item in entry["occurrences"]:
            basis.update(item["dependencies"])
            if item["resolution"] == "explicit-override":
                basis.add(item["definition"])
    return dict(
        id=INVENTORY_ID,
        target=dict(requirement="R402", facet="assumed-name-census", source_units=["4.1.3#R402"]),
        basis=sorted(basis), sections=[SECTION], coverage_credit="none",
        claim="Finite classification of every original base and reviewed fine unit in8.2. Seven physical parent occurrences of object-name/function-name are rebound to their governing fine contexts;31 occurrence records are not31 physical tokens. Function-name uses R402; object-name is explicitly overridden by R804, including its defining head. Prose mentions, binding-label NAME= and identifiers in examples are not fabricated syntax-class uses.",
        limitation=(
            "This is not the whole-standard assumed-name census, recursive grammar expansion, complete program "
            "name/scope resolution, fixture approval or processor evidence. Enclosing8.2conditions and lexical "
            "R603/C601 dependencies are retained, not replaced by the alias. Global absence of an explicit "
            "function-name head is checked against all502original numbered production heads, independently "
            "of a known-rule whitelist; their canonical compact-JSON record SHA256 is " + HEADS_SHA256 +
            ". That bounded heading check does not ratify the global paragraph/list/table census. The target "
            "facet stays pending; source-unit classification, source review, inventory adjudication and "
            "execution/coverage credit remain separate."),
        entries=entries)


def generated_registry(registry):
    result = copy.deepcopy(registry.source_uses.data)
    inventory = build_inventory(registry)
    existing = [i for i, row in enumerate(result["inventories"]) if row["id"] == INVENTORY_ID]
    if existing:
        index = existing[0]
        old = result["inventories"][index]
        if "review" in old:
            inventory["review"] = copy.deepcopy(old["review"])
        result["inventories"][index] = inventory
    else:
        result["inventories"].append(inventory)
    return result


def check_generated(registry):
    if registry.source_uses.data != generated_registry(registry):
        raise SuiteError("stale declaration-name source-use inventory; regenerate its reviewed finite classification")


def verify_pdf(registry, filename):
    reviewed_units(registry)
    raw = filename.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PDF_SHA256:
        raise SuiteError("PDF checksum differs from the pinned J3/24-007 document")
    import fitz
    import import_standard as source

    document = fitz.open(stream=raw, filetype="pdf")
    if len(document) != 688:
        raise SuiteError("unexpected pinned PDF page count")
    end = next(page for _, title, page in document.get_toc() if title == "Index")
    known = {unit for section in registry.sections.values() for unit in section["units"]
             if re.fullmatch(r"[RC]\d+", unit)}
    heads = {}
    current = active = None
    fragments = []
    units = {}
    for page_number in range(14, end - 1):
        for spans in source.rows(document[page_number]):
            heading = source.heading(spans)
            if heading:
                current, active = heading, None
                continue
            first = spans[0]
            label = first["text"].strip()
            text = " ".join(span["text"].strip() for span in spans)
            # Derive the raw denominator before comparing it with the structural census.
            if 55 <= first["bbox"][0] <= 61 and re.fullmatch(r"R\d+", label):
                match = re.fullmatch(r"(R\d+)\s+([a-z][a-z0-9-]*)\s+is(?:\s+.*)?", text)
                if not match or label in heads:
                    raise SuiteError("unparsed or repeated original rule head: " + label)
                if current not in registry.sections or label not in registry.sections[current]["units"]:
                    raise SuiteError("original rule head missing from source census: " + label)
                binding = registry.sections[current]["units"][label]
                if binding["pdf_page"] != page_number + 1:
                    raise SuiteError("original rule-head page differs from source census: " + label)
                heads[label] = dict(id=label, term=match[2], section=current,
                                    pdf_page=page_number + 1, source_unit_sha256=binding["sha256"])
            if current != SECTION:
                continue
            fragments.append(text)
            labelled = source.unit_label(spans, known)
            if labelled:
                name, _ = labelled
                if name in units:
                    suffix = 2
                    while f"{name}.{suffix}" in units:
                        suffix += 1
                    name = f"{name}.{suffix}"
                active = name
                units[active] = []
            if active is None:
                raise SuiteError("unlabelled source within the reviewed8.2scope")
            units[active].append(text)
    expected_heads = {name for name in known if name.startswith("R")}
    records = [heads[name] for name in sorted(heads)]
    digest = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if set(heads) != expected_heads or len(heads) != HEAD_COUNT or digest != HEADS_SHA256:
        raise SuiteError("original rule-head census changed; independent resolution review is required")
    if [row["id"] for row in records if row["term"] == "object-name"] != ["R804"]:
        raise SuiteError("object-name explicit-definition resolution changed")
    if any(row["term"] == "function-name" for row in records):
        raise SuiteError("function-name now has an explicit overriding production")
    if hashlib.sha256("\n".join(fragments).encode()).hexdigest() != SECTION_SHA256:
        raise SuiteError("original8.2section hash differs from the reviewed scope")
    if set(units) != set(SUBUNITS):
        raise SuiteError("original8.2unit denominator differs from the reviewed scope")
    term_pattern = re.compile(r"(?<![a-z0-9-])(?:[a-z][a-z0-9]*-)+name(?![a-z0-9-])")
    count = 0
    for name, lines in units.items():
        text = "\n".join(lines)
        if hashlib.sha256(text.encode()).hexdigest() != registry.sections[SECTION]["units"][name]["sha256"]:
            raise SuiteError("original source-unit hash changed: " + name)
        actual = term_pattern.findall(text)
        if actual != PARENT_TERMS.get(name, []):
            raise SuiteError("original name occurrences differ from the finite classification: " + name)
        count += len(actual)
    return dict(numbered_heads=len(heads), physical_parent_occurrences=count, head_records_sha256=digest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pdf", type=Path, help="also verify original source and all rule heads using PyMuPDF")
    args = parser.parse_args()
    registry = Registry(ROOT)
    if args.pdf:
        print(json.dumps(verify_pdf(registry, args.pdf), sort_keys=True))
    if args.check:
        check_generated(registry)
    else:
        write_json(registry.source_uses.path, generated_registry(registry))
    report = next(row for row in Registry(ROOT).source_uses.report() if row["id"] == INVENTORY_ID)
    print(f"{'Checked' if args.check else 'Generated'} {INVENTORY_ID}: "
          f"{report['source_unit_count']} units, {report['occurrence_record_count']} occurrence records; "
          f"state={report['state']}, coverage=none, target facet=pending.")


if __name__ == "__main__":
    main()
