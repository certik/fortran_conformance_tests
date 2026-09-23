#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 control edit descriptors."""

import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha, wrong_oracle_source

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_BEGIN = "<!-- BEGIN CONTROL EDIT DESCRIPTOR FIXTURES -->"
SUMMARY_END = "<!-- END CONTROL EDIT DESCRIPTOR FIXTURES -->"

CATALOGUES = {
    "13.8.1.1": "doc/catalogues/position_editing_13_8_1_1.json",
    "13.8.1.2": "doc/catalogues/t_tl_and_tr_editing_13_8_1_2.json",
    "13.8.1.3": "doc/catalogues/x_editing_13_8_1_3.json",
    "13.8.2": "doc/catalogues/slash_editing_13_8_2.json",
    "13.8.3": "doc/catalogues/colon_editing_13_8_3.json",
    "13.8.4": "doc/catalogues/ss_sp_and_s_editing_13_8_4.json",
    "13.8.5": "doc/catalogues/lzs_lzp_and_lz_editing_13_8_5.json",
    "13.8.7": "doc/catalogues/bn_and_bz_editing_13_8_7.json",
    "13.8.9": "doc/catalogues/dc_and_dp_editing_13_8_9.json",
    "13.9": "doc/catalogues/character_string_edit_descriptors_13_9.json",
}
VIEWS = {section: f"doc/fortran_2023_{section.replace('.', '_')}.md" for section in CATALOGUES}

CASES = [
    dict(
        variant="position_t3_writes_later_blank_fill", section="13.8.1.1", rule="S13.8.1.1-004",
        facets=["skipped-output-filled-with-blanks"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(T3,\"Z\")')", observed="buf", expected="  Z",
        input_mutation=("\"Z\"", "\"Y\""), descriptor="T3", descriptor_replacement="T4",
        descriptor_omission="T3,",
        derivation="T3 makes the next output position 3; p4 fills skipped positions 1-2 with blanks when Z is written."),
    dict(
        variant="position_t1_subsequent_replacement", section="13.8.1.1", rule="S13.8.1.1-005",
        facets=["subsequent-editing-replaces"], kind="char", length=2,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(\"AB\",T1,\"C\")')", observed="buf", expected="CB",
        input_mutation=("\"C\"", "\"D\""), descriptor="T1", descriptor_omission="T1,",
        derivation="The string AB first occupies positions 1-2; T1 repositions to position 1 and the later C replaces A."),
    dict(
        variant="t_forward_from_current", section="13.8.1.2", rule="S13.8.1.2-002",
        facets=["T-forward-from-current"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(\"A\",T3,\"B\")')", observed="buf", expected="A B",
        input_mutation=("\"B\"", "\"C\""), descriptor="T3", descriptor_replacement="T4",
        descriptor_omission="T3,",
        reverse_sentinel=True,
        derivation="After A at position 1, T3 sets the next position to 3 relative to the left tab limit; p4 blanks position 2 before B."),
    dict(
        variant="tl_backward_two_positions", section="13.8.1.2", rule="S13.8.1.2-003",
        facets=["TL-backward"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(\"ABC\",TL2,\"Z\")')", observed="buf", expected="AZC",
        input_mutation=("\"Z\"", "\"Y\""), descriptor="TL2", descriptor_replacement="TR2",
        descriptor_omission="TL2,",
        derivation="ABC leaves the current position after 3; TL2 moves back to position 2 and Z replaces B."),
    dict(
        variant="tr_forward_two_positions", section="13.8.1.2", rule="S13.8.1.2-004",
        facets=["TR-forward"], kind="char", length=4,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(\"A\",TR2,\"B\")')", observed="buf", expected="A  B",
        input_mutation=("\"B\"", "\"C\""), descriptor="TR2", descriptor_omission="TR2,",
        derivation="After A, TR2 advances two positions so B is written at position 4 and positions 2-3 are blank-filled."),
    dict(
        variant="x_forward_two_positions", section="13.8.1.3", rule="S13.8.1.3-001",
        facets=["X-forward"], kind="char", length=4,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(\"A\",2X,\"B\")')", observed="buf", expected="A  B",
        input_mutation=("\"B\"", "\"C\""), descriptor="2X", descriptor_omission="2X,",
        derivation="2X has the same forward-positioning effect as TR2; B lands at position 4 after two skipped blanks."),
    dict(
        variant="slash_explicit_repeat", section="13.8.2", rule="S13.8.2-004",
        facets=["slash-explicit-repeat"], kind="array_chars", length=3,
        declarations=["character(len=1) :: rec(3)", "character(len=3) :: observed"], init="rec = '#'",
        write="write(rec,'(\"A\",2/,\"B\")')", observed="observed", expected="A B",
        after=["observed = rec(1) // rec(2) // rec(3)"], input_mutation=("\"B\"", "\"C\""),
        descriptor="2/", descriptor_omission="2/ ,".replace(" ", ""),
        derivation="The explicit repeat 2/ ends the A record, creates one blank internal record, then B is written to record 3."),
    dict(
        variant="colon_terminates_without_item", section="13.8.3", rule="S13.8.3-001",
        facets=["colon-terminates-without-item"], kind="char", length=1,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(I1,:,\",\",I1)') 4", observed="buf", expected="4",
        input_mutation=("4", "5"), descriptor=":",
        derivation="The first I1 writes 4; with no remaining effective item, colon terminates before the comma and second I1."),
    dict(
        variant="colon_no_effect_with_item", section="13.8.3", rule="S13.8.3-001",
        facets=["colon-no-effect-with-item"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(I1,:,\",\",I1)') 4,5", observed="buf", expected="4,5",
        input_mutation=("5", "6"), descriptor=":",
        derivation="Because a second effective item is present, colon has no effect and the comma plus second I1 are processed."),
    dict(
        variant="ss_suppresses_optional_plus", section="13.8.4", rule="S13.8.4-001",
        facets=["SS-sets-suppress"], kind="char", length=2,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(SS,I2)') 7", observed="buf", expected=" 7",
        input_mutation=("7", "8"), descriptor="SS", descriptor_replacement="SP",
        derivation="SS selects SUPPRESS sign mode, so I2 for positive 7 has a leading blank rather than an optional plus."),
    dict(
        variant="sp_prints_optional_plus", section="13.8.4", rule="S13.8.4-001",
        facets=["SP-sets-plus"], kind="char", length=2,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(SP,I2)') 7", observed="buf", expected="+7",
        input_mutation=("7", "8"), descriptor="SP", descriptor_replacement="SS",
        derivation="SP selects PLUS sign mode, so the optional sign position in I2 is a plus before 7."),
    dict(
        variant="bn_nonleading_blank_null", section="13.8.7", rule="S13.8.7-001",
        facets=["BN-sets-null"], kind="integer_input", expected=12,
        declarations=["character(len=3) :: input", "integer :: observed"], init="input = '1 2'; observed = -999",
        read="read(input,'(BN,I3)') observed", observed="observed",
        input_mutation=("'1 2'", "'2 3'"), descriptor="BN", descriptor_replacement="BZ",
        derivation="BN sets NULL blank interpretation: removing the nonleading blank from field '1 2' gives integer 12."),
    dict(
        variant="bz_nonleading_blank_zero", section="13.8.7", rule="S13.8.7-001",
        facets=["BZ-sets-zero"], kind="integer_input", expected=102,
        declarations=["character(len=3) :: input", "integer :: observed"], init="input = '1 2'; observed = -999",
        read="read(input,'(BZ,I3)') observed", observed="observed",
        input_mutation=("'1 2'", "'2 3'"), descriptor="BZ", descriptor_replacement="BN",
        derivation="BZ sets ZERO blank interpretation: the nonleading blank in field '1 2' is interpreted as zero, giving 102."),
    dict(
        variant="dc_outputs_comma_decimal", section="13.8.9", rule="S13.8.9-001",
        facets=["DC-sets-comma"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(DC,F3.1)') 1.5", observed="buf", expected="1,5",
        input_mutation=("1.5", "2.5"), descriptor="DC", descriptor_replacement="DP",
        derivation="1.5 is exact; DC selects COMMA decimal mode, so F3.1 writes comma as the decimal symbol."),
    dict(
        variant="dp_outputs_point_decimal", section="13.8.9", rule="S13.8.9-001",
        facets=["DP-sets-point"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(DP,F3.1)') 1.5", observed="buf", expected="1.5",
        input_mutation=("1.5", "2.5"), descriptor="DP", descriptor_replacement="DC",
        derivation="1.5 is exact; DP selects POINT decimal mode, so F3.1 writes point as the decimal symbol."),
    dict(
        variant="string_descriptor_includes_blank", section="13.9", rule="S13.9-002",
        facets=["string-includes-blanks"], kind="char", length=3,
        declarations=[], init="buf = repeat('#', len(buf))",
        write="write(buf,'(\"A B\")')", observed="buf", expected="A B",
        input_mutation=("\"A B\"", "\"AXB\""), descriptor="\"A B\"",
        derivation="The character string edit descriptor writes the three enclosed characters, including the embedded blank."),
]

VARIANTS = {case["variant"]: case for case in CASES}
FACETS_BY_RULE = {}
for case in CASES:
    FACETS_BY_RULE.setdefault(case["rule"], []).extend(case["facets"])
FACETS_BY_RULE = {rule: tuple(facets) for rule, facets in sorted(FACETS_BY_RULE.items())}
REMAINING_PENDING = {
    "S13.8.1.1-004": {"position-alone-no-transmission"},
    "S13.8.1.1-005": {"position-does-not-replace"},
    "S13.8.1.2-002": {"T-backward-from-current"},
    "S13.8.1.2-003": {"TL-clamps-left-tab-limit"},
    "S13.8.1.2-004": set(),
    "S13.8.1.3-001": set(),
    "S13.8.2-004": {"slash-default-repeat-one"},
    "S13.8.3-001": set(),
    "S13.8.4-001": {"S-sets-processor-defined", "sign-mode-persists-within-statement"},
    "S13.8.5-001": {
        "LZS-sets-suppress", "LZP-sets-print",
        "LZ-sets-processor-defined", "leading-zero-mode-persists-within-statement"},
    "S13.8.7-001": {"blank-mode-persists-within-statement"},
    "S13.8.9-001": {"decimal-mode-persists-within-statement"},
    "S13.9-002": {"string-output-positive-control", "string-writes-enclosed-characters", "doubled-delimiter-counts-one-character"},
}
WITHDRAWN_PENDING = {
    "S13.8.5-001": {
        "LZS-sets-suppress": "Source-derived pending plan: 13.8.5 makes LZS set LEADING_ZERO=SUPPRESS. In F, E, D, and G output editing, that mode controls optional leading zero characters in numeric output fields and SUPPRESS means the processor shall not produce a leading zero in any position that normally contains an optional leading zero; the descriptors have no effect during input. For example WRITE(buf,'(LZS,F3.1)') 0.5 would be expected to produce exactly ' .5'. No reference-validated oracle exists yet because neither available toolchain implements the LZS control edit descriptor in this conforming source; gfortran 16.1.0 with -std=f2023 and frozen LFortran 0.65.0-411 with --std=f23 both report a missing-comma parse diagnostic.",
        "LZP-sets-print": "Source-derived pending plan: 13.8.5 makes LZP set LEADING_ZERO=PRINT. In F, E, D, and G output editing, that mode controls optional leading zero characters in numeric output fields and PRINT means the processor shall produce a leading zero in any position that normally contains an optional leading zero; the descriptors have no effect during input. For example WRITE(buf,'(LZP,F3.1)') 0.5 would be expected to produce exactly '0.5'. No reference-validated oracle exists yet because neither available toolchain implements the LZP control edit descriptor in this conforming source; gfortran 16.1.0 with -std=f2023 and frozen LFortran 0.65.0-411 with --std=f23 both report a missing-comma parse diagnostic.",
    },
}
WITHDRAWN_ORACLE_RESET = {
    "S13.8.5-001": (
        "Plans are pending and source-derived. Positive plans use independent literal expected strings or scalar "
        "sentinels. Negative plans change one property from a conforming control and attribute the violation to "
        "this unit only."),
}
WITHDRAWN_LIMITATION_RESET = {
    "S13.8.5-001": (
        "Source accounting only. This packet creates no Fortran fixture, compiler invocation, execution evidence, "
        "evidence link, fixture approval, oracle approval, or coverage claim. Pending output plans use internal "
        "WRITE to a CHARACTER variable and name exact expected characters including blanks when the unit is "
        "internally testable. Unnumbered prose restrictions are not promoted to numbered-constraint diagnostics. "
        "Where the source makes a behavior processor dependent, or where a rule requires external stream/direct/"
        "sequential files or unregistered defined I/O, the pending plan is explicitly source-control or "
        "unassertable rather than a fixture oracle. PROCESSOR_DEFINED leading-zero mode is processor latitude; "
        "print and suppress choices are both permitted. The LZ descriptor facet records only the mandatory "
        "mode-setting effect; output latitude is accounted under p2.processor-defined-option."),
}

ORACLE_PREFIX = {rule: rule + " control edit descriptor runtime fixtures: " for rule in FACETS_BY_RULE}
LIMIT_PREFIX = {rule: rule + " control edit descriptor fixture boundaries: " for rule in FACETS_BY_RULE}

ORACLES = {
    rule: ORACLE_PREFIX[rule] + " ".join(
        f"{case['variant']} uses {case.get('write', case.get('read'))} and expects {repr(case['expected'])}: {case['derivation']}"
        for case in CASES if case["rule"] == rule)
    for rule in FACETS_BY_RULE
}
LIMITATIONS = {
    rule: LIMIT_PREFIX[rule] + (
        "Only the listed executable facets are represented. Every character-output case pre-fills the internal "
        "file variable or array with '#', asserts LEN where a character scalar is observed, and compares the whole "
        "field or assembled record with an equal-length literal so blank padding cannot hide a short oracle. "
        "The fixtures do not assert processor-defined sign or leading-zero modes, nondefault-character skipped "
        "positions, external sequential/stream/direct file positioning, diagnostics, or G0 processor-selected "
        "parameters. Mutation plans are generated with each parent source: wrong oracle, changed input value, "
        "control-descriptor removal where portable, and descriptor substitutions for T3/T4, TL2/TR2, SP/SS, "
        "DC/DP, and BN/BZ."
    ) for rule in FACETS_BY_RULE
}

COMPLETIONS = {case["variant"]: "CONTROL EDIT " + case["variant"].upper() + " OK\n" for case in CASES}


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown control edit descriptor variant")
    rule = VARIANTS[variant]["rule"]
    return rule.replace(".", "_").replace("-", "_") + "_valid__control_edit_descriptor_" + variant


class Program:
    def __init__(self, case):
        self.case = case
        self.variant = case["variant"]
        self.text = ""
        self.guards = []
        self.probes = []
        self.input_mutations = []
        self.descriptor_mutations = []
        self.omissions = []
        self.reverse_mutations = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def token(self, name):
        return f"CED:{self.variant}:{name}"

    def guard_equal(self, name, expression, expected, replacement, category="value", count=True):
        expected = str(expected)
        replacement = str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = self.token(name)
        self.add(prefix + expected + ") then\n")
        self.add(f"    write(*,'(a)') '{token}'\n    error stop\n  end if\n")
        if count:
            self.add("  checks=checks+1\n")
        guard = dict(id=name, guard_id=name, kind="guard", category=category, expression=expression,
                     expected=expected, replacement=replacement, span=[start, start + len(expected)],
                     line=self.text[:start].count("\n") + 1, counter="checks" if count else None,
                     mutation="guard-literal-expectation", failure_token=token,
                     failure_stdout=token + "\n", block_span=[block_start, len(self.text)])
        self.guards.append(guard)
        self.probes.append(dict(guard))
        if count:
            self.observations.append(guard)
        return guard

    def guard_char(self, name, expression, expected, category="value"):
        lit = fortran_char_literal(expected)
        replacement = fortran_char_literal(altered_string(expected))
        return self.guard_equal(name, expression, lit, replacement, category)

    def record_single_span_mutation(self, collection, name, expected, replacement, *, kind, category, mutation):
        start = self.text.index(expected)
        collection.append(dict(id=name, kind=kind, category=category, expected=expected, replacement=replacement,
                               span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
                               mutation=mutation, failure_stdout=""))

    def finish(self):
        total = self.guard_equal("check-total", "checks", len(self.observations), len(self.observations) + 1,
                                 "completion", count=False)
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        block = self.add(prefix + literal + "'\n")
        completion = dict(id="completion-output", guard_id="completion-output", kind="output",
                          category="completion", expected=literal, replacement=literal.replace(" OK", " BAD"),
                          span=[start, start + len(literal)], line=self.text[:start].count("\n") + 1,
                          mutation="completion-literal", failure_stdout="", block_span=block)
        self.guards.append(completion)
        self.probes.append(dict(completion))
        self.add(f"end program ced_{self.variant}\n")
        self.omissions.append(dict(id="omit-completion", guard_id=completion["id"], kind="output",
                                   category="omission", span=block, expected=self.text[block[0]:block[1]],
                                   replacement="", line=self.text[:block[0]].count("\n") + 1,
                                   mutation="completion-statement-omission", failure_stdout=""))
        for guard in self.observations:
            start, end = guard["block_span"]
            self.omissions.append(dict(id="omit-observation-" + guard["id"], guard_id=total["id"],
                                       kind="guard", category="omission", span=[start, end],
                                       expected=self.text[start:end], replacement="",
                                       line=self.text[:start].count("\n") + 1,
                                       mutation="whole-program-omission",
                                       failure_token=total["failure_token"], failure_stdout=total["failure_stdout"]))


def fortran_char_literal(value):
    return "'" + value.replace("'", "''") + "'"


def altered_string(value):
    if not value:
        return "X"
    chars = list(value)
    for i, ch in enumerate(chars):
        if ch == " ":
            chars[i] = "#"
            return "".join(chars)
    chars[-1] = "Z" if chars[-1] != "Z" else "Y"
    return "".join(chars)


def emit_program(case):
    p = Program(case)
    p.add(f"! rule: {case['rule']}\n")
    for facet in case["facets"]:
        p.add(f"! covers: {facet}\n")
    p.add("! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.\n")
    p.add(f"program ced_{case['variant']}\n  implicit none\n  integer :: checks\n")
    if case["kind"] in {"char"}:
        p.add(f"  character(len={case['length']}) :: buf\n")
    for decl in case.get("declarations", []):
        p.add("  " + decl + "\n")
    p.add("  checks=0\n")
    init_start = len(p.text)
    p.add("  " + case["init"] + "\n")
    action = case.get("write") or case.get("read")
    action_start = len(p.text)
    p.add("  " + action + "\n")
    action_end = len(p.text)
    for line in case.get("after", []):
        p.add("  " + line + "\n")
    if case["kind"] in {"char", "array_chars"}:
        if case["kind"] == "char":
            p.guard_equal("observed-length", f"len({case['observed']})", case["length"], case["length"] + 1, "length")
        p.guard_char("observed-characters", case["observed"], case["expected"])
    elif case["kind"] == "integer_input":
        p.guard_equal("observed-value", case["observed"], case["expected"], case["expected"] + 1, "value")
    else:
        raise ValueError("unknown case kind")
    p.finish()

    input_expected, input_replacement = case["input_mutation"]
    p.record_single_span_mutation(p.input_mutations, "input-value-change", input_expected, input_replacement,
                                  kind="input", category="input", mutation="input-value-change")
    descriptor = case.get("descriptor")
    if descriptor and case.get("descriptor_replacement"):
        start = p.text.index(descriptor, action_start, action_end)
        p.descriptor_mutations.append(dict(
            id="descriptor-" + descriptor.lower().replace("/", "slash") + "-to-" + case["descriptor_replacement"].lower(),
            kind="descriptor", category="descriptor-substitution", expected=descriptor,
            replacement=case["descriptor_replacement"], span=[start, start + len(descriptor)],
            line=p.text[:start].count("\n") + 1, mutation="control-descriptor-substitution",
            failure_stdout=""))
    if case.get("descriptor_omission"):
        expected = case["descriptor_omission"]
        start = p.text.index(expected, action_start, action_end)
        p.descriptor_mutations.append(dict(
            id="remove-control-descriptor", kind="descriptor", category="descriptor-omission",
            expected=expected, replacement="", span=[start, start + len(expected)],
            line=p.text[:start].count("\n") + 1, mutation="control-descriptor-omission",
            failure_stdout=""))
    if case.get("reverse_sentinel"):
        init_line = "  " + case["init"] + "\n"
        write_line = "  " + action + "\n"
        init_span = [init_start, init_start + len(init_line)]
        write_span = [action_start, action_start + len(write_line)]
        replacement = "  buf = " + fortran_char_literal(case["expected"]) + "\n"
        p.reverse_mutations.append(dict(
            id="reverse-sentinel-preload-and-remove-write", kind="reverse", category="sentinel-load-bearing",
            mutation="reverse-sentinel-and-feature-omission", intended="pass",
            replacements=[dict(span=init_span, expected=init_line, replacement=replacement),
                          dict(span=write_span, expected=write_line, replacement="")]))
    return finalize(p, case)


def finalize(p, case):
    raw = p.text.encode("ascii")
    for mutation in p.probes + p.input_mutations + p.descriptor_mutations + p.omissions:
        start, end = mutation["span"]
        if raw[start:end].decode("ascii") != mutation["expected"]:
            raise ValueError(f"mutation span {mutation['id']} lost complete-parent binding")
    for mutation in p.reverse_mutations:
        for repl in mutation["replacements"]:
            start, end = repl["span"]
            if raw[start:end].decode("ascii") != repl["expected"]:
                raise ValueError("reverse mutation lost complete-parent binding")
    return dict(id=identifier(case["variant"]), variant=case["variant"], rule=case["rule"],
                facets=case["facets"], evidence="effect", standard="f2023", phase="run",
                source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[case["variant"]],
                expected=case["expected"], derivation=case["derivation"], guards=p.guards,
                probes=p.probes, input_mutations=p.input_mutations,
                descriptor_mutations=p.descriptor_mutations, omissions=p.omissions,
                reverse_mutations=p.reverse_mutations, observations=p.observations,
                expected_counts=dict(checks=len(p.observations)))


def source_specs():
    return {identifier(case["variant"]): emit_program(case) for case in CASES}


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    if "replacements" in mutation:
        mutated = raw
        for repl in sorted(mutation["replacements"], key=lambda item: item["span"][0], reverse=True):
            start, end = repl["span"]
            if raw[start:end].decode("ascii") != repl["expected"]:
                raise ValueError("the reverse mutation span does not bind the complete parent")
            mutated = mutated[:start] + repl["replacement"].encode("ascii") + mutated[end:]
        return mutated
    return wrong_oracle_source(spec, mutation)


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("control_edit_descriptor_" + spec["variant"])
        manifest = dict(schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
                        evidence="effect", standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    section = catalogue["section"]
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, pending in WITHDRAWN_PENDING.items():
        if not rule.startswith("S" + section):
            continue
        owner = by_rule[rule]
        owner.setdefault("pending", {}).update(pending)
        owner["oracle"] = WITHDRAWN_ORACLE_RESET[rule]
        owner["oracle_limitation"] = WITHDRAWN_LIMITATION_RESET[rule]
    for rule, facets in FACETS_BY_RULE.items():
        if not rule.startswith("S" + section):
            continue
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("selected control edit descriptor facets changed for " + rule)
        for facet in facets:
            owner.get("pending", {}).pop(facet, None)
        if rule in REMAINING_PENDING and set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIX[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(owner.get("oracle_limitation", ""), LIMIT_PREFIX[rule], LIMITATIONS[rule])
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
    selected = [case for case in CASES if case["section"] == section]
    if selected:
        summary = (SUMMARY_BEGIN + "\n"
                   f"## Control edit descriptor runtime observations for {section}\n\n"
                   f"This fixture packet contributes {len(selected)} complete run/effect/f2023 case(s) for this "
                   "section. Internal output cases pre-fill their internal file variable or records with '#', assert "
                   "the full observed field, and include permanent oracle/input/descriptor mutation plans. "
                   "Unselected pending plans, processor latitude, external-file positioning, and diagnostics remain "
                   "outside this packet.\n" + SUMMARY_END)
        if SUMMARY_BEGIN in before or SUMMARY_END in before:
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
        path = root / rel
        catalogue = json.loads(path.read_text())
        updated = synced_catalogue(catalogue)
        updated_catalogues[section] = updated
        updated_views[section] = render_view(section, updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for section, rel in CATALOGUES.items():
            if json.loads((root / rel).read_text()) != updated_catalogues[section]:
                stale.append(rel)
            if (root / VIEWS[section]).read_text() != updated_views[section]:
                stale.append(VIEWS[section])
        if stale:
            raise ValueError("stale control-edit-descriptor fixture family: " + ", ".join(stale))
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    specs = generate(args.root, args.check, args.sync_catalogue)
    descriptor_substitutions = sum(
        1 for row in specs.values() for mutation in row["descriptor_mutations"]
        if mutation["category"] == "descriptor-substitution")
    descriptor_omissions = sum(
        1 for row in specs.values() for mutation in row["descriptor_mutations"]
        if mutation["category"] == "descriptor-omission")
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} control-edit-descriptor cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} oracle, "
          f"{sum(len(row['input_mutations']) for row in specs.values())} input, "
          f"{descriptor_substitutions} descriptor substitution, "
          f"{descriptor_omissions} descriptor omission, "
          f"{sum(len(row['reverse_mutations']) for row in specs.values())} reverse and "
          f"{sum(len(row['omissions']) for row in specs.values())} omission plans.")


if __name__ == "__main__":
    main()
