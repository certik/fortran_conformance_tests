#!/usr/bin/env python3
"""Generate Clause 12.7-12.9 WAIT, positioning, and FLUSH fixtures."""
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
TOPIC = "io_wait_position_flush_12_7_12_9"
CATALOGUES = {
    "12.7.1": "doc/catalogues/waiting_for_pending_data_transfer_12_7_1.json",
    "12.7.2": "doc/catalogues/wait_statement_12_7_2.json",
    "12.8.1": "doc/catalogues/file_positioning_statement_syntax_12_8_1.json",
    "12.8.2": "doc/catalogues/backspace_statement_12_8_2.json",
    "12.8.3": "doc/catalogues/endfile_statement_12_8_3.json",
    "12.8.4": "doc/catalogues/rewind_statement_12_8_4.json",
    "12.9": "doc/catalogues/flush_statement_12_9.json",
}
VIEWS = {
    "12.7.1": "doc/fortran_2023_12_7_1.md",
    "12.7.2": "doc/fortran_2023_12_7_2.md",
    "12.8.1": "doc/fortran_2023_12_8_1.md",
    "12.8.2": "doc/fortran_2023_12_8_2.md",
    "12.8.3": "doc/fortran_2023_12_8_3.md",
    "12.8.4": "doc/fortran_2023_12_8_4.md",
    "12.9": "doc/fortran_2023_12_9.md",
}
VIEW_TITLES = {
    "12.7.1": "Waiting for pending data transfer operations",
    "12.7.2": "WAIT statement",
    "12.8.1": "File positioning statement syntax",
    "12.8.2": "BACKSPACE statement",
    "12.8.3": "ENDFILE statement",
    "12.8.4": "REWIND statement",
    "12.9": "FLUSH statement",
}
RESTORED_PENDING = {
    ("S12.8.3-005", "stream-output-after-endfile-permitted"):
        "Left pending: ordinary stream output at the same position is also permitted, so this permission did not have a conforming feature mutation that made the read-back assertion depend specifically on ENDFILE.",
    ("S12.8.3-003", "sequential-endfile-reposition-before-data-transfer"):
        "Left pending: omitting the required repositioning before a data transfer is nonconforming and the unnumbered restriction has no required diagnostic.",
    ("S12.8.3-003", "sequential-endfile-reposition-before-another-endfile"):
        "Left pending: omitting the required repositioning before another ENDFILE is nonconforming and the unnumbered restriction has no required diagnostic.",
    ("R1229", "flush-unit-specifier-form"):
        "Left pending: FLUSH UNIT= syntax has no portable single-image feature mutation independent of IOSTAT or asynchronous-wait semantics; external availability is processor dependent.",
    ("S12.7.1-007", "wait-waits-for-actual-completion"):
        "Left pending: processors may perform asynchronous I/O synchronously, and INQUIRE(PENDING=) may itself perform a wait, so no conforming single-image mutant removes every wait operation and still portably distinguishes this WAIT effect.",
    ("S12.7.1-007", "successful-input-wait-defines-storage-values"):
        "Left pending: the transferred value after WAIT is required, but a record-value mutant tests data transfer rather than WAIT semantics and deleting WAIT is masked by permitted synchronous I/O or INQUIRE(PENDING=) waiting.",
    ("S12.7.2-003", "wait-omitted-id-waits-all-unit-transfers"):
        "Left pending: INQUIRE(PENDING=) can perform the wait and processors may complete asynchronous transfers synchronously, so omitted-ID WAIT-all semantics lack a load-bearing portable single-image mutant.",
    ("S12.8.1-002", "positioning-statement-waits-all-pending-for-unit"):
        "Left pending: record values after a positioning statement do not distinguish required wait semantics on a synchronous processor, and INQUIRE(PENDING=) can itself wait.",
    ("S12.9-006", "flush-waits-all-pending-for-unit"):
        "Left pending: replacing FLUSH with another positioning statement still waits, while deleting FLUSH is masked by permitted synchronous I/O or INQUIRE(PENDING=) performing a wait."
}

CHECKS = """
module io_wait_position_flush_checks
use iso_fortran_env, only: iostat_end, iostat_eor
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, check_false, finish_checks, iostat_end, iostat_eor
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
end module io_wait_position_flush_checks
""".lstrip()

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
            continue
        match = LOGICAL_DECL.match(line)
        if match:
            for item in match.group("names").split(","):
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
    for next_line in lines[index + 1:index + 30]:
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
        target = match.group("target")
        if target not in types:
            raise ValueError(f"read target {target} has no known declaration")
        category, length = types[target]
        expected = find_read_expected(lines, index, target, category)
        read_index += 1
        indent = match.group("indent")
        for previous in range(len(output) - 1, max(-1, len(output) - 5), -1):
            if re.match(r"^\s*" + re.escape(target) + r"\s*=", output[previous], re.I):
                output.pop(previous)
                break
        label = f"pre-read-{read_index}-{target}"
        if category == "integer":
            sentinel = f"-{7000 + read_index}"
            poison = f"-{8000 + read_index}"
            default = "0"
            expected_init = expected.strip()
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_int('{label}', {target}, {sentinel})")
        elif category == "character":
            mark = CHAR_SENTINELS[(read_index - 1) % len(CHAR_SENTINELS)]
            sentinel = "'" + (mark * length) + "'"
            poison = "'" + ("!" * length) + "'"
            default = "'" + (" " * length) + "'"
            expected_init = expected
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_char('{label}', {target}, {sentinel})")
        else:
            sentinel = ".true."
            poison = ".false."
            default = ".false."
            expected_init = expected.strip()
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_true('{label}', {target})")
        expected_probe = expected_init
        if expected_probe == sentinel:
            if category == "character":
                alt = next(ch for ch in CHAR_SENTINELS if "'" + (ch * length) + "'" != sentinel)
                expected_probe = "'" + (alt * length) + "'"
            elif category == "integer":
                expected_probe = str(int(sentinel) - 97)
            else:
                expected_probe = ".false." if sentinel == ".true." else ".true."
        probes.extend([
            (f"{label}-remove-sentinel-init", sentinel_line,
             f"{indent}! sentinel initializer removed for probe", "sentinel"),
            (f"{label}-expected-sentinel-init", sentinel_line,
             f"{indent}{target} = {expected_probe}", "sentinel"),
            (f"{label}-default-sentinel-init", sentinel_line,
             f"{indent}{target} = {default}", "sentinel"),
        ])
        output.append(line)
    return "\n".join(output) + "\n", probes


def source(body_text, count):
    main, probes = add_pre_read_guards(body(body_text))
    total = count + sum(1 for _, _, _, category in probes if category == "sentinel") // 3
    src = CHECKS + "program p\nuse io_wait_position_flush_checks\nimplicit none\n" + main
    src += f"call finish_checks({total})\nend program p\n"
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

    def add_valid(self, section, rule, variant, facets, body_text, checks, derivation, mutants):
        name = ident(rule, variant, "valid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src, total_checks, sentinel_probes = source(body_text, checks)
        evidence = "positive-control" if rule in {"S12.7.2-002", "S12.8.3-003"} else "effect"
        manifest = {
            "schema_version": 1,
            "id": name,
            "rule": rule,
            "facets": list(facets),
            "standard": "f2023",
            "evidence": evidence,
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
            "kind": "valid",
            "evidence": evidence,
            "checks": total_checks,
            "derivation": derivation,
            "mutants": [{"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in normalized],
        }

    def add_invalid(self, section, rule, variant, facets, source_text, derivation, diagnostic_line,
                    contains_any, control):
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
                        "unexpected end of file", "unexpected eof", "missing end", "out of memory"
                    ],
                },
            },
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
            "kind": "invalid",
            "checks": 0,
            "derivation": derivation,
            "diagnostic_line": diagnostic_line,
            "contains_any": contains_any,
            "control": control,
            "mutants": [],
        }


def build_corpus(root=ROOT):
    c = Corpus(root)

    c.add_valid("12.8.4", "S12.8.4-001", "rewind_initial_point",
        ["rewind-positions-at-initial-point"], """
        integer :: u, ios, value
        open(newunit=u, file='iwpf_rewind.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 801
        write(u,'(i0)') 802
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('rewind-first-read-status', ios, 0)
        call check_int('rewind-first-read-value', value, 801)
        value = -2
        read(u,*,iostat=ios) value
        call check_int('second-read-status', ios, 0)
        call check_int('second-read-value', value, 802)
        rewind(unit=u, iostat=ios)
        call check_int('rewind-position-status', ios, 0)
        value = -3
        read(u,*,iostat=ios) value
        call check_int('rewind-reread-status', ios, 0)
        call check_int('rewind-reread-value', value, 801)
        close(u, status='delete')
    """, 7,
        "12.8.4 p1 requires REWIND to position the file at its initial point; after reading two exact records, REWIND makes the next read return the first record again.",
        [("remove-rewind-before-reread", "        rewind(unit=u, iostat=ios)", "        ios = 0"),
         ("initial-record-changed", "        write(u,'(i0)') 801", "        write(u,'(i0)') 811")])

    c.add_valid("12.8.2", "S12.8.2-001", "backspace_current_record",
        ["backspace-before-current-record"], """
        integer :: u, ios
        character(len=2) :: part
        character(len=5) :: whole
        open(newunit=u, file='iwpf_back_current.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'ABCDE'
        rewind u
        part = '??'
        read(u,'(a2)',advance='no',iostat=ios) part
        call check_int('nonadvancing-part-status', ios, 0)
        call check_char('nonadvancing-part-value', part, 'AB')
        backspace u
        whole = '!!!!!'
        read(u,'(a)',iostat=ios) whole
        call check_int('backspace-current-status', ios, 0)
        call check_char('backspace-current-value', whole, 'ABCDE')
        close(u, status='delete')
    """, 4,
        "12.8.2 p1 says BACKSPACE before a current record positions before that current record; after a nonadvancing partial read, BACKSPACE makes a full read return the same record.",
        [("remove-backspace-current", "        backspace u", "        continue"),
         ("backspace-current-record-text", "        write(u,'(a)') 'ABCDE'", "        write(u,'(a)') 'ABXDE'")])

    c.add_valid("12.8.2", "S12.8.2-001", "backspace_preceding_and_initial",
        ["backspace-before-preceding-record", "backspace-at-initial-point-unchanged"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_back_preceding.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        rewind u
        backspace(unit=u, iostat=ios)
        call check_int('initial-backspace-status', ios, 0)
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('initial-backspace-read-status', ios, 0)
        call check_char('initial-backspace-read-value', rec, 'A')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('second-record-read-status', ios, 0)
        call check_char('second-record-read-value', rec, 'B')
        backspace u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('preceding-backspace-status', ios, 0)
        call check_char('preceding-backspace-value', rec, 'B')
        close(u, status='delete')
    """, 7,
        "12.8.2 p1 leaves the initial point unchanged by BACKSPACE and otherwise positions before the preceding record when no current record exists; exact read-back distinguishes A from B.",
        [("remove-initial-backspace", "        backspace(unit=u, iostat=ios)", "        read(u,'(a)',iostat=ios) rec"),
         ("remove-preceding-backspace", "        backspace u", "        continue"),
         ("second-record-changed", "        write(u,'(a)') 'B'", "        write(u,'(a)') 'C'")])

    c.add_valid("12.8.2", "S12.8.2-002", "backspace_implicit_endfile",
        ["backspace-implicit-endfile-before-preceding-record"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_back_implicit.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        backspace u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('implicit-endfile-backspace-status', ios, 0)
        call check_char('implicit-endfile-backspace-value', rec, 'B')
        close(u, status='delete')
    """, 2,
        "12.8.2 p2 fixes the result when BACKSPACE implicitly writes an endfile record; after output records A and B, BACKSPACE positions before B, not before an end marker.",
        [("remove-implicit-backspace", "        backspace u", "        rewind u"),
         ("implicit-record-changed", "        write(u,'(a)') 'B'", "        write(u,'(a)') 'C'")])

    c.add_valid("12.8.3", "S12.8.3-001", "endfile_sequential_record",
        ["sequential-endfile-writes-endfile-record", "sequential-endfile-record-becomes-last"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_endfile_seq.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        endfile u
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('endfile-first-status', ios, 0)
        call check_char('endfile-first-record', rec, 'A')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('endfile-second-status', ios, 0)
        call check_char('endfile-second-record', rec, 'B')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('endfile-status', ios, iostat_end)
        call check_char('endfile-read-preserves-sentinel', rec, '$')
        close(u, status='delete')
        open(newunit=u, file='iwpf_endfile_last.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'D'
        write(u,'(a)') 'E'
        write(u,'(a)') 'F'
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('last-record-prefix-status', ios, 0)
        call check_char('last-record-prefix-value', rec, 'D')
        endfile u
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('last-record-reread-status', ios, 0)
        call check_char('last-record-reread-value', rec, 'D')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('last-record-end-status', ios, iostat_end)
        call check_char('last-record-end-sentinel', rec, '?')
        close(u, status='delete')
    """, 12,
        "12.8.3 p1 writes an endfile record as the next record and makes it last; one scenario observes the endfile after A/B, and one writes ENDFILE before prior trailing records E/F and observes D followed by IOSTAT_END.",
        [("replace-endfile-with-data-record",
          "endfile u\nrewind u\nrec = '!'\nrec = '#'\ncall check_char('pre-read-1-rec', rec, '#')",
          "write(u,'(a)') 'C'\nrewind u\nrec = '!'\nrec = '#'\ncall check_char('pre-read-1-rec', rec, '#')"),
         ("remove-last-record-endfile",
          "endfile u\nrewind u\nrec = '!'\nrec = '&'\ncall check_char('pre-read-5-rec', rec, '&')",
          "rewind u\nrec = '!'\nrec = '&'\ncall check_char('pre-read-5-rec', rec, '&')")])

    c.add_valid("12.8.3", "S12.8.3-001", "endfile_position_after",
        ["sequential-endfile-positions-after-endfile"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_endfile_after.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        endfile u
        backspace u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('post-endfile-backspace-status', ios, iostat_end)
        call check_char('post-endfile-backspace-sentinel', rec, '#')
        close(u, status='delete')
    """, 2,
        "12.8.3 p1 positions after the endfile record; the required BACKSPACE before a following transfer therefore positions before the endfile record, and the next READ reports IOSTAT_END.",
        [("remove-endfile-before-backspace", "        endfile u", "        continue"),
         ("replace-backspace-with-rewind", "        backspace u", "        rewind u")])

    c.add_valid("12.8.3", "S12.8.3-004", "stream_endfile_terminal",
        ["stream-endfile-terminal-point-current-position", "stream-endfile-only-before-current-written",
         "stream-endfile-only-before-current-read"], """
        integer :: u, ios, pos_after_ab, terminal_pos
        character(len=1) :: ch
        open(newunit=u, file='iwpf_stream_endfile.dat', status='replace', access='stream', &
             form='unformatted', action='readwrite')
        write(u) 'A'
        write(u) 'B'
        inquire(unit=u, pos=pos_after_ab)
        write(u) 'C'
        write(u) 'D'
        write(u, pos=pos_after_ab) 'X'
        inquire(unit=u, pos=terminal_pos)
        endfile u
        ch = '#'
        read(u, pos=1, iostat=ios) ch
        call check_int('stream-prefix-read-status', ios, 0)
        call check_char('stream-prefix-read-value', ch, 'A')
        ch = '#'
        read(u, pos=pos_after_ab, iostat=ios) ch
        call check_int('stream-current-minus-one-status', ios, 0)
        call check_char('stream-current-minus-one-value', ch, 'X')
        ch = '#'
        read(u, pos=terminal_pos, iostat=ios) ch
        call check_int('stream-terminal-read-status', ios, iostat_end)
        call check_char('stream-terminal-read-sentinel', ch, '$')
        close(u, status='delete')
    """, 6,
        "12.8.3 p3 sets a stream endfile terminal point to the current POS= position; positions before it read exact bytes A and X, while reading at the terminal point reports IOSTAT_END.",
        [("remove-stream-endfile", "        endfile u", "        continue"),
         ("replace-stream-endfile-with-flush", "        endfile u", "        flush u"),
         ("replace-stream-endfile-with-rewind", "        endfile u", "        rewind u")])

    c.add_valid("12.8.1", "R1224", "backspace_forms",
        ["backspace-unit-number-form", "backspace-position-spec-list-form"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_r1224.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        rewind u
        read(u,'(a)',iostat=ios) rec
        call check_int('r1224-first-read-status', ios, 0)
        call check_char('r1224-first-read-value', rec, 'A')
        backspace u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1224-unit-form-status', ios, 0)
        call check_char('r1224-unit-form-value', rec, 'A')
        read(u,'(a)',iostat=ios) rec
        call check_int('r1224-second-read-status', ios, 0)
        call check_char('r1224-second-read-value', rec, 'B')
        backspace(unit=u, iostat=ios)
        call check_int('r1224-position-form-backspace-status', ios, 0)
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1224-position-form-read-status', ios, 0)
        call check_char('r1224-position-form-value', rec, 'B')
        close(u, status='delete')
    """, 9,
        "R1224 gives both BACKSPACE unit-number and parenthesized position-spec-list forms; each form repositions a known sequential file and exact read-back observes the form used.",
        [("remove-backspace-unit-form", "        backspace u", "        continue"),
         ("remove-backspace-position-form", "        backspace(unit=u, iostat=ios)", "        ios = 0"),
         ("r1224-second-record-changed", "        write(u,'(a)') 'B'", "        write(u,'(a)') 'C'")])

    c.add_valid("12.8.1", "R1225", "endfile_forms",
        ["endfile-unit-number-form", "endfile-position-spec-list-form"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_r1225a.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        endfile u
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1225-unit-read-status', ios, 0)
        call check_char('r1225-unit-read-value', rec, 'A')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1225-unit-end-status', ios, iostat_end)
        call check_char('r1225-unit-end-sentinel', rec, '@')
        close(u, status='delete')
        open(newunit=u, file='iwpf_r1225b.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'B'
        endfile(unit=u, iostat=ios)
        call check_int('r1225-position-endfile-status', ios, 0)
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1225-position-read-status', ios, 0)
        call check_char('r1225-position-read-value', rec, 'B')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1225-position-end-status', ios, iostat_end)
        call check_char('r1225-position-end-sentinel', rec, '%')
        close(u, status='delete')
    """, 9,
        "R1225 gives both ENDFILE unit-number and position-spec-list forms; each writes an endfile marker after a known record, observed by exact read-back and IOSTAT_END.",
        [("replace-endfile-unit-form-with-data", "        endfile u", "        write(u,'(a)') 'C'"),
         ("replace-endfile-position-form-with-data", "        endfile(unit=u, iostat=ios)",
          "        write(u,'(a)') 'C'\n        ios = 0"),
         ("r1225-position-record-changed", "        write(u,'(a)') 'B'", "        write(u,'(a)') 'C'")])

    c.add_valid("12.8.1", "R1226", "rewind_forms",
        ["rewind-unit-number-form", "rewind-position-spec-list-form"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_r1226.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1226-first-read-status', ios, 0)
        call check_char('r1226-first-read-value', rec, 'A')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1226-second-read-status', ios, 0)
        call check_char('r1226-second-read-value', rec, 'B')
        rewind(unit=u, iostat=ios)
        call check_int('r1226-position-rewind-status', ios, 0)
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1226-position-read-status', ios, 0)
        call check_char('r1226-position-read-value', rec, 'A')
        close(u, status='delete')
    """, 7,
        "R1226 gives both REWIND unit-number and position-spec-list forms; after the unit-number form and later position-spec-list form, the next exact read is the first record.",
        [("remove-rewind-unit-form", "        rewind u", "        continue"),
         ("remove-rewind-position-form", "        rewind(unit=u, iostat=ios)", "        ios = 0"),
         ("r1226-first-record-changed", "        write(u,'(a)') 'A'", "        write(u,'(a)') 'C'")])

    c.add_valid("12.8.1", "R1227", "position_specifiers",
        ["position-unit-specifier-form", "position-iostat-specifier-form", "position-iomsg-specifier-form",
         "position-err-label-specifier-form"], """
        integer :: u, other, ios, msg_probe, err_probe
        character(len=1) :: rec
        character(len=32) :: msg
        open(newunit=u, file='iwpf_r1227.dat', status='replace', form='formatted', action='readwrite')
        open(newunit=other, file='iwpf_r1227_other.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        write(other,'(a)') 'X'
        write(other,'(a)') 'Y'
        rewind u
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-first-read-status', ios, 0)
        call check_char('r1227-first-read-value', rec, 'A')
        backspace(unit=u)
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-unit-specifier-read-status', ios, 0)
        call check_char('r1227-unit-specifier-read-value', rec, 'A')
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-second-read-status', ios, 0)
        call check_char('r1227-second-read-value', rec, 'B')
        ios = -123
        backspace(unit=u, iostat=ios)
        call check_int('r1227-iostat-specifier-status', ios, 0)
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-iostat-reread-status', ios, 0)
        call check_char('r1227-iostat-reread-value', rec, 'B')
        msg = '################################'
        msg_probe = -456
        rewind(unit=u, iomsg=msg)
        call check_int('r1227-iomsg-probe-unchanged', msg_probe, -456)
        err_probe = -789
        rewind(unit=u, err=90)
        call check_int('r1227-err-branch-not-taken', err_probe, -789)
        goto 100
90      err_probe = 0
100     continue
        close(u, status='delete')
        close(other, status='delete')
    """, 11,
        "R1227 admits UNIT, IOSTAT, IOMSG, and ERR position specifiers; separate BACKSPACE/REWIND observations exercise UNIT targeting, IOSTAT zero, IOMSG syntax without text comparison, and no ERR branch.",
        [("position-unit-specifier-target-other", "        backspace(unit=u)", "        backspace(unit=other)"),
         ("position-remove-iostat-specifier", "        backspace(unit=u, iostat=ios)",
          "        backspace(unit=u)\n        ios = -123"),
         ("position-iomsg-as-iostat-probe", "        rewind(unit=u, iomsg=msg)", "        rewind(unit=u, iostat=msg_probe)"),
         ("position-err-label-target", "        rewind(unit=u, err=90)", "        rewind(unit=u)\n        err_probe = 0"),
         ("position-record-changed", "        write(u,'(a)') 'A'", "        write(u,'(a)') 'C'", "hygiene")])

    c.add_valid("12.9", "R1228", "flush_forms",
        ["flush-unit-number-form", "flush-spec-list-form"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_flush_forms.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('flush-unit-first-read-status', ios, 0)
        call check_char('flush-unit-first-read-value', rec, 'A')
        flush u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('flush-unit-second-read-status', ios, 0)
        call check_char('flush-unit-second-read-value', rec, 'B')
        ios = -11
        flush(unit=u, iostat=ios)
        call check_int('flush-spec-list-status', ios, 0)
        close(u, status='delete')
    """, 5,
        "R1228 gives both FLUSH unit-number and parenthesized flush-spec-list forms; the spec-list form on a connected file reports IOSTAT zero, and no external visibility is asserted.",
        [("flush-unit-form-wrong-positioner", "        flush u", "        rewind u"),
         ("remove-flush-spec-form", "        flush(unit=u, iostat=ios)", "        ios = -11")])

    c.add_valid("12.9", "R1229", "flush_specifiers",
        ["flush-iostat-specifier-form", "flush-iomsg-specifier-form", "flush-err-label-specifier-form"], """
        integer :: u, ios, msg_probe, err_probe
        character(len=32) :: msg
        open(newunit=u, file='iwpf_flush_specs.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(i0)') 922
        ios = -22
        flush(unit=u, iostat=ios)
        call check_int('flush-unit-iostat-status', ios, 0)
        msg = '################################'
        msg_probe = -33
        flush(unit=u, iomsg=msg)
        call check_int('flush-iomsg-probe-unchanged', msg_probe, -33)
        err_probe = -44
        flush(unit=u, err=90)
        call check_int('flush-err-branch-not-taken', err_probe, -44)
        goto 100
90      err_probe = 0
100     continue
        close(u, status='delete')
    """, 3,
        "R1229 admits IOSTAT, IOMSG, and ERR flush specifiers; successful FLUSH gives IOSTAT zero and no ERR branch, with IOMSG text left unspecified and untested.",
        [("flush-remove-iostat-statement", "        flush(unit=u, iostat=ios)", "        ios = -22"),
         ("flush-iomsg-as-iostat-probe", "        flush(unit=u, iomsg=msg)", "        flush(unit=u, iostat=msg_probe)"),
         ("flush-err-label-target", "        flush(unit=u, err=90)", "        flush(unit=u)\n        err_probe = 0")])

    c.add_valid("12.9", "S12.9-005", "flush_position_unchanged",
        ["flush-file-position-unchanged"], """
        integer :: u, ios
        character(len=1) :: rec
        open(newunit=u, file='iwpf_flush_position.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        rewind u
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('flush-position-first-status', ios, 0)
        call check_char('flush-position-first-value', rec, 'A')
        flush(unit=u, iostat=ios)
        call check_int('flush-position-status', ios, 0)
        rec = '#'
        read(u,'(a)',iostat=ios) rec
        call check_int('flush-position-second-status', ios, 0)
        call check_char('flush-position-second-value', rec, 'B')
        close(u, status='delete')
    """, 5,
        "12.9 p3 says FLUSH has no effect on file position; after reading A, FLUSH leaves the next sequential read positioned at B.",
        [("flush-position-rewind-mutant", "        flush(unit=u, iostat=ios)", "        rewind(unit=u, iostat=ios)"),
         ("flush-position-second-record-changed", "        write(u,'(a)') 'B'", "        write(u,'(a)') 'C'")])

    c.add_valid("12.7.2", "S12.7.2-002", "wait_id_zero_no_pending",
        ["wait-id-zero-or-pending-identifier"], """
        integer :: u, ios, err_flag, end_flag
        open(newunit=u, file='iwpf_wait_id_zero.dat', status='replace', form='formatted', &
             action='readwrite', asynchronous='yes')
        ios = -111
        err_flag = -222
        end_flag = -333
        wait(unit=u, id=0, iostat=ios, err=90, end=91)
        call check_int('wait-id-zero-status', ios, 0)
        call check_int('wait-id-zero-err-not-taken', err_flag, -222)
        call check_int('wait-id-zero-end-not-taken', end_flag, -333)
        goto 100
90      err_flag = 0
        goto 100
91      end_flag = 0
100     continue
        close(u, status='delete')
    """, 3,
        "12.7.2 p3 permits ID=0; on an asynchronous connection with no pending operation, WAIT with ID=0 succeeds with IOSTAT zero and no ERR/END branch.",
        [("remove-wait-id-zero", "        wait(unit=u, id=0, iostat=ios, err=90, end=91)", "        ios = -111")])

    c.add_valid("12.7.2", "S12.7.2-004", "wait_no_id_unavailable",
        ["wait-no-id-unconnected-unit-permitted", "wait-no-id-nonasynchronous-unit-permitted"], """
        integer :: u, closed_unit, ios
        logical :: opened
        open(newunit=closed_unit, status='scratch', form='formatted')
        close(closed_unit, status='delete')
        inquire(unit=closed_unit, opened=opened)
        call check_false('closed-unit-not-opened', opened)
        ios = -121
        wait(unit=closed_unit, iostat=ios)
        call check_int('wait-closed-unit-status', ios, 0)
        open(newunit=u, file='iwpf_wait_nonasync.dat', status='replace', form='formatted', action='readwrite')
        ios = -122
        wait(unit=u, iostat=ios)
        call check_int('wait-nonasync-unit-status', ios, 0)
        close(u, status='delete')
    """, 3,
        "12.7.2 p4 permits WAIT without ID for unconnected and non-asynchronous units; both cases report IOSTAT zero with no timing or buffering assertion.",
        [("remove-wait-closed-unit", "        wait(unit=closed_unit, iostat=ios)", "        ios = -121"),
         ("remove-wait-nonasync-unit", "        wait(unit=u, iostat=ios)", "        ios = -122")])

    c.add_valid("12.7.2", "S12.7.2-005", "wait_unavailable_no_error_end",
        ["wait-no-id-unavailable-unit-no-error", "wait-no-id-unavailable-unit-no-end"], """
        integer :: closed_unit, ios, err_flag, end_flag
        logical :: opened
        open(newunit=closed_unit, status='scratch', form='formatted')
        close(closed_unit, status='delete')
        inquire(unit=closed_unit, opened=opened)
        call check_false('unavailable-closed-unit', opened)
        ios = -131
        err_flag = -132
        end_flag = -133
        wait(unit=closed_unit, iostat=ios, err=90, end=91)
        call check_int('unavailable-wait-status', ios, 0)
        call check_int('unavailable-wait-no-error-branch', err_flag, -132)
        call check_int('unavailable-wait-no-end-branch', end_flag, -133)
        goto 100
90      err_flag = 0
        goto 100
91      end_flag = 0
100     continue
    """, 4,
        "12.7.2 p4 says permitted no-ID WAIT on an unavailable unit causes no error or EOF; IOSTAT is zero and neither ERR nor END branch is taken.",
        [("remove-unavailable-wait", "        wait(unit=closed_unit, iostat=ios, err=90, end=91)", "        ios = -131"),
         ("force-error-branch-mutant", "        wait(unit=closed_unit, iostat=ios, err=90, end=91)",
          "        wait(unit=closed_unit, iostat=ios)\n        err_flag = 0")])

    c.add_invalid("12.8.1", "C1241", "position_duplicate_iostat",
        ["position-duplicate-specifier-rejected"], """
        program p
        implicit none
        integer :: u, ios, ios2
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        rewind(unit=u, iostat=ios, iostat=ios2)
        end program p
    """,
        "C1241 prohibits duplicate position specifiers; the conforming control removes only the second IOSTAT= specifier.",
        5, ["duplicate", "already", "iostat"], "position_specifiers")

    c.add_invalid("12.9", "C1244", "flush_duplicate_iostat",
        ["flush-duplicate-specifier-rejected"], """
        program p
        implicit none
        integer :: u, ios, ios2
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        flush(unit=u, iostat=ios, iostat=ios2)
        end program p
    """,
        "C1244 prohibits duplicate FLUSH specifiers; the conforming control removes only the second IOSTAT= specifier.",
        5, ["duplicate", "already", "iostat"], "flush_specifiers")

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
            raise ValueError(f"pending mismatch for {requirement['id']}: {set(requirement['pending'])} != {expected_pending}")
        if selected:
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered))
            diag_count = sum(1 for spec in selected if spec["kind"] == "invalid")
            run_count = len(selected) - diag_count
            text = ("WAIT/position/FLUSH fixture implementation: "
                    f"{run_count} valid run-phase program(s) and {diag_count} diagnostic program(s) cover {labels}. "
                    "Runtime oracles use per-run named files, exact integer/character read-back, IOSTAT zero "
                    "or ISO_FORTRAN_ENV IOSTAT_END only, and branch sentinel flags; IOMSG text, specific "
                    "nonzero IOSTAT values, asynchronous overlap timing, external FLUSH visibility, and processor-dependent "
                    "file storage are not asserted.")
            requirement["oracle"] = owned_paragraph(requirement["oracle"],
                                                     "WAIT/position/FLUSH fixture implementation:", text)
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
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - WAIT/position/FLUSH fixtures\n\n"
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
    text += "## WAIT/position/FLUSH fixture derivations\n\n"
    for spec in selected:
        text += f"### `{spec['variant']}` / `{spec['rule']}`\n\n"
        text += "**Facets:** " + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n"
        text += spec["derivation"] + "\n\n"
        if spec["kind"] == "valid":
            feature = [m["id"] for m in spec["mutants"] if m["category"] == "feature"]
            text += "Feature mutations: " + ", ".join(f"`{m}`" for m in feature) + ".\n\n"
        else:
            text += f"Conforming control: `{spec['control']}`.\n\n"
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
        raise SystemExit("stale io_wait_position_flush_12_7_12_9 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def known_parent_compile_skip(compiler, source, output):
    if "lfortran" not in Path(compiler).name.lower():
        return False
    return ("wait(" in source.lower()
            and "Newline is unexpected here" in output
            and "syntax error" in output.lower())


def run_mutations(compiler, std, keep=False):
    files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_wait_position_flush_12_7_12_9" / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    skipped = 0
    try:
        for name, spec in specs.items():
            if spec["kind"] != "valid":
                continue
            parent = (ROOT / spec["source_path"]).read_text()
            parent_work = base / name / "__parent_compile"
            parent_work.mkdir(parents=True)
            parent_src = parent_work / "source.f90"
            parent_exe = parent_work / "program"
            parent_src.write_text(parent)
            parent_built = subprocess.run(compiler_command(compiler, std) + [str(parent_src), "-o", str(parent_exe)],
                                          cwd=parent_work, text=True, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, timeout=40)
            if parent_built.returncode != 0:
                if known_parent_compile_skip(compiler, parent, parent_built.stdout):
                    count = len(spec["mutants"])
                    skipped += count
                    print(f"Known parent skip {name}: {count} mutants (LFortran WAIT parser defect).")
                    continue
                raise SystemExit(f"{name}: parent failed to compile\n{parent_built.stdout}")
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
                                       stderr=subprocess.STDOUT, timeout=40)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, timeout=40)
                if ran.returncode == 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant survived")
        if skipped:
            print(f"Mutation check failed all {total} runnable mutants with {compiler} ({std}); "
                  f"skipped {skipped} mutants for known parent defects.")
        else:
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
