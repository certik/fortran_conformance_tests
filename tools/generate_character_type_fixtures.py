#!/usr/bin/env python3
"""Generate the bounded, unprofiled character-type corpus; never run compilers."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import textwrap


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_ERRORS = [
    "not implemented", "not yet implemented", "unimplemented",
    "not supported yet", "not yet supported", "unsupported feature",
    "not currently supported", "implementation limitation",
    "ASR verify", "ASR verifier", "internal compiler error",
    "unexpected end of file", "unexpected eof", "missing end",
    "obsolescent", "obsolete feature",
]
SYNTAX_EXCLUSIONS = IMPLEMENTATION_ERRORS + [
    "not supported", "unsupported", "not available",
    "overflow", "too large", "out of range",
]
SPECIAL_CHARACTERS = " =+-*/\\()[]{},.:;!\"%&~<>?'`^|$#@"
LEGACY_INVALID_SHA256 = "b879e1f2b42ec9deca084b660798d658bf1bc5e1989c53d81b14aa1c3005784e"
LEGACY_FACETS = {
    "component": "forbidden-component",
    "module-function-result": "forbidden-module-result",
    "local-variable": "forbidden-local",
    "allocate-local": "allocate-nondummy",
    "allocate-dummy-deferred": "allocate-deferred-dummy",
    "internal-function-result": "forbidden-internal-result",
}
LEGACY_REPAIRS = {
    "component": ("component_repair", "3"),
    "module-function-result": ("module_result_repair", "3"),
    "local-variable": ("local_repair", "3"),
    "allocate-local": ("allocate_local_repair", "3"),
    "allocate-dummy-deferred": ("allocate_deferred_repair", "3"),
    "internal-function-result": ("internal_result_repair", "1"),
}
LENGTH_CONTEXT_MESSAGES = [
    "must be a dummy argument or a PARAMETER",
    "must be a dummy argument or a named constant",
    "Assumed length character variable must be a dummy argument",
]
FUNCTION_LENGTH_MESSAGES = [
    "must not be assumed length",
    "assumed-length character function must be external",
    "assumed character length is only allowed for external functions",
]
ASSUMED_DECLARATION_MESSAGES = [
    "An assumed (*) type parameter may be used only for a (non-statement function) dummy argument, "
    "associate name, character named constant, or external function result",
]
NONFUNCTION_ASSUMED_MESSAGES = [
    "AssumedLength-string variable should be a dummy variable (intent IN or OUT or INOUT) "
    "or a function return variable.",
]
ALLOCATION_MESSAGES = [
    "must be a dummy argument with assumed character length",
    "must have assumed character length",
    "asterisk character length is only allowed for assumed-length dummy arguments",
    "type parameter must be assumed in the declaration of the allocate-object",
    "Type parameters in type-spec must be assumed if and only if they are assumed "
    "for allocatable object in ALLOCATE",
]
C728_MESSAGES = {
    "array": [
        "CHARACTER(*) function 'f' at (1) cannot be array-valued",
        "An assumed-length CHARACTER(*) function cannot return an array",
    ],
    "pointer": [
        "CHARACTER(*) function 'f' at (1) cannot be pointer-valued",
        "An assumed-length CHARACTER(*) function cannot return a POINTER",
    ],
    "pure": [
        "CHARACTER(*) function 'f' at (1) cannot be pure",
        "An assumed-length CHARACTER(*) function cannot be PURE",
    ],
    "elemental": [
        "An assumed-length CHARACTER(*) function cannot be ELEMENTAL",
    ],
    "recursive": [
        "CHARACTER(*) function 'f' at (1) cannot be recursive",
        "An assumed-length CHARACTER(*) function cannot be RECURSIVE",
    ],
}


def source(text):
    return textwrap.dedent(text).strip("\n") + "\n"


def literal(value, delimiter="'"):
    return delimiter + value.replace(delimiter, delimiter * 2) + delimiter


def identifier(rule, variant, valid=True):
    stem = rule.replace(".", "_").replace("-", "_")
    return stem + ("_valid" if valid else "_invalid") + ("__" + variant if variant else "")


def build_corpus():
    files, cases, repairs = {}, {}, {}

    def put(path, content):
        path = ROOT / path
        if path in files:
            raise ValueError(f"duplicate generated path: {path}")
        files[path] = content if isinstance(content, bytes) else content.encode("ascii")

    def register(name, rule, facets, phase, path, evidence, **extra):
        if name in cases:
            raise ValueError(f"duplicate execution ID: {name}")
        cases[name] = dict(rule=rule, facets=list(facets), phase=phase, path=path,
                           evidence=evidence, **extra)

    def program(rule, variant, facets, body):
        name = identifier(rule, variant)
        evidence = "effect" if rule.startswith("S") else "positive-control"
        path = f"tests/clause07/{name}.f90"
        header = (f"! rule: {rule}\n! covers: {' '.join(facets)}\n"
                  f"! evidence: {evidence}\n! standard: f2023\n")
        put(path, header + "program character_type_case\n" + source(body) + "end program\n")
        register(name, rule, facets, "run", path, evidence, standard="f2023")

    def fixture(name, rule, facets, inputs, phase="compile", diagnostic=None,
                evidence="positive-control", forms=None, relation=""):
        folder = "tests/fixtures/character_type_" + name.lower().replace(":", "_")
        forms = forms or {}
        steps = []
        for filename, content in inputs.items():
            step = Path(filename).stem
            steps.append(dict(id=step, source=filename, language="fortran",
                              form=forms.get(filename, "free"), output=step + ".o",
                              depends_on=[item["id"] for item in steps]))
            put(folder + "/" + filename, content)
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=list(facets), evidence=evidence,
            standard="f2023", files=list(inputs), build=steps,
            expect=dict(phase=phase, outcome="diagnose" if diagnostic else "success"))
        if phase == "compile":
            manifest["expect"]["step"] = steps[-1]["id"]
        else:
            manifest["link"] = dict(objects=[item["output"] for item in steps], output="program")
            manifest["expect"]["exit_code"] = 0
        if diagnostic:
            manifest["expect"]["diagnostic"] = diagnostic
        path = folder + "/fixture.json"
        put(path, json.dumps(manifest, indent=2) + "\n")
        register(name, rule, facets, phase, path, evidence, standard="f2023",
                 source_relation=relation)

    def pair(rule, variant, facets, bad, wrong, repaired, messages, good_facets=None,
             excludes=SYNTAX_EXCLUSIONS, relation_start=None, relation=""):
        bad = source(bad)
        if bad.count(wrong) != 1 or "\n" in wrong or "\n" in repaired:
            raise ValueError(f"{rule}/{variant}: repair must be one unique line-local replacement")
        marked = [n for n, line in enumerate(bad.splitlines(), 1) if wrong in line]
        first = marked[0]
        if relation_start:
            starts = [n for n, line in enumerate(bad.splitlines(), 1) if relation_start in line]
            if len(starts) != 1 or starts[0] > first or not relation:
                raise ValueError(f"{rule}/{variant}: invalid declared source relation")
            first = starts[0]
        diagnostic = dict(file="source.f90", line=first,
                          contains_any=list(messages), excludes_any=list(excludes))
        if first != marked[0]:
            diagnostic["end_line"] = marked[0]
        negative = identifier(rule, variant, False)
        positive = identifier(rule, variant + "_repair")
        fixture(negative, rule, facets, {"source.f90": bad}, diagnostic=diagnostic,
                evidence="effect", relation=relation)
        fixture(positive, rule, good_facets or facets,
                {"source.f90": bad.replace(wrong, repaired, 1)}, relation=relation)
        repairs[negative] = dict(control=positive, wrong=wrong, repaired=repaired,
                                 source=bad, line=marked[0], relation=relation)

    program("S7.4.4.1-001", "positions", ["ordered-positions"], """
        implicit none
        character(4) :: text
        text = 'aB3!'
        if (len(text) /= 4) error stop 1
        if (text(1:1) /= 'a') error stop 2
        if (text(2:2) /= 'B') error stop 3
        if (text(3:3) /= '3') error stop 4
        if (text(4:4) /= '!') error stop 5
        if (text(2:3) /= 'B3') error stop 6
        if (text(1:1) == text(2:2)) error stop 7
    """)
    program("S7.4.4.1-001", "lengths", ["zero-and-positive-lengths"], """
        implicit none
        character(0) :: empty
        character(1) :: one
        character(4) :: four, words(2)
        empty = ''
        one = 'A'
        four = 'abcd'
        words = ['wxyz', 'QRST']
        if (len(empty) /= 0 .or. empty%len /= 0) error stop 1
        if (len(one) /= 1 .or. one%len /= 1) error stop 2
        if (len(four) /= 4 .or. four%len /= 4) error stop 3
        if (len(words) /= 4 .or. words%len /= 4) error stop 4
        if (one /= 'A' .or. four /= 'abcd') error stop 5
        if (words(1) /= 'wxyz' .or. words(2) /= 'QRST') error stop 6
    """)
    program("S7.4.4.1-002", "default_method", ["required-default-method"], """
        implicit none
        character :: bare
        character(kind=kind('A')) :: explicit
        bare = 'B'
        explicit = 'C'
        if (kind(bare) /= kind('A')) error stop 1
        if (kind(explicit) /= kind(bare)) error stop 2
        if (selected_char_kind('DEFAULT') /= kind('A')) error stop 3
        if (bare /= 'B' .or. explicit /= 'C') error stop 4
    """)
    program("S7.4.4.1-002", "named_selection", ["named-method-selection"], """
        use iso_fortran_env, only: character_kinds
        implicit none
        integer :: ascii, ucs
        if (selected_char_kind('DEFAULT') /= kind('A')) error stop 1
        if (selected_char_kind('dEfAuLt   ') /= kind('A')) error stop 2
        if (.not. any(character_kinds == kind('A'))) error stop 3
        ascii = selected_char_kind('ASCII')
        ucs = selected_char_kind('ISO_10646')
        if (ascii < -1 .or. ucs < -1) error stop 4
        if (selected_char_kind('aScIi   ') /= ascii) error stop 5
        if (selected_char_kind('iSo_10646   ') /= ucs) error stop 6
        if (ascii >= 0) then
            if (.not. any(character_kinds == ascii)) error stop 7
        end if
        if (ucs >= 0) then
            if (.not. any(character_kinds == ucs)) error stop 8
        end if
    """)
    program("S7.4.4.1-003", "constructed", ["constructed-character-members"], """
        implicit none
        character :: member
        character(3) :: text
        member = char(0, kind=kind('A'))
        text = 'A' // member // 'Z'
        if (len(member) /= 1 .or. len(text) /= 3) error stop 1
        if (text(1:1) /= 'A' .or. text(3:3) /= 'Z') error stop 2
        if (text(2:2) /= member) error stop 3
    """)

    for variant, selector, count, facet in (
        ("len_kind_keywords", "(len=2+1,kind=kind('A'))", 3, "len-kind-keywords"),
        ("positional", "(2+1,kind('A'))", 3, "positional-len-kind"),
        ("positional_keyword", "(2+1,kind=kind('A'))", 3, "positional-len-keyword-kind"),
        ("kind_only", "(kind=kind('A'))", 1, "kind-only"),
        ("kind_len_keywords", "(kind=kind('A'),len=2+1)", 3, "kind-len-keywords"),
    ):
        value = "ABC"[:count]
        program("R721", variant, [facet], f"""
            implicit none
            character{selector} :: text
            text = '{value}'
            if (len(text) /= {count}) error stop 1
            if (kind(text) /= kind('A')) error stop 2
            if (text /= '{value}') error stop 3
        """)
    program("R722", "parentheses", ["parenthesized-lengths"], """
        implicit none
        character(3) :: positional
        character(len=3) :: keyword
        positional = 'ABC'
        keyword = 'xyz'
        if (len(positional) /= 3 .or. len(keyword) /= 3) error stop 1
        if (positional /= 'ABC' .or. keyword /= 'xyz') error stop 2
        call automatic(3)
    contains
        subroutine automatic(n)
            integer, intent(in) :: n
            character(len=n) :: text
            text = 'DEF'
            if (len(text) /= n) error stop 3
            if (text /= 'DEF') error stop 4
        end subroutine
    """)
    program("R722", "star_forms", ["star-forms"], """
        implicit none
        character*3 :: bare
        character*(2+1) :: expression
        bare = 'ABC'
        expression = 'xyz'
        if (len(bare) /= 3 .or. len(expression) /= 3) error stop 1
        if (bare /= 'ABC' .or. expression /= 'xyz') error stop 2
    """)
    program("R722", "comma", ["optional-comma"], """
        implicit none
        character*3, bare
        character*(3), parenthesized
        bare = 'ABC'
        parenthesized = 'xyz'
        if (len(bare) /= 3 .or. len(parenthesized) /= 3) error stop 1
        if (bare /= 'ABC' .or. parenthesized /= 'xyz') error stop 2
    """)
    program("R722", "selected_length_expression", ["integer-expression-kind"], """
        implicit none
        integer, parameter :: lk = selected_int_kind(4)
        character(len=3_lk) :: selector
        character :: individual*(3_lk)
        selector = 'ABC'
        individual = 'xyz'
        if (len(selector) /= 3 .or. len(individual) /= 3) error stop 1
        if (selector /= 'ABC' .or. individual /= 'xyz') error stop 2
    """)
    program("R723", "expression", ["parenthesized-expression"], """
        implicit none
        character :: positive*(2+1), negative*(-2), empty*(0)
        positive = 'ABC'
        negative = ''
        empty = ''
        if (len(positive) /= 3) error stop 1
        if (len(negative) /= 0 .or. len(empty) /= 0) error stop 2
        if (positive /= 'ABC') error stop 3
    """)
    program("R723", "integer", ["bare-integer-literal"], """
        implicit none
        character*3 :: selector
        character :: individual*3
        selector = 'ABC'
        individual = 'xyz'
        if (len(selector) /= 3 .or. len(individual) /= 3) error stop 1
        if (selector /= 'ABC' .or. individual /= 'xyz') error stop 2
    """)
    program("R723", "assumed_deferred", ["assumed-and-deferred-values"], """
        implicit none
        character, allocatable :: allocated_text*(:)
        character, pointer :: pointed_text*(:)
        character(3), target :: target
        integer :: stat
        target = 'xyz'
        call assumed('ABC')
        allocate(character(3) :: allocated_text, stat=stat)
        if (stat /= 0) error stop 1
        if (.not. allocated(allocated_text)) error stop 2
        allocated_text = 'ABC'
        pointed_text => target
        if (.not. associated(pointed_text)) error stop 3
        if (len(allocated_text) /= 3 .or. len(pointed_text) /= 3) error stop 4
        if (allocated_text /= 'ABC' .or. pointed_text /= 'xyz') error stop 5
    contains
        subroutine assumed(text)
            character, intent(in) :: text*(*)
            if (len(text) /= 3 .or. text /= 'ABC') error stop 6
        end subroutine
    """)
    program("C725", "parenthesized_suffix", ["parenthesized-suffix-admission"], """
        implicit none
        integer, parameter :: ik = kind(0)
        character*(3_ik) :: selector
        character :: individual*(3_ik)
        selector = 'ABC'
        individual = 'xyz'
        if (len(selector) /= 3 .or. len(individual) /= 3) error stop 1
        if (selector /= 'ABC' .or. individual /= 'xyz') error stop 2
    """)
    program("C731", "constant_lengths", ["statement-function-length", "statement-dummy-length"], """
        implicit none
        character(2) :: f, x
        f(x) = x
        if (len(f('AB')) /= 2) error stop 1
        if (f('AB') /= 'AB') error stop 2
        if (f('xy') /= 'xy') error stop 3
    """)
    program("C732", "supported", ["supported-prefix"], """
        implicit none
        integer, parameter :: dk = kind('A')
        if (kind(dk_'ABC') /= dk .or. kind(dk_"xyz") /= dk) error stop 1
        if (len(dk_'ABC') /= 3 .or. len(dk_"xyz") /= 3) error stop 2
        if (dk_'ABC' /= 'ABC' .or. dk_"xyz" /= "xyz") error stop 3
    """)

    program("S7.4.4.2-001", "bare", ["bare-default-kind"], """
        implicit none
        character :: text
        text = 'A'
        if (kind(text) /= kind('A') .or. len(text) /= 1) error stop 1
        call check(text)
    contains
        subroutine check(value)
            character, intent(in) :: value
            if (value /= 'A') error stop 2
        end subroutine
    """)
    program("S7.4.4.2-001", "length_only", ["length-only-default-kind"], """
        implicit none
        character(3) :: positional
        character(len=3) :: keyword
        character*3 :: legacy
        character :: individual*3
        positional = 'ABC'
        keyword = 'DEF'
        legacy = 'ghi'
        individual = 'jkl'
        call check(positional, 'ABC')
        call check(keyword, 'DEF')
        call check(legacy, 'ghi')
        call check(individual, 'jkl')
    contains
        subroutine check(text, expected)
            character(*), intent(in) :: text, expected
            if (kind(text) /= kind('A')) error stop 1
            if (len(text) /= 3 .or. text /= expected) error stop 2
        end subroutine
    """)
    if len(SPECIAL_CHARACTERS) != 32 or len(set(SPECIAL_CHARACTERS)) != 32:
        raise ValueError("the explicit Table 6.1 repertoire must have 32 distinct entries")
    program("S7.4.4.2-002", "repertoire",
            ["letter-values", "digit-values", "underscore-value", "special-character-values"], f"""
        implicit none
        character(*), parameter :: upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        character(*), parameter :: lower = 'abcdefghijklmnopqrstuvwxyz'
        character(*), parameter :: digits = '0123456789'
        character(*), parameter :: special = {literal(SPECIAL_CHARACTERS)}
        character(*), parameter :: repertoire = upper // lower // digits // '_' // special
        integer :: i, j
        if (len(upper) /= 26 .or. len(lower) /= 26) error stop 1
        if (len(digits) /= 10 .or. len(special) /= 32) error stop 2
        if (len(repertoire) /= 95) error stop 3
        do i = 1, 95
            do j = i + 1, 95
                if (repertoire(i:i) == repertoire(j:j)) error stop 4
            end do
        end do
    """)
    program("S7.4.4.2-004", "selector", ["selector-inheritance"], """
        implicit none
        character(len=3) :: first, second, words(2)
        first = 'ABC'
        second = 'def'
        words = ['GHI', 'jkl']
        if (len(first) /= 3 .or. len(second) /= 3) error stop 1
        if (len(words) /= 3 .or. len(words(2)) /= 3) error stop 2
        if (first /= 'ABC' .or. second /= 'def') error stop 3
        if (words(1) /= 'GHI' .or. words(2) /= 'jkl') error stop 4
    """)
    program("S7.4.4.2-004", "entity", ["entity-override"], """
        implicit none
        character(len=5,kind=kind('A')) :: short*2, empty*0, inherited
        character :: standalone*3
        short = 'AB'
        empty = ''
        inherited = 'cdefg'
        standalone = 'XYZ'
        if (len(short) /= 2 .or. len(empty) /= 0 .or. len(inherited) /= 5) error stop 1
        if (len(standalone) /= 3) error stop 2
        if (kind(short) /= kind('A') .or. kind(empty) /= kind('A')) error stop 3
        if (kind(inherited) /= kind('A') .or. kind(standalone) /= kind('A')) error stop 4
        if (short /= 'AB' .or. inherited /= 'cdefg' .or. standalone /= 'XYZ') error stop 5
    """)
    program("S7.4.4.2-004", "component", ["component-override"], """
        implicit none
        type :: record
            character(len=5) :: short*2, empty*0, inherited
        end type
        type(record) :: item
        item%short = 'AB'
        item%empty = ''
        item%inherited = 'cdefg'
        if (len(item%short) /= 2 .or. len(item%empty) /= 0) error stop 1
        if (len(item%inherited) /= 5) error stop 2
        if (item%short /= 'AB' .or. item%inherited /= 'cdefg') error stop 3
    """)
    program("S7.4.4.2-004", "default_one", ["omitted-length-one"], """
        implicit none
        type :: record
            character :: text
        end type
        character :: bare, sibling*3
        character(kind=kind('A')) :: kind_only
        type(record) :: item
        bare = 'A'
        kind_only = 'B'
        sibling = 'cde'
        item%text = 'F'
        if (len(bare) /= 1 .or. len(kind_only) /= 1 .or. len(item%text) /= 1) error stop 1
        if (len(sibling) /= 3) error stop 2
        if (bare /= 'A' .or. kind_only /= 'B' .or. item%text /= 'F') error stop 3
        if (sibling /= 'cde') error stop 4
    """)
    program("S7.4.4.2-005", "constant", ["constant-negative"], """
        implicit none
        character(-2) :: negative
        character(0) :: empty
        character(1) :: one
        negative = ''
        empty = ''
        one = 'X'
        if (len(negative) /= 0 .or. negative%len /= 0) error stop 1
        if (len(empty) /= 0 .or. empty%len /= 0) error stop 2
        if (len(one) /= 1 .or. one /= 'X') error stop 3
    """)
    program("S7.4.4.2-005", "runtime", ["runtime-negative"], """
        implicit none
        call check(-2)
        call check(0)
        call check(3)
    contains
        subroutine check(n)
            integer, intent(in) :: n
            character(len=n) :: text
            text = 'ABC'
            if (len(text) /= max(n,0)) error stop 1
            if (n == 3) then
                if (text /= 'ABC') error stop 2
            end if
        end subroutine
    """)
    program("S7.4.4.2-005", "individual", ["individual-negative"], """
        implicit none
        type :: record
            character(len=-2) :: empty
            character(len=3) :: normal
        end type
        character(len=5) :: overridden*(-2), sibling
        type(record) :: item
        overridden = ''
        sibling = 'ABCDE'
        item%empty = ''
        item%normal = 'xyz'
        if (len(overridden) /= 0 .or. len(sibling) /= 5) error stop 1
        if (len(item%empty) /= 0 .or. len(item%normal) /= 3) error stop 2
        if (sibling /= 'ABCDE' .or. item%normal /= 'xyz') error stop 3
    """)
    program("S7.4.4.2-006", "dummy", ["ordinary-dummy-length"], """
        implicit none
        call check('', 0)
        call check('AB', 2)
        call check('ABCDE', 5)
        call prefix('ABCDE')
    contains
        subroutine check(text, expected)
            character(*), intent(in) :: text
            integer, intent(in) :: expected
            if (len(text) /= expected) error stop 1
            if (expected > 0) then
                if (text(1:1) /= 'A') error stop 2
            end if
            if (expected == 5) then
                if (text(5:5) /= 'E') error stop 3
            end if
        end subroutine
        subroutine prefix(text)
            character(3), intent(in) :: text
            if (len(text) /= 3 .or. text /= 'ABC') error stop 4
        end subroutine
    """)
    program("S7.4.4.2-006", "optional", ["optional-dummy-presence"], """
        implicit none
        integer :: observed
        call check(observed)
        if (observed /= -1) error stop 1
        call check(observed, '')
        if (observed /= 0) error stop 2
        call check(observed, 'ABC')
        if (observed /= 3) error stop 3
    contains
        subroutine check(observed, text)
            integer, intent(out) :: observed
            character(*), optional, intent(in) :: text
            if (present(text)) then
                observed = len(text)
                if (len(text) == 3) then
                    if (text /= 'ABC') error stop 4
                end if
            else
                observed = -1
            end if
        end subroutine
    """)
    program("S7.4.4.2-006", "allocatable_dummy", ["allocatable-assumed-dummy"], """
        implicit none
        character(3), allocatable :: text
        integer :: stat
        allocate(text, stat=stat)
        if (stat /= 0) error stop 1
        text = 'ABC'
        call check(text)
    contains
        subroutine check(value)
            character(*), allocatable, intent(in) :: value
            if (.not. allocated(value)) error stop 2
            if (len(value) /= 3) error stop 3
            if (value /= 'ABC') error stop 4
        end subroutine
    """)
    program("S7.4.4.2-006", "pointer_dummy", ["pointer-assumed-dummy"], """
        implicit none
        character(3), target :: target
        character(3), pointer :: text
        target = 'xyz'
        text => target
        call check(text)
    contains
        subroutine check(value)
            character(*), pointer, intent(in) :: value
            if (.not. associated(value)) error stop 1
            if (len(value) /= 3) error stop 2
            if (value /= 'xyz') error stop 3
        end subroutine
    """)
    for variant, attribute, status_function, initialization in (
        ("allocate_assumed", "allocatable", "allocated", ""),
        ("allocate_assumed_pointers", "pointer", "associated", " => null()"),
    ):
        program("S7.4.4.2-006", variant, ["allocate-effective-lengths"], f"""
            implicit none
            character(2), {attribute} :: short{initialization}
            character(5), {attribute} :: long{initialization}
            call establish(short, long)
            if (.not. {status_function}(short)) error stop 1
            if (.not. {status_function}(long)) error stop 2
            if (len(short) /= 2 .or. len(long) /= 5) error stop 3
            if (short /= 'AB' .or. long /= 'CDEFG') error stop 4
            deallocate(short, long)
        contains
            subroutine establish(a, b)
                character(*), {attribute}, intent(inout) :: a, b
                integer :: stat
                allocate(character(*) :: a, b, stat=stat)
                if (stat /= 0) error stop 5
                if (.not. {status_function}(a)) error stop 6
                if (.not. {status_function}(b)) error stop 7
                if (len(a) /= 2 .or. len(b) /= 5) error stop 8
                a = 'AB'
                b = 'CDEFG'
            end subroutine
        """)
    program("S7.4.4.2-006", "guard", ["guard-selector-length"], """
        implicit none
        call check('', 0)
        call check('AB', 2)
        call check('ABCDE', 5)
    contains
        subroutine check(value, expected)
            class(*), intent(in) :: value
            integer, intent(in) :: expected
            select type (text => value)
            type is (character(len=*,kind=kind('A')))
                if (len(text) /= expected .or. kind(text) /= kind('A')) error stop 1
                if (expected > 0) then
                    if (text(1:1) /= 'A') error stop 2
                end if
                if (expected == 5) then
                    if (text /= 'ABCDE') error stop 3
                end if
            class default
                error stop 4
            end select
        end subroutine
    """)
    external = source("""
        function character_external(expected) result(text)
            implicit none
            integer, intent(in) :: expected
            character(*) :: text
            if (len(text) /= expected) error stop 1
            text = 'ABCDE'
        end function
    """)
    fixture(identifier("S7.4.4.2-006", "external"), "S7.4.4.2-006", ["external-caller-length"],
            {"external.f90": external, "main.f90": source("""
                program p
                    implicit none
                    call short_path()
                    call long_path()
                contains
                    subroutine short_path()
                        character(2), external :: character_external
                        character(2) :: text
                        text = character_external(2)
                        if (len(character_external(2)) /= 2) error stop 2
                        if (text /= 'AB') error stop 3
                    end subroutine
                    subroutine long_path()
                        character(5), external :: character_external
                        character(5) :: text
                        text = character_external(5)
                        if (len(character_external(5)) /= 5) error stop 4
                        if (text /= 'ABCDE') error stop 5
                    end subroutine
                end program
            """)}, phase="run", evidence="effect")
    fixture(identifier("S7.4.4.2-006", "access_routes"), "S7.4.4.2-006", ["invoking-and-passing-access"],
            {"declarations.f90": source("""
                module character_declarations
                    implicit none
                    character(3), external :: character_external
                end module
            """), "external.f90": external, "routes.f90": source("""
                subroutine local_route()
                    implicit none
                    character(3), external :: character_external
                    character(3) :: text
                    text = character_external(3)
                    if (text /= 'ABC') error stop 2
                end subroutine
                subroutine host_route()
                    implicit none
                    character(3), external :: character_external
                    call inner()
                contains
                    subroutine inner()
                        character(3) :: text
                        text = character_external(3)
                        if (text /= 'ABC') error stop 3
                    end subroutine
                end subroutine
                subroutine use_route()
                    use character_declarations, only: character_external
                    implicit none
                    character(3) :: text
                    text = character_external(3)
                    if (text /= 'ABC') error stop 4
                end subroutine
                subroutine dummy_route(f)
                    implicit none
                    character(3), external :: f
                    character(3) :: text
                    text = f(3)
                    if (text /= 'ABC') error stop 5
                    call forwarded(f)
                end subroutine
                subroutine forwarded(f)
                    implicit none
                    character(3), external :: f
                    character(3) :: text
                    text = f(3)
                    if (text /= 'ABC') error stop 6
                end subroutine
            """), "main.f90": source("""
                program p
                    implicit none
                    character(3), external :: character_external
                    call local_route()
                    call host_route()
                    call use_route()
                    call dummy_route(character_external)
                end program
            """)}, phase="run", evidence="effect")

    program("S7.4.4.3-001", "default", ["omitted-prefix-default"], """
        implicit none
        if (kind('') /= kind('A') .or. kind("") /= kind('A')) error stop 1
        if (kind('ABC') /= kind('A') .or. kind("xyz") /= kind('A')) error stop 2
        if (len('') /= 0 .or. len("") /= 0) error stop 3
        if (len('ABC') /= 3 .or. len("xyz") /= 3) error stop 4
        call check('ABC')
        call check("ABC")
    contains
        subroutine check(value)
            character(*), intent(in) :: value
            if (len(value) /= 3 .or. value /= 'ABC') error stop 5
        end subroutine
    """)
    program("S7.4.4.3-001", "named_prefix", ["named-prefix-value"], """
        implicit none
        integer, parameter :: dk = kind('A')
        integer, parameter :: selected_default = selected_char_kind('DEFAULT')
        if (kind(dk_'ABC') /= dk .or. kind(dk_"xyz") /= dk) error stop 1
        if (len(dk_'ABC') /= 3 .or. len(dk_"xyz") /= 3) error stop 2
        if (kind(selected_default_'ABC') /= dk) error stop 3
        if (kind(selected_default_"xyz") /= dk) error stop 4
        if (len(selected_default_'ABC') /= 3) error stop 5
        if (len(selected_default_"xyz") /= 3) error stop 6
        if (dk_'ABC' /= selected_default_"ABC") error stop 7
        if (dk_"xyz" /= selected_default_'xyz') error stop 8
    """)
    graphic_body = """
        implicit none
        character(*), parameter :: a = ' A  a '
        character(*), parameter :: b = "a  A  "
        if (len(a) /= 6 .or. len(b) /= 6) error stop 1
        if (a(2:2) == a(5:5)) error stop 2
        if (a(2:2) /= b(4:4) .or. a(5:5) /= b(1:1)) error stop 3
        if (a(1:1) /= ' ' .or. a(3:4) /= '  ') error stop 4
        if (a(6:6) /= ' ' .or. b(2:3) /= '  ') error stop 5
        if (b(5:6) /= '  ') error stop 6
    """
    program("S7.4.4.3-002", "free_graphics", ["free-required-graphics"], graphic_body)
    fixed_lines = ["program p"] + source(graphic_body).splitlines() + ["end program"]
    if any(len(line) > 66 for line in fixed_lines):
        raise ValueError("fixed-form test statement exceeds its 66-character field")
    fixed = "".join(("      " + line).ljust(72) + "\n" for line in fixed_lines)
    fixture(identifier("S7.4.4.3-002", "fixed_graphics"), "S7.4.4.3-002",
            ["fixed-required-graphics"], {"source.f90": fixed}, phase="run",
            forms={"source.f90": "fixed"}, evidence="effect")
    for variant, delimiter, facet in (
        ("apostrophe", "'", "apostrophe-delimiter-exclusion"),
        ("quotation", '"', "quotation-delimiter-exclusion"),
    ):
        program("S7.4.4.3-003", variant, [facet], f"""
            implicit none
            character(*), parameter :: text = {literal('AbC', delimiter)}
            if (len({literal('', delimiter)}) /= 0) error stop 1
            if (len({literal('X', delimiter)}) /= 1) error stop 2
            if (len({literal('AbC', delimiter)}) /= 3) error stop 3
            if (text(1:1) /= 'A' .or. text(2:2) /= 'b' .or. text(3:3) /= 'C') error stop 4
        """)
    program("S7.4.4.3-003", "opposite_delimiters", ["other-delimiter-data"], """
        implicit none
        character(*), parameter :: a = 'A"B'
        character(*), parameter :: b = "A'B"
        if (len(a) /= 3 .or. len(b) /= 3) error stop 1
        if (a(2:2) /= '"') error stop 2
        if (b(2:2) /= "'") error stop 3
        if (a(2:2) == b(2:2)) error stop 4
        if (a(1:1) /= 'A' .or. a(3:3) /= 'B') error stop 5
        if (b(1:1) /= 'A' .or. b(3:3) /= 'B') error stop 6
    """)
    for variant, delimiter, opposite, facet in (
        ("apostrophe", "'", '"', "apostrophe-doubling-and-count"),
        ("quotation", '"', "'", "quotation-doubling-and-count"),
    ):
        program("S7.4.4.3-004", variant, [facet], f"""
            implicit none
            character(*), parameter :: text = {literal('A' + delimiter + 'B', delimiter)}
            if (len(text) /= 3) error stop 1
            if (text(1:1) /= 'A' .or. text(3:3) /= 'B') error stop 2
            if (text(2:2) /= {literal(delimiter, opposite)}) error stop 3
        """)
    boundary = ["implicit none"]
    for label, delimiter in (("a", "'"), ("q", '"')):
        boundary += [
            f"character(*), parameter :: {label} = {literal(delimiter + 'X' + delimiter, delimiter)}",
            f"character(*), parameter :: {label}2 = {literal(delimiter * 2, delimiter)}",
        ]
    boundary += [
        "if (len(a) /= 3 .or. len(q) /= 3) error stop 1",
        "if (len(a2) /= 2 .or. len(q2) /= 2) error stop 2",
        "if (a(2:2) /= 'X' .or. q(2:2) /= 'X') error stop 3",
        "if (a(1:1) /= a2(1:1) .or. a(3:3) /= a2(2:2)) error stop 4",
        "if (q(1:1) /= q2(1:1) .or. q(3:3) /= q2(2:2)) error stop 5",
        "if (a(1:1) == q(1:1)) error stop 6",
    ]
    program("S7.4.4.3-004", "boundaries", ["boundary-and-repeated-pairs"], "\n".join(boundary))
    for variant, delimiter, facet in (
        ("apostrophe", "'", "empty-apostrophe"), ("quotation", '"', "empty-quotation"),
    ):
        empty = literal("", delimiter)
        program("S7.4.4.3-005", variant, [facet], f"""
            implicit none
            integer, parameter :: dk = kind('A')
            if (len({empty}) /= 0 .or. len(dk_{empty}) /= 0) error stop 1
            if (kind({empty}) /= dk .or. kind(dk_{empty}) /= dk) error stop 2
            if (len({empty} // 'ABC') /= 3) error stop 3
            if (len('ABC' // {empty}) /= 3) error stop 4
            if ({empty} // 'ABC' /= 'ABC') error stop 5
            if ('ABC' // {empty} /= 'ABC') error stop 6
        """)
    context = ["implicit none"]
    for label, delimiter in (("a", "'"), ("q", '"')):
        context += [f"character(*), parameter :: {label} = {literal(delimiter, delimiter)}"]
    for number, delimiter in enumerate(("'", '"'), 1):
        context += [
            f"if (len({literal('', delimiter)}) /= 0) error stop {number}",
            f"if (len({literal(' ', delimiter)}) /= 1) error stop {number+2}",
            f"if (len({literal(delimiter, delimiter)}) /= 1) error stop {number+4}",
        ]
    context += ["if (a == ' ' .or. q == ' ' .or. a == q) error stop 7"]
    program("S7.4.4.3-005", "context", ["empty-versus-interior-pair"], "\n".join(context))

    for variant, alphabet, count, facet in (
        ("uppercase", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 26, "uppercase-order"),
        ("digits", "0123456789", 10, "digit-order"),
        ("lowercase", "abcdefghijklmnopqrstuvwxyz", 26, "lowercase-order"),
    ):
        program("S7.4.4.4-002", variant, [facet], f"""
            implicit none
            character(*), parameter :: alphabet = '{alphabet}'
            integer :: i
            if (len(alphabet) /= {count}) error stop 1
            do i = 1, {count-1}
                if (.not. (alphabet(i:i) < alphabet(i+1:i+1))) error stop 2
            end do
        """)
    for variant, first, last, facet in (
        ("blank_uppercase", "A", "Z", "blank-digit-uppercase-alternatives"),
        ("blank_lowercase", "a", "z", "blank-digit-lowercase-alternatives"),
    ):
        program("S7.4.4.4-002", variant, [facet], f"""
            implicit none
            logical :: digits_first, letters_first
            digits_first = ' ' < '0' .and. '0' < '9' .and. '9' < '{first}'
            letters_first = ' ' < '{first}' .and. '{first}' < '{last}' .and. '{last}' < '0'
            if (.not. (digits_first .or. letters_first)) error stop 1
        """)
    program("S7.4.4.4-004", "default", ["default-ascii-order"], """
        implicit none
        call check(lge('ONE','TWO'), .false.)
        call check(lgt('ONE','TWO'), .false.)
        call check(lle('ONE','TWO'), .true.)
        call check(llt('ONE','TWO'), .true.)
        call check(lge('TWO','ONE'), .true.)
        call check(lgt('TWO','ONE'), .true.)
        call check(lle('TWO','ONE'), .false.)
        call check(llt('TWO','ONE'), .false.)
        call check(lge('ONE','ONE'), .true.)
        call check(lgt('ONE','ONE'), .false.)
        call check(lle('ONE','ONE'), .true.)
        call check(llt('ONE','ONE'), .false.)
    contains
        subroutine check(value, expected)
            logical, intent(in) :: value, expected
            if (value .neqv. expected) error stop 1
        end subroutine
    """)
    program("S7.4.4.4-004", "padding_empty", ["padding-and-empty"], """
        implicit none
        call equal('A', 'A  ')
        call equal('A  ', 'A')
        call equal('', '   ')
        call equal('   ', '')
        call equal('', '')
        if (.not. llt('ONEZ', 'TWOA')) error stop 1
        if (lge('ONEZ', 'TWOA')) error stop 2
        if (.not. lgt('TWOA', 'ONEZ')) error stop 3
        if (lle('TWOA', 'ONEZ')) error stop 4
    contains
        subroutine equal(a, b)
            character(*), intent(in) :: a, b
            if (.not. lge(a,b) .or. .not. lle(a,b)) error stop 5
            if (lgt(a,b) .or. llt(a,b)) error stop 6
        end subroutine
    """)
    program("S7.4.4.4-004", "iachar_consistency", ["iachar-consistency"], """
        implicit none
        character(*), parameter :: sample = 'OTX'
        integer :: i, j
        do i = 1, 3
            if (achar(iachar(sample(i:i))) /= sample(i:i)) error stop 1
            do j = 1, 3
                if (lle(sample(i:i),sample(j:j))) then
                    if (iachar(sample(i:i)) > iachar(sample(j:j))) error stop 2
                end if
            end do
        end do
    """)

    pair("R721", "len_keyword_positional_kind", ["len-keyword-positional-kind-exclusion"], """
        subroutine p
            implicit none
            integer, parameter :: dk = kind('A')
            character(len=3,dk) :: text
        end subroutine
    """, "len=3,dk", "len=3,kind=dk", [
        "Token 'dk' (of type 'identifier') is unexpected here",
        "KIND= is required after LEN=",
        "positional kind is not permitted after LEN=",
        "Syntax error in CHARACTER declaration: positional type parameters cannot follow a keyword argument",
    ], good_facets=["len-kind-keywords"])
    pair("R721", "kind_keyword_positional_length", ["kind-keyword-positional-length-exclusion"], """
        subroutine p
            implicit none
            integer, parameter :: dk = kind('A')
            character(kind=dk,3) :: text
        end subroutine
    """, "kind=dk,3", "kind=dk,len=3", [
        "Token '3' (of type 'integer') is unexpected here",
        "LEN= is required after KIND=",
        "positional length is not permitted after KIND=",
        "Syntax error in CHARACTER declaration: positional type parameters cannot follow a keyword argument",
    ], good_facets=["kind-len-keywords"])
    pair("R723", "bare_expression", ["bare-expression-exclusion"], """
        subroutine p
            implicit none
            character*2+1 text
        end subroutine
    """, "character*2+1", "character*(2+1)", [
        "Token '+' (of type '+') is unexpected here",
        "character length expression must be parenthesized",
    ], good_facets=["parenthesized-expression"])
    pair("C724", "negative", ["negative-kind"], """
        subroutine p
            implicit none
            character(kind=-1) :: text
        end subroutine
    """, "kind=-1", "kind=kind('A')", [
        "kind -1 is not supported for character",
        "kind -1 not supported for type character",
        "character(kind=-1) is not a supported type",
        "kind -1 is not a supported character kind",
        "KIND value (-1) not valid for CHARACTER",
    ], good_facets=["supported-kind"], excludes=IMPLEMENTATION_ERRORS + [
        "constant integer", "constant expression", "kind parameter syntax",
        "character kind parameters are not supported",
    ])
    fixture("C724_valid__supported", "C724", ["supported-kind"], {"source.f90": source("""
        subroutine p
            implicit none
            character(kind=kind('A')) :: text
        end subroutine
    """)})
    pair("C725", "bare_suffix", ["bare-suffix-exclusion"], """
        subroutine p
            implicit none
            integer, parameter :: ik = kind(0)
            character*3_ik text
        end subroutine
    """, "character*3_ik", "character*3", [
        "does not allow a kind parameter",
        "kind parameter is not allowed in a character length",
        "kind parameter not permitted in character length",
    ])
    pair("C726", "allocate_mixed", ["allocate-mixed-list"], """
        subroutine p(assumed_dummy)
            implicit none
            character(*), allocatable, intent(inout) :: assumed_dummy
            character(:), allocatable :: local_deferred
            allocate(character(*) :: assumed_dummy,local_deferred)
        end subroutine
    """, "assumed_dummy,local_deferred", "assumed_dummy", ALLOCATION_MESSAGES)
    fixture("C727_valid__unused_dummy_function", "C727", ["dummy-function-declaration"],
            {"source.f90": source("""
                subroutine p(f)
                    implicit none
                    character(*), external :: f
                end subroutine
            """)})
    fixture("C727_valid__caller_assumed_repair", "C727", ["fixed-length-external-declaration"],
            {"source.f90": source("""
                program p
                    implicit none
                    character(3), external :: f
                end program
            """)},
            relation="The historical repair ID is retained as a fixed-length external declaration admission control, not an invalid/repair contrast.")
    for variant, attribute, facet in (
        ("pure", "pure ", "pure-exclusion"),
        ("elemental", "impure elemental ", "elemental-exclusion"),
        ("recursive", "recursive ", "recursive-attribute-exclusion"),
    ):
        pair("C728", variant, [facet], f"""
            {attribute}character(*) function f(n)
                implicit none
                integer, intent(in) :: n
                f = 'ABC'
            end function
        """, "character(*)", "character(3)", C728_MESSAGES[variant] + [
            f"assumed character length is not allowed for a {variant} function",
            f"assumed-length character function cannot be {variant}",
        ])
    pair("C728", "array", ["array-exclusion"], """
        function f() result(value)
            implicit none
            character(*) :: value(2)
            value = 'ABC'
        end function
    """, "character(*)", "character(3)", C728_MESSAGES["array"] + [
        "assumed-length character function cannot be an array",
        "assumed-length character function result must be scalar",
    ], relation_start="function f()", relation="Function header and its scalar-type/rank declaration jointly specify an assumed-length array result.")
    pair("C728", "pointer", ["pointer-exclusion"], """
        function f() result(value)
            implicit none
            character(*), pointer :: value
            character(3), target, save :: target = 'ABC'
            value => target
        end function
    """, "character(*)", "character(3)", C728_MESSAGES["pointer"] + [
        "assumed-length character function cannot be a pointer",
        "assumed-length character function result cannot have the POINTER attribute",
    ], relation_start="function f()", relation="Function header and result declaration jointly specify assumed length and POINTER; the target is live and length three.")
    comma_messages = [
        "optional comma in a length-selector is permitted only in a type-declaration-stmt",
        "character length comma is only allowed in a type declaration",
        "comma after character length is not allowed in this context",
    ]
    pair("C729", "component_comma", ["component-exclusion"], """
        module p
            implicit none
            type :: record
                character*3, text
            end type
        end module
    """, "character*3,", "character*3", comma_messages)
    pair("C729", "function_comma", ["function-prefix-exclusion"], """
        character*3, function f()
            implicit none
            f = 'ABC'
        end function
    """, "character*3,", "character*3", comma_messages)
    pair("C729", "allocate_comma", ["allocate-exclusion"], """
        subroutine p
            implicit none
            character(:), allocatable :: text
            allocate(character*3, :: text)
        end subroutine
    """, "character*3,", "character*3", comma_messages)
    pair("C730", "double_colon", ["double-colon-exclusion"], """
        subroutine p
            implicit none
            character*3, :: text
        end subroutine
    """, "character*3,", "character*3", [
        "character length comma is not permitted with a double-colon separator",
        "optional comma requires no double-colon",
        "comma after character length is not allowed before ::",
        "Token '::' is unexpected here",
    ])
    for variant, declarations, wrong in (
        ("function_length", "character(2) :: x\ncharacter(n) :: f", "character(n) :: f"),
        ("dummy_length", "character(2) :: f\ncharacter(n) :: x", "character(n) :: x"),
    ):
        bad = ("subroutine p(n)\nimplicit none\ninteger, intent(in) :: n\n"
               + declarations + "\nf(x) = x\nend subroutine\n")
        messages = ([
            "character length of a statement function must be constant",
            "Character-valued statement function 'f' at (1) must have constant length",
        ] if variant == "function_length" else [
            "character length of a statement function dummy argument must be constant",
            "Character-valued argument 'x' of statement function at (1) must have constant length",
        ])
        pair("C731", variant,
             ["statement-function-length" if variant == "function_length" else "statement-dummy-length"],
             bad, wrong, wrong.replace("(n)", "(2)"), messages,
             relation="The character length declaration and the immediately following statement-function definition establish the constant-length condition.")
        negative = identifier("C731", variant, False)
        manifest_path = ROOT / cases[negative]["path"]
        manifest = json.loads(files[manifest_path])
        manifest["expect"]["diagnostic"]["end_line"] = repairs[negative]["line"] + 1
        files[manifest_path] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    for variant, bad_literal, good_literal, facet, admission in (
        ("apostrophe_closer", "'ABC\"", "'ABC'", "unterminated-apostrophe", "apostrophe-form"),
        ("quotation_closer", "\"ABC'", '"ABC"', "unterminated-quotation", "quotation-form"),
    ):
        pair("R724", variant, [facet],
             "subroutine p\nimplicit none\ncharacter(*), parameter :: text = "
             + bad_literal + "\nend subroutine\n",
             bad_literal, good_literal, [
                 "Unterminated character constant",
                 "unterminated character literal",
                 "unterminated string",
                 "character literal constant is not closed",
                 "Incomplete character literal",
             ], good_facets=[admission])
    pair("R724", "prefix_separator", ["prefix-separator"], """
        subroutine p
            implicit none
            integer, parameter :: dk = kind('A')
            character(*), parameter :: text = dk'ABC'
        end subroutine
    """, "dk'ABC'", "dk_'ABC'", [
        "kind prefix must be followed by an underscore",
        "missing underscore after character kind prefix",
        "Token ''ABC'' (of type 'string') is unexpected here",
    ], good_facets=["named-prefix-form", "apostrophe-form"])

    # The retained container remains the one source of the six isolated inputs.
    sys.path.insert(0, str(ROOT / "tests"))
    from run_tests import isolated_cases
    legacy = ROOT / "tests/clause07/C726_invalid.f90"
    if hashlib.sha256(legacy.read_bytes()).hexdigest() != LEGACY_INVALID_SHA256:
        raise ValueError("retained C726 source differs from the reviewed container")
    contracts = {}
    for line, rule, member, bounds, bad in isolated_cases(str(legacy), "C726"):
        facet = LEGACY_FACETS[member]
        variant, length = LEGACY_REPAIRS[member]
        if bad.count("character(*)") != 1:
            raise ValueError(f"C726/{member}: expected one isolated character star")
        messages = ([
            "A CHARACTER component must have a constant length",
            "with CHARACTER attribute at (1) must have constant character length",
            "character length of component 's' must be constant",
            "Character length of component 's' needs to be a constant specification expression",
        ] + NONFUNCTION_ASSUMED_MESSAGES + ASSUMED_DECLARATION_MESSAGES
                    if member == "component" else FUNCTION_LENGTH_MESSAGES + ASSUMED_DECLARATION_MESSAGES
                    if member in ("module-function-result", "internal-function-result")
                    else ALLOCATION_MESSAGES if member.startswith("allocate-")
                    else LENGTH_CONTEXT_MESSAGES + NONFUNCTION_ASSUMED_MESSAGES + ASSUMED_DECLARATION_MESSAGES)
        diagnostic = dict(contains_any=list(messages), excludes_any=SYNTAX_EXCLUSIONS)
        relation = "Exact original marker point."
        if member in ("module-function-result", "internal-function-result"):
            diagnostic.update(line=line-1, end_line=line)
            relation = "The function statement and adjacent character result declaration establish the nonexternal assumed-length result; the enclosing PRINT is excluded."
        contracts[member] = dict(facets=[facet], outcome="diagnose", diagnostic=diagnostic)
        name = identifier("C726", variant)
        fixture(name, "C726", [facet], {"source.f90": bad.replace("character(*)", f"character({length})", 1)},
                relation=relation)
        invalid_id = "C726_invalid:" + member
        repairs[invalid_id] = dict(control=name, wrong="character(*)",
                                  repaired=f"character({length})", source=bad, line=line,
                                  relation=relation)
        register(invalid_id, "C726", [facet], "compile", "tests/clause07/C726_invalid.f90",
                 "effect", standard="", retained=True, source_relation=relation)
    put("tests/clause07/C726_invalid.cases.json",
        json.dumps(dict(schema_version=1, cases=contracts), indent=2) + "\n")
    register("C726_valid", "C726", ["ordinary-dummies", "named-constant", "character-type-guard"],
             "run", "tests/clause07/C726_valid.f90", "positive-control",
             standard="f2023", retained=True)
    return files, cases, repairs


def outputs():
    return build_corpus()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, cases, _ = build_corpus()
    stale = []
    for path, content in files.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if stale:
        parser.exit(1, "stale generated character files:\n" + "\n".join(stale) + "\n")
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(cases)} character executions; no compiler invoked.")


if __name__ == "__main__":
    main()
