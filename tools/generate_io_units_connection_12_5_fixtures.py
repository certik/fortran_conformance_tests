#!/usr/bin/env python3
"""Generate Clause 12.5.1-12.5.4 I/O unit and connection fixtures."""
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
TOPIC = "io_units_connection_12_5"
CATALOGUES = {
    "12.5.1": "doc/catalogues/units_12_5_1.json",
    "12.5.2": "doc/catalogues/connection_modes_12_5_2.json",
    "12.5.3": "doc/catalogues/unit_existence_12_5_3.json",
    "12.5.4": "doc/catalogues/connection_status_12_5_4.json",
}
VIEWS = {
    "12.5.1": "doc/fortran_2023_12_5_1.md",
    "12.5.2": "doc/fortran_2023_12_5_2.md",
    "12.5.3": "doc/fortran_2023_12_5_3.md",
    "12.5.4": "doc/fortran_2023_12_5_4.md",
}
VIEW_TITLES = {
    "12.5.1": "Units",
    "12.5.2": "Connection modes",
    "12.5.3": "Unit existence",
    "12.5.4": "Connection of units to files",
}

RESTORED_PENDING = {
    ("S12.5.1-003", "file-unit-number-nonnegative-or-special"):
        "Left pending: the positive fixture still uses NEWUNIT= as a valid special unit, but the negative/special value-set facet needs a conforming feature mutation that changes the established unit value without relying on processor-dependent ordinary unit existence.",
    ("S12.5.1-007", "error-reporting-external-unit"):
        "Left pending: ERROR_UNIT is required to identify the processor-dependent error-reporting unit, but 12.5.1 p5 does not require a distinct stderr stream or portable physical destination.",
    ("S12.5.1-007", "error-unit-preconnected-formatted-output"):
        "Left pending: a write can check successful formatted output, but this packet does not assert a physical stderr/stdout destination because ERROR_UNIT may be the same as the output unit.",
    ("S12.5.1-007", "error-unit-error_unit-constant"):
        "Left pending: using ERROR_UNIT directly is portable, but distinguishing it from OUTPUT_UNIT or a harness stderr stream is not required by 12.5.1 p5.",
    ("S12.5.4-003", "io-statements-require-connected-unit"):
        "Left pending: this unnumbered shall restriction is not discharged by a positive control, and no portable diagnostic oracle is required here.",
}

CHECKS = """
module io_units_connection_checks
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
end module io_units_connection_checks
""".lstrip()

READ_TARGETS = [
    re.compile(r"^(?P<indent>\s*)read\s*\(.*\)\s*(?P<target>[A-Za-z]\w*)\s*$", re.I),
    re.compile(r"^(?P<indent>\s*)read\s+\*,\s*(?P<target>[A-Za-z]\w*)\s*$", re.I),
]
INTEGER_DECL = re.compile(r"^\s*integer\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
CHARACTER_DECL = re.compile(r"^\s*character\s*\(\s*len\s*=\s*(?P<len>\d+)\s*\)\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
LOGICAL_DECL = re.compile(r"^\s*logical\s*(?:,\s*[^:]*)?::\s*(?P<names>.+)$", re.I)
CHAR_SENTINELS = "#@$%&?+*/;:<>=^~|[]{}"


def body(text):
    return textwrap.dedent(text).strip() + "\n"


def read_match(line):
    for pattern in READ_TARGETS:
        match = pattern.match(line)
        if match:
            return match
    return None


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
    for next_line in lines[index + 1:index + 9]:
        if read_match(next_line):
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
            if expected.strip() == sentinel:
                raise ValueError(f"{label}: expected value equals sentinel")
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_int('{label}', {target}, {sentinel})")
        elif category == "character":
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
        else:
            sentinel = ".true."
            poison = ".false."
            default = ".false."
            output.append(f"{indent}{target} = {poison}")
            sentinel_line = f"{indent}{target} = {sentinel}"
            output.append(sentinel_line)
            output.append(f"{indent}call check_true('{label}', {target})")
        probes.extend([
            (f"{label}-remove-sentinel-init", sentinel_line, f"{indent}! sentinel initializer removed for probe", "sentinel"),
            (f"{label}-expected-sentinel-init", sentinel_line, f"{indent}{target} = {expected.strip()}", "sentinel"),
            (f"{label}-default-sentinel-init", sentinel_line, f"{indent}{target} = {default}", "sentinel"),
        ])
        output.append(line)
    return "\n".join(output) + "\n", probes


def source(body_text, count, modules=""):
    main, probes = add_pre_read_guards(body(body_text))
    total = count + sum(1 for _, _, _, category in probes if category == "sentinel") // 3
    src = CHECKS + modules + "program p\nuse io_units_connection_checks\n"
    src += "use iso_fortran_env, only: input_unit, output_unit, error_unit\n"
    src += "implicit none\n" + main
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
        if path.suffix in (".f90", ".c") and max(map(len, raw.splitlines()), default=0) > 132:
            raise ValueError(f"line too long in {rel}")
        self.files[path] = raw

    def add_valid(self, section, rule, variant, facets, body_text, checks, derivation, mutants,
                  stdout=None, stderr=None, stdin=None, modules=""):
        name = ident(rule, variant, "valid")
        folder = f"tests/fixtures/{TOPIC}_{name.lower()}"
        src, total_checks, sentinel_probes = source(body_text, checks, modules)
        files = ["source.f90"]
        if stdin is not None:
            files.append("stdin.txt")
            self.put(folder + "/stdin.txt", stdin)
        expect = {"phase": "run", "outcome": "success", "exit_code": 0}
        evidence = "positive-control" if rule in {
            "R1201", "R1202", "R1203", "C1201", "C1202", "S12.5.1-003", "S12.5.4-003"
        } else "effect"
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
            "evidence": evidence,
            "files": files,
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free",
                       "output": "source.o"}],
            "link": {"objects": ["source.o"], "output": "program"},
            "expect": expect,
        }
        if stdin is not None:
            manifest["run"] = {"stdin_file": "stdin.txt"}
        self.put(folder + "/source.f90", src)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        normalized_mutants = []
        for item in mutants:
            if len(item) == 3:
                mid, old, new = item
                category = "feature"
            elif len(item) == 4:
                mid, old, new, category = item
            else:
                raise ValueError(f"invalid mutant tuple for {name}: {item!r}")
            normalized_mutants.append((mid, textwrap.dedent(old).strip("\n"),
                                       textwrap.dedent(new).strip("\n"), category))
        normalized_mutants += sentinel_probes
        for item in normalized_mutants:
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
            "stdout": stdout,
            "stderr": stderr,
            "stdin": stdin,
            "mutants": [{"id": m[0], "old": m[1], "new": m[2], "category": m[3]} for m in normalized_mutants],
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
            "evidence": "effect",
            "checks": 0,
            "derivation": derivation,
            "diagnostic_line": diagnostic_line,
            "contains_any": contains_any,
            "control": control,
            "mutants": [],
        }


def build_corpus(root=ROOT):
    c = Corpus(root)

    c.add_valid("12.5.1", "S12.5.1-001", "external_internal_designators",
        ["io-unit-refers-to-file"], """
        integer :: u, ios, external_value, internal_value, class_value
        character(len=8) :: internal_file, alternate_file
        internal_file = '82      '
        alternate_file = '91      '
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        write(u,'(i0)') 41
        rewind u
        external_value = -1
        read(u,*,iostat=ios) external_value
        call check_int('file-unit-number-status', ios, 0)
        call check_int('file-unit-number-value', external_value, 41)
        internal_value = -2
        read(internal_file,*,iostat=ios) internal_value
        call check_int('internal-unit-status', ios, 0)
        call check_int('internal-unit-value', internal_value, 82)
        internal_file = '########'
        write(internal_file,'(i0)') 73
        call check_char('internal-write-designated-file', internal_file, '73      ')
        rewind u
        class_value = -3
        read(u,*,iostat=ios) class_value
        call check_int('external-internal-class-status', ios, 0)
        call check_int('external-internal-class-value', class_value, 41)
        close(u, status='delete')
    """, 7,
        "12.5.1 p1-p2/R1201-R1203 and C1202 define external file-unit-number and default-character internal units; the fixture observes distinct exact records through each designator.",
        [("external-read-uses-internal-file", "        read(u,*,iostat=ios) external_value",
          "        read(alternate_file,*,iostat=ios) external_value"),
         ("internal-read-uses-external-unit", "        read(internal_file,*,iostat=ios) internal_value",
          "        read(u,*,iostat=ios) internal_value"),
         ("internal-write-other-file", "        write(internal_file,'(i0)') 73",
          "        write(alternate_file,'(i0)') 73"),
         ("classification-reread-internal", "        read(u,*,iostat=ios) class_value",
          "        read(internal_file,*,iostat=ios) class_value"),
         ("external-written-record-changed", "        write(u,'(i0)') 41", "        write(u,'(i0)') 42"),
         ("internal-file-initial-record-changed", "        internal_file = '82      '",
          "        internal_file = '83      '"),
         ("default-character-width-changed", "        character(len=8) :: internal_file, alternate_file",
          "        character(len=7) :: internal_file, alternate_file"),
         ("connected-file-data-effect-changed", "        call check_int('file-unit-number-value', external_value, 41)",
          "        call check_int('file-unit-number-value', external_value, 42)", "hygiene"),
         ("internal-designated-file-expected-changed", "        call check_char('internal-write-designated-file', internal_file, '73      ')",
          "        call check_char('internal-write-designated-file', internal_file, '74      ')", "hygiene")])

    c.add_valid("12.5.1", "S12.5.1-005", "preconnected_input_units",
        ["read-asterisk-input-unit", "input-unit-preconnected-initial-image",
         "input-unit-input_unit-constant", "read-without-control-list-uses-input-unit"], """
        integer :: star_value, input_value, bare_value, ios
        character(len=8) :: internal_star, internal_input, internal_bare
        internal_star = '91      '
        internal_input = '92      '
        internal_bare = '93      '
        star_value = -1
        read(*,*,iostat=ios) star_value
        call check_int('read-star-status', ios, 0)
        call check_int('read-star-value', star_value, 31)
        input_value = -2
        read(input_unit,*,iostat=ios) input_value
        call check_int('read-input-unit-status', ios, 0)
        call check_int('read-input-unit-value', input_value, 32)
        bare_value = -3
        read *, bare_value
        call check_int('read-bare-value', bare_value, 33)
    """, 5,
        "12.5.1 p4 maps READ * and INPUT_UNIT, and a READ without a control list, to the preconnected input unit; controlled stdin supplies three exact integers.",
        [("star-read-internal-file", "        read(*,*,iostat=ios) star_value",
          "        read(internal_star,*,iostat=ios) star_value"),
         ("input-unit-read-internal-file", "        read(input_unit,*,iostat=ios) input_value",
          "        read(internal_input,*,iostat=ios) input_value"),
         ("bare-read-internal-file", "        read *, bare_value",
          "        read(internal_bare,*) bare_value"),
         ("star-read-other-internal", "        read(*,*,iostat=ios) star_value",
          "        read(internal_input,*,iostat=ios) star_value")],
        stdin="31\n32\n33\n")

    c.add_valid("12.5.1", "S12.5.1-006", "preconnected_output_units",
        ["write-asterisk-output-unit", "output-unit-preconnected", "output-unit-output_unit-constant",
         "print-uses-output-unit"], """
        write(*,'(a)') 'STAR-OUTPUT'
        write(output_unit,'(a)') 'NAMED-OUTPUT'
        print '(a)', 'PRINT-OUTPUT'
    """, 0,
        "12.5.1 p4 maps WRITE * , OUTPUT_UNIT, and PRINT to the preconnected formatted output unit; the harness observes exact output records.",
        [("star-output-to-error", "        write(*,'(a)') 'STAR-OUTPUT'",
          "        write(error_unit,'(a)') 'STAR-OUTPUT'"),
         ("named-output-to-error", "        write(output_unit,'(a)') 'NAMED-OUTPUT'",
          "        write(error_unit,'(a)') 'NAMED-OUTPUT'"),
         ("print-output-to-error", "        print '(a)', 'PRINT-OUTPUT'",
          "        write(error_unit,'(a)') 'PRINT-OUTPUT'"),
         ("output-record-text-changed", "        write(output_unit,'(a)') 'NAMED-OUTPUT'",
          "        write(output_unit,'(a)') 'CHANGED-OUTPUT'")],
        stdout="STAR-OUTPUT\nNAMED-OUTPUT\nPRINT-OUTPUT\n", stderr="")

    c.add_valid("12.5.1", "S12.5.1-004", "external_unit_identity_program_units",
        ["external-unit-identity-across-program-units"], """
        integer :: u, other, ios, value
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        open(newunit=other, status='scratch', form='formatted', action='readwrite')
        call writer(u, 64)
        call writer(other, 91)
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('same-unit-across-procedures-status', ios, 0)
        call check_int('same-unit-across-procedures-value', value, 64)
        call check_true('newunit-is-negative', u < 0)
        call check_true('newunit-distinct-from-other', u /= other)
        call check_true('newunit-distinct-from-input', u /= input_unit)
        call check_true('newunit-distinct-from-output', u /= output_unit)
        call check_true('newunit-distinct-from-error', u /= error_unit)
        close(u, status='delete')
        close(other, status='delete')
    """, 7,
        "12.5.1 p2-p3 and 12.5.6.13 allow a negative NEWUNIT value that identifies the same external unit in a called procedure; exact read-back proves identity.",
        [("write-through-other-unit", "        call writer(u, 64)", "        call writer(other, 64)"),
         ("read-back-other-unit", "        read(u,*,iostat=ios) value", "        read(other,*,iostat=ios) value"),
         ("newunit-negative-check-flipped", "        call check_true('newunit-is-negative', u < 0)",
          "        call check_true('newunit-is-negative', u > 0)", "hygiene"),
         ("newunit-distinct-other-check-flipped", "        call check_true('newunit-distinct-from-other', u /= other)",
          "        call check_true('newunit-distinct-from-other', u == other)", "hygiene"),
         ("procedure-value-changed", "        call writer(u, 64)", "        call writer(u, 65)")],
        modules="""
subroutine writer(unit, item)
integer, intent(in) :: unit, item
write(unit,'(i0)') item
end subroutine writer
""")

    c.add_invalid("12.5.1", "C1201", "vector_subscript_internal_file",
        ["internal-file-variable-not-vector-subscript-section"], """
        program p
        implicit none
        character(len=4) :: c(2)
        integer :: idx(2)
        idx = [1, 2]
        write(c(idx),'(a)') 'AB'
        end program p
    """,
        "C1201 requires the R1203 character variable not be an array section with a vector subscript; the control changes only the subscript to c(1:2).",
        6, ["vector subscript", "array section"],
        "write(c(1:2),'(a)') 'AB'")

    c.add_valid("12.5.1", "C1201", "nonvector_section_internal_file_control",
        ["internal-file-variable-not-vector-subscript-section"], """
        character(len=4) :: c(2)
        c = '####'
        write(c(1:2),'(a)') 'AB', 'CD'
        call check_char('nonvector-section-first', c(1), 'AB  ')
        call check_char('nonvector-section-second', c(2), 'CD  ')
    """, 2,
        "C1201 prohibits only vector-subscript array sections; the conforming control changes that one property to a triplet section c(1:2) and observes exact internal-file records.",
        [("triplet-section-reversed", "        write(c(1:2),'(a)') 'AB', 'CD'",
          "        write(c(2:1:-1),'(a)') 'AB', 'CD'")])

    c.add_valid("12.5.2", "S12.5.2-003", "open_and_subsequent_blank_modes",
        ["open-established-mode-values"], """
        integer :: u, ios, initial_value, changed_value
        character(len=4) :: blank_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')
        write(u,'(a)') '1 2'
        rewind u
        initial_value = -1
        read(u,'(i3)',iostat=ios) initial_value
        call check_int('open-established-null-status', ios, 0)
        call check_int('open-established-null-value', initial_value, 12)
        open(unit=u, blank='zero')
        inquire(unit=u, blank=blank_mode)
        call check_char('subsequent-open-blank-mode', blank_mode, 'ZERO')
        rewind u
        changed_value = -2
        read(u,'(i3)',iostat=ios) changed_value
        call check_int('subsequent-open-zero-status', ios, 0)
        call check_int('subsequent-open-zero-value', changed_value, 102)
        close(u, status='delete')
    """, 5,
        "12.5.2 p2 and p4 establish BLANK='NULL' at OPEN and then change it by a subsequent OPEN; 13.8.7 makes '1 2' read as 12 vs 102.",
        [("initial-open-blank-zero", "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')",
          "        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='zero')"),
         ("subsequent-open-blank-null", "        open(unit=u, blank='zero')",
          "        open(unit=u, blank='null')"),
         ("subsequent-inquire-before-open", "        open(unit=u, blank='zero')\n        inquire(unit=u, blank=blank_mode)",
          "        inquire(unit=u, blank=blank_mode)\n        open(unit=u, blank='zero')")])

    c.add_valid("12.5.2", "S12.5.2-004", "implicit_zero_scale_factor",
        ["open-scale-factor-implicit-zero"], """
        integer :: u
        character(len=5) :: external_field, internal_field
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        write(u,'(ss,f5.1)') 1.0
        rewind u
        external_field = '#####'
        read(u,'(a5)') external_field
        call check_char('external-open-implicit-zero-scale', external_field, '  1.0')
        close(u, status='delete')
        internal_field = '#####'
        write(internal_field,'(ss,f5.1)') 2.0
        call check_char('internal-implied-open-zero-scale', internal_field, '  2.0')
    """, 2,
        "12.5.2 p2-p3 gives internal files the initial OPEN-implied modes and makes scale factor implicitly zero; exact F5.1 output of whole-number reals observes zero scale.",
        [("external-scale-factor-one", "        write(u,'(ss,f5.1)') 1.0", "        write(u,'(ss,1p,f5.1)') 1.0"),
         ("internal-scale-factor-one", "        write(internal_field,'(ss,f5.1)') 2.0",
          "        write(internal_field,'(ss,1p,f5.1)') 2.0")])

    c.add_valid("12.5.2", "S12.5.2-006", "temporary_blank_modes",
        ["data-transfer-keyword-temporary-mode", "edit-descriptor-temporary-mode",
         "mode-reset-after-data-transfer"], """
        integer :: u, ios, keyword_value, reset_value, bz_value, bn_value
        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')
        write(u,'(a)') '1 2'
        write(u,'(a)') '1 2'
        write(u,'(a)') '1 21 2'
        rewind u
        keyword_value = -1
        read(u,'(i3)',blank='zero',iostat=ios) keyword_value
        call check_int('keyword-temporary-status', ios, 0)
        call check_int('keyword-temporary-value', keyword_value, 102)
        reset_value = -2
        read(u,'(i3)',iostat=ios) reset_value
        call check_int('mode-reset-status', ios, 0)
        call check_int('mode-reset-value', reset_value, 12)
        bz_value = -7101
        call check_int('pre-read-bz-value', bz_value, -7101)
        bn_value = -7102
        call check_int('pre-read-bn-value', bn_value, -7102)
        read(u,'(bz,i3,bn,i3)',iostat=ios) bz_value, bn_value
        call check_int('edit-descriptor-status', ios, 0)
        call check_int('edit-descriptor-bz-value', bz_value, 102)
        call check_int('edit-descriptor-bn-value', bn_value, 12)
        close(u, status='delete')
    """, 9,
        "12.5.2 p5 says data-transfer keywords and edit descriptors temporarily change modes and then reset; BLANK ZERO/NULL effects distinguish 102 from 12.",
        [("keyword-blank-null", "        read(u,'(i3)',blank='zero',iostat=ios) keyword_value",
          "        read(u,'(i3)',blank='null',iostat=ios) keyword_value"),
         ("reset-read-keeps-zero", "        read(u,'(i3)',iostat=ios) reset_value",
          "        read(u,'(i3)',blank='zero',iostat=ios) reset_value"),
         ("edit-bz-changed-to-bn", "        read(u,'(bz,i3,bn,i3)',iostat=ios) bz_value, bn_value",
          "        read(u,'(bn,i3,bn,i3)',iostat=ios) bz_value, bn_value"),
         ("edit-bn-changed-to-bz", "        read(u,'(bz,i3,bn,i3)',iostat=ios) bz_value, bn_value",
          "        read(u,'(bz,i3,bz,i3)',iostat=ios) bz_value, bn_value"),
         ("pre-read-bz-remove-sentinel-init", "        bz_value = -7101",
          "        ! bz sentinel initializer removed for probe", "sentinel"),
         ("pre-read-bz-expected-sentinel-init", "        bz_value = -7101",
          "        bz_value = 102", "sentinel"),
         ("pre-read-bz-default-sentinel-init", "        bz_value = -7101",
          "        bz_value = 0", "sentinel"),
         ("pre-read-bn-remove-sentinel-init", "        bn_value = -7102",
          "        ! bn sentinel initializer removed for probe", "sentinel"),
         ("pre-read-bn-expected-sentinel-init", "        bn_value = -7102",
          "        bn_value = 12", "sentinel"),
         ("pre-read-bn-default-sentinel-init", "        bn_value = -7102",
          "        bn_value = 0", "sentinel")])

    c.add_valid("12.5.3", "S12.5.3-002", "existing_unit_io_statements",
        ["io-statements-may-refer-existing-units"], """
        integer :: u, ios, value
        logical :: exists, opened
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        inquire(unit=u, exist=exists, opened=opened)
        call check_true('newunit-exists-after-open', exists)
        call check_true('newunit-opened-after-open', opened)
        write(u,'(i0)') 57
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('existing-unit-read-status', ios, 0)
        call check_int('existing-unit-read-value', value, 57)
        close(u, status='delete')
    """, 4,
        "12.5.3 p2 permits I/O statements to refer to units that exist; OPEN(NEWUNIT=) establishes existence, then WRITE/REWIND/READ use the unit.",
        [("write-existing-unit-other-value", "        write(u,'(i0)') 57", "        write(u,'(i0)') 58"),
         ("opened-inquire-before-open", "        open(newunit=u, status='scratch', form='formatted', action='readwrite')\n        inquire(unit=u, exist=exists, opened=opened)",
          "        u = -100\n        inquire(unit=u, exist=exists, opened=opened)\n        open(newunit=u, status='scratch', form='formatted', action='readwrite')")])

    c.add_valid("12.5.4", "S12.5.4-001", "inquire_connection_symmetry",
        ["external-unit-connected-or-not", "connected-unit-refers-external-file", "unit-file-connection-symmetric"], """
        integer :: u, unit_number, file_number
        logical :: unit_opened, file_opened, unit_exists, file_exists, unit_named, file_named
        character(len=20) :: unit_name, file_name
        open(newunit=u, file='iouc_12_5_status.dat', status='replace', form='formatted', action='readwrite')
        unit_opened = .false.
        file_opened = .false.
        unit_exists = .false.
        file_exists = .false.
        unit_named = .false.
        file_named = .false.
        unit_number = 0
        file_number = 0
        unit_name = '####################'
        file_name = '@@@@@@@@@@@@@@@@@@@@'
        inquire(unit=u, opened=unit_opened, exist=unit_exists, number=unit_number, named=unit_named, name=unit_name)
        inquire(file='iouc_12_5_status.dat', opened=file_opened, exist=file_exists, &
                number=file_number, named=file_named, name=file_name)
        call check_true('unit-opened', unit_opened)
        call check_true('file-opened', file_opened)
        call check_true('unit-exists', unit_exists)
        call check_true('file-exists', file_exists)
        call check_int('unit-number', unit_number, u)
        call check_int('file-number', file_number, u)
        call check_true('unit-named', unit_named)
        call check_true('file-named', file_named)
        call check_char('unit-name', unit_name, 'iouc_12_5_status.dat')
        call check_char('file-name', file_name, 'iouc_12_5_status.dat')
        close(u, status='delete')
        unit_opened = .true.
        inquire(unit=u, opened=unit_opened)
        call check_false('unit-not-opened-after-close', unit_opened)
    """, 11,
        "12.5.4 p1 makes connection a symmetric unit-file property; INQUIRE by UNIT and FILE observes the same open named file and NUMBER= unit, then closed state.",
        [("inquire-file-other-name", "        inquire(file='iouc_12_5_status.dat', opened=file_opened, exist=file_exists, &\n                number=file_number, named=file_named, name=file_name)",
          "        inquire(file='iouc_12_5_missing.dat', opened=file_opened, exist=file_exists, &\n                number=file_number, named=file_named, name=file_name)"),
         ("open-different-name", "        open(newunit=u, file='iouc_12_5_status.dat', status='replace', form='formatted', action='readwrite')",
          "        open(newunit=u, file='iouc_12_5_other.dat', status='replace', form='formatted', action='readwrite')"),
         ("open-third-name", "        open(newunit=u, file='iouc_12_5_status.dat', status='replace', form='formatted', action='readwrite')",
          "        open(newunit=u, file='iouc_12_5_third.dat', status='replace', form='formatted', action='readwrite')")])

    c.add_valid("12.5.4", "S12.5.4-006", "file_reconnect_after_close",
        ["means-change-external-unit-status"], """
        integer :: first_unit, second_unit, ios, value
        logical :: opened
        open(newunit=first_unit, file='iouc_12_5_reconnect.dat', status='replace', &
             form='formatted', action='readwrite')
        write(first_unit,'(i0)') 88
        close(first_unit)
        opened = .true.
        inquire(unit=first_unit, opened=opened)
        call check_false('closed-unit-status-changed', opened)
        open(newunit=second_unit, file='iouc_12_5_reconnect.dat', status='old', &
             form='formatted', action='readwrite')
        rewind second_unit
        value = -1
        read(second_unit,*,iostat=ios) value
        call check_int('reconnected-file-status', ios, 0)
        call check_int('reconnected-file-value', value, 88)
        close(second_unit, status='delete')
    """, 3,
        "12.5.4 p4 and p7 provide CLOSE as a means to change unit status and reconnect a disconnected named file; exact read-back after reopening proves the file reconnection.",
        [("skip-close-before-inquire", "        close(first_unit)\n        opened = .true.",
          "        opened = .true."),
         ("reconnect-different-file", "        open(newunit=second_unit, file='iouc_12_5_reconnect.dat', status='old', &\n             form='formatted', action='readwrite')",
          "        open(newunit=second_unit, file='iouc_12_5_other.dat', status='replace', &\n             form='formatted', action='readwrite')"),
         ("reconnected-record-changed", "        write(first_unit,'(i0)') 88", "        write(first_unit,'(i0)') 89")])


    c.add_valid("12.5.1", "R1201", "io_unit_forms",
        ["io-unit-file-unit-number-form", "io-unit-asterisk-form", "io-unit-internal-file-variable-form"], """
        integer :: u, ios, external_value, internal_value
        character(len=8) :: internal_file, alternate_file
        internal_file = '62      '
        alternate_file = '91      '
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        write(u,'(i0)') 61
        rewind u
        external_value = -1
        read(u,*,iostat=ios) external_value
        call check_int('file-unit-number-form-status', ios, 0)
        call check_int('file-unit-number-form-value', external_value, 61)
        internal_value = -2
        read(internal_file,*,iostat=ios) internal_value
        call check_int('internal-file-variable-form-status', ios, 0)
        call check_int('internal-file-variable-form-value', internal_value, 62)
        write(*,'(a)') 'R1201-STAR-OUTPUT'
        close(u, status='delete')
    """, 4,
        "R1201 admits a file-unit-number, an asterisk, or an internal-file-variable; the fixture observes exact effects for all three io-unit forms.",
        [("file-unit-number-form-to-internal", "        read(u,*,iostat=ios) external_value",
          "        read(alternate_file,*,iostat=ios) external_value"),
         ("internal-form-to-external", "        read(internal_file,*,iostat=ios) internal_value",
          "        read(u,*,iostat=ios) internal_value"),
         ("asterisk-form-to-error", "        write(*,'(a)') 'R1201-STAR-OUTPUT'",
          "        write(error_unit,'(a)') 'R1201-STAR-OUTPUT'")],
        stdout="R1201-STAR-OUTPUT\n", stderr="")

    c.add_valid("12.5.1", "R1202", "scalar_integer_file_unit",
        ["file-unit-number-scalar-int-expr"], """
        integer :: u, other, unit_expr, ios, value
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        open(newunit=other, status='scratch', form='formatted', action='readwrite')
        write(u,'(i0)') 71
        write(other,'(i0)') 72
        rewind u
        rewind other
        unit_expr = u + 0
        value = -1
        read(unit_expr,*,iostat=ios) value
        call check_int('scalar-int-expr-status', ios, 0)
        call check_int('scalar-int-expr-value', value, 71)
        close(u, status='delete')
        close(other, status='delete')
    """, 2,
        "R1202 makes a file-unit-number a scalar integer expression; u+0 selects the same unit and reads the exact record.",
        [("scalar-expression-selects-other", "        unit_expr = u + 0", "        unit_expr = other"),
         ("scalar-expression-record-changed", "        write(u,'(i0)') 71", "        write(u,'(i0)') 73")])

    c.add_valid("12.5.1", "R1203", "character_internal_file_variable",
        ["internal-file-variable-char-variable"], """
        integer :: ios, value
        character(len=8) :: internal_file, other_file
        internal_file = '81      '
        other_file = '91      '
        value = -1
        read(internal_file,*,iostat=ios) value
        call check_int('char-variable-internal-status', ios, 0)
        call check_int('char-variable-internal-value', value, 81)
        internal_file = '########'
        write(internal_file,'(i0)') 82
        call check_char('char-variable-write-target', internal_file, '82      ')
    """, 3,
        "R1203 requires an internal-file-variable to be a character variable; exact internal READ and WRITE effects prove that variable is the file.",
        [("read-other-character-variable", "        read(internal_file,*,iostat=ios) value",
          "        read(other_file,*,iostat=ios) value"),
         ("write-other-character-variable", "        write(internal_file,'(i0)') 82",
          "        write(other_file,'(i0)') 82")])

    c.add_valid("12.5.1", "C1202", "default_character_internal_file",
        ["internal-file-variable-permitted-character-kind"], """
        integer :: ios, value
        character(kind=kind('a'), len=8) :: internal_file, other_file
        internal_file = '84      '
        other_file = '94      '
        value = -1
        read(internal_file,*,iostat=ios) value
        call check_int('default-character-kind-status', ios, 0)
        call check_int('default-character-kind-value', value, 84)
    """, 2,
        "C1202 permits default character internal-file variables; kind('a') is default character and exact internal READ observes it.",
        [("default-character-read-other", "        read(internal_file,*,iostat=ios) value",
          "        read(other_file,*,iostat=ios) value")])

    c.add_valid("12.5.1", "S12.5.1-002", "external_internal_classification",
        ["unit-external-or-internal-classification", "external-unit-designates-external-file",
         "internal-unit-designates-internal-file"], """
        integer :: u, ios, external_value, internal_value
        character(len=8) :: internal_file, other_file
        internal_file = '92      '
        other_file = '93      '
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        write(u,'(i0)') 91
        rewind u
        external_value = -1
        read(u,*,iostat=ios) external_value
        call check_int('external-unit-status', ios, 0)
        call check_int('external-unit-value', external_value, 91)
        internal_value = -2
        read(internal_file,*,iostat=ios) internal_value
        call check_int('internal-unit-status', ios, 0)
        call check_int('internal-unit-value', internal_value, 92)
        close(u, status='delete')
    """, 4,
        "12.5.1 p2 classifies units as external or internal; a NEWUNIT external file and a character internal file produce distinct exact records.",
        [("external-designates-internal", "        read(u,*,iostat=ios) external_value",
          "        read(other_file,*,iostat=ios) external_value"),
         ("internal-designates-external", "        read(internal_file,*,iostat=ios) internal_value",
          "        read(u,*,iostat=ios) internal_value"),
         ("external-record-changed", "        write(u,'(i0)') 91", "        write(u,'(i0)') 94")])

    c.add_valid("12.5.1", "S12.5.1-003", "newunit_valid_file_unit",
        ["file-unit-number-valid-unit"], """
        integer :: u, other, ios, value
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        open(newunit=other, status='scratch', form='formatted', action='readwrite')
        call check_true('newunit-distinct-other', u /= other)
        call check_true('newunit-distinct-input', u /= input_unit)
        call check_true('newunit-distinct-output', u /= output_unit)
        call check_true('newunit-distinct-error', u /= error_unit)
        write(u,'(i0)') 101
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('newunit-valid-status', ios, 0)
        call check_int('newunit-valid-value', value, 101)
        close(u, status='delete')
        close(other, status='delete')
    """, 6,
        "12.5.1 p2 permits a NEWUNIT value as a valid file-unit-number; the value is distinct from the other opened unit and supports exact I/O.",
        [("newunit-record-other-unit", "        write(u,'(i0)') 101", "        write(other,'(i0)') 101"),
         ("newunit-read-other-unit", "        read(u,*,iostat=ios) value", "        read(other,*,iostat=ios) value")])

    c.add_valid("12.5.2", "S12.5.2-003", "internal_initial_zero_scale",
        ["internal-preconnected-initial-mode-values"], """
        character(len=5) :: internal_field
        internal_field = '#####'
        write(internal_field,'(ss,f5.1)') 3.0
        call check_char('internal-initial-zero-scale', internal_field, '  3.0')
    """, 1,
        "12.5.2 p2 gives an internal file the modes implied by an initial OPEN without keywords; p3 makes its scale factor zero, observed by exact F5.1 output.",
        [("internal-initial-scale-one", "        write(internal_field,'(ss,f5.1)') 3.0",
          "        write(internal_field,'(ss,1p,f5.1)') 3.0")])

    c.add_valid("12.5.2", "S12.5.2-005", "subsequent_open_blank_change",
        ["subsequent-open-can-change-external-modes"], """
        integer :: u, ios, changed_value
        character(len=4) :: blank_mode
        open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')
        write(u,'(a)') '1 2'
        open(unit=u, blank='zero')
        inquire(unit=u, blank=blank_mode)
        call check_char('subsequent-open-changed-blank', blank_mode, 'ZERO')
        rewind u
        changed_value = -1
        read(u,'(i3)',iostat=ios) changed_value
        call check_int('subsequent-open-read-status', ios, 0)
        call check_int('subsequent-open-read-value', changed_value, 102)
        close(u, status='delete')
    """, 3,
        "12.5.2 p4 permits a subsequent OPEN to change an external connection mode; BLANK changes to ZERO and makes '1 2' read as 102.",
        [("subsequent-open-keeps-null", "        open(unit=u, blank='zero')", "        open(unit=u, blank='null')"),
         ("subsequent-open-after-read", "        open(unit=u, blank='zero')\n        inquire(unit=u, blank=blank_mode)",
          "        inquire(unit=u, blank=blank_mode)\n        open(unit=u, blank='zero')")])

    c.add_valid("12.5.4", "S12.5.4-002", "connection_by_open_and_preconnection",
        ["external-unit-connection-by-preconnection", "external-unit-connection-by-open"], """
        integer :: u
        logical :: opened
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        opened = .false.
        inquire(unit=u, opened=opened)
        call check_true('connection-by-open-opened', opened)
        write(output_unit,'(a)') 'PRECONNECTED-OUTPUT-CONNECTION'
        close(u, status='delete')
    """, 1,
        "12.5.4 p1 permits connection by OPEN and by preconnection; INQUIRE observes the OPEN connection and OUTPUT_UNIT writes without OPEN.",
        [("open-connection-inquire-before-open", "        open(newunit=u, status='scratch', form='formatted', action='readwrite')\n        opened = .false.",
          "        u = -100\n        opened = .false."),
         ("preconnected-output-to-error", "        write(output_unit,'(a)') 'PRECONNECTED-OUTPUT-CONNECTION'",
          "        write(error_unit,'(a)') 'PRECONNECTED-OUTPUT-CONNECTION'")],
        stdout="PRECONNECTED-OUTPUT-CONNECTION\n", stderr="")

    c.add_valid("12.5.4", "S12.5.4-003", "connected_unit_file_effect",
        ["io-statements-use-or-affect-connected-file"], """
        integer :: u, ios, value
        open(newunit=u, status='scratch', form='formatted', action='readwrite')
        write(u,'(i0)') 111
        rewind u
        value = -1
        read(u,*,iostat=ios) value
        call check_int('connected-unit-read-status', ios, 0)
        call check_int('connected-unit-read-value', value, 111)
        close(u, status='delete')
    """, 2,
        "12.5.4 p2 requires ordinary I/O to refer to a connected unit and affect its file; exact write/read through an OPENed unit observes that effect.",
        [("connected-file-record-changed", "        write(u,'(i0)') 111", "        write(u,'(i0)') 112"),
         ("connected-file-record-changed-again", "        write(u,'(i0)') 111", "        write(u,'(i0)') 113")])

    c.add_valid("12.5.4", "S12.5.4-011", "reconnect_file_after_close",
        ["file-reconnect-same-or-different-unit-after-close"], """
        integer :: first_unit, second_unit, ios, value
        open(newunit=first_unit, file='iouc_12_5_file_reuse.dat', status='replace', &
             form='formatted', action='readwrite')
        write(first_unit,'(i0)') 121
        close(first_unit)
        open(newunit=second_unit, file='iouc_12_5_file_reuse.dat', status='old', &
             form='formatted', action='readwrite')
        rewind second_unit
        value = -1
        read(second_unit,*,iostat=ios) value
        call check_int('file-reconnect-status', ios, 0)
        call check_int('file-reconnect-value', value, 121)
        close(second_unit, status='delete')
    """, 2,
        "12.5.4 p7 permits a disconnected external file to be connected again to a different unit; exact read-back after CLOSE/OPEN observes it.",
        [("file-reconnect-other-name", "        open(newunit=second_unit, file='iouc_12_5_file_reuse.dat', status='old', &\n             form='formatted', action='readwrite')",
          "        open(newunit=second_unit, file='iouc_12_5_file_other.dat', status='replace', &\n             form='formatted', action='readwrite')"),
         ("file-reconnect-record-changed", "        write(first_unit,'(i0)') 121", "        write(first_unit,'(i0)') 122")])

    c.add_valid("12.5.4", "S12.5.4-012", "internal_unit_designated_file",
        ["internal-unit-always-connected-to-designated-internal-file"], """
        integer :: ios, value
        character(len=8) :: internal_file, other_file
        internal_file = '131     '
        other_file = '141     '
        value = -1
        read(internal_file,*,iostat=ios) value
        call check_int('internal-unit-connected-status', ios, 0)
        call check_int('internal-unit-connected-value', value, 131)
        internal_file = '########'
        write(internal_file,'(i0)') 132
        call check_char('internal-unit-write-designated', internal_file, '132     ')
    """, 3,
        "12.5.4 p8 says an internal unit is always connected to its designating internal file; READ and WRITE affect the named character variable exactly.",
        [("internal-connected-read-other", "        read(internal_file,*,iostat=ios) value",
          "        read(other_file,*,iostat=ios) value"),
         ("internal-connected-write-other", "        write(internal_file,'(i0)') 132",
          "        write(other_file,'(i0)') 132")])

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
            diag_count = sum(1 for spec in selected if spec["kind"] == "invalid")
            run_count = len(selected) - diag_count
            text = ("I/O units-connection fixture implementation: "
                    f"{run_count} valid run-phase program(s) and {diag_count} diagnostic program(s) cover {labels}. "
                    "Runtime oracles use scratch or run-directory files, controlled stdin/stdout/stderr, "
                    "INQUIRE properties, exact integer/character/logical values, and IOSTAT zero only. "
                    "No processor-dependent ordinary unit number, physical device, IOMSG text, or numeric "
                    "nonzero status is asserted.")
            requirement["oracle"] = owned_paragraph(requirement["oracle"],
                                                     "I/O units-connection fixture implementation:", text)
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
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - I/O units and connection fixtures\n\n"
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
    text += "## I/O units and connection fixture derivations\n\n"
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
        raise SystemExit("stale io_units_connection_12_5 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def expected_stream(spec, key):
    value = spec.get(key)
    return "" if value is None else value


def run_mutations(compiler, std, keep=False):
    files, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / ".mutation_io_units_connection_12_5" / digest
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
                stdin_data = spec["stdin"] if spec.get("stdin") is not None else None
                ran = subprocess.run([str(exe)], cwd=work, input=stdin_data, text=True,
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
