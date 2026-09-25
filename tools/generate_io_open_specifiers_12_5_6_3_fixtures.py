#!/usr/bin/env python3
"""Generate Clause 12.5.6.3-.11 OPEN specifier fixtures."""
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
TOPIC = "io_open_specifiers_12_5_6_3"
CATALOGUES = {
    "12.5.6.3": "doc/catalogues/access_specifier_12_5_6_3.json",
    "12.5.6.4": "doc/catalogues/action_specifier_12_5_6_4.json",
    "12.5.6.6": "doc/catalogues/blank_specifier_12_5_6_6.json",
    "12.5.6.7": "doc/catalogues/decimal_specifier_12_5_6_7.json",
    "12.5.6.8": "doc/catalogues/delim_specifier_12_5_6_8.json",
    "12.5.6.9": "doc/catalogues/encoding_specifier_12_5_6_9.json",
    "12.5.6.10": "doc/catalogues/file_specifier_12_5_6_10.json",
    "12.5.6.11": "doc/catalogues/form_specifier_12_5_6_11.json",
}
VIEWS = {
    "12.5.6.3": "doc/fortran_2023_12_5_6_3.md",
    "12.5.6.4": "doc/fortran_2023_12_5_6_4.md",
    "12.5.6.6": "doc/fortran_2023_12_5_6_6.md",
    "12.5.6.7": "doc/fortran_2023_12_5_6_7.md",
    "12.5.6.8": "doc/fortran_2023_12_5_6_8.md",
    "12.5.6.9": "doc/fortran_2023_12_5_6_9.md",
    "12.5.6.10": "doc/fortran_2023_12_5_6_10.md",
    "12.5.6.11": "doc/fortran_2023_12_5_6_11.md",
}
VIEW_TITLES = {
    "12.5.6.3": "ACCESS= specifier",
    "12.5.6.4": "ACTION= specifier",
    "12.5.6.6": "BLANK= specifier",
    "12.5.6.7": "DECIMAL= specifier",
    "12.5.6.8": "DELIM= specifier",
    "12.5.6.9": "ENCODING= specifier",
    "12.5.6.10": "FILE= specifier",
    "12.5.6.11": "FORM= specifier",
}

RESTORED_PENDING = {
    ("S12.5.6.5-002", "asynchronous-yes-allows-async-io"):
        "Left pending: a load-bearing ASYNCHRONOUS='YES' mutation does not currently fail on both toolchains because the frozen LFortran reports ASYNCHRONOUS='NO' after OPEN(...,ASYNCHRONOUS='YES'); a future async-transfer packet should ship this as an LFortran defect with WAIT semantics.",
}

CHECKS = """
module io_open_specifier_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, check_false, finish_checks
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
subroutine check_false(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (actual) call fail(label)
checked = checked + 1
end subroutine check_false
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 4
end if
end subroutine finish_checks
end module io_open_specifier_checks
""".lstrip()

READ_TARGET = re.compile(r"^(?P<indent>\s*)read\s*\(.*\)\s*(?P<target>[A-Za-z]\w*)\s*$", re.I)
INTEGER_DECL = re.compile(r"^\s*integer\s*(?:,[^:]*)?::\s*(?P<names>.+)$", re.I)
CHARACTER_DECL = re.compile(r"^\s*character\s*\((?P<attrs>[^)]*)\)\s*(?:,[^:]*)?::\s*(?P<names>.+)$", re.I)
LOGICAL_DECL = re.compile(r"^\s*logical\s*(?:,[^:]*)?::\s*(?P<names>.+)$", re.I)
CHAR_SENTINELS = "#@$%&?+*/;:<>=^~|[]{}"


def body(text):
    return textwrap.dedent(text).strip() + "\n"


def clean_name(item):
    return item.split('=')[0].strip()


def parse_char_attrs(attrs):
    length = None
    kind = None
    for part in attrs.split(','):
        key_value = part.strip().lower().replace(' ', '')
        if key_value.startswith('len='):
            try:
                length = int(key_value.split('=', 1)[1])
            except ValueError:
                length = None
        elif key_value.startswith('kind='):
            kind = key_value.split('=', 1)[1]
        elif key_value.isdigit():
            length = int(key_value)
    return length, kind


def declaration_types(lines):
    result = {}
    for line in lines:
        match = INTEGER_DECL.match(line)
        if match:
            for item in match.group('names').split(','):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("integer", None, None)
            continue
        match = CHARACTER_DECL.match(line)
        if match:
            length, kind = parse_char_attrs(match.group('attrs'))
            if length is None:
                continue
            for item in match.group('names').split(','):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("character", length, kind)
            continue
        match = LOGICAL_DECL.match(line)
        if match:
            for item in match.group('names').split(','):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("logical", None, None)
    return result


def find_read_expected(lines, index, target, category):
    if category == "integer":
        pattern = re.compile(r"call check_int\('[^']+',\s*" + re.escape(target) + r"\s*,\s*([^,)]+)\)", re.I)
    elif category == "character":
        pattern = re.compile(r"call check_char\('[^']+',\s*" + re.escape(target) + r"\s*,\s*('[^']*')\)", re.I)
    else:
        pattern = re.compile(r"call check_(true|false)\('[^']+',\s*" + re.escape(target) + r"\s*\)", re.I)
    for next_line in lines[index + 1:index + 10]:
        if READ_TARGET.match(next_line):
            break
        match = pattern.search(next_line)
        if match:
            return match.group(1) if category != "logical" else match.group(0)
    if category == "character":
        pattern = re.compile(r"call check_true\('[^']+',\s*(?P<left>[^)]*\b" + re.escape(target) + r"\b[^)]*)\)", re.I)
        for next_line in lines[index + 1:index + 10]:
            match = pattern.search(next_line)
            if match:
                return "__CHAR_TRUE__"
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
        target = match.group('target')
        if target not in types:
            raise ValueError(f"read target {target} has no known declaration")
        category, length, kind = types[target]
        expected = find_read_expected(lines, index, target, category)
        read_index += 1
        indent = match.group('indent')
        for previous in range(len(output) - 1, -1, -1):
            if re.match(r"^\s*" + re.escape(target) + r"\s*=", output[previous], re.I):
                output.pop(previous)
                break
        label = f"pre-read-{read_index}-{target}"
        if category == "integer":
            sentinel = f"-{7000 + read_index}"
            poison = f"-{8000 + read_index}"
            default = "0"
            if expected.strip() == sentinel:
                raise ValueError(f"{label}: expected value equals sentinel")
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_int('{label}', {target}, {sentinel})")
            expected_init = expected.strip()
        elif category == "character":
            mark = CHAR_SENTINELS[(read_index - 1) % len(CHAR_SENTINELS)]
            prefix = "ucs_" if kind == "ucs" else ""
            sentinel = prefix + "'" + (mark * length) + "'"
            poison = prefix + "'" + ("!" * length) + "'"
            default = prefix + "'" + (" " * length) + "'"
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            if kind == "ucs":
                output.append(f"{indent}call check_true('{label}', {target} == {sentinel})")
                expected_init = "c"
            else:
                output.append(f"{indent}call check_char('{label}', {target}, {sentinel})")
                expected_init = "'" + (('X' if expected == "__CHAR_TRUE__" else expected.strip("'")).ljust(length)[:length]) + "'"
        else:
            sentinel = ".true."
            poison = ".false."
            default = ".false."
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_true('{label}', {target})")
            expected_init = expected.strip()
        probes.extend([
            (f"{label}-remove-sentinel-init", sentinel_line,
             f"{indent}! sentinel initializer removed for probe", "sentinel"),
            (f"{label}-expected-sentinel-init", sentinel_line,
             f"{indent}{target} = {expected_init}", "sentinel"),
            (f"{label}-default-sentinel-init", sentinel_line,
             f"{indent}{target} = {default}", "sentinel"),
        ])
        output.append(line)
    return "\n".join(output) + "\n", probes


def source(body_text, count):
    main, probes = add_pre_read_guards(body(body_text))
    total = count + sum(1 for _, _, _, category in probes if category == "sentinel") // 3
    src = CHECKS + "program p\nuse io_open_specifier_checks\nimplicit none\n" + main
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
        raw = content.encode('ascii')
        if path.suffix == '.f90' and max(map(len, raw.splitlines()), default=0) > 132:
            raise ValueError(f"line too long in {rel}")
        self.files[path] = raw

    def add(self, section, rule, variant, facets, body_text, checks, derivation, mutants, profiles=None):
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
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free",
                       "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0},
        }
        if profiles:
            manifest["profiles"] = list(profiles)
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        normalized = []
        for item in mutants:
            if len(item) == 3:
                mid, old, new = item
                category = "feature"
            elif len(item) == 4:
                mid, old, new, category = item
            else:
                raise ValueError(f"invalid mutant tuple for {name}: {item!r}")
            normalized.append((mid, textwrap.dedent(old).strip("\n"), textwrap.dedent(new).strip("\n"), category))
        normalized += sentinel_probes
        for item in normalized:
            if item[1] not in src:
                raise ValueError(f"{name}: mutant span not found: {item[0]} -> {item[1]}")
            if src.count(item[1]) != 1:
                raise ValueError(f"{name}: mutant span not unique: {item[0]} -> {item[1]}")
        self.cases[name] = {
            "section": section,
            "rule": rule,
            "variant": variant,
            "facets": list(facets),
            "path": folder + "/fixture.json",
            "source_path": folder + "/source.f90",
            "checks": total_checks,
            "derivation": derivation,
            "profiles": list(profiles or []),
            "mutants": [{"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in normalized],
        }


def build_corpus(root=ROOT):
    c = Corpus(root)
    c.add("12.5.6.3", "S12.5.6.3-002", "access_default_new_existing", [
        "access-selects-connection-method"], """
        integer :: u, ios, recl, value, char_units, second_pos
        character(len=10) :: access_mode
        character(len=1) :: ch
        value = 0
        inquire(iolength=recl) value
        inquire(iolength=char_units) ch
        second_pos = 1 + char_units
        open(newunit=u, file='ioos_access_default.dat', status='replace', &
             form='formatted', action='readwrite')
        inquire(unit=u, access=access_mode)
        call check_char('default-access-sequential', access_mode, 'SEQUENTIAL')
        write(u,'(i0)') 211
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('default-sequential-read-status', ios, 0)
        call check_int('default-sequential-read-value', value, 211)
        close(u, status='delete')
        open(newunit=u, file='ioos_access_stream.dat', status='replace', &
             access='stream', form='unformatted', action='readwrite')
        write(u,pos=second_pos) 'S'
        close(u)
        open(newunit=u, file='ioos_access_stream.dat', status='old', &
             access='stream', form='unformatted', action='readwrite')
        inquire(unit=u, access=access_mode)
        call check_char('existing-stream-access', access_mode, 'STREAM    ')
        ch = '#'
        read(u,pos=second_pos,iostat=ios) ch
        call check_int('existing-stream-read-status', ios, 0)
        call check_char('existing-stream-read-value', ch, 'S')
        close(u, status='delete')
        open(newunit=u, file='ioos_access_direct.dat', status='replace', &
             access='direct', form='unformatted', recl=recl, action='readwrite')
        inquire(unit=u, access=access_mode)
        call check_char('new-direct-access', access_mode, 'DIRECT    ')
        write(u,rec=1) 223
        value = -2
        read(u,rec=1,iostat=ios) value
        call check_int('new-direct-read-status', ios, 0)
        call check_int('new-direct-read-value', value, 223)
        close(u, status='delete')
    """, 9,
        "12.5.6.3 p1 makes omitted ACCESS default SEQUENTIAL and requires specified new/existing access methods to be in the file's allowed set; INQUIRE(ACCESS=) and method-specific transfers observe those properties.",
        [("default-access-changed-to-stream",
          "        open(newunit=u, file='ioos_access_default.dat', status='replace', &\n             form='formatted', action='readwrite')",
          "        open(newunit=u, file='ioos_access_default.dat', status='replace', &\n             access='stream', form='formatted', action='readwrite')"),
         ("existing-open-replaces-file",
          "        open(newunit=u, file='ioos_access_stream.dat', status='old', &\n             access='stream', form='unformatted', action='readwrite')",
          "        open(newunit=u, file='ioos_access_stream.dat', status='replace', &\n             access='stream', form='unformatted', action='readwrite')"),
         ("new-direct-access-changed-to-stream",
          "        open(newunit=u, file='ioos_access_direct.dat', status='replace', &\n             access='direct', form='unformatted', recl=recl, action='readwrite')",
           "        open(newunit=u, file='ioos_access_direct.dat', status='replace', &\n             access='stream', form='unformatted', action='readwrite')"),
         ("new-direct-access-changed-to-sequential",
          "        open(newunit=u, file='ioos_access_direct.dat', status='replace', &\n             access='direct', form='unformatted', recl=recl, action='readwrite')",
           "        open(newunit=u, file='ioos_access_direct.dat', status='replace', &\n             access='sequential', form='unformatted', action='readwrite')")])

    c.add("12.5.6.4", "S12.5.6.4-006", "action_modes", [
        "readwrite-action-implies-read-and-write"], """
        integer :: u, ios, value
        character(len=10) :: action_mode, read_mode, write_mode, readwrite_mode
        open(newunit=u, file='ioos_action.dat', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(i0)') 321
        close(u)
        open(newunit=u, file='ioos_action.dat', status='old', &
             form='formatted', action='read')
        inquire(unit=u, action=action_mode, read=read_mode, write=write_mode, readwrite=readwrite_mode)
        call check_char('action-read-token', action_mode, 'READ      ')
        call check_char('action-read-allows-read', read_mode, 'YES       ')
        call check_char('action-read-disallows-write', write_mode, 'NO        ')
        call check_char('action-read-disallows-readwrite', readwrite_mode, 'NO        ')
        value = -1
        read(u,*,iostat=ios) value
        call check_int('existing-read-action-status', ios, 0)
        call check_int('existing-read-action-value', value, 321)
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='write')
        inquire(unit=u, action=action_mode, read=read_mode, write=write_mode)
        call check_char('action-write-token', action_mode, 'WRITE     ')
        call check_char('action-write-disallows-read', read_mode, 'NO        ')
        call check_char('action-write-allows-write', write_mode, 'YES       ')
        write(u,'(i0)') 322
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, action=action_mode, read=read_mode, write=write_mode, readwrite=readwrite_mode)
        call check_char('action-readwrite-token', action_mode, 'READWRITE ')
        call check_char('action-readwrite-allows-read', read_mode, 'YES       ')
        call check_char('action-readwrite-allows-write', write_mode, 'YES       ')
        call check_char('action-readwrite-allows-readwrite', readwrite_mode, 'YES       ')
        write(u,'(i0)') 323
        rewind u
        value = -2
        read(u,*,iostat=ios) value
        call check_int('readwrite-read-status', ios, 0)
        call check_int('readwrite-read-value', value, 323)
        close(u, status='delete')
    """, 15,
        "12.5.6.4 p1 requires READ and WRITE to be included when READWRITE is included; INQUIRE on an ACTION='READWRITE' connection reports READ=YES and WRITE=YES and exact transfers prove both actions work.",
        [("read-action-changed-to-readwrite",
          "        open(newunit=u, file='ioos_action.dat', status='old', &\n             form='formatted', action='read')",
          "        open(newunit=u, file='ioos_action.dat', status='old', &\n             form='formatted', action='readwrite')"),
         ("read-existing-open-replaces-file",
          "        open(newunit=u, file='ioos_action.dat', status='old', &\n             form='formatted', action='read')",
          "        open(newunit=u, file='ioos_action.dat', status='replace', &\n             form='formatted', action='read')"),
         ("write-action-changed-to-readwrite",
          "        open(newunit=u, status='scratch', form='formatted', action='write')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')"),
         ("new-write-action-changed-to-read",
          "        open(newunit=u, status='scratch', form='formatted', action='write')",
          "        open(newunit=u, status='scratch', form='formatted', action='read')"),
         ("readwrite-action-changed-to-read",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='read')"),
         ("readwrite-action-changed-to-write",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='write')")])

    c.add("12.5.6.6", "S12.5.6.6-003", "blank_modes", [
        "blank-mode-effect"], """
        integer :: u, ios, value
        character(len=4) :: blank_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, blank=blank_mode)
        call check_char('blank-default-null-token', blank_mode, 'NULL')
        write(u,'(a)') '1 2'
        rewind u
        value = -1
        read(u,'(i3)',iostat=ios) value
        call check_int('blank-default-read-status', ios, 0)
        call check_int('blank-default-read-value', value, 12)
        open(unit=u, blank='zero')
        inquire(unit=u, blank=blank_mode)
        call check_char('blank-changeable-zero-token', blank_mode, 'ZERO')
        rewind u
        value = -2
        read(u,'(i3)',iostat=ios) value
        call check_int('blank-changeable-read-status', ios, 0)
        call check_int('blank-changeable-read-value', value, 102)
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')
        write(u,'(a)') '1 2'
        rewind u
        value = -3
        read(u,'(i3)',iostat=ios) value
        call check_int('blank-zero-read-status', ios, 0)
        call check_int('blank-zero-read-value', value, 102)
        close(u, status='delete')
    """, 8,
        "12.5.6.6 p1 makes omitted BLANK default NULL, permits it for formatted I/O, and makes it changeable; 13.8.7 distinguishes '1 2' as 12 under NULL and 102 under ZERO.",
        [("default-blank-changed-to-zero",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')"),
         ("subsequent-blank-zero-to-null",
          "        open(unit=u, blank='zero')", "        open(unit=u, blank='null')"),
         ("explicit-blank-zero-to-null",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')"),
         ("blank-input-field-changed",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')\n        write(u,'(a)') '1 2'",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')\n        write(u,'(a)') '12 '" )])

    c.add("12.5.6.7", "S12.5.6.7-003", "decimal_modes", [
        "decimal-mode-effect"], """
        integer :: u, ios
        character(len=5) :: decimal_mode
        character(len=3) :: field
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, decimal=decimal_mode)
        call check_char('decimal-default-point-token', decimal_mode, 'POINT')
        write(u,'(ss,f3.1)') 1.5
        rewind u
        field = '###'
        read(u,'(a3)',iostat=ios) field
        call check_int('decimal-default-output-status', ios, 0)
        call check_char('decimal-default-output-field', field, '1.5')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', decimal='comma')
        inquire(unit=u, decimal=decimal_mode)
        call check_char('decimal-comma-token', decimal_mode, 'COMMA')
        write(u,'(ss,f3.1)') 1.5
        rewind u
        field = '###'
        read(u,'(a3)',iostat=ios) field
        call check_int('decimal-comma-output-status', ios, 0)
        call check_char('decimal-comma-output-field', field, '1,5')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', decimal='point')
        open(unit=u, decimal='comma')
        inquire(unit=u, decimal=decimal_mode)
        call check_char('decimal-changeable-comma-token', decimal_mode, 'COMMA')
        write(u,'(ss,f3.1)') 1.5
        rewind u
        field = '###'
        read(u,'(a3)',iostat=ios) field
        call check_int('decimal-changeable-output-status', ios, 0)
        call check_char('decimal-changeable-output-field', field, '1,5')
        close(u, status='delete')
    """, 9,
        "12.5.6.7 p1 defaults DECIMAL to POINT, permits COMMA on formatted connections, and makes it changeable; exact SS,F3.1 output of exactly representable 1.5 distinguishes 1.5 from 1,5 without rounding or plus-sign latitude.",
        [("default-decimal-changed-to-comma",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', decimal='comma')"),
         ("explicit-decimal-comma-to-point",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', decimal='comma')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', decimal='point')"),
         ("subsequent-decimal-comma-to-point",
          "        open(unit=u, decimal='comma')", "        open(unit=u, decimal='point')"),
         ("decimal-output-format-changed",
           "        open(unit=u, decimal='comma')\n        inquire(unit=u, decimal=decimal_mode)\n        call check_char('decimal-changeable-comma-token', decimal_mode, 'COMMA')\n        write(u,'(ss,f3.1)') 1.5",
           "        open(unit=u, decimal='comma')\n        inquire(unit=u, decimal=decimal_mode)\n        call check_char('decimal-changeable-comma-token', decimal_mode, 'COMMA')\n        write(u,'(ss,f3.1)') 2.5")])

    c.add("12.5.6.8", "S12.5.6.8-003", "delim_modes", [
        "delim-mode-effect"], """
        integer :: u, ios, pos
        character(len=10) :: delim_mode
        character(len=30) :: line
        character(len=3) :: ch
        namelist /grp/ ch
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, delim=delim_mode)
        call check_char('delim-default-none-token', delim_mode, 'NONE      ')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='quote')
        write(u,*) 'A"B'
        rewind u
        line = '##############################'
        call check_char('pre-read-list-line', line, '##############################')
        read(u,'(a)',iostat=ios) line(1:len(line))
        call check_int('delim-quote-list-status', ios, 0)
        pos = index(line, '"')
        call check_true('delim-quote-list-opening', pos > 0)
        call check_int('delim-quote-list-substring-len', len(line(pos:pos+5)), 6)
        call check_char('delim-quote-list-substring', line(pos:pos+5), '"A""B"')
        close(u, status='delete')
        ch = 'A''B'
        open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='none')
        open(unit=u, delim='apostrophe')
        inquire(unit=u, delim=delim_mode)
        call check_char('delim-changeable-apostrophe-token', delim_mode, 'APOSTROPHE')
        write(u,nml=grp)
        rewind u
        line = '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        call check_char('pre-read-namelist-header', line, '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        read(u,'(a)',iostat=ios) line(1:len(line))
        call check_int('delim-namelist-header-status', ios, 0)
        line = '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        call check_char('pre-read-namelist-value', line, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        read(u,'(a)',iostat=ios) line(1:len(line))
        call check_int('delim-apostrophe-namelist-status', ios, 0)
        pos = index(line, '''')
        call check_true('delim-apostrophe-namelist-opening', pos > 0)
        call check_int('delim-apostrophe-namelist-substring-len', len(line(pos:pos+5)), 6)
        call check_char('delim-apostrophe-namelist-substring', line(pos:pos+5), "'A''B'")
        close(u, status='delete')
    """, 14,
        "12.5.6.8 p1 defaults DELIM to NONE and makes it changeable for formatted list-directed and namelist output; exact delimited substrings observe QUOTE and APOSTROPHE with doubled internal delimiters without asserting processor-dependent spacing.",
        [("default-delim-changed-to-quote",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='quote')"),
         ("list-delim-quote-to-apostrophe",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='quote')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='apostrophe')"),
         ("changeable-delim-apostrophe-to-quote",
          "        open(unit=u, delim='apostrophe')", "        open(unit=u, delim='quote')"),
         ("namelist-delim-none-kept",
          "        open(unit=u, delim='apostrophe')", "        open(unit=u, delim='none')"),
         ("pre-read-list-expected-sentinel",
           "        line = '##############################'", "        line = '\"#############################'", "sentinel"),
         ("pre-read-namelist-value-expected-sentinel",
          "        line = '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'", "        line = '''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'", "sentinel")])

    c.add("12.5.6.9", "S12.5.6.9-003", "encoding_utf8_iso10646", [
        "encoding-utf8-specifies-iso-10646"], """
        integer, parameter :: ucs = selected_char_kind('ISO_10646')
        integer :: u, ios
        character(len=10) :: encoding_mode
        character(kind=ucs,len=1) :: c, d
        c = ucs_'A'
        open(newunit=u, status='scratch', form='formatted', action='readwrite', encoding='utf-8')
        inquire(unit=u, encoding=encoding_mode)
        call check_char('encoding-utf8-token', encoding_mode, 'UTF-8     ')
        write(u,'(a)') c
        rewind u
        d = ucs_'#'
        read(u,'(a)',iostat=ios) d
        call check_int('encoding-utf8-read-status', ios, 0)
        call check_true('encoding-utf8-iso10646-roundtrip', c == d)
        close(u, status='delete')
    """, 3,
        "12.5.6.9 p1 permits ENCODING='UTF-8' only with ISO 10646 support; under the iso10646 profile INQUIRE(ENCODING=) reports UTF-8 and a kind ISO_10646 character round-trips through formatted UTF-8 I/O.",
        [("encoding-utf8-to-default",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', encoding='utf-8')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', encoding='default')"),
         ("encoding-write-other-character",
           "        write(u,'(a)') c", "        write(u,'(a)') ucs_'B'"),
         ("encoding-read-skipped-to-other-target",
          "        read(u,'(a)',iostat=ios) d", "        read(u,'(a)',iostat=ios) c")],
        profiles=["iso10646"])

    c.add("12.5.6.10", "S12.5.6.10-001", "file_names", [
        "file-specifier-names-connected-file"], """
        integer :: u, ios, value
        open(newunit=u, file='ioos_file_main.dat', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(i0)') 401
        close(u)
        open(newunit=u, file='ioos_file_other.dat', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(i0)') 499
        close(u)
        open(newunit=u, file='ioos_file_main.dat', status='old', &
             form='formatted', action='read')
        value = -1
        read(u,*,iostat=ios) value
        call check_int('file-main-read-status', ios, 0)
        call check_int('file-main-read-value', value, 401)
        close(u, status='delete')
        open(newunit=u, file='ioos_file_trailing.dat   ', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(i0)') 402
        close(u)
        open(newunit=u, file='ioos_file_trailing.dat', status='old', &
             form='formatted', action='read')
        value = -2
        read(u,*,iostat=ios) value
        call check_int('file-trailing-read-status', ios, 0)
        call check_int('file-trailing-read-value', value, 402)
        close(u, status='delete')
        open(newunit=u, file='ioos_file_other.dat', status='old', &
             form='formatted', action='readwrite')
        close(u, status='delete')
    """, 4,
        "12.5.6.10 p1 says FILE names the connected file and ignores trailing blanks; both checks create files before STATUS='OLD' and distinguish the named file by exact read-back.",
        [("main-reopen-other-existing-file",
          "        open(newunit=u, file='ioos_file_main.dat', status='old', &\n             form='formatted', action='read')",
          "        open(newunit=u, file='ioos_file_other.dat', status='old', &\n             form='formatted', action='read')"),
         ("trailing-reopen-other-existing-file",
          "        open(newunit=u, file='ioos_file_trailing.dat', status='old', &\n             form='formatted', action='read')",
          "        open(newunit=u, file='ioos_file_other.dat', status='old', &\n             form='formatted', action='read')")])

    c.add("12.5.6.11", "S12.5.6.11-002", "form_modes", [
        "form-determines-formatted-unformatted"], """
        integer :: u, ios, recl, value
        character(len=11) :: form_mode
        value = 0
        inquire(iolength=recl) value
        open(newunit=u, file='ioos_form_seq.dat', status='replace', &
             access='sequential', action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('form-default-sequential', form_mode, 'FORMATTED  ')
        close(u, status='delete')
        open(newunit=u, file='ioos_form_direct.dat', status='replace', &
             access='direct', recl=recl, action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('form-default-direct', form_mode, 'UNFORMATTED')
        close(u, status='delete')
        open(newunit=u, file='ioos_form_stream.dat', status='replace', &
             access='stream', action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('form-default-stream', form_mode, 'UNFORMATTED')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('form-explicit-formatted-token', form_mode, 'FORMATTED  ')
        write(u,'(i0)') 511
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('form-formatted-read-status', ios, 0)
        call check_int('form-formatted-read-value', value, 511)
        close(u, status='delete')
        open(newunit=u, file='ioos_form_existing.dat', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(i0)') 512
        close(u)
        open(newunit=u, file='ioos_form_existing.dat', status='old', &
             form='formatted', action='read')
        inquire(unit=u, form=form_mode)
        call check_char('form-existing-formatted-token', form_mode, 'FORMATTED  ')
        value = -2
        read(u,*,iostat=ios) value
        call check_int('form-existing-read-status', ios, 0)
        call check_int('form-existing-read-value', value, 512)
        close(u, status='delete')
        open(newunit=u, file='ioos_form_unformatted.dat', status='replace', &
             form='unformatted', action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('form-new-unformatted-token', form_mode, 'UNFORMATTED')
        write(u) 513
        rewind u
        value = -3
        read(u,iostat=ios) value
        call check_int('form-unformatted-read-status', ios, 0)
        call check_int('form-unformatted-read-value', value, 513)
        close(u, status='delete')
    """, 12,
        "12.5.6.11 p1 fixes omitted FORM by ACCESS, and specified FORM determines matching formatted or unformatted transfers; existing/new files are created before reopening and exact values are read back.",
        [("sequential-default-form-changed-to-unformatted",
          "        open(newunit=u, file='ioos_form_seq.dat', status='replace', &\n             access='sequential', action='readwrite')",
          "        open(newunit=u, file='ioos_form_seq.dat', status='replace', &\n             access='sequential', form='unformatted', action='readwrite')"),
         ("direct-default-form-changed-to-formatted",
          "        open(newunit=u, file='ioos_form_direct.dat', status='replace', &\n             access='direct', recl=recl, action='readwrite')",
          "        open(newunit=u, file='ioos_form_direct.dat', status='replace', &\n             access='direct', form='formatted', recl=recl, action='readwrite')"),
         ("stream-default-form-changed-to-formatted",
          "        open(newunit=u, file='ioos_form_stream.dat', status='replace', &\n             access='stream', action='readwrite')",
          "        open(newunit=u, file='ioos_form_stream.dat', status='replace', &\n             access='stream', form='formatted', action='readwrite')"),
         ("explicit-formatted-changed-to-unformatted",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='unformatted', action='readwrite')"),
         ("existing-form-open-replaces-file",
          "        open(newunit=u, file='ioos_form_existing.dat', status='old', &\n             form='formatted', action='read')",
          "        open(newunit=u, file='ioos_form_existing.dat', status='replace', &\n             form='formatted', action='read')"),
         ("new-unformatted-changed-to-formatted",
          "        open(newunit=u, file='ioos_form_unformatted.dat', status='replace', &\n             form='unformatted', action='readwrite')",
          "        open(newunit=u, file='ioos_form_unformatted.dat', status='replace', &\n             form='formatted', action='readwrite')")])

    c.add("12.5.6.3", "S12.5.6.3-003", "access_default_sequential", [
        "access-default-sequential"], """
        integer :: u, ios, value
        character(len=10) :: access_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, access=access_mode)
        call check_char('omitted-access-is-sequential', access_mode, 'SEQUENTIAL')
        write(u,'(i0)') 231
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('omitted-access-read-status', ios, 0)
        call check_int('omitted-access-read-value', value, 231)
        close(u, status='delete')
    """, 3,
        "12.5.6.3 p1 specifies omitted ACCESS defaults to SEQUENTIAL; INQUIRE(ACCESS=) and a sequential read-back observe it.",
        [("omitted-access-made-stream",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
           "        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')")])

    c.add("12.5.6.4", "S12.5.6.4-008", "action_write_disallows_read", [
        "action-new-file-action-included"], """
        integer :: u
        character(len=10) :: action_mode, read_mode, write_mode
        open(newunit=u, status='scratch', form='formatted', action='write')
        inquire(unit=u, action=action_mode, read=read_mode, write=write_mode)
        call check_char('write-action-token', action_mode, 'WRITE     ')
        call check_char('write-action-read-no', read_mode, 'NO        ')
        call check_char('write-action-write-yes', write_mode, 'YES       ')
        write(u,'(i0)') 341
        close(u, status='delete')
    """, 3,
        "12.5.6.4 p1 says a new file's allowed action set includes the specified action; ACTION='WRITE' on a scratch file reports WRITE=YES and accepts a WRITE statement.",
        [("write-action-made-readwrite",
           "        open(newunit=u, status='scratch', form='formatted', action='write')",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite')")])

    c.add("12.5.6.4", "S12.5.6.4-004", "action_readwrite_transfer", [
        "action-readwrite-permits-input-output"], """
        integer :: u, ios, value
        character(len=10) :: action_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, action=action_mode)
        call check_char('readwrite-action-token', action_mode, 'READWRITE ')
        write(u,'(i0)') 351
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('readwrite-action-read-status', ios, 0)
        call check_int('readwrite-action-read-value', value, 351)
        close(u, status='delete')
    """, 3,
        "12.5.6.4 p1 says ACTION='READWRITE' permits any I/O statements; the fixture writes and reads one exact record.",
        [("readwrite-action-made-read",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
           "        open(newunit=u, status='scratch', form='formatted', action='read')")])

    c.add("12.5.6.6", "S12.5.6.6-006", "blank_default_null", [
        "blank-default-null"], """
        integer :: u, ios, value
        character(len=4) :: blank_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, blank=blank_mode)
        call check_char('blank-omitted-null-token', blank_mode, 'NULL')
        write(u,'(a)') '1 2'
        rewind u
        value = -1
        read(u,'(i3)',iostat=ios) value
        call check_int('blank-omitted-read-status', ios, 0)
        call check_int('blank-omitted-read-value', value, 12)
        close(u, status='delete')
    """, 3,
        "12.5.6.6 p1 makes omitted BLANK default NULL; INQUIRE reports NULL and formatted input treats '1 2' as 12.",
        [("blank-default-made-zero",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')")])

    c.add("12.5.6.7", "S12.5.6.7-005", "decimal_default_point", [
        "decimal-default-point"], """
        integer :: u, ios
        character(len=5) :: decimal_mode
        character(len=3) :: field
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, decimal=decimal_mode)
        call check_char('decimal-omitted-point-token', decimal_mode, 'POINT')
        write(u,'(ss,f3.1)') 1.5
        rewind u
        field = '###'
        read(u,'(a3)',iostat=ios) field
        call check_int('decimal-omitted-read-status', ios, 0)
        call check_char('decimal-omitted-output', field, '1.5')
        close(u, status='delete')
    """, 3,
        "12.5.6.7 p1 makes omitted DECIMAL default POINT; exact SS,F3.1 output of 1.5 contains a point.",
        [("decimal-default-made-comma",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite', decimal='comma')")])

    c.add("12.5.6.8", "S12.5.6.8-006", "delim_default_none", [
        "delim-default-none"], """
        integer :: u
        character(len=10) :: delim_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, delim=delim_mode)
        call check_char('delim-omitted-none-token', delim_mode, 'NONE      ')
        close(u, status='delete')
    """, 1,
        "12.5.6.8 p1 makes omitted DELIM default NONE; INQUIRE(DELIM=) reports the exact token NONE.",
        [("delim-default-made-quote",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
           "        open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='quote')")])

    c.add("12.5.6.10", "S12.5.6.10-002", "file_trailing_blanks", [
        "file-name-trailing-blanks-ignored"], """
        integer :: u, ios, value
        open(newunit=u, file='ioos_trailing_name.dat   ', status='replace', &
              form='formatted', action='readwrite')
        write(u,'(i0)') 421
        close(u)
        open(newunit=u, file='ioos_trailing_other.dat', status='replace', &
              form='formatted', action='readwrite')
        write(u,'(i0)') 499
        close(u)
        open(newunit=u, file='ioos_trailing_name.dat', status='old', form='formatted', action='read')
        value = -1
        read(u,*,iostat=ios) value
        call check_int('trailing-file-read-status', ios, 0)
        call check_int('trailing-file-read-value', value, 421)
        close(u, status='delete')
        open(newunit=u, file='ioos_trailing_other.dat', status='old', &
              form='formatted', action='readwrite')
        close(u, status='delete')
    """, 2,
        "12.5.6.10 p1 ignores trailing blanks in FILE=; the STATUS='OLD' open uses an already-created name without blanks and reads the same exact record.",
        [("trailing-reopen-uses-other-existing",
           "        open(newunit=u, file='ioos_trailing_name.dat', status='old', form='formatted', action='read')",
           "        open(newunit=u, file='ioos_trailing_other.dat', status='old', form='formatted', action='read')")])

    c.add("12.5.6.11", "S12.5.6.11-003", "form_defaults_by_access", [
        "form-default-by-access"], """
        integer :: u, recl, value
        character(len=11) :: form_mode
        value = 0
        inquire(iolength=recl) value
        open(newunit=u, status='scratch', access='sequential', action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('sequential-default-formatted', form_mode, 'FORMATTED  ')
        close(u, status='delete')
        open(newunit=u, status='scratch', access='direct', recl=recl, action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('direct-default-unformatted', form_mode, 'UNFORMATTED')
        close(u, status='delete')
        open(newunit=u, status='scratch', access='stream', action='readwrite')
        inquire(unit=u, form=form_mode)
        call check_char('stream-default-unformatted', form_mode, 'UNFORMATTED')
        close(u, status='delete')
    """, 3,
        "12.5.6.11 p1 makes omitted FORM default FORMATTED for sequential access and UNFORMATTED for direct or stream access.",
        [("sequential-default-form-made-unformatted",
           "        open(newunit=u, status='scratch', access='sequential', action='readwrite')",
           "        open(newunit=u, status='scratch', access='sequential', form='unformatted', action='readwrite')"),
          ("direct-default-form-made-formatted",
           "        open(newunit=u, status='scratch', access='direct', recl=recl, action='readwrite')",
           "        open(newunit=u, status='scratch', access='direct', form='formatted', recl=recl, action='readwrite')"),
          ("stream-default-form-made-formatted",
           "        open(newunit=u, status='scratch', access='stream', action='readwrite')",
           "        open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')")])
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
                raise ValueError(f"unknown facet {facet} for {requirement['id']}")
            requirement["pending"].pop(facet, None)
        expected_pending = set(requirement["facets"]) - covered
        for facet in sorted(expected_pending - set(requirement["pending"])):
            reason = RESTORED_PENDING.get((requirement["id"], facet))
            if reason is not None:
                requirement["pending"][facet] = reason
        if set(requirement["pending"]) != expected_pending:
            raise ValueError(f"pending mismatch for {requirement['id']}")
        if selected:
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered))
            text = ("OPEN-specifier fixture implementation: "
                    f"{len(selected)} valid run-phase program(s) cover {labels}. "
                    "Runtime oracles use run-directory or scratch files created before STATUS='OLD', "
                    "INQUIRE tokens, guarded reads with sentinels, exact integer/character/logical values, "
                    "and only IOSTAT zero; no IOMSG text, nonzero IOSTAT number, processor-dependent file "
                    "case behavior, optional plus sign, or ambiguous real formatting is asserted.")
            requirement["oracle"] = owned_paragraph(requirement["oracle"],
                                                     "OPEN-specifier fixture implementation:", text)
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
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - OPEN specifier fixtures\n\n"
            f"The canonical catalogue is `{CATALOGUES[section]}`. "
            "This author packet adds finite runtime fixtures without fixture approval.\n\n"
            "Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256 "
            "`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.\n\n"
            f"**Catalogue source review: {registry.catalogue_review_state(section)}.** "
            f"This topic represents {represented} facets in {len(selected)} program(s); "
            f"{total - pending} of {total} facets are represented and {pending} remain pending.\n\n"
            f"<!-- BEGIN GENERATED {section} -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"])
    text += f"\n<!-- END GENERATED {section} -->\n\n"
    text += "## OPEN specifier fixture derivations\n\n"
    for spec in selected:
        text += f"### `{spec['variant']}` / `{spec['rule']}`\n\n"
        text += "**Facets:** " + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n"
        text += spec["derivation"] + "\n\n"
        feature = [m["id"] for m in spec["mutants"] if m["category"] == "feature"]
        text += "Feature mutations: " + ", ".join(f"`{m}`" for m in feature) + ".\n\n"
    return text.rstrip() + "\n"


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
        raise SystemExit("stale io_open_specifiers_12_5_6_3 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std, keep=False):
    files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_open_specifiers_12_5_6_3" / digest
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
                built = subprocess.run(cmd, cwd=work, text=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, timeout=30)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
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
