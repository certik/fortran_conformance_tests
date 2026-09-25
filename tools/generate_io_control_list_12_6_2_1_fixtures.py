#!/usr/bin/env python3
"""Generate Clause 12.6.2.1 I/O control-list fixtures."""
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
TOPIC = "io_control_list_12_6_2_1"
CATALOGUES = {"12.6.2.1": "doc/catalogues/control_information_list_12_6_2_1.json"}
VIEWS = {"12.6.2.1": "doc/fortran_2023_12_6_2_1.md"}
VIEW_TITLES = {"12.6.2.1": "Control information list"}

RESTORED_PENDING = {
    ("R1213", "leading-zero-specifier-form"):
        "Left pending: the reference gfortran on this host rejects LEADING_ZERO= in a data-transfer statement, so no reference-validated syntax control can be shipped.",
    ("C1212", "read-leading-zero-rejected"):
        "Left pending: the required conforming WRITE-side LEADING_ZERO= control is rejected by the reference gfortran, so the READ-side negative would not have a one-property reference-valid control.",
    ("C1229", "leading-zero-requires-format-or-namelist"):
        "Left pending: the reference gfortran rejects LEADING_ZERO= in data-transfer control lists before this constraint can be isolated.",
    ("C1225", "asynchronous-yes-value"):
        "Left pending: ASYNCHRONOUS='YES' support has no non-vacuous single-image oracle in this section beyond successful execution; ID/status semantics are owned by later asynchronous I/O rules.",
    ("C1225", "asynchronous-no-value"):
        "Left pending: ASYNCHRONOUS='NO' support has no non-vacuous single-image oracle in this section beyond successful execution; changing it to YES is not observably distinct here.",
    ("C1223", "advance-sequential-or-stream-required"):
        "Left pending: the reference gfortran accepts ADVANCE= on a direct-access control, so no required diagnostic is reference-validated for this property on this host.",
    ("C1226", "async-yes-internal-file-rejected"):
        "Left pending: the reference gfortran rejects ASYNCHRONOUS= even with value NO on an internal file, so a one-property control for the YES-only C1226 diagnostic cannot be compiled.",
    ("C1229", "round-requires-format-or-namelist"):
        "Left pending: the reference gfortran accepts ROUND= on an otherwise unformatted transfer, so no required diagnostic is reference-validated for this property on this host.",
    ("C1231", "narrow-id-range-no-portable-negative"):
        "Left pending: no portable isolated negative exists because processors need not provide an integer kind with decimal exponent range smaller than default integer.",
    ("S12.6.2.1-002", "eor-advance-no-required"):
        "Left pending: changing ADVANCE='NO' to a conforming feature value while retaining EOR= violates the unnumbered shall restriction itself; no portable runtime oracle isolates this non-diagnostic rule.",
    ("S12.6.2.1-004", "limited-character-value-lists"):
        "Left pending: the complete value lists are supplied by later specifier subclauses; this packet covers case interpretation without inventing a list here.",
    ("S12.6.2.1-004", "trailing-blanks-ignored"):
        "Left pending: the reference gfortran on this host rejects ADVANCE= character literals with trailing blanks in data-transfer statements, so this p4 property cannot be reference-validated here.",
    ("S12.6.2.1-006", "delim-list-directed-control"):
        "Left pending: successful DELIM= use with list-directed formatting has no non-vacuous oracle in this section without asserting list-directed output spelling owned by 13.11.",
    ("S12.6.2.1-006", "delim-namelist-control"):
        "Left pending: successful DELIM= use with namelist formatting has no non-vacuous oracle in this section without asserting namelist output spelling owned by 13.11.",
}

CHECKS = r'''
module io_control_list_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_nonzero, check_char, check_true, finish_checks
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
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 5
end if
end subroutine finish_checks
end module io_control_list_checks
'''.lstrip()

EXCLUDES = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported feature",
    "unsupported", "not supported", "not yet supported", "implementation limitation",
    "ASR verify", "ASR verifier", "internal compiler error", "LLVM ERROR",
    "unexpected end of file", "unexpected eof", "out of memory",
]


def body(text):
    return textwrap.dedent(text).strip() + "\n"



READ_TARGETS = [
    re.compile(r"^(?P<indent>\s*)read\s*\(.*\)\s*(?P<target>[A-Za-z]\w*)\s*$", re.I),
    re.compile(r"^(?P<indent>\s*)read\s+\*\s*,\s*(?P<target>[A-Za-z]\w*)\s*$", re.I),
]
INTEGER_DECL = re.compile(r"^\s*integer\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)


def clean_name(item):
    return item.split('=')[0].strip()


def read_match(line):
    for pattern in READ_TARGETS:
        match = pattern.match(line)
        if match:
            return match
    return None


def integer_declarations(lines):
    names = set()
    for line in lines:
        match = INTEGER_DECL.match(line)
        if not match:
            continue
        for item in match.group("names").split(","):
            name = clean_name(item)
            if re.match(r"^[A-Za-z]\w*$", name):
                names.add(name.lower())
    return names


def find_read_expected(lines, index, target):
    pattern = re.compile(r"call check_int\('[^']+',\s*" + re.escape(target) + r"\s*,\s*([^,)]+)\)", re.I)
    for next_line in lines[index + 1:index + 12]:
        if read_match(next_line):
            break
        match = pattern.search(next_line)
        if match:
            return match.group(1).strip()
    raise ValueError(f"read target {target} has no following integer value oracle")


def add_pre_read_guards(main):
    lines = main.splitlines()
    integers = integer_declarations(lines)
    output = []
    probes = []
    read_index = 0
    for index, line in enumerate(lines):
        match = read_match(line)
        if not match:
            output.append(line)
            continue
        target = match.group("target")
        if target.lower() not in integers:
            raise ValueError(f"read target {target} has no integer declaration")
        expected = find_read_expected(lines, index, target)
        read_index += 1
        indent = match.group("indent")
        sentinel = f"-{7000 + read_index}"
        poison = f"-{8000 + read_index}"
        default = "0"
        if expected == sentinel:
            raise ValueError(f"read target {target} expected value equals sentinel {sentinel}")
        label = f"pre-read-{read_index}-{target}"
        output.append(f"{indent}{target} = {poison}")
        sentinel_line = f"{indent}{target} = {sentinel}"
        output.append(sentinel_line)
        output.append(f"{indent}call check_int('{label}', {target}, {sentinel})")
        probes.extend([
            (f"{label}-remove-sentinel-init", sentinel_line, "", "sentinel"),
            (f"{label}-expected-sentinel-init", sentinel_line, f"{indent}{target} = {expected}", "sentinel"),
            (f"{label}-default-sentinel-init", sentinel_line, f"{indent}{target} = {default}", "sentinel"),
        ])
        output.append(line)
    return "\n".join(output) + "\n", probes, read_index


def with_checks(body_text, checks):
    main, probes, guard_checks = add_pre_read_guards(body(body_text))
    total_checks = checks + guard_checks
    src = CHECKS + "program p\nuse io_control_list_checks\nimplicit none\n" + main
    if re.search(r"(?im)^\s*contains\s*$", main):
        src = CHECKS + "program p\nuse io_control_list_checks\nimplicit none\n" + re.sub(
            r"(?im)^\s*contains\s*$", f"call finish_checks({total_checks})\ncontains", main, count=1) + "end program p\n"
    else:
        src += f"call finish_checks({total_checks})\nend program p\n"
    return src, total_checks, probes


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
        if path.suffix == ".f90" and max(map(len, content.splitlines()), default=0) > 132:
            raise ValueError(f"line too long in {rel}")
        self.files[path] = raw

    def add_valid(self, rule, variant, facets, body_text, checks, derivation, mutants):
        name = ident(rule, variant, "valid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src, total_checks, sentinel_probes = with_checks(body_text, checks)
        manifest = {
            "schema_version": 1, "id": name, "rule": rule, "facets": list(facets),
            "standard": "f2023", "evidence": "effect", "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0},
        }
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        normalized = []
        for item in mutants:
            if len(item) == 3:
                mid, old, new = item; category = "feature"
            else:
                mid, old, new, category = item
            old = textwrap.dedent(old).strip("\n")
            new = textwrap.dedent(new).strip("\n")
            if src.count(old) != 1:
                raise ValueError(f"{name}: mutant span not unique: {mid}: {old!r} count {src.count(old)}")
            normalized.append({"id": mid, "old": old, "new": new, "category": category})
        self.cases[name] = {
            "section": "12.6.2.1", "rule": rule, "variant": variant, "facets": list(facets),
            "path": folder + "/fixture.json", "source_path": folder + "/source.f90",
            "kind": "valid", "evidence": "effect", "checks": total_checks,
            "derivation": derivation, "mutants": normalized + [
                {"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in sentinel_probes
            ],
        }

    def add_control(self, rule, variant, facets, source_text, derivation, control_for):
        name = ident(rule, variant, "valid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src = body(source_text)
        manifest = {
            "schema_version": 1, "id": name, "rule": rule, "facets": list(facets),
            "standard": "f2023", "evidence": "positive-control", "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0},
        }
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = {
            "section": "12.6.2.1", "rule": rule, "variant": variant, "facets": list(facets),
            "path": folder + "/fixture.json", "source_path": folder + "/source.f90",
            "kind": "valid", "evidence": "positive-control", "checks": 0,
            "derivation": derivation, "control_for": control_for, "mutants": [],
        }
        return name

    def add_invalid(self, rule, variant, facets, source_text, derivation, control_id, end_extra=0):
        name = ident(rule, variant, "invalid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        raw = body(source_text)
        lines = raw.splitlines()
        markers = [i + 1 for i, line in enumerate(lines) if "!ERROR" in line]
        if len(markers) != 1:
            raise ValueError(f"{name}: expected one !ERROR marker")
        line = markers[0]
        src = "\n".join(line_text.replace(" !ERROR", "").replace("!ERROR", "") for line_text in lines) + "\n"
        diagnostic = {"file": "source.f90", "line": line, "excludes_any": EXCLUDES}
        if end_extra:
            diagnostic["end_line"] = line + end_extra
        manifest = {
            "schema_version": 1, "id": name, "rule": rule, "facets": list(facets),
            "standard": "f2023", "evidence": "effect", "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
            "expect": {"phase": "compile", "outcome": "diagnose", "step": "source", "diagnostic": diagnostic},
        }
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = {
            "section": "12.6.2.1", "rule": rule, "variant": variant, "facets": list(facets),
            "path": folder + "/fixture.json", "source_path": folder + "/source.f90",
            "kind": "invalid", "evidence": "effect", "checks": 0,
            "derivation": derivation, "control": control_id, "diagnostic_line": line, "mutants": [],
        }

    def add_pair(self, rule, variant, facets, invalid_source, control_source, derivation, end_extra=0):
        control_id = self.add_control(rule, variant + "_control", facets, control_source,
                                      "Conforming one-property control for diagnostic fixture `" + variant + "`.",
                                      ident(rule, variant, "invalid"))
        self.add_invalid(rule, variant, facets, invalid_source, derivation, control_id, end_extra=end_extra)


COMMON_READ_CONTROL = """
program p
implicit none
integer :: value
character(len=1) :: rec
rec = '7'
value = -777
read(unit=rec, fmt='(I1)') value
if (value /= 7) error stop 1
end program p
"""

COMMON_WRITE_CONTROL = """
program p
implicit none
integer :: u
open(newunit=u, status='scratch', form='formatted')
write(unit=u, fmt='(I1)') 7
close(u)
end program p
"""


def build_corpus(root=ROOT):
    c = Corpus(root)

    c.add_valid("S12.6.2.1-001", "internal_read_fmt_governs_transfer",
        ["control-list-governs-data-transfer"], """
        integer :: value
        character(len=1) :: rec
        rec = '7'
        value = -777
        call check_int('pre-read-value', value, -777)
        read(unit=rec, fmt='(I1)') value
        call check_int('formatted-internal-read', value, 7)
        """, 2,
        "R1213 UNIT= and FMT= choose the internal file and explicit format; p1 says the list governs transfer, C1221 permits the internal formatted read, and p3 classifies the format-controlled transfer as formatted.",
        [("format-width-load-bearing", "read(unit=rec, fmt='(I1)') value", "read(unit=rec, fmt='(A1)') value")])

    c.add_valid("S12.6.2.1-003", "external_unformatted_absence_roundtrip",
        ["absence-makes-unformatted"], """
        integer :: u, value
        open(newunit=u, status='scratch', form='unformatted')
        write(u) 77
        rewind(u)
        value = -777
        call check_int('pre-unformatted-read', value, -777)
        read(u) value
        call check_int('unformatted-roundtrip', value, 77)
        close(u)
        """, 2,
        "p3 says absence of a format or namelist group makes the transfer unformatted; an external unformatted write/read round trip recovers the exact integer without asserting file bytes.",
        [("insert-format-on-write", "write(u) 77", "write(u,'(I2)') 77")])

    c.add_valid("S12.6.2.1-005", "advance_no_sequential_two_reads",
        ["advance-admitted-external-formatted-sequential-explicit-format"], """
        integer :: u, first, second
        open(newunit=u, status='scratch', form='formatted', access='sequential')
        write(u,'(A)') '12'
        rewind(u)
        first = -701
        second = -702
        call check_int('pre-first', first, -701)
        read(u,'(I1)',advance='NO') first
        call check_int('nonadvance-first', first, 1)
        call check_int('pre-second', second, -702)
        read(u,'(I1)') second
        call check_int('same-record-second', second, 2)
        close(u)
        """, 4,
        "C1223 admits ADVANCE= for an external formatted sequential statement with explicit format; ADVANCE='NO' leaves the second digit available to the next read from the same record.",
        [("sequential-advance-no-to-yes", "read(u,'(I1)',advance='NO') first", "read(u,'(I1)',advance='YES') first")])

    c.add_valid("S12.6.2.1-005", "advance_no_stream_two_reads",
        ["advance-admitted-external-formatted-stream-explicit-format"], """
        integer :: u, first, second
        open(newunit=u, status='scratch', form='formatted', access='stream')
        write(u,'(A)') '34'
        rewind(u)
        first = -703
        second = -704
        call check_int('pre-stream-first', first, -703)
        read(u,'(I1)',advance='NO') first
        call check_int('stream-first', first, 3)
        call check_int('pre-stream-second', second, -704)
        read(u,'(I1)') second
        call check_int('stream-same-record-second', second, 4)
        close(u)
        """, 4,
        "C1223 also admits ADVANCE= for external formatted stream transfers with explicit format; the nonadvancing read leaves the next stream character for the following read.",
        [("stream-advance-no-to-yes", "read(u,'(I1)',advance='NO') first", "read(u,'(I1)',advance='YES') first")])

    c.add_valid("S12.6.2.1-004", "advance_value_case_insensitive",
        ["case-insensitive-values"], """
        integer :: u, c, d
        open(newunit=u, status='scratch', form='formatted', access='sequential')
        write(u,'(A)') '34'
        rewind(u)
        c=-3; d=-4
        read(u,'(I1)',advance='no') c
        call check_int('case-first', c, 3)
        read(u,'(I1)') d
        call check_int('case-second', d, 4)
        close(u)
        """, 2,
        "p4 requires control-character values to be interpreted without regard to case; lowercase ADVANCE='no' behaves as ADVANCE='NO' and leaves the second digit for the next read.",
        [("lowercase-value-to-yes", "read(u,'(I1)',advance='no') c", "read(u,'(I1)',advance='yes') c")])

    c.add_valid("C1216", "internal_namelist_read_group",
        ["namelist-group-name-valid"], """
        integer :: value
        character(len=40) :: rec
        namelist /grp/ value
        rec = '&grp value=8 /'
        value = -808
        call check_int('pre-namelist-value', value, -808)
        read(unit=rec, nml=grp)
        call check_int('namelist-read-value', value, 8)
        """, 2,
        "R1213 admits NML=, C1216 requires the operand to name a namelist group, C1221 permits namelist control for an internal file, and p3 classifies the namelist transfer as formatted.",
        [("namelist-to-explicit-format", "read(unit=rec, nml=grp)", "read(unit=rec, fmt='(I1)') value")])

    c.add_valid("R1213", "iostat_and_err_status_controls",
        ["iostat-variable-specifier-form", "err-label-specifier-form"], """
        integer :: ios, value, u
        character(len=1) :: rec
        rec = '9'
        ios = -909
        value = -919
        read(unit=rec, fmt='(I1)', iostat=ios) value
        call check_int('iostat-success-zero', ios, 0)
        call check_int('iostat-read-value', value, 9)
        open(newunit=u, status='scratch', form='formatted', action='read')
        write(u,'(I1)',err=100) 7
        error stop 101
100     call check_true('err-branch-taken', .true.)
        close(u)
        """, 3,
        "R1213 admits IOSTAT= and ERR=; a successful formatted read sets IOSTAT to zero, and a too-small internal WRITE takes the ERR branch without asserting message text.",
        [("remove-iostat-specifier", "read(unit=rec, fmt='(I1)', iostat=ios) value", "read(unit=rec, fmt='(I1)') value"),
         ("remove-err-specifier", "write(u,'(I1)',err=100) 7", "write(u,'(I1)') 7")])

    c.add_valid("R1213", "end_label_branch_on_eof",
        ["end-label-specifier-form"], """
        integer :: u
        open(newunit=u, status='scratch', form='formatted')
        rewind(u)
        read(u,'(I1)',end=100)
        error stop 10
100     call check_true('end-branch-taken', .true.)
        close(u)
        """, 1,
        "R1213 admits END=; reading an empty external formatted file takes the END branch without asserting a processor-dependent status value.",
        [("remove-end-branch", "read(u,'(I1)',end=100)", "read(u,'(I1)')")])

    c.add_valid("R1213", "eor_label_branch_on_short_record",
        ["eor-label-specifier-form", "size-variable-specifier-form"], """
        integer :: u, value, n
        open(newunit=u, status='scratch', form='formatted')
        write(u,'(A)') '5'
        rewind(u)
        value = -505
        n = -515
        read(u,'(I2)',advance='NO',eor=100,size=n) value
        error stop 11
100     call check_int('eor-value', value, 5)
        call check_int('eor-size', n, 1)
        close(u)
        """, 2,
        "R1213 admits EOR= and SIZE=; a nonadvancing read of a short record reaches EOR and reports the single character transferred in SIZE.",
        [("remove-eor-specifier", "read(u,'(I2)',advance='NO',eor=100,size=n) value", "read(u,'(I2)',advance='NO',size=n) value"),
         ("remove-size-specifier", "read(u,'(I2)',advance='NO',eor=100,size=n) value", "read(u,'(I2)',advance='NO',eor=100) value")])

    c.add_valid("R1213", "pos_and_rec_controls",
        ["pos-specifier-form", "rec-specifier-form"], """
        integer :: us, ud, value
        open(newunit=us, status='scratch', form='formatted', access='stream')
        write(us,'(A)') '567'
        value = -565
        read(us,'(I1)',pos=2) value
        call check_int('stream-pos-read', value, 6)
        close(us)
        open(newunit=ud, status='scratch', form='formatted', access='direct', recl=1)
        write(ud,'(I1)',rec=1) 7
        value = -575
        read(ud,'(I1)',rec=1) value
        call check_int('direct-rec-read', value, 7)
        close(ud)
        """, 2,
        "R1213 admits POS= and REC=; POS=2 on a formatted stream reads the second digit and REC=1 on direct access retrieves the written record.",
        [("pos-change", "read(us,'(I1)',pos=2) value", "read(us,'(I1)',pos=1) value"),
         ("rec-change", "read(ud,'(I1)',rec=1) value", "read(ud,'(I1)',rec=2) value")])

    # R1213 syntax negatives (LEADING_ZERO left pending because gfortran rejects controls).
    r1213_cases = [
        ("unit_missing_operand", ["unit-specifier-form"], "read(unit=, fmt='(I1)') value", COMMON_READ_CONTROL),
        ("fmt_missing_operand", ["format-specifier-form"], "read(unit=rec, fmt=) value", COMMON_READ_CONTROL),
        ("nml_missing_operand", ["namelist-specifier-form"], "read(unit=rec, nml=) ", """program p
implicit none
integer :: value
character(len=40) :: rec
namelist /grp/ value
rec='&grp value=7 /'; value=-1
read(unit=rec, nml=grp)
if(value/=7) error stop 1
end program p
"""),
        ("advance_missing_operand", ["advance-specifier-form"], "read(u,'(I1)',advance=) value", """program p
implicit none
integer :: u,value
open(newunit=u,status='scratch',form='formatted')
write(u,'(A)') '7'; rewind(u); value=-1
read(u,'(I1)',advance='NO') value
if(value/=7) error stop 1
close(u)
end program p
"""),
        ("asynchronous_missing_operand", ["asynchronous-specifier-form"], "write(u,'(I1)',asynchronous=) 7", """program p
implicit none
integer :: u
open(newunit=u,status='scratch',form='formatted')
write(u,'(I1)',asynchronous='NO') 7
close(u)
end program p
"""),
        ("blank_missing_operand", ["blank-specifier-form"], "read(rec,'(I1)',blank=) value", COMMON_READ_CONTROL),
        ("decimal_missing_operand", ["decimal-specifier-form"], "read(rec,'(I1)',decimal=) value", COMMON_READ_CONTROL),
        ("delim_missing_operand", ["delim-specifier-form"], "write(unit=u, fmt=*, delim=) 'a'", """program p
implicit none
integer :: u
open(newunit=u,status='scratch',form='formatted')
write(unit=u, fmt=*, delim='QUOTE') 'a'
close(u)
end program p
"""),
        ("end_missing_operand", ["end-label-specifier-form"], "read(u,'(I1)',end=) value", COMMON_READ_CONTROL),
        ("eor_missing_operand", ["eor-label-specifier-form"], "read(u,'(I1)',advance='NO',eor=) value", COMMON_READ_CONTROL),
        ("err_missing_operand", ["err-label-specifier-form"], "read(rec,'(I1)',err=) value", COMMON_READ_CONTROL),
        ("id_missing_operand", ["id-variable-specifier-form"], "write(u,'(I1)',asynchronous='YES',id=) 7", """program p
implicit none
integer :: u,id
open(newunit=u,status='scratch',form='formatted',asynchronous='yes')
id=-1
write(u,'(I1)',asynchronous='YES',id=id) 7
close(u)
end program p
"""),
        ("iomsg_missing_operand", ["iomsg-variable-specifier-form"], "read(rec,'(I1)',iostat=ios,iomsg=) value", """program p
implicit none
integer :: value, ios
character(len=1) :: rec
character(len=40) :: msg
rec='7'; value=-1; ios=-1; msg='sentinel'
read(rec,'(I1)',iostat=ios,iomsg=msg) value
if(value/=7 .or. ios/=0) error stop 1
end program p
"""),
        ("iostat_missing_operand", ["iostat-variable-specifier-form"], "read(rec,'(I1)',iostat=) value", COMMON_READ_CONTROL),
        ("pad_missing_operand", ["pad-specifier-form"], "read(rec,'(I1)',pad=) value", COMMON_READ_CONTROL),
        ("pos_missing_operand", ["pos-specifier-form"], "read(u,'(I1)',pos=) value", """program p
implicit none
integer :: u,value
open(newunit=u,status='scratch',form='formatted',access='stream')
write(u,'(A)') '7'; value=-1
read(u,'(I1)',pos=1) value
if(value/=7) error stop 1
close(u)
end program p
"""),
        ("rec_missing_operand", ["rec-specifier-form"], "read(u,'(I1)',rec=) value", """program p
implicit none
integer :: u,value
open(newunit=u,status='scratch',form='formatted',access='direct',recl=1)
write(u,'(I1)',rec=1) 7; value=-1
read(u,'(I1)',rec=1) value
if(value/=7) error stop 1
close(u)
end program p
"""),
        ("round_missing_operand", ["round-specifier-form"], "read(rec,'(I1)',round=) value", COMMON_READ_CONTROL),
        ("sign_missing_operand", ["sign-specifier-form"], "write(unit=u, fmt='(I1)', sign=) 7", COMMON_WRITE_CONTROL),
        ("size_missing_operand", ["size-variable-specifier-form"], "read(u,'(I1)',advance='NO',size=) value", COMMON_READ_CONTROL),
    ]
    for variant, facets, bad_stmt, control in r1213_cases:
        invalid = f"""program p
implicit none
integer :: value, u, ios
character(len=40) :: rec
rec = '7'; value = -1; u = 10; ios = -1
{bad_stmt} !ERROR
end program p
"""
        c.add_pair("R1213", variant, facets, invalid, control,
                   "R1213 enumerates this io-control-spec form; deleting only its operand/punctuation is a syntax error anchored at the changed control item.")

    # Numbered constraint diagnostic/control pairs.
    pairs = [
        ("R1214", "id_nonscalar", ["nonscalar-id-variable-rejected"], "integer :: u, id(1)", "write(u,'(I1)',asynchronous='YES',id=id) 7", "integer :: u, id"),
        ("R1214", "id_noninteger", ["noninteger-id-variable-rejected"], "integer :: u\nreal :: id", "write(u,'(I1)',asynchronous='YES',id=id) 7", "integer :: u, id"),
        ("C1210", "duplicate_fmt", ["duplicate-specifier-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,fmt='(I1)',fmt='(I1)') value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1211", "missing_unit", ["io-unit-present"], "integer :: value", "read(fmt='(I1)') value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1211", "positional_unit_not_first", ["positional-io-unit-first"], "integer :: value\ncharacter(len=1) :: rec", "read(fmt='(I1)', rec) value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1212", "read_delim", ["read-delim-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,'(I1)',delim='QUOTE') value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1212", "read_sign", ["read-sign-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,'(I1)',sign='SUPPRESS') value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1213", "write_blank", ["write-blank-rejected"], "integer :: u", "write(u,'(I1)',blank='ZERO') 7", "integer :: u"),
        ("C1213", "write_pad", ["write-pad-rejected"], "integer :: u", "write(u,'(I1)',pad='YES') 7", "integer :: u"),
        ("C1213", "write_end", ["write-end-rejected"], "integer :: u", "write(u,'(I1)',end=100) 7", "integer :: u"),
        ("C1213", "write_eor", ["write-eor-rejected"], "integer :: u", "write(u,'(I1)',advance='NO',eor=100) 7", "integer :: u"),
        ("C1213", "write_size", ["write-size-rejected"], "integer :: u, n", "write(u,'(I1)',size=n) 7", "integer :: u, n"),
        ("C1214", "list_directed_size", ["list-directed-size-rejected"], "integer :: value, n\ncharacter(len=1) :: rec", "read(rec,*,size=n) value", "integer :: value, n\ncharacter(len=1) :: rec"),
        ("C1214", "namelist_size", ["namelist-size-rejected"], "integer :: value, n\ncharacter(len=40) :: rec\nnamelist /grp/ value", "read(rec,nml=grp,size=n)", "integer :: value, n\ncharacter(len=40) :: rec\nnamelist /grp/ value"),
        ("C1216", "non_namelist_name", ["non-namelist-name-rejected"], "integer :: value\ncharacter(len=40) :: rec", "read(rec,nml=value)", "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value"),
        ("C1217", "namelist_with_format", ["namelist-with-format-rejected"], "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value", "read(rec,nml=grp,fmt='(I1)')", "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value"),
        ("C1217", "namelist_with_input", ["namelist-with-input-items-rejected"], "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value", "read(rec,nml=grp) value", "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value"),
        ("C1217", "namelist_with_output", ["namelist-with-output-items-rejected"], "integer :: value, u\nnamelist /grp/ value", "write(u,nml=grp) value", "integer :: value, u\nnamelist /grp/ value"),
        ("C1218", "positional_format_third", ["positional-format-second"], "integer :: value, ios\ncharacter(len=1) :: rec", "read(unit=rec, iostat=ios, '(I1)') value", "integer :: value, ios\ncharacter(len=1) :: rec"),
        ("C1218", "positional_format_first_not_unit", ["positional-format-first-item-io-unit"], "integer :: value\ncharacter(len=1) :: rec", "read(err=100, '(I1)', unit=rec) value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1219", "positional_namelist_third", ["positional-namelist-second"], "integer :: value, ios\ncharacter(len=40) :: rec\nnamelist /grp/ value", "read(unit=rec, iostat=ios, grp)", "integer :: value, ios\ncharacter(len=40) :: rec\nnamelist /grp/ value"),
        ("C1219", "positional_namelist_first_not_unit", ["positional-namelist-first-item-io-unit"], "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value", "read(err=100, grp, unit=rec)", "integer :: value\ncharacter(len=40) :: rec\nnamelist /grp/ value"),
        ("C1220", "internal_rec", ["internal-file-rec-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,'(I1)',rec=1) value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1220", "internal_pos", ["internal-file-pos-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,'(I1)',pos=1) value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1221", "internal_missing_format", ["internal-file-missing-format-or-namelist-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec) value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1222", "rec_with_end", ["rec-with-end-rejected"], "integer :: u, value", "read(u,'(I1)',rec=1,end=100) value", "integer :: u, value"),
        ("C1222", "rec_with_asterisk", ["rec-with-asterisk-format-rejected"], "integer :: u, value", "read(u,*,rec=1) value", "integer :: u, value"),
        ("C1223", "advance_unformatted", ["advance-formatted-transfer-required"], "integer :: u, value", "read(u,advance='NO') value", "integer :: u, value"),
        ("C1223", "advance_direct", ["advance-sequential-or-stream-required"], "integer :: u, value", "read(u,'(I1)',rec=1,advance='NO') value", "integer :: u, value"),
        ("C1223", "advance_list_directed", ["advance-explicit-format-required"], "integer :: u, value", "read(u,*,advance='NO') value", "integer :: u, value"),
        ("C1223", "advance_internal", ["advance-external-unit-required"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,'(I1)',advance='NO') value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1224", "eor_no_advance", ["eor-requires-advance"], "integer :: u, value", "read(u,'(I1)',eor=100) value", "integer :: u, value"),
        ("C1225", "asynchronous_other", ["asynchronous-other-value-rejected"], "integer :: u", "write(u,'(I1)',asynchronous='MAYBE') 7", "integer :: u"),
        ("C1226", "async_yes_internal", ["async-yes-internal-file-rejected"], "integer :: value\ncharacter(len=1) :: rec", "read(rec,'(I1)',asynchronous='YES') value", "integer :: value\ncharacter(len=1) :: rec"),
        ("C1227", "id_missing_async", ["id-missing-asynchronous-rejected"], "integer :: u, id", "write(u,'(I1)',id=id) 7", "integer :: u, id"),
        ("C1227", "id_async_no", ["id-with-asynchronous-no-rejected"], "integer :: u, id", "write(u,'(I1)',asynchronous='NO',id=id) 7", "integer :: u, id"),
        ("C1228", "pos_with_rec", ["pos-with-rec-rejected"], "integer :: u, value", "read(u,'(I1)',pos=1,rec=1) value", "integer :: u, value"),
        ("C1229", "decimal_unformatted", ["decimal-requires-format-or-namelist"], "integer :: u, value", "read(u,decimal='POINT') value", "integer :: u, value"),
        ("C1229", "blank_unformatted", ["blank-requires-format-or-namelist"], "integer :: u, value", "read(u,blank='ZERO') value", "integer :: u, value"),
        ("C1229", "pad_unformatted", ["pad-requires-format-or-namelist"], "integer :: u, value", "read(u,pad='YES') value", "integer :: u, value"),
        ("C1229", "sign_unformatted", ["sign-requires-format-or-namelist"], "integer :: u", "write(u,sign='SUPPRESS') 7", "integer :: u"),
        ("C1229", "round_unformatted", ["round-requires-format-or-namelist"], "integer :: u, value", "read(u,round='NEAREST') value", "integer :: u, value"),
        ("C1230", "delim_explicit_format", ["delim-explicit-format-rejected"], "integer :: u", "write(u,'(A)',delim='QUOTE') 'a'", "integer :: u"),
    ]
    unsupported_variants = {"advance_direct", "async_yes_internal", "round_unformatted"}
    pairs = [item for item in pairs if item[1] not in unsupported_variants]
    for rule, variant, facets, decls, bad_stmt, control_decls in pairs:
        setup = ""
        if "character(len=1) :: rec" in decls:
            setup += "rec = '7'\n"
        if "character(len=40) :: rec" in decls:
            setup += "rec = '&grp value=7 /'\n"
        if "integer :: value" in decls or "integer :: value," in decls:
            setup += "value = -1\n"
        if "integer :: u" in decls or "integer :: u," in decls:
            setup += "open(newunit=u, status='scratch', form='formatted', access='sequential')\n"
        if "integer :: id" in decls or "id" in decls:
            setup += "id = -2\n" if "id" in decls else ""
        tail = "100 continue\n" if "100" in bad_stmt else ""
        invalid = f"""program p
implicit none
{decls}
{setup}{bad_stmt} !ERROR
{tail}end program p
"""
        csetup = ""
        if "character(len=1) :: rec" in control_decls:
            csetup += "rec = '7'\n"
        if "character(len=40) :: rec" in control_decls:
            csetup += "rec = '&grp value=7 /'\n"
        if "integer :: value" in control_decls or "integer :: value," in control_decls:
            csetup += "value = -1\n"
        if "integer :: u" in control_decls or "integer :: u," in control_decls:
            csetup += "open(newunit=u, status='scratch', form='formatted', access='sequential')\n"
        if "id" in control_decls:
            csetup += "id = -2\n"
        # One-property repairs for cases whose statement needs an external unit mode.
        control_stmt = bad_stmt
        replacements = {
            "fmt='(I1)',fmt='(I1)'": "fmt='(I1)'",
            "read(fmt='(I1)') value": "read(rec,fmt='(I1)') value",
            "read(fmt='(I1)', rec) value": "read(unit=rec, fmt='(I1)') value",
            ",delim='QUOTE'": "",
            ",sign='SUPPRESS'": "",
            ",blank='ZERO'": "",
            ",pad='YES'": "",
            ",end=100": "",
            ",eor=100": "",
            ",size=n": "",
            "read(rec,*,size=n) value": "read(rec,*) value",
            "read(rec,nml=grp,size=n)": "read(rec,nml=grp)",
            "nml=value": "nml=grp",
            ",fmt='(I1)'": "",
            "read(rec,nml=grp) value": "read(rec,nml=grp)",
            "write(u,nml=grp) value": "write(u,nml=grp)",
            "unit=rec, iostat=ios, '(I1)'": "unit=rec, '(I1)', iostat=ios",
            "err=100, '(I1)', unit=rec": "unit=rec, '(I1)', err=100",
            "unit=rec, iostat=ios, grp": "unit=rec, grp, iostat=ios",
            "err=100, grp, unit=rec": "unit=rec, grp, err=100",
            ",rec=1": "",
            ",pos=1": "",
            "read(rec) value": "read(rec,'(I1)') value",
            "rec=1,end=100": "rec=1",
            "read(u,*,rec=1) value": "read(u,'(I1)',rec=1) value",
            "read(u,advance='NO') value": "read(u) value",
            ",advance='NO'": "",
            "read(u,*,advance='NO') value": "read(u,'(I1)',advance='NO') value",
            "read(rec,'(I1)',advance='NO') value": "read(rec,'(I1)') value",
            "read(u,'(I1)',eor=100) value": "read(u,'(I1)',advance='NO',eor=100) value",
            "asynchronous='MAYBE'": "asynchronous='NO'",
            "asynchronous='YES'": "asynchronous='NO'",
            "write(u,'(I1)',id=id) 7": "write(u,'(I1)',asynchronous='YES',id=id) 7",
            "asynchronous='NO',id=id": "asynchronous='YES',id=id",
            "pos=1,rec=1": "pos=1",
            "read(u,decimal='POINT') value": "read(u,'(I1)',decimal='POINT') value",
            "read(u,blank='ZERO') value": "read(u,'(I1)',blank='ZERO') value",
            "read(u,pad='YES') value": "read(u,'(I1)',pad='YES') value",
            "write(u,sign='SUPPRESS') 7": "write(u,'(I1)',sign='SUPPRESS') 7",
            "read(u,round='NEAREST') value": "read(u,'(I1)',round='NEAREST') value",
            "write(u,'(A)',delim='QUOTE') 'a'": "write(u,*,delim='QUOTE') 'a'",
        }
        for old, new in replacements.items():
            if old in control_stmt:
                control_stmt = control_stmt.replace(old, new)
        special_repairs = {
            "positional_format_third": "read(rec, '(I1)', iostat=ios) value",
            "positional_format_first_not_unit": "read(rec, '(I1)', err=100) value",
            "positional_namelist_third": "read(rec, grp, iostat=ios)",
            "positional_namelist_first_not_unit": "read(rec, grp, err=100)",
        }
        if variant in special_repairs:
            control_stmt = special_repairs[variant]
        if "read(u,'(I1)',rec=1)" in control_stmt or "write(u,'(I1)',rec=1)" in control_stmt:
            csetup = csetup.replace("access='sequential'", "access='direct', recl=1")
            csetup += "write(u,'(I1)',rec=1) 7\n"
        if "read(u,'(I1)',pos=1)" in control_stmt or "write" not in control_stmt and "pos=1" in control_stmt:
            csetup = csetup.replace("access='sequential'", "access='stream'")
            csetup += "write(u,'(A)') '7'\n"
        control = f"""program p
implicit none
{control_decls}
if (.false.) then
  {control_stmt}
end if
{tail}end program p
"""
        c.add_pair(rule, variant, facets, invalid, control,
                   f"{rule} requires this restriction; the invalid source changes only the listed control-list property from its conforming control.")

    # C1215 branch-target and inclusive-scope diagnostics use bespoke sources.
    for branch, stmt in [("err", "read(rec,'(I1)',err=100) value"),
                         ("end", "read(u,'(I1)',end=100) value"),
                         ("eor", "read(u,'(I2)',advance='NO',eor=100) value")]:
        facets = [f"{branch}-label-branch-target"]
        decl = "integer :: value\ncharacter(len=1) :: rec\nrec='7'; value=-1" if branch == "err" else "integer :: u, value\nopen(newunit=u,status='scratch',form='formatted')\nvalue=-1"
        invalid = f"""program p
implicit none
{decl}
{stmt} !ERROR
100 format(I1)
end program p
"""
        control = f"""program p
implicit none
{decl}
if (.false.) then
  {stmt}
end if
100 continue
end program p
"""
        c.add_pair("C1215", f"{branch}_label_format_target", facets, invalid, control,
                   "C1215 requires ERR/EOR/END labels to identify branch target statements; a FORMAT label is defined but is not a branch target.")
        facets = [f"{branch}-label-same-inclusive-scope"]
        invalid = f"""program p
implicit none
{decl}
{stmt} !ERROR
contains
subroutine q()
100 continue
end subroutine q
end program p
"""
        control = f"""program p
implicit none
{decl}
if (.false.) then
  {stmt}
end if
100 continue
end program p
"""
        c.add_pair("C1215", f"{branch}_label_other_scope", facets, invalid, control,
                   "C1215 also requires the branch target statement to appear in the same inclusive scope as the data transfer statement.",
                   end_extra=3)

    # C1217 namelist with REC needs direct-access setup, kept bespoke.
    c.add_pair("C1217", "namelist_with_rec", ["namelist-with-rec-rejected"], """
        program p
        implicit none
        integer :: u, value
        namelist /grp/ value
        open(newunit=u, status='scratch', form='formatted', access='direct', recl=40)
        value = 1
        write(u,nml=grp,rec=1)
        read(u,nml=grp,rec=1) !ERROR
        close(u)
        end program p
        """, """
        program p
        implicit none
        integer :: u, value
        namelist /grp/ value
        open(newunit=u, status='scratch', form='formatted', access='sequential')
        value = 1
        write(u,nml=grp)
        rewind(u)
        read(u,nml=grp)
        close(u)
        end program p
        """, "C1217 forbids a namelist-group-name when REC= appears; the control removes only REC= from namelist input.")

    return c.files, c.cases


def owned_paragraph(original, marker, replacement):
    paragraphs = [p for p in original.split("\n\n") if p.strip()]
    matches = [i for i, para in enumerate(paragraphs) if para.startswith(marker)]
    if len(matches) > 1:
        raise ValueError(f"multiple owned paragraphs for {marker}")
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
    for req in result["requirements"]:
        selected = by_rule.get(req["id"], [])
        covered = {facet for spec in selected for facet in spec["facets"]}
        for facet in covered:
            if facet not in req["facets"]:
                raise ValueError(f"unknown facet {facet} for {req['id']}")
            req["pending"].pop(facet, None)
        expected_pending = set(req["facets"]) - covered
        for facet in sorted(expected_pending):
            reason = RESTORED_PENDING.get((req["id"], facet))
            if reason is not None:
                req["pending"][facet] = reason
            elif facet not in req["pending"]:
                raise ValueError(f"missing pending reason for {req['id']}:{facet}")
        if set(req["pending"]) != expected_pending:
            raise ValueError(f"pending mismatch for {req['id']}: {set(req['pending'])} != {expected_pending}")
        if selected:
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered))
            diag_count = sum(1 for spec in selected if spec["kind"] == "invalid")
            run_count = len(selected) - diag_count
            text = ("I/O control-list fixture implementation: "
                    f"{run_count} valid/control program(s) and {diag_count} diagnostic program(s) cover {labels}. "
                    "Runtime oracles use exact integer/character/logical values, sentinel preconditions, scratch files, "
                    "stream/direct positions chosen by the processor, and only zero/nonzero or named status properties. "
                    "Diagnostics are line-anchored for R1213/R1214/C1210-C1231 syntax or constraints and have real one-property controls. "
                    "No IOMSG text, processor-dependent unit number, physical filename, or specific nonzero status is asserted.")
            req["oracle"] = owned_paragraph(req["oracle"], "I/O control-list fixture implementation:", text)
            prefix = "Source accounting only. "
            if req["oracle_limitation"].startswith(prefix):
                req["oracle_limitation"] = "Runtime fixture coverage is finite and does not imply fixture review. " + req["oracle_limitation"][len(prefix):]
    return result


def render_view(section, catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(ROOT)
    registry.catalogues[section] = catalogue
    selected = [s for s in specs.values() if s["section"] == section]
    represented = len({(s["rule"], f) for s in selected for f in s["facets"]})
    total = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - I/O control-list fixtures\n\n"
            f"The canonical catalogue is `{CATALOGUES[section]}`. This author packet adds finite runtime and diagnostic fixtures without fixture approval.\n\n"
            "Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256 "
            "`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.\n\n"
            f"**Catalogue source review: {registry.catalogue_review_state(section)}.** "
            f"This topic represents {represented} distinct facets in {len(selected)} program(s); "
            f"{total - pending} of {total} facets are represented and {pending} remain pending.\n\n"
            f"<!-- BEGIN GENERATED {section} -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"])
    text += f"\n<!-- END GENERATED {section} -->\n\n"
    text += "## I/O control-list fixture derivations\n\n"
    for spec in selected:
        text += f"### `{spec['variant']}` / `{spec['rule']}`\n\n"
        text += "**Facets:** " + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n"
        text += spec["derivation"] + "\n\n"
        if spec["kind"] == "valid" and spec["evidence"] == "effect":
            feature = [m["id"] for m in spec["mutants"] if m["category"] == "feature"]
            text += "Feature mutations: " + ", ".join(f"`{m}`" for m in feature) + ".\n\n"
        elif spec["kind"] == "invalid":
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
        raise SystemExit("stale io_control_list_12_6_2_1 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    if "lfortran" in Path(compiler).name.lower():
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std, keep=False):
    _files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_control_list_12_6_2_1" / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    try:
        for name, spec in specs.items():
            if spec["kind"] != "valid" or spec["evidence"] != "effect":
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
                built = subprocess.run(compiler_command(compiler, std) + [str(src), "-o", str(exe)],
                                       cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
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
        check_files(files, specs); action = "Checked"
    else:
        sync_files(files, specs); action = "Generated"
    print(f"{action} {len(files)} files for {len(specs)} fixtures and {len({(s['rule'], f) for s in specs.values() for f in s['facets']})} distinct facets.")


if __name__ == "__main__":
    main()
