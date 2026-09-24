#!/usr/bin/env python3
"""Generate Fortran 2023 Clause 16.9.22-16.9.27 intrinsic fixtures."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "intrinsics_16_9_d"
SECTIONS = ("16.9.22", "16.9.23", "16.9.24", "16.9.25", "16.9.26", "16.9.27")
CATALOGUES = {
    "16.9.22": "doc/catalogues/atan2_16_9_22.json",
    "16.9.23": "doc/catalogues/atan2d_16_9_23.json",
    "16.9.25": "doc/catalogues/atand_16_9_25.json",
    "16.9.26": "doc/catalogues/atanh_16_9_26.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in SECTIONS}
SUMMARY_BEGIN = "<!-- BEGIN INTRINSICS 16.9.D FIXTURES -->"
SUMMARY_END = "<!-- END INTRINSICS 16.9.D FIXTURES -->"
PENDING_RESTORES = {
    "S16.9.22-003": {
        "atan2-not-both-zero-when-y-zero":
            "Left pending by intrinsics_16_9_d review follow-up: this is an unnumbered restriction on the program; no diagnostic is required, and a Y=0/X-nonzero positive control does not observe the prohibited Y=0/X=0 case."
    },
    "S16.9.23-003": {
        "atan2d-y-real":
            "Left pending by intrinsics_16_9_d review follow-up: this unnumbered argument restriction can be used only as a conforming positive control here; no portable runtime assertion with a load-bearing feature mutant distinguishes the real-Y property without relying on processor-dependent degree approximation quality.",
        "atan2d-not-both-zero-when-y-zero":
            "Left pending by intrinsics_16_9_d review follow-up: this is an unnumbered restriction on the program; no diagnostic is required, and a Y=0/X-nonzero positive control does not observe the prohibited Y=0/X=0 case."
    },
    "S16.9.22-005": {
        "atan2-range-minus-pi-through-pi":
            "Left pending by intrinsics_16_9_d review follow-up: a strictly portable executable oracle for the exact -pi through pi bound is not available without choosing a processor approximation to pi; weaker enclosing constants such as [-4,4] are not the declared facet."
    },
    "S16.9.23-005": {
        "atan2d-degree-result-range":
            "Left pending by intrinsics_16_9_d review follow-up: the only exact property stated here is the broad [-180, 180] degree range, which does not distinguish an ATAN2 radian substitution because ATAN2's radian principal values also lie inside that interval; the degree approximation has no portable error bound."
    },
    "S16.9.25-003": {
        "atand-y-real-when-present":
            "Left pending by intrinsics_16_9_d review follow-up: this unnumbered argument restriction can be used only as a conforming positive control here; no portable runtime assertion with a load-bearing feature mutant distinguishes the real-Y property without relying on processor-dependent degree approximation quality.",
        "atand-x-real-without-y":
            "Left pending by intrinsics_16_9_d review follow-up: this unnumbered argument restriction can be used only as a conforming positive control here; the one-argument degree range does not distinguish an ATAN radian substitution.",
        "atand-not-both-zero-when-y-zero":
            "Left pending by intrinsics_16_9_d review follow-up: this is an unnumbered restriction on the program; no diagnostic is required, and a Y=0/X-nonzero positive control does not observe the prohibited Y=0/X=0 case."
    },
    "S16.9.25-005": {
        "atand-one-argument-degree-range":
            "Left pending by intrinsics_16_9_d review follow-up: the exact [-90, 90] range for one-argument ATAND does not distinguish an ATAN radian substitution because ATAN's radian result range lies inside it; the degree approximation has no portable error bound."
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identifier(rule: str, variant: str) -> str:
    return rule.replace('.', '_').replace('-', '_') + f"_valid__{TOPIC}_{variant}"


@dataclass(frozen=True)
class Case:
    section: str
    variant: str
    rule: str
    facets: tuple[str, ...]
    evidence: str
    source: str
    mutations: tuple[tuple[str, str, str], ...]
    oracle: str

    @property
    def completion(self) -> str:
        return "INTRINSICS 16.9.D " + self.variant.upper().replace("_", " ") + " OK\n"


def program(name: str, body: str, completion: str) -> str:
    return f"""program i169d_{name}
  implicit none
{body}  write(*,'(a)') '{completion.rstrip()}'
contains
  subroutine require_true(label, condition)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_complex_kind(label, value)
    character(len=*), intent(in) :: label
    complex(kind=kind(0.0d0)), intent(in) :: value
    call require_true(label, kind(value) == kind(0.0d0))
  end subroutine require_complex_kind
end program i169d_{name}
"""


def atan2_arguments_source(completion):
    return program("atan2_arguments", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: arg_y, arg_x, high_y, high_x
  real(kind=RK) :: sign_result
  arg_y = 1.0_RK
  arg_x = 2.0_RK
  sign_result = atan2(arg_y, arg_x)
  call require_true('atan2 real y reaches positive radian branch', &
       sign_result > 0.0_RK .and. sign_result < 4.0_RK)
  high_y = 1.0_RK
  high_x = 2.0_RK
  call require_true('atan2 same kind operands keep x kind', &
       kind(atan2(high_y, high_x)) == kind(high_x))
""", completion)


def two_arg_arguments_source(name, intrinsic, limit, completion):
    return program(name + "_arguments", f"""  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: high_y, high_x
  high_y = 1.0_RK
  high_x = 2.0_RK
  call require_true('{name} same kind operands keep x kind', &
       kind({intrinsic}(high_y, high_x)) == kind(high_x))
""", completion)


def atand_arguments_source(completion):
    return program("atand_arguments", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y, x
  y = 1.0_RK
  x = 2.0_RK
  call require_true('atand same kind operands keep x kind', kind(atand(y, x)) == kind(x))
""", completion)


def atanpi_arguments_source(completion):
    return program("atanpi_arguments", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y, x, one_arg, two_arg
  y = 1.0_RK
  x = 2.0_RK
  two_arg = atanpi(y, x)
  call require_true('atanpi real y positive control in half revolution range', &
       two_arg == two_arg .and. two_arg >= -1.0_RK .and. two_arg <= 1.0_RK)
  one_arg = atanpi(x)
  call require_true('atanpi real x absent y control in half revolution range', &
       one_arg == one_arg .and. one_arg >= -0.5_RK .and. one_arg <= 0.5_RK)
  call require_true('atanpi same kind operands keep x kind', kind(atanpi(y, x)) == kind(x))
""", completion)


def atanh_arguments_source(completion):
    return program("atanh_arguments", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: real_x, real_result
  complex(kind=RK) :: complex_x, complex_result
  real_x = 0.25_RK
  complex_x = cmplx(0.0_RK, 2.0_RK, kind=RK)
  real_result = atanh(real_x)
  complex_result = atanh(complex_x)
  call require_true('atanh real argument keeps real kind', kind(real_result) == kind(real_x))
  call require_true('atanh complex argument keeps complex kind', kind(complex_result) == kind(complex_x))
  call require_true('atanh complex argument reaches bounded result', &
       aimag(complex_result) >= -1.6_RK .and. aimag(complex_result) <= 1.6_RK)
""", completion)


def elemental_two_arg_source(name, intrinsic, completion):
    return program(name + "_elemental", f"""  real :: y(3), x(3)
  y = [1.0, 0.5, -1.0]
  x = [2.0, 2.0, 2.0]
  associate(observed => {intrinsic}(y, x))
    call require_true('{name} elemental rank one result', rank(observed) == 1)
    call require_true('{name} elemental extent follows arguments', size(observed) == 3)
  end associate
""", completion)


def elemental_one_arg_source(name, intrinsic, completion):
    return program(name + "_elemental", f"""  real :: x(3)
  x = [-0.5, 0.0, 0.5]
  associate(observed => {intrinsic}(x))
    call require_true('{name} elemental rank one result', rank(observed) == 1)
    call require_true('{name} elemental extent follows argument', size(observed) == 3)
  end associate
""", completion)


def characteristics_two_arg_source(name, intrinsic, completion):
    return program(name + "_characteristics", f"""  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y(2), x(2)
  y = [1.0_RK, -1.0_RK]
  x = [2.0_RK, 2.0_RK]
  associate(result => {intrinsic}(y, x))
    call require_true('{name} result kind same as x', kind(result) == kind(x))
    call require_true('{name} result rank same as x', rank(result) == rank(x))
    call require_true('{name} result extent same as x', size(result) == size(x))
  end associate
""", completion)


def characteristics_one_arg_source(name, intrinsic, completion):
    return program(name + "_characteristics", f"""  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: x(2)
  x = [-0.5_RK, 0.5_RK]
  associate(result => {intrinsic}(x))
    call require_true('{name} result kind same as x', kind(result) == kind(x))
    call require_true('{name} result rank same as x', rank(result) == rank(x))
    call require_true('{name} result extent same as x', size(result) == size(x))
  end associate
""", completion)


def atanh_characteristics_source(completion):
    return program("atanh_characteristics", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: real_x(2)
  complex(kind=RK) :: complex_x
  real_x = [-0.25_RK, 0.25_RK]
  complex_x = cmplx(0.0_RK, 0.5_RK, kind=RK)
  associate(real_result => atanh(real_x))
    call require_true('atanh real result kind same as x', kind(real_result) == kind(real_x))
    call require_true('atanh real result extent same as x', size(real_result) == size(real_x))
  end associate
  call require_true('atanh complex expression kind same as x', kind(atanh(complex_x)) == kind(complex_x))
  call require_complex_kind('atanh complex expression type discriminator', atanh(complex_x))
""", completion)


def atan2_values_source(completion):
    return program("atan2_values", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: pos_value, zero_value, neg_value
  real(kind=RK) :: y_pos, y_neg, y_zero, x_pos, x_neg
  y_pos = 1.0_RK
  y_neg = -1.0_RK
  y_zero = 0.0_RK
  x_pos = 2.0_RK
  x_neg = -2.0_RK
  pos_value = atan2(y_pos, x_neg)
  call require_true('atan2 positive y gives positive result', pos_value > 0.0_RK)
  zero_value = atan2(y_zero, x_pos)
  call require_true('atan2 zero y positive x result is y', zero_value == y_zero)
  neg_value = atan2(y_neg, x_pos)
  call require_true('atan2 negative y gives negative result', neg_value < 0.0_RK)
""", completion)


def atan2d_range_source(completion):
    return program("atan2d_range", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: result
  result = atan2d(1.0_RK, -1.0_RK)
  call require_true('atan2d result lies in degree range', &
       result >= -180.0_RK .and. result <= 180.0_RK)
""", completion)


def atan2pi_range_source(completion):
    return program("atan2pi_range", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: result
  result = atan2pi(1.0_RK, -1.0_RK)
  call require_true('atan2pi result lies in half revolution range', &
       result >= -1.0_RK .and. result <= 1.0_RK)
""", completion)


def atand_values_source(completion):
    return program("atand_values", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y, x, observed, reference
  y = 1.0_RK
  x = 2.0_RK
  observed = atand(y, x)
  reference = atan2d(y, x)
  call require_true('atand two argument result matches atan2d', observed == reference)
""", completion)


def atanh_range_source(completion):
    return program("atanh_complex_range", """  integer, parameter :: RK = kind(0.0d0)
  complex(kind=RK) :: x, y
  real(kind=RK) :: imag_part
  x = cmplx(0.0_RK, 2.0_RK, kind=RK)
  y = atanh(x)
  imag_part = aimag(y)
  call require_true('atanh complex imaginary part lies in enclosing radian range', &
       imag_part >= -1.6_RK .and. imag_part <= 1.6_RK)
""", completion)


def atanpi_values_source(completion):
    return program("atanpi_values", """  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y, x, observed, reference, one_arg
  y = 1.0_RK
  x = 2.0_RK
  observed = atanpi(y, x)
  reference = atan2pi(y, x)
  call require_true('atanpi two argument result matches atan2pi', observed == reference)
  one_arg = atanpi(10.0_RK)
  call require_true('atanpi one argument result lies in half revolution range', &
       one_arg >= -0.5_RK .and. one_arg <= 0.5_RK)
""", completion)


def make_cases():
    raw = []

    def add(section, variant, rule, facets, evidence, source_func, mutations, oracle):
        completion = "INTRINSICS 16.9.D " + variant.upper().replace("_", " ") + " OK\n"
        raw.append(Case(section, variant, rule, tuple(facets), evidence, source_func(completion), tuple(mutations), oracle))

    add("16.9.22", "atan2_arguments", "S16.9.22-003",
        ["atan2-y-real", "atan2-x-same-type-kind-as-y"],
        "positive-control", atan2_arguments_source,
        [("y-real-degree-intrinsic", "sign_result = atan2(arg_y, arg_x)", "sign_result = atan2d(arg_y, arg_x)"),
         ("same-kind-default-cast", "kind(atan2(high_y, high_x))", "kind(atan2(real(high_y), real(high_x)))")],
        "ATAN2 argument control uses real Y and same-kind X with distinct sign and kind assertions.")
    add("16.9.22", "atan2_elemental", "S16.9.22-002", ["atan2-elemental-function-class"],
        "effect", lambda c: elemental_two_arg_source("atan2", "atan2", c),
        [("array-to-singleton-call", "atan2(y, x))", "atan2(y(1:1), x(1:1)))")],
        "ATAN2 elemental fixture applies the function to rank-one conformable arrays and observes the expression rank and extent.")
    add("16.9.22", "atan2_characteristics", "S16.9.22-004", ["atan2-result-same-as-x"],
        "effect", lambda c: characteristics_two_arg_source("atan2", "atan2", c),
        [("array-to-singleton-result", "atan2(y, x))", "atan2(y(1:1), x(1:1)))")],
        "ATAN2 result-characteristics fixture checks kind, rank, and shape match X without asserting an approximate angle.")
    add("16.9.22", "atan2_values", "S16.9.22-005",
        ["atan2-positive-when-y-positive", "atan2-zero-y-positive-x-result-y", "atan2-negative-when-y-negative"],
        "effect", atan2_values_source,
        [("positive-swap-arguments", "pos_value = atan2(y_pos, x_neg)", "pos_value = atan2(x_neg, y_pos)"),
         ("zero-swap-arguments", "zero_value = atan2(y_zero, x_pos)", "zero_value = atan2(x_pos, y_zero)"),
         ("negative-swap-arguments", "neg_value = atan2(y_neg, x_pos)", "neg_value = atan2(x_pos, y_neg)")],
        "ATAN2 value fixture checks the sign rules and exact Y result for Y=0/X>0, leaving the exact pi-bounded range pending.")

    add("16.9.23", "atan2d_arguments", "S16.9.23-003",
        ["atan2d-x-same-type-kind-as-y"], "positive-control",
        lambda c: two_arg_arguments_source("atan2d", "atan2d", "180.0", c),
        [("same-kind-default-cast", "kind(atan2d(high_y, high_x))", "kind(atan2d(real(high_y), real(high_x)))")],
        "ATAN2D argument control checks only the same-kind X/Y property with a kind-changing feature mutant.")
    add("16.9.23", "atan2d_elemental", "S16.9.23-002", ["atan2d-elemental-function-class"],
        "effect", lambda c: elemental_two_arg_source("atan2d", "atan2d", c),
        [("array-to-singleton-call", "atan2d(y, x))", "atan2d(y(1:1), x(1:1)))")],
        "ATAN2D elemental fixture applies the function to rank-one conformable arrays and observes expression rank and extent.")
    add("16.9.23", "atan2d_characteristics", "S16.9.23-004", ["atan2d-result-same-as-x"],
        "effect", lambda c: characteristics_two_arg_source("atan2d", "atan2d", c),
        [("array-to-singleton-result", "atan2d(y, x))", "atan2d(y(1:1), x(1:1)))")],
        "ATAN2D result-characteristics fixture checks kind, rank, and shape match X.")
    add("16.9.25", "atand_arguments", "S16.9.25-003",
        ["atand-x-same-kind-as-y-when-y-present"],
        "positive-control", atand_arguments_source,
        [("same-kind-default-cast", "kind(atand(y, x))", "kind(atand(real(y), real(x)))")],
        "ATAND argument control checks only same-kind two-argument operands with a kind-changing feature mutant.")
    add("16.9.25", "atand_elemental", "S16.9.25-002", ["atand-elemental-function-class"],
        "effect", lambda c: elemental_one_arg_source("atand", "atand", c),
        [("array-to-singleton-call", "atand(x))", "atand(x(1:1)))")],
        "ATAND elemental fixture applies one-argument ATAND to a rank-one array and observes expression rank and extent.")
    add("16.9.25", "atand_characteristics", "S16.9.25-004", ["atand-result-same-as-x"],
        "effect", lambda c: characteristics_one_arg_source("atand", "atand", c),
        [("array-to-singleton-result", "atand(x))", "atand(x(1:1)))")],
        "ATAND result-characteristics fixture checks kind, rank, and shape match one-argument X.")
    add("16.9.25", "atand_values", "S16.9.25-005",
        ["atand-two-argument-same-as-atan2d"],
        "effect", atand_values_source,
        [("wrong-radian-intrinsic", "observed = atand(y, x)", "observed = atan(y, x)")],
        "ATAND value fixture compares the two-argument result exactly with ATAN2D and does not claim the non-discriminating one-argument degree range.")

    add("16.9.26", "atanh_arguments", "S16.9.26-003", ["atanh-x-real-or-complex"],
        "positive-control", atanh_arguments_source,
        [("complex-call-removed", "complex_result = atanh(complex_x)", "complex_result = complex_x")],
        "ATANH argument control calls ATANH with both real and complex X and observes same-kind assignment.")
    add("16.9.26", "atanh_elemental", "S16.9.26-002", ["atanh-elemental-function-class"],
        "effect", lambda c: elemental_one_arg_source("atanh", "atanh", c),
        [("array-to-singleton-call", "atanh(x))", "atanh(x(1:1)))")],
        "ATANH elemental fixture applies ATANH to a rank-one real array and observes expression rank and extent.")
    add("16.9.26", "atanh_characteristics", "S16.9.26-004", ["atanh-result-same-as-x"],
        "effect", atanh_characteristics_source,
        [("real-array-to-singleton-result", "atanh(real_x))", "atanh(real_x(1:1)))"),
         ("complex-expression-default-kind", "kind(atanh(complex_x))", "kind(atanh(cmplx(real(complex_x), aimag(complex_x))))")],
        "ATANH result-characteristics fixture directly inquires on ATANH expressions and uses a complex-kind dummy discriminator for the complex result type.")
    add("16.9.26", "atanh_complex_range", "S16.9.26-005", ["atanh-complex-imaginary-radian-range"],
        "effect", atanh_range_source,
        [("wrong-hyperbolic-intrinsic", "y = atanh(x)", "y = tanh(x)")],
        "ATANH complex-range fixture checks an exact enclosing bound of 1.6 for the source-stated AIMAG interval -pi/2 through pi/2.")

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
    matches = [i for i, p in enumerate(paragraphs) if p.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned paragraph " + prefix)
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(p for p in paragraphs if p)


def without_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    return "\n\n".join(p for p in paragraphs if not p.startswith(prefix))


def sync_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    covered_rules = {spec["rule"] for spec in specs.values()}
    for row in result["requirements"]:
        if row["id"] not in covered_rules:
            fixture_prefix = row["id"] + " intrinsics_16_9_d fixture: "
            limit_prefix = row["id"] + " intrinsics_16_9_d boundaries: "
            row["oracle"] = without_owned_paragraph(row.get("oracle", ""), fixture_prefix)
            row["oracle_limitation"] = without_owned_paragraph(row.get("oracle_limitation", ""), limit_prefix)
    for spec in specs.values():
        row = by_rule[spec["rule"]]
        if not set(spec["facets"]) <= set(row["facets"]):
            raise ValueError("facet moved or removed for " + spec["rule"])
        for facet in spec["facets"]:
            row.setdefault("pending", {}).pop(facet, None)
        prefix = spec["rule"] + " intrinsics_16_9_d fixture: "
        row["oracle"] = owned_paragraph(row.get("oracle", ""), prefix, prefix + spec["oracle"])
        limit_prefix = spec["rule"] + " intrinsics_16_9_d boundaries: "
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""), limit_prefix,
            limit_prefix + "This packet supplies only the listed positive-control or effect facets. "
            "It does not assert exact transcendental approximations, IEEE signed-zero behavior, "
            "diagnostics for unnumbered restrictions, coarray behavior, source-review renewal, "
            "fixture approval for unrelated facets, or compiler-consensus oracles.")
    for rule, pending in PENDING_RESTORES.items():
        row = by_rule.get(rule)
        if not row:
            continue
        covered = set()
        for spec in specs.values():
            if spec["rule"] == rule:
                covered.update(spec["facets"])
        for facet, reason in pending.items():
            if facet not in covered:
                row.setdefault("pending", {})[facet] = reason
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
        "## Intrinsics 16.9.D runtime observations\n\n"
        "This batch adds bounded generated fixtures for ATAN2, ATAN2D, ATAND, "
        "and ATANH. ATAN2PI and ATANPI remain pending because the reference "
        "compiler fails to link variable calls to those intrinsics. The fixtures assert only result characteristics, "
        "source-stated ranges, ATAN2 sign/zero rules, and exact same-result relationships; "
        "processor-dependent approximation facets remain pending.\n" + SUMMARY_END)
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
        section_specs = {k: v for k, v in specs.items() if v["section"] == section}
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
            raise ValueError("stale intrinsics_16_9_d generated files: " + ", ".join(stale))
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
    comp = subprocess.run(cmd, cwd=workdir, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=30)
    if comp.returncode != 0:
        return "compile-fail", comp.stdout + comp.stderr
    run = subprocess.run([str(exe)], cwd=workdir, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=30)
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
                    head = output.splitlines()[0][:120] if output else status
                    skipped.append(spec["id"] + ":" + status + ":" + head)
                    continue
                failures.append(spec["id"] + " parent did not pass (" + status + "):\n" + output)
                continue
            for mutation in spec["mutations"]:
                checked += 1
                case_dir = workspace / (spec["variant"] + "_" + mutation["id"])
                case_dir.mkdir()
                status, output = compile_and_run(case_dir, compiler, std, mutate_source(spec, mutation))
                if status == "pass":
                    failures.append(spec["id"] + ":" + mutation["id"] + " survived")
                elif status != "run-fail":
                    failures.append(spec["id"] + ":" + mutation["id"] + " invalid mutant (" + status + "):\n" + output)
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
        print(f"Mutation-checked {checked} intrinsics_16_9_d mutations; {len(skipped)} parents skipped.")
        if skipped:
            print("Skipped parents:")
            for row in skipped:
                print("  " + row)
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} intrinsics_16_9_d cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets, "
          f"{sum(len(s['mutations']) for s in specs.values())} mutations.")


if __name__ == "__main__":
    main()
