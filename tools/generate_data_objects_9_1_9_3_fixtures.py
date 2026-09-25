#!/usr/bin/env python3
"""Fixtures for Fortran 2023 data object designators, variables, and constants."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "data_objects_9_1_9_3"
PREFIX = TOPIC + "_"
CATALOGUES = {
    "9.1": "doc/catalogues/designator_9_1.json",
    "9.2": "doc/catalogues/variable_9_2.json",
    "9.3": "doc/catalogues/constant_9_3.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}
SUMMARY_BEGIN = "<!-- BEGIN DATA OBJECTS 9.1-9.3 FIXTURES -->"
SUMMARY_END = "<!-- END DATA OBJECTS 9.1-9.3 FIXTURES -->"

COVERED = {
    "R901": {
        "object-name-alternative",
        "array-element-alternative",
        "array-section-alternative",
        "complex-part-designator-alternative",
        "structure-component-alternative",
        "substring-alternative",
    },
    "R902": {
        "designator-variable",
        "function-reference-variable",
        "expression-not-variable",
        "type-parameter-inquiry-boundary",
    },
    "C901": {"named-constant-excluded"},
    "C902": {
        "data-pointer-result-admission",
        "nonpointer-result-excluded",
        "procedure-pointer-result-excluded",
    },
    "S9.2-001": {
        "designator-denotes-object",
        "function-reference-denotes-target",
        "associated-pointer-required",
    },
    "S9.2-002": {
        "defined-variable-reference",
        "defined-pointer-target-reference",
        "definition-event-source",
    },
    "R903": {"single-name-token", "not-designator-syntax"},
    "C903": {"ordinary-variable-name"},
    "R905": {"designator-character-variable"},
    "C905": {"character-type-admission"},
    "R907": {"designator-integer-variable", "function-reference-integer-variable"},
    "C907": {"integer-type-admission"},
    "S9.3-001": {
        "literal-constant-reference",
        "named-constant-reference",
        "parameter-attribute-source",
        "constant-subobject-reference",
    },
}

PENDING_REASONS = {
    "R901": {
        "coindexed-named-object-alternative": (
            "PENDING after batch300: coindexed named objects require coarray/multi-image support, "
            "which this single-image fixture packet does not exercise."
        ),
    },
    "C901": {
        "constant-array-element-excluded": (
            "PENDING after batch300: gfortran diagnoses the constant element assignment, but the "
            "frozen LFortran build emits LLVM/code-generation output rather than a located diagnostic."
        ),
        "constant-structure-component-excluded": (
            "PENDING after batch300: gfortran diagnoses the constant component assignment, but the "
            "frozen LFortran build emits LLVM/code-generation output rather than a located diagnostic."
        ),
        "literal-substring-excluded": (
            "PENDING after batch300: processors disagree on parsing a literal substring assignment; "
            "no portable one-property diagnostic/control pair was retained."
        ),
    },
    "R904": {
        "designator-logical-variable": (
            "PENDING after batch300: the available scalar-logical-variable contexts are coarray "
            "synchronization forms outside this single-image packet."
        ),
        "function-reference-logical-variable": (
            "PENDING after batch300: the available scalar-logical-variable contexts are coarray "
            "synchronization forms outside this single-image packet."
        ),
    },
    "C904": {
        "logical-type-admission": (
            "PENDING after batch300: logical-variable contexts found for this packet are coarray "
            "synchronization forms outside scope."
        ),
        "nonlogical-exclusion": (
            "PENDING after batch300: the diagnostic would be in a coarray synchronization context "
            "not exercised by this single-image suite."
        ),
    },
    "R905": {
        "function-reference-character-variable": (
            "PENDING after batch300: gfortran rejects a character data-pointer function reference as "
            "an internal-file variable, so there is no reference-validating runtime case."
        ),
    },
    "C905": {
        "noncharacter-exclusion": (
            "PENDING after batch300: the tested internal-file context treats an INTEGER expression as "
            "an external unit number, not as a one-property C905 violation."
        ),
    },
    "R906": {
        "designator-default-character-variable": (
            "PENDING after batch300: IOMSG/ERRMSG default-character contexts either leave the variable "
            "unchanged on success or assign processor-dependent text on error; no exact feature-sensitive "
            "oracle was retained."
        ),
        "function-reference-default-character-variable": (
            "PENDING after batch300: the frozen LFortran build rejects an IOMSG data-pointer function "
            "reference as a non-variable expression."
        ),
    },
    "C906": {
        "default-character-admission": (
            "PENDING after batch300: no exact portable runtime oracle was found for reaching a "
            "default-char-variable context without relying on processor-dependent IOMSG/ERRMSG text."
        ),
        "nondefault-character-exclusion": (
            "PENDING after batch300: support for a distinct nondefault character kind is optional and "
            "not established for both validation toolchains."
        ),
    },
    "C907": {
        "noninteger-exclusion": (
            "PENDING after batch300: gfortran diagnoses REAL STAT=, but frozen LFortran reaches backend "
            "output instead of a located diagnostic."
        ),
    },
    "S9.3-001": {
        "constant-redefinition-prohibited": (
            "PENDING after batch300: the executable diagnostic owner is 9.2 C901 for a designator "
            "variable that denotes a constant; this prose facet is not given a separate rejection oracle."
        ),
    },
}

ORACLE_PREFIX = {rule: f"{rule} data-objects batch300 fixtures: " for rule in COVERED}
LIMIT_PREFIX = {rule: f"{rule} data-objects batch300 boundaries: " for rule in COVERED}
ORACLES = {
    "R901": ORACLE_PREFIX["R901"] + (
        "one positive-control program references an object name, an array element, an array section, "
        "complex %RE/%IM designators, a structure component, and a substring after explicit definition. "
        "Each selected designator has its own exact assertion and a conforming feature mutation that "
        "selects a different object or subobject. Coindexed designators remain pending as coarray-only."
    ),
    "R902": ORACLE_PREFIX["R902"] + (
        "one positive-control program assigns through an ordinary designator and through an INTEGER "
        "data-pointer function reference; one diagnostic pair rejects an expression and a type-parameter "
        "inquiry in assignment-variable position, with a runtime control that uses ordinary variables."
    ),
    "C901": ORACLE_PREFIX["C901"] + (
        "one diagnostic/control pair attempts to assign to an INTEGER named constant and repairs only "
        "the PARAMETER attribute. The control mutates the assignment value and reads it back."
    ),
    "C902": ORACLE_PREFIX["C902"] + (
        "one positive-control program assigns through three data-pointer function references serving as "
        "the admission case and the one-property controls for nonpointer and procedure-pointer results. "
        "Two negative modules change only the result category and require a located diagnostic."
    ),
    "S9.2-001": ORACLE_PREFIX["S9.2-001"] + (
        "one runtime program observes that a designator denotes its object, a function-reference variable "
        "defines the target of the evaluated associated pointer, and a selected associated pointer target "
        "is the variable. Mutants redirect values or the selected association path."
    ),
    "S9.2-002": ORACLE_PREFIX["S9.2-002"] + (
        "one runtime program references only variables already defined by intrinsic assignment, a defined "
        "associated pointer target, and an internal WRITE definition event. Mutants change the defining "
        "events while preserving definedness."
    ),
    "R903": ORACLE_PREFIX["R903"] + (
        "one namelist positive control reads a scalar variable-name token and a second scalar name used "
        "as the one-property repair for an array-element namelist object. The invalid fixture supplies the "
        "x(1) designator contrast."
    ),
    "C903": ORACLE_PREFIX["C903"] + (
        "one namelist positive control reads an ordinary variable-name and observes the assigned value. "
        "Named-constant and procedure-name exclusions remain pending because the frozen LFortran build "
        "does not provide suitable located diagnostics for the planned contrasts."
    ),
    "R905": ORACLE_PREFIX["R905"] + (
        "one positive-control internal WRITE uses a CHARACTER designator as the internal-file variable "
        "and checks the exact buffer contents after the write."
    ),
    "C905": ORACLE_PREFIX["C905"] + (
        "one positive-control internal WRITE uses a CHARACTER variable and checks exact character length "
        "and contents, demonstrating the character-type admission route."
    ),
    "R907": ORACLE_PREFIX["R907"] + (
        "one ALLOCATE STAT= program uses both an INTEGER designator and an INTEGER data-pointer function "
        "reference as int-variables; exact zero STAT values are checked after successful allocation."
    ),
    "C907": ORACLE_PREFIX["C907"] + (
        "one ALLOCATE STAT= positive control observes that an INTEGER variable is accepted and defined "
        "with zero on successful allocation."
    ),
    "S9.3-001": ORACLE_PREFIX["S9.3-001"] + (
        "one positive-control program references literal constants, named constants from both PARAMETER "
        "forms, and constant array/character subobjects in value contexts only. All oracles are exact "
        "integer or character values with length checked before equality."
    ),
}
LIMITATIONS = {
    rule: LIMIT_PREFIX[rule] + (
        "Only the listed batch300 facets are bound. The fixtures assert exact integer, logical, and "
        "character properties after explicit definition, or located diagnostics for numbered syntax/" 
        "constraint cases that both retained toolchains report. They do not assert addresses, storage "
        "layout, processor-dependent IOMSG text, coarray behavior, undefined references, generic warning "
        "policy, source review state, or any facet left pending with a batch300 reason."
    ) for rule in COVERED
}

EXCLUDES = [
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
]

@dataclass(frozen=True)
class Case:
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[dict, ...] = ()
    invalid: bool = False
    diagnostic: Optional[dict] = None
    completion: Optional[str] = None

    @property
    def id(self):
        validity = "invalid" if self.invalid else "valid"
        return self.rule.replace(".", "_").replace("-", "_") + f"_{validity}__" + PREFIX + self.variant


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def mut(mid, facet, replacements):
    return {"id": mid, "facet": facet, "kind": "feature", "replacements": replacements}


def header(rule, facets, evidence):
    return (
        f"! rule: {rule}\n"
        f"! covers: {' '.join(facets)}\n"
        f"! evidence: {evidence}\n"
        "! standard: f2023\n"
        "! oracle-basis: standard\n"
    )

HELPERS = """contains
  subroutine expect_true(ok, label)
    logical, intent(in) :: ok
    character(len=*), intent(in) :: label
    if (.not. ok) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'DATAOBJ-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char(observed, expected, label)
    character(len=*), intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-LEN', label
      error stop
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-CHAR', label
      error stop
    end if
    checks = checks + 1
  end subroutine
"""


def finish(program, completion, total):
    return (
        f"  call expect_int(checks, {total}, 'check count before completion')\n"
        f"  write(*,'(a)') '{completion.rstrip()}'\n"
        + HELPERS
        + f"end program {program}\n"
    )


def make_cases():
    cases = []

    def valid(variant, rule, facets, body, mutations, *, prefix="", evidence="positive-control", total=None):
        completion = "DATA OBJECTS " + variant.upper().replace("_", " ") + " OK\n"
        source = header(rule, facets, evidence) + prefix + body + finish("dataobj_" + variant, completion, total or len(facets))
        cases.append(Case(variant, rule, tuple(facets), evidence, source, tuple(mutations), False, None, completion))

    def invalid(variant, rule, facets, source, line, contains):
        source = header(rule, facets, "effect") + source
        diagnostic = {"file": "source.f90", "line": line + 2, "end_line": line + 2,
                      "contains_any": contains, "excludes_any": EXCLUDES}
        cases.append(Case(variant, rule, tuple(facets), "effect", source, (), True, diagnostic, None))

    valid(
        "designator_forms",
        "R901",
        [
            "object-name-alternative", "array-element-alternative", "array-section-alternative",
            "complex-part-designator-alternative", "structure-component-alternative", "substring-alternative",
        ],
        """program dataobj_designator_forms
  implicit none
  type :: person_t
    integer :: age
    integer :: code
  end type
  integer :: scalar_value, other_scalar, arr(3), section_values(2), checks
  complex :: z
  type(person_t) :: person
  character(len=5) :: text
  checks = 0
  scalar_value = 11
  other_scalar = 12
  arr = [11, 22, 33]
  z = (3.0, 4.0)
  person = person_t(37, 99)
  text = 'abcde'
  call expect_int(scalar_value, 11, 'object name designator')
  call expect_int(arr(2), 22, 'array element designator')
  section_values = arr(1:3:2)
  call expect_int(size(section_values), 2, 'array section extent')
  call expect_int(sum(section_values), 44, 'array section values')
  call expect_int(int(z%im), 4, 'complex part designator')
  call expect_int(person%age, 37, 'structure component designator')
  call expect_char(text(2:4), 'bcd', 'substring designator')
""",
        [
            mut("object-name-other-object", "object-name-alternative",
                [("call expect_int(scalar_value, 11, 'object name designator')",
                  "call expect_int(other_scalar, 11, 'object name designator')")]),
            mut("array-element-first", "array-element-alternative",
                [("call expect_int(arr(2), 22, 'array element designator')",
                  "call expect_int(arr(1), 22, 'array element designator')")]),
            mut("array-section-contiguous", "array-section-alternative",
                [("section_values = arr(1:3:2)", "section_values = arr(1:2)")]),
            mut("complex-part-real", "complex-part-designator-alternative",
                [("call expect_int(int(z%im), 4, 'complex part designator')",
                  "call expect_int(int(z%re), 4, 'complex part designator')")]),
            mut("structure-component-code", "structure-component-alternative",
                [("call expect_int(person%age, 37, 'structure component designator')",
                  "call expect_int(person%code, 37, 'structure component designator')")]),
            mut("substring-first-three", "substring-alternative",
                [("call expect_char(text(2:4), 'bcd', 'substring designator')",
                  "call expect_char(text(1:3), 'bcd', 'substring designator')")]),
        ],
        total=7,
    )

    valid(
        "variable_alternatives",
        "R902",
        ["designator-variable", "function-reference-variable"],
        """program dataobj_variable_alternatives
  use dataobj_r902_pointer_m
  implicit none
  integer :: x, checks
  checks = 0
  x = 11
  call expect_int(x, 11, 'designator variable assignment')
  ip() = 23
  call expect_int(target_value, 23, 'function reference variable assignment')
""",
        [
            mut("designator-assignment-value", "designator-variable", [("x = 11", "x = 12")]),
            mut("function-reference-assignment-value", "function-reference-variable", [("ip() = 23", "ip() = 24")]),
        ],
        prefix="""module dataobj_r902_pointer_m
  implicit none
  integer, target, save :: target_value = -101
contains
  function ip() result(p)
    integer, pointer :: p
    p => target_value
  end function
end module dataobj_r902_pointer_m
""",
    )

    valid(
        "variable_boundary_control",
        "R902",
        ["expression-not-variable", "type-parameter-inquiry-boundary"],
        """program dataobj_variable_boundary_control
  implicit none
  integer :: x, len_value, checks
  character(len=3) :: c
  checks = 0
  c = 'abc'
  x = 7
  len_value = len(c)
  call expect_int(x, 7, 'ordinary variable repair for expression lhs')
  call expect_int(len_value, 3, 'ordinary variable repair for len inquiry')
""",
        [
            mut("expression-repair-value", "expression-not-variable", [("x = 7", "x = 8")]),
            mut("len-inquiry-repair-value", "type-parameter-inquiry-boundary", [("len_value = len(c)", "len_value = len(c) + 1")]),
        ],
    )
    invalid("expression_not_variable", "R902", ["expression-not-variable"],
            """program dataobj_expression_not_variable
  implicit none
  integer :: x
  (x + 0) = 7
end program dataobj_expression_not_variable
""", 7, ["Unclassifiable statement", "LHS of assignment"])
    invalid("type_parameter_inquiry_boundary", "R902", ["type-parameter-inquiry-boundary"],
            """program dataobj_type_parameter_inquiry_boundary
  implicit none
  character(len=3) :: c
  c%len = 4
end program dataobj_type_parameter_inquiry_boundary
""", 7, ["constant expression", "LHS of assignment"])

    valid(
        "c901_named_constant_control",
        "C901",
        ["named-constant-excluded"],
        """program dataobj_c901_named_constant_control
  implicit none
  integer :: k = 1
  integer :: checks
  checks = 0
  k = 2
  call expect_int(k, 2, 'ordinary variable repair for named constant')
""",
        [mut("named-constant-control-value", "named-constant-excluded", [("k = 2", "k = 3")])],
    )
    invalid("c901_named_constant", "C901", ["named-constant-excluded"],
            """program dataobj_c901_named_constant
  implicit none
  integer, parameter :: k = 1
  k = 2
end program dataobj_c901_named_constant
""", 7, ["Named constant", "constant variable"])

    valid(
        "c902_data_pointer_controls",
        "C902",
        ["data-pointer-result-admission", "nonpointer-result-excluded", "procedure-pointer-result-excluded"],
        """program dataobj_c902_data_pointer_controls
  use dataobj_c902_pointer_m
  implicit none
  integer :: checks
  checks = 0
  p_admit() = 31
  call expect_int(admit_target, 31, 'data pointer function result admission')
  p_nonptr_repair() = 41
  call expect_int(nonptr_target, 41, 'data pointer repair for nonpointer result')
  p_proc_repair() = 51
  call expect_int(proc_target, 51, 'data pointer repair for procedure pointer result')
""",
        [
            mut("admission-target-value", "data-pointer-result-admission", [("p_admit() = 31", "p_admit() = 32")]),
            mut("nonpointer-repair-value", "nonpointer-result-excluded", [("p_nonptr_repair() = 41", "p_nonptr_repair() = 42")]),
            mut("procedure-pointer-repair-value", "procedure-pointer-result-excluded", [("p_proc_repair() = 51", "p_proc_repair() = 52")]),
        ],
        prefix="""module dataobj_c902_pointer_m
  implicit none
  integer, target, save :: admit_target = -1, nonptr_target = -2, proc_target = -3
contains
  function p_admit() result(p)
    integer, pointer :: p
    p => admit_target
  end function
  function p_nonptr_repair() result(p)
    integer, pointer :: p
    p => nonptr_target
  end function
  function p_proc_repair() result(p)
    integer, pointer :: p
    p => proc_target
  end function
end module dataobj_c902_pointer_m
""",
    )
    invalid("c902_nonpointer_result", "C902", ["nonpointer-result-excluded"],
            """module dataobj_c902_nonpointer_m
contains
  function f() result(r)
    integer :: r
    r = 1
  end function
end module dataobj_c902_nonpointer_m
program dataobj_c902_nonpointer_result
  use dataobj_c902_nonpointer_m
  implicit none
  f() = 31
end program dataobj_c902_nonpointer_result
""", 14, ["function result", "LHS of assignment"])
    invalid("c902_procedure_pointer_result", "C902", ["procedure-pointer-result-excluded"],
            """module dataobj_c902_procedure_m
  implicit none
  abstract interface
    subroutine sub_i()
    end subroutine
  end interface
contains
  subroutine target_sub()
  end subroutine
  function f() result(p)
    procedure(sub_i), pointer :: p
    p => target_sub
  end function
end module dataobj_c902_procedure_m
program dataobj_c902_procedure_pointer_result
  use dataobj_c902_procedure_m
  implicit none
  f() = 31
end program dataobj_c902_procedure_pointer_result
""", 21, ["function result", "Type mismatch"])

    valid(
        "variable_identity",
        "S9.2-001",
        ["designator-denotes-object", "function-reference-denotes-target", "associated-pointer-required"],
        """program dataobj_variable_identity
  use dataobj_identity_pointer_m
  implicit none
  integer :: x, checks
  checks = 0
  x = 41
  call expect_int(x, 41, 'designator denotes the assigned object')
  target_a = -5
  ip() = 42
  call expect_int(target_a, 42, 'function reference denotes pointer target')
  choose_first = .true.
  selected_ptr() = 52
  call expect_int(first_selected, 52, 'associated pointer selected first target')
""",
        [
            mut("designator-identity-value", "designator-denotes-object", [("x = 41", "x = 40")]),
            mut("function-target-value", "function-reference-denotes-target", [("ip() = 42", "ip() = 43")]),
            mut("associated-selected-other", "associated-pointer-required", [("  choose_first = .true.\n  selected_ptr() = 52", "  choose_first = .false.\n  selected_ptr() = 52")]),
        ],
        prefix="""module dataobj_identity_pointer_m
  implicit none
  integer, target, save :: target_a = -1, first_selected = -2, second_selected = 53
  logical, save :: choose_first = .true.
contains
  function ip() result(p)
    integer, pointer :: p
    p => target_a
  end function
  function selected_ptr() result(p)
    integer, pointer :: p
    if (choose_first) then
      p => first_selected
    else
      p => second_selected
    end if
  end function
end module dataobj_identity_pointer_m
""",
        evidence="effect",
    )

    valid(
        "defined_references",
        "S9.2-002",
        ["defined-variable-reference", "defined-pointer-target-reference", "definition-event-source"],
        """program dataobj_defined_references
  implicit none
  integer, target :: t
  integer, pointer :: p
  integer :: x, checks
  character(len=2) :: buffer
  checks = 0
  x = 51
  call expect_int(x, 51, 'defined variable reference after assignment')
  t = 61
  p => t
  call expect_int(p, 61, 'defined target reference through pointer')
  buffer = '##'
  write(buffer, '(i2)') 73
  call expect_char(buffer, '73', 'internal write definition event')
""",
        [
            mut("defined-variable-value", "defined-variable-reference", [("x = 51", "x = 50")]),
            mut("defined-pointer-target-value", "defined-pointer-target-reference", [("t = 61", "t = 60")]),
            mut("internal-write-value", "definition-event-source", [("write(buffer, '(i2)') 73", "write(buffer, '(i2)') 74")]),
        ],
        evidence="effect",
    )

    valid(
        "variable_name_token_control",
        "R903",
        ["single-name-token", "not-designator-syntax"],
        """program dataobj_variable_name_token_control
  implicit none
  integer :: x, z, y, w, ios, checks
  character(len=32) :: input_one, input_two
  namelist /grp_one/ x
  namelist /grp_two/ z
  checks = 0
  x = -777
  z = -888
  y = -1
  w = -2
  input_one = '&grp_one x=64 /'
  input_two = '&grp_two z=74 /'
  read(input_one, nml=grp_one, iostat=ios)
  call expect_int(ios, 0, 'single name token namelist read status')
  call expect_int(x, 64, 'single variable-name token')
  read(input_two, nml=grp_two, iostat=ios)
  call expect_int(ios, 0, 'designator repair namelist read status')
  call expect_int(z, 74, 'simple name repair for designator syntax')
""",
        [
            mut("single-token-different-name", "single-name-token",
                [("namelist /grp_one/ x", "namelist /grp_one/ y"), ("input_one = '&grp_one x=64 /'", "input_one = '&grp_one y=64 /'")]),
            mut("designator-repair-different-name", "not-designator-syntax",
                [("namelist /grp_two/ z", "namelist /grp_two/ w"), ("input_two = '&grp_two z=74 /'", "input_two = '&grp_two w=74 /'")]),
        ],
        total=4,
    )
    invalid("r903_designator_not_name", "R903", ["not-designator-syntax"],
            """program dataobj_r903_designator_not_name
  implicit none
  integer :: x(2)
  namelist /grp/ x(1)
end program dataobj_r903_designator_not_name
""", 7, ["Syntax error", "Newline is unexpected"])

    valid(
        "c903_ordinary_variable_name",
        "C903",
        ["ordinary-variable-name"],
        """program dataobj_c903_ordinary_variable_name
  implicit none
  integer :: ordinary, other, ios, checks
  character(len=32) :: input
  namelist /grp/ ordinary
  checks = 0
  ordinary = -909
  other = -1
  input = '&grp ordinary=71 /'
  read(input, nml=grp, iostat=ios)
  call expect_int(ios, 0, 'ordinary variable-name namelist status')
  call expect_int(ordinary, 71, 'ordinary variable-name value')
""",
        [mut("ordinary-variable-other-name", "ordinary-variable-name",
             [("namelist /grp/ ordinary", "namelist /grp/ other"),
              ("input = '&grp ordinary=71 /'", "input = '&grp other=71 /'")])],
        total=2,
    )

    valid(
        "char_variable_designator",
        "R905",
        ["designator-character-variable"],
        """program dataobj_char_variable_designator
  implicit none
  character(len=4) :: buffer, other_buffer
  integer :: checks
  checks = 0
  buffer = '####'
  other_buffer = '????'
  write(buffer, '(a)') 'ok'
  call expect_char(buffer(1:2), 'ok', 'character designator internal file')
""",
        [mut("char-designator-other-buffer", "designator-character-variable",
             [("write(buffer, '(a)') 'ok'", "write(other_buffer, '(a)') 'ok'")])],
    )

    valid(
        "character_type_admission",
        "C905",
        ["character-type-admission"],
        """program dataobj_character_type_admission
  implicit none
  character(len=5) :: buffer, other_buffer
  integer :: checks
  checks = 0
  buffer = '#####'
  other_buffer = '?????'
  write(buffer, '(a)') 'abc'
  call expect_int(len(buffer), 5, 'character variable length')
  call expect_char(buffer(1:3), 'abc', 'character variable internal write')
""",
        [mut("character-type-other-buffer", "character-type-admission",
             [("write(buffer, '(a)') 'abc'", "write(other_buffer, '(a)') 'abc'")])],
        total=2,
    )

    valid(
        "int_variable_stat",
        "R907",
        ["designator-integer-variable", "function-reference-integer-variable"],
        """program dataobj_int_variable_stat
  use dataobj_r907_stat_m
  implicit none
  integer, allocatable :: a, b
  integer :: s, other_s, checks
  checks = 0
  s = -777
  other_s = -888
  allocate(a, stat=s)
  call expect_int(s, 0, 'integer designator STAT variable')
  stat_target = -999
  allocate(b, stat=stat_ptr())
  call expect_int(stat_target, 0, 'integer function-reference STAT variable')
""",
        [
            mut("stat-designator-other", "designator-integer-variable", [("allocate(a, stat=s)", "allocate(a, stat=other_s)")]),
            mut("stat-function-other", "function-reference-integer-variable", [("allocate(b, stat=stat_ptr())", "allocate(b, stat=other_stat_ptr())")]),
        ],
        prefix="""module dataobj_r907_stat_m
  implicit none
  integer, target, save :: stat_target = -1, other_stat_target = -2
contains
  function stat_ptr() result(p)
    integer, pointer :: p
    p => stat_target
  end function
  function other_stat_ptr() result(p)
    integer, pointer :: p
    p => other_stat_target
  end function
end module dataobj_r907_stat_m
""",
    )

    valid(
        "integer_type_admission",
        "C907",
        ["integer-type-admission"],
        """program dataobj_integer_type_admission
  implicit none
  integer, allocatable :: a
  integer :: stat_value, other_stat, checks
  checks = 0
  stat_value = -777
  other_stat = -888
  allocate(a, stat=stat_value)
  call expect_int(stat_value, 0, 'integer STAT variable type admission')
""",
        [mut("integer-type-other-stat", "integer-type-admission",
             [("allocate(a, stat=stat_value)", "allocate(a, stat=other_stat)")])],
    )

    valid(
        "constant_references",
        "S9.3-001",
        ["literal-constant-reference", "named-constant-reference", "parameter-attribute-source", "constant-subobject-reference"],
        """program dataobj_constant_references
  implicit none
  integer, parameter :: k = 81
  character(len=*), parameter :: word = 'ok'
  integer :: stmt_param
  parameter (stmt_param = 5)
  integer, parameter :: arr(3) = [11, 22, 33]
  character(len=*), parameter :: letters = 'abcd'
  integer :: literal_total, checks
  checks = 0
  literal_total = 1 + 2
  call expect_int(literal_total, 3, 'literal constants in value context')
  call expect_int(k, 81, 'named integer constant reference')
  call expect_char(word, 'ok', 'named character constant reference')
  call expect_int(stmt_param + 6, 11, 'PARAMETER statement named constant')
  call expect_int(arr(2), 22, 'constant array element reference')
  call expect_char(letters(2:3), 'bc', 'constant substring reference')
""",
        [
            mut("literal-value", "literal-constant-reference", [("literal_total = 1 + 2", "literal_total = 1 + 3")]),
            mut("named-constant-value", "named-constant-reference", [("integer, parameter :: k = 81", "integer, parameter :: k = 82")]),
            mut("parameter-statement-value", "parameter-attribute-source", [("parameter (stmt_param = 5)", "parameter (stmt_param = 6)")]),
            mut("constant-subobject-selection", "constant-subobject-reference", [("call expect_int(arr(2), 22", "call expect_int(arr(1), 22")]),
        ],
        total=6,
    )

    return {case.id: case for case in cases}


def manifest(case):
    data = {
        "schema_version": 1,
        "id": case.id,
        "rule": case.rule,
        "facets": list(case.facets),
        "evidence": case.evidence,
        "standard": "f2023",
        "oracle_basis": "standard",
        "files": ["source.f90"],
        "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
    }
    if case.invalid:
        data["expect"] = {"phase": "compile", "step": "source", "outcome": "diagnose", "diagnostic": case.diagnostic}
    else:
        data["link"] = {"driver": "fortran", "objects": ["source.o"], "output": "program"}
        data["expect"] = {"phase": "run", "outcome": "success", "exit_code": 0, "stdout": case.completion, "stderr": ""}
    return data


def mutation_records(case):
    records = []
    for mutation in case.mutations:
        changed = case.source
        repls = []
        for expected, replacement in mutation["replacements"]:
            count = changed.count(expected)
            if count != 1:
                raise ValueError(f"{case.variant}:{mutation['id']} expected unique text {expected!r}, saw {count}")
            start = changed.index(expected)
            repls.append({"expected": expected, "replacement": replacement, "span": [start, start + len(expected)]})
            changed = changed[:start] + replacement + changed[start + len(expected):]
        if changed == case.source:
            raise ValueError(f"{case.variant}:{mutation['id']} did not change source")
        item = copy.deepcopy(mutation)
        item["replacements"] = repls
        item["mutant_sha256"] = sha(changed.encode("ascii"))
        records.append(item)
    return records


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for cid, case in make_cases().items():
        raw = case.source.encode("ascii")
        directory = root / "tests" / "fixtures" / (PREFIX + case.variant)
        spec = {
            "id": cid,
            "variant": case.variant,
            "rule": case.rule,
            "facets": list(case.facets),
            "kind": "invalid" if case.invalid else "valid",
            "evidence": case.evidence,
            "source": case.source,
            "source_sha256": sha(raw),
            "manifest": manifest(case),
            "path": directory.relative_to(root).as_posix() + "/fixture.json",
            "mutations": mutation_records(case),
        }
        if case.completion:
            spec["completion"] = case.completion
        specs[cid] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def synced_catalogue(section, catalogue, specs):
    result = copy.deepcopy(catalogue)
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for req in result["requirements"]:
        rule = req["id"]
        for facet in covered.get(rule, set()):
            req.setdefault("pending", {}).pop(facet, None)
        for facet, reason in PENDING_REASONS.get(rule, {}).items():
            if facet in req.get("facets", []):
                req.setdefault("pending", {})[facet] = reason
        if rule in COVERED:
            selected = COVERED[rule]
            if not selected <= set(req["facets"]):
                raise ValueError(f"selected facets changed for {rule}")
            req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIX[rule], ORACLES[rule])
            req["oracle_limitation"] = owned_paragraph(
                req.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMITATIONS[rule])
    return result


def rendered_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed for " + section)
    before, rest = text.split(begin)
    _, after = rest.split(end)
    if section == "9.1":
        summary = (
            SUMMARY_BEGIN + "\n"
            "## Data object designator/variable/constant fixtures\n\n"
            "Batch300 adds runtime positive controls and selected diagnostics for non-coarray "
            "designators, variables, typed variable contexts, and constants in 9.1-9.3. Coindexed "
            "designators, logical-variable coarray synchronization contexts, and diagnostics that "
            "one retained toolchain does not locate remain pending in their owning requirements.\n"
            + SUMMARY_END
        )
        if SUMMARY_BEGIN in before and SUMMARY_END in before:
            leading, owned = before.split(SUMMARY_BEGIN)
            _, trailing = owned.split(SUMMARY_END)
            before = leading + summary + trailing
        else:
            before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generated_catalogues_and_views(root, specs):
    root = Path(root)
    cat_out, view_out = {}, {}
    for section, rel in CATALOGUES.items():
        updated = synced_catalogue(section, json.loads((root / rel).read_text()), specs)
        cat_out[rel] = updated
        view_out[VIEWS[section]] = rendered_view(section, updated, root)
    return cat_out, view_out


def generate(root=ROOT, check=False):
    root = Path(root)
    files, specs = build_corpus(root)
    cats, views = generated_catalogues_and_views(root, specs)
    stale = []
    if check:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                stale.append(path.relative_to(root).as_posix())
        for rel, data in cats.items():
            if json.loads((root / rel).read_text()) != data:
                stale.append(rel)
        for rel, text in views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise SystemExit("stale data_objects_9_1_9_3 generated files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for rel, data in cats.items():
            (root / rel).write_text(json.dumps(data, indent=2) + "\n")
        for rel, text in views.items():
            (root / rel).write_text(text)
    return files, specs


def mutate_source(spec, mutation, allow_identical=False):
    changed = spec["source"]
    for repl in mutation["replacements"]:
        expected, replacement = repl["expected"], repl["replacement"]
        if changed.count(expected) != 1:
            raise ValueError(f"{spec['variant']}:{mutation['id']} replacement not bound: {expected!r}")
        changed = changed.replace(expected, replacement, 1)
    if changed == spec["source"] and not allow_identical:
        raise ValueError(f"{spec['variant']}:{mutation['id']} did not change source")
    return changed


def std_flag(compiler, std):
    return "--std=" + std if "lfortran" in Path(compiler).name.lower() else "-std=" + std


def run_command(argv, cwd, timeout=40):
    env = os.environ.copy()
    env["TMPDIR"] = str((ROOT / ".data_objects_9_1_9_3_tmp").resolve())
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)


def compile_and_run(source, compiler, std, workdir):
    source_path = workdir / "source.f90"
    source_path.write_text(source)
    exe = workdir / "program"
    comp = run_command([compiler, std_flag(compiler, std), "source.f90", "-o", "program"], workdir)
    if comp.returncode != 0:
        return {"phase": "compile", "returncode": comp.returncode, "stdout": comp.stdout, "stderr": comp.stderr}
    run = run_command([str(exe)], workdir)
    return {"phase": "run", "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
            "compile_stdout": comp.stdout, "compile_stderr": comp.stderr}


def mutation_matrix(compiler, std="f2023", root=ROOT, keep=False):
    root = Path(root)
    _, specs = build_corpus(root)
    scratch = root / ".data_objects_9_1_9_3_mutation_work"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir()
    results = []
    try:
        for cid, spec in specs.items():
            if spec["kind"] != "valid":
                continue
            pdir = scratch / cid / "parent"
            pdir.mkdir(parents=True)
            parent = compile_and_run(spec["source"], compiler, std, pdir)
            parent_ok = (parent["phase"] == "run" and parent["returncode"] == 0
                         and parent["stdout"] == spec["completion"] and parent["stderr"] == "")
            results.append({"case": cid, "mutation": "parent", "ok": parent_ok, **parent})
            if not parent_ok:
                continue
            for mutation in spec["mutations"]:
                mdir = scratch / cid / mutation["id"]
                mdir.mkdir(parents=True)
                observed = compile_and_run(mutate_source(spec, mutation), compiler, std, mdir)
                failed = (observed["phase"] == "run" and not (
                    observed["returncode"] == 0 and observed["stdout"] == spec["completion"] and observed["stderr"] == ""))
                results.append({"case": cid, "mutation": mutation["id"], "facet": mutation["facet"],
                                "kind": mutation["kind"], "ok": failed, **observed})
    finally:
        if not keep:
            shutil.rmtree(scratch, ignore_errors=True)
            shutil.rmtree(root / ".data_objects_9_1_9_3_tmp", ignore_errors=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        results = mutation_matrix(args.compiler, args.std, args.root, args.keep_work)
        failed = [row for row in results if not row["ok"]]
        if failed:
            for row in failed:
                print(json.dumps({k: row.get(k) for k in ("case", "mutation", "phase", "returncode", "stdout", "stderr")}, indent=2))
            raise SystemExit(f"mutation matrix failed: {len(failed)} bad rows out of {len(results)}")
        parents = sum(1 for row in results if row["mutation"] == "parent")
        mutants = sum(1 for row in results if row["mutation"] != "parent")
        print(f"mutation matrix OK: {parents} parents passed; {mutants} mutants failed")
        return
    _, specs = generate(args.root, args.check)
    facets = {facet for spec in specs.values() for facet in spec["facets"]}
    print(f"{'checked' if args.check else 'generated'} {len(specs)} {TOPIC} fixtures, {len(facets)} facets")

if __name__ == "__main__":
    main()
