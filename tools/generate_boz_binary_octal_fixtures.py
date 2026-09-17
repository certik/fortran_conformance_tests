#!/usr/bin/env python3
"""Finite binary/octal BOZ lexical compile cases; no numeric or representation oracles."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.7"
CATALOGUE = "doc/catalogues/boz_literals.json"
VIEW = "doc/fortran_2023_7_7.md"
ELIGIBLE = {
    "R773": ["quotation-mark-form", "nonempty-digit-sequence", "nondigit-body"],
    "C7117": ["zero-and-one-admissions", "other-decimal-digit-exclusion", "interior-invalid-digit"],
    "R774": ["quotation-mark-form", "nonempty-digit-sequence", "nondigit-body"],
    "C7118": ["zero-through-seven-admissions", "eight-and-nine-exclusion", "interior-invalid-digit"],
}
EXCLUDED = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "implementation limitation", "internal compiler error", "ASR verify", "ASR verifier",
    "module failed verification", "out of memory", "cannot allocate memory", "segmentation fault",
    "unexpected end of file", "unexpected eof", "missing end", "unterminated", "missing quote", "stack trace",
]
RADICES = {"B": ("binary", "01", "R773", "C7117"), "O": ("octal", "01234567", "R774", "C7118")}
DECIMAL = "0123456789"


def identifier(rule, variant, invalid=False):
    return rule + ("_invalid__boz_binary_octal_" if invalid else "_valid__boz_binary_octal_") + variant


def token(prefix, quote, body):
    if prefix not in RADICES or quote not in ("'", '"'):
        raise ValueError("this corpus requires an uppercase binary/octal prefix and matched ordinary delimiters")
    return prefix + quote + body + quote


def lexical_conditions(prefix, body):
    """Classify source characters/positions only; never compute a literal's numeric value."""
    radix, allowed, syntax, constraint = RADICES[prefix]
    nondigits = [i for i, char in enumerate(body, 1) if char not in DECIMAL]
    invalid_values = [i for i, char in enumerate(body, 1) if char in DECIMAL and char not in allowed]
    owners = []
    if not body or nondigits:
        owners.append(syntax)
    if invalid_values:
        owners.append(constraint)
    return dict(radix=radix, empty=not body, nondigit_positions=nondigits,
                excluded_decimal_positions=invalid_values, owners=owners, numeric_value=None)


def quotation_prelude(prefix):
    bodies = ["0", "1", "101"] if prefix == "B" else ["0", "7", "157"]
    return [(f"admitted_{i}", token(prefix, '"', body)) for i, body in enumerate(bodies, 1)]


def alphabet_prelude(prefix):
    if prefix == "B":
        return [(f"admitted_{i}", token(prefix, quote, body)) for i, (quote, body) in enumerate(
            [("'", "0"), ("'", "1"), ("'", "101"), ('"', "0"), ('"', "1"), ('"', "101")], 1)]
    return [(f"admitted_{i+1}", token(prefix, "'", digit)) for i, digit in enumerate("01234567")] + [
        ("admitted_9", token(prefix, '"', "157"))]


def data_source(prelude, target):
    pairs = list(prelude) + [("subject", target)]
    names = [name for name, _ in pairs]
    if len(names) != len(set(names)):
        raise ValueError("each DATA target must be a distinct scalar")
    text = "program boz_lexical\nimplicit none\n"
    text += "".join("integer :: " + name + "\n" for name in names)
    text += "".join(f"data {name} / {literal} /\n" for name, literal in pairs)
    return text + "end program boz_lexical\n"


def diagnostic_messages(prefix, body):
    """Finite prospective cause predicates; actual native additions need bound observations."""
    radix, allowed, _, _ = RADICES[prefix]
    state = lexical_conditions(prefix, body)
    if state["empty"]:
        return [f"Empty {radix} BOZ literal",
                f"A {radix} BOZ literal must contain at least one digit",
                "Empty set of digits in BOZ constant at (1)"]
    positions = state["nondigit_positions"] or state["excluded_decimal_positions"]
    if len(positions) != 1:
        raise ValueError("a negative requires one focused offending character")
    char = body[positions[0]-1]
    if state["nondigit_positions"]:
        messages = [f"Character '{char}' is not a decimal digit in a {radix} BOZ literal",
                    f"Invalid character '{char}' in a {radix} BOZ literal"]
    else:
        messages = [f"Digit '{char}' is not allowed in a {radix} BOZ literal",
                    f"Invalid digit '{char}' in a {radix} BOZ literal"]
    native_bodies = {"B": set("23456789") | {"1021", "A"}, "O": {"8", "9", "1781", "A"}}
    if body in native_bodies[prefix]:
        messages.append(f"Invalid digit ('{char.lower()}') in BOZ literal '{prefix.lower()}\"{body.lower()}\"'")
    return messages


def source_anchor(source, literal, conditions):
    line_text = f"data subject / {literal} /"
    lines = source.splitlines()
    if lines.count(line_text) != 1:
        raise ValueError("the diagnostic target must occupy one unique DATA line")
    line = lines.index(line_text) + 1
    start = line_text.index(literal) + 1
    body_start = start + 2
    positions = conditions["nondigit_positions"] + conditions["excluded_decimal_positions"]
    return dict(line=line, token_first_column=start, token_last_column=start+len(literal)-1,
                body_first_column=body_start, offending_body_positions=positions,
                offending_columns=[body_start+position-1 for position in positions],
                empty_body_insertion_column=body_start if conditions["empty"] else None)


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="boz_binary_octal", root=root)
        self.repairs = {}
        self.sources = {}
        self.control_sources = {}

    def add(self, rule, variant, facets, prefix, quote, body, prelude, diagnostic=None):
        name = identifier(rule, variant, diagnostic is not None)
        if name in self.cases:
            raise ValueError("duplicate case " + name)
        literal = token(prefix, quote, body)
        source = data_source(prelude, literal)
        state = lexical_conditions(prefix, body)
        anchor = source_anchor(source, literal, state)
        folder = "tests/fixtures/boz_binary_octal_" + name.lower()
        expectation = dict(phase="compile", step="source", outcome="diagnose" if diagnostic else "success")
        if diagnostic:
            expectation["diagnostic"] = dict(file="source.f90", line=anchor["line"],
                                            contains_any=diagnostic, excludes_any=EXCLUDED)
        evidence = "effect" if diagnostic else "positive-control"
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=list(facets), standard="f2023", evidence=evidence,
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=expectation)
        self.put(folder + "/source.f90", source)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.sources[name] = source
        self.cases[name] = dict(
            rule=rule, facets=list(facets), kind="invalid" if diagnostic else "valid",
            phase="compile", evidence=evidence, path=folder + "/fixture.json",
            prefix=prefix, radix=state["radix"], quote=quote, body=body, literal=literal,
            prelude=[dict(object=name, literal=value) for name, value in prelude],
            target_object="subject", lexical_conditions=state, source_anchor=anchor,
            receiver=dict(type="integer", kind="default", rank=0, pointer=False, allocatable=False,
                          dummy=False, automatic=False, other_initialization=False,
                          data_values_per_object=1),
            diagnostic_location_limit="Native manifest predicates enforce file/line. Exact token/body columns and the "
                                      "sole offending position are source-bound metadata, not an invented column matcher.")
        return name

    def control(self, rule, variant, facets, prefix, quote, body, prelude):
        if lexical_conditions(prefix, body)["owners"]:
            raise ValueError("control literal is not lexically conforming")
        source = data_source(prelude, token(prefix, quote, body))
        key = (rule, source)
        if key in self.control_sources:
            raise ValueError("identical same-primary control must be shared, not cloned")
        name = self.add(rule, variant, facets, prefix, quote, body, prelude)
        self.control_sources[key] = name
        return name

    def negative(self, rule, variant, facet, control, body):
        good = self.cases[control]
        if good["rule"] != rule or good["kind"] != "valid":
            raise ValueError("repair must have the same primary and a real valid control")
        prefix, quote = good["prefix"], good["quote"]
        conditions = lexical_conditions(prefix, body)
        if conditions["owners"] != [rule]:
            raise ValueError("negative has a wrong or competing lexical owner")
        if body:
            differing = [i for i, (a, b) in enumerate(zip(body, good["body"])) if a != b]
            if len(body) != len(good["body"]) or len(differing) != 1:
                raise ValueError("nonempty repair must change exactly one body character")
        elif good["body"] != "0":
            raise ValueError("empty-body repair must insert exactly0")
        prelude = [(item["object"], item["literal"]) for item in good["prelude"]]
        name = self.add(rule, variant, [facet], prefix, quote, body, prelude,
                        diagnostic_messages(prefix, body))
        wrong, repaired = self.cases[name]["literal"], good["literal"]
        source = self.sources[name]
        # Replace the targeted DATA statement, not an identical admitted prelude token.
        before = f"data subject / {wrong} /"
        after = f"data subject / {repaired} /"
        if source.count(before) != 1 or source.replace(before, after, 1) != self.sources[control]:
            raise ValueError("the DATA control is not the unique focused repair")
        self.repairs[name] = dict(
            control=control, file="source.f90", wrong=before, repaired=after,
            bad_literal=wrong, good_literal=repaired, body_before=body, body_after=good["body"],
            edit="insert0" if not body else "one-character-replacement",
            anchor=self.cases[name]["source_anchor"], cause=facet,
            other_conditions="Same complete declared default-INTEGER scalar DATA objects, unique one-value pairs, "
                             "prefix, matching quote kind and all valid prelude statements. No numeric value of the bad token.")


def grammar_cases(c, prefix):
    rule = RADICES[prefix][2]
    prelude = quotation_prelude(prefix)
    apostrophe = c.control(rule, "apostrophe_control", ELIGIBLE[rule], prefix, "'", "0", prelude)
    quotation = c.control(rule, "quotation_control", ["quotation-mark-form", "nonempty-digit-sequence"],
                           prefix, '"', "0", prelude)
    c.negative(rule, "empty_apostrophe", "nonempty-digit-sequence", apostrophe, "")
    c.negative(rule, "empty_quotation", "nonempty-digit-sequence", quotation, "")
    for name, char in [("letter", "A"), ("underscore", "_"), ("plus", "+"), ("minus", "-")]:
        c.negative(rule, "nondigit_" + name, "nondigit-body", apostrophe, char)


def digit_cases(c, prefix):
    rule = RADICES[prefix][3]
    prelude = alphabet_prelude(prefix)
    if prefix == "B":
        admission, exclusion = "zero-and-one-admissions", "other-decimal-digit-exclusion"
        good_digit, disallowed = "0", "23456789"
        interior_bad, interior_good = "1021", "1011"
    else:
        admission, exclusion = "zero-through-seven-admissions", "eight-and-nine-exclusion"
        good_digit, disallowed = "7", "89"
        interior_bad, interior_good = "1781", "1771"
    single = c.control(rule, "digit_control", [admission, exclusion], prefix, "'", good_digit, prelude)
    interior = c.control(rule, "interior_control", [admission, "interior-invalid-digit"],
                          prefix, "'", interior_good, prelude)
    for char in disallowed:
        c.negative(rule, "digit_" + char, exclusion, single, char)
    c.negative(rule, "interior_digit", "interior-invalid-digit", interior, interior_bad)


def build_corpus(root=ROOT):
    c = Corpus(root)
    for prefix in ("B", "O"):
        grammar_cases(c, prefix)
        digit_cases(c, prefix)
    if c.coverage() != {rule: set(facets) for rule, facets in ELIGIBLE.items()}:
        raise ValueError("coverage differs from the exact12 authorized facets")
    return c.files, c.cases, c.repairs


def synced_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    for requirement in result["requirements"]:
        cases = [s for s in specs.values() if s["rule"] == requirement["id"]]
        covered = {facet for case in cases for facet in case["facets"]}
        for facet in covered:
            if facet not in requirement["facets"]:
                raise ValueError("unknown lexical facet")
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - covered:
            raise ValueError("missing preserved pending plan: " + requirement["id"])
        if cases:
            negatives = sum(case["kind"] == "invalid" for case in cases)
            old = requirement["oracle"].split("\n\nFinite binary/octal implementation:", 1)[0]
            requirement["oracle"] = old + (
                f"\n\nFinite binary/octal implementation: {len(cases)} compile-only cases represent "
                f"{len(covered)} facets, with {negatives} diagnostic inputs and {len(cases)-negatives} "
                "shared positive controls. Distinct default-INTEGER scalars each have exactly one separate DATA value. "
                "Every negative changes only one target body character, or inserts0 into one closed empty body. "
                "Exact positions and decimal-versus-nondigit ownership are source-bound; no runtime numeric result "
                "or representation is asserted. Source/case/link/inventory adjudications are separate content-bound records.")
    return result


CONDITIONS = """## Source and exact finite scope

Authority: J3/24-007, 18 December 2023,688 physical PDF pages,
SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Original7.7 on PDF113-114 was read through the actual7.8 boundary before the
concrete inputs. All10base/83fine/93accounting units,9requirements and64facet IDs
are preserved. The independent source gate qualifies these plans; it does not
approve fixtures or processor observations.

Only R773/C7117/R774/C7118's twelve selected lexical facets advance. All files
are compile phase. A complete program declares ordinary default-INTEGER
scalars before its DATA statements. Each scalar has exactly one separate
DATA value, no other initialization, and no POINTER, ALLOCATABLE, dummy or
automatic-object condition. Source8.6.7p11 specifically requires INTEGER and
defines destination-kind INT conversion; no numerical result is checked here.

R773/R774 controls include the requested B"0"/B"1"/B"101" or
O"0"/O"7"/O"157" admissions on distinct scalars. Both closed empty quote forms
are repaired only by inserting0. Closed A, underscore, plus and minus bodies
are Fortran characters outside the decimal digit class and retain R773/R774
ownership. They are not C7117/C7118 decimal-value cases.

C7117 includes every disallowed decimal2..9 and the interior1021->1011
replacement. Its controls admit0/1 and mixed bodies in both quote forms.
C7118 controls contain every digit0..7 and a multidigit form;8/9 are repaired
to7, and1781->1771 changes only the interior8. No value is assigned by the
model or oracle to any invalid literal. The source position of the sole
offending character is explicit and all other body characters are valid.

Exactly identical same-primary controls are shared. Admitted prelude DATA
pairs are independent valid statements, never repeated initialization of the
target object. Only the subject DATA line changes in a repair. Existing
R605/S6/S10BOZ cases keep their owners and bytes; no copy is made to clear an
unselected wrapper, prefix or source-form facet.

## Cause and reporting qualification

Prospective predicates identify the BOZ/radix and empty-body, nondigit or
excluded-decimal property. Actual native wording is calibrated only when its
located message establishes that cause. Generic punctuation, syntax,
expected/error text, missing quote/EOF/END recovery, DATA count or receiver
errors, source echoes, unsupported wrappers and Internal/verifier/resource/
timeout failures are not corroboration. Reporting can occur with exit0 or a
nonzero exit; no fatal or printed-rule-code policy is introduced. Nonfatal
warnings require an explicit exact family/message/severity allowance if a
legitimate native observation warrants one.

The current manifest mechanism checks the source file and the one target
DATA line. Exact token columns, body offsets and offending-character
positions are preserved with source/repair metadata; this is not a claim
that a nonexistent column matcher was added to the shared harness.

Native calibration retains GNU's empty-set-of-digits message only for the
four actually empty bodies, not for its nonempty invalid-body recoveries.
Flang's qualified digit messages name the offending character and the entire
canonical BOZ token, including its radix prefix and body; they do not rely
on a source echo to supply the token. Generic illegal-character, unexpected
string and expected-DATA-delimiter reports remain uncredited. No warning
allowance or broader exclusion policy was added.

R772, R775/R776, C7119 and S7.7-001 remain pending. Source-form,
continuation/prefix/delimiter ambiguity, reuse/capacity/profile and numeric
interpretation contexts are not implemented. The source review's typed-REAL
array C7127 condition, REAL physical width/order and maximum-kind/enum
qualifications remain pending. No7.8 body or REAL/enum interpretation is
authored. The real-BOZ needs-oracle case and its profile are untouched.
"""


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def render_view(catalogue, specs, repairs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    total = sum(len(r["facets"]) for r in catalogue["requirements"])
    text = (
        "# Fortran 2023: 7.7 BOZ literals - binary/octal lexical implementation\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Current case/evidence adjudications remain separate content-bound records.\n\n"
        f"The finite corpus has **{len(specs)} compile-only cases**, **{len(repairs)} diagnostic inputs** "
        f"and **{len(specs)-len(repairs)} shared controls**. **{total-pending} of {total} facets are represented; "
        f"{pending} remain PENDING.** No runtime numeric or representation effect is claimed.\n\n"
        + CONDITIONS + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.7 -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    text += "<!-- END GENERATED 7.7 -->\n\n## Exact finite lexical case and repair census\n\n"
    text += "| Case | Primary / evidence | Subject token | Target line / body position | Minimal control |\n"
    text += "| --- | --- | --- | --- | --- |\n"
    for name, spec in specs.items():
        anchor = spec["source_anchor"]
        positions = anchor["offending_body_positions"]
        position = ",".join(map(str, positions)) if positions else "insert0" if not spec["body"] else "valid"
        control = repairs[name]["control"] if name in repairs else "positive control"
        text += f"| `{name}` | {spec['rule']} / {spec['evidence']} | `{spec['literal']}` | "
        text += f"{anchor['line']} / {position} | `{control}` |\n"
    text += "\n## Complete finite pending plans\n\n"
    text += "The following maps remain PENDING exactly as stored in canonical JSON. No canonical source or observation is automatically linked.\n\n"
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            text += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                text += f"* **`{facet}`** - {plan}\n"
            text += "\n"
    return text + (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_boz_binary_octal_fixtures.py --check` checks generated "
        "inputs, phase/facet/pending metadata and both document regions. Targeted regressions "
        "verify source digit tables, exact repairs/positions, DATA contexts, shared controls and "
        "role/location/nonfatal/failure predicates. Original and refreshed reports retain their "
        "exact fingerprints, modes, input hashes and command contexts. An index of current rows "
        "is not a combined processor run; f2018 passes are not f2023 qualification.\n\n"
        "This generator does not register the catalogue or renew source, fixture, link, inventory "
        "or baseline records. The original author packet excluded its local index overlay and "
        "preserved its1937 existing case bindings and nine links. Subsequent main registration "
        "and adjudication belong to the coordinator; their current states are in the registry "
        "and reports, not inferred from authorship.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, specs, repairs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs, repairs)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, b in files.items() if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob("boz_binary_octal_*/*") if p.is_file()}
        stale += [str(p.relative_to(ROOT)) for p in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale binary/octal packet: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(specs)} "
          f"compile cases, {len(repairs)} repairs and12 facets.")


if __name__ == "__main__":
    main()
