#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 input/output rounding modes."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ROUND_SECTION = "13.7.2.3.8"
ROUND_CATALOGUE = "doc/catalogues/input_output_rounding_mode_13_7_2_3_8.json"
ROUND_VIEW = "doc/fortran_2023_13_7_2_3_8.md"
EDIT_SECTION = "13.8.8"
EDIT_CATALOGUE = "doc/catalogues/ru_rd_rz_rn_rc_and_rp_editing_13_8_8.json"
EDIT_VIEW = "doc/fortran_2023_13_8_8.md"
SUMMARY_BEGIN = "<!-- BEGIN ROUNDING MODE FIXTURES -->"
SUMMARY_END = "<!-- END ROUNDING MODE FIXTURES -->"

CASES = [
    dict(variant="open_specifier_up", section=ROUND_SECTION, catalogue=ROUND_CATALOGUE,
         rule="S13.7.2.3.8-001", facets=("round-mode-open-specifier",),
         title="OPEN ROUND specifier sets connection rounding mode", builder="open_specifier_up"),
    dict(variant="data_transfer_specifier_down", section=ROUND_SECTION, catalogue=ROUND_CATALOGUE,
         rule="S13.7.2.3.8-001", facets=("round-mode-data-transfer-specifier",),
         title="Data-transfer ROUND specifier temporarily sets rounding mode", builder="data_transfer_specifier_down"),
    dict(variant="edit_descriptor_specifier_zero", section=ROUND_SECTION, catalogue=ROUND_CATALOGUE,
         rule="S13.7.2.3.8-001", facets=("round-mode-edit-descriptor",),
         title="Round edit descriptor sets rounding mode", builder="edit_descriptor_specifier_zero"),
    dict(variant="decimal_internal_directions", section=ROUND_SECTION, catalogue=ROUND_CATALOGUE,
         rule="S13.7.2.3.8-002",
         facets=("decimal-value-defined", "internal-value-defined",
                 "formatted-output-conversion-direction", "formatted-input-conversion-direction"),
         title="Decimal and internal value conversion directions", builder="decimal_internal_directions"),
    dict(variant="required_rounding_modes", section=ROUND_SECTION, catalogue=ROUND_CATALOGUE,
         rule="S13.7.2.3.8-003",
         facets=("round-up-conversion", "round-down-conversion", "round-zero-conversion",
                 "round-nearest-conversion", "round-compatible-conversion"),
         title="Required non-default rounding mode conversions", builder="required_rounding_modes"),
    dict(variant="edit_descriptors_required_modes", section=EDIT_SECTION, catalogue=EDIT_CATALOGUE,
         rule="S13.8.8-001",
         facets=("RU-sets-up", "RD-sets-down", "RZ-sets-zero", "RN-sets-nearest",
                 "RC-sets-compatible"),
         title="RU, RD, RZ, RN, and RC descriptor effects", builder="edit_descriptors_required_modes"),
]

CASE_BY_VARIANT = {case["variant"]: case for case in CASES}
SELECTED_FACETS_BY_CATALOGUE_RULE = {}
for case in CASES:
    SELECTED_FACETS_BY_CATALOGUE_RULE.setdefault((case["catalogue"], case["rule"]), set()).update(case["facets"])

ORACLE_PARAGRAPHS = {
    (ROUND_CATALOGUE, "S13.7.2.3.8-001"): (
        "S13.7.2.3.8-001 rounding-mode specifier runtime fixtures: three complete programs observe the "
        "three sources named by p1 independently. An external formatted connection opened with ROUND='UP' "
        "writes exact -1.25 using (SS,F5.1) as ' -1.2'. An internal-file data transfer ROUND='DOWN' "
        "writes exact 1.25 as '  1.2'. An RZ edit descriptor in another internal WRITE writes exact 1.25 "
        "as '  1.2'. OPEN UP->DOWN, data-transfer DOWN->UP, and descriptor RZ->RU substitutions all "
        "change the selected field; the data-transfer fixture currently exposes a frozen-LFortran defect "
        "while the reference passes."),
    (ROUND_CATALOGUE, "S13.7.2.3.8-002"): (
        "S13.7.2.3.8-002 decimal/internal direction runtime fixture: one complete internal-file program reads "
        "the character string '1.25' with F4.2 into a real initialized and pre-READ-guarded at -99.0, then "
        "requires the exactly representable internal value 1.25. The same program writes the exactly "
        "representable internal value 1.125 with (SS,F5.3) and requires the exact decimal field '1.125'. "
        "This uses p2's decimal-value/internal-value distinction without relying on any inexact source token. "
        "Field, descriptor, oracle, and sentinel-initialization substitutions are permanently load-bearing."),
    (ROUND_CATALOGUE, "S13.7.2.3.8-003"): (
        "S13.7.2.3.8-003 required-mode runtime fixture: one complete program writes exact binary values with "
        "explicit round edit descriptors and asserts only p3-required results. (SS,RU,F5.1) on 1.25 gives "
        "'  1.3'; (SS,RD,F5.1) on 1.25 gives '  1.2'; (SS,RZ,F5.1) on -1.25 gives ' -1.2'; "
        "(SS,RN,F5.1) on non-halfway 1.125 gives '  1.1'; and (SS,RC,F5.1) on halfway -1.25 gives "
        "' -1.3' by the specified away-from-zero compatible tie rule. NEAREST halfway, PROCESSOR_DEFINED, "
        "and conditional IEEE tie-even facets remain pending because p3/p4 do not give an unconditional exact "
        "string oracle. RU/RD/RZ/RN/RC mode substitutions all differ on the selected exact value."),
    (EDIT_CATALOGUE, "S13.8.8-001"): (
        "S13.8.8-001 round-edit-descriptor runtime fixture: one complete program uses RU, RD, RZ, RN, and RC "
        "with F editing of exact real values, proving that each descriptor temporarily sets the corresponding "
        "13.7.2.3.8 mode for a selected real formatted output conversion. The asserted fields are '  1.3' "
        "for RU on 1.25, '  1.2' for RD on 1.25, ' -1.2' for RZ on -1.25, '  1.1' for RN on non-halfway "
        "1.125, and ' -1.3' for RC on halfway -1.25. RP and the real/complex-only selected-descriptor "
        "facet remain pending; no unique processor-defined RP field is asserted."),
}

LIMIT_PARAGRAPHS = {
    ROUND_CATALOGUE: (
        "Rounding-mode fixture boundaries: this packet discharges the selected 12 facets removed from pending "
        "above. All finite output uses SS for positive values, nonzero integer parts, and exact binary values; "
        "no optional leading zero is asserted. UP/DOWN/ZERO/RN/RC assertions use exact 1.25, -1.25, and 1.125 "
        "so the discarded decimal part is known. RN is asserted only for a non-halfway case; the p3 halfway "
        "choice and PROCESSOR_DEFINED default remain processor dependent. The p4 IEEE-conversion tie-even facet "
        "is not claimed because this packet has no non-circular portable support gate for IEEE conversion "
        "rounding."),
    EDIT_CATALOGUE: (
        "Rounding-edit fixture boundaries: this packet discharges only RU, RD, RZ, RN, and RC descriptor effects "
        "for selected F editing of exactly representable real values. RP and the real/complex-only selected-"
        "descriptor facet remain pending. Positive numeric output uses SS, optional leading-zero positions are "
        "not asserted, and every descriptor substitution changes the chosen exact value's required field."),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    case = CASE_BY_VARIANT[variant]
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__rounding_mode_" + variant


def program_name(variant):
    return "rm_" + variant


class Program:
    def __init__(self, case):
        self.case = case
        self.variant = case["variant"]
        self.text = ""
        self.probes = []
        self.observations = []
        self.declarations = []
        self.body = []

    def render_prefix(self):
        covers = "".join(f"! covers: {facet}\n" for facet in self.case["facets"])
        return (f"program {program_name(self.variant)}\n"
                "  implicit none\n"
                f"! rule: {self.case['rule']}\n" + covers +
                "  integer :: checks\n" +
                "\n".join(self.declarations) + ("\n" if self.declarations else "") +
                "  checks = 0\n")

    def render_suffix(self, total):
        completion = self.completion_literal()
        return (
            f"  if (checks /= {total}) then\n"
            f"    write(*,'(a)') 'RM:{self.variant}:check-total'\n"
            "    error stop 1\n"
            "  end if\n"
            f"  write(*,'(a)') '{completion}'\n"
            "contains\n"
            "  subroutine expect_text(observed, expected, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'RM:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'RM:text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_text\n"
            "  subroutine expect_real(observed, expected, label)\n"
            "    real, intent(in) :: observed, expected\n"
            "    character(len=*), intent(in) :: label\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'RM:real', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_real\n"
            f"end program {program_name(self.variant)}\n")

    def completion_literal(self):
        return "ROUNDING MODE " + self.variant.upper().replace("_", " ") + " OK"

    def source(self):
        prefix = self.render_prefix()
        body = "".join(self.body)
        total = len(self.observations)
        suffix_start = len(prefix) + len(body)
        suffix = self.render_suffix(total)
        self.text = prefix + body + suffix
        needle = f"checks /= {total}"
        start = suffix_start + suffix.index(needle)
        self.probes.append(dict(
            id="reverse-check-total", kind="reverse", category="sentinel", mutation="reverse-total-sentinel",
            span=[start + len("checks "), start + len("checks ") + len("/=")], expected="/=", replacement="==",
            failure_stdout=f"RM:{self.variant}:check-total\n"))
        literal = self.completion_literal()
        marker = f"write(*,'(a)') '{literal}'"
        start = suffix_start + suffix.index(marker) + marker.index(literal)
        self.probes.append(dict(
            id="oracle-completion", kind="output", category="oracle", mutation="completion-literal",
            span=[start, start + len(literal)], expected=literal, replacement=literal.replace(" OK", " BAD"),
            failure_stdout=""))
        raw = self.text.encode("ascii")
        for probe in self.probes:
            lo, hi = probe["span"]
            if raw[lo:hi].decode("ascii") != probe["expected"]:
                raise ValueError(f"probe span lost complete-parent binding: {self.variant}:{probe['id']}")
        return self.text

    def declare(self, line):
        self.declarations.append("  " + line)

    def add(self, text):
        self.body.append(text)

    def current_length(self):
        return len(self.render_prefix()) + sum(len(part) for part in self.body)

    def mutate_span_in_next(self, line, expected, replacement, probe_id, mutation, category,
                            failure_stdout=None, discriminant=None):
        start = self.current_length() + line.index(expected)
        probe = dict(id=probe_id, kind="source", category=category, mutation=mutation,
                     span=[start, start + len(expected)], expected=expected, replacement=replacement,
                     failure_stdout=failure_stdout if failure_stdout is not None else f"RM:{self.variant}")
        if discriminant:
            probe["discriminant"] = discriminant
        self.probes.append(probe)

    def assign_real(self, name, value, replacement):
        line = f"  {name} = {value}\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-value", "input")
        self.add(line)

    def assign_character(self, name, value, replacement):
        line = f"  {name} = '{value}'\n"
        self.mutate_span_in_next(line, value, replacement, f"input-{name}", "input-field", "input")
        self.add(line)

    def init_real(self, name, value, expected_after_read, label):
        line = f"  {name} = {value}\n"
        start = self.current_length()
        for suffix, replacement, note in (
            ("remove", "", f"{name}: removing the sentinel leaves the pre-READ guard unestablished"),
            ("expected", f"  {name} = {expected_after_read}\n",
             f"{name}: initializing to the expected READ result would make a missing READ vacuous"),
            ("zero", f"  {name} = 0.0\n",
             f"{name}: zero is distinguishable from the sentinel and expected result"),
        ):
            self.probes.append(dict(
                id=f"sentinel-{label}-{suffix}", kind="source", category="sentinel-init",
                mutation="sentinel-initialization-" + suffix,
                span=[start, start + len(line)], expected=line, replacement=replacement,
                failure_stdout=f"RM:real {label}\n", discriminant=note))
        self.add(line)
        self.expect_real(name, value, "0.0", label)


    def init_character(self, name, value, expected_after_read, label):
        line = f"  {name} = '{value}'\n"
        start = self.current_length()
        blank = " " * len(value)
        for suffix, replacement, note in (
            ("remove", "", f"{name}: removing the sentinel leaves the pre-READ guard unestablished"),
            ("expected", f"  {name} = '{expected_after_read}'\n",
             f"{name}: initializing to the expected READ field would make a missing READ vacuous"),
            ("blank", f"  {name} = '{blank}'\n",
             f"{name}: blanks are distinguishable from the sentinel and expected READ field"),
        ):
            self.probes.append(dict(
                id=f"sentinel-{label}-{suffix}", kind="source", category="sentinel-init",
                mutation="sentinel-initialization-" + suffix,
                span=[start, start + len(line)], expected=line, replacement=replacement,
                failure_stdout=f"RM:text {label}\n", discriminant=note))
        self.add(line)
        self.expect_text(name, value, label)

    def set_buffer(self, name, sentinel):
        self.add(f"  {name} = '{sentinel}'\n")

    def open_stmt(self, unit, filename, round_mode, *, mode_mutations=()):
        line = (f"  open(newunit={unit}, file='{filename}', status='replace', action='readwrite', "
                f"form='formatted', round='{round_mode}')\n")
        for mutation in mode_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "round-mode-substitution", "round-mode",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def write_stmt(self, target, fmt, values, *, round_mode=None, mode_mutations=(), descriptor_mutations=()):
        suffix = f",round='{round_mode}'" if round_mode else ""
        line = f"  write({target},'({fmt})'{suffix}) {values}\n"
        for mutation in mode_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "round-mode-substitution", "round-mode",
                                     discriminant=mutation["discriminant"])
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def read_stmt(self, source, fmt, out_var, *, descriptor_mutations=()):
        line = f"  read({source},'({fmt})') {out_var}\n"
        for mutation in descriptor_mutations:
            self.mutate_span_in_next(line, mutation["from"], mutation["to"], mutation["id"],
                                     "descriptor-substitution", "descriptor",
                                     discriminant=mutation["discriminant"])
        self.add(line)

    def expect_text(self, buf, expected, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_text({buf}, '{expected}', '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "text-oracle", "oracle",
                                 f"RM:text {label}\n")
        self.add(line)
        self.observations.append(label)

    def expect_real(self, var, expected, replacement, label):
        line = f"  call expect_real({var}, {expected}, '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "real-oracle", "oracle",
                                 f"RM:real {label}\n")
        self.add(line)
        self.observations.append(label)


def corrupt_text(value):
    chars = list(value)
    for index in range(len(chars) - 1, -1, -1):
        if chars[index] != " ":
            chars[index] = "X" if chars[index] != "X" else "Y"
            return "".join(chars)
    chars[0] = "X"
    return "".join(chars)


def rsub(old, new, tag, discriminant):
    return {"from": old, "to": new, "id": "round-" + tag, "discriminant": discriminant}


def dsub(old, new, tag, discriminant):
    return {"from": old, "to": new, "id": "descriptor-" + tag, "discriminant": discriminant}


def make_program(case):
    p = Program(case)
    getattr(sys.modules[__name__], "build_" + case["builder"])(p)
    return p, p.source()


def build_open_specifier_up(p):
    p.declare("integer :: unit")
    p.declare("real :: open_value")
    p.declare("character(len=5) :: open_field")
    p.assign_real("open_value", "-1.25", "-1.75")
    p.open_stmt("unit", "rounding_mode_open_specifier_up.dat", "UP", mode_mutations=(
        rsub("UP", "DOWN", "open-up-to-down", "-1.25: OPEN ROUND='UP' gives ' -1.2', DOWN gives ' -1.3'"),
    ))
    p.write_stmt("unit", "SS,F5.1", "open_value")
    p.init_character("open_field", "#####", " -1.2", "sentinel-open-field")
    p.add("  rewind(unit)\n")
    p.add("  read(unit,'(a)') open_field\n")
    p.add("  close(unit, status='delete')\n")
    p.expect_text("open_field", " -1.2", "open-up")


def build_data_transfer_specifier_down(p):
    p.declare("real :: transfer_value")
    p.declare("character(len=5) :: transfer_field")
    p.assign_real("transfer_value", "1.25", "1.75")
    p.set_buffer("transfer_field", "#####")
    p.write_stmt("transfer_field", "SS,F5.1", "transfer_value", round_mode="DOWN", mode_mutations=(
        rsub("DOWN", "UP", "transfer-down-to-up", "1.25: data-transfer ROUND='DOWN' gives '  1.2', UP gives '  1.3'"),
    ))
    p.expect_text("transfer_field", "  1.2", "transfer-down")


def build_edit_descriptor_specifier_zero(p):
    p.declare("real :: descriptor_value")
    p.declare("character(len=5) :: descriptor_field")
    p.assign_real("descriptor_value", "1.25", "1.75")
    p.set_buffer("descriptor_field", "#####")
    p.write_stmt("descriptor_field", "SS,RZ,F5.1", "descriptor_value", descriptor_mutations=(
        dsub("RZ", "RU", "rz-to-ru", "1.25: RZ gives '  1.2', RU gives '  1.3'"),
    ))
    p.expect_text("descriptor_field", "  1.2", "descriptor-rz")


def build_decimal_internal_directions(p):
    p.declare("character(len=4) :: input_field")
    p.declare("character(len=5) :: output_field")
    p.declare("real :: input_value, output_value")
    p.assign_character("input_field", "1.25", "1.50")
    p.init_real("input_value", "-99.0", "1.25", "sentinel-input-value")
    p.read_stmt("input_field", "F4.2", "input_value", descriptor_mutations=(
        dsub("F4.2", "F3.2", "f4_2-to-f3_2", "'1.25': F4.2 reads 1.25, F3.2 reads the shorter field '1.2'"),
    ))
    p.expect_real("input_value", "1.25", "1.5", "input-decimal-to-internal")
    p.assign_real("output_value", "1.125", "1.625")
    p.set_buffer("output_field", "#####")
    p.write_stmt("output_field", "SS,F5.3", "output_value", descriptor_mutations=(
        dsub("F5.3", "F5.1", "f5_3-to-f5_1", "1.125: F5.3 writes '1.125', F5.1 writes '  1.1'"),
    ))
    p.expect_text("output_field", "1.125", "output-internal-to-decimal")


def add_required_mode_sequence(p):
    p.declare("real :: tie_positive, tie_negative, nearest_value")
    p.declare("character(len=5) :: up_field, down_field, zero_field, nearest_field, compatible_field")
    p.assign_real("tie_positive", "1.25", "1.75")
    p.assign_real("tie_negative", "-1.25", "-1.75")
    p.assign_real("nearest_value", "1.125", "1.625")
    p.set_buffer("up_field", "#####")
    p.write_stmt("up_field", "SS,RU,F5.1", "tie_positive", descriptor_mutations=(
        dsub("RU", "RD", "ru-to-rd", "1.25: RU gives '  1.3', RD gives '  1.2'"),
    ))
    p.expect_text("up_field", "  1.3", "round-up")
    p.set_buffer("down_field", "#####")
    p.write_stmt("down_field", "SS,RD,F5.1", "tie_positive", descriptor_mutations=(
        dsub("RD", "RU", "rd-to-ru", "1.25: RD gives '  1.2', RU gives '  1.3'"),
    ))
    p.expect_text("down_field", "  1.2", "round-down")
    p.set_buffer("zero_field", "#####")
    p.write_stmt("zero_field", "SS,RZ,F5.1", "tie_negative", descriptor_mutations=(
        dsub("RZ", "RD", "rz-to-rd", "-1.25: RZ gives ' -1.2', RD gives ' -1.3'"),
    ))
    p.expect_text("zero_field", " -1.2", "round-zero")
    p.set_buffer("nearest_field", "#####")
    p.write_stmt("nearest_field", "SS,RN,F5.1", "nearest_value", descriptor_mutations=(
        dsub("RN", "RU", "rn-to-ru", "1.125: RN gives nearest '  1.1', RU gives '  1.2'"),
    ))
    p.expect_text("nearest_field", "  1.1", "round-nearest")
    p.set_buffer("compatible_field", "#####")
    p.write_stmt("compatible_field", "SS,RC,F5.1", "tie_negative", descriptor_mutations=(
        dsub("RC", "RU", "rc-to-ru", "-1.25: RC tie away from zero gives ' -1.3', RU gives ' -1.2'"),
    ))
    p.expect_text("compatible_field", " -1.3", "round-compatible")


def build_required_rounding_modes(p):
    add_required_mode_sequence(p)


def build_edit_descriptors_required_modes(p):
    add_required_mode_sequence(p)


def source_specs():
    specs = {}
    for case in CASES:
        program, source = make_program(case)
        raw = source.encode("ascii")
        name = identifier(case["variant"])
        specs[name] = dict(
            id=name, variant=case["variant"], rule=case["rule"], facets=list(case["facets"]),
            profiles=list(case.get("profiles", ())), section=case["section"], title=case["title"],
            source=source, source_sha256=sha(raw), probes=copy.deepcopy(program.probes),
            observations=list(program.observations), completion=program.completion_literal() + "\n")
    return specs


def wrong_oracle_source(spec, probe):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = probe["span"]
    if raw[start:end].decode("ascii") != probe["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + probe["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, spec in specs.items():
        directory = "tests/fixtures/rounding_mode_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        if spec["profiles"]:
            manifest["profiles"] = spec["profiles"]
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate rounding-mode fixture paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue, catalogue_path):
    result = copy.deepcopy(catalogue)
    selected_by_rule = {rule: facets for (cat, rule), facets in SELECTED_FACETS_BY_CATALOGUE_RULE.items()
                        if cat == catalogue_path}
    for rule, facets in selected_by_rule.items():
        rows = [row for row in result["requirements"] if row["id"] == rule]
        if len(rows) != 1:
            raise ValueError(f"selected requirement {rule} changed")
        row = rows[0]
        if not facets <= set(row["facets"]):
            raise ValueError(f"selected facets for {rule} changed")
        for facet in sorted(facets):
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), rule + " ",
                                         ORACLE_PARAGRAPHS[(catalogue_path, rule)])
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""),
                                                   "Rounding-", LIMIT_PARAGRAPHS[catalogue_path])
    return result


def summary_text(section):
    if section == ROUND_SECTION:
        detail = ("This packet adds executable fixtures for 12 selected 13.7.2.3.8 facets: OPEN, data-transfer, "
                  "and edit-descriptor mode sources; decimal/internal conversion direction; and the UP, DOWN, "
                  "ZERO, NEAREST non-halfway, and COMPATIBLE required rounding modes. It deliberately leaves "
                  "NEAREST tie latitude, PROCESSOR_DEFINED latitude, and conditional IEEE conversion tie-even "
                  "pending.")
    else:
        detail = ("This packet adds executable fixtures for five selected 13.8.8 facets: RU, RD, RZ, RN, and RC "
                  "descriptor effects for F editing of exact real values. RP and the real/complex-only selected-"
                  "descriptor facet remain pending.")
    return (SUMMARY_BEGIN + "\n"
            "## Executable input/output rounding mode fixtures\n\n" + detail + " The fixtures use SS for positive "
            "numeric output, avoid optional leading-zero oracles, initialize character buffers with '#', guard-check "
            "the one input target sentinel before READ, and include permanent mode/descriptor, input, oracle, and "
            "sentinel mutation probes.\n" + SUMMARY_END)


def render_view(catalogue, section, view_path, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / view_path
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError(f"generated boundary changed for {section}")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError(f"summary boundary changed for {section}")
        leading, rest_summary = before.split(SUMMARY_BEGIN)
        _, trailing = rest_summary.split(SUMMARY_END)
        before = leading.rstrip() + "\n\n" + trailing.lstrip()
    return before.rstrip() + "\n\n" + summary_text(section) + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogues = {
        ROUND_CATALOGUE: (ROUND_SECTION, ROUND_VIEW),
        EDIT_CATALOGUE: (EDIT_SECTION, EDIT_VIEW),
    }
    updated = {}
    views = {}
    for catalogue_path, (section, view_path) in catalogues.items():
        catalogue = json.loads((root / catalogue_path).read_text())
        updated[catalogue_path] = synced_catalogue(catalogue, catalogue_path)
        views[view_path] = render_view(updated[catalogue_path], section, view_path, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for catalogue_path, catalogue in updated.items():
            if json.loads((root / catalogue_path).read_text()) != catalogue:
                stale.append(catalogue_path)
        for view_path, text in views.items():
            if (root / view_path).read_text() != text:
                stale.append(view_path)
        if stale:
            raise ValueError("stale rounding mode fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for catalogue_path, catalogue in updated.items():
                (root / catalogue_path).write_text(json.dumps(catalogue, indent=2) + "\n")
            for view_path, text in views.items():
                (root / view_path).write_text(text)
    return specs


def compiler_command(compiler, std, source, output):
    command = [str(compiler)]
    if std:
        command.append(std)
    command += [str(source), "-o", str(output)]
    return command


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compile_run = subprocess.run(compiler_command(compiler, std, source, exe), text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cwd=work_dir)
    if compile_run.returncode != 0:
        return dict(status="compile-fail", stdout=compile_run.stdout, stderr=compile_run.stderr,
                    returncode=compile_run.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         timeout=60, cwd=work_dir)
    passed = (run.returncode == 0 and run.stdout == expected_stdout and run.stderr == "")
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr,
                returncode=run.returncode)


def mutation_check(root, compiler, std, keep_work=False):
    root = Path(root)
    specs = source_specs()
    work_dir = root / ".rounding_mode_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    try:
        report = []
        for spec in specs.values():
            parent = run_one_source(compiler, std, work_dir, spec["source"], spec["completion"],
                                    spec["variant"] + "_parent")
            parent_ok = parent["status"] == "pass"
            for index, probe in enumerate(spec["probes"]):
                mutant_source = wrong_oracle_source(spec, probe).decode("ascii")
                observed = run_one_source(compiler, std, work_dir, mutant_source, spec["completion"],
                                          f"{spec['variant']}_mut_{index:03d}")
                failed = not (observed["status"] == "pass")
                report.append(dict(variant=spec["variant"], probe=probe["id"], mutation=probe["mutation"],
                                   category=probe["category"], expected=probe["expected"],
                                   replacement=probe["replacement"],
                                   discriminant=probe.get("discriminant", ""), parent_ok=parent_ok,
                                   failed=failed, status=observed["status"], stdout=observed["stdout"],
                                   stderr=observed["stderr"], returncode=observed["returncode"]))
        bad = [row for row in report if not row["parent_ok"] or not row["failed"]]
        if bad:
            raise RuntimeError(json.dumps(bad[:5], indent=2))
        return report
    finally:
        if not keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)


def counts(specs):
    facets = {facet for spec in specs.values() for facet in spec["facets"]}
    mutations = sum(len(spec["probes"]) for spec in specs.values())
    descriptor = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["mutation"] == "descriptor-substitution")
    round_modes = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["mutation"] == "round-mode-substitution")
    inputs = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "input")
    sentinels = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "sentinel-init")
    return len(specs), len(facets), mutations, descriptor, round_modes, inputs, sentinels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogues", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogues:
        parser.error("--check and --sync-catalogues are separate operations")
    if args.mutation_check:
        if args.check or args.sync_catalogues:
            parser.error("--mutation-check is separate from generation/checking")
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        total = len(report)
        descriptor = sum(row["mutation"] == "descriptor-substitution" for row in report)
        round_modes = sum(row["mutation"] == "round-mode-substitution" for row in report)
        sentinels = sum(row["category"] == "sentinel-init" for row in report)
        print(f"Mutation-checked {total} rounding-mode mutations: {descriptor} descriptor, "
              f"{round_modes} round-mode, {sentinels} sentinel-init; all failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count, descriptor_count, round_count, input_count, sentinel_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} rounding mode cases, "
          f"{facet_count} facets and {mutation_count} mutations "
          f"({descriptor_count} descriptor, {round_count} round-mode, {input_count} input, "
          f"{sentinel_count} sentinel-init).")


if __name__ == "__main__":
    main()
