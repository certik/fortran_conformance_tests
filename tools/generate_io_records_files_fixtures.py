#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 12.1-12.3.2 I/O records and files."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "io_records_files"
SECTIONS = ("12.1", "12.2.1", "12.2.2", "12.2.3", "12.2.4", "12.3.1", "12.3.2")
CATALOGUES = {
    "12.1": "doc/catalogues/input_output_concepts_12_1.json",
    "12.2.1": "doc/catalogues/definition_of_a_record_12_2_1.json",
    "12.2.2": "doc/catalogues/formatted_record_12_2_2.json",
    "12.2.3": "doc/catalogues/unformatted_record_12_2_3.json",
    "12.2.4": "doc/catalogues/endfile_record_12_2_4.json",
    "12.3.1": "doc/catalogues/external_file_concepts_12_3_1.json",
    "12.3.2": "doc/catalogues/file_existence_12_3_2.json",
}
VIEWS = {
    "12.1": "doc/fortran_2023_12_1.md",
    "12.2.1": "doc/fortran_2023_12_2_1.md",
    "12.2.2": "doc/fortran_2023_12_2_2.md",
    "12.2.3": "doc/fortran_2023_12_2_3.md",
    "12.2.4": "doc/fortran_2023_12_2_4.md",
    "12.3.1": "doc/fortran_2023_12_3_1.md",
    "12.3.2": "doc/fortran_2023_12_3_2.md",
}
SUMMARY_BEGIN = "<!-- BEGIN IO RECORDS FILES FIXTURES -->"
SUMMARY_END = "<!-- END IO RECORDS FILES FIXTURES -->"

CASES = [
    dict(
        variant="internal_formatted_transfer",
        rule="S12.1-001",
        facets=["input-reading-transfer", "output-writing-transfer", "editing-specified-by-some-io-statements"],
        extra_facets={
            "S12.1-006": ["external-or-internal-file-classification"],
            "S12.2.1-001": ["record-character-sequence", "record-kind-formatted-unformatted-endfile"],
            "S12.2.2-001": ["formatted-record-character-sequence"],
            "S12.2.2-003": ["formatted-length-measured-in-characters"],
        },
    ),
    dict(
        variant="external_formatted_records",
        rule="S12.1-002",
        facets=["auxiliary-manipulates-external-medium", "auxiliary-inquires-connection-properties"],
        extra_facets={
            "S12.1-004": ["record-file-composition"],
            "S12.1-006": ["external-or-internal-file-classification"],
            "S12.2.2-005": ["formatted-zero-length-record-permitted"],
            "S12.3.1-001": ["external-file-external-medium"],
            "S12.3.1-006": ["connected-external-file-position-property"],
        },
    ),
    dict(
        variant="unformatted_value_and_empty_records",
        rule="S12.2.3-001",
        facets=["unformatted-value-sequence", "unformatted-any-type-or-no-data"],
        extra_facets={
            "S12.2.1-001": ["record-value-sequence", "record-kind-formatted-unformatted-endfile"],
            "S12.2.3-002": ["unformatted-length-output-list-dependent"],
            "S12.2.3-005": ["unformatted-zero-length-record-permitted"],
        },
    ),
    dict(
        variant="endfile_explicit_and_implicit",
        rule="S12.2.4-001",
        facets=["explicit-endfile-statement-writes-endfile-record"],
        extra_facets={
            "S12.2.1-001": ["record-kind-formatted-unformatted-endfile"],
            "S12.2.4-003": [
                "implicit-endfile-after-output-before-rewind-or-backspace",
                "implicit-endfile-on-close-after-output",
                "implicit-endfile-on-open-same-unit-after-output",
            ],
        },
    ),
    dict(
        variant="named_file_create_delete_inquire",
        rule="S12.3.1-003",
        facets=["file-may-have-name", "named-file-definition", "file-name-character-string"],
        extra_facets={
            "S12.3.2-001": ["known-file-need-not-exist-for-program"],
            "S12.3.2-002": ["create-file-causes-existence", "delete-file-terminates-existence"],
            "S12.3.2-004": ["inquire-may-reference-nonexistent-file", "open-may-reference-nonexistent-file"],
        },
    ),
]
CASE_BY_VARIANT = {case["variant"]: case for case in CASES}

RULE_FACETS = {}
for case in CASES:
    RULE_FACETS.setdefault(case["rule"], []).extend(case["facets"])
    for rule, facets in case.get("extra_facets", {}).items():
        RULE_FACETS.setdefault(rule, []).extend(facets)
RULE_FACETS = {rule: tuple(dict.fromkeys(facets)) for rule, facets in RULE_FACETS.items()}
POSITIVE_CONTROL_RULES = set()

ORACLE_PREFIX = {rule: f"{rule} I/O records/files runtime fixtures: " for rule in RULE_FACETS}
LIMIT_PREFIX = {rule: f"{rule} I/O records/files fixture boundaries: " for rule in RULE_FACETS}

ORACLE_PARAGRAPHS = {
    "S12.1-001": ORACLE_PREFIX["S12.1-001"] +
        "the internal formatted-transfer program initializes a character internal file to '#', writes exact characters "
        "with WRITE(record,'(I3,1X,A)'), then initializes integer and character input targets to distinctive sentinels "
        "and READs the same record back with the same explicit format. Exact record text, IOSTAT zero, and changed target "
        "values prove reading, writing, and specified editing without external representation assumptions.",
    "S12.1-002": ORACLE_PREFIX["S12.1-002"] +
        "the external formatted-record program opens a scratch sequential formatted external file, INQUIREs OPENED=.true., "
        "writes records, REWINDs, and reads them in order. The REWIND is load-bearing because deleting it leaves the file "
        "position at terminal point; the INQUIRE logical is initialized opposite to the expected value.",
    "S12.1-004": ORACLE_PREFIX["S12.1-004"] +
        "one scratch sequential formatted file is observed as a record file by reading back two nonempty records around an "
        "empty formatted record. No byte count, newline encoding, or stream/record correspondence is asserted; stream and "
        "file-storage-unit latitude facets remain pending.",
    "S12.1-006": ORACLE_PREFIX["S12.1-006"] +
        "internal-file transfer is observed through a CHARACTER variable and external-file transfer through scratch/named "
        "unit connections, with exact data effects only.",
    "S12.2.1-001": ORACLE_PREFIX["S12.2.1-001"] +
        "formatted fixtures recover exact character sequences and the unformatted fixture recovers integer/logical value "
        "sequences from records; the endfile fixture observes the named IOSTAT_END condition after explicit and implicit "
        "endfile records. These three executable observations cover the three record kinds without observing or assuming "
        "any physical record entity.",
    "S12.2.2-001": ORACLE_PREFIX["S12.2.2-001"] +
        "the internal formatted WRITE produces exact representable characters '137 Q' in a length-five record prefilled with "
        "'#', and a formatted READ recovers 137 and 'Q' into nondefault sentinels.",
    "S12.2.2-003": ORACLE_PREFIX["S12.2.2-003"] +
        "LEN(record)==5 is checked before equality for the internal formatted record '137 Q', so the measured character "
        "length is part of the oracle rather than blank-padding character comparison.",
    "S12.2.2-005": ORACLE_PREFIX["S12.2.2-005"] +
        "an empty formatted record is written between 'A' and 'B'; after REWIND, formatted reads observe 'A', then a blank "
        "from the zero-length record into a length-one character item, then 'B'. Record lengths of external media remain unasserted.",
    "S12.2.3-001": ORACLE_PREFIX["S12.2.3-001"] +
        "the unformatted fixture writes an integer/logical value record, an empty unformatted record, and a second integer "
        "record; after REWIND it recovers 137/.true., advances over the empty record with a no-list READ, and recovers 246.",
    "S12.2.3-002": ORACLE_PREFIX["S12.2.3-002"] +
        "changing the first unformatted output list from two values to one is a load-bearing mutation; the oracle observes "
        "value-count compatibility but never asserts storage-unit byte sizes.",
    "S12.2.3-005": ORACLE_PREFIX["S12.2.3-005"] +
        "the no-list WRITE creates an empty unformatted record between value records, and a no-list READ must consume that "
        "middle position before the following integer record is read. Processor/medium length is not compared.",
    "S12.2.4-001": ORACLE_PREFIX["S12.2.4-001"] +
        "after a sequential formatted data record, ENDFILE is executed explicitly; REWIND then reads the data record first "
        "and the next READ returns the named intrinsic IOSTAT_END value, not a processor-specific number.",
    "S12.2.4-003": ORACLE_PREFIX["S12.2.4-003"] +
        "three separate sequential cases observe implicit endfile records after output followed by REWIND, by CLOSE and reopen, "
        "and by another OPEN on the same unit. Each first reads the known data record, then observes IOSTAT_END.",
    "S12.3.1-001": ORACLE_PREFIX["S12.3.1-001"] +
        "scratch external files are connected to units and used for portable data transfer effects only; no medium implementation "
        "or storage representation is asserted.",
    "S12.3.1-003": ORACLE_PREFIX["S12.3.1-003"] +
        "the named-file fixture uses a nonblank CHARACTER value as FILE=, observes EXIST=.false. before creation, opens the "
        "same name, writes data, observes EXIST=.true., and closes with STATUS='DELETE' to observe nonexistence again.",
    "S12.3.1-006": ORACLE_PREFIX["S12.3.1-006"] +
        "the formatted external record fixture distinguishes the terminal post-write position from the initial record position "
        "by requiring a load-bearing REWIND before reads recover the records; no byte/device offset is asserted.",
    "S12.3.2-001": ORACLE_PREFIX["S12.3.2-001"] +
        "after a controlled delete of a conservative local name, INQUIRE(FILE=name, EXIST=...) observes that a processor-known "
        "character string need not denote an existing file for the program at that time.",
    "S12.3.2-002": ORACLE_PREFIX["S12.3.2-002"] +
        "the named-file fixture observes EXIST changing from false to true after OPEN(STATUS='NEW') creates the file, then "
        "from true to false after CLOSE(STATUS='DELETE') terminates its existence.",
    "S12.3.2-004": ORACLE_PREFIX["S12.3.2-004"] +
        "INQUIRE(FILE=name, EXIST=...) is executed while the controlled name does not exist and returns .false.; OPEN with "
        "STATUS='NEW' then refers to that nonexistent name and creates it. Other permitted-statement facets remain pending.",
}
LIMIT_PARAGRAPH = (
    "These fixtures are single-image positive runtime observations over internal CHARACTER files, scratch external files, "
    "and conservative local named files created in the execution working directory and deleted by the program. They assert "
    "only exact integers/logicals/characters, LEN before character equality, IOSTAT zero, and equality with the named "
    "IOSTAT_END constant. They do not assert byte sizes, record marker layout, IOMSG text, numeric IOSTAT values, ambient "
    "file existence, path syntax beyond the chosen local names, preconnected file identity, coarray image interactions, "
    "stream/record correspondence, or required diagnostics for mismatched forms/nonexistent files. Remaining facets stay "
    "pending with their source-accounting rationale."
)

RESTORED_PENDING = {
    "S12.2.2-004": {
        "formatted-records-formatted-io-only":
            "This unnumbered shall restriction is not discharged by a positive formatted-I/O control; a future owning-rule "
            "negative must establish a portable required rejection or other executable effect for mismatched forms."
    },
    "S12.2.3-003": {
        "unformatted-records-unformatted-io-only":
            "This unnumbered shall restriction is not discharged by a positive unformatted-I/O control; a future owning-rule "
            "negative must establish a portable required rejection or other executable effect for mismatched forms."
    },
    "S12.2.4-002": {
        "explicit-endfile-requires-sequential-access":
            "This unnumbered shall restriction is not discharged by a sequential positive control; direct/stream ENDFILE "
            "rejection is not required by this catalogue alone."
    },
    "S12.2.4-004": {
        "endfile-record-last-record-only":
            "This unnumbered shall restriction is not discharged by observing a conforming endfile at terminal position; "
            "a data-after-endfile negative belongs to later positioning/data-transfer rules if portably observable."
    },
}

FACET_ASSERTION_MUTANTS = {
    ("S12.1-001", "input-reading-transfer"):
        dict(variant="internal_formatted_transfer", assertion="n-read", feature_mutant="read-format-substitution"),
    ("S12.1-001", "output-writing-transfer"):
        dict(variant="internal_formatted_transfer", assertion="record-text", feature_mutant="remove-internal-write"),
    ("S12.1-001", "editing-specified-by-some-io-statements"):
        dict(variant="internal_formatted_transfer", assertion="record-text", feature_mutant="write-format-substitution"),
    ("S12.1-002", "auxiliary-manipulates-external-medium"):
        dict(variant="external_formatted_records", assertion="read-a", feature_mutant="remove-rewind"),
    ("S12.1-002", "auxiliary-inquires-connection-properties"):
        dict(variant="external_formatted_records", assertion="opened-inquire", feature_mutant="remove-opened-inquire"),
    ("S12.1-004", "record-file-composition"):
        dict(variant="external_formatted_records", assertion="read-b", feature_mutant="change-second-record"),
    ("S12.1-006", "external-or-internal-file-classification"):
        [
            dict(variant="internal_formatted_transfer", assertion="record-text", feature_mutant="remove-internal-write"),
            dict(variant="external_formatted_records", assertion="read-a", feature_mutant="change-first-record"),
        ],
    ("S12.2.1-001", "record-character-sequence"):
        dict(variant="internal_formatted_transfer", assertion="record-text", feature_mutant="write-format-substitution"),
    ("S12.2.1-001", "record-value-sequence"):
        dict(variant="unformatted_value_and_empty_records", assertion="first-read", feature_mutant="drop-logical-output-list"),
    ("S12.2.1-001", "record-kind-formatted-unformatted-endfile"):
        [
            dict(variant="internal_formatted_transfer", assertion="record-text", feature_mutant="write-format-substitution"),
            dict(variant="unformatted_value_and_empty_records", assertion="flag-read",
                 feature_mutant="change-logical-unformatted-value"),
            dict(variant="endfile_explicit_and_implicit", assertion="explicit-end-status",
                 feature_mutant="explicit-endfile-to-data-record"),
        ],
    ("S12.2.2-001", "formatted-record-character-sequence"):
        dict(variant="internal_formatted_transfer", assertion="record-text", feature_mutant="remove-internal-write"),
    ("S12.2.2-003", "formatted-length-measured-in-characters"):
        dict(variant="internal_formatted_transfer", assertion="record-len", feature_mutant="write-format-substitution"),
    ("S12.2.2-005", "formatted-zero-length-record-permitted"):
        dict(variant="external_formatted_records", assertion="read-empty", feature_mutant="remove-empty-record-write"),
    ("S12.2.3-001", "unformatted-value-sequence"):
        dict(variant="unformatted_value_and_empty_records", assertion="second-read",
             feature_mutant="change-second-unformatted-value"),
    ("S12.2.3-001", "unformatted-any-type-or-no-data"):
        dict(variant="unformatted_value_and_empty_records", assertion="flag-read",
             feature_mutant="change-logical-unformatted-value"),
    ("S12.2.3-002", "unformatted-length-output-list-dependent"):
        dict(variant="unformatted_value_and_empty_records", assertion="read-values-status",
             feature_mutant="drop-logical-output-list"),
    ("S12.2.3-005", "unformatted-zero-length-record-permitted"):
        dict(variant="unformatted_value_and_empty_records", assertion="read-second-status",
             feature_mutant="remove-empty-unformatted-record"),
    ("S12.2.4-001", "explicit-endfile-statement-writes-endfile-record"):
        dict(variant="endfile_explicit_and_implicit", assertion="explicit-end-status",
             feature_mutant="explicit-endfile-to-data-record"),
    ("S12.2.4-003", "implicit-endfile-after-output-before-rewind-or-backspace"):
        dict(variant="endfile_explicit_and_implicit", assertion="implicit-rewind-end",
             feature_mutant="remove-implicit-rewind"),
    ("S12.2.4-003", "implicit-endfile-on-close-after-output"):
        dict(variant="endfile_explicit_and_implicit", assertion="implicit-close-end",
             feature_mutant="implicit-close-to-data-record"),
    ("S12.2.4-003", "implicit-endfile-on-open-same-unit-after-output"):
        dict(variant="endfile_explicit_and_implicit", assertion="implicit-open-end",
             feature_mutant="same-unit-open-to-extra-data"),
    ("S12.3.1-001", "external-file-external-medium"):
        dict(variant="external_formatted_records", assertion="read-a", feature_mutant="change-first-record"),
    ("S12.3.1-003", "file-may-have-name"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-after-open",
             feature_mutant="open-different-name"),
    ("S12.3.1-003", "named-file-definition"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-after-open",
             feature_mutant="open-different-name"),
    ("S12.3.1-003", "file-name-character-string"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-after-open",
             feature_mutant="open-different-name"),
    ("S12.3.1-006", "connected-external-file-position-property"):
        dict(variant="external_formatted_records", assertion="read-a", feature_mutant="remove-rewind"),
    ("S12.3.2-001", "known-file-need-not-exist-for-program"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-before",
             feature_mutant="create-known-file-before-inquire"),
    ("S12.3.2-002", "create-file-causes-existence"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-after-open",
             feature_mutant="open-scratch-instead-of-named"),
    ("S12.3.2-002", "delete-file-terminates-existence"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-after-delete",
             feature_mutant="remove-close-delete"),
    ("S12.3.2-004", "inquire-may-reference-nonexistent-file"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-before",
             feature_mutant="remove-inquire-before"),
    ("S12.3.2-004", "open-may-reference-nonexistent-file"):
        dict(variant="named_file_create_delete_inquire", assertion="exists-after-open",
             feature_mutant="open-scratch-instead-of-named"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier_for(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__io_records_files_" + variant


def program_name(variant):
    return "io_rf_" + variant


def sentinel_init_probes(block, remove_replacement, expected_replacement, default_replacement, stem):
    probes = [
        (stem + "-remove", block, remove_replacement, "sentinel-init-remove"),
        (stem + "-expected", block, expected_replacement, "sentinel-init-expected"),
    ]
    if default_replacement is not None:
        probes.append((stem + "-default", block, default_replacement, "sentinel-init-default"))
    return probes


def common_contains(variant, body, completion):
    return f"""contains
  subroutine pass(label)
    character(len=*), intent(in) :: label
    checks = checks + 1
  end subroutine pass
  subroutine expect_int(value, expected, label)
    integer, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IORF:int', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int
  subroutine expect_logical(value, expected, label)
    logical, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value .neqv. expected) then
      write(*,'(a,1x,a)') 'IORF:logical', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_logical
  subroutine expect_char(value, expected, label)
    character(len=*), intent(in) :: value, expected, label
    if (len(value) /= len(expected)) then
      write(*,'(a,1x,a)') 'IORF:length', label
      error stop 1
    end if
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IORF:char', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char
  subroutine expect_zero(status, label)
    integer, intent(in) :: status
    character(len=*), intent(in) :: label
    if (status /= 0) then
      write(*,'(a,1x,a)') 'IORF:iostat-zero', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_zero
  subroutine expect_end(status, label)
    integer, intent(in) :: status
    character(len=*), intent(in) :: label
    if (status /= iostat_end) then
      write(*,'(a,1x,a)') 'IORF:iostat-end', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_end
  subroutine finish()
    if (checks /= EXPECTED_CHECKS) then
      write(*,'(a)') 'IORF:{variant}:check-total'
      error stop 1
    end if
    write(*,'(a)') '{completion}'
  end subroutine finish
end program {program_name(variant)}
""".replace("EXPECTED_CHECKS", str(body.count("call expect_") + body.count("call pass(")))


def source_internal_formatted_transfer():
    variant = "internal_formatted_transfer"
    completion = "IO RECORDS FILES INTERNAL FORMATTED TRANSFER OK"
    body = """  record = '#####'
  n = -777
  letter = 'Z'
  ios = -900
  call expect_int(n, -777, 'n-pre')
  call expect_char(letter, 'Z', 'letter-pre')
  call expect_char(record, '#####', 'record-pre')
  write(record,'(I3,1X,A)',iostat=ios) 137, 'Q'
  call expect_zero(ios, 'write-internal')
  call expect_int(len(record), 5, 'record-len')
  call expect_char(record, '137 Q', 'record-text')
  ios = -901
  read(record,'(I3,1X,A)',iostat=ios) n, letter
  call expect_zero(ios, 'read-internal')
  call expect_int(n, 137, 'n-read')
  call expect_char(letter, 'Q', 'letter-read')
  call finish()
"""
    src = f"""program {program_name(variant)}
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.1-001
! covers: input-reading-transfer output-writing-transfer editing-specified-by-some-io-statements
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, n
  character(len=5) :: record
  character(len=1) :: letter
  checks = 0
""" + body + common_contains(variant, body, completion)
    n_block = "  n = -777\n"
    letter_block = "  letter = 'Z'\n"
    record_block = "  record = '#####'\n"
    mutations = [
        ("remove-internal-write", "  write(record,'(I3,1X,A)',iostat=ios) 137, 'Q'\n", "  ! mutation removed formatted internal write\n", "feature-removal"),
        ("write-format-substitution", "write(record,'(I3,1X,A)'", "write(record,'(I2,1X,A)'", "format-substitution"),
        ("read-format-substitution", "read(record,'(I3,1X,A)'", "read(record,'(I2,1X,A)'", "format-substitution"),
        ("oracle-record-text", "'137 Q', 'record-text'", "'137 Z', 'record-text'", "oracle"),
        ("completion-output", completion, completion.replace(" OK", " BAD"), "completion"),
    ] + sentinel_init_probes(n_block, "", "  n = 137\n", "  n = 0\n", "sentinel-n") + \
        sentinel_init_probes(letter_block, "", "  letter = 'Q'\n", "  letter = ' '\n", "sentinel-letter") + \
        sentinel_init_probes(record_block, "", "  record = '137 Q'\n", "  record = '     '\n", "sentinel-record")
    return src, mutations


def source_external_formatted_records():
    variant = "external_formatted_records"
    completion = "IO RECORDS FILES EXTERNAL FORMATTED RECORDS OK"
    body = """  opened = .true.
  call expect_logical(opened, .true., 'opened-pre')
  inquire(unit=u, opened=opened)
  call expect_logical(opened, .false., 'opened-inquire')
  ios = -910
  open(newunit=u, status='scratch', form='formatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'open-scratch')
  write(u,'(A)',iostat=ios) 'A'
  call expect_zero(ios, 'write-a')
  write(u,'()',iostat=ios)
  call expect_zero(ios, 'write-empty')
  write(u,'(A)',iostat=ios) 'B'
  call expect_zero(ios, 'write-b')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'rewind')
  ch = '#'
  call expect_char(ch, '#', 'ch-pre-a')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'read-a-status')
  call expect_char(ch, 'A', 'read-a')
  ch = '#'
  call expect_char(ch, '#', 'ch-pre-empty')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'read-empty-status')
  call expect_char(ch, ' ', 'read-empty')
  ch = '#'
  call expect_char(ch, '#', 'ch-pre-b')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'read-b-status')
  call expect_char(ch, 'B', 'read-b')
  close(u)
  call finish()
"""
    src = f"""program {program_name(variant)}
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.1-002
! covers: auxiliary-manipulates-external-medium auxiliary-inquires-connection-properties
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u
  character(len=1) :: ch
  logical :: opened
  checks = 0
""" + body + common_contains(variant, body, completion)
    opened_block = "  opened = .true.\n  call expect_logical(opened, .true., 'opened-pre')\n"
    ch_a_block = "  ch = '#'\n  call expect_char(ch, '#', 'ch-pre-a')\n"
    ch_empty_block = "  ch = '#'\n  call expect_char(ch, '#', 'ch-pre-empty')\n"
    ch_b_block = "  ch = '#'\n  call expect_char(ch, '#', 'ch-pre-b')\n"
    mutations = [
        ("remove-opened-inquire", "  inquire(unit=u, opened=opened)\n", "  ! mutation removed OPENED inquire\n", "feature-removal"),
        ("remove-rewind", "  rewind(u, iostat=ios)\n", "  ! mutation removed rewind\n", "feature-removal"),
        ("remove-empty-record-write", "  write(u,'()',iostat=ios)\n", "  ! mutation removed empty formatted record\n", "feature-removal"),
        ("change-first-record", "  write(u,'(A)',iostat=ios) 'A'\n", "  write(u,'(A)',iostat=ios) 'Z'\n", "record-data"),
        ("change-second-record", "  write(u,'(A)',iostat=ios) 'B'\n", "  write(u,'(A)',iostat=ios) 'C'\n", "record-data"),
        ("oracle-empty-record", "' ', 'read-empty'", "'#', 'read-empty'", "oracle"),
        ("completion-output", completion, completion.replace(" OK", " BAD"), "completion"),
    ] + sentinel_init_probes(opened_block, "  call expect_logical(opened, .true., 'opened-pre')\n",
                             "  opened = .false.\n  call expect_logical(opened, .true., 'opened-pre')\n",
                             "  opened = .false.\n  call expect_logical(opened, .true., 'opened-pre')\n", "sentinel-opened") + \
        sentinel_init_probes(ch_a_block, "  call expect_char(ch, '#', 'ch-pre-a')\n",
                             "  ch = 'A'\n  call expect_char(ch, '#', 'ch-pre-a')\n",
                             "  ch = ' '\n  call expect_char(ch, '#', 'ch-pre-a')\n", "sentinel-ch-a") + \
        sentinel_init_probes(ch_empty_block, "  call expect_char(ch, '#', 'ch-pre-empty')\n",
                             "  ch = ' '\n  call expect_char(ch, '#', 'ch-pre-empty')\n",
                             "  ch = ' '\n  call expect_char(ch, '#', 'ch-pre-empty')\n", "sentinel-ch-empty") + \
        sentinel_init_probes(ch_b_block, "  call expect_char(ch, '#', 'ch-pre-b')\n",
                             "  ch = 'B'\n  call expect_char(ch, '#', 'ch-pre-b')\n",
                             "  ch = ' '\n  call expect_char(ch, '#', 'ch-pre-b')\n", "sentinel-ch-b")
    return src, mutations


def source_unformatted_value_and_empty_records():
    variant = "unformatted_value_and_empty_records"
    completion = "IO RECORDS FILES UNFORMATTED VALUE AND EMPTY RECORDS OK"
    body = """  ios = -920
  open(newunit=u, status='scratch', form='unformatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'open-unformatted')
  first = 0
  first = -701
  second = 0
  second = -702
  flag = .false.
  flag = .true.
  call expect_int(first, -701, 'first-pre')
  call expect_int(second, -702, 'second-pre')
  call expect_logical(flag, .true., 'flag-pre')
  write(u, iostat=ios) 137, .false.
  call expect_zero(ios, 'write-values')
  write(u, iostat=ios)
  call expect_zero(ios, 'write-empty-unformatted')
  write(u, iostat=ios) 246
  call expect_zero(ios, 'write-second')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'rewind-unformatted')
  read(u, iostat=ios) first, flag
  call expect_zero(ios, 'read-values-status')
  call expect_int(first, 137, 'first-read')
  call expect_logical(flag, .false., 'flag-read')
  read(u, iostat=ios)
  call expect_zero(ios, 'read-empty-unformatted')
  read(u, iostat=ios) second
  call expect_zero(ios, 'read-second-status')
  call expect_int(second, 246, 'second-read')
  close(u)
  call finish()
"""
    src = f"""program {program_name(variant)}
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.2.3-001
! covers: unformatted-value-sequence unformatted-any-type-or-no-data
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u, first, second
  logical :: flag
  checks = 0
""" + body + common_contains(variant, body, completion)
    first_block = "  first = -701\n"
    second_block = "  second = -702\n"
    flag_block = "  flag = .true.\n"
    mutations = [
        ("remove-empty-unformatted-record", "  write(u, iostat=ios)\n", "  ! mutation removed empty unformatted record\n", "feature-removal"),
        ("drop-logical-output-list", "  write(u, iostat=ios) 137, .false.\n", "  write(u, iostat=ios) 137\n", "output-list"),
        ("change-logical-unformatted-value", "  write(u, iostat=ios) 137, .false.\n", "  write(u, iostat=ios) 137, .true.\n", "record-data"),
        ("change-second-unformatted-value", "  write(u, iostat=ios) 246\n", "  write(u, iostat=ios) 247\n", "record-data"),
        ("oracle-second", "246, 'second-read'", "247, 'second-read'", "oracle"),
        ("completion-output", completion, completion.replace(" OK", " BAD"), "completion"),
    ] + sentinel_init_probes(first_block, "", "  first = 137\n", "  first = 0\n", "sentinel-first") + \
        sentinel_init_probes(second_block,
                             "",
                             "  second = 246\n",
                             "  second = 0\n",
                             "sentinel-second") + \
        sentinel_init_probes(flag_block,
                             "",
                             "  flag = .false.\n",
                             "  flag = .false.\n",
                             "sentinel-flag")
    return src, mutations


def source_endfile_explicit_and_implicit():
    variant = "endfile_explicit_and_implicit"
    completion = "IO RECORDS FILES ENDFILE EXPLICIT AND IMPLICIT OK"
    body = """  call cleanup_name(name_close)
  call cleanup_name(name_open_a)
  call cleanup_name(name_open_b)

  open(newunit=u, status='scratch', form='formatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'explicit-open')
  write(u,'(A)',iostat=ios) 'E'
  call expect_zero(ios, 'explicit-write')
  endfile(u, iostat=ios)
  call expect_zero(ios, 'explicit-endfile')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'explicit-rewind')
  ch = '#'
  call expect_char(ch, '#', 'explicit-data-pre')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'explicit-data-status')
  call expect_char(ch, 'E', 'explicit-data')
  ch = '!'
  call expect_char(ch, '!', 'explicit-end-pre')
  ios = -930
  read(u,'(A)',iostat=ios) ch
  call expect_end(ios, 'explicit-end-status')
  close(u)

  open(newunit=u, status='scratch', form='formatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'implicit-rewind-open')
  write(u,'(A)',iostat=ios) 'R'
  call expect_zero(ios, 'implicit-rewind-write')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'implicit-rewind')
  ch = '@'
  call expect_char(ch, '@', 'implicit-rewind-data-pre')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'implicit-rewind-data-status')
  call expect_char(ch, 'R', 'implicit-rewind-data')
  ch = '$'
  call expect_char(ch, '$', 'implicit-rewind-end-pre')
  ios = -931
  read(u,'(A)',iostat=ios) ch
  call expect_end(ios, 'implicit-rewind-end')
  close(u)

  open(newunit=u, file=name_close, status='new', form='formatted', action='write', iostat=ios)
  call expect_zero(ios, 'implicit-close-open')
  write(u,'(A)',iostat=ios) 'C'
  call expect_zero(ios, 'implicit-close-write')
  close(u, iostat=ios)
  call expect_zero(ios, 'implicit-close-close')
  open(newunit=u, file=name_close, status='old', form='formatted', action='read', iostat=ios)
  call expect_zero(ios, 'implicit-close-reopen')
  ch = '%'
  call expect_char(ch, '%', 'implicit-close-data-pre')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'implicit-close-data-status')
  call expect_char(ch, 'C', 'implicit-close-data')
  ch = '&'
  call expect_char(ch, '&', 'implicit-close-end-pre')
  ios = -932
  read(u,'(A)',iostat=ios) ch
  call expect_end(ios, 'implicit-close-end')
  close(u, status='delete')

  open(newunit=u, file=name_open_a, status='new', form='formatted', action='write', iostat=ios)
  call expect_zero(ios, 'implicit-open-first')
  write(u,'(A)',iostat=ios) 'O'
  call expect_zero(ios, 'implicit-open-write')
  open(unit=u, file=name_open_b, status='new', form='formatted', action='write', iostat=ios)
  call expect_zero(ios, 'implicit-open-second')
  close(u, status='delete')
  open(newunit=v, file=name_open_a, status='old', form='formatted', action='read', iostat=ios)
  call expect_zero(ios, 'implicit-open-reopen-first')
  ch = '?'
  call expect_char(ch, '?', 'implicit-open-data-pre')
  read(v,'(A)',iostat=ios) ch
  call expect_zero(ios, 'implicit-open-data-status')
  call expect_char(ch, 'O', 'implicit-open-data')
  ch = '~'
  call expect_char(ch, '~', 'implicit-open-end-pre')
  ios = -933
  read(v,'(A)',iostat=ios) ch
  call expect_end(ios, 'implicit-open-end')
  close(v, status='delete')
  call finish()
"""
    src = f"""program {program_name(variant)}
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.2.4-001
! covers: explicit-endfile-statement-writes-endfile-record
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u, v
  character(len=1) :: ch
  character(len=*), parameter :: name_close = 'io_records_files_implicit_close.dat'
  character(len=*), parameter :: name_open_a = 'io_records_files_implicit_open_a.dat'
  character(len=*), parameter :: name_open_b = 'io_records_files_implicit_open_b.dat'
  checks = 0
""" + body + common_contains(variant, body, completion).replace(
        "contains\n", "contains\n  subroutine cleanup_name(name)\n    character(len=*), intent(in) :: name\n    integer :: cu, cios\n    open(newunit=cu, file=name, status='replace', iostat=cios)\n    if (cios == 0) close(cu, status='delete')\n  end subroutine cleanup_name\n")
    def ch_sentinel(label, sentinel, expected_value):
        block = f"  ch = '{sentinel}'\n  call expect_char(ch, '{sentinel}', '{label}-pre')\n"
        return sentinel_init_probes(block, f"  call expect_char(ch, '{sentinel}', '{label}-pre')\n",
                                    f"  ch = '{expected_value}'\n  call expect_char(ch, '{sentinel}', '{label}-pre')\n",
                                    f"  ch = ' '\n  call expect_char(ch, '{sentinel}', '{label}-pre')\n",
                                    "sentinel-ch-" + label)

    mutations = [
        ("explicit-endfile-to-data-record", "  endfile(u, iostat=ios)\n",
         "  write(u,'(A)',iostat=ios) 'X'\n", "feature-substitution"),
        ("remove-implicit-rewind", "  rewind(u, iostat=ios)\n", "  ! mutation removed implicit-endfile rewind\n", "feature-removal"),
        ("implicit-close-to-data-record", "  close(u, iostat=ios)\n",
         "  write(u,'(A)',iostat=ios) 'D'\n", "feature-substitution"),
        ("same-unit-open-to-extra-data",
         "  open(unit=u, file=name_open_b, status='new', form='formatted', action='write', iostat=ios)\n"
         "  call expect_zero(ios, 'implicit-open-second')\n"
         "  close(u, status='delete')\n",
         "  write(u,'(A)',iostat=ios) 'X'\n"
         "  call expect_zero(ios, 'implicit-open-second')\n"
         "  close(u, iostat=ios)\n",
         "feature-substitution"),
        ("oracle-explicit-end", "call expect_end(ios, 'explicit-end-status')", "call expect_zero(ios, 'explicit-end-status')", "oracle"),
        ("oracle-implicit-close-data", "'C', 'implicit-close-data'", "'D', 'implicit-close-data'", "oracle"),
        ("completion-output", completion, completion.replace(" OK", " BAD"), "completion"),
    ]
    for label, sentinel, expected_value in (
        ("explicit-data", "#", "E"),
        ("explicit-end", "!", "E"),
        ("implicit-rewind-data", "@", "R"),
        ("implicit-rewind-end", "$", "R"),
        ("implicit-close-data", "%", "C"),
        ("implicit-close-end", "&", "C"),
        ("implicit-open-data", "?", "O"),
        ("implicit-open-end", "~", "O"),
    ):
        mutations.extend(ch_sentinel(label, sentinel, expected_value))
    return src, mutations


def source_named_file_create_delete_inquire():
    variant = "named_file_create_delete_inquire"
    completion = "IO RECORDS FILES NAMED FILE CREATE DELETE INQUIRE OK"
    body = """  call cleanup_name(name)
  exists = .false.
  exists = .true.
  call expect_logical(exists, .true., 'exists-before-sentinel')
  inquire(file=name, exist=exists)
  call expect_logical(exists, .false., 'exists-before')
  ios = -940
  open(newunit=u, file=name, status='new', form='formatted', action='readwrite', iostat=ios)
  call expect_zero(ios, 'open-new')
  write(u,'(A)',iostat=ios) 'N'
  call expect_zero(ios, 'write-named')
  exists = .true.
  exists = .false.
  call expect_logical(exists, .false., 'exists-after-open-sentinel')
  inquire(file=name, exist=exists)
  call expect_logical(exists, .true., 'exists-after-open')
  close(u, status='delete', iostat=ios)
  call expect_zero(ios, 'close-delete')
  exists = .false.
  exists = .true.
  call expect_logical(exists, .true., 'exists-after-delete-sentinel')
  inquire(file=name, exist=exists)
  call expect_logical(exists, .false., 'exists-after-delete')
  call finish()
"""
    src = f"""program {program_name(variant)}
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.3.1-003
! covers: file-may-have-name named-file-definition file-name-character-string
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u
  logical :: exists
  character(len=*), parameter :: name = 'io_records_files_named_create_delete.dat'
  checks = 0
""" + body + common_contains(variant, body, completion).replace(
        "contains\n", "contains\n  subroutine cleanup_name(path)\n    character(len=*), intent(in) :: path\n    integer :: cu, cios\n    open(newunit=cu, file=path, status='replace', iostat=cios)\n    if (cios == 0) close(cu, status='delete')\n  end subroutine cleanup_name\n")
    before_inquire_block = "  inquire(file=name, exist=exists)\n  call expect_logical(exists, .false., 'exists-before')\n"
    after_open_inquire_block = "  inquire(file=name, exist=exists)\n  call expect_logical(exists, .true., 'exists-after-open')\n"
    after_delete_inquire_block = "  inquire(file=name, exist=exists)\n  call expect_logical(exists, .false., 'exists-after-delete')\n"
    exists_before_block = "  exists = .true.\n  call expect_logical(exists, .true., 'exists-before-sentinel')\n"
    exists_after_open_block = "  exists = .false.\n  call expect_logical(exists, .false., 'exists-after-open-sentinel')\n"
    exists_after_delete_block = "  exists = .true.\n  call expect_logical(exists, .true., 'exists-after-delete-sentinel')\n"
    mutations = [
        ("create-known-file-before-inquire", "  call cleanup_name(name)\n",
         "  call cleanup_name(name)\n  open(newunit=u, file=name, status='new', iostat=ios)\n  if (ios == 0) close(u)\n",
         "feature-substitution"),
        ("remove-inquire-before", before_inquire_block,
         "  ! mutation removed nonexistent-file inquire\n  call expect_logical(exists, .false., 'exists-before')\n",
         "feature-removal"),
        ("remove-inquire-after-open", after_open_inquire_block,
         "  ! mutation removed post-create inquire\n  call expect_logical(exists, .true., 'exists-after-open')\n",
         "feature-removal"),
        ("remove-inquire-after-delete", after_delete_inquire_block,
         "  ! mutation removed post-delete inquire\n  call expect_logical(exists, .false., 'exists-after-delete')\n",
         "feature-removal"),
        ("open-scratch-instead-of-named",
         "  open(newunit=u, file=name, status='new', form='formatted', action='readwrite', iostat=ios)\n",
         "  open(newunit=u, status='scratch', form='formatted', action='readwrite', iostat=ios)\n",
         "feature-substitution"),
        ("open-different-name", "open(newunit=u, file=name, status='new'",
         "open(newunit=u, file='io_records_files_named_other.dat', status='new'", "file-name"),
        ("remove-close-delete", "  close(u, status='delete', iostat=ios)\n", "  close(u, iostat=ios)\n", "feature-removal"),
        ("oracle-exists-after-open", ".true., 'exists-after-open'", ".false., 'exists-after-open'", "oracle"),
        ("completion-output", completion, completion.replace(" OK", " BAD"), "completion"),
    ] + sentinel_init_probes(exists_before_block,
                             "  call expect_logical(exists, .true., 'exists-before-sentinel')\n",
                             "  exists = .false.\n  call expect_logical(exists, .true., 'exists-before-sentinel')\n",
                             "  exists = .false.\n  call expect_logical(exists, .true., 'exists-before-sentinel')\n",
                             "sentinel-exists-before") + \
        sentinel_init_probes(exists_after_open_block,
                             "  call expect_logical(exists, .false., 'exists-after-open-sentinel')\n",
                             "  exists = .true.\n  call expect_logical(exists, .false., 'exists-after-open-sentinel')\n",
                             None, "sentinel-exists-after-open") + \
        sentinel_init_probes(exists_after_delete_block,
                             "  call expect_logical(exists, .true., 'exists-after-delete-sentinel')\n",
                             "  exists = .false.\n  call expect_logical(exists, .true., 'exists-after-delete-sentinel')\n",
                             "  exists = .false.\n  call expect_logical(exists, .true., 'exists-after-delete-sentinel')\n",
                             "sentinel-exists-after-delete")
    return src, mutations


SOURCE_BUILDERS = {
    "internal_formatted_transfer": source_internal_formatted_transfer,
    "external_formatted_records": source_external_formatted_records,
    "unformatted_value_and_empty_records": source_unformatted_value_and_empty_records,
    "endfile_explicit_and_implicit": source_endfile_explicit_and_implicit,
    "named_file_create_delete_inquire": source_named_file_create_delete_inquire,
}


def case_facets(case):
    return {case["rule"]: list(case["facets"]), **copy.deepcopy(case.get("extra_facets", {}))}


def all_case_facets(case):
    result = []
    for facets in case_facets(case).values():
        result.extend(facets)
    return result


def source_specs():
    specs = {}
    for case in CASES:
        variant = case["variant"]
        for rule, facets in case_facets(case).items():
            source, mutation_specs = SOURCE_BUILDERS[variant]()
            lines = source.splitlines()
            for index, line in enumerate(lines):
                if line.startswith("! rule: "):
                    lines[index] = "! rule: " + rule
                elif line.startswith("! covers: "):
                    covers = "! covers: " + " ".join(facets)
                    if len(covers) > 120:
                        covers = "! covers: " + facets[0] + " (additional facets in fixture.json)"
                    lines[index] = covers
            source = "\n".join(lines) + "\n"
            raw = source.encode("ascii")
            mutations = []
            for mid, expected, replacement, category in mutation_specs:
                start = source.index(expected)
                mutations.append(dict(id=mid, category=category, expected=expected, replacement=replacement,
                                      span=[start, start + len(expected)],
                                      line=source[:start].count("\n") + 1))
            name = identifier_for(rule, variant)
            specs[name] = dict(id=name, variant=variant, rule=rule, facets=list(facets),
                               all_rule_facets=case_facets(case), source=source, source_sha256=sha(raw),
                               mutations=mutations,
                               completion="IO RECORDS FILES " + variant.upper().replace("_", " ") + " OK\n")
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (
            "io_records_files_" + spec["variant"] + "__" + spec["rule"].replace(".", "_").replace("-", "_")
        )
        evidence = "positive-control" if spec["rule"] in POSITIVE_CONTROL_RULES else "effect"
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence=evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    hits = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(hits) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if hits:
        paragraphs[hits[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def without_owned_paragraph(text, prefix):
    return "\n\n".join(p for p in (text.split("\n\n") if text else []) if not p.startswith(prefix))


def synced_catalogue(section, catalogue):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    for rule, pending in RESTORED_PENDING.items():
        if rule not in by_rule:
            continue
        row = by_rule[rule]
        row.setdefault("pending", {}).update(pending)
        old_oracle_prefix = f"{rule} I/O records/files runtime fixtures: "
        old_limit_prefix = f"{rule} I/O records/files fixture boundaries: "
        row["oracle"] = without_owned_paragraph(row.get("oracle", ""), old_oracle_prefix)
        row["oracle_limitation"] = without_owned_paragraph(row.get("oracle_limitation", ""), old_limit_prefix)
    for rule, facets in RULE_FACETS.items():
        if rule not in by_rule:
            continue
        row = by_rule[rule]
        if not set(facets) <= set(row["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX[rule], ORACLE_PARAGRAPHS[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIX[rule],
                                                   LIMIT_PREFIX[rule] + LIMIT_PARAGRAPH)
    return result


def summary_text():
    total_facets = sum(len(facets) for facets in RULE_FACETS.values())
    return (SUMMARY_BEGIN + "\n"
            "## I/O records and files runtime observations\n\n"
            f"Five complete single-image fixtures discharge {total_facets} selected facets in 12.1-12.3.2. "
            "They use internal character files, scratch sequential files, and local named files deleted by the program. "
            "All input targets and inquiry logicals start from distinctive sentinels with pre-transfer guards; character "
            "comparisons check LEN first; endfile observations compare only with ISO_FORTRAN_ENV IOSTAT_END. Permanent "
            "mutations remove or substitute the relevant WRITE/READ/REWIND/ENDFILE/INQUIRE/OPEN/CLOSE feature and alter "
            "sentinels/oracles; no fixture asserts byte sizes, record-marker layout, IOMSG text, numeric IOSTAT values, "
            "preconnected-file identity, or coarray behavior.\n"
            + SUMMARY_END)


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
    old = "This source packet records source accounting and pending plans only, not fixture approval."
    new = ("This source packet records source accounting. Selected I/O records/files fixtures now supply "
           "executable standard-oracle observations and mutation plans; fixture approval remains separate.")
    before = before.replace(old, new)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("summary boundary changed for " + section)
        leading, rest_summary = before.split(SUMMARY_BEGIN)
        _, trailing = rest_summary.split(SUMMARY_END)
        before = leading.rstrip() + "\n\n" + trailing.lstrip()
    return before.rstrip() + "\n\n" + summary_text() + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updates, views = {}, {}
    stale = []
    for section in SECTIONS:
        cat_path = root / CATALOGUES[section]
        catalogue = json.loads(cat_path.read_text())
        updated = synced_catalogue(section, catalogue)
        rendered = render_view(section, updated, root)
        updates[section] = updated
        views[section] = rendered
        if catalogue != updated:
            stale.append(CATALOGUES[section])
        if (root / VIEWS[section]).read_text() != rendered:
            stale.append(VIEWS[section])
    stale.extend(path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw)
    if check:
        if stale:
            raise ValueError("stale I/O records/files fixtures: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updates[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
    return specs


def compiler_command(compiler, std, source, output):
    compiler = Path(compiler)
    command = [str(compiler)]
    if std:
        if compiler.name.startswith("lfortran"):
            command.extend(["--std=" + std.lstrip("-").removeprefix("std=").removeprefix("std"), "--no-color"])
        elif std.startswith("-"):
            command.append(std)
        else:
            command.append("-std=" + std)
    command += [str(source), "-o", str(output)]
    return command


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compiled = subprocess.run(compiler_command(compiler, std, source, exe), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cwd=work_dir)
    if compiled.returncode != 0:
        return dict(status="compile-fail", returncode=compiled.returncode,
                    stdout=compiled.stdout, stderr=compiled.stderr)
    run = subprocess.run([str(exe)], cwd=work_dir, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = run.returncode == 0 and run.stdout == expected_stdout and run.stderr == ""
    return dict(status="pass" if passed else "run-fail", returncode=run.returncode,
                stdout=run.stdout, stderr=run.stderr)


def mutation_check(root, compiler, std, keep_work=False):
    root = Path(root)
    specs = source_specs()
    workspace_parent = root.parent / "io_records_files_mutation_runs"
    workspace_parent.mkdir(parents=True, exist_ok=True)
    work_root = Path(tempfile.mkdtemp(prefix=sha((str(compiler) + str(std)).encode())[:12] + "-", dir=workspace_parent))
    run_dirs = []

    def fresh_run_dir(label):
        safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)[:48]
        directory = Path(tempfile.mkdtemp(prefix=safe_label + "-", dir=work_root))
        run_dirs.append(directory)
        return directory

    try:
        report = []
        for spec in specs.values():
            parent = run_one_source(compiler, std, fresh_run_dir(spec["variant"] + "_parent"),
                                    spec["source"], spec["completion"], spec["variant"] + "_parent")
            parent_ok = parent["status"] == "pass"
            for index, mutation in enumerate(spec["mutations"]):
                mutant = mutated_source(spec, mutation).decode("ascii")
                observed = run_one_source(compiler, std, fresh_run_dir(f"{spec['variant']}_mut_{index:03d}"),
                                          mutant, spec["completion"],
                                          f"{spec['variant']}_mut_{index:03d}")
                failed = observed["status"] != "pass"
                report.append(dict(variant=spec["variant"], mutation=mutation["id"],
                                   category=mutation["category"], parent_ok=parent_ok,
                                   failed=failed, status=observed["status"],
                                   returncode=observed["returncode"], stdout=observed["stdout"],
                                   stderr=observed["stderr"]))
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:6], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_root, ignore_errors=True)


def counts(specs):
    return (len(specs), sum(len(set(spec["facets"])) for spec in specs.values()),
            sum(len(facets) for facets in RULE_FACETS.values()),
            sum(len(spec["mutations"]) for spec in specs.values()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogues:
        parser.error("--check and --sync-catalogues are separate operations")
    if args.mutation_check:
        if args.check or args.sync_catalogues:
            parser.error("--mutation-check is separate from generation/checking")
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        by_cat = {}
        for row in report:
            by_cat[row["category"]] = by_cat.get(row["category"], 0) + 1
        print(f"Mutation-checked {len(report)} I/O records/files mutations: " +
              ", ".join(f"{key}={by_cat[key]}" for key in sorted(by_cat)) + "; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, manifest_facets, total_facets, mutation_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} I/O records/files cases, "
          f"{total_facets} total bound facets ({manifest_facets} manifest-primary facets) and {mutation_count} mutations.")


if __name__ == "__main__":
    main()
