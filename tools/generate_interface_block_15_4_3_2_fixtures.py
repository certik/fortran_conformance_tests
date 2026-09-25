#!/usr/bin/env python3
"""Runtime and diagnostic fixtures for Fortran 2023 interface blocks, 15.4.3.1-15.4.3.2."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "interface_block_15_4_3_2"
CATALOGUES = {
    "15.4.3.1": "doc/catalogues/interface_specification_general_15_4_3_1.json",
    "15.4.3.2": "doc/catalogues/interface_block_15_4_3_2.json",
}
VIEWS = {
    "15.4.3.1": "doc/fortran_2023_15_4_3_1.md",
    "15.4.3.2": "doc/fortran_2023_15_4_3_2.md",
}
SUMMARY_BEGIN = "<!-- BEGIN INTERFACE BLOCK 15.4.3.1-15.4.3.2 FIXTURES -->"
SUMMARY_END = "<!-- END INTERFACE BLOCK 15.4.3.1-15.4.3.2 FIXTURES -->"

EXCLUSIONS = (
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "segmentation fault",
    "stack trace", "please report unclear", "compiler traceback",
)

SELECTED = {
    "S15.4.3.1-001": [
        "function-statement-specifies-interface",
        "subroutine-statement-specifies-interface",
        "specification-statements-specify-dummy-and-result-interface",
        "interface-statements-in-interface-body",
        "interface-statements-in-definition-and-interface-body",
    ],
    "R1501": ["interface-block-delimiters", "interface-specification-sequence"],
    "R1502": ["interface-body-specification", "procedure-stmt-specification"],
    "R1503": ["ordinary-interface-stmt", "abstract-interface-stmt"],
    "R1504": ["end-interface-keywords", "end-interface-generic-spec"],
    "R1505": ["function-interface-body", "subroutine-interface-body"],
    "R1506": ["procedure-stmt-form", "module-procedure-stmt-form", "procedure-list-required"],
    "R1507": ["specific-procedure-name"],
    "C1502": ["end-interface-generic-spec-matches-opening"],
    "S15.4.3.2-001": ["relational-operator-spelling-equivalence"],
    "C1504": ["procedure-stmt-requires-generic-interface"],
    "S15.4.3.2-002": ["procedure-stmt-admitted-in-generic-interface"],
    "C1505": ["pure-interface-body-dummy-intents"],
    "C1506": [
        "interface-body-no-data-stmt",
        "interface-body-no-format-stmt",
        "interface-body-no-entry-stmt",
        "interface-body-no-stmt-function-stmt",
    ],
    "C1507": ["module-procedure-stmt-names-module-procedures"],
    "C1509": ["generic-interface-no-duplicate-accessible-specific"],
    "S15.4.3.2-004": ["abstract-interface-block-definition", "generic-interface-block-definition"],
    "S15.4.3.2-009": [
        "interface-body-specifies-external-attribute",
        "interface-body-specifies-explicit-specific-interface",
    ],
    "S15.4.3.2-014": ["pure-definition-interface-may-be-nonpure"],
}

RUNTIME_RULES = {
    "S15.4.3.1-001", "S15.4.3.2-001", "S15.4.3.2-002", "S15.4.3.2-004",
    "S15.4.3.2-009", "S15.4.3.2-014",
}

ORACLE_PREFIXES = {rule: f"{rule} interface-block fixture packet: " for rule in SELECTED}
LIMIT_PREFIXES = {rule: f"{rule} interface-block fixture boundaries: " for rule in SELECTED}

ORACLES = {
    "S15.4.3.1-001": ORACLE_PREFIXES["S15.4.3.1-001"] + (
        "one external-interface runtime fixture contains a specific interface block with a function body, "
        "a subroutine body, and an assumed-shape function body whose specification statements give the "
        "dummy and result interface. Matching external definitions are present. Three distinct runtime "
        "assertions check exact integer results 42, 24, and 42; conforming feature mutations retarget the "
        "corresponding interface body and call to same-characteristic alternate procedures that return 41, "
        "23, and 41. The entry-statement and procedure-definition-only facets remain pending."
    ),
    "R1501": ORACLE_PREFIXES["R1501"] + (
        "two compile/diagnose negatives exercise the numbered syntax: one removes the END INTERFACE "
        "delimiter from an otherwise running generic-control module, and one places an INTEGER declaration "
        "where R1501/R1502 permit only interface specifications. Each has a one-property run control."
    ),
    "R1502": ORACLE_PREFIXES["R1502"] + (
        "two compile/diagnose negatives distinguish the two admitted interface-specification alternatives: "
        "a declaration replacing an interface body, and malformed MODULE :: syntax replacing a procedure-stmt. "
        "Each rejected source differs from its running control only in that selected interface specification."
    ),
    "R1503": ORACLE_PREFIXES["R1503"] + (
        "ordinary INTERFACE and ABSTRACT INTERFACE syntax are covered by one-property compile/diagnose "
        "mutations of running controls: INTERFACE g is changed to INTERFACE, g, and ABSTRACT INTERFACE to "
        "INTERFACE ABSTRACT."
    ),
    "R1504": ORACLE_PREFIXES["R1504"] + (
        "END INTERFACE syntax is covered by one-property compile/diagnose mutations of generic controls: "
        "END MODULE replaces the required end-interface statement, and END INTERFACE (g) supplies a malformed "
        "generic-spec."
    ),
    "R1505": ORACLE_PREFIXES["R1505"] + (
        "function and subroutine interface-body syntax are covered by malformed end-statement negatives "
        "paired with controls that run through the corresponding interface body."
    ),
    "R1506": ORACLE_PREFIXES["R1506"] + (
        "procedure-stmt forms are covered by one-property compile/diagnose mutations of running generic "
        "module controls: PROCEDURE is misspelled, MODULE PROCEDURE is reordered as MODULE :: PROCEDURE, "
        "and the specific-procedure list is deleted."
    ),
    "R1507": ORACLE_PREFIXES["R1507"] + (
        "the specific-procedure name syntax is covered by replacing the one valid listed module procedure "
        "name in a running generic control by the token 123 and requiring a line-anchored syntax diagnostic."
    ),
    "C1502": ORACLE_PREFIXES["C1502"] + (
        "a generic interface opening as g and closing as h is rejected on the END INTERFACE line, with a "
        "one-token repair h->g producing a running control. Operator spelling equivalence is covered separately."
    ),
    "S15.4.3.2-001": ORACLE_PREFIXES["S15.4.3.2-001"] + (
        "a defined operator interface opens as OPERATOR(.LT.) and closes as OPERATOR(<); the run checks "
        "a true comparison of two derived-type values. The feature mutation keeps the delimiter spellings "
        "but retargets the module procedure to a same-characteristic false implementation."
    ),
    "C1504": ORACLE_PREFIXES["C1504"] + (
        "a MODULE PROCEDURE statement inside an interface block with no generic-spec is rejected; adding "
        "only generic name g to the INTERFACE line yields the paired running control."
    ),
    "S15.4.3.2-002": ORACLE_PREFIXES["S15.4.3.2-002"] + (
        "a generic interface block contains MODULE PROCEDURE choose_int, choose_log. Calls through the "
        "generic choose dispatch to integer and logical specifics with exact results 37 and .false.; "
        "feature mutations retarget one listed specific at a time to same-characteristic wrong-result module procedures."
    ),
    "C1505": ORACLE_PREFIXES["C1505"] + (
        "a pure interface body omitting INTENT for an ordinary integer dummy is rejected; adding only "
        "INTENT(IN) to that declaration yields a running control that does not call the nonexistent external."
    ),
    "C1506": ORACLE_PREFIXES["C1506"] + (
        "four one-property compile/diagnose negatives place DATA, FORMAT, ENTRY, or a statement-function "
        "statement inside an otherwise valid interface body. Removing exactly that statement yields a running control."
    ),
    "C1507": ORACLE_PREFIXES["C1507"] + (
        "MODULE PROCEDURE s in a generic module interface is rejected when no module procedure s is defined "
        "in the module; the control changes only the denotation by defining contained module function s and "
        "runs through generic g(-5)==37."
    ),
    "C1509": ORACLE_PREFIXES["C1509"] + (
        "two accessible INTERFACE g blocks repeating module procedure s are rejected; the control changes "
        "only the repeated specific in the second block from s to distinct t and runs g(-5)==37 and g(.true.)==.false."
    ),
    "S15.4.3.2-004": ORACLE_PREFIXES["S15.4.3.2-004"] + (
        "the generic-block facet is bound to the generic dispatch fixture described for S15.4.3.2-002. "
        "The abstract-block facet is bound to an ABSTRACT INTERFACE used as a procedure-pointer interface; "
        "a call through the pointer sets 33, and a feature mutation assigns a same-interface target setting 32. "
        "The specific-interface-block definitional facet remains pending until a distinct dependent rule is exercised."
    ),
    "S15.4.3.2-009": ORACLE_PREFIXES["S15.4.3.2-009"] + (
        "the external-interface runtime fixture has no EXTERNAL statement but calls three external procedures "
        "through a specific interface block, including an assumed-shape dummy that requires the explicit specific "
        "interface. Distinct assertions and same-characteristic alternate-procedure mutations cover the EXTERNAL "
        "attribute and explicit-specific-interface facets."
    ),
    "S15.4.3.2-014": ORACLE_PREFIXES["S15.4.3.2-014"] + (
        "a pure external function pure_inc is defined, while the specific interface body omits PURE. The call "
        "pure_inc(9) must return 10; the feature mutation retargets the interface body and call to a same-characteristic "
        "pure function returning 9. SIMPLE is left pending because the frozen toolchain lacks portable support evidence."
    ),
}

LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "only the listed facets are discharged by this generator-owned packet. Unselected pending facets, "
        "coarray cases, unnumbered shall-not restrictions without required diagnostics, full generic resolution "
        "rules owned by later 15.4.3 subclauses, and argument-association details owned by 15.5 remain pending. "
        "Diagnostic fixtures require line anchoring and exclude unsupported-feature, ICE, verifier, ASR, traceback, "
        "and unclear internal reports."
    ) for rule in SELECTED
}

COMPLETIONS = {
    "external_specific": "INTERFACE BLOCK EXTERNAL SPECIFIC OK\n",
    "generic_resolution": "INTERFACE BLOCK GENERIC RESOLUTION OK\n",
    "abstract_pointer": "INTERFACE BLOCK ABSTRACT POINTER OK\n",
    "operator_equivalence": "INTERFACE BLOCK OPERATOR EQUIVALENCE OK\n",
    "pure_latitude": "INTERFACE BLOCK PURE LATITUDE OK\n",
    "procedure_admission": "INTERFACE BLOCK PROCEDURE ADMISSION OK\n",
    "external_attribute": "INTERFACE BLOCK EXTERNAL ATTRIBUTE OK\n",
    "explicit_specific": "INTERFACE BLOCK EXPLICIT SPECIFIC OK\n",
    "control_generic": "INTERFACE BLOCK GENERIC CONTROL OK\n",
    "control_body": "INTERFACE BLOCK BODY CONTROL OK\n",
    "control_subroutine_body": "INTERFACE BLOCK SUBROUTINE BODY CONTROL OK\n",
    "control_abstract": "INTERFACE BLOCK ABSTRACT CONTROL OK\n",
    "control_pure": "INTERFACE BLOCK PURE CONTROL OK\n",
    "control_c1506_data": "INTERFACE BLOCK C1506 DATA CONTROL OK\n",
    "control_c1506_format": "INTERFACE BLOCK C1506 FORMAT CONTROL OK\n",
    "control_c1506_entry": "INTERFACE BLOCK C1506 ENTRY CONTROL OK\n",
    "control_c1506_stmtfunc": "INTERFACE BLOCK C1506 STMTFUNC CONTROL OK\n",
    "control_c1507": "INTERFACE BLOCK C1507 CONTROL OK\n",
    "control_c1509": "INTERFACE BLOCK C1509 CONTROL OK\n",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ident(variant):
    return f"interface_block_15_4_3_2_{variant}"


def _replace_all(text, replacements):
    for expected, replacement in replacements:
        if text.count(expected) != 1:
            raise ValueError(f"mutation token count changed for {expected!r}: {text.count(expected)}")
        text = text.replace(expected, replacement)
    return text


def valid_spec(variant, rule, facets, source, *, evidence="effect", mutations=None):
    raw = source.encode("ascii")
    return dict(
        id=ident(variant), variant=variant, kind="valid", evidence=evidence,
        rule=rule, facets=list(facets), phase="run", source=source, source_sha256=sha(raw),
        completion=COMPLETIONS[variant], feature_mutations=mutations or [],
        oracle_mutations=[dict(id="completion-text", replacements=[[COMPLETIONS[variant].rstrip("\n"), "INTERFACE BLOCK BAD"]], conforming=True)] if mutations else [],
        line_derivation="Runtime checks derive from Fortran 2023 15.4.3.1-15.4.3.2 interface-block text.")


def invalid_spec(variant, rule, facets, source, *, line, control_id, control_sha):
    raw = source.encode("ascii")
    return dict(
        id=ident(variant), variant=variant, kind="invalid", evidence="effect",
        rule=rule, facets=list(facets), phase="compile", source=source, source_sha256=sha(raw),
        diagnostic=dict(file="source.f90", line=line, end_line=line,
                        excludes_any=list(EXCLUSIONS)),
        repair=dict(control_id=control_id, control_sha256=control_sha, line=line),
        line_derivation="Rejected source is a one-property mutation of its running control.")


def external_specific_source():
    return """program interface_block_external_specific
  implicit none
  integer :: f_value, sub_value, sum_value
  ! rule: S15.4.3.1-001 S15.4.3.2-009
  ! covers: function/subroutine/specification statements in a specific interface body for externals
  interface
    integer function ib_func()
    end function ib_func
    subroutine ib_sub(x)
      integer, intent(out) :: x
    end subroutine ib_sub
    integer function ib_sum(values)
      integer, intent(in) :: values(:)
    end function ib_sum
    integer function ib_body()
    end function ib_body
    integer function ib_both()
    end function ib_both
  end interface
  f_value = -100
  f_value = ib_func()
  if (f_value /= 42) error stop 1
  sub_value = -101
  call ib_sub(sub_value)
  if (sub_value /= 24) error stop 2
  sum_value = -102
  sum_value = ib_sum([5, 37])
  if (sum_value /= 42) error stop 3
  f_value = -103
  f_value = ib_body()
  if (f_value /= 52) error stop 4
  f_value = -104
  f_value = ib_both()
  if (f_value /= 62) error stop 5
  print '(a)', 'INTERFACE BLOCK EXTERNAL SPECIFIC OK'
end program interface_block_external_specific

integer function ib_func()
  implicit none
  ib_func = 42
end function ib_func

integer function ib_func_alt()
  implicit none
  ib_func_alt = 41
end function ib_func_alt

subroutine ib_sub(x)
  implicit none
  integer, intent(out) :: x
  x = 24
end subroutine ib_sub

subroutine ib_sub_alt(x)
  implicit none
  integer, intent(out) :: x
  x = 23
end subroutine ib_sub_alt

integer function ib_sum(values)
  implicit none
  integer, intent(in) :: values(:)
  ib_sum = sum(values)
end function ib_sum

integer function ib_sum_alt(values)
  implicit none
  integer, intent(in) :: values(:)
  ib_sum_alt = sum(values) - 1
end function ib_sum_alt

integer function ib_body()
  implicit none
  ib_body = 52
end function ib_body

integer function ib_body_alt()
  implicit none
  ib_body_alt = 51
end function ib_body_alt

integer function ib_both()
  implicit none
  ib_both = 62
end function ib_both

integer function ib_both_alt()
  implicit none
  ib_both_alt = 61
end function ib_both_alt
"""


def generic_resolution_source():
    return """module interface_block_generic_resolution_m
  implicit none
  ! rule: S15.4.3.2-002 S15.4.3.2-004
  ! covers: generic interface block with MODULE PROCEDURE specifics
  interface choose
    module procedure choose_int, choose_log
  end interface choose
contains
  integer function choose_int(i)
    integer, intent(in) :: i
    choose_int = 42 + i
  end function choose_int
  logical function choose_log(flag)
    logical, intent(in) :: flag
    choose_log = .not. flag
  end function choose_log
  integer function wrong_int(i)
    integer, intent(in) :: i
    wrong_int = 41 + i
  end function wrong_int
  logical function wrong_log(flag)
    logical, intent(in) :: flag
    wrong_log = flag
  end function wrong_log
end module interface_block_generic_resolution_m

program interface_block_generic_resolution
  use interface_block_generic_resolution_m
  implicit none
  integer :: ivalue
  logical :: lvalue
  ivalue = -100
  ivalue = choose(-5)
  if (ivalue /= 37) error stop 1
  lvalue = .true.
  lvalue = choose(.true.)
  if (lvalue .neqv. .false.) error stop 2
  print '(a)', 'INTERFACE BLOCK GENERIC RESOLUTION OK'
end program interface_block_generic_resolution
"""


def abstract_pointer_source():
    return """program interface_block_abstract_pointer
  implicit none
  ! rule: S15.4.3.2-004
  ! covers: ABSTRACT INTERFACE used as a procedure pointer interface
  abstract interface
    subroutine action(x)
      integer, intent(out) :: x
    end subroutine action
  end interface
  procedure(action), pointer :: pp
  integer :: observed
  observed = -77
  pp => set_good
  call pp(observed)
  if (observed /= 33) error stop 1
  print '(a)', 'INTERFACE BLOCK ABSTRACT POINTER OK'
contains
  subroutine set_good(x)
    integer, intent(out) :: x
    x = 33
  end subroutine set_good
  subroutine set_bad(x)
    integer, intent(out) :: x
    x = 32
  end subroutine set_bad
end program interface_block_abstract_pointer
"""


def procedure_admission_source():
    return """module interface_block_procedure_admission_m
  implicit none
  ! rule: S15.4.3.2-002
  ! covers: procedure-stmt admitted in a generic interface block
  interface apply
    module procedure set_good
  end interface apply
contains
  subroutine set_good(x)
    integer, intent(out) :: x
    x = 23
  end subroutine set_good
  subroutine set_bad(x)
    integer, intent(out) :: x
    x = 22
  end subroutine set_bad
end module interface_block_procedure_admission_m

program interface_block_procedure_admission
  use interface_block_procedure_admission_m
  implicit none
  integer :: observed
  observed = -7
  call apply(observed)
  if (observed /= 23) error stop 1
  print '(a)', 'INTERFACE BLOCK PROCEDURE ADMISSION OK'
end program interface_block_procedure_admission
"""


def external_attribute_source():
    return """program interface_block_external_attribute
  implicit none
  ! rule: S15.4.3.2-009
  ! covers: interface body supplies the EXTERNAL attribute without an EXTERNAL statement
  interface
    subroutine ext_marker(x)
      integer, intent(out) :: x
    end subroutine ext_marker
  end interface
  integer :: observed
  observed = -3
  call ext_marker(observed)
  if (observed /= 17) error stop 1
  print '(a)', 'INTERFACE BLOCK EXTERNAL ATTRIBUTE OK'
end program interface_block_external_attribute

subroutine ext_marker(x)
  implicit none
  integer, intent(out) :: x
  x = 17
end subroutine ext_marker

subroutine ext_marker_bad(x)
  implicit none
  integer, intent(out) :: x
  x = 16
end subroutine ext_marker_bad
"""


def explicit_specific_source():
    return """program interface_block_explicit_specific
  implicit none
  ! rule: S15.4.3.2-009
  ! covers: interface body supplies an explicit specific interface with an assumed-shape dummy
  interface
    integer function ext_vector_sum(values)
      integer, intent(in) :: values(:)
    end function ext_vector_sum
  end interface
  integer :: observed
  observed = -4
  observed = ext_vector_sum([11, 31])
  if (observed /= 42) error stop 1
  print '(a)', 'INTERFACE BLOCK EXPLICIT SPECIFIC OK'
end program interface_block_explicit_specific

integer function ext_vector_sum(values)
  implicit none
  integer, intent(in) :: values(:)
  ext_vector_sum = sum(values)
end function ext_vector_sum

integer function ext_vector_sum_bad(values)
  implicit none
  integer, intent(in) :: values(:)
  ext_vector_sum_bad = sum(values) - 1
end function ext_vector_sum_bad
"""


def operator_equivalence_source():
    return """module interface_block_operator_equivalence_m
  implicit none
  ! rule: S15.4.3.2-001
  ! covers: OPERATOR(.LT.) opening matched by OPERATOR(<) ending
  type :: box
    integer :: value
  end type box
  interface operator(.lt.)
    module procedure less_box
  end interface operator(<)
contains
  logical function less_box(left, right)
    type(box), intent(in) :: left, right
    less_box = left%value < right%value
  end function less_box
  logical function false_less_box(left, right)
    type(box), intent(in) :: left, right
    false_less_box = .false.
  end function false_less_box
end module interface_block_operator_equivalence_m

program interface_block_operator_equivalence
  use interface_block_operator_equivalence_m
  implicit none
  type(box) :: low, high
  low%value = 1
  high%value = 2
  if (.not. (low < high)) error stop 1
  print '(a)', 'INTERFACE BLOCK OPERATOR EQUIVALENCE OK'
end program interface_block_operator_equivalence
"""


def pure_latitude_source():
    return """program interface_block_pure_latitude
  implicit none
  integer :: observed
  ! rule: S15.4.3.2-014
  ! covers: interface omits PURE for a pure external function definition
  interface
    integer function pure_inc(i)
      integer, intent(in) :: i
    end function pure_inc
  end interface
  observed = -90
  observed = pure_inc(9)
  if (observed /= 10) error stop 1
  print '(a)', 'INTERFACE BLOCK PURE LATITUDE OK'
end program interface_block_pure_latitude

pure integer function pure_inc(i)
  implicit none
  integer, intent(in) :: i
  pure_inc = i + 1
end function pure_inc

pure integer function pure_inc_bad(i)
  implicit none
  integer, intent(in) :: i
  pure_inc_bad = i
end function pure_inc_bad
"""


def control_generic_source(completion="INTERFACE BLOCK GENERIC CONTROL OK", *, name="interface_block_generic_control"):
    return f"""module {name}_m
  implicit none
  interface g
    module procedure s
  end interface g
contains
  integer function s(i)
    integer, intent(in) :: i
    s = 42 + i
  end function s
end module {name}_m
program {name}
  use {name}_m
  implicit none
  integer :: observed
  observed = -99
  observed = g(-5)
  if (observed /= 37) error stop 1
  print '(a)', '{completion}'
end program {name}
"""


def control_body_source(completion="INTERFACE BLOCK BODY CONTROL OK", *, name="interface_block_body_control"):
    return f"""program {name}
  implicit none
  integer :: observed
  interface
    integer function ext_body(i)
      integer, intent(in) :: i
    end function ext_body
  end interface
  observed = -99
  observed = ext_body(36)
  if (observed /= 37) error stop 1
  print '(a)', '{completion}'
end program {name}
integer function ext_body(i)
  implicit none
  integer, intent(in) :: i
  ext_body = i + 1
end function ext_body
"""


def control_subroutine_body_source():
    return """program interface_block_subroutine_body_control
  implicit none
  interface
    subroutine ext_sub_body()
    end subroutine ext_sub_body
  end interface
  print '(a)', 'INTERFACE BLOCK SUBROUTINE BODY CONTROL OK'
end program interface_block_subroutine_body_control
subroutine ext_sub_body()
  implicit none
end subroutine ext_sub_body
"""


def control_abstract_source():
    return """program interface_block_abstract_control
  implicit none
  abstract interface
    subroutine proc()
    end subroutine proc
  end interface
  print '(a)', 'INTERFACE BLOCK ABSTRACT CONTROL OK'
end program interface_block_abstract_control
"""


def control_pure_source():
    return """program interface_block_pure_control
  implicit none
  interface
    pure subroutine p(x)
      integer, intent(in) :: x
    end subroutine p
  end interface
  print '(a)', 'INTERFACE BLOCK PURE CONTROL OK'
end program interface_block_pure_control
"""


def c1506_control_source(variant, extra=""):
    completion = COMPLETIONS["control_c1506_" + variant].rstrip("\n")
    return f"""program interface_block_c1506_{variant}_control
  implicit none
  interface
    subroutine s()
{extra}    end subroutine s
  end interface
  print '(a)', '{completion}'
end program interface_block_c1506_{variant}_control
"""


def c1507_control_source():
    return control_generic_source(COMPLETIONS["control_c1507"].rstrip("\n"), name="interface_block_c1507_control")


def c1509_control_source():
    return """module interface_block_c1509_control_m
  implicit none
  interface g
    module procedure s
  end interface
  interface g
    module procedure t
  end interface
contains
  integer function s(i)
    integer, intent(in) :: i
    s = 42 + i
  end function s
  logical function t(flag)
    logical, intent(in) :: flag
    t = .not. flag
  end function t
end module interface_block_c1509_control_m
program interface_block_c1509_control
  use interface_block_c1509_control_m
  implicit none
  if (g(-5) /= 37) error stop 1
  if (g(.true.) .neqv. .false.) error stop 2
  print '(a)', 'INTERFACE BLOCK C1509 CONTROL OK'
end program interface_block_c1509_control
"""


def source_specs():
    specs = {}
    def add(spec):
        specs[spec["id"]] = spec

    add(valid_spec("external_specific", "S15.4.3.1-001", SELECTED["S15.4.3.1-001"], external_specific_source(), mutations=[
        dict(id="function-interface-name", facet="function-statement-specifies-interface", replacements=[
            ["integer function ib_func()\n    end function ib_func", "integer function ib_func_alt()\n    end function ib_func_alt"],
            ["f_value = ib_func()", "f_value = ib_func_alt()"],
        ], conforming=True),
        dict(id="subroutine-interface-name", facet="subroutine-statement-specifies-interface", replacements=[
            ["subroutine ib_sub(x)\n      integer, intent(out) :: x\n    end subroutine ib_sub", "subroutine ib_sub_alt(x)\n      integer, intent(out) :: x\n    end subroutine ib_sub_alt"],
            ["call ib_sub(sub_value)", "call ib_sub_alt(sub_value)"],
        ], conforming=True),
        dict(id="assumed-shape-interface-name", facet="specification-statements-specify-dummy-and-result-interface", replacements=[
            ["integer function ib_sum(values)\n      integer, intent(in) :: values(:)\n    end function ib_sum", "integer function ib_sum_alt(values)\n      integer, intent(in) :: values(:)\n    end function ib_sum_alt"],
            ["sum_value = ib_sum([5, 37])", "sum_value = ib_sum_alt([5, 37])"],
        ], conforming=True),
        dict(id="interface-body-function-name", facet="interface-statements-in-interface-body", replacements=[
            ["integer function ib_body()\n    end function ib_body", "integer function ib_body_alt()\n    end function ib_body_alt"],
            ["f_value = ib_body()", "f_value = ib_body_alt()"],
        ], conforming=True),
        dict(id="definition-and-body-function-name", facet="interface-statements-in-definition-and-interface-body", replacements=[
            ["integer function ib_both()\n    end function ib_both", "integer function ib_both_alt()\n    end function ib_both_alt"],
            ["f_value = ib_both()", "f_value = ib_both_alt()"],
        ], conforming=True),
    ]))
    add(valid_spec("procedure_admission", "S15.4.3.2-002", ["procedure-stmt-admitted-in-generic-interface"], procedure_admission_source(), mutations=[
        dict(id="admitted-procedure-specific", facet="procedure-stmt-admitted-in-generic-interface", replacements=[
            ["module procedure set_good", "module procedure set_bad"],
        ], conforming=True),
    ]))
    add(valid_spec("generic_resolution", "S15.4.3.2-004", ["generic-interface-block-definition"], generic_resolution_source(), mutations=[
        dict(id="generic-int-specific", facet="generic-interface-block-definition", replacements=[
            ["module procedure choose_int, choose_log", "module procedure wrong_int, choose_log"],
        ], conforming=True),
    ]))
    add(valid_spec("abstract_pointer", "S15.4.3.2-004", ["abstract-interface-block-definition"], abstract_pointer_source(), mutations=[
        dict(id="abstract-pointer-target", facet="abstract-interface-block-definition", replacements=[
            ["pp => set_good", "pp => set_bad"],
        ], conforming=True),
    ]))
    add(valid_spec("operator_equivalence", "S15.4.3.2-001", ["relational-operator-spelling-equivalence"], operator_equivalence_source(), mutations=[
        dict(id="operator-specific-target", facet="relational-operator-spelling-equivalence", replacements=[
            ["module procedure less_box", "module procedure false_less_box"],
        ], conforming=True),
    ]))
    add(valid_spec("pure_latitude", "S15.4.3.2-014", ["pure-definition-interface-may-be-nonpure"], pure_latitude_source(), mutations=[
        dict(id="pure-latitude-target", facet="pure-definition-interface-may-be-nonpure", replacements=[
            ["integer function pure_inc(i)\n      integer, intent(in) :: i\n    end function pure_inc", "integer function pure_inc_bad(i)\n      integer, intent(in) :: i\n    end function pure_inc_bad"],
            ["observed = pure_inc(9)", "observed = pure_inc_bad(9)"],
        ], conforming=True),
    ]))
    add(valid_spec("external_attribute", "S15.4.3.2-009", ["interface-body-specifies-external-attribute"], external_attribute_source(), mutations=[
        dict(id="external-attribute-name", facet="interface-body-specifies-external-attribute", replacements=[
            ["subroutine ext_marker(x)\n      integer, intent(out) :: x\n    end subroutine ext_marker", "subroutine ext_marker_bad(x)\n      integer, intent(out) :: x\n    end subroutine ext_marker_bad"],
            ["call ext_marker(observed)", "call ext_marker_bad(observed)"],
        ], conforming=True),
    ]))
    add(valid_spec("explicit_specific", "S15.4.3.2-009", ["interface-body-specifies-explicit-specific-interface"], explicit_specific_source(), mutations=[
        dict(id="explicit-specific-name", facet="interface-body-specifies-explicit-specific-interface", replacements=[
            ["integer function ext_vector_sum(values)\n      integer, intent(in) :: values(:)\n    end function ext_vector_sum", "integer function ext_vector_sum_bad(values)\n      integer, intent(in) :: values(:)\n    end function ext_vector_sum_bad"],
            ["observed = ext_vector_sum([11, 31])", "observed = ext_vector_sum_bad([11, 31])"],
        ], conforming=True),
    ]))

    controls = {
        "control_generic": valid_spec("control_generic", "R1501", ["interface-block-delimiters", "interface-specification-sequence"], control_generic_source(), evidence="positive-control"),
        "control_body": valid_spec("control_body", "R1502", ["interface-body-specification"], control_body_source(), evidence="positive-control"),
        "control_subroutine_body": valid_spec("control_subroutine_body", "R1505", ["subroutine-interface-body"], control_subroutine_body_source(), evidence="positive-control"),
        "control_abstract": valid_spec("control_abstract", "R1503", ["abstract-interface-stmt"], control_abstract_source(), evidence="positive-control"),
        "control_pure": valid_spec("control_pure", "C1505", ["pure-interface-body-dummy-intents"], control_pure_source(), evidence="positive-control"),
        "control_c1506_data": valid_spec("control_c1506_data", "C1506", ["interface-body-no-data-stmt"], c1506_control_source("data", "      integer :: x\n"), evidence="positive-control"),
        "control_c1506_format": valid_spec("control_c1506_format", "C1506", ["interface-body-no-format-stmt"], c1506_control_source("format"), evidence="positive-control"),
        "control_c1506_entry": valid_spec("control_c1506_entry", "C1506", ["interface-body-no-entry-stmt"], c1506_control_source("entry"), evidence="positive-control"),
        "control_c1506_stmtfunc": valid_spec("control_c1506_stmtfunc", "C1506", ["interface-body-no-stmt-function-stmt"], c1506_control_source("stmtfunc", "      integer :: f\n"), evidence="positive-control"),
        "control_c1507": valid_spec("control_c1507", "C1507", ["module-procedure-stmt-names-module-procedures"], c1507_control_source(), evidence="positive-control"),
        "control_c1509": valid_spec("control_c1509", "C1509", ["generic-interface-no-duplicate-accessible-specific"], c1509_control_source(), evidence="positive-control"),
    }
    for spec in controls.values():
        add(spec)

    cg = controls["control_generic"]
    cb = controls["control_body"]
    ca = controls["control_abstract"]
    cp = controls["control_pure"]
    add(invalid_spec("r1501_missing_end", "R1501", ["interface-block-delimiters"], cg["source"].replace("  end interface g\n", "", 1), line=5, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1501_bad_sequence", "R1501", ["interface-specification-sequence"], cg["source"].replace("    module procedure s", "    integer :: not_an_interface_spec", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1502_bad_body", "R1502", ["interface-body-specification"], cb["source"].replace("    integer function ext_body(i)\n      integer, intent(in) :: i\n    end function ext_body", "    integer :: x", 1), line=5, control_id=cb["id"], control_sha=cb["source_sha256"]))
    add(invalid_spec("r1502_bad_procedure_stmt", "R1502", ["procedure-stmt-specification"], cg["source"].replace("    module procedure s", "    module :: s", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1503_bad_ordinary", "R1503", ["ordinary-interface-stmt"], cg["source"].replace("  interface g", "  interface, g", 1), line=3, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1503_bad_abstract", "R1503", ["abstract-interface-stmt"], ca["source"].replace("  abstract interface", "  abstract interface proc", 1), line=3, control_id=ca["id"], control_sha=ca["source_sha256"]))
    add(invalid_spec("r1504_end_keywords", "R1504", ["end-interface-keywords"], cg["source"].replace("  end interface g", "  end module", 1), line=5, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1504_bad_generic", "R1504", ["end-interface-generic-spec"], cg["source"].replace("  end interface g", "  end interface (g)", 1), line=5, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1505_function_end", "R1505", ["function-interface-body"], cb["source"].replace("    end function ext_body", "    end subroutine ext_body", 1), line=7, control_id=cb["id"], control_sha=cb["source_sha256"]))
    add(invalid_spec("r1505_subroutine_end", "R1505", ["subroutine-interface-body"], controls["control_subroutine_body"]["source"].replace("    end subroutine ext_sub_body", "    end function ext_sub_body", 1), line=5, control_id=controls["control_subroutine_body"]["id"], control_sha=controls["control_subroutine_body"]["source_sha256"]))
    add(invalid_spec("r1506_misspelled", "R1506", ["procedure-stmt-form"], cg["source"].replace("    module procedure s", "    module procedures s", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1506_module_order", "R1506", ["module-procedure-stmt-form"], cg["source"].replace("    module procedure s", "    module :: procedure s", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1506_missing_list", "R1506", ["procedure-list-required"], cg["source"].replace("    module procedure s", "    module procedure", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("r1507_bad_name", "R1507", ["specific-procedure-name"], cg["source"].replace("    module procedure s", "    module procedure 123", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("c1502_mismatch", "C1502", ["end-interface-generic-spec-matches-opening"], cg["source"].replace("  end interface g", "  end interface h", 1), line=5, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("c1504_nongeneric", "C1504", ["procedure-stmt-requires-generic-interface"], cg["source"].replace("  interface g", "  interface", 1).replace("  end interface g", "  end interface", 1), line=4, control_id=cg["id"], control_sha=cg["source_sha256"]))
    add(invalid_spec("c1505_pure_no_intent", "C1505", ["pure-interface-body-dummy-intents"], cp["source"].replace("      integer, intent(in) :: x", "      integer :: x", 1), line=4, control_id=cp["id"], control_sha=cp["source_sha256"]))
    c1506_defs = [
        ("data", "interface-body-no-data-stmt", "      integer :: x\n      data x /1/\n", 6, ["DATA statement", "DATA", "INTERFACE"]),
        ("format", "interface-body-no-format-stmt", "10  format(i0)\n", 5, ["FORMAT statement", "FORMAT", "INTERFACE"]),
        ("entry", "interface-body-no-entry-stmt", "      entry e()\n", 5, ["ENTRY statement", "ENTRY", "INTERFACE"]),
        ("stmtfunc", "interface-body-no-stmt-function-stmt", "      integer :: f\n      f() = 1\n", 6, ["Statement function", "statement function", "INTERFACE"]),
    ]
    for variant, facet, extra, line, causes in c1506_defs:
        control = controls["control_c1506_" + variant]
        add(invalid_spec("c1506_" + variant, "C1506", [facet], c1506_control_source(variant, extra), line=line, control_id=control["id"], control_sha=control["source_sha256"]))
    add(invalid_spec("c1507_external", "C1507", ["module-procedure-stmt-names-module-procedures"], c1507_control_source().replace("contains\n  integer function s(i)\n    integer, intent(in) :: i\n    s = 42 + i\n  end function s\n", "", 1) + "\ninteger function s(i)\n  implicit none\n  integer, intent(in) :: i\n  s = 42 + i\nend function s\n", line=4, control_id=controls["control_c1507"]["id"], control_sha=controls["control_c1507"]["source_sha256"]))
    add(invalid_spec("c1509_duplicate", "C1509", ["generic-interface-no-duplicate-accessible-specific"], c1509_control_source().replace("  interface g\n    module procedure t\n  end interface", "  interface g\n    module procedure s\n  end interface", 1), line=7, control_id=controls["control_c1509"]["id"], control_sha=controls["control_c1509"]["source_sha256"]))
    return specs


def all_mutations(spec):
    return spec.get("feature_mutations", []) + spec.get("oracle_mutations", [])


def mutated_source(spec, mutation):
    return _replace_all(spec["source"], mutation["replacements"]).encode("ascii")


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        )
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                      stdout=[spec["completion"]], stderr=[""])
        else:
            manifest["expect"] = dict(phase="compile", step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
        rel = Path("tests/fixtures") / spec["id"]
        directory = Path(root) / rel
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        spec["path"] = (rel / "fixture.json").as_posix()
        spec["manifest"] = manifest
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        if rule not in by_rule:
            continue
        row = by_rule[rule]
        for facet in facets:
            if facet not in row["facets"]:
                raise ValueError(f"selected facet vanished: {rule} {facet}")
            row.setdefault("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin = f"<!-- BEGIN GENERATED {section} -->"
    end = f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated-region boundaries changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    selected = sum(len(f) for rule, f in SELECTED.items() if rule in {row["id"] for row in catalogue["requirements"]})
    summary = (
        SUMMARY_BEGIN + "\n"
        f"## Interface block fixture packet for {section}\n\n"
        f"This generator-owned packet discharges {selected} selected pending facets in this section with "
        "runtime interface-block programs and line-anchored diagnostic/control pairs. Runtime feature "
        "mutations are permanent generator data and are checked on both configured compilers. Diagnostic "
        "fixtures use one-property running controls and exclude unsupported-feature, ICE, verifier, ASR, "
        "traceback, and unclear internal reports. Argument-association observations are not claimed for "
        "15.5-owned facets, and definitional facets are only bound where a dependent rule is exercised.\n"
        + SUMMARY_END
    )
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("interface-block summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues = {section: json.loads((root / path).read_text()) for section, path in CATALOGUES.items()}
    updated = {section: synced_catalogue(cat) for section, cat in catalogues.items()}
    rendered = {section: render_view(section, updated[section], root) for section in updated}
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, cat in updated.items():
            if catalogues[section] != cat:
                stale.append(CATALOGUES[section])
            if (root / VIEWS[section]).read_text() != rendered[section]:
                stale.append(VIEWS[section])
        if stale:
            raise SystemExit("stale interface-block fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section, cat in updated.items():
                (root / CATALOGUES[section]).write_text(json.dumps(cat, indent=2) + "\n")
                (root / VIEWS[section]).write_text(rendered[section])
    return specs


def compile_and_run(work, source, compiler, std, expected_stdout):
    src = work / "source.f90"
    obj = work / "source.o"
    exe = work / "program"
    src.write_bytes(source)
    cmd = [str(compiler), f"--std={std}" if "lfortran" in Path(str(compiler)).name else f"-std={std}", "-c", str(src), "-J", str(work), "-o", str(obj)]
    build = subprocess.run(cmd, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if build.returncode != 0:
        return False, "compile", build.stdout + build.stderr
    link = subprocess.run([str(compiler), str(obj), "-o", str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if link.returncode != 0:
        return False, "link", link.stdout + link.stderr
    run = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if run.returncode == 0 and run.stdout == expected_stdout and run.stderr == "":
        return True, "run", run.stdout + run.stderr
    return False, "run", run.stdout + run.stderr


def check_mutations(root, compiler, std):
    root = Path(root)
    specs = source_specs()
    mutations = [(spec, mut) for spec in specs.values() if spec.get("feature_mutations") for mut in all_mutations(spec)]
    if not mutations:
        raise SystemExit("no interface-block mutations defined")
    workspace = root / ".interface_block_15_4_3_2_mutations"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    survived = []
    bad_compile = []
    try:
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
            case_dir.mkdir()
            ok, phase, output = compile_and_run(case_dir, mutated_source(spec, mutation), compiler, std, spec["completion"])
            if ok:
                survived.append((spec["id"], mutation["id"], output))
            elif phase != "run":
                bad_compile.append((spec["id"], mutation["id"], phase, output))
    finally:
        shutil.rmtree(workspace)
    if bad_compile:
        detail = "\n".join(f"{case} {mutation} {phase}: {output[:400]!r}" for case, mutation, phase, output in bad_compile)
        raise SystemExit("interface-block mutation failed before run:\n" + detail)
    if survived:
        detail = "\n".join(f"{case} {mutation}: {output!r}" for case, mutation, output in survived)
        raise SystemExit("interface-block mutation survived:\n" + detail)
    print(f"Checked {len(mutations)} interface-block mutations with {compiler}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--check-mutations", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.check_mutations))) > 1:
        parser.error("--check, --sync-catalogue and --check-mutations are separate operations")
    if args.check_mutations:
        if not args.compiler or not args.std:
            parser.error("--check-mutations requires --compiler and --std")
        check_mutations(args.root, args.compiler, args.std)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    selected = sum(len(v) for v in SELECTED.values())
    mutations = sum(len(all_mutations(row)) for row in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} interface-block fixtures, {selected} facets, {mutations} mutations.")


if __name__ == "__main__":
    main()
