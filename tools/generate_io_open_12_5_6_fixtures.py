#!/usr/bin/env python3
"""Generate Clause 12.5.5/12.5.6.1/12.5.6.2 OPEN fixtures."""
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
TOPIC = "io_open_12_5_6"
CATALOGUES = {
    "12.5.5": "doc/catalogues/preconnection_12_5_5.json",
    "12.5.6.1": "doc/catalogues/effect_of_open_statement_12_5_6_1.json",
    "12.5.6.2": "doc/catalogues/open_statement_syntax_12_5_6_2.json",
}
VIEWS = {
    "12.5.5": "doc/fortran_2023_12_5_5.md",
    "12.5.6.1": "doc/fortran_2023_12_5_6_1.md",
    "12.5.6.2": "doc/fortran_2023_12_5_6_2.md",
}
VIEW_TITLES = {
    "12.5.5": "Preconnection",
    "12.5.6.1": "Effect of the OPEN statement",
    "12.5.6.2": "OPEN statement syntax",
}

RESTORED_PENDING = {
    ("S12.5.6.1-003", "preconnected-nonexistent-same-file-modes-attach"):
        "Left pending: no portable profile in this suite exposes a suitable preconnected file name that is the same "
        "as a nonexistent file, so a single-image fixture would assume processor-dependent preconnection details.",
    ("S12.5.6.1-010", "same-file-open-waits-for-pending-async"):
        "Left pending: asynchronous transfer completion needs the later asynchronous I/O rules and processor support; "
        "this packet does not treat an unsupported branch as coverage.",
    ("S12.5.6.1-011", "same-file-open-position-must-agree"):
        "Left pending: this prose shall restriction is not a numbered constraint, so no portable diagnostic is required; "
        "positive same-file OPEN controls are covered separately.",
    ("S12.5.6.1-012", "same-file-open-status-must-be-old"):
        "Left pending: this prose shall restriction is not a numbered constraint, so no portable diagnostic is required; "
        "the conforming STATUS='OLD' same-file OPEN is covered separately.",
    ("S12.5.6.1-013", "same-file-open-nonchangeable-specifiers-match"):
        "Left pending: this prose shall restriction is not a numbered constraint, so no portable diagnostic is required; "
        "same-file controls avoid differing non-changeable specifiers.",
    ("S12.5.6.1-015", "same-file-open-scratch-status-preserved"):
        "Left pending: an unnamed scratch file's later deletion/status cannot be observed portably without asserting "
        "processor-dependent scratch names or filesystem exposure.",
    ("R1205", "connect-spec-asynchronous"):
        "Left pending: ASYNCHRONOUS='YES' is processor-support dependent here and the supported ASYNCHRONOUS='NO' "
        "case has no conforming feature mutation that both reference toolchains distinguish.",
    ("R1205", "connect-spec-iomsg"):
        "Left pending: successful OPEN leaves IOMSG unchanged and error text is not portable; this syntax alternative "
        "needs a non-vacuous portable feature mutation before claiming coverage.",
    ("R1205", "connect-spec-leading-zero"):
        "Left pending: the reference gfortran on this host rejects LEADING_ZERO= in OPEN, so no reference-validated "
        "fixture can be shipped.",
    ("R1207", "iomsg-variable-scalar-default-character"):
        "Left pending: R1207's positive IOMSG variable form has no portable non-vacuous runtime oracle in this packet; "
        "the required non-variable diagnostic is covered.",
    ("S12.5.6.2-001", "omitted-specifier-defaults-exist"):
        "Left pending: concrete default-token behavior belongs to the individual specifier catalogues; this packet "
        "does not assert processor-dependent defaults or INQUIRE states that are not fixed here.",
}

CHECKS = r'''
module io_open_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_nonzero, check_char, check_true, check_false, finish_checks
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
subroutine check_nonzero(label, actual)
character(*), intent(in) :: label
integer, intent(in) :: actual
if (actual == 0) then
print *, 'CHECK_NONZERO', label, 'ACTUAL', actual
error stop 2
end if
checked = checked + 1
end subroutine check_nonzero
subroutine check_char(label, actual, expected)
character(*), intent(in) :: label
character(*), intent(in) :: actual, expected
if (len(actual) /= len(expected)) then
print *, 'CHECK_CHAR_LEN', label, len(actual), len(expected)
error stop 3
end if
if (actual /= expected) then
print *, 'CHECK_CHAR', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 4
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
error stop 5
end if
end subroutine finish_checks
end module io_open_checks
'''.lstrip()

READ_TARGETS = [
    re.compile(r"^(?P<indent>\s*)read\s*\(.*\)\s*(?P<target>[A-Za-z]\w*)\s*$", re.I),
]
INTEGER_DECL = re.compile(r"^\s*integer\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
CHARACTER_DECL = re.compile(r"^\s*character\s*\(\s*len\s*=\s*(?P<len>\d+)\s*\)\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
CHAR_SENTINELS = "#@$%&?+*/;:<>=^~|[]{}"


def body(text):
    return textwrap.dedent(text).strip() + "\n"


def clean_name(item):
    return item.split('=')[0].strip()


def read_match(line):
    for pattern in READ_TARGETS:
        match = pattern.match(line)
        if match:
            return match
    return None


def declaration_types(lines):
    result = {}
    for line in lines:
        match = INTEGER_DECL.match(line)
        if match:
            for item in match.group("names").split(","):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("integer", None)
            continue
        match = CHARACTER_DECL.match(line)
        if match:
            length = int(match.group("len"))
            for item in match.group("names").split(","):
                name = clean_name(item)
                if re.match(r"^[A-Za-z]\w*$", name):
                    result[name] = ("character", length)
    return result


def find_read_expected(lines, index, target, category):
    if category == "integer":
        pattern = re.compile(r"call check_int\('[^']+',\s*" + re.escape(target) + r"\s*,\s*([^,)]+)\)", re.I)
    else:
        pattern = re.compile(r"call check_char\('[^']+',\s*" + re.escape(target) + r"\s*,\s*('[^']*')\)", re.I)
    for next_line in lines[index + 1:index + 10]:
        if read_match(next_line):
            break
        match = pattern.search(next_line)
        if match:
            return match.group(1).strip()
    raise ValueError(f"read target {target} has no following value oracle")


def add_pre_read_guards(main):
    lines = main.splitlines()
    types = declaration_types(lines)
    output = []
    probes = []
    read_index = 0
    for index, line in enumerate(lines):
        match = read_match(line)
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
            (f"{label}-remove-sentinel-init", sentinel_line,
             f"{indent}! sentinel initializer removed for probe", "sentinel"),
            (f"{label}-expected-sentinel-init", sentinel_line,
             f"{indent}{target} = {expected}", "sentinel"),
            (f"{label}-default-sentinel-init", sentinel_line,
             f"{indent}{target} = {default}", "sentinel"),
        ])
        output.append(line)
    return "\n".join(output) + "\n", probes


def source(body_text, count, uses_iso=False):
    main, probes = add_pre_read_guards(body(body_text))
    total = count + sum(1 for _, _, _, category in probes if category == "sentinel") // 3
    src = CHECKS + "program p\nuse io_open_checks\n"
    if uses_iso:
        src += "use iso_fortran_env, only: output_unit, error_unit\n"
    src += "implicit none\n"
    if re.search(r"(?im)^\s*contains\s*$", main):
        main = re.sub(r"(?im)^\s*contains\s*$", f"call finish_checks({total})\ncontains", main, count=1)
        src += main + "end program p\n"
    else:
        src += main + f"call finish_checks({total})\nend program p\n"
    return src, total, probes


def ident(rule, variant, kind="valid"):
    return rule.replace('.', '_').replace('-', '_') + f"_{kind}__" + TOPIC + "_" + variant


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

    def add_valid(self, section, rule, variant, facets, body_text, checks, derivation, mutants,
                  stdout=None, stderr=None, uses_iso=False):
        name = ident(rule, variant, "valid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src, total_checks, sentinel_probes = source(body_text, checks, uses_iso=uses_iso)
        expect = {"phase": "run", "outcome": "success", "exit_code": 0}
        if stdout is not None:
            expect["stdout"] = stdout
        if stderr is not None:
            expect["stderr"] = stderr
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
            "expect": expect,
        }
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        normalized = []
        for item in mutants:
            if len(item) == 3:
                mid, old, new = item
                category = "feature"
            else:
                mid, old, new, category = item
            normalized.append((mid, textwrap.dedent(old).strip("\n"),
                               textwrap.dedent(new).strip("\n"), category))
        normalized += sentinel_probes
        for mid, old, _new, _category in normalized:
            if old not in src:
                raise ValueError(f"{name}: mutant span not found: {mid} -> {old}")
            if src.count(old) != 1:
                raise ValueError(f"{name}: mutant span not unique: {mid} -> {old}")
        self.cases[name] = {
            "section": section,
            "rule": rule,
            "variant": variant,
            "facets": list(facets),
            "path": folder + "/fixture.json",
            "source_path": folder + "/source.f90",
            "kind": "valid",
            "evidence": "effect",
            "checks": total_checks,
            "derivation": derivation,
            "stdout": stdout,
            "stderr": stderr,
            "mutants": [{"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in normalized],
        }

    def add_invalid(self, section, rule, variant, facets, source_text, derivation, diagnostic_line,
                    contains_any, control_id, diagnostic_end_line=None):
        name = ident(rule, variant, "invalid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src = body(source_text)
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
            "expect": {
                "phase": "compile",
                "outcome": "diagnose",
                "step": "source",
                "diagnostic": {
                    "file": "source.f90",
                    "line": diagnostic_line,
                    "contains_any": contains_any,
                    "excludes_any": [
                        "not implemented", "not yet implemented", "unimplemented", "unsupported feature",
                        "unsupported", "not supported", "not yet supported", "implementation limitation",
                        "ASR verify", "ASR verifier", "internal compiler error", "LLVM ERROR",
                        "unexpected end of file", "unexpected eof", "out of memory",
                    ],
                },
            },
        }
        if diagnostic_end_line is not None:
            manifest["expect"]["diagnostic"]["end_line"] = diagnostic_end_line
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = {
            "section": section,
            "rule": rule,
            "variant": variant,
            "facets": list(facets),
            "path": folder + "/fixture.json",
            "source_path": folder + "/source.f90",
            "kind": "invalid",
            "evidence": "effect",
            "checks": 0,
            "derivation": derivation,
            "diagnostic_line": diagnostic_line,
            "contains_any": contains_any,
            "control": control_id,
            "mutants": [],
        }

    def add_control(self, section, rule, variant, facets, source_text, derivation, control_for):
        name = ident(rule, variant, "valid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src = body(source_text)
        manifest = {
            "schema_version": 1,
            "id": name,
            "rule": rule,
            "facets": list(facets),
            "standard": "f2023",
            "evidence": "positive-control",
            "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free",
                       "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0},
        }
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = {
            "section": section,
            "rule": rule,
            "variant": variant,
            "facets": list(facets),
            "path": folder + "/fixture.json",
            "source_path": folder + "/source.f90",
            "kind": "valid",
            "evidence": "positive-control",
            "checks": 0,
            "derivation": derivation,
            "stdout": None,
            "stderr": None,
            "control_for": control_for,
            "mutants": [],
        }


def build_corpus(root=ROOT):
    c = Corpus(root)

    c.add_valid("12.5.5", "S12.5.5-001", "preconnected_output_beginning",
        ["preconnection-at-program-beginning"], """
        write(output_unit,'(a)') 'PRECONNECTED-BEGINNING'
    """, 0,
        "12.5.5 p1 says preconnection exists at program beginning; OUTPUT_UNIT writes before any OPEN.",
        [("output-unit-routed-to-error", "        write(output_unit,'(a)') 'PRECONNECTED-BEGINNING'",
          "        write(error_unit,'(a)') 'PRECONNECTED-BEGINNING'")],
        stdout="PRECONNECTED-BEGINNING\n", stderr="", uses_iso=True)

    c.add_valid("12.5.5", "S12.5.5-002", "preconnected_without_open",
        ["preconnected-unit-io-without-open"], """
        write(*,'(a)') 'PRECONNECTED-NO-OPEN'
    """, 0,
        "12.5.5 p1 permits a preconnected unit in I/O without prior OPEN; WRITE * emits an exact record.",
        [("star-output-routed-to-error", "        write(*,'(a)') 'PRECONNECTED-NO-OPEN'",
          "        write(error_unit,'(a)') 'PRECONNECTED-NO-OPEN'")],
        stdout="PRECONNECTED-NO-OPEN\n", stderr="", uses_iso=True)

    c.add_valid("12.5.6.1", "S12.5.6.1-001", "open_create_modify_connection",
        ["open-initiates-connection", "open-modifies-connection", "open-connects-or-creates-file"], """
        integer :: u, ios, value, changed
        logical :: opened
        character(len=29) :: name
        character(len=4) :: blank_mode
        open(newunit=u, file='io_open_create_modify.dat', status='replace', form='formatted', &
             action='readwrite', blank='null', iostat=ios)
        call check_int('open-initiates-iostat', ios, 0)
        opened = .false.
        name = '#############################'
        inquire(unit=u, opened=opened, name=name)
        call check_true('open-created-unit-opened', opened)
        call check_char('open-created-file-name', name, 'io_open_create_modify.dat    ')
        write(u,'(a)') '1 2'
        rewind u
        read(u,'(i3)',iostat=ios) value
        call check_int('initial-blank-null-status', ios, 0)
        call check_int('initial-blank-null-value', value, 12)
        open(unit=u, blank='zero', iostat=ios)
        call check_int('open-modifies-iostat', ios, 0)
        blank_mode = '####'
        inquire(unit=u, blank=blank_mode)
        call check_char('open-modified-blank-mode', blank_mode, 'ZERO')
        rewind u
        read(u,'(i3)',iostat=ios) changed
        call check_int('modified-blank-zero-status', ios, 0)
        call check_int('modified-blank-zero-value', changed, 102)
        close(u, status='delete')
    """, 9,
        "12.5.6.1 p1 lets OPEN initiate a named connection, create/connect a file, and later change BLANK mode; "
        "exact BLANK NULL/ZERO reads distinguish 12 from 102.",
        [("created-name-other-file", "        call check_char('open-created-file-name', name, 'io_open_create_modify.dat    ')",
          "        call check_char('open-created-file-name', name, 'io_open_other_name.dat     ')", "hygiene"),
         ("modify-open-keeps-null", "        open(unit=u, blank='zero', iostat=ios)",
          "        open(unit=u, blank='null', iostat=ios)"),
         ("created-file-name-changed", "        open(newunit=u, file='io_open_create_modify.dat', status='replace', form='formatted', &",
          "        open(newunit=u, file='io_open_create_other.dat', status='replace', form='formatted', &"),
         ("initial-open-scratch", "        open(newunit=u, file='io_open_create_modify.dat', status='replace', form='formatted', &\n             action='readwrite', blank='null', iostat=ios)",
          "        open(newunit=u, status='scratch', form='formatted', &\n             action='readwrite', blank='null', iostat=ios)")])

    c.add_valid("12.5.6.1", "S12.5.6.1-002", "open_main_and_subprogram",
        ["open-in-main-program-permitted", "open-in-subprogram-permitted"], """
        integer :: main_u, sub_u, ios, main_value, sub_value
        open(newunit=main_u, file='io_open_main.dat', status='replace', form='formatted', action='readwrite')
        write(main_u,'(i0)') 31
        rewind main_u
        read(main_u,*,iostat=ios) main_value
        call check_int('main-open-read-status', ios, 0)
        call check_int('main-open-read-value', main_value, 31)
        call connect_in_subprogram(sub_u)
        rewind sub_u
        read(sub_u,*,iostat=ios) sub_value
        call check_int('subprogram-open-read-status', ios, 0)
        call check_int('subprogram-open-read-value', sub_value, 42)
        close(main_u, status='delete')
        close(sub_u, status='delete')
        contains
        subroutine connect_in_subprogram(unit)
        integer, intent(out) :: unit
        open(newunit=unit, file='io_open_sub.dat', status='replace', form='formatted', action='readwrite')
        write(unit,'(i0)') 42
        end subroutine connect_in_subprogram
    """, 4,
        "12.5.6.1 p2 permits OPEN in the main program and any subprogram; exact read-backs prove both connections.",
        [("main-open-record-changed", "        write(main_u,'(i0)') 31", "        write(main_u,'(i0)') 32"),
         ("subprogram-open-record-changed", "        write(unit,'(i0)') 42", "        write(unit,'(i0)') 43")])

    c.add_valid("12.5.6.1", "S12.5.6.1-004", "open_different_file_implies_close",
        ["open-different-file-implies-close-without-status"], """
        integer :: u, ios, value
        logical :: first_opened
        character(len=28) :: name
        open(newunit=u, file='io_open_first_file.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 61
        open(unit=u, file='io_open_second_file.dat', status='replace', form='formatted', action='readwrite')
        first_opened = .true.
        inquire(file='io_open_first_file.dat', opened=first_opened)
        call check_false('first-file-no-longer-opened', first_opened)
        name = '############################'
        inquire(unit=u, name=name)
        call check_char('unit-now-second-file', name, 'io_open_second_file.dat     ')
        write(u,'(i0)') 62
        rewind u
        read(u,*,iostat=ios) value
        call check_int('second-file-read-status', ios, 0)
        call check_int('second-file-read-value', value, 62)
        close(u, status='delete')
        open(newunit=u, file='io_open_first_file.dat', status='old', form='formatted', action='readwrite')
        close(u, status='delete')
    """, 4,
        "12.5.6.1 p4 gives a different-file OPEN the effect of CLOSE-without-STATUS first; INQUIRE sees the "
        "first file no longer open and subsequent exact I/O reaches the second file.",
        [("second-open-same-first-file", "        open(unit=u, file='io_open_second_file.dat', status='replace', form='formatted', action='readwrite')",
          "        open(unit=u, file='io_open_first_file.dat', status='replace', form='formatted', action='readwrite')")])

    c.add_valid("12.5.6.1", "S12.5.6.1-005", "connected_existing_open_permitted",
        ["open-connected-existing-file-permitted"], """
        integer :: u, ios
        open(newunit=u, file='io_open_connected_existing.dat', status='replace', form='formatted', action='readwrite')
        open(unit=u, blank='null', iostat=ios)
        call check_int('connected-existing-open-iostat', ios, 0)
        close(u, status='delete')
    """, 1,
        "12.5.6.1 p5 permits OPEN for a unit connected to an existing file; IOSTAT zero observes success only.",
        [("connected-open-removed", "        open(unit=u, blank='null', iostat=ios)",
          "        ios = -91")])

    c.add_valid("12.5.6.1", "S12.5.6.1-006", "omitted_file_same_file",
        ["connected-open-omitted-file-same-file"], """
        integer :: u, other, ios, value
        character(len=28) :: name
        open(newunit=other, file='io_open_omitted_other.dat', status='replace', form='formatted', action='readwrite')
        write(other,'(i0)') 777
        close(other)
        open(newunit=u, file='io_open_omitted_same.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 555
        open(unit=u, status='old', iostat=ios)
        call check_int('omitted-file-open-status', ios, 0)
        name = '############################'
        inquire(unit=u, name=name)
        call check_char('omitted-file-name-same', name, 'io_open_omitted_same.dat    ')
        rewind u
        read(u,*,iostat=ios) value
        call check_int('omitted-file-read-status', ios, 0)
        call check_int('omitted-file-read-value', value, 555)
        close(u, status='delete')
        open(newunit=other, file='io_open_omitted_other.dat', status='old', form='formatted')
        close(other, status='delete')
    """, 4,
        "12.5.6.1 p5 says omitting FILE= on a connected existing unit keeps the same file; INQUIRE name and "
        "exact read-back identify that file.",
        [("omitted-file-replaced-by-other", "        open(unit=u, status='old', iostat=ios)",
          "        open(unit=u, file='io_open_omitted_other.dat', status='old', iostat=ios)")])

    c.add_valid("12.5.6.1", "S12.5.6.1-007", "same_file_no_new_connection",
        ["same-file-open-no-new-connection"], """
        integer :: u, other, ios, value
        open(newunit=other, file='io_open_no_new_other.dat', status='replace', form='formatted', action='readwrite')
        write(other,'(i0)') 888
        close(other)
        open(newunit=u, file='io_open_no_new_same.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 444
        open(unit=u, file='io_open_no_new_same.dat', status='old', iostat=ios)
        call check_int('same-file-open-status', ios, 0)
        rewind u
        read(u,*,iostat=ios) value
        call check_int('same-file-read-status', ios, 0)
        call check_int('same-file-read-original-data', value, 444)
        close(u, status='delete')
        open(newunit=other, file='io_open_no_new_other.dat', status='old', form='formatted')
        close(other, status='delete')
    """, 3,
        "12.5.6.1 p6 says same-file OPEN establishes no new connection; read-back remains from the original file.",
        [("same-file-changed-to-other-file", "        open(unit=u, file='io_open_no_new_same.dat', status='old', iostat=ios)",
          "        open(unit=u, file='io_open_no_new_other.dat', status='old', iostat=ios)")])

    c.add_valid("12.5.6.1", "S12.5.6.1-008", "same_file_changeable_mode",
        ["same-file-open-changeable-modes-take-effect"], """
        integer :: u, ios, value
        character(len=4) :: blank_mode
        open(newunit=u, file='io_open_mode_same.dat', status='replace', form='formatted', &
             action='readwrite', blank='null')
        write(u,'(a)') '1 2'
        rewind u
        open(unit=u, file='io_open_mode_same.dat', status='old', blank='zero', iostat=ios)
        call check_int('same-file-mode-open-status', ios, 0)
        blank_mode = '####'
        inquire(unit=u, blank=blank_mode)
        call check_char('same-file-blank-zero-mode', blank_mode, 'ZERO')
        read(u,'(i3)',iostat=ios) value
        call check_int('same-file-mode-read-status', ios, 0)
        call check_int('same-file-blank-zero-value', value, 102)
        close(u, status='delete')
    """, 4,
        "12.5.6.1 p6 applies changeable modes in a same-file OPEN; BLANK='ZERO' changes the exact read to 102.",
        [("same-file-mode-keeps-null", "        open(unit=u, file='io_open_mode_same.dat', status='old', blank='zero', iostat=ios)",
          "        open(unit=u, file='io_open_mode_same.dat', status='old', blank='null', iostat=ios)")])

    c.add_valid("12.5.6.1", "S12.5.6.1-009", "same_file_position_unaffected",
        ["same-file-open-position-unaffected"], """
        integer :: u, other, ios, first, second
        open(newunit=other, file='io_open_position_other.dat', status='replace', form='formatted', action='readwrite')
        write(other,'(i0)') 333
        close(other)
        open(newunit=u, file='io_open_position_same.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 111
        write(u,'(i0)') 222
        rewind u
        read(u,*,iostat=ios) first
        call check_int('position-first-status', ios, 0)
        call check_int('position-first-value', first, 111)
        open(unit=u, file='io_open_position_same.dat', status='old', iostat=ios)
        call check_int('position-open-status', ios, 0)
        read(u,*,iostat=ios) second
        call check_int('position-second-status', ios, 0)
        call check_int('position-second-value', second, 222)
        close(u, status='delete')
        open(newunit=other, file='io_open_position_other.dat', status='old', form='formatted')
        close(other, status='delete')
    """, 5,
        "12.5.6.1 p6 leaves current file position unaffected by same-file OPEN; after reading record one, "
        "the next read still obtains record two.",
        [("same-file-position-open-other", "        open(unit=u, file='io_open_position_same.dat', status='old', iostat=ios)",
          "        open(unit=u, file='io_open_position_other.dat', status='old', iostat=ios)")])

    c.add_valid("12.5.6.1", "S12.5.6.1-014", "same_file_status_old_allowed",
        ["same-file-open-status-old-always-allowed"], """
        integer :: u, ios
        open(newunit=u, file='io_open_status_old.dat', status='replace', form='formatted', action='readwrite')
        open(unit=u, file='io_open_status_old.dat', status='old', iostat=ios)
        call check_int('same-file-status-old-iostat', ios, 0)
        close(u, status='delete')
    """, 1,
        "12.5.6.1 p7 always allows STATUS='OLD' for the same connected file; IOSTAT zero observes success.",
        [("same-file-status-old-removed", "        open(unit=u, file='io_open_status_old.dat', status='old', iostat=ios)",
          "        ios = -91")])

    c.add_valid("12.5.6.2", "R1204", "open_parenthesized_control",
        ["open-parenthesized-connect-spec-list"], """
        integer :: u, ios
        logical :: opened
        open(newunit=u, status='scratch', iostat=ios)
        call check_int('r1204-open-iostat', ios, 0)
        opened = .false.
        inquire(unit=u, opened=opened)
        call check_true('r1204-opened', opened)
        close(u, status='delete')
    """, 2,
        "R1204 defines OPEN(connect-spec-list); a parenthesized NEWUNIT/STATUS list opens a scratch unit.",
        [("remove-open-statement", "        open(newunit=u, status='scratch', iostat=ios)",
          "        ios = -91")])

    CONNECT_OPEN = ("        open(unit=u, file='io_open_connect_modes.dat', status='replace', access='sequential', &\n"
                    "             form='formatted', action='readwrite', blank='zero', decimal='comma', delim='quote', &\n"
                    "             encoding='default', pad='no', round='up', sign='plus', iostat=ios)")

    c.add_valid("12.5.6.2", "R1205", "connect_spec_modes",
        ["connect-spec-unit", "connect-spec-access", "connect-spec-action", "connect-spec-blank",
         "connect-spec-decimal", "connect-spec-delim", "connect-spec-encoding", "connect-spec-file",
         "connect-spec-form", "connect-spec-iostat", "connect-spec-pad", "connect-spec-round",
         "connect-spec-sign"], """
        integer :: u, ios
        logical :: opened
        character(len=28) :: name
        character(len=12) :: access, action, blank, decimal, delim, encoding, form, pad, round_mode, sign_mode
        u = 71
        ios = -91
        open(unit=u, file='io_open_connect_modes.dat', status='replace', access='sequential', &
             form='formatted', action='readwrite', blank='zero', decimal='comma', delim='quote', &
             encoding='default', pad='no', round='up', sign='plus', iostat=ios)
        call check_int('connect-spec-iostat-zero', ios, 0)
        opened = .false.
        name = '############################'
        access = '############'
        action = '############'
        blank = '############'
        decimal = '############'
        delim = '############'
        encoding = '############'
        form = '############'
        pad = '############'
        round_mode = '############'
        sign_mode = '############'
        inquire(unit=u, opened=opened, name=name, access=access, action=action, blank=blank, &
                decimal=decimal, delim=delim, encoding=encoding, form=form, pad=pad, &
                round=round_mode, sign=sign_mode)
        call check_true('connect-spec-unit-opened', opened)
        call check_char('connect-spec-file-name', name, 'io_open_connect_modes.dat   ')
        call check_char('connect-spec-access', access, 'SEQUENTIAL  ')
        call check_char('connect-spec-action', action, 'READWRITE   ')
        call check_char('connect-spec-blank', blank, 'ZERO        ')
        call check_char('connect-spec-decimal', decimal, 'COMMA       ')
        call check_char('connect-spec-delim', delim, 'QUOTE       ')
        call check_char('connect-spec-encoding', encoding, 'DEFAULT     ')
        call check_char('connect-spec-form', form, 'FORMATTED   ')
        call check_char('connect-spec-pad', pad, 'NO          ')
        call check_char('connect-spec-round', round_mode, 'UP          ')
        call check_char('connect-spec-sign', sign_mode, 'PLUS        ')
        close(u, status='delete')
    """, 13,
        "R1205 lists OPEN connect-spec alternatives; UNIT, FILE, IOSTAT and listed character mode specifiers "
        "are observed by successful OPEN and INQUIRE tokens fixed by those specifiers.",
        [
            ("unit-spec-other-unit", CONNECT_OPEN,
             CONNECT_OPEN.replace("unit=u", "unit=72", 1)),
            ("file-spec-other-name", CONNECT_OPEN,
             CONNECT_OPEN.replace("io_open_connect_modes.dat", "io_open_connect_other.dat", 1)),
            ("access-spec-stream", CONNECT_OPEN,
             CONNECT_OPEN.replace("access='sequential'", "access='stream'", 1)),
            ("action-spec-read", CONNECT_OPEN,
             CONNECT_OPEN.replace("action='readwrite'", "action='read'", 1)),
            ("blank-spec-null", CONNECT_OPEN,
             CONNECT_OPEN.replace("blank='zero'", "blank='null'", 1)),
            ("decimal-spec-point", CONNECT_OPEN,
             CONNECT_OPEN.replace("decimal='comma'", "decimal='point'", 1)),
            ("delim-spec-apostrophe", CONNECT_OPEN,
             CONNECT_OPEN.replace("delim='quote'", "delim='apostrophe'", 1)),
            ("encoding-spec-utf8", CONNECT_OPEN,
             CONNECT_OPEN.replace("encoding='default'", "encoding='utf-8'", 1)),
            ("form-spec-unformatted", CONNECT_OPEN,
             "        open(unit=u, file='io_open_connect_modes.dat', status='replace', access='sequential', &\n"
             "             form='unformatted', action='readwrite', iostat=ios)"),
            ("iostat-spec-omitted", CONNECT_OPEN,
             CONNECT_OPEN.replace(", iostat=ios", "", 1)),
            ("pad-spec-yes", CONNECT_OPEN,
             CONNECT_OPEN.replace("pad='no'", "pad='yes'", 1)),
            ("round-spec-down", CONNECT_OPEN,
             CONNECT_OPEN.replace("round='up'", "round='down'", 1)),
            ("sign-spec-suppress", CONNECT_OPEN,
             CONNECT_OPEN.replace("sign='plus'", "sign='suppress'", 1)),
        ])

    c.add_valid("12.5.6.2", "R1205", "connect_spec_newunit",
        ["connect-spec-newunit"], """
        integer :: u, other
        u = 0
        other = 0
        open(newunit=u, status='scratch')
        call check_true('newunit-assigned-negative', u < 0)
        call check_true('newunit-not-other-variable', other == 0)
        close(u, status='delete')
    """, 2,
        "R1205 includes NEWUNIT=scalar-int-variable; OPEN assigns a valid negative unit to that variable.",
        [("newunit-spec-other-variable", "        open(newunit=u, status='scratch')",
          "        open(newunit=other, status='scratch')")])

    c.add_valid("12.5.6.2", "R1205", "connect_spec_recl_direct",
        ["connect-spec-recl"], """
        integer :: u, recl_value
        character(len=10) :: access
        open(newunit=u, file='io_open_recl_direct.dat', status='replace', access='direct', &
             form='formatted', recl=8)
        recl_value = -1
        access = '##########'
        inquire(unit=u, recl=recl_value, access=access)
        call check_char('recl-direct-access', access, 'DIRECT    ')
        call check_int('recl-direct-value', recl_value, 8)
        close(u, status='delete')
    """, 2,
        "R1205 includes RECL=scalar-int-expr; direct formatted OPEN reports the specified exact RECL value.",
        [("recl-spec-changed", "             form='formatted', recl=8)", "             form='formatted', recl=9)")])

    c.add_valid("12.5.6.2", "R1205", "connect_spec_position_append",
        ["connect-spec-position"], """
        integer :: u, ios, a, b, cval
        open(newunit=u, file='io_open_position_append.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 1
        write(u,'(i0)') 2
        close(u)
        open(newunit=u, file='io_open_position_append.dat', status='old', position='append', &
             form='formatted', action='readwrite')
        write(u,'(i0)') 3
        rewind u
        read(u,*,iostat=ios) a
        call check_int('position-append-first-status', ios, 0)
        call check_int('position-append-first', a, 1)
        read(u,*,iostat=ios) b
        call check_int('position-append-second-status', ios, 0)
        call check_int('position-append-second', b, 2)
        read(u,*,iostat=ios) cval
        call check_int('position-append-third-status', ios, 0)
        call check_int('position-append-third', cval, 3)
        close(u, status='delete')
    """, 6,
        "R1205 includes POSITION=; POSITION='APPEND' makes the subsequent write follow the two existing records.",
        [("position-spec-rewind", "        open(newunit=u, file='io_open_position_append.dat', status='old', position='append', &\n             form='formatted', action='readwrite')",
          "        open(newunit=u, file='io_open_position_append.dat', status='old', position='rewind', &\n             form='formatted', action='readwrite')")])

    c.add_valid("12.5.6.2", "R1205", "connect_spec_status_replace",
        ["connect-spec-status"], """
        integer :: u, ios
        open(newunit=u, file='io_open_status_replace.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 999
        close(u)
        open(newunit=u, file='io_open_status_replace.dat', status='replace', form='formatted', action='readwrite')
        read(u,*,iostat=ios)
        call check_nonzero('status-replace-created-empty-file', ios)
        close(u, status='delete')
    """, 1,
        "R1205 includes STATUS=; STATUS='REPLACE' deletes any existing file and creates an empty replacement, "
        "so an immediate read has nonzero IOSTAT.",
        [("status-spec-old", "        open(newunit=u, file='io_open_status_replace.dat', status='replace', form='formatted', action='readwrite')\n        read(u,*,iostat=ios)",
          "        open(newunit=u, file='io_open_status_replace.dat', status='old', form='formatted', action='readwrite')\n        read(u,*,iostat=ios)")])

    c.add_valid("12.5.6.2", "R1205", "connect_spec_err_branch",
        ["connect-spec-err"], """
        integer :: u, marker
        marker = -1
        open(newunit=u, file='io_open_missing_for_err.dat', status='old', err=20)
        marker = 0
        goto 30
20      marker = 20
30      call check_int('err-spec-branch-target', marker, 20)
    """, 1,
        "R1205 includes ERR=label; an OLD nonexistent file error transfers control to the branch target.",
        [("err-spec-existing-file-no-branch", "        open(newunit=u, file='io_open_missing_for_err.dat', status='old', err=20)",
          "        open(newunit=u, file='io_open_err_existing.dat', status='replace')\n        close(u)\n        open(newunit=u, file='io_open_err_existing.dat', status='old', err=20)")])

    c.add_valid("12.5.6.2", "R1206", "file_name_expr_variable",
        ["file-name-expr-scalar-default-character"], """
        integer :: u, ios, value
        character(len=29) :: filename
        character(len=29) :: name
        filename = 'io_open_file_expr_name.dat   '
        open(newunit=u, file=filename, status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 123
        name = '#############################'
        inquire(unit=u, name=name)
        call check_char('file-name-expr-inquired-name', name, 'io_open_file_expr_name.dat   ')
        rewind u
        read(u,*,iostat=ios) value
        call check_int('file-name-expr-read-status', ios, 0)
        call check_int('file-name-expr-read-value', value, 123)
        close(u, status='delete')
    """, 3,
        "R1206 defines FILE= as a scalar default character expression; a padded character variable names the file.",
        [("file-name-expr-other-variable", "        filename = 'io_open_file_expr_name.dat   '",
          "        filename = 'io_open_file_expr_other.dat '")])

    c.add_valid("12.5.6.2", "S12.5.6.2-001", "limited_values_case_trailing",
        ["limited-character-values", "trailing-blanks-ignored", "case-insensitive-values"], """
        integer :: u
        character(len=8) :: blank_mode, decimal_mode, delim_mode
        open(newunit=u, file='io_open_limited_values.dat', status='replace', form='formatted', &
             blank='zErO   ', decimal='cOmMa  ', delim='qUoTe  ')
        blank_mode = '########'
        decimal_mode = '########'
        delim_mode = '########'
        inquire(unit=u, blank=blank_mode, decimal=decimal_mode, delim=delim_mode)
        call check_char('limited-blank-zero', blank_mode, 'ZERO    ')
        call check_char('trailing-decimal-comma', decimal_mode, 'COMMA   ')
        call check_char('case-delim-quote', delim_mode, 'QUOTE   ')
        close(u, status='delete')
    """, 3,
        "12.5.6.2 p1 makes limited character values case-insensitive and ignores trailing blanks; INQUIRE "
        "reports the fixed BLANK, DECIMAL, and DELIM tokens.",
        [("limited-value-blank-null", "             blank='zErO   ', decimal='cOmMa  ', delim='qUoTe  ')",
          "             blank='nUlL   ', decimal='cOmMa  ', delim='qUoTe  ')") ,
         ("trailing-value-decimal-point", "             blank='zErO   ', decimal='cOmMa  ', delim='qUoTe  ')",
          "             blank='zErO   ', decimal='pOiNt  ', delim='qUoTe  ')") ,
         ("case-value-delim-apostrophe", "             blank='zErO   ', decimal='cOmMa  ', delim='qUoTe  ')",
          "             blank='zErO   ', decimal='cOmMa  ', delim='aPoStRoPhE')")])

    c.add_valid("12.5.6.2", "S12.5.6.2-002", "open_error_specifiers_defer",
        ["open-error-specifiers-defer-to-12-11"], """
        integer :: u, ios, marker
        marker = -1
        ios = 0
        open(newunit=u, file='io_open_missing_error_defer.dat', status='old', iostat=ios, err=40)
        marker = 0
        goto 50
40      marker = 40
50      call check_nonzero('open-error-iostat-nonzero', ios)
        call check_int('open-error-err-branch', marker, 40)
    """, 2,
        "12.5.6.2 p2 defers IOSTAT and ERR to 12.11; for OLD on a nonexistent file the portable oracle is "
        "only nonzero IOSTAT and control transfer to the branch label.",
        [("error-specifiers-existing-file", "        open(newunit=u, file='io_open_missing_error_defer.dat', status='old', iostat=ios, err=40)",
          "        open(newunit=u, file='io_open_error_existing.dat', status='replace', iostat=ios, err=40)")])

    c.add_invalid("12.5.6.2", "R1204", "missing_parenthesis",
        ["open-missing-parenthesis-rejected"], """
        program p
        integer :: u
        open unit=10,status='scratch'
        end program p
    """,
        "R1204 requires OPEN followed by a parenthesized connect-spec-list; the control adds only the parentheses.",
        3, ["unclassifiable", "unexpected", "syntax"],
        ident("R1204", "missing_parenthesis_control", "valid"))

    c.add_control("12.5.6.2", "R1204", "missing_parenthesis_control",
        ["open-missing-parenthesis-rejected"], """
        program p
        integer :: u
        open(unit=10,status='scratch')
        end program p
    """,
        "One-property control for R1204 missing-parenthesis: the OPEN statement differs only by the required parentheses.",
        ident("R1204", "missing_parenthesis", "invalid"))

    c.add_invalid("12.5.6.2", "R1206", "noncharacter_file_name",
        ["noncharacter-file-name-rejected"], """
        program p
        integer :: u
        open(newunit=u, file=123, status='replace')
        close(u, status='delete')
        end program p
    """,
        "R1206 requires FILE= to be a scalar default character expression; the control changes only FILE= to a string.",
        3, ["character", "String"],
        ident("R1206", "noncharacter_file_name_control", "valid"))

    c.add_control("12.5.6.2", "R1206", "noncharacter_file_name_control",
        ["noncharacter-file-name-rejected"], """
        program p
        integer :: u
        open(newunit=u, file='io_open_r1206_control.dat', status='replace')
        close(u, status='delete')
        end program p
    """,
        "One-property control for R1206 noncharacter FILE=: the FILE= value is a default character expression.",
        ident("R1206", "noncharacter_file_name", "invalid"))

    c.add_invalid("12.5.6.2", "R1207", "iomsg_nonvariable",
        ["iomsg-nonvariable-rejected"], """
        program p
        integer :: u, ios
        open(newunit=u, status='scratch', iostat=ios, iomsg='bad')
        end program p
    """,
        "R1207 requires IOMSG= to be a scalar default character variable; the control uses a character variable.",
        3, ["Non-variable", "variable"],
        ident("R1207", "iomsg_nonvariable_control", "valid"))

    c.add_control("12.5.6.2", "R1207", "iomsg_nonvariable_control",
        ["iomsg-nonvariable-rejected"], """
        program p
        integer :: u, ios
        character(len=20) :: msg
        msg = 'sentinel'
        open(newunit=u, status='scratch', iostat=ios, iomsg=msg)
        close(u, status='delete')
        end program p
    """,
        "One-property control for R1207 IOMSG=: the specifier designates a scalar default character variable.",
        ident("R1207", "iomsg_nonvariable", "invalid"))

    c.add_invalid("12.5.6.2", "C1203", "duplicate_unit_specifier",
        ["duplicate-open-specifier-rejected"], """
        program p
        integer :: u
        u = 10
        open(unit=u, unit=11, status='scratch')
        end program p
    """,
        "C1203 prohibits duplicate specifiers in one connect-spec-list; the control removes the second UNIT=.",
        4, ["Duplicate", "specified"],
        ident("C1203", "duplicate_unit_specifier_control", "valid"))

    c.add_control("12.5.6.2", "C1203", "duplicate_unit_specifier_control",
        ["duplicate-open-specifier-rejected"], """
        program p
        integer :: u
        u = 10
        open(unit=u, status='scratch')
        end program p
    """,
        "One-property control for C1203 duplicate specifier: the second UNIT= specifier is absent.",
        ident("C1203", "duplicate_unit_specifier", "invalid"))

    c.add_invalid("12.5.6.2", "C1204", "unit_required_without_newunit",
        ["unit-required-without-newunit"], """
        program p
        open(status='scratch')
        end program p
    """,
        "C1204 requires a file-unit-number when NEWUNIT= is absent; the control adds UNIT=10.",
        2, ["UNIT", "newunit", "specified"],
        ident("C1204", "unit_required_without_newunit_control", "valid"))

    c.add_control("12.5.6.2", "C1204", "unit_required_without_newunit_control",
        ["unit-required-without-newunit"], """
        program p
        open(unit=10, status='scratch')
        end program p
    """,
        "One-property control for C1204 missing file-unit-number: UNIT=10 is supplied.",
        ident("C1204", "unit_required_without_newunit", "invalid"))

    c.add_invalid("12.5.6.2", "C1204", "bare_unit_not_first",
        ["bare-unit-first"], """
        program p
        open(status='scratch', 10)
        end program p
    """,
        "C1204 requires a bare file-unit-number without UNIT= to be first in the connect-spec-list; the control moves it first.",
        2, ["Syntax", "OPEN", "unexpected"],
        ident("C1204", "bare_unit_first_control", "valid"))

    c.add_control("12.5.6.2", "C1204", "bare_unit_first_control",
        ["bare-unit-first"], """
        program p
        open(10, status='scratch')
        end program p
    """,
        "One-property control for C1204 bare-unit placement: the bare file-unit-number is first.",
        ident("C1204", "bare_unit_not_first", "invalid"))

    c.add_invalid("12.5.6.2", "C1205", "newunit_excludes_unit",
        ["newunit-excludes-file-unit-number"], """
        program p
        integer :: u
        open(10, newunit=u, status='scratch')
        end program p
    """,
        "C1205 prohibits a file-unit-number when NEWUNIT= appears; the control removes the bare unit.",
        3, ["NEWUNIT", "Duplicate", "UNIT"],
        ident("C1205", "newunit_excludes_unit_control", "valid"))

    c.add_control("12.5.6.2", "C1205", "newunit_excludes_unit_control",
        ["newunit-excludes-file-unit-number"], """
        program p
        integer :: u
        open(newunit=u, status='scratch')
        end program p
    """,
        "One-property control for C1205 NEWUNIT/file-unit-number exclusion: the bare unit is absent.",
        ident("C1205", "newunit_excludes_unit", "invalid"))

    c.add_invalid("12.5.6.2", "C1206", "err_label_undefined",
        ["err-label-branch-target-same-scope"], """
        program p
        integer :: u
        open(newunit=u, status='scratch', err=99)
        close(u, status='delete')
        end program p
    """,
        "C1206 requires ERR= to name a branch target in the same inclusive scope; the control defines label 99.",
        1, ["label 99", "not defined", "never defined"],
        ident("C1206", "err_label_undefined_control", "valid"), diagnostic_end_line=3)

    c.add_control("12.5.6.2", "C1206", "err_label_undefined_control",
        ["err-label-branch-target-same-scope"], """
        program p
        integer :: u
        open(newunit=u, status='scratch', err=99)
        close(u, status='delete')
99      continue
        end program p
    """,
        "One-property control for C1206 ERR= label: label 99 is a branch target in the same inclusive scope.",
        ident("C1206", "err_label_undefined", "invalid"))

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
    by_rule = {}
    for spec in specs.values():
        if spec["section"] == section:
            by_rule.setdefault(spec["rule"], []).append(spec)
    for requirement in result["requirements"]:
        selected = by_rule.get(requirement["id"], [])
        covered = {facet for spec in selected for facet in spec["facets"]}
        for facet in covered:
            if facet not in requirement["facets"]:
                raise ValueError(f"unknown facet {facet} for {requirement['id']}")
            requirement["pending"].pop(facet, None)
        expected_pending = set(requirement["facets"]) - covered
        for facet in sorted(expected_pending):
            reason = RESTORED_PENDING.get((requirement["id"], facet))
            if reason is not None:
                requirement["pending"][facet] = reason
            elif facet not in requirement["pending"]:
                raise ValueError(f"missing pending reason for {requirement['id']}:{facet}")
        if set(requirement["pending"]) != expected_pending:
            raise ValueError(f"pending mismatch for {requirement['id']}: {set(requirement['pending'])} != {expected_pending}")
        if selected:
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered))
            diag_count = sum(1 for spec in selected if spec["kind"] == "invalid")
            run_count = len(selected) - diag_count
            text = ("I/O OPEN fixture implementation: "
                    f"{run_count} valid run-phase program(s) and {diag_count} diagnostic program(s) cover {labels}. "
                    "Runtime oracles use controlled stdout/stderr, per-run relative files, INQUIRE properties, "
                    "exact integer/character/logical values, and only zero/nonzero IOSTAT distinctions. "
                    "Diagnostics are line-anchored for numbered syntax or constraints and have one-property controls. "
                    "No IOMSG text, processor-dependent unit number, physical filename, or specific nonzero status "
                    "is asserted.")
            requirement["oracle"] = owned_paragraph(requirement["oracle"],
                                                     "I/O OPEN fixture implementation:", text)
            prefix = "Source accounting only. "
            if requirement["oracle_limitation"].startswith(prefix):
                requirement["oracle_limitation"] = ("Runtime fixture coverage is finite and does not imply "
                                                     "fixture review. "
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
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - OPEN fixtures\n\n"
            f"The canonical catalogue is `{CATALOGUES[section]}`. "
            "This author packet adds finite runtime and diagnostic fixtures without fixture approval.\n\n"
            "Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256 "
            "`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.\n\n"
            f"**Catalogue source review: {registry.catalogue_review_state(section)}.** "
            f"This topic represents {represented} facets in {len(selected)} program(s); "
            f"{total - pending} of {total} facets are represented and {pending} remain pending.\n\n"
            f"<!-- BEGIN GENERATED {section} -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"])
    text += f"\n<!-- END GENERATED {section} -->\n\n"
    text += "## I/O OPEN fixture derivations\n\n"
    for spec in selected:
        text += f"### `{spec['variant']}` / `{spec['rule']}`\n\n"
        text += "**Facets:** " + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n"
        text += spec["derivation"] + "\n\n"
        if spec["kind"] == "valid":
            feature = [m["id"] for m in spec["mutants"] if m["category"] == "feature"]
            text += "Feature mutations: " + ", ".join(f"`{m}`" for m in feature) + ".\n\n"
        else:
            text += f"Conforming control: `{spec['control']}`.\n\n"
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
        raise SystemExit("stale io_open_12_5_6 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def expected_stream(spec, key):
    value = spec.get(key)
    return "" if value is None else value


def run_mutations(compiler, std, keep=False):
    _files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_open_12_5_6" / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    try:
        for name, spec in specs.items():
            if spec["kind"] != "valid":
                continue
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
                if (ran.returncode == 0 and ran.stdout == expected_stream(spec, "stdout")
                        and ran.stderr == expected_stream(spec, "stderr")):
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
