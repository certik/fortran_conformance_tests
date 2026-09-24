#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.59-16.9.66 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_f"
SECTIONS = ("16.9.59", "16.9.60", "16.9.61", "16.9.62", "16.9.63", "16.9.65", "16.9.66")
CATALOGUES = {
    "16.9.59": "doc/catalogues/command_argument_count_16_9_59.json",
    "16.9.60": "doc/catalogues/conjg_16_9_60.json",
    "16.9.61": "doc/catalogues/cos_16_9_61.json",
    "16.9.62": "doc/catalogues/cosd_16_9_62.json",
    "16.9.63": "doc/catalogues/cosh_16_9_63.json",
    "16.9.65": "doc/catalogues/cospi_16_9_65.json",
    "16.9.66": "doc/catalogues/count_16_9_66.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.F FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.F FIXTURES -->"
COSPI_PENDING = {
    "S16.9.65-001": {
        "cospi-circular-cosine-description":
            "Left pending by intrinsics_16_9_f: the prose circular-cosine description has no distinct portable oracle beyond the executable argument and characteristic facets plus the approximate result-value facets."
    },
    "S16.9.65-005": {
        "cospi-half-revolution-argument":
            "Left pending by intrinsics_16_9_f: p5 says COSPI(X) is a processor-dependent approximation to COS(X*pi) and gives no portable exact value or error bound for distinguishing the half-revolution interpretation."
    },
    "S16.9.65-006": {
        "cospi-processor-dependent-approximation":
            "Left pending by intrinsics_16_9_f: no portable exact bits, error bound, rounded value, or agreement with another intrinsic is required for the processor-dependent approximation."
    },
}
COMMAND_PENDING = {
    "S16.9.59-002": {
        "command_argument_count-counts-available-arguments":
            "Left pending by intrinsics_16_9_f: p5 permits processors with no command-argument support to return zero even when a host launcher supplies extra arguments, so a nonzero argument-count oracle is not portable."
    },
    "S16.9.59-003": {
        "command_argument_count-support-may-be-absent":
            "Left pending by intrinsics_16_9_f: absence of command-argument support is processor latitude, not a portable run-time outcome the suite can require.",
        "command_argument_count-command-name-concept-processor-dependent":
            "Left pending by intrinsics_16_9_f: whether a processor has a command-name concept is processor dependent; no fixture may require that concept to exist."
    },
}
TRIG_ARGUMENT_PENDING = {
    "S16.9.61-001": {
        "cos-real-argument":
            "Left pending by intrinsics_16_9_f correction: p5 defines only a processor-dependent approximation for COS, so a valid real-argument call has no facet-specific portable value oracle distinct from result characteristics.",
        "cos-complex-argument":
            "Left pending by intrinsics_16_9_f correction: p5 defines only a processor-dependent approximation for COS, so a valid complex-argument call has no facet-specific portable value oracle distinct from result characteristics."
    },
    "S16.9.62-001": {
        "cosd-real-argument":
            "Left pending by intrinsics_16_9_f correction: p5 defines only a processor-dependent approximation for COSD, so a valid real-argument call has no facet-specific portable value oracle distinct from result characteristics."
    },
    "S16.9.63-001": {
        "cosh-real-argument":
            "Left pending by intrinsics_16_9_f correction: p5 defines only a processor-dependent approximation for COSH, so a valid real-argument call has no facet-specific portable value oracle distinct from result characteristics.",
        "cosh-complex-argument":
            "Left pending by intrinsics_16_9_f correction: p5 defines only a processor-dependent approximation for COSH, so a valid complex-argument call has no facet-specific portable value oracle distinct from result characteristics."
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace(".", "_").replace("-", "_") + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Case:
    section: str
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[tuple[str, str, str, str], ...]
    oracle: str

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.F " + self.variant.upper().replace("_", " ") + " OK\n"


def program(name: str, body: str, completion: str, helpers: str = "") -> str:
    return f"""program i169f_{name}
  implicit none
{body}  write(*,'(a)') '{completion.rstrip()}'
{helpers}end program i169f_{name}
"""


REQUIRE_HELPERS = """contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
"""


def command_count_kind_source(completion):
    return program("command_argument_count_kind", """  integer, parameter :: WIDE = selected_int_kind(18)
  integer :: observed_kind
  observed_kind = -777
  observed_kind = kind(command_argument_count())
  call require_true('command_argument_count default integer kind', observed_kind == kind(0))
""", completion, REQUIRE_HELPERS)


def command_count_value_source(completion):
    return program("command_argument_count_no_args", """  integer :: observed, command_name_control
  observed = -99
  observed = command_argument_count()
  call require_true('command_argument_count no arguments zero', observed == 0)
  command_name_control = -88
  command_name_control = command_argument_count()
  call require_true('command_argument_count command name not counted', command_name_control == 0)
""", completion, REQUIRE_HELPERS)


def conjg_argument_source(completion):
    return program("conjg_arguments", """  complex(kind=kind(0.0d0)) :: scalar_z, scalar_result
  complex(kind=kind(0.0d0)) :: vector_z(2), vector_result(2)
  scalar_z = cmplx(2.0d0, 3.0d0, kind=kind(0.0d0))
  vector_z = [cmplx(2.0d0, 3.0d0, kind=kind(0.0d0)), cmplx(-4.0d0, -5.0d0, kind=kind(0.0d0))]
  scalar_result = cmplx(-77.0d0, 88.0d0, kind=kind(0.0d0))
  vector_result = cmplx(-77.0d0, 88.0d0, kind=kind(0.0d0))
  scalar_result = conjg(scalar_z)
  vector_result = conjg(vector_z)
  call require_true('conjg scalar complex argument reached', aimag(scalar_result) == -3.0d0)
  call require_true('conjg vector complex argument reached', all(aimag(vector_result) == [-3.0d0, 5.0d0]))
""", completion, REQUIRE_HELPERS)


def conjg_characteristics_source(completion):
    return program("conjg_characteristics", """  complex(kind=kind(0.0d0)) :: scalar_z, vector_z(2)
  scalar_z = cmplx(2.0d0, 3.0d0, kind=kind(0.0d0))
  vector_z = [cmplx(2.0d0, 3.0d0, kind=kind(0.0d0)), cmplx(-4.0d0, -5.0d0, kind=kind(0.0d0))]
  call require_true('conjg scalar result kind direct', kind(conjg(scalar_z)) == kind(scalar_z))
  call require_true('conjg vector result kind direct', kind(conjg(vector_z)) == kind(vector_z))
  call require_true('conjg direct shape inquiry', all(shape(conjg(vector_z)) == shape(vector_z)))
""", completion, REQUIRE_HELPERS)


def conjg_value_source(completion):
    return program("conjg_value", """  complex(kind=kind(0.0d0)) :: z(2), result(2)
  z = [cmplx(2.0d0, 3.0d0, kind=kind(0.0d0)), cmplx(-4.0d0, -5.0d0, kind=kind(0.0d0))]
  result = cmplx(-77.0d0, 88.0d0, kind=kind(0.0d0))
  result = conjg(z)
  call require_true('conjg real parts unchanged', all(real(result) == [2.0d0, -4.0d0]))
  call require_true('conjg imaginary parts negated', all(aimag(result) == [-3.0d0, 5.0d0]))
""", completion, REQUIRE_HELPERS)


def cos_characteristics_source(completion):
    return program("cos_characteristics", """  real(kind=kind(0.0d0)) :: real_x(2)
  complex(kind=kind(0.0d0)) :: complex_x(2)
  real_x = [0.0d0, 1.0d0]
  complex_x = [cmplx(0.0d0, 0.0d0, kind=kind(0.0d0)), cmplx(1.0d0, 0.0d0, kind=kind(0.0d0))]
  call require_true('cos real result kind direct', kind(cos(real_x)) == kind(real_x))
  call require_true('cos direct shape inquiry', all(shape(cos(real_x)) == shape(real_x)))
  call require_true('cos complex result kind direct', kind(cos(complex_x)) == kind(complex_x))
  call require_true('cos complex direct shape inquiry', all(shape(cos(complex_x)) == shape(complex_x)))
""", completion, REQUIRE_HELPERS)


def cosd_characteristics_source(completion):
    return program("cosd_characteristics", """  real(kind=kind(0.0d0)) :: x(2)
  x = [0.0d0, 60.0d0]
  call require_true('cosd result kind direct', kind(cosd(x)) == kind(x))
  call require_true('cosd direct shape inquiry', all(shape(cosd(x)) == shape(x)))
""", completion, REQUIRE_HELPERS)


def cosh_characteristics_source(completion):
    return program("cosh_characteristics", """  real(kind=kind(0.0d0)) :: real_x(2)
  complex(kind=kind(0.0d0)) :: complex_x(2)
  real_x = [0.0d0, 1.0d0]
  complex_x = [cmplx(0.0d0, 0.0d0, kind=kind(0.0d0)), cmplx(0.0d0, 1.0d0, kind=kind(0.0d0))]
  call require_true('cosh real result kind direct', kind(cosh(real_x)) == kind(real_x))
  call require_true('cosh real direct shape inquiry', all(shape(cosh(real_x)) == shape(real_x)))
  call require_true('cosh complex result kind direct', kind(cosh(complex_x)) == kind(complex_x))
  call require_true('cosh direct shape inquiry', all(shape(cosh(complex_x)) == shape(complex_x)))
""", completion, REQUIRE_HELPERS)


def cospi_elemental_source(completion):
    return program("cospi_elemental", """  real(kind=kind(0.0d0)) :: x(3)
  x = [0.0d0, 0.25d0, 1.0d0]
  call require_true('cospi elemental array extent direct', size(cospi(x)) == 3)
  call require_true('cospi elemental array shape direct', all(shape(cospi(x)) == shape(x)))
""", completion, REQUIRE_HELPERS)


def cospi_argument_source(completion):
    return program("cospi_argument", """  real(kind=kind(0.0d0)) :: x
  x = 0.25d0
  call require_true('cospi real x accepted with same kind', kind(cospi(x)) == kind(x))
""", completion, REQUIRE_HELPERS)


def cospi_characteristics_source(completion):
    return program("cospi_characteristics", """  real(kind=kind(0.0d0)) :: scalar_x, vector_x(3)
  scalar_x = 0.25d0
  vector_x = [0.0d0, 0.25d0, 1.0d0]
  call require_true('cospi result same kind direct', kind(cospi(scalar_x)) == kind(scalar_x))
  call require_true('cospi result shape direct', all(shape(cospi(vector_x)) == shape(vector_x)))
""", completion, REQUIRE_HELPERS)


def count_arguments_source(completion):
    return program("count_arguments", """      integer, parameter :: IK = selected_int_kind(18)
    logical :: mask1(3), mask2(2,3)
    integer :: mask_control, dim_value
    integer, allocatable :: dim_counts(:), pointer_counts(:)
    integer, target :: dim_target
    integer, pointer :: dim_ptr
  mask1 = [.true., .false., .true.]
  mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
  mask_control = -77
  mask_control = count(mask1)
  call require_true('count logical mask argument', mask_control == 2)
  dim_value = 1
  dim_counts = [-77, -77, -77]
  dim_counts = count(mask2, dim=dim_value)
  call require_true('count dim scalar in range size', size(dim_counts) == 3)
  call require_true('count dim scalar in range values', all(dim_counts == [1, 2, 0]))
  dim_target = 1
  dim_ptr => dim_target
  pointer_counts = [-77, -77, -77]
  pointer_counts = count(mask2, dim=dim_ptr)
  call require_true('count associated pointer dim actual size', size(pointer_counts) == 3)
  call require_true('count associated pointer dim actual values', all(pointer_counts == [1, 2, 0]))
  call require_true('count kind constant argument', kind(count(mask1, kind=IK)) == IK)
""", completion, REQUIRE_HELPERS)


def count_characteristics_source(completion):
    return program("count_characteristics", """      integer, parameter :: IK = selected_int_kind(18)
    logical :: mask1(4), mask2(2,3)
    integer :: integer_result, scalar_count
    integer, allocatable :: dim_counts(:)
    mask1 = [.true., .false., .true., .false.]
    mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
    integer_result = -777
    integer_result = count(mask1)
    call require_true('count result integer exact assignment', integer_result == 2)
    call require_true('count result selected kind', kind(count(mask1, kind=IK)) == IK)
    call require_true('count result default kind', kind(count(mask1)) == kind(0))
  scalar_count = -777
  scalar_count = count(mask1)
  call require_true('count result scalar without dim', size(shape(count(mask1))) == 0 .and. scalar_count == 2)
  dim_counts = [-777, -777, -777]
  dim_counts = count(mask2, dim=1)
  call require_true('count dim result direct rank and shape', &
       size(shape(count(mask2, dim=1))) == 1 .and. size(count(mask2, dim=1)) == 3)
  call require_true('count dim result assigned size', size(dim_counts) == 3)
  call require_true('count dim result assigned values', all(dim_counts == [1, 2, 0]))
""", completion, REQUIRE_HELPERS)


def count_values_source(completion):
    return program("count_values", """  logical :: mask1(4), empty(0), companion(4), mask2(2,3)
    integer :: description_count, rank_one_count, empty_count
    integer, allocatable :: dim_counts(:)
  mask1 = [.true., .false., .true., .false.]
  empty = [logical ::]
  companion = [.true., .false., .true., .false.]
  mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
  description_count = -777
  description_count = count([.true., .false., .true.])
  call require_true('count true value reduction description', description_count == 2)
  call require_true('count transformational dim rank reduction', &
       size(shape(count(mask2, dim=1))) == 1 .and. size(shape(count(mask2))) == 0)
  rank_one_count = -777
  rank_one_count = count(mask1)
  call require_true('count rank one true elements', rank_one_count == 2)
  empty_count = -777
  empty_count = count(empty)
  call require_true('count size zero mask zero with companion', empty_count == 0 .and. count(companion) == 2)
  dim_counts = [-777, -777, -777]
  dim_counts = count(mask2, dim=1)
  call require_true('count dim present section size', size(dim_counts) == 3)
  call require_true('count dim present section dim one', all(dim_counts == [1, 2, 0]))
  call require_true('count dim present section dim two', all(count(mask2, dim=2) == [2, 1]))
""", completion, REQUIRE_HELPERS)


def count_description_source(completion):
    return program("count_description", """  integer :: description_count
  description_count = -777
  description_count = count([.true., .false., .true.])
  call require_true('count true value reduction description', description_count == 2)
""", completion, REQUIRE_HELPERS)


def count_transformational_source(completion):
    return program("count_transformational", """  logical :: mask2(2,3)
  mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
  call require_true('count transformational dim rank reduction', &
       size(shape(count(mask2, dim=1))) == 1 .and. size(shape(count(mask2))) == 0)
""", completion, REQUIRE_HELPERS)


def make_cases():
    raw = []

    def add(section, variant, rule, facets, evidence, source_func, mutations, oracle):
        completion = "INTRINSICS 16.9.F " + variant.upper().replace("_", " ") + " OK\n"
        raw.append(Case(section, variant, rule, tuple(facets), evidence, source_func(completion), tuple(mutations), oracle))

    add("16.9.59", "command_argument_count_no_args", "S16.9.59-001",
        ["command_argument_count-default-integer-scalar"], "effect", command_count_kind_source,
        [("command_argument_count-default-integer-scalar", "default-kind-wide-substitution", "kind(command_argument_count())", "kind(int(command_argument_count(), kind=WIDE))")],
        "COMMAND_ARGUMENT_COUNT characteristics are observed by directly inquiring KIND(COMMAND_ARGUMENT_COUNT()) in a no-argument run; the source fixes a default integer scalar result.")
    add("16.9.59", "command_argument_count_no_args_value", "S16.9.59-002",
        ["command_argument_count-no-arguments-zero", "command_argument_count-command-name-not-counted"], "effect", command_count_value_source,
        [("command_argument_count-no-arguments-zero", "no-args-feature-removed", "observed = command_argument_count()", "observed = 1"),
         ("command_argument_count-command-name-not-counted", "command-name-feature-removed", "command_name_control = command_argument_count()", "command_name_control = 1")],
        "The runner launches executables with no run.arguments by default, so p5 requires zero whether command-argument support is absent or no user arguments are available; the same zero observation excludes counting a processor command name as an argument in this execution.")

    add("16.9.60", "conjg_arguments", "S16.9.60-001", ["conjg-argument-type"], "positive-control", conjg_argument_source,
        [("conjg-argument-type", "scalar-conjg-feature-removed", "scalar_result = conjg(scalar_z)", "scalar_result = scalar_z")],
        "CONJG is called with scalar and rank-one complex operands; exact imaginary-component checks prove the complex-argument calls are reached.")
    add("16.9.60", "conjg_characteristics", "S16.9.60-002", ["conjg-result-same-characteristics"], "effect", conjg_characteristics_source,
        [("conjg-result-same-characteristics", "vector-shape-feature-removed", "shape(conjg(vector_z))", "shape([conjg(vector_z(1))])")],
        "CONJG result characteristics are checked directly with KIND(CONJG(...)) and SHAPE(CONJG(...)) inquiries on intrinsic expressions.")
    add("16.9.60", "conjg_value", "S16.9.60-003", ["conjg-complex-conjugate-value"], "effect", conjg_value_source,
        [("conjg-complex-conjugate-value", "conjg-to-identity", "result = conjg(z)", "result = z")],
        "For exact complex inputs (2,3) and (-4,-5), p5 requires real parts unchanged and imaginary parts negated.")

    add("16.9.61", "cos_characteristics", "S16.9.61-002", ["cos-result-same-characteristics"], "effect", cos_characteristics_source,
        [("cos-result-same-characteristics", "real-kind-feature-defaulted", "kind(cos(real_x))", "kind(cos(real(real_x, kind=kind(0.0))))")],
        "COS result characteristics are checked directly with KIND(COS(...)) and SHAPE(COS(...)) inquiries on real and complex intrinsic expressions; no exact COS value is asserted.")

    add("16.9.62", "cosd_characteristics", "S16.9.62-002", ["cosd-result-same-characteristics"], "effect", cosd_characteristics_source,
        [("cosd-result-same-characteristics", "cosd-kind-feature-defaulted", "kind(cosd(x))", "kind(cosd(real(x, kind=kind(0.0))))")],
        "COSD result characteristics are checked directly with KIND(COSD(X)) and SHAPE(COSD(X)) inquiries; no exact COSD value is asserted.")

    add("16.9.63", "cosh_characteristics", "S16.9.63-002", ["cosh-result-same-characteristics"], "effect", cosh_characteristics_source,
        [("cosh-result-same-characteristics", "cosh-kind-feature-defaulted", "kind(cosh(real_x))", "kind(cosh(real(real_x, kind=kind(0.0))))")],
        "COSH result characteristics are checked directly with KIND(COSH(...)) and SHAPE(COSH(...)) inquiries on real and complex intrinsic expressions; no exact COSH value is asserted.")

    add("16.9.65", "cospi_elemental", "S16.9.65-002", ["cospi-elemental-class"], "effect", cospi_elemental_source,
        [("cospi-elemental-class", "cospi-array-to-singleton", "size(cospi(x))", "size([cospi(x(1))])")],
        "COSPI elemental class is observed by applying COSPI to a rank-one real array and directly inquiring the COSPI expression extent and shape, without comparing approximated values.")
    add("16.9.65", "cospi_argument", "S16.9.65-003", ["cospi-x-real"], "positive-control", cospi_argument_source,
        [("cospi-x-real", "cospi-real-kind-defaulted", "kind(cospi(x))", "kind(cospi(real(x, kind=kind(0.0))))")],
        "COSPI X-real positive control calls COSPI with a selected-real-kind scalar and observes only the direct result kind, making the real argument feature load-bearing without any exact value oracle.")
    add("16.9.65", "cospi_characteristics", "S16.9.65-004",
        ["cospi-result-same-kind-as-x", "cospi-result-elemental-shape"], "effect", cospi_characteristics_source,
        [("cospi-result-same-kind-as-x", "cospi-kind-feature-defaulted", "kind(cospi(scalar_x))", "kind(cospi(real(scalar_x, kind=kind(0.0))))"),
         ("cospi-result-elemental-shape", "cospi-vector-to-singleton", "shape(cospi(vector_x))", "shape([cospi(vector_x(1))])")],
        "COSPI result characteristics are checked directly with KIND(COSPI(scalar_x)) and SHAPE(COSPI(vector_x)) inquiries; p5 approximation values are not asserted.")

    add("16.9.66", "count_arguments", "S16.9.66-003",
        ["count-mask-logical-array", "count-dim-integer-scalar-in-range", "count-dim-actual-present-associated-allocated", "count-kind-scalar-integer-constant"],
        "positive-control", count_arguments_source,
        [("count-mask-logical-array", "mask-pattern-perturb", "mask1 = [.true., .false., .true.]", "mask1 = [.true., .false., .false.]"),
         ("count-dim-integer-scalar-in-range", "dim-value-perturb", "dim_value = 1", "dim_value = 2"),
         ("count-dim-actual-present-associated-allocated", "associated-pointer-dim-perturb", "dim_target = 1", "dim_target = 2"),
         ("count-kind-scalar-integer-constant", "kind-argument-defaulted", "kind(count(mask1, kind=IK))", "kind(count(mask1, kind=kind(0)))")],
        "COUNT argument controls use logical masks, scalar DIM variables in range including an associated pointer actual, and a scalar integer constant KIND; exact counts and direct KIND inquiry make each argument feature load-bearing.")
    add("16.9.66", "count_characteristics", "S16.9.66-004",
        ["count-result-integer", "count-result-kind-selected", "count-result-kind-default", "count-result-scalar-without-dim-or-rank-one", "count-result-rank-and-shape-with-dim"],
        "effect", count_characteristics_source,
        [("count-result-integer", "integer-result-feature-removed", "integer_result = count(mask1)", "integer_result = -777"),
         ("count-result-kind-selected", "selected-kind-defaulted", "kind(count(mask1, kind=IK))", "kind(count(mask1, kind=kind(0)))"),
         ("count-result-kind-default", "default-kind-made-selected", "kind(count(mask1))", "kind(count(mask1, kind=IK))"),
         ("count-result-scalar-without-dim-or-rank-one", "scalar-rank-to-dim-result", "size(shape(count(mask1)))", "size(shape(count(mask2, dim=1)))"),
         ("count-result-rank-and-shape-with-dim", "dim-shape-perturb", "dim_counts = count(mask2, dim=1)", "dim_counts = count(mask2, dim=2)")],
        "COUNT result characteristics are observed with integer assignment, direct KIND(COUNT(...)) inquiries for selected and default kind, direct RANK(COUNT(...)) for scalar results, and direct rank/size plus exact DIM values for rank-reduced results.")
    add("16.9.66", "count_values", "S16.9.66-005",
        ["count-rank-one-true-elements", "count-size-zero-mask-zero", "count-dim-present-section-counts"], "effect", count_values_source,
        [("count-rank-one-true-elements", "rank-one-mask-perturb", "mask1 = [.true., .false., .true., .false.]", "mask1 = [.true., .false., .false., .false.]"),
         ("count-size-zero-mask-zero", "empty-feature-to-companion", "empty_count = count(empty)", "empty_count = count(companion)"),
         ("count-dim-present-section-counts", "dim-section-perturb", "dim_counts = count(mask2, dim=1)", "dim_counts = count(mask2, dim=2)")],
        "COUNT value cases use exact logical masks: rank-one COUNT has two true elements, a zero-size mask counts zero with a nonzero companion guard, and DIM section counts are [1,2,0] and [2,1].")
    add("16.9.66", "count_description_transform", "S16.9.66-001",
        ["count-true-value-reduction-description"], "effect", count_description_source,
        [("count-true-value-reduction-description", "description-count-to-size", "description_count = count([.true., .false., .true.])", "description_count = size([.true., .false., .true.])")],
        "The COUNT description is bound through an exact true-value reduction: COUNT([T,F,T]) is required to be 2, not the array size.")
    add("16.9.66", "count_transformational", "S16.9.66-002",
        ["count-transformational-class"], "effect", count_transformational_source,
        [("count-transformational-class", "dim-reduction-to-scalar", "size(shape(count(mask2, dim=1)))", "size(shape(count(mask2)))")],
        "The transformational class is observed through DIM rank reduction: COUNT on a rank-two mask with DIM has rank one while COUNT without DIM is scalar.")

    return {identifier(case.rule, case.variant): case for case in raw}


def mutation_records(case: Case):
    records = []
    raw = case.source.encode("ascii")
    for facet, mid, expected, replacement in case.mutations:
        count = case.source.count(expected)
        if count != 1:
            raise ValueError(f"{case.variant}:{mid} expected unique mutation text {expected!r}, saw {count}")
        start = case.source.index(expected)
        mutated = raw[:start] + replacement.encode("ascii") + raw[start + len(expected):]
        records.append(dict(id=mid, facet=facet, kind="feature", category="intrinsic-feature",
                            expected=expected, replacement=replacement, span=[start, start + len(expected)],
                            line=case.source[:start].count("\n") + 1, source_sha256=sha(mutated)))
    return records


def build_corpus(root=ROOT):
    files, specs = {}, {}
    for name, case in make_cases().items():
        raw = case.source.encode("ascii")
        mutations = mutation_records(case)
        spec = dict(id=name, variant=case.variant, section=case.section, rule=case.rule,
                    facets=list(case.facets), evidence=case.evidence, source=case.source,
                    source_sha256=sha(raw), completion=case.completion, mutations=mutations,
                    oracle=case.oracle)
        directory = Path(root) / "tests" / "fixtures" / (TOPIC + "_" + case.variant)
        manifest = dict(schema_version=1, id=name, rule=case.rule, facets=list(case.facets),
                        evidence=case.evidence, standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=case.completion, stderr=""))
        spec["path"], spec["manifest"] = directory.relative_to(root).as_posix() + "/fixture.json", manifest
        specs[name] = spec
        files[directory / "source.f90"] = raw
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def without_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    return "\n\n".join(paragraph for paragraph in paragraphs if not paragraph.startswith(prefix))


def sync_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    covered_rules = {spec["rule"] for spec in specs.values()}
    for rule, pending in COMMAND_PENDING.items():
        if rule in by_rule:
            by_rule[rule].setdefault("pending", {}).update(pending)
    for rule, pending in TRIG_ARGUMENT_PENDING.items():
        if rule in by_rule:
            by_rule[rule].setdefault("pending", {}).update(pending)
    for rule, pending in COSPI_PENDING.items():
        if rule in by_rule:
            by_rule[rule]["pending"] = dict(pending)
    for row in result["requirements"]:
        if row["id"] not in covered_rules:
            row["oracle"] = without_owned_paragraph(row.get("oracle", ""), row["id"] + " intrinsics_16_9_f fixture: ")
            row["oracle_limitation"] = without_owned_paragraph(
                row.get("oracle_limitation", ""), row["id"] + " intrinsics_16_9_f boundaries: ")
    for spec in specs.values():
        row = by_rule[spec["rule"]]
        if not set(spec["facets"]) <= set(row["facets"]):
            raise ValueError("selected facets changed for " + spec["rule"])
        for facet in spec["facets"]:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = spec["rule"] + " intrinsics_16_9_f fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + spec["oracle"])
        limit_prefix = spec["rule"] + " intrinsics_16_9_f boundaries: "
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""), limit_prefix,
            limit_prefix + "This packet supplies only the listed single-image f2023 positive-control or effect facets. "
            "It does not assert diagnostics for unnumbered Clause 16 restrictions, approximate transcendental values, "
            "processor-dependent command-argument support or command-name concepts, source-review renewal, "
            "evidence-link approval, or unrelated pending facets.")
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
    section_specs = [spec for spec in build_corpus(root)[1].values() if spec["section"] == section]
    covered = sum(len(spec["facets"]) for spec in section_specs)
    summary = (SUMMARY_BEGIN + "\n"
        f"\n## Intrinsics 16.9.F runtime observations\n\n"
        f"This batch adds {len(section_specs)} generated f2023 runtime fixtures for {section}, covering {covered} "
        "portable pending facets with exact integer, logical, kind, shape/rank, or exactly representable zero-value "
        "oracles. Feature mutations are conforming source substitutions that must compile and fail at run time on both "
        "toolchains. Approximate COS/COSD/COSH/COSPI values and nonzero command-argument support remain pending where "
        "the standard provides no portable oracle.\n" + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("fixture summary boundaries changed for " + section)
        head, tail = before.split(SUMMARY_BEGIN)
        _, rest_tail = tail.split(SUMMARY_END)
        before = head + summary + rest_tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    generated = "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n"
    return before + begin + generated + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        section_specs = {key: value for key, value in specs.items() if value["section"] == section}
        updated = sync_catalogue(catalogue, section_specs)
        updated_catalogues[rel] = updated
        updated_views[VIEWS[section]] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for rel, updated in updated_catalogues.items():
            if json.loads((root / rel).read_text()) != updated:
                stale.append(rel)
        for rel, text in updated_views.items():
            if (root / rel).read_text() != text:
                stale.append(rel)
        if stale:
            raise ValueError("stale intrinsics_16_9_f generated files: " + ", ".join(stale))
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
        raise ValueError("complete parent source changed for " + spec["id"])
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span lost parent binding")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def std_args(compiler, std):
    name = Path(str(compiler)).name.lower()
    if "lfortran" in name:
        return ["--std=" + std]
    return ["-std=" + std]


def compile_and_run(workdir, compiler, std, source_bytes, expected_stdout):
    source = workdir / "source.f90"
    exe = workdir / "program"
    source.write_bytes(source_bytes)
    cmd = [str(compiler)] + std_args(compiler, std) + ["source.f90", "-o", "program"]
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
    if comp.returncode != 0:
        return "compile-fail", comp.stdout + comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
    if run.returncode == 0 and run.stdout == expected_stdout and run.stderr == "":
        return "pass", run.stdout + run.stderr
    return "run-fail", run.stdout + run.stderr


def check_mutations(root, compiler, std, inject_survivor=False):
    root = Path(root)
    specs = generate(root)
    workspace = root / ("." + TOPIC + "_mutation_runs") / sha((str(compiler) + std).encode())[:12]
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    failures, checked = [], 0
    try:
        for spec in specs.values():
            parent_dir = workspace / (spec["variant"] + "_parent")
            parent_dir.mkdir()
            status, output = compile_and_run(parent_dir, compiler, std, spec["source"].encode("ascii"), spec["completion"])
            if status != "pass":
                failures.append(spec["id"] + " parent did not pass (" + status + "):\n" + output)
                continue
            for mutation in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mutation["id"])
                case_dir.mkdir()
                mutant = spec["source"].encode("ascii") if inject_survivor and checked == 1 else mutate_source(spec, mutation)
                status, output = compile_and_run(case_dir, compiler, std, mutant, spec["completion"])
                if status == "compile-fail":
                    failures.append(spec["id"] + ":" + mutation["id"] + " failed to compile:\n" + output)
                elif status == "pass":
                    failures.append(spec["id"] + ":" + mutation["id"] + " survived")
        if failures:
            raise SystemExit("\n\n".join(failures[:20]))
        return checked
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
    parser.add_argument("--inject-surviving-mutant", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogues, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogues and --mutation-check are separate operations")
    if args.inject_surviving_mutant and not args.mutation_check:
        parser.error("--inject-surviving-mutant requires --mutation-check")
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        checked = check_mutations(args.root, args.compiler, args.std, args.inject_surviving_mutant)
        print(f"Mutation-checked {checked} intrinsics_16_9_f feature mutations; all compiled and failed at run time.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_f cases, "
          f"{sum(len(spec['facets']) for spec in specs.values())} facets, "
          f"{sum(len(spec['mutations']) for spec in specs.values())} mutations.")


if __name__ == "__main__":
    main()
