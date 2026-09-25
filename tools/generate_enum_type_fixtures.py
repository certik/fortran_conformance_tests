#!/usr/bin/env python3
"""Distinct unnamed ENUM,BIND(C) fixtures and one R762 diagnostic for 7.6.1."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from generate_assumed_rank_effect_fixtures import owned_paragraph
from generate_type_inheritance_fixtures import evidence_for_category

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.6.1"
CATALOGUE = "doc/catalogues/enum_type_7_6_1.json"
VIEW = "doc/fortran_2023_7_6_1.md"
PREFIX = "enum_type_"
SUMMARY_BEGIN = "<!-- BEGIN ENUM TYPE FIXTURES -->"
SUMMARY_END = "<!-- END ENUM TYPE FIXTURES -->"

ENUM_VALUE_SELECTED = {
    "S7.6.1-001": {"within-definition-common-kind"},
    "S7.6.1-004": {
        "first-implicit-zero", "explicit-values", "successor-after-explicit",
        "across-statement-boundary", "negative-and-repeated-values", "new-definition-reset",
    },
}
SELECTED = {
    "R759": {
        "single-enumerator-statement", "multiple-enumerator-statements", "nonempty-definition",
    },
    "R760": {"unnamed-bind-c"},
    "R761": {"colon-and-colon-free-admissions", "nonempty-list"},
    "R762": {
        "implicit-and-explicit-initializers", "prior-integer-constant-expression",
        "constant-initializer",
    },
    "R763": {"closing-statement-admission"},
    "C7111": {"no-initializer-controls"},
    "S7.6.1-004": {"named-constant-and-existing-context-graph"},
}
EXTERNAL_SELECTED = {
    "R760": {"required-bind-c", "required-comma", "c-language-designator"},
    "R761": {"list-separator"},
    "R762": {"scalar-initializer", "integer-initializer"},
    "R763": {"trailing-name"},
    "C7111": {"first-initializer", "later-list-initializer", "later-statement-initializer"},
}
EXTERNAL_PREFIXES = ("enum_type_7_6_1_b_",)

DIAGNOSTIC_CAUSE = "constant expression"
DIAGNOSTIC_EXCLUSIONS = (
    "internal compiler error", "internal error", "AssertFailed", "LCOMPILERS_ASSERT",
    "traceback", "segmentation fault", "not implemented", "unsupported", "verifier",
    "out of memory",
)
ORACLE_PREFIXES = {
    "R759": "R759 unnamed enum-def admission fixture: ",
    "R760": "R760 unnamed ENUM,BIND(C) admission fixture: ",
    "R761": "R761 enumerator-list admission fixture: ",
    "R762": "R762 constant-initializer admission fixture: ",
    "R763": "R763 END ENUM admission fixture: ",
    "C7111": "C7111 no-initializer control fixture: ",
    "S7.6.1-004": "S7.6.1-004 named-constant consumer fixture: ",
}
LIMIT_PREFIXES = {
    "R759": "R759 unnamed enum-def fixture boundaries: ",
    "R760": "R760 unnamed ENUM,BIND(C) fixture boundaries: ",
    "R761": "R761 enumerator-list fixture boundaries: ",
    "R762": "R762 constant-initializer fixture boundaries: ",
    "R763": "R763 END ENUM fixture boundaries: ",
    "C7111": "C7111 no-initializer control fixture boundaries: ",
    "S7.6.1-004": "S7.6.1-004 named-constant consumer fixture boundaries: ",
}
ORACLES = {
    "R759": ORACLE_PREFIXES["R759"] + (
        "one run/positive-control program has a complete unnamed ENUM,BIND(C) definition with a "
        "single enumerator statement, and a second complete unnamed definition with two enumerator "
        "statements. Runtime checks on constants from both definitions prove that the nonempty "
        "definitions are reached."
    ),
    "R760": ORACLE_PREFIXES["R760"] + (
        "one run/positive-control program uses only the required unnamed header spelling "
        "ENUM, BIND(C), with no :: enum-type-name group, and observes an enumerator from that definition."
    ),
    "R761": ORACLE_PREFIXES["R761"] + (
        "one run/positive-control program observes constants from a colon-free ENUMERATOR name list "
        "and from a colon-present initialized list. Both lists are nonempty and comma separated."
    ),
    "R762": ORACLE_PREFIXES["R762"] + (
        "one run/positive-control program admits omitted initializers and a prior INTEGER PARAMETER "
        "initializer seed in ENUMERATOR :: first = seed. A paired invalid compile fixture differs only "
        "by removing PARAMETER from seed's declaration, so seed is an initialized integer variable rather "
        "than a constant expression. The invalid fixture is line-anchored at the enumerator initializer "
        "and excludes ICE/internal-error text; frozen LFortran currently ICEs there while GNU f2023 "
        "reports the constant-expression violation."
    ),
    "R763": ORACLE_PREFIXES["R763"] + (
        "one run/positive-control program closes an unnamed definition with END ENUM and observes an "
        "enumerator declared before the terminator."
    ),
    "C7111": ORACLE_PREFIXES["C7111"] + (
        "one run/positive-control program contains colon-present and colon-free ENUMERATOR statements "
        "with no initializer in either statement, proving the no-initializer antecedent control."
    ),
    "S7.6.1-004": ORACLE_PREFIXES["S7.6.1-004"] + (
        "one run/effect program uses enumerators as specification expressions in array bounds, writes "
        "nonzero sentinels, and checks the resulting bounds, sizes and payload. Existing enum_value "
        "fixtures continue to own default, explicit, successor, cross-statement, negative/repeated and "
        "fresh-definition value facets."
    ),
}
LIMITATIONS = {
    "R759": LIMIT_PREFIXES["R759"] + (
        "empty definitions, missing terminators and source-use graph facets remain pending. The runtime "
        "case is a finite positive admission/control, not a diagnostic vocabulary policy."
    ),
    "R760": LIMIT_PREFIXES["R760"] + (
        "missing BIND(C), missing comma, wrong language designator, named header separator and named enum "
        "type syntax remain pending. GNU f2023 rejected named enum type syntax during qualification."
    ),
    "R761": LIMIT_PREFIXES["R761"] + (
        "missing commas, empty lists and initializer-triggered separator diagnostics remain pending."
    ),
    "R762": LIMIT_PREFIXES["R762"] + (
        "scalar and integer initializer diagnostics plus broader constant/name consumer graphs remain pending. "
        "The shipped nonconstant-initializer negative is expected to fail on frozen LFortran because an ICE is "
        "not a diagnosis; GNU f2023 supplies the validating diagnostic."
    ),
    "R763": LIMIT_PREFIXES["R763"] + (
        "trailing enum names and Clause 6 spelling reuse remain pending or owned elsewhere."
    ),
    "C7111": LIMIT_PREFIXES["C7111"] + (
        "missing double-colon diagnostics for initialized statements remain pending; this is only the "
        "no-initializer positive control."
    ),
    "S7.6.1-004": LIMIT_PREFIXES["S7.6.1-004"] + (
        "only named-constant use in array bounds is added here. No C_INT kind equality, named enum type, "
        "constructor, BOZ, C companion or representation claim is made."
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_id(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__enum_type_" + variant


def invalid_id(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_invalid__enum_type_" + variant


class Program:
    def __init__(self, variant, completion):
        self.variant = variant
        self.completion = completion
        self.text = ""
        self.guards = []
        self.feature_mutations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def feature_line(self, line, expected, replacement, name, *, category="enum-source"):
        start = len(self.text) + line.index(expected)
        self.add(line)
        self.feature_mutations.append(dict(
            id=name, kind="feature", category=category, expected=expected,
            replacement=replacement, span=[start, start + len(expected)],
            line=self.text[:start].count("\n") + 1, mutation="enum-feature-substitution"))

    def guard_equal(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"ETY:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter,
            mutation="guard-literal-expectation", failure_token=token,
            failure_stdout=token + "\n")
        self.add(prefix + expected + ") then\n")
        self.add(f"    write(*,'(a)') '{token}'\n")
        self.add("    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter} = {counter} + 1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)

    def finish(self, expected_checks):
        self.guard_equal("check-total", "checks", expected_checks, expected_checks + 1,
                         category="completion", counter=None)
        literal = self.completion.rstrip("\n")
        block_start = len(self.text)
        prefix = "  write(*,'(a)') '"
        start = block_start + len(prefix)
        guard = dict(
            id="completion-output", guard_id="completion-output", kind="output",
            category="completion", expected=literal,
            replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
            line=self.text.count("\n") + 1, counter=None, mutation="completion-literal",
            failure_token="", failure_stdout="")
        self.add(prefix + literal + "'\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)


def r759_program():
    p = Program("enum_def_structure", "ENUM TYPE R759 ENUM DEF STRUCTURE OK\n")
    p.add("program enum_type_enum_def_structure\n  implicit none\n  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator solo\n", "solo", "inserted, solo", "insert-before-single-enumerator")
    p.add("  end enum\n  enum, bind(c)\n")
    p.feature_line("    enumerator :: anchor = 3\n", " = 3", "", "remove-anchor-initializer")
    p.add("    enumerator follower\n  end enum\n  checks = 0\n")
    p.guard_equal("single-definition-value", "solo", 0, 1)
    p.guard_equal("multiple-statement-successor", "follower", 4, 1)
    p.finish(2)
    p.add("end program enum_type_enum_def_structure\n")
    return p


def r760_program():
    p = Program("unnamed_bind_c", "ENUM TYPE R760 UNNAMED BIND C OK\n")
    p.add("program enum_type_unnamed_bind_c\n  implicit none\n  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator :: required = 8, observed\n", " = 8", "", "remove-header-definition-initializer")
    p.add("  end enum\n  checks = 0\n")
    p.guard_equal("unnamed-bind-c-observed", "observed", 9, 1)
    p.finish(1)
    p.add("end program enum_type_unnamed_bind_c\n")
    return p


def r761_program():
    p = Program("enumerator_lists", "ENUM TYPE R761 ENUMERATOR LISTS OK\n")
    p.add("program enum_type_enumerator_lists\n  implicit none\n  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator plain_a, plain_b\n", "plain_a, plain_b", "plain_b, plain_a",
                   "reorder-colon-free-list")
    p.feature_line("    enumerator :: explicit_c = 5, explicit_d\n", " = 5", "",
                   "remove-colon-present-initializer")
    p.add("  end enum\n  checks = 0\n")
    p.guard_equal("colon-free-list-order", "plain_b", 1, 0)
    p.guard_equal("colon-present-list-successor", "explicit_d", 6, 3)
    p.finish(2)
    p.add("end program enum_type_enumerator_lists\n")
    return p


def r762_program(parameter=True):
    variant = "constant_initializers"
    p = Program(variant, "ENUM TYPE R762 CONSTANT INITIALIZERS OK\n")
    attr = ", parameter" if parameter else ""
    p.add(f"program enum_type_constant_initializers\n  implicit none\n  integer{attr} :: seed = 4\n"
          "  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator :: first = seed, second\n", " = seed", "",
                   "remove-prior-constant-initializer")
    p.add("    enumerator implicit_tail\n  end enum\n  checks = 0\n")
    p.guard_equal("prior-parameter-value", "first", 4, 0)
    p.guard_equal("implicit-after-parameter", "second", 5, 1)
    p.guard_equal("implicit-initializer-admission", "implicit_tail", 6, 2)
    p.finish(3)
    p.add("end program enum_type_constant_initializers\n")
    return p


def r762_diagnostic_source(parameter):
    attr = ", parameter" if parameter else ""
    return (
        "program enum_type_nonconstant_initializer\n"
        "  implicit none\n"
        f"  integer{attr} :: seed = 4\n"
        "  enum, bind(c)\n"
        "    enumerator :: first = seed\n"
        "  end enum\n"
        "end program enum_type_nonconstant_initializer\n")


def r763_program():
    p = Program("end_enum", "ENUM TYPE R763 END ENUM OK\n")
    p.add("program enum_type_end_enum\n  implicit none\n  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator :: before_end = 6, after_value\n", " = 6", "",
                   "remove-pre-end-initializer")
    p.add("  end enum\n  checks = 0\n")
    p.guard_equal("closed-definition-value", "after_value", 7, 1)
    p.finish(1)
    p.add("end program enum_type_end_enum\n")
    return p


def c7111_program():
    p = Program("no_initializer_control", "ENUM TYPE C7111 NO INITIALIZER CONTROL OK\n")
    p.add("program enum_type_no_initializer_control\n  implicit none\n  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator :: colon_a, colon_b\n", "colon_a, colon_b", "colon_b, colon_a",
                   "reorder-colon-present-no-initializer")
    p.feature_line("    enumerator bare_a, bare_b\n", "bare_a, bare_b", "inserted, bare_a, bare_b",
                   "insert-before-colon-free-no-initializer")
    p.add("  end enum\n  checks = 0\n")
    p.guard_equal("colon-present-no-initializer", "colon_b", 1, 0)
    p.guard_equal("colon-free-no-initializer", "bare_a", 2, 3)
    p.finish(2)
    p.add("end program enum_type_no_initializer_control\n")
    return p


def s761004_program():
    p = Program("unnamed_syntax_constants", "ENUM TYPE NAMED CONSTANT CONSUMER OK\n")
    p.add("program enum_type_unnamed_syntax_constants\n  implicit none\n  integer :: checks\n  enum, bind(c)\n")
    p.feature_line("    enumerator :: lower = 2, upper = 5\n", " = 2", "",
                   "remove-lower-bound-initializer")
    p.feature_line("    enumerator extent_marker\n", "extent_marker", "inserted, extent_marker",
                   "insert-before-bound-marker")
    p.add("  end enum\n  integer :: table(lower:upper)\n  integer :: vector(upper + extent_marker)\n"
          "  checks = 0\n  table = 37\n  vector = 41\n")
    p.guard_equal("array-lower-bound", "lbound(table, 1)", 2, 1, category="constant-consumer")
    p.guard_equal("array-upper-bound", "ubound(table, 1)", 5, 4, category="constant-consumer")
    p.guard_equal("array-size-from-two-enumerators", "size(vector)", 11, 10, category="constant-consumer")
    p.guard_equal("table-sentinel", "table(upper)", 37, 0, category="sentinel")
    p.guard_equal("vector-sentinel", "vector(1)", 41, 0, category="sentinel")
    p.finish(5)
    p.add("end program enum_type_unnamed_syntax_constants\n")
    return p


PROGRAMS = {
    "R759": r759_program,
    "R760": r760_program,
    "R761": r761_program,
    "R762": r762_program,
    "R763": r763_program,
    "C7111": c7111_program,
    "S7.6.1-004": s761004_program,
}


def wrong_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("parent source fingerprint changed")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("mutation span no longer binds the parent source")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def program_mutations(p):
    raw = p.text.encode("ascii")
    mutations = []
    for guard in p.guards:
        start, end = guard["span"]
        if raw[start:end].decode("ascii") != guard["expected"]:
            raise ValueError("guard span lost parent binding: " + guard["id"])
        mutations.append(dict(guard))
        if guard["kind"] == "guard" and guard.get("counter"):
            start, end = guard["block_span"]
            mutations.append(dict(
                id="omit-observation-" + guard["id"], guard_id="check-total", kind="guard",
                category="omission", expected=p.text[start:end], replacement="", span=[start, end],
                line=p.text[:start].count("\n") + 1, mutation="whole-observation-omission",
                failure_token=f"ETY:{p.variant}:check-total",
                failure_stdout=f"ETY:{p.variant}:check-total\n"))
    completion = p.guards[-1]
    mutations.append(dict(
        id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
        expected=p.text[completion["block_span"][0]:completion["block_span"][1]], replacement="",
        span=completion["block_span"], line=p.text[:completion["block_span"][0]].count("\n") + 1,
        mutation="completion-statement-omission", failure_stdout=""))
    for mutation in p.feature_mutations:
        start, end = mutation["span"]
        if raw[start:end].decode("ascii") != mutation["expected"]:
            raise ValueError("feature mutation span lost parent binding: " + mutation["id"])
        mutations.append(dict(mutation))
    return mutations


def source_specs():
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    categories = {row["id"]: row["category"] for row in catalogue["requirements"]}
    specs = {}
    for rule, builder in PROGRAMS.items():
        p = builder()
        raw = p.text.encode("ascii")
        name = valid_id(rule, p.variant)
        specs[name] = dict(
            id=name, variant=p.variant, rule=rule, facets=sorted(SELECTED[rule]),
            evidence=evidence_for_category(categories[rule]), standard="f2023",
            kind="valid", phase="run", source=p.text, source_sha256=sha(raw),
            completion=p.completion, mutations=program_mutations(p),
            feature_mutations=p.feature_mutations, guards=p.guards)
    control_source = r762_diagnostic_source(parameter=True)
    control_name = valid_id("R762", "nonconstant_initializer_control")
    specs[control_name] = dict(
        id=control_name, variant="nonconstant_initializer_control", rule="R762",
        facets=["constant-initializer"], evidence="positive-control", standard="f2023",
        kind="valid", phase="compile", source=control_source,
        source_sha256=sha(control_source.encode("ascii")))
    invalid_source = r762_diagnostic_source(parameter=False)
    raw = invalid_source.encode("ascii")
    name = invalid_id("R762", "nonconstant_initializer")
    specs[name] = dict(
        id=name, variant="nonconstant_initializer", rule="R762", facets=["constant-initializer"],
        evidence="effect", standard="f2023", kind="invalid", phase="compile", source=invalid_source,
        source_sha256=sha(raw), control_id=control_name,
        diagnostic=dict(file="source.f90", line=5, end_line=5,
                        contains_any=[DIAGNOSTIC_CAUSE],
                        excludes_any=list(DIAGNOSTIC_EXCLUSIONS)))
    return specs


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / (PREFIX + spec["variant"])
        expect = dict(phase=spec["phase"])
        link = None
        if spec["kind"] == "invalid":
            expect.update(step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
        elif spec["phase"] == "compile":
            expect.update(step="source", outcome="success")
        else:
            link = dict(driver="fortran", objects=["source.o"], output="program")
            expect.update(outcome="success", exit_code=0, stdout=spec["completion"], stderr="")
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran",
                        form="free", output="source.o")],
            expect=expect)
        if link:
            manifest["link"] = link
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def union_coverage():
    result = {rule: set(facets) for rule, facets in ENUM_VALUE_SELECTED.items()}
    for rule, facets in SELECTED.items():
        result.setdefault(rule, set()).update(facets)
    for rule, facets in EXTERNAL_SELECTED.items():
        result.setdefault(rule, set()).update(facets)
    return result


OBSOLETE_ORACLE_PREFIXES = {
    "R759": ("R759 unnamed enum-def admission fixtures: ",
             "R759 enum_type_7_6_1_b diagnostic fixtures: "),
    "R762": ("R762 initializer syntax fixtures: ",),
}
OBSOLETE_LIMIT_PREFIXES = {
    "R759": ("R759 enum_type_7_6_1_b diagnostic boundaries: ",),
    "R762": ("R762 initializer fixture boundaries: ",),
}


def replace_owned(text, prefix, replacement, obsolete=()):
    prefixes = (prefix, *obsolete)
    paragraphs = [paragraph for paragraph in text.split("\n\n")
                  if not any(paragraph.startswith(item) for item in prefixes)]
    return ("\n\n".join(p for p in paragraphs if p) + ("\n\n" if paragraphs and any(paragraphs) else "")
            + replacement)


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    coverage = union_coverage()
    import generate_enum_type_7_6_1_b_fixtures as enum_type_b
    for requirement in updated["requirements"]:
        facets = coverage.get(requirement["id"], set())
        for facet in facets:
            requirement["pending"].pop(facet, None)
        expected_pending = set(requirement["facets"]) - facets
        if set(requirement.get("pending", {})) != expected_pending:
            raise ValueError("enum_type shared pending partition mismatch for " + requirement["id"])
        if requirement["id"] in SELECTED:
            rule = requirement["id"]
            requirement["oracle"] = replace_owned(
                requirement.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule],
                OBSOLETE_ORACLE_PREFIXES.get(rule, ()))
            requirement["oracle_limitation"] = replace_owned(
                requirement.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule],
                OBSOLETE_LIMIT_PREFIXES.get(rule, ()))
        if requirement["id"] in enum_type_b.SELECTED:
            rule = requirement["id"]
            requirement["oracle"] = replace_owned(
                requirement.get("oracle", ""), enum_type_b.ORACLE_PREFIXES[rule], enum_type_b.ORACLES[rule])
            requirement["oracle_limitation"] = replace_owned(
                requirement.get("oracle_limitation", ""), enum_type_b.LIMIT_PREFIXES[rule],
                enum_type_b.LIMITATIONS[rule])
    return updated


def catalogue_review_status(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import Registry
    registry = Registry(Path(root))
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the 7.6.1 generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    pending = sum(len(row.get("pending", {})) for row in catalogue["requirements"])
    represented = sum(len(row["facets"]) for row in catalogue["requirements"]) - pending
    before = re.sub(
        r"\*\*Catalogue source review: [^.]+\.?\*\*",
        f"**Catalogue source review: {catalogue_review_status(catalogue, root)}.**",
        before,
        count=1)
    before = before.replace(
        "All23 original base units,93 fine units,116 accounting rows,15 requirements and64\n"
        "facet identities are preserved. Only the seven selected pending/oracle\n"
        "implementation entries change. Named enum types, ENUMERATION TYPE, BOZ,\n"
        "representation/C-companion profiles, unsigned extremes, source-use links and\n"
        "diagnostic policies remain outside this packet.",
        "All23 original base units,93 fine units,116 accounting rows,15 requirements and64\n"
        "facet identities are preserved. The enum_value and enum_type generators own only\n"
        "their selected pending/oracle implementation entries. Named enum types,\n"
        "ENUMERATION TYPE, BOZ, representation/C-companion profiles, unsigned extremes and\n"
        "source-use links remain outside this packet; only the R762 nonconstant-initializer\n"
        "diagnostic is newly executable.")
    before = before.replace(
        "source-use links remain outside this packet; only the R762 nonconstant-initializer\n"
        "diagnostic is newly executable.",
        "source-use links remain outside this packet; enum_type diagnostics now add the R762\n"
        "nonconstant-initializer pair and ten unnamed-header/list/initializer controls.")
    before = before.replace(
        "All cases remain run-phase on implementation failure. Frozen LF411, GNU actual\n"
        "f2023 and Flang actual f2018 observations retain their original inputs, compiler\n"
        "identities, ordered compile/link/run traces and source_root. No f2018 observation\n"
        "is relabelled as f2023 and no compiler consensus supplies an expected value.",
        "Enum_value cases remain run-phase on implementation failure. Enum_type adds\n"
        "positive run/compile controls and one R762 compile diagnostic whose GNU f2023\n"
        "acceptance and frozen-LFortran ICE are reported separately. No f2018 observation\n"
        "is relabelled as f2023 and no compiler consensus supplies an expected value.")
    before = before.replace(
        "Enum_value cases remain run-phase on implementation failure. Enum_type adds\n"
        "positive run/compile controls and one R762 compile diagnostic whose GNU f2023\n"
        "acceptance and frozen-LFortran ICE are reported separately. No f2018 observation\n"
        "is relabelled as f2023 and no compiler consensus supplies an expected value.",
        "Enum_value cases remain run-phase on implementation failure. Enum_type generators add\n"
        "positive run/compile controls and compile diagnostics whose GNU f2023 acceptance and\n"
        "frozen-LFortran divergences are reported separately. No f2018 observation is relabelled\n"
        "as f2023 and no compiler consensus supplies an expected value.")
    before = re.sub(
        r"\*\*[^\n]*\*\* represent \*\*\d+ of64 facets\*\*; \*\*\d+ remain pending\*\*\."
        r"(?: There are no new diagnostic or compile-only cases\.)?",
        f"**Seven run fixtures, eleven compile controls and eleven diagnostic fixtures** represent **{represented} of64 facets**; "
        f"**{pending} remain pending**.",
        before,
        count=1)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Unnamed ENUM syntax, constants and diagnostics\n\n"
        "Seven generated `enum_type_` runtime fixtures use distinct sources/assertions for positive "
        "7.6.1 coverage, and one compile-control/diagnostic pair checks the R762 nonconstant "
        "initializer violation. The R762 invalid source differs from its conforming control only by "
        "removing `PARAMETER` from `integer, parameter :: seed = 4`; the enumerator statement still "
        "has `::` and an integer scalar initializer, so the isolated property is constancy.\n\n"
        "The separate `enum_type_7_6_1_b_` diagnostics add ten one-property compile-control/"
        "invalid pairs for remaining unnamed ENUM,BIND(C) syntax facets. GNU Fortran 16.1 accepts "
        "unnamed `ENUM, BIND(C)` but rejects named enum-type syntax (`ENUM, BIND(C) :: name`) and "
        "all probed `ENUMERATION TYPE` forms, so named type/constructor facets remain pending.\n\n"
        "The sources use only C-interoperable unnamed `ENUM, BIND(C)`, not 7.6.2 `ENUMERATION TYPE`, "
        "named enum types, enum constructors, BOZ operands, C companions, representation probes, or "
        "`KIND(enumerator)==C_INT`. The pinned text makes C_INT an evaluation route, not the required "
        "selected kind.\n\n"
        "The permanent mutation runner covers only genuine runtime parents once: guard flips, "
        "observation omissions, completion removal, and conforming source-feature substitutions bound "
        "to each distinct source. The diagnostic fixture is validated by the normal compile-diagnostic "
        "runner with ICE/internal-error exclusions rather than by runtime mutation.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the enum_type summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    tail = ("\n\n## Complete finite pending plans\n\n"
            "Every unselected original plan is retained. Incidental checks do not create "
            "source-use/link or extra requirement credit.\n\n")
    for requirement in catalogue["requirements"]:
        if requirement.get("pending"):
            tail += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                tail += f"* **`{facet}`** - {plan}\n"
            tail += "\n"
    tail += (
        "## Reproduction and separate gates\n\n"
        "`python3 -B tools/generate_enum_type_fixtures.py --check` and "
        "`python3 -B tools/generate_enum_type_7_6_1_b_fixtures.py --check`, plus "
        "`python3 -B tools/generate_enum_value_fixtures.py --check` verify exact bytes and the "
        "shared 7.6.1 generated view. The enum_type mutation runner covers only distinct runtime "
        "parents; compile diagnostics are checked by the compile-diagnostic runner. Named enum types, "
        "constructors, BOZ, C companions and representation evidence remain pending because the "
        "reference rejects the named-type syntax needed to qualify them.\n")
    return (before + begin + "\n\n"
            + "\n".join(render_requirement(row) for row in catalogue["requirements"])
            + "\n" + end + tail)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {path for path in (root / "tests/fixtures").glob(PREFIX + "*/*") if path.is_file()
                  if not any(path.parent.name.startswith(prefix) for prefix in EXTERNAL_PREFIXES)}
        stale += [path.relative_to(root).as_posix() for path in sorted(actual - set(files))]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale enum_type fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return files, specs


def executable_command(compiler, std, source, output):
    if "lfortran" in Path(compiler).name.lower():
        return [compiler, f"--std={std}", str(source), "-o", str(output)]
    return [compiler, f"-std={std}", str(source), "-o", str(output)]


def run_source(compiler, std, cwd, source, exe, completion):
    compile_result = subprocess.run(
        executable_command(compiler, std, source, exe), cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if compile_result.returncode != 0:
        return "compile-fail", compile_result.stdout
    run_result = subprocess.run(
        [str(exe)], cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=30)
    return ("pass" if run_result.returncode == 0 and run_result.stdout == completion else "run-fail",
            run_result.stdout)


def check_mutations(root, compiler, std, vacuity_probe=False):
    root = Path(root)
    _, specs = build_corpus(root)
    mutations = [(spec, mutation) for spec in specs.values() if spec["phase"] == "run"
                 for mutation in spec["mutations"]]
    if vacuity_probe:
        first = next(spec for spec in specs.values() if spec["phase"] == "run")
        mutations.append((first, dict(id="vacuity-identical-parent", source=first["source"], identical=True)))
    if not mutations:
        raise SystemExit("no enum_type mutations defined")
    workspace = Path(tempfile.mkdtemp(prefix=".enum_type_mutations_", dir=root))
    failures = []
    checked = 0
    vacuity_reported = False
    try:
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
            case_dir.mkdir()
            parent_source = case_dir / "parent.f90"
            parent_exe = case_dir / "parent"
            parent_source.write_text(spec["source"])
            parent_status, parent_output = run_source(
                compiler, std, case_dir, parent_source, parent_exe, spec["completion"])
            if parent_status != "pass":
                failures.append(f"{spec['id']} parent did not pass before mutation ({parent_status}):\n{parent_output}")
                continue
            source = case_dir / "source.f90"
            exe = case_dir / "program"
            mutant = mutation.get("source")
            source.write_bytes(mutant.encode("ascii") if mutant is not None else wrong_source(spec, mutation))
            status, output = run_source(compiler, std, case_dir, source, exe, spec["completion"])
            if status == "compile-fail":
                failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{output}")
                continue
            checked += 1
            if status == "pass":
                if mutation.get("identical"):
                    vacuity_reported = True
                else:
                    failures.append(f"{spec['id']}:{mutation['id']} survived")
        if vacuity_probe:
            if not vacuity_reported:
                failures.append("vacuity probe did not report the identical mutant as survived")
            if failures:
                raise SystemExit("\n\n".join(failures))
            print(f"Vacuity probe: identical mutant reported as survived for {compiler} ({std}).")
            return
        if failures:
            raise SystemExit("\n\n".join(failures))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    print(f"Mutation check: {checked}/{checked} mutants failed for {compiler} ({std}).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--check-mutations", action="store_true")
    parser.add_argument("--vacuity-probe", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.check_mutations, args.vacuity_probe))) > 1:
        parser.error("--check, --sync-catalogue, --check-mutations and --vacuity-probe are separate operations")
    if (args.check_mutations or args.vacuity_probe) and (not args.compiler or not args.std):
        parser.error("mutation modes require --compiler and --std")
    if args.check_mutations or args.vacuity_probe:
        check_mutations(args.root, args.compiler, args.std, args.vacuity_probe)
        return
    _, specs = generate(args.root, args.check, args.sync_catalogue)
    facets = sum(len(facets) for facets in SELECTED.values())
    mutations = sum(len(spec.get("mutations", [])) for spec in specs.values() if spec["phase"] == "run")
    diagnostics = sum(1 for spec in specs.values() if spec["kind"] == "invalid")
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} enum_type cases, "
          f"{facets} facet bindings, {mutations} runtime mutations and {diagnostics} diagnostic.")


if __name__ == "__main__":
    main()
