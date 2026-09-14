#!/usr/bin/env python3
"""Generate only the batch005 byte-sensitive free_source fixture inputs."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def manifest(name, rule, facets, evidence="effect", diagnostic=None, standard=""):
    data = {
        "schema_version": 1,
        "id": name,
        "rule": rule,
        "facets": facets,
        "evidence": evidence,
        "files": ["source.f90"],
        "build": [
            {"id": "source", "source": "source.f90", "language": "fortran",
             "form": "free", "output": "source.o"}
        ],
    }
    if standard:
        data["standard"] = standard
    if diagnostic is not None:
        data["expect"] = {
            "phase": "compile", "step": "source", "outcome": "diagnose",
            "diagnostic": {"file": "source.f90", **diagnostic},
        }
    else:
        data["link"] = {"objects": ["source.o"], "output": "program"}
        data["expect"] = {
            "phase": "run", "outcome": "success", "exit_code": 0,
            "stdout": "OK\n",
        }
    return (json.dumps(data, indent=2) + "\n").encode("ascii")


def outputs():
    result = {}

    def add(directory, lines, metadata):
        base = ROOT / "tests" / "fixtures" / directory
        source = b"\n".join(lines) + b"\n"
        if not source.isascii() or max(map(len, lines)) > 10000:
            raise ValueError(f"{directory}: invalid generated source repertoire or line size")
        result[base / "source.f90"] = source
        result[base / "fixture.json"] = metadata

    lines = [
        b"! Before the program unit: & ; '",
        b"",
        b"   ",
        b"program comment_lines",
        b"implicit none",
        b"! Between declaration statements.",
        b"integer :: value",
        b"value = -1",
        b"  ! A comment after leading blanks.",
        b"",
        b"   ",
        b"if (value /= -1) error stop 1",
    ]
    lines += [b"! value = 99 ; &"] * 300
    lines += [
        b"if (value /= -1) error stop 2",
        b"value = 7",
        b"if (value /= 7) error stop 3",
        b"print '(A)', 'OK'",
        b"end program",
        b"! After the program unit: & ; '",
        b"",
    ]
    add("free_source_comments_lines", lines, manifest(
        "S6_3_2_3_001_valid__raw_lines", "S6.3.2.3-001",
        ["bang-line", "blank-line", "empty-line", "inside-unit",
         "before-unit", "after-unit", "consecutive-lines"]))

    lines = [
        b"program continuation_chain",
        b"implicit none",
        b"character(len=257) :: s",
        b"integer :: i",
        b"s = '?'",
        b"s='x&",
    ]
    lines += [b"&x&"] * 255
    lines += [
        b"&Z'",
        b"if (len(s) /= 257) error stop 1",
        b"do i = 1, 256",
        b"  if (s(i:i) /= 'x') error stop 2",
        b"end do",
        b"if (s(257:257) /= 'Z') error stop 3",
        b"print '(A)', 'OK'",
        b"end program",
    ]
    add("free_source_continuation_256", lines, manifest(
        "S6_3_2_4_001_valid__256_continuations", "S6.3.2.4-001",
        ["long-chain"], standard="f2023"))

    lines = [
        b"program character_blanks",
        b"implicit none",
        b"character(len=8) :: a, b",
        b"character(len=7) :: record",
        b"character(len=5) :: data",
        b"integer :: ios",
        b"a='?'",
        b"b='?'",
        b"record='?'",
        b"data='?'",
        b"ios=-1",
        b"a='ab  &   ",
        b"    &  cd'",
        b'b="ef  &   ',
        b'    &  gh"',
        b"if (a /= 'ab    cd') error stop 1",
        b"if (b /= 'ef    gh') error stop 2",
        b"if (a(3:6) /= ' ' .or. a(7:8) /= 'cd') error stop 6",
        b"if (b(3:6) /= ' ' .or. b(7:8) /= 'gh') error stop 7",
        b"data='A&&",
        b"&!;B'",
        b"if (data /= 'A&!;B') error stop 3",
        b"if (iachar(data(2:2)) /= 38) error stop 8",
        b"if (iachar(data(3:3)) /= 33) error stop 9",
        b"if (iachar(data(4:4)) /= 59) error stop 10",
        b"write(record,100,iostat=ios)",
        b"if (ios /= 0) error stop 4",
        b"if (record /= 'ij    k') error stop 5",
        b"if (record(3:6) /= ' ' .or. record(7:7) /= 'k') error stop 11",
        b"100 format('ij  &   ",
        b"    &  k')",
        b"print '(A)', 'OK'",
        b"end program",
    ]
    add("free_source_character_blanks", lines, manifest(
        "S6_3_2_4_006_valid__raw_blanks", "S6.3.2.4-006",
        ["before-marker-blanks", "after-marker-blanks", "trailing-layout-blanks",
         "leading-layout-blanks", "both-literal-delimiters", "edit-descriptor",
         "ampersand-data"]))

    for statement_length in (1000000, 1000001):
        payload = b"x" * (statement_length - 5) + b"Z"
        chunks = [payload[i:i + 4000] for i in range(0, len(payload), 4000)]
        lines = [
            b"program statement_boundary",
            b"implicit none",
            b"integer, parameter :: k=selected_int_kind(9)",
            b"character(len=999997_k) :: s",
            b"integer(k) :: i",
            b"s='?'",
        ]
        statement_start = len(lines) + 1
        for i, chunk in enumerate(chunks):
            if i and i % 20 == 0:
                lines.append(b"! statement commentary")
            prefix = b"s='" if i == 0 else b"&"
            suffix = b"';!x" if i == len(chunks) - 1 else b"&"
            lines.append(prefix + chunk + suffix)
        diagnostic_line = len(lines)
        lines += [
            b"if (len(s,kind=k) /= 999997_k) error stop 1",
            b"do i=1_k,999995_k",
            b"  if (s(i:i) /= 'x') error stop 2",
            b"end do",
            b"if (s(999996_k:999996_k) /= 'Z') error stop 3",
            b"if (s(999997_k:999997_k) /= ' ') error stop 4",
            b"print '(A)', 'OK'",
            b"end program",
        ]
        invalid = statement_length > 1000000
        name = f"S6_3_2_6_002_{'invalid' if invalid else 'valid'}__{statement_length}"
        facets = ["one-over-limit"] if invalid else [
            "at-limit", "continuation-exclusion", "comment-exclusion", "terminator-exclusion"]
        diagnostic = None
        if invalid:
            diagnostic = {
                "line": statement_start, "end_line": diagnostic_line,
                "contains_any": ["statement is too long", "statement too long",
                                 "statement exceeds", "statement length", "statement limit",
                                 "too many characters in statement",
                                 "too many characters in a statement",
                                 "too many characters in the statement"],
            }
        add(f"free_source_statement_{statement_length}", lines, manifest(
            name, "S6.3.2.6-002", facets,
            evidence="effect" if invalid else "positive-control",
            diagnostic=diagnostic, standard="f2023"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare existing bytes without writing")
    args = parser.parse_args()
    generated = outputs()
    mismatches = []
    for path, expected in generated.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        parser.exit(1, "Generated fixtures differ or are missing:\n" + "\n".join(mismatches) + "\n")
    print(f"{'Checked' if args.check else 'Generated'} {len(generated)} owned fixture files.")


if __name__ == "__main__":
    main()
