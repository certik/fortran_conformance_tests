#!/usr/bin/env python3
"""Generate bounded EQUIVALENCE statement storage-association fixtures."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.10.1.1"
CATALOGUE = "doc/catalogues/equivalence_statement_8_10_1_1.json"
VIEW = "doc/fortran_2023_8_10_1_1.md"
PREFIX = "equivalence_statement_"
SUMMARY_BEGIN = "<!-- BEGIN EQUIVALENCE STATEMENT FIXTURES -->"
SUMMARY_END = "<!-- END EQUIVALENCE STATEMENT FIXTURES -->"

CHECKS = """module equivalence_statement_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, check_character, finish_checks
contains
subroutine check_integer(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
  write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_INTEGER', label, actual, expected
  error stop 10
end if
checked = checked + 1
end subroutine check_integer
subroutine check_logical(label, actual, expected)
character(*), intent(in) :: label
logical, intent(in) :: actual, expected
if (actual .neqv. expected) then
  write(*,'(a,1x,a,1x,l1,1x,l1)') 'CHECK_LOGICAL', label, actual, expected
  error stop 11
end if
checked = checked + 1
end subroutine check_logical
subroutine check_character(label, actual, expected)
character(*), intent(in) :: label, actual, expected
if (len(actual) /= len(expected)) then
  write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_CHARACTER_LEN', label, len(actual), len(expected)
  error stop 12
end if
if (actual /= expected) then
  write(*,'(a,1x,a,1x,a,1x,a)') 'CHECK_CHARACTER', label, actual, expected
  error stop 13
end if
checked = checked + 1
end subroutine check_character
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
  write(*,'(a,1x,i0,1x,i0)') 'CHECK_COUNT', checked, expected
  error stop 14
end if
end subroutine finish_checks
end module equivalence_statement_checks
"""

SELECTED = {
    "R873": ["one-set", "multiple-sets"],
    "R874": ["two-object-set", "three-object-set"],
    "R875": ["scalar-variable-name", "whole-array-name", "array-element", "scalar-substring", "array-element-substring"],
    "C8113": ["named-constant-arithmetic", "omitted-endpoints"],
    "C8114": ["numeric-sequence-trigger"],
    "C8115": ["default-character-pair"],
    "C8117": ["nondefault-complex-same-kind"],
    "C8120": ["one-character-substring"],
    "S8.10.1.1-001": ["scalar-array-properties", "character-length-properties"],
}

ORACLE_PREFIX = "Finite EQUIVALENCE runtime fixture family: "
LIMIT_PREFIX = "Finite EQUIVALENCE runtime fixture boundaries: "
ORACLE = ORACLE_PREFIX + (
    "eleven complete single-image programs observe storage association caused by EQUIVALENCE using only same-type/same-kind "
    "default INTEGER, default CHARACTER, numeric-sequence, and "
    "COMPLEX(KIND(0.0D0)) objects. Each program initializes non-default sentinels, verifies the positive pre-state, "
    "performs the defining write through the associated object, checks the independently derived alias value, and prints "
    "one exact completion line with empty runtime stderr. Array-element and substring cases use in-bounds constant offsets; "
    "mutations delete the EQUIVALENCE statement or change the object/offset while remaining conforming, so survivors would "
    "show that the selected rule facet was not load-bearing."
)
LIMITATION = LIMIT_PREFIX + (
    "only the selected positive/runtime facets are discharged. No cross-type bit-pattern interpretation, mathematical "
    "conversion, LOGICAL truth representation, padding layout, TRANSFER result, diagnostic vocabulary, COMMON interaction, "
    "use-associated name, TARGET/PROTECTED exclusion, pointer/allocatable/dummy/function-result exclusion, coarray, BIND, "
    "zero-length substring, unsupported kind fallback, suite-wide count, review-state claim, or negative-control adjudication "
    "is made. Differing intrinsic-type admissions under C8114 are not value-tested here; all value effects are same-kind "
    "numeric sequence or character storage effects derived from 8.10.1.1 and 19.5.3."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__" + PREFIX + variant


def fsource(text):
    body = textwrap.dedent(text).strip() + "\n"
    if max(map(len, body.splitlines()), default=0) > 132:
        raise ValueError("source line longer than 132 columns")
    return body


def indent(text, spaces=2):
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines()) + "\n"


class Program:
    def __init__(self, rule, variant, facets, title, declarations, equivalences, body, derivation, mutations):
        self.rule = rule
        self.variant = variant
        self.facets = list(facets)
        self.title = title
        self.declarations = textwrap.dedent(declarations).strip("\n")
        self.equivalences = [line.strip() for line in equivalences]
        self.body = textwrap.dedent(body).strip("\n")
        self.derivation = derivation
        self.mutations = list(mutations)
        self.id = identifier(rule, variant)
        self.checks = self.body.count("call check_")
        self.stdout = f"EQUIVALENCE STATEMENT {variant.upper()} OK\n"
        for mutation in self.mutations:
            mutation.setdefault("category", "feature")

    def source(self):
        lines = [
            CHECKS.rstrip("\n"),
            "program p",
            "use equivalence_statement_checks, only: check_integer, check_logical, check_character, finish_checks",
            "implicit none",
        ]
        if self.declarations:
            lines.append(self.declarations)
        lines.extend(self.equivalences)
        if self.body:
            lines.append(self.body)
        lines.append(f"call finish_checks({self.checks})")
        lines.append(f"write(*,'(a)') 'EQUIVALENCE STATEMENT {self.variant.upper()} OK'")
        lines.append("end program p")
        return fsource("\n".join(lines))

    def mutated_source(self, mutation):
        source = self.source()
        if mutation["kind"] == "remove-equivalence":
            for expected in self.equivalences:
                needle = expected + "\n"
                if source.count(needle) != 1:
                    raise ValueError(f"{self.id}: equivalence removal is not unique: {expected}")
                source = source.replace(needle, "", 1)
            return source
        if mutation["kind"] == "replace":
            expected = mutation["expected"]
            replacement = mutation["replacement"]
            if source.count(expected) != 1:
                raise ValueError(f"{self.id}: mutation token is not unique: {expected}")
            return source.replace(expected, replacement, 1)
        raise ValueError("unknown mutation kind")


def remove_all():
    return dict(id="remove-equivalence", kind="remove-equivalence", mutation="feature-removal",
                description="delete every EQUIVALENCE statement; sentinels remain defined")


def repl(mid, expected, replacement, desc):
    return dict(id=mid, kind="replace", expected=expected, replacement=replacement,
                mutation="feature-substitution", description=desc)


def cases():
    return [
        Program(
            "R873", "one_set", ["one-set"],
            "One EQUIVALENCE set associates integer array elements with an offset.",
            """
            integer :: a(4), b(3)
            """,
            ["equivalence (a(3), b(1))"],
            """
            a = -101
            b = -202
            call check_integer('one-set-pre', a(4), -202)
            b(2) = 17
            call check_integer('one-set-alias', a(4), 17)
            """,
            "R873 permits one nonempty set-list; 19.5.3.3 aligns b(2) with a(4) when a(3) and b(1) share a numeric unit.",
            [remove_all(), repl("offset-a3-to-a2", "equivalence (a(3), b(1))", "equivalence (a(2), b(1))",
                                "change the integer-array offset so b(2) reaches a(3), not a(4)")]),
        Program(
            "R873", "multiple_sets", ["multiple-sets"],
            "Two comma-separated EQUIVALENCE sets are independent and both observed.",
            """
            integer :: a(4), b(3), c(3), d(4)
            """,
            ["equivalence (a(3), b(1)), (c(1), d(2))"],
            """
            a = -111
            b = -222
            c = -333
            d = -444
            call check_integer('multiple-first-pre', a(4), -222)
            call check_integer('multiple-second-pre', c(2), -444)
            b(2) = 23
            d(3) = 29
            call check_integer('multiple-first-alias', a(4), 23)
            call check_integer('multiple-second-alias', c(2), 29)
            """,
            "R873's set-list admits a comma-separated second set; each set independently causes same-kind integer storage association.",
            [remove_all(), repl("first-offset-a3-to-a2", "equivalence (a(3), b(1)), (c(1), d(2))",
                                "equivalence (a(2), b(1)), (c(1), d(2))",
                                "change the first set offset while leaving the second set conforming")]),
        Program(
            "R874", "two_object_set", ["two-object-set"],
            "The syntactic minimum two-object set is observed through integer aliasing.",
            """
            integer :: a(4), b(3)
            """,
            ["equivalence (a(3), b(1))"],
            """
            a = -121
            b = -232
            call check_integer('two-object-pre', a(4), -232)
            b(2) = 31
            call check_integer('two-object-alias', a(4), 31)
            """,
            "R874 requires a first object, comma, and nonempty object list; the two-object set aligns a(3) with b(1).",
            [remove_all(), repl("offset-a3-to-a2", "equivalence (a(3), b(1))", "equivalence (a(2), b(1))",
                                "change the two-object offset so the observed element no longer aliases")]),
        Program(
            "R874", "three_object_set", ["three-object-set"],
            "A three-object set aligns all listed integer scalars.",
            """
            integer :: a, b, c, spare
            """,
            ["equivalence (a, b, c)"],
            """
            a = -131
            b = -242
            c = -353
            spare = -464
            call check_integer('three-object-pre-a', a, -353)
            call check_integer('three-object-pre-c', c, -353)
            b = 37
            call check_integer('three-object-a-alias', a, 37)
            call check_integer('three-object-c-alias', c, 37)
            """,
            "R874's equivalence-object-list can contain a second tail object; a, b, and c share one numeric unit.",
            [remove_all(), repl("middle-object-substitution", "equivalence (a, b, c)",
                                "equivalence (a, spare, c)",
                                "replace the middle object so assignment to b is no longer associated")]),
        Program(
            "R875", "object_forms", SELECTED["R875"],
            "Variable-name, whole-array-name, array-element and substring object forms are all observed.",
            """
            integer :: s, t, spare
            integer :: wa(3), wb(3)
            integer :: ea(4), eb(3)
            character(4) :: cs
            character(2) :: ds
            character(3) :: ca(2)
            character(1) :: da
            """,
            [
                "equivalence (s, t)",
                "equivalence (wa, wb)",
                "equivalence (ea(3), eb(1))",
                "equivalence (cs(2:3), ds)",
                "equivalence (ca(2)(2:2), da)",
            ],
            """
            s = -141
            t = -252
            spare = -363
            wa = -474
            wb = -585
            ea = -696
            eb = -707
            cs = '####'
            ds = '@@'
            ca = '###'
            da = '@'
            call check_integer('scalar-pre', s, -252)
            call check_integer('whole-array-pre', wa(2), -585)
            call check_integer('array-element-pre', ea(4), -707)
            call check_character('scalar-substring-pre', cs(3:3), '@')
            call check_character('array-element-substring-pre', ca(2)(2:2), '@')
            t = 41
            wb(2) = 43
            eb(2) = 47
            ds(2:2) = 'Q'
            da = 'R'
            call check_integer('scalar-alias', s, 41)
            call check_integer('whole-array-alias', wa(2), 43)
            call check_integer('array-element-alias', ea(4), 47)
            call check_character('scalar-substring-alias', cs(3:3), 'Q')
            call check_character('array-element-substring-alias', ca(2)(2:2), 'R')
            """,
            "R875's three alternatives are exercised with defined same-type values; whole arrays enter through the variable-name alternative.",
            [remove_all(),
             repl("scalar-peer", "equivalence (s, t)", "equivalence (s, spare)",
                  "replace the scalar peer so assigning t no longer defines s"),
             repl("whole-array-offset", "equivalence (wa, wb)", "equivalence (wa(2), wb(1))",
                  "offset the whole-array association so wb(2) reaches wa(3), not wa(2)"),
             repl("array-element-offset", "equivalence (ea(3), eb(1))", "equivalence (ea(2), eb(1))",
                  "change the array-element offset"),
             repl("scalar-substring-offset", "equivalence (cs(2:3), ds)", "equivalence (cs(1:2), ds)",
                  "change the scalar substring offset"),
             repl("array-element-substring-offset", "equivalence (ca(2)(2:2), da)", "equivalence (ca(1)(2:2), da)",
                  "change the array-element substring base element")]),
        Program(
            "C8113", "constant_expressions", SELECTED["C8113"],
            "Named-constant arithmetic and omitted substring endpoints are used as constant expressions.",
            """
            integer, parameter :: k = 2
            integer :: a(5), b(3)
            character(3) :: left_start, left_end
            character(4) :: left_both
            character(2) :: peer_start, peer_end
            character(4) :: peer_both
            """,
            [
                "equivalence (a(k+1), b(1))",
                "equivalence (left_start(:2), peer_start)",
                "equivalence (left_end(2:), peer_end)",
                "equivalence (left_both(:), peer_both)",
            ],
            """
            a = -151
            b = -262
            left_start = '###'
            left_end = '###'
            left_both = '####'
            peer_start = '@@'
            peer_end = '@@'
            peer_both = '@@@@'
            call check_integer('named-constant-pre', a(k+2), -262)
            call check_character('omitted-start-pre', left_start(2:2), '@')
            call check_character('omitted-end-pre', left_end(3:3), '@')
            call check_character('omitted-both-pre', left_both(1:1), '@')
            b(2) = 53
            peer_start(2:2) = 'M'
            peer_end(2:2) = 'N'
            peer_both(1:1) = 'P'
            call check_integer('named-constant-alias', a(k+2), 53)
            call check_character('omitted-start-alias', left_start(2:2), 'M')
            call check_character('omitted-end-alias', left_end(3:3), 'N')
            call check_character('omitted-both-alias', left_both(1:1), 'P')
            """,
            "C8113 permits integer constant expressions, including prior named-constant arithmetic and omitted substring endpoints from 9.4.1p3.",
            [remove_all(),
             repl("integer-offset", "equivalence (a(k+1), b(1))", "equivalence (a(k), b(1))",
                  "change the constant-expression subscript offset"),
             repl("omitted-start-offset", "equivalence (left_start(:2), peer_start)",
                  "equivalence (left_start(2:3), peer_start)", "supply a different conforming start"),
             repl("omitted-end-offset", "equivalence (left_end(2:), peer_end)",
                  "equivalence (left_end(1:2), peer_end)", "supply a different conforming end"),
             repl("omitted-both-offset", "equivalence (left_both(:), peer_both)",
                  "equivalence (left_both(2:), peer_both)", "change the full-substring offset")]),
        Program(
            "C8114", "numeric_sequence", ["numeric-sequence-trigger"],
            "A numeric SEQUENCE object and default INTEGER array share numeric storage units.",
            """
            type :: pair
              sequence
              integer :: first
              integer :: second
            end type pair
            type(pair) :: box
            integer :: a(2)
            """,
            ["equivalence (box, a)"],
            """
            box%first = -161
            box%second = -272
            a = -383
            call check_integer('numeric-sequence-pre', box%second, -383)
            a(2) = 59
            call check_integer('numeric-sequence-alias', box%second, 59)
            """,
            "C8114 includes numeric SEQUENCE types in the default numeric family; pair%second and a(2) are same-kind integer units.",
            [remove_all(), repl("numeric-sequence-offset", "equivalence (box, a)", "equivalence (box, a(2))",
                                "align the sequence object with a(2), moving the observed second component beyond a")]),
        Program(
            "C8115", "character_family", SELECTED["C8115"],
            "Default CHARACTER objects of unequal lengths share character storage units.",
            """
            character(4) :: c
            character(2) :: d
            """,
            ["equivalence (c, d)"],
            """
            c = '####'
            d = '@@'
            call check_integer('default-character-c-len', len(c), 4)
            call check_integer('default-character-d-len', len(d), 2)
            call check_character('default-character-pre', c(2:2), '@')
            d(2:2) = 'F'
            call check_character('default-character-alias', c(2:2), 'F')
            """,
            "C8115 permits default CHARACTER members throughout the set; d(2:2) and c(2:2) are the same character unit.",
            [remove_all(),
             repl("default-character-offset", "equivalence (c, d)", "equivalence (c(2:3), d)",
                  "offset the default-character association")]),
        Program(
            "C8117", "nondefault_complex", ["nondefault-complex-same-kind"],
            "Two nondefault COMPLEX objects with the same kind are equivalenced and observed.",
            """
            integer, parameter :: dk = kind(0.0d0)
            complex(kind=dk) :: a(4), b(3)
            """,
            ["equivalence (a(3), b(1))"],
            """
            a = cmplx(-1.0d0, -2.0d0, kind=dk)
            b = cmplx(-3.0d0, -4.0d0, kind=dk)
            call check_logical('nondefault-complex-kind', kind(a) == dk, .true.)
            call check_logical('nondefault-complex-pre', a(4) == cmplx(-3.0d0, -4.0d0, kind=dk), .true.)
            b(2) = cmplx(67.0d0, 71.0d0, kind=dk)
            call check_logical('nondefault-complex-alias', a(4) == cmplx(67.0d0, 71.0d0, kind=dk), .true.)
            """,
            "C8117 requires matching intrinsic type and KIND for nondefault COMPLEX; exact integer-valued components avoid rounding ambiguity.",
            [remove_all(), repl("complex-offset", "equivalence (a(3), b(1))", "equivalence (a(2), b(1))",
                                "change the nondefault complex array offset")]),
        Program(
            "C8120", "one_character_substring", ["one-character-substring"],
            "A nonzero one-character substring participates in character storage association.",
            """
            character(3) :: c
            character(1) :: d
            """,
            ["equivalence (c(2:2), d)"],
            """
            c = '###'
            d = '@'
            call check_character('one-character-pre', c(2:2), '@')
            d = 'Z'
            call check_character('one-character-alias', c(2:2), 'Z')
            """,
            "C8120 excludes only zero-length substrings; c(2:2) has length one and shares one character unit with d.",
            [remove_all(), repl("substring-offset", "equivalence (c(2:2), d)", "equivalence (c(1:1), d)",
                                "change the one-character substring offset")]),
        Program(
            "S8.10.1.1-001", "retained_properties", SELECTED["S8.10.1.1-001"],
            "Scalar/array rank and CHARACTER lengths are retained while storage is shared.",
            """
            integer :: scalar
            integer :: array(4)
            character(4) :: text
            character(2) :: part
            """,
            [
                "equivalence (scalar, array(2))",
                "equivalence (text(2:3), part)",
            ],
            """
            scalar = -181
            array = -292
            text = '####'
            part = '@@'
            call check_integer('scalar-rank', rank(scalar), 0)
            call check_integer('array-rank', rank(array), 1)
            call check_integer('array-size', size(array), 4)
            call check_integer('text-len', len(text), 4)
            call check_integer('part-len', len(part), 2)
            call check_integer('scalar-array-pre', scalar, -292)
            call check_character('character-length-pre', text(2:3), '@@')
            array(2) = 73
            part = 'UV'
            call check_integer('scalar-array-alias', scalar, 73)
            call check_character('character-length-alias', text(2:3), 'UV')
            """,
            "8.10.1.1p2 says scalar and array properties are retained; same-type aliasing observes value effects while RANK/SIZE/LEN stay declared.",
            [remove_all(),
             repl("scalar-array-offset", "equivalence (scalar, array(2))", "equivalence (scalar, array(1))",
                  "change the scalar/array alignment"),
             repl("character-length-offset", "equivalence (text(2:3), part)", "equivalence (text(1:2), part)",
                  "change the character substring alignment")]),
    ]


def build_corpus(root=ROOT):
    root = Path(root)
    files, specs = {}, {}
    for spec in cases():
        source = spec.source().encode("ascii")
        folder = f"tests/fixtures/{PREFIX}{spec.variant}"
        manifest = dict(
            schema_version=1, id=spec.id, rule=spec.rule, facets=spec.facets,
            standard="f2023", evidence="effect", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0,
                        stdout=[spec.stdout], stderr=[""]))
        source_path = root / folder / "source.f90"
        fixture_path = root / folder / "fixture.json"
        if source_path in files or fixture_path in files:
            raise ValueError("duplicate generated fixture path")
        files[source_path] = source
        files[fixture_path] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
        specs[spec.id] = dict(
            id=spec.id, rule=spec.rule, variant=spec.variant, facets=spec.facets, title=spec.title,
            source=source.decode("ascii"), source_sha256=sha(source), stdout=spec.stdout,
            fixture=folder + "/fixture.json", derivation=spec.derivation,
            equivalences=list(spec.equivalences), mutations=copy.deepcopy(spec.mutations),
            mutation_sources={m["id"]: spec.mutated_source(m) for m in spec.mutations},
            expected_check_count=spec.checks)
    return files, specs


def selected_facets():
    return {rule: set(facets) for rule, facets in SELECTED.items()}


def owned_paragraph(current, prefix, replacement):
    parts = current.split("\n\n") if current else []
    kept = [p for p in parts if not p.startswith(prefix)]
    kept.append(replacement)
    return "\n\n".join(kept)


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    wanted = selected_facets()
    seen = set()
    for row in updated["requirements"]:
        facets = wanted.get(row["id"])
        if not facets:
            continue
        seen.add(row["id"])
        if not facets <= set(row["facets"]):
            raise ValueError(f"selected facets missing from {row['id']}")
        for facet in facets:
            row["pending"].pop(facet, None)
        row["oracle"] = owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX, ORACLE)
        row["oracle_limitation"] = owned_paragraph(row.get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    if seen != set(wanted):
        raise ValueError("selected requirement IDs missing from catalogue")
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated section boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (SUMMARY_BEGIN + "\n"
               "## Finite EQUIVALENCE runtime fixture family\n\n"
               "This packet adds eleven single-image runtime fixtures for exactly seventeen selected\n"
               "facets of 8.10.1.1. The programs use only same-kind INTEGER/COMPLEX,\n"
               "default CHARACTER, and numeric-SEQUENCE value observations. Each fixture starts from non-default\n"
               "sentinels, checks the pre-state, performs the aliasing write, checks the\n"
               "derived alias value, and has conforming removal/offset mutants that fail on\n"
               "both the frozen LFortran target and the gfortran reference.\n\n"
               "No differing-type value reinterpretation, processor-dependent truth bits,\n"
               "padding layout, TRANSFER image, diagnostic text, COMMON effect, or review\n"
               "state is asserted. All unselected facets remain pending in the catalogue.\n"
               + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    rendered = render_view(updated, root)
    if check:
        stale = []
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                stale.append(path.relative_to(root).as_posix())
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != rendered:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale equivalence statement fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(rendered)
    return specs


def compiler_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    if "gfortran" in name:
        return [str(compiler), f"-std={std}", str(source), "-o", str(output)]
    return [str(compiler), f"--std={std}", str(source), "-o", str(output)]


def run_process(command, cwd):
    return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)


def mutation_check(root=ROOT, compiler=None, std=None, keep_work=False):
    if compiler is None or std is None:
        raise ValueError("mutation_check requires compiler and std")
    root = Path(root)
    _, specs = build_corpus(root)
    workspace = root / ".equivalence_statement_mutations" / (sha((str(compiler) + std).encode())[:12])
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    report = []
    failures = []
    try:
        index = 0
        for spec in specs.values():
            for mutation in spec["mutations"]:
                index += 1
                case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
                case_dir.mkdir(parents=True)
                source = case_dir / "source.f90"
                source.write_text(spec["mutation_sources"][mutation["id"]])
                exe = case_dir / "program"
                compile_result = run_process(compiler_command(compiler, std, source, exe), case_dir)
                row = dict(case=spec["id"], variant=spec["variant"], mutation=mutation["id"],
                           category=mutation["category"], compile_status=compile_result.returncode)
                if compile_result.returncode != 0 or not exe.is_file():
                    failures.append(f"{spec['id']}:{mutation['id']} did not compile\n{compile_result.stdout}{compile_result.stderr}")
                    row["run_status"] = None
                    report.append(row)
                    continue
                run_result = run_process([str(exe)], case_dir)
                row.update(run_status=run_result.returncode, stdout=run_result.stdout, stderr=run_result.stderr)
                if run_result.returncode == 0:
                    failures.append(f"{spec['id']}:{mutation['id']} survived\n{run_result.stdout}{run_result.stderr}")
                report.append(row)
        if failures:
            raise RuntimeError("\n".join(failures))
        return report
    finally:
        if not keep_work and workspace.exists():
            shutil.rmtree(workspace)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    modes = sum(map(bool, (args.check, args.sync_catalogue, args.mutation_check)))
    if modes > 1:
        parser.error("--check, --sync-catalogue and --mutation-check are separate operations")
    if args.mutation_check:
        if not args.compiler or not args.std:
            parser.error("--mutation-check requires --compiler and --std")
        report = mutation_check(args.root, args.compiler, args.std, args.keep_work)
        print(f"Mutation-checked {len(report)} EQUIVALENCE statement mutants; all compiled and failed.")
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    facets = sum(len(spec["facets"]) for spec in specs.values())
    mutations = sum(len(spec["mutations"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} EQUIVALENCE statement fixtures, "
          f"{facets} facets and {mutations} conforming mutants.")


if __name__ == "__main__":
    main()
