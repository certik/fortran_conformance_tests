#!/usr/bin/env python3
"""Generate Clause 12.5.6.12-.18 OPEN specifier fixtures."""
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
TOPIC = "io_open_specifiers_12_5_6_12"
CATALOGUES = {
    "12.5.6.13": "doc/catalogues/newunit_specifier_12_5_6_13.json",
    "12.5.6.14": "doc/catalogues/pad_specifier_12_5_6_14.json",
    "12.5.6.15": "doc/catalogues/position_specifier_12_5_6_15.json",
    "12.5.6.16": "doc/catalogues/recl_specifier_12_5_6_16.json",
    "12.5.6.17": "doc/catalogues/round_specifier_12_5_6_17.json",
    "12.5.6.18": "doc/catalogues/sign_specifier_12_5_6_18.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}
VIEW_TITLES = {
    "12.5.6.13": "NEWUNIT= specifier",
    "12.5.6.14": "PAD= specifier",
    "12.5.6.15": "POSITION= specifier",
    "12.5.6.16": "RECL= specifier",
    "12.5.6.17": "ROUND= specifier",
    "12.5.6.18": "SIGN= specifier",
}
POSITIVE_CONTROL_RULES = {
    "S12.5.6.16-010",
}
RESTORED_PENDING = {
    ("S12.5.6.16-003", "recl-sequential-maximum-record-length"):
        "Left pending: both compilers accept the positive control, but changing the sequential RECL from 5 to 4 is not load-bearing on the frozen LFortran, so no conforming feature mutation currently validates this facet on both toolchains.",
    ("S12.5.6.16-007", "recl-formatted-default-character-count"):
        "Left pending: both compilers accept default-character formatted output with RECL=5, but the shortened-RECL feature mutation is not load-bearing on the frozen LFortran, so this facet lacks the required two-toolchain mutation evidence.",
}

CHECKS = r'''
module io_open_specifier_12_5_6_12_checks
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
end module io_open_specifier_12_5_6_12_checks
'''.lstrip()

READ_TARGET = re.compile(r"^(?P<indent>\s*)read\s*\(.*\)\s*(?P<target>[A-Za-z]\w*)\s*$", re.I)
INTEGER_DECL = re.compile(r"^\s*integer\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
CHARACTER_DECL = re.compile(r"^\s*character\s*\(\s*len\s*=\s*(?P<len>\d+)\s*\)\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
LOGICAL_DECL = re.compile(r"^\s*logical\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
CHAR_SENTINELS = "#@$%&?+*/;:<>=^~|[]{}"


def body(text):
    return textwrap.dedent(text).strip() + "\n"


def clean_name(item):
    return item.split('=')[0].strip()


def declaration_types(lines):
    result = {}
    for line in lines:
        match = INTEGER_DECL.match(line)
        if match:
            for item in match.group('names').split(','):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("integer", None)
            continue
        match = CHARACTER_DECL.match(line)
        if match:
            length = int(match.group('len'))
            for item in match.group('names').split(','):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("character", length)
            continue
        match = LOGICAL_DECL.match(line)
        if match:
            for item in match.group('names').split(','):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("logical", None)
    return result


def find_read_expected(lines, index, target, category):
    if category == "integer":
        pattern = re.compile(r"call check_int\('[^']+',\s*" + re.escape(target) + r"\s*,\s*([^,)]+)\)", re.I)
    elif category == "character":
        pattern = re.compile(r"call check_char\('[^']+',\s*" + re.escape(target) + r"\s*,\s*('[^']*')\)", re.I)
    else:
        pattern = re.compile(r"call check_(true|false)\('[^']+',\s*" + re.escape(target) + r"\s*\)", re.I)
    for next_line in lines[index + 1:index + 12]:
        if READ_TARGET.match(next_line):
            break
        match = pattern.search(next_line)
        if match:
            return match.group(1) if category != "logical" else match.group(0)
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
        category, length = types[target]
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
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_int('{label}', {target}, {sentinel})")
            expected_init = expected.strip()
        elif category == "character":
            mark = CHAR_SENTINELS[(read_index - 1) % len(CHAR_SENTINELS)]
            sentinel = "'" + (mark * length) + "'"
            poison = "'" + ("!" * length) + "'"
            default = "'" + (" " * length) + "'"
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_char('{label}', {target}, {sentinel})")
            expected_init = expected.strip()
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
    src = CHECKS + "program p\nuse io_open_specifier_12_5_6_12_checks\n"
    src += "use iso_fortran_env, only: input_unit, output_unit, error_unit, iostat_eor\n"
    src += "implicit none\n" + main
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
            "evidence": "positive-control" if rule in POSITIVE_CONTROL_RULES else "effect",
            "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free",
                       "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0},
        }
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
            normalized.append((mid, textwrap.dedent(old).strip("\n"),
                               textwrap.dedent(new).strip("\n"), category))
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
            "evidence": "positive-control" if rule in POSITIVE_CONTROL_RULES else "effect",
            "checks": total_checks,
            "derivation": derivation,
            "mutants": [{"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in normalized],
        }


def build_corpus(root=ROOT):
    c = Corpus(root)

    c.add("12.5.6.13", "S12.5.6.13-002", "newunit_success_defined", [
        "newunit-success-defines-variable"], """
        integer :: u_success, u_spare
        u_success = 777
        u_spare = 778
        open(newunit=u_success, status='scratch', form='formatted', action='readwrite')
        call check_true('newunit-success-defined', u_success /= 777)
        close(u_success, status='delete')
    """, 1,
        "12.5.6.13 p2 defines the NEWUNIT variable on successful OPEN; a positive sentinel changes to a processor-selected unit value.",
        [("use-unit-instead-of-newunit",
          "        open(newunit=u_success, status='scratch', form='formatted', action='readwrite')",
          "        open(unit=u_success, status='scratch', form='formatted', action='readwrite')")])

    c.add("12.5.6.13", "S12.5.6.13-004", "newunit_negative_not_minus_one", [
        "newunit-negative-not-minus-one"], """
        integer :: u_neg, u_spare
        u_neg = 779
        u_spare = 780
        open(newunit=u_neg, status='scratch', form='formatted', action='readwrite')
        call check_true('newunit-negative', u_neg < 0)
        call check_true('newunit-not-minus-one', u_neg /= -1)
        close(u_neg, status='delete')
    """, 2,
        "12.5.6.13 p3 requires every NEWUNIT value to be negative and not -1; the assertions avoid the exact processor choice.",
        [("omit-newunit-for-negative-property",
          "        open(newunit=u_neg, status='scratch', form='formatted', action='readwrite')",
          "        open(unit=u_neg, status='scratch', form='formatted', action='readwrite')")])

    c.add("12.5.6.13", "S12.5.6.13-005", "newunit_not_standard_units", [
        "newunit-not-error-input-output-units"], """
        integer :: u_named, u_spare
        u_named = 781
        u_spare = 782
        open(newunit=u_named, status='scratch', form='formatted', action='readwrite')
        call check_true('newunit-not-input-unit', u_named /= input_unit)
        call check_true('newunit-not-output-unit', u_named /= output_unit)
        call check_true('newunit-not-error-unit', u_named /= error_unit)
        close(u_named, status='delete')
    """, 3,
        "12.5.6.13 p3 excludes INPUT_UNIT, OUTPUT_UNIT, and ERROR_UNIT from NEWUNIT values; only distinctness from named constants is asserted.",
        [("substitute-output-unit-value",
          "        open(newunit=u_named, status='scratch', form='formatted', action='readwrite')",
          "        u_named = output_unit\n        open(newunit=u_spare, status='scratch', form='formatted', action='readwrite')")])

    c.add("12.5.6.13", "S12.5.6.13-007", "newunit_unique_connected", [
        "newunit-unique-while-connected"], """
        integer :: u_first, u_second, u_spare
        u_first = 783
        u_second = 784
        u_spare = 785
        open(newunit=u_first, status='scratch', form='formatted', action='readwrite')
        open(newunit=u_second, status='scratch', form='formatted', action='readwrite')
        call check_true('newunit-unique-connected', u_first /= u_second)
        close(u_first, status='delete')
        close(u_second, status='delete')
    """, 1,
        "12.5.6.13 p3 forbids reuse of a NEWUNIT value while the previous NEWUNIT file is connected; two simultaneous scratch OPENs must differ.",
        [("reuse-first-newunit-variable",
          "        open(newunit=u_second, status='scratch', form='formatted', action='readwrite')",
          "        u_second = u_first\n        open(newunit=u_spare, status='scratch', form='formatted', action='readwrite')")])

    c.add("12.5.6.14", "S12.5.6.14-001", "pad_value_no_token", [
        "pad-value-set"], """
        integer :: u
        character(len=8) :: pad_mode
        pad_mode = '########'
        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='no')
        inquire(unit=u, pad=pad_mode)
        call check_char('pad-no-token', pad_mode, 'NO      ')
        close(u, status='delete')
    """, 1,
        "12.5.6.14 p1 lists NO as a PAD value; INQUIRE(PAD=) returns the fixed token for the formatted connection.",
        [("pad-no-to-yes-token",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='no')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='yes')")])

    c.add("12.5.6.14", "S12.5.6.14-003", "pad_no_eor_effect", [
        "pad-mode-effect"], """
        integer :: u, ios
        character(len=3) :: pad_field
        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='no')
        write(u,'(a)') 'Q'
        rewind u
        ios = -700
        call check_int('pad-ios-sentinel', ios, -700)
        pad_field = '###'
        call check_char('pad-field-sentinel', pad_field, '###')
        read(u,'(a3)', iostat=ios, advance='no') pad_field(1:3)
        call check_int('pad-no-eor-status', ios, iostat_eor)
        call check_char('pad-no-target-unchanged', pad_field, '###')
        close(u, status='delete')
    """, 4,
        "12.5.6.14 p1 makes PAD= specify the input pad mode; with PAD='NO' a short nonadvancing read reaches the EOR condition instead of padding.",
        [("pad-no-to-yes-eor",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='no')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='yes')"),
         ("pad-short-record-made-long-enough",
          "        write(u,'(a)') 'Q'",
          "        write(u,'(a)') 'Q  '", "feature"),
         ("pad-ios-sentinel-default", "        ios = -700", "        ios = 0", "sentinel"),
         ("pad-field-sentinel-default", "        pad_field = '###'", "        pad_field = '   '", "sentinel")])

    c.add("12.5.6.14", "S12.5.6.14-005", "pad_changeable_mode", [
        "pad-changeable-mode"], """
        integer :: u
        character(len=8) :: pad_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='yes')
        open(unit=u, pad='no')
        pad_mode = '########'
        inquire(unit=u, pad=pad_mode)
        call check_char('pad-changeable-no-token', pad_mode, 'NO      ')
        close(u, status='delete')
    """, 1,
        "12.5.6.14 p1 says PAD is changeable; a same-unit OPEN changes a formatted connection from YES to NO as observed by INQUIRE.",
        [("pad-change-to-yes-instead",
          "        open(unit=u, pad='no')",
          "        open(unit=u, pad='yes')")])

    c.add("12.5.6.14", "S12.5.6.14-006", "pad_default_yes", [
        "pad-default-yes"], """
        integer :: u
        character(len=8) :: pad_mode
        pad_mode = '%%%%%%%%'
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, pad=pad_mode)
        call check_char('pad-default-yes-token', pad_mode, 'YES     ')
        close(u, status='delete')
    """, 1,
        "12.5.6.14 p1 makes omitted PAD default to YES for an initiating OPEN; INQUIRE observes that default token.",
        [("pad-default-made-no",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', pad='no')")])

    c.add("12.5.6.15", "S12.5.6.15-004", "position_rewind_existing", [
        "position-rewind-initial"], """
        integer :: u, ios
        character(len=5) :: rec
        open(newunit=u, file='ioos_12_5_6_12_rewind.dat', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(a)') 'FIRST'
        write(u,'(a)') 'SECND'
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_rewind.dat', status='old', &
             form='formatted', action='readwrite', position='rewind')
        rec = '#####'
        read(u,'(a5)', iostat=ios) rec
        call check_int('position-rewind-read-status', ios, 0)
        call check_char('position-rewind-first-record', rec, 'FIRST')
        close(u, status='delete')
    """, 2,
        "12.5.6.15 p1 says POSITION='REWIND' positions an existing file at its initial point; the first of two records is read next.",
        [("position-rewind-to-append",
          "             form='formatted', action='readwrite', position='rewind')",
          "             form='formatted', action='readwrite', position='append')")])

    c.add("12.5.6.15", "S12.5.6.15-007", "position_asis_connected", [
        "position-asis-connected-unchanged"], """
        integer :: u, ios
        character(len=5) :: rec
        open(newunit=u, file='ioos_12_5_6_12_asis.dat', status='replace', &
             form='formatted', action='readwrite')
        write(u,'(a)') 'FIRST'
        write(u,'(a)') 'SECND'
        rewind u
        rec = '#####'
        read(u,'(a5)', iostat=ios) rec
        call check_int('position-asis-first-status', ios, 0)
        call check_char('position-asis-first-record', rec, 'FIRST')
        open(unit=u, position='asis')
        rec = '@@@@@'
        read(u,'(a5)', iostat=ios) rec
        call check_int('position-asis-next-status', ios, 0)
        call check_char('position-asis-next-record', rec, 'SECND')
        close(u, status='delete')
    """, 4,
        "12.5.6.15 p1 says ASIS leaves position unchanged for an existing connected file; after one read, same-unit OPEN leaves the second record next.",
        [("position-asis-to-rewind",
          "        open(unit=u, position='asis')",
          "        rewind u")])

    c.add("12.5.6.15", "S12.5.6.15-006", "position_append_stream_terminal", [
        "position-append-terminal-no-endfile"], """
        integer :: u, ios, char_units
        character(len=1) :: ch
        inquire(iolength=char_units) ch
        open(newunit=u, file='ioos_12_5_6_12_stream.dat', status='replace', &
             access='stream', form='unformatted', action='readwrite')
        write(u, pos=1) 'A'
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_stream.dat', status='old', &
             access='stream', form='unformatted', action='readwrite', position='append')
        write(u) 'B'
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_stream.dat', status='old', &
             access='stream', form='unformatted', action='read')
        ch = '#'
        read(u, pos=1, iostat=ios) ch
        call check_int('position-append-stream-first-status', ios, 0)
        call check_char('position-append-stream-first', ch, 'A')
        ch = '@'
        read(u, pos=1+char_units, iostat=ios) ch
        call check_int('position-append-stream-second-status', ios, 0)
        call check_char('position-append-stream-second', ch, 'B')
        close(u, status='delete')
    """, 4,
        "12.5.6.15 p1 positions an existing stream file with no endfile at its terminal point under APPEND; IOLENGTH-derived positions show A then appended B.",
        [("position-append-stream-to-rewind",
          "             access='stream', form='unformatted', action='readwrite', position='append')",
          "             access='stream', form='unformatted', action='readwrite', position='rewind')")])

    c.add("12.5.6.15", "S12.5.6.15-005", "position_append_before_endfile", [
        "position-append-before-endfile"], """
        integer :: u, ios
        character(len=5) :: rec
        open(newunit=u, file='ioos_12_5_6_12_endfile.dat', status='replace', &
             form='formatted', action='write')
        write(u,'(a)') 'ONE  '
        endfile u
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_endfile.dat', status='old', &
             form='formatted', action='readwrite', position='append')
        write(u,'(a)') 'TWO  '
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_endfile.dat', status='old', &
             form='formatted', action='read')
        rec = '#####'
        read(u,'(a5)', iostat=ios) rec
        call check_int('position-append-endfile-first-status', ios, 0)
        call check_char('position-append-endfile-first', rec, 'ONE  ')
        rec = '@@@@@'
        read(u,'(a5)', iostat=ios) rec
        call check_int('position-append-endfile-second-status', ios, 0)
        call check_char('position-append-endfile-second', rec, 'TWO  ')
        close(u, status='delete')
    """, 4,
        "12.5.6.15 p1 says APPEND positions before an existing endfile record; a later write replaces that endfile so the two data records read in order.",
        [("position-append-endfile-to-rewind",
          "             form='formatted', action='readwrite', position='append')",
          "             form='formatted', action='readwrite', position='rewind')")])

    c.add("12.5.6.15", "S12.5.6.15-001", "position_value_append_token", [
        "position-value-set-asis-rewind-append"], """
        integer :: u
        character(len=8) :: pos_mode
        open(newunit=u, file='ioos_12_5_6_12_pos_token.dat', status='replace', &
             access='stream', form='unformatted', action='readwrite')
        write(u, pos=1) 'A'
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_pos_token.dat', status='old', &
             access='stream', form='unformatted', action='readwrite', position='append')
        pos_mode = '########'
        inquire(unit=u, position=pos_mode)
        call check_char('position-append-token', pos_mode, 'APPEND  ')
        close(u, status='delete')
    """, 1,
        "12.5.6.15 p1 lists APPEND as a POSITION value; on an existing stream file, INQUIRE(POSITION=) observes end positioning.",
        [("position-append-token-to-rewind",
          "             access='stream', form='unformatted', action='readwrite', position='append')",
          "             access='stream', form='unformatted', action='readwrite', position='rewind')")])

    c.add("12.5.6.16", "S12.5.6.16-002", "recl_direct_record_length", [
        "recl-direct-record-length"], """
        integer :: u, ios, reclen, value
        value = 12345
        inquire(iolength=reclen) value
        open(newunit=u, file='ioos_12_5_6_12_direct.dat', status='replace', &
             access='direct', form='unformatted', recl=reclen, action='readwrite')
        write(u, rec=1, iostat=ios) value
        call check_int('recl-direct-write-status', ios, 0)
        value = -1
        read(u, rec=1, iostat=ios) value
        call check_int('recl-direct-read-status', ios, 0)
        call check_int('recl-direct-read-value', value, 12345)
        close(u, status='delete')
    """, 3,
        "12.5.6.16 p1 makes RECL the direct-access record length; an INQUIRE(IOLENGTH=) length admits exact unformatted direct read-back.",
        [("direct-write-different-record",
          "        write(u, rec=1, iostat=ios) value",
          "        write(u, rec=2, iostat=ios) value")])

    c.add("12.5.6.16", "S12.5.6.16-009", "recl_unformatted_storage_units", [
        "recl-unformatted-file-storage-units"], """
        integer :: u, ios, reclen, a, b
        a = 17
        b = 29
        inquire(iolength=reclen) a, b
        open(newunit=u, file='ioos_12_5_6_12_fsu.dat', status='replace', &
             access='direct', form='unformatted', recl=reclen, action='readwrite')
        write(u, rec=1, iostat=ios) a, b
        call check_int('recl-fsu-write-status', ios, 0)
        a = -1
        b = -2
        read(u, rec=1, iostat=ios) a, b
        call check_int('recl-fsu-read-status', ios, 0)
        call check_int('recl-fsu-a', a, 17)
        call check_int('recl-fsu-b', b, 29)
        close(u, status='delete')
    """, 4,
        "12.5.6.16 p1 measures unformatted RECL in file storage units; INQUIRE(IOLENGTH=) supplies the processor's required units for two integers.",
        [("unformatted-record-omits-second-item",
          "        write(u, rec=1, iostat=ios) a, b",
          "        write(u, rec=1, iostat=ios) a")])

    c.add("12.5.6.16", "S12.5.6.16-011", "recl_new_file_length_included", [
        "recl-new-file-length-included"], """
        integer :: u, ios, reclen, value
        value = 2468
        inquire(iolength=reclen) value
        open(newunit=u, file='ioos_12_5_6_12_newrecl.dat', status='replace', &
             access='direct', form='unformatted', recl=reclen, action='readwrite')
        write(u, rec=1, iostat=ios) value
        call check_int('recl-new-file-write-status', ios, 0)
        value = -1
        read(u, rec=1, iostat=ios) value
        call check_int('recl-new-file-read-status', ios, 0)
        call check_int('recl-new-file-value', value, 2468)
        close(u, status='delete')
    """, 3,
        "12.5.6.16 p1 creates a new file whose allowed record lengths include the specified RECL; the matching direct transfer succeeds.",
        [("new-file-direct-to-sequential",
          "             access='direct', form='unformatted', recl=reclen, action='readwrite')",
          "             access='sequential', form='unformatted', action='readwrite')")])

    c.add("12.5.6.16", "S12.5.6.16-010", "recl_existing_length_allowed", [
        "recl-existing-file-length-allowed"], """
        integer :: u, ios, reclen, value
        value = 1357
        inquire(iolength=reclen) value
        open(newunit=u, file='ioos_12_5_6_12_oldrecl.dat', status='replace', &
             access='direct', form='unformatted', recl=reclen, action='readwrite')
        write(u, rec=1) value
        close(u)
        open(newunit=u, file='ioos_12_5_6_12_oldrecl.dat', status='old', &
             access='direct', form='unformatted', recl=reclen, action='readwrite')
        value = -1
        read(u, rec=1, iostat=ios) value
        call check_int('recl-existing-read-status', ios, 0)
        call check_int('recl-existing-value', value, 1357)
        close(u, status='delete')
    """, 2,
        "12.5.6.16 p1 requires an existing-file RECL to be an allowed length; reopening with the length used to create the direct file reads the record.",
        [("existing-recl-replace-file",
          "status='old'",
          "status='replace'")])

    c.add("12.5.6.17", "S12.5.6.17-001", "round_value_up_token", [
        "round-value-set"], """
        integer :: u
        character(len=17) :: round_mode
        round_mode = '#################'
        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='up')
        inquire(unit=u, round=round_mode)
        call check_char('round-up-token', round_mode, 'UP               ')
        close(u, status='delete')
    """, 1,
        "12.5.6.17 p1 lists UP as a ROUND value; INQUIRE(ROUND=) returns the fixed token for that formatted connection.",
        [("round-up-to-down-token",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='up')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='down')")])

    c.add("12.5.6.17", "S12.5.6.17-003", "round_mode_effect", [
        "round-mode-effect"], """
        integer :: u, ios
        character(len=4) :: field
        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='up')
        write(u,'(ss,f4.1)') 1.125
        rewind u
        field = '####'
        read(u,'(a4)', iostat=ios) field
        call check_int('round-up-read-status', ios, 0)
        call check_char('round-up-field', field, ' 1.2')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='down')
        write(u,'(ss,f4.1)') 1.125
        rewind u
        field = '@@@@'
        read(u,'(a4)', iostat=ios) field
        call check_int('round-down-read-status', ios, 0)
        call check_char('round-down-field', field, ' 1.1')
        close(u, status='delete')
    """, 4,
        "12.5.6.17 p1 specifies the I/O rounding mode; exact 1.125 is not a tie for F4.1, so UP gives 1.2 and DOWN gives 1.1.",
        [("round-up-to-down-output",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='up')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='down')"),
         ("round-down-to-up-output",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='down')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='up')")])

    c.add("12.5.6.17", "S12.5.6.17-004", "round_changeable_mode", [
        "round-changeable-mode"], """
        integer :: u, ios
        character(len=4) :: field
        character(len=17) :: round_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite', round='down')
        open(unit=u, round='up')
        round_mode = '#################'
        inquire(unit=u, round=round_mode)
        call check_char('round-changeable-up-token', round_mode, 'UP               ')
        write(u,'(ss,f4.1)') 1.125
        rewind u
        field = '####'
        read(u,'(a4)', iostat=ios) field
        call check_int('round-changeable-read-status', ios, 0)
        call check_char('round-changeable-field', field, ' 1.2')
        close(u, status='delete')
    """, 3,
        "12.5.6.17 p1 says ROUND is changeable; after same-unit OPEN changes DOWN to UP, INQUIRE and F output observe UP.",
        [("round-changeable-keeps-down",
          "        open(unit=u, round='up')",
          "        open(unit=u, round='down')")])

    c.add("12.5.6.17", "S12.5.6.17-006", "round_default_listed_mode", [
        "round-default-one-of-listed-modes"], """
        integer :: u
        character(len=17) :: round_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        round_mode = '#################'
        inquire(unit=u, round=round_mode)
        call check_true('round-default-listed', &
             trim(round_mode) == 'UP' .or. trim(round_mode) == 'DOWN' .or. &
             trim(round_mode) == 'ZERO' .or. trim(round_mode) == 'NEAREST' .or. &
             trim(round_mode) == 'COMPATIBLE' .or. trim(round_mode) == 'PROCESSOR_DEFINED')
        close(u, status='delete')
    """, 1,
        "12.5.6.17 p1 makes the omitted ROUND mode processor dependent but one of the six listed modes; INQUIRE returns a member token only.",
        [("round-default-inquire-after-close",
          "        inquire(unit=u, round=round_mode)",
          "        close(u, status='delete')\n        inquire(unit=u, round=round_mode)")])

    c.add("12.5.6.18", "S12.5.6.18-001", "sign_value_tokens", [
        "sign-value-set"], """
        integer :: u
        character(len=17) :: sign_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')
        sign_mode = '#################'
        inquire(unit=u, sign=sign_mode)
        call check_char('sign-plus-token', sign_mode, 'PLUS             ')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')
        sign_mode = '@@@@@@@@@@@@@@@@@'
        inquire(unit=u, sign=sign_mode)
        call check_char('sign-suppress-token', sign_mode, 'SUPPRESS         ')
        close(u, status='delete')
    """, 2,
        "12.5.6.18 p1 lists PLUS and SUPPRESS as SIGN values; INQUIRE(SIGN=) returns their fixed tokens.",
        [("sign-plus-token-to-suppress",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')"),
         ("sign-suppress-token-to-plus",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')")])

    c.add("12.5.6.18", "S12.5.6.18-003", "sign_mode_effect", [
        "sign-mode-effect"], """
        integer :: u, ios
        character(len=2) :: field
        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')
        write(u,'(i2)') 7
        rewind u
        field = '##'
        read(u,'(a2)', iostat=ios) field
        call check_int('sign-plus-read-status', ios, 0)
        call check_char('sign-plus-field', field, '+7')
        close(u, status='delete')
        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')
        write(u,'(i2)') 7
        rewind u
        field = '@@'
        read(u,'(a2)', iostat=ios) field
        call check_int('sign-suppress-read-status', ios, 0)
        call check_char('sign-suppress-field', field, ' 7')
        close(u, status='delete')
    """, 4,
        "12.5.6.18 p1 sets the connection sign mode; SIGN='PLUS' emits +7 while SIGN='SUPPRESS' emits blank-plus suppression for positive I output.",
        [("sign-plus-output-to-suppress",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')"),
         ("sign-suppress-output-to-plus",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')")])

    c.add("12.5.6.18", "S12.5.6.18-004", "sign_changeable_mode", [
        "sign-changeable-mode"], """
        integer :: u, ios
        character(len=2) :: field
        character(len=17) :: sign_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='suppress')
        open(unit=u, sign='plus')
        sign_mode = '#################'
        inquire(unit=u, sign=sign_mode)
        call check_char('sign-changeable-plus-token', sign_mode, 'PLUS             ')
        write(u,'(i2)') 8
        rewind u
        field = '##'
        read(u,'(a2)', iostat=ios) field
        call check_int('sign-changeable-read-status', ios, 0)
        call check_char('sign-changeable-field', field, '+8')
        close(u, status='delete')
    """, 3,
        "12.5.6.18 p1 says SIGN is changeable; same-unit OPEN changes SUPPRESS to PLUS and exact I output shows the plus sign.",
        [("sign-changeable-keeps-suppress",
          "        open(unit=u, sign='plus')",
          "        open(unit=u, sign='suppress')")])

    c.add("12.5.6.18", "S12.5.6.18-005", "sign_default_processor_defined", [
        "sign-default-token-processor-defined"], """
        integer :: u
        character(len=17) :: sign_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        sign_mode = '#################'
        inquire(unit=u, sign=sign_mode)
        call check_char('sign-default-processor-defined', sign_mode, 'PROCESSOR_DEFINED')
        close(u, status='delete')
    """, 1,
        "12.5.6.18 p1 makes omitted SIGN default to PROCESSOR_DEFINED for an initiating formatted OPEN; INQUIRE observes that token.",
        [("sign-default-made-plus",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', sign='plus')")])

    return c.files, c.cases


def owned_paragraph(existing, marker, replacement):
    paragraphs = existing.split("\n\n") if existing else []
    updated = []
    replaced = False
    for para in paragraphs:
        if para.startswith(marker):
            if not replaced:
                updated.append(replacement)
                replaced = True
        else:
            updated.append(para)
    if not replaced:
        updated.append(replacement)
    return "\n\n".join(updated)


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
            raise ValueError(f"pending mismatch for {requirement['id']}: {set(requirement['pending'])} != {expected_pending}")
        if selected:
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered))
            text = ("OPEN specifier 12.5.6.12 fixture implementation: "
                    f"{len(selected)} valid run-phase program(s) cover {labels}. "
                    "Runtime oracles use scratch or run-directory files, INQUIRE tokens, named IOSTAT constants, "
                    "INQUIRE(IOLENGTH=)-derived record lengths, exact character/integer/logical values, and IOSTAT zero only. "
                    "No IOMSG text, processor-dependent ordinary unit number, physical device, byte offset, or numeric nonzero status is asserted.")
            requirement["oracle"] = owned_paragraph(requirement["oracle"],
                                                     "OPEN specifier 12.5.6.12 fixture implementation:", text)
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
        raise SystemExit("stale io_open_specifiers_12_5_6_12 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std, keep=False):
    files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_open_specifiers_12_5_6_12" / digest
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
                built = subprocess.run(compiler_command(compiler, std) + [str(src), "-o", str(exe)],
                                       cwd=work, text=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, timeout=30)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, timeout=30)
                if ran.returncode == 0 and ran.stdout == "" and ran.stderr == "":
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
