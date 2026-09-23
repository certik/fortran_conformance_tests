#!/usr/bin/env python3
"""DO construct form fixtures for Fortran 2023 subclause 11.1.7.2."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha

ROOT = Path(__file__).resolve().parents[1]
SECTION = "11.1.7.2"
CATALOGUE = "doc/catalogues/form_of_the_do_construct_11_1_7_2.json"
VIEW = "doc/fortran_2023_11_1_7_2.md"
PREFIX = "do_construct_form_"
SUMMARY_BEGIN = "<!-- BEGIN DO CONSTRUCT FORM FIXTURES -->"
SUMMARY_END = "<!-- END DO CONSTRUCT FORM FIXTURES -->"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "recovery",
    "cannot read module", "segmentation fault", "traceback",
)

SELECTED = {
    "R1119": ["do-construct-form"],
    "R1120": ["nonlabel-do-stmt-alternative", "label-do-stmt-alternative"],
    "R1121": [
        "unnamed-label-do-stmt", "label-do-with-loop-control",
    ],
    "R1122": [
        "unnamed-nonlabel-do-stmt", "named-nonlabel-do-stmt",
        "nonlabel-do-with-loop-control", "nonlabel-do-without-loop-control",
    ],
    "R1125": ["concurrent-header-without-type-spec", "concurrent-header-with-integer-type-spec"],
    "R1126": ["concurrent-control-default-step", "concurrent-control-explicit-step"],
    "R1128": ["concurrent-step-expression-form"],
    "R1129": ["single-locality-spec"],
    "R1130": ["default-none-locality"],
    "R1133": ["continue-stmt-alternative"],
    "C1135": [
        "matching-do-construct-name-control",
        "named-do-missing-end-name-rejected",
        "unnamed-do-end-name-rejected",
    ],
}
FACETS_BY_RULE = {rule: tuple(facets) for rule, facets in SELECTED.items()}
REMAINING_PENDING = {
    "R1121": {
        "named-label-do-stmt": (
            "PENDING positive admission plan for a named label-do-stmt; the frozen target rejects "
            "the conforming `name: DO label ... label END DO name` probe, so this packet leaves the "
            "facet pending rather than recording a one-sided fixture."
        ),
        "label-do-without-loop-control": (
            "PENDING positive admission plan for a label-do-stmt without loop-control; the frozen "
            "target rejects a conforming bounded `DO label` plus internal EXIT probe, so this packet "
            "leaves the facet pending rather than recording a one-sided fixture."
        ),
    }
}

ORACLE_PREFIXES = {
    "R1119": "R1119 DO construct form admission fixtures: ",
    "R1120": "R1120 DO statement alternative admission fixtures: ",
    "R1121": "R1121 label DO statement form fixtures: ",
    "R1122": "R1122 nonlabel DO statement form fixtures: ",
    "R1125": "R1125 DO CONCURRENT header admission fixtures: ",
    "R1126": "R1126 concurrent-control admission fixture: ",
    "R1128": "R1128 concurrent-step expression admission fixture: ",
    "R1129": "R1129 concurrent-locality admission fixture: ",
    "R1130": "R1130 DEFAULT(NONE) locality admission fixture: ",
    "R1133": "R1133 CONTINUE end-do admission fixture: ",
    "C1135": "C1135 DO construct-name diagnostic fixtures: ",
}
LIMIT_PREFIXES = {
    rule: prefix.replace(" fixtures: ", " fixture boundaries: ")
    for rule, prefix in ORACLE_PREFIXES.items()
}
ORACLES = {
    "R1119": ORACLE_PREFIXES["R1119"] + (
        "one complete run/positive-control/f2023 program contains a DO statement, a block that appends "
        "three hand-computed values to a sentinel-initialized trace array, and the corresponding END DO. "
        "The exact trace [11,12,13], count three, completion stdout, empty stderr and exit0 prove that the "
        "source form was admitted and the block associated with that DO construct was reached. The asserted "
        "values are only an admission trace; loop termination and post-loop DO-variable semantics remain with "
        "11.1.7.4."
    ),
    "R1120": ORACLE_PREFIXES["R1120"] + (
        "two complete programs admit the nonlabel and label do-stmt alternatives. The nonlabel case uses an "
        "ordinary END DO. The label case uses a labeled CONTINUE end-do and then executes a statement after "
        "the label exactly once, so a parser that extends the label-DO range beyond the labeled statement or "
        "does not bind the label form fails the sentinel trace and after-label count."
    ),
    "R1121": ORACLE_PREFIXES["R1121"] + (
        "two complete programs admit an unnamed label-do-stmt and a label-do-stmt with loop-control. Both use a "
        "labeled CONTINUE end-do, and both place a statement after the label that must execute exactly once after "
        "the construct rather than once per iteration."
    ),
    "R1122": ORACLE_PREFIXES["R1122"] + (
        "four complete programs admit unnamed, named, loop-controlled and no-loop-control nonlabel DO statements. "
        "The named case checks a matching END DO name. The no-loop-control case uses an EXIT guard to bound the "
        "otherwise indefinite form and observes the exact three-value trace."
    ),
    "R1125": ORACLE_PREFIXES["R1125"] + (
        "two complete DO CONCURRENT programs admit concurrent headers without an integer type specifier and with "
        "`integer ::` before the control list. Each iteration writes only its own array element, so no evaluation "
        "order, temporary, image, or reduction order is observed; the oracle is the exact final array contents and "
        "count of non-sentinel elements."
    ),
    "R1126": ORACLE_PREFIXES["R1126"] + (
        "two complete DO CONCURRENT programs admit default-step and explicit-step concurrent controls. The explicit "
        "step case uses `i = 1:5:2`, writes elements 1, 3 and 5 of a sentinel array, and requires elements 2 and 4 "
        "to remain sentinel, discriminating an ignored or misparsed step from the admitted form."
    ),
    "R1128": ORACLE_PREFIXES["R1128"] + (
        "one complete DO CONCURRENT program admits a scalar integer expression as the concurrent-step. The step is "
        "the ordinary integer variable `step`, initialized to two before the construct. The final sentinel array "
        "requires exactly the odd elements to have been written, so replacing the expression value changes the trace."
    ),
    "R1129": ORACLE_PREFIXES["R1129"] + (
        "one complete DO CONCURRENT program admits a single concurrent-locality specification. It uses SHARED(offset) "
        "and writes independent array elements as i+offset, observing only final contents, not storage or ordering."
    ),
    "R1130": ORACLE_PREFIXES["R1130"] + (
        "one complete DO CONCURRENT program admits DEFAULT(NONE) together with an explicit SHARED locality list for "
        "the containing-scope variables used in the block. It checks only independent final array contents."
    ),
    "R1133": ORACLE_PREFIXES["R1133"] + (
        "one complete label DO program admits the CONTINUE alternative for end-do. A statement immediately following "
        "the labeled CONTINUE increments an after-label counter once after the construct, discriminating the end-do "
        "boundary from a plausible misparse that includes the following statement in the loop body."
    ),
    "C1135": ORACLE_PREFIXES["C1135"] + (
        "one named positive control and two compile/f2023 negatives isolate construct-name consistency. The named "
        "control uses `outer: do ... end do outer` and runs a three-value trace. The missing-name negative differs "
        "only by deleting `outer` from the corresponding END DO. The unnamed-end-name negative differs from its "
        "unnamed nonlabel control only by adding `inner` to END DO. Diagnostics are line anchored at the END DO "
        "statement and require a real parser/semantic report while excluding unsupported-feature, recovery, ICE and "
        "internal-error routes."
    ),
}
LIMITATIONS = {
    "R1119": LIMIT_PREFIXES["R1119"] + (
        "only the do-construct-form facet is represented. This is admission/control evidence, not a separate "
        "11.1.7.4 execution-semantics claim, and it does not test active-state, DO-variable final value, trip-count "
        "definition, branching, construct-name diagnostics, label diagnostics, or DO CONCURRENT locality semantics."
    ),
    "R1120": LIMIT_PREFIXES["R1120"] + (
        "only the two do-stmt alternatives are represented. The fixtures intentionally avoid R1123 and C1121, which "
        "remain under the open migration followups because pre-existing tests/clause11 cases already cover them."
    ),
    "R1121": LIMIT_PREFIXES["R1121"] + (
        "only the unnamed-label-do-stmt and label-do-with-loop-control admission facets are represented. Named "
        "label DO and label DO without loop-control remain pending because the frozen target rejects simple "
        "conforming probes for those forms. Invalid label target diagnostics, branch-target restrictions and R1123 "
        "loop-control grammar negatives remain pending or explicitly out of this packet."
    ),
    "R1122": LIMIT_PREFIXES["R1122"] + (
        "only four positive nonlabel-do-stmt admission facets are represented. The nonlabel CONTINUE negative is "
        "left pending for a later C1136 diagnostic packet; this packet uses END DO for every nonlabel positive."
    ),
    "R1125": LIMIT_PREFIXES["R1125"] + (
        "only the no-type-spec and integer-type-spec concurrent-header facets are represented. The mask facet remains "
        "pending because the frozen target currently fails a simple conforming masked DO CONCURRENT runtime probe while "
        "the reference passes, so this packet does not ship that admission case without an XFAIL integration path."
    ),
    "R1126": LIMIT_PREFIXES["R1126"] + (
        "only the default-step and explicit-step concurrent-control facets are represented. This packet does not "
        "claim multi-control lists, C1124/C1125 diagnostics, or any DO CONCURRENT scheduling or locality storage effect."
    ),
    "R1128": LIMIT_PREFIXES["R1128"] + (
        "only a scalar integer variable expression used as a concurrent-step is represented. Other expression forms, "
        "constant folding behavior, evaluation order and C1125 references to index names remain pending."
    ),
    "R1129": LIMIT_PREFIXES["R1129"] + (
        "only a single locality-spec is represented. No-locality and multiple-locality forms remain pending. The case "
        "does not observe LOCAL, LOCAL_INIT, REDUCE, allocation, finalization, definability or locality storage effects."
    ),
    "R1130": LIMIT_PREFIXES["R1130"] + (
        "only DEFAULT(NONE) admission is represented under R1130. LOCAL, LOCAL_INIT, REDUCE and SHARED-specific R1130 "
        "facets remain pending except that SHARED is used only as supporting syntax for R1129/R1130 controls."
    ),
    "R1133": LIMIT_PREFIXES["R1133"] + (
        "only the CONTINUE end-do alternative is represented. The END DO alternative is already present as supporting "
        "syntax in other positives but is not claimed as a discharged R1133 facet here."
    ),
    "C1135": LIMIT_PREFIXES["C1135"] + (
        "only the matching-name control, named missing END DO name, and unnamed DO with END DO name facets are "
        "represented. The end-name mismatch facet remains pending because the frozen target reports the simple "
        "one-property mismatch probe with an internal compiler error rather than a diagnostic. Diagnostic wording, "
        "fatal status and printed rule numbers are not part of the oracle."
    ),
}


def identifier(variant):
    return SPECS[variant]["id"]


def check_block(expr, token):
    return f"  if ({expr}) then\n    write(*,'(a)') '{token}'\n    error stop\n  end if\n"


def finish_success(name, body, completion, checks):
    text = body
    for expr, token in checks:
        text += check_block(expr, token)
    text += f"  write(*,'(a)') '{completion}'\nend program {name}\n"
    return text


def serial_loop_source(name, rule, facet, do_line, end_line, *, values="11, 12, 13",
                       expected="[11, 12, 13]", after_label=False, no_control=False):
    completion = "DO CONSTRUCT FORM " + name.upper().replace("_", " ") + " OK"
    body = (
        f"! rule: {rule}\n! covers: {facet}\n"
        f"program {name}\n"
        "  implicit none\n"
        "  integer :: i, n, after_label_count\n"
        "  integer :: trace(3)\n"
        "  trace = -777\n  n = 0\n  after_label_count = 0\n"
        f"  {do_line}\n"
        "    n = n + 1\n"
        "    if (n > 3) then\n      write(*,'(a)') 'DCF:too-many-iterations'\n      error stop\n    end if\n"
    )
    if no_control:
        body += "    trace(n) = 20 + n\n    if (n == 3) exit\n"
    else:
        body += "    trace(n) = 10 + i\n"
    body += f"  {end_line}\n"
    if after_label:
        body += "  after_label_count = after_label_count + 1\n"
    checks = [
        ("n /= 3", "DCF:" + name + ":count"),
        (f"any(trace /= {expected})", "DCF:" + name + ":trace"),
    ]
    if after_label:
        checks.append(("after_label_count /= 1", "DCF:" + name + ":after-label"))
    else:
        checks.append(("after_label_count /= 0", "DCF:" + name + ":after-label-sentinel"))
    return finish_success(name, body, completion, checks), completion + "\n"


def concurrent_source(name, rule, facet, header, locality="", expected="[11, 12, 13, 14]", size=4,
                      sentinel_checks=None, offset_decl=False, count_expected=4):
    completion = "DO CONSTRUCT FORM " + name.upper().replace("_", " ") + " OK"
    decl = "  integer :: trace(" + str(size) + ")\n"
    if "integer ::" not in header.lower():
        decl += "  integer :: i\n"
    init = "  trace = -777\n"
    if offset_decl:
        decl += "  integer :: offset\n"
        init += "  offset = 30\n"
    body = (
        f"! rule: {rule}\n! covers: {facet}\n"
        f"program {name}\n"
        "  implicit none\n" + decl + init +
        f"  do concurrent {header}{locality}\n"
    )
    if offset_decl:
        body += "    trace(i) = offset + i\n"
    else:
        body += "    trace(i) = 10 + i\n"
    body += "  end do\n"
    checks = [(f"any(trace /= {expected})", "DCF:" + name + ":trace")]
    if sentinel_checks:
        checks.extend(sentinel_checks)
    checks.append(("count(trace /= -777) /= " + str(count_expected), "DCF:" + name + ":count"))
    return finish_success(name, body, completion, checks), completion + "\n"


def invalid_source(name, rule, facet, lines):
    return "\n".join([f"! rule: {rule}", f"! covers: {facet}"] + lines) + "\n"


SPECS = {}

def add_valid(variant, rule, facet, source, stdout, mutations, controls=None):
    case_id = rule.replace(".", "_").replace("-", "_") + "_valid__" + PREFIX + variant
    SPECS[variant] = dict(
        id=case_id, variant=variant, kind="valid", evidence="positive-control", rule=rule,
        facets=[facet], source=source, stdout=stdout, mutations=mutations, controls=controls or [])


def add_invalid(variant, rule, facet, source, line, messages, control_id, repair):
    case_id = rule.replace(".", "_").replace("-", "_") + "_invalid__" + PREFIX + variant
    SPECS[variant] = dict(
        id=case_id, variant=variant, kind="invalid", evidence="effect", rule=rule,
        facets=[facet], source=source, diagnostic_line=line, messages=list(messages),
        control_id=control_id, repair=repair)


src, out = serial_loop_source(
    "do_construct_form_basic_construct", "R1119", "do-construct-form",
    "do i = 1, 3", "end do")
add_valid("basic_construct", "R1119", "do-construct-form", src, out,
          [dict(id="upper-bound-two", expected="do i = 1, 3", replacement="do i = 1, 2")])

src, out = serial_loop_source(
    "do_construct_form_nonlabel_statement", "R1120", "nonlabel-do-stmt-alternative",
    "do i = 1, 3", "end do")
add_valid("nonlabel_statement", "R1120", "nonlabel-do-stmt-alternative", src, out,
          [dict(id="upper-bound-two", expected="do i = 1, 3", replacement="do i = 1, 2")])

src, out = serial_loop_source(
    "do_construct_form_label_statement", "R1120", "label-do-stmt-alternative",
    "do 120 i = 1, 3", "120 continue", after_label=True)
add_valid("label_statement", "R1120", "label-do-stmt-alternative", src, out,
          [dict(id="label-target-changed", expected="do 120 i = 1, 3", replacement="do 121 i = 1, 3")])

src, out = serial_loop_source(
    "do_construct_form_unnamed_label", "R1121", "unnamed-label-do-stmt",
    "do 130 i = 1, 3", "130 continue", after_label=True)
add_valid("unnamed_label", "R1121", "unnamed-label-do-stmt", src, out,
          [dict(id="label-target-changed", expected="do 130 i = 1, 3", replacement="do 131 i = 1, 3")])

src, out = serial_loop_source(
    "do_construct_form_label_with_loop_control", "R1121", "label-do-with-loop-control",
    "do 150 i = 1, 3", "150 continue", after_label=True)
add_valid("label_with_loop_control", "R1121", "label-do-with-loop-control", src, out,
          [dict(id="loop-upper-bound-two", expected="do 150 i = 1, 3", replacement="do 150 i = 1, 2")])

src, out = serial_loop_source(
    "do_construct_form_unnamed_nonlabel", "R1122", "unnamed-nonlabel-do-stmt",
    "do i = 1, 3", "end do")
add_valid("unnamed_nonlabel", "R1122", "unnamed-nonlabel-do-stmt", src, out,
          [dict(id="loop-upper-bound-two", expected="do i = 1, 3", replacement="do i = 1, 2")])

src, out = serial_loop_source(
    "do_construct_form_named_nonlabel", "R1122", "named-nonlabel-do-stmt",
    "outer: do i = 1, 3", "end do outer")
add_valid("named_nonlabel", "R1122", "named-nonlabel-do-stmt", src, out,
          [dict(id="construct-name-changed", expected="end do outer", replacement="end do wrong")])

src, out = serial_loop_source(
    "do_construct_form_nonlabel_with_loop_control", "R1122", "nonlabel-do-with-loop-control",
    "do i = 1, 3", "end do")
add_valid("nonlabel_with_loop_control", "R1122", "nonlabel-do-with-loop-control", src, out,
          [dict(id="loop-lower-bound-two", expected="do i = 1, 3", replacement="do i = 2, 3")])

src, out = serial_loop_source(
    "do_construct_form_nonlabel_without_loop_control", "R1122", "nonlabel-do-without-loop-control",
    "do", "end do", values="21, 22, 23", expected="[21, 22, 23]", no_control=True)
add_valid("nonlabel_without_loop_control", "R1122", "nonlabel-do-without-loop-control", src, out,
          [dict(id="exit-threshold-two", expected="if (n == 3) exit", replacement="if (n == 2) exit")])

src, out = concurrent_source(
    "do_construct_form_concurrent_header_without_type", "R1125", "concurrent-header-without-type-spec",
    "(i = 1:4)")
add_valid("concurrent_header_without_type", "R1125", "concurrent-header-without-type-spec", src, out,
          [dict(id="concurrent-upper-three", expected="(i = 1:4)", replacement="(i = 1:3)")])

src, out = concurrent_source(
    "do_construct_form_concurrent_header_with_type", "R1125", "concurrent-header-with-integer-type-spec",
    "(integer :: i = 1:4)")
add_valid("concurrent_header_with_type", "R1125", "concurrent-header-with-integer-type-spec", src, out,
          [dict(id="remove-integer-type-spec", expected="(integer :: i = 1:4)", replacement="(i = 1:3)")])

src, out = concurrent_source(
    "do_construct_form_concurrent_default_step", "R1126", "concurrent-control-default-step",
    "(i = 1:4)")
add_valid("concurrent_default_step", "R1126", "concurrent-control-default-step", src, out,
          [dict(id="default-step-upper-three", expected="(i = 1:4)", replacement="(i = 1:3)")])

src, out = concurrent_source(
    "do_construct_form_concurrent_explicit_step", "R1126", "concurrent-control-explicit-step",
    "(i = 1:5:2)", expected="[11, -777, 13, -777, 15]", size=5,
    sentinel_checks=[("trace(2) /= -777", "DCF:explicit-step:sentinel-two"),
                     ("trace(4) /= -777", "DCF:explicit-step:sentinel-four")],
    count_expected=3)
add_valid("concurrent_explicit_step", "R1126", "concurrent-control-explicit-step", src, out,
          [dict(id="step-one", expected="(i = 1:5:2)", replacement="(i = 1:5:1)")])

src, out = concurrent_source(
    "do_construct_form_concurrent_step_expression", "R1128", "concurrent-step-expression-form",
    "(i = 1:5:step)", expected="[11, -777, 13, -777, 15]", size=5,
    sentinel_checks=[("trace(2) /= -777", "DCF:step-expression:sentinel-two"),
                     ("trace(4) /= -777", "DCF:step-expression:sentinel-four")],
    count_expected=3)
src = src.replace("  trace = -777\n", "  integer :: step\n  trace = -777\n  step = 2\n", 1)
add_valid("concurrent_step_expression", "R1128", "concurrent-step-expression-form", src, out,
          [dict(id="step-expression-one", expected="step = 2", replacement="step = 1")])

src, out = concurrent_source(
    "do_construct_form_single_locality", "R1129", "single-locality-spec",
    "(i = 1:4)", " shared(offset)", expected="[31, 32, 33, 34]", offset_decl=True)
add_valid("single_locality", "R1129", "single-locality-spec", src, out,
          [dict(id="locality-loop-upper-three", expected="(i = 1:4)", replacement="(i = 1:3)")])

src, out = concurrent_source(
    "do_construct_form_default_none", "R1130", "default-none-locality",
    "(i = 1:4)", " default(none) shared(trace, offset)", expected="[31, 32, 33, 34]",
    offset_decl=True)
add_valid("default_none", "R1130", "default-none-locality", src, out,
          [dict(id="default-none-loop-upper-three", expected="(i = 1:4)", replacement="(i = 1:3)")])

src, out = serial_loop_source(
    "do_construct_form_continue_end", "R1133", "continue-stmt-alternative",
    "do 170 i = 1, 3", "170 continue", after_label=True)
add_valid("continue_end", "R1133", "continue-stmt-alternative", src, out,
          [dict(id="label-target-changed", expected="do 170 i = 1, 3", replacement="do 171 i = 1, 3")])

src, out = serial_loop_source(
    "do_construct_form_matching_construct_name", "C1135", "matching-do-construct-name-control",
    "outer: do i = 1, 3", "end do outer")
add_valid("matching_construct_name", "C1135", "matching-do-construct-name-control", src, out,
          [dict(id="construct-name-changed", expected="end do outer", replacement="end do wrong")])

def line_number(source, needle):
    if source.count(needle) != 1:
        raise ValueError(f"expected one occurrence of {needle!r}")
    return source[:source.index(needle)].count("\n") + 1


def with_header(source, rule, facet):
    lines = source.splitlines()
    if len(lines) < 2 or not lines[0].startswith("! rule: ") or not lines[1].startswith("! covers: "):
        raise ValueError("source header is not the two-line rule/covers form")
    lines[0] = f"! rule: {rule}"
    lines[1] = f"! covers: {facet}"
    return "\n".join(lines) + "\n"


matching_control = SPECS["matching_construct_name"]["source"]
named_missing = with_header(
    matching_control.replace("end do outer", "end do", 1),
    "C1135", "named-do-missing-end-name-rejected")
named_missing_line = line_number(named_missing, "end do\n")
add_invalid("named_missing_end_name", "C1135", "named-do-missing-end-name-rejected",
            named_missing, named_missing_line,
            ["Expected block name of 'outer'", "Newline is unexpected here"],
            identifier("matching_construct_name"),
            dict(line=named_missing_line, expected="end do", replacement="end do outer"))

unnamed_control = SPECS["unnamed_nonlabel"]["source"]
unnamed_named = with_header(
    unnamed_control.replace("end do", "end do inner", 1),
    "C1135", "unnamed-do-end-name-rejected")
unnamed_named_line = line_number(unnamed_named, "end do inner")
add_invalid("unnamed_end_name", "C1135", "unnamed-do-end-name-rejected",
            unnamed_named, unnamed_named_line,
            ["Syntax error in END DO statement", "Token 'inner'"],
            identifier("unnamed_nonlabel"),
            dict(line=unnamed_named_line, expected="end do inner", replacement="end do"))


def mutate_source(spec, mutation):
    raw = spec["source"]
    expected = mutation["expected"]
    if raw.count(expected) != 1:
        raise ValueError(f"{spec['id']} mutation {mutation['id']} does not identify one span")
    return raw.replace(expected, mutation["replacement"], 1)


def source_specs():
    by_variant = copy.deepcopy(SPECS)
    for spec in by_variant.values():
        raw = spec["source"].encode("ascii")
        spec["source_sha256"] = sha(raw)
        for mutation in spec.get("mutations", []):
            mutant = mutate_source(spec, mutation).encode("ascii")
            mutation["mutant_sha256"] = sha(mutant)
    return {spec["id"]: spec for spec in by_variant.values()}


def build_corpus(root=ROOT):
    files = {}
    specs = source_specs()
    for spec in specs.values():
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            expect=dict(phase="compile" if spec["kind"] == "invalid" else "run",
                        outcome="diagnose" if spec["kind"] == "invalid" else "success"),
        )
        if spec["kind"] == "valid":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"].update(exit_code=0, stdout=spec["stdout"], stderr="")
        else:
            manifest["expect"].update(step="source", diagnostic=dict(
                file="source.f90", line=spec["diagnostic_line"], end_line=spec["diagnostic_line"],
                contains_any=spec["messages"], excludes_any=list(EXCLUSIONS)))
        directory = Path(root) / "tests" / "fixtures" / (PREFIX + spec["variant"])
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError(f"{rule} selected facets no longer exist")
        owner.setdefault("pending", {})
        for facet in facets:
            owner["pending"].pop(facet, None)
        for facet, rationale in REMAINING_PENDING.get(rule, {}).items():
            owner["pending"].setdefault(facet, rationale)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## DO construct form fixture packet\n\n"
        "Twenty facets are discharged by complete f2023 fixtures. Seventeen positive\n"
        "admission cases execute exact sentinel-backed traces for nonlabel DO, label DO,\n"
        "no-loop-control DO, labeled CONTINUE end-do, and selected DO CONCURRENT header\n"
        "and locality forms. Three C1135 cases cover one matching construct-name control\n"
        "and two one-property END DO name diagnostics. Label-DO fixtures place an\n"
        "after-label statement outside the labeled range and require it to execute once.\n\n"
        "The packet intentionally does not migrate C1121 or R1123, does not cover branch\n"
        "target facets, and does not claim 11.1.7.4 loop execution semantics such as\n"
        "iteration-count definition or final DO-variable value. Masked DO CONCURRENT and\n"
        "END-name mismatch probes remain pending because the frozen target does not yet\n"
        "provide clean reference-compatible validation for those forms.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("fixture summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return (before + begin + "\n\n" +
            "\n".join(render_requirement(row) for row in catalogue["requirements"]) +
            "\n" + end + after)


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
            raise ValueError("stale DO construct form fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return files, specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    _, specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} DO construct form cases "
          f"for {sum(len(v) for v in FACETS_BY_RULE.values())} facets.")


if __name__ == "__main__":
    main()
