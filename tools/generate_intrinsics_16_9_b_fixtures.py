#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.11-16.9.17."""

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
TOPIC = "intrinsics_16_9_b"
SECTIONS = ("16.9.11", "16.9.12", "16.9.13", "16.9.14", "16.9.15", "16.9.16", "16.9.17")
CATALOGUES = {
    "16.9.11": "doc/catalogues/aint_16_9_11.json",
    "16.9.12": "doc/catalogues/all_16_9_12.json",
    "16.9.13": "doc/catalogues/allocated_16_9_13.json",
    "16.9.14": "doc/catalogues/anint_16_9_14.json",
    "16.9.15": "doc/catalogues/any_intrinsic_16_9_15.json",
    "16.9.16": "doc/catalogues/asin_intrinsic_16_9_16.json",
    "16.9.17": "doc/catalogues/asind_intrinsic_16_9_17.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fail_block(token):
    return f"    write(*,'(a)') '{token}'\n    error stop\n"


def guard(variant, name, condition):
    token = f"I16B:{variant}:{name}"
    return f"  if ({condition}) then\n{fail_block(token)}  end if\n  checks=checks+1\n"


def finish_source(variant, body):
    checks = body.count("checks=checks+1")
    program = "intrinsics_16_9_b_" + variant
    completion = "INTRINSICS 16.9.B " + variant.upper().replace("_", " ") + " OK"
    return (
        f"program {program}\n"
        "  implicit none\n"
        "  integer :: checks\n"
        + body.replace("__CHECKS__", str(checks)) +
        f"  write(*,'(a)') '{completion}'\n"
        f"end program {program}\n"
    ), completion + "\n", checks


def make_case(section, rule, facets, variant, body, feature_expected, feature_replacement, derivation):
    source, completion, checks = finish_source(variant, body)
    return dict(
        section=section,
        rule=rule,
        evidence="positive-control" if rule.endswith("-003") else "effect",
        facets=list(facets),
        variant=variant,
        source=source,
        completion=completion,
        checks=checks,
        feature_expected=feature_expected,
        feature_replacement=feature_replacement,
        derivation=derivation,
    )


CASES = [
    make_case(
        "16.9.11", "S16.9.11-003", ["a-real-argument", "kind-scalar-integer-constant"],
        "aint_arguments",
        "  real(kind=kind(0.0d0)) :: high\n"
        "  real :: observed\n"
        "  checks=0\n"
        "  high = 2.5d0\n"
        "  observed = aint(2.5)\n"
        + guard("aint_arguments", "real-argument", "observed /= 2.0") +
        "  observed = aint(high, kind=kind(0.0))\n"
        + guard("aint_arguments", "constant-kind", "kind(aint(high, kind=kind(0.0))) /= kind(0.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:aint_arguments:check-total") + "  end select\n",
        "kind(aint(high, kind=kind(0.0)))", "kind(aint(high))",
        "p3 requires real A and scalar integer constant KIND; conforming calls with real A and constant KIND reach exact AINT effects."
    ),
    make_case(
        "16.9.11", "S16.9.11-004", ["result-real-type", "kind-present-selects-result-kind", "kind-absent-uses-a-kind"],
        "aint_result_kind",
        "  real(kind=kind(0.0d0)) :: high\n"
        "  real :: value\n"
        "  checks=0\n"
        "  high = 2.0d0\n"
        "  value = aint(2.5)\n"
        + guard("aint_result_kind", "real-result-value", "value /= 2.0") +
        guard("aint_result_kind", "kind-present", "kind(aint(high, kind=kind(0.0))) /= kind(0.0)") +
        guard("aint_result_kind", "kind-absent", "kind(aint(high)) /= kind(high)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:aint_result_kind:check-total") + "  end select\n",
        "kind(aint(high, kind=kind(0.0)))", "kind(aint(high))",
        "p4 fixes a real result; present KIND selects the requested kind and absent KIND preserves A's kind."
    ),
    make_case(
        "16.9.11", "S16.9.11-005", ["magnitude-less-than-one-gives-zero", "positive-truncates-toward-zero", "negative-truncates-toward-zero"],
        "aint_truncation_values",
        "  real :: below_one, positive, negative\n"
        "  checks=0\n"
        "  below_one = aint(0.5)\n"
        "  positive = aint(2.5)\n"
        "  negative = aint(-2.5)\n"
        + guard("aint_truncation_values", "below-one-zero", "below_one /= 0.0") +
        guard("aint_truncation_values", "positive-toward-zero", "positive /= 2.0") +
        guard("aint_truncation_values", "negative-toward-zero", "negative /= -2.0") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:aint_truncation_values:check-total") + "  end select\n",
        "positive = aint(2.5)", "positive = anint(2.5)",
        "p5 fixes zero for |A|<1 and truncation toward zero; 0.5 and 2.5 are exact test values."
    ),
    make_case(
        "16.9.12", "S16.9.12-003", ["mask-logical-array", "dim-integer-scalar", "dim-value-in-range"],
        "all_arguments",
        "  logical :: mask(2,3)\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  mask = reshape([.true., .true., .true., .false., .true., .true.], [2,3])\n"
        "  reduced = all(mask, dim=1)\n"
        + guard("all_arguments", "dim-one-values", "any(reduced .neqv. [.true., .false., .true.])") +
        "  reduced = all(mask, dim=2)\n"
        + guard("all_arguments", "dim-two-values", "any(reduced .neqv. [.true., .false.])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:all_arguments:check-total") + "  end select\n",
        "reduced = all(mask, dim=1)", "reduced = all(mask, dim=2)",
        "p3 requires a logical array MASK and scalar integer DIM in range; DIM=1 and DIM=2 are in range for rank-two MASK."
    ),
    make_case(
        "16.9.12", "S16.9.12-004", ["result-logical-same-kind", "dim-absent-scalar", "rank-one-dim-scalar", "dim-present-rank-and-shape"],
        "all_result_characteristics",
        "  logical :: mask2(2,3), vector(2), scalar_result\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  mask2 = reshape([.true., .true., .true., .false., .true., .true.], [2,3])\n"
        "  vector = [.true., .true.]\n"
        + guard("all_result_characteristics", "same-kind", "kind(all(vector)) /= kind(vector(1))") +
        "  scalar_result = all(mask2)\n"
        + guard("all_result_characteristics", "dim-absent-scalar", "scalar_result") +
        "  scalar_result = all(vector, dim=1)\n"
        + guard("all_result_characteristics", "rank-one-dim-scalar", ".not. scalar_result") +
        "  reduced = all(mask2, dim=1)\n"
        + guard("all_result_characteristics", "dim-shape", "any(shape(reduced) /= [3])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:all_result_characteristics:check-total") + "  end select\n",
        "reduced = all(mask2, dim=1)", "reduced = all(mask2, dim=2)",
        "p4 fixes logical result kind, scalar result without DIM or rank-one DIM, and DIM result shape with the DIM extent removed."
    ),
    make_case(
        "16.9.12", "S16.9.12-005", ["all-elements-true", "zero-size-true", "any-false-gives-false", "dim-section-reductions"],
        "all_result_values",
        "  logical :: all_true(2), has_false(3), empty(0), mask2(2,3)\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  all_true = [.true., .true.]\n"
        "  has_false = [.true., .false., .true.]\n"
        "  mask2 = reshape([.true., .true., .true., .false., .true., .true.], [2,3])\n"
        + guard("all_result_values", "all-true", ".not. all(all_true)") +
        guard("all_result_values", "zero-size-true", ".not. all(empty)") +
        guard("all_result_values", "false-element", "all(has_false)") +
        "  reduced = all(mask2, dim=1)\n"
        + guard("all_result_values", "dim-sections", "any(reduced .neqv. [.true., .false., .true.])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:all_result_values:check-total") + "  end select\n",
        "has_false = [.true., .false., .true.]", "has_false = [.true., .true., .true.]",
        "p5 fixes true for all true or zero size, false for any false, and DIM elements as slice reductions."
    ),
    make_case(
        "16.9.13", "S16.9.13-003", ["array-allocatable-argument", "scalar-allocatable-argument"],
        "allocated_arguments",
        "  integer, allocatable :: array(:), scalar\n"
        "  logical :: array_status, scalar_status\n"
        "  checks=0\n"
        "  allocate(array(2))\n"
        "  array_status = allocated(array)\n"
        "  scalar_status = allocated(scalar)\n"
        + guard("allocated_arguments", "array-argument", ".not. array_status") +
        guard("allocated_arguments", "scalar-argument", "scalar_status") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:allocated_arguments:check-total") + "  end select\n",
        "allocate(array(2))", "! allocate(array(2))",
        "p3 admits allocatable array and scalar arguments; the fixture observes both forms through ALLOCATED."
    ),
    make_case(
        "16.9.13", "S16.9.13-004", ["default-logical-result", "scalar-result"],
        "allocated_result_characteristics",
        "  integer, allocatable :: array(:)\n"
        "  logical :: status\n"
        "  checks=0\n"
        "  allocate(array(3))\n"
        "  status = allocated(array)\n"
        + guard("allocated_result_characteristics", "default-logical-kind", "kind(allocated(array)) /= kind(.false.)") +
        "  associate (scalar_probe => allocated(array))\n"
        + guard("allocated_result_characteristics", "scalar-rank", "rank(scalar_probe) /= 0").replace("\n", "\n  ") +
        "  end associate\n" +
        guard("allocated_result_characteristics", "scalar-result", ".not. status") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:allocated_result_characteristics:check-total") + "  end select\n",
        "status = allocated(array)", "status = .false.",
        "p4 fixes a default logical scalar result; assignment to a scalar and KIND inquiry observe both properties."
    ),
    make_case(
        "16.9.13", "S16.9.13-005", ["allocated-true", "unallocated-false"],
        "allocated_result_values",
        "  integer, allocatable :: array(:), scalar\n"
        "  logical :: array_status, scalar_status\n"
        "  checks=0\n"
        "  allocate(array(4))\n"
        "  array_status = allocated(array)\n"
        "  scalar_status = allocated(scalar)\n"
        + guard("allocated_result_values", "allocated-true", ".not. array_status") +
        guard("allocated_result_values", "unallocated-false", "scalar_status") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:allocated_result_values:check-total") + "  end select\n",
        "scalar_status = allocated(scalar)", "allocate(scalar)\n  scalar_status = allocated(scalar)",
        "p5 fixes true for allocated arguments and false for unallocated arguments."
    ),
    make_case(
        "16.9.14", "S16.9.14-003", ["a-real-argument", "kind-scalar-integer-constant"],
        "anint_arguments",
        "  real(kind=kind(0.0d0)) :: high\n"
        "  real :: observed\n"
        "  checks=0\n"
        "  high = 2.25d0\n"
        "  observed = anint(2.25)\n"
        + guard("anint_arguments", "real-argument", "observed /= 2.0") +
        "  observed = anint(high, kind=kind(0.0))\n"
        + guard("anint_arguments", "constant-kind", "kind(anint(high, kind=kind(0.0))) /= kind(0.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:anint_arguments:check-total") + "  end select\n",
        "kind(anint(high, kind=kind(0.0)))", "kind(anint(high, kind=kind(0.0d0)))",
        "p3 requires real A and scalar integer constant KIND; conforming real calls reach exact ANINT effects."
    ),
    make_case(
        "16.9.14", "S16.9.14-004", ["result-real-type", "kind-present-selects-result-kind", "kind-absent-uses-a-kind"],
        "anint_result_kind",
        "  real(kind=kind(0.0d0)) :: high\n"
        "  real :: value\n"
        "  checks=0\n"
        "  high = 2.0d0\n"
        "  value = anint(2.25)\n"
        + guard("anint_result_kind", "real-result-value", "value /= 2.0") +
        guard("anint_result_kind", "kind-present", "kind(anint(high, kind=kind(0.0))) /= kind(0.0)") +
        guard("anint_result_kind", "kind-absent", "kind(anint(high)) /= kind(high)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:anint_result_kind:check-total") + "  end select\n",
        "kind(anint(high, kind=kind(0.0)))", "kind(anint(high))",
        "p4 fixes a real result; present KIND selects the requested kind and absent KIND preserves A's kind."
    ),
    make_case(
        "16.9.14", "S16.9.14-005", ["nearest-positive", "nearest-negative", "tie-greater-magnitude-positive", "tie-greater-magnitude-negative"],
        "anint_nearest_values",
        "  real :: near_pos, near_neg, tie_pos, tie_neg\n"
        "  checks=0\n"
        "  near_pos = anint(2.25)\n"
        "  near_neg = anint(-2.25)\n"
        "  tie_pos = anint(2.5)\n"
        "  tie_neg = anint(-2.5)\n"
        + guard("anint_nearest_values", "nearest-positive", "near_pos /= 2.0") +
        guard("anint_nearest_values", "nearest-negative", "near_neg /= -2.0") +
        guard("anint_nearest_values", "tie-positive", "tie_pos /= 3.0") +
        guard("anint_nearest_values", "tie-negative", "tie_neg /= -3.0") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:anint_nearest_values:check-total") + "  end select\n",
        "tie_pos = anint(2.5)", "tie_pos = aint(2.5)",
        "p5 fixes nearest integer and greater magnitude for exact half-way ties; 2.25 and 2.5 are exact test values."
    ),
    make_case(
        "16.9.15", "S16.9.15-001", ["any-logical-or-reduction"],
        "any_or_reduction",
        "  logical :: mask(3), observed, explicit_or\n"
        "  checks=0\n"
        "  mask = [.false., .true., .false.]\n"
        "  observed = any(mask)\n"
        "  explicit_or = mask(1) .or. mask(2) .or. mask(3)\n"
        + guard("any_or_reduction", "or-reduction", "observed .neqv. explicit_or") +
        guard("any_or_reduction", "true-result", ".not. observed") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:any_or_reduction:check-total") + "  end select\n",
        "observed = any(mask)", "observed = all(mask)",
        "p1 defines ANY as .OR. reduction of a logical array; the explicit .OR. chain has the same true value."
    ),
    make_case(
        "16.9.15", "S16.9.15-002", ["any-transformational-function-class"],
        "any_transformational_class",
        "  logical :: mask(2,3), scalar_result\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  mask = reshape([.false., .false., .true., .false., .false., .true.], [2,3])\n"
        "  scalar_result = any(mask)\n"
        "  reduced = any(mask, dim=1)\n"
        + guard("any_transformational_class", "scalar-transform", ".not. scalar_result") +
        guard("any_transformational_class", "rank-reduced-transform", "any(shape(reduced) /= [3])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:any_transformational_class:check-total") + "  end select\n",
        "reduced = any(mask, dim=1)", "reduced = any(mask, dim=2)",
        "p2 classifies ANY as transformational; rank-two input can produce a scalar or a rank-reduced array."
    ),
    make_case(
        "16.9.15", "S16.9.15-003", ["any-mask-logical-array", "any-dim-integer-scalar-in-rank-range"],
        "any_arguments",
        "  logical :: mask(2,3)\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  mask = reshape([.false., .false., .true., .false., .false., .true.], [2,3])\n"
        "  reduced = any(mask, dim=1)\n"
        + guard("any_arguments", "dim-one-values", "any(reduced .neqv. [.false., .true., .true.])") +
        "  reduced = any(mask, dim=2)\n"
        + guard("any_arguments", "dim-two-values", "any(reduced .neqv. [.true., .true.])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:any_arguments:check-total") + "  end select\n",
        "reduced = any(mask, dim=1)", "reduced = any(mask, dim=2)",
        "p3 requires a logical array MASK and scalar integer DIM in range; DIM=1 and DIM=2 are in range for rank-two MASK."
    ),
    make_case(
        "16.9.15", "S16.9.15-004", ["any-result-logical-same-kind", "any-result-scalar-without-dim-or-rank-one", "any-result-dim-rank-and-shape"],
        "any_result_characteristics",
        "  logical :: mask2(2,3), vector(2), scalar_result\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  mask2 = reshape([.false., .false., .true., .false., .false., .true.], [2,3])\n"
        "  vector = [.false., .true.]\n"
        + guard("any_result_characteristics", "same-kind", "kind(any(vector)) /= kind(vector(1))") +
        "  scalar_result = any(mask2)\n"
        + guard("any_result_characteristics", "dim-absent-scalar", ".not. scalar_result") +
        "  scalar_result = any(vector, dim=1)\n"
        + guard("any_result_characteristics", "rank-one-dim-scalar", ".not. scalar_result") +
        "  reduced = any(mask2, dim=1)\n"
        + guard("any_result_characteristics", "dim-shape", "any(shape(reduced) /= [3])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:any_result_characteristics:check-total") + "  end select\n",
        "reduced = any(mask2, dim=1)", "reduced = any(mask2, dim=2)",
        "p4 fixes logical result kind, scalar result without DIM or rank-one DIM, and DIM result shape with the DIM extent removed."
    ),
    make_case(
        "16.9.15", "S16.9.15-005", ["any-true-if-any-element-true", "any-false-if-no-elements-true", "any-false-for-zero-size-mask", "any-dim-result-equals-slice-reductions"],
        "any_result_values",
        "  logical :: has_true(3), all_false(3), empty(0), mask2(2,3)\n"
        "  logical, allocatable :: reduced(:)\n"
        "  checks=0\n"
        "  has_true = [.false., .true., .false.]\n"
        "  all_false = [.false., .false., .false.]\n"
        "  mask2 = reshape([.false., .false., .true., .false., .false., .true.], [2,3])\n"
        + guard("any_result_values", "any-true", ".not. any(has_true)") +
        guard("any_result_values", "none-true-false", "any(all_false)") +
        guard("any_result_values", "zero-size-false", "any(empty)") +
        "  reduced = any(mask2, dim=1)\n"
        + guard("any_result_values", "dim-sections", "any(reduced .neqv. [.false., .true., .true.])") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:any_result_values:check-total") + "  end select\n",
        "has_true = [.false., .true., .false.]", "has_true = [.false., .false., .false.]",
        "p5 fixes true for any true element, false when none are true or size is zero, and DIM elements as slice reductions."
    ),
    make_case(
        "16.9.16", "S16.9.16-001", ["asin-operation-description"],
        "asin_operation",
        "  real :: inputs(3), values(3)\n"
        "  checks=0\n"
        "  inputs = [-1.0, 0.0, 1.0]\n"
        "  values = asin(inputs)\n"
        + guard("asin_operation", "bounded-operation", "any(values < -2.0) .or. any(values > 2.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asin_operation:check-total") + "  end select\n",
        "values = asin(inputs)", "values = 10.0 * asin(inputs)",
        "p1 defines ASIN as arcsine; p5 fixes only bounded radian results for real values, not an exact approximation."
    ),
    make_case(
        "16.9.16", "S16.9.16-002", ["asin-elemental-function-class"],
        "asin_elemental_class",
        "  real :: inputs(3), values(3)\n"
        "  checks=0\n"
        "  inputs = [-1.0, 0.0, 1.0]\n"
        "  values = asin(inputs)\n"
        + guard("asin_elemental_class", "shape-preserved", "any(shape(values) /= [3])") +
        guard("asin_elemental_class", "position-signs", "values(1) >= 0.0 .or. values(3) <= 0.0") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asin_elemental_class:check-total") + "  end select\n",
        "values = asin(inputs)", "values = asin(inputs(2))",
        "p2 classifies ASIN as elemental; array input yields corresponding array elements."
    ),
    make_case(
        "16.9.16", "S16.9.16-003", ["asin-argument-restrictions"],
        "asin_arguments",
        "  real :: real_values(3)\n"
        "  complex :: z, z_value\n"
        "  checks=0\n"
        "  real_values = asin([-1.0, 0.0, 1.0])\n"
        "  z = (0.5, 0.75)\n"
        "  z_value = asin(z)\n"
        + guard("asin_arguments", "real-boundary-arguments", "any(real_values < -2.0) .or. any(real_values > 2.0)") +
        guard("asin_arguments", "complex-argument", "real(z_value) < -2.0 .or. real(z_value) > 2.0") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asin_arguments:check-total") + "  end select\n",
        "z_value = asin(z)", "z_value = (10.0, 0.0) * asin(z)",
        "p3 permits real values with |X|<=1 and complex X; this fixture uses both conforming forms."
    ),
    make_case(
        "16.9.16", "S16.9.16-004", ["asin-result-same-as-x"],
        "asin_result_characteristics",
        "  real(kind=kind(0.0d0)) :: high_inputs(2)\n"
        "  complex :: z\n"
        "  checks=0\n"
        "  high_inputs = [-1.0d0, 1.0d0]\n"
        "  z = (0.5, 0.75)\n"
        + guard("asin_result_characteristics", "real-kind", "kind(asin(high_inputs(1))) /= kind(high_inputs(1))") +
        guard("asin_result_characteristics", "real-size", "size(asin(high_inputs)) /= 2") +
        guard("asin_result_characteristics", "complex-kind", "kind(asin(z)) /= kind(z)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asin_result_characteristics:check-total") + "  end select\n",
        "size(asin(high_inputs))", "size([asin(high_inputs(1))])",
        "p4 fixes result characteristics as same as X; kind and array shape are checked without exact approximation."
    ),
    make_case(
        "16.9.16", "S16.9.16-006", ["asin-real-result-radians", "asin-real-result-range"],
        "asin_real_range",
        "  real :: inputs(3), values(3)\n"
        "  checks=0\n"
        "  inputs = [-1.0, 0.0, 1.0]\n"
        "  values = asin(inputs)\n"
        + guard("asin_real_range", "radian-lower-bound", "any(values < -2.0)") +
        guard("asin_real_range", "radian-upper-bound", "any(values > 2.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asin_real_range:check-total") + "  end select\n",
        "values = asin(inputs)", "values = 10.0 * asin(inputs)",
        "p5 fixes real ASIN in radians within -pi/2..pi/2; the exact wider [-2,2] bound is portable."
    ),
    make_case(
        "16.9.16", "S16.9.16-007", ["asin-complex-real-part-radians", "asin-complex-real-part-range"],
        "asin_complex_range",
        "  complex :: z, z_value\n"
        "  real :: part\n"
        "  checks=0\n"
        "  z = (0.5, 0.75)\n"
        "  z_value = asin(z)\n"
        "  part = real(z_value)\n"
        + guard("asin_complex_range", "complex-real-lower", "part < -2.0") +
        guard("asin_complex_range", "complex-real-upper", "part > 2.0") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asin_complex_range:check-total") + "  end select\n",
        "z_value = asin(z)", "z_value = (10.0, 0.0) * asin(z)",
        "p5 fixes the real part of complex ASIN in radians within -pi/2..pi/2."
    ),
    make_case(
        "16.9.17", "S16.9.17-001", ["asind-operation-description"],
        "asind_operation",
        "  real :: inputs(3), values(3)\n"
        "  checks=0\n"
        "  inputs = [-1.0, 0.0, 1.0]\n"
        "  values = asind(inputs)\n"
        + guard("asind_operation", "degree-operation-range", "any(values < -90.0) .or. any(values > 90.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asind_operation:check-total") + "  end select\n",
        "values = asind(inputs)", "values = 2.0 * asind(inputs)",
        "p1 defines ASIND as arc sine in degrees; p5 fixes only degree range, not exact approximation."
    ),
    make_case(
        "16.9.17", "S16.9.17-002", ["asind-elemental-function-class"],
        "asind_elemental_class",
        "  real :: inputs(3), values(3)\n"
        "  checks=0\n"
        "  inputs = [-1.0, 0.0, 1.0]\n"
        "  values = asind(inputs)\n"
        + guard("asind_elemental_class", "shape-preserved", "any(shape(values) /= [3])") +
        guard("asind_elemental_class", "position-signs", "values(1) >= 0.0 .or. values(3) <= 0.0") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asind_elemental_class:check-total") + "  end select\n",
        "values = asind(inputs)", "values = asind(inputs(2))",
        "p2 classifies ASIND as elemental; array input yields corresponding array elements."
    ),
    make_case(
        "16.9.17", "S16.9.17-003", ["asind-argument-restrictions"],
        "asind_arguments",
        "  real :: values(3)\n"
        "  checks=0\n"
        "  values = asind([-1.0, 0.0, 1.0])\n"
        + guard("asind_arguments", "real-boundary-arguments", "any(values < -90.0) .or. any(values > 90.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asind_arguments:check-total") + "  end select\n",
        "values = asind([-1.0, 0.0, 1.0])", "values = 2.0 * asind([-1.0, 0.0, 1.0])",
        "p3 permits real X with |X|<=1; the fixture uses both boundary values and zero."
    ),
    make_case(
        "16.9.17", "S16.9.17-004", ["asind-result-same-as-x"],
        "asind_result_characteristics",
        "  real(kind=kind(0.0d0)) :: high_inputs(2)\n"
        "  checks=0\n"
        "  high_inputs = [-1.0d0, 1.0d0]\n"
        + guard("asind_result_characteristics", "real-kind", "kind(asind(high_inputs(1))) /= kind(high_inputs(1))") +
        guard("asind_result_characteristics", "real-size", "size(asind(high_inputs)) /= 2") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asind_result_characteristics:check-total") + "  end select\n",
        "size(asind(high_inputs))", "size([asind(high_inputs(1))])",
        "p4 fixes result characteristics as same as X; kind and array shape are checked without exact approximation."
    ),
    make_case(
        "16.9.17", "S16.9.17-006", ["asind-result-degrees", "asind-result-range"],
        "asind_degree_range",
        "  real :: inputs(3), values(3)\n"
        "  checks=0\n"
        "  inputs = [-1.0, 0.0, 1.0]\n"
        "  values = asind(inputs)\n"
        + guard("asind_degree_range", "degree-lower-bound", "any(values < -90.0)") +
        guard("asind_degree_range", "degree-upper-bound", "any(values > 90.0)") +
        "  select case (checks)\n  case (__CHECKS__)\n  case default\n" + fail_block("I16B:asind_degree_range:check-total") + "  end select\n",
        "values = asind(inputs)", "values = 2.0 * asind(inputs)",
        "p5 fixes ASIND results as degrees in the closed range -90..90; no exact approximation is asserted."
    ),
]

ORIGINAL_PENDING_JSON = '{\n  "S16.9.11-003": {\n    "a-real-argument": "Future source-control plan only: compile conforming calls AINT(2.5) and AINT(-2.5) as positive controls; do not require a diagnostic for a nonreal A because this is an unnumbered Clause 16 program restriction.",\n    "kind-scalar-integer-constant": "Future source-control plan only: compile a conforming call AINT(2.5, KIND=KIND(0.0)) as the positive control; do not require a diagnostic for a nonconstant KIND because this is an unnumbered Clause 16 program restriction."\n  },\n  "S16.9.11-004": {\n    "kind-absent-uses-a-kind": "Call AINT(2.0) without KIND and assert KIND(result)==KIND(2.0) plus exact value 2.0; the default real argument kind gives a portable absent-KIND oracle.",\n    "kind-present-selects-result-kind": "Call AINT(2.0, KIND=KIND(0.0)) and assert KIND(result)==KIND(0.0) plus exact value 2.0; KIND is present and the selected default real kind is portable.",\n    "result-real-type": "Assign AINT(2.5) to a real initialized to -777.0 and assert exact value 2.0; the declared real target and exact whole-number result avoid a default-state oracle."\n  },\n  "S16.9.11-005": {\n    "magnitude-less-than-one-gives-zero": "Initialize a real result to 777.0 and assign AINT(0.0); assert exact result 0.0, then mutate the input to 1.0 in the fixture matrix to make the less-than-one case load-bearing without depending on fractional representation.",\n    "negative-truncates-toward-zero": "Use A = -2.0 - 1.0 / REAL(RADIX(1.0)) so A is less than -2 and greater than or equal to -2.5 in the processor real model; initialize result to 777.0 and assert AINT(A)==-2.0. Mutate to ANINT to distinguish truncation from nearest rounding when the mutation changes the result.",\n    "positive-truncates-toward-zero": "Use A = 2.0 + 1.0 / REAL(RADIX(1.0)) so A is greater than 2 and less than or equal to 2.5 in the processor real model; initialize result to -777.0 and assert AINT(A)==2.0. Mutate to ANINT to distinguish truncation from nearest rounding when the mutation changes the result."\n  },\n  "S16.9.12-003": {\n    "dim-integer-scalar": "Future source-control plan only: compile a conforming call with scalar DIM=1 as the positive control; do not require a diagnostic for nonscalar or noninteger DIM because this is an unnumbered Clause 16 program restriction.",\n    "dim-value-in-range": "Use only DIM values probed from RANK(MASK) in future positive fixtures; out-of-range DIM rejection is not recorded as a diagnostic facet because this is an unnumbered Clause 16 program restriction.",\n    "mask-logical-array": "Future source-control plan only: compile conforming calls ALL([.true., .false.]) and ALL(RESHAPE([.true.,.false.,.true.,.true.],[2,2]), DIM=1) as positive controls; do not require a diagnostic for nonlogical MASK because this is an unnumbered Clause 16 program restriction."\n  },\n  "S16.9.12-004": {\n    "dim-absent-scalar": "Initialize a scalar logical result to .true., evaluate ALL(RESHAPE([.true.,.false.,.true.,.true.],[2,2])) without DIM, and assert the scalar result is .false.; the companion DIM=1 expression over the same rank-2 MASK has rank one with exact expected values [.false., .true.], so DIM=1 genuinely exercises the rank-reduction case rather than the n=1 scalar rule.",\n    "dim-present-rank-and-shape": "For a 2x3 logical array with DIM=1, assert SHAPE(result)==[3] and exact values from column reductions; mutate DIM to 2 to prove the removed extent and values are load-bearing.",\n    "rank-one-dim-scalar": "Evaluate ALL([.true.,.true.], DIM=1) into a scalar initialized to .false. and assert .true.; this distinguishes the rank-one DIM case from higher-rank DIM reductions.",\n    "result-logical-same-kind": "Use a default logical array [.true., .true.] and assert KIND(ALL(mask))==KIND(mask) together with a scalar .true. value initialized from .false.; this default-kind equality is a portable oracle for the required same-kind property."\n  },\n  "S16.9.12-005": {\n    "all-elements-true": "Evaluate ALL([.true.,.true.]) into a logical initialized to .false. and assert .true.; mutate one element to .false. to make the all-true case load-bearing.",\n    "any-false-gives-false": "Initialize result to .true., evaluate ALL([.true.,.false.,.true.]), and assert .false.; mutate the false element to true to prove the negative observation is load-bearing.",\n    "dim-section-reductions": "Use a 2x3 mask with mixed columns and evaluate DIM=1; initialize the rank-one result to the opposite logical vector and assert exact column-wise conjunction values.",\n    "zero-size-true": "Use a zero-size logical array produced by a zero upper bound and initialize the scalar result to .false.; assert ALL(mask) is .true. without relying on a default .true. initialization. Pair it with a nonempty one-false companion mask, initialized from .true. and expected to yield .false., to prove the zero-size true result is non-vacuous."\n  },\n  "S16.9.13-003": {\n    "array-allocatable-argument": "Future source-control plan only: compile a conforming allocatable array argument before and after ALLOCATE as the positive control; do not require a diagnostic for a nonallocatable array because this is an unnumbered Clause 16 program restriction.",\n    "scalar-allocatable-argument": "Future source-control plan only: compile a conforming allocatable scalar argument before and after ALLOCATE as the positive control; do not require a diagnostic for a nonallocatable scalar because this is an unnumbered Clause 16 program restriction."\n  },\n  "S16.9.13-004": {\n    "default-logical-result": "Evaluate ALLOCATED on an allocatable scalar with a result variable initialized to the opposite logical value; assert KIND(result)==KIND(.false.) and the expected allocation status.",\n    "scalar-result": "Evaluate ALLOCATED on an allocatable array and assign to a scalar logical initialized to the opposite value; assert scalar assignment succeeds and the value matches allocation status."\n  },\n  "S16.9.13-005": {\n    "allocated-true": "Declare an allocatable integer array, allocate it to a nonzero size, initialize a logical result to .false., then assert ALLOCATED(array) is .true.; mutation removes ALLOCATE to make the status observation load-bearing.",\n    "unallocated-false": "Declare an allocatable scalar and leave it unallocated after explicitly setting a logical result to .true.; assert ALLOCATED(scalar) is .false.; mutation adds ALLOCATE to make the unallocated observation load-bearing."\n  },\n  "S16.9.14-003": {\n    "a-real-argument": "Future source-control plan only: compile conforming calls ANINT(2.5) and ANINT(-2.5) as positive controls; do not require a diagnostic for nonreal A because this is an unnumbered Clause 16 program restriction.",\n    "kind-scalar-integer-constant": "Future source-control plan only: compile a conforming call ANINT(2.5, KIND=KIND(0.0)) as the positive control; do not require a diagnostic for nonconstant KIND because this is an unnumbered Clause 16 program restriction."\n  },\n  "S16.9.14-004": {\n    "kind-absent-uses-a-kind": "Call ANINT(2.0) without KIND and assert KIND(result)==KIND(2.0) plus exact value 2.0; the default real argument kind gives a portable absent-KIND oracle.",\n    "kind-present-selects-result-kind": "Call ANINT(2.0, KIND=KIND(0.0)) and assert KIND(result)==KIND(0.0) plus exact value 2.0; KIND is present and the selected default real kind is portable.",\n    "result-real-type": "Assign ANINT(2.25) to a real initialized to -777.0 and assert exact value 2.0; the declared real target and exact whole-number result avoid a default-state oracle."\n  },\n  "S16.9.14-005": {\n    "nearest-negative": "Use A = -2.0 - 1.0 / REAL(RADIX(1.0)**2), which is closer to -2 than to -3 for any permitted radix; initialize result to 777.0 and assert ANINT(A)==-2.0 exactly. Also use B = -3.0 + 1.0 / REAL(RADIX(1.0)**2) and assert ANINT(B)==-3.0 exactly.",\n    "nearest-positive": "Use A = 2.0 + 1.0 / REAL(RADIX(1.0)**2), which is closer to 2 than to 3 for any permitted radix; initialize result to -777.0 and assert ANINT(A)==2.0 exactly. Also use B = 3.0 - 1.0 / REAL(RADIX(1.0)**2) and assert ANINT(B)==3.0 exactly.",\n    "tie-greater-magnitude-negative": "Guard the tie case by first computing H = 0.5 and verifying -2.0 - H + 2.0 equals -H and -2.0 - H is distinct from -2.0 and -3.0; only when that probe succeeds, initialize result to 777.0 and assert ANINT(-2.0 - H)==-3.0. If the probe fails, do not claim this tie facet for that processor.",\n    "tie-greater-magnitude-positive": "Guard the tie case by first computing H = 0.5 and verifying 2.0 + H - 2.0 equals H and 2.0 + H is distinct from 2.0 and 3.0; only when that probe succeeds, initialize result to -777.0 and assert ANINT(2.0 + H)==3.0. If the probe fails, do not claim this tie facet for that processor."\n  },\n  "S16.9.15-001": {\n    "any-logical-or-reduction": "Use a future logical array initialized with both .false. and .true. elements; compare ANY(MASK) with an explicit .OR. reduction over the same nonempty data so replacing ANY with ALL or COUNT changes the result."\n  },\n  "S16.9.15-002": {\n    "any-transformational-function-class": "Use a rank-two MASK with DIM present and absent; assert scalar reduction without DIM and rank-reduced result with DIM, demonstrating array transformation rather than elementwise mapping."\n  },\n  "S16.9.15-003": {\n    "any-dim-integer-scalar-in-rank-range": "Use DIM=1 and DIM=2 on a rank-two MASK and assert the required shapes and values; out-of-range DIM probes remain source-control only because this unnumbered restriction carries no required diagnostic.",\n    "any-mask-logical-array": "Use conforming logical arrays of rank one and two initialized to nondefault truth patterns; wrong-type MASK probes remain source-control only because this unnumbered restriction carries no required diagnostic."\n  },\n  "S16.9.15-004": {\n    "any-result-dim-rank-and-shape": "For a 2 by 3 MASK, prefill an expected rank-one result with the opposite truth pattern, evaluate ANY(MASK,DIM=1) and ANY(MASK,DIM=2), and assert exact extents [3] and [2].",\n    "any-result-logical-same-kind": "Declare a default-kind logical MASK and check KIND(ANY(MASK)) equals KIND(MASK); this observes the required same-kind relationship without depending on optional nondefault logical kinds.",\n    "any-result-scalar-without-dim-or-rank-one": "Initialize rank-one and rank-two masks with nonuniform values and assert ANY(MASK) is scalar by assignment to a scalar logical sentinel that changes to the expected truth value."\n  },\n  "S16.9.15-005": {\n    "any-dim-result-equals-slice-reductions": "Use a rank-two MASK whose rows and columns have distinct truth reductions; prefill result arrays with the opposite pattern and assert exact DIM=1 and DIM=2 vectors.",\n    "any-false-for-zero-size-mask": "Use a zero-size logical array and initialize the observed scalar to .true.; assert ANY changes it to .false., proving the empty case rather than relying on default initialization.",\n    "any-false-if-no-elements-true": "Use a nonempty all-false MASK and initialize the observed result to .true.; assert it changes to .false., avoiding default false vacuity.",\n    "any-true-if-any-element-true": "Use a logical array initialized [.false., .true., .false.] and assert the result changes a .false. sentinel to .true.; a mutant replacing ANY by ALL must fail."\n  },\n  "S16.9.16-001": {\n    "asin-operation-description": "Use a future source-derived fixture that calls ASIN with conforming exact inputs and observes only the result properties registered for this section, not an unrelated intrinsic."\n  },\n  "S16.9.16-002": {\n    "asin-elemental-function-class": "Apply ASIN to a rank-one array with at least two distinct elements and assert the result array has corresponding element positions; a scalar-only replacement would fail."\n  },\n  "S16.9.16-003": {\n    "asin-argument-restrictions": "Use conforming arguments at representative interior and boundary values; nonconforming type or value probes remain source-control only because these unnumbered restrictions carry no required diagnostic."\n  },\n  "S16.9.16-004": {\n    "asin-result-same-as-x": "Evaluate ASIN for scalar and rank-one arguments of a selected real kind, and for complex where allowed; assign to same-kind result variables and assert KIND and shape without comparing approximate numerical equality."\n  },\n  "S16.9.16-005": {\n    "asin-processor-dependent-approximation": "No portable exact-value oracle exists for the approximation; future fixtures must not compare ASIN results with the approximate example or a hard-coded decimal value."\n  },\n  "S16.9.16-006": {\n    "asin-real-result-radians": "Use real inputs -1.0, 0.0, and 1.0 and assert only that the result is a real radian measure through the registered range bound check, not an exact decimal.",\n    "asin-real-result-range": "For real inputs -1.0, 0.0, and 1.0, assert the result is within the required closed interval using a registered pi/range helper; mutate by replacing ASIN with ASINH or scaling the bound."\n  },\n  "S16.9.16-007": {\n    "asin-complex-real-part-radians": "Use complex inputs with nonzero imaginary components and check only the real-part range in radians after initializing the observed real component to an out-of-range sentinel.",\n    "asin-complex-real-part-range": "For representative complex X values, assert REAL(ASIN(X)) lies in the required closed interval; do not assert the imaginary component approximation."\n  },\n  "S16.9.17-001": {\n    "asind-operation-description": "Use a future source-derived fixture that calls ASIND with conforming exact inputs and observes only the result properties registered for this section, not an unrelated intrinsic."\n  },\n  "S16.9.17-002": {\n    "asind-elemental-function-class": "Apply ASIND to a rank-one array with at least two distinct elements and assert the result array has corresponding element positions; a scalar-only replacement would fail."\n  },\n  "S16.9.17-003": {\n    "asind-argument-restrictions": "Use conforming arguments at representative interior and boundary values; nonconforming type or value probes remain source-control only because these unnumbered restrictions carry no required diagnostic."\n  },\n  "S16.9.17-004": {\n    "asind-result-same-as-x": "Evaluate ASIND for scalar and rank-one arguments of a selected real kind, and for complex where allowed; assign to same-kind result variables and assert KIND and shape without comparing approximate numerical equality."\n  },\n  "S16.9.17-005": {\n    "asind-processor-dependent-approximation": "No portable exact-value oracle exists for the approximation; future fixtures must not compare ASIND results with the approximate example or a hard-coded decimal value."\n  },\n  "S16.9.17-006": {\n    "asind-result-degrees": "Use exact real inputs -1.0, 0.0, and 1.0 and assert only degree-range properties rather than exact approximation values.",\n    "asind-result-range": "Initialize observed results to out-of-range sentinels, call ASIND on exact boundary and interior inputs, and assert every result lies in the required closed interval [-90,90]; mutate by using ASIN or wrong bounds."\n  }\n}'


DROPPED_VARIANTS = {
    "all_arguments", "any_transformational_class", "any_arguments",
    "asin_operation", "asind_operation",
}

CLAIMED_FACETS_BY_VARIANT = {
    "aint_arguments": ["kind-scalar-integer-constant"],
    "aint_result_kind": ["kind-present-selects-result-kind", "kind-absent-uses-a-kind"],
    "aint_truncation_values": ["magnitude-less-than-one-gives-zero", "positive-truncates-toward-zero", "negative-truncates-toward-zero"],
    "all_result_characteristics": ["dim-absent-scalar", "rank-one-dim-scalar", "dim-present-rank-and-shape"],
    "all_result_values": ["all-elements-true", "zero-size-true", "any-false-gives-false", "dim-section-reductions"],
    "allocated_arguments": ["array-allocatable-argument", "scalar-allocatable-argument"],
    "allocated_result_characteristics": ["scalar-result"],
    "allocated_result_values": ["allocated-true", "unallocated-false"],
    "anint_arguments": ["kind-scalar-integer-constant"],
    "anint_result_kind": ["kind-present-selects-result-kind", "kind-absent-uses-a-kind"],
    "anint_nearest_values": ["nearest-positive", "nearest-negative", "tie-greater-magnitude-positive", "tie-greater-magnitude-negative"],
    "any_or_reduction": ["any-logical-or-reduction"],
    "any_result_characteristics": ["any-result-scalar-without-dim-or-rank-one", "any-result-dim-rank-and-shape"],
    "any_result_values": ["any-true-if-any-element-true", "any-false-if-no-elements-true", "any-false-for-zero-size-mask", "any-dim-result-equals-slice-reductions"],
    "asin_elemental_class": ["asin-elemental-function-class"],
    "asin_arguments": ["asin-argument-restrictions"],
    "asin_result_characteristics": ["asin-result-same-as-x"],
    "asin_real_range": ["asin-real-result-range"],
    "asin_complex_range": ["asin-complex-real-part-range"],
    "asind_elemental_class": ["asind-elemental-function-class"],
    "asind_arguments": ["asind-argument-restrictions"],
    "asind_result_characteristics": ["asind-result-same-as-x"],
    "asind_degree_range": ["asind-result-range"],
}

FEATURE_MUTATIONS_BY_VARIANT = {
    "aint_arguments": [("kind-scalar-integer-constant", "kind(aint(high, kind=kind(0.0)))", "kind(aint(high))")],
    "aint_result_kind": [
        ("kind-present-selects-result-kind", "kind(aint(high, kind=kind(0.0)))", "kind(aint(high))"),
        ("kind-absent-uses-a-kind", "kind(aint(high))", "kind(aint(real(high, kind=kind(0.0))))"),
    ],
    "aint_truncation_values": [
        ("magnitude-less-than-one-gives-zero", "below_one = aint(0.5)", "below_one = aint(1.0)"),
        ("positive-truncates-toward-zero", "positive = aint(2.5)", "positive = anint(2.5)"),
        ("negative-truncates-toward-zero", "negative = aint(-2.5)", "negative = anint(-2.5)"),
    ],
    "all_result_characteristics": [
        ("dim-absent-scalar", "scalar_result = all(mask2)", "scalar_result = any(mask2)"),
        ("rank-one-dim-scalar", "vector = [.true., .true.]", "vector = [.true., .false.]"),
        ("dim-present-rank-and-shape", "reduced = all(mask2, dim=1)", "reduced = all(mask2, dim=2)"),
    ],
    "all_result_values": [
        ("all-elements-true", "all_true = [.true., .true.]", "all_true = [.true., .false.]"),
        ("zero-size-true", "all(empty)", "any(empty)"),
        ("any-false-gives-false", "has_false = [.true., .false., .true.]", "has_false = [.true., .true., .true.]"),
        ("dim-section-reductions", "reduced = all(mask2, dim=1)", "reduced = all(mask2, dim=2)"),
    ],
    "allocated_arguments": [
        ("array-allocatable-argument", "allocate(array(2))", "! allocate(array(2))"),
        ("scalar-allocatable-argument", "scalar_status = allocated(scalar)", "allocate(scalar)\n  scalar_status = allocated(scalar)"),
    ],
    "allocated_result_characteristics": [
        ("scalar-result", "scalar_probe => allocated(array)", "scalar_probe => [allocated(array)]"),
    ],
    "allocated_result_values": [
        ("allocated-true", "allocate(array(4))", "! allocate(array(4))"),
        ("unallocated-false", "scalar_status = allocated(scalar)", "allocate(scalar)\n  scalar_status = allocated(scalar)"),
    ],
    "anint_arguments": [
        ("kind-scalar-integer-constant", "kind(anint(high, kind=kind(0.0)))", "kind(anint(high, kind=kind(0.0d0)))"),
    ],
    "anint_result_kind": [
        ("kind-present-selects-result-kind", "kind(anint(high, kind=kind(0.0)))", "kind(anint(high))"),
        ("kind-absent-uses-a-kind", "kind(anint(high))", "kind(anint(real(high, kind=kind(0.0))))"),
    ],
    "anint_nearest_values": [
        ("nearest-positive", "near_pos = anint(2.25)", "near_pos = anint(2.75)"),
        ("nearest-negative", "near_neg = anint(-2.25)", "near_neg = anint(-2.75)"),
        ("tie-greater-magnitude-positive", "tie_pos = anint(2.5)", "tie_pos = aint(2.5)"),
        ("tie-greater-magnitude-negative", "tie_neg = anint(-2.5)", "tie_neg = aint(-2.5)"),
    ],
    "any_or_reduction": [("any-logical-or-reduction", "observed = any(mask)", "observed = all(mask)")],
    "any_result_characteristics": [
        ("any-result-scalar-without-dim-or-rank-one", "scalar_result = any(mask2)", "scalar_result = all(mask2)"),
        ("any-result-dim-rank-and-shape", "reduced = any(mask2, dim=1)", "reduced = any(mask2, dim=2)"),
    ],
    "any_result_values": [
        ("any-true-if-any-element-true", "has_true = [.false., .true., .false.]", "has_true = [.false., .false., .false.]"),
        ("any-false-if-no-elements-true", "all_false = [.false., .false., .false.]", "all_false = [.false., .true., .false.]"),
        ("any-false-for-zero-size-mask", "any(empty)", "all(empty)"),
        ("any-dim-result-equals-slice-reductions", "reduced = any(mask2, dim=1)", "reduced = any(mask2, dim=2)"),
    ],
    "asin_elemental_class": [("asin-elemental-function-class", "values = asin(inputs)", "values = asin(inputs(2))")],
    "asin_arguments": [("asin-argument-restrictions", "z_value = asin(z)", "z_value = (10.0, 0.0) * asin(z)")],
    "asin_result_characteristics": [("asin-result-same-as-x", "size(asin(high_inputs))", "size([asin(high_inputs(1))])")],
    "asin_real_range": [("asin-real-result-range", "values = asin(inputs)", "values = 10.0 * asin(inputs)")],
    "asin_complex_range": [("asin-complex-real-part-range", "z_value = asin(z)", "z_value = (10.0, 0.0) * asin(z)")],
    "asind_elemental_class": [("asind-elemental-function-class", "values = asind(inputs)", "values = asind(inputs(2))")],
    "asind_arguments": [("asind-argument-restrictions", "values = asind([-1.0, 0.0, 1.0])", "values = 2.0 * asind([-1.0, 0.0, 1.0])")],
    "asind_result_characteristics": [("asind-result-same-as-x", "size(asind(high_inputs))", "size([asind(high_inputs(1))])")],
    "asind_degree_range": [("asind-result-range", "values = asind(inputs)", "values = 2.0 * asind(inputs)")],
}

ORIGINAL_PENDING = json.loads(ORIGINAL_PENDING_JSON)

CASES = [case for case in CASES if case["variant"] not in DROPPED_VARIANTS]
for case in CASES:
    case["facets"] = CLAIMED_FACETS_BY_VARIANT[case["variant"]]
    if len(FEATURE_MUTATIONS_BY_VARIANT[case["variant"]]) != len(case["facets"]):
        raise ValueError("feature mutation/facet count mismatch for " + case["variant"])

FACETS_BY_RULE = {case["rule"]: case["facets"] for case in CASES}
CASE_BY_RULE = {case["rule"]: case for case in CASES}
REMAINING_PENDING = {
    rule: set(pending) - set(FACETS_BY_RULE.get(rule, ()))
    for rule, pending in ORIGINAL_PENDING.items()
    if set(pending) - set(FACETS_BY_RULE.get(rule, ()))
}


def identifier(case):
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__" + TOPIC + "_" + case["variant"]


def case_dir(root, case):
    return Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case["variant"])


def mutation_span(source, expected):
    if source.count(expected) != 1:
        raise ValueError(f"mutation token is not unique: {expected!r}")
    start = source.index(expected)
    return [start, start + len(expected)]


def source_specs():
    specs = {}
    for case in CASES:
        source = case["source"]
        raw = source.encode("ascii")
        fid = identifier(case)
        completion_line = f"  write(*,'(a)') '{case['completion'].rstrip()}'"
        features = []
        for facet, expected, replacement in FEATURE_MUTATIONS_BY_VARIANT[case["variant"]]:
            features.append(dict(
                id="feature-" + facet, facet=facet, kind="feature", category="intrinsic-effect",
                expected=expected, replacement=replacement, span=mutation_span(source, expected),
                mutation="facet-feature-perturbation",
            ))
        oracle = dict(
            id="check-count-oracle", kind="oracle", category="check-total",
            expected=f"case ({case['checks']})", replacement=f"case ({case['checks'] + 1})",
            span=mutation_span(source, f"case ({case['checks']})"), mutation="oracle-check-count",
        )
        omission = dict(
            id="completion-omission", kind="output", category="completion",
            expected=completion_line, replacement="! completion omitted",
            span=mutation_span(source, completion_line), mutation="completion-omission",
        )
        for mutation in features + [oracle, omission]:
            start, end = mutation["span"]
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError("mutation span does not bind parent source")
            mutation["line"] = source[:start].count("\n") + 1
        specs[fid] = dict(
            id=fid, variant=case["variant"], section=case["section"], rule=case["rule"],
            facets=case["facets"], evidence=case["evidence"],
            source=source, source_sha256=sha(raw), completion=case["completion"],
            checks=case["checks"], derivation=case["derivation"],
            mutations=features + [oracle, omission], feature_mutations=features, oracle_mutations=[oracle],
        )
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
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = case_dir(root, spec)
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""),
        )
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def oracle_for(rule):
    spec = CASE_BY_RULE[rule]
    prefix = f"{rule} {TOPIC} runtime fixture: "
    return prefix + (
        f"the `{spec['variant']}` complete run/effect/f2023 program covers {', '.join(spec['facets'])}. "
        f"{spec['derivation']} The source establishes non-default or bounded observations before completion, "
        "uses exact logical, shape, kind, allocation-status, or exactly representable whole-number real oracles, "
        "and does not compare processor-dependent transcendental approximations for equality."
    )


def limitation_for(rule):
    spec = CASE_BY_RULE[rule]
    prefix = f"{rule} {TOPIC} fixture boundaries: "
    common = (
        "Only ordinary single-image valid programs are covered. Clause 16 unnumbered argument restrictions are "
        "exercised by conforming positive controls only; no diagnostic rejection, wording, or error code is claimed. "
        "No coarray, IEEE exception, evaluation-order, nondefault logical kind, resource failure, or universal "
        "compiler-conformance property is asserted."
    )
    if spec["section"] in {"16.9.16", "16.9.17"}:
        common += " Transcendental results are checked only against ranges and characteristics fixed by the text."
    return prefix + common


ORACLE_PREFIXES = {rule: f"{rule} {TOPIC} runtime fixture: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} {TOPIC} fixture boundaries: " for rule in FACETS_BY_RULE}
ORACLES = {rule: oracle_for(rule) for rule in FACETS_BY_RULE}
LIMITATIONS = {rule: limitation_for(rule) for rule in FACETS_BY_RULE}


def without_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    return "\n\n".join(paragraph for paragraph in paragraphs if not paragraph.startswith(prefix))


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, pending in ORIGINAL_PENDING.items():
        if rule in by_rule:
            owner = by_rule[rule]
            owner["pending"] = dict(pending)
            owner["oracle"] = without_owned_paragraph(
                owner.get("oracle", ""), f"{rule} {TOPIC} runtime fixture: ")
            owner["oracle_limitation"] = without_owned_paragraph(
                owner.get("oracle_limitation", ""), f"{rule} {TOPIC} fixture boundaries: ")
    for rule, facets in FACETS_BY_RULE.items():
        if not rule.startswith("S" + section):
            continue
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        owner.setdefault("pending", {})
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    for rule, remaining in REMAINING_PENDING.items():
        if rule in by_rule:
            if set(by_rule[rule].get("pending", {})) != remaining:
                raise ValueError("unexpected remaining pending facets for " + rule)
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
    owned_begin = f"<!-- BEGIN INTRINSICS 16.9.B FIXTURES {section} -->"
    owned_end = f"<!-- END INTRINSICS 16.9.B FIXTURES {section} -->"
    owned_cases = [case for case in CASES if case["section"] == section]
    covered = sum(len(case["facets"]) for case in owned_cases)
    pending_count = sum(len(facets) for rule, facets in REMAINING_PENDING.items() if rule.startswith("S" + section))
    pending_text = ""
    if pending_count:
        pending_text = f" {pending_count} facets remain pending because they lack a facet-specific portable oracle/mutation in this packet."
    summary = (
        owned_begin + "\n"
        f"\n## `{TOPIC}` executable fixture observations\n\n"
        f"This packet adds {len(owned_cases)} complete run/effect/f2023 fixtures for {section}, covering "
        f"{covered} pending facets with exact logical, shape, kind, allocation-status, whole-number real, "
        f"or bounded-range observations. Generated mutation metadata perturbs each fixture's intrinsic feature, "
        f"each claimed facet's intrinsic feature, its check-count oracle, and its completion output; "
        f"the mutation-check mode compiles each mutant in "
        f"a repository-local scratch directory and requires every mutant to fail at run time or by output mismatch."
        f"{pending_text}\n"
        + owned_end
    )
    if owned_begin in before or owned_end in before:
        if before.count(owned_begin) != 1 or before.count(owned_end) != 1:
            raise ValueError("fixture summary boundaries changed for " + section)
        head, tail = before.split(owned_begin)
        _, rest_tail = tail.split(owned_end)
        before = head + summary + rest_tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    generated = "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n"
    return before + begin + generated + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    rendered_views = {}
    for section in SECTIONS:
        path = root / CATALOGUES[section]
        catalogue = json.loads(path.read_text())
        updated = synced_catalogue(section, catalogue)
        updated_catalogues[section] = updated
        rendered_views[section] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section in SECTIONS:
            if json.loads((root / CATALOGUES[section]).read_text()) != updated_catalogues[section]:
                stale.append(CATALOGUES[section])
            if (root / VIEWS[section]).read_text() != rendered_views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale intrinsics 16.9.b fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section in SECTIONS:
                (root / CATALOGUES[section]).write_text(json.dumps(updated_catalogues[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(rendered_views[section])
    return specs


def std_args(compiler, std):
    name = Path(compiler).name.lower()
    if "gfortran" in name:
        return [f"-std={std}"]
    return [f"--std={std}"]


def compile_and_run(compiler, std, source, workdir, expected_stdout, timeout=20):
    workdir.mkdir(parents=True, exist_ok=True)
    source_path = workdir / "source.f90"
    exe_path = workdir / "program"
    source_path.write_bytes(source)
    cmd = [compiler] + std_args(compiler, std) + [str(source_path), "-o", str(exe_path)]
    compile_proc = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=timeout)
    if compile_proc.returncode != 0:
        return dict(phase="compile", passed=False, returncode=compile_proc.returncode,
                    stdout=compile_proc.stdout, stderr=compile_proc.stderr)
    run_proc = subprocess.run([str(exe_path)], cwd=workdir, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout)
    passed = run_proc.returncode == 0 and run_proc.stdout == expected_stdout and run_proc.stderr == ""
    return dict(phase="run", passed=passed, returncode=run_proc.returncode,
                stdout=run_proc.stdout, stderr=run_proc.stderr)


def run_mutations(root, compiler, std):
    root = Path(root)
    specs = source_specs()
    work = root / "scratch_intrinsics_16_9_b_mutations"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    try:
        parent_passed = 0
        mutant_failed = 0
        mutant_total = 0
        failures = []
        for index, spec in enumerate(specs.values(), 1):
            parent = compile_and_run(compiler, std, spec["source"].encode("ascii"),
                                     work / f"{index:03d}_parent", spec["completion"])
            if not parent["passed"]:
                failures.append((spec["id"], "parent", parent))
                continue
            parent_passed += 1
            for midx, mutation in enumerate(spec["mutations"], 1):
                mutant_total += 1
                result = compile_and_run(compiler, std, mutated_source(spec, mutation),
                                         work / f"{index:03d}_{midx:02d}_{mutation['id']}", spec["completion"])
                if result["phase"] != "run":
                    failures.append((spec["id"], mutation["id"], result))
                elif result["passed"]:
                    failures.append((spec["id"], mutation["id"], result))
                else:
                    mutant_failed += 1
        if failures:
            lines = [f"mutation check failed for {len(failures)} item(s)"]
            for case_id, mutation_id, result in failures[:20]:
                lines.append(f"{case_id} {mutation_id} phase={result['phase']} rc={result['returncode']}")
                lines.append("stdout=" + result["stdout"][:500].replace("\n", "\\n"))
                lines.append("stderr=" + result["stderr"][:500].replace("\n", "\\n"))
            raise RuntimeError("\n".join(lines))
        return dict(parents=parent_passed, mutants=mutant_failed, total=mutant_total)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-compiler")
    parser.add_argument("--mutation-std", default="f2023")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_compiler:
        result = run_mutations(args.root, args.mutation_compiler, args.mutation_std)
        print(f"Mutation check OK: {result['parents']}/{len(CASES)} parents passed; "
              f"{result['mutants']}/{result['total']} mutants failed as expected.")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics 16.9.b cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
