#!/usr/bin/env python3
"""Generate only the byte-sensitive, manifest-backed section 6.4 fixtures."""
import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SYNTAX_MESSAGES = [
    "unclassifiable statement", "syntax error", "unexpected", "unrecognized statement",
    "invalid include", "malformed include", "expected character", "expected a character",
    "expected string", "expected a string", "only string", "not a character literal",
    "expected '=>'",
]
CONTINUATION_MESSAGES = SYNTAX_MESSAGES + [
    "continuation", "continued", "ampersand", "malformed path name string",
]
SOLE_LINE_MESSAGES = SYNTAX_MESSAGES + [
    "label", "semicolon", "not allowed", "not permitted", "extra characters",
    "non-comment text", "excess characters",
]
CYCLE_MESSAGES = ["recursive", "recursion", "cycle detected", "same source text"]
EXCESS_PATH_MESSAGES = ["excess characters after path name"]
EXCESS_PATH_WARNING = [{
    "compiler": "flang", "severity": "warning",
    "equals_any": ["excess characters after path name [-Wscanning]"],
}]


def records(lines, form):
    if form not in ("free", "fixed"):
        raise ValueError("Every source needs an explicit form")
    result = []
    for line in lines:
        if not line.isascii() or any(char in line for char in "\r\n\t") or chr(36) in line:
            raise ValueError("Fixtures require ASCII records without tabs or currency symbols")
        if form == "fixed":
            if len(line) > 72:
                raise ValueError(f"Overlong fixed record: {line!r}")
            line = line.ljust(72)
        elif len(line) > 10000:
            raise ValueError("Overlong free source record")
        result.append(line.encode("ascii") + b"\n")
    return b"".join(result)


def initial(form, text):
    return ("      " if form == "fixed" else "") + text


def program(form, body, expected=23, value=-9, declarations=()):
    before = [
        "program inclusion", "implicit none", "integer :: value",
        *declarations, f"value = {value}",
    ]
    after = [f"if (value /= {expected}) stop 1", "end program inclusion"]
    return [initial(form, line) for line in before] + body + [
        initial(form, line) for line in after
    ]


@dataclass
class IncludeCase:
    slug: str
    number: int
    form: str
    facets: List[str]
    files: Dict[str, bytes]
    rationale: str
    diagnostic: Optional[dict] = None
    repair_of: str = ""

    @property
    def kind(self):
        return "invalid" if self.diagnostic else "valid"

    @property
    def name(self):
        return f"S6_4_{self.number:03d}_{self.kind}__{self.slug}"

    @property
    def folder(self):
        return FIXTURES / f"include_{self.slug}_{self.kind}"

    @property
    def source(self):
        return "source.f" if self.form == "fixed" else "source.f90"

    @property
    def evidence(self):
        return "effect" if self.diagnostic or self.number == 5 else "positive-control"

    def manifest(self):
        result = {
            "schema_version": 1,
            "id": self.name,
            "rule": f"S6.4-{self.number:03d}",
            "facets": self.facets,
            "evidence": self.evidence,
            "files": [self.source] + sorted(set(self.files) - {self.source}),
            "build": [{
                "id": "source", "source": self.source, "language": "fortran",
                "form": self.form, "output": "source.o",
            }],
        }
        if self.diagnostic:
            result["expect"] = {
                "phase": "compile", "step": "source", "outcome": "diagnose",
                "diagnostic": self.diagnostic,
            }
        else:
            result["link"] = {"objects": ["source.o"], "output": "program"}
            result["expect"] = {
                "phase": "run", "outcome": "success", "exit_code": 0, "stdout": "",
            }
        return result

    def outputs(self):
        return {
            "fixture.json": (json.dumps(self.manifest(), indent=2) + "\n").encode("ascii"),
            **self.files,
        }


def build_cases():
    cases = []

    def add(slug, number, form, main, assets, facets, rationale, anchor=None,
            messages=None, repair_of="", allow_nonfatal=()):
        source = "source.f" if form == "fixed" else "source.f90"
        files = {source: records(main, form)}
        files.update({name: records(lines, form) for name, lines in assets.items()})
        diagnostic = None
        if anchor:
            filename, text = anchor
            filename = source if filename == "source" else filename
            matches = [
                number for number, line in enumerate(files[filename].decode("ascii").splitlines(), 1)
                if line.strip() == text.strip()
            ]
            if len(matches) != 1:
                raise ValueError(f"{slug}: the diagnostic needs one exact source record")
            diagnostic = {
                "file": filename, "line": matches[0], "contains_any": list(messages),
            }
            if allow_nonfatal:
                diagnostic["allow_nonfatal"] = list(allow_nonfatal)
        case = IncludeCase(slug, number, form, list(facets), files, rationale,
                           diagnostic, repair_of)
        cases.append(case)
        return case

    def pair(slug, number, form, bad_main, good_main, bad_assets, good_assets,
             bad_facets, good_facets, anchor, messages, violation, repair, allow_nonfatal=()):
        bad = add(slug, number, form, bad_main, bad_assets, bad_facets,
                  violation, anchor, messages, allow_nonfatal=allow_nonfatal)
        add(slug, number, form, good_main, good_assets, good_facets, repair,
            repair_of=bad.name)

    payload = {"payload.inc": ["value = 23"]}
    for slug, spelling, facets in (
        ("form_apostrophe", "INCLUDE 'payload.inc'", ["free-apostrophe", "case-equivalence"]),
        ("form_quotation", 'iNcLuDe "payload.inc"', ["free-quotation", "case-equivalence"]),
    ):
        add(slug, 1, "free", program("free", [spelling]), payload, facets,
            "A complete default-character literal references the staged sidecar; value is 23.")
    add("form_fixed_blanks", 1, "fixed",
        program("fixed", ["      I N C L U D E'payload.inc'"]),
        {"payload.inc": ["      value = 23"]},
        ["fixed-blank-spelling"],
        "Fixed-form blanks outside character context are insignificant; all records have 72 characters.")
    add("form_name", 1, "free",
        program("free", ["include = 10", "include 'payload.inc'", "value = include"],
                expected=12, declarations=["integer :: include"]),
        {"payload.inc": ["include = include + 2"]}, ["include-name-context"],
        "The included assignment uses include as a name rather than recursively treating it as a directive.")
    add("form_context", 1, "free",
        program("free", [
            "value = 0",
            'directive = "#include \'payload.inc\'"',
            "! include 'payload.inc'",
            "include 'payload.inc'",
            "if (len_trim(directive) /= 22) stop 2",
        ], expected=1, declarations=["character(len=32) :: directive"]),
        {"payload.inc": ["value = value + 1"]}, ["comment-literal-context"],
        "Comment and literal INCLUDE spellings do not insert the payload; only the actual line adds one.")
    for slug, spelling, declarations, facet, violation, repair in (
        ("form_nonliteral", "include part",
         ["character(len=*), parameter :: part = 'payload.inc'"],
         "nonliteral-source-diagnostic",
         "A declared named character constant is not the char-literal-constant required by p1.",
         "Replace just part on the INCLUDE line by the literal 'payload.inc'; the value becomes 23."),
        ("form_expression", "include 'payload.inc' // ''", [],
         "expression-source-diagnostic",
         "Concatenation is an expression, not one char-literal-constant; the intended sidecar exists.",
         "Remove only the concatenation with the empty literal; the value becomes 23."),
    ):
        pair(slug, 1, "free",
             program("free", [spelling], declarations=declarations),
             program("free", ["include 'payload.inc'"], declarations=declarations),
             payload, payload, [facet], ["free-apostrophe"],
             ("source", spelling),
             SYNTAX_MESSAGES + (EXCESS_PATH_MESSAGES if slug == "form_expression" else []),
             violation, repair,
             allow_nonfatal=EXCESS_PATH_WARNING if slug == "form_expression" else ())

    declarations = ["integer, parameter :: ck = kind('a')"]
    pair("named_kind", 2, "free",
         program("free", ["include ck_'payload.inc'"], declarations=declarations),
         program("free", ["include 'payload.inc'"], declarations=declarations),
         payload, payload, ["named-kind-diagnostic"], ["omitted-kind-control"],
         ("source", "include ck_'payload.inc'"), SYNTAX_MESSAGES + ["kind parameter", "kind-param"],
         "ck is declared and has a supported character kind, but p2 forbids a named INCLUDE kind selector.",
         "Remove only ck_ from the INCLUDE literal; retain the supported parameter declaration and check 23.")

    for slug, form, split, facet in (
        ("split_tokens_free", "free", ["include &", "& 'payload.inc'"],
         "free-token-continuation-diagnostic"),
        ("split_literal_free", "free", ["include 'pay&", "&load.inc'"],
         "free-literal-continuation-diagnostic"),
        ("split_fixed", "fixed", ["      include", "     &'payload.inc'"],
         "fixed-continuation-diagnostic"),
    ):
        included = {"payload.inc": [initial(form, "value = 23")]}
        pair(slug, 3, form, program(form, split),
             program(form, [initial(form, "include 'payload.inc'")]),
             included, included, [facet], [f"{form}-single-line", "statement-position"],
             ("source", split[0]), CONTINUATION_MESSAGES,
             "p3/p4 do not allow the attempted INCLUDE to occupy two physical source records.",
             "Join only the split INCLUDE records, preserving the intended filename and value 23.")

    for form in ("free", "fixed"):
        included = {"payload.inc": [initial(form, "value = 23")]}
        label = "10 include 'payload.inc'" if form == "free" else "   10 include 'payload.inc'"
        pair(f"label_{form}", 4, form, program(form, [label]),
             program(form, [initial(form, "include 'payload.inc'")]),
             included, included, [f"label-{form}-diagnostic"], [f"sole-line-{form}"],
             ("source", label), SOLE_LINE_MESSAGES,
             "The otherwise well-formed label is on INCLUDE, which p4 explicitly forbids.",
             "Remove only the INCLUDE label and retain the included assignment to 23.")
        for side in ("before", "after"):
            if side == "before":
                text = "value = 0; include 'payload.inc'"
                repaired = ["value = 0", "include 'payload.inc'"]
                expected = 23
            else:
                text = "include 'payload.inc'; value = value + 1"
                repaired = ["include 'payload.inc'", "value = value + 1"]
                expected = 24
            bad_line = initial(form, text)
            pair(f"semicolon_{side}_{form}", 4, form,
                 program(form, [bad_line], expected=expected),
                 program(form, [initial(form, line) for line in repaired], expected=expected),
                 included, included, [f"semicolon-{side}-{form}-diagnostic"], [f"sole-line-{form}"],
                 ("source", bad_line), SOLE_LINE_MESSAGES,
                 "p4 excludes another statement on the INCLUDE source record, despite an ordinary semicolon.",
                 "Replace only the semicolon boundary by a new initial source record; retain the arithmetic.",
                 allow_nonfatal=EXCESS_PATH_WARNING if side == "after" else ())
        comment_line = initial(form, "  include   'payload.inc'   ! trailing comment &")
        add(f"trailing_comment_{form}", 4, form, program(form, [comment_line]),
            included, [f"trailing-comment-{form}", "leading-trailing-blanks", f"sole-line-{form}"],
            "Blanks and a real trailing comment are permitted; the comment ampersand does not continue INCLUDE.")
    pair("two_includes", 4, "free",
         program("free", ["include 'payload.inc'; include 'payload.inc'"], expected=2, value=0),
         program("free", ["include 'payload.inc'", "include 'payload.inc'"], expected=2, value=0),
         {"payload.inc": ["value = value + 1"]}, {"payload.inc": ["value = value + 1"]},
         ["two-includes-diagnostic"], ["sole-line-free"],
         ("source", "include 'payload.inc'; include 'payload.inc'"), SOLE_LINE_MESSAGES,
         "p4 permits neither two INCLUDE forms nor their semicolon on the same physical line.",
         "Replace only the semicolon boundary by a new source record; two completed insertions produce 2.",
         allow_nonfatal=EXCESS_PATH_WARNING)
    pair("action_if", 4, "free",
         program("free", ["if (.true.) include 'payload.inc'"]),
         program("free", ["if (.true.) then", "include 'payload.inc'", "end if"]),
         payload, payload, ["action-if-diagnostic"], ["sole-line-free"],
         ("source", "if (.true.) include 'payload.inc'"), SOLE_LINE_MESSAGES,
         "INCLUDE is not an action statement, and the IF prefix violates p4's sole-text condition.",
         "Use the minimal block IF so INCLUDE occupies its own source record; the value is 23.")

    add("replacement_declarations", 5, "free", [
        "program inclusion", "implicit none", "include 'declarations.inc'",
        "value = -9", "value = answer + 2", "if (value /= 37) stop 1",
        "end program inclusion",
    ], {"declarations.inc": ["integer, parameter :: answer = 35", "integer :: value"]},
        ["specification-text"], "Inserted declarations participate in normal processing; the result is 37.")
    add("replacement_order", 5, "free",
        program("free", ["include 'step.inc'", "value = value * 3", "include 'step.inc'"],
                expected=19, value=1),
        {"step.inc": ["value = value * 2 + 1"]},
        ["executable-order", "repeated-nonrecursive-text"],
        "Two completed insertions preserve their positions around host arithmetic: (1*2+1)*3*2+1 = 19.")
    add("replacement_construct", 5, "free",
        program("free", ["include 'open.inc'", "end if"], expected=7, value=5),
        {"open.inc": ["if (value == 5) then", "value = value + 2"]},
        ["partial-construct"],
        "A complete included statement need not close its construct; the host END IF completes the value-7 path.")
    add("replacement_procedure", 5, "free", [
        "program inclusion", "implicit none", "integer :: value", "value = -9",
        "value = answer()", "if (value /= 43) stop 1", "contains",
        "include 'procedure.inc'", "end program inclusion",
    ], {"procedure.inc": [
        "integer function answer()", "implicit none", "answer = 43", "end function answer",
    ]}, ["contained-subprogram"],
        "The inserted contained function has a defined result and returns the independent value 43.")
    add("replacement_unit", 5, "free", ["include 'whole.inc'"],
        {"whole.inc": program("free", ["value = 47"], expected=47)},
        ["whole-program-unit"],
        "The driver consists solely of INCLUDE; substitution supplies the entire value-47 main program.")
    add("replacement_fixed", 5, "fixed",
        program("fixed", ["      include 'payload.inc'"], expected=21, value=0),
        {"payload.inc": [
            "C Included text uses fixed form",
            "      value = 10", "     &+ 11", "      go to 20",
            "      value = -3", "   20 continue",
        ]}, ["fixed-form-text"],
        "All records have 72 characters; continuation and a label inside the included text are legal and yield 21.")
    add("replacement_nested", 5, "free",
        program("free", ["include 'outer.inc'"], expected=45, value=1),
        {"outer.inc": ["value = value + 2", "include 'inner.inc'", "value = value * 3"],
         "inner.inc": ["value = value * 5"]},
        ["nested-replacement"],
        "Nested replacement preserves ordering before further processing: (1+2)*5*3 = 45; depth is only two.")
    add("replacement_empty_comments", 5, "free",
        program("free", ["include 'empty.inc'", "include 'comments.inc'"], expected=17, value=17),
        {"empty.inc": [], "comments.inc": ["! Only commentary", "", "! A comment ending in &"]},
        ["empty-text", "comment-only-text"],
        "The empty asset has zero bytes; comment-only insertion has no statement boundary and leaves 17 unchanged.")

    for slug, main_name, bad_assets, good_assets, closing_file, closing_text, bad_facet, good_facet in (
        ("cycle_direct", "loop.inc", {"loop.inc": ["include 'loop.inc'"]},
         {"loop.inc": ["value = value + 1"]}, "loop.inc", "include 'loop.inc'",
         "direct-cycle-diagnostic", "acyclic-direct-control"),
        ("cycle_indirect", "first.inc",
         {"first.inc": ["include 'second.inc'"], "second.inc": ["include 'first.inc'"]},
         {"first.inc": ["include 'second.inc'"], "second.inc": ["value = value + 1"]},
         "second.inc", "include 'first.inc'",
         "indirect-cycle-diagnostic", "acyclic-indirect-control"),
    ):
        main = program("free", [f"include '{main_name}'"], expected=1, value=0)
        pair(slug, 6, "free", main, main, bad_assets, good_assets, [bad_facet], [good_facet],
             (closing_file, closing_text), CYCLE_MESSAGES,
             "The anchored edge includes source that is already active, violating p5 at this nesting level.",
             "Replace only the edge closing the cycle by an increment; retain the same driver and check 1.")
    add("sibling_reuse", 6, "free",
        program("free", ["include 'first.inc'", "include 'second.inc'"], expected=3, value=0),
        {"first.inc": ["include 'leaf.inc'", "value = value + 1"],
         "second.inc": ["include 'leaf.inc'"], "leaf.inc": ["value = value + 1"]},
        ["sibling-reuse-control"],
        "The leaf is reused after its first expansion completes, not during its own expansion; the result is 3.")

    for form, nested in (("free", False), ("fixed", False), ("free", True)):
        flavor = "nested" if nested else form
        filename = "inner.inc" if nested else "payload.inc"
        source_reference = "outer.inc" if nested else filename
        start = initial(form, "value = 10 &" if form == "free" else "value = 10")
        continuation = "& + 2" if form == "free" else "     &+ 2"
        leading = ["! Leading comment", ""] if form == "free" else ["C Leading comment", ""]
        trailing = ["! Trailing comment", ""] if form == "free" else ["C Trailing comment", ""]
        nested_asset = {"outer.inc": [f"include '{filename}'"]} if nested else {}
        include_line = initial(form, f"include '{source_reference}'")
        pair(f"first_{flavor}", 7, form,
             program(form, [start, include_line], expected=12),
             program(form, [include_line], expected=12),
             {filename: leading + [continuation] + trailing, **nested_asset},
             {filename: leading + [start, continuation] + trailing, **nested_asset},
             [f"{flavor}-first-continuation-diagnostic", "leading-comments"],
             [f"{flavor}-internal-continuation-control", "leading-comments"],
             (filename, continuation), CONTINUATION_MESSAGES,
             "After resolution the first included statement line continues a host statement; comments cannot hide it.",
             "Move the initial host statement record into the included asset just before its continuation; check 12.")
        pair(f"last_{flavor}", 8, form,
             program(form, [include_line, continuation], expected=12),
             program(form, [include_line], expected=12),
             {filename: leading + [start] + trailing, **nested_asset},
             {filename: leading + [start, continuation] + trailing, **nested_asset},
             [f"{flavor}-last-continuation-diagnostic", "trailing-comments"],
             [f"{flavor}-contained-statement-control", "trailing-comments"],
             (filename, start), CONTINUATION_MESSAGES,
             "The last resolved included statement is continued by a host record, despite trailing commentary.",
             "Move only the completing host record into the included asset before its trailing comments; check 12.")
    add("last_comment_ampersand", 8, "free",
        program("free", ["include 'payload.inc'"]),
        {"payload.inc": ["value = 23 ! &", "! Trailing comment &"]},
        ["comment-ampersand-control"],
        "The final statement is complete; both ampersands occur in comments and the result is 23.")
    return cases


def materialize(cases, check=False):
    names = set()
    for case in cases:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", case.slug) or case.name in names:
            raise ValueError(f"Invalid or duplicate generated fixture: {case.name}")
        names.add(case.name)
        folder = case.folder
        if folder.resolve().parent != FIXTURES.resolve() or folder.is_symlink():
            raise ValueError(f"Fixture output escapes owned include directory: {folder}")
        outputs = case.outputs()
        if folder.exists():
            present = {path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()}
            extra = present - outputs.keys()
            if extra:
                raise ValueError(f"{folder}: unexpected assets {sorted(extra)}")
        elif not check:
            folder.mkdir()
        for name, data in outputs.items():
            if not re.fullmatch(r"[a-z][a-z0-9_.]*", name):
                raise ValueError(f"Only flat owned fixture assets may be written: {name}")
            path = folder / name
            if path.resolve().parent != folder.resolve() or path.is_symlink():
                raise ValueError(f"Asset output escapes its fixture: {path}")
            if check:
                if not path.is_file() or path.read_bytes() != data:
                    raise ValueError(f"Generated fixture is missing or stale: {path}")
            elif not path.exists() or path.read_bytes() != data:
                path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check exact bytes without writing")
    args = parser.parse_args()
    cases = build_cases()
    materialize(cases, check=args.check)
    counts = Counter((case.kind, case.evidence) for case in cases)
    assets = sum(len(case.files) for case in cases)
    print(f"{'Checked' if args.check else 'Generated'} {len(cases)} INCLUDE fixtures, {assets} declared assets.")
    print("; ".join(f"{kind}/{evidence}: {count}" for (kind, evidence), count in sorted(counts.items())))


if __name__ == "__main__":
    main()
