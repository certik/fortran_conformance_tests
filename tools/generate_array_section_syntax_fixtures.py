#!/usr/bin/env python3
"""Executable fixtures for Fortran 2023 9.5.3.1 array element/section syntax."""

import argparse
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION = "9.5.3.1"
CATALOGUE = "doc/catalogues/array_element_section_syntax_9_5_3_1.json"
VIEW = "doc/fortran_2023_9_5_3_1.md"
SUMMARY_BEGIN = "<!-- BEGIN ARRAY SECTION SYNTAX FIXTURES -->"
SUMMARY_END = "<!-- END ARRAY SECTION SYNTAX FIXTURES -->"

SELECTED = {
    "R917": ["data-ref-array-element-form"],
    "C924": ["all-part-refs-rank-zero", "last-part-ref-has-subscript-list"],
    "R918": ["data-ref-section-form", "data-ref-with-substring-range-form"],
    "C925": ["exactly-one-nonzero-rank-part-ref", "final-section-subscript-list-nonzero-rank"],
    "C926": ["character-data-ref-with-substring-range"],
    "R921": ["subscript-alternative", "subscript-triplet-alternative", "vector-subscript-alternative"],
    "R922": ["lower-and-upper-triplet", "omitted-first-subscript", "omitted-second-subscript", "explicit-stride"],
    "R924": ["literal-scalar-int-stride", "variable-scalar-int-stride"],
    "R925": ["int-expr-vector-subscript-form"],
    "C929": ["integer-rank-one-array-expression"],
    "S9.5.3.1-001": ["substring-range-applies-to-each-section-element"],
}

PREFIX = "array_section_syntax_"

CHECKS = """module array_section_syntax_checks
implicit none
private
integer, save :: checks = 0
public :: check_int_scalar, check_int_rank1, check_char_rank1, finish_checks
contains
subroutine fail(label, why)
  character(*), intent(in) :: label, why
  write(*,'(a,1x,a)') trim(label), trim(why)
  error stop 1
end subroutine fail
subroutine check_int_scalar(label, actual, expected)
  character(*), intent(in) :: label
  integer, intent(in) :: actual(..)
  integer, intent(in) :: expected
  select rank(actual)
  rank(0)
    if (actual /= expected) call fail(label, 'scalar-value')
  rank default
    call fail(label, 'scalar-rank')
  end select
  checks = checks + 1
end subroutine check_int_scalar
subroutine check_int_rank1(label, actual, expected)
  character(*), intent(in) :: label
  integer, intent(in) :: actual(..)
  integer, intent(in) :: expected(:)
  select rank(actual)
  rank(1)
    if (size(actual) /= size(expected)) call fail(label, 'rank1-size')
    if (size(actual) == size(expected)) then
      if (any(actual /= expected)) call fail(label, 'rank1-values')
    end if
  rank default
    call fail(label, 'rank1-rank')
  end select
  checks = checks + 1
end subroutine check_int_rank1
subroutine check_char_rank1(label, actual, expected, expected_len)
  character(*), intent(in) :: label
  character(len=*), intent(in) :: actual(:)
  character(len=*), intent(in) :: expected(:)
  integer, intent(in) :: expected_len
  integer :: i
  if (len(actual) /= expected_len) call fail(label, 'char-length')
  if (len(expected) /= expected_len) call fail(label, 'expected-char-length')
  if (size(actual) /= size(expected)) call fail(label, 'char-size')
  do i = 1, min(size(actual), size(expected))
    if (actual(i) /= expected(i)) call fail(label, 'char-value')
  end do
  checks = checks + 1
end subroutine check_char_rank1
subroutine finish_checks(expected, message)
  integer, intent(in) :: expected
  character(*), intent(in) :: message
  if (checks /= expected) call fail('finish', 'check-count')
  write(*,'(a)') message
end subroutine finish_checks
end module array_section_syntax_checks
"""

ARRAY_DECL = """integer :: a(-2:3)
"""

ARRAY_ASSIGN = """a=-777
a(-2)=11; a(-1)=22; a(0)=33; a(1)=44; a(2)=55; a(3)=66
"""

CHAR_DECL = """character(len=5) :: words(-1:1)
"""

CHAR_ASSIGN = """words='#####'
words(-1)='abcde'; words(0)='vwxyz'; words(1)='lmnop'
"""

MATRIX_DECL = """integer :: m(-1:1,-1:1)
"""

MATRIX_ASSIGN = """m=-777
m(-1,-1)=11; m(0,-1)=21; m(1,-1)=31
m(-1,0)=12; m(0,0)=22; m(1,0)=32
m(-1,1)=13; m(0,1)=23; m(1,1)=33
"""

COMMON_ARRAY_SETUP = """integer :: a(-2:3)
a(-2)=11; a(-1)=22; a(0)=33; a(1)=44; a(2)=55; a(3)=66
"""

COMMON_CHAR_SETUP = """character(len=5) :: words(-1:1)
words(-1)='abcde'; words(0)='vwxyz'; words(1)='lmnop'
"""

COMMON_MATRIX_SETUP = """integer :: m(-1:1,-1:1)
m(-1,-1)=11; m(0,-1)=21; m(1,-1)=31
m(-1,0)=12; m(0,0)=22; m(1,0)=32
m(-1,1)=13; m(0,1)=23; m(1,1)=33
"""


def rid(rule):
    return rule.replace('.', '_').replace('-', '_')


def identifier(rule, variant):
    return rid(rule) + "_valid__" + PREFIX + variant


def stdout_for(variant):
    return "ARRAY SECTION SYNTAX " + variant.upper().replace('_', ' ') + " OK\n"


def program(body, expected_checks, message, declarations=""):
    return (CHECKS + "program p\nuse array_section_syntax_checks\nimplicit none\n" + declarations
            + body + f"call finish_checks({expected_checks}, '{message}')\nend program p\n")


def mut(mid, expected, replacement, category="feature"):
    return {"id": mid, "expected": expected, "replacement": replacement, "category": category}


def case(rule, variant, facets, body, checks, mutations, declarations=""):
    source = program(body, checks, stdout_for(variant).rstrip("\n"), declarations)
    for mutation in mutations:
        count = source.count(mutation["expected"])
        if count != 1:
            raise ValueError(f"{variant}:{mutation['id']} binds {count} source spans")
        if mutation["expected"] == mutation["replacement"]:
            raise ValueError(f"{variant}:{mutation['id']} is vacuous")
    return {
        "id": identifier(rule, variant), "rule": rule, "variant": variant, "facets": list(facets),
        "source": source, "stdout": stdout_for(variant), "mutations": list(mutations),
        "expected_checks": checks,
    }


def source_specs():
    specs = []
    specs.append(case(
        "R917", "array_element_data_ref", SELECTED["R917"],
        """type element_box
  integer :: c(-1:1)
end type element_box
type(element_box) :: box
integer :: k
box%c=-777; box%c(-1)=101; box%c(0)=202; box%c(1)=303
k=0
call check_int_rank1('R917 data-ref element', [box%c(k)], [202])
""",
        1,
        [mut("remove-final-subscript-list", "box%c(k)", "box%c"),
         mut("change-selected-subscript", "box%c(k)", "box%c(1)")],
    ))
    specs.append(case(
        "C924", "element_part_ref_rules", SELECTED["C924"],
        """type child_t
  integer :: c(-1:1)
end type child_t
type parent_t
  type(child_t) :: child
end type parent_t
type(parent_t) :: box
integer :: j
box%child%c=-777; box%child%c(-1)=401; box%child%c(0)=602; box%child%c(1)=803
j=0
call check_int_rank1('C924 component element', [box%child%c(j)], [602])
""",
        1,
        [mut("remove-rightmost-subscript-list", "box%child%c(j)", "box%child%c"),
         mut("select-neighbour-component", "box%child%c(j)", "box%child%c(1)")],
    ))
    specs.append(case(
        "R918", "data_ref_and_substring_sections", SELECTED["R918"],
        ARRAY_ASSIGN + CHAR_ASSIGN +
        """call check_int_rank1('R918 data-ref section', a(-1:3:2), [22,44,66])
call check_char_rank1('R918 substring section', words(:)(2:4), [character(len=3)::'bcd','wxy','mno'], 3)
""",
        2,
        [mut("remove-triplet-stride", "a(-1:3:2)", "a(-1:3)"),
         mut("remove-substring-range", "words(:)(2:4)", "words(:)")],
        declarations=ARRAY_DECL + CHAR_DECL,
    ))
    specs.append(case(
        "C925", "final_section_nonzero_rank", SELECTED["C925"],
        ARRAY_ASSIGN +
        """call check_int_rank1('C925 final section rank', a(-1:3:2), [22,44,66])
""",
        1,
        [mut("remove-section-list-rank", "a(-1:3:2)", "[a(0)]"),
         mut("change-stride-sign", "a(-1:3:2)", "a(3:-1:-2)")],
        declarations=ARRAY_DECL,
    ))
    specs.append(case(
        "C926", "character_substring_section", SELECTED["C926"],
        CHAR_ASSIGN +
        """call check_char_rank1('C926 character data-ref substring', words(:)(2:4), &
     [character(len=3)::'bcd','wxy','mno'], 3)
""",
        1,
        [mut("remove-substring-range", "words(:)(2:4)", "words(:)"),
         mut("omit-section-lower", "words(:)(2:4)", "words(0:)(2:4)")],
        declarations=CHAR_DECL,
    ))
    specs.append(case(
        "R921", "section_subscript_alternatives", SELECTED["R921"],
        ARRAY_ASSIGN + MATRIX_ASSIGN +
        """call check_int_rank1('R921 scalar subscript alternative', m(0,:), [21,22,23])
call check_int_rank1('R921 triplet alternative', a(-1:3:2), [22,44,66])
call check_int_rank1('R921 vector alternative', a([3,-2,1]), [66,11,44])
""",
        3,
        [mut("swap-subscript-order", "m(0,:)", "m(:,0)"),
         mut("remove-triplet-stride", "a(-1:3:2)", "a(-1:3)"),
         mut("replace-vector-with-triplet", "a([3,-2,1])", "a(-2:3:2)")],
        declarations=ARRAY_DECL + MATRIX_DECL,
    ))
    specs.append(case(
        "R922", "subscript_triplet_forms", SELECTED["R922"],
        ARRAY_ASSIGN +
        """call check_int_rank1('R922 lower upper', a(-1:1), [22,33,44])
call check_int_rank1('R922 omitted lower', a(:1), [11,22,33,44])
call check_int_rank1('R922 omitted upper', a(1:), [44,55,66])
call check_int_rank1('R922 explicit stride', a(-2:2:2), [11,33,55])
""",
        4,
        [mut("omit-first-bound", "a(-1:1)", "a(:1)"),
         mut("supply-omitted-lower", "a(:1)", "a(-1:1)"),
         mut("supply-omitted-upper", "a(1:)", "a(1:2)"),
         mut("remove-explicit-stride", "a(-2:2:2)", "a(-2:2)")],
        declarations=ARRAY_DECL,
    ))
    specs.append(case(
        "R924", "scalar_stride_expressions", SELECTED["R924"],
        ARRAY_ASSIGN +
        """step=-2
call check_int_rank1('R924 literal stride', a(-2:2:2), [11,33,55])
call check_int_rank1('R924 variable stride', a(2:-2:step), [55,33,11])
""",
        2,
        [mut("remove-literal-stride", "a(-2:2:2)", "a(-2:2)"),
         mut("remove-variable-stride", "a(2:-2:step)", "a(2:-2)"),
         mut("change-stride-sign", "step=-2", "step=2")],
        declarations=ARRAY_DECL + "integer :: step\n",
    ))
    specs.append(case(
        "R925", "vector_subscript_int_expr", SELECTED["R925"],
        ARRAY_ASSIGN +
        """idx=[3,-2,1]
call check_int_rank1('R925 vector int-expr', a(idx), [66,11,44])
""",
        1,
        [mut("swap-vector-order", "idx=[3,-2,1]", "idx=[-2,3,1]"),
         mut("replace-vector-with-triplet", "a(idx)", "a(-2:3:2)")],
        declarations=ARRAY_DECL + "integer :: idx(3)\n",
    ))
    specs.append(case(
        "C929", "rank_one_integer_vector", SELECTED["C929"],
        ARRAY_ASSIGN +
        """call check_int_rank1('C929 rank-one integer vector', a([3,-2,1]), [66,11,44])
""",
        1,
        [mut("replace-vector-with-scalar-subscript", "a([3,-2,1])", "[a(1)]"),
         mut("swap-vector-subscript-order", "a([3,-2,1])", "a([-2,3,1])")],
        declarations=ARRAY_DECL,
    ))
    specs.append(case(
        "S9.5.3.1-001", "substring_elementwise", SELECTED["S9.5.3.1-001"],
        CHAR_ASSIGN +
        """call check_char_rank1('p1 elementwise substrings', words(:)(2:4), &
     [character(len=3)::'bcd','wxy','mno'], 3)
""",
        1,
        [mut("remove-substring-range", "words(:)(2:4)", "words(:)"),
         mut("omit-section-lower", "words(:)(2:4)", "words(0:)(2:4)")],
        declarations=CHAR_DECL,
    ))
    return {spec["id"]: spec for spec in specs}


def mutated_source(spec, mutation):
    return spec["source"].replace(mutation["expected"], mutation["replacement"], 1)


def build_corpus(root=ROOT):
    root = Path(root)
    specs = source_specs()
    files = {}
    for spec in specs.values():
        directory = root / "tests/fixtures" / (PREFIX + spec["variant"])
        manifest = {
            "schema_version": 1,
            "id": spec["id"],
            "rule": spec["rule"],
            "facets": spec["facets"],
            "evidence": "effect" if spec["rule"].startswith("S") else "positive-control",
            "standard": "f2023",
            "files": ["source.f90"],
            "build": [{"id": "source", "source": "source.f90", "language": "fortran", "form": "free", "output": "source.o"}],
            "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
            "expect": {"phase": "run", "outcome": "success", "exit_code": 0,
                       "stdout": spec["stdout"], "stderr": ""},
        }
        spec["manifest"] = manifest
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def append_owned(text, paragraph):
    prefix = paragraph.split(": ", 1)[0] + ": "
    if paragraph in text:
        return text
    if prefix in text:
        before, rest = text.split(prefix, 1)
        tail = rest.split("\n\n", 1)[1] if "\n\n" in rest else ""
        return before.rstrip() + "\n\n" + paragraph + ("\n\n" + tail if tail else "")
    return text.rstrip() + "\n\n" + paragraph


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        row = by_rule[rule]
        if not set(facets) <= set(row["facets"]):
            raise ValueError("selected facets no longer belong to " + rule)
        for facet in facets:
            row.get("pending", {}).pop(facet, None)
        row["oracle"] = append_owned(row.get("oracle", ""), ORACLE_NOTES[rule])
        row["oracle_limitation"] = append_owned(row.get("oracle_limitation", ""), LIMITATION_NOTES[rule])
    return updated


ORACLE_NOTES = {
    "R917": "Array-section syntax fixture oracle: one run/positive-control/f2023 program selects box%c(k) from a scalar derived-type data-ref with a nondefault component lower bound and distinct values, then places that scalar element in a one-element constructor. The observer requires size one and value 202; removing the final subscript contributes the whole component array and changing the subscript selects 303.",
    "C924": "Array-section syntax fixture oracle: one run/positive-control/f2023 program observes box%child%c(j) through a scalar parent chain and a one-element constructor. The rightmost part-ref has the only subscript list and every part-ref is rank zero; removing that list contributes the rank-one component array and selecting c(1) yields 803.",
    "R918": "Array-section syntax fixture oracle: one run/positive-control/f2023 program observes an integer data-ref section a(-1:3:2) with shape three and values [22,44,66], and a character array-section substring words(:)(2:4) with length three and values ['bcd','wxy','mno']. Removing the stride or substring range changes rank-one extent, values, or character length.",
    "C925": "Array-section syntax fixture oracle: one run/positive-control/f2023 program observes a(-1:3:2), whose final part-ref section-subscript-list has nonzero rank and is the only nonzero-rank part-ref. The observer checks rank one, size three, and values [22,44,66]; replacing the section by a one-element constructor or reversing the stride changes the observed size, value, or order.",
    "C926": "Array-section syntax fixture oracle: one run/positive-control/f2023 program applies words(:)(2:4) only to a CHARACTER data-ref. The observer checks element length before equality and then the three substrings ['bcd','wxy','mno']; removing the substring range leaves length five and omitting the lower section bound drops an element.",
    "R921": "Array-section syntax fixture oracle: one run/positive-control/f2023 program exercises a scalar subscript alternative m(0,:), a subscript-triplet alternative a(-1:3:2), and a vector-subscript alternative a([3,-2,1]). Distinct coordinate-coded values make swapping subscript order, removing the triplet stride, or replacing the vector by a triplet fail.",
    "R922": "Array-section syntax fixture oracle: one run/positive-control/f2023 program covers lower-and-upper triplet a(-1:1), omitted first subscript a(:1), omitted second subscript a(1:), and explicit stride a(-2:2:2), all on an array with lower bound -2. Mutants omit or supply a bound or remove the stride and thereby change shape or values.",
    "R924": "Array-section syntax fixture oracle: one run/positive-control/f2023 program observes both literal scalar stride a(-2:2:2) and variable scalar stride a(2:-2:step) with step=-2. Removing either stride or changing the variable stride sign is conforming but changes the selected sequence.",
    "R925": "Array-section syntax fixture oracle: one run/positive-control/f2023 program uses the integer expression idx as the vector subscript in a(idx), yielding values [66,11,44]. Reordering idx or replacing the vector subscript by a triplet is conforming and changes the selected elements.",
    "C929": "Array-section syntax fixture oracle: one run/positive-control/f2023 program uses the rank-one integer array expression [3,-2,1] as a vector subscript and checks rank one plus values [66,11,44]. Replacing it with a one-element constructor around a scalar subscript changes size and value, while reordering the vector changes values.",
    "S9.5.3.1-001": "Array-section syntax fixture oracle: one run/effect/f2023 program observes words(:)(2:4) as a rank-one character array whose element length is three and whose elements are the substrings ['bcd','wxy','mno'] of the corresponding section elements. Removing the substring range or dropping the lower section element changes length, size, or values.",
}

LIMITATION_NOTES = {
    rule: "Array-section syntax fixture boundaries: these selected fixtures cover only ordinary single-image default INTEGER arrays and default CHARACTER arrays with constant bounds and defined values. Multiple-subscript @ forms, multiple-subscript-triplets, assumed-size omission constraints, diagnostic negatives, zero stride, duplicate-vector definability, finalization, coarrays, pointers, allocatables, complex part designators, and nonfinal array-parent component sections remain pending or delegated to dependent clauses. No I/O numeric formatting, rounding, optional plus sign, storage-layout, address, undefined-value, or compiler-consensus oracle is used."
    for rule in SELECTED
}


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated view boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    before = before.replace(
        "All facets in this packet are pending source plans. No Fortran test program, compiler invocation, execution evidence, oracle approval, fixture approval or coverage claim is supplied here.",
        "Selected array element and section syntax facets now have executable positive-control fixtures; unsupported @ multiple-subscript forms, diagnostics, assumed-size omission constraints, and remaining source plans stay pending.")
    summary = (SUMMARY_BEGIN + "\n"
        "## Array element and section syntax fixture observations\n\n"
        "Eleven complete run/f2023 fixtures cover twenty selected facets of 9.5.3.1. They use nondefault lower bounds, distinct integer values, and distinct fixed-length character values so wrong bound, stride, vector order, subscript-order, rank, or substring-length behavior changes a checked result. Character assertions check LEN before equality. No numeric formatted-output oracle is used.\n\n"
        "The generator records conforming feature mutations for every fixture, including removing the tested subscript list, section triplet stride, vector subscript, or substring range; changing stride sign; omitting or supplying a triplet bound; and swapping subscript/vector order. Multiple-subscript @ forms, multiple-subscript-triplets, assumed-size omission constraints, negatives, zero stride, nonfinal component sections, and complex part designators remain pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before:
        lead, owned = before.split(SUMMARY_BEGIN)
        _, tail = owned.split(SUMMARY_END)
        before = lead.rstrip() + "\n\n" + summary + tail
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    generated = "\n".join(render_requirement(row) for row in catalogue["requirements"])
    return before + begin + "\n\n" + generated + "\n" + end + after


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
            raise SystemExit("stale array-section syntax fixture packet: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def executable_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}", str(source), "-o", str(output)]
    return [compiler, f"-std={std}", str(source), "-o", str(output)]


def check_mutations(root, compiler, std):
    root = Path(root)
    _, specs = build_corpus(root)
    mutations = [(spec, mutation) for spec in specs.values() for mutation in spec["mutations"]]
    if not mutations:
        raise SystemExit("no array-section syntax mutations defined")
    workspace = root / ".array_section_syntax_mutations"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    failures = []
    try:
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{mutation['id']}"
            case_dir.mkdir()
            source = case_dir / "source.f90"
            exe = case_dir / "program"
            source.write_text(mutated_source(spec, mutation))
            compile_result = subprocess.run(
                executable_command(compiler, std, source, exe), cwd=case_dir, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            if compile_result.returncode != 0:
                failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{compile_result.stdout}")
                continue
            run_result = subprocess.run([str(exe)], cwd=case_dir, text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            if run_result.returncode == 0:
                failures.append(f"{spec['id']}:{mutation['id']} survived with output:\n{run_result.stdout}")
        if failures:
            raise SystemExit("\n\n".join(failures))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    print(f"Mutation check: {len(mutations)}/{len(mutations)} mutants failed for {compiler} ({std}).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--check-mutations", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std")
    args = parser.parse_args()
    if sum(map(bool, (args.check, args.sync_catalogue, args.check_mutations))) > 1:
        parser.error("--check, --sync-catalogue and --check-mutations are separate operations")
    if args.check_mutations:
        if not args.compiler or not args.std:
            parser.error("--check-mutations requires --compiler and --std")
        check_mutations(args.root, args.compiler, args.std)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} array-section syntax cases, "
          f"{sum(len(s['facets']) for s in specs.values())} facets and "
          f"{sum(len(s['mutations']) for s in specs.values())} feature mutations.")


if __name__ == "__main__":
    main()
