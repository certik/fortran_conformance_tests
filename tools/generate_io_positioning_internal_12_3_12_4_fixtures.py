#!/usr/bin/env python3
"""Generate Clause 12.3 positioning, storage-unit, and 12.4 internal-file fixtures."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "io_positioning_internal_12_3_12_4"
SECTIONS = ("12.3.4.2", "12.3.4.3", "12.3.4.4", "12.3.5", "12.4")
CATALOGUES = {
    "12.3.4.2": "doc/catalogues/advancing_nonadvancing_io_12_3_4_2.json",
    "12.3.4.3": "doc/catalogues/positioning_before_data_transfer_12_3_4_3.json",
    "12.3.4.4": "doc/catalogues/positioning_after_data_transfer_12_3_4_4.json",
    "12.3.5": "doc/catalogues/file_storage_units_12_3_5.json",
    "12.4": "doc/catalogues/internal_files_12_4.json",
}
VIEWS = {
    "12.3.4.2": "doc/fortran_2023_12_3_4_2.md",
    "12.3.4.3": "doc/fortran_2023_12_3_4_3.md",
    "12.3.4.4": "doc/fortran_2023_12_3_4_4.md",
    "12.3.5": "doc/fortran_2023_12_3_5.md",
    "12.4": "doc/fortran_2023_12_4.md",
}
VIEW_TITLES = {
    "12.3.4.2": "Advancing and nonadvancing input/output",
    "12.3.4.3": "Positioning before data transfer",
    "12.3.4.4": "Positioning after data transfer",
    "12.3.5": "File storage units",
    "12.4": "Internal files",
}

SUMMARY_BEGIN = "<!-- BEGIN IO POSITIONING INTERNAL FIXTURES -->"
SUMMARY_END = "<!-- END IO POSITIONING INTERNAL FIXTURES -->"

COMMON = r'''
module io_positioning_internal_checks
  use, intrinsic :: iso_fortran_env, only: iostat_end, iostat_eor, file_storage_size
  implicit none
  integer :: checks = 0
contains
  subroutine fail(label)
    character(len=*), intent(in) :: label
    write(*,'(a,1x,a)') 'CHECK_FAILED', label
    error stop 99
  end subroutine
  subroutine check_int(label, actual, expected)
    character(len=*), intent(in) :: label
    integer, intent(in) :: actual, expected
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_INT', label, actual, expected
      error stop 1
    end if
    checks = checks + 1
  end subroutine
  subroutine check_true(label, actual)
    character(len=*), intent(in) :: label
    logical, intent(in) :: actual
    if (.not. actual) call fail(label)
    checks = checks + 1
  end subroutine
  subroutine check_char(label, actual, expected)
    character(len=*), intent(in) :: label
    character(len=*), intent(in) :: actual, expected
    if (len(actual) /= len(expected)) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_CHAR_LEN', label, len(actual), len(expected)
      error stop 2
    end if
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,"[",a,"] [",a,"]")') 'CHECK_CHAR', label, actual, expected
      error stop 3
    end if
    checks = checks + 1
  end subroutine
  subroutine finish(expected)
    integer, intent(in) :: expected
    if (checks /= expected) then
      write(*,'(a,1x,i0,1x,i0)') 'CHECK_COUNT', checks, expected
      error stop 4
    end if
  end subroutine
end module io_positioning_internal_checks
'''.lstrip()

CASES = [
    dict(
        variant="advancing_sequential_read_order",
        rule_facets={
            "S12.3.4.2-001": ["advancing-io-positions-after-last-record"],
        },
        derivation="12.3.4.2 p1 and 12.3.4.4 p5 position an advancing sequential read after the record just read; a following read gets the next record, and BACKSPACE then rereads the preceding record.",
    ),
    dict(
        variant="nonadvancing_input_segments",
        rule_facets={
            "S12.3.4.2-002": ["nonadvancing-may-position-within-current-record", "nonadvancing-partial-record-sequence"],
        },
        derivation="12.3.4.2 p2 permits a record to be read by successive nonadvancing transfers; 12.3.4.3 p2 and 12.3.4.4 p4 leave the current record/position for the second transfer when no condition occurred.",
    ),
    dict(
        variant="nonadvancing_input_eor_next",
        rule_facets={
            "S12.3.4.4-005": ["nonadvancing-input-eor-positions-after-record"],
        },
        derivation="12.3.4.4 p4 positions after the record when nonadvancing input reaches EOR; the next sequential read therefore obtains the following distinctive record.",
    ),
    dict(
        variant="nonadvancing_output_completion",
        rule_facets={
            "S12.3.4.2-003": ["nonadvancing-output-completed-before-close", "nonadvancing-output-completed-before-backspace-endfile-rewind"],
        },
        derivation="12.3.4.2 p2 gives advancing-output effect when a partial nonadvancing output is followed by close or rewind, and 12.3.4.3 p4/12.3.4.4 p4 keep successive nonadvancing output in the current record.",
    ),
    dict(
        variant="sequential_output_truncates_following",
        rule_facets={
            "S12.3.4.3-006": ["sequential-output-current-record-becomes-last", "sequential-output-creates-new-next-last-current-record"],
        },
        derivation="12.3.4.3 p4 makes sequential output create the next record as the last record when there is no current record after an input transfer; the previous following record is no longer read before EOF.",
    ),
    dict(
        variant="direct_access_rec_positions",
        rule_facets={
            "S12.3.4.3-007": ["direct-access-position-at-rec-record"],
        },
        derivation="12.3.4.3 p5 positions direct access at the REC= record and makes it current; reads of REC=3 and REC=1 recover only those written records.",
    ),
    dict(
        variant="stream_pos_no_pos_storage",
        rule_facets={
            "S12.3.4.3-008": ["stream-access-position-before-pos-unit", "stream-access-no-pos-position-unchanged"],
        },
        derivation="12.3.4.3 p6 positions stream access by POS= or leaves it unchanged without POS=; 12.3.5 p1/p3 define file-storage-unit positions and forbid unformatted stream alignment restrictions.",
    ),
    dict(
        variant="unformatted_stream_terminal_size",
        rule_facets={
            "S12.3.4.4-003": ["unformatted-stream-position-unchanged-after-transfer", "unformatted-stream-output-extends-terminal-point"],
        },
        derivation="12.3.4.4 p2 leaves an empty unformatted stream output at the POS= position and extends the terminal point after a later positioned datum; 12.3.5 p1 makes SIZE= report file-size units.",
    ),
    dict(
        variant="iolength_storage_units",
        rule_facets={
            "S12.3.5-002": ["values-occupy-integer-file-storage-units", "unformatted-same-type-params-uniform-storage-units"],
        },
        derivation="12.3.5 p2 says IOLENGTH= determines integer file-storage units and is uniform for scalar values of the same type parameters; p4 provides FILE_STORAGE_SIZE.",
    ),
    dict(
        variant="internal_scalar_write_read",
        rule_facets={
            "S12.4-001": ["internal-file-internal-storage-transfer", "internal-file-internal-storage-conversion"],
        },
        derivation="12.4 p1-p2 define formatted transfers through character internal storage; a scalar length-eight record written with six characters is defined, converts back to integer/character values, and is blank-filled.",
    ),
    dict(
        variant="internal_array_records_position",
        rule_facets={
            "S12.4-005": ["array-internal-file-elements-are-records", "array-internal-file-record-order-array-order", "array-internal-file-records-same-element-length"],
        },
        derivation="12.4 p2 treats each character array element as a same-length scalar record in array order and positions each internal transfer at the first record.",
    ),
    dict(
        variant="internal_assignment_defined_record",
        rule_facets={
            "S12.4-011": ["internal-file-record-defined-by-assignment"],
        },
        derivation="12.4 p2 says a record can become defined by character assignment; reading the assigned scalar internal record converts the assigned fields into nondefault targets.",
    ),
]


def case_facets(case):
    return case["rule_facets"]


def all_rule_facets():
    result = {}
    for case in CASES:
        for rule, facets in case_facets(case).items():
            result.setdefault(rule, [])
            for facet in facets:
                if facet not in result[rule]:
                    result[rule].append(facet)
    return result

RULE_FACETS = all_rule_facets()


def common_program(variant, body):
    completion = "IO POSITIONING INTERNAL " + variant.upper().replace("_", " ") + " OK"
    source = COMMON + f"program fixture_{variant}\n  use io_positioning_internal_checks\n  implicit none\n" + body.strip("\n") + f"\n  call finish(@COUNT@)\n  write(*,'(a)') '{completion}'\nend program fixture_{variant}\n"
    count = source.count("call check_")
    source = source.replace("@COUNT@", str(count))
    return source, completion + "\n"


def sentinel_probes(label, old, expected, default, poison):
    return [
        (f"sentinel-{label}-remove", old, poison, "sentinel"),
        (f"sentinel-{label}-expected", old, expected, "sentinel"),
        (f"sentinel-{label}-default", old, default, "sentinel"),
    ]


def source_advancing_sequential_read_order():
    body = r'''
  integer :: u, ios, first, second, again
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(I0)') 11
  write(u,'(I0)') 22
  rewind u
  first = -7101
  call check_int('pre-first-record', first, -7101)
  read(u,*,iostat=ios) first
  call check_int('first-read-status', ios, 0)
  call check_int('first-read-value', first, 11)
  second = -7102
  call check_int('pre-second-record', second, -7102)
  read(u,*,iostat=ios) second
  call check_int('second-read-status', ios, 0)
  call check_int('second-read-value', second, 22)
  backspace u
  again = -7103
  call check_int('pre-backspace-reread', again, -7103)
  read(u,*,iostat=ios) again
  call check_int('backspace-reread-status', ios, 0)
  call check_int('backspace-reread-value', again, 22)
  close(u, status='delete')
'''
    muts = [
        ("advance-between-reads-reset", "  read(u,*,iostat=ios) first\n", "  read(u,*,iostat=ios) first\n  rewind u\n", "feature"),
        ("next-record-uses-backspace", "  rewind u\n", "  backspace u\n", "feature"),
        ("preceding-record-backspace-to-rewind", "  backspace u\n", "  rewind u\n", "feature"),
    ]
    muts += sentinel_probes("first-record", "  first = -7101\n", "  first = 11\n", "  first = 0\n", "  first = -8101\n")
    muts += sentinel_probes("second-record", "  second = -7102\n", "  second = 22\n", "  second = 0\n", "  second = -8102\n")
    muts += sentinel_probes("backspace-reread", "  again = -7103\n", "  again = 22\n", "  again = 0\n", "  again = -8103\n")
    return common_program("advancing_sequential_read_order", body), muts


def source_nonadvancing_input_segments():
    body = r'''
  integer :: u, ios, got
  character(len=3) :: first, second
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)') 'ABCDEF'
  write(u,'(A)') 'NEXT'
  rewind u
  first = '###'
  call check_char('pre-first-segment', first, '###')
  read(u,'(A3)',advance='no',size=got,iostat=ios) first
  call check_int('first-segment-status', ios, 0)
  call check_int('first-segment-size', got, 3)
  call check_char('first-segment-text', first, 'ABC')
  second = '@@@'
  call check_char('pre-second-segment', second, '@@@')
  read(u,'(A3)',advance='no',size=got,iostat=ios) second
  call check_int('second-segment-status', ios, 0)
  call check_int('second-segment-size', got, 3)
  call check_char('second-segment-text', second, 'DEF')
  close(u, status='delete')
'''
    muts = [
        ("first-read-advances", "read(u,'(A3)',advance='no',size=got,iostat=ios) first", "got = 3\n  read(u,'(A3)',iostat=ios) first", "feature"),
        ("first-segment-too-wide", "read(u,'(A3)',advance='no',size=got,iostat=ios) first", "read(u,'(A4)',advance='no',size=got,iostat=ios) first", "feature"),
        ("second-segment-too-narrow", "read(u,'(A3)',advance='no',size=got,iostat=ios) second", "read(u,'(A2)',advance='no',size=got,iostat=ios) second", "feature"),
    ]
    muts += sentinel_probes("first-segment", "  first = '###'\n", "  first = 'ABC'\n", "  first = '   '\n", "  first = '!!!'\n")
    muts += sentinel_probes("second-segment", "  second = '@@@'\n", "  second = 'DEF'\n", "  second = '   '\n", "  second = '!!!'\n")
    return common_program("nonadvancing_input_segments", body), muts


def source_nonadvancing_input_eor_next():
    body = r'''
  integer :: u, ios, got
  character(len=10) :: wide
  character(len=4) :: next
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)') 'ABCDEF'
  write(u,'(A)') 'NEXT'
  rewind u
  wide = '##########'
  call check_char('pre-wide-eor', wide, '##########')
  read(u,'(A10)',advance='no',size=got,iostat=ios) wide
  call check_int('eor-status', ios, iostat_eor)
  call check_int('eor-size', got, 6)
  call check_char('eor-padded-text', wide, 'ABCDEF    ')
  next = '@@@@'
  call check_char('pre-next-after-eor', next, '@@@@')
  read(u,'(A4)',iostat=ios) next
  call check_int('next-after-eor-status', ios, 0)
  call check_char('next-after-eor-text', next, 'NEXT')
  close(u, status='delete')
'''
    muts = [
        ("not-wide-enough-for-eor", "read(u,'(A10)',advance='no',size=got,iostat=ios) wide", "read(u,'(A3)',advance='no',size=got,iostat=ios) wide", "feature"),
        ("next-record-changed", "  write(u,'(A)') 'NEXT'\n", "  write(u,'(A)') 'LAST'\n", "feature"),
    ]
    muts += sentinel_probes("wide-eor", "  wide = '##########'\n", "  wide = 'ABCDEF    '\n", "  wide = '          '\n", "  wide = '!!!!!!!!!!'\n")
    muts += sentinel_probes("next-after-eor", "  next = '@@@@'\n", "  next = 'NEXT'\n", "  next = '    '\n", "  next = '!!!!'\n")
    return common_program("nonadvancing_input_eor_next", body), muts


def source_nonadvancing_output_completion():
    body = r'''
  integer :: u, ios
  character(len=4) :: closed_record
  character(len=3) :: rewind_record
  character(len=4) :: combined
  character(len=*), parameter :: name1 = 'batch284_nonadvancing_close.dat'
  character(len=*), parameter :: name2 = 'batch284_nonadvancing_rewind.dat'
  open(newunit=u, file=name1, status='replace', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)',advance='no') 'CLO'
  close(u)
  open(newunit=u, file=name1, status='old', access='sequential', form='formatted', action='read')
  closed_record = '####'
  call check_char('pre-closed-record', closed_record, '####')
  read(u,'(A4)',iostat=ios) closed_record
  call check_int('closed-record-status', ios, 0)
  call check_char('closed-record-text', closed_record, 'CLO ')
  close(u, status='delete')

  open(newunit=u, file=name2, status='replace', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)',advance='no') 'RE'
  rewind u
  rewind_record = '@@@'
  call check_char('pre-rewind-record', rewind_record, '@@@')
  read(u,'(A3)',iostat=ios) rewind_record
  call check_int('rewind-record-status', ios, 0)
  call check_char('rewind-record-text', rewind_record, 'RE ')
  close(u, status='delete')

  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)',advance='no') 'AA'
  write(u,'(A)',advance='no') 'BB'
  rewind u
  combined = '????'
  call check_char('pre-combined-output', combined, '????')
  read(u,'(A4)',iostat=ios) combined
  call check_int('combined-output-status', ios, 0)
  call check_char('combined-output-text', combined, 'AABB')
  close(u, status='delete')
'''
    muts = [
        ("close-completion-intervening-output", "  close(u)\n", "  write(u,'(A)',advance='no') 'X'\n  close(u)\n", "feature"),
        ("rewind-completion-intervening-output", "  rewind u\n  rewind_record = '@@@'", "  write(u,'(A)',advance='no') 'X'\n  rewind u\n  rewind_record = '@@@'", "feature"),
        ("first-output-advances", "write(u,'(A)',advance='no') 'AA'", "write(u,'(A)') 'AA'", "feature"),
        ("second-output-different-suffix", "write(u,'(A)',advance='no') 'BB'", "write(u,'(A)',advance='no') 'BC'", "feature"),
    ]
    muts += sentinel_probes("closed-record", "  closed_record = '####'\n", "  closed_record = 'CLO '\n", "  closed_record = '    '\n", "  closed_record = '!!!!'\n")
    muts += sentinel_probes("rewind-record", "  rewind_record = '@@@'\n", "  rewind_record = 'RE '\n", "  rewind_record = '   '\n", "  rewind_record = '!!!'\n")
    muts += sentinel_probes("combined-output", "  combined = '????'\n", "  combined = 'AABB'\n", "  combined = '    '\n", "  combined = '!!!!'\n")
    return common_program("nonadvancing_output_completion", body), muts


def source_sequential_output_truncates_following():
    body = r'''
  integer :: u, ios, first, rewritten, eof_probe
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(I0)') 10
  write(u,'(I0)') 20
  write(u,'(I0)') 30
  rewind u
  first = -7201
  call check_int('pre-existing-first', first, -7201)
  read(u,*,iostat=ios) first
  call check_int('existing-first-status', ios, 0)
  call check_int('existing-first-value', first, 10)
  write(u,'(I0)') 15
  rewind u
  first = -7202
  call check_int('pre-final-first', first, -7202)
  read(u,*,iostat=ios) first
  call check_int('final-first-status', ios, 0)
  call check_int('final-first-value', first, 10)
  rewritten = -7203
  call check_int('pre-rewritten-next', rewritten, -7203)
  read(u,*,iostat=ios) rewritten
  call check_int('rewritten-next-status', ios, 0)
  call check_int('rewritten-next-value', rewritten, 15)
  eof_probe = -7204
  call check_int('pre-output-eof', eof_probe, -7204)
  read(u,*,iostat=ios) eof_probe
  call check_int('output-truncated-eof', ios, iostat_end)
  close(u, status='delete')
'''
    muts = [
        ("new-output-wrong-value", "  write(u,'(I0)') 15\n", "  write(u,'(I0)') 25\n", "feature"),
        ("output-appends-after-terminal", "  read(u,*,iostat=ios) first\n  call check_int('existing-first-status'", "  read(u,*,iostat=ios) first\n  read(u,*,iostat=ios) first\n  read(u,*,iostat=ios) first\n  call check_int('existing-first-status'", "feature"),
    ]
    muts += sentinel_probes("existing-first", "  first = -7201\n", "  first = 10\n", "  first = 0\n", "  first = -8201\n")
    muts += sentinel_probes("final-first", "  first = -7202\n", "  first = 10\n", "  first = 0\n", "  first = -8202\n")
    muts += sentinel_probes("rewritten-next", "  rewritten = -7203\n", "  rewritten = 15\n", "  rewritten = 0\n", "  rewritten = -8203\n")
    muts += sentinel_probes("output-eof", "  eof_probe = -7204\n", "  eof_probe = 30\n", "  eof_probe = 0\n", "  eof_probe = -8204\n")
    return common_program("sequential_output_truncates_following", body), muts


def source_direct_access_rec_positions():
    body = r'''
  integer :: u, ios, recl, sample, selected, first
  sample = 0
  inquire(iolength=recl) sample
  open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
  write(u,rec=1) 111
  write(u,rec=3) 333
  selected = -7301
  call check_int('pre-direct-selected', selected, -7301)
  read(u,rec=3,iostat=ios) selected
  call check_int('direct-selected-status', ios, 0)
  call check_int('direct-selected-value', selected, 333)
  first = -7302
  call check_int('pre-direct-first', first, -7302)
  read(u,rec=1,iostat=ios) first
  call check_int('direct-first-status', ios, 0)
  call check_int('direct-first-value', first, 111)
  close(u, status='delete')
'''
    muts = [
        ("direct-selected-other-rec", "read(u,rec=3,iostat=ios) selected", "read(u,rec=1,iostat=ios) selected", "feature"),
        ("direct-selected-written-value", "  write(u,rec=3) 333\n", "  write(u,rec=3) 334\n", "feature"),
    ]
    muts += sentinel_probes("direct-selected", "  selected = -7301\n", "  selected = 333\n", "  selected = 0\n", "  selected = -8301\n")
    muts += sentinel_probes("direct-first", "  first = -7302\n", "  first = 111\n", "  first = 0\n", "  first = -8302\n")
    return common_program("direct_access_rec_positions", body), muts


def source_stream_pos_no_pos_storage():
    body = r'''
  integer :: u, ios, char_units, second_pos, int_value
  character(len=1) :: ch
  inquire(iolength=char_units) ch
  second_pos = 1 + char_units
  open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
  write(u,pos=1) 'A'
  write(u,pos=second_pos) 'B'
  ch = '#'
  call check_char('pre-stream-pos-second', ch, '#')
  read(u,pos=second_pos,iostat=ios) ch
  call check_int('stream-pos-second-status', ios, 0)
  call check_char('stream-pos-second-value', ch, 'B')
  ch = '@'
  call check_char('pre-stream-pos-first', ch, '@')
  read(u,pos=1,iostat=ios) ch
  call check_int('stream-pos-first-status', ios, 0)
  call check_char('stream-pos-first-value', ch, 'A')
  ch = '?'
  call check_char('pre-stream-no-pos', ch, '?')
  read(u,iostat=ios) ch
  call check_int('stream-no-pos-status', ios, 0)
  call check_char('stream-no-pos-value', ch, 'B')
  close(u, status='delete')

  open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
  write(u,pos=2) 2468
  int_value = -7401
  call check_int('pre-unaligned-integer', int_value, -7401)
  read(u,pos=2,iostat=ios) int_value
  call check_int('unaligned-integer-status', ios, 0)
  call check_int('unaligned-integer-value', int_value, 2468)
  close(u, status='delete')
'''
    muts = [
        ("stream-pos-read-first", "read(u,pos=second_pos,iostat=ios) ch", "read(u,pos=1,iostat=ios) ch", "feature"),
        ("stream-no-pos-reset", "  ch = '?'\n  call check_char('pre-stream-no-pos'", "  rewind u\n  ch = '?'\n  call check_char('pre-stream-no-pos'", "feature"),
        ("stream-second-written-value", "  write(u,pos=second_pos) 'B'\n", "  write(u,pos=second_pos) 'C'\n", "feature"),
    ]
    muts += sentinel_probes("stream-pos-second", "  ch = '#'\n", "  ch = 'B'\n", "  ch = ' '\n", "  ch = '!'\n")
    muts += sentinel_probes("stream-pos-first", "  ch = '@'\n", "  ch = 'A'\n", "  ch = ' '\n", "  ch = '!'\n")
    muts += sentinel_probes("stream-no-pos", "  ch = '?'\n", "  ch = 'B'\n", "  ch = ' '\n", "  ch = '!'\n")
    muts += sentinel_probes("unaligned-integer", "  int_value = -7401\n", "  int_value = 2468\n", "  int_value = 0\n", "  int_value = -8401\n")
    return common_program("stream_pos_no_pos_storage", body), muts


def source_unformatted_stream_terminal_size():
    body = r'''
  integer :: u, pos_after_empty, pos_after_write, size_after_write, ios
  character(len=1) :: ch
  open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
  write(u,pos=3)
  inquire(unit=u, pos=pos_after_empty)
  call check_int('empty-output-position', pos_after_empty, 3)
  write(u,pos=5) 'Z'
  inquire(unit=u, pos=pos_after_write, size=size_after_write, iostat=ios)
  call check_int('terminal-inquire-status', ios, 0)
  call check_true('terminal-size-extended', size_after_write >= 5)
  call check_true('terminal-position-after-write', pos_after_write > 5)
  ch = '#'
  call check_char('pre-terminal-readback', ch, '#')
  read(u,pos=5,iostat=ios) ch
  call check_int('terminal-readback-status', ios, 0)
  call check_char('terminal-readback-value', ch, 'Z')
  close(u, status='delete')
'''
    muts = [
        ("empty-output-other-pos", "  write(u,pos=3)\n", "  write(u,pos=4)\n", "feature"),
        ("terminal-write-other-value", "  write(u,pos=5) 'Z'\n", "  write(u,pos=5) 'Y'\n", "feature"),
    ]
    muts += sentinel_probes("terminal-readback", "  ch = '#'\n", "  ch = 'Z'\n", "  ch = ' '\n", "  ch = '!'\n")
    return common_program("unformatted_stream_terminal_size", body), muts


def source_iolength_storage_units():
    body = r'''
  integer :: units_a, units_b, units_repeat, u, ios, value
  integer :: a, b
  a = 17
  b = -23
  inquire(iolength=units_a) a
  inquire(iolength=units_b) b
  inquire(iolength=units_repeat) a
  call check_true('iolength-positive', units_a > 0)
  call check_int('same-type-uniform-units', units_b, units_a)
  call check_int('repeat-iolength-stable', units_repeat, units_a)
  call check_true('file-storage-size-positive', file_storage_size > 0)
  open(newunit=u, status='scratch', access='direct', form='unformatted', recl=units_a, action='readwrite')
  write(u,rec=1) 909
  value = -7501
  call check_int('pre-direct-recl-read', value, -7501)
  read(u,rec=1,iostat=ios) value
  call check_int('direct-recl-read-status', ios, 0)
  call check_int('direct-recl-read-value', value, 909)
  close(u, status='delete')
'''
    muts = [
        ("iolength-compare-different-expression", "  inquire(iolength=units_b) b\n", "  inquire(iolength=units_b) b, b\n", "feature"),
        ("iolength-repeat-changed", "  inquire(iolength=units_repeat) a\n", "  inquire(iolength=units_repeat) a, a\n", "feature"),
        ("direct-recl-write-other-value", "  write(u,rec=1) 909\n", "  write(u,rec=1) 808\n", "feature"),
    ]
    muts += sentinel_probes("direct-recl", "  value = -7501\n", "  value = 909\n", "  value = 0\n", "  value = -8501\n")
    return common_program("iolength_storage_units", body), muts


def source_internal_scalar_write_read():
    body = r'''
  integer :: ios, number
  character(len=8) :: record
  character(len=2) :: code
  record = '########'
  call check_char('pre-scalar-record', record, '########')
  write(record,'(I3,1X,A2)',iostat=ios) 137, 'QZ'
  call check_int('internal-write-status', ios, 0)
  call check_int('scalar-record-len', len(record), 8)
  call check_char('scalar-record-text', record, '137 QZ  ')
  call check_char('scalar-blank-fill', record(7:8), '  ')
  number = -7601
  code = '@@'
  call check_int('pre-internal-number', number, -7601)
  call check_char('pre-internal-code', code, '@@')
  read(record,'(I3,1X,A2)',iostat=ios) number, code
  call check_int('internal-read-status', ios, 0)
  call check_int('internal-number-value', number, 137)
  call check_char('internal-code-value', code, 'QZ')
'''
    muts = [
        ("internal-write-other-record", "write(record,'(I3,1X,A2)',iostat=ios) 137, 'QZ'", "write(record,'(I3,1X,A2)',iostat=ios) 246, 'QZ'", "feature"),
        ("internal-read-format-substitution", "read(record,'(I3,1X,A2)',iostat=ios) number, code", "read(record,'(I2,1X,A2)',iostat=ios) number, code", "feature"),
        ("scalar-record-length-nine", "character(len=8) :: record", "character(len=9) :: record", "feature"),
        ("blank-fill-exact-width", "write(record,'(I3,1X,A2)',iostat=ios) 137, 'QZ'", "write(record,'(I3,1X,A4)',iostat=ios) 137, 'QZ!!'", "feature"),
    ]
    muts += sentinel_probes("internal-number", "  number = -7601\n", "  number = 137\n", "  number = 0\n", "  number = -8601\n")
    muts += sentinel_probes("internal-code", "  code = '@@'\n", "  code = 'QZ'\n", "  code = '  '\n", "  code = '!!'\n")
    return common_program("internal_scalar_write_read", body), muts


def source_internal_array_records_position():
    body = r'''
  integer :: ios
  character(len=5) :: records(3), first_again, first_third
  records = '@@@@@'
  call check_char('pre-array-record-one', records(1), '@@@@@')
  write(records,'(A)') 'AA', 'BB', 'CC'
  call check_int('array-record-len-one', len(records(1)), 5)
  call check_char('array-record-one-text', records(1), 'AA   ')
  call check_char('array-record-two-text', records(2), 'BB   ')
  call check_char('array-record-three-text', records(3), 'CC   ')
  first_again = '#####'
  call check_char('pre-array-read-first', first_again, '#####')
  read(records,'(A)',iostat=ios) first_again
  call check_int('array-read-first-status', ios, 0)
  call check_char('array-read-first-text', first_again, 'AA   ')
  first_third = '?????'
  call check_char('pre-array-reread-first', first_third, '?????')
  read(records,'(A)',iostat=ios) first_third
  call check_int('array-reread-first-status', ios, 0)
  call check_char('array-reread-first-text', first_third, 'AA   ')
'''
    muts = [
        ("array-write-starts-second", "write(records,'(A)') 'AA', 'BB', 'CC'", "write(records(2:3),'(A)') 'AA', 'BB'", "feature"),
        ("array-write-reversed-section", "write(records,'(A)') 'AA', 'BB', 'CC'", "write(records(3:1:-1),'(A)') 'AA', 'BB', 'CC'", "feature"),
        ("array-record-length-six", "character(len=5) :: records(3), first_again, first_third", "character(len=6) :: records(3), first_again, first_third", "feature"),
        ("array-reread-second-record", "read(records,'(A)',iostat=ios) first_third", "read(records(2:3),'(A)',iostat=ios) first_third", "feature"),
    ]
    muts += sentinel_probes("array-read-first", "  first_again = '#####'\n", "  first_again = 'AA   '\n", "  first_again = '     '\n", "  first_again = '!!!!!'\n")
    muts += sentinel_probes("array-reread-first", "  first_third = '?????'\n", "  first_third = 'AA   '\n", "  first_third = '     '\n", "  first_third = '!!!!!'\n")
    return common_program("internal_array_records_position", body), muts


def source_internal_assignment_defined_record():
    body = r'''
  integer :: ios, number
  character(len=5) :: record
  character(len=1) :: tag
  record = '246 R'
  call check_char('assigned-record-text', record, '246 R')
  number = -7701
  tag = '#'
  call check_int('pre-assigned-number', number, -7701)
  call check_char('pre-assigned-tag', tag, '#')
  read(record,'(I3,1X,A1)',iostat=ios) number, tag
  call check_int('assigned-read-status', ios, 0)
  call check_int('assigned-number-value', number, 246)
  call check_char('assigned-tag-value', tag, 'R')
'''
    muts = [
        ("assignment-record-other-value", "  record = '246 R'\n", "  record = '135 S'\n", "feature"),
        ("assignment-read-format-substitution", "read(record,'(I3,1X,A1)',iostat=ios) number, tag", "read(record,'(I2,1X,A1)',iostat=ios) number, tag", "feature"),
    ]
    muts += sentinel_probes("assigned-number", "  number = -7701\n", "  number = 246\n", "  number = 0\n", "  number = -8701\n")
    muts += sentinel_probes("assigned-tag", "  tag = '#'\n", "  tag = 'R'\n", "  tag = ' '\n", "  tag = '!'\n")
    return common_program("internal_assignment_defined_record", body), muts


SOURCE_BUILDERS = {name.removeprefix("source_"): obj for name, obj in list(globals().items()) if name.startswith("source_")}

ORACLE_PREFIX = {rule: f"{rule} I/O positioning/internal runtime fixtures: " for rule in RULE_FACETS}
LIMIT_PREFIX = {rule: f"{rule} I/O positioning/internal fixture boundaries: " for rule in RULE_FACETS}
POSITIVE_CONTROL_RULES = set()

RESTORED_PENDING = {}

GENERIC_PENDING = "Pending after batch284 review: no distinct fixture with its own facet-specific assertion and feature mutation is shipped in this packet."


LIMIT_PARAGRAPH = (
    "These fixtures are finite single-image positive runtime observations over scratch or local external files "
    "and character internal files. They assert only exact integers, logical inequalities, exact characters with LEN "
    "checks, IOSTAT zero, IOSTAT_END/EOR named constants, IOLENGTH=/POS=/SIZE= values or inequalities derived from "
    "the executing processor, and FILE_STORAGE_SIZE positivity. They do not assert physical byte encodings, record-marker "
    "layout, IOMSG text, processor-specific numeric error statuses, unsupported deferred-length internal WRITE behavior, "
    "or diagnostics for unnumbered restrictions."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(rule, variant):
    return rule.replace('.', '_').replace('-', '_') + "_valid__" + TOPIC + "_" + variant


def source_specs():
    specs = {}
    for case in CASES:
        variant = case["variant"]
        (source, completion), mut_specs = SOURCE_BUILDERS[variant]()
        raw = source.encode("ascii")
        mutations = []
        for mid, expected, replacement, category in mut_specs:
            if source.count(expected) != 1:
                raise ValueError(f"{variant}: mutation span {mid} count is {source.count(expected)}")
            start = source.index(expected)
            mutations.append(dict(id=mid, expected=expected, replacement=replacement, category=category,
                                  span=[start, start + len(expected)], line=source[:start].count("\n") + 1))
        for rule, facets in case_facets(case).items():
            name = identifier(rule, variant)
            specs[name] = dict(id=name, variant=variant, rule=rule, facets=list(facets), source=source,
                               source_sha256=sha(raw), mutations=mutations, completion=completion,
                               derivation=case["derivation"], rule_facets=case_facets(case))
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("source fingerprint mismatch")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span mismatch")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (TOPIC + "_" + spec["variant"] + "__" + spec["rule"].replace('.', '_').replace('-', '_'))
        evidence = "positive-control" if spec["rule"] in POSITIVE_CONTROL_RULES else "effect"
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence=evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["source_path"] = directory.relative_to(root).as_posix() + "/source.f90"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    hits = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(hits) > 1:
        raise ValueError("duplicate owned paragraph")
    if hits:
        paragraphs[hits[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def pending_note(rule, facet):
    if rule == "S12.4-007":
        return ("Reference gfortran 16.1.0 on this host raises a runtime end-of-file for the F2023 deferred-length "
                "allocatable scalar internal WRITE rule while frozen LFortran succeeds; no reference-validated fixture ships in this packet.")
    if rule == "S12.4-013":
        return "No fixture in this packet depends on a 12.5.2 connection-mode default; leave pending until those modes are registered."
    return None


def synced_catalogue(section, catalogue, specs=None):
    if specs is None:
        specs = source_specs()
    result = copy.deepcopy(catalogue)
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for req in result["requirements"]:
        rule = req["id"]
        req.setdefault("pending", {})
        for facet in req["facets"]:
            if facet not in covered.get(rule, set()) and facet not in req["pending"]:
                req["pending"][facet] = pending_note(rule, facet) or GENERIC_PENDING
        if rule in RESTORED_PENDING:
            req["pending"].update(RESTORED_PENDING[rule])
        for facet in sorted(covered.get(rule, set())):
            if facet not in req["facets"]:
                raise ValueError(f"unknown facet {facet} for {rule}")
            req.get("pending", {}).pop(facet, None)
        for facet in list(req.get("pending", {})):
            note = pending_note(rule, facet)
            if note:
                req["pending"][facet] = note
        if covered.get(rule):
            labels = ", ".join(f"`{facet}`" for facet in sorted(covered[rule]))
            para = ORACLE_PREFIX[rule] + f"valid run-phase fixtures cover {labels}. " + LIMIT_PARAGRAPH
            req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIX[rule], para)
            req["oracle_limitation"] = owned_paragraph(req.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMIT_PREFIX[rule] + LIMIT_PARAGRAPH)
    return result


def summary_text(specs):
    represented = sum(len(set(spec["facets"])) for spec in specs.values())
    cases = len({spec["variant"] for spec in specs.values()})
    return (SUMMARY_BEGIN + "\n"
            "## I/O positioning, file-storage-unit, and internal-file fixtures\n\n"
            f"This packet adds {cases} runtime programs and {len(specs)} rule-bound manifests representing "
            f"{represented} selected facets in 12.3.4.2, 12.3.4.3, 12.3.4.4, 12.3.5, and 12.4. "
            "The programs use scratch or local files deleted by the program and character internal files. "
            "READ targets use nondefault sentinels and pre-READ guards; stream positions are derived with "
            "IOLENGTH=, POS=, and SIZE= inquiries; character equality checks first compare LEN. Deferred-length "
            "allocatable internal WRITE facets remain pending because the reference compiler does not validate them.\n"
            + SUMMARY_END)


def render_view(section, catalogue, specs, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import Registry, render_requirement
    registry = Registry(root)
    registry.catalogues[section] = catalogue
    selected = [s for s in specs.values() if s["rule"] in {r["id"] for r in catalogue["requirements"]}]
    represented = sum(len(s["facets"]) for s in selected)
    total = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r.get("pending", {})) for r in catalogue["requirements"])
    text = (f"# Fortran 2023 {section}: {VIEW_TITLES[section]} - I/O positioning/internal fixtures\n\n"
            f"The canonical catalogue is `{CATALOGUES[section]}`. This author packet adds finite runtime fixtures; "
            "fixture approval remains separate.\n\n"
            "Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256 "
            "`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.\n\n"
            f"**Catalogue source review: {registry.catalogue_review_state(section)}.** "
            f"This topic represents {represented} facets in {len(selected)} rule-bound manifest(s); "
            f"{total - pending} of {total} facets are represented and {pending} remain pending.\n\n"
            f"<!-- BEGIN GENERATED {section} -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"])
    text += f"\n<!-- END GENERATED {section} -->\n\n"
    text += summary_text(specs) + "\n\n"
    for spec in selected:
        text += f"### `{spec['variant']}` / `{spec['rule']}`\n\n"
        text += "**Facets:** " + ", ".join(f"`{f}`" for f in spec["facets"]) + ".\n\n"
        text += spec["derivation"] + "\n\n"
        text += "Feature/sentinel mutations: " + ", ".join(f"`{m['id']}`" for m in spec["mutations"]) + ".\n\n"
    return text.rstrip() + "\n"


def sync_files(files, specs):
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for section, cat_path in CATALOGUES.items():
        path = ROOT / cat_path
        updated = synced_catalogue(section, json.loads(path.read_text()), specs)
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
        current = json.loads((ROOT / cat_path).read_text())
        expected = synced_catalogue(section, current, specs)
        if current != expected:
            stale.append(cat_path)
        view = render_view(section, expected, specs)
        if not (ROOT / VIEWS[section]).is_file() or (ROOT / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    if stale:
        raise SystemExit("stale io_positioning_internal packet: " + ", ".join(stale))


def compiler_command(compiler, std):
    if "lfortran" in Path(compiler).name.lower():
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std, keep=False):
    _, specs = build_corpus(ROOT)
    unique = {}
    for spec in specs.values():
        unique.setdefault(spec["variant"], spec)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / (".mutation_" + TOPIC) / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    try:
        for spec in unique.values():
            for mutation in spec["mutations"]:
                total += 1
                mutated = mutated_source(spec, mutation).decode("ascii")
                work = base / spec["variant"] / mutation["id"]
                work.mkdir(parents=True)
                src = work / "source.f90"
                exe = work / "program"
                src.write_text(mutated)
                built = subprocess.run(compiler_command(compiler, std) + [str(src), "-o", str(exe)], cwd=work,
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)
                if built.returncode != 0:
                    raise SystemExit(f"{spec['variant']}/{mutation['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=45)
                if ran.returncode == 0:
                    raise SystemExit(f"{spec['variant']}/{mutation['id']}: mutant survived")
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
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-mutation-work", action="store_true")
    args = parser.parse_args()
    if args.check and args.mutation_check:
        parser.error("choose one mode")
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
    print(f"{action} {len(files)} files for {len(specs)} manifests and {sum(len(s['facets']) for s in specs.values())} facets.")


if __name__ == "__main__":
    main()
