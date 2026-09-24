#!/usr/bin/env python3
"""Executable 8.5.7 contiguity-property fixtures with bounded IS_CONTIGUOUS oracles."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from generate_contiguous_dummy_effect_fixtures import render_view as prior_render_view

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "doc/catalogues/contiguous_attribute_8_5_7.json"
VIEW = "doc/fortran_2023_8_5_7.md"
RULE_TRUE = "S8.5.7-003"
RULE_FALSE = "S8.5.7-004"
COMPLETION_PREFIX = "CONTIGUOUS PROPERTY OK "
TRUE_FACETS = (
    "attributed-object",
    "whole-nonpointer-array",
    "assumed-shape-contiguous-actual",
    "allocated-array",
    "associated-pointer",
    "gap-free-numeric-section",
    "full-leading-dimensions",
    "full-character-substring",
)
FALSE_FACETS = (
    "ordinary-gapped-section",
    "multidimensional-interleaving",
)
FACETS_BY_RULE = {RULE_TRUE: TRUE_FACETS, RULE_FALSE: FALSE_FACETS}
ORACLE_TRUE = (
    "Eight complete run/effect/f2023 programs discharge eight S8.5.7-003 facets. Each program uses "
    "direct IS_CONTIGUOUS on the actual designator named by a complete p2 route and expects literal true: "
    "a CONTIGUOUS associated array pointer, a nonpointer explicit-shape whole array, an assumed-shape "
    "dummy associated with a contiguous whole-array actual, arrays allocated by ALLOCATE statements "
    "(ordinary allocatable nonzero, ordinary allocatable zero-size, and allocated pointer target), a "
    "non-CONTIGUOUS pointer associated with a contiguous whole target, a gap-free INTEGER section, a "
    "multi-dimensional section taking full leading dimensions, and a full-length CHARACTER substring "
    "array section. Every fixture also checks hand-computed bounds, shape, and nonzero INTEGER or "
    "CHARACTER payload values that are independent of the contiguity inquiry. Feature mutations replace "
    "the inquired expression with a p3 nonconsecutive array subobject; the character full-substring "
    "fixture uses a same-program INTEGER p3 sentinel so the mutation is not weakened by processor "
    "latitude for residual character-section handling. Each "
    "mutated complete program fails before printing the completion line."
)
LIMITATION_TRUE = (
    "The selected p2 cases establish only the standard-required result of IS_CONTIGUOUS and ordinary "
    "bounds/shape/value preservation for the finite designators present in the sources. They do not "
    "measure addresses, storage stride, allocation layout, copy creation, temporaries, timing, padding, "
    "or optimization. The assumed-rank, explicit-stride singleton, vector/multiple-subscript and "
    "ranked-part/complex source-use facets remain pending. A missing positive route is never interpreted "
    "as false; false expectations belong only to the two separately selected S8.5.7-004 fixtures. The "
    "zero-size allocated object is queried only for ALLOCATED, IS_CONTIGUOUS and SHAPE, never for payload."
)
ORACLE_FALSE = (
    "Two complete run/effect/f2023 programs discharge ordinary-gapped-section and multidimensional-"
    "interleaving for S8.5.7-004. Each false expectation is paired in the same program with a p2 positive "
    "control on the same base object, so a default logical false or skipped inquiry cannot satisfy the "
    "case. The one-dimensional case inquires a(-3:3:2), whose at-least-two selected elements are not "
    "consecutive in the base object's element order. The two-dimensional case inquires a(1:2,5:6) from "
    "a(1:3,5:7), whose selected element order contains interleaved excluded base elements. Hand-computed "
    "bounds, shape and nonzero payload values prove the intended valid subobjects are used. Feature "
    "mutations corrupt the positive control designator to the same nonconsecutive form while retaining "
    "its literal true oracle, and wrong-false reverse mutations change the required false to true; both "
    "classes fail in execution."
)
LIMITATION_FALSE = (
    "These negative fixtures use only ordinary INTEGER array subobjects satisfying the complete p3 "
    "conjunction. They do not generalize to zero-size, singleton, zero-length CHARACTER, zero-storage "
    "derived-type, vector-subscript, reversed-order, partial-substring, complex-part or padding-dependent "
    "objects, all of which remain pending or processor dependent unless another source route resolves "
    "them. No diagnostic, trap, address, hidden-copy or performance behavior is required."
)

BATCH296_ORACLE_PREFIX = "Batch296 S8.5.7-003 assumed-rank route: "
BATCH296_LIMIT_PREFIX = "Batch296 S8.5.7-003 assumed-rank limits: "


def carry_owned_paragraph(base, current, prefix):
    paragraphs = [part for part in current.split("\n\n") if part.startswith(prefix)]
    if len(paragraphs) > 1:
        raise ValueError("duplicate carried contiguous-property paragraph: " + prefix)
    return base if not paragraphs else base + "\n\n" + paragraphs[0]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Program:
    def __init__(self, name):
        self.name = name
        self.text = ""
        self.guards = []
        self.feature_span = None
        self.feature_replacement = None

    def add(self, text):
        self.text += text

    def guard(self, guard_id, expression, expected, replacement, *, logical=False):
        operator = ".neqv." if logical else "/="
        literal = ".true." if expected is True else ".false." if expected is False else str(expected)
        prefix = f"  if ({expression} {operator} "
        start = len(self.text) + len(prefix)
        self.guards.append(dict(id=guard_id, expression=expression, expected=literal,
                                replacement=replacement, span=[start, start + len(literal)],
                                failure_token="CP:" + guard_id))
        self.add(prefix + literal + f") error stop 'CP:{guard_id}'\n")

    def guard_true(self, guard_id, expression, *, feature_replacement=None):
        if feature_replacement is not None:
            needle = expression
            prefix = f"  if ({needle} .neqv. "
            start = len(self.text) + len("  if (")
            self.feature_span = [start, start + len(needle)]
            self.feature_replacement = feature_replacement
        self.guard(guard_id, expression, True, ".false.", logical=True)

    def guard_false(self, guard_id, expression):
        self.guard(guard_id, expression, False, ".true.", logical=True)

    def guard_int(self, guard_id, expression, expected):
        self.guard(guard_id, expression, expected, str(expected + 1))

    def finish(self, variant):
        literal = COMPLETION_PREFIX + variant
        prefix = "  write(*,'(a)') '"
        start = len(self.text) + len(prefix)
        self.guards.append(dict(id="completion-output", expression="stdout", expected=literal,
                                replacement=literal + " BAD", span=[start, start + len(literal)],
                                failure_token="stdout"))
        self.add(prefix + literal + "'\nend program " + self.name + "\n")


def header(program_name):
    return f"program {program_name}\n  implicit none\n"


def fill_rank2(name, ilo, ihi, jlo, jhi):
    return ("  do j=" + str(jlo) + "," + str(jhi) + "\n"
            "    do i=" + str(ilo) + "," + str(ihi) + "\n"
            f"      {name}(i,j)=1000+100*j+7*i\n"
            "    end do\n"
            "  end do\n")


def fill_rank1(name, lo, hi):
    return ("  do i=" + str(lo) + "," + str(hi) + "\n"
            f"    {name}(i)=200+11*i\n"
            "  end do\n")


def case_attributed_pointer():
    p = Program("contiguous_property_attributed_pointer")
    p.add(header(p.name) + "  integer, target :: a(-2:2,4:6)\n"
          "  integer, pointer, contiguous :: ptr(:,:)\n  integer :: i, j, sh(2)\n")
    p.add(fill_rank2("a", -2, 2, 4, 6))
    p.add("  ptr(-2:,4:) => a\n  sh=shape(ptr)\n")
    p.guard_true("attributed-contiguous", "is_contiguous(ptr)",
                 feature_replacement="is_contiguous(a(-2:2:2,4:6))")
    for gid, expr, val in (("lb1", "lbound(ptr,1)", -2), ("ub1", "ubound(ptr,1)", 2),
                           ("lb2", "lbound(ptr,2)", 4), ("ub2", "ubound(ptr,2)", 6),
                           ("shape1", "sh(1)", 5), ("shape2", "sh(2)", 3),
                           ("payload", "ptr(-1,5)", 1493)):
        p.guard_int(gid, expr, val)
    p.finish("attributed_pointer")
    return spec("attributed_pointer", RULE_TRUE, "attributed-object", p,
                "CONTIGUOUS pointer ptr(-2:,4:) associated with whole target a(-2:2,4:6); value ptr(-1,5)=1493.")


def case_whole_nonpointer():
    p = Program("contiguous_property_whole_nonpointer")
    p.add(header(p.name) + "  integer :: a(-2:2,4:6)\n  integer, allocatable :: empty(:)\n  integer :: i, j, sh(2), esh(1)\n")
    p.add(fill_rank2("a", -2, 2, 4, 6))
    p.add("  allocate(empty(5:4))\n  sh=shape(a)\n  esh=shape(empty)\n")
    p.guard_true("whole-contiguous", "is_contiguous(a)",
                 feature_replacement="is_contiguous(a(-2:2:2,4:6))")
    p.guard_true("zero-size-whole-contiguous", "is_contiguous(empty)")
    for gid, expr, val in (("lb1", "lbound(a,1)", -2), ("ub1", "ubound(a,1)", 2),
                           ("lb2", "lbound(a,2)", 4), ("ub2", "ubound(a,2)", 6),
                           ("shape1", "sh(1)", 5), ("shape2", "sh(2)", 3),
                           ("empty-allocated", "merge(1,2,allocated(empty))", 1),
                           ("empty-shape", "esh(1)", 0), ("payload", "a(2,6)", 1614)):
        p.guard_int(gid, expr, val)
    p.finish("whole_nonpointer")
    return spec("whole_nonpointer", RULE_TRUE, "whole-nonpointer-array", p,
                "Explicit-shape whole a(-2:2,4:6) and allocated zero-size whole empty(5:4); value a(2,6)=1614.")


def case_assumed_shape():
    p = Program("contiguous_property_assumed_shape")
    p.add(header(p.name) + "  integer :: a(-2:2,4:6)\n  integer :: i, j\n")
    p.add(fill_rank2("a", -2, 2, 4, 6))
    p.add("  call check(a)\n  write(*,'(a)') '" + COMPLETION_PREFIX + "assumed_shape'\ncontains\n"
          "  subroutine check(x)\n    integer, intent(in) :: x(-2:,4:)\n    integer :: sh(2)\n    sh=shape(x)\n")
    p.guard_true("assumed-shape-contiguous", "is_contiguous(x)",
                 feature_replacement="is_contiguous(x(-2:2:2,4:6))")
    for gid, expr, val in (("lb1", "lbound(x,1)", -2), ("ub1", "ubound(x,1)", 2),
                           ("lb2", "lbound(x,2)", 4), ("ub2", "ubound(x,2)", 6),
                           ("shape1", "sh(1)", 5), ("shape2", "sh(2)", 3),
                           ("payload", "x(1,5)", 1507)):
        p.guard_int(gid, expr, val)
    p.add("  end subroutine check\nend program " + p.name + "\n")
    return spec("assumed_shape", RULE_TRUE, "assumed-shape-contiguous-actual", p,
                "Assumed-shape x(-2:,4:) associated with whole contiguous actual a; value x(1,5)=1507.")


def case_allocated_array():
    p = Program("contiguous_property_allocated_array")
    p.add(header(p.name) + "  integer, allocatable :: a(:,:), empty(:)\n  integer, pointer :: pt(:)\n  integer :: i, j, sh(2), esh(1), psh(1)\n")
    p.add("  allocate(a(-3:1,7:9))\n" + fill_rank2("a", -3, 1, 7, 9) +
          "  allocate(empty(8:7))\n  allocate(pt(4:6))\n  do i=4,6\n    pt(i)=300+13*i\n  end do\n"
          "  sh=shape(a)\n  esh=shape(empty)\n  psh=shape(pt)\n")
    p.guard_true("allocatable-contiguous", "is_contiguous(a)",
                 feature_replacement="is_contiguous(a(-3:1:2,7:9))")
    p.guard_true("allocated-empty-contiguous", "is_contiguous(empty)")
    p.guard_true("allocated-pointer-target-contiguous", "is_contiguous(pt)")
    for gid, expr, val in (("allocated", "merge(1,2,allocated(a))", 1), ("pt-associated", "merge(1,2,associated(pt))", 1),
                           ("lb1", "lbound(a,1)", -3), ("ub1", "ubound(a,1)", 1),
                           ("lb2", "lbound(a,2)", 7), ("ub2", "ubound(a,2)", 9),
                           ("shape1", "sh(1)", 5), ("shape2", "sh(2)", 3),
                           ("empty-shape", "esh(1)", 0), ("pt-lb", "lbound(pt,1)", 4),
                           ("pt-ub", "ubound(pt,1)", 6), ("pt-shape", "psh(1)", 3),
                           ("payload", "a(-2,8)", 1786), ("pt-payload", "pt(5)", 365)):
        p.guard_int(gid, expr, val)
    p.finish("allocated_array")
    return spec("allocated_array", RULE_TRUE, "allocated-array", p,
                "ALLOCATE creates a(-3:1,7:9), empty(8:7), and pointer target pt(4:6); values a(-2,8)=1786, pt(5)=365.")


def case_associated_pointer():
    p = Program("contiguous_property_associated_pointer")
    p.add(header(p.name) + "  integer, target :: a(-2:2,4:6)\n  integer, pointer :: ptr(:,:)\n  integer :: i, j, sh(2)\n")
    p.add(fill_rank2("a", -2, 2, 4, 6))
    p.add("  ptr(-2:,4:) => a\n  sh=shape(ptr)\n")
    p.guard_int("associated", "merge(1,2,associated(ptr))", 1)
    p.guard_true("associated-pointer-contiguous", "is_contiguous(ptr)",
                 feature_replacement="is_contiguous(a(-2:2:2,4:6))")
    for gid, expr, val in (("lb1", "lbound(ptr,1)", -2), ("ub1", "ubound(ptr,1)", 2),
                           ("lb2", "lbound(ptr,2)", 4), ("ub2", "ubound(ptr,2)", 6),
                           ("shape1", "sh(1)", 5), ("shape2", "sh(2)", 3),
                           ("payload", "ptr(2,6)", 1614)):
        p.guard_int(gid, expr, val)
    p.finish("associated_pointer")
    return spec("associated_pointer", RULE_TRUE, "associated-pointer", p,
                "Non-CONTIGUOUS pointer ptr associated with contiguous whole target a(-2:2,4:6); value ptr(2,6)=1614.")


def case_gap_free_section():
    p = Program("contiguous_property_gap_free_section")
    p.add(header(p.name) + "  integer :: a(-3:3)\n  integer :: i, sh(1)\n")
    p.add(fill_rank1("a", -3, 3))
    p.add("  sh=shape(a(-2:2))\n")
    p.guard_true("gap-free-section-contiguous", "is_contiguous(a(-2:2))",
                 feature_replacement="is_contiguous(a(-2:2:2))")
    for gid, expr, val in (("lb", "lbound(a(-2:2),1)", 1), ("ub", "ubound(a(-2:2),1)", 5),
                           ("shape", "sh(1)", 5), ("first", "a(-2)", 178), ("last", "a(2)", 222)):
        p.guard_int(gid, expr, val)
    p.finish("gap_free_section")
    return spec("gap_free_section", RULE_TRUE, "gap-free-numeric-section", p,
                "Section a(-2:2) of a(-3:3) selects five consecutive elements; values 178 and 222.")


def case_full_leading_dimensions():
    p = Program("contiguous_property_full_leading_dimensions")
    p.add(header(p.name) + "  integer :: a(-2:2,4:7)\n  integer :: i, j, sh(2)\n")
    p.add(fill_rank2("a", -2, 2, 4, 7))
    p.add("  sh=shape(a(:,4:5))\n")
    p.guard_true("full-leading-section-contiguous", "is_contiguous(a(:,4:5))",
                 feature_replacement="is_contiguous(a(-1:1,4:5))")
    for gid, expr, val in (("lb1", "lbound(a(:,4:5),1)", 1), ("ub1", "ubound(a(:,4:5),1)", 5),
                           ("lb2", "lbound(a(:,4:5),2)", 1), ("ub2", "ubound(a(:,4:5),2)", 2),
                           ("shape1", "sh(1)", 5), ("shape2", "sh(2)", 2),
                           ("payload", "a(2,5)", 1514)):
        p.guard_int(gid, expr, val)
    p.finish("full_leading_dimensions")
    return spec("full_leading_dimensions", RULE_TRUE, "full-leading-dimensions", p,
                "Section a(:,4:5) takes all elements of the leading dimension for two complete columns; value a(2,5)=1514.")


def case_full_character_substring():
    p = Program("contiguous_property_full_character_substring")
    p.add(header(p.name) + "  character(len=4) :: c(2:5)\n  integer :: sentinel(-3:3)\n  integer :: i, sh(1)\n")
    p.add("  do i=-3,3\n    sentinel(i)=200+11*i\n  end do\n  c(2)='ABCD'\n  c(3)='EFGH'\n  c(4)='IJKL'\n  c(5)='MNOP'\n  sh=shape(c(2:4)(1:4))\n")
    p.guard_true("full-character-substring-contiguous", "is_contiguous(c(2:4)(1:4))",
                 feature_replacement="is_contiguous(sentinel(-3:3:2))")
    for gid, expr, val in (("lb", "lbound(c(2:4)(1:4),1)", 1), ("ub", "ubound(c(2:4)(1:4),1)", 3),
                           ("shape", "sh(1)", 3), ("len", "len(c(2:4)(1:4))", 4)):
        p.guard_int(gid, expr, val)
    p.add("  if (c(3)(1:4) /= 'EFGH') error stop 'CP:char-payload'\n")
    p.finish("full_character_substring")
    return spec("full_character_substring", RULE_TRUE, "full-character-substring", p,
                "Full substring range c(2:4)(1:4) preserves length 4 and payload c(3)='EFGH'.")


def case_ordinary_gapped_section():
    p = Program("contiguous_property_ordinary_gapped_section")
    p.add(header(p.name) + "  integer :: a(-3:3)\n  integer :: i, sh(1), gapsh(1)\n")
    p.add(fill_rank1("a", -3, 3))
    p.add("  sh=shape(a(-2:2))\n  gapsh=shape(a(-3:3:2))\n")
    p.guard_true("positive-control-contiguous", "is_contiguous(a(-2:2))",
                 feature_replacement="is_contiguous(a(-3:3:2))")
    p.guard_false("gapped-section-not-contiguous", "is_contiguous(a(-3:3:2))")
    for gid, expr, val in (("positive-shape", "sh(1)", 5), ("gap-lb", "lbound(a(-3:3:2),1)", 1),
                           ("gap-ub", "ubound(a(-3:3:2),1)", 4), ("gap-shape", "gapsh(1)", 4),
                           ("gap-first", "a(-3)", 167), ("gap-last", "a(3)", 233)):
        p.guard_int(gid, expr, val)
    p.finish("ordinary_gapped_section")
    return spec("ordinary_gapped_section", RULE_FALSE, "ordinary-gapped-section", p,
                "Gapped section a(-3:3:2) has four nonconsecutive elements 167,189,211,233, paired with true control a(-2:2).")


def case_multidimensional_interleaving():
    p = Program("contiguous_property_multidimensional_interleaving")
    p.add(header(p.name) + "  integer :: a(1:3,5:7)\n  integer :: i, j, sh(2), gapsh(2)\n")
    p.add(fill_rank2("a", 1, 3, 5, 7))
    p.add("  sh=shape(a(:,5:6))\n  gapsh=shape(a(1:2,5:6))\n")
    p.guard_true("positive-control-contiguous", "is_contiguous(a(:,5:6))",
                 feature_replacement="is_contiguous(a(1:2,5:6))")
    p.guard_false("interleaved-section-not-contiguous", "is_contiguous(a(1:2,5:6))")
    for gid, expr, val in (("positive-shape1", "sh(1)", 3), ("positive-shape2", "sh(2)", 2),
                           ("gap-lb1", "lbound(a(1:2,5:6),1)", 1), ("gap-ub1", "ubound(a(1:2,5:6),1)", 2),
                           ("gap-lb2", "lbound(a(1:2,5:6),2)", 1), ("gap-ub2", "ubound(a(1:2,5:6),2)", 2),
                           ("gap-shape1", "gapsh(1)", 2), ("gap-shape2", "gapsh(2)", 2),
                           ("gap-first", "a(1,5)", 1507), ("gap-last", "a(2,6)", 1614)):
        p.guard_int(gid, expr, val)
    p.finish("multidimensional_interleaving")
    return spec("multidimensional_interleaving", RULE_FALSE, "multidimensional-interleaving", p,
                "Section a(1:2,5:6) excludes a(3,5) between selected elements in base element order; values 1507 and 1614.")


def spec(variant, rule, facet, program, derivation):
    raw = program.text.encode("ascii")
    for guard in program.guards:
        start, end = guard["span"]
        if raw[start:end].decode("ascii") != guard["expected"]:
            raise ValueError(f"guard span mismatch for {variant}:{guard['id']}")
    if program.feature_span:
        start, end = program.feature_span
        original = raw[start:end].decode("ascii")
        if not original.startswith("is_contiguous("):
            raise ValueError("feature mutation must replace the queried designator")
    return dict(id=identifier(rule, variant), variant=variant, rule=rule, facet=facet,
                source=program.text, source_sha256=sha(raw), guards=program.guards,
                feature_span=program.feature_span, feature_replacement=program.feature_replacement,
                completion=COMPLETION_PREFIX + variant + "\n", derivation=derivation)


def identifier(rule, variant):
    return rule.replace(".", "_").replace("-", "_") + "_valid__contiguous_property_" + variant


def source_specs():
    specs = {row["id"]: row for row in (
        case_attributed_pointer(), case_whole_nonpointer(), case_assumed_shape(),
        case_allocated_array(), case_associated_pointer(), case_gap_free_section(),
        case_full_leading_dimensions(), case_full_character_substring(),
        case_ordinary_gapped_section(), case_multidimensional_interleaving())}
    if len(specs) != 10:
        raise ValueError("expected ten contiguous property fixtures")
    return specs


def build_corpus(root=ROOT):
    specs = source_specs()
    files = {}
    for name, row in specs.items():
        directory = Path(root) / "tests" / "fixtures" / ("contiguous_property_" + row["variant"])
        manifest = dict(schema_version=1, id=name, rule=row["rule"], facets=[row["facet"]],
                        evidence="effect", standard="f2023", files=["source.f90"],
                        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
                        link=dict(driver="fortran", objects=["source.o"], output="program"),
                        expect=dict(phase="run", outcome="success", exit_code=0,
                                    stdout=row["completion"], stderr=""))
        row["path"] = str((directory / "fixture.json").relative_to(root))
        row["manifest"] = manifest
        files[directory / "source.f90"] = row["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def wrong_oracle_source(row, guard):
    raw = row["source"].encode("ascii")
    start, end = guard["span"]
    if raw[start:end].decode("ascii") != guard["expected"]:
        raise ValueError("wrong-oracle span stale")
    return raw[:start] + guard["replacement"].encode("ascii") + raw[end:]


def feature_mutation_source(row):
    raw = row["source"].encode("ascii")
    start, end = row["feature_span"]
    return raw[:start] + row["feature_replacement"].encode("ascii") + raw[end:]


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    for rule, facets in FACETS_BY_RULE.items():
        requirement = next(row for row in result["requirements"] if row["id"] == rule)
        if not set(facets) <= set(requirement["facets"]):
            raise ValueError(f"selected {rule} facet definitions changed")
        for facet in facets:
            requirement["pending"].pop(facet, None)
        if rule == RULE_TRUE:
            requirement["oracle"] = carry_owned_paragraph(ORACLE_TRUE, requirement.get("oracle", ""),
                                                           BATCH296_ORACLE_PREFIX)
            requirement["oracle_limitation"] = carry_owned_paragraph(LIMITATION_TRUE,
                                                                      requirement.get("oracle_limitation", ""),
                                                                      BATCH296_LIMIT_PREFIX)
        else:
            requirement["oracle"] = ORACLE_FALSE
            requirement["oracle_limitation"] = LIMITATION_FALSE
    return result


def render_view(catalogue, root=ROOT):
    text = prior_render_view(catalogue, root)
    begin, end = "<!-- BEGIN CONTIGUOUS PROPERTY EFFECTS -->", "<!-- END CONTIGUOUS PROPERTY EFFECTS -->"
    if begin in text or end in text:
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("invalid contiguous-property view boundaries")
        before, rest = text.split(begin)
        _, after = rest.split(end)
    else:
        before, after = text.rstrip() + "\n\n", "\n"
    req_true = next(row for row in catalogue["requirements"] if row["id"] == RULE_TRUE)
    req_false = next(row for row in catalogue["requirements"] if row["id"] == RULE_FALSE)
    detail = (
        "## Bounded CONTIGUOUS property runtime effects\n\n"
        "Ten complete run/effect programs exercise only standard-required contiguity\n"
        "answers. Eight positive cases use 8.5.7 p2 routes and require\n"
        "IS_CONTIGUOUS(...)=true; two negative cases use the complete p3\n"
        "nonconsecutive-subobject conjunction and require false. The false cases\n"
        "contain positive controls in the same source, so zero-filled logical storage\n"
        "or skipped execution cannot satisfy the oracle.\n\n"
        "Every source hand-computes nonzero INTEGER or CHARACTER payloads together\n"
        "with LBOUND/UBOUND/SHAPE checks. Zero-size allocated arrays are queried\n"
        "only for allocation, shape and contiguity, never for payload. The fixtures\n"
        "make no assertion about addresses, storage layout, temporaries, copy\n"
        "strategy, allocation mechanism, padding, performance or optimization.\n\n"
        "Each case has an exact feature mutation that replaces the queried designator\n"
        "or positive-control designator by a p3 nonconsecutive subobject while\n"
        "leaving the original true oracle in place. Wrong-oracle mutations cover\n"
        "each contiguity, bounds, shape, payload and completion literal; the p3\n"
        "cases also have reverse false-to-true mutations.\n\n"
        f"{len(req_true['pending'])} {RULE_TRUE} facets and {len(req_false['pending'])} {RULE_FALSE} facets remain PENDING.\n"
        "Assumed-rank, singleton/stride-boundary, vector/multiple-subscript, ranked-part,\n"
        "complex-part, zero-storage-type, ordered-reversal and processor-dependent\n"
        "residual cases remain outside this packet.\n\n")
    return before + begin + "\n\n" + detail + end + after


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    args = parser.parse_args()
    if args.check and args.sync_catalogue:
        parser.error("--check and --sync-catalogue are separate operations")
    files, _ = build_corpus()
    catalogue = json.loads((ROOT / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue)
    view = render_view(updated)
    actual = {path for path in (ROOT / "tests/fixtures").glob("contiguous_property_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale contiguous property corpus: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in contiguous property corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} files: {len(files)//2} run cases, "
          f"{sum(len(v) for v in FACETS_BY_RULE.values())} facets.")


if __name__ == "__main__":
    main()
