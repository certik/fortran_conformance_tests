#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 EN and ES real editing."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EN_SECTION = "13.7.2.3.4"
ES_SECTION = "13.7.2.3.5"
EN_CATALOGUE = "doc/catalogues/en_editing_13_7_2_3_4.json"
ES_CATALOGUE = "doc/catalogues/es_editing_13_7_2_3_5.json"
EN_VIEW = "doc/fortran_2023_13_7_2_3_4.md"
ES_VIEW = "doc/fortran_2023_13_7_2_3_5.md"
SUMMARY_BEGIN = "<!-- BEGIN EN ES EDITING FIXTURES -->"
SUMMARY_END = "<!-- END EN ES EDITING FIXTURES -->"

CASES = [
    dict(variant="en_engineering_notation", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-001", facets=("EN-engineering-notation",),
         title="EN engineering notation for one half", descriptor="EN12.3E2",
         value="0.5", replacement_value="2.5", expected=" 500.000E-03",
         derivation="0.5 = 500.000 x 10**(-3); EN requires exponent divisible by three and 1<=500<1000."),
    dict(variant="en_exponent_divisible_by_three", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-001", facets=("EN-exponent-divisible-by-three",),
         title="EN exponent is a multiple of three", descriptor="EN12.3E2",
         value="0.5", replacement_value="2.5", expected=" 500.000E-03",
         derivation="0.5 is represented with decimal exponent -3, the EN exponent divisible by three."),
    dict(variant="en_significand_range", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-001", facets=("EN-significand-range",),
         title="EN significand stays in engineering range", descriptor="EN12.3E2",
         value="0.125", replacement_value="0.500", expected=" 125.000E-03",
         derivation="0.125 = 125.000 x 10**(-3); 125 is within the required 1<=yyy<1000 interval."),
    dict(variant="en_scale_factor_no_effect", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-001", facets=("EN-scale-factor-no-effect",),
         title="EN output ignores an active scale factor", descriptor="EN12.3E2",
         value="0.5", replacement_value="2.5", expected=" 500.000E-03", scale_prefix="1P",
         derivation="EN output ignores the 1P scale factor, so 0.5 remains 500.000 x 10**(-3)."),
    dict(variant="en_field_width", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-002", facets=("EN-field-width",),
         title="EN occupies the requested field width", descriptor="EN12.3E2",
         value="100.0", replacement_value="0.125", expected=" 100.000E+00",
         derivation="100.0 = 100.000 x 10**0; EN12.3E2 occupies exactly twelve positions."),
    dict(variant="en_fractional_digits", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-002", facets=("EN-fractional-digits",),
         title="EN fractional part has d digits", descriptor="EN11.2E2",
         value="100.0", replacement_value="0.125", expected=" 100.00E+00",
         derivation="With d=2, 100.0 in EN form has exactly two following digits: 100.00E+00."),
    dict(variant="en_exponent_digit_count", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-002", facets=("EN-exponent-digit-count",),
         title="EN explicit Ee fixes exponent digit count", descriptor="EN12.3E2",
         value="0.125", replacement_value="0.500", expected=" 125.000E-03",
         derivation="The exponent is -3 and explicit E2 requires exactly two exponent digits, hence E-03."),
    dict(variant="en_output_significand_digits", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-005", facets=("EN-output-significand-digits",),
         title="EN finite output has one to three leading significand digits", descriptor="EN12.3E2",
         value="0.5", replacement_value="2.5", expected=" 500.000E-03",
         derivation="The EN leading significand digits for 0.5 are the three digits 500 before the decimal symbol."),
    dict(variant="en_output_decimal_symbol", section=EN_SECTION, catalogue=EN_CATALOGUE,
         rule="S13.7.2.3.4-005", facets=("EN-output-decimal-symbol",),
         title="EN finite output contains the decimal symbol", descriptor="EN12.3E2",
         value="0.5", replacement_value="2.5", expected=" 500.000E-03",
         derivation="POINT-mode formatted output places the decimal symbol after the EN significand digits 500."),
    dict(variant="es_scientific_notation", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-001", facets=("ES-scientific-notation",),
         title="ES scientific notation for one half", descriptor="ES12.3E2",
         value="0.5", replacement_value="2.5", expected="   5.000E-01",
         derivation="0.5 = 5.000 x 10**(-1); ES requires a one-digit significand in [1,10)."),
    dict(variant="es_significand_range", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-001", facets=("ES-significand-range",),
         title="ES significand stays in scientific range", descriptor="ES12.3E2",
         value="0.125", replacement_value="0.500", expected="   1.250E-01",
         derivation="0.125 = 1.250 x 10**(-1); 1.250 is within the required 1<=significand<10 interval."),
    dict(variant="es_scale_factor_no_effect", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-001", facets=("ES-scale-factor-no-effect",),
         title="ES output ignores an active scale factor", descriptor="ES12.3E2",
         value="0.5", replacement_value="2.5", expected="   5.000E-01", scale_prefix="2P",
         derivation="ES output ignores the 2P scale factor, so 0.5 remains 5.000 x 10**(-1)."),
    dict(variant="es_field_width", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-002", facets=("ES-field-width",),
         title="ES occupies the requested field width", descriptor="ES12.3E2",
         value="100.0", replacement_value="0.125", expected="   1.000E+02",
         derivation="100.0 = 1.000 x 10**2; ES12.3E2 occupies exactly twelve positions."),
    dict(variant="es_fractional_digits", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-002", facets=("ES-fractional-digits",),
         title="ES fractional part has d digits", descriptor="ES11.2E2",
         value="100.0", replacement_value="0.125", expected="   1.00E+02",
         derivation="With d=2, 100.0 in ES form has exactly two following digits: 1.00E+02."),
    dict(variant="es_exponent_digit_count", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-002", facets=("ES-exponent-digit-count",),
         title="ES explicit Ee fixes exponent digit count", descriptor="ES12.3E2",
         value="0.125", replacement_value="0.500", expected="   1.250E-01",
         derivation="The exponent is -1 and explicit E2 requires exactly two exponent digits, hence E-01."),
    dict(variant="es_output_leading_digit", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-005", facets=("ES-output-leading-digit",),
         title="ES finite output has one leading digit", descriptor="ES12.3E2",
         value="0.5", replacement_value="2.5", expected="   5.000E-01",
         derivation="The ES leading significand digit for 0.5 is the single digit 5 before the decimal symbol."),
    dict(variant="es_output_decimal_symbol", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-005", facets=("ES-output-decimal-symbol",),
         title="ES finite output contains the decimal symbol", descriptor="ES12.3E2",
         value="0.5", replacement_value="2.5", expected="   5.000E-01",
         derivation="POINT-mode formatted output places the decimal symbol after the ES leading digit 5."),
    dict(variant="es_output_d_fractional_digits", section=ES_SECTION, catalogue=ES_CATALOGUE,
         rule="S13.7.2.3.5-005", facets=("ES-output-d-fractional-digits",),
         title="ES finite output has d following digits", descriptor="ES12.3E2",
         value="0.5", replacement_value="2.5", expected="   5.000E-01",
         derivation="With d=3, the ES digits following the decimal symbol for 0.5 are exactly 000."),
]

CASE_BY_VARIANT = {case["variant"]: case for case in CASES}
SELECTED_FACETS_BY_CATALOGUE_RULE = {}
for case in CASES:
    SELECTED_FACETS_BY_CATALOGUE_RULE.setdefault((case["catalogue"], case["rule"]), set()).update(case["facets"])

ORACLE_PARAGRAPHS = {
    (EN_CATALOGUE, "S13.7.2.3.4-001"): (
        "S13.7.2.3.4-001 EN runtime fixtures: complete internal-file programs write exact default-real "
        "values using SS and explicit EN w.dE2 fields. 0.5 expects ' 500.000E-03', exercising engineering "
        "notation and an exponent divisible by three; 0.125 expects ' 125.000E-03', exercising the "
        "1<=yyy<1000 significand interval; the scale-factor fixture writes 0.5 with (SS,1P,EN12.3E2) and "
        "with a 0P control and expects the same field because EN output ignores scale factor. Descriptor "
        "substitutions EN<->ES, EN<->E, w, d, and e mutations are permanent and fail."),
    (EN_CATALOGUE, "S13.7.2.3.4-002"): (
        "S13.7.2.3.4-002 EN descriptor-form runtime fixtures: complete internal-file programs write exact "
        "values with SS. EN12.3E2 of 100.0 expects ' 100.000E+00' and proves the 12-position field; "
        "EN11.2E2 of 100.0 expects ' 100.00E+00' and proves d=2 fractional digits; EN12.3E2 of "
        "0.125 expects ' 125.000E-03' and proves explicit E2 gives two exponent digits. All descriptor "
        "substitutions in the generated matrix fail."),
    (EN_CATALOGUE, "S13.7.2.3.4-005"): (
        "S13.7.2.3.4-005 EN finite-output runtime fixtures: complete internal-file programs write exact "
        "0.5 with (SS,EN12.3E2) and expect ' 500.000E-03'. Separate fixtures bind the one-to-three "
        "leading significand digits and the decimal symbol. Expected fields check LEN before equality; "
        "the source keeps other facets in this requirement pending."),
    (ES_CATALOGUE, "S13.7.2.3.5-001"): (
        "S13.7.2.3.5-001 ES runtime fixtures: complete internal-file programs write exact default-real "
        "values using SS and explicit ES w.dE2 fields. 0.5 expects '   5.000E-01', exercising scientific "
        "notation; 0.125 expects '   1.250E-01', exercising the 1<=significand<10 interval; the "
        "scale-factor fixture writes 0.5 with (SS,2P,ES12.3E2) and with a 0P control and expects the "
        "same field because ES output ignores scale factor. Descriptor substitutions ES<->EN, ES<->E, "
        "w, d, and e mutations are permanent and fail."),
    (ES_CATALOGUE, "S13.7.2.3.5-002"): (
        "S13.7.2.3.5-002 ES descriptor-form runtime fixtures: complete internal-file programs write exact "
        "values with SS. ES12.3E2 of 100.0 expects '   1.000E+02' and proves the 12-position field; "
        "ES11.2E2 of 100.0 expects '   1.00E+02' and proves d=2 fractional digits; ES12.3E2 of "
        "0.125 expects '   1.250E-01' and proves explicit E2 gives two exponent digits. All descriptor "
        "substitutions in the generated matrix fail."),
    (ES_CATALOGUE, "S13.7.2.3.5-005"): (
        "S13.7.2.3.5-005 ES finite-output runtime fixtures: complete internal-file programs write exact "
        "0.5 with (SS,ES12.3E2) and expect '   5.000E-01'. Separate fixtures bind the single leading "
        "digit, the decimal symbol, and the three following digits. Expected fields check LEN before "
        "equality; the source keeps the Table 13.3 exponent-form facet pending."),
}

LIMIT_PARAGRAPHS = {
    EN_CATALOGUE: (
        "EN-editing fixture boundaries: this packet discharges only the selected EN output facets removed "
        "from pending above. It deliberately leaves EN input, IEEE infinity/NaN output, EN w.d alternative "
        "exponent spellings, exponent magnitudes above 99, E0/w=0 selected-width forms, zero exponent plus, "
        "diagnostics, external files, DECIMAL=COMMA, nondefault sign mode, processor-defined leading-zero "
        "mode for E/D/G, and rounded/inexact decimal cases pending. All positive outputs use SS and exact "
        "binary values whose discarded decimal digits are zero."),
    ES_CATALOGUE: (
        "ES-editing fixture boundaries: this packet discharges only the selected ES output facets removed "
        "from pending above. It deliberately leaves ES input, IEEE infinity/NaN output, ES w.d alternative "
        "exponent spellings, exponent magnitudes above 99, E0/w=0 selected-width forms, zero exponent plus, "
        "diagnostics, external files, DECIMAL=COMMA, nondefault sign mode, and rounded/inexact decimal "
        "cases pending. All positive outputs use SS and exact binary values whose discarded decimal digits "
        "are zero."),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    case = CASE_BY_VARIANT[variant]
    return case["rule"].replace(".", "_").replace("-", "_") + "_valid__en_es_editing_" + variant


def program_name(variant):
    return "eee_" + variant


_DESCRIPTOR_RE = re.compile(r"^(EN|ES)(\d+)\.(\d+)E(\d+)$")


def descriptor_mutations(descriptor):
    match = _DESCRIPTOR_RE.match(descriptor)
    if not match:
        raise ValueError("unsupported descriptor " + descriptor)
    kind, w, d, e = match.groups()
    counterpart = "ES" if kind == "EN" else "EN"
    other_w = "11" if w == "12" else "12"
    other_d = "2" if d == "3" else "3"
    other_e = "1" if e == "2" else "2"
    return (
        (descriptor, counterpart + w + "." + d + "E" + e, kind.lower() + "-to-" + counterpart.lower()),
        (descriptor, "E" + w + "." + d + "E" + e, kind.lower() + "-to-e"),
        (descriptor, kind + other_w + "." + d + "E" + e, "change-w"),
        (descriptor, kind + w + "." + other_d + "E" + e, "change-d"),
        (descriptor, kind + w + "." + d + "E" + other_e, "change-e"),
    )


def field_width(descriptor):
    match = _DESCRIPTOR_RE.match(descriptor)
    if not match:
        raise ValueError("unsupported descriptor " + descriptor)
    return int(match.group(2))


def format_for(case, control=False):
    prefix = "0P" if control else case.get("scale_prefix")
    parts = ["SS"]
    if prefix:
        parts.append(prefix)
    parts.append(case["descriptor"])
    return ",".join(parts)


class Program:
    def __init__(self, case):
        self.case = case
        self.variant = case["variant"]
        self.text = ""
        self.probes = []
        self.observations = []
        self.declarations = []
        self.body = []

    def declare(self, line):
        self.declarations.append("  " + line)

    def add(self, text):
        self.body.append(text)

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
            f"    write(*,'(a)') 'EEE:{self.variant}:check-total'\n"
            "    error stop 1\n"
            "  end if\n"
            f"  write(*,'(a)') '{completion}'\n"
            "contains\n"
            "  subroutine expect_text(observed, expected, label)\n"
            "    character(len=*), intent(in) :: observed, expected, label\n"
            "    if (len(observed) /= len(expected)) then\n"
            "      write(*,'(a,1x,a)') 'EEE:length', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    if (observed /= expected) then\n"
            "      write(*,'(a,1x,a)') 'EEE:text', label\n"
            "      error stop 1\n"
            "    end if\n"
            "    checks = checks + 1\n"
            "  end subroutine expect_text\n"
            f"end program {program_name(self.variant)}\n")

    def completion_literal(self):
        return "EN ES EDITING " + self.variant.upper().replace("_", " ") + " OK"

    def current_length(self):
        return len(self.render_prefix()) + sum(len(part) for part in self.body)

    def mutate_span_in_next(self, line, expected, replacement, probe_id, mutation, category, failure_stdout=None):
        start = self.current_length() + line.index(expected)
        self.probes.append(dict(
            id=probe_id, kind="source", category=category, mutation=mutation,
            span=[start, start + len(expected)], expected=expected, replacement=replacement,
            failure_stdout=failure_stdout if failure_stdout is not None else f"EEE:{self.variant}"))

    def assign_value(self):
        value = self.case["value"]
        line = f"  value = {value}\n"
        self.mutate_span_in_next(line, value, self.case["replacement_value"], "input-value", "input-value", "input")
        self.add(line)

    def init_field(self, name, width):
        self.add(f"  {name} = '{'#' * width}'\n")

    def write_stmt(self, buf, fmt, value_name, mutations=()):
        line = f"  write({buf},'({fmt})') {value_name}\n"
        for expected, replacement, tag in mutations:
            self.mutate_span_in_next(line, expected, replacement, f"descriptor-{tag}",
                                     "descriptor-substitution", "descriptor")
        self.mutate_span_in_next(line, "SS", "SP", f"sign-{buf}", "sign-mode-substitution", "sign")
        self.add(line)

    def expect_text(self, buf, expected, label):
        replacement = corrupt_text(expected)
        line = f"  call expect_text({buf}, '{expected}', '{label}')\n"
        self.mutate_span_in_next(line, expected, replacement, f"oracle-{label}", "text-oracle", "oracle",
                                 f"EEE:text {label}\n")
        self.add(line)
        self.observations.append(label)

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
            failure_stdout=f"EEE:{self.variant}:check-total\n"))
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


def corrupt_text(value):
    if not value:
        raise ValueError("empty text oracle")
    chars = list(value)
    for index in range(len(chars) - 1, -1, -1):
        if chars[index] != " ":
            chars[index] = "X" if chars[index] != "X" else "Y"
            return "".join(chars)
    chars[0] = "X"
    return "".join(chars)


def make_program(case):
    p = Program(case)
    width = field_width(case["descriptor"])
    p.declare("real :: value")
    if case.get("scale_prefix"):
        p.declare(f"character(len={width}) :: scaled, control")
        p.assign_value()
        p.init_field("scaled", width)
        p.init_field("control", width)
        p.write_stmt("scaled", format_for(case), "value", descriptor_mutations(case["descriptor"]))
        p.expect_text("scaled", case["expected"], "scaled")
        p.write_stmt("control", format_for(case, control=True), "value")
        p.expect_text("control", case["expected"], "control")
    else:
        p.declare(f"character(len={width}) :: field")
        p.assign_value()
        p.init_field("field", width)
        p.write_stmt("field", format_for(case), "value", descriptor_mutations(case["descriptor"]))
        p.expect_text("field", case["expected"], "field")
    text = p.source()
    return p, text


def source_specs():
    specs = {}
    for case in CASES:
        program, source = make_program(case)
        raw = source.encode("ascii")
        name = identifier(case["variant"])
        specs[name] = dict(
            id=name, variant=case["variant"], rule=case["rule"], facets=list(case["facets"]),
            section=case["section"], title=case["title"], descriptor=format_for(case),
            input_value=case["value"], expected=case["expected"], derivation=case["derivation"],
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
        directory = "tests/fixtures/en_es_editing_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate EN/ES fixture paragraph")
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
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""),
            ("EN-editing fixture boundaries:" if catalogue_path == EN_CATALOGUE else "ES-editing fixture boundaries:"),
            LIMIT_PARAGRAPHS[catalogue_path])
    return result


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
    note = summary_text(section)
    return before.rstrip() + "\n\n" + note + "\n\n" + begin + "\n\n" + \
        "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def summary_text(section):
    if section == EN_SECTION:
        return (SUMMARY_BEGIN + "\n"
                "## Executable EN editing fixtures\n\n"
                "This packet adds nine complete internal-file programs for selected 13.7.2.3.4 EN output "
                "facets. Each writes an exact binary default-real value to a CHARACTER variable initialized "
                "with # sentinels, uses SS to suppress optional plus signs, checks LEN before equality, and "
                "keeps the EN/ES/E descriptor-substitution matrix permanent in the generator.\n"
                + SUMMARY_END)
    return (SUMMARY_BEGIN + "\n"
            "## Executable ES editing fixtures\n\n"
            "This packet adds nine complete internal-file programs for selected 13.7.2.3.5 ES output "
            "facets. Each writes an exact binary default-real value to a CHARACTER variable initialized "
            "with # sentinels, uses SS to suppress optional plus signs, checks LEN before equality, and "
            "keeps the ES/EN/E descriptor-substitution matrix permanent in the generator.\n"
            + SUMMARY_END)


def generate(root=ROOT, check=False, sync_catalogues=False):
    root = Path(root)
    files, specs = build_corpus(root)
    updated_catalogues = {}
    updated_views = {}
    for catalogue_path, section, view_path in ((EN_CATALOGUE, EN_SECTION, EN_VIEW),
                                               (ES_CATALOGUE, ES_SECTION, ES_VIEW)):
        catalogue = json.loads((root / catalogue_path).read_text())
        updated = synced_catalogue(catalogue, catalogue_path)
        updated_catalogues[catalogue_path] = updated
        updated_views[view_path] = render_view(updated, section, view_path, root)
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        for catalogue_path, updated in updated_catalogues.items():
            if json.loads((root / catalogue_path).read_text()) != updated:
                stale.append(catalogue_path)
        for view_path, updated in updated_views.items():
            if (root / view_path).read_text() != updated:
                stale.append(view_path)
        if stale:
            raise ValueError("stale EN/ES editing fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogues:
            for catalogue_path, updated in updated_catalogues.items():
                (root / catalogue_path).write_text(json.dumps(updated, indent=2) + "\n")
            for view_path, updated in updated_views.items():
                (root / view_path).write_text(updated)
    return specs


def compiler_command(compiler, std, source, output):
    command = [str(compiler)]
    name = Path(compiler).name.lower()
    if std:
        command.append(("--std=" if "lfortran" in name else "-std=") + std)
    command += [str(source), "-o", str(output)]
    return command


def run_one_source(compiler, std, work_dir, source_text, expected_stdout, name):
    source = work_dir / (name + ".f90")
    exe = work_dir / (name + ".exe")
    source.write_text(source_text)
    compile_run = subprocess.run(compiler_command(compiler, std, source, exe), text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_run.returncode != 0:
        return dict(status="compile-fail", stdout=compile_run.stdout, stderr=compile_run.stderr,
                    returncode=compile_run.returncode)
    run = subprocess.run([str(exe)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    passed = (run.returncode == 0 and run.stdout == expected_stdout and run.stderr == "")
    return dict(status="pass" if passed else "run-fail", stdout=run.stdout, stderr=run.stderr,
                returncode=run.returncode)


def mutation_check(root, compiler, std, keep_work=False):
    root = Path(root)
    specs = source_specs()
    work_dir = root / ".en_es_mutation_runs" / sha((str(compiler) + str(std)).encode())[:12]
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
                                   replacement=probe["replacement"], parent_ok=parent_ok, failed=failed,
                                   status=observed["status"], stdout=observed["stdout"],
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
    descriptor = sum(1 for spec in specs.values() for probe in spec["probes"]
                     if probe["mutation"] == "descriptor-substitution")
    sign = sum(1 for spec in specs.values() for probe in spec["probes"]
               if probe["mutation"] == "sign-mode-substitution")
    inputs = sum(1 for spec in specs.values() for probe in spec["probes"] if probe["category"] == "input")
    return len(specs), len(facets), mutations, descriptor, sign, inputs


def mutation_matrix(report):
    matrix = {}
    for row in report:
        if row["mutation"] == "descriptor-substitution":
            key = (row["expected"], row["replacement"])
            matrix[key] = matrix.get(key, 0) + 1
    return matrix


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
        descriptor = sum(row["mutation"] == "descriptor-substitution" for row in report)
        sign = sum(row["mutation"] == "sign-mode-substitution" for row in report)
        matrix = mutation_matrix(report)
        pairs = ", ".join(f"{old}->{new}:{count}" for (old, new), count in sorted(matrix.items()))
        print(f"Mutation-checked {len(report)} EN/ES mutations: {descriptor} descriptor, {sign} sign; all failed.")
        print("Descriptor matrix: " + pairs)
        return
    specs = generate(args.root, args.check, args.sync_catalogues)
    case_count, facet_count, mutation_count, descriptor_count, sign_count, input_count = counts(specs)
    print(f"{'Checked' if args.check else 'Generated'} {case_count} EN/ES editing cases, "
          f"{facet_count} facets and {mutation_count} mutations "
          f"({descriptor_count} descriptor, {sign_count} sign, {input_count} input).")


if __name__ == "__main__":
    main()
