#!/usr/bin/env python3
"""Runtime and diagnostic fixtures for Fortran 2023 12.6.3 I/O lists."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "12.6.3"
CATALOGUE = "doc/catalogues/data_transfer_input_output_list_12_6_3.json"
VIEW = "doc/fortran_2023_12_6_3.md"
SUMMARY_BEGIN = "<!-- BEGIN IO-LIST 12.6.3 FIXTURES -->"
SUMMARY_END = "<!-- END IO-LIST 12.6.3 FIXTURES -->"
MUTATION_WORK = ".io_list_12_6_3_mutation_work"
EXCLUSIONS = [
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal compiler error", "internal error", "code generation error", "asr", "verifier",
    "out of memory", "recovery", "cannot read module",
]
POSITIVE_CONTROL_RULES = {
    "R1216", "R1217", "R1218", "R1219", "R1220", "C1234", "C1235",
    "S12.6.3-003", "S12.6.3-004", "S12.6.3-005",
}

SELECTED = {
    "S12.6.3-001": {"io-list-specifies-transferred-entities"},
    "R1216": {"input-variable-form", "input-io-implied-do-form", "input-nonvariable-rejected"},
    "R1217": {"output-expression-form", "output-io-implied-do-form"},
    "R1218": {"io-implied-do-parenthesized-form", "io-implied-do-object-list-form", "io-implied-do-control-form"},
    "R1219": {"implied-do-object-input-item-form", "implied-do-object-output-item-form"},
    "R1220": {"implied-do-control-do-variable", "implied-do-control-initial-expr", "implied-do-control-terminal-expr", "implied-do-control-optional-increment"},
    "C1233": {"whole-assumed-size-input-item-rejected"},
    "C1234": {"input-list-implied-do-object-input-item", "input-list-output-expression-object-rejected", "output-list-implied-do-object-output-item"},
    "C1235": {"ordinary-output-expression-control"},
    "S12.6.3-003": {"input-pointer-definable-associated-target", "input-pointer-transfer-to-target"},
    "S12.6.3-004": {"output-pointer-associated-target", "output-pointer-transfer-from-target"},
    "S12.6.3-005": {"allocatable-input-item-allocated", "allocatable-output-item-allocated"},
    "S12.6.3-011": {"io-list-expansion-rules-reapplied"},
    "S12.6.3-012": {"array-list-item-expands-in-element-order"},
    "S12.6.3-017": {"formatted-derived-component-order-expansion"},
    "S12.6.3-019": {"io-implied-do-do-construct-execution"},
    "S12.6.3-020": {"effective-items-are-expanded-scalar-objects"},
    "S12.6.3-021": {"zero-sized-array-no-effective-items"},
    "S12.6.3-022": {"zero-count-implied-do-no-effective-items"},
    "S12.6.3-023": {"zero-length-character-is-effective-item"},
}

ORACLE_PREFIX = "IO-list 12.6.3 executable fixture family: "
LIMIT_PREFIX = "IO-list 12.6.3 fixture boundaries: "
ORACLE = ORACLE_PREFIX + (
    "fourteen valid programs and three diagnostic/control pairs exercise bounded 12.6.3 input/output-list rules. "
    "Runtime cases use internal files only, SS on every numeric formatted WRITE, exact integer/logical/default-character "
    "observations, LEN checks before character equality, sentinel-filled output buffers, and distinctive nonzero/nonblank "
    "pre-READ guards for every input target. Pointer cases observe the associated target, allocatable cases allocate before "
    "transfer, whole-array cases distinguish array element order, derived-type formatted cases distinguish component order and "
    "re-applied array-component expansion, and zero-effective-item cases prove descriptor consumption by the following marker. "
    "The implied-DO cases also assert the post-loop do-variable value required by DO execution, and one case reads n before "
    "using n in a later input item bound. The diagnostic negatives are line-anchored one-property changes with real controls. "
    "The generator records per-target sentinel probes, oracle mutations, and feature substitutions that compile and fail at run "
    "time for valid runtime fixtures."
)
LIMITATION = LIMIT_PREFIX + (
    "coverage is limited to default integer, logical and default-character internal formatted/list-directed transfers. It does "
    "not assert external-file representation, IOMSG text, specific IOSTAT values, nondefault character kind support, enum I/O, "
    "polymorphic DTIO admission, defined-I/O side effects, unformatted derived-object storage forms, inaccessible/private "
    "subcomponent diagnostics, pointer/allocatable restriction diagnostics, BOZ output-item rejection, procedure-pointer "
    "output rejection, coarrays, asynchronous transfer, or processor-dependent raw storage. Unnumbered shall-not rules without "
    "a portable positive observation remain pending as source-control plans rather than required diagnostics."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def clean(text):
    return textwrap.dedent(text).lstrip("\n")


def identifier(rule, variant, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__io_list_12_6_3_" + variant


def mutation_span(source, expected, replacement, mid, kind="feature", category="feature"):
    count = source.count(expected)
    if count != 1:
        raise ValueError(f"{mid}: expected unique token {expected!r}, found {count}")
    start = source.index(expected)
    return dict(id=mid, kind=kind, category=category, span=[start, start + len(expected)],
                expected=expected, replacement=replacement,
                line=source[:start].count("\n") + 1)


def spec(rule, variant, facets, source, *, evidence="effect", feature=(), sentinel=(), oracle=(),
         diagnostics=None, kind="valid", control_of=None):
    source = clean(source)
    if kind == "valid" and diagnostics is None and evidence == "effect" and rule in POSITIVE_CONTROL_RULES:
        evidence = "positive-control"
    raw = source.encode("ascii")
    sid = identifier(rule, variant, kind)
    completion = (f"IO_LIST_12_6_3 {variant.upper()} OK\n"
                  if kind == "valid" and diagnostics is None and "print '(a)'" in source else "")
    result = dict(id=sid, rule=rule, variant=variant, kind=kind, facets=list(facets), evidence=evidence,
                  source=source, source_sha256=sha(raw), completion=completion, control_of=control_of)
    result["feature_mutations"] = [mutation_span(source, a, b, m, "feature", c) for m, a, b, c in feature]
    result["sentinel_mutations"] = [mutation_span(source, a, b, m, "sentinel", c) for m, a, b, c in sentinel]
    result["oracle_mutations"] = [mutation_span(source, a, b, m, "oracle", c) for m, a, b, c in oracle]
    result["diagnostic"] = diagnostics
    return result


def source_specs():
    specs = []
    specs.append(spec("S12.6.3-001", "basic_input_output",
        ["io-list-specifies-transferred-entities"], r'''
        program io_list_basic_input_output
          implicit none
          integer :: checks
          character(len=2) :: rec
          character(len=6) :: out
          integer :: x, spare
          checks = 0
          rec = '17'
          out = '######'
          x = -777
          spare = -333
          if (x /= -777) error stop 'x pre-read sentinel'
          checks = checks + 1
          read(rec,*) x
          if (x /= 17) error stop 'x read value'
          checks = checks + 1
          if (spare /= -333) error stop 'unlisted entity changed'
          checks = checks + 1
          write(out,'(SS,I2)') x + 5
          if (len(out) /= 6) error stop 'out len'
          checks = checks + 1
          if (out /= '22    ') error stop 'output expression value'
          checks = checks + 1
          if (checks /= 5) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 BASIC_INPUT_OUTPUT OK'
        end program io_list_basic_input_output
        ''', feature=[
            ("remove-read-transfer", "  read(rec,*) x", "  continue", "input-list-transfer"),
            ("read-wrong-variable", "  read(rec,*) x", "  read(rec,*) spare", "input-variable-form"),
            ("output-expression-plus-six", "  write(out,'(SS,I2)') x + 5", "  write(out,'(SS,I2)') x + 6", "output-expression-form"),
        ], sentinel=[
            ("x-init-removed", "  x = -777", "  continue", "input-sentinel"),
            ("x-init-expected", "  x = -777", "  x = 17", "input-sentinel"),
            ("x-init-zero", "  x = -777", "  x = 0", "input-sentinel"),
        ], oracle=[
            ("x-oracle", "if (x /= 17)", "if (x /= 18)", "value-oracle"),
            ("out-oracle", "if (out /= '22    ')", "if (out /= '23    ')", "value-oracle"),
        ]))

    specs.append(spec("R1216", "input_implied_do",
        ["input-io-implied-do-form"], r'''
        program io_list_input_implied_do
          implicit none
          integer :: checks
          character(len=5) :: rec
          integer :: a(3), i
          checks = 0
          rec = '1 2 3'
          a = [-11, -22, -33]
          i = -44
          if (any(a /= [-11, -22, -33])) error stop 'a pre-read sentinel'
          checks = checks + 1
          read(rec,*) (a(i), i = 1, 3)
          if (any(a /= [1, 2, 3])) error stop 'implied-do item order'
          checks = checks + 1
          if (checks /= 2) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 INPUT_IMPLIED_DO OK'
        end program io_list_input_implied_do
        ''', feature=[
            ("remove-implied-do-read", "  read(rec,*) (a(i), i = 1, 3)", "  continue", "remove-feature"),
            ("drop-parenthesized-implied-do", "  read(rec,*) (a(i), i = 1, 3)", "  read(rec,*) a(1)", "parenthesized-form"),
            ("change-object-list", "(a(i), i = 1, 3)", "(a(3), i = 1, 3)", "object-list"),
            ("change-terminal-expr", "(a(i), i = 1, 3)", "(a(i), i = 1, 2)", "terminal-expr"),
            ("change-do-variable", "(a(i), i = 1, 3)", "(a(1), i = 1, 3)", "do-variable-use"),
        ], sentinel=[
            ("a-init-removed", "  a = [-11, -22, -33]", "  continue", "input-sentinel"),
            ("a-init-expected", "  a = [-11, -22, -33]", "  a = [1, 2, 3]", "input-sentinel"),
            ("a-init-zero", "  a = [-11, -22, -33]", "  a = 0", "input-sentinel"),
        ], oracle=[
            ("array-oracle", "if (any(a /= [1, 2, 3]))", "if (any(a /= [1, 3, 2]))", "value-oracle"),
        ]))

    specs.append(spec("R1220", "implied_do_increment",
        ["implied-do-control-do-variable", "implied-do-control-initial-expr", "implied-do-control-terminal-expr", "implied-do-control-optional-increment"], r'''
        program io_list_implied_do_increment
          implicit none
          integer :: checks
          character(len=5) :: rec
          integer :: a(5), j, lo, hi, stride
          checks = 0
          rec = '8 9 7'
          a = [-1, -2, -3, -4, -5]
          lo = 1
          hi = 5
          stride = 2
          if (any(a /= [-1, -2, -3, -4, -5])) error stop 'a pre-read sentinel'
          checks = checks + 1
          read(rec,*) (a(j), j = lo + 1, hi, stride)
          if (any(a /= [-1, 8, -3, 9, -5])) error stop 'increment positions'
          checks = checks + 1
          if (checks /= 2) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 IMPLIED_DO_INCREMENT OK'
        end program io_list_implied_do_increment
        ''', feature=[
            ("change-initial-expr", "j = lo + 1, hi, stride", "j = lo + 2, hi, stride", "initial-expr"),
            ("change-terminal-expr", "j = lo + 1, hi, stride", "j = lo + 1, hi - 2, stride", "terminal-expr"),
            ("change-increment-expr", "j = lo + 1, hi, stride", "j = lo + 1, hi, 1", "increment-expr"),
            ("remove-increment-read", "  read(rec,*) (a(j), j = lo + 1, hi, stride)", "  continue", "remove-feature"),
        ], sentinel=[
            ("a-init-removed", "  a = [-1, -2, -3, -4, -5]", "  continue", "input-sentinel"),
            ("a-init-expected", "  a = [-1, -2, -3, -4, -5]", "  a = [-1, 8, -3, 9, -5]", "input-sentinel"),
            ("a-init-zero", "  a = [-1, -2, -3, -4, -5]", "  a = 0", "input-sentinel"),
        ], oracle=[
            ("positions-oracle", "if (any(a /= [-1, 8, -3, 9, -5]))", "if (any(a /= [-1, 8, -3, 10, -5]))", "value-oracle"),
        ]))

    specs.append(spec("R1217", "output_implied_do",
        ["output-io-implied-do-form"], r'''
        program io_list_output_implied_do
          implicit none
          integer :: checks
          integer :: a(3), i
          character(len=6) :: out
          checks = 0
          a = [2, 4, 6]
          out = '######'
          write(out,'(SS,3I2)') (a(i) + 1, i = 1, 3)
          if (len(out) /= 6) error stop 'out len'
          checks = checks + 1
          if (out /= ' 3 5 7') error stop 'output implied-do values'
          checks = checks + 1
          if (checks /= 2) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 OUTPUT_IMPLIED_DO OK'
        end program io_list_output_implied_do
        ''', feature=[
            ("remove-output-implied-do", "  write(out,'(SS,3I2)') (a(i) + 1, i = 1, 3)", "  continue", "remove-feature"),
            ("change-output-object-expression", "(a(i) + 1, i = 1, 3)", "(a(i) + 2, i = 1, 3)", "output-object"),
            ("change-output-terminal", "(a(i) + 1, i = 1, 3)", "(a(i) + 1, i = 1, 2)", "output-control"),
        ], oracle=[
            ("out-oracle", "if (out /= ' 3 5 7')", "if (out /= ' 4 6 8')", "value-oracle"),
        ]))

    specs.append(spec("S12.6.3-003", "pointer_io",
        ["input-pointer-definable-associated-target", "input-pointer-transfer-to-target"], r'''
        program io_list_pointer_io
          implicit none
          integer :: checks
          character(len=2) :: rec
          character(len=4) :: out
          integer, target :: target
          integer, pointer :: p
          checks = 0
          rec = '31'
          out = '####'
          target = -919
          p => target
          if (.not. associated(p, target)) error stop 'pointer not associated before input'
          checks = checks + 1
          if (target /= -919) error stop 'target pre-read sentinel'
          checks = checks + 1
          read(rec,*) p
          if (target /= 31) error stop 'input pointer target value'
          checks = checks + 1
          target = 42
          write(out,'(SS,I2)') p
          if (len(out) /= 4) error stop 'out len'
          checks = checks + 1
          if (out /= '42  ') error stop 'output pointer target value'
          checks = checks + 1
          if (checks /= 5) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 POINTER_IO OK'
        end program io_list_pointer_io
        ''', feature=[
            ("remove-pointer-read", "  read(rec,*) p", "  continue", "pointer-input"),
            ("output-target-not-pointer", "  write(out,'(SS,I2)') p", "  write(out,'(SS,I2)') target + 1", "pointer-output"),
        ], sentinel=[
            ("target-init-removed", "  target = -919", "  continue", "input-sentinel"),
            ("target-init-expected", "  target = -919", "  target = 31", "input-sentinel"),
            ("target-init-zero", "  target = -919", "  target = 0", "input-sentinel"),
        ], oracle=[
            ("target-oracle", "if (target /= 31)", "if (target /= 32)", "value-oracle"),
            ("out-oracle", "if (out /= '42  ')", "if (out /= '43  ')", "value-oracle"),
        ]))

    specs.append(spec("S12.6.3-005", "allocatable_io",
        ["allocatable-input-item-allocated", "allocatable-output-item-allocated"], r'''
        program io_list_allocatable_io
          implicit none
          integer :: checks
          character(len=2) :: rec
          character(len=4) :: out
          integer, allocatable :: x
          checks = 0
          rec = '26'
          out = '####'
          allocate(x)
          x = -626
          if (.not. allocated(x)) error stop 'allocatable not allocated before input'
          checks = checks + 1
          if (x /= -626) error stop 'allocatable pre-read sentinel'
          checks = checks + 1
          read(rec,*) x
          if (x /= 26) error stop 'allocatable input value'
          checks = checks + 1
          x = 37
          write(out,'(SS,I2)') x
          if (out /= '37  ') error stop 'allocatable output value'
          checks = checks + 1
          if (checks /= 4) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 ALLOCATABLE_IO OK'
        end program io_list_allocatable_io
        ''', feature=[
            ("remove-allocate", "  allocate(x)", "  allocate(x)", "allocated-premise"),
            ("remove-allocatable-read", "  read(rec,*) x", "  continue", "allocatable-input"),
            ("change-allocatable-output", "  write(out,'(SS,I2)') x", "  write(out,'(SS,I2)') x + 1", "allocatable-output"),
        ], sentinel=[
            ("x-init-removed", "  x = -626", "  continue", "input-sentinel"),
            ("x-init-expected", "  x = -626", "  x = 26", "input-sentinel"),
            ("x-init-zero", "  x = -626", "  x = 0", "input-sentinel"),
        ], oracle=[
            ("input-oracle", "if (x /= 26)", "if (x /= 27)", "value-oracle"),
            ("output-oracle", "if (out /= '37  ')", "if (out /= '38  ')", "value-oracle"),
        ]))

    # remove-allocate is deliberately identity-free: replace a separate premise token instead.
    specs[-1]["feature_mutations"][0] = mutation_span(specs[-1]["source"],
        "if (.not. allocated(x)) error stop 'allocatable not allocated before input'",
        "if (allocated(x)) error stop 'allocatable not allocated before input'",
        "allocated-premise-guard", "feature", "allocated-premise")

    specs.append(spec("S12.6.3-001", "read_n_then_slice",
        ["io-list-specifies-transferred-entities"], r'''
        program io_list_read_n_then_slice
          implicit none
          integer :: checks
          character(len=7) :: rec
          integer :: n, a(4)
          checks = 0
          rec = '3 5 6 7'
          n = -303
          a = [-41, -42, -43, -44]
          if (n /= -303) error stop 'n pre-read sentinel'
          checks = checks + 1
          if (any(a /= [-41, -42, -43, -44])) error stop 'a pre-read sentinel'
          checks = checks + 1
          read(rec,*) n, a(1:n)
          if (n /= 3) error stop 'n read before later bound'
          checks = checks + 1
          if (any(a /= [5, 6, 7, -44])) error stop 'slice values'
          checks = checks + 1
          if (checks /= 4) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 READ_N_THEN_SLICE OK'
        end program io_list_read_n_then_slice
        ''', feature=[
            ("remove-n-from-input-list", "  read(rec,*) n, a(1:n)", "  read(rec,*) a(1:3)", "earlier-input-defines-bound"),
            ("change-later-bound", "a(1:n)", "a(1:2)", "later-input-bound"),
        ], sentinel=[
            ("n-init-removed", "  n = -303", "  continue", "input-sentinel"),
            ("n-init-expected", "  n = -303", "  n = 3", "input-sentinel"),
            ("n-init-zero", "  n = -303", "  n = 0", "input-sentinel"),
            ("a-init-removed", "  a = [-41, -42, -43, -44]", "  continue", "input-sentinel"),
            ("a-init-expected", "  a = [-41, -42, -43, -44]", "  a = [5, 6, 7, -44]", "input-sentinel"),
            ("a-init-zero", "  a = [-41, -42, -43, -44]", "  a = 0", "input-sentinel"),
        ], oracle=[
            ("n-oracle", "if (n /= 3)", "if (n /= 4)", "value-oracle"),
            ("slice-oracle", "if (any(a /= [5, 6, 7, -44]))", "if (any(a /= [5, 7, 6, -44]))", "value-oracle"),
        ]))

    specs.append(spec("S12.6.3-012", "array_element_order_input",
        ["array-list-item-expands-in-element-order"], r'''
        program io_list_array_element_order_input
          implicit none
          integer :: checks
          character(len=7) :: rec
          integer :: a(2,2)
          checks = 0
          rec = '1 2 3 4'
          a = reshape([-11, -22, -33, -44], [2, 2])
          if (any(reshape(a, [4]) /= [-11, -22, -33, -44])) error stop 'a pre-read sentinel'
          checks = checks + 1
          read(rec,*) a
          if (any(reshape(a, [4]) /= [1, 2, 3, 4])) error stop 'array element order'
          checks = checks + 1
          if (checks /= 2) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 ARRAY_ELEMENT_ORDER_INPUT OK'
        end program io_list_array_element_order_input
        ''', feature=[
            ("remove-array-read", "  read(rec,*) a", "  continue", "array-item"),
            ("row-order-explicit-list", "  read(rec,*) a", "  read(rec,*) a(1,1), a(1,2), a(2,1), a(2,2)", "array-element-order"),
        ], sentinel=[
            ("a-init-removed", "  a = reshape([-11, -22, -33, -44], [2, 2])", "  continue", "input-sentinel"),
            ("a-init-expected", "  a = reshape([-11, -22, -33, -44], [2, 2])", "  a = reshape([1, 2, 3, 4], [2, 2])", "input-sentinel"),
            ("a-init-zero", "  a = reshape([-11, -22, -33, -44], [2, 2])", "  a = 0", "input-sentinel"),
        ], oracle=[
            ("order-oracle", "if (any(reshape(a, [4]) /= [1, 2, 3, 4]))", "if (any(reshape(a, [4]) /= [1, 3, 2, 4]))", "value-oracle"),
        ]))

    specs.append(spec("S12.6.3-017", "derived_formatted_components",
        ["formatted-derived-component-order-expansion"], r'''
        program io_list_derived_formatted_components
          implicit none
          type :: pair
            integer :: code
            character(len=2) :: tag
          end type pair
          integer :: checks
          type(pair) :: item
          character(len=4) :: rec
          character(len=6) :: out
          checks = 0
          rec = '7 AB'
          item = pair(-8, 'ZZ')
          if (item%code /= -8) error stop 'code pre-read sentinel'
          checks = checks + 1
          if (len(item%tag) /= 2) error stop 'tag len before read'
          checks = checks + 1
          if (item%tag /= 'ZZ') error stop 'tag pre-read sentinel'
          checks = checks + 1
          read(rec,'(I1,1X,A2)') item
          if (item%code /= 7) error stop 'derived read integer component'
          checks = checks + 1
          if (len(item%tag) /= 2) error stop 'tag len after read'
          checks = checks + 1
          if (item%tag /= 'AB') error stop 'derived read character component'
          checks = checks + 1
          item = pair(42, 'QR')
          out = '######'
          write(out,'(SS,I2,A2)') item
          if (out /= '42QR  ') error stop 'derived write component order'
          checks = checks + 1
          if (checks /= 7) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 DERIVED_FORMATTED_COMPONENTS OK'
        end program io_list_derived_formatted_components
        ''', feature=[
            ("remove-derived-read", "  read(rec,'(I1,1X,A2)') item", "  continue", "derived-input-expansion"),
            ("read-only-first-component", "  read(rec,'(I1,1X,A2)') item", "  read(rec,'(I1,1X,A2)') item%code", "derived-input-expansion"),
            ("remove-derived-write", "  write(out,'(SS,I2,A2)') item", "  continue", "derived-output-expansion"),
            ("write-only-first-component", "  write(out,'(SS,I2,A2)') item", "  write(out,'(SS,I2,A2)') item%code", "derived-output-expansion"),
        ], sentinel=[
            ("item-init-removed", "  item = pair(-8, 'ZZ')", "  continue", "input-sentinel"),
            ("item-init-expected", "  item = pair(-8, 'ZZ')", "  item = pair(7, 'AB')", "input-sentinel"),
            ("item-init-zero", "  item = pair(-8, 'ZZ')", "  item = pair(0, '  ')", "input-sentinel"),
        ], oracle=[
            ("code-oracle", "if (item%code /= 7)", "if (item%code /= 8)", "value-oracle"),
            ("tag-oracle", "if (item%tag /= 'AB')", "if (item%tag /= 'AC')", "value-oracle"),
            ("out-oracle", "if (out /= '42QR  ')", "if (out /= '42QS  ')", "value-oracle"),
        ]))

    specs.append(spec("S12.6.3-011", "derived_array_reapplied",
        ["io-list-expansion-rules-reapplied"], r'''
        program io_list_derived_array_reapplied
          implicit none
          type :: nested
            integer :: head
            integer :: values(2)
          end type nested
          integer :: checks
          type(nested) :: item
          character(len=5) :: out
          checks = 0
          item = nested(3, [4, 5])
          out = '#####'
          write(out,'(SS,3I1)') item
          if (out /= '345  ') error stop 'reapplied derived array order'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 DERIVED_ARRAY_REAPPLIED OK'
        end program io_list_derived_array_reapplied
        ''', feature=[
            ("remove-reapplied-write", "  write(out,'(SS,3I1)') item", "  continue", "remove-feature"),
            ("write-head-only", "  write(out,'(SS,3I1)') item", "  write(out,'(SS,3I1)') item%head", "reapply-expansion"),
        ], oracle=[
            ("out-oracle", "if (out /= '345  ')", "if (out /= '354  ')", "value-oracle"),
        ]))

    specs.append(spec("S12.6.3-020", "effective_items_scalar_sequence", ["effective-items-are-expanded-scalar-objects"], r'''
        program io_list_effective_items_scalar_sequence
          implicit none
          type :: pair
            integer :: left
            integer :: right
          end type pair
          integer :: checks
          integer :: a(2)
          type(pair) :: item
          character(len=5) :: out
          checks = 0
          a = [2, 3]
          item = pair(4, 5)
          out = '#####'
          write(out,'(SS,5I1)') 1, a, item
          if (out /= '12345') error stop 'effective scalar sequence'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 EFFECTIVE_ITEMS_SCALAR_SEQUENCE OK'
        end program io_list_effective_items_scalar_sequence
        ''', feature=[
            ("remove-array-effective-items", "  write(out,'(SS,5I1)') 1, a, item", "  write(out,'(SS,5I1)') 1, item", "effective-items"),
            ("change-derived-effective-items", "  write(out,'(SS,5I1)') 1, a, item", "  write(out,'(SS,5I1)') 1, a, item%left", "effective-items"),
        ], oracle=[("out-oracle", "if (out /= '12345')", "if (out /= '12354')", "value-oracle")]))

    specs.append(spec("S12.6.3-021", "zero_effective_items",
        ["zero-sized-array-no-effective-items"], r'''
        program io_list_zero_effective_items
          implicit none
          integer :: checks, i
          integer, allocatable :: empty(:)
          integer :: vals(2)
          character(len=2) :: out_zero_array, out_zero_do
          character(len=1) :: out_zero_char, z
          checks = 0
          vals = [8, 9]
          allocate(empty(0))
          empty = 8
          out_zero_array = '##'
          write(out_zero_array,'(SS,I2,I2)') empty, 7
          if (out_zero_array /= ' 7') error stop 'zero-sized array marker'
          checks = checks + 1
          out_zero_do = '##'
          write(out_zero_do,'(SS,I2,I2)') (vals(i), i = 1, 0), 7
          if (out_zero_do /= ' 7') error stop 'zero-count implied-do marker'
          checks = checks + 1
          z = 'X'
          out_zero_char = '#'
          write(out_zero_char,'(A,I1)') z(:0), 7
          if (len(z(:0)) /= 0) error stop 'zero character len'
          checks = checks + 1
          if (out_zero_char /= '7') error stop 'zero character effective item'
          checks = checks + 1
          if (checks /= 4) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 ZERO_EFFECTIVE_ITEMS OK'
        end program io_list_zero_effective_items
        ''', feature=[
            ("make-array-nonzero-size", "  allocate(empty(0))", "  allocate(empty(1))", "zero-sized-array"),
            ("make-implied-do-one-trip", "(vals(i), i = 1, 0)", "(vals(i), i = 1, 1)", "zero-count-implied-do"),
            ("make-character-nonzero-length", "  write(out_zero_char,'(A,I1)') z(:0), 7", "  write(out_zero_char,'(A,I1)') z(:1), 7", "zero-length-character"),
            ("remove-zero-array-write", "  write(out_zero_array,'(SS,I2,I2)') empty, 7", "  continue", "remove-feature"),
        ], oracle=[
            ("zero-array-oracle", "if (out_zero_array /= ' 7')", "if (out_zero_array /= ' 8')", "value-oracle"),
            ("zero-do-oracle", "if (out_zero_do /= ' 7')", "if (out_zero_do /= ' 8')", "value-oracle"),
            ("zero-char-oracle", "if (out_zero_char /= '7')", "if (out_zero_char /= '8')", "value-oracle"),
        ]))

    specs.append(spec("C1235", "ordinary_procedure_pointer_result_control",
        ["ordinary-output-expression-control"], r'''
        program io_list_ordinary_procedure_pointer_result_control
          implicit none
          abstract interface
            integer function f()
            end function f
          end interface
          integer :: checks
          procedure(f), pointer :: p
          character(len=4) :: out
          checks = 0
          p => value
          out = '####'
          write(out,'(SS,I2)') p()
          if (out /= '12  ') error stop 'procedure pointer result output'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 ORDINARY_PROCEDURE_POINTER_RESULT_CONTROL OK'
        contains
          integer function value()
            value = 12
          end function value
        end program io_list_ordinary_procedure_pointer_result_control
        ''', feature=[
            ("change-invoked-result", "value = 12", "value = 13", "ordinary-expression-result"),
            ("remove-output-expression", "  write(out,'(SS,I2)') p()", "  continue", "ordinary-output-expression"),
        ], oracle=[
            ("out-oracle", "if (out /= '12  ')", "if (out /= '13  ')", "value-oracle"),
        ]))

    specs.append(spec("R1217", "output_expression", ["output-expression-form"], r'''
        program io_list_output_expression
          implicit none
          integer :: checks, x
          character(len=4) :: out
          checks = 0
          x = 6
          out = '####'
          write(out,'(SS,I2)') x + 4
          if (out /= '10  ') error stop 'output expression'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 OUTPUT_EXPRESSION OK'
        end program io_list_output_expression
        ''', feature=[
            ("change-output-expression", "  write(out,'(SS,I2)') x + 4", "  write(out,'(SS,I2)') x + 5", "output-expression"),
            ("remove-output-expression", "  write(out,'(SS,I2)') x + 4", "  continue", "remove-feature"),
        ], oracle=[("out-oracle", "if (out /= '10  ')", "if (out /= '11  ')", "value-oracle")]))

    specs.append(spec("R1218", "io_implied_do_form", ["io-implied-do-parenthesized-form", "io-implied-do-object-list-form", "io-implied-do-control-form"], r'''
        program io_list_io_implied_do_form
          implicit none
          integer :: checks, i
          integer :: a(2), b(2)
          character(len=8) :: out
          checks = 0
          a = [1, 2]
          b = [3, 4]
          out = '########'
          write(out,'(SS,4I1)') (a(i), b(i), i = 1, 2)
          if (out /= '1324    ') error stop 'implied do form'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 IO_IMPLIED_DO_FORM OK'
        end program io_list_io_implied_do_form
        ''', feature=[
            ("remove-parenthesized-implied-do", "  write(out,'(SS,4I1)') (a(i), b(i), i = 1, 2)", "  write(out,'(SS,4I1)') a", "parenthesized-form"),
            ("remove-second-object", "(a(i), b(i), i = 1, 2)", "(a(i), i = 1, 2)", "object-list"),
            ("change-control", "(a(i), b(i), i = 1, 2)", "(a(i), b(i), i = 1, 1)", "control-form"),
        ], oracle=[("out-oracle", "if (out /= '1324    ')", "if (out /= '1234    ')", "value-oracle")]))

    specs.append(spec("R1219", "io_implied_do_objects", ["implied-do-object-input-item-form", "implied-do-object-output-item-form"], r'''
        program io_list_io_implied_do_objects
          implicit none
          integer :: checks, i
          character(len=3) :: rec
          character(len=4) :: out
          integer :: a(2)
          checks = 0
          rec = '5 6'
          a = [-5, -6]
          out = '####'
          if (any(a /= [-5, -6])) error stop 'a pre-read sentinel'
          checks = checks + 1
          read(rec,*) (a(i), i = 1, 2)
          if (any(a /= [5, 6])) error stop 'input object form'
          checks = checks + 1
          write(out,'(SS,2I2)') (a(i) + 1, i = 1, 2)
          if (out /= ' 6 7') error stop 'output object form'
          checks = checks + 1
          if (checks /= 3) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 IO_IMPLIED_DO_OBJECTS OK'
        end program io_list_io_implied_do_objects
        ''', feature=[
            ("remove-input-object", "  read(rec,*) (a(i), i = 1, 2)", "  continue", "input-object"),
            ("change-output-object", "(a(i) + 1, i = 1, 2)", "(a(i) + 2, i = 1, 2)", "output-object"),
        ], sentinel=[
            ("a-init-removed", "  a = [-5, -6]", "  continue", "input-sentinel"),
            ("a-init-expected", "  a = [-5, -6]", "  a = [5, 6]", "input-sentinel"),
            ("a-init-zero", "  a = [-5, -6]", "  a = 0", "input-sentinel"),
        ], oracle=[("input-oracle", "if (any(a /= [5, 6]))", "if (any(a /= [6, 5]))", "value-oracle"),
                   ("output-oracle", "if (out /= ' 6 7')", "if (out /= ' 7 8')", "value-oracle")]))

    specs.append(spec("C1234", "output_implied_do_object_control", ["output-list-implied-do-object-output-item"], r'''
        program io_list_output_implied_do_object_control
          implicit none
          integer :: checks, i
          integer :: a(2)
          character(len=4) :: out
          checks = 0
          a = [7, 8]
          out = '####'
          write(out,'(SS,2I2)') (a(i), i = 1, 2)
          if (out /= ' 7 8') error stop 'output-list implied-do object'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 OUTPUT_IMPLIED_DO_OBJECT_CONTROL OK'
        end program io_list_output_implied_do_object_control
        ''', feature=[
            ("change-output-object-control", "(a(i), i = 1, 2)", "(a(i), i = 2, 1)", "output-list-object"),
            ("remove-output-object-control", "  write(out,'(SS,2I2)') (a(i), i = 1, 2)", "  continue", "remove-feature"),
        ], oracle=[("out-oracle", "if (out /= ' 7 8')", "if (out /= ' 8 7')", "value-oracle")]))

    specs.append(spec("S12.6.3-004", "pointer_output", ["output-pointer-associated-target", "output-pointer-transfer-from-target"], r'''
        program io_list_pointer_output
          implicit none
          integer :: checks
          integer, target :: target
          integer, pointer :: p
          character(len=4) :: out
          checks = 0
          target = 54
          p => target
          out = '####'
          if (.not. associated(p, target)) error stop 'pointer not associated before output'
          checks = checks + 1
          write(out,'(SS,I2)') p
          if (out /= '54  ') error stop 'pointer output target'
          checks = checks + 1
          if (checks /= 2) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 POINTER_OUTPUT OK'
        end program io_list_pointer_output
        ''', feature=[
            ("change-target-value", "  target = 54", "  target = 55", "pointer-target"),
            ("remove-pointer-output", "  write(out,'(SS,I2)') p", "  continue", "remove-feature"),
        ], oracle=[("out-oracle", "if (out /= '54  ')", "if (out /= '55  ')", "value-oracle")]))

    specs.append(spec("S12.6.3-019", "implied_do_execution", ["io-implied-do-do-construct-execution"], r'''
        program io_list_implied_do_execution
          implicit none
          integer :: checks, i
          integer :: a(3)
          character(len=5) :: rec
          checks = 0
          rec = '1 2 3'
          a = [-1, -2, -3]
          if (any(a /= [-1, -2, -3])) error stop 'a pre-read sentinel'
          checks = checks + 1
          read(rec,*) (a(i), i = 1, 3)
          if (any(a /= [1, 2, 3])) error stop 'implied-do execution values'
          checks = checks + 1
          if (i /= 4) error stop 'implied-do execution final variable'
          checks = checks + 1
          if (checks /= 3) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 IMPLIED_DO_EXECUTION OK'
        end program io_list_implied_do_execution
        ''', feature=[
            ("change-execution-terminal", "(a(i), i = 1, 3)", "(a(i), i = 1, 2)", "do-execution"),
            ("remove-execution-read", "  read(rec,*) (a(i), i = 1, 3)", "  continue", "remove-feature"),
        ], sentinel=[
            ("a-init-removed", "  a = [-1, -2, -3]", "  continue", "input-sentinel"),
            ("a-init-expected", "  a = [-1, -2, -3]", "  a = [1, 2, 3]", "input-sentinel"),
            ("a-init-zero", "  a = [-1, -2, -3]", "  a = 0", "input-sentinel"),
        ], oracle=[("values-oracle", "if (any(a /= [1, 2, 3]))", "if (any(a /= [1, 3, 2]))", "value-oracle"),
                   ("final-oracle", "if (i /= 4)", "if (i /= 3)", "value-oracle")]))

    specs.append(spec("S12.6.3-022", "zero_count_implied_do", ["zero-count-implied-do-no-effective-items"], r'''
        program io_list_zero_count_implied_do
          implicit none
          integer :: checks, i
          integer :: vals(2)
          character(len=2) :: out
          checks = 0
          vals = [8, 9]
          out = '##'
          write(out,'(SS,I2,I2)') (vals(i), i = 1, 0), 7
          if (out /= ' 7') error stop 'zero-count implied-do marker'
          checks = checks + 1
          if (checks /= 1) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 ZERO_COUNT_IMPLIED_DO OK'
        end program io_list_zero_count_implied_do
        ''', feature=[
            ("make-implied-do-one-trip", "(vals(i), i = 1, 0)", "(vals(i), i = 1, 1)", "zero-count-implied-do"),
            ("remove-zero-count-write", "  write(out,'(SS,I2,I2)') (vals(i), i = 1, 0), 7", "  continue", "remove-feature"),
        ], oracle=[("out-oracle", "if (out /= ' 7')", "if (out /= ' 8')", "value-oracle")]))

    specs.append(spec("S12.6.3-023", "zero_length_character", ["zero-length-character-is-effective-item"], r'''
        program io_list_zero_length_character
          implicit none
          integer :: checks
          character(len=1) :: out, z
          checks = 0
          z = 'X'
          out = '#'
          write(out,'(A,I1)') z(:0), 7
          if (len(z(:0)) /= 0) error stop 'zero character len'
          checks = checks + 1
          if (out /= '7') error stop 'zero character effective item'
          checks = checks + 1
          if (checks /= 2) error stop 'checks'
          print '(a)', 'IO_LIST_12_6_3 ZERO_LENGTH_CHARACTER OK'
        end program io_list_zero_length_character
        ''', feature=[
            ("make-character-nonzero-length", "  write(out,'(A,I1)') z(:0), 7", "  write(out,'(A,I1)') z(:1), 7", "zero-length-character"),
            ("remove-zero-character-write", "  write(out,'(A,I1)') z(:0), 7", "  continue", "remove-feature"),
        ], oracle=[("out-oracle", "if (out /= '7')", "if (out /= '8')", "value-oracle")]))

    specs.append(spec("R1216", "input_nonvariable_control", ["input-variable-form", "input-nonvariable-rejected"], r'''
        program io_list_input_nonvariable_control
          implicit none
          character(len=1) :: rec
          integer :: x
          rec = '7'
          x = -7
          read(rec,*) x
        end program io_list_input_nonvariable_control
        ''', evidence="positive-control"))
    specs.append(spec("R1216", "input_nonvariable", ["input-nonvariable-rejected"], r'''
        program io_list_input_nonvariable
          implicit none
          character(len=1) :: rec
          rec = '7'
          read(rec,*) 1
        end program io_list_input_nonvariable
        ''', kind="invalid", diagnostics=dict(file="source.f90", line=5, end_line=5,
             excludes_any=EXCLUSIONS), control_of=identifier("R1216", "input_nonvariable_control")))

    specs.append(spec("C1233", "assumed_size_input_control", ["whole-assumed-size-input-item-rejected"], r'''
        subroutine io_list_assumed_size_input_control(a)
          implicit none
          integer :: a(*)
          character(len=1) :: rec
          rec = '5'
          read(rec,*) a(1)
        end subroutine io_list_assumed_size_input_control
        ''', evidence="positive-control"))
    specs.append(spec("C1233", "assumed_size_input", ["whole-assumed-size-input-item-rejected"], r'''
        subroutine io_list_assumed_size_input(a)
          implicit none
          integer :: a(*)
          character(len=1) :: rec
          rec = '5'
          read(rec,*) a
        end subroutine io_list_assumed_size_input
        ''', kind="invalid", diagnostics=dict(file="source.f90", line=6, end_line=6,
             excludes_any=EXCLUSIONS), control_of=identifier("C1233", "assumed_size_input_control")))

    specs.append(spec("C1234", "input_implied_do_expression_control", ["input-list-implied-do-object-input-item"], r'''
        program io_list_input_implied_do_expression_control
          implicit none
          integer :: a(2), i
          character(len=3) :: rec
          rec = '1 2'
          a = -9
          read(rec,*) (a(i), i = 1, 2)
        end program io_list_input_implied_do_expression_control
        ''', evidence="positive-control"))
    specs.append(spec("C1234", "input_implied_do_expression", ["input-list-output-expression-object-rejected"], r'''
        program io_list_input_implied_do_expression
          implicit none
          integer :: a(2), i
          character(len=3) :: rec
          rec = '1 2'
          a = -9
          read(rec,*) (a(i) + 1, i = 1, 2)
        end program io_list_input_implied_do_expression
        ''', kind="invalid", diagnostics=dict(file="source.f90", line=7, end_line=7,
             excludes_any=EXCLUSIONS), control_of=identifier("C1234", "input_implied_do_expression_control")))

    by_id = {row["id"]: row for row in specs}
    if len(by_id) != len(specs):
        raise ValueError("duplicate fixture id")
    return by_id


def all_runtime_mutations(spec):
    return spec.get("feature_mutations", []) + spec.get("sentinel_mutations", []) + spec.get("oracle_mutations", [])


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source fingerprint changed for " + spec["id"])
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span no longer binds for " + spec["id"] + " " + mutation["id"])
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for row in specs.values():
        directory = Path(root) / "tests/fixtures" / ("io_list_12_6_3_" + row["variant"])
        manifest = dict(schema_version=1, id=row["id"], rule=row["rule"], facets=row["facets"],
                        evidence=row["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
        if row["kind"] == "valid" and row.get("completion"):
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                      stdout=row["completion"], stderr="")
        else:
            manifest["expect"] = dict(phase="compile", step="source",
                                      outcome="diagnose" if row["kind"] == "invalid" else "success")
            if row["kind"] == "invalid":
                manifest["expect"]["diagnostic"] = row["diagnostic"]
        row["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        row["manifest"] = manifest
        files[directory / "source.f90"] = row["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        if rule not in by_rule or not facets <= set(by_rule[rule]["facets"]):
            raise ValueError("selected 12.6.3 facet definitions changed for " + rule)
        owner = by_rule[rule]
        for facet in facets:
            owner.setdefault("pending", {}).pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX, ORACLE)
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("12.6.3 generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    old = "This source packet records source accounting and pending plans only, not fixture approval."
    new = ("This source packet records source accounting. Selected io_list_12_6_3 fixtures now supply "
           "executable standard-oracle observations and mutation plans; fixture approval remains separate.")
    before = before.replace(old, new)
    summary = (SUMMARY_BEGIN + "\n"
        "## I/O list runtime and diagnostic observations\n\n"
        "The io_list_12_6_3 fixture family covers variable input items, output expressions, input and output "
        "I/O implied DOs, pointer targets, allocated allocatables, whole-array element order, formatted derived-type "
        "component expansion, zero-contribution items, zero-length character effective items, and the conforming case "
        "where an earlier input item defines a bound used by a later input item. Diagnostic pairs cover a nonvariable "
        "READ item, a whole assumed-size input item, and an output expression inside an input-list implied DO. Every "
        "runtime input target has a nondefault pre-READ sentinel guard and recorded sentinel probes; numeric formatted "
        "output uses SS and exact integer values only.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("io_list_12_6_3 summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    stale = []
    for path, raw in files.items():
        if not path.is_file() or path.read_bytes() != raw:
            stale.append(path.relative_to(root).as_posix())
    if catalogue != updated:
        stale.append(CATALOGUE)
    if (root / VIEW).read_text() != view:
        stale.append(VIEW)
    if check:
        if stale:
            raise ValueError("stale io_list_12_6_3 fixture family: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def compiler_command(compiler, std, source="source.f90", output="program"):
    name = Path(compiler).name.lower()
    flag = ("--std=" + std) if "lfortran" in name else ("-std=" + std)
    return [compiler, flag, source, "-o", output]


def run_mutations(root, compiler, std, label):
    root = Path(root)
    specs = generate(root, check=True)
    runnable = [row for row in specs.values() if row["kind"] == "valid" and row.get("completion")]
    work_root = root / MUTATION_WORK / label
    if work_root.exists():
        shutil.rmtree(work_root)
    failures = []
    total = 0
    try:
        for row in runnable:
            for mutation in all_runtime_mutations(row):
                total += 1
                case_dir = work_root / row["variant"] / mutation["id"]
                case_dir.mkdir(parents=True, exist_ok=True)
                (case_dir / "source.f90").write_bytes(mutated_source(row, mutation))
                cmd = compiler_command(compiler, std)
                compiled = subprocess.run(cmd, cwd=case_dir, text=True, capture_output=True, timeout=30)
                if compiled.returncode != 0:
                    failures.append((row["id"], mutation["id"], "compile", compiled.stdout + compiled.stderr))
                    continue
                ran = subprocess.run([str(case_dir / "program")], cwd=case_dir, text=True,
                                     capture_output=True, timeout=30)
                survived = ran.returncode == 0 and ran.stdout == row["completion"] and ran.stderr == ""
                if survived:
                    failures.append((row["id"], mutation["id"], "survived", ran.stdout + ran.stderr))
        if failures:
            for case, mid, phase, output in failures[:20]:
                print(f"MUTATION {phase}: {case} {mid}\n{output[:1000]}", file=sys.stderr)
            raise SystemExit(f"{len(failures)} / {total} mutations did not compile-and-fail for {label}")
        print(f"Checked {total} io_list_12_6_3 mutations on {label}: all compiled and failed at run time.")
    finally:
        if work_root.exists():
            shutil.rmtree(work_root)
        parent = root / MUTATION_WORK
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-compiler")
    parser.add_argument("--mutation-std")
    parser.add_argument("--mutation-label", default="compiler")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_compiler:
        if not args.mutation_std:
            parser.error("--mutation-std is required with --mutation-compiler")
        run_mutations(args.root, args.mutation_compiler, args.mutation_std, args.mutation_label)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    facets = sorted({facet for row in specs.values() for facet in row["facets"]})
    mutations = sum(len(all_runtime_mutations(row)) for row in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} io_list_12_6_3 cases, "
          f"{len(facets)} distinct facets and {mutations} runtime mutations.")


if __name__ == "__main__":
    main()
