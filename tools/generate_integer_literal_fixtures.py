#!/usr/bin/env python3
"""Generate the bounded 7.4.1/7.4.3.1 fixtures and qualified literal profiles."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_ERRORS = [
    "not implemented", "not yet implemented", "unimplemented",
    "not supported yet", "not yet supported", "unsupported feature",
]
SYNTAX_EXCLUSIONS = IMPLEMENTATION_ERRORS + [
    "unsupported", "not supported", "too large", "overflow",
    "out of range", "outside the representable range",
]
# These are numeric-model branches, not universal storage layouts or kind codes.
BOUNDARIES = [
    ("range2_binary7", "selected_int_kind(2)", 7, "selected-small-boundary", False),
    ("range4_binary15", "selected_int_kind(4)", 15, "selected-small-boundary", False),
    ("default_binary31", "kind(0)", 31, "default-model-boundary", False),
    ("range18_binary63", "selected_int_kind(18)", 63, "selected-wide-boundary", False),
    ("range38_binary127", "selected_int_kind(38)", 127, "optional-large-boundary", True),
]


def kind_value_messages(category, value):
    messages = [
        f"kind {value} is not supported for {category}",
        f"kind {value} not supported for type {category}",
        f"{category}(kind={value}) is not a supported type",
    ]
    if category == "integer":
        messages.append(f"integer kind {value} at (1) not available")
    return messages


def outputs():
    result = {}

    def put(relative, content):
        path = ROOT / relative
        if path in result:
            raise ValueError(f"duplicate generated path: {relative}")
        result[path] = content.encode("ascii")

    def program(rule, variant, facets, body, evidence="positive-control", profiles=(), standard=""):
        stem = rule.replace(".", "_").replace("-", "_") + "_valid"
        if variant:
            stem += "__" + variant
        header = f"! rule: {rule}\n! covers: {' '.join(facets)}\n! evidence: {evidence}\n"
        if profiles:
            header += "! profile: " + " ".join(profiles) + "\n"
        if standard:
            header += "! standard: " + standard + "\n"
        put(f"tests/clause07/{stem}.f90", header + "program p\n" + body + "end program\n")

    def pair(prefix, rule, name, bad, wrong, repaired, statement, bad_facets,
             good_facets, messages, profiles=(), excludes=IMPLEMENTATION_ERRORS):
        if bad.count(wrong) != 1:
            raise ValueError(f"{rule}/{name}: repair is not one unique substitution")
        locations = [n for n, line in enumerate(bad.splitlines(), 1) if line.strip() == statement]
        if len(locations) != 1:
            raise ValueError(f"{rule}/{name}: diagnostic statement is not unique")
        for invalid in (True, False):
            state = "invalid" if invalid else "valid"
            folder = f"tests/fixtures/{prefix}_{rule.lower()}_{name}_{state}"
            identifier = f"{rule}_{state}__{name}" + ("" if invalid else "_repair")
            manifest = {
                "schema_version": 1, "id": identifier, "rule": rule,
                "facets": bad_facets if invalid else good_facets,
                "evidence": "effect" if invalid else "positive-control",
                "files": ["source.f90"],
                "build": [{"id": "source", "source": "source.f90", "language": "fortran",
                           "form": "free", "output": "source.o"}],
                "expect": {"phase": "compile", "step": "source",
                           "outcome": "diagnose" if invalid else "success"},
            }
            if profiles:
                manifest["profiles"] = list(profiles)
            if invalid:
                manifest["expect"]["diagnostic"] = {
                    "file": "source.f90", "line": locations[0],
                    "contains_any": messages, "excludes_any": excludes,
                }
            put(folder + "/source.f90", bad if invalid else bad.replace(wrong, repaired, 1))
            put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")

    intrinsic_controls = [
        ("integer", ["integer-alternative"], """    implicit none
    integer :: a = 17
    integer(kind=kind(0)) :: b = -23
    if (a /= 17) error stop 1
    if (b /= -23) error stop 2
"""),
        ("real", ["real-default", "real-selector"], """    implicit none
    real :: a = 0.0
    real(kind=kind(0.0d0)) :: b = 0.0d0
    if (a /= 0.0) error stop 1
    if (b /= 0.0d0) error stop 2
"""),
        ("double_precision", ["double-precision"], """    implicit none
    double precision :: a = 0.0d0
    if (a /= 0.0d0) error stop 1
"""),
        ("complex", ["complex-default", "complex-selector"], """    implicit none
    complex :: a = (0.0, 0.0)
    complex(kind=kind(0.0d0)) :: b = (0.0d0, 0.0d0)
    if (a /= (0.0, 0.0)) error stop 1
    if (b /= (0.0d0, 0.0d0)) error stop 2
"""),
        ("character", ["character-default", "character-selector"], """    implicit none
    character :: a = 'a'
    character(len=3, kind=kind('a')) :: b = 'bcd'
    if (a /= 'a') error stop 1
    if (b /= 'bcd') error stop 2
"""),
        ("logical", ["logical-default", "logical-selector"], """    implicit none
    logical :: a = .true.
    logical(kind=kind(.true.)) :: b = .false.
    if (.not. a) error stop 1
    if (b) error stop 2
"""),
    ]
    for name, facets, body in intrinsic_controls:
        program("R704", name, facets, body)
    program("R705", "", ["without-selector", "with-selector"], """    implicit none
    integer :: a = 17
    integer(kind=kind(0)) :: b = -23
    call check(a, 17)
    call check(b, -23)
contains
    subroutine check(value, expected)
        integer, intent(in) :: value, expected
        if (value /= expected) error stop 1
    end subroutine
""")
    program("R706", "", ["positional-expression", "keyword-expression"], """    implicit none
    integer, parameter :: selector = kind(0)
    integer(selector + 0) :: a = 13
    integer(kind=kind(0) + 0) :: b = -19
    if (kind(a) /= kind(0)) error stop 1
    if (kind(b) /= kind(0)) error stop 2
    if (a /= 13) error stop 3
    if (b /= -19) error stop 4
""")
    program("R706", "selected_expression_kind", ["integer-expression-kind"], """    implicit none
    integer, parameter :: wide = selected_int_kind(18)
    integer(wide), parameter :: selector = kind(0)
    integer(selector + 0_wide) :: a = 13
    if (kind(a) /= kind(0)) error stop 1
    if (a /= 13) error stop 2
""", profiles=["integer-literal-kind-code-decimal10"], standard="f2023")
    for name, wrong, repaired, facet in (
        ("missing_value", "integer(kind=)", "integer(kind=kind(0))", "missing-value"),
        ("wrong_keyword", "integer(knd=kind(0))", "integer(kind=kind(0))", "wrong-keyword"),
    ):
        statement = wrong + " :: value"
        premise = "    integer, parameter :: knd = kind(0)\n" if name == "wrong_keyword" else ""
        messages = (["Token ')' is unexpected here", "Expected initialization expression", "expected ')'"]
                    if name == "missing_value" else ["Missing right parenthesis", "expected ')'"])
        pair("intrinsic_type_spec", "R706", name,
             "subroutine p\n    implicit none\n" + premise + "    " + statement + "\nend subroutine\n",
             wrong, repaired, statement, [facet], ["keyword-expression"],
             messages, excludes=SYNTAX_EXCLUSIONS)

    selectors = {
        "integer": ("integer", "kind(0)", "integer"),
        "real": ("real", "kind(0.0)", "real"),
        "complex": ("complex", "kind(0.0)", "real"),
        "logical": ("logical", "kind(.true.)", "logical"),
    }
    for name, (keyword, supported, inventory) in selectors.items():
        for value, variant, profiles in (
            ("-1", "negative", ()),
            ("0", "absent_zero", (f"integer-literal-absent-zero-{inventory}",)),
        ):
            statement = f"{keyword}(kind={value}) :: value"
            pair("intrinsic_type_spec", "C717", name + "_" + variant,
                 "subroutine p\n    implicit none\n    " + statement + "\nend subroutine\n",
                 f"kind={value}", f"kind={supported}", statement,
                 [f"{variant.replace('_', '-')}-{name}"], [f"supported-{name}"],
                 kind_value_messages(keyword, value), profiles)

    parameter_types = [
        ("integer", "integer", "0", "kind(0)"),
        ("real", "real(kind=kind(0.0d0))", "0.0d0", "kind(0.0d0)"),
        ("complex", "complex(kind=kind(0.0d0))", "(0.0d0, 0.0d0)", "kind(0.0d0)"),
        ("character", "character(len=3, kind=kind('a'))", "'abc'", "kind('a')"),
        ("logical", "logical", ".true.", "kind(.true.)"),
    ]
    for name, declaration, initializer, expected in parameter_types:
        program("S7.4.1-001", name, [name + "-parameter"], f"""    implicit none
    {declaration} :: value = {initializer}
    if (kind(value%kind) /= kind(0)) error stop 1
    call check(value%kind, {expected})
contains
    subroutine check(parameter, expected)
        integer, intent(in) :: parameter, expected
        if (parameter /= expected) error stop 2
    end subroutine
""", evidence="effect")

    program("R707", "", ["unsigned", "plus", "minus", "kind-suffix"], """    implicit none
    integer, parameter :: k = kind(0)
    integer :: a, b, c, d, e, f
    data a, b, c, d, e, f /13, +17, -19, 23_k, +29_k, -31_k/
    if (a /= 10 + 3) error stop 1
    if (b /= 10 + 7) error stop 2
    if (c /= 1 - 20) error stop 3
    if (d /= 20 + 3) error stop 4
    if (e /= 30 - 1) error stop 5
    if (f /= 0 - 30 - 1) error stop 6
""")
    pair("integer_literal", "R707", "double_sign",
         "subroutine p\n    implicit none\n    integer :: value\n    data value /--7/\nend subroutine\n",
         "--7", "-7", "data value /--7/", ["single-sign-only"], ["minus"],
         ["Syntax error in DATA statement", "expected '('"], excludes=SYNTAX_EXCLUSIONS)
    program("R708", "", ["digits-only", "kind-suffix"], """    implicit none
    integer, parameter :: k = kind(0)
    integer :: a, b
    data a, b /37, 41_k/
    if (a /= 30 + 7) error stop 1
    if (b /= 40 + 1) error stop 2
""")
    pair("integer_literal", "R708", "empty_suffix",
         "subroutine p\n    implicit none\n    integer, parameter :: k = kind(0)\n"
         "    integer :: value\n    data value /7_/\nend subroutine\n",
         "7_", "7_k", "data value /7_/", ["suffix-needs-kind"], ["kind-suffix"],
         ["Token '_' (of type 'identifier') is unexpected here", "Missing kind-parameter", "expected '/'"],
         excludes=SYNTAX_EXCLUSIONS)
    program("R709", "name", ["constant-name"], """    implicit none
    integer, parameter :: selector = kind(0)
    integer :: value
    data value /43_selector/
    if (value /= 40 + 3) error stop 1
""")
    program("R709", "digits", ["digit-string", "zero-padded-kind-digits"], """    implicit none
    integer, parameter :: selector = 8
    integer(selector) :: a, b
    data a, b /43_8, 47_0008/
    if (a /= 40_selector + 3_selector) error stop 1
    if (b /= 40_selector + 7_selector) error stop 2
""", profiles=["integer-literal-kind-eight"])
    pair("integer_literal", "R709", "expression_suffix",
         "subroutine p\n    implicit none\n    integer, parameter :: selector = kind(0)\n"
         "    integer :: value\n    data value /7_(selector)/\nend subroutine\n",
         "7_(selector)", "7_selector", "data value /7_(selector)/",
         ["expression-not-alternative"], ["constant-name"],
         ["Token '_' (of type 'identifier') is unexpected here", "Missing kind-parameter", "expected '/'"],
         excludes=SYNTAX_EXCLUSIONS)
    program("R710", "", ["unsigned-digits", "plus-digits", "minus-digits"], """    implicit none
    double precision :: a = 1.0d0, b = 1.0d+1, c = 1.0d-1
    if (a /= 1.0d0) error stop 1
    if (b /= 10.0d0) error stop 2
    if (c <= 0.0d0) error stop 3
    if (c >= 1.0d0) error stop 4
""")
    pair("integer_literal", "R710", "double_exponent_sign",
         "subroutine p\n    implicit none\n    double precision :: value = 1.0d++1\nend subroutine\n",
         "1.0d++1", "1.0d+1", "double precision :: value = 1.0d++1",
         ["single-sign-only"], ["plus-digits"],
         ["Token 'd' (of type 'identifier') is unexpected here", "Missing exponent in real number"],
         excludes=SYNTAX_EXCLUSIONS)
    program("R711", "", ["one-digit", "multiple-digits", "leading-zero"], """    implicit none
    integer :: a, b, c
    data a, b, c /7, 12345, 00089/
    if (a /= 3 + 4) error stop 1
    if (b /= 12000 + 345) error stop 2
    if (c /= 80 + 9) error stop 3
""")
    pair("integer_literal", "R711", "nondigit",
         "subroutine p\n    implicit none\n    integer :: value\n    data value /1a2/\nend subroutine\n",
         "1a2", "12", "data value /1a2/", ["digits-only"], ["multiple-digits"],
         ["Token 'a2' (of type 'identifier') is unexpected here", "Syntax error in DATA statement", "expected '/'"],
         excludes=SYNTAX_EXCLUSIONS)
    program("R712", "", ["plus", "minus"], """    implicit none
    integer :: positive, negative
    data positive, negative /+37, -41/
    if (positive /= 30 + 7) error stop 1
    if (negative /= 0 - 40 - 1) error stop 2
""")
    pair("integer_literal", "C718", "variable_name",
         "subroutine p\n    implicit none\n    integer :: selector = kind(0)\n"
         "    integer, parameter :: value = 1_selector\nend subroutine\n",
         "integer :: selector", "integer, parameter :: selector",
         "integer, parameter :: value = 1_selector", ["named-constant-required"], ["integer-named-constant"],
         ["must be a constant value", "not a constant expression", "is not a named constant"],
         excludes=SYNTAX_EXCLUSIONS)
    pair("integer_literal", "C718", "real_name",
         "subroutine p\n    implicit none\n    double precision, parameter :: selector = kind(0)\n"
         "    integer, parameter :: value = 1_selector\nend subroutine\n",
         "double precision, parameter :: selector", "integer, parameter :: selector",
         "integer, parameter :: value = 1_selector", ["integer-type-required"], ["integer-named-constant"],
         ["is constant but not an integer", "must have integer type, but is real"],
         profiles=["integer-literal-kind-code-decimal10"],
         excludes=SYNTAX_EXCLUSIONS)
    pair("integer_literal", "C719", "negative_name",
         "subroutine p\n    implicit none\n    integer, parameter :: selector = -1\n"
         "    integer, parameter :: value = 1_selector\nend subroutine\n",
         "selector = -1", "selector = kind(0)", "integer, parameter :: value = 1_selector",
         ["negative-named-value"], ["nonnegative-supported-value"],
         kind_value_messages("integer", "-1"))
    pair("integer_literal", "C720", "absent_digit",
         "subroutine p\n    implicit none\n    integer, parameter :: selector = kind(0)\n"
         "    integer, parameter :: value = 1_0\nend subroutine\n",
         "1_0", "1_selector", "integer, parameter :: value = 1_0",
         ["unsupported-digit-value"], ["supported-name"], kind_value_messages("integer", "0"),
         ["integer-literal-absent-zero-integer"])
    pair("integer_literal", "C720", "absent_name",
         "subroutine p\n    implicit none\n    integer, parameter :: selector = 0\n"
         "    integer, parameter :: value = 1_selector\nend subroutine\n",
         "selector = 0", "selector = kind(0)", "integer, parameter :: value = 1_selector",
         ["unsupported-named-value"], ["supported-name"], kind_value_messages("integer", "0"),
         ["integer-literal-absent-zero-integer"])

    program("S7.4.3.1-001", "", ["default-method", "selected-method", "inquiry-connections", "inventory-membership"], """    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: wide = selected_int_kind(18)
    integer :: default_value, quotient, decimal_range
    integer(wide) :: selected_value, wide_quotient
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (.not. any(integer_kinds == wide)) error stop 3
    default_value = -17
    selected_value = 23_wide
    if (kind(selected_value) /= wide) error stop 4
    if (default_value /= 0 - 10 - 7) error stop 5
    if (selected_value /= 20_wide + 3_wide) error stop 6
    quotient = huge(default_value)
    decimal_range = 0
    do while (quotient >= 10)
        quotient = quotient / 10
        decimal_range = decimal_range + 1
    end do
    if (range(default_value) /= decimal_range) error stop 7
    wide_quotient = huge(selected_value)
    decimal_range = 0
    do while (wide_quotient >= 10_wide)
        wide_quotient = wide_quotient / 10_wide
        decimal_range = decimal_range + 1
    end do
    if (range(selected_value) /= decimal_range) error stop 8
    print *, 'integer_kinds', integer_kinds
    print *, 'default_kind_radix_digits_range', kind(0), radix(0), digits(0), range(0)
    print *, 'default_huge', huge(0)
    print *, 'selected18_kind_radix_digits_range', wide, radix(0_wide), digits(0_wide), range(0_wide)
    print *, 'selected18_huge', huge(0_wide)
""", evidence="effect", standard="f2023")
    for name, declaration, suffix, standard in (
        ("default", "", "", ""),
        ("selected", "    integer, parameter :: k = selected_int_kind(18)\n", "_k", "f2023"),
    ):
        kind = "(k)" if suffix else ""
        program("S7.4.3.1-002", name, [name + "-zero", name + "-signed-zero"], f"""    implicit none
{declaration}    integer{kind} :: bare, positive, negative
    data bare, positive, negative /0{suffix}, +0{suffix}, -0{suffix}/
    if (bare /= 1{suffix} - 1{suffix}) error stop 1
    if (positive /= 1{suffix} - 1{suffix}) error stop 2
    if (negative /= 1{suffix} - 1{suffix}) error stop 3
    if (bare < 0{suffix}) error stop 4
    if (bare > 0{suffix}) error stop 5
    if (positive < 0{suffix}) error stop 6
    if (positive > 0{suffix}) error stop 7
    if (negative < 0{suffix}) error stop 8
    if (negative > 0{suffix}) error stop 9
""", evidence="effect", standard=standard)
    program("S7.4.3.1-003", "", ["method-exists", "eighteen-digit-capacity"], """    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: value
    integer :: i
    if (k < 0) error stop 1
    value = 0_k
    do i = 1, 18
        if (value > (huge(value) - 9_k) / 10_k) error stop 2
        value = value * 10_k + 9_k
    end do
    do i = 1, 18
        if (mod(value, 10_k) /= 9_k) error stop 3
        value = value / 10_k
    end do
    if (value /= 0_k) error stop 4
""", evidence="effect", standard="f2023")
    # Selection's open decimal interval is not a proof about every possible
    # processor model. Inspect all advertised kinds in this bounded branch.
    inventory = "    use iso_fortran_env, only: integer_kinds\n    implicit none\n"
    inventory += "    integer, parameter :: n = size(integer_kinds)\n"
    for slot in range(1, 17):
        inventory += f"    integer, parameter :: k{slot} = integer_kinds(min({slot}, n))\n"
    inventory += "    integer :: ranges(16)\n"
    inventory += "    if (n < 1 .or. n > 16) error stop 1\n"
    for slot in range(1, 17):
        inventory += f"    ranges({slot}) = range(0_k{slot})\n"
    inventory += "    if (maxval(ranges) < 18) error stop 2\n"
    inventory += "    print *, 'advertised_kind_count', n\n"
    inventory += "    print *, 'advertised_ranges', ranges(1:n)\n"
    program("S7.4.3.1-003", "inventory", ["range-eighteen"], inventory,
            evidence="effect", profiles=["integer-literal-bounded-inventory"], standard="f2023")
    put("tests/profiles/integer_literal_bounded_inventory.f90", """program integer_literal_bounded_inventory
    use iso_fortran_env, only: integer_kinds
    implicit none
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (selected_int_kind(18) < 0) error stop 3
    if (size(integer_kinds) > 16) stop 77
end program
""")
    program("S7.4.3.1-004", "", ["omitted-selector-kind", "default-range-five"], """    implicit none
    integer :: value
    integer(kind=kind(0)) :: explicit_value
    value = 99999
    explicit_value = -99999
    if (kind(value) /= kind(0)) error stop 1
    if (kind(value) /= kind(explicit_value)) error stop 2
    if (range(value) < 5) error stop 3
    if (value /= 10000 * 9 + 9999) error stop 4
    if (explicit_value /= 0 - 10000 * 9 - 9999) error stop 5
    call check(value)
contains
    subroutine check(n)
        integer(kind=kind(0)), intent(in) :: n
        if (n /= 99999) error stop 6
    end subroutine
""", evidence="effect")
    program("S7.4.3.1-005", "small", ["small-default-values"], """    implicit none
    integer :: a, b, c, d
    data a, b, c, d /0, +19, -23, 99999/
    if (a /= 1 - 1) error stop 1
    if (b /= 20 - 1) error stop 2
    if (c /= 0 - 20 - 3) error stop 3
    if (d /= 9 * 10000 + 9999) error stop 4
""", evidence="effect")
    program("S7.4.3.1-005", "mandatory_wide", ["eighteen-digit-values"], """    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: positive, negative, expected
    integer :: i
    data positive, negative /+999999999999999999_k, -999999999999999999_k/
    expected = 0_k
    do i = 1, 18
        if (expected > (huge(expected) - 9_k) / 10_k) error stop 1
        expected = 10_k * expected + 9_k
    end do
    if (positive /= expected) error stop 2
    if (negative /= -expected) error stop 3
""", evidence="effect", standard="f2023")
    program("S7.4.3.1-006", "omitted", ["omitted-default"], """    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: destination
    destination = 37
    if (kind(37) /= kind(0)) error stop 1
    if (destination /= 30_k + 7_k) error stop 2
""", evidence="effect", standard="f2023")
    for name, selector, facet, profiles, standard in (
        ("named_default", "kind(0)", "named-default", (), ""),
        ("named_selected", "selected_int_kind(18)", "named-selected", (), "f2023"),
        ("digits", "8", "numeric-selector", ("integer-literal-kind-eight",), ""),
    ):
        literal = "37_8" if name == "digits" else "37_k"
        program("S7.4.3.1-006", name, [facet], f"""    implicit none
    integer, parameter :: k = {selector}
    if (kind({literal}) /= k) error stop 1
    call check({literal})
contains
    subroutine check(value)
        integer(k), intent(in) :: value
        if (value /= 30_k + 7_k) error stop 2
    end subroutine
""", evidence="effect", profiles=profiles, standard=standard)
    program("S7.4.3.1-007", "decimal", ["all-digits", "positional-value", "leading-zero-decimal"], """    implicit none
    integer :: values(10), i, positional, padded
    data values /0, 1, 2, 3, 4, 5, 6, 7, 8, 9/
    data positional, padded /12345, 00089/
    if (size(values) /= 10) error stop 1
    if (lbound(values, 1) /= 1) error stop 2
    if (ubound(values, 1) /= 10) error stop 3
    do i = 1, 10
        if (values(i) /= i - 1) error stop 4
    end do
    if (positional /= 10000 + 2000 + 300 + 40 + 5) error stop 5
    if (padded /= 8 * 10 + 9) error stop 6
""", evidence="effect")
    program("S7.4.3.1-007", "named_kind", ["named-kind-decimal"], """    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: value
    data value /000123456789012345678_k/
    if (value /= 123456789_k * 1000000000_k + 12345678_k) error stop 1
""", evidence="effect", standard="f2023")
    zeros = "0" * 64
    program("S7.4.3.1-007", "long_zero_prefix", ["long-leading-zero-small"], f"""    implicit none
    integer :: nonzero, zero
    data nonzero /{zeros}89/
    data zero /{zeros}/
    if (nonzero /= 8 * 10 + 9) error stop 1
    if (zero /= 1 - 1) error stop 2
""", evidence="effect")

    for name, selector, bits, facet, optional in BOUNDARIES:
        profile = "integer-literal-" + name.replace("_", "-")
        k_expr = "merge(candidate, kind(0), candidate >= 0)" if optional else "candidate"
        unavailable = "    if (candidate < 0) stop 77\n" if optional else "    if (candidate < 0) error stop 1\n"
        profile_body = f"""program integer_literal_profile
    implicit none
    integer, parameter :: candidate = {selector}
    integer, parameter :: k = {k_expr}
    integer(k) :: limit, reconstructed
    integer :: i
{unavailable}    if (radix(0_k) /= 2) stop 77
    if (digits(0_k) /= {bits}) stop 77
    limit = huge(0_k)
    reconstructed = 0_k
    do i = 1, {bits}
        if (reconstructed > (limit - 1_k) / 2_k) error stop 2
        reconstructed = 2_k * reconstructed + 1_k
    end do
    if (reconstructed /= limit) error stop 3
    print *, 'kind_radix_digits_range', k, radix(0_k), digits(0_k), range(0_k)
    print *, 'model_limit', limit
end program
"""
        put(f"tests/profiles/{profile.replace('-', '_')}.f90", profile_body)
        maximum = 2 ** bits - 1
        prefix = "    integer, parameter :: k = " + selector + "\n"
        declaration = "integer(k)"
        suffix = "_k"
        if name == "default_binary31":
            prefix, declaration, suffix = "", "integer", ""
        body = f"""    implicit none
{prefix}    {declaration} :: upper, adjacent, positive, lower
    data upper /{maximum}{suffix}/
    data adjacent /{maximum - 1}{suffix}/
    data positive /+{maximum}{suffix}/
    data lower /-{maximum}{suffix}/
    if (upper /= huge(upper)) error stop 1
    if (adjacent /= huge(adjacent) - 1{suffix}) error stop 2
    if (positive /= huge(positive)) error stop 3
    if (lower /= -huge(lower)) error stop 4
"""
        program("S7.4.3.1-005", name, [facet], body, evidence="effect",
                profiles=[profile], standard="f2023")
        zero_body = f"""    implicit none
{prefix}    {declaration} :: positive, negative
    data positive /+{'0' * 48}{maximum}{suffix}/
    data negative /-{'0' * 48}{maximum}{suffix}/
    if (positive /= huge(positive)) error stop 1
    if (negative /= -huge(negative)) error stop 2
"""
        program("S7.4.3.1-007", name, ["long-leading-zero-boundary"], zero_body,
                evidence="effect", profiles=[profile], standard="f2023")

    for family, default in (("integer", "0"), ("real", "0.0"), ("logical", ".true.")):
        put(f"tests/profiles/integer_literal_absent_zero_{family}.f90", f"""program integer_literal_absent_zero
    use iso_fortran_env, only: {family}_kinds
    implicit none
    if (size({family}_kinds) < 1) error stop 1
    if (.not. any({family}_kinds == kind({default}))) error stop 2
    if (any({family}_kinds == 0)) stop 77
end program
""")
    put("tests/profiles/integer_literal_kind_eight.f90", """program integer_literal_kind_eight
    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: probe = merge(8, kind(0), any(integer_kinds == 8))
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (.not. any(integer_kinds == 8)) stop 77
    if (huge(0_probe) < 47) stop 77
end program
""")
    put("tests/profiles/integer_literal_kind_code_decimal10.f90", """program integer_literal_kind_code_decimal10
    implicit none
    integer :: reduced, i
    reduced = kind(0)
    if (reduced < 0) error stop 1
    do i = 1, 10
        reduced = reduced / 10
    end do
    if (reduced /= 0) stop 77
end program
""")
    for path, raw in result.items():
        if path.suffix == ".f90" and max(map(len, raw.splitlines())) > 132:
            raise ValueError(f"unintended free-form line limit: {path.relative_to(ROOT)}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare generated files without writing")
    args = parser.parse_args()
    expected = outputs()
    if args.check:
        mismatches = [str(path.relative_to(ROOT)) for path, raw in expected.items()
                      if not path.is_file() or path.read_bytes() != raw]
        if mismatches:
            parser.error("generated inputs differ: " + ", ".join(mismatches))
    else:
        for path, raw in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    ordinary = sum(path.parent.name == "clause07" for path in expected)
    manifests = sum(path.name == "fixture.json" for path in expected)
    profiles = sum(path.parent.name == "profiles" for path in expected)
    print(f"{'Checked' if args.check else 'Generated'} {ordinary} programs, {manifests} manifests, "
          f"{profiles} profiles; {len(expected)} files.")


if __name__ == "__main__":
    main()
