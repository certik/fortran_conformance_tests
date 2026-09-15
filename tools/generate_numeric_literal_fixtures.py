#!/usr/bin/env python3
"""Generate the bounded real, complex and logical literal draft fixtures."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from tools.generate_integer_literal_fixtures import IMPLEMENTATION_ERRORS, kind_value_messages
from run_tests import isolated_cases


LEGACY_POSITIVE_SHA256 = "04861eb744699d5ddb6aa6e617db7b4bc3ffaeff2d1c0580a8b983afc8d3f2ff"
LEGACY_NEGATIVE_SHA256 = "d5ae5c4fd4c213ebd660ec45b57fe3fd3e90a8d2e38d5736a6f02b035c7c20ee"
LEGACY_POSITIVE_PROFILE = "numeric-literal-legacy-real-kinds"
LEGACY_DEFAULT_PROFILE = "numeric-literal-legacy-default-model"
ABSENT_LOGICAL_PROFILE = "integer-literal-absent-zero-logical"
CONSTANCY_ERRORS = [
    "must be a constant expression", "not a constant expression",
    "must be an integer constant expression", "is not constant",
]
DIAGNOSTIC_FAILURES = IMPLEMENTATION_ERRORS + [
    "ASR verify", "ASR verifier", "out of memory", "virtual memory exhausted",
    "resource exhausted", "resource limit",
]
SYNTAX_EXCLUSIONS = DIAGNOSTIC_FAILURES + CONSTANCY_ERRORS + [
    "overflow", "too large", "out of range", "outside the representable range",
    "invalid real kind", "invalid logical kind",
    "not supported for type real", "not supported for type logical",
]
RELATIONS = [
    ("==", True), ("/=", False), ("<", False), ("<=", True),
    (">", False), (">=", True), (".eq.", True), (".ne.", False),
    (".lt.", False), (".le.", True), (".gt.", False), (".ge.", True),
]
LEGACY_FACETS = {
    "digit-string": "unsupported-digit",
    "named-constant": "unsupported-name",
    "exponent-form": "unsupported-exponent",
    "constant-expression": "unsupported-constant-expression",
    "array-constructor": "unsupported-array-constructor",
}


def support_messages(category, value):
    return kind_value_messages(category, value) + [
        f"invalid {category} kind {value}",
        f"unsupported {category} kind {value}",
        f"{category} kind {value} is not supported",
        f"unsupported {category}(kind={value})",
    ]


def legacy_positive_body(root=ROOT):
    text = (root / "tests/clause07/C722_valid.f90").read_text()
    body = text[text.index("! C722 (R714)"):]
    if hashlib.sha256(body.encode("ascii")).hexdigest() != LEGACY_POSITIVE_SHA256:
        raise ValueError("The retained C722 positive body changed; review it explicitly.")
    return body


def legacy_negative_body(root=ROOT):
    text = (root / "tests/clause07/C722_invalid.f90").read_text()
    prefix = "! standard: f2023\n"
    if not text.startswith(prefix):
        raise ValueError("The retained C722 container needs its explicit f2023 metadata header.")
    body = text[len(prefix):]
    if hashlib.sha256(body.encode("ascii")).hexdigest() != LEGACY_NEGATIVE_SHA256:
        raise ValueError("The retained C722 negative body or marker IDs changed.")
    return body


class Bundle:
    def __init__(self):
        self.files = {}
        self.cases = {}
        self.pairs = []
        self.legacy_repairs = {}

    def put(self, path, text):
        if path in self.files:
            raise ValueError(f"duplicate generated path: {path}")
        data = text.encode("ascii")
        if not data.endswith(b"\n"):
            raise ValueError(f"missing final newline: {path}")
        if path.endswith(".f90") and any(len(line) > 132 for line in text.splitlines()):
            raise ValueError(f"overlong free-form line: {path}")
        self.files[path] = data

    def register(self, identifier, rule, facets, path, phase, evidence, profiles=()):
        if identifier in self.cases:
            raise ValueError(f"duplicate generated execution: {identifier}")
        self.cases[identifier] = dict(
            rule=rule, facets=list(facets), path=path, phase=phase,
            evidence=evidence, profiles=list(profiles), standard="f2023")

    def program(self, rule, name, facets, body):
        stem = rule.replace(".", "_").replace("-", "_") + "_valid__numeric_" + name
        path = f"tests/clause07/{stem}.f90"
        header = (f"! rule: {rule}\n! covers: {' '.join(facets)}\n"
                  "! evidence: effect\n! standard: f2023\n")
        self.put(path, header + "program numeric_literal_case\n" + body
                 + "end program numeric_literal_case\n")
        self.register(stem, rule, facets, path, "run", "effect")

    def fixture(self, rule, name, facets, source, diagnostic=None, profiles=(),
                identifier=None):
        state = "invalid" if diagnostic is not None else "valid"
        identifier = identifier or f"{rule}_{state}__numeric_{name}"
        folder = f"tests/fixtures/numeric_literal_{rule.lower()}_{name}_{state}"
        path = folder + "/fixture.json"
        evidence = "effect" if diagnostic is not None else "positive-control"
        manifest = dict(
            schema_version=1, id=identifier, rule=rule, facets=list(facets),
            evidence=evidence, standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran",
                        form="free", output="source.o")],
            expect=dict(phase="compile", step="source",
                        outcome="diagnose" if diagnostic is not None else "success"))
        if diagnostic is not None:
            manifest["expect"]["diagnostic"] = dict(file="source.f90", **diagnostic)
        if profiles:
            manifest["profiles"] = list(profiles)
        self.put(folder + "/source.f90", source)
        self.put(path, json.dumps(manifest, indent=2) + "\n")
        self.register(identifier, rule, facets, path, "compile", evidence, profiles)
        return path

    def pair(self, rule, name, source, bad, repair, statement, bad_facets,
             good_facets, messages, profiles=(), excludes=SYNTAX_EXCLUSIONS,
             nonfatal=()):
        if source.count(bad) != 1:
            raise ValueError(f"{rule}/{name}: repair is not one unique substitution")
        lines = [n for n, line in enumerate(source.splitlines(), 1)
                 if line.strip() == statement]
        if len(lines) != 1:
            raise ValueError(f"{rule}/{name}: diagnostic statement is not unique")
        diagnostic = dict(line=lines[0], contains_any=list(messages), excludes_any=list(excludes))
        if nonfatal:
            diagnostic["allow_nonfatal"] = list(nonfatal)
        invalid = self.fixture(rule, name, bad_facets, source, diagnostic, profiles)
        valid = self.fixture(rule, name + "_repair", good_facets,
                             source.replace(bad, repair, 1), profiles=profiles)
        self.pairs.append(dict(rule=rule, name=name, invalid=invalid, valid=valid,
                               bad=bad, repair=repair, line=lines[0]))

    def coverage(self):
        result = defaultdict(set)
        for case in self.cases.values():
            result[case["rule"]].update(case["facets"])
        return dict(result)


def subroutine(declarations, statements):
    return "subroutine p\n    implicit none\n" + declarations + statements + "end subroutine\n"


def integer_dummy():
    return """contains
    subroutine integer_result(value)
        integer, intent(in) :: value
        if (kind(value) /= kind(0)) error stop 90
    end subroutine
"""


def relation_checks(pairs, relations=RELATIONS):
    lines = []
    for left, right in pairs:
        for operator, expected in relations:
            expr = f"{left} {operator} {right}"
            failure = f".not. ({expr})" if expected else expr
            lines.append(f"    if ({failure}) error stop {len(lines) + 1}\n")
    return "".join(lines)


def legacy_profiles(bundle):
    bundle.put("tests/profiles/numeric_literal_legacy_real_kinds.f90", """program legacy_real_kinds
    use iso_fortran_env, only: real_kinds, real32, real64, real128
    implicit none
    integer, parameter :: dk = kind(0.0d0)
    integer, parameter :: selected_qp = merge(real128, real64, real128 > 0)
    ! Safe selectors permit an absent optional method to reach STOP 77.
    integer, parameter :: sk = merge(real32, dk, real32 >= 0)
    integer, parameter :: dp = merge(real64, dk, real64 >= 0)
    integer, parameter :: qk = merge(selected_qp, dk, selected_qp >= 0)
    real(sk) :: zs = 0.0_sk
    real(dp) :: zd = 0.0_dp
    real(qk) :: zq = 0.0_qk
    if (size(real_kinds) < 2) error stop 1
    if (.not. any(real_kinds == kind(0.0))) error stop 2
    if (.not. any(real_kinds == dk)) error stop 3
    if (precision(0.0d0) <= precision(0.0)) error stop 4
    if (precision(0.0d0) < 10 .or. range(0.0d0) < 37) error stop 5
    if (real32 /= 4 .or. real64 /= 8) stop 77
    if (dk /= real64) stop 77
    if (selected_qp < 0) stop 77
    if (.not. any(real_kinds == real32)) error stop 6
    if (.not. any(real_kinds == real64)) error stop 7
    if (.not. any(real_kinds == selected_qp)) error stop 8
    if (radix(zs) /= 2 .or. radix(zd) /= 2 .or. radix(zq) /= 2) stop 77
    if (digits(zs) < 3 .or. digits(zd) < 3 .or. digits(zq) < 3) stop 77
    if (range(zs) < 1 .or. range(zd) < 1 .or. range(zq) < 1) stop 77
    print *, 'default,double,real32,real64,real128,selected_qp'
    print *, kind(0.0), dk, real32, real64, real128, selected_qp
    if (real128 == 0) print *, 'REAL128 zero uses the retained REAL64 fallback'
end program
""")
    bundle.put("tests/profiles/numeric_literal_legacy_default_model.f90", """program legacy_default_model
    use iso_fortran_env, only: real_kinds
    implicit none
    if (size(real_kinds) < 2) error stop 1
    if (.not. any(real_kinds == kind(0.0))) error stop 2
    if (.not. any(real_kinds == kind(0.0d0))) error stop 3
    if (precision(0.0d0) <= precision(0.0)) error stop 4
    if (precision(0.0d0) < 10 .or. range(0.0d0) < 37) error stop 5
    ! A numerical model bound, not a rounding or physical-format assertion.
    if (radix(0.0) /= 2) stop 77
    if (digits(0.0) < 3 .or. range(0.0) < 1) stop 77
    print *, 'default kind,radix,digits,range'
    print *, kind(0.0), radix(0.0), digits(0.0), range(0.0)
end program
""")


def retained_cases(bundle, root):
    body = legacy_positive_body(root)
    facets = ["supported-name", "legacy-supported-digit-codes"]
    header = ("! rule: C722\n! covers: " + " ".join(facets)
              + "\n! evidence: positive-control\n! standard: f2023\n"
              + f"! profile: {LEGACY_POSITIVE_PROFILE}\n"
              + "! oracle-basis: processor-profile\n"
              + f"! oracle-profile: {LEGACY_POSITIVE_PROFILE}\n"
              + "! Legacy conditional admission control, not an IEEE or rounding oracle.\n")
    path = "tests/clause07/C722_valid.f90"
    bundle.put(path, header + body)
    bundle.register("C722_valid", "C722", facets, path, "run", "positive-control",
                    [LEGACY_POSITIVE_PROFILE])
    bundle.cases["C722_valid"].update(oracle_basis="processor-profile",
                                    oracle_profile=LEGACY_POSITIVE_PROFILE)
    invalid = root / "tests/clause07/C722_invalid.f90"
    legacy_negative_body(root)
    contracts = {}
    profiles = [LEGACY_DEFAULT_PROFILE, "absent-real-kind-seven"]
    replacements = {
        "digit-string": ("1.0_7", "1.0"),
        "named-constant": ("integer, parameter :: k = 7",
                           "integer, parameter :: k = kind(0.0)"),
        "exponent-form": ("1.0e0_7", "1.0e0"),
        "constant-expression": ("2.0_7", "2.0"),
        "array-constructor": ("[1.0_7, 2.0_7]", "[1.0, 2.0]"),
    }
    for marker, rule, name, bounds, source in isolated_cases(str(invalid), "C722"):
        facet = LEGACY_FACETS[name]
        contracts[name] = dict(
            facets=[facet], profiles=profiles, outcome="diagnose",
            diagnostic=dict(
                contains_any=support_messages("real", 7),
                excludes_any=DIAGNOSTIC_FAILURES + CONSTANCY_ERRORS + [
                    "invalid number of array", "array constructor has",
                    "has a 'd' exponent", "overflow", "out of range"]))
        identifier = "C722_invalid:" + name
        bundle.register(identifier, "C722", [facet], str(invalid.relative_to(root)),
                        "compile", "effect", profiles)
        bad, repair = replacements[name]
        if source.count(bad) != 1:
            raise ValueError(f"legacy {name}: repair is not unique")
        # The candidate container is untouched; only its conforming twin is generated.
        control = source.replace(bad, repair, 1).rstrip("\n") + "\n"
        path = bundle.fixture("C722", "legacy_" + name.replace("-", "_") + "_repair",
                              ["supported-name"] if name == "named-constant" else [facet],
                              control, profiles=[LEGACY_DEFAULT_PROFILE])
        bundle.legacy_repairs[name] = dict(
            path=path, marker=marker, bad=bad, repair=repair,
            invalid_source=source, control_source=control)
    bundle.put("tests/clause07/C722_invalid.cases.json",
               json.dumps(dict(schema_version=1, cases=contracts), indent=2) + "\n")


def real_syntax(bundle):
    kd = "    integer, parameter :: kd = kind(0.0d0)\n"
    bundle.fixture("R713", "sign_forms",
                   ["unsigned", "plus", "minus", "signed-suffixed"],
                   subroutine(kd + "    real(kd) :: a, b, c, d, e\n",
                              "    data a, b, c, d, e /0.0d0, +0.0d0, -0.0d0, +0.0_kd, -0.0_kd/\n"))
    bundle.pair("R713", "double_leading_sign",
                subroutine("    double precision :: x\n", "    data x /--0.0d0/\n"),
                "--0.0d0", "-0.0d0", "data x /--0.0d0/",
                ["single-leading-sign"], ["minus"],
                ["Token '-' is unexpected here"])
    bundle.fixture("R714", "literal_forms", [
        "significand-only", "significand-exponent", "digits-exponent",
        "significand-suffix", "significand-exponent-suffix", "digits-exponent-suffix"],
        subroutine(kd + "    real :: a, b, c\n    real(kd) :: d, e, f, g, h\n",
                   "    data a, b, c /0.0, 0.0e0, 0e0/\n"
                   "    data d, e, f, g, h /0.0d0, 0d0, 0.0_kd, 0.0e0_kd, 0e0_kd/\n"))
    bundle.pair("R714", "empty_suffix",
                subroutine(kd + "    real(kd) :: x\n", "    data x /0.0_/\n"),
                "0.0_", "0.0_kd", "data x /0.0_/",
                ["suffix-needs-kind"], ["significand-suffix"],
                ["Missing kind-parameter", "Token '_' (of type 'identifier') is unexpected here"])
    bundle.fixture("R715", "significands",
                   ["digits-both-sides", "trailing-point", "leading-point"],
                   subroutine("    double precision :: a, b, c\n",
                              "    data a, b, c /00.0d0, 0.d0, .0d0/\n"))
    bundle.pair("R715", "bare_dot",
                subroutine("    real :: x\n", "    data x /./\n"),
                "data x /./", "data x /.0/", "data x /./",
                ["digit-required"], ["leading-point"],
                ["Token '.' is not recognized"])
    bundle.fixture("R716", "letters", ["e-letter", "d-letter"],
                   subroutine("    real :: a, b\n    double precision :: c, d\n",
                              "    data a, b /0.0E0, 0.0e0/\n"
                              "    data c, d /0.0D0, 0.0d0/\n"))
    bundle.pair("R716", "q_exponent",
                subroutine("    double precision :: x\n", "    data x /0.0Q0/\n"),
                "0.0Q0", "0.0D0", "data x /0.0Q0/",
                ["nonstandard-letter"], ["d-letter"],
                ["exponent-letter 'q' in real-literal-constant",
                 "Token 'Q0' (of type 'identifier') is unexpected here",
                 "nonstandard usage: Q exponent"],
                nonfatal=[dict(compiler="flang", severity="portability",
                               equals_any=["nonstandard usage: Q exponent"])])
    bundle.fixture("R717", "exponent_forms", [
        "unsigned-exponent", "plus-exponent", "minus-exponent",
        "multiple-and-leading-zero-digits"],
        subroutine("    double precision :: a, b, c, d, e\n",
                   "    data a, b, c, d, e /0.0d0, 0.0d+0, 0.0d-0, 0.0d000, 0.0d+000/\n"))
    bundle.fixture("C721", "conditional_controls",
                   ["suffix-without-exponent", "e-with-suffix", "d-without-suffix"],
                   subroutine(kd + "    real(kd) :: a, b, c\n",
                              "    data a, b, c /0.0_kd, 0.0e0_kd, 0.0d0/\n"))
    bundle.pair("C721", "d_named_suffix",
                subroutine(kd + "    real(kd) :: x\n", "    data x /0.0d0_kd/\n"),
                "0.0d0_kd", "0.0e0_kd", "data x /0.0d0_kd/",
                ["d-with-named-suffix"], ["e-with-suffix"],
                ["has a 'd' exponent and an explicit kind",
                 "Explicit kind parameter together with non-'E' exponent letter is not standard"],
                nonfatal=[dict(
                    compiler="flang", severity="portability",
                    equals_any=["Explicit kind parameter together with non-'E' exponent letter "
                                "is not standard [-Wexponent-matching-kind-param]"])])
    bundle.fixture("C722", "supported_names", ["supported-name"],
                   subroutine("    integer, parameter :: kr = kind(0.0), kd = kind(0.0d0)\n"
                              "    real(kr) :: a\n    real(kd) :: b\n",
                              "    data a, b /0.0_kr, 0.0e0_kd/\n"))


def real_effects(bundle):
    bundle.program("S7.4.3.2-001", "mandatory_methods",
                   ["two-method-minimum", "default-double-membership"], """    use iso_fortran_env, only: real_kinds
    implicit none
    real :: r = 0.0
    double precision :: d = 0.0d0
    if (size(real_kinds) < 2) error stop 1
    if (kind(r) /= kind(0.0)) error stop 2
    if (kind(d) /= kind(0.0d0)) error stop 3
    if (kind(r) == kind(d)) error stop 4
    if (.not. any(real_kinds == kind(r))) error stop 5
    if (.not. any(real_kinds == kind(d))) error stop 6
""")
    queries = [
        "kind(0.0)", "kind(0.0d0)", "precision(0.0)", "precision(0.0d0)",
        "range(0.0)", "range(0.0d0)", "radix(0.0)", "radix(0.0d0)",
        "selected_real_kind(p=10)", "selected_real_kind(r=37)",
        "selected_real_kind(p=10, r=37, radix=radix(0.0d0))",
    ]
    body = "    implicit none\n"
    for index, expression in enumerate(queries, 1):
        body += f"    if (kind({expression}) /= kind(0)) error stop {index}\n"
        body += f"    call integer_result({expression})\n"
    bundle.program("S7.4.3.2-002", "inquiry_result_types",
                   ["default-integer-inquiry-results"], body + integer_dummy())
    for name, request, facets, tests in [
        ("precision_selection", "p=10", ["precision-selection"], ["precision(z) < 10"]),
        ("range_selection", "r=37", ["range-selection"], ["range(z) < 37"]),
        ("radix_selection", "p=10, r=37, radix=radix(0.0d0)", ["radix-selection"],
         ["precision(z) < 10", "range(z) < 37", "radix(z) /= radix(0.0d0)"]),
    ]:
        body = (f"    implicit none\n    integer, parameter :: k = selected_real_kind({request})\n"
                "    real(k) :: z = 0.0_k\n    if (k < 0) error stop 1\n"
                "    if (kind(z) /= k) error stop 2\n")
        body += "".join(f"    if ({test}) error stop {n}\n" for n, test in enumerate(tests, 3))
        bundle.program("S7.4.3.2-002", name, facets, body)
    for name, declaration, zero in [
        ("default", "real", "0.0"), ("double", "double precision", "0.0d0"),
    ]:
        body = (f"    implicit none\n    {declaration} :: u, p, n\n"
                f"    data u, p, n /{zero}, +{zero}, -{zero}/\n"
                f"    if (u /= {zero}) error stop 100\n")
        body += relation_checks([(a, b) for a in ["p", "n"] for b in ["p", "n"]])
        bundle.program("S7.4.3.2-003", name + "_zero_relations",
                       ["zero-exists", "all-relational-spellings"], body)
        body = (f"    implicit none\n    {declaration} :: u, p, n\n"
                f"    data u, p, n /{zero}, +{zero}, -{zero}/\n")
        for index, expr in enumerate(["abs(p)", "abs(n)", "min(p,n)", "min(n,p)",
                                      "max(p,n)", "max(n,p)"], 1):
            body += f"    if ({expr} /= u) error stop {index}\n"
        body += ("    if (int(p) /= 0 .or. int(n) /= 0) error stop 7\n"
                 "    if (kind(int(p)) /= kind(0)) error stop 8\n")
        bundle.program("S7.4.3.2-003", name + "_zero_intrinsics",
                       ["finite-intrinsic-arguments"], body)
    declarations = """    implicit none
    real :: rp = +0.0, rn = -0.0
    double precision :: dp = +0.0d0, dn = -0.0d0
"""
    pairs = [(r, d) for r in ["rp", "rn"] for d in ["dp", "dn"]]
    bundle.program("S7.4.3.2-003", "mixed_real_zeros", ["mixed-kind-and-type-relations"],
                   declarations + relation_checks(pairs + [(b, a) for a, b in pairs]))
    pairs = [(r, "i") for r in ["rp", "rn", "dp", "dn"]]
    bundle.program("S7.4.3.2-003", "integer_real_zeros", ["mixed-kind-and-type-relations"],
                   declarations + "    integer :: i = 0\n"
                   + relation_checks(pairs + [(b, a) for a, b in pairs]))
    pairs = [(r, c) for r in ["rp", "rn", "dp", "dn"] for c in ["c", "dc"]]
    bundle.program("S7.4.3.2-003", "complex_real_zeros", ["mixed-kind-and-type-relations"],
                   declarations + "    complex :: c = (0.0, 0.0)\n"
                   "    complex(kind(0.0d0)) :: dc = (0.0d0, 0.0d0)\n"
                   + relation_checks(pairs + [(b, a) for a, b in pairs],
                                     [item for item in RELATIONS if item[0] in ["==", "/=", ".eq.", ".ne."]]))
    for name, declaration, selector, zero, facets in [
        ("default_declaration", "real", "kind(0.0)", "0.0", ["default-declaration-kind"]),
        ("double_declaration", "double precision", "kind(0.0d0)", "0.0d0",
         ["double-declaration-kind", "double-is-real"]),
    ]:
        bundle.program("S7.4.3.2-004", name, facets, f"""    implicit none
    {declaration} :: value = {zero}
    if (kind(value) /= {selector}) error stop 1
    call check(value)
contains
    subroutine check(x)
        real({selector}), intent(in) :: x
        if (kind(x) /= {selector}) error stop 2
        if (x /= {zero}) error stop 3
    end subroutine
""")
    bundle.program("S7.4.3.2-004", "strict_precision", ["strict-decimal-precision"], """    implicit none
    if (precision(0.0d0) <= precision(0.0)) error stop 1
""")
    for name, query, threshold, facet in [
        ("double_precision_minimum", "precision", 10, "double-precision-at-least-ten"),
        ("double_range_minimum", "range", 37, "double-range-at-least-thirty-seven"),
    ]:
        bundle.program("S7.4.3.2-005", name, [facet], f"""    implicit none
    if ({query}(0.0d0) < {threshold}) error stop 1
    call check({query}(0.0d0))
contains
    subroutine check(value)
        integer, intent(in) :: value
        if (value < {threshold}) error stop 2
    end subroutine
""")
    for name, forms, expected, facets in [
        ("no_exponent_kind", ["0.0", "0.", ".0"], "kind(0.0)", ["no-exponent-default"]),
        ("e_exponent_kind", ["0.0E0", "0e0"], "kind(0.0)", ["e-exponent-default"]),
        ("d_exponent_kind", ["0.0D0", "0d0"], "kind(0.0d0)", ["d-exponent-double"]),
    ]:
        body = "    implicit none\n"
        for index, literal in enumerate(forms, 1):
            body += f"    if (kind({literal}) /= {expected}) error stop {index}\n"
            body += f"    call check({literal})\n"
        body += f"""contains
    subroutine check(value)
        real({expected}), intent(in) :: value
        if (kind(value) /= {expected}) error stop 20
    end subroutine
"""
        bundle.program("S7.4.3.2-006", name, facets, body)
    body = "    implicit none\n    integer, parameter :: kr = kind(0.0), kd = kind(0.0d0)\n"
    for index, (literal, kind_name) in enumerate([
        ("0.0_kr", "kr"), ("0.0e0_kr", "kr"), ("0e0_kr", "kr"),
        ("0.0_kd", "kd"), ("0.0e0_kd", "kd"), ("0e0_kd", "kd"),
    ], 1):
        body += f"    if (kind({literal}) /= {kind_name}) error stop {index}\n"
    bundle.program("S7.4.3.2-006", "named_literal_kinds", ["named-kind"], body)


def complex_syntax(bundle):
    kd = "    integer, parameter :: kd = kind(0.0d0)\n"
    z = kd + "    complex(kd) :: z\n"
    bundle.fixture("R718", "pair_forms", ["parenthesized-pair", "spaced-pair"],
                   subroutine(kd + "    complex(kd) :: a, b\n",
                              "    data a, b /(0.0d0,0.0d0), ( 0.0d0 , 0.0d0 )/\n"))
    for name, bad, repair, facet, messages in [
        ("missing_comma", "(0.0d0 0.0d0)", "(0.0d0,0.0d0)", "comma-required",
         ["Token '0.0d0' (of type 'real') is unexpected here"]),
        ("third_part", "(0.0d0,0.0d0,0.0d0)", "(0.0d0,0.0d0)", "exactly-two-parts",
         ["Token ',' is unexpected here"]),
    ]:
        statement = f"data z /{bad}/"
        bundle.pair("R718", name, subroutine(z, "    " + statement + "\n"),
                    bad, repair, statement, [facet], ["parenthesized-pair"], messages)
    for rule, position in [("R719", 0), ("R720", 1)]:
        def value(part):
            parts = ["0.0d0", "0.0d0"]
            parts[position] = part
            return "(" + ", ".join(parts) + ")"
        for name, parts, facet, premises in [
            ("integer_part_forms", ["0", "+0", "-0", "0_ik"], "signed-integer-part",
             "    integer, parameter :: ik = selected_int_kind(18)\n"),
            ("real_part_forms", ["0.0d0", "+0.0d0", "-0.0d0", "0.0e0_kd"],
             "signed-real-part", ""),
            ("part_alternatives", ["ni", "nr"], "named-part",
             "    integer, parameter :: ni = -1\n    real(kd), parameter :: nr = -0.0_kd\n"),
        ]:
            declarations = kd + premises + f"    complex(kd) :: a({len(parts)})\n"
            statements = "".join(f"    data a({i}) /{value(part)}/\n"
                                 for i, part in enumerate(parts, 1))
            bundle.fixture(rule, name, [facet], subroutine(declarations, statements))
        declarations = z + "    integer, parameter :: n = 0\n    real(kd), parameter :: r = 0.0_kd\n"
        for name, part, repair, facet, messages in [
            ("constant_expression_part", "0.0d0+0.0d0", "0.0d0", "expression-not-part",
             ["Token '+' is unexpected here"]),
            ("signed_name_part", "-r", "r", "sign-before-name",
             ["A sign before a named constant is not permitted in the "
              + ("real" if position == 0 else "imaginary") + " part of a complex literal"]),
        ]:
            bad = value(part)
            good = value(repair)
            statement = "data z /" + bad + "/"
            bundle.pair(rule, name, subroutine(declarations, "    " + statement + "\n"),
                        bad, good, statement, [facet],
                        ["signed-real-part"] if name == "constant_expression_part" else ["named-part"],
                        messages)
    bundle.fixture("C723", "integer_names", ["scalar-integer-names"],
                   subroutine("    integer, parameter :: a = 0, b = 0\n    complex :: z\n",
                              "    data z /(a,b)/\n"))
    bundle.fixture("C723", "real_names", ["scalar-real-names"],
                   subroutine(kd + "    real(kd), parameter :: a = 0.0_kd, b = 0.0_kd\n"
                              "    complex(kd) :: z\n", "    data z /(a,b)/\n"))
    for position, label in [(0, "real"), (1, "imaginary")]:
        rank_message = (("Real" if position == 0 else "Imaginary")
                        + " part of complex literal constant is not scalar [-Wcomplex-constructor]")
        type_message = "operands must be INTEGER, UNSIGNED, REAL, or BOZ"
        for name, declaration, facet, messages, nonfatal in [
            ("rank", "    integer, parameter :: bad(1) = [0]\n", label + "-part-rank",
             ["Scalar PARAMETER required in complex constant", rank_message],
             [dict(compiler="flang", severity="portability", equals_any=[rank_message])]),
            ("logical_type", "    logical, parameter :: bad = .false.\n", label + "-part-type",
             ["Numeric PARAMETER required in complex constant", type_message], []),
            ("character_type", "    character, parameter :: bad = 'a'\n", label + "-part-type",
             ["Numeric PARAMETER required in complex constant", type_message], []),
            ("complex_type", "    complex(kd), parameter :: bad = (0.0d0,0.0d0)\n", label + "-part-type",
             [type_message], []),
        ]:
            parts = ["0.0d0", "0.0d0"]
            parts[position] = "bad"
            wrong = "(" + ", ".join(parts) + ")"
            parts[position] = "scalar"
            repaired = "(" + ", ".join(parts) + ")"
            statement = "data z /" + wrong + "/"
            source = subroutine(z + "    integer, parameter :: scalar = 0\n" + declaration,
                                "    " + statement + "\n")
            bundle.pair("C723", label + "_" + name, source, wrong, repaired, statement,
                        [facet], ["scalar-integer-names"], messages, nonfatal=nonfatal)


def complex_effects(bundle):
    for name, selector, facet in [
        ("default_method", "kind(0.0)", "default-real-correspondence"),
        ("double_method", "kind(0.0d0)", "double-real-correspondence"),
    ]:
        bundle.program("S7.4.3.3-002", name,
                       [facet, "real-component-kind", "imaginary-component-kind", "kind-inquiry"],
                       f"""    implicit none
    integer, parameter :: k = {selector}
    complex(k) :: z = (0.0_k, 0.0_k)
    if (kind(z) /= k) error stop 1
    if (kind(z%re) /= k .or. kind(z%im) /= k) error stop 2
    if (kind(real(z)) /= k .or. kind(aimag(z)) /= k) error stop 3
    if (kind(kind(z)) /= kind(0)) error stop 4
    call real_component(z%re)
    call real_component(z%im)
    call integer_result(kind(z))
contains
    subroutine real_component(value)
        real(k), intent(in) :: value
        if (kind(value) /= k) error stop 5
    end subroutine
    subroutine integer_result(value)
        integer, intent(in) :: value
        if (value /= k) error stop 6
    end subroutine
""")
    bundle.program("S7.4.3.3-003", "default_declaration",
                   ["default-complex-kind", "default-real-component", "default-imaginary-component"],
                   """    implicit none
    complex :: z = (0.0, 0.0)
    if (kind(z) /= kind(0.0)) error stop 1
    call check(z%re)
    call check(z%im)
contains
    subroutine check(value)
        real, intent(in) :: value
        if (kind(value) /= kind(0.0)) error stop 2
    end subroutine
""")
    for name, literal, facet in [
        ("greater_precision_first", "(0.0d0,0.0)", "greater-precision-first"),
        ("greater_precision_second", "(0.0,0.0d0)", "greater-precision-second"),
    ]:
        bundle.program("S7.4.3.3-004", name, [facet], f"""    implicit none
    integer, parameter :: k = kind({literal})
    complex(k) :: z = {literal}
    if (kind({literal}) /= kind(0.0d0)) error stop 1
    if (kind(z%re) /= k .or. kind(z%im) /= k) error stop 2
""")
    bundle.program("S7.4.3.3-004", "same_kind_parts", ["same-kind-parts"], """    implicit none
    integer, parameter :: kr = kind(0.0), kd = kind(0.0d0)
    if (kind((0.0_kr,0.0_kr)) /= kr) error stop 1
    if (kind((0.0_kd,0.0_kd)) /= kd) error stop 2
""")
    for name, literals, expected, facet in [
        ("default_integer_parts", ["(0,0)"], "kind(0.0)", "both-default-integers"),
        ("selected_integer_parts", ["(0_ik,0)", "(0,0_ik)", "(0_ik,0_ik)"],
         "kind(0.0)", "both-selected-integers"),
        ("integer_first", ["(0,0.0d0)", "(0_ik,0.0d0)"],
         "kind(0.0d0)", "integer-first-real-second"),
        ("integer_second", ["(0.0d0,0)", "(0.0d0,0_ik)"],
         "kind(0.0d0)", "real-first-integer-second"),
    ]:
        body = "    implicit none\n"
        if any("_ik" in literal for literal in literals):
            body += "    integer, parameter :: ik = selected_int_kind(18)\n"
        for index, literal in enumerate(literals, 1):
            body += f"    if (kind({literal}) /= {expected}) error stop {index}\n"
            body += f"    call check({literal})\n"
        body += f"""contains
    subroutine check(value)
        complex({expected}), intent(in) :: value
        if (kind(value%re) /= {expected}) error stop 20
        if (kind(value%im) /= {expected}) error stop 21
    end subroutine
"""
        bundle.program("S7.4.3.3-005", name, [facet], body)


def logical_syntax(bundle):
    decl = "    integer, parameter :: lk = kind(.false.)\n"
    bundle.fixture("R725", "literal_forms",
                   ["true-unsuffixed", "false-unsuffixed", "true-named-suffix",
                    "false-named-suffix", "letter-case-use"],
                   subroutine(decl + "    logical(lk) :: a(6)\n",
                              "    data a /.TRUE., .false., .TRUE._lk, .FALSE._lk, .TrUe._LK, .FaLsE._lK/\n"))
    for name, bad, repair, facet, good_facets, messages in [
        ("abbreviated_true", ".T.", ".TRUE.", "true-spelling", ["true-unsuffixed"],
         ["Token '.T.' (of type 'defined operator') is unexpected here"]),
        ("abbreviated_false", ".F.", ".FALSE.", "false-spelling", ["false-unsuffixed"],
         ["Token '.F.' (of type 'defined operator') is unexpected here"]),
        ("missing_dot", ".TRUE", ".TRUE.", "closing-dot", ["true-unsuffixed"],
         ["Token '.' is not recognized"]),
        ("empty_suffix", ".FALSE._", ".FALSE._lk", "suffix-needs-kind", ["false-named-suffix"],
         ["Missing kind-parameter", "Token '_' (of type 'identifier') is unexpected here"]),
    ]:
        statement = "data x /" + bad + "/"
        bundle.pair("R725", name, subroutine(decl + "    logical(lk) :: x\n",
                                            "    " + statement + "\n"),
                    "data x /" + bad + "/", "data x /" + repair + "/",
                    statement, [facet], good_facets, messages)
    bundle.fixture("C733", "supported_names", ["supported-true", "supported-false"],
                   subroutine(decl + "    logical(lk) :: a, b\n",
                              "    data a, b /.true._lk, .false._lk/\n"))
    for truth in ["true", "false"]:
        for spelling in ["digit", "name"]:
            declarations = decl + "    integer, parameter :: bad = 0\n    logical(lk) :: x\n"
            literal = f".{truth}._" + ("0" if spelling == "digit" else "bad")
            statement = "data x /" + literal + "/"
            if spelling == "digit":
                bad, repaired = literal, f".{truth}._lk"
            else:
                bad = "integer, parameter :: bad = 0"
                repaired = "integer, parameter :: bad = kind(.false.)"
            bundle.pair("C733", truth + "_absent_zero_" + spelling,
                        subroutine(declarations, "    " + statement + "\n"),
                        bad, repaired, statement,
                        [f"unsupported-{truth}-{spelling}"], [f"supported-{truth}"],
                        support_messages("logical", 0) + ["Bad kind for logical constant at (1)"],
                        [ABSENT_LOGICAL_PROFILE],
                        DIAGNOSTIC_FAILURES + CONSTANCY_ERRORS)


def logical_effects(bundle):
    bundle.program("S7.4.5-001", "default_values", ["default-truth-values"], """    implicit none
    logical :: t = .true., f = .false.
    if (.not. t) error stop 1
    if (f) error stop 2
    if (t .eqv. f) error stop 3
    if (.not. (t .neqv. f)) error stop 4
    if (.not. (t .eqv. .not. f)) error stop 5
""")
    bundle.program("S7.4.5-002", "mandatory_method", ["one-method-minimum"], """    use iso_fortran_env, only: logical_kinds
    implicit none
    if (size(logical_kinds) < 1) error stop 1
    if (.not. any(logical_kinds == kind(.false.))) error stop 2
    if (.not. any(logical_kinds == kind(.true.))) error stop 3
""")
    bundle.program("S7.4.5-002", "kind_inquiries",
                   ["kind-inquiry", "default-integer-inquiry-result"], """    use iso_fortran_env, only: logical_kinds
    implicit none
    integer, parameter :: first = logical_kinds(1), lk = kind(.false.)
    logical :: a = .false.
    logical(first) :: b = .true._first
    if (kind(a) /= lk) error stop 1
    if (kind(b) /= first) error stop 2
    if (kind(kind(a)) /= kind(0)) error stop 3
    if (kind(kind(b)) /= kind(0)) error stop 4
    call integer_result(kind(a))
    call integer_result(kind(b))
""" + integer_dummy())
    bundle.program("S7.4.5-003", "default_declaration",
                   ["omitted-selector-kind", "explicit-default-agreement"], """    implicit none
    logical :: a = .true., b = .false.
    if (kind(a) /= kind(.false.)) error stop 1
    call check(a, .true.)
    call check(b, .false.)
contains
    subroutine check(value, expected)
        logical(kind(.false.)), intent(in) :: value, expected
        if (kind(value) /= kind(.false.)) error stop 2
        if (value .neqv. expected) error stop 3
    end subroutine
""")
    bundle.program("S7.4.5-004", "unsuffixed_kinds",
                   ["unsuffixed-true", "unsuffixed-false"], """    implicit none
    logical :: a = .true.
    if (kind(.true.) /= kind(.false.)) error stop 1
    if (kind(.false.) /= kind(a)) error stop 2
    if (.not. .true.) error stop 3
    if (.false.) error stop 4
""")
    bundle.program("S7.4.5-004", "default_named_kinds",
                   ["default-named-true", "default-named-false"], """    implicit none
    integer, parameter :: lk = kind(.false.)
    if (kind(.true._lk) /= lk) error stop 1
    if (kind(.false._lk) /= lk) error stop 2
    call check(.true._lk, .true.)
    call check(.false._lk, .false.)
contains
    subroutine check(value, expected)
        logical(lk), intent(in) :: value, expected
        if (value .neqv. expected) error stop 3
    end subroutine
""")
    bundle.program("S7.4.5-004", "aliased_selectors", ["coincident-selectors"], """    implicit none
    integer, parameter :: first = kind(.false.), second = first
    if (kind(.true._first) /= kind(.false._second)) error stop 1
    call first_kind(.true._first, .true.)
    call first_kind(.false._first, .false.)
    call second_kind(.true._second, .true.)
    call second_kind(.false._second, .false.)
contains
    subroutine first_kind(value, expected)
        logical(first), intent(in) :: value, expected
        if (value .neqv. expected) error stop 2
    end subroutine
    subroutine second_kind(value, expected)
        logical(second), intent(in) :: value, expected
        if (value .neqv. expected) error stop 3
    end subroutine
""")


def build(root=ROOT):
    bundle = Bundle()
    legacy_profiles(bundle)
    retained_cases(bundle, root)
    real_syntax(bundle)
    real_effects(bundle)
    complex_syntax(bundle)
    complex_effects(bundle)
    logical_syntax(bundle)
    logical_effects(bundle)
    return bundle


def outputs():
    return {ROOT / path: data for path, data in build().files.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    different = [path for path, data in generated.items()
                 if not path.exists() or path.read_bytes() != data]
    if args.check:
        if different:
            for path in different:
                print(path.relative_to(ROOT))
            raise SystemExit("Numeric literal generated files are missing or stale.")
        print(f"Checked {len(generated)} generated numeric literal files.")
        return
    for path in different:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(generated[path])
    print(f"Wrote {len(different)} of {len(generated)} numeric literal generated files.")


if __name__ == "__main__":
    main()
