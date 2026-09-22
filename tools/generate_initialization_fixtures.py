#!/usr/bin/env python3
"""Runtime fixtures for Fortran 2023 subclause 8.4 initialization."""

import argparse
import copy
import json
from pathlib import Path
import re
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, probe_verdict, sha, wrong_oracle_source


ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.4"
CATALOGUE = "doc/catalogues/initialization_8_4.json"
VIEW = "doc/fortran_2023_8_4.md"
SUMMARY_BEGIN = "<!-- BEGIN INITIALIZATION FIXTURES -->"
SUMMARY_END = "<!-- END INITIALIZATION FIXTURES -->"

VARIANTS = {
    "scalar_integer_logical": ("S8.4-001", "scalar-integer-and-logical"),
    "integer_kind_conversion": ("S8.4-001", "integer-kind-conversion"),
    "character_length_conversion": ("S8.4-001", "character-length-conversion"),
    "scalar_array_expansion": ("S8.4-001", "scalar-array-expansion"),
    "array_values": ("S8.4-001", "array-values"),
    "derived_explicit_override": ("S8.4-001", "derived-explicit-override"),
    "saved_scalar_target": ("S8.4-004", "saved-scalar-target"),
    "subprogram_retention": ("S8.4-005", "subprogram-retention"),
    "block_retention": ("S8.4-005", "block-retention"),
    "data_part_retention": ("S8.4-005", "data-part-retention"),
}
FACETS_BY_RULE = {}
for rule, facet in VARIANTS.values():
    FACETS_BY_RULE.setdefault(rule, []).append(facet)
FACETS_BY_RULE = {rule: tuple(facets) for rule, facets in FACETS_BY_RULE.items()}
REMAINING_PENDING = {
    "S8.4-001": {"enum-and-enumeration-values", "numeric-representation-source-use"},
    "S8.4-004": {
        "null-scalar", "null-array", "saved-array-and-element-targets",
        "deferred-character-target", "data-versus-procedure-source-use",
    },
    "S8.4-005": {
        "saved-pointer-live-target", "allocated-component-retention",
        "common-and-implicit-save-source-use", "default-versus-explicit-source-use",
    },
}
COMPLETIONS = {name: "INITIALIZATION " + name.upper().replace("_", " ") + " OK\n" for name in VARIANTS}
ORACLE_PREFIXES = {
    "S8.4-001": "S8.4-001 declaration-initializer runtime fixtures: ",
    "S8.4-004": "S8.4-004 pointer target-initialization runtime fixture: ",
    "S8.4-005": "S8.4-005 implied-SAVE initialization runtime fixtures: ",
}
LIMIT_PREFIXES = {
    "S8.4-001": "S8.4-001 declaration-initializer fixture boundaries: ",
    "S8.4-004": "S8.4-004 pointer target-initialization fixture boundaries: ",
    "S8.4-005": "S8.4-005 implied-SAVE fixture boundaries: ",
}
ORACLES = {
    "S8.4-001": ORACLE_PREFIXES["S8.4-001"] + (
        "six complete run/effect/f2023 programs observe declaration initializers before any executable "
        "assignment to the initialized variables. The scalar case checks INTEGER -31417 and a .TRUE. "
        "LOGICAL branch; the pending .FALSE. subcase from the original plan is deliberately not used as "
        "an asserted initializer sentinel. The integer-kind case uses SELECTED_INT_KIND(18) and checks "
        "default-to-selected -31417 plus selected-to-default 2719, never a numeric KIND-code oracle. The "
        "character case checks LEN explicitly while observing truncation of 'Zq7R' to LEN 2 as 'Zq' and "
        "padding of 'Bx' to LEN 5 with three blanks; the load-bearing nonblank source characters reject a "
        "zero/blank-fill implementation. The scalar-array case uses INTEGER a(-3:-1)=-24681 and "
        "b(5:6,-2:0)=13579, checking LBOUND/UBOUND and every element, with rank-two extents 2 and 3. "
        "The array-value case uses v(4:6)=[2,3,5], checking nonunit bounds and all elements. The derived "
        "case declares a component default -111 and an object explicitly initialized by sample(2719), then "
        "observes 2719 so default initialization alone cannot pass. Expected values are finite literals "
        "hand-derived from 8.4 p1 and intrinsic-assignment conversion; no compiler consensus, storage layout, "
        "TRANSFER or address oracle is used. Wrong-oracle, input-literal and initializer-removal mutations "
        "bind complete-parent byte spans."
    ),
    "S8.4-004": ORACLE_PREFIXES["S8.4-004"] + (
        "one complete run/effect/f2023 program initializes an INTEGER POINTER to a saved module TARGET "
        "whose declaration value is -22231. It first requires ASSOCIATED(p,target_value), then reads -22231, "
        "changes the target to -22230 and reads -22230 through the pointer. This distinguishes association "
        "from a one-time value copy without TRANSFER, LOC, C_LOC or address comparison. The target values are "
        "distinct nonzero sentinels; the initializer-removal mutation is a sensitivity check on the nonconforming "
        "mutant and is not used as a portable oracle for undefined pointer status."
    ),
    "S8.4-005": ORACLE_PREFIXES["S8.4-005"] + (
        "three complete run/effect/f2023 programs execute the same initialized entity more than once. The "
        "subprogram case has local INTEGER kept=-31417, returning -31417 on the first call and -31416 after "
        "the first call increments it. The BLOCK case executes one textual BLOCK twice and observes -27182 "
        "then the retained -27181. The DATA-part case initializes only a(-2) to -12345 by DATA in a local "
        "array a(-2:-1), defines a(-1)=2468 before any read, and on the second call observes retained "
        "-12344/2468. Each case uses exact visit counts and independent caller snapshots so a reinitializing "
        "implementation, a single-call program or an endpoint-only check cannot pass. The array DATA case checks "
        "nonunit bounds and makes clear that the uninitialized part is first defined before observation."
    ),
}
LIMITATIONS = {
    "S8.4-001": LIMIT_PREFIXES["S8.4-001"] + (
        "only scalar-integer-and-logical, integer-kind-conversion, character-length-conversion, "
        "scalar-array-expansion, array-values and derived-explicit-override are represented. The length-zero "
        "character subcase from the original plan is not represented because deleting its initializer leaves no "
        "load-bearing character value to observe. The scalar logical coverage uses .TRUE. only; no case asserts an initialized .FALSE. value because that would be a vacuous "
        "default-fill sentinel under this packet's non-vacuity rule. enum-and-enumeration-values and "
        "numeric-representation-source-use remain pending. The fixtures do not cover real/complex approximation, "
        "BOZ representation, nondefault character kinds, ALLOCATABLE entities, PARAMETER receivers, pointer "
        "initialization, default component initialization as an owner, diagnostics or repeated initialization."
    ),
    "S8.4-004": LIMIT_PREFIXES["S8.4-004"] + (
        "only saved-scalar-target is represented. Null pointer initializers, array and element targets, "
        "deferred-length character targets and DATA/procedure-pointer source-use remain pending because this packet "
        "does not create a portable no-initializer counterfactual for undefined association status. The valid parent "
        "queries association only while the pointer is declaration-initialized and defined. It does not claim target "
        "lifetime extension beyond the saved module target or any allocation/storage-address behavior."
    ),
    "S8.4-005": LIMIT_PREFIXES["S8.4-005"] + (
        "only subprogram-retention, block-retention and data-part-retention are represented. saved-pointer-live-target, "
        "allocated-component-retention, common-and-implicit-save-source-use and default-versus-explicit-source-use "
        "remain pending. The fixtures do not read an undefined variable part, infer physical static storage, test "
        "COMMON behavior, component default reinitialization, explicit SAVE confirmation, finalization, recursion, "
        "coarrays or thread interactions. Initializer-removal mutants are negative sensitivity probes rather than "
        "conforming programs with a portable value."
    ),
}
SENTINELS = {
    "scalar_integer_logical": ["-31417", ".TRUE."],
    "integer_kind_conversion": ["-31417", "2719"],
    "character_length_conversion": ["'Zq7R'", "'Bx'"],
    "scalar_array_expansion": ["-24681", "13579"],
    "array_values": ["2", "3", "5"],
    "derived_explicit_override": ["2719", "component default -111 as the rejected alternative"],
    "saved_scalar_target": ["-22231", "-22230"],
    "subprogram_retention": ["-31417", "-31416"],
    "block_retention": ["-27182", "-27181"],
    "data_part_retention": ["-12345", "-12344", "2468"],
}
IGNORED_INITIALIZATION = {
    "scalar_integer_logical": "typical zero/default-fill would produce integer 0 and logical false; the integer guard rejects it",
    "integer_kind_conversion": "typical zero-fill would produce 0 for both initialized variables; both guards reject it",
    "character_length_conversion": "typical blank-fill would produce blanks; nonblank 'Zq'/'Bx' guards reject it",
    "scalar_array_expansion": "typical zero-fill would produce zero elements; every sentinel element guard rejects it",
    "array_values": "typical zero-fill would produce 0/0/0; all value guards reject it",
    "derived_explicit_override": "default initialization alone would produce component -111; the 2719 guard rejects it",
    "saved_scalar_target": "without pointer initialization p has undefined association status; the mutation must fail and is not a portable value oracle",
    "subprogram_retention": "typical zero/default-fill would return 0 instead of -31417 on the first call; the first snapshot rejects it",
    "block_retention": "typical zero/default-fill would capture 0 instead of -27182 on the first block execution; the first snapshot rejects it",
    "data_part_retention": "without DATA, a(-2) would not be initially defined and typical zero-fill gives 0; the first snapshot rejects it",
}


def identifier(variant):
    if variant not in VARIANTS:
        raise ValueError("unknown initialization variant")
    rule, _ = VARIANTS[variant]
    return rule.replace(".", "_").replace("-", "_") + "_valid__initialization_" + variant


class Program:
    def __init__(self, variant):
        self.variant = variant
        self.rule, self.facet = VARIANTS[variant]
        self.text = ""
        self.guards = []
        self.probes = []
        self.input_mutations = []
        self.initializer_removals = []
        self.observations = []

    def add(self, text):
        start = len(self.text)
        self.text += text
        return [start, len(self.text)]

    def replace_site(self, id_, expected, replacement, *, mutation, collection, category="input"):
        matches = [m for m in re.finditer(re.escape(expected), self.text)]
        if len(matches) != 1:
            raise ValueError(f"{self.variant}: {expected!r} has {len(matches)} matches")
        start, end = matches[0].span()
        collection.append(dict(
            id=id_, guard_id=id_, kind=category, category=category, span=[start, end],
            expected=expected, replacement=replacement, line=self.text[:start].count("\n") + 1,
            mutation=mutation, failure_stdout=""))

    def remove_site(self, id_, expected, replacement=""):
        self.replace_site(id_, expected, replacement, mutation="initializer-removal",
                          collection=self.initializer_removals, category="initializer-removal")

    def input_site(self, id_, expected, replacement):
        self.replace_site(id_, expected, replacement, mutation="input-literal",
                          collection=self.input_mutations, category="input")

    def guard(self, name, expression, expected, replacement=None, *, category="value", counter="checks", indent="  "):
        expected = str(expected)
        replacement = str(int(expected) + 1) if replacement is None and re.fullmatch(r"-?\d+", expected) else str(replacement)
        block_start = len(self.text)
        prefix = indent + f"if ({expression} /= "
        start = block_start + len(prefix)
        token = f"INIT:{self.variant}:{name}"
        guard = dict(
            id=name, guard_id=name, kind="guard", category=category, expression=expression,
            expected=expected, replacement=replacement, span=[start, start + len(expected)],
            line=self.text.count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="guard-literal-expectation")
        self.add(prefix + expected + ") then\n" + indent + f"  write(*,'(a)') '{token}'\n"
                 + indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")
            self.observations.append(guard)
        guard["block_span"] = [block_start, len(self.text)]
        self.guards.append(guard)
        self.probes.append(dict(guard))
        return guard

    def guard_logical_true(self, name, expression, *, counter="checks", indent="  "):
        block_start = len(self.text)
        prefix = indent + "if (.not. "
        start = block_start + len(prefix)
        token = f"INIT:{self.variant}:{name}"
        self.add(prefix + expression + ") then\n" + indent + f"  write(*,'(a)') '{token}'\n"
                 + indent + "  error stop\n" + indent + "end if\n")
        if counter:
            self.add(indent + f"{counter}={counter}+1\n")
        guard = dict(
            id=name, guard_id=name, kind="guard", category="logical", expression=expression,
            expected=expression, replacement=f"({expression} .eqv. .false.)", span=[start, start + len(expression)],
            line=self.text[:start].count("\n") + 1, counter=counter, activation=None,
            failure_token=token, failure_stdout=token + "\n", mutation="logical-branch-expectation",
            block_span=[block_start, len(self.text)])
        self.guards.append(guard)
        self.probes.append(dict(guard))
        self.observations.append(guard)
        return guard

    def finish(self):
        total = self.guard("check-total", "checks", len(self.observations), len(self.observations) + 1,
                           category="completion", counter=None)
        literal = COMPLETIONS[self.variant].rstrip("\n")
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        completion = dict(
            id="completion-output", guard_id="completion-output", kind="output", category="completion",
            expected=literal, replacement=literal.replace(" OK", " BAD"), span=[start, start + len(literal)],
            line=self.text.count("\n") + 1, counter=None, activation=None, mutation="completion-literal",
            failure_stdout="")
        completion["block_span"] = self.add(prefix + literal + "'\n")
        self.guards.append(completion)
        self.probes.append(dict(completion))
        return total


def program(variant):
    p = Program(variant)
    p.add(f"! rule: {p.rule}\n! covers: {p.facet}\n")
    p.add("! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.\n")
    p.add(f"program initialization_{variant}_effect\n  implicit none\n")
    if variant == "scalar_integer_logical":
        p.add("  integer :: i = -31417\n  logical :: flag = .true.\n  integer :: checks\n  checks=0\n")
        p.input_site("integer-sentinel", "-31417", "-31418")
        p.input_site("logical-sentinel", ".true.", ".false.")
        p.remove_site("remove-integer-initializer", " = -31417")
        p.remove_site("remove-logical-initializer", " = .true.")
        p.guard("integer-initial-value", "i", -31417, -31418)
        p.guard_logical_true("logical-true-initial-value", "flag")
    elif variant == "integer_kind_conversion":
        p.add("  integer, parameter :: wide_k = selected_int_kind(18)\n")
        p.add("  integer(kind=wide_k), parameter :: wide_source = 2719_wide_k\n")
        p.add("  integer(kind=wide_k) :: wide = -31417\n  integer :: narrow = wide_source\n")
        p.add("  integer :: checks\n  checks=0\n")
        p.input_site("wide-source-parameter", "2719_wide_k", "2720_wide_k")
        p.input_site("wide-initializer", "-31417", "-31418")
        p.remove_site("remove-wide-initializer", " = -31417")
        p.remove_site("remove-narrow-initializer", " = wide_source")
        p.guard("default-to-selected", "wide", -31417, -31418)
        p.guard("selected-to-default", "narrow", 2719, 2720)
    elif variant == "character_length_conversion":
        p.add("  character(len=2) :: trunc = 'Zq7R'\n")
        p.add("  character(len=5) :: padded = 'Bx'\n  integer :: checks\n  checks=0\n")
        for name, expected, repl in (("trunc-source", "'Zq7R'", "'Yq7R'"),
                                     ("pad-source", "'Bx'", "'Cx'")):
            p.input_site(name, expected, repl)
        for name, clause in (("remove-trunc-initializer", " = 'Zq7R'"),
                             ("remove-pad-initializer", " = 'Bx'")):
            p.remove_site(name, clause)
        p.guard("trunc-len", "len(trunc)", 2, 3, category="length")
        p.guard("trunc-value", "trunc(1:2)", "'Zq'", "'Yq'", category="value")
        p.guard("padded-len", "len(padded)", 5, 4, category="length")
        p.guard("padded-prefix", "padded(1:2)", "'Bx'", "'Cx'", category="value")
        p.guard("padded-tail-blank-1", "padded(3:3)", "' '", "'Z'", category="padding")
        p.guard("padded-tail-blank-2", "padded(4:4)", "' '", "'Z'", category="padding")
        p.guard("padded-tail-blank-3", "padded(5:5)", "' '", "'Z'", category="padding")
    elif variant == "scalar_array_expansion":
        p.add("  integer :: a(-3:-1) = -24681\n  integer :: b(5:6,-2:0) = 13579\n")
        p.add("  integer :: checks\n  checks=0\n")
        p.input_site("rank-one-scalar", "-24681", "-24682")
        p.input_site("rank-two-scalar", "13579", "13580")
        p.remove_site("remove-rank-one-initializer", " = -24681")
        p.remove_site("remove-rank-two-initializer", " = 13579")
        for name, expr, expected in (("a-lbound", "lbound(a,1)", -3), ("a-ubound", "ubound(a,1)", -1),
                                     ("b-lbound-1", "lbound(b,1)", 5), ("b-ubound-1", "ubound(b,1)", 6),
                                     ("b-lbound-2", "lbound(b,2)", -2), ("b-ubound-2", "ubound(b,2)", 0)):
            p.guard(name, expr, expected, expected + 1, category="bounds")
        for i in range(-3, 0):
            p.guard(f"a-{i}", f"a({i})", -24681, -24682)
        for i in range(5, 7):
            for j in range(-2, 1):
                p.guard(f"b-{i}-{j}", f"b({i},{j})", 13579, 13580)
    elif variant == "array_values":
        p.add("  integer :: v(4:6) = [2,3,5]\n  integer :: checks\n  checks=0\n")
        p.input_site("constructor-first", "[2,3,5]", "[7,3,5]")
        p.remove_site("remove-array-constructor", " = [2,3,5]")
        for name, expr, expected in (("v-lbound", "lbound(v,1)", 4), ("v-ubound", "ubound(v,1)", 6),
                                     ("v4", "v(4)", 2), ("v5", "v(5)", 3), ("v6", "v(6)", 5)):
            p.guard(name, expr, expected, expected + 1, category="bounds" if "bound" in name else "value")
    elif variant == "derived_explicit_override":
        p.add("  type :: sample\n    integer :: component = -111\n  end type sample\n")
        p.add("  type(sample) :: obj = sample(2719)\n  integer :: checks\n  checks=0\n")
        p.input_site("constructor-component", "2719", "2720")
        p.remove_site("remove-object-constructor", " = sample(2719)")
        p.guard("component-explicit-over-default", "obj%component", 2719, -111)
    elif variant == "saved_scalar_target":
        p.add("  integer, target, save :: target_value = -22231\n")
        p.add("  integer, pointer :: p => target_value\n  integer :: checks\n  checks=0\n")
        p.input_site("target-initial-value", "-22231", "-22232")
        p.remove_site("remove-pointer-initializer", " => target_value")
        p.guard_logical_true("associated-with-target", "associated(p, target_value)")
        p.guard("initial-target-value", "p", -22231, -22232)
        p.add("  target_value = -22230\n")
        p.input_site("target-update-value", "target_value = -22230", "target_value = -22229")
        p.guard("updated-target-visible-through-pointer", "p", -22230, -22229)
    elif variant == "subprogram_retention":
        p.add("  integer :: first, second, checks\n  checks=0\n  call visit(first)\n  call visit(second)\n")
        p.guard("first-snapshot", "first", -31417, -31418)
        p.guard("second-snapshot", "second", -31416, -31415)
        p.finish()
        p.add("contains\n  subroutine visit(out)\n    implicit none\n    integer, intent(out) :: out\n")
        p.add("    integer :: kept = -31417\n    out = kept\n    kept = kept + 1\n  end subroutine visit\n")
        p.input_site("retained-initializer", "integer :: kept = -31417", "integer :: kept = -31418")
        p.remove_site("remove-retained-initializer", "    integer :: kept = -31417", "    integer :: kept")
        p.add("end program initialization_subprogram_retention_effect\n")
        return finalize_spec(p)
    elif variant == "block_retention":
        p.add("  integer :: pass, first, second, checks\n  checks=0\n  first=-9\n  second=-9\n")
        p.add("  do pass=1,2\n    block\n      integer :: kept = -27182\n")
        p.add("      if (pass == 1) then\n        first = kept\n        kept = -27181\n      else\n")
        p.add("        second = kept\n        kept = -27180\n      end if\n    end block\n  end do\n")
        p.input_site("block-initializer", "-27182", "-27183")
        p.input_site("block-retained-update", "-27181", "-27180")
        p.remove_site("remove-block-initializer", " = -27182")
        p.guard("first-block-execution", "first", -27182, -27183)
        p.guard("second-block-execution", "second", -27181, -27180)
    elif variant == "data_part_retention":
        p.add("  integer :: first_a, first_b, second_a, second_b, checks\n  checks=0\n")
        p.add("  call visit(1, first_a, first_b)\n  call visit(2, second_a, second_b)\n")
        for name, expr, expected, repl in (("first-initialized-part", "first_a", -12345, -12346),
                                           ("first-defined-other-part", "first_b", 2468, 2469),
                                           ("second-retained-initialized-part", "second_a", -12344, -12343),
                                           ("second-retained-other-part", "second_b", 2468, 2469)):
            p.guard(name, expr, expected, repl)
        p.finish()
        p.add("contains\n  subroutine visit(pass, obs_a, obs_b)\n    implicit none\n")
        p.add("    integer, intent(in) :: pass\n    integer, intent(out) :: obs_a, obs_b\n")
        p.add("    integer :: a(-2:-1)\n    data a(-2) /-12345/\n")
        p.add("    if (lbound(a,1) /= -2) error stop\n    if (ubound(a,1) /= -1) error stop\n")
        p.add("    if (pass == 1) then\n      a(-1) = 2468\n      obs_a = a(-2)\n      obs_b = a(-1)\n")
        p.add("      a(-2) = -12344\n    else\n      obs_a = a(-2)\n      obs_b = a(-1)\n    end if\n")
        p.add("  end subroutine visit\n")
        p.input_site("data-initializer", "data a(-2) /-12345/", "data a(-2) /-12346/")
        p.input_site("defined-other-part", "a(-1) = 2468", "a(-1) = 2469")
        p.input_site("retained-update", "a(-2) = -12344", "a(-2) = -12343")
        p.remove_site("remove-data-statement", "    data a(-2) /-12345/\n")
        p.add("end program initialization_data_part_retention_effect\n")
        return finalize_spec(p)
    else:
        raise ValueError("unknown variant")
    p.finish()
    p.add(f"end program initialization_{variant}_effect\n")
    return finalize_spec(p)


def finalize_spec(p):
    raw = p.text.encode("ascii")
    all_mutations = p.probes + p.input_mutations + p.initializer_removals
    hashes = set()
    for probe in all_mutations:
        start, end = probe["span"]
        if raw[start:end].decode("ascii") != probe["expected"]:
            raise ValueError(f"{p.variant}: mutation {probe['id']} lost its complete-parent span")
        mutant = mutated_source(dict(source=p.text, source_sha256=sha(raw)), probe)
        digest = sha(mutant)
        if digest in hashes:
            raise ValueError(f"{p.variant}: duplicate mutation source {probe['id']}")
        hashes.add(digest)
    return dict(
        id=identifier(p.variant), variant=p.variant, rule=p.rule, facets=[p.facet], evidence="effect",
        standard="f2023", phase="run", source=p.text, source_sha256=sha(raw), completion=COMPLETIONS[p.variant],
        guards=p.guards, probes=p.probes, input_mutations=p.input_mutations,
        initializer_removals=p.initializer_removals, observations=p.observations,
        sentinels=SENTINELS[p.variant], ignored_initialization=IGNORED_INITIALIZATION[p.variant],
        expected_counts=dict(checks=len(p.observations)))


def source_specs():
    return {identifier(variant): program(variant) for variant in VARIANTS}


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = Path(root) / "tests/fixtures" / ("initialization_" + spec["variant"])
        manifest = dict(
            schema_version=1, id=name, rule=spec["rule"], facets=spec["facets"], evidence="effect", standard="f2023",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def mutated_source(spec, probe):
    if probe.get("spans"):
        raw = spec["source"].encode("ascii")
        if sha(raw) != spec["source_sha256"]:
            raise ValueError("the complete parent input no longer matches its fingerprint")
        result = raw
        for start, end in reversed(probe["spans"]):
            result = result[:start] + probe["replacement"].encode("ascii") + result[end:]
        return result
    return wrong_oracle_source(spec, probe)


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in FACETS_BY_RULE.items():
        owner = by_rule[rule]
        if owner["category"] != "effect" or not set(facets) <= set(owner["facets"]):
            raise ValueError("selected initialization facets changed")
        for facet in facets:
            owner["pending"].pop(facet, None)
        if set(owner.get("pending", {})) != REMAINING_PENDING[rule]:
            raise ValueError("unexpected remaining pending facets for " + rule)
        if rule == "S8.4-001":
            owner["oracle_limitation"] = owner.get("oracle_limitation", "").replace(
                "All facets remain pending.", "Unimplemented facets remain pending.")
        if rule == "S8.4-005":
            owner["oracle_limitation"] = owner.get("oracle_limitation", "").replace(
                "All plans remain pending and genuine runs.",
                "Unimplemented plans remain pending; selected facets below are genuine runs.")
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the initialization generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "**INDEPENDENTLY SOURCE-REVIEWED; ALL FIXTURES PENDING.** All facets remain\npending, with no new fixtures, executable models, compiler probes, policies\nor fixture approvals.",
        "**INDEPENDENTLY SOURCE-REVIEWED; SELECTED FIXTURES ADDED.** Ten effect facets now have\nruntime fixtures; remaining facets stay pending, with no fixture approvals.")
    before = before.replace(
        "Five append-only local S requirements have thirty-five facets, all\npending.",
        "Five append-only local S requirements have thirty-five facets; ten effect facets\nnow have executable fixtures and the rest remain pending.")
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Initialization runtime observations\n\n"
        "Ten complete run/effect/f2023 programs cover six declaration-initializer facets, one "
        "pointer target-initialization facet and three implied-SAVE facets. Every asserted initialized "
        "value uses a distinctive nonzero, nonblank or .TRUE. sentinel; no fixture expects 0, 0.0, "
        ".FALSE. or a blank string as the initialized value. Character fixtures assert LEN explicitly, "
        "and array fixtures use nonunit lower bounds; rank-two arrays use distinct extents and explicit "
        "LBOUND/UBOUND checks.\n\n"
        "Each source has exact completion output plus wrong-oracle, input-literal and initializer-removal "
        "mutation plans. The pointer and SAVE initializer-removal mutants are sensitivity probes, not "
        "portable conforming programs with defined no-initializer values. `enum-and-enumeration-values`, "
        "`numeric-representation-source-use`, null/array/deferred-character pointer cases and the remaining "
        "SAVE/source-use facets remain pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the initialization summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return (before + begin + "\n\n"
            + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after)


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
            raise ValueError("stale initialization fixture family: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} initialization cases, "
          f"{sum(len(row['facets']) for row in specs.values())} facets, "
          f"{sum(len(row['probes']) for row in specs.values())} wrong-oracle, "
          f"{sum(len(row['input_mutations']) for row in specs.values())} input and "
          f"{sum(len(row['initializer_removals']) for row in specs.values())} initializer-removal plans.")


if __name__ == "__main__":
    main()
