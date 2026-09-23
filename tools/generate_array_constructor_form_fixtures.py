#!/usr/bin/env python3
"""Finite array-constructor form, control and diagnostic fixtures for 7.8."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.8"
CATALOGUE = "doc/catalogues/array_constructors.json"
PREFIX = "array_constructor_form_"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "assert", "asr", "verifier", "out of memory", "traceback",
    "unknown exception", "segmentation", "bus error", "abort", "cannot read module",
)
SELECTED = {
    "R777": ["slash-parenthesis-admission", "square-bracket-admission"],
    "R778": ["typed-empty-integer", "typed-nonempty", "untyped-nonempty", "untyped-empty-list"],
    "R781": ["scalar-expression-admission", "array-expression-admission", "implied-do-admission"],
    "R782": ["single-body-value", "multiple-body-values", "nested-form"],
    "R783": ["inferred-integer-variable", "runtime-bound-and-step-expressions"],
    "C7120": ["same-type-kind-different-ranks", "different-intrinsic-type"],
    "C7122": ["same-derived-type-admission"],
    "C7128": ["distinct-nested-variables"],
    "S7.8-002": ["runtime-equal-length-controls"],
    "S7.8-007": ["constant-length-zero-trip-control"],
}
ORACLE_PREFIX = "Array constructor form packet implementation: "
LIMIT_PREFIX = "Array constructor form packet boundaries: "
ORACLE = ORACLE_PREFIX + (
    "15 generated fixtures represent 20 selected 7.8 facets. Thirteen valid run/positive-control fixtures use six distinct source bodies with "
    "ASSOCIATE names or direct SIZE/LEN/SUM inquiries to observe the actual constructor form, finite "
    "sequence, type parameter, derived-component and zero-size effects. Two compile-time negatives are "
    "limited to numbered syntax/constraint obligations and each has a one-property conforming control in "
    "the same packet: [] is repaired only to [INTEGER ::], and [1,vec,2.0] is repaired only to [1,vec,2]. "
    "The slash and square delimiter forms are both exercised and compared on non-palindromic values; "
    "typed nonempty INTEGER and derived constructors are distinct from untyped homogeneous constructors; "
    "implied-DO body order, multiple body values, distinct nested variables and runtime scalar bounds are "
    "checked with literal element guards. CHARACTER witnesses check LEN before value equality, and zero-size "
    "constructors also use type-specific operations (SUM for INTEGER, LEN for CHARACTER)."
)
LIMITATION = LIMIT_PREFIX + (
    "only the 20 named facets are discharged. No inline integer-type-spec facet is claimed because both "
    "qualifying compilers reject that valid syntax in this frozen toolchain window. No mismatched-delimiter, "
    "missing-body, missing-bound or nested-same-name diagnostic is shipped; LFortran currently accepts some "
    "invalid delimiter/nested-control sources or reports only earlier syntax failures for inline forms. No "
    "enum, enumeration, BOZ, REAL/COMPLEX numeric conversion, polymorphic dynamic-type, abstract, PDT kind/LEN, "
    "character-kind, processor-representation, optional-evaluation or side-effect order claim is added. The "
    "batch130 array_constructor_value fixtures and their catalogue paragraphs remain unmodified. The rendered "
    "7.8 markdown is intentionally not generator-owned by this packet."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(rule, variant, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__array_constructor_form_" + variant


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, p in enumerate(paragraphs) if p.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned array-constructor form paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


def locate_line(source, needle):
    lines = source.splitlines()
    matches = [i + 1 for i, line in enumerate(lines) if needle in line]
    if len(matches) != 1:
        raise ValueError(f"line anchor is not unique for {needle!r}")
    return matches[0]


def remove_lines(source, *needles):
    for needle in needles:
        line = "  " + needle + "\n"
        if source.count(line) != 1:
            raise ValueError("mutation line is not unique: " + needle)
        source = source.replace(line, "")
    return source


def manifest(spec):
    item = dict(
        schema_version=1,
        id=spec["id"],
        rule=spec["rule"],
        facets=spec["facets"],
        standard="f2023",
        evidence=spec["evidence"],
        files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
    )
    if spec["kind"] == "invalid":
        item["expect"] = dict(phase="compile", step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
    else:
        item["link"] = dict(driver="fortran", objects=["source.o"], output="program")
        item["expect"] = dict(phase="run", outcome="success", exit_code=0)
    return item


def valid_case(rule, variant, facets, source, derivation, observations, mutations):
    return dict(id=identifier(rule, variant), rule=rule, variant=variant, kind="valid", evidence="positive-control",
                facets=list(facets), source=source, derivation=derivation,
                observations=list(observations), mutations=list(mutations))


def invalid_case(rule, variant, facets, source, derivation, diagnostic_line, contains, control_id,
                 control_rule, control_facets, repair_note):
    diag = dict(file="source.f90", line=diagnostic_line, end_line=diagnostic_line,
                contains_any=list(contains), excludes_any=list(EXCLUSIONS))
    return dict(id=identifier(rule, variant, "invalid"), rule=rule, variant=variant, kind="invalid",
                evidence="effect", facets=list(facets), source=source, derivation=derivation,
                diagnostic=diag, control_id=control_id, control_rule=control_rule,
                control_facets=list(control_facets), repair_note=repair_note, observations=[], mutations=[])


def source_specs():
    specs = []
    delimiter = """program p
implicit none
associate(slash => (/11,13/))
  if (size(slash) /= 2) error stop 1
  if (slash(1) /= 11) error stop 2
  if (slash(2) /= 13) error stop 3
end associate
associate(square => [11,13])
  if (size(square) /= 2) error stop 4
  if (square(1) /= 11) error stop 5
  if (square(2) /= 13) error stop 6
end associate
end program p
"""
    specs.append(valid_case(
        "R777", "delimiter_forms", SELECTED["R777"], delimiter,
        "R777 provides exactly the (/ ac-spec /) and [ ac-spec ] alternatives; the same two INTEGER values are observed through both matched forms.",
        ["slash size 2", "slash values 11,13", "square size 2", "square values 11,13"],
        [dict(id="slash-swap", original="(/11,13/)", replacement="(/13,11/)", source=delimiter.replace("(/11,13/)", "(/13,11/)", 1)),
         dict(id="square-swap", original="[11,13]", replacement="[13,11]", source=delimiter.replace("[11,13]", "[13,11]", 1))]))

    empty_control = """program p
implicit none
integer :: n
n = size([integer ::])
if (n /= 0) error stop 1
if (sum([integer ::]) /= 0) error stop 2
end program p
"""
    specs.append(valid_case(
        "R778", "typed_empty_integer_control", ["typed-empty-integer"], empty_control,
        "R778's type-spec :: alternative admits a syntactically empty INTEGER constructor; SIZE is zero and SUM is an INTEGER-only operation.",
        ["size [integer ::] is 0", "sum [integer ::] is integer zero"],
        [dict(id="add-ac-value", original="[integer ::]", replacement="[integer :: 5]", source=empty_control.replace("[integer ::]", "[integer :: 5]", 1))]))
    empty_invalid = """program p
implicit none
integer :: n
n = size([])
if (n /= 0) error stop 1
if (sum([integer ::]) /= 0) error stop 2
end program p
"""
    specs.append(invalid_case(
        "R778", "untyped_empty_list", ["untyped-empty-list"], empty_invalid,
        "R778 has no untyped empty ac-spec alternative; inserting only INTEGER :: gives the conforming typed-empty control.",
        locate_line(empty_invalid, "n = size"), ["empty array constructor"], specs[-1]["id"], "R778",
        ["typed-empty-integer"], "insert only INTEGER :: between the brackets"))

    typed = """program p
implicit none
type rec
  integer :: marker
end type rec
type(rec) :: left, right
left%marker = 31
right%marker = 37
associate(ints => [integer :: 17,19,23])
  if (size(ints) /= 3) error stop 1
  if (ints(1) /= 17) error stop 2
  if (ints(2) /= 19) error stop 3
  if (ints(3) /= 23) error stop 4
end associate
associate(records => [rec :: left,right])
  if (size(records) /= 2) error stop 5
  if (records(1)%marker /= 31) error stop 6
  if (records(2)%marker /= 37) error stop 7
end associate
end program p
"""
    specs.append(valid_case(
        "R778", "typed_nonempty_and_derived", ["typed-nonempty"], typed,
        "R778 permits an optional type-spec :: before a nonempty value list; C7122 separately verifies the derived type-spec use in the same source.",
        ["typed INTEGER values 17,19,23", "derived record markers 31,37"],
        [dict(id="drop-integer-ac-value", original="[integer :: 17,19,23]", replacement="[integer :: 17,19]", source=remove_lines(typed.replace("[integer :: 17,19,23]", "[integer :: 17,19]", 1), "if (ints(3) /= 23) error stop 4")),
         dict(id="drop-derived-ac-value", original="[rec :: left,right]", replacement="[rec :: left]", source=remove_lines(typed.replace("[rec :: left,right]", "[rec :: left]", 1), "if (records(2)%marker /= 37) error stop 7")),
         dict(id="swap-derived-values", original="[rec :: left,right]", replacement="[rec :: right,left]", source=typed.replace("[rec :: left,right]", "[rec :: right,left]", 1))]))
    specs.append(valid_case(
        "C7122", "same_derived_type", ["same-derived-type-admission"], typed,
        "C7122 admits an explicit derived type-spec when each ac-value expression has that declared type; component markers prove the two record values are read.",
        ["records declared TYPE(rec)", "record markers 31,37"],
        [dict(id="drop-derived-ac-value", original="[rec :: left,right]", replacement="[rec :: left]", source=remove_lines(typed.replace("[rec :: left,right]", "[rec :: left]", 1), "if (records(2)%marker /= 37) error stop 7")),
         dict(id="swap-derived-values", original="[rec :: left,right]", replacement="[rec :: right,left]", source=typed.replace("[rec :: left,right]", "[rec :: right,left]", 1))]))

    untyped_control = """program p
implicit none
integer :: vec(2), matrix(2,2)
vec(1) = 11
vec(2) = 13
matrix(1,1) = 17
matrix(2,1) = 19
matrix(1,2) = 23
matrix(2,2) = 29
associate(values => [7,vec,matrix,31])
  if (size(values) /= 8) error stop 1
  if (values(1) /= 7) error stop 2
  if (values(2) /= 11) error stop 3
  if (values(3) /= 13) error stop 4
  if (values(4) /= 17) error stop 5
  if (values(5) /= 19) error stop 6
  if (values(6) /= 23) error stop 7
  if (values(7) /= 29) error stop 8
  if (values(8) /= 31) error stop 9
end associate
end program p
"""
    specs.append(valid_case(
        "C7120", "untyped_same_type_rank_control", ["same-type-kind-different-ranks"], untyped_control,
        "C7120 permits omitted type-spec when scalar, rank-one and rank-two ac-value expressions are all default INTEGER with the same KIND.",
        ["scalar 7", "rank-one vec 11,13", "rank-two matrix in array element order", "scalar 31"],
        [dict(id="drop-array-ac-value", original="[7,vec,matrix,31]", replacement="[7,vec,31]", source=remove_lines(untyped_control.replace("[7,vec,matrix,31]", "[7,vec,31]", 1), "if (values(5) /= 19) error stop 6", "if (values(6) /= 23) error stop 7", "if (values(7) /= 29) error stop 8", "if (values(8) /= 31) error stop 9")),
         dict(id="swap-matrix-elements", original="matrix(2,1) = 19", replacement="matrix(2,1) = 23", source=untyped_control.replace("matrix(2,1) = 19", "matrix(2,1) = 23", 1)),
         dict(id="reverse-leading-values", original="[7,vec,matrix,31]", replacement="[31,matrix,vec,7]", source=untyped_control.replace("[7,vec,matrix,31]", "[31,matrix,vec,7]", 1))]))
    specs.append(valid_case(
        "R778", "untyped_nonempty", ["untyped-nonempty"], untyped_control,
        "R778's nonempty ac-value-list alternative needs no type-spec when the values satisfy the separate type and length conditions.",
        ["nonempty omitted type-spec constructor"],
        [dict(id="drop-matrix-ac-value", original="[7,vec,matrix,31]", replacement="[7,vec,31]", source=remove_lines(untyped_control.replace("[7,vec,matrix,31]", "[7,vec,31]", 1), "if (values(5) /= 19) error stop 6", "if (values(6) /= 23) error stop 7", "if (values(7) /= 29) error stop 8", "if (values(8) /= 31) error stop 9")),
         dict(id="reverse-ac-value-order", original="[7,vec,matrix,31]", replacement="[31,matrix,vec,7]", source=untyped_control.replace("[7,vec,matrix,31]", "[31,matrix,vec,7]", 1))]))
    specs.append(valid_case(
        "R781", "scalar_and_array_values", ["scalar-expression-admission", "array-expression-admission"], untyped_control,
        "R781 admits both ordinary scalar expressions and array expressions as ac-values; the source observes both categories in one homogeneous constructor.",
        ["scalar ac-values 7 and 31", "array ac-values vec and matrix"],
        [dict(id="drop-array-ac-value", original="[7,vec,matrix,31]", replacement="[7,vec,31]", source=remove_lines(untyped_control.replace("[7,vec,matrix,31]", "[7,vec,31]", 1), "if (values(5) /= 19) error stop 6", "if (values(6) /= 23) error stop 7", "if (values(7) /= 29) error stop 8", "if (values(8) /= 31) error stop 9")),
         dict(id="reverse-ac-value-order", original="[7,vec,matrix,31]", replacement="[31,matrix,vec,7]", source=untyped_control.replace("[7,vec,matrix,31]", "[31,matrix,vec,7]", 1))]))
    diff_type = untyped_control.replace("[7,vec,matrix,31]", "[7,vec,2.0,31]")
    specs.append(invalid_case(
        "C7120", "different_intrinsic_type", ["different-intrinsic-type"], diff_type,
        "With type-spec omitted, replacing only the INTEGER matrix ac-value by REAL literal 2.0 violates C7120's same declared type requirement.",
        locate_line(diff_type, "associate(values"), ["array constructor"], specs[-3]["id"], "C7120",
        ["same-type-kind-different-ranks"], "replace only REAL literal 2.0 by the INTEGER matrix ac-value"))

    implied = """program p
implicit none
integer :: i, j, lower, upper, stride
lower = 1
upper = 5
stride = 2
associate(single => [(i,i=1,3)])
  if (size(single) /= 3) error stop 1
  if (single(1) /= 1) error stop 2
  if (single(2) /= 2) error stop 3
  if (single(3) /= 3) error stop 4
end associate
associate(multiple => [(i,10*i,i=1,2)])
  if (size(multiple) /= 4) error stop 5
  if (multiple(1) /= 1) error stop 6
  if (multiple(2) /= 10) error stop 7
  if (multiple(3) /= 2) error stop 8
  if (multiple(4) /= 20) error stop 9
end associate
associate(nested => [((10*i+j,j=1,2),i=1,2)])
  if (size(nested) /= 4) error stop 10
  if (nested(1) /= 11) error stop 11
  if (nested(2) /= 12) error stop 12
  if (nested(3) /= 21) error stop 13
  if (nested(4) /= 22) error stop 14
end associate
associate(runtime => [(i,i=lower,upper,stride)])
  if (size(runtime) /= 3) error stop 15
  if (runtime(1) /= 1) error stop 16
  if (runtime(2) /= 3) error stop 17
  if (runtime(3) /= 5) error stop 18
end associate
end program p
"""
    specs.append(valid_case(
        "R781", "implied_do_value", ["implied-do-admission"], implied,
        "R781 admits an ac-implied-do as an ac-value; the program observes four such constructors under ordinary INTEGER controls.",
        ["single implied DO", "multiple body implied DO", "nested implied DO", "runtime-bound implied DO"],
        [dict(id="drop-multiple-body-value", original="[(i,10*i,i=1,2)]", replacement="[(i,i=1,2)]", source=remove_lines(implied.replace("[(i,10*i,i=1,2)]", "[(i,i=1,2)]", 1), "if (multiple(3) /= 2) error stop 8", "if (multiple(4) /= 20) error stop 9")),
         dict(id="swap-nested-order", original="[((10*i+j,j=1,2),i=1,2)]", replacement="[((10*i+j,i=1,2),j=1,2)]", source=implied.replace("[((10*i+j,j=1,2),i=1,2)]", "[((10*i+j,i=1,2),j=1,2)]", 1))]))
    specs.append(valid_case(
        "R782", "implied_do_forms", ["single-body-value", "multiple-body-values", "nested-form"], implied,
        "R782's parenthesized ac-value-list, comma and control form is exercised with one body value, two body values and a nested implied DO.",
        ["single body 1,2,3", "multiple body 1,10,2,20", "nested 11,12,21,22"],
        [dict(id="drop-multiple-body-value", original="[(i,10*i,i=1,2)]", replacement="[(i,i=1,2)]", source=remove_lines(implied.replace("[(i,10*i,i=1,2)]", "[(i,i=1,2)]", 1), "if (multiple(3) /= 2) error stop 8", "if (multiple(4) /= 20) error stop 9")),
         dict(id="swap-nested-order", original="[((10*i+j,j=1,2),i=1,2)]", replacement="[((10*i+j,i=1,2),j=1,2)]", source=implied.replace("[((10*i+j,j=1,2),i=1,2)]", "[((10*i+j,i=1,2),j=1,2)]", 1)),
         dict(id="drop-runtime-ac-value", original="[(i,i=lower,upper,stride)]", replacement="[(i,i=lower,lower,stride)]", source=implied.replace("[(i,i=lower,upper,stride)]", "[(i,i=lower,lower,stride)]", 1))]))
    specs.append(valid_case(
        "R783", "inferred_and_runtime_controls", ["inferred-integer-variable", "runtime-bound-and-step-expressions"], implied,
        "R783 permits omitted integer-type-spec when containing-scope INTEGER names supply the ac-do-variable type, and scalar runtime INTEGER bounds/step are used.",
        ["declared INTEGER i and j", "runtime lower upper stride"],
        [dict(id="change-runtime-upper-bound", original="upper = 5", replacement="upper = 3", source=implied.replace("upper = 5", "upper = 3", 1)),
         dict(id="change-runtime-stride", original="stride = 2", replacement="stride = 1", source=implied.replace("stride = 2", "stride = 1", 1))]))
    specs.append(valid_case(
        "C7128", "distinct_nested_variables", ["distinct-nested-variables"], implied,
        "C7128 permits the nested form when the inner ac-do-variable j is distinct from the containing ac-do-variable i.",
        ["inner j", "outer i"],
        [dict(id="swap-distinct-nested-order", original="[((10*i+j,j=1,2),i=1,2)]", replacement="[((10*i+j,i=1,2),j=1,2)]", source=implied.replace("[((10*i+j,j=1,2),i=1,2)]", "[((10*i+j,i=1,2),j=1,2)]", 1)),
         dict(id="change-inner-bound", original="j=1,2", replacement="j=1,1", source=remove_lines(implied.replace("j=1,2", "j=1,1", 1), "if (nested(3) /= 21) error stop 13", "if (nested(4) /= 22) error stop 14"))]))

    chars = """program p
implicit none
integer :: i
character(len=2) :: left, right
left = 'AB'
right = 'CD'
associate(equal => [left,right])
  if (len(equal) /= 2) error stop 1
  if (size(equal) /= 2) error stop 2
  if (equal(1) /= 'AB') error stop 3
  if (equal(2) /= 'CD') error stop 4
end associate
associate(zero_constant => [('AB',i=1,0)])
  if (size(zero_constant) /= 0) error stop 5
  if (len(zero_constant) /= 2) error stop 6
end associate
associate(zero_typed => [character(len=3) :: ('AB',i=1,0)])
  if (size(zero_typed) /= 0) error stop 7
  if (len(zero_typed) /= 3) error stop 8
end associate
end program p
"""
    specs.append(valid_case(
        "S7.8-002", "equal_character_lengths", ["runtime-equal-length-controls"], chars,
        "7.8p2 permits omitted type-spec when corresponding CHARACTER LEN parameters agree; two separately assigned CHARACTER(2) values give LEN 2 and exact contents.",
        ["LEN equal is 2", "values AB and CD"],
        [dict(id="change-declared-length", original="character(len=2) :: left, right", replacement="character(len=3) :: left, right", source=chars.replace("character(len=2) :: left, right", "character(len=3) :: left, right", 1)),
         dict(id="drop-character-ac-value", original="[left,right]", replacement="[left]", source=remove_lines(chars.replace("[left,right]", "[left]", 1), "if (equal(2) /= 'CD') error stop 4"))]))
    specs.append(valid_case(
        "S7.8-007", "constant_zero_trip_character", ["constant-length-zero-trip-control"], chars,
        "7.8p5 permits a zero-trip implied DO whose CHARACTER ac-value length is constant; SIZE is zero and LEN is checked for both untyped and typed forms.",
        ["zero-trip untyped LEN 2", "zero-trip typed LEN 3"],
        [dict(id="change-type-spec-length", original="character(len=3)", replacement="character(len=2)", source=chars.replace("character(len=3)", "character(len=2)", 1)),
         dict(id="make-zero-trip-nonempty", original="('AB',i=1,0)", replacement="('AB',i=1,1)", source=chars.replace("('AB',i=1,0)", "('AB',i=1,1)", 1))]))
    ids = [s["id"] for s in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case identifiers")
    return specs


def build_corpus(root=ROOT):
    files = {}
    specs = {spec["id"]: spec for spec in source_specs()}
    for spec in specs.values():
        raw = spec["source"].encode("ascii")
        if max(map(len, raw.splitlines())) > 132:
            raise ValueError(spec["id"] + " has an overlong source line")
        spec["source_sha256"] = sha(raw)
        spec["manifest"] = manifest(spec)
        folder = Path(root) / "tests/fixtures" / (PREFIX + spec["id"].lower())
        spec["path"] = str(folder.relative_to(root) / "fixture.json")
        files[folder / "source.f90"] = raw
        files[folder / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    selected = {rule: set(facets) for rule, facets in SELECTED.items()}
    case_facets = {}
    for spec in specs.values():
        case_facets.setdefault(spec["rule"], set()).update(spec["facets"])
    if case_facets != selected:
        raise ValueError("case/facet partition differs from selected 20 facets")
    requirements = {row["id"]: row for row in result["requirements"]}
    for rule, facets in selected.items():
        if rule not in requirements or not facets <= set(requirements[rule]["facets"]):
            raise ValueError("selected facet definitions changed for " + rule)
        for facet in facets:
            requirements[rule]["pending"].pop(facet, None)
        requirements[rule]["oracle"] = owned_paragraph(requirements[rule].get("oracle", ""), ORACLE_PREFIX, ORACLE)
        requirements[rule]["oracle_limitation"] = owned_paragraph(
            requirements[rule].get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    return result


def composed_view(catalogue, root=ROOT):
    import generate_array_constructor_value_fixtures as value_packet
    _, value_specs = value_packet.build_corpus(root)
    return value_packet.render_view(catalogue, value_specs)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = composed_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {p for p in (root / "tests/fixtures").glob(PREFIX + "*/*") if p.is_file()}
        stale += [p.relative_to(root).as_posix() for p in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / "doc/fortran_2023_7_8.md").read_text() != view:
            stale.append("doc/fortran_2023_7_8.md")
        if stale:
            raise SystemExit("stale array-constructor form packet: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / "doc/fortran_2023_7_8.md").write_text(view)
    return specs


def executable_command(compiler, std, source, output):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}", str(source), "-o", str(output)]
    return [compiler, f"-std={std}", str(source), "-o", str(output)]


def check_mutations(root, compiler, std):
    root = Path(root)
    _, specs = build_corpus(root)
    mutations = [(spec, mutation) for spec in specs.values() if spec["kind"] == "valid"
                 for mutation in spec["mutations"]]
    if not mutations:
        raise SystemExit("no array-constructor form mutations defined")
    workspace = root / ".array_constructor_form_mutations"
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
            source.write_text(mutation["source"])
            compile_result = subprocess.run(
                executable_command(compiler, std, source, exe),
                cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            if compile_result.returncode != 0:
                failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{compile_result.stdout}")
                continue
            run_result = subprocess.run(
                [str(exe)], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            if run_result.returncode == 0:
                failures.append(f"{spec['id']}:{mutation['id']} survived")
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
    if args.check_mutations and (not args.compiler or not args.std):
        parser.error("--check-mutations requires --compiler and --std")
    if args.check_mutations:
        check_mutations(args.root, args.compiler, args.std)
        return
    specs = generate(args.root, args.check, args.sync_catalogue)
    facets = sum(len(spec["facets"]) for spec in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} array-constructor form cases and {facets} facets.")


if __name__ == "__main__":
    main()
