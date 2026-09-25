#!/usr/bin/env python3
"""Additional array constructor 7.8 fixtures for type/category and syntax edges."""
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
VIEW = "doc/fortran_2023_7_8.md"
PREFIX = "array_constructors_7_8_b_"
EXCLUSIONS = (
    "not yet implemented", "not implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "assert", "asr", "verifier", "out of memory", "traceback",
    "unknown exception", "segmentation", "bus error", "abort", "cannot read module",
)
SELECTED = {
    "R778": ["typed-empty-other-categories"],
    "C7121": ["intrinsic-type-admissions"],
    "C7124": ["limited-value-admissions"],
    "C7125": ["concrete-child-admission"],
    "C7128": ["disjoint-reuse-admission"],
    "S7.8-002": ["zero-size-and-explicit-spec-boundaries"],
    "R782": ["missing-control-separator", "missing-body-list"],
    "R784": ["bare-scalar-integer-name", "literal-is-not-control-variable"],
}
CONTROL_FACETS = {
    "R782": ["single-body-value"],
}
ORACLE_PREFIX = "Array constructors 7.8.b implementation: "
LIMIT_PREFIX = "Array constructors 7.8.b boundaries: "
ORACLE = ORACLE_PREFIX + (
    "12 generated fixtures discharge 10 additional 7.8 facets. Six positive controls use complete "
    "constructors to observe typed-empty CHARACTER and derived-type forms, explicit intrinsic type "
    "admissions, limited polymorphic CLASS(base) values with an explicit concrete type-spec, concrete "
    "child values extending an abstract parent, disjoint reuse of an ac-do-variable spelling in separate "
    "nonnested implied DOs, and explicit CHARACTER length boundaries for zero-size and converted values. "
    "Two R784 positive controls check bare scalar INTEGER names and confirm the containing host variable is "
    "not the statement entity. Three focused syntax negatives are line-anchored diagnostics with real one-property "
    "controls: a missing implied-DO body/control comma, a missing implied-DO body list, and a literal used "
    "where the ac-do-variable name is required. Each valid case has source-generated feature mutations that "
    "compile and fail at run time on both qualifying toolchains; each diagnostic case records its conforming "
    "single-property repair."
)
LIMITATION = LIMIT_PREFIX + (
    "only the named facets are discharged. Runtime CHARACTER(LEN=n) constructors remain pending because "
    "the frozen LFortran target rejects the direct standard-conforming expression. Inline integer-type-spec "
    "implied-DO controls, same-nested-name C7128 diagnostics, unlimited-polymorphic and declared-abstract "
    "negative contrasts, BOZ constructors, enumeration constructors, PDT kind/LEN matrices and optional "
    "distinct integer-kind negatives remain pending under their existing source-use or processor-support "
    "qualifications. Existing array_constructor_form and array_constructor_value bindings are not altered."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ident(rule, variant, kind="valid"):
    return rule.replace(".", "_").replace("-", "_") + f"_{kind}__array_constructors_7_8_b_" + variant


def locate_line(source, needle):
    matches = [i + 1 for i, line in enumerate(source.splitlines()) if needle in line]
    if len(matches) != 1:
        raise ValueError("line anchor is not unique: " + needle)
    return matches[0]


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned 7.8.b paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
        return "\n\n".join(paragraphs)
    return text + ("\n\n" if text else "") + replacement


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
    return dict(id=ident(rule, variant), rule=rule, variant=variant, kind="valid",
                evidence="positive-control", facets=list(facets), source=source,
                derivation=derivation, observations=list(observations), mutations=list(mutations))


def invalid_case(rule, variant, facets, source, derivation, repair, control_id):
    line = locate_line(source, repair["anchor"])
    diagnostic = dict(file="source.f90", line=line, end_line=line, excludes_any=list(EXCLUSIONS))
    return dict(id=ident(rule, variant, "invalid"), rule=rule, variant=variant, kind="invalid",
                evidence="effect", facets=list(facets), source=source, derivation=derivation,
                diagnostic=diagnostic, repair=repair, control_id=control_id, mutations=[])


def source_specs():
    specs = []
    typed_empty_other = """program p
implicit none
type :: rec
  integer :: marker
end type rec
associate(chars => [character(len=3) ::])
  if (size(chars) /= 0) error stop 1
  if (len(chars) /= 3) error stop 2
end associate
if (size([rec ::]) /= 0) error stop 3
end program p
"""
    specs.append(valid_case(
        "R778", "typed_empty_other_categories", SELECTED["R778"], typed_empty_other,
        "R778's type-spec :: empty alternative is not limited to INTEGER; fixed CHARACTER(LEN=3) and a prior derived type both form zero-size constructors without ac-values.",
        ["CHARACTER typed-empty size zero", "CHARACTER typed-empty LEN 3", "derived typed-empty size zero"],
        [dict(id="change-empty-character-length", source=typed_empty_other.replace("[character(len=3) ::]", "[character(len=2) ::]", 1)),
         dict(id="make-character-empty-nonempty", source=typed_empty_other.replace("[character(len=3) ::]", "[character(len=3) :: 'abc']", 1)),
         dict(id="make-derived-empty-nonempty", source=typed_empty_other.replace("size([rec ::])", "size([rec :: rec(5)])", 1))]))

    explicit_char = """program p
implicit none
associate(empty => [character(len=3) ::])
  if (size(empty) /= 0) error stop 1
  if (len(empty) /= 3) error stop 2
end associate
associate(values => [character(len=3) :: 'ab','abcd'])
  if (len(values) /= 3) error stop 3
  if (size(values) /= 2) error stop 4
  if (values(1) /= 'ab ') error stop 5
  if (values(2) /= 'abc') error stop 6
end associate
end program p
"""
    specs.append(valid_case(
        "S7.8-002", "explicit_character_length_boundaries", SELECTED["S7.8-002"], explicit_char,
        "7.8p2's omitted-type LEN agreement restriction is bounded by an explicit CHARACTER(LEN=3) type-spec: p8 keeps the typed-empty result zero-sized with LEN 3, and p3 with 10.2.1.3 pads/truncates the nonempty values to LEN 3.",
        ["explicit CHARACTER typed-empty size zero and LEN 3", "explicit LEN 3 pads ab", "explicit LEN 3 truncates abcd"],
        [dict(id="change-explicit-empty-length", source=explicit_char.replace("[character(len=3) ::]", "[character(len=2) ::]", 1)),
         dict(id="change-explicit-value-length", source=explicit_char.replace("[character(len=3) :: 'ab','abcd']", "[character(len=4) :: 'ab','abcd']", 1)),
         dict(id="swap-explicit-character-values", source=explicit_char.replace("[character(len=3) :: 'ab','abcd']", "[character(len=3) :: 'abcd','ab']", 1))]))

    intrinsic = """program p
implicit none
associate(ints => [integer :: 1, 2.0, (3.0,0.0)])
  if (size(ints) /= 3) error stop 1
  if (ints(1) /= 1) error stop 2
  if (ints(2) /= 2) error stop 3
  if (ints(3) /= 3) error stop 4
end associate
associate(reals => [real :: 1, 2.0, (3.0,0.0)])
  if (size(reals) /= 3) error stop 5
  if (reals(1) /= 1.0) error stop 6
  if (reals(2) /= 2.0) error stop 7
  if (reals(3) /= 3.0) error stop 8
end associate
associate(complexes => [complex :: 1, 2.0, (3.0,-4.0)])
  if (size(complexes) /= 3) error stop 9
  if (complexes(1) /= (1.0,0.0)) error stop 10
  if (complexes(2) /= (2.0,0.0)) error stop 11
  if (complexes(3) /= (3.0,-4.0)) error stop 12
end associate
associate(logicals => [logical :: .true., .false.])
  if (size(logicals) /= 2) error stop 13
  if (.not. logicals(1)) error stop 14
  if (logicals(2)) error stop 15
end associate
associate(chars => [character(len=2) :: 'A','BC'])
  if (len(chars) /= 2) error stop 16
  if (size(chars) /= 2) error stop 17
  if (chars(1) /= 'A ') error stop 18
  if (chars(2) /= 'BC') error stop 19
end associate
end program p
"""
    specs.append(valid_case(
        "C7121", "intrinsic_type_admissions", SELECTED["C7121"], intrinsic,
        "C7121 admits explicit intrinsic type-spec constructors when each ac-value conforms by Table 10.8 or ordinary CHARACTER/LOGICAL identity; small exact values check each admitted category.",
        ["INTEGER from integer/real/complex values", "REAL from integer/real/complex values",
         "COMPLEX from integer/real/complex values", "LOGICAL values", "CHARACTER length and values"],
        [dict(id="reverse-integer-values", source=intrinsic.replace("[integer :: 1, 2.0, (3.0,0.0)]", "[integer :: (3.0,0.0), 2.0, 1]", 1)),
         dict(id="change-real-converted-value", source=intrinsic.replace("[real :: 1, 2.0, (3.0,0.0)]", "[real :: 1, 4.0, (3.0,0.0)]", 1)),
         dict(id="reverse-complex-values", source=intrinsic.replace("[complex :: 1, 2.0, (3.0,-4.0)]", "[complex :: (3.0,-4.0), 2.0, 1]", 1)),
         dict(id="swap-logical-values", source=intrinsic.replace("[logical :: .true., .false.]", "[logical :: .false., .true.]", 1)),
         dict(id="swap-character-values", source=intrinsic.replace("[character(len=2) :: 'A','BC']", "[character(len=2) :: 'BC','A']", 1))]))

    limited = """module m
implicit none
type :: base
  integer :: payload
end type base
type, extends(base) :: child
  integer :: extra
end type child
contains
subroutine observe_class(x)
  class(base), intent(in) :: x
  type(base) :: local
  local%payload = 41
  associate(values => [base :: local, x])
    if (size(values) /= 2) error stop 1
    if (values(1)%payload /= 41) error stop 2
    if (values(2)%payload /= 43) error stop 3
  end associate
end subroutine observe_class
end module m
program p
use m
implicit none
type(child) :: actual
actual%payload = 43
actual%extra = 47
associate(ints => [integer :: 5, 7])
  if (size(ints) /= 2) error stop 4
  if (ints(1) /= 5) error stop 5
  if (ints(2) /= 7) error stop 6
end associate
call observe_class(actual)
end program p
"""
    specs.append(valid_case(
        "C7124", "limited_value_admissions", SELECTED["C7124"], limited,
        "C7124 excludes only unlimited polymorphic ac-values; explicit INTEGER values, TYPE(base) values and CLASS(base) values are limited and their payloads are observed.",
        ["intrinsic INTEGER values", "concrete TYPE(base) payload", "limited CLASS(base) payload"],
        [dict(id="swap-limited-class-values", source=limited.replace("[base :: local, x]", "[base :: x, local]", 1)),
         dict(id="swap-intrinsic-limited-values", source=limited.replace("[integer :: 5, 7]", "[integer :: 7, 5]", 1))]))

    concrete_child = """program p
implicit none
type, abstract :: base
  integer :: payload
end type base
type, extends(base) :: child
  integer :: extra
end type child
type(child) :: left, right
left%payload = 17
left%extra = 19
right%payload = 23
right%extra = 29
associate(values => [left, right])
  if (size(values) /= 2) error stop 1
  if (values(1)%payload /= 17) error stop 2
  if (values(1)%extra /= 19) error stop 3
  if (values(2)%payload /= 23) error stop 4
  if (values(2)%extra /= 29) error stop 5
end associate
end program p
"""
    specs.append(valid_case(
        "C7125", "concrete_child_admission", SELECTED["C7125"], concrete_child,
        "C7125 prohibits ac-values whose declared type is abstract; concrete child values extending an abstract parent have declared type child and are admitted.",
        ["two TYPE(child) values", "inherited payload components", "child extra components"],
        [dict(id="swap-concrete-child-values", source=concrete_child.replace("[left, right]", "[right, left]", 1)),
         dict(id="duplicate-left-child", source=concrete_child.replace("[left, right]", "[left, left]", 1))]))

    disjoint = """program p
implicit none
integer :: i
i = 99
associate(values => [(i,i=1,2),(i,i=3,4)])
  if (size(values) /= 4) error stop 1
  if (values(1) /= 1) error stop 2
  if (values(2) /= 2) error stop 3
  if (values(3) /= 3) error stop 4
  if (values(4) /= 4) error stop 5
end associate
if (i /= 99) error stop 6
end program p
"""
    specs.append(valid_case(
        "C7128", "disjoint_reuse_admission", SELECTED["C7128"], disjoint,
        "C7128's nested-name prohibition does not apply to separate nonnested implied DOs; both uses of i have separate statement-entity scopes and the host i remains 99.",
        ["first nonnested i loop 1,2", "second nonnested i loop 3,4", "host i unchanged"],
        [dict(id="change-second-disjoint-bounds", source=disjoint.replace("(i,i=3,4)", "(i,i=4,5)", 1)),
         dict(id="drop-first-disjoint-loop", source=disjoint.replace("[(i,i=1,2),(i,i=3,4)]", "[(i,i=3,4),(i,i=1,2)]", 1))]))

    bare = """program p
implicit none
integer :: i
i = 77
associate(values => [(i,i=2,4)])
  if (size(values) /= 3) error stop 1
  if (values(1) /= 2) error stop 2
  if (values(2) /= 3) error stop 3
  if (values(3) /= 4) error stop 4
end associate
if (i /= 77) error stop 5
end program p
"""
    specs.append(valid_case(
        "R784", "bare_scalar_integer_name", ["bare-scalar-integer-name"], bare,
        "R784 uses the do-variable name form for an ac-do-variable; the scalar INTEGER name controls the implied DO as a statement entity, leaving the host i value unchanged.",
        ["bare i controls values 2,3,4", "host i remains 77"],
        [dict(id="change-bare-terminal-bound", source=bare.replace("[(i,i=2,4)]", "[(i,i=3,5)]", 1)),
         dict(id="change-bare-initial-bound", source=bare.replace("[(i,i=2,4)]", "[(i,i=1,3)]", 1))]))
    bare_id = specs[-1]["id"]

    literal_control = bare.replace("[(i,i=2,4)]", "[(7,i=2,4)]")
    literal_control = literal_control.replace("if (values(1) /= 2) error stop 2", "if (values(1) /= 7) error stop 2")
    literal_control = literal_control.replace("if (values(2) /= 3) error stop 3", "if (values(2) /= 7) error stop 3")
    literal_control = literal_control.replace("if (values(3) /= 4) error stop 4", "if (values(3) /= 7) error stop 4")
    specs.append(valid_case(
        "R784", "literal_control_repair", ["bare-scalar-integer-name"], literal_control,
        "This one-property control for the literal-control diagnostic uses the same constant body and repairs only the ac-do-variable to the bare INTEGER name i.",
        ["constant body 7 is expanded three times", "host i remains 77"],
        [dict(id="change-literal-control-body", source=literal_control.replace("[(7,i=2,4)]", "[(8,i=2,4)]", 1))]))
    literal_control_id = specs[-1]["id"]

    control_r782 = """program p
implicit none
integer :: i
associate(values => [(7, i=1,2)])
  if (size(values) /= 2) error stop 1
  if (values(1) /= 7) error stop 2
  if (values(2) /= 7) error stop 3
end associate
end program p
"""
    specs.append(valid_case(
        "R782", "implied_do_syntax_control", CONTROL_FACETS["R782"], control_r782,
        "R782's conforming control has a nonempty body list, comma separator and complete ac-implied-do-control.",
        ["two literal 7 body values under i=1,2"],
        [dict(id="change-control-body-value", source=control_r782.replace("[(7, i=1,2)]", "[(8, i=1,2)]", 1))]))
    control_id = specs[-1]["id"]
    missing_separator = control_r782.replace("[(7, i=1,2)]", "[(7 i=1,2)]")
    specs.append(invalid_case(
        "R782", "missing_control_separator", ["missing-control-separator"], missing_separator,
        "R782 requires the comma between the ac-value-list and ac-implied-do-control; inserting only that comma gives the conforming control.",
        dict(anchor="associate(values", original="[(7 i=1,2)]", replacement="[(7, i=1,2)]", control_facets=CONTROL_FACETS["R782"]), control_id))
    missing_body = control_r782.replace("[(7, i=1,2)]", "[(, i=1,2)]")
    specs.append(invalid_case(
        "R782", "missing_body_list", ["missing-body-list"], missing_body,
        "R782 requires a nonempty ac-value-list before the comma; inserting only literal 7 gives the conforming control.",
        dict(anchor="associate(values", original="[(, i=1,2)]", replacement="[(7, i=1,2)]", control_facets=CONTROL_FACETS["R782"]), control_id))

    literal_invalid = literal_control.replace("[(7,i=2,4)]", "[(7,1=2,4)]")
    specs.append(invalid_case(
        "R784", "literal_control_variable", ["literal-is-not-control-variable"], literal_invalid,
        "R784 requires an ac-do-variable name; replacing only the literal control-left-side 1 by i gives the conforming bare-name control.",
        dict(anchor="associate(values", original="[(7,1=2,4)]", replacement="[(7,i=2,4)]", control_facets=["bare-scalar-integer-name"]),
        literal_control_id))

    ids = [spec["id"] for spec in specs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fixture ids")
    return specs


def build_corpus(root=ROOT):
    root = Path(root)
    files = {}
    specs = {spec["id"]: spec for spec in source_specs()}
    for spec in specs.values():
        raw = spec["source"].encode("ascii")
        if max(map(len, raw.splitlines())) > 132:
            raise ValueError(spec["id"] + " has an overlong source line")
        spec["source_sha256"] = sha(raw)
        spec["manifest"] = manifest(spec)
        folder = root / "tests/fixtures" / (PREFIX + spec["id"].lower())
        spec["path"] = str(folder.relative_to(root) / "fixture.json")
        files[folder / "source.f90"] = raw
        files[folder / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, specs


def selected_facets():
    return {rule: set(facets) for rule, facets in SELECTED.items()}


def synced_catalogue(catalogue, specs):
    result = copy.deepcopy(catalogue)
    expected = selected_facets()
    actual = {}
    for spec in specs.values():
        if spec["rule"] in SELECTED:
            selected = set(SELECTED[spec["rule"]])
            claimed = set(spec["facets"]) & selected
            if claimed:
                actual.setdefault(spec["rule"], set()).update(claimed)
    if actual != expected:
        raise ValueError("case/facet partition differs from selected 7.8.b facets")
    requirements = {item["id"]: item for item in result["requirements"]}
    for rule, facets in expected.items():
        req = requirements[rule]
        if not facets <= set(req["facets"]):
            raise ValueError("unknown selected facet for " + rule)
        for facet in facets:
            req["pending"].pop(facet, None)
        req["oracle"] = owned_paragraph(req.get("oracle", ""), ORACLE_PREFIX, ORACLE)
        req["oracle_limitation"] = owned_paragraph(req.get("oracle_limitation", ""), LIMIT_PREFIX, LIMITATION)
    return result


def render_view(catalogue, root=ROOT):
    import generate_array_constructor_value_fixtures as value_packet
    _, value_specs = value_packet.build_corpus(root)
    return value_packet.render_view(catalogue, value_specs)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, specs = build_corpus(root)
    catalogue = json.loads((root / CATALOGUE).read_text())
    updated = synced_catalogue(catalogue, specs)
    view = render_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {p for p in (root / "tests/fixtures").glob(PREFIX + "*/*") if p.is_file()}
        stale += [p.relative_to(root).as_posix() for p in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (root / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale array constructors 7.8.b packet: " + ", ".join(sorted(stale)))
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
    mutations = [(spec, mutation) for spec in specs.values() if spec["kind"] == "valid"
                 for mutation in spec.get("mutations", [])]
    workspace = root / ".array_constructors_7_8_b_mutations"
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
                executable_command(compiler, std, Path("source.f90"), Path("program")), cwd=case_dir, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            if compile_result.returncode != 0:
                failures.append(f"{spec['id']}:{mutation['id']} did not compile:\n{compile_result.stdout}")
                continue
            run_result = subprocess.run(["./program"], cwd=case_dir, text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
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
    facets = sum(len(facets) for facets in SELECTED.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} array constructors 7.8.b cases and {facets} facets.")


if __name__ == "__main__":
    main()
