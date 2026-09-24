#!/usr/bin/env python3
"""Clause 14.1 and 14.2.1 main-program/module fixtures."""

import argparse
import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
MAIN_CATALOGUE = "doc/catalogues/main_program_14_1.json"
MODULE_CATALOGUE = "doc/catalogues/module_syntax_and_semantics_14_2_1.json"
MAIN_VIEW = "doc/fortran_2023_14_1.md"
MODULE_VIEW = "doc/fortran_2023_14_2_1.md"
SECTION_MAIN = "14.1"
SECTION_MODULE = "14.2.1"
PREFIX = "modules_14_1_14_2_1_"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
)
MAIN_ORACLE_PREFIX = "Batch281 main-program fixture family: "
MAIN_LIMIT_PREFIX = "Batch281 main-program fixture boundaries: "
MODULE_ORACLE_PREFIX = "Batch281 module fixture family: "
MODULE_LIMIT_PREFIX = "Batch281 module fixture boundaries: "
MAIN_SUMMARY_BEGIN = "<!-- BEGIN MODULES 14.1/14.2.1 FIXTURES: MAIN -->"
MAIN_SUMMARY_END = "<!-- END MODULES 14.1/14.2.1 FIXTURES: MAIN -->"
MODULE_SUMMARY_BEGIN = "<!-- BEGIN MODULES 14.1/14.2.1 FIXTURES: MODULES -->"
MODULE_SUMMARY_END = "<!-- END MODULES 14.1/14.2.1 FIXTURES: MODULES -->"

MAIN_FACETS = {
    "R1402": ["program-stmt-missing-name-rejected"],
    "R1403": ["malformed-end-program-stmt-rejected"],
}

MODULE_FACETS = {
    "R1404": ["module-missing-end-rejected"],
    "R1405": ["module-stmt-missing-name-rejected"],
    "R1406": ["malformed-end-module-stmt-rejected"],
    "R1407": ["module-subprogram-without-contains-rejected"],
    "R1408": ["invalid-module-subprogram-form-rejected"],
    "C1402": ["end-module-name-mismatch-rejected"],
    "C1403": ["module-specification-no-stmt-function", "module-specification-no-entry", "module-specification-no-format"],
    "S14.2.1-005": ["module-implicit-interface-procedure-external", "module-implicit-interface-function-explicit-type"],
    "S14.2.1-006": ["module-intrinsic-procedure-intrinsic-attribute", "module-intrinsic-procedure-intrinsic-use"],
}

MAIN_ORACLE = MAIN_ORACLE_PREFIX + (
    "four f2023 fixtures cover two required R1402/R1403 syntax diagnostics with one-property controls. "
    "The corresponding conforming controls compile successfully; diagnostic expectations are line-bounded and "
    "exclude crashes/unimplemented messages."
)
MAIN_LIMITATION = MAIN_LIMIT_PREFIX + (
    "R1401 and C1401 remain with the pre-existing deferred coverage noted by the source catalogue. Optional "
    "END PROGRAM spelling facets, the PROGRAM-statement positive form, and main-program classification/exclusion "
    "facets are not discharged because they have no conforming load-bearing feature mutation beyond ordinary execution. "
    "Non-Fortran main-program latitude/restrictions and the unnumbered prohibition on referencing a Fortran main "
    "program require mixed-language/source-control evidence or have no required diagnostic obligation. The fixtures "
    "add no review approval, SourceUse renewal, baseline update, or universal compiler-conformance claim."
)
MODULE_ORACLE = MODULE_ORACLE_PREFIX + (
    "twenty-six f2023 fixtures cover module program-unit source form, named MODULE statements, contained module "
    "function and subroutine subprograms, CONTAINS with and without module subprograms, public module identifiers "
    "observed by a simple USE, nonintrinsic modules defined by module program units, module variables retaining "
    "state across module procedure calls, C1402 and C1403 diagnostics, R1404-R1408 diagnostics, and p3/p4 "
    "external/intrinsic procedure declarations. Runtime cases use exact integer or character length/value checks; "
    "diagnostic cases have one-property conforming controls and line-bounded exclusions for crashes/unimplemented "
    "messages."
)
MODULE_LIMITATION = MODULE_LIMIT_PREFIX + (
    "USE-statement spelling, ONLY/renaming, private-name rejection, shared-storage identity, module contents, "
    "public accessibility effects, nonintrinsic module definition, positive module/program-unit syntax forms, "
    "module procedure positive forms, intrinsic-module provision/classification, optional END MODULE spelling facets, "
    "and the R1408 separate module subprogram form are not discharged here: they either require other owners, "
    "processor/build-system support, submodule ownership, or lack conforming load-bearing feature mutations. The fixtures add no review "
    "approval, SourceUse renewal, baseline update, or universal compiler-conformance claim."
)


def src_main_without_program():
    return """implicit none
integer :: observed
observed = -777
if (observed /= -777) error stop
observed = 41
if (observed /= 41) error stop
print '(a)', 'MAIN WITHOUT PROGRAM OK'
end
"""


def src_program_named():
    return """program r1402_named_main
  implicit none
  integer :: observed
  observed = -777
  if (observed /= -777) error stop
  observed = 42
  if (observed /= 42) error stop
  print '(a)', 'PROGRAM NAMED OK'
end program r1402_named_main
"""


def src_program_missing_name_control():
    return """program r1402_missing_name_control
  implicit none
  integer :: observed
  observed = 42
end
"""


def src_program_missing_name_invalid():
    return src_program_missing_name_control().replace("program r1402_missing_name_control", "program", 1)


def src_end_program_extra_control():
    return """program r1403_named_end_control
  implicit none
  integer :: observed
  observed = -777
  if (observed /= -777) error stop
  observed = 43
  if (observed /= 43) error stop
  print '(a)', 'END PROGRAM CONTROL OK'
end program r1403_named_end_control
"""


def src_end_program_extra_invalid():
    return src_end_program_extra_control().replace(
        "end program r1403_named_end_control", "end program r1403_named_end_control extra")


def src_module_contents():
    return """module m1421_content
  implicit none
  private
  public :: content_type, content_value, bump_counter, module_counter
  integer, parameter :: declaration_value = 17
  integer :: module_counter
  type :: content_type
    integer :: marker
  end type content_type
contains
  function content_value() result(value)
    type(content_type) :: local
    integer :: value
    local%marker = declaration_value + 5
    value = local%marker + 20
  end function content_value
  subroutine bump_counter(value)
    integer, intent(out) :: value
    module_counter = module_counter + 1
    value = module_counter
  end subroutine bump_counter
end module m1421_content
program content_probe
  use m1421_content
  implicit none
  integer :: first, second
  if (content_value() /= 42) error stop
  module_counter = 6
  call bump_counter(first)
  call bump_counter(second)
  if (first /= 7) error stop
  if (second /= 8) error stop
  print '(a)', 'MODULE CONTENT OK'
end program content_probe
"""


def src_public_identifier():
    return """module m1421_public
  implicit none
  private
  public :: public_value, public_double
  integer, parameter :: public_value = 24
  integer, parameter :: hidden_offset = 18
contains
  function public_double() result(value)
    integer :: value
    value = public_value + hidden_offset
  end function public_double
end module m1421_public
program public_probe
  use m1421_public
  implicit none
  integer :: observed
  observed = -777
  observed = public_value
  if (observed /= 24) error stop
  if (public_double() /= 42) error stop
  print '(a)', 'PUBLIC MODULE IDENTIFIERS OK'
end program public_probe
"""


def src_nonintrinsic_module():
    return """module m1421_nonintrinsic
  implicit none
  integer, parameter :: answer = 42
contains
  integer function nonintrinsic_answer()
    nonintrinsic_answer = answer
  end function nonintrinsic_answer
end module m1421_nonintrinsic
program nonintrinsic_probe
  use m1421_nonintrinsic
  implicit none
  if (nonintrinsic_answer() /= 42) error stop
  print '(a)', 'NONINTRINSIC MODULE OK'
end program nonintrinsic_probe
"""


def src_module_form():
    return """module r1404_form_m
  implicit none
  integer, parameter :: base = 37
contains
  integer function answer()
    answer = base + 5
  end function answer
end module r1404_form_m
program r1404_form_probe
  use r1404_form_m
  implicit none
  if (answer() /= 42) error stop
  print '(a)', 'MODULE FORM OK'
end program r1404_form_probe
"""


def src_module_missing_end_control():
    return """module r1404_missing_end_m
  implicit none
  integer, parameter :: answer = 42
end module r1404_missing_end_m
"""


def src_module_missing_end_invalid():
    return src_module_missing_end_control().replace(
        "end module r1404_missing_end_m", "end program r1404_missing_end_m", 1)


def src_module_stmt_named():
    return """module r1405_named_m
  implicit none
  integer, parameter :: answer = 42
end module r1405_named_m
program r1405_named_probe
  use r1405_named_m
  implicit none
  if (answer /= 42) error stop
  print '(a)', 'MODULE STMT NAMED OK'
end program r1405_named_probe
"""


def src_module_stmt_missing_name_control():
    return """module r1405_missing_name_m
  implicit none
  integer, parameter :: answer = 42
end
"""


def src_module_stmt_missing_name_invalid():
    return src_module_stmt_missing_name_control().replace("module r1405_missing_name_m", "module", 1)


def src_end_module_extra_control():
    return """module r1406_named_end_m
  implicit none
  integer, parameter :: answer = 42
end module r1406_named_end_m
program r1406_named_end_probe
  use r1406_named_end_m
  implicit none
  if (answer /= 42) error stop
  print '(a)', 'END MODULE CONTROL OK'
end program r1406_named_end_probe
"""


def src_end_module_extra_invalid():
    return src_end_module_extra_control().replace(
        "end module r1406_named_end_m", "end module r1406_named_end_m extra", 1)


def src_contains_with_subprogram():
    return """module r1407_contains_m
  implicit none
contains
  integer function answer()
    answer = 42
  end function answer
end module r1407_contains_m
program r1407_contains_probe
  use r1407_contains_m
  implicit none
  if (answer() /= 42) error stop
  print '(a)', 'CONTAINS SUBPROGRAM OK'
end program r1407_contains_probe
"""


def src_contains_without_subprograms():
    return """module r1407_empty_contains_m
  implicit none
  integer, parameter :: answer = 42
contains
end module r1407_empty_contains_m
program r1407_empty_contains_probe
  use r1407_empty_contains_m
  implicit none
  if (answer /= 42) error stop
  print '(a)', 'EMPTY CONTAINS OK'
end program r1407_empty_contains_probe
"""


def src_module_subprogram_without_contains_control():
    return src_contains_with_subprogram()


def src_module_subprogram_without_contains_invalid():
    return src_contains_with_subprogram().replace("contains\n", "", 1)


def src_module_function_subprogram():
    return """module r1408_function_m
  implicit none
contains
  integer function answer()
    answer = 42
  end function answer
end module r1408_function_m
program r1408_function_probe
  use r1408_function_m
  implicit none
  if (answer() /= 42) error stop
  print '(a)', 'MODULE FUNCTION OK'
end program r1408_function_probe
"""


def src_module_subroutine_subprogram():
    return """module r1408_subroutine_m
  implicit none
contains
  subroutine set_answer(value)
    integer, intent(out) :: value
    value = 42
  end subroutine set_answer
end module r1408_subroutine_m
program r1408_subroutine_probe
  use r1408_subroutine_m
  implicit none
  integer :: observed
  observed = -777
  if (observed /= -777) error stop
  call set_answer(observed)
  if (observed /= 42) error stop
  print '(a)', 'MODULE SUBROUTINE OK'
end program r1408_subroutine_probe
"""


def src_invalid_module_subprogram_control():
    return """module r1408_invalid_form_m
  implicit none
contains
  subroutine invalid_inside_module
  end subroutine invalid_inside_module
end module r1408_invalid_form_m
"""


def src_invalid_module_subprogram_invalid():
    return src_invalid_module_subprogram_control().replace(
        "subroutine invalid_inside_module", "block data invalid_inside_module", 1).replace(
        "end subroutine invalid_inside_module", "end block data invalid_inside_module", 1)


def src_c1402_name_control():
    return """module c1402_name_m
  implicit none
  integer, parameter :: answer = 42
end module c1402_name_m
program c1402_name_probe
  use c1402_name_m
  implicit none
  if (answer /= 42) error stop
  print '(a)', 'C1402 CONTROL OK'
end program c1402_name_probe
"""


def src_c1402_name_mismatch_invalid():
    return src_c1402_name_control().replace("end module c1402_name_m", "end module c1402_other_m", 1)


def src_c1403_stmt_function_control():
    return """module c1403_stmt_function_m
  implicit none
  integer :: i, f
  integer, parameter :: answer = 42
end module c1403_stmt_function_m
"""


def src_c1403_stmt_function_invalid():
    return src_c1403_stmt_function_control().replace(
        "  integer :: i, f\n", "  integer :: i, f\n  f(i) = i + 1\n", 1)


def src_c1403_entry_control():
    return """module c1403_entry_m
  implicit none
  integer, parameter :: answer = 42
end module c1403_entry_m
"""


def src_c1403_entry_invalid():
    return src_c1403_entry_control().replace(
        "  implicit none\n", "  implicit none\n  entry alternate()\n", 1)


def src_c1403_format_control():
    return """module c1403_format_m
  implicit none
  integer, parameter :: answer = 42
end module c1403_format_m
"""


def src_c1403_format_invalid():
    return src_c1403_format_control().replace(
        "  implicit none\n", "  implicit none\n  100 format(I0)\n", 1)


def src_external_implicit_interface():
    return """module p3_external_m
  implicit none
  integer :: abs
  external :: abs
  character(len=5) :: ext_word
  external :: ext_word
contains
  integer function external_value()
    external_value = abs(-1)
  end function external_value
  integer function external_word_len()
    external_word_len = len(ext_word())
  end function external_word_len
  character(len=5) function external_word_value()
    external_word_value = ext_word()
  end function external_word_value
end module p3_external_m
program p3_external_probe
  use p3_external_m
  implicit none
  character(len=5) :: word
  if (external_value() /= 41) error stop
  if (external_word_len() /= 5) error stop
  word = external_word_value()
  if (len(word) /= 5) error stop
  if (word /= 'HELLO') error stop
  print '(a)', 'MODULE EXTERNAL PROCEDURE OK'
end program p3_external_probe
integer function abs(x)
  integer, intent(in) :: x
  abs = 42 + x
end function abs
character(len=5) function ext_word()
  ext_word = 'HELLO'
end function ext_word
"""


def src_intrinsic_attribute_module():
    return """module p4_intrinsic_attr_m
  implicit none
  intrinsic :: abs
contains
  integer function via_attribute()
    via_attribute = abs(-7)
  end function via_attribute
end module p4_intrinsic_attr_m
program p4_intrinsic_attr_probe
  use p4_intrinsic_attr_m
  implicit none
  if (via_attribute() /= 7) error stop
  print '(a)', 'MODULE INTRINSIC ATTRIBUTE OK'
end program p4_intrinsic_attr_probe
! external-abs-anchor
"""


def src_intrinsic_use_module():
    return """module p4_intrinsic_use_m
  implicit none
  ! intrinsic-use-anchor
contains
  integer function via_use()
    via_use = abs(-7)
  end function via_use
end module p4_intrinsic_use_m
program p4_intrinsic_use_probe
  use p4_intrinsic_use_m
  implicit none
  if (via_use() /= 7) error stop
  print '(a)', 'MODULE INTRINSIC USE OK'
end program p4_intrinsic_use_probe
! external-abs-anchor
"""


def valid_case(name, rule, facets, source, stdout=None, evidence="effect", compile_only=False, mutations=None):
    return dict(id=name, kind="valid", rule=rule, facets=facets, evidence=evidence, source=source,
                stdout=stdout, compile_only=compile_only, mutations=[list(item) for item in (mutations or [])])


def invalid_case(name, rule, facets, source, line, messages, control, end_line=None, lfortran_defect=False):
    return dict(id=name, kind="invalid", rule=rule, facets=facets, evidence="effect", source=source,
                line=line, end_line=end_line or line, messages=messages, control=control,
                lfortran_defect=lfortran_defect)


def case_specs():
    cases = []
    cases.append(valid_case("R1402_valid__program_statement_name_control", "R1402",
                            ["program-stmt-missing-name-rejected"], src_program_missing_name_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1402_invalid__program_statement_missing_name", "R1402",
                              ["program-stmt-missing-name-rejected"], src_program_missing_name_invalid(), 1,
                              ["Invalid form of PROGRAM statement", "program name", "Expected", "Syntax error", "Unexpected", "unexpected here"],
                              "R1402_valid__program_statement_name_control"))
    cases.append(valid_case("R1403_valid__end_program_extra_token_control", "R1403",
                            ["malformed-end-program-stmt-rejected"], src_end_program_extra_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1403_invalid__end_program_extra_token", "R1403",
                              ["malformed-end-program-stmt-rejected"], src_end_program_extra_invalid(), 9,
                              ["Unexpected", "Syntax error", "Expected end of statement", "Extra characters"],
                              "R1403_valid__end_program_extra_token_control"))
    cases.append(valid_case("R1404_valid__module_missing_end_control", "R1404",
                            ["module-missing-end-rejected"], src_module_missing_end_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1404_invalid__module_missing_end", "R1404",
                              ["module-missing-end-rejected"], src_module_missing_end_invalid(), 4,
                              ["END MODULE", "Unexpected end", "Unexpected", "Syntax error", "Expecting END MODULE"],
                              "R1404_valid__module_missing_end_control"))
    cases.append(valid_case("R1405_valid__module_statement_name_control", "R1405",
                            ["module-stmt-missing-name-rejected"], src_module_stmt_missing_name_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1405_invalid__module_statement_missing_name", "R1405",
                              ["module-stmt-missing-name-rejected"], src_module_stmt_missing_name_invalid(), 1,
                              ["Invalid character in name", "module name", "Expected", "Syntax error", "Unexpected", "unexpected here"],
                              "R1405_valid__module_statement_name_control"))
    cases.append(valid_case("R1406_valid__end_module_extra_token_control", "R1406",
                            ["malformed-end-module-stmt-rejected"], src_end_module_extra_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1406_invalid__end_module_extra_token", "R1406",
                              ["malformed-end-module-stmt-rejected"], src_end_module_extra_invalid(), 4,
                              ["Unexpected", "Syntax error", "Expected end of statement", "Extra characters"],
                              "R1406_valid__end_module_extra_token_control"))
    cases.append(valid_case("R1407_valid__module_subprogram_without_contains_control", "R1407",
                            ["module-subprogram-without-contains-rejected"], src_module_subprogram_without_contains_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1407_invalid__module_subprogram_without_contains", "R1407",
                              ["module-subprogram-without-contains-rejected"], src_module_subprogram_without_contains_invalid(), 3,
                              ["CONTAINS", "Unexpected", "Syntax error", "procedure"],
                              "R1407_valid__module_subprogram_without_contains_control", end_line=5))
    cases.append(valid_case("R1408_valid__invalid_module_subprogram_control", "R1408",
                            ["invalid-module-subprogram-form-rejected"], src_invalid_module_subprogram_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1408_invalid__block_data_as_module_subprogram", "R1408",
                              ["invalid-module-subprogram-form-rejected"], src_invalid_module_subprogram_invalid(), 4,
                              ["BLOCK DATA", "Unexpected", "Syntax error", "module subprogram"],
                              "R1408_valid__invalid_module_subprogram_control", end_line=5))
    cases.append(valid_case("C1402_valid__end_module_name_mismatch_control", "C1402",
                            ["end-module-name-mismatch-rejected"], src_c1402_name_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1402_invalid__end_module_name_mismatch", "C1402",
                              ["end-module-name-mismatch-rejected"], src_c1402_name_mismatch_invalid(), 1,
                              ["does not match", "Expected", "name", "END MODULE"],
                              "C1402_valid__end_module_name_mismatch_control", end_line=4))
    cases.append(valid_case("C1403_valid__stmt_function_control", "C1403",
                            ["module-specification-no-stmt-function"], src_c1403_stmt_function_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1403_invalid__stmt_function_in_module_spec", "C1403",
                              ["module-specification-no-stmt-function"], src_c1403_stmt_function_invalid(), 4,
                              ["statement function", "Unexpected", "Syntax error", "specification", "executable statement is not allowed"],
                              "C1403_valid__stmt_function_control"))
    cases.append(valid_case("C1403_valid__entry_control", "C1403",
                            ["module-specification-no-entry"], src_c1403_entry_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1403_invalid__entry_in_module_spec", "C1403",
                              ["module-specification-no-entry"], src_c1403_entry_invalid(), 3,
                              ["ENTRY", "Unexpected", "Syntax error", "specification", "executable statement is not allowed"],
                              "C1403_valid__entry_control"))
    cases.append(valid_case("C1403_valid__format_control", "C1403",
                            ["module-specification-no-format"], src_c1403_format_control(),
                            compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1403_invalid__format_in_module_spec", "C1403",
                              ["module-specification-no-format"], src_c1403_format_invalid(), 3,
                              ["FORMAT", "Unexpected", "Syntax error", "specification", "executable statement is not allowed"],
                              "C1403_valid__format_control"))
    cases.append(valid_case("S14_2_1_005_valid__external_implicit_interface_declarations", "S14.2.1-005",
                            ["module-implicit-interface-procedure-external", "module-implicit-interface-function-explicit-type"],
                            src_external_implicit_interface(), "MODULE EXTERNAL PROCEDURE OK\n", evidence="positive-control", mutations=[
                                ("EXTERNAL attribute selects external ABS", "external :: abs", "intrinsic :: abs"),
                                ("explicit character function length", "character(len=5) :: ext_word", "character(len=6) :: ext_word"),
                                ("external character function definition length", "character(len=5) function ext_word()", "character(len=6) function ext_word()"),
                            ]))
    cases.append(valid_case("S14_2_1_006_valid__intrinsic_attribute", "S14.2.1-006",
                            ["module-intrinsic-procedure-intrinsic-attribute"],
                            src_intrinsic_attribute_module(), "MODULE INTRINSIC ATTRIBUTE OK\n", evidence="positive-control", mutations=[
                                ("INTRINSIC attribute selects intrinsic ABS", "intrinsic :: abs", "integer :: abs\n  external :: abs"),
                                ("external ABS definition for attribute mutation", "! external-abs-anchor", "integer function abs(x)\n  integer, intent(in) :: x\n  abs = 42 + x\nend function abs"),
                            ]))
    cases.append(valid_case("S14_2_1_006_valid__intrinsic_use", "S14.2.1-006",
                            ["module-intrinsic-procedure-intrinsic-use"],
                            src_intrinsic_use_module(), "MODULE INTRINSIC USE OK\n", evidence="positive-control", mutations=[
                                ("direct intrinsic use without declaration", "! intrinsic-use-anchor", "integer :: abs\n  external :: abs"),
                                ("external ABS definition for intrinsic-use mutation", "! external-abs-anchor", "integer function abs(x)\n  integer, intent(in) :: x\n  abs = 42 + x\nend function abs"),
                            ]))
    return {case["id"]: case for case in cases}


def build_corpus(root=ROOT):
    files = {}
    specs = case_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["id"].lower().replace(".", "_"))
        manifest = dict(schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
                        evidence=spec["evidence"], standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")])
        if spec["kind"] == "valid":
            if spec.get("compile_only"):
                manifest["expect"] = dict(phase="compile", step="source", outcome="success")
            else:
                manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
                manifest["expect"] = dict(phase="run", outcome="success", exit_code=0,
                                          stdout=spec["stdout"], stderr="")
        else:
            manifest["expect"] = dict(
                phase="compile", step="source", outcome="diagnose",
                diagnostic=dict(file="source.f90", line=spec["line"], end_line=spec["end_line"],
                                contains_any=spec["messages"], excludes_any=list(EXCLUSIONS)))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        spec["source_sha256"] = sha(spec["source"].encode("ascii"))
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def sync_catalogue(catalogue, facet_map, oracle_prefix, oracle, limit_prefix, limitation):
    result = copy.deepcopy(catalogue)
    by_id = {row["id"]: row for row in result["requirements"]}
    for rule, facets in facet_map.items():
        owner = by_id[rule]
        missing = set(facets) - set(owner["facets"])
        if missing:
            raise ValueError(f"{rule} missing facets {sorted(missing)}")
        owner.setdefault("pending", {})
        for facet in facets:
            owner["pending"].pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), oracle_prefix, oracle)
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), limit_prefix, limitation)
    return result


def render_view(catalogue, view_path, section, summary, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / view_path).read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    before, rest = text.split(begin)
    _, after = rest.split(end)
    if section == SECTION_MAIN:
        marker_begin, marker_end = MAIN_SUMMARY_BEGIN, MAIN_SUMMARY_END
    else:
        marker_begin, marker_end = MODULE_SUMMARY_BEGIN, MODULE_SUMMARY_END
    if marker_begin in before or marker_end in before:
        if before.count(marker_begin) != 1 or before.count(marker_end) != 1:
            raise ValueError("owned summary markers changed")
        leading, owned = before.split(marker_begin)
        _, trailing = owned.split(marker_end)
        before = leading.rstrip() + "\n\n" + trailing.lstrip()
    return before.rstrip() + "\n\n" + summary + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def synced_catalogues(root=ROOT):
    root = Path(root)
    main = json.loads((root / MAIN_CATALOGUE).read_text())
    module = json.loads((root / MODULE_CATALOGUE).read_text())
    updated_main = sync_catalogue(main, MAIN_FACETS, MAIN_ORACLE_PREFIX, MAIN_ORACLE,
                                  MAIN_LIMIT_PREFIX, MAIN_LIMITATION)
    updated_module = sync_catalogue(module, MODULE_FACETS, MODULE_ORACLE_PREFIX, MODULE_ORACLE,
                                    MODULE_LIMIT_PREFIX, MODULE_LIMITATION)
    main_pending_reasons = {
        ("S14.1-001", "main-program-unit-classification"):
            "PENDING not discharged: executing a program body observes the body, not the main-program classification; no conforming load-bearing feature mutation distinguishes this facet from ordinary execution.",
        ("S14.1-001", "main-program-first-statement-exclusion"):
            "PENDING not discharged: controls whose first statement is SUBROUTINE, FUNCTION, MODULE, SUBMODULE, or BLOCK DATA classify other program-unit kinds but do not provide a conforming load-bearing single-image runtime oracle for the exclusion itself.",
        ("R1402", "program-stmt-with-name"):
            "PENDING not discharged: the named PROGRAM positive form has no conforming load-bearing feature mutation beyond ordinary execution; the missing-name diagnostic facet is covered separately.",
        ("R1403", "bare-end-program-stmt"):
            "PENDING not discharged: bare END spelling is admitted but has no conforming load-bearing runtime mutation distinct from ordinary main-program execution.",
        ("R1403", "end-program-keyword-stmt"):
            "PENDING not discharged: END PROGRAM spelling is admitted but has no conforming load-bearing runtime mutation distinct from ordinary main-program execution.",
        ("R1403", "end-program-named-stmt"):
            "PENDING not discharged: END PROGRAM name spelling is admitted but has no conforming load-bearing runtime mutation; C1401 identity is deferred to existing coverage noted in source accounting.",
        ("S14.1-002", "non-fortran-main-definition-permitted"):
            "PENDING not discharged: the permission depends on a processor/build-system non-Fortran main and has no mandatory portable Fortran-only single-image oracle.",
        ("S14.1-003", "non-fortran-main-excludes-fortran-main-unit"):
            "PENDING not discharged: this is an unnumbered mixed-language program restriction with no required diagnostic; a conforming C-main control would not observe the prohibited case.",
        ("S14.1-004", "main-program-reference-prohibited"):
            "PENDING not discharged: this unnumbered program restriction has no required diagnostic; a positive call to a different external procedure is only a source-control companion.",
    }
    for (rule, facet), reason in main_pending_reasons.items():
        row = next(row for row in updated_main["requirements"] if row["id"] == rule)
        if facet in row.get("facets", []):
            row.setdefault("pending", {})[facet] = reason
    module_pending_reasons = {
        ("S14.2.1-001", "module-contains-declarations-specifications-definitions"):
            "PENDING not discharged: value/body changes observe the chosen declarations or procedure body, not the module-contains classification; no conforming load-bearing feature mutation is available here.",
        ("S14.2.1-002", "public-module-identifiers-use-accessible"):
            "PENDING not discharged: a simple USE/value check overlaps 14.2.2 use association and was only supported by value/body mutants; 14.2.2 owns accessibility effects.",
        ("S14.2.1-003", "nonintrinsic-module-program-unit-defined"):
            "PENDING not discharged: defining a Fortran module and changing its exported value observes the body, not the nonintrinsic-module definition facet; no conforming load-bearing feature mutation is available here.",
        ("R1404", "module-program-unit-form"):
            "PENDING not discharged: the positive module form has no conforming load-bearing feature mutation beyond ordinary execution; the missing-END diagnostic facet is covered separately.",
        ("R1405", "module-stmt-with-name"):
            "PENDING not discharged: the positive MODULE-name form has no conforming load-bearing feature mutation beyond ordinary execution; the missing-name diagnostic facet is covered separately.",
        ("R1407", "module-subprogram-part-with-contains"):
            "PENDING not discharged: the positive CONTAINS-plus-subprogram form was only observed through a procedure body value; the without-CONTAINS diagnostic facet is covered separately.",
        ("R1407", "contains-without-module-subprograms"):
            "PENDING not discharged: empty CONTAINS admission has no conforming load-bearing runtime mutation distinct from ordinary module admission.",
        ("R1408", "module-function-subprogram"):
            "PENDING not discharged: changing a contained function result observes the function body, not the R1408 function-subprogram alternative.",
        ("R1408", "module-subroutine-subprogram"):
            "PENDING not discharged: changing a contained subroutine assignment observes the subroutine body, not the R1408 subroutine-subprogram alternative.",
        ("C1402", "end-module-name-identical"):
            "PENDING not discharged: a matching END MODULE name positive control has no conforming load-bearing feature mutation; the mismatched-name diagnostic facet is covered separately.",
        ("S14.2.1-003", "intrinsic-module-processor-provided"):
            "PENDING not discharged: intrinsic module provision is processor/intrinsic-module ownership; using ISO_FORTRAN_ENV would only retest its own Clause 16 entities without a 14.2.1-specific load-bearing mutation.",
        ("S14.2.1-003", "nonintrinsic-module-non-fortran-defined"):
            "PENDING not discharged: non-Fortran module definition is processor/build-system latitude without a mandatory portable source fixture.",
        ("S14.2.1-004", "intrinsic-module-procedures-not-intrinsic-procedures"):
            "PENDING not discharged: procedure classification for entities supplied by intrinsic modules is owned by their Clause 16/15 procedure rules; no 14.2.1-specific runtime oracle is introduced.",
        ("S14.2.1-004", "intrinsic-module-types-not-intrinsic-types"):
            "PENDING not discharged: type classification for intrinsic-module derived types is owned by their intrinsic-module/type rules; no 14.2.1-specific runtime oracle is introduced.",
        ("R1406", "bare-end-module-stmt"):
            "PENDING not discharged: bare END MODULE spelling is admitted but has no conforming load-bearing runtime mutation; C1402 covers named-end identity.",
        ("R1406", "end-module-keyword-stmt"):
            "PENDING not discharged: END MODULE spelling is admitted but has no conforming load-bearing runtime mutation; C1402 covers named-end identity.",
        ("R1406", "end-module-named-stmt"):
            "PENDING not discharged: END MODULE name spelling is admitted but has no conforming load-bearing runtime mutation; C1402 separately observes matching/mismatched names.",
        ("R1408", "separate-module-subprogram-form"):
            "PENDING not discharged: separate module subprogram execution is owned by the submodule packet for 14.2.3; this 14.2.1 packet does not duplicate it.",
    }
    for (rule, facet), reason in module_pending_reasons.items():
        row = next(row for row in updated_module["requirements"] if row["id"] == rule)
        if facet in row.get("facets", []):
            row.setdefault("pending", {})[facet] = reason
    main_summary = (MAIN_SUMMARY_BEGIN + "\n## Batch281 main-program fixtures\n\n" +
                    "Diagnostic fixtures cover a missing PROGRAM name and malformed END PROGRAM extra "
                    "token with conforming controls. Optional END PROGRAM spellings, non-Fortran main programs, "
                    "and prose-only main-program reference restrictions remain pending for the reasons recorded "
                    "in the catalogue.\n" + MAIN_SUMMARY_END)
    module_summary = (MODULE_SUMMARY_BEGIN + "\n## Batch281 module fixtures\n\n" +
                      "Runtime fixtures exercise p3/p4 EXTERNAL/INTRINSIC resolution. "
                      "Diagnostic fixtures cover R1404-R1408 malformed source, C1402 name mismatch, and C1403 "
                      "statement-function/ENTRY/FORMAT exclusions, each with a one-property control. Optional END "
                      "MODULE spelling facets, intrinsic-module classifications, non-Fortran module definitions, "
                      "and separate-module-subprogram execution remain pending.\n" + MODULE_SUMMARY_END)
    return {
        MAIN_CATALOGUE: json.dumps(updated_main, indent=2) + "\n",
        MODULE_CATALOGUE: json.dumps(updated_module, indent=2) + "\n",
        MAIN_VIEW: render_view(updated_main, MAIN_VIEW, SECTION_MAIN, main_summary, root),
        MODULE_VIEW: render_view(updated_module, MODULE_VIEW, SECTION_MODULE, module_summary, root),
    }


def generate(root=ROOT, check=False, sync=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_files = synced_catalogues(root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for name, text in catalogue_files.items():
            if (root / name).read_text() != text:
                stale.append(name)
        if stale:
            raise ValueError("stale modules 14.1/14.2.1 fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync:
            for name, text in catalogue_files.items():
                (root / name).write_text(text)
    return specs


def classify_compiler(command):
    name = Path(command).name.lower()
    return "lfortran" if "lfortran" in name else "gfortran"


def compiler_args(command, standard, source, output):
    flag = f"--std={standard}" if "lfortran" in Path(command).name else f"-std={standard}"
    return [command, flag, source, "-o", output]


def mutated_source(source, mutations, selected):
    result = source
    for label, old, new in mutations:
        if label in selected:
            if result.count(old) != 1:
                raise ValueError(f"mutation token for {label!r} is not unique")
            result = result.replace(old, new)
    return result


def mutation_check(root, compiler, standard):
    root = Path(root)
    specs = generate(root, check=True)
    family = classify_compiler(compiler)
    work_root = Path(tempfile.mkdtemp(prefix=f"modules-14-1-14-2-1-{family}-", dir=str(root.parent)))
    total = 0
    failures = []
    try:
        for spec in specs.values():
            if spec["kind"] != "valid" or spec.get("compile_only") or not spec.get("mutations"):
                continue
            mutation_sets = []
            if spec["id"] == "S14_2_1_005_valid__external_implicit_interface_declarations":
                mutation_sets = [
                    ("module-implicit-interface-procedure-external", ["EXTERNAL attribute selects external ABS"]),
                    ("module-implicit-interface-function-explicit-type", ["explicit character function length", "external character function definition length"]),
                ]
            elif spec["id"] == "S14_2_1_006_valid__intrinsic_attribute":
                mutation_sets = [
                    ("module-intrinsic-procedure-intrinsic-attribute", ["INTRINSIC attribute selects intrinsic ABS", "external ABS definition for attribute mutation"]),
                ]
            elif spec["id"] == "S14_2_1_006_valid__intrinsic_use":
                mutation_sets = [
                    ("module-intrinsic-procedure-intrinsic-use", ["direct intrinsic use without declaration", "external ABS definition for intrinsic-use mutation"]),
                ]
            else:
                mutation_sets = [(label, [label]) for label, _, _ in spec["mutations"]]
            for index, (matrix_label, labels) in enumerate(mutation_sets, 1):
                total += 1
                work = work_root / (spec["id"] + f"_{index}")
                work.mkdir()
                try:
                    mutated = mutated_source(spec["source"], spec["mutations"], set(labels))
                except ValueError as error:
                    failures.append((spec["id"], matrix_label, str(error)))
                    continue
                if sha(mutated.encode("ascii")) == spec["source_sha256"]:
                    failures.append((spec["id"], matrix_label, "mutant is identical to parent"))
                    continue
                (work / "source.f90").write_text(mutated)
                exe = work / "program"
                comp = subprocess.run(compiler_args(compiler, standard, "source.f90", "program"),
                                      cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if comp.returncode != 0:
                    failures.append((spec["id"], matrix_label,
                                     "mutant did not compile: " + (comp.stderr + comp.stdout)[:500]))
                    continue
                run = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if run.returncode == 0 and run.stdout == spec["stdout"] and run.stderr == "":
                    failures.append((spec["id"], matrix_label, "mutant survived"))
    finally:
        shutil.rmtree(work_root, ignore_errors=True)
    if failures:
        detail = "\n".join(f"{case} {label}: {reason}" for case, label, reason in failures)
        raise SystemExit(f"{len(failures)} of {total} mutants did not fail on {family}:\n{detail}")
    print(f"{total}/{total} mutants failed on {family}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check")
    parser.add_argument("--std", default="f23")
    args = parser.parse_args()
    if args.mutation_check:
        mutation_check(args.root, args.mutation_check, args.std)
        return
    specs = generate(args.root, check=args.check, sync=args.sync_catalogue)
    invalid = sum(1 for spec in specs.values() if spec["kind"] == "invalid")
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} modules 14.1/14.2.1 cases ({invalid} invalid).")


if __name__ == "__main__":
    main()
