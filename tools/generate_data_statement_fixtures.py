#!/usr/bin/env python3
"""Finite DATA statement syntax controls and runtime initialization effects."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph, sha, wrong_oracle_source

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.6.7"
CATALOGUE = "doc/catalogues/data_statement_8_6_7.json"
VIEW = "doc/fortran_2023_8_6_7.md"
SUMMARY_BEGIN = "<!-- BEGIN DATA STATEMENT FIXTURES -->"
SUMMARY_END = "<!-- END DATA STATEMENT FIXTURES -->"

SELECTED = {
    "R840": ("single-set", "sets-with-comma", "sets-without-comma"),
    "R841": ("matched-lists",),
    "R846": ("unrepeated-value", "repeated-value"),
    "R847": ("literal-and-named-repeat",),
    "C886": ("positive-repeat", "zero-repeat"),
    "R848": ("scalar-intrinsic-constants", "signed-integer", "signed-real", "null-init", "initial-data-target"),
    "S8.6.7-004": (
        "repeat-and-default-one", "zero-length-scalar-position", "character-length-conversion",
        "integer-boz-qualified-value", "triplet-section-order", "vector-section-order",
        "component-section-order", "negative-step-order"),
    "S8.6.7-006": ("initial-association-owner",),
    "S8.6.7-008": ("integer-domain",),
}

ORACLE_TEXT = {
    "R840": (
        "DATA statement fixture family: one complete positive-control program reaches one set, comma-separated "
        "sets and adjacent sets without the optional comma. Five distinct nonzero INTEGER objects are checked after "
        "normal execution, so syntax admission is tied to the actual DATA statements and not to declaration "
        "initialization or default zero storage."),
    "R841": (
        "DATA statement fixture family: one complete positive-control program reaches a two-object and two-value "
        "DATA set between slashes and observes the two nonzero initial values. This establishes only the selected "
        "matched-list control; empty-list and slash-omission diagnostics remain separate."),
    "R846": (
        "DATA statement fixture family: one complete positive-control program initializes a three-element INTEGER "
        "array from one unprefixed value and one explicit repeat. The checks distinguish a default repeat of one "
        "from a repeated contribution without claiming the missing-asterisk or zero-repeat syntax negatives."),
    "R847": (
        "DATA statement fixture family: one complete positive-control program uses both a literal repeat and a "
        "previously defined named INTEGER PARAMETER repeat on separate arrays, with all elements checked. No signed, "
        "noninteger, forward or expression repeat form is credited."),
    "C886": (
        "DATA statement fixture family: one complete positive-control program uses a positive named repeat and a "
        "zero repeat in the same matched DATA list. The zero repeat consumes no constant before a nonzero tail value, "
        "so the oracle distinguishes a zero contribution from an omitted DATA statement."),
    "R848": (
        "DATA statement fixture family: one complete positive-control program reaches scalar intrinsic constants "
        "(INTEGER, LOGICAL, CHARACTER, COMPLEX and a named constant), signed integer literals of both signs, a signed "
        "REAL literal, NULL() pointer initialization and an INTEGER initial data target. It observes values or defined "
        "association status only for these portable default-kind contexts."),
    "S8.6.7-004": (
        "DATA statement fixture family: five complete run/effect programs observe repeat/default-one correspondence, "
        "zero-length CHARACTER still consuming one value, same-kind CHARACTER padding/truncation with LEN guards, a "
        "qualified six-bit positive BOZ INTEGER value, triplet and vector array-section order, scalar component "
        "section order, and negative-step DATA implied-DO order. Each expected value is a nondefault literal "
        "independent of the DATA spelling, and the four order cases deliberately distinguish reversed or transposed "
        "expansion. The vector-subscript case uses a rank-one constant array constructor section-subscript permitted "
        "by R921/R925/C929 and constant under C879."),
    "S8.6.7-006": (
        "DATA statement fixture family: one complete positive-control program observes DATA NULL() producing a "
        "defined disassociated pointer and DATA initial-data-target producing association with a live saved TARGET. "
        "It does not claim allocation, target definition from association, procedure-pointer targets or incompatible "
        "parameter cases."),
    "S8.6.7-008": (
        "DATA statement fixture family: one complete positive-control program uses a BOZ literal with an INTEGER "
        "receiver and checks RADIX, BIT_SIZE and the independent decimal value 53. Noninteger receivers, high-bit "
        "interpretation and kind-width variation remain pending."),
}
LIMIT_TEXT = {
    rule: "DATA statement fixture family boundaries: only " + ", ".join(f"`{f}`" for f in facets)
          + " are represented by this generator. All other facets, diagnostics, source-use links, reviews and the "
            "existing DATA position effect fixtures remain independently managed. Generation grants no review or baseline update."
    for rule, facets in SELECTED.items()
}

CASES = [
    dict(
        id="R840_valid__data_statement_sets", directory="data_statement_r840_sets", rule="R840",
        facets=list(SELECTED["R840"]), evidence="positive-control",
        completion="DATA STATEMENT R840 SETS OK\n",
        derivation="R840 admits one DATA set and additional sets with or without the optional comma; all five initialized INTEGER objects are observed.",
        source="""program data_statement_r840_sets
  implicit none
  integer :: single, comma_left, comma_right, bare_left, bare_right
  data single /17/
  data comma_left /19/, comma_right /23/
  data bare_left /29/ bare_right /31/
  if (single /= 17) error stop 1
  if (comma_left /= 19) error stop 2
  if (comma_right /= 23) error stop 3
  if (bare_left /= 29) error stop 4
  if (bare_right /= 31) error stop 5
  write(*,'(a)') 'DATA STATEMENT R840 SETS OK'
end program data_statement_r840_sets
""",
        mutations=[
            ("sentinel-single-set", "  data single /17/\n", "  data single /18/\n"),
            ("change-comma-set-value", "comma_right /23/", "comma_right /24/"),
            ("change-no-comma-set-value", "bare_right /31/", "bare_right /32/"),
        ]),
    dict(
        id="R841_valid__data_statement_matched_lists", directory="data_statement_r841_matched_lists",
        rule="R841", facets=list(SELECTED["R841"]), evidence="positive-control",
        completion="DATA STATEMENT R841 MATCHED LISTS OK\n",
        derivation="R841's object list and value list are both present and matched; the two scalar correspondences are observed as 37 and 41.",
        source="""program data_statement_r841_matched_lists
  implicit none
  integer :: first, second
  data first, second /37, 41/
  if (first /= 37) error stop 1
  if (second /= 41) error stop 2
  write(*,'(a)') 'DATA STATEMENT R841 MATCHED LISTS OK'
end program data_statement_r841_matched_lists
""",
        mutations=[
            ("sentinel-matched-data", "  data first, second /37, 41/\n", "  data first, second /38, 42/\n"),
            ("change-second-value", "/37, 41/", "/37, 42/"),
        ]),
    dict(
        id="R846_valid__data_statement_repeats", directory="data_statement_r846_repeats", rule="R846",
        facets=list(SELECTED["R846"]), evidence="positive-control",
        completion="DATA STATEMENT R846 REPEATS OK\n",
        derivation="R846 permits an omitted repeat and an explicit repeat; p6 expands 43 once and 2*47 into two constants.",
        source="""program data_statement_r846_repeats
  implicit none
  integer :: a(3)
  data a /43, 2*47/
  if (a(1) /= 43) error stop 1
  if (a(2) /= 47) error stop 2
  if (a(3) /= 47) error stop 3
  write(*,'(a)') 'DATA STATEMENT R846 REPEATS OK'
end program data_statement_r846_repeats
""",
        mutations=[
            ("sentinel-repeat-data", "  data a /43, 2*47/\n", "  data a /44, 2*48/\n"),
            ("mutate-repeat-factor", "43, 2*47", "2*47, 43"),
            ("mutate-unrepeated-value", "/43,", "/44,"),
        ]),
    dict(
        id="R847_valid__data_statement_named_repeats", directory="data_statement_r847_named_repeats",
        rule="R847", facets=list(SELECTED["R847"]), evidence="positive-control",
        completion="DATA STATEMENT R847 NAMED REPEATS OK\n",
        derivation="R847 admits scalar integer literal and named-constant repeats; the named PARAMETER n is defined before DATA.",
        source="""program data_statement_r847_named_repeats
  implicit none
  integer, parameter :: n = 2
  integer :: literal(2), named(2)
  data literal /2*53/
  data named /n*59/
  if (literal(1) /= 53) error stop 1
  if (literal(2) /= 53) error stop 2
  if (named(1) /= 59) error stop 3
  if (named(2) /= 59) error stop 4
  write(*,'(a)') 'DATA STATEMENT R847 NAMED REPEATS OK'
end program data_statement_r847_named_repeats
""",
        mutations=[
            ("sentinel-named-repeat-data", "  data literal /2*53/\n  data named /n*59/\n",
             "  data literal /2*54/\n  data named /n*60/\n"),
            ("mutate-literal-repeat", "2*53", "1*53, 54"),
            ("mutate-named-repeat", "integer, parameter :: n = 2\n  integer :: literal(2), named(2)\n  data literal /2*53/\n  data named /n*59/", "integer, parameter :: n = 1\n  integer :: literal(2), named(2)\n  data literal /2*53/\n  data named /n*59, 60/"),
        ]),
    dict(
        id="C886_valid__data_statement_repeat_bounds", directory="data_statement_c886_repeat_bounds",
        rule="C886", facets=list(SELECTED["C886"]), evidence="positive-control",
        completion="DATA STATEMENT C886 REPEAT BOUNDS OK\n",
        derivation="C886 permits positive and zero repeats; n*61 contributes two constants and 0*999 contributes none before tail=67.",
        source="""program data_statement_c886_repeat_bounds
  implicit none
  integer, parameter :: n = 2
  integer :: repeated(2), tail
  data repeated, tail /n*61, 0*999, 67/
  if (repeated(1) /= 61) error stop 1
  if (repeated(2) /= 61) error stop 2
  if (tail /= 67) error stop 3
  write(*,'(a)') 'DATA STATEMENT C886 REPEAT BOUNDS OK'
end program data_statement_c886_repeat_bounds
""",
        mutations=[
            ("sentinel-repeat-bound-data", "  data repeated, tail /n*61, 0*999, 67/\n",
             "  data repeated, tail /n*62, 0*999, 68/\n"),
            ("mutate-positive-repeat", "integer, parameter :: n = 2\n  integer :: repeated(2), tail\n  data repeated, tail /n*61, 0*999, 67/", "integer, parameter :: n = 1\n  integer :: repeated(2), tail\n  data repeated, tail /n*61, 62, 0*999, 67/"),
            ("mutate-zero-repeat", "0*999, 67", "1*999"),
            ("mutate-tail-value", ", 67/", ", 68/"),
        ]),
    dict(
        id="R848_valid__data_statement_constants", directory="data_statement_r848_constants", rule="R848",
        facets=list(SELECTED["R848"]), evidence="positive-control",
        completion="DATA STATEMENT R848 CONSTANTS OK\n",
        derivation="R848 supplies scalar intrinsic constants, signed literals, NULL() and an initial data target; values and association status are observed.",
        source="""program data_statement_r848_constants
  implicit none
  integer, parameter :: named_constant = 73
  integer, target, save :: target_value
  integer :: scalar_integer, named_receiver, signed_negative, signed_positive
  real :: signed_real
  logical :: scalar_logical
  character(len=2) :: scalar_character
  complex :: scalar_complex
  integer, pointer :: null_pointer, target_pointer
  data scalar_integer, scalar_logical, scalar_character, scalar_complex, named_receiver &
       /71, .true., 'AB', (3.0,4.0), named_constant/
  data signed_negative, signed_positive, signed_real /-7, +11, -1.0/
  data target_value /79/
  data null_pointer /null()/
  data target_pointer /target_value/
  if (scalar_integer /= 71) error stop 1
  if (.not. scalar_logical) error stop 2
  if (len(scalar_character) /= 2) error stop 3
  if (scalar_character /= 'AB') error stop 4
  if (real(scalar_complex) /= 3.0) error stop 5
  if (aimag(scalar_complex) /= 4.0) error stop 6
  if (named_receiver /= 73) error stop 7
  if (signed_negative /= -7) error stop 8
  if (signed_positive /= 11) error stop 9
  if (signed_real /= -1.0) error stop 10
  if (associated(null_pointer)) error stop 11
  if (.not. associated(target_pointer, target_value)) error stop 12
  if (target_pointer /= 79) error stop 13
  write(*,'(a)') 'DATA STATEMENT R848 CONSTANTS OK'
end program data_statement_r848_constants
""",
        mutations=[
            ("sentinel-scalar-constant-data", "/71, .true., 'AB', (3.0,4.0), named_constant/",
             "/72, .false., 'CD', (5.0,6.0), 74/"),
            ("mutate-scalar-integer", "/71, .true.,", "/72, .true.,"),
            ("mutate-signed-integer", "/-7, +11, -1.0/", "/-8, +12, -1.0/"),
            ("mutate-signed-real", "-1.0/", "-2.0/"),
            ("mutate-null-init", "data null_pointer /null()/", "data null_pointer /target_value/"),
            ("mutate-initial-target", "data target_pointer /target_value/", "data target_pointer /null()/"),
        ]),
    dict(
        id="S8_6_7_004_valid__data_statement_runtime_effects",
        directory="data_statement_s004_runtime_effects", rule="S8.6.7-004",
        facets=["repeat-and-default-one", "zero-length-scalar-position",
                "character-length-conversion", "integer-boz-qualified-value"], evidence="effect",
        completion="DATA STATEMENT S004 RUNTIME EFFECTS OK\n",
        derivation="Paragraphs 5-11 expand repeats, zero-length CHARACTER objects, character conversion and a qualified BOZ INTEGER into positionwise initial values.",
        source="""program data_statement_s004_runtime_effects
  implicit none
  integer :: repeated(5), boz_value
  character(len=0) :: empty
  character(len=1) :: tail
  character(len=4) :: padded
  character(len=2) :: cut
  data repeated /2*11, 22, 2*33/
  data empty, tail /'discarded', 'Q'/
  data padded, cut /'AB', 'WXYZ'/
  data boz_value /b'110101'/
  if (repeated(1) /= 11) error stop 1
  if (repeated(2) /= 11) error stop 2
  if (repeated(3) /= 22) error stop 3
  if (repeated(4) /= 33) error stop 4
  if (repeated(5) /= 33) error stop 5
  if (len(empty) /= 0) error stop 6
  if (len(tail) /= 1) error stop 7
  if (tail /= 'Q') error stop 8
  if (len(padded) /= 4) error stop 9
  if (padded /= 'AB  ') error stop 10
  if (len(cut) /= 2) error stop 11
  if (cut /= 'WX') error stop 12
  if (radix(boz_value) /= 2) error stop 13
  if (bit_size(boz_value) < 6) error stop 14
  if (boz_value /= 53) error stop 15
  write(*,'(a)') 'DATA STATEMENT S004 RUNTIME EFFECTS OK'
end program data_statement_s004_runtime_effects
""",
        mutations=[
            ("sentinel-runtime-data", "  data repeated /2*11, 22, 2*33/\n",
             "  data repeated /2*12, 23, 2*34/\n"),
            ("mutate-repeat-factor", "2*11, 22, 2*33", "1*11, 12, 22, 2*33"),
            ("mutate-zero-length-position", "'discarded', 'Q'", "'Q', 'R'"),
            ("mutate-character-padding", "'AB', 'WXYZ'", "'AC', 'WXYZ'"),
            ("mutate-boz-value", "b'110101'", "b'110100'"),
        ]),
    dict(
        id="S8_6_7_004_valid__data_statement_triplet_section_order",
        directory="data_statement_s004_triplet_section_order", rule="S8.6.7-004",
        facets=["triplet-section-order"], evidence="effect",
        completion="DATA STATEMENT S004 TRIPLET SECTION ORDER OK\n",
        derivation="Paragraph p5 makes an array section equivalent to its elements in array element order; p8 maps 21,43,65 to a(2),a(4),a(6).",
        source="""program data_statement_s004_triplet_section_order
  implicit none
  integer :: a(6)
  data a(2:6:2) /21, 43, 65/
  if (a(2) /= 21) error stop 1
  if (a(4) /= 43) error stop 2
  if (a(6) /= 65) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 TRIPLET SECTION ORDER OK'
end program data_statement_s004_triplet_section_order
""",
        mutations=[
            ("sentinel-triplet-section", "/21, 43, 65/", "/22, 44, 66/"),
            ("reverse-triplet-values", "/21, 43, 65/", "/65, 43, 21/"),
        ]),
    dict(
        id="S8_6_7_004_valid__data_statement_vector_section_order",
        directory="data_statement_s004_vector_section_order", rule="S8.6.7-004",
        facets=["vector-section-order"], evidence="effect",
        completion="DATA STATEMENT S004 VECTOR SECTION ORDER OK\n",
        derivation="R921/R925/C929 permit a rank-one integer vector-subscript; C879 is met by the constant constructor [4,1,3], and p5/p8 map values in section element order.",
        source="""program data_statement_s004_vector_section_order
  implicit none
  integer :: a(4)
  data a([4,1,3]) /41, 11, 31/
  if (a(4) /= 41) error stop 1
  if (a(1) /= 11) error stop 2
  if (a(3) /= 31) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 VECTOR SECTION ORDER OK'
end program data_statement_s004_vector_section_order
""",
        mutations=[
            ("sentinel-vector-section", "/41, 11, 31/", "/42, 12, 32/"),
            ("rotate-vector-values", "/41, 11, 31/", "/11, 31, 41/"),
        ]),
    dict(
        id="S8_6_7_004_valid__data_statement_component_section_order",
        directory="data_statement_s004_component_section_order", rule="S8.6.7-004",
        facets=["component-section-order"], evidence="effect",
        completion="DATA STATEMENT S004 COMPONENT SECTION ORDER OK\n",
        derivation="Paragraph p5 expands an array section of scalar components in array element order; p8 maps 13,29,47 to cells(1:3)%value.",
        source="""program data_statement_s004_component_section_order
  implicit none
  type :: cell
    integer :: value
  end type cell
  type(cell) :: cells(3)
  data cells(:)%value /13, 29, 47/
  if (cells(1)%value /= 13) error stop 1
  if (cells(2)%value /= 29) error stop 2
  if (cells(3)%value /= 47) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 COMPONENT SECTION ORDER OK'
end program data_statement_s004_component_section_order
""",
        mutations=[
            ("sentinel-component-section", "/13, 29, 47/", "/14, 30, 48/"),
            ("reverse-component-values", "/13, 29, 47/", "/47, 29, 13/"),
        ]),
    dict(
        id="S8_6_7_004_valid__data_statement_negative_step_order",
        directory="data_statement_s004_negative_step_order", rule="S8.6.7-004",
        facets=["negative-step-order"], evidence="effect",
        completion="DATA STATEMENT S004 NEGATIVE STEP ORDER OK\n",
        derivation="Paragraph p5 expands a DATA implied-DO as the DO construct; the negative step visits i=3,2,1 and p8 maps 31,21,11 respectively.",
        source="""program data_statement_s004_negative_step_order
  implicit none
  integer :: a(3)
  integer :: i
  data (a(i), i=3,1,-1) /31, 21, 11/
  if (a(3) /= 31) error stop 1
  if (a(2) /= 21) error stop 2
  if (a(1) /= 11) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 NEGATIVE STEP ORDER OK'
end program data_statement_s004_negative_step_order
""",
        mutations=[
            ("sentinel-negative-step", "/31, 21, 11/", "/32, 22, 12/"),
            ("reverse-negative-step-values", "/31, 21, 11/", "/11, 21, 31/"),
        ]),
    dict(
        id="S8_6_7_006_valid__data_statement_pointer_init", directory="data_statement_s006_pointer_init",
        rule="S8.6.7-006", facets=list(SELECTED["S8.6.7-006"]), evidence="positive-control",
        completion="DATA STATEMENT S006 POINTER INIT OK\n",
        derivation="Paragraph 9 gives NULL() a disassociated initial status and a compatible initial data target an associated initial status.",
        source="""program data_statement_s006_pointer_init
  implicit none
  integer, target, save :: target_value, other_target
  integer, pointer :: null_pointer, target_pointer
  data target_value, other_target /83, 89/
  data null_pointer /null()/
  data target_pointer /target_value/
  if (target_value /= 83) error stop 1
  if (other_target /= 89) error stop 2
  if (associated(null_pointer)) error stop 3
  if (.not. associated(target_pointer, target_value)) error stop 4
  if (target_pointer /= 83) error stop 5
  write(*,'(a)') 'DATA STATEMENT S006 POINTER INIT OK'
end program data_statement_s006_pointer_init
""",
        mutations=[
            ("sentinel-pointer-target", "data target_pointer /target_value/", "data target_pointer /other_target/"),
            ("mutate-target-value", "data target_value, other_target /83, 89/", "data target_value, other_target /84, 89/"),
            ("mutate-null-pointer", "data null_pointer /null()/", "data null_pointer /target_value/"),
            ("mutate-target-pointer", "data target_pointer /target_value/", "data target_pointer /null()/"),
        ]),
    dict(
        id="S8_6_7_008_valid__data_statement_boz_domain", directory="data_statement_s008_boz_domain",
        rule="S8.6.7-008", facets=list(SELECTED["S8.6.7-008"]), evidence="positive-control",
        completion="DATA STATEMENT S008 BOZ DOMAIN OK\n",
        derivation="Paragraph 11 restricts a contributing BOZ DATA constant to an INTEGER receiver; the decimal value 53 is independently checked after radix/capacity guards.",
        source="""program data_statement_s008_boz_domain
  implicit none
  integer :: value
  data value /z'35'/
  if (radix(value) /= 2) error stop 1
  if (bit_size(value) < 6) error stop 2
  if (value /= 53) error stop 3
  write(*,'(a)') 'DATA STATEMENT S008 BOZ DOMAIN OK'
end program data_statement_s008_boz_domain
""",
        mutations=[
            ("sentinel-boz-data", "  data value /z'35'/\n", "  data value /z'34'/\n"),
            ("mutate-boz-domain-value", "z'35'", "z'34'"),
        ]),
]


def identifier(rule, variant):
    for case in CASES:
        if case["rule"] == rule and case["directory"].endswith(variant):
            return case["id"]
    raise ValueError("unknown DATA statement fixture variant")


def bind_mutations(spec):
    bound = []
    source = spec["source"]
    for mid, expected, replacement in spec["mutations"]:
        if source.count(expected) != 1:
            raise ValueError(f"mutation {mid} is not uniquely bound")
        start = source.index(expected)
        bound.append(dict(id=mid, span=[start, start + len(expected)], expected=expected,
                          replacement=replacement, line=source[:start].count("\n") + 1))
    return bound


def source_specs():
    specs = {}
    for raw in CASES:
        spec = copy.deepcopy(raw)
        spec["source_sha256"] = sha(spec["source"].encode("ascii"))
        spec["mutations"] = bind_mutations(spec)
        specs[spec["id"]] = spec
    return specs


def build_corpus(root=ROOT):
    root = Path(root)
    files = {}
    specs = source_specs()
    for spec in specs.values():
        directory = root / "tests/fixtures" / spec["directory"]
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0,
                        stdout=spec["completion"], stderr=""))
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def coverage(specs):
    result = {}
    for spec in specs.values():
        result.setdefault(spec["rule"], set()).update(spec["facets"])
    return result


def synced_catalogue(catalogue, specs=None):
    specs = specs or source_specs()
    updated = copy.deepcopy(catalogue)
    represented = coverage(specs)
    if represented != {rule: set(facets) for rule, facets in SELECTED.items()}:
        raise ValueError("DATA statement facet partition changed")
    for rule, facets in represented.items():
        matches = [row for row in updated["requirements"] if row["id"] == rule]
        if len(matches) != 1 or not facets <= set(matches[0]["facets"]):
            raise ValueError("selected DATA statement definitions changed")
        requirement = matches[0]
        for facet in facets:
            requirement["pending"].pop(facet, None)
        requirement["oracle"] = owned_paragraph(
            requirement.get("oracle", ""), "DATA statement fixture family: ", ORACLE_TEXT[rule])
        requirement["oracle_limitation"] = owned_paragraph(
            requirement.get("oracle_limitation", ""), "DATA statement fixture family boundaries: ", LIMIT_TEXT[rule])
    return updated


def render_view(catalogue, specs, root=ROOT):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    text = (Path(root) / VIEW).read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("the DATA statement generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    represented = sum(len(spec["facets"]) for spec in specs.values())
    summary = (
        SUMMARY_BEGIN + "\n"
        "## Finite DATA statement fixture packet\n\n"
        f"Thirteen complete fixtures under `data_statement_*` represent {represented} selected facets. "
        "R840/R841 controls exercise set and matched-list syntax while observing nonzero initialized values. "
        "R846/R847/C886 controls isolate default, literal, named, positive and zero repeat contributions. "
        "R848 covers portable scalar constants, signed literals, NULL() and initial data targets. "
        "S8.6.7-004 observes repeat/default-one correspondence, zero-length CHARACTER consumption, "
        "same-kind CHARACTER padding/truncation with LEN guards, a qualified positive BOZ INTEGER value, and "
        "triplet, vector, component-section and negative-step implied-DO order. "
        "S8.6.7-006 and S8.6.7-008 add pointer-association and INTEGER-domain controls.\n\n"
        "Every checked value is nonzero or otherwise nondefault, and CHARACTER comparisons are preceded by LEN "
        "guards. The BOZ cases first check radix/capacity and then compare against an independently written decimal "
        "literal. The pointer cases query only defined DATA-initialized pointer status. Mutations replace DATA "
        "features or constants and are calibrated separately; unsupported implied-DO ordering, sections, derived "
        "constructors, constant subobject repeats and DATA-implied SAVE retention stay pending here.\n\n"
        "This block and the bounded oracle paragraphs are generator-owned. The existing DATA position effects block, "
        "its fixtures, all foreign pending facets, reviews, links, baselines and rollout accounting remain unchanged.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("the DATA statement summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return (before + begin + "\n\n"
            + "\n".join(render_requirement(row) for row in catalogue["requirements"])
            + "\n" + end + after)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise ValueError("stale DATA statement fixture family: " + ", ".join(stale))
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
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} DATA statement fixtures "
          f"covering {sum(len(spec['facets']) for spec in specs.values())} facets and "
          f"{sum(len(spec['mutations']) for spec in specs.values())} feature mutations.")


if __name__ == "__main__":
    main()
