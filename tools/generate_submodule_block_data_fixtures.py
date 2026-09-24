#!/usr/bin/env python3
"""Submodule and block data fixtures for Fortran 2023 14.2.3 and 14.3."""

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
SUBMODULE_CATALOGUE = "doc/catalogues/submodules_14_2_3.json"
BLOCK_DATA_CATALOGUE = "doc/catalogues/block_data_program_units_14_3.json"
SUBMODULE_VIEW = "doc/fortran_2023_14_2_3.md"
BLOCK_DATA_VIEW = "doc/fortran_2023_14_3.md"
SECTION_SUBMODULE = "14.2.3"
SECTION_BLOCK_DATA = "14.3"
PREFIX = "submodule_block_data_"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
)
SUBMODULE_ORACLE_PREFIX = "Batch270 submodule fixture family: "
SUBMODULE_LIMIT_PREFIX = "Batch270 submodule fixture boundaries: "
BLOCK_DATA_ORACLE_PREFIX = "Batch270 block data fixture family: "
BLOCK_DATA_LIMIT_PREFIX = "Batch270 block data fixture boundaries: "
SUBMODULE_SUMMARY_BEGIN = "<!-- BEGIN SUBMODULE BLOCK DATA FIXTURES: SUBMODULES -->"
SUBMODULE_SUMMARY_END = "<!-- END SUBMODULE BLOCK DATA FIXTURES: SUBMODULES -->"
BLOCK_DATA_SUMMARY_BEGIN = "<!-- BEGIN SUBMODULE BLOCK DATA FIXTURES: BLOCK DATA -->"
BLOCK_DATA_SUMMARY_END = "<!-- END SUBMODULE BLOCK DATA FIXTURES: BLOCK DATA -->"

SUBMODULE_FACETS = {
    "S14.2.3-001": ["submodule-host-is-parent-identifier", "submodule-can-extend-module-or-submodule"],
    "S14.2.3-002": ["ancestor-descendant-chain", "ordered-pair-submodule-identifier", "submodule-name-not-local-or-global-identifier"],
    "S14.2.3-003": ["ancestor-declared-procedure-implemented-in-submodule", "submodule-declared-procedure-implemented-in-descendant"],
    "S14.2.3-004": ["ancestor-module-entity-host-associated-in-submodule", "parent-submodule-entity-host-associated-in-child"],
    "R1416": ["submodule-specification-part-form", "submodule-module-subprogram-part-form", "malformed-submodule-order-rejected"],
    "R1417": ["malformed-submodule-statement-rejected"],
    "C1411": ["format-stmt-forbidden-in-submodule-spec"],
    "C1413": ["matching-end-submodule-name", "mismatched-end-submodule-name-rejected"],
}

BLOCK_DATA_FACETS = {
    "S14.3-001": ["named-common-initial-values-observable"],

    "C1414": ["end-block-data-name-requires-start-name", "matching-end-block-data-name", "mismatched-end-block-data-name-rejected"],
    "C1415": ["unlisted-specification-statement-rejected"],
    "C1416": ["allocatable-attribute-forbidden-in-block-data-type-decl"],
    "S14.3-002": ["all-storage-units-specified-for-initialized-common"],
    "S14.3-003": ["multiple-named-common-blocks-in-one-block-data"],
    "S14.3-004": ["initialized-object-in-named-common"],

}

SUBMODULE_ORACLE = SUBMODULE_ORACLE_PREFIX + (
    "submodule fixtures cover host selection, extension of a module and of a submodule, ancestor/descendant "
    "chains, duplicate submodule names under distinct ancestor modules, separate module procedure bodies "
    "declared in ancestors and descendants, descendant host association, the R1416 specification and module "
    "subprogram parts, and required diagnostics for submodule ordering, malformed SUBMODULE syntax, FORMAT in "
    "the submodule specification part, and mismatched END SUBMODULE names. Runtime cases use exact integer "
    "sentinels and completion stdout; diagnostic cases have one-property positive controls and line-bounded "
    "messages."
)
SUBMODULE_LIMITATION = SUBMODULE_LIMIT_PREFIX + (
    "coarrays, link-name spellings, procedure pointer details, 15.6.2.5 procedure semantics beyond the invoked "
    "separate module procedures, R1417/R1418/R1419 optional-form semantics without load-bearing runtime mutants, "
    "C1412 parent invalids, ENTRY and statement-function variants of C1411, and stand-alone claims about global "
    "symbols are not represented. Frozen LFortran 0.65.0-411 rejects the duplicate "
    "submodule-name ordered-pair fixture that gfortran accepts; that is reported as a target defect, not suppressed. "
    "The fixtures add no review approval, evidence "
    "link, SourceUse renewal, baseline update or universal compiler-conformance claim."
)
BLOCK_DATA_ORACLE = BLOCK_DATA_ORACLE_PREFIX + (
    "block data fixtures cover observable initialization of named COMMON blocks, all-storage-units-specified "
    "source form, multiple named common blocks in one block data program unit, initialized objects that belong "
    "to named common blocks, matching block-data end names, and required diagnostics for C1414, C1415 and "
    "C1416. Runtime cases use exact nonzero integer values from named COMMON blocks before assignment; "
    "diagnostic cases have one-property controls."
)
BLOCK_DATA_LIMITATION = BLOCK_DATA_LIMIT_PREFIX + (
    "R1420/R1421/R1422 optional-form semantics without load-bearing runtime mutants, declaration-only C1415 "
    "listed-statement census, BIND statement admission, VALUE/COMMON storage layout, undefined common members, "
    "duplicate-common and duplicate-unnamed prose restrictions without required diagnostic obligation, and "
    "processor diagnostic wording are not represented. Frozen LFortran 0.65.0-411 accepts the "
    "four shipped block-data invalids that gfortran diagnoses; those are reported as target defects, not "
    "suppressed. The fixtures add no review approval, SourceUse renewal, baseline update or universal claim."
)


def src_submodule_tree():
    return """module tree_root_m
  implicit none
  integer, parameter :: module_base = 17
  interface
    module subroutine set_from_module(value)
      integer, intent(out) :: value
    end subroutine
    module function from_child() result(value)
      integer :: value
    end function
  end interface
end module tree_root_m
submodule (tree_root_m) tree_parent
  implicit none
  integer, parameter :: parent_base = 30
  interface
    module function declared_in_parent() result(value)
      integer :: value
    end function
  end interface
contains
  module procedure set_from_module
    value = module_base + 5
  end procedure set_from_module
end submodule tree_parent
submodule (tree_root_m:tree_parent) tree_child
contains
  module procedure from_child
    value = parent_base + 11
  end procedure from_child
  module procedure declared_in_parent
    value = module_base + parent_base + 7
  end procedure declared_in_parent
end submodule tree_child
program submodule_tree_probe
  use tree_root_m
  implicit none
  integer :: value, checks
  checks = 0
  value = -99
  call set_from_module(value)
  if (value /= 22) error stop
  checks = checks + 1
  if (from_child() /= 41) error stop
  checks = checks + 1
  if (declared_in_parent() /= 54) error stop
  checks = checks + 1
  if (checks /= 3) error stop
  print '(a)', 'SUBMODULE TREE OK'
end program submodule_tree_probe
"""


def src_submodule_identifier_pairs():
    return """module pair_left_m
  implicit none
  interface
    module function value_left() result(value)
      integer :: value
    end function
  end interface
end module pair_left_m
module pair_right_m
  implicit none
  interface
    module function value_right() result(value)
      integer :: value
    end function
  end interface
end module pair_right_m
submodule (pair_left_m) impl
contains
  module procedure value_left
    value = 14
  end procedure value_left
end submodule impl
submodule (pair_right_m) impl
contains
  module procedure value_right
    value = 23
  end procedure value_right
end submodule impl
program submodule_pair_probe
  use pair_left_m
  use pair_right_m
  implicit none
  integer :: checks
  checks = 0
  if (value_left() /= 14) error stop
  checks = checks + 1
  if (value_right() /= 23) error stop
  checks = checks + 1
  if (checks /= 2) error stop
  print '(a)', 'SUBMODULE IDENTIFIER PAIRS OK'
end program submodule_pair_probe
"""


def src_submodule_minimal():
    return """module minimal_parent_m
  implicit none
  interface
    module subroutine later(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module minimal_parent_m
submodule (minimal_parent_m) minimal_child
end submodule minimal_child
"""


def src_submodule_end_forms():
    return """module end_forms_m
  implicit none
  interface
    module function bare_value() result(value)
      integer :: value
    end function
    module function keyword_value() result(value)
      integer :: value
    end function
    module function named_value() result(value)
      integer :: value
    end function
  end interface
end module end_forms_m
submodule (end_forms_m) bare_end_sm
contains
  module procedure bare_value
    value = 9
  end procedure bare_value
end
submodule (end_forms_m) keyword_end_sm
contains
  module procedure keyword_value
    value = 10
  end procedure keyword_value
end submodule
submodule (end_forms_m) named_end_sm
contains
  module procedure named_value
    value = 11
  end procedure named_value
end submodule named_end_sm
program submodule_end_forms_probe
  use end_forms_m
  implicit none
  if (bare_value() /= 9) error stop
  if (keyword_value() /= 10) error stop
  if (named_value() /= 11) error stop
  print '(a)', 'SUBMODULE END FORMS OK'
end program submodule_end_forms_probe
"""


def src_submodule_statement_control():
    return """module statement_control_m
  implicit none
  interface
    module subroutine p(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module statement_control_m
submodule (statement_control_m) statement_control_sm
contains
  module procedure p
    value = 18
  end procedure p
end submodule statement_control_sm
"""


def src_submodule_statement_invalid():
    return src_submodule_statement_control().replace(
        "submodule (statement_control_m) statement_control_sm",
        "submodule statement_control_m statement_control_sm", 1)


def src_submodule_format_control():
    return """module format_control_m
  implicit none
  interface
    module subroutine p(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module format_control_m
submodule (format_control_m) format_control_sm
contains
  module procedure p
    100 format(I0)
    value = 13
  end procedure p
end submodule format_control_sm
"""


def src_submodule_format_invalid():
    return src_submodule_format_control().replace(
        "submodule (format_control_m) format_control_sm\ncontains",
        "submodule (format_control_m) format_control_sm\n  100 format(I0)\ncontains", 1).replace(
        "  module procedure p\n    100 format(I0)\n", "  module procedure p\n", 1)


def src_submodule_end_mismatch_control():
    return """module mismatch_control_m
  implicit none
  interface
    module subroutine p(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module mismatch_control_m
submodule (mismatch_control_m) sm
contains
  module procedure p
    value = 44
  end procedure p
end submodule sm
"""


def src_submodule_end_mismatch_invalid():
    return src_submodule_end_mismatch_control().replace("end submodule sm\n", "end submodule other\n")


def src_block_data_values():
    return """program block_data_values_probe
  implicit none
  integer :: a, b, c, left_value, right_value, checks
  common /main_blk/ a, b, c
  common /left_blk/ left_value
  common /right_blk/ right_value
  checks = 0
  if (b /= 33) error stop
  checks = checks + 1
  if (left_value /= 12) error stop
  checks = checks + 1
  if (right_value /= 34) error stop
  checks = checks + 1
  if (checks /= 3) error stop
  print '(a)', 'BLOCK DATA VALUES OK'
end program block_data_values_probe
block data bd_values
  implicit none
  integer :: a, b, c, left_value, right_value
  common /main_blk/ a, b, c
  common /left_blk/ left_value
  common /right_blk/ right_value
  data b /33/
  data left_value /12/
  data right_value /34/
end block data bd_values
"""


def src_block_data_unnamed_and_named():
    return """program block_data_unnamed_probe
  implicit none
  integer :: unnamed_value, named_value
  common /unnamed_blk/ unnamed_value
  common /named_blk/ named_value
  if (unnamed_value /= 21) error stop
  if (named_value /= 62) error stop
  print '(a)', 'BLOCK DATA UNNAMED OK'
end program block_data_unnamed_probe
block data
  implicit none
  integer :: unnamed_value
  common /unnamed_blk/ unnamed_value
  data unnamed_value /21/
end block data
block data bd_named
  implicit none
  integer :: named_value
  common /named_blk/ named_value
  data named_value /62/
end block data bd_named
"""


def src_block_data_end_forms():
    return """program block_data_end_forms_probe
  implicit none
  integer :: bare_value, keyword_value, named_value
  common /bare_blk/ bare_value
  common /keyword_blk/ keyword_value
  common /end_named_blk/ named_value
  if (bare_value /= 24) error stop
  if (keyword_value /= 25) error stop
  if (named_value /= 26) error stop
  print '(a)', 'BLOCK DATA END FORMS OK'
end program block_data_end_forms_probe
block data bd_bare
  implicit none
  integer :: bare_value
  common /bare_blk/ bare_value
  data bare_value /24/
end
block data bd_keyword
  implicit none
  integer :: keyword_value
  common /keyword_blk/ keyword_value
  data keyword_value /25/
end block data
block data bd_named_end
  implicit none
  integer :: named_value
  common /end_named_blk/ named_value
  data named_value /26/
end block data bd_named_end
"""


def src_block_data_distinct_owners():
    return """program block_data_distinct_probe
  implicit none
  integer :: first_value, second_value
  common /first_blk/ first_value
  common /second_blk/ second_value
  if (first_value /= 51) error stop
  if (second_value /= 52) error stop
  print '(a)', 'BLOCK DATA DISTINCT OWNERS OK'
end program block_data_distinct_probe
block data bd_first
  implicit none
  integer :: first_value
  common /first_blk/ first_value
  data first_value /51/
end block data bd_first
block data bd_second
  implicit none
  integer :: second_value
  common /second_blk/ second_value
  data second_value /52/
end block data bd_second
"""


def src_block_data_minimal():
    return """block data bd_minimal
end block data bd_minimal
"""


def src_block_data_name_control():
    return """block data bd
  integer :: a
  common /name_control_blk/ a
  data a /27/
end block data bd
"""


def src_block_data_unnamed_end_invalid():
    return src_block_data_name_control().replace("block data bd\n", "block data\n", 1)


def src_block_data_mismatch_invalid():
    return src_block_data_name_control().replace("end block data bd\n", "end block data other\n")


def src_block_data_alloc_control():
    return """block data bd_alloc_control
  integer :: a
end block data bd_alloc_control
"""


def src_block_data_alloc_invalid():
    return src_block_data_alloc_control().replace("integer :: a", "integer, allocatable :: a")


def src_block_data_external_control():
    return """block data bd_intrinsic_control
  intrinsic :: abs
end block data bd_intrinsic_control
"""


def src_block_data_external_invalid():
    return src_block_data_external_control().replace("intrinsic :: abs", "external :: f")


def valid_case(name, rule, facets, source, stdout=None, evidence="effect", compile_only=False, mutations=None):
    return dict(id=name, kind="valid", rule=rule, facets=facets, evidence=evidence, source=source,
                stdout=stdout, compile_only=compile_only, mutations=[list(item) for item in (mutations or [])])


def invalid_case(name, rule, facets, source, line, messages, control, lfortran_defect=False, end_line=None):
    return dict(id=name, kind="invalid", rule=rule, facets=facets, evidence="effect", source=source,
                line=line, end_line=end_line or line, messages=messages, control=control,
                lfortran_defect=lfortran_defect)



def src_submodule_p2_relationships():
    return """module relation_root_m
  implicit none
  interface
    module function child_value() result(value)
      integer :: value
    end function
  end interface
end module relation_root_m
module relation_left_m
  implicit none
  interface
    module function left_value() result(value)
      integer :: value
    end function
  end interface
end module relation_left_m
module relation_right_m
  implicit none
  interface
    module function right_value() result(value)
      integer :: value
    end function
  end interface
end module relation_right_m
submodule (relation_root_m) relation_parent
contains
end submodule relation_parent
submodule (relation_root_m:relation_parent) relation_child
contains
  module procedure child_value
    value = 41
  end procedure child_value
end submodule relation_child
submodule (relation_left_m) impl
contains
  module procedure left_value
    value = 14
  end procedure left_value
end submodule impl
submodule (relation_right_m) impl
contains
  module procedure right_value
    value = 23
  end procedure right_value
end submodule impl
program submodule_relationship_probe
  use relation_root_m
  use relation_left_m
  use relation_right_m
  implicit none
  if (child_value() /= 41) error stop
  if (left_value() /= 14) error stop
  if (right_value() /= 23) error stop
  print '(a)', 'SUBMODULE RELATIONSHIPS OK'
end program submodule_relationship_probe
"""


def src_submodule_separate_procedures():
    return """module separate_proc_m
  implicit none
  interface
    module subroutine ancestor_set(value)
      integer, intent(out) :: value
    end subroutine
    module function child_value() result(value)
      integer :: value
    end function
  end interface
end module separate_proc_m
submodule (separate_proc_m) separate_parent
  implicit none
  interface
    module function declared_in_submodule() result(value)
      integer :: value
    end function
  end interface
contains
  module procedure ancestor_set
    value = 42
  end procedure ancestor_set
end submodule separate_parent
submodule (separate_proc_m:separate_parent) separate_child
contains
  module procedure child_value
    value = declared_in_submodule() - 1
  end procedure child_value
  module procedure declared_in_submodule
    value = 65
  end procedure declared_in_submodule
end submodule separate_child
program separate_procedure_probe
  use separate_proc_m
  implicit none
  integer :: value
  value = -7
  call ancestor_set(value)
  if (value /= 42) error stop
  if (child_value() /= 64) error stop
  print '(a)', 'SUBMODULE SEPARATE PROCEDURES OK'
end program separate_procedure_probe
"""


def src_submodule_host_association():
    return """module host_assoc_m
  implicit none
  integer, parameter :: module_base = 17
  interface
    module subroutine module_host_value(value)
      integer, intent(out) :: value
    end subroutine
    module function parent_host_value() result(value)
      integer :: value
    end function
  end interface
end module host_assoc_m
submodule (host_assoc_m) host_parent
  implicit none
  integer, parameter :: parent_base = 30
contains
  module procedure module_host_value
    value = module_base + 5
  end procedure module_host_value
end submodule host_parent
submodule (host_assoc_m:host_parent) host_child
contains
  module procedure parent_host_value
    value = parent_base + 11
  end procedure parent_host_value
end submodule host_child
program host_association_probe
  use host_assoc_m
  implicit none
  integer :: value
  value = -99
  call module_host_value(value)
  if (value /= 22) error stop
  if (parent_host_value() /= 41) error stop
  print '(a)', 'SUBMODULE HOST ASSOCIATION OK'
end program host_association_probe
"""


def src_submodule_r1416_forms():
    return """module r1416_m
  implicit none
  interface
    module subroutine implemented(value)
      integer, intent(out) :: value
    end subroutine
    module subroutine unimplemented(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module r1416_m
submodule (r1416_m) minimal_r1416
end submodule minimal_r1416
submodule (r1416_m) full_r1416
  implicit none
  integer, parameter :: k = 8
contains
  module procedure implemented
    value = k + 7
  end procedure implemented
end submodule full_r1416
program r1416_probe
  use r1416_m
  implicit none
  integer :: value
  value = -8
  call implemented(value)
  if (value /= 15) error stop
  print '(a)', 'SUBMODULE R1416 FORMS OK'
end program r1416_probe
"""



def src_submodule_order_invalid():
    return src_submodule_r1416_forms().replace("contains\n  module procedure implemented", "contains\n  integer :: late_decl\n  module procedure implemented", 1)

def src_submodule_parent_identifier_forms():
    return """module parent_identifier_m
  implicit none
  interface
    module function module_parent_value() result(value)
      integer :: value
    end function
    module function submodule_parent_value() result(value)
      integer :: value
    end function
  end interface
end module parent_identifier_m
submodule (parent_identifier_m) parent_identifier_parent
contains
  module procedure module_parent_value
    value = 12
  end procedure module_parent_value
end submodule parent_identifier_parent
submodule (parent_identifier_m:parent_identifier_parent) parent_identifier_child
contains
  module procedure submodule_parent_value
    value = 32
  end procedure submodule_parent_value
end submodule parent_identifier_child
program parent_identifier_probe
  use parent_identifier_m
  implicit none
  if (module_parent_value() /= 12) error stop
  if (submodule_parent_value() /= 32) error stop
  print '(a)', 'SUBMODULE PARENT IDENTIFIER FORMS OK'
end program parent_identifier_probe
"""


def src_block_data_initial_values():
    return """program block_data_initial_values_probe
  implicit none
  integer :: a, b
  common /initial_blk/ a, b
  if (a /= 17) error stop
  if (b /= 23) error stop
  print '(a)', 'BLOCK DATA INITIAL VALUES OK'
end program block_data_initial_values_probe
block data bd_initial_values
  implicit none
  integer :: a, b
  common /initial_blk/ a, b
  data a /17/
  data b /23/
end block data bd_initial_values
block data bd_initial_values_alt
  implicit none
  integer :: alt_a, alt_b
  common /initial_alt_blk/ alt_a, alt_b
  data alt_a /18/
  data alt_b /24/
end block data bd_initial_values_alt
"""


def src_block_data_r1420_forms():
    return """program block_data_r1420_probe
  implicit none
  integer :: value
  common /r1420_blk/ value
  if (value /= 19) error stop
  print '(a)', 'BLOCK DATA R1420 FORMS OK'
end program block_data_r1420_probe
block data bd_minimal_r1420
end block data bd_minimal_r1420
block data bd_spec_r1420
  implicit none
  integer :: value
  common /r1420_blk/ value
  data value /19/
end block data bd_spec_r1420
"""


def src_block_data_r1421_forms():
    return """program block_data_r1421_probe
  implicit none
  integer :: unnamed_value, named_value
  common /r1421_unnamed_blk/ unnamed_value
  common /r1421_named_blk/ named_value
  if (unnamed_value /= 21) error stop
  if (named_value /= 22) error stop
  print '(a)', 'BLOCK DATA R1421 FORMS OK'
end program block_data_r1421_probe
block data
  implicit none
  integer :: unnamed_value
  common /r1421_unnamed_blk/ unnamed_value
  data unnamed_value /21/
end block data
block data bd_r1421_named
  implicit none
  integer :: named_value
  common /r1421_named_blk/ named_value
  data named_value /22/
end block data bd_r1421_named
"""


def src_block_data_all_storage_specified():
    return """program block_data_storage_sequence_probe
  implicit none
  integer :: a, b, c
  common /storage_blk/ a, b, c
  if (b /= 33) error stop
  print '(a)', 'BLOCK DATA STORAGE SEQUENCE OK'
end program block_data_storage_sequence_probe
block data bd_storage_sequence
  implicit none
  integer :: a, b, c
  common /storage_blk/ a, b, c
  data b /33/
end block data bd_storage_sequence
block data bd_storage_sequence_alt
  implicit none
  integer :: alt_a, alt_b, alt_c
  common /storage_alt_blk/ alt_a, alt_b, alt_c
  data alt_b /34/
end block data bd_storage_sequence_alt
"""


def src_block_data_multiple_named_common():
    return """program block_data_multiple_named_probe
  implicit none
  integer :: left_value, right_value
  common /multi_left_blk/ left_value
  common /multi_right_blk/ right_value
  if (left_value /= 12) error stop
  if (right_value /= 34) error stop
  print '(a)', 'BLOCK DATA MULTIPLE NAMED OK'
end program block_data_multiple_named_probe
block data bd_multiple_named
  implicit none
  integer :: left_value, right_value
  common /multi_left_blk/ left_value
  common /multi_right_blk/ right_value
  data left_value /12/
  data right_value /34/
end block data bd_multiple_named
block data bd_multiple_named_alt
  implicit none
  integer :: alt_left_value, alt_right_value
  common /multi_left_alt_blk/ alt_left_value
  common /multi_right_alt_blk/ alt_right_value
  data alt_left_value /13/
  data alt_right_value /35/
end block data bd_multiple_named_alt
"""


def src_block_data_initialized_object_named_common():
    return """program block_data_named_object_probe
  implicit none
  integer :: value
  common /named_object_blk/ value
  if (value /= 45) error stop
  print '(a)', 'BLOCK DATA NAMED OBJECT OK'
end program block_data_named_object_probe
block data bd_named_object
  implicit none
  integer :: value
  common /named_object_blk/ value
  data value /45/
end block data bd_named_object
block data bd_named_object_alt
  implicit none
  integer :: alt_value
  common /named_object_alt_blk/ alt_value
  data alt_value /46/
end block data bd_named_object_alt
"""


def case_specs():
    cases = []
    cases.append(valid_case("S14_2_3_001_valid__submodule_host_parent_identifier", "S14.2.3-001",
                            SUBMODULE_FACETS["S14.2.3-001"], src_submodule_host_association(),
                            "SUBMODULE HOST ASSOCIATION OK\n", mutations=[
                                ("module host parameter", "module_base = 17", "module_base = 18"),
                                ("parent submodule host value", "parent_base = 30", "parent_base = 31"),
                            ]))
    cases.append(valid_case("S14_2_3_002_valid__submodule_relationships", "S14.2.3-002",
                            SUBMODULE_FACETS["S14.2.3-002"], src_submodule_p2_relationships(),
                            "SUBMODULE RELATIONSHIPS OK\n", mutations=[
                                ("child descendant result", "value = 41", "value = 42"),
                                ("left ordered pair result", "value = 14", "value = 15"),
                                ("right ordered pair result", "value = 23", "value = 24"),
                            ]))
    cases.append(valid_case("S14_2_3_003_valid__separate_module_procedures", "S14.2.3-003",
                            SUBMODULE_FACETS["S14.2.3-003"], src_submodule_separate_procedures(),
                            "SUBMODULE SEPARATE PROCEDURES OK\n", mutations=[
                                ("ancestor separate procedure", "value = 42", "value = 43"),
                                ("descendant separate procedure", "value = 65", "value = 66"),
                            ]))
    cases.append(valid_case("S14_2_3_004_valid__submodule_host_association", "S14.2.3-004",
                            SUBMODULE_FACETS["S14.2.3-004"], src_submodule_host_association(),
                            "SUBMODULE HOST ASSOCIATION OK\n", mutations=[
                                ("module associated entity", "module_base = 17", "module_base = 16"),
                                ("parent associated entity", "parent_base = 30", "parent_base = 29"),
                            ]))
    cases.append(valid_case("R1416_valid__submodule_forms", "R1416",
                            ["submodule-specification-part-form", "submodule-module-subprogram-part-form"],
                            src_submodule_r1416_forms(), "SUBMODULE R1416 FORMS OK\n", mutations=[
                                ("specification parameter", "integer, parameter :: k = 8", "integer, parameter :: k = 9"),
                                ("module subprogram body", "value = k + 7", "value = k + 8"),
                            ]))
    cases.append(invalid_case("R1416_invalid__submodule_declaration_after_contains", "R1416",
                              ["malformed-submodule-order-rejected"], src_submodule_order_invalid(), 18,
                              ["Unexpected", "Invalid", "Unexpected data declaration"],
                              "R1416_valid__submodule_forms"))
    cases.append(valid_case("R1417_valid__submodule_statement_control", "R1417", ["malformed-submodule-statement-rejected"],
                            src_submodule_statement_control(), compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("R1417_invalid__submodule_statement_missing_parens", "R1417",
                              ["malformed-submodule-statement-rejected"], src_submodule_statement_invalid(), 9,
                              ["unexpected here", "Syntax error in SUBMODULE"], "R1417_valid__submodule_statement_control"))
    cases.append(valid_case("C1411_valid__submodule_format_in_procedure_control", "C1411", ["format-stmt-forbidden-in-submodule-spec"],
                            src_submodule_format_control(), compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1411_invalid__submodule_format_in_specification_part", "C1411",
                              ["format-stmt-forbidden-in-submodule-spec"], src_submodule_format_invalid(), 10,
                              ["executable statement is not allowed", "Format statement"], "C1411_valid__submodule_format_in_procedure_control"))
    cases.append(valid_case("C1413_valid__submodule_end_name_control", "C1413", ["matching-end-submodule-name", "mismatched-end-submodule-name-rejected"],
                            src_submodule_end_mismatch_control(), compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1413_invalid__submodule_end_name_mismatch", "C1413",
                              ["mismatched-end-submodule-name-rejected"], src_submodule_end_mismatch_invalid(), 9,
                              ["End submodule name", "Expected label"], "C1413_valid__submodule_end_name_control",
                              end_line=14))

    cases.append(valid_case("S14_3_001_valid__block_data_initial_values", "S14.3-001", BLOCK_DATA_FACETS["S14.3-001"],
                            src_block_data_initial_values(), "BLOCK DATA INITIAL VALUES OK\n", mutations=[
                                ("main selects alternate initialized common", "program block_data_initial_values_probe\n  implicit none\n  integer :: a, b\n  common /initial_blk/ a, b", "program block_data_initial_values_probe\n  implicit none\n  integer :: a, b\n  common /initial_alt_blk/ a, b"),
                            ]))
    cases.append(valid_case("C1414_valid__block_data_name_control", "C1414", ["end-block-data-name-requires-start-name", "matching-end-block-data-name", "mismatched-end-block-data-name-rejected"],
                            src_block_data_name_control(), compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1414_invalid__block_data_end_name_without_start_name", "C1414",
                              ["end-block-data-name-requires-start-name"], src_block_data_unnamed_end_invalid(), 5,
                              ["has no corresponding", "Syntax error", "Expecting END PROGRAM"],
                              "C1414_valid__block_data_name_control", lfortran_defect=True))
    cases.append(invalid_case("C1414_invalid__block_data_end_name_mismatch", "C1414",
                              ["mismatched-end-block-data-name-rejected"], src_block_data_mismatch_invalid(), 5,
                              ["Expected label", "names do not match", "Expecting END PROGRAM"],
                              "C1414_valid__block_data_name_control", lfortran_defect=True))
    cases.append(valid_case("C1416_valid__block_data_type_decl_control", "C1416", ["allocatable-attribute-forbidden-in-block-data-type-decl"],
                            src_block_data_alloc_control(), compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1416_invalid__block_data_allocatable_type_decl", "C1416",
                              ["allocatable-attribute-forbidden-in-block-data-type-decl"], src_block_data_alloc_invalid(), 2,
                              ["ALLOCATABLE", "not allowed", "cannot appear"],
                              "C1416_valid__block_data_type_decl_control", lfortran_defect=True))
    cases.append(valid_case("C1415_valid__block_data_intrinsic_control", "C1415", ["unlisted-specification-statement-rejected"],
                            src_block_data_external_control(), compile_only=True, evidence="positive-control"))
    cases.append(invalid_case("C1415_invalid__block_data_external_statement", "C1415",
                              ["unlisted-specification-statement-rejected"], src_block_data_external_invalid(), 2,
                              ["EXTERNAL", "not allowed", "Unexpected attribute"],
                              "C1415_valid__block_data_intrinsic_control", lfortran_defect=True))
    cases.append(valid_case("S14_3_002_valid__block_data_all_storage_specified", "S14.3-002", BLOCK_DATA_FACETS["S14.3-002"],
                            src_block_data_all_storage_specified(), "BLOCK DATA STORAGE SEQUENCE OK\n", evidence="positive-control", mutations=[
                                ("main selects alternate specified storage sequence", "program block_data_storage_sequence_probe\n  implicit none\n  integer :: a, b, c\n  common /storage_blk/ a, b, c", "program block_data_storage_sequence_probe\n  implicit none\n  integer :: a, b, c\n  common /storage_alt_blk/ a, b, c"),
                            ]))
    cases.append(valid_case("S14_3_003_valid__block_data_multiple_named_common", "S14.3-003", BLOCK_DATA_FACETS["S14.3-003"],
                            src_block_data_multiple_named_common(), "BLOCK DATA MULTIPLE NAMED OK\n", mutations=[
                                ("main selects alternate left common", "program block_data_multiple_named_probe\n  implicit none\n  integer :: left_value, right_value\n  common /multi_left_blk/ left_value", "program block_data_multiple_named_probe\n  implicit none\n  integer :: left_value, right_value\n  common /multi_left_alt_blk/ left_value"),
                                ("main selects alternate right common", "program block_data_multiple_named_probe\n  implicit none\n  integer :: left_value, right_value\n  common /multi_left_blk/ left_value\n  common /multi_right_blk/ right_value", "program block_data_multiple_named_probe\n  implicit none\n  integer :: left_value, right_value\n  common /multi_left_blk/ left_value\n  common /multi_right_alt_blk/ right_value"),
                            ]))
    cases.append(valid_case("S14_3_004_valid__block_data_initialized_object_named_common", "S14.3-004", BLOCK_DATA_FACETS["S14.3-004"],
                            src_block_data_initialized_object_named_common(), "BLOCK DATA NAMED OBJECT OK\n", evidence="positive-control", mutations=[
                                ("main selects alternate named common object", "program block_data_named_object_probe\n  implicit none\n  integer :: value\n  common /named_object_blk/ value", "program block_data_named_object_probe\n  implicit none\n  integer :: value\n  common /named_object_alt_blk/ value"),
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
    marker_begin = SUBMODULE_SUMMARY_BEGIN if section == SECTION_SUBMODULE else BLOCK_DATA_SUMMARY_BEGIN
    marker_end = SUBMODULE_SUMMARY_END if section == SECTION_SUBMODULE else BLOCK_DATA_SUMMARY_END
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
    sub = json.loads((root / SUBMODULE_CATALOGUE).read_text())
    block = json.loads((root / BLOCK_DATA_CATALOGUE).read_text())
    updated_sub = sync_catalogue(sub, SUBMODULE_FACETS, SUBMODULE_ORACLE_PREFIX, SUBMODULE_ORACLE,
                                 SUBMODULE_LIMIT_PREFIX, SUBMODULE_LIMITATION)
    updated_block = sync_catalogue(block, BLOCK_DATA_FACETS, BLOCK_DATA_ORACLE_PREFIX, BLOCK_DATA_ORACLE,
                                   BLOCK_DATA_LIMIT_PREFIX, BLOCK_DATA_LIMITATION)
    r1416 = next(row for row in updated_sub["requirements"] if row["id"] == "R1416")
    r1416["pending"]["minimal-submodule-form"] = (
        "PENDING not discharged: an empty minimal submodule has only source admission here; no distinct "
        "portable runtime assertion or conforming load-bearing feature mutant observes the minimal form.")
    for rule, facet in (
            ("S14.3-005", "named-common-block-single-block-data-owner"),
            ("S14.3-006", "single-unnamed-block-data-program-unit")):
        owner = next(row for row in updated_block["requirements"] if row["id"] == rule)
        owner["pending"][facet] = (
            "PENDING not discharged: this is an unnumbered program restriction with no required "
            "diagnostic obligation; a conforming positive program with distinct named or unnamed block "
            "data units is only a control and does not observe violation of the restriction.")
    sub_summary = (SUBMODULE_SUMMARY_BEGIN + "\n## Batch270 submodule fixtures\n\n" +
                   "Runtime fixtures exercise module-root and submodule-parent forms, host association from both "
                   "ancestor modules and parent submodules, separate module procedure implementations declared in "
                   "ancestors and descendants, duplicate submodule names under distinct ancestor modules, and the "
                   "R1416 specification and module-subprogram parts. Diagnostic fixtures cover malformed R1416 "
                   "ordering, a malformed SUBMODULE statement, a FORMAT statement in the submodule specification "
                   "part, and mismatched end names, each with a one-property compile-success control. The minimal "
                   "submodule form, optional END SUBMODULE forms, C1412, and the ENTRY/statement-function C1411 "
                   "variants remain pending.\n" +
                   SUBMODULE_SUMMARY_END)
    block_summary = (BLOCK_DATA_SUMMARY_BEGIN + "\n## Batch270 block data fixtures\n\n" +
                     "Runtime fixtures observe exact integer initialization of named COMMON blocks from BLOCK DATA, "
                     "including all-storage-units-specified source form, multiple named common blocks in one block "
                     "data unit, and an initialized object in a named common block. Diagnostic fixtures cover "
                     "C1414, C1415 and C1416 one-property invalids with controls; frozen LFortran currently accepts "
                     "those invalid block-data sources while gfortran diagnoses them. R1420/R1421/R1422 optional "
                     "forms, the declaration-only C1415 listed-statement census, and prose-only restrictions remain "
                     "pending.\n" + BLOCK_DATA_SUMMARY_END)
    return {
        SUBMODULE_CATALOGUE: json.dumps(updated_sub, indent=2) + "\n",
        BLOCK_DATA_CATALOGUE: json.dumps(updated_block, indent=2) + "\n",
        SUBMODULE_VIEW: render_view(updated_sub, SUBMODULE_VIEW, SECTION_SUBMODULE, sub_summary, root),
        BLOCK_DATA_VIEW: render_view(updated_block, BLOCK_DATA_VIEW, SECTION_BLOCK_DATA, block_summary, root),
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
            raise ValueError("stale submodule/block-data fixture family: " + ", ".join(stale))
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


def compiler_args(command, standard, source, output, compile_only=False):
    if compile_only:
        return [command, f"--std={standard}" if "lfortran" in Path(command).name else f"-std={standard}", "-c", source]
    return [command, f"--std={standard}" if "lfortran" in Path(command).name else f"-std={standard}", source, "-o", output]


def mutation_check(root, compiler, standard):
    root = Path(root)
    specs = generate(root, check=True)
    family = classify_compiler(compiler)
    work_root = Path(tempfile.mkdtemp(prefix=f"submodule-block-data-{family}-", dir=str(root.parent)))
    total = 0
    failures = []
    try:
        for spec in specs.values():
            if spec["kind"] != "valid" or spec.get("compile_only") or not spec.get("mutations"):
                continue
            for index, (label, old, new) in enumerate(spec["mutations"], 1):
                total += 1
                work = work_root / (spec["id"] + f"_{index}")
                work.mkdir()
                source = spec["source"]
                if source.count(old) != 1:
                    failures.append((spec["id"], label, "mutation token is not unique"))
                    continue
                mutated = source.replace(old, new)
                (work / "source.f90").write_text(mutated)
                exe = work / "program"
                compile_cmd = compiler_args(compiler, standard, "source.f90", "program")
                comp = subprocess.run(compile_cmd, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
                if comp.returncode != 0:
                    failures.append((spec["id"], label, "mutant did not compile: " + (comp.stderr + comp.stdout)[:400]))
                    continue
                run = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
                if run.returncode == 0 and run.stdout == spec["stdout"] and run.stderr == "":
                    failures.append((spec["id"], label, "mutant survived"))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} submodule/block-data cases ({invalid} invalid).")


if __name__ == "__main__":
    main()
