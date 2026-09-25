#!/usr/bin/env python3
"""Generate Fortran 2023 12.10.1/12.10.2.1 INQUIRE fixtures."""
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
TOPIC = "io_inquire_12_10_1"
SECTIONS = ("12.10.1", "12.10.2.1")
CATALOGUES = {
    "12.10.1": "doc/catalogues/inquire_statement_general_12_10_1.json",
    "12.10.2.1": "doc/catalogues/inquiry_specifier_list_12_10_2_1.json",
}
EVIDENCE_LINKS_PATH = "doc/evidence/canonical_case_links.json"
VIEWS = {
    "12.10.1": "doc/fortran_2023_12_10_1.md",
    "12.10.2.1": "doc/fortran_2023_12_10_2_1.md",
}
SUMMARY_BEGIN = "<!-- BEGIN IO INQUIRE 12.10.1 FIXTURES -->"
SUMMARY_END = "<!-- END IO INQUIRE 12.10.1 FIXTURES -->"

RULE_FACETS = {
    "S12.10.1-001": ["inquire-by-file-form", "inquire-by-unit-form", "inquire-by-output-list-form"],
    "S12.10.1-002": ["inquire-character-padding", "inquire-character-truncation",
                       "inquire-numeric-logical-assignment"],
    "S12.10.1-003": ["inquire-unit-need-not-be-connected"],
    "S12.10.1-004": ["unit-inquiry-connection-properties", "unit-inquiry-connected-file-properties"],
    "S12.10.1-005": ["inquire-file-need-not-exist", "inquire-file-need-not-be-connected"],
    "S12.10.1-006": ["file-inquiry-connection-properties", "file-inquiry-connected-file-properties"],
    "S12.10.1-007": ["inquire-before-connection", "inquire-during-connection",
                       "inquire-after-connection"],
    "S12.10.1-008": ["inquire-values-current-at-execution"],
    "R1230": ["inquire-spec-list-form", "inquire-iolength-output-list-form"],
    "S12.10.2.1-001": ["specifier-usable-by-file-form", "specifier-usable-by-unit-form"],
    "R1231": [
        "inquire-spec-unit", "inquire-spec-file", "inquire-spec-access", "inquire-spec-action",
        "inquire-spec-asynchronous", "inquire-spec-blank", "inquire-spec-decimal",
        "inquire-spec-delim", "inquire-spec-direct", "inquire-spec-encoding",
        "inquire-spec-exist", "inquire-spec-form", "inquire-spec-formatted",
        "inquire-spec-iostat", "inquire-spec-name", "inquire-spec-named",
        "inquire-spec-nextrec", "inquire-spec-number", "inquire-spec-opened",
        "inquire-spec-pad", "inquire-spec-pending", "inquire-spec-pos",
        "inquire-spec-position", "inquire-spec-read", "inquire-spec-readwrite",
        "inquire-spec-recl", "inquire-spec-round", "inquire-spec-sequential",
        "inquire-spec-sign", "inquire-spec-size", "inquire-spec-stream",
        "inquire-spec-unformatted", "inquire-spec-write",
    ],
    "C1247": ["duplicate-inquire-specifier-rejected"],
    "C1248": ["inquire-file-or-unit-required", "inquire-file-and-unit-mutually-exclusive"],
    "C1249": ["positional-inquire-unit-first"],
    "C1250": ["id-requires-pending"],
    "C1251": ["inquire-err-label-branch-target", "inquire-err-label-same-inclusive-scope"],
    "S12.10.2.1-003": ["character-inquiry-results-uppercase-except-name"],
}

RESTORED_PENDING = {
    ("S12.10.1-003", "inquire-unit-need-not-exist"):
        "Left pending: 12.5.1 requires ordinary file-unit-number values to be nonnegative "
        "or otherwise valid, and both reference processors report all probed nonnegative "
        "external unit numbers as existing; no conforming single-image fixture can force "
        "a nonexistent-but-valid unit value on this host.",
    ("R1231", "inquire-spec-err"):
        "Left pending: ERR= is exercised only as the one-property control/negative pair for "
        "C1251; no non-vacuous R1231 syntax fixture has a portable runtime assertion that "
        "distinguishes the presence of ERR= on a successful INQUIRE.",
    ("R1231", "inquire-spec-id"):
        "Left pending: ID= is exercised only as the one-property control/negative pair for "
        "C1250, and frozen LFortran rejects the conforming ID= plus PENDING= control. No "
        "reference-validated non-vacuous R1231 feature mutant is available for this syntax "
        "alternative in this packet.",
    ("R1231", "inquire-spec-iomsg"):
        "Left pending: successful INQUIRE gives no portable IOMSG text oracle, and error "
        "message text is processor dependent; a non-vacuous syntax fixture for IOMSG= needs "
        "a portable assignment property beyond merely compiling the variable form.",
    ("R1231", "inquire-spec-leading-zero"):
        "Left pending: the reference gfortran on this host rejects LEADING_ZERO= in INQUIRE, "
        "so no reference-validated fixture can be shipped for this R1231 alternative.",
}

RULE_SECTION = {rule: "12.10.1" for rule in RULE_FACETS if rule == "R1230" or rule.startswith("S12.10.1")}
RULE_SECTION.update({rule: "12.10.2.1" for rule in RULE_FACETS if rule not in RULE_SECTION})

DIRECT_RUNTIME_RULES = {
    "S12.10.1-001": "forms_timing",
    "R1230": "syntax_forms",
    "R1231": "specifier_assignments",
}

LINKED_RUNTIME_RULES = {
    "S12.10.1-002": "forms_timing",
    "S12.10.1-003": "forms_timing",
    "S12.10.1-004": "forms_timing",
    "S12.10.1-005": "forms_timing",
    "S12.10.1-006": "forms_timing",
    "S12.10.1-007": "forms_timing",
    "S12.10.1-008": "forms_timing",
    "S12.10.2.1-001": "specifier_assignments",
    "S12.10.2.1-003": "specifier_assignments",
}

PRIMARY_RULE = {"forms_timing": "S12.10.1-001", "syntax_forms": "R1230", "specifier_assignments": "R1231"}
PRIMARY_SOURCE = {
    "forms_timing": "12.10.1#p1.inquiry-forms",
    "syntax_forms": "12.10.1#R1230",
    "specifier_assignments": "12.10.2.1#R1231",
}

INVALID_CASES = [
    dict(rule="C1247", facet="duplicate-inquire-specifier-rejected", variant="duplicate_opened_specifier",
         source="""program p
logical :: opened
inquire(unit=10, opened=opened, opened=opened)
end program p
""", line=3, contains=["duplicate", "already", "specified"],
         control="duplicate_opened_specifier_control",
         derivation="C1247 prohibits repeating one specifier; the control removes only the second OPENED=."),
    dict(rule="C1248", facet="inquire-file-or-unit-required", variant="missing_file_or_unit",
         source="""program p
logical :: opened
inquire(opened=opened)
end program p
""", line=3, contains=["FILE", "UNIT", "specifier", "specified"],
         control="missing_file_or_unit_control",
         derivation="C1248 requires one FILE= or file-unit-number; the control adds only UNIT=10."),
    dict(rule="C1248", facet="inquire-file-and-unit-mutually-exclusive", variant="file_and_unit_together",
         source="""program p
logical :: opened
inquire(unit=10, file='io_inquire_both.dat', opened=opened)
end program p
""", line=3, contains=["both", "FILE", "UNIT"],
         control="file_and_unit_together_control",
         derivation="C1248 prohibits FILE= and file-unit-number together; the control removes only UNIT=."),
    dict(rule="C1249", facet="positional-inquire-unit-first", variant="positional_unit_not_first",
         source="""program p
logical :: opened
inquire(opened=opened, 10)
end program p
""", line=3, contains=["syntax", "unexpected", "inquire"],
         control="positional_unit_not_first_control",
         derivation="C1249 requires an omitted-UNIT positional file-unit-number to be first."),
    dict(rule="C1250", facet="id-requires-pending", variant="id_without_pending",
         source="""program p
logical :: opened
inquire(unit=10, id=1, opened=opened)
end program p
""", line=3, contains=["PENDING", "id", "Invalid"],
         control="id_without_pending_control",
         derivation="C1250 requires PENDING= whenever ID= appears; the control adds only PENDING=."),
    dict(rule="C1251", facet="inquire-err-label-branch-target", variant="err_label_format_target",
         source="""program p
logical :: opened
inquire(unit=10, opened=opened, err=10)
10 format('not a branch target')
end program p
""", line=4, contains=["branch", "target", "label"],
         control="err_label_format_target_control",
         derivation="C1251 requires ERR= to name a branch target; FORMAT is not a branch target statement."),
    dict(rule="C1251", facet="inquire-err-label-same-inclusive-scope", variant="err_label_other_scope",
         source="""program p
logical :: opened
inquire(unit=10, opened=opened, err=20)
contains
subroutine target_scope()
20 continue
end subroutine target_scope
end program p
""", line=3, contains=["Label", "defined", "scope"],
         control="err_label_other_scope_control",
         derivation="C1251 requires the ERR= branch target to appear in the same inclusive scope."),
]

CONTROLS = {
    "duplicate_opened_specifier_control": ("C1247", ["duplicate-inquire-specifier-rejected"], """program p
logical :: opened
inquire(unit=10, opened=opened)
end program p
"""),
    "missing_file_or_unit_control": ("C1248", ["inquire-file-or-unit-required"], """program p
logical :: opened
inquire(unit=10, opened=opened)
end program p
"""),
    "file_and_unit_together_control": ("C1248", ["inquire-file-and-unit-mutually-exclusive"], """program p
logical :: opened
inquire(file='io_inquire_both.dat', opened=opened)
end program p
"""),
    "positional_unit_not_first_control": ("C1249", ["positional-inquire-unit-first"], """program p
logical :: opened
inquire(10, opened=opened)
end program p
"""),
    "id_without_pending_control": ("C1250", ["id-requires-pending"], """program p
logical :: pending
inquire(unit=10, id=1, pending=pending)
end program p
"""),
    "err_label_format_target_control": ("C1251", ["inquire-err-label-branch-target"], """program p
logical :: opened
inquire(unit=10, opened=opened, err=10)
10 continue
end program p
"""),
    "err_label_other_scope_control": ("C1251", ["inquire-err-label-same-inclusive-scope"], """program p
logical :: opened
inquire(unit=10, opened=opened, err=20)
20 continue
end program p
"""),
}

ORACLE_PREFIX = {rule: f"{rule} INQUIRE 12.10.1 fixture implementation: " for rule in RULE_FACETS}
LIMIT_PREFIX = {rule: f"{rule} INQUIRE 12.10.1 fixture boundaries: " for rule in RULE_FACETS}

ORACLE_PARAGRAPHS = {
    "S12.10.1-001": ORACLE_PREFIX["S12.10.1-001"] +
        "the forms/timing fixture executes INQUIRE by FILE= before/after creating a named file, by UNIT= on "
        "connected and unconnected units, and by IOLENGTH= on an integer output list whose returned length is "
        "used as a direct unformatted RECL= value.",
    "S12.10.1-002": ORACLE_PREFIX["S12.10.1-002"] +
        "the same fixture initializes every inquiry target to a nonmatching sentinel, checks the sentinel before "
        "INQUIRE, then observes logical OPENED/EXIST and integer NUMBER assignments plus FORM padding and ACCESS "
        "truncation under intrinsic assignment rules.",
    "S12.10.1-003": ORACLE_PREFIX["S12.10.1-003"] +
        "a real external unit is first opened and closed, then INQUIRE(UNIT=...) reports OPENED=.false. without "
        "assuming the unit is nonexistent. The nonexistent-unit permission remains pending because no conforming "
        "nonnegative valid unit value that reports EXIST=.false. is available on the reference processors.",
    "S12.10.1-004": ORACLE_PREFIX["S12.10.1-004"] +
        "a connected named stream/formatted unit reports OPENED=.true., NUMBER equal to the unit, and fixed "
        "ACCESS/ACTION/FORM/NAMED properties; the returned NAME is used only as an OPEN FILE= value.",
    "S12.10.1-005": ORACLE_PREFIX["S12.10.1-005"] +
        "a controlled absent file reports EXIST=.false./OPENED=.false.; the same name after close(STATUS='KEEP') "
        "reports EXIST=.true./OPENED=.false.",
    "S12.10.1-006": ORACLE_PREFIX["S12.10.1-006"] +
        "while the controlled name is connected on exactly one unit, INQUIRE(FILE=...) reports OPENED=.true., "
        "NUMBER equal to that unit, and the fixed FORM token.",
    "S12.10.1-007": ORACLE_PREFIX["S12.10.1-007"] +
        "three FILE= inquiries around the OPEN/CLOSE transition observe before, during, and after states with "
        "fresh sentinel initialization for each target.",
    "S12.10.1-008": ORACLE_PREFIX["S12.10.1-008"] +
        "the OPENED= target is reset before each of the before/during/after inquiries and changes false/true/false, "
        "so stale target values cannot satisfy the oracle.",
    "R1230": ORACLE_PREFIX["R1230"] +
        "the positive-control source contains both R1230 forms, INQUIRE(inquire-spec-list) and "
        "INQUIRE(IOLENGTH=scalar-int-variable) output-list; feature mutants redirect the designator or IOLENGTH target.",
    "S12.10.2.1-001": ORACLE_PREFIX["S12.10.2.1-001"] +
        "the specifier fixture uses selected inquiry specifiers in both UNIT= and FILE= forms, with sentinel guarded "
        "targets and exact OPENED/NUMBER observations where the source fixes them.",
    "R1231": ORACLE_PREFIX["R1231"] +
        "the specifier fixture positively exercises all reference-validated R1231 alternatives except ERR=, ID=, "
        "IOMSG=, and LEADING_ZERO=. Each claimed target has a sentinel guard and a feature mutant that redirects "
        "that specifier away from the asserted target or changes the governing connection feature. ERR=/ID= "
        "remain pending for R1231 because the shipped C1250/C1251 diagnostic controls exercise those spellings "
        "only as constraint repairs, not as non-vacuous R1231 syntax-oracle fixtures.",
    "C1247": ORACLE_PREFIX["C1247"] +
        "the negative duplicates only OPENED= in an otherwise valid UNIT inquiry, and the paired control removes "
        "only the duplicate specifier.",
    "C1248": ORACLE_PREFIX["C1248"] +
        "one negative omits both designators and one supplies both UNIT= and FILE=; controls repair exactly the "
        "missing/excess designator property.",
    "C1249": ORACLE_PREFIX["C1249"] +
        "the negative places a positional file-unit-number after OPENED=, while the control moves that same "
        "positional unit to the first position.",
    "C1250": ORACLE_PREFIX["C1250"] +
        "the negative uses ID= without PENDING=, while the control adds only PENDING=. The frozen LFortran target "
        "currently rejects the valid control, which is reported as a compiler defect.",
    "C1251": ORACLE_PREFIX["C1251"] +
        "one negative targets a FORMAT label and one targets a label in a contained subprogram; controls use "
        "same-scope CONTINUE branch targets.",
    "S12.10.2.1-003": ORACLE_PREFIX["S12.10.2.1-003"] +
        "lowercase OPEN mode spellings are inquired through character specifiers other than NAME= and observed as "
        "upper-case tokens such as READWRITE, STREAM, ZERO, and FORMATTED.",
}

LIMIT_PARAGRAPH = (
    "These fixtures assert only exact logical/integer values fixed by 12.10.2, exact upper-case tokens fixed by "
    "the individual specifier rules, changed-from-sentinel assignment where a token is processor dependent, and "
    "IOLENGTH suitability as a RECL= value. They do not compare NAME spelling or case, IOMSG text, numeric nonzero "
    "IOSTAT codes, processor-dependent file sizes, ambiguous multiple-unit NUMBER choices, or undefined inquiry "
    "variables. ERR=, ID=, IOMSG=, LEADING_ZERO= syntax facets and internal-unit/error-variable effect facets remain "
    "pending unless covered by the diagnostic controls named here."
)

COMPLETIONS = {
    "forms_timing": "IO INQUIRE FORMS TIMING OK\n",
    "syntax_forms": "IO INQUIRE SYNTAX FORMS OK\n",
    "specifier_assignments": "IO INQUIRE SPECIFIER ASSIGNMENTS OK\n",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rule_slug(rule):
    return rule.replace(".", "_").replace("-", "_")


def case_id(rule, variant, kind="valid"):
    return f"{rule_slug(rule)}_{kind}__{TOPIC}_{variant}"


def program_name(variant):
    return "p_" + variant


def common_helpers(variant):
    completion = COMPLETIONS[variant].strip()
    return f"""
contains
  subroutine pass(label)
    character(len=*), intent(in) :: label
    checks = checks + 1
  end subroutine pass
  subroutine expect_int(value, expected, label)
    integer, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'IOINQ:int', label, value, expected
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int
  subroutine expect_int_not(value, forbidden, label)
    integer, intent(in) :: value, forbidden
    character(len=*), intent(in) :: label
    if (value == forbidden) then
      write(*,'(a,1x,a,1x,i0)') 'IOINQ:int-not', label, value
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int_not
  subroutine expect_positive(value, label)
    integer, intent(in) :: value
    character(len=*), intent(in) :: label
    if (value <= 0) then
      write(*,'(a,1x,a,1x,i0)') 'IOINQ:positive', label, value
      error stop 1
    end if
    call pass(label)
  end subroutine expect_positive
  subroutine expect_logical(value, expected, label)
    logical, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value .neqv. expected) then
      write(*,'(a,1x,a)') 'IOINQ:logical', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_logical
  subroutine expect_char(value, expected, label)
    character(len=*), intent(in) :: value, expected, label
    if (len(value) /= len(expected)) then
      write(*,'(a,1x,a)') 'IOINQ:char-len', label
      error stop 1
    end if
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IOINQ:char', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char
  subroutine expect_char_not(value, forbidden, label)
    character(len=*), intent(in) :: value, forbidden, label
    if (len(value) /= len(forbidden)) then
      write(*,'(a,1x,a)') 'IOINQ:char-not-len', label
      error stop 1
    end if
    if (value == forbidden) then
      write(*,'(a,1x,a)') 'IOINQ:char-not', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char_not
  subroutine cleanup_name(name)
    character(len=*), intent(in) :: name
    integer :: cu, cios
    logical :: ex
    inquire(file=name, exist=ex)
    if (ex) then
      open(newunit=cu, file=name, status='old', iostat=cios)
      if (cios == 0) close(cu, status='delete')
    end if
  end subroutine cleanup_name
  subroutine finish()
    if (checks /= EXPECTED_CHECKS) then
      write(*,'(a,1x,i0,1x,i0)') 'IOINQ:check-total', checks, EXPECTED_CHECKS
      error stop 1
    end if
    write(*,'(a)') '{completion}'
  end subroutine finish
end program {program_name(variant)}
"""


def with_expected_checks(source):
    count = source.count("call expect_")
    return source.replace("EXPECTED_CHECKS", str(count))


def add_mutation(mutations, mid, source, expected, replacement, category="feature"):
    if expected not in source:
        raise ValueError(f"missing mutation span {mid}: {expected!r}")
    if source.count(expected) != 1:
        raise ValueError(f"nonunique mutation span {mid}: {expected!r}")
    start = source.index(expected)
    mutations.append(dict(id=mid, category=category, expected=expected, replacement=replacement,
                          span=[start, start + len(expected)], line=source[:start].count("\n") + 1))


def add_sentinel_mutations(source, mutations):
    for line in source.splitlines(True):
        if "! sentinel-probe:" not in line:
            continue
        code, marker = line.split("! sentinel-probe:", 1)
        ident, poison, default = marker.strip().split(":")
        old = line
        add_mutation(mutations, ident + "-remove-sentinel", source, old, poison + "\n",
                     "sentinel-init-remove")
        add_mutation(mutations, ident + "-poison-sentinel", source, old, poison + "\n",
                     "sentinel-init-expected")
        add_mutation(mutations, ident + "-default-sentinel", source, old, default + "\n",
                     "sentinel-init-default")


def source_forms_timing():
    variant = "forms_timing"
    body = """program p_forms_timing
  implicit none
  integer :: checks, u, again, du, iol, values(2), got(2), ios, unconnected_unit
  integer :: number_before, number_keep, number_unit, number_file_live
  integer :: number_after
  logical :: exists_before, opened_before, exists_keep, opened_keep, opened_unit, named_unit
  logical :: opened_file_live, exists_after, opened_after, opened_unconnected
  logical :: opened_current
  character(len=25) :: name_before, name_keep, name_direct
  character(len=12) :: form_long, access_unit, action_unit, form_unit, form_file_live
  character(len=2) :: access_short
  character(len=80) :: name_from_unit
  checks = 0
  name_before = 'io_inquire_before.dat'
  name_keep = 'io_inquire_keep.dat'
  name_direct = 'io_inquire_direct.dat'
  call cleanup_name(name_before)
  call cleanup_name(name_keep)
  call cleanup_name(name_direct)

  exists_before = .false.
  exists_before = .true. ! sentinel-probe:exists-before:  exists_before = .false.:  exists_before = .false.
  call expect_logical(exists_before, .true., 'exists-before-pre')
  opened_before = .false.
  opened_before = .true. ! sentinel-probe:opened-before:  opened_before = .false.:  opened_before = .false.
  call expect_logical(opened_before, .true., 'opened-before-pre')
  number_before = 0
  number_before = -777 ! sentinel-probe:number-before:  number_before = -1:  number_before = 0
  call expect_int(number_before, -777, 'number-before-pre')
  inquire(file=name_before, exist=exists_before, opened=opened_before, number=number_before)
  call expect_logical(exists_before, .false., 'exists-before-false')
  call expect_logical(opened_before, .false., 'opened-before-false')
  call expect_int(number_before, -1, 'number-before-minus-one')

  open(newunit=u, file=name_keep, status='replace', access='stream', form='formatted', &
       action='readwrite', iostat=ios)
  call expect_int(ios, 0, 'open-keep-status')
  write(u,'(a)', iostat=ios) 'alpha'
  call expect_int(ios, 0, 'write-keep-status')
  close(u, status='keep', iostat=ios)
  call expect_int(ios, 0, 'close-keep-status')

  exists_keep = .false. ! sentinel-probe:exists-keep:  exists_keep = .true.:  exists_keep = .true.
  call expect_logical(exists_keep, .false., 'exists-keep-pre')
  opened_keep = .true. ! sentinel-probe:opened-keep:  opened_keep = .false.:  opened_keep = .false.
  call expect_logical(opened_keep, .true., 'opened-keep-pre')
  number_keep = 0
  number_keep = -777 ! sentinel-probe:number-keep:  number_keep = -1:  number_keep = 0
  call expect_int(number_keep, -777, 'number-keep-pre')
  inquire(file=name_keep, exist=exists_keep, opened=opened_keep, number=number_keep)
  call expect_logical(exists_keep, .true., 'exists-keep-true')
  call expect_logical(opened_keep, .false., 'opened-keep-false')
  call expect_int(number_keep, -1, 'number-keep-minus-one')

  open(newunit=u, file=name_keep, status='old', access='stream', form='formatted', &
       action='readwrite', iostat=ios)
  call expect_int(ios, 0, 'open-live-status')
  opened_current = .true. ! sentinel-probe:opened-current-live:  opened_current = .false.:  opened_current = .false.
  call expect_logical(opened_current, .true., 'opened-current-live-pre')
  inquire(file=name_keep, opened=opened_current)
  call expect_logical(opened_current, .true., 'opened-current-live')

  opened_unit = .false. ! sentinel-probe:opened-unit:  opened_unit = .true.:  opened_unit = .true.
  call expect_logical(opened_unit, .false., 'opened-unit-pre')
  number_unit = 0
  number_unit = -777 ! sentinel-probe:number-unit:  number_unit = -1:  number_unit = 0
  call expect_int(number_unit, -777, 'number-unit-pre')
  named_unit = .false. ! sentinel-probe:named-unit:  named_unit = .true.:  named_unit = .true.
  call expect_logical(named_unit, .false., 'named-unit-pre')
  access_unit = '############' ! sentinel-probe:access-unit:  access_unit = 'STREAM      ':  access_unit = '            '
  call expect_char(access_unit, '############', 'access-unit-pre')
  action_unit = '############' ! sentinel-probe:action-unit:  action_unit = 'READWRITE   ':  action_unit = '            '
  call expect_char(action_unit, '############', 'action-unit-pre')
  form_unit = '############' ! sentinel-probe:form-unit:  form_unit = 'FORMATTED   ':  form_unit = '            '
  call expect_char(form_unit, '############', 'form-unit-pre')
  name_from_unit = repeat('#', len(name_from_unit))
  inquire(unit=u, opened=opened_unit, number=number_unit, named=named_unit, &
          access=access_unit, action=action_unit, form=form_unit, name=name_from_unit)
  call expect_logical(opened_unit, .true., 'opened-unit-true')
  call expect_int(number_unit, u, 'number-unit-value')
  call expect_logical(named_unit, .true., 'named-unit-true')
  call expect_char(access_unit, 'STREAM      ', 'access-unit-stream')
  call expect_char(action_unit, 'READWRITE   ', 'action-unit-readwrite')
  call expect_char(form_unit, 'FORMATTED   ', 'form-unit-formatted')
  call expect_char_not(name_from_unit, repeat('#', len(name_from_unit)), 'name-unit-assigned')

  opened_file_live = .false. ! sentinel-probe:opened-file-live:  opened_file_live = .true.:  opened_file_live = .true.
  call expect_logical(opened_file_live, .false., 'opened-file-live-pre')
  number_file_live = 0
  number_file_live = -777 ! sentinel-probe:number-file-live:  number_file_live = -1:  number_file_live = 0
  call expect_int(number_file_live, -777, 'number-file-live-pre')
  form_file_live = '############' ! sentinel-probe:form-file:form_file_live='FORMATTED   ':form_file_live='            '
  call expect_char(form_file_live, '############', 'form-file-live-pre')
  inquire(file=name_keep, opened=opened_file_live, number=number_file_live, form=form_file_live)
  call expect_logical(opened_file_live, .true., 'opened-file-live-true')
  call expect_int(number_file_live, u, 'number-file-live-unit')
  call expect_char(form_file_live, 'FORMATTED   ', 'form-file-live-formatted')

  form_long = '############' ! sentinel-probe:form-long:  form_long = 'FORMATTED   ':  form_long = '            '
  call expect_char(form_long, '############', 'form-long-pre')
  access_short = '##' ! sentinel-probe:access-short:  access_short = 'ST':  access_short = '  '
  call expect_char(access_short, '##', 'access-short-pre')
  inquire(unit=u, form=form_long, access=access_short)
  call expect_char(form_long, 'FORMATTED   ', 'form-padding')
  call expect_char(access_short, 'ST', 'access-truncation')

  close(u, status='keep', iostat=ios)
  call expect_int(ios, 0, 'close-live-keep-status')
  exists_after = .false. ! sentinel-probe:exists-after:  exists_after = .true.:  exists_after = .true.
  call expect_logical(exists_after, .false., 'exists-after-pre')
  opened_after = .true. ! sentinel-probe:opened-after:  opened_after = .false.:  opened_after = .false.
  call expect_logical(opened_after, .true., 'opened-after-pre')
  number_after = 0
  number_after = -777 ! sentinel-probe:number-after:  number_after = -1:  number_after = 0
  call expect_int(number_after, -777, 'number-after-pre')
  inquire(file=name_keep, exist=exists_after, opened=opened_after, number=number_after)
  call expect_logical(exists_after, .true., 'exists-after-true')
  call expect_logical(opened_after, .false., 'opened-after-false')
  call expect_int(number_after, -1, 'number-after-minus-one')

  unconnected_unit = 88
  open(unit=unconnected_unit, status='scratch', iostat=ios)
  call expect_int(ios, 0, 'open-unconnected-setup')
  close(unconnected_unit, status='delete', iostat=ios)
  call expect_int(ios, 0, 'close-unconnected-setup')
  opened_unconnected = .true. ! sentinel-probe:opened-unconnected:  opened_unconnected = .false.:  opened_unconnected = .false.
  call expect_logical(opened_unconnected, .true., 'opened-unconnected-pre')
  inquire(unit=unconnected_unit, opened=opened_unconnected)
  call expect_logical(opened_unconnected, .false., 'opened-unconnected-false')

  values = [17, 23]
  got = [-1, -1]
  iol = 0
  iol = -777 ! sentinel-probe:iolength-target:  iol = 8:  iol = 0
  call expect_int(iol, -777, 'iolength-pre')
  inquire(iolength=iol) values
  call expect_positive(iol, 'iolength-positive')
  open(newunit=du, file=name_direct, status='replace', access='direct', &
       form='unformatted', recl=iol, iostat=ios)
  call expect_int(ios, 0, 'open-direct-iolength')
  write(du, rec=1, iostat=ios) values
  call expect_int(ios, 0, 'write-direct-iolength')
  read(du, rec=1, iostat=ios) got
  call expect_int(ios, 0, 'read-direct-iolength')
  call expect_int(got(1), 17, 'iolength-value-one')
  call expect_int(got(2), 23, 'iolength-value-two')
  close(du, status='delete')

  open(newunit=again, file=name_from_unit, status='old', iostat=ios)
  call expect_int(ios, 0, 'name-open-suitable')
  close(again)
  call cleanup_name(name_keep)
  call finish()
""" + common_helpers(variant)
    source = with_expected_checks(body)
    mutations = []
    # feature mutations for major INQUIRE forms and outputs
    add_mutation(mutations, "by-file-connected-to-absent", source,
                 "  inquire(file=name_keep, opened=opened_file_live, number=number_file_live, form=form_file_live)\n",
                 "  inquire(file=name_before, opened=opened_file_live, number=number_file_live, form=form_file_live)\n")
    add_mutation(mutations, "by-unit-redirect-unconnected", source,
                 "  inquire(unit=u, opened=opened_unit, number=number_unit, named=named_unit, &\n"
                 "          access=access_unit, action=action_unit, form=form_unit, name=name_from_unit)\n",
                 "  inquire(unit=unconnected_unit, opened=opened_unit, number=number_unit, named=named_unit, &\n"
                 "          access=access_unit, action=action_unit, form=form_unit, name=name_from_unit)\n")
    add_mutation(mutations, "iolength-redirect-target", source,
                 "  inquire(iolength=iol) values\n", "  inquire(iolength=ios) values\n")
    add_mutation(mutations, "create-before-file-early", source,
                 "  call cleanup_name(name_before)\n  call cleanup_name(name_keep)\n",
                 "  call cleanup_name(name_before)\n  open(newunit=u, file=name_before, status='replace')\n  close(u)\n"
                 "  call cleanup_name(name_keep)\n")
    add_mutation(mutations, "keep-file-still-open", source,
                 "  close(u, status='keep', iostat=ios)\n  call expect_int(ios, 0, 'close-keep-status')\n",
                 "  ios = 0\n  call expect_int(ios, 0, 'close-keep-status')\n")
    add_mutation(mutations, "unit-form-unformatted", source,
                 "open(newunit=u, file=name_keep, status='old', access='stream', form='formatted', &",
                 "open(newunit=u, file=name_keep, status='old', access='stream', form='unformatted', &")
    add_mutation(mutations, "after-close-left-open", source,
                 "  close(u, status='keep', iostat=ios)\n  call expect_int(ios, 0, 'close-live-keep-status')\n",
                 "  ios = 0\n  call expect_int(ios, 0, 'close-live-keep-status')\n")
    add_mutation(mutations, "unconnected-unit-left-open", source,
                 "  close(unconnected_unit, status='delete', iostat=ios)\n  call expect_int(ios, 0, 'close-unconnected-setup')\n",
                 "  ios = 0\n  call expect_int(ios, 0, 'close-unconnected-setup')\n")
    add_sentinel_mutations(source, mutations)
    return source, mutations


def source_specifier_assignments():
    variant = "specifier_assignments"
    body = """program p_specifier_assignments
  implicit none
  integer :: checks, u, du, ios, dummy_int, number, pos_value, size_value, nextrec_value, recl_value
  logical :: exists, opened, named, pending, dummy_logical
  character(len=28) :: name_stream, name_direct
  character(len=16) :: access, action, asynchronous, blank, decimal, delim, encoding, form
  character(len=16) :: formatted, name_value, pad, position, read_value, readwrite
  character(len=16) :: round_value, sequential, sign_value, stream_value, unformatted, write_value
  character(len=16) :: direct_value, dummy_char
  checks = 0
  name_stream = 'io_inquire_spec_stream.dat'
  name_direct = 'io_inquire_spec_direct.dat'
  call cleanup_name(name_stream)
  call cleanup_name(name_direct)
  open(newunit=u, file=name_stream, status='replace', access='stream', form='formatted', &
       action='readwrite', blank='zero', decimal='comma', delim='quote', encoding='default', &
       pad='no', round='up', sign='plus', iostat=ios)
  call expect_int(ios, 0, 'open-stream-status')

  access = '################' ! sentinel-probe:spec-access:  access = 'STREAM          ':  access = '                '
  call expect_char(access, '################', 'access-pre')
  action = '################' ! sentinel-probe:spec-action:  action = 'READWRITE       ':  action = '                '
  call expect_char(action, '################', 'action-pre')
  asynchronous = '################' ! sentinel-probe:sp-async:asynchronous='NO              ':asynchronous='                '
  call expect_char(asynchronous, '################', 'asynchronous-pre')
  blank = '################' ! sentinel-probe:spec-blank:  blank = 'ZERO            ':  blank = '                '
  call expect_char(blank, '################', 'blank-pre')
  decimal = '################' ! sentinel-probe:spec-decimal:  decimal = 'COMMA           ':  decimal = '                '
  call expect_char(decimal, '################', 'decimal-pre')
  delim = '################' ! sentinel-probe:spec-delim:  delim = 'QUOTE           ':  delim = '                '
  call expect_char(delim, '################', 'delim-pre')
  encoding = '################' ! sentinel-probe:spec-encoding:  encoding = 'DEFAULT         ':  encoding = '                '
  call expect_char(encoding, '################', 'encoding-pre')
  exists = .false. ! sentinel-probe:spec-exist:  exists = .true.:  exists = .true.
  call expect_logical(exists, .false., 'exist-pre')
  form = '################' ! sentinel-probe:spec-form:  form = 'FORMATTED       ':  form = '                '
  call expect_char(form, '################', 'form-pre')
  formatted = '################' ! sentinel-probe:spec-formatted:  formatted = 'YES             ':  formatted = '                '
  call expect_char(formatted, '################', 'formatted-pre')
  name_value = '################' ! sentinel-probe:spec-name:  name_value = 'changed-name    ':  name_value = '                '
  call expect_char(name_value, '################', 'name-pre')
  named = .false. ! sentinel-probe:spec-named:  named = .true.:  named = .true.
  call expect_logical(named, .false., 'named-pre')
  number = 0
  number = -777 ! sentinel-probe:spec-number:  number = -1:  number = 0
  call expect_int(number, -777, 'number-pre')
  opened = .false. ! sentinel-probe:spec-opened:  opened = .true.:  opened = .true.
  call expect_logical(opened, .false., 'opened-pre')
  pad = '################' ! sentinel-probe:spec-pad:  pad = 'NO              ':  pad = '                '
  call expect_char(pad, '################', 'pad-pre')
  pending = .true. ! sentinel-probe:spec-pending:  pending = .false.:  pending = .false.
  call expect_logical(pending, .true., 'pending-pre')
  pos_value = 0
  pos_value = -777 ! sentinel-probe:spec-pos:  pos_value = 1:  pos_value = 0
  call expect_int(pos_value, -777, 'pos-pre')
  position = '################' ! sentinel-probe:spec-position:  position = 'REWIND          ':  position = '                '
  call expect_char(position, '################', 'position-pre')
  read_value = '################' ! sentinel-probe:spec-read:  read_value = 'YES             ':  read_value = '                '
  call expect_char(read_value, '################', 'read-pre')
  readwrite = '################' ! sentinel-probe:spec-readwrite:  readwrite = 'YES             ':  readwrite = '                '
  call expect_char(readwrite, '################', 'readwrite-pre')
  round_value = '################' ! sentinel-probe:spec-round:  round_value = 'UP              ':  round_value = '                '
  call expect_char(round_value, '################', 'round-pre')
  sequential = '################' ! sentinel-probe:sp-seq:sequential='NO              ':sequential='                '
  call expect_char(sequential, '################', 'sequential-pre')
  sign_value = '################' ! sentinel-probe:spec-sign:  sign_value = 'PLUS            ':  sign_value = '                '
  call expect_char(sign_value, '################', 'sign-pre')
  size_value = -777 ! sentinel-probe:spec-size:  size_value = 0:  size_value = 0
  call expect_int(size_value, -777, 'size-pre')
  stream_value = '################' ! sentinel-probe:sp-stream:stream_value='YES             ':stream_value='                '
  call expect_char(stream_value, '################', 'stream-pre')
  unformatted = '################' ! sentinel-probe:sp-unfmt:unformatted='NO              ':unformatted='                '
  call expect_char(unformatted, '################', 'unformatted-pre')
  write_value = '################' ! sentinel-probe:spec-write:  write_value = 'YES             ':  write_value = '                '
  call expect_char(write_value, '################', 'write-pre')
  ios = -777 ! sentinel-probe:spec-iostat:  ios = 0:  ios = 0
  call expect_int(ios, -777, 'iostat-pre')
  dummy_char = '................'
  dummy_int = -909
  dummy_logical = .true.
  inquire(unit=u, access=access, action=action, asynchronous=asynchronous, blank=blank, &
          decimal=decimal, delim=delim, encoding=encoding, exist=exists, form=form, &
          formatted=formatted, name=name_value, named=named, number=number, opened=opened, &
          pad=pad, pending=pending, pos=pos_value, position=position, read=read_value, &
          readwrite=readwrite, round=round_value, sequential=sequential, sign=sign_value, &
          size=size_value, stream=stream_value, unformatted=unformatted, write=write_value, &
          iostat=ios)
  call expect_int(ios, 0, 'iostat-zero')
  call expect_char(access, 'STREAM          ', 'access-stream')
  call expect_char(action, 'READWRITE       ', 'action-readwrite')
  call expect_char(asynchronous, 'NO              ', 'asynchronous-no')
  call expect_char(blank, 'ZERO            ', 'blank-zero')
  call expect_char(decimal, 'COMMA           ', 'decimal-comma')
  call expect_char(delim, 'QUOTE           ', 'delim-quote')
  call expect_char(encoding, 'DEFAULT         ', 'encoding-default')
  call expect_logical(exists, .true., 'exist-true')
  call expect_char(form, 'FORMATTED       ', 'form-formatted')
  call expect_char(formatted, 'YES             ', 'formatted-yes')
  call expect_char_not(name_value, '################', 'name-assigned')
  call expect_logical(named, .true., 'named-true')
  call expect_int(number, u, 'number-value')
  call expect_logical(opened, .true., 'opened-true')
  call expect_char(pad, 'NO              ', 'pad-no')
  call expect_logical(pending, .false., 'pending-false')
  call expect_int(pos_value, 1, 'pos-one')
  call expect_char_not(position, '################', 'position-assigned')
  call expect_char(read_value, 'YES             ', 'read-yes')
  call expect_char(readwrite, 'YES             ', 'readwrite-yes')
  call expect_char(round_value, 'UP              ', 'round-up')
  call expect_char(sequential, 'NO              ', 'sequential-no')
  call expect_char(sign_value, 'PLUS            ', 'sign-plus')
  call expect_int_not(size_value, -777, 'size-assigned')
  call expect_char(stream_value, 'YES             ', 'stream-yes')
  call expect_char(unformatted, 'NO              ', 'unformatted-no')
  call expect_char(write_value, 'YES             ', 'write-yes')

  opened = .false. ! sentinel-probe:spec-file-opened:  opened = .true.:  opened = .true.
  call expect_logical(opened, .false., 'file-opened-pre')
  number = -777 ! sentinel-probe:spec-file-number:  number = -1:  number = 0
  call expect_int(number, -777, 'file-number-pre')
  inquire(file=name_stream, opened=opened, number=number)
  call expect_logical(opened, .true., 'file-opened-true')
  call expect_int(number, u, 'file-number-unit')
  close(u, status='delete')

  open(newunit=du, file=name_direct, status='replace', access='direct', form='formatted', &
       action='readwrite', recl=16, iostat=ios)
  call expect_int(ios, 0, 'open-direct-status')
  direct_value = '################' ! sentinel-probe:sp-direct:direct_value='YES             ':direct_value='                '
  call expect_char(direct_value, '################', 'direct-pre')
  nextrec_value = -777 ! sentinel-probe:spec-nextrec:  nextrec_value = 1:  nextrec_value = 0
  call expect_int(nextrec_value, -777, 'nextrec-pre')
  recl_value = -777 ! sentinel-probe:spec-recl:  recl_value = 16:  recl_value = 0
  call expect_int(recl_value, -777, 'recl-pre')
  inquire(unit=du, direct=direct_value, nextrec=nextrec_value, recl=recl_value)
  call expect_char(direct_value, 'YES             ', 'direct-yes')
  call expect_int(nextrec_value, 1, 'nextrec-one')
  call expect_int(recl_value, 16, 'recl-sixteen')
  close(du, status='delete')
  call finish()
""" + common_helpers(variant)
    source = with_expected_checks(body)
    mutations = []
    # Redirect each claimed R1231 specifier target or change the governing designator.
    replacements = {
        "access=access": "access=dummy_char", "action=action": "action=dummy_char",
        "asynchronous=asynchronous": "asynchronous=dummy_char", "blank=blank": "blank=dummy_char",
        "decimal=decimal": "decimal=dummy_char", "delim=delim": "delim=dummy_char",
        "encoding=encoding": "encoding=dummy_char", "exist=exists": "exist=dummy_logical",
        "form=form": "form=dummy_char", "formatted=formatted": "formatted=dummy_char",
        "name=name_value": "name=dummy_char", "named=named": "named=dummy_logical",
        "pad=pad": "pad=dummy_char", "pending=pending": "pending=dummy_logical",
        "pos=pos_value": "pos=dummy_int", "position=position": "position=dummy_char",
        "read=read_value": "read=dummy_char", "readwrite=readwrite": "readwrite=dummy_char",
        "round=round_value": "round=dummy_char", "sequential=sequential": "sequential=dummy_char",
        "sign=sign_value": "sign=dummy_char", "size=size_value": "size=dummy_int",
        "stream=stream_value": "stream=dummy_char", "unformatted=unformatted": "unformatted=dummy_char",
        "write=write_value": "write=dummy_char",
    }
    for old, new in replacements.items():
        add_mutation(mutations, "redirect-" + old.split("=")[0].replace("_", "-"), source, old, new)
    add_mutation(mutations, "unit-designator-other", source, "inquire(unit=u, access=access",
                 "inquire(unit=du, access=access")
    add_mutation(mutations, "redirect-number", source,
                 "named=named, number=number, opened=opened",
                 "named=named, number=dummy_int, opened=opened")
    add_mutation(mutations, "redirect-opened", source,
                 "number=number, opened=opened, &\n          pad=pad",
                 "number=number, opened=dummy_logical, &\n          pad=pad")
    add_mutation(mutations, "redirect-iostat", source,
                 "write=write_value, &\n          iostat=ios)",
                 "write=write_value, &\n          iostat=dummy_int)")
    add_mutation(mutations, "file-designator-other", source, "inquire(file=name_stream, opened=opened, number=number)",
                 "inquire(file=name_direct, opened=opened, number=number)")
    add_mutation(mutations, "direct-target-redirect", source, "direct=direct_value", "direct=dummy_char")
    add_mutation(mutations, "nextrec-target-redirect", source, "nextrec=nextrec_value", "nextrec=dummy_int")
    add_mutation(mutations, "recl-target-redirect", source, "recl=recl_value", "recl=dummy_int")
    add_mutation(mutations, "direct-open-sequential", source, "access='direct', form='formatted', &",
                 "access='sequential', form='formatted', &")
    add_sentinel_mutations(source, mutations)
    return source, mutations


def source_syntax_forms():
    variant = "syntax_forms"
    body = """program p_syntax_forms
  implicit none
  integer :: checks, iol, ios, u, values(2), got(2)
  logical :: opened
  checks = 0
  opened = .true. ! sentinel-probe:syntax-opened:  opened = .false.:  opened = .false.
  call expect_logical(opened, .true., 'opened-pre')
  inquire(unit=10, opened=opened)
  call expect_logical(opened, .false., 'inquire-spec-list-form')
  values = [31, 32]
  got = [-1, -1]
  iol = -777 ! sentinel-probe:syntax-iolength:  iol = 8:  iol = 0
  call expect_int(iol, -777, 'iolength-pre')
  inquire(iolength=iol) values
  call expect_positive(iol, 'iolength-output-list-form')
  open(newunit=u, file='io_inquire_r1230_direct.dat', status='replace', access='direct', &
       form='unformatted', recl=iol, iostat=ios)
  call expect_int(ios, 0, 'open-direct')
  write(u, rec=1, iostat=ios) values
  call expect_int(ios, 0, 'write-direct')
  read(u, rec=1, iostat=ios) got
  call expect_int(ios, 0, 'read-direct')
  call expect_int(got(1), 31, 'got-one')
  call expect_int(got(2), 32, 'got-two')
  close(u, status='delete')
  call finish()
""" + common_helpers(variant)
    source = with_expected_checks(body)
    mutations = []
    add_mutation(mutations, "inquire-spec-list-target", source,
                 "  inquire(unit=10, opened=opened)\n", "  inquire(unit=10)\n")
    add_mutation(mutations, "iolength-target-redirect", source,
                 "  inquire(iolength=iol) values\n", "  inquire(iolength=ios) values\n")
    add_sentinel_mutations(source, mutations)
    return source, mutations


SOURCE_BUILDERS = {"forms_timing": source_forms_timing, "syntax_forms": source_syntax_forms, "specifier_assignments": source_specifier_assignments}

LFORTRAN_DEFECT_PARENTS = {
    "forms_timing": "LFortran 0.65.0-411 misreports FILE= inquiry state after CLOSE(STATUS='KEEP')",
    "specifier_assignments": "LFortran 0.65.0-411 misreports FILE= OPENED/NUMBER inquiry state",
}


def runtime_source_specs():
    base = {}
    for variant, builder in SOURCE_BUILDERS.items():
        source, mutations = builder()
        raw = source.encode("ascii")
        base[variant] = dict(variant=variant, source=source, source_sha256=sha(raw), mutations=mutations,
                             completion=COMPLETIONS[variant])
    return base


def all_specs():
    base = runtime_source_specs()
    specs = {}
    for rule, variant in DIRECT_RUNTIME_RULES.items():
        parent = copy.deepcopy(base[variant])
        source = parent["source"].replace("! rule: RULE", f"! rule: {rule}")
        name = case_id(rule, variant, "valid")
        evidence = "positive-control" if rule == "R1230" else "effect"
        specs[name] = dict(id=name, rule=rule, section=RULE_SECTION[rule], variant=variant,
                           facets=RULE_FACETS[rule], kind="valid", evidence=evidence,
                           source=source, source_sha256=sha(source.encode("ascii")),
                           mutations=parent["mutations"], completion=parent["completion"])
    for item in INVALID_CASES:
        name = case_id(item["rule"], item["variant"], "invalid")
        specs[name] = dict(id=name, rule=item["rule"], section="12.10.2.1", variant=item["variant"],
                           facets=[item["facet"]], kind="invalid", evidence="effect",
                           source=item["source"], diagnostic_line=item["line"], contains_any=item["contains"],
                           control=case_id(item["rule"], item["control"], "valid"), derivation=item["derivation"],
                           mutations=[], completion="")
    for variant, (rule, facets, source) in CONTROLS.items():
        name = case_id(rule, variant, "valid")
        specs[name] = dict(id=name, rule=rule, section="12.10.2.1", variant=variant,
                           facets=facets, kind="valid", evidence="positive-control", source=source,
                           source_sha256=sha(source.encode("ascii")), mutations=[], completion="")
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError(spec["id"] + ": parent source fingerprint changed")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError(spec["id"] + ": mutation span mismatch for " + mutation["id"])
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    root = Path(root)
    specs = all_specs()
    files = {}
    for name, spec in specs.items():
        directory = root / "tests/fixtures" / (TOPIC + "_" + spec["variant"] + "__" + rule_slug(spec["rule"]))
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran",
                                    form="free", output="source.o")])
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            expect = dict(phase="run", outcome="success", exit_code=0)
            if spec.get("completion"):
                expect.update(stdout=spec["completion"], stderr="")
            manifest["expect"] = expect
        else:
            manifest["expect"] = dict(
                phase="compile", outcome="diagnose", step="source",
                diagnostic=dict(file="source.f90", line=spec["diagnostic_line"],
                                contains_any=spec["contains_any"],
                                excludes_any=["not implemented", "not yet implemented", "unimplemented",
                                              "unsupported feature", "unsupported", "not supported",
                                              "not yet supported", "implementation limitation", "ASR verify",
                                              "ASR verifier", "internal compiler error", "LLVM ERROR",
                                              "unexpected end of file", "unexpected eof", "out of memory"])
            )
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["source_path"] = directory.relative_to(root).as_posix() + "/source.f90"
        spec["manifest"] = manifest
        raw = spec["source"].encode("ascii")
        if max(map(len, raw.splitlines()), default=0) > 132:
            raise ValueError(name + ": source line exceeds 132 characters")
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    hits = [i for i, p in enumerate(paragraphs) if p.startswith(prefix)]
    if len(hits) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if hits:
        paragraphs[hits[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def synced_catalogue(section, catalogue):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    for (rule, facet), rationale in RESTORED_PENDING.items():
        if RULE_SECTION.get(rule, section) != section or rule not in by_rule:
            continue
        by_rule[rule].setdefault("pending", {})[facet] = rationale
    for rule, facets in RULE_FACETS.items():
        if RULE_SECTION[rule] != section or rule not in by_rule:
            continue
        row = by_rule[rule]
        missing = set(facets) - set(row["facets"])
        if missing:
            raise ValueError(rule + " selected unknown facets " + repr(sorted(missing)))
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX[rule], ORACLE_PARAGRAPHS[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIX[rule],
                                                   LIMIT_PREFIX[rule] + LIMIT_PARAGRAPH)
    return result


def link_id(rule, facet):
    return f"{rule}.{facet}.io-inquire-12-10-1"


def linked_case_member(target_rule, target_facet):
    variant = LINKED_RUNTIME_RULES[target_rule]
    primary = PRIMARY_RULE[variant]
    return dict(id=case_id(primary, variant, "valid"), role="runtime-effect", primary_rule=primary,
                source=PRIMARY_SOURCE[variant],
                path=f"tests/fixtures/{TOPIC}_{variant}__{rule_slug(primary)}/fixture.json",
                phase="run")


def desired_evidence_links(root, catalogues):
    links = []
    for rule, variant in LINKED_RUNTIME_RULES.items():
        row = next(r for r in catalogues[RULE_SECTION[rule]]["requirements"] if r["id"] == rule)
        target_sources = [RULE_SECTION[rule] + "#" + unit for unit in row["source_units"]]
        basis = sorted(set(target_sources + [PRIMARY_SOURCE[variant]]))
        for facet in RULE_FACETS[rule]:
            if (rule, facet) in RESTORED_PENDING:
                continue
            links.append(dict(
                id=link_id(rule, facet),
                pattern="runtime-effect",
                target=dict(requirement=rule, facet=facet, source_units=target_sources),
                basis=basis,
                claim=(f"The canonical {variant.replace('_', '-')} INQUIRE fixture contains a distinct "
                       f"sentinel-guarded assertion and feature mutant for {rule} facet {facet}. "
                       "The catalogue oracle names the exact assertion class; this link prevents duplicate "
                       "execution manifests for the same parent program."),
                limitation=("Linked runtime-effect evidence only: no extra execution, no additional diagnostic "
                            "policy, no assertion of NAME spelling/case, IOMSG text, numeric nonzero status "
                            "codes, processor-dependent file sizes, or undefined inquiry variables."),
                cases=[linked_case_member(rule, facet)]))
    return links


def synced_evidence_links(root, catalogues):
    path = Path(root) / EVIDENCE_LINKS_PATH
    data = json.loads(path.read_text())
    prefix = ".io-inquire-12-10-1"
    retained = [link for link in data["links"] if not link["id"].endswith(prefix)]
    reviews = {link["id"]: link["review"] for link in data["links"]
               if link["id"].endswith(prefix) and "review" in link}
    desired = desired_evidence_links(root, catalogues)
    for link in desired:
        # Integrator-recorded link adjudications are owned by the review ledger, not by this generator.
        if link["id"] in reviews:
            link["review"] = reviews[link["id"]]
    data["links"] = retained + desired
    return data


def summary_text():
    total = sum(len(facets) for facets in RULE_FACETS.values())
    return (SUMMARY_BEGIN + "\n"
            "## INQUIRE general/specifier-list fixtures\n\n"
            f"This packet adds {total} selected facet bindings for INQUIRE by file, by unit, by IOLENGTH, "
            "reference-validated inquiry specifier syntax, and numbered specifier-list constraints. Runtime "
            "fixtures initialize every inquiry target to a distinguished sentinel and check that sentinel before "
            "INQUIRE; diagnostic fixtures have one-property compiled controls. NAME spelling/case, IOMSG text, "
            "processor-dependent sizes and undefined variables are not asserted.\n"
            + SUMMARY_END)


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated region changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    old = "This source packet records source accounting and pending plans only, not fixture approval."
    new = ("This source packet records source accounting. Selected INQUIRE fixtures now supply executable "
           "standard-oracle observations and mutation plans; fixture approval remains separate.")
    before = before.replace(old, new)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        lead, rest2 = before.split(SUMMARY_BEGIN)
        _, trail = rest2.split(SUMMARY_END)
        before = lead.rstrip() + "\n\n" + trail.lstrip()
    return (before.rstrip() + "\n\n" + summary_text() + "\n\n" + begin + "\n\n" +
            "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after)


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updates, views, stale = {}, {}, []
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
    evidence = synced_evidence_links(root, updates)
    if json.loads((root / EVIDENCE_LINKS_PATH).read_text()) != evidence:
        stale.append(EVIDENCE_LINKS_PATH)
    for path, raw in files.items():
        if not path.is_file() or path.read_bytes() != raw:
            stale.append(path.relative_to(root).as_posix())
    if check:
        if stale:
            raise ValueError("stale INQUIRE fixtures: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updates[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(views[section])
            (root / EVIDENCE_LINKS_PATH).write_text(json.dumps(evidence, indent=2) + "\n")
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
    compiled = subprocess.run(compiler_command(compiler, std, source, exe), cwd=work_dir, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
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
    compiler_name = Path(compiler).name.lower()
    specs = {}
    for name, spec in all_specs().items():
        if spec["kind"] != "valid" or not spec.get("mutations"):
            continue
        key = (spec["variant"], spec["source_sha256"])
        specs.setdefault(key, spec)
    workspace_parent = root / ".io_inquire_mutation_runs"
    workspace_parent.mkdir(exist_ok=True)
    work_root = Path(tempfile.mkdtemp(prefix=sha((str(compiler) + str(std)).encode())[:12] + "-",
                                      dir=workspace_parent))
    skipped = []
    try:
        report = []
        for spec in specs.values():
            parent_dir = Path(tempfile.mkdtemp(prefix=spec["variant"] + "-parent-", dir=work_root))
            parent = run_one_source(compiler, std, parent_dir, spec["source"], spec["completion"], spec["variant"])
            parent_ok = parent["status"] == "pass"
            if not parent_ok and compiler_name.startswith("lfortran") and spec["variant"] in LFORTRAN_DEFECT_PARENTS:
                skipped.append(dict(variant=spec["variant"], mutations=len(spec["mutations"]),
                                    reason=LFORTRAN_DEFECT_PARENTS[spec["variant"]],
                                    parent_status=parent["status"], stdout=parent["stdout"], stderr=parent["stderr"]))
                continue
            for index, mutation in enumerate(spec["mutations"]):
                mutant_dir = Path(tempfile.mkdtemp(prefix=spec["variant"] + f"-m{index:03d}-", dir=work_root))
                mutant = mutated_source(spec, mutation).decode("ascii")
                observed = run_one_source(compiler, std, mutant_dir, mutant, spec["completion"],
                                          spec["variant"] + f"_m{index:03d}")
                report.append(dict(case=spec["id"], mutation=mutation["id"], category=mutation["category"],
                                   parent_ok=parent_ok, failed=observed["status"] != "pass",
                                   status=observed["status"], returncode=observed["returncode"],
                                   stdout=observed["stdout"], stderr=observed["stderr"]))
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:10], indent=2))
        return report, skipped
    finally:
        if not keep_work:
            shutil.rmtree(work_root, ignore_errors=True)


def counts(specs):
    unique_mutants = {}
    for spec in specs.values():
        if spec.get("mutations"):
            unique_mutants.setdefault((spec["variant"], spec["source_sha256"]), spec["mutations"])
    return (len(specs), sum(len(spec["facets"]) for spec in specs.values()),
            sum(len(facets) for facets in RULE_FACETS.values()),
            sum(len(mutations) for mutations in unique_mutants.values()))


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
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report, skipped = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        by_cat = {}
        for row in report:
            by_cat[row["category"]] = by_cat.get(row["category"], 0) + 1
        details = ", ".join(f"{k}={by_cat[k]}" for k in sorted(by_cat)) or "none"
        message = f"Mutation-checked {len(report)} INQUIRE mutations: " + details + "; all checked mutants failed."
        if skipped:
            skipped_text = "; ".join(f"{row['variant']} skipped {row['mutations']} ({row['reason']})"
                                      for row in skipped)
            message += " Skipped reviewed LFortran-defect parents: " + skipped_text + "."
        print(message)
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, manifest_facets, total_facets, mutation_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} INQUIRE cases, "
          f"{total_facets} selected catalogue facets ({manifest_facets} manifest facets) "
          f"and {mutation_count} mutations.")


if __name__ == "__main__":
    main()
