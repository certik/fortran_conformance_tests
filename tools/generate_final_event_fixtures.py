#!/usr/bin/env python3
"""Finite ordinary finalization-event witnesses, without review or compiler actions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from generate_derived_parameter_fixtures import Corpus as ParameterCorpus, source
from generate_final_process_fixtures import (
    LOG_MODULE, allocate, array_callback, callback, case_accepts, checkpoint as process_checkpoint,
    deallocate, model_accepts, observation_code as process_observation_code,
)

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.6.3"
CATALOGUE = "doc/catalogues/derived_types_7_5_6_3.json"
VIEW = "doc/fortran_2023_7_5_6_3.md"
ELIGIBLE = {
    "S7.5.6.3-001": [
        "old-value-before-definition", "rhs-evaluation-before-final",
        "unallocated-left-exclusion", "allocated-left-reallocation",
        "allocated-subobject-before-release",
    ],
    "S7.5.6.3-003": [
        "explicit-return-local", "end-subprogram-local",
        "multiple-locals-unordered", "saved-local-exclusion-control",
    ],
    "S7.5.6.3-004": [
        "ordinary-end-block", "nested-block-timing", "saved-block-exclusion-control",
    ],
    "S7.5.6.3-005": [
        "statement-result-boundary", "if-construct-boundary", "do-control-boundary",
        "pointer-result-exclusion-control",
    ],
    "S7.5.6.3-007": [
        "ordinary-intent-out-old-value", "elemental-scalar-selection",
        "elemental-array-only-no-entry-final",
    ],
}
ITEM = "type :: item\ninteger :: token\ncontains\nfinal :: finish_scalar\nend type item\n"


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__final_event_" + variant


def checkpoint(label, boundary, expected, before=(), repetitions=1):
    result = process_checkpoint(label, boundary, expected, before)
    result["boundary"] = result.pop("mandatory_event")
    result["repetitions"] = repetitions
    return result


def observation_code(observation):
    return ("! checkpoint: " + observation["label"] + "\n"
            + process_observation_code(observation))


def expanded_observations(spec):
    return [o for o in spec["observations"] for _ in range(o["repetitions"])]


def history_accepts(spec, traces):
    if not case_accepts(expanded_observations(spec), traces):
        return False
    return all(list(later[:len(earlier)]) == list(earlier)
               for earlier, later in zip(traces, traces[1:]))


def bind_observations(text, observations):
    bindings = []
    for observation in observations:
        code = observation_code(observation)
        if text.count(code) != 1:
            raise ValueError("checkpoint must bind to exactly one emitted guard: " + observation["label"])
        start = text.index(code)
        bindings.append(dict(
            label=observation["label"], line=text[:start].count("\n") + 1,
            end_line=text[:start + len(code)].count("\n"),
            sha256=hashlib.sha256(code.encode("ascii")).hexdigest(),
            repetitions=observation["repetitions"],
        ))
    return bindings


class Corpus(ParameterCorpus):
    def __init__(self, root=ROOT):
        super().__init__(namespace="final_event", root=root)

    def add(self, rule, variant, facets, definitions, procedures, declarations, body,
            observations, premises, module_state="", whole_assignments=(), entry_edges=()):
        name = identifier(rule, variant)
        folder = "tests/fixtures/final_event_" + name.lower()
        text = (LOG_MODULE + "module final_types\n"
                "use final_log, only: record_event, expect_log, expect_before\nimplicit none\n"
                + definitions + module_state + "contains\n" + procedures
                + "end module final_types\nprogram p\nuse final_types\n"
                "use final_log, only: reset_log, record_event, expect_log, expect_before\n"
                "implicit none\ninteger :: status\n" + declarations
                + "call reset_log()\n" + body + "end program p\n")
        if not observations or not any(
                event[0] in (10, 30) for o in observations for event in o["expected"]):
            raise ValueError("an event witness needs a nonvacuous final callback")
        if len({o["label"] for o in observations}) != len(observations):
            raise ValueError("duplicate event checkpoint")
        manifest = dict(
            schema_version=1, id=name, rule=rule, facets=list(facets), standard="f2023",
            evidence="effect", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free",
                        output="source.o")],
            link=dict(objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0),
        )
        self.put(folder + "/source.f90", text)
        self.put(folder + "/fixture.json", json.dumps(manifest, indent=2) + "\n")
        self.cases[name] = dict(
            rule=rule, facets=list(facets), kind="valid", phase="run", evidence="effect",
            path=folder + "/fixture.json", observations=observations, premises=premises,
            oracle_guards=bind_observations(text, observations),
            whole_assignments=list(whole_assignments), entry_edges=list(entry_edges),
        )


def assignment_cases(c):
    rule = "S7.5.6.3-001"
    before = checkpoint("before-assignment", "primitive setup, before intrinsic assignment", [])
    after = checkpoint("after-assignment", "completed intrinsic assignment",
                       [(5, 11), (10, 7)], [((5, 11), (10, 7))])
    procedures = callback("finish_scalar", "item", 10) + source("""
        impure integer function rhs_token() result(value)
        call record_event(5,11)
        value=11
        end function rhs_token
        """)
    assignment = "left=item(token=rhs_token())"
    c.add(rule, "assignment_order", ELIGIBLE[rule][:2], ITEM, procedures, "type(item) :: left\n",
          "left%token=7\n" + observation_code(before) + assignment + "\n"
          + observation_code(after) + "if (left%token/=11) error stop 121\n",
          [before, after],
          "One shared witness uses a genuine item constructor, with no same-name generic. "
          "An INTEGER-only RHS helper logs evaluation. The sole old-left callback records7 "
          "after that marker; the new live left value is11. No setup record assignment, "
          "finalizable RHS function result, or compiler-temporary-count premise is present.",
          whole_assignments=[assignment])

    before = checkpoint("unallocated-before", "unallocated left side before assignment", [])
    after = checkpoint("unallocated-assigned", "assignment allocated and defined the left side", [])
    cleanup = checkpoint("unallocated-cleanup", "separate later checked DEALLOCATE(left)", [(10, 1)])
    assignment = "left=item(token=11)"
    c.add(rule, "unallocated_left", ["unallocated-left-exclusion"], ITEM,
          source("""
          subroutine finish_scalar(self)
          type(item), intent(inout) :: self
          call record_event(10,1)
          end subroutine finish_scalar
          """), "type(item), allocatable :: left\n",
          "if (allocated(left)) error stop 122\n" + observation_code(before) + assignment + "\n"
          "if (.not.allocated(left)) error stop 123\nif (left%token/=11) error stop 124\n"
          + observation_code(after) + deallocate("left") + observation_code(cleanup),
          [before, after, cleanup],
          "The exclusion is checked immediately after allocation by intrinsic assignment, "
          "before any later cleanup. A constant callback marker avoids reading nonexistent "
          "old payload even if an implementation incorrectly calls it for the unallocated LHS. "
          "The separate successful deallocation is a nonvacuous observer, not a new p2-owned case.",
          whole_assignments=[assignment])

    definitions = "type :: item\ninteger :: token\ncontains\nfinal :: finish_array\nend type item\n"
    before = checkpoint("reallocation-before", "defined allocated old rank-one extent2", [])
    after = checkpoint("reallocation-assigned", "different-extent intrinsic assignment",
                       [(10, 2), (11, 7), (11, 11)])
    cleanup = checkpoint("reallocation-cleanup", "separate later checked DEALLOCATE(left)",
                         after["expected"] + [(10, 3), (11, 17), (11, 19), (11, 23)])
    assignment = "left=[item(token=17),item(token=19),item(token=23)]"
    c.add(rule, "allocated_reallocation", ["allocated-left-reallocation"], definitions,
          array_callback("finish_array", "item", 10, 11),
          "type(item), allocatable :: left(:)\n",
          allocate("left", "(2)") + "left(1)%token=7\nleft(2)%token=11\n"
          + observation_code(before) + assignment + "\n"
          "if (.not.allocated(left)) error stop 125\nif (size(left)/=3) error stop 126\n"
          "if (any(left%token/=[17,19,23])) error stop 127\n"
          + observation_code(after) + deallocate("left") + observation_code(cleanup),
          [before, after, cleanup],
          "The unparameterized nonpolymorphic type is identical on both sides; rank is one, "
          "old extent2 differs from constructor-array extent3. Checked allocation precedes "
          "primitive initialization. The matching ordinary array final records its own old "
          "extent/tokens before release; the new allocation is guarded before value inquiries. "
          "The assertion before later cleanup prevents a missed assignment event being hidden.",
          whole_assignments=[assignment])

    definitions = source("""
        type :: item
        integer :: token
        integer, allocatable :: child(:)
        contains
        final :: finish_scalar
        end type item
        """)
    procedures = source("""
        subroutine finish_scalar(self)
        type(item), intent(inout) :: self
        integer :: i
        call record_event(10,self%token)
        if (.not.allocated(self%child)) error stop 128
        call record_event(11,size(self%child))
        do i=1,size(self%child)
        call record_event(12,self%child(i))
        end do
        end subroutine finish_scalar
        """)
    before = checkpoint("subobject-before", "defined old containing object and allocated child", [])
    after = checkpoint("subobject-assigned", "assignment after containing final and child replacement",
                       [(10, 7), (11, 2), (12, 17), (12, 19)])
    assignment = "left=item(token=11,child=[31,37,41])"
    c.add(rule, "allocated_subobject", ["allocated-subobject-before-release"], definitions,
          procedures, "type(item) :: left\n", "left%token=7\n" + allocate("left%child", "(2)")
          + "left%child(1)=17\nleft%child(2)=19\n" + observation_code(before) + assignment + "\n"
          "if (.not.allocated(left%child)) error stop 129\n"
          "if (size(left%child)/=3) error stop 130\n"
          "if (any(left%child/=[31,37,41])) error stop 131\n"
          "if (left%token/=11) error stop 132\n" + observation_code(after) + deallocate("left%child"),
          [before, after],
          "The containing own final, not a child final, observes its still-allocated INTEGER "
          "child under9.7.3.2p7/p9. Only the callback's own defined fields are read. "
          "The constructor's rank-one intrinsic component data source is legal7.5.10p6/p8. "
          "S10_2_1_3_029_valid__finalization instead counts a replaced finalizable child, "
          "with no containing own callback; it is preserved, not duplicated or relabelled.",
          whole_assignments=[assignment])


def local_cases(c):
    rule = "S7.5.6.3-003"
    for variant, facet, ending, tokens, saved in (
        ("return_local", "explicit-return-local", "return\n", [17], False),
        ("end_local", "end-subprogram-local", "", [19], False),
        ("multiple_locals", "multiple-locals-unordered", "", [17, 19], False),
        ("saved_local", "saved-local-exclusion-control", "return\n", [17], True),
    ):
        before = checkpoint("local-before-exit", "initialized live locals immediately before exit", [])
        after = checkpoint("local-after-exit", "caller after RETURN/END-subprogram",
                           [(10, t) for t in tokens])
        local_names = ["first", "second"][:len(tokens)]
        declarations = "type(item) :: " + ",".join(local_names) + "\n"
        if saved:
            declarations += "type(item), save :: kept\n"
        setup = "".join(f"{name}%token={token}\n" for name, token in zip(local_names, tokens))
        if saved:
            setup += "kept%token=41\n"
        procedures = (callback("finish_scalar", "item", 10) + "subroutine leave_scope()\n"
                      + declarations + setup + observation_code(before) + ending
                      + "end subroutine leave_scope\n")
        c.add(rule, variant, [facet], ITEM, procedures, "",
              "call leave_scope()\n" + observation_code(after), [before, after],
              "The event locals are unsaved nonpointer nonallocatable TYPE(item) objects, "
              "neither dummies nor results, with no declaration initializer or whole-object setup. "
              "The caller reads only the separate saved INTEGER log. "
              + ("Two own-token callbacks are a multiset; both orders are accepted."
                 if len(tokens) == 2 else
                 "Explicit SAVE retains kept; its41 callback is excluded alongside a real17 event."
                 if saved else
                 "The explicit RETURN path is exercised." if ending else
                 "Fallthrough END SUBROUTINE, not END PROGRAM, is exercised."))


def block_cases(c):
    rule = "S7.5.6.3-004"
    before = checkpoint("block-inside", "defined live ordinary BLOCK local", [])
    after = checkpoint("block-after", "immediately after END BLOCK", [(10, 17)])
    c.add(rule, "end_block", ["ordinary-end-block"], ITEM,
          callback("finish_scalar", "item", 10), "",
          "block\ntype(item) :: local\nlocal%token=17\n" + observation_code(before)
          + "end block\n" + observation_code(after), [before, after],
          "A nonpointer nonallocatable unsaved BLOCK-local object becomes undefined at "
          "END BLOCK under19.6.6(23). Its primitive token is defined before the event; "
          "the post-block observer does not reference the dead local.")

    before = checkpoint("nested-inner-inside", "both locals live before inner END BLOCK", [])
    middle = checkpoint("nested-between", "inner ended, outer BLOCK still active", [(10, 19)])
    after = checkpoint("nested-after", "both BLOCK constructs have ended",
                       [(10, 19), (10, 17)], [((10, 19), (10, 17))])
    c.add(rule, "nested_blocks", ["nested-block-timing"], ITEM,
          callback("finish_scalar", "item", 10), "",
          "block\ntype(item) :: outer\nouter%token=17\n"
          "block\ntype(item) :: inner\ninner%token=19\n" + observation_code(before)
          + "end block\n" + observation_code(middle) + "end block\n" + observation_code(after),
          [before, middle, after],
          "The separate-log middle checkpoint requires the inner19 callback already complete "
          "and excludes the still-live outer17 callback. No inner object is read after its "
          "lifetime. The two distinct nesting events, not sibling declaration order, impose the edge.")

    before = checkpoint("saved-block-inside", "saved and unsaved BLOCK locals are live", [])
    after = checkpoint("saved-block-after", "END BLOCK excludes saved kept", [(10, 17)])
    c.add(rule, "saved_block", ["saved-block-exclusion-control"], ITEM,
          callback("finish_scalar", "item", 10), "",
          "block\ntype(item) :: local\ntype(item), save :: kept\n"
          "local%token=17\nkept%token=41\n" + observation_code(before)
          + "end block\n" + observation_code(after), [before, after],
          "Explicitly saved kept retains its definition status under8.5.16; only unsaved "
          "local17 receives the direct END BLOCK event. Primitive setup and a positive "
          "local callback make the saved exclusion nonvacuous. No termination claim is made.")


def result_procedures(token, getter_observation, extra_final="", pointer=False):
    procedures = callback("finish_scalar", "item", 10)
    if extra_final:
        procedures = procedures.replace("end subroutine finish_scalar\n",
                                        extra_final + "end subroutine finish_scalar\n")
    if pointer:
        procedures += source(f"""
            impure function locate() result(value)
            type(item), pointer :: value
            value=>saved_target
            call record_event(5,{token})
            end function locate
            """)
    else:
        procedures += source("""
            impure function make(token) result(value)
            integer, intent(in) :: token
            type(item) :: value
            value%token=token
            call record_event(5,token)
            end function make
            """)
    procedures += ("impure integer function consume(value) result(answer)\n"
                   "type(item), intent(in) :: value\n" + observation_code(getter_observation)
                   + "answer=value%token\ncall record_event(20,answer)\n"
                   "end function consume\n")
    return procedures


def result_cases(c):
    rule = "S7.5.6.3-005"
    getter = checkpoint("statement-getter", "result returned, getter executing before statement ends", [(5, 17)])
    after = checkpoint("statement-after", "INTEGER assignment statement completed",
                       [(5, 17), (20, 17), (10, 17)], [((20, 17), (10, 17))])
    c.add(rule, "statement_result", ["statement-result-boundary"], ITEM,
          result_procedures(17, getter), "integer :: answer\n",
          "answer=consume(make(17))\n" + observation_code(after)
          + "if (answer/=17) error stop 141\n", [getter, after],
          "An ordinary IMPURE module function initializes only its nonpointer result's token. "
          "The INTEGER getter genuinely consumes the result, expects creation but no final "
          "at getter entry, and logs consumption. Exactly one old-result callback follows "
          "the complete assignment statement; function END is not that event.")

    getter = checkpoint("if-getter", "block IF condition consumes a created nonpointer result", [(5, 1)])
    inside = checkpoint("if-inside", "inside the selected block after its first body marker",
                        [(5, 1), (20, 1), (40, 31)])
    last = checkpoint("if-last-body", "last body checkpoint, still within block IF",
                      inside["expected"] + [(40, 37)])
    after = checkpoint("if-after", "whole block IF completed",
                       last["expected"] + [(10, 1)], [((40, 37), (10, 1))])
    c.add(rule, "if_result", ["if-construct-boundary"], ITEM, result_procedures(1, getter),
          "integer :: entered\n", "entered=0\nif (consume(make(1))==1) then\n"
          "entered=entered+1\ncall record_event(40,31)\n" + observation_code(inside)
          + "call record_event(40,37)\n" + observation_code(last)
          + "else\nerror stop 142\nend if\n" + observation_code(after)
          + "if (entered/=1) error stop 143\n", [getter, inside, last, after],
          "The reference is in the block IF controlling expression, not in a body statement "
          "or unevaluated inquiry. Distinct first/last body markers and in-block zero-final "
          "checks precede the outside single-final checkpoint. The selected block must execute.")

    getter = checkpoint("do-getter", "ordinary counted DO terminal expression is consumed", [(5, 3)])
    inside = checkpoint("do-inside", "each of three counted DO iterations", [(5, 3), (20, 3)],
                        repetitions=3)
    after = checkpoint("do-after", "entire counted DO including final index increment completed",
                       [(5, 3), (20, 3), (10, 3), (41, 4)], [((20, 3), (10, 3))])
    c.add(rule, "do_result", ["do-control-boundary"], ITEM,
          result_procedures(3, getter, extra_final="call record_event(41,loop_index)\n"),
          "integer :: iterations,total\n",
          "iterations=0\ntotal=0\ndo loop_index=1,consume(make(3))\n"
          "iterations=iterations+1\ntotal=total+loop_index\n" + observation_code(inside)
          + "end do\n" + observation_code(after)
          + "if (iterations/=3) error stop 144\nif (total/=6) error stop 145\n"
          "if (loop_index/=4) error stop 146\n", [getter, inside, after],
          "The terminal expression of an ordinary counted DO, not DO CONCURRENT or a body "
          "statement, consumes the nonpointer result once. All three iterations exclude a "
          "callback. The callback also records the separate live INTEGER DO index4, which "
          "distinguishes cleanup before the final increment; caller iteration/sum checks "
          "exclude vacuous or misbounded loops.",
          module_state="integer, save :: loop_index=0\n")

    getter = checkpoint("pointer-getter", "defined saved target consumed through an associated result",
                        [(5, 23)])
    after = checkpoint("pointer-after", "pointer function reference statement completed",
                       [(5, 23), (20, 23)])
    positive = checkpoint("pointer-positive", "later legal intrinsic assignment to saved target",
                          after["expected"] + [(10, 23)])
    assignment = "saved_target=item(token=29)"
    c.add(rule, "pointer_result", ["pointer-result-exclusion-control"], ITEM,
          result_procedures(23, getter, pointer=True), "integer :: answer\n",
          "saved_target%token=23\nanswer=consume(locate())\n" + observation_code(after)
          + "if (answer/=23) error stop 147\n" + assignment + "\n"
          + observation_code(positive) + "if (saved_target%token/=29) error stop 148\n",
          [getter, after, positive],
          "An ordinary IMPURE pointer factory explicitly associates its result with a "
          "defined saved module TARGET that remains reachable by name. There is no result "
          "finalization. A later genuine-constructor assignment legally finalizes the old "
          "target23 and provides the positive observer; no pointer or nonallocated target "
          "is deallocated, and no PURE association shortcut is used.",
          module_state="type(item), target, save :: saved_target\n",
          whole_assignments=[assignment])


def intent_out_cases(c):
    rule = "S7.5.6.3-007"
    definitions = source("""
        type :: item
        integer :: token
        integer :: defaulted=5
        contains
        final :: finish_scalar
        end type item
        """)
    entry = checkpoint("ordinary-body-entry", "OUT body after finalization and default initialization",
                       [(10, 7), (11, 9)])
    after = checkpoint("ordinary-after-call", "body defined new primitive fields and returned",
                       entry["expected"] + [(20, 5)])
    cleanup = checkpoint("ordinary-cleanup", "separate later checked whole-object DEALLOCATE",
                         after["expected"] + [(10, 11), (11, 13)])
    procedures = source("""
        subroutine finish_scalar(self)
        type(item), intent(inout) :: self
        call record_event(10,self%token)
        call record_event(11,self%defaulted)
        end subroutine finish_scalar
        subroutine define_out(self)
        type(item), intent(out) :: self
        """) + observation_code(entry) + source("""
        if (self%defaulted/=5) error stop 151
        call record_event(20,self%defaulted)
        self%token=11
        self%defaulted=13
        end subroutine define_out
        """)
    c.add(rule, "ordinary_out", ["ordinary-intent-out-old-value"], definitions, procedures,
          "type(item), allocatable :: actual\n",
          allocate("actual") + "actual%token=7\nactual%defaulted=9\ncall define_out(actual)\n"
          + observation_code(after)
          + "if (actual%token/=11) error stop 152\nif (actual%defaulted/=13) error stop 153\n"
          + deallocate("actual") + observation_code(cleanup), [entry, after, cleanup],
          "The OUT dummy is nonpointer and nonallocatable even though its defined actual "
          "is allocated. Before undefinition its final sees old token7/defaulted9. On entry "
          "the body sees both completed log records and the defaulted field reset to5 under "
          "7.5.4.6/19.6.5(24); it never reads the undefined nondefaulted token. It defines "
          "11/13 before caller checks and later cleanup, whose callbacks remain separately bounded.")

    definitions = source("""
        type :: item
        integer :: token
        contains
        final :: finish_each
        final :: finish_array
        end type item
        """)
    entry_edges = [((10, 17), (20, 17)), ((10, 19), (20, 19))]
    after = checkpoint("elemental-after-call", "completed elemental OUT call, before later cleanup",
                       [(10, 17), (20, 17), (10, 19), (20, 19)], entry_edges)
    cleanup = checkpoint("elemental-cleanup", "whole-array DEALLOCATE selects the ordinary rank-one final",
                         after["expected"] + [(30, 2), (31, 31), (31, 37)], entry_edges)
    procedures = (callback("finish_each", "item", 10, elemental=True)
                  + array_callback("finish_array", "item", 30, 31)
                  + source("""
        impure elemental subroutine define_out(self,old_token,new_token)
        type(item), intent(out) :: self
        integer, intent(in) :: old_token,new_token
        call record_event(20,old_token)
        call expect_before(10,old_token,20,old_token)
        self%token=new_token
        end subroutine define_out
        """))
    c.add(rule, "elemental_scalar", ["elemental-scalar-selection"], definitions, procedures,
          "type(item), allocatable :: actual(:)\n",
          allocate("actual", "(2)") + "actual(1)%token=17\nactual(2)%token=19\n"
          "call define_out(actual,[17,19],[31,37])\n" + observation_code(after)
          + "if (any(actual%token/=[31,37])) error stop 154\n"
          + deallocate("actual") + observation_code(cleanup), [after, cleanup],
          "Same-type scalar IMPURE ELEMENTAL and ordinary rank-one finals are a legal "
          "C793 distinct-rank family. Entry uses the scalar dummy context, not actual-array "
          "rank. Each body checks its own completed old-token callback using independent "
          "INTEGER marker arrays, not an aliased actual%token or its undefined OUT field. "
          "Only per-element before-edges and final multisets are required; no inter-element "
          "side-effect order is imposed. Later whole-array cleanup selects the rank-one final.",
          entry_edges=entry_edges)

    definitions = "type :: item\ninteger :: token\ncontains\nfinal :: finish_array\nend type item\n"
    after = checkpoint("array-only-after-call", "elemental OUT call with only an ordinary array final",
                       [(20, 31), (20, 37)])
    cleanup = checkpoint("array-only-cleanup", "separate later checked whole-array DEALLOCATE",
                         after["expected"] + [(30, 2), (31, 31), (31, 37)])
    procedures = array_callback("finish_array", "item", 30, 31).replace(
        "call record_event(30,size(self))",
        "array_finals=array_finals+1\ncall record_event(30,size(self))")
    procedures += source("""
        impure elemental subroutine define_out(self,new_token)
        type(item), intent(out) :: self
        integer, intent(in) :: new_token
        if (array_finals/=0) error stop 155
        call record_event(20,new_token)
        self%token=new_token
        end subroutine define_out
        """)
    c.add(rule, "elemental_array_only", ["elemental-array-only-no-entry-final"], definitions,
          procedures, "type(item), allocatable :: actual(:)\n",
          allocate("actual", "(2)") + "actual(1)%token=17\nactual(2)%token=19\n"
          "call define_out(actual,[31,37])\n" + observation_code(after)
          + "if (array_finals/=0) error stop 156\n"
          "if (any(actual%token/=[31,37])) error stop 157\n"
          + deallocate("actual") + observation_code(cleanup)
          + "if (array_finals/=1) error stop 158\n", [after, cleanup],
          "There is only an ordinary rank-one final, with no finalizable parent or plain "
          "component. The logging callee is explicitly IMPURE ELEMENTAL with scalar legal "
          "intents; each body sees zero entry callbacks and defines its output token. "
          "Before cleanup, the exact two body markers exclude entry finalization. Successful "
          "later deallocation of the still-allocated actual supplies one real array callback "
          "over the newly defined values, so the exclusion is not a no-op proof.",
          module_state="integer, save :: array_finals=0\n")


def build_corpus(root=ROOT):
    c = Corpus(root)
    assignment_cases(c)
    local_cases(c)
    block_cases(c)
    result_cases(c)
    intent_out_cases(c)
    if c.coverage() != {r: set(fs) for r, fs in ELIGIBLE.items()} or len(c.cases) != 18:
        raise ValueError("finite event corpus differs from the 18 programs / 19 supported facets")
    return c.files, c.cases


def catalogue_review_status(catalogue):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import Registry
    registry = Registry(ROOT)
    registry.catalogues[SECTION] = catalogue
    return registry.catalogue_review_state(SECTION)


def synced_catalogue(catalogue, specs):
    result = json.loads(json.dumps(catalogue))
    for requirement in result["requirements"]:
        rows = [s for s in specs.values() if s["rule"] == requirement["id"]]
        coverage = {f for row in rows for f in row["facets"]}
        for facet in coverage:
            requirement["pending"].pop(facet, None)
        if set(requirement["pending"]) != set(requirement["facets"]) - coverage:
            raise ValueError("event pending/facet partition mismatch")
        if not rows:
            continue
        old = requirement["oracle"].split("\n\nFinite ordinary-event implementation:", 1)[0]
        requirement["oracle"] = old + (
            f"\n\nFinite ordinary-event implementation: {len(rows)} run-phase programs "
            f"represent {len(coverage)} direct facets using qualified events and before/inside/"
            "after checkpoints. Exact saved INTEGER log multisets, required partial-order "
            "edges and live primitive value/state checks distinguish missing, early, late, "
            "duplicate and vacuous events. No extra order of event peers is imposed. "
            f"{len(requirement['pending'])} source/use graph facet remains pending. "
            "Source/case/evidence adjudications are separate content-bound records; "
            "generation and processor observations do not confer approval.")
    return result


DOCUMENT = """## Source and bounded ownership

Authority: J3/24-007, **18 December 2023**, **688 physical PDF pages**, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
All nine original 7.5.6.3 base units are on PDF103. The preserved source inventory
has36 subdivisions and45 accounting rows; its seven requirement definitions and
all33 facet identities are unchanged.

The independent gate is `finalization-source-review.json`, SHA-256
`6280f2250fbf5464c58144a0207a56a51c88fd4771830bf04942906c2ec092ea`.
FSRC-001 was corrected in `57ba04c24354a1ef30ef41cb19bf890ac2ba18c5`; the
correction receipt SHA-256 is
`bc1b70834d015af14d9cf7a2fbe5f70229ee9a85109fb85b325eb3dd5aed490d`.
Actual elemental conditions are15.9.1/.3 on PDF362-363, not15.8 Simple procedures.
All FQ01-08 qualifications remain binding. Original C791-C794, constructor and
intrinsic assignment, allocation/deallocation, SAVE/BLOCK, executable-construct,
purity/elemental, argument-association and definition/undefinition dependencies
were read before these ordinary plans were elaborated.

## Concrete oracle premises

* **Assignment:** old primitive fields are written individually. The shared
  old-value/RHS-order program uses an INTEGER-returning helper inside a genuine
  constructor, never a same-name generic or finalizable RHS function. The old
  final observes7 after RHS evaluation, before new11. Initially unallocated
  assignment is checked before separate positive cleanup; its callback does not
  read nonexistent old payload. Different-extent array reallocation and a
  containing final's still-allocated INTEGER child have explicit state/value
  guards. No unspecified compiler temporary receives an expected callback.
* **Canonical reuse:** `S10_2_1_3_029_valid__finalization` at
  `tests/clause10/S10_2_1_3_029_valid__finalization.f90` counts a replaced
  finalizable allocatable component. It does not observe the new planned own
  containing callback before child release. That case and its ownership stay
  untouched. Deallocation process witnesses are not copied into event-owned
  cases. The associated source/use graphs remain pending without new links.
* **Locals and BLOCK:** all event locals are unsaved, nonpointer, nonallocatable,
  nondummy and nonresult. No declaration initializer accidentally supplies SAVE.
  Multiple locals use a multiset, not declaration order. Nested BLOCK timing is
  checked through separate logs after inner END BLOCK, never through a dead
  object. Explicit saved controls have a live positive unsaved peer.
* **Function results:** ordinary IMPURE module factories define primitive result
  fields. An INTEGER getter really consumes the value and rejects finalization
  at function END. Block IF and counted DO header references are not body
  statement references. Inside/outside checkpoints and nonzero branch/iteration
  checks distinguish the correct whole-construct boundary; the DO callback also
  records the live final index4. Pointer results keep a named saved TARGET
  reachable and use a later legal assignment, never invalid deallocation, as
  their positive observer.
* **INTENT OUT:** callbacks see only their own old defined fields. Ordinary entry
  checks the completed old-token/defaulted-field log before reading the valid
  reset default and defining the new fields. Logging elemental callees/finals
  are explicitly IMPURE ELEMENTAL with C15118/C15120 scalar intents. A legal
  scalar-elemental/rank-one final family tests scalar entry context; disjoint
  INTEGER markers let each body check its own preceding callback without
  reading undefined OUT payload or imposing an inter-element order. An
  array-only type has no hidden parent/component final path and needs zero entry
  callbacks before its later positive rank-one deallocation observer.
* **Selection and state:** all final dummies are nonpolymorphic TYPE, exactly one
  nonoptional/nonpointer/nonallocatable/noncoarray argument, never OUT or VALUE.
  Types are ordinary, concrete and unparameterized: there are no intrinsic
  representation-selector assumptions or unassumed LEN parameters. Explicit
  allocations/deallocations check STAT and allocation state. Automatic assignment
  allocation has no STAT syntax; new state is checked before payload inquiries.
* **Observer limits:** reused primitive log guards enforce exact membership,
  multiplicity and only required before-edges. No finalizer reads an already
  finalized peer or a dead alias. A guard ERROR STOP marks an ordinary failed
  self-check; process-status, PURE-expression and termination effects are not
  tested or inferred. Models and deliberately wrong-expectation controls test
  the emitted oracle, not compiler consensus or extra language-invalid policies.

## Evidence and integration boundaries

Every owned case is a standard-based runtime effect with no diagnostic policy,
optional-success fallback, coarray execution claim, skip or termination profile.
Source-valid implementation failures remain run-phase failures. Original target
and reference reports keep their actual standards, inputs, fingerprints, commands
and identities; an exact current-row selection is not an invented combined run.
Frozen LF411 a0afaa840b, GNU f2023 and actual Flang f2018 observations do not
themselves grant source/case approval.

All six p2 deallocation facets and all three p6 specification-expression facets
remain pending, as do one canonical graph in each represented family. There are
no new deallocation-owned duplicates, PURE/ERROR STOP candidates, unreachable-
pointer permissions or7.5.6.4 termination observers. Only this catalogue/view,
the event generator/regression and `tests/fixtures/final_event_*` are owned.
The local index overlay is validation-only, excluded from the author commit.
"""


def render_view(catalogue, specs):
    sys.path.insert(0, str(ROOT / "tests"))
    from suite_data import render_requirement
    facets = sum(len(r["facets"]) for r in catalogue["requirements"])
    pending = sum(len(r["pending"]) for r in catalogue["requirements"])
    checkpoints = sum(len(s["observations"]) for s in specs.values())
    out = (
        "# Fortran 2023: 7.5.6.3 When finalization occurs\n\n"
        f"**Catalogue source review: {catalogue_review_status(catalogue)}.** "
        "Case and evidence adjudications are separate content-bound records.\n\n"
        f"The bounded corpus has **{len(specs)} run-phase effect programs**, "
        f"**{checkpoints} finite checkpoint sites**, and **{facets-pending} represented "
        f"of {facets} facets; {pending} remain pending**. The old-value and RHS-order "
        "facets share one program, not two copied inputs.\n\n" + DOCUMENT
        + "\n## Definitions\n\n<!-- BEGIN GENERATED 7.5.6.3 -->\n\n"
        + "\n".join(render_requirement(r) for r in catalogue["requirements"])
        + "\n<!-- END GENERATED 7.5.6.3 -->\n\n## Exact finite case observations\n\n")
    for name, spec in specs.items():
        out += (f"### `{name}`\n\n**Primary:** {spec['rule']}; **facets:** "
                + ", ".join(f"`{f}`" for f in spec["facets"])
                + f"; **phase/evidence:** {spec['phase']} / {spec['evidence']}.\n\n"
                + spec["premises"] + "\n\n")
        for obs in spec["observations"]:
            out += (f"* `{obs['label']}`: {obs['boundary']}; multiset `{obs['expected']}`; "
                    f"before-edges `{obs['before']}`; executions `{obs['repetitions']}`.\n")
        out += "\n"
    out += ("## Complete finite pending plans\n\n"
            "The following canonical plans retain their exact text. A prerequisite event, "
            "model or unregistered reuse relationship does not clear a pending facet.\n\n")
    for r in catalogue["requirements"]:
        if r["pending"]:
            out += f"### Pending {r['id']}\n\n"
            for facet, plan in r["pending"].items():
                out += f"* **`{facet}`** - {plan}\n"
            out += "\n"
    out += (
        "## Reproduction and remaining gates\n\n"
        "`python3 -B tools/generate_final_event_fixtures.py --check` checks exact fixture "
        "bytes, finite coverage, current administrative review rendering and the complete "
        "pending appendix. Focused regressions use independently specified expected histories, "
        "permitted unordered alternatives and wrong timing/multiplicity/nonvacuity countermodels "
        "bound to actual emitted guard ranges. Independent review and exact observation "
        "provenance are recorded in `doc/source_audits/batch_019.json`. Sixteen cases have "
        "qualifying GNU f2023 observations. IF/DO result cases retain source-only adjudication "
        "and whole-construct oracles despite the recorded missing or premature callbacks; "
        "synthetic guard runs are not successful automatic-finalization executions. All "
        "14 pending facets remain open, and current source/case/evidence approvals remain "
        "separate content-bound records.\n")
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
        bad = [str(p.relative_to(ROOT)) for p, b in outputs.items()
               if not p.is_file() or p.read_bytes() != b]
        actual = {p for p in (ROOT / "tests/fixtures").glob("final_event_*/*") if p.is_file()}
        bad += [str(p.relative_to(ROOT)) for p in actual - set(outputs)]
        if updated != catalogue:
            bad.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            bad.append(VIEW)
        if bad:
            raise SystemExit("stale final-event packet: " + ", ".join(sorted(bad)))
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} files for "
          f"{len(specs)} final-event runs and 19 represented facets.")


if __name__ == "__main__":
    main()
