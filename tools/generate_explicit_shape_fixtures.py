#!/usr/bin/env python3
"""Runtime fixtures for scalar explicit-shape array bounds in 8.5.8.2."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.5.8.2"
CATALOGUE = "doc/catalogues/explicit_shape_8_5_8_2.json"
VIEW = "doc/fortran_2023_8_5_8_2.md"
SUMMARY_BEGIN = "<!-- BEGIN EXPLICIT SHAPE SCALAR EFFECTS -->"
SUMMARY_END = "<!-- END EXPLICIT SHAPE SCALAR EFFECTS -->"

VARIANTS = {
    "scalar_bounds": ("S8.5.8.2-002", [
        "upper-only-default", "per-dimension-bounds", "mixed-omitted-lowers"]),
    "range_bounds": ("S8.5.8.2-004", [
        "bound-signs", "inclusive-nonempty-range", "singleton-zero-bound"]),
    "empty_ranges": ("S8.5.8.2-004", [
        "empty-one-dimensional", "mixed-zero-extent"]),
}
FACETS_BY_RULE = {
    "S8.5.8.2-002": ["upper-only-default", "per-dimension-bounds", "mixed-omitted-lowers"],
    "S8.5.8.2-004": [
        "bound-signs", "inclusive-nonempty-range", "singleton-zero-bound",
        "empty-one-dimensional", "mixed-zero-extent"],
}
REMAINING_PENDING = {
    "S8.5.8.2-002": set(),
    "S8.5.8.2-004": {"inquiry-normalization-source"},
}
COMPLETIONS = {
    variant: "EXPLICIT SHAPE " + variant.upper().replace("_", " ") + " OK\n"
    for variant in VARIANTS
}
ORACLE_PREFIXES = {
    "S8.5.8.2-002": "Scalar explicit-shape bounds runtime fixtures: ",
    "S8.5.8.2-004": "Scalar explicit-shape range runtime fixtures: ",
}
LIMIT_PREFIXES = {
    "S8.5.8.2-002": "Scalar explicit-shape bounds fixture boundaries: ",
    "S8.5.8.2-004": "Scalar explicit-shape range fixture boundaries: ",
}
ORACLES = {
    "S8.5.8.2-002": ORACLE_PREFIXES["S8.5.8.2-002"] + (
        "one complete run/effect/f2023 program declares three ordinary local INTEGER arrays with scalar "
        "explicit-shape-spec lists. `upper_only(4)` observes omitted lower bound one through LBOUND=[1], "
        "UBOUND=[4], SHAPE=[4], SIZE=4 and a nonzero whole-array payload. `explicit2d(-2:0,4:5)` observes "
        "dimension-order lower bounds [-2,4], upper bounds [0,5], shape [3,2], total size six and payload 52. "
        "`mixed(2,-1:1)` observes an omitted lower bound in only the first dimension, lower [1,-1], upper [2,1], "
        "shape [2,3], total size six and payload 63. Feature substitutions replace the upper-only declaration "
        "with a same-extent nonunit lower bound and remove explicit lower bounds from the other declarations, so "
        "default-lower and per-dimension lower-bound behavior are load-bearing rather than descriptor aliases."
    ),
    "S8.5.8.2-004": ORACLE_PREFIXES["S8.5.8.2-004"] + (
        "two complete run/effect/f2023 programs exercise scalar bound signs, inclusive nonempty ranges, singleton "
        "zero bounds and empty ranges. The range program declares positive_range(2:4), negative_range(-2:0) and "
        "zero_singleton(0:0), assigns nonzero whole-array payloads, observes bounds/shape/size and reads the actual "
        "lower and upper endpoint elements through LBOUND/UBOUND-derived subscripts. The empty program declares "
        "empty1(5:3) and empty2(5:3,-2:1), observes rank, normalized whole-array bounds, shapes [0] and [0,4], "
        "SIZE=0 for both, and a nonzero scalar path sentinel without reading any nonexistent element. Feature "
        "substitutions turn ranges into same-rank nonempty or default-lower declarations, so zero extent, inclusive "
        "range and bound-sign effects are distinguished while every mutant remains a conforming program."
    ),
}
LIMITATIONS = {
    "S8.5.8.2-002": LIMIT_PREFIXES["S8.5.8.2-002"] + (
        "only scalar explicit-shape-spec-list effects on ordinary local INTEGER arrays are covered. This packet does "
        "not claim vector-bound syntax, rank-zero scalar vector-boundary behavior, dummy sequence association, "
        "function results, diagnostics, type parameters, storage layout, contiguity, coarrays, COMMON/EQUIVALENCE, "
        "allocation, pointer association or named-local nonconstant entry-capture semantics."
    ),
    "S8.5.8.2-004": LIMIT_PREFIXES["S8.5.8.2-004"] + (
        "only valid scalar-list declarations with small default INTEGER bounds are covered. Empty arrays are observed "
        "only through permitted whole-array inquiries and a separate path sentinel; no element access, section "
        "inquiry boundary, assumed-size, optional dummy, allocation or processor diagnostic behavior is asserted. "
        "The separate inquiry-normalization-source facet remains pending."
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__explicit_shape_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facets = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.observations = []
        self.input_mutations = []
        self.feature_mutations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def add_input_line(self, line, expected, replacement, name):
        start = len(self.text) + line.index(expected)
        self.add(line)
        self.input_mutations.append(dict(
            id=name, kind="input", category="input", expected=expected, replacement=replacement,
            span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
            mutation="input-sentinel-literal"))

    def add_line_with_feature(self, line, expected, replacement, name):
        start = len(self.text) + line.index(expected)
        self.add(line)
        self.feature_mutations.append(dict(
            id=name, kind="feature", category="explicit-shape-spec", expected=expected, replacement=replacement,
            span=[start, start + len(expected)], line=self.text[:start].count("\n") + 1,
            mutation="feature-under-test-substitution"))

    def guard_equal(self, name, expression, expected, replacement, *, category="value", counter="checks"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if ({expression} /= "
        start = block_start + len(prefix)
        token = f"ESH:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter,
            mutation="guard-literal-expectation", failure_token=token)
        self.add(prefix + expected + ") then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n")
        if counter:
            self.add(f"  {counter}=checks+1\n")
            self.observations.append(guard)
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        return guard

    def guard_any(self, name, expression, expected, replacement, *, category="shape"):
        expected, replacement = str(expected), str(replacement)
        block_start = len(self.text)
        prefix = f"  if (any({expression} /= "
        start = block_start + len(prefix)
        token = f"ESH:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter="checks",
            mutation="guard-vector-expectation", failure_token=token)
        self.add(prefix + expected + ")) then\n" + f"    write(*,'(a)') '{token}'\n"
                 + "    error stop\n  end if\n  checks=checks+1\n")
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.observations.append(guard)
        return guard

    def finish(self):
        self.guard_equal("check-total", "checks", len(self.observations), len(self.observations) + 1,
                         category="completion", counter=None)
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        completion = dict(
            id="completion-output", guard_id="completion-output", kind="output", category="completion",
            expected=literal, replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
            line=self.text.count("\n") + 1, counter=None, mutation="completion-literal",
            failure_token="")
        completion["block_span"] = self.add(prefix + literal + "'\n")
        self.guards.append(completion)
        self.add(f"end program explicit_shape_{self.variant}\n")


def start_program(p):
    p.add(f"! rule: {p.rule}\n! covers: {','.join(p.facets)}\n")
    p.add("! Expected bounds, extents and payloads are hand-derived from Fortran 2023 8.5.8.2.\n")
    p.add(f"program explicit_shape_{p.variant}\n  implicit none\n  integer :: checks\n")


def scalar_bounds_program():
    p = Program("scalar_bounds")
    start_program(p)
    p.add_line_with_feature("  integer :: upper_only(4)\n", "upper_only(4)", "upper_only(-2:1)",
                            "feature-upper-only-to-nonunit-lower")
    p.add_line_with_feature("  integer :: explicit2d(-2:0,4:5)\n", "explicit2d(-2:0,4:5)", "explicit2d(3,2)",
                            "feature-remove-explicit-lowers")
    p.add_line_with_feature("  integer :: mixed(2,-1:1)\n", "mixed(2,-1:1)", "mixed(2,3)",
                            "feature-remove-second-dimension-lower")
    p.add("  checks=0\n")
    p.add_input_line("  upper_only=41\n", "41", "42", "input-upper-only-payload")
    p.add_input_line("  explicit2d=52\n", "52", "53", "input-explicit2d-payload")
    p.add_input_line("  mixed=63\n", "63", "64", "input-mixed-payload")
    p.guard_equal("upper-only-rank", "rank(upper_only)", 1, 2, category="rank")
    p.guard_any("upper-only-lower", "lbound(upper_only)", "[1]", "[-2]", category="lower")
    p.guard_any("upper-only-upper", "ubound(upper_only)", "[4]", "[1]", category="upper")
    p.guard_any("upper-only-shape", "shape(upper_only)", "[4]", "[3]", category="shape")
    p.guard_equal("upper-only-size", "size(upper_only)", 4, 5, category="size")
    p.guard_equal("upper-only-values", "count(upper_only == 41)", 4, 3)
    p.guard_equal("explicit2d-rank", "rank(explicit2d)", 2, 1, category="rank")
    p.guard_any("explicit2d-lower", "lbound(explicit2d)", "[-2,4]", "[1,1]", category="lower")
    p.guard_any("explicit2d-upper", "ubound(explicit2d)", "[0,5]", "[3,2]", category="upper")
    p.guard_any("explicit2d-shape", "shape(explicit2d)", "[3,2]", "[2,3]", category="shape")
    p.guard_equal("explicit2d-size", "size(explicit2d)", 6, 5, category="size")
    p.guard_equal("explicit2d-values", "count(explicit2d == 52)", 6, 5)
    p.guard_equal("mixed-rank", "rank(mixed)", 2, 1, category="rank")
    p.guard_any("mixed-lower", "lbound(mixed)", "[1,-1]", "[1,1]", category="lower")
    p.guard_any("mixed-upper", "ubound(mixed)", "[2,1]", "[2,3]", category="upper")
    p.guard_any("mixed-shape", "shape(mixed)", "[2,3]", "[3,2]", category="shape")
    p.guard_equal("mixed-size", "size(mixed)", 6, 5, category="size")
    p.guard_equal("mixed-values", "count(mixed == 63)", 6, 5)
    p.finish()
    return p


def range_bounds_program():
    p = Program("range_bounds")
    start_program(p)
    p.add_line_with_feature("  integer :: positive_range(2:4)\n", "positive_range(2:4)", "positive_range(3)",
                            "feature-remove-positive-explicit-lower")
    p.add_line_with_feature("  integer :: negative_range(-2:0)\n", "negative_range(-2:0)", "negative_range(3)",
                            "feature-remove-negative-and-zero-bounds")
    p.add_line_with_feature("  integer :: zero_singleton(0:0)\n", "zero_singleton(0:0)", "zero_singleton(1:1)",
                            "feature-zero-bound-to-positive-singleton")
    p.add("  checks=0\n")
    p.add_input_line("  positive_range=68\n", "68", "69", "input-positive-payload")
    p.add_input_line("  negative_range=74\n", "74", "75", "input-negative-payload")
    p.add_input_line("  zero_singleton=85\n", "85", "86", "input-zero-payload")
    p.guard_any("positive-lower", "lbound(positive_range)", "[2]", "[1]", category="lower")
    p.guard_any("positive-upper", "ubound(positive_range)", "[4]", "[3]", category="upper")
    p.guard_any("positive-shape", "shape(positive_range)", "[3]", "[2]", category="shape")
    p.guard_equal("positive-size", "size(positive_range)", 3, 4, category="size")
    p.guard_equal("positive-lower-endpoint", "positive_range(lbound(positive_range,1))", 68, 69)
    p.guard_equal("positive-upper-endpoint", "positive_range(ubound(positive_range,1))", 68, 69)
    p.guard_any("negative-lower", "lbound(negative_range)", "[-2]", "[1]", category="lower")
    p.guard_any("negative-upper", "ubound(negative_range)", "[0]", "[3]", category="upper")
    p.guard_any("negative-shape", "shape(negative_range)", "[3]", "[2]", category="shape")
    p.guard_equal("negative-size", "size(negative_range)", 3, 4, category="size")
    p.guard_equal("negative-lower-endpoint", "negative_range(lbound(negative_range,1))", 74, 75)
    p.guard_equal("negative-upper-endpoint", "negative_range(ubound(negative_range,1))", 74, 75)
    p.guard_any("zero-lower", "lbound(zero_singleton)", "[0]", "[1]", category="lower")
    p.guard_any("zero-upper", "ubound(zero_singleton)", "[0]", "[1]", category="upper")
    p.guard_any("zero-shape", "shape(zero_singleton)", "[1]", "[0]", category="shape")
    p.guard_equal("zero-size", "size(zero_singleton)", 1, 0, category="size")
    p.guard_equal("zero-value", "zero_singleton(lbound(zero_singleton,1))", 85, 86)
    p.finish()
    return p


def empty_ranges_program():
    p = Program("empty_ranges")
    start_program(p)
    p.add_line_with_feature("  integer :: empty1(5:3)\n", "empty1(5:3)", "empty1(5:5)",
                            "feature-empty-one-dimensional-to-singleton")
    p.add_line_with_feature("  integer :: empty2(5:3,-2:1)\n", "empty2(5:3,-2:1)", "empty2(5:5,-2:1)",
                            "feature-mixed-zero-extent-to-nonempty")
    p.add("  integer :: reached\n  checks=0\n")
    p.add_input_line("  reached=917\n", "917", "918", "input-path-sentinel")
    p.guard_equal("empty1-rank", "rank(empty1)", 1, 2, category="rank")
    p.guard_any("empty1-lower", "lbound(empty1)", "[1]", "[5]", category="lower")
    p.guard_any("empty1-upper", "ubound(empty1)", "[0]", "[5]", category="upper")
    p.guard_any("empty1-shape", "shape(empty1)", "[0]", "[1]", category="shape")
    p.guard_equal("empty1-size", "size(empty1)", 0, 1, category="size")
    p.guard_equal("empty2-rank", "rank(empty2)", 2, 1, category="rank")
    p.guard_any("empty2-lower", "lbound(empty2)", "[1,-2]", "[5,-2]", category="lower")
    p.guard_any("empty2-upper", "ubound(empty2)", "[0,1]", "[5,1]", category="upper")
    p.guard_any("empty2-shape", "shape(empty2)", "[0,4]", "[1,4]", category="shape")
    p.guard_equal("empty2-size", "size(empty2)", 0, 4, category="size")
    p.guard_equal("path-sentinel", "reached", 917, 918, category="path")
    p.finish()
    return p


PROGRAMS = {
    "scalar_bounds": scalar_bounds_program,
    "range_bounds": range_bounds_program,
    "empty_ranges": empty_ranges_program,
}


def source_specs():
    specs = {}
    for variant in VARIANTS:
        p = PROGRAMS[variant]()
        raw = p.text.encode("ascii")
        probes = []
        omissions = []
        for guard in p.guards:
            start, end = guard["span"]
            if raw[start:end].decode("ascii") != guard["expected"]:
                raise ValueError(f"guard span lost parent binding: {variant} {guard['id']}")
            probes.append(dict(guard))
            if guard["kind"] == "guard" and guard.get("counter"):
                start, end = guard["block_span"]
                omissions.append(dict(
                    id="omit-observation-" + guard["id"], guard_id="check-total", kind="guard",
                    category="omission", expected=p.text[start:end], replacement="", span=[start, end],
                    line=p.text[:start].count("\n") + 1, mutation="whole-observation-omission",
                    failure_token=f"ESH:{variant}:check-total"))
        completion = p.guards[-1]
        omissions.append(dict(
            id="omit-completion", guard_id=completion["id"], kind="output", category="omission",
            expected=p.text[completion["block_span"][0]:completion["block_span"][1]], replacement="",
            span=completion["block_span"], line=p.text[:completion["block_span"][0]].count("\n") + 1,
            mutation="completion-statement-omission", failure_token=""))
        for mutation in p.input_mutations + p.feature_mutations:
            start, end = mutation["span"]
            if raw[start:end].decode("ascii") != mutation["expected"]:
                raise ValueError(f"mutation span lost parent binding: {variant} {mutation['id']}")
        name = identifier(variant)
        specs[name] = dict(
            id=name, variant=variant, rule=p.rule, facets=p.facets, evidence="effect", standard="f2023",
            phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[variant],
            guards=p.guards, probes=probes, omissions=omissions, input_mutations=p.input_mutations,
            feature_mutations=p.feature_mutations, observations=p.observations,
            expected_counts=dict(checks=len(p.observations)))
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent input no longer matches its fingerprint")
    start, end = mutation["span"]
    if raw[start:end].decode("ascii") != mutation["expected"]:
        raise ValueError("the mutation span does not bind the complete parent")
    return raw[:start] + mutation["replacement"].encode("ascii") + raw[end:]


def all_mutations(spec):
    return spec["probes"] + spec["omissions"] + spec["input_mutations"] + spec["feature_mutations"]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("explicit_shape_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect",
            standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned explicit-shape paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue, specs=None):
    if specs is None:
        _, specs = build_corpus()
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        requirement = by_rule[rule]
        covered = {facet for spec in specs.values() if spec["rule"] == rule for facet in spec["facets"]}
        if covered != set(facets):
            raise ValueError("case partition differs from the authorized explicit-shape facets")
        for facet in covered:
            if facet not in requirement["facets"]:
                raise ValueError("unknown represented explicit-shape facet")
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - covered:
            raise ValueError("unselected explicit-shape source plans were not preserved")
        requirement["oracle"] = owned_paragraph(requirement["oracle"], ORACLE_PREFIXES[rule], ORACLES[rule])
        requirement["oracle_limitation"] = owned_paragraph(
            requirement["oracle_limitation"], LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return result


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tools"))
    import generate_explicit_bound_capture_fixtures as bound_capture

    text = bound_capture.render_view(catalogue, root)
    detail = (
        "## Scalar explicit-shape runtime effects\n\n"
        "Three complete run/effect/f2023 fixtures cover eight selected scalar-list facets "
        "without changing the existing explicit-bound capture fixtures. The scalar-bounds "
        "case observes `upper_only(4)`, `explicit2d(-2:0,4:5)` and `mixed(2,-1:1)` with "
        "independent LBOUND/UBOUND/SHAPE/SIZE and nonzero whole-array payload checks. "
        "The range case observes positive, negative and zero bounds, including actual "
        "endpoint reads through LBOUND/UBOUND-derived subscripts. The empty-range case "
        "observes normalized whole-array inquiries for `empty1(5:3)` and "
        "`empty2(5:3,-2:1)` plus a nonzero path sentinel, with no element access.\n\n"
        "Feature substitutions are same-rank, conforming declarations: they supply a "
        "nonunit lower bound for the upper-only case, remove explicit lower bounds from "
        "same-shape nonempty arrays, and turn empty ranges into nonempty ranges. Guard, "
        "omission and input-sentinel mutations cover every observation and completion "
        "literal. S8.5.8.2-002 is fully represented here; S8.5.8.2-004 still leaves "
        "`inquiry-normalization-source` pending. Vector bounds, C831 diagnostics or "
        "contexts, dummy sequence association, function results and p5 entry-capture "
        "semantics remain with their existing pending plans or owner packets.\n")
    if SUMMARY_BEGIN in text or SUMMARY_END in text:
        if text.count(SUMMARY_BEGIN) != 1 or text.count(SUMMARY_END) != 1:
            raise ValueError("the explicit-shape scalar summary boundary changed")
        before, rest = text.split(SUMMARY_BEGIN)
        _, after = rest.split(SUMMARY_END)
        return before + SUMMARY_BEGIN + "\n\n" + detail + "\n" + SUMMARY_END + after
    marker = "<!-- BEGIN EXPLICIT BOUND CAPTURE -->"
    if marker in text:
        before, after = text.split(marker, 1)
        return before.rstrip() + "\n\n" + SUMMARY_BEGIN + "\n\n" + detail + "\n" + SUMMARY_END + "\n\n" + marker + after
    return text.rstrip() + "\n\n" + SUMMARY_BEGIN + "\n\n" + detail + "\n" + SUMMARY_END + "\n"


def generate(root=ROOT, check=False, sync_catalogue=False):
    files, specs = build_corpus(root)
    catalogue_path = Path(root) / CATALOGUE
    view_path = Path(root) / VIEW
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, root)
    actual = {path for path in (Path(root) / "tests/fixtures").glob("explicit_shape_*/*") if path.is_file()}
    if check:
        stale = [str(path.relative_to(root)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(root)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if view_path.read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale explicit-shape scalar subset: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the explicit-shape scalar corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            view_path.write_text(view)
    return files, specs


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    if "gfortran" in name or "flang" in name:
        return [compiler, f"-std={std}", str(source), "-o", str(output)]
    return [compiler, f"--std={std}", str(source), "-o", str(output)]


def run_source(source_bytes, compiler, std):
    with tempfile.TemporaryDirectory(prefix="explicit_shape_mutation_") as tmp:
        work = Path(tmp)
        source = work / "source.f90"
        output = work / "program"
        source.write_bytes(source_bytes)
        compile_run = subprocess.run(
            compiler_command(compiler, std, source, output), cwd=work, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if compile_run.returncode != 0:
            return dict(phase="compile", returncode=compile_run.returncode,
                        stdout=compile_run.stdout, stderr=compile_run.stderr)
        executed = subprocess.run([str(output)], cwd=work, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=30)
        return dict(phase="run", returncode=executed.returncode,
                    stdout=executed.stdout, stderr=executed.stderr)


def mutation_check(compiler, std, root=ROOT):
    _, specs = build_corpus(root)
    total = 0
    for spec in specs.values():
        parent = run_source(spec["source"].encode("ascii"), compiler, std)
        if parent["phase"] != "run" or parent["returncode"] != 0 or parent["stdout"] != spec["completion"] or parent["stderr"] != "":
            raise SystemExit(f"parent failed for {spec['id']}: {parent}")
        for mutation in all_mutations(spec):
            total += 1
            result = run_source(mutated_source(spec, mutation), compiler, std)
            if result["phase"] != "run":
                raise SystemExit(f"nonconforming mutant failed to compile: {spec['id']} {mutation['id']}: {result}")
            survived = result["returncode"] == 0 and result["stdout"] == spec["completion"] and result["stderr"] == ""
            if survived:
                raise SystemExit(f"mutation survived: {spec['id']} {mutation['id']}")
    print(f"Mutation check failed all {total} explicit-shape scalar mutants with {Path(compiler).name} {std}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler or not args.std:
            parser.error("--mutation-check requires --compiler and --std")
        mutation_check(args.compiler, args.std)
        return
    generate(ROOT, check=args.check, sync_catalogue=args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} three explicit-shape scalar run/effect programs and eight facets.")


if __name__ == "__main__":
    main()
