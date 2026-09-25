#!/usr/bin/env python3
"""Finite constructor values observed through real assumed-rank dummy data objects."""
import argparse
import copy
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.8"
CATALOGUE = "doc/catalogues/array_constructors.json"
VIEW = "doc/fortran_2023_7_8.md"
LEGACY_ELIGIBLE = {
    "S7.8-001": ["rank-one-and-scalar-sequence", "higher-rank-flattening"],
    "S7.8-008": ["default-increment-sequence", "positive-and-negative-strides", "multiple-body-values",
                "nested-dependent-bounds", "array-valued-body-sequence"],
    "S7.8-009": ["typed-empty-and-zero-trip", "zero-sized-array-ac-value", "empty-character-parameters"],
}
NEW_ELIGIBLE = {
    "S7.8-001": ["mixed-shapes-and-empty-source", "value-expression-state-source-use"],
    "S7.8-003": ["inferred-integer-kind", "inferred-character-length"],
    "S7.8-005": ["character-padding-and-truncation", "nonzero-dependent-character-length"],
    "S7.8-008": ["kind-and-host-scope-source-use"],
}
ELIGIBLE = copy.deepcopy(LEGACY_ELIGIBLE)
for _rule, _facets in NEW_ELIGIBLE.items():
    ELIGIBLE.setdefault(_rule, []).extend(_facets)
CHECKS = """module array_value_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, finish_checks
contains
subroutine check_integer(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'CHECK_INTEGER',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(*), intent(in) :: label
logical, intent(in) :: actual,expected
if (actual .neqv. expected) then
print *, 'CHECK_LOGICAL',label,'ACTUAL',actual,'EXPECTED',expected
error stop 2
end if
checked=checked+1
end subroutine check_logical
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked/=expected) then
print *, 'CHECK_COUNT',checked,'EXPECTED',expected
error stop 3
end if
end subroutine finish_checks
end module array_value_checks
"""


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__array_constructor_value_" + variant


def operation(name, expression, values, category="integer", length=None, controls=(), kind=None,
              feature_mutations=(), observer="dummy"):
    if category not in ("integer", "character"):
        raise ValueError("only ordinary INTEGER/default CHARACTER constructor values are authorized")
    if category == "character" and length is None:
        raise ValueError("a CHARACTER operation needs an independent length expectation")
    if observer not in ("dummy", "associate"):
        raise ValueError("unknown observation strategy")
    return dict(name=name, expression=expression, expected=list(values), category=category,
                expected_length=length, controls=list(controls), expected_kind=kind,
                feature_mutations=list(feature_mutations), observer=observer)


def guard(label, expression, expected, family, location):
    return dict(label=label, expression=expression, expected=expected, family=family, location=location,
                category="logical" if type(expected) is bool else "integer")


def literal(value):
    return (".true." if value else ".false.") if type(value) is bool else str(value)


def guard_code(item):
    return f"call check_{item['category']}('{item['label']}',{item['expression']},{literal(item['expected'])})\n"


def block_code(item):
    name, expression, values = item["name"], item["expression"], item["expected"]
    size_class = "empty" if not values else "nonempty"
    if item["observer"] == "associate":
        alias = "a_" + name
        guards = [guard(name + ":rank", f"rank({alias})", 1, "associate-rank", name),
                  guard(name + ":size", f"size({alias})", len(values),
                        "associate-size-" + size_class, name)]
        if item.get("expected_kind") is not None:
            guards.append(guard(name + ":kind", f"kind({alias})", item["expected_kind"],
                                "associate-kind", name))
        if item["category"] == "character":
            guards.append(guard(name + ":length", f"len({alias})", item["expected_length"],
                                "associate-character-length", name))
        for index, value in enumerate(values, 1):
            if item["category"] == "integer":
                guards.append(guard(name + f":value-{index}", f"{alias}({index})", value,
                                    "integer-element", name))
            else:
                if not isinstance(value, str) or "'" in value:
                    raise ValueError("the bounded CHARACTER oracle is a plain independently supplied literal")
                guards.append(guard(name + f":value-{index}", f"{alias}({index})=='{value}'", True,
                                    "character-element", name))
        main = f"associate({alias}=>{expression})\n" + "".join(guard_code(g) for g in guards) + "end associate\n"
        return main, "", guards
    direct = [
        guard(name + ":size", f"size({expression})", len(values), "constructor-size-" + size_class, "main"),
    ]
    if item.get("expected_kind") is not None:
        direct.append(guard(name + ":kind", f"kind({expression})", item["expected_kind"],
                            "constructor-kind", "main"))
    if item["category"] == "character":
        direct.append(guard(name + ":length", f"len({expression})", item["expected_length"],
                            "constructor-character-length", "main"))
    dummy_type = "integer" if item["category"] == "integer" else "character(len=*)"
    rank = guard(name + ":rank", "rank(a)", 1, "assumed-rank-argument", name)
    observer = f"subroutine observe_{name}(a)\n{dummy_type}, intent(in) :: a(..)\n"
    observer += guard_code(rank) + "select rank(a)\nrank(1)\n"
    observed = [guard(name + ":argument-size", "size(a)", len(values), "argument-size-" + size_class, name)]
    if item["category"] == "character":
        observed.append(guard(name + ":argument-length", "len(a)", item["expected_length"],
                              "argument-character-length", name))
    for index, value in enumerate(values, 1):
        if item["category"] == "integer":
            observed.append(guard(name + f":value-{index}", f"a({index})", value, "integer-element", name))
        else:
            if not isinstance(value, str) or "'" in value:
                raise ValueError("the bounded CHARACTER oracle is a plain independently supplied literal")
            observed.append(guard(name + f":value-{index}", f"a({index})=='{value}'", True, "character-element", name))
    observer += "".join(guard_code(g) for g in observed)
    observer += f"rank default\nprint *, 'UNEXPECTED_RANK','{name}',rank(a)\nerror stop 4\nend select\n"
    observer += f"end subroutine observe_{name}\n"
    main = "".join(guard_code(g) for g in direct) + f"call observe_{name}({expression})\n"
    return main, observer, direct + [rank] + observed


def accepts(guards, observed):
    wanted = {g["label"]: g["expected"] for g in guards}
    return set(wanted) == set(observed) and all(
        type(observed[label]) is type(expected) and observed[label] == expected for label, expected in wanted.items())


def bind_guard_spans(source, guards, check_count):
    lines = source.splitlines()
    result = []
    for item in guards:
        text = guard_code(item).rstrip("\n")
        if lines.count(text) != 1:
            raise ValueError("guard source is not uniquely located")
        expected = literal(item["expected"])
        offset = text.rfind("," + expected + ")") + 1
        if offset <= 0:
            raise ValueError("expected guard literal is not isolated")
        result.append(dict(**item, line=lines.index(text) + 1, first_column=offset + 1,
                           last_column=offset + len(expected), source_text=text, expected_text=expected,
                           failure_marker="CHECK_LOGICAL" if item["category"] == "logical" else "CHECK_INTEGER"))
    completion = f"call finish_checks({check_count})"
    if lines.count(completion) != 1:
        raise ValueError("completion guard is not unique")
    expected = str(check_count)
    offset = completion.index("(") + 1
    result.append(dict(label="completion-count", expression="checked", expected=check_count,
                       category="integer", family="completion-count", location="main",
                       line=lines.index(completion) + 1, first_column=offset + 1,
                       last_column=offset + len(expected), source_text=completion, expected_text=expected,
                       failure_marker="CHECK_COUNT"))
    return result


def bind_argument_spans(source, operations):
    lines = source.splitlines()
    result = []
    for item in operations:
        if item["observer"] == "associate":
            prefix = f"associate(a_{item['name']}=>"
            suffix = ")"
        else:
            prefix = f"call observe_{item['name']}("
            suffix = ")"
        text = prefix + item["expression"] + suffix
        if lines.count(text) != 1:
            raise ValueError("observer actual argument is not uniquely located")
        result.append(dict(operation=item["name"], expression=item["expression"], category=item["category"],
                           line=lines.index(text) + 1, first_column=len(prefix) + 1,
                           last_column=len(prefix) + len(item["expression"]), source_text=text,
                           observer=item["observer"]))
    return result


def bind_setup_spans(source, setup_inputs):
    lines = source.splitlines()
    result = []
    for item in setup_inputs:
        text = item["source_text"]
        if lines.count(text) != 1:
            raise ValueError("setup input source is not uniquely located: " + text)
        first = text.index(item["expected_text"]) + 1
        result.append(dict(item, line=lines.index(text) + 1, first_column=first,
                           last_column=first + len(item["expected_text"]) - 1))
    return result


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="array_constructor_value", root=root)

    def add(self, rule, variant, facets, declarations, setup, operations, premises, setup_inputs=(),
            post_guards=()):
        name = identifier(rule, variant)
        if name in self.cases or not operations or not any(op["expected"] for op in operations):
            raise ValueError("a unique case needs a nonempty value-control operation")
        main, observers, guards = "", "", []
        for item in operations:
            code, observer, observations = block_code(item)
            main += code
            observers += observer
            guards += observations
        post_guards = list(post_guards)
        for item in post_guards:
            main += guard_code(item)
        guards += post_guards
        if len({g["label"] for g in guards}) != len(guards):
            raise ValueError("duplicate observation label")
        source = CHECKS + "program p\nuse array_value_checks, only: check_integer, check_logical, finish_checks\nimplicit none\n"
        source += "\n".join(declarations) + ("\n" if declarations else "")
        source += "\n".join(setup) + ("\n" if setup else "")
        source += main + f"call finish_checks({len(guards)})\ncontains\n" + observers + "end program p\n"
        spans = bind_guard_spans(source, guards, len(guards))
        representative = {}
        for item in spans:
            representative.setdefault(item["family"], item["label"])
        folder = "tests/fixtures/array_constructor_value_" + name.lower()
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=list(facets), standard="f2023", evidence="effect",
            files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0))
        self.put(folder + "/source.f90", source)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(
            rule=rule, facets=list(facets), kind="valid", phase="run", evidence="effect",
            path=folder + "/fixture.json", declarations=list(declarations), setup=list(setup),
            operations=operations, observations=guards, expected_check_count=len(guards),
            guard_bindings=spans, argument_bindings=bind_argument_spans(source, operations),
            setup_bindings=bind_setup_spans(source, setup_inputs),
            sensitivity_representatives=representative, premises=premises)


def sequence_case(c):
    operations = [
        operation("scalars", "[11,13,17]", [11,13,17]),
        operation("matrix", "[5,m,23]", [5,11,13,17,19,23]),
    ]
    c.add("S7.8-001", "sequence", LEGACY_ELIGIBLE["S7.8-001"], ["integer :: m(2,2)"],
          ["m(1,1)=11", "m(2,1)=13", "m(1,2)=17", "m(2,2)=19"], operations,
          "The four matrix cells are independently assigned by name. Direct SIZE inspects actual constructor "
          "expressions; complete assumed-rank dummy data objects receive those expressions and expose their actual rank. "
          "RANK(a) precedes SELECT RANK; only RANK(1) permits size and literal-index observations. "
          "No constructor, RESHAPE, PACK or expected array initializes the matrix or derives the oracle.")


def ordinary_loop_case(c):
    operations = [
        operation("default_step", "[(i,i=1,3)]", [1,2,3],
                  controls=[dict(variable="i", initial=1, terminal=3, increment=1, explicit_step=False)]),
        operation("positive_step", "[(i,i=1,5,2)]", [1,3,5],
                  controls=[dict(variable="i", initial=1, terminal=5, increment=2, explicit_step=True)]),
        operation("negative_step", "[(i,i=5,1,-2)]", [5,3,1],
                  controls=[dict(variable="i", initial=5, terminal=1, increment=-2, explicit_step=True)]),
        operation("multiple_body", "[(i,10*i,i=1,2)]", [1,10,2,20],
                  controls=[dict(variable="i", initial=1, terminal=2, increment=1, explicit_step=False)]),
    ]
    c.add("S7.8-008", "ordinary_loops",
          ["default-increment-sequence", "positive-and-negative-strides", "multiple-body-values"],
          ["integer :: i"], [], operations,
          "Separate ordinary implied DO scopes infer default INTEGER from the containing scalar declaration, with finite limits and nonzero "
          "increments. The independent literals distinguish default, positive, negative and per-iteration multiple-body "
          "placement. The statement entity inherits only type/parameters, not host attributes or a host value. "
          "No uninitialized host read, post-scope read or callback-evaluation order is used. R783 remains pending.")


def dependent_body_case(c):
    operations = [
        operation("nested", "[((10*i+j,j=1,i),i=1,3)]", [11,21,22,31,32,33],
                  controls=[dict(variable="i", initial=1, terminal=3, increment=1, explicit_step=False),
                            dict(variable="j", initial=1, terminal="i", increment=1, explicit_step=False,
                                 defined_outer_dependency="i")]),
        operation("array_body", "[(vector+i,i=1,2)]", [32,38,33,39],
                  controls=[dict(variable="i", initial=1, terminal=2, increment=1, explicit_step=False)]),
    ]
    c.add("S7.8-008", "dependent_bodies", ["nested-dependent-bounds", "array-valued-body-sequence"],
          ["integer :: vector(2)", "integer :: i,j"], ["vector(1)=31", "vector(2)=37"], operations,
          "The inner j limit reads the already defined outer i, never its own uninitialized statement entity. "
          "Containing scalar INTEGER i/j declarations supply types only; their values are never read. "
          "Array-valued vector+i bodies contribute their two elements per iteration. Vector setup and all six/four "
          "result markers are independent named scalar literals.")


def integer_empty_case(c):
    operations = [
        operation("integer_control", "[7]", [7]),
        operation("typed_empty", "[integer ::]", []),
        operation("zero_trip", "[(i,i=1,0)]", [],
                  controls=[dict(variable="i", initial=1, terminal=0, increment=1, explicit_step=False)]),
        operation("empty_source", "[11,empty,13]", [11,13]),
    ]
    c.add("S7.8-009", "integer_empty", ["typed-empty-and-zero-trip", "zero-sized-array-ac-value"],
          ["integer :: empty(0)", "integer :: i"], [], operations,
          "The ordinary explicit-shape empty(0) is always defined. Typed-empty syntax and a nonempty zero-trip body "
          "are separate operations within one program. Direct zero size and associated assumed-rank observations, "
          "plus nonempty [7]/[11,empty,13] checks, are nonvacuous. Scalar INTEGER i supplies a type only; "
          "no unallocated source, empty assertion loop, host value or host final-index query is used.")


def character_empty_case(c):
    operations = [
        operation("character_control", "[character(len=3) :: 'abc']", ["abc"], "character", 3),
        operation("character_fixed", "[character(len=3) ::]", [], "character", 3),
        operation("character_runtime", "[character(len=n) ::]", [], "character", 3),
    ]
    c.add("S7.8-009", "character_empty", ["empty-character-parameters"],
          ["integer :: n"], ["n=3"], operations,
          "Runtime n is an ordinary separately defined INTEGER, not PARAMETER. Both empty expressions have no ac-value, "
          "so no zero-trip index-dependent character-length premise is introduced. Direct SIZE/LEN and complete "
          "assumed-rank, assumed-length CHARACTER data-object consumers preserve actual rank and length. RANK(a) "
          "precedes SELECT RANK and any rank-specific access; a nonempty abc control validates "
          "the observer without fixed-length destination masking or character conversion claims.")


def feature(reordered, dropped, duplicated):
    return [
        dict(id="reorder-same-multiset", replacement=reordered, category="reorder"),
        dict(id="drop-ac-value", replacement=dropped, category="drop"),
        dict(id="duplicate-ac-value", replacement=duplicated, category="duplicate"),
    ]


def additional_state_case(c):
    operations = [
        operation("mixed", "[one,empty,three]", [61,73,79,83], observer="associate",
                  feature_mutations=feature("[three,empty,one]", "[empty,three]", "[one,empty,three,one]")),
        operation("state", "[ptr,alloc]", [41,43,47,53],
                  feature_mutations=feature("[alloc,ptr]", "[ptr]", "[ptr,alloc,ptr]"), observer="associate"),
    ]
    setup_inputs = [
        dict(id="backing-1", source_text="backing(1)=41", expected_text="41", replacement="42"),
        dict(id="backing-2", source_text="backing(2)=43", expected_text="43", replacement="44"),
        dict(id="alloc-1", source_text="alloc(1)=47", expected_text="47", replacement="48"),
        dict(id="alloc-2", source_text="alloc(2)=53", expected_text="53", replacement="54"),
        dict(id="one-1", source_text="one(1)=61", expected_text="61", replacement="62"),
        dict(id="three-1", source_text="three(1)=73", expected_text="73", replacement="74"),
        dict(id="three-2", source_text="three(2)=79", expected_text="79", replacement="80"),
        dict(id="three-3", source_text="three(3)=83", expected_text="83", replacement="84"),
    ]
    c.add("S7.8-001", "state_and_mixed", NEW_ELIGIBLE["S7.8-001"],
          ["integer, target :: backing(2)", "integer, pointer :: ptr(:)",
           "integer, allocatable :: alloc(:)", "integer :: one(1), empty(0), three(3)"],
          ["backing(1)=41", "backing(2)=43", "ptr=>backing", "allocate(alloc(2))",
           "alloc(1)=47", "alloc(2)=53", "one(1)=61", "three(1)=73",
           "three(2)=79", "three(3)=83"], operations,
          "The mixed constructor has rank-one sources of extents one, zero and three. The empty source "
          "contributes no element, so the exact sequence is 61,73,79,83. The state constructor uses a live "
          "associated pointer and an allocated allocatable array whose individual elements are assigned by name; "
          "the constructor contributes their data values 41,43,47,53 rather than status bits. No source setup "
          "uses another constructor or an array-producing intrinsic.", setup_inputs)


def type_parameter_case(c):
    operations = [
        operation("integer_kind", "[left_k,right_k]", [89,97], kind="k", observer="associate",
                  feature_mutations=feature("[right_k,left_k]", "[left_k]", "[left_k,right_k,left_k]")),
        operation("character_inferred", "[left_c,right_c]", ["AB","CD"], "character", 2, observer="associate",
                  feature_mutations=feature("[right_c,left_c]", "[left_c]", "[left_c,right_c,left_c]")),
    ]
    setup_inputs = [
        dict(id="left-k", source_text="left_k=89", expected_text="89", replacement="90"),
        dict(id="right-k", source_text="right_k=97", expected_text="97", replacement="98"),
        dict(id="left-c", source_text="left_c='AB'", expected_text="'AB'", replacement="'AX'"),
        dict(id="right-c", source_text="right_c='CD'", expected_text="'CD'", replacement="'CY'"),
    ]
    c.add("S7.8-003", "type_parameters", NEW_ELIGIBLE["S7.8-003"],
          ["integer, parameter :: k=kind(0)", "integer(kind=k) :: left_k, right_k",
           "character(len=2) :: left_c, right_c"],
          ["left_k=89", "right_k=97", "left_c='AB'", "right_c='CD'"], operations,
          "The integer kind is named by the symbolic parameter k=KIND(0), and the constructor KIND is "
          "checked against k rather than a numeric kind code. Character inference is observed from two "
          "defined CHARACTER(2) sources, with LEN 2 and exact element strings AB/CD. The ordinary "
          "runtime CHARACTER(LEN=n) plan remains pending because gfortran 16.1 loses that length when "
          "the expression is associated with a data object.", setup_inputs)


def character_conversion_case(c):
    operations = [
        operation("pad_truncate", "[character(len=3) :: 'A','BCDE']", ["A  ","BCD"],
                  "character", 3, observer="associate",
                  feature_mutations=feature("[character(len=3) :: 'BCDE','A']",
                                            "[character(len=3) :: 'A']",
                                            "[character(len=3) :: 'A','BCDE','A']")),
        operation("dependent_substrings", "[character(len=3) :: (text(1:i),i=1,3)]",
                  ["A  ","AB ","ABC"], "character", 3, observer="associate",
                  feature_mutations=feature("[character(len=3) :: (text(1:i),i=3,1,-1)]",
                                            "[character(len=3) ::]",
                                            "[character(len=3) :: (text(1:i),i=1,3),(text(1:i),i=1,3)]")),
    ]
    c.add("S7.8-005", "character_conversion", NEW_ELIGIBLE["S7.8-005"],
          ["character(len=3), parameter :: text='ABC'", "integer :: i"], [], operations,
          "The explicit CHARACTER(LEN=3) constructor pads 'A' to 'A  ' and truncates 'BCDE' to 'BCD'. "
          "The nonzero implied DO reads the constant text(1:i) for i=1,2,3, all in range, and then the "
          "same explicit LEN=3 conversion yields 'A  ','AB ','ABC'. LEN is asserted before element "
          "comparisons so blank-padded character equality cannot hide a wrong constructor length.")


def host_scope_case(c):
    operations = [
        operation("host_scope", "[77,(i,i=1_k,3_k),88]", [77,1,2,3,88], kind="k",
                  observer="associate",
                  controls=[dict(variable="i", initial="1_k", terminal="3_k", increment=1,
                                 explicit_step=False, host_value_after=99)],
                  feature_mutations=feature("[(i,i=1_k,3_k),77,88]",
                                            "[77,(i,i=1_k,3_k)]",
                                            "[77,(i,i=1_k,3_k),88,77]")),
    ]
    setup_inputs = [dict(id="host-i", source_text="i=99", expected_text="99", replacement="98")]
    c.add("S7.8-008", "host_scope", NEW_ELIGIBLE["S7.8-008"],
          ["integer, parameter :: k=kind(0)", "integer(kind=k) :: i"], ["i=99"], operations,
          "The ac-do variable i has the symbolic default kind k and is a statement entity separate from "
          "the host variable i. The constructor sequence is 77,1,2,3,88, and after the constructor the "
          "host variable is still 99. This does not assert side-effect callback order, a zero step, "
          "post-scope ac-do-variable access or distinct non-default kind availability.", setup_inputs,
          [guard("host_i_after", "i", 99, "host-scope", "main")])


def build_corpus(root=ROOT):
    c = Corpus(root)
    sequence_case(c)
    additional_state_case(c)
    type_parameter_case(c)
    character_conversion_case(c)
    ordinary_loop_case(c)
    dependent_body_case(c)
    host_scope_case(c)
    integer_empty_case(c)
    character_empty_case(c)
    if c.coverage() != {rule:set(facets) for rule,facets in ELIGIBLE.items()}:
        raise ValueError("case partition differs from the seventeen authorized facets")
    return c.files, c.cases


def externally_bound_facets(root=ROOT):
    root = Path(root)
    local_rules = {item["id"] for item in json.loads((root / CATALOGUE).read_text())["requirements"]}
    result = {}
    for path in (root / "tests/fixtures").glob("*/fixture.json"):
        if path.parent.name.startswith("array_constructor_value_"):
            continue
        data = json.loads(path.read_text())
        if data.get("rule") in local_rules:
            result.setdefault(data["rule"], set()).update(data.get("facets", []))
    return result


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned array-constructor value paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def synced_catalogue(catalogue, specs, root=ROOT):
    result = copy.deepcopy(catalogue)
    external = externally_bound_facets(root)
    for requirement in result["requirements"]:
        cases = [s for s in specs.values() if s["rule"] == requirement["id"]]
        covered = {facet for case in cases for facet in case["facets"]}
        for facet in covered:
            if facet not in requirement["facets"]:
                raise ValueError("unknown represented facet")
            requirement["pending"].pop(facet, None)
        externally_covered = external.get(requirement["id"], set())
        if not externally_covered <= set(requirement["facets"]):
            raise ValueError("unknown externally represented facet")
        if set(requirement["pending"]) != set(requirement["facets"]) - covered - externally_covered:
            raise ValueError("missing unselected source plan")
        if cases:
            value_text = (
                f"\n\nFinite value implementation: {len(cases)} shared valid run-phase programs represent "
                f"{len(covered)} selected facets using independent default-INTEGER/default-CHARACTER literal guards. "
                "Direct constructor SIZE/LEN retain their own argument rules where they are used. RANK requires a "
                "data object: legacy operations associate the actual constructor expression with an explicit "
                "INTENT(IN) assumed-rank dummy a(..), while the added exact state/type/character operations use "
                "ASSOCIATE names bound to the constructor expression. RANK is checked on that data object before "
                "rank-one size/length/indexed observations. Legacy assumed-rank observers retain an explicit "
                "unexpected-rank failure branch, not a rank-one dummy/destination proxy. "
                "Ordinary implied DO indices infer INTEGER from containing scalar i/j declarations, which supply "
                "types only; no host value or inherited attributes are used and R783 remains pending. "
                "Source setup never uses another constructor, RESHAPE or PACK. Empty contexts retain nonempty controls. "
                "Every other plan stays pending and all administrative review fields are preserved; changed source "
                "material may make the existing source review stale, never silently renewed.").lstrip()
            requirement["oracle"] = owned_paragraph(requirement["oracle"], "Finite value implementation:", value_text)
            prefix = "No runtime witness is implemented. "
            if requirement["oracle_limitation"].startswith(prefix):
                requirement["oracle_limitation"] = (
                    "Finite runtime witnesses do not confer independent adjudication. "
                    + requirement["oracle_limitation"][len(prefix):])
    return result


CONDITIONS = """## Source and oracle qualifications

Authority is J3/24-007,18December2023,688 physical PDF pages,
SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Original7.8 occupies PDF114-116 and ends before Clause8 on PDF117.
The31base/100fine/131accounting units,26requirements and107facet IDs remain.
The independently reviewed source was already registered on main; its review
state/fingerprint/rationale are preserved, not replaced by author approval.

Only S7.8-001's first four, S7.8-003's first two, S7.8-005's two
CHARACTER conversion facets, S7.8-008's first six and S7.8-009's first three
facets are represented. S7.8-001 evaluation-order, S7.8-003 runtime explicit
length plus nonintrinsic and deferred-boundary, S7.8-005 numeric/enum/BOZ,
S7.8-006 dynamic-type, S7.8-008 control-evaluation, and S7.8-009
state/optional-evaluation plans remain pending. No R/C, other S,
dynamic/representation/source-use diagnostic policy or processor-kind
availability claim is added.

All payloads and limits are small default INTEGER values, default INTEGER(KIND(0))
values, or ordinary default CHARACTER. Matrix cells11/13/17/19, vector
cells31/37, pointer/allocatable cells41/43/47/53, mixed-source cells61/73/79/83
and type-parameter cells89/97 are assigned individually by name. No expected
Fortran array or setup constructor, RESHAPE, PACK, matching reordered construction
or processor inquiry supplies an expected sequence. Element order follows9.5.3.3,
not a memory-layout or function-call-order claim.

Ordinary implied DO initiation/execution follows11.1.7.4.1/.3. The optional
inline INTEGER type-spec is omitted; containing-scope scalar INTEGER i/j
declarations supply type/parameters under19.4p1/p2/p5. The ac-do names remain
separate statement entities and inherit no other attributes. Their host values
are not used as loop values; the dedicated host-scope fixture separately checks
that the host i value99 survives the constructor. Steps are nonzero. Inner
j=1:i reads the defined outer i; no own uninitialized bound, mutable function-order
counter, DO CONCURRENT or optional-evaluation absence oracle is used. This is a
separate grammar-alternative change: the original inline syntax was valid and
its observed processor failures remain history. No R783 facet is claimed.

RANK16.9.171p3 requires a DATA OBJECT. Under5.4.3.2.1/.2/.3,6.2.3R604/R605
and9.2R902/C901/C902, a constructor computation is not a constant or variable.
Its result is a data entity under5.4.3.3, not automatically a data object.
Legacy operations pass exact constructor expressions to complete internal
INTEGER or CHARACTER(LEN=*),INTENT(IN) dummies a(..), without POINTER,
ALLOCATABLE,CODIMENSION or VALUE. Those are real assumed-rank dummy data objects
under8.5.8.7p1/R827/C839. Added exact state/type/character operations instead
use ASSOCIATE names bound to the constructor expression, because both qualifying
toolchains preserve the constructor value there and gfortran does not preserve
all added exact cases through assumed-rank argument association. RANK is checked
on the data object before size/length/indexed guards; legacy SELECT RANK
observers retain an explicit RANK DEFAULT failure. No declared rank-one dummy or
destination is used as a rank proxy. Primitive expectations and completion
counts are regenerated from the case table, not hand-edited after generation.

SIZE16.9.194 and LEN16.9.122 still inspect actual constructor expressions or
ASSOCIATE names bound to those expressions: their own argument paragraphs permit
an array or a CHARACTER entity, respectively, unlike RANK's DATA OBJECT
restriction. Internal explicit interfaces meet15.4.2.1/.2. Ordinary argument
association under15.5.2.4/.5 permits any actual rank for an assumed-rank dummy
and preserves actual rank, extents, element order and assumed length in legacy
operations. Lower bounds are one. SELECT RANK under11.1.10.1/.2/.3 and19.5.1.6
preserves type/parameters and selects the rank-specific entity with those bounds;
11.1.3.3 forbids defining the read-only association. Size guards precede element
reads. An assumed or associated CHARACTER length is observed directly, never
masked by a fixed-length destination.

The ordinary INTEGER empty(0) is always defined under19.6.2. Typed-empty
[INTEGER ::] and a syntactically nonempty zero-trip implied DO both have
rank1/size0. The [7] and [11,empty,13] controls ensure actual nonempty value
observations. Empty CHARACTER(LEN=3) and runtime n=3 have no ac-value, so they
do not invoke the zero-trip CHARACTER ac-value length restriction. The abc
control has matching source/target length3 and makes no padding/conversion claim.

Pointer and allocatable source-state observations first establish association,
allocation, extents and element definitions, then read constructor elements through
an assumed-rank observer. They do not infer pointer broadcasting, allocation-status
elements, finalization, deallocation or pointer/allocatable inheritance by the
constructor expression.

CHARACTER constructor observations always check LEN explicitly and use length-3
expected strings such as 'A  ' and 'BC ', not shorter operands that would compare
equal by blank padding. The substring fixture has nonzero iteration count and
constant text='ABC'; it does not cover the zero-trip p5 restriction.

Each primitive expected value is a scalar literal at its real source guard.
Each program also checks its completed guard count. Separate single-span
wrong-oracle probes are permitted only on a processor that genuinely runs the
current parent program; successful compile/link and the intended failed runtime
guard are required. Separate bounded scalar/rank-two actual-argument probes exercise
the unconstrained descriptor and must fail at RANK(a) before any element access.
Such finite sensitivity is not universal intrinsic correctness, a conformance
case, or approval.

AVFR-001 invalidates the15direct RANK expression sites in the frozen5161d38e
parent packet. Its original15processor rows and35wrong-oracle executions remain
unchanged empirical history, not qualification of these corrected programs.
The original inline-type syntax rejections, GNU CHARACTER ICE and LF empty
CHARACTER LEN failure are separate observations; no claim attributes them to RANK.

Source-valid compiler failures keep run-phase expectations. Actual f2018
reference modes are not relabelled f2023. No optional kind/profile, BOZ,
REAL/COMPLEX accuracy, dynamic/PDT/pointer/allocatable state, C/image or compiler
work is introduced. Candidate29fc461 is outside this packet and is not used.
"""


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    total = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    checks = sum(s["expected_check_count"] for s in specs.values())
    text = (
        "# Fortran 2023: 7.8 Array constructors - ordinary value implementation\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Source and case/evidence adjudications remain separate content-bound records.\n\n"
        f"The value corpus has **{len(specs)} shared valid run/effect programs**, **{checks} primitive value/shape/length guards** "
        f"and one completion guard per program. The shared catalogue now has **{total-pending} of {total} facets represented; "
        f"{pending} remain PENDING.** No source/case/link/inventory approval is implied.\n\n"
        + CONDITIONS + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.8 -->\n\n")
    text += "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    text += "<!-- END GENERATED 7.8 -->\n\n## Exact finite constructor and guard plans\n\n"
    for name, spec in specs.items():
        text += f"### `{name}`\n\n**Primary:** {spec['rule']}; **phase/evidence:** run / effect.\n\n"
        text += "**Facets:** " + ", ".join("`" + f + "`" for f in spec["facets"]) + ".\n\n"
        text += spec["premises"] + "\n\n"
        for op in spec["operations"]:
            text += f"* `{op['name']}`: actual `{op['expression']}`; independent indexed literals `{op['expected']}`"
            if op["category"] == "character":
                text += f"; actual LEN must be `{op['expected_length']}`"
            text += ".\n"
        text += f"\nThe exact completed primitive guard count is `{spec['expected_check_count']}`. "
        text += "Guard families: " + ", ".join("`" + f + "`" for f in spec["sensitivity_representatives"]) + ".\n\n"
    text += "## Complete finite pending plans\n\n"
    text += "Every unselected map below is retained exactly from the canonical source; incidental feature use does not clear it.\n\n"
    for requirement in catalogue["requirements"]:
        if requirement["pending"]:
            text += f"### Pending {requirement['id']}\n\n"
            for facet, plan in requirement["pending"].items():
                text += f"* **`{facet}`** - {plan}\n"
            text += "\n"
    return text + (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_array_constructor_value_fixtures.py --check` checks exact inputs, "
        "case/facet partition and both source-view regions. Targeted regressions independently check "
        "literal sequences, source setup, scope/definedness, direct SIZE/LEN, assumed-rank data objects and real guard spans. "
        "Full-program sensitivity records retain original/mutated bytes and exact actual execution contexts.\n\n"
        "The1937-case base and nine links stay intact. The existing reviewed source record can become "
        "stale after the implementation metadata changes, and the observational inventory changes through "
        "new cases/context; neither is renewed. Independent source/fixture/oracle adjudication remains separate.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, specs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs, ROOT)
    view = render_view(updated, specs)
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p,b in files.items() if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob("array_constructor_value_*/*") if p.is_file()}
        stale += [str(p.relative_to(ROOT)) for p in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale array-constructor value packet: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    represented = sum(len(spec["facets"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files for {len(specs)} runtime programs "
          f"and {represented} facets.")


if __name__ == "__main__":
    main()
