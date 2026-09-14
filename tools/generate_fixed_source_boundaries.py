#!/usr/bin/env python3
"""Generate the bounded 6.3.3 fixture matrix, without touching the calibration."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def initial(text):
    return "      " + text


def continued(text, indicator="1"):
    if len(indicator) != 1 or indicator in " 0":
        raise ValueError("A continuation needs one nonblank, nonzero indicator")
    return "     " + indicator + text


def program(declarations, body):
    return [initial("program p"), initial("implicit none"),
            *(initial(text) for text in declarations), *body,
            initial("end program p")]


def records(lines):
    encoded = []
    for line in lines:
        if len(line) > 72 or any(not 32 <= ord(char) <= 126 for char in line):
            raise ValueError(f"Not a printable ASCII record of at most 72 characters: {line!r}")
        if chr(36) in line:
            raise ValueError("The unprofiled fixtures do not assume a currency graphic")
        encoded.append(line.ljust(72).encode("ascii") + b"\n")
    return b"".join(encoded)


def matrix():
    outputs = {}

    def add(section, number, suffix, facets, lines, *, restriction=False,
            diagnostic=None, compile_only=False, parent=None, standard=""):
        kind = "invalid" if diagnostic else "valid"
        name = f"S6_3_3_{section}_{number:03d}_{kind}__{suffix}"
        folder = f"fixed_source_{section}_{number:03d}_{kind}_{suffix}"
        manifest = {
            "schema_version": 1,
            "id": name,
            "rule": f"S6.3.3.{section}-{number:03d}",
            "facets": facets,
            "evidence": "positive-control" if restriction and not diagnostic else "effect",
            "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran",
                       "form": "fixed", "output": "source.o"}],
        }
        assets = {"source.f90": records(lines)}
        if parent is not None:
            manifest["files"].insert(0, "parent.f90")
            manifest["build"].insert(0, {
                "id": "parent", "source": "parent.f90", "language": "fortran",
                "form": "fixed", "output": "parent.o",
            })
            manifest["build"][-1]["depends_on"] = ["parent"]
            assets["parent.f90"] = records(parent)
        if standard:
            manifest["standard"] = standard
        if diagnostic:
            manifest["expect"] = {
                "phase": "compile", "step": "source", "outcome": "diagnose",
                "diagnostic": {"file": "source.f90", **diagnostic},
            }
        elif compile_only:
            manifest["expect"] = {"phase": "compile", "step": "source", "outcome": "success"}
        else:
            manifest["link"] = {"objects": [step["output"] for step in manifest["build"]],
                                "output": "program"}
            manifest["expect"] = {"phase": "run", "outcome": "success", "exit_code": 0}
        assets["fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        for filename, content in assets.items():
            relative = Path(folder) / filename
            if relative in outputs:
                raise ValueError(f"Duplicate output: {relative}")
            outputs[relative] = content

    add(1, 1, "exact_width", ["exact-72", "content-in-column-72"], program(
        ["character(len=59) :: text"],
        [initial("text=repeat('?',59)"),
         initial("text='" + "A" * 58 + "Z'"),
         initial("if (text(1:58)/=repeat('A',58)) error stop 1"),
         initial("if (text(59:59)/='Z') error stop 2")]), restriction=True)

    add(1, 2, "tokens",
        ["keyword-interiors", "name-interiors", "constant-interiors", "operator-interiors"],
        [initial("p r o g r a m p"), initial("i m p l i c i t n o n e"),
         initial("i n t e g e r :: v a l u e"), initial("value=0"),
         initial("v a l u e=1 2 * * 2+1"),
         initial("i f (v a l u e . n e . 1 4 5) e r r o r s t o p 1"),
         initial("e n d p r o g r a m p")])
    add(1, 2, "format_spacing", ["format-spacing"], program(
        ["character(len=2) :: record", "integer :: ios"],
        [initial("record='??'"), initial("ios=99"),
         initial("write(record,10,iostat=ios) 7"),
         initial("if (ios/=0) error stop 1"),
         initial("if (record/=' 7') error stop 2"),
         "   10 format ( I   2 )"]))
    add(1, 2, "character_blanks", ["literal-blanks", "edit-descriptor-blanks"], program(
        ["character(len=4) :: text, record", "integer :: ios"],
        [initial("text='????'"), initial("record='????'"), initial("ios=99"),
         initial("text='a  b'"), initial("write(record,10,iostat=ios)"),
         initial("if (ios/=0) error stop 1"),
         initial("if (text(1:1)/='a'.or.text(4:4)/='b') error stop 2"),
         initial("if (text(2:3)/=repeat(' ',2)) error stop 3"),
         initial("if (record(1:1)/='a'.or.record(4:4)/='b') error stop 4"),
         initial("if (record(2:3)/=repeat(' ',2)) error stop 5"),
         "   10 format('a  b')"]))

    markers = ["C    ! error stop 91; count=91",
               "c    ; error stop 92; count=92",
               "*    ! error stop 93; count=93",
               *(" " * (column - 1) + "! error stop 94; count=94"
                 for column in range(1, 6)),
               "      ! error stop 95; count=95", " " * 71 + "!", ""]
    add(2, 1, "comment_markers",
        ["bang-columns-one-to-five", "bang-column-seven", "bang-column-72",
         "c-column-one", "asterisk-column-one", "all-blank-line", "before-unit",
         "within-unit", "after-unit"],
        [*markers, *program(["integer :: count"],
                           [initial("count=0"), *markers, initial("count=7"),
                            initial("if (count/=7) error stop 1")]), *markers])
    tail = "count=7! count=99; error stop 99"
    add(2, 1, "inline_comment",
        ["inline-comment", "comment-through-end", "noncomment-c-and-asterisk"], program(
            ["integer :: count"],
            [initial("count=0"), initial(tail + "!" * (66 - len(tail))),
             initial("count=count*2"),
             initial("if (count/=14) error stop 1")]))
    add(2, 1, "character_bang", ["literal-exception", "edit-descriptor-exception"], program(
        ["character(len=3) :: text, record", "integer :: ios"],
        [initial("text='???'"), initial("record='???'"), initial("ios=99"),
         initial("text='a!b'"), initial("write(record,10,iostat=ios)"),
         initial("if (ios/=0) error stop 1"),
         initial("if (text(1:1)/='a'.or.text(3:3)/='b') error stop 2"),
         initial("if (text(2:2)/='!') error stop 3"),
         initial("if (record(1:1)/='a'.or.record(3:3)/='b') error stop 4"),
         initial("if (record(2:2)/='!') error stop 5"),
         "   10 format('a!b')"]))
    add(2, 1, "bang_column_six", ["column-six-exception"], program(
        ["integer :: x"], [initial("x=0"), initial("x=1"), continued("+2", "!"),
                           initial("if (x/=3) error stop 1")]))

    add(3, 1, "indicator_classes",
        ["numeric-indicator", "punctuation-indicator", "letter-indicator",
         "column-seven", "indicator-excluded", "commentary-precedence"], program(
            ["integer :: x"],
            [initial("x=0"), "C    ; x=99", "*    ! x=98", "    !;x=97",
             *(continued("+1", char) for char in ("1", "9", "A", "a", "C", "c", "_", "&", "*", "!", ";")),
             initial("if (x/=11) error stop 1")]))
    add(3, 1, "initial_indicators", ["blank-initial", "zero-initial"], program(
        ["integer :: x, y"],
        [initial("x=0"), initial("y=0"), initial("x=1"), "     0x=2",
         initial("y=3"), initial("y=4"),
         initial("if (x/=2.or.y/=4) error stop 1")]))
    add(3, 1, "split_tokens", ["split-token"], program(
        ["integer :: value"],
        [initial("value=0"), initial("va"), continued("lue=1"), continued("2", "2"),
         initial("if (value/=12) error stop 1")]))
    add(3, 1, "literal_padding",
        ["continued-literal-padding", "column-seven", "column-72", "indicator-excluded"], program(
            ["character(len=61) :: text"],
            [initial("text=repeat('?',61)"), initial("text='A"), continued("B'", ";"),
             initial("if (text(1:1)/='A') error stop 1"),
             initial("if (text(2:60)/=repeat(' ',59)) error stop 2"),
             initial("if (text(61:61)/='B') error stop 3")]))
    orphan = ["C    ! A comment is not a preceding noncomment line.",
              continued("program p"), initial("implicit none"), initial("end program p")]
    add(3, 3, "orphan", ["preceding-noncomment-required"], orphan, restriction=True, diagnostic={
        "line": 2,
        "allow_nonfatal": [{"compiler": "flang", "severity": "warning",
                           "contains_any": ["Statement should not begin with a continuation line"]}],
    })
    add(3, 3, "orphan_repair", ["preceding-noncomment-required"],
        [orphan[0], initial("program p"), *orphan[2:]], restriction=True, compile_only=True)
    add(3, 2, "comment_intervention",
        ["comment-marker-is-inert", "following-initial-is-executable", "intervening-comment-kinds"],
        program(["integer :: x, sentinel"],
                [initial("x=0"), initial("sentinel=0"), initial("x=1"),
                 "C    ! +99", "*    ; +99", "    !1+99", "",
                 continued("+2"), "C    & sentinel=99", initial("sentinel=7"),
                 initial("if (x/=3) error stop 1"),
                 initial("if (sentinel/=7) error stop 2")]))

    add(4, 1, "line_and_comment", ["line-end", "inline-comment"], program(
        ["integer :: x"],
        [initial("x=0"), initial("x=2"), initial("x=x+5! x=99"),
         initial("if (x/=7) error stop 1")]))
    add(4, 1, "continued_comment", ["continued-exception"], program(
        ["integer :: x"],
        [initial("x=0"), initial("x=1! x=99"), "C     Intervening commentary.",
         continued("+2"), initial("if (x/=3) error stop 1")]))
    add(4, 2, "semicolon_runs", ["same-line-next", "blank-semicolon-runs", "trailing-runs"], program(
        ["integer :: x, y"],
        [initial("x=0; y=0"), initial("x=2;;;x=x+5; ; ;y=x+3;; ;"),
         initial("if (x/=7) error stop 1"),
         initial("if (y/=10) error stop 2")]))
    add(4, 2, "same_line_continued", ["same-line-continued"], program(
        ["integer :: x, y"],
        [initial("x=0; y=0"), initial("y=7; x=1"), continued("+2"),
         initial("if (x/=3.or.y/=7) error stop 1")]))
    add(4, 2, "semicolon_exceptions",
        ["literal-exception", "edit-descriptor-exception", "comment-exception", "column-six-exception"],
        program(["character(len=3) :: text, record", "integer :: ios, x"],
                [initial("text='???'"), initial("record='???'"), initial("ios=99"),
                 initial("x=0"), initial("text='a;b'! ;x=99"),
                 initial("write(record,10,iostat=ios)"),
                 initial("if (ios/=0) error stop 1"),
                 initial("if (text(1:1)/='a'.or.text(3:3)/='b') error stop 2"),
                 initial("if (text(2:2)/=';') error stop 3"),
                 initial("if (record(1:1)/='a'.or.record(3:3)/='b') error stop 4"),
                 initial("if (record(2:2)/=';') error stop 5"),
                 initial("x=1"), continued("+2", ";"),
                 initial("if (x/=3) error stop 6"), "   10 format('a;b')"]))
    for column, facet in ((7, "semicolon-in-column-seven"),
                          (12, "semicolon-after-statement-field-blanks")):
        bad = " " * (column - 1) + ";x=3"
        lines = program(["integer :: x"],
                        [initial("x=0"), bad, initial("if (x/=3) error stop 1")])
        add(4, 3, f"leading_c{column}", [facet], lines,
            restriction=True, diagnostic={
                "line": 5,
                "allow_nonfatal": [{"compiler": "flang", "severity": "portability",
                                   "contains_any": ["empty statement"]}],
            })
        repaired = list(lines)
        repaired[4] = bad.replace(";", " ", 1)
        add(4, 3, f"leading_c{column}_repair", [facet], repaired, restriction=True)

    labeled_body = [initial("count=0")]
    for column in range(1, 6):
        labeled_body += [initial(f"go to {column}"), initial("error stop 1"),
                         str(column).rjust(column).ljust(5) + " " + "count=count+1"]
    labeled_body += [initial("go to 100"), initial("error stop 2"),
                     "1 0 0 count=count+1",
                     initial("if (count/=6) error stop 3")]
    add(5, 1, "label_positions",
        ["label-in-each-field-position", "label-interior-blanks", "unlabeled-blank-field"],
        program(["integer :: count"], labeled_body), restriction=True)
    lines = program(["integer :: x"],
                    [initial("x=0"), "    X x=3", initial("if (x/=3) error stop 1")])
    add(5, 1, "nonlabel_field", ["nonlabel-field-character"], lines,
        restriction=True, diagnostic={"line": 5})
    repair = list(lines)
    repair[4] = initial("x=3")
    add(5, 1, "nonlabel_field_repair", ["nonlabel-field-character", "unlabeled-blank-field"],
        repair, restriction=True)
    lines = program(["integer :: x"],
                    [initial("x=0"), initial("10 continue"), initial("x=3"),
                     initial("if (x/=3) error stop 1")])
    add(5, 1, "label_in_statement", ["label-in-statement-field"], lines,
        restriction=True, diagnostic={
            "line": 5,
            "allow_nonfatal": [{"compiler": "flang", "severity": "portability",
                               "contains_any": ["Label digit is not in fixed-form label field"]}],
        })
    repair = list(lines)
    repair[4] = "   10 continue"
    add(5, 1, "label_in_statement_repair", ["label-in-statement-field"],
        repair, restriction=True)
    lines = program(["integer :: x"],
                    [initial("x=0"), initial("x=1"), "  20 1+2",
                     initial("if (x/=3) error stop 1")])
    add(5, 1, "continuation_label", ["continuation-field-label"], lines,
        restriction=True, diagnostic={"line": 6})
    repair = list(lines)
    repair[5] = continued("+2")
    add(5, 1, "continuation_label_repair", ["continuation-field-label", "continuation-blank-field"],
        repair, restriction=True)

    for length, facet in ((1000000, "statement-1000000"),
                          (1000001, "statement-1000001"),
                          (66 * 256 + 34, "more-than-255-continuations")):
        prefix, suffix = "s='", "'"
        literal_size = length - len(prefix) - len(suffix)
        statement = prefix + "A" * (literal_size - 1) + "Z" + suffix
        fields = [statement[offset:offset + 66] for offset in range(0, len(statement), 66)]
        if len(fields[-1]) == 66:
            raise ValueError("The final field must have room for a semicolon")
        fields[-1] += ";"
        logical_lines = [initial(fields[0]), *(continued(field) for field in fields[1:])]
        logical_lines.insert(128, "C     This line does not contribute statement characters.")
        lines = [initial("subroutine boundary(s)"), initial("implicit none"),
                 initial("character(*), intent(out) :: s"), *logical_lines,
                 initial("end subroutine boundary")]
        diagnostic = None
        if length == 1000001:
            diagnostic = {
                "line": 4,
                "end_line": 3 + len(logical_lines),
                "contains_any": ["statement is too long", "statement too long",
                                 "statement exceeds", "statement length", "statement limit",
                                 "too many characters in statement",
                                 "too many characters in a statement",
                                 "too many characters in the statement"],
            }
        add(5, 2, f"length_{length}", [facet], lines, restriction=True,
            diagnostic=diagnostic, compile_only=True, standard="f2023")

    unit_headers = {
        "main": ([initial("program p"), initial("implicit none")], "program p"),
        "external_subroutine": ([initial("subroutine boundary"), initial("implicit none")],
                                "subroutine boundary"),
        "external_function": ([initial("integer function boundary()"), initial("implicit none"),
                               initial("boundary=7")], "function boundary"),
        "module": ([initial("module boundary"), initial("implicit none")], "module boundary"),
        "block_data": ([initial("block data boundary"), initial("implicit none")],
                       "block data boundary"),
        "submodule": ([initial("submodule (ancestor) boundary"), initial("implicit none"),
                       initial("contains"), initial("module procedure seed"),
                       initial("end procedure seed")], "submodule boundary"),
    }
    parent_lines = [initial("module ancestor"), initial("implicit none"), initial("interface"),
                    initial("module subroutine seed()"), initial("end subroutine seed"),
                    initial("end interface"), initial("end module ancestor")]
    for unit, (header, end_suffix) in unit_headers.items():
        facet = unit.replace("_", "-") + "-end"
        parent = parent_lines if unit == "submodule" else None
        add(5, 3, f"continued_end_{unit}", [facet],
            [*header, initial("en"), continued("d " + end_suffix)],
            restriction=True, diagnostic={"line": len(header) + 1, "end_line": len(header) + 2},
            compile_only=True, parent=parent)
        add(5, 3, f"continued_end_{unit}_repair", [facet],
            [*header, initial("end " + end_suffix)],
            restriction=True, compile_only=True, parent=parent)
    add(5, 3, "internal_end", ["nonunit-end-control"],
        [initial("program p"), initial("implicit none"), initial("integer :: x"),
         initial("x=0"), initial("call inner(x)"), initial("if (x/=7) error stop 1"),
         initial("contains"), initial("subroutine inner(value)"),
         initial("integer, intent(out) :: value"), initial("value=7"), initial("en"),
         continued("d subroutine inner"), initial("end program p")], restriction=True)

    for suffix, first, rest, name, facet in (
            ("bare", "end", "value=7", "endvalue", "bare-end-prefix"),
            ("spaced", "e n d", "value=7", "endvalue", "spaced-end-prefix"),
            ("named", "end program p", "=7", "endprogramp", "named-end-prefix")):
        lines = program([f"integer :: {name}"],
                        [initial(name + "=0"), initial(first), continued(rest),
                         initial(f"if ({name}/=7) error stop 1")])
        add(5, 4, f"apparent_end_{suffix}", [facet], lines,
            restriction=True, diagnostic={"line": 5})
        repair = list(lines)
        repair[4] = initial("en")
        repair[5] = continued(name[2:] + "=7")
        add(5, 4, f"apparent_end_{suffix}_repair", [facet], repair, restriction=True)
    add(5, 4, "end_name", ["non-end-initial-control"], program(
        ["integer :: endvalue"],
        [initial("endvalue=0"), initial("endvalue"), continued("=7"),
         initial("if (endvalue/=7) error stop 1")]), restriction=True)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare generated bytes without writing")
    args = parser.parse_args()
    outputs = matrix()
    for relative, content in outputs.items():
        if len(relative.parts) != 2 or not relative.parts[0].startswith("fixed_source_"):
            raise ValueError(f"Output outside owned fixture namespace: {relative}")
        path = FIXTURES / relative
        if path.resolve() != path.absolute():
            raise ValueError(f"Output path contains a symlink: {path}")
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                raise SystemExit(f"Missing or stale generated fixture: {path}")
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(content)
    fixtures = sum(path.name == "fixture.json" for path in outputs)
    action = "Checked" if args.check else "Generated"
    print(f"{action} {fixtures} fixtures, {len(outputs)} files, "
          f"{sum(map(len, outputs.values()))} bytes; calibration untouched.")


if __name__ == "__main__":
    main()
