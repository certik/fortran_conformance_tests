#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.92 through 16.9.94."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_k"
SECTIONS = ("16.9.92", "16.9.93", "16.9.94")
CATALOGUES = {
    "16.9.92": "doc/catalogues/get_command_16_9_92.json",
    "16.9.93": "doc/catalogues/get_command_argument_16_9_93.json",
    "16.9.94": "doc/catalogues/get_environment_variable_16_9_94.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9 K FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9 K FIXTURES -->"
COMMAND_PROFILE = "command-arguments-supported"

SELECTED = {
    "S16.9.92-002": ("effect", (
        "GET_COMMAND-command-assigned-entire-command-or-blanks",
        "GET_COMMAND-length-significant-or-zero",
        "GET_COMMAND-length-independent-of-command-buffer",
    )),
    "S16.9.92-004": ("effect", (
        "GET_COMMAND-status-nonnegative-without-command",
        "GET_COMMAND-status-minus-one-for-command-truncation",
        "GET_COMMAND-status-zero-for-success",
    )),
    "S16.9.93-001": ("positive-control", (
        "GET_COMMAND_ARGUMENT-NUMBER-integer-scalar",
        "GET_COMMAND_ARGUMENT-VALUE-default-character-scalar",
        "GET_COMMAND_ARGUMENT-LENGTH-integer-scalar-range",
        "GET_COMMAND_ARGUMENT-STATUS-integer-scalar-range",
        "GET_COMMAND_ARGUMENT-argument-intents",
    )),
    "S16.9.93-002": ("effect", ("GET_COMMAND_ARGUMENT-zero-always-exists",)),
    "S16.9.93-003": ("effect", ("GET_COMMAND_ARGUMENT-positive-arguments-consecutive",)),
    "S16.9.93-004": ("effect", (
        "GET_COMMAND_ARGUMENT-absent-value-all-blanks",
        "GET_COMMAND_ARGUMENT-absent-length-zero",
        "GET_COMMAND_ARGUMENT-length-independent-of-value-buffer",
        "GET_COMMAND_ARGUMENT-existing-value-processor-supplied",
    )),
    "S16.9.93-006": ("effect", (
        "GET_COMMAND_ARGUMENT-status-positive-for-negative-number",
        "GET_COMMAND_ARGUMENT-status-minus-one-for-value-truncation",
        "GET_COMMAND_ARGUMENT-status-zero-for-nonfailure-nontruncation",
    )),
}

ORACLE_PREFIXES = {rule: f"{rule} intrinsics_16_9_k runtime fixture: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} intrinsics_16_9_k fixture boundaries: " for rule in SELECTED}
ORACLES = {
    "S16.9.92-002": ORACLE_PREFIXES["S16.9.92-002"] +
        "With the command-argument profile, GET_COMMAND is expected to retrieve the invocation command: STATUS is zero, the assigned COMMAND text has LEN_TRIM(COMMAND) no greater than LENGTH, characters beyond LENGTH are blank-filled when the buffer is longer, and the same LENGTH is reported when COMMAND is absent or too short.",
    "S16.9.92-004": ORACLE_PREFIXES["S16.9.92-004"] +
        "With the same profiled launch, VALUE-absent and full-buffer GET_COMMAND calls observe STATUS zero, while a deliberately too-short COMMAND buffer observes STATUS -1; exact command spelling and positive failure status values are not asserted.",
    "S16.9.93-001": ORACLE_PREFIXES["S16.9.93-001"] +
        "Generated positive controls call GET_COMMAND_ARGUMENT with conforming scalar NUMBER, VALUE, LENGTH, and STATUS actuals; separate sentinel assertions prove the OUT actuals are defined by the call without promoting unnumbered restrictions to diagnostic obligations.",
    "S16.9.93-002": ORACLE_PREFIXES["S16.9.93-002"] +
        "The command-argument-support profile excludes command retrieval failure; a VALUE-absent call for NUMBER 0 then observes STATUS zero, which is the nontruncating existing-argument branch without asserting command-name spelling.",
    "S16.9.93-003": ORACLE_PREFIXES["S16.9.93-003"] +
        "The runner supplies one argument, so COMMAND_ARGUMENT_COUNT is positive; GET_COMMAND_ARGUMENT(1) observes the sole positive argument while count+1 observes the required absent-argument control.",
    "S16.9.93-004": ORACLE_PREFIXES["S16.9.93-004"] +
        "For NUMBER greater than COMMAND_ARGUMENT_COUNT, VALUE is all blanks and LENGTH is zero; the same zero length with VALUE absent and present shows buffer-independent LENGTH for the absent argument, and the one supplied argument gives an exact single-argument VALUE oracle.",
    "S16.9.93-006": ORACLE_PREFIXES["S16.9.93-006"] +
        "With a one-argument launch, NUMBER=-1 observes a positive STATUS, a long VALUE observes STATUS zero, and a shorter VALUE observes STATUS -1 while LENGTH remains the significant argument length; exact command-name spelling and positive failure status numbers are not asserted.",
}
LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] +
    "Only the listed portable facets are discharged. The fixture runner supports command-line arguments through fixture.json run.arguments but does not pass a controlled environment, so absent-environment-variable facets remain pending. ERRMSG dummy arguments are left pending because the reference compiler rejects the Fortran 2023 ERRMSG forms in this worktree. Frozen LFortran failures on GET_COMMAND and GET_COMMAND_ARGUMENT(-1) are shipped as genuine defects, not treated as unsupported coverage."
    for rule in SELECTED
}
SOURCE_ONLY_PATTERNS = [
    ("Source accounting only. This packet creates no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.",
     "Original source accounting created no Fortran fixture, compiler invocation, execution evidence, evidence link, fixture approval, oracle approval, or coverage claim; this intrinsics_16_9_k generator supplies selected profiled runtime fixtures and mutation plans without granting universal coverage."),
    ("Source registration only.",
     "Original source registration only; selected GET_COMMAND and GET_COMMAND_ARGUMENT facets now have bounded runtime fixtures and mutation plans."),
]

HELPERS = """contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require

  logical function all_blank(text)
    character(len=*), intent(in) :: text
    integer :: i
    all_blank = .true.
    do i = 1, len(text)
      if (text(i:i) /= ' ') all_blank = .false.
    end do
  end function all_blank

  logical function blank_after(text, used)
    character(len=*), intent(in) :: text
    integer, intent(in) :: used
    if (used < 0) then
      blank_after = .false.
    else if (used >= len(text)) then
      blank_after = .true.
    else
      blank_after = all_blank(text(used + 1:))
    end if
  end function blank_after
end program {program}
"""


def identifier(variant, rule):
    return rule.replace('.', '_').replace('-', '_') + f"_valid__{TOPIC}_{variant}"


def mut(mid, facet, expected, replacement):
    return {"id": mid, "facet": facet, "kind": "source", "category": "feature",
            "replacements": [{"expected": expected, "replacement": replacement}]}


def multi_mut(mid, facet, replacements):
    return {"id": mid, "facet": facet, "kind": "source", "category": "feature",
            "replacements": [{"expected": old, "replacement": new} for old, new in replacements]}


def header(rule, facets, program):
    lines = [f"! rule: {rule}"] + [f"! covers: {facet}" for facet in facets]
    return "\n".join(lines) + f"\nprogram {program}\n  implicit none\n"


def finish(program, completion, checks):
    return f"  if (checks /= {checks}) error stop\n  write(*,'(a)') '{completion.rstrip()}'\n" + HELPERS.format(program=program)


def make_source(variant, rule, facets, declarations, body):
    program = "i169k_" + variant
    completion = "INTRINSICS 16.9 K " + variant.upper().replace("_", " ") + " OK\n"
    checks = len(facets)
    source = header(rule, facets, program) + declarations + "  checks = 0\n" + body + finish(program, completion, checks)
    return source, completion


def build_case(variant, rule, facets, declarations, body, mutations, arguments=(), profiles=(COMMAND_PROFILE,)):
    evidence = SELECTED[rule][0]
    source, completion = make_source(variant, rule, facets, declarations, body)
    raw = source.encode("ascii")
    materialized = []
    for m in mutations:
        mutant = raw
        spans = []
        for item in m["replacements"]:
            old = item["expected"].encode("ascii")
            count = mutant.count(old)
            if count != 1:
                raise ValueError(f"{variant}:{m['id']} expected unique {item['expected']!r}, found {count}")
            start = mutant.index(old)
            end = start + len(old)
            spans.append([start, end, item["expected"], item["replacement"]])
            mutant = mutant[:start] + item["replacement"].encode("ascii") + mutant[end:]
        row = dict(m)
        row["spans"] = spans
        row["mutant_sha256"] = sha(mutant)
        materialized.append(row)
    covered = {m["facet"] for m in materialized}
    missing = set(facets) - covered
    if missing:
        raise ValueError(f"{variant} lacks feature mutations for {sorted(missing)}")
    return dict(id=identifier(variant, rule), variant=variant, rule=rule, facets=list(facets), evidence=evidence,
                source=source, source_sha256=sha(raw), completion=completion, mutations=materialized,
                arguments=list(arguments), profiles=list(profiles))


def cases():
    out = []
    out.append(build_case(
        "get_command_effects", "S16.9.92-002", SELECTED["S16.9.92-002"][1],
        "  integer :: checks\n  integer :: length_full, status_full, length_absent, status_absent\n"
        "  integer :: length_short, status_short\n  character(len=1024) :: command_full\n"
        "  character(len=2) :: command_short\n",
        "  command_full = repeat('#', len(command_full)); length_full = -7777; status_full = -7777\n"
        "  call get_command(command_full, length_full, status_full)\n"
        "  call require('GET_COMMAND assigns command with bounded trimmed length and blank fill', &\n"
        "       status_full == 0 .and. len_trim(command_full) <= length_full .and. &\n"
        "       blank_after(command_full, length_full), checks)\n"
        "  length_absent = -7777; status_absent = -7777\n"
        "  call get_command(length=length_absent, status=status_absent)\n"
        "  call require('GET_COMMAND reports significant length for successful retrieval', &\n"
        "       status_absent == 0 .and. length_absent >= 0, checks)\n"
        "  command_short = '##'; length_short = -7777; status_short = -7777\n"
        "  call get_command(command_short, length_short, status_short)\n"
        "  call require('GET_COMMAND LENGTH ignores COMMAND buffer truncation', &\n"
        "       status_short == -1 .and. length_short == length_absent, checks)\n",
        [mut("command-to-absent-argument", "GET_COMMAND-command-assigned-entire-command-or-blanks",
             "call get_command(command_full, length_full, status_full)",
             "call get_command_argument(command_argument_count() + 1, command_full, length_full, status_full)"),
         mut("length-to-absent-argument", "GET_COMMAND-length-significant-or-zero",
             "call get_command(length=length_absent, status=status_absent)",
             "call get_command_argument(command_argument_count() + 1, length=length_absent, status=status_absent)"),
         mut("short-command-to-argument", "GET_COMMAND-length-independent-of-command-buffer",
             "call get_command(command_short, length_short, status_short)",
             "call get_command_argument(1, command_short, length_short, status_short)")],
        arguments=("omega",)))
    out.append(build_case(
        "get_command_status", "S16.9.92-004", SELECTED["S16.9.92-004"][1],
        "  integer :: checks\n  integer :: length_absent, status_absent, length_short, status_short\n"
        "  integer :: length_full, status_full\n  character(len=2) :: command_short\n"
        "  character(len=1024) :: command_full\n",
        "  length_absent = -7777; status_absent = -7777\n"
        "  call get_command(length=length_absent, status=status_absent)\n"
        "  call require('GET_COMMAND without COMMAND reports nonfailure status', status_absent == 0, checks)\n"
        "  command_short = '##'; length_short = -7777; status_short = -7777\n"
        "  call get_command(command_short, length_short, status_short)\n"
        "  call require('GET_COMMAND short COMMAND gives STATUS minus one', &\n"
        "       status_short == -1 .and. length_short >= 0, checks)\n"
        "  command_full = repeat('#', len(command_full)); length_full = -7777; status_full = -7777\n"
        "  call get_command(command_full, length_full, status_full)\n"
        "  call require('GET_COMMAND successful full buffer gives STATUS zero', &\n"
        "       status_full == 0, checks)\n",
        [mut("status-without-command-to-absent-argument", "GET_COMMAND-status-nonnegative-without-command",
             "call get_command(length=length_absent, status=status_absent)",
             "call get_command_argument(command_argument_count() + 1, length=length_absent, status=status_absent)"),
         mut("short-buffer-to-full-buffer", "GET_COMMAND-status-minus-one-for-command-truncation",
             "character(len=2) :: command_short", "character(len=1024) :: command_short"),
         mut("success-status-to-absent-argument", "GET_COMMAND-status-zero-for-success",
             "call get_command(command_full, length_full, status_full)",
             "call get_command_argument(command_argument_count() + 1, command_full, length_full, status_full)")],
        arguments=("omega",)))
    out.append(build_case(
        "command_argument_controls", "S16.9.93-001", SELECTED["S16.9.93-001"][1],
        "  integer :: checks\n  integer :: n, length_number, length_only, status_number, status_only\n"
        "  character(len=8) :: value_number, value_only, value_intent\n  integer :: length_intent, status_intent\n",
        "  n = command_argument_count()\n"
        "  value_number = '########'; length_number = -7777; status_number = -7777\n"
        "  call get_command_argument(1, value_number, length_number, status_number)\n"
        "  call require('NUMBER integer scalar actual selects supplied argument', &\n"
        "       status_number == 0 .and. length_number == 5 .and. value_number(1:5) == 'omega', checks)\n"
        "  value_only = '########'\n"
        "  call get_command_argument(1, value_only)\n"
        "  call require('VALUE default character scalar actual is assigned', &\n"
        "       value_only(1:5) == 'omega' .and. all_blank(value_only(6:)), checks)\n"
        "  length_only = -7777\n"
        "  call get_command_argument(1, length=length_only)\n"
        "  call require('LENGTH integer scalar actual is assigned', length_only == 5, checks)\n"
        "  status_only = -7777\n"
        "  call get_command_argument(1, status=status_only)\n"
        "  call require('STATUS integer scalar actual is assigned', status_only == 0, checks)\n"
        "  value_intent = '########'; length_intent = -7777; status_intent = -7777\n"
        "  call get_command_argument(1, value_intent, length_intent, status_intent)\n"
        "  call require('OUT arguments are defined by GET_COMMAND_ARGUMENT', &\n"
        "       value_intent(1:5) == 'omega' .and. length_intent == 5 .and. status_intent == 0, checks)\n",
        [mut("number-to-absent", "GET_COMMAND_ARGUMENT-NUMBER-integer-scalar",
             "call get_command_argument(1, value_number, length_number, status_number)",
             "call get_command_argument(n + 1, value_number, length_number, status_number)"),
         mut("omit-value", "GET_COMMAND_ARGUMENT-VALUE-default-character-scalar",
             "call get_command_argument(1, value_only)",
             "call get_command_argument(1)"),
         mut("omit-length", "GET_COMMAND_ARGUMENT-LENGTH-integer-scalar-range",
             "call get_command_argument(1, length=length_only)",
             "call get_command_argument(1)"),
         mut("omit-status", "GET_COMMAND_ARGUMENT-STATUS-integer-scalar-range",
             "call get_command_argument(1, status=status_only)",
             "call get_command_argument(1)"),
         mut("remove-intent-call", "GET_COMMAND_ARGUMENT-argument-intents",
             "call get_command_argument(1, value_intent, length_intent, status_intent)",
             "! call get_command_argument(1, value_intent, length_intent, status_intent)")],
        arguments=("omega",)))
    out.append(build_case(
        "command_argument_values", "S16.9.93-004", SELECTED["S16.9.93-004"][1],
        "  integer :: checks\n  integer :: n, length_absent, length_no_value, length_with_value\n"
        "  character(len=8) :: absent_value, existing_value, short_absent\n",
        "  n = command_argument_count()\n"
        "  absent_value = '########'\n"
        "  call get_command_argument(n + 1, value=absent_value)\n"
        "  call require('absent command argument assigns VALUE blanks', all_blank(absent_value), checks)\n"
        "  length_absent = -7777\n"
        "  call get_command_argument(n + 1, length=length_absent)\n"
        "  call require('absent command argument assigns LENGTH zero', length_absent == 0, checks)\n"
        "  length_no_value = -7777; length_with_value = -8888; short_absent = '########'\n"
        "  call get_command_argument(n + 1, length=length_no_value)\n"
        "  call get_command_argument(n + 1, value=short_absent, length=length_with_value)\n"
        "  call require('absent LENGTH ignores VALUE buffer size', &\n"
        "       length_no_value == 0 .and. length_with_value == 0 .and. all_blank(short_absent), checks)\n"
        "  existing_value = '########'\n"
        "  call get_command_argument(1, value=existing_value)\n"
        "  call require('sole supplied command argument value is observed', &\n"
        "       existing_value(1:5) == 'omega' .and. all_blank(existing_value(6:)), checks)\n",
        [mut("absent-value-number-to-one", "GET_COMMAND_ARGUMENT-absent-value-all-blanks",
             "call get_command_argument(n + 1, value=absent_value)",
             "call get_command_argument(1, value=absent_value)"),
         mut("absent-length-number-to-one", "GET_COMMAND_ARGUMENT-absent-length-zero",
             "call get_command_argument(n + 1, length=length_absent)",
             "call get_command_argument(1, length=length_absent)"),
         mut("buffered-absent-number-to-one", "GET_COMMAND_ARGUMENT-length-independent-of-value-buffer",
             "call get_command_argument(n + 1, value=short_absent, length=length_with_value)",
             "call get_command_argument(1, value=short_absent, length=length_with_value)"),
         mut("existing-number-to-absent", "GET_COMMAND_ARGUMENT-existing-value-processor-supplied",
             "call get_command_argument(1, value=existing_value)",
             "call get_command_argument(n + 1, value=existing_value)")],
        arguments=("omega",)))
    out.append(build_case(
        "command_argument_numbering", "S16.9.93-003", SELECTED["S16.9.93-003"][1],
        "  integer :: checks\n  integer :: n, status_first, status_after\n  character(len=8) :: first, after\n",
        "  n = command_argument_count()\n"
        "  first = '########'; status_first = -7777\n"
        "  call get_command_argument(1, value=first, status=status_first)\n"
        "  after = '########'; status_after = -7777\n"
        "  call get_command_argument(n + 1, value=after, status=status_after)\n"
        "  call require('positive command arguments are consecutive from one through count', &\n"
        "       n == 1 .and. status_first == 0 .and. first(1:5) == 'omega' .and. &\n"
        "       status_after > 0 .and. all_blank(after), checks)\n",
        [mut("first-positive-to-absent", "GET_COMMAND_ARGUMENT-positive-arguments-consecutive",
             "call get_command_argument(1, value=first, status=status_first)",
             "call get_command_argument(n + 1, value=first, status=status_first)")],
        arguments=("omega",)))
    out.append(build_case(
        "command_argument_zero", "S16.9.93-002", SELECTED["S16.9.93-002"][1],
        "  integer :: checks\n  integer :: n, length_zero, status_zero\n",
        "  n = command_argument_count()\n"
        "  length_zero = -7777; status_zero = -7777\n"
        "  call get_command_argument(0, length=length_zero, status=status_zero)\n"
        "  call require('command argument zero exists without spelling oracle', &\n"
        "       status_zero == 0 .and. length_zero >= 0, checks)\n",
        [mut("zero-to-after-count", "GET_COMMAND_ARGUMENT-zero-always-exists",
             "call get_command_argument(0, length=length_zero, status=status_zero)",
             "call get_command_argument(n + 1, length=length_zero, status=status_zero)")],
        arguments=("omega",)))
    out.append(build_case(
        "command_argument_status", "S16.9.93-006", SELECTED["S16.9.93-006"][1],
        "  integer :: checks\n  integer :: status_negative, length_long, status_long, length_short, status_short\n"
        "  character(len=8) :: long_value\n  character(len=2) :: short_value\n",
        "  status_negative = -7777\n"
        "  call get_command_argument(-1, status=status_negative)\n"
        "  call require('negative NUMBER gives positive STATUS', status_negative > 0, checks)\n"
        "  long_value = '########'; length_long = -7777; status_long = -7777\n"
        "  call get_command_argument(1, value=long_value, length=length_long, status=status_long)\n"
        "  call require('nonfailure nontruncating argument has STATUS zero', &\n"
        "       status_long == 0 .and. length_long == 5 .and. long_value(1:5) == 'omega', checks)\n"
        "  short_value = '##'; length_short = -7777; status_short = -7777\n"
        "  call get_command_argument(1, value=short_value, length=length_short, status=status_short)\n"
        "  call require('short VALUE argument gives STATUS minus one', &\n"
        "       status_short == -1 .and. length_short == 5 .and. short_value == 'om', checks)\n",
        [mut("negative-number-to-present", "GET_COMMAND_ARGUMENT-status-positive-for-negative-number",
             "call get_command_argument(-1, status=status_negative)",
             "call get_command_argument(1, status=status_negative)"),
         mut("status-zero-to-short", "GET_COMMAND_ARGUMENT-status-zero-for-nonfailure-nontruncation",
             "call get_command_argument(1, value=long_value, length=length_long, status=status_long)",
             "call get_command_argument(command_argument_count() + 1, value=long_value, length=length_long, status=status_long)"),
         mut("status-minus-one-to-long", "GET_COMMAND_ARGUMENT-status-minus-one-for-value-truncation",
             "character(len=2) :: short_value", "character(len=8) :: short_value")],
        arguments=("omega",)))
    return out


def source_specs():
    return {case["id"]: case for case in cases()}


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("complete parent source no longer matches fingerprint")
    mutated = raw
    for start, end, expected, replacement in reversed(mutation["spans"]):
        if raw[start:end].decode("ascii") != expected:
            raise ValueError("mutation span lost complete-parent binding")
        mutated = mutated[:start] + replacement.encode("ascii") + mutated[end:]
    return mutated


def profile_sources():
    return {
        "tests/profiles/command_arguments_supported.f90": b"""program command_arguments_supported
  implicit none
  integer :: length, status
  length = -7777
  status = -7777
  call get_command_argument(0, length=length, status=status)
  if (status > 0) stop 77
  if (status /= 0 .or. length < 0) error stop
end program command_arguments_supported
""",
    }


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (TOPIC + "_" + spec["variant"])
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", profiles=spec["profiles"], files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        if spec.get("arguments"):
            manifest["run"] = {"arguments": spec["arguments"]}
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    for rel, raw in profile_sources().items():
        files[Path(root) / rel] = raw
    return files, specs


def soften_source_only(text):
    for old, new in SOURCE_ONLY_PATTERNS:
        text = text.replace(old, new)
    return text


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, (_, facets) in SELECTED.items():
        if rule not in by_rule:
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner.setdefault("pending", {})
        owner["oracle"] = owned_paragraph(soften_source_only(owner.get("oracle", "")), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(soften_source_only(owner.get("oracle_limitation", "")), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    selected_here = [rule for rule in SELECTED if rule in {row["id"] for row in catalogue["requirements"]}]
    facet_count = sum(len(SELECTED[rule][1]) for rule in selected_here)
    if selected_here:
        summary = (SUMMARY_BEGIN + "\n"
                   "## Intrinsics 16.9 K profiled runtime observations\n\n"
                   f"The `intrinsics_16_9_k` generator supplies {len(selected_here)} requirement bindings "
                   f"covering {facet_count} portable facets in this section. The runner schema supports "
                   "`run.arguments` but no environment map, so GET_ENVIRONMENT_VARIABLE absent-name facets remain "
                   "pending. ERRMSG forms remain pending; frozen LFortran GET_COMMAND/negative-NUMBER failures are "
                   "kept as defect fixtures.\n"
                   + SUMMARY_END)
        if SUMMARY_BEGIN in before or SUMMARY_END in before:
            leading, owned = before.split(SUMMARY_BEGIN)
            _, trailing = owned.split(SUMMARY_END)
            before = leading + summary + trailing
        else:
            before = before.rstrip() + "\n\n" + summary + "\n\n"
    elif SUMMARY_BEGIN in before or SUMMARY_END in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading.rstrip() + "\n\n" + trailing.lstrip()
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues, updated_views = {}, {}
    for section, path in CATALOGUES.items():
        catalogue = json.loads((root / path).read_text())
        updated = synced_catalogue(catalogue)
        updated_catalogues[path] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for path, updated in updated_catalogues.items():
            if json.loads((root / path).read_text()) != updated:
                stale.append(path)
        for path, updated in updated_views.items():
            if (root / path).read_text() != updated:
                stale.append(path)
        if stale:
            raise ValueError("stale intrinsics_16_9_k fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogues:
            for path, updated in updated_catalogues.items():
                (root / path).write_text(json.dumps(updated, indent=2) + "\n")
            for path, updated in updated_views.items():
                (root / path).write_text(updated)
    return files, specs


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    flag = (("--std=" if "lfortran" in name else "-std=") + std) if std else ""
    return [str(compiler)] + ([flag] if flag else []) + [str(source), "-o", str(output)]


def compiler_family(compiler):
    return "lfortran" if "lfortran" in Path(compiler).name.lower() else "gfortran"


KNOWN_PARENT_FAILURES = {
    "lfortran": {
        "get_command_effects",
        "get_command_status",
        "command_argument_status",
    },
}


def run_source(compiler, std, case_dir, source_text, expected_stdout, arguments):
    source = case_dir / "source.f90"
    exe = case_dir / "program"
    source.write_text(source_text)
    compile_result = subprocess.run(compiler_command(compiler, std, source, exe), cwd=case_dir,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_result.returncode != 0:
        return dict(status="compile-fail", stdout=compile_result.stdout, stderr=compile_result.stderr,
                    returncode=compile_result.returncode)
    run_result = subprocess.run([str(exe)] + list(arguments), cwd=case_dir, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run_result.returncode == 0 and run_result.stdout == expected_stdout and run_result.stderr == ""
    return dict(status="pass" if passed else "run-fail", stdout=run_result.stdout,
                stderr=run_result.stderr, returncode=run_result.returncode)


def mutation_check(root, compiler, std, keep_work=False, inject_survivor=False):
    root = Path(root)
    _, specs = build_corpus(root)
    family = compiler_family(compiler)
    workspace = root / ".intrinsics_16_9_k_mutations" / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    report = []
    try:
        for case_index, spec in enumerate(specs.values(), 1):
            case_dir = workspace / f"{case_index:03d}_{spec['variant']}"
            case_dir.mkdir()
            parent = run_source(compiler, std, case_dir, spec["source"], spec["completion"], spec["arguments"])
            parent_ok = parent["status"] == "pass"
            parent_known = spec["variant"] in KNOWN_PARENT_FAILURES.get(family, set())
            for index, mutation in enumerate(spec["mutations"]):
                if not parent_ok and parent_known:
                    report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                       kind=mutation["kind"], skipped=True, parent_ok=False, failed=True,
                                       status="known-parent-failure", stdout=parent["stdout"], stderr=parent["stderr"],
                                       returncode=parent["returncode"]))
                    continue
                mutant_dir = case_dir / f"mut_{index:03d}"
                mutant_dir.mkdir()
                mutant = spec["source"] if inject_survivor and not report else mutated_source(spec, mutation).decode("ascii")
                observed = run_source(compiler, std, mutant_dir, mutant, spec["completion"], spec["arguments"])
                failed = observed["status"] == "run-fail"
                report.append(dict(variant=spec["variant"], mutation=mutation["id"], facet=mutation["facet"],
                                   kind=mutation["kind"], parent_ok=parent_ok, failed=failed,
                                   status=observed["status"], stdout=observed["stdout"], stderr=observed["stderr"],
                                   returncode=observed["returncode"]))
        bad = [row for row in report if (not row["parent_ok"] and not row.get("skipped"))
               or not row["failed"] or row["status"] == "compile-fail"]
        if bad:
            raise RuntimeError(json.dumps(bad[:10], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check))) > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work, args.inject_surviving_mutant)
        skipped = sum(1 for row in report if row.get("skipped"))
        print(f"Mutation-checked {len(report) - skipped}/{len(report) - skipped} intrinsics_16_9_k mutants; "
              f"{skipped} skipped for known parent failures.")
        return
    files, specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_k cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
