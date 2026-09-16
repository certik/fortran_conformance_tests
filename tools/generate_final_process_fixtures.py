#!/usr/bin/env python3
"""Finite automatic-finalization process witnesses; no compiler or review actions."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import textwrap

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.6.2"
CATALOGUE = "doc/catalogues/derived_types_7_5_6_2.json"
VIEW = "doc/fortran_2023_7_5_6_2.md"
ELIGIBLE = {
    "S7.5.6.2-001": [
        "scalar-exact-match", "array-exact-match", "kind-tuple-dispatch",
        "exact-array-before-elemental", "assumed-rank-fallback",
        "no-matching-own-final", "private-final-name"],
    "S7.5.6.2-002": [
        "plain-component-recursion", "sibling-order-independent", "array-element-components",
        "zero-sized-outer-array", "pointer-target-exclusion"],
    "S7.5.6.2-003": [
        "own-before-components", "components-before-parent",
        "parent-without-own-child-final", "recursive-parent-process"],
    "S7.5.6.2-004": ["independent-entity-control"],
}


def text(value):
    return textwrap.dedent(value).strip() + "\n"


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__final_process_" + variant


LOG_MODULE = """module final_log
implicit none
private
integer, parameter :: capacity=64
integer, save :: nlog=0
integer, save :: log_kind(capacity)=0, log_token(capacity)=0
public :: record_event, reset_log, expect_log, expect_before
contains
subroutine reset_log()
nlog=0
log_kind=0
log_token=0
end subroutine reset_log
subroutine record_event(kind,token)
integer, intent(in) :: kind,token
if (nlog >= capacity) error stop 101
nlog=nlog+1
log_kind(nlog)=kind
log_token(nlog)=token
end subroutine record_event
subroutine report_actual()
integer :: i
print *, 'ACTUAL_COUNT',nlog
do i=1,nlog
print *, 'ACTUAL_EVENT',log_kind(i),log_token(i)
end do
end subroutine report_actual
subroutine expect_log(kinds,tokens)
integer, intent(in) :: kinds(:),tokens(:)
integer :: i
if (size(kinds) /= size(tokens)) error stop 102
if (nlog /= size(kinds)) then
call report_actual()
error stop 103
end if
do i=1,size(kinds)
if (count(log_kind(1:nlog)==kinds(i) .and. log_token(1:nlog)==tokens(i)) /= &
    count(kinds==kinds(i) .and. tokens==tokens(i))) then
call report_actual()
error stop 104
end if
end do
end subroutine expect_log
subroutine expect_before(left_kind,left_token,right_kind,right_token)
integer, intent(in) :: left_kind,left_token,right_kind,right_token
integer :: i,last_left,first_right
last_left=0
first_right=nlog+1
do i=1,nlog
if (log_kind(i)==left_kind .and. log_token(i)==left_token) last_left=i
if (log_kind(i)==right_kind .and. log_token(i)==right_token) first_right=min(first_right,i)
end do
if (last_left==0 .or. first_right==nlog+1) then
call report_actual()
error stop 105
end if
if (last_left>=first_right) then
call report_actual()
error stop 106
end if
end subroutine expect_before
end module final_log
"""


def model_accepts(expected, edges, actual):
    expected = [tuple(e) for e in expected]
    actual = [tuple(e) for e in actual]
    if Counter(expected) != Counter(actual):
        return False
    for left, right in edges:
        a = [i for i, e in enumerate(actual) if e == tuple(left)]
        b = [i for i, e in enumerate(actual) if e == tuple(right)]
        if not a or not b or max(a) >= min(b):
            return False
    return True


def case_accepts(observations, actual_traces):
    return len(observations) == len(actual_traces) and all(
        model_accepts(o["expected"], o["before"], trace)
        for o, trace in zip(observations, actual_traces))


def checkpoint(label, event, expected, before=()):
    pairs = [tuple(pair) for pair in expected]
    for left, right in before:
        if tuple(left) not in pairs or tuple(right) not in pairs:
            raise ValueError("partial order endpoint is not an expected event")
    return dict(label=label, mandatory_event=event, expected=pairs, before=list(before))


def array_literal(values):
    return "[" + ",".join(map(str, values)) + "]" if values else "[integer ::]"


def observation_code(observation):
    expected = observation["expected"]
    result = ("call expect_log(" + array_literal([x[0] for x in expected]) + ","
              + array_literal([x[1] for x in expected]) + ")\n")
    for left, right in observation["before"]:
        result += "call expect_before(" + ",".join(map(str, (*left, *right))) + ")\n"
    return result


def allocate(variable, shape=""):
    return (f"allocate({variable}{shape},stat=status)\nif (status/=0) error stop 111\n"
            f"if (.not.allocated({variable})) error stop 112\n")


def deallocate(*variables):
    body = "".join(f"if (.not.allocated({v})) error stop 113\n" for v in variables)
    body += "deallocate(" + ",".join(variables) + ",stat=status)\n"
    body += "if (status/=0) error stop 114\n"
    body += "".join(f"if (allocated({v})) error stop 115\n" for v in variables)
    return body


def callback(name, typename, code, field="token", rank="", elemental=False):
    prefix = "impure elemental " if elemental else ""
    return (f"{prefix}subroutine {name}(self)\n"
            f"type({typename}), intent(inout) :: self{rank}\n"
            f"call record_event({code},self%{field})\nend subroutine {name}\n")


def array_callback(name, typename, header, payload, rank=1):
    shape = "(:)" if rank == 1 else "(:,:)"
    body = (f"subroutine {name}(self)\ntype({typename}), intent(inout) :: self{shape}\n"
            "integer :: i" + (",j" if rank == 2 else "") + "\n"
            f"call record_event({header},size(self))\n")
    if rank == 1:
        body += f"do i=1,size(self)\ncall record_event({payload},self(i)%token)\nend do\n"
    else:
        body += (f"do j=1,size(self,2)\ndo i=1,size(self,1)\n"
                 f"call record_event({payload},self(i,j)%token)\nend do\nend do\n")
    return body + f"end subroutine {name}\n"


def type_module(definitions, procedures, private_names=()):
    return ("module final_types\nuse final_log, only: record_event\nimplicit none\n"
            + ("private :: " + ",".join(private_names) + "\n" if private_names else "")
            + definitions + "contains\n" + procedures + "end module final_types\n")


def program(declarations, body, only=""):
    return ("program p\nuse final_types" + (", only: " + only if only else "") + "\n"
            "use final_log, only: reset_log, expect_log, expect_before\nimplicit none\ninteger :: status\n"
            + declarations + "call reset_log()\n" + body + "end program p\n")


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="final_process", root=root)

    def add(self, rule, variant, facet, definitions, procedures, declarations, body,
            observations, variables, private_names=(), only="", premises=""):
        name = identifier(rule, variant)
        folder = "tests/fixtures/final_process_" + name.lower()
        source = LOG_MODULE + type_module(definitions, procedures, private_names) + program(declarations, body, only)
        evidence = "positive-control" if rule == "S7.5.6.2-004" else "effect"
        if not observations or not any(o["expected"] for o in observations):
            raise ValueError("a process case needs a nonvacuous mandatory-event observation")
        manifest = dict(schema_version=1, id=name, rule=rule, facets=[facet],
                        standard="f2023", evidence=evidence, files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free",
                                    output="source.o")],
                        link=dict(objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0))
        self.put(folder + "/source.f90", source)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(rule=rule, facets=[facet], kind="valid", phase="run", evidence=evidence,
                                path=folder + "/fixture.json", observations=observations,
                                finalizable_variables=variables, premises=premises)


def selection_cases(c):
    rule = "S7.5.6.2-001"
    scalar_type = "type :: item\ninteger :: token\ncontains\nfinal :: finish_scalar\nend type item\n"
    scalar_obs = checkpoint("scalar", "DEALLOCATE(value)", [(10, 17)])
    c.add(rule, "scalar", "scalar-exact-match", scalar_type,
          callback("finish_scalar", "item", 10),
          "type(item), allocatable :: value\n",
          allocate("value") + "value%token=17\n" + deallocate("value") + observation_code(scalar_obs),
          [scalar_obs], ["value"], premises="Scalar exact own final; no component/parent or setup finalization.")

    array_type = "type :: item\ninteger :: token\ncontains\nfinal :: finish_vector\nfinal :: finish_matrix\nend type item\n"
    observations = [
        checkpoint("vector", "DEALLOCATE(vector)", [(10, 2), (11, 17), (11, 19)]),
        checkpoint("matrix", "DEALLOCATE(matrix)", [(20, 4), (21, 23), (21, 29), (21, 31), (21, 37)]),
        checkpoint("empty-vector-exact", "DEALLOCATE(vector)", [(10, 0)]),
    ]
    body = allocate("vector", "(2)") + "vector(1)%token=17\nvector(2)%token=19\n"
    body += deallocate("vector") + observation_code(observations[0]) + "call reset_log()\n"
    body += allocate("matrix", "(2,2)") + (
        "matrix(1,1)%token=23\nmatrix(2,1)%token=29\nmatrix(1,2)%token=31\nmatrix(2,2)%token=37\n")
    body += deallocate("matrix") + observation_code(observations[1]) + "call reset_log()\n"
    body += allocate("vector", "(0)") + deallocate("vector") + observation_code(observations[2])
    c.add(rule, "array_exact", "array-exact-match", array_type,
          array_callback("finish_vector", "item", 10, 11) + array_callback("finish_matrix", "item", 20, 21, 2),
          "type(item), allocatable :: vector(:),matrix(:,:)\n", body, observations, ["vector", "matrix"],
          premises="Rank-one/rank-two ordinary finals; exact empty rank-one invokes its array final once.")

    definitions = (
        "type :: item(ka,kb,n,m)\ninteger, kind :: ka,kb\ninteger, len :: n,m\ninteger :: token\n"
        "contains\nfinal :: finish_11\nfinal :: finish_12\nfinal :: finish_21\nfinal :: finish_22\nend type item\n")
    procedures = ""
    for ka, kb in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        procedures += (
            f"subroutine finish_{ka}{kb}(self)\n"
            f"type(item(ka={ka},kb={kb},n=*,m=*)), intent(inout) :: self\n"
            f"call record_event({100*ka+kb},self%token)\n"
            f"call record_event(901,self%n)\ncall record_event(902,self%m)\n"
            f"end subroutine finish_{ka}{kb}\n")
    declarations, body, observations, variables = "", "", [], []
    for variable, ka, kb, n, m, token in [
        ("a", 1, 1, 3, 5, 11), ("b", 1, 2, 7, 9, 13),
        ("c", 2, 1, 4, 6, 17), ("d", 2, 2, 8, 10, 19),
        ("e", 1, 1, 12, 14, 23),
    ]:
        variables.append(variable)
        declarations += f"type(item(ka={ka},kb={kb},n={n},m={m})), allocatable :: {variable}\n"
        obs = checkpoint("kind-" + variable, f"DEALLOCATE({variable})",
                         [(100 * ka + kb, token), (901, n), (902, m)])
        observations.append(obs)
        body += "call reset_log()\n" + allocate(variable) + f"{variable}%token={token}\n"
        body += deallocate(variable) + observation_code(obs)
    c.add(rule, "kind_tuple", "kind-tuple-dispatch", definitions, procedures, declarations,
          body, observations, variables,
          premises="Four abstract KIND tuples, not intrinsic selectors; both LEN parameters are assumed in every final. A repeated tuple with different LEN values selects the same final.")

    family = "type :: item\ninteger :: token\ncontains\nfinal :: finish_each\nfinal :: finish_vector\nend type item\n"
    procedures = callback("finish_each", "item", 20, elemental=True)
    procedures += ("subroutine finish_vector(self)\ntype(item), intent(inout) :: self(:)\n"
                   "call record_event(10,size(self))\nend subroutine finish_vector\n")
    observations = [
        checkpoint("exact-vector-before-elemental", "DEALLOCATE(vector)", [(10, 2)]),
        checkpoint("rank-two-elemental-fallback", "DEALLOCATE(matrix)", [(20, 17), (20, 19), (20, 23), (20, 29)]),
        checkpoint("empty-rank-two-elemental", "DEALLOCATE(matrix)", []),
    ]
    body = allocate("vector", "(2)") + "vector(1)%token=11\nvector(2)%token=13\n"
    body += deallocate("vector") + observation_code(observations[0]) + "call reset_log()\n"
    body += allocate("matrix", "(2,2)") + (
        "matrix(1,1)%token=17\nmatrix(2,1)%token=19\nmatrix(1,2)%token=23\nmatrix(2,2)%token=29\n")
    body += deallocate("matrix") + observation_code(observations[1]) + "call reset_log()\n"
    body += allocate("matrix", "(0,2)") + deallocate("matrix") + observation_code(observations[2])
    c.add(rule, "exact_before_elemental", "exact-array-before-elemental", family, procedures,
          "type(item), allocatable :: vector(:),matrix(:,:)\n", body, observations, ["vector", "matrix"],
          premises="Legal rank-one ordinary plus scalar IMPURE ELEMENTAL family; no assumed-rank competitor. Empty fallback has an independently verified nonzero fallback control.")

    any_type = "type :: item\ninteger :: token\ncontains\nfinal :: finish_any\nend type item\n"
    any_final = """subroutine finish_any(self)
type(item), intent(inout) :: self(..)
integer :: i,j
call record_event(50,rank(self))
select rank(self)
rank(0)
call record_event(60,self%token)
rank(1)
do i=1,size(self)
call record_event(60,self(i)%token)
end do
rank(2)
do j=1,size(self,2)
do i=1,size(self,1)
call record_event(60,self(i,j)%token)
end do
end do
rank default
error stop 121
end select
end subroutine finish_any
"""
    observations = [
        checkpoint("assumed-scalar", "DEALLOCATE(scalar)", [(50, 0), (60, 11)]),
        checkpoint("assumed-vector", "DEALLOCATE(vector)", [(50, 1), (60, 17), (60, 19)]),
        checkpoint("assumed-empty-matrix", "DEALLOCATE(matrix)", [(50, 2)]),
    ]
    body = allocate("scalar") + "scalar%token=11\n" + deallocate("scalar") + observation_code(observations[0])
    body += "call reset_log()\n" + allocate("vector", "(2)") + "vector(1)%token=17\nvector(2)%token=19\n"
    body += deallocate("vector") + observation_code(observations[1]) + "call reset_log()\n"
    body += allocate("matrix", "(0,2)") + deallocate("matrix") + observation_code(observations[2])
    c.add(rule, "assumed_rank", "assumed-rank-fallback", any_type, any_final,
          "type(item), allocatable :: scalar,vector(:),matrix(:,:)\n", body, observations,
          ["scalar", "vector", "matrix"], premises="Sole same-KIND final; RANK/SELECT RANK precede rank-specific access. Empty array still invokes the assumed-rank final once.")

    definitions = (
        "type :: leaf\ninteger :: token\ncontains\nfinal :: finish_leaf\nend type leaf\n"
        "type :: item\ntype(leaf) :: part\ncontains\nfinal :: finish_vector\nend type item\n")
    procedures = callback("finish_leaf", "leaf", 30) + (
        "subroutine finish_vector(self)\ntype(item), intent(inout) :: self(:)\n"
        "call record_event(10,size(self))\nend subroutine finish_vector\n")
    obs = checkpoint("no-own-but-component", "DEALLOCATE(value)", [(30, 17)])
    c.add(rule, "no_own_match", "no-matching-own-final", definitions, procedures,
          "type(item), allocatable :: value\n",
          allocate("value") + "value%part%token=17\n" + deallocate("value") + observation_code(obs),
          [obs], ["value"], premises="A scalar cannot select the sole ordinary rank-one own final; its defined plain leaf provides positive automatic process evidence.")

    obs = checkpoint("private-final-automatic", "DEALLOCATE(value)", [(10, 23)])
    c.add(rule, "private_name", "private-final-name", scalar_type,
          callback("finish_scalar", "item", 10), "type(item), allocatable :: value\n",
          allocate("value") + "value%token=23\n" + deallocate("value") + observation_code(obs),
          [obs], ["value"], private_names=["finish_scalar"], only="item",
          premises="Client imports only the public type; private final procedure is invoked only by automatic finalization.")


LEAF = "type :: leaf\ninteger :: token\ncontains\nfinal :: finish_leaf\nend type leaf\n"


def component_cases(c):
    rule = "S7.5.6.2-002"
    definitions = LEAF + (
        "type :: middle\ntype(leaf) :: part\nend type middle\n"
        "type :: item\ntype(middle) :: branch\nend type item\n")
    obs = checkpoint("nested-component", "DEALLOCATE(value)", [(20, 17)])
    c.add(rule, "plain_recursion", "plain-component-recursion", definitions,
          callback("finish_leaf", "leaf", 20), "type(item), allocatable :: value\n",
          allocate("value") + "value%branch%part%token=17\n" + deallocate("value") + observation_code(obs),
          [obs], ["value"], premises="Two ordinary nonallocatable component levels; only the terminal leaf has an own final.")

    definitions = LEAF + "type :: item\ntype(leaf) :: a,b\nend type item\n"
    obs = checkpoint("siblings", "DEALLOCATE(value)", [(20, 11), (20, 13)])
    c.add(rule, "siblings", "sibling-order-independent", definitions,
          callback("finish_leaf", "leaf", 20), "type(item), allocatable :: value\n",
          allocate("value") + "value%a%token=11\nvalue%b%token=13\n"
          + deallocate("value") + observation_code(obs), [obs], ["value"],
          premises="Exact two-member multiset; both sibling orders accepted without peer reads.")

    definitions = (
        "type :: leaf\ninteger :: token\ncontains\nfinal :: finish_leaf\nfinal :: finish_leaf_array\nend type leaf\n"
        "type :: item\ntype(leaf) :: scalar,group(2)\ncontains\nfinal :: finish_outer\nend type item\n")
    procedures = callback("finish_leaf", "leaf", 20) + array_callback("finish_leaf_array", "leaf", 30, 31)
    procedures += ("subroutine finish_outer(self)\ntype(item), intent(inout) :: self(:)\n"
                   "call record_event(10,size(self))\nend subroutine finish_outer\n")
    obs = checkpoint("per-outer-element-components", "DEALLOCATE(values)", [
        (10, 2), (20, 11), (20, 13), (30, 2), (30, 2),
        (31, 21), (31, 23), (31, 25), (31, 27)])
    setup = ("values(1)%scalar%token=11\nvalues(2)%scalar%token=13\n"
             "values(1)%group(1)%token=21\nvalues(1)%group(2)%token=23\n"
             "values(2)%group(1)%token=25\nvalues(2)%group(2)%token=27\n")
    c.add(rule, "array_components", "array-element-components", definitions, procedures,
          "type(item), allocatable :: values(:)\n",
          allocate("values", "(2)") + setup + deallocate("values") + observation_code(obs),
          [obs], ["values"],
          premises="Each actual outer element supplies one scalar leaf and one rank-one leaf component. Two scalar calls and two distinct array-final calls are required; no synthetic aggregate of scalar components.")

    definitions = LEAF + (
        "type :: item\ntype(leaf) :: part\ncontains\nfinal :: finish_outer\nend type item\n")
    procedures = callback("finish_leaf", "leaf", 20) + (
        "subroutine finish_outer(self)\ntype(item), intent(inout) :: self(:)\n"
        "call record_event(10,size(self))\nend subroutine finish_outer\n")
    observations = [
        checkpoint("empty-container", "DEALLOCATE(values)", [(10, 0)]),
        checkpoint("nonempty-container-control", "DEALLOCATE(values)", [(10, 2), (20, 17), (20, 19)]),
    ]
    body = allocate("values", "(0)") + deallocate("values") + observation_code(observations[0])
    body += "call reset_log()\n" + allocate("values", "(2)")
    body += "values(1)%part%token=17\nvalues(2)%part%token=19\n"
    body += deallocate("values") + observation_code(observations[1])
    c.add(rule, "empty_outer", "zero-sized-outer-array", definitions, procedures,
          "type(item), allocatable :: values(:)\n", body, observations, ["values"],
          premises="The exact outer array final proves the empty containing process ran; the nonzero control proves leaf callback membership. No empty-only success case.")

    definitions = LEAF + (
        "type :: item\ninteger :: token\ntype(leaf), pointer :: link=>null()\n"
        "contains\nfinal :: finish_owner\nend type item\n")
    procedures = callback("finish_leaf", "leaf", 20) + callback("finish_owner", "item", 10)
    observations = [
        checkpoint("pointer-excluded-from-owner", "DEALLOCATE(owner)", [(10, 11)]),
        checkpoint("independent-target-positive-event", "DEALLOCATE(target)", [(20, 31)]),
    ]
    body = allocate("target") + allocate("owner")
    body += "target%token=31\nowner%token=11\nowner%link=>target\n"
    body += deallocate("owner") + "if (.not.allocated(target)) error stop 122\n"
    body += observation_code(observations[0]) + "call reset_log()\n"
    body += deallocate("target") + observation_code(observations[1])
    c.add(rule, "pointer_exclusion", "pointer-target-exclusion", definitions, procedures,
          "type(item), allocatable :: owner\ntype(leaf), allocatable, target :: target\n",
          body, observations, ["owner", "target"],
          premises="Owner has its own positive final. Pointer target remains independently reachable through its actual allocated variable, which is later legally deallocated; no saved nonallocated target or dead owner alias is accessed.")


def order_cases(c):
    rule = "S7.5.6.2-003"
    definitions = LEAF + (
        "type :: item\ninteger :: token\ntype(leaf) :: a,b\ncontains\nfinal :: finish_owner\nend type item\n")
    procedures = callback("finish_leaf", "leaf", 20) + callback("finish_owner", "item", 10)
    obs = checkpoint("own-before-siblings", "DEALLOCATE(value)",
                     [(10, 1), (20, 11), (20, 13)],
                     [((10, 1), (20, 11)), ((10, 1), (20, 13))])
    body = allocate("value") + "value%token=1\nvalue%a%token=11\nvalue%b%token=13\n"
    body += deallocate("value") + observation_code(obs)
    c.add(rule, "own_before_components", "own-before-components", definitions, procedures,
          "type(item), allocatable :: value\n", body, [obs], ["value"],
          premises="Own precedes both declared components; either sibling order is legal. Exact event membership/multiplicity is checked before the edges.")

    parent = "type :: parent\ninteger :: parent_token\ncontains\nfinal :: finish_parent\nend type parent\n"
    child = ("type, extends(parent) :: item\ninteger :: token\ntype(leaf) :: part\n"
             "contains\nfinal :: finish_owner\nend type item\n")
    definitions = LEAF + parent + child
    procedures = (callback("finish_leaf", "leaf", 20) + callback("finish_parent", "parent", 30, "parent_token")
                  + callback("finish_owner", "item", 10))
    obs = checkpoint("components-before-parent", "DEALLOCATE(value)", [(10, 1), (20, 11), (30, 21)],
                     [((10, 1), (20, 11)), ((20, 11), (30, 21))])
    body = allocate("value") + "value%token=1\nvalue%part%token=11\nvalue%parent_token=21\n"
    body += deallocate("value") + observation_code(obs)
    c.add(rule, "components_before_parent", "components-before-parent", definitions, procedures,
          "type(item), allocatable :: value\n", body, [obs], ["value"],
          premises="Scalar own stage, declared child component, then the actual scalar parent process; no read of an already finalized child component in parent callback.")

    definitions = LEAF + parent + "type, extends(parent) :: item\ntype(leaf) :: part\nend type item\n"
    procedures = callback("finish_leaf", "leaf", 20) + callback("finish_parent", "parent", 30, "parent_token")
    obs = checkpoint("no-own-child-parent-later", "DEALLOCATE(value)", [(20, 11), (30, 21)],
                     [((20, 11), (30, 21))])
    body = allocate("value") + "value%part%token=11\nvalue%parent_token=21\n"
    body += deallocate("value") + observation_code(obs)
    c.add(rule, "parent_without_child_final", "parent-without-own-child-final", definitions, procedures,
          "type(item), allocatable :: value\n", body, [obs], ["value"],
          premises="Child has no own final. Its declared leaf is processed before parent final exactly once, not before/again as an inherited own final.")

    definitions = LEAF + (
        "type :: root\ninteger :: root_token\ncontains\nfinal :: finish_root\nend type root\n"
        "type, extends(root) :: parent\ninteger :: parent_token\ntype(leaf) :: parent_a,parent_b\n"
        "contains\nfinal :: finish_parent\nend type parent\n"
        "type, extends(parent) :: item\ninteger :: token\ntype(leaf) :: a,b\n"
        "contains\nfinal :: finish_owner\nend type item\n")
    procedures = (callback("finish_leaf", "leaf", 20)
                  + callback("finish_root", "root", 40, "root_token")
                  + callback("finish_parent", "parent", 30, "parent_token")
                  + callback("finish_owner", "item", 10))
    events = [(10, 1), (20, 11), (20, 13), (30, 21), (20, 31), (20, 33), (40, 41)]
    edges = [
        ((10, 1), (20, 11)), ((10, 1), (20, 13)),
        ((20, 11), (30, 21)), ((20, 13), (30, 21)),
        ((30, 21), (20, 31)), ((30, 21), (20, 33)),
        ((20, 31), (40, 41)), ((20, 33), (40, 41)),
    ]
    obs = checkpoint("recursive-parent-stages", "DEALLOCATE(value)", events, edges)
    body = allocate("value") + (
        "value%token=1\nvalue%a%token=11\nvalue%b%token=13\nvalue%parent_token=21\n"
        "value%parent_a%token=31\nvalue%parent_b%token=33\nvalue%root_token=41\n")
    body += deallocate("value") + observation_code(obs)
    c.add(rule, "recursive_parent", "recursive-parent-process", definitions, procedures,
          "type(item), allocatable :: value\n", body, [obs], ["value"],
          premises="Child siblings precede complete parent process; parent's own callback precedes its declared siblings; root follows them. Four sibling permutations are permitted. Inherited components may not be traversed in both child and parent stages.")


def independent_entities(c):
    obs = checkpoint("independent-event-peers", "DEALLOCATE(left,right)", [(20, 17), (20, 19)])
    body = allocate("left") + allocate("right") + "left%token=17\nright%token=19\n"
    body += deallocate("left", "right") + observation_code(obs)
    c.add("S7.5.6.2-004", "independent_entities", "independent-entity-control",
          LEAF, callback("finish_leaf", "leaf", 20),
          "type(leaf), allocatable :: left,right\n", body, [obs], ["left", "right"],
          premises="One multi-entity mandatory event. Each callback reads only its own token and writes separate saved nonfinalizable logs; both peer orders accepted. This is a positive control, not a forbidden-peer-access or trapping test.")


def build_corpus(root=ROOT):
    c = Corpus(root)
    selection_cases(c)
    component_cases(c)
    order_cases(c)
    independent_entities(c)
    if c.coverage() != {k: set(v) for k, v in ELIGIBLE.items()}:
        raise ValueError("finite process coverage differs from the reviewed 17 facets")
    if len(c.cases) != 17:
        raise ValueError("the finite process corpus must have 17 executable cases")
    return c.files, c.cases


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    r = Registry(ROOT)
    r.catalogues[SECTION] = catalogue
    return r.catalogue_review_state(SECTION)


def synced_catalogue(catalogue, specs):
    result = json.loads(json.dumps(catalogue))
    for requirement in result["requirements"]:
        rows = [s for s in specs.values() if s["rule"] == requirement["id"]]
        coverage = {f for row in rows for f in row["facets"]}
        for facet in coverage:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - coverage:
            raise ValueError("pending process graph mismatch")
        old = requirement["oracle"].split("\n\nFinite process implementation:", 1)[0]
        requirement["oracle"] = old + (
            f"\n\nFinite process implementation: {len(rows)} run-phase cases represent "
            f"{len(coverage)} finite facets with mandatory guarded whole-allocatable DEALLOCATE "
            "events before observations. Exact log multisets and required partial-order edges "
            "are checked without peeking at finalized peers. "
            + ("These are positive controls for the restriction, not forbidden-access effects. "
               if requirement["id"] == "S7.5.6.2-004" else "")
            + f"{len(requirement['pending'])} source/use graph facets remain pending. "
            "Source/case/evidence adjudications are separate content-bound records; authorship "
            "and observations do not confer approval.")
    return result


DOCUMENT = """## Source and bounded ownership

Authority: J3/24-007, **18 December 2023**, **688 PDF pages**, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The three 7.5.6.2 base units are on physical PDF102-103. Original PDF102-104,
15.9.1/15.9.3 on PDF362-363 and necessary deallocation/definition/lifetime
conditions were read. The preceding POINT_LENGTH note and other finalization
sections are not new local requirements.

The independent source review is `finalization-source-review.json`
(SHA-256 `6280f2250fbf5464c58144a0207a56a51c88fd4771830bf04942906c2ec092ea`).
FSRC-001 was corrected by the preserved `57ba04c24354a1ef30ef41cb19bf890ac2ba18c5`
source checkpoint; the correction receipt hash is
`bc1b70834d015af14d9cf7a2fbe5f70229ee9a85109fb85b325eb3dd5aed490d`.
Only its 7.5.6.2 catalogue/view are owned here. FINAL statement constraints,
event definitions, termination and conditional external observers retain their
canonical owners.
Independent concrete fixture, observer, refresh and provenance decisions are
recorded in `doc/source_audits/batch_016.json`; source/case approval remains
separate from generation and processor observations.

## Concrete oracle premises

* **Known event first.** Every observation follows a guarded whole-allocated
  DEALLOCATE, with successful allocation/deallocation status and correct live
  object state. There is no explicit CALL to a final subroutine and no
  declaration-only finalization proof. DEALLOCATE is the prerequisite event,
  not a new 7.5.6.3 event-owned fixture.
* **Defined, independently named inputs.** Every primitive token is set through
  its actual named component/element before the event. Setup never assigns a
  whole finalizable object, creates a finalizable result or uses a structure
  constructor. All later observations read only separate saved INTEGER logs;
  callbacks read their own current dummy and safe SIZE/RANK/type-parameter
  properties, never a dead peer or a retained alias.
* **Exact selection.** Final dummies are nonpolymorphic TYPE, nonoptional,
  nonpointer, nonallocatable and noncoarray, with INOUT (not OUT or VALUE).
  All PDT LEN parameters are assumed. KIND tags1/2 are abstract type parameters,
  never intrinsic representation selectors. Assumed rank is the sole same-KIND
  final in its family; it does not compete illegally with a fixed-rank final.
* **Elemental qualifications.** Logging elemental callbacks are explicitly
  IMPURE ELEMENTAL with scalar data dummies and valid intent under15.9.
  A same-KIND rank-one ordinary/scalar-elemental family is legal; exact rank-one
  wins, rank-two falls back, and zero fallback elements produce no scalar calls.
  The zero fallback is paired with nonzero exact and elemental controls.
  Logs use counts/multisets, not an assumed elemental global-side-effect order.
* **Nonvacuous components.** An exact array final still records one invocation
  for an empty array. A zero outer array has a containing marker and a nonzero
  component control. Scalar components of each outer array element require
  scalar child calls, while each real array component invokes its array final
  separately. A no-own-match scalar still produces its real component callback.
* **Pointer target survives separately.** Owner destruction has a positive own
  callback. Its pointer target is an independently reachable, actually allocated
  allocatable TARGET, not a saved nonallocated variable; a later legal deallocation
  supplies the target-positive event. No owner/alias is dereferenced after death.
  Allocatable component cleanup has its own event graph and remains pending.
* **Partial parent order, not layout.** Own processing precedes declared eligible
  components; all those siblings precede actual recursive parent processing.
  Inherited components are processed at the parent stage exactly once, not again
  at child stage. Parent finals are not inherited own finals. Every allowed
  sibling permutation is accepted with exact membership/multiplicity.
* **Role and access limits.** Private FINAL names are invoked automatically;
  the client imports only the type and never calls the private procedure.
  S7.5.6.2-004 remains restriction/not-required and its run is positive-control.
  There is no forbidden peer access, expected trap, new diagnostic policy,
  ERROR STOP profile or post-termination observer. ERROR STOP in these programs
  only marks a failed ordinary self-check; it is not the property being tested.

FQ01-08 remain binding source qualifications. Function-result/executable-
construct and PURE/image-termination observer work is outside these fixtures.
No hypothetical graph or Python countermodel replaces an automatic Fortran event.
Each final name is declared in its own permitted FINAL statement (R746/R748/R753),
so comma-list parsing is not an incidental prerequisite for these process cases.
Failed log checks print only saved primitive log entries after the event; they
do not inspect finalized objects. Original list-form failures and later
source-equivalent declaration/logging refinements remain separate observations.

## Evidence and integration boundaries

All runtime cases stay run-phase if a compiler rejects, crashes or misses a
callback. Source-valid reference failures do not justify weakening the expected
set/order, changing event ownership, making a logging finalizer PURE, or replacing
the program with a compile-only/no-op control. Original and refresh reports,
complete command traces and per-case current-fingerprint selection are preserved
separately in `final-process-phase2-handoff.json`; a current-row index is not one
invented processor run. The target is the frozen LF411 a0afaa840b toolchain;
GNU f2023 and actual Flang f2018 modes are recorded without relabelling.

Only this process catalogue/view, generator/test and `tests/fixtures/final_process_*`
inputs are owned by the author packet. Its validation-only local index overlay
is not merged wholesale. The packet preserved all1546 author-base case bindings
and inputs; serial main integration separately preserves the current prior
case universe. Adjudication and baseline/evidence updates remain explicit
coordinator work, never side effects of this generator.
"""


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    observations = sum(len(s["observations"]) for s in specs.values())
    out = (
        "# Fortran 2023: 7.5.6.2 The finalization process\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Case and evidence adjudications are separate content-bound records.\n\n"
        f"The bounded corpus has **{len(specs)} run-phase cases**, "
        f"**{sum(s['evidence']=='effect' for s in specs.values())} effects** and "
        f"**{sum(s['evidence']=='positive-control' for s in specs.values())} positive control**, "
        f"with **{observations} mandatory-event checkpoints**. "
        f"**{22-pending} of 22 facets are represented; {pending} remain pending.**\n\n"
        + DOCUMENT + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.5.6.2 -->")
    out += "\n\n" + "\n".join(render_requirement(r) for r in catalogue["requirements"]) + "\n"
    out += "<!-- END GENERATED 7.5.6.2 -->\n\n## Exact finite case observations\n\n"
    for name, spec in specs.items():
        out += f"### `{name}`\n\n**Primary:** {spec['rule']}; **facet:** `{spec['facets'][0]}`; "
        out += f"**phase/evidence:** run / {spec['evidence']}.\n\n{spec['premises']}\n\n"
        for obs in spec["observations"]:
            out += f"* `{obs['label']}` after `{obs['mandatory_event']}`: multiset `{obs['expected']}`"
            out += f"; required before-edges `{obs['before']}`.\n"
        out += "\n"
    out += "## Complete finite pending plans\n\n"
    out += "These five canonical source/use graphs are unrepresented; no model or declaration clears them.\n\n"
    for r in catalogue["requirements"]:
        if r["pending"]:
            out += f"### Pending {r['id']}\n\n"
            for facet, plan in r["pending"].items():
                out += f"* **`{facet}`** — {plan}\n"
            out += "\n"
    out += (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_final_process_fixtures.py --check` verifies exact owned "
        "inputs, pending/phase metadata and both document regions. The targeted Python "
        "regressions independently enumerate permitted partial orders and reject missing, "
        "duplicate, aggregated, wrong-stage and vacuous traces. Shared parameter inputs "
        "remain unchanged. Source/case approval is not inferred from any check or observation; "
        "consult the current adjudication records before integration.\n")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    outputs, specs = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, specs)
    if args.check:
        bad = [str(p.relative_to(ROOT)) for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob("final_process_*/*") if p.is_file()}
        bad += [str(p.relative_to(ROOT)) for p in actual - set(outputs)]
        if catalogue != updated:
            bad.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            bad.append(VIEW)
        if bad:
            raise SystemExit("stale final-process packet: " + ", ".join(sorted(bad)))
    else:
        for p, b in outputs.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files for "
          f"{len(specs)} final-process run cases and 17 represented facets.")


if __name__ == "__main__":
    main()
