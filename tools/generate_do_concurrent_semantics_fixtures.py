#!/usr/bin/env python3
"""DO CONCURRENT additional-semantics fixtures for Fortran 2023 11.1.7.5."""

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha


ROOT = Path(__file__).resolve().parents[1]
SECTION = "11.1.7.5"
CATALOGUE = "doc/catalogues/additional_semantics_for_do_concurrent_constructs_11_1_7_5.json"
VIEW = "doc/fortran_2023_11_1_7_5.md"
PREFIX = "do_concurrent_semantics_"
SUMMARY_BEGIN = "<!-- BEGIN DO CONCURRENT SEMANTICS FIXTURES -->"
SUMMARY_END = "<!-- END DO CONCURRENT SEMANTICS FIXTURES -->"

RULE_LOCAL = "S11.1.7.5-002"
RULE_LOCAL_INIT = "S11.1.7.5-003"
RULE_REDUCE_INITIAL = "S11.1.7.5-006"
RULE_REDUCE_FORMS = "S11.1.7.5-007"
RULE_REDUCE_FINAL = "S11.1.7.5-008"
RULE_REDUCE_ORDER = "S11.1.7.5-009"
RULE_SHARED = "S11.1.7.5-010"

FACETS_BY_RULE = {
    RULE_LOCAL: ("local-hides-outside-variable", "local-nonpointer-same-bounds"),
    RULE_LOCAL_INIT: (
        "local-initial-undefined-source-control",
        "local-assigned-before-use-control",
        "local-init-copies-outside-definition-status",
        "local-init-outside-defined-source-control",
    ),
    RULE_REDUCE_INITIAL: (
        "reduce-plus-initial-zero",
        "reduce-times-initial-one",
        "reduce-logical-initial-identities",
        "reduce-bitwise-initial-identities",
        "reduce-minmax-initial-extremes",
    ),
    RULE_REDUCE_FORMS: (
        "reduce-variable-allowed-binary-left-form-control",
        "reduce-variable-allowed-binary-right-form-control",
        "reduce-variable-allowed-function-form-control",
        "reduce-variable-same-form-source-control",
    ),
    RULE_REDUCE_FINAL: (
        "reduce-final-integer-result",
        "reduce-final-logical-result",
        "reduce-outside-updated-only-at-termination",
    ),
    RULE_REDUCE_ORDER: (
        "reduce-combination-order-unobservable-source-control",
        "floating-reduce-order-sensitive-oracle-excluded",
    ),
    RULE_SHARED: ("shared-refers-to-outside-final-state", "shared-cross-iteration-definition-source-control"),
}
EVIDENCE_BY_RULE = {
    RULE_REDUCE_FORMS: "positive-control",
    RULE_SHARED: "positive-control",
}

EXPECTED_REMAINING = {
    RULE_LOCAL: {
        "local-preserves-allowed-attributes",
        "local-excludes-disallowed-attributes",
    },
    RULE_LOCAL_INIT: set(),
    RULE_REDUCE_INITIAL: set(),
    RULE_REDUCE_FORMS: {"reduce-variable-disallowed-appearance-source-control"},
    RULE_REDUCE_FINAL: set(),
    RULE_REDUCE_ORDER: set(),
    RULE_SHARED: {
        "shared-cross-iteration-status-inquiry-source-control",
        "shared-noncontiguous-contiguous-inout-source-control",
    },
}

ORACLE_PREFIXES = {
    RULE_LOCAL: "S11.1.7.5-002 LOCAL construct-entity runtime fixtures: ",
    RULE_LOCAL_INIT: "S11.1.7.5-003 LOCAL/LOCAL_INIT defined-use runtime fixtures: ",
    RULE_REDUCE_INITIAL: "S11.1.7.5-006 REDUCE identity runtime fixtures: ",
    RULE_REDUCE_FORMS: "S11.1.7.5-007 REDUCE appearance-form runtime fixtures: ",
    RULE_REDUCE_FINAL: "S11.1.7.5-008 REDUCE final-update runtime fixtures: ",
    RULE_REDUCE_ORDER: "S11.1.7.5-009 REDUCE order-latitude source-control fixtures: ",
    RULE_SHARED: "S11.1.7.5-010 SHARED final-state runtime fixtures: ",
}
LIMIT_PREFIXES = {
    rule: prefix.replace(" fixtures: ", " fixture boundaries: ")
    for rule, prefix in ORACLE_PREFIXES.items()
}
RETIRED_PREFIXES = {
    RULE_REDUCE_INITIAL: {
        "oracle": ("S11.1.7.5-006 integer REDUCE identity runtime fixtures: ",),
        "oracle_limitation": ("S11.1.7.5-006 integer REDUCE identity runtime fixture boundaries: ",),
    },
}

ORACLES = {
    RULE_LOCAL: ORACLE_PREFIXES[RULE_LOCAL] + (
        "one complete run/effect/f2023 program declares an outside scalar sentinel 17 and an outside "
        "integer array with bounds 2:5 and sentinel -444. A one-iteration DO CONCURRENT construct gives "
        "both names LOCAL locality, assigns both construct entities before any value reference, stores "
        "lbound/ubound inquiries and a local scalar value in distinct SHARED result elements, and then "
        "checks after termination that the outside scalar and every outside array element are unchanged. "
        "Removing the LOCAL locality spec remains conforming because there is only one iteration and then "
        "changes the outside sentinels, so the locality feature is load-bearing."
    ),
    RULE_LOCAL_INIT: ORACLE_PREFIXES[RULE_LOCAL_INIT] + (
        "one complete run/effect/f2023 program gives one scalar LOCAL and one scalar LOCAL_INIT locality "
        "in a one-iteration DO CONCURRENT construct. The LOCAL scalar is assigned before use; the "
        "LOCAL_INIT scalar reads the defined outside value 7 at iteration start, contributes it to a "
        "distinct result element, and is then modified locally. After termination the outside LOCAL and "
        "LOCAL_INIT sentinels remain -222 and 7, while the result is 107. Separate locality-removal "
        "mutants for LOCAL and LOCAL_INIT stay conforming in the one-iteration construct and fail the "
        "outside-sentinel checks."
    ),
    RULE_REDUCE_INITIAL: ORACLE_PREFIXES[RULE_REDUCE_INITIAL] + (
        "two complete run/effect/f2023 programs use default INTEGER and default LOGICAL reductions whose "
        "operations are order-independent on the selected operands. The integer outside sentinels are "
        "nonidentity values. The + case starts from 50 and contributes 1,2,3,4 to reach 60; * starts "
        "from 3 and contributes four factors of 2 to reach 48; IOR/IAND/IEOR use hand-derived bit "
        "patterns 23/241/33; MAX/MIN use ordinary small integer contributions that dominate the table "
        "extremes and yield 12/16. The logical identity case uses .AND. with all true contributions, "
        ".OR. with all false contributions, .EQV. with all true contributions, and .NEQV. with all "
        "false contributions; changing the Table 11.1 identity for the selected operation would change "
        "each final result. The oracle constants are hand-computed integers/logicals, not compiler "
        "consensus or floating-point sums."
    ),
    RULE_REDUCE_FORMS: ORACLE_PREFIXES[RULE_REDUCE_FORMS] + (
        "one complete run/effect/f2023 program uses the three p4-permitted intrinsic-assignment forms: "
        "`variable = variable + expr`, `variable = expr + variable`, and `variable = max(expr, variable)`. "
        "Each REDUCE variable has the same syntactic form at every appearance within its construct. The "
        "final integer results 16, 16 and 12 are independent of iteration-combination order, and paired "
        "operator/function substitutions keep each mutant conforming while changing the final value."
    ),
    RULE_REDUCE_FINAL: ORACLE_PREFIXES[RULE_REDUCE_FINAL] + (
        "two complete run/effect/f2023 programs initialize outside INTEGER and LOGICAL reduction variables "
        "to defined sentinels and observe only after DO CONCURRENT termination that the outside variables "
        "have been updated by p5. The integer + case starts from 100 and contributions 1,2,3,4 update it "
        "to 110. The logical case uses .AND., .OR., .EQV. and .NEQV. with operands chosen so every final "
        "value differs from its outside pre-construct value and so .AND.<->.OR. and .EQV.<->.NEQV. "
        "operator substitutions are load-bearing. The body references each REDUCE construct entity by "
        "name in the required reduction assignment form; no source line attempts to observe an outside "
        "variable during an iteration."
    ),
    RULE_REDUCE_ORDER: ORACLE_PREFIXES[RULE_REDUCE_ORDER] + (
        "one complete run/effect/f2023 program documents the order latitude by using only order-independent "
        "default INTEGER + and MAX reductions. No REAL or COMPLEX entity, floating literal, procedure call "
        "counter, I/O ordering, or iteration-order observation appears in the source. Feature substitutions "
        "to different integer reduction operations and a removed contribution are permanent load-bearing "
        "mutants; no fixture requires any particular reduction tree or iteration order."
    ),
    RULE_SHARED: ORACLE_PREFIXES[RULE_SHARED] + (
        "one complete run/effect/f2023 program initializes an outside scalar sentinel -777 and then uses a "
        "one-iteration DO CONCURRENT construct with SHARED locality to assign 411 to that same outside "
        "variable. The result is checked only after termination. Replacing SHARED with LOCAL and deleting "
        "the defining statement are conforming mutants that fail the final-state oracle. The source-control "
        "claim is limited to the generated one-iteration program, which has no other iteration that "
        "references or defines the same SHARED variable."
    ),
}

LIMITATIONS = {
    RULE_LOCAL: LIMIT_PREFIXES[RULE_LOCAL] + (
        "only local-hides-outside-variable and local-nonpointer-same-bounds are represented. Allowed and "
        "excluded attribute propagation facets remain pending. The fixture does not read a LOCAL value "
        "before definition or after the construct, does not infer storage identity, and uses one iteration "
        "only so locality-removal mutants remain conforming."
    ),
    RULE_LOCAL_INIT: LIMIT_PREFIXES[RULE_LOCAL_INIT] + (
        "only the four selected defined-use/source-control facets are represented. Undefined LOCAL initial "
        "values are not read; the source-control evidence is the generated assignment-before-use structure. "
        "Pointer association, default-initialized subobjects, pending I/O and TARGET pointer lifetime are "
        "not tested."
    ),
    RULE_REDUCE_INITIAL: LIMIT_PREFIXES[RULE_REDUCE_INITIAL] + (
        "only default INTEGER +, *, IOR, IAND, IEOR, MAX, MIN and default LOGICAL .AND., .OR., .EQV. "
        "and .NEQV. identities are represented. The logical fixture is retained even though the frozen "
        "target rejects conforming dotted logical reduce-operation syntax; gfortran validates it as the "
        "reference. No REAL, COMPLEX, nondefault kind, IEEE, overflow, representation-width or processor "
        "limit oracle is used."
    ),
    RULE_REDUCE_FORMS: LIMIT_PREFIXES[RULE_REDUCE_FORMS] + (
        "only the three allowed positive appearance forms and same-form source control are represented. "
        "The disallowed-appearance contrast remains pending because p4 is not a numbered constraint and "
        "this packet records no diagnostic expectation for it. The function-form case uses MAX only."
    ),
    RULE_REDUCE_FINAL: LIMIT_PREFIXES[RULE_REDUCE_FINAL] + (
        "only INTEGER + and default LOGICAL .AND., .OR., .EQV. and .NEQV. final results observed after "
        "termination are represented. The fixture does not test intermediate timing, temporary storage, "
        "or a particular reduction-combination order."
    ),
    RULE_REDUCE_ORDER: LIMIT_PREFIXES[RULE_REDUCE_ORDER] + (
        "these facets are source-control/latitude boundaries, not a requirement to exercise multiple "
        "processor orders. The fixture intentionally avoids floating-point reductions and any oracle that "
        "would distinguish permitted reduction trees."
    ),
    RULE_SHARED: LIMIT_PREFIXES[RULE_SHARED] + (
        "only SHARED final-state reference and the generated one-iteration cross-definition source-control "
        "claim are represented. Status-inquiry and noncontiguous-contiguous-dummy restrictions remain "
        "pending until their dependent allocation/pointer/procedure contexts are registered."
    ),
}


def identifier(variant):
    spec = VARIANTS[variant]
    return spec["rule"].replace(".", "_").replace("-", "_") + "_valid__" + PREFIX + variant


def complete_source(variant, rule, facets, declarations, setup, body, checks):
    completion = "DO CONCURRENT SEMANTICS " + variant.upper().replace("_", " ") + " OK"
    lines = [f"! rule: {rule}"]
    lines.extend(f"! covers: {facet}" for facet in facets)
    lines.extend([
        f"program {PREFIX}{variant}",
        "  implicit none",
        "  integer :: checks",
        declarations.rstrip(),
        "  checks = 0",
        setup.rstrip(),
        body.rstrip(),
    ])
    for expression, token in checks:
        lines.extend([
            f"  if ({expression}) then",
            f"    write(*,'(a)') 'DCS:{variant}:{token}'",
            "    error stop",
            "  end if",
            "  checks = checks + 1",
        ])
    lines.extend([
        f"  if (checks /= {len(checks)}) then",
        f"    write(*,'(a)') 'DCS:{variant}:check-count'",
        "    error stop",
        "  end if",
        f"  write(*,'(a)') '{completion}'",
        f"end program {PREFIX}{variant}",
        "",
    ])
    source = "\n".join(line for line in lines if line != "")
    source += "\n"
    return source, completion + "\n"


def mutation(mid, replacements, rationale, *, run_when_parent_fails=False):
    return {
        "id": mid,
        "replacements": list(replacements),
        "rationale": rationale,
        "run_when_parent_fails": run_when_parent_fails,
    }


def site(expected, replacement):
    return {"expected": expected, "replacement": replacement}


def logical_reduce_operations_are_order_independent():
    operations = {
        ".and.": lambda a, b: a and b,
        ".or.": lambda a, b: a or b,
        ".eqv.": lambda a, b: a == b,
        ".neqv.": lambda a, b: a != b,
    }
    values = (False, True)
    for operator in operations.values():
        for a in values:
            for b in values:
                if operator(a, b) != operator(b, a):
                    return False
                for c in values:
                    if operator(operator(a, b), c) != operator(a, operator(b, c)):
                        return False
    return True


def local_entities_source():
    return complete_source(
        "local_entities",
        RULE_LOCAL,
        FACETS_BY_RULE[RULE_LOCAL],
        "\n".join([
            "  integer :: i",
            "  integer :: local_scalar",
            "  integer :: local_array(2:5)",
            "  integer :: result(2:5), lower_seen(2:5), upper_seen(2:5)",
        ]),
        "\n".join([
            "  local_scalar = 17",
            "  local_array = -444",
            "  result = -901",
            "  lower_seen = -902",
            "  upper_seen = -903",
        ]),
        "\n".join([
            "  do concurrent (i = 2:2) local(local_scalar, local_array) shared(result, lower_seen, upper_seen)",
            "    local_scalar = 100 + i",
            "    local_array = -333",
            "    local_array(i) = local_scalar",
            "    result(i) = local_array(i)",
            "    lower_seen(i) = lbound(local_array, 1)",
            "    upper_seen(i) = ubound(local_array, 1)",
            "  end do",
        ]),
        [
            ("local_scalar /= 17", "outside-scalar"),
            ("any(local_array /= -444)", "outside-array"),
            ("result(2) /= 102", "local-value"),
            ("lower_seen(2) /= 2", "lower-bound"),
            ("upper_seen(2) /= 5", "upper-bound"),
        ],
    )


def local_init_source():
    return complete_source(
        "local_init_defined",
        RULE_LOCAL_INIT,
        FACETS_BY_RULE[RULE_LOCAL_INIT],
        "\n".join([
            "  integer :: i",
            "  integer :: local_value, init_value",
            "  integer :: observed(1)",
        ]),
        "\n".join([
            "  local_value = -222",
            "  init_value = 7",
            "  observed = -333",
        ]),
        "\n".join([
            "  do concurrent (i = 1:1) local(local_value) local_init(init_value) shared(observed)",
            "    local_value = 100",
            "    observed(i) = local_value + init_value",
            "    init_value = -77",
            "  end do",
        ]),
        [
            ("observed(1) /= 107", "local-init-copy"),
            ("local_value /= -222", "local-outside"),
            ("init_value /= 7", "local-init-outside"),
        ],
    )


def reduce_identities_source():
    return complete_source(
        "reduce_identities",
        RULE_REDUCE_INITIAL,
        (
            "reduce-plus-initial-zero",
            "reduce-times-initial-one",
            "reduce-bitwise-initial-identities",
            "reduce-minmax-initial-extremes",
        ),
        "\n".join([
            "  integer :: i",
            "  integer :: sum_value, product_value",
            "  integer :: or_value, and_value, xor_value",
            "  integer :: max_value, min_value",
        ]),
        "\n".join([
            "  sum_value = 50",
            "  product_value = 3",
            "  or_value = 16",
            "  and_value = 255",
            "  xor_value = 32",
            "  max_value = -10",
            "  min_value = 99",
        ]),
        "\n".join([
            "  do concurrent (i = 1:4) reduce(+:sum_value)",
            "    sum_value = sum_value + i",
            "  end do",
            "  do concurrent (i = 1:4) reduce(*:product_value)",
            "    product_value = product_value * 2",
            "  end do",
            "  do concurrent (i = 1:3) reduce(ior:or_value) reduce(iand:and_value) reduce(ieor:xor_value)",
            "    or_value = ior(or_value, 2 * i + 1)",
            "    and_value = iand(and_value, 255 - 2**i)",
            "    xor_value = ieor(xor_value, 2 * i + 1)",
            "  end do",
            "  do concurrent (i = 1:4) reduce(max:max_value) reduce(min:min_value)",
            "    max_value = max(max_value, i * 3)",
            "    min_value = min(20 - i, min_value)",
            "  end do",
        ]),
        [
            ("sum_value /= 60", "plus"),
            ("product_value /= 48", "times"),
            ("or_value /= 23", "ior"),
            ("and_value /= 241", "iand"),
            ("xor_value /= 33", "ieor"),
            ("max_value /= 12", "max"),
            ("min_value /= 16", "min"),
        ],
    )


def reduce_logical_identities_source():
    return complete_source(
        "reduce_logical_identities",
        RULE_REDUCE_INITIAL,
        ("reduce-logical-initial-identities",),
        "\n".join([
            "  integer :: i",
            "  logical :: and_identity, or_identity",
            "  logical :: eqv_identity, neqv_identity",
            "  logical :: contribution_guard",
        ]),
        "\n".join([
            "  and_identity = .true.",
            "  or_identity = .false.",
            "  eqv_identity = .true.",
            "  neqv_identity = .true.",
            "  contribution_guard = .false.",
        ]),
        "\n".join([
            "  do concurrent (i = 1:3) reduce(.and.:and_identity) reduce(.or.:or_identity) &",
            "      reduce(.eqv.:eqv_identity) reduce(.neqv.:neqv_identity) reduce(.or.:contribution_guard)",
            "    and_identity = and_identity .and. .true.",
            "    or_identity = or_identity .or. .false.",
            "    eqv_identity = eqv_identity .eqv. .true.",
            "    neqv_identity = neqv_identity .neqv. .false.",
            "    contribution_guard = contribution_guard .or. (i == 2)",
            "  end do",
        ]),
        [
            (".not. and_identity", "and-identity"),
            ("or_identity", "or-identity"),
            (".not. eqv_identity", "eqv-identity"),
            (".not. neqv_identity", "neqv-identity"),
            (".not. contribution_guard", "contribution-guard"),
        ],
    )


def reduce_forms_source():
    return complete_source(
        "reduce_forms",
        RULE_REDUCE_FORMS,
        FACETS_BY_RULE[RULE_REDUCE_FORMS],
        "\n".join([
            "  integer :: i",
            "  integer :: left_value, right_value, function_value",
        ]),
        "\n".join([
            "  left_value = 10",
            "  right_value = 10",
            "  function_value = -5",
        ]),
        "\n".join([
            "  do concurrent (i = 1:3) reduce(+:left_value)",
            "    left_value = left_value + i",
            "  end do",
            "  do concurrent (i = 1:3) reduce(+:right_value)",
            "    right_value = i + right_value",
            "  end do",
            "  do concurrent (i = 1:3) reduce(max:function_value)",
            "    function_value = max(i * 4, function_value)",
            "  end do",
        ]),
        [
            ("left_value /= 16", "left-form"),
            ("right_value /= 16", "right-form"),
            ("function_value /= 12", "function-form"),
        ],
    )


def reduce_final_source():
    return complete_source(
        "reduce_final_update",
        RULE_REDUCE_FINAL,
        ("reduce-final-integer-result", "reduce-outside-updated-only-at-termination"),
        "\n".join([
            "  integer :: i",
            "  integer :: total_value",
        ]),
        "\n".join([
            "  total_value = 100",
        ]),
        "\n".join([
            "  do concurrent (i = 1:4) reduce(+:total_value)",
            "    total_value = total_value + i",
            "  end do",
        ]),
        [
            ("total_value /= 110", "final-update"),
        ],
    )


def reduce_logical_final_source():
    return complete_source(
        "reduce_logical_final_update",
        RULE_REDUCE_FINAL,
        ("reduce-final-logical-result",),
        "\n".join([
            "  integer :: i",
            "  logical :: and_final, or_final",
            "  logical :: eqv_final, neqv_final",
        ]),
        "\n".join([
            "  and_final = .true.",
            "  or_final = .false.",
            "  eqv_final = .true.",
            "  neqv_final = .true.",
        ]),
        "\n".join([
            "  do concurrent (i = 1:3) reduce(.and.:and_final) reduce(.or.:or_final) &",
            "      reduce(.eqv.:eqv_final) reduce(.neqv.:neqv_final)",
            "    and_final = and_final .and. (i /= 2)",
            "    or_final = or_final .or. (i == 2)",
            "    eqv_final = eqv_final .eqv. (i /= 2)",
            "    neqv_final = neqv_final .neqv. (i == 1)",
            "  end do",
        ]),
        [
            ("and_final", "and-final"),
            (".not. or_final", "or-final"),
            ("eqv_final", "eqv-final"),
            ("neqv_final", "neqv-final"),
        ],
    )


def reduce_order_source():
    return complete_source(
        "reduce_order_independent",
        RULE_REDUCE_ORDER,
        FACETS_BY_RULE[RULE_REDUCE_ORDER],
        "\n".join([
            "  integer :: i",
            "  integer :: total_value, maximum_value",
        ]),
        "\n".join([
            "  total_value = 70",
            "  maximum_value = -30",
        ]),
        "\n".join([
            "  do concurrent (i = 1:4) reduce(+:total_value) reduce(max:maximum_value)",
            "    total_value = total_value + i",
            "    maximum_value = max(maximum_value, 5 * i)",
            "  end do",
        ]),
        [
            ("total_value /= 80", "integer-sum"),
            ("maximum_value /= 20", "integer-max"),
        ],
    )


def shared_source():
    return complete_source(
        "shared_final_state",
        RULE_SHARED,
        FACETS_BY_RULE[RULE_SHARED],
        "\n".join([
            "  integer :: i",
            "  integer :: shared_value",
        ]),
        "\n".join([
            "  shared_value = -777",
        ]),
        "\n".join([
            "  do concurrent (i = 1:1) shared(shared_value)",
            "    shared_value = 411",
            "  end do",
        ]),
        [
            ("shared_value /= 411", "outside-value"),
        ],
    )


VARIANTS = {
    "local_entities": {"rule": RULE_LOCAL, "facets": FACETS_BY_RULE[RULE_LOCAL], "source": local_entities_source},
    "local_init_defined": {
        "rule": RULE_LOCAL_INIT,
        "facets": FACETS_BY_RULE[RULE_LOCAL_INIT],
        "source": local_init_source,
    },
    "reduce_identities": {
        "rule": RULE_REDUCE_INITIAL,
        "facets": (
            "reduce-plus-initial-zero",
            "reduce-times-initial-one",
            "reduce-bitwise-initial-identities",
            "reduce-minmax-initial-extremes",
        ),
        "source": reduce_identities_source,
    },
    "reduce_logical_identities": {
        "rule": RULE_REDUCE_INITIAL,
        "facets": ("reduce-logical-initial-identities",),
        "source": reduce_logical_identities_source,
    },
    "reduce_forms": {
        "rule": RULE_REDUCE_FORMS,
        "facets": FACETS_BY_RULE[RULE_REDUCE_FORMS],
        "source": reduce_forms_source,
    },
    "reduce_final_update": {
        "rule": RULE_REDUCE_FINAL,
        "facets": ("reduce-final-integer-result", "reduce-outside-updated-only-at-termination"),
        "source": reduce_final_source,
    },
    "reduce_logical_final_update": {
        "rule": RULE_REDUCE_FINAL,
        "facets": ("reduce-final-logical-result",),
        "source": reduce_logical_final_source,
    },
    "reduce_order_independent": {
        "rule": RULE_REDUCE_ORDER,
        "facets": FACETS_BY_RULE[RULE_REDUCE_ORDER],
        "source": reduce_order_source,
    },
    "shared_final_state": {"rule": RULE_SHARED, "facets": FACETS_BY_RULE[RULE_SHARED], "source": shared_source},
}

MUTATION_PLANS = {
    "local_entities": [
        mutation(
            "remove-local-locality-spec",
            [site(" local(local_scalar, local_array)", "")],
            "single-iteration removal is conforming and changes outside scalar/array sentinels",
        ),
        mutation(
            "substitute-local-with-shared",
            [site("local(local_scalar, local_array)", "shared(local_scalar, local_array)")],
            "single-iteration SHARED substitution is conforming and exposes outside updates",
        ),
    ],
    "local_init_defined": [
        mutation(
            "remove-local-spec",
            [site(" local(local_value)", "")],
            "single-iteration LOCAL removal is conforming and changes the outside local_value",
        ),
        mutation(
            "remove-local-init-spec",
            [site(" local_init(init_value)", "")],
            "single-iteration LOCAL_INIT removal is conforming and changes the outside init_value",
        ),
    ],
    "reduce_identities": [
        mutation(
            "remove-plus-contribution",
            [site("    sum_value = sum_value + i\n", "    sum_value = sum_value + 0\n")],
            "keeps the + reduction form but removes the per-iteration contribution",
        ),
        mutation(
            "substitute-plus-with-times",
            [
                site("  do concurrent (i = 1:4) reduce(+:sum_value)\n",
                     "  do concurrent (i = 1:4) reduce(*:sum_value)\n"),
                site("    sum_value = sum_value + i\n", "    sum_value = sum_value * i\n"),
            ],
            "paired operation/body substitution keeps p4 form conforming",
        ),
        mutation(
            "substitute-times-with-plus",
            [
                site("  do concurrent (i = 1:4) reduce(*:product_value)\n",
                     "  do concurrent (i = 1:4) reduce(+:product_value)\n"),
                site("    product_value = product_value * 2\n", "    product_value = product_value + 2\n"),
            ],
            "paired operation/body substitution keeps p4 form conforming",
        ),
        mutation(
            "substitute-ior-with-ieor",
            [
                site("reduce(ior:or_value)", "reduce(ieor:or_value)"),
                site("or_value = ior(or_value, 2 * i + 1)", "or_value = ieor(or_value, 2 * i + 1)"),
            ],
            "paired bitwise substitution distinguishes overlapping integer bit patterns",
        ),
        mutation(
            "substitute-iand-with-ior",
            [
                site("reduce(iand:and_value)", "reduce(ior:and_value)"),
                site("and_value = iand(and_value, 255 - 2**i)", "and_value = ior(and_value, 255 - 2**i)"),
            ],
            "paired bitwise substitution changes the hand-derived mask result",
        ),
        mutation(
            "substitute-ieor-with-ior",
            [
                site("reduce(ieor:xor_value)", "reduce(ior:xor_value)"),
                site("xor_value = ieor(xor_value, 2 * i + 1)", "xor_value = ior(xor_value, 2 * i + 1)"),
            ],
            "paired bitwise substitution changes overlapping-bit parity into inclusion",
        ),
        mutation(
            "substitute-max-with-min",
            [
                site("reduce(max:max_value)", "reduce(min:max_value)"),
                site("max_value = max(max_value, i * 3)", "max_value = min(max_value, i * 3)"),
            ],
            "paired min/max substitution keeps the function form conforming",
        ),
        mutation(
            "substitute-min-with-max",
            [
                site("reduce(min:min_value)", "reduce(max:min_value)"),
                site("min_value = min(20 - i, min_value)", "min_value = max(20 - i, min_value)"),
            ],
            "paired min/max substitution keeps the function form conforming",
        ),
    ],
    "reduce_logical_identities": [
        mutation(
            "remove-logical-identity-reduce-locality",
            [
                site("  logical :: and_identity, or_identity\n  logical :: eqv_identity, neqv_identity\n"
                     "  logical :: contribution_guard",
                     "  logical :: and_identity, or_identity\n  logical :: eqv_identity, neqv_identity\n"
                     "  logical :: contribution_guard\n"
                     "  logical :: local_and, local_or, local_eqv, local_neqv, local_guard"),
                site(
                    "  do concurrent (i = 1:3) reduce(.and.:and_identity) reduce(.or.:or_identity) &\n"
                    "      reduce(.eqv.:eqv_identity) reduce(.neqv.:neqv_identity) reduce(.or.:contribution_guard)\n",
                    "  do concurrent (i = 1:3) local(local_and, local_or, local_eqv, local_neqv, local_guard)\n",
                ),
                site(
                    "    and_identity = and_identity .and. .true.\n"
                    "    or_identity = or_identity .or. .false.\n"
                    "    eqv_identity = eqv_identity .eqv. .true.\n"
                    "    neqv_identity = neqv_identity .neqv. .false.\n"
                    "    contribution_guard = contribution_guard .or. (i == 2)\n",
                    "    local_and = .true.\n"
                    "    local_or = .false.\n"
                    "    local_eqv = .true.\n"
                    "    local_neqv = .false.\n"
                    "    local_guard = .false.\n"
                    "    local_and = local_and .and. .true.\n"
                    "    local_or = local_or .or. .false.\n"
                    "    local_eqv = local_eqv .eqv. .true.\n"
                    "    local_neqv = local_neqv .neqv. .false.\n"
                    "    local_guard = local_guard .or. (i == 2)\n",
                ),
            ],
            "removes REDUCE locality while using per-iteration LOCAL scratch values; outside values stay pre-construct",
            run_when_parent_fails=True,
        ),
        mutation(
            "substitute-identity-and-with-neqv",
            [
                site("reduce(.and.:and_identity)", "reduce(.neqv.:and_identity)"),
                site("and_identity = and_identity .and. .true.",
                     "and_identity = and_identity .neqv. .true."),
            ],
            "paired logical operation substitution makes the .AND. identity load-bearing",
        ),
        mutation(
            "substitute-identity-or-with-eqv",
            [
                site("reduce(.or.:or_identity)", "reduce(.eqv.:or_identity)"),
                site("or_identity = or_identity .or. .false.",
                     "or_identity = or_identity .eqv. .false."),
            ],
            "paired logical operation substitution makes the .OR. identity load-bearing",
        ),
        mutation(
            "substitute-identity-eqv-with-neqv",
            [
                site("reduce(.eqv.:eqv_identity)", "reduce(.neqv.:eqv_identity)"),
                site("eqv_identity = eqv_identity .eqv. .true.",
                     "eqv_identity = eqv_identity .neqv. .true."),
            ],
            "paired logical operation substitution makes the .EQV. identity load-bearing",
        ),
        mutation(
            "substitute-identity-neqv-with-eqv",
            [
                site("reduce(.neqv.:neqv_identity)", "reduce(.eqv.:neqv_identity)"),
                site("neqv_identity = neqv_identity .neqv. .false.",
                     "neqv_identity = neqv_identity .eqv. .false."),
            ],
            "paired logical operation substitution makes the .NEQV. identity load-bearing",
        ),
    ],
    "reduce_forms": [
        mutation(
            "remove-left-form-contribution",
            [site("    left_value = left_value + i\n", "    left_value = left_value + 0\n")],
            "removes the load-bearing contribution while preserving the allowed left binary form",
        ),
        mutation(
            "substitute-left-plus-with-times",
            [
                site("  do concurrent (i = 1:3) reduce(+:left_value)\n",
                     "  do concurrent (i = 1:3) reduce(*:left_value)\n"),
                site("    left_value = left_value + i\n", "    left_value = left_value * i\n"),
            ],
            "paired operation/body substitution keeps the allowed left binary form",
        ),
        mutation(
            "substitute-right-plus-with-times",
            [
                site("  do concurrent (i = 1:3) reduce(+:right_value)\n",
                     "  do concurrent (i = 1:3) reduce(*:right_value)\n"),
                site("    right_value = i + right_value\n", "    right_value = i * right_value\n"),
            ],
            "paired operation/body substitution keeps the allowed right binary form",
        ),
        mutation(
            "substitute-function-max-with-min",
            [
                site("reduce(max:function_value)", "reduce(min:function_value)"),
                site("function_value = max(i * 4, function_value)", "function_value = min(i * 4, function_value)"),
            ],
            "paired function-form substitution keeps all appearances in the same form",
        ),
    ],
    "reduce_final_update": [
        mutation(
            "remove-final-update-contribution",
            [site("    total_value = total_value + i\n", "    total_value = total_value + 0\n")],
            "keeps the + reduction but removes values combined into the outside variable",
        ),
        mutation(
            "substitute-final-plus-with-times",
            [
                site("  do concurrent (i = 1:4) reduce(+:total_value)\n",
                     "  do concurrent (i = 1:4) reduce(*:total_value)\n"),
                site("    total_value = total_value + i\n", "    total_value = total_value * i\n"),
            ],
            "paired substitution keeps the reduction conforming and changes the final update",
        ),
    ],
    "reduce_logical_final_update": [
        mutation(
            "remove-logical-final-reduce-locality",
            [
                site("  logical :: and_final, or_final\n  logical :: eqv_final, neqv_final",
                     "  logical :: and_final, or_final\n  logical :: eqv_final, neqv_final\n"
                     "  logical :: local_and, local_or, local_eqv, local_neqv"),
                site(
                    "  do concurrent (i = 1:3) reduce(.and.:and_final) reduce(.or.:or_final) &\n"
                    "      reduce(.eqv.:eqv_final) reduce(.neqv.:neqv_final)\n",
                    "  do concurrent (i = 1:3) local(local_and, local_or, local_eqv, local_neqv)\n",
                ),
                site(
                    "    and_final = and_final .and. (i /= 2)\n"
                    "    or_final = or_final .or. (i == 2)\n"
                    "    eqv_final = eqv_final .eqv. (i /= 2)\n"
                    "    neqv_final = neqv_final .neqv. (i == 1)\n",
                    "    local_and = .true.\n"
                    "    local_or = .false.\n"
                    "    local_eqv = .true.\n"
                    "    local_neqv = .false.\n"
                    "    local_and = local_and .and. (i /= 2)\n"
                    "    local_or = local_or .or. (i == 2)\n"
                    "    local_eqv = local_eqv .eqv. (i /= 2)\n"
                    "    local_neqv = local_neqv .neqv. (i == 1)\n",
                ),
            ],
            "removes REDUCE locality while using per-iteration LOCAL scratch values; outside values stay pre-construct",
            run_when_parent_fails=True,
        ),
        mutation(
            "substitute-final-and-with-or",
            [
                site("reduce(.and.:and_final)", "reduce(.or.:and_final)"),
                site("and_final = and_final .and. (i /= 2)",
                     "and_final = and_final .or. (i /= 2)"),
            ],
            ".AND.<->.OR. substitution differs for true/false/true contributions",
        ),
        mutation(
            "substitute-final-or-with-and",
            [
                site("reduce(.or.:or_final)", "reduce(.and.:or_final)"),
                site("or_final = or_final .or. (i == 2)",
                     "or_final = or_final .and. (i == 2)"),
            ],
            ".OR.<->.AND. substitution differs for false/true/false contributions",
        ),
        mutation(
            "substitute-final-eqv-with-neqv",
            [
                site("reduce(.eqv.:eqv_final)", "reduce(.neqv.:eqv_final)"),
                site("eqv_final = eqv_final .eqv. (i /= 2)",
                     "eqv_final = eqv_final .neqv. (i /= 2)"),
            ],
            ".EQV.<->.NEQV. substitution differs for true/false/true contributions",
        ),
        mutation(
            "substitute-final-neqv-with-eqv",
            [
                site("reduce(.neqv.:neqv_final)", "reduce(.eqv.:neqv_final)"),
                site("neqv_final = neqv_final .neqv. (i == 1)",
                     "neqv_final = neqv_final .eqv. (i == 1)"),
            ],
            ".NEQV.<->.EQV. substitution differs for true/false/false contributions",
        ),
    ],
    "reduce_order_independent": [
        mutation(
            "remove-order-independent-sum-contribution",
            [site("    total_value = total_value + i\n", "    total_value = total_value + 0\n")],
            "removes the integer contribution without introducing order sensitivity",
        ),
        mutation(
            "substitute-order-plus-with-times",
            [
                site("reduce(+:total_value)", "reduce(*:total_value)"),
                site("total_value = total_value + i", "total_value = total_value * i"),
            ],
            "paired integer operation substitution keeps the mutant conforming",
        ),
        mutation(
            "substitute-order-max-with-min",
            [
                site("reduce(max:maximum_value)", "reduce(min:maximum_value)"),
                site("maximum_value = max(maximum_value, 5 * i)", "maximum_value = min(maximum_value, 5 * i)"),
            ],
            "paired integer function substitution keeps the mutant conforming",
        ),
    ],
    "shared_final_state": [
        mutation(
            "remove-shared-definition-statement",
            [site("    shared_value = 411\n", "")],
            "removes the load-bearing definition while leaving a conforming one-iteration construct",
        ),
    ],
}


def mutate_source(spec, plan, *, allow_identical=False):
    source = spec["source"]
    for item in plan["replacements"]:
        expected, replacement = item["expected"], item["replacement"]
        if source.count(expected) != 1:
            raise ValueError(f"{plan['id']} does not bind exactly one parent span: {expected!r}")
        if not allow_identical and expected == replacement:
            raise ValueError(f"{plan['id']} is identical to its parent")
        source = source.replace(expected, replacement, 1)
    if not allow_identical and source == spec["source"]:
        raise ValueError(f"{plan['id']} did not change the parent")
    return source


def source_specs():
    specs = {}
    for variant, config in VARIANTS.items():
        source, stdout = config["source"]()
        name = identifier(variant)
        raw = source.encode("ascii")
        mutations = []
        for plan in MUTATION_PLANS[variant]:
            mutant = mutate_source({"source": source}, plan)
            entry = copy.deepcopy(plan)
            entry["mutant_sha256"] = sha(mutant.encode("ascii"))
            mutations.append(entry)
        specs[name] = dict(
            id=name,
            variant=variant,
            rule=config["rule"],
            facets=list(config["facets"]),
            evidence=EVIDENCE_BY_RULE.get(config["rule"], "effect"),
            source=source,
            source_sha256=sha(raw),
            stdout=stdout,
            mutations=mutations,
        )
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["variant"])
        manifest = dict(
            schema_version=1,
            id=spec["id"],
            rule=spec["rule"],
            facets=spec["facets"],
            evidence=spec["evidence"],
            standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["stdout"], stderr=""),
        )
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] not in {"effect", "restriction"}:
            raise ValueError("unexpected category for " + rule)
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != EXPECTED_REMAINING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        for key, prefixes in RETIRED_PREFIXES.get(rule, {}).items():
            owner[key] = "\n\n".join(
                paragraph for paragraph in owner.get(key, "").split("\n\n")
                if not paragraph.startswith(prefixes))
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the DO CONCURRENT semantics generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "Source-only draft catalogue: see the corresponding `doc/catalogues/*.json` entry.\n"
        "No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.",
        "Catalogue: `doc/catalogues/additional_semantics_for_do_concurrent_constructs_11_1_7_5.json`. "
        "The original source-only registration supplied pending plans; the bounded fixtures below supply "
        "selected runtime/source-control cases and mutation plans, not universal coverage.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## DO CONCURRENT additional-semantics runtime observations\n\n"
        "Nine complete run/effect/f2023 programs discharge twenty-two selected facets for LOCAL, "
        "LOCAL_INIT, SHARED and INTEGER/LOGICAL REDUCE semantics. Every DO CONCURRENT observation is "
        "order-independent: either the construct has one iteration so locality-removal mutants remain "
        "conforming, or each iteration contributes to an associative/commutative integer or logical "
        "reduction with a hand-derived final result. No fixture asserts an iteration order, reduction "
        "tree, procedure call count, I/O order, storage identity or floating-point sum.\n\n"
        "The reduction fixtures cover INTEGER +, *, IOR, IAND, IEOR, MAX, MIN and LOGICAL .AND., "
        ".OR., .EQV. and .NEQV. The logical cases are retained even though the frozen target rejects "
        "the conforming dotted logical reduce-operation syntax; the reference compiler validates them. "
        "The packet uses no REAL or COMPLEX values, no coarray/image control operation, no ADVANCE= I/O, "
        "and no cross-iteration read of a variable defined in another iteration.\n\n"
        "Permanent feature-level mutation plans remove locality/contribution statements or substitute "
        "paired reduction operation and assignment forms so each mutant remains conforming, compiles in "
        "its own temporary directory, and must fail at run time on both accepted toolchains.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the DO CONCURRENT semantics summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(
        render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale DO CONCURRENT semantics fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def compiler_std_flag(compiler, standard):
    name = Path(compiler).name.lower()
    return f"--std={standard}" if "lfortran" in name else f"-std={standard}"


def compile_and_run(source, compiler, standard):
    with tempfile.TemporaryDirectory(prefix="dcs_mutant_") as tmp:
        work = Path(tmp)
        src = work / "source.f90"
        exe = work / "program"
        src.write_text(source)
        compile_cmd = [compiler, compiler_std_flag(compiler, standard), "source.f90", "-o", "program"]
        compile_result = subprocess.run(
            compile_cmd, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if compile_result.returncode != 0:
            return dict(phase="compile", returncode=compile_result.returncode,
                        stdout=compile_result.stdout, stderr=compile_result.stderr)
        run_result = subprocess.run(
            [str(exe)], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return dict(phase="run", returncode=run_result.returncode,
                    stdout=run_result.stdout, stderr=run_result.stderr)


def mutation_matrix(compiler, standard, *, sabotage_first=False, skip_parent_failures=False):
    _, specs = build_corpus(ROOT)
    rows, survivors, compile_failures, parent_failures = [], [], [], []
    first = True
    for spec in specs.values():
        parent = compile_and_run(spec["source"], compiler, standard)
        if parent["phase"] != "run" or parent["returncode"] != 0 or parent["stdout"] != spec["stdout"]:
            parent_failure = dict(case=spec["id"], phase=parent["phase"], returncode=parent["returncode"],
                                  stdout=parent["stdout"], stderr=parent["stderr"])
            parent_failures.append(parent_failure)
            if not skip_parent_failures:
                raise RuntimeError(
                    f"parent failed for {spec['id']} with {parent['phase']} rc={parent['returncode']}\n"
                    f"stdout={parent['stdout']}\nstderr={parent['stderr']}")
            plans = [plan for plan in spec["mutations"] if plan.get("run_when_parent_fails")]
        else:
            plans = spec["mutations"]
        for plan in plans:
            active = copy.deepcopy(plan)
            allow_identical = False
            if sabotage_first and first:
                active["replacements"][0]["replacement"] = active["replacements"][0]["expected"]
                active["id"] = active["id"] + "__identity_sabotage"
                allow_identical = True
                first = False
            mutant = mutate_source(spec, active, allow_identical=allow_identical)
            result = compile_and_run(mutant, compiler, standard)
            row = dict(case=spec["id"], mutation=active["id"], phase=result["phase"],
                       returncode=result["returncode"], stdout=result["stdout"], stderr=result["stderr"])
            rows.append(row)
            if result["phase"] != "run":
                compile_failures.append(row)
            elif result["returncode"] == 0 and result["stdout"] == spec["stdout"]:
                survivors.append(row)
    return dict(rows=rows, survivors=survivors, compile_failures=compile_failures,
                parent_failures=parent_failures)


def run_mutation_check(compiler, standard, *, skip_parent_failures=False):
    matrix = mutation_matrix(compiler, standard, skip_parent_failures=skip_parent_failures)
    if matrix["compile_failures"] or matrix["survivors"]:
        print(json.dumps(matrix, indent=2))
        raise SystemExit(1)
    skipped = ""
    if matrix["parent_failures"]:
        skipped = f"; skipped {len(matrix['parent_failures'])} parent-failing compiler-defect cases"
    print(f"Mutation check passed: {len(matrix['rows'])}/{len(matrix['rows'])} mutants failed on {compiler}{skipped}.")


def prove_non_vacuous(compiler, standard, *, skip_parent_failures=False):
    matrix = mutation_matrix(compiler, standard, sabotage_first=True,
                             skip_parent_failures=skip_parent_failures)
    if not matrix["survivors"]:
        print(json.dumps(matrix, indent=2))
        raise SystemExit("identity sabotage was not reported as a surviving mutant")
    survivor = matrix["survivors"][0]
    print("Non-vacuity proof passed: identity mutant reported as survivor "
          f"{survivor['case']}::{survivor['mutation']} on {compiler}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--prove-non-vacuous", action="store_true")
    parser.add_argument("--skip-parent-failures", action="store_true",
                        help="continue mutation/proof modes after parent cases that already fail on this compiler")
    parser.add_argument("--compiler")
    parser.add_argument("--standard", default="f2023")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    if args.mutation_check or args.prove_non_vacuous:
        if not args.compiler:
            parser.error("--compiler is required for mutation modes")
        if args.mutation_check:
            run_mutation_check(args.compiler, args.standard, skip_parent_failures=args.skip_parent_failures)
        else:
            prove_non_vacuous(args.compiler, args.standard, skip_parent_failures=args.skip_parent_failures)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} DO CONCURRENT semantics cases "
          f"covering {sum(len(facets) for facets in FACETS_BY_RULE.values())} facets.")


if __name__ == "__main__":
    main()
