#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 scoping and name-association rules in 19.3.5-19.5.1.2."""

import argparse
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "scoping_19_3_19_5_"
WORK_DIR = ROOT / ".scoping_19_3_19_5_mutation_work"

CATALOGUES = {
    "19.3.5": "doc/catalogues/argument_keywords_19_3_5.json",
    "19.4": "doc/catalogues/statement_and_construct_entities_19_4.json",
    "19.5.1.1": "doc/catalogues/forms_of_name_association_19_5_1_1.json",
    "19.5.1.2": "doc/catalogues/argument_association_summary_19_5_1_2.json",
}
VIEWS = {
    "19.3.5": "doc/fortran_2023_19_3_5.md",
    "19.4": "doc/fortran_2023_19_4.md",
    "19.5.1.1": "doc/fortran_2023_19_5_1_1.md",
    "19.5.1.2": "doc/fortran_2023_19_5_1_2.md",
}
SUMMARY_BEGIN = "<!-- BEGIN SCOPING 19.3-19.5 FIXTURES -->"
SUMMARY_END = "<!-- END SCOPING 19.3-19.5 FIXTURES -->"

FACETS_BY_RULE = {
    "S19.3.5-001": (
        "internal-module-interface-keyword-host-scope",
        "procedure-declaration-keyword-containing-scope",
    ),
    "S19.3.5-002": (
        "argument-keyword-accessible-through-use-association",
        "argument-keyword-accessible-through-host-association",
    ),
    "S19.3.5-003": ("intrinsic-keyword-reference-site-scope",),
    "S19.4-001": ("statement-entity-class-list", "statement-entity-shadows-outer-identifier"),
    "S19.4-002": (
        "statement-entity-common-block-name-exception",
        "statement-entity-scalar-variable-name-exception",
    ),
    "S19.4-003": (
        "do-concurrent-forall-index-construct-entity",
        "associate-select-rank-select-type-name-construct-entity",
        "local-local-init-construct-entity",
        "block-declared-entity-construct-entity",
        "block-use-associated-entity-construct-entity",
    ),
    "S19.4-006": (
        "implied-do-variable-scope-only-implied-do",
        "implied-do-variable-scalar",
        "implicit-rules-control-implied-do-type",
        "implied-do-variable-not-host-declaration",
    ),
    "S19.4-007": (
        "do-concurrent-forall-index-scope",
        "index-name-scalar-variable",
        "implicit-rules-control-index-type",
        "index-name-not-host-declaration",
    ),
    "S19.4-008": ("local-local-init-scope-of-do-concurrent",),
    "S19.4-009": (
        "default-typed-index-common-block-exception",
        "default-typed-index-scalar-variable-exception",
    ),
    "S19.4-010": ("associate-name-block-scope",),
    "S19.4-012": ("select-rank-associate-name-separate-block-scope",),
    "S19.4-013": ("select-type-associate-name-separate-block-scope",),
    "S19.4-014": (
        "statement-function-dummy-statement-scope",
        "statement-function-dummy-scalar-type-from-enclosing",
    ),
    "S19.5.1.1-001": ("cross-scope-access-mechanisms",),
    "S19.5.1.2-001": (
        "procedure-reference-establishes-argument-association",
        "present-dummy-associated-with-effective-argument",
    ),
    "S19.5.1.2-002": ("dummy-name-may-differ", "dummy-name-accesses-effective-argument"),
    "S19.5.1.2-003": (
        "argument-association-terminates-on-return",
        "subsequent-invocation-new-effective-argument",
    ),
}

EXPECTED_REMAINING = {
    "S19.3.5-001": set(),
    "S19.3.5-002": {"argument-keyword-only-for-own-procedure"},
    "S19.3.5-003": {"intrinsic-keyword-own-procedure-only"},
    "S19.4-001": set(),
    "S19.4-002": {
        "statement-entity-not-accessible-global-or-class-one",
        "no-duplicate-statement-entity-in-scope",
    },
    "S19.4-003": {"change-team-coarray-name-construct-entity"},
    "S19.4-004": {"data-initialized-block-entity-not-used-before-data"},
    "S19.4-005": {"same-construct-entities-distinct-identifiers"},
    "S19.4-006": {"inline-integer-type-spec-controls-type", "implied-do-variable-must-be-integer", "implied-do-variable-no-other-attributes"},
    "S19.4-007": {"concurrent-header-integer-type-spec-controls-type", "index-name-must-be-integer", "index-name-no-other-attributes"},
    "S19.4-008": {"local-local-init-attributes-owned-by-11-1-7-5"},
    "S19.4-009": {
        "default-typed-index-not-accessible-global-local-outer-construct",
        "contained-index-not-containing-index",
    },
    "S19.4-010": {"associate-name-attributes-owned-by-11-1-3-2"},
    "S19.4-011": {
        "change-team-associate-name-block-scope",
        "change-team-associate-name-attributes-owned-by-11-1-5",
    },
    "S19.4-012": {"select-rank-associate-attributes-owned-by-11-1-10-3"},
    "S19.4-013": {"select-type-associate-attributes-owned-by-11-1-11-2"},
    "S19.4-014": {"statement-function-dummy-no-other-attributes"},
    "S19.5.1.1-001": {"five-name-association-forms"},
    "S19.5.1.2-001": {"sequence-association-cross-reference"},
    "S19.5.1.2-002": set(),
    "S19.5.1.2-003": set(),
}

ORACLE_PREFIXES = {rule: f"{rule} scoping/name-association runtime fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIXES = {rule: f"{rule} scoping/name-association fixture boundaries: " for rule in FACETS_BY_RULE}

ORACLES = {
    "S19.3.5-001": ORACLE_PREFIXES["S19.3.5-001"] + (
        "one complete run/effect/f2023 program calls an internal procedure, an external procedure with an "
        "interface body, and a procedure pointer declared with an explicit abstract interface by their dummy "
        "argument keywords. Same-spelling host sentinels keep distinct negative values, while each procedure "
        "writes a distinct exact integer result. Positional-call mutants use the host sentinel actuals instead "
        "of keyword literals and therefore expose any loss of keyword scoping."
    ),
    "S19.3.5-002": ORACLE_PREFIXES["S19.3.5-002"] + (
        "the argument-keyword fixture also calls a module procedure imported by USE association and calls a "
        "host-associated module procedure from another module procedure, using keyword literals that differ "
        "from same-spelling local sentinels. Positional-call mutants pass the sentinels and fail the exact "
        "result checks. The own-procedure-only restriction remains pending because it is unnumbered and no "
        "diagnostic is required here."
    ),
    "S19.3.5-003": ORACLE_PREFIXES["S19.3.5-003"] + (
        "one MERGE reference uses intrinsic dummy keywords tsource, fsource, and mask with exact integer and "
        "logical literals while same-spelling local variables retain distinct sentinels. A mutant changes the "
        "reference to positional actuals using those sentinels, so reference-site keyword scope is load-bearing."
    ),
    "S19.4-001": ORACLE_PREFIXES["S19.4-001"] + (
        "one complete program observes all four statement-entity classes: an array-constructor implied-DO, a "
        "DATA implied-DO, a FORALL statement index, and a statement-function dummy. Each uses a name that also "
        "names an outer scalar sentinel; the statement entity produces distinct exact values and the outer "
        "sentinel is checked unchanged. Feature mutants reverse the DATA implied-DO order, remove the array "
        "constructor implied-DO, change the FORALL range, or replace the statement-function dummy reference."
    ),
    "S19.4-002": ORACLE_PREFIXES["S19.4-002"] + (
        "one positive-control program uses statement-entity names that match a scalar variable and a common "
        "block name. Exact DATA and array-constructor values prove the exception source is accepted, and the "
        "scalar sentinel remains unchanged. Prohibition facets for non-exception names and duplicates remain "
        "pending because 19.4 p2 is an unnumbered program restriction."
    ),
    "S19.4-003": ORACLE_PREFIXES["S19.4-003"] + (
        "one program exercises construct-entity classes other than CHANGE TEAM: DO CONCURRENT/FORALL indices, "
        "ASSOCIATE, SELECT RANK, SELECT TYPE, LOCAL/LOCAL_INIT variables, BLOCK declarations, and BLOCK USE "
        "association. Every construct entity has a same-spelling host sentinel or separate module sentinel; "
        "distinct exact writes prove the construct binding and post-construct checks prove the outer binding was "
        "not disturbed. Feature mutants remove or replace each construct scope with an ordinary outer-scope use."
    ),
    "S19.4-006": ORACLE_PREFIXES["S19.4-006"] + (
        "one program observes array-constructor and DATA implied-DO variables as scalar integer variables scoped "
        "only to their implied DO. It checks exact constructor/DATA values, unchanged outer scalar sentinels, "
        "an implicit INTEGER(k2) ac-implied-do KIND, and a same-spelling module variable read by an internal "
        "procedure after an ac-implied-do. Mutants remove the implied-DO or replace it with an ordinary DO "
        "that aliases the module variable, so exact values, KIND checks, or host-read sentinels fail."
    ),
    "S19.4-007": ORACLE_PREFIXES["S19.4-007"] + (
        "one program observes DO CONCURRENT, FORALL statement, and FORALL construct indices as scalar integer "
        "entities scoped to their statement or construct. It checks exact index-written arrays, unchanged outer "
        "sentinels, an implicit INTEGER(k2) index KIND, and a same-spelling module variable read by an "
        "internal procedure after a DO CONCURRENT index. Mutants remove the index construct, change its "
        "range/type source, or replace it with an ordinary DO that aliases the module variable."
    ),
    "S19.4-008": ORACLE_PREFIXES["S19.4-008"] + (
        "one one-iteration DO CONCURRENT program gives same-spelling outer variables LOCAL and LOCAL_INIT "
        "locality, assigns LOCAL before use, reads the defined LOCAL_INIT value, then checks exact result values "
        "and unchanged outer sentinels after termination. Removing either locality spec is conforming in the "
        "one-iteration construct and fails the outer-sentinel checks."
    ),
    "S19.4-009": ORACLE_PREFIXES["S19.4-009"] + (
        "one positive-control program uses default-typed DO CONCURRENT index names matching a scalar variable "
        "and a common block name. The index values fill arrays with exact nondefault values while the scalar and "
        "common-block storage sentinel remain unchanged. The non-exception and nested-index restrictions remain "
        "pending because no diagnostic is required by this unnumbered rule."
    ),
    "S19.4-010": ORACLE_PREFIXES["S19.4-010"] + (
        "one ASSOCIATE program maps associate name item to a target while an outer item sentinel remains 99. "
        "The associate assignment changes only the target to 303. Replacing the construct by an outer assignment "
        "is conforming and fails both target and outer-sentinel checks."
    ),
    "S19.4-012": ORACLE_PREFIXES["S19.4-012"] + (
        "one SELECT RANK program passes a rank-one array to an assumed-rank dummy, uses associate name item in "
        "the rank(1) block, and checks the array update, rank observation, and unchanged host item sentinel. A "
        "mutant replaces the SELECT RANK construct with ordinary host-sentinel assignments and fails."
    ),
    "S19.4-013": ORACLE_PREFIXES["S19.4-013"] + (
        "one SELECT TYPE program associates name item with an allocated dynamic child object while an outer "
        "integer item sentinel remains 99. The type branch writes child components and records exact values; a "
        "mutant replaces the construct with an outer assignment and fails the dynamic-type observations."
    ),
    "S19.4-014": ORACLE_PREFIXES["S19.4-014"] + (
        "one program has statement functions whose dummy arguments share an outer scalar name and whose type is "
        "also supplied by enclosing implicit rules. Exact function results and unchanged outer sentinels prove "
        "statement scope and scalar typing. A feature mutant rewrites the statement function expression to use "
        "an outer sentinel and fails the result check."
    ),
    "S19.5.1.1-001": ORACLE_PREFIXES["S19.5.1.1-001"] + (
        "one program observes the three cross-scope access mechanisms named by 19.5.1.1: argument association "
        "changes an actual through a differently named dummy, USE association reads a module sentinel through a "
        "rename, and host association reads a host sentinel from an internal procedure. Distinct exact values "
        "make wrong-resolution bindings observable. The five-form inventory facet remains pending as a source "
        "cross-reference because linkage and coarray/team forms are owned elsewhere or out of scope."
    ),
    "S19.5.1.2-001": ORACLE_PREFIXES["S19.5.1.2-001"] + (
        "one program calls procedures with present actual arguments initialized to nondefault values; dummy "
        "assignments change the effective arguments to exact sentinel values. Removing the procedure reference "
        "or changing the dummy assignment leaves the actuals at their pre-call sentinels and fails. Sequence "
        "association remains pending to its Clause 15 owner."
    ),
    "S19.5.1.2-002": ORACLE_PREFIXES["S19.5.1.2-002"] + (
        "the argument-association program calls rename_probe(formal) with an actual named actual_value and a "
        "host homonym formal initialized to -777. Assignment to dummy formal changes actual_value to 42 while "
        "the host homonym remains unchanged, proving the dummy name is the procedure-local access name."
    ),
    "S19.5.1.2-003": ORACLE_PREFIXES["S19.5.1.2-003"] + (
        "the program calls the same subroutine twice with distinct actuals a and b. The first invocation changes "
        "only a to 42; after return the second invocation changes b to 77 while a remains 42, proving the first "
        "association terminated and the later invocation established a new effective argument."
    ),
}

LIMITATIONS = {
    rule: LIMIT_PREFIXES[rule] + (
        "only single-image default INTEGER/LOGICAL/derived-type observations with exact values, inquiry results, "
        "and outer-sentinel preservation are covered. Unnumbered prohibitions without a required diagnostic, "
        "CHANGE TEAM/coarray facets, storage identity, addresses, undefined values, processor-dependent diagnostics, "
        "and owner-catalogue attribute details remain pending or out of scope."
    ) for rule in FACETS_BY_RULE
}


def ident(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__" + PREFIX + variant


def source_program(name, rule, facets, declarations, setup, body, checks, *, prefix_modules="", implicit="implicit none"):
    completion = "SCOPING 19.3-19.5 " + name.upper().replace("_", " ") + " OK"
    def split_declarations(text):
        use_lines, implicit_lines, other_lines = [], [], []
        for line in text.splitlines():
            stripped = line.strip().lower()
            if stripped.startswith("use ") or stripped.startswith("import"):
                use_lines.append(line)
            elif stripped.startswith("implicit "):
                implicit_lines.append(line)
            else:
                other_lines.append(line)
        return use_lines, implicit_lines, other_lines

    use_lines, implicit_lines, other_lines = split_declarations(declarations)
    lines = [f"! rule: {rule}"]
    lines += [f"! covers: {facet}" for facet in facets]
    lines += [f"program {PREFIX}{name}"]
    lines += use_lines
    if implicit_lines:
        lines += implicit_lines
    elif implicit:
        lines.append(f"  {implicit}")
    lines.append("  integer :: checks")
    lines += [line for line in other_lines if line.strip()]
    lines.append("  checks = 0")
    if setup.strip():
        lines.append(setup.rstrip())
    if body.strip():
        lines.append(body.rstrip())
    for expr, token in checks:
        lines += [
            f"  if ({expr}) then",
            f"    write(*,'(a)') 'SCOPE:{name}:{token}'",
            "    error stop",
            "  end if",
            "  checks = checks + 1",
        ]
    lines += [
        f"  if (checks /= {len(checks)}) then",
        f"    write(*,'(a)') 'SCOPE:{name}:check-count'",
        "    error stop",
        "  end if",
        f"  write(*,'(a)') '{completion}'",
        "contains",
    ]
    # body may include internal procedures after a marker.
    text = "\n".join(lines)
    contains = ""
    if "\n!CONTAINS\n" in body:
        before, contains = body.split("\n!CONTAINS\n", 1)
        lines2 = lines[:]
        # Rebuild replacing full body with executable part before marker.
        use_lines, implicit_lines, other_lines = split_declarations(declarations)
        lines2 = [f"! rule: {rule}"] + [f"! covers: {facet}" for facet in facets]
        lines2 += [f"program {PREFIX}{name}"]
        lines2 += use_lines
        if implicit_lines:
            lines2 += implicit_lines
        elif implicit:
            lines2.append(f"  {implicit}")
        lines2.append("  integer :: checks")
        lines2 += [line for line in other_lines if line.strip()]
        lines2.append("  checks = 0")
        if setup.strip():
            lines2.append(setup.rstrip())
        if before.strip():
            lines2.append(before.rstrip())
        for expr, token in checks:
            lines2 += [
                f"  if ({expr}) then",
                f"    write(*,'(a)') 'SCOPE:{name}:{token}'",
                "    error stop",
                "  end if",
                "  checks = checks + 1",
            ]
        lines2 += [
            f"  if (checks /= {len(checks)}) then",
            f"    write(*,'(a)') 'SCOPE:{name}:check-count'",
            "    error stop",
            "  end if",
            f"  write(*,'(a)') '{completion}'",
            "contains",
            contains.rstrip(),
            f"end program {PREFIX}{name}",
            "",
        ]
        return prefix_modules + "\n".join(lines2), completion + "\n"
    lines += [f"end program {PREFIX}{name}", ""]
    return prefix_modules + "\n".join(lines), completion + "\n"


def site(expected, replacement):
    return {"expected": expected, "replacement": replacement}


def mutation(mid, replacements, rationale):
    return {"id": mid, "replacements": list(replacements), "rationale": rationale}


def keyword_modules():
    return """module scoping_keyword_mod
  implicit none
  integer :: use_result = -801
  integer :: host_result = -802
contains
  subroutine used_proc(use_arg)
    integer, intent(in) :: use_arg
    use_result = use_arg
  end subroutine
  subroutine host_proc(host_arg)
    integer, intent(in) :: host_arg
    host_result = host_arg
  end subroutine
  subroutine host_caller()
    integer :: host_arg
    host_arg = -15
    call host_proc(host_arg=13)
  end subroutine
end module

subroutine interface_body_proc(iface_arg)
  implicit none
  integer, intent(in) :: iface_arg
  common /kw_iface_common/ iface_result
  integer :: iface_result
  iface_result = iface_arg
end subroutine

subroutine pointer_target(ptr_arg)
  implicit none
  integer, intent(in) :: ptr_arg
  common /kw_ptr_common/ ptr_result
  integer :: ptr_result
  ptr_result = ptr_arg
end subroutine

"""


def keyword_source():
    source, stdout = source_program(
        "argument_keywords",
        "S19.3.5-001",
        FACETS_BY_RULE["S19.3.5-001"],
        "\n".join([
            "  use scoping_keyword_mod, only: used_proc, host_caller, use_result, host_result",
            "  interface",
            "    subroutine interface_body_proc(iface_arg)",
            "      integer, intent(in) :: iface_arg",
            "    end subroutine",
            "    subroutine pointer_target(ptr_arg)",
            "      integer, intent(in) :: ptr_arg",
            "    end subroutine",
            "  end interface",
            "  abstract interface",
            "    subroutine pointer_iface(ptr_arg)",
            "      integer, intent(in) :: ptr_arg",
            "    end subroutine",
            "  end interface",
            "  procedure(pointer_iface), pointer :: proc_ptr",
            "  integer :: internal_result, alpha, iface_arg, ptr_arg, use_arg, host_arg",
            "  integer :: iface_result, ptr_result",
            "  common /kw_iface_common/ iface_result",
            "  common /kw_ptr_common/ ptr_result",
        ]),
        "\n".join([
            "  internal_result = -901",
            "  iface_result = -902",
            "  ptr_result = -903",
            "  use_result = -904",
            "  host_result = -905",
            "  alpha = -11",
            "  iface_arg = -12",
            "  ptr_arg = -13",
            "  use_arg = -14",
            "  host_arg = -15",
            "  proc_ptr => pointer_target",
        ]),
        "\n".join([
            "  call internal_proc(alpha=21)",
            "  call interface_body_proc(iface_arg=31)",
            "  call proc_ptr(ptr_arg=41)",
            "  call used_proc(use_arg=12)",
            "  call host_caller()",
            "!CONTAINS",
            "  subroutine internal_proc(alpha)",
            "    integer, intent(in) :: alpha",
            "    internal_result = alpha",
            "  end subroutine",
        ]),
        [
            ("internal_result /= 21", "internal-keyword"),
            ("alpha /= -11", "alpha-sentinel"),
            ("iface_result /= 31", "interface-keyword"),
            ("iface_arg /= -12", "interface-sentinel"),
            ("ptr_result /= 41", "procedure-declaration-keyword"),
            ("ptr_arg /= -13", "procedure-declaration-sentinel"),
            ("use_result /= 12", "use-associated-keyword"),
            ("use_arg /= -14", "use-associated-sentinel"),
            ("host_result /= 13", "host-associated-keyword"),
            ("host_arg /= -15", "host-associated-sentinel"),
        ],
        prefix_modules=keyword_modules(),
    )
    return source, stdout


def keyword_access_source():
    prefix = """module scoping_keyword_access_mod
  implicit none
  integer :: use_result = -801
  integer :: host_result = -802
contains
  subroutine used_proc(use_arg)
    integer, intent(in) :: use_arg
    use_result = use_arg
  end subroutine
  subroutine host_proc(host_arg)
    integer, intent(in) :: host_arg
    host_result = host_arg
  end subroutine
  subroutine host_caller()
    integer :: host_arg
    host_arg = -15
    call host_proc(host_arg=13)
  end subroutine
end module

"""
    return source_program(
        "argument_keyword_accessibility",
        "S19.3.5-002",
        FACETS_BY_RULE["S19.3.5-002"],
        "\n".join([
            "  use scoping_keyword_access_mod, only: used_proc, host_caller, use_result, host_result",
            "  integer :: use_arg, host_arg",
        ]),
        "\n".join([
            "  use_result = -904",
            "  host_result = -905",
            "  use_arg = -14",
            "  host_arg = -15",
        ]),
        "\n".join([
            "  call used_proc(use_arg=12)",
            "  call host_caller()",
        ]),
        [
            ("use_result /= 12", "use-associated-keyword"),
            ("use_arg /= -14", "use-associated-sentinel"),
            ("host_result /= 13", "host-associated-keyword"),
            ("host_arg /= -15", "host-associated-sentinel"),
        ],
        prefix_modules=prefix,
    )


def intrinsic_keyword_source():
    return source_program(
        "intrinsic_keywords",
        "S19.3.5-003",
        FACETS_BY_RULE["S19.3.5-003"],
        "\n".join([
            "  integer :: tsource, fsource, result_value",
            "  logical :: mask",
        ]),
        "\n".join([
            "  tsource = -701",
            "  fsource = -702",
            "  mask = .false.",
            "  result_value = -703",
        ]),
        "  result_value = merge(tsource=7, fsource=9, mask=.true.)",
        [
            ("result_value /= 7", "merge-keyword-result"),
            ("tsource /= -701", "tsource-sentinel"),
            ("fsource /= -702", "fsource-sentinel"),
            ("mask", "mask-sentinel"),
        ],
    )


def statement_entities_source():
    return source_program(
        "statement_entities",
        "S19.4-001",
        FACETS_BY_RULE["S19.4-001"],
        "\n".join([
            "  integer :: i, di, k, q, sf",
            "  integer :: ac_values(3), data_values(3), forall_values(3)",
            "  sf(q) = q + 1",
        ]),
        "\n".join([
            "  i = 99",
            "  di = 88",
            "  k = 77",
            "  q = 66",
            "  ac_values = -1",
            "  forall_values = -2",
        ]),
        "\n".join([
            "  data (data_values(di), di = 1, 3) / 10, 20, 30 /",
            "  ac_values = [(i, i = 1, 3)]",
            "  forall (k = 1:3) forall_values(k) = k + 40",
        ]),
        [
            ("any(ac_values /= [1, 2, 3])", "array-constructor-values"),
            ("i /= 99", "array-constructor-outer"),
            ("any(data_values /= [10, 20, 30])", "data-values"),
            ("di /= 88", "data-outer"),
            ("any(forall_values /= [41, 42, 43])", "forall-statement-values"),
            ("k /= 77", "forall-statement-outer"),
            ("sf(4) /= 5", "statement-function-value"),
            ("q /= 66", "statement-function-outer"),
        ],
    )


def statement_entity_exceptions_source():
    prefix = """module scoping_common_holder
  implicit none
  integer :: common_payload
  common /idx/ common_payload
end module

"""
    return source_program(
        "statement_entity_exceptions",
        "S19.4-002",
        FACETS_BY_RULE["S19.4-002"],
        "\n".join([
            "  use scoping_common_holder, only: common_payload",
            "  implicit integer (i)",
            "  integer :: i, idx_values(3), scalar_values(3)",
        ]),
        "\n".join([
            "  i = 99",
            "  common_payload = -505",
        ]),
        "\n".join([
            "  data (idx_values(idx), idx = 1, 3) / 101, 102, 103 /",
            "  scalar_values = [(i, i = 1, 3)]",
        ]),
        [
            ("any(idx_values /= [101, 102, 103])", "common-name-data"),
            ("common_payload /= -505", "common-storage-sentinel"),
            ("any(scalar_values /= [1, 2, 3])", "scalar-exception-values"),
            ("i /= 99", "scalar-exception-outer"),
        ],
        prefix_modules=prefix,
    )


def implied_do_scope_source():
    prefix = """module scoping_kind_provider
  implicit none
  integer, parameter :: k2 = selected_int_kind(18)
end module

"""
    return source_program(
        "implied_do_scope_type",
        "S19.4-006",
        FACETS_BY_RULE["S19.4-006"],
        "\n".join([
            "  use scoping_kind_provider, only: k2",
            "  implicit integer(kind=k2) (p)",
            "  integer :: i, di, host_ac",
            "  integer :: values(3), data_values(3), implicit_kind(1)",
            "  integer :: host_values(3), host_seen",
        ]),
        "\n".join([
            "  i = 99",
            "  di = 88",
            "  host_ac = 444",
            "  values = -1",
            "  implicit_kind = -3",
            "  host_values = -4",
            "  host_seen = -5",
        ]),
        "\n".join([
            "  data (data_values(di), di = 1, 3) / 10, 20, 30 /",
            "  values = [(i, i = 1, 3)]",
            "  implicit_kind = [(kind(p), p = 1, 1)]",
            "  block",
            "    host_values = [(host_ac, host_ac = 1, 3)]",
            "    host_seen = host_ac",
            "  end block",
        ]),
        [
            ("any(values /= [1, 2, 3])", "ac-implied-do-values"),
            ("i /= 99", "ac-outer-sentinel"),
            ("any(data_values /= [10, 20, 30])", "data-implied-do-values"),
            ("di /= 88", "data-outer-sentinel"),
            ("implicit_kind(1) /= k2", "implicit-kind"),
            ("any(host_values /= [1, 2, 3])", "host-ac-values"),
            ("host_seen /= 444", "host-ac-not-declared"),
        ],
        prefix_modules=prefix,
        implicit="implicit none",
    )


def index_scope_source():
    prefix = """module scoping_kind_provider_index
  implicit none
  integer, parameter :: k2 = selected_int_kind(18)
end module

"""
    return source_program(
        "index_scope_type",
        "S19.4-007",
        FACETS_BY_RULE["S19.4-007"],
        "\n".join([
            "  use scoping_kind_provider_index, only: k2",
            "  implicit integer(kind=k2) (p)",
            "  integer :: i, k, m, host_idx",
            "  integer :: dc_values(3), forall_stmt(3), forall_construct(3)",
            "  integer :: implicit_kind, host_index_values(3), host_index_seen",
        ]),
        "\n".join([
            "  i = 99",
            "  k = 88",
            "  m = 77",
            "  host_idx = 555",
            "  dc_values = -1",
            "  forall_stmt = -2",
            "  forall_construct = -3",
            "  implicit_kind = -5",
            "  host_index_values = -6",
            "  host_index_seen = -7",
        ]),
        "\n".join([
            "  do concurrent (i = 1:3)",
            "    dc_values(i) = i",
            "  end do",
            "  forall (k = 1:3) forall_stmt(k) = k + 10",
            "  forall (m = 1:3)",
            "    forall_construct(m) = m + 20",
            "  end forall",
            "  do concurrent (p = 1:1)",
            "    implicit_kind = kind(p)",
            "  end do",
            "  block",
            "    do concurrent (host_idx = 1:3)",
            "      host_index_values(host_idx) = host_idx",
            "    end do",
            "    host_index_seen = host_idx",
            "  end block",
        ]),
        [
            ("any(dc_values /= [1, 2, 3])", "do-concurrent-values"),
            ("i /= 99", "do-concurrent-outer"),
            ("any(forall_stmt /= [11, 12, 13])", "forall-statement-values"),
            ("k /= 88", "forall-statement-outer"),
            ("any(forall_construct /= [21, 22, 23])", "forall-construct-values"),
            ("m /= 77", "forall-construct-outer"),
            ("implicit_kind /= k2", "implicit-kind"),
            ("any(host_index_values /= [1, 2, 3])", "host-index-values"),
            ("host_index_seen /= 555", "host-index-not-declared"),
        ],
        prefix_modules=prefix,
    )


def construct_entities_source():
    prefix = """module scoping_block_use_provider
  implicit none
  integer :: block_use = -606
end module

"""
    return source_program(
        "construct_entities",
        "S19.4-003",
        FACETS_BY_RULE["S19.4-003"],
        "\n".join([
            "  use scoping_block_use_provider, only: module_block_use => block_use",
            "  type :: base_t",
            "    integer :: tag = -1",
            "  end type",
            "  type, extends(base_t) :: child_t",
            "    integer :: payload = -2",
            "  end type",
            "  integer :: i, item, x, block_use, local_value, init_value",
            "  integer :: dc_values(3), forall_values(3), target, assoc_seen",
            "  integer :: rank_array(2), rank_seen, type_seen, block_seen, local_seen(1)",
            "  class(base_t), allocatable :: poly",
        ]),
        "\n".join([
            "  i = 99",
            "  item = 98",
            "  x = 97",
            "  block_use = 96",
            "  local_value = 95",
            "  init_value = 7",
            "  dc_values = -1",
            "  forall_values = -2",
            "  target = 10",
            "  assoc_seen = -3",
            "  rank_array = -4",
            "  rank_seen = -5",
            "  type_seen = -6",
            "  block_seen = -7",
            "  local_seen = -8",
            "  module_block_use = -606",
            "  allocate(child_t :: poly)",
        ]),
        "\n".join([
            "  do concurrent (i = 1:3)",
            "    dc_values(i) = i",
            "  end do",
            "  forall (i = 1:3)",
            "    forall_values(i) = i + 10",
            "  end forall",
            "  associate (item => target)",
            "    item = 303",
            "    assoc_seen = item",
            "  end associate",
            "  call rank_probe(rank_array, rank_seen)",
            "  select type (item => poly)",
            "  type is (child_t)",
            "    item%tag = 505",
            "    item%payload = 506",
            "    type_seen = item%tag + item%payload",
            "  class default",
            "    type_seen = -5000",
            "  end select",
            "  do concurrent (i = 1:1) local(local_value) local_init(init_value) shared(local_seen)",
            "    local_value = 100",
            "    local_seen(i) = local_value + init_value",
            "    init_value = -77",
            "  end do",
            "  block",
            "    integer :: x",
            "    x = 55",
            "    block_seen = x",
            "  end block",
            "  block",
            "    use scoping_block_use_provider, only: block_use",
            "    block_use = 606",
            "  end block",
            "!CONTAINS",
            "  subroutine rank_probe(a, seen)",
            "    integer, intent(inout) :: a(..)",
            "    integer, intent(inout) :: seen",
            "    select rank (item => a)",
            "    rank (1)",
            "      item(1) = 404",
            "      seen = rank(item) + size(item)",
            "    rank default",
            "      seen = -404",
            "    end select",
            "  end subroutine",
        ]),
        [
            ("any(dc_values /= [1, 2, 3])", "do-concurrent-index"),
            ("any(forall_values /= [11, 12, 13])", "forall-index"),
            ("target /= 303 .or. assoc_seen /= 303", "associate-name"),
            ("rank_array(1) /= 404 .or. rank_seen /= 3", "select-rank-name"),
            ("type_seen /= 1011", "select-type-name"),
            ("any(local_seen /= [107])", "local-local-init"),
            ("block_seen /= 55", "block-declared"),
            ("module_block_use /= 606", "block-use-associated"),
            ("i /= 99", "outer-i"),
            ("item /= 98", "outer-item"),
            ("x /= 97", "outer-x"),
            ("block_use /= 96", "outer-block-use"),
            ("local_value /= 95 .or. init_value /= 7", "outer-locality"),
        ],
        prefix_modules=prefix,
    )


def local_scope_source():
    return source_program(
        "local_scope",
        "S19.4-008",
        FACETS_BY_RULE["S19.4-008"],
        "\n".join([
            "  integer :: i, local_value, init_value, observed(1)",
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
            ("observed(1) /= 107", "local-result"),
            ("local_value /= -222", "local-outer"),
            ("init_value /= 7", "local-init-outer"),
        ],
    )


def index_exceptions_source():
    prefix = """module scoping_index_common_holder
  implicit none
  integer :: common_payload
  common /idx/ common_payload
end module

"""
    return source_program(
        "index_exceptions",
        "S19.4-009",
        FACETS_BY_RULE["S19.4-009"],
        "\n".join([
            "  use scoping_index_common_holder, only: common_payload",
            "  implicit integer (i)",
            "  integer :: i, scalar_values(3), common_values(3)",
        ]),
        "\n".join([
            "  i = 99",
            "  common_payload = -909",
            "  scalar_values = -1",
            "  common_values = -2",
        ]),
        "\n".join([
            "  do concurrent (i = 1:3)",
            "    scalar_values(i) = i",
            "  end do",
            "  do concurrent (idx = 1:3)",
            "    common_values(idx) = idx + 10",
            "  end do",
        ]),
        [
            ("any(scalar_values /= [1, 2, 3])", "scalar-index-values"),
            ("i /= 99", "scalar-index-outer"),
            ("any(common_values /= [11, 12, 13])", "common-index-values"),
            ("common_payload /= -909", "common-index-storage"),
        ],
        prefix_modules=prefix,
    )


def associate_scope_source():
    return source_program(
        "associate_scope",
        "S19.4-010",
        FACETS_BY_RULE["S19.4-010"],
        "  integer :: item, target, seen",
        "\n".join(["  item = 99", "  target = 10", "  seen = -1"]),
        "\n".join([
            "  associate (item => target)",
            "    item = 303",
            "    seen = item",
            "  end associate",
        ]),
        [("target /= 303", "target"), ("seen /= 303", "seen"), ("item /= 99", "outer")],
    )


def select_rank_scope_source():
    return source_program(
        "select_rank_scope",
        "S19.4-012",
        FACETS_BY_RULE["S19.4-012"],
        "  integer :: item, rank_array(2), seen",
        "\n".join(["  item = 99", "  rank_array = -1", "  seen = -2"]),
        "  call rank_probe(rank_array, seen)\n!CONTAINS\n" + "\n".join([
            "  subroutine rank_probe(a, seen)",
            "    integer, intent(inout) :: a(..)",
            "    integer, intent(inout) :: seen",
            "    select rank (item => a)",
            "    rank (1)",
            "      item(1) = 404",
            "      seen = rank(item) + size(item)",
            "    rank default",
            "      seen = -404",
            "    end select",
            "  end subroutine",
        ]),
        [("rank_array(1) /= 404", "array"), ("seen /= 3", "seen"), ("item /= 99", "outer")],
    )


def select_type_scope_source():
    return source_program(
        "select_type_scope",
        "S19.4-013",
        FACETS_BY_RULE["S19.4-013"],
        "\n".join([
            "  type :: base_t",
            "    integer :: tag = -1",
            "  end type",
            "  type, extends(base_t) :: child_t",
            "    integer :: payload = -2",
            "  end type",
            "  class(base_t), allocatable :: poly",
            "  integer :: item, seen",
        ]),
        "\n".join(["  item = 99", "  seen = -3", "  allocate(child_t :: poly)"]),
        "\n".join([
            "  select type (item => poly)",
            "  type is (child_t)",
            "    item%tag = 505",
            "    item%payload = 506",
            "    seen = item%tag + item%payload",
            "  class default",
            "    seen = -5000",
            "  end select",
        ]),
        [("seen /= 1011", "seen"), ("item /= 99", "outer")],
    )


def statement_function_scope_source():
    return source_program(
        "statement_function_scope",
        "S19.4-014",
        FACETS_BY_RULE["S19.4-014"],
        "\n".join([
            "  implicit integer (r)",
            "  integer :: q, sf, sg, observed, implicit_observed",
            "  sf(q) = q + 1",
            "  sg(r) = r + 2",
        ]),
        "\n".join(["  q = 99", "  observed = sf(4)", "  implicit_observed = sg(5)"]),
        "",
        [("observed /= 5", "dummy-scope"), ("q /= 99", "outer"), ("implicit_observed /= 7", "implicit-type")],
        implicit="implicit none",
    )


def name_association_forms_source():
    prefix = """module scoping_use_assoc_provider
  implicit none
  integer :: module_value = 222
end module

"""
    return source_program(
        "name_association_cross_scope",
        "S19.5.1.1-001",
        FACETS_BY_RULE["S19.5.1.1-001"],
        "\n".join([
            "  use scoping_use_assoc_provider, only: used_value => module_value",
            "  integer :: actual_value, host_value, argument_seen, use_seen, host_seen",
        ]),
        "\n".join([
            "  actual_value = 1",
            "  host_value = 333",
            "  argument_seen = -1",
            "  use_seen = -2",
            "  host_seen = -3",
        ]),
        "  call argument_probe(actual_value)\n  use_seen = used_value\n  call host_probe()\n!CONTAINS\n" + "\n".join([
            "  subroutine argument_probe(dummy_name)",
            "    integer, intent(inout) :: dummy_name",
            "    dummy_name = 111",
            "    argument_seen = dummy_name",
            "  end subroutine",
            "  subroutine host_probe()",
            "    host_seen = host_value",
            "  end subroutine",
        ]),
        [("actual_value /= 111", "argument-association"), ("argument_seen /= 111", "argument-seen"),
         ("use_seen /= 222", "use-association"), ("host_seen /= 333", "host-association")],
        prefix_modules=prefix,
    )


def argument_association_source():
    return source_program(
        "argument_association_lifetime",
        "S19.5.1.2-001",
        FACETS_BY_RULE["S19.5.1.2-001"],
        "  integer :: actual_value, formal, a, b, first_seen, second_seen",
        "\n".join([
            "  actual_value = 1",
            "  formal = -777",
            "  a = 1",
            "  b = 2",
            "  first_seen = -1",
            "  second_seen = -2",
        ]),
        "  call rename_probe(actual_value)\n  call set_dummy(a, 42, first_seen)\n  call set_dummy(b, 77, second_seen)\n!CONTAINS\n" + "\n".join([
            "  subroutine rename_probe(formal)",
            "    integer, intent(inout) :: formal",
            "    formal = 42",
            "  end subroutine",
            "  subroutine set_dummy(d, value, seen)",
            "    integer, intent(inout) :: d",
            "    integer, intent(in) :: value",
            "    integer, intent(out) :: seen",
            "    d = value",
            "    seen = d",
            "  end subroutine",
        ]),
        [("actual_value /= 42", "dummy-accesses-effective"), ("formal /= -777", "host-homonym"),
         ("a /= 42", "first-actual"), ("b /= 77", "second-actual"),
         ("first_seen /= 42", "first-seen"), ("second_seen /= 77", "second-seen")],
    )

def procedure_association_source():
    return source_program(
        "argument_association_lifetime",
        "S19.5.1.2-001",
        FACETS_BY_RULE["S19.5.1.2-001"],
        "  integer :: first_actual, second_actual, first_seen, second_seen",
        "\n".join(["  first_actual = 1", "  second_actual = -7", "  first_seen = -1", "  second_seen = -2"]),
        "  call pair_probe(first_actual, second_actual, first_seen, second_seen)\n!CONTAINS\n" + "\n".join([
            "  subroutine pair_probe(first_dummy, second_dummy, first_seen, second_seen)",
            "    integer, intent(inout) :: first_dummy, second_dummy",
            "    integer, intent(out) :: first_seen, second_seen",
            "    first_dummy = 42",
            "    second_dummy = 77",
            "    first_seen = first_dummy",
            "    second_seen = second_dummy",
            "  end subroutine",
        ]),
        [("first_actual /= 42", "first-present-dummy"), ("second_actual /= 77", "second-present-dummy"),
         ("first_seen /= 42", "first-seen"), ("second_seen /= 77", "second-seen")],
    )


def dummy_name_association_source():
    return source_program(
        "argument_association_dummy_name",
        "S19.5.1.2-002",
        FACETS_BY_RULE["S19.5.1.2-002"],
        "  integer :: actual_value, formal",
        "\n".join(["  actual_value = 1", "  formal = -777"]),
        "  call rename_probe(actual_value)\n!CONTAINS\n" + "\n".join([
            "  subroutine rename_probe(formal)",
            "    integer, intent(inout) :: formal",
            "    formal = 42",
            "  end subroutine",
        ]),
        [("actual_value /= 42", "dummy-accesses-effective"), ("formal /= -777", "host-homonym")],
    )


def termination_association_source():
    return source_program(
        "argument_association_termination",
        "S19.5.1.2-003",
        FACETS_BY_RULE["S19.5.1.2-003"],
        "  integer :: a, b, first_seen, second_seen",
        "\n".join(["  a = 1", "  b = 2", "  first_seen = -1", "  second_seen = -2"]),
        "  call set_dummy(a, 42, first_seen)\n  call set_dummy(b, 77, second_seen)\n!CONTAINS\n" + "\n".join([
            "  subroutine set_dummy(d, value, seen)",
            "    integer, intent(inout) :: d",
            "    integer, intent(in) :: value",
            "    integer, intent(out) :: seen",
            "    d = value",
            "    seen = d",
            "  end subroutine",
        ]),
        [("a /= 42", "first-actual"), ("b /= 77", "second-actual"),
         ("first_seen /= 42", "first-seen"), ("second_seen /= 77", "second-seen")],
    )



VARIANTS = {
    "argument_keywords": {"rule": "S19.3.5-001", "facets": FACETS_BY_RULE["S19.3.5-001"], "source": keyword_source},
    "argument_keyword_accessibility": {"rule": "S19.3.5-002", "facets": FACETS_BY_RULE["S19.3.5-002"], "source": keyword_access_source, "evidence": "positive-control"},
    "intrinsic_keywords": {"rule": "S19.3.5-003", "facets": FACETS_BY_RULE["S19.3.5-003"], "source": intrinsic_keyword_source, "evidence": "positive-control"},
    "statement_entities": {"rule": "S19.4-001", "facets": FACETS_BY_RULE["S19.4-001"], "source": statement_entities_source},
    "statement_entity_exceptions": {"rule": "S19.4-002", "facets": FACETS_BY_RULE["S19.4-002"], "source": statement_entity_exceptions_source, "evidence": "positive-control"},
    "construct_entities": {"rule": "S19.4-003", "facets": FACETS_BY_RULE["S19.4-003"], "source": construct_entities_source},
    "implied_do_scope_type": {"rule": "S19.4-006", "facets": FACETS_BY_RULE["S19.4-006"], "source": implied_do_scope_source},
    "index_scope_type": {"rule": "S19.4-007", "facets": FACETS_BY_RULE["S19.4-007"], "source": index_scope_source},
    "local_scope": {"rule": "S19.4-008", "facets": FACETS_BY_RULE["S19.4-008"], "source": local_scope_source},
    "index_exceptions": {"rule": "S19.4-009", "facets": FACETS_BY_RULE["S19.4-009"], "source": index_exceptions_source, "evidence": "positive-control"},
    "associate_scope": {"rule": "S19.4-010", "facets": FACETS_BY_RULE["S19.4-010"], "source": associate_scope_source},
    "select_rank_scope": {"rule": "S19.4-012", "facets": FACETS_BY_RULE["S19.4-012"], "source": select_rank_scope_source},
    "select_type_scope": {"rule": "S19.4-013", "facets": FACETS_BY_RULE["S19.4-013"], "source": select_type_scope_source},
    "statement_function_scope": {"rule": "S19.4-014", "facets": FACETS_BY_RULE["S19.4-014"], "source": statement_function_scope_source},
    "name_association_cross_scope": {"rule": "S19.5.1.1-001", "facets": FACETS_BY_RULE["S19.5.1.1-001"], "source": name_association_forms_source},
    "argument_association_lifetime": {"rule": "S19.5.1.2-001", "facets": FACETS_BY_RULE["S19.5.1.2-001"], "source": procedure_association_source},
    "argument_association_dummy_name": {"rule": "S19.5.1.2-002", "facets": FACETS_BY_RULE["S19.5.1.2-002"], "source": dummy_name_association_source},
    "argument_association_termination": {"rule": "S19.5.1.2-003", "facets": FACETS_BY_RULE["S19.5.1.2-003"], "source": termination_association_source},
}

MUTATION_PLANS = {
    "argument_keywords": [
        mutation("internal-keyword-to-positional-sentinel", [site("call internal_proc(alpha=21)", "call internal_proc(alpha)")], "uses host sentinel instead of keyword literal"),
        mutation("interface-keyword-to-positional-sentinel", [site("call interface_body_proc(iface_arg=31)", "call interface_body_proc(iface_arg)")], "uses host sentinel instead of interface keyword literal"),
        mutation("procedure-pointer-keyword-to-positional-sentinel", [site("call proc_ptr(ptr_arg=41)", "call proc_ptr(ptr_arg)")], "uses host sentinel instead of procedure-declaration keyword literal"),
    ],
    "argument_keyword_accessibility": [
        mutation("use-keyword-to-positional-sentinel", [site("call used_proc(use_arg=12)", "call used_proc(use_arg)")], "uses local sentinel instead of USE-associated keyword literal"),
        mutation("host-keyword-to-positional-sentinel", [site("call host_proc(host_arg=13)", "call host_proc(host_arg)")], "uses local sentinel instead of host-associated keyword literal"),
    ],
    "intrinsic_keywords": [mutation("merge-keywords-to-positional-sentinels", [site("merge(tsource=7, fsource=9, mask=.true.)", "merge(tsource, fsource, mask)")], "uses local sentinels instead of intrinsic keyword literals")],
    "statement_entities": [
        mutation("array-constructor-remove-implied-do", [site("ac_values = [(i, i = 1, 3)]", "ac_values = [i, i + 1, i + 2]")], "removes ac-implied-do and uses outer scalar"),
        mutation("data-implied-do-reverse", [site("data (data_values(di), di = 1, 3) / 10, 20, 30 /", "data (data_values(di), di = 3, 1, -1) / 10, 20, 30 /")], "keeps DATA implied DO conforming but reverses initialized elements"),
        mutation("forall-statement-range", [site("forall (k = 1:3) forall_values(k) = k + 40", "forall (k = 2:3) forall_values(k) = k + 40")], "keeps FORALL statement valid but leaves first element unchanged"),
        mutation("statement-function-expression", [site("sf(q) = q + 1", "sf(q) = q + 2")], "changes statement-function dummy expression"),
    ],
    "statement_entity_exceptions": [
        mutation("common-data-reverse", [site("data (idx_values(idx), idx = 1, 3) / 101, 102, 103 /", "data (idx_values(idx), idx = 3, 1, -1) / 101, 102, 103 /")], "common block homonym DATA implied DO remains conforming but fails values"),
        mutation("scalar-array-constructor-remove-implied-do", [site("scalar_values = [(i, i = 1, 3)]", "scalar_values = [i, i + 1, i + 2]")], "removes scalar-homonym implied DO"),
    ],
    "construct_entities": [
        mutation("do-concurrent-range", [site("do concurrent (i = 1:3)\n    dc_values(i) = i\n  end do", "do concurrent (i = 2:3)\n    dc_values(i) = i\n  end do")], "changes DO CONCURRENT index coverage"),
        mutation("forall-range", [site("forall (i = 1:3)\n    forall_values(i) = i + 10\n  end forall", "forall (i = 2:3)\n    forall_values(i) = i + 10\n  end forall")], "changes FORALL construct index coverage"),
        mutation("associate-to-outer-assignment", [site("associate (item => target)\n    item = 303\n    assoc_seen = item\n  end associate", "item = 303\n  assoc_seen = item")], "removes ASSOCIATE construct association"),
        mutation("select-rank-to-host-assignment", [site("select rank (item => a)\n    rank (1)\n      item(1) = 404\n      seen = rank(item) + size(item)\n    rank default\n      seen = -404\n    end select", "seen = item")], "removes SELECT RANK associate name"),
        mutation("select-type-to-outer-assignment", [site("select type (item => poly)\n  type is (child_t)\n    item%tag = 505\n    item%payload = 506\n    type_seen = item%tag + item%payload\n  class default\n    type_seen = -5000\n  end select", "item = 505\n  type_seen = item")], "removes SELECT TYPE associate name"),
        mutation("remove-local-locality", [site(" local(local_value)", "")], "LOCAL removal changes outer local_value in one-iteration construct"),
        mutation("block-to-outer-assignment", [site("block\n    integer :: x\n    x = 55\n    block_seen = x\n  end block", "x = 55\n  block_seen = x")], "removes BLOCK declaration scope"),
        mutation("block-use-to-outer-assignment", [site("block\n    use scoping_block_use_provider, only: block_use\n    block_use = 606\n  end block", "block_use = 606")], "removes BLOCK USE association"),
    ],
    "implied_do_scope_type": [
        mutation("array-constructor-remove-implied-do", [site("values = [(i, i = 1, 3)]", "values = [i, i + 1, i + 2]")], "removes ac-implied-do scope"),
        mutation("data-implied-do-reverse", [site("data (data_values(di), di = 1, 3) / 10, 20, 30 /", "data (data_values(di), di = 3, 1, -1) / 10, 20, 30 /")], "changes data-implied-do control"),
        mutation("implicit-letter-to-default", [site("implicit integer(kind=k2) (p)", "implicit integer (p)")], "changes enclosing implicit type source"),
        mutation(
            "host-ac-implied-do-to-ordinary-do",
            [site(
                "    host_values = [(host_ac, host_ac = 1, 3)]",
                "    do host_ac = 1, 3\n      host_values(host_ac) = host_ac\n    end do"
            )],
            "replaces ac-implied-do statement entity with an ordinary DO that aliases the module variable",
        ),
    ],
    "index_scope_type": [
        mutation("do-concurrent-range", [site("do concurrent (i = 1:3)\n    dc_values(i) = i\n  end do", "do concurrent (i = 2:3)\n    dc_values(i) = i\n  end do")], "changes index coverage"),
        mutation("forall-statement-range", [site("forall (k = 1:3) forall_stmt(k) = k + 10", "forall (k = 2:3) forall_stmt(k) = k + 10")], "changes FORALL statement index coverage"),
        mutation("forall-construct-range", [site("forall (m = 1:3)\n    forall_construct(m) = m + 20\n  end forall", "forall (m = 2:3)\n    forall_construct(m) = m + 20\n  end forall")], "changes FORALL construct index coverage"),
        mutation("implicit-letter-to-default", [site("implicit integer(kind=k2) (p)", "implicit integer (p)")], "changes enclosing implicit type for index"),
        mutation(
            "host-index-do-concurrent-to-ordinary-do",
            [site(
                "    do concurrent (host_idx = 1:3)\n      host_index_values(host_idx) = host_idx\n    end do",
                "    do host_idx = 1, 3\n      host_index_values(host_idx) = host_idx\n    end do"
            )],
            "replaces construct index with an ordinary DO that aliases the module variable",
        ),
    ],
    "local_scope": [mutation("remove-local-spec", [site(" local(local_value)", "")], "LOCAL removal changes outer variable"), mutation("remove-local-init-spec", [site(" local_init(init_value)", "")], "LOCAL_INIT removal changes outer variable")],
    "index_exceptions": [mutation("scalar-index-range", [site("do concurrent (i = 1:3)\n    scalar_values(i) = i\n  end do", "do concurrent (i = 2:3)\n    scalar_values(i) = i\n  end do")], "changes scalar-homonym index coverage"), mutation("common-index-range", [site("do concurrent (idx = 1:3)\n    common_values(idx) = idx + 10\n  end do", "do concurrent (idx = 2:3)\n    common_values(idx) = idx + 10\n  end do")], "changes common-block-homonym index coverage")],
    "associate_scope": [mutation("associate-to-outer", [site("associate (item => target)\n    item = 303\n    seen = item\n  end associate", "item = 303\n  seen = item")], "removes ASSOCIATE construct association")],
    "select_rank_scope": [mutation("select-rank-to-host", [site("select rank (item => a)\n    rank (1)\n      item(1) = 404\n      seen = rank(item) + size(item)\n    rank default\n      seen = -404\n    end select", "seen = item")], "removes SELECT RANK associate name")],
    "select_type_scope": [mutation("select-type-to-outer", [site("select type (item => poly)\n  type is (child_t)\n    item%tag = 505\n    item%payload = 506\n    seen = item%tag + item%payload\n  class default\n    seen = -5000\n  end select", "item = 505\n  seen = item")], "removes SELECT TYPE associate name")],
    "statement_function_scope": [mutation("statement-function-expression", [site("sf(q) = q + 1", "sf(q) = q + 2")], "changes statement-function dummy expression"), mutation("implicit-statement-function-expression", [site("sg(r) = r + 2", "sg(r) = r + 3")], "changes implicit-typed statement-function dummy expression")],
    "name_association_cross_scope": [mutation("remove-argument-call", [site("call argument_probe(actual_value)", "actual_value = actual_value")], "removes argument association"), mutation("use-wrong-local", [site("use_seen = used_value", "use_seen = actual_value")], "removes USE-associated access"), mutation("host-wrong-local", [site("host_seen = host_value", "host_seen = actual_value")], "removes host-associated access")],
    "argument_association_lifetime": [
        mutation("remove-pair-procedure-reference", [site("call pair_probe(first_actual, second_actual, first_seen, second_seen)", "first_actual = first_actual")], "removes procedure reference association"),
        mutation("change-first-dummy-assignment", [site("first_dummy = 42", "first_dummy = 43")], "changes first present dummy assignment"),
        mutation("change-second-dummy-assignment", [site("second_dummy = 77", "second_dummy = 78")], "changes second present dummy assignment"),
    ],
    "argument_association_dummy_name": [
        mutation("remove-rename-probe", [site("call rename_probe(actual_value)", "actual_value = actual_value")], "removes dummy-name access to effective argument"),
        mutation("change-dummy-assignment", [site("formal = 42", "formal = 43")], "changes dummy assignment through procedure-local name"),
    ],
    "argument_association_termination": [
        mutation("first-call-to-second-actual", [site("call set_dummy(a, 42, first_seen)", "call set_dummy(b, 42, first_seen)")], "changes effective argument of first invocation"),
        mutation("remove-second-call", [site("call set_dummy(b, 77, second_seen)", "b = b")], "removes subsequent invocation association"),
    ],
}


def mutate_source(spec, plan, *, allow_identical=False):
    source = spec["source"]
    for item in plan["replacements"]:
        expected, replacement = item["expected"], item["replacement"]
        if source.count(expected) != 1:
            raise ValueError(f"{spec['variant']}::{plan['id']} does not bind exactly one parent span: {expected!r} count={source.count(expected)}")
        if not allow_identical and expected == replacement:
            raise ValueError(f"{plan['id']} is identical")
        source = source.replace(expected, replacement, 1)
    if not allow_identical and source == spec["source"]:
        raise ValueError(f"{plan['id']} did not change parent")
    return source


def source_specs():
    specs = {}
    for variant, config in VARIANTS.items():
        source, stdout = config["source"]()
        # Override rule/facets when a shared source function serves a sibling rule.
        rule = config["rule"]
        facets = list(config["facets"])
        lines = source.splitlines()
        lines = [line for line in lines if not line.startswith("! rule: ") and not line.startswith("! covers: ")]
        header = [f"! rule: {rule}"] + [f"! covers: {facet}" for facet in facets]
        source = "\n".join(header + lines) + ("\n" if source.endswith("\n") else "")
        name = ident(rule, variant)
        raw = source.encode("ascii")
        mutations = []
        for plan in MUTATION_PLANS[variant]:
            mutant = mutate_source({"source": source, "variant": variant}, plan)
            entry = copy.deepcopy(plan)
            entry["mutant_sha256"] = sha(mutant.encode("ascii"))
            mutations.append(entry)
        specs[name] = dict(
            id=name,
            variant=variant,
            rule=rule,
            facets=facets,
            evidence=config.get("evidence", "effect"),
            source=source,
            stdout=stdout,
            source_sha256=sha(raw),
            mutations=mutations,
        )
    return specs


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["variant"])
        manifest = dict(
            schema_version=1,
            id=spec["id"],
            rule=spec["rule"],
            facets=spec["facets"],
            evidence=spec["evidence"],
            standard="f2023",
            oracle_basis="standard",
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


def section_for_rule(rule):
    if rule.startswith("S19.3.5"):
        return "19.3.5"
    if rule.startswith("S19.4"):
        return "19.4"
    if rule.startswith("S19.5.1.1"):
        return "19.5.1.1"
    if rule.startswith("S19.5.1.2"):
        return "19.5.1.2"
    raise ValueError(rule)


def synced_catalogue(section, catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        if section_for_rule(rule) != section:
            continue
        owner = by_rule[rule]
        for facet in facets:
            owner["pending"].pop(facet, None)
        expected = EXPECTED_REMAINING[rule]
        if set(owner.get("pending", {})) != expected:
            raise ValueError(f"unexpected pending for {rule}: {set(owner.get('pending', {}))} != {expected}")
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    # Also assert untouched known pending sets in 19.4 for unbound rules.
    if section == "19.4":
        for rule in ("S19.4-004", "S19.4-005", "S19.4-011"):
            if set(by_rule[rule].get("pending", {})) != EXPECTED_REMAINING[rule]:
                raise ValueError(f"unexpected pending for untouched {rule}")
    return updated


def rendered_view(section, catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin = f"<!-- BEGIN GENERATED {section} -->"
    end = f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated region boundaries changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "This source packet records source accounting and pending plans only, not fixture approval.",
        "This source packet records source accounting; selected pending facets now have bounded runtime fixtures.")
    summary = (
        SUMMARY_BEGIN + "\n"
        f"## Scoping/name-association fixture observations for {section}\n\n"
        "The `scoping_19_3_19_5` packet adds complete run/effect/f2023 programs with exact integer, "
        "logical, kind, rank, and outer-sentinel observations. Each same-spelling construct or statement "
        "entity uses a distinct outer sentinel, and permanent feature mutants remove or alter the scoping "
        "construct rather than only changing the oracle. CHANGE TEAM/coarray facets and unnumbered "
        "prohibitions without required diagnostics remain pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before:
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for section, rel in CATALOGUES.items():
        catalogue = json.loads((root / rel).read_text())
        updated = synced_catalogue(section, catalogue)
        updated_catalogues[section] = updated
        updated_views[section] = rendered_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, rel in CATALOGUES.items():
            if json.loads((root / rel).read_text()) != updated_catalogues[section]:
                stale.append(rel)
            if (root / VIEWS[section]).read_text() != updated_views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale scoping fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            for section, rel in CATALOGUES.items():
                (root / rel).write_text(json.dumps(updated_catalogues[section], indent=2) + "\n")
                (root / VIEWS[section]).write_text(updated_views[section])
    return specs


def compiler_std_flag(compiler, standard):
    name = Path(compiler).name.lower()
    return f"--std={standard}" if "lfortran" in name else f"-std={standard}"


def compile_and_run(source, compiler, standard, case_name):
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    work = WORK_DIR / case_name
    work.mkdir(parents=True)
    try:
        (work / "source.f90").write_text(source)
        compile_cmd = [compiler, compiler_std_flag(compiler, standard), "source.f90", "-o", "program"]
        cr = subprocess.run(compile_cmd, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        if cr.returncode != 0:
            return dict(phase="compile", returncode=cr.returncode, stdout=cr.stdout, stderr=cr.stderr)
        rr = subprocess.run([str(work / "program")], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        return dict(phase="run", returncode=rr.returncode, stdout=rr.stdout, stderr=rr.stderr)
    finally:
        shutil.rmtree(WORK_DIR, ignore_errors=True)


def mutation_matrix(compiler, standard, *, sabotage_first=False):
    _, specs = build_corpus(ROOT)
    rows, survivors, compile_failures, parent_failures = [], [], [], []
    first = True
    for spec in specs.values():
        parent = compile_and_run(spec["source"], compiler, standard, spec["variant"] + "_parent")
        if parent["phase"] != "run" or parent["returncode"] != 0 or parent["stdout"] != spec["stdout"]:
            parent_failures.append(dict(case=spec["id"], **parent))
            continue
        for plan in spec["mutations"]:
            active = copy.deepcopy(plan)
            allow_identical = False
            if sabotage_first and first:
                active["replacements"][0]["replacement"] = active["replacements"][0]["expected"]
                active["id"] += "__identity_sabotage"
                allow_identical = True
                first = False
            mutant = mutate_source(spec, active, allow_identical=allow_identical)
            result = compile_and_run(mutant, compiler, standard, spec["variant"] + "_" + active["id"][:24])
            row = dict(case=spec["id"], mutation=active["id"], phase=result["phase"],
                       returncode=result["returncode"], stdout=result["stdout"], stderr=result["stderr"])
            rows.append(row)
            if result["phase"] != "run":
                compile_failures.append(row)
            elif result["returncode"] == 0 and result["stdout"] == spec["stdout"]:
                survivors.append(row)
    return dict(rows=rows, survivors=survivors, compile_failures=compile_failures, parent_failures=parent_failures)


def run_mutation_check(compiler, standard):
    matrix = mutation_matrix(compiler, standard)
    if matrix["parent_failures"] or matrix["compile_failures"] or matrix["survivors"]:
        print(json.dumps(matrix, indent=2))
        raise SystemExit(1)
    print(f"Mutation check passed: {len(matrix['rows'])}/{len(matrix['rows'])} mutants failed on {compiler}.")


def prove_non_vacuous(compiler, standard):
    matrix = mutation_matrix(compiler, standard, sabotage_first=True)
    if not matrix["survivors"]:
        print(json.dumps(matrix, indent=2))
        raise SystemExit("identity sabotage was not reported as surviving")
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
    parser.add_argument("--compiler")
    parser.add_argument("--standard", default="f2023")
    args = parser.parse_args()
    if args.mutation_check or args.prove_non_vacuous:
        if not args.compiler:
            parser.error("--compiler is required for mutation modes")
        if args.mutation_check:
            run_mutation_check(args.compiler, args.standard)
        else:
            prove_non_vacuous(args.compiler, args.standard)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    action = "Checked" if args.check else "Generated"
    print(f"{action} {len(specs)} scoping cases covering {sum(len(f) for f in FACETS_BY_RULE.values())} facets.")


if __name__ == "__main__":
    main()
