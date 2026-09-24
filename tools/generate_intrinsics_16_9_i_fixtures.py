#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.78-16.9.86 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_i"
SECTIONS = ("16.9.78", "16.9.79", "16.9.80", "16.9.81", "16.9.84", "16.9.85", "16.9.86")
CATALOGUES = {
    "16.9.78": "doc/catalogues/epsilon_16_9_78.json",
    "16.9.79": "doc/catalogues/erf_16_9_79.json",
    "16.9.80": "doc/catalogues/erfc_16_9_80.json",
    "16.9.81": "doc/catalogues/erfc_scaled_16_9_81.json",
    "16.9.84": "doc/catalogues/exp_16_9_84.json",
    "16.9.85": "doc/catalogues/exponent_16_9_85.json",
    "16.9.86": "doc/catalogues/extends_type_of_16_9_86.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.I FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.I FIXTURES -->"
RESTORED_PENDING = {
    "S16.9.86-003": {
        "extends-type-of-a-pointer-defined-association": (
            "PENDING after batch288 review: this is an unnumbered shall restriction that a polymorphic "
            "pointer A not have undefined association status; a positive control cannot discharge it and "
            "there is no required diagnostic for the forbidden undefined-status call."
        ),
    },
    "S16.9.86-004": {
        "extends-type-of-mold-pointer-defined-association": (
            "PENDING after batch288 review: this is an unnumbered shall restriction that a polymorphic "
            "pointer MOLD not have undefined association status; a positive control cannot discharge it "
            "and there is no required diagnostic for the forbidden undefined-status call."
        ),
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace('.', '_').replace('-', '_') + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Case:
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[tuple[str, str, str], ...]
    oracle: str
    profiles: tuple[str, ...] = ()

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.I " + self.variant.upper().replace("_", " ") + " OK\n"


REQUIRE_HELPERS = """contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
"""


def program(name: str, declarations: str, body: str, completion: str, use_lines: str = "") -> str:
    return f"""program i169i_{name}
{use_lines}  implicit none
{declarations}{body}  write(*,'(a)') '{completion.rstrip()}'
{REQUIRE_HELPERS}end program i169i_{name}
"""


def epsilon_arguments_source(completion):
    return program("epsilon_arguments", """  real :: scalar_x = 1.25
  real :: array_x(3) = [1.0, 2.0, 4.0]
""", """  call require_true('real scalar argument gives positive model epsilon', epsilon(scalar_x) > 0.0)
  call require_true('array argument still gives scalar result', rank(epsilon(array_x)) == 0)
""", completion)


def epsilon_characteristics_source(completion):
    return program("epsilon_characteristics", """  real :: array_x(2) = [1.0, 2.0]
  real(kind=kind(0.0d0)) :: double_x = 1.0d0
""", """  call require_true('epsilon array result is scalar', rank(epsilon(array_x)) == 0)
  call require_true('epsilon result has x kind', kind(epsilon(double_x)) == kind(double_x))
""", completion)


def epsilon_model_source(completion):
    return program("epsilon_model", """  real :: default_x = 1.0
  real(kind=kind(0.0d0)) :: double_x = 1.0d0
  real :: default_expected
  real(kind=kind(0.0d0)) :: double_expected
""", """  default_expected = real(radix(default_x), kind(default_x)) ** (1 - digits(default_x))
  double_expected = real(radix(double_x), kind(double_x)) ** (1 - digits(double_x))
  call require_true('epsilon default real model value', epsilon(default_x) == default_expected)
  call require_true('epsilon double real model value', epsilon(double_x) == double_expected)
""", completion)


def real_elemental_source(name, intrinsic, completion):
    upper = intrinsic.upper()
    return program(name, f"""  real :: xs(3) = [-0.5, 0.0, 0.5]
  real :: scalar_x = 0.25
  real(kind=kind(0.0d0)) :: double_x = 0.25d0
  real :: scalar_observed
  real(kind=kind(0.0d0)) :: double_observed
""", f"""  call require_true('{intrinsic} elemental preserves shape', all(shape({intrinsic}(xs)) == shape(xs)))
  scalar_observed = {intrinsic}(scalar_x)
  double_observed = {intrinsic}(double_x)
  call require_true('{intrinsic} accepts default real scalar', kind(scalar_observed) == kind(scalar_x))
  call require_true('{intrinsic} accepts double real scalar', kind(double_observed) == kind(double_x))
  call require_true('{intrinsic} result kind follows x expression', kind({intrinsic}(double_x)) == kind(double_x))
""", completion)


def exp_characteristics_source(completion):
    return program("exp_characteristics", """  real :: real_xs(3) = [-1.0, 0.0, 1.0]
  complex :: complex_xs(2) = [(0.0, 0.5), (1.0, -0.5)]
  real :: real_scalar = 0.25
  complex :: complex_scalar = (0.25, 0.5)
  real(kind=kind(0.0d0)) :: double_scalar = 0.25d0
  complex(kind=kind(0.0d0)) :: double_complex = (0.25d0, 0.5d0)
  real :: real_observed
  complex :: complex_observed
""", """  call require_true('exp elemental real array shape', all(shape(exp(real_xs)) == shape(real_xs)))
  call require_true('exp elemental complex array shape', all(shape(exp(complex_xs)) == shape(complex_xs)))
  real_observed = exp(real_scalar)
  complex_observed = exp(complex_scalar)
  call require_true('exp accepts real argument', kind(real_observed) == kind(real_scalar))
  call require_true('exp accepts complex argument', kind(complex_observed) == kind(complex_scalar))
  call require_true('exp real result kind follows x', kind(exp(double_scalar)) == kind(double_scalar))
  call require_true('exp complex result kind follows x', kind(exp(double_complex)) == kind(double_complex))
""", completion)


def exponent_characteristics_source(completion):
    return program("exponent_characteristics", """  real :: xs(3) = [0.0, 1.0, -1.0]
  integer, parameter :: description_power = 2
  integer, parameter :: argument_power = 3
  real :: real_x
  real :: real_y
""", """  real_x = real(radix(1.0), kind(1.0)) ** description_power
  real_y = real(radix(1.0), kind(1.0)) ** argument_power
  call require_true('exponent describes floating exponent value', &
       exponent(real_x) == description_power + 1)
  call require_true('exponent elemental shape', all(shape(exponent(xs)) == shape(xs)))
  call require_true('exponent accepts real x', exponent(real_y) == argument_power + 1)
""", completion)


def exponent_result_kind_source(completion):
    return program("exponent_result_kind", """  integer, parameter :: alt_int_kind = merge(8, 4, kind(0) /= 8)
  integer, parameter :: result_power = 2
  real :: result_x
""", """  result_x = real(radix(1.0), kind(1.0)) ** result_power
  call require_true('exponent result default integer', kind(exponent(result_x)) == kind(0))
""", completion)


def exponent_model_source(completion):
    return program("exponent_model", """  real :: default_x, default_power, negative_power
  real(kind=kind(0.0d0)) :: double_power
  integer, parameter :: default_power_k = 3
  integer, parameter :: double_power_k = 5
""", """  default_x = real(radix(1.0), kind(1.0)) ** 2
  default_power = real(radix(default_x), kind(default_x)) ** default_power_k
  negative_power = -default_power
  double_power = real(radix(0.0d0), kind(0.0d0)) ** double_power_k
  call require_true('exponent exact radix power model exponent', &
       exponent(default_power) == default_power_k + 1)
  call require_true('exponent negative value uses same exponent', exponent(negative_power) == exponent(default_power))
  call require_true('exponent double kind model relation', exponent(double_power) == double_power_k + 1)
""", completion)


def exponent_zero_source(completion):
    return program("exponent_zero", """  real :: zero = 0.0
  real :: negative_zero = -0.0
""", """  call require_true('exponent positive zero result zero', exponent(zero) == 0)
  call require_true('exponent negative zero result zero', exponent(negative_zero) == 0)
""", completion)


def exponent_ieee_source(completion):
    return program("exponent_ieee", """  real :: inf_value
  real :: nan_value
""", """  inf_value = ieee_value(0.0, ieee_positive_inf)
  nan_value = ieee_value(0.0, ieee_quiet_nan)
  call require_true('exponent ieee infinity huge result', exponent(inf_value) == huge(0))
  call require_true('exponent ieee nan huge result', exponent(nan_value) == huge(0))
""", completion, "  use ieee_arithmetic, only: ieee_value, ieee_positive_inf, ieee_quiet_nan\n")


def extends_relation_source(completion):
    return program("extends_type_relation", """  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type, extends(child) :: grandchild
    integer :: g = 3
  end type grandchild
  type, extends(parent) :: sibling
    integer :: s = 4
  end type sibling
  type(parent) :: p
  type(child) :: c
  type(grandchild) :: g
  type(sibling) :: s
  logical :: inquiry_result
""", """  call require_true('dynamic type extension inquiry child parent', extends_type_of(c, p))
  inquiry_result = .false.
  inquiry_result = extends_type_of(g, p)
  call require_true('inquiry function usable in logical expression', inquiry_result)
  call require_true('grandchild extends parent true iff', extends_type_of(g, p))
  call require_false('parent does not extend child true iff', extends_type_of(p, c))
  call require_false('sibling does not extend child true iff', extends_type_of(s, c))
""", completion)


def extends_arguments_source(completion):
    return program("extends_type_arguments", """  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type, extends(parent) :: sibling
    integer :: s = 3
  end type sibling
  type(parent) :: p
  type(child) :: c
  class(*), allocatable :: unlimited_a
  class(*), allocatable :: unlimited_mold
""", """  allocate(child :: unlimited_a)
  allocate(parent :: unlimited_mold)
  call require_true('a may be unlimited polymorphic allocated child', extends_type_of(unlimited_a, p))
  call require_true('mold may be unlimited polymorphic allocated parent', extends_type_of(c, unlimited_mold))
""", completion)


def extends_a_argument_source(completion):
    return program("extends_type_a_argument", """  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type(child) :: c
  class(*), allocatable :: unlimited_a
""", """  allocate(child :: unlimited_a)
  call require_true('a may be unlimited polymorphic allocated child', extends_type_of(unlimited_a, c))
""", completion)


def extends_characteristics_source(completion):
    return program("extends_type_characteristics", """  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  integer, parameter :: alt_logical_kind = merge(1, 4, kind(.false.) /= 1)
  type(parent) :: p
  type(child) :: c
""", """  call require_true('extends_type_of result default logical', &
       kind(extends_type_of(c, p)) == kind(.false.))
  call require_true('extends_type_of result logical value', &
       extends_type_of(c, p))
  call require_true('extends_type_of result scalar', rank(extends_type_of(c, p)) == 0)
""", completion)


def extends_unlimited_absent_source(completion):
    return program("extends_type_unlimited_absent", """  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type(parent) :: p
  class(*), allocatable :: mold_absent
  class(*), allocatable :: a_absent
  class(*), pointer :: a_pointer
""", """  nullify(a_pointer)
  call require_true('unallocated unlimited mold gives true', extends_type_of(p, mold_absent))
  call require_false('unallocated unlimited a gives false', extends_type_of(a_absent, p))
  call require_false('disassociated unlimited a pointer gives false', extends_type_of(a_pointer, p))
""", completion)


def make_cases():
    raw = []

    def add(variant, rule, facets, evidence, source_func, mutations, oracle, profiles=()):
        completion = "INTRINSICS 16.9.I " + variant.upper().replace("_", " ") + " OK\n"
        raw.append(Case(variant, rule, tuple(facets), evidence, source_func(completion), tuple(mutations), oracle, tuple(profiles)))

    add("epsilon_arguments", "S16.9.78-001", ["EPSILON-X-real", "EPSILON-X-scalar-or-array"], "positive-control", epsilon_arguments_source,
        [("real-argument-feature-negated", "epsilon(scalar_x) > 0.0", "(-epsilon(scalar_x)) > 0.0"),
         ("array-argument-wrapped", "rank(epsilon(array_x)) == 0", "rank([epsilon(array_x)]) == 0")],
        "EPSILON argument fixture calls EPSILON with real scalar and rank-one real array X and observes a positive model value plus scalar result rank.")
    add("epsilon_characteristics", "S16.9.78-002", ["EPSILON-result-scalar", "EPSILON-result-same-real-kind-as-X"], "effect", epsilon_characteristics_source,
        [("scalar-result-wrapped", "rank(epsilon(array_x)) == 0", "rank([epsilon(array_x)]) == 0"),
         ("kind-argument-demoted", "kind(epsilon(double_x)) == kind(double_x)", "kind(epsilon(real(double_x))) == kind(double_x)")],
        "EPSILON result-characteristics fixture inquires rank and kind directly on EPSILON expressions for array and double-real X.")
    add("epsilon_model", "S16.9.78-003", ["EPSILON-model-b-to-one-minus-p", "EPSILON-distinguishes-real-kinds"], "effect", epsilon_model_source,
        [("default-model-wrong-intrinsic", "epsilon(default_x) == default_expected", "tiny(default_x) == default_expected"),
         ("double-model-wrong-kind", "epsilon(double_x) == double_expected", "epsilon(real(double_x)) == double_expected")],
        "EPSILON model fixture computes b**(1-p) from RADIX and DIGITS of each X kind and compares with EPSILON(X).")

    add("erf_characteristics", "S16.9.79-002", ["erf-elemental-class"], "effect", lambda c: real_elemental_source("erf_characteristics", "erf", c),
        [("elemental-singleton", "shape(erf(xs))", "shape([erf(xs(1))])")],
        "ERF elemental fixture checks only the expression shape from applying ERF to a rank-one real array.")
    add("erf_arguments", "S16.9.79-003", ["erf-x-real"], "positive-control", lambda c: real_elemental_source("erf_arguments", "erf", c),
        [("double-call-demoted", "kind(erf(double_x)) == kind(double_x)", "kind(erf(real(double_x))) == kind(double_x)")],
        "ERF argument positive control calls ERF with default and double real scalar X without asserting an approximate value.")
    add("erf_result_characteristics", "S16.9.79-004", ["erf-result-same-as-x"], "effect", lambda c: real_elemental_source("erf_result_characteristics", "erf", c),
        [("result-kind-demoted", "kind(erf(double_x)) == kind(double_x)", "kind(erf(real(double_x))) == kind(double_x)")],
        "ERF result-characteristics fixture inquires KIND directly on ERF(double_x) and checks array shape separately from any approximate value.")

    add("erfc_characteristics", "S16.9.80-002", ["erfc-elemental-class"], "effect", lambda c: real_elemental_source("erfc_characteristics", "erfc", c),
        [("elemental-singleton", "shape(erfc(xs))", "shape([erfc(xs(1))])")],
        "ERFC elemental fixture checks only the expression shape from applying ERFC to a rank-one real array.")
    add("erfc_arguments", "S16.9.80-003", ["erfc-x-real"], "positive-control", lambda c: real_elemental_source("erfc_arguments", "erfc", c),
        [("double-call-demoted", "kind(erfc(double_x)) == kind(double_x)", "kind(erfc(real(double_x))) == kind(double_x)")],
        "ERFC argument positive control calls ERFC with default and double real scalar X without asserting an approximate value.")
    add("erfc_result_characteristics", "S16.9.80-004", ["erfc-result-same-as-x"], "effect", lambda c: real_elemental_source("erfc_result_characteristics", "erfc", c),
        [("result-kind-demoted", "kind(erfc(double_x)) == kind(double_x)", "kind(erfc(real(double_x))) == kind(double_x)")],
        "ERFC result-characteristics fixture inquires KIND directly on ERFC(double_x) and checks array shape separately from any approximate value.")

    add("erfc_scaled_characteristics", "S16.9.81-002", ["erfc-scaled-elemental-class"], "effect", lambda c: real_elemental_source("erfc_scaled_characteristics", "erfc_scaled", c),
        [("elemental-singleton", "shape(erfc_scaled(xs))", "shape([erfc_scaled(xs(1))])")],
        "ERFC_SCALED elemental fixture checks only the expression shape from applying ERFC_SCALED to a rank-one real array.")
    add("erfc_scaled_arguments", "S16.9.81-003", ["erfc-scaled-x-real"], "positive-control", lambda c: real_elemental_source("erfc_scaled_arguments", "erfc_scaled", c),
        [("double-call-demoted", "kind(erfc_scaled(double_x)) == kind(double_x)", "kind(erfc_scaled(real(double_x))) == kind(double_x)")],
        "ERFC_SCALED argument positive control calls ERFC_SCALED with default and double real scalar X without asserting an approximate value.")
    add("erfc_scaled_result_characteristics", "S16.9.81-004", ["erfc-scaled-result-same-as-x"], "effect", lambda c: real_elemental_source("erfc_scaled_result_characteristics", "erfc_scaled", c),
        [("result-kind-demoted", "kind(erfc_scaled(double_x)) == kind(double_x)", "kind(erfc_scaled(real(double_x))) == kind(double_x)")],
        "ERFC_SCALED result-characteristics fixture inquires KIND directly on ERFC_SCALED(double_x) and checks array shape separately from any approximate value.")

    add("exp_characteristics", "S16.9.84-002", ["exp-elemental-class"], "effect", exp_characteristics_source,
        [("real-elemental-singleton", "shape(exp(real_xs))", "shape([exp(real_xs(1))])")],
        "EXP elemental fixture checks expression shapes for real and complex rank-one arrays without comparing approximate exponential values.")
    add("exp_arguments", "S16.9.84-003", ["exp-x-real-or-complex"], "positive-control", exp_characteristics_source,
        [("complex-call-demoted", "kind(exp(double_complex)) == kind(double_complex)", "kind(exp(cmplx(real(double_complex), aimag(double_complex)))) == kind(double_complex)")],
        "EXP argument positive control calls EXP with real and complex scalar arguments and observes only type/kind-compatible completion.")
    add("exp_result_characteristics", "S16.9.84-004", ["exp-result-same-as-x"], "effect", exp_characteristics_source,
        [("double-result-demoted", "kind(exp(double_scalar)) == kind(double_scalar)", "kind(exp(real(double_scalar))) == kind(double_scalar)")],
        "EXP result-characteristics fixture inquires KIND directly on real and complex EXP expressions of the same kind as X.")

    add("exponent_characteristics", "S16.9.85-001", ["exponent-description"], "effect", exponent_characteristics_source,
        [("description-wrong-intrinsic", "exponent(real_x) == description_power + 1", "int(real_x) == description_power + 1")],
        "EXPONENT description fixture observes the exact model exponent of a radix-derived default-real power.")
    add("exponent_elemental", "S16.9.85-002", ["exponent-elemental-class"], "effect", exponent_characteristics_source,
        [("elemental-singleton", "shape(exponent(xs))", "shape([exponent(xs(1))])")],
        "EXPONENT elemental fixture applies EXPONENT to a rank-one real array and checks the expression shape.")
    add("exponent_arguments", "S16.9.85-003", ["exponent-x-real"], "positive-control", exponent_characteristics_source,
        [("x-real-wrong-intrinsic", "exponent(real_y) == argument_power + 1", "int(real_y) == argument_power + 1")],
        "EXPONENT argument positive control calls EXPONENT with a real X whose exact model exponent is known.")
    add("exponent_result_kind", "S16.9.85-004", ["exponent-result-default-integer"], "effect", exponent_result_kind_source,
        [("result-kind-changed-by-int-kind", "kind(exponent(result_x)) == kind(0)", "kind(int(result_x, kind=alt_int_kind)) == kind(0)")],
        "EXPONENT result-kind fixture inquires KIND directly on the EXPONENT expression and compares with default integer kind.",
        profiles=("integer-kinds-4-8",))
    add("exponent_model", "S16.9.85-005", ["exponent-nonzero-model-exponent", "exponent-negative-uses-value-exponent", "exponent-different-kinds"], "effect", exponent_model_source,
        [("model-wrong-intrinsic", "exponent(default_power) == default_power_k + 1", "int(default_power) == default_power_k + 1"),
         ("negative-exponent-shifted", "negative_power = -default_power", "negative_power = -default_power / real(radix(default_power), kind(default_power))"),
         ("double-kind-input-zeroed", "double_power = real(radix(0.0d0), kind(0.0d0)) ** double_power_k", "double_power = 0.0d0")],
        "EXPONENT model fixture uses exact powers of RADIX with expected exponents computed from each real kind's model.")
    add("exponent_zero", "S16.9.85-006", ["exponent-zero-result-zero"], "effect", exponent_zero_source,
        [("zero-changed-to-one", "exponent(zero) == 0", "exponent(1.0) == 0")],
        "EXPONENT zero fixture asserts the exact zero result for +0.0 and -0.0 real values.")
    add("exponent_ieee", "S16.9.85-007", ["exponent-ieee-infinity-huge", "exponent-ieee-nan-huge"], "effect", exponent_ieee_source,
        [("infinity-ordinary-value", "inf_value = ieee_value(0.0, ieee_positive_inf)", "inf_value = 1.0"),
         ("nan-ordinary-value", "nan_value = ieee_value(0.0, ieee_quiet_nan)", "nan_value = 1.0")],
        "EXPONENT IEEE fixture constructs IEEE infinity and quiet NaN and asserts the required HUGE(0) result under the ieee-binary profile.", profiles=("ieee-binary",))

    add("extends_type_relation", "S16.9.86-001", ["extends-type-of-dynamic-type-extension-inquiry"], "effect", extends_relation_source,
        [("relation-order-swapped", "extends_type_of(c, p)", "extends_type_of(p, c)")],
        "EXTENDS_TYPE_OF relation fixture observes child-parent and inverse dynamic type extension results.")
    add("extends_type_inquiry", "S16.9.86-002", ["extends-type-of-inquiry-function-class"], "effect", extends_relation_source,
        [("inquiry-order-swapped", "inquiry_result = extends_type_of(g, p)", "inquiry_result = extends_type_of(p, g)")],
        "EXTENDS_TYPE_OF inquiry fixture uses the intrinsic in a scalar logical expression whose exact result is checked.")
    add("extends_type_a_argument", "S16.9.86-003", ["extends-type-of-a-extensible-or-unlimited"], "positive-control", extends_a_argument_source,
        [("a-allocated-parent", "allocate(child :: unlimited_a)", "allocate(parent :: unlimited_a)")],
        "EXTENDS_TYPE_OF A-argument fixture passes an allocated unlimited-polymorphic A with an extensible dynamic type.")
    add("extends_type_mold_argument", "S16.9.86-004", ["extends-type-of-mold-extensible-or-unlimited"], "positive-control", extends_arguments_source,
        [("mold-allocated-sibling", "allocate(parent :: unlimited_mold)", "allocate(sibling :: unlimited_mold)")],
        "EXTENDS_TYPE_OF MOLD-argument fixture passes allocated unlimited-polymorphic A and MOLD objects with extensible dynamic types.")
    add("extends_type_characteristics", "S16.9.86-005", ["extends-type-of-default-logical-result", "extends-type-of-scalar-result"], "effect", extends_characteristics_source,
        [("default-logical-kind-converted", "kind(extends_type_of(c, p)) == kind(.false.)", "kind(logical(extends_type_of(c, p), kind=alt_logical_kind)) == kind(.false.)"),
         ("scalar-result-wrapped", "rank(extends_type_of(c, p)) == 0", "rank([extends_type_of(c, p)]) == 0")],
        "EXTENDS_TYPE_OF characteristics fixture inquires KIND and RANK directly on EXTENDS_TYPE_OF expressions.",
        profiles=("logical-kinds-1-4",))
    add("extends_type_unlimited_absent", "S16.9.86-006", ["extends-type-of-unlimited-mold-disassociated-or-unallocated-true", "extends-type-of-unlimited-a-disassociated-or-unallocated-false"], "effect", extends_unlimited_absent_source,
        [("mold-absent-allocated-child", "call require_true('unallocated unlimited mold gives true', extends_type_of(p, mold_absent))", "allocate(child :: mold_absent)\n  call require_true('unallocated unlimited mold gives true', extends_type_of(p, mold_absent))"),
         ("a-absent-allocated-child", "call require_false('unallocated unlimited a gives false', extends_type_of(a_absent, p))", "allocate(child :: a_absent)\n  call require_false('unallocated unlimited a gives false', extends_type_of(a_absent, p))"),
         ("a-pointer-allocated-child", "call require_false('disassociated unlimited a pointer gives false', extends_type_of(a_pointer, p))", "allocate(child :: a_pointer)\n  call require_false('disassociated unlimited a pointer gives false', extends_type_of(a_pointer, p))")],
        "EXTENDS_TYPE_OF unlimited-absent fixture checks true for unallocated unlimited-polymorphic MOLD and false for unallocated or disassociated unlimited-polymorphic A.")
    add("extends_type_extension_values", "S16.9.86-006", ["extends-type-of-extension-relation-true-iff"], "effect", extends_relation_source,
        [("grandchild-order-swapped", "call require_true('grandchild extends parent true iff', extends_type_of(g, p))", "call require_true('grandchild extends parent true iff', extends_type_of(p, g))"),
         ("parent-child-order-swapped", "call require_false('parent does not extend child true iff', extends_type_of(p, c))", "call require_false('parent does not extend child true iff', extends_type_of(c, p))"),
         ("sibling-child-parent-control", "call require_false('sibling does not extend child true iff', extends_type_of(s, c))", "call require_false('sibling does not extend child true iff', extends_type_of(c, p))")],
        "EXTENDS_TYPE_OF exact-value fixture checks true and false directions for parent, child, grandchild, and sibling extensible dynamic types.")
    return {identifier(case.rule, case.variant): case for case in raw}


def mutation_records(case: Case):
    records = []
    raw = case.source.encode("ascii")
    for mid, expected, replacement in case.mutations:
        count = case.source.count(expected)
        if count != 1:
            raise ValueError(f"{case.variant}:{mid} expected unique mutation text {expected!r}, saw {count}")
        start = case.source.index(expected)
        mutated = raw[:start] + replacement.encode("ascii") + raw[start + len(expected):]
        records.append(dict(id=mid, expected=expected, replacement=replacement,
                            span=[start, start + len(expected)], source_sha256=sha(mutated)))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for name, case in make_cases().items():
        raw = case.source.encode("ascii")
        mutations = mutation_records(case)
        spec = dict(id=name, variant=case.variant, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                    source=case.source, source_sha256=sha(raw), completion=case.completion, mutations=mutations,
                    oracle=case.oracle, profiles=list(case.profiles))
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case.variant)
        manifest = dict(schema_version=1, id=name, rule=case.rule, facets=list(case.facets), evidence=case.evidence,
                        standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0, stdout=case.completion, stderr=""))
        if case.profiles:
            manifest["profiles"] = list(case.profiles)
        spec["path"], spec["manifest"] = directory.relative_to(root).as_posix() + "/fixture.json", manifest
        specs[name] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, p in enumerate(paragraphs) if p.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def sync_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    covered = {}
    for spec in specs.values():
        covered.setdefault(spec["rule"], set()).update(spec["facets"])
    for rule, reasons in RESTORED_PENDING.items():
        if rule in by_rule:
            pending = by_rule[rule].setdefault("pending", {})
            for facet, reason in reasons.items():
                if facet not in covered.get(rule, set()):
                    pending.setdefault(facet, reason)
    for spec in specs.values():
        row = by_rule[spec["rule"]]
        if not set(spec["facets"]) <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + spec["rule"])
        for facet in spec["facets"]:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = spec["rule"] + " intrinsics_16_9_i fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + spec["oracle"])
        limit_prefix = spec["rule"] + " intrinsics_16_9_i boundaries: "
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), limit_prefix,
            limit_prefix + "This packet supplies the named run/effect or positive-control fixture only; it does not approve unrelated facets, diagnostics, source review, evidence links, baselines, coarray behavior, processor-dependent approximations, or compiler consensus oracles.")
    return result


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
    summary = (SUMMARY_BEGIN + "\n"
        "## Intrinsics 16.9.I runtime observations\n\n"
        "This batch adds source-derived runtime fixtures for EPSILON, ERF, ERFC, ERFC_SCALED, EXP, "
        "EXPONENT, and EXTENDS_TYPE_OF. Exact real-model assertions use RADIX, DIGITS, HUGE, and "
        "MAXEXPONENT of the same kind; approximate transcendental results are exercised only through "
        "argument, elemental, kind, and shape properties. Processor-dependent approximation and residual "
        "nonextensible EXTENDS_TYPE_OF facets remain pending.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        section_specs = {k: v for k, v in specs.items() if v["rule"].startswith("S" + section + "-")}
        updated = sync_catalogue(catalogue, section_specs)
        updated_catalogues[rel] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items() if not path.is_file() or path.read_bytes() != raw]
        for rel, updated in updated_catalogues.items():
            if json.loads((root / rel).read_text()) != updated:
                stale.append(rel)
        for rel, text in updated_views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise ValueError("stale intrinsics_16_9_i generated files: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogues:
            for rel, updated in updated_catalogues.items():
                (root / rel).write_text(json.dumps(updated, indent=2) + "\n")
            for rel, text in updated_views.items():
                (root / rel).write_text(text)
    return specs


def mutate_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source hash changed for " + spec["id"])
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span lost complete-parent binding")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def compile_and_run(workdir, compiler, std, source_bytes):
    source = workdir / "source.f90"
    exe = workdir / "program"
    source.write_bytes(source_bytes)
    cmd = [str(compiler)]
    if "lfortran" in Path(str(compiler)).name:
        cmd.append("--std=" + std)
    else:
        cmd.append("-std=" + std)
    cmd += ["source.f90", "-o", "program"]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if comp.returncode != 0:
        return "compile-fail", comp.stdout + comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if run.returncode == 0:
        return "pass", run.stdout + run.stderr
    return "run-fail", run.stdout + run.stderr


def check_mutations(root, compiler, std, skip_parent_failures=False):
    root = Path(root)
    specs = generate(root)
    workspace = root / ("." + TOPIC + "_mutation_runs") / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    failures, skipped, checked = [], [], 0
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, output = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"))
            if status != "pass":
                if skip_parent_failures:
                    skipped.append(spec["id"] + ":" + status + ":" + (output.splitlines()[0][:120] if output else ""))
                    continue
                failures.append(spec["id"] + " parent did not pass (" + status + "):\n" + output)
                continue
            for mutation in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mutation["id"])
                case_dir.mkdir()
                status, output = compile_and_run(case_dir, compiler, std, mutate_source(spec, mutation))
                if status == "compile-fail":
                    failures.append(spec["id"] + ":" + mutation["id"] + " failed to compile:\n" + output)
                elif status == "pass":
                    failures.append(spec["id"] + ":" + mutation["id"] + " survived")
        if failures:
            raise SystemExit("\n\n".join(failures))
        return checked, skipped
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--skip-parent-failures", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        checked, skipped = check_mutations(args.root, args.compiler, args.std, args.skip_parent_failures)
        print(f"Mutation-checked {checked} intrinsics_16_9_i mutations; {len(skipped)} parents skipped.")
        if skipped:
            print("Skipped parents:")
            for row in skipped:
                print("  " + row)
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_i cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} mutations.")


if __name__ == "__main__":
    main()
