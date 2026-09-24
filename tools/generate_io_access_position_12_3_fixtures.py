#!/usr/bin/env python3
"""Generate Clause 12.3.3/12.3.4.1 external-file access and position fixtures."""
import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "io_access_position_12_3"
CATALOGUES = {
    "12.3.3.1": "doc/catalogues/file_access_methods_12_3_3_1.json",
    "12.3.3.2": "doc/catalogues/sequential_access_12_3_3_2.json",
    "12.3.3.3": "doc/catalogues/direct_access_12_3_3_3.json",
    "12.3.3.4": "doc/catalogues/stream_access_12_3_3_4.json",
    "12.3.4.1": "doc/catalogues/file_position_concepts_12_3_4_1.json",
}
VIEWS = {
    "12.3.3.1": "doc/fortran_2023_12_3_3_1.md",
    "12.3.3.2": "doc/fortran_2023_12_3_3_2.md",
    "12.3.3.3": "doc/fortran_2023_12_3_3_3.md",
    "12.3.3.4": "doc/fortran_2023_12_3_3_4.md",
    "12.3.4.1": "doc/fortran_2023_12_3_4_1.md",
}
VIEW_TITLES = {
    "12.3.3.1": "File access methods",
    "12.3.3.2": "Sequential access",
    "12.3.3.3": "Direct access",
    "12.3.3.4": "Stream access",
    "12.3.4.1": "File position concepts",
}

CHECKS = """
module io_access_position_checks
use iso_fortran_env, only: iostat_end
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, finish_checks, iostat_end
contains
subroutine fail(label)
character(*), intent(in) :: label
print *, 'CHECK_FAILED', label
error stop 99
end subroutine fail
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
print *, 'CHECK_INT', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 1
end if
checked = checked + 1
end subroutine check_int
subroutine check_char(label, actual, expected)
character(*), intent(in) :: label
character(*), intent(in) :: actual, expected
if (len(actual) /= len(expected)) then
print *, 'CHECK_CHAR_LEN', label, len(actual), len(expected)
error stop 2
end if
if (actual /= expected) then
print *, 'CHECK_CHAR', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 3
end if
checked = checked + 1
end subroutine check_char
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) call fail(label)
checked = checked + 1
end subroutine check_true
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 4
end if
end subroutine finish_checks
end module io_access_position_checks
""".lstrip()


def body(text):
    return textwrap.dedent(text).strip() + "\n"


READ_TARGET = re.compile(r"^(?P<indent>\s*)read\s*\(.*\)\s*(?P<target>[A-Za-z]\w*)\s*$", re.I)
INTEGER_DECL = re.compile(r"^\s*integer\s*::\s*(?P<names>.+)$", re.I)
CHARACTER_DECL = re.compile(r"^\s*character\s*\(\s*len\s*=\s*(?P<len>\d+)\s*\)\s*::\s*(?P<names>.+)$", re.I)
CHAR_SENTINELS = "#@$%&?+*/;:<>=^~|[]{}"


def declaration_types(lines):
    result = {}
    for line in lines:
        match = INTEGER_DECL.match(line)
        if match:
            for item in match.group("names").split(","):
                result[item.strip()] = ("integer", None)
            continue
        match = CHARACTER_DECL.match(line)
        if match:
            length = int(match.group("len"))
            for item in match.group("names").split(","):
                result[item.strip()] = ("character", length)
    return result


def find_read_expected(lines, index, target, category):
    pattern = (re.compile(r"call check_int\('[^']+',\s*" + re.escape(target) + r"\s*,\s*([^)\s]+)\)", re.I)
               if category == "integer"
               else re.compile(r"call check_char\('[^']+',\s*" + re.escape(target) + r"\s*,\s*('[^']*')\)", re.I))
    for next_line in lines[index + 1:index + 8]:
        if READ_TARGET.match(next_line):
            break
        match = pattern.search(next_line)
        if match:
            return match.group(1)
    raise ValueError(f"read target {target} has no following value oracle")


def add_pre_read_guards(main):
    lines = main.splitlines()
    types = declaration_types(lines)
    output = []
    probes = []
    read_index = 0
    for index, line in enumerate(lines):
        match = READ_TARGET.match(line)
        if not match:
            output.append(line)
            continue
        target = match.group("target")
        if target not in types:
            raise ValueError(f"read target {target} has no known declaration")
        category, length = types[target]
        expected = find_read_expected(lines, index, target, category)
        read_index += 1
        indent = match.group("indent")
        for previous in range(len(output) - 1, -1, -1):
            if re.match(r"^\s*" + re.escape(target) + r"\s*=", output[previous], re.I):
                output.pop(previous)
                break
        label = f"pre-read-{read_index}-{target}"
        if category == "integer":
            sentinel = f"-{7000 + read_index}"
            poison = f"-{8000 + read_index}"
            default = "0"
            if expected == sentinel:
                raise ValueError(f"{label}: expected value equals sentinel")
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_int('{label}', {target}, {sentinel})")
        else:
            mark = CHAR_SENTINELS[(read_index - 1) % len(CHAR_SENTINELS)]
            sentinel = "'" + (mark * length) + "'"
            poison = "'" + ("!" * length) + "'"
            default = "'" + (" " * length) + "'"
            if expected == sentinel:
                raise ValueError(f"{label}: expected value equals sentinel")
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_char('{label}', {target}, {sentinel})")
        probes.extend([
            (f"{label}-remove-sentinel-init", sentinel_line, f"{indent}! sentinel initializer removed for probe", "sentinel"),
            (f"{label}-expected-sentinel-init", sentinel_line, f"{indent}{target} = {expected}", "sentinel"),
            (f"{label}-default-sentinel-init", sentinel_line, f"{indent}{target} = {default}", "sentinel"),
        ])
        output.append(line)
    return "\n".join(output) + "\n", probes


def source(body_text, count):
    main, probes = add_pre_read_guards(body(body_text))
    total = count + sum(1 for _, _, _, category in probes if category == "sentinel") // 3
    src = CHECKS + "program p\nuse io_access_position_checks\nimplicit none\n" + main
    src += f"call finish_checks({total})\nend program p\n"
    return src, total, probes


def ident(rule, variant):
    return rule.replace('.', '_').replace('-', '_') + "_valid__" + TOPIC + "_" + variant


class Corpus:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.files = {}
        self.cases = {}

    def put(self, rel, content):
        path = self.root / rel
        raw = content.encode("ascii")
        if path.suffix == ".f90" and max(map(len, raw.splitlines()), default=0) > 132:
            raise ValueError(f"line too long in {rel}")
        self.files[path] = raw

    def add(self, section, rule, variant, facets, body_text, checks, derivation, mutants):
        name = ident(rule, variant)
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src, total_checks, sentinel_probes = source(body_text, checks)
        manifest = {
            "schema_version": 1,
            "id": name,
            "rule": rule,
            "facets": list(facets),
            "standard": "f2023",
            "evidence": "effect",
            "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0},
        }
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        normalized_mutants = [
            (mid, textwrap.dedent(old).strip("\n"), textwrap.dedent(new).strip("\n"), "feature")
            for mid, old, new in mutants
        ] + sentinel_probes
        for item in normalized_mutants:
            if item[1] not in src:
                raise ValueError(f"{name}: mutant span not found: {item[0]}")
            if src.count(item[1]) != 1:
                raise ValueError(f"{name}: mutant span not unique: {item[0]}")
        self.cases[name] = {
            "section": section,
            "rule": rule,
            "variant": variant,
            "facets": list(facets),
            "path": folder + "/fixture.json",
            "source_path": folder + "/source.f90",
            "checks": total_checks,
            "derivation": derivation,
            "mutants": [{"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in normalized_mutants],
        }

    def coverage(self):
        result = {}
        for case in self.cases.values():
            result.setdefault(case["rule"], set()).update(case["facets"])
        return result


def build_corpus(root=ROOT):
    c = Corpus(root)
    c.add("12.3.3.1", "S12.3.3.1-001", "three_methods",
          ["sequential-access-method", "direct-access-method", "stream-access-method"], """
        integer :: u, ios, recl, sample, value, char_units, stream_second
        character(len=1) :: ch
        sample = 0
        inquire(iolength=recl) sample
        inquire(iolength=char_units) ch
        stream_second = 1 + char_units
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 31
        write(u,'(i0)') 32
        rewind u
        value = -91
        read(u,*,iostat=ios) value
        call check_int('sequential-access-method-status', ios, 0)
        call check_int('sequential-access-method-value', value, 31)
        close(u, status='delete')
        open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
        write(u,rec=2) 52
        write(u,rec=1) 51
        value = -92
        read(u,rec=2,iostat=ios) value
        call check_int('direct-access-method-status', ios, 0)
        call check_int('direct-access-method-value', value, 52)
        close(u, status='delete')
        open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
        write(u,pos=stream_second) 'T'
        write(u,pos=1) 'S'
        ch = '#'
        read(u,pos=stream_second,iostat=ios) ch
        call check_int('stream-access-method-status', ios, 0)
        call check_char('stream-access-method-value', ch, 'T')
        close(u, status='delete')
    """, 6,
          "12.3.3.1 p1 defines sequential, direct and stream methods; the fixture uses one scratch external file connection of each access method and observes data by that method.",
          [("sequential-backspace-not-rewind", "        rewind u", "        backspace u"),
           ("direct-read-other-rec", "        read(u,rec=2,iostat=ios) value", "        read(u,rec=1,iostat=ios) value"),
           ("stream-read-other-pos", "        read(u,pos=stream_second,iostat=ios) ch", "        read(u,pos=1,iostat=ios) ch")])

    c.add("12.3.3.1", "S12.3.3.1-003", "access_method_connection",
          ["access-method-determined-at-connection"], """
        integer :: u, ios, recl, sample, value, char_units
        character(len=10) :: access_name
        character(len=1) :: ch
        character(len=*), parameter :: fname = 'io_access_position_12_3_connection.dat'
        sample = 0
        inquire(iolength=recl) sample
        inquire(iolength=char_units) ch
        open(newunit=u, file=fname, status='replace', access='sequential', form='formatted', action='readwrite')
        inquire(unit=u, access=access_name)
        call check_char('sequential-connection-access', access_name, 'SEQUENTIAL')
        write(u,'(i0)') 37
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('sequential-connection-read-status', ios, 0)
        call check_int('sequential-connection-read-value', value, 37)
        close(u)
        open(newunit=u, file=fname, status='replace', access='direct', form='unformatted', recl=recl, action='readwrite')
        inquire(unit=u, access=access_name)
        call check_char('direct-connection-access', access_name, 'DIRECT    ')
        write(u,rec=1) 73
        value = -2
        read(u,rec=1,iostat=ios) value
        call check_int('direct-connection-read-status', ios, 0)
        call check_int('direct-connection-read-value', value, 73)
        close(u)
        open(newunit=u, file=fname, status='replace', access='stream', form='unformatted', action='readwrite')
        inquire(unit=u, access=access_name)
        call check_char('stream-connection-access', access_name, 'STREAM    ')
        write(u,pos=1 + char_units) 'V'
        ch = '#'
        read(u,pos=1 + char_units,iostat=ios) ch
        call check_int('stream-connection-read-status', ios, 0)
        call check_char('stream-connection-read-value', ch, 'V')
        close(u, status='delete')
    """, 9,
          "12.3.3.1 p2 says access method is determined when the file is connected; the same run-directory file name is connected sequential, direct, and stream, with INQUIRE(ACCESS=) and method-specific read-back each time.",
          [("connection-method-changed", "        open(newunit=u, file=fname, status='replace', access='sequential', form='formatted', action='readwrite')",
            "        open(newunit=u, file=fname, status='replace', access='stream', form='formatted', action='readwrite')")])

    c.add("12.3.3.2", "S12.3.3.2-001", "sequential_order",
          ["sequential-access-records-in-order"], """
        integer :: u, ios, first, second
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 41
        write(u,'(i0)') 73
        rewind u
        first = -11
        second = -12
        read(u,*,iostat=ios) first
        call check_int('first-record-status', ios, 0)
        call check_int('first-record-value', first, 41)
        read(u,*,iostat=ios) second
        call check_int('second-record-status', ios, 0)
        call check_int('second-record-value', second, 73)
        close(u, status='delete')
    """, 4,
          "12.3.3.2 p1 defines sequential access as record access in order; after REWIND the two records are read as written.",
          [("drop-rewind", "        rewind u", "        backspace u")])

    c.add("12.3.3.2", "S12.3.3.2-007", "sequential_endfile",
          ["sequential-final-endfile-record-permitted"], """
        integer :: u, ios, value
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 81
        endfile u
        rewind u
        value = -81
        read(u,*,iostat=ios) value
        call check_int('data-before-endfile-status', ios, 0)
        call check_int('data-before-endfile-value', value, 81)
        read(u,*,iostat=ios)
        call check_int('final-endfile-status', ios, iostat_end)
        close(u, status='delete')
    """, 3,
          "12.3.3.2 p2 permits the last sequential record to be an endfile record; after the data record, the next read returns IOSTAT_END.",
          [("replace-endfile-with-data", "        endfile u", "        write(u,'(i0)') 82")])

    c.add("12.3.3.3", "S12.3.3.3-001", "direct_arbitrary_order",
          ["direct-access-arbitrary-record-order"], """
        integer :: u, ios, recl, sample, left, right
        sample = 0
        inquire(iolength=recl) sample
        open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
        write(u,rec=2) 202
        write(u,rec=1) 101
        left = -1
        right = -2
        read(u,rec=1,iostat=ios) left
        call check_int('read-record-one-status', ios, 0)
        call check_int('read-record-one-value', left, 101)
        read(u,rec=2,iostat=ios) right
        call check_int('read-record-two-status', ios, 0)
        call check_int('read-record-two-value', right, 202)
        close(u, status='delete')
    """, 4,
          "12.3.3.3 p1 defines direct access as arbitrary-order record access; records written 2 then 1 are read back by REC=1 and REC=2.",
          [("read-one-as-two", "        read(u,rec=1,iostat=ios) left", "        read(u,rec=2,iostat=ios) left")])

    c.add("12.3.3.3", "S12.3.3.3-002", "direct_record_numbers",
          ["direct-record-positive-number", "direct-record-number-specified-on-write", "direct-record-number-immutable"], """
        integer :: u, ios, recl, sample, value
        sample = 0
        inquire(iolength=recl) sample
        open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
        write(u,rec=1) 11
        write(u,rec=2) 22
        value = -1
        read(u,rec=1,iostat=ios) value
        call check_int('positive-record-number-status', ios, 0)
        call check_int('positive-record-number-value', value, 11)
        value = -2
        read(u,rec=2,iostat=ios) value
        call check_int('specified-record-number-status', ios, 0)
        call check_int('specified-record-number-value', value, 22)
        write(u,rec=2) 44
        value = -3
        read(u,rec=2,iostat=ios) value
        call check_int('rewritten-record-status', ios, 0)
        call check_int('rewritten-record-value', value, 44)
        close(u, status='delete')
    """, 6,
          "12.3.3.3 p2 identifies each direct record by a positive REC= value fixed when written; rewriting REC=2 changes that record's value without renumbering it.",
          [("positive-read-other-written-record", "        read(u,rec=1,iostat=ios) value", "        read(u,rec=2,iostat=ios) value"),
           ("specified-read-other-written-record", "        read(u,rec=2,iostat=ios) value\n        call check_int('specified-record-number-status'", "        read(u,rec=1,iostat=ios) value\n        call check_int('specified-record-number-status'"),
           ("rewrite-other-record", "        write(u,rec=2) 44", "        write(u,rec=1) 44")])

    c.add("12.3.3.3", "S12.3.3.3-006", "direct_out_of_order_gap",
          ["direct-out-of-order-write-permitted", "direct-gap-write-permitted", "direct-written-record-read-permitted"], """
        integer :: u, ios, recl, sample, value
        sample = 0
        inquire(iolength=recl) sample
        open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
        write(u,rec=3) 303
        write(u,rec=1) 101
        value = -1
        read(u,rec=1,iostat=ios) value
        call check_int('out-of-order-lower-record-status', ios, 0)
        call check_int('out-of-order-lower-record-value', value, 101)
        value = -3
        read(u,rec=3,iostat=ios) value
        call check_int('gap-written-record-status', ios, 0)
        call check_int('gap-written-record-value', value, 303)
        value = -4
        read(u,rec=3,iostat=ios) value
        call check_int('written-record-read-status', ios, 0)
        call check_int('written-record-read-value', value, 303)
        close(u, status='delete')
    """, 6,
          "12.3.3.3 p2 permits direct writes and reads out of record-number order, including writing REC=3 before lower records; written records are read by REC=.",
          [("out-of-order-read-higher", "        read(u,rec=1,iostat=ios) value", "        read(u,rec=3,iostat=ios) value"),
           ("gap-read-lower", "        read(u,rec=3,iostat=ios) value\n        call check_int('gap-written-record-status'", "        read(u,rec=1,iostat=ios) value\n        call check_int('gap-written-record-status'"),
           ("written-read-lower", "        read(u,rec=3,iostat=ios) value\n        call check_int('written-record-read-status'", "        read(u,rec=1,iostat=ios) value\n        call check_int('written-record-read-status'")])

    c.add("12.3.3.4", "S12.3.3.4-001", "stream_storage_units",
          ["stream-access-file-storage-units"], """
        integer :: u, ios, char_units, second_pos
        character(len=1) :: ch
        inquire(iolength=char_units) ch
        second_pos = 1 + char_units
        open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
        write(u,pos=1) 'A'
        write(u,pos=second_pos) 'B'
        ch = '#'
        read(u,pos=second_pos,iostat=ios) ch
        call check_int('stream-storage-unit-status', ios, 0)
        call check_char('stream-storage-unit-value', ch, 'B')
        close(u, status='delete')
    """, 2,
          "12.3.3.4 p1 defines stream access over file storage units; single-character stream writes at POS=1 and POS=2 are read by position.",
          [("read-first-position", "        read(u,pos=second_pos,iostat=ios) ch", "        read(u,pos=1,iostat=ios) ch")])

    c.add("12.3.3.4", "S12.3.3.4-002", "stream_form_dependence",
          ["stream-properties-depend-on-form"], """
        integer :: u, ios, char_units, next_pos
        character(len=3) :: rec
        character(len=1) :: ch
        inquire(iolength=char_units) ch
        next_pos = 1 + char_units
        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
        write(u,'(a)') 'ABC'
        rewind u
        rec = '###'
        read(u,'(a)',iostat=ios) rec
        call check_int('formatted-stream-record-status', ios, 0)
        call check_char('formatted-stream-record-value', rec, 'ABC')
        close(u, status='delete')
        open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
        write(u,pos=1) 'U'
        write(u,pos=next_pos) 'V'
        ch = '#'
        read(u,pos=1,iostat=ios) ch
        call check_int('unformatted-stream-position-status', ios, 0)
        call check_char('unformatted-stream-position-value', ch, 'U')
        close(u, status='delete')
    """, 4,
          "12.3.3.4 p2 makes stream properties form-dependent; the fixture observes a formatted record and an unformatted positioned storage unit separately.",
          [("unformatted-read-wrong-pos", "        read(u,pos=1,iostat=ios) ch", "        read(u,pos=next_pos,iostat=ios) ch")])

    c.add("12.3.3.4", "S12.3.3.4-004", "unformatted_stream_positions",
          ["unformatted-stream-positive-positions", "unformatted-stream-first-position-one", "unformatted-stream-subsequent-position-plus-one"], """
        integer :: u, ios, pos0, char_units, second_pos
        character(len=1) :: ch
        inquire(iolength=char_units) ch
        second_pos = 1 + char_units
        open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
        inquire(unit=u, pos=pos0)
        call check_true('initial-unformatted-position-positive', pos0 > 0)
        call check_int('initial-unformatted-position-one', pos0, 1)
        write(u,pos=1) 'Z'
        write(u,pos=1) 'A'
        write(u,pos=second_pos) 'B'
        ch = '#'
        read(u,pos=1,iostat=ios) ch
        call check_int('first-position-status', ios, 0)
        call check_char('first-position-value', ch, 'A')
        ch = '#'
        read(u,pos=second_pos,iostat=ios) ch
        call check_int('subsequent-position-status', ios, 0)
        call check_char('subsequent-position-value', ch, 'B')
        close(u, status='delete')
    """, 6,
          "12.3.3.4 p3 says unformatted stream positions are positive, first at 1, and subsequent positions increment by one; POS=1 and POS=2 are read distinctly.",
          [("positive-position-read-second", "        read(u,pos=1,iostat=ios) ch", "        read(u,pos=second_pos,iostat=ios) ch"),
           ("first-position-write-second", "        write(u,pos=1) 'A'", "        write(u,pos=second_pos) 'A'"),
           ("subsequent-position-read-first", "        read(u,pos=second_pos,iostat=ios) ch", "        read(u,pos=1,iostat=ios) ch")])

    c.add("12.3.3.4", "S12.3.3.4-005", "unformatted_stream_out_of_order_gap",
          ["unformatted-stream-out-of-order-permitted", "unformatted-stream-gap-write-permitted", "unformatted-stream-written-unit-read-permitted"], """
        integer :: u, ios, char_units, gap_pos
        character(len=1) :: ch
        inquire(iolength=char_units) ch
        gap_pos = 1 + 2 * char_units
        open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
        write(u,pos=gap_pos) 'C'
        write(u,pos=1) 'A'
        ch = '#'
        read(u,pos=1,iostat=ios) ch
        call check_int('out-of-order-stream-lower-status', ios, 0)
        call check_char('out-of-order-stream-lower-value', ch, 'A')
        ch = '#'
        read(u,pos=gap_pos,iostat=ios) ch
        call check_int('stream-gap-written-status', ios, 0)
        call check_char('stream-gap-written-value', ch, 'C')
        ch = '#'
        read(u,pos=gap_pos,iostat=ios) ch
        call check_int('stream-written-unit-status', ios, 0)
        call check_char('stream-written-unit-value', ch, 'C')
        close(u, status='delete')
    """, 6,
          "12.3.3.4 p3 permits positioned unformatted stream writes out of order and at a later position; written positions are then read by POS=.",
          [("out-of-order-stream-read-gap", "        read(u,pos=1,iostat=ios) ch", "        read(u,pos=gap_pos,iostat=ios) ch"),
           ("stream-gap-read-lower", "        read(u,pos=gap_pos,iostat=ios) ch\n        call check_int('stream-gap-written-status'", "        read(u,pos=1,iostat=ios) ch\n        call check_int('stream-gap-written-status'"),
           ("stream-written-read-lower", "        read(u,pos=gap_pos,iostat=ios) ch\n        call check_int('stream-written-unit-status'", "        read(u,pos=1,iostat=ios) ch\n        call check_int('stream-written-unit-status'")])

    c.add("12.3.3.4", "S12.3.3.4-006", "formatted_stream_records",
          ["formatted-stream-record-markers-impose-records"], """
        integer :: u, ios
        character(len=3) :: first, second
        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
        write(u,'(a)') 'ABC'
        write(u,'(a)') 'XYZ'
        rewind u
        first = '###'
        second = '@@@'
        read(u,'(a)',iostat=ios) first
        call check_int('formatted-stream-first-record-status', ios, 0)
        call check_char('formatted-stream-first-record-value', first, 'ABC')
        read(u,'(a)',iostat=ios) second
        call check_int('formatted-stream-second-record-status', ios, 0)
        call check_char('formatted-stream-second-record-value', second, 'XYZ')
        close(u, status='delete')
    """, 4,
          "12.3.3.4 p4 says formatted stream record markers impose record structure; two advancing writes are read as two records.",
          [("remove-first-record-marker", "        write(u,'(a)') 'ABC'", "        write(u,'(a)',advance='no') 'ABC'")])

    c.add("12.3.3.4", "S12.3.3.4-008", "formatted_empty_no_marker",
          ["formatted-stream-empty-record-without-marker-no-effect"], """
        integer :: u, before_empty, after_empty, after_data
        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
        write(u,'(a)',advance='no') 'A'
        inquire(unit=u, pos=before_empty)
        write(u,'(a)',advance='no') ''
        inquire(unit=u, pos=after_empty)
        write(u,'(a)',advance='no') 'B'
        inquire(unit=u, pos=after_data)
        call check_int('empty-no-marker-same-position', after_empty, before_empty)
        call check_true('surrounding-data-advanced-position', after_data > after_empty)
        close(u, status='delete')
    """, 2,
          "12.3.3.4 p4 says an empty formatted stream record with no marker has no effect; POS= before and after that write is unchanged while following data advances it.",
          [("empty-write-creates-marker", "        write(u,'(a)',advance='no') ''", "        write(u,'(a)') ''")])

    c.add("12.3.3.4", "S12.3.3.4-009", "formatted_stream_positions",
          ["formatted-stream-positive-positions", "formatted-stream-first-position-one"], """
        integer :: u, initial_pos, after_one
        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
        inquire(unit=u, pos=initial_pos)
        call check_true('formatted-initial-position-positive', initial_pos > 0)
        call check_int('formatted-first-position-one', initial_pos, 1)
        write(u,'(a)',advance='no') 'A'
        inquire(unit=u, pos=after_one)
        call check_true('formatted-after-write-position-positive', after_one > 0)
        close(u, status='delete')
    """, 3,
          "12.3.3.4 p4 gives formatted stream positive positions and first position 1; INQUIRE(POS=) observes those portable properties without byte-count assumptions.",
          [("advance-initial-before-inquire", "        inquire(unit=u, pos=initial_pos)", "        write(u,'(a)',advance='no') 'Z'\n        inquire(unit=u, pos=initial_pos)"),
           ("drop-positive-pos-inquire", "        inquire(unit=u, pos=after_one)", "        after_one = -1")])

    c.add("12.3.3.4", "S12.3.3.4-010", "formatted_stream_inquired_pos",
          ["formatted-stream-position-to-inquired-pos-permitted"], """
        integer :: u, saved, ios
        character(len=1) :: ch
        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
        write(u,'(a)',advance='no') 'A'
        inquire(unit=u, pos=saved)
        write(u,'(a)',advance='no') 'B'
        write(u,'(a)',pos=saved,advance='no',iostat=ios) 'C'
        call check_int('write-to-inquired-position-status', ios, 0)
        ch = '#'
        read(u,'(a)',pos=saved,iostat=ios) ch
        call check_char('read-inquired-position-value', ch, 'C')
        close(u, status='delete')
    """, 2,
          "12.3.3.4 p4 permits formatted stream positioning to a previously inquired POS= value; overwriting and rereading that saved position yields C.",
          [("write-to-initial-not-saved", "        write(u,'(a)',pos=saved,advance='no',iostat=ios) 'C'", "        write(u,'(a)',pos=1,advance='no',iostat=ios) 'C'")])

    c.add("12.3.4.1", "S12.3.4.1-001", "io_execution_moves_position",
          ["io-execution-affects-external-file-position"], """
        integer :: u, ios, first, second
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 14
        write(u,'(i0)') 28
        rewind u
        first = -1
        second = -2
        read(u,*,iostat=ios) first
        call check_int('first-read-status', ios, 0)
        call check_int('first-read-value', first, 14)
        read(u,*,iostat=ios) second
        call check_int('position-advanced-read-status', ios, 0)
        call check_int('position-advanced-read-value', second, 28)
        close(u, status='delete')
    """, 4,
          "12.3.4.1 p1 says some I/O statements affect external-file position; the second read observes that the first read advanced to the next record.",
          [("rewind-between-reads", "        read(u,*,iostat=ios) second", "        rewind u\n        read(u,*,iostat=ios) second")])

    c.add("12.3.4.1", "S12.3.4.1-002", "initial_terminal_empty_points",
          ["initial-point-before-first-unit", "terminal-point-after-last-unit", "empty-file-initial-terminal-same"], """
        integer :: u, empty_u, ios, value
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 41
        write(u,'(i0)') 42
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('initial-point-next-status', ios, 0)
        call check_int('initial-point-next-value', value, 41)
        value = -2
        read(u,*,iostat=ios) value
        call check_int('last-record-status', ios, 0)
        call check_int('last-record-value', value, 42)
        read(u,*,iostat=ios)
        call check_int('terminal-point-end-status', ios, iostat_end)
        close(u, status='delete')
        open(newunit=empty_u, status='scratch', access='sequential', form='formatted', action='readwrite')
        read(empty_u,*,iostat=ios)
        call check_int('empty-initial-terminal-status', ios, iostat_end)
        close(empty_u, status='delete')
    """, 6,
          "12.3.4.1 p2 defines initial before first and terminal after last; REWIND/read observes the first record, reading past the last or in an empty file returns IOSTAT_END.",
          [("drop-initial-rewind", "        rewind u", "        backspace u"),
           ("add-record-before-terminal", "        rewind u", "        write(u,'(i0)') 43\n        rewind u"),
           ("make-empty-nonempty", "        read(empty_u,*,iostat=ios)", "        write(empty_u,'(i0)') 77\n        rewind empty_u\n        read(empty_u,*,iostat=ios)")])

    c.add("12.3.4.1", "S12.3.4.1-003", "current_record",
          ["current-record-when-positioned-within-record", "no-current-record-otherwise"], """
        integer :: u, ios
        character(len=2) :: head, tail, next
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(a)') 'ABCD'
        write(u,'(a)') 'WXYZ'
        rewind u
        head = '##'
        tail = '@@'
        next = '??'
        read(u,'(a2)',advance='no',iostat=ios) head
        call check_int('within-record-head-status', ios, 0)
        call check_char('within-record-head-value', head, 'AB')
        read(u,'(a2)',iostat=ios) tail
        call check_int('within-record-tail-status', ios, 0)
        call check_char('within-record-tail-value', tail, 'CD')
        read(u,'(a2)',iostat=ios) next
        call check_int('no-current-next-status', ios, 0)
        call check_char('no-current-next-value', next, 'WX')
        close(u, status='delete')
    """, 6,
          "12.3.4.1 p3 defines a current record only while positioned within a record; a nonadvancing read leaves ABCD current, and the following advancing read ends it before WXYZ.",
          [("make-head-advancing", "        read(u,'(a2)',advance='no',iostat=ios) head", "        read(u,'(a2)',iostat=ios) head"),
           ("backspace-before-next", "        read(u,'(a2)',iostat=ios) next", "        backspace u\n        read(u,'(a2)',iostat=ios) next")])

    c.add("12.3.4.1", "S12.3.4.1-004", "preceding_records",
          ["preceding-record-before-current-or-between"], """
        integer :: u, ios, value, prior
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 11
        write(u,'(i0)') 22
        write(u,'(i0)') 33
        rewind u
        read(u,*,iostat=ios)
        read(u,*,iostat=ios)
        backspace u
        prior = -2
        read(u,*,iostat=ios) prior
        call check_int('preceding-between-status', ios, 0)
        call check_int('preceding-between-value', prior, 22)
        close(u, status='delete')
    """, 2,
          "12.3.4.1 p4 defines the preceding record before a between-record position; after reading record 2, BACKSPACE/read observes record 22 again.",
          [("rewind-not-backspace-between", "        backspace u", "        rewind u"),
           ])

    c.add("12.3.4.1", "S12.3.4.1-005", "next_records",
          ["next-record-after-current-or-between", "initial-point-next-is-first-record", "no-next-record-at-terminal-empty-or-last"], """
        integer :: u, empty_u, ios, first, middle, last, value
        open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
        write(u,'(i0)') 11
        write(u,'(i0)') 22
        write(u,'(i0)') 33
        rewind u
        first = -1
        read(u,*,iostat=ios) first
        call check_int('initial-next-status', ios, 0)
        call check_int('initial-next-value', first, 11)
        middle = -2
        read(u,*,iostat=ios) middle
        call check_int('between-next-status', ios, 0)
        call check_int('between-next-value', middle, 22)
        last = -3
        read(u,*,iostat=ios) last
        call check_int('last-record-status', ios, 0)
        call check_int('last-record-value', last, 33)
        read(u,*,iostat=ios)
        call check_int('terminal-no-next-status', ios, iostat_end)
        close(u, status='delete')
        open(newunit=empty_u, status='scratch', access='sequential', form='formatted', action='readwrite')
        read(empty_u,*,iostat=ios)
        call check_int('empty-no-next-status', ios, iostat_end)
        close(empty_u, status='delete')
    """, 8,
          "12.3.4.1 p5 defines the next record at initial and between records and says no next exists at terminal or in an empty file; reads observe those cases.",
          [("drop-next-rewind", "        rewind u", "        backspace u"),
           ("backspace-before-middle", "        read(u,*,iostat=ios) middle", "        backspace u\n        read(u,*,iostat=ios) middle"),
           ("add-fourth-record", "        rewind u", "        write(u,'(i0)') 44\n        rewind u")])

    c.add("12.3.4.1", "S12.3.4.1-006", "stream_positions",
          ["stream-position-between-storage-units", "stream-position-at-initial-or-terminal"], """
        integer :: u, ios, initial_pos, terminal_pos, char_units, second_pos
        character(len=1) :: ch
        inquire(iolength=char_units) ch
        second_pos = 1 + char_units
        open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
        inquire(unit=u, pos=initial_pos)
        call check_int('stream-initial-position', initial_pos, 1)
        write(u,pos=1) 'A'
        write(u,pos=second_pos) 'B'
        inquire(unit=u, pos=terminal_pos)
        call check_true('stream-terminal-after-initial', terminal_pos > initial_pos)
        ch = '#'
        read(u,pos=second_pos,iostat=ios) ch
        call check_int('stream-between-position-status', ios, 0)
        call check_char('stream-between-position-value', ch, 'B')
        close(u, status='delete')
    """, 4,
          "12.3.4.1 p6 places stream positions at initial, terminal, or between storage units; INQUIRE observes endpoints and POS=2 reads between known units.",
          [("stream-inquire-after-write", "        inquire(unit=u, pos=initial_pos)", "        write(u,pos=1) 'Z'\n        inquire(unit=u, pos=initial_pos)"),
           ("stream-read-first-not-second", "        read(u,pos=second_pos,iostat=ios) ch", "        read(u,pos=1,iostat=ios) ch")])
    return c.files, c.cases


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraphs)


def synced_catalogue(section, catalogue, specs):
    result = copy.deepcopy(catalogue)
    cases = [spec for spec in specs.values() if spec["section"] == section]
    by_rule = {}
    for spec in cases:
        by_rule.setdefault(spec["rule"], []).append(spec)
    for requirement in result["requirements"]:
        selected = by_rule.get(requirement["id"], [])
        covered = {facet for spec in selected for facet in spec["facets"]}
        for facet in covered:
            if facet not in requirement["facets"]:
                raise ValueError(f"unknown facet {facet}")
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - covered:
            raise ValueError(f"pending mismatch for {requirement['id']}")
        if selected:
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered))
            text = ("Access-position fixture implementation: "
                    f"{len(selected)} valid run-phase scratch-file program(s) cover {labels}. "
                    "They create the external files in the run directory with STATUS='SCRATCH' and also close with "
                    "STATUS='DELETE'. Oracles are limited to exact integer/character values, character lengths, "
                    "IOSTAT zero, IOSTAT_END, and POS= inequalities or values fixed by this source. No file name, "
                    "external representation, processor-specific IOSTAT number, IOMSG text, formatted-stream byte "
                    "spacing, or unsupported cross-access-method property is asserted.")
            requirement["oracle"] = owned_paragraph(requirement["oracle"], "Access-position fixture implementation:", text)
            prefix = "Source accounting only. "
            if requirement["oracle_limitation"].startswith(prefix):
                requirement["oracle_limitation"] = ("Runtime fixture coverage is finite and does not imply fixture review. "
                                                     + requirement["oracle_limitation"][len(prefix):])
    return result


def render_view(section, catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(ROOT)
    registry.catalogues[section] = catalogue
    selected = [s for s in specs.values() if s["section"] == section]
    represented = sum(len(s["facets"]) for s in selected)
    total = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - access-position fixtures\n\n"
            f"The canonical catalogue is `{CATALOGUES[section]}`. "
            "This author packet adds finite scratch-file runtime fixtures without fixture approval.\n\n"
            "Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256 "
            "`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.\n\n"
            f"**Catalogue source review: {registry.catalogue_review_state(section)}.** "
            f"This topic represents {represented} facets in {len(selected)} program(s); "
            f"{total - pending} of {total} facets are represented and {pending} remain pending.\n\n"
            f"<!-- BEGIN GENERATED {section} -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"])
    text += f"\n<!-- END GENERATED {section} -->\n\n"
    text += "## Access-position fixture derivations\n\n"
    for spec in selected:
        text += f"### `{spec['variant']}` / `{spec['rule']}`\n\n"
        text += "**Facets:** " + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n"
        text += spec["derivation"] + "\n\n"
        text += "Feature mutations: " + ", ".join(f"`{m['id']}`" for m in spec["mutants"]) + ".\n\n"
    return text


def sync_files(files, specs):
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for section, cat_path in CATALOGUES.items():
        path = ROOT / cat_path
        current = json.loads(path.read_text())
        updated = synced_catalogue(section, current, specs)
        path.write_text(json.dumps(updated, indent=2) + "\n")
        (ROOT / VIEWS[section]).write_text(render_view(section, updated, specs))


def check_files(files, specs):
    stale = []
    for path, raw in files.items():
        if not path.is_file() or path.read_bytes() != raw:
            stale.append(str(path.relative_to(ROOT)))
    actual = {p for p in (ROOT / "tests/fixtures").glob(TOPIC + "_*/*") if p.is_file()}
    stale += [str(p.relative_to(ROOT)) for p in sorted(actual - set(files))]
    for section, cat_path in CATALOGUES.items():
        path = ROOT / cat_path
        current = json.loads(path.read_text())
        expected = synced_catalogue(section, current, specs)
        if current != expected:
            stale.append(cat_path)
        view = render_view(section, expected, specs)
        if not (ROOT / VIEWS[section]).is_file() or (ROOT / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    if stale:
        raise SystemExit("stale io_access_position_12_3 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std, keep=False):
    files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_access_position_12_3" / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    try:
        for name, spec in specs.items():
            parent = (ROOT / spec["source_path"]).read_text()
            for mutant in spec["mutants"]:
                total += 1
                mutated = parent.replace(mutant["old"], mutant["new"], 1)
                if mutated == parent:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant did not change source")
                work = base / name / mutant["id"]
                work.mkdir(parents=True)
                src = work / "source.f90"
                exe = work / "program"
                src.write_text(mutated)
                cmd = compiler_command(compiler, std) + [str(src), "-o", str(exe)]
                built = subprocess.run(cmd, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
                if ran.returncode == 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant survived")
        print(f"Mutation check failed all {total} mutants with {compiler} ({std}).")
    finally:
        if keep:
            print(f"Kept mutation work in {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)
            if base.parent.exists() and not any(base.parent.iterdir()):
                base.parent.rmdir()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-mutation-work", action="store_true")
    args = parser.parse_args()
    modes = sum(bool(x) for x in (args.check, args.sync_catalogue, args.mutation_check))
    if modes > 1:
        parser.error("choose only one mode")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        run_mutations(args.compiler, args.std, args.keep_mutation_work)
        return
    files, specs = build_corpus(ROOT)
    if args.check:
        check_files(files, specs)
        action = "Checked"
    else:
        sync_files(files, specs)
        action = "Generated"
    print(f"{action} {len(files)} files for {len(specs)} fixtures and {sum(len(s['facets']) for s in specs.values())} facets.")


if __name__ == "__main__":
    main()
